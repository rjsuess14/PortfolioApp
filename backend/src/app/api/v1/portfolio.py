from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from decimal import Decimal

from ...services.portfolio_service import PortfolioService
from ...services.auth_service import get_current_user_id, AuthService

router = APIRouter()
security = HTTPBearer()


class HoldingResponse(BaseModel):
    id: UUID
    symbol: str
    shares: Decimal
    avg_cost: Decimal
    current_price: float
    total_value: float
    gain_loss: float
    account_id: UUID | None = None


class PortfolioAccountResponse(BaseModel):
    id: UUID
    account_name: str
    account_type: str
    total_value: float
    holdings: List[HoldingResponse]


def get_portfolio_service_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> PortfolioService:
    auth_service = AuthService()
    token = credentials.credentials
    # Attach user JWT to supabase client so RLS passes
    try:
        if hasattr(auth_service.supabase, "auth") and hasattr(auth_service.supabase.auth, "set_auth"):
            auth_service.supabase.auth.set_auth(token)
    except Exception:
        pass
    try:
        if hasattr(auth_service.supabase, "auth") and hasattr(auth_service.supabase.auth, "set_session"):
            auth_service.supabase.auth.set_session(token, "")
    except Exception:
        pass
    try:
        if hasattr(auth_service.supabase, "postgrest") and hasattr(auth_service.supabase.postgrest, "auth"):
            auth_service.supabase.postgrest.auth(token)
    except Exception:
        pass
    return PortfolioService(auth_service.supabase)


@router.get("/", response_model=List[PortfolioAccountResponse])
async def get_portfolio(
    user_id: str = Depends(get_current_user_id),
    portfolio_service: PortfolioService = Depends(get_portfolio_service_dependency),
):
    try:
        accounts = await portfolio_service.get_user_portfolio(user_id)
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts", response_model=List[PortfolioAccountResponse])
async def get_accounts(
    user_id: str = Depends(get_current_user_id),
    portfolio_service: PortfolioService = Depends(get_portfolio_service_dependency),
):
    try:
        accounts = await portfolio_service.get_user_accounts(user_id)
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
