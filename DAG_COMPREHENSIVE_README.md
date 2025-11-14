# DAG包括的分析システム - 月額100万円の価値

**PDF仕様書完全準拠**: `docs/DAG.pdf`

---

## 🎯 概要

DAG因果グラフの**識別可能性→介入シミュレーション→感度分析→監査→エクスポート**まで一気通貫で実行するエンタープライズグレードシステム

### 実装済み10モジュール

1. **Interactive DAG** (プロヴナンス&信頼度レイヤ)
   - 2D/3D DAG可視化
   - 360°ターンテーブルGIF
   - 隣接行列ヒートマップ
   - 次数分布ヒストグラム

2. **Identifiability Assistant** (識別可能性アシスタント)
   - Backdoor criterion自動判定
   - Frontdoor criterion判定
   - 最小調整集合の発見
   - DAGハイライト表示

3. **do-Operator Runner** (介入シミュレーション)
   - do(X=x)介入効果推定
   - ATE/CATE with 95% CI
   - Rosenbaum Γ感度曲線
   - KPI影響の定量化

4. **Path & Bias Explorer** (パス・バイアス探索)
   - 全パス列挙 (direct/backdoor/collider)
   - M-bias自動検出と警告
   - Overcontrol bias警告
   - バイアスパターン可視化

5. **IV Tester** (操作変数テスター)
   - First-stage F統計量 (weak: F>10, strong: F>20)
   - 2SLS vs OLS比較
   - 弱IV警告と代替案提示

6. **CATE Heterogeneity** (異質効果分析)
   - セグメント別効果分布
   - トップ/ワーストサブグループ特定
   - 3D可視化: Cost × CATE × Segment
   - 推奨ターゲティング表

7. **Timeseries DAG** (時系列DAG)
   - ラグ効果分析
   - Adstock/減衰モデリング
   - イベント影響分析
   - 4Dスライダー可視化

8. **Network Spillover** (ネットワークスピルオーバー)
   - 干渉効果分析
   - Transportability分析
   - 隣接行列ヒートマップ

9. **Data Audit & Quality Gates** (データ監査)
   - **10個のQuality Gate自動チェック**:
     1. Overlap check (common support)
     2. t-statistic > 2.0
     3. IV F-statistic > 10
     4. SMD < 0.1
     5. Missing data < 10%
     6. Outliers < 5%
     7. Sample size ≥ 100
     8. Linearity (R > 0.5)
     9. Homoscedasticity
     10. Normality (Jarque-Bera)
   - Overlap/Love plot
   - Missing dataヒートマップ
   - Quality Gatesダッシュボード

10. **Export & Reproducibility** (エクスポート&再現性)
    - GraphML/JSON/DOT形式エクスポート
    - curl再現スクリプト生成
    - Python再現スクリプト生成
    - 包括的PDFレポート
    - 完全な監査証跡

---

## 📁 ファイル構成

### Backend

```
backend/
├── engine/
│   └── router_dag_comprehensive.py  # 10モジュールAPIエンドポイント
└── gateway/
    └── app.py                       # ルーター登録＆artifacts静的公開
```

### Frontend

```
frontend/src/
├── ui/
│   ├── DAGComprehensivePage.tsx     # 10モジュール統合UI
│   └── App.tsx                      # メインページ（リンク追加済み）
└── main.tsx                         # ルーティング設定
```

### Wolfram Scripts

```
scripts/wolfram/dag/
├── 01_interactive_dag.wl            # Module 1
├── 02_identifiability.wl            # Module 2
├── 03_do_operator.wl                # Module 3
├── 04_path_bias_explorer.wl         # Module 4
├── 05_iv_tester.wl                  # Module 5
├── 06_cate_heterogeneity.wl         # Module 6
├── 07_timeseries_dag.wl             # Module 7
├── 08_network_spillover.wl          # Module 8
├── 09_data_audit.wl                 # Module 9
├── 10_export_reproducibility.wl     # Module 10
└── README.md                        # 詳細ドキュメント
```

---

## 🚀 使い方

### 1. UIからアクセス

1. ブラウザで `http://localhost:5173` を開く
2. メインページのナビゲーションバーから **「⭐ DAG包括分析 (100万円級)」** をクリック
3. Dataset ID、Treatment、Outcome、Adjustmentを入力
4. **「▶️ Run All 10 Modules」** をクリックして全モジュール実行
   - または、個別のモジュールカードをクリックして単独実行

### 2. APIから直接実行

