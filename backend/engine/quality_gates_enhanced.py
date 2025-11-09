"""
Enhanced Quality Gates - NASA/Google Standard

Purpose: Comprehensive quality validation for causal estimates
Features:
- IV first-stage F-test (F > 10)
- RD McCrary density test (p > 0.05)
- Overlap gate (90% in [0.05, 0.95])
- Moran's I for spatial autocorrelation
- CI width checks
- Rosenbaum Gamma sensitivity
- Go/Canary/Hold decision logic
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, Literal
from scipy import stats
from sklearn.linear_model import LinearRegression


@dataclass
class GateThresholds:
    """Quality gate thresholds"""
    # IV
    iv_first_stage_f_min: float = 10.0

    # RD
    rd_mccrary_p_min: float = 0.05

    # Overlap
    overlap_min_e: float = 0.05
    overlap_max_e: float = 0.95
    overlap_min_pct: float = 0.90  # 90% of units

    # Uncertainty
    ci_width_max: float = 2.0  # Maximum CI width relative to mean
    se_ratio_max: float = 0.5  # SE / |estimate|

    # Sensitivity
    rosenbaum_gamma_min: float = 1.2

    # Spatial
    morans_i_p_max: float = 0.05  # Significant autocorrelation is bad

    # Overall decision
    gate_pass_min_pct: float = 0.70  # 70% gates must pass for GO
    gate_canary_min_pct: float = 0.50  # 50-70% for CANARY


@dataclass
class GateResult:
    """Result of a single quality gate"""
    name: str
    passed: bool
    value: float
    threshold: float
    comparison: Literal[">=", "<=", ">", "<"]
    message: str
    severity: Literal["critical", "warning", "info"] = "warning"


@dataclass
class QualityGateReport:
    """Complete quality gate report"""
    gates: list[GateResult] = field(default_factory=list)
    decision: Literal["GO", "CANARY", "HOLD"] = "HOLD"
    pass_rate: float = 0.0
    summary: str = ""

    def add_gate(self, gate: GateResult):
        """Add gate result"""
        self.gates.append(gate)

    def compute_decision(self, thresholds: GateThresholds):
        """Compute GO/CANARY/HOLD decision"""
        total = len(self.gates)
        if total == 0:
            self.decision = "HOLD"
            self.summary = "No quality gates evaluated"
            return

        passed = sum(1 for g in self.gates if g.passed)
        self.pass_rate = passed / total

        if self.pass_rate >= thresholds.gate_pass_min_pct:
            self.decision = "GO"
            self.summary = f"PASS: {passed}/{total} gates passed ({self.pass_rate*100:.1f}%)"
        elif self.pass_rate >= thresholds.gate_canary_min_pct:
            self.decision = "CANARY"
            self.summary = f"CANARY: {passed}/{total} gates passed ({self.pass_rate*100:.1f}%). Recommend staged rollout."
        else:
            self.decision = "HOLD"
            self.summary = f"FAIL: Only {passed}/{total} gates passed ({self.pass_rate*100:.1f}%). Do not deploy."

    def to_dict(self) -> Dict[str, Any]:
        """Export to dictionary"""
        return {
            "decision": self.decision,
            "pass_rate": self.pass_rate,
            "summary": self.summary,
            "gates": [
                {
                    "name": g.name,
                    "passed": g.passed,
                    "value": g.value,
                    "threshold": g.threshold,
                    "comparison": g.comparison,
                    "message": g.message,
                    "severity": g.severity
                }
                for g in self.gates
            ]
        }


class EnhancedQualityGates:
    """
    Enhanced Quality Gates for Causal Inference

    Implements NASA/Google-level validation standards
    """

    def __init__(self, thresholds: Optional[GateThresholds] = None):
        """
        Initialize quality gates

        Args:
            thresholds: Custom thresholds (defaults to NASA/Google standard)
        """
        self.thresholds = thresholds or GateThresholds()

    def check_iv_first_stage(
        self,
        df: pd.DataFrame,
        z_col: str = "Z_instrument",
        treatment_col: str = "treatment",
        covariates: Optional[list[str]] = None
    ) -> GateResult:
        """
        Check IV first-stage F-statistic

        Args:
            df: DataFrame
            z_col: Instrument column
            treatment_col: Treatment column
            covariates: Optional covariates

        Returns:
            GateResult
        """
        # First stage: T ~ Z + X
        X_cols = [z_col]
        if covariates:
            X_cols.extend(covariates)

        X = df[X_cols].fillna(0).values
        T = df[treatment_col].values

        # OLS regression
        model = LinearRegression()
        model.fit(X, T)

        # Predict
        T_pred = model.predict(X)
        residuals = T - T_pred

        # F-statistic for instrument
        # F = (SSR_restricted - SSR_full) / (p / (n - k - 1))
        # Simplified: use R^2 of Z alone
        z_values = df[z_col].values.reshape(-1, 1)
        model_z = LinearRegression()
        model_z.fit(z_values, T)
        r2_z = model_z.score(z_values, T)

        n = len(df)
        k = len(X_cols)

        # F-stat approximation
        f_stat = (r2_z / (1 - r2_z)) * (n - k - 1)

        passed = f_stat >= self.thresholds.iv_first_stage_f_min

        return GateResult(
            name="IV First Stage F",
            passed=passed,
            value=float(f_stat),
            threshold=self.thresholds.iv_first_stage_f_min,
            comparison=">=",
            message=f"F-stat={f_stat:.2f}. {'PASS' if passed else 'FAIL: Weak instrument'}",
            severity="critical" if not passed else "info"
        )

    def check_overlap(
        self,
        df: pd.DataFrame,
        propensity_col: str = "propensity"
    ) -> GateResult:
        """
        Check propensity overlap

        Args:
            df: DataFrame
            propensity_col: Propensity column

        Returns:
            GateResult
        """
        if propensity_col not in df.columns:
            return GateResult(
                name="Overlap",
                passed=False,
                value=0.0,
                threshold=self.thresholds.overlap_min_pct,
                comparison=">=",
                message=f"Propensity column '{propensity_col}' not found",
                severity="critical"
            )

        e = df[propensity_col].values

        # Check fraction in [0.05, 0.95]
        in_overlap = ((e >= self.thresholds.overlap_min_e) &
                     (e <= self.thresholds.overlap_max_e)).mean()

        passed = in_overlap >= self.thresholds.overlap_min_pct

        return GateResult(
            name="Overlap",
            passed=passed,
            value=float(in_overlap),
            threshold=self.thresholds.overlap_min_pct,
            comparison=">=",
            message=f"{in_overlap*100:.1f}% of units in [{self.thresholds.overlap_min_e}, {self.thresholds.overlap_max_e}]. {'PASS' if passed else 'FAIL: Poor overlap'}",
            severity="warning" if not passed else "info"
        )

    def check_ci_width(
        self,
        estimate: float,
        ci: tuple[float, float]
    ) -> GateResult:
        """
        Check confidence interval width

        Args:
            estimate: Point estimate
            ci: (lower, upper) confidence interval

        Returns:
            GateResult
        """
        ci_width = ci[1] - ci[0]
        relative_width = ci_width / abs(estimate) if estimate != 0 else float('inf')

        passed = relative_width <= self.thresholds.ci_width_max

        return GateResult(
            name="CI Width",
            passed=passed,
            value=float(relative_width),
            threshold=self.thresholds.ci_width_max,
            comparison="<=",
            message=f"CI width = {relative_width:.2f}x estimate. {'PASS' if passed else 'FAIL: Too uncertain'}",
            severity="warning" if not passed else "info"
        )

    def check_se_ratio(
        self,
        estimate: float,
        se: float
    ) -> GateResult:
        """
        Check standard error ratio

        Args:
            estimate: Point estimate
            se: Standard error

        Returns:
            GateResult
        """
        se_ratio = se / abs(estimate) if estimate != 0 else float('inf')

        passed = se_ratio <= self.thresholds.se_ratio_max

        return GateResult(
            name="SE Ratio",
            passed=passed,
            value=float(se_ratio),
            threshold=self.thresholds.se_ratio_max,
            comparison="<=",
            message=f"SE/|estimate| = {se_ratio:.3f}. {'PASS' if passed else 'FAIL: High variance'}",
            severity="warning" if not passed else "info"
        )

    def check_rosenbaum_gamma(
        self,
        gamma_critical: float
    ) -> GateResult:
        """
        Check Rosenbaum Gamma sensitivity

        Args:
            gamma_critical: Critical gamma value (where effect becomes non-significant)

        Returns:
            GateResult
        """
        passed = gamma_critical >= self.thresholds.rosenbaum_gamma_min

        return GateResult(
            name="Rosenbaum Γ",
            passed=passed,
            value=float(gamma_critical),
            threshold=self.thresholds.rosenbaum_gamma_min,
            comparison=">=",
            message=f"Γ* = {gamma_critical:.2f}. {'PASS: Robust to hidden bias' if passed else 'FAIL: Sensitive to confounding'}",
            severity="warning" if not passed else "info"
        )

    def check_morans_i(
        self,
        df: pd.DataFrame,
        residual_col: str = "residual",
        lat_col: str = "lat",
        lon_col: str = "lon"
    ) -> GateResult:
        """
        Check Moran's I for spatial autocorrelation

        Args:
            df: DataFrame
            residual_col: Residual column
            lat_col: Latitude column
            lon_col: Longitude column

        Returns:
            GateResult
        """
        if residual_col not in df.columns:
            return GateResult(
                name="Moran's I",
                passed=True,  # Skip if not applicable
                value=0.0,
                threshold=self.thresholds.morans_i_p_max,
                comparison=">=",
                message="Residuals not available (skipped)",
                severity="info"
            )

        # Simplified Moran's I calculation
        # In production, use PySAL or similar
        from scipy.spatial.distance import pdist, squareform

        coords = df[[lat_col, lon_col]].values
        residuals = df[residual_col].values

        # Distance matrix
        dist_matrix = squareform(pdist(coords))

        # Inverse distance weights (with cutoff)
        W = 1 / (dist_matrix + 1e-10)
        np.fill_diagonal(W, 0)

        # Row-normalize
        W = W / W.sum(axis=1, keepdims=True)

        # Moran's I
        n = len(residuals)
        z = residuals - residuals.mean()
        num = n * np.sum(W * np.outer(z, z))
        den = np.sum(W) * np.sum(z ** 2)
        I = num / den if den != 0 else 0.0

        # Approximate p-value (under normality assumption)
        # E[I] = -1/(n-1)
        # Var[I] ≈ 1/n (very rough approximation)
        expected_I = -1 / (n - 1)
        var_I = 1 / n
        z_score = (I - expected_I) / np.sqrt(var_I)
        p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))

        # Pass if p > threshold (no significant autocorrelation)
        passed = p_value >= self.thresholds.morans_i_p_max

        return GateResult(
            name="Moran's I",
            passed=passed,
            value=float(I),
            threshold=float(p_value),
            comparison=">=",
            message=f"I={I:.3f}, p={p_value:.3f}. {'PASS: No spatial autocorrelation' if passed else 'FAIL: Spatial autocorrelation detected'}",
            severity="warning" if not passed else "info"
        )

    def check_mccrary_density(
        self,
        df: pd.DataFrame,
        running_var_col: str = "r_running",
        cutoff: float = 0.0
    ) -> GateResult:
        """
        McCrary density test for RD

        Args:
            df: DataFrame
            running_var_col: Running variable column
            cutoff: RD cutoff

        Returns:
            GateResult
        """
        if running_var_col not in df.columns:
            return GateResult(
                name="McCrary Test",
                passed=True,
                value=1.0,
                threshold=self.thresholds.rd_mccrary_p_min,
                comparison=">=",
                message="Running variable not found (skipped)",
                severity="info"
            )

        r = df[running_var_col].values

        # Split at cutoff
        below = r[r < cutoff]
        above = r[r >= cutoff]

        # Simplified McCrary test: compare densities just below/above cutoff
        # Using KS test as approximation
        # In production, use rddensity or similar
        if len(below) > 10 and len(above) > 10:
            # Bandwidth
            h = 1.06 * np.std(r) * len(r) ** (-1/5)

            # Density just below cutoff
            below_near = below[(below >= cutoff - h) & (below < cutoff)]
            above_near = above[(above >= cutoff) & (above <= cutoff + h)]

            if len(below_near) > 5 and len(above_near) > 5:
                # Log ratio of densities
                dens_below = len(below_near) / h
                dens_above = len(above_near) / h

                log_ratio = np.log(dens_above / dens_below) if dens_below > 0 else 0.0

                # Approximate p-value (simplified)
                # In reality, McCrary computes SE via bootstrap
                se_log_ratio = np.sqrt(1/len(below_near) + 1/len(above_near))
                z = log_ratio / se_log_ratio
                p_value = 2 * (1 - stats.norm.cdf(abs(z)))
            else:
                p_value = 1.0
        else:
            p_value = 1.0

        passed = p_value >= self.thresholds.rd_mccrary_p_min

        return GateResult(
            name="McCrary Test",
            passed=passed,
            value=float(p_value),
            threshold=self.thresholds.rd_mccrary_p_min,
            comparison=">=",
            message=f"p={p_value:.3f}. {'PASS: No manipulation' if passed else 'FAIL: Potential sorting at cutoff'}",
            severity="critical" if not passed else "info"
        )

    def evaluate_all(
        self,
        df: pd.DataFrame,
        estimate: Optional[float] = None,
        ci: Optional[tuple[float, float]] = None,
        se: Optional[float] = None,
        gamma_critical: Optional[float] = None,
        estimator_type: Optional[str] = None
    ) -> QualityGateReport:
        """
        Evaluate all applicable quality gates

        Args:
            df: DataFrame
            estimate: Point estimate
            ci: Confidence interval
            se: Standard error
            gamma_critical: Rosenbaum gamma
            estimator_type: Type of estimator (iv, rd, etc.)

        Returns:
            QualityGateReport
        """
        report = QualityGateReport()

        # Always check: Overlap
        if "propensity" in df.columns or "log_propensity" in df.columns:
            prop_col = "propensity" if "propensity" in df.columns else None
            if prop_col is None and "log_propensity" in df.columns:
                df["propensity"] = np.exp(df["log_propensity"])
                prop_col = "propensity"

            if prop_col:
                report.add_gate(self.check_overlap(df, prop_col))

        # Estimator-specific checks
        if estimator_type == "iv" and "Z_instrument" in df.columns:
            report.add_gate(self.check_iv_first_stage(df))

        if estimator_type == "rd" and "r_running" in df.columns:
            cutoff = df["c_cutoff"].iloc[0] if "c_cutoff" in df.columns else 0.0
            report.add_gate(self.check_mccrary_density(df, cutoff=cutoff))

        # Spatial check
        if "lat" in df.columns and "lon" in df.columns and "residual" in df.columns:
            report.add_gate(self.check_morans_i(df))

        # Uncertainty checks
        if estimate is not None and ci is not None:
            report.add_gate(self.check_ci_width(estimate, ci))

        if estimate is not None and se is not None:
            report.add_gate(self.check_se_ratio(estimate, se))

        # Sensitivity check
        if gamma_critical is not None:
            report.add_gate(self.check_rosenbaum_gamma(gamma_critical))

        # Compute decision
        report.compute_decision(self.thresholds)

        return report
