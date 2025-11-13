# マーケティングROI最適化 - 可視化詳細ドキュメント

## ⚠️ 現状の問題

**指摘：「安っぽい棒・円グラフしか出ない」**

→ **これは正しい指摘です。**

現在実装されている可視化は、**基本的な2Dチャート（棒グラフ、円グラフ、ヒストグラム）のみ**です。

---

## 📊 実装済み可視化（Pythonスクリプト）

### Phase 1: ROI計算 & 予算最適化

#### 1. チャネル別ROI比較
- **ファイル:** `scripts/visualize_marketing_roi.py` (lines 31-66)
- **タイプ:** **棒グラフ（Bar Chart）**
- **ライブラリ:** Plotly
- **出力:** `visualizations/marketing_roi/channel_roi_comparison.html`
- **内容:**
  - X軸: マーケティングチャネル（Social Media, Email, Search, Display, etc.）
  - Y軸: ROI (%)
  - カラー: ROIの値に応じたグラデーション（赤→黄→緑）
  - ゼロライン: 損益分岐点を赤い破線で表示
- **問題:**
  - ✅ 基本的なROI比較には十分
  - ❌ インタラクティブ性が低い
  - ❌ 多次元分析ができない

#### 2. 予算配分最適化（現在 vs 最適）
- **ファイル:** `scripts/visualize_marketing_roi.py` (lines 68-108)
- **タイプ:** **グループ化棒グラフ（Grouped Bar Chart）**
- **ライブラリ:** Plotly
- **出力:** `visualizations/marketing_roi/budget_optimization_comparison.html`
- **内容:**
  - X軸: マーケティングチャネル
  - Y軸: 予算（万円）
  - 2つのバー: 「現在の配分」（水色）vs 「最適配分」（オレンジ）
- **問題:**
  - ✅ 現在と最適の比較はわかりやすい
  - ❌ 最適化のプロセスが見えない
  - ❌ 制約条件や飽和効果が可視化されていない

#### 3. 予算最適化 - ROI vs Revenue
- **ファイル:** `scripts/create_marketing_roi_visualizations.py` (lines 149-183)
- **タイプ:** **棒グラフ + 折れ線グラフ（Bar + Line Chart）**
- **ライブラリ:** Plotly
- **出力:** `visualizations/marketing_roi/budget_optimization_comparison.html`
- **内容:**
  - X軸: 予算シナリオ（Current, Optimized -10%, Optimized, +10%, +20%）
  - 左Y軸: Total ROI（棒グラフ）
  - 右Y軸: Total Revenue（折れ線グラフ）
- **問題:**
  - ✅ ROIと売上のトレードオフが見える
  - ❌ 5つのシナリオしか表示されない（連続的な変化が見えない）

---

### Phase 2: アトリビューション & LTV予測

#### 4. マルチタッチアトリビューション（Shapley値）
- **ファイル:** `scripts/visualize_marketing_roi.py` (lines 159-185)
- **タイプ:** **ドーナツ円グラフ（Pie Chart with Hole）**
- **ライブラリ:** Plotly
- **出力:** `visualizations/marketing_roi/multi_touch_attribution.html`
- **内容:**
  - 各タッチポイント（touch_1, touch_2, etc.）のShapley値貢献度を%表示
  - カラー: Plotly Set3パレット
- **問題:**
  - ✅ 貢献度の割合は一目瞭然
  - ❌ **円グラフは「安っぽい」**（まさにユーザーの指摘通り）
  - ❌ タッチポイントの順序や時系列が見えない
  - ❌ カスタマージャーニーが可視化されていない

#### 5. マルチタッチアトリビューション - モデル比較
- **ファイル:** `scripts/create_marketing_roi_visualizations.py` (lines 13-37)
- **タイプ:** **グループ化棒グラフ（Grouped Bar Chart）**
- **ライブラリ:** Plotly
- **出力:** `visualizations/marketing_roi/multi_touch_attribution.html`
- **内容:**
  - X軸: マーケティングチャネル
  - Y軸: Attribution (%)
  - 4つのバー: First Touch, Last Touch, Linear, Time Decay
