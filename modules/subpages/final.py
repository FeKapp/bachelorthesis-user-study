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

def show_debrief():
    st.title("Study Complete")
    st.write("**Thank you for participating!**")

    all_countries = sorted([c.name for c in pycountry.countries])
    priority_countries = ["Switzerland", "Singapore"]
    other_countries = [c for c in all_countries if c not in priority_countries]
    country_list = priority_countries + sorted(other_countries)

    with st.form(key="debrief_form", enter_to_submit=False):
        # Expertise
        st.subheader("Expertise")
        st.write("We would like to know how you rate your expertise with topics relevant to this research.")
        ai_proficiency = st.radio(
            "How would you rate your expertise in AI on a scale from novice to expert?",
            options=[1, 2, 3, 4, 5, 6, 7],
            horizontal=True,
            format_func=lambda x: f"{x} - {['Novice','','','','','','Expert'][x-1]}"
        )
        financial_literacy = st.radio(
            "How would you rate your financial literacy on a scale from novice to expert?",
            options=[1, 2, 3, 4, 5, 6, 7],
            horizontal=True,
            format_func=lambda x: f"{x} - {['Novice','','','','','','Expert'][x-1]}"
        )

        # Demographics
        st.markdown("---")
        st.subheader("Demographic information")
        country = st.selectbox("Country of Residence", options=["Select a country"] + country_list)

        place_of_birth = st.text_input("Place of Birth (optional)", value="", key="birth_place")

        gender = st.selectbox(
            "Gender",
            options=["Select Gender", "Male", "Female", "non-binary", "prefer not to disclose", "prefer to self-describe"]
        )
        if gender == "prefer to self-describe":
            gender = st.text_input("Please specify", value="prefer to self-describe")

        age = st.number_input("Age", min_value=18, max_value=100, value=None, step=1)

        education_level = st.selectbox("Highest Level of Education", options=[
            "Select Education Level",
            "No school",
            "Primary School",
            "High School",
            "Vocational training",
            "Tertiary (college, university)",
            "PhD",
            "Prefer not to say",
            "Other"
        ])

        # Data Quality
        st.markdown("---")
        st.subheader("Data Quality")
        st.write("We would like to know whether or not you have answered the questions carefully.")
        use_data = st.radio(
            "In your honest opinion, Should we use your data in our analyses in this study?",
            options=["Yes", "No"],
            index=0
        )
        comment = st.text_area("If you chose 'No', why do you think we should not use your data?")

        if st.form_submit_button("Finalize Submission"):
            validation_errors = []
            if country == "Select a country":
                validation_errors.append("Country of residence is required")
            if gender == "Select Gender":
                validation_errors.append("Gender is required")
            if gender == "prefer to self-describe":
                validation_errors.append("Please self-describe your gender")
            if age is None:
                validation_errors.append("Age is required")
            if education_level == "Select Education Level":
                validation_errors.append("Education level is required")

            if validation_errors:
                for error in validation_errors:
                    st.error(error)
            else:
                # Save demographics
                save_demographics(st.query_params['session_id'], {
                    'country': country,
                    'gender': gender,
                    'age': age,
                    'education_level': education_level,
                    'ai_proficiency': ai_proficiency,
                    'financial_literacy': financial_literacy
                })

                # Update "instructed response" (place_of_birth is optional)
                instructed_response = (place_of_birth.strip() == "")
                supabase.table('sessions').update({
                    'instructed_response_1_passed': instructed_response
                }).eq('session_id', st.query_params['session_id']).execute()

                # Mark session as complete
                supabase.table('sessions').update({
                    'completed_at': datetime.now().isoformat(),
                    'data_quality': (use_data == "Yes"),
                    'data_quality_comment': comment if use_data == "No" else None
                }).eq('session_id', st.query_params['session_id']).execute()

                st.success("Thank you for your participation! Your data has been saved.")
                st.balloons()
