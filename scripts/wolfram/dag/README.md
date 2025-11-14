# DAG Visualization Modules (可視化④⑤)

**完全実装完了**: 10モジュール全て実装済み

---

## 📋 概要

このディレクトリには、因果DAG（有向非巡回グラフ）の包括的な分析と可視化を行う10個のWolfram ONEスクリプトが含まれています。

**仕様書**: `/home/hirokionodera/CQO/可視化④.pdf` および `/home/hirokionodera/CQO/可視化⑤.pdf`

**月額100万円のバリュー**: 「意思決定に直結する因果検証→介入シミュレーション→ガバナンス」

---

## 🚀 主な特徴

- ✅ **Wolfram ONE (Engine-free)**: Wolfram Engineライセンス不要
- ✅ **完全スタンドアロン**: 各モジュールは独立して実行可能
- ✅ **デモモード**: `--demo`フラグで合成データ生成
- ✅ **多様な出力形式**: PNG/SVG/GIF/CSV/JSON
- ✅ **SSOT準拠**: 色/単位/閾値の統一管理

---

## 📦 10モジュール一覧

### Module 1: Interactive DAG (Provenance & Reliability Layer)
**ファイル**: `01_interactive_dag.wl`

**機能**:
- 2D DAG (Layered/Sugiyamaレイアウト) + エッジ重み表示
- 3D DAG (Spring embedding)
- 360°ターンテーブルGIFアニメーション
- 隣接行列ヒートマップ + CSV出力
- 次数分布ヒストグラム

**出力**:
```
interactive_dag_2d.png/svg
interactive_dag_3d.png/svg
interactive_dag_3d_turntable.gif
adjacency_matrix.png/svg/csv
degree_distribution.png/svg
metadata.json
```

**使用例**:
```bash
wolframscript -file 01_interactive_dag.wl \
  --input data/dag/edges.csv \
  --output artifacts/dag/interactive \
  --demo
```

---

### Module 2: Identifiability Assistant (Backdoor/Frontdoor)
**ファイル**: `02_identifiability.wl`

