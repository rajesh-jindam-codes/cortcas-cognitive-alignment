import uuid
from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel

class DashboardSummary(BaseModel):
    total_students: int
    avg_engagement: float
    total_anomaly_alerts: int
    risk_distribution: Dict[str, int]

class RiskStudentItem(BaseModel):
    student_id: uuid.UUID
    name: str
    email: str
    department: str
    avg_engagement: float
    at_risk_prediction: bool
    risk_confidence: float

class AlertOut(BaseModel):
    session_id: uuid.UUID
    student_id: uuid.UUID
    student_name: str
    timestamp: datetime
    inactivity_duration: int
    wrong_answers: int
    response_time: float
    anomaly_score: float
