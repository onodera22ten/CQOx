"""
Integrated Estimators with Strict Data Contract

統合: 既存の推定器 + 新しいStrictDataContract
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

from backend.common.schema_validator import (
    StrictDataContract, EstimatorFamily, ValidationError
)
from backend.engine.service.estimators import (
    tvce, ope_ipw, iv_2sls, transport, proximal, network, hidden
)
from backend.engine.money_view import MoneyView, MoneyParams
from backend.engine.quality_gates_enhanced import EnhancedQualityGates


def _ci(tau, se):
    hw = 1.96 * se
    return (float(tau - hw), float(tau + hw))


class IntegratedEstimator:
    """
    統合推定器

    既存の推定器を新しいデータ契約と統合
    """

    def __init__(self, dataset_id: str):
        self.dataset_id = dataset_id
        self.contract = StrictDataContract(dataset_id)

    def run_all_estimators(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str],
        money_params: Optional[MoneyParams] = None
    ) -> Dict[str, Any]:
        """
        全推定器を実行

        Returns:
            推定結果、品質ゲート、金額換算
        """
        results = {}

        # 推定器リスト
        estimators = {
            "tvce": (tvce, [EstimatorFamily.DID]),
            "ope": (ope_ipw, [EstimatorFamily.OPE]),
            "iv": (iv_2sls, [EstimatorFamily.IV]),
            "transport": (transport, [EstimatorFamily.TRANSPORT]),
            "proximal": (proximal, [EstimatorFamily.PROXIMAL]),
            "network": (network, [EstimatorFamily.NETWORK]),
            "hidden": (hidden, [EstimatorFamily.BASIC]),
        }

        for name, (estimator_func, families) in estimators.items():
            try:
                # データ契約検証
                self.contract.validate(df, families, mapping)

                # 推定実行
                result = estimator_func(df, mapping)

                if result is None:
                    results[name] = {
                        "status": "skipped",
                        "reason": "insufficient_data"
                    }
                    continue

                tau, se, ci, method = result if len(result) == 4 else (*result, "")

                # 金額換算
                if money_params:
                    money_view = MoneyView(money_params)
                    money_result = money_view.ate_to_money(
                        ate=tau,
                        ate_ci=ci,
                        n_units=len(df),
                        cost=df.get(mapping.get("cost", "cost"), 0).sum()
                    )
                else:
                    money_result = None

                # 品質ゲート
                gates = EnhancedQualityGates()
                gate_report = gates.evaluate_all(
                    df,
                    estimate=tau,
                    ci=ci,
                    se=se,
                    estimator_type=name
                )

                results[name] = {
                    "status": "ok",
                    "tau": float(tau),
                    "se": float(se),
                    "ci": list(ci),
                    "method": method,
                    "money": money_result,
                    "quality_gates": gate_report.to_dict()
                }

            except ValidationError as e:
                results[name] = {
                    "status": "failed",
                    "error": e.message,
                    "missing_columns": e.missing_columns
                }
            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e)
                }

        return results

    def run_with_comparison(
        self,
        df: pd.DataFrame,
        mapping: Dict[str, str],
        scenario_df: Optional[pd.DataFrame] = None,
        money_params: Optional[MoneyParams] = None
    ) -> Dict[str, Any]:
        """
        S0/S1比較つきで実行

        Args:
            df: 観測データ (S0)
            mapping: カラムマッピング
            scenario_df: 反実仮想データ (S1、オプション)
            money_params: 金額パラメータ

        Returns:
            S0/S1の比較結果
        """
        # S0 (観測)
        s0_results = self.run_all_estimators(df, mapping, money_params)

        # S1 (反実仮想)
        if scenario_df is not None:
            s1_results = self.run_all_estimators(scenario_df, mapping, money_params)
        else:
            s1_results = None

        # 差分計算
        delta_results = {}
        if s1_results:
            for name in s0_results.keys():
                if (s0_results[name].get("status") == "ok" and
                    s1_results[name].get("status") == "ok"):

                    delta_ate = s1_results[name]["tau"] - s0_results[name]["tau"]

                    delta_money = None
                    if (s1_results[name].get("money") and
                        s0_results[name].get("money")):
                        delta_money = (
                            s1_results[name]["money"]["delta_profit"] -
                            s0_results[name]["money"]["delta_profit"]
                        )

                    delta_results[name] = {
                        "delta_ate": delta_ate,
                        "delta_money": delta_money
                    }

        return {
            "S0": s0_results,
            "S1": s1_results,
            "delta": delta_results
        }


# 便利関数

def run_comprehensive_analysis(
    dataset_id: str,
    df: pd.DataFrame,
    mapping: Dict[str, str],
    value_per_y: Optional[float] = None,
    scenario_df: Optional[pd.DataFrame] = None
) -> Dict[str, Any]:
    """
    包括的分析を実行

    Usage:
        results = run_comprehensive_analysis(
            dataset_id="demo",
            df=df,
            mapping={"y": "revenue", "treatment": "campaign", ...},
            value_per_y=1200
        )
    """
    estimator = IntegratedEstimator(dataset_id)

    money_params = MoneyParams(value_per_y=value_per_y) if value_per_y else None

    return estimator.run_with_comparison(
        df=df,
        mapping=mapping,
        scenario_df=scenario_df,
        money_params=money_params
    )
