import React from "react";

/**
 * EstimatorBarChart - 23推定器の結果を横棒グラフで表示
 *
 * PSM, IPW, DiD, RDD, IV, DML, Causal Forest, BART, etc.
 */

interface EstimatorResult {
  name: string;
  tau_hat: number | null;
  se: number | null;
  ci_lower: number | null;
  ci_upper: number | null;
  status: string;
}

interface Props {
  results: EstimatorResult[];
}

const ESTIMATOR_LABELS: Record<string, string> = {
  "tvce": "Treatment vs Control (TVCE)",
  "ope": "Off-Policy Evaluation (OPE)",
  "hidden": "Sensitivity Analysis (Hidden Confounding)",
  "iv": "Instrumental Variables (IV/2SLS)",
  "transport": "Transportability (IPSW)",
  "proximal": "Proximal Causal Inference",
  "network": "Network Effects (Horvitz-Thompson)",
  "synthetic_control": "Synthetic Control Method",
  "causal_forest": "Causal Forest (Athey & Imbens)",
  "rd": "Regression Discontinuity (RD)",
  "did": "Difference-in-Differences (DiD)",
  "psm": "Propensity Score Matching (PSM)",
  "ipw": "Inverse Propensity Weighting (IPW)",
  "dr": "Doubly Robust (DR/AIPW)",
  "bart": "Bayesian Additive Regression Trees (BART)",
  "dml": "Double/Debiased Machine Learning (DML)",
  "grf": "Generalized Random Forest (GRF)",
  "tmle": "Targeted Maximum Likelihood (TMLE)",
  "sbw": "Stable Balancing Weights (SBW)",
  "cbps": "Covariate Balancing Propensity Score (CBPS)",
  "entropy": "Entropy Balancing",
  "genetic": "Genetic Matching",
  "mahalanobis": "Mahalanobis Distance Matching",
};

