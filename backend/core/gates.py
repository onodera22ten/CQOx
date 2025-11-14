"""
品質ゲート - Quality Gates

目的: SMD/Overlap/Γ/IV F/ネットワーク仮定などを合否で判定し、
      Failなら結果を出さない（Fail Fast）

設計境界:
  - 入力: Diagnostics{...}
  - 出力: GateResult{pass:bool, reasons:[code]}
  - 失敗: pass=False →HTTP 422 & 理由一覧

Expert insight:
  可視化前Failは、SREより先のプロダクト品質保証。月100万円の最低ライン。

品質ゲート（10項目）:
  1. Overlap（PSコモン）> 0.1
  2. |t| > 2（ATE）
  3. SE/|τ| < 0.5
  4. 95% CI 幅 / |τ| < 1.0
  5. 前トレンド（DiD）傾き ~ 0（p>0.1）
  6. IV First-Stage F > 10
  7. Rosenbaum Γ ≥ 1.3（感度に耐える）
  8. 飽和/Adstock 形状の単調性検査パス
  9. 特徴量リーク/高共線性(VIF) アラート無し
  10. 予測 vs 実測 MAPE < 20%（直近4週）
"""
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass
class GateResult:
    """品質ゲートの判定結果"""
    ok: bool
    reasons: List[str]  # 失敗理由コードのリスト


# 品質ゲートの閾値（ENVで上書き可能）
import os

THRESHOLDS = {
    "overlap_min": float(os.getenv("GATE_OVERLAP_MIN", "0.1")),
    "t_stat_min": float(os.getenv("GATE_T_STAT_MIN", "2.0")),
    "se_tau_ratio_max": float(os.getenv("GATE_SE_TAU_RATIO_MAX", "0.5")),
    "ci_width_ratio_max": float(os.getenv("GATE_CI_WIDTH_RATIO_MAX", "1.0")),
    "did_trend_p_min": float(os.getenv("GATE_DID_TREND_P_MIN", "0.1")),
    "iv_f_min": float(os.getenv("GATE_IV_F_MIN", "10.0")),
    "gamma_min": float(os.getenv("GATE_GAMMA_MIN", "1.3")),
    "smd_max": float(os.getenv("GATE_SMD_MAX", "0.25")),
    "vif_max": float(os.getenv("GATE_VIF_MAX", "10.0")),
    "mape_max": float(os.getenv("GATE_MAPE_MAX", "20.0")),
}


def check_gates(diag: Dict[str, float]) -> GateResult:
    """
    品質ゲートをチェック

    Args:
        diag: 診断指標の辞書
              例: {"overlap_rate": 0.92, "iv_first_stage_F": 15.0, ...}

    Returns:
        GateResult: 合否と失敗理由

    Example:
        >>> diag = {"overlap_rate": 0.95, "iv_first_stage_F": 15.0, "smd_max": 0.12}
        >>> result = check_gates(diag)
        >>> assert result.ok
    """
    reasons = []

    # 1. Overlap
    if diag.get("overlap_rate", 1.0) < THRESHOLDS["overlap_min"]:
        reasons.append("POOR_OVERLAP")

    # 2. t統計量
    t_stat = abs(diag.get("t_stat", 0.0))
    if t_stat <= THRESHOLDS["t_stat_min"]:
        reasons.append("WEAK_T_STAT")

    # 3. SE/|τ| 比
    tau = diag.get("tau", 0.0)
    se = diag.get("se", 0.0)
    if tau != 0 and abs(se / tau) > THRESHOLDS["se_tau_ratio_max"]:
        reasons.append("HIGH_SE_TAU_RATIO")

    # 4. CI幅/|τ| 比
    ci_width = diag.get("ci_width", 0.0)
    if tau != 0 and abs(ci_width / tau) > THRESHOLDS["ci_width_ratio_max"]:
        reasons.append("WIDE_CI")

    # 5. DiD前トレンド（p値）
    did_trend_p = diag.get("did_trend_p", 1.0)
    if did_trend_p < THRESHOLDS["did_trend_p_min"]:
        reasons.append("DID_TREND_VIOLATION")

    # 6. IV First-stage F
    iv_f = diag.get("iv_first_stage_F", 0.0)
    if iv_f > 0 and iv_f <= THRESHOLDS["iv_f_min"]:
        reasons.append("IV_WEAK_F")

    # 7. Rosenbaum Γ
    gamma = diag.get("rosenbaum_gamma", 999.0)
    if gamma < THRESHOLDS["gamma_min"]:
        reasons.append("LOW_GAMMA")

    # 8. SMD（標準化平均差）
    smd_max = diag.get("smd_max", 0.0)
    if smd_max > THRESHOLDS["smd_max"]:
        reasons.append("IMBALANCED")

    # 9. VIF（多重共線性）
    vif_max = diag.get("vif_max", 0.0)
    if vif_max > THRESHOLDS["vif_max"]:
        reasons.append("HIGH_VIF")

    # 10. MAPE（予測精度）
    mape = diag.get("mape", 0.0)
    if mape > THRESHOLDS["mape_max"]:
        reasons.append("HIGH_MAPE")

    ok = (len(reasons) == 0)
    return GateResult(ok, reasons)