- **問題:**
  - ✅ モデル比較は有用
  - ❌ Shapley値が含まれていない（最も公平なアトリビューション手法）
  - ❌ 棒グラフのみで視覚的インパクトが弱い

#### 6. LTV分布（ヒストグラム + 箱ひげ図）
- **ファイル:** `scripts/visualize_marketing_roi.py` (lines 110-157)
- **タイプ:** **ヒストグラム + 箱ひげ図（Histogram + Box Plot）**
- **ライブラリ:** Plotly (Subplots)
- **出力:** `visualizations/marketing_roi/ltv_distribution.html`
- **内容:**
  - 左パネル: LTV分布ヒストグラム（50ビン）
  - 右パネル: セグメント別LTV箱ひげ図
- **問題:**
  - ✅ 分布の形状とセグメント差が見える
  - ❌ チャーン率との関係が見えない
  - ❌ 予測の不確実性（信頼区間）が表示されていない

#### 7. LTV分布 - チャネル別
- **ファイル:** `scripts/create_marketing_roi_visualizations.py` (lines 72-116)
- **タイプ:** **重ね合わせヒストグラム（Overlay Histogram）**
- **ライブラリ:** Plotly
- **出力:** `visualizations/marketing_roi/ltv_distribution.html`
- **内容:**
  - 3つのチャネル（Organic, Paid Search, Social Media）のLTV分布を重ねて表示
  - 半透明で重なりが見える
- **問題:**
  - ✅ チャネル比較が視覚的
  - ❌ 3チャネルに限定（実際は6チャネル以上）
  - ❌ サンプルデータ（ランダム生成）で実際のLTV予測結果ではない

---

### Phase 3: マーケティングミックスモデリング

#### 8. （可視化なし）
- **問題:** Phase 3の可視化が**完全に欠落**
- **期待される可視化:**
  - Adstock効果の時系列グラフ
  - チャネル別貢献度の時系列
  - シナリオシミュレーション結果
  - 最適ミックス推奨

---

### Phase 4: リアルタイムダッシュボード

#### 9. エグゼクティブダッシュボード
- **ファイル:** `scripts/visualize_marketing_roi.py` (lines 187-238)
- **タイプ:** **メトリクスカード（Metric Cards）**
- **ライブラリ:** Plotly (Shapes + Annotations)
- **出力:** `visualizations/marketing_roi/executive_dashboard.html`
- **内容:**
  - 3つのKPIカード:
    1. 総予算（万円）
    2. 平均ROI (%)
    3. 期待改善率 (%)
  - カラー: 水色、ピンク、緑
- **問題:**
  - ✅ 重要KPIが一目で見える
  - ❌ **「安っぽい」** - 静的なカードのみ
  - ❌ トレンドグラフがない
  - ❌ アラートや推奨アクションが表示されない
  - ❌ リアルタイム更新機能がない

#### 10. ROI vs Revenue 散布図
- **ファイル:** `scripts/create_marketing_roi_visualizations.py` (lines 118-147)
- **タイプ:** **散布図（Scatter Plot）**
- **ライブラリ:** Plotly
- **出力:** `visualizations/marketing_roi/roi_vs_revenue.html`
- **内容:**
  - X軸: Revenue Generated ($)
  - Y軸: ROI (Return per Dollar)
  - 色: チャネル別（Social, Email, Search, Display）
- **問題:**
  - ✅ ROIとRevenueの関係が見える
  - ❌ サンプルデータ（50点のランダム生成）
  - ❌ 実際のマーケティングデータではない

#### 11. チャネルROI比較 - バブルチャート
- **ファイル:** `scripts/create_marketing_roi_visualizations.py` (lines 39-70)
- **タイプ:** **バブルチャート（Scatter with Size）**
- **ライブラリ:** Plotly
- **出力:** `visualizations/marketing_roi/channel_roi_comparison.html`
- **内容:**
  - X軸: Marketing Spend ($)
  - Y軸: ROI (Return per Dollar)
  - バブルサイズ: Spend額
  - カラー: ROI値（Viridisカラースケール）
- **問題:**
  - ✅ 3次元情報（Spend, ROI, Channel）を表現
  - ❌ サンプルデータ（6チャネル固定値）
  - ❌ 時系列変化が見えない

