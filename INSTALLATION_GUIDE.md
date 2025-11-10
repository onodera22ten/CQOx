# 📦 CQOx インストールガイド

**対象者**: エンジニア・非エンジニア両方
**所要時間**: 15〜30分

---

## 🎯 インストール方法の選択

### 方法1: Docker版（推奨） ⭐

**メリット**:
- ✅ 簡単・速い（コマンド2つで完了）
- ✅ 環境を汚さない
- ✅ 本番環境と同じ構成
- ✅ Windows/Mac/Linux すべて対応

**こんな人におすすめ**:
- 初めて使う人
- 手っ取り早く試したい人
- 本番環境を想定している人

### 方法2: ローカル版

**メリット**:
- ✅ カスタマイズしやすい
- ✅ デバッグしやすい

**こんな人におすすめ**:
- 開発者
- コードを改変したい人

---

## 🐳 方法1: Docker版インストール（推奨）

### 前提条件

以下がインストールされていること:
- Docker Desktop (Windows/Mac) または Docker Engine (Linux)
- Docker Compose

**インストール方法**:
- **Windows/Mac**: [Docker Desktop](https://www.docker.com/products/docker-desktop) をダウンロード&インストール
- **Linux**:
  ```bash
  # Ubuntu/Debian
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  ```

### ステップ1: プロジェクトのクローン

```bash
git clone https://github.com/onodera22ten/CQOx.git
cd CQOx
```

### ステップ2: 環境変数の設定

```bash
# .envファイルをコピー
cp .env.example .env

# 必要に応じて編集（デフォルトでOK）
nano .env  # または vim, code など
```

**重要な環境変数**:

```bash
# データベース
DB_USER=cqox_user
DB_PASSWORD=changeme  # 本番環境では必ず変更！
DB_NAME=cqox_db

# セキュリティ
JWT_SECRET_KEY=your-secret-key-here  # ランダムな文字列に変更
ENCRYPTION_KEY=your-encryption-key   # ランダムな文字列に変更
VAULT_TOKEN=root

# 可視化（オプション）
WOLFRAM_API_KEY=your-wolfram-api-key  # Wolfram APIを使う場合
```

### ステップ3: Docker起動

```bash
# すべてのサービスを起動
docker compose up -d

# 起動確認
docker compose ps
```

**起動するサービス**:
- TimescaleDB (データベース) - ポート5432
- Redis (キャッシュ) - ポート6379
- Vault (秘密管理) - ポート8200
- Prometheus (メトリクス) - ポート9090
- Grafana (可視化) - ポート3000
- Loki (ログ) - ポート3100
- Jaeger (トレーシング) - ポート16686
- CQOx API (メインAPI) - ポート8080
- Frontend (フロントエンド) - ポート4000

### ステップ4: パイプライン実行

```bash
# 完全パイプラインを実行
./scripts/run_full_pipeline_with_docker.sh
```

これにより以下が自動実行されます:
1. データ生成（1万行）
2. データ前処理
3. TimescaleDBへ投入
4. 全推定器実行（20種類）
5. 3D可視化生成

### ステップ5: 結果確認

#### ブラウザで確認

- **Grafana**: http://localhost:3000
  - ユーザー名: `admin`
  - パスワード: `admin`

- **Prometheus**: http://localhost:9090

- **Jaeger**: http://localhost:16686

#### 可視化ファイル確認

```bash
# 生成された可視化を確認
ls -lh visualizations/

# ブラウザで開く
open visualizations/3d_treatment_effect_surface.html  # Mac
xdg-open visualizations/3d_treatment_effect_surface.html  # Linux
start visualizations/3d_treatment_effect_surface.html  # Windows
```

### トラブルシューティング

#### ポート競合エラー

```
Error: Bind for 0.0.0.0:5432 failed: port is already allocated
```

**解決策**: docker-compose.yml のポート番号を変更

```yaml
ports:
  - "15432:5432"  # 5432 → 15432 に変更
```

#### メモリ不足エラー

**解決策**: Docker のメモリ割り当てを増やす

1. Docker Desktop → Settings → Resources
2. Memory を 8GB に設定

---

## 💻 方法2: ローカル版インストール

### 前提条件

- Python 3.11 以上
- PostgreSQL 15 以上（TimescaleDB拡張付き）
- Redis 7 以上

### ステップ1: Python環境構築

#### Python 3.11のインストール

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-dev
```

**macOS**:
```bash
brew install python@3.11
```

**Windows**:
- [Python.org](https://www.python.org/downloads/) からインストーラーをダウンロード

### ステップ2: 仮想環境作成

```bash
# プロジェクトディレクトリに移動
cd CQOx

# 仮想環境作成
python3.11 -m venv venv

# 仮想環境を有効化
# Linux/Mac:
source venv/bin/activate

# Windows:
venv\Scripts\activate
```

### ステップ3: 依存パッケージインストール

```bash
# pip を最新化
pip install --upgrade pip

# 依存パッケージをインストール
pip install -r requirements.txt
```

**requirements.txt の内容**:

```
# データ処理
pandas>=2.0.0
numpy>=1.24.0
pyarrow>=12.0.0

# 機械学習
scikit-learn>=1.3.0
scipy>=1.11.0

# 可視化
matplotlib>=3.7.0
seaborn>=0.12.0
plotly>=5.14.0
kaleido>=0.2.1

# データベース
psycopg2-binary>=2.9.0
sqlalchemy>=2.0.0
redis>=4.5.0

# API
fastapi>=0.100.0
uvicorn[standard]>=0.23.0
pydantic>=2.0.0

# 監視・ログ
prometheus-client>=0.17.0
python-json-logger>=2.0.0

# セキュリティ
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
python-multipart>=0.0.6

# テスト
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0

# その他
python-dotenv>=1.0.0
requests>=2.31.0
```

### ステップ4: TimescaleDB セットアップ

#### PostgreSQL + TimescaleDB インストール

**Ubuntu/Debian**:
```bash
# PostgreSQL リポジトリ追加
sudo sh -c 'echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" > /etc/apt/sources.list.d/timescaledb.list'
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -

# インストール
sudo apt update
sudo apt install timescaledb-2-postgresql-15

# TimescaleDB 設定
sudo timescaledb-tune

# PostgreSQL 再起動
sudo systemctl restart postgresql
```

**macOS**:
```bash
brew tap timescale/tap
brew install timescaledb

# 設定
timescaledb-tune

# 再起動
brew services restart postgresql
```

#### データベース作成

```bash
# PostgreSQL に接続
sudo -u postgres psql

# データベースとユーザー作成
CREATE DATABASE cqox_db;
CREATE USER cqox_user WITH ENCRYPTED PASSWORD 'changeme';
GRANT ALL PRIVILEGES ON DATABASE cqox_db TO cqox_user;

# TimescaleDB 拡張を有効化
\c cqox_db
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;

# 終了
\q
```

### ステップ5: Redis セットアップ

**Ubuntu/Debian**:
```bash
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**macOS**:
```bash
brew install redis
brew services start redis
```

**Windows**:
- [Redis for Windows](https://github.com/microsoftarchive/redis/releases) をダウンロード

### ステップ6: 環境変数設定

```bash
# .envファイル作成
cp .env.example .env

# 編集
nano .env
```

```.env
DATABASE_URL=postgresql://cqox_user:changeme@localhost:5432/cqox_db
REDIS_HOST=localhost
REDIS_PORT=6379
```

### ステップ7: データベース初期化

```bash
python -c "from backend.db.timescaledb_config import initialize_timescaledb; initialize_timescaledb()"
```

### ステップ8: パイプライン実行

```bash
# データ生成
python scripts/generate_marketing_10k.py

# 前処理
python scripts/data_preprocessing_pipeline.py

# データ投入
python scripts/load_to_timescaledb.py

# 推定器実行
python scripts/run_all_estimators.py

# 可視化生成
python scripts/advanced_3d_visualizations.py
```

---

## 🔍 動作確認

### 1. データベース接続確認

```bash
python -c "
import psycopg2
conn = psycopg2.connect('postgresql://cqox_user:changeme@localhost:5432/cqox_db')
print('✅ データベース接続成功')
conn.close()
"
```

### 2. Redis接続確認

```bash
python -c "
import redis
r = redis.Redis(host='localhost', port=6379)
r.ping()
print('✅ Redis接続成功')
"
```

### 3. 生成ファイル確認

```bash
# データファイル
ls -lh data/*.csv data/*.json

# 可視化ファイル
ls -lh visualizations/*.html
```

---

## 📊 オプション: 追加ツール

### 1. WolframONE（高度な可視化）

WolframONEを使うと、さらに高度な可視化が可能です。

```bash
# Wolfram API キーを取得
# https://account.wolfram.com/auth/create

# .env に追加
WOLFRAM_API_KEY=your-api-key-here
```

### 2. Jupyter Notebook（対話的分析）

```bash
pip install jupyter

# Notebook起動
jupyter notebook
```

---

## 🐛 トラブルシューティング

### よくあるエラー

#### 1. ModuleNotFoundError

```
ModuleNotFoundError: No module named 'pandas'
```

**解決策**:
```bash
pip install pandas
# または
pip install -r requirements.txt
```

#### 2. PostgreSQL接続エラー

```
could not connect to server: Connection refused
```

**解決策**:
```bash
# PostgreSQL が起動しているか確認
sudo systemctl status postgresql

# 起動
sudo systemctl start postgresql
```

#### 3. Redis接続エラー

```
redis.exceptions.ConnectionError: Error connecting to Redis
```

**解決策**:
```bash
# Redis が起動しているか確認
redis-cli ping

# 起動
sudo systemctl start redis-server
```

#### 4. メモリ不足エラー

```
MemoryError: Unable to allocate array
```

**解決策**:
- データサイズを削減
- サーバーのメモリを増やす

---

## 🔄 アップデート方法

### Git プル

```bash
git pull origin main
```

### 依存パッケージ更新

```bash
pip install -r requirements.txt --upgrade
```

### Dockerイメージ更新

```bash
docker compose pull
docker compose up -d --force-recreate
```

---

## 🗑️ アンインストール

### Docker版

```bash
# コンテナ停止・削除
docker compose down

# ボリューム削除（データも削除）
docker compose down -v

# イメージ削除
docker rmi $(docker images | grep cqox | awk '{print $3}')
```

### ローカル版

```bash
# 仮想環境削除
rm -rf venv

# データベース削除
sudo -u postgres psql -c "DROP DATABASE cqox_db;"
sudo -u postgres psql -c "DROP USER cqox_user;"
```

---

## 📞 サポート

問題が解決しない場合:
1. [Issues](https://github.com/onodera22ten/CQOx/issues) で検索
2. 新しいIssueを作成
3. 詳細なエラーメッセージとログを添付

---

## 🎉 インストール完了！

次は [EXECUTION_LOG.md](./EXECUTION_LOG.md) を見て、実際にシステムを動かしてみましょう！
