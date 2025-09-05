#!/usr/bin/env python3
"""
Simple test script to verify authentication API endpoints.
Run this while the backend server is running.
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_health():
    """Test basic server health"""
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Health check failed: {e}")
        return False

def test_auth_endpoints():
    """Test authentication endpoints"""
    if not test_health():
        print("Server not responding, skipping auth tests")
        return
    
    print("\n=== Testing Authentication Endpoints ===")
    
    # Test registration
    print("\n1. Testing Registration:")
    register_data = {
        "email": "test@example.com",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=register_data)
        print(f"Register: {response.status_code}")
        if response.status_code in [200, 400]:  # 400 if user already exists
            print(f"Response: {response.json()}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Registration failed: {e}")
    
    # Test login
    print("\n2. Testing Login:")
    login_data = {
        "email": "test@example.com", 
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data)
        print(f"Login: {response.status_code}")
        if response.status_code == 200:
            login_result = response.json()
            print(f"Login successful!")
            access_token = login_result.get("access_token")
            
            if access_token:
                # Test protected endpoint
                print("\n3. Testing Protected Endpoint:")
                headers = {"Authorization": f"Bearer {access_token}"}
                
                try:
                    response = requests.get(f"{BASE_URL}/auth/me", headers=headers)
                    print(f"Get current user: {response.status_code}")
                    if response.status_code == 200:
                        print(f"User info: {response.json()}")
                    else:
                        print(f"Error: {response.text}")
                except Exception as e:
                    print(f"Protected endpoint test failed: {e}")
                
                # Test logout
                print("\n4. Testing Logout:")
                try:
                    response = requests.post(f"{BASE_URL}/auth/logout", headers=headers)
                    print(f"Logout: {response.status_code}")
                    if response.status_code == 200:
                        print(f"Response: {response.json()}")
                    else:
                        print(f"Error: {response.text}")
                except Exception as e:
                    print(f"Logout test failed: {e}")
            
        else:
            print(f"Login failed: {response.text}")
            
    except Exception as e:
        print(f"Login test failed: {e}")

def test_validation():
    """Test input validation"""
    print("\n=== Testing Input Validation ===")
    
    # Test invalid email
    print("\n1. Testing Invalid Email:")
    invalid_data = {
        "email": "invalid-email",
        "password": "testpassword123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=invalid_data)
        print(f"Invalid email: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Validation test failed: {e}")
    
    # Test short password
    print("\n2. Testing Short Password:")
    short_pass_data = {
        "email": "test2@example.com",
        "password": "123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/auth/register", json=short_pass_data)
        print(f"Short password: {response.status_code}")
        print(f"Response: {response.json()}")
    except Exception as e:
        print(f"Validation test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing Portfolio App Backend API")
    print("=" * 50)
    
    test_auth_endpoints()
    test_validation()
    
    print("\n✅ Testing completed!")
    print("Visit http://localhost:8000/docs for interactive API documentation")