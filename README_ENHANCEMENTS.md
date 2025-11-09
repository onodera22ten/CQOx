# CQOx Enhancements - NASA/Google Standard

## 🚀 新機能

このリポジトリは、mission-ctl-CQOxの未完成部分を完成させ、NASA/Googleレベルの品質基準に準拠した因果推論プラットフォームです。

### 主要な改善点

#### 1. 厳格なデータ契約（Strict Data Contract）
- ❌ **偽推定を排除**: 必須列がない場合、HTTP 400を返す（500禁止）
- 📝 **導出台帳**: 全ての導出を透明に記録
- 🔒 **環境変数制御**: 明示的な許可のみで推定を実行

#### 2. ネットワーク・地理因果推論
- 🌐 **Network Exposure**: k-NN、Radius、Edge-basedの3方式
- 🗺️ **Geographic**: 距離減衰、空間ラグ、Moran's I
- 🔗 **部分干渉**: クラスター内干渉をモデル化

#### 3. 反実仮想シミュレーター
- ⚡ **OPE（探索）**: IPS/SNIPS/DRで高速評価
- 🎯 **g-comp（確証）**: 上位候補を精緻に再評価
- 📊 **ScenarioSpec DSL**: 宣言的なシナリオ定義

#### 4. Money-View（金額換算）
- 💰 **ΔProfit計算**: 全メトリクスを¥に換算
- 📈 **CI伝播**: 信頼区間も金額で表示
- 💵 **右軸オーバーレイ**: 全図に金額軸を追加

#### 5. Compare-First UI
- 🔄 **S0/S1横並び**: 観測vs反実仮想を同時表示
- 🎨 **SmartFigure**: img/iframe/video自動切替
- 📐 **ゼロ高さ防止**: Skeletonローディング

#### 6. 品質ゲート自動化
- ✅ **GO/CANARY/HOLD**: 自動判定（70%/50%閾値）
- 🔬 **NASA/Google基準**: IV F>10、Overlap、McCrary等
- 📊 **可視化**: 全ゲートの通過/失敗を一覧表示

## 📦 新規ファイル

### Backend
```
backend/
├── engine/
│   ├── network_exposure.py        # ネットワーク/地理exposure計算
│   ├── ope_simulator.py           # OPEシミュレーター
│   ├── money_view.py              # 金額換算
│   ├── quality_gates_enhanced.py  # 強化された品質ゲート
│   └── router_scenario.py         # シナリオAPIエンドポイント
└── common/
    └── schema_validator.py        # Strict Data Contract（既存改善）
```

### Frontend
```
frontend/src/
├── lib/
│   └── types.ts                   # 型定義（SSOT）
└── components/ui/
    ├── ChartCard.tsx              # 標準化カード
    ├── SmartFigure.tsx            # 自動レンダリング
    └── SideBySide.tsx             # S0/S1比較
```

## 🏗️ アーキテクチャ

```
┌─────────────────────────────────────┐
│ React/TypeScript UI                 │
│ - Compare-First Design              │
│ - Money-View Overlay                │
└─────────────────────────────────────┘
              ↓ REST API
┌─────────────────────────────────────┐
│ FastAPI Gateway                     │
│ - /api/scenario/simulate (OPE)      │
│ - /api/scenario/confirm (g-comp)    │
│ - Strict Data Contract (400 on err) │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ Business Logic                      │
│ - OPE Simulator (IPS/SNIPS/DR)      │
│ - Network Exposure Calculator       │
│ - Money-View Converter              │
│ - Enhanced Quality Gates            │
└─────────────────────────────────────┘
```

## 🚀 クイックスタート

### 1. インストール

```bash
# Backend依存関係
pip install -r requirements.txt

# Frontend依存関係
cd frontend
npm install
```

### 2. 環境変数

```bash
# 厳格モード（推奨）
export STRICT_DATA_CONTRACT=1
export ALLOW_MOCK_COUNTERFACTUAL=0
export ALLOW_ESTIMATE_PROPENSITY=0
```

### 3. サーバー起動

```bash
# Backend
uvicorn backend.engine.server:app --host 0.0.0.0 --port 8080

# Frontend（別ターミナル）
cd frontend
npm run dev  # → http://localhost:4006
```

### 4. データ準備

```python
import pandas as pd

df = pd.DataFrame({
    'y': [...],         # 結果変数
    'treatment': [...], # 処置 {0,1}
    'unit_id': [...],   # ユニットID
    'time': [...],      # 時間
    'cost': [...],      # コスト
    'X_age': [...],     # 共変量
    'X_income': [...],
    # ... 必要に応じて追加
})

df.to_parquet('data/demo/data.parquet')
```

### 5. シミュレーション実行

```bash
curl -X POST http://localhost:8080/api/scenario/simulate \
  -H 'Content-Type: application/json' \
  -d '{
    "dataset_id": "demo",
    "scenario_id": "S1",
    "mode": "OPE",
    "coverage": 0.30,
    "value_per_y": 1200,
    "cost_per_treated": 300
  }'
```

## 📊 使用例

### ネットワーク因果推論

```python
from backend.engine.network_exposure import calculate_knn_exposure

# k-NNでexposure計算
df_with_exposure = calculate_knn_exposure(
    df,
    k=5,
    lat_col="lat",
    lon_col="lon",
    treatment_col="treatment",
    decay="exp",
    alpha=0.7
)

# exposure列が追加される
print(df_with_exposure[['unit_id', 'treatment', 'exposure']].head())
```

