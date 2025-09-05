from typing import List
from uuid import UUID
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from decimal import Decimal

from ...services.portfolio_service import PortfolioService
from ...services.auth_service import get_current_user_id

router = APIRouter()


class HoldingResponse(BaseModel):
    symbol: str
    shares: Decimal
    avg_cost: Decimal
    current_price: float
    total_value: float
    gain_loss: float


class PortfolioAccountResponse(BaseModel):
    id: UUID
    account_name: str
    account_type: str
    total_value: float
    holdings: List[HoldingResponse]


@router.get("/", response_model=List[PortfolioAccountResponse])
async def get_portfolio(user_id: str = Depends(get_current_user_id)):
    portfolio_service = PortfolioService()
    try:
        accounts = await portfolio_service.get_user_portfolio(user_id)
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts", response_model=List[PortfolioAccountResponse])
async def get_accounts(user_id: str = Depends(get_current_user_id)):
    portfolio_service = PortfolioService()
    try:
        accounts = await portfolio_service.get_user_accounts(user_id)
        return accounts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))