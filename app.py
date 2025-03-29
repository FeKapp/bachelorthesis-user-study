import streamlit as st
from modules.session import initialize_session_state
from modules.components.progress import show_progress
from modules.subpages import (
    consent,
    intro,
    demographics,
    trial_steps,
    demo,
    final
)

def main():
    session_id = initialize_session_state()
    
    if st.session_state.page == 'consent':
        consent.show_consent(session_id)
    elif st.session_state.page == 'intro':
        intro.show_intro(session_id)
    elif st.session_state.page == 'demo':
        if st.session_state.trial_step == 1:
            demo.show_demo_initial(session_id)
        elif st.session_state.trial_step == 2:
            demo.show_demo_ai(session_id)
        elif st.session_state.trial_step == 3:
            demo.show_demo_performance(session_id)
    elif st.session_state.page == 'trial':
        if st.session_state.trial_step == 1:
            trial_steps.show_initial_allocation(session_id, st.session_state.trial)
        elif st.session_state.trial_step == 2:
            trial_steps.show_ai_recommendation(
                session_id,
                st.session_state.trial,
                st.session_state.scenario_id,
                st.session_state.allocations
            )
        elif st.session_state.trial_step == 3:
            trial_steps.show_performance(
                session_id,
                st.session_state.trial,
                st.session_state.fund_returns,
                st.session_state.allocations
            )
    elif st.session_state.page == 'final':
        final.show_final(session_id, st.session_state.max_trials, st.session_state.fund_returns_data)
    elif st.session_state.page == 'debrief':
        final.show_debrief(session_id)

    if st.session_state.page not in ['consent', 'intro', 'demo']:
        show_progress()
        
if __name__ == "__main__":
    main()