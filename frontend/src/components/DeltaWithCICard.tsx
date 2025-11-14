/**
 * Delta with CI Card Component
 * Element 2: 不確実性の提示（Δの95%CI）
 *
 * Reference: 可視化③.pdf - Element 2
 */
import React from 'react';

interface DeltaCIData {
  delta: number;
  ci_lower: number;
  ci_upper: number;
  method: string;
  n_bootstrap?: number;
  is_significant?: boolean;
  badge?: 'green' | 'yellow' | 'red';
}

interface DeltaWithCICardProps {
  delta_ci: DeltaCIData;
  unit?: string;
  className?: string;
}

const DeltaWithCICard: React.FC<DeltaWithCICardProps> = ({
  delta_ci,
  unit = '¥',
  className = ''
}) => {
  const formatValue = (value: number): string => {
    if (unit === '¥' || unit === '$') {
      return `${unit}${value.toLocaleString('ja-JP', { maximumFractionDigits: 0 })}`;
    } else if (unit === '%') {
      return `${value.toFixed(1)}%`;
    } else {
      return value.toLocaleString('ja-JP', { maximumFractionDigits: 2 });
    }
  };

  const getBadgeColor = () => {
    const badge = delta_ci.badge || 'yellow';
    switch (badge) {
      case 'green':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'red':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'yellow':
      default:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    }
  };

  const getBadgeText = () => {
    const badge = delta_ci.badge || 'yellow';
    switch (badge) {
      case 'green':
        return '✓ 有意 (正の効果)';
      case 'red':
        return '✗ 有意 (負の効果)';
      case 'yellow':
      default:
        return '⚠ 非有意';
    }
  };

  const getBarColor = () => {
    const badge = delta_ci.badge || 'yellow';
    switch (badge) {
      case 'green':
        return 'bg-green-500';
      case 'red':
        return 'bg-red-500';
      case 'yellow':
      default:
        return 'bg-yellow-500';
    }
  };

  // Calculate percentage position for CI visualization
  const range = delta_ci.ci_upper - delta_ci.ci_lower;
  const deltaPosition = ((delta_ci.delta - delta_ci.ci_lower) / range) * 100;

  return (
    <div className={`p-6 bg-white rounded-lg shadow-md border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-gray-800">
          Δ (差分効果) with 95% CI
        </h3>
        <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getBadgeColor()}`}>
          {getBadgeText()}
        </span>
      </div>

      {/* Delta Value */}
      <div className="mb-6">
        <div className="text-center">
          <div className="text-sm text-gray-500 mb-1">Δ = J(S1) - J(S0)</div>
          <div className="text-4xl font-bold text-purple-700 mb-2">
            {formatValue(delta_ci.delta)}
          </div>
          <div className="text-sm text-gray-600">
            95% CI: [{formatValue(delta_ci.ci_lower)}, {formatValue(delta_ci.ci_upper)}]
          </div>
        </div>
      </div>

      {/* CI Visualization Bar */}
      <div className="mb-4">
        <div className="relative h-12 bg-gray-100 rounded-lg overflow-hidden">
          {/* CI Range */}
          <div
            className="absolute h-full bg-purple-200 opacity-50"
            style={{
              left: '0%',
              width: '100%'
            }}
          />

          {/* Zero Line */}
          {delta_ci.ci_lower < 0 && delta_ci.ci_upper > 0 && (
            <div
              className="absolute h-full w-0.5 bg-gray-400 z-10"
              style={{
                left: `${((0 - delta_ci.ci_lower) / range) * 100}%`
              }}
            >
              <span className="absolute -top-6 left-0 transform -translate-x-1/2 text-xs text-gray-500">
                0
              </span>
            </div>
          )}

          {/* Delta Point */}
          <div
            className={`absolute h-full w-1 ${getBarColor()} z-20`}
            style={{
              left: `${deltaPosition}%`,
              transform: 'translateX(-50%)'
            }}
          >
            <div className="absolute -top-8 left-0 transform -translate-x-1/2 bg-purple-700 text-white px-2 py-1 rounded text-xs font-semibold whitespace-nowrap">
              Δ: {formatValue(delta_ci.delta)}
            </div>
          </div>
        </div>

        {/* CI Labels */}
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>下限: {formatValue(delta_ci.ci_lower)}</span>
          <span>上限: {formatValue(delta_ci.ci_upper)}</span>
        </div>
      </div>

      {/* Methodology Info */}
      <div className="pt-4 border-t border-gray-200">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500">手法:</span>
            <span className="ml-2 font-semibold text-gray-700">
              {delta_ci.method === 'bootstrap' ? 'ブートストラップ' : 'デルタ法'}
            </span>
          </div>
          {delta_ci.n_bootstrap && (
            <div>
              <span className="text-gray-500">反復回数:</span>
              <span className="ml-2 font-semibold text-gray-700">
                {delta_ci.n_bootstrap.toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Interpretation */}
      <div className="mt-4 p-3 bg-blue-50 rounded text-sm text-blue-800">
        <strong>解釈:</strong> {' '}
        {delta_ci.is_significant ? (
          <>
            95%信頼区間がゼロを含まないため、この効果は統計的に有意です。
            {delta_ci.delta > 0 ? '正の効果が確認されました。' : '負の効果が確認されました。'}
          </>
        ) : (
          <>
            95%信頼区間がゼロを含むため、この効果は統計的に有意ではありません。
            より多くのデータまたは異なるアプローチが必要かもしれません。
          </>
        )}
      </div>
    </div>
  );
};

export default DeltaWithCICard;
