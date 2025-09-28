#!/usr/bin/env python3
"""Test script to verify API endpoints"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Test credentials
TEST_EMAIL = "new@user.com"
TEST_PASSWORD = "testPassword"

def test_register():
    """Test user registration"""
    print("Testing registration...")
    response = requests.post(
        f"{BASE_URL}/auth/register",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    print(f"Register status: {response.status_code}")
    if response.status_code in [200, 201]:
        print("Registration successful")
        return response.json()
    else:
        print(f"Registration response: {response.text}")
        return None

def test_login():
    """Test user login"""
    print("\nTesting login...")
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    print(f"Login status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print("Login successful")
        return data.get("access_token")
    else:
        print(f"Login response: {response.text}")
        return None

def test_portfolio(token):
    """Test portfolio endpoint"""
    print("\nTesting portfolio endpoint...")
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/portfolio/", headers=headers)
    print(f"Portfolio status: {response.status_code}")
    print(f"Portfolio response: {response.text[:200]}")

def test_plaid_link_token(token):
    """Test Plaid link token endpoint"""
    print("\nTesting Plaid link token endpoint...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    response = requests.post(f"{BASE_URL}/plaid/link-token", headers=headers)
    print(f"Plaid link token status: {response.status_code}")
    print(f"Plaid link token response: {response.text[:200]}")
    return response.status_code == 200

if __name__ == "__main__":
    # Try registration (may fail if user exists)
    test_register()
    
    # Login
    token = test_login()
    
    if token:
        print(f"\nAccess token obtained: {token[:50]}...")
        
        # Test authenticated endpoints
        test_portfolio(token)
        test_plaid_link_token(token)
    else:
        print("\nFailed to obtain access token")