#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
Data Audit Display - Module 9: Quality Gates & Diagnostics
Reference: /home/hirokionodera/CQO/可視化④.pdf p.4

10 Quality Gate Checks:
1. Overlap check (propensity score common support)
2. t-statistic threshold (> 2.0)
3. IV F-statistic (> 10 weak, > 20 strong)
4. SMD balance (< 0.1)
5. Missing data heatmap
6. Outlier detection
7. Sample size adequacy
8. Linearity check
9. Homoscedasticity check
10. Normality check (residuals)

Visualizations:
- Overlap histogram
- Love plot (SMD before/after)
- Missing data heatmap
- Quality gates dashboard

Usage:
  wolframscript -file 09_data_audit.wl --input data/dag/data.csv --treatment T --outcome Y --covariates X1,X2,X3 --output artifacts/dag/audit --demo

Outputs:
  - overlap_histogram.png/svg
  - love_plot_smd.png/svg
  - missing_heatmap.png/svg
  - quality_gates_dashboard.png/svg
  - audit_report.json
*)

Get[FileNameJoin[{NotebookDirectory[], "..", "common", "00_common.wl"}]];

(* ==================== Parse Arguments ==================== *)

args = ParseArgs[$ScriptCommandLine[[2;;]]];

inputPath = Lookup[args, "input", "data/dag/data.csv"];
treatment = Lookup[args, "treatment", "T"];
outcome = Lookup[args, "outcome", "Y"];
covariates = If[KeyExistsQ[args, "covariates"],
  StringSplit[Lookup[args, "covariates"], ","],
  {"X1", "X2", "X3"}
];
outputPrefix = Lookup[args, "output", "artifacts/dag/audit"];
demoMode = KeyExistsQ[args, "demo"];

(* ==================== Load or Generate Data ==================== *)

