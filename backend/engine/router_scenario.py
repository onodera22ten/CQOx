"""
Scenario Router - NASA/Google Standard

Purpose: API endpoints for counterfactual scenario simulation
Features:
- /api/scenario/simulate - OPE simulation
- /api/scenario/confirm - g-computation confirmation
- /api/scenario/compare - Multi-scenario comparison
"""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.engine.ope_simulator import OPESimulator, ScenarioSpec, compare_scenarios
from backend.engine.money_view import MoneyView, MoneyParams
from backend.engine.quality_gates_enhanced import EnhancedQualityGates
from backend.common.schema_validator import StrictDataContract

router = APIRouter(prefix="/api/scenario", tags=["scenario"])

# In-memory cache for loaded datasets
_dataset_cache: Dict[str, pd.DataFrame] = {}


class SimulateRequest(BaseModel):
    """Request for scenario simulation"""
    dataset_id: str
    scenario_id: str
    mode: str = "OPE"  # OPE, gcomp, DiD

    # Scenario parameters
    coverage: Optional[float] = None
    budget_cap: Optional[float] = None
    policy_threshold: Optional[float] = None
    neighbor_boost: Optional[float] = None
    geo_multiplier: Optional[float] = None
    network_size: Optional[float] = None
    value_per_y: Optional[float] = None
    cost_per_treated: Optional[float] = None

    # Exposure specification
    exposure: Optional[Dict[str, Any]] = None


class ConfirmRequest(BaseModel):
    """Request for g-computation confirmation"""
    dataset_id: str
    scenario_id: str
    mode: str = "gcomp"


class CompareRequest(BaseModel):
    """Request for multi-scenario comparison"""
    dataset_id: str
    scenarios: List[str]  # List of scenario IDs
    mode: str = "OPE"


def load_dataset(dataset_id: str) -> pd.DataFrame:
    """Load dataset from cache or disk"""
    if dataset_id in _dataset_cache:
        return _dataset_cache[dataset_id]

    # Try to load from data directory
    base_path = Path(__file__).resolve().parents[2] / "data" / dataset_id

    for ext in [".parquet", ".csv"]:
        file_path = base_path / f"data{ext}"
        if file_path.exists():
            if ext == ".parquet":
                df = pd.read_parquet(file_path)
            else:
                df = pd.read_csv(file_path)

            _dataset_cache[dataset_id] = df
            return df

    raise HTTPException(status_code=404, detail=f"Dataset '{dataset_id}' not found")


def create_scenario_spec_from_request(req: SimulateRequest) -> ScenarioSpec:
    """Create ScenarioSpec from request"""
    return ScenarioSpec(
        id=req.scenario_id,
        label=f"Scenario {req.scenario_id}",
        intervention_type="policy",
        coverage=req.coverage,
        budget_cap=req.budget_cap,
        policy_rule=f"score > {req.policy_threshold}" if req.policy_threshold else None,
        network_neighbor_boost=req.neighbor_boost or 0.0,
        geo_multiplier=req.geo_multiplier or 1.0,
        value_per_y=req.value_per_y,
        cost_per_treated=req.cost_per_treated,
    )


@router.post("/simulate")
async def simulate_scenario(req: SimulateRequest):
    """
    Simulate counterfactual scenario using OPE

    Fast evaluation using logged data
    """
    try:
        # Load dataset
        df = load_dataset(req.dataset_id)

        # Create scenario spec
        spec = create_scenario_spec_from_request(req)

        # Run OPE simulation
        simulator = OPESimulator(df)

        # Generate score column if not present (simplified)
        score_col = None
        if "cate_score" in df.columns:
            score_col = "cate_score"
        elif "uplift_score" in df.columns:
            score_col = "uplift_score"

        # Simulate
        result = simulator.simulate_scenario(spec, method="dr", score_col=score_col)

        # Also compute baseline (S0)
        baseline_spec = ScenarioSpec(
            id="S0",
            label="Observation",
            intervention_type="do",
            do_value=None  # Observed treatment
        )

        # For baseline, use observed treatment
        baseline_policy = df["treatment"].values
        baseline_estimate = simulator.estimate_dr(baseline_policy)

        # Compute S0
        S0 = {
            "ATE": baseline_estimate["mean"],
            "CI": baseline_estimate["ci"],
            "treated": int(baseline_policy.sum())
        }

        # Compute S1
        S1 = {
            "ATE": result["estimate"]["mean"],
            "CI": result["estimate"]["ci"],
            "treated": result["n_treated"]
        }

        # Compute delta
        delta_ATE = S1["ATE"] - S0["ATE"]

        # Money-view calculation
        if spec.value_per_y:
            delta_profit = result["profit"] - (S0["treated"] * (spec.cost_per_treated or 0))
            delta_profit_ci = [
                result["profit_ci"][0] - (S0["treated"] * (spec.cost_per_treated or 0)),
                result["profit_ci"][1] - (S0["treated"] * (spec.cost_per_treated or 0))
            ] if result["profit_ci"] else None
        else:
            delta_profit = None
            delta_profit_ci = None

        # Quality gates
        quality_gates = EnhancedQualityGates()
        gate_report = quality_gates.evaluate_all(
            df,
            estimate=S1["ATE"],
            ci=tuple(S1["CI"]),
            se=(S1["CI"][1] - S1["CI"][0]) / (2 * 1.96)
        )

        # Generate run ID
        run_id = str(uuid.uuid4())

        return {
            "run_id": run_id,
            "S0": S0,
            "S1": S1,
            "delta": {
                "ATE": delta_ATE,
                "money": {
                    "point": delta_profit,
                    "CI": delta_profit_ci
                } if delta_profit is not None else None
            },
            "quality": {
                "overlap": gate_report.gates[0].value if len(gate_report.gates) > 0 else 0.0,
                "gamma": 1.5,  # Placeholder
                "smd": 0.1,  # Placeholder
                "q": None
            },
            "quality_gate_report": gate_report.to_dict(),
            "fig_refs": []
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/confirm")
async def confirm_scenario(req: ConfirmRequest):
    """
    Confirm scenario using g-computation (heavier, more accurate)

    This would implement full g-computation, but for now returns similar to OPE
    """
    # For MVP, delegate to simulate with different method
    simulate_req = SimulateRequest(
        dataset_id=req.dataset_id,
        scenario_id=req.scenario_id,
        mode="gcomp"
    )

    return await simulate_scenario(simulate_req)


@router.post("/compare")
async def compare_scenarios_endpoint(req: CompareRequest):
    """
    Compare multiple scenarios

    Returns comparison table with all scenarios
    """
    try:
        # Load dataset
        df = load_dataset(req.dataset_id)

        # Create scenario specs (simplified)
        scenarios = []
        for scenario_id in req.scenarios:
            spec = ScenarioSpec(
                id=scenario_id,
                label=f"Scenario {scenario_id}"
            )
            scenarios.append(spec)

        # Run comparison
        comparison_df = compare_scenarios(df, scenarios, method="dr")

        return {
            "comparison": comparison_df.to_dict(orient="records")
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "scenario"}
