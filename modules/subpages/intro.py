import streamlit as st
from streamlit.components.v1 import html
import os
import numpy as np
from modules.database import supabase
from streamlit_scroll_to_top import scroll_to_here

def scroll_to_top():
    # inject a tiny iframe/html snippet with your JS
    html(
        """
        <script>
          // Find the <main> container and scroll it to 0,0 immediately
          const main = window.parent.document.querySelector('main');
          if (main) {
            main.scroll(0, 0);
          }
        </script>
        """,
        height=0,
        width=0,
    )
    
def show_intro():
    st.title("Experiment Description")

    scroll_to_here(0, key='top')       # Scroll to 0 px (top)
    st.session_state.to_top = False

    # Get the session State Scenario
    scenario = st.session_state.get('scenario_id')
    # Insert the scenario_id for the scenario "long" from the database
    if st.session_state.max_trials == 100:
        intro_file_path = os.path.join("assets", "text", "100trial_experiment_description.txt")
    else:
        intro_file_path = os.path.join("assets", "text", "5trial_experiment_description.txt")

    with open(intro_file_path, "r", encoding="utf-8") as f:
        intro_text = f.read()
    st.write(intro_text)

    read_instructions = st.checkbox(
                "Confirm that you have read the experiment description."
            )
    
    if st.button("Start Demo"):
        # Generate random demo data
        if read_instructions is False:
            st.error("Please confirm that you have read the instructions to continue.")
        else:
            st.session_state.demo_data = {
                'ai_a': np.random.randint(40, 61),
                'return_a': np.random.uniform(0, 0.1),
                'return_b': np.random.uniform(0, 0.1),
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