# 完全統合ガイド - CQOx 可視化③④⑤⑥実装

**実装日**: 2025-11-14
**実装者**: Claude Code
**ステータス**: ✅ 可視化③④⑤ 完全実装完了 | 🔄 可視化⑥ 次のステップ

---

## 📋 実装完了サマリー

### ✅ DAGページ (可視化④⑤) - 完全実装

**10個のWolfram ONEモジュール**:

1. ✅ **Interactive DAG** - 2D/3D/GIFアニメーション
   `scripts/wolfram/dag/01_interactive_dag.wl`

2. ✅ **Identifiability** - Backdoor/Frontdoor判定
   `scripts/wolfram/dag/02_identifiability.wl`

3. ✅ **do-Operator** - 介入シミュレーション
   `scripts/wolfram/dag/03_do_operator.wl`

4. ✅ **Path/Bias Explorer** - M-bias検出
   `scripts/wolfram/dag/04_path_bias_explorer.wl`

5. ✅ **IV Tester** - F統計量検証
   `scripts/wolfram/dag/05_iv_tester.wl`

6. ✅ **CATE Heterogeneity** - サブグループ分析
   `scripts/wolfram/dag/06_cate_heterogeneity.wl`

7. ✅ **Time-series DAG** - ラグ効果とAdstock
   `scripts/wolfram/dag/07_timeseries_dag.wl`

8. ✅ **Network Spillover** - ネットワーク効果
   `scripts/wolfram/dag/08_network_spillover.wl`

9. ✅ **Data Audit** - 10個のQuality Gates
   `scripts/wolfram/dag/09_data_audit.wl`

10. ✅ **Export & Reproducibility** - GraphML/JSON/DOT/PDF/Python/curl
    `scripts/wolfram/dag/10_export_reproducibility.wl`

**共通ユーティリティ**: `scripts/wolfram/common/00_common.wl`
**テストスクリプト**: `scripts/wolfram/test_all_modules.sh`
**ドキュメント**: `scripts/wolfram/dag/README.md`

---

### ✅ 目的関数ページ (可視化③) - 完全実装

**6個の必須要素** (月額100万円の説得力):

#### 1. ✅ 目的関数の明示
- **コンポーネント**: `frontend/src/components/ObjectiveFormula.tsx`
- **API**: `GET /api/objective/formula`
- **機能**: J(θ)数式をKaTeX表示、V_Y・C_T表示

#### 2. ✅ Δの95%CI
- **コンポーネント**: `frontend/src/components/DeltaWithCICard.tsx`
- **バックエンド**: `backend/core/objective_comparison_enhanced.py::DeltaWithCI`
- **機能**: ブートストラップCI、有意性バッジ (green/yellow/red)

#### 3. ✅ シナリオ管理
- **コンポーネント**: `frontend/src/components/ScenarioCompare.tsx`
- **API**:
  - `POST /api/objective/run` - 保存
  - `GET /api/objective/runs` - 一覧
  - `GET /api/objective/run/{run_id}` - 復元
  - `POST /api/objective/compare` - 比較
  - `POST /api/objective/tag/{run_id}` - タグ付け
- **ストレージ**: `data/objective_runs/*.json`

#### 4. ✅ 単位の一貫表示
- **バックエンド**: `backend/core/objective_comparison_enhanced.py::UnitFormatter`
- **API**: `GET /api/objective/units/formats`
- **対応単位**: ¥, $, %, 件 (count)

#### 5. ✅ トルネード図
- **コンポーネント**: `frontend/src/components/TornadoChart.tsx`
- **バックエンド**: `backend/core/objective_comparison_enhanced.py::TornadoDiagram`
- **API**: `POST /api/objective/tornado`
- **機能**: 各パラメータ±10%変化時のΔ影響度ランキング

#### 6. ✅ 実行メタデータ
- **コンポーネント**: `frontend/src/components/MetadataFooter.tsx`
- **バックエンド**: `backend/core/objective_comparison_enhanced.py::ExecutionMetadata`
- **含まれるデータ**: run_id, seed, estimator_set, cv_config, created_at, engine_version

**統合ページ**: `frontend/src/components/ObjectiveComparisonEnhanced.tsx`

---

## 🔧 セットアップ手順

### 1. バックエンドの依存関係確認

既存のパッケージで動作します（追加インストール不要）:
- numpy
- pandas
- fastapi
- pydantic

### 2. フロントエンドのKaTeXインストール

```bash
cd frontend
npm install katex @types/katex
```

### 3. ディレクトリ作成

```bash
# シナリオ保存用
mkdir -p data/objective_runs

# Wolfram出力用
mkdir -p artifacts/dag
```

