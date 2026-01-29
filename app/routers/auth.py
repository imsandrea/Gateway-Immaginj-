"""
Authentication router.
"""
from datetime import timedelta
from fastapi import APIRouter, HTTPException, status

from app.schemas.auth import LoginRequest, TokenResponse
from app.auth.jwt import authenticate_user, create_access_token
from app.config import settings

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate and get JWT token.

    **Credentials:**
    - username: public_api
    - password: [provided separately]

    **Returns:**
    - JWT token valid for 7 days
    """
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create token
    access_token = create_access_token(
        data={"sub": request.username},
        expires_delta=timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.JWT_EXPIRATION_HOURS * 3600  # in seconds
    )
