from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.auth import Token, LoginRequest, TokenData
from app.auth.utils import verify_password, create_access_token, get_password_hash
from app.schemas.user import UserCreate
from app.utils import create_response, get_logger

router = APIRouter(prefix="/auth", tags=["authentication"])
logger = get_logger(__name__)

@router.post("/login", response_model=Token)
async def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """Login endpoint to get JWT token - accepts JSON body"""
    # Try to find user by username or email
    user = db.query(User).filter(
        (User.username == credentials.username) | (User.email == credentials.username)
    ).first()
    
    if not user:
        logger.warning(f"Login attempt with non-existent user: {credentials.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(credentials.password, user.hashed_password):
        logger.warning(f"Failed password attempt for user: {user.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=60 * 24 * 7)  # 7 days
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "role": user.role.value,
            "sub": user.username
        },
        expires_delta=access_token_expires
    )
    
    logger.info(f"User logged in successfully: {user.username}")
    return Token(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        role=user.role.value
    )

@router.post("/register")
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """Register a new user (initially superadmin only)"""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        role=user_data.role
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    logger.info(f"New user registered: {db_user.username} with role: {db_user.role}")
    
    return create_response(
        success=True,
        message="User registered successfully",
        data={
            "id": db_user.id,
            "email": db_user.email,
            "username": db_user.username,
            "role": db_user.role.value
        }
    )

@router.post("/logout")
async def logout():
    """Logout endpoint (client-side token invalidation)"""
    return create_response(
        success=True,
        message="Logged out successfully"
    )