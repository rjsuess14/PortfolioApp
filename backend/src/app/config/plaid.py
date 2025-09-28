from plaid.api import plaid_api
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

from ..core.config import get_settings


class PlaidClient:
    """Plaid API client wrapper with configuration"""
    
    def __init__(self):
        self.settings = get_settings()
        self._client = None
    
    @property
    def client(self) -> plaid_api.PlaidApi:
        """Lazy initialization of Plaid client"""
        if self._client is None:
            configuration = Configuration(
                host=self._get_plaid_host(),
                api_key={
                    'clientId': self.settings.PLAID_CLIENT_ID,
                    'secret': self.settings.PLAID_SECRET,
                }
            )
            api_client = ApiClient(configuration)
            self._client = plaid_api.PlaidApi(api_client)
        return self._client
    
    def _get_plaid_host(self):
        """Get the appropriate Plaid host based on environment"""
        from plaid.configuration import Environment
        env_map = {
            'sandbox': Environment.Sandbox,
            'development': Environment.Sandbox,  # Use Sandbox for development
            'production': Environment.Production
        }
        return env_map.get(self.settings.PLAID_ENV.lower(), Environment.Sandbox)


# Global instance
plaid_client = PlaidClient()