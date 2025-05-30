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
    try:
        # 1) Initialize or load session
        init_session()

        # 2) Route the user to the correct "page"
        page = st.session_state.page
        if page == 'consent':
            show_consent()
        elif page == 'intro':
            show_intro()
        elif page == 'demo':
            handle_demo_steps()
        elif page == 'trial':
            handle_trial_steps()
        elif page == 'final':
            show_final()
        elif page == 'debrief':
            show_debrief()

        # 3) Show the progress bar on all pages except these
        if page not in ['consent', 'intro', 'demo']:
            show_progress()

    except Exception as e:
        st.error(
            f"""⚠️ An unexpected error occurred:
            {str(e)} \n\n
            Please try to reload the page, switch browser, or press Enter after entering a value in Field A to ensure allocations to Fund B are updated automatically."""
        )
    
if __name__ == "__main__":
    main()
