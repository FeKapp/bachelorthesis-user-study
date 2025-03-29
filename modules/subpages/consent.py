import streamlit as st
from modules.database import supabase
from modules.session import update_session_progress

def show_consent():
    st.title("Welcome!")

    # Container with introduction & consent text
    with st.container():
        intro_file_path = "assets/text/introduction.txt"
        consent_file_path = "assets/text/consent.txt"

        # Load intro text
        with open(intro_file_path, "r", encoding="utf-8") as i:
            intro_text = i.read()
        st.markdown(intro_text)
        st.markdown("---")

        # Load consent text
        with open(consent_file_path, "r", encoding="utf-8") as f:
            consent_text = f.read()
        st.markdown(consent_text)

        # Consent form
        with st.form(key="consent_form"):
            consent_given = st.checkbox(
                "I agree to the consent form and to the processing of my personal data in accordance with the information provided herein."
            )
            submitted = st.form_submit_button("Agree & Continue")
            if submitted:
                if consent_given:
                    # Update sessions table
                    supabase.table('sessions').update({
                        'consent_given': True,
                        'current_page': 'intro'
                    }).eq('session_id', st.query_params['session_id']).execute()

                    st.session_state.page = 'intro'
                    st.rerun()
                else:
                    st.error("You must agree to participate to continue.")
