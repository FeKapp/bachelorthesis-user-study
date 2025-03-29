import streamlit as st
import os
import pandas as pd
from modules.database import supabase, update_session_progress, save_allocation
from modules.components.charts import create_performance_bar_chart

def handle_trial_steps():
    # Check if we've finished all trials
    if st.session_state.trial >= st.session_state.max_trials:
        st.session_state.page = 'final'
        update_session_progress(st.query_params['session_id'])
        st.rerun()

    # Route to the correct trial step
    if st.session_state.trial_step == 1:
        show_initial_allocation()
    elif st.session_state.trial_step == 2:
        show_ai_recommendation()
    elif st.session_state.trial_step == 3:
        show_performance()

def show_initial_allocation():
    st.title(f"Trial {st.session_state.trial + 1} - Step 1: Initial Allocation")

    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join("assets", "images", "fund_A.png"), width=200)
        initial_a = st.number_input(
            "Allocation to Fund A (%)",
            min_value=0,
            max_value=100,
            value=50,
            key=f"initial_a_{st.session_state.trial}"
        )
    with col2:
        st.image(os.path.join("assets", "images", "fund_B.png"), width=200)
        initial_b = 100 - initial_a
        st.write(f"Automatic allocation: {initial_b}%")

    if st.button("Submit Initial Allocation"):
        save_allocation(
            st.query_params['session_id'],
            st.session_state.trial,
            'initial',
            initial_a,
            initial_b
        )
        st.session_state.trial_step = 2
        update_session_progress(st.query_params['session_id'])
        st.rerun()

def show_ai_recommendation():
    st.title(f"Trial {st.session_state.trial + 1} - Step 2: AI Recommendation")

    # Query scenario to check if we need an instructed response
    scenario_res = supabase.table('scenario_config') \
        .select('*') \
        .eq('scenario_id', st.session_state.scenario_id) \
        .execute()
    scenario = scenario_res.data[0]

    # Check if this is an instructed response trial
    is_instructed_trial = (
        (scenario['num_trials'] == 5 and st.session_state.trial == 3) or
        (scenario['num_trials'] == 100 and st.session_state.trial == 79)
    )

    current_trial_index = st.session_state.trial + 1

    # If the AI allocation wasn't already saved, save it
    if st.session_state.allocations.get(st.session_state.trial, {}).get('ai') is None:
        if is_instructed_trial:
            # Hardcoded instructed response
            ai_a, ai_b = 55, 45
            with st.container():
                st.markdown("""
                    ⚠️ **Special Instruction** ⚠️  
                    For this trial only:  
                    - You **MUST** allocate **exactly 55% to Fund A**  
                    - You **MUST** allocate **exactly 45% to Fund B**  
                    This is a test of following instructions! 
                    The real AI recommendation will be shown after you submit this trial.
                """)
        else:
            ai_a, ai_b = st.session_state.ai_recommendations_data[current_trial_index]

        save_allocation(
            st.query_params['session_id'],
            st.session_state.trial,
            'ai',
            ai_a,
            ai_b
        )

        # Update local session_state
        st.session_state.allocations[st.session_state.trial] = {
            'initial': st.session_state.allocations.get(st.session_state.trial, {}).get('initial'),
            'ai': (ai_a, ai_b),
            'final': None
        }

    # Display user and AI allocations
    initial_a, initial_b = st.session_state.allocations[st.session_state.trial]['initial']
    ai_a, ai_b = st.session_state.allocations[st.session_state.trial]['ai']

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your Initial Allocation")
        st.write(f"Fund A: {initial_a}%")
        st.write(f"Fund B: {initial_b}%")

    with col2:
        st.subheader("✨ AI Recommendation")
        st.write(f"Fund A: {ai_a}%")
        st.write(f"Fund B: {ai_b}%")

    adjusted_a = st.number_input(
        "Revised allocation to Fund A (%)",
        min_value=0,
        max_value=100,
        value=initial_a,
        key=f"adjusted_a_{st.session_state.trial}"
    )
    adjusted_b = 100 - adjusted_a

    if st.button("Submit Final Allocation"):
        # Save final
        save_allocation(
            st.query_params['session_id'],
            st.session_state.trial,
            'post-ai',
            adjusted_a,
            adjusted_b
        )

        # If it's an instructed response trial, check compliance
        if is_instructed_trial:
            instructed_response_passed = (adjusted_a == 55 and adjusted_b == 45)
            supabase.table('sessions').update({
                'instructed_response_2_passed': instructed_response_passed
            }).eq('session_id', st.query_params['session_id']).execute()

        # Store the returns in 'trials'
        return_a, return_b = st.session_state.fund_returns_data[current_trial_index]
        trial_response = supabase.table('trials') \
            .select('trial_id') \
            .eq('session_id', st.query_params['session_id']) \
            .eq('trial_number', st.session_state.trial) \
            .execute()
        trial_id = trial_response.data[0]['trial_id']

        supabase.table('trials').update({
            'return_a': float(return_a),
            'return_b': float(return_b)
        }).eq('trial_id', trial_id).execute()

        st.session_state.trial_step = 3
        update_session_progress(st.query_params['session_id'])
        st.rerun()

def show_performance():
    st.title(f"Trial {st.session_state.trial + 1} - Step 3: Performance")

    trial_data = st.session_state.allocations[st.session_state.trial]
    return_a, return_b = st.session_state.fund_returns[st.session_state.trial]

    final_a, final_b = trial_data['final']
    final_return = (final_a/100)*return_a + (final_b/100)*return_b

    ai_a, ai_b = trial_data['ai']
    ai_return = (ai_a/100)*return_a + (ai_b/100)*return_b

    df = pd.DataFrame({
        'Category': ['Fund A', 'Fund B', 'AI Portfolio', 'User Portfolio'],
        'Performance': [
            return_a * 100,
            return_b * 100,
            ai_return * 100,
            final_return * 100
        ]
    })

    fig = create_performance_bar_chart(df, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    btn_label = (
        "Continue to Next Trial" if st.session_state.trial < st.session_state.max_trials - 1
        else "Proceed to Final Allocation"
    )
    if st.button(btn_label):
        st.session_state.trial += 1
        st.session_state.trial_step = 1
        update_session_progress(st.query_params['session_id'])
        st.rerun()
