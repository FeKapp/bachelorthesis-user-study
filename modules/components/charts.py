import plotly.graph_objects as go

def create_performance_bar_chart(df, margin=None):
    """
    Create a bar chart for performance data in the same style as the original code.
    df should have columns: 'Category' and 'Performance' (in %).
    """
    fig = go.Figure(data=[
        go.Bar(
            x=df['Category'],
            y=df['Performance'],
            marker_color=['green' if p >= 0 else 'red' for p in df['Performance']],
            text=[f"{val:.2f}%" for val in df['Performance']],
            textposition='outside'
        )
    ])

    fig.update_layout(
        yaxis_title='Performance (%)',
        showlegend=False,
        margin=margin if margin else dict(t=20, b=20)
    )
    return fig
