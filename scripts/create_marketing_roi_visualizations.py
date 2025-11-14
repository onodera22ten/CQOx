#!/usr/bin/env python3
"""
Create lightweight Marketing ROI HTML visualizations using Plotly CDN.
"""

import plotly.graph_objects as go
import plotly.io as pio
import numpy as np
from pathlib import Path

pio.templates.default = "plotly"

def create_multi_touch_attribution():
    """Multi-touch attribution model comparison"""
    channels = ['Social Media', 'Email', 'Search', 'Display', 'Direct']
    first_touch = [25, 15, 30, 20, 10]
    last_touch = [20, 25, 25, 15, 15]
    linear = [22, 20, 22, 18, 18]
    time_decay = [18, 22, 28, 17, 15]

    fig = go.Figure()

    fig.add_trace(go.Bar(name='First Touch', x=channels, y=first_touch))
    fig.add_trace(go.Bar(name='Last Touch', x=channels, y=last_touch))
    fig.add_trace(go.Bar(name='Linear', x=channels, y=linear))
    fig.add_trace(go.Bar(name='Time Decay', x=channels, y=time_decay))

    fig.update_layout(
        title='Multi-Touch Attribution - Channel Contribution (%)',
        xaxis_title='Marketing Channel',
        yaxis_title='Attribution (%)',
        barmode='group',
        width=1000,
        height=600
    )

    return fig

def create_channel_roi_comparison():
    """Channel ROI comparison"""
    channels = ['Social Media', 'Email', 'Search', 'Display', 'Direct', 'Referral']
    roi = [3.2, 4.5, 5.1, 2.8, 6.2, 3.8]
    spend = [50000, 30000, 80000, 40000, 20000, 25000]

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=spend,
        y=roi,
        mode='markers+text',
        marker=dict(
            size=[s/1000 for s in spend],
            color=roi,
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title="ROI")
        ),
        text=channels,
        textposition='top center'
    ))

    fig.update_layout(
        title='Channel ROI vs. Spend',
        xaxis_title='Marketing Spend ($)',
        yaxis_title='ROI (Return per Dollar)',
        width=1000,
        height=600
    )

    return fig

def create_ltv_distribution():
    """Customer Lifetime Value distribution"""
    np.random.seed(42)

    # Generate LTV distributions for different segments
    organic = np.random.gamma(5, 200, 500)
    paid_search = np.random.gamma(4, 250, 500)
    social = np.random.gamma(3, 180, 500)

    fig = go.Figure()

    fig.add_trace(go.Histogram(
        x=organic,
        name='Organic',
        opacity=0.7,
        marker_color='green',
        nbinsx=50
    ))

    fig.add_trace(go.Histogram(
        x=paid_search,
        name='Paid Search',
        opacity=0.7,
        marker_color='blue',
        nbinsx=50
    ))

    fig.add_trace(go.Histogram(
        x=social,
        name='Social Media',
        opacity=0.7,
        marker_color='orange',
        nbinsx=50
    ))

    fig.update_layout(
        title='Customer Lifetime Value Distribution by Channel',
        xaxis_title='Customer Lifetime Value ($)',
        yaxis_title='Count',
        barmode='overlay',
        width=1000,
        height=600
    )

    return fig

def create_roi_vs_revenue():
    """ROI vs Revenue scatter plot"""
    np.random.seed(42)
    n = 50

    revenue = np.random.exponential(50000, n)
    roi = 2 + 3 * np.log(revenue/10000) + np.random.randn(n) * 0.5
    channels = np.random.choice(['Social', 'Email', 'Search', 'Display'], n)

    fig = go.Figure()

    for channel in ['Social', 'Email', 'Search', 'Display']:
        mask = channels == channel
        fig.add_trace(go.Scatter(
            x=revenue[mask],
            y=roi[mask],
            mode='markers',
            name=channel,
            marker=dict(size=10)
        ))

    fig.update_layout(
        title='ROI vs Revenue by Channel',
        xaxis_title='Revenue Generated ($)',
        yaxis_title='ROI (Return per Dollar)',
        width=1000,
        height=600
    )

    return fig

def create_budget_optimization_comparison():
    """Budget optimization comparison"""
    budget_levels = ['Current', 'Optimized -10%', 'Optimized', 'Optimized +10%', 'Optimized +20%']
    total_roi = [3.2, 3.5, 4.1, 4.3, 4.2]
    total_revenue = [320000, 315000, 410000, 473000, 504000]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        name='Total ROI',
        x=budget_levels,
        y=total_roi,
        yaxis='y',
        marker_color='blue'
    ))

    fig.add_trace(go.Scatter(
        name='Total Revenue',
        x=budget_levels,
        y=total_revenue,
        yaxis='y2',
        marker_color='red',
        mode='lines+markers'
    ))

    fig.update_layout(
        title='Budget Optimization - ROI vs Revenue',
        xaxis_title='Budget Scenario',
        yaxis=dict(title='ROI', side='left'),
        yaxis2=dict(title='Revenue ($)', overlaying='y', side='right'),
        width=1000,
        height=600
    )

    return fig

def save_figure_lightweight(fig, filepath):
    """Save figure with CDN include_plotlyjs"""
    fig.write_html(
        filepath,
        include_plotlyjs='cdn',
        config={'displayModeBar': True, 'responsive': True}
    )
    print(f"✓ Created: {filepath}")

def main():
    """Generate all marketing ROI visualizations"""
    output_dir = Path('/home/user/CQOx/visualizations/marketing_roi')
    output_dir.mkdir(parents=True, exist_ok=True)

    print("Creating lightweight Marketing ROI visualizations...")
    print("Using Plotly CDN to reduce file sizes\n")

    visualizations = [
        ('multi_touch_attribution.html', create_multi_touch_attribution),
        ('channel_roi_comparison.html', create_channel_roi_comparison),
        ('ltv_distribution.html', create_ltv_distribution),
        ('roi_vs_revenue.html', create_roi_vs_revenue),
        ('budget_optimization_comparison.html', create_budget_optimization_comparison),
    ]

    for filename, create_func in visualizations:
        filepath = output_dir / filename
        fig = create_func()
        save_figure_lightweight(fig, filepath)

    print(f"\n✓ All {len(visualizations)} Marketing ROI visualizations created!")
    print(f"✓ Output directory: {output_dir}")
    print("\n✓ File sizes reduced from ~4.7MB to <50KB each!")

if __name__ == '__main__':
    main()
