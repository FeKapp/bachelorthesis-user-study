import streamlit as st
import numpy as np
import pandas as pd
from datetime import datetime
import uuid
import os
from supabase import create_client, Client
from dotenv import load_dotenv
import plotly.graph_objects as go
import pycountry

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
    trial_response = supabase.table('trials').select('trial_id').eq('session_id', session_id).eq('trial_number', trial_num).execute()
    trial_id = trial_response.data[0]['trial_id'] if trial_response.data else str(uuid.uuid4())
    
    if not trial_response.data:
        supabase.table('trials').insert({
            'trial_id': trial_id,
            'session_id': session_id,
            'trial_number': trial_num,
            'created_at': datetime.now().isoformat()
        }).execute()
    
    supabase.table('allocations').insert({
        'allocation_id': str(uuid.uuid4()),
        'trial_id': trial_id,
        'allocation_type': allocation_type,
        'fund_a': fund_a,
        'fund_b': fund_b,
        'portfolio_return': portfolio_return,
        'created_at': datetime.now().isoformat()
    }).execute()

def save_demographics(data):
    """Save demographic data to Supabase"""
    supabase.table('demographics').insert({
        'demographic_id': str(uuid.uuid4()),
        'session_id': session_id,
        **data,
        'created_at': datetime.now().isoformat()
    }).execute()

def load_session_data():
    session_response = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
    if session_response.data:
        session_data = session_response.data[0]
        trials_response = supabase.table('trials').select('*').eq('session_id', session_id).execute()
        fund_returns = {}
        allocations = {}
        
        for trial in trials_response.data:
            fund_returns[trial['trial_number']] = (trial['return_a'], trial['return_b'])
            alloc_response = supabase.table('allocations').select('*').eq('trial_id', trial['trial_id']).execute()
            allocations[trial['trial_number']] = {'initial': None, 'ai': None, 'final': None}
            for alloc in alloc_response.data:
                allocations[trial['trial_number']][alloc['allocation_type']] = (alloc['fund_a'], alloc['fund_b'])
        
        return session_data, fund_returns, allocations
    return None, {}, {}

# Initialize or load session
session_response = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
if session_response.data:
    session_data = session_response.data[0]
    fund_returns = {}
    allocations = {}
    
    trials_response = supabase.table('trials').select('*').eq('session_id', session_id).execute()
    for trial in trials_response.data:
        fund_returns[trial['trial_number']] = (trial['return_a'], trial['return_b'])
        alloc_response = supabase.table('allocations').select('*').eq('trial_id', trial['trial_id']).execute()
        allocations[trial['trial_number']] = {'initial': None, 'ai': None, 'final': None}
        for alloc in alloc_response.data:
            allocations[trial['trial_number']][alloc['allocation_type']] = (alloc['fund_a'], alloc['fund_b'])
    
    st.session_state.update({
        'page': session_data['current_page'],
        'trial': session_data['current_trial'],
        'trial_step': session_data['current_trial_step'],
        'scenario_id': session_data['scenario_id'],
        'max_trials': session_data['max_trials'],
        'fund_returns': fund_returns,
        'allocations': allocations
    })
else:
    # Create new session with scenario data from database
    scenario_res = supabase.table('scenario_config').select('*').execute()
    scenarios = scenario_res.data
    selected_scenario = np.random.choice(scenarios)
    
    fr_res = supabase.table('fund_returns').select('*').eq('scenario_id', selected_scenario['scenario_id']).execute()
    ai_res = supabase.table('ai_recommendations').select('*').eq('scenario_id', selected_scenario['scenario_id']).execute()
    
    session_data = {
        'session_id': session_id,
        'scenario_id': selected_scenario['scenario_id'],
        'current_page': 'intro',
        'current_trial': 0,
        'current_trial_step': 1,
        'created_at': datetime.now().isoformat(),
        'max_trials': selected_scenario['num_trials']
    }
    supabase.table('sessions').insert(session_data).execute()
    
    st.session_state.update({
        'page': 'intro',
        'trial': 1,
        'trial_step': 1,
        'scenario_id': selected_scenario['scenario_id'],
        'max_trials': selected_scenario['num_trials'],
        'fund_returns': {},
        'allocations': {},
        'fund_returns_data': {fr['trial_number']: (fr['return_a'], fr['return_b']) for fr in fr_res.data},
        'ai_recommendations_data': {ai['trial_number']: (ai['fund_a'], ai['fund_b']) for ai in ai_res.data}
    })

def show_progress():
    progress = min(st.session_state.trial / st.session_state.max_trials, 1.0)
    with st.container():
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.progress(progress)
        st.caption(f"Study progress: {int(progress*100)}% complete")

def show_intro():
    st.title("Experiment Introduction")
    intro_file_path = os.path.join("assets", "text", "introduction.txt")
    with open(intro_file_path, "r", encoding="utf-8") as f:
        intro_text = f.read()
    st.write(intro_text)
    
    if st.button("Start Demographic Questionnaire"):
        st.session_state.page = 'demographics'  
        update_session_progress()
        st.rerun()

