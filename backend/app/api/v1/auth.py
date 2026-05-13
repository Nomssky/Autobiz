from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from uuid import uuid4

from app.auth.jwt_handler import create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str


@router.post("/login", response_model=LoginResponse, summary="Login and get JWT token")
def login(request: LoginRequest):
    """Authenticate user and return a JWT token.

    For now, accepts any credentials and creates a new user ID.
    In production, validate against a user database.
    """
    user_id = str(uuid4())
    token = create_access_token({"sub": user_id, "roles": ["ceo"]})
    return LoginResponse(access_token=token, user_id=user_id)
