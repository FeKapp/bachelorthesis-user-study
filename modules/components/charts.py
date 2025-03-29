import plotly.graph_objects as go

def performance_chart(data_df):
    fig = go.Figure(data=[
        go.Bar(
            x=data_df['Category'],
            y=data_df['Performance'],
            marker_color=['green' if p >= 0 else 'red' for p in data_df['Performance']],
            text=[f"{val:.2f}%" for val in data_df['Performance']],
            textposition='outside'
        )
    ])
    fig.update_layout(
        yaxis_title='Performance (%)',
        showlegend=False,
        margin=dict(t=20, b=20),
        height=400
    )
    return fig