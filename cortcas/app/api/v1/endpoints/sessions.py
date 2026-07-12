import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status

from app.models.db_models import Session, User
from app.dependencies.deps import get_session_repo, get_cache_service, check_permissions
from app.repositories.session import SessionRepository
from app.cache.service import CacheService
from app.schemas.session import SessionCreate, SessionUpdate, SessionOut

router = APIRouter()

@router.get("/", response_model=List[SessionOut])
async def list_sessions(
    skip: int = 0,
    limit: int = 100,
    student_id: Optional[uuid.UUID] = None,
    session_repo: SessionRepository = Depends(get_session_repo),
    current_user: User = Depends(check_permissions("viewer"))
):
    """Retrieve study sessions list with optional student_id filtering (Viewer role required)."""
    if student_id:
        return await session_repo.get_student_sessions(student_id, limit=limit, skip=skip)
    return await session_repo.get_multi(skip=skip, limit=limit)

@router.post("/", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
async def create_session(
    session_in: SessionCreate,
    session_repo: SessionRepository = Depends(get_session_repo),
    cache_service: CacheService = Depends(get_cache_service),
    current_user: User = Depends(check_permissions("admin"))
):
    """Create a new study session record (Admin role required). Invalidates dashboard caches."""
    db_session = Session(
        id=uuid.uuid4(),
        **session_in.model_dump()
    )
    res = await session_repo.create(db_session)
    
    # Invalidate dashboard caching
    cache_service.invalidate_prefix("dashboard:")
    
    return res

@router.get("/{id}", response_model=SessionOut)
async def get_session(
    id: uuid.UUID,
    session_repo: SessionRepository = Depends(get_session_repo),
    current_user: User = Depends(check_permissions("viewer"))
):
    """Retrieve a specific session record (Viewer role required)."""
    session = await session_repo.get(id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )
    return session

@router.put("/{id}", response_model=SessionOut)
async def update_session(
    id: uuid.UUID,
    session_in: SessionUpdate,
    session_repo: SessionRepository = Depends(get_session_repo),
    cache_service: CacheService = Depends(get_cache_service),
    current_user: User = Depends(check_permissions("admin"))
):
    """Modify a session record (Admin role required). Invalidates dashboard caches."""
    session = await session_repo.get(id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )
    
    res = await session_repo.update(session, session_in.model_dump(exclude_unset=True))
    cache_service.invalidate_prefix("dashboard:")
    return res

@router.delete("/{id}", response_model=SessionOut)
async def delete_session(
    id: uuid.UUID,
    session_repo: SessionRepository = Depends(get_session_repo),
    cache_service: CacheService = Depends(get_cache_service),
    current_user: User = Depends(check_permissions("admin"))
):
    """Remove a session record (Admin role required). Invalidates dashboard caches."""
    session = await session_repo.get(id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found."
        )
    
    await session_repo.remove(id)
    cache_service.invalidate_prefix("dashboard:")
    return session
