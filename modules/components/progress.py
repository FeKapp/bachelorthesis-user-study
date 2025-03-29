import streamlit as st

def show_progress():
    progress = min(st.session_state.trial / st.session_state.max_trials, 1.0)
    with st.container():
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.progress(progress)
        st.caption(f"Study progress: {int(progress*100)}% complete")