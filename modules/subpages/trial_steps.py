import streamlit as st
from streamlit.components.v1 import html
import os
import pandas as pd
from modules.subpages.intro import scroll_to_top
from modules.database import supabase, update_session_progress, save_allocation
from modules.components.charts import create_performance_bar_chart

# Cache expensive chart creation
@st.cache_data(max_entries=100)
def cached_performance_chart(df):
    return create_performance_bar_chart(df, margin=dict(t=20, b=20))


def handle_trial_steps():
    session_id = st.query_params['session_id']
    
    if st.session_state.trial > st.session_state.max_trials:
        st.session_state.page = 'final'
        update_session_progress(session_id)
        st.rerun()

    step_handlers = {
        1: show_initial_allocation,
        2: show_ai_recommendation,
        3: show_performance,
        4: show_instructed
    }
    step_handlers.get(st.session_state.trial_step, show_initial_allocation)()

def show_initial_allocation():
    scroll_to_top()
    session_id     = st.query_params['session_id']
    ordinal        = st.session_state.trial
    actual_trial   = st.session_state.trial_sequence[ordinal - 1]

    # Get period information from scenario_config
    periods = "3 months" if st.session_state.max_trials == 100 else "5 years"
    
    st.title(f"Step 1: Initial Allocation")
    st.markdown(f"Please allocate your money for the **next {periods}**.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## Fund A 🔵")
        st.image(os.path.join("assets", "images", "fund_A.png"), width=200)
        initial_a = st.number_input("Allocation to Fund A (%)", 
                                    min_value=0, max_value=100, 
                                    value=None, key=f"initial_a_{ordinal}")
    with col2:
        st.markdown("## Fund B 🟡")
        st.image(os.path.join("assets", "images", "fund_B.png"), width=200)
        initial_b = 100 - initial_a if initial_a is not None else 0
        st.number_input("Automatic allocation to Fund B (%)", 
                        min_value=0, max_value=100, 
                        value=initial_b, key=f"initial_b_{ordinal}", disabled=True)

    if st.button("Submit Allocation", key=f"initial_btn_{ordinal}"):
        if initial_a is None:
            st.error("Allocation to Fund A (0% - 100%) is required.")
            return
        elif initial_b is None:
            st.error("Please press enter after allocating Fund A to automatically allocate Fund B.")
            return

        save_allocation(session_id, actual_trial, 'initial', initial_a, initial_b)
        
        is_instructed = (
            (st.session_state.max_trials == 5   and ordinal == 3) or
            (st.session_state.max_trials == 100 and ordinal == 79)
        )
        st.session_state.trial_step = 4 if is_instructed else 2
        st.session_state.allocations[ordinal] = {
            'initial': (initial_a, initial_b),
            'ai':      None,
            'final':   None
        }
        update_session_progress(session_id)
        st.rerun()

def show_ai_recommendation():
    scroll_to_top()
    session_id   = st.query_params['session_id']
    ordinal      = st.session_state.trial
    actual_trial = st.session_state.trial_sequence[ordinal - 1]

    st.title(f"Step 2: AI Recommendation")

    try:
        ai_a, ai_b = st.session_state.ai_recommendations_data[actual_trial]
    except KeyError:
        st.error("Missing AI recommendation data!")
        st.stop()

    if not st.session_state.allocations[ordinal]['ai']:
        save_allocation(session_id, actual_trial, 'ai', ai_a, ai_b)
        st.session_state.allocations[ordinal]['ai'] = (ai_a, ai_b)

    initial_a, initial_b = st.session_state.allocations[ordinal]['initial']
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Your Initial Allocation 👤")
            st.metric("Fund A:", f"{initial_a}%")
            st.metric("Fund B:", f"{initial_b}%")
    with col2:
        with st.container(border=True):
            st.subheader("AI Recommendation ✨")
            st.metric("Fund A:", f"{ai_a}%")
            st.metric("Fund B:", f"{ai_b}%")

    st.markdown("---")
    st.markdown("Based on your initial allocation and the AI recommendation, how do you allocate your money?")
    
    col3, col4 = st.columns(2)
    with col3:
        final_a = st.number_input("Allocation to Fund A (%)", 
                                  min_value=0, max_value=100, 
                                  value=None, key=f"final_a_{ordinal}")
    with col4:
        final_b = 100 - final_a if final_a is not None else 0
        st.number_input("Automatic allocation to Fund B (%)", 
                        min_value=0, max_value=100, 
                        value=final_b, key=f"initial_b_{ordinal}", disabled=True)

    if st.button("Submit Allocation", key=f"final_btn_{ordinal}"):
        if final_a is None:
            st.error("Allocation to Fund A (0% - 100%)is required.")
            return
        elif final_b is None:
            st.error("Please press enter after allocating Fund A to automatically allocate Fund B.")
            return
        
        save_allocation(session_id, actual_trial, 'final', final_a, final_b)
        st.session_state.allocations[ordinal]['final'] = (final_a, final_b)

        st.session_state.trial_step = 3
        update_session_progress(session_id)
        st.rerun()

