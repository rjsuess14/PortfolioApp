"""
Tests for Plaid service functionality
"""

import pytest
from unittest.mock import Mock, patch
from plaid.exceptions import PlaidError

from src.app.services.plaid_service import PlaidService, plaid_service


class TestPlaidService:
    """Test cases for PlaidService class"""

    @pytest.fixture
    def service(self, mock_plaid_client):
        """Create PlaidService instance with mocked client"""
        service = PlaidService()
        service.client = mock_plaid_client
        return service

    @pytest.mark.asyncio
    async def test_create_link_token_success(
        self, service, plaid_link_token_response
    ):
        """Test successful link token creation"""
        user_id = "test-user-123"
        user_email = "test@example.com"
        
        result = await service.create_link_token(user_id, user_email)
        
        assert result['link_token'] == 'link-sandbox-test-token'
        assert result['expiration'] == '2024-01-01T00:00:00Z'
        
        # Verify the client was called with correct parameters
        service.client.link_token_create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_link_token_plaid_error(self, service):
        """Test link token creation with Plaid error"""
        service.client.link_token_create.side_effect = PlaidError("Invalid credentials")
        
        with pytest.raises(PlaidError):
            await service.create_link_token("test-user", "test@example.com")

    @pytest.mark.asyncio
    async def test_create_link_token_unexpected_error(self, service):
        """Test link token creation with unexpected error"""
        service.client.link_token_create.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            await service.create_link_token("test-user", "test@example.com")

    @pytest.mark.asyncio
    async def test_exchange_public_token_success(self, service):
        """Test successful public token exchange"""
        public_token = "public-sandbox-test-token"
        
        result = await service.exchange_public_token(public_token)
        
        assert result == 'access-sandbox-test-token'
        service.client.item_public_token_exchange.assert_called_once()

    @pytest.mark.asyncio
    async def test_exchange_public_token_invalid_token(self, service):
        """Test public token exchange with invalid token"""
        service.client.item_public_token_exchange.side_effect = PlaidError(
            "Invalid public token"
        )
        
        with pytest.raises(PlaidError):
            await service.exchange_public_token("invalid-token")

    @pytest.mark.asyncio
    async def test_get_accounts_success(self, service, plaid_accounts_response):
        """Test successful accounts retrieval"""
        access_token = "access-sandbox-test-token"
        
        result = await service.get_accounts(access_token)
        
        assert len(result) == 1
        account = result[0]
        assert account['account_id'] == 'test-account-id'
        assert account['name'] == 'Test Checking Account'
        assert account['type'] == 'depository'
        assert account['balances']['current'] == 1750.25
        
        service.client.accounts_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_accounts_invalid_token(self, service):
        """Test accounts retrieval with invalid access token"""
        service.client.accounts_get.side_effect = PlaidError(
            "Invalid access token"
        )
        
        with pytest.raises(PlaidError):
            await service.get_accounts("invalid-access-token")

    @pytest.mark.asyncio
    async def test_get_investments_holdings_success(self, service):
        """Test successful investment holdings retrieval"""
        access_token = "access-sandbox-test-token"
        
        result = await service.get_investments_holdings(access_token)
        
        assert 'holdings' in result
        assert 'securities' in result
        
        holdings = result['holdings']
        assert len(holdings) == 1
        
        holding = holdings[0]
        assert holding['symbol'] == 'AAPL'
        assert holding['quantity'] == 10.0
        assert holding['institution_value'] == 1502.50
        
        service.client.investments_holdings_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_investments_holdings_no_holdings(self, service):
        """Test holdings retrieval when account has no holdings"""
        # Mock empty holdings response
        service.client.investments_holdings_get.return_value = {
            'holdings': [],
            'securities': []
        }
        
        result = await service.get_investments_holdings("access-token")
        
        assert result['holdings'] == []
        assert result['securities'] == {}

    @pytest.mark.asyncio
    async def test_get_investments_holdings_error(self, service):
        """Test holdings retrieval with API error"""
        service.client.investments_holdings_get.side_effect = PlaidError(
            "Account not found"
        )
        
        with pytest.raises(PlaidError):
            await service.get_investments_holdings("invalid-token")

    @pytest.mark.asyncio
    async def test_validate_access_token_valid(self, service):
        """Test access token validation with valid token"""
        result = await service.validate_access_token("valid-access-token")
        
        assert result is True
        service.client.accounts_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_access_token_invalid(self, service):
        """Test access token validation with invalid token"""
        service.client.accounts_get.side_effect = PlaidError("Invalid token")
        
        result = await service.validate_access_token("invalid-token")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_validate_access_token_network_error(self, service):
        """Test access token validation with network error"""
        service.client.accounts_get.side_effect = Exception("Network error")
        
        result = await service.validate_access_token("any-token")
        
        assert result is False


