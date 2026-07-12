import pytest
import uuid
from datetime import datetime, date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.db_models import Student, Session, ModelPrediction, User, BehavioralEvent
from app.repositories.student import StudentRepository
from app.repositories.session import SessionRepository
from app.repositories.prediction import PredictionRepository
from app.repositories.user import UserRepository

pytestmark = pytest.mark.asyncio

async def test_student_repository(db_session: AsyncSession):
    student_repo = StudentRepository(db_session)
    
    unique_email = f"test_student_{uuid.uuid4().hex[:6]}@example.com"
    student = Student(
        id=uuid.uuid4(),
        email=unique_email,
        name="John Doe",
        age=20,
        gender="Male",
        department="Computer Science",
        year_of_study=2,
        enrollment_date=date.today(),
        created_at=datetime.utcnow()
    )
    
    # Create student
    created_student = await student_repo.create(student)
    assert created_student.email == unique_email
    
    # Get by email
    fetched = await student_repo.get_by_email(unique_email)
    assert fetched is not None
    assert fetched.name == "John Doe"
    
    # List students with filters
    students_list = await student_repo.list_students(department="Computer Science", year_of_study=2)
    assert len(students_list) >= 1
    assert any(s.email == unique_email for s in students_list)

async def test_session_repository(db_session: AsyncSession):
    student_repo = StudentRepository(db_session)
    session_repo = SessionRepository(db_session)
    
    # Create a student first
    unique_email = f"test_sess_student_{uuid.uuid4().hex[:6]}@example.com"
    student = Student(
        id=uuid.uuid4(),
        email=unique_email,
        name="Jane Doe",
        age=21,
        gender="Female",
        department="Mathematics",
        year_of_study=3,
        enrollment_date=date.today(),
        created_at=datetime.utcnow()
    )
    await student_repo.create(student)
    
    # Create a session
    now = datetime.utcnow()
    sess = Session(
        id=uuid.uuid4(),
        student_id=student.id,
        start_time=now,
        end_time=now + timedelta(minutes=30),
        duration_minutes=30,
        engagement_score=0.85,
        focus_score=0.90,
        inactivity_duration=60,
        revision_count=3,
        wrong_answers=1,
        response_time=15.5,
        created_at=now
    )
    
    await session_repo.create(sess)
    
    # Get student sessions
    student_sessions = await session_repo.get_student_sessions(student.id)
    assert len(student_sessions) == 1
    assert student_sessions[0].engagement_score == 0.85
    
    # Check average engagement aggregation
    avgs = await session_repo.get_average_engagement_per_student()
    matching_avg = [avg for student_id, avg in avgs if student_id == student.id]
    assert len(matching_avg) == 1
    assert matching_avg[0] == pytest.approx(0.85)

async def test_prediction_repository(db_session: AsyncSession):
    student_repo = StudentRepository(db_session)
    pred_repo = PredictionRepository(db_session)
    
    # Create a student
    unique_email = f"test_pred_student_{uuid.uuid4().hex[:6]}@example.com"
    student = Student(
        id=uuid.uuid4(),
        email=unique_email,
        name="Bob Smith",
        age=22,
        gender="Male",
        department="Physics",
        year_of_study=4,
        enrollment_date=date.today(),
        created_at=datetime.utcnow()
    )
    await student_repo.create(student)
    
    # Create a prediction
    pred = ModelPrediction(
        id=uuid.uuid4(),
        student_id=student.id,
        model_name="logistic_regression",
        prediction={"at_risk": True},
        confidence=0.89,
        created_at=datetime.utcnow()
    )
    await pred_repo.create(pred)
    
    # Fetch predictions
    preds = await pred_repo.get_student_predictions(student.id)
    assert len(preds) == 1
    assert preds[0].model_name == "logistic_regression"
    assert preds[0].confidence == 0.89
    
    # Fetch latest prediction
    latest = await pred_repo.get_latest_prediction_for_student(student.id, "logistic_regression")
    assert latest is not None
    assert latest.prediction == {"at_risk": True}

async def test_user_repository(db_session: AsyncSession):
    user_repo = UserRepository(db_session)
    
    unique_email = f"user_{uuid.uuid4().hex[:6]}@example.com"
    user = User(
        id=uuid.uuid4(),
        email=unique_email,
        hashed_password="some_hashed_password",
        role="viewer",
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    await user_repo.create(user)
    
    fetched = await user_repo.get_by_email(unique_email)
    assert fetched is not None
    assert fetched.role == "viewer"