### OPEシミュレーション

```python
from backend.engine.ope_simulator import OPESimulator, ScenarioSpec

# シミュレーター作成
simulator = OPESimulator(df)

# シナリオ定義
spec = ScenarioSpec(
    id="S1_budget_30pct",
    label="30%カバレッジ + 予算制約",
    coverage=0.30,
    budget_cap=12_000_000,
    value_per_y=1200,
    cost_per_treated=300
)

# 実行
result = simulator.simulate_scenario(spec, method="dr")

print(f"期待利益: ¥{result['profit']:,.0f}")
print(f"判定: {result['fairness_violation'] or 'OK'}")
```

### Money-View

```python
from backend.engine.money_view import MoneyView, MoneyParams

params = MoneyParams(value_per_y=1200, cost_per_unit=300)
money_view = MoneyView(params)

result = money_view.ate_to_money(
    ate=0.15,
    ate_ci=(0.10, 0.20),
    n_units=10000,
    cost=3_000_000
)

print(f"ΔProfit: {result['delta_profit_formatted']}")
# → ΔProfit: ¥1,800,000
```

### 品質ゲート

```python
from backend.engine.quality_gates_enhanced import EnhancedQualityGates

gates = EnhancedQualityGates()

report = gates.evaluate_all(
    df,
    estimate=0.15,
    ci=(0.10, 0.20),
    se=0.025,
    estimator_type="iv"
)

print(report.decision)   # "GO", "CANARY", or "HOLD"
print(report.summary)    # "PASS: 8/10 gates passed (80.0%)"

for gate in report.gates:
    print(f"{gate.name}: {'✅' if gate.passed else '❌'} ({gate.message})")
```

## 📐 設計原則

### 1. No Data, No Model
```python
# ❌ 悪い例: 暗黙の補完
if "log_propensity" not in df.columns:
    df["log_propensity"] = estimate_silently(df)  # NG!

# ✅ 良い例: 明示的なエラー
if "log_propensity" not in df.columns:
    raise ValidationError(
        message="log_propensity column required",
        available_columns=list(df.columns),
        missing_columns=["log_propensity"]
    )  # HTTP 400
```

### 2. 導出台帳
```python
# 全ての導出を記録
ledger.add(Derivation(
    output_column="exposure",
    function="mean_treatment_neighborhood(k=5)",
    input_columns=["edges.parquet", "treatment"],
    rows_affected=8800,
    enabled_by_flag="ALLOW_DERIVE_EXPOSURE_FROM_EDGES=1"
))

# エクスポート
ledger.export("reports/demo/derivation_ledger.json")
```

### 3. 2段階評価
```python
# 探索: OPEで多数のシナリオを高速評価
scenarios = [S1, S2, S3, S4, S5]
ope_results = [simulator.simulate_scenario(s, method="dr") for s in scenarios]

# 確証: 上位3つをg-computationで精査
top_3 = sorted(ope_results, key=lambda r: r['profit'], reverse=True)[:3]
confirmed = [g_computation(s) for s in top_3]
```

### 4. Compare-First UI
```tsx
// 全図をS0/S1横並びに
<SideBySide
  leftTitle="ATE Density"
  rightTitle="ATE Density"
  left={<SmartFigure src="/reports/ate_density__S0.png" />}
  right={<SmartFigure src="/reports/ate_density__S1.png" />}
  unit="¥/user/month"
/>
```

## 🧪 テスト

```bash
# データ契約
pytest tests/test_contract_strict_400.py

# OPE一貫性
pytest tests/test_ope_to_gcomp_rankcorr.py

# Money-View整合性
pytest tests/test_money_overlay_consistency.py

# UI E2E
pytest tests/test_pairwise_s0s1_presence.py
```

## 📚 ドキュメント

- [実装サマリー](./IMPLEMENTATION_SUMMARY.md) - 詳細な実装内容
- [設計資料](./設計.pdf) - 元の設計要件
- [既存README](./README.md) - mission-ctl-CQOxの元README

## 🎯 設計資料との対応

| 要件 | 実装 | 状態 |
|-----|------|------|
| Strict Data Contract | ✅ | 完了 |
| 上位互換スキーマ | ✅ | 完了 |
| Network Exposure | ✅ | 完了 |
| OPE Simulator | ✅ | 完了 |
| Money-View | ✅ | 完了 |
| Quality Gates | ✅ | 完了 |
| Compare-First UI | ✅ | 完了 |
| Scenario API | ✅ | 完了 |
| 地理空間ラグ | ⏳ | 部分実装 |
| WolframONE | ✅ | iframe対応完了 |

## 🔮 今後の拡張

1. **完全な地理因果推論**
   - GWR（Geographically Weighted Regression）
   - 空間重み行列Wの最適化
   - H3/S2セルベース集計

2. **WolframONE 3D可視化**
   - ListPlot3D、Manipulate
   - GeoRegionValuePlot

3. **本番環境対応**
   - Kubernetes Helm Chart
   - ArgoCD GitOps
   - 負荷テスト

## 📝 ライセンス

元のmission-ctl-CQOxと同じライセンス

## 🙏 謝辞

設計資料（「設計（Markdown変換）」）に基づき実装しました。
