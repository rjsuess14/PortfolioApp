"""
Pytest configuration and fixtures for testing
"""

import pytest
import os
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from typing import Dict, Any

# Mock Plaid configurations for testing
MOCK_PLAID_CONFIG = {
    'PLAID_CLIENT_ID': 'test_client_id',
    'PLAID_SECRET': 'test_secret',
    'PLAID_ENV': 'sandbox'
}


@pytest.fixture(scope="session", autouse=True)
def mock_env_vars():
    """Mock environment variables for all tests"""
    with patch.dict(os.environ, MOCK_PLAID_CONFIG):
        yield


@pytest.fixture
def mock_plaid_client():
    """Mock Plaid API client for testing"""
    mock_client = Mock()
    
    # Mock successful link token creation
    mock_client.link_token_create.return_value = {
        'link_token': 'link-sandbox-test-token',
        'expiration': '2024-01-01T00:00:00Z'
    }
    
    # Mock successful token exchange
    mock_client.item_public_token_exchange.return_value = {
        'access_token': 'access-sandbox-test-token',
        'item_id': 'test-item-id'
    }
    
    # Mock successful accounts retrieval
    mock_account = Mock()
    mock_account.account_id = 'test-account-id'
    mock_account.name = 'Test Checking Account'
    mock_account.type = 'depository'
    mock_account.subtype = 'checking'
    mock_account.balances = Mock()
    mock_account.balances.available = 1500.50
    mock_account.balances.current = 1750.25
    mock_account.balances.limit = None
    mock_account.balances.iso_currency_code = 'USD'
    
    mock_client.accounts_get.return_value = {
        'accounts': [mock_account],
        'item': Mock()
    }
    
    # Mock successful holdings retrieval
    mock_security = Mock()
    mock_security.security_id = 'test-security-id'
    mock_security.name = 'Apple Inc.'
    mock_security.ticker_symbol = 'AAPL'
    mock_security.cusip = '037833100'
    mock_security.type = 'equity'
    mock_security.close_price = 150.25
    mock_security.close_price_as_of = None
    
    mock_holding = Mock()
    mock_holding.account_id = 'test-investment-account-id'
    mock_holding.security_id = 'test-security-id'
    mock_holding.security = mock_security
    mock_holding.quantity = 10.0
    mock_holding.institution_price = 150.25
    mock_holding.institution_value = 1502.50
    mock_holding.cost_basis = 1400.00
    mock_holding.iso_currency_code = 'USD'
    
    mock_client.investments_holdings_get.return_value = {
        'holdings': [mock_holding],
        'securities': [mock_security],
        'accounts': []
    }
    
    return mock_client


@pytest.fixture
def mock_current_user():
    """Mock authenticated user for testing"""
    user = Mock()
    user.id = "test-user-id"
    user.email = "test@example.com"
    return user


@pytest.fixture
def test_client():
    """Create FastAPI test client"""
    from src.app.main import app
    return TestClient(app)


# Plaid test data fixtures
@pytest.fixture
def plaid_link_token_response():
    """Mock Plaid link token response"""
    return {
        'link_token': 'link-sandbox-test-token',
        'expiration': '2024-01-01T00:00:00Z'
    }


@pytest.fixture
def plaid_public_token():
    """Mock Plaid public token"""
    return 'public-sandbox-test-token'


@pytest.fixture
def plaid_access_token():
    """Mock Plaid access token"""
    return 'access-sandbox-test-token'


@pytest.fixture
def plaid_accounts_response():
    """Mock Plaid accounts response data"""
    return [
        {
            'account_id': 'test-checking-account',
            'name': 'Test Checking Account',
            'type': 'depository',
            'subtype': 'checking',
            'balances': {
                'available': 1500.50,
                'current': 1750.25,
                'limit': None,
                'currency': 'USD'
            }
        },
        {
            'account_id': 'test-investment-account',
            'name': 'Test Investment Account',
            'type': 'investment',
            'subtype': 'ira',
            'balances': {
                'available': None,
                'current': 25000.75,
                'limit': None,
                'currency': 'USD'
            }
        }
    ]


@pytest.fixture
def plaid_holdings_response():
    """Mock Plaid investment holdings response data"""
    return {
        'holdings': [
            {
                'account_id': 'test-investment-account',
                'security_id': 'aapl-security-id',
                'symbol': 'AAPL',
                'name': 'Apple Inc.',
                'quantity': 10.0,
                'institution_price': 150.25,
                'institution_value': 1502.50,
                'cost_basis': 1400.00,
                'currency': 'USD'
            },
            {
                'account_id': 'test-investment-account',
                'security_id': 'tsla-security-id',
                'symbol': 'TSLA',
                'name': 'Tesla Inc.',
                'quantity': 5.0,
                'institution_price': 250.75,
                'institution_value': 1253.75,
                'cost_basis': 1200.00,
                'currency': 'USD'
            }
        ],
        'securities': {
            'aapl-security-id': {
                'security_id': 'aapl-security-id',
                'name': 'Apple Inc.',
                'ticker_symbol': 'AAPL',
                'type': 'equity',
                'close_price': 150.25,
                'close_price_as_of': '2024-01-01T16:00:00Z'
            },
            'tsla-security-id': {
                'security_id': 'tsla-security-id',
                'name': 'Tesla Inc.',
                'ticker_symbol': 'TSLA',
                'type': 'equity',
                'close_price': 250.75,
                'close_price_as_of': '2024-01-01T16:00:00Z'
            }
        }
    }


@pytest.fixture
def plaid_error_response():
    """Mock Plaid error response"""
    from plaid.exceptions import PlaidError
    
    error = PlaidError()
    error.error_message = "TEST_ERROR"
    error.error_code = "INVALID_ACCESS_TOKEN"
    return error


# Sandbox test credentials (safe to include in tests)
@pytest.fixture
def sandbox_credentials():
    """Plaid sandbox test credentials"""
    return {
        'institution_id': 'ins_109508',  # Chase sandbox
        'username': 'user_good',
        'password': 'pass_good',
        'public_token': 'public-sandbox-test-token'
    }