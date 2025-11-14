/**
 * Objective Formula Component
 * Element 1: Display objective function J(θ) with LaTeX rendering
 *
 * Reference: 可視化③.pdf - Element 1: 目的関数の明示
 */
import React, { useEffect, useState } from 'react';
import katex from 'katex';
import 'katex/dist/katex.min.css';

interface ObjectiveFormulaProps {
  className?: string;
}

interface FormulaData {
  name: string;
  formula_tex: string;
  constraints_tex: string;
  value_per_y: number;
  cost_per_treated: number;
  explanation: {
    S0: string;
    S1: string;
    delta: string;
  };
}

const ObjectiveFormula: React.FC<ObjectiveFormulaProps> = ({ className = '' }) => {
  const [formulaData, setFormulaData] = useState<FormulaData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch formula from API
    fetch('/api/objective/formula')
      .then(res => res.json())
      .then(data => {
        setFormulaData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load objective formula:', err);
        // Fallback to default
        setFormulaData({
          name: 'Expected Net Value',
          formula_tex: String.raw`\max_\theta J(\theta)=V_Y\,\mathbb{E}[Y|\text{policy}(\theta)]-C_T\,\mathbb{E}[T|\text{policy}(\theta)]`,
          constraints_tex: String.raw`\text{s.t. Budget}\le \text{Cap},\ \text{Coverage}\in[0,1]`,
          value_per_y: 1000,
          cost_per_treated: 500,
          explanation: {
            S0: '現状 (Status Quo)',
            S1: 'シナリオ (Counterfactual)',
            delta: 'Δ = J(S1) - J(S0)'
          }
        });
        setLoading(false);
      });
  }, []);

  if (loading || !formulaData) {
    return (
      <div className={`p-4 bg-gray-50 rounded-lg ${className}`}>
        <div className="animate-pulse flex space-x-4">
          <div className="flex-1 space-y-2 py-1">
            <div className="h-4 bg-gray-300 rounded w-3/4"></div>
            <div className="h-4 bg-gray-300 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const renderTeX = (tex: string): string => {
    try {
      return katex.renderToString(tex, {
        throwOnError: false,
        displayMode: true
      });
    } catch (e) {
      console.error('KaTeX rendering error:', e);
      return tex;
    }
  };

  return (
    <div className={`p-6 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg border border-blue-200 shadow-sm ${className}`}>
      <div className="mb-4">
        <h3 className="text-lg font-bold text-gray-800 mb-2 flex items-center">
          <span className="text-2xl mr-2">🎯</span>
          {formulaData.name}
        </h3>
        <p className="text-sm text-gray-600">
          最大化する目的関数 J(θ) と制約条件
        </p>
      </div>

      {/* Main Formula */}
      <div className="mb-4 p-4 bg-white rounded shadow-sm">
        <div
          className="text-center text-lg"
          dangerouslySetInnerHTML={{ __html: renderTeX(formulaData.formula_tex) }}
        />
      </div>

      {/* Constraints */}
      <div className="mb-4 p-3 bg-white rounded shadow-sm">
        <div
          className="text-center text-base"
          dangerouslySetInnerHTML={{ __html: renderTeX(formulaData.constraints_tex) }}
        />
      </div>

      {/* Parameters */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="p-3 bg-white rounded shadow-sm">
          <div className="text-xs text-gray-500 mb-1">単位価値</div>
          <div className="font-semibold text-blue-600">V<sub>Y</sub> = ¥{formulaData.value_per_y.toLocaleString()}</div>
        </div>
        <div className="p-3 bg-white rounded shadow-sm">
          <div className="text-xs text-gray-500 mb-1">処置コスト</div>
          <div className="font-semibold text-orange-600">C<sub>T</sub> = ¥{formulaData.cost_per_treated.toLocaleString()}</div>
        </div>
      </div>

      {/* Explanation */}
      <div className="p-3 bg-white rounded shadow-sm text-sm">
        <div className="grid grid-cols-3 gap-2 text-center">
          <div>
            <span className="font-semibold text-gray-700">S0:</span> {formulaData.explanation.S0}
          </div>
          <div>
            <span className="font-semibold text-green-700">S1:</span> {formulaData.explanation.S1}
          </div>
          <div>
            <span className="font-semibold text-purple-700">Δ:</span> {formulaData.explanation.delta}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ObjectiveFormula;
