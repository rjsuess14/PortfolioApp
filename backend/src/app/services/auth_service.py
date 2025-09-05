from typing import Dict, Any, Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from supabase import create_client, Client
from supabase.lib.client_options import ClientOptions
import logging
from ..core.config import get_settings

settings = get_settings()
security = HTTPBearer()
logger = logging.getLogger(__name__)

class AuthException(HTTPException):
    pass

class AuthService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY,
            options=ClientOptions(
                auto_refresh_token=True,
                persist_session=True,
            )
        )
    
    async def login(self, email: str, password: str) -> Dict[str, Any]:
        try:
            response = self.supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if not response.user or not response.session:
                logger.warning(f"Login failed for email: {email}")
                raise AuthException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": response.user.email_confirmed_at,
                    "created_at": response.user.created_at
                }
            }
        except AuthException:
            raise
        except Exception as e:
            logger.error(f"Login error for {email}: {str(e)}")
            raise AuthException(
                status_code=500,
                detail="Authentication service temporarily unavailable"
            )
    
    async def register(self, email: str, password: str) -> Dict[str, Any]:
        try:
            response = self.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if not response.user:
                logger.warning(f"Registration failed for email: {email}")
                raise AuthException(
                    status_code=400,
                    detail="Registration failed. Email may already be in use."
                )
            
            # Handle case where email confirmation is required
            if not response.session:
                return {
                    "message": "Registration successful. Please check your email to confirm your account.",
                    "user": {
                        "id": response.user.id,
                        "email": response.user.email,
                        "email_confirmed_at": response.user.email_confirmed_at
                    }
                }
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": response.user.email_confirmed_at,
                    "created_at": response.user.created_at
                }
            }
        except AuthException:
            raise
        except Exception as e:
            logger.error(f"Registration error for {email}: {str(e)}")
            raise AuthException(
                status_code=500,
                detail="Registration service temporarily unavailable"
            )
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            response = self.supabase.auth.get_user(token)
            
            if not response.user:
                raise AuthException(
                    status_code=401,
                    detail="Invalid or expired token"
                )
            
            return {
                "id": response.user.id,
                "email": response.user.email,
                "email_confirmed_at": response.user.email_confirmed_at,
                "created_at": response.user.created_at
            }
        except AuthException:
            raise
        except Exception as e:
            logger.error(f"Token verification error: {str(e)}")
            raise AuthException(
                status_code=401,
                detail="Invalid or expired token"
            )
    
    async def refresh_token(self, refresh_token: str) -> Dict[str, Any]:
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            if not response.session or not response.user:
                raise AuthException(
                    status_code=401,
                    detail="Invalid refresh token"
                )
            
            return {
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "email_confirmed_at": response.user.email_confirmed_at
                }
            }
        except AuthException:
            raise
        except Exception as e:
            logger.error(f"Token refresh error: {str(e)}")
            raise AuthException(
                status_code=401,
                detail="Token refresh failed"
            )
    
    async def logout(self, token: str) -> Dict[str, str]:
        try:
            self.supabase.auth.sign_out(token)
            return {"message": "Successfully logged out"}
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            # Don't raise exception on logout - always succeed
            return {"message": "Logged out"}


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    auth_service = AuthService()
    user = await auth_service.verify_token(credentials.credentials)
    return user

async def get_current_user_id(user: Dict[str, Any] = Depends(get_current_user)) -> str:
    return user["id"]