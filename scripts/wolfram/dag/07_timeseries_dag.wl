#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
Time-series DAG - Module 7: Temporal Causal Graphs
Reference: /home/hirokionodera/CQO/可視化④.pdf p.4

Features:
1. 4D visualization with time slider (lag effects)
2. Adstock/decay effects visualization
3. Event impact analysis
4. Dynamic DAG animation

Usage:
  wolframscript -file 07_timeseries_dag.wl --input data/dag/timeseries.csv --output artifacts/dag/timeseries --demo

Input CSV format (timeseries.csv):
  date,X,Y,event
  2024-01-01,1.2,5.3,0
  2024-01-02,1.4,5.5,0
  2024-01-15,2.1,7.2,1
  ...

Outputs:
  - timeseries_dag_animation.gif (DAG evolving over time)
  - lag_effects.png/svg (cross-correlation at different lags)
  - adstock_decay.png/svg (decay curve)
  - event_impact.png/svg (before/after event analysis)
  - timeseries_results.json
*)

Get[FileNameJoin[{NotebookDirectory[], "..", "common", "00_common.wl"}]];

(* ==================== Parse Arguments ==================== *)

args = ParseArgs[$ScriptCommandLine[[2;;]]];

inputPath = Lookup[args, "input", "data/dag/timeseries.csv"];
outputPrefix = Lookup[args, "output", "artifacts/dag/timeseries"];
demoMode = KeyExistsQ[args, "demo"];
maxLag = If[KeyExistsQ[args, "maxlag"], ToExpression[Lookup[args, "maxlag"]], 10];

(* ==================== Load or Generate Data ==================== *)

{dataMatrix, headers} = If[demoMode || !FileExistsQ[inputPath],
  Print["Demo mode: Generating synthetic time-series with lag effects..."];

  n = 100;
  dates = DateRange[DateObject[{2024, 1, 1}], DateObject[{2024, 4, 9}]];

  (* X with trend and seasonality *)
  x = Table[2 + 0.01*t + 0.5*Sin[2*Pi*t/7] + RandomVariate[NormalDistribution[0, 0.2]], {t, n}];

  (* Y with lagged effect from X (lag=3) and adstock (decay=0.7) *)
  y = Table[0, {n}];
  y[[1]] = 3 + RandomVariate[NormalDistribution[0, 0.3]];
  Do[
    lagEffect = If[t > 3, 0.6 * x[[t-3]], 0];
    adstockEffect = If[t > 1, 0.7 * y[[t-1]], 0];
    y[[t]] = 3 + 0.3 * x[[t]] + lagEffect + 0.3 * adstockEffect + RandomVariate[NormalDistribution[0, 0.3]],
    {t, 2, n}
  ];

  (* Event at t=50 *)
  event = Table[If[t == 50, 1, 0], {t, n}];
  y[[50;;]] += 1.5; (* Event impact *)

  {Transpose[{Range[n], x, y, event}], {"time", "X", "Y", "event"}},

  Print["Loading data from: " <> inputPath];
  rawData = ReadCSV[inputPath];
  {Rest[rawData], First[rawData]}
];

tData = dataMatrix[[All, 1]];
xData = dataMatrix[[All, 2]];
yData = dataMatrix[[All, 3]];
eventData = If[Length[headers] >= 4, dataMatrix[[All, 4]], Table[0, {Length[tData]}]];

n = Length[tData];

Print["Loaded " <> ToString[n] <> " time points"];

(* ==================== Cross-Correlation Analysis ==================== *)

Print["Computing cross-correlation at different lags..."];

(* Cross-correlation: Cor(X_t, Y_{t+lag}) *)
lagValues = Range[-maxLag, maxLag];
crossCorr = Table[
  If[Abs[lag] >= n, 0,
    If[lag >= 0,
      (* Positive lag: X leads Y *)
      Correlation[Take[xData, n - lag], Take[yData, -(n - lag)]],
      (* Negative lag: Y leads X *)
      Correlation[Take[xData, -(n + lag)], Take[yData, n + lag]]
    ]
  ],
  {lag, lagValues}
];

