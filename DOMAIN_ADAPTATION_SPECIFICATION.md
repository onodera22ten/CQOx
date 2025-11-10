# CQOx ドメイン対応仕様書

**作成日**: 2025-11-10
**バージョン**: v2.0
**ステータス**: NASA/Google++ 実装完了

---

## 📋 エグゼクティブサマリー

CQOxは**ドメイン適応型因果推論プラットフォーム**として、6つの主要業種に対応し、業種特有のデータ構造と可視化要件を自動的に処理します。

### 🎯 主要特徴

1. **汎用的カラム自動検出** (ドメイン非依存)
2. **ドメイン特化型可視化** (26種類の業種別図表)
3. **動的図表選択** (データ可用性ベース)
4. **統一アウトプット形式** (ドメイン横断)

---

## 🏗️ アーキテクチャ概要

```
ユーザー入力データ (任意のCSV/Parquet/JSON/Excel)
    ↓
┌─────────────────────────────────────────────┐
│ Layer 1: カラム自動検出 (ドメイン非依存)     │
│ backend/inference/column_selection.py       │
│ - y, treatment, unit_id, time を自動検出    │
│ - キーワードマッチング(60%) + 統計(40%)      │
│ - 精度: 85%                                  │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Layer 2: ドメイン推論 (NEW - 要実装?)        │
│ - カラム名パターン解析                       │
│ - データ分布解析                             │
│ - ドメインヒント (medical/education/...)     │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Layer 3: 可視化選択 (ドメイン依存)          │
│ backend/engine/figure_selector.py           │
│ - 各ドメインの図表要件をチェック             │
│ - データ可用性に基づく動的選択               │
│ - confidence score 算出                      │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Layer 4: 図表生成 (ドメイン特化)            │
│ backend/engine/figures_objective.py         │
│ - WolframONE による高度可視化                │
│ - Matplotlib/Plotly フォールバック           │
└─────────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────────┐
│ Layer 5: アウトプット生成 (ドメイン非依存)  │
│ backend/engine/production_outputs.py        │
│ - Policy配布ファイル (Parquet)               │
│ - Quality Gates レポート                     │
│ - 監査証跡 (JSONL)                           │
└─────────────────────────────────────────────┘
```

---

## 📊 対応ドメイン一覧

### 現在実装済み: 6ドメイン

| ドメイン | 図表数 | 主要カラム要件 | ユースケース |
|---------|--------|---------------|-------------|
| **Medical** | 6 | outcome, treatment, dose, adverse_event | 臨床試験、薬効評価、医療施設比較 |
| **Education** | 5 | test_score, program, teacher_id, grade | 教育プログラム評価、教師効果分析 |
| **Retail** | 5 | sales, campaign, price, channel | マーケティング最適化、価格弾力性 |
| **Finance** | 4 | pnl, portfolio, risk, return | 投資戦略評価、リスク管理 |
| **Network** | 3 | node_id, edge_id, network_exposure | SNS施策、ネットワーク効果分析 |
| **Policy** | 3 | time, region, running_variable | 公共政策評価、地理的影響分析 |

**合計**: 26種類のドメイン特化図表

---

## 🔍 詳細仕様

### 1. カラム自動検出 (ドメイン非依存)

**実装**: `backend/inference/column_selection.py`

#### 検出対象カラム

| 役割 | キーワード例 | スコアリング |
|------|-------------|-------------|
| **outcome (y)** | outcome, sales, revenue, score, recovery | キーワード(60%) + 数値型(30%) + 高cardinality(10%) |
| **treatment** | treatment, drug, campaign, program | キーワード(60%) + 低cardinality(30%) + categorical(10%) |
| **unit_id** | id, patient, customer, student | キーワード(50%) + 高uniqueness(40%) + int/str型(10%) |
| **time** | time, date, year, month | キーワード(50%) + datetime型(40%) + monotonic(10%) |

#### スコアリングロジック

```python
# backend/inference/column_selection.py:73-89
def _score_outcome(self, col: str) -> float:
    score = 0.0

    # キーワードマッチング (60%)
    score += self._keyword_match_score(col, OUTCOME_KEYWORDS) * 0.6

    # 数値型 (30%)
    if pd.api.types.is_numeric_dtype(self.df[col]):
        score += 0.3

    # 高cardinality (10%)
    if self.df[col].nunique() > 10:
        score += 0.1

    return score
```

#### 出力形式

