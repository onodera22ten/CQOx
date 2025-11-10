"""
Off-Policy Evaluation (OPE) Simulator - NASA/Google Standard

Purpose: Fast counterfactual evaluation using logged data
Features:
- IPS (Inverse Propensity Scoring)
- DR (Doubly Robust)
- SNIPS (Self-Normalized IPS)
- Budget and fairness constraints
- Scenario specification (ScenarioSpec)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass
from typing import Optional, Dict, Any, Literal
from sklearn.linear_model import LogisticRegression, Ridge


@dataclass
class ScenarioSpec:
    """
    Scenario Specification for Counterfactual Simulation

    Based on design document requirements
    """
    id: str
    label: str

    # Intervention
    intervention_type: Literal["policy", "do", "intensity", "spend"] = "policy"
    policy_rule: Optional[str] = None  # e.g., "score > 0.72"
    coverage: Optional[float] = None  # 0-1
    do_value: Optional[int] = None  # For do() interventions

    # Constraints
    budget_cap: Optional[float] = None
    unit_cost_col: str = "cost"
    fairness_group_col: Optional[str] = None
    fairness_max_gap: float = 0.05
    inventory_cap: Optional[int] = None

    # Geography
    geo_include_regions: Optional[list[str]] = None
    geo_multiplier: float = 1.0

    # Network
    network_seed_size: float = 0.01  # Fraction
    network_neighbor_boost: float = 0.0
    network_k: int = 5

    # Time
    time_start: Optional[str] = None
    time_horizon_days: int = 28

    # Value
    value_per_y: Optional[float] = None
    cost_per_treated: Optional[float] = None


class OPESimulator:
    """
    Off-Policy Evaluation Simulator

    Evaluates counterfactual policies using logged data
    """

    def __init__(self, df: pd.DataFrame, propensity_col: str = "log_propensity"):
        """
        Initialize OPE simulator

        Args:
            df: Logged data with outcomes, treatments, and propensities
            propensity_col: Column name for log propensity
        """
        self.df = df
        self.propensity_col = propensity_col

        # Convert log propensity to propensity
        if propensity_col in df.columns:
            self.df["propensity"] = np.exp(df[propensity_col])
        else:
            # Estimate propensity if not provided
            self._estimate_propensity()

    def _estimate_propensity(self):
        """Estimate propensity from covariates"""
        X_cols = [c for c in self.df.columns if c.startswith("X_")]

        if len(X_cols) == 0:
            # Uniform propensity
            self.df["propensity"] = self.df["treatment"].mean()
            return

        X = self.df[X_cols].fillna(0)
        y = self.df["treatment"]

        model = LogisticRegression(max_iter=1000)
        model.fit(X, y)

        self.df["propensity"] = model.predict_proba(X)[:, 1]

    def estimate_ips(
        self,
        policy: np.ndarray,
        outcome_col: str = "y",
        treatment_col: str = "treatment"
    ) -> Dict[str, float]:
        """
        Inverse Propensity Scoring (IPS)

        Args:
            policy: Binary policy (0/1 array)
            outcome_col: Outcome column name
            treatment_col: Treatment column name

        Returns:
            Dictionary with mean, std, and CI
        """
        y = self.df[outcome_col].values
        t = self.df[treatment_col].values
        pi = policy
        e = self.df["propensity"].values

        # IPS weights
        weights = (t * pi / e) + ((1 - t) * (1 - pi) / (1 - e))

        # Clip extreme weights
        weights = np.clip(weights, 0, 100)

        # Weighted outcome
        weighted_y = weights * y

        mean = weighted_y.mean()
        std = weighted_y.std() / np.sqrt(len(y))
        ci_low = mean - 1.96 * std
        ci_high = mean + 1.96 * std

        return {
            "mean": float(mean),
            "std": float(std),
            "ci": [float(ci_low), float(ci_high)],
            "n": len(y)
        }

    def estimate_snips(
        self,
        policy: np.ndarray,
        outcome_col: str = "y",
        treatment_col: str = "treatment"
    ) -> Dict[str, float]:
        """
        Self-Normalized Inverse Propensity Scoring (SNIPS)

        More stable than IPS, especially with extreme propensities

        Args:
            policy: Binary policy
            outcome_col: Outcome column name
            treatment_col: Treatment column name

        Returns:
            Dictionary with mean, std, and CI
        """
        y = self.df[outcome_col].values
        t = self.df[treatment_col].values
        pi = policy
        e = self.df["propensity"].values

        # IPS weights
        weights = (t * pi / e) + ((1 - t) * (1 - pi) / (1 - e))
        weights = np.clip(weights, 0, 100)

        # Self-normalize
        weights = weights / weights.sum() * len(weights)

        # Weighted outcome
        weighted_y = weights * y

        mean = weighted_y.mean()
        std = weighted_y.std() / np.sqrt(len(y))
        ci_low = mean - 1.96 * std
        ci_high = mean + 1.96 * std

        return {
            "mean": float(mean),
            "std": float(std),
            "ci": [float(ci_low), float(ci_high)],
            "n": len(y)
        }

    def estimate_dr(
        self,
        policy: np.ndarray,
        outcome_col: str = "y",
        treatment_col: str = "treatment"
    ) -> Dict[str, float]:
        """
        Doubly Robust (DR) estimation

        Combines outcome regression with propensity weighting

        Args:
            policy: Binary policy
            outcome_col: Outcome column name
            treatment_col: Treatment column name

        Returns:
            Dictionary with mean, std, and CI
        """
        y = self.df[outcome_col].values
        t = self.df[treatment_col].values
        pi = policy
        e = self.df["propensity"].values

        # Estimate outcome models
        X_cols = [c for c in self.df.columns if c.startswith("X_")]

        if len(X_cols) > 0:
            X = self.df[X_cols].fillna(0).values

            # Fit E[Y|X,T=1]
            model_1 = Ridge(alpha=1.0)
            model_1.fit(X[t == 1], y[t == 1])
            mu_1 = model_1.predict(X)

            # Fit E[Y|X,T=0]
            model_0 = Ridge(alpha=1.0)
            model_0.fit(X[t == 0], y[t == 0])
            mu_0 = model_0.predict(X)
        else:
            # No covariates - use simple means
            mu_1 = np.full(len(y), y[t == 1].mean())
            mu_0 = np.full(len(y), y[t == 0].mean())

        # DR estimator
        dr_values = (
            pi * (t * (y - mu_1) / e + mu_1) +
            (1 - pi) * ((1 - t) * (y - mu_0) / (1 - e) + mu_0)
        )

        mean = dr_values.mean()
        std = dr_values.std() / np.sqrt(len(y))
        ci_low = mean - 1.96 * std
        ci_high = mean + 1.96 * std

        return {
            "mean": float(mean),
            "std": float(std),
            "ci": [float(ci_low), float(ci_high)],
            "n": len(y)
        }

    def apply_scenario(
        self,
        spec: ScenarioSpec,
        score_col: Optional[str] = None
    ) -> np.ndarray:
        """
        Apply scenario specification to generate policy

        Args:
            spec: Scenario specification
            score_col: Column with uplift/CATE scores (for policy rules)

        Returns:
            Binary policy array
        """
        n = len(self.df)
        policy = np.zeros(n, dtype=int)

        # Intervention type
        if spec.intervention_type == "do":
            # do(T=1) or do(T=0)
            policy[:] = spec.do_value or 1

        elif spec.intervention_type == "policy":
            # Policy rule (e.g., "score > 0.72")
            if spec.policy_rule and score_col:
                scores = self.df[score_col].values

                # Parse rule (simplified)
                if ">" in spec.policy_rule:
                    threshold = float(spec.policy_rule.split(">")[1].strip())
                    policy = (scores > threshold).astype(int)
                elif "<" in spec.policy_rule:
                    threshold = float(spec.policy_rule.split("<")[1].strip())
                    policy = (scores < threshold).astype(int)

            # Coverage constraint
            if spec.coverage is not None:
                n_treat = int(n * spec.coverage)
                if score_col:
                    # Select top-k by score
                    top_indices = np.argsort(self.df[score_col].values)[-n_treat:]
                else:
                    # Random selection
                    top_indices = np.random.choice(n, n_treat, replace=False)

                policy[:] = 0
                policy[top_indices] = 1

        # Budget constraint
        if spec.budget_cap is not None and spec.unit_cost_col in self.df.columns:
            costs = self.df[spec.unit_cost_col].values
            cumulative_cost = 0

            # Greedy allocation by score
            if score_col:
                sorted_indices = np.argsort(self.df[score_col].values)[::-1]
            else:
                sorted_indices = np.arange(n)

            budget_policy = np.zeros(n, dtype=int)
            for idx in sorted_indices:
                if cumulative_cost + costs[idx] <= spec.budget_cap:
                    budget_policy[idx] = 1
                    cumulative_cost += costs[idx]

            policy = np.minimum(policy, budget_policy)

        # Geographic filter
        if spec.geo_include_regions and "region_id" in self.df.columns:
            geo_mask = self.df["region_id"].isin(spec.geo_include_regions)
            policy = policy * geo_mask.values.astype(int)

        return policy

    def simulate_scenario(
        self,
        spec: ScenarioSpec,
        method: Literal["ips", "snips", "dr"] = "dr",
        score_col: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Simulate scenario and estimate value

        Args:
            spec: Scenario specification
            method: Estimation method
            score_col: Score column for policy rules

        Returns:
            Dictionary with estimation results
        """
        # Generate policy from scenario
        policy = self.apply_scenario(spec, score_col)

        # Estimate value
        if method == "ips":
            estimate = self.estimate_ips(policy)
        elif method == "snips":
            estimate = self.estimate_snips(policy)
        elif method == "dr":
            estimate = self.estimate_dr(policy)
        else:
            raise ValueError(f"Unknown method: {method}")

        # Calculate treated count
        n_treated = policy.sum()

        # Calculate cost
        if spec.unit_cost_col in self.df.columns:
            total_cost = (policy * self.df[spec.unit_cost_col].values).sum()
        elif spec.cost_per_treated:
            total_cost = n_treated * spec.cost_per_treated
        else:
            total_cost = 0.0

        # Calculate profit
        if spec.value_per_y:
            delta_y = estimate["mean"]
            profit = delta_y * spec.value_per_y - total_cost
            profit_ci = [
                estimate["ci"][0] * spec.value_per_y - total_cost,
                estimate["ci"][1] * spec.value_per_y - total_cost
            ]
        else:
            profit = None
            profit_ci = None

        # Check fairness constraint
        fairness_violation = None
        if spec.fairness_group_col and spec.fairness_group_col in self.df.columns:
            groups = self.df[spec.fairness_group_col].unique()
            group_rates = {}
            for g in groups:
                mask = self.df[spec.fairness_group_col] == g
                group_rates[str(g)] = policy[mask].mean()

            max_gap = max(group_rates.values()) - min(group_rates.values())
            if max_gap > spec.fairness_max_gap:
                fairness_violation = {
                    "max_gap": float(max_gap),
                    "threshold": spec.fairness_max_gap,
                    "group_rates": group_rates
                }

        return {
            "scenario_id": spec.id,
            "label": spec.label,
            "method": method,
            "estimate": estimate,
            "n_treated": int(n_treated),
            "coverage": float(n_treated / len(self.df)),
            "total_cost": float(total_cost),
            "profit": float(profit) if profit is not None else None,
            "profit_ci": [float(x) for x in profit_ci] if profit_ci else None,
            "fairness_violation": fairness_violation,
            "policy_hash": hash(policy.tobytes())
        }


