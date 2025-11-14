/**
 * Metadata Footer Component
 * Element 6: 実行メタデータ
 *
 * Reference: 可視化③.pdf - Element 6
 */
import React from 'react';

interface ExecutionMetadata {
  run_id: string;
  seed: number;
  estimator_set: string;
  cv_config: {
    n_folds: number;
    shuffle: boolean;
  };
  created_at: string;
  engine_version?: string;
}

interface MetadataFooterProps {
  metadata: ExecutionMetadata;
  className?: string;
  compact?: boolean;
}

const MetadataFooter: React.FC<MetadataFooterProps> = ({
  metadata,
  className = '',
  compact = false
}) => {
  const formatTimestamp = (isoDate: string): string => {
    const date = new Date(isoDate);
    return date.toLocaleString('ja-JP', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZoneName: 'short'
    });
  };

  const getEstimatorName = (estimator: string): string => {
    const names: Record<string, string> = {
      'ipw': 'IPW (逆傾向スコア重み付け)',
      'dr': 'DR (二重ロバスト)',
      'dm': 'DM (直接法)',
      'aipw': 'AIPW (拡張IPW)'
    };
    return names[estimator] || estimator.toUpperCase();
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    alert('コピーしました: ' + text);
  };

  if (compact) {
    return (
      <div className={`p-2 bg-gray-100 rounded text-xs text-gray-600 ${className}`}>
        <div className="flex flex-wrap gap-4 items-center">
          <span>
            <strong>Run ID:</strong>{' '}
            <button
              onClick={() => copyToClipboard(metadata.run_id)}
              className="font-mono text-blue-600 hover:text-blue-800 hover:underline"
              title="クリックしてコピー"
            >
              {metadata.run_id.substring(0, 8)}...
            </button>
          </span>
          <span><strong>Seed:</strong> {metadata.seed}</span>
          <span><strong>時刻:</strong> {formatTimestamp(metadata.created_at)}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`p-4 bg-gray-50 rounded-lg border border-gray-200 ${className}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h4 className="text-sm font-bold text-gray-700 flex items-center gap-2">
          <span className="text-lg">📋</span>
          実行メタデータ (監査証跡)
        </h4>
        <span className="text-xs text-gray-500">
          再現性とガバナンスのための完全な実行記録
        </span>
      </div>

      {/* Metadata Grid */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {/* Run ID */}
        <div className="p-3 bg-white rounded border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">Run ID</div>
          <div className="font-mono text-sm text-gray-800 break-all">
            {metadata.run_id}
          </div>
          <button
            onClick={() => copyToClipboard(metadata.run_id)}
            className="mt-1 text-xs text-blue-600 hover:text-blue-800 hover:underline"
          >
            📋 コピー
          </button>
        </div>

        {/* Random Seed */}
        <div className="p-3 bg-white rounded border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">乱数シード</div>
          <div className="text-lg font-semibold text-gray-800">
            {metadata.seed}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            再現性担保
          </div>
        </div>

        {/* Estimator */}
        <div className="p-3 bg-white rounded border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">推定器</div>
          <div className="text-sm font-semibold text-purple-700">
            {getEstimatorName(metadata.estimator_set)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {metadata.estimator_set.toUpperCase()}
          </div>
        </div>

        {/* Cross-Validation */}
        <div className="p-3 bg-white rounded border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">交差検証</div>
          <div className="text-sm font-semibold text-gray-800">
            {metadata.cv_config.n_folds}-Fold CV
          </div>
          <div className="text-xs text-gray-500 mt-1">
            {metadata.cv_config.shuffle ? 'シャッフル有効' : 'シャッフル無効'}
          </div>
        </div>

        {/* Timestamp */}
        <div className="p-3 bg-white rounded border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">実行時刻</div>
          <div className="text-xs font-semibold text-gray-800">
            {formatTimestamp(metadata.created_at)}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            ISO 8601形式
          </div>
        </div>

        {/* Engine Version */}
        <div className="p-3 bg-white rounded border border-gray-200">
          <div className="text-xs text-gray-500 mb-1">エンジンバージョン</div>
          <div className="text-sm font-semibold text-gray-800">
            {metadata.engine_version || '1.0.0'}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            CQOx Platform
          </div>
        </div>
      </div>

      {/* Reproducibility Note */}
      <div className="mt-4 p-3 bg-blue-50 rounded text-sm text-blue-800">
        <strong>🔒 再現性保証:</strong> {' '}
        このメタデータを使用することで、全く同じ結果を再現できます。
        Run IDとSeedを記録し、監査時に提示してください。
      </div>

      {/* Export Metadata Button */}
      <div className="mt-3 flex justify-end">
        <button
          onClick={() => {
            const json = JSON.stringify(metadata, null, 2);
            const blob = new Blob([json], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = url;
            link.download = `metadata_${metadata.run_id}.json`;
            link.click();
          }}
          className="px-4 py-2 bg-gray-600 hover:bg-gray-700 text-white rounded text-sm font-semibold"
        >
          📥 メタデータをJSON出力
        </button>
      </div>
    </div>
  );
};

export default MetadataFooter;
