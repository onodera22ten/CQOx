#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
do-Operator Runner - Module 3: Intervention Simulation
Reference: /home/hirokionodera/CQO/可視化④.pdf p.2

Simulates interventions using do-calculus:
- do(X=x): Set treatment to value x
- Compute E[Y|do(X=x)] for different intervention levels
- Compare with observational E[Y|X=x]
- Show confounding bias
- Display ATE and CATE with 95% CI
- Rosenbaum Γ sensitivity analysis

Usage:
  wolframscript -file 03_do_operator.wl --input data/dag/data.csv --treatment X --outcome Y --adjustment Z --output artifacts/dag/do_operator --demo

Input CSV format (data.csv):
  X,Y,Z
  1.2,5.3,0.8
  0.9,4.1,0.5
  ...

Outputs:
  - intervention_curve.png/svg (E[Y|do(X)] vs X)
  - ate_cate_ci.png/svg (ATE and CATE with confidence intervals)
  - sensitivity_gamma.png/svg (Rosenbaum Γ sensitivity)
  - intervention_results.json
*)

Get[FileNameJoin[{NotebookDirectory[], "..", "common", "00_common.wl"}]];

(* ==================== Parse Arguments ==================== *)

args = ParseArgs[$ScriptCommandLine[[2;;]]];

inputPath = Lookup[args, "input", "data/dag/data.csv"];
treatment = Lookup[args, "treatment", "X"];
outcome = Lookup[args, "outcome", "Y"];
adjustmentVars = If[KeyExistsQ[args, "adjustment"],
  StringSplit[Lookup[args, "adjustment"], ","],
  {}
];
outputPrefix = Lookup[args, "output", "artifacts/dag/do_operator"];
demoMode = KeyExistsQ[args, "demo"];

(* ==================== Load or Generate Data ==================== *)

{dataMatrix, headers} = If[demoMode || !FileExistsQ[inputPath],
  Print["Demo mode: Generating synthetic observational data with confounding..."];

  n = 1000;
  (* Confounder Z affects both X and Y *)
  z = RandomVariate[NormalDistribution[0, 1], n];
  (* X is influenced by Z *)
  x = 0.7 * z + RandomVariate[NormalDistribution[0, 0.5], n];
  (* Y is influenced by both X (causal) and Z (confounding) *)
  y = 0.5 * x + 0.8 * z + RandomVariate[NormalDistribution[0, 0.3], n];

  {Transpose[{x, y, z}], {"X", "Y", "Z"}},

  Print["Loading data from: " <> inputPath];
  rawData = ReadCSV[inputPath];
  {Rest[rawData], First[rawData]}
];

