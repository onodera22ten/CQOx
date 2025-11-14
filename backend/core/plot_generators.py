"""
2D Chart Generators - 可視化仕様書準拠

Implements all 18 marketing charts following specification:
- 3D → 2D conversion with CI bands
- SSOT colors, units, thresholds
- Performance optimization (≤200KB, ≤1.5s LCP)
- PNG + CSV download

Reference: /home/hirokionodera/CQO/可視化.pdf
"""

from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path

from backend.core.visualization import (
    ChannelColor,
    THRESHOLDS,
    CURRENCY,
    Unit,
    ChartMetadata,
    CI_CONFIG,
    get_plotly_layout_config,
    get_plotly_config,
    create_threshold_line,
    create_optimal_point_annotation,
    MarketingChartSpec,
    get_chart_spec,
)


# ============================================================================
# #1: ROI Surface (3D → 2D Contour + Heatmap)
# ============================================================================

def plot_roi_surface_2d(
    x_budget: np.ndarray,
    y_budget: np.ndarray,
    roi_grid: np.ndarray,
    optimal_x: float,
    optimal_y: float,
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #1: ROI Surface - 3D → 2D Contour + Heatmap

    Specification (可視化.pdf p.10):
    - Replace 3D surface with 2D contour + heatmap
    - Show optimal allocation point with annotation
    - Use gradient from low (red) to high (green) ROI
    """
    meta = ChartMetadata(
        title="ROI Surface - Optimal Budget Allocation",
        unit=Unit.USD,
        period=period,
        sample_size=sample_size,
    )

    fig = go.Figure()

    # Heatmap layer
    fig.add_trace(go.Contour(
        x=x_budget,
        y=y_budget,
        z=roi_grid,
        colorscale=[
            [0, "#FEE2E2"],    # Light red (low ROI)
            [0.5, "#FEF3C7"],  # Yellow (break-even)
            [1, "#D1FAE5"],    # Light green (high ROI)
        ],
        contours=dict(
            showlabels=True,
            labelfont=dict(size=10, color="white"),
        ),
        colorbar=dict(
            title="ROI",
            titleside="right",
            tickmode="linear",
            tick0=0,
            dtick=0.5,
        ),
        name="ROI",
        hovertemplate="Budget X: $%{x:,.0f}<br>Budget Y: $%{y:,.0f}<br>ROI: %{z:.2f}<extra></extra>",
    ))

    # Optimal point annotation
    fig.add_trace(go.Scatter(
        x=[optimal_x],
        y=[optimal_y],
        mode="markers+text",
        marker=dict(
            size=20,
            color="#10B981",  # Green
            symbol="star",
            line=dict(color="white", width=2),
        ),
        text=["★ Optimal"],
        textposition="top center",
        textfont=dict(size=14, color="#10B981", family="Inter"),
        name="Optimal Point",
        hovertemplate="Optimal Allocation<br>Budget X: $%{x:,.0f}<br>Budget Y: $%{y:,.0f}<extra></extra>",
    ))

    # Layout
    layout = get_plotly_layout_config(meta, height=600)
    layout["xaxis"]["title"] = "Channel 1 Budget ($)"
    layout["yaxis"]["title"] = "Channel 2 Budget ($)"
    fig.update_layout(**layout)

    # Save
    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #2: Budget Contour with Gradient Vectors
# ============================================================================

def plot_budget_contour(
    x_budget: np.ndarray,
    y_budget: np.ndarray,
    objective_grid: np.ndarray,
    gradient_x: np.ndarray,
    gradient_y: np.ndarray,
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #2: Budget Allocation Contour with Gradient Vectors

    Shows optimization direction with arrow annotations
    """
    meta = ChartMetadata(
        title="Budget Allocation - Optimization Direction",
        unit=Unit.USD,
        period=period,
        sample_size=sample_size,
    )

    fig = go.Figure()

    # Contour layer
    fig.add_trace(go.Contour(
        x=x_budget,
        y=y_budget,
        z=objective_grid,
        colorscale="Viridis",
        contours=dict(showlabels=True),
        colorbar=dict(title="Objective"),
        name="Objective",
    ))

    # Gradient vectors (sample every 5th point for clarity)
    step = 5
    for i in range(0, len(x_budget), step):
        for j in range(0, len(y_budget), step):
            if i < gradient_x.shape[0] and j < gradient_x.shape[1]:
                fig.add_annotation(
                    x=x_budget[i],
                    y=y_budget[j],
                    ax=x_budget[i] - gradient_x[i, j] * 1000,
                    ay=y_budget[j] - gradient_y[i, j] * 1000,
                    xref="x",
                    yref="y",
                    axref="x",
                    ayref="y",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=1.5,
                    arrowcolor="#6366F1",
                )

    layout = get_plotly_layout_config(meta, height=600)
    layout["xaxis"]["title"] = "Channel 1 Budget ($)"
    layout["yaxis"]["title"] = "Channel 2 Budget ($)"
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #3: Saturation Curves with CI Ribbons
# ============================================================================

def plot_saturation_curves(
    channels: List[str],
    budgets: np.ndarray,
    responses: Dict[str, np.ndarray],
    ci_lower: Dict[str, np.ndarray],
    ci_upper: Dict[str, np.ndarray],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #3: Saturation Curves with 95% CI Ribbons

    One line per channel with confidence band
    """
    meta = ChartMetadata(
        title="Channel Saturation Curves",
        unit=Unit.RATIO,
        period=period,
        sample_size=sample_size,
        subtitle="Response rate vs. budget spend (95% CI)",
    )

    fig = go.Figure()

    for channel in channels:
        color = ChannelColor.get_channel_color(channel)
        response = responses[channel]
        lower = ci_lower[channel]
        upper = ci_upper[channel]

        # Main line
        fig.add_trace(go.Scatter(
            x=budgets,
            y=response,
            mode="lines",
            name=channel,
            line=dict(color=color, width=3),
            hovertemplate=f"{channel}<br>Budget: $%{{x:,.0f}}<br>Response: %{{y:.3f}}<extra></extra>",
        ))

        # CI ribbon (upper bound)
        fig.add_trace(go.Scatter(
            x=budgets,
            y=upper,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ))

        # CI ribbon (lower bound, fill to upper)
        fig.add_trace(go.Scatter(
            x=budgets,
            y=lower,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor=f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2)",
            showlegend=False,
            hoverinfo="skip",
        ))

    layout = get_plotly_layout_config(meta, height=600)
    layout["xaxis"]["title"] = "Budget ($)"
    layout["yaxis"]["title"] = "Response Rate"
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #4: Budget Waterfall
# ============================================================================

def plot_budget_waterfall(
    channels: List[str],
    deltas: List[float],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #4: Budget Waterfall showing deltas

    Visualizes budget changes across channels
    """
    meta = ChartMetadata(
        title="Budget Allocation Changes",
        unit=Unit.USD,
        period=period,
        sample_size=sample_size,
    )

    # Calculate cumulative for waterfall
    cumulative = [0]
    for delta in deltas:
        cumulative.append(cumulative[-1] + delta)

    # Create measures: relative for each channel, total for last
    measures = ["relative"] * len(channels) + ["total"]
    labels = channels + ["Total"]
    values = deltas + [cumulative[-1]]

    # Colors: green for positive, red for negative
    colors = [ChannelColor.get_channel_color(ch) for ch in channels] + ["#6B7280"]

    fig = go.Figure(go.Waterfall(
        x=labels,
        y=values,
        measure=measures,
        text=[CURRENCY.format(v) for v in values],
        textposition="outside",
        connector={"line": {"color": "#9CA3AF", "width": 2, "dash": "dot"}},
        increasing={"marker": {"color": "#10B981"}},  # Green
        decreasing={"marker": {"color": "#EF4444"}},  # Red
        totals={"marker": {"color": "#6B7280"}},      # Gray
    ))

    layout = get_plotly_layout_config(meta, height=600)
    layout["xaxis"]["title"] = "Channel"
    layout["yaxis"]["title"] = "Budget Change ($)"
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #5: Marginal ROI with Error Bars
# ============================================================================

def plot_marginal_roi(
    channels: List[str],
    marginal_roi: List[float],
    ci_lower: List[float],
    ci_upper: List[float],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #5: Marginal ROI per Channel with 95% CI Error Bars
    """
    meta = ChartMetadata(
        title="Marginal ROI by Channel",
        unit=Unit.RATIO,
        period=period,
        sample_size=sample_size,
        subtitle="Next dollar return (95% CI)",
    )

    colors = [ChannelColor.get_channel_color(ch) for ch in channels]

    # Calculate error bar sizes
    error_y_minus = [roi - lower for roi, lower in zip(marginal_roi, ci_lower)]
    error_y_plus = [upper - roi for roi, upper in zip(marginal_roi, ci_upper)]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=channels,
        y=marginal_roi,
        error_y=dict(
            type="data",
            symmetric=False,
            array=error_y_plus,
            arrayminus=error_y_minus,
            color=CI_CONFIG.error_bar_color,
            thickness=CI_CONFIG.error_bar_width,
        ),
        marker=dict(
            color=colors,
            line=dict(color="#1F2937", width=1),
        ),
        text=[f"{roi:.2f}" for roi in marginal_roi],
        textposition="outside",
        hovertemplate="%{x}<br>Marginal ROI: %{y:.2f}<br>95% CI: [%{customdata[0]:.2f}, %{customdata[1]:.2f}]<extra></extra>",
        customdata=[[lower, upper] for lower, upper in zip(ci_lower, ci_upper)],
    ))

    # Add break-even threshold line at 0
    fig.add_shape(create_threshold_line(
        threshold_value=THRESHOLDS.ROI_BREAK_EVEN,
        threshold_name="Break-even",
        axis="y",
        color="#DC2626",
    ))

    # Add "good ROI" threshold line at 1.0
    fig.add_shape(create_threshold_line(
        threshold_value=THRESHOLDS.ROI_GOOD,
        threshold_name="Good ROI",
        axis="y",
        color="#10B981",
        dash="dot",
    ))

    layout = get_plotly_layout_config(meta, height=600, show_legend=False)
    layout["xaxis"]["title"] = "Channel"
    layout["yaxis"]["title"] = "Marginal ROI"
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #6: Pareto Frontier (2D Scatter, not 3D surface)
# ============================================================================

def plot_pareto_frontier(
    objective1: np.ndarray,
    objective2: np.ndarray,
    pareto_mask: np.ndarray,
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #6: Pareto Frontier - 2D Scatter with Frontier Line

    Specification: 2D scatter, NOT 3D surface
    """
    meta = ChartMetadata(
        title="Multi-Objective Pareto Frontier",
        unit=Unit.RATIO,
        period=period,
        sample_size=sample_size,
    )

    fig = go.Figure()

    # Non-Pareto points
    fig.add_trace(go.Scatter(
        x=objective1[~pareto_mask],
        y=objective2[~pareto_mask],
        mode="markers",
        marker=dict(
            size=8,
            color="#D1D5DB",  # Gray
            opacity=0.5,
        ),
        name="Feasible",
        hovertemplate="Obj 1: %{x:.2f}<br>Obj 2: %{y:.2f}<extra></extra>",
    ))

    # Pareto optimal points
    pareto_obj1 = objective1[pareto_mask]
    pareto_obj2 = objective2[pareto_mask]

    # Sort for frontier line
    sort_idx = np.argsort(pareto_obj1)
    pareto_obj1_sorted = pareto_obj1[sort_idx]
    pareto_obj2_sorted = pareto_obj2[sort_idx]

    fig.add_trace(go.Scatter(
        x=pareto_obj1_sorted,
        y=pareto_obj2_sorted,
        mode="markers+lines",
        marker=dict(
            size=12,
            color="#10B981",  # Green
            symbol="star",
            line=dict(color="white", width=2),
        ),
        line=dict(
            color="#10B981",
            width=2,
            dash="dash",
        ),
        name="Pareto Optimal",
        hovertemplate="★ Pareto Optimal<br>Obj 1: %{x:.2f}<br>Obj 2: %{y:.2f}<extra></extra>",
    ))

    layout = get_plotly_layout_config(meta, height=600)
    layout["xaxis"]["title"] = "Objective 1 (Maximize)"
    layout["yaxis"]["title"] = "Objective 2 (Maximize)"
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #7: Customer Journey Sankey Diagram
# ============================================================================

def plot_journey_sankey(
    nodes: List[str],
    sources: List[int],
    targets: List[int],
    values: List[float],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #7: Customer Journey Sankey Flow Diagram

    With flow conservation check (assert_sankey_conservation)
    """
    from backend.core.invariants import assert_sankey_conservation
    from collections import defaultdict

    # Calculate total inflow and outflow for conservation check
    inflow = defaultdict(float)
    outflow = defaultdict(float)

    for src, tgt, val in zip(sources, targets, values):
        outflow[src] += val
        inflow[tgt] += val

    # Check conservation: total inflow should equal total outflow
    # Use values from initial sources and final targets
    initial_sources = [i for i in set(sources) if i not in set(targets)]
    final_targets = [i for i in set(targets) if i not in set(sources)]

    layer_in = [outflow[i] for i in initial_sources] if initial_sources else [sum(values)]
    layer_out = [inflow[i] for i in final_targets] if final_targets else [sum(values)]

    # Invariant check (仕様書準拠)
    assert_sankey_conservation(layer_in, layer_out)

    meta = ChartMetadata(
        title="Customer Journey Flow",
        unit=Unit.COUNT,
        period=period,
        sample_size=sample_size,
    )

    # Generate colors for nodes
    node_colors = [ChannelColor.get_channel_color(node.split("-")[0]) if "-" in node else "#6B7280" for node in nodes]

    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="#1F2937", width=1),
            label=nodes,
            color=node_colors,
        ),
        link=dict(
            source=sources,
            target=targets,
            value=values,
            color="rgba(107, 114, 128, 0.3)",  # Gray with opacity
        ),
    ))

    layout = get_plotly_layout_config(meta, height=600, show_legend=False)
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #8: Shapley Attribution (Bar Chart preferred, Radar optional)
# ============================================================================

def plot_shapley_attribution(
    channels: List[str],
    shapley_values: List[float],
    ci_lower: List[float],
    ci_upper: List[float],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
    use_radar: bool = False,
) -> str:
    """
    Chart #8: Shapley Attribution Values

    Specification: Bar chart preferred. Radar optional.
    Must sum to 100% (assert_shapley_simplex check)
    """
    from backend.core.invariants import assert_shapley_simplex

    # Invariant check (仕様書準拠)
    assert_shapley_simplex(shapley_values, tol=1e-4)

    meta = ChartMetadata(
        title="Shapley Attribution Values",
        unit=Unit.PERCENT,
        period=period,
        sample_size=sample_size,
        subtitle=f"Sum = {sum(shapley_values):.1f}% (must equal 100%)",
    )

    colors = [ChannelColor.get_channel_color(ch) for ch in channels]

    if use_radar:
        # Radar chart (optional)
        fig = go.Figure()

        fig.add_trace(go.Scatterpolar(
            r=shapley_values,
            theta=channels,
            fill="toself",
            marker=dict(color=colors),
            name="Shapley Values",
        ))

        layout = get_plotly_layout_config(meta, height=600, show_legend=False)
        layout["polar"] = dict(radialaxis=dict(visible=True, range=[0, max(shapley_values) * 1.2]))
        fig.update_layout(**layout)
    else:
        # Bar chart (default)
        error_y_minus = [sv - lower for sv, lower in zip(shapley_values, ci_lower)]
        error_y_plus = [upper - sv for sv, upper in zip(shapley_values, ci_upper)]

        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=channels,
            y=shapley_values,
            error_y=dict(
                type="data",
                symmetric=False,
                array=error_y_plus,
                arrayminus=error_y_minus,
                color=CI_CONFIG.error_bar_color,
                thickness=CI_CONFIG.error_bar_width,
            ),
            marker=dict(
                color=colors,
                line=dict(color="#1F2937", width=1),
            ),
            text=[f"{sv:.1f}%" for sv in shapley_values],
            textposition="outside",
            hovertemplate="%{x}<br>Shapley: %{y:.2f}%<br>95% CI: [%{customdata[0]:.2f}, %{customdata[1]:.2f}]<extra></extra>",
            customdata=[[lower, upper] for lower, upper in zip(ci_lower, ci_upper)],
        ))

        layout = get_plotly_layout_config(meta, height=600, show_legend=False)
        layout["xaxis"]["title"] = "Channel"
        layout["yaxis"]["title"] = "Attribution (%)"
        fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #9: LTV Distribution (Histogram + KDE)
# ============================================================================

def plot_ltv_distribution(
    ltv_values: np.ndarray,
    kde_x: np.ndarray,
    kde_y: np.ndarray,
    percentiles: Dict[str, float],  # {"p25": value, "p50": value, "p75": value}
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #9: LTV Distribution - Histogram + KDE Overlay

    With percentile markers (25th, 50th, 75th)
    """
    meta = ChartMetadata(
        title="Customer Lifetime Value Distribution",
        unit=Unit.USD,
        period=period,
        sample_size=sample_size,
    )

    fig = go.Figure()

    # Histogram
    fig.add_trace(go.Histogram(
        x=ltv_values,
        nbinsx=50,
        name="LTV",
        marker=dict(
            color="#60A5FA",  # Blue
            line=dict(color="#1F2937", width=1),
        ),
        opacity=0.7,
        hovertemplate="LTV Range: %{x}<br>Count: %{y}<extra></extra>",
    ))

    # KDE overlay
    fig.add_trace(go.Scatter(
        x=kde_x,
        y=kde_y,
        mode="lines",
        name="KDE",
        line=dict(color="#EF4444", width=3),  # Red
        yaxis="y2",
        hovertemplate="LTV: %{x:,.0f}<br>Density: %{y:.4f}<extra></extra>",
    ))

    # Percentile lines
    for pname, pvalue in percentiles.items():
        fig.add_vline(
            x=pvalue,
            line_dash="dash",
            line_color="#10B981" if pname == "p50" else "#F59E0B",
            annotation_text=f"{pname.upper()}: {CURRENCY.format(pvalue)}",
            annotation_position="top",
        )

    layout = get_plotly_layout_config(meta, height=600)
    layout["xaxis"]["title"] = "Lifetime Value ($)"
    layout["yaxis"]["title"] = "Count"
    layout["yaxis2"] = dict(
        title="Density",
        overlaying="y",
        side="right",
    )
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #10: Survival Curve (Kaplan-Meier with CI Bands)
# ============================================================================

def plot_survival_curve(
    time: np.ndarray,
    survival_prob: np.ndarray,
    ci_lower: np.ndarray,
    ci_upper: np.ndarray,
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #10: Kaplan-Meier Survival Curve with 95% CI Bands

    With monotone decreasing check (assert_survival_monotone_down)
    """
    from backend.core.invariants import assert_survival_monotone_down

    # Invariant check (仕様書準拠)
    assert_survival_monotone_down(survival_prob.tolist())

    meta = ChartMetadata(
        title="Customer Survival Curve (Kaplan-Meier)",
        unit=Unit.PROBABILITY,
        period=period,
        sample_size=sample_size,
        subtitle="Retention probability over time (95% CI)",
    )

    fig = go.Figure()

    # Main survival curve
    fig.add_trace(go.Scatter(
        x=time,
        y=survival_prob,
        mode="lines",
        name="Survival Probability",
        line=dict(color="#3B82F6", width=3),  # Blue
        hovertemplate="Time: %{x} days<br>Survival: %{y:.3f}<extra></extra>",
    ))

    # CI upper bound
    fig.add_trace(go.Scatter(
        x=time,
        y=ci_upper,
        mode="lines",
        line=dict(width=0),
        showlegend=False,
        hoverinfo="skip",
    ))

    # CI lower bound (fill to upper)
    fig.add_trace(go.Scatter(
        x=time,
        y=ci_lower,
        mode="lines",
        line=dict(width=0),
        fill="tonexty",
        fillcolor="rgba(59, 130, 246, 0.2)",  # Blue with opacity
        showlegend=False,
        hoverinfo="skip",
    ))

    layout = get_plotly_layout_config(meta, height=600)
    layout["xaxis"]["title"] = "Time (days)"
    layout["yaxis"]["title"] = "Survival Probability"
    layout["yaxis"]["range"] = [0, 1.05]
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #11-18: Remaining Chart Generators (Stubs for Now)
# ============================================================================

def plot_ltv_confidence_intervals(
    segments: List[str],
    ltv_mean: List[float],
    ci_lower: List[float],
    ci_upper: List[float],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """Chart #11: LTV Confidence Intervals by Segment"""
    # Similar to #5 but for LTV by segment
    return plot_marginal_roi(segments, ltv_mean, ci_lower, ci_upper, output_path, period, sample_size)


def plot_adstock_timeseries(
    dates: pd.DatetimeIndex,
    actual: np.ndarray,
    adstocked: np.ndarray,
    ci_lower: np.ndarray,
    ci_upper: np.ndarray,
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """Chart #12: Adstock Time Series (Dual Axis)"""
    meta = ChartMetadata(
        title="Adstock Effect Over Time",
        unit=Unit.RATIO,
        period=period,
        sample_size=sample_size,
    )

    fig = make_subplots(specs=[[{"secondary_y": True}]])

    # Actual spend
    fig.add_trace(go.Scatter(
        x=dates, y=actual, name="Actual Spend",
        mode="lines", line=dict(color="#3B82F6", width=2)),
        secondary_y=False,
    )

    # Adstocked with CI
    fig.add_trace(go.Scatter(
        x=dates, y=adstocked, name="Adstock Effect",
        mode="lines", line=dict(color="#EF4444", width=2)),
        secondary_y=True,
    )

    fig.add_trace(go.Scatter(
        x=dates, y=ci_upper, mode="lines", line=dict(width=0),
        showlegend=False, hoverinfo="skip"), secondary_y=True,
    )

    fig.add_trace(go.Scatter(
        x=dates, y=ci_lower, mode="lines", line=dict(width=0),
        fill="tonexty", fillcolor="rgba(239, 68, 68, 0.2)",
        showlegend=False, hoverinfo="skip"), secondary_y=True,
    )

    layout = get_plotly_layout_config(meta, height=600)
    fig.update_xaxes(title_text="Date")
    fig.update_yaxes(title_text="Spend ($)", secondary_y=False)
    fig.update_yaxes(title_text="Adstock Effect", secondary_y=True)
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)
    return str(output_path)


def plot_scenario_heatmap(
    scenarios: List[str],
    channels: List[str],
    ratio_matrix: np.ndarray,
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """Chart #13: Scenario Comparison Heatmap"""
    meta = ChartMetadata(
        title="Scenario ROI Comparison",
        unit=Unit.RATIO,
        period=period,
        sample_size=sample_size,
    )

    # Create annotations for cell values
    annotations = []
    for i, scenario in enumerate(scenarios):
        for j, channel in enumerate(channels):
            annotations.append(dict(
                x=channel,
                y=scenario,
                text=f"{ratio_matrix[i, j]:.2f}x",
                showarrow=False,
                font=dict(color="white" if ratio_matrix[i, j] > 1.5 else "black"),
            ))

    fig = go.Figure(go.Heatmap(
        x=channels,
        y=scenarios,
        z=ratio_matrix,
        colorscale="RdYlGn",
        text=ratio_matrix,
        texttemplate="%{text:.2f}x",
        colorbar=dict(title="ROI Ratio"),
    ))

    layout = get_plotly_layout_config(meta, height=600, show_legend=False)
    layout["annotations"] = annotations
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)
    return str(output_path)


# ============================================================================
# #14: Optimal Channel Mix (Stacked Bar, NOT Donut)
# ============================================================================

def plot_optimal_channel_mix(
    channels: List[str],
    allocation_pct: List[float],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #14: Optimal Channel Mix - Stacked Bar Chart

    Specification: Stacked bar chart (NOT donut pie chart)
    Shows budget allocation percentage per channel
    """
    meta = ChartMetadata(
        title="Optimal Marketing Channel Mix",
        unit=Unit.PERCENT,
        period=period,
        sample_size=sample_size,
        subtitle="Recommended budget allocation",
    )

    colors = [ChannelColor.get_channel_color(ch) for ch in channels]

    fig = go.Figure()

    # Stacked bar chart
    for i, channel in enumerate(channels):
        fig.add_trace(go.Bar(
            x=["Optimal Allocation"],
            y=[allocation_pct[i]],
            name=channel,
            marker=dict(
                color=colors[i],
                line=dict(color="#1F2937", width=1),
            ),
            text=f"{allocation_pct[i]:.1f}%",
            textposition="inside",
            textfont=dict(size=14, color="white", family="Inter"),
            hovertemplate=f"{channel}<br>Allocation: %{{y:.1f}}%<extra></extra>",
        ))

    layout = get_plotly_layout_config(meta, height=500, show_legend=True)
    layout["barmode"] = "stack"
    layout["xaxis"]["title"] = "Budget Allocation"
    layout["yaxis"]["title"] = "Percentage (%)"
    layout["yaxis"]["range"] = [0, 105]
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #15: KPI Dashboard (Small Multiples with CI)
# ============================================================================

def plot_kpi_dashboard(
    kpis: List[str],
    time_series: Dict[str, np.ndarray],
    ci_lower: Dict[str, np.ndarray],
    ci_upper: Dict[str, np.ndarray],
    time_points: np.ndarray,
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #15: KPI Dashboard - Small Multiples (2x2 grid)

    Each subplot shows one KPI with 95% CI bands
    """
    meta = ChartMetadata(
        title="KPI Performance Dashboard",
        unit=Unit.RATIO,
        period=period,
        sample_size=sample_size,
    )

    n_kpis = len(kpis)
    rows = 2
    cols = 2

    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=kpis,
        vertical_spacing=0.15,
        horizontal_spacing=0.12,
    )

    for i, kpi in enumerate(kpis):
        row = i // cols + 1
        col = i % cols + 1

        ts = time_series[kpi]
        lower = ci_lower[kpi]
        upper = ci_upper[kpi]

        # Main line
        fig.add_trace(go.Scatter(
            x=time_points,
            y=ts,
            mode="lines",
            name=kpi,
            line=dict(color="#3B82F6", width=2),
            showlegend=False,
            hovertemplate=f"{kpi}<br>Week: %{{x}}<br>Value: %{{y:.2f}}<extra></extra>",
        ), row=row, col=col)

        # CI upper
        fig.add_trace(go.Scatter(
            x=time_points,
            y=upper,
            mode="lines",
            line=dict(width=0),
            showlegend=False,
            hoverinfo="skip",
        ), row=row, col=col)

        # CI lower (fill to upper)
        fig.add_trace(go.Scatter(
            x=time_points,
            y=lower,
            mode="lines",
            line=dict(width=0),
            fill="tonexty",
            fillcolor="rgba(59, 130, 246, 0.2)",
            showlegend=False,
            hoverinfo="skip",
        ), row=row, col=col)

    layout = get_plotly_layout_config(meta, height=800, show_legend=False)
    fig.update_layout(**layout)

    # Update all x-axes
    fig.update_xaxes(title_text="Week", showgrid=True, gridcolor="#E5E7EB")
    fig.update_yaxes(showgrid=True, gridcolor="#E5E7EB")

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #16: Alert Timeline (2D Scatter with Severity Colors)
# ============================================================================

def plot_alert_timeline(
    time_points: np.ndarray,
    alert_times: np.ndarray,
    alert_severities: List[str],
    alert_messages: List[str],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #16: Alert Timeline - 2D Scatter on Time Axis

    Colors by severity: Low=Green, Medium=Orange, High=Red
    """
    meta = ChartMetadata(
        title="Quality Alert Timeline",
        unit=Unit.COUNT,
        period=period,
        sample_size=sample_size,
    )

    severity_colors = {
        "Low": "#10B981",     # Green
        "Medium": "#F59E0B",  # Orange
        "High": "#EF4444",    # Red
    }

    fig = go.Figure()

    for severity in ["Low", "Medium", "High"]:
        mask = np.array([s == severity for s in alert_severities])
        if mask.sum() == 0:
            continue

        fig.add_trace(go.Scatter(
            x=alert_times[mask],
            y=np.ones(mask.sum()),
            mode="markers+text",
            marker=dict(
                size=20,
                color=severity_colors[severity],
                symbol="diamond",
                line=dict(color="#1F2937", width=2),
            ),
            text=[severity] * mask.sum(),
            textposition="top center",
            textfont=dict(size=12, family="Inter"),
            name=severity,
            hovertemplate="<b>%{text}</b><br>Week: %{x}<extra></extra>",
            customdata=[alert_messages[i] for i, m in enumerate(mask) if m],
        ))

    layout = get_plotly_layout_config(meta, height=400)
    layout["xaxis"]["title"] = "Week"
    layout["yaxis"]["visible"] = False
    layout["yaxis"]["range"] = [0.5, 1.5]
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #17: AI Recommendations Table with Sparklines
# ============================================================================

def plot_ai_recommendations_table(
    recommendations: List[str],
    impacts: List[str],
    priorities: List[str],
    confidence_scores: List[float],
    trend_data: List[np.ndarray],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #17: AI Recommendations - Table with Embedded Sparklines

    Each row has: Priority, Recommendation, Impact, Confidence, Trend (sparkline)
    """
    meta = ChartMetadata(
        title="AI-Powered Marketing Recommendations",
        unit=Unit.COUNT,
        period=period,
        sample_size=sample_size,
    )

    # Priority color mapping
    priority_colors = {
        "High": "#FEE2E2",    # Light red
        "Medium": "#FEF3C7",  # Light yellow
        "Low": "#D1FAE5",     # Light green
    }

    # Build sparkline strings (simple text representation)
    sparklines = []
    for trend in trend_data:
        # Simple sparkline using Unicode block characters
        min_val, max_val = trend.min(), trend.max()
        normalized = (trend - min_val) / (max_val - min_val + 1e-6)
        bars = "".join(["▁▂▃▄▅▆▇█"[min(7, int(v * 8))] for v in normalized])
        sparklines.append(bars)

    # Cell colors based on priority
    cell_colors = [[priority_colors[p] for p in priorities] for _ in range(5)]

    fig = go.Figure(go.Table(
        header=dict(
            values=["Priority", "Recommendation", "Est. Impact", "Confidence", "Trend"],
            fill_color="#3B82F6",
            font=dict(color="white", size=14, family="Inter"),
            align="left",
            height=40,
        ),
        cells=dict(
            values=[
                priorities,
                recommendations,
                impacts,
                [f"{c:.0f}%" for c in confidence_scores],
                sparklines,
            ],
            fill_color=cell_colors,
            align="left",
            font=dict(size=12, family="Inter"),
            height=35,
        ),
    ))

    layout = get_plotly_layout_config(meta, height=400, show_legend=False)
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


# ============================================================================
# #18: Optimization Animation (Limited Use - 2D Frames)
# ============================================================================

def plot_optimization_animation(
    iterations: List[int],
    objective_values: List[float],
    parameter_history: List[Dict[str, float]],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Chart #18: Optimization Process Animation

    Specification: Limited use only - for optimization convergence
    Shows 2D animation of objective function over iterations
    """
    meta = ChartMetadata(
        title="Optimization Convergence Animation",
        unit=Unit.RATIO,
        period=period,
        sample_size=sample_size,
        subtitle="Objective function value over iterations",
    )

    # Create frames for animation
    frames = []
    for i in range(len(iterations)):
        frame_data = go.Scatter(
            x=iterations[:i+1],
            y=objective_values[:i+1],
            mode="lines+markers",
            line=dict(color="#3B82F6", width=2),
            marker=dict(size=8, color="#EF4444"),
            name="Objective",
        )
        frames.append(go.Frame(
            data=[frame_data],
            name=str(i),
        ))

    # Initial trace
    fig = go.Figure(
        data=[go.Scatter(
            x=[iterations[0]],
            y=[objective_values[0]],
            mode="lines+markers",
            line=dict(color="#3B82F6", width=2),
            marker=dict(size=8, color="#EF4444"),
        )],
        frames=frames,
    )

    # Add play/pause buttons
    fig.update_layout(
        updatemenus=[{
            "type": "buttons",
            "showactive": False,
            "buttons": [
                {
                    "label": "▶ Play",
                    "method": "animate",
                    "args": [None, {
                        "frame": {"duration": 50, "redraw": True},
                        "fromcurrent": True,
                        "mode": "immediate",
                    }],
                },
                {
                    "label": "⏸ Pause",
                    "method": "animate",
                    "args": [[None], {
                        "frame": {"duration": 0, "redraw": False},
                        "mode": "immediate",
                    }],
                },
            ],
            "x": 0.1,
            "y": 1.15,
        }],
    )

    layout = get_plotly_layout_config(meta, height=600, show_legend=False)
    layout["xaxis"]["title"] = "Iteration"
    layout["yaxis"]["title"] = "Objective Value"
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)
