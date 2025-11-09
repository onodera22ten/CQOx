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
from backend.engine.counterfactual_automation import CounterfactualAutomation, automate_counterfactual_comparison
from backend.reporting.narrative_generator import generate_executive_summary

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
    Simulate counterfactual scenario using automated comparison

    Features:
    - Automatic S0/S1 estimation
    - All visualization panels generated
    - Money-View applied
    - Quality Gates evaluated
    """
    try:
        # Load dataset
        df = load_dataset(req.dataset_id)

        # Create scenario spec
        spec = create_scenario_spec_from_request(req)

        # Load column mapping (simplified - should come from dataset metadata)
        mapping = {
            "treatment": "treatment",
            "outcome": "outcome",
            "unit_id": "unit_id" if "unit_id" in df.columns else None,
            "lat": "lat" if "lat" in df.columns else None,
            "lon": "lon" if "lon" in df.columns else None,
        }

        # Run automated counterfactual comparison
        result = automate_counterfactual_comparison(
            df=df,
            mapping=mapping,
            scenario_spec=spec,
            estimator_method="AIPW",
            ope_method="DR",
            wolfram_path=None  # Use fallback matplotlib if WolframONE not available
        )

        # === NASA/Google++ Addition: Automated Narrative Generation ===
        # Generate executive summary (business-oriented narrative)
        try:
            s0_dict = {
                "s0_ate": result.s0_ate,
                "s0_ate_ci": result.s0_ate_ci,
                "s0_n_total": result.s0_n_total,
                "s0_n_treated": result.s0_n_treated,
                "s0_quality_decision": result.s0_quality_decision,
                "s0_quality_pass_rate": result.s0_quality_pass_rate
            }

            s1_dict = {
                "s1_ate": result.s1_ate,
                "s1_ate_ci": result.s1_ate_ci,
                "s1_n_treated": result.s1_n_treated,
                "s1_coverage": result.s1_coverage,
                "s1_total_cost": result.s1_total_cost,
                "s1_profit": result.s1_profit,
                "s1_profit_ci": result.s1_profit_ci,
                "s1_quality_decision": result.s1_quality_decision,
                "s1_quality_pass_rate": result.s1_quality_pass_rate
            }

            delta_dict = {
                "delta_ate": result.delta_ate,
                "delta_profit": result.delta_profit,
                "delta_profit_ci": result.delta_profit_ci
            }

            business_context = {
                "title": f"シナリオ分析: {spec.label}",
                "date": result.timestamp,
                "scenario_id": spec.id,
                "dataset_id": req.dataset_id
            }

            narrative_markdown = generate_executive_summary(
                s0_result=s0_dict,
                s1_result=s1_dict,
                delta_result=delta_dict,
                business_context=business_context
            )
        except Exception as e:
            print(f"[scenario] Narrative generation failed: {e}")
            narrative_markdown = None

        # Convert to API response format
        response = {
            "run_id": result.run_id,
            "S0": {
                "ATE": result.s0_ate,
                "CI": list(result.s0_ate_ci),
                "treated": result.s0_n_treated
            },
            "S1": {
                "ATE": result.s1_ate,
                "CI": list(result.s1_ate_ci),
                "treated": result.s1_n_treated
            },
            "delta": {
                "ATE": result.delta_ate,
                "money": {
                    "point": result.delta_profit,
                    "CI": list(result.delta_profit_ci) if result.delta_profit_ci else None
                } if result.delta_profit is not None else None
            },
            "quality": {
                "S0_decision": result.s0_quality_decision,
                "S1_decision": result.s1_quality_decision,
                "S0_pass_rate": result.s0_quality_pass_rate,
                "S1_pass_rate": result.s1_quality_pass_rate,
            },
            "fig_refs": result.figures,  # All figure paths
            "metadata": {
                "run_id": result.run_id,
                "timestamp": result.timestamp,
                "runtime_ms": result.runtime_ms
            }
        }

        # Add narrative if generated successfully
        if narrative_markdown:
            response["narrative"] = {
                "format": "markdown",
                "content": narrative_markdown,
                "summary": narrative_markdown[:500] + "..." if len(narrative_markdown) > 500 else narrative_markdown
            }

        return response

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
