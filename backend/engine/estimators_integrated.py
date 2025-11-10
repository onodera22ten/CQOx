"""
Integrated Estimators with Strict Data Contract

統合: 既存の推定器 + 新しいStrictDataContract
"""

from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np
import time
import sys

from backend.common.schema_validator import (
    StrictDataContract, EstimatorFamily, ValidationError
)
from backend.engine.service.estimators import (
    tvce, ope_ipw, iv_2sls, transport, proximal, network, hidden
)
from backend.engine.money_view import MoneyView, MoneyParams
from backend.engine.quality_gates_enhanced import EnhancedQualityGates


def _log(message: str, level: str = "INFO"):
    """Simple logging to stdout with color"""
    symbols = {"INFO": "✓", "WARN": "⚠", "ERROR": "✗", "RUN": "▶"}
    colors = {"INFO": "\033[92m", "WARN": "\033[93m", "ERROR": "\033[91m", "RUN": "\033[94m"}
    reset = "\033[0m"

    symbol = symbols.get(level, "•")
    color = colors.get(level, "")
    print(f"{color}{symbol} {message}{reset}", flush=True)


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
        money_params: Optional[MoneyParams] = None,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        全推定器を実行

        Returns:
            推定結果、品質ゲート、金額換算
        """
        start_time = time.time()
        results = {}

        if verbose:
            _log(f"Data loaded: {len(df):,} rows, {len(df.columns)} columns", "INFO")
            _log("Running 7 estimators...", "RUN")

        # 推定器リスト
        estimators = {
            "tvce": (tvce, [EstimatorFamily.DID], "TVCE (Double ML)"),
            "ope": (ope_ipw, [EstimatorFamily.OPE], "OPE (IPW)"),
            "iv": (iv_2sls, [EstimatorFamily.IV], "IV (2SLS)"),
            "transport": (transport, [EstimatorFamily.TRANSPORT], "Transportability"),
            "proximal": (proximal, [EstimatorFamily.PROXIMAL], "Proximal Causal"),
            "network": (network, [EstimatorFamily.NETWORK], "Network Effects"),
            "hidden": (hidden, [EstimatorFamily.BASIC], "Hidden Confounding"),
        }

        total = len(estimators)
        passed = 0

        for idx, (name, (estimator_func, families, display_name)) in enumerate(estimators.items(), 1):
            est_start = time.time()

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
                    if verbose:
                        _log(f"  [{idx}/{total}] {display_name:.<25} Skipped (insufficient data)", "WARN")
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

                gate_status = "Pass" if gate_report.overall_pass else "Fail"
                passed += 1 if gate_report.overall_pass else 0

                est_time = time.time() - est_start

                if verbose:
                    _log(
                        f"  [{idx}/{total}] {display_name:.<25} "
                        f"ATE={tau:.3f} (SE={se:.3f}, CI=[{ci[0]:.2f}, {ci[1]:.2f}]) "
                        f"{gate_status} ({est_time:.2f}s)",
                        "INFO" if gate_status == "Pass" else "WARN"
                    )

                results[name] = {
                    "status": "ok",
                    "tau": float(tau),
                    "se": float(se),
                    "ci": list(ci),
                    "method": method,
                    "money": money_result,
                    "quality_gates": gate_report.to_dict(),
                    "execution_time": est_time
                }

            except ValidationError as e:
                results[name] = {
                    "status": "failed",
                    "error": e.message,
                    "missing_columns": e.missing_columns
                }
                if verbose:
                    _log(f"  [{idx}/{total}] {display_name:.<25} Failed: {e.message}", "ERROR")

            except Exception as e:
                results[name] = {
                    "status": "error",
                    "error": str(e)
                }
                if verbose:
                    _log(f"  [{idx}/{total}] {display_name:.<25} Error: {str(e)}", "ERROR")

        total_time = time.time() - start_time

        if verbose:
            _log(f"Completed in {total_time:.2f}s", "INFO")
            _log(f"Quality Gates: {passed}/{total} passed", "INFO")

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
    scenario_df: Optional[pd.DataFrame] = None,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    包括的分析を実行

    Usage:
        results = run_comprehensive_analysis(
            dataset_id="demo",
            df=df,
            mapping={"y": "revenue", "treatment": "campaign", ...},
            value_per_y=1200,
            verbose=True  # Enable progress logging
        )

    Output with verbose=True:
        ✓ Data loaded: 5,000 rows, 25 columns
        ▶ Running 7 estimators...
          [1/7] TVCE (Double ML)........ ATE=2.450 (SE=0.320, CI=[1.82, 3.08]) Pass (0.35s)
          [2/7] OPE (IPW)............... ATE=2.510 (SE=0.350, CI=[1.82, 3.20]) Pass (0.12s)
          ...
        ✓ Completed in 0.85s
        ✓ Quality Gates: 6/7 passed
    """
    estimator = IntegratedEstimator(dataset_id)

    money_params = MoneyParams(value_per_y=value_per_y) if value_per_y else None

    if verbose:
        _log(f"Starting comprehensive analysis (dataset: {dataset_id})", "RUN")

    result = estimator.run_with_comparison(
        df=df,
        mapping=mapping,
        scenario_df=scenario_df,
        money_params=money_params
    )

    if verbose and scenario_df is not None:
        _log("S0 vs S1 comparison completed", "INFO")

    return result
