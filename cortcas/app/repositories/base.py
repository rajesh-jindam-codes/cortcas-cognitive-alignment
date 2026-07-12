from typing import Generic, TypeVar, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.base import Base

ModelType = TypeVar("ModelType", bound=Base)

class BaseRepository(Generic[ModelType]):
    def __init__(self, db: AsyncSession, model: Type[ModelType]):
        self.db = db
        self.model = model

    async def get(self, id: Any) -> Optional[ModelType]:
        """Fetch a single record by its primary key ID."""
        result = await self.db.execute(select(self.model).filter(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(
        self, *, skip: int = 0, limit: int = 100
    ) -> List[ModelType]:
        """Fetch multiple records with offset and limit."""
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: ModelType) -> ModelType:
        """Add a record to the session."""
        self.db.add(obj_in)
        await self.db.flush()
        return obj_in

    async def update(self, db_obj: ModelType, obj_in: Dict[str, Any] | ModelType) -> ModelType:
        """Update a database record."""
        # Simple implementation
        if isinstance(obj_in, dict):
            for field, value in obj_in.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)
        else:
            for field in self.model.__table__.columns.keys():
                if field != "id" and hasattr(obj_in, field):
                    val = getattr(obj_in, field)
                    if val is not None:
                        setattr(db_obj, field, val)
        self.db.add(db_obj)
        await self.db.flush()
        return db_obj

    async def remove(self, id: Any) -> Optional[ModelType]:
        """Remove a record by its primary key ID."""
        obj = await self.get(id)
        if obj:
            await self.db.delete(obj)
            await self.db.flush()
        return obj
        
    async def add_all(self, items: List[ModelType]) -> List[ModelType]:
        """Batch add records to the database session."""
        self.db.add_all(items)
        await self.db.flush()
        return items
