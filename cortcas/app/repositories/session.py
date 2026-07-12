import uuid
from typing import List, Tuple
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.db_models import Session
from app.repositories.base import BaseRepository

class SessionRepository(BaseRepository[Session]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Session)

    async def get_student_sessions(
        self, student_id: uuid.UUID, *, limit: int = 20, skip: int = 0
    ) -> List[Session]:
        """Fetch sessions for a given student ordered by start time descending."""
        query = (
            select(Session)
            .filter(Session.student_id == student_id)
            .order_by(Session.start_time.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_average_engagement_per_student(self) -> List[Tuple[uuid.UUID, float]]:
        """Calculate the average engagement score for each student."""
        query = (
            select(Session.student_id, func.avg(Session.engagement_score).label("avg_engagement"))
            .group_by(Session.student_id)
        )
        result = await self.db.execute(query)
        # Convert output to list of tuples (student_id, avg_engagement)
        return [(row[0], float(row[1]) if row[1] is not None else 0.0) for row in result.all()]
