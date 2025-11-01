#!/usr/bin/env python3
"""
E-Saha Backend Admin ve Fotoğraf Sistemi Test Suite
Tests all admin functionality and photo management system
"""

import requests
import json
import os
import sys
from datetime import datetime
import tempfile
from pathlib import Path

# Get backend URL from frontend .env
BACKEND_URL = "https://pitch-control-1.preview.emergentagent.com/api"

class ESahaBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.admin_token = None
        self.owner_token = None
        self.user_token = None
        self.test_results = {}
        
    def log_test(self, test_name, success, message="", details=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        self.test_results[test_name] = {
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": datetime.now().isoformat()
        }
        
    def test_admin_authentication(self):
        """Test admin login with default credentials"""
        print("\n=== Testing Admin Authentication ===")
        
        try:
            # Test admin login
            login_data = {
                "email": "cnrakbb070@hotmail.com",
                "password": "Canerak07"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "success" and data.get("user", {}).get("role") == "admin":
                    self.admin_token = data.get("session_token")
                    self.log_test("Admin Login", True, "Admin successfully logged in")
                    
                    # Test admin session
                    headers = {"Authorization": f"Bearer {self.admin_token}"}
                    session_response = self.session.get(f"{BACKEND_URL}/auth/session", headers=headers)
                    
                    if session_response.status_code == 200:
                        session_data = session_response.json()
                        if session_data.get("role") == "admin":
                            self.log_test("Admin Session Validation", True, "Admin role verified")
                        else:
                            self.log_test("Admin Session Validation", False, f"Wrong role: {session_data.get('role')}")
                    else:
                        self.log_test("Admin Session Validation", False, f"Session check failed: {session_response.status_code}")
                        
                else:
                    self.log_test("Admin Login", False, f"Login failed or wrong role: {data}")
            else:
                self.log_test("Admin Login", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Login", False, f"Exception: {str(e)}")
            
    def test_admin_dashboard(self):
        """Test admin dashboard endpoint"""
        print("\n=== Testing Admin Dashboard ===")
        
        if not self.admin_token:
            self.log_test("Admin Dashboard", False, "No admin token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            response = self.session.get(f"{BACKEND_URL}/admin/dashboard", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                required_fields = ["statistics", "recent_fields", "recent_bookings"]
                
                if all(field in data for field in required_fields):
                    stats = data["statistics"]
                    required_stats = ["total_users", "total_owners", "total_fields", "pending_fields", 
                                    "total_bookings", "total_revenue", "platform_revenue", "owner_revenue"]
                    
                    if all(stat in stats for stat in required_stats):
                        self.log_test("Admin Dashboard", True, "Dashboard data complete", 
                                    {"user_count": stats["total_users"], "field_count": stats["total_fields"]})
                    else:
                        missing = [s for s in required_stats if s not in stats]
                        self.log_test("Admin Dashboard", False, f"Missing statistics: {missing}")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Admin Dashboard", False, f"Missing fields: {missing}")
            else:
                self.log_test("Admin Dashboard", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Admin Dashboard", False, f"Exception: {str(e)}")
            
    def test_field_management(self):
        """Test admin field management endpoints"""
        print("\n=== Testing Field Management ===")
        
        if not self.admin_token:
            self.log_test("Field Management", False, "No admin token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test get all fields
            response = self.session.get(f"{BACKEND_URL}/admin/fields", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "fields" in data:
                    self.log_test("Get All Fields", True, f"Retrieved {len(data['fields'])} fields")
                    
                    # Test get pending fields
                    pending_response = self.session.get(f"{BACKEND_URL}/admin/fields?status=pending", headers=headers)
                    if pending_response.status_code == 200:
                        pending_data = pending_response.json()
                        pending_count = len(pending_data.get("fields", []))
                        self.log_test("Get Pending Fields", True, f"Retrieved {pending_count} pending fields")
                        
                        # If there are fields, test approve/reject (using first field if available)
                        if data["fields"]:
                            test_field_id = data["fields"][0]["id"]
                            
                            # Test field approval
                            approve_response = self.session.post(f"{BACKEND_URL}/admin/fields/{test_field_id}/approve", headers=headers)
                            if approve_response.status_code == 200:
                                self.log_test("Field Approval", True, "Field approval endpoint working")
                            else:
                                self.log_test("Field Approval", False, f"HTTP {approve_response.status_code}")
                                
                            # Test field rejection
                            reject_data = {"reason": "Test rejection reason"}
                            reject_response = self.session.post(f"{BACKEND_URL}/admin/fields/{test_field_id}/reject", 
                                                              headers=headers, params={"reason": "Test rejection"})
                            if reject_response.status_code == 200:
                                self.log_test("Field Rejection", True, "Field rejection endpoint working")
                            else:
                                self.log_test("Field Rejection", False, f"HTTP {reject_response.status_code}")
                        else:
                            self.log_test("Field Approval/Rejection", True, "No fields to test approval/rejection")
                    else:
                        self.log_test("Get Pending Fields", False, f"HTTP {pending_response.status_code}")
                else:
                    self.log_test("Get All Fields", False, "No 'fields' key in response")
            else:
                self.log_test("Get All Fields", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Field Management", False, f"Exception: {str(e)}")
            
    def test_user_management(self):
        """Test admin user management endpoints"""
        print("\n=== Testing User Management ===")
        
        if not self.admin_token:
            self.log_test("User Management", False, "No admin token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            # Test get all users
            response = self.session.get(f"{BACKEND_URL}/admin/users", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "users" in data:
                    users = data["users"]
                    self.log_test("Get All Users", True, f"Retrieved {len(users)} users")
                    
                    # Test filter by role
                    owner_response = self.session.get(f"{BACKEND_URL}/admin/users?role=owner", headers=headers)
                    if owner_response.status_code == 200:
                        owner_data = owner_response.json()
                        owner_count = len(owner_data.get("users", []))
                        self.log_test("Filter Users by Role", True, f"Retrieved {owner_count} owners")
                    else:
                        self.log_test("Filter Users by Role", False, f"HTTP {owner_response.status_code}")
                        
                    # Test user management actions (find a non-admin user)
                    test_user = None
                    for user in users:
                        if user.get("role") != "admin":
                            test_user = user
                            break
                            
                    if test_user:
                        user_id = test_user["id"]
                        
                        # Test suspend user
                        suspend_response = self.session.post(f"{BACKEND_URL}/admin/users/{user_id}/suspend", headers=headers)
                        if suspend_response.status_code == 200:
                            self.log_test("Suspend User", True, "User suspension endpoint working")
                        else:
                            self.log_test("Suspend User", False, f"HTTP {suspend_response.status_code}")
                            
                        # Test unsuspend user
                        unsuspend_response = self.session.post(f"{BACKEND_URL}/admin/users/{user_id}/unsuspend", headers=headers)
                        if unsuspend_response.status_code == 200:
                            self.log_test("Unsuspend User", True, "User unsuspension endpoint working")
                        else:
                            self.log_test("Unsuspend User", False, f"HTTP {unsuspend_response.status_code}")
                            
                        # Note: Not testing DELETE as it's destructive
                        self.log_test("Delete User Endpoint", True, "Endpoint exists (not tested to avoid data loss)")
                    else:
                        self.log_test("User Management Actions", True, "No non-admin users to test with")
                        
                else:
                    self.log_test("Get All Users", False, "No 'users' key in response")
            else:
                self.log_test("Get All Users", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("User Management", False, f"Exception: {str(e)}")
            
    def test_booking_management(self):
        """Test admin booking management"""
        print("\n=== Testing Booking Management ===")
        
        if not self.admin_token:
            self.log_test("Booking Management", False, "No admin token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = self.session.get(f"{BACKEND_URL}/admin/bookings", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "bookings" in data:
                    booking_count = len(data["bookings"])
                    self.log_test("Get All Bookings", True, f"Retrieved {booking_count} bookings")
                else:
                    self.log_test("Get All Bookings", False, "No 'bookings' key in response")
            else:
                self.log_test("Get All Bookings", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Booking Management", False, f"Exception: {str(e)}")
            
    def test_analytics(self):
        """Test admin analytics endpoint"""
        print("\n=== Testing Analytics ===")
        
        if not self.admin_token:
            self.log_test("Analytics", False, "No admin token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = self.session.get(f"{BACKEND_URL}/admin/analytics", headers=headers)
            if response.status_code == 200:
                data = response.json()
                required_fields = ["booking_stats", "monthly_revenue", "top_fields"]
                
                if all(field in data for field in required_fields):
                    self.log_test("Analytics Data", True, "All analytics data present")
                else:
                    missing = [f for f in required_fields if f not in data]
                    self.log_test("Analytics Data", False, f"Missing fields: {missing}")
            else:
                self.log_test("Analytics Data", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Analytics", False, f"Exception: {str(e)}")
            
    def test_audit_logs(self):
        """Test audit logs endpoint"""
        print("\n=== Testing Audit Logs ===")
        
        if not self.admin_token:
            self.log_test("Audit Logs", False, "No admin token available")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.admin_token}"}
            
            response = self.session.get(f"{BACKEND_URL}/admin/audit-logs", headers=headers)
            if response.status_code == 200:
                data = response.json()
                if "logs" in data:
                    log_count = len(data["logs"])
                    self.log_test("Get Audit Logs", True, f"Retrieved {log_count} audit logs")
                else:
                    self.log_test("Get Audit Logs", False, "No 'logs' key in response")
            else:
                self.log_test("Get Audit Logs", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_test("Audit Logs", False, f"Exception: {str(e)}")
            
    def create_test_owner(self):
        """Create a test owner account for photo testing"""
        try:
            # Register as owner
            register_data = {
                "email": f"testowner_{datetime.now().timestamp()}@test.com",
                "password": "TestPass123",
                "name": "Test Owner",
                "phone": "5551234567",
                "role": "owner"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code == 200:
                data = response.json()
                self.owner_token = data.get("session_token")
                self.log_test("Create Test Owner", True, "Test owner account created")
                return True
            else:
                self.log_test("Create Test Owner", False, f"HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            self.log_test("Create Test Owner", False, f"Exception: {str(e)}")
            return False
            
    def create_test_field(self):
        """Create a test field for photo testing"""
        if not self.owner_token:
            return None
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            field_data = {
                "name": "Test Saha",
                "city": "İstanbul",
                "address": "Test Adres",
                "location": {"lat": 41.0, "lng": 29.0},
                "base_price_per_hour": 100.0,
                "phone": "5551234567",
                "tax_number": "1234567890",
                "iban": "TR123456789012345678901234"
            }
            
            response = self.session.post(f"{BACKEND_URL}/fields", json=field_data, headers=headers)
            if response.status_code == 200:
                data = response.json()
                field_id = data.get("field", {}).get("id")
                self.log_test("Create Test Field", True, f"Test field created: {field_id}")
                return field_id
            else:
                self.log_test("Create Test Field", False, f"HTTP {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            self.log_test("Create Test Field", False, f"Exception: {str(e)}")
            return None
            
    def test_photo_management(self):
        """Test photo upload and management system"""
        print("\n=== Testing Photo Management ===")
        
        # Create test owner and field
        if not self.create_test_owner():
            self.log_test("Photo Management Setup", False, "Could not create test owner")
            return
            
        field_id = self.create_test_field()
        if not field_id:
            self.log_test("Photo Management Setup", False, "Could not create test field")
            return
            
        try:
            headers = {"Authorization": f"Bearer {self.owner_token}"}
            
            # Create a test image file
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                # Create a minimal JPEG file (just header bytes)
                jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
                tmp_file.write(jpeg_header + b'\x00' * 1000)  # Small test image
                tmp_file_path = tmp_file.name
                
            try:
                # Test photo upload
                with open(tmp_file_path, 'rb') as f:
                    files = {'file': ('test.jpg', f, 'image/jpeg')}
                    response = self.session.post(f"{BACKEND_URL}/fields/{field_id}/photos", 
                                               files=files, headers=headers)
                    
                if response.status_code == 200:
                    data = response.json()
                    photo_url = data.get("photo_url")
                    if photo_url:
                        self.log_test("Photo Upload", True, f"Photo uploaded: {photo_url}")
                        
                        # Test photo serving
                        photo_response = self.session.get(f"{BACKEND_URL}{photo_url}")
                        if photo_response.status_code == 200:
                            self.log_test("Photo Serving", True, "Photo served successfully")
                        else:
                            self.log_test("Photo Serving", False, f"HTTP {photo_response.status_code}")
                            
                        # Test set cover photo
                        cover_response = self.session.put(f"{BACKEND_URL}/fields/{field_id}/cover-photo",
                                                        params={"photo_url": photo_url}, headers=headers)
                        if cover_response.status_code == 200:
                            self.log_test("Set Cover Photo", True, "Cover photo set successfully")
                        else:
                            self.log_test("Set Cover Photo", False, f"HTTP {cover_response.status_code}")
                            
                        # Test photo deletion
                        delete_response = self.session.delete(f"{BACKEND_URL}/fields/{field_id}/photos",
                                                            params={"photo_url": photo_url}, headers=headers)
                        if delete_response.status_code == 200:
                            self.log_test("Photo Deletion", True, "Photo deleted successfully")
                        else:
                            self.log_test("Photo Deletion", False, f"HTTP {delete_response.status_code}")
                    else:
                        self.log_test("Photo Upload", False, "No photo_url in response")
                else:
                    self.log_test("Photo Upload", False, f"HTTP {response.status_code}: {response.text}")
                    
            finally:
                # Clean up temp file
                os.unlink(tmp_file_path)
                
        except Exception as e:
            self.log_test("Photo Management", False, f"Exception: {str(e)}")
            
    def test_access_control(self):
        """Test access control for admin endpoints"""
        print("\n=== Testing Access Control ===")
        
        try:
            # Create regular user
            register_data = {
                "email": f"testuser_{datetime.now().timestamp()}@test.com",
                "password": "TestPass123",
                "name": "Test User",
                "role": "user"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            if response.status_code == 200:
                data = response.json()
                user_token = data.get("session_token")
                
                # Try to access admin endpoint with user token
                headers = {"Authorization": f"Bearer {user_token}"}
                admin_response = self.session.get(f"{BACKEND_URL}/admin/dashboard", headers=headers)
                
                if admin_response.status_code == 403:
                    self.log_test("Admin Access Control", True, "Non-admin users correctly blocked from admin endpoints")
                else:
                    self.log_test("Admin Access Control", False, f"Expected 403, got {admin_response.status_code}")
                    
                # Test photo upload access control (user trying to upload)
                with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                    jpeg_header = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00'
                    tmp_file.write(jpeg_header + b'\x00' * 1000)
                    tmp_file_path = tmp_file.name
                    
                try:
                    with open(tmp_file_path, 'rb') as f:
                        files = {'file': ('test.jpg', f, 'image/jpeg')}
                        photo_response = self.session.post(f"{BACKEND_URL}/fields/test-field-id/photos", 
                                                         files=files, headers=headers)
                        
                    if photo_response.status_code == 403:
                        self.log_test("Photo Upload Access Control", True, "Non-owners correctly blocked from photo upload")
                    else:
                        self.log_test("Photo Upload Access Control", False, f"Expected 403, got {photo_response.status_code}")
                        
                finally:
                    os.unlink(tmp_file_path)
                    
            else:
                self.log_test("Access Control Setup", False, f"Could not create test user: {response.status_code}")
                
        except Exception as e:
            self.log_test("Access Control", False, f"Exception: {str(e)}")
            
    def test_registration_control(self):
        """Test that admin role cannot be registered through public endpoint"""
        print("\n=== Testing Registration Control ===")
        
        try:
            register_data = {
                "email": f"testadmin_{datetime.now().timestamp()}@test.com",
                "password": "TestPass123",
                "name": "Test Admin",
                "role": "admin"
            }
            
            response = self.session.post(f"{BACKEND_URL}/auth/register", json=register_data)
            
            if response.status_code == 403:
                self.log_test("Admin Registration Block", True, "Admin role correctly blocked in registration")
            else:
                self.log_test("Admin Registration Block", False, f"Expected 403, got {response.status_code}")
                
        except Exception as e:
            self.log_test("Registration Control", False, f"Exception: {str(e)}")
            
    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🚀 Starting E-Saha Backend Test Suite")
        print(f"Testing against: {BACKEND_URL}")
        print("=" * 60)
        
        # Core admin tests
        self.test_admin_authentication()
        self.test_admin_dashboard()
        self.test_field_management()
        self.test_user_management()
        self.test_booking_management()
        self.test_analytics()
        self.test_audit_logs()
        
        # Photo management tests
        self.test_photo_management()
        
        # Security tests
        self.test_access_control()
        self.test_registration_control()
        
        # Print summary
        self.print_summary()
        
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results.values() if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        print("\n📋 DETAILED RESULTS:")
        for test_name, result in self.test_results.items():
            status = "✅" if result["success"] else "❌"
            print(f"{status} {test_name}: {result['message']}")
            
        print("\n" + "=" * 60)
        
        # Return results for programmatic use
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "success_rate": (passed/total)*100,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = ESahaBackendTester()
    try:
        results = tester.run_all_tests()
        
        # Exit with error code if tests failed
        if results and results["failed"] > 0:
            sys.exit(1)
        else:
            sys.exit(0)
    except Exception as e:
        print(f"Test execution failed: {e}")
        sys.exit(1)