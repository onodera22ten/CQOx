# CQOx 完全アーキテクチャマップ

## 🎯 目的
CQOx（Causal Query Optimization eXtended）の全機能を網羅したアーキテクチャマップ。
3D/4D可視化、マーケティングROI、DAG、反実仮想パラメータ制御の実装場所を明示。

---

## 📊 システム全体図

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          CQOx システム全体                                   │
│                                                                             │
│  ┌──────────────────┐  HTTP   ┌──────────────────┐  SQL  ┌──────────────┐ │
│  │   React UI       │ ◄────► │   FastAPI        │ ◄───► │ TimescaleDB  │ │
│  │  (frontend/)     │         │   (backend/)     │       │ PostgreSQL   │ │
│  └──────────────────┘         └──────────────────┘       └──────────────┘ │
│         │                              │                                    │
│         │                              ├─ 23推定器 (PSM, IPW, DiD, etc.)   │
│         │                              ├─ 反実仮想エンジン (8パラメータ)    │
│         │                              ├─ マーケティングROI (Phase 1-4)    │
│         │                              ├─ WolframONE統合                   │
│         │                              └─ 診断図表生成                     │
│         │                                                                   │
│         └─ SmartFigure: HTML/PNG/MP4自動検出                               │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │                   CLI実行スクリプト (scripts/)                        │  │
│  │  ├─ 3D/4D可視化 (advanced_3d_visualizations.py)                     │  │
│  │  ├─ マーケティングROI (run_marketing_roi_optimization.py)            │  │
│  │  ├─ データ前処理 (data_preprocessing_pipeline.py)                   │  │
│  │  └─ データ生成 (generate_marketing_10k.py, etc.)                    │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │            WolframONE スクリプト (backend/wolfram/)                  │  │
│  │  ├─ 3D因果曲面 (causal_surface_3d.wls)                              │  │
│  │  ├─ 3D CATE景観 (cate_landscape_3d.wls)                            │  │
│  │  ├─ 3Dネットワーク (network_spillover_3d.wls)                       │  │
│  │  ├─ マーケティング3D (marketing_roi_3d_surface.wls)                 │  │
│  │  ├─ アニメーション (ate_animation.wls, spillover_dynamics_*.wls)   │  │
│  │  ├─ DAGネットワーク (domain_network.wls)                            │  │
│  │  └─ CASレーダー (cas_radar_chart.wls)                              │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🖥️ UI階層（React Frontend）

### ✅ **実装済み・UI統合済み**

```
main.tsx
 └─ App.tsx (メインページ - frontend/src/ui/App.tsx)
     │
     ├─ [1] データセット選択パネル
     │   ├─ プリセット: Retail 5K, Education, Finance, Policy
     │   ├─ ファイルアップロード: CSV/TSV/Parquet
     │   └─ カラムマッピング (y, treatment, unit_id, time, cost, log_propensity)
     │
     ├─ [2] Analyzeボタン → 因果推論実行
     │
     ├─ [3] MetricsDashboard (frontend/src/components/MetricsDashboard.tsx)
     │   ├─ CAS Score カード
     │   ├─ Estimators カード (23推定器数)
     │   ├─ Quality Gate カード (合格率)
     │   ├─ Average ATE カード
     │   │
     │   └─ ObjectiveComparison ★反実仮想比較 (パラメータ制御)
     │       │
     │       ├─ ScenarioPlayground (8パラメータスライダー)
     │       │   ├─ coverage: カバレッジ (0-100%)
     │       │   ├─ budget_cap: 予算上限
     │       │   ├─ policy_threshold: ポリシー閾値 (0-1)
     │       │   ├─ neighbor_boost: ネットワーク効果 (0-1)
     │       │   ├─ geo_multiplier: 地理倍率 (0-5)
     │       │   ├─ network_size: ネットワークサイズ (0-100)
     │       │   ├─ value_per_y: 1単位あたり価値
     │       │   └─ cost_per_treated: 処置コスト
     │       │
     │       ├─ ATE比較メトリクス
     │       │   ├─ 観測ATE (S0)
     │       │   ├─ 反実仮想ATE (S1)
     │       │   ├─ ΔATE
     │       │   └─ Δ利益
     │       │
     │       └─ **S0 vs S1 可視化** (FigureCompare - 左右並列)
     │           ├─ ate_density (ATE密度分布)
     │           ├─ cate_distribution (CATE分布)
     │           ├─ parallel_trends (並行トレンド)
     │           ├─ event_study (イベントスタディ)
     │           ├─ network_exposure (ネットワーク露出)
     │           ├─ spatial_heatmap (空間ヒートマップ)
     │           ├─ policy_frontier (政策フロンティア)
     │           └─ cas_radar (CASレーダー)
     │
     ├─ [4] Estimation Results (23推定器バーチャート)
     │   └─ PSM, IPW, DiD, RDD, IV, DML, Causal Forest, BART, etc.
     │
     └─ [5] Diagnostic Figures (TasksPanel - 診断図表)
         ├─ balance_smd (バランス診断)
         ├─ propensity_overlap (傾向スコア重なり)
         ├─ parallel_trends (並行トレンド)
         ├─ event_study (イベントスタディ)
         ├─ rosenbaum_sensitivity (感度分析)
         ├─ heterogeneity_waterfall (異質性ウォーターフォール)
         ├─ network_spillover (ネットワークスピルオーバー)
         ├─ iv_first_stage_f (IV第1段階F統計量)
         ├─ iv_strength_stability (IV強度・安定性)
         ├─ tvce (時変因果効果)
         ├─ transport_weights (輸送重み)
         ├─ cas_radar (CASレーダー)
         ├─ ate_density (ATE密度)
         └─ quality_gates_board (品質ゲート全体)
```

