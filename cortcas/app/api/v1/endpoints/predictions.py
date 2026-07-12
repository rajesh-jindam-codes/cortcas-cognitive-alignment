import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.db_models import ModelPrediction, User
from app.dependencies.deps import (
    get_student_repo, get_session_repo, get_prediction_repo,
    get_cache_service, get_model_factory, check_permissions
)
from app.repositories.student import StudentRepository
from app.repositories.session import SessionRepository
from app.repositories.prediction import PredictionRepository
from app.cache.service import CacheService
from app.schemas.prediction import PredictionOut, SinglePredictionResult, BatchPredictionOut

router = APIRouter()

@router.post("/predict/{student_id}", response_model=SinglePredictionResult, status_code=status.HTTP_201_CREATED)
async def predict_student(
    student_id: uuid.UUID,
    student_repo: StudentRepository = Depends(get_student_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    pred_repo: PredictionRepository = Depends(get_prediction_repo),
    cache_service: CacheService = Depends(get_cache_service),
    model_factory = Depends(get_model_factory),
    current_user: User = Depends(check_permissions("viewer"))
):
    """Trigger ML inference for a single student (Viewer/Admin). Returns and persists predictions."""
    student = await student_repo.get(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found.")
        
    sessions = await session_repo.get_student_sessions(student_id, limit=100)
    if not sessions:
        raise HTTPException(
            status_code=400,
            detail="Student has no session records. Inference requires at least one session."
        )
        
    # 1. Aggregate features for LR & KMeans (Student-level)
    avg_engagement = sum(s.engagement_score for s in sessions) / len(sessions)
    avg_inactivity = sum(s.inactivity_duration for s in sessions) / len(sessions)
    avg_revisions = sum(s.revision_count for s in sessions) / len(sessions)
    avg_wrong = sum(s.wrong_answers for s in sessions) / len(sessions)
    avg_response = sum(s.response_time for s in sessions) / len(sessions)
    avg_duration = sum(s.duration_minutes for s in sessions) / len(sessions)
    avg_focus = sum(s.focus_score for s in sessions) / len(sessions)
    
    student_features = [
        avg_engagement,
        avg_inactivity,
        avg_revisions,
        avg_wrong,
        avg_response,
        avg_duration,
        avg_focus
    ]
    
    # 2. Extract features for Isolation Forest on LATEST session (Session-level)
    latest_sess = sessions[0]
    session_features = [
        latest_sess.duration_minutes,
        latest_sess.engagement_score,
        latest_sess.focus_score,
        latest_sess.inactivity_duration,
        latest_sess.revision_count,
        latest_sess.wrong_answers,
        latest_sess.response_time
    ]
    
    # 3. Load wrappers from factory and predict
    lr_wrapper = model_factory.get_model("logistic_regression")
    km_wrapper = model_factory.get_model("kmeans")
    if_wrapper = model_factory.get_model("isolation_forest")
    
    lr_res = lr_wrapper.predict(student_features)
    km_res = km_wrapper.predict(student_features)
    if_res = if_wrapper.predict(session_features)
    
    # 4. Persist to DB using PredictionRepository
    lr_pred_db = ModelPrediction(
        id=uuid.uuid4(),
        student_id=student_id,
        model_name="logistic_regression",
        prediction=lr_res,
        confidence=lr_res["confidence"]
    )
    km_pred_db = ModelPrediction(
        id=uuid.uuid4(),
        student_id=student_id,
        model_name="kmeans",
        prediction=km_res,
        confidence=1.0
    )
    if_pred_db = ModelPrediction(
        id=uuid.uuid4(),
        student_id=student_id,
        model_name="isolation_forest",
        prediction=if_res,
        confidence=if_res["confidence"]
    )
    
    await pred_repo.create(lr_pred_db)
    await pred_repo.create(km_pred_db)
    await pred_repo.create(if_pred_db)
    
    # Invalidate cache keys for prediction history and dashboard
    cache_service.delete(f"predictions:history:{student_id}")
    cache_service.invalidate_prefix("dashboard:")
    
    return {
        "student_id": student_id,
        "risk_prediction": lr_res,
        "cluster_prediction": km_res,
        "anomaly_prediction": if_res
    }

@router.post("/batch-predict", response_model=BatchPredictionOut)
async def batch_predict(
    student_repo: StudentRepository = Depends(get_student_repo),
    session_repo: SessionRepository = Depends(get_session_repo),
    pred_repo: PredictionRepository = Depends(get_prediction_repo),
    cache_service: CacheService = Depends(get_cache_service),
    model_factory = Depends(get_model_factory),
    current_user: User = Depends(check_permissions("admin"))
):
    """Trigger batch ML inference on all students with session data (Admin only)."""
    students = await student_repo.get_multi(limit=1000)
    
    lr_wrapper = model_factory.get_model("logistic_regression")
    km_wrapper = model_factory.get_model("kmeans")
    if_wrapper = model_factory.get_model("isolation_forest")
    
    predictions_to_insert = []
    processed_count = 0
    
    for student in students:
        sessions = await session_repo.get_student_sessions(student.id, limit=100)
        if not sessions:
            continue
            
        processed_count += 1
        
        # Aggregated student-level features
        avg_engagement = sum(s.engagement_score for s in sessions) / len(sessions)
        avg_inactivity = sum(s.inactivity_duration for s in sessions) / len(sessions)
        avg_revisions = sum(s.revision_count for s in sessions) / len(sessions)
        avg_wrong = sum(s.wrong_answers for s in sessions) / len(sessions)
        avg_response = sum(s.response_time for s in sessions) / len(sessions)
        avg_duration = sum(s.duration_minutes for s in sessions) / len(sessions)
        avg_focus = sum(s.focus_score for s in sessions) / len(sessions)
        
        student_features = [
            avg_engagement, avg_inactivity, avg_revisions, avg_wrong,
            avg_response, avg_duration, avg_focus
        ]
        
        # Latest session level features
        latest_sess = sessions[0]
        session_features = [
            latest_sess.duration_minutes, latest_sess.engagement_score, latest_sess.focus_score,
            latest_sess.inactivity_duration, latest_sess.revision_count, latest_sess.wrong_answers,
            latest_sess.response_time
        ]
        
        lr_res = lr_wrapper.predict(student_features)
        km_res = km_wrapper.predict(student_features)
        if_res = if_wrapper.predict(session_features)
        
        predictions_to_insert.append(ModelPrediction(
            id=uuid.uuid4(), student_id=student.id, model_name="logistic_regression",
            prediction=lr_res, confidence=lr_res["confidence"]
        ))
        predictions_to_insert.append(ModelPrediction(
            id=uuid.uuid4(), student_id=student.id, model_name="kmeans",
            prediction=km_res, confidence=1.0
        ))
        predictions_to_insert.append(ModelPrediction(
            id=uuid.uuid4(), student_id=student.id, model_name="isolation_forest",
            prediction=if_res, confidence=if_res["confidence"]
        ))
        
        # Clean local cache for this student
        cache_service.delete(f"predictions:history:{student.id}")
        
    if predictions_to_insert:
        await pred_repo.add_all(predictions_to_insert)
        
    cache_service.invalidate_prefix("dashboard:")
    
    return {
        "status": "success",
        "predictions_count": len(predictions_to_insert),
        "students_processed": processed_count
    }

@router.get("/history/{student_id}", response_model=List[PredictionOut])
async def prediction_history(
    student_id: uuid.UUID,
    pred_repo: PredictionRepository = Depends(get_prediction_repo),
    cache_service: CacheService = Depends(get_cache_service),
    current_user: User = Depends(check_permissions("viewer"))
):
    """Fetch model prediction history for a student. Heavily cached (Viewer/Admin)."""
    cache_key = f"predictions:history:{student_id}"
    cached_data = cache_service.get(cache_key)
    if cached_data:
        return cached_data
        
    predictions = await pred_repo.get_student_predictions(student_id, limit=50)
    
    # Format database results into JSON-serializable structures for caching
    # Since Pydantic model outputs are validated, we serialize using dicts
    serializable = []
    for p in predictions:
        serializable.append({
            "id": str(p.id),
            "student_id": str(p.student_id),
            "model_name": p.model_name,
            "prediction": p.prediction,
            "confidence": p.confidence,
            "created_at": p.created_at.isoformat()
        })
        
    cache_service.set(cache_key, serializable, ttl=180)
    return predictions
