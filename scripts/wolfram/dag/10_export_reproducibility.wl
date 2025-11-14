#!/usr/bin/env wolframscript
(* -*- coding: utf-8 -*- *)
(*
Export & Reproducibility - Module 10
Reference: /home/hirokionodera/CQO/可視化④.pdf p.5

Features:
1. Export DAG in multiple formats (GraphML, JSON, DOT)
2. Generate curl command for API replication
3. Generate Python code for reproduction
4. PDF report generation
5. Complete audit trail

Usage:
  wolframscript -file 10_export_reproducibility.wl --input data/dag/edges.csv --treatment X --outcome Y --output artifacts/dag/export --demo

Outputs:
  - dag.graphml (GraphML format for Cytoscape/Gephi)
  - dag.json (JSON format for web visualization)
  - dag.dot (Graphviz DOT format)
  - reproduce_curl.sh (curl commands)
  - reproduce_python.py (Python script)
  - analysis_report.pdf (comprehensive PDF report)
  - metadata.json (full provenance)
*)

Get[FileNameJoin[{NotebookDirectory[], "..", "common", "00_common.wl"}]];

(* ==================== Parse Arguments ==================== *)

args = ParseArgs[$ScriptCommandLine[[2;;]]];

inputPath = Lookup[args, "input", "data/dag/edges.csv"];
treatment = Lookup[args, "treatment", "X1"];
outcome = Lookup[args, "outcome", "Y"];
outputPrefix = Lookup[args, "output", "artifacts/dag/export"];
demoMode = KeyExistsQ[args, "demo"];

(* ==================== Load DAG ==================== *)

edges = If[demoMode || !FileExistsQ[inputPath],
  Print["Demo mode: Generating synthetic DAG..."];
  GenerateDemoDAG[10, 0.25],

  Print["Loading edges from: " <> inputPath];
  data = ReadCSV[inputPath];
  Rest[data]
];