### ❌ **未実装・UI統合なし**

以下の機能はバックエンド/CLIで完全実装済みだが、UIには統合されていない：

1. **3D/4D可視化**
   - 場所: `scripts/advanced_3d_visualizations.py`
   - 実行方法: CLI実行のみ
   - 含まれる図:
     - 3D因果効果曲面
     - 3Dネットワークグラフ
     - 4D時系列アニメーション
     - インタラクティブDAG
     - 3D地理ヒートマップ

2. **マーケティングROI最適化 (Phase 1-4)**
   - 場所: `backend/marketing/roi_engine.py`, `scripts/run_marketing_roi_optimization.py`
   - 実行方法: CLI実行のみ
   - 機能:
     - Incremental ROI Calculator
     - Budget Optimizer
     - Multi-Touch Attribution
     - LTV Predictor
     - Marketing Mix Modeling
     - Realtime ROI Dashboard

3. **AI可視化推奨エンジン**
   - 場所: `backend/ai/visualization_advisor.py`
   - 実行方法: API経由（UIから未使用）

---

## 📁 ファイル・スクリプト一覧

### 🐍 Pythonスクリプト (scripts/)

#### ✨ 3D/4D可視化
```bash
scripts/advanced_3d_visualizations.py
```
**実行方法:**
```bash
docker compose exec backend python scripts/advanced_3d_visualizations.py
```
**生成される図:**
- 3D因果効果曲面
- インタラクティブDAG
- 4D時系列アニメーション (3D + 時間軸)
- 3Dネットワークグラフ
- 3D地理ヒートマップ
- 3Dヘテロジェニティ景観
- 処置効果アニメーション (MP4)
- パレート最適フロンティア3D

#### 💰 マーケティングROI最適化
```bash
scripts/run_marketing_roi_optimization.py          # Phase 1-4実行
scripts/visualize_marketing_roi.py                 # 可視化詳細版
scripts/visualize_marketing_roi_simple.py          # 可視化簡易版
scripts/create_marketing_roi_visualizations.py     # 可視化作成
scripts/generate_marketing_10k.py                  # テストデータ生成
```
**実行方法:**
```bash
docker compose exec backend python scripts/run_marketing_roi_optimization.py
```
**Phase 1-4内容:**
- Phase 1: Incremental ROI分析
- Phase 2: Budget最適化
- Phase 3: Multi-Touch Attribution
- Phase 4: LTV予測 & Marketing Mix Modeling