def compare_scenarios(
    df: pd.DataFrame,
    scenarios: list[ScenarioSpec],
    baseline_spec: Optional[ScenarioSpec] = None,
    method: str = "dr",
    score_col: Optional[str] = None
) -> pd.DataFrame:
    """
    Compare multiple scenarios

    Args:
        df: Logged data
        scenarios: List of scenario specifications
        baseline_spec: Baseline scenario (S0)
        method: OPE method
        score_col: Score column

    Returns:
        DataFrame with comparison results
    """
    simulator = OPESimulator(df)

    results = []

    # Evaluate baseline
    if baseline_spec:
        baseline_result = simulator.simulate_scenario(baseline_spec, method, score_col)
        baseline_mean = baseline_result["estimate"]["mean"]
        baseline_profit = baseline_result["profit"]
    else:
        baseline_mean = 0.0
        baseline_profit = 0.0

    # Evaluate scenarios
    for spec in scenarios:
        result = simulator.simulate_scenario(spec, method, score_col)

        # Calculate deltas
        delta_ate = result["estimate"]["mean"] - baseline_mean
        delta_profit = (result["profit"] or 0) - baseline_profit if baseline_profit is not None else None

        results.append({
            "scenario_id": spec.id,
            "label": spec.label,
            "ATE": result["estimate"]["mean"],
            "ATE_CI_low": result["estimate"]["ci"][0],
            "ATE_CI_high": result["estimate"]["ci"][1],
            "delta_ATE": delta_ate,
            "n_treated": result["n_treated"],
            "coverage": result["coverage"],
            "total_cost": result["total_cost"],
            "profit": result["profit"],
            "delta_profit": delta_profit,
            "fairness_ok": result["fairness_violation"] is None,
        })

    return pd.DataFrame(results)
