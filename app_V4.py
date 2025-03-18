import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import uuid
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Session persistence setup
session_id = st.query_params.get("session_id") or str(uuid.uuid4())
if "session_id" not in st.query_params:
    st.query_params["session_id"] = session_id
    st.rerun()

def update_session_progress():
    """Update session progress in database"""
    supabase.table('sessions').update({
        'current_page': st.session_state.page,
        'current_trial': st.session_state.trial,
        'current_trial_step': st.session_state.trial_step
    }).eq('session_id', session_id).execute()

def save_allocation(trial_num, allocation_type, fund_a, fund_b, portfolio_return=None):
    """Save allocation to Supabase"""
    # Get or create trial ID
    trial_response = supabase.table('trials').select('trial_id').eq('session_id', session_id).eq('trial_number', trial_num).execute()
    trial_id = trial_response.data[0]['trial_id'] if trial_response.data else str(uuid.uuid4())
    
    # Create trial record if it doesn't exist
    if not trial_response.data:
        supabase.table('trials').insert({
            'trial_id': trial_id,
            'session_id': session_id,
            'trial_number': trial_num,
            'created_at': datetime.now().isoformat()
        }).execute()
    
    # Create allocation record
    supabase.table('allocations').insert({
        'allocation_id': str(uuid.uuid4()),
        'trial_id': trial_id,
        'allocation_type': allocation_type,
        'fund_a': fund_a,
        'fund_b': fund_b,
        'portfolio_return': portfolio_return,
        'created_at': datetime.now().isoformat()
    }).execute()

def load_session_data():
    """Load existing session data from Supabase"""
    # Load session
    session_response = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
    if session_response.data:
        session_data = session_response.data[0]
        
        # Load trials and allocations
        trials_response = supabase.table('trials').select('*').eq('session_id', session_id).execute()
        fund_returns = {}
        allocations = {}
        
        for trial in trials_response.data:
            fund_returns[trial['trial_number']] = (
                trial['return_a'],
                trial['return_b']
            )
            
            alloc_response = supabase.table('allocations').select('*').eq('trial_id', trial['trial_id']).execute()
            allocations[trial['trial_number']] = {
                'initial': None,
                'ai': None,
                'final': None
            }
            
            for alloc in alloc_response.data:
                allocations[trial['trial_number']][alloc['allocation_type']] = (
                    alloc['fund_a'],
                    alloc['fund_b']
                )
        
        return session_data, fund_returns, allocations
    return None, {}, {}

# Initialize or load session
session_response = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
if session_response.data:
    session_data = session_response.data[0]
    fund_returns = {}
    allocations = {}
    
    # Load trials and allocations
    trials_response = supabase.table('trials').select('*').eq('session_id', session_id).execute()
    for trial in trials_response.data:
        fund_returns[trial['trial_number']] = (trial['return_a'], trial['return_b'])
        
        alloc_response = supabase.table('allocations').select('*').eq('trial_id', trial['trial_id']).execute()
        allocations[trial['trial_number']] = {
            'initial': None,
            'ai': None,
            'final': None
        }
        for alloc in alloc_response.data:
            allocations[trial['trial_number']][alloc['allocation_type']] = (alloc['fund_a'], alloc['fund_b'])
    
    # Set session state
    st.session_state.update({
        'page': session_data['current_page'],
        'trial': session_data['current_trial'],
        'trial_step': session_data['current_trial_step'],
        'scenario': session_data['scenario'],
        'ai_type': session_data['ai_type'],
        'max_trials': session_data['max_trials'],
        'fund_returns': fund_returns,
        'allocations': allocations
    })
else:
    # Create new session
    scenario = np.random.choice(['short_unbiased', 'short_biased', 'long_unbiased', 'long_biased'])
    session_data = {
        'session_id': session_id,
        'scenario': scenario,
        'ai_type': 'biased' if 'biased' in scenario else 'unbiased',
        'max_trials': 100 if 'long' in scenario else 5,
        'current_page': 'intro',
        'current_trial': 0,
        'current_trial_step': 1,
        'created_at': datetime.now().isoformat()
    }
    supabase.table('sessions').insert(session_data).execute()
    
    st.session_state.update({
        'page': 'intro',
        'trial': 0,
        'trial_step': 1,
        'scenario': scenario,
        'ai_type': session_data['ai_type'],
        'max_trials': session_data['max_trials'],
        'fund_returns': {},
        'allocations': {}
    })

def show_progress():
    progress = min(st.session_state.trial / st.session_state.max_trials, 1.0)
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
        st.session_state.page = 'trial'
        update_session_progress()
        st.rerun()

def handle_trial_steps():
    if st.session_state.trial >= st.session_state.max_trials:
        st.session_state.page = 'final'
        update_session_progress()
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
        initial_a = st.number_input("Allocation to Fund A (%)", 0, 100, 50, key=f"initial_a_{st.session_state.trial}")
    
    with col2:
        initial_b = 100 - initial_a
        st.write(f"Automatic allocation: {initial_b}%")

    if st.button("Submit Initial Allocation"):
        save_allocation(st.session_state.trial, 'initial', initial_a, initial_b)
        st.session_state.trial_step = 2
        update_session_progress()
        st.rerun()

