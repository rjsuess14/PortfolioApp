from typing import List, Dict, Any
from uuid import UUID
from supabase import create_client, Client
from ..core.config import get_settings

settings = get_settings()

class PortfolioService:
    def __init__(self):
        self.supabase: Client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_ANON_KEY
        )
    
    async def get_user_portfolio(self, user_id: str) -> List[Dict[str, Any]]:
        # Fetch user's portfolio accounts with holdings
        accounts_response = self.supabase.table("portfolio_accounts").select("*").eq("user_id", user_id).execute()
        accounts = accounts_response.data
        
        for account in accounts:
            # Fetch holdings for each account
            holdings_response = self.supabase.table("holdings").select("*").eq("account_id", account["id"]).execute()
            account["holdings"] = holdings_response.data
        
        return accounts
    
    async def get_user_accounts(self, user_id: str) -> List[Dict[str, Any]]:
        # Fetch user's portfolio accounts
        response = self.supabase.table("portfolio_accounts").select("*").eq("user_id", user_id).execute()
        return response.data
    
    async def create_account(self, user_id: str, account_data: Dict[str, Any]) -> Dict[str, Any]:
        # Create a new portfolio account
        account_data["user_id"] = user_id
        response = self.supabase.table("portfolio_accounts").insert(account_data).execute()
        return response.data[0] if response.data else None