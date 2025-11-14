"""
Objective Comparison Enhanced - 可視化③ Specification
Implements 6 missing essential elements for "月額100万円の説得力"

Reference: /home/hirokionodera/CQO/可視化③.pdf

6 Missing Essential Elements:
1. Objective Function Display (J(θ) formula)
2. Delta with 95% CI (bootstrap/delta method)
3. Scenario Management (save/compare/restore)
4. Consistent Units ($, %, count)
5. Tornado Diagram (sensitivity analysis)
6. Execution Metadata (run_id, seed, timestamp, estimator)
"""
from __future__ import annotations
from typing import Dict, List, Optional, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid
import json
from pathlib import Path


@dataclass
class ObjectiveFunction:
    """
    Objective Function Definition

    J(θ) = V_Y · E[Y|policy(θ)] - C_T · E[T|policy(θ)]

    Subject to:
    - Budget ≤ Cap
    - Coverage ∈ [0, 1]
    """
    name: str
    formula_tex: str
    constraints_tex: str
    value_per_y: float  # V_Y
    cost_per_treated: float  # C_T

    @classmethod
    def default(cls) -> "ObjectiveFunction":
        """Create default objective function"""
        return cls(
            name="Expected Net Value",
            formula_tex=r"\max_\theta J(\theta)=V_Y\,\mathbb{E}[Y|\text{policy}(\theta)]-C_T\,\mathbb{E}[T|\text{policy}(\theta)]",
            constraints_tex=r"\text{s.t. Budget}\le \text{Cap},\ \text{Coverage}\in[0,1]",
            value_per_y=1000.0,  # 1 unit = ¥1000
            cost_per_treated=500.0  # ¥500 per treatment
        )

    def compute(self, expected_y: float, expected_t: float) -> float:
        """Compute objective value J(θ)"""
        return self.value_per_y * expected_y - self.cost_per_treated * expected_t


@dataclass
class DeltaWithCI:
    """
    Delta (Δ) with 95% Confidence Interval

    Δ = J(S1) - J(S0)

    Computed using bootstrap or delta method
    """
    delta: float
    ci_lower: float
    ci_upper: float
    method: str  # "bootstrap" or "delta_method"
    n_bootstrap: int = 1000
    alpha: float = 0.05

    @property
    def is_significant(self) -> bool:
        """Check if CI does not cross zero"""
        return (self.ci_lower > 0) or (self.ci_upper < 0)

    @property
    def badge(self) -> str:
        """Return badge color based on significance"""
        if not self.is_significant:
            return "yellow"  # Not significant
        elif self.delta > 0:
            return "green"  # Positive and significant
        else:
            return "red"  # Negative and significant

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "is_significant": self.is_significant,
            "badge": self.badge
        }


def compute_delta_with_ci(
    sim_fn: callable,
    params: Dict[str, Any],
    n_boot: int = 1000,
    alpha: float = 0.05,
    rng: Optional[np.random.Generator] = None
) -> DeltaWithCI:
    """
    Compute Δ with 95% CI using bootstrap

    Args:
        sim_fn: Simulation function (params, bootstrap=True, rng=rng) -> (s0, s1)
        params: Parameter dict
        n_boot: Number of bootstrap iterations
        alpha: Significance level (default: 0.05 for 95% CI)
        rng: Random number generator

    Returns:
        DeltaWithCI object
    """
    if rng is None:
        rng = np.random.default_rng()

    deltas = []

    for _ in range(n_boot):
        s0, s1 = sim_fn(params, bootstrap=True, rng=rng)
        delta_i = s1.get("J", 0) - s0.get("J", 0)
        deltas.append(delta_i)

    deltas = np.array(deltas)
    delta_mean = np.mean(deltas)
    ci_lower = np.quantile(deltas, alpha / 2)
    ci_upper = np.quantile(deltas, 1 - alpha / 2)

    return DeltaWithCI(
        delta=float(delta_mean),
        ci_lower=float(ci_lower),
        ci_upper=float(ci_upper),
        method="bootstrap",
        n_bootstrap=n_boot,
        alpha=alpha
    )


