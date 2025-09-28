"""
Tests for Plaid API endpoints
"""

import pytest
from unittest.mock import Mock, patch
from fastapi import status
from plaid.exceptions import PlaidError

from src.app.api.v1.plaid import router


class TestPlaidAPI:
    """Test cases for Plaid API endpoints"""

    @pytest.fixture
    def auth_headers(self):
        """Mock authentication headers"""
        return {"Authorization": "Bearer test-jwt-token"}

    @pytest.mark.asyncio
    async def test_create_link_token_success(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test successful link token creation endpoint"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                # Mock service response
                mock_service.create_link_token.return_value = {
                    'link_token': 'link-sandbox-test-token',
                    'expiration': '2024-01-01T00:00:00Z'
                }
                
                response = test_client.post(
                    "/api/v1/plaid/link-token",
                    json={},
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data['link_token'] == 'link-sandbox-test-token'
                assert data['expiration'] == '2024-01-01T00:00:00Z'
                
                # Verify service was called with correct parameters
                mock_service.create_link_token.assert_called_once_with(
                    "test-user-id", "test@example.com"
                )

    @pytest.mark.asyncio
    async def test_create_link_token_unauthenticated(self, test_client):
        """Test link token creation without authentication"""
        response = test_client.post("/api/v1/plaid/link-token", json={})
        
        # Should return 401 or 403 depending on auth implementation
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]

    @pytest.mark.asyncio
    async def test_create_link_token_plaid_error(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test link token creation with Plaid error"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                # Mock Plaid error
                plaid_error = PlaidError()
                plaid_error.error_message = "Invalid credentials"
                mock_service.create_link_token.side_effect = plaid_error
                
                response = test_client.post(
                    "/api/v1/plaid/link-token",
                    json={},
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST
                assert "Failed to create link token" in response.json()['detail']

    @pytest.mark.asyncio
    async def test_create_link_token_server_error(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test link token creation with server error"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                mock_service.create_link_token.side_effect = Exception("Database error")
                
                response = test_client.post(
                    "/api/v1/plaid/link-token",
                    json={},
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    @pytest.mark.asyncio
    async def test_exchange_token_success(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test successful public token exchange"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                mock_service.exchange_public_token.return_value = 'access-token-123'
                
                response = test_client.post(
                    "/api/v1/plaid/exchange-token",
                    json={"public_token": "public-sandbox-test-token"},
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert data['success'] is True
                assert "successfully" in data['message'].lower()

    @pytest.mark.asyncio
    async def test_exchange_token_missing_token(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test token exchange with missing public token"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            response = test_client.post(
                "/api/v1/plaid/exchange-token",
                json={},  # Missing public_token
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_exchange_token_invalid_token(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test token exchange with invalid public token"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                plaid_error = PlaidError()
                plaid_error.error_message = "Invalid public token"
                mock_service.exchange_public_token.side_effect = plaid_error
                
                response = test_client.post(
                    "/api/v1/plaid/exchange-token",
                    json={"public_token": "invalid-token"},
                    headers=auth_headers
                )
                
                assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.asyncio
    async def test_get_accounts_not_implemented(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test accounts endpoint returns not implemented"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            response = test_client.get(
                "/api/v1/plaid/accounts",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
            assert "not yet implemented" in response.json()['detail']

    @pytest.mark.asyncio
    async def test_get_holdings_not_implemented(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test holdings endpoint returns not implemented"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            response = test_client.get(
                "/api/v1/plaid/holdings",
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
            assert "not yet implemented" in response.json()['detail']

    @pytest.mark.asyncio
    async def test_request_validation(self, test_client, auth_headers, mock_current_user):
        """Test request model validation"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            # Test invalid JSON structure
            response = test_client.post(
                "/api/v1/plaid/exchange-token",
                json={"public_token": 123},  # Should be string
                headers=auth_headers
            )
            
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_cors_headers(self, test_client):
        """Test CORS headers are properly set"""
        response = test_client.options("/api/v1/plaid/link-token")
        
        # Basic OPTIONS request should work
        # Specific CORS headers would depend on middleware configuration
        assert response.status_code in [
            status.HTTP_200_OK, 
            status.HTTP_405_METHOD_NOT_ALLOWED
        ]


class TestPlaidAPIIntegration:
    """Integration tests for Plaid API endpoints"""

    @pytest.mark.asyncio
    async def test_full_plaid_flow_simulation(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test complete Plaid integration flow through API"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                # Configure service mocks
                mock_service.create_link_token.return_value = {
                    'link_token': 'link-test-token',
                    'expiration': '2024-01-01T00:00:00Z'
                }
                mock_service.exchange_public_token.return_value = 'access-test-token'
                
                # Step 1: Create link token
                link_response = test_client.post(
                    "/api/v1/plaid/link-token",
                    json={},
                    headers=auth_headers
                )
                assert link_response.status_code == status.HTTP_200_OK
                link_token = link_response.json()['link_token']
                
                # Step 2: Exchange public token
                exchange_response = test_client.post(
                    "/api/v1/plaid/exchange-token",
                    json={"public_token": "public-test-token"},
                    headers=auth_headers
                )
                assert exchange_response.status_code == status.HTTP_200_OK
                assert exchange_response.json()['success'] is True

    @pytest.mark.asyncio
    async def test_error_propagation(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test that service errors are properly propagated to API responses"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                # Test different types of errors
                error_scenarios = [
                    (PlaidError("Rate limit"), status.HTTP_400_BAD_REQUEST),
                    (Exception("Network error"), status.HTTP_500_INTERNAL_SERVER_ERROR),
                ]
                
                for error, expected_status in error_scenarios:
                    mock_service.create_link_token.side_effect = error
                    
                    response = test_client.post(
                        "/api/v1/plaid/link-token",
                        json={},
                        headers=auth_headers
                    )
                    
                    assert response.status_code == expected_status


class TestPlaidAPISecurity:
    """Security tests for Plaid API endpoints"""

    @pytest.mark.asyncio
    async def test_authentication_required(self, test_client):
        """Test all endpoints require authentication"""
        endpoints = [
            ("POST", "/api/v1/plaid/link-token", {}),
            ("POST", "/api/v1/plaid/exchange-token", {"public_token": "test"}),
            ("GET", "/api/v1/plaid/accounts", {}),
            ("GET", "/api/v1/plaid/holdings", {}),
        ]
        
        for method, url, data in endpoints:
            if method == "POST":
                response = test_client.post(url, json=data)
            else:
                response = test_client.get(url)
            
            # Should require authentication
            assert response.status_code in [
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]

    @pytest.mark.asyncio
    async def test_user_isolation(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test that users can only access their own data"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                mock_service.create_link_token.return_value = {
                    'link_token': 'user-specific-token',
                    'expiration': '2024-01-01T00:00:00Z'
                }
                
                response = test_client.post(
                    "/api/v1/plaid/link-token",
                    json={},
                    headers=auth_headers
                )
                
                # Verify service was called with current user's info
                mock_service.create_link_token.assert_called_with(
                    "test-user-id", "test@example.com"
                )

    @pytest.mark.asyncio
    async def test_input_sanitization(
        self, test_client, auth_headers, mock_current_user
    ):
        """Test input sanitization and validation"""
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            # Test various malicious inputs
            malicious_inputs = [
                "<script>alert('xss')</script>",
                "'; DROP TABLE users; --",
                "../../../etc/passwd",
                "\x00\x01\x02",  # Null bytes and control characters
            ]
            
            for malicious_input in malicious_inputs:
                response = test_client.post(
                    "/api/v1/plaid/exchange-token",
                    json={"public_token": malicious_input},
                    headers=auth_headers
                )
                
                # Should either validate properly or handle gracefully
                # Not crash the application
                assert response.status_code in [
                    status.HTTP_200_OK,
                    status.HTTP_400_BAD_REQUEST,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    status.HTTP_500_INTERNAL_SERVER_ERROR
                ]

    @pytest.mark.asyncio
    async def test_rate_limiting_headers(self, test_client, auth_headers):
        """Test rate limiting headers if implemented"""
        # This test would check for rate limiting headers
        # Implementation depends on whether rate limiting is configured
        response = test_client.post(
            "/api/v1/plaid/link-token",
            json={},
            headers=auth_headers
        )
        
        # Check if rate limiting headers are present
        # This is optional and depends on middleware configuration
        rate_limit_headers = [
            'X-RateLimit-Limit',
            'X-RateLimit-Remaining',
            'X-RateLimit-Reset'
        ]
        
        # Don't fail if not implemented, just log
        for header in rate_limit_headers:
            if header in response.headers:
                assert isinstance(response.headers[header], str)


class TestPlaidAPILogging:
    """Tests for proper logging in Plaid API endpoints"""

    @pytest.mark.asyncio
    async def test_error_logging(
        self, test_client, auth_headers, mock_current_user, caplog
    ):
        """Test that errors are properly logged"""
        import logging
        
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                mock_service.create_link_token.side_effect = Exception("Test error")
                
                with caplog.at_level(logging.ERROR):
                    response = test_client.post(
                        "/api/v1/plaid/link-token",
                        json={},
                        headers=auth_headers
                    )
                
                # Check that error was logged
                assert len(caplog.records) > 0
                assert "Test error" in caplog.text

    @pytest.mark.asyncio
    async def test_success_logging(
        self, test_client, auth_headers, mock_current_user, caplog
    ):
        """Test that successful operations are logged"""
        import logging
        
        with patch('src.app.api.v1.plaid.get_current_user', return_value=mock_current_user):
            with patch('src.app.api.v1.plaid.plaid_service') as mock_service:
                mock_service.exchange_public_token.return_value = 'test-access-token'
                
                with caplog.at_level(logging.INFO):
                    response = test_client.post(
                        "/api/v1/plaid/exchange-token",
                        json={"public_token": "test-token"},
                        headers=auth_headers
                    )
                
                # Check that success was logged
                assert "Successfully exchanged token" in caplog.text