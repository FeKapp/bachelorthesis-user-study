import streamlit as st
import numpy as np
import uuid
from datetime import datetime
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
        .select('*, trials(*, allocations(*))') \
        .eq('session_id', session_id) \
        .execute()

    if not response.data:
        return False

    session_data = response.data[0]
    trials = session_data.get('trials', [])

    # Process allocations in single pass
    allocations = {}
    fund_returns = {}
    
    for trial in trials:
        trial_num = trial['trial_number']
        fund_returns[trial_num] = (
            trial.get('return_a', 0),
            trial.get('return_b', 0))
        
        allocs = {'initial': None, 'ai': None, 'final': None}
        for alloc in trial.get('allocations', []):
            alloc_type = alloc['allocation_type']
            if alloc_type in allocs:
                allocs[alloc_type] = (
                    alloc.get('fund_a', 0),
                    alloc.get('fund_b', 0))
        allocations[trial_num] = allocs

    st.session_state.update({
        'page': session_data['current_page'],
        'trial': session_data['current_trial'],
        'trial_step': session_data['current_trial_step'],
        'scenario_id': session_data['scenario_id'],
        'max_trials': session_data['max_trials'],
        'fund_returns': fund_returns,
        'allocations': allocations
    })
    return True

def _create_new_session(session_id):
    """Batch create new session with pre-loaded data"""
    scenarios = _fetch_scenario_config()
    scenario = np.random.choice(scenarios)
    
    st.session_state.update({
        'page': 'consent',
        'trial': 1,
        'trial_step': 1,
        'scenario_id': scenario['scenario_id'],
        'max_trials': scenario['num_trials'],
        'fund_returns': {},
        'allocations': {1: {'initial': None, 'ai': None, 'final': None}},
        'fund_returns_data': _fetch_fund_returns(scenario['scenario_id']),
        'ai_recommendations_data': _fetch_ai_recommendations(scenario['scenario_id'])
    })

    supabase.table('sessions').insert({
        'session_id': session_id,
        'scenario_id': scenario['scenario_id'],
        'current_page': 'consent',
        'current_trial': 0,
        'current_trial_step': 1,
        'created_at': datetime.now().isoformat(),
        'max_trials': scenario['num_trials']
    }).execute()