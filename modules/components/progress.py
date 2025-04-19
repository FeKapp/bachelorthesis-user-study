import streamlit as st

def show_progress():
    if st.session_state.page == 'debrief':
        progress = 1.0
    else:
        progress = min((st.session_state.trial - 1) / st.session_state.max_trials, 1.0)

    # Add custom CSS for the progress bar
    st.markdown("""
    <style>
        .stProgress > div > div > div > div {
            background-color: #0056b3;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.progress(progress, "Study progress:")