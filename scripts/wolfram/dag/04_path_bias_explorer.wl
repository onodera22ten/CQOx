#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
Path & Bias Explorer - Module 4: Identify Biasing Paths
Reference: /home/hirokionodera/CQO/可視化④.pdf p.3

Features:
1. Enumerate all paths from treatment to outcome
2. Classify paths (direct, backdoor, mediated)
3. Detect M-bias and other common bias structures
4. Auto-warning for problematic patterns
5. Highlight biasing paths in DAG visualization

Common bias patterns:
- M-bias: Z <- U1 -> X, Z <- U2 -> Y (adjusting for Z creates bias)
- Butterfly bias: Similar collider bias structure
- Overcontrol bias: Adjusting for mediator

Usage:
  wolframscript -file 04_path_bias_explorer.wl --input data/dag/edges.csv --treatment X --outcome Y --output artifacts/dag/path_bias --demo

Outputs:
  - path_enumeration.json (all paths with classifications)
  - bias_warnings.json (detected bias patterns)
  - dag_paths_highlighted.png/svg (visualization with path types)
  - m_bias_warning.png/svg (if M-bias detected)
*)

Get[FileNameJoin[{NotebookDirectory[], "..", "common", "00_common.wl"}]];

(* ==================== Parse Arguments ==================== *)

args = ParseArgs[$ScriptCommandLine[[2;;]]];

inputPath = Lookup[args, "input", "data/dag/edges.csv"];
treatment = Lookup[args, "treatment", "X1"];
outcome = Lookup[args, "outcome", "Y"];
outputPrefix = Lookup[args, "output", "artifacts/dag/path_bias"];
demoMode = KeyExistsQ[args, "demo"];

(* ==================== Load or Generate DAG ==================== *)

edges = If[demoMode || !FileExistsQ[inputPath],
  Print["Demo mode: Generating DAG with M-bias structure..."];
  (* Classic M-bias: U1->Z, U2->Z, U1->X, U2->Y, X->Y *)
  {
    {"U1", "Z", 0.6},
    {"U2", "Z", 0.7},
    {"U1", "X1", 0.8},
    {"U2", "Y", 0.75},
    {"X1", "M", 0.7},
    {"M", "Y", 0.65}
  },

  Print["Loading edges from: " <> inputPath];
  data = ReadCSV[inputPath];
  Rest[data]
];

