#!/usr/bin/env wolframscript
(* ::Package:: *)

(*
Time Series Causal Effect Animation
Creates animated visualization of treatment effect evolution over time
*)

(* Parse command line arguments *)
args = Rest[$ScriptCommandLine];
If[Length[args] < 3,
  Print["Usage: timeseries_animation.wls <data_path> <output_dir> <mapping_json>"];
  Exit[1];
];

dataPath = args[[1]];
outputDir = args[[2]];
mappingJson = ImportString[args[[3]], "JSON"];

Print["[TimeSeriesAnimation] Starting time series animation"];
Print["[TimeSeriesAnimation] Data: ", dataPath];

(* Load data *)
data = Import[dataPath, "Dataset"];
Print["[TimeSeriesAnimation] Loaded ", Length[data], " rows"];

(* Extract columns from mapping *)
yCol = mappingJson["y"];
treatmentCol = mappingJson["treatment"];
timeCol = mappingJson["time"];

If[timeCol == Null || timeCol == "",
  Print["[TimeSeriesAnimation] ERROR: No time column specified"];
  Exit[1];
];

Print["[TimeSeriesAnimation] Outcome: ", yCol];
Print["[TimeSeriesAnimation] Treatment: ", treatmentCol];
Print["[TimeSeriesAnimation] Time: ", timeCol];

(* Extract and sort by time *)
dataTable = Normal[data[All, {timeCol, treatmentCol, yCol}]];
dataTable = Map[Values, dataTable];
dataTable = SortBy[dataTable, First];

(* Get unique time periods *)
timePeriods = Sort[Union[dataTable[[All, 1]]]];
Print["[TimeSeriesAnimation] Time periods: ", Length[timePeriods]];

(* Get treatment values *)
treatmentVals = Union[dataTable[[All, 2]]];
Print["[TimeSeriesAnimation] Treatment groups: ", treatmentVals];