#### 📊 データ前処理・生成
```bash
scripts/data_preprocessing_pipeline.py             # 前処理 (6言語対応)
scripts/generate_marketing_10k.py                  # マーケティングデータ
scripts/generate_realistic_retail.py               # 小売データ
scripts/generate_complete_dataset.py               # 完全データセット
scripts/generate_ultimate_dataset.py               # 最終データセット
scripts/generate_demo_data.py                      # デモデータ
scripts/generate_sample_data.py                    # サンプルデータ
scripts/make_sample_data.py                        # サンプル作成
```

#### 🔬 推定・可視化実行
```bash
scripts/run_all_estimators.py                      # 全推定器実行
scripts/generate_estimator_visualizations.py       # 推定器可視化
scripts/generate_visualizations.py                 # 汎用可視化
scripts/create_lightweight_visualizations.py       # 軽量可視化
```

#### 🗄️ データベース
```bash
scripts/load_to_timescaledb.py                     # TimescaleDBロード
```

#### 🧪 テスト
```bash
scripts/test_e2e_full.py                           # E2Eテスト
```

#### 📈 ダッシュボード生成
```bash
scripts/generate_dashboard.py                      # ダッシュボード生成
scripts/gen_dashboard.py                           # ダッシュボード生成v2
```

**合計:** 22スクリプト

---

### 🐚 シェルスクリプト (scripts/)

```bash
scripts/check_docker.sh                            # Docker環境チェック
scripts/check_integration.sh                       # 統合チェック
scripts/docker_full_reset.sh                       # Docker完全リセット
scripts/run_batch_analysis.sh                      # バッチ解析実行
scripts/run_minimal_pipeline.sh                    # 最小パイプライン
scripts/setup_monitoring.sh                        # モニタリング設定
scripts/start_backend.sh                           # バックエンド起動
scripts/start_services.sh                          # サービス起動
scripts/test_full_pipeline.sh                      # フルパイプラインテスト
```

**合計:** 9スクリプト

---

### 🔮 WolframONE スクリプト (backend/wolfram/)

#### 3D可視化
```mathematica
backend/wolfram/causal_surface_3d.wls              # 3D因果曲面
backend/wolfram/cate_landscape_3d.wls              # 3D CATE景観
backend/wolfram/network_spillover_3d.wls           # 3Dネットワークスピルオーバー
backend/wolfram/marketing_roi_3d_surface.wls       # マーケティングROI 3D曲面
```

#### アニメーション
```mathematica
backend/wolfram/ate_animation.wls                  # ATE時系列アニメーション
backend/wolfram/spillover_dynamics_animation.wls   # スピルオーバーダイナミクス
```

#### ネットワーク・DAG
```mathematica
backend/wolfram/domain_network.wls                 # ドメイン別ネットワークグラフ
```

#### その他
```mathematica
backend/wolfram/cas_radar_chart.wls                # CASレーダーチャート
backend/wolfram/shadow_price_net_benefit.wls       # シャドウプライス・純便益
backend/wolfram/all_42_figures_templates.wls       # 42図表テンプレート
backend/wolfram/figures_42_templates.wls           # 42図表v2
backend/wolfram/common_library.wls                 # 共通ライブラリ
```

**合計:** 13スクリプト

---

### 🏗️ バックエンドモジュール (backend/)

```
backend/
├── ai/                        # AI推奨エンジン
│   └── visualization_advisor.py
├── chaos/                     # カオスエンジニアリング
├── common/                    # 共通ユーティリティ
├── counterfactual/            # 反実仮想エンジン
├── db/                        # データベース接続
├── engine/                    # コアエンジン (推定器・図表)
│   ├── estimators_integrated.py      # 23推定器統合
│   ├── figures.py                    # 基本図表
│   ├── figures_advanced.py           # 高度な図表
│   ├── figures_objective.py          # 目的関数図表
│   ├── figures_primitives.py         # プリミティブ図表
│   ├── wolfram_integrated.py         # WolframONE統合
│   ├── wolfram_cf_visualizer.py      # 反実仮想WolframONE
│   ├── counterfactual_automation.py  # 反実仮想自動化
│   ├── quality_gates.py              # 品質ゲート
│   └── server.py                     # FastAPIサーバー
├── gateway/                   # APIゲートウェイ
├── inference/                 # 推論エンジン
├── ingestion/                 # データ取り込み
├── marketing/                 # マーケティングROIエンジン ★
│   └── roi_engine.py                 # ROI最適化エンジン
├── observability/             # 可観測性 (Prometheus, Grafana)
├── optimization/              # 最適化エンジン
├── provenance/                # データ系譜
├── reporting/                 # レポート生成
├── resilience/                # 耐障害性
├── security/                  # セキュリティ (Vault, 暗号化)
├── validation/                # データ検証
├── visualization/             # 可視化エンジン
│   └── money_view.py
├── wolfram/                   # WolframONEスクリプト群 ★
└── worker/                    # バックグラウンドワーカー
```

