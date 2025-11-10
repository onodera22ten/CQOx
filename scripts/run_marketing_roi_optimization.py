"""
マーケティングROI最適化 - 統合実行スクリプト

Phase 1-4の全機能を実行:
1. 増分粗利ROI計算
2. 予算配分最適化
3. マルチタッチアトリビューション
4. LTV予測
5. マーケティングミックスモデリング
6. リアルタイムダッシュボード
7. 自動推奨アクション

実行ログと可視化を生成
"""

import sys
sys.path.append('/home/user/CQOx')

import pandas as pd
import numpy as np
import json
from datetime import datetime
from backend.marketing.roi_engine import (
    IncrementalROICalculator,
    BudgetOptimizer,
    MultiTouchAttribution,
    LTVPredictor,
    MarketingMixModeling,
    RealtimeROIDashboard
)

import warnings
warnings.filterwarnings('ignore')


class MarketingROIPipeline:
    """マーケティングROI最適化パイプライン"""

    def __init__(self, data_path: str):
        self.df = pd.read_csv(data_path)
        self.results = {}
        self.execution_log = []
        self.start_time = datetime.now()

        print("=" * 80)
        print("マーケティングROI最適化パイプライン")
        print("=" * 80)
        print(f"\n開始時刻: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"データ: {len(self.df):,}行 × {len(self.df.columns)}列\n")

    def run_phase1_roi_calculation(self):
        """Phase 1: 増分粗利ROI計算"""
        print("\n" + "=" * 80)
        print("Phase 1: 増分粗利ROI計算")
        print("=" * 80)

        roi_calc = IncrementalROICalculator()

        # チャネル別ROI計算
        print("\n[1/2] チャネル別ROI計算中...")
        channel_roi = roi_calc.calculate_channel_roi(
            self.df,
            channel_col='channel',
            treatment_col='treatment',
            outcome_col='y',
            cost_col='cost',
            gross_margin_rate=0.40  # 粗利率40%
        )

        # 結果表示
        print("\nチャネル別ROI:")
        print("-" * 80)
        for _, row in channel_roi.iterrows():
            print(f"\n{row['channel']}:")
            print(f"  増分売上: {row['incremental_revenue']:,.0f}円")
            print(f"  増分粗利: {row['incremental_gross_margin']:,.0f}円")
            print(f"  コスト: {row['total_cost']:,.0f}円")
            print(f"  純利益: {row['net_profit']:,.0f}円")
            print(f"  ROI: {row['roi']:.1f}%")
            print(f"  回収期間: {row['payback_period_months']:.1f}ヶ月")

        self.results['phase1_channel_roi'] = channel_roi

        # 全体ROI計算
        print("\n[2/2] 全体ROI計算中...")
        total_treatment_revenue = self.df[self.df['treatment'] == 1]['y'].sum()
        total_control_revenue = self.df[self.df['treatment'] == 0]['y'].sum()
        total_cost = self.df[self.df['treatment'] == 1]['cost'].sum()

        overall_roi = roi_calc.calculate_roi(
            treatment_revenue=total_treatment_revenue,
            control_revenue=total_control_revenue,
            gross_margin_rate=0.40,
            marketing_cost=total_cost
        )

        print("\n全体ROI:")
        print("-" * 80)
        print(f"  増分売上: {overall_roi['incremental_revenue']:,.0f}円")
        print(f"  増分粗利: {overall_roi['incremental_gross_margin']:,.0f}円")
        print(f"  コスト: {overall_roi['total_cost']:,.0f}円")
        print(f"  純利益: {overall_roi['net_profit']:,.0f}円")
        print(f"  ROI: {overall_roi['roi']:.1f}%")

        self.results['phase1_overall_roi'] = overall_roi

        print("\n✅ Phase 1完了")

    def run_phase1_budget_optimization(self):
        """Phase 1: 予算配分最適化"""
        print("\n" + "=" * 80)
        print("Phase 1: 予算配分最適化")
        print("=" * 80)

        optimizer = BudgetOptimizer()
        channel_roi = self.results['phase1_channel_roi']

        # チャネル情報の抽出
        channels = channel_roi['channel'].tolist()

        # 効果係数（増分売上 / コスト）
        channel_effects = {}
        gross_margin_rates = {}
        unit_costs = {}

        for _, row in channel_roi.iterrows():
            ch = row['channel']
            channel_effects[ch] = row['incremental_revenue'] / row['total_cost'] if row['total_cost'] > 0 else 0
            gross_margin_rates[ch] = 0.40  # 粗利率40%
            unit_costs[ch] = 1.0  # 単位コスト（簡略化）

        # 現在の予算配分
        current_allocation = {}
        for ch in channels:
            current_allocation[ch] = float(
                self.df[
                    (self.df['channel'] == ch) & (self.df['treatment'] == 1)
                ]['cost'].sum() / 10000  # 万円単位
            )

        total_budget = sum(current_allocation.values())

        print(f"\n現在の予算配分（総額: {total_budget:.0f}万円）:")
        print("-" * 80)
        for ch, budget in current_allocation.items():
            print(f"  {ch}: {budget:.0f}万円")

        # 最適化実行
        print("\n[1/2] 線形計画法による最適化中...")
        optimal_result = optimizer.optimize_linear(
            channels=channels,
            channel_effects=channel_effects,
            gross_margin_rates=gross_margin_rates,
            unit_costs=unit_costs,
            total_budget=total_budget
        )

        print("\n最適予算配分:")
        print("-" * 80)
        for ch, budget in optimal_result['optimal_allocation'].items():
            current = current_allocation[ch]
            diff = budget - current
            symbol = "+" if diff > 0 else ""
            print(f"  {ch}: {budget:.0f}万円 ({symbol}{diff:.0f}万円)")

        print(f"\n予想パフォーマンス:")
        print(f"  予想粗利: {optimal_result['expected_gross_margin']:,.0f}円")
        print(f"  予想コスト: {optimal_result['expected_cost']:,.0f}円")
        print(f"  予想純利益: {optimal_result['expected_net_profit']:,.0f}円")
        print(f"  予想ROI: {optimal_result['expected_roi']:.1f}%")

        # 改善率計算
        current_net_profit = self.results['phase1_overall_roi']['net_profit']
        improvement = (optimal_result['expected_net_profit'] - current_net_profit) / current_net_profit * 100

        print(f"\n💰 期待改善:")
        print(f"  純利益改善: {optimal_result['expected_net_profit'] - current_net_profit:,.0f}円 (+{improvement:.1f}%)")

        self.results['phase1_optimization'] = {
            'current_allocation': current_allocation,
            'optimal_allocation': optimal_result['optimal_allocation'],
            'expected_improvement_pct': improvement,
            'optimal_result': optimal_result
        }

        # 飽和効果モデル
        print("\n[2/2] 飽和効果モデルによる最適化中...")

        saturation_params = {}
        for ch in channels:
            saturation_params[ch] = {
                'alpha': channel_effects[ch] * total_budget * 2,  # 最大効果
                'beta': 0.1,
                'gamma': 0.7,
                'gross_margin_rate': 0.40
            }

        optimal_saturation = optimizer.optimize_with_saturation(
            channels=channels,
            saturation_params=saturation_params,
            total_budget=total_budget
        )

        if 'error' not in optimal_saturation:
            print("\n飽和効果を考慮した最適配分:")
            print("-" * 80)
            for ch, budget in optimal_saturation['optimal_allocation'].items():
                print(f"  {ch}: {budget:.0f}万円")

            self.results['phase1_saturation_optimization'] = optimal_saturation

        print("\n✅ Phase 1完了")

    def run_phase2_attribution(self):
        """Phase 2: マルチタッチアトリビューション"""
        print("\n" + "=" * 80)
        print("Phase 2: マルチタッチアトリビューション（Shapley値）")
        print("=" * 80)

        # タッチポイントデータの準備（簡易版）
        print("\n[1/1] Shapley値計算中...")

        # チャネルをバイナリ変数に変換
        channels = self.df['channel'].unique()
        for ch in channels:
            self.df[f'touch_{ch}'] = (self.df['channel'] == ch).astype(int)

        # コンバージョン定義（簡易版: 高額購入）
        self.df['converted'] = (self.df['y'] > self.df['y'].median()).astype(int)

        # Shapley値計算
        attributor = MultiTouchAttribution()
        touchpoint_cols = [f'touch_{ch}' for ch in channels]

        shapley_values = attributor.shapley_attribution(
            self.df,
            touchpoint_cols=touchpoint_cols,
            conversion_col='converted'
        )

        print("\nShapley値（貢献度）:")
        print("-" * 80)
        for tp, value in sorted(shapley_values.items(), key=lambda x: x[1], reverse=True):
            ch_name = tp.replace('touch_', '')
            print(f"  {ch_name}: {value:.1f}%")

        self.results['phase2_attribution'] = shapley_values

        print("\n✅ Phase 2完了")

    def run_phase2_ltv_prediction(self):
        """Phase 2: LTV予測"""
        print("\n" + "=" * 80)
        print("Phase 2: 顧客生涯価値（LTV）予測")
        print("=" * 80)

        print("\n[1/2] LTVモデル学習中...")

        predictor = LTVPredictor()

        # 特徴量
        feature_cols = ['age', 'income', 'previous_purchases', 'engagement_score']
        feature_cols = [col for col in feature_cols if col in self.df.columns]

        # 学習
        predictor.train(
            self.df,
            feature_cols=feature_cols,
            target_col='y'
        )

        print("\n[2/2] LTV予測中...")

        # 予測
        ltv_predictions = predictor.predict_ltv(
            self.df,
            feature_cols=feature_cols,
            time_horizon_months=36
        )

        print("\nLTV予測サマリー:")
        print("-" * 80)
        print(f"  平均LTV（3年）: {ltv_predictions['predicted_ltv'].mean():,.0f}円")
        print(f"  中央値LTV: {ltv_predictions['predicted_ltv'].median():,.0f}円")
        print(f"  最大LTV: {ltv_predictions['predicted_ltv'].max():,.0f}円")
        print(f"  平均チャーン確率: {ltv_predictions['churn_probability'].mean():.1%}")
        print(f"  平均獲得コスト閾値: {ltv_predictions['acquisition_cost_threshold'].mean():,.0f}円")

        # セグメント別LTV
        if 'customer_segment' in self.df.columns:
            print("\nセグメント別LTV:")
            print("-" * 80)
            ltv_predictions['segment'] = self.df['customer_segment'].values
            for segment in ltv_predictions['segment'].unique():
                segment_ltv = ltv_predictions[ltv_predictions['segment'] == segment]['predicted_ltv'].mean()
                print(f"  {segment}: {segment_ltv:,.0f}円")

        self.results['phase2_ltv'] = ltv_predictions

        print("\n✅ Phase 2完了")

    def run_phase3_mmm(self):
        """Phase 3: マーケティングミックスモデリング"""
        print("\n" + "=" * 80)
        print("Phase 3: マーケティングミックスモデリング（MMM）")
        print("=" * 80)

        print("\n[1/2] MMMモデル学習中...")

        # 時系列データに集約
        self.df['date'] = pd.to_datetime(self.df['date'])
        self.df['week'] = self.df['date'].dt.to_period('W')

        weekly_data = self.df.groupby('week').agg({
            'y': 'sum',
            'cost': 'sum'
        }).reset_index()

        # チャネル別支出
        channels = self.df['channel'].unique()
        for ch in channels:
            weekly_data[ch] = self.df[self.df['channel'] == ch].groupby('week')['cost'].sum().values

        # MMMモデル学習
        mmm = MarketingMixModeling()
        mmm.fit(
            weekly_data,
            channel_cols=channels.tolist(),
            outcome_col='y'
        )

        print("\nMMMモデル学習完了")
        print(f"  R²: {mmm.model.rsquared:.3f}")

        print("\n[2/2] シナリオシミュレーション中...")

        # 現在の平均支出
        current_spend = {ch: float(self.df[self.df['channel'] == ch]['cost'].mean()) for ch in channels}

        # シナリオ1: 最もROIが高いチャネルに予算を増額
        best_channel = self.results['phase1_channel_roi'].nlargest(1, 'roi')['channel'].values[0]
        proposed_spend = current_spend.copy()
        proposed_spend[best_channel] *= 1.5

        scenario_result = mmm.simulate_scenario(
            current_spend=current_spend,
            proposed_spend=proposed_spend,
            gross_margin_rate=0.40
        )

        print(f"\nシナリオ: {best_channel}の予算を50%増額")
        print("-" * 80)
        print(f"  現在の売上: {scenario_result['current_sales']:,.0f}円")
        print(f"  予想売上: {scenario_result['proposed_sales']:,.0f}円")
        print(f"  増分売上: {scenario_result['incremental_sales']:,.0f}円")
        print(f"  増分粗利: {scenario_result['incremental_gross_margin']:,.0f}円")
        print(f"  増分コスト: {scenario_result['incremental_cost']:,.0f}円")
        print(f"  増分純利益: {scenario_result['incremental_net_profit']:,.0f}円")
        print(f"  増分ROI: {scenario_result['incremental_roi']:.1f}%")

        self.results['phase3_mmm'] = {
            'model_r2': mmm.model.rsquared,
            'scenario_result': scenario_result
        }

        print("\n✅ Phase 3完了")

    def run_phase4_dashboard(self):
        """Phase 4: リアルタイムダッシュボード"""
        print("\n" + "=" * 80)
        print("Phase 4: リアルタイムダッシュボード & 自動推奨アクション")
        print("=" * 80)

        print("\n[1/1] エグゼクティブサマリー生成中...")

        dashboard = RealtimeROIDashboard()

        summary = dashboard.generate_executive_summary(
            channel_roi=self.results['phase1_channel_roi'],
            optimal_allocation=self.results['phase1_optimization']['optimal_allocation'],
            current_allocation=self.results['phase1_optimization']['current_allocation']
        )

        print("\n" + "=" * 80)
        print("📊 エグゼクティブサマリー")
        print("=" * 80)

        print(f"\n期間: {summary['period']}")

        print("\n【現在のパフォーマンス】")
        print("-" * 80)
        print(f"  総予算: {summary['current_performance']['total_budget']:.0f}万円")
        print(f"  平均ROI: {summary['current_performance']['average_roi']:.1f}%")

        print("\n【最適化提案】")
        print("-" * 80)
        print(f"  期待改善率: {summary['optimization_proposal']['expected_improvement_pct']:.1f}%")

        print("\n【🚨 アラート】")
        print("-" * 80)
        if summary['alerts']:
            for alert in summary['alerts']:
                severity_icon = "🔴" if alert['severity'] == 'critical' else "⚠️"
                print(f"  {severity_icon} {alert['message']}")
        else:
            print("  ✅ 問題なし")

        print("\n【💡 推奨アクション】")
        print("-" * 80)
        for rec in summary['recommendations']:
            print(f"  {rec}")

        self.results['phase4_dashboard'] = summary

        print("\n✅ Phase 4完了")

    def run_all(self):
        """全Phase実行"""
        try:
            self.run_phase1_roi_calculation()
            self.run_phase1_budget_optimization()
            self.run_phase2_attribution()
            self.run_phase2_ltv_prediction()
            self.run_phase3_mmm()
            self.run_phase4_dashboard()

            # 終了
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()

            print("\n" + "=" * 80)
            print("✅ 全Phase完了！")
            print("=" * 80)
            print(f"\n実行時間: {duration:.2f}秒")

            # 結果保存
            output_path = "/home/user/CQOx/data/marketing_roi_optimization_results.json"
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)

            print(f"\n📄 結果保存: {output_path}")

            return self.results

        except Exception as e:
            print(f"\n❌ エラー: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    pipeline = MarketingROIPipeline(
        data_path="/home/user/CQOx/data/marketing_campaign_10k_processed.csv"
    )

    results = pipeline.run_all()
