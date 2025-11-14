import React, { useState } from "react";
import { Link } from "react-router-dom";

/**
 * MarketingROIPage - マーケティングROI最適化ページ
 *
 * ARCHITECTURE_COMPLETE.mdに基づく実装
 * Phase 1-4: Incremental ROI, Budget Optimizer, Multi-Touch Attribution, LTV Predictor
 */

export default function MarketingROIPage() {
  const [datasetId, setDatasetId] = useState<string>(
    localStorage.getItem("cqox_dataset_id") || ""
  );
  const [selectedPhase, setSelectedPhase] = useState<string>("all");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);
  const [executionId, setExecutionId] = useState<string | null>(null);
  const [failedStep, setFailedStep] = useState<string | null>(null);

  const phases = [
    { id: "all", label: "All Phases (1-4)", description: "Complete ROI optimization pipeline" },
    { id: "phase1", label: "Phase 1: Incremental ROI", description: "Incremental ROI Calculator" },
    { id: "phase2", label: "Phase 2: Budget Optimizer", description: "Budget allocation optimization" },
    { id: "phase3", label: "Phase 3: Attribution", description: "Multi-Touch Attribution" },
    { id: "phase4", label: "Phase 4: LTV & MMM", description: "LTV Predictor & Marketing Mix Modeling" },
  ];

  const handleRunROI = async () => {
    if (!datasetId) {
      setError("Please enter dataset ID");
      return;
    }

    setLoading(true);
    setError(null);
    setFailedStep(null);

    // Generate execution ID
    const execId = `roi_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setExecutionId(execId);

    try {
      const response = await fetch("/api/marketing/roi/run", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Execution-ID": execId,
        },
        body: JSON.stringify({
          dataset_id: datasetId,
          phase: selectedPhase,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);

        // 品質ゲート失敗の場合（仕様書p.11）
        if (response.status === 422 && errorData?.detail?.gates) {
          setError(JSON.stringify(errorData.detail));
          setFailedStep("quality_gates");
        } else {
          setError(`Failed to run marketing ROI: ${response.statusText}`);
          setFailedStep("api_call");
        }
        return;
      }

      const data = await response.json();
      setResult(data);
      setError(null);
      setFailedStep(null);
    } catch (err: any) {
      console.error("Marketing ROI failed:", err);
      setError(typeof err === "string" ? err : err.message || "Unknown error");
      setFailedStep("network");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 32, maxWidth: 1400, margin: "0 auto" }}>
      {/* Navigation Bar */}
      <div style={{
        marginBottom: 24,
        display: "flex",
        alignItems: "center",
        gap: 16,
        borderBottom: "2px solid #e5e7eb",
        paddingBottom: 16,
      }}>
        <Link to="/" style={{
          color: "#8b5cf6",
          textDecoration: "none",
          fontWeight: 600,
          fontSize: 14,
        }}>
          ← Back to Main
        </Link>
      </div>

      {/* Page Header */}
      <h1 style={{
        fontSize: 32,
        fontWeight: 700,
        marginBottom: 8,
        color: "#1f2937",
      }}>
        マーケティングROI最適化
      </h1>
      <p style={{
        fontSize: 16,
        color: "#6b7280",
        marginBottom: 32,
      }}>
        Marketing ROI Optimization - Phase 1-4 Complete Pipeline
      </p>

      {/* Configuration Section */}
      <div style={{
        background: "white",
        borderRadius: 12,
        padding: 24,
        marginBottom: 24,
        boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
      }}>
        <h2 style={{
          fontSize: 20,
          fontWeight: 600,
          marginBottom: 16,
          color: "#1f2937",
        }}>
          Configuration
        </h2>

        <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
          {/* Dataset ID Input */}
          <div>
            <label style={{
              display: "block",
              fontSize: 14,
              fontWeight: 600,
              marginBottom: 8,
              color: "#374151",
            }}>
              Dataset ID
            </label>
            <input
              type="text"
              value={datasetId}
              onChange={(e) => {
                setDatasetId(e.target.value);
                localStorage.setItem("cqox_dataset_id", e.target.value);
              }}
              placeholder="Enter dataset ID (marketing data)"
              style={{
                width: "100%",
                padding: "12px 16px",
                border: "2px solid #e5e7eb",
                borderRadius: 8,
                fontSize: 14,
                fontFamily: "monospace",
              }}
            />
          </div>

          {/* Info: Always runs all phases */}
          <div style={{
            padding: "12px 16px",
            background: "linear-gradient(135deg, #fef3c7 0%, #fde68a 100%)",
            borderRadius: 8,
            border: "2px solid #f59e0b",
          }}>
            <p style={{
              fontSize: 13,
              fontWeight: 600,
              color: "#92400e",
              margin: 0,
            }}>
              ℹ️ All 4 phases will be executed simultaneously to provide complete ROI optimization results
            </p>
          </div>

          {/* Hidden Phase Selection (always "all") */}
          <div style={{ display: "none" }}>
            <select
              value={selectedPhase}
              onChange={(e) => setSelectedPhase(e.target.value)}
            >
              {phases.map((phase) => (
                <option key={phase.id} value={phase.id}>
                  {phase.label} - {phase.description}
                </option>
              ))}
            </select>
          </div>

          {/* Run Button */}
          <button
            onClick={handleRunROI}
            disabled={loading || !datasetId}
            style={{
              padding: "16px 32px",
              background: loading ? "#9ca3af" : "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
              color: "white",
              border: "none",
              borderRadius: 8,
              fontSize: 16,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            }}
          >
            {loading ? "Running ROI Analysis..." : "Run Marketing ROI Optimization"}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (() => {
        // 品質ゲート失敗の詳細表示（仕様書p.11）
        let gateError = null;
        try {
          gateError = JSON.parse(error);
        } catch {
          // Not a quality gate error
        }

        if (gateError?.gates) {
          return (
            <div style={{
              background: "#fef2f2",
              border: "3px solid #dc2626",
              borderRadius: 12,
              padding: 20,
              marginBottom: 24,
            }}>
              {/* Error Header with Execution ID */}
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: 12 }}>
                <div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: "#991b1b", marginBottom: 4 }}>
                    🚫 Quality Gates Failed
                  </div>
                  <div style={{ fontSize: 12, color: "#7f1d1d", fontFamily: "monospace" }}>
                    Execution ID: {executionId}
                  </div>
                  <div style={{ fontSize: 12, color: "#7f1d1d", fontFamily: "monospace" }}>
                    Failed Step: {failedStep}
                  </div>
                </div>
                {/* Action Buttons */}
                <div style={{ display: "flex", gap: 8 }}>
                  <button
                    onClick={handleRunROI}
                    style={{
                      padding: "8px 16px",
                      background: "#dc2626",
                      color: "white",
                      border: "none",
                      borderRadius: 6,
                      fontSize: 13,
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    🔄 Retry
                  </button>
                  <button
                    onClick={() => window.open(`/logs/${executionId}`, '_blank')}
                    style={{
                      padding: "8px 16px",
                      background: "#6b7280",
                      color: "white",
                      border: "none",
                      borderRadius: 6,
                      fontSize: 13,
                      fontWeight: 600,
                      cursor: "pointer",
                    }}
                  >
                    📋 View Logs
                  </button>
                </div>
              </div>

              <div style={{ fontSize: 14, color: "#7f1d1d", marginBottom: 16 }}>
                {gateError.message}
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                {gateError.gates.map((gate: string, idx: number) => {
                  const report = gateError.report?.[gate];
                  return (
                    <div key={idx} style={{
                      background: "white",
                      border: "1px solid #fca5a5",
                      borderRadius: 8,
                      padding: 16,
                    }}>
                      <div style={{ fontSize: 14, fontWeight: 600, color: "#dc2626", marginBottom: 8 }}>
                        ❌ {gate}
                      </div>
                      {report && (
                        <>
                          <div style={{ fontSize: 13, color: "#7f1d1d", marginBottom: 8 }}>
                            <strong>Issue:</strong> {report.description}
                          </div>
                          <div style={{
                            background: "#fef3c7",
                            border: "1px solid #f59e0b",
                            borderRadius: 6,
                            padding: 12,
                          }}>
                            <div style={{ fontSize: 12, fontWeight: 600, color: "#92400e", marginBottom: 6 }}>
                              💡 Remediation
                            </div>
                            <div style={{ fontSize: 12, color: "#78350f" }}>
                              {report.action}
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        }

        // 通常のエラー表示（可視化.pdf p.9準拠）
        return (
          <div style={{
            background: "#fee2e2",
            border: "2px solid #ef4444",
            borderRadius: 12,
            padding: 20,
            marginBottom: 24,
          }}>
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "start", marginBottom: 12 }}>
              <div>
                <div style={{ fontSize: 16, fontWeight: 700, color: "#991b1b", marginBottom: 8 }}>
                  ❌ Execution Failed
                </div>
                <div style={{ fontSize: 12, color: "#7f1d1d", fontFamily: "monospace", marginBottom: 4 }}>
                  Execution ID: {executionId}
                </div>
                <div style={{ fontSize: 12, color: "#7f1d1d", fontFamily: "monospace", marginBottom: 12 }}>
                  Failed Step: {failedStep || "unknown"}
                </div>
                <div style={{ fontSize: 14, color: "#7f1d1d" }}>
                  <strong>Error:</strong> {error}
                </div>
              </div>
              {/* Action Buttons */}
              <div style={{ display: "flex", gap: 8 }}>
                <button
                  onClick={handleRunROI}
                  style={{
                    padding: "8px 16px",
                    background: "#dc2626",
                    color: "white",
                    border: "none",
                    borderRadius: 6,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  🔄 Retry
                </button>
                <button
                  onClick={() => window.open(`/logs/${executionId}`, '_blank')}
                  style={{
                    padding: "8px 16px",
                    background: "#6b7280",
                    color: "white",
                    border: "none",
                    borderRadius: 6,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  📋 View Logs
                </button>
                <button
                  onClick={() => window.open('https://github.com/anthropics/claude-code/issues', '_blank')}
                  style={{
                    padding: "8px 16px",
                    background: "#3b82f6",
                    color: "white",
                    border: "none",
                    borderRadius: 6,
                    fontSize: 13,
                    fontWeight: 600,
                    cursor: "pointer",
                  }}
                >
                  🐛 Report Issue
                </button>
              </div>
            </div>
          </div>
        );
      })()}

      {/* Phase Details */}
      <div style={{
        background: "white",
        borderRadius: 12,
        padding: 24,
        marginBottom: 24,
        boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
      }}>
        <h2 style={{
          fontSize: 20,
          fontWeight: 600,
          marginBottom: 16,
          color: "#1f2937",
          borderBottom: "2px solid #f59e0b",
          paddingBottom: 8,
        }}>
          ROI Optimization Phases
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div style={{ padding: 16, background: "#fef3c7", borderRadius: 8, border: "1px solid #fbbf24" }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#92400e" }}>
              📊 Phase 1: Incremental ROI
            </h3>
            <p style={{ fontSize: 14, color: "#78350f", margin: 0 }}>
              Incremental ROI Calculator - 増分ROI計算<br />
              処置群と対照群の差分から真の効果を測定
            </p>
          </div>

          <div style={{ padding: 16, background: "#dbeafe", borderRadius: 8, border: "1px solid #3b82f6" }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#1e3a8a" }}>
              💰 Phase 2: Budget Optimizer
            </h3>
            <p style={{ fontSize: 14, color: "#1e40af", margin: 0 }}>
              Budget Allocation Optimization - 予算配分最適化<br />
              制約条件下での最適なチャネル配分
            </p>
          </div>

          <div style={{ padding: 16, background: "#d1fae5", borderRadius: 8, border: "1px solid #10b981" }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#065f46" }}>
              🎯 Phase 3: Multi-Touch Attribution
            </h3>
            <p style={{ fontSize: 14, color: "#047857", margin: 0 }}>
              Multi-Touch Attribution - マルチタッチアトリビューション<br />
              複数接点の貢献度分析（First-touch, Last-touch, Linear, etc.）
            </p>
          </div>

          <div style={{ padding: 16, background: "#fce7f3", borderRadius: 8, border: "1px solid #ec4899" }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#831843" }}>
              📈 Phase 4: LTV & MMM
            </h3>
            <p style={{ fontSize: 14, color: "#9f1239", margin: 0 }}>
              LTV Predictor & Marketing Mix Modeling<br />
              顧客生涯価値予測とマーケティングミックス最適化
            </p>
          </div>
        </div>
      </div>

      {/* Results Display */}
      {result && (
        <div style={{
          background: "white",
          borderRadius: 12,
          padding: 24,
          boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
        }}>
          <h2 style={{
            fontSize: 20,
            fontWeight: 600,
            marginBottom: 16,
            color: "#1f2937",
            borderBottom: "2px solid #f59e0b",
            paddingBottom: 8,
          }}>
            Optimization Results
          </h2>

          {/* Metrics Cards */}
          {result.metrics && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16, marginBottom: 24 }}>
              <div style={{ padding: 16, background: "#fef3c7", borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#92400e" }}>
                  ${result.metrics.total_roi?.toLocaleString() || 0}
                </div>
                <div style={{ fontSize: 14, color: "#78350f", marginTop: 4 }}>Total ROI</div>
              </div>

              <div style={{ padding: 16, background: "#dbeafe", borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#1e3a8a" }}>
                  {result.metrics.optimal_channels || 0}
                </div>
                <div style={{ fontSize: 14, color: "#1e40af", marginTop: 4 }}>Optimal Channels</div>
              </div>

              <div style={{ padding: 16, background: "#d1fae5", borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#065f46" }}>
                  {result.metrics.conversion_lift?.toFixed(1) || 0}%
                </div>
                <div style={{ fontSize: 14, color: "#047857", marginTop: 4 }}>Conversion Lift</div>
              </div>

              <div style={{ padding: 16, background: "#fce7f3", borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#831843" }}>
                  ${result.metrics.predicted_ltv?.toLocaleString() || 0}
                </div>
                <div style={{ fontSize: 14, color: "#9f1239", marginTop: 4 }}>Predicted LTV</div>
              </div>
            </div>
          )}

          {/* All 18 Visualizations - One per Row */}
          {result.visualizations && Object.keys(result.visualizations).length > 0 && (
            <div style={{
              display: "flex",
              flexDirection: "column",
              gap: 32,
            }}>
              {Object.entries(result.visualizations).sort().map(([key, url]: [string, any]) => (
                <div key={key} style={{
                  border: "2px solid #f59e0b",
                  borderRadius: 12,
                  overflow: "hidden",
                  background: "white",
                  boxShadow: "0 6px 12px rgba(0,0,0,0.1)",
                }}>
                  <div style={{
                    padding: 16,
                    background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
                    borderBottom: "2px solid #b45309",
                    fontWeight: 700,
                    fontSize: 16,
                    color: "white",
                  }}>
                    {key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div style={{ padding: 20 }}>
                    {url.endsWith('.html') ? (
                      <iframe
                        src={url}
                        style={{
                          width: "100%",
                          height: 700,
                          border: "none",
                          borderRadius: 8,
                        }}
                        title={key}
                      />
                    ) : (
                      <img
                        src={url}
                        alt={key}
                        style={{
                          width: "100%",
                          height: "auto",
                          borderRadius: 8,
                        }}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Implementation Info */}
      <div style={{
        marginTop: 24,
        padding: 16,
        background: "#fef3c7",
        border: "1px solid #fbbf24",
        borderRadius: 8,
      }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: "#92400e" }}>
          📝 Implementation Note
        </h3>
        <p style={{ fontSize: 13, color: "#78350f", margin: 0 }}>
          <strong>Backend Module:</strong> backend/marketing/roi_engine.py<br />
          <strong>Script:</strong> scripts/run_marketing_roi_optimization.py<br />
          <strong>Features:</strong> Incremental ROI, Budget Optimizer, Attribution, LTV, MMM<br />
          <strong>Status:</strong> Backend implementation complete, API integration in progress
        </p>
      </div>
    </div>
  );
}
