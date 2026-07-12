import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.db_models import BehavioralEvent
from app.repositories.base import BaseRepository

class BehaviorRepository(BaseRepository[BehavioralEvent]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, BehavioralEvent)

    async def get_session_events(
        self, session_id: uuid.UUID, *, limit: int = 100, skip: int = 0, event_type: Optional[str] = None
    ) -> List[BehavioralEvent]:
        """Fetch behavioral events for a specific session, optionally filtering by type."""
        query = select(BehavioralEvent).filter(BehavioralEvent.session_id == session_id)
        if event_type:
            query = query.filter(BehavioralEvent.event_type == event_type)
        query = query.order_by(BehavioralEvent.timestamp.asc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
