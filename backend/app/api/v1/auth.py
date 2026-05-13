from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.orm import Session
from uuid import uuid4

from app.auth.jwt_handler import create_access_token
from app.api.dependencies import get_db_session
from app.models.user import User
import bcrypt as _bcrypt

router = APIRouter(prefix="/auth", tags=["auth"])


class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str = ""


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    name: str
    role: str


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db_session)):
    existing = db.execute(select(User).where(User.email == request.email)).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    user = User(
        email=request.email,
        password_hash=_bcrypt.hashpw(request.password.encode(), _bcrypt.gensalt()).decode(),
        name=request.name or request.email.split("@")[0],
        role="ceo",
    )
    db.add(user)
    db.flush()
    db.refresh(user)

    token = create_access_token({"sub": str(user.id), "roles": [user.role]})
    return AuthResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        name=user.name or "",
        role=user.role,
    )


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db_session)):
    user = db.execute(select(User).where(User.email == request.email)).scalar_one_or_none()
    if not user or not _bcrypt.checkpw(request.password.encode(), user.password_hash.encode()):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    user.last_login_at = __import__("datetime").datetime.utcnow()
    db.flush()

    token = create_access_token({"sub": str(user.id), "roles": [user.role]})
    return AuthResponse(
        access_token=token,
        user_id=str(user.id),
        email=user.email,
        name=user.name or "",
        role=user.role,
    )
