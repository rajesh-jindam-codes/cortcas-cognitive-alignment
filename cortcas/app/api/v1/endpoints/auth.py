from datetime import timedelta
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.models.db_models import User
from app.auth.security import verify_password, get_password_hash
from app.auth.auth_utils import create_access_token, create_refresh_token, decode_token
from app.dependencies.deps import get_user_repo, get_current_user
from app.repositories.user import UserRepository
from app.schemas.auth import UserRegister, UserOut, Token

router = APIRouter()

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserRegister,
    user_repo: UserRepository = Depends(get_user_repo)
):
    """Register a new platform user."""
    existing_user = await user_repo.get_by_email(user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system."
        )
    
    hashed_pwd = get_password_hash(user_in.password)
    db_user = User(
        id=uuid.uuid4(),
        email=user_in.email,
        hashed_password=hashed_pwd,
        role=user_in.role,
        is_active=True
    )
    return await user_repo.create(db_user)

@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo: UserRepository = Depends(get_user_repo)
):
    """Authenticate a user and return access/refresh tokens (supports OAuth2 flow)."""
    user = await user_repo.get_by_email(form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token = create_access_token(subject=user.email, role=user.role)
    refresh_token = create_refresh_token(subject=user.email, role=user.role)
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    user_repo: UserRepository = Depends(get_user_repo)
):
    """Generate a new access token using a valid refresh token."""
    try:
        payload = decode_token(refresh_token)
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "refresh":
            raise HTTPException(status_code=401, detail="Invalid refresh token")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
        
    user = await user_repo.get_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
        
    access_token = create_access_token(subject=user.email, role=user.role)
    new_refresh_token = create_refresh_token(subject=user.email, role=user.role)
    
    return {
        "access_token": access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer"
    }

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """Log out current user (client-side deletes JWT, backend returns success)."""
    return {"message": f"Successfully logged out user {current_user.email}"}

@router.get("/me", response_model=UserOut)
async def read_current_user(current_user: User = Depends(get_current_user)):
    """Fetch current user profiles."""
    return current_user