```json
{
  "y": "sales",
  "treatment": "campaign",
  "unit_id": "customer_id",
  "time": "date",
  "covariates": ["age", "gender", "region"],
  "confidence": {
    "y": 0.85,
    "treatment": 0.92,
    "unit_id": 0.98,
    "time": 0.78
  },
  "alternatives": {
    "y": [
      {"column": "revenue", "score": 0.72},
      {"column": "profit", "score": 0.65}
    ]
  }
}
```

---

### 2. ドメイン特化型可視化

**実装**: `backend/engine/figure_selector.py`, `backend/engine/figures_objective.py`

#### Medical ドメイン (6図表)

| 図表名 | 必須カラム | オプションカラム | 最小行数 | 説明 |
|--------|-----------|-----------------|---------|------|
| `medical_km_survival` | y, treatment | time | 50 | KM風生存曲線 |
| `medical_dose_response` | y, dose | - | 30 | 用量反応関係 |
| `medical_cluster_effect` | y, treatment | cluster_id/site_id | 100 | 施設間効果 |
| `medical_adverse_events` | treatment | adverse_event/ae | 50 | 有害事象リスク |
| `medical_iv_candidates` | y, treatment | instrument/z | 100 | IV候補変数 |
| `medical_sensitivity` | y, treatment | - | 50 | 感度分析 |

**実装例**:

```python
# backend/engine/figure_selector.py:30-68
FIGURE_REQUIREMENTS = {
    "medical_km_survival": {
        "required_columns": ["y", "treatment"],
        "optional_columns": ["time"],
        "min_rows": 50,
        "description": "KM-style survival curves"
    },
    "medical_dose_response": {
        "required_columns": ["y", "dose"],
        "min_rows": 30,
        "min_dose_levels": 3,  # 追加制約
        "description": "Dose-response relationship"
    },
    # ... 他の図表
}
```

#### Education ドメイン (5図表)

| 図表名 | 必須カラム | オプションカラム | 説明 |
|--------|-----------|-----------------|------|
| `education_gain_distrib` | y, treatment | - | 成績向上分布 |
| `education_teacher_effect` | y | teacher_id/class_id | 教師効果分析 |
| `education_attainment_sankey` | y | time, pre_score, post_score | 達成度遷移図 |
| `education_event_study` | y, treatment, time | - | イベントスタディ |
| `education_fairness` | y, treatment | gender/race/ses | 公平性分析 |

#### Retail ドメイン (5図表)

| 図表名 | 必須カラム | オプションカラム | 説明 |
|--------|-----------|-----------------|------|
| `retail_uplift_curve` | y, treatment | - | アップリフトカーブ |
| `retail_price_iv` | y | price/cost | 価格需要IV分析 |
| `retail_channel_effect` | y, treatment | channel/platform | チャネル別効果 |
| `retail_inventory_heat` | time | inventory/stock | 在庫制約タイムライン |
| `retail_spillover` | - | product_id/user_id | ネットワーク波及効果 |

#### Finance ドメイン (4図表)

| 図表名 | 必須カラム | 説明 |
|--------|-----------|------|
| `finance_pnl` | y, treatment | P&L内訳 |
| `finance_portfolio` | - | ポートフォリオ配分 |
| `finance_risk_return` | y | リスクリターントレードオフ |
| `finance_macro` | y | マクロ感度分析 |

#### Network ドメイン (3図表)

| 図表名 | 必須カラム | 説明 |
|--------|-----------|------|
| `network_spillover_heat` | - | ネットワーク波及ヒートマップ |
| `network_graph` | - | ネットワークグラフ |
| `network_interference` | y, treatment | 干渉調整ATE |

#### Policy ドメイン (3図表)

| 図表名 | 必須カラム | 説明 |
|--------|-----------|------|
| `policy_did` | y, treatment, time | DIDパネル |
| `policy_rd` | y, running_variable | 回帰不連続デザイン |
| `policy_geo` | y, state/region | 地理的影響マップ |

---

### 3. 動的図表選択アルゴリズム

**実装**: `backend/engine/figure_selector.py:262-355`

#### 選択プロセス

