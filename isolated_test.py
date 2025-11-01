#!/usr/bin/env python3
"""
Isolated test to check session management
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://pitch-control-1.preview.emergentagent.com/api"

def test_isolated_owner():
    """Test owner functionality in isolation"""
    print("=== Testing Owner in Isolation ===")
    
    # Create completely new session
    session = requests.Session()
    
    # Create owner account
    owner_data = {
        "email": f"isolatedowner_{datetime.now().timestamp()}@test.com",
        "password": "TestPass123",
        "name": "Isolated Owner",
        "phone": "5551234567",
        "role": "owner"
    }
    
    owner_response = session.post(f"{BACKEND_URL}/auth/register", json=owner_data)
    print(f"Owner registration: {owner_response.status_code}")
    
    if owner_response.status_code == 200:
        data = owner_response.json()
        owner_token = data.get("session_token")
        print(f"Owner token received: {owner_token[:50]}...")
        
        # Use only Authorization header, no cookies
        headers = {"Authorization": f"Bearer {owner_token}"}
        
        # Check session with explicit token
        session_check = requests.get(f"{BACKEND_URL}/auth/session", headers=headers)
        print(f"Session check: {session_check.status_code}")
        if session_check.status_code == 200:
            session_data = session_check.json()
            print(f"Session data: {session_data}")
            
            if session_data.get("role") == "owner":
                print("✅ Owner role confirmed")
                
                # Try to create field
                field_data = {
                    "name": "Isolated Test Saha",
                    "city": "İstanbul", 
                    "address": "Isolated Test Adres",
                    "location": {"lat": 41.0, "lng": 29.0},
                    "base_price_per_hour": 100.0,
                    "phone": "5551234567",
                    "tax_number": "1234567890",
                    "iban": "TR123456789012345678901234"
                }
                
                field_response = requests.post(f"{BACKEND_URL}/fields", json=field_data, headers=headers)
                print(f"Field creation: {field_response.status_code} - {field_response.text}")
                
                if field_response.status_code == 200:
                    field_id = field_response.json().get("field", {}).get("id")
                    print(f"✅ Field created: {field_id}")
                    return field_id, owner_token
                else:
                    print("❌ Field creation failed")
            else:
                print(f"❌ Wrong role in session: {session_data.get('role')}")
        else:
            print(f"❌ Session check failed: {session_check.text}")
    
    return None, None

def test_photo_upload(field_id, owner_token):
    """Test photo upload with valid field"""
    if not field_id or not owner_token:
        print("❌ No field or token for photo test")
        return
        
    print(f"\n=== Testing Photo Upload for Field {field_id} ===")
    
    import tempfile
    import os
    
    # Create test image
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
        jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
        tmp_file.write(jpeg_header + b'\x00' * 1000)
        tmp_file_path = tmp_file.name
        
    try:
        headers = {"Authorization": f"Bearer {owner_token}"}
        
        with open(tmp_file_path, 'rb') as f:
            files = {'file': ('test.jpg', f, 'image/jpeg')}
            response = requests.post(f"{BACKEND_URL}/fields/{field_id}/photos", 
                                   files=files, headers=headers)
            
        print(f"Photo upload: {response.status_code} - {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            photo_url = data.get("photo_url")
            print(f"✅ Photo uploaded: {photo_url}")
            
            # Test photo serving
            photo_response = requests.get(f"{BACKEND_URL}{photo_url}")
            print(f"Photo serving: {photo_response.status_code}")
            
            if photo_response.status_code == 200:
                print("✅ Photo served successfully")
            else:
                print("❌ Photo serving failed")
                
        else:
            print("❌ Photo upload failed")
            
    finally:
        os.unlink(tmp_file_path)

if __name__ == "__main__":
    field_id, owner_token = test_isolated_owner()
    test_photo_upload(field_id, owner_token)