### 4. Wolfram ONEスクリプトを実行可能にする

```bash
chmod +x scripts/wolfram/common/*.wl
chmod +x scripts/wolfram/dag/*.wl
chmod +x scripts/wolfram/test_all_modules.sh
```

---

## 🚀 使用方法

### DAGページ (Wolfram ONE必要)

#### デモモードで全モジュールテスト:
```bash
./scripts/wolfram/test_all_modules.sh
```

#### 個別モジュール実行例:
```bash
# Module 1: Interactive DAG
wolframscript -file scripts/wolfram/dag/01_interactive_dag.wl \
  --demo \
  --output artifacts/dag/interactive

# Module 9: Data Audit (Quality Gates)
wolframscript -file scripts/wolfram/dag/09_data_audit.wl \
  --demo \
  --treatment T \
  --outcome Y \
  --covariates X1,X2,X3 \
  --output artifacts/dag/audit
```

---

### 目的関数ページ

#### サーバー起動:
```bash
# エンジンとゲートウェイを起動
./scripts/start_services.sh
```

#### API使用例:

**1. 目的関数取得**:
```bash
curl http://localhost:8081/api/objective/formula
```

**2. シナリオ保存**:
```bash
curl -X POST http://localhost:8081/api/objective/run \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "realistic_retail_5k",
    "scenario_id": "S1_geo_budget",
    "params": {"coverage": 30, "budget_cap": 12000000},
    "s0_results": {"J": 1000000},
    "s1_results": {"J": 1234567},
    "tag": "Baseline"
  }'
```

**3. 保存済みシナリオ一覧**:
```bash
curl http://localhost:8081/api/objective/runs
```

**4. シナリオ比較**:
```bash
curl -X POST http://localhost:8081/api/objective/compare \
  -H "Content-Type: application/json" \
  -d '{
    "run_ids": ["uuid-1", "uuid-2", "uuid-3"]
  }'
```

**5. トルネード図生成**:
```bash
curl -X POST http://localhost:8081/api/objective/tornado \
  -H "Content-Type: application/json" \
  -d '{
    "params": {"coverage": 30, "budget_cap": 12000000, "policy_threshold": 0.5},
    "param_names": ["coverage", "budget_cap", "policy_threshold"],
    "dataset_id": "test",
    "scenario_id": "test"
  }'
```

---

## 📂 ファイル構成

```
backend/
├── core/
│   └── objective_comparison_enhanced.py      # 6要素のコアロジック (NEW)
├── engine/
│   └── router_objective_enhanced.py          # 9個のAPIエンドポイント (NEW)
└── gateway/
    └── app.py                                 # ルーター登録追加 (MODIFIED)

frontend/
└── src/
    └── components/
        ├── ObjectiveFormula.tsx               # Element 1 (NEW)
        ├── DeltaWithCICard.tsx                # Element 2 (NEW)
        ├── ScenarioCompare.tsx                # Element 3 (NEW)
        ├── TornadoChart.tsx                   # Element 5 (NEW)
        ├── MetadataFooter.tsx                 # Element 6 (NEW)
        └── ObjectiveComparisonEnhanced.tsx    # 統合ページ (NEW)

scripts/
└── wolfram/
    ├── common/
    │   └── 00_common.wl                       # 共通ユーティリティ (NEW)
    ├── dag/
    │   ├── 01_interactive_dag.wl              # Module 1 (NEW)
    │   ├── 02_identifiability.wl              # Module 2 (NEW)
    │   ├── 03_do_operator.wl                  # Module 3 (NEW)
    │   ├── 04_path_bias_explorer.wl           # Module 4 (NEW)
    │   ├── 05_iv_tester.wl                    # Module 5 (NEW)
    │   ├── 06_cate_heterogeneity.wl           # Module 6 (NEW)
    │   ├── 07_timeseries_dag.wl               # Module 7 (NEW)
    │   ├── 08_network_spillover.wl            # Module 8 (NEW)
    │   ├── 09_data_audit.wl                   # Module 9 (NEW)
    │   ├── 10_export_reproducibility.wl       # Module 10 (NEW)
    │   └── README.md                          # DAGドキュメント (NEW)
    └── test_all_modules.sh                    # テストスクリプト (NEW)

data/
└── objective_runs/                            # シナリオ保存ディレクトリ (NEW)
    ├── {uuid-1}.json
    ├── {uuid-2}.json
    └── ...

artifacts/
└── dag/                                       # Wolfram出力ディレクトリ (NEW)
    ├── interactive/
    ├── identifiability/
    ├── do_operator/
    └── ...
```

---

## 🧪 テスト