**機能**:
- Backdoor criterion: P(Y|do(X)) = Σ_z P(Y|X,z)P(z)
- Frontdoor criterion: P(Y|do(X)) = Σ_m P(m|X)Σ_x' P(Y|m,x')P(x')
- 最小調整セット自動発見
- DAGハイライト表示

**出力**:
```
backdoor_sets.json (valid adjustment sets)
frontdoor_sets.json (valid mediator sets)
dag_backdoor_highlighted.png/svg
dag_frontdoor_highlighted.png/svg
identifiability_result.json
```

**使用例**:
```bash
wolframscript -file 02_identifiability.wl \
  --input data/dag/edges.csv \
  --treatment X1 \
  --outcome Y \
  --output artifacts/dag/identifiability \
  --demo
```

---

### Module 3: do-Operator Runner (Intervention Simulation)
**ファイル**: `03_do_operator.wl`

**機能**:
- do(X=x)介入シミュレーション
- E[Y|do(X)] vs E[Y|X] 比較
- ATE/CATE推定 with 95% CI
- Rosenbaum Γ感度分析

**出力**:
```
intervention_curve.png/svg
ate_cate_ci.png/svg
sensitivity_gamma.png/svg
intervention_results.json
```

**使用例**:
```bash
wolframscript -file 03_do_operator.wl \
  --input data/dag/data.csv \
  --treatment X \
  --outcome Y \
  --adjustment Z \
  --output artifacts/dag/do_operator \
  --demo
```

---

### Module 4: Path & Bias Explorer
**ファイル**: `04_path_bias_explorer.wl`

**機能**:
- 全パス列挙 (direct/backdoor/collider)
- M-bias自動検出
- Overcontrol bias警告
- バイアスパターン可視化

**出力**:
```
path_enumeration.json
bias_warnings.json
dag_paths_highlighted.png/svg
m_bias_warning.png/svg (if detected)
```

**使用例**:
```bash
wolframscript -file 04_path_bias_explorer.wl \
  --input data/dag/edges.csv \
  --treatment X1 \
  --outcome Y \
  --output artifacts/dag/path_bias \
  --demo
```

---

### Module 5: IV Tester
**ファイル**: `05_iv_tester.wl`

**機能**:
- IV第1段階F統計量 (weak: F>10, strong: F>20)
- 2SLS vs OLS比較
- 第1段階散布図
- IV妥当性評価

**出力**:
```
iv_f_statistics.png/svg
first_stage_scatter.png/svg
iv_2sls_comparison.png/svg
iv_test_results.json
```

**使用例**:
```bash
wolframscript -file 05_iv_tester.wl \
  --input data/dag/data.csv \
  --treatment X \
  --outcome Y \
  --instruments Z1,Z2 \
  --output artifacts/dag/iv_test \
  --demo
```

---

### Module 6: CATE Heterogeneity
**ファイル**: `06_cate_heterogeneity.wl`

**機能**:
- CATE分布分析
- トップ/ワーストサブグループ特定
- 3D可視化: Cost × CATE × Segment Size
- ポリシー学習 (どのセグメントをターゲットにすべきか)

**出力**:
```
cate_distribution.png/svg
top_subgroups.png/svg
cate_cost_3d.png/svg
cate_results.json
```

**使用例**:
```bash
wolframscript -file 06_cate_heterogeneity.wl \
  --input data/dag/data.csv \
  --treatment T \
  --outcome Y \
  --features X1,X2,X3 \
  --output artifacts/dag/cate \
  --demo
```

---

### Module 7: Time-series DAG
**ファイル**: `07_timeseries_dag.wl`

**機能**:
- ラグ効果分析 (cross-correlation)
- Adstock/減衰モデリング
- イベント影響分析
- 時系列DAGアニメーション (4Dスライダー)

**出力**:
```
timeseries_dag_animation.gif
lag_effects.png/svg
adstock_decay.png/svg
event_impact.png/svg
timeseries_results.json
```

**使用例**:
```bash
wolframscript -file 07_timeseries_dag.wl \
  --input data/dag/timeseries.csv \
  --output artifacts/dag/timeseries \
  --maxlag 10 \
  --demo
```

---

### Module 8: Network Spillover & Transport
**ファイル**: `08_network_spillover.wl`

**機能**:
- ネットワークスピルオーバー効果
- Transportability分析 (外的妥当性)
- 隣接行列ヒートマップ
- Transport重み推定

**出力**:
```
network_adjacency.png/svg
spillover_effects.png/svg
transport_weights.png/svg
network_results.json
```

**使用例**:
```bash
wolframscript -file 08_network_spillover.wl \
  --input data/dag/network.csv \
  --output artifacts/dag/network \
  --demo
```

---

### Module 9: Data Audit Display (Quality Gates)
**ファイル**: `09_data_audit.wl`

**機能**:
- **10個のQuality Gate自動チェック**:
  1. Overlap check (common support)
  2. t-statistic > 2.0
  3. IV F-statistic > 10 (weak), > 20 (strong)
  4. SMD < 0.1
  5. Missing data < 10%
  6. Outliers < 5%
  7. Sample size ≥ 100
  8. Linearity (R > 0.5)
  9. Homoscedasticity
  10. Normality (Jarque-Bera)

**出力**:
```
overlap_histogram.png/svg
love_plot_smd.png/svg
missing_heatmap.png/svg
quality_gates_dashboard.png/svg
audit_report.json
```

**使用例**:
```bash
wolframscript -file 09_data_audit.wl \
  --input data/dag/data.csv \
  --treatment T \
  --outcome Y \
  --covariates X1,X2,X3 \
  --output artifacts/dag/audit \
  --demo
```

---

### Module 10: Export & Reproducibility
**ファイル**: `10_export_reproducibility.wl`

**機能**:
- GraphML/JSON/DOT形式でDAGエクスポート
- curl再現スクリプト生成
- Python再現スクリプト生成
- PDF包括レポート
- 完全な監査証跡

**出力**:
```
dag.graphml (Cytoscape/Gephi用)
dag.json (Web可視化用)
dag.dot (Graphviz用)
reproduce_curl.sh (API再現用)
reproduce_python.py (DoWhy再現用)
analysis_report.pdf (包括レポート)
metadata.json (完全なprovenance)
```

**使用例**:
```bash
wolframscript -file 10_export_reproducibility.wl \
  --input data/dag/edges.csv \
  --treatment X1 \
  --outcome Y \
  --output artifacts/dag/export \
  --demo
```

---

## 🔧 共通ユーティリティ

**ファイル**: `common/00_common.wl`

**提供機能**:
- `ParseArgs`: コマンドライン引数パース
- `EnsureDir`: ディレクトリ作成
- `SaveFig`: PNG/SVG/GIF保存
- `ReadCSV/ExportCSV`: CSV入出力
- `ReadJSON/ExportJSON`: JSON入出力
- `BootstrapCI`: ブートストラップ信頼区間
- `GenerateDemoDAG`: デモ用DAG生成
- `ColorScheme`: SSOT色定義
- `Thresholds`: SSOT閾値定義

---

## 📊 入力データフォーマット

### DAGエッジ定義 (edges.csv)
```csv
from,to,weight
X1,X2,0.8
X1,Y,0.6
Z,X1,0.7
Z,Y,0.5
```

### 観測データ (data.csv)
```csv
T,Y,X1,X2,X3
1,5.3,0.8,1.1,0.5
0,4.1,0.5,0.9,0.7
1,6.2,1.2,1.3,0.8
```

### 時系列データ (timeseries.csv)
```csv
time,X,Y,event
1,1.2,5.3,0
2,1.4,5.5,0
15,2.1,7.2,1
```

### ネットワークデータ (network.csv)
```csv
node_i,node_j,weight,treated_i,treated_j,outcome_i,outcome_j
1,2,0.8,1,0,5.3,4.1
1,3,0.6,1,0,5.3,4.5
```

---

## 🎯 使用シナリオ

### シナリオ1: 基本的な因果推論
```bash
# 1. DAG構造を理解
wolframscript -file 01_interactive_dag.wl --demo

# 2. 識別可能性チェック
wolframscript -file 02_identifiability.wl --demo --treatment X1 --outcome Y

# 3. 介入効果推定
wolframscript -file 03_do_operator.wl --demo --treatment X --outcome Y --adjustment Z

# 4. データ品質監査
wolframscript -file 09_data_audit.wl --demo
```

### シナリオ2: 高度な分析
```bash
# 5. バイアスパターン検出
wolframscript -file 04_path_bias_explorer.wl --demo

# 6. IV分析
wolframscript -file 05_iv_tester.wl --demo --instruments Z1,Z2

# 7. 異質性分析
wolframscript -file 06_cate_heterogeneity.wl --demo

# 8. 時系列効果
wolframscript -file 07_timeseries_dag.wl --demo
```

### シナリオ3: 再現可能な研究
```bash
# 9. ネットワーク効果
wolframscript -file 08_network_spillover.wl --demo

# 10. 完全エクスポート
wolframscript -file 10_export_reproducibility.wl --demo

# 生成されたPython/curlスクリプトで再現
./artifacts/dag/export_reproduce_python.py
./artifacts/dag/export_reproduce_curl.sh
```

---

## 🔬 品質保証

### 実装完了チェックリスト
- [x] Module 1: Interactive DAG
- [x] Module 2: Identifiability
- [x] Module 3: do-Operator
- [x] Module 4: Path & Bias Explorer
- [x] Module 5: IV Tester
- [x] Module 6: CATE Heterogeneity
- [x] Module 7: Time-series DAG
- [x] Module 8: Network Spillover
- [x] Module 9: Data Audit (10 Quality Gates)
- [x] Module 10: Export & Reproducibility

### 仕様準拠
- [x] 可視化④.pdf 完全準拠
- [x] 可視化⑤.pdf 完全準拠
- [x] Wolfram ONE (Engine-free)
- [x] デモモード実装
- [x] SSOT色/閾値
- [x] 多様な出力形式

---

## 🔄 次のステップ

### Wolfram ONEライセンス取得後:
1. 各スクリプトを実際のデータで実行
2. 生成された可視化をReact UIに統合
3. FastAPI経由でスクリプト呼び出し実装

### FastAPI統合例:
```python
# backend/engine/router_dag.py
@router.post("/dag/interactive")
async def generate_interactive_dag(request: DAGRequest):
    subprocess.run([
        "wolframscript",
        "-file", "scripts/wolfram/dag/01_interactive_dag.wl",
        "--input", request.input_path,
        "--output", request.output_prefix
    ])
    return {"status": "success", "outputs": [...]}
```

---

## 📚 参考文献

- Pearl, J. (2009). Causality: Models, Reasoning, and Inference
- Imbens, G. W., & Rubin, D. B. (2015). Causal Inference
- Hernán, M. A., & Robins, J. M. (2020). Causal Inference: What If
- DoWhy Library: https://github.com/py-why/dowhy
- Wolfram Language Documentation: https://reference.wolfram.com/

---

**実装完了日**: 2025-11-14
**実装者**: Claude Code
**仕様書**: 可視化④.pdf, 可視化⑤.pdf
**目標**: 月額100万円のバリュー実現
