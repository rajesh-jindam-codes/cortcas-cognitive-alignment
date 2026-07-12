import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.db_models import Student, User
from app.dependencies.deps import get_student_repo, check_permissions
from app.repositories.student import StudentRepository
from app.schemas.student import StudentCreate, StudentUpdate, StudentOut

router = APIRouter()

@router.get("/", response_model=List[StudentOut])
async def list_students(
    skip: int = 0,
    limit: int = 100,
    department: Optional[str] = None,
    year_of_study: Optional[int] = None,
    student_repo: StudentRepository = Depends(get_student_repo),
    current_user: User = Depends(check_permissions("viewer"))
):
    """Retrieve students list with optional pagination and filters (Viewer role required)."""
    return await student_repo.list_students(
        skip=skip, limit=limit, department=department, year_of_study=year_of_study
    )

@router.post("/", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
async def create_student(
    student_in: StudentCreate,
    student_repo: StudentRepository = Depends(get_student_repo),
    current_user: User = Depends(check_permissions("admin"))
):
    """Add a new student profile (Admin role required)."""
    existing = await student_repo.get_by_email(student_in.email)
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Student with email '{student_in.email}' already exists."
        )
    
    student = Student(
        id=uuid.uuid4(),
        **student_in.model_dump()
    )
    return await student_repo.create(student)

@router.get("/{id}", response_model=StudentOut)
async def get_student(
    id: uuid.UUID,
    student_repo: StudentRepository = Depends(get_student_repo),
    current_user: User = Depends(check_permissions("viewer"))
):
    """Retrieve a specific student by ID (Viewer role required)."""
    student = await student_repo.get(id)
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found."
        )
    return student

@router.put("/{id}", response_model=StudentOut)
async def update_student(
    id: uuid.UUID,
    student_in: StudentUpdate,
    student_repo: StudentRepository = Depends(get_student_repo),
    current_user: User = Depends(check_permissions("admin"))
):
    """Modify a student's profile (Admin role required)."""
    student = await student_repo.get(id)
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found."
        )
    
    return await student_repo.update(student, student_in.model_dump(exclude_unset=True))

@router.delete("/{id}", response_model=StudentOut)
async def delete_student(
    id: uuid.UUID,
    student_repo: StudentRepository = Depends(get_student_repo),
    current_user: User = Depends(check_permissions("admin"))
):
    """Remove a student profile (Admin role required)."""
    student = await student_repo.get(id)
    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found."
        )
    
    await student_repo.remove(id)
    return student
