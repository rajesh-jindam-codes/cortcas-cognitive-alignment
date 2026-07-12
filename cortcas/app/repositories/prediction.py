import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.db_models import ModelPrediction
from app.repositories.base import BaseRepository

class PredictionRepository(BaseRepository[ModelPrediction]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, ModelPrediction)

    async def get_student_predictions(
        self, student_id: uuid.UUID, *, model_name: Optional[str] = None, limit: int = 50, skip: int = 0
    ) -> List[ModelPrediction]:
        """Fetch model predictions for a student, optionally filtered by model_name, sorted by created_at DESC."""
        query = select(ModelPrediction).filter(ModelPrediction.student_id == student_id)
        if model_name:
            query = query.filter(ModelPrediction.model_name == model_name)
        query = query.order_by(ModelPrediction.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_latest_prediction_for_student(
        self, student_id: uuid.UUID, model_name: str
    ) -> Optional[ModelPrediction]:
        """Fetch the latest prediction of a specific model for a student."""
        query = (
            select(ModelPrediction)
            .filter(ModelPrediction.student_id == student_id, ModelPrediction.model_name == model_name)
            .order_by(ModelPrediction.created_at.desc())
            .limit(1)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
