import streamlit as st
import pandas as pd
from modules.database import save_allocation, update_session_progress
from modules.components.charts import performance_chart

def show_initial_allocation(session_id, trial_num):
    st.title(f"Trial {trial_num + 1} - Step 1: Initial Allocation")
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/images/fund_A.png", width=200)
        initial_a = st.number_input("Fund A (%)", 0, 100, 50, key=f"initial_a_{trial_num}")
    with col2:
        st.image("assets/images/fund_B.png", width=200)
        st.write(f"Fund B: {100 - initial_a}%")

    if st.button("Submit Initial Allocation"):
        save_allocation(session_id, trial_num, 'initial', initial_a, 100-initial_a)
        st.session_state.trial_step = 2
        update_session_progress(
            session_id,
            page='trial',
            trial=st.session_state.trial,
            trial_step=st.session_state.trial_step
        )
        st.rerun()

def show_ai_recommendation(session_id, trial_num, scenario_id, allocations):
    # Convert to 1-based trial number for database operations
    db_trial_num = trial_num + 1
    
    # Check if AI recommendation needs to be created
    if allocations.get(db_trial_num, {}).get('ai') is None:
        # Fetch AI recommendation from preloaded data
        ai_a, ai_b = st.session_state.ai_recommendations_data[db_trial_num]
        
        # Save AI recommendation to database
        from modules.database import save_allocation
        save_allocation(session_id, db_trial_num, 'ai', ai_a, ai_b)
        
        # Update local allocations
        allocations[db_trial_num] = allocations.get(db_trial_num, {'initial': None, 'ai': None, 'final': None})
        allocations[db_trial_num]['ai'] = (ai_a, ai_b)
    
    # Now safe to unpack
    ai_a, ai_b = allocations[db_trial_num]['ai']

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your Initial Allocation")
        st.write(f"Fund A: {allocations[trial_num]['initial'][0]}%")
        st.write(f"Fund B: {allocations[trial_num]['initial'][1]}%")
    with col2:
        st.subheader("✨ AI Recommendation")
        st.write(f"Fund A: {ai_a}%")
        st.write(f"Fund B: {ai_b}%")

    adjusted_a = st.number_input("Revised allocation", 0, 100, ai_a, key=f"adjusted_a_{trial_num}")
    
    if st.button("Submit Final Allocation"):
        save_allocation(session_id, trial_num, 'final', adjusted_a, 100-adjusted_a)
        st.session_state.trial_step = 3
        update_session_progress(
            session_id,
            page='trial',
            trial=st.session_state.trial,
            trial_step=st.session_state.trial_step
        )
        st.rerun()

def show_performance(session_id, trial_num, fund_returns, allocations):
    st.title(f"Trial {trial_num + 1} - Step 3: Performance")
    return_a, return_b = fund_returns[trial_num]
    final_a, final_b = allocations[trial_num]['final']
    
    performance_data = {
        'Fund A': return_a * 100,
        'Fund B': return_b * 100,
        'AI Portfolio': (allocations[trial_num]['ai'][0]/100*return_a + 
                        allocations[trial_num]['ai'][1]/100*return_b) * 100,
        'Your Portfolio': (final_a/100*return_a + final_b/100*return_b) * 100
    }
    
    st.plotly_chart(performance_chart(pd.DataFrame({
        'Category': list(performance_data.keys()),
        'Performance': list(performance_data.values())
    })), use_container_width=True)

    btn_label = "Continue" if trial_num < st.session_state.max_trials-1 else "Finish"
    if st.button(btn_label):
        st.session_state.trial += 1
        st.session_state.trial_step = 1
        update_session_progress(
            session_id,
            page='trial' if trial_num < st.session_state.max_trials-1 else 'final',
            trial=st.session_state.trial,
            trial_step=st.session_state.trial_step
        )
        st.rerun()