**合計:** 21モジュールディレクトリ

---

## 🔍 各機能の場所マップ

### 1. **3D可視化**

| 機能 | 実装場所 | UIアクセス | 実行方法 |
|------|----------|-----------|----------|
| 3D因果効果曲面 | `scripts/advanced_3d_visualizations.py` | ❌ なし | CLI |
| 3D CATE景観 | `backend/wolfram/cate_landscape_3d.wls` | ❌ なし | WolframONE |
| 3Dネットワーク | `backend/wolfram/network_spillover_3d.wls` | ❌ なし | WolframONE |
| 3D地理ヒートマップ | `scripts/advanced_3d_visualizations.py` | ❌ なし | CLI |

### 2. **4D可視化 (3D + 時間)**

| 機能 | 実装場所 | UIアクセス | 実行方法 |
|------|----------|-----------|----------|
| 4D時系列アニメーション | `scripts/advanced_3d_visualizations.py` | ❌ なし | CLI |
| ATEアニメーション | `backend/wolfram/ate_animation.wls` | ❌ なし | WolframONE |
| スピルオーバーダイナミクス | `backend/wolfram/spillover_dynamics_animation.wls` | ❌ なし | WolframONE |

### 3. **DAG (因果グラフ)**

| 機能 | 実装場所 | UIアクセス | 実行方法 |
|------|----------|-----------|----------|
| インタラクティブDAG | `scripts/advanced_3d_visualizations.py` | ❌ なし | CLI |
| ドメインネットワークDAG | `backend/wolfram/domain_network.wls` | ❌ なし | WolframONE |

### 4. **マーケティングROI最適化**

| 機能 | 実装場所 | UIアクセス | 実行方法 |
|------|----------|-----------|----------|
| Incremental ROI Calculator | `backend/marketing/roi_engine.py` | ❌ なし | API/CLI |
| Budget Optimizer | `backend/marketing/roi_engine.py` | ❌ なし | API/CLI |
| Multi-Touch Attribution | `backend/marketing/roi_engine.py` | ❌ なし | API/CLI |
| LTV Predictor | `backend/marketing/roi_engine.py` | ❌ なし | API/CLI |
| Marketing Mix Modeling | `backend/marketing/roi_engine.py` | ❌ なし | API/CLI |
| Realtime ROI Dashboard | `backend/marketing/roi_engine.py` | ❌ なし | API/CLI |
| マーケティング3D曲面 | `backend/wolfram/marketing_roi_3d_surface.wls` | ❌ なし | WolframONE |

### 5. **反実仮想パラメータ制御**

| 機能 | 実装場所 | UIアクセス | 実行方法 |
|------|----------|-----------|----------|
| 8パラメータスライダー | `frontend/src/components/ScenarioPlayground.tsx` | ✅ **あり** | UI |
| S0 vs S1 比較 | `frontend/src/components/ObjectiveComparison.tsx` | ✅ **あり** | UI |
| FigureCompare (左右並列) | `frontend/src/components/figures/FigureCompare.tsx` | ✅ **あり** | UI |
| 反実仮想エンジン | `backend/engine/counterfactual_automation.py` | ✅ **あり** | API |

### 6. **WolframONE統合**

| 機能 | 実装場所 | UIアクセス | 実行方法 |
|------|----------|-----------|----------|
| WolframONE HTML生成 | `backend/engine/wolfram_integrated.py` | ✅ **あり** | 自動 |
| 反実仮想WolframONE | `backend/engine/wolfram_cf_visualizer.py` | ✅ **あり** | 自動 |
| SmartFigure表示 | `frontend/src/components/ui/SmartFigure.tsx` | ✅ **あり** | UI |

