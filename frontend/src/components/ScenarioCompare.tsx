/**
 * Scenario Compare Component
 * Element 3: シナリオ管理（保存・比較・復元）
 *
 * Reference: 可視化③.pdf - Element 3
 */
import React, { useState, useEffect } from 'react';

interface ComparisonRow {
  run_id: string;
  tag: string;
  S0: number;
  S1: number;
  Δ: number;
  CI_lower: number;
  CI_upper: number;
  significant: boolean;
  created_at: string;
  S0_formatted?: string;
  S1_formatted?: string;
  Δ_formatted?: string;
  CI_formatted?: string;
}

interface ScenarioCompareProps {
  run_ids?: string[];
  dataset_id?: string;
  className?: string;
  onSelectRun?: (run_id: string) => void;
}

const ScenarioCompare: React.FC<ScenarioCompareProps> = ({
  run_ids,
  dataset_id,
  className = '',
  onSelectRun
}) => {
  const [comparison, setComparison] = useState<ComparisonRow[]>([]);
  const [allRuns, setAllRuns] = useState<any[]>([]);
  const [selectedRunIds, setSelectedRunIds] = useState<string[]>(run_ids || []);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load all available runs
  useEffect(() => {
    const fetchRuns = async () => {
      try {
        const url = dataset_id
          ? `/api/objective/runs?dataset_id=${dataset_id}`
          : '/api/objective/runs';

        const response = await fetch(url);
        const data = await response.json();

        setAllRuns(data.runs || []);
      } catch (err: any) {
        console.error('Failed to load runs:', err);
        setError(err.message);
      }
    };

    fetchRuns();
  }, [dataset_id]);

  // Load comparison when run IDs change
  useEffect(() => {
    if (selectedRunIds.length === 0) {
      setComparison([]);
      return;
    }

    const fetchComparison = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/objective/compare', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ run_ids: selectedRunIds })
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        setComparison(data.comparison || []);
      } catch (err: any) {
        console.error('Failed to compare runs:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [selectedRunIds]);

  const handleToggleRun = (run_id: string) => {
    if (selectedRunIds.includes(run_id)) {
      setSelectedRunIds(selectedRunIds.filter(id => id !== run_id));
    } else {
      if (selectedRunIds.length < 10) {
        setSelectedRunIds([...selectedRunIds, run_id]);
      } else {
        alert('最大10個のシナリオまで比較できます');
      }
    }
  };

  const handleClearAll = () => {
    setSelectedRunIds([]);
  };

  const formatDate = (isoDate: string): string => {
    const date = new Date(isoDate);
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className={`p-6 bg-white rounded-lg shadow-md border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-gray-800">
          シナリオ比較 (最大10個)
        </h3>
        <div className="flex gap-2">
          <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-semibold">
            選択中: {selectedRunIds.length}/10
          </span>
          {selectedRunIds.length > 0 && (
            <button
              onClick={handleClearAll}
              className="px-3 py-1 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded text-sm font-semibold"
            >
              クリア
            </button>
          )}
        </div>
      </div>

      {/* Run Selector */}
      {allRuns.length > 0 && (
        <div className="mb-6 p-4 bg-gray-50 rounded">
          <div className="text-sm font-semibold text-gray-700 mb-2">
            比較するシナリオを選択:
          </div>
          <div className="max-h-40 overflow-y-auto space-y-1">
            {allRuns.map((run) => (
              <label key={run.run_id} className="flex items-center space-x-2 p-2 hover:bg-gray-100 rounded cursor-pointer">
                <input
                  type="checkbox"
                  checked={selectedRunIds.includes(run.run_id)}
                  onChange={() => handleToggleRun(run.run_id)}
                  className="rounded"
                />
                <span className="text-sm flex-1">
                  {run.tag && <span className="font-semibold text-blue-600">[{run.tag}]</span>}
                  {' '}
                  <span className="text-gray-600">{formatDate(run.created_at)}</span>
                  {' '}
                  <span className="text-gray-500 text-xs">({run.run_id.substring(0, 8)}...)</span>
                </span>
              </label>
            ))}
          </div>
        </div>
      )}

      {/* Loading */}
      {loading && (
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p className="text-gray-600">比較データを読み込み中...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700">
          エラー: {error}
        </div>
      )}

      {/* Comparison Table */}
      {!loading && comparison.length > 0 && (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-300">
                <th className="px-3 py-2 text-left font-semibold text-gray-700">タグ</th>
                <th className="px-3 py-2 text-left font-semibold text-gray-700">作成日時</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-700">S0</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-700">S1</th>
                <th className="px-3 py-2 text-right font-semibold text-gray-700">Δ</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">95% CI</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">有意性</th>
                <th className="px-3 py-2 text-center font-semibold text-gray-700">操作</th>
              </tr>
            </thead>
            <tbody>
              {comparison.map((row, idx) => (
                <tr key={row.run_id} className={`border-b ${idx % 2 === 0 ? 'bg-white' : 'bg-gray-50'}`}>
                  <td className="px-3 py-2">
                    {row.tag !== '-' ? (
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-semibold">
                        {row.tag}
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-gray-600">
                    {formatDate(row.created_at)}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {row.S0_formatted || row.S0.toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-right font-mono">
                    {row.S1_formatted || row.S1.toLocaleString()}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono font-semibold ${row.Δ > 0 ? 'text-green-600' : row.Δ < 0 ? 'text-red-600' : 'text-gray-600'}`}>
                    {row.Δ > 0 ? '+' : ''}{row.Δ_formatted || row.Δ.toLocaleString()}
                  </td>
                  <td className="px-3 py-2 text-center text-xs text-gray-600">
                    {row.CI_formatted || `[${row.CI_lower.toFixed(0)}, ${row.CI_upper.toFixed(0)}]`}
                  </td>
                  <td className="px-3 py-2 text-center">
                    {row.significant ? (
                      <span className="px-2 py-1 bg-green-100 text-green-800 rounded text-xs font-semibold">
                        ✓ 有意
                      </span>
                    ) : (
                      <span className="px-2 py-1 bg-yellow-100 text-yellow-800 rounded text-xs font-semibold">
                        ⚠ 非有意
                      </span>
                    )}
                  </td>
                  <td className="px-3 py-2 text-center">
                    <button
                      onClick={() => onSelectRun && onSelectRun(row.run_id)}
                      className="text-blue-600 hover:text-blue-800 text-xs font-semibold"
                    >
                      詳細
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty State */}
      {!loading && comparison.length === 0 && selectedRunIds.length > 0 && (
        <div className="text-center py-8 text-gray-500">
          比較するシナリオを選択してください
        </div>
      )}

      {/* Export Button */}
      {comparison.length > 0 && (
        <div className="mt-4 flex justify-end">
          <button
            onClick={() => {
              const csv = [
                ['タグ', '作成日時', 'S0', 'S1', 'Δ', 'CI下限', 'CI上限', '有意性'],
                ...comparison.map(row => [
                  row.tag,
                  row.created_at,
                  row.S0,
                  row.S1,
                  row.Δ,
                  row.CI_lower,
                  row.CI_upper,
                  row.significant ? '有意' : '非有意'
                ])
              ].map(row => row.join(',')).join('\n');

              const blob = new Blob(['\uFEFF' + csv], { type: 'text/csv;charset=utf-8;' });
              const url = URL.createObjectURL(blob);
              const link = document.createElement('a');
              link.href = url;
              link.download = `scenario_comparison_${new Date().toISOString().split('T')[0]}.csv`;
              link.click();
            }}
            className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded font-semibold text-sm"
          >
            📥 CSV出力
          </button>
        </div>
      )}
    </div>
  );
};

export default ScenarioCompare;
