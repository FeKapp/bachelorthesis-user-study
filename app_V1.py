import streamlit as st
import numpy as np
import pandas as pd
import altair as alt
from datetime import datetime

# Initialize session state
if 'page' not in st.session_state:
    st.session_state.page = 'intro'
if 'trials' not in st.session_state:
    st.session_state.trials = 0
if 'ai_recommendation' not in st.session_state:
    st.session_state.ai_recommendation = None
if 'final_allocation' not in st.session_state:
    st.session_state.final_allocation = False

def main():
    if st.session_state.page == 'intro':
        show_intro()
    elif st.session_state.page == 'allocation':
        show_allocation()
    elif st.session_state.page == 'results':
        show_results()
    elif st.session_state.page == 'final':
        show_final()
    elif st.session_state.page == 'debrief':
        show_debrief()

def show_intro():
    st.title("Fund Allocation Simulation")
    st.write("""
    Welcome to the fund allocation study!
    
    In this experiment, you'll allocate investments between two funds:
    - Fund A: High risk/return (11% mean, 15% stdev)
    - Fund B: Low risk/return (3% mean, 5% stdev)
    
    You'll go through 5 rounds of allocations with AI recommendations.
    """)
    
    if st.button("Start Experiment"):
        st.session_state.page = 'allocation'
        st.rerun()

def show_allocation():
    st.title("Fund Allocation")
    
    if st.session_state.trials >= 5:
        st.session_state.page = 'final'
        st.rerun()
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Fund A")
        default = st.session_state.ai_recommendation if st.session_state.ai_recommendation else 50
        fund_a = st.number_input("Percentage for Fund A", 0, 100, default, key=f"a_{st.session_state.trials}")
    
    with col2:
        st.subheader("Fund B")
        fund_b = 100 - fund_a
        st.write(f"Automatically calculated: {fund_b}%")

    if st.button("Allocate Funds"):
        # Generate returns
        return_a = np.random.normal(0.11, 0.15)
        return_b = np.random.normal(0.03, 0.05)
        portfolio_return = (fund_a/100)*return_a + (fund_b/100)*return_b
        
        # Save to CSV
        save_data(fund_a, fund_b, return_a, return_b, portfolio_return, 'pre_ai')
        
        # Generate AI recommendation
        st.session_state.ai_recommendation = np.random.randint(0, 101)
        st.session_state.current_returns = {
            'fund_a': return_a,
            'fund_b': return_b,
            'portfolio': portfolio_return
        }
        
        st.session_state.page = 'results'
        st.rerun()

def show_results():
    st.title("Investment Results")
    
    # # Display results
    # returns = st.session_state.current_returns
    # chart_data = pd.DataFrame({
    #     'Returns': [returns['fund_a'], returns['fund_b'], returns['portfolio']],
    #     'Type': ['Fund A', 'Fund B', 'Portfolio']
    # })
    
    # st.bar_chart(chart_data.set_index('Type'))

        # Get the returns data
    returns = st.session_state.current_returns

    # Create a DataFrame
    chart_data = pd.DataFrame({
        'Returns': [returns['fund_a'], returns['fund_b'], returns['portfolio']],
        'Type': ['Fund A', 'Fund B', 'Portfolio']
    })

    # Create an Altair bar chart with conditional coloring
    chart = alt.Chart(chart_data).mark_bar().encode(
        x=alt.X('Type:N', title='Type'),
        y=alt.Y('Returns:Q', title='Returns'),
        color=alt.condition(
            alt.datum.Returns >= 0,  # Condition for positive returns
            alt.value('green'),      # Color if condition is True
            alt.value('red')         # Color if condition is False
        )
    )

    # Display the chart in Streamlit
    st.altair_chart(chart, use_container_width=True)


    
    # Show AI recommendation
    ai_rec = st.session_state.ai_recommendation
    st.info(f"AI Recommendation: {ai_rec}% Fund A, {100-ai_rec}% Fund B")
    
    # Save post-AI allocation
    if st.button("Continue with Recommendation"):
        save_data(ai_rec, 100-ai_rec, 
                 np.random.normal(0.11, 0.15), 
                 np.random.normal(0.03, 0.05), 
                 (ai_rec/100)*0.11 + ((100-ai_rec)/100)*0.03,
                 'post_ai')
        
        st.session_state.trials += 1
        st.session_state.ai_recommendation = None
        st.session_state.page = 'allocation'
        st.rerun()

def show_final():
    st.title("Final Allocation")
    st.write("This is your final asset allocation")
    
    fund_a = st.number_input("Final percentage for Fund A", 0, 100, 50)
    fund_b = 100 - fund_a
    
    if st.button("Submit Final Allocation"):
        return_a = np.random.normal(0.11, 0.15)
        return_b = np.random.normal(0.03, 0.05)
        portfolio_return = (fund_a/100)*return_a + (fund_b/100)*return_b
        
        save_data(fund_a, fund_b, return_a, return_b, portfolio_return, 'final')
        st.session_state.page = 'debrief'
        st.rerun()

def show_debrief():
    st.title("Study Complete")
    st.write("Thank you for participating in our study!")
    
    if st.checkbox("I consent to my data being used for research purposes"):
        if st.button("Confirm Consent"):
            st.success("Thank you for your participation!")
            # Add consent timestamp to CSV if needed

def save_data(fund_a, fund_b, return_a, return_b, portfolio_return, allocation_type):
    data = {
        'timestamp': datetime.now(),
        'trial': st.session_state.trials + 1,
        'type': allocation_type,
        'fund_a': fund_a,
        'fund_b': fund_b,
        'return_a': return_a,
        'return_b': return_b,
        'portfolio_return': portfolio_return
    }
    
    df = pd.DataFrame([data])
    df.to_csv('allocations.csv', mode='a', 
              header=not pd.io.common.file_exists('allocations.csv'), 
              index=False)

if __name__ == "__main__":
    main()