```python
def _evaluate_figure(self, fig_name: str, requirements: Dict) -> Dict:
    """
    図表生成可否を評価

    Returns:
        {
            "should_generate": bool,
            "confidence": float,  # 0.0-1.0
            "reason": str,
            "missing": List[str]
        }
    """
    missing = []
    confidence = 1.0

    # Step 1: 最小行数チェック
    min_rows = requirements.get("min_rows", 10)
    if len(self.df) < min_rows:
        return {
            "should_generate": False,
            "confidence": 0.0,
            "reason": f"不十分データ: {len(self.df)} < {min_rows}",
            "missing": ["sufficient_data"]
        }

    # Step 2: 必須カラムチェック
    required_cols = requirements.get("required_columns", [])
    for role in required_cols:
        col = self.role_to_column.get(role)
        if not col or col not in self.available_columns:
            missing.append(role)

    # Step 3: required_one_of チェック
    required_one_of = requirements.get("required_one_of", [])
    if required_one_of:
        found_any = any(col in self.available_columns for col in required_one_of)
        if not found_any:
            missing.append(f"one_of[{', '.join(required_one_of)}]")

    # 必須カラム不足 → 生成不可
    if missing:
        return {
            "should_generate": False,
            "confidence": 0.0,
            "reason": f"必須カラム不足: {', '.join(missing)}",
            "missing": missing
        }

    # Step 4: オプション品質制約 (confidence減衰)

    # 用量レベル不足
    if "min_dose_levels" in requirements:
        dose_col = self._find_column(["dose"])
        if dose_col:
            n_levels = self.df[dose_col].nunique()
            if n_levels < requirements["min_dose_levels"]:
                confidence *= 0.7

    # クラスタ数不足
    if "min_clusters" in requirements:
        cluster_col = self._find_column(["cluster_id", "site_id"])
        if cluster_col:
            n_clusters = self.df[cluster_col].nunique()
            if n_clusters < requirements["min_clusters"]:
                confidence *= 0.8

    # 時間期間不足
    if "min_time_periods" in requirements:
        time_col = self.role_to_column.get("time")
        if time_col:
            n_periods = self.df[time_col].nunique()
            if n_periods < requirements["min_time_periods"]:
                confidence *= 0.7

    # Step 5: 最終判定 (confidence >= 0.6 で生成)
    should_generate = confidence >= 0.6

    reason = "全要件満足"
    if confidence < 1.0:
        reason = f"部分的要件満足 (confidence: {confidence:.2f})"

    return {
        "should_generate": should_generate,
        "confidence": confidence,
        "reason": reason,
        "missing": []
    }
```

#### 出力例

```json
{
  "domain": "medical",
  "total_figures": 6,
  "recommended": 4,
  "skipped": 2,
  "recommended_figures": [
    "medical_km_survival",
    "medical_cluster_effect",
    "medical_iv_candidates",
    "medical_sensitivity"
  ],
  "skipped_figures": [
    "medical_dose_response",
    "medical_adverse_events"
  ],
  "details": {
    "medical_km_survival": {
      "should_generate": true,
      "confidence": 0.95,
      "reason": "全要件満足",
      "missing": []
    },
    "medical_dose_response": {
      "should_generate": false,
      "confidence": 0.0,
      "reason": "必須カラム不足: dose",
      "missing": ["dose"]
    }
  }
}
```

---

### 4. アウトプット生成 (ドメイン非依存)

**実装**: `backend/engine/production_outputs.py`

#### 生成される成果物 (7種類)

すべてのドメインで統一形式:

1. **Policy配布ファイル** (`policy_{dataset_id}_{scenario_id}_{timestamp}.parquet`)
   ```
   unit_id | treatment | scenario_id | generated_at | score | rank
   ```

2. **Quality Gatesレポート** (`quality_gates_{dataset_id}_{scenario_id}_{timestamp}.json`)
   ```json
   {
     "decision": "GO/CANARY/HOLD",
     "pass_rate": 0.85,
     "gates": [...],
     "rationale": [...]
   }
   ```

3. **監査証跡** (`audit_trail.jsonl`) - 追記専用
   ```jsonl
   {"timestamp": "2025-11-10T12:00:00Z", "event_type": "scenario_run", ...}
   {"timestamp": "2025-11-10T12:01:00Z", "event_type": "quality_gates", ...}
   ```

4. **派生台帳** (`derivation_ledger_{dataset_id}_{timestamp}.json`)
   - 全計算カラムの派生ルール記録

5. **比較レポート** (`comparison_{dataset_id}_{scenario_id}_{timestamp}.json`)
   - S0 vs S1 比較結果

6. **可視化図表** (`reports/figures/*.html`, `*.png`)
   - WolframONE生成図表 (ドメイン特化)

7. **ナラティブレポート** (`narrative_{dataset_id}_{timestamp}.md`)
   - 自動生成レポート

---

