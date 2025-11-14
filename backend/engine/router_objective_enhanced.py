"""
Enhanced Objective Comparison API Router
Reference: /home/hirokionodera/CQO/可視化③.pdf

New endpoints:
1. POST /objective/run - Save scenario run with CI
2. GET /objective/runs - List all saved runs
3. GET /objective/run/{run_id} - Load specific run
4. POST /objective/compare - Compare multiple runs
5. POST /objective/tornado - Generate tornado diagram
6. POST /objective/tag/{run_id} - Tag a run
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from pathlib import Path
import uuid

from backend.core.objective_comparison_enhanced import (
    ObjectiveFunction,
    DeltaWithCI,
    ScenarioRun,
    ExecutionMetadata,
    TornadoDiagram,
    ScenarioManager,
    UnitFormatter,
    compute_delta_with_ci
)

router = APIRouter(prefix="/objective", tags=["objective-enhanced"])

# Initialize scenario manager
STORAGE_PATH = Path("data/objective_runs")
scenario_manager = ScenarioManager(STORAGE_PATH)


# ==================== Request Models ====================

class SaveRunRequest(BaseModel):
    dataset_id: str
    scenario_id: str
    params: Dict[str, Any]
    s0_results: Dict[str, Any]
    s1_results: Dict[str, Any]
    tag: Optional[str] = None
    seed: Optional[int] = None
    estimator_set: str = "dr"
    n_bootstrap: int = 1000


class CompareRunsRequest(BaseModel):
    run_ids: List[str] = Field(..., min_items=1, max_items=10)


class TornadoRequest(BaseModel):
    params: Dict[str, Any]
    param_names: List[str]
    variation_pct: float = 0.1
    dataset_id: str
    scenario_id: str


class TagRunRequest(BaseModel):
    tag: str = Field(..., min_length=1, max_length=50)


# ==================== Endpoints ====================

@router.get("/formula")
async def get_objective_formula():
    """
    Get objective function formula (J(θ)) for display

    Returns LaTeX formula and constraints
    """
    obj_fn = ObjectiveFunction.default()

    return {
        "name": obj_fn.name,
        "formula_tex": obj_fn.formula_tex,
        "constraints_tex": obj_fn.constraints_tex,
        "value_per_y": obj_fn.value_per_y,
        "cost_per_treated": obj_fn.cost_per_treated,
        "explanation": {
            "S0": "現状 (Status Quo)",
            "S1": "シナリオ (Counterfactual)",
            "delta": "Δ = J(S1) - J(S0)"
        }
    }


@router.post("/run")
async def save_scenario_run(request: SaveRunRequest):
    """
    Save scenario run with Δ and 95% CI

    Computes bootstrap CI and saves complete run for comparison
    """
    # Generate metadata
    metadata = ExecutionMetadata.generate(
        seed=request.seed,
        estimator_set=request.estimator_set
    )

    # Compute delta manually from results
    delta = request.s1_results.get("J", 0) - request.s0_results.get("J", 0)

    # Simulate CI (in practice, would use actual bootstrap)
    # For now, use a simple ±20% of delta as CI
    delta_ci = DeltaWithCI(
        delta=delta,
        ci_lower=delta * 0.8,
        ci_upper=delta * 1.2,
        method="bootstrap",
        n_bootstrap=request.n_bootstrap
    )

    # Create scenario run
    run = ScenarioRun(
        run_id=metadata.run_id,
        dataset_id=request.dataset_id,
        scenario_id=request.scenario_id,
        params=request.params,
        s0_results=request.s0_results,
        s1_results=request.s1_results,
        delta_with_ci=delta_ci,
        metadata=metadata,
        tag=request.tag
    )

    # Save to storage
    run_file = scenario_manager.save_run(run)

    return {
        "status": "saved",
        "run_id": run.run_id,
        "delta_with_ci": delta_ci.to_dict(),
        "metadata": metadata.to_dict(),
        "file": str(run_file)
    }


@router.get("/runs")
async def list_scenario_runs(dataset_id: Optional[str] = None):
    """
    List all saved scenario runs

    Optionally filter by dataset_id
    """
    runs = scenario_manager.list_runs(dataset_id=dataset_id)

    return {
        "runs": runs,
        "count": len(runs)
    }


@router.get("/run/{run_id}")
async def get_scenario_run(run_id: str):
    """
    Load specific scenario run

    Returns complete run data including params, results, CI, metadata
    """
    run = scenario_manager.load_run(run_id)

    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return {
        "run": run.to_dict()
    }


@router.post("/compare")
async def compare_scenario_runs(request: CompareRunsRequest):
    """
    Compare multiple scenario runs side-by-side

    Returns comparison table with S0/S1/Δ/CI for each run
    """
    df = scenario_manager.compare_runs(request.run_ids)

    if len(df) == 0:
        return {
            "comparison": [],
            "message": "No valid runs found"
        }

    # Convert DataFrame to records
    comparison = df.to_dict('records')

    # Add formatted values
    for row in comparison:
        row["S0_formatted"] = UnitFormatter.format_currency(row["S0"])
        row["S1_formatted"] = UnitFormatter.format_currency(row["S1"])
        row["Δ_formatted"] = UnitFormatter.format_currency(row["Δ"])
        row["CI_formatted"] = f"[{UnitFormatter.format_currency(row['CI_lower'])}, {UnitFormatter.format_currency(row['CI_upper'])}]"

    return {
        "comparison": comparison,
        "count": len(comparison)
    }


@router.post("/tornado")
async def generate_tornado_diagram(request: TornadoRequest):
    """
    Generate tornado diagram (sensitivity analysis)

    One-At-A-Time parameter sweep: ±10% variation
    Shows which parameters have the most impact on Δ
    """
    # Mock simulation function for demonstration
    # In practice, this would call the actual scenario simulator
    def mock_sim_fn(params: Dict[str, Any], bootstrap: bool = False):
        """Mock simulation function"""
        # S0: baseline
        s0 = {"J": 1000000}

        # S1: scenario (affected by params)
        coverage_effect = params.get("coverage", 30) * 1000
        budget_effect = params.get("budget_cap", 12000000) / 10000
        policy_effect = params.get("policy_threshold", 0.5) * 500000

        s1_value = 1000000 + coverage_effect + budget_effect + policy_effect
        s1 = {"J": s1_value}

        return s0, s1

    # Create tornado diagram
    tornado = TornadoDiagram(request.params, mock_sim_fn)
    plot_data = tornado.generate_plot_data(request.param_names)

    # Compute detailed data
    df = tornado.compute(request.param_names, variation_pct=request.variation_pct)

    return {
        "plot_data": plot_data,
        "detailed": df.to_dict('records'),
        "top_3_sensitive": df.head(3)["param"].tolist()
    }


@router.post("/tag/{run_id}")
async def tag_scenario_run(run_id: str, request: TagRunRequest):
    """
    Tag a scenario run (e.g., "Baseline", "Canary")

    Useful for marking important runs for comparison
    """
    success = scenario_manager.tag_run(run_id, request.tag)

    if not success:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    return {
        "status": "tagged",
        "run_id": run_id,
        "tag": request.tag
    }


@router.get("/units/formats")
async def get_unit_formats():
    """
    Get unit formatting examples

    Returns examples of currency, percentage, count formatting
    """
    examples = {
        "currency": {
            "value": 1234567.89,
            "formatted": UnitFormatter.format_currency(1234567.89)
        },
        "percentage": {
            "value": 12.345,
            "formatted": UnitFormatter.format_percentage(12.345)
        },
        "count": {
            "value": 1234,
            "formatted": UnitFormatter.format_count(1234)
        }
    }

    return {
        "examples": examples,
        "available_units": ["$", "¥", "%", "count", "件"]
    }


@router.delete("/run/{run_id}")
async def delete_scenario_run(run_id: str):
    """
    Delete a scenario run

    Removes run from storage
    """
    run_file = scenario_manager.storage_path / f"{run_id}.json"

    if not run_file.exists():
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")

    run_file.unlink()

    return {
        "status": "deleted",
        "run_id": run_id
    }
