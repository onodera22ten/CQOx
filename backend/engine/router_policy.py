"""
Policy Router - Beyond NASA/Google

Purpose: Optimal policy learning API endpoints
Features:
- /api/policy/optimize - Learn optimal treatment policy
- /api/policy/evaluate - Evaluate policy performance
- /api/policy/compare - Compare multiple policies
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Dict, Any, List

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.optimization.policy_learner import OptimalPolicyLearner, find_optimal_policy


router = APIRouter(prefix="/api/policy", tags=["policy"])

# In-memory cache for loaded datasets
_dataset_cache: Dict[str, pd.DataFrame] = {}


class OptimizeRequest(BaseModel):
    """Request for policy optimization"""
    dataset_id: str

    # Constraints
    budget: Optional[float] = None
    min_coverage: Optional[float] = 0.0
    max_coverage: Optional[float] = 1.0
    value_per_y: Optional[float] = 1000.0
    cost_per_unit: Optional[float] = 100.0

    # Objective
    objective: str = "profit"  # profit, ate, coverage


class EvaluateRequest(BaseModel):
    """Request for policy evaluation"""
    dataset_id: str
    policy_threshold: float  # CATE threshold for treatment


class CompareRequest(BaseModel):
    """Request for policy comparison"""
    dataset_id: str
    policies: List[Dict[str, Any]]  # List of policy specifications


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


@router.post("/optimize")
async def optimize_policy(req: OptimizeRequest):
    """
    Learn optimal treatment policy

    Features:
    - CATE-based optimization
    - Budget & coverage constraints
    - Pareto frontier generation
    - Alternative policies comparison

    Returns:
    - Optimal policy with expected profit, coverage, ATE
    - Alternative policies for comparison
    - Pareto frontier (profit vs coverage trade-off)
    """
    try:
        # Load dataset
        df = load_dataset(req.dataset_id)

        # Load column mapping (simplified)
        mapping = {
            "treatment": "treatment",
            "outcome": "outcome",
            "unit_id": "unit_id" if "unit_id" in df.columns else None,
        }

        # Build constraints
        constraints = {
            "budget": req.budget,
            "min_coverage": req.min_coverage,
            "max_coverage": req.max_coverage,
            "value_per_y": req.value_per_y,
            "cost_per_unit": req.cost_per_unit
        }

        # Learn optimal policy
        result = find_optimal_policy(
            df=df,
            mapping=mapping,
            constraints=constraints,
            objective=req.objective
        )

        # === Beyond NASA/Google: Generate Policy Narrative ===
        try:
            from backend.reporting.narrative_generator import NarrativeGenerator

            narrative_gen = NarrativeGenerator(
                template="policy_recommendation",
                audience="C-level",
                language="ja"
            )

            # Create narrative context
            policy_narrative = _generate_policy_narrative(
                optimal_policy=result.optimal_policy,
                alternatives=result.alternative_policies,
                pareto_frontier=result.pareto_frontier,
                constraints=constraints
            )
        except Exception as e:
            print(f"[policy] Narrative generation failed: {e}")
            policy_narrative = None

        # Prepare response
        response = {
            "optimal_policy": result.optimal_policy.to_dict(),
            "alternative_policies": [p.to_dict() for p in result.alternative_policies],
            "pareto_frontier": result.pareto_frontier,
            "optimization_summary": result.optimization_summary
        }

        # Add narrative if generated
        if policy_narrative:
            response["narrative"] = policy_narrative

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evaluate")
async def evaluate_policy(req: EvaluateRequest):
    """
    Evaluate a specific policy

    Given a CATE threshold, evaluate expected performance
    """
    try:
        # Load dataset
        df = load_dataset(req.dataset_id)

        # Load column mapping
        mapping = {
            "treatment": "treatment",
            "outcome": "outcome",
        }

        # Learn CATE
        learner = OptimalPolicyLearner()
        cate_estimates = learner._estimate_cate(df, mapping)

        # Evaluate policy at threshold
        treated = cate_estimates >= req.policy_threshold
        n_treated = treated.sum()
        coverage = n_treated / len(cate_estimates)

        expected_ate = cate_estimates[treated].mean() if n_treated > 0 else 0

        # Calculate profit (if value/cost provided)
        value_per_y = 1000.0  # Default
        cost_per_unit = 100.0  # Default

        profit_per_unit = cate_estimates * value_per_y - cost_per_unit
        expected_profit = profit_per_unit[treated].sum() if n_treated > 0 else 0

        return {
            "policy_threshold": req.policy_threshold,
            "expected_coverage": float(coverage),
            "n_treated": int(n_treated),
            "expected_ate": float(expected_ate),
            "expected_profit": float(expected_profit),
            "roi": float(expected_profit / (n_treated * cost_per_unit) * 100) if n_treated > 0 else 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/compare")
async def compare_policies(req: CompareRequest):
    """
    Compare multiple policies

    Returns comparison table
    """
    try:
        # Load dataset
        df = load_dataset(req.dataset_id)

        # Load column mapping
        mapping = {
            "treatment": "treatment",
            "outcome": "outcome",
        }

        # Learn CATE
        learner = OptimalPolicyLearner()
        cate_estimates = learner._estimate_cate(df, mapping)

        # Evaluate each policy
        results = []
        for policy_spec in req.policies:
            threshold = policy_spec.get("threshold", 0)
            label = policy_spec.get("label", f"Threshold {threshold}")

            treated = cate_estimates >= threshold
            n_treated = treated.sum()
            coverage = n_treated / len(cate_estimates)

            expected_ate = cate_estimates[treated].mean() if n_treated > 0 else 0

            value_per_y = policy_spec.get("value_per_y", 1000.0)
            cost_per_unit = policy_spec.get("cost_per_unit", 100.0)

            profit_per_unit = cate_estimates * value_per_y - cost_per_unit
            expected_profit = profit_per_unit[treated].sum() if n_treated > 0 else 0

            results.append({
                "label": label,
                "threshold": threshold,
                "coverage": float(coverage),
                "n_treated": int(n_treated),
                "expected_ate": float(expected_ate),
                "expected_profit": float(expected_profit),
                "roi": float(expected_profit / (n_treated * cost_per_unit) * 100) if n_treated > 0 else 0
            })

        # Sort by profit (descending)
        results = sorted(results, key=lambda x: x["expected_profit"], reverse=True)

        return {
            "comparison": results,
            "best_policy": results[0] if results else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check"""
    return {"status": "ok", "service": "policy"}


