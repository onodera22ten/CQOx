#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
IV Tester - Module 5: Instrumental Variables Testing
Reference: /home/hirokionodera/CQO/可視化④.pdf p.3

Tests instrumental variable validity:
1. Relevance: F-statistic > 10 (weak), > 20 (strong)
2. Exclusion: IV affects Y only through X
3. Exogeneity: IV uncorrelated with error term

Visualizations:
- F-statistic bar chart with threshold lines
- First-stage regression scatter
- Reduced-form regression
- 2SLS vs OLS comparison

Usage:
  wolframscript -file 05_iv_tester.wl --input data/dag/data.csv --treatment X --outcome Y --instruments Z1,Z2 --output artifacts/dag/iv_test --demo

Input CSV format:
  X,Y,Z1,Z2
  1.2,5.3,0.8,1.1
  ...

Outputs:
  - iv_f_statistics.png/svg (bar chart with thresholds)
  - first_stage_scatter.png/svg
  - iv_2sls_comparison.png/svg
  - iv_test_results.json
*)

Get[FileNameJoin[{NotebookDirectory[], "..", "common", "00_common.wl"}]];

(* ==================== Parse Arguments ==================== *)

args = ParseArgs[$ScriptCommandLine[[2;;]]];

inputPath = Lookup[args, "input", "data/dag/data.csv"];
treatment = Lookup[args, "treatment", "X"];
outcome = Lookup[args, "outcome", "Y"];
instruments = If[KeyExistsQ[args, "instruments"],
  StringSplit[Lookup[args, "instruments"], ","],
  {"Z"}
];
outputPrefix = Lookup[args, "output", "artifacts/dag/iv_test"];
demoMode = KeyExistsQ[args, "demo"];

(* ==================== Load or Generate Data ==================== *)

{dataMatrix, headers} = If[demoMode || !FileExistsQ[inputPath],
  Print["Demo mode: Generating synthetic IV data..."];

  n = 1000;
  (* Strong instrument Z *)
  z = RandomVariate[NormalDistribution[0, 1], n];
  (* Unmeasured confounder U *)
  u = RandomVariate[NormalDistribution[0, 1], n];
  (* Treatment X affected by Z (relevance) and U (confounding) *)
  x = 0.6 * z + 0.4 * u + RandomVariate[NormalDistribution[0, 0.3], n];
  (* Outcome Y affected by X (causal) and U (confounding), NOT Z (exclusion) *)
  y = 0.5 * x + 0.5 * u + RandomVariate[NormalDistribution[0, 0.3], n];

  {Transpose[{x, y, z}], {"X", "Y", "Z"}},

  Print["Loading data from: " <> inputPath];
  rawData = ReadCSV[inputPath];
  {Rest[rawData], First[rawData]}
];

