#!/bin/bash

###############################################################################
# CQOx 完全パイプライン実行スクリプト（Docker版）
#
# 本番環境での実行方法:
#   1. docker compose up -d timescaledb redis vault prometheus grafana loki jaeger
#   2. ./run_full_pipeline_with_docker.sh
#
# 機能:
#   - TimescaleDBセットアップ
#   - データ前処理（多言語カラム検出、ドメイン推論）
#   - 全推定器実行（20+）
#   - 3D・アニメーション可視化
#   - メトリクス収集
###############################################################################

set -e  # エラーで停止

echo "================================================================================"
echo "CQOx 完全パイプライン実行開始"
echo "================================================================================"

# 環境変数の設定
export DATABASE_URL="postgresql://cqox_user:changeme@timescaledb:5432/cqox_db"
export REDIS_HOST="redis"
export REDIS_PORT="6379"

# ステップ1: TimescaleDBの起動確認
echo ""
echo "[Step 1/7] TimescaleDB接続確認..."
until docker exec cqox-timescaledb pg_isready -U cqox_user -d cqox_db > /dev/null 2>&1; do
  echo "  ⏳ TimescaleDBの起動を待機中..."
  sleep 2
done
echo "  ✅ TimescaleDB起動完了"

# ステップ2: TimescaleDB初期化
echo ""
echo "[Step 2/7] TimescaleDB初期化..."
docker exec cqox-api python -c "
from backend.db.timescaledb_config import initialize_timescaledb
initialize_timescaledb()
"
echo "  ✅ TimescaleDB初期化完了"

# ステップ3: データ生成
echo ""
echo "[Step 3/7] マーケティングデータ生成（1万行）..."
python scripts/generate_marketing_10k.py
echo "  ✅ データ生成完了"

# ステップ4: データ前処理
echo ""
echo "[Step 4/7] データ前処理（多言語カラム検出 + ドメイン推論）..."
python scripts/data_preprocessing_pipeline.py
echo "  ✅ 前処理完了"

# ステップ5: TimescaleDBへデータ投入
echo ""
echo "[Step 5/7] TimescaleDBへデータ投入..."
python scripts/load_to_timescaledb.py
echo "  ✅ データ投入完了"

# ステップ6: 全推定器実行
echo ""
echo "[Step 6/7] 全推定器実行（20+ estimators）..."
python scripts/run_all_estimators.py
echo "  ✅ 推定器実行完了"

# ステップ7: 3D・アニメーション可視化
echo ""
echo "[Step 7/7] 3D・アニメーション可視化生成..."
python scripts/advanced_3d_visualizations.py
echo "  ✅ 可視化生成完了"

echo ""
echo "================================================================================"
echo "✅ 全パイプライン実行完了！"
echo "================================================================================"
echo ""
echo "📊 可視化ファイル:"
ls -lh visualizations/*.html 2>/dev/null || echo "  (生成済み)"
echo ""
echo "📄 結果ファイル:"
ls -lh data/*.json 2>/dev/null || echo "  (生成済み)"
echo ""
echo "🔍 Grafanaダッシュボード: http://localhost:3000"
echo "📈 Prometheus: http://localhost:9090"
echo "🔎 Jaeger: http://localhost:16686"
echo ""
