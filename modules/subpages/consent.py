import streamlit as st
import os
from modules.database import supabase, update_session_progress

def show_consent(session_id):
    st.title("Welcome!")
    
    with st.container(border=True):
        intro_file_path = os.path.join("assets", "text", "introduction.txt")
        with open(intro_file_path, "r", encoding="utf-8") as i:
            intro_text = i.read()
        st.markdown(intro_text)

        st.markdown("---")
        
        consent_file_path = os.path.join("assets", "text", "consent.txt")
        with open(consent_file_path, "r", encoding="utf-8") as f:
            consent_text = f.read()
        st.markdown(consent_text)
    
    with st.form(key="consent_form"):
        consent_given = st.checkbox("I agree to participate...")
        submitted = st.form_submit_button("Agree & Continue")
        if submitted and consent_given:
            update_session_progress(session_id, 'intro', 0, 1)
            st.session_state.page = 'intro'
            st.rerun()
        elif submitted:
            st.error("You must agree to participate to continue.")