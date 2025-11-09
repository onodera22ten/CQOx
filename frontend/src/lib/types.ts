/**
 * Type Definitions - NASA/Google Standard
 *
 * Purpose: SSOT for all API contracts and UI types
 */

// Scenario Specification
export interface ScenarioSpec {
  id: string;
  label: string;

  // Intervention
  intervention_type: "policy" | "do" | "intensity" | "spend";
  policy_rule?: string;
  coverage?: number;
  do_value?: number;

  // Constraints
  budget_cap?: number;
  unit_cost_col?: string;
  fairness_group_col?: string;
  fairness_max_gap?: number;
  inventory_cap?: number;

  // Geography
  geo_include_regions?: string[];
  geo_multiplier?: number;

  // Network
  network_seed_size?: number;
  network_neighbor_boost?: number;
  network_k?: number;

  // Time
  time_start?: string;
  time_horizon_days?: number;

  // Value
  value_per_y?: number;
  cost_per_treated?: number;
}

// Simulate Request
export interface SimulateRequest {
  scenario_id: string;
  mode: "OPE" | "gcomp" | "DiD";
  coverage?: number;
  budget_cap?: number;
  policy_threshold?: number;
  neighbor_boost?: number;
  geo_multiplier?: number;
  network_size?: number;
  value_per_y?: number;
  cost_per_treated?: number;
  exposure?: {
    type: "kNN" | "radius" | "edges";
    k?: number;
    radius_km?: number;
    decay?: "exp" | "pow" | "uniform";
    alpha?: number;
  };
}

// Simulate Response
export interface SimulateResponse {
  run_id: string;
  S0: {
    ATE: number;
    CI: [number, number];
    treated: number;
  };
  S1: {
    ATE: number;
    CI: [number, number];
    treated: number;
  };
  delta: {
    ATE: number;
    money: {
      point: number;
      CI: [number, number];
    };
  };
  quality: {
    overlap: number;
    gamma: number;
    smd: number;
    q?: number;
  };
  fig_refs?: string[];
}

// Quality Gate Result
export interface QualityGate {
  name: string;
  passed: boolean;
  value: number;
  threshold: number;
  comparison: ">=" | "<=" | ">" | "<";
  message: string;
  severity: "critical" | "warning" | "info";
}

// Quality Gate Report
export interface QualityGateReport {
  decision: "GO" | "CANARY" | "HOLD";
  pass_rate: number;
  summary: string;
  gates: QualityGate[];
}

// Money-View Parameters
export interface MoneyParams {
  value_per_y?: number;
  cost_per_unit?: number;
  value_per_sale?: number;
  r_per_period?: number;
  horizon_days?: number;
}

// Figure Data
export interface FigureData {
  title: string;
  subtitle?: string;
  src: string;
  alt?: string;
  unit?: string;
  money_overlay?: {
    delta_profit?: number;
    delta_profit_ci?: [number, number];
    delta_profit_formatted?: string;
  };
}

// Comparison Data
export interface ComparisonData {
  scenario_id: string;
  label: string;
  S0: ObservationData;
  S1: CounterfactualData;
  delta: DeltaData;
  quality_gates: QualityGateReport;
  figures: Record<string, FigureData>;
  run_metadata: RunMetadata;
}

export interface ObservationData {
  ATE: number;
  ATE_CI: [number, number];
  n_treated: number;
  n_total: number;
}

export interface CounterfactualData {
  ATE: number;
  ATE_CI: [number, number];
  n_treated: number;
  coverage: number;
  total_cost: number;
  profit?: number;
  profit_CI?: [number, number];
}

export interface DeltaData {
  ATE: number;
  profit?: number;
  profit_CI?: [number, number];
}

export interface RunMetadata {
  run_id: string;
  seed?: number;
  code_hash?: string;
  data_hash?: string;
  timestamp: string;
  runtime_ms?: number;
  cost?: number;
}