---

## 🔮 高度な可視化（WolframONEのみ）

### 12. Marketing ROI 3D Surface
- **ファイル:** `backend/wolfram/marketing_roi_3d_surface.wls`
- **タイプ:** **3D曲面プロット（Plot3D）**
- **ライブラリ:** WolframONE
- **出力:** `visualizations/marketing_roi/roi_3d_surface.png`
- **内容:**
  - X軸: Channel Index（チャネル番号）
  - Y軸: Budget Multiplier（予算倍率 0.5x - 2.0x）
  - Z軸: ROI (%)
  - カラー: TemperatureMapカラーリング（赤→黄→青）
  - メッシュ: 3D格子線
  - ライティング: 3点照明
  - Break-evenプレーン: ROI=0の赤い半透明面
  - Optimal Region: ROI>0の緑の半透明面
- **特徴:**
  - ✅ **NASA/Google標準の3D可視化**
  - ✅ ROI飽和効果が視覚的に理解できる
  - ✅ 最適予算配分が3D空間で見える
  - ✅ インタラクティブ版（Manipulate）も生成
    - ビューアングル変更
    - カラースキーム切り替え
    - メッシュ密度調整
- **問題:**
  - ❌ **WolframONEが必要**（$995/年または無料評価版）
  - ❌ Pythonスクリプトだけでは実行不可
  - ❌ HTML版が生成されない（PNG/Notebook形式のみ）

---

## 📋 可視化サマリー

### 実装済み可視化の内訳

| Phase | 可視化名 | タイプ | ファイル | 評価 |
|-------|----------|--------|----------|------|
| **Phase 1** | チャネル別ROI比較 | 棒グラフ | visualize_marketing_roi.py | ⭐⭐⭐ |
| **Phase 1** | 予算配分最適化 | グループ棒グラフ | visualize_marketing_roi.py | ⭐⭐⭐ |
| **Phase 1** | 予算シナリオ比較 | 棒+線グラフ | create_marketing_roi_visualizations.py | ⭐⭐ |
| **Phase 1** | ROI vs Spend | バブルチャート | create_marketing_roi_visualizations.py | ⭐⭐ |
| **Phase 2** | マルチタッチアトリビューション | **円グラフ** | visualize_marketing_roi.py | ⭐⭐ ❌ |
| **Phase 2** | アトリビューションモデル比較 | グループ棒グラフ | create_marketing_roi_visualizations.py | ⭐⭐⭐ |
| **Phase 2** | LTV分布 | ヒストグラム+箱ひげ図 | visualize_marketing_roi.py | ⭐⭐⭐ |
| **Phase 2** | LTV分布（チャネル別） | 重ね合わせヒストグラム | create_marketing_roi_visualizations.py | ⭐⭐ |
| **Phase 2** | ROI vs Revenue | 散布図 | create_marketing_roi_visualizations.py | ⭐⭐ |
| **Phase 3** | （可視化なし） | - | - | ❌ **欠落** |
| **Phase 4** | エグゼクティブダッシュボード | メトリクスカード | visualize_marketing_roi.py | ⭐⭐ ❌ |
| **WolframONE** | Marketing ROI 3D Surface | **3D曲面** | marketing_roi_3d_surface.wls | ⭐⭐⭐⭐⭐ ✅ |

**評価基準:**
- ⭐⭐⭐⭐⭐: NASA/Google標準、インタラクティブ、多次元
- ⭐⭐⭐: 実用的、情報量十分
- ⭐⭐: 基本的、情報量が少ない
- ⭐: 「安っぽい」

---

## ❌ 欠落している可視化

### Phase 1: ROI計算 & 予算最適化

1. **予算配分最適化の詳細可視化（欠落）**
   - 線形計画法の制約条件グラフ
   - 実行可能領域（Feasible Region）の可視化
   - 目的関数の等高線図
   - 最適解への収束プロセス

2. **ROI飽和効果曲線（欠落）**
   - チャネル別の予算 vs ROI曲線
   - 限界ROI（Marginal ROI）の変化
   - 最適予算点の可視化

3. **非線形最適化の可視化（欠落）**
   - 最急降下法の収束グラフ
   - パラメータ空間の探索軌跡

