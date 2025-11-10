#!/usr/bin/env wolframscript
(* ::Package:: *)

(*
Causal Surface 3D Visualization
Visualizes treatment effect across 2D covariate space as 3D surface
*)

(* Parse command line arguments *)
args = Rest[$ScriptCommandLine];
If[Length[args] < 3,
  Print["Usage: causal_surface_3d.wls <data_path> <output_dir> <mapping_json>"];
  Exit[1];
];

dataPath = args[[1]];
outputDir = args[[2]];
mappingJson = ImportString[args[[3]], "JSON"];

Print["[CausalSurface] Starting 3D surface generation"];
Print["[CausalSurface] Data: ", dataPath];

(* Load data *)
data = Import[dataPath, "Dataset"];
Print["[CausalSurface] Loaded ", Length[data], " rows"];

(* Extract columns from mapping *)
yCol = mappingJson["y"];
treatmentCol = mappingJson["treatment"];
Print["[CausalSurface] Outcome: ", yCol];
Print["[CausalSurface] Treatment: ", treatmentCol];

(* Get covariates (first 2 numeric columns that aren't y or treatment) *)
numericCols = Select[Keys[Normal[data[[1]]]],
  NumericQ[Normal[data[#]][[1]]] && # != yCol && # != treatmentCol &
];

If[Length[numericCols] < 2,
  Print["[CausalSurface] ERROR: Need at least 2 covariates for 3D surface"];
  Exit[1];
];

xCovariate = numericCols[[1]];
yCovariate = numericCols[[2]];
Print["[CausalSurface] X covariate: ", xCovariate];
Print["[CausalSurface] Y covariate: ", yCovariate];

(* Extract data *)
dataTable = Normal[data[All, {xCovariate, yCovariate, yCol, treatmentCol}]];
dataTable = Map[Values, dataTable];

(* Separate treatment and control groups *)
treatmentVals = Union[dataTable[[All, 4]]];
If[Length[treatmentVals] != 2,
  Print["[CausalSurface] Warning: Expected binary treatment, found ", Length[treatmentVals], " values"];
];

treated = Select[dataTable, #[[4]] == treatmentVals[[1]] &];
control = Select[dataTable, #[[4]] == treatmentVals[[2]] &];

Print["[CausalSurface] Treated: ", Length[treated], " samples"];
Print["[CausalSurface] Control: ", Length[control], " samples"];

(* Create grid for surface estimation *)
xRange = {Min[dataTable[[All, 1]]], Max[dataTable[[All, 1]]]};
yRange = {Min[dataTable[[All, 2]]], Max[dataTable[[All, 2]]]};

gridSize = 30;
xGrid = Range[xRange[[1]], xRange[[2]], (xRange[[2]] - xRange[[1]]) / gridSize];
yGrid = Range[yRange[[1]], yRange[[2]], (yRange[[2]] - yRange[[1]]) / gridSize];

Print["[CausalSurface] Creating ", gridSize, "x", gridSize, " grid"];

(* Estimate ATE at each grid point using local regression *)
ateGrid = Table[
  (* Find nearby points *)
  bandwidth = (xRange[[2]] - xRange[[1]]) / 5;

  nearbyTreated = Select[treated,
    Norm[{#[[1]] - x, #[[2]] - y}] < bandwidth &
  ];
  nearbyControl = Select[control,
    Norm[{#[[1]] - x, #[[2]] - y}] < bandwidth &
  ];

  (* Compute local ATE *)
  If[Length[nearbyTreated] > 5 && Length[nearbyControl] > 5,
    Mean[nearbyTreated[[All, 3]]] - Mean[nearbyControl[[All, 3]]],
    0
  ],
  {x, xGrid}, {y, yGrid}
];

(* Create 3D surface plot *)
Print["[CausalSurface] Generating 3D surface..."];

surface3D = ListPlot3D[ateGrid,
  DataRange -> {xRange, yRange},
  ColorFunction -> "TemperatureMap",
  ColorFunctionScaling -> True,
  Mesh -> 15,
  MeshStyle -> Directive[Thin, Gray, Opacity[0.3]],
  PlotLegends -> Automatic,
  AxesLabel -> {xCovariate, yCovariate, "ATE"},
  PlotLabel -> "Causal Effect Surface",
  Boxed -> False,
  BoxRatios -> {1, 1, 0.6},
  ViewPoint -> {1.3, -2.4, 2},
  ImageSize -> Large,
  PlotTheme -> "Scientific"
];

outputSurface = FileNameJoin[{outputDir, "causal_surface_3d.png"}];
Export[outputSurface, surface3D, "PNG", ImageSize -> 1400];
Print["[CausalSurface] Saved 3D surface: ", outputSurface];

(* Create contour plot (2D view) *)
Print["[CausalSurface] Generating contour plot..."];

contourPlot = ListContourPlot[ateGrid,
  DataRange -> {xRange, yRange},
  ColorFunction -> "TemperatureMap",
  Contours -> 15,
  ContourLabels -> True,
  PlotLegends -> Automatic,
  FrameLabel -> {xCovariate, yCovariate},
  PlotLabel -> "Causal Effect Contours (2D View)",
  ImageSize -> Large,
  PlotTheme -> "Detailed"
];

outputContour = FileNameJoin[{outputDir, "causal_surface_contour.png"}];
Export[outputContour, contourPlot, "PNG", ImageSize -> 1200];
Print["[CausalSurface] Saved contour plot: ", outputContour];

(* Create rotating animation *)
Print["[CausalSurface] Generating rotation animation..."];

frames = Table[
  Show[surface3D, ViewPoint -> {Cos[angle], Sin[angle], 2}],
  {angle, 0, 2*Pi, 2*Pi/36}
];

outputAnimation = FileNameJoin[{outputDir, "causal_surface_rotation.gif"}];
Export[outputAnimation, frames, "GIF", "DisplayDurations" -> 0.1];
Print["[CausalSurface] Saved animation: ", outputAnimation];

(* Interactive HTML *)
Print["[CausalSurface] Generating interactive HTML..."];

htmlContent = ExportString[
  Manipulate[
    Show[ListPlot3D[ateGrid,
      DataRange -> {xRange, yRange},
      ColorFunction -> "TemperatureMap",
      Mesh -> meshCount,
      ViewPoint -> {Cos[viewAngle], Sin[viewAngle], viewHeight},
      PlotLabel -> "Causal Effect Surface (Interactive)",
      AxesLabel -> {xCovariate, yCovariate, "ATE"},
      ImageSize -> Large
    ]],
    {{viewAngle, Pi/4, "Rotation"}, 0, 2*Pi},
    {{viewHeight, 2, "Height"}, 0.5, 3},
    {{meshCount, 15, "Mesh Density"}, 5, 30, 1}
  ],
  "HTML"
];

outputHTML = FileNameJoin[{outputDir, "causal_surface_interactive.html"}];
Export[outputHTML, htmlContent, "Text"];
Print["[CausalSurface] Saved interactive HTML: ", outputHTML];

(* Summary statistics *)
stats = <|
  "mean_ate" -> Mean[Flatten[ateGrid]],
  "max_ate" -> Max[Flatten[ateGrid]],
  "min_ate" -> Min[Flatten[ateGrid]],
  "ate_variance" -> Variance[Flatten[ateGrid]],
  "x_covariate" -> xCovariate,
  "y_covariate" -> yCovariate,
  "grid_size" -> gridSize
|>;

statsFile = FileNameJoin[{outputDir, "causal_surface_stats.json"}];
Export[statsFile, stats, "JSON"];
Print["[CausalSurface] Saved statistics: ", statsFile];

Print["[CausalSurface] Complete!"];
Exit[0];
