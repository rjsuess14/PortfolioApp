from decimal import Decimal
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LinkTokenRequest(BaseModel):
    """Request to create a Plaid link token"""
    user_id: str
    
    
class LinkTokenResponse(BaseModel):
    """Response containing Plaid link token"""
    link_token: str
    expiration: datetime
    

class ExchangeTokenRequest(BaseModel):
    """Request to exchange public token for access token"""
    public_token: str
    

class ExchangeTokenResponse(BaseModel):
    """Response after exchanging tokens"""
    success: bool
    message: str
    

class PlaidAccount(BaseModel):
    """Plaid account information"""
    account_id: str
    name: str
    type: str
    subtype: Optional[str] = None
    balance: Decimal
    currency: str = "USD"
    

class PlaidHolding(BaseModel):
    """Plaid investment holding"""
    account_id: str
    security_id: Optional[str] = None
    symbol: Optional[str] = None
    name: str
    quantity: Decimal
    price: Decimal
    value: Decimal
    cost_basis: Optional[Decimal] = None
    

class PlaidSecurity(BaseModel):
    """Plaid security information"""
    security_id: str
    symbol: Optional[str] = None
    name: str
    type: Optional[str] = None
    currency: str = "USD"
    

class PlaidAccountsResponse(BaseModel):
    """Response containing accounts and holdings data"""
    accounts: List[PlaidAccount]
    holdings: List[PlaidHolding]
    securities: List[PlaidSecurity]
    
class SandboxLinkInvestmentsRequest(BaseModel):
    """Request to programmatically link a sandbox investments institution"""
    query: Optional[str] = "invest"
    institution_id: Optional[str] = None

class SandboxLinkInvestmentsResponse(BaseModel):
    """Response after linking sandbox investments institution"""
    success: bool
    institution_id: str
    institution_name: Optional[str] = None
    message: Optional[str] = None
    

class PlaidAccessToken(BaseModel):
    """Encrypted access token storage model"""
    id: Optional[UUID] = None
    user_id: UUID
    item_id: str
    access_token_encrypted: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    

class PlaidError(BaseModel):
    """Plaid error response"""
    error_type: str
    error_code: str
    display_message: Optional[str] = None
    documentation_url: Optional[str] = None
    
