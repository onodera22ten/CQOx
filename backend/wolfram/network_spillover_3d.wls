#!/usr/bin/env wolframscript
(* ::Package:: *)

(*
 * Network Spillover 3D Visualization
 *
 * Purpose: NASA/Meta-level 3D network visualization of spillover effects
 *
 * Features:
 *   - 3D node positioning based on community structure
 *   - Node size = direct treatment effect magnitude
 *   - Edge thickness = spillover effect magnitude
 *   - Color gradient = effect heterogeneity (CATE)
 *
 * Standards: Meta AI Graph Neural Networks, Google DeepMind
 *)

(* Load network data *)
dataPath = If[Length[$ScriptCommandLine] >= 2 && $ScriptCommandLine[[2]] =!= "",
              $ScriptCommandLine[[2]],
              "data/network_test.csv"];

outputPath = If[Length[$ScriptCommandLine] >= 3 && $ScriptCommandLine[[3]] =!= "",
               $ScriptCommandLine[[3]],
               "visualizations/wolfram/network_spillover_3d.png"];

(* Import network data *)
rawData = Import[dataPath, "Dataset", HeaderLines -> 1];

(* Extract nodes and edges *)
nodes = DeleteDuplicates[Join[rawData[All, "src_id"], rawData[All, "dst_id"]]];
edges = rawData[All, {"src_id", "dst_id", "weight"}];

(* Create graph *)
graph = Graph[
  DirectedEdge @@@ edges[All, {"src_id", "dst_id"}],
  EdgeWeight -> edges[All, "weight"],
  VertexLabels -> "Name"
];

(* Generate 3D layout using force-directed algorithm *)
layout3D = GraphLayout3D[graph, Method -> "SpringElectricalEmbedding"];
vertexCoords = Association[Thread[VertexList[graph] -> layout3D]];

