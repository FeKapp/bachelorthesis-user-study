# main.py
import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import uuid
import os

# Import our DB helpers
from db import (
    get_or_create_session, update_session, create_trial, create_allocation,
    fetch_latest_trial, give_consent
)

# ========== STEP 1: Handle or Generate Session ID =============
query_params = st.experimental_get_query_params()
session_id = query_params.get("session_id", [None])[0]

if not session_id:
    session_id = str(uuid.uuid4())
    st.experimental_set_query_params(session_id=session_id)

# ========== STEP 2: Initialize or Load Session from DB =============
# If it's a new session, we randomly pick scenario, ai_type, etc.
if "session_data_loaded" not in st.session_state:
    scenario = np.random.choice(['short_unbiased', 'short_biased', 'long_unbiased', 'long_biased'])
    max_trials = 100 if 'long' in scenario else 5
    ai_type = 'biased' if 'biased' in scenario else 'unbiased'

    # Create or fetch row from DB
    session_row = get_or_create_session(
        session_id=session_id,
        scenario=scenario,
        ai_type=ai_type,
        max_trials=max_trials,
        page="intro",
        trial=0,
        trial_step=1
    )

    # Load relevant fields into st.session_state
    st.session_state["scenario"] = session_row["scenario"]
    st.session_state["ai_type"] = session_row["ai_type"]
    st.session_state["max_trials"] = session_row["max_trials"]
    st.session_state["page"] = session_row["current_page"] or "intro"
    st.session_state["trial"] = session_row["current_trial"] or 0
    st.session_state["trial_step"] = session_row["current_trial_step"] or 1

    st.session_state["session_data_loaded"] = True
else:
    # If user navigates around, we assume st.session_state is up to date 
    # But you might also fetch from DB to re-sync
    pass

# ========== STEP 3: Define Page Functions =============

def show_progress():
    progress = min(st.session_state["trial"] / st.session_state["max_trials"], 1.0)
    with st.container():
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.progress(progress)
        st.caption(f"Study progress: {int(progress*100)}% complete")

def show_intro():
    st.title("Fund Allocation Study")
    st.write("""
    **Welcome to the investment study!**
    
    You will complete multiple rounds of:
    1. Initial allocation
    2. AI recommendation review
    3. Performance analysis
    
    Funds available:
    - Fund A (High Risk/Return): 11% mean, 15% stdev
    - Fund B (Low Risk/Return): 3% mean, 5% stdev
    """)
    if st.button("Begin Study"):
        st.session_state["page"] = "trial"
        update_session(session_id, current_page="trial")
        st.experimental_rerun()

def show_initial_allocation():
    trial_number = st.session_state["trial"] + 1
    st.title(f"Trial {trial_number} - Step 1: Initial Allocation")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Fund A")
        init_key = f"initial_a_{st.session_state['trial']}"
        initial_a = st.number_input("Allocation to Fund A (%)", 0, 100, 50, key=init_key)
    with col2:
        st.subheader("Fund B")
        initial_b = 100 - st.session_state[init_key]
        st.write(f"Automatic allocation: {initial_b}%")

    if st.button("Submit Initial Allocation"):
        # Insert an allocation row in DB with allocation_type='initial'
        # First, we need a trial row in `trials` if it doesn't exist yet
        existing_trial = fetch_latest_trial(session_id, st.session_state["trial"])
        if not existing_trial:
            # We haven't assigned returns yet, so let's do that
            return_a = np.random.normal(0.11, 0.15)
            return_b = np.random.normal(0.03, 0.05)
            trial_id = create_trial(session_id, st.session_state["trial"], return_a, return_b)
        else:
            trial_id = existing_trial["trial_id"]
        
        create_allocation(
            trial_id=trial_id,
            allocation_type="initial",
            fund_a=initial_a,
            fund_b=initial_b
        )

        st.session_state["trial_step"] = 2
        update_session(session_id, current_trial_step=2)
        st.experimental_rerun()

def show_ai_recommendation():
    trial_number = st.session_state["trial"] + 1
    st.title(f"Trial {trial_number} - Step 2: AI Recommendation")

    # Fetch the existing trial row
    existing_trial = fetch_latest_trial(session_id, st.session_state["trial"])
    if not existing_trial:
        st.error("No trial found! Something went wrong.")
        return

    # Now create or set AI allocation if not already stored
    ai_a_key = f"ai_a_{st.session_state['trial']}"
    if ai_a_key not in st.session_state:
        # If biased, recommend 100% B. Otherwise random
        if st.session_state["ai_type"] == "biased":
            st.session_state[ai_a_key] = 0
        else:
            st.session_state[ai_a_key] = np.random.randint(0, 101)

    ai_a = st.session_state[ai_a_key]
    ai_b = 100 - ai_a

    # We also need the "initial" allocation from the DB if we want to show it
    # For brevity, let's just store them in session_state (but you can fetch from DB).
    initial_a_key = f"initial_a_{st.session_state['trial']}"
    initial_a = st.session_state[initial_a_key]
    initial_b = 100 - initial_a

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your Initial Allocation")
        st.write(f"Fund A: {initial_a}%")
        st.write(f"Fund B: {initial_b}%")
    with col2:
        st.subheader("AI Recommendation")
        st.write(f"Fund A: {ai_a}%")
        st.write(f"Fund B: {ai_b}%")

    st.subheader("Adjust Your Allocation")
    final_key = f"adjusted_a_{st.session_state['trial']}"
    adjusted_a = st.number_input("Revised allocation to Fund A (%)", 0, 100, initial_a, key=final_key)
    adjusted_b = 100 - adjusted_a
    st.write(f"Revised Fund B allocation: {adjusted_b}%")

    if st.button("Submit Final Allocation"):
        # Insert an allocation row in DB with allocation_type='final'
        create_allocation(
            trial_id=existing_trial["trial_id"],
            allocation_type="final",
            fund_a=adjusted_a,
            fund_b=adjusted_b
        )

        # We already have returns in the trial row (return_a, return_b).
        # The portfolio_return is: (adjusted_a/100)*return_a + (adjusted_b/100)*return_b
        # Let's store that as well with a separate "final_portfolio" type or just update the "final" row:
        r_a = existing_trial["return_a"]
        r_b = existing_trial["return_b"]
        portfolio_return = (adjusted_a/100) * r_a + (adjusted_b/100) * r_b

        # We could do an update or create a new allocation row "final_result" if needed
        # For simplicity, let's update the same "final" allocation row right after we create it.
        # A simpler approach is to create it with the portfolio_return right away:
        create_allocation(
            trial_id=existing_trial["trial_id"],
            allocation_type="final_result",
            fund_a=adjusted_a,
            fund_b=adjusted_b,
            portfolio_return=portfolio_return
        )

        st.session_state["trial_step"] = 3
        update_session(session_id, current_trial_step=3)
        st.experimental_rerun()

