import React, { useState, useEffect } from 'react';

/**
 * Dynamic Figure Control Component
 * Allows users to customize visualization parameters in real-time
 */

interface DynamicFigureControlProps {
  figureType: string;
  data: any;
  onParameterChange: (params: VisualizationParams) => void;
  initialParams?: Partial<VisualizationParams>;
}

interface VisualizationParams {
  colorScheme: string;
  binCount: number;
  smoothing: number;
  confidenceLevel: number;
  showGrid: boolean;
  showLegend: boolean;
  fontSize: number;
  width: number;
  height: number;
  transparency: number;
}

const defaultParams: VisualizationParams = {
  colorScheme: 'viridis',
  binCount: 30,
  smoothing: 0.5,
  confidenceLevel: 0.95,
  showGrid: true,
  showLegend: true,
  fontSize: 12,
  width: 800,
  height: 600,
  transparency: 0.8
};

const colorSchemes = [
  { value: 'viridis', label: 'Viridis' },
  { value: 'plasma', label: 'Plasma' },
  { value: 'inferno', label: 'Inferno' },
  { value: 'magma', label: 'Magma' },
  { value: 'rainbow', label: 'Rainbow' },
  { value: 'blues', label: 'Blues' },
  { value: 'reds', label: 'Reds' },
  { value: 'greens', label: 'Greens' }
];

export const DynamicFigureControl: React.FC<DynamicFigureControlProps> = ({
  figureType,
  data,
  onParameterChange,
  initialParams = {}
}) => {
  const [params, setParams] = useState<VisualizationParams>({
    ...defaultParams,
    ...initialParams
  });

  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Notify parent of parameter changes
    onParameterChange(params);
  }, [params, onParameterChange]);

  const updateParameter = (key: keyof VisualizationParams, value: any) => {
    setParams(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const resetToDefaults = () => {
    setParams(defaultParams);
  };

  const exportConfiguration = () => {
    const configJson = JSON.stringify(params, null, 2);
    const blob = new Blob([configJson], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${figureType}_config.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="dynamic-figure-control border border-gray-300 rounded-lg p-4 bg-white shadow-sm">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Visualization Controls
        </h3>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="text-sm text-blue-600 hover:text-blue-800"
        >
          {isExpanded ? 'Collapse' : 'Expand'}
        </button>
      </div>

      {/* Quick Actions */}
      <div className="flex gap-2 mb-4">
        <button
          onClick={resetToDefaults}
          className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded border border-gray-300"
        >
          Reset to Defaults
        </button>
        <button
          onClick={exportConfiguration}
          className="px-3 py-1 text-sm bg-blue-100 hover:bg-blue-200 rounded border border-blue-300"
        >
          Export Config
        </button>
      </div>

      {/* Controls */}
      {isExpanded && (
        <div className="space-y-4">
          {/* Color Scheme */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Color Scheme
            </label>
            <select
              value={params.colorScheme}
              onChange={(e) => updateParameter('colorScheme', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
            >
              {colorSchemes.map(scheme => (
                <option key={scheme.value} value={scheme.value}>
                  {scheme.label}
                </option>
              ))}
            </select>
          </div>

          {/* Bin Count (for histograms) */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Histogram Bins: {params.binCount}
            </label>
            <input
              type="range"
              min="10"
              max="100"
              step="5"
              value={params.binCount}
              onChange={(e) => updateParameter('binCount', parseInt(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>10</span>
              <span>100</span>
            </div>
          </div>

          {/* Smoothing */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Smoothing: {params.smoothing.toFixed(2)}
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={params.smoothing}
              onChange={(e) => updateParameter('smoothing', parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>None</span>
              <span>Maximum</span>
            </div>
          </div>

          {/* Confidence Level */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Confidence Level: {(params.confidenceLevel * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0.80"
              max="0.99"
              step="0.01"
              value={params.confidenceLevel}
              onChange={(e) => updateParameter('confidenceLevel', parseFloat(e.target.value))}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-gray-500">
              <span>80%</span>
              <span>99%</span>
            </div>
          </div>

          {/* Transparency */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Transparency: {(params.transparency * 100).toFixed(0)}%
            </label>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={params.transparency}
              onChange={(e) => updateParameter('transparency', parseFloat(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Font Size */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Font Size: {params.fontSize}px
            </label>
            <input
              type="range"
              min="8"
              max="20"
              step="1"
              value={params.fontSize}
              onChange={(e) => updateParameter('fontSize', parseInt(e.target.value))}
              className="w-full"
            />
          </div>

          {/* Dimensions */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Width: {params.width}px
              </label>
              <input
                type="number"
                min="400"
                max="2000"
                step="50"
                value={params.width}
                onChange={(e) => updateParameter('width', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Height: {params.height}px
              </label>
              <input
                type="number"
                min="300"
                max="1500"
                step="50"
                value={params.height}
                onChange={(e) => updateParameter('height', parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
          </div>

          {/* Boolean Options */}
          <div className="space-y-2">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={params.showGrid}
                onChange={(e) => updateParameter('showGrid', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Show Grid</span>
            </label>

            <label className="flex items-center">
              <input
                type="checkbox"
                checked={params.showLegend}
                onChange={(e) => updateParameter('showLegend', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Show Legend</span>
            </label>
          </div>
        </div>
      )}

      {/* Parameter Summary (when collapsed) */}
      {!isExpanded && (
        <div className="text-sm text-gray-600">
          <p>Color: {params.colorScheme} | Bins: {params.binCount} | CI: {(params.confidenceLevel * 100).toFixed(0)}%</p>
        </div>
      )}
    </div>
  );
};

export default DynamicFigureControl;
