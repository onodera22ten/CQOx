"""
DAG Comprehensive Analysis API Router
10 Modules for 100万円/month value
Based on /docs/DAG.pdf specification
"""

from fastapi import APIRouter, HTTPException, status, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import subprocess
import json
from pathlib import Path
import uuid
import os

router = APIRouter(prefix="/api/dag", tags=["dag_comprehensive"])


# ==================== Request/Response Models ====================

class DAGAnalysisRequest(BaseModel):
    """DAG分析リクエスト"""
    dataset_id: str
    edges_csv: Optional[str] = None  # Custom edges CSV path
    treatment: Optional[str] = "X1"
    outcome: Optional[str] = "Y"
    adjustment: Optional[List[str]] = None
    instruments: Optional[List[str]] = None
    features: Optional[List[str]] = None


class ModuleResult(BaseModel):
    """モジュール実行結果"""
    module_id: int
    module_name: str
    status: str  # success, error, running
    outputs: Dict[str, str]  # filename -> URL mapping
    metadata: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None


class DAGAnalysisResponse(BaseModel):
    """DAG分析レスポンス"""
    job_id: str
    status: str  # completed, running, error
    modules: List[ModuleResult]
    artifacts_dir: str


# ==================== Helper Functions ====================

def run_wolfram_script(script_name: str, args: List[str], output_dir: Path) -> Dict[str, Any]:
    """
    Wolfram scriptを実行して結果を返す

    Args:
        script_name: スクリプト名 (e.g., "01_interactive_dag.wl")
        args: コマンドライン引数
        output_dir: 出力ディレクトリ

    Returns:
        実行結果の辞書
    """
    script_path = Path("scripts/wolfram/dag") / script_name

    if not script_path.exists():
        return {
            "status": "error",
            "error": f"Script not found: {script_path}"
        }

    # Wolframスクリプトを実行
    cmd = ["wolframscript", "-file", str(script_path)] + args

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5分タイムアウト
        )

        if result.returncode == 0:
            # 出力ファイルを検索
            outputs = {}
            for file in output_dir.glob("*"):
                if file.is_file():
                    rel_path = file.relative_to(Path("artifacts"))
                    outputs[file.name] = f"/artifacts/{rel_path}"

            return {
                "status": "success",
                "outputs": outputs,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        else:
            return {
                "status": "error",
                "error": result.stderr,
                "stdout": result.stdout
            }

    except subprocess.TimeoutExpired:
        return {
            "status": "error",
            "error": "Script execution timed out (>5min)"
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


# ==================== API Endpoints ====================

@router.post("/run-all", response_model=DAGAnalysisResponse)
async def run_all_modules(req: DAGAnalysisRequest, background_tasks: BackgroundTasks):
    """
    10モジュール全てを実行
    """
    job_id = f"dag_{uuid.uuid4().hex[:12]}"
    artifacts_dir = Path("artifacts/dag") / job_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # データセットパスを解決
    dataset_path = resolve_dataset_path(req.dataset_id)

    modules_results = []

    # Module 1: Interactive DAG
    module1_dir = artifacts_dir / "01_interactive"
    module1_dir.mkdir(exist_ok=True)

    result1 = run_wolfram_script(
        "01_interactive_dag.wl",
        [
            "--input", req.edges_csv or f"{dataset_path}/edges.csv",
            "--output", str(module1_dir / "interactive"),
            "--demo" if not req.edges_csv else ""
        ],
        module1_dir
    )

    modules_results.append(ModuleResult(
        module_id=1,
        module_name="Interactive DAG",
        status=result1["status"],
        outputs=result1.get("outputs", {}),
        error_message=result1.get("error")
    ))

    # Module 2: Identifiability
    module2_dir = artifacts_dir / "02_identifiability"
    module2_dir.mkdir(exist_ok=True)

    result2 = run_wolfram_script(
        "02_identifiability.wl",
        [
            "--input", req.edges_csv or f"{dataset_path}/edges.csv",
            "--treatment", req.treatment,
            "--outcome", req.outcome,
            "--output", str(module2_dir / "identifiability"),
            "--demo" if not req.edges_csv else ""
        ],
        module2_dir
    )

    modules_results.append(ModuleResult(
        module_id=2,
        module_name="Identifiability Assistant",
        status=result2["status"],
        outputs=result2.get("outputs", {}),
        error_message=result2.get("error")
    ))

    # Module 3: do-Operator
    module3_dir = artifacts_dir / "03_do_operator"
    module3_dir.mkdir(exist_ok=True)

    adjustment_str = ",".join(req.adjustment) if req.adjustment else "Z"

    result3 = run_wolfram_script(
        "03_do_operator.wl",
        [
            "--input", f"{dataset_path}/data.csv",
            "--treatment", req.treatment,
            "--outcome", req.outcome,
            "--adjustment", adjustment_str,
            "--output", str(module3_dir / "do_operator"),
            "--demo" if not os.path.exists(f"{dataset_path}/data.csv") else ""
        ],
        module3_dir
    )

    modules_results.append(ModuleResult(
        module_id=3,
        module_name="do-Operator Runner",
        status=result3["status"],
        outputs=result3.get("outputs", {}),
        error_message=result3.get("error")
    ))

    # Module 4: Path & Bias Explorer
    module4_dir = artifacts_dir / "04_path_bias"
    module4_dir.mkdir(exist_ok=True)

    result4 = run_wolfram_script(
        "04_path_bias_explorer.wl",
        [
            "--input", req.edges_csv or f"{dataset_path}/edges.csv",
            "--treatment", req.treatment,
            "--outcome", req.outcome,
            "--output", str(module4_dir / "path_bias"),
            "--demo" if not req.edges_csv else ""
        ],
        module4_dir
    )

    modules_results.append(ModuleResult(
        module_id=4,
        module_name="Path & Bias Explorer",
        status=result4["status"],
        outputs=result4.get("outputs", {}),
        error_message=result4.get("error")
    ))

    # Module 5: IV Tester
    module5_dir = artifacts_dir / "05_iv_test"
    module5_dir.mkdir(exist_ok=True)

    instruments_str = ",".join(req.instruments) if req.instruments else "Z1,Z2"

    result5 = run_wolfram_script(
        "05_iv_tester.wl",
        [
            "--input", f"{dataset_path}/data.csv",
            "--treatment", req.treatment,
            "--outcome", req.outcome,
            "--instruments", instruments_str,
            "--output", str(module5_dir / "iv_test"),
            "--demo"
        ],
        module5_dir
    )

    modules_results.append(ModuleResult(
        module_id=5,
        module_name="IV Tester",
        status=result5["status"],
        outputs=result5.get("outputs", {}),
        error_message=result5.get("error")
    ))

    # Module 6: CATE Heterogeneity
    module6_dir = artifacts_dir / "06_cate"
    module6_dir.mkdir(exist_ok=True)

    features_str = ",".join(req.features) if req.features else "X1,X2,X3"

    result6 = run_wolfram_script(
        "06_cate_heterogeneity.wl",
        [
            "--input", f"{dataset_path}/data.csv",
            "--treatment", req.treatment,
            "--outcome", req.outcome,
            "--features", features_str,
            "--output", str(module6_dir / "cate"),
            "--demo"
        ],
        module6_dir
    )

    modules_results.append(ModuleResult(
        module_id=6,
        module_name="CATE Heterogeneity",
        status=result6["status"],
        outputs=result6.get("outputs", {}),
        error_message=result6.get("error")
    ))

    # Module 7: Timeseries DAG
    module7_dir = artifacts_dir / "07_timeseries"
    module7_dir.mkdir(exist_ok=True)

    result7 = run_wolfram_script(
        "07_timeseries_dag.wl",
        [
            "--input", f"{dataset_path}/timeseries.csv",
            "--output", str(module7_dir / "timeseries"),
            "--maxlag", "10",
            "--demo"
        ],
        module7_dir
    )

    modules_results.append(ModuleResult(
        module_id=7,
        module_name="Timeseries DAG",
        status=result7["status"],
        outputs=result7.get("outputs", {}),
        error_message=result7.get("error")
    ))

    # Module 8: Network Spillover
    module8_dir = artifacts_dir / "08_network"
    module8_dir.mkdir(exist_ok=True)

    result8 = run_wolfram_script(
        "08_network_spillover.wl",
        [
            "--input", f"{dataset_path}/network.csv",
            "--output", str(module8_dir / "network"),
            "--demo"
        ],
        module8_dir
    )

    modules_results.append(ModuleResult(
        module_id=8,
        module_name="Network Spillover",
        status=result8["status"],
        outputs=result8.get("outputs", {}),
        error_message=result8.get("error")
    ))

    # Module 9: Data Audit (Quality Gates)
    module9_dir = artifacts_dir / "09_audit"
    module9_dir.mkdir(exist_ok=True)

    result9 = run_wolfram_script(
        "09_data_audit.wl",
        [
            "--input", f"{dataset_path}/data.csv",
            "--treatment", req.treatment,
            "--outcome", req.outcome,
            "--covariates", features_str,
            "--output", str(module9_dir / "audit"),
            "--demo"
        ],
        module9_dir
    )

    modules_results.append(ModuleResult(
        module_id=9,
        module_name="Data Audit & Quality Gates",
        status=result9["status"],
        outputs=result9.get("outputs", {}),
        error_message=result9.get("error")
    ))

    # Module 10: Export & Reproducibility
    module10_dir = artifacts_dir / "10_export"
    module10_dir.mkdir(exist_ok=True)

    result10 = run_wolfram_script(
        "10_export_reproducibility.wl",
        [
            "--input", req.edges_csv or f"{dataset_path}/edges.csv",
            "--treatment", req.treatment,
            "--outcome", req.outcome,
            "--output", str(module10_dir / "export"),
            "--demo" if not req.edges_csv else ""
        ],
        module10_dir
    )

    modules_results.append(ModuleResult(
        module_id=10,
        module_name="Export & Reproducibility",
        status=result10["status"],
        outputs=result10.get("outputs", {}),
        error_message=result10.get("error")
    ))

    # 全体のステータスを判定
    all_success = all(m.status == "success" for m in modules_results)
    overall_status = "completed" if all_success else "partial"

    return DAGAnalysisResponse(
        job_id=job_id,
        status=overall_status,
        modules=modules_results,
        artifacts_dir=f"/artifacts/dag/{job_id}"
    )


@router.post("/module/{module_id}", response_model=ModuleResult)
async def run_single_module(module_id: int, req: DAGAnalysisRequest):
    """
    単一モジュールを実行
    """
    job_id = f"dag_m{module_id}_{uuid.uuid4().hex[:8]}"
    artifacts_dir = Path("artifacts/dag") / job_id
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    dataset_path = resolve_dataset_path(req.dataset_id)

    module_map = {
        1: ("01_interactive_dag.wl", ["--input", req.edges_csv or f"{dataset_path}/edges.csv", "--output", str(artifacts_dir / "interactive"), "--demo"]),
        2: ("02_identifiability.wl", ["--input", req.edges_csv or f"{dataset_path}/edges.csv", "--treatment", req.treatment, "--outcome", req.outcome, "--output", str(artifacts_dir / "identifiability"), "--demo"]),
        3: ("03_do_operator.wl", ["--input", f"{dataset_path}/data.csv", "--treatment", req.treatment, "--outcome", req.outcome, "--adjustment", "Z", "--output", str(artifacts_dir / "do_operator"), "--demo"]),
        4: ("04_path_bias_explorer.wl", ["--input", req.edges_csv or f"{dataset_path}/edges.csv", "--treatment", req.treatment, "--outcome", req.outcome, "--output", str(artifacts_dir / "path_bias"), "--demo"]),
        5: ("05_iv_tester.wl", ["--input", f"{dataset_path}/data.csv", "--treatment", req.treatment, "--outcome", req.outcome, "--instruments", "Z1,Z2", "--output", str(artifacts_dir / "iv_test"), "--demo"]),
        6: ("06_cate_heterogeneity.wl", ["--input", f"{dataset_path}/data.csv", "--treatment", req.treatment, "--outcome", req.outcome, "--features", "X1,X2,X3", "--output", str(artifacts_dir / "cate"), "--demo"]),
        7: ("07_timeseries_dag.wl", ["--input", f"{dataset_path}/timeseries.csv", "--output", str(artifacts_dir / "timeseries"), "--maxlag", "10", "--demo"]),
        8: ("08_network_spillover.wl", ["--input", f"{dataset_path}/network.csv", "--output", str(artifacts_dir / "network"), "--demo"]),
        9: ("09_data_audit.wl", ["--input", f"{dataset_path}/data.csv", "--treatment", req.treatment, "--outcome", req.outcome, "--covariates", "X1,X2,X3", "--output", str(artifacts_dir / "audit"), "--demo"]),
        10: ("10_export_reproducibility.wl", ["--input", req.edges_csv or f"{dataset_path}/edges.csv", "--treatment", req.treatment, "--outcome", req.outcome, "--output", str(artifacts_dir / "export"), "--demo"]),
    }

    if module_id not in module_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid module_id: {module_id}. Must be 1-10."
        )

    script_name, args = module_map[module_id]
    result = run_wolfram_script(script_name, args, artifacts_dir)

    module_names = {
        1: "Interactive DAG",
        2: "Identifiability Assistant",
        3: "do-Operator Runner",
        4: "Path & Bias Explorer",
        5: "IV Tester",
        6: "CATE Heterogeneity",
        7: "Timeseries DAG",
        8: "Network Spillover",
        9: "Data Audit & Quality Gates",
        10: "Export & Reproducibility"
    }

    return ModuleResult(
        module_id=module_id,
        module_name=module_names[module_id],
        status=result["status"],
        outputs=result.get("outputs", {}),
        error_message=result.get("error")
    )


@router.get("/job/{job_id}")
async def get_job_results(job_id: str):
    """
    ジョブ結果を取得
    """
    artifacts_dir = Path("artifacts/dag") / job_id

    if not artifacts_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job not found: {job_id}"
        )

    # 全てのモジュールディレクトリをスキャン
    modules = []
    for i in range(1, 11):
        module_dir = artifacts_dir / f"{i:02d}_*"
        matching_dirs = list(artifacts_dir.glob(f"{i:02d}_*"))

        if matching_dirs:
            module_dir = matching_dirs[0]
            outputs = {}
            for file in module_dir.glob("*"):
                if file.is_file():
                    rel_path = file.relative_to(Path("artifacts"))
                    outputs[file.name] = f"/artifacts/{rel_path}"

            modules.append({
                "module_id": i,
                "outputs": outputs
            })

    return {
        "job_id": job_id,
        "modules": modules,
        "artifacts_dir": f"/artifacts/dag/{job_id}"
    }


def resolve_dataset_path(dataset_id: str) -> str:
    """データセットパスを解決"""
    candidates = [
        f"data/packets/{dataset_id}",
        f"data/{dataset_id}",
        f"data/dag/{dataset_id}"
    ]

    for path in candidates:
        if Path(path).exists():
            return path

    # デフォルトパスを返す（存在しなくても--demoモードで動く）
    return f"data/dag/{dataset_id}"
