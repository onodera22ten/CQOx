#!/usr/bin/env wolframscript
(* ::Package:: *)

(*
 * Spillover Dynamics Animation
 *
 * Purpose: NASA/Meta-level animation of network spillover propagation over time
 *
 * Features:
 *   - Wave-like diffusion animation (30 frames)
 *   - Node activation sequence (treatment adoption)
 *   - Edge weight changes (spillover strength evolution)
 *   - Color transitions (effect magnitude over time)
 *
 * Standards: Meta AI Diffusion Models, Google DeepMind Temporal Networks
 *)

(* Parameters *)
outputPath = If[Length[$ScriptCommandLine] >= 2 && $ScriptCommandLine[[2]] =!= "",
               $ScriptCommandLine[[2]],
               "visualizations/wolfram/spillover_dynamics_animation.gif"];

(* Network parameters *)
SeedRandom[42];
numNodes = 30;
numTimeSteps = 30;

(* Generate random network *)
graph = RandomGraph[{numNodes, 60}, DirectedEdges -> True];

(* Initial treatment seeds (5% of nodes) *)
initialTreated = RandomSample[VertexList[graph], Ceiling[0.05 * numNodes]];

(* Propagation parameters *)
propagationProb = 0.3;  (* Probability of spillover per timestep *)
effectDecay = 0.95;     (* Effect decay over time *)