```bash
# 全モジュール実行
curl -X POST http://localhost:8000/api/dag/run-all \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "your_dataset_id",
    "treatment": "X1",
    "outcome": "Y",
    "adjustment": ["Z"]
  }'

# 単一モジュール実行 (例: Module 2 - Identifiability)
curl -X POST http://localhost:8000/api/dag/module/2 \
  -H "Content-Type: application/json" \
  -d '{
    "dataset_id": "your_dataset_id",
    "treatment": "X1",
    "outcome": "Y"
  }'
```

### 3. デモモード (データなしで動作確認)

全てのWolframスクリプトは `--demo` フラグで合成データを自動生成します：

```bash
# Module 1 デモ実行
wolframscript -file scripts/wolfram/dag/01_interactive_dag.wl --demo

# Module 9 デモ実行
wolframscript -file scripts/wolfram/dag/09_data_audit.wl --demo
```

---

## 📊 出力例

各モジュールは以下のような出力を生成します：

### Module 1: Interactive DAG
- `interactive_dag_2d.png/svg` - 2D DAG (Layered layout)
- `interactive_dag_3d.png` - 3D DAG (Spring embedding)
- `interactive_dag_3d_turntable.gif` - 360°回転GIF
- `adjacency_matrix.png/csv` - 隣接行列
- `degree_distribution.png` - 次数分布

### Module 2: Identifiability
- `backdoor_sets.json` - 有効な調整集合リスト
- `frontdoor_sets.json` - 有効な媒介集合リスト
- `dag_backdoor_highlighted.png` - Backdoor強調表示DAG
- `identifiability_result.json` - 識別可能性結果

### Module 3: do-Operator
- `intervention_curve.png` - do(X)介入曲線
- `ate_cate_ci.png` - ATE/CATE with信頼区間
- `sensitivity_gamma.png` - Rosenbaum Γ曲線
- `intervention_results.json` - 推定結果

... (以下同様に各モジュールの出力)

---

## 🎨 UI特徴

- **10個のモジュールカード**: 各モジュールのステータス（Pending/Running/Success/Error）をリアルタイム表示
- **タブ切り替え**: 成功したモジュールの結果を即座に切り替え
- **画像プレビュー**: PNG/SVG/GIFを直接表示
- **ダウンロードリンク**: JSON/CSVファイルをワンクリックダウンロード
- **エラーハンドリング**: 失敗したモジュールのエラーメッセージ表示

---

## 🔬 技術スタック

### Backend
- **FastAPI**: RESTful API
- **subprocess**: Wolframスクリプト実行
- **Pydantic**: リクエスト/レスポンススキーマ

### Frontend
- **React**: UI フレームワーク
- **TypeScript**: 型安全
- **React Router**: ページナビゲーション

### Computation
- **Wolfram ONE**: 全10モジュールの計算・可視化エンジン
- **NetworkX**: DAG操作（Wolframスクリプト内）
- **NumPy/Pandas**: データ処理（Wolframスクリプト内）

---

## ✅ チェックリスト

### 実装完了項目
- [x] Wolframスクリプト10個完成
- [x] バックエンドAPI実装（全モジュール対応）
- [x] フロントエンド統合UI実装
- [x] ルーティング設定
- [x] artifacts静的公開
- [x] メインページからのリンク
- [x] デモモード対応（全スクリプト）

### 確認項目
- [ ] ブラウザでUIにアクセス可能
- [ ] 全モジュールが正常実行（デモモードで確認）
- [ ] 生成された画像/JSON/CSVが正常表示/ダウンロード可能

---

## 📖 参考資料

- **PDF仕様書**: `docs/DAG.pdf` (11ページ)
- **Wolframスクリプト詳細**: `scripts/wolfram/dag/README.md`
- **Pearl, J. (2009)**: Causality: Models, Reasoning, and Inference
- **Hernán, M. A., & Robins, J. M. (2020)**: Causal Inference: What If
- **DoWhy Library**: https://github.com/py-why/dowhy

---

## 💡 次のステップ

1. **Wolfram ONEライセンス取得** (現在はデモモードで動作)
2. **実データでの動作確認**
3. **パフォーマンス最適化** (大規模DAG対応)
4. **共通診断コンポーネント追加** (Γ曲線、Overlap、ATE密度の共有コンポーネント)

---

**実装完了日**: 2025-11-14
**目標**: 月額100万円のバリュー実現
**仕様書準拠**: docs/DAG.pdf 完全準拠