def show_ai_recommendation():
    st.title(f"Trial {st.session_state.trial + 1} - Step 2: AI Recommendation")
    
    if st.session_state.allocations.get(st.session_state.trial, {}).get('ai') is None:
        if st.session_state.ai_type == 'biased':
            ai_a, ai_b = 0, 100
        else:
            ai_a = np.random.randint(0, 101)
            ai_b = 100 - ai_a
        save_allocation(st.session_state.trial, 'ai', ai_a, ai_b)
        st.session_state.allocations[st.session_state.trial] = {
            'initial': st.session_state.allocations.get(st.session_state.trial, {}).get('initial'),
            'ai': (ai_a, ai_b),
            'final': None
        }
    
    initial_a, initial_b = st.session_state.allocations[st.session_state.trial]['initial']
    ai_a, ai_b = st.session_state.allocations[st.session_state.trial]['ai']
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Your Initial Allocation")
        st.write(f"Fund A: {initial_a}%")
        st.write(f"Fund B: {initial_b}%")
    
    with col2:
        st.subheader("AI Recommendation")
        st.write(f"Fund A: {ai_a}%")
        st.write(f"Fund B: {ai_b}%")
    
    adjusted_a = st.number_input("Revised allocation to Fund A (%)", 0, 100, initial_a, key=f"adjusted_a_{st.session_state.trial}")
    adjusted_b = 100 - adjusted_a
    
    if st.button("Submit Final Allocation"):
        save_allocation(st.session_state.trial, 'final', adjusted_a, adjusted_b)
        
        return_a = np.random.normal(0.11, 0.15)
        return_b = np.random.normal(0.03, 0.05)
        
        # Update trial with returns
        trial_response = supabase.table('trials').select('trial_id').eq('session_id', session_id).eq('trial_number', st.session_state.trial).execute()
        trial_id = trial_response.data[0]['trial_id']
        supabase.table('trials').update({
            'return_a': float(return_a),
            'return_b': float(return_b)
        }).eq('trial_id', trial_id).execute()
        
        st.session_state.trial_step = 3
        update_session_progress()
        st.rerun()

def show_performance():
    st.title(f"Trial {st.session_state.trial + 1} - Step 3: Performance")
    
    trial_data = st.session_state.allocations[st.session_state.trial]
    return_a, return_b = st.session_state.fund_returns[st.session_state.trial]
    
    final_a, final_b = trial_data['final']
    final_return = (final_a/100)*return_a + (final_b/100)*return_b
    
    chart_data = pd.DataFrame({
        'Returns': [return_a, return_b, final_return],
        'Category': ['Fund A', 'Fund B', 'Your Portfolio']
    }).set_index('Category')
    
    st.bar_chart(chart_data)

    btn_label = "Continue to Next Trial" if st.session_state.trial < st.session_state.max_trials - 1 else "Proceed to Final Allocation"
    if st.button(btn_label):
        st.session_state.trial += 1
        st.session_state.trial_step = 1
        update_session_progress()
        st.rerun()

def show_final():
    st.title("Final Allocation")
    final_a = st.number_input("Final allocation to Fund A (%)", 0, 100, 50)
    final_b = 100 - final_a
    
    if st.button("Submit Final Allocation"):
        return_a = np.random.normal(0.11, 0.15)
        return_b = np.random.normal(0.03, 0.05)
        portfolio_return = (final_a/100)*return_a + (final_b/100)*return_b
        
        # Save final allocation
        save_allocation(st.session_state.trial, 'final', final_a, final_b, portfolio_return)
        
        # Update trial with returns
        trial_response = supabase.table('trials').select('trial_id').eq('session_id', session_id).eq('trial_number', st.session_state.trial).execute()
        trial_id = trial_response.data[0]['trial_id']
        supabase.table('trials').update({
            'return_a': float(return_a),
            'return_b': float(return_b)
        }).eq('trial_id', trial_id).execute()
        
        st.session_state.page = 'debrief'
        update_session_progress()
        st.rerun()

def show_debrief():
    st.title("Study Complete")
    st.write("**Thank you for participating!**")
    
    if st.checkbox("I consent to my data being used for research purposes"):
        if st.button("Confirm Consent"):
            supabase.table('sessions').update({
                'completed_at': datetime.now().isoformat(),
                'consent_given': True
            }).eq('session_id', session_id).execute()
            st.success("Consent confirmed. Thank you!")
            st.balloons()

def main():
    if st.session_state.page == 'intro':
        show_intro()
    elif st.session_state.page == 'trial':
        handle_trial_steps()
    elif st.session_state.page == 'final':
        show_final()
    elif st.session_state.page == 'debrief':
        show_debrief()
    
    if st.session_state.page != 'intro':
        show_progress()

if __name__ == "__main__":
    main()