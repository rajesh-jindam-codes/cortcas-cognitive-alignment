import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

class SessionBase(BaseModel):
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    engagement_score: float
    focus_score: float
    inactivity_duration: int
    revision_count: int
    wrong_answers: int
    response_time: float

class SessionCreate(SessionBase):
    student_id: uuid.UUID

class SessionUpdate(BaseModel):
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    engagement_score: Optional[float] = None
    focus_score: Optional[float] = None
    inactivity_duration: Optional[int] = None
    revision_count: Optional[int] = None
    wrong_answers: Optional[int] = None
    response_time: Optional[float] = None

class SessionOut(SessionBase):
    id: uuid.UUID
    student_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True
