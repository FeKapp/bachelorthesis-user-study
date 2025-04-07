import streamlit as st

def show_progress():
    if st.session_state.page == 'debrief':
        progress = 1.0
    else:
        progress = min((st.session_state.trial - 1) / st.session_state.max_trials, 1.0)

    with st.container():
        # st.markdown("<br><br>", unsafe_allow_html=True)
        # st.caption(f"Study progress: {int(progress * 100)}% complete")
        st.caption(f"Study progress:")
        st.progress(progress)
        
