// frontend/src/ui/App.tsx
import React, { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, ReferenceLine, Label } from "recharts";
import { analyzeComprehensive, runScenario } from "../lib/client";
import TasksPanel from "./TasksPanel";
import MetricsDashboard from "../components/MetricsDashboard";
import EstimatorBarChart from "./EstimatorBarChart";

// 階層構造対応: 具体ドメイン（Level 2）のみ表示
const DOMAINS = ["education", "medical", "policy", "retail", "finance", "network"];

// サンプルデータセットのプリセット
const SAMPLE_DATASETS = [
  {
    path: "data/realistic_retail_5k.csv",
    label: "Retail (5K rows)",
    mapping: {
      y: "y",
      treatment: "treatment",
      unit_id: "user_id",
      time: "date",
      cost: "cost",
      log_propensity: "log_propensity"
    },
    domain: "retail",
  },
  {
    path: "data/education_test.csv",
    label: "Education Test",
    mapping: { y: "y", treatment: "treatment", unit_id: "user_id" },
    domain: "education",
  },
  {
    path: "data/finance_test.csv",
    label: "Finance Test",
    mapping: { y: "y", treatment: "treatment", unit_id: "user_id" },
    domain: "finance",
  },
  {
    path: "data/policy_test.csv",
    label: "Policy Test",
    mapping: { y: "y", treatment: "treatment", unit_id: "user_id" },
    domain: "policy",
  },
];

type Mapping = Record<string, string>;

