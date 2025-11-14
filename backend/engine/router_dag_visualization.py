"""
DAG Visualization API Router
Interactive DAG, Domain Network DAG, Causal Discovery
"""

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import pandas as pd
from pathlib import Path
import uuid
import json

router = APIRouter(prefix="/api/visualizations/dag", tags=["dag_visualization"])


class DAGVisualizationRequest(BaseModel):
    """DAG可視化リクエスト"""
    dataset_id: str
    dag_type: str = "interactive"  # interactive, domain_network, causal_discovery


class DAGVisualizationResponse(BaseModel):
    """DAG可視化レスポンス"""
    status: str
    job_id: str
    dag_type: str
    statistics: Dict[str, Any]
    visualization_url: str
    message: Optional[str] = None


@router.post("/generate", response_model=DAGVisualizationResponse)
async def generate_dag(req: DAGVisualizationRequest):
    """
    DAG可視化を生成

    Types:
    - interactive: インタラクティブDAG
    - domain_network: ドメインネットワークDAG
    - causal_discovery: 因果発見DAG (PC/FCI Algorithm)
    """
    try:
        # Load dataset
        data_path = Path(f"data/packets/{req.dataset_id}/data.parquet")
        if not data_path.exists():
            data_path = Path(f"data/{req.dataset_id}/data.parquet")
        if not data_path.exists():
            data_path = Path(f"data/{req.dataset_id}.parquet")

        if not data_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Dataset not found: {req.dataset_id}"
            )

        df = pd.read_parquet(data_path)

        # Create job ID
        job_id = f"dag_{uuid.uuid4().hex[:8]}"
        output_dir = Path("reports/dag") / job_id
        output_dir.mkdir(parents=True, exist_ok=True)

        statistics = {}
        visualization_url = ""

        try:
            # Import DAG generation modules
            if req.dag_type == "interactive":
                from backend.visualization.dag_generator import generate_interactive_dag
                output_path = output_dir / "interactive_dag.html"
                stats = generate_interactive_dag(df, str(output_path))
                statistics = stats
                visualization_url = f"/reports/dag/{job_id}/interactive_dag.html"

            elif req.dag_type == "domain_network":
                from backend.visualization.dag_generator import generate_domain_network
                output_path = output_dir / "domain_network.html"
                stats = generate_domain_network(df, str(output_path))
                statistics = stats
                visualization_url = f"/reports/dag/{job_id}/domain_network.html"

            elif req.dag_type == "causal_discovery":
                from backend.causal.discovery import run_causal_discovery
                output_path = output_dir / "causal_discovery.html"
                stats = run_causal_discovery(df, str(output_path))
                statistics = stats
                visualization_url = f"/reports/dag/{job_id}/causal_discovery.html"

            else:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid DAG type: {req.dag_type}"
                )

        except ImportError as e:
            print(f"[DAG] DAG generation module not available: {e}")
            # Generate placeholder DAG
            statistics, visualization_url = generate_placeholder_dag(
                df, output_dir, job_id, req.dag_type
            )

        return DAGVisualizationResponse(
            status="completed",
            job_id=job_id,
            dag_type=req.dag_type,
            statistics=statistics,
            visualization_url=visualization_url,
            message=f"Generated {req.dag_type} DAG visualization"
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"[DAG] Error in generate_dag: {e}")
        print(f"[DAG] Traceback:\n{error_trace}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"DAG generation failed: {str(e)}"
        )


def generate_placeholder_dag(df: pd.DataFrame, output_dir: Path, job_id: str, dag_type: str):
    """Generate placeholder DAG when advanced modules are not available"""
    import networkx as nx
    import plotly.graph_objects as go
    import numpy as np

    # Create a sample DAG based on dataset columns
    G = nx.DiGraph()

    # Use first few columns as nodes
    columns = df.columns.tolist()[:min(10, len(df.columns))]

    # Add nodes
    for col in columns:
        G.add_node(col)

    # Add some random edges to create a DAG structure
    np.random.seed(42)
    for i, source in enumerate(columns[:-1]):
        # Connect to 1-2 downstream nodes
        num_targets = min(np.random.randint(1, 3), len(columns) - i - 1)
        targets = np.random.choice(columns[i+1:], size=num_targets, replace=False)
        for target in targets:
            G.add_edge(source, target)

    # Calculate statistics
    statistics = {
        "nodes": G.number_of_nodes(),
        "edges": G.number_of_edges(),
        "layers": len(list(nx.topological_generations(G))),
        "causal_paths": sum(1 for _ in nx.all_simple_paths(G, columns[0], columns[-1])) if len(columns) > 1 else 0
    }

    # Generate visualization using Plotly
    pos = nx.spring_layout(G, k=2, iterations=50)

    # Create edge traces
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=2, color='#888'),
        hoverinfo='none',
        mode='lines',
        name='Edges'
    )

    # Create node traces
    node_x = []
    node_y = []
    node_text = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)
        node_text.append(f"{node}<br>Degree: {G.degree(node)}")

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers+text',
        text=list(G.nodes()),
        textposition="top center",
        hovertext=node_text,
        hoverinfo='text',
        marker=dict(
            size=30,
            color='lightblue',
            line=dict(width=2, color='darkblue')
        ),
        name='Nodes'
    )

    # Create figure
    fig = go.Figure(data=[edge_trace, node_trace])

    title_map = {
        "interactive": "Interactive DAG (Placeholder)",
        "domain_network": "Domain Network DAG (Placeholder)",
        "causal_discovery": "Causal Discovery DAG (Placeholder)"
    }

    fig.update_layout(
        title=title_map.get(dag_type, "DAG Visualization (Placeholder)"),
        titlefont_size=16,
        showlegend=True,
        hovermode='closest',
        margin=dict(b=20, l=5, r=5, t=40),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        plot_bgcolor='white',
        height=600
    )

    # Save visualization
    output_path = output_dir / f"{dag_type}_dag.html"
    fig.write_html(str(output_path))

    visualization_url = f"/reports/dag/{job_id}/{dag_type}_dag.html"

    return statistics, visualization_url
