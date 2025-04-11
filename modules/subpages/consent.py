import streamlit as st
import os
from modules.database import supabase
from modules.session import update_session_progress

def show_consent():
    st.title("Welcome!")

    # Container with introduction & consent text
    with st.container():
        # Load and display introduction text
        intro_file_path = os.path.join("assets", "text", "introduction.txt")
        intro_text = load_text(intro_file_path)
        st.markdown(intro_text)
        st.markdown("---")

        # Load and display consent text
        consent_file_path = os.path.join("assets", "text", "consent.txt")
        consent_text = load_text(consent_file_path)
        


        # Consent form
        with st.form(key="consent_form"):
            st.markdown(consent_text)   

            # Display the clickable text that expands to show more information
            with st.expander("Obtain more information about the processing of your personal data"):
                data_processing_file_path = os.path.join("assets", "text", "data_processing.txt")
                data_processing_text = load_text(data_processing_file_path)
                st.markdown(data_processing_text)

            consent_given = st.checkbox(
                "I agree to the consent form and to the processing of my personal data in accordance with the information provided herein."
            )
            submitted = st.form_submit_button("Continue")
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

def load_text(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()