import React, { useState } from "react";
import { Link } from "react-router-dom";

/**
 * Advanced3DPage - 3D/4D可視化ページ
 *
 * ARCHITECTURE_COMPLETE.mdに基づく実装
 * 実行: scripts/advanced_3d_visualizations.py
 */

export default function Advanced3DPage() {
  const [datasetId, setDatasetId] = useState<string>(
    localStorage.getItem("cqox_dataset_id") || ""
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<any | null>(null);

  const handleRun3DVisualization = async () => {
    if (!datasetId) {
      setError("Please enter dataset ID");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Call backend endpoint to run 3D visualization script
      const response = await fetch("/api/visualizations/3d/run", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ dataset_id: datasetId }),
      });

      if (!response.ok) {
        throw new Error(`Failed to run 3D visualization: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);
    } catch (err: any) {
      console.error("3D visualization failed:", err);
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
        3D/4D Advanced Visualizations
      </h1>
      <p style={{
        fontSize: 16,
        color: "#6b7280",
        marginBottom: 32,
      }}>
        3D因果効果曲面、4D時系列アニメーション、インタラクティブDAG、3Dネットワークグラフ
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

          {/* Run Button */}
          <button
            onClick={handleRun3DVisualization}
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
            {loading ? "Generating 3D Visualizations..." : "Run 3D/4D Visualization"}
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

      {/* Available Visualizations Info */}
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
          borderBottom: "2px solid #8b5cf6",
          paddingBottom: 8,
        }}>
          Available 3D/4D Visualizations
        </h2>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          <div style={{ padding: 16, background: "#f9fafb", borderRadius: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#4b5563" }}>
              📊 3D Causal Surface
            </h3>
            <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>
              3D因果効果曲面 - 2つの共変量と処置効果の3次元関係
            </p>
          </div>

          <div style={{ padding: 16, background: "#f9fafb", borderRadius: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#4b5563" }}>
              🎬 4D Animation
            </h3>
            <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>
              4D時系列アニメーション - 3D + 時間軸で動的に可視化
            </p>
          </div>

          <div style={{ padding: 16, background: "#f9fafb", borderRadius: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#4b5563" }}>
              🕸️ Interactive DAG
            </h3>
            <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>
              インタラクティブDAG - 因果グラフの対話的探索
            </p>
          </div>

          <div style={{ padding: 16, background: "#f9fafb", borderRadius: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#4b5563" }}>
              🌐 3D Network
            </h3>
            <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>
              3Dネットワークグラフ - ネットワーク効果の立体表示
            </p>
          </div>

          <div style={{ padding: 16, background: "#f9fafb", borderRadius: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#4b5563" }}>
              🗺️ 3D Geo Heatmap
            </h3>
            <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>
              3D地理ヒートマップ - 地域別効果の立体分布
            </p>
          </div>

          <div style={{ padding: 16, background: "#f9fafb", borderRadius: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#4b5563" }}>
              🏔️ 3D CATE Landscape
            </h3>
            <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>
              3D CATE景観 - 条件付き処置効果の地形図
            </p>
          </div>

          <div style={{ padding: 16, background: "#f9fafb", borderRadius: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#4b5563" }}>
              ⏱️ Treatment Effect Animation
            </h3>
            <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>
              処置効果アニメーション (MP4) - 時間経過の視覚化
            </p>
          </div>

          <div style={{ padding: 16, background: "#f9fafb", borderRadius: 8 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 8, color: "#4b5563" }}>
              📈 Pareto Frontier 3D
            </h3>
            <p style={{ fontSize: 14, color: "#6b7280", margin: 0 }}>
              パレート最適フロンティア3D - 多目的最適化の可視化
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
            borderBottom: "2px solid #8b5cf6",
            paddingBottom: 8,
          }}>
            Generated Visualizations
          </h2>

          {result.visualizations && Object.keys(result.visualizations).length > 0 ? (
            <div style={{
              display: "flex",
              flexDirection: "column",
              gap: 32,
            }}>
              {Object.entries(result.visualizations).map(([key, url]: [string, any]) => (
                <div key={key} style={{
                  border: "2px solid #8b5cf6",
                  borderRadius: 12,
                  overflow: "hidden",
                  background: "white",
                  boxShadow: "0 6px 12px rgba(0,0,0,0.1)",
                }}>
                  <div style={{
                    padding: 16,
                    background: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
                    borderBottom: "2px solid #7c3aed",
                    fontWeight: 700,
                    fontSize: 16,
                    color: "white",
                  }}>
                    {key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase())}
                  </div>
                  <div style={{ padding: 20 }}>
                    {url.endsWith('.html') || url.endsWith('.mp4') ? (
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
                        onError={(e) => {
                          (e.target as HTMLImageElement).style.display = "none";
                          (e.target as HTMLImageElement).parentElement!.innerHTML =
                            `<div style="padding:40px;text-align:center;color:#9ca3af;font-size:16px">Failed to load visualization</div>`;
                        }}
                      />
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: "#6b7280" }}>No visualizations generated yet.</p>
          )}
        </div>
      )}

      {/* Implementation Info */}
      <div style={{
        marginTop: 24,
        padding: 16,
        background: "#f0f9ff",
        border: "1px solid #bae6fd",
        borderRadius: 8,
      }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: "#0369a1" }}>
          📝 Implementation Note
        </h3>
        <p style={{ fontSize: 13, color: "#075985", margin: 0 }}>
          <strong>Backend Script:</strong> scripts/advanced_3d_visualizations.py<br />
          <strong>Output Directory:</strong> /home/user/CQOx/visualizations/*.html<br />
          <strong>Technology:</strong> Plotly, NetworkX, Matplotlib<br />
          <strong>Status:</strong> Backend implementation complete, API integration in progress
        </p>
      </div>
    </div>
  );
}
