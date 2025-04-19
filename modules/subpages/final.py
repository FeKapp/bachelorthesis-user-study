import streamlit as st
import os
from modules.database import supabase, update_session_progress, save_allocation, save_demographics

def show_final():
    st.title("Final Allocation")

    st.markdown(":red[This is your final allocation: Please allocate your assets to Fund A (0-100%) and Fund B (0-100%) for the **next 50 years**.]")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## Fund A")
        st.image(os.path.join("assets", "images", "fund_A.png"), width=200)
        final_a = st.number_input("Allocation to Fund A (%)", min_value=0, max_value=100, value= None, key="demo_initial_a")
    with col2:
        st.markdown("## Fund B")
        st.image(os.path.join("assets", "images", "fund_B.png"), width=200)
        final_b = st.number_input("Automatic allocation to Fund B (%)", min_value=0, max_value=100, value= (100 - final_a) if final_a is not None else 0, key="demo_initial_b", disabled=True)

    if st.button("Submit Final Allocation"):
        if final_a is None:
            st.error("Allocation to Fund A (0% - 100%) is required.")
        else:
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