from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.db_models import Student
from app.repositories.base import BaseRepository

class StudentRepository(BaseRepository[Student]):
    def __init__(self, db: AsyncSession):
        super().__init__(db, Student)

    async def get_by_email(self, email: str) -> Optional[Student]:
        """Retrieve a student by their email address."""
        result = await self.db.execute(select(Student).filter(Student.email == email))
        return result.scalar_one_or_none()

    async def list_students(
        self, *, skip: int = 0, limit: int = 100, department: Optional[str] = None, year_of_study: Optional[int] = None
    ) -> List[Student]:
        """List students with optional filters for department and year of study."""
        query = select(Student)
        if department:
            query = query.filter(Student.department == department)
        if year_of_study:
            query = query.filter(Student.year_of_study == year_of_study)
        query = query.offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())
