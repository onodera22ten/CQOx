"""
Diagnostic Chart Generators with Thresholds - 可視化仕様書準拠

Generates diagnostic charts for causal inference with:
- SMD threshold line (0.1)
- IV F-statistic threshold (10.0)
- Other quality diagnostic thresholds

Reference: /home/hirokionodera/CQO/可視化.pdf p.7
"""

from typing import List, Dict, Optional
import numpy as np
import plotly.graph_objects as go
from pathlib import Path

from backend.core.visualization import (
    ChartMetadata,
    Unit,
    THRESHOLDS,
    get_plotly_layout_config,
    get_plotly_config,
    create_threshold_line,
)


def plot_balance_smd(
    covariates: List[str],
    smd_before: List[float],
    smd_after: List[float],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Balance Check - Standardized Mean Difference (SMD)

    Shows SMD before and after matching/weighting with threshold line at 0.1
    """
    meta = ChartMetadata(
        title="Balance Check - Standardized Mean Difference",
        unit=Unit.RATIO,
        period=period,
        sample_size=sample_size,
        subtitle=f"SMD threshold = {THRESHOLDS.SMD_THRESHOLD} (ideal < {THRESHOLDS.SMD_IDEAL})",
    )

    fig = go.Figure()

    # SMD Before matching
    fig.add_trace(go.Scatter(
        x=covariates,
        y=smd_before,
        mode="markers",
        name="Before Matching",
        marker=dict(
            size=12,
            color="#EF4444",  # Red
            symbol="circle",
            line=dict(color="#1F2937", width=1),
        ),
        hovertemplate="Covariate: %{x}<br>SMD Before: %{y:.3f}<extra></extra>",
    ))

    # SMD After matching
    fig.add_trace(go.Scatter(
        x=covariates,
        y=smd_after,
        mode="markers",
        name="After Matching",
        marker=dict(
            size=12,
            color="#10B981",  # Green
            symbol="diamond",
            line=dict(color="#1F2937", width=1),
        ),
        hovertemplate="Covariate: %{x}<br>SMD After: %{y:.3f}<extra></extra>",
    ))

    # Add threshold line at 0.1
    fig.add_shape(create_threshold_line(
        threshold_value=THRESHOLDS.SMD_THRESHOLD,
        threshold_name=f"SMD Threshold ({THRESHOLDS.SMD_THRESHOLD})",
        axis="y",
        color="#DC2626",
        dash="dash",
    ))

    # Add ideal threshold at 0.05
    fig.add_shape(create_threshold_line(
        threshold_value=THRESHOLDS.SMD_IDEAL,
        threshold_name=f"Ideal SMD ({THRESHOLDS.SMD_IDEAL})",
        axis="y",
        color="#10B981",
        dash="dot",
    ))

    # Add annotations for thresholds
    fig.add_annotation(
        x=len(covariates) - 1,
        y=THRESHOLDS.SMD_THRESHOLD,
        text=f"Threshold ({THRESHOLDS.SMD_THRESHOLD})",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font=dict(size=11, color="#DC2626"),
        bgcolor="rgba(255, 255, 255, 0.8)",
    )

    layout = get_plotly_layout_config(meta, height=600)
    layout["xaxis"]["title"] = "Covariate"
    layout["yaxis"]["title"] = "Standardized Mean Difference"
    layout["yaxis"]["range"] = [0, max(max(smd_before), max(smd_after)) * 1.2]
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


def plot_iv_first_stage_f(
    instruments: List[str],
    f_statistics: List[float],
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    IV First-Stage F-Statistics

    Shows F-statistics for each instrument with threshold at 10.0 (weak) and 20.0 (strong)
    """
    meta = ChartMetadata(
        title="IV First-Stage F-Statistics",
        unit=Unit.RATIO,
        period=period,
        sample_size=sample_size,
        subtitle=f"F > {THRESHOLDS.IV_F_THRESHOLD} = valid, F > {THRESHOLDS.IV_F_STRONG} = strong",
    )

    # Color by threshold
    colors = [
        "#EF4444" if f < THRESHOLDS.IV_F_THRESHOLD else
        "#F59E0B" if f < THRESHOLDS.IV_F_STRONG else
        "#10B981"
        for f in f_statistics
    ]

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=instruments,
        y=f_statistics,
        marker=dict(
            color=colors,
            line=dict(color="#1F2937", width=1),
        ),
        text=[f"{f:.1f}" for f in f_statistics],
        textposition="outside",
        hovertemplate="Instrument: %{x}<br>F-Statistic: %{y:.2f}<extra></extra>",
        showlegend=False,
    ))

    # Weak instrument threshold (F=10)
    fig.add_shape(create_threshold_line(
        threshold_value=THRESHOLDS.IV_F_THRESHOLD,
        threshold_name=f"Weak IV Threshold ({THRESHOLDS.IV_F_THRESHOLD})",
        axis="y",
        color="#DC2626",
        dash="dash",
    ))

    # Strong instrument threshold (F=20)
    fig.add_shape(create_threshold_line(
        threshold_value=THRESHOLDS.IV_F_STRONG,
        threshold_name=f"Strong IV Threshold ({THRESHOLDS.IV_F_STRONG})",
        axis="y",
        color="#10B981",
        dash="dot",
    ))

    # Annotations
    fig.add_annotation(
        x=len(instruments) - 1,
        y=THRESHOLDS.IV_F_THRESHOLD,
        text=f"Weak Threshold ({THRESHOLDS.IV_F_THRESHOLD})",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font=dict(size=11, color="#DC2626"),
        bgcolor="rgba(255, 255, 255, 0.8)",
    )

    fig.add_annotation(
        x=len(instruments) - 1,
        y=THRESHOLDS.IV_F_STRONG,
        text=f"Strong Threshold ({THRESHOLDS.IV_F_STRONG})",
        showarrow=False,
        xanchor="left",
        yanchor="bottom",
        font=dict(size=11, color="#10B981"),
        bgcolor="rgba(255, 255, 255, 0.8)",
    )

    layout = get_plotly_layout_config(meta, height=600, show_legend=False)
    layout["xaxis"]["title"] = "Instrument"
    layout["yaxis"]["title"] = "F-Statistic"
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)


