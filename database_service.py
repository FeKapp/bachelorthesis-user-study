# database_service.py
from supabase_client import init_supabase
from datetime import datetime
import numpy as np

supabase = init_supabase()

def create_session(session_id):
    # Check if session exists
    existing = supabase.table('sessions').select('*').eq('session_id', session_id).execute()
    
    if not existing.data:
        # Create new session with random scenario
        scenario = np.random.choice(['short_unbiased', 'short_biased', 'long_unbiased', 'long_biased'])
        ai_type = 'biased' if 'biased' in scenario else 'unbiased'
        trial_count = 100 if 'long' in scenario else 5
        
        new_session = {
            "session_id": str(session_id),
            "scenario_type": scenario,
            "ai_type": ai_type,
            "trial_count": trial_count,
            "current_trial": 0,
            "trial_step": 1,
            "completed": False
        }
        supabase.table('sessions').insert(new_session).execute()
        return new_session
    return existing.data[0]

def save_allocation(session_id, trial_number, allocation_type, fund_a, fund_b):
    return supabase.table('allocations').insert({
        "session_id": str(session_id),
        "trial_number": trial_number,
        "allocation_type": allocation_type,
        "fund_a_percent": float(fund_a),
        "fund_b_percent": float(fund_b)
    }).execute()

def get_trial_data(scenario_type, trial_number):
    result = supabase.table('trial_data').select("*").eq(
        "scenario_type", scenario_type
    ).eq(
        "trial_number", trial_number
    ).execute()
    return result.data[0] if result.data else None

def update_session_progress(session_id, page, trial, trial_step):
    supabase.table('sessions').update({
        "current_page": page,
        "current_trial": trial,
        "trial_step": trial_step
    }).eq('session_id', session_id).execute()