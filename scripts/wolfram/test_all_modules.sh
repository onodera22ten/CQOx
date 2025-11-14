#!/bin/bash
#
# Test All DAG Modules - Demo Mode
# Tests all 10 DAG visualization modules with synthetic data
#
# Usage: ./test_all_modules.sh
#

set -e

echo "=========================================="
echo "Testing All 10 DAG Modules (Demo Mode)"
echo "=========================================="
echo ""

# Create output directories
mkdir -p artifacts/dag/{interactive,identifiability,do_operator,path_bias,iv_test,cate,timeseries,network,audit,export}

echo "Module 1/10: Interactive DAG..."
wolframscript -file scripts/wolfram/dag/01_interactive_dag.wl \
  --demo \
  --output artifacts/dag/interactive/test

echo "✓ Module 1 complete"
echo ""

echo "Module 2/10: Identifiability..."
wolframscript -file scripts/wolfram/dag/02_identifiability.wl \
  --demo \
  --treatment X1 \
  --outcome Y \
  --output artifacts/dag/identifiability/test

echo "✓ Module 2 complete"
echo ""

echo "Module 3/10: do-Operator..."
wolframscript -file scripts/wolfram/dag/03_do_operator.wl \
  --demo \
  --treatment X \
  --outcome Y \
  --adjustment Z \
  --output artifacts/dag/do_operator/test

echo "✓ Module 3 complete"
echo ""

echo "Module 4/10: Path & Bias Explorer..."
wolframscript -file scripts/wolfram/dag/04_path_bias_explorer.wl \
  --demo \
  --treatment X1 \
  --outcome Y \
  --output artifacts/dag/path_bias/test

echo "✓ Module 4 complete"
echo ""

echo "Module 5/10: IV Tester..."
wolframscript -file scripts/wolfram/dag/05_iv_tester.wl \
  --demo \
  --treatment X \
  --outcome Y \
  --instruments Z \
  --output artifacts/dag/iv_test/test

echo "✓ Module 5 complete"
echo ""

echo "Module 6/10: CATE Heterogeneity..."
wolframscript -file scripts/wolfram/dag/06_cate_heterogeneity.wl \
  --demo \
  --treatment T \
  --outcome Y \
  --features X1,X2 \
  --output artifacts/dag/cate/test

echo "✓ Module 6 complete"
echo ""

echo "Module 7/10: Time-series DAG..."
wolframscript -file scripts/wolfram/dag/07_timeseries_dag.wl \
  --demo \
  --output artifacts/dag/timeseries/test \
  --maxlag 10

echo "✓ Module 7 complete"
echo ""

echo "Module 8/10: Network Spillover..."
wolframscript -file scripts/wolfram/dag/08_network_spillover.wl \
  --demo \
  --output artifacts/dag/network/test

echo "✓ Module 8 complete"
echo ""

echo "Module 9/10: Data Audit (Quality Gates)..."
wolframscript -file scripts/wolfram/dag/09_data_audit.wl \
  --demo \
  --treatment T \
  --outcome Y \
  --covariates X1,X2,X3 \
  --output artifacts/dag/audit/test

echo "✓ Module 9 complete"
echo ""

echo "Module 10/10: Export & Reproducibility..."
wolframscript -file scripts/wolfram/dag/10_export_reproducibility.wl \
  --demo \
  --treatment X1 \
  --outcome Y \
  --output artifacts/dag/export/test

echo "✓ Module 10 complete"
echo ""

echo "=========================================="
echo "✅ All 10 modules tested successfully!"
echo "=========================================="
echo ""
echo "Generated artifacts in: artifacts/dag/"
echo ""
echo "File count summary:"
find artifacts/dag -type f | wc -l | awk '{print "  Total files: " $1}'
find artifacts/dag -name "*.png" | wc -l | awk '{print "  PNG images: " $1}'
find artifacts/dag -name "*.svg" | wc -l | awk '{print "  SVG images: " $1}'
find artifacts/dag -name "*.json" | wc -l | awk '{print "  JSON files: " $1}'
find artifacts/dag -name "*.csv" | wc -l | awk '{print "  CSV files: " $1}'
find artifacts/dag -name "*.gif" | wc -l | awk '{print "  GIF animations: " $1}'
echo ""
echo "Next steps:"
echo "  1. Review generated visualizations in artifacts/dag/"
echo "  2. Integrate with FastAPI backend (backend/engine/router_dag.py)"
echo "  3. Connect to React frontend"
echo ""