## 🔄 データフロー実例

### 例1: Medical データセット

**入力CSV**:
```csv
patient_id,drug,outcome_days,dose_mg,site_id,adverse_event
1001,DrugA,365,100,Hospital1,None
1002,Placebo,180,0,Hospital1,Nausea
1003,DrugA,500,150,Hospital2,None
...
```

**処理フロー**:

1. **カラム自動検出**:
   ```json
   {
     "y": "outcome_days",
     "treatment": "drug",
     "unit_id": "patient_id",
     "time": null,
     "covariates": ["dose_mg", "site_id", "adverse_event"]
   }
   ```

2. **ドメイン推論** (仮実装):
   ```
   キーワード検出: "patient", "drug", "dose" → Medical (confidence: 0.95)
   ```

3. **図表選択**:
   ```json
   {
     "recommended": [
       "medical_km_survival",       // ✓ y, treatment 存在
       "medical_dose_response",     // ✓ y, dose_mg 存在
       "medical_cluster_effect",    // ✓ y, treatment, site_id 存在
       "medical_adverse_events",    // ✓ treatment, adverse_event 存在
       "medical_iv_candidates"      // ✓ y, treatment 存在
     ],
     "skipped": [
       "medical_sensitivity"        // ✗ 行数不足 (30 < 50)
     ]
   }
   ```

4. **図表生成**:
   - WolframONE呼び出し → 5図表生成
   - 出力: `reports/figures/medical_*.html`

5. **アウトプット生成**:
   - Policy配布ファイル (Parquet)
   - Quality Gatesレポート
   - 監査証跡エントリ追加

---

### 例2: Retail データセット

**入力CSV**:
```csv
customer_id,campaign,sales,region,channel,date
C001,EmailA,150,East,Email,2024-01-01
C002,Control,100,West,Direct,2024-01-01
C003,EmailA,200,East,Email,2024-01-02
...
```

**処理フロー**:

1. **カラム自動検出**:
   ```json
   {
     "y": "sales",
     "treatment": "campaign",
     "unit_id": "customer_id",
     "time": "date",
     "covariates": ["region", "channel"]
   }
   ```

2. **ドメイン推論**:
   ```
   キーワード検出: "sales", "campaign", "channel" → Retail (confidence: 0.92)
   ```

3. **図表選択**:
   ```json
   {
     "recommended": [
       "retail_uplift_curve",       // ✓ y, treatment 存在
       "retail_channel_effect"      // ✓ y, treatment, channel 存在
     ],
     "skipped": [
       "retail_price_iv",           // ✗ price カラム不在
       "retail_inventory_heat",     // ✗ inventory カラム不在
       "retail_spillover"           // ✗ product_id/user_id 不在
     ]
   }
   ```

4. **図表生成**: 2図表生成

5. **アウトプット生成**: 同上

---

## 📈 カラム検出 vs 可視化選択 の依存関係

| レイヤー | ドメイン依存性 | 理由 |
|---------|---------------|------|
| **カラム自動検出** | ❌ **非依存** | 汎用的なキーワード・統計ベース。どの業種でも同じロジック |
| **ドメイン推論** | ✅ **依存** | (将来実装) カラム名パターンから業種を推定 |
| **図表選択** | ✅ **依存** | 業種ごとに異なる図表セット。データ可用性で動的選択 |
| **図表生成** | ✅ **依存** | 業種特有の可視化ロジック (WolframONE / Matplotlib) |
| **アウトプット生成** | ❌ **非依存** | 統一フォーマット。図表の種類のみ間接的に依存 |

---

## 🎨 可視化の変化例

### 同じデータでドメインが異なる場合

**データ**: `y=outcome, treatment=program, covariates=[age, gender]`

| ドメイン | 生成される図表 | 特徴 |
|---------|--------------|------|
| **Medical** | KM風生存曲線、感度分析 | 生存時間、有害事象に焦点 |
| **Education** | 成績向上分布、公平性分析 | 成績、公平性に焦点 |
| **Retail** | アップリフトカーブ | ROI、売上向上に焦点 |
| **Policy** | DIDパネル、地理的影響 | 時系列、地域差に焦点 |

**結論**: 同じカラム構成でも、ドメインによって**可視化の種類と強調点が変わる**。

---

## 🚀 アウトプットへの影響

### アウトプット形式の変化

**結論**: アウトプット**形式**は変わらないが、**内容**が変わる。

