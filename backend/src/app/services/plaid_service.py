import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
from uuid import UUID

from plaid.exceptions import ApiException
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.investments_holdings_get_request import InvestmentsHoldingsGetRequest
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.country_code import CountryCode
from plaid.model.products import Products
from plaid.model.institutions_search_request import InstitutionsSearchRequest
from plaid.model.sandbox_public_token_create_request import SandboxPublicTokenCreateRequest
from supabase import Client

from ..config.plaid import plaid_client
from ..core.encryption import encryption_service
from ..core.config import get_settings
from ..schemas.plaid import (
    LinkTokenResponse,
    PlaidAccount,
    PlaidAccountsResponse,
    PlaidHolding,
    PlaidSecurity,
    PlaidError as PlaidErrorSchema,
)

logger = logging.getLogger(__name__)


class PlaidService:
    """Service for handling Plaid API interactions"""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
        self.client = plaid_client.client
    
    async def create_link_token(self, user_id: str, user_email: str) -> LinkTokenResponse:
        """Create a link token for Plaid Link initialization"""
        try:
            request = LinkTokenCreateRequest(
                products=[Products('investments')],
                client_name="Portfolio App",
                country_codes=[CountryCode('US')],
                language='en',
                user=LinkTokenCreateRequestUser(client_user_id=user_id),
                webhook='https://your-webhook-url.com/plaid/webhook'  # TODO: Update with actual webhook
            )
            
            response = self.client.link_token_create(request)
            
            # Handle response as object or dict
            if hasattr(response, 'link_token'):
                link_token = response.link_token
                expiration = response.expiration
            else:
                link_token = response['link_token']
                expiration = response['expiration']
            
            # Parse expiration date
            if isinstance(expiration, str):
                expiration = datetime.fromisoformat(expiration.replace('Z', '+00:00'))
            
            return LinkTokenResponse(
                link_token=link_token,
                expiration=expiration
            )
            
        except ApiException as e:
            error_body = e.body if hasattr(e, 'body') else str(e)
            logger.error(f"Plaid API error creating link token: {error_body}")
            raise self._convert_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error creating link token: {e}")
            raise Exception("Failed to create link token")
    
    async def exchange_public_token(self, public_token: str, user_id: UUID) -> bool:
        """Exchange public token for access token and store securely"""
        try:
            request = ItemPublicTokenExchangeRequest(public_token=public_token)
            response = self.client.item_public_token_exchange(request)
            
            access_token = response['access_token']
            item_id = response['item_id']
            
            # Encrypt the access token
            encrypted_token = encryption_service.encrypt(access_token)
            
            # Store in database
            result = self.supabase.table('plaid_access_tokens').insert({
                'user_id': str(user_id),
                'item_id': item_id,
                'access_token_encrypted': encrypted_token,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }).execute()
            
            if result.data:
                logger.info(f"Successfully stored access token for user {user_id}")
                return True
            else:
                logger.error(f"Failed to store access token for user {user_id}")
                return False
                
        except ApiException as e:
            logger.error(f"Plaid API error exchanging token: {e}")
            raise self._convert_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error exchanging token: {e}")
            raise Exception("Failed to exchange public token")
    
    async def get_accounts_and_holdings(self, user_id: UUID) -> PlaidAccountsResponse:
        """Retrieve accounts and investment holdings for a user"""
        try:
            # Get user's access tokens
            tokens_result = self.supabase.table('plaid_access_tokens').select('*').eq('user_id', str(user_id)).execute()
            
            if not tokens_result.data:
                raise Exception("No Plaid accounts linked for this user")
            
            logger.info("Plaid sync: found %d access token(s) for user %s", len(tokens_result.data or []), user_id)

            all_accounts = []
            all_holdings = []
            all_securities = []
            
            def _get(obj, key, default=None):
                if isinstance(obj, dict):
                    return obj.get(key, default)
                return getattr(obj, key, default)

            def _enum_to_str(val):
                if val is None:
                    return None
                # Plaid SDK enums have `.value` with the string like 'depository'
                return getattr(val, 'value', str(val))

            for token_record in tokens_result.data:
                # Decrypt access token
                decrypted_token = encryption_service.decrypt(token_record['access_token_encrypted'])
                item_id = token_record.get('item_id') if isinstance(token_record, dict) else None
                logger.info("Plaid sync: fetching accounts for item_id=%s", item_id or "<unknown>")

                # Get accounts
                accounts_request = AccountsGetRequest(access_token=decrypted_token)
                accounts_response = self.client.accounts_get(accounts_request)

                accounts_list = _get(accounts_response, 'accounts') or (accounts_response.get('accounts') if isinstance(accounts_response, dict) else [])
                logger.info("Plaid sync: accounts returned=%d for item_id=%s", len(accounts_list or []), item_id or "<unknown>")

                # Process accounts
                for account in accounts_list:
                    balances = _get(account, 'balances', {})
                    current_balance = _get(balances, 'current')
                    currency_code = _get(balances, 'iso_currency_code', 'USD') or 'USD'

                    all_accounts.append(PlaidAccount(
                        account_id=_get(account, 'account_id'),
                        name=_get(account, 'name'),
                        type=str(_enum_to_str(_get(account, 'type'))),
                        subtype=_enum_to_str(_get(account, 'subtype')),
                        balance=Decimal(str(current_balance or 0)),
                        currency=currency_code
                    ))

                # Get investment holdings if account supports it
                try:
                    holdings_request = InvestmentsHoldingsGetRequest(access_token=decrypted_token)
                    holdings_response = self.client.investments_holdings_get(holdings_request)

                    holdings_list = _get(holdings_response, 'holdings') or (holdings_response.get('holdings') if isinstance(holdings_response, dict) else [])
                    securities_list = _get(holdings_response, 'securities') or (holdings_response.get('securities') if isinstance(holdings_response, dict) else [])
                    logger.info("Plaid sync: holdings returned=%d, securities returned=%d for item_id=%s", len(holdings_list or []), len(securities_list or []), item_id or "<unknown>")

                    # Process holdings
                    for holding in holdings_list:
                        qty = _get(holding, 'quantity')
                        inst_price = _get(holding, 'institution_price')
                        inst_value = _get(holding, 'institution_value')
                        cost_basis = _get(holding, 'cost_basis')

                        all_holdings.append(PlaidHolding(
                            account_id=_get(holding, 'account_id'),
                            security_id=_get(holding, 'security_id'),
                            quantity=Decimal(str(qty or 0)),
                            price=Decimal(str(inst_price or 0)),
                            value=Decimal(str(inst_value or 0)),
                            cost_basis=Decimal(str(cost_basis)) if cost_basis is not None else None,
                            name="Unknown Security",
                            symbol=None
                        ))

                    # Process securities
                    for security in securities_list:
                        all_securities.append(PlaidSecurity(
                            security_id=_get(security, 'security_id'),
                            symbol=_get(security, 'ticker_symbol'),
                            name=_get(security, 'name'),
                            type=_enum_to_str(_get(security, 'type')),
                            currency=_get(security, 'iso_currency_code', 'USD') or 'USD'
                        ))

                    # Update holdings with security info
                    security_map = {s.security_id: s for s in all_securities}
                    for holding in all_holdings:
                        if holding.security_id and holding.security_id in security_map:
                            security = security_map[holding.security_id]
                            holding.name = security.name
                            holding.symbol = security.symbol

                except ApiException as holdings_error:
                    # Some accounts may not support investments endpoint
                    logger.warning(f"Could not fetch holdings for item: {holdings_error}")
                    continue
            
            # Store/update account and holdings data in database
            await self._store_portfolio_data(user_id, all_accounts, all_holdings)
            logger.info("Plaid sync: processed %d account(s) and %d holding(s) for user %s", len(all_accounts), len(all_holdings), user_id)
            
            return PlaidAccountsResponse(
                accounts=all_accounts,
                holdings=all_holdings,
                securities=all_securities
            )
            
        except ApiException as e:
            logger.error(f"Plaid API error getting accounts: {e}")
            raise self._convert_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error getting accounts: {e}")
            raise Exception("Failed to retrieve account data")
    
    async def _store_portfolio_data(self, user_id: UUID, accounts: List[PlaidAccount], holdings: List[PlaidHolding]):
        """Store portfolio data in the database"""
        try:
            inserted_accounts = 0
            updated_accounts = 0
            upserted_holdings = 0
            # Store/update accounts
            for account in accounts:
                # Check if account exists
                existing = self.supabase.table('portfolio_accounts').select('id').eq('user_id', str(user_id)).eq('plaid_account_id', account.account_id).execute()
                
                account_data = {
                    'user_id': str(user_id),
                    'account_name': account.name,
                    'account_type': account.subtype or account.type,
                    'total_value': float(account.balance),
                    'plaid_account_id': account.account_id,
                    'updated_at': datetime.utcnow().isoformat()
                }
                
                if existing.data:
                    # Update existing account
                    upd = self.supabase.table('portfolio_accounts').update(account_data).eq('id', existing.data[0]['id']).execute()
                    if hasattr(upd, 'error') and upd.error:
                        logger.error("Supabase update portfolio_accounts error: %s", upd.error)
                    updated_accounts += 1
                    account_db_id = existing.data[0]['id']
                else:
                    # Insert new account
                    account_data['created_at'] = datetime.utcnow().isoformat()
                    result = self.supabase.table('portfolio_accounts').insert(account_data).execute()
                    if hasattr(result, 'error') and result.error:
                        logger.error("Supabase insert portfolio_accounts error: %s", result.error)
                    # Some Supabase clients may not return inserted rows; re-select if needed
                    if result and getattr(result, 'data', None):
                        account_db_id = result.data[0]['id']
                    else:
                        reselect = self.supabase.table('portfolio_accounts') \
                            .select('id') \
                            .eq('user_id', str(user_id)) \
                            .eq('plaid_account_id', account.account_id) \
                            .limit(1) \
                            .execute()
                        if reselect and reselect.data:
                            account_db_id = reselect.data[0]['id']
                        else:
                            logger.error("Failed to retrieve inserted account id for user %s, plaid_account_id %s", user_id, account.account_id)
                            continue
                    inserted_accounts += 1
                
                # Store holdings for this account
                account_holdings = [h for h in holdings if h.account_id == account.account_id]
                for holding in account_holdings:
                    holding_data = {
                        'account_id': account_db_id,
                        'symbol': holding.symbol or 'UNKNOWN',
                        'shares': float(holding.quantity),
                        'avg_cost': float(holding.cost_basis or 0) / float(holding.quantity) if holding.cost_basis and holding.quantity > 0 else 0,
                        'current_price': float(holding.price),
                        'total_value': float(holding.value),
                        'gain_loss': float(holding.value) - float(holding.cost_basis or 0),
                        'security_name': holding.name,
                        'updated_at': datetime.utcnow().isoformat()
                    }
                    
                    # Check if holding exists
                    existing_holding = self.supabase.table('holdings').select('id').eq('account_id', account_db_id).eq('symbol', holding.symbol or 'UNKNOWN').execute()
                    
                    if existing_holding.data:
                        # Update existing holding
                        upd_h = self.supabase.table('holdings').update(holding_data).eq('id', existing_holding.data[0]['id']).execute()
                        if hasattr(upd_h, 'error') and upd_h.error:
                            logger.error("Supabase update holdings error: %s", upd_h.error)
                        upserted_holdings += 1
                    else:
                        # Insert new holding
                        holding_data['created_at'] = datetime.utcnow().isoformat()
                        ins_h = self.supabase.table('holdings').insert(holding_data).execute()
                        if hasattr(ins_h, 'error') and ins_h.error:
                            logger.error("Supabase insert holdings error: %s", ins_h.error)
                        upserted_holdings += 1
            logger.info("Plaid sync: DB upsert summary for user %s -> inserted_accounts=%d, updated_accounts=%d, upserted_holdings=%d", user_id, inserted_accounts, updated_accounts, upserted_holdings)
        
        except Exception as e:
            logger.error(f"Error storing portfolio data: {e}")
            # Don't raise exception here as the main operation (fetching data) succeeded
    
    def _convert_plaid_error(self, error: ApiException) -> Exception:
        """Convert Plaid API error to our error format"""
        error_data = error.response.json() if hasattr(error, 'response') else {}
        
        plaid_error = PlaidErrorSchema(
            error_type=error_data.get('error_type', 'UNKNOWN'),
            error_code=error_data.get('error_code', 'UNKNOWN'),
            display_message=error_data.get('display_message'),
            documentation_url=error_data.get('documentation_url')
        )
        
        return Exception(f"Plaid API Error: {plaid_error.display_message or plaid_error.error_code}")

    async def sandbox_create_investments_item(self, user_id: UUID, query: Optional[str] = "invest", institution_id: Optional[str] = None) -> dict:
        """Helper to search for a sandbox investments institution, create a public token, and link it.

        Only works in Plaid Sandbox environment.
        """
        settings = get_settings()
        if settings.PLAID_ENV.lower() != 'sandbox':
            raise Exception("This helper is only available in Plaid sandbox environment")

        try:
            selected_institution = None
            inst_id = institution_id

            if not inst_id:
                search_req = InstitutionsSearchRequest(
                    query=query or "invest",
                    products=[Products('investments')],
                    country_codes=[CountryCode('US')]
                )
                search_resp = self.client.institutions_search(search_req)
                institutions = getattr(search_resp, 'institutions', None)
                if institutions is None and isinstance(search_resp, dict):
                    institutions = search_resp.get('institutions')

                if not institutions:
                    raise Exception("No sandbox investments institutions found for given query")

                selected_institution = institutions[0]
                inst_id = getattr(selected_institution, 'institution_id', None)
                if inst_id is None and isinstance(selected_institution, dict):
                    inst_id = selected_institution.get('institution_id')

            # Create sandbox public token
            token_req = SandboxPublicTokenCreateRequest(
                institution_id=inst_id,
                initial_products=[Products('investments')]
            )
            token_resp = self.client.sandbox_public_token_create(token_req)
            public_token = getattr(token_resp, 'public_token', None)
            if public_token is None and isinstance(token_resp, dict):
                public_token = token_resp.get('public_token')

            if not public_token:
                raise Exception("Failed to create sandbox public token")

            # Exchange and sync
            success = await self.exchange_public_token(public_token, user_id)
            if not success:
                raise Exception("Failed to exchange sandbox public token")

            # Perform initial sync to populate portfolio tables
            await self.get_accounts_and_holdings(user_id)

            return {
                'success': True,
                'institution_id': inst_id,
                'institution_name': getattr(selected_institution, 'name', None) if selected_institution else None
            }

        except ApiException as e:
            logger.error(f"Plaid API error creating sandbox investments item: {e}")
            raise self._convert_plaid_error(e)
        except Exception as e:
            logger.error(f"Unexpected error creating sandbox investments item: {e}")
            raise


def get_plaid_service(supabase_client: Client) -> PlaidService:
    """Factory function for PlaidService"""
    return PlaidService(supabase_client)