### Phase 2: アトリビューション & LTV予測

4. **カスタマージャーニー可視化（欠落）**
   - サンキーダイアグラム（タッチポイント遷移）
   - コンバージョンファネル
   - タッチポイント順序の重要性

5. **Shapley値計算プロセス（欠落）**
   - 全組み合わせのShapley値計算過程
   - 公平性の証明

6. **LTV予測の可視化（欠落）**
   - 予測 vs 実測の散布図
   - 信頼区間付き時系列グラフ
   - 特徴量重要度（XGBoost）
   - 部分依存プロット（Partial Dependence）
   - SHAPによる説明可能性

7. **チャーン率分析（欠落）**
   - 生存曲線（Survival Curve）
   - リスク関数（Hazard Function）
   - コホート分析

### Phase 3: マーケティングミックスモデリング（全欠落）

8. **Adstock効果の時系列グラフ（欠落）**
   - 広告効果の減衰曲線
   - 持ち越し効果の可視化

9. **チャネル別貢献度の時系列（欠落）**
   - 各チャネルの売上貢献度の推移
   - 季節性の分解

10. **シナリオシミュレーション（欠落）**
    - What-ifシナリオ比較
    - モンテカルロシミュレーション結果

11. **最適ミックス推奨（欠落）**
    - パレートフロンティア
    - トレードオフ分析

### Phase 4: リアルタイムダッシュボード

12. **KPIトレンドグラフ（欠落）**
    - ROI、売上、コストの時系列推移
    - 移動平均とトレンドライン

13. **アラート可視化（欠落）**
    - 異常検知の閾値グラフ
    - アラートトリガーのタイムライン

14. **推奨アクション表示（欠落）**
    - AIによる推奨の優先度表示
    - アクション実行シミュレーション

15. **リアルタイム更新（欠落）**
    - WebSocket接続でのライブデータ表示
    - 自動リフレッシュ機能

---

## 🎯 結論

### 現状

**ユーザーの指摘「安っぽい棒・円グラフしか出ない」は正しい。**

実装されている可視化の**90%は基本的な2Dチャート**：
- ✅ 棒グラフ（Bar Chart）
- ✅ 円グラフ（Pie Chart） ← 「安っぽい」
- ✅ ヒストグラム（Histogram）
- ✅ 箱ひげ図（Box Plot）
- ✅ 散布図（Scatter Plot）
- ✅ メトリクスカード（静的な数値表示） ← 「安っぽい」

**高度な可視化は1つだけ：**
- ✅ Marketing ROI 3D Surface（WolframONEのみ）

### 問題点

1. **Phase 3の可視化が完全に欠落**
   - マーケティングミックスモデリングの結果が見えない

2. **Phase 4のダッシュボードが「安っぽい」**
   - 静的なメトリクスカードのみ
   - トレンドグラフ、アラート、推奨アクションがない

3. **円グラフに頼りすぎ**
   - マルチタッチアトリビューションが円グラフ
   - カスタマージャーニーが見えない

4. **インタラクティブ性が低い**
   - ほとんどが静的なPlotly HTML
   - パラメータ調整やシミュレーションができない

5. **サンプルデータが多い**
   - 一部の可視化がランダム生成データを使用
   - 実際のマーケティングデータではない

6. **WolframONE依存**
   - 唯一の高度な3D可視化がWolframONE必須
   - Pythonだけでは実行不可

---

## 🚀 推奨される改善

### 優先度1: Phase 3の可視化実装
- Adstock効果の時系列グラフ
- チャネル別貢献度の時系列
- シナリオシミュレーション

### 優先度2: ダッシュボード強化
- KPIトレンドグラフ追加
- アラート表示
- 推奨アクション表示

### 優先度3: 円グラフの置き換え
- サンキーダイアグラムでカスタマージャーニー可視化
- コンバージョンファネル追加

### 優先度4: 3D可視化のPython実装
- Plotlyで3D Surface Plot作成（WolframONE不要）
- インタラクティブな予算最適化3D可視化

---

**最終更新:** 2025-11-13
**ステータス:** 現状分析完了 - 改善案提示済み
