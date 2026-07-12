import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.db_models import Student, Session, ModelPrediction, User
from app.dependencies.deps import get_cache_service, check_permissions
from app.cache.service import CacheService
from app.schemas.dashboard import DashboardSummary, RiskStudentItem, AlertOut

router = APIRouter()

@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    db: AsyncSession = Depends(get_db),
    cache_service: CacheService = Depends(get_cache_service),
    current_user: User = Depends(check_permissions("viewer"))
):
    """Retrieve aggregate KPI statistics (total students, average engagement, total alerts) (Cached)."""
    cache_key = "dashboard:summary"
    cached = cache_service.get(cache_key)
    if cached:
        return cached

    # 1. Total students count
    total_students = await db.scalar(select(func.count(Student.id))) or 0

    # 2. Average engagement score across all sessions
    avg_engagement = await db.scalar(select(func.avg(Session.engagement_score))) or 0.0

    # 3. Total anomaly alerts (Isolation Forest predictions where is_anomaly = true)
    # Using JSONB querying
    anomaly_query = (
        select(func.count(ModelPrediction.id))
        .filter(
            ModelPrediction.model_name == "isolation_forest",
            ModelPrediction.prediction["is_anomaly"].astext == "true"
        )
    )
    total_anomaly_alerts = await db.scalar(anomaly_query) or 0

    # 4. Risk distribution (how many students are predicted as at-risk vs safe)
    # Get the latest prediction of logistic_regression for each student
    subquery = (
        select(
            ModelPrediction.student_id,
            ModelPrediction.prediction["at_risk"].astext.label("at_risk"),
            func.row_number().over(
                partition_by=ModelPrediction.student_id,
                order_by=desc(ModelPrediction.created_at)
            ).label("rn")
        )
        .filter(ModelPrediction.model_name == "logistic_regression")
        .subquery()
    )
    
    risk_dist_query = (
        select(subquery.c.at_risk, func.count(subquery.c.student_id))
        .filter(subquery.c.rn == 1)
        .group_by(subquery.c.at_risk)
    )
    
    risk_rows = await db.execute(risk_dist_query)
    risk_distribution = {"at_risk": 0, "safe": 0}
    for row in risk_rows.all():
        is_at_risk = row[0] == "true"
        count = row[1]
        if is_at_risk:
            risk_distribution["at_risk"] = count
        else:
            risk_distribution["safe"] = count

    summary = {
        "total_students": total_students,
        "avg_engagement": float(avg_engagement),
        "total_anomaly_alerts": total_anomaly_alerts,
        "risk_distribution": risk_distribution
    }

    cache_service.set(cache_key, summary, ttl=60)
    return summary

@router.get("/risk-students", response_model=List[RiskStudentItem])
async def get_top_risk_students(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions("viewer"))
):
    """Retrieve top 10 at-risk students based on prediction history (Viewer/Admin)."""
    # Latest logistic_regression predictions per student
    subquery = (
        select(
            ModelPrediction.student_id,
            ModelPrediction.prediction["at_risk"].astext.label("at_risk"),
            ModelPrediction.confidence,
            ModelPrediction.created_at,
            func.row_number().over(
                partition_by=ModelPrediction.student_id,
                order_by=desc(ModelPrediction.created_at)
            ).label("rn")
        )
        .filter(ModelPrediction.model_name == "logistic_regression")
        .subquery()
    )
    
    # Query details joining Student and average engagement
    query = (
        select(
            Student.id.label("student_id"),
            Student.name,
            Student.email,
            Student.department,
            subquery.c.confidence.label("risk_confidence")
        )
        .join(subquery, Student.id == subquery.c.student_id)
        .filter(subquery.c.rn == 1, subquery.c.at_risk == "true")
        .order_by(desc(subquery.c.confidence))
        .limit(10)
    )
    
    results = await db.execute(query)
    risk_students = []
    
    for row in results.all():
        # Fetch average engagement score for the student
        avg_eng = await db.scalar(
            select(func.avg(Session.engagement_score))
            .filter(Session.student_id == row.student_id)
        ) or 0.0
        
        risk_students.append({
            "student_id": row.student_id,
            "name": row.name,
            "email": row.email,
            "department": row.department,
            "avg_engagement": float(avg_eng),
            "at_risk_prediction": True,
            "risk_confidence": float(row.risk_confidence)
        })
        
    return risk_students

@router.get("/alerts", response_model=List[AlertOut])
async def get_latest_alerts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(check_permissions("viewer"))
):
    """Retrieve latest 20 anomaly alerts detected by Isolation Forest."""
    query = (
        select(
            ModelPrediction.student_id,
            ModelPrediction.prediction,
            ModelPrediction.created_at,
            Student.name.label("student_name")
        )
        .join(Student, ModelPrediction.student_id == Student.id)
        .filter(
            ModelPrediction.model_name == "isolation_forest",
            ModelPrediction.prediction["is_anomaly"].astext == "true"
        )
        .order_by(desc(ModelPrediction.created_at))
        .limit(20)
    )
    
    results = await db.execute(query)
    alerts = []
    
    for row in results.all():
        # Get the session details that triggered the anomaly (the latest session before/at prediction time)
        session_query = (
            select(Session)
            .filter(
                Session.student_id == row.student_id,
                Session.start_time <= row.created_at
            )
            .order_by(desc(Session.start_time))
            .limit(1)
        )
        sess = await db.scalar(session_query)
        
        if sess:
            alerts.append({
                "session_id": sess.id,
                "student_id": row.student_id,
                "student_name": row.student_name,
                "timestamp": sess.start_time,
                "inactivity_duration": sess.inactivity_duration,
                "wrong_answers": sess.wrong_answers,
                "response_time": float(sess.response_time),
                "anomaly_score": float(row.prediction.get("anomaly_score", 0.0))
            })
            
    return alerts
