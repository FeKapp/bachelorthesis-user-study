import streamlit as st
import uuid
import random      
import random
from dateutil.parser import isoparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict             
from modules.database import supabase, update_session_progress

# Cached database fetches with session-specific isolation
@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_scenario_config():
    return supabase.table('scenario_config').select('*').execute().data

@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_fund_returns(scenario_id):
    return {fr['trial_number']: (fr['return_a'], fr['return_b']) 
            for fr in supabase.table('fund_returns')
                .select('*')
                .eq('scenario_id', scenario_id)
                .execute().data}

@st.cache_data(ttl=3600, show_spinner=False)
def _fetch_ai_recommendations(scenario_id):
    return {ai['trial_number']: (ai['fund_a'], ai['fund_b'])
            for ai in supabase.table('ai_recommendations')
                .select('*')
                .eq('scenario_id', scenario_id)
                .execute().data}

def init_session():
    """Optimized session handling with safe initialization"""
    if 'session_initialized' in st.session_state:
        return

    # Session ID handling with single rerun
    session_id = st.query_params.get("session_id")
    if not session_id:
        session_id = str(uuid.uuid4())
        st.query_params["session_id"] = session_id
        st.rerun()

    # Load or create session with atomic operations
    if not _load_existing_session(session_id):
        _create_new_session(session_id)

    # Ensure valid state for current trial
    current_trial = st.session_state.get('trial', 1)
    if current_trial not in st.session_state.allocations:
        st.session_state.allocations[current_trial] = {
            'initial': None,
            'ai': None,
            'final': None
        }

    st.session_state.session_initialized = True
    update_session_progress(session_id)

def _load_existing_session(session_id):
    """Efficiently load session data with joined queries"""
    response = supabase.table('sessions') \
        .select('*, trials(*, allocations(*)), trial_sequence_id') \
        .eq('session_id', session_id) \
        .execute()

    if not response.data:
        return False

    session_data = response.data[0]
    trials = session_data.get('trials', [])

    # Re-load the stored trial_sequence
    seq_rec = supabase.table('trial_sequences') \
        .select('*') \
        .eq('trial_sequence_id', session_data['trial_sequence_id']) \
        .execute().data[0]

    # convert string IDs to ints
    fy_trials = [int(x) for x in seq_rec['five_year_trials']]
    tm_trials = [int(x) for x in seq_rec['three_month_trials']]

    # decide which to use based on stored max_trials
    if session_data['max_trials'] == len(fy_trials):
        trial_seq = fy_trials
    else:
        trial_seq = tm_trials

    # Process allocations in single pass
    allocations = {}
    fund_returns = {}
    for trial in trials:
        trial_num = trial['trial_number']
        fund_returns[trial_num] = (
            trial.get('return_a', 0),
            trial.get('return_b', 0)
        )
        allocs = {'initial': None, 'ai': None, 'final': None}
        for alloc in trial.get('allocations', []):
            alloc_type = alloc['allocation_type']
            if alloc_type in allocs:
                allocs[alloc_type] = (
                    alloc.get('fund_a', 0),
                    alloc.get('fund_b', 0)
                )
        allocations[trial_num] = allocs

    st.session_state.update({
        'page':               session_data['current_page'],
        'trial':              session_data['current_trial'],
        'trial_step':         session_data['current_trial_step'],
        'scenario_id':        session_data['scenario_id'],
        'max_trials':         session_data['max_trials'],
        'trial_sequence_id':  session_data['trial_sequence_id'],
        'trial_sequence':     trial_seq,
        'fund_returns':       fund_returns,
        'allocations':        allocations
    })
    return True

def _create_new_session(session_id):
    """Create a new session with optimized data fetching"""

    all_seqs     = supabase.table('trial_sequences').select('*').execute().data
    scenarios    = _fetch_scenario_config()
    all_sessions = supabase.table('sessions').select('*').execute().data

    seq_rec, scenario = get_session_config(all_seqs, scenarios, all_sessions, lock_window_hours=1.5)

    fy_trials = [int(x) for x in seq_rec['five_year_trials']]
    tm_trials = [int(x) for x in seq_rec['three_month_trials']]
    trial_seq = fy_trials if scenario['num_trials'] == 5 else tm_trials

    # choose based on scenario length
    if scenario.get('num_trials') == 5:
        trial_seq = fy_trials
    else:
        trial_seq = tm_trials

    st.session_state.update({
        'page':                   'consent',
        'trial':                  1,
        'trial_step':             1,
        'scenario_id':            scenario['scenario_id'],
        'trial_sequence_id':      seq_rec['trial_sequence_id'],
        'trial_sequence':         trial_seq,
        'max_trials':             len(trial_seq),
        'fund_returns':           {},
        'allocations':            {1: {'initial': None, 'ai': None, 'final': None}},
        'fund_returns_data':      _fetch_fund_returns(scenario['scenario_id']),
        'ai_recommendations_data':_fetch_ai_recommendations(scenario['scenario_id'])
    })

    supabase.table('sessions').insert({
        'session_id':         session_id,
        'scenario_id':        scenario['scenario_id'],
        'trial_sequence_id':  seq_rec['trial_sequence_id'],   # store pointer
        'current_page':       'consent',
        'current_trial':      0,
        'current_trial_step': 1,
        'created_at':         datetime.now(timezone.utc).isoformat(),
        'max_trials':         len(trial_seq)
    }).execute()

def get_session_config(all_seqs, scenarios, all_sessions, lock_window_hours=1):
    """Select a scenario and sequence based on existing sessions and lock window"""

    now = datetime.now(timezone.utc)
    lock_threshold = now - timedelta(hours=lock_window_hours)

    # 1. Filter valid sessions
    valid = []
    for sess in all_sessions:
        created = isoparse(sess['created_at'])
        completed = sess['completed_at']
        dq_good = sess.get('data_quality') is True

        if (completed is not None and dq_good) or (created >= lock_threshold):
            valid.append(sess)

    # 2. Group by sequence
    by_seq = defaultdict(list)
    for sess in valid:
        by_seq[sess['trial_sequence_id']].append(sess['scenario_id'])

    # prepare set of all scenario_ids
    all_sids = {s['scenario_id'] for s in scenarios}

    # 3. Look for a group with <4 sessions
    for seq in all_seqs:
        seq_id = seq['trial_sequence_id']
        seen = set(by_seq.get(seq_id, []))
        if len(seen) < len(all_sids):
            # missing scenarios
            missing = list(all_sids - seen)
            pick_sid = random.choice(missing)
            # find the matching scenario dict
            scenario = next(s for s in scenarios if s['scenario_id'] == pick_sid)
            return seq, scenario

    # 5. if no partial group (or no sessions), just pick entirely at random
    seq = random.choice(all_seqs)
    scenario = random.choice(scenarios)
    return seq, scenario