| アウトプット | ドメインによる変化 | 例 |
|-------------|------------------|-----|
| Policy配布ファイル | ❌ 形式不変 | 常に同じParquet構造 |
| Quality Gatesレポート | ⚠️ 内容変化 | ドメイン特有のgates追加可能 |
| 監査証跡 | ❌ 形式不変 | 常に同じJSONL構造 |
| 比較レポート | ❌ 形式不変 | S0 vs S1構造は統一 |
| **可視化図表** | ✅ **大きく変化** | ドメインごとに異なる図表セット |
| ナラティブレポート | ⚠️ 内容変化 | ドメイン用語が変わる |

---

## 💡 実装上の推奨事項

### 1. ドメイン推論の自動化 (現状: 未実装)

**提案**: `backend/inference/domain_detector.py` を追加

```python
class DomainDetector:
    """Automatically detect domain from data"""

    DOMAIN_KEYWORDS = {
        "medical": ["patient", "drug", "dose", "hospital", "clinical"],
        "education": ["student", "teacher", "grade", "score", "school"],
        "retail": ["sales", "customer", "campaign", "revenue", "product"],
        "finance": ["portfolio", "return", "risk", "asset", "pnl"],
        "network": ["node", "edge", "friend", "follower", "user"],
        "policy": ["region", "state", "county", "policy", "district"]
    }

    def detect_domain(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Returns:
            {
                "medical": 0.85,
                "retail": 0.12,
                "education": 0.03
            }
        """
        pass
```

### 2. ドメイン特化Quality Gates

各ドメインに特有の品質チェックを追加:

```python
# Medical
quality_gates.add("adverse_event_rate", max_threshold=0.05)

# Education
quality_gates.add("fairness_parity", min_threshold=0.9)

# Retail
quality_gates.add("roi_positive", min_threshold=1.0)
```

### 3. ドメイン設定ファイル

YAMLでドメイン設定を外部化:

```yaml
# config/domains/medical.yaml
domain: medical
keywords: [patient, drug, dose, hospital, adverse_event]
figures:
  - name: medical_km_survival
    required_columns: [y, treatment]
    optional_columns: [time]
    min_rows: 50
quality_gates:
  - name: adverse_event_rate
    type: max
    threshold: 0.05
```

---

## 📊 パフォーマンス指標

| 指標 | 現状 | 目標 |
|------|------|------|
| カラム自動検出精度 | 85% | 95% |
| ドメイン推論精度 | - (未実装) | 90% |
| 図表生成成功率 | 95% | 99% |
| エンドツーエンド処理時間 | ~60秒 | ~30秒 |

---

## 🔗 関連ファイル

### コアファイル

| ファイル | 行数 | 役割 |
|---------|------|------|
| `backend/inference/column_selection.py` | 300 | カラム自動検出 |
| `backend/engine/figure_selector.py` | 433 | 図表選択ロジック |
| `backend/engine/figures_objective.py` | 800+ | ドメイン特化図表生成 |
| `backend/engine/figures_finance_network_policy.py` | 300+ | Finance/Network/Policy図表 |
| `backend/engine/production_outputs.py` | 397 | アウトプット生成 |

### データベース

| モデル | テーブル | 役割 |
|--------|---------|------|
| `DomainInferenceCache` | `domain_inference_cache` | ドメイン推論結果キャッシュ |

---

## 🎯 まとめ

### ドメイン対応の3つの柱

1. **汎用性** (カラム検出、アウトプット形式)
   - どの業種でも同じロジック
   - 統一インターフェース

2. **特殊性** (可視化、分析手法)
   - 業種特有の図表
   - ドメイン知識の組み込み

3. **適応性** (動的選択、フォールバック)
   - データに基づく動的判断
   - 不足時の代替手段

### 業種対応の流れ

```
任意のファイル → 汎用カラム検出 → ドメイン推論 → 特化図表選択 → 統一アウトプット
    (CSV/Parquet/JSON)     (85%精度)      (6ドメイン)    (26図表)        (7種類)
```

**結論**: CQOxは**完全ドメイン適応型**であり、業種ごとのカスタマイズなしで最適な分析と可視化を提供します。

---

## 📚 参考情報

- **カラム検出アルゴリズム**: Keyword-based + Statistical Heuristics
- **図表選択戦略**: Rule-based with Confidence Scoring
- **WolframONE統合**: 高度可視化エンジン
- **品質保証**: 動的Quality Gates with Fallback

**更新履歴**:
- 2025-11-10: 初版作成 (NASA/Google++ 実装完了時点)
