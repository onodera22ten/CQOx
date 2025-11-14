import React from "react";

/**
 * RiskBadge - リスクレベル表示コンポーネント（仕様書p.6-7）
 *
 * 信頼区間に基づくリスク分類:
 * - low: 下限が正（確実に正の効果）
 * - medium: 下限が負、上限が正（不確実）
 * - high: 上限が0以下（効果なし/悪化）
 */

interface RiskBadgeProps {
  riskLevel: "low" | "medium" | "high";
  ci?: [number, number];
  size?: "sm" | "md" | "lg";
}

const RISK_CONFIGS = {
  low: {
    label: "低リスク",
    labelEn: "Low Risk",
    color: "#10b981",
    bgColor: "#d1fae5",
    icon: "✓",
  },
  medium: {
    label: "中リスク",
    labelEn: "Medium Risk",
    color: "#f59e0b",
    bgColor: "#fef3c7",
    icon: "⚠",
  },
  high: {
    label: "高リスク",
    labelEn: "High Risk",
    color: "#ef4444",
    bgColor: "#fee2e2",
    icon: "✗",
  },
};

const SIZE_CONFIGS = {
  sm: { fontSize: 11, padding: "4px 8px", iconSize: 12 },
  md: { fontSize: 13, padding: "6px 12px", iconSize: 14 },
  lg: { fontSize: 15, padding: "8px 16px", iconSize: 16 },
};

export default function RiskBadge({ riskLevel, ci, size = "md" }: RiskBadgeProps) {
  const config = RISK_CONFIGS[riskLevel];
  const sizeConfig = SIZE_CONFIGS[size];

  return (
    <div
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 6,
        padding: sizeConfig.padding,
        background: config.bgColor,
        border: `2px solid ${config.color}`,
        borderRadius: 6,
        fontSize: sizeConfig.fontSize,
        fontWeight: 600,
        color: config.color,
      }}
    >
      <span style={{ fontSize: sizeConfig.iconSize }}>{config.icon}</span>
      <span>{config.label}</span>
      {ci && (
        <span style={{ fontSize: sizeConfig.fontSize - 2, fontWeight: 400, marginLeft: 4 }}>
          [{ci[0].toFixed(1)}, {ci[1].toFixed(1)}]
        </span>
      )}
    </div>
  );
}

/**
 * リスクレベル判定関数（backend/core/reco.pyと同期）
 */
export function getRiskLevel(ci: [number, number]): "low" | "medium" | "high" {
  const [lo, hi] = ci;
  if (hi <= 0) return "high";
  if (lo < 0) return "medium";
  return "low";
}
