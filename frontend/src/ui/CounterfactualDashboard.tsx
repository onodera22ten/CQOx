import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { runScenario, listScenarios } from "../lib/client";

/**
 * CounterfactualDashboard - 反実仮想シナリオ分析
 *
 * S0 (観測データ) と S1 (反実仮想) の比較を表示
 * URL: /counterfactual-dashboard
 */

interface ScenarioResult {
  status: string;
  scenario_id: string;
  mode: string;
  ate_s0: number;
  ate_s1: number;
  delta_ate: number;
  delta_profit: number;
  quality_gates?: {
    gates: Array<{
      category: string;
      metric: string;
      threshold: string;
      s0_value: number | null;
      s1_value: number | null;
      status: string;
      reason: string;
    }>;
    overall: {
      pass_count: number;
      fail_count: number;
      warning_count: number;
      pass_rate: number;
      decision: string;
    };
    rationale: string[];
  };
  decision: string;
  warnings: string[];
  figures: Record<string, string>;
}

interface AvailableScenario {
  id: string;
  label: string;
  description: string;
  path: string;
}

export default function CounterfactualDashboard() {
  const location = useLocation();
  const initialDatasetId = (location.state as any)?.datasetId || localStorage.getItem("cqox_dataset_id") || "";

  const [datasetId, setDatasetId] = useState<string>(initialDatasetId);
  const [scenarios, setScenarios] = useState<AvailableScenario[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>("");
  const [result, setResult] = useState<ScenarioResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Save dataset ID to localStorage when it changes
  useEffect(() => {
    if (datasetId) {
      localStorage.setItem("cqox_dataset_id", datasetId);
    }
  }, [datasetId]);

  // Load available scenarios when dataset ID is entered
  useEffect(() => {
    if (datasetId) {
      listScenarios(datasetId)
        .then((data) => {
          setScenarios(data.scenarios);
          if (data.scenarios.length > 0) {
            setSelectedScenario(data.scenarios[0].id);
          }
        })
        .catch((err) => {
          console.error("Failed to load scenarios:", err);
          setError("Failed to load scenarios");
        });
    }
  }, [datasetId]);

  const handleRunScenario = async () => {
    if (!datasetId || !selectedScenario) {
      setError("Please enter dataset ID and select a scenario");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const data = await runScenario({
        dataset_id: datasetId,
        scenario: selectedScenario,
        mode: "ope",
        // Default parameters (can be made configurable later)
        coverage: 0.8,
        value_per_y: 1000,
        cost_per_treated: 50,
      });

      setResult(data as ScenarioResult);
    } catch (err: any) {
      console.error("Scenario run failed:", err);
      setError(err.response?.data?.detail || err.message || "Unknown error");
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
        <Link to="/objective-comparison" style={{
          color: "#8b5cf6",
          textDecoration: "none",
          fontWeight: 600,
          fontSize: 14,
        }}>
          Objective Comparison →
        </Link>
      </div>

      {/* Page Header */}
      <h1 style={{
        fontSize: 32,
        fontWeight: 700,
        marginBottom: 8,
        color: "#1f2937",
      }}>
        反実仮想シナリオ分析
      </h1>
      <p style={{
        fontSize: 16,
        color: "#6b7280",
        marginBottom: 32,
      }}>
        Counterfactual Scenario Analysis - S0 vs S1 Comparison
      </p>

      {/* Input Section */}
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
              onChange={(e) => setDatasetId(e.target.value)}
              placeholder="Enter dataset ID (e.g., b251ecc63c...)"
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

          {/* Scenario Selection */}
          {scenarios.length > 0 && (
            <div>
              <label style={{
                display: "block",
                fontSize: 14,
                fontWeight: 600,
                marginBottom: 8,
                color: "#374151",
              }}>
                Select Scenario
              </label>
              <select
                value={selectedScenario}
                onChange={(e) => setSelectedScenario(e.target.value)}
                style={{
                  width: "100%",
                  padding: "12px 16px",
                  border: "2px solid #e5e7eb",
                  borderRadius: 8,
                  fontSize: 14,
                }}
              >
                {scenarios.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.label} - {s.description}
                  </option>
                ))}
              </select>
            </div>
          )}

          {/* Run Button */}
          <button
            onClick={handleRunScenario}
            disabled={loading || !datasetId || !selectedScenario}
            style={{
              padding: "16px 32px",
              background: loading ? "#9ca3af" : "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              color: "white",
              border: "none",
              borderRadius: 8,
              fontSize: 16,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            }}
          >
            {loading ? "Running Scenario..." : "Run Scenario Analysis"}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div style={{
          background: "#fee2e2",
          border: "2px solid #ef4444",
          borderRadius: 12,
          padding: 16,
          marginBottom: 24,
          color: "#991b1b",
        }}>
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Results Display */}
      {result && (
        <div style={{ display: "flex", flexDirection: "column", gap: 24 }}>
          {/* S0 vs S1 Comparison Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 24 }}>
            {/* S0 Card */}
            <div style={{
              background: "linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%)",
              borderRadius: 12,
              padding: 24,
              color: "white",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            }}>
              <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
                S0 (Observation)
              </h3>
              <div style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>
                {result.ate_s0.toLocaleString('en-US', { maximumFractionDigits: 2 })}
              </div>
              <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 16 }}>
                ATE (Average Treatment Effect)
              </div>
              <div style={{
                marginTop: 16,
                padding: "8px 12px",
                background: "rgba(255,255,255,0.2)",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: 600,
              }}>
                Mode: {result.mode.toUpperCase()}
              </div>
            </div>

            {/* S1 Card */}
            <div style={{
              background: "linear-gradient(135deg, #34d399 0%, #10b981 100%)",
              borderRadius: 12,
              padding: 24,
              color: "white",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            }}>
              <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
                S1 (Counterfactual)
              </h3>
              <div style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>
                {result.ate_s1.toLocaleString('en-US', { maximumFractionDigits: 2 })}
              </div>
              <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 16 }}>
                ATE (Counterfactual Effect)
              </div>
              <div style={{
                marginTop: 16,
                padding: "8px 12px",
                background: "rgba(255,255,255,0.2)",
                borderRadius: 6,
                fontSize: 14,
                fontWeight: 600,
              }}>
                Decision: {result.decision}
              </div>
            </div>

            {/* Delta Card */}
            <div style={{
              background: "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)",
              borderRadius: 12,
              padding: 24,
              color: "white",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            }}>
              <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 16 }}>
                Δ (S1 - S0)
              </h3>
              <div style={{ fontSize: 32, fontWeight: 700, marginBottom: 8 }}>
                {result.delta_ate >= 0 ? "+" : ""}{result.delta_ate.toLocaleString('en-US', { maximumFractionDigits: 2 })}
              </div>
              <div style={{ fontSize: 14, opacity: 0.9, marginBottom: 16 }}>
                Delta ATE
              </div>
              <div style={{ fontSize: 24, fontWeight: 700, marginTop: 16 }}>
                ${result.delta_profit.toLocaleString('en-US', { maximumFractionDigits: 2 })}
              </div>
              <div style={{ fontSize: 14, opacity: 0.9 }}>
                Profit Impact
              </div>
            </div>
          </div>

          {/* Quality Gates Section */}
          {result.quality_gates && (
            <div style={{
              background: "white",
              borderRadius: 12,
              padding: 24,
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            }}>
              <h3 style={{
                fontSize: 20,
                fontWeight: 600,
                marginBottom: 16,
                color: "#1f2937",
                borderBottom: "2px solid #8b5cf6",
                paddingBottom: 8,
              }}>
                Quality Gates
              </h3>
              <div style={{
                display: "grid",
                gap: 12,
                marginBottom: 16,
              }}>
                {result.quality_gates.gates.map((gate, idx) => (
                  <div key={idx} style={{
                    padding: 12,
                    background: gate.status === "PASS" ? "#d1fae5" : "#fee2e2",
                    borderRadius: 8,
                    border: `1px solid ${gate.status === "PASS" ? "#10b981" : "#ef4444"}`,
                  }}>
                    <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                      <div style={{ fontWeight: 600, fontSize: 14 }}>{gate.metric}</div>
                      <div style={{
                        fontSize: 12,
                        fontWeight: 700,
                        color: gate.status === "PASS" ? "#059669" : "#dc2626",
                      }}>
                        {gate.status}
                      </div>
                    </div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>
                      {gate.category} | Threshold: {gate.threshold}
                    </div>
                    {gate.reason && (
                      <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 4 }}>
                        {gate.reason}
                      </div>
                    )}
                  </div>
                ))}
              </div>
              <div style={{
                padding: 16,
                background: "#f9fafb",
                borderRadius: 8,
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600, color: "#1f2937" }}>
                    Overall Decision: {result.quality_gates.overall.decision}
                  </div>
                  <div style={{ fontSize: 12, color: "#6b7280", marginTop: 4 }}>
                    Pass Rate: {(result.quality_gates.overall.pass_rate * 100).toFixed(1)}%
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Warnings */}
          {result.warnings.length > 0 && (
            <div style={{
              background: "#fef3c7",
              border: "2px solid #f59e0b",
              borderRadius: 12,
              padding: 16,
            }}>
              <strong>Warnings:</strong>
              <ul style={{ marginTop: 8, marginBottom: 0, paddingLeft: 20 }}>
                {result.warnings.map((warning, idx) => (
                  <li key={idx}>{warning}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Figures Section */}
          {result.figures && Object.keys(result.figures).length > 0 && (
            <div style={{
              background: "white",
              borderRadius: 12,
              padding: 24,
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
              marginTop: 24,
            }}>
              <h3 style={{
                fontSize: 20,
                fontWeight: 600,
                marginBottom: 16,
                color: "#1f2937",
                borderBottom: "2px solid #8b5cf6",
                paddingBottom: 8,
              }}>
                Visualization & Diagnostics
              </h3>
              <div style={{
                display: "grid",
                gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))",
                gap: 24,
              }}>
                {Object.entries(result.figures).map(([key, url]) => (
                  <div key={key} style={{
                    border: "1px solid #e5e7eb",
                    borderRadius: 8,
                    overflow: "hidden",
                    background: "#f9fafb",
                  }}>
                    <div style={{
                      padding: 12,
                      background: "#f3f4f6",
                      borderBottom: "1px solid #e5e7eb",
                      fontWeight: 600,
                      fontSize: 14,
                      color: "#374151",
                    }}>
                      {key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                    </div>
                    <div style={{ padding: 12 }}>
                      {url.endsWith('.html') ? (
                        <iframe
                          src={url}
                          style={{
                            width: "100%",
                            height: 400,
                            border: "none",
                            borderRadius: 4,
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
                            borderRadius: 4,
                          }}
                          onError={(e) => {
                            (e.target as HTMLImageElement).style.display = "none";
                            (e.target as HTMLImageElement).parentElement!.innerHTML =
                              `<div style="padding:20px;text-align:center;color:#9ca3af">Failed to load image</div>`;
                          }}
                        />
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
