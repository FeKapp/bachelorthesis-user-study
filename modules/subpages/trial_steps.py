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
    st.title(f"Trial {st.session_state.trial} - Step 1: Initial Allocation")

     # Get the session State Scenario
    scenario = st.session_state.get('scenario_id')
    # Insert the scenario_id for the scenario "long" from the database
    if scenario == '2e1e164a-699c-4c00-acff-61a98e23ddec' or 'b8426ff5-c6f2-4f25-a259-764e993ffa29':
        st.markdown("Please allocate your assets to Fund A (0-100%) and Fund B (0-100%) for the **next financial period**.")
    else:
        st.markdown("Please allocate your assets to Fund A (0-100%) and Fund B (0-100%) for the **next 20 financial periods**.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## Fund A")
        st.image(os.path.join("assets", "images", "fund_A.png"), width=200)
        initial_a = st.number_input("Allocation to Fund A (%)", min_value=0, max_value=100, value= None, key="demo_initial_a")
    with col2:
        st.markdown("## Fund B")
        st.image(os.path.join("assets", "images", "fund_B.png"), width=200)
        initial_b = st.number_input("Automatic allocation to Fund B (%)", min_value=0, max_value=100, value= (100 - initial_a) if initial_a is not None else 0, key="demo_initial_b", disabled=True)
        # st.write(f"Automatic allocation: {initial_b}%")

    if st.button("Submit Allocation"):
        if initial_a is None:
            st.error("Allocation to Fund A (0% - 100%) is required.")
        else:
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
    st.title(f"Trial {st.session_state.trial} - Step 2: AI Recommendation")

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
        with st.container(border=True):
            st.subheader("Your Initial Allocation")
            st.metric("Fund A:", f"{initial_a}%")
            st.metric("Fund B:", f"{initial_b}%")
        
    with col2:
        with st.container(border=True):
            st.subheader("AI Recommendation ✨")

            if is_instructed_trial:
                st.markdown("""
                    **Special Instruction** For this trial only:  
                    You **MUST** allocate **exactly 55% to Fund A** and 45% to **Fund B**  
                    This is a test of following instructions and does not affect your performance.
                    The real AI recommendation will be shown after you submit this trial.
                """)
            st.metric("Fund A:", f"{ai_a}%")
            st.metric("Fund B:", f"{ai_b}%")
            
    st.markdown("---")
    st.markdown("Based on your initial allocation and the AI recommendation, how do you allocate your assets?")
    col3, col4 = st.columns(2)
    with col3:
        adjusted_a = st.number_input("Allocation to Fund A (%)", min_value=0, max_value=100, value= None, key="adjusted_a")

    with col4:
        adjusted_b = st.number_input("Automatic allocation to Fund B (%)", min_value=0, max_value=100, value= (100 - adjusted_a) if adjusted_a is not None else 0, key="adjusted_b", disabled=True)
        # st.write(f"Automatic allocation: {adjusted_b}%")

    if st.button("Submit Allocation"):
        if adjusted_a is None:
            st.error("Allocation to Fund A is required.")
        else:
            # Save final
            save_allocation(
                st.query_params['session_id'],
                st.session_state.trial,
                'final',
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
    st.title(f"Trial {st.session_state.trial} - Step 3: Performance")

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

    scenario = st.session_state.get('scenario_id')
    # Insert the scenario_id for the scenario "long" from the database
    if scenario == '2e1e164a-699c-4c00-acff-61a98e23ddec' or 'b8426ff5-c6f2-4f25-a259-764e993ffa29':
        duration = "last financial period"
    else:
        duration = "last 20 financial periods"

    st.markdown(f"""
    Allocation breakdown:
    - Your Portfolio: **Fund A**: {final_a}%, **Fund B**: {final_b}%
    - AI portfolio: **Fund A**: {ai_a}%, **Fund B**: {ai_b}%""")

    st.markdown(f"Overview how Fund A, Fund B, the AI portfolio and your portfolio performed in the **{duration}**:")
    

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
