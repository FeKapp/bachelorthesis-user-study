import streamlit as st
from streamlit_theme import st_theme
import numpy as np
import pandas as pd
import os
from modules.database import supabase, update_session_progress
from modules.components.charts import create_performance_bar_chart

def handle_demo_steps():
    if st.session_state.trial_step == 1:
        show_demo_initial()
    elif st.session_state.trial_step == 2:
        show_demo_ai()
    elif st.session_state.trial_step == 3:
        show_demo_performance()

def show_demo_initial():
    st.title("Demo: Initial Allocation")
    st.markdown(
        "<div style='color: red; margin-bottom: 20px;'>This is a demonstration of the initial allocation step. "
        "Try adjusting the slider to see how allocations work.</div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## Fund A")
        st.image(os.path.join("assets", "images", "fund_A.png"), width=200)
        demo_initial_a = st.number_input("Allocation to Fund A (%)", min_value=0, max_value=100, value= None, key="demo_initial_a")
    with col2:
        st.markdown("## Fund B")
        st.image(os.path.join("assets", "images", "fund_B.png"), width=200)
        demo_initial_b = st.number_input("Automatic allocation to Fund B (%)", min_value=0, max_value=100, value= (100 - demo_initial_a) if demo_initial_a is not None else 0, key="demo_initial_b", disabled=True)
        st.write(f"Automatic allocation: {demo_initial_b}%")

    if st.button("Next: AI Recommendation Demo"):
        if demo_initial_a is None:
            st.error("Allocation to Fund A is required.")
        else:
            st.session_state.trial_step = 2
            update_session_progress(st.query_params['session_id'])
            st.rerun()

def show_demo_ai():
    st.title("Demo: AI Recommendation")
    st.markdown(
        "<div style='color: red; margin-bottom: 20px;'>This demonstrates the AI recommendation step. "
        "The AI suggestion here is randomly generated.</div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your Initial Allocation")
        st.write("Fund A: 50%")
        st.write("Fund B: 50%")
    with col2:
        st.subheader("✨ AI Recommendation")
        st.write(f"Fund A: {st.session_state.demo_data['ai_a']}%")
        st.write(f"Fund B: {st.session_state.demo_data['ai_b']}%")

    adjusted_a = st.number_input("Revised allocation to Fund A (%)", 0, 100, 50, key="demo_adjusted_a")
    # adjusted_b
    _ = 100 - adjusted_a

    if st.button("Next: Performance Demo"):
        st.session_state.trial_step = 3
        update_session_progress(st.query_params['session_id'])
        st.rerun()

def show_demo_performance():
    st.title("Demo: Performance Overview")
    st.markdown(
        "<div style='color: red; margin-bottom: 20px;'>This shows performance results. "
        "Returns are randomly generated for demonstration.</div>",
        unsafe_allow_html=True
    )

    # Calculate returns using demo data
    return_a = st.session_state.demo_data['return_a']
    return_b = st.session_state.demo_data['return_b']
    ai_return = (st.session_state.demo_data['ai_a']/100) * return_a + \
                (st.session_state.demo_data['ai_b']/100) * return_b
    user_return = (50/100) * return_a + (50/100) * return_b  # Using default 50% from demo

    df = pd.DataFrame({
        'Category': ['Fund A', 'Fund B', 'AI Portfolio', 'Your Portfolio'],
        'Performance': [
            return_a * 100,
            return_b * 100,
            ai_return * 100,
            user_return * 100
        ]
    })

    fig = create_performance_bar_chart(df, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    if st.button("Start Real Experiment"):
        st.session_state.page = 'trial'
        st.session_state.trial_step = 1
        update_session_progress(st.query_params['session_id'])
        st.rerun()
