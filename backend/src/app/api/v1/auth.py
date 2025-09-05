from typing import Union, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field

from ...services.auth_service import AuthService, AuthException, get_current_user

router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=128)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: dict


class RegisterResponse(BaseModel):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: dict
    message: Optional[str] = None


class UserResponse(BaseModel):
    user: dict


class MessageResponse(BaseModel):
    message: str


@router.post("/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    auth_service = AuthService()
    try:
        result = await auth_service.login(request.email, request.password)
        return AuthResponse(
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            user=result["user"]
        )
    except AuthException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication service temporarily unavailable"
        )


@router.post("/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    auth_service = AuthService()
    try:
        result = await auth_service.register(request.email, request.password)
        
        # Handle email confirmation case
        if "message" in result:
            return RegisterResponse(
                user=result["user"],
                message=result["message"]
            )
        
        return RegisterResponse(
            access_token=result["access_token"],
            refresh_token=result.get("refresh_token"),
            user=result["user"]
        )
    except AuthException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration service temporarily unavailable"
        )


@router.post("/refresh", response_model=AuthResponse)
async def refresh_token(request: RefreshTokenRequest):
    auth_service = AuthService()
    try:
        result = await auth_service.refresh_token(request.refresh_token)
        return AuthResponse(
            access_token=result["access_token"],
            refresh_token=result["refresh_token"],
            user=result["user"]
        )
    except AuthException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh service temporarily unavailable"
        )


@router.post("/logout", response_model=MessageResponse)
async def logout(credentials: HTTPAuthorizationCredentials = Depends(get_current_user)):
    auth_service = AuthService()
    try:
        result = await auth_service.logout(credentials.credentials)
        return MessageResponse(message=result["message"])
    except Exception:
        # Always succeed on logout
        return MessageResponse(message="Logged out")


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: dict = Depends(get_current_user)):
    return UserResponse(user=user)