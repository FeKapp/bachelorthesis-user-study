import streamlit as st
import pycountry
from modules.database import save_demographics

def show_demographics(session_id):
    st.title("Demographic Questionnaire")
    all_countries = sorted([c.name for c in pycountry.countries])
    priority_countries = ["Switzerland", "Singapore"]
    country_list = priority_countries + sorted([c for c in all_countries if c not in priority_countries])

    with st.form(key="demographic_form"):
        country = st.selectbox("Country of Residence", ["Select a country"] + country_list)
        place_of_birth = st.text_input("Place of Birth", "")
        gender = st.selectbox("Gender", ["Select Gender", "Male", "Female", "Prefer not to say"])
        age = st.number_input("Age", 0, 100, 0)
        education_level = st.selectbox("Highest Education", [
            "Select Education Level", "Mandatory Education", "Vocational Education", 
            "Baccalaureate", "Higher Vocational Education", "University (Bachelor's)", 
            "University (Master's)", "Doctoral Degree", "Other"
        ])
        
        ai_proficiency = st.radio("AI Proficiency", 
            ["Select AI proficiency"] + [f"{i} - {['Novice','','','','','','Expert'][i-1]}" for i in range(1, 8)],
            horizontal=True)
        
        financial_literacy = st.radio("Financial Literacy", 
            ["Select Financial Literacy"] + [f"{i} - {['Novice','','','','','','Expert'][i-1]}" for i in range(1, 8)],
            horizontal=True)

        if st.form_submit_button("Submit"):
            if (country.startswith("Select") or gender.startswith("Select") or 
                education_level.startswith("Select") or age == 0 or
                ai_proficiency.startswith("Select") or financial_literacy.startswith("Select")):
                st.error("Please fill all required fields")
            else:
                demographics = {
                    'country': country,
                    'gender': gender,
                    'age': age,
                    'education_level': education_level,
                    'ai_proficiency': int(ai_proficiency.split(" - ")[0]),
                    'financial_literacy': int(financial_literacy.split(" - ")[0])
                }
                save_demographics(session_id, demographics)
                st.session_state.page = 'trial'
                st.rerun()