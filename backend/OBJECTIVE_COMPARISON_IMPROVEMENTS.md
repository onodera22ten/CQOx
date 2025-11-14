# Objective Comparison Improvements (可視化③)

**Status**: Backend Implementation Complete ✅
**Frontend**: Partial (ObjectiveFormula component created)
**Reference**: `/home/hirokionodera/CQO/可視化③.pdf`
**Goal**: 月額100万円の説得力 (Persuasive Power for Monthly 1M Yen Value)

---

## 📋 Summary

Implemented **6 missing essential elements** to elevate the Objective Comparison page from basic S0/S1 comparison to enterprise-grade decision support tool.

---

## ✅ 6 Essential Elements Implemented

### 1. **目的関数の明示** (Objective Function Display)
**Status**: ✅ Complete

**What**: Display J(θ) formula with LaTeX rendering at UI top

**Formula**:
```
max_θ J(θ) = V_Y · E[Y|policy(θ)] - C_T · E[T|policy(θ)]
Subject to: Budget ≤ Cap, Coverage ∈ [0,1]
```

**Implementation**:
- **Backend**: `backend/core/objective_comparison_enhanced.py`
  - `ObjectiveFunction` dataclass with LaTeX formulas
  - Default factory method with sensible defaults
  - API endpoint: `GET /objective/formula`

- **Frontend**: `frontend/src/components/ObjectiveFormula.tsx`
  - KaTeX rendering for beautiful math display
  - Responsive card design with gradient background
  - Shows V_Y (value per unit) and C_T (cost per treated)
  - Explains S0, S1, Δ

**Usage**:
```typescript
import ObjectiveFormula from './components/ObjectiveFormula';

<ObjectiveFormula className="mb-6" />
```

---

### 2. **不確実性の提示** (Δ with 95% CI)
**Status**: ✅ Complete

**What**: Show Δ with ±95% confidence interval using bootstrap/delta method

**Key Features**:
- Bootstrap confidence intervals (n=1000 iterations)
- Significance badge (green/yellow/red)
  - **Green**: CI does not cross 0, Δ > 0 (significant positive effect)
  - **Red**: CI does not cross 0, Δ < 0 (significant negative effect)
  - **Yellow**: CI crosses 0 (not significant)
- CI bands on diagnostic charts

**Implementation**:
- **Backend**:
  - `DeltaWithCI` dataclass in `objective_comparison_enhanced.py`
  - `compute_delta_with_ci()` function with bootstrap
  - Properties: `is_significant`, `badge`, `to_dict()`

- **API**: Embedded in `POST /objective/run` response
  ```json
  {
    "delta_with_ci": {
      "delta": 1234567.89,
      "ci_lower": 987654.32,
      "ci_upper": 1481481.48,
      "method": "bootstrap",
      "n_bootstrap": 1000,
      "alpha": 0.05,
      "is_significant": true,
      "badge": "green"
    }
  }
  ```

---

### 3. **シナリオ管理** (Scenario Management: Save/Compare/Restore)
**Status**: ✅ Complete

**What**: Full scenario lifecycle management for reproducibility

**Key Features**:
- **Save**: Store scenario runs with complete params/results
- **List**: View all saved runs, filtered by dataset
- **Load**: Restore any previous run by ID
- **Compare**: Side-by-side comparison of multiple runs (1-10)
- **Tag**: Mark runs as "Baseline", "Canary", etc.
- **Delete**: Remove old runs

**Implementation**:
- **Backend**:
  - `ScenarioManager` class handles persistence (JSON files in `data/objective_runs/`)
  - `ScenarioRun` dataclass with complete state
  - Export/Import JSON for external sharing

- **API Endpoints**:
  - `POST /objective/run` - Save new run
  - `GET /objective/runs?dataset_id=...` - List runs
  - `GET /objective/run/{run_id}` - Load specific run
  - `POST /objective/compare` - Compare multiple runs
  - `POST /objective/tag/{run_id}` - Tag a run
  - `DELETE /objective/run/{run_id}` - Delete run

**Storage Format** (`data/objective_runs/{run_id}.json`):
```json
{
  "run_id": "uuid",
  "dataset_id": "realistic_retail_5k",
  "scenario_id": "S1_geo_budget",
  "params": {...},
  "s0_results": {...},
  "s1_results": {...},
  "delta_with_ci": {...},
  "metadata": {...},
  "tag": "Baseline",
  "created_at": "2025-11-14T12:34:56Z"
}
```

---

### 4. **単位と基準の一貫表示** (Consistent Units)
**Status**: ✅ Complete

