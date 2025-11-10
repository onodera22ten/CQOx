import React, { useState } from 'react';

/**
 * Custom Domain Builder
 * GUI for creating custom domain definitions with keywords, figures, and quality gates
 */

interface KeywordSet {
  strong: string[];
  medium: string[];
  weak: string[];
}

interface FigureDefinition {
  name: string;
  displayName: string;
  requiredColumns: string[];
  optionalColumns: string[];
  minRows: number;
  description: string;
}

interface QualityGate {
  name: string;
  metric: string;
  thresholdType: 'min' | 'max';
  threshold: number;
  severity: 'error' | 'warning';
}

interface DomainConfig {
  name: string;
  displayName: string;
  description: string;
  keywords: KeywordSet;
  figures: FigureDefinition[];
  qualityGates: QualityGate[];
}

const emptyDomain: DomainConfig = {
  name: '',
  displayName: '',
  description: '',
  keywords: {
    strong: [],
    medium: [],
    weak: []
  },
  figures: [],
  qualityGates: []
};

export const CustomDomainBuilder: React.FC = () => {
  const [domain, setDomain] = useState<DomainConfig>(emptyDomain);
  const [activeTab, setActiveTab] = useState<'basic' | 'keywords' | 'figures' | 'quality'>('basic');

  // Keyword input states
  const [newStrongKeyword, setNewStrongKeyword] = useState('');
  const [newMediumKeyword, setNewMediumKeyword] = useState('');
  const [newWeakKeyword, setNewWeakKeyword] = useState('');

  // Figure input states
  const [newFigure, setNewFigure] = useState<FigureDefinition>({
    name: '',
    displayName: '',
    requiredColumns: [],
    optionalColumns: [],
    minRows: 50,
    description: ''
  });

  // Quality gate input state
  const [newQualityGate, setNewQualityGate] = useState<QualityGate>({
    name: '',
    metric: '',
    thresholdType: 'min',
    threshold: 0,
    severity: 'warning'
  });

  const addKeyword = (type: 'strong' | 'medium' | 'weak', keyword: string) => {
    if (keyword.trim()) {
      setDomain(prev => ({
        ...prev,
        keywords: {
          ...prev.keywords,
          [type]: [...prev.keywords[type], keyword.trim()]
        }
      }));

      // Clear input
      if (type === 'strong') setNewStrongKeyword('');
      if (type === 'medium') setNewMediumKeyword('');
      if (type === 'weak') setNewWeakKeyword('');
    }
  };

  const removeKeyword = (type: 'strong' | 'medium' | 'weak', index: number) => {
    setDomain(prev => ({
      ...prev,
      keywords: {
        ...prev.keywords,
        [type]: prev.keywords[type].filter((_, i) => i !== index)
      }
    }));
  };

  const addFigure = () => {
    if (newFigure.name && newFigure.displayName) {
      setDomain(prev => ({
        ...prev,
        figures: [...prev.figures, { ...newFigure }]
      }));

      setNewFigure({
        name: '',
        displayName: '',
        requiredColumns: [],
        optionalColumns: [],
        minRows: 50,
        description: ''
      });
    }
  };

  const removeFigure = (index: number) => {
    setDomain(prev => ({
      ...prev,
      figures: prev.figures.filter((_, i) => i !== index)
    }));
  };

  const addQualityGate = () => {
    if (newQualityGate.name && newQualityGate.metric) {
      setDomain(prev => ({
        ...prev,
        qualityGates: [...prev.qualityGates, { ...newQualityGate }]
      }));

      setNewQualityGate({
        name: '',
        metric: '',
        thresholdType: 'min',
        threshold: 0,
        severity: 'warning'
      });
    }
  };

  const removeQualityGate = (index: number) => {
    setDomain(prev => ({
      ...prev,
      qualityGates: prev.qualityGates.filter((_, i) => i !== index)
    }));
  };

  const exportYAML = () => {
    const yaml = `domain:
  name: ${domain.name}
  display_name: "${domain.displayName}"
  description: "${domain.description}"

keywords:
  strong:
${domain.keywords.strong.map(k => `    - ${k}`).join('\n')}
  medium:
${domain.keywords.medium.map(k => `    - ${k}`).join('\n')}
  weak:
${domain.keywords.weak.map(k => `    - ${k}`).join('\n')}

figures:
${domain.figures.map(fig => `  - name: ${fig.name}
    display_name: "${fig.displayName}"
    required_columns:
${fig.requiredColumns.map(c => `      - ${c}`).join('\n')}
    optional_columns:
${fig.optionalColumns.map(c => `      - ${c}`).join('\n')}
    min_rows: ${fig.minRows}
    description: "${fig.description}"`).join('\n')}

quality_gates:
${domain.qualityGates.map(qg => `  - name: ${qg.name}
    metric: ${qg.metric}
    threshold:
      ${qg.thresholdType}: ${qg.threshold}
    severity: ${qg.severity}`).join('\n')}
`;

    const blob = new Blob([yaml], { type: 'text/yaml' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${domain.name || 'domain'}.yaml`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const saveDomain = async () => {
    try {
      const response = await fetch('/api/domains/custom', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(domain)
      });

      if (response.ok) {
        alert('Domain saved successfully!');
      } else {
        alert('Failed to save domain');
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('Error saving domain');
    }
  };

  return (
    <div className="custom-domain-builder max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold mb-6">Custom Domain Builder</h1>

      {/* Tabs */}
      <div className="flex border-b border-gray-300 mb-6">
        {(['basic', 'keywords', 'figures', 'quality'] as const).map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 font-medium ${
              activeTab === tab
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-600 hover:text-gray-800'
            }`}
          >
            {tab === 'basic' && 'Basic Info'}
            {tab === 'keywords' && 'Keywords'}
            {tab === 'figures' && 'Figures'}
            {tab === 'quality' && 'Quality Gates'}
          </button>
        ))}
      </div>

      {/* Basic Info Tab */}
      {activeTab === 'basic' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Domain Name (Internal)
            </label>
            <input
              type="text"
              value={domain.name}
              onChange={(e) => setDomain(prev => ({ ...prev, name: e.target.value }))}
              placeholder="saas_analytics"
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Display Name
            </label>
            <input
              type="text"
              value={domain.displayName}
              onChange={(e) => setDomain(prev => ({ ...prev, displayName: e.target.value }))}
              placeholder="SaaS Analytics"
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={domain.description}
              onChange={(e) => setDomain(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Domain for analyzing SaaS product metrics and user behavior"
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>
      )}

      {/* Keywords Tab */}
      {activeTab === 'keywords' && (
        <div className="space-y-6">
          {/* Strong Keywords */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Strong Keywords (High Importance)</h3>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newStrongKeyword}
                onChange={(e) => setNewStrongKeyword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addKeyword('strong', newStrongKeyword)}
                placeholder="e.g., churn, mrr, ltv"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              />
              <button
                onClick={() => addKeyword('strong', newStrongKeyword)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {domain.keywords.strong.map((kw, i) => (
                <span key={i} className="px-3 py-1 bg-red-100 text-red-800 rounded-full text-sm flex items-center gap-2">
                  {kw}
                  <button onClick={() => removeKeyword('strong', i)} className="text-red-600 hover:text-red-800">×</button>
                </span>
              ))}
            </div>
          </div>

          {/* Medium Keywords */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Medium Keywords</h3>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newMediumKeyword}
                onChange={(e) => setNewMediumKeyword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addKeyword('medium', newMediumKeyword)}
                placeholder="e.g., activation, feature_usage"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              />
              <button
                onClick={() => addKeyword('medium', newMediumKeyword)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {domain.keywords.medium.map((kw, i) => (
                <span key={i} className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm flex items-center gap-2">
                  {kw}
                  <button onClick={() => removeKeyword('medium', i)} className="text-yellow-600 hover:text-yellow-800">×</button>
                </span>
              ))}
            </div>
          </div>

          {/* Weak Keywords */}
          <div>
            <h3 className="text-lg font-semibold mb-2">Weak Keywords (Low Importance)</h3>
            <div className="flex gap-2 mb-2">
              <input
                type="text"
                value={newWeakKeyword}
                onChange={(e) => setNewWeakKeyword(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addKeyword('weak', newWeakKeyword)}
                placeholder="e.g., date, timestamp"
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md"
              />
              <button
                onClick={() => addKeyword('weak', newWeakKeyword)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
              >
                Add
              </button>
            </div>
            <div className="flex flex-wrap gap-2">
              {domain.keywords.weak.map((kw, i) => (
                <span key={i} className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm flex items-center gap-2">
                  {kw}
                  <button onClick={() => removeKeyword('weak', i)} className="text-green-600 hover:text-green-800">×</button>
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Figures Tab */}
      {activeTab === 'figures' && (
        <div className="space-y-6">
          <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
            <h3 className="text-lg font-semibold mb-4">Add New Figure</h3>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <input
                type="text"
                value={newFigure.name}
                onChange={(e) => setNewFigure(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Figure name (e.g., saas_retention_curve)"
                className="px-3 py-2 border border-gray-300 rounded-md"
              />
              <input
                type="text"
                value={newFigure.displayName}
                onChange={(e) => setNewFigure(prev => ({ ...prev, displayName: e.target.value }))}
                placeholder="Display name"
                className="px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <textarea
              value={newFigure.description}
              onChange={(e) => setNewFigure(prev => ({ ...prev, description: e.target.value }))}
              placeholder="Description"
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md mb-4"
            />
            <div className="flex items-center gap-4 mb-4">
              <label className="text-sm font-medium">Min Rows:</label>
              <input
                type="number"
                value={newFigure.minRows}
                onChange={(e) => setNewFigure(prev => ({ ...prev, minRows: parseInt(e.target.value) }))}
                className="w-24 px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <button
              onClick={addFigure}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Add Figure
            </button>
          </div>

          <div className="space-y-3">
            <h3 className="text-lg font-semibold">Defined Figures ({domain.figures.length})</h3>
            {domain.figures.map((fig, i) => (
              <div key={i} className="border border-gray-300 rounded-lg p-4 bg-white">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <h4 className="font-semibold">{fig.displayName}</h4>
                    <p className="text-sm text-gray-600">{fig.name}</p>
                  </div>
                  <button
                    onClick={() => removeFigure(i)}
                    className="text-red-600 hover:text-red-800"
                  >
                    Remove
                  </button>
                </div>
                <p className="text-sm text-gray-700 mb-2">{fig.description}</p>
                <p className="text-sm text-gray-500">Min Rows: {fig.minRows}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Quality Gates Tab */}
      {activeTab === 'quality' && (
        <div className="space-y-6">
          <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
            <h3 className="text-lg font-semibold mb-4">Add Quality Gate</h3>
            <div className="grid grid-cols-2 gap-4 mb-4">
              <input
                type="text"
                value={newQualityGate.name}
                onChange={(e) => setNewQualityGate(prev => ({ ...prev, name: e.target.value }))}
                placeholder="Gate name"
                className="px-3 py-2 border border-gray-300 rounded-md"
              />
              <input
                type="text"
                value={newQualityGate.metric}
                onChange={(e) => setNewQualityGate(prev => ({ ...prev, metric: e.target.value }))}
                placeholder="Metric name"
                className="px-3 py-2 border border-gray-300 rounded-md"
              />
            </div>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <select
                value={newQualityGate.thresholdType}
                onChange={(e) => setNewQualityGate(prev => ({ ...prev, thresholdType: e.target.value as 'min' | 'max' }))}
                className="px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="min">Minimum</option>
                <option value="max">Maximum</option>
              </select>
              <input
                type="number"
                value={newQualityGate.threshold}
                onChange={(e) => setNewQualityGate(prev => ({ ...prev, threshold: parseFloat(e.target.value) }))}
                placeholder="Threshold"
                className="px-3 py-2 border border-gray-300 rounded-md"
              />
              <select
                value={newQualityGate.severity}
                onChange={(e) => setNewQualityGate(prev => ({ ...prev, severity: e.target.value as 'error' | 'warning' }))}
                className="px-3 py-2 border border-gray-300 rounded-md"
              >
                <option value="warning">Warning</option>
                <option value="error">Error</option>
              </select>
            </div>
            <button
              onClick={addQualityGate}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
            >
              Add Quality Gate
            </button>
          </div>

          <div className="space-y-3">
            <h3 className="text-lg font-semibold">Defined Quality Gates ({domain.qualityGates.length})</h3>
            {domain.qualityGates.map((qg, i) => (
              <div key={i} className="border border-gray-300 rounded-lg p-4 bg-white flex justify-between items-center">
                <div>
                  <h4 className="font-semibold">{qg.name}</h4>
                  <p className="text-sm text-gray-600">
                    {qg.metric} {qg.thresholdType === 'min' ? '≥' : '≤'} {qg.threshold}
                    <span className={`ml-2 px-2 py-1 rounded text-xs ${
                      qg.severity === 'error' ? 'bg-red-100 text-red-800' : 'bg-yellow-100 text-yellow-800'
                    }`}>
                      {qg.severity}
                    </span>
                  </p>
                </div>
                <button
                  onClick={() => removeQualityGate(i)}
                  className="text-red-600 hover:text-red-800"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-4 mt-8 pt-6 border-t border-gray-300">
        <button
          onClick={exportYAML}
          className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-medium"
        >
          Export YAML
        </button>
        <button
          onClick={saveDomain}
          className="px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 font-medium"
        >
          Save & Activate Domain
        </button>
      </div>
    </div>
  );
};

export default CustomDomainBuilder;