class TestPlaidServiceIntegration:
    """Integration tests for Plaid service with real-like scenarios"""

    @pytest.fixture
    def service(self):
        """Use real service instance for integration tests"""
        return plaid_service

    @pytest.mark.asyncio
    async def test_full_flow_simulation(self, service, mock_plaid_client):
        """Test complete Plaid integration flow"""
        # Patch the client to use our mock
        with patch.object(service, 'client', mock_plaid_client):
            # Step 1: Create link token
            link_result = await service.create_link_token(
                "integration-test-user", 
                "integration@example.com"
            )
            assert 'link_token' in link_result
            
            # Step 2: Exchange public token
            access_token = await service.exchange_public_token(
                "public-integration-test-token"
            )
            assert access_token == 'access-sandbox-test-token'
            
            # Step 3: Get accounts
            accounts = await service.get_accounts(access_token)
            assert len(accounts) >= 1
            
            # Step 4: Get holdings
            holdings_data = await service.get_investments_holdings(access_token)
            assert 'holdings' in holdings_data
            assert 'securities' in holdings_data

    @pytest.mark.asyncio
    async def test_error_handling_chain(self, service):
        """Test error handling across multiple service calls"""
        # Create a service with failing client
        failing_client = Mock()
        failing_client.link_token_create.side_effect = PlaidError("Service unavailable")
        
        with patch.object(service, 'client', failing_client):
            # All operations should fail gracefully
            with pytest.raises(PlaidError):
                await service.create_link_token("user", "email@test.com")
            
            with pytest.raises(PlaidError):
                await service.exchange_public_token("any-token")
            
            with pytest.raises(PlaidError):
                await service.get_accounts("any-token")
            
            with pytest.raises(PlaidError):
                await service.get_investments_holdings("any-token")

    @pytest.mark.asyncio
    async def test_data_transformation_accuracy(self, service, mock_plaid_client):
        """Test that data transformation preserves all required fields"""
        with patch.object(service, 'client', mock_plaid_client):
            # Test accounts data transformation
            accounts = await service.get_accounts("test-token")
            account = accounts[0]
            
            required_account_fields = [
                'account_id', 'name', 'type', 'subtype', 'balances'
            ]
            for field in required_account_fields:
                assert field in account
            
            # Test balances structure
            balances = account['balances']
            required_balance_fields = ['available', 'current', 'currency']
            for field in required_balance_fields:
                assert field in balances
            
            # Test holdings data transformation
            holdings_data = await service.get_investments_holdings("test-token")
            if holdings_data['holdings']:
                holding = holdings_data['holdings'][0]
                
                required_holding_fields = [
                    'account_id', 'security_id', 'symbol', 'quantity',
                    'institution_price', 'institution_value', 'currency'
                ]
                for field in required_holding_fields:
                    assert field in holding


class TestPlaidServicePerformance:
    """Performance and load tests for Plaid service"""

    @pytest.mark.asyncio
    async def test_concurrent_link_token_creation(self, mock_plaid_client):
        """Test concurrent link token creation"""
        import asyncio
        
        service = PlaidService()
        service.client = mock_plaid_client
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(10):
            task = service.create_link_token(f"user-{i}", f"user{i}@test.com")
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # All should succeed
        assert len(results) == 10
        for result in results:
            assert 'link_token' in result
            assert result['link_token'] == 'link-sandbox-test-token'

    @pytest.mark.asyncio
    async def test_rate_limiting_simulation(self, mock_plaid_client):
        """Test behavior under simulated rate limiting"""
        service = PlaidService()
        
        # Simulate rate limiting error
        rate_limit_error = PlaidError("Rate limit exceeded")
        mock_plaid_client.link_token_create.side_effect = rate_limit_error
        service.client = mock_plaid_client
        
        with pytest.raises(PlaidError):
            await service.create_link_token("user", "email@test.com")