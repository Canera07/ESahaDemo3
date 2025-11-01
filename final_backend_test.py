#!/usr/bin/env python3
"""
Final comprehensive backend test with fixes
"""

import requests
import json
import os
import tempfile
from datetime import datetime

BACKEND_URL = "https://pitch-control-1.preview.emergentagent.com/api"

class FinalBackendTester:
    def __init__(self):
        self.results = {}
        
    def log_result(self, test_name, success, message=""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        self.results[test_name] = {"success": success, "message": message}
        
    def test_admin_system(self):
        """Test complete admin system"""
        print("=== Testing Admin System ===")
        
        # Admin login
        login_data = {"email": "cnrakbb070@hotmail.com", "password": "Canerak07"}
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data)
        
        if response.status_code == 200:
            data = response.json()
            if data.get("user", {}).get("role") == "admin":
                admin_token = data.get("session_token")
                self.log_result("Admin Authentication", True, "Admin login successful")
                
                # Test all admin endpoints
                headers = {"Authorization": f"Bearer {admin_token}"}
                
                # Dashboard
                dashboard = requests.get(f"{BACKEND_URL}/admin/dashboard", headers=headers)
                self.log_result("Admin Dashboard", dashboard.status_code == 200, 
                              f"Status: {dashboard.status_code}")
                
                # Fields management
                fields = requests.get(f"{BACKEND_URL}/admin/fields", headers=headers)
                self.log_result("Admin Fields List", fields.status_code == 200,
                              f"Status: {fields.status_code}")
                
                pending_fields = requests.get(f"{BACKEND_URL}/admin/fields?status=pending", headers=headers)
                self.log_result("Admin Pending Fields", pending_fields.status_code == 200,
                              f"Status: {pending_fields.status_code}")
                
                # Users management
                users = requests.get(f"{BACKEND_URL}/admin/users", headers=headers)
                self.log_result("Admin Users List", users.status_code == 200,
                              f"Status: {users.status_code}")
                
                owners = requests.get(f"{BACKEND_URL}/admin/users?role=owner", headers=headers)
                self.log_result("Admin Filter Users", owners.status_code == 200,
                              f"Status: {owners.status_code}")
                
                # Bookings
                bookings = requests.get(f"{BACKEND_URL}/admin/bookings", headers=headers)
                self.log_result("Admin Bookings", bookings.status_code == 200,
                              f"Status: {bookings.status_code}")
                
                # Analytics
                analytics = requests.get(f"{BACKEND_URL}/admin/analytics", headers=headers)
                self.log_result("Admin Analytics", analytics.status_code == 200,
                              f"Status: {analytics.status_code}")
                
                # Audit logs
                audit = requests.get(f"{BACKEND_URL}/admin/audit-logs", headers=headers)
                self.log_result("Admin Audit Logs", audit.status_code == 200,
                              f"Status: {audit.status_code}")
                
                return admin_token
            else:
                self.log_result("Admin Authentication", False, "Wrong role or login failed")
        else:
            self.log_result("Admin Authentication", False, f"HTTP {response.status_code}")
            
        return None
        
    def test_photo_system(self):
        """Test complete photo system"""
        print("\n=== Testing Photo System ===")
        
        # Create owner
        owner_data = {
            "email": f"photoowner_{datetime.now().timestamp()}@test.com",
            "password": "TestPass123",
            "name": "Photo Owner",
            "phone": "5551234567",
            "role": "owner"
        }
        
        owner_response = requests.post(f"{BACKEND_URL}/auth/register", json=owner_data)
        if owner_response.status_code == 200:
            owner_token = owner_response.json().get("session_token")
            self.log_result("Owner Account Creation", True, "Owner created successfully")
            
            # Create field
            headers = {"Authorization": f"Bearer {owner_token}"}
            field_data = {
                "name": "Photo Test Saha",
                "city": "İstanbul",
                "address": "Photo Test Adres", 
                "location": {"lat": 41.0, "lng": 29.0},
                "base_price_per_hour": 100.0,
                "phone": "5551234567",
                "tax_number": "1234567890",
                "iban": "TR123456789012345678901234"
            }
            
            field_response = requests.post(f"{BACKEND_URL}/fields", json=field_data, headers=headers)
            if field_response.status_code == 200:
                field_id = field_response.json().get("field", {}).get("id")
                self.log_result("Field Creation", True, f"Field created: {field_id}")
                
                # Test photo upload
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
                    tmp_file.write(jpeg_header + b'\x00' * 1000)
                    tmp_file_path = tmp_file.name
                    
                try:
                    with open(tmp_file_path, 'rb') as f:
                        files = {'file': ('test.jpg', f, 'image/jpeg')}
                        upload_response = requests.post(f"{BACKEND_URL}/fields/{field_id}/photos",
                                                      files=files, headers=headers)
                        
                    if upload_response.status_code == 200:
                        photo_data = upload_response.json()
                        photo_url = photo_data.get("photo_url")
                        self.log_result("Photo Upload", True, f"Photo uploaded: {photo_url}")
                        
                        # Test photo serving
                        serve_response = requests.get(f"{BACKEND_URL}{photo_url}")
                        self.log_result("Photo Serving", serve_response.status_code == 200,
                                      f"Status: {serve_response.status_code}")
                        
                        # Test cover photo
                        cover_response = requests.put(f"{BACKEND_URL}/fields/{field_id}/cover-photo",
                                                    params={"photo_url": photo_url}, headers=headers)
                        self.log_result("Set Cover Photo", cover_response.status_code == 200,
                                      f"Status: {cover_response.status_code}")
                        
                        # Test photo deletion
                        delete_response = requests.delete(f"{BACKEND_URL}/fields/{field_id}/photos",
                                                        params={"photo_url": photo_url}, headers=headers)
                        self.log_result("Photo Deletion", delete_response.status_code == 200,
                                      f"Status: {delete_response.status_code}")
                    else:
                        self.log_result("Photo Upload", False, f"HTTP {upload_response.status_code}")
                        
                finally:
                    os.unlink(tmp_file_path)
                    
            else:
                self.log_result("Field Creation", False, f"HTTP {field_response.status_code}")
        else:
            self.log_result("Owner Account Creation", False, f"HTTP {owner_response.status_code}")
            
    def test_access_control(self):
        """Test access control"""
        print("\n=== Testing Access Control ===")
        
        # Create regular user
        user_data = {
            "email": f"accessuser_{datetime.now().timestamp()}@test.com",
            "password": "TestPass123",
            "name": "Access User",
            "role": "user"
        }
        
        user_response = requests.post(f"{BACKEND_URL}/auth/register", json=user_data)
        if user_response.status_code == 200:
            user_token = user_response.json().get("session_token")
            
            # Try admin access
            headers = {"Authorization": f"Bearer {user_token}"}
            admin_response = requests.get(f"{BACKEND_URL}/admin/dashboard", headers=headers)
            
            self.log_result("Admin Access Control", admin_response.status_code == 403,
                          f"Status: {admin_response.status_code}")
            
            # Try photo upload (should fail)
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
                tmp_file.write(jpeg_header + b'\x00' * 1000)
                tmp_file_path = tmp_file.name
                
            try:
                with open(tmp_file_path, 'rb') as f:
                    files = {'file': ('test.jpg', f, 'image/jpeg')}
                    photo_response = requests.post(f"{BACKEND_URL}/fields/fake-id/photos",
                                                 files=files, headers=headers)
                    
                self.log_result("Photo Access Control", photo_response.status_code == 403,
                              f"Status: {photo_response.status_code}")
                
            finally:
                os.unlink(tmp_file_path)
        else:
            self.log_result("Access Control Setup", False, "Could not create test user")
            
    def test_registration_control(self):
        """Test registration control"""
        print("\n=== Testing Registration Control ===")
        
        admin_data = {
            "email": f"fakeadmin_{datetime.now().timestamp()}@test.com",
            "password": "TestPass123",
            "name": "Fake Admin",
            "role": "admin"
        }
        
        response = requests.post(f"{BACKEND_URL}/auth/register", json=admin_data)
        self.log_result("Admin Registration Block", response.status_code == 403,
                      f"Status: {response.status_code}")
        
    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Final E-Saha Backend Test Suite")
        print(f"Testing: {BACKEND_URL}")
        print("=" * 60)
        
        self.test_admin_system()
        self.test_photo_system()
        self.test_access_control()
        self.test_registration_control()
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for r in self.results.values() if r["success"])
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 RESULTS:")
        for test_name, result in self.results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {test_name}: {result['message']}")
            
        return self.results

if __name__ == "__main__":
    tester = FinalBackendTester()
    results = tester.run_all_tests()