# Helper functions

def _generate_policy_narrative(
    optimal_policy,
    alternatives: List,
    pareto_frontier: List[Dict],
    constraints: Dict
) -> Dict[str, Any]:
    """Generate policy recommendation narrative"""

    # Create markdown narrative
    narrative = f"""
# 最適ポリシー推奨

## TL;DR

✅ **推奨ルール**: {optimal_policy.condition}

### 期待効果
- **カバレッジ**: {optimal_policy.expected_coverage*100:.1f}%
- **増分利益**: ¥{optimal_policy.expected_profit/1e6:.1f}M
  （90%CI: ¥{optimal_policy.expected_profit_ci[0]/1e6:.1f}M - ¥{optimal_policy.expected_profit_ci[1]/1e6:.1f}M）
- **平均効果**: {optimal_policy.expected_ate:.2f}

### なぜこのルールが最適か

このルールは、制約条件の下で**利益を最大化**します：

1. **高ROI**: CATE（個人レベルの効果）が高い層に集中投資
2. **制約充足**:
   - 予算制約: {constraints.get('budget', '制約なし')}
   - 最小カバレッジ: {constraints.get('min_coverage', 0)*100:.0f}%
   - 最大カバレッジ: {constraints.get('max_coverage', 1)*100:.0f}%

### 代替案との比較

| ポリシー | カバレッジ | 利益 | ROI |
|---------|-----------|------|-----|
| **推奨** | {optimal_policy.expected_coverage*100:.1f}% | ¥{optimal_policy.expected_profit/1e6:.1f}M | - |
"""

    # Add alternatives
    for i, alt in enumerate(alternatives[:3], 1):
        narrative += f"| 代替{i} | {alt.expected_coverage*100:.1f}% | ¥{alt.expected_profit/1e6:.1f}M | - |\n"

    narrative += """

### 実行プラン

1. **Phase 1**: パイロット展開（推奨ルールの上位20%）
2. **Phase 2**: 段階的拡大（上位50%）
3. **Phase 3**: 全面展開（推奨ルール適用）

### リスク

- **効果過小推定**: 実際の効果がCATEより低い場合 → 保守的見積もりで対策
- **実行遅延**: リソース不足 → 早期準備とPM体制強化
"""

    return {
        "format": "markdown",
        "content": narrative,
        "summary": f"推奨: {optimal_policy.condition} | 期待利益: ¥{optimal_policy.expected_profit/1e6:.1f}M"
    }
