"""
Test data fixtures and constants for Plaid integration testing

This file contains safe test data that can be used across different test files.
All data here is either mocked or uses Plaid sandbox credentials.
"""

from typing import Dict, List, Any
from datetime import datetime, timedelta

# Plaid Sandbox Test Credentials
# These are safe to include as they only work with Plaid's sandbox environment
PLAID_SANDBOX_CREDENTIALS = {
    'client_id': '6171e7e7b4614e001313316e',  # Example sandbox client ID
    'secret': 'sandbox_abc123',  # Example sandbox secret
    'env': 'sandbox',
    'products': ['investments', 'accounts'],
    'country_codes': ['US']
}

# Plaid Sandbox Institution IDs (these are public and safe to include)
SANDBOX_INSTITUTIONS = {
    'chase': 'ins_109508',
    'wells_fargo': 'ins_109512',
    'bank_of_america': 'ins_109509',
    'citi': 'ins_109511',
    'td_bank': 'ins_109514'
}

# Plaid Sandbox Test Users (these are documented and safe)
SANDBOX_TEST_USERS = {
    'good_user': {
        'username': 'user_good',
        'password': 'pass_good',
        'description': 'User with successful auth and account creation'
    },
    'bad_user': {
        'username': 'user_bad',
        'password': 'pass_bad',
        'description': 'User with invalid credentials'
    },
    'locked_user': {
        'username': 'user_locked',
        'password': 'pass_locked',
        'description': 'User account is locked'
    }
}

# Mock API Responses
MOCK_LINK_TOKEN_RESPONSE = {
    'link_token': 'link-sandbox-test-token-12345',
    'expiration': '2024-12-31T23:59:59Z'
}

MOCK_TOKEN_EXCHANGE_RESPONSE = {
    'access_token': 'access-sandbox-test-token-67890',
    'item_id': 'test-item-id-abcdef',
    'request_id': 'test-request-id-123'
}

