import streamlit as st
import os
import numpy as np
from modules.database import update_session_progress

def show_intro(session_id):
    st.title("Experiment Description")
    
    # Load intro text from file
    intro_file_path = os.path.join("assets", "text", "experiment_description.txt")
    with open(intro_file_path, "r", encoding="utf-8") as f:
        intro_text = f.read()
    st.write(intro_text)
    
    if st.button("Start Experiment"):
        # Generate random demo data
        st.session_state.demo_data = {
            'ai_a': np.random.randint(0, 101),
            'return_a': np.random.uniform(-0.1, 0.2),
            'return_b': np.random.uniform(-0.1, 0.2),
        }
        st.session_state.demo_data['ai_b'] = 100 - st.session_state.demo_data['ai_a']
        
        # Update session state
        st.session_state.update({
            'page': 'demo',
            'trial_step': 1,
            'trial': 1
        })
        
        # Update database
        update_session_progress(
            session_id,
            page='demo',
            trial=st.session_state.trial,
            trial_step=st.session_state.trial_step
        )
        
        st.rerun()