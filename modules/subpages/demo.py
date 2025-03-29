import streamlit as st
import numpy as np
import pandas as pd
from modules.database import update_session_progress
from modules.components.charts import performance_chart

def show_demo_initial(session_id):
    st.title("Demo: Initial Allocation")
    col1, col2 = st.columns(2)
    with col1:
        st.image("assets/images/fund_A.png", width=200)
        demo_initial_a = st.number_input("Fund A (%)", 0, 100, 50, key="demo_initial_a")
    with col2:
        st.image("assets/images/fund_B.png", width=200)
        st.write(f"Fund B: {100 - demo_initial_a}%")

    if st.button("Next: AI Recommendation Demo"):
        st.session_state.trial_step = 2
        update_session_progress(
            session_id,
            page='demo',
            trial=st.session_state.trial,
            trial_step=st.session_state.trial_step
        )
        st.rerun()

def show_demo_ai(session_id):
    st.title("Demo: AI Recommendation")
    ai_a = np.random.randint(0, 101)
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your Initial Allocation")
        st.write("Fund A: 50%")
        st.write("Fund B: 50%")
    with col2:
        st.subheader("✨ AI Recommendation")
        st.write(f"Fund A: {ai_a}%")
        st.write(f"Fund B: {100 - ai_a}%")

    adjusted_a = st.number_input("Revised allocation", 0, 100, ai_a, key="demo_adjusted_a")
    
    if st.button("Next: Performance Demo"):
        st.session_state.demo_data = {'ai_a': ai_a, 'ai_b': 100-ai_a}
        st.session_state.trial_step = 3
        update_session_progress(
            session_id,
            page='demo',
            trial=st.session_state.trial,
            trial_step=st.session_state.trial_step
        )
        st.rerun()

def show_demo_performance(session_id):
    st.title("Demo: Performance Overview")
    returns = np.random.uniform(-0.1, 0.2, 2)
    ai_return = (st.session_state.demo_data['ai_a']/100*returns[0] + 
                (100-st.session_state.demo_data['ai_a'])/100*returns[1]) * 100
    user_return = (50/100*returns[0] + 50/100*returns[1]) * 100
    
    st.plotly_chart(performance_chart(pd.DataFrame({
        'Category': ['Fund A', 'Fund B', 'AI Portfolio', 'Your Portfolio'],
        'Performance': [returns[0]*100, returns[1]*100, ai_return, user_return]
    })), use_container_width=True)

    if st.button("Start Real Experiment"):
        st.session_state.page = 'trial'
        st.session_state.trial_step = 1
        update_session_progress(
            session_id,
            page='trial',
            trial=st.session_state.trial,
            trial_step=st.session_state.trial_step
        )
        st.rerun()