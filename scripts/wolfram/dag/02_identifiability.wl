#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
Identifiability Assistant - Module 2: Backdoor & Frontdoor Criterion
Reference: /home/hirokionodera/CQO/可視化④.pdf p.2

Generates:
1. Backdoor adjustment sets (minimal + all valid)
2. Frontdoor adjustment sets (if applicable)
3. DAG visualization with highlighted adjustment sets
4. Identifiability check results (JSON)

Formulas:
- Backdoor: P(Y|do(X)) = Σ_z P(Y|X,z)P(z)
- Frontdoor: P(Y|do(X)) = Σ_m P(m|X)Σ_x' P(Y|m,x')P(x')

Usage:
  wolframscript -file 02_identifiability.wl --input data/dag/edges.csv --treatment X --outcome Y --output artifacts/dag/identifiability --demo

Outputs:
  - backdoor_sets.json (list of valid adjustment sets)
  - frontdoor_sets.json (list of valid mediator sets)
  - dag_backdoor_highlighted.png/svg
  - dag_frontdoor_highlighted.png/svg
  - identifiability_result.json
*)

Get[FileNameJoin[{NotebookDirectory[], "..", "common", "00_common.wl"}]];

(* ==================== Parse Arguments ==================== *)

args = ParseArgs[$ScriptCommandLine[[2;;]]];

inputPath = Lookup[args, "input", "data/dag/edges.csv"];
treatment = Lookup[args, "treatment", "X1"];
outcome = Lookup[args, "outcome", "Y"];
outputPrefix = Lookup[args, "output", "artifacts/dag/identifiability"];
demoMode = KeyExistsQ[args, "demo"];

(* ==================== Load or Generate DAG ==================== *)

edges = If[demoMode || !FileExistsQ[inputPath],
  Print["Demo mode: Generating synthetic DAG with confounder..."];
  (* Create a DAG with confounding: Z -> X1, Z -> Y *)
  {
    {"Z", "X1", 0.7},
    {"Z", "Y", 0.6},
    {"X1", "M", 0.8},
    {"M", "Y", 0.75},
    {"X2", "Y", 0.5}
  },

  Print["Loading edges from: " <> inputPath];
  data = ReadCSV[inputPath];
  Rest[data]
];

