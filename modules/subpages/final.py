import streamlit as st
import os
import pandas as pd
from datetime import datetime
import pycountry
from modules.database import supabase, update_session_progress, save_allocation, save_demographics
from modules.components.charts import create_performance_bar_chart

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
        # If not found, default returns
        return_a, return_b = st.session_state.fund_returns_data.get(current_trial, (0.11, 0.03))
        portfolio_return = (final_a/100)*return_a + (final_b/100)*return_b

        # Save final
        save_allocation(
            st.query_params['session_id'],
            st.session_state.trial,
            'final',
            final_a,
            final_b,
            portfolio_return
        )

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

        st.session_state.page = 'debrief'
        update_session_progress(st.query_params['session_id'])
        st.rerun()