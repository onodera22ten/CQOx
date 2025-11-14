"""
CSV Export Module - 可視化仕様書準拠

Exports chart data to CSV format alongside PNG visualizations.
Reference: /home/hirokionodera/CQO/可視化.pdf p.8
"""

from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np


def export_to_csv(
    data: Dict[str, Any],
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """
    Export chart data to CSV with metadata header

    Args:
        data: Dictionary of column_name -> values
        output_path: Path to save CSV file
        metadata: Optional metadata to include in header

    Returns:
        Path to saved CSV file
    """
    # Create DataFrame from data
    df = pd.DataFrame(data)

    # Write CSV with metadata header
    with open(output_path, 'w') as f:
        if metadata:
            f.write("# Chart Metadata\n")
            for key, value in metadata.items():
                f.write(f"# {key}: {value}\n")
            f.write("#\n")

        # Write DataFrame
        df.to_csv(f, index=False)

    return str(output_path)


# Specific export functions for each chart type

def export_roi_surface_csv(
    x_budget: np.ndarray,
    y_budget: np.ndarray,
    roi_grid: np.ndarray,
    optimal_x: float,
    optimal_y: float,
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Export ROI surface data to CSV"""
    # Flatten grid to long format
    rows = []
    for i, x in enumerate(x_budget):
        for j, y in enumerate(y_budget):
            rows.append({
                "budget_channel_1": x,
                "budget_channel_2": y,
                "roi": roi_grid[j, i],
                "is_optimal": (abs(x - optimal_x) < 1e-6 and abs(y - optimal_y) < 1e-6),
            })

    return export_to_csv({"data": rows}, output_path, metadata)


def export_saturation_curves_csv(
    channels: List[str],
    budgets: np.ndarray,
    responses: Dict[str, np.ndarray],
    ci_lower: Dict[str, np.ndarray],
    ci_upper: Dict[str, np.ndarray],
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Export saturation curves to CSV"""
    data = {"budget": budgets}
    for ch in channels:
        data[f"{ch}_response"] = responses[ch]
        data[f"{ch}_ci_lower"] = ci_lower[ch]
        data[f"{ch}_ci_upper"] = ci_upper[ch]

    return export_to_csv(data, output_path, metadata)


def export_marginal_roi_csv(
    channels: List[str],
    marginal_roi: List[float],
    ci_lower: List[float],
    ci_upper: List[float],
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Export marginal ROI to CSV"""
    data = {
        "channel": channels,
        "marginal_roi": marginal_roi,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
    }
    return export_to_csv(data, output_path, metadata)


def export_shapley_attribution_csv(
    channels: List[str],
    shapley_values: List[float],
    ci_lower: List[float],
    ci_upper: List[float],
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Export Shapley attribution to CSV"""
    data = {
        "channel": channels,
        "shapley_value_pct": shapley_values,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
    }
    return export_to_csv(data, output_path, metadata)


def export_ltv_distribution_csv(
    ltv_values: np.ndarray,
    kde_x: np.ndarray,
    kde_y: np.ndarray,
    percentiles: Dict[str, float],
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Export LTV distribution to CSV"""
    # Export raw LTV values and KDE
    data = {
        "ltv_raw": ltv_values,
    }

    # Add KDE (pad with NaN if different length)
    max_len = len(ltv_values)
    kde_padded_x = np.pad(kde_x, (0, max_len - len(kde_x)), constant_values=np.nan) if len(kde_x) < max_len else kde_x[:max_len]
    kde_padded_y = np.pad(kde_y, (0, max_len - len(kde_y)), constant_values=np.nan) if len(kde_y) < max_len else kde_y[:max_len]

    data["kde_x"] = kde_padded_x
    data["kde_y"] = kde_padded_y

    # Add percentiles as metadata
    if metadata is None:
        metadata = {}
    metadata.update({f"percentile_{k}": str(v) for k, v in percentiles.items()})

    return export_to_csv(data, output_path, metadata)


def export_survival_curve_csv(
    time: np.ndarray,
    survival_prob: np.ndarray,
    ci_lower: np.ndarray,
    ci_upper: np.ndarray,
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Export survival curve to CSV"""
    data = {
        "time_days": time,
        "survival_probability": survival_prob,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper,
    }
    return export_to_csv(data, output_path, metadata)


def export_kpi_dashboard_csv(
    kpis: List[str],
    time_series: Dict[str, np.ndarray],
    ci_lower: Dict[str, np.ndarray],
    ci_upper: Dict[str, np.ndarray],
    time_points: np.ndarray,
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Export KPI dashboard data to CSV"""
    data = {"time": time_points}
    for kpi in kpis:
        data[f"{kpi}_value"] = time_series[kpi]
        data[f"{kpi}_ci_lower"] = ci_lower[kpi]
        data[f"{kpi}_ci_upper"] = ci_upper[kpi]

    return export_to_csv(data, output_path, metadata)


def export_recommendations_csv(
    recommendations: List[str],
    impacts: List[str],
    priorities: List[str],
    confidence_scores: List[float],
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """Export AI recommendations to CSV"""
    data = {
        "priority": priorities,
        "recommendation": recommendations,
        "estimated_impact": impacts,
        "confidence_pct": confidence_scores,
    }
    return export_to_csv(data, output_path, metadata)


def export_generic_csv(
    data_dict: Dict[str, Any],
    output_path: Path,
    metadata: Optional[Dict[str, str]] = None,
) -> str:
    """
    Generic CSV export for any chart data

    Args:
        data_dict: Dictionary of column_name -> values
        output_path: Path to save CSV
        metadata: Optional metadata

    Returns:
        Path to saved CSV file
    """
    return export_to_csv(data_dict, output_path, metadata)