@dataclass
class ScenarioRun:
    """
    Scenario Run Record for Comparison

    Stores complete execution history for reproducibility
    """
    run_id: str
    dataset_id: str
    scenario_id: str
    params: Dict[str, Any]
    s0_results: Dict[str, Any]
    s1_results: Dict[str, Any]
    delta_with_ci: DeltaWithCI
    metadata: "ExecutionMetadata"
    tag: Optional[str] = None  # "Baseline", "Canary", etc.
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat() + "Z"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_id": self.run_id,
            "dataset_id": self.dataset_id,
            "scenario_id": self.scenario_id,
            "params": self.params,
            "s0_results": self.s0_results,
            "s1_results": self.s1_results,
            "delta_with_ci": self.delta_with_ci.to_dict(),
            "metadata": self.metadata.to_dict(),
            "tag": self.tag,
            "created_at": self.created_at
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ScenarioRun":
        return cls(
            run_id=data["run_id"],
            dataset_id=data["dataset_id"],
            scenario_id=data["scenario_id"],
            params=data["params"],
            s0_results=data["s0_results"],
            s1_results=data["s1_results"],
            delta_with_ci=DeltaWithCI(**data["delta_with_ci"]),
            metadata=ExecutionMetadata.from_dict(data["metadata"]),
            tag=data.get("tag"),
            created_at=data["created_at"]
        )


@dataclass
class ExecutionMetadata:
    """
    Execution Metadata (監査証跡)

    Required for audit trail and reproducibility
    """
    run_id: str
    seed: int
    estimator_set: str  # "ipw", "dr", "dm", etc.
    cv_config: Dict[str, Any]  # Cross-validation settings
    created_at: str
    engine_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionMetadata":
        return cls(**data)

    @classmethod
    def generate(
        cls,
        seed: Optional[int] = None,
        estimator_set: str = "dr",
        cv_folds: int = 5
    ) -> "ExecutionMetadata":
        """Generate new execution metadata"""
        if seed is None:
            seed = np.random.randint(0, 2**31 - 1)

        return cls(
            run_id=str(uuid.uuid4()),
            seed=seed,
            estimator_set=estimator_set,
            cv_config={"n_folds": cv_folds, "shuffle": True},
            created_at=datetime.utcnow().isoformat() + "Z"
        )


class TornadoDiagram:
    """
    Tornado Diagram (Sensitivity Analysis)

    One-At-A-Time (OAT) parameter sweep: ±10% variation
    Shows which parameters have the most impact on Δ
    """

    def __init__(self, base_params: Dict[str, Any], sim_fn: callable):
        self.base_params = base_params
        self.sim_fn = sim_fn

    def compute(self, param_names: List[str], variation_pct: float = 0.1) -> pd.DataFrame:
        """
        Compute tornado diagram data

        Args:
            param_names: List of parameter names to vary
            variation_pct: Variation percentage (default: 0.1 for ±10%)

        Returns:
            DataFrame with columns: [param, low_value, high_value, low_delta, high_delta, range]
        """
        results = []

        # Baseline delta
        s0_base, s1_base = self.sim_fn(self.base_params, bootstrap=False)
        delta_base = s1_base.get("J", 0) - s0_base.get("J", 0)

        for param_name in param_names:
            if param_name not in self.base_params:
                continue

            base_value = self.base_params[param_name]

            # Low variation (-10%)
            params_low = self.base_params.copy()
            params_low[param_name] = base_value * (1 - variation_pct)

            s0_low, s1_low = self.sim_fn(params_low, bootstrap=False)
            delta_low = s1_low.get("J", 0) - s0_low.get("J", 0)

            # High variation (+10%)
            params_high = self.base_params.copy()
            params_high[param_name] = base_value * (1 + variation_pct)

            s0_high, s1_high = self.sim_fn(params_high, bootstrap=False)
            delta_high = s1_high.get("J", 0) - s0_high.get("J", 0)

            # Compute range (impact)
            impact_range = abs(delta_high - delta_low)

            results.append({
                "param": param_name,
                "base_value": base_value,
                "low_value": base_value * (1 - variation_pct),
                "high_value": base_value * (1 + variation_pct),
                "low_delta": delta_low,
                "high_delta": delta_high,
                "range": impact_range,
                "direction": "positive" if delta_high > delta_low else "negative"
            })

        df = pd.DataFrame(results)
        df = df.sort_values("range", ascending=False)

        return df

    def generate_plot_data(self, param_names: List[str]) -> Dict[str, Any]:
        """Generate plot data for frontend tornado visualization"""
        df = self.compute(param_names)

        return {
            "params": df["param"].tolist(),
            "low_deltas": df["low_delta"].tolist(),
            "high_deltas": df["high_delta"].tolist(),
            "ranges": df["range"].tolist(),
            "base_values": df["base_value"].tolist()
        }