def show_performance():
    trial_number = st.session_state["trial"] + 1
    st.title(f"Trial {trial_number} - Step 3: Performance")

    # You can fetch the existing_trial data from the DB
    existing_trial = fetch_latest_trial(session_id, st.session_state["trial"])
    if not existing_trial:
        st.error("No trial found!")
        return
    return_a = existing_trial["return_a"]
    return_b = existing_trial["return_b"]
    
    # We want the final allocation from DB. For brevity, let's just compute again from session.
    final_key = f"adjusted_a_{st.session_state['trial']}"
    final_a = st.session_state[final_key]
    final_b = 100 - final_a

    final_return = (final_a/100)*return_a + (final_b/100)*return_b

    chart_data = pd.DataFrame({
        'Returns': [return_a, return_b, final_return],
        'Category': ['Fund A', 'Fund B', 'Your Portfolio']
    }).set_index('Category')
    st.bar_chart(chart_data)

    btn_label = "Continue to Next Trial" if st.session_state["trial"] < st.session_state["max_trials"] - 1 else "Proceed to Final Allocation"
    if st.button(btn_label):
        # Next trial
        new_trial_number = st.session_state["trial"] + 1
        # Update session
        update_session(session_id, current_trial=new_trial_number, current_trial_step=1)
        st.session_state["trial"] = new_trial_number
        st.session_state["trial_step"] = 1

        # If we are done, we switch page
        if new_trial_number >= st.session_state["max_trials"]:
            st.session_state["page"] = "final"
            update_session(session_id, current_page="final")
        else:
            st.session_state["page"] = "trial"
            update_session(session_id, current_page="trial")

        st.experimental_rerun()

def show_final():
    st.title("Final Allocation")
    st.write("**This is your last investment decision**")

    final_a = st.number_input("Final allocation to Fund A (%)", 0, 100, 50)
    final_b = 100 - final_a

    if st.button("Submit Final Allocation"):
        # We can create a new final row in DB or do another approach
        existing_trial = fetch_latest_trial(session_id, st.session_state["trial"])
        if not existing_trial:
            # create a trial if it doesn't exist
            return_a = np.random.normal(0.11, 0.15)
            return_b = np.random.normal(0.03, 0.05)
            trial_id = create_trial(session_id, st.session_state["trial"], return_a, return_b)
        else:
            trial_id = existing_trial["trial_id"]
            return_a = existing_trial["return_a"]
            return_b = existing_trial["return_b"]

        portfolio_return = (final_a/100)*return_a + (final_b/100)*return_b
        create_allocation(
            trial_id=trial_id,
            allocation_type="final_allocation",
            fund_a=final_a,
            fund_b=final_b,
            portfolio_return=portfolio_return
        )

        st.session_state["page"] = "debrief"
        update_session(session_id, current_page="debrief")
        st.experimental_rerun()

def show_debrief():
    st.title("Study Complete")
    st.write("""
    **Thank you for participating!**

    Your responses have been recorded anonymously.
    """)

    if st.checkbox("I consent to my data being used for research purposes"):
        if st.button("Confirm Consent"):
            give_consent(session_id)
            st.success("Consent confirmed. Thank you!")
            st.balloons()

# ========== MAIN APP LOGIC ==========
def handle_trial_steps():
    if st.session_state["trial"] >= st.session_state["max_trials"]:
        st.session_state["page"] = "final"
        update_session(session_id, current_page="final")
        st.experimental_rerun()
    
    if st.session_state["trial_step"] == 1:
        show_initial_allocation()
    elif st.session_state["trial_step"] == 2:
        show_ai_recommendation()
    elif st.session_state["trial_step"] == 3:
        show_performance()

def main():
    page = st.session_state["page"]
    if page == "intro":
        show_intro()
    elif page == "trial":
        handle_trial_steps()
    elif page == "final":
        show_final()
    elif page == "debrief":
        show_debrief()

    if page != "intro":
        show_progress()

if __name__ == "__main__":
    main()