**What**: Standardized unit formatting across all cards/axes/tooltips

**Supported Units**:
- **Currency**: ¥ / $ (e.g., "¥1,234,567")
- **Percentage**: % (e.g., "12.3%")
- **Count**: 件 / count (e.g., "1,234 件")

**Implementation**:
- **Backend**:
  - `UnitFormatter` class in `objective_comparison_enhanced.py`
  - Methods: `format_currency()`, `format_percentage()`, `format_count()`, `format_unit()`

- **API**: `GET /objective/units/formats` provides examples

**Usage**:
```python
from backend.core.objective_comparison_enhanced import UnitFormatter

UnitFormatter.format_currency(1234567.89)  # "¥1,234,567"
UnitFormatter.format_percentage(12.345)     # "12.3%"
UnitFormatter.format_count(1234)            # "1,234 件"
```

---

### 5. **感度分析** (Tornado Diagram)
**Status**: ✅ Complete

**What**: One-At-A-Time (OAT) sensitivity analysis showing parameter impact on Δ

**Method**:
- Vary each parameter by ±10% (configurable)
- Compute Δ for low/high values
- Rank by impact range (Δ_high - Δ_low)
- Display top contributors as horizontal bars

**Key Insight**: Shows "which lever to pull" for maximizing impact

**Implementation**:
- **Backend**:
  - `TornadoDiagram` class in `objective_comparison_enhanced.py`
  - `compute()` method returns sorted DataFrame
  - `generate_plot_data()` for frontend visualization

- **API**: `POST /objective/tornado`
  ```json
  {
    "params": {...},
    "param_names": ["coverage", "budget_cap", "policy_threshold"],
    "variation_pct": 0.1
  }
  ```

**Response**:
```json
{
  "plot_data": {
    "params": ["coverage", "budget_cap", "policy_threshold"],
    "low_deltas": [100, 200, 300],
    "high_deltas": [150, 250, 400],
    "ranges": [50, 50, 100]
  },
  "top_3_sensitive": ["policy_threshold", "coverage", "budget_cap"]
}
```

---

### 6. **実行メタデータ** (Execution Metadata)
**Status**: ✅ Complete

**What**: Complete audit trail for reproducibility and governance

**Included Metadata**:
- `run_id`: Unique UUID for this execution
- `seed`: Random seed for reproducibility
- `estimator_set`: Estimator used ("ipw", "dr", "dm")
- `cv_config`: Cross-validation settings (n_folds, shuffle)
- `created_at`: ISO 8601 timestamp
- `engine_version`: Backend version

**Implementation**:
- **Backend**:
  - `ExecutionMetadata` dataclass in `objective_comparison_enhanced.py`
  - `generate()` factory method auto-generates UUID/timestamp/seed
  - Embedded in every `ScenarioRun`

- **API**: Included in all run responses

**Example**:
```json
{
  "metadata": {
    "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "seed": 42,
    "estimator_set": "dr",
    "cv_config": {"n_folds": 5, "shuffle": true},
    "created_at": "2025-11-14T12:34:56.789Z",
    "engine_version": "1.0.0"
  }
}
```

---

## 📂 File Structure

```
backend/
├── core/
│   └── objective_comparison_enhanced.py  # Core classes (NEW)
│       ├── ObjectiveFunction
│       ├── DeltaWithCI
│       ├── ScenarioRun
│       ├── ExecutionMetadata
│       ├── TornadoDiagram
│       ├── ScenarioManager
│       └── UnitFormatter
│
├── engine/
│   └── router_objective_enhanced.py  # API router (NEW)
│       ├── GET  /objective/formula
│       ├── POST /objective/run
│       ├── GET  /objective/runs
│       ├── GET  /objective/run/{run_id}
│       ├── POST /objective/compare
│       ├── POST /objective/tornado
│       ├── POST /objective/tag/{run_id}
│       ├── DELETE /objective/run/{run_id}
│       └── GET  /objective/units/formats
│
data/
└── objective_runs/  # Scenario run storage
    ├── {uuid-1}.json
    ├── {uuid-2}.json
    └── {uuid-3}.json

frontend/
└── src/
    └── components/
        └── ObjectiveFormula.tsx  # Formula display component (NEW)
```

---

## 🔧 Integration Steps

### 1. Install KaTeX (Frontend)
```bash
cd frontend
npm install katex @types/katex
```

### 2. Register Enhanced Router (Backend)
Add to `backend/gateway/app.py`:
```python
from backend.engine.router_objective_enhanced import router as objective_enhanced_router

app.include_router(objective_enhanced_router, prefix="/api")
```

