import React, { useState } from "react";
import { Link } from "react-router-dom";

/**
 * DAG Comprehensive Analysis Page - 月額100万円の価値
 *
 * 10モジュール統合:
 * 1. Interactive DAG (Provenance & Reliability)
 * 2. Identifiability Assistant (Backdoor/Frontdoor)
 * 3. do-Operator Runner (Intervention Simulation)
 * 4. Path & Bias Explorer
 * 5. IV Tester
 * 6. CATE Heterogeneity
 * 7. Timeseries DAG
 * 8. Network Spillover
 * 9. Data Audit & Quality Gates
 * 10. Export & Reproducibility
 *
 * PDF仕様: docs/DAG.pdf 完全準拠
 */

interface ModuleResult {
  module_id: number;
  module_name: string;
  status: string;
  outputs: Record<string, string>;
  metadata?: Record<string, any>;
  error_message?: string;
}

interface DAGAnalysisResponse {
  job_id: string;
  status: string;
  modules: ModuleResult[];
  artifacts_dir: string;
}

export default function DAGComprehensivePage() {
  const [datasetId, setDatasetId] = useState<string>(
    localStorage.getItem("cqox_dataset_id") || ""
  );
  const [treatment, setTreatment] = useState("X1");
  const [outcome, setOutcome] = useState("Y");
  const [adjustment, setAdjustment] = useState("Z");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<DAGAnalysisResponse | null>(null);
  const [activeTab, setActiveTab] = useState(1);
  const [runningModules, setRunningModules] = useState<Set<number>>(new Set());

  const modules = [
    {
      id: 1,
      name: "Interactive DAG",
      description: "プロヴナンス&信頼度レイヤ - 2D/3D/GIF可視化",
      icon: "🕸️",
      color: "#10b981"
    },
    {
      id: 2,
      name: "Identifiability",
      description: "識別可能性アシスタント - Backdoor/Frontdoor判定",
      icon: "🎯",
      color: "#3b82f6"
    },
    {
      id: 3,
      name: "do-Operator",
      description: "do演算ランナー - 介入シミュレーション ATE/CATE",
      icon: "⚡",
      color: "#8b5cf6"
    },
    {
      id: 4,
      name: "Path & Bias",
      description: "パス・バイアス探索 - M-bias警告",
      icon: "🔍",
      color: "#ec4899"
    },
    {
      id: 5,
      name: "IV Tester",
      description: "操作変数テスター - F統計/2SLS",
      icon: "📊",
      color: "#f59e0b"
    },
    {
      id: 6,
      name: "CATE Heterogeneity",
      description: "異質効果分析 - セグメント別効果",
      icon: "📈",
      color: "#06b6d4"
    },
    {
      id: 7,
      name: "Timeseries DAG",
      description: "時系列DAG - ラグ/アドストック効果",
      icon: "⏱️",
      color: "#84cc16"
    },
    {
      id: 8,
      name: "Network Spillover",
      description: "ネットワークスピルオーバー&トランスポート",
      icon: "🌐",
      color: "#14b8a6"
    },
    {
      id: 9,
      name: "Quality Gates",
      description: "データ監査 - 10個のQuality Gates",
      icon: "✅",
      color: "#a855f7"
    },
    {
      id: 10,
      name: "Export & Reproducibility",
      description: "エクスポート&再現性 - GraphML/JSON/PDF",
      icon: "📦",
      color: "#f43f5e"
    }
  ];

  const handleRunAll = async () => {
    if (!datasetId) {
      setError("Please enter dataset ID");
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch("/api/dag/run-all", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: datasetId,
          treatment,
          outcome,
          adjustment: [adjustment]
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to run analysis: ${response.statusText}`);
      }

      const data = await response.json();
      setResult(data);

      // 最初の成功したモジュールにタブを切り替え
      const firstSuccess = data.modules.find((m: ModuleResult) => m.status === "success");
      if (firstSuccess) {
        setActiveTab(firstSuccess.module_id);
      }
    } catch (err: any) {
      console.error("DAG analysis failed:", err);
      setError(err.message || "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  const handleRunModule = async (moduleId: number) => {
    if (!datasetId) {
      setError("Please enter dataset ID");
      return;
    }

    setRunningModules(prev => new Set(prev).add(moduleId));
    setError(null);

    try {
      const response = await fetch(`/api/dag/module/${moduleId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          dataset_id: datasetId,
          treatment,
          outcome,
          adjustment: [adjustment]
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to run module ${moduleId}: ${response.statusText}`);
      }

      const moduleResult: ModuleResult = await response.json();

      // Update result with single module
      setResult(prev => {
        if (!prev) {
          return {
            job_id: `module_${moduleId}`,
            status: "completed",
            modules: [moduleResult],
            artifacts_dir: ""
          };
        }

        const existingIndex = prev.modules.findIndex(m => m.module_id === moduleId);
        const newModules = [...prev.modules];

        if (existingIndex >= 0) {
          newModules[existingIndex] = moduleResult;
        } else {
          newModules.push(moduleResult);
          newModules.sort((a, b) => a.module_id - b.module_id);
        }

        return {
          ...prev,
          modules: newModules
        };
      });

      setActiveTab(moduleId);
    } catch (err: any) {
      console.error(`Module ${moduleId} failed:`, err);
      setError(err.message || "Unknown error");
    } finally {
      setRunningModules(prev => {
        const next = new Set(prev);
        next.delete(moduleId);
        return next;
      });
    }
  };

  const getModuleStatus = (moduleId: number) => {
    if (runningModules.has(moduleId)) return "running";
    const module = result?.modules.find(m => m.module_id === moduleId);
    return module?.status || "pending";
  };

  const getModuleResult = (moduleId: number) => {
    return result?.modules.find(m => m.module_id === moduleId);
  };

  return (
    <div style={{ padding: 32, maxWidth: 1600, margin: "0 auto" }}>
      {/* Header */}
      <div style={{
        marginBottom: 24,
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        borderBottom: "2px solid #e5e7eb",
        paddingBottom: 16,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <Link to="/" style={{
            color: "#8b5cf6",
            textDecoration: "none",
            fontWeight: 600,
            fontSize: 14,
          }}>
            ← Back to Main
          </Link>
        </div>
        <div style={{
          background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
          color: "white",
          padding: "8px 16px",
          borderRadius: 8,
          fontSize: 13,
          fontWeight: 600,
        }}>
          月額100万円のバリュー実現
        </div>
      </div>

      {/* Page Title */}
      <h1 style={{
        fontSize: 36,
        fontWeight: 700,
        marginBottom: 8,
        background: "linear-gradient(135deg, #10b981 0%, #3b82f6 50%, #8b5cf6 100%)",
        WebkitBackgroundClip: "text",
        WebkitTextFillColor: "transparent",
      }}>
        DAG 因果推論 - 包括的分析
      </h1>
      <p style={{
        fontSize: 16,
        color: "#6b7280",
        marginBottom: 32,
      }}>
        識別可能性→介入シミュレーション→感度分析→監査→エクスポート まで一気通貫
      </p>

      {/* Configuration Panel */}
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

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr 1fr", gap: 16, marginBottom: 16 }}>
          <div>
            <label style={{ display: "block", fontSize: 14, fontWeight: 600, marginBottom: 8, color: "#374151" }}>
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

          <div>
            <label style={{ display: "block", fontSize: 14, fontWeight: 600, marginBottom: 8, color: "#374151" }}>
              Treatment (X)
            </label>
            <input
              type="text"
              value={treatment}
              onChange={(e) => setTreatment(e.target.value)}
              placeholder="X1"
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

          <div>
            <label style={{ display: "block", fontSize: 14, fontWeight: 600, marginBottom: 8, color: "#374151" }}>
              Outcome (Y)
            </label>
            <input
              type="text"
              value={outcome}
              onChange={(e) => setOutcome(e.target.value)}
              placeholder="Y"
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

          <div>
            <label style={{ display: "block", fontSize: 14, fontWeight: 600, marginBottom: 8, color: "#374151" }}>
              Adjustment (Z)
            </label>
            <input
              type="text"
              value={adjustment}
              onChange={(e) => setAdjustment(e.target.value)}
              placeholder="Z"
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
        </div>

        <button
          onClick={handleRunAll}
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
          {loading ? "🔄 Running All Modules..." : "▶️ Run All 10 Modules"}
        </button>
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

      {/* Module Grid */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(5, 1fr)",
        gap: 16,
        marginBottom: 24,
      }}>
        {modules.map((module) => {
          const status = getModuleStatus(module.id);
          const isRunning = status === "running";
          const isSuccess = status === "success";
          const isError = status === "error";

          return (
            <div
              key={module.id}
              onClick={() => {
                if (isSuccess) setActiveTab(module.id);
                else handleRunModule(module.id);
              }}
              style={{
                background: activeTab === module.id ? module.color : "white",
                color: activeTab === module.id ? "white" : "#1f2937",
                border: `2px solid ${module.color}`,
                borderRadius: 12,
                padding: 16,
                cursor: "pointer",
                transition: "all 0.2s",
                opacity: isRunning ? 0.7 : 1,
              }}
            >
              <div style={{ fontSize: 32, marginBottom: 8 }}>{module.icon}</div>
              <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 4 }}>
                {module.id}. {module.name}
              </div>
              <div style={{ fontSize: 11, marginBottom: 8, opacity: 0.8 }}>
                {module.description}
              </div>
              <div style={{
                fontSize: 12,
                fontWeight: 600,
                padding: "4px 8px",
                borderRadius: 4,
                background: activeTab === module.id ? "rgba(255,255,255,0.2)" : "#f3f4f6",
                color: activeTab === module.id ? "white" : (
                  isSuccess ? "#059669" : isError ? "#dc2626" : isRunning ? "#3b82f6" : "#6b7280"
                ),
                textAlign: "center",
              }}>
                {isRunning ? "🔄 Running" : isSuccess ? "✅ Success" : isError ? "❌ Error" : "⏸️ Pending"}
              </div>
            </div>
          );
        })}
      </div>

      {/* Module Results Display */}
      {result && (
        <div style={{
          background: "white",
          borderRadius: 12,
          padding: 24,
          boxShadow: "0 4px 6px rgba(0,0,0,0.1)",
        }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: 16,
            paddingBottom: 16,
            borderBottom: "2px solid #e5e7eb",
          }}>
            <h2 style={{ fontSize: 20, fontWeight: 600, color: "#1f2937", margin: 0 }}>
              {modules.find(m => m.id === activeTab)?.icon} {modules.find(m => m.id === activeTab)?.name}
            </h2>
            <div style={{
              padding: "8px 16px",
              background: "#d1fae5",
              color: "#065f46",
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 600,
            }}>
              Job ID: {result.job_id}
            </div>
          </div>

          <ModuleResultPanel moduleResult={getModuleResult(activeTab)} />
        </div>
      )}

      {/* Footer Info */}
      <div style={{
        marginTop: 24,
        padding: 16,
        background: "#f9fafb",
        border: "1px solid #e5e7eb",
        borderRadius: 8,
        fontSize: 13,
        color: "#6b7280",
      }}>
        <strong>📚 仕様書準拠:</strong> docs/DAG.pdf 完全実装 |
        <strong> 🔬 Wolfram ONE:</strong> scripts/wolfram/dag/*.wl |
        <strong> 🎯 目標:</strong> 月額100万円のバリュー実現
      </div>
    </div>
  );
}

// Module Result Panel Component
function ModuleResultPanel({ moduleResult }: { moduleResult?: ModuleResult }) {
  if (!moduleResult) {
    return (
      <div style={{ padding: 32, textAlign: "center", color: "#9ca3af" }}>
        Run this module to see results
      </div>
    );
  }

  if (moduleResult.status === "error") {
    return (
      <div style={{
        padding: 24,
        background: "#fee2e2",
        border: "2px solid #ef4444",
        borderRadius: 8,
        color: "#991b1b",
      }}>
        <strong>Error:</strong> {moduleResult.error_message || "Unknown error occurred"}
      </div>
    );
  }

  const outputs = Object.entries(moduleResult.outputs || {});

  if (outputs.length === 0) {
    return (
      <div style={{ padding: 32, textAlign: "center", color: "#9ca3af" }}>
        No outputs available
      </div>
    );
  }

  return (
    <div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(400px, 1fr))", gap: 16 }}>
        {outputs.map(([filename, url]) => (
          <div
            key={filename}
            style={{
              border: "1px solid #e5e7eb",
              borderRadius: 8,
              overflow: "hidden",
            }}
          >
            <div style={{
              padding: 12,
              background: "#f3f4f6",
              borderBottom: "1px solid #e5e7eb",
              fontWeight: 600,
              fontSize: 13,
              color: "#374151",
            }}>
              {filename}
            </div>
            <div style={{ padding: 12 }}>
              {filename.endsWith(".png") || filename.endsWith(".svg") || filename.endsWith(".gif") ? (
                <img
                  src={url}
                  alt={filename}
                  style={{ width: "100%", height: "auto", borderRadius: 4 }}
                />
              ) : filename.endsWith(".json") ? (
                <a
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: "block",
                    padding: "12px 16px",
                    background: "#dbeafe",
                    color: "#1e40af",
                    textDecoration: "none",
                    borderRadius: 4,
                    textAlign: "center",
                    fontWeight: 600,
                  }}
                >
                  📄 View JSON
                </a>
              ) : filename.endsWith(".csv") ? (
                <a
                  href={url}
                  download
                  style={{
                    display: "block",
                    padding: "12px 16px",
                    background: "#dcfce7",
                    color: "#166534",
                    textDecoration: "none",
                    borderRadius: 4,
                    textAlign: "center",
                    fontWeight: 600,
                  }}
                >
                  📊 Download CSV
                </a>
              ) : (
                <a
                  href={url}
                  target="_blank"
                  rel="noreferrer"
                  style={{
                    display: "block",
                    padding: "12px 16px",
                    background: "#f3f4f6",
                    color: "#374151",
                    textDecoration: "none",
                    borderRadius: 4,
                    textAlign: "center",
                    fontWeight: 600,
                  }}
                >
                  📎 View File
                </a>
              )}
            </div>
          </div>
        ))}
      </div>

      {moduleResult.metadata && (
        <div style={{
          marginTop: 16,
          padding: 16,
          background: "#f9fafb",
          border: "1px solid #e5e7eb",
          borderRadius: 8,
        }}>
          <div style={{ fontSize: 14, fontWeight: 600, marginBottom: 8, color: "#374151" }}>
            Metadata
          </div>
          <pre style={{
            fontSize: 12,
            fontFamily: "monospace",
            color: "#6b7280",
            margin: 0,
            overflowX: "auto",
          }}>
            {JSON.stringify(moduleResult.metadata, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}
