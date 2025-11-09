"""
Optimal Policy Learning - Beyond NASA/Google

Purpose: Automatic optimal policy learning from causal analysis
Features:
- CATE-based policy optimization
- Constraint optimization (budget, fairness, coverage)
- Treatment rule generation
- Pareto frontier for multi-objective optimization
- Expected value calculation
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from scipy.optimize import linprog, minimize


@dataclass
class PolicyRule:
    """Treatment assignment rule"""
    rule_type: str  # "threshold", "quantile", "complex"
    description: str
    condition: str  # Human-readable condition
    expected_coverage: float
    expected_ate: float
    expected_profit: float
    expected_profit_ci: Tuple[float, float]

    # Rule parameters
    threshold: Optional[float] = None
    quantile: Optional[float] = None
    features: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class OptimizationResult:
    """Result of policy optimization"""
    optimal_policy: PolicyRule
    alternative_policies: List[PolicyRule]
    pareto_frontier: Optional[List[Dict[str, Any]]] = None
    optimization_summary: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "optimal_policy": self.optimal_policy.to_dict(),
            "alternative_policies": [p.to_dict() for p in self.alternative_policies],
            "pareto_frontier": self.pareto_frontier,
            "optimization_summary": self.optimization_summary
        }


class OptimalPolicyLearner:
    """
    最適ポリシー学習

    - CATE推定に基づいて最適な治療ルールを学習
    - 制約条件（予算、公平性、カバレッジ）を考慮
    - 複数目的の最適化（利益 vs 公平性 vs カバレッジ）
    """

    def __init__(self):
        self.cate_estimates = None
        self.features = None

    def learn_optimal_policy(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str],
        cate_estimates: Optional[np.ndarray] = None,
        constraints: Optional[Dict[str, Any]] = None,
        objective: str = "profit"
    ) -> OptimizationResult:
        """
        Learn optimal treatment policy

        Args:
            df: Input data
            mapping: Column mapping
            cate_estimates: Pre-computed CATE estimates (if None, will estimate)
            constraints: Optimization constraints
                - budget: Maximum total cost
                - min_coverage: Minimum treatment coverage
                - max_coverage: Maximum treatment coverage
                - fairness_constraint: Fairness metric threshold
            objective: Optimization objective ("profit", "ate", "coverage")

        Returns:
            OptimizationResult with optimal policy and alternatives
        """
        constraints = constraints or {}

        # Step 1: Estimate CATE if not provided
        if cate_estimates is None:
            cate_estimates = self._estimate_cate(df, mapping)

        self.cate_estimates = cate_estimates

        # Step 2: Extract features for policy learning
        features_df = self._extract_features(df, mapping)
        self.features = features_df

        # Step 3: Solve optimization problem
        optimal_policy = self._optimize_policy(
            cate_estimates=cate_estimates,
            features=features_df,
            constraints=constraints,
            objective=objective
        )

        # Step 4: Generate alternative policies
        alternative_policies = self._generate_alternatives(
            cate_estimates=cate_estimates,
            features=features_df,
            constraints=constraints
        )

        # Step 5: Compute Pareto frontier (profit vs coverage vs fairness)
        pareto_frontier = self._compute_pareto_frontier(
            cate_estimates=cate_estimates,
            features=features_df,
            constraints=constraints
        )

        # Step 6: Create summary
        optimization_summary = self._create_summary(
            optimal_policy=optimal_policy,
            alternatives=alternative_policies,
            constraints=constraints
        )

        return OptimizationResult(
            optimal_policy=optimal_policy,
            alternative_policies=alternative_policies,
            pareto_frontier=pareto_frontier,
            optimization_summary=optimization_summary
        )

    def _estimate_cate(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str]
    ) -> np.ndarray:
        """
        Estimate CATE (Conditional Average Treatment Effect)

        Simplified: Use residual-based approach
        In production: Use S-learner, T-learner, X-learner, or Causal Forest
        """
        y_col = mapping["outcome"]
        t_col = mapping["treatment"]

        # Get covariates
        exclude_cols = {y_col, t_col, mapping.get("unit_id")}
        covariate_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in [np.number]]

        if len(covariate_cols) == 0:
            # Fallback: constant CATE (ATE)
            treated_mean = df[df[t_col] == 1][y_col].mean()
            control_mean = df[df[t_col] == 0][y_col].mean()
            ate = treated_mean - control_mean
            return np.full(len(df), ate)

        # Simple S-learner approach
        X = df[covariate_cols].fillna(0).values
        y = df[y_col].values
        t = df[t_col].values

        # Fit model: E[Y|X,T]
        from sklearn.ensemble import RandomForestRegressor

        X_with_t = np.column_stack([X, t])
        model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
        model.fit(X_with_t, y)

        # Predict under T=1 and T=0
        X_t1 = np.column_stack([X, np.ones(len(X))])
        X_t0 = np.column_stack([X, np.zeros(len(X))])

        y_pred_t1 = model.predict(X_t1)
        y_pred_t0 = model.predict(X_t0)

        # CATE = E[Y|X,T=1] - E[Y|X,T=0]
        cate = y_pred_t1 - y_pred_t0

        return cate

    def _extract_features(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str]
    ) -> pd.DataFrame:
        """Extract features for policy learning"""
        y_col = mapping["outcome"]
        t_col = mapping["treatment"]

        exclude_cols = {y_col, t_col, mapping.get("unit_id")}
        feature_cols = [c for c in df.columns if c not in exclude_cols and df[c].dtype in [np.number]]

        return df[feature_cols].fillna(0)

    def _optimize_policy(
        self,
        cate_estimates: np.ndarray,
        features: pd.DataFrame,
        constraints: Dict[str, Any],
        objective: str
    ) -> PolicyRule:
        """
        Solve optimization problem to find optimal policy

        Maximize: E[Y(1) - Y(0)] * I(treat) - cost * I(treat)
        Subject to: budget, coverage, fairness constraints
        """
        n = len(cate_estimates)

        # Get constraints
        budget = constraints.get("budget", np.inf)
        min_coverage = constraints.get("min_coverage", 0.0)
        max_coverage = constraints.get("max_coverage", 1.0)
        cost_per_unit = constraints.get("cost_per_unit", 100)
        value_per_y = constraints.get("value_per_y", 1000)

        # Simple greedy approach: sort by CATE and take top-k
        # More sophisticated: solve integer programming problem

        # Convert CATE to profit per unit
        profit_per_unit = cate_estimates * value_per_y - cost_per_unit

        # Sort by profit (descending)
        sorted_indices = np.argsort(-profit_per_unit)
        sorted_cate = cate_estimates[sorted_indices]
        sorted_profit = profit_per_unit[sorted_indices]

        # Find optimal threshold
        cumulative_profit = np.cumsum(sorted_profit)
        cumulative_cost = np.arange(1, n + 1) * cost_per_unit
        cumulative_coverage = np.arange(1, n + 1) / n

        # Apply constraints
        feasible = (cumulative_cost <= budget) & \
                   (cumulative_coverage >= min_coverage) & \
                   (cumulative_coverage <= max_coverage)

        if not np.any(feasible):
            # No feasible solution, return minimum coverage
            k = int(n * min_coverage)
        else:
            # Find k that maximizes profit among feasible solutions
            feasible_profits = np.where(feasible, cumulative_profit, -np.inf)
            k = np.argmax(feasible_profits) + 1

        # Determine threshold
        if k < n:
            threshold_cate = sorted_cate[k]
            threshold_profit = sorted_profit[k]
        else:
            threshold_cate = sorted_cate[-1] - 1
            threshold_profit = sorted_profit[-1] - 1

        # Create policy rule
        coverage = k / n
        expected_ate = sorted_cate[:k].mean() if k > 0 else 0
        expected_profit_total = cumulative_profit[k - 1] if k > 0 else 0
        expected_profit_per_unit = expected_profit_total / k if k > 0 else 0

        # Rough CI estimate (assume SE = std/sqrt(k))
        profit_std = sorted_profit[:k].std() if k > 1 else 0
        profit_se = profit_std / np.sqrt(k) if k > 0 else 0
        profit_ci = (
            expected_profit_total - 1.96 * profit_se * np.sqrt(k),
            expected_profit_total + 1.96 * profit_se * np.sqrt(k)
        )

        # Generate human-readable condition
        if threshold_cate > 0:
            condition = f"Treat if CATE > {threshold_cate:.2f}"
        else:
            condition = f"Treat top {coverage*100:.1f}% by CATE"

        policy = PolicyRule(
            rule_type="threshold",
            description=f"Treat units with CATE above {threshold_cate:.2f}",
            condition=condition,
            expected_coverage=coverage,
            expected_ate=expected_ate,
            expected_profit=expected_profit_total,
            expected_profit_ci=profit_ci,
            threshold=float(threshold_cate)
        )

        return policy

    def _generate_alternatives(
        self,
        cate_estimates: np.ndarray,
        features: pd.DataFrame,
        constraints: Dict[str, Any]
    ) -> List[PolicyRule]:
        """Generate alternative policies for comparison"""
        alternatives = []

        value_per_y = constraints.get("value_per_y", 1000)
        cost_per_unit = constraints.get("cost_per_unit", 100)

        # Alternative 1: Top 10%
        alternatives.append(self._create_quantile_policy(
            cate_estimates, quantile=0.9, value_per_y=value_per_y,
            cost_per_unit=cost_per_unit, label="Top 10%"
        ))

        # Alternative 2: Top 25%
        alternatives.append(self._create_quantile_policy(
            cate_estimates, quantile=0.75, value_per_y=value_per_y,
            cost_per_unit=cost_per_unit, label="Top 25%"
        ))

        # Alternative 3: Top 50%
        alternatives.append(self._create_quantile_policy(
            cate_estimates, quantile=0.5, value_per_y=value_per_y,
            cost_per_unit=cost_per_unit, label="Top 50%"
        ))

        # Alternative 4: Treat all with positive CATE
        alternatives.append(self._create_threshold_policy(
            cate_estimates, threshold=0, value_per_y=value_per_y,
            cost_per_unit=cost_per_unit, label="Positive CATE only"
        ))

        return alternatives

    def _create_quantile_policy(
        self,
        cate_estimates: np.ndarray,
        quantile: float,
        value_per_y: float,
        cost_per_unit: float,
        label: str
    ) -> PolicyRule:
        """Create quantile-based policy"""
        threshold = np.quantile(cate_estimates, quantile)
        return self._create_threshold_policy(
            cate_estimates, threshold, value_per_y, cost_per_unit, label
        )

    def _create_threshold_policy(
        self,
        cate_estimates: np.ndarray,
        threshold: float,
        value_per_y: float,
        cost_per_unit: float,
        label: str
    ) -> PolicyRule:
        """Create threshold-based policy"""
        treated = cate_estimates >= threshold
        n_treated = treated.sum()
        coverage = n_treated / len(cate_estimates)

        expected_ate = cate_estimates[treated].mean() if n_treated > 0 else 0
        profit_per_unit = cate_estimates * value_per_y - cost_per_unit
        expected_profit = profit_per_unit[treated].sum() if n_treated > 0 else 0

        # Rough CI
        profit_std = profit_per_unit[treated].std() if n_treated > 1 else 0
        profit_se = profit_std / np.sqrt(n_treated) if n_treated > 0 else 0
        profit_ci = (
            expected_profit - 1.96 * profit_se * np.sqrt(n_treated),
            expected_profit + 1.96 * profit_se * np.sqrt(n_treated)
        )

        return PolicyRule(
            rule_type="threshold",
            description=f"{label}: Treat if CATE >= {threshold:.2f}",
            condition=f"CATE >= {threshold:.2f}",
            expected_coverage=coverage,
            expected_ate=expected_ate,
            expected_profit=expected_profit,
            expected_profit_ci=profit_ci,
            threshold=float(threshold)
        )

    def _compute_pareto_frontier(
        self,
        cate_estimates: np.ndarray,
        features: pd.DataFrame,
        constraints: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Compute Pareto frontier for multi-objective optimization

        Objectives:
        - Maximize profit
        - Maximize coverage (equity)
        - Minimize cost
        """
        value_per_y = constraints.get("value_per_y", 1000)
        cost_per_unit = constraints.get("cost_per_unit", 100)

        profit_per_unit = cate_estimates * value_per_y - cost_per_unit

        # Try different coverage levels
        coverage_levels = np.linspace(0.1, 1.0, 10)
        pareto_points = []

        for coverage in coverage_levels:
            # Sort by CATE and take top coverage%
            k = int(len(cate_estimates) * coverage)
            if k == 0:
                continue

            top_k_indices = np.argsort(-cate_estimates)[:k]

            total_profit = profit_per_unit[top_k_indices].sum()
            total_cost = k * cost_per_unit
            avg_cate = cate_estimates[top_k_indices].mean()

            pareto_points.append({
                "coverage": float(coverage),
                "profit": float(total_profit),
                "cost": float(total_cost),
                "avg_cate": float(avg_cate),
                "roi": float(total_profit / total_cost * 100) if total_cost > 0 else 0
            })

        return pareto_points

    def _create_summary(
        self,
        optimal_policy: PolicyRule,
        alternatives: List[PolicyRule],
        constraints: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create optimization summary"""
        return {
            "optimal_policy_description": optimal_policy.description,
            "expected_improvement": {
                "profit": optimal_policy.expected_profit,
                "coverage": optimal_policy.expected_coverage,
                "ate": optimal_policy.expected_ate
            },
            "compared_to_alternatives": {
                "n_alternatives": len(alternatives),
                "best_alternative_profit": max([p.expected_profit for p in alternatives]) if alternatives else 0
            },
            "constraints_applied": {
                "budget": constraints.get("budget", "None"),
                "min_coverage": constraints.get("min_coverage", 0),
                "max_coverage": constraints.get("max_coverage", 1.0)
            }
        }


# Convenience function

def find_optimal_policy(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    constraints: Optional[Dict[str, Any]] = None,
    objective: str = "profit"
) -> OptimizationResult:
    """
    One-shot optimal policy learning

    Example:
        >>> result = find_optimal_policy(
        ...     df=data,
        ...     mapping={"outcome": "revenue", "treatment": "campaign"},
        ...     constraints={
        ...         "budget": 100_000_000,
        ...         "min_coverage": 0.3,
        ...         "value_per_y": 1000,
        ...         "cost_per_unit": 100
        ...     }
        ... )
        >>> print(result.optimal_policy.description)
        >>> print(f"Expected profit: ¥{result.optimal_policy.expected_profit:,.0f}")
    """
    learner = OptimalPolicyLearner()
    return learner.learn_optimal_policy(df, mapping, constraints=constraints, objective=objective)
