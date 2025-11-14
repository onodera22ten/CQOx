import React, { useState } from "react";
import { Link } from "react-router-dom";

/**
 * DAGVisualizationPage - DAG (因果グラフ) 可視化ページ
 *
 * ARCHITECTURE_COMPLETE.mdに基づく実装
 * インタラクティブDAG、ドメインネットワークDAG
 */

export default function DAGVisualizationPage() {
  const [datasetId, setDatasetId] = useState<string>(
    localStorage.getItem("cqox_dataset_id") || ""
  );
  const [dagType, setDagType] = useState<string>("interactive");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);

  const dagTypes = [
    { id: "interactive", label: "Interactive DAG", description: "インタラクティブ因果グラフ" },
    { id: "domain_network", label: "Domain Network DAG", description: "ドメイン別ネットワークDAG" },
    { id: "causal_discovery", label: "Causal Discovery", description: "因果探索アルゴリズム (PC, FCI)" },
  ];

  const handleGenerateDAG = async () => {
    if (!datasetId) {
      setError("Please enter dataset ID");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch("/api/visualizations/dag/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: datasetId,
          dag_type: dagType,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to generate DAG: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      console.error("DAG generation failed:", err);
      setError(err.message || "Unknown error");
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
        DAG因果グラフ可視化
      </h1>
      <p style={{
        fontSize: 16,
        color: "#6b7280",
        marginBottom: 32,
      }}>
        Directed Acyclic Graph (DAG) - Interactive Causal Graph Visualization
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
              placeholder="Enter dataset ID"
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

          {/* DAG Type Selection */}
          <div>
            <label style={{
              display: "block",
              fontSize: 14,
              fontWeight: 600,
              marginBottom: 8,
              color: "#374151",
            }}>
              DAG Type
            </label>
            <select
              value={dagType}
              onChange={(e) => setDagType(e.target.value)}
              style={{
                width: "100%",
                padding: "12px 16px",
                border: "2px solid #e5e7eb",
                borderRadius: 8,
                fontSize: 14,
              }}
            >
              {dagTypes.map((type) => (
                <option key={type.id} value={type.id}>
                  {type.label} - {type.description}
                </option>
              ))}
            </select>
          </div>

          {/* Run Button */}
          <button
            onClick={handleGenerateDAG}
            disabled={loading || !datasetId}
            style={{
              padding: "16px 32px",
              background: loading ? "#9ca3af" : "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              color: "white",
              border: "none",
              borderRadius: 8,
              fontSize: 16,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
            }}
          >
            {loading ? "Generating DAG..." : "Generate DAG Visualization"}
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

      {/* DAG Types Info */}
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
          borderBottom: "2px solid #10b981",
          paddingBottom: 8,
        }}>
          Available DAG Visualizations
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 16 }}>
          <div style={{ padding: 16, background: "#d1fae5", borderRadius: 8, border: "1px solid #10b981" }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#065f46" }}>
              🕸️ Interactive DAG
            </h3>
            <p style={{ fontSize: 14, color: "#047857", margin: 0 }}>
              インタラクティブDAG<br />
              ドラッグ&ドロップ、ズーム、ノード選択可能<br />
              D3.js / NetworkX実装
            </p>
          </div>

          <div style={{ padding: 16, background: "#dbeafe", borderRadius: 8, border: "1px solid #3b82f6" }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#1e3a8a" }}>
              🌐 Domain Network DAG
            </h3>
            <p style={{ fontSize: 14, color: "#1e40af", margin: 0 }}>
              ドメインネットワークDAG<br />
              教育・医療・小売など分野別<br />
              WolframONE実装
            </p>
          </div>

          <div style={{ padding: 16, background: "#fce7f3", borderRadius: 8, border: "1px solid #ec4899" }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#831843" }}>
              🔍 Causal Discovery
            </h3>
            <p style={{ fontSize: 14, color: "#9f1239", margin: 0 }}>
              因果探索アルゴリズム<br />
              PC, FCI, GES, LiNGAM<br />
              自動DAG生成
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
            borderBottom: "2px solid #10b981",
            paddingBottom: 8,
          }}>
            Generated DAG
          </h2>

          {/* DAG Statistics */}
          {result.statistics && (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16, marginBottom: 24 }}>
              <div style={{ padding: 16, background: "#d1fae5", borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#065f46" }}>
                  {result.statistics.nodes || 0}
                </div>
                <div style={{ fontSize: 14, color: "#047857", marginTop: 4 }}>Nodes</div>
              </div>

              <div style={{ padding: 16, background: "#dbeafe", borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#1e3a8a" }}>
                  {result.statistics.edges || 0}
                </div>
                <div style={{ fontSize: 14, color: "#1e40af", marginTop: 4 }}>Edges</div>
              </div>

              <div style={{ padding: 16, background: "#fce7f3", borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#831843" }}>
                  {result.statistics.layers || 0}
                </div>
                <div style={{ fontSize: 14, color: "#9f1239", marginTop: 4 }}>Layers</div>
              </div>

              <div style={{ padding: 16, background: "#fef3c7", borderRadius: 8, textAlign: "center" }}>
                <div style={{ fontSize: 28, fontWeight: 700, color: "#92400e" }}>
                  {result.statistics.paths || 0}
                </div>
                <div style={{ fontSize: 14, color: "#78350f", marginTop: 4 }}>Causal Paths</div>
              </div>
            </div>
          )}

          {/* DAG Visualization */}
          {result.visualization_url && (
            <div style={{
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
                Interactive DAG Visualization
              </div>
              <div style={{ padding: 12 }}>
                <iframe
                  src={result.visualization_url}
                  style={{
                    width: "100%",
                    height: 600,
                    border: "none",
                    borderRadius: 4,
                  }}
                  title="dag_visualization"
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Implementation Info */}
      <div style={{
        marginTop: 24,
        padding: 16,
        background: "#d1fae5",
        border: "1px solid #10b981",
        borderRadius: 8,
      }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: "#065f46" }}>
          📝 Implementation Note
        </h3>
        <p style={{ fontSize: 13, color: "#047857", margin: 0 }}>
          <strong>Backend Script:</strong> scripts/advanced_3d_visualizations.py (Interactive DAG)<br />
          <strong>WolframONE:</strong> backend/wolfram/domain_network.wls<br />
          <strong>Technology:</strong> NetworkX, D3.js, Plotly, WolframONE<br />
          <strong>Status:</strong> Backend implementation complete, API integration in progress
        </p>
      </div>
    </div>
  );
}
