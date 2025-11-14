#!/usr/bin/env wolframscript
(* ::Package:: *)

(*
 * Marketing ROI 3D Surface Visualization
 *
 * Purpose: NASA/WPP-level 3D visualization of ROI across channels and budget levels
 *
 * Inputs:
 *   - channels: List of marketing channels
 *   - budgets: Range of budget allocations
 *   - roi_matrix: ROI values for each channel × budget combination
 *
 * Output: Interactive 3D surface plot with gradient coloring
 *)

(* Load data from JSON *)
dataPath = If[$ScriptCommandLine[[2]] =!= Null,
              $ScriptCommandLine[[2]],
              "data/marketing_roi_optimization_results.json"];

outputPath = If[$ScriptCommandLine[[3]] =!= Null,
               $ScriptCommandLine[[3]],
               "visualizations/marketing_roi/roi_3d_surface.png"];

(* Parse JSON data *)
jsonData = Import[dataPath, "RawJSON"];

(* Extract optimization results *)
channels = Keys[jsonData["phase1"]["budget_optimization"]["current_allocation"]];
roiData = jsonData["phase1"]["roi_results"];

(* Generate budget range (50% to 200% of current) *)
budgetMultipliers = Range[0.5, 2.0, 0.1];

(* Create ROI surface data *)
(* ROI(channel, budget) = base_ROI × (1 - saturation_effect) *)
roiSurfaceData = Table[
  {
    channelIdx,
    budgetMult,
    (* ROI with saturation effect: ROI decreases as budget increases *)
    roiData[[channels[[channelIdx]]]] * (1 - 0.3 * Log[budgetMult + 1])
  },
  {channelIdx, 1, Length[channels]},
  {budgetMult, budgetMultipliers}
];

(* Create 3D surface plot *)
roi3DSurface = Plot3D[
  Evaluate[
    Interpolation[
      Flatten[roiSurfaceData, 1],
      InterpolationOrder -> 2
    ][x, y]
  ],
  {x, 1, Length[channels]},
  {y, 0.5, 2.0},

  (* Styling *)
  ColorFunction -> Function[{x, y, z},
    ColorData["TemperatureMap"][Rescale[z, {-150, 50}]]
  ],
  ColorFunctionScaling -> False,

  (* Mesh and grid *)
  Mesh -> {Length[channels], 15},
  MeshStyle -> Directive[GrayLevel[0.3], Opacity[0.3]],

  (* Lighting *)
  Lighting -> {
    {"Ambient", White},
    {"Point", White, {2, 0, 2}},
    {"Point", LightBlue, {-2, -2, 2}}
  },

  (* Plot range *)
  PlotRange -> All,
  ClippingStyle -> None,

  (* Axes *)
  AxesLabel -> {
    Style["Channel Index", 14, Bold],
    Style["Budget Multiplier", 14, Bold],
    Style["ROI (%)", 14, Bold]
  },

  (* Ticks *)
  Ticks -> {
    Table[{i, channels[[i]]}, {i, 1, Length[channels]}],
    Automatic,
    Automatic
  },

  (* View angle *)
  ViewPoint -> {1.3, -2.4, 2.0},
  ViewAngle -> 35 Degree,

  (* Box ratios *)
  BoxRatios -> {1, 1, 0.6},

  (* Image size *)
  ImageSize -> 1200,

  (* Plot label *)
  PlotLabel -> Style[
    "Marketing ROI 3D Surface\nChannel × Budget Optimization",
    16, Bold, Black
  ],

  (* Background *)
  Background -> White,

  (* Frame *)
  Boxed -> True,
  BoxStyle -> Directive[Black, Thickness[0.002]]
];

(* Add contour lines at z=0 (break-even) *)
roi3DWithContour = Show[
  roi3DSurface,

  (* Zero ROI plane (break-even) *)
  Graphics3D[{
    Opacity[0.2],
    Red,
    Cuboid[{1, 0.5, -5}, {Length[channels], 2.0, 0}]
  }],

  (* Optimal region highlight *)
  Graphics3D[{
    Opacity[0.1],
    Green,
    Cuboid[{1, 0.5, 0}, {Length[channels], 1.2, 50}]
  }]
];

(* Export high-resolution image *)
Export[outputPath, roi3DWithContour,
  ImageResolution -> 300,
  Background -> White
];

Print["[WolframONE] Marketing ROI 3D Surface generated: " <> outputPath];

(* Generate interactive Manipulate version *)
manipulatePath = StringReplace[outputPath, ".png" -> "_interactive.nb"];

manipulateROI = Manipulate[
  Plot3D[
    Evaluate[
      Interpolation[Flatten[roiSurfaceData, 1], InterpolationOrder -> 2][x, y]
    ],
    {x, 1, Length[channels]},
    {y, 0.5, 2.0},

    ColorFunction -> Function[{x, y, z},
      ColorData[colorScheme][Rescale[z, {-150, 50}]]
    ],
    ColorFunctionScaling -> False,

    ViewPoint -> viewPoint,
    ViewAngle -> viewAngle Degree,

    Mesh -> meshDensity,
    MeshStyle -> Directive[GrayLevel[0.3], Opacity[meshOpacity]],

    PlotRange -> All,
    AxesLabel -> {"Channel", "Budget Multiplier", "ROI (%)"},
    BoxRatios -> {1, 1, 0.6},
    ImageSize -> 800,
    PlotLabel -> Style["Interactive Marketing ROI 3D Surface", 14, Bold]
  ],

  (* Controls *)
  {{viewPoint, {1.3, -2.4, 2.0}, "View Point"},
   {{1.3, -2.4, 2.0}, {-1.3, -2.4, 2.0}, {0, -3, 2.0}, {2, -1, 1.5}},
   ControlType -> PopupMenu},

  {{viewAngle, 35, "View Angle"}, 20, 60, 5, Appearance -> "Labeled"},

  {{colorScheme, "TemperatureMap", "Color Scheme"},
   {"TemperatureMap", "Rainbow", "DarkRainbow", "BlueGreenYellow", "SolarColors"},
   ControlType -> PopupMenu},

  {{meshDensity, {5, 15}, "Mesh Density"},
   {{3, 8}, {5, 15}, {10, 25}},
   ControlType -> PopupMenu},

  {{meshOpacity, 0.3, "Mesh Opacity"}, 0, 1, 0.1, Appearance -> "Labeled"},

  ControlPlacement -> Left,
  SaveDefinitions -> True
];

Export[manipulatePath, manipulateROI];

Print["[WolframONE] Interactive notebook generated: " <> manipulatePath];

(* Summary statistics *)
Print[""];
Print["=== ROI 3D Surface Statistics ==="];
Print["Channels: " <> ToString[Length[channels]]];
Print["Budget range: 50% - 200%"];
Print["Max ROI: " <> ToString[Max[Flatten[roiSurfaceData[[All, All, 3]]]]] <> "%"];
Print["Min ROI: " <> ToString[Min[Flatten[roiSurfaceData[[All, All, 3]]]]] <> "%"];
Print["Break-even regions: " <> ToString[
  Count[Flatten[roiSurfaceData[[All, All, 3]]], _?Positive] /
  Length[Flatten[roiSurfaceData[[All, All, 3]]]] * 100
] <> "% of surface"];
