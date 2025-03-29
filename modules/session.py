import streamlit as st
import uuid
import numpy as np
from datetime import datetime
from modules.database import supabase

def initialize_session_state():
    session_id = st.query_params.get("session_id") or str(uuid.uuid4())
    if "session_id" not in st.query_params:
        st.query_params["session_id"] = session_id
        st.rerun()

    # Load or create session
    session_response = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
    
    if not session_response.data:
        # Create new session with scenario data
        scenario_res = supabase.table('scenario_config').select('*').execute()
        selected_scenario = np.random.choice(scenario_res.data)
        
        # Load FUND RETURNS and AI RECOMMENDATIONS for the scenario
        fr_res = supabase.table('fund_returns').select('*').eq('scenario_id', selected_scenario['scenario_id']).execute()
        ai_res = supabase.table('ai_recommendations').select('*').eq('scenario_id', selected_scenario['scenario_id']).execute()
        
        # Initialize session state with PROPER TRIAL NUMBERING (1-based)
        st.session_state.update({
            'page': 'consent',
            'trial': 1,  # Start at first trial
            'trial_step': 1,
            'scenario_id': selected_scenario['scenario_id'],
            'max_trials': selected_scenario['num_trials'],
            'fund_returns': {},
            'allocations': {},
            'fund_returns_data': {fr['trial_number']: (fr['return_a'], fr['return_b']) for fr in fr_res.data},
            'ai_recommendations_data': {ai['trial_number']: (ai['fund_a'], ai['fund_b']) for ai in ai_res.data}
        })
        
        # Create session record
        supabase.table('sessions').insert({
            'session_id': session_id,
            'scenario_id': selected_scenario['scenario_id'],
            'current_page': 'consent',
            'current_trial': 1,
            'current_trial_step': 1,
            'max_trials': selected_scenario['num_trials'],
            'created_at': datetime.now().isoformat()
        }).execute()
    else:
        # Load existing session with PROPER TRIAL NUMBER HANDLING
        session_data = session_response.data[0]
        
        # Load trials and allocations
        trials_response = supabase.table('trials').select('*').eq('session_id', session_id).execute()
        allocations = {}
        fund_returns = {}
        
        for trial in trials_response.data:
            # Trial numbers are 1-based in database
            trial_num = trial['trial_number']
            
            # Get allocations for this trial
            alloc_response = supabase.table('allocations').select('*').eq('trial_id', trial['trial_id']).execute()
            allocations[trial_num] = {'initial': None, 'ai': None, 'final': None}
            
            for alloc in alloc_response.data:
                alloc_type = alloc['allocation_type']
                allocations[trial_num][alloc_type] = (alloc['fund_a'], alloc['fund_b'])
            
            # Store fund returns if available
            if trial['return_a'] and trial['return_b']:
                fund_returns[trial_num] = (trial['return_a'], trial['return_b'])
        
        # Initialize session state with 1-BASED TRIAL NUMBERS
        st.session_state.update({
            'page': session_data['current_page'],
            'trial': session_data['current_trial'],
            'trial_step': session_data['current_trial_step'],
            'scenario_id': session_data['scenario_id'],
            'max_trials': session_data['max_trials'],
            'fund_returns': fund_returns,
            'allocations': allocations,
            'fund_returns_data': {},  # Loaded only for new sessions
            'ai_recommendations_data': {}  # Loaded only for new sessions
        })
    
    return session_id
