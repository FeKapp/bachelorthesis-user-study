# import plotly.graph_objects as go

# def create_performance_bar_chart(df, margin=None):
#     """
#     Create a bar chart for performance data in the same style as the original code.
#     df should have columns: 'Category' and 'Performance' (in %).
#     """
#     fig = go.Figure(data=[
#         go.Bar(
#             x=df['Category'],
#             y=df['Performance'],
#             marker_color=['green' if p >= 0 else 'red' for p in df['Performance']],
#             text=[f"{val:.2f}%" for val in df['Performance']],
#             textposition='outside'
#         )
#     ])

#     fig.update_layout(
#         yaxis_title='Performance (%)',
#         showlegend=False,
#         margin=margin if margin else dict(t=20, b=20)
#     )
#     return fig

import plotly.graph_objects as go
import streamlit as st
import os

def create_performance_bar_chart(df, margin=None, fixed_y_range=None):
    """
    Create a bar chart for performance data.
    
    Parameters:
      - df: DataFrame with columns 'Category' and 'Performance' (in %)
      - margin: Optional dictionary to control figure margins
      - fixed_y_range: A tuple or list defining the fixed y-axis range (e.g., [-10, 10])
      
    This function fixes the y-axis scaling to ensure that a given return 
    always appears the same across different charts.
    """
    # Create the bar chart
    fig = go.Figure(data=[
        go.Bar(
            x=df['Category'],
            y=df['Performance'],
            marker_color=['green' if p >= 0 else 'red' for p in df['Performance']],
            text=[f"{val:.2f}%" for val in df['Performance']],
            textposition='outside',    
        ),
    ])
    
    # Note: Set this default based on the range relevant for your data.
    scenario = st.session_state.get('scenario_id')
    # Insert the scenario_id for the scenario "long" from the database
    
    #set the fixed range based on returns analysis
    if st.session_state.max_trials == 100:
        fixed_y_range = [-35, 35]
    else:
        fixed_y_range = [-150, 150]

    # Update layout to use the fixed y-axis range
    fig.update_layout(
        yaxis_title='Performance (%)',
        yaxis=dict(range=fixed_y_range),
        showlegend=False,
        margin=margin if margin else dict(t=20, b=20)
    )
    return fig

