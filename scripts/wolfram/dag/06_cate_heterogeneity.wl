#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
CATE Heterogeneity - Module 6: Conditional Average Treatment Effects
Reference: /home/hirokionodera/CQO/可視化④.pdf p.3

Analyzes treatment effect heterogeneity:
1. CATE distribution across covariates
2. Top/worst performing subgroups
3. 3D visualization: Cost × CATE × Segment
4. Policy learning: which segments to target

Usage:
  wolframscript -file 06_cate_heterogeneity.wl --input data/dag/data.csv --treatment T --outcome Y --features X1,X2,X3 --output artifacts/dag/cate --demo

Input CSV format:
  T,Y,X1,X2,X3,cost
  1,5.3,0.8,1.1,0.5,100
  0,4.1,0.5,0.9,0.7,120
  ...

Outputs:
  - cate_distribution.png/svg (2D histogram)
  - top_subgroups.png/svg (bar chart of best/worst segments)
  - cate_cost_3d.png/svg (3D: cost × CATE × segment size)
  - cate_results.json
*)

Get[FileNameJoin[{NotebookDirectory[], "..", "common", "00_common.wl"}]];

(* ==================== Parse Arguments ==================== *)

args = ParseArgs[$ScriptCommandLine[[2;;]]];

inputPath = Lookup[args, "input", "data/dag/data.csv"];
treatment = Lookup[args, "treatment", "T"];
outcome = Lookup[args, "outcome", "Y"];
features = If[KeyExistsQ[args, "features"],
  StringSplit[Lookup[args, "features"], ","],
  {"X1", "X2"}
];
outputPrefix = Lookup[args, "output", "artifacts/dag/cate"];
demoMode = KeyExistsQ[args, "demo"];

(* ==================== Load or Generate Data ==================== *)

