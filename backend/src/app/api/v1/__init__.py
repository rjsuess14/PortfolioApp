from fastapi import APIRouter

from .auth import router as auth_router
from .portfolio import router as portfolio_router
from .plaid import router as plaid_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
api_router.include_router(plaid_router, prefix="/plaid", tags=["plaid"])