(* Simulate diffusion dynamics *)
diffusionHistory = Module[{treated, effects, history},
  treated = Association[# -> 0 & /@ VertexList[graph]];  (* 0 = untreated *)

  (* Initialize seeds *)
  Do[treated[node] = 1, {node, initialTreated}];

  (* Initialize effects *)
  effects = Association[# -> 0.0 & /@ VertexList[graph]];
  Do[effects[node] = RandomReal[{3, 5}], {node, initialTreated}];

  history = {};

  (* Simulate timesteps *)
  Do[
    Module[{newTreated, newEffects},
      newTreated = treated;
      newEffects = effects;

      (* Propagate treatment through edges *)
      Do[
        If[treated[edge[[1]]] > 0,  (* If source is treated *)
          If[RandomReal[] < propagationProb && treated[edge[[2]]] == 0,
            (* Activate target node *)
            newTreated[edge[[2]]] = t;
            newEffects[edge[[2]]] = effects[edge[[1]]] * effectDecay * RandomReal[{0.7, 1.0}]
          ]
        ],
        {edge, EdgeList[graph]}
      ];

      (* Decay existing effects *)
      newEffects = Association[# -> newEffects[#] * effectDecay & /@ Keys[newEffects]];

      treated = newTreated;
      effects = newEffects;

      AppendTo[history, {treated, effects}]
    ],
    {t, 1, numTimeSteps}
  ];

  history
];

(* Generate layout (fixed across frames) *)
layout = GraphLayout[graph, "SpringElectricalEmbedding"];
vertexCoords = Association[Thread[VertexList[graph] -> layout]];

(* Create animation frames *)
frames = Table[
  Module[{treated, effects, nodeColors, nodeSizes, edgeColors},
    {treated, effects} = diffusionHistory[[t]];

    (* Node colors based on effect magnitude *)
    nodeColors = Table[
      node -> If[treated[node] > 0,
        Blend[{White, Red, Orange, Yellow}, Rescale[effects[node], {0, 5}]],
        GrayLevel[0.9]
      ],
      {node, VertexList[graph]}
    ];

    (* Node sizes based on activation time *)
    nodeSizes = Table[
      node -> If[treated[node] > 0,
        Rescale[t - treated[node], {0, numTimeSteps}, {0.03, 0.12}],
        0.02
      ],
      {node, VertexList[graph]}
    ];

    (* Edge colors based on spillover activity *)
    edgeColors = Table[
      edge -> If[treated[edge[[1]]] > 0 && treated[edge[[2]]] == 0,
        Directive[Red, Opacity[0.6], Thickness[0.008]],  (* Active spillover *)
        Directive[Gray, Opacity[0.2], Thickness[0.003]]  (* Inactive *)
      ],
      {edge, EdgeList[graph]}
    ];

    (* Create graph visualization *)
    graph2D = Graph[
      graph,
      VertexCoordinates -> vertexCoords,
      VertexSize -> nodeSizes,
      VertexStyle -> nodeColors,
      EdgeStyle -> edgeColors,
      ImageSize -> 800,
      Background -> White,
      PlotLabel -> Style[
        "Spillover Dynamics (t=" <> ToString[t] <> "/" <> ToString[numTimeSteps] <> ")\n" <>
        "Treated: " <> ToString[Count[Values[treated], _?Positive]] <> "/" <> ToString[numNodes],
        14, Bold, Black
      ],
      PlotRangePadding -> 0.1
    ];

    (* Add legend *)
    Legended[
      graph2D,
      Placed[
        Grid[
          {
            {Graphics[{Red, Disk[]}, ImageSize -> 15],
             Style["High Effect (>4)", 10]},
            {Graphics[{Orange, Disk[]}, ImageSize -> 15],
             Style["Medium Effect (2-4)", 10]},
            {Graphics[{Yellow, Disk[]}, ImageSize -> 15],
             Style["Low Effect (<2)", 10]},
            {Graphics[{GrayLevel[0.9], Disk[]}, ImageSize -> 15],
             Style["Untreated", 10]},
            {"", ""},
            {Graphics[{Red, Opacity[0.6], Thickness[0.008], Line[{{0, 0}, {1, 0}}]},
                     ImageSize -> {25, 5}],
             Style["Active Spillover", 10]},
            {Graphics[{Gray, Opacity[0.2], Thickness[0.003], Line[{{0, 0}, {1, 0}}]},
                     ImageSize -> {25, 5}],
             Style["Inactive Edge", 10]}
          },
          Alignment -> Left,
          Spacings -> {0.5, 0.3},
          Frame -> True,
          Background -> White
        ],
        {Right, Top}
      ]
    ]
  ],
  {t, 1, numTimeSteps}
];

(* Export as GIF animation *)
Export[outputPath, frames,
  "DisplayDurations" -> 0.2,  (* 200ms per frame = 5 FPS *)
  "AnimationRepetitions" -> Infinity,
  ImageResolution -> 150
];

Print["[WolframONE] Spillover Dynamics Animation generated: " <> outputPath];
Print["Frames: " <> ToString[numTimeSteps]];
Print["Duration: " <> ToString[numTimeSteps * 0.2] <> " seconds"];

(* Also export individual frames for inspection *)
frameDir = StringReplace[outputPath, ".gif" -> "_frames"];
CreateDirectory[frameDir];

Do[
  Export[
    FileNameJoin[{frameDir, "frame_" <> IntegerString[t, 10, 3] <> ".png"}],
    frames[[t]],
    ImageResolution -> 150
  ],
  {t, 1, numTimeSteps}
];

Print["[WolframONE] Individual frames exported to: " <> frameDir];

(* Generate interactive Manipulate version *)
interactivePath = StringReplace[outputPath, ".gif" -> "_interactive.nb"];

interactiveSpillover = Manipulate[
  Module[{treated, effects, nodeColors, nodeSizes, edgeColors},
    {treated, effects} = diffusionHistory[[timeStep]];

    nodeColors = Table[
      node -> If[treated[node] > 0,
        Blend[colorGradient, Rescale[effects[node], {0, 5}]],
        GrayLevel[0.9]
      ],
      {node, VertexList[graph]}
    ];

    nodeSizes = Table[
      node -> If[treated[node] > 0,
        Rescale[timeStep - treated[node], {0, numTimeSteps}, {minNodeSize, maxNodeSize}],
        minNodeSize
      ],
      {node, VertexList[graph]}
    ];

    edgeColors = Table[
      edge -> If[treated[edge[[1]]] > 0 && treated[edge[[2]]] == 0,
        Directive[highlightColor, Opacity[activeOpacity], Thickness[0.008]],
        Directive[Gray, Opacity[inactiveOpacity], Thickness[0.003]]
      ],
      {edge, EdgeList[graph]}
    ];

    Graph[
      graph,
      VertexCoordinates -> vertexCoords,
      VertexSize -> nodeSizes,
      VertexStyle -> nodeColors,
      EdgeStyle -> edgeColors,
      ImageSize -> 700,
      Background -> If[darkMode, Black, White],
      PlotLabel -> Style[
        "Interactive Spillover Dynamics (t=" <> ToString[timeStep] <> ")",
        12, Bold
      ]
    ]
  ],

  (* Time control *)
  {{timeStep, 1, "Time Step"}, 1, numTimeSteps, 1,
   Appearance -> "Labeled", AnimationRate -> animationSpeed},

  Delimiter,
  Style["Visual Controls", Bold],

  (* Color controls *)
  {{colorGradient, {White, Red, Orange, Yellow}, "Color Gradient"},
   {
     {White, Red, Orange, Yellow} -> "Warm",
     {White, Blue, Cyan, Green} -> "Cool",
     {White, Purple, Magenta, Pink} -> "Vibrant"
   },
   ControlType -> PopupMenu},

  {{highlightColor, Red, "Active Edge Color"},
   {Red, Blue, Green, Purple, Orange},
   ControlType -> PopupMenu},

  (* Size controls *)
  {{minNodeSize, 0.02, "Min Node Size"}, 0.01, 0.05, 0.01, Appearance -> "Labeled"},
  {{maxNodeSize, 0.12, "Max Node Size"}, 0.05, 0.20, 0.01, Appearance -> "Labeled"},

  (* Opacity controls *)
  {{activeOpacity, 0.6, "Active Edge Opacity"}, 0.2, 1.0, 0.1, Appearance -> "Labeled"},
  {{inactiveOpacity, 0.2, "Inactive Edge Opacity"}, 0.1, 0.5, 0.05, Appearance -> "Labeled"},

  (* Animation controls *)
  {{animationSpeed, 1, "Animation Speed"}, 0.5, 5, 0.5, Appearance -> "Labeled"},

  (* Display options *)
  {{darkMode, False, "Dark Mode"}, {True, False}},

  ControlPlacement -> Left,
  SaveDefinitions -> True
];

Export[interactivePath, interactiveSpillover];

Print["[WolframONE] Interactive notebook generated: " <> interactivePath];

(* Summary statistics *)
Print[""];
Print["=== Spillover Dynamics Statistics ==="];
Print["Network size: " <> ToString[numNodes] <> " nodes"];
Print["Initial seeds: " <> ToString[Length[initialTreated]]];
Print["Final adoption rate: " <> ToString[
  Count[Values[diffusionHistory[[-1]][[1]]], _?Positive] / numNodes * 100
] <> "%"];
Print["Propagation probability: " <> ToString[propagationProb * 100] <> "%"];
Print["Effect decay rate: " <> ToString[(1 - effectDecay) * 100] <> "% per timestep"];