def show_instructed():
    scroll_to_top()
    session_id = st.query_params['session_id']
    current_trial = st.session_state.trial
    scenario_id = st.session_state.scenario_id
    
    # st.title(f"Trial {current_trial} - Step 2: AI Recommendation")
    st.title(f"Step 2: AI Recommendation")

    # Display allocations
    initial_a, initial_b = st.session_state.allocations[current_trial]['initial']
    ai_a, ai_b = (55, 45)

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Your Initial Allocation 👤")
            st.metric("Fund A:", f"{initial_a}%")
            st.metric("Fund B:", f"{initial_b}%")
        
    with col2:
        with st.container(border=True):
            st.subheader("AI Recommendation ✨")
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
    st.markdown("Based on your initial allocation and the AI recommendation, how do you allocate your money?")
    
    col3, col4 = st.columns(2)
    with col3:
        instructed_a = st.number_input("Final Allocation to Fund A (%)", 
                               min_value=0, max_value=100, 
                               value=None, key=f"final_a_{current_trial}")

    with col4:
        instructed_b = 100 - instructed_a if instructed_a is not None else 0
        st.number_input("Automatic allocation to Fund B (%)", 
                      min_value=0, max_value=100, 
                      value=instructed_b, key=f"initial_b_{current_trial}", disabled=True)

    
    # Submit allocation
    if st.button("Submit Allocation", key=f"final_btn_{current_trial}"):
        if instructed_a is None:
            st.error("Allocation to Fund A is required.")
            return

        supabase.table('sessions').update({
            'instructed_response_2_passed': instructed_a == 55
        }).eq('session_id', session_id).execute()

        # Move to next step
        st.session_state.trial_step = 2
        st.rerun()

def show_performance():
    scroll_to_top()
    session_id   = st.query_params['session_id']
    ordinal      = st.session_state.trial
    actual_trial = st.session_state.trial_sequence[ordinal - 1]

    return_a, return_b = st.session_state.fund_returns_data[actual_trial]
    final_a, final_b   = st.session_state.allocations[ordinal]['final']
    ai_a, ai_b         = st.session_state.allocations[ordinal]['ai']

    final_return = (final_a/100)*return_a + (final_b/100)*return_b
    ai_return    = (ai_a/100)*return_a  + (ai_b/100)*return_b

    df = pd.DataFrame({
        'Category':    ['Your Portfolio 👤', 'AI Portfolio ✨', 'Fund A 🔵', 'Fund B 🟡'],
        'Performance': [final_return*100, ai_return*100, return_a*100, return_b*100]
    })

    st.title("Step 3: Performance")
    duration = "last 3 months" if st.session_state.max_trials == 100 else "last 5 years"
    st.markdown(f"""
    Allocation breakdown:
    - Your Portfolio: **Fund A**: {final_a}%, **Fund B**: {final_b}%
    - AI portfolio: **Fund A**: {ai_a}%, **Fund B**: {ai_b}%
    
    Overview how your portfolio, the AI portfolio, Fund A and Fund B performed during the **{duration}**:
    """)

    st.plotly_chart(cached_performance_chart(df), use_container_width=True)

    btn_label = "Continue to next period" if ordinal < st.session_state.max_trials else ":red[Next: Final Decision]"
    if st.button(btn_label, key=f"continue_{ordinal}"):
        if ordinal < st.session_state.max_trials:
            st.session_state.trial      += 1
            st.session_state.trial_step  = 1
        else:
            st.session_state.page = 'final'
        update_session_progress(session_id)
        st.rerun()
