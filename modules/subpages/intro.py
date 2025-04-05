import streamlit as st
import os
import numpy as np
from modules.database import supabase
from modules.database import update_session_progress

def show_intro():
    st.title("Experiment Description")

    # Get the session State Scenario
    scenario = st.session_state.get('scenario_id')
    # Insert the scenario_id for the scenario "long" from the database
    if scenario == '2e1e164a-699c-4c00-acff-61a98e23ddec' or 'b8426ff5-c6f2-4f25-a259-764e993ffa29':
        intro_file_path = os.path.join("assets", "text", "100trial_experiment_description.txt")
    else:
        intro_file_path = os.path.join("assets", "text", "5trial_experiment_description.txt")

    with open(intro_file_path, "r", encoding="utf-8") as f:
        intro_text = f.read()
    st.write(intro_text)

    if st.button("Start Demo"):
        # Generate random demo data
        st.session_state.demo_data = {
            'ai_a': np.random.randint(0, 101),
            'return_a': np.random.uniform(-0.1, 0.2),
            'return_b': np.random.uniform(-0.1, 0.2),
        }
        st.session_state.demo_data['ai_b'] = 100 - st.session_state.demo_data['ai_a']
        st.session_state.page = 'demo'
        st.session_state.trial_step = 1

        # Immediately update the DB to reflect "demo"
        supabase.table('sessions').update({
            'current_page': 'demo',
            'current_trial': st.session_state.trial,
            'current_trial_step': st.session_state.trial_step
        }).eq('session_id', st.query_params['session_id']).execute()

        st.rerun()       