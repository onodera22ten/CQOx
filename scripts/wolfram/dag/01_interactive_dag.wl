#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
Interactive DAG Visualization - Module 1: Provenance & Reliability Layer
Reference: /home/hirokionodera/CQO/可視化⑤.pdf p.1-2

Generates:
1. 2D DAG (Layered/Sugiyama layout) with edge weights
2. 3D DAG (Spring embedding)
3. Turntable GIF animation (360° rotation)
4. Adjacency matrix heatmap + CSV export
5. Degree distribution histogram

Usage:
  wolframscript -file 01_interactive_dag.wl --input data/dag/edges.csv --output artifacts/dag/interactive --demo

Input CSV format (edges.csv):
  from,to,weight
  X1,X2,0.8
  X1,X3,0.6
  ...

Outputs:
  - interactive_dag_2d.png/svg
  - interactive_dag_3d.png/svg
  - interactive_dag_3d_turntable.gif
  - adjacency_matrix.png/svg
  - adjacency_matrix.csv
  - degree_distribution.png/svg
*)

(* Load common utilities *)
Get[FileNameJoin[{NotebookDirectory[], "..", "common", "00_common.wl"}]];

(* ==================== Parse Arguments ==================== *)

args = ParseArgs[$ScriptCommandLine[[2;;]]];

inputPath = Lookup[args, "input", "data/dag/edges.csv"];
outputPrefix = Lookup[args, "output", "artifacts/dag/interactive"];
demoMode = KeyExistsQ[args, "demo"];

(* ==================== Load or Generate Data ==================== *)

edges = If[demoMode || !FileExistsQ[inputPath],
  Print["Demo mode: Generating synthetic DAG..."];
  GenerateDemoDAG[12, 0.25],

  Print["Loading edges from: " <> inputPath];
  data = ReadCSV[inputPath];
  Rest[data] (* Skip header *)
];