(* Calculate ATE at each time period *)
ateByTime = Table[
  periodData = Select[dataTable, #[[1]] == t &];

  treated = Select[periodData, #[[2]] == treatmentVals[[1]] &];
  control = Select[periodData, #[[2]] == treatmentVals[[2]] &];

  If[Length[treated] > 0 && Length[control] > 0,
    {t, Mean[treated[[All, 3]]] - Mean[control[[All, 3]]]},
    {t, 0}
  ],
  {t, timePeriods}
];

Print["[TimeSeriesAnimation] Computed ATE for ", Length[ateByTime], " time periods"];

(* Create cumulative ATE plot frames *)
Print["[TimeSeriesAnimation] Generating animation frames..."];

maxATE = Max[Abs[ateByTime[[All, 2]]]];
yRange = {-maxATE * 1.2, maxATE * 1.2};

frames = Table[
  currentData = Take[ateByTime, Min[t, Length[ateByTime]]];

  plot = ListPlot[currentData,
    Joined -> True,
    PlotStyle -> Directive[Thick, Blue],
    Filling -> Axis,
    FillingStyle -> Directive[Opacity[0.3], LightBlue],
    PlotRange -> {{timePeriods[[1]], timePeriods[[-1]]}, yRange},
    PlotLabel -> Style["ATE Over Time (Period " <> ToString[t] <> " / " <> ToString[Length[timePeriods]] <> ")", 16, Bold],
    AxesLabel -> {"Time", "ATE"},
    GridLines -> {None, {0}},
    GridLinesStyle -> Directive[Red, Dashed],
    ImageSize -> Large,
    PlotMarkers -> {Automatic, 10},
    Frame -> True
  ];

  (* Add current ATE value annotation *)
  If[t <= Length[ateByTime],
    Show[plot,
      Epilog -> {
        Red, PointSize[0.02],
        Point[currentData[[-1]]],
        Text[Style["ATE: " <> ToString[NumberForm[currentData[[-1, 2]], {4, 2}]], 12, Bold],
             currentData[[-1]] + {0, maxATE * 0.1}]
      }
    ],
    plot
  ],
  {t, 1, Length[timePeriods]}
];

Print["[TimeSeriesAnimation] Generated ", Length[frames], " frames"];

(* Export as GIF animation *)
outputGIF = FileNameJoin[{outputDir, "ate_timeseries_animation.gif"}];
Export[outputGIF, frames, "GIF", "DisplayDurations" -> 0.15];
Print["[TimeSeriesAnimation] Saved GIF animation: ", outputGIF];

(* Export as MP4 video (higher quality) *)
outputMP4 = FileNameJoin[{outputDir, "ate_timeseries_animation.mp4"}];
Export[outputMP4, frames, "MP4", "FrameRate" -> 10];
Print["[TimeSeriesAnimation] Saved MP4 video: ", outputMP4];

(* Create static plot (final frame) *)
Print["[TimeSeriesAnimation] Generating static summary..."];

finalPlot = Show[
  ListPlot[ateByTime,
    Joined -> True,
    PlotStyle -> Directive[Thick, Blue],
    Filling -> Axis,
    FillingStyle -> Directive[Opacity[0.3], LightBlue],
    PlotLabel -> Style["Treatment Effect Evolution Over Time", 16, Bold],
    AxesLabel -> {Style[timeCol, 12, Bold], Style["ATE", 12, Bold]},
    GridLines -> {None, {0}},
    GridLinesStyle -> Directive[Red, Dashed, Thick],
    ImageSize -> Large,
    PlotMarkers -> {Automatic, 8},
    Frame -> True,
    FrameStyle -> Directive[Black, Thick]
  ],

  (* Add statistical annotations *)
  Graphics[{
    (* Mean line *)
    Green, Dashed, Thick,
    Line[{{timePeriods[[1]], Mean[ateByTime[[All, 2]]]},
          {timePeriods[[-1]], Mean[ateByTime[[All, 2]]]}}],

    (* Legend *)
    Inset[
      Framed[
        Column[{
          Style["Statistics:", 11, Bold],
          "Mean ATE: " <> ToString[NumberForm[Mean[ateByTime[[All, 2]]], {4, 2}]],
          "Max ATE: " <> ToString[NumberForm[Max[ateByTime[[All, 2]]], {4, 2}]],
          "Min ATE: " <> ToString[NumberForm[Min[ateByTime[[All, 2]]], {4, 2}]],
          "Std Dev: " <> ToString[NumberForm[StandardDeviation[ateByTime[[All, 2]]], {4, 2}]]
        }, Alignment -> Left],
        Background -> LightYellow,
        RoundingRadius -> 5
      ],
      Scaled[{0.8, 0.8}]
    ]
  }]
];

outputStatic = FileNameJoin[{outputDir, "ate_timeseries_static.png"}];
Export[outputStatic, finalPlot, "PNG", ImageSize -> 1400];
Print["[TimeSeriesAnimation] Saved static plot: ", outputStatic];

(* Interactive HTML with slider *)
Print["[TimeSeriesAnimation] Generating interactive HTML..."];

htmlContent = ExportString[
  Manipulate[
    currentData = Take[ateByTime, Min[period, Length[ateByTime]]];

    ListPlot[currentData,
      Joined -> True,
      PlotStyle -> Directive[Thick, Blue],
      Filling -> Axis,
      FillingStyle -> Directive[Opacity[0.3], LightBlue],
      PlotRange -> {{timePeriods[[1]], timePeriods[[-1]]}, yRange},
      PlotLabel -> "ATE Over Time (Interactive)",
      AxesLabel -> {"Time", "ATE"},
      GridLines -> {None, {0}},
      ImageSize -> Large,
      PlotMarkers -> {Automatic, 10}
    ],
    {{period, 1, "Time Period"}, 1, Length[timePeriods], 1, Appearance -> "Labeled"}
  ],
  "HTML"
];

outputHTML = FileNameJoin[{outputDir, "ate_timeseries_interactive.html"}];
Export[outputHTML, htmlContent, "Text"];
Print["[TimeSeriesAnimation] Saved interactive HTML: ", outputHTML];

(* Export statistics *)
stats = <|
  "num_periods" -> Length[timePeriods],
  "mean_ate" -> Mean[ateByTime[[All, 2]]],
  "max_ate" -> Max[ateByTime[[All, 2]]],
  "min_ate" -> Min[ateByTime[[All, 2]]],
  "std_dev_ate" -> StandardDeviation[ateByTime[[All, 2]]],
  "ate_trend" -> If[ateByTime[[-1, 2]] > ateByTime[[1, 2]], "increasing", "decreasing"],
  "time_periods" -> timePeriods
|>;

statsFile = FileNameJoin[{outputDir, "ate_timeseries_stats.json"}];
Export[statsFile, stats, "JSON"];
Print["[TimeSeriesAnimation] Saved statistics: ", statsFile];

Print["[TimeSeriesAnimation] Complete!"];
Exit[0];
