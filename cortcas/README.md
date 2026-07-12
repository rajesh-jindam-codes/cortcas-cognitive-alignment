# CORTCAS: Continuous Observation & Reality-Tracked Cognitive Alignment System

CORTCAS is an educational monitoring and student alignment platform. It aggregates student behavioral events and session data, trains multiple machine learning models to identify at-risk behaviors, segments engagement profiles, flags anomalies, and serves predictions via a highly optimized FastAPI REST API.

---

## System Architecture

```mermaid
flowchart TD
    subgraph Client Layer
        React[React Dashboard]
        Locust[Locust Benchmark]
    end

    subgraph API & Service Layer [FastAPI Application]
        Router[API Router]
        Auth[JWT & RBAC Middleware]
        Deps[Dependency Injections]
        Cache[Cache Service]
        MF[Model Factory]
    end

    subgraph Cache Layer
        Redis[(Redis Cache)]
        MemCache[In-Memory Fallback]
    end

    subgraph ML Inference Layer [scikit-learn]
        LR[Logistic Regression: At-Risk Classifier]
        KM[KMeans: Engagement Profiler]
        IF[Isolation Forest: Anomaly Detector]
    end

    subgraph Data Layer
        Repo[Async Repository Layer]
        DB[(PostgreSQL DB)]
    end

    React -->|REST Calls| Router
    Locust -->|Load Tests| Router
    Router --> Auth
    Auth --> Deps
    Deps --> Cache
    Deps --> Repo
    Deps --> MF
    
    Cache -->|Fast Reads| Redis
    Cache -->|Local Failover| MemCache
    
    MF -->|Predict Risk| LR
    MF -->|Segment Profile| KM
    MF -->|Scan Session Anomaly| IF
    
    Repo -->|Async Queries| DB
    MF -->|Record Prediction| Repo
```

---

## Technology Stack

* **Backend Framework**: FastAPI (Async ASGI)
* **ORM & Database**: SQLAlchemy 2.0 (Async) + Alembic migrations + PostgreSQL
* **Caching**: Redis (with automatic thread-safe Local In-Memory TTL fallback)
* **Machine Learning**: scikit-learn (Logistic Regression, KMeans, Isolation Forest)
* **Task Automation & Run**: Docker & Docker Compose
* **CI/CD Pipeline**: GitHub Actions

---

## Configuration Variables

Configured via the `.env` file in the project root:

| Key | Description | Default Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | Asyncpg PostgreSQL URL | `postgresql+asyncpg://postgres:1803@localhost:5432/cortcas` |
| `SYNC_DATABASE_URL` | Sync psycopg2 URL | `postgresql://postgres:1803@localhost:5432/cortcas` |
| `REDIS_URL` | Redis Cache URI | `redis://localhost:6379/0` |
| `SECRET_KEY` | JWT signature seed key | (HMAC SHA-256 Secret) |
| `ALGORITHM` | JWT hashing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifespan | `30` |

---

## Getting Started

### Method 1: Docker Compose (Entire Stack)

Spin up PostgreSQL, Redis, the FastAPI Backend, and the Nginx Frontend proxy with a single command:
```bash
docker compose up --build -d
```
* **FastAPI Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Frontend proxy URL**: [http://localhost/](http://localhost/)

### Method 2: Local Setup (Developer Mode)

1. **Install Python dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```
2. **Apply Migrations**:
   ```bash
   alembic upgrade head
   ```
3. **Seed Database**:
   ```bash
   python scripts/generate_data.py
   ```
4. **Train ML Models**:
   ```bash
   python app/ml/train.py
   ```
5. **Start Dev Server**:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## API Endpoints List (Selected)

| Method | Endpoint | Access Role | Description |
| :--- | :--- | :--- | :--- |
| **POST** | `/api/v1/auth/register` | Open | Create platform credentials |
| **POST** | `/api/v1/auth/login` | Open | Authenticate and get JWT token pair |
| **GET** | `/api/v1/students/` | Viewer/Admin | Retrieve student lists (Paginated) |
| **POST** | `/api/v1/students/` | Admin | Create a student profile |
| **POST** | `/api/v1/predictions/predict/{student_id}` | Viewer/Admin | Perform ML inference and save results |
| **GET** | `/api/v1/dashboard/summary` | Viewer/Admin | KPI Summary Stats (Cached) |
| **GET** | `/api/v1/dashboard/alerts` | Viewer/Admin | Isolation Forest anomalies |

---

## Performance Summary

### Caching Performance Benchmarks
A comparison between hitting the database query aggregates directly vs. hitting the cache service layer (compiled via `pytest-benchmark`):

* **Direct DB Query Latency (Mean)**: **2.19 milliseconds** (456.6 OPS)
* **Cache Service Lookup Latency (Mean)**: **3.81 microseconds** (262,166.3 OPS)
* **Efficiency Boost**: **574x Speedup**

### Database Query Benchmarks
Adding composite indices resulted in a **9.0x speedup** on student session lookups (Bitmap Index Scan vs. Sequential Scan), dropping execution scan times from **1.139 ms** to **0.126 ms**.

---

## Machine Learning Layer Details

1. **Logistic Regression (Classifier)**:
   * Classifies student at-risk status (binary).
   * Accuracy: `98.67%` | Precision: `100.00%` | Recall: `95.24%` | ROC-AUC: `99.91%`.
2. **KMeans Clustering (Profiler)**:
   * Segments students into 4 distinct groups (`Highly Engaged`, `Average`, `Irregular`, `At Risk`).
   * Silhouette Score: `0.7443` (K=4 is the optimal inflection curve).
3. **Isolation Forest (Anomaly Detection)**:
   * Flags student sessions exhibiting irregular patterns.
   * Contamination Rate: `3.01%`.
   * Anomalous sessions average **1,731.95 seconds** of inactivity compared to **284.53 seconds** for normal.
