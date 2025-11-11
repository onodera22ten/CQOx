/**
 * SmartFigureCompare Component
 *
 * Side-by-side comparison of S0 (Baseline) vs S1 (Counterfactual) figures
 * Supports WolframONE HTML visualizations and images
 */

import React from 'react';
import { SmartFigure } from '../ui/SmartFigure';

export interface SmartFigureCompareProps {
  title: string;
  srcLeft: string;   // S0 (Baseline)
  srcRight: string;  // S1 (Counterfactual)
  labelLeft?: string;
  labelRight?: string;
  className?: string;
}

export function SmartFigureCompare({
  title,
  srcLeft,
  srcRight,
  labelLeft = "S0 (Baseline)",
  labelRight = "S1 (Counterfactual)",
  className = ""
}: SmartFigureCompareProps) {
  return (
    <div className={`mb-8 ${className}`}>
      {/* Title */}
      <h3 className="text-lg font-semibold mb-4 text-slate-200 border-b border-slate-700 pb-2">
        {title.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())}
      </h3>

      {/* Side-by-side comparison */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: S0 (Baseline) */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
          <div className="mb-3">
            <span className="inline-block px-3 py-1 bg-blue-500/20 text-blue-300 text-sm font-medium rounded-md border border-blue-500/30">
              {labelLeft}
            </span>
          </div>
          <SmartFigure
            src={srcLeft}
            alt={`${title} - ${labelLeft}`}
            title={`${title} - ${labelLeft}`}
          />
        </div>

        {/* Right: S1 (Counterfactual) */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 p-4">
          <div className="mb-3">
            <span className="inline-block px-3 py-1 bg-purple-500/20 text-purple-300 text-sm font-medium rounded-md border border-purple-500/30">
              {labelRight}
            </span>
          </div>
          <SmartFigure
            src={srcRight}
            alt={`${title} - ${labelRight}`}
            title={`${title} - ${labelRight}`}
          />
        </div>
      </div>

      {/* Delta indicator */}
      <div className="mt-4 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 bg-amber-500/10 border border-amber-500/30 rounded-lg">
          <svg className="w-4 h-4 text-amber-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
          </svg>
          <span className="text-sm text-amber-300 font-medium">
            Δ = S1 - S0 (Compare visual differences)
          </span>
        </div>
      </div>
    </div>
  );
}

export default SmartFigureCompare;
