"""
Counterfactual Automation - NASA/Google Standard

Purpose: Orchestrate S0/S1 comparison across all visualization panels
Features:
- Automatic estimator execution for S0 and S1
- Automatic figure generation for all panels
- Parameter-controlled comparison
- Money-View integration
- Quality gates for both scenarios
"""

from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
from dataclasses import dataclass, asdict

from backend.engine.estimators_integrated import IntegratedEstimator
from backend.engine.wolfram_integrated import IntegratedWolframVisualizer
from backend.engine.ope_simulator import OPESimulator, ScenarioSpec
from backend.engine.money_view import MoneyViewConverter
from backend.engine.quality_gates_enhanced import EnhancedQualityGates


@dataclass
class ComparisonResult:
    """Complete S0/S1 comparison result"""
    scenario_id: str
    scenario_label: str

    # S0 (Observation)
    s0_ate: float
    s0_ate_ci: tuple
    s0_n_treated: int
    s0_n_total: int

    # S1 (Counterfactual)
    s1_ate: float
    s1_ate_ci: tuple
    s1_n_treated: int
    s1_coverage: float
    s1_total_cost: float

    # Delta (S1 - S0)
    delta_ate: float

    # Quality
    s0_quality_decision: str  # GO/CANARY/HOLD
    s1_quality_decision: str
    s0_quality_pass_rate: float
    s1_quality_pass_rate: float

    # Optional fields with defaults
    s1_profit: Optional[float] = None
    s1_profit_ci: Optional[tuple] = None
    delta_profit: Optional[float] = None
    delta_profit_ci: Optional[tuple] = None

    # Figures (panel_name -> {S0: path, S1: path})
    figures: Dict[str, Dict[str, str]] = None

    # Metadata
    run_id: str = ""
    timestamp: str = ""
    runtime_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API response"""
        return {
            "scenario_id": self.scenario_id,
            "scenario_label": self.scenario_label,
            "S0": {
                "ATE": self.s0_ate,
                "ATE_CI": self.s0_ate_ci,
                "n_treated": self.s0_n_treated,
                "n_total": self.s0_n_total
            },
            "S1": {
                "ATE": self.s1_ate,
                "ATE_CI": self.s1_ate_ci,
                "n_treated": self.s1_n_treated,
                "coverage": self.s1_coverage,
                "total_cost": self.s1_total_cost,
                "profit": self.s1_profit,
                "profit_CI": self.s1_profit_ci
            },
            "delta": {
                "ATE": self.delta_ate,
                "profit": self.delta_profit,
                "profit_CI": self.delta_profit_ci
            },
            "quality_gates": {
                "S0": {
                    "decision": self.s0_quality_decision,
                    "pass_rate": self.s0_quality_pass_rate
                },
                "S1": {
                    "decision": self.s1_quality_decision,
                    "pass_rate": self.s1_quality_pass_rate
                }
            },
            "figures": self.figures or {},
            "run_metadata": {
                "run_id": self.run_id,
                "timestamp": self.timestamp,
                "runtime_ms": self.runtime_ms
            }
        }


class CounterfactualAutomation:
    """
    反実仮想自動化エンジン

    - ScenarioSpecからS0/S1を自動計算
    - 全パネルの可視化を自動生成
    - Money-View自動適用
    - Quality Gates自動評価
    """

    def __init__(
        self,
        dataset_id: str,
        wolfram_path: Optional[str] = None,
        output_dir: str = "reports/figures"
    ):
        self.dataset_id = dataset_id
        self.wolfram_path = wolfram_path
        self.money_converter = MoneyViewConverter()
        self.quality_evaluator = EnhancedQualityGates()

        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def run_full_comparison(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str],
        scenario_spec: ScenarioSpec,
        estimator_method: str = "AIPW",
        ope_method: str = "DR"
    ) -> ComparisonResult:
        """
        Complete S0/S1 comparison with all visualizations

        Args:
            df: Input data
            mapping: Column mapping (treatment, outcome, covariates, etc.)
            scenario_spec: Counterfactual scenario specification
            estimator_method: Estimator to use (AIPW, DML, etc.)
            ope_method: OPE method (IPS, SNIPS, DR)

        Returns:
            ComparisonResult with all metrics and figure paths
        """
        import time
        import uuid
        from datetime import datetime

        start_time = time.time()
        run_id = str(uuid.uuid4())[:8]

        # Initialize objects that need data
        estimator = IntegratedEstimator(self.dataset_id)
        visualizer = IntegratedWolframVisualizer(self.wolfram_path)
        ope_simulator = OPESimulator(df)

        # Step 1: Run S0 (Observation) estimation
        s0_result = self._run_s0_estimation(df, mapping, estimator_method, estimator)

        # Step 2: Run S1 (Counterfactual) simulation
        s1_result = self._run_s1_simulation(
            df, mapping, scenario_spec, ope_method, ope_simulator
        )

        # Step 3: Calculate delta (S1 - S0)
        delta = self._calculate_delta(s0_result, s1_result, scenario_spec)

        # Step 4: Generate all visualization panels
        figures = self._generate_all_figures(
            df, mapping, scenario_spec, s0_result, s1_result
        )

        # Step 5: Assemble result
        elapsed_ms = (time.time() - start_time) * 1000

        result = ComparisonResult(
            scenario_id=scenario_spec.id,
            scenario_label=scenario_spec.label,
            s0_ate=s0_result["ate"],
            s0_ate_ci=s0_result["ci"],
            s0_n_treated=s0_result["n_treated"],
            s0_n_total=s0_result["n_total"],
            s1_ate=s1_result["ate"],
            s1_ate_ci=s1_result["ci"],
            s1_n_treated=s1_result["n_treated"],
            s1_coverage=s1_result["coverage"],
            s1_total_cost=s1_result["total_cost"],
            s1_profit=s1_result.get("profit"),
            s1_profit_ci=s1_result.get("profit_ci"),
            delta_ate=delta["ate"],
            delta_profit=delta.get("profit"),
            delta_profit_ci=delta.get("profit_ci"),
            s0_quality_decision=s0_result["quality"]["decision"],
            s1_quality_decision=s1_result["quality"]["decision"],
            s0_quality_pass_rate=s0_result["quality"]["pass_rate"],
            s1_quality_pass_rate=s1_result["quality"]["pass_rate"],
            figures=figures,
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            runtime_ms=elapsed_ms
        )

        return result

    def _run_s0_estimation(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str],
        method: str,
        estimator
    ) -> Dict[str, Any]:
        """Run S0 (observed) estimation"""
        # Use integrated estimator
        result = estimator.run_estimator(df, mapping, method)

        # Evaluate quality gates
        quality = self.quality_evaluator.evaluate_all(
            df=df,
            estimate=result["ate"],
            ci=result["ci"],
            se=result["se"],
            gamma_critical=2.0,
            estimator_type=method
        )

        return {
            "ate": result["ate"],
            "ci": result["ci"],
            "se": result["se"],
            "n_treated": int(df[mapping["treatment"]].sum()),
            "n_total": len(df),
            "quality": {
                "decision": quality.decision,
                "pass_rate": quality.pass_rate,
                "gates": [asdict(g) for g in quality.gates]
            }
        }

    def _run_s1_simulation(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str],
        scenario_spec: ScenarioSpec,
        ope_method: str,
        ope_simulator
    ) -> Dict[str, Any]:
        """Run S1 (counterfactual) simulation"""
        # Use OPE simulator
        sim_result = ope_simulator.simulate_scenario(
            df=df,
            mapping=mapping,
            scenario=scenario_spec,
            method=ope_method
        )

        # Calculate cost
        n_treated_s1 = sim_result["n_treated"]
        unit_cost = scenario_spec.cost_per_treated or 100.0
        total_cost = n_treated_s1 * unit_cost

        # Apply Money-View if value_per_y is specified
        profit = None
        profit_ci = None
        if scenario_spec.value_per_y:
            money_result = self.money_converter.ate_to_money(
                ate=sim_result["ate"],
                ate_ci=sim_result["ci"],
                n_units=n_treated_s1,
                cost=total_cost,
                value_per_y=scenario_spec.value_per_y
            )
            profit = money_result["delta_profit"]
            profit_ci = money_result["delta_profit_ci"]

        # Evaluate quality gates
        quality = self.quality_evaluator.evaluate_all(
            df=df,
            estimate=sim_result["ate"],
            ci=sim_result["ci"],
            se=sim_result["se"],
            gamma_critical=2.0,
            estimator_type=ope_method
        )

        return {
            "ate": sim_result["ate"],
            "ci": sim_result["ci"],
            "se": sim_result["se"],
            "n_treated": n_treated_s1,
            "coverage": sim_result["coverage"],
            "total_cost": total_cost,
            "profit": profit,
            "profit_ci": profit_ci,
            "quality": {
                "decision": quality.decision,
                "pass_rate": quality.pass_rate,
                "gates": [asdict(g) for g in quality.gates]
            }
        }

    def _calculate_delta(
        self,
        s0_result: Dict[str, Any],
        s1_result: Dict[str, Any],
        scenario_spec: ScenarioSpec
    ) -> Dict[str, Any]:
        """Calculate delta (S1 - S0)"""
        delta_ate = s1_result["ate"] - s0_result["ate"]

        delta_profit = None
        delta_profit_ci = None
        if s1_result["profit"] is not None:
            # Delta profit = S1 profit - S0 baseline
            # (Assuming S0 profit = 0 as baseline)
            delta_profit = s1_result["profit"]
            delta_profit_ci = s1_result["profit_ci"]

        return {
            "ate": delta_ate,
            "profit": delta_profit,
            "profit_ci": delta_profit_ci
        }

    def _generate_all_figures(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str],
        scenario_spec: ScenarioSpec,
        s0_result: Dict[str, Any],
        s1_result: Dict[str, Any]
    ) -> Dict[str, Dict[str, str]]:
        """
        Generate all visualization panels for S0/S1 comparison

        Returns:
            {
                "ate_density": {"S0": "path/to/ate_density__S0.html", "S1": "..."},
                "cate_distribution": {...},
                ...
            }
        """
        # Define all panels to generate
        panels = [
            "ate_density",           # ATE distribution (2D histogram)
            "cate_distribution",     # CATE distribution (2D violin)
            "parallel_trends",       # Pre-trend check (animation)
            "event_study",          # Event study (animation)
            "network_exposure",     # Network exposure map (3D)
            "spatial_heatmap",      # Geographic heatmap (2D)
            "policy_frontier",      # Policy frontier (3D surface)
            "cas_radar"             # CAS radar chart (2D polar)
        ]

        figures = {}

        for panel_name in panels:
            try:
                # Prepare data for this panel
                data_s0 = self._prepare_panel_data(df, panel_name, s0_result, "S0")
                data_s1 = self._prepare_panel_data(df, panel_name, s1_result, "S1")

                # Generate comparison figures
                panel_figures = self.visualizer.generate_comparison_figures(
                    panel_name=panel_name,
                    data_s0=data_s0,
                    data_s1=data_s1,
                    mapping=mapping,
                    scenario_id=scenario_spec.id
                )

                figures[panel_name] = panel_figures

            except Exception as e:
                print(f"[WARNING] Failed to generate {panel_name}: {e}")
                figures[panel_name] = {}

        return figures

    def _prepare_panel_data(
        self,
        df: pd.DataFrame,
        panel_name: str,
        result: Dict[str, Any],
        scenario: str
    ) -> pd.DataFrame:
        """Prepare data for specific panel visualization"""
        # Base data
        panel_df = df.copy()

        # Add ATE/CATE columns if needed
        if panel_name in ["ate_density", "cate_distribution"]:
            # For simplicity, use constant ATE (in real implementation,
            # would calculate CATE for each unit)
            panel_df["ate"] = result["ate"]
            panel_df["ate_lower"] = result["ci"][0]
            panel_df["ate_upper"] = result["ci"][1]

        # Add scenario label
        panel_df["scenario"] = scenario

        return panel_df


# Convenience function

def automate_counterfactual_comparison(
    df: pd.DataFrame,
    mapping: Dict[str, str],
    scenario_spec: ScenarioSpec,
    dataset_id: str,
    estimator_method: str = "AIPW",
    ope_method: str = "DR",
    wolfram_path: Optional[str] = None
) -> ComparisonResult:
    """
    One-shot function to run complete S0/S1 comparison

    Example:
        >>> scenario = ScenarioSpec(
        ...     id="policy_001",
        ...     label="Increase coverage to 80%",
        ...     intervention_type="policy",
        ...     coverage=0.8,
        ...     value_per_y=1000,
        ...     cost_per_treated=50
        ... )
        >>> result = automate_counterfactual_comparison(
        ...     df=data,
        ...     mapping=col_mapping,
        ...     scenario_spec=scenario,
        ...     dataset_id="my_dataset_id"
        ... )
        >>> print(result.delta_profit)  # Money impact
        >>> print(result.figures["ate_density"]["S0"])  # Figure path
    """
    automation = CounterfactualAutomation(dataset_id=dataset_id, wolfram_path=wolfram_path)
    return automation.run_full_comparison(
        df=df,
        mapping=mapping,
        scenario_spec=scenario_spec,
        estimator_method=estimator_method,
        ope_method=ope_method
    )
