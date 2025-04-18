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
            textfont=dict(
                color='black',
                size=14   # Setzt die Prozentangaben auf schwarz
            )    
        ),
    ])
    
    #set the fixed range based on returns analysis for scenarios
    if st.session_state.max_trials == 100:
        fixed_y_range = [-35, 35]
    else:
        fixed_y_range = [-120, 120]

    fig.update_layout(
    xaxis=dict(
        tickfont=dict(
            color='black',
            size= 18  # Set the font size
        )
    ),
    # black axis title
    yaxis_title= 'Performance (%)' ,
    yaxis_title_font=dict(
        color='black',
        size= 14  # Set the font size
    ),
    yaxis=dict(range=fixed_y_range),
    showlegend=False,
    margin=margin if margin else dict(t=20, b=20),
    shapes=[
            dict(
                type='line',
                # 'x' so we place it at an x-value instead of in normalized [0..1] figure space
                xref='x',
                yref='paper',     # 'paper' -> spans the entire plot area in the y-direction
                x0=1.5,           # mid-way between bar at x=1 and bar at x=2
                x1=1.5,
                y0=0,             # bottom of the plotting area
                y1=1,             # top of the plotting area
                line=dict(
                    color='black',
                    dash='dot',    # makes it dotted
                    width=2
                )
            )
        ]
    )

    return fig

