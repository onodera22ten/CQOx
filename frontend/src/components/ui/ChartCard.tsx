/**
 * ChartCard Component - NASA/Google Standard
 *
 * Purpose: Standardized card for all visualizations
 * Features:
 * - Zero-height prevention
 * - Mock/placeholder visual distinction
 * - Unit badges
 * - Skeleton loading
 */

import { ReactNode, useEffect, useRef, useState } from "react";

export interface ChartCardProps {
  title: string;
  unit?: string;
  children: ReactNode;
  mock?: boolean;
  minHeight?: number;
  subtitle?: string;
}

export function ChartCard({
  title,
  unit,
  children,
  mock = false,
  minHeight = 360,
  subtitle,
}: ChartCardProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const ro = new ResizeObserver(() => {
      if (ref.current && ref.current.offsetHeight > 0) {
        setReady(true);
      }
    });

    if (ref.current) {
      ro.observe(ref.current);
    }

    return () => ro.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={`rounded-2xl p-4 shadow-sm relative border border-slate-700/50 bg-slate-800/40 ${
        mock
          ? "opacity-50 bg-[repeating-linear-gradient(45deg,transparent,transparent_8px,rgba(255,255,255,0.02)_8px,rgba(255,255,255,0.02)_16px)]"
          : ""
      }`}
      style={{ minHeight }}
    >
      {/* Header */}
      <div className="text-sm mb-3 flex items-center gap-2 flex-wrap">
        <span className="font-medium text-slate-200">{title}</span>

        {unit && (
          <span className="px-2 py-0.5 text-xs rounded bg-slate-700/50 text-slate-300 font-mono">
            {unit}
          </span>
        )}

        {mock && (
          <span className="px-2 py-0.5 text-xs rounded bg-amber-500/20 text-amber-400 font-medium">
            mock
          </span>
        )}

        {subtitle && (
          <span className="text-xs text-slate-400 ml-auto">{subtitle}</span>
        )}
      </div>

      {/* Content */}
      {!ready ? (
        <div className="animate-pulse h-[calc(100%-2.5rem)] bg-slate-700/30 rounded" />
      ) : (
        children
      )}
    </div>
  );
}
