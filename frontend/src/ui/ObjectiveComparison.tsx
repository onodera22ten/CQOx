import React, { useState, useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { runScenario } from "../lib/client";
import RiskBadge, { getRiskLevel } from "../components/RiskBadge";

/**
 * ObjectiveComparison - 8パラメータスライダーによるシナリオ比較
 *
 * 反実仮想パラメータをリアルタイムで調整して結果を比較
 * URL: /objective-comparison
 */

interface ScenarioParams {
  coverage: number;
  budget_cap: number;
  policy_threshold: number;
  neighbor_boost: number;
  geo_multiplier: number;
  network_size: number;
  value_per_y: number;
  cost_per_treated: number;
}

interface ComparisonResult {
  scenario_id: string;
  ate_s0: number;
  ate_s1: number;
  delta_ate: number;
  delta_profit: number;
  decision: string;
  figures?: Record<string, string>;
  objective?: {
    name: string;
    formula: string;
    unit: string;
    weights: Record<string, number>;
    constraints?: Record<string, number>;
    digest: string;
  };
  S0?: { ATE: number; CI: [number, number]; treated: number };
  S1?: { ATE: number; CI: [number, number]; treated: number };
  delta?: { ATE: number; money?: { point: number; CI: [number, number] | null } };
}

const DEFAULT_PARAMS: ScenarioParams = {
  coverage: 0.8,
  budget_cap: 100000,
  policy_threshold: 0.5,
  neighbor_boost: 0.1,
  geo_multiplier: 1.0,
  network_size: 100,
  value_per_y: 1000,
  cost_per_treated: 50,
};

const PARAM_CONFIGS = {
  coverage: { min: 0, max: 1, step: 0.05, label: "Coverage", unit: "" },
  budget_cap: { min: 0, max: 1000000, step: 10000, label: "Budget Cap", unit: "$" },
  policy_threshold: { min: 0, max: 1, step: 0.05, label: "Policy Threshold", unit: "" },
  neighbor_boost: { min: 0, max: 1, step: 0.05, label: "Neighbor Boost", unit: "" },
  geo_multiplier: { min: 0.1, max: 5, step: 0.1, label: "Geographic Multiplier", unit: "x" },
  network_size: { min: 10, max: 1000, step: 10, label: "Network Size", unit: "" },
  value_per_y: { min: 0, max: 10000, step: 100, label: "Value per Y", unit: "$" },
  cost_per_treated: { min: 0, max: 1000, step: 10, label: "Cost per Treated", unit: "$" },
};

export default function ObjectiveComparison() {
  const location = useLocation();
  const initialDatasetId = (location.state as any)?.datasetId || localStorage.getItem("cqox_dataset_id") || "";

  const [datasetId, setDatasetId] = useState<string>(initialDatasetId);
  const [params, setParams] = useState<ScenarioParams>(DEFAULT_PARAMS);
  const [results, setResults] = useState<ComparisonResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Save dataset ID to localStorage when it changes
  useEffect(() => {
    if (datasetId) {
      localStorage.setItem("cqox_dataset_id", datasetId);
    }
  }, [datasetId]);

  const handleParamChange = (key: keyof ScenarioParams, value: number) => {
    setParams((prev) => ({ ...prev, [key]: value }));
  };

  const handleRunComparison = async () => {
    if (!datasetId) {
      setError("Please enter dataset ID");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Create custom scenario JSON from parameters
      const customScenario = {
        id: `custom_${Date.now()}`,
        label: "Custom Scenario",
        description: "User-defined parameter tuning",
        params: {
          coverage: params.coverage,
          budget_cap: params.budget_cap,
          policy_threshold: params.policy_threshold,
          neighbor_boost: params.neighbor_boost,
          geo_multiplier: params.geo_multiplier,
          network_size: params.network_size,
          value_per_y: params.value_per_y,
          cost_per_treated: params.cost_per_treated,
        }
      };

      const data = await runScenario({
        dataset_id: datasetId,
        scenario: JSON.stringify(customScenario),
        mode: "ope",
      });

      const newResult: ComparisonResult = {
        scenario_id: customScenario.id,
        ate_s0: data.S0?.ATE || data.ate_s0 || 0,
        ate_s1: data.S1?.ATE || data.ate_s1 || 0,
        delta_ate: data.delta?.ATE || data.delta_ate || 0,
        delta_profit: data.delta?.money?.point || data.delta_profit || 0,
        decision: data.decision || "UNKNOWN",
        figures: data.fig_refs || data.figures || {},
        objective: data.objective,  // 目的関数SSOT情報
        S0: data.S0,
        S1: data.S1,
        delta: data.delta,
      };

      setResults((prev) => [newResult, ...prev].slice(0, 10)); // Keep last 10 results
    } catch (err: any) {
      console.error("Comparison failed:", err);
      setError(err.response?.data?.detail || err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setParams(DEFAULT_PARAMS);
    setResults([]);
    setError(null);
  };

  return (
    <div style={{ padding: 32, maxWidth: 1600, margin: "0 auto", background: "#0b1323", minHeight: "100vh" }}>
      {/* Navigation Bar */}
      <div style={{
        marginBottom: 24,
        display: "flex",
        alignItems: "center",
        gap: 16,
        borderBottom: "2px solid #334155",
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
        color: "#e2e8f0",
      }}>
        目的関数比較 (Objective Comparison)
      </h1>
      <p style={{
        fontSize: 16,
        color: "#94a3b8",
        marginBottom: 32,
      }}>
        8-Parameter Scenario Tuning with Real-time Comparison
      </p>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 24 }}>
        {/* Left Panel: Controls */}
        <div>
          {/* Dataset Input */}
          <div style={{
            background: "white",
            borderRadius: 12,
            padding: 24,
            marginBottom: 16,
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
          }}>
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
              placeholder="Enter dataset ID (or navigate from main page)"
              readOnly={!!initialDatasetId}
              style={{
                width: "100%",
                padding: "12px 16px",
                border: "2px solid #e5e7eb",
                borderRadius: 8,
                fontSize: 14,
                fontFamily: "monospace",
                marginBottom: 16,
                backgroundColor: initialDatasetId ? "#f3f4f6" : "white",
                cursor: initialDatasetId ? "not-allowed" : "text",
              }}
            />
          </div>

          {/* Parameter Sliders */}
          <div style={{
            background: "white",
            borderRadius: 12,
            padding: 24,
            marginBottom: 16,
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
          }}>
            <h2 style={{
              fontSize: 18,
              fontWeight: 600,
              marginBottom: 16,
              color: "#1f2937",
            }}>
              Scenario Parameters
            </h2>

            {(Object.keys(params) as Array<keyof ScenarioParams>).map((key) => {
              const config = PARAM_CONFIGS[key];
              return (
                <div key={key} style={{ marginBottom: 20 }}>
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    marginBottom: 8,
                  }}>
                    <label style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: "#374151",
                    }}>
                      {config.label}
                    </label>
                    <span style={{
                      fontSize: 13,
                      fontWeight: 600,
                      color: "#8b5cf6",
                    }}>
                      {config.unit}{params[key].toLocaleString()}
                    </span>
                  </div>
                  <input
                    type="range"
                    min={config.min}
                    max={config.max}
                    step={config.step}
                    value={params[key]}
                    onChange={(e) => handleParamChange(key, parseFloat(e.target.value))}
                    style={{
                      width: "100%",
                      accentColor: "#8b5cf6",
                    }}
                  />
                  <div style={{
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 11,
                    color: "#9ca3af",
                    marginTop: 4,
                  }}>
                    <span>{config.unit}{config.min}</span>
                    <span>{config.unit}{config.max}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Action Buttons */}
          <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
            <button
              onClick={handleRunComparison}
              disabled={loading || !datasetId}
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
              {loading ? "Running..." : "Run Comparison"}
            </button>
            <button
              onClick={handleReset}
              disabled={loading}
              style={{
                padding: "12px 24px",
                background: "white",
                color: "#6b7280",
                border: "2px solid #e5e7eb",
                borderRadius: 8,
                fontSize: 14,
                fontWeight: 600,
                cursor: loading ? "not-allowed" : "pointer",
              }}
            >
              Reset to Defaults
            </button>
          </div>

          {/* Error Display */}
          {error && (
            <div style={{
              background: "#fee2e2",
              border: "2px solid #ef4444",
              borderRadius: 8,
              padding: 12,
              marginTop: 16,
              color: "#991b1b",
              fontSize: 13,
            }}>
              <strong>Error:</strong> {error}
            </div>
          )}
        </div>

        {/* Right Panel: Results */}
        <div>
          <div style={{
            background: "white",
            borderRadius: 12,
            padding: 24,
            boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            minHeight: 600,
          }}>
            <h2 style={{
              fontSize: 20,
              fontWeight: 600,
              marginBottom: 16,
              color: "#1f2937",
              borderBottom: "2px solid #8b5cf6",
              paddingBottom: 8,
            }}>
              Comparison Results
            </h2>

            {results.length === 0 ? (
              <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: 400,
                color: "#9ca3af",
                fontSize: 16,
              }}>
                No results yet. Run a comparison to see results.
              </div>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
                {results.map((result, idx) => (
                  <div key={result.scenario_id} style={{
                    background: idx === 0 ? "#f0fdf4" : "#f9fafb",
                    border: idx === 0 ? "2px solid #10b981" : "1px solid #e5e7eb",
                    borderRadius: 8,
                    padding: 16,
                  }}>
                    <div style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: 12,
                    }}>
                      <div style={{
                        fontSize: 14,
                        fontWeight: 600,
                        color: "#1f2937",
                      }}>
                        {idx === 0 ? "🔥 Latest Result" : `Result ${idx + 1}`}
                      </div>
                      <div style={{
                        fontSize: 12,
                        color: "#6b7280",
                      }}>
                        {new Date(parseInt(result.scenario_id.split("_")[1])).toLocaleTimeString()}
                      </div>
                    </div>

                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
                      {/* S0 */}
                      <div style={{
                        background: "white",
                        padding: 12,
                        borderRadius: 6,
                        border: "1px solid #e5e7eb",
                      }}>
                        <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 4 }}>
                          S0 (Observation)
                        </div>
                        <div style={{ fontSize: 20, fontWeight: 700, color: "#3b82f6" }}>
                          {result.ate_s0.toFixed(3)}
                        </div>
                        <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 4 }}>
                          Observation
                        </div>
                      </div>

                      {/* S1 */}
                      <div style={{
                        background: "white",
                        padding: 12,
                        borderRadius: 6,
                        border: "1px solid #e5e7eb",
                      }}>
                        <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 4 }}>
                          S1 (Counterfactual)
                        </div>
                        <div style={{ fontSize: 20, fontWeight: 700, color: "#10b981" }}>
                          {result.ate_s1.toLocaleString('en-US', { maximumFractionDigits: 0 })}
                        </div>
                        <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 4 }}>
                          {result.decision}
                        </div>
                      </div>

                      {/* Delta */}
                      <div style={{
                        background: "white",
                        padding: 12,
                        borderRadius: 6,
                        border: "1px solid #e5e7eb",
                      }}>
                        <div style={{ fontSize: 12, color: "#6b7280", marginBottom: 4 }}>
                          Δ (S1 - S0)
                        </div>
                        <div style={{
                          fontSize: 20,
                          fontWeight: 700,
                          color: result.delta_ate >= 0 ? "#10b981" : "#ef4444",
                        }}>
                          {result.delta_ate >= 0 ? "+" : ""}{result.delta_ate.toFixed(3)}
                        </div>
                        {result.delta_profit !== null && (
                          <div style={{ fontSize: 11, color: "#9ca3af", marginTop: 4 }}>
                            ${result.delta_profit.toFixed(2)}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* 目的関数SSOT表示（仕様書p.4-5） */}
                    {result.objective && (
                      <div style={{
                        marginTop: 12,
                        padding: 12,
                        background: "#fef3c7",
                        borderRadius: 6,
                        border: "1px solid #f59e0b",
                      }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: "#92400e", marginBottom: 6 }}>
                          📐 Objective Function (SSOT)
                        </div>
                        <div style={{ fontSize: 11, color: "#78350f", marginBottom: 4 }}>
                          <strong>Formula:</strong> <code style={{ background: "white", padding: "2px 4px", borderRadius: 3 }}>{result.objective.formula}</code>
                        </div>
                        <div style={{ fontSize: 11, color: "#78350f", marginBottom: 4 }}>
                          <strong>Unit:</strong> {result.objective.unit}
                        </div>
                        <div style={{ fontSize: 10, color: "#92400e", fontFamily: "monospace" }}>
                          Digest: {result.objective.digest}
                        </div>
                      </div>
                    )}

                    {/* 信頼区間表示（仕様書p.3） */}
                    {(result.S0 || result.S1 || result.delta) && (
                      <div style={{
                        marginTop: 12,
                        padding: 12,
                        background: "#dbeafe",
                        borderRadius: 6,
                        border: "1px solid #3b82f6",
                      }}>
                        <div style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: 6
                        }}>
                          <div style={{ fontSize: 12, fontWeight: 600, color: "#1e40af" }}>
                            📊 Confidence Intervals (95%)
                          </div>
                          {result.delta?.money?.CI && (
                            <RiskBadge
                              riskLevel={getRiskLevel(result.delta.money.CI as [number, number])}
                              size="sm"
                            />
                          )}
                        </div>
                        {result.S0?.CI && (
                          <div style={{ fontSize: 11, color: "#1e3a8a", marginBottom: 2 }}>
                            <strong>S0 CI:</strong> [{result.S0.CI[0].toFixed(3)}, {result.S0.CI[1].toFixed(3)}]
                          </div>
                        )}
                        {result.S1?.CI && (
                          <div style={{ fontSize: 11, color: "#1e3a8a", marginBottom: 2 }}>
                            <strong>S1 CI:</strong> [{result.S1.CI[0].toFixed(3)}, {result.S1.CI[1].toFixed(3)}]
                          </div>
                        )}
                        {result.delta?.money?.CI && (
                          <div style={{ fontSize: 11, color: "#1e3a8a" }}>
                            <strong>Δ Profit CI:</strong> [{result.delta.money.CI[0].toFixed(2)}, {result.delta.money.CI[1].toFixed(2)}] {result.objective?.unit || "$"}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Summary Statistics */}
            {results.length > 1 && (
              <div style={{
                marginTop: 24,
                padding: 16,
                background: "#f9fafb",
                borderRadius: 8,
                border: "1px solid #e5e7eb",
              }}>
                <h3 style={{
                  fontSize: 14,
                  fontWeight: 600,
                  marginBottom: 12,
                  color: "#1f2937",
                }}>
                  Summary Statistics ({results.length} runs)
                </h3>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                  <div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>Avg Δ ATE</div>
                    <div style={{ fontSize: 18, fontWeight: 600, color: "#1f2937" }}>
                      {(results.reduce((sum, r) => sum + r.delta_ate, 0) / results.length).toFixed(3)}
                    </div>
                  </div>
                  <div>
                    <div style={{ fontSize: 12, color: "#6b7280" }}>Avg Δ Profit</div>
                    <div style={{ fontSize: 18, fontWeight: 600, color: "#1f2937" }}>
                      ${(results.filter(r => r.delta_profit !== null)
                        .reduce((sum, r) => sum + (r.delta_profit || 0), 0) /
                        results.filter(r => r.delta_profit !== null).length || 0).toFixed(2)}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Figures Section - S0 vs S1 Side-by-Side Comparison */}
            {results.length > 0 && results[0].figures && Object.keys(results[0].figures).length > 0 && (() => {
              // Separate S0 and S1 figures
              const allFigures = results[0].figures;
              const s0Figures: Record<string, string> = {};
              const s1Figures: Record<string, string> = {};
              const otherFigures: Record<string, string> = {};

              Object.entries(allFigures).forEach(([key, url]) => {
                if (key.includes('_s0')) {
                  s0Figures[key.replace('_s0', '')] = url;
                } else if (key.includes('_s1')) {
                  s1Figures[key.replace('_s1', '')] = url;
                } else {
                  otherFigures[key] = url;
                }
              });

              return (
                <div style={{
                  marginTop: 24,
                  padding: 16,
                  background: "white",
                  borderRadius: 8,
                  border: "1px solid #e5e7eb",
                }}>
                  <h3 style={{
                    fontSize: 14,
                    fontWeight: 600,
                    marginBottom: 16,
                    color: "#1f2937",
                  }}>
                    Visualization & Diagnostics (Latest Run)
                  </h3>

                  {/* S0 vs S1 Pair-by-Pair Comparison */}
                  {Object.keys(s0Figures).length > 0 && (
                    <div style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 20,
                    }}>
                      {Object.keys(s0Figures).map((key) => (
                      <div key={key}>
                        {/* Chart Title */}
                        <h4 style={{
                          fontSize: 14,
                          fontWeight: 700,
                          marginBottom: 12,
                          color: "#1f2937",
                        }}>
                          {key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                        </h4>

                        {/* S0 vs S1 Side-by-Side */}
                        <div style={{
                          display: "grid",
                          gridTemplateColumns: "1fr 1fr",
                          gap: 16,
                        }}>
                          {/* S0 */}
                          <div style={{
                            border: "3px solid #3b82f6",
                            borderRadius: 8,
                            overflow: "hidden",
                            background: "#fafafa",
                          }}>
                            <div style={{
                              padding: 10,
                              background: "linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%)",
                              borderBottom: "3px solid #3b82f6",
                              fontWeight: 700,
                              fontSize: 12,
                              color: "#1e40af",
                              textAlign: "center",
                            }}>
                              S0 (Baseline)
                            </div>
                            <div style={{ padding: 12 }}>
                              {s0Figures[key].endsWith('.html') ? (
                                <iframe
                                  src={s0Figures[key]}
                                  style={{
                                    width: "100%",
                                    height: 400,
                                    border: "none",
                                  }}
                                  title={`s0_${key}`}
                                />
                              ) : (
                                <img
                                  src={s0Figures[key]}
                                  alt={`S0 ${key}`}
                                  style={{
                                    width: "100%",
                                    height: "auto",
                                  }}
                                />
                              )}
                            </div>
                          </div>

                          {/* S1 */}
                          <div style={{
                            border: "3px solid #ef4444",
                            borderRadius: 8,
                            overflow: "hidden",
                            background: "#fafafa",
                          }}>
                            <div style={{
                              padding: 10,
                              background: "linear-gradient(135deg, #fee2e2 0%, #fecaca 100%)",
                              borderBottom: "3px solid #ef4444",
                              fontWeight: 700,
                              fontSize: 12,
                              color: "#991b1b",
                              textAlign: "center",
                            }}>
                              S1 (Alternative)
                            </div>
                            <div style={{ padding: 12 }}>
                              {s1Figures[key] && s1Figures[key].endsWith('.html') ? (
                                <iframe
                                  src={s1Figures[key]}
                                  style={{
                                    width: "100%",
                                    height: 400,
                                    border: "none",
                                  }}
                                  title={`s1_${key}`}
                                />
                              ) : s1Figures[key] ? (
                                <img
                                  src={s1Figures[key]}
                                  alt={`S1 ${key}`}
                                  style={{
                                    width: "100%",
                                    height: "auto",
                                  }}
                                />
                              ) : (
                                <div style={{
                                  padding: 40,
                                  textAlign: "center",
                                  color: "#9ca3af",
                                }}>
                                  No S1 data available
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                  )}

                  {/* Other Figures - Display side by side as well */}
                  {Object.keys(otherFigures).length > 0 && (
                    <div style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 20,
                      marginTop: Object.keys(s0Figures).length > 0 ? 20 : 0,
                    }}>
                      {Object.entries(otherFigures).map(([key, url]) => (
                        <div key={key}>
                          {/* Chart Title */}
                          <h4 style={{
                            fontSize: 14,
                            fontWeight: 700,
                            marginBottom: 12,
                            color: "#1f2937",
                          }}>
                            {key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                          </h4>

                          {/* Display full width */}
                          <div style={{
                            border: "2px solid #8b5cf6",
                            borderRadius: 8,
                            overflow: "hidden",
                            background: "#fafafa",
                          }}>
                            <div style={{
                              padding: 12,
                              background: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
                              borderBottom: "2px solid #7c3aed",
                              fontWeight: 700,
                              fontSize: 14,
                              color: "white",
                              textAlign: "center",
                            }}>
                              Visualization
                            </div>
                            <div style={{ padding: 16 }}>
                              {url.endsWith('.html') ? (
                                <iframe
                                  src={url}
                                  style={{
                                    width: "100%",
                                    height: 500,
                                    border: "none",
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
                                  }}
                                />
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              );
            })()}
          </div>
        </div>
      </div>
    </div>
  );
}
