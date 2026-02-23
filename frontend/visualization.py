import plotly.graph_objects as go

def build_spider_chart(ratios: dict, ticker: str, color: str, ratio_labels: dict) -> go.Figure:
    """Build a radar/spider chart for a single company's Altman ratios."""
    keys   = ['x1', 'x2', 'x3', 'x4', 'x5']
    labels = ['x1', 'x2', 'x3', 'x4', 'x5']
    values = [ratios.get(k) or 0.0 for k in keys]

    # Close the polygon
    r      = values + [values[0]]
    theta  = labels + [labels[0]]
    hover  = [
        f"<b>{lbl}</b><br>{ratio_labels[k]}<br>Value: {v:.4f}<extra></extra>"
        for lbl, k, v in zip(labels, keys, values)
    ] + [f"<b>{labels[0]}</b><br>{ratio_labels[keys[0]]}<br>Value: {values[0]:.4f}<extra></extra>"]

    # Low-opacity fill derived from the classification colour (hex → rgba)
    r_ch = int(color[1:3], 16)
    g_ch = int(color[3:5], 16)
    b_ch = int(color[5:7], 16)
    fill_color = f"rgba({r_ch},{g_ch},{b_ch},0.25)"

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=r,
        theta=theta,
        fill='toself',
        fillcolor=fill_color,
        line=dict(color=color, width=2),
        hovertemplate=hover,
        name=ticker,
    ))

    fig.update_layout(
        polar=dict(
            bgcolor="#161A23",
            radialaxis=dict(
                visible=True,
                color="#6B7280",
                gridcolor="#252A36",
                linecolor="#252A36",
                tickfont=dict(size=9, color="#6B7280"),
            ),
            angularaxis=dict(
                color="#9CA3AF",
                gridcolor="#252A36",
                linecolor="#252A36",
                tickfont=dict(size=12, color="#E8EAF0"),
            ),
        ),
        paper_bgcolor="#161A23",
        font=dict(color="#9CA3AF"),
        margin=dict(l=50, r=50, t=30, b=30),
        showlegend=False,
        height=300,
    )
    return fig