import os
import uuid
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
import streamlit as st

# Load environment variables here so it's done once
load_dotenv()

# Create a global Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def update_session_progress(session_id: str):
    """Update session progress in database."""
    supabase.table('sessions').update({
        'current_page': st.session_state.page,
        'current_trial': st.session_state.trial,
        'current_trial_step': st.session_state.trial_step
    }).eq('session_id', session_id).execute()

def save_allocation(session_id: str, trial_num, allocation_type, fund_a, fund_b, portfolio_return=None):
    """Save allocation to Supabase."""
    trial_response = supabase.table('trials') \
        .select('trial_id') \
        .eq('session_id', session_id) \
        .eq('trial_number', trial_num) \
        .execute()

    trial_id = trial_response.data[0]['trial_id'] if trial_response.data else str(uuid.uuid4())

    # If trial doesn't exist yet, create it
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

def save_demographics(session_id: str, data: dict):
    """Save demographic data to Supabase."""
    supabase.table('demographics').insert({
        'demographic_id': str(uuid.uuid4()),
        'session_id': session_id,
        **data,
        'created_at': datetime.now().isoformat()
    }).execute()

def load_session_data(session_id: str):
    """
    Load the session data from 'sessions' table,
    along with trials and their allocations.
    """
    session_response = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
    if session_response.data:
        session_data = session_response.data[0]
        trials_response = supabase.table('trials').select('*').eq('session_id', session_id).execute()

        fund_returns = {}
        allocations = {}

        for trial in trials_response.data:
            fund_returns[trial['trial_number']] = (trial['return_a'], trial['return_b'])

            alloc_response = supabase.table('allocations') \
                .select('*') \
                .eq('trial_id', trial['trial_id']) \
                .execute()

            allocations[trial['trial_number']] = {'initial': None, 'ai': None, 'final': None}
            for alloc in alloc_response.data:
                allocations[trial['trial_number']][alloc['allocation_type']] = (
                    alloc['fund_a'],
                    alloc['fund_b']
                )

        return session_data, fund_returns, allocations

    return None, {}, {}