vertices = Union[Flatten[edges[[All, {1, 2}]]]];
edgeRules = Map[DirectedEdge[#[[1]], #[[2]]] &, edges];

g = Graph[vertices, edgeRules];

Print["Exporting DAG with " <> ToString[Length[vertices]] <> " vertices and " <> ToString[Length[edges]] <> " edges"];

(* ==================== Export GraphML ==================== *)

Print["Exporting GraphML format..."];

graphmlPath = outputPrefix <> "_dag.graphml";

(* Manually create GraphML XML *)
graphmlXML = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n" <>
  "<graphml xmlns=\"http://graphml.graphdrawing.org/xmlns\">\n" <>
  "  <key id=\"weight\" for=\"edge\" attr.name=\"weight\" attr.type=\"double\"/>\n" <>
  "  <graph id=\"DAG\" edgedefault=\"directed\">\n";

(* Add nodes *)
Do[
  graphmlXML = graphmlXML <> "    <node id=\"" <> v <> "\"/>\n",
  {v, vertices}
];

(* Add edges *)
Do[
  graphmlXML = graphmlXML <>
    "    <edge source=\"" <> edge[[1]] <> "\" target=\"" <> edge[[2]] <> "\">\n" <>
    "      <data key=\"weight\">" <> ToString[edge[[3]]] <> "</data>\n" <>
    "    </edge>\n",
  {edge, edges}
];

graphmlXML = graphmlXML <> "  </graph>\n</graphml>\n";

EnsureDir[graphmlPath];
Export[graphmlPath, graphmlXML, "Text"];
Print["Saved: " <> graphmlPath];

(* ==================== Export JSON ==================== *)

Print["Exporting JSON format..."];

dagJSON = <|
  "nodes" -> Map[<|"id" -> #, "label" -> #|> &, vertices],
  "edges" -> Map[<|
    "source" -> #[[1]],
    "target" -> #[[2]],
    "weight" -> #[[3]]
  |> &, edges],
  "metadata" -> <|
    "treatment" -> treatment,
    "outcome" -> outcome,
    "n_nodes" -> Length[vertices],
    "n_edges" -> Length[edges],
    "timestamp" -> DateString["ISODateTime"]
  |>
|>;

ExportJSON[dagJSON, outputPrefix <> "_dag.json"];
Print["Saved: " <> outputPrefix <> "_dag.json"];

(* ==================== Export DOT (Graphviz) ==================== *)

Print["Exporting DOT format..."];

dotContent = "digraph DAG {\n";
dotContent = dotContent <> "  rankdir=LR;\n";
dotContent = dotContent <> "  node [shape=circle, style=filled, fillcolor=\"#3B82F6\", fontcolor=white];\n";

Do[
  dotContent = dotContent <>
    "  \"" <> edge[[1]] <> "\" -> \"" <> edge[[2]] <>
    "\" [label=\"" <> ToString[NumberForm[edge[[3]], {3, 2}]] <> "\"];\n",
  {edge, edges}
];

dotContent = dotContent <> "}\n";

dotPath = outputPrefix <> "_dag.dot";
EnsureDir[dotPath];
Export[dotPath, dotContent, "Text"];
Print["Saved: " <> dotPath];

(* ==================== Generate curl Commands ==================== *)

Print["Generating curl reproduction script..."];

curlScript = "#!/bin/bash\n\n";
curlScript = curlScript <> "# Causal Analysis Reproduction Script\n";
curlScript = curlScript <> "# Generated: " <> DateString["ISODateTime"] <> "\n\n";

curlScript = curlScript <> "API_URL=\"http://localhost:8081\"\n\n";

curlScript = curlScript <> "# 1. Interactive DAG Visualization\n";
curlScript = curlScript <> "curl -X POST \"${API_URL}/dag/interactive\" \\\n";
curlScript = curlScript <> "  -H \"Content-Type: application/json\" \\\n";
curlScript = curlScript <> "  -d '{\n";
curlScript = curlScript <> "    \"edges\": " <> ExportString[edges, "JSON", "Compact" -> True] <> ",\n";
curlScript = curlScript <> "    \"output_prefix\": \"artifacts/dag/interactive\"\n";
curlScript = curlScript <> "  }'\n\n";

curlScript = curlScript <> "# 2. Identifiability Analysis\n";
curlScript = curlScript <> "curl -X POST \"${API_URL}/dag/identifiability\" \\\n";
curlScript = curlScript <> "  -H \"Content-Type: application/json\" \\\n";
curlScript = curlScript <> "  -d '{\n";
curlScript = curlScript <> "    \"edges\": " <> ExportString[edges, "JSON", "Compact" -> True] <> ",\n";
curlScript = curlScript <> "    \"treatment\": \"" <> treatment <> "\",\n";
curlScript = curlScript <> "    \"outcome\": \"" <> outcome <> "\"\n";
curlScript = curlScript <> "  }'\n\n";

curlScript = curlScript <> "# 3. do-Operator Intervention\n";
curlScript = curlScript <> "curl -X POST \"${API_URL}/dag/intervention\" \\\n";
curlScript = curlScript <> "  -H \"Content-Type: application/json\" \\\n";
curlScript = curlScript <> "  -d '{\n";
curlScript = curlScript <> "    \"treatment\": \"" <> treatment <> "\",\n";
curlScript = curlScript <> "    \"outcome\": \"" <> outcome <> "\",\n";
curlScript = curlScript <> "    \"adjustment\": [\"Z\"]\n";
curlScript = curlScript <> "  }'\n\n";

curlPath = outputPrefix <> "_reproduce_curl.sh";
EnsureDir[curlPath];
Export[curlPath, curlScript, "Text"];

(* Make executable *)
Run["chmod +x " <> curlPath];
Print["Saved: " <> curlPath];

(* ==================== Generate Python Script ==================== *)

Print["Generating Python reproduction script..."];

pythonScript = "#!/usr/bin/env python3\n";
pythonScript = pythonScript <> "\"\"\"\n";
pythonScript = pythonScript <> "Causal Analysis Reproduction Script\n";
pythonScript = pythonScript <> "Generated: " <> DateString["ISODateTime"] <> "\n";
pythonScript = pythonScript <> "\"\"\"\n\n";

pythonScript = pythonScript <> "import networkx as nx\n";
pythonScript = pythonScript <> "import pandas as pd\n";
pythonScript = pythonScript <> "from dowhy import CausalModel\n\n";

pythonScript = pythonScript <> "# Define DAG\n";
pythonScript = pythonScript <> "edges = [\n";
Do[
  pythonScript = pythonScript <> "    (\"" <> edge[[1]] <> "\", \"" <> edge[[2]] <> "\", {\"weight\": " <> ToString[edge[[3]]] <> "}),\n",
  {edge, edges}
];
pythonScript = pythonScript <> "]\n\n";

pythonScript = pythonScript <> "# Create NetworkX graph\n";
pythonScript = pythonScript <> "G = nx.DiGraph()\n";
pythonScript = pythonScript <> "G.add_edges_from(edges)\n\n";

pythonScript = pythonScript <> "# DoWhy causal model\n";
pythonScript = pythonScript <> "model = CausalModel(\n";
pythonScript = pythonScript <> "    data=df,  # Your DataFrame here\n";
pythonScript = pythonScript <> "    treatment=\"" <> treatment <> "\",\n";
pythonScript = pythonScript <> "    outcome=\"" <> outcome <> "\",\n";
pythonScript = pythonScript <> "    graph=G\n";
pythonScript = pythonScript <> ")\n\n";

pythonScript = pythonScript <> "# Identify causal effect\n";
pythonScript = pythonScript <> "identified_estimand = model.identify_effect()\n";
pythonScript = pythonScript <> "print(identified_estimand)\n\n";

pythonScript = pythonScript <> "# Estimate causal effect\n";
pythonScript = pythonScript <> "estimate = model.estimate_effect(\n";
pythonScript = pythonScript <> "    identified_estimand,\n";
pythonScript = pythonScript <> "    method_name=\"backdoor.propensity_score_matching\"\n";
pythonScript = pythonScript <> ")\n";
pythonScript = pythonScript <> "print(f\"ATE: {estimate.value}\")\n\n";

pythonScript = pythonScript <> "# Refute estimate\n";
pythonScript = pythonScript <> "refute = model.refute_estimate(\n";
pythonScript = pythonScript <> "    identified_estimand,\n";
pythonScript = pythonScript <> "    estimate,\n";
pythonScript = pythonScript <> "    method_name=\"random_common_cause\"\n";
pythonScript = pythonScript <> ")\n";
pythonScript = pythonScript <> "print(refute)\n";

pythonPath = outputPrefix <> "_reproduce_python.py";
EnsureDir[pythonPath];
Export[pythonPath, pythonScript, "Text"];

(* Make executable *)
Run["chmod +x " <> pythonPath];
Print["Saved: " <> pythonPath];

(* ==================== Generate PDF Report ==================== *)

Print["Generating PDF report..."];

(* Create report content *)
reportContent = {
  Style["Causal Analysis Report", Bold, 24],
  "",
  Style["1. DAG Structure", Bold, 18],
  "Treatment: " <> treatment,
  "Outcome: " <> outcome,
  "Vertices: " <> ToString[Length[vertices]],
  "Edges: " <> ToString[Length[edges]],
  "",
  Style["2. Graph Properties", Bold, 18],
  "Density: " <> ToString[NumberForm[N[Length[edges] / (Length[vertices] * (Length[vertices] - 1))], {3, 2}]],
  "Average Degree: " <> ToString[NumberForm[N[2 * Length[edges] / Length[vertices]], {3, 2}]],
  "",
  Style["3. Vertices", Bold, 18],
  Grid[Partition[vertices, 5, 5, 1, ""], Frame -> All],
  "",
  Style["4. Edges", Bold, 18],
  Grid[Prepend[Map[{#[[1]], " → ", #[[2]], NumberForm[#[[3]], {3, 2}]} &, edges], {"From", "", "To", "Weight"}], Frame -> All],
  "",
  Style["5. Reproducibility", Bold, 18],
  "Generated: " <> DateString["ISODateTime"],
  "Scripts: reproduce_curl.sh, reproduce_python.py",
  "Formats: GraphML, JSON, DOT"
};

pdfPath = outputPrefix <> "_analysis_report.pdf";
EnsureDir[pdfPath];
Export[pdfPath, Column[reportContent, Spacings -> 1], "PDF"];
Print["Saved: " <> pdfPath];

(* ==================== Export Complete Metadata ==================== *)

Print["Exporting complete metadata..."];

metadata = <|
  "project" -> "CQOx Causal Analysis",
  "treatment" -> treatment,
  "outcome" -> outcome,
  "dag" -> <|
    "vertices" -> vertices,
    "edges" -> edges,
    "n_vertices" -> Length[vertices],
    "n_edges" -> Length[edges]
  |>,
  "files" -> <|
    "graphml" -> graphmlPath,
    "json" -> outputPrefix <> "_dag.json",
    "dot" -> dotPath,
    "curl_script" -> curlPath,
    "python_script" -> pythonPath,
    "pdf_report" -> pdfPath
  |>,
  "provenance" -> <|
    "generated_by" -> "Wolfram ONE (Engine-free)",
    "script" -> "10_export_reproducibility.wl",
    "timestamp" -> DateString["ISODateTime"],
    "system" -> $SystemID,
    "version" -> $VersionNumber
  |>
|>;

ExportJSON[metadata, outputPrefix <> "_metadata.json"];
Print["Saved: " <> outputPrefix <> "_metadata.json"];

Print[""];
Print["==================== EXPORT COMPLETE ===================="];
Print["All files exported to: " <> DirectoryName[outputPrefix]];
Print[""];
Print["Available formats:"];
Print["  - GraphML: " <> FileNameTake[graphmlPath]];
Print["  - JSON: " <> FileNameTake[outputPrefix <> "_dag.json"]];
Print["  - DOT: " <> FileNameTake[dotPath]];
Print["  - curl: " <> FileNameTake[curlPath]];
Print["  - Python: " <> FileNameTake[pythonPath]];
Print["  - PDF: " <> FileNameTake[pdfPath]];
Print[""];

Print["Export and reproducibility complete!"];