(* Simulate treatment effects (Direct + Indirect) *)
SeedRandom[42];
directEffect = Association[# -> RandomReal[{-2, 5}] & /@ nodes];
indirectEffect = Association[# -> RandomReal[{-1, 3}] & /@ nodes];

(* Node colors based on total effect *)
totalEffect = Association[# -> (directEffect[#] + indirectEffect[#]) & /@ nodes];
colorFunc = ColorData["TemperatureMap"][Rescale[#, {-3, 8}]] &;

(* Node sizes based on direct effect magnitude *)
nodeSizes = Association[# -> Rescale[Abs[directEffect[#]], {0, 5}, {0.02, 0.15}] & /@ nodes];

(* Edge thickness based on spillover magnitude *)
edgeThickness = Association[
  DirectedEdge[#src_id, #dst_id] ->
    Rescale[Abs[#weight * indirectEffect[#dst_id]], {0, 5}, {0.001, 0.01}]
  & /@ Normal[edges]
];

(* Create 3D network visualization *)
network3D = Graph3D[
  graph,

  (* Vertex styling *)
  VertexCoordinates -> vertexCoords,
  VertexSize -> nodeSizes,
  VertexStyle -> Table[
    node -> Directive[
      colorFunc[totalEffect[node]],
      Specularity[White, 10],
      Opacity[0.9]
    ],
    {node, nodes}
  ],

  (* Edge styling *)
  EdgeStyle -> Table[
    edge -> Directive[
      Gray,
      Opacity[0.4],
      Thickness[edgeThickness[edge]]
    ],
    {edge, EdgeList[graph]}
  ],

  (* Layout *)
  GraphLayout -> {"SpringElectricalEmbedding3D", "EdgeWeighted" -> True},

  (* Visual options *)
  ImageSize -> 1200,
  ViewPoint -> {1.5, -2.0, 1.5},
  ViewAngle -> 40 Degree,
  Boxed -> False,
  Background -> White,

  (* Lighting *)
  Lighting -> {
    {"Ambient", White},
    {"Point", White, {2, -1, 2}},
    {"Point", LightBlue, {-2, 1, 2}}
  }
];

(* Add legend and annotations *)
network3DWithLegend = Legended[
  network3D,
  Placed[
    Grid[
      {
        {Style["Network Spillover Effects (3D)", 14, Bold], SpanFromLeft},
        {Graphics[{colorFunc[-3], Disk[]}, ImageSize -> 20],
         "Negative Total Effect (-3)"},
        {Graphics[{colorFunc[2.5], Disk[]}, ImageSize -> 20],
         "Neutral Effect (0)"},
        {Graphics[{colorFunc[8], Disk[]}, ImageSize -> 20],
         "Positive Total Effect (+8)"},
        {"", ""},
        {Graphics[{Gray, Opacity[0.4], Thickness[0.001], Line[{{0, 0}, {1, 0}}]},
                  ImageSize -> {30, 5}],
         "Weak Spillover"},
        {Graphics[{Gray, Opacity[0.4], Thickness[0.01], Line[{{0, 0}, {1, 0}}]},
                  ImageSize -> {30, 5}],
         "Strong Spillover"},
        {"", ""},
        {Graphics[{Blue, Opacity[0.9], Disk[{0, 0}, 0.02]}, ImageSize -> 20],
         "Small Direct Effect"},
        {Graphics[{Blue, Opacity[0.9], Disk[{0, 0}, 0.15]}, ImageSize -> 20],
         "Large Direct Effect"}
      },
      Alignment -> Left,
      Spacings -> {1, 0.5},
      Frame -> All,
      Background -> White
    ],
    Right
  ]
];

(* Export high-resolution image *)
Export[outputPath, network3DWithLegend,
  ImageResolution -> 300,
  Background -> White
];

Print["[WolframONE] Network Spillover 3D generated: " <> outputPath];

(* Generate interactive version *)
interactivePath = StringReplace[outputPath, ".png" -> "_interactive.nb"];

interactiveNetwork = Manipulate[
  Graph3D[
    graph,
    VertexCoordinates -> vertexCoords,
    VertexSize -> nodeSizes,
    VertexStyle -> Table[
      node -> Directive[
        ColorData[colorScheme][Rescale[totalEffect[node], {-3, 8}]],
        Specularity[White, specularityLevel],
        Opacity[nodeOpacity]
      ],
      {node, nodes}
    ],
    EdgeStyle -> Table[
      edge -> Directive[
        Gray,
        Opacity[edgeOpacity],
        Thickness[edgeThickness[edge] * edgeThicknessMult]
      ],
      {edge, EdgeList[graph]}
    ],
    ViewPoint -> viewPoint,
    ViewAngle -> viewAngle Degree,
    ImageSize -> 800,
    Background -> If[darkMode, Black, White],
    Boxed -> showBox,
    Lighting -> If[enhancedLighting,
      {{"Ambient", White}, {"Point", White, {2, -1, 2}}, {"Point", LightBlue, {-2, 1, 2}}},
      "Neutral"
    ]
  ],

  {{viewPoint, {1.5, -2.0, 1.5}, "View Point"},
   {{1.5, -2.0, 1.5}, {-1.5, -2.0, 1.5}, {0, -3, 2}, {2, -1, 1}},
   ControlType -> PopupMenu},

  {{viewAngle, 40, "View Angle"}, 20, 60, 5, Appearance -> "Labeled"},

  {{colorScheme, "TemperatureMap", "Color Scheme"},
   {"TemperatureMap", "Rainbow", "DarkRainbow", "SolarColors", "Pastel"},
   ControlType -> PopupMenu},

  {{nodeOpacity, 0.9, "Node Opacity"}, 0.3, 1.0, 0.1, Appearance -> "Labeled"},
  {{edgeOpacity, 0.4, "Edge Opacity"}, 0.1, 1.0, 0.1, Appearance -> "Labeled"},
  {{edgeThicknessMult, 1.0, "Edge Thickness Multiplier"}, 0.5, 3.0, 0.5, Appearance -> "Labeled"},
  {{specularityLevel, 10, "Specularity"}, 0, 30, 5, Appearance -> "Labeled"},

  {{darkMode, False, "Dark Mode"}, {True, False}},
  {{showBox, False, "Show Box"}, {True, False}},
  {{enhancedLighting, True, "Enhanced Lighting"}, {True, False}},

  ControlPlacement -> Left,
  SaveDefinitions -> True
];

Export[interactivePath, interactiveNetwork];

Print["[WolframONE] Interactive notebook generated: " <> interactivePath];

(* Summary statistics *)
Print[""];
Print["=== Network Spillover 3D Statistics ==="];
Print["Nodes: " <> ToString[Length[nodes]]];
Print["Edges: " <> ToString[Length[edges]]];
Print["Avg Direct Effect: " <> ToString[Mean[Values[directEffect]]]];
Print["Avg Indirect Effect: " <> ToString[Mean[Values[indirectEffect]]]];
Print["Avg Total Effect: " <> ToString[Mean[Values[totalEffect]]]];
Print["Positive Effect Nodes: " <> ToString[Count[Values[totalEffect], _?Positive]] <> "/" <> ToString[Length[nodes]]];