### バックエンドテスト

```bash
# 目的関数ページのテスト
pytest backend/tests/test_objective_enhanced.py -v

# 個別テスト
pytest backend/tests/test_objective_enhanced.py::test_get_formula -v
pytest backend/tests/test_objective_enhanced.py::test_delta_with_ci -v
pytest backend/tests/test_objective_enhanced.py::test_save_and_load_run -v
pytest backend/tests/test_objective_enhanced.py::test_tornado_sensitivity -v
```

### フロントエンドテスト

```bash
cd frontend

# ObjectiveFormula
npm run test -- ObjectiveFormula.test.tsx

# DeltaWithCICard
npm run test -- DeltaWithCICard.test.tsx

# TornadoChart
npm run test -- TornadoChart.test.tsx
```

### 統合テスト

```bash
# 1. サーバー起動
./scripts/start_services.sh

# 2. ブラウザで確認
open http://localhost:3000/objective-comparison

# 3. 操作フロー確認:
#    - 目的関数が表示されるか
#    - パラメータ調整後、シナリオ実行
#    - Δに95%CIが表示されるか
#    - 保存ボタンでシナリオ保存
#    - 比較テーブルで複数シナリオ比較
#    - トルネード図で感度分析表示
#    - フッターにメタデータ表示
```

---

## 📊 成果: 月額100万円の説得力

### Before (既存):
- ❌ ΔだけでCI無し → 不確実性不明
- ❌ 再現不可 → 監査不可
- ❌ 単位バラバラ → 混乱
- ❌ 感度不明 → 何を改善すべきか不明
- ❌ メタデータ無し → 追跡不可

### After (実装後):
- ✅ **Δ with 95% CI** → 統計的有意性を数値で提示
- ✅ **シナリオ管理** → 完全な再現性とA/B比較
- ✅ **トルネード図** → 「このレバーを引け」と明確
- ✅ **単位統一** → 誤解ゼロ
- ✅ **数式表示** → 全員が目標を理解
- ✅ **メタデータ** → 監査証跡完備

**結果**: 「興味深い分析」→ **「役員会で通る意思決定ツール」**

---

## 🔜 次のステップ: マーケティングROIページ (可視化⑥)

### P0優先実装 (意思決定ツール化の5要素)

参照: `/home/hirokionodera/CQO/可視化⑥.pdf`

1. **Budget Recommendation Table** (Decision Pack)
   - 推奨予算配分 + risk_of_loss + 95%CI
   - 実装先: Wolfram ONE or Python/Plotly

2. **Qini Curve & Uplift Decile**
   - AUUC (Area Under Uplift Curve) with CI
   - トップ10%のリフト効果検証

3. **Retention Cohort Heatmap**
   - 月 × 獲得コホート
   - 色: retention rate

4. **Calibration Plot + Backtest**
   - 予測 vs 実測
   - Slope ≈ 1, ECE < 0.1
   - MAPE/SMAPE表示

5. **Distributed Lag Response + Tornado**
   - IRF (Impulse Response Function)
   - パラメータ感度 ±10%

---

## 📚 ドキュメント

- **DAG詳細**: `scripts/wolfram/dag/README.md`
- **目的関数詳細**: `backend/OBJECTIVE_COMPARISON_IMPROVEMENTS.md`
- **本ガイド**: `COMPLETE_INTEGRATION_GUIDE.md`

---

## ✅ チェックリスト

### DAGページ
- [x] 10モジュール全てWolfram ONEで実装
- [x] 共通ユーティリティ作成
- [x] デモモード実装
- [x] テストスクリプト作成
- [x] README完備
- [ ] Wolfram ONEライセンス取得後の実行テスト

### 目的関数ページ
- [x] 6要素全てのバックエンド実装
- [x] 6要素全てのフロントエンド実装
- [x] API統合 (9エンドポイント)
- [x] ルーター登録
- [x] ドキュメント作成
- [ ] KaTeXインストール (`npm install katex @types/katex`)
- [ ] ブラウザでの動作確認

### マーケティングROIページ
- [ ] 可視化⑥.pdfの詳細確認
- [ ] P0優先5要素の実装
- [ ] 既存18チャートとの統合

---

**実装完了日**: 2025-11-14
**実装ステータス**:
- ✅ 可視化④⑤ (DAG) - 完全実装
- ✅ 可視化③ (目的関数) - 完全実装
- 🔄 可視化⑥ (マーケティングROI) - 次のステップ

**次のアクション**:
1. `cd frontend && npm install katex @types/katex`
2. サーバー起動して目的関数ページの動作確認
3. 可視化⑥のP0実装に着手