MOCK_ACCOUNTS_RESPONSE = [
    {
        'account_id': 'test-checking-account-123',
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
        'account_id': 'test-savings-account-456',
        'name': 'Test Savings Account',
        'type': 'depository',
        'subtype': 'savings',
        'balances': {
            'available': 5000.00,
            'current': 5000.00,
            'limit': None,
            'currency': 'USD'
        }
    },
    {
        'account_id': 'test-investment-account-789',
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

MOCK_HOLDINGS_RESPONSE = {
    'holdings': [
        {
            'account_id': 'test-investment-account-789',
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
            'account_id': 'test-investment-account-789',
            'security_id': 'tsla-security-id',
            'symbol': 'TSLA',
            'name': 'Tesla Inc.',
            'quantity': 5.0,
            'institution_price': 250.75,
            'institution_value': 1253.75,
            'cost_basis': 1200.00,
            'currency': 'USD'
        },
        {
            'account_id': 'test-investment-account-789',
            'security_id': 'googl-security-id',
            'symbol': 'GOOGL',
            'name': 'Alphabet Inc.',
            'quantity': 3.0,
            'institution_price': 2800.00,
            'institution_value': 8400.00,
            'cost_basis': 8100.00,
            'currency': 'USD'
        }
    ],
    'securities': {
        'aapl-security-id': {
            'security_id': 'aapl-security-id',
            'cusip': '037833100',
            'isin': 'US0378331005',
            'name': 'Apple Inc.',
            'ticker_symbol': 'AAPL',
            'type': 'equity',
            'close_price': 150.25,
            'close_price_as_of': '2024-01-01T16:00:00Z'
        },
        'tsla-security-id': {
            'security_id': 'tsla-security-id',
            'cusip': '88160R101',
            'isin': 'US88160R1014',
            'name': 'Tesla Inc.',
            'ticker_symbol': 'TSLA',
            'type': 'equity',
            'close_price': 250.75,
            'close_price_as_of': '2024-01-01T16:00:00Z'
        },
        'googl-security-id': {
            'security_id': 'googl-security-id',
            'cusip': '02079K305',
            'isin': 'US02079K3059',
            'name': 'Alphabet Inc.',
            'ticker_symbol': 'GOOGL',
            'type': 'equity',
            'close_price': 2800.00,
            'close_price_as_of': '2024-01-01T16:00:00Z'
        }
    }
}

# Test User Data
TEST_USERS = [
    {
        'id': 'test-user-123',
        'email': 'test1@example.com',
        'password': 'TestPassword123!',
        'created_at': datetime.now().isoformat()
    },
    {
        'id': 'test-user-456',
        'email': 'test2@example.com',
        'password': 'TestPassword456!',
        'created_at': datetime.now().isoformat()
    }
]

# Error Responses for Testing
PLAID_ERROR_RESPONSES = {
    'invalid_access_token': {
        'error_type': 'INVALID_INPUT',
        'error_code': 'INVALID_ACCESS_TOKEN',
        'error_message': 'Invalid access token',
        'display_message': 'An error occurred. Please try again.'
    },
    'invalid_public_token': {
        'error_type': 'INVALID_INPUT',
        'error_code': 'INVALID_PUBLIC_TOKEN',
        'error_message': 'Invalid public token',
        'display_message': 'Unable to connect your account. Please try again.'
    },
    'rate_limit_exceeded': {
        'error_type': 'RATE_LIMIT_EXCEEDED',
        'error_code': 'RATE_LIMIT_EXCEEDED',
        'error_message': 'Rate limit exceeded',
        'display_message': 'Too many requests. Please try again later.'
    }
}

# Test Scenarios
TEST_SCENARIOS = {
    'successful_linking': {
        'description': 'Complete successful account linking flow',
        'steps': [
            'create_link_token',
            'complete_plaid_link',
            'exchange_public_token',
            'fetch_accounts',
            'fetch_holdings'
        ],
        'expected_accounts': 3,
        'expected_holdings': 3
    },
    'failed_linking': {
        'description': 'Account linking fails at token exchange',
        'steps': [
            'create_link_token',
            'complete_plaid_link',
            'fail_token_exchange'
        ],
        'error_expected': True
    },
    'partial_data': {
        'description': 'Account links but some data is missing',
        'steps': [
            'create_link_token',
            'complete_plaid_link',
            'exchange_public_token',
            'fetch_accounts_partial'
        ],
        'expected_accounts': 1,
        'expected_holdings': 0
    }
}

# Performance Test Data
PERFORMANCE_TEST_CONFIG = {
    'concurrent_requests': 10,
    'timeout_seconds': 30,
    'max_response_time_ms': 2000,
    'memory_limit_mb': 100
}

# Security Test Patterns
SECURITY_TEST_PATTERNS = {
    'sql_injection': [
        "'; DROP TABLE users; --",
        "' OR '1'='1",
        "'; DELETE FROM accounts WHERE '1'='1'; --"
    ],
    'xss_attempts': [
        "<script>alert('xss')</script>",
        "javascript:alert('xss')",
        "<img src=x onerror=alert('xss')>"
    ],
    'path_traversal': [
        "../../../etc/passwd",
        "..\\..\\windows\\system32\\config\\sam",
        "/etc/shadow"
    ]
}

def get_mock_account_by_type(account_type: str) -> Dict[str, Any]:
    """Get mock account data by type"""
    accounts_by_type = {
        'checking': MOCK_ACCOUNTS_RESPONSE[0],
        'savings': MOCK_ACCOUNTS_RESPONSE[1],
        'investment': MOCK_ACCOUNTS_RESPONSE[2]
    }
    return accounts_by_type.get(account_type, MOCK_ACCOUNTS_RESPONSE[0])

def get_mock_holding_by_symbol(symbol: str) -> Dict[str, Any]:
    """Get mock holding data by stock symbol"""
    for holding in MOCK_HOLDINGS_RESPONSE['holdings']:
        if holding['symbol'] == symbol:
            return holding
    return MOCK_HOLDINGS_RESPONSE['holdings'][0]

def create_test_portfolio_summary() -> Dict[str, Any]:
    """Create a complete test portfolio summary"""
    total_value = sum(account['balances']['current'] for account in MOCK_ACCOUNTS_RESPONSE)
    investment_value = sum(holding['institution_value'] for holding in MOCK_HOLDINGS_RESPONSE['holdings'])
    
    return {
        'total_portfolio_value': total_value + investment_value,
        'cash_balance': total_value,
        'investment_value': investment_value,
        'accounts_count': len(MOCK_ACCOUNTS_RESPONSE),
        'holdings_count': len(MOCK_HOLDINGS_RESPONSE['holdings']),
        'last_updated': datetime.now().isoformat()
    }

def get_test_config_for_environment(env: str) -> Dict[str, str]:
    """Get test configuration based on environment"""
    configs = {
        'sandbox': {
            'PLAID_ENV': 'sandbox',
            'BASE_URL': 'https://sandbox.plaid.com',
            'API_VERSION': '2020-09-14'
        },
        'development': {
            'PLAID_ENV': 'development',
            'BASE_URL': 'https://development.plaid.com',
            'API_VERSION': '2020-09-14'
        }
    }
    return configs.get(env, configs['sandbox'])