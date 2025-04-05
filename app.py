import streamlit as st
from modules.session import init_session
from modules.subpages.consent import show_consent
from modules.subpages.demo import handle_demo_steps
from modules.subpages.intro import show_intro
from modules.subpages.trial_steps import handle_trial_steps
from modules.subpages.final import show_final
from modules.subpages.debrief import show_debrief
from modules.components.progress import show_progress

def main():
    # 1) Initialize or load session
    init_session()

    # 2) Route the user to the correct "page"
    # page = st.session_state.page
    # if page == 'consent':
    #     show_consent()
    # elif page == 'intro':
    #     show_intro()
    # elif page == 'demo':
    #     handle_demo_steps()
    # elif page == 'trial':
    #     handle_trial_steps()
    # elif page == 'final':
    #     show_final()
    # elif page == 'debrief':
    #     show_debrief()

    handle_demo_steps()

    # 3) Show the progress bar on all pages except these
    if page not in ['consent', 'intro', 'demo']:
        show_progress()

if __name__ == "__main__":
    main()