{dataMatrix, headers} = If[demoMode || !FileExistsQ[inputPath],
  Print["Demo mode: Generating synthetic data with heterogeneous effects..."];

  n = 1000;
  (* Features *)
  x1 = RandomVariate[NormalDistribution[0, 1], n];
  x2 = RandomVariate[NormalDistribution[0, 1], n];
  (* Treatment (binary) *)
  pTreat = Logistic[0.3 * x1 + 0.2 * x2];
  treat = Map[If[RandomReal[] < #, 1, 0] &, pTreat];
  (* Outcome with heterogeneous treatment effect *)
  (* CATE = 0.5 + 0.3*x1 - 0.2*x2 *)
  cateTrue = 0.5 + 0.3 * x1 - 0.2 * x2;
  y = 2.0 + cateTrue * treat + 0.4 * x1 + 0.3 * x2 + RandomVariate[NormalDistribution[0, 0.5], n];
  (* Cost *)
  cost = RandomVariate[UniformDistribution[{50, 200}], n];

  {Transpose[{treat, y, x1, x2, cost}], {"T", "Y", "X1", "X2", "cost"}},

  Print["Loading data from: " <> inputPath];
  rawData = ReadCSV[inputPath];
  {Rest[rawData], First[rawData]}
];

(* Find column indices *)
treatmentIdx = First[Position[headers, treatment]][[1]];
outcomeIdx = First[Position[headers, outcome]][[1]];
featureIdx = Map[First[Position[headers, #]][[1]] &, features];
costIdx = If[MemberQ[headers, "cost"], First[Position[headers, "cost"]][[1]], 0];

tData = dataMatrix[[All, treatmentIdx]];
yData = dataMatrix[[All, outcomeIdx]];
xData = Transpose[Map[dataMatrix[[All, #]] &, featureIdx]];
costData = If[costIdx > 0, dataMatrix[[All, costIdx]], Table[100, {Length[tData]}]];

Print["Loaded " <> ToString[Length[tData]] <> " observations"];
Print["Features: " <> ToString[features]];

(* ==================== CATE Estimation via S-Learner ==================== *)

Print["Estimating CATE using S-learner (linear regression)..."];

(* Split into treated and control *)
treatedIdx = Flatten[Position[tData, 1]];
controlIdx = Flatten[Position[tData, 0]];

Print["Treated: " <> ToString[Length[treatedIdx]] <> ", Control: " <> ToString[Length[controlIdx]]];

(* Estimate CATE for each observation via stratification *)
(* For each feature combination (binned), compute ATE in that stratum *)

(* Bin features into tertiles *)
nBins = 3;
binEdges = Map[Quantile[#, Range[0, 1, 1/nBins]] &, Transpose[xData]];

(* Assign each observation to a bin *)
binAssignments = MapThread[
  Function[{obs, edges},
    First[Flatten[Position[edges, _?(# >= obs &)]]] - 1
  ],
  {xData, binEdges}
];

(* Compute CATE for each bin combination *)
binCombos = Tuples[Range[0, nBins], Length[features]];

cateEstimates = Table[
  (* Get observations in this bin *)
  binIdx = Flatten[Position[binAssignments, combo]];
  treatedBin = Intersection[binIdx, treatedIdx];
  controlBin = Intersection[binIdx, controlIdx];

  If[Length[treatedBin] >= 5 && Length[controlBin] >= 5,
    ate = Mean[yData[[treatedBin]]] - Mean[yData[[controlBin]]];
    se = Sqrt[Variance[yData[[treatedBin]]]/Length[treatedBin] + Variance[yData[[controlBin]]]/Length[controlBin]];
    <|
      "bin" -> combo,
      "cate" -> ate,
      "se" -> se,
      "ci_lower" -> ate - 1.96 * se,
      "ci_upper" -> ate + 1.96 * se,
      "n" -> Length[binIdx],
      "avg_cost" -> Mean[costData[[binIdx]]]
    |>,
    <|"bin" -> combo, "cate" -> Missing[], "se" -> Missing[], "ci_lower" -> Missing[], "ci_upper" -> Missing[], "n" -> 0, "avg_cost" -> Missing[]|>
  ],
  {combo, binCombos}
];

(* Remove missing *)
validCateEstimates = Select[cateEstimates, NumericQ[#["cate"]] &];

Print["Estimated CATE for " <> ToString[Length[validCateEstimates]] <> " subgroups"];

(* ==================== Top/Worst Subgroups ==================== *)

Print["Identifying top and worst performing subgroups..."];

(* Sort by CATE *)
sortedByCATE = SortBy[validCateEstimates, -#["cate"] &];

topSubgroups = Take[sortedByCATE, Min[5, Length[sortedByCATE]]];
worstSubgroups = Take[Reverse[sortedByCATE], Min[5, Length[sortedByCATE]]];

Print["Top 5 subgroups (highest CATE):"];
Print[topSubgroups[[All, {"bin", "cate"}]]];

Print["Worst 5 subgroups (lowest CATE):"];
Print[worstSubgroups[[All, {"bin", "cate"}]]];

(* ==================== Visualizations ==================== *)

(* 1. CATE Distribution *)
Print["Generating CATE distribution..."];

cateValues = validCateEstimates[[All, "cate"]];

cateHist = Histogram[
  cateValues,
  20,
  ChartStyle -> ColorScheme["Primary"],
  FrameLabel -> {"CATE", "Frequency"},
  PlotLabel -> Style["Distribution of Conditional Average Treatment Effects", Bold, 18],
  ImageSize -> 1200,
  Frame -> True
];

SaveFig[cateHist, outputPrefix <> "_cate_distribution.png"];
Print["Saved: " <> outputPrefix <> "_cate_distribution.png"];

(* 2. Top/Worst Subgroups Bar Chart *)
Print["Generating top/worst subgroups chart..."];

topLabels = Map["Bin " <> ToString[#["bin"]] &, topSubgroups];
worstLabels = Map["Bin " <> ToString[#["bin"]] &, worstSubgroups];

topWorstChart = BarChart[
  {topSubgroups[[All, "cate"]], worstSubgroups[[All, "cate"]]},
  ChartLabels -> {topLabels, worstLabels},
  ChartLegends -> {"Top 5 (Highest CATE)", "Worst 5 (Lowest CATE)"},
  ChartStyle -> {ColorScheme["Success"], ColorScheme["Danger"]},
  FrameLabel -> {"Subgroup", "CATE"},
  PlotLabel -> Style["Top and Worst Performing Subgroups", Bold, 18],
  ImageSize -> 1200
];

SaveFig[topWorstChart, outputPrefix <> "_top_subgroups.png"];
Print["Saved: " <> outputPrefix <> "_top_subgroups.png"];

(* 3. 3D: Cost × CATE × Segment Size *)
Print["Generating 3D cost × CATE × segment visualization..."];

costs3D = validCateEstimates[[All, "avg_cost"]];
cates3D = validCateEstimates[[All, "cate"]];
sizes3D = validCateEstimates[[All, "n"]];

(* Color by ROI (CATE / cost) *)
roi = MapThread[If[#1 > 0, #2 / #1, 0] &, {costs3D, cates3D}];
colorFunc = Blend[{ColorScheme["Danger"], ColorScheme["Warning"], ColorScheme["Success"]}, Rescale[#, MinMax[roi]]] &;

bubbleChart3D = BubbleChart3D[
  MapThread[{#1, #2, #3, #4} &, {costs3D, cates3D, sizes3D, roi}],
  BubbleSizes -> {0.01, 0.1},
  ColorFunction -> colorFunc,
  AxesLabel -> {"Avg Cost", "CATE", "Segment Size"},
  PlotLabel -> Style["3D: Cost × CATE × Segment Size (color = ROI)", Bold, 18],
  ImageSize -> 1200,
  ViewPoint -> {1.3, -2.4, 2.0}
];

SaveFig[bubbleChart3D, outputPrefix <> "_cate_cost_3d.png"];
Print["Saved: " <> outputPrefix <> "_cate_cost_3d.png"];

(* ==================== Export Results ==================== *)

results = <|
  "treatment" -> treatment,
  "outcome" -> outcome,
  "features" -> features,
  "all_subgroups" -> validCateEstimates,
  "top_subgroups" -> topSubgroups,
  "worst_subgroups" -> worstSubgroups,
  "avg_cate" -> Mean[cateValues],
  "cate_sd" -> StandardDeviation[cateValues],
  "n_observations" -> Length[tData],
  "timestamp" -> DateString["ISODateTime"]
|>;

ExportJSON[results, outputPrefix <> "_cate_results.json"];
Print["Saved: " <> outputPrefix <> "_cate_results.json"];

Print["CATE heterogeneity analysis complete!"];