(* Extract vertices and weights *)
vertices = Union[Flatten[edges[[All, {1, 2}]]]];
edgeRules = Map[DirectedEdge[#[[1]], #[[2]]] &, edges];
edgeWeights = AssociationThread[edgeRules, edges[[All, 3]]];

Print["Loaded " <> ToString[Length[vertices]] <> " vertices and " <> ToString[Length[edges]] <> " edges"];

(* ==================== Create Graph Object ==================== *)

g = Graph[
  vertices,
  edgeRules,
  EdgeWeight -> edges[[All, 3]],
  VertexLabels -> "Name",
  VertexStyle -> ColorScheme["Primary"],
  VertexSize -> 0.3,
  EdgeStyle -> Directive[Arrowheads[0.02], Thickness[0.005]],
  ImageSize -> 1200
];

(* ==================== 2D DAG Visualization ==================== *)

Print["Generating 2D DAG (Layered layout)..."];

(* Color edges by weight *)
edgeColors = Map[
  If[Abs[#] > 0.7, ColorScheme["Success"],
     If[Abs[#] > 0.4, ColorScheme["Warning"], ColorScheme["Danger"]]
  ] &,
  edges[[All, 3]]
];

g2d = Graph[
  vertices,
  edgeRules,
  GraphLayout -> "LayeredDigraphEmbedding",
  VertexLabels -> Placed["Name", Center],
  VertexStyle -> ColorScheme["Primary"],
  VertexSize -> 0.4,
  VertexLabelStyle -> Directive[White, Bold, 14],
  EdgeStyle -> Thread[edgeRules -> edgeColors],
  EdgeLabels -> Thread[edgeRules -> Map[NumberForm[#, {3, 2}] &, edges[[All, 3]]]],
  EdgeLabelStyle -> Directive[Bold, 11],
  ImageSize -> 1200,
  PlotLabel -> Style["Causal DAG - 2D Layered Layout", Bold, 18]
];

SaveFig[g2d, outputPrefix <> "_dag_2d.png"];
Print["Saved: " <> outputPrefix <> "_dag_2d.png"];

(* ==================== 3D DAG Visualization ==================== *)

Print["Generating 3D DAG (Spring embedding)..."];

(* Get 3D coordinates using spring embedding *)
coords3d = GraphEmbedding[g, Dimension -> 3, "SpringEmbedding"];
vertexCoords = AssociationThread[vertices, coords3d];

(* Create 3D graphics *)
edges3d = Map[
  Arrow[Tube[{vertexCoords[#[[1]]], vertexCoords[#[[2]]]}, 0.02]] &,
  edges[[All, {1, 2}]]
];

vertices3d = MapThread[
  {ColorScheme["Primary"], Sphere[#1, 0.1],
   Text[Style[#2, Bold, 14], #1 + {0, 0, 0.2}]} &,
  {coords3d, vertices}
];

g3d = Graphics3D[
  {edges3d, vertices3d},
  Boxed -> False,
  ViewPoint -> {1.3, -2.4, 2.0},
  ImageSize -> 1200,
  Lighting -> "Neutral",
  PlotLabel -> Style["Causal DAG - 3D Spring Layout", Bold, 18]
];

SaveFig[g3d, outputPrefix <> "_dag_3d.png"];
Print["Saved: " <> outputPrefix <> "_dag_3d.png"];

(* ==================== 3D Turntable GIF ==================== *)

Print["Generating 3D turntable GIF (36 frames)..."];

frames = Table[
  Graphics3D[
    {edges3d, vertices3d},
    Boxed -> False,
    ViewPoint -> {1.3 * Cos[angle], -2.4 * Sin[angle], 2.0},
    ImageSize -> 800,
    Lighting -> "Neutral",
    PlotLabel -> Style["Causal DAG - 3D Rotation", Bold, 16]
  ],
  {angle, 0, 2 Pi, 2 Pi / 36}
];

SaveFig[frames, outputPrefix <> "_dag_3d_turntable.gif"];
Print["Saved: " <> outputPrefix <> "_dag_3d_turntable.gif"];

(* ==================== Adjacency Matrix ==================== *)

Print["Generating adjacency matrix..."];

(* Build adjacency matrix *)
n = Length[vertices];
adjMatrix = Table[0.0, {n}, {n}];

Do[
  from = Position[vertices, edge[[1]]][[1, 1]];
  to = Position[vertices, edge[[2]]][[1, 1]];
  adjMatrix[[from, to]] = edge[[3]],
  {edge, edges}
];

(* Heatmap visualization *)
heatmap = ArrayPlot[
  adjMatrix,
  ColorFunction -> (Blend[{ColorScheme["Danger"], White, ColorScheme["Success"]}, (#1 + 1)/2] &),
  ColorFunctionScaling -> False,
  PlotLegends -> Automatic,
  FrameLabel -> {"To", "From"},
  FrameTicks -> {{Range[n], vertices}, {Range[n], vertices}},
  ImageSize -> 1000,
  PlotLabel -> Style["Adjacency Matrix (Edge Weights)", Bold, 18]
];

SaveFig[heatmap, outputPrefix <> "_adjacency_matrix.png"];
Print["Saved: " <> outputPrefix <> "_adjacency_matrix.png"];

(* Export adjacency matrix as CSV *)
adjCSV = Prepend[
  MapThread[Prepend[#1, #2] &, {adjMatrix, vertices}],
  Prepend[vertices, ""]
];
ExportCSV[adjCSV, outputPrefix <> "_adjacency_matrix.csv"];
Print["Saved: " <> outputPrefix <> "_adjacency_matrix.csv"];

(* ==================== Degree Distribution ==================== *)

Print["Generating degree distribution..."];

inDegrees = VertexInDegree[g];
outDegrees = VertexOutDegree[g];

degreeHist = Histogram[
  {inDegrees, outDegrees},
  ChartLegends -> {"In-Degree", "Out-Degree"},
  ChartStyle -> {ColorScheme["Primary"], ColorScheme["Secondary"]},
  FrameLabel -> {"Degree", "Count"},
  PlotLabel -> Style["Degree Distribution", Bold, 18],
  ImageSize -> 1200,
  BarOrigin -> Left
];

SaveFig[degreeHist, outputPrefix <> "_degree_distribution.png"];
Print["Saved: " <> outputPrefix <> "_degree_distribution.png"];

(* ==================== Export Metadata ==================== *)

metadata = <|
  "vertices" -> Length[vertices],
  "edges" -> Length[edges],
  "avg_degree" -> N[Mean[inDegrees + outDegrees]],
  "max_in_degree" -> Max[inDegrees],
  "max_out_degree" -> Max[outDegrees],
  "density" -> N[Length[edges] / (Length[vertices] * (Length[vertices] - 1))],
  "avg_weight" -> N[Mean[Abs[edges[[All, 3]]]]],
  "timestamp" -> DateString["ISODateTime"]
|>;

ExportJSON[metadata, outputPrefix <> "_metadata.json"];
Print["Saved: " <> outputPrefix <> "_metadata.json"];

Print["Interactive DAG visualization complete!"];
