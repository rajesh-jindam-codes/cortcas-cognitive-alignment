import uuid
from datetime import datetime, date
from typing import List, Optional, Dict, Any
from sqlalchemy import (
    String, Integer, Float, DateTime, Date, ForeignKey, Boolean, Index
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="viewer", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        Index("idx_users_email", "email"),
        Index("idx_users_created_at", "created_at"),
    )

class Student(Base):
    __tablename__ = "students"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    age: Mapped[int] = mapped_column(Integer, nullable=False)
    gender: Mapped[str] = mapped_column(String(50), nullable=False)
    department: Mapped[str] = mapped_column(String(100), nullable=False)
    year_of_study: Mapped[int] = mapped_column(Integer, nullable=False)
    enrollment_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="student", cascade="all, delete-orphan")
    predictions: Mapped[List["ModelPrediction"]] = relationship("ModelPrediction", back_populates="student", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_students_email", "email"),
        Index("idx_students_created_at", "created_at"),
    )

class Session(Base):
    __tablename__ = "sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    engagement_score: Mapped[float] = mapped_column(Float, nullable=False)
    focus_score: Mapped[float] = mapped_column(Float, nullable=False)
    inactivity_duration: Mapped[int] = mapped_column(Integer, nullable=False)
    revision_count: Mapped[int] = mapped_column(Integer, nullable=False)
    wrong_answers: Mapped[int] = mapped_column(Integer, nullable=False)
    response_time: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="sessions")
    events: Mapped[List["BehavioralEvent"]] = relationship("BehavioralEvent", back_populates="session", cascade="all, delete-orphan")
    
    __table_args__ = (
        Index("idx_sessions_student_id", "student_id"),
        Index("idx_sessions_created_at", "created_at"),
        Index("idx_sessions_engagement_score", "engagement_score"),
        Index("idx_sessions_student_id_created_at", "student_id", "created_at"),
        Index("idx_sessions_student_id_start_time", "student_id", "start_time"),
    )

class BehavioralEvent(Base):
    __tablename__ = "behavioral_events"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    event_metadata: Mapped[Dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False)
    
    # Relationships
    session: Mapped["Session"] = relationship("Session", back_populates="events")
    
    __table_args__ = (
        Index("idx_behavioral_events_session_id", "session_id"),
        Index("idx_behavioral_events_timestamp", "timestamp"),
    )

class ModelPrediction(Base):
    __tablename__ = "model_predictions"
    
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    student_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    prediction: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    student: Mapped["Student"] = relationship("Student", back_populates="predictions")
    
    __table_args__ = (
        Index("idx_model_predictions_student_id", "student_id"),
        Index("idx_model_predictions_model_name", "model_name"),
        Index("idx_model_predictions_created_at", "created_at"),
        Index("idx_model_predictions_student_id_created_at", "student_id", "created_at"),
        Index("idx_model_predictions_model_name_created_at", "model_name", "created_at"),
    )
