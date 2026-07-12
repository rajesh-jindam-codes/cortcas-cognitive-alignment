from typing import AsyncGenerator, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.core.config import settings
from app.cache.service import CacheService
from app.ml.factory import ModelFactory
from app.models.db_models import User
from app.auth.auth_utils import decode_token
from app.repositories.student import StudentRepository
from app.repositories.session import SessionRepository
from app.repositories.behavior import BehaviorRepository
from app.repositories.prediction import PredictionRepository
from app.repositories.user import UserRepository

# OAuth2 scheme pointing to login route
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Cache service singleton instance
_cache_instance = CacheService()

def get_cache_service() -> CacheService:
    """Inject the global CacheService singleton."""
    return _cache_instance

def get_model_factory():
    """Inject ModelFactory."""
    return ModelFactory

# Repository Injectors
def get_student_repo(db: AsyncSession = Depends(get_db)) -> StudentRepository:
    return StudentRepository(db)

def get_session_repo(db: AsyncSession = Depends(get_db)) -> SessionRepository:
    return SessionRepository(db)

def get_behavior_repo(db: AsyncSession = Depends(get_db)) -> BehaviorRepository:
    return BehaviorRepository(db)

def get_prediction_repo(db: AsyncSession = Depends(get_db)) -> PredictionRepository:
    return PredictionRepository(db)

def get_user_repo(db: AsyncSession = Depends(get_db)) -> UserRepository:
    return UserRepository(db)

# Authentication Injectors
async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo: UserRepository = Depends(get_user_repo)
) -> User:
    """Decode token, validate claims, and yield current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "access":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    user = await user_repo.get_by_email(email)
    if user is None:
        raise credentials_exception
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return user

def check_permissions(required_role: str) -> Callable:
    """Enforce hierarchical Role-Based Access Control (RBAC)."""
    def dependency(current_user: User = Depends(get_current_user)) -> User:
        # Hierarchical roles: admin can view everything, viewer can only read.
        if required_role == "admin" and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted: Admin privileges required."
            )
        # In a hierarchical setup, any valid user satisfies "viewer" role
        if required_role == "viewer" and current_user.role not in ["admin", "viewer"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted: Insufficient permissions."
            )
        return current_user
    return dependency
