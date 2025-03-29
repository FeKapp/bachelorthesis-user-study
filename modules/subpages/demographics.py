import streamlit as st
import pycountry
from modules.database import supabase, save_demographics, update_session_progress

def show_demographics():
    st.title("Demographic Questionnaire")

    # Get country list
    all_countries = sorted([c.name for c in pycountry.countries])
    priority_countries = ["Switzerland", "Singapore"]
    other_countries = [c for c in all_countries if c not in priority_countries]
    country_list = priority_countries + sorted(other_countries)

    with st.form(key="demographic_form", enter_to_submit=False):
        st.write("Please answer the following questions before we begin:")

        # Country selection with placeholder option
        country = st.selectbox("Country of Residence", options=["Select a country"] + country_list)

        # Place of Birth is optional
        place_of_birth = st.text_input("Place of Birth", value="", key="birth_place")

        # Gender selection with placeholder
        gender = st.selectbox("Gender", options=["Select Gender", "Male", "Female", "Prefer not to say"])

        # Use 0 as default for age
        age = st.number_input("Age", min_value=0, max_value=100, value=0, step=1)

        # Education level
        education_level = st.selectbox("Highest Level of Education", options=[
            "Select Education Level",
            "Mandatory Education (Primary/Secondary)",
            "Vocational Education (EFZ, apprenticeship)",
            "Baccalaureate (Gymnasium)",
            "Higher Vocational Education (PET, Diploma)",
            "University (Bachelor's Degree)",
            "University (Master's Degree)",
            "Doctoral Degree (PhD)",
            "Other"
        ])

        # AI proficiency
        ai_options = ["Select AI proficiency"] + [
            f"{i} - {['Novice','','','','','','Expert'][i-1]}" for i in range(1, 8)
        ]
        ai_proficiency = st.radio(
            "How would you rate your proficiency with Artificial Intelligence?",
            options=ai_options,
            horizontal=True
        )

        # Financial literacy
        fin_options = ["Select Financial Literacy"] + [
            f"{i} - {['Novice','','','','','','Expert'][i-1]}" for i in range(1, 8)
        ]
        financial_literacy = st.radio(
            "How would you rate your financial literacy?",
            options=fin_options,
            horizontal=True
        )

        submit = st.form_submit_button("Submit Demographics")

        if submit:
            # Validate
            if (country == "Select a country" or
                gender == "Select Gender" or
                age == 0 or
                education_level == "Select Education Level" or
                ai_proficiency == "Select AI proficiency" or
                financial_literacy == "Select Financial Literacy"):
                
                st.warning("Please fill in all required fields before submitting.")
            else:
                ai_value = int(ai_proficiency.split(" - ")[0])
                fin_value = int(financial_literacy.split(" - ")[0])

                save_demographics(st.query_params['session_id'], {
                    'country': country,
                    'gender': gender,
                    'age': age,
                    'education_level': education_level,
                    'ai_proficiency': ai_value,
                    'financial_literacy': fin_value
                })

                # Update "instructed response" if place_of_birth is empty
                instructed_response = (place_of_birth.strip() == "")
                supabase.table('sessions').update({
                    'instructed_response_1_passed': instructed_response
                }).eq('session_id', st.query_params['session_id']).execute()

                st.session_state.page = 'trial'
                update_session_progress(st.query_params['session_id'])
                st.rerun()
