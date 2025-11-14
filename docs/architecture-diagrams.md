# CQOx System Architecture Diagrams

This document contains comprehensive system architecture diagrams for the CQOx platform.

## Table of Contents
1. [High-Level System Architecture](#high-level-system-architecture)
2. [Data Flow Architecture](#data-flow-architecture)
3. [Causal Inference Pipeline](#causal-inference-pipeline)
4. [Microservices Architecture](#microservices-architecture)
5. [Database Schema](#database-schema)
6. [Deployment Architecture](#deployment-architecture)
7. [Security Architecture](#security-architecture)

---

## High-Level System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        UI[React Frontend]
        API_CLIENT[API Clients<br/>Python/R/JS SDKs]
    end

    subgraph "API Gateway Layer"
        GATEWAY[FastAPI Gateway<br/>Rate Limiting<br/>Authentication<br/>Circuit Breaker]
    end

    subgraph "Application Layer"
        ENGINE[Causal Engine<br/>20+ Estimators]
        COMPOSER[Analysis Composer<br/>Parallel Execution]
        VALIDATOR[Quality Gates<br/>Schema Validator]
    end

    subgraph "Data Processing Layer"
        PARQUET[Parquet Pipeline<br/>Encoding Detection]
        COLUMN_MAP[Column Mapper<br/>6-Language Support]
        PREPROCESSOR[Preprocessor<br/>Normalization]
    end

    subgraph "Inference Layer"
        PSM[PSM Estimator]
        IPW[IPW Estimator]
        DID[DiD Estimator]
        IV[IV Estimator]
        RD[RD Estimator]
        CATE[CATE Estimator]
        FOREST[Causal Forest]
        NETWORK[Network Effects]
        GEOGRAPHIC[Geographic]
        OTHERS[15+ More...]
    end

    subgraph "Visualization Layer"
        WOLFRAM[WolframONE<br/>3D/Animation]
        PLOTLY[Plotly Interactive]
        MATPLOTLIB[Matplotlib 2D]
    end

    subgraph "Storage Layer"
        TIMESCALE[(TimescaleDB<br/>Time-Series)]
        POSTGRES[(PostgreSQL<br/>Metadata)]
        REDIS[(Redis<br/>Cache)]
        S3[(S3/MinIO<br/>Artifacts)]
    end

    subgraph "Observability Layer"
        PROMETHEUS[Prometheus<br/>Metrics]
        GRAFANA[Grafana<br/>Dashboards]
        JAEGER[Jaeger<br/>Tracing]
        LOKI[Loki<br/>Logs]
    end

    subgraph "Infrastructure Layer"
        K8S[Kubernetes<br/>Orchestration]
        ARGOCD[ArgoCD<br/>GitOps]
        ISTIO[Istio<br/>Service Mesh]
    end

    UI --> GATEWAY
    API_CLIENT --> GATEWAY
    GATEWAY --> ENGINE
    ENGINE --> COMPOSER
    COMPOSER --> VALIDATOR
    VALIDATOR --> PARQUET
    PARQUET --> COLUMN_MAP
    COLUMN_MAP --> PREPROCESSOR

    COMPOSER --> PSM
    COMPOSER --> IPW
    COMPOSER --> DID
    COMPOSER --> IV
    COMPOSER --> RD
    COMPOSER --> CATE
    COMPOSER --> FOREST
    COMPOSER --> NETWORK
    COMPOSER --> GEOGRAPHIC
    COMPOSER --> OTHERS

    PSM --> WOLFRAM
    IPW --> PLOTLY
    DID --> MATPLOTLIB

    ENGINE --> TIMESCALE
    ENGINE --> POSTGRES
    ENGINE --> REDIS
    ENGINE --> S3

    ENGINE --> PROMETHEUS
    PROMETHEUS --> GRAFANA
    ENGINE --> JAEGER
    ENGINE --> LOKI

    K8S --> ENGINE
    ARGOCD --> K8S
    ISTIO --> K8S

    style ENGINE fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style WOLFRAM fill:#FF9800,stroke:#E65100,stroke-width:3px
    style TIMESCALE fill:#2196F3,stroke:#0D47A1,stroke-width:3px
```

---

## Data Flow Architecture

```mermaid
flowchart LR
    subgraph "Input"
        CSV[CSV Files]
        JSON[JSON Files]
        PARQUET_IN[Parquet Files]
        EXCEL[Excel Files]
        DB_IN[Database]
    end

    subgraph "Ingestion & Validation"
        UPLOAD[Multi-Format<br/>Upload API]
        ENCODING[Encoding<br/>Detection<br/>UTF-8/Shift-JIS]
        CONVERT[Parquet<br/>Conversion]
        SCHEMA[Schema<br/>Validation<br/>Pandera]
    end

    subgraph "Data Preparation"
        MAPPING[Column<br/>Mapping<br/>Auto-Inference]
        CLEAN[Data<br/>Cleaning<br/>Missing/Outliers]
        TRANSFORM[Feature<br/>Engineering]
        QUALITY[Quality<br/>Gates<br/>SMD/VIF]
    end

    subgraph "Causal Analysis"
        ESTIMATOR_SELECT[Estimator<br/>Selection<br/>Auto/Manual]
        PARALLEL[Parallel<br/>Execution<br/>ThreadPool]
        INFERENCE[Inference<br/>20+ Methods]
        SENSITIVITY[Sensitivity<br/>Analysis<br/>E-value]
    end

    subgraph "Visualization"
        VIZ_GEN[Visualization<br/>Generation<br/>42+ Figures]
        WOLFRAM_VIZ[WolframONE<br/>3D/Animation]
        INTERACTIVE[Interactive<br/>Plotly/D3]
    end

    subgraph "Output"
        JSON_OUT[JSON<br/>Results]
        PDF[PDF<br/>Reports]
        HTML[HTML<br/>Dashboards]
        POLICY[Policy<br/>Files CSV]
    end

    subgraph "Storage"
        TIMESCALE_STORE[(TimescaleDB<br/>Panel Data)]
        POSTGRES_STORE[(PostgreSQL<br/>Metadata)]
        S3_STORE[(S3<br/>Artifacts)]
    end

    CSV --> UPLOAD
    JSON --> UPLOAD
    PARQUET_IN --> UPLOAD
    EXCEL --> UPLOAD
    DB_IN --> UPLOAD

    UPLOAD --> ENCODING
    ENCODING --> CONVERT
    CONVERT --> SCHEMA

    SCHEMA --> MAPPING
    MAPPING --> CLEAN
    CLEAN --> TRANSFORM
    TRANSFORM --> QUALITY

    QUALITY --> ESTIMATOR_SELECT
    ESTIMATOR_SELECT --> PARALLEL
    PARALLEL --> INFERENCE
    INFERENCE --> SENSITIVITY

    SENSITIVITY --> VIZ_GEN
    VIZ_GEN --> WOLFRAM_VIZ
    VIZ_GEN --> INTERACTIVE

    WOLFRAM_VIZ --> JSON_OUT
    INTERACTIVE --> PDF
    WOLFRAM_VIZ --> HTML
    INFERENCE --> POLICY

    INFERENCE --> TIMESCALE_STORE
    INFERENCE --> POSTGRES_STORE
    VIZ_GEN --> S3_STORE

    style INFERENCE fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style WOLFRAM_VIZ fill:#FF9800,stroke:#E65100,stroke-width:3px
    style TIMESCALE_STORE fill:#2196F3,stroke:#0D47A1,stroke-width:3px
```

---

## Causal Inference Pipeline

```mermaid
sequenceDiagram
    participant Client
    participant Gateway
    participant Engine
    participant Composer
    participant Estimators
    participant QualityGates
    participant Visualization
    participant Storage

    Client->>Gateway: POST /api/analyze/comprehensive
    activate Gateway
    Gateway->>Gateway: Authenticate (JWT)
    Gateway->>Gateway: Rate Limit Check
    Gateway->>Engine: Forward Request
    deactivate Gateway

    activate Engine
    Engine->>Engine: Load Data (Parquet)
    Engine->>Engine: Validate Schema
    Engine->>Composer: Orchestrate Analysis
    deactivate Engine

    activate Composer
    Composer->>Composer: Select Estimators (Auto/Manual)

    par Parallel Execution (ThreadPool)
        Composer->>Estimators: Run PSM
        activate Estimators
        Estimators-->>Composer: ATE=2.45, SE=0.32
        deactivate Estimators

        Composer->>Estimators: Run IPW
        activate Estimators
        Estimators-->>Composer: ATE=2.51, SE=0.35
        deactivate Estimators

        Composer->>Estimators: Run DiD
        activate Estimators
        Estimators-->>Composer: ATE=2.38, SE=0.28
        deactivate Estimators

        Composer->>Estimators: Run CATE
        activate Estimators
        Estimators-->>Composer: Heterogeneity Map
        deactivate Estimators
    end

    Composer->>QualityGates: Validate Results
    activate QualityGates
    QualityGates->>QualityGates: Check SMD < 0.1
    QualityGates->>QualityGates: Check Overlap > 90%
    QualityGates->>QualityGates: Check E-value > 2.0
    QualityGates-->>Composer: All Gates PASS (10/10)
    deactivate QualityGates

    Composer->>Visualization: Generate Figures
    activate Visualization

    par Parallel Visualization
        Visualization->>Visualization: WolframONE 3D Surface
        Visualization->>Visualization: Plotly Interactive
        Visualization->>Visualization: Matplotlib 2D
    end

    Visualization-->>Composer: 42 Figures Generated
    deactivate Visualization

    Composer->>Storage: Save Results
    activate Storage
    Storage->>Storage: Insert to TimescaleDB
    Storage->>Storage: Cache in Redis
    Storage->>Storage: Upload to S3
    Storage-->>Composer: Stored (job_id=abc123)
    deactivate Storage

    Composer-->>Engine: Analysis Complete
    deactivate Composer

    activate Engine
    Engine-->>Gateway: Response JSON
    deactivate Engine

    activate Gateway
    Gateway-->>Client: 200 OK + Results
    deactivate Gateway
```

---

## Microservices Architecture

```mermaid
graph TB
    subgraph "Frontend Services"
        REACT[React SPA<br/>Port 3000]
        NGINX[NGINX Reverse Proxy<br/>Port 80/443]
    end

    subgraph "API Services"
        GATEWAY_SVC[Gateway Service<br/>Port 8081<br/>Replicas: 3]
        ENGINE_SVC[Engine Service<br/>Port 8080<br/>Replicas: 5]
        WORKER_SVC[Worker Service<br/>Background Jobs<br/>Replicas: 10]
    end

    subgraph "Data Services"
        TIMESCALE_SVC[(TimescaleDB<br/>Port 5432<br/>HA: Primary+Replica)]
        POSTGRES_SVC[(PostgreSQL<br/>Port 5433<br/>HA: Primary+Replica)]
        REDIS_SVC[(Redis Cluster<br/>Port 6379<br/>3 Masters + 3 Replicas)]
    end

    subgraph "Storage Services"
        MINIO_SVC[(MinIO S3<br/>Port 9000<br/>Distributed: 4 nodes)]
    end

    subgraph "Observability Services"
        PROMETHEUS_SVC[Prometheus<br/>Port 9090]
        GRAFANA_SVC[Grafana<br/>Port 3001]
        JAEGER_SVC[Jaeger<br/>Port 16686]
        LOKI_SVC[Loki<br/>Port 3100]
    end

    subgraph "Infrastructure Services"
        ARGOCD_SVC[ArgoCD Server<br/>Port 8082]
        VAULT_SVC[HashiCorp Vault<br/>Port 8200<br/>HA: 3 nodes]
    end

    REACT --> NGINX
    NGINX --> GATEWAY_SVC
    GATEWAY_SVC --> ENGINE_SVC
    ENGINE_SVC --> WORKER_SVC

    ENGINE_SVC --> TIMESCALE_SVC
    ENGINE_SVC --> POSTGRES_SVC
    ENGINE_SVC --> REDIS_SVC
    ENGINE_SVC --> MINIO_SVC

    ENGINE_SVC --> PROMETHEUS_SVC
    PROMETHEUS_SVC --> GRAFANA_SVC
    ENGINE_SVC --> JAEGER_SVC
    ENGINE_SVC --> LOKI_SVC

    ARGOCD_SVC --> ENGINE_SVC
    ENGINE_SVC --> VAULT_SVC

    style ENGINE_SVC fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style TIMESCALE_SVC fill:#2196F3,stroke:#0D47A1,stroke-width:3px
    style REDIS_SVC fill:#D32F2F,stroke:#B71C1C,stroke-width:3px
```

---

## Database Schema

```mermaid
erDiagram
    DATASETS ||--o{ ANALYSES : "has"
    ANALYSES ||--o{ ESTIMATES : "produces"
    ANALYSES ||--o{ FIGURES : "generates"
    ANALYSES ||--o{ QUALITY_GATES : "validates"
    DATASETS ||--o{ TIME_SERIES_DATA : "contains"

    DATASETS {
        uuid id PK
        string name
        string domain
        int row_count
        jsonb schema
        timestamp created_at
        string uploaded_by
    }

    ANALYSES {
        uuid id PK
        uuid dataset_id FK
        string status
        jsonb config
        timestamp started_at
        timestamp completed_at
        float duration_seconds
    }

    ESTIMATES {
        uuid id PK
        uuid analysis_id FK
        string estimator
        float ate
        float se
        float ci_lower
        float ci_upper
        float p_value
        jsonb diagnostics
    }

    FIGURES {
        uuid id PK
        uuid analysis_id FK
        string figure_type
        string file_path
        string format
        int width
        int height
        timestamp generated_at
    }

    QUALITY_GATES {
        uuid id PK
        uuid analysis_id FK
        string gate_name
        string category
        float threshold
        float value
        boolean passed
        string severity
    }

    TIME_SERIES_DATA {
        uuid id PK
        uuid dataset_id FK
        timestamp time
        int unit_id
        int treatment
        float outcome
        jsonb covariates
        float propensity
    }
```

---

## Deployment Architecture

```mermaid
graph TB
    subgraph "GitHub"
        REPO[Git Repository<br/>Source of Truth]
    end

    subgraph "CI/CD Pipeline"
        GITHUB_ACTIONS[GitHub Actions<br/>Build + Test]
        DOCKER_BUILD[Docker Build<br/>Multi-stage]
        REGISTRY[Container Registry<br/>ECR/GCR/DockerHub]
    end

    subgraph "GitOps"
        ARGOCD_DEPLOY[ArgoCD<br/>Continuous Deployment]
        SYNC[Auto-Sync<br/>3-minute interval]
    end

    subgraph "Kubernetes Cluster - Production"
        INGRESS[Ingress Controller<br/>NGINX/Traefik]

        subgraph "Namespace: cqox-prod"
            ROLLOUT[Argo Rollouts<br/>Canary Deployment]

            subgraph "Canary Strategy"
                V1[Stable Version<br/>Replicas: 4<br/>Traffic: 90%]
                V2[Canary Version<br/>Replicas: 1<br/>Traffic: 10%]
            end

            HPA[Horizontal Pod<br/>Autoscaler<br/>Min: 2, Max: 10]
            PDB[Pod Disruption<br/>Budget<br/>MinAvailable: 50%]
        end

        subgraph "Namespace: cqox-monitoring"
            PROM_DEPLOY[Prometheus]
            GRAFANA_DEPLOY[Grafana]
            ALERT_MANAGER[AlertManager]
        end
    end

    subgraph "Analysis Engine"
        ANALYSIS[Prometheus<br/>Analysis]
        METRICS[Success Rate > 95%<br/>Latency P99 < 1s]
    end

    subgraph "Rollback Decision"
        AUTO_ROLLBACK{Metrics<br/>Failing?}
    end

    REPO --> GITHUB_ACTIONS
    GITHUB_ACTIONS --> DOCKER_BUILD
    DOCKER_BUILD --> REGISTRY
    REGISTRY --> ARGOCD_DEPLOY
    ARGOCD_DEPLOY --> SYNC
    SYNC --> INGRESS
    INGRESS --> ROLLOUT
    ROLLOUT --> V1
    ROLLOUT --> V2
    ROLLOUT --> HPA
    ROLLOUT --> PDB

    V2 --> ANALYSIS
    ANALYSIS --> METRICS
    METRICS --> AUTO_ROLLBACK
    AUTO_ROLLBACK -->|Yes| V1
    AUTO_ROLLBACK -->|No| V2

    PROM_DEPLOY --> ANALYSIS
    GRAFANA_DEPLOY --> PROM_DEPLOY
    ALERT_MANAGER --> PROM_DEPLOY

    style ROLLOUT fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style AUTO_ROLLBACK fill:#FF5722,stroke:#BF360C,stroke-width:3px
    style V2 fill:#FFC107,stroke:#F57F17,stroke-width:2px
```

---

## Security Architecture

```mermaid
graph TB
    subgraph "External"
        USER[End User]
        API_USER[API Client]
    end

    subgraph "Edge Security"
        CLOUDFLARE[Cloudflare<br/>DDoS Protection<br/>WAF]
        TLS_TERM[TLS 1.3<br/>Termination]
    end

    subgraph "Authentication Layer"
        JWT_AUTH[JWT Validation<br/>HS256/RS256]
        OAUTH[OAuth2 Provider<br/>Google/GitHub/MS]
        API_KEY[API Key Auth<br/>Service-to-Service]
    end

    subgraph "Authorization Layer"
        RBAC[Role-Based Access<br/>Admin/Analyst/Viewer]
        POLICY[Policy Engine<br/>OPA/Casbin]
    end

    subgraph "Application Security"
        RATE_LIMIT[Rate Limiting<br/>100 req/min/IP]
        CIRCUIT_BREAKER[Circuit Breaker<br/>5 failures → open]
        INPUT_VAL[Input Validation<br/>Pydantic Schemas]
        SQL_INJECT[SQL Injection<br/>Prevention]
    end

    subgraph "Network Security"
        SERVICE_MESH[Istio Service Mesh<br/>mTLS]
        NETWORK_POLICY[Kubernetes<br/>Network Policies]
    end

    subgraph "Data Security"
        ENCRYPT_REST[Encryption at Rest<br/>AES-256]
        ENCRYPT_TRANSIT[Encryption in Transit<br/>TLS 1.3]
        VAULT_SECRETS[HashiCorp Vault<br/>Secret Management]
    end

    subgraph "Audit & Compliance"
        AUDIT_LOG[Audit Logging<br/>Immutable JSONL]
        GDPR[GDPR Compliance<br/>Data Portability]
        HIPAA[HIPAA Compliance<br/>PHI Protection]
    end

    USER --> CLOUDFLARE
    API_USER --> CLOUDFLARE
    CLOUDFLARE --> TLS_TERM
    TLS_TERM --> JWT_AUTH
    TLS_TERM --> OAUTH
    TLS_TERM --> API_KEY

    JWT_AUTH --> RBAC
    OAUTH --> RBAC
    API_KEY --> RBAC
    RBAC --> POLICY

    POLICY --> RATE_LIMIT
    RATE_LIMIT --> CIRCUIT_BREAKER
    CIRCUIT_BREAKER --> INPUT_VAL
    INPUT_VAL --> SQL_INJECT

    SQL_INJECT --> SERVICE_MESH
    SERVICE_MESH --> NETWORK_POLICY

    NETWORK_POLICY --> ENCRYPT_REST
    NETWORK_POLICY --> ENCRYPT_TRANSIT
    NETWORK_POLICY --> VAULT_SECRETS

    ENCRYPT_REST --> AUDIT_LOG
    AUDIT_LOG --> GDPR
    AUDIT_LOG --> HIPAA

    style JWT_AUTH fill:#4CAF50,stroke:#2E7D32,stroke-width:3px
    style SERVICE_MESH fill:#2196F3,stroke:#0D47A1,stroke-width:3px
    style AUDIT_LOG fill:#FF9800,stroke:#E65100,stroke-width:3px
```

---

## Performance Metrics Flow

```mermaid
flowchart LR
    subgraph "Application"
        APP[CQOx Engine]
        METRICS_LIB[Prometheus Client<br/>Library]
    end

    subgraph "Metrics Collection"
        PROMETHEUS[Prometheus Server<br/>Scrape Interval: 15s]
    end

    subgraph "Metrics Types"
        COUNTER[Counters<br/>http_requests_total]
        GAUGE[Gauges<br/>active_connections]
        HISTOGRAM[Histograms<br/>request_duration_seconds]
        SUMMARY[Summaries<br/>request_size_bytes]
    end

    subgraph "Visualization"
        GRAFANA[Grafana Dashboards]
        DASHBOARD_1[API Performance<br/>Latency/Throughput]
        DASHBOARD_2[Causal Analysis<br/>Estimator Execution]
        DASHBOARD_3[System Health<br/>CPU/Memory/Disk]
    end

    subgraph "Alerting"
        ALERT_RULES[Alert Rules<br/>PromQL]
        ALERT_MANAGER[AlertManager]
        PAGERDUTY[PagerDuty]
        SLACK[Slack]
    end

    APP --> METRICS_LIB
    METRICS_LIB --> PROMETHEUS
    PROMETHEUS --> COUNTER
    PROMETHEUS --> GAUGE
    PROMETHEUS --> HISTOGRAM
    PROMETHEUS --> SUMMARY

    COUNTER --> GRAFANA
    GAUGE --> GRAFANA
    HISTOGRAM --> GRAFANA
    SUMMARY --> GRAFANA

    GRAFANA --> DASHBOARD_1
    GRAFANA --> DASHBOARD_2
    GRAFANA --> DASHBOARD_3

    PROMETHEUS --> ALERT_RULES
    ALERT_RULES --> ALERT_MANAGER
    ALERT_MANAGER --> PAGERDUTY
    ALERT_MANAGER --> SLACK

    style PROMETHEUS fill:#E65100,stroke:#BF360C,stroke-width:3px
    style GRAFANA fill:#FF9800,stroke:#E65100,stroke-width:3px
```

---

## Notes

- All diagrams are rendered using Mermaid.js
- Diagrams are versioned with the codebase
- Update diagrams when architecture changes
- Export PNG versions for presentations: `mmdc -i diagram.mmd -o diagram.png`
