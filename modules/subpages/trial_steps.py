import streamlit as st
import os
import pandas as pd
from modules.database import supabase, update_session_progress, save_allocation
from modules.components.charts import create_performance_bar_chart

# Cache expensive chart creation
@st.cache_data(max_entries=100)
def cached_performance_chart(df):
    return create_performance_bar_chart(df, margin=dict(t=20, b=20))

def handle_trial_steps():
    session_id = st.query_params['session_id']
    
    if st.session_state.trial >= st.session_state.max_trials:
        st.session_state.page = 'final'
        update_session_progress(session_id)
        st.rerun()

    step_handlers = {
        1: show_initial_allocation,
        2: show_ai_recommendation,
        3: show_performance
    }
    step_handlers.get(st.session_state.trial_step, show_initial_allocation)()

def show_initial_allocation():
    session_id = st.query_params['session_id']
    current_trial = st.session_state.trial
    scenario_id = st.session_state.scenario_id
    
    # Get period information from scenario_config
    periods = "3 months" if st.session_state.max_trials == 100 else "5 years"
    
    # st.title(f"Trial {current_trial} - Step 1: Initial Allocation")
    st.title(f"Step 1: Initial Allocation")
    st.markdown(f"Please allocate your assets for the **next {periods}**.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## Fund A")
        st.image(os.path.join("assets", "images", "fund_A.png"), width=200)
        initial_a = st.number_input("Allocation to Fund A (%)", 
                                  min_value=0, max_value=100, 
                                  value=None, key=f"initial_a_{current_trial}")
        
    with col2:
        st.markdown("## Fund B")
        st.image(os.path.join("assets", "images", "fund_B.png"), width=200)
        initial_b = 100 - initial_a if initial_a is not None else 0
        st.number_input("Automatic allocation to Fund B (%)", 
                      min_value=0, max_value=100, 
                      value=initial_b, key=f"initial_b_{current_trial}", disabled=True)

    if st.button("Submit Allocation", key=f"initial_btn_{current_trial}"):
        if initial_a is None:
            st.error("Allocation to Fund A (0% - 100%) is required.")
            return

        # Save allocation and create trial record
        save_allocation(session_id, current_trial, 'initial', initial_a, initial_b)
        
        # Update session state
        st.session_state.trial_step = 2
        st.session_state.allocations[current_trial] = {
            'initial': (initial_a, initial_b),
            'ai': None,
            'final': None
        }
        update_session_progress(session_id)
        st.rerun()

def show_ai_recommendation():
    session_id = st.query_params['session_id']
    current_trial = st.session_state.trial
    scenario_id = st.session_state.scenario_id
    
    # st.title(f"Trial {current_trial} - Step 2: AI Recommendation")
    st.title(f"Step 2: AI Recommendation")

    # Get pre-loaded AI recommendation
    try:
        ai_data = st.session_state.ai_recommendations_data[current_trial]
    except KeyError:
        st.error("Missing AI recommendation data!")
        st.stop()

    # Check for instructed trial
    is_instructed = (
        (st.session_state.max_trials == 5 and current_trial == 3) or
        (st.session_state.max_trials == 100 and current_trial == 79)
    )

    # Save AI recommendation if not exists
    if not st.session_state.allocations[current_trial]['ai']:
        ai_a, ai_b = (55, 45) if is_instructed else ai_data
        save_allocation(session_id, current_trial, 'ai', ai_a, ai_b)
        st.session_state.allocations[current_trial]['ai'] = (ai_a, ai_b)

    # Display allocations
    initial_a, initial_b = st.session_state.allocations[current_trial]['initial']
    ai_a, ai_b = st.session_state.allocations[current_trial]['ai']

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Your Allocation")
            st.metric("Fund A:", f"{initial_a}%")
            st.metric("Fund B:", f"{initial_b}%")
        
    with col2:
        with st.container(border=True):
            st.subheader("AI Recommendation ✨")
            if is_instructed:
                st.markdown("""
                    **Special Instruction** For this trial only:  
                    You **MUST** allocate **exactly 55% to Fund A** and 45% to **Fund B**  
                    This is a test of following instructions and does not affect your performance.
                    The real AI recommendation will be shown after you submit this trial.
                """)
            st.metric("Fund A:", f"{ai_a}%")
            st.metric("Fund B:", f"{ai_b}%")

    # Final allocation input
    st.markdown("---")
    st.markdown("Based on your initial allocation and the AI recommendation, how do you allocate your assets?")
    
    col3, col4 = st.columns(2)
    with col3:
        adjusted_a = st.number_input("Final Allocation to Fund A (%)", 
                               min_value=0, max_value=100, 
                               value=None, key=f"final_a_{current_trial}")

    with col4:
        adjusted_b = 100 - adjusted_a if adjusted_a is not None else 0
        st.number_input("Automatic allocation to Fund B (%)", 
                      min_value=0, max_value=100, 
                      value=adjusted_b, key=f"initial_b_{current_trial}", disabled=True)

    
    if st.button("Submit Allocation", key=f"final_btn_{current_trial}"):
        if adjusted_a is None:
            st.error("Allocation to Fund A is required.")
            return

        # Save final allocation
        save_allocation(session_id, current_trial, 'final', adjusted_a, adjusted_b)
        st.session_state.allocations[current_trial]['final'] = (adjusted_a, adjusted_b)

        # Handle instructed trial
        if is_instructed:
            supabase.table('sessions').update({
                'instructed_response_2_passed': adjusted_a == 55
            }).eq('session_id', session_id).execute()

        # Move to next step
        st.session_state.trial_step = 3
        update_session_progress(session_id)
        st.rerun()

def show_performance():
    session_id = st.query_params['session_id']
    current_trial = st.session_state.trial
    scenario_id = st.session_state.scenario_id
    
    # Get returns from pre-loaded fund_returns data
    return_a, return_b = st.session_state.fund_returns_data[current_trial]
    
    # Get allocations
    alloc = st.session_state.allocations[current_trial]
    final_a, final_b = alloc['final']
    ai_a, ai_b = alloc['ai']

    # Calculate returns
    final_return = (final_a/100)*return_a + (final_b/100)*return_b
    ai_return = (ai_a/100)*return_a + (ai_b/100)*return_b

    # Create performance data
    df = pd.DataFrame({
        'Category': ['Fund A', 'Fund B', 'AI Portfolio', 'Your Portfolio'],
        'Performance': [return_a*100, return_b*100, ai_return*100, final_return*100]
    })

    # Display section
    # st.title(f"Trial {current_trial} - Step 3: Performance")
    st.title(f"Step 3: Performance")

    duration = "last 3 months" if st.session_state.max_trials == 100 else "last 5 years"

    st.markdown(f"""
    Allocation breakdown:
    - Your Portfolio: **Fund A**: {final_a}%, **Fund B**: {final_b}%
    - AI portfolio: **Fund A**: {ai_a}%, **Fund B**: {ai_b}%
    
    Overview how Fund A, Fund B, the AI portfolio and your portfolio performed in the **{duration}**:
    """)
    
    st.plotly_chart(cached_performance_chart(df), use_container_width=True)

    # Next trial button
    btn_label = "Continue to next trial" if current_trial < st.session_state.max_trials else "Finish"
    if st.button(btn_label, key=f"continue_{current_trial}"):
        if current_trial < st.session_state.max_trials:
            st.session_state.trial += 1
            st.session_state.trial_step = 1
        else:
            st.session_state.page = 'final'
        update_session_progress(session_id)
        st.rerun()