def show_demographics():
    st.title("Demographic Questionnaire")
    
    # Get country list with Switzerland and Singapore first
    all_countries = sorted([c.name for c in pycountry.countries])
    priority_countries = ["Switzerland", "Singapore"]
    other_countries = [c for c in all_countries if c not in priority_countries]
    country_list = priority_countries + sorted(other_countries)
    
    with st.form("demographic_form"):
        st.write("Please answer the following questions before we begin:")
        
        country = st.selectbox("Country of Residence", options=country_list)
        gender = st.selectbox("Gender", options=[
            "Male", "Female", "Prefer not to say"
        ])
        
        age = st.number_input("Age", min_value=18, max_value=100, value=25)
        
        education_level = st.selectbox("Highest Level of Education", options=[
            "Mandatory Education (Primary/Secondary)",
            "Vocational Education (EFZ, apprenticeship)",
            "Baccalaureate (Gymnasium)",
            "Higher Vocational Education (PET, Diploma)",
            "University (Bachelor's Degree)",
            "University (Master's Degree)",
            "Doctoral Degree (PhD)",
            "Other"
        ])
        
        ai_proficiency = st.radio(
            "How would you rate your proficiency with Artificial Intelligence?",
            options=[1, 2, 3, 4, 5, 6, 7],
            horizontal=True,
            format_func=lambda x: f"{x} - {['Novice','','','','','','Expert'][x-1]}"
        )
        
        financial_literacy = st.radio(
            "How would you rate your financial literacy?",
            options=[1, 2, 3, 4, 5, 6, 7],
            horizontal=True,
            format_func=lambda x: f"{x} - {['Novice','','','','','','Expert'][x-1]}"
        )

        if st.form_submit_button("Submit Demographics"):
            save_demographics({
                'country': country,
                'gender': gender,
                'age': age,
                'education_level': education_level,
                'ai_proficiency': ai_proficiency,
                'financial_literacy': financial_literacy
            })
            st.session_state.page = 'trial'
            update_session_progress()
            st.rerun()

def handle_trial_steps():
    if st.session_state.trial >= st.session_state.max_trials:
        # means we've finished the last trial
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
        st.image(os.path.join("assets", "images", "fund_A.png"), width=200) 
        initial_a = st.number_input("Allocation to Fund A (%)", 0, 100, 50, key=f"initial_a_{st.session_state.trial}")
    with col2:
        st.image(os.path.join("assets", "images", "fund_B.png"), width=200)  
        initial_b = 100 - initial_a
        st.write(f"Automatic allocation: {initial_b}%")

    if st.button("Submit Initial Allocation"):
        save_allocation(st.session_state.trial, 'initial', initial_a, initial_b)
        st.session_state.trial_step = 2
        update_session_progress()
        st.rerun()

def show_ai_recommendation():
    # Display the trial number as (trial + 1) for the user
    st.title(f"Trial {st.session_state.trial + 1} - Step 2: AI Recommendation")
    
    # When accessing the AI recommendations from the DB,
    # use trial + 1 because DB trial numbers start at 1.
    current_trial = st.session_state.trial + 1  
    if st.session_state.allocations.get(st.session_state.trial, {}).get('ai') is None:
        ai_a, ai_b = st.session_state.ai_recommendations_data[current_trial]
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
        st.subheader("✨ AI Recommendation")
        st.write(f"Fund A: {ai_a}%")
        st.write(f"Fund B: {ai_b}%")
    
    adjusted_a = st.number_input("Revised allocation to Fund A (%)", 0, 100, initial_a, key=f"adjusted_a_{st.session_state.trial}")
    adjusted_b = 100 - adjusted_a
    
    if st.button("Submit Final Allocation"):
        save_allocation(st.session_state.trial, 'final', adjusted_a, adjusted_b)
        # Also look up fund returns using trial+1
        return_a, return_b = st.session_state.fund_returns_data[st.session_state.trial + 1]
        
        trial_response = supabase.table('trials') \
            .select('trial_id') \
            .eq('session_id', session_id) \
            .eq('trial_number', st.session_state.trial) \
            .execute()
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

    fig = go.Figure(data=[
        go.Bar(
            x=df['Category'],
            y=df['Performance'],
            marker_color=['green' if p >= 0 else 'red' for p in df['Performance']],
            text=[f"{val:.2f}%" for val in df['Performance']],
            textposition='outside'
        )
    ])
    fig.update_layout(yaxis_title='Performance (%)', showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    btn_label = "Continue to Next Trial" if st.session_state.trial < st.session_state.max_trials - 1 else "Proceed to Final Allocation"
    if st.button(btn_label):
        st.session_state.trial += 1
        st.session_state.trial_step = 1
        update_session_progress()
        st.rerun()

def show_final():
    st.title("Final Allocation")
    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join("assets", "images", "fund_A.png"), width=200)  
        final_a = st.number_input("Final allocation to Fund A (%)", 0, 100, 50)
    with col2:
        st.image(os.path.join("assets", "images", "fund_B.png"), width=200) 
        final_b = 100 - final_a
        st.write(f"Automatic allocation: {final_b}%")
    
    if st.button("Submit Final Allocation"):
        current_trial = st.session_state.max_trials
        return_a, return_b = st.session_state.fund_returns_data.get(current_trial, (0.11, 0.03))
        portfolio_return = (final_a/100)*return_a + (final_b/100)*return_b
        
        save_allocation(st.session_state.trial, 'final', final_a, final_b, portfolio_return)
        
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
    elif st.session_state.page == 'demographics':
        show_demographics()
    elif st.session_state.page == 'trial':
        handle_trial_steps()
    elif st.session_state.page == 'final':
        show_final()
    elif st.session_state.page == 'debrief':
        show_debrief()
    
    if st.session_state.page not in ['intro', 'demographics']:
        show_progress()

if __name__ == "__main__":
    main()