export default function App() {
  const [dfPath, setDfPath] = useState("data/realistic_retail_5k.csv");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [domain, setDomain] = useState<string>("retail");
  const [mapping, setMapping] = useState<Mapping>({
    y: "y",
    treatment: "treatment",
    unit_id: "user_id",
    time: "date",
    cost: "cost",
    log_propensity: "log_propensity",
  });
  const [result, setResult] = useState<any | null>(null);
  const [busy, setBusy] = useState(false);
  const [scenarioResult, setScenarioResult] = useState<any | null>(null);
  const [scenarioBusy, setScenarioBusy] = useState(false);
  const [currentDatasetId, setCurrentDatasetId] = useState<string | null>(
    localStorage.getItem("cqox_dataset_id")
  );
  const canAnalyze = useMemo(
    () => (!!dfPath || !!uploadedFile) && !!mapping.y && !!mapping.treatment,
    [dfPath, uploadedFile, mapping]
  );

  function loadPreset(preset: typeof SAMPLE_DATASETS[0]) {
    setDfPath(preset.path);
    setUploadedFile(null);
    setMapping(preset.mapping);
    setDomain(preset.domain);
    setResult(null);
  }

  function handleFileUpload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      setDfPath(""); // Clear path when file is uploaded
      setResult(null);
    }
  }

  async function onAnalyze() {
    if (!canAnalyze) return;
    setBusy(true);
    try {
      let res;
      if (uploadedFile) {
        // Upload file first
        const formData = new FormData();
        formData.append('file', uploadedFile);
        const uploadRes = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });
        const uploadData = await uploadRes.json();

        // Store dataset_id for scenario analysis
        setCurrentDatasetId(uploadData.dataset_id);
        // Save to localStorage for cross-page persistence
        localStorage.setItem("cqox_dataset_id", uploadData.dataset_id);

        // Then analyze with uploaded dataset_id
        res = await analyzeComprehensive({
          dataset_id: uploadData.dataset_id,
          mapping,
          domain,
        });
      } else {
        // Use specified path
        res = await analyzeComprehensive({
          df_path: dfPath,
          mapping,
          domain,
        });
      }
      setResult(res);
    } finally {
      setBusy(false);
    }
  }

  async function onRunScenario(scenarioId: string) {
    if (!currentDatasetId) {
      alert("Please upload and analyze a dataset first");
      return;
    }
    setScenarioBusy(true);
    try {
      const res = await runScenario({
        dataset_id: currentDatasetId,
        scenario: scenarioId,
        mode: "ope",
        coverage: 0.3,
        budget_cap: 12000000,
        policy_threshold: 0.5,
        neighbor_boost: 0.1,
        geo_multiplier: 1.0,
        network_size: 20,
        value_per_y: 1000,
        cost_per_treated: 500,
      });
      setScenarioResult(res);
    } catch (error: any) {
      alert(`Scenario failed: ${error.message || error}`);
    } finally {
      setScenarioBusy(false);
    }
  }

  return (
    <div style={{ padding: 24, color: "#e5edf7", background: "#0b1323", minHeight: "100vh" }}>
      <div style={{
        marginBottom: 32,
        paddingBottom: 24,
        borderBottom: "2px solid #1e293b",
      }}>
        <h1 style={{
          fontSize: 32,
          fontWeight: 700,
          margin: 0,
          marginBottom: 8,
          background: "linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%)",
          WebkitBackgroundClip: "text",
          WebkitTextFillColor: "transparent",
        }}>
          CQOx Complete
        </h1>
        <p style={{ margin: 0, color: "#94a3b8", fontSize: 14 }}>
          Causal Inference Dashboard with Quality Assurance
        </p>
        <div style={{
          marginTop: 16,
          display: "flex",
          gap: 16,
          alignItems: "center",
        }}>
          <Link
            to="/objective-comparison"
            state={{ datasetId: currentDatasetId }}
            style={{
              padding: "10px 20px",
              background: currentDatasetId
                ? "linear-gradient(135deg, #f59e0b 0%, #d97706 100%)"
                : "linear-gradient(135deg, #6b7280 0%, #4b5563 100%)",
              color: "white",
              textDecoration: "none",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "all 0.2s",
              opacity: currentDatasetId ? 1 : 0.5,
              cursor: currentDatasetId ? "pointer" : "not-allowed",
            }}
            onClick={(e) => {
              if (!currentDatasetId) {
                e.preventDefault();
                alert("Please upload and analyze a dataset first");
              }
            }}
          >
            目的関数比較
          </Link>
          <Link
            to="/advanced-3d"
            state={{ datasetId: currentDatasetId }}
            style={{
              padding: "10px 20px",
              background: "linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%)",
              color: "white",
              textDecoration: "none",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "all 0.2s",
            }}
          >
            3D/4D可視化
          </Link>
          <Link
            to="/marketing-roi"
            state={{ datasetId: currentDatasetId }}
            style={{
              padding: "10px 20px",
              background: "linear-gradient(135deg, #ec4899 0%, #d946ef 100%)",
              color: "white",
              textDecoration: "none",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "all 0.2s",
            }}
          >
            マーケティングROI
          </Link>
          <Link
            to="/dag-visualization"
            state={{ datasetId: currentDatasetId }}
            style={{
              padding: "10px 20px",
              background: "linear-gradient(135deg, #10b981 0%, #059669 100%)",
              color: "white",
              textDecoration: "none",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "all 0.2s",
            }}
          >
            DAG可視化
          </Link>
          <Link
            to="/dag-comprehensive"
            state={{ datasetId: currentDatasetId }}
            style={{
              padding: "10px 20px",
              background: "linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)",
              color: "white",
              textDecoration: "none",
              borderRadius: 8,
              fontSize: 14,
              fontWeight: 600,
              boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
              transition: "all 0.2s",
              border: "2px solid #fbbf24",
            }}
          >
            ⭐ DAG包括分析 (100万円級)
          </Link>
        </div>
      </div>

      <div style={{
        display: "flex",
        flexDirection: "column",
        gap: 16,
        marginBottom: 24,
        padding: 20,
        background: "#1e293b",
        borderRadius: 12,
        border: "1px solid #334155",
      }}>

        {/* File Upload */}
        <div>
          <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "#94a3b8" }}>
            Upload Dataset (CSV, TSV, Parquet)
          </label>
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
            <label style={{
              padding: "8px 16px",
              borderRadius: 8,
              border: "2px dashed #475569",
              background: uploadedFile ? "#3b82f620" : "#0f172a",
              color: uploadedFile ? "#3b82f6" : "#e2e8f0",
              cursor: "pointer",
              fontSize: 14,
              fontWeight: 500,
              transition: "all 0.2s",
            }}>
              <input
                type="file"
                accept=".csv,.tsv,.parquet"
                onChange={handleFileUpload}
                style={{ display: "none" }}
              />
              {uploadedFile ? `📁 ${uploadedFile.name}` : "Choose File..."}
            </label>
            {uploadedFile && (
              <button
                onClick={() => setUploadedFile(null)}
                style={{
                  padding: "6px 12px",
                  borderRadius: 6,
                  border: "1px solid #ef4444",
                  background: "#7f1d1d",
                  color: "#fca5a5",
                  fontSize: 12,
                  cursor: "pointer",
                }}
              >
                Clear
              </button>
            )}
          </div>
        </div>

        {/* Dataset ID Display */}
        {currentDatasetId && (
          <div style={{
            padding: "10px 14px",
            background: "#1e293b",
            border: "1px solid #3b82f6",
            borderRadius: 8,
            marginTop: 12,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}>
            <div style={{
              fontSize: 11,
              color: "#94a3b8",
              fontWeight: 600,
              whiteSpace: "nowrap",
            }}>
              Dataset Ready:
            </div>
            <code style={{
              flex: 1,
              padding: "4px 8px",
              background: "#0f172a",
              border: "1px solid #475569",
              borderRadius: 4,
              color: "#60a5fa",
              fontSize: 11,
              fontFamily: "monospace",
              overflow: "hidden",
              textOverflow: "ellipsis",
            }}>
              {currentDatasetId}
            </code>
            <div style={{
              fontSize: 11,
              color: "#10b981",
              fontWeight: 600,
            }}>
              ✓
            </div>
          </div>
        )}

        {/* OR Divider */}
        <div style={{ display: "flex", alignItems: "center", gap: 12, margin: "8px 0" }}>
          <div style={{ flex: 1, height: 1, background: "#475569" }} />
          <span style={{ color: "#94a3b8", fontSize: 12, fontWeight: 600 }}>OR</span>
          <div style={{ flex: 1, height: 1, background: "#475569" }} />
        </div>

        {/* Dataset Path and Domain */}
        <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap" }}>
          <div style={{ flex: "1 1 400px" }}>
            <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "#94a3b8" }}>
              Or Specify Server Path
            </label>
            <input
              type="text"
              value={dfPath}
              onChange={(e) => { setDfPath(e.target.value); setUploadedFile(null); }}
              placeholder="data/realistic_retail_5k.csv"
              disabled={!!uploadedFile}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid #475569",
                background: uploadedFile ? "#1e293b" : "#0f172a",
                color: uploadedFile ? "#64748b" : "#e2e8f0",
                fontSize: 14,
                opacity: uploadedFile ? 0.5 : 1,
              }}
            />
          </div>
          <div style={{ flex: "0 0 160px" }}>
            <label style={{ display: "block", marginBottom: 6, fontSize: 13, color: "#94a3b8" }}>
              Domain
            </label>
            <select
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              style={{
                width: "100%",
                padding: "8px 12px",
                borderRadius: 8,
                border: "1px solid #475569",
                background: "#0f172a",
                color: "#e2e8f0",
                cursor: "pointer",
              }}
            >
              {DOMAINS.map((d) => (
                <option key={d} value={d}>{d}</option>
              ))}
            </select>
          </div>
          <div style={{ flex: "0 0 auto", alignSelf: "flex-end" }}>
            <button
              onClick={onAnalyze}
              disabled={!canAnalyze || busy}
              style={{
                padding: "8px 24px",
                borderRadius: 8,
                border: "none",
                background: !canAnalyze || busy ? "#475569" : "#10b981",
                color: "#fff",
                fontWeight: 600,
                fontSize: 14,
                cursor: !canAnalyze || busy ? "not-allowed" : "pointer",
                transition: "background 0.2s",
              }}
            >
              {busy ? "Analyzing..." : "Analyze"}
            </button>
          </div>
        </div>
      </div>

      {/* Mapping Editor */}
      <div style={{
        marginBottom: 24,
        padding: 20,
        background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
        borderRadius: 16,
        border: "1px solid #334155",
      }}>
        <h3 style={{
          margin: 0,
          marginBottom: 16,
          fontSize: 20,
          fontWeight: 600,
          color: "#e2e8f0",
          borderBottom: "2px solid #3b82f6",
          paddingBottom: 8,
        }}>
          Column Mapping
        </h3>
        <div style={{ display: "grid", gridTemplateColumns: "150px 1fr", gap: 12, maxWidth: 920 }}>
          {["y", "treatment", "unit_id", "time", "cost", "log_propensity"].map((role) => (
            <React.Fragment key={role}>
              <label style={{
                fontSize: 13,
                fontWeight: 600,
                color: "#94a3b8",
                alignSelf: "center",
              }}>
                {role}
                {(role === "y" || role === "treatment") && (
                  <span style={{ color: "#ef4444", marginLeft: 4 }}>*</span>
                )}
              </label>
              <input
                type="text"
                value={mapping[role] ?? ""}
                onChange={(e) => setMapping((m) => ({ ...m, [role]: e.target.value }))}
                placeholder={`Column name for ${role}`}
                style={{
                  padding: "6px 12px",
                  borderRadius: 8,
                  border: "1px solid #475569",
                  background: "#0f172a",
                  color: "#e2e8f0",
                  fontSize: 13,
                }}
              />
            </React.Fragment>
          ))}
        </div>
      </div>

      {/* Estimator Validation Panel - Removed since we don't have profile data */}
      {false && (
        <div style={{
          marginTop: 24,
          padding: 20,
          background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
          borderRadius: 16,
          border: "1px solid #334155",
        }}>
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: 12,
            marginBottom: 16,
            paddingBottom: 12,
            borderBottom: "2px solid #8b5cf6",
          }}>
            <h3 style={{
              margin: 0,
              fontSize: 20,
              fontWeight: 600,
              color: "#e2e8f0",
            }}>
              Estimator Validation
            </h3>
            <span style={{
              padding: "4px 12px",
              background: profile.estimator_validation.runnable?.length >= 5 ? "#10b981" : "#f59e0b",
              borderRadius: 16,
              fontSize: 13,
              fontWeight: 600,
              color: "#fff",
            }}>
              {profile.estimator_validation.count}
            </span>
          </div>

          {/* Runnable Estimators */}
          {profile.estimator_validation.runnable && profile.estimator_validation.runnable.length > 0 && (
            <div style={{ marginBottom: 16 }}>
              <div style={{
                fontSize: 14,
                fontWeight: 600,
                color: "#10b981",
                marginBottom: 8,
              }}>
                ✓ Ready to Run ({profile.estimator_validation.runnable.length})
              </div>
              <div style={{
                display: "flex",
                flexWrap: "wrap",
                gap: 8,
              }}>
                {profile.estimator_validation.runnable.map((est: string) => (
                  <span
                    key={est}
                    style={{
                      padding: "6px 12px",
                      background: "#10b98120",
                      border: "1px solid #10b981",
                      borderRadius: 8,
                      fontSize: 13,
                      color: "#10b981",
                      fontWeight: 500,
                    }}
                  >
                    {est.toUpperCase()}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Non-runnable Estimators */}
          {profile.estimator_validation.details && Object.entries(profile.estimator_validation.details).some(
            ([_, val]: [string, any]) => !val.can_run
          ) && (
            <div>
              <div style={{
                fontSize: 14,
                fontWeight: 600,
                color: "#f59e0b",
                marginBottom: 8,
              }}>
                ⚠ Missing Requirements
              </div>
              <div style={{
                display: "grid",
                gap: 12,
              }}>
                {Object.entries(profile.estimator_validation.details)
                  .filter(([_, val]: [string, any]) => !val.can_run)
                  .map(([estimator, val]: [string, any]) => (
                    <div
                      key={estimator}
                      style={{
                        padding: 12,
                        background: "#0f172a",
                        border: "1px solid #475569",
                        borderRadius: 8,
                      }}
                    >
                      <div style={{
                        fontSize: 13,
                        fontWeight: 600,
                        color: "#e2e8f0",
                        marginBottom: 4,
                      }}>
                        {estimator.toUpperCase()}
                      </div>
                      <div style={{
                        fontSize: 12,
                        color: "#94a3b8",
                        marginBottom: 6,
                      }}>
                        {val.name}
                      </div>
                      {val.missing_required && val.missing_required.length > 0 && (
                        <div style={{
                          fontSize: 12,
                          color: "#f87171",
                        }}>
                          Missing: {val.missing_required.join(", ")}
                        </div>
                      )}
                      {val.fallback && (
                        <div style={{
                          fontSize: 11,
                          color: "#94a3b8",
                          marginTop: 4,
                          fontStyle: "italic",
                        }}>
                          Fallback: {val.fallback}
                        </div>
                      )}
                    </div>
                  ))}
              </div>
            </div>
          )}
        </div>
      )}

      {result && (
        <div style={{ marginTop: 32 }}>
          {/* 主要指標ダッシュボード */}
          <MetricsDashboard result={result} />

          {/* 23推定器バーチャート */}
          {result.results && result.results.length > 0 && (
            <div style={{ marginTop: 24 }}>
              <EstimatorBarChart results={result.results} />
            </div>
          )}

          {/* Results セクション */}
          <div style={{
            marginBottom: 32,
            padding: 20,
            background: "linear-gradient(135deg, #1e293b 0%, #0f172a 100%)",
            borderRadius: 16,
            border: "1px solid #334155",
          }}>
            <h3 style={{
              margin: 0,
              marginBottom: 16,
              fontSize: 20,
              fontWeight: 600,
              color: "#e2e8f0",
              borderBottom: "2px solid #3b82f6",
              paddingBottom: 8,
            }}>
              Estimation Results
            </h3>
            {Array.isArray(result.results) && result.results.length > 0 ? (
              <div style={{ position: 'relative' }}>
                <div style={{ height: 400, background: "#0f172a", padding: 16, borderRadius: 12, border: "1px solid #1e293b" }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={result.results.map((e: any) => ({ name: e.name ?? e.kind, tau: e.tau_hat ?? e.ate ?? 0 }))}>
                      <XAxis dataKey="name" stroke="#94a3b8" style={{ fontSize: 12 }} />
                      <YAxis stroke="#94a3b8" style={{ fontSize: 12 }} />
                      <Tooltip
                        contentStyle={{
                          background: "#1e293b",
                          border: "1px solid #334155",
                          borderRadius: 8,
                          color: "#e2e8f0",
                        }}
                      />
                      {/* 閾値ライン：Effect Size Threshold |τ| > 0.1 */}
                      <ReferenceLine y={0.1} stroke="#10b981" strokeDasharray="5 5" strokeWidth={2}>
                        <Label value="Effect Threshold (τ=0.1)" position="insideTopRight" fill="#10b981" style={{ fontSize: 11, fontWeight: 600 }} />
                      </ReferenceLine>
                      <ReferenceLine y={-0.1} stroke="#10b981" strokeDasharray="5 5" strokeWidth={2} />
                      {/* 閾値ライン：ゼロライン */}
                      <ReferenceLine y={0} stroke="#64748b" strokeWidth={1.5} />
                      <Bar dataKey="tau" fill="#3b82f6" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
                {/* 推定器の通過閾値を表示 */}
                <div style={{
                  marginTop: 12,
                  padding: 12,
                  background: "#1e293b",
                  borderRadius: 8,
                  border: "1px solid #334155",
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: 8,
                  fontSize: 13
                }}>
                  <div style={{ color: "#94a3b8" }}>
                    <span style={{ fontWeight: 600, color: "#10b981" }}>✓ Significance:</span> p &lt; 0.05
                  </div>
                  <div style={{ color: "#94a3b8" }}>
                    <span style={{ fontWeight: 600, color: "#3b82f6" }}>✓ Effect Size:</span> |τ| &gt; 0.1
                  </div>
                  <div style={{ color: "#94a3b8" }}>
                    <span style={{ fontWeight: 600, color: "#8b5cf6" }}>✓ Precision:</span> SE/|τ| &lt; 0.5
                  </div>
                  <div style={{ color: "#94a3b8" }}>
                    <span style={{ fontWeight: 600, color: "#f59e0b" }}>✓ CI Width:</span> (CI<sub>upper</sub> - CI<sub>lower</sub>)/|τ| &lt; 2.0
                  </div>
                </div>
              </div>
            ) : (
              <pre style={{
                background: "#0f172a",
                padding: 16,
                borderRadius: 8,
                overflow: "auto",
                maxHeight: 400,
                border: "1px solid #1e293b",
                fontSize: 13,
                color: "#94a3b8",
              }}>
                {JSON.stringify(result, null, 2)}
              </pre>
            )}
          </div>

          {/* Figures セクション */}
          {result.figures && (
            <div>
              <h3 style={{
                margin: 0,
                marginBottom: 20,
                fontSize: 20,
                fontWeight: 600,
                color: "#e2e8f0",
                borderBottom: "2px solid #8b5cf6",
                paddingBottom: 8,
              }}>
                Diagnostic Figures
              </h3>
              <TasksPanel figures={result.figures} />
            </div>
          )}
        </div>
      )}
    </div>
  );
}