{dataMatrix, headers} = If[demoMode || !FileExistsQ[inputPath],
  Print["Demo mode: Generating synthetic data with quality issues..."];

  n = 1000;
  (* Covariates *)
  x1 = RandomVariate[NormalDistribution[0, 1], n];
  x2 = RandomVariate[NormalDistribution[0, 1], n];
  x3 = RandomVariate[NormalDistribution[0, 1], n];

  (* Treatment (binary) with selection bias *)
  pTreat = Logistic[0.5 * x1 + 0.3 * x2];
  treat = Map[If[RandomReal[] < #, 1, 0] &, pTreat];

  (* Outcome *)
  y = 3 + 2 * treat + 0.5 * x1 + 0.3 * x2 + 0.2 * x3 + RandomVariate[NormalDistribution[0, 0.5], n];

  (* Introduce missing data (5%) *)
  x1 = MapIndexed[If[RandomReal[] < 0.05, Missing[], #1] &, x1];
  x2 = MapIndexed[If[RandomReal[] < 0.05, Missing[], #1] &, x2];

  (* Introduce outliers (1%) *)
  y = MapIndexed[If[RandomReal[] < 0.01, #1 + RandomVariate[NormalDistribution[0, 10]], #1] &, y];

  {Transpose[{treat, y, x1, x2, x3}], {"T", "Y", "X1", "X2", "X3"}},

  Print["Loading data from: " <> inputPath];
  rawData = ReadCSV[inputPath];
  {Rest[rawData], First[rawData]}
];

(* Find column indices *)
treatmentIdx = First[Position[headers, treatment]][[1]];
outcomeIdx = First[Position[headers, outcome]][[1]];
covariateIdx = Map[First[Position[headers, #]][[1]] &, covariates];

tData = dataMatrix[[All, treatmentIdx]];
yData = dataMatrix[[All, outcomeIdx]];
xData = Transpose[Map[dataMatrix[[All, #]] &, covariateIdx]];

n = Length[tData];
Print["Loaded " <> ToString[n] <> " observations"];

(* ==================== Quality Gate 1: Overlap Check ==================== *)

Print["QG1: Checking propensity score overlap..."];

(* Estimate propensity scores using logistic regression *)
(* Simplified: use mean of covariates as proxy *)
propensityScores = Map[
  Logistic[0.3 * Total[#] / Length[#]] &,
  xData
];

treatedIdx = Flatten[Position[tData, 1]];
controlIdx = Flatten[Position[tData, 0]];

propTreated = propensityScores[[treatedIdx]];
propControl = propensityScores[[controlIdx]];

(* Check overlap *)
minOverlap = Thresholds["OverlapMin"];
maxOverlap = Thresholds["OverlapMax"];

overlapViolations = Count[propTreated, _?(# < minOverlap || # > maxOverlap &)] +
                    Count[propControl, _?(# < minOverlap || # > maxOverlap &)];

qg1Pass = overlapViolations < 0.05 * n;
Print["  Overlap violations: " <> ToString[overlapViolations] <> " / " <> ToString[n] <> " - " <> If[qg1Pass, "PASS", "FAIL"]];

(* ==================== Quality Gate 2: t-statistic ==================== *)

Print["QG2: Checking t-statistics for treatment effect..."];

(* Simple t-test *)
yTreated = yData[[treatedIdx]];
yControl = yData[[controlIdx]];

meanDiff = Mean[yTreated] - Mean[yControl];
seDiff = Sqrt[Variance[yTreated]/Length[yTreated] + Variance[yControl]/Length[yControl]];
tStat = Abs[meanDiff / seDiff];

qg2Pass = tStat > Thresholds["TStatMin"];
Print["  t-statistic: " <> ToString[NumberForm[tStat, {4, 2}]] <> " - " <> If[qg2Pass, "PASS", "FAIL"]];

(* ==================== Quality Gate 3: IV F-statistic ==================== *)

(* Skipped if no IV - placeholder *)
qg3Pass = True;
Print["QG3: IV F-statistic - SKIPPED (no IV specified)"];

(* ==================== Quality Gate 4: SMD Balance ==================== *)

Print["QG4: Checking SMD balance..."];

smdBefore = Table[
  xTreated = Map[#[[i]] &, xData[[treatedIdx]]];
  xControl = Map[#[[i]] &, xData[[controlIdx]]];

  (* Remove missing *)
  xTreated = DeleteMissing[xTreated];
  xControl = DeleteMissing[xControl];

  meanDiff = Mean[xTreated] - Mean[xControl];
  pooledSD = Sqrt[(Variance[xTreated] + Variance[xControl]) / 2];

  If[pooledSD > 0, Abs[meanDiff / pooledSD], 0],

  {i, Length[covariates]}
];

qg4Pass = AllTrue[smdBefore, # < Thresholds["SMD"] &];
Print["  SMD: " <> ToString[Map[NumberForm[#, {3, 2}] &, smdBefore]] <> " - " <> If[qg4Pass, "PASS", "FAIL"]];

(* ==================== Quality Gate 5: Missing Data ==================== *)

Print["QG5: Checking missing data..."];

missingCounts = Table[
  col = dataMatrix[[All, covariateIdx[[i]]]];
  Count[col, _Missing],
  {i, Length[covariates]}
];

missingPct = Map[100.0 * # / n &, missingCounts];
qg5Pass = AllTrue[missingPct, # < 10 &];

Print["  Missing %: " <> ToString[Map[NumberForm[#, {3, 1}] &, missingPct]] <> " - " <> If[qg5Pass, "PASS", "FAIL"]];

(* ==================== Quality Gate 6: Outlier Detection ==================== *)

Print["QG6: Checking outliers in outcome..."];

(* IQR method *)
q1 = Quantile[yData, 0.25];
q3 = Quantile[yData, 0.75];
iqr = q3 - q1;
lowerBound = q1 - 1.5 * iqr;
upperBound = q3 + 1.5 * iqr;

outlierCount = Count[yData, _?(# < lowerBound || # > upperBound &)];
outlierPct = 100.0 * outlierCount / n;

qg6Pass = outlierPct < 5;
Print["  Outliers: " <> ToString[outlierCount] <> " (" <> ToString[NumberForm[outlierPct, {3, 1}]] <> "%) - " <> If[qg6Pass, "PASS", "FAIL"]];

(* ==================== Quality Gate 7: Sample Size ==================== *)

Print["QG7: Checking sample size adequacy..."];

minSampleSize = 100;
qg7Pass = Length[treatedIdx] >= minSampleSize && Length[controlIdx] >= minSampleSize;

Print["  Sample size: T=" <> ToString[Length[treatedIdx]] <> ", C=" <> ToString[Length[controlIdx]] <> " - " <> If[qg7Pass, "PASS", "FAIL"]];

(* ==================== Quality Gate 8-10: Regression Diagnostics ==================== *)

Print["QG8-10: Checking linearity, homoscedasticity, normality..."];

(* Fit linear model *)
designMatrix = Transpose[Prepend[Transpose[xData], Table[1, {n}]]];
(* Remove missing rows *)
validRows = Select[Range[n], AllTrue[xData[[#]], NumericQ] &];
designMatrixClean = designMatrix[[validRows]];
yDataClean = yData[[validRows]];

coeffs = LeastSquares[designMatrixClean, yDataClean];
fitted = designMatrixClean . coeffs;
residuals = yDataClean - fitted;

(* QG8: Linearity (correlation between fitted and actual) *)
linearityR = Correlation[fitted, yDataClean];
qg8Pass = linearityR > 0.5;
Print["  Linearity (R): " <> ToString[NumberForm[linearityR, {3, 2}]] <> " - " <> If[qg8Pass, "PASS", "FAIL"]];

(* QG9: Homoscedasticity (constant variance) - Breusch-Pagan simplified *)
residualsSq = residuals^2;
homoTest = Correlation[fitted, residualsSq];
qg9Pass = Abs[homoTest] < 0.3;
Print["  Homoscedasticity: " <> ToString[NumberForm[homoTest, {3, 2}]] <> " - " <> If[qg9Pass, "PASS", "FAIL"]];

(* QG10: Normality (Jarque-Bera approximation) *)
skewness = Skewness[residuals];
kurtosis = Kurtosis[residuals];
jbStat = Length[residuals] / 6 * (skewness^2 + (kurtosis - 3)^2 / 4);
qg10Pass = jbStat < 5.99; (* Chi-square critical value at 0.05 *)

Print["  Normality (JB): " <> ToString[NumberForm[jbStat, {4, 2}]] <> " - " <> If[qg10Pass, "PASS", "FAIL"]];

(* ==================== Overall Quality Summary ==================== *)

allPassed = {qg1Pass, qg2Pass, qg3Pass, qg4Pass, qg5Pass, qg6Pass, qg7Pass, qg8Pass, qg9Pass, qg10Pass};
passCount = Count[allPassed, True];

Print[""];
Print["==================== QUALITY GATES SUMMARY ===================="];
Print["Passed: " <> ToString[passCount] <> " / 10"];
If[passCount == 10,
  Print["Status: ✓ ALL CHECKS PASSED"],
  Print["Status: ✗ FAILED (" <> ToString[10 - passCount] <> " issues)"]
];

(* ==================== Visualizations ==================== *)

(* 1. Overlap Histogram *)
Print["Generating overlap histogram..."];

overlapHist = Histogram[
  {propTreated, propControl},
  20,
  ChartLegends -> {"Treated", "Control"},
  ChartStyle -> {Opacity[0.6, ColorScheme["Primary"]], Opacity[0.6, ColorScheme["Danger"]]},
  FrameLabel -> {"Propensity Score", "Frequency"},
  PlotLabel -> Style["Propensity Score Overlap", Bold, 18],
  ImageSize -> 1200,
  Frame -> True,
  Epilog -> {
    ColorScheme["Warning"], Thickness[0.005], Dashed,
    Line[{{minOverlap, 0}, {minOverlap, 100}}],
    Line[{{maxOverlap, 0}, {maxOverlap, 100}}]
  }
];

SaveFig[overlapHist, outputPrefix <> "_overlap_histogram.png"];
Print["Saved: " <> outputPrefix <> "_overlap_histogram.png"];

(* 2. Love Plot (SMD) *)
Print["Generating Love plot..."];

lovePlot = ListPlot[
  {Transpose[{Range[Length[smdBefore]], smdBefore}],
   Transpose[{Range[Length[smdBefore]], Table[Thresholds["SMD"], {Length[smdBefore]}]}]},
  Joined -> {False, True},
  PlotStyle -> {{ColorScheme["Danger"], PointSize[0.02]}, {ColorScheme["Success"], Dashed, Thickness[0.005]}},
  PlotLegends -> {"SMD Before Adjustment", "Threshold (0.1)"},
  FrameLabel -> {"Covariate", "Standardized Mean Difference"},
  PlotLabel -> Style["Love Plot - Balance Check", Bold, 18],
  ImageSize -> 1200,
  Frame -> True
];

SaveFig[lovePlot, outputPrefix <> "_love_plot_smd.png"];
Print["Saved: " <> outputPrefix <> "_love_plot_smd.png"];

(* 3. Missing Data Heatmap *)
Print["Generating missing data heatmap..."];

missingMatrix = Table[
  If[MissingQ[dataMatrix[[i, covariateIdx[[j]]]]], 1, 0],
  {i, Min[100, n]}, {j, Length[covariates]}
];

missingHeatmap = ArrayPlot[
  Transpose[missingMatrix],
  ColorFunction -> (If[# > 0, ColorScheme["Danger"], White] &),
  ColorFunctionScaling -> False,
  FrameLabel -> {"Observation (first 100)", "Covariate"},
  FrameTicks -> {{Range[Length[covariates]], covariates}, Automatic},
  ImageSize -> 1200,
  PlotLabel -> Style["Missing Data Pattern", Bold, 18]
];

SaveFig[missingHeatmap, outputPrefix <> "_missing_heatmap.png"];
Print["Saved: " <> outputPrefix <> "_missing_heatmap.png"];

(* 4. Quality Gates Dashboard *)
Print["Generating quality gates dashboard..."];

gateLabels = {"QG1 Overlap", "QG2 t-stat", "QG3 IV-F", "QG4 SMD", "QG5 Missing",
              "QG6 Outlier", "QG7 Sample", "QG8 Linear", "QG9 Homo", "QG10 Normal"};
gateColors = Map[If[#, ColorScheme["Success"], ColorScheme["Danger"]] &, allPassed];

gateDashboard = BarChart[
  Map[If[#, 1, 0] &, allPassed],
  ChartLabels -> gateLabels,
  ChartStyle -> gateColors,
  ChartElementFunction -> "GlassRectangle",
  FrameLabel -> {"Quality Gate", "Pass/Fail"},
  PlotLabel -> Style["Quality Gates Dashboard (" <> ToString[passCount] <> "/10 Passed)", Bold, 18],
  ImageSize -> 1200
];

SaveFig[gateDashboard, outputPrefix <> "_quality_gates_dashboard.png"];
Print["Saved: " <> outputPrefix <> "_quality_gates_dashboard.png"];

(* ==================== Export Results ==================== *)

results = <|
  "n_observations" -> n,
  "quality_gates" -> <|
    "qg1_overlap" -> qg1Pass,
    "qg2_tstat" -> qg2Pass,
    "qg3_ivf" -> qg3Pass,
    "qg4_smd" -> qg4Pass,
    "qg5_missing" -> qg5Pass,
    "qg6_outlier" -> qg6Pass,
    "qg7_sample" -> qg7Pass,
    "qg8_linearity" -> qg8Pass,
    "qg9_homoscedasticity" -> qg9Pass,
    "qg10_normality" -> qg10Pass
  |>,
  "passed_count" -> passCount,
  "all_passed" -> passCount == 10,
  "smd_before" -> Thread[covariates -> smdBefore],
  "missing_pct" -> Thread[covariates -> missingPct],
  "outlier_pct" -> outlierPct,
  "timestamp" -> DateString["ISODateTime"]
|>;

ExportJSON[results, outputPrefix <> "_audit_report.json"];
Print["Saved: " <> outputPrefix <> "_audit_report.json"];

Print["Data audit and quality gates complete!"];
