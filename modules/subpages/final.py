import streamlit as st
from modules.database import save_allocation, save_demographics

def show_final(session_id, max_trials, fund_returns):
    st.title("Final Allocation")
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/images/fund_A.png", width=200)
        final_a = st.number_input("Fund A (%)", 0, 100, 50)
    with col2:
        st.image("assets/images/fund_B.png", width=200)
        st.write(f"Fund B: {100 - final_a}%")

    if st.button("Submit"):
        return_a, return_b = fund_returns.get(max_trials, (0.11, 0.03))
        portfolio_return = (final_a/100*return_a + (100-final_a)/100*return_b)
        save_allocation(session_id, max_trials, 'final', final_a, 100-final_a, portfolio_return)
        st.session_state.page = 'debrief'
        st.rerun()

def show_debrief(session_id):
    st.title("Study Complete")
    with st.form(key="debrief"):
        # Debrief form elements
        if st.form_submit_button("Submit"):
            save_demographics(session_id, {})  # Add actual demographics data
            st.success("Thank you!")
            st.balloons()