def plot_propensity_overlap(
    propensity_treated: np.ndarray,
    propensity_control: np.ndarray,
    output_path: Path,
    period: str = "2024-Q1",
    sample_size: int = 1000,
) -> str:
    """
    Propensity Score Overlap

    Shows distribution of propensity scores with overlap threshold lines
    """
    meta = ChartMetadata(
        title="Propensity Score Overlap",
        unit=Unit.PROBABILITY,
        period=period,
        sample_size=sample_size,
        subtitle=f"Overlap region: [{THRESHOLDS.OVERLAP_MIN}, {THRESHOLDS.OVERLAP_MAX}]",
    )

    fig = go.Figure()

    # Treated group histogram
    fig.add_trace(go.Histogram(
        x=propensity_treated,
        nbinsx=50,
        name="Treated",
        marker=dict(color="#3B82F6", opacity=0.6),
        hovertemplate="Propensity: %{x:.3f}<br>Count: %{y}<extra></extra>",
    ))

    # Control group histogram
    fig.add_trace(go.Histogram(
        x=propensity_control,
        nbinsx=50,
        name="Control",
        marker=dict(color="#EF4444", opacity=0.6),
        hovertemplate="Propensity: %{x:.3f}<br>Count: %{y}<extra></extra>",
    ))

    # Minimum overlap threshold
    fig.add_vline(
        x=THRESHOLDS.OVERLAP_MIN,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"Min Overlap ({THRESHOLDS.OVERLAP_MIN})",
        annotation_position="top",
    )

    # Maximum overlap threshold
    fig.add_vline(
        x=THRESHOLDS.OVERLAP_MAX,
        line_dash="dash",
        line_color="#F59E0B",
        annotation_text=f"Max Overlap ({THRESHOLDS.OVERLAP_MAX})",
        annotation_position="top",
    )

    layout = get_plotly_layout_config(meta, height=600)
    layout["xaxis"]["title"] = "Propensity Score"
    layout["yaxis"]["title"] = "Count"
    layout["barmode"] = "overlay"
    fig.update_layout(**layout)

    config = get_plotly_config()
    fig.write_html(str(output_path), config=config)

    return str(output_path)
