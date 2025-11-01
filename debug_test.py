#!/usr/bin/env python3
"""
Debug specific issues found in testing
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://pitch-control-1.preview.emergentagent.com/api"

def debug_owner_field_creation():
    """Debug why owner can't create field"""
    print("=== Debugging Owner Field Creation ===")
    
    # Login as admin first
    admin_login = {
        "email": "cnrakbb070@hotmail.com",
        "password": "Canerak07"
    }
    
    session = requests.Session()
    admin_response = session.post(f"{BACKEND_URL}/auth/login", json=admin_login)
    admin_token = admin_response.json().get("session_token")
    
    # Create owner account
    owner_data = {
        "email": f"debugowner_{datetime.now().timestamp()}@test.com",
        "password": "TestPass123",
        "name": "Debug Owner",
        "phone": "5551234567",
        "role": "owner"
    }
    
    owner_response = session.post(f"{BACKEND_URL}/auth/register", json=owner_data)
    print(f"Owner registration: {owner_response.status_code} - {owner_response.text}")
    
    if owner_response.status_code == 200:
        owner_token = owner_response.json().get("session_token")
        
        # Check owner session
        headers = {"Authorization": f"Bearer {owner_token}"}
        session_check = session.get(f"{BACKEND_URL}/auth/session", headers=headers)
        print(f"Owner session check: {session_check.status_code} - {session_check.json()}")
        
        # Try to create field
        field_data = {
            "name": "Debug Test Saha",
            "city": "İstanbul",
            "address": "Debug Test Adres",
            "location": {"lat": 41.0, "lng": 29.0},
            "base_price_per_hour": 100.0,
            "phone": "5551234567",
            "tax_number": "1234567890",
            "iban": "TR123456789012345678901234"
        }
        
        field_response = session.post(f"{BACKEND_URL}/fields", json=field_data, headers=headers)
        print(f"Field creation: {field_response.status_code} - {field_response.text}")
        
        if field_response.status_code == 200:
            field_id = field_response.json().get("field", {}).get("id")
            print(f"Field created successfully: {field_id}")
            return field_id, owner_token
        else:
            print("Field creation failed")
            return None, owner_token
    
    return None, None

def debug_access_control():
    """Debug access control issue"""
    print("\n=== Debugging Access Control ===")
    
    # Create regular user
    user_data = {
        "email": f"debuguser_{datetime.now().timestamp()}@test.com",
        "password": "TestPass123",
        "name": "Debug User",
        "role": "user"
    }
    
    session = requests.Session()
    user_response = session.post(f"{BACKEND_URL}/auth/register", json=user_data)
    print(f"User registration: {user_response.status_code} - {user_response.text}")
    
    if user_response.status_code == 200:
        user_token = user_response.json().get("session_token")
        
        # Check user session
        headers = {"Authorization": f"Bearer {user_token}"}
        session_check = session.get(f"{BACKEND_URL}/auth/session", headers=headers)
        print(f"User session check: {session_check.status_code} - {session_check.json()}")
        
        # Try to access admin dashboard
        admin_access = session.get(f"{BACKEND_URL}/admin/dashboard", headers=headers)
        print(f"Admin dashboard access: {admin_access.status_code} - {admin_access.text}")
        
        if admin_access.status_code != 403:
            print("❌ SECURITY ISSUE: Regular user can access admin endpoints!")
        else:
            print("✅ Access control working correctly")

if __name__ == "__main__":
    field_id, owner_token = debug_owner_field_creation()
    debug_access_control()