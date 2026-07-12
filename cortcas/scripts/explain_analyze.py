import asyncio
import os
import sys
import uuid
from typing import List, Dict, Any

import asyncpg

# Add project root to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

QUERIES = {
    "dashboard_aggregation": """
        SELECT student_id, AVG(engagement_score) as avg_engagement
        FROM sessions
        GROUP BY student_id;
    """,
    "student_session_lookup": """
        SELECT *
        FROM sessions
        WHERE student_id = $1
        ORDER BY start_time DESC
        LIMIT 20;
    """,
    "prediction_history": """
        SELECT *
        FROM model_predictions
        WHERE student_id = $1
        ORDER BY created_at DESC;
    """
}

# The indexes that directly impact our benchmark queries
TARGET_INDEXES = [
    {
        "name": "idx_sessions_student_id",
        "table": "sessions",
        "definition": "CREATE INDEX idx_sessions_student_id ON sessions (student_id);"
    },
    {
        "name": "idx_sessions_engagement_score",
        "table": "sessions",
        "definition": "CREATE INDEX idx_sessions_engagement_score ON sessions (engagement_score);"
    },
    {
        "name": "idx_sessions_student_id_created_at",
        "table": "sessions",
        "definition": "CREATE INDEX idx_sessions_student_id_created_at ON sessions (student_id, created_at);"
    },
    {
        "name": "idx_sessions_student_id_start_time",
        "table": "sessions",
        "definition": "CREATE INDEX idx_sessions_student_id_start_time ON sessions (student_id, start_time);"
    },
    {
        "name": "idx_model_predictions_student_id",
        "table": "model_predictions",
        "definition": "CREATE INDEX idx_model_predictions_student_id ON model_predictions (student_id);"
    },
    {
        "name": "idx_model_predictions_created_at",
        "table": "model_predictions",
        "definition": "CREATE INDEX idx_model_predictions_created_at ON model_predictions (created_at);"
    },
    {
        "name": "idx_model_predictions_student_id_created_at",
        "table": "model_predictions",
        "definition": "CREATE INDEX idx_model_predictions_student_id_created_at ON model_predictions (student_id, created_at);"
    }
]

async def run_explain(conn: asyncpg.Connection, query_key: str, student_id: uuid.UUID) -> str:
    raw_query = QUERIES[query_key]
    explain_query = f"EXPLAIN ANALYZE {raw_query}"
    
    if "$1" in raw_query:
        rows = await conn.fetch(explain_query, student_id)
    else:
        rows = await conn.fetch(explain_query)
        
    return "\n".join([row[0] for row in rows])

async def main():
    # Load settings database connection
    # Convert settings.DATABASE_URL (which has asyncpg://) to format suitable for asyncpg.connect
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    print(f"Connecting to database...")
    conn = await asyncpg.connect(db_url)
    
    # 1. Fetch a random student ID to make queries realistic
    student_record = await conn.fetchrow("SELECT id FROM students LIMIT 1;")
    if not student_record:
        print("Error: No students found in database. Run generate_data.py first.")
        await conn.close()
        sys.exit(1)
        
    student_id = student_record["id"]
    print(f"Benchmarking queries using student ID: {student_id}")
    
    # Let's write some mock model predictions first, in case model_predictions table is empty
    # This ensures that query 3 ('prediction_history') returns rows and can be properly evaluated.
    pred_count = await conn.fetchval("SELECT COUNT(*) FROM model_predictions;")
    if pred_count == 0:
        print("Inserting dummy model predictions for benchmarking...")
        from datetime import datetime, timedelta
        for i in range(10):
            created_at = datetime.utcnow() - timedelta(days=i)
            await conn.execute(
                "INSERT INTO model_predictions (id, student_id, model_name, prediction, confidence, created_at) "
                "VALUES ($1, $2, $3, $4, $5, $6);",
                uuid.uuid4(), student_id, "logistic_regression", '{"at_risk": false}', 0.92, created_at
            )
            await conn.execute(
                "INSERT INTO model_predictions (id, student_id, model_name, prediction, confidence, created_at) "
                "VALUES ($1, $2, $3, $4, $5, $6);",
                uuid.uuid4(), student_id, "kmeans_clustering", '{"cluster": 1}', 1.0, created_at
            )
    
    # 2. BEFORE: Drop indexes
    print("Dropping indexes for baseline measurement...")
    for idx in TARGET_INDEXES:
        await conn.execute(f"DROP INDEX IF EXISTS {idx['name']};")
        
    # Run explain analyze BEFORE
    before_results = {}
    for key in QUERIES.keys():
        print(f"Running EXPLAIN ANALYZE for {key} (BEFORE)...")
        before_results[key] = await run_explain(conn, key, student_id)
        
    # 3. AFTER: Recreate indexes
    print("Recreating indexes for optimized measurement...")
    for idx in TARGET_INDEXES:
        await conn.execute(idx["definition"])
        
    # Run explain analyze AFTER
    after_results = {}
    for key in QUERIES.keys():
        print(f"Running EXPLAIN ANALYZE for {key} (AFTER)...")
        after_results[key] = await run_explain(conn, key, student_id)
        
    await conn.close()
    
    # 4. Generate the report
    report_content = f"""# EXPLAIN ANALYZE Query Optimization Report

This report compares performance of the 3 most expensive database queries in **CORTCAS** before and after applying optimized indexes.

**Benchmark Target Student ID**: `{student_id}`

---

## Query 1: Dashboard Aggregation
Average engagement score per student.

```sql
{QUERIES['dashboard_aggregation'].strip()}
```

### Before Indexes
```text
{before_results['dashboard_aggregation']}
```

### After Indexes
```text
{after_results['dashboard_aggregation']}
```

---

## Query 2: Student Session Lookup
Fetch latest 20 sessions for a specific student.

```sql
{QUERIES['student_session_lookup'].strip()}
```

### Before Indexes
```text
{before_results['student_session_lookup']}
```

### After Indexes
```text
{after_results['student_session_lookup']}
```

---

## Query 3: Prediction History
Fetch prediction history for a specific student.

```sql
{QUERIES['prediction_history'].strip()}
```

### Before Indexes
```text
{before_results['prediction_history']}
```

### After Indexes
```text
{after_results['prediction_history']}
```
"""
    
    # Save report to artifact directory
    artifact_dir = r"C:\Users\rajes\.gemini\antigravity-ide\brain\eaefe5d9-04d2-49cd-98b4-234cf6ee9ea3"
    report_path = os.path.join(artifact_dir, "explain_analyze_report.md")
    
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
        
    print(f"\nBenchmark completed! Report saved to {report_path}")

if __name__ == "__main__":
    asyncio.run(main())
