import streamlit as st
import pandas as pd
import os
from modules.database import supabase, update_session_progress
from modules.components.charts import create_performance_bar_chart

def handle_demo_steps():
    if st.session_state.trial_step == 1:
        show_demo_initial()
    elif st.session_state.trial_step == 2:
        show_demo_ai()
    elif st.session_state.trial_step == 3:
        show_demo_performance()

def show_demo_initial():
    st.title("Demo: Initial Allocation")
    
    # Demo description initial allocation step
    with st.container(border=True):
        st.markdown("""
        :red[This is a demo step: You are about to make your **initial allocation**:]
        - :red[Allocate **0% to 100%** of your assets to **Fund A**.]
        - :red[The remainder (100% minus your chosen % for Fund A) 
        automatically goes to **Fund B**.]
        - :red[When you’re ready, click **Submit Allocation**.]
        """)

    if st.session_state.max_trials == 100:
        st.markdown("Please allocate your assets to Fund A (0-100%) and Fund B (0-100%) for the **next 3 months**.")
    else:
        st.markdown("Please allocate your assets to Fund A (0-100%) and Fund B (0-100%) for the **next 5 years**.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## Fund A 🔵")
        st.image(os.path.join("assets", "images", "fund_A.png"), width=200)
        initial_a = st.number_input(
            "Allocation to Fund A (%)",
            min_value=0,
            max_value=100,
            value=None,
            key="demo_initial_a"
        )
    with col2:
        st.markdown("## Fund B 🟡")
        st.image(os.path.join("assets", "images", "fund_B.png"), width=200)
        initial_b = st.number_input(
            "Automatic allocation to Fund B (%)",
            min_value=0,
            max_value=100,
            value=(100 - initial_a) if initial_a is not None else 0,
            key="demo_initial_b",
            disabled=True
        )
        # st.write(f"Automatic allocation: {initial_b}%")

    if st.button("Submit Allocation"):
        if initial_a is None:
            st.error("Please specify a percentage for Fund A (0% – 100%).")
        else:
            st.session_state.demo_data['initial_a'] = initial_a
            st.session_state.demo_data['initial_b'] = initial_b

            st.session_state.trial_step = 2
            update_session_progress(st.query_params['session_id'])
            st.rerun()

def show_demo_ai():
    st.title("Demo: AI Recommendation")
    
    # Demo description AI recommendation step
    with st.container(border=True):
        st.markdown("""
        :red[This is a demo step: You will receive an **AI Recommendation**:] 
        - :red[On the left side under **Your Initial Allocation**, you will see your initial allocation in the previous step.]
        - :red[On the right side under **AI Recommendation**, you will see the AI's suggested allocation.]
        - :red[Based on this information, you can adjust your allocation to Fund A (0-100%) or re-enter your initial allocation.]
        - :red[Note: The AI recommendation **here in the demo** is randomly generated for illustration purpose. The real values will be shown as soon as the experiment starts.]
        - :red[Once you have entered your allocation, click on **Submit Allocation**.]
        """)

    # Display user and AI allocations
    initial_a = st.session_state.demo_data['initial_a']
    initial_b = st.session_state.demo_data['initial_b']
    ai_a = st.session_state.demo_data['ai_a']
    ai_b = st.session_state.demo_data['ai_b']

    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Your Initial Allocation 👤")
            st.metric("Fund A:", f"{initial_a}%")
            st.metric("Fund B:", f"{initial_b}%")
        
    with col2:
        with st.container(border=True):
            st.subheader("AI Recommendation ✨")
            st.metric("Fund A:", f"{ai_a}%")
            st.metric("Fund B:", f"{ai_b}%")
            
    st.markdown("---")
    st.markdown("Based on your initial allocation and the AI recommendation, how do you allocate your assets?")
    col3, col4 = st.columns(2)
    with col3:
        final_a = st.number_input("Allocation to Fund A (%)", min_value=0, max_value=100, value= None, key="adjusted_a")

    with col4:
        final_b = st.number_input("Automatic allocation to Fund B (%)", min_value=0, max_value=100, value= (100 - final_a) if final_a is not None else 0, key="adjusted_b", disabled=True)
        # st.write(f"Automatic allocation: {adjusted_b}%")

    if st.button("Submit Allocation"):
        if final_a is None:
            st.error("Allocation to Fund A is required.")
        else:
            st.session_state.demo_data['final_a'] = final_a
            st.session_state.demo_data['final_b'] = final_b

            st.session_state.trial_step = 3
            update_session_progress(st.query_params['session_id'])
            st.rerun()
    
def show_demo_performance():
    st.title("Demo: Performance Overview")
    
    # Demo description performance overview step
    with st.container(border=True):
        st.markdown("""
        :red[This is a demo step: You now see the **performance overview** of your allocation:]
        - :red[In the allocation breakdown, you can see your and the AI's allocation to Fund A and Fund B.]
        - :red[In the bar chart, you can see the performance for the given investment period of your portfolio, the AI suggested portfolio, Fund A and Fund B.]
        - :red[The bar in the chart will be green if the performance is positive and red if it is negative.]
        - :red[Note: The returns of Fund A and Fund B **here in the demo** are randomly generated for illustration purpose. The real values will be shown as soon as the experiment starts.]
        - :red[To terminate the demo and start with the experiment, click on **Start Experiment**.]
        """)

    # Calculate returns using demo data
    return_a = st.session_state.demo_data['return_a']
    return_b = st.session_state.demo_data['return_b']
    final_a = st.session_state.demo_data['final_a']
    final_b = st.session_state.demo_data['final_b']
    ai_a = st.session_state.demo_data['ai_a']
    ai_b = st.session_state.demo_data['ai_b']

    ai_return = (ai_a/100) * return_a + \
                (ai_b/100) * return_b
    user_return = (final_a/100) * return_a +  (final_b/100) * return_b  

    df = pd.DataFrame({
        'Category': ['Your Portfolio 👤', 'AI Portfolio ✨', 'Fund A 🔵', 'Fund B 🟡'],
        'Performance': [user_return*100, ai_return*100, return_a*100, return_b*100 ]
    })

    if st.session_state.max_trials == 100:
        duration = "last 3 months"
    else:
        duration = "last 5 years"

    st.markdown(f"""
    Allocation breakdown:
    - Your Portfolio: **Fund A**: {final_a}%, **Fund B**: {final_b}%
    - AI portfolio: **Fund A**: {ai_a}%, **Fund B**: {ai_b}%""")

    st.markdown(f"Overview how your portfolio, the AI portfolio, Fund A and Fund B performed in the **{duration}**:")
    
    fig = create_performance_bar_chart(df, margin=dict(t=20, b=20))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(":red[This is the end of the demo. You can now start the experiment.]")

    if st.button("Start Experiment"):
        st.session_state.page = 'trial'
        st.session_state.trial_step = 1
        update_session_progress(st.query_params['session_id'])
        st.rerun()
