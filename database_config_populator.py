# %% [markdown]
# # Database Configuration Populator
# 
# This notebook creates and populates the experiment scenarios with required financial data and AI recommendations.

# %%
import numpy as np
import pandas as pd
from supabase import create_client
import os
import uuid
from tqdm import tqdm

# Database Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# %% [markdown]
# ## 1. Scenario Configuration

# %%
scenarios = [
    {
        "scenario_name": "short_unbiased",
        "ai_type": "unbiased",
        "num_trials": 5,
        "periods_per_trial": 20,
        "description": "5 trials with 20 periods each, unbiased AI"
    },
    {
        "scenario_name": "short_biased",
        "ai_type": "biased",
        "num_trials": 5,
        "periods_per_trial": 20,
        "description": "5 trials with 20 periods each, biased AI"
    },
    {
        "scenario_name": "long_unbiased",
        "ai_type": "unbiased",
        "num_trials": 100,
        "periods_per_trial": 1,
        "description": "100 trials with 1 period each, unbiased AI"
    },
    {
        "scenario_name": "long_biased",
        "ai_type": "biased",
        "num_trials": 100,
        "periods_per_trial": 1,
        "description": "100 trials with 1 period each, biased AI"
    }
]

# Insert scenarios into database
for scenario in scenarios:
    record = {
        "scenario_id": str(uuid.uuid4()),
        **scenario
    }
    supabase.table("scenario_config").insert(record).execute()

# %% [markdown]
# ## 2. Generate Fund Returns

# %%
def generate_returns(scenario_name, num_trials, periods_per_trial):
    """Generate returns for a single scenario"""
    returns = []
    scenario_id = supabase.table("scenario_config").select("scenario_id").eq("scenario_name", scenario_name).execute().data[0]["scenario_id"]
    
    for trial in range(num_trials):
        # Generate periodic returns
        a_returns = np.random.normal(0.0025, 0.00177, periods_per_trial)  # 0.25% mean, 0.177% std
        b_returns = np.random.normal(0.01, 0.0354, periods_per_trial)     # 1% mean, 3.54% std
        
        # Convert to total returns
        total_a = np.prod(1 + a_returns) - 1
        total_b = np.prod(1 + b_returns) - 1
        
        returns.append({
            "fund_return_id": str(uuid.uuid4()),
            "scenario_id": scenario_id,
            "trial_number": trial + 1,  # Trials are 1-indexed
            "return_a": float(total_a),
            "return_b": float(total_b)
        })
    
    # Batch insert
    supabase.table("fund_returns").insert(returns).execute()

# Generate for all scenarios
for scenario in tqdm(scenarios, desc="Generating returns"):
    generate_returns(
        scenario["scenario_name"],
        scenario["num_trials"],
        scenario["periods_per_trial"]
    )

# %% [markdown]
# ## 3. Generate AI Recommendations

# %%
def generate_recommendations(scenario_name):
    """Generate AI recommendations for a scenario"""
    scenario = supabase.table("scenario_config").select("*").eq("scenario_name", scenario_name).execute().data[0]
    recommendations = []
    
    for trial in range(scenario["num_trials"]):
        if scenario["ai_type"] == "biased":
            fund_a = 100.0
            fund_b = 0.0
        else:
            fund_a = np.random.randint(0, 101)
            fund_b = 100 - fund_a
        
        recommendations.append({
            "recommendation_id": str(uuid.uuid4()),
            "scenario_id": scenario["scenario_id"],
            "trial_number": trial + 1,  # 1-indexed
            "fund_a": float(fund_a),
            "fund_b": float(fund_b)
        })
    
    # Batch insert
    supabase.table("ai_recommendations").insert(recommendations).execute()

# Generate for all scenarios
for scenario in tqdm(scenarios, desc="Generating AI recommendations"):
    generate_recommendations(scenario["scenario_name"])

# %% [markdown]
# ## 4. Verification

# %%
def verify_data():
    """Verify database population"""
    # Count scenarios
    scenarios = supabase.table("scenario_config").select("count", count="exact").execute().count
    print(f"Scenarios created: {scenarios}")
    
    # Count fund returns
    for scenario in supabase.table("scenario_config").select("*").execute().data:
        returns = supabase.table("fund_returns").select("count", count="exact").eq("scenario_id", scenario["scenario_id"]).execute().count
        print(f"{scenario['scenario_name']} returns: {returns}")
        
    # Count recommendations
    for scenario in supabase.table("scenario_config").select("*").execute().data:
        recs = supabase.table("ai_recommendations").select("count", count="exact").eq("scenario_id", scenario["scenario_id"]).execute().count
        print(f"{scenario['scenario_name']} recommendations: {recs}")

verify_data()