vertices = Union[Flatten[edges[[All, {1, 2}]]]];
edgeRules = Map[DirectedEdge[#[[1]], #[[2]]] &, edges];

(* Verify treatment and outcome exist *)
If[!MemberQ[vertices, treatment],
  ExitError["Treatment variable '" <> treatment <> "' not found in DAG"]
];
If[!MemberQ[vertices, outcome],
  ExitError["Outcome variable '" <> outcome <> "' not found in DAG"]
];

g = Graph[vertices, edgeRules];

Print["Analyzing identifiability for: " <> treatment <> " -> " <> outcome];

(* ==================== Helper Functions ==================== *)

(* Find all paths from X to Y *)
FindAllPaths[graph_, start_, end_] := FindPath[graph, start, end, Infinity, All];

(* Find ancestors of a vertex *)
FindAncestors[graph_, vertex_] := Module[{ancestors = {}},
  Do[
    If[PathGraphQ[FindPath[graph, v, vertex, Infinity, 1]],
      AppendTo[ancestors, v]
    ],
    {v, VertexList[graph]}
  ];
  DeleteCases[ancestors, vertex]
];

(* Find descendants of a vertex *)
FindDescendants[graph_, vertex_] := Module[{descendants = {}},
  Do[
    If[PathGraphQ[FindPath[graph, vertex, v, Infinity, 1]],
      AppendTo[descendants, v]
    ],
    {v, VertexList[graph]}
  ];
  DeleteCases[descendants, vertex]
];

(* Check if set blocks all backdoor paths *)
CheckBackdoorCriterion[graph_, treatment_, outcome_, adjustmentSet_] := Module[
  {allPaths, backdoorPaths, blocked},

  (* Find all paths from treatment to outcome *)
  allPaths = FindAllPaths[graph, treatment, outcome];

  (* Backdoor paths are those that start with an arrow INTO treatment *)
  backdoorPaths = Select[allPaths, Length[#] > 1 && !EdgeQ[graph, DirectedEdge[treatment, #[[2]]]] &];

  (* Check if all backdoor paths are blocked by adjustment set *)
  blocked = AllTrue[backdoorPaths,
    Function[path,
      AnyTrue[adjustmentSet, MemberQ[Most[Rest[path]], #] &]
    ]
  ];

  (* Also check no descendant of treatment in adjustment set *)
  descendants = FindDescendants[graph, treatment];
  noDescendants = Intersection[adjustmentSet, descendants] === {};

  blocked && noDescendants
];

(* ==================== Backdoor Criterion ==================== *)

Print["Computing backdoor adjustment sets..."];

(* Find all possible adjustment sets (power set of non-descendants) *)
nonDescendants = Complement[
  vertices,
  {treatment, outcome},
  FindDescendants[g, treatment]
];

(* Check all subsets *)
allSubsets = Subsets[nonDescendants];
validBackdoorSets = Select[
  allSubsets,
  CheckBackdoorCriterion[g, treatment, outcome, #] &
];

(* Find minimal sets (no proper subset is also valid) *)
minimalBackdoorSets = Select[
  validBackdoorSets,
  Function[set,
    !AnyTrue[validBackdoorSets, # != set && SubsetQ[set, #] &]
  ]
];

Print["Found " <> ToString[Length[validBackdoorSets]] <> " valid backdoor sets"];
Print["Found " <> ToString[Length[minimalBackdoorSets]] <> " minimal backdoor sets"];

(* Export backdoor sets *)
backdoorResult = <|
  "treatment" -> treatment,
  "outcome" -> outcome,
  "all_valid_sets" -> validBackdoorSets,
  "minimal_sets" -> minimalBackdoorSets,
  "identifiable" -> Length[validBackdoorSets] > 0,
  "recommended" -> If[Length[minimalBackdoorSets] > 0, First[minimalBackdoorSets], {}]
|>;

ExportJSON[backdoorResult, outputPrefix <> "_backdoor_sets.json"];
Print["Saved: " <> outputPrefix <> "_backdoor_sets.json"];

(* ==================== Frontdoor Criterion ==================== *)

Print["Computing frontdoor adjustment sets..."];

(* A mediator set M satisfies frontdoor if:
   1. M intercepts all directed paths from X to Y
   2. No backdoor path from X to M
   3. X blocks all backdoor paths from M to Y *)

(* Find all directed paths from treatment to outcome *)
directedPaths = FindAllPaths[g, treatment, outcome];

(* Potential mediators are vertices on these paths (excluding X and Y) *)
potentialMediators = Union[Flatten[Map[Most[Rest[#]] &, directedPaths]]];

validFrontdoorSets = {};

(* Check subsets of potential mediators *)
Do[
  mediatorSet = subset;

  (* Check if M intercepts all directed paths *)
  interceptsAll = AllTrue[directedPaths,
    Function[path, AnyTrue[mediatorSet, MemberQ[Most[Rest[path]], #] &]]
  ];

  If[interceptsAll,
    (* Check no backdoor from X to M *)
    noBackdoorXM = AllTrue[mediatorSet,
      Function[m, !AnyTrue[FindAllPaths[g, treatment, m], Length[#] > 1 && !EdgeQ[g, DirectedEdge[treatment, #[[2]]]] &]]
    ];

    If[noBackdoorXM,
      AppendTo[validFrontdoorSets, mediatorSet]
    ]
  ],
  {subset, Subsets[potentialMediators]}
];

Print["Found " <> ToString[Length[validFrontdoorSets]] <> " valid frontdoor sets"];

frontdoorResult = <|
  "treatment" -> treatment,
  "outcome" -> outcome,
  "valid_sets" -> validFrontdoorSets,
  "identifiable" -> Length[validFrontdoorSets] > 0,
  "recommended" -> If[Length[validFrontdoorSets] > 0, First[validFrontdoorSets], {}]
|>;

ExportJSON[frontdoorResult, outputPrefix <> "_frontdoor_sets.json"];
Print["Saved: " <> outputPrefix <> "_frontdoor_sets.json"];

(* ==================== Visualization - Backdoor ==================== *)

If[Length[minimalBackdoorSets] > 0,
  Print["Visualizing backdoor adjustment set..."];

  recommendedBackdoor = First[minimalBackdoorSets];

  (* Color vertices by role *)
  vertexColors = Map[
    Which[
      # == treatment, ColorScheme["Primary"],
      # == outcome, ColorScheme["Success"],
      MemberQ[recommendedBackdoor, #], ColorScheme["Warning"],
      True, ColorScheme["Neutral"]
    ] &,
    vertices
  ];

  gBackdoor = Graph[
    vertices,
    edgeRules,
    GraphLayout -> "LayeredDigraphEmbedding",
    VertexLabels -> Placed["Name", Center],
    VertexStyle -> Thread[vertices -> vertexColors],
    VertexSize -> 0.4,
    VertexLabelStyle -> Directive[White, Bold, 14],
    EdgeStyle -> Directive[Arrowheads[0.02], Thickness[0.005]],
    ImageSize -> 1200,
    PlotLabel -> Style["Backdoor Adjustment: " <> ToString[recommendedBackdoor], Bold, 18]
  ];

  SaveFig[gBackdoor, outputPrefix <> "_dag_backdoor_highlighted.png"];
  Print["Saved: " <> outputPrefix <> "_dag_backdoor_highlighted.png"];
];

(* ==================== Visualization - Frontdoor ==================== *)

If[Length[validFrontdoorSets] > 0,
  Print["Visualizing frontdoor adjustment set..."];

  recommendedFrontdoor = First[validFrontdoorSets];

  vertexColors = Map[
    Which[
      # == treatment, ColorScheme["Primary"],
      # == outcome, ColorScheme["Success"],
      MemberQ[recommendedFrontdoor, #], ColorScheme["Info"],
      True, ColorScheme["Neutral"]
    ] &,
    vertices
  ];

  gFrontdoor = Graph[
    vertices,
    edgeRules,
    GraphLayout -> "LayeredDigraphEmbedding",
    VertexLabels -> Placed["Name", Center],
    VertexStyle -> Thread[vertices -> vertexColors],
    VertexSize -> 0.4,
    VertexLabelStyle -> Directive[White, Bold, 14],
    EdgeStyle -> Directive[Arrowheads[0.02], Thickness[0.005]],
    ImageSize -> 1200,
    PlotLabel -> Style["Frontdoor Adjustment: " <> ToString[recommendedFrontdoor], Bold, 18]
  ];

  SaveFig[gFrontdoor, outputPrefix <> "_dag_frontdoor_highlighted.png"];
  Print["Saved: " <> outputPrefix <> "_dag_frontdoor_highlighted.png"];
];

(* ==================== Summary Report ==================== *)

identifiabilityResult = <|
  "treatment" -> treatment,
  "outcome" -> outcome,
  "backdoor_identifiable" -> Length[validBackdoorSets] > 0,
  "frontdoor_identifiable" -> Length[validFrontdoorSets] > 0,
  "recommended_method" -> If[Length[validBackdoorSets] > 0, "backdoor", If[Length[validFrontdoorSets] > 0, "frontdoor", "none"]],
  "backdoor_minimal_sets" -> minimalBackdoorSets,
  "frontdoor_valid_sets" -> validFrontdoorSets,
  "timestamp" -> DateString["ISODateTime"]
|>;

ExportJSON[identifiabilityResult, outputPrefix <> "_identifiability_result.json"];
Print["Saved: " <> outputPrefix <> "_identifiability_result.json"];

Print["Identifiability analysis complete!"];