vertices = Union[Flatten[edges[[All, {1, 2}]]]];
edgeRules = Map[DirectedEdge[#[[1]], #[[2]]] &, edges];

g = Graph[vertices, edgeRules, GraphLayout -> "LayeredDigraphEmbedding"];

Print["Analyzing path structure for: " <> treatment <> " -> " <> outcome];

(* ==================== Helper Functions ==================== *)

(* Find all paths between two vertices (including undirected) *)
FindAllPathsUndirected[graph_, start_, end_] := Module[{ugraph},
  ugraph = UndirectedGraph[graph];
  FindPath[ugraph, start, end, Infinity, All]
];

(* Classify path type *)
ClassifyPath[graph_, path_List, treatment_, outcome_] := Module[
  {isDirected, startsBackdoor, hasCollider},

  (* Check if path is a directed path from treatment to outcome *)
  isDirected = AllTrue[
    Partition[path, 2, 1],
    EdgeQ[graph, DirectedEdge[#[[1]], #[[2]]]] &
  ];

  (* Check if path starts with arrow into treatment (backdoor) *)
  startsBackdoor = Length[path] > 1 && EdgeQ[graph, DirectedEdge[path[[2]], path[[1]]]];

  (* Check for colliders (v <- ... <- -> ... -> w structure) *)
  hasCollider = False;
  If[Length[path] >= 3,
    Do[
      (* Check if vertex i is a collider: both arrows point into it *)
      If[EdgeQ[graph, DirectedEdge[path[[i-1]], path[[i]]]] &&
         EdgeQ[graph, DirectedEdge[path[[i+1]], path[[i]]]],
        hasCollider = True; Break[]
      ],
      {i, 2, Length[path] - 1}
    ]
  ];

  Which[
    isDirected, "direct",
    startsBackdoor, "backdoor",
    hasCollider, "collider",
    True, "other"
  ]
];

(* Detect M-bias pattern *)
DetectMBias[graph_] := Module[{colliders, mBiasPatterns = {}},
  (* Find colliders: vertices with 2+ incoming edges *)
  colliders = Select[VertexList[graph], VertexInDegree[graph, #] >= 2 &];

  (* For each collider, check if parents lead to distinct variables *)
  Do[
    parents = Cases[EdgeList[graph], DirectedEdge[_, collider] :> First[#]] & /@ EdgeList[graph];
    If[Length[parents] >= 2,
      (* Check if adjusting for this collider would induce M-bias *)
      AppendTo[mBiasPatterns, <|
        "collider" -> collider,
        "parents" -> parents,
        "type" -> "M-bias",
        "warning" -> "Adjusting for " <> ToString[collider] <> " may induce bias"
      |>]
    ],
    {collider, colliders}
  ];

  mBiasPatterns
];

(* ==================== Path Enumeration ==================== *)

Print["Enumerating all paths from " <> treatment <> " to " <> outcome <> "..."];

allPaths = FindAllPathsUndirected[g, treatment, outcome];

Print["Found " <> ToString[Length[allPaths]] <> " paths"];

(* Classify each path *)
pathClassifications = Map[
  <|
    "path" -> #,
    "length" -> Length[#] - 1,
    "type" -> ClassifyPath[g, #, treatment, outcome]
  |> &,
  allPaths
];

(* Count by type *)
pathCounts = GroupBy[pathClassifications, #["type"] &, Length];
Print["Path types: " <> ToString[pathCounts]];

(* ==================== Bias Detection ==================== *)

Print["Detecting bias patterns..."];

mBiasPatterns = DetectMBias[g];

(* Detect overcontrol bias (adjusting for mediators on causal path) *)
directPaths = Select[pathClassifications, #["type"] == "direct" &];
mediators = If[Length[directPaths] > 0,
  Union[Flatten[Map[Most[Rest[#["path"]]] &, directPaths]]],
  {}
];

overcontrolWarnings = Map[
  <|
    "mediator" -> #,
    "type" -> "overcontrol",
    "warning" -> "Adjusting for " <> ToString[#] <> " (mediator) blocks causal path"
  |> &,
  mediators
];

allWarnings = Join[mBiasPatterns, overcontrolWarnings];

Print["Detected " <> ToString[Length[allWarnings]] <> " potential bias patterns"];

(* Export warnings *)
ExportJSON[allWarnings, outputPrefix <> "_bias_warnings.json"];
Print["Saved: " <> outputPrefix <> "_bias_warnings.json"];

(* Export path enumeration *)
ExportJSON[pathClassifications, outputPrefix <> "_path_enumeration.json"];
Print["Saved: " <> outputPrefix <> "_path_enumeration.json"];

(* ==================== Visualization - All Paths ==================== *)

Print["Visualizing path types..."];

(* Color edges by path type they participate in *)
edgeColors = Map[
  Module[{edge = DirectedEdge[#[[1]], #[[2]]], pathsWithEdge},
    pathsWithEdge = Select[pathClassifications, MemberQ[Partition[#["path"], 2, 1], {#[[1]], #[[2]]}] || MemberQ[Partition[#["path"], 2, 1], {#[[2]], #[[1]]}] &];

    Which[
      AnyTrue[pathsWithEdge, #["type"] == "direct" &], ColorScheme["Success"],
      AnyTrue[pathsWithEdge, #["type"] == "backdoor" &], ColorScheme["Danger"],
      AnyTrue[pathsWithEdge, #["type"] == "collider" &], ColorScheme["Warning"],
      True, ColorScheme["Neutral"]
    ]
  ] &,
  edges
];

gPaths = Graph[
  vertices,
  edgeRules,
  GraphLayout -> "LayeredDigraphEmbedding",
  VertexLabels -> Placed["Name", Center],
  VertexStyle -> ColorScheme["Primary"],
  VertexSize -> 0.4,
  VertexLabelStyle -> Directive[White, Bold, 14],
  EdgeStyle -> Thread[edgeRules -> edgeColors],
  ImageSize -> 1200,
  PlotLabel -> Style["Path Analysis: " <> ToString[pathCounts], Bold, 18]
];

SaveFig[gPaths, outputPrefix <> "_dag_paths_highlighted.png"];
Print["Saved: " <> outputPrefix <> "_dag_paths_highlighted.png"];

(* ==================== Visualization - M-bias Warning ==================== *)

If[Length[mBiasPatterns] > 0,
  Print["Generating M-bias warning visualization..."];

  colliderVertices = mBiasPatterns[[All, "collider"]];

  vertexColors = Map[
    Which[
      # == treatment, ColorScheme["Primary"],
      # == outcome, ColorScheme["Success"],
      MemberQ[colliderVertices, #], ColorScheme["Danger"],
      True, ColorScheme["Neutral"]
    ] &,
    vertices
  ];

  gMBias = Graph[
    vertices,
    edgeRules,
    GraphLayout -> "LayeredDigraphEmbedding",
    VertexLabels -> Placed["Name", Center],
    VertexStyle -> Thread[vertices -> vertexColors],
    VertexSize -> 0.4,
    VertexLabelStyle -> Directive[White, Bold, 14],
    EdgeStyle -> Directive[Arrowheads[0.02], Thickness[0.005]],
    ImageSize -> 1200,
    PlotLabel -> Style["⚠ M-Bias Detected: Do NOT adjust for " <> ToString[colliderVertices], Bold, 18, ColorScheme["Danger"]]
  ];

  SaveFig[gMBias, outputPrefix <> "_m_bias_warning.png"];
  Print["Saved: " <> outputPrefix <> "_m_bias_warning.png"];
];

Print["Path and bias analysis complete!"];
