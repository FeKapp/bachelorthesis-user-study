# db.py
import os
from dotenv import load_dotenv
from supabase import create_client, Client
from typing import Optional
from datetime import datetime
import uuid

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_or_create_session(session_id: str, scenario: Optional[str] = None, 
                          ai_type: Optional[str] = None, max_trials: Optional[int] = None,
                          page: str = "intro", trial: int = 0, trial_step: int = 1):
    """
    If session_id exists in DB, return it. Otherwise create a new session row.
    """
    existing = supabase.table("sessions").select("*").eq("session_id", session_id).execute()
    if existing.data:
        return existing.data[0]
    # If not found, create a new session row
    created_at = datetime.utcnow().isoformat()
    new_session = {
        "session_id": session_id,
        "scenario": scenario,
        "ai_type": ai_type,
        "max_trials": max_trials,
        "current_page": page,
        "current_trial": trial,
        "current_trial_step": trial_step,
        "created_at": created_at
    }
    supabase.table("sessions").insert(new_session).execute()
    return new_session

def update_session(session_id: str, **kwargs):
    """
    Update the sessions table with the given fields.
    """
    supabase.table("sessions").update(kwargs).eq("session_id", session_id).execute()

def create_trial(session_id: str, trial_number: int, return_a: float, return_b: float):
    trial_id = str(uuid.uuid4())
    row = {
        "trial_id": trial_id,
        "session_id": session_id,
        "trial_number": trial_number,
        "return_a": return_a,
        "return_b": return_b,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("trials").insert(row).execute()
    return trial_id

def create_allocation(trial_id: str, allocation_type: str, fund_a: float, fund_b: float, 
                      portfolio_return: Optional[float] = None):
    allocation_id = str(uuid.uuid4())
    row = {
        "allocation_id": allocation_id,
        "trial_id": trial_id,
        "allocation_type": allocation_type,
        "fund_a": fund_a,
        "fund_b": fund_b,
        "portfolio_return": portfolio_return,
        "created_at": datetime.utcnow().isoformat()
    }
    supabase.table("allocations").insert(row).execute()

def fetch_latest_trial(session_id: str, trial_number: int):
    """Fetch an existing trial (if any) for this session + trial_number."""
    resp = supabase.table("trials") \
        .select("*") \
        .eq("session_id", session_id) \
        .eq("trial_number", trial_number) \
        .execute()
    data = resp.data
    return data[0] if data else None

def give_consent(session_id: str):
    """Mark the session as consent given."""
    supabase.table("sessions").update({
        "consent_given": True,
        "completed_at": datetime.utcnow().isoformat()
    }).eq("session_id", session_id).execute()