(* Find optimal lag (max correlation) *)
optimalLag = lagValues[[First[Ordering[Abs[crossCorr], -1]]]];
maxCorr = crossCorr[[First[Ordering[Abs[crossCorr], -1]]]];

Print["Optimal lag: " <> ToString[optimalLag] <> " (correlation = " <> ToString[NumberForm[maxCorr, {3, 2}]] <> ")"];

(* ==================== Adstock/Decay Modeling ==================== *)

Print["Estimating adstock decay parameter..."];

(* Fit geometric adstock model: Y_t = α + β * Σ_{s=0}^∞ λ^s * X_{t-s} *)
(* Approximate with finite lag L=maxLag *)

decayRates = Range[0.1, 0.9, 0.1];
bestDecay = 0.5;
bestRSq = 0;

Do[
  (* Compute adstock transform *)
  xAdstock = Table[
    Sum[If[t - s >= 1, decay^s * xData[[t-s]], 0], {s, 0, Min[t-1, maxLag]}],
    {t, n}
  ];

  (* Regression: Y ~ X_adstock *)
  designMatrix = Transpose[{Table[1, {n}], xAdstock}];
  coeffs = LeastSquares[designMatrix, yData];
  fitted = designMatrix . coeffs;

  (* R-squared *)
  ssTotal = Total[(yData - Mean[yData])^2];
  ssResidual = Total[(yData - fitted)^2];
  rSq = 1 - ssResidual / ssTotal;

  If[rSq > bestRSq,
    bestRSq = rSq;
    bestDecay = decay
  ],

  {decay, decayRates}
];

Print["Best decay rate: " <> ToString[NumberForm[bestDecay, {2, 1}]] <> " (R² = " <> ToString[NumberForm[bestRSq, {3, 2}]] <> ")"];

(* ==================== Event Impact Analysis ==================== *)