export default function EstimatorBarChart({ results }: Props) {
  if (!results || results.length === 0) {
    return null;
  }

  // Filter successful results and sort by tau_hat
  const successfulResults = results
    .filter(r => r.status === "success" && r.tau_hat !== null)
    .sort((a, b) => (b.tau_hat || 0) - (a.tau_hat || 0));

  if (successfulResults.length === 0) {
    return (
      <div style={{
        padding: 24,
        background: "#fef3c7",
        borderRadius: 12,
        border: "2px solid #fbbf24",
        textAlign: "center",
      }}>
        <p style={{ margin: 0, color: "#92400e", fontWeight: 600 }}>
          No estimators produced results. Please check your data and try again.
        </p>
      </div>
    );
  }

  // Calculate max absolute value for scale
  const maxAbsValue = Math.max(...successfulResults.map(r => Math.abs(r.tau_hat || 0)));
  const scale = maxAbsValue > 0 ? maxAbsValue : 1;

  return (
    <div style={{
      background: "white",
      borderRadius: 12,
      padding: 24,
      border: "2px solid #e5e7eb",
    }}>
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: 20,
      }}>
        <h3 style={{
          fontSize: 18,
          fontWeight: 700,
          color: "#1f2937",
          margin: 0,
        }}>
          📊 Estimation Results ({successfulResults.length} Estimators)
        </h3>
        <div style={{
          fontSize: 12,
          color: "#6b7280",
          background: "#f3f4f6",
          padding: "6px 12px",
          borderRadius: 6,
        }}>
          ATE ± 95% CI
        </div>
      </div>

      {/* Bar Chart */}
      <div style={{
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}>
        {successfulResults.map((result, index) => {
          const tau = result.tau_hat || 0;
          const ciLower = result.ci_lower || (tau - (result.se || 0) * 1.96);
          const ciUpper = result.ci_upper || (tau + (result.se || 0) * 1.96);
          const label = ESTIMATOR_LABELS[result.name] || result.name.toUpperCase();

          // Calculate bar position and width
          const barLeft = tau < 0 ? ((tau + scale) / (2 * scale)) * 100 : 50;
          const barWidth = (Math.abs(tau) / scale) * 50;

          // Calculate CI position
          const ciLeftPos = ((ciLower + scale) / (2 * scale)) * 100;
          const ciRightPos = ((ciUpper + scale) / (2 * scale)) * 100;
          const ciWidth = ciRightPos - ciLeftPos;

          const isPositive = tau >= 0;

          return (
            <div key={result.name} style={{
              position: "relative",
              padding: "8px 0",
              borderBottom: index < successfulResults.length - 1 ? "1px solid #e5e7eb" : "none",
            }}>
              {/* Label */}
              <div style={{
                fontSize: 12,
                fontWeight: 600,
                color: "#374151",
                marginBottom: 6,
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}>
                <span>{label}</span>
                <span style={{
                  fontSize: 13,
                  fontWeight: 700,
                  color: isPositive ? "#059669" : "#dc2626",
                }}>
                  {tau >= 0 ? "+" : ""}{tau.toFixed(3)}
                </span>
              </div>

              {/* Chart Area */}
              <div style={{
                position: "relative",
                height: 32,
                background: "#f9fafb",
                borderRadius: 6,
                overflow: "hidden",
              }}>
                {/* Zero line */}
                <div style={{
                  position: "absolute",
                  left: "50%",
                  top: 0,
                  bottom: 0,
                  width: 2,
                  background: "#9ca3af",
                  zIndex: 1,
                }} />

                {/* Confidence Interval */}
                <div style={{
                  position: "absolute",
                  left: `${ciLeftPos}%`,
                  width: `${ciWidth}%`,
                  top: "50%",
                  transform: "translateY(-50%)",
                  height: 4,
                  background: isPositive ? "#a7f3d0" : "#fecaca",
                  borderRadius: 2,
                  zIndex: 2,
                }} />

                {/* Point Estimate Bar */}
                <div style={{
                  position: "absolute",
                  left: tau < 0 ? `${barLeft}%` : "50%",
                  width: `${barWidth}%`,
                  top: "50%",
                  transform: "translateY(-50%)",
                  height: 20,
                  background: isPositive
                    ? "linear-gradient(90deg, #10b981 0%, #059669 100%)"
                    : "linear-gradient(90deg, #ef4444 0%, #dc2626 100%)",
                  borderRadius: 4,
                  zIndex: 3,
                  boxShadow: "0 2px 4px rgba(0,0,0,0.15)",
                }} />

                {/* CI labels */}
                <div style={{
                  position: "absolute",
                  left: `${ciLeftPos}%`,
                  top: "100%",
                  fontSize: 10,
                  color: "#6b7280",
                  transform: "translateX(-50%)",
                  marginTop: 2,
                }}>
                  {ciLower.toFixed(2)}
                </div>
                <div style={{
                  position: "absolute",
                  left: `${ciRightPos}%`,
                  top: "100%",
                  fontSize: 10,
                  color: "#6b7280",
                  transform: "translateX(-50%)",
                  marginTop: 2,
                }}>
                  {ciUpper.toFixed(2)}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div style={{
        marginTop: 20,
        padding: 16,
        background: "#f9fafb",
        borderRadius: 8,
        fontSize: 11,
        color: "#6b7280",
        display: "flex",
        gap: 24,
        flexWrap: "wrap",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 20, height: 12, background: "linear-gradient(90deg, #10b981 0%, #059669 100%)", borderRadius: 2 }} />
          <span>Positive Effect (ATE {">"} 0)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 20, height: 12, background: "linear-gradient(90deg, #ef4444 0%, #dc2626 100%)", borderRadius: 2 }} />
          <span>Negative Effect (ATE {"<"} 0)</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 20, height: 4, background: "#a7f3d0", borderRadius: 2 }} />
          <span>95% Confidence Interval</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          <div style={{ width: 2, height: 20, background: "#9ca3af" }} />
          <span>Zero Effect Line</span>
        </div>
      </div>
    </div>
  );
}
