"""
TimescaleDBへのデータ投入スクリプト

特徴:
- ハイパーテーブルへの高速バルク挿入
- メトリクス記録
- トランザクション管理
"""

import pandas as pd
import psycopg2
from psycopg2.extras import execute_batch
import json
from datetime import datetime
import os


class TimescaleDBLoader:
    """TimescaleDB データローダー"""

    def __init__(self):
        self.db_url = os.getenv(
            "DATABASE_URL",
            "postgresql://cqox_user:changeme@localhost:5432/cqox_db"
        )

    def load_processed_data(self, csv_path: str, metadata_path: str):
        """前処理済みデータをTimescaleDBに投入"""
        print("=" * 80)
        print("TimescaleDBへのデータ投入")
        print("=" * 80)

        # データ読み込み
        df = pd.read_csv(csv_path)
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        print(f"\n読み込みデータ:")
        print(f"  行数: {len(df):,}")
        print(f"  列数: {len(df.columns)}")
        print(f"  ドメイン: {metadata['domain']}")

        # DB接続
        try:
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()

            # テーブル作成（存在しない場合）
            self._create_tables(cursor)
            conn.commit()

            # データセット登録
            dataset_id = self._insert_dataset(cursor, metadata)
            conn.commit()

            # ジョブ登録
            job_id = self._insert_job(cursor, dataset_id)
            conn.commit()

            # 生データ投入
            self._insert_raw_data(cursor, df, dataset_id)
            conn.commit()

            # メトリクス記録
            self._insert_metrics(cursor, df, job_id)
            conn.commit()

            print(f"\n✅ データ投入完了!")
            print(f"  Dataset ID: {dataset_id}")
            print(f"  Job ID: {job_id}")

            cursor.close()
            conn.close()

        except Exception as e:
            print(f"\n❌ エラー: {e}")
            print(f"  注意: TimescaleDBが起動していない場合、docker compose up -d timescaledb を実行してください")
            return None

    def _create_tables(self, cursor):
        """テーブル作成"""
        print("\nテーブル作成中...")

        # Datasets テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255),
                domain VARCHAR(100),
                confidence FLOAT,
                row_count INTEGER,
                column_count INTEGER,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                metadata JSONB
            );
        """)

        # Jobs テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id SERIAL PRIMARY KEY,
                dataset_id INTEGER REFERENCES datasets(id),
                status VARCHAR(50) DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Raw data テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS raw_marketing_data (
                id SERIAL PRIMARY KEY,
                dataset_id INTEGER REFERENCES datasets(id),
                user_id INTEGER,
                date TIMESTAMPTZ,
                treatment INTEGER,
                outcome FLOAT,
                cost FLOAT,
                propensity_score FLOAT,
                age FLOAT,
                income FLOAT,
                education VARCHAR(100),
                gender VARCHAR(50),
                region VARCHAR(100),
                cluster_id INTEGER,
                neighbor_exposure FLOAT,
                channel VARCHAR(100),
                customer_segment VARCHAR(100),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Metrics テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS metrics (
                id SERIAL PRIMARY KEY,
                job_id INTEGER REFERENCES jobs(id),
                metric_name VARCHAR(255),
                metric_value FLOAT,
                timestamp TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        print("  ✅ テーブル作成完了")

    def _insert_dataset(self, cursor, metadata):
        """データセット登録"""
        cursor.execute("""
            INSERT INTO datasets (name, domain, confidence, row_count, column_count, metadata)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id;
        """, (
            'marketing_campaign_10k',
            metadata['domain'],
            metadata['domain_confidence'],
            metadata['processed_shape'][0],
            metadata['processed_shape'][1],
            json.dumps(metadata)
        ))

        return cursor.fetchone()[0]

    def _insert_job(self, cursor, dataset_id):
        """ジョブ登録"""
        cursor.execute("""
            INSERT INTO jobs (dataset_id, status)
            VALUES (%s, %s)
            RETURNING id;
        """, (dataset_id, 'running'))

        return cursor.fetchone()[0]

    def _insert_raw_data(self, cursor, df, dataset_id):
        """生データ挿入（バルク）"""
        print(f"\n生データ挿入中（{len(df):,}行）...")

        # 必要なカラムを抽出
        records = []
        for _, row in df.iterrows():
            record = (
                dataset_id,
                int(row['user_id']) if 'user_id' in df.columns else None,
                pd.to_datetime(row['date']) if 'date' in df.columns else None,
                int(row['treatment']) if 'treatment' in df.columns else None,
                float(row['y']) if 'y' in df.columns and pd.notna(row['y']) else None,
                float(row['cost']) if 'cost' in df.columns else None,
                float(row['propensity_score']) if 'propensity_score' in df.columns else None,
                float(row['age']) if 'age' in df.columns and pd.notna(row['age']) else None,
                float(row['income']) if 'income' in df.columns and pd.notna(row['income']) else None,
                str(row['education']) if 'education' in df.columns else None,
                str(row['gender']) if 'gender' in df.columns else None,
                str(row['region']) if 'region' in df.columns else None,
                int(row['cluster_id']) if 'cluster_id' in df.columns else None,
                float(row['neighbor_exposure']) if 'neighbor_exposure' in df.columns else None,
                str(row['channel']) if 'channel' in df.columns else None,
                str(row['customer_segment']) if 'customer_segment' in df.columns else None,
            )
            records.append(record)

        # バルク挿入
        execute_batch(cursor, """
            INSERT INTO raw_marketing_data (
                dataset_id, user_id, date, treatment, outcome, cost,
                propensity_score, age, income, education, gender, region,
                cluster_id, neighbor_exposure, channel, customer_segment
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, records, page_size=1000)

        print(f"  ✅ {len(records):,}行挿入完了")

    def _insert_metrics(self, cursor, df, job_id):
        """メトリクス記録"""
        print("\nメトリクス記録中...")

        metrics = [
            ('total_rows', len(df)),
            ('treatment_rate', df['treatment'].mean() if 'treatment' in df.columns else 0),
            ('avg_outcome', df['y'].mean() if 'y' in df.columns else 0),
            ('avg_cost', df['cost'].mean() if 'cost' in df.columns else 0),
        ]

        for metric_name, metric_value in metrics:
            cursor.execute("""
                INSERT INTO metrics (job_id, metric_name, metric_value)
                VALUES (%s, %s, %s)
            """, (job_id, metric_name, float(metric_value)))

        print(f"  ✅ {len(metrics)}個のメトリクス記録完了")


if __name__ == "__main__":
    loader = TimescaleDBLoader()

    loader.load_processed_data(
        csv_path="/home/hirokionodera//CQO/data/marketing_campaign_10k_processed.csv",
        metadata_path="/home/hirokionodera/CQO/data/preprocessing_metadata.json"
    )