### 7. **23推定器**

| 機能 | 実装場所 | UIアクセス | 実行方法 |
|------|----------|-----------|----------|
| 推定器統合 | `backend/engine/estimators_integrated.py` | ✅ **あり** | API |
| バーチャート表示 | `frontend/src/ui/App.tsx` (lines 501-585) | ✅ **あり** | UI |

### 8. **診断図表 (14種類)**

| 機能 | 実装場所 | UIアクセス | 実行方法 |
|------|----------|-----------|----------|
| 診断図表生成 | `backend/engine/figures.py` | ✅ **あり** | API |
| TasksPanel表示 | `frontend/src/ui/TasksPanel.tsx` | ✅ **あり** | UI |

---

## 🚀 実行方法サマリー

### ✅ UI経由で実行可能

1. **基本因果推論 (23推定器 + 診断図表)**
   ```bash
   # フロントエンド起動
   cd frontend && npm run dev
   # ブラウザで http://localhost:5173 にアクセス
   # Analyzeボタンをクリック
   ```

2. **反実仮想比較 (8パラメータ制御)**
   ```bash
   # 上記UIで自動表示される
   # MetricsDashboard → ObjectiveComparison
   # スライダーで8パラメータを調整 → 「実行」ボタン
   # S0 vs S1 が左右並列で表示
   ```

### ❌ CLI経由でのみ実行可能

1. **3D/4D可視化**
   ```bash
   docker compose exec backend python scripts/advanced_3d_visualizations.py
   # 出力: /home/user/CQOx/visualizations/*.html
   ```

2. **マーケティングROI最適化 (Phase 1-4)**
   ```bash
   docker compose exec backend python scripts/run_marketing_roi_optimization.py
   # 出力: コンソール + 可視化ファイル
   ```

3. **マーケティング可視化**
   ```bash
   docker compose exec backend python scripts/visualize_marketing_roi.py
   ```

4. **WolframONE 3D可視化**
   ```bash
   # WolframONE がインストールされている場合
   wolframscript -file backend/wolfram/cate_landscape_3d.wls
   ```

---

## 📝 まとめ

### ✅ **UI統合済み機能**
1. 23推定器の因果推論
2. 14種類の診断図表
3. 反実仮想比較 (8パラメータスライダー)
4. S0 vs S1 左右並列比較 (WolframONE HTML)
5. SmartFigure自動検出 (HTML/PNG/MP4)
6. 品質ゲート・CASスコア
7. メトリクスダッシュボード

### ❌ **UI未統合機能 (バックエンド/CLI実装済み)**
1. **3D/4D可視化** (8種類)
   - 場所: `scripts/advanced_3d_visualizations.py`
2. **マーケティングROI最適化** (Phase 1-4)
   - 場所: `backend/marketing/roi_engine.py`
3. **DAG可視化** (インタラクティブDAG)
   - 場所: `scripts/advanced_3d_visualizations.py`
4. **AI可視化推奨エンジン**
   - 場所: `backend/ai/visualization_advisor.py`

---

## 🔧 次のステップ（推奨）

### オプション1: 既存UIで実行
- ObjectiveComparisonを使用して反実仮想比較（すでに実装済み）
- S0 vs S1 の左右並列表示が自動で表示される

### オプション2: CLI実行
3D/4D可視化やマーケティングROIをCLIで実行：
```bash
# 3D/4D可視化
docker compose exec backend python scripts/advanced_3d_visualizations.py

# マーケティングROI
docker compose exec backend python scripts/run_marketing_roi_optimization.py
```

### オプション3: UI統合（将来の拡張）
未統合機能をUIに追加する場合：
1. 3D可視化タブを追加
2. マーケティングROIダッシュボードを追加
3. DAG可視化パネルを追加

---

**生成日:** 2025-11-13
**バージョン:** CQOx v1.0
**ブランチ:** claude/timescaledb-marketing-pipeline-011CUyXJm6zoJFc7cNd2FL6W
