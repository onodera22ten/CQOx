import React, { useState, useEffect, useCallback } from 'react';
import { debounce } from 'lodash';
import { runScenario } from '../lib/client';

export type ScenarioParams = {
  coverage: number;          // カバレッジ (0-100%)
  budget_cap: number;        // 予算上限
  policy_threshold: number;  // ポリシー閾値 (0-1)
  neighbor_boost: number;    // ネットワーク効果ブースト (0-1)
  geo_multiplier: number;    // 地理倍率 (0-5)
  network_size: number;      // ネットワークサイズ (0-100)
  value_per_y: number;       // 1単位あたり価値
  cost_per_treated: number;  // 処置コスト
};

interface ScenarioPlaygroundProps {
  initialParams: ScenarioParams;
  onScenarioComplete: (data: any) => void;
  onParamsChange: (params: ScenarioParams) => void;
  datasetId: string;
  scenarioId: string;
  setLoading: (loading: boolean) => void;
}

const ScenarioPlayground: React.FC<ScenarioPlaygroundProps> = ({
  initialParams,
  onScenarioComplete,
  onParamsChange,
  datasetId,
  scenarioId,
  setLoading
}) => {
  const [params, setParams] = useState<ScenarioParams>(initialParams);

  const debouncedRunScenario = useCallback(
    debounce(async (newParams: ScenarioParams) => {
      setLoading(true);
      try {
        const result = await runScenario({
          dataset_id: datasetId,
          scenario: scenarioId,
          mode: 'ope',
          // 全8パラメータを送信
          coverage: newParams.coverage / 100, // 0-1の範囲に変換
          budget_cap: newParams.budget_cap,
          policy_threshold: newParams.policy_threshold,
          neighbor_boost: newParams.neighbor_boost,
          geo_multiplier: newParams.geo_multiplier,
          network_size: newParams.network_size,
          value_per_y: newParams.value_per_y,
          cost_per_treated: newParams.cost_per_treated,
        });
        onScenarioComplete(result);
      } catch (error) {
        console.error('Failed to run scenario:', error);
      } finally {
        setLoading(false);
      }
    }, 300), // 300ms のデバウンス
    [datasetId, scenarioId, onScenarioComplete, setLoading]
  );

  useEffect(() => {
    onParamsChange(params);
    debouncedRunScenario(params);
  }, [params, onParamsChange, debouncedRunScenario]);

  const handleSliderChange = (paramName: keyof ScenarioParams, value: number) => {
    setParams(prevParams => ({ ...prevParams, [paramName]: value }));
  };

  return (
    <div className="p-6 border-2 border-purple-300 rounded-xl bg-gradient-to-br from-purple-50 to-blue-50 mb-6 shadow-lg">
      <h3 className="text-2xl font-bold mb-6 text-purple-800 flex items-center">
        <span className="mr-2">🎛️</span>
        反実仮想パラメータ (Counterfactual Parameters)
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Coverage */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label htmlFor="coverage" className="block text-sm font-semibold text-gray-800 mb-2">
            📊 Coverage (カバレッジ)
          </label>
          <div className="text-2xl font-bold text-purple-600 mb-2">
            {params.coverage}%
          </div>
          <input
            type="range"
            id="coverage"
            min="0"
            max="100"
            step="1"
            value={params.coverage}
            onChange={(e) => handleSliderChange('coverage', parseInt(e.target.value, 10))}
            className="w-full h-3 bg-purple-200 rounded-lg appearance-none cursor-pointer slider-purple"
          />
          <p className="text-xs text-gray-500 mt-1">対象人口の割合</p>
        </div>

        {/* Budget Cap */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label htmlFor="budget_cap" className="block text-sm font-semibold text-gray-800 mb-2">
            💰 Budget Cap (予算上限)
          </label>
          <div className="text-2xl font-bold text-green-600 mb-2">
            ¥{params.budget_cap.toLocaleString()}
          </div>
          <input
            type="range"
            id="budget_cap"
            min="0"
            max="100000000"
            step="1000000"
            value={params.budget_cap}
            onChange={(e) => handleSliderChange('budget_cap', parseInt(e.target.value, 10))}
            className="w-full h-3 bg-green-200 rounded-lg appearance-none cursor-pointer"
          />
          <p className="text-xs text-gray-500 mt-1">最大予算</p>
        </div>

        {/* Policy Threshold */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label htmlFor="policy_threshold" className="block text-sm font-semibold text-gray-800 mb-2">
            🎯 Policy Threshold (閾値)
          </label>
          <div className="text-2xl font-bold text-blue-600 mb-2">
            {params.policy_threshold.toFixed(2)}
          </div>
          <input
            type="range"
            id="policy_threshold"
            min="0"
            max="1"
            step="0.01"
            value={params.policy_threshold}
            onChange={(e) => handleSliderChange('policy_threshold', parseFloat(e.target.value))}
            className="w-full h-3 bg-blue-200 rounded-lg appearance-none cursor-pointer"
          />
          <p className="text-xs text-gray-500 mt-1">処置判定閾値</p>
        </div>

        {/* Neighbor Boost */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label htmlFor="neighbor_boost" className="block text-sm font-semibold text-gray-800 mb-2">
            🔗 Neighbor Boost (近隣効果)
          </label>
          <div className="text-2xl font-bold text-orange-600 mb-2">
            {params.neighbor_boost.toFixed(2)}
          </div>
          <input
            type="range"
            id="neighbor_boost"
            min="0"
            max="1"
            step="0.05"
            value={params.neighbor_boost}
            onChange={(e) => handleSliderChange('neighbor_boost', parseFloat(e.target.value))}
            className="w-full h-3 bg-orange-200 rounded-lg appearance-none cursor-pointer"
          />
          <p className="text-xs text-gray-500 mt-1">ネットワーク波及効果</p>
        </div>

        {/* Geo Multiplier */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label htmlFor="geo_multiplier" className="block text-sm font-semibold text-gray-800 mb-2">
            🌍 Geo Multiplier (地域倍率)
          </label>
          <div className="text-2xl font-bold text-teal-600 mb-2">
            {params.geo_multiplier.toFixed(1)}x
          </div>
          <input
            type="range"
            id="geo_multiplier"
            min="0"
            max="5"
            step="0.1"
            value={params.geo_multiplier}
            onChange={(e) => handleSliderChange('geo_multiplier', parseFloat(e.target.value))}
            className="w-full h-3 bg-teal-200 rounded-lg appearance-none cursor-pointer"
          />
          <p className="text-xs text-gray-500 mt-1">地域効果倍率</p>
        </div>

        {/* Network Size */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label htmlFor="network_size" className="block text-sm font-semibold text-gray-800 mb-2">
            🕸️ Network Size (ネットワーク)
          </label>
          <div className="text-2xl font-bold text-indigo-600 mb-2">
            {params.network_size}
          </div>
          <input
            type="range"
            id="network_size"
            min="0"
            max="100"
            step="5"
            value={params.network_size}
            onChange={(e) => handleSliderChange('network_size', parseInt(e.target.value, 10))}
            className="w-full h-3 bg-indigo-200 rounded-lg appearance-none cursor-pointer"
          />
          <p className="text-xs text-gray-500 mt-1">ネットワーク規模</p>
        </div>

        {/* Value per Y */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label htmlFor="value_per_y" className="block text-sm font-semibold text-gray-800 mb-2">
            💎 Value per Y (単位価値)
          </label>
          <div className="text-2xl font-bold text-yellow-600 mb-2">
            ¥{params.value_per_y.toLocaleString()}
          </div>
          <input
            type="range"
            id="value_per_y"
            min="0"
            max="10000"
            step="100"
            value={params.value_per_y}
            onChange={(e) => handleSliderChange('value_per_y', parseInt(e.target.value, 10))}
            className="w-full h-3 bg-yellow-200 rounded-lg appearance-none cursor-pointer"
          />
          <p className="text-xs text-gray-500 mt-1">アウトカム1単位の価値</p>
        </div>

        {/* Cost per Treated */}
        <div className="bg-white p-4 rounded-lg shadow">
          <label htmlFor="cost_per_treated" className="block text-sm font-semibold text-gray-800 mb-2">
            💸 Cost per Treated (処置コスト)
          </label>
          <div className="text-2xl font-bold text-red-600 mb-2">
            ¥{params.cost_per_treated.toLocaleString()}
          </div>
          <input
            type="range"
            id="cost_per_treated"
            min="0"
            max="5000"
            step="50"
            value={params.cost_per_treated}
            onChange={(e) => handleSliderChange('cost_per_treated', parseInt(e.target.value, 10))}
            className="w-full h-3 bg-red-200 rounded-lg appearance-none cursor-pointer"
          />
          <p className="text-xs text-gray-500 mt-1">1人あたり処置コスト</p>
        </div>
      </div>

      {/* Summary */}
      <div className="mt-6 p-4 bg-white rounded-lg border-2 border-purple-200">
        <h4 className="font-semibold text-gray-800 mb-2">📋 パラメータサマリー</h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
          <div><span className="font-medium">Coverage:</span> {params.coverage}%</div>
          <div><span className="font-medium">Budget:</span> ¥{(params.budget_cap/1000000).toFixed(1)}M</div>
          <div><span className="font-medium">Threshold:</span> {params.policy_threshold.toFixed(2)}</div>
          <div><span className="font-medium">Network Boost:</span> {params.neighbor_boost.toFixed(2)}</div>
          <div><span className="font-medium">Geo:</span> {params.geo_multiplier.toFixed(1)}x</div>
          <div><span className="font-medium">Network:</span> {params.network_size}</div>
          <div><span className="font-medium">Value:</span> ¥{params.value_per_y}</div>
          <div><span className="font-medium">Cost:</span> ¥{params.cost_per_treated}</div>
        </div>
      </div>
    </div>
  );
};

export default ScenarioPlayground;
