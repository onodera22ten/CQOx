/**
 * SideBySide Component - NASA/Google Standard
 *
 * Purpose: Side-by-side comparison of S0 (observation) vs S1 (counterfactual)
 * Features:
 * - Responsive grid (2 columns on desktop, 1 on mobile)
 * - Unified scale for comparison
 * - Gray placeholder for missing S1
 */

import { ReactNode } from "react";
import { ChartCard } from "./ChartCard";

export interface SideBySideProps {
  leftTitle: string;
  rightTitle: string;
  left: ReactNode;
  right?: ReactNode;
  unit?: string;
  subtitle?: string;
}

export function SideBySide({
  leftTitle,
  rightTitle,
  left,
  right,
  unit,
  subtitle,
}: SideBySideProps) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {/* S0 - Observation */}
      <ChartCard title={`${leftTitle} (S0)`} unit={unit} subtitle={subtitle}>
        {left}
      </ChartCard>

      {/* S1 - Counterfactual */}
      {right ? (
        <ChartCard title={`${rightTitle} (S1)`} unit={unit} subtitle={subtitle}>
          {right}
        </ChartCard>
      ) : (
        <ChartCard
          title={`${rightTitle} (S1)`}
          unit={unit}
          subtitle="未計算"
          mock
        >
          <div className="flex items-center justify-center h-full text-slate-500">
            <div className="text-center">
              <svg
                className="w-16 h-16 mx-auto mb-3 opacity-30"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1.5}
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
                />
              </svg>
              <p className="text-sm">No scenario output (S1)</p>
              <p className="text-xs mt-1 opacity-60">
                Run simulation to compare
              </p>
            </div>
          </div>
        </ChartCard>
      )}
    </div>
  );
}