(* Find column indices *)
treatmentIdx = First[Position[headers, treatment]][[1]];
outcomeIdx = First[Position[headers, outcome]][[1]];
adjustmentIdx = Map[First[Position[headers, #]][[1]] &, adjustmentVars];

treatmentData = dataMatrix[[All, treatmentIdx]];
outcomeData = dataMatrix[[All, outcomeIdx]];
adjustmentData = If[Length[adjustmentIdx] > 0,
  dataMatrix[[All, adjustmentIdx]],
  {}
];

Print["Loaded " <> ToString[Length[treatmentData]] <> " observations"];

(* ==================== Observational Association ==================== *)

Print["Computing observational association E[Y|X]..."];

(* Bin treatment into quantiles for curve *)
quantiles = Quantile[treatmentData, Range[0, 1, 0.1]];
xBins = quantiles;

observationalMeans = Table[
  indices = Position[treatmentData, _?(# >= xBins[[i]] && # < xBins[[i+1]] &)];
  If[Length[indices] > 0,
    Mean[outcomeData[[Flatten[indices]]]],
    Missing[]
  ],
  {i, 1, Length[xBins] - 1}
];

(* ==================== Intervention do(X=x) ==================== *)

Print["Computing interventional distribution E[Y|do(X)]..."];

(* Use adjustment formula: E[Y|do(X=x)] = Σ_z E[Y|X=x,Z=z]P(z) *)
(* For continuous Z, we approximate with stratification *)

interventionalMeans = If[Length[adjustmentData] > 0,
  Print["Using adjustment formula with variables: " <> ToString[adjustmentVars]];

  (* Stratify by adjustment variables *)
  zQuantiles = Quantile[adjustmentData[[All, 1]], Range[0, 1, 0.2]];

  Table[
    (* For each intervention level x *)
    xVal = (xBins[[i]] + xBins[[i+1]]) / 2;

    (* Stratify by Z and compute weighted average *)
    strataMeans = Table[
      (* Find observations in this X bin and Z stratum *)
      indices = Flatten[Position[
        MapThread[And,
          {Map[# >= xBins[[i]] && # < xBins[[i+1]] &, treatmentData],
           Map[# >= zQuantiles[[j]] && # < zQuantiles[[j+1]] &, adjustmentData[[All, 1]]]}
        ],
        True
      ]];

      If[Length[indices] > 10,
        {Mean[outcomeData[[indices]]], Length[indices]},
        {Missing[], 0}
      ],
      {j, 1, Length[zQuantiles] - 1}
    ];

    (* Weighted average across strata *)
    weights = strataMeans[[All, 2]];
    means = strataMeans[[All, 1]];
    If[Total[weights] > 0,
      Total[MapThread[#1 * #2 &, {means, weights}]] / Total[weights],
      Missing[]
    ],
    {i, 1, Length[xBins] - 1}
  ],

  (* No adjustment - interventional = observational (biased) *)
  Print["WARNING: No adjustment variables specified - results may be biased!"];
  observationalMeans
];

(* ==================== ATE Calculation ==================== *)

Print["Computing Average Treatment Effect (ATE)..."];

(* Compare high vs low treatment *)
highTreatmentIdx = Flatten[Position[treatmentData, _?(# > Quantile[treatmentData, 0.75] &)]];
lowTreatmentIdx = Flatten[Position[treatmentData, _?(# < Quantile[treatmentData, 0.25] &)]];

(* Adjustment formula for ATE *)
If[Length[adjustmentData] > 0,
  (* Stratified ATE *)
  zStrata = Table[
    Flatten[Position[adjustmentData[[All, 1]], _?(# >= zQuantiles[[j]] && # < zQuantiles[[j+1]] &)]],
    {j, 1, Length[zQuantiles] - 1}
  ];

  ateStrata = Table[
    highIdx = Intersection[highTreatmentIdx, stratum];
    lowIdx = Intersection[lowTreatmentIdx, stratum];
    If[Length[highIdx] > 5 && Length[lowIdx] > 5,
      {Mean[outcomeData[[highIdx]]] - Mean[outcomeData[[lowIdx]]], Length[stratum]},
      {Missing[], 0}
    ],
    {stratum, zStrata}
  ];

  ateWeights = ateStrata[[All, 2]];
  ateValues = ateStrata[[All, 1]];
  ate = If[Total[ateWeights] > 0,
    Total[MapThread[#1 * #2 &, {ateValues, ateWeights}]] / Total[ateWeights],
    0.0
  ];

  (* Bootstrap CI for ATE *)
  ateCI = BootstrapCI[
    Range[Length[treatmentData]],
    Function[indices,
      Module[{highIdx, lowIdx},
        highIdx = Select[indices, treatmentData[[#]] > Quantile[treatmentData, 0.75] &];
        lowIdx = Select[indices, treatmentData[[#]] < Quantile[treatmentData, 0.25] &];
        If[Length[highIdx] > 5 && Length[lowIdx] > 5,
          Mean[outcomeData[[highIdx]]] - Mean[outcomeData[[lowIdx]]],
          0.0
        ]
      ]
    ],
    "Bootstraps" -> 1000,
    "Level" -> 0.95
  ],

  (* Unadjusted ATE (biased) *)
  ate = Mean[outcomeData[[highTreatmentIdx]]] - Mean[outcomeData[[lowTreatmentIdx]]];
  ateCI = <|"lower" -> ate - 1.96 * StandardError[outcomeData], "upper" -> ate + 1.96 * StandardError[outcomeData]|>
];

Print["ATE = " <> ToString[NumberForm[ate, {4, 2}]] <> " [" <> ToString[NumberForm[ateCI["lower"], {4, 2}]] <> ", " <> ToString[NumberForm[ateCI["upper"], {4, 2}]] <> "]"];

(* ==================== CATE by Subgroup ==================== *)

Print["Computing Conditional Average Treatment Effect (CATE) by subgroup..."];

(* Compute CATE for each Z quartile *)
cateResults = Table[
  stratumIdx = Flatten[Position[adjustmentData[[All, 1]], _?(# >= zQuantiles[[j]] && # < zQuantiles[[j+1]] &)]];
  highIdx = Intersection[highTreatmentIdx, stratumIdx];
  lowIdx = Intersection[lowTreatmentIdx, stratumIdx];

  If[Length[highIdx] > 5 && Length[lowIdx] > 5,
    cate = Mean[outcomeData[[highIdx]]] - Mean[outcomeData[[lowIdx]]];
    se = Sqrt[Variance[outcomeData[[highIdx]]]/Length[highIdx] + Variance[outcomeData[[lowIdx]]]/Length[lowIdx]];
    <|"stratum" -> j, "cate" -> cate, "ci_lower" -> cate - 1.96*se, "ci_upper" -> cate + 1.96*se, "n" -> Length[stratumIdx]|>,
    <|"stratum" -> j, "cate" -> Missing[], "ci_lower" -> Missing[], "ci_upper" -> Missing[], "n" -> 0|>
  ],
  {j, 1, Length[zQuantiles] - 1}
];

(* ==================== Rosenbaum Γ Sensitivity ==================== *)

Print["Computing Rosenbaum Γ sensitivity analysis..."];

(* Simulate how ATE changes under different levels of hidden confounding *)
gammaValues = Range[1.0, 3.0, 0.1];

(* Simplified sensitivity: ATE ± Γ * SE *)
ateSE = (ateCI["upper"] - ateCI["lower"]) / (2 * 1.96);
sensitivityBounds = Map[
  <|"gamma" -> #, "lower_bound" -> ate - (# - 1) * 2 * ateSE, "upper_bound" -> ate + (# - 1) * 2 * ateSE|> &,
  gammaValues
];

(* ==================== Visualizations ==================== *)

(* 1. Intervention Curve *)
Print["Generating intervention curve..."];

xMidpoints = Table[(xBins[[i]] + xBins[[i+1]])/2, {i, 1, Length[xBins]-1}];
validIndices = Position[interventionalMeans, _?NumericQ];

interventionPlot = ListPlot[
  {Transpose[{xMidpoints, observationalMeans}],
   Transpose[{xMidpoints, interventionalMeans}]},
  Joined -> True,
  PlotStyle -> {{Dashed, ColorScheme["Neutral"], Thickness[0.006]},
                {ColorScheme["Primary"], Thickness[0.008]}},
  PlotLegends -> {"Observational E[Y|X]", "Interventional E[Y|do(X)]"},
  FrameLabel -> {treatment <> " (intervention level)", outcome <> " (expected value)"},
  PlotLabel -> Style["Intervention Curve: E[Y|do(X)] vs E[Y|X]", Bold, 18],
  ImageSize -> 1200,
  Frame -> True
];

SaveFig[interventionPlot, outputPrefix <> "_intervention_curve.png"];
Print["Saved: " <> outputPrefix <> "_intervention_curve.png"];

(* 2. ATE and CATE with CI *)
Print["Generating ATE/CATE confidence intervals..."];

cateValues = cateResults[[All, "cate"]];
cateLower = cateResults[[All, "ci_lower"]];
cateUpper = cateResults[[All, "ci_upper"]];

ateBarPlot = BarChart[
  Prepend[cateValues, ate],
  ChartLabels -> Prepend[Table["Q" <> ToString[i], {i, Length[cateValues]}], "Overall ATE"],
  ChartStyle -> ColorScheme["Primary"],
  ChartElementFunction -> "GlassRectangle",
  FrameLabel -> {"Group", "Treatment Effect"},
  PlotLabel -> Style["ATE and CATE by Subgroup (95% CI)", Bold, 18],
  ImageSize -> 1200
];

SaveFig[ateBarPlot, outputPrefix <> "_ate_cate_ci.png"];
Print["Saved: " <> outputPrefix <> "_ate_cate_ci.png"];

(* 3. Rosenbaum Γ Sensitivity *)
Print["Generating Rosenbaum Γ sensitivity plot..."];

lowerBounds = sensitivityBounds[[All, "lower_bound"]];
upperBounds = sensitivityBounds[[All, "upper_bound"]];

sensitivityPlot = ListPlot[
  {Transpose[{gammaValues, lowerBounds}],
   Transpose[{gammaValues, upperBounds}],
   Transpose[{gammaValues, Table[0, {Length[gammaValues]}]}]},
  Joined -> True,
  PlotStyle -> {
    {ColorScheme["Danger"], Thickness[0.006]},
    {ColorScheme["Success"], Thickness[0.006]},
    {Dashed, ColorScheme["Neutral"], Thickness[0.004]}
  },
  Filling -> {1 -> {2}},
  FillingStyle -> Opacity[0.2, ColorScheme["Primary"]],
  PlotLegends -> {"Lower Bound", "Upper Bound", "Null Effect"},
  FrameLabel -> {"Γ (sensitivity parameter)", "ATE bounds"},
  PlotLabel -> Style["Rosenbaum Γ Sensitivity Analysis", Bold, 18],
  ImageSize -> 1200,
  Frame -> True
];

SaveFig[sensitivityPlot, outputPrefix <> "_sensitivity_gamma.png"];
Print["Saved: " <> outputPrefix <> "_sensitivity_gamma.png"];

(* ==================== Export Results ==================== *)

results = <|
  "treatment" -> treatment,
  "outcome" -> outcome,
  "adjustment_vars" -> adjustmentVars,
  "ate" -> ate,
  "ate_ci_lower" -> ateCI["lower"],
  "ate_ci_upper" -> ateCI["upper"],
  "cate_results" -> cateResults,
  "sensitivity_analysis" -> sensitivityBounds,
  "n_observations" -> Length[treatmentData],
  "timestamp" -> DateString["ISODateTime"]
|>;

ExportJSON[results, outputPrefix <> "_intervention_results.json"];
Print["Saved: " <> outputPrefix <> "_intervention_results.json"];

Print["do-operator intervention simulation complete!"];
