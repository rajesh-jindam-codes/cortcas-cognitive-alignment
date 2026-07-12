import pytest
import time
import psycopg2
from app.core.config import settings
from app.cache.service import CacheService

# Cache instance
cache = CacheService()

def test_db_lookup_benchmark(benchmark):
    """Benchmark direct DB query latency (Simulating Without Cache, with connection reused)."""
    # Open connection once for the benchmark session
    # Parse settings sync URL parameters
    conn = psycopg2.connect(
        dbname="cortcas",
        user="postgres",
        password="1803",
        host="localhost",
        port="5432"
    )
    
    def run_query():
        cursor = conn.cursor()
        
        # 1. Total students
        cursor.execute("SELECT COUNT(*) FROM students;")
        total_students = cursor.fetchone()[0]
        
        # 2. Average engagement
        cursor.execute("SELECT AVG(engagement_score) FROM sessions;")
        avg_engagement = float(cursor.fetchone()[0] or 0.0)
        
        # 3. Anomaly alert counts
        cursor.execute(
            "SELECT COUNT(*) FROM model_predictions "
            "WHERE model_name = 'isolation_forest' AND (prediction->>'is_anomaly')::boolean = true;"
        )
        total_anomaly_alerts = cursor.fetchone()[0]
        
        cursor.close()
        return {
            "total_students": total_students,
            "avg_engagement": avg_engagement,
            "total_anomaly_alerts": total_anomaly_alerts
        }
        
    try:
        res = benchmark(run_query)
        assert res["total_students"] > 0
    finally:
        conn.close()

def test_cached_lookup_benchmark(benchmark):
    """Benchmark CacheService lookup latency (Simulating With Cache)."""
    cache_key = "dashboard:summary_benchmark"
    
    # Seed cache
    dummy_summary = {
        "total_students": 300,
        "avg_engagement": 0.65,
        "total_anomaly_alerts": 240
    }
    cache.set(cache_key, dummy_summary, ttl=300)
    
    def run_cache():
        return cache.get(cache_key)
        
    res = benchmark(run_cache)
    assert res["total_students"] == 300