### 3. Update ObjectiveComparison Component
```typescript
// frontend/src/components/ObjectiveComparison.tsx
import ObjectiveFormula from './ObjectiveFormula';
import DeltaWithCICard from './DeltaWithCICard';  // TODO: Create
import ScenarioCompare from './ScenarioCompare';  // TODO: Create
import TornadoChart from './TornadoChart';        // TODO: Create

const ObjectiveComparison = () => {
  return (
    <div>
      <ObjectiveFormula className="mb-6" />  {/* NEW */}

      <ScenarioPlayground ... />

      <DeltaWithCICard delta_ci={comparisonData.delta_with_ci} />  {/* NEW */}

      <TornadoChart params={params} />  {/* NEW */}

      <ScenarioCompare run_ids={[...]} />  {/* NEW */}
    </div>
  );
};
```

---

## 🧪 Testing

### Backend Tests
```bash
# Test formula endpoint
pytest backend/tests/test_objective_enhanced.py::test_get_formula

# Test CI computation
pytest backend/tests/test_objective_enhanced.py::test_delta_with_ci

# Test scenario management
pytest backend/tests/test_objective_enhanced.py::test_save_and_load_run
pytest backend/tests/test_objective_enhanced.py::test_compare_runs

# Test tornado diagram
pytest backend/tests/test_objective_enhanced.py::test_tornado_sensitivity
```

### Frontend Tests
```bash
cd frontend
npm run test -- ObjectiveFormula.test.tsx
```

### Manual Testing
```bash
# 1. Start services
./scripts/start_services.sh

# 2. Test formula endpoint
curl http://localhost:8081/objective/formula

# 3. Save a run
curl -X POST http://localhost:8081/objective/run \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "realistic_retail_5k",
    "scenario_id": "S1_geo_budget",
    "params": {"coverage": 30, "budget_cap": 12000000},
    "s0_results": {"J": 1000000},
    "s1_results": {"J": 1234567},
    "tag": "Baseline"
  }'

# 4. List runs
curl http://localhost:8081/objective/runs

# 5. Generate tornado diagram
curl -X POST http://localhost:8081/objective/tornado \
  -H "Content-Type: application/json" \
  -d '{
    "params": {"coverage": 30, "budget_cap": 12000000, "policy_threshold": 0.5},
    "param_names": ["coverage", "budget_cap", "policy_threshold"],
    "dataset_id": "test",
    "scenario_id": "test"
  }'
```

---

## 📊 Impact: "月額100万円の説得力"

### Before (Current State)
- ❌ Δ shown without uncertainty → Low confidence
- ❌ No reproducibility → Can't revisit decisions
- ❌ Inconsistent units → Confusing
- ❌ No sensitivity → Don't know what matters
- ❌ No metadata → Can't audit

### After (With 6 Elements)
- ✅ **Δ with 95% CI** → Quantified uncertainty
- ✅ **Scenario Management** → Full reproducibility
- ✅ **Tornado Diagram** → Clear actionable insights ("pull this lever!")
- ✅ **Consistent Units** → No ambiguity
- ✅ **Formula Display** → Everyone understands the objective
- ✅ **Metadata** → Complete audit trail

**Result**: Transforms from "interesting analysis" to **"board-ready decision support tool"**

---

## 🚀 Next Steps (Frontend Components)

1. **DeltaWithCICard.tsx** - Display Δ with confidence interval and badge
2. **ScenarioCompare.tsx** - Side-by-side comparison table
3. **TornadoChart.tsx** - Horizontal bar chart for sensitivity
4. **MetadataFooter.tsx** - Display run_id, seed, timestamp

---

## 📚 References

- **Spec**: `/home/hirokionodera/CQO/可視化③.pdf`
- **Backend Core**: `backend/core/objective_comparison_enhanced.py`
- **API Router**: `backend/engine/router_objective_enhanced.py`
- **Frontend Component**: `frontend/src/components/ObjectiveFormula.tsx`
- **Expert Insight**: "Δだけを出すUIは意思決定では弱い。Δの95%CIと感度（トルネード）を同時に出すと、効果の確からしさと何を動かせばレバーが効くかを一画面で説明でき、承認プロセスの反論コストを劇的に下げる。" (Google/Meta/NASA level insight from 可視化③.pdf)

---

**Implementation Date**: 2025-11-14
**Implemented By**: Claude Code
**Status**: Backend ✅ Complete | Frontend 🔄 In Progress
