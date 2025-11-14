"""
Money-View Overlay - NASA/Google Standard

Purpose: Convert all metrics to monetary values for decision-making
Features:
- ΔProfit calculation with CI propagation
- Money-View overlay for all visualizations
- Unit conversion and validation
- Small total (期間合算) calculation
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Dict, Any, Literal


@dataclass
class MoneyParams:
    """Money-View parameters"""
    value_per_y: Optional[float] = None  # Value per outcome unit (¥/y)
    cost_per_unit: Optional[float] = None  # Cost per treatment unit
    value_per_sale: Optional[float] = None  # Gross margin per sale (MMM)
    r_per_period: Optional[float] = None  # Revenue per period (Survival)
    horizon_days: int = 28  # Time horizon


class MoneyView:
    """
    Money-View Calculator

    Converts causal estimates to monetary values
    """

    def __init__(self, params: MoneyParams):
        """
        Initialize Money-View calculator

        Args:
            params: Money-View parameters
        """
        self.params = params

    def validate_params(self, metric_type: str) -> bool:
        """
        Validate that required parameters are present

        Args:
            metric_type: Type of metric (ate, mmm, survival, etc.)

        Returns:
            True if params are sufficient
        """
        if metric_type in ["ate", "cate", "event_study"]:
            return self.params.value_per_y is not None

        elif metric_type == "mmm":
            return self.params.value_per_sale is not None

        elif metric_type == "survival":
            return self.params.r_per_period is not None

        return False

    def ate_to_money(
        self,
        ate: float,
        ate_ci: tuple[float, float],
        n_units: int,
        cost: float = 0.0
    ) -> Dict[str, Any]:
        """
        Convert ATE to ΔProfit

        Args:
            ate: Average Treatment Effect
            ate_ci: 95% CI for ATE
            n_units: Number of units
            cost: Total treatment cost

        Returns:
            Dictionary with ΔProfit and CI
        """
        if not self.validate_params("ate"):
            return {
                "delta_profit": None,
                "delta_profit_ci": None,
                "error": "value_per_y not provided"
            }

        value_per_y = self.params.value_per_y

        # ΔProfit = value_per_y * ATE * n_units - cost
        delta_profit = value_per_y * ate * n_units - cost

        # CI propagation (linear transformation)
        delta_profit_ci = (
            value_per_y * ate_ci[0] * n_units - cost,
            value_per_y * ate_ci[1] * n_units - cost
        )

        return {
            "delta_profit": delta_profit,
            "delta_profit_ci": delta_profit_ci,
            "value_per_y": value_per_y,
            "cost": cost,
            "n_units": n_units
        }

    def cate_to_money(
        self,
        cate_df: pd.DataFrame,
        cate_col: str = "cate",
        ci_low_col: str = "ci_low",
        ci_high_col: str = "ci_high",
        n_col: str = "n"
    ) -> pd.DataFrame:
        """
        Convert CATE distribution to money

        Args:
            cate_df: DataFrame with CATE estimates
            cate_col: CATE column name
            ci_low_col: CI lower bound column
            ci_high_col: CI upper bound column
            n_col: Sample size column

        Returns:
            DataFrame with delta_profit columns
        """
        if not self.validate_params("cate"):
            cate_df["delta_profit"] = None
            cate_df["delta_profit_ci_low"] = None
            cate_df["delta_profit_ci_high"] = None
            return cate_df

        value_per_y = self.params.value_per_y
        cost_per_unit = self.params.cost_per_unit or 0.0

        # ΔProfit = value_per_y * CATE - cost_per_unit
        cate_df["delta_profit"] = value_per_y * cate_df[cate_col] - cost_per_unit
        cate_df["delta_profit_ci_low"] = value_per_y * cate_df[ci_low_col] - cost_per_unit
        cate_df["delta_profit_ci_high"] = value_per_y * cate_df[ci_high_col] - cost_per_unit

        return cate_df

    def event_study_to_money(
        self,
        es_df: pd.DataFrame,
        ate_col: str = "ate",
        ci_low_col: str = "ci_low",
        ci_high_col: str = "ci_high",
        n_col: str = "n",
        cost_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert Event Study estimates to cumulative ΔProfit

        Args:
            es_df: Event study DataFrame (rows = time periods)
            ate_col: ATE column name
            ci_low_col: CI lower bound column
            ci_high_col: CI upper bound column
            n_col: Sample size column
            cost_col: Cost column (per period)

        Returns:
            Dictionary with cumulative ΔProfit
        """
        if not self.validate_params("event_study"):
            return {"delta_profit_cumulative": None, "error": "value_per_y not provided"}

        value_per_y = self.params.value_per_y

        # Cumulative profit calculation
        es_df = es_df.copy()

        costs = es_df[cost_col].values if cost_col and cost_col in es_df.columns else np.zeros(len(es_df))

        es_df["delta_profit_period"] = value_per_y * es_df[ate_col] * es_df[n_col] - costs
        es_df["delta_profit_period_ci_low"] = value_per_y * es_df[ci_low_col] * es_df[n_col] - costs
        es_df["delta_profit_period_ci_high"] = value_per_y * es_df[ci_high_col] * es_df[n_col] - costs

        cumulative_profit = es_df["delta_profit_period"].sum()
        cumulative_ci_low = es_df["delta_profit_period_ci_low"].sum()
        cumulative_ci_high = es_df["delta_profit_period_ci_high"].sum()

        return {
            "delta_profit_cumulative": cumulative_profit,
            "delta_profit_cumulative_ci": (cumulative_ci_low, cumulative_ci_high),
            "es_with_money": es_df
        }

    def survival_to_money(
        self,
        rmst_diff: float,
        rmst_diff_ci: tuple[float, float],
        n_units: int
    ) -> Dict[str, Any]:
        """
        Convert RMST difference to ΔProfit for survival/churn analysis

        Args:
            rmst_diff: Restricted Mean Survival Time difference (days)
            rmst_diff_ci: 95% CI for RMST diff
            n_units: Number of units

        Returns:
            Dictionary with ΔProfit
        """
        if not self.validate_params("survival"):
            return {"delta_profit": None, "error": "r_per_period not provided"}

        r_per_period = self.params.r_per_period

        # Convert RMST (days) to revenue
        # ΔProfit = (RMST_diff / horizon) * r_per_period * n_units
        horizon_days = self.params.horizon_days
        delta_profit = (rmst_diff / horizon_days) * r_per_period * n_units

        delta_profit_ci = (
            (rmst_diff_ci[0] / horizon_days) * r_per_period * n_units,
            (rmst_diff_ci[1] / horizon_days) * r_per_period * n_units
        )

        return {
            "delta_profit": delta_profit,
            "delta_profit_ci": delta_profit_ci,
            "r_per_period": r_per_period,
            "horizon_days": horizon_days
        }

    def mmm_to_money(
        self,
        delta_sales: float,
        delta_sales_ci: tuple[float, float],
        delta_spend: float
    ) -> Dict[str, Any]:
        """
        Convert MMM estimates to ΔProfit

        Args:
            delta_sales: Change in sales (units)
            delta_sales_ci: 95% CI for delta_sales
            delta_spend: Change in media spend (¥)

        Returns:
            Dictionary with ΔProfit
        """
        if not self.validate_params("mmm"):
            return {"delta_profit": None, "error": "value_per_sale not provided"}

        value_per_sale = self.params.value_per_sale

        # ΔProfit = value_per_sale * ΔSales - ΔSpend
        delta_profit = value_per_sale * delta_sales - delta_spend

        delta_profit_ci = (
            value_per_sale * delta_sales_ci[0] - delta_spend,
            value_per_sale * delta_sales_ci[1] - delta_spend
        )

        return {
            "delta_profit": delta_profit,
            "delta_profit_ci": delta_profit_ci,
            "value_per_sale": value_per_sale,
            "delta_spend": delta_spend,
            "marginal_roi": delta_profit / delta_spend if delta_spend != 0 else None
        }

    def format_yen(self, value: float) -> str:
        """
        Format value as Japanese Yen

        Args:
            value: Numeric value

        Returns:
            Formatted string (e.g., "¥1,234,567")
        """
        return f"¥{value:,.0f}"

    def format_money_metric(
        self,
        delta_y: float,
        delta_y_ci: tuple[float, float],
        metric_type: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generic money formatting for any metric type

        Args:
            delta_y: Change in outcome
            delta_y_ci: 95% CI for delta_y
            metric_type: Type of metric
            **kwargs: Additional parameters (n_units, cost, etc.)

        Returns:
            Dictionary with formatted money values
        """
        if metric_type == "ate":
            money = self.ate_to_money(
                ate=delta_y,
                ate_ci=delta_y_ci,
                n_units=kwargs.get("n_units", 1),
                cost=kwargs.get("cost", 0.0)
            )

        elif metric_type == "survival":
            money = self.survival_to_money(
                rmst_diff=delta_y,
                rmst_diff_ci=delta_y_ci,
                n_units=kwargs.get("n_units", 1)
            )

        elif metric_type == "mmm":
            money = self.mmm_to_money(
                delta_sales=delta_y,
                delta_sales_ci=delta_y_ci,
                delta_spend=kwargs.get("delta_spend", 0.0)
            )

        else:
            return {"error": f"Unknown metric type: {metric_type}"}

        if money.get("delta_profit") is not None:
            money["delta_profit_formatted"] = self.format_yen(money["delta_profit"])

            if money.get("delta_profit_ci"):
                money["delta_profit_ci_formatted"] = [
                    self.format_yen(money["delta_profit_ci"][0]),
                    self.format_yen(money["delta_profit_ci"][1])
                ]

        return money


def create_money_overlay(
    fig_data: Dict[str, Any],
    params: MoneyParams,
    metric_type: str
) -> Dict[str, Any]:
    """
    Add money overlay to figure data

    Args:
        fig_data: Figure data dictionary
        params: Money-View parameters
        metric_type: Type of metric

    Returns:
        Figure data with money overlay
    """
    money_view = MoneyView(params)

    # Add right axis data
    if "delta_y" in fig_data and "delta_y_ci" in fig_data:
        money = money_view.format_money_metric(
            delta_y=fig_data["delta_y"],
            delta_y_ci=fig_data["delta_y_ci"],
            metric_type=metric_type,
            **fig_data
        )

        fig_data["money_overlay"] = money

    # Add tooltip data
    if "tooltips" in fig_data:
        for tooltip in fig_data["tooltips"]:
            if "delta_y" in tooltip:
                money = money_view.format_money_metric(
                    delta_y=tooltip["delta_y"],
                    delta_y_ci=tooltip.get("delta_y_ci", (tooltip["delta_y"], tooltip["delta_y"])),
                    metric_type=metric_type,
                    **tooltip
                )
                tooltip["money"] = money

    return fig_data


# Alias for backward compatibility
MoneyViewConverter = MoneyView
