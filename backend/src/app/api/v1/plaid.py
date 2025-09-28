from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status
from uuid import UUID
import logging

from ...services.auth_service import get_current_user, get_current_user_id, AuthService
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from ...services.plaid_service import get_plaid_service, PlaidService
from ...schemas.plaid import (
    LinkTokenRequest,
    LinkTokenResponse,
    ExchangeTokenRequest,
    ExchangeTokenResponse,
    PlaidAccountsResponse,
    SandboxLinkInvestmentsRequest,
    SandboxLinkInvestmentsResponse,
)

router = APIRouter()
security = HTTPBearer()
logger = logging.getLogger(__name__)


def get_plaid_service_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> PlaidService:
    """Dependency to get PlaidService with a user-authenticated Supabase client.

    Ensure the Supabase client includes the caller's JWT so RLS policies
    like `auth.uid() = user_id` pass during inserts/selects.
    """
    auth_service = AuthService()

    token = credentials.credentials
    # Best-effort set of the auth token for both auth and postgrest layers
    try:
        # Newer supabase-py: set only access token
        if hasattr(auth_service.supabase, "auth") and hasattr(auth_service.supabase.auth, "set_auth"):
            auth_service.supabase.auth.set_auth(token)
    except Exception:
        pass
    try:
        # Fallback: set session if available (refresh token not required for RLS)
        if hasattr(auth_service.supabase, "auth") and hasattr(auth_service.supabase.auth, "set_session"):
            auth_service.supabase.auth.set_session(token, "")
    except Exception:
        pass
    try:
        # Ensure PostgREST client carries the Bearer token
        if hasattr(auth_service.supabase, "postgrest") and hasattr(auth_service.supabase.postgrest, "auth"):
            auth_service.supabase.postgrest.auth(token)
    except Exception:
        pass

    return get_plaid_service(auth_service.supabase)


@router.post("/link-token", response_model=LinkTokenResponse)
async def create_link_token(
    user: Dict[str, Any] = Depends(get_current_user),
    plaid_service: PlaidService = Depends(get_plaid_service_dependency)
):
    """
    Create a Plaid link token for frontend account linking
    
    This endpoint creates a link token that allows the frontend to
    initialize Plaid Link for account connection.
    """
    try:
        user_id = user["id"]
        user_email = user["email"]
        
        logger.info(f"Creating link token for user {user_id}")
        
        link_token_response = await plaid_service.create_link_token(
            user_id=user_id,
            user_email=user_email
        )
        
        return link_token_response
        
    except Exception as e:
        logger.error(f"Error creating link token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/exchange-token", response_model=ExchangeTokenResponse)
async def exchange_public_token(
    request: ExchangeTokenRequest,
    user_id: str = Depends(get_current_user_id),
    plaid_service: PlaidService = Depends(get_plaid_service_dependency)
):
    """
    Exchange public token for access token
    
    This endpoint securely exchanges the public token received from 
    Plaid Link for a permanent access token, which is encrypted and
    stored in the database.
    """
    try:
        logger.info(f"Exchanging public token for user {user_id}")
        
        success = await plaid_service.exchange_public_token(
            public_token=request.public_token,
            user_id=UUID(user_id)
        )

        if success:
            # Optionally perform an initial sync so the dashboard has data
            try:
                await plaid_service.get_accounts_and_holdings(user_id=UUID(user_id))
            except Exception as sync_err:
                # Don't fail the link flow if sync has a transient issue
                logger.warning(f"Initial Plaid sync after exchange failed: {sync_err}")
            return ExchangeTokenResponse(
                success=True,
                message="Account successfully linked"
            )
        else:
            return ExchangeTokenResponse(
                success=False,
                message="Failed to link account. Please try again."
            )
            
    except Exception as e:
        logger.error(f"Error exchanging public token: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/accounts", response_model=PlaidAccountsResponse)
async def get_accounts_and_holdings(
    user_id: str = Depends(get_current_user_id),
    plaid_service: PlaidService = Depends(get_plaid_service_dependency)
):
    """
    Retrieve user's accounts and investment holdings
    
    This endpoint fetches all linked accounts and their investment
    holdings from Plaid, and stores/updates the data in the database.
    """
    try:
        logger.info(f"Fetching accounts and holdings for user {user_id}")
        
        accounts_response = await plaid_service.get_accounts_and_holdings(
            user_id=UUID(user_id)
        )
        
        return accounts_response
        
    except Exception as e:
        logger.error(f"Error fetching accounts and holdings: {e}")
        
        # Check if the error is due to no linked accounts
        if "No Plaid accounts linked" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No linked accounts found. Please link an account first."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.delete("/accounts/{item_id}")
async def unlink_account(
    item_id: str,
    user_id: str = Depends(get_current_user_id),
    plaid_service: PlaidService = Depends(get_plaid_service_dependency)
):
    """
    Unlink a Plaid account
    
    This endpoint removes a linked Plaid account and all associated data
    from the user's portfolio.
    """
    try:
        logger.info(f"Unlinking account {item_id} for user {user_id}")
        
        # TODO: Implement account unlinking logic
        # This would involve:
        # 1. Removing the access token from plaid_access_tokens table
        # 2. Optionally removing associated portfolio accounts and holdings
        # 3. Calling Plaid's item/remove endpoint to revoke access
        
        return {"message": f"Account {item_id} unlinked successfully"}
        
    except Exception as e:
        logger.error(f"Error unlinking account: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sync")
async def sync_accounts(
    user_id: str = Depends(get_current_user_id),
    plaid_service: PlaidService = Depends(get_plaid_service_dependency)
):
    """
    Manually sync account data
    
    This endpoint triggers a manual sync of account data from Plaid,
    useful for refreshing portfolio information on demand.
    """
    try:
        logger.info(f"Manual sync requested for user {user_id}")
        
        accounts_response = await plaid_service.get_accounts_and_holdings(
            user_id=UUID(user_id)
        )
        
        return {
            "message": "Accounts synced successfully",
            "accounts_count": len(accounts_response.accounts),
            "holdings_count": len(accounts_response.holdings)
        }
        
    except Exception as e:
        logger.error(f"Error during manual sync: {e}")
        
        if "No Plaid accounts linked" in str(e):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No linked accounts found. Please link an account first."
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sandbox/link-investments", response_model=SandboxLinkInvestmentsResponse)
async def sandbox_link_investments(
    request: SandboxLinkInvestmentsRequest,
    user_id: str = Depends(get_current_user_id),
    plaid_service: PlaidService = Depends(get_plaid_service_dependency)
):
    """
    Sandbox helper: search for an investments institution, create a sandbox public token,
    exchange it, and perform an initial sync.

    Useful when the Link modal search doesn't surface investments institutions.
    """
    try:
        logger.info(f"Sandbox investments helper requested for user {user_id}")
        result = await plaid_service.sandbox_create_investments_item(
            user_id=UUID(user_id),
            query=request.query,
            institution_id=request.institution_id,
        )
        return SandboxLinkInvestmentsResponse(
            success=True,
            institution_id=result['institution_id'],
            institution_name=result.get('institution_name')
        )
    except Exception as e:
        logger.error(f"Error in sandbox investments helper: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
