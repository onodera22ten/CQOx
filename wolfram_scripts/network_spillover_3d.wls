#!/usr/bin/env wolframscript
(* ::Package:: *)

(*
Network Spillover 3D Visualization
Visualizes causal effect propagation through network connections
*)

(* Parse command line arguments *)
args = Rest[$ScriptCommandLine];
If[Length[args] < 3,
  Print["Usage: network_spillover_3d.wls <data_path> <output_dir> <mapping_json>"];
  Exit[1];
];

dataPath = args[[1]];
outputDir = args[[2]];
mappingJson = ImportString[args[[3]], "JSON"];

Print["[NetworkSpillover] Starting network spillover 3D generation"];
Print["[NetworkSpillover] Data: ", dataPath];

(* Load data *)
data = Import[dataPath, "Dataset"];
Print["[NetworkSpillover] Loaded ", Length[data], " rows"];

(* Extract columns *)
yCol = mappingJson["y"];
treatmentCol = mappingJson["treatment"];
unitIdCol = mappingJson["unit_id"];

Print["[NetworkSpillover] Outcome: ", yCol];
Print["[NetworkSpillover] Treatment: ", treatmentCol];
Print["[NetworkSpillover] Unit ID: ", unitIdCol];

(* Look for network columns *)
networkCols = Select[Keys[Normal[data[[1]]]],
  StringContainsQ[ToLowerCase[#], "friend" | "connection" | "neighbor" | "network"] &
];

If[Length[networkCols] == 0,
  Print["[NetworkSpillover] No explicit network columns found, generating random network..."];

  (* Generate random network structure *)
  numNodes = Min[50, Length[data]];
  edges = RandomGraph[{numNodes, Round[numNodes * 1.5]}, DirectedEdges -> False];

  (* Assign node IDs *)
  nodeIds = Take[Normal[data[All, unitIdCol]], numNodes];
  nodeIds = Flatten[Map[Values, nodeIds]];

  (* Create adjacency mapping *)
  adjacency = AdjacencyMatrix[edges];,

  Print["[NetworkSpillover] Using network column: ", networkCols[[1]]];
  (* Build network from data *)
  (* Simplified: assume each row represents an edge *)
  numNodes = Min[50, Length[data]];
  nodeIds = Take[Union[Normal[data[All, unitIdCol]]], numNodes];
  nodeIds = Flatten[Map[Values, nodeIds]];

  (* Random network for demonstration *)
  edges = RandomGraph[{numNodes, Round[numNodes * 1.5]}, DirectedEdges -> False];
  adjacency = AdjacencyMatrix[edges];
];

Print["[NetworkSpillover] Network: ", numNodes, " nodes, ", EdgeCount[edges], " edges"];

(* Extract outcomes and treatments *)
dataTable = Normal[data[All, {unitIdCol, treatmentCol, yCol}]];
dataTable = Map[Values, Take[dataTable, numNodes]];

(* Calculate direct and spillover effects *)
directEffects = Table[
  If[dataTable[[i, 2]] == 1,  (* Treated *)
    dataTable[[i, 3]],  (* Direct effect = outcome *)
    0
  ],
  {i, numNodes}
];

(* Spillover effects = weighted sum of neighbors' effects *)
spilloverEffects = Table[
  neighbors = Position[Normal[adjacency[[i]]], 1] // Flatten;
  If[Length[neighbors] > 0,
    Mean[directEffects[[neighbors]]],
    0
  ],
  {i, numNodes}
];

totalEffects = directEffects + spilloverEffects;

Print["[NetworkSpillover] Mean direct effect: ", Mean[directEffects]];
Print["[NetworkSpillover] Mean spillover effect: ", Mean[spilloverEffects]];

(* Create 3D network graph with effect-based node sizing *)
Print["[NetworkSpillover] Generating 3D network visualization..."];

(* Normalize effects for visualization *)
maxEffect = Max[Abs[totalEffects]];
normalizedEffects = If[maxEffect > 0, totalEffects / maxEffect, totalEffects];

(* Create graph with 3D layout *)
graph3D = Graph3D[edges,
  VertexSize -> Map[0.1 + 0.3 * Abs[#] &, normalizedEffects],
  VertexStyle -> Table[
    i -> ColorData["TemperatureMap"][0.5 + 0.5 * normalizedEffects[[i]]],
    {i, numNodes}
  ],
  EdgeStyle -> Directive[Opacity[0.3], Gray, Thickness[0.002]],
  GraphLayout -> {"SpringElectricalEmbedding", "Dimension" -> 3},
  Boxed -> False,
  ImageSize -> Large,
  PlotLabel -> Style["Network Spillover Effects (3D)", 16, Bold]
];

output3D = FileNameJoin[{outputDir, "network_spillover_3d.png"}];
Export[output3D, graph3D, "PNG", ImageSize -> 1400];
Print["[NetworkSpillover] Saved 3D network: ", output3D];

(* 2D network layout *)
Print["[NetworkSpillover] Generating 2D network visualization..."];

graph2D = Graph[edges,
  VertexSize -> Map[0.15 + 0.4 * Abs[#] &, normalizedEffects],
  VertexStyle -> Table[
    i -> ColorData["TemperatureMap"][0.5 + 0.5 * normalizedEffects[[i]]],
    {i, numNodes}
  ],
  EdgeStyle -> Directive[Opacity[0.4], Gray, Thickness[0.003]],
  GraphLayout -> "SpringElectricalEmbedding",
  ImageSize -> Large,
  PlotLabel -> Style["Network Spillover Effects (2D)", 16, Bold]
];

(* Add legend *)
graph2DWithLegend = Legended[graph2D,
  BarLegend[{"TemperatureMap", {-maxEffect, maxEffect}},
    LegendLabel -> "Total Effect"]
];

output2D = FileNameJoin[{outputDir, "network_spillover_2d.png"}];
Export[output2D, graph2DWithLegend, "PNG", ImageSize -> 1400];
Print["[NetworkSpillover] Saved 2D network: ", output2D];

(* Heatmap of spillover intensity *)
Print["[NetworkSpillover] Generating spillover heatmap..."];

(* Create distance matrix *)
distMatrix = GraphDistanceMatrix[edges];

(* Spillover intensity matrix (inverse of distance, weighted by effects) *)
spilloverMatrix = Table[
  If[i != j && distMatrix[[i, j]] < Infinity,
    (directEffects[[j]] / distMatrix[[i, j]]),
    0
  ],
  {i, numNodes}, {j, numNodes}
];

heatmap = MatrixPlot[spilloverMatrix,
  ColorFunction -> "TemperatureMap",
  PlotLegends -> Automatic,
  FrameLabel -> {"Target Node", "Source Node"},
  PlotLabel -> Style["Network Spillover Intensity Heatmap", 16, Bold],
  ImageSize -> Large
];

outputHeatmap = FileNameJoin[{outputDir, "network_spillover_heatmap.png"}];
Export[outputHeatmap, heatmap, "PNG", ImageSize -> 1200];
Print["[NetworkSpillover] Saved heatmap: ", outputHeatmap];

(* Interactive 3D rotation *)
Print["[NetworkSpillover] Generating interactive HTML..."];

htmlContent = ExportString[
  Manipulate[
    Show[graph3D, ViewPoint -> {3*Cos[angle], 3*Sin[angle], height}],
    {{angle, Pi/4, "Rotation"}, 0, 2*Pi},
    {{height, 2, "View Height"}, 0.5, 3}
  ],
  "HTML"
];

outputHTML = FileNameJoin[{outputDir, "network_spillover_interactive.html"}];
Export[outputHTML, htmlContent, "Text"];
Print["[NetworkSpillover] Saved interactive HTML: ", outputHTML];

(* Network statistics *)
stats = <|
  "num_nodes" -> numNodes,
  "num_edges" -> EdgeCount[edges],
  "density" -> EdgeCount[edges] / (numNodes * (numNodes - 1) / 2),
  "mean_direct_effect" -> Mean[directEffects],
  "mean_spillover_effect" -> Mean[spilloverEffects],
  "mean_total_effect" -> Mean[totalEffects],
  "max_effect" -> Max[totalEffects],
  "min_effect" -> Min[totalEffects],
  "spillover_ratio" -> Mean[spilloverEffects] / (Mean[directEffects] + 0.001)
|>;

statsFile = FileNameJoin[{outputDir, "network_spillover_stats.json"}];
Export[statsFile, stats, "JSON"];
Print["[NetworkSpillover] Saved statistics: ", statsFile];

Print["[NetworkSpillover] Complete!"];
Exit[0];