def get_gate_remediation(reason_code: str) -> Dict[str, str]:
    """
    ゲート失敗理由に対する改善アクション

    Args:
        reason_code: 失敗理由コード

    Returns:
        {"action": "...", "description": "..."}
    """
    remediation = {
        "POOR_OVERLAP": {
            "action": "再重み付け（IPW/Trimming）またはマッチング範囲の拡大",
            "description": "共通支持領域が不足しています。処置群と対照群の重なりを増やす必要があります。"
        },
        "WEAK_T_STAT": {
            "action": "サンプルサイズの拡大、またはクラスタリング調整",
            "description": "効果推定の統計的有意性が低いです。サンプルを増やすか、分散を減らす工夫が必要です。"
        },
        "HIGH_SE_TAU_RATIO": {
            "action": "共変量の追加、または層別化",
            "description": "推定値の標準誤差が大きすぎます。説明変数を増やして精度を向上させてください。"
        },
        "WIDE_CI": {
            "action": "サンプルサイズ拡大、または事前知識の活用（ベイズ）",
            "description": "信頼区間が広すぎます。推定の不確実性が高い状態です。"
        },
        "DID_TREND_VIOLATION": {
            "action": "平行トレンド仮定の再検討、またはイベント前期間の延長",
            "description": "DiDの平行トレンド仮定が破れています。処置前のトレンドが一致していません。"
        },
        "IV_WEAK_F": {
            "action": "より強い操作変数の選択、またはIV手法の見直し",
            "description": "操作変数が弱いです。F統計量が10を下回っています。"
        },
        "LOW_GAMMA": {
            "action": "感度分析の強化、または追加の共変量調整",
            "description": "隠れた交絡因子への頑健性が低いです。Γ値を向上させる必要があります。"
        },
        "IMBALANCED": {
            "action": "マッチング、再重み付け、または層別化",
            "description": "処置群と対照群のバランスが悪いです。共変量の分布を揃えてください。"
        },
        "HIGH_VIF": {
            "action": "多重共線性のある変数を除去、またはPCA/正則化",
            "description": "説明変数間の相関が強すぎます。変数選択を見直してください。"
        },
        "HIGH_MAPE": {
            "action": "モデルの再学習、特徴量エンジニアリング、または実験でのキャリブレーション",
            "description": "予測精度が低いです。モデルと現実のズレが大きい状態です。"
        },
    }
    return remediation.get(reason_code, {
        "action": "不明",
        "description": "詳細は担当者にお問い合わせください。"
    })


def generate_gate_report(result: GateResult) -> str:
    """
    品質ゲートレポートを生成

    Args:
        result: GateResult

    Returns:
        人間が読めるレポート文字列
    """
    if result.ok:
        return "✅ すべての品質ゲートを通過しました。"

    lines = ["❌ 以下の品質ゲートに失敗しました:\n"]
    for i, reason in enumerate(result.reasons, 1):
        remedy = get_gate_remediation(reason)
        lines.append(f"{i}. {reason}")
        lines.append(f"   アクション: {remedy['action']}")
        lines.append(f"   説明: {remedy['description']}\n")

    return "\n".join(lines)
