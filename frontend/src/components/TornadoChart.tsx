/**
 * Tornado Chart Component
 * Element 5: 感度分析（トルネード図）
 *
 * Reference: 可視化③.pdf - Element 5
 */
import React, { useState, useEffect } from 'react';

interface TornadoData {
  plot_data: {
    params: string[];
    low_deltas: number[];
    high_deltas: number[];
    ranges: number[];
    base_values: number[];
  };
  detailed: Array<{
    param: string;
    base_value: number;
    low_value: number;
    high_value: number;
    low_delta: number;
    high_delta: number;
    range: number;
    direction: string;
  }>;
  top_3_sensitive: string[];
}

interface TornadoChartProps {
  params: Record<string, any>;
  param_names?: string[];
  dataset_id?: string;
  scenario_id?: string;
  variation_pct?: number;
  className?: string;
}

const TornadoChart: React.FC<TornadoChartProps> = ({
  params,
  param_names,
  dataset_id = 'test',
  scenario_id = 'test',
  variation_pct = 0.1,
  className = ''
}) => {
  const [tornadoData, setTornadoData] = useState<TornadoData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchTornadoData = async () => {
      setLoading(true);
      setError(null);

      try {
        const requestBody = {
          params,
          param_names: param_names || Object.keys(params),
          variation_pct,
          dataset_id,
          scenario_id
        };

        const response = await fetch('/api/objective/tornado', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        setTornadoData(data);
      } catch (err: any) {
        console.error('Failed to generate tornado diagram:', err);
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    if (params && Object.keys(params).length > 0) {
      fetchTornadoData();
    }
  }, [params, param_names, variation_pct, dataset_id, scenario_id]);

  if (loading) {
    return (
      <div className={`p-6 bg-white rounded-lg shadow-md border border-gray-200 ${className}`}>
        <div className="text-center py-8">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
          <p className="text-gray-600">感度分析を計算中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`p-6 bg-white rounded-lg shadow-md border border-gray-200 ${className}`}>
        <div className="p-4 bg-red-50 border border-red-200 rounded text-red-700">
          エラー: {error}
        </div>
      </div>
    );
  }

  if (!tornadoData) {
    return null;
  }

  const { plot_data, top_3_sensitive } = tornadoData;
  const maxRange = Math.max(...plot_data.ranges);

  // Parameter labels (Japanese)
  const paramLabels: Record<string, string> = {
    coverage: 'カバレッジ',
    budget_cap: '予算上限',
    policy_threshold: 'ポリシー閾値',
    neighbor_boost: 'ネットワーク効果',
    geo_multiplier: '地域倍率',
    network_size: 'ネットワークサイズ',
    value_per_y: '単位価値',
    cost_per_treated: '処置コスト'
  };

  const getParamLabel = (param: string): string => {
    return paramLabels[param] || param;
  };

  return (
    <div className={`p-6 bg-white rounded-lg shadow-md border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gray-800 mb-2">
          トルネード図 (感度分析)
        </h3>
        <p className="text-sm text-gray-600">
          各パラメータを±{(variation_pct * 100).toFixed(0)}%変化させた時のΔへの影響
        </p>
      </div>

      {/* Top Sensitive Parameters */}
      <div className="mb-4 p-3 bg-blue-50 rounded">
        <div className="text-sm font-semibold text-blue-800 mb-1">
          影響度トップ3:
        </div>
        <div className="flex flex-wrap gap-2">
          {top_3_sensitive.map((param, idx) => (
            <span key={param} className="px-3 py-1 bg-blue-600 text-white rounded-full text-xs font-semibold">
              {idx + 1}. {getParamLabel(param)}
            </span>
          ))}
        </div>
      </div>

      {/* Tornado Bars */}
      <div className="space-y-3">
        {plot_data.params.map((param, idx) => {
          const range = plot_data.ranges[idx];
          const lowDelta = plot_data.low_deltas[idx];
          const highDelta = plot_data.high_deltas[idx];
          const baseValue = plot_data.base_values[idx];

          // Calculate bar widths as percentage of max range
          const leftWidth = ((Math.abs(lowDelta - highDelta) / 2) / maxRange) * 100;
          const rightWidth = leftWidth;

          const isPositive = highDelta > lowDelta;

          return (
            <div key={param} className="relative">
              {/* Parameter Label */}
              <div className="flex justify-between items-center mb-1">
                <span className="text-sm font-semibold text-gray-700">
                  {getParamLabel(param)}
                </span>
                <span className="text-xs text-gray-500">
                  影響: ±{range.toLocaleString('ja-JP', { maximumFractionDigits: 0 })}
                </span>
              </div>

              {/* Tornado Bar */}
              <div className="relative h-8 flex items-center">
                {/* Center Line */}
                <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-gray-300 z-0" />

                {/* Low Delta Bar (left) */}
                <div
                  className={`absolute h-full ${isPositive ? 'bg-red-400' : 'bg-green-400'} opacity-80`}
                  style={{
                    right: '50%',
                    width: `${leftWidth}%`
                  }}
                >
                  <span className="absolute right-2 top-1/2 transform -translate-y-1/2 text-xs text-white font-semibold">
                    {lowDelta.toLocaleString('ja-JP', { maximumFractionDigits: 0 })}
                  </span>
                </div>

                {/* High Delta Bar (right) */}
                <div
                  className={`absolute h-full ${isPositive ? 'bg-green-400' : 'bg-red-400'} opacity-80`}
                  style={{
                    left: '50%',
                    width: `${rightWidth}%`
                  }}
                >
                  <span className="absolute left-2 top-1/2 transform -translate-y-1/2 text-xs text-white font-semibold">
                    {highDelta.toLocaleString('ja-JP', { maximumFractionDigits: 0 })}
                  </span>
                </div>
              </div>

              {/* Base Value */}
              <div className="text-xs text-gray-500 mt-1 text-right">
                基準値: {baseValue.toLocaleString('ja-JP', { maximumFractionDigits: 2 })}
              </div>
            </div>
          );
        })}
      </div>

      {/* Legend */}
      <div className="mt-6 pt-4 border-t border-gray-200">
        <div className="flex justify-center gap-6 text-sm">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-red-400 rounded"></div>
            <span className="text-gray-600">-{(variation_pct * 100).toFixed(0)}% (低)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 bg-green-400 rounded"></div>
            <span className="text-gray-600">+{(variation_pct * 100).toFixed(0)}% (高)</span>
          </div>
        </div>
        <p className="text-xs text-gray-500 text-center mt-2">
          横棒が長いほど、そのパラメータがΔに大きな影響を与えます
        </p>
      </div>

      {/* Interpretation */}
      <div className="mt-4 p-3 bg-yellow-50 rounded text-sm text-yellow-900">
        <strong>💡 インサイト:</strong> {' '}
        {top_3_sensitive.length > 0 && (
          <>
            <strong>{getParamLabel(top_3_sensitive[0])}</strong>が最も影響力の高いパラメータです。
            この値を最適化することで、Δを最大化できます。
          </>
        )}
      </div>
    </div>
  );
};

export default TornadoChart;