class ScenarioManager:
    """
    Scenario Management (保存・比較・復元)

    Provides scenario save/load/compare functionality
    """

    def __init__(self, storage_path: Path):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def save_run(self, run: ScenarioRun) -> Path:
        """Save scenario run to storage"""
        run_file = self.storage_path / f"{run.run_id}.json"

        with open(run_file, "w") as f:
            json.dump(run.to_dict(), f, indent=2)

        return run_file

    def load_run(self, run_id: str) -> Optional[ScenarioRun]:
        """Load scenario run from storage"""
        run_file = self.storage_path / f"{run_id}.json"

        if not run_file.exists():
            return None

        with open(run_file, "r") as f:
            data = json.load(f)

        return ScenarioRun.from_dict(data)

    def list_runs(self, dataset_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all saved runs (optionally filtered by dataset)"""
        runs = []

        for run_file in self.storage_path.glob("*.json"):
            with open(run_file, "r") as f:
                data = json.load(f)

            if dataset_id is None or data.get("dataset_id") == dataset_id:
                runs.append({
                    "run_id": data["run_id"],
                    "dataset_id": data["dataset_id"],
                    "scenario_id": data["scenario_id"],
                    "tag": data.get("tag"),
                    "delta": data["delta_with_ci"]["delta"],
                    "ci_lower": data["delta_with_ci"]["ci_lower"],
                    "ci_upper": data["delta_with_ci"]["ci_upper"],
                    "created_at": data["created_at"]
                })

        # Sort by creation time (newest first)
        runs.sort(key=lambda x: x["created_at"], reverse=True)

        return runs

    def compare_runs(self, run_ids: List[str]) -> pd.DataFrame:
        """Compare multiple scenario runs"""
        rows = []

        for run_id in run_ids:
            run = self.load_run(run_id)
            if run is None:
                continue

            rows.append({
                "run_id": run.run_id,
                "tag": run.tag or "-",
                "S0": run.s0_results.get("J", 0),
                "S1": run.s1_results.get("J", 0),
                "Δ": run.delta_with_ci.delta,
                "CI_lower": run.delta_with_ci.ci_lower,
                "CI_upper": run.delta_with_ci.ci_upper,
                "significant": run.delta_with_ci.is_significant,
                "created_at": run.created_at
            })

        return pd.DataFrame(rows)

    def tag_run(self, run_id: str, tag: str) -> bool:
        """Tag a run (e.g., "Baseline", "Canary")"""
        run = self.load_run(run_id)
        if run is None:
            return False

        run.tag = tag
        self.save_run(run)

        return True


# ==================== Unit Formatting Utilities ====================

class UnitFormatter:
    """Consistent unit formatting ($, %, count)"""

    @staticmethod
    def format_currency(value: float, currency: str = "¥") -> str:
        """Format as currency: ¥1,234,567"""
        return f"{currency}{value:,.0f}"

    @staticmethod
    def format_percentage(value: float, decimals: int = 1) -> str:
        """Format as percentage: 12.3%"""
        return f"{value:.{decimals}f}%"

    @staticmethod
    def format_count(value: float) -> str:
        """Format as count: 1,234 件"""
        return f"{value:,.0f} 件"

    @staticmethod
    def format_unit(value: float, unit: str) -> str:
        """Format with custom unit"""
        if unit == "$" or unit == "¥":
            return UnitFormatter.format_currency(value, currency=unit)
        elif unit == "%":
            return UnitFormatter.format_percentage(value)
        elif unit == "count" or unit == "件":
            return UnitFormatter.format_count(value)
        else:
            return f"{value:.2f} {unit}"
