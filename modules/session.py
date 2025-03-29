import streamlit as st
import numpy as np
import uuid
from datetime import datetime
from modules.database import supabase, load_session_data, update_session_progress

def init_session():
    """
    - Checks if a session_id is already in st.query_params.
    - If not, sets a new session_id and reruns.
    - Then checks if there's an existing session in the DB or creates a new one.
    - Updates st.session_state accordingly.
    """
    # Check if session_id is in query params
    session_id = st.query_params.get("session_id") or str(uuid.uuid4())
    if "session_id" not in st.query_params:
        st.query_params["session_id"] = session_id
        st.rerun()

    # Attempt to load existing session
    session_response = supabase.table('sessions') \
        .select('*') \
        .eq('session_id', session_id) \
        .execute()

    if session_response.data:
        # Session exists, load data from DB
        session_data = session_response.data[0]
        fund_returns = {}
        allocations = {}

        trials_response = supabase.table('trials') \
            .select('*') \
            .eq('session_id', session_id) \
            .execute()

        for trial in trials_response.data:
            fund_returns[trial['trial_number']] = (trial['return_a'], trial['return_b'])

            alloc_response = supabase.table('allocations') \
                .select('*') \
                .eq('trial_id', trial['trial_id']) \
                .execute()

            allocations[trial['trial_number']] = {'initial': None, 'ai': None, 'final': None}
            for alloc in alloc_response.data:
                allocations[trial['trial_number']][alloc['allocation_type']] = (
                    alloc['fund_a'],
                    alloc['fund_b']
                )

        st.session_state.update({
            'page': session_data['current_page'],
            'trial': session_data['current_trial'],
            'trial_step': session_data['current_trial_step'],
            'scenario_id': session_data['scenario_id'],
            'max_trials': session_data['max_trials'],
            'fund_returns': fund_returns,
            'allocations': allocations
        })

    else:
        # Create a new session in the DB
        scenario_res = supabase.table('scenario_config').select('*').execute()
        scenarios = scenario_res.data
        selected_scenario = np.random.choice(scenarios)

        fr_res = supabase.table('fund_returns') \
            .select('*') \
            .eq('scenario_id', selected_scenario['scenario_id']) \
            .execute()

        ai_res = supabase.table('ai_recommendations') \
            .select('*') \
            .eq('scenario_id', selected_scenario['scenario_id']) \
            .execute()

        # Insert new session row
        session_data = {
            'session_id': session_id,
            'scenario_id': selected_scenario['scenario_id'],
            'current_page': 'consent',
            'current_trial': 0,
            'current_trial_step': 1,
            'created_at': datetime.now().isoformat(),
            'max_trials': selected_scenario['num_trials']
        }
        supabase.table('sessions').insert(session_data).execute()

        # Update st.session_state
        st.session_state.update({
            'page': 'consent',
            'trial': 1,
            'trial_step': 1,
            'scenario_id': selected_scenario['scenario_id'],
            'max_trials': selected_scenario['num_trials'],
            'fund_returns': {},
            'allocations': {},
            'fund_returns_data': {
                fr['trial_number']: (fr['return_a'], fr['return_b'])
                for fr in fr_res.data
            },
            'ai_recommendations_data': {
                ai['trial_number']: (ai['fund_a'], ai['fund_b'])
                for ai in ai_res.data
            }
        })

    # Optional: update session progress in DB
    update_session_progress(session_id)
