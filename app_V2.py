import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'intro'
if 'trial' not in st.session_state:
    st.session_state.trial = 0
if 'trial_step' not in st.session_state:
    st.session_state.trial_step = 1
if 'fund_returns' not in st.session_state:
    st.session_state.fund_returns = {}
if 'allocations' not in st.session_state:
    st.session_state.allocations = {}

def main():
    if st.session_state.page == 'intro':
        show_intro()
    elif st.session_state.page == 'trial':
        handle_trial_steps()
    elif st.session_state.page == 'final':
        show_final()
    elif st.session_state.page == 'debrief':
        show_debrief()
    
    # Show progress bar at bottom for all pages except intro
    if st.session_state.page != 'intro':
        show_progress()

def show_progress():
    # Calculate progress percentage
    progress = min(st.session_state.trial / 5, 1.0)
    
    # Create container at bottom of page
    with st.container():
        st.markdown("<br><br>", unsafe_allow_html=True)  # Add spacing
        st.progress(progress)
        st.caption(f"Study progress: {int(progress*100)}% complete")

def show_intro():
    st.title("Fund Allocation Study")
    st.write("""
    **Welcome to the investment study!**
    
    You will complete 5 rounds of:
    1. Initial allocation
    2. AI recommendation review
    3. Performance analysis
    
    Funds available:
    - Fund A (High Risk/Return): 11% mean, 15% stdev
    - Fund B (Low Risk/Return): 3% mean, 5% stdev
    """)
    
    if st.button("Begin Study"):
        st.session_state.page = 'trial'
        st.rerun()

def handle_trial_steps():
    if st.session_state.trial >= 5:
        st.session_state.page = 'final'
        st.rerun()
    
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
        st.subheader("Fund A")
        initial_a = st.number_input("Allocation to Fund A (%)", 0, 100, 50, key=f"initial_a_{st.session_state.trial}")
    
    with col2:
        st.subheader("Fund B")
        initial_b = 100 - initial_a
        st.write(f"Automatic allocation: {initial_b}%")

    if st.button("Submit Initial Allocation"):
        st.session_state.allocations[st.session_state.trial] = {
            'initial': (initial_a, initial_b),
            'ai': None,
            'final': None
        }
        st.session_state.trial_step = 2
        st.rerun()

def show_ai_recommendation():
    st.title(f"Trial {st.session_state.trial + 1} - Step 2: AI Recommendation")
    
    if st.session_state.allocations[st.session_state.trial]['ai'] is None:
        ai_a = np.random.randint(0, 101)
        ai_b = 100 - ai_a
        st.session_state.allocations[st.session_state.trial]['ai'] = (ai_a, ai_b)
    
    initial_a, initial_b = st.session_state.allocations[st.session_state.trial]['initial']
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your Initial Allocation")
        st.write(f"Fund A: {initial_a}%")
        st.write(f"Fund B: {initial_b}%")
    
    with col2:
        st.subheader("AI Recommendation")
        ai_a, ai_b = st.session_state.allocations[st.session_state.trial]['ai']
        st.write(f"Fund A: {ai_a}%")
        st.write(f"Fund B: {ai_b}%")
    
    st.subheader("Adjust Your Allocation")
    adjusted_a = st.number_input("Revised allocation to Fund A (%)", 0, 100, initial_a, key=f"adjusted_a_{st.session_state.trial}")
    adjusted_b = 100 - adjusted_a
    st.write(f"Revised Fund B allocation: {adjusted_b}%")
    
    if st.button("Submit Final Allocation"):
        st.session_state.allocations[st.session_state.trial]['final'] = (adjusted_a, adjusted_b)
        
        return_a = np.random.normal(0.11, 0.15)
        return_b = np.random.normal(0.03, 0.05)
        st.session_state.fund_returns[st.session_state.trial] = (return_a, return_b)
        
        st.session_state.trial_step = 3
        st.rerun()

def show_performance():
    st.title(f"Trial {st.session_state.trial + 1} - Step 3: Performance")
    
    trial_data = st.session_state.allocations[st.session_state.trial]
    return_a, return_b = st.session_state.fund_returns[st.session_state.trial]
    
    final_a, final_b = trial_data['final']
    final_return = (final_a/100)*return_a + (final_b/100)*return_b
    
    # Single bar chart showing key metrics
    st.subheader("Investment Performance")
    chart_data = pd.DataFrame({
        'Returns': [
            return_a,
            return_b,
            final_return
        ],
        'Category': ['Fund A', 'Fund B', 'Your Portfolio']
    }).set_index('Category')
    
    st.bar_chart(chart_data)

    btn_label = "Continue to Next Trial" if st.session_state.trial < 4 else "Proceed to Final Allocation"
    if st.button(btn_label):
        st.session_state.trial += 1
        st.session_state.trial_step = 1
        st.session_state.page = 'trial' if st.session_state.trial < 5 else 'final'
        st.rerun()

def show_final():
    st.title("Final Allocation")
    st.write("**This is your last investment decision**")
    
    final_a = st.number_input("Final allocation to Fund A (%)", 0, 100, 50)
    final_b = 100 - final_a
    
    if st.button("Submit Final Allocation"):
        return_a = np.random.normal(0.11, 0.15)
        return_b = np.random.normal(0.03, 0.05)
        portfolio_return = (final_a/100)*return_a + (final_b/100)*return_b
        
        save_data(final_a, final_b, return_a, return_b, portfolio_return, 'final')
        st.session_state.page = 'debrief'
        st.rerun()

def show_debrief():
    st.title("Study Complete")
    st.write("""
    **Thank you for participating!**
    
    Your responses have been recorded anonymously.
    """)
    
    if st.checkbox("I consent to my data being used for research purposes"):
        if st.button("Confirm Consent"):
            st.success("Consent confirmed. Thank you!")
            st.balloons()

def save_data(fund_a, fund_b, return_a, return_b, portfolio_return, 
             allocation_type, timestamp=None):
    data = {
        'timestamp': timestamp or datetime.now(),
        'type': allocation_type,
        'fund_a': fund_a,
        'fund_b': fund_b,
        'return_a': return_a,
        'return_b': return_b,
        'portfolio_return': portfolio_return
    }
    
    df = pd.DataFrame([data])
    df.to_csv('allocations.csv', mode='a', 
              header=not pd.io.common.file_exists('allocations.csv'), 
              index=False)

if __name__ == "__main__":
    main()