import uuid
from datetime import datetime
from typing import Dict, Any, List
from pydantic import BaseModel

class PredictionOut(BaseModel):
    id: uuid.UUID
    student_id: uuid.UUID
    model_name: str
    prediction: Dict[str, Any]
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True

class SinglePredictionResult(BaseModel):
    student_id: uuid.UUID
    risk_prediction: Dict[str, Any]
    cluster_prediction: Dict[str, Any]
    anomaly_prediction: Dict[str, Any]

class BatchPredictionOut(BaseModel):
    status: str
    predictions_count: int
    students_processed: int