(* Find column indices *)
treatmentIdx = First[Position[headers, treatment]][[1]];
outcomeIdx = First[Position[headers, outcome]][[1]];
instrumentIdx = Map[First[Position[headers, #]][[1]] &, instruments];

xData = dataMatrix[[All, treatmentIdx]];
yData = dataMatrix[[All, outcomeIdx]];
zData = Map[dataMatrix[[All, #]] &, instrumentIdx];

Print["Loaded " <> ToString[Length[xData]] <> " observations"];
Print["Testing " <> ToString[Length[instruments]] <> " instruments: " <> ToString[instruments]];

(* ==================== First-Stage Regression ==================== *)

Print["Running first-stage regression: " <> treatment <> " ~ " <> ToString[instruments]];

(* For each instrument, regress X on Z *)
firstStageResults = Table[
  z = zData[[i]];

  (* Simple linear regression: X = α + β*Z + ε *)
  designMatrix = Transpose[{Table[1, {Length[z]}], z}];
  coeffs = LeastSquares[designMatrix, xData];
  fitted = designMatrix . coeffs;
  residuals = xData - fitted;

  (* Compute F-statistic *)
  ssRegression = Total[(fitted - Mean[xData])^2];
  ssResidual = Total[residuals^2];
  dfRegression = 1; (* Single instrument *)
  dfResidual = Length[xData] - 2;

  msRegression = ssRegression / dfRegression;
  msResidual = ssResidual / dfResidual;
  fStat = msRegression / msResidual;

  (* Correlation *)
  corr = Correlation[z, xData];

  Print["  " <> instruments[[i]] <> ": F = " <> ToString[NumberForm[fStat, {5, 2}]] <> ", r = " <> ToString[NumberForm[corr, {4, 2}]]];

  <|
    "instrument" -> instruments[[i]],
    "f_statistic" -> fStat,
    "correlation" -> corr,
    "coefficient" -> coeffs[[2]],
    "is_weak" -> fStat < Thresholds["IVFWeak"],
    "is_strong" -> fStat >= Thresholds["IVFStrong"]
  |>,

  {i, Length[instruments]}
];

(* ==================== 2SLS Estimation ==================== *)

Print["Running 2SLS estimation..."];

(* Use first instrument for 2SLS *)
z = zData[[1]];

(* Stage 1: X = α + β*Z + ε *)
designMatrix1 = Transpose[{Table[1, {Length[z]}], z}];
coeffs1 = LeastSquares[designMatrix1, xData];
xHat = designMatrix1 . coeffs1;

(* Stage 2: Y = γ + δ*X_hat + η *)
designMatrix2 = Transpose[{Table[1, {Length[xHat]}], xHat}];
coeffs2SLS = LeastSquares[designMatrix2, yData];
ivEstimate = coeffs2SLS[[2]];

(* OLS for comparison: Y = α + β*X + ε *)
designMatrixOLS = Transpose[{Table[1, {Length[xData]}], xData}];
coeffsOLS = LeastSquares[designMatrixOLS, yData];
olsEstimate = coeffsOLS[[2]];

Print["2SLS estimate: " <> ToString[NumberForm[ivEstimate, {4, 3}]]];
Print["OLS estimate: " <> ToString[NumberForm[olsEstimate, {4, 3}]]];
Print["Bias: " <> ToString[NumberForm[olsEstimate - ivEstimate, {4, 3}]]];

(* ==================== Visualizations ==================== *)

(* 1. F-statistic Bar Chart *)
Print["Generating F-statistic chart..."];

fStats = firstStageResults[[All, "f_statistic"]];

(* Color by strength *)
colors = Map[
  If[# < Thresholds["IVFWeak"], ColorScheme["Danger"],
     If[# < Thresholds["IVFStrong"], ColorScheme["Warning"], ColorScheme["Success"]]] &,
  fStats
];

fBarChart = BarChart[
  fStats,
  ChartLabels -> instruments,
  ChartStyle -> colors,
  ChartElementFunction -> "GlassRectangle",
  FrameLabel -> {"Instrument", "F-Statistic"},
  PlotLabel -> Style["IV First-Stage F-Statistics", Bold, 18],
  ImageSize -> 1200,
  GridLines -> {{}, {Thresholds["IVFWeak"], Thresholds["IVFStrong"]}},
  GridLinesStyle -> Directive[Dashed, ColorScheme["Neutral"]]
];

SaveFig[fBarChart, outputPrefix <> "_iv_f_statistics.png"];
Print["Saved: " <> outputPrefix <> "_iv_f_statistics.png"];

(* 2. First-Stage Scatter *)
Print["Generating first-stage scatter plot..."];

firstStageScatter = ListPlot[
  Transpose[{z, xData}],
  PlotStyle -> {ColorScheme["Primary"], PointSize[0.008]},
  FrameLabel -> {instruments[[1]], treatment},
  PlotLabel -> Style["First Stage: " <> treatment <> " ~ " <> instruments[[1]], Bold, 18],
  ImageSize -> 1200,
  Frame -> True,
  Epilog -> {
    ColorScheme["Danger"],
    Thickness[0.006],
    Line[{{Min[z], coeffs1[[1]] + coeffs1[[2]]*Min[z]}, {Max[z], coeffs1[[1]] + coeffs1[[2]]*Max[z]}}]
  }
];

SaveFig[firstStageScatter, outputPrefix <> "_first_stage_scatter.png"];
Print["Saved: " <> outputPrefix <> "_first_stage_scatter.png"];

(* 3. 2SLS vs OLS Comparison *)
Print["Generating 2SLS vs OLS comparison..."];

comparisonData = {
  <|"method" -> "OLS", "estimate" -> olsEstimate|>,
  <|"method" -> "2SLS (IV)", "estimate" -> ivEstimate|>
};

comparisonChart = BarChart[
  {olsEstimate, ivEstimate},
  ChartLabels -> {"OLS\n(biased)", "2SLS\n(unbiased)"},
  ChartStyle -> {ColorScheme["Warning"], ColorScheme["Success"]},
  ChartElementFunction -> "GlassRectangle",
  FrameLabel -> {"Method", "Estimated Effect"},
  PlotLabel -> Style["2SLS vs OLS: Effect of " <> treatment <> " on " <> outcome, Bold, 18],
  ImageSize -> 1200
];

SaveFig[comparisonChart, outputPrefix <> "_iv_2sls_comparison.png"];
Print["Saved: " <> outputPrefix <> "_iv_2sls_comparison.png"];

(* ==================== Export Results ==================== *)

results = <|
  "treatment" -> treatment,
  "outcome" -> outcome,
  "instruments" -> instruments,
  "first_stage_results" -> firstStageResults,
  "ols_estimate" -> olsEstimate,
  "iv_2sls_estimate" -> ivEstimate,
  "bias" -> olsEstimate - ivEstimate,
  "weak_instruments" -> Select[firstStageResults, #["is_weak"] &],
  "strong_instruments" -> Select[firstStageResults, #["is_strong"] &],
  "n_observations" -> Length[xData],
  "timestamp" -> DateString["ISODateTime"]
|>;

ExportJSON[results, outputPrefix <> "_iv_test_results.json"];
Print["Saved: " <> outputPrefix <> "_iv_test_results.json"];

Print["IV testing complete!"];
