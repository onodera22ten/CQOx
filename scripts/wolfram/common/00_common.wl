#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
Common Utilities for Wolfram ONE Visualization Scripts (Engine-Free)
Reference: /home/hirokionodera/CQO/可視化⑤.pdf

Provides shared functionality:
- ParseArgs: Command line argument parsing
- EnsureDir: Directory creation
- SaveFig: PNG/SVG export
- ReadCSV: CSV dataset loading
- BootstrapCI: Confidence interval calculation
- ExitError: Error handling with exit codes
*)

(* ==================== Argument Parsing ==================== *)

ParseArgs[args_List] := Module[{parsed = <||>, i = 1, key, val},
  While[i <= Length[args],
    If[StringStartsQ[args[[i]], "--"],
      key = StringDrop[args[[i]], 2];
      If[i < Length[args] && !StringStartsQ[args[[i+1]], "--"],
        val = args[[i+1]];
        i += 2;
        parsed[key] = val,
        (* Flag without value - set to True *)
        parsed[key] = True;
        i += 1
      ],
      (* Positional argument - skip or add to "positional" list *)
      i += 1
    ]
  ];
  parsed
];

(* ==================== Directory Management ==================== *)

EnsureDir[path_String] := Module[{dir},
  dir = If[StringEndsQ[path, "/"], path, DirectoryName[path]];
  If[dir != "" && !DirectoryQ[dir],
    CreateDirectory[dir, CreateIntermediateDirectories -> True]
  ]
];

(* ==================== Figure Export ==================== *)

SaveFig[fig_, path_String, opts___] := Module[{ext, pngPath, svgPath},
  EnsureDir[path];
  ext = ToLowerCase[FileExtension[path]];

  Which[
    ext == "png",
    Export[path, fig, "PNG", ImageSize -> 1200, ImageResolution -> 144, opts],

    ext == "svg",
    Export[path, fig, "SVG", ImageSize -> 1200, opts],

    ext == "gif",
    Export[path, fig, "GIF", "AnimationRepetitions" -> Infinity, opts],

    True,
    (* Default: export both PNG and SVG *)
    pngPath = StringReplace[path, RegularExpression["\\.[^.]+$"] -> ".png"];
    svgPath = StringReplace[path, RegularExpression["\\.[^.]+$"] -> ".svg"];
    Export[pngPath, fig, "PNG", ImageSize -> 1200, ImageResolution -> 144, opts];
    Export[svgPath, fig, "SVG", ImageSize -> 1200, opts];
  ]
];

(* ==================== CSV I/O ==================== *)

ReadCSV[path_String] := Module[{data},
  If[!FileExistsQ[path],
    ExitError["CSV file not found: " <> path]
  ];
  data = Import[path, "CSV"];
  If[Length[data] < 2,
    ExitError["CSV file has insufficient data: " <> path]
  ];
  data
];

ExportCSV[data_, path_String] := Module[{},
  EnsureDir[path];
  Export[path, data, "CSV"]
];

(* ==================== JSON I/O ==================== *)

ReadJSON[path_String] := Module[{data},
  If[!FileExistsQ[path],
    ExitError["JSON file not found: " <> path]
  ];
  data = Import[path, "JSON"];
  data
];

ExportJSON[data_, path_String] := Module[{},
  EnsureDir[path];
  Export[path, data, "JSON", "Compact" -> False]
];

(* ==================== Statistical Utilities ==================== *)

BootstrapCI[data_List, statFunc_, opts___] := Module[
  {nboot, alpha, level, boot, estimates, lower, upper},

  nboot = OptionValue[{opts}, "Bootstraps", 1000];
  level = OptionValue[{opts}, "Level", 0.95];
  alpha = 1 - level;

  (* Bootstrap resampling *)
  boot = Table[
    statFunc[RandomChoice[data, Length[data]]],
    {nboot}
  ];

  estimates = Sort[boot];
  lower = Quantile[estimates, alpha/2];
  upper = Quantile[estimates, 1 - alpha/2];

  <|"lower" -> lower, "upper" -> upper, "mean" -> Mean[estimates]|>
];

StandardError[data_List] := StandardDeviation[data] / Sqrt[Length[data]];

(* ==================== Error Handling ==================== *)

ExitError[msg_String, code_Integer: 1] := (
  WriteString["stderr", "ERROR: " <> msg <> "\n"];
  Exit[code];
);

(* ==================== Graph Utilities ==================== *)

(* Convert edge list to Graph object *)
EdgeListToGraph[edges_List] := Module[{vertexList, edgeRules},
  edgeRules = Map[DirectedEdge[#[[1]], #[[2]]] &, edges];
  vertexList = Union[Flatten[edges[[All, {1, 2}]]]];
  Graph[vertexList, edgeRules]
];

(* Generate synthetic DAG for demo mode *)
GenerateDemoDAG[n_Integer: 10, p_: 0.3] := Module[
  {vertices, edges, i, j},

  vertices = Table["X" <> ToString[i], {i, n}];
  edges = {};

  (* Generate DAG by only allowing edges from lower to higher indices *)
  Do[
    Do[
      If[RandomReal[] < p,
        AppendTo[edges, {vertices[[i]], vertices[[j]], RandomReal[{-1, 1}]}]
      ],
      {j, i + 1, n}
    ],
    {i, 1, n - 1}
  ];

  edges
];

(* ==================== Color Schemes (SSOT) ==================== *)

ColorScheme = <|
  "Primary" -> RGBColor["#3B82F6"],      (* Blue *)
  "Secondary" -> RGBColor["#8B5CF6"],    (* Purple *)
  "Success" -> RGBColor["#10B981"],      (* Green *)
  "Warning" -> RGBColor["#F59E0B"],      (* Amber *)
  "Danger" -> RGBColor["#EF4444"],       (* Red *)
  "Info" -> RGBColor["#06B6D4"],         (* Cyan *)
  "Neutral" -> RGBColor["#6B7280"],      (* Gray *)
  "Background" -> RGBColor["#F9FAFB"],   (* Light gray *)
  "Text" -> RGBColor["#1F2937"]          (* Dark gray *)
|>;

(* ==================== Thresholds (SSOT) ==================== *)

Thresholds = <|
  "SMD" -> 0.1,
  "SMDIdeal" -> 0.05,
  "IVFWeak" -> 10.0,
  "IVFStrong" -> 20.0,
  "OverlapMin" -> 0.1,
  "OverlapMax" -> 0.9,
  "TStatMin" -> 2.0,
  "PValueMax" -> 0.05,
  "CalibrationSlope" -> 1.0,
  "CalibrationECE" -> 0.1
|>;

Print["Common utilities loaded successfully."];