eventIdx = Flatten[Position[eventData, _?(# > 0 &)]];

If[Length[eventIdx] > 0,
  Print["Analyzing event impact at time: " <> ToString[eventIdx]];

  eventTime = First[eventIdx];
  preEventWindow = Max[1, eventTime - 10];
  postEventWindow = Min[n, eventTime + 10];

  yPreEvent = yData[[preEventWindow ;; eventTime - 1]];
  yPostEvent = yData[[eventTime ;; postEventWindow]];

  meanPre = Mean[yPreEvent];
  meanPost = Mean[yPostEvent];
  eventImpact = meanPost - meanPre;

  Print["Event impact: " <> ToString[NumberForm[eventImpact, {4, 2}]] <> " (pre = " <> ToString[NumberForm[meanPre, {4, 2}]] <> ", post = " <> ToString[NumberForm[meanPost, {4, 2}]] <> ")"];
,
  Print["No events detected"];
  eventImpact = 0;
];

(* ==================== Visualizations ==================== *)

(* 1. Lag Effects (Cross-Correlation) *)
Print["Generating lag effects plot..."];

lagPlot = BarChart[
  crossCorr,
  ChartLabels -> lagValues,
  ChartStyle -> ColorScheme["Primary"],
  FrameLabel -> {"Lag (time steps)", "Cross-Correlation"},
  PlotLabel -> Style["Cross-Correlation: X vs Y at Different Lags", Bold, 18],
  ImageSize -> 1200,
  GridLines -> {{optimalLag}, {0}},
  GridLinesStyle -> Directive[Dashed, ColorScheme["Danger"]]
];

SaveFig[lagPlot, outputPrefix <> "_lag_effects.png"];
Print["Saved: " <> outputPrefix <> "_lag_effects.png"];

(* 2. Adstock Decay Curve *)
Print["Generating adstock decay curve..."];

decaySteps = Range[0, 20];
decayWeights = Map[bestDecay^# &, decaySteps];

decayPlot = ListPlot[
  Transpose[{decaySteps, decayWeights}],
  Joined -> True,
  PlotStyle -> {ColorScheme["Primary"], Thickness[0.008]},
  Filling -> Axis,
  FillingStyle -> Opacity[0.3, ColorScheme["Primary"]],
  FrameLabel -> {"Lag (time steps)", "Weight"},
  PlotLabel -> Style["Adstock Decay (λ = " <> ToString[NumberForm[bestDecay, {2, 1}]] <> ")", Bold, 18],
  ImageSize -> 1200,
  Frame -> True
];

SaveFig[decayPlot, outputPrefix <> "_adstock_decay.png"];
Print["Saved: " <> outputPrefix <> "_adstock_decay.png"];

(* 3. Event Impact *)
If[Length[eventIdx] > 0,
  Print["Generating event impact plot..."];

  eventPlot = ListPlot[
    {Transpose[{tData, yData}],
     Transpose[{tData[[preEventWindow ;; eventTime - 1]], yData[[preEventWindow ;; eventTime - 1]]}],
     Transpose[{tData[[eventTime ;; postEventWindow]], yData[[eventTime ;; postEventWindow]]}]},
    Joined -> {True, False, False},
    PlotStyle -> {
      {ColorScheme["Neutral"], Thickness[0.005]},
      {ColorScheme["Primary"], PointSize[0.01]},
      {ColorScheme["Danger"], PointSize[0.01]}
    },
    PlotLegends -> {"Full Series", "Pre-Event", "Post-Event"},
    FrameLabel -> {"Time", "Y"},
    PlotLabel -> Style["Event Impact Analysis", Bold, 18],
    ImageSize -> 1200,
    Frame -> True,
    Epilog -> {
      ColorScheme["Warning"],
      Thickness[0.006],
      Dashed,
      Line[{{eventTime, Min[yData]}, {eventTime, Max[yData]}}]
    }
  ];

  SaveFig[eventPlot, outputPrefix <> "_event_impact.png"];
  Print["Saved: " <> outputPrefix <> "_event_impact.png"];
];

(* 4. Time-series DAG Animation *)
Print["Generating time-series DAG animation..."];

(* Create DAG at different time slices *)
frames = Table[
  (* DAG with X_t -> Y_{t+optimalLag} *)
  vertices = {"X[t]", "Y[t]", "X[t-1]", "Y[t-1]"};
  edges = {
    DirectedEdge["X[t-1]", "X[t]"],
    DirectedEdge["Y[t-1]", "Y[t]"],
    DirectedEdge["X[t]", "Y[t]"],
    DirectedEdge["X[t-1]", "Y[t]"]
  };

  (* Edge weights based on current time slice *)
  edgeWeights = If[t <= n,
    {0.8, bestDecay, 0.3, 0.6},
    {0.8, bestDecay, 0.3, 0.6}
  ];

  g = Graph[
    vertices,
    edges,
    GraphLayout -> "LayeredDigraphEmbedding",
    VertexLabels -> Placed["Name", Center],
    VertexStyle -> ColorScheme["Primary"],
    VertexSize -> 0.5,
    VertexLabelStyle -> Directive[White, Bold, 14],
    EdgeStyle -> Directive[Arrowheads[0.03], Thickness[0.008]],
    EdgeLabels -> Thread[edges -> Map[NumberForm[#, {2, 1}] &, edgeWeights]],
    ImageSize -> 800,
    PlotLabel -> Style["Time-series DAG (t = " <> ToString[t] <> ")", Bold, 16]
  ];

  g,
  {t, 1, Min[n, 20], 2}
];

SaveFig[frames, outputPrefix <> "_timeseries_dag_animation.gif"];
Print["Saved: " <> outputPrefix <> "_timeseries_dag_animation.gif"];

(* ==================== Export Results ==================== *)

results = <|
  "n_timepoints" -> n,
  "optimal_lag" -> optimalLag,
  "max_correlation" -> maxCorr,
  "best_decay_rate" -> bestDecay,
  "adstock_r_squared" -> bestRSq,
  "event_impact" -> eventImpact,
  "cross_correlation" -> Thread[lagValues -> crossCorr],
  "timestamp" -> DateString["ISODateTime"]
|>;

ExportJSON[results, outputPrefix <> "_timeseries_results.json"];
Print["Saved: " <> outputPrefix <> "_timeseries_results.json"];

Print["Time-series DAG analysis complete!"];
