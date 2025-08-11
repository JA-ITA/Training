import requests
import sys
import json
from datetime import datetime
import tempfile
import os

class TrainingAPITester:
    def __init__(self, base_url="https://3458b62d-977b-4bf3-a5b3-a15559b6b88b.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_program_id = None
        self.created_module_id = None
        self.created_unit_id = None
        
        # Authentication tokens for different roles
        self.admin_token = None
        self.instructor_token = None
        self.learner_token = None
        
        # Created resource IDs for testing
        self.created_question_ids = []
        self.created_assessment_id = None
        self.created_user_ids = []

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    if isinstance(response_data, dict) and 'id' in response_data:
                        print(f"   Created ID: {response_data['id']}")
                    return True, response_data
                except:
                    return True, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_health_check(self):
        """Test health endpoint"""
        success, response = self.run_test(
            "Health Check",
            "GET",
            "api/health",
            200
        )
        return success

    def test_create_program(self):
        """Test creating a program"""
        program_data = {
            "title": "Hazardous Materials Transportation Safety",
            "description": "Comprehensive training on safe handling and transportation of hazardous materials",
            "learning_objectives": [
                "Identify hazardous material classifications",
                "Understand DOT regulations",
                "Apply proper packaging procedures"
            ],
            "expiry_duration": 24,
            "renewal_requirements": "Complete refresher course and pass assessment"
        }
        
        success, response = self.run_test(
            "Create Program",
            "POST",
            "api/programs",
            200,
            data=program_data
        )
        
        if success and 'id' in response:
            self.created_program_id = response['id']
            print(f"   Program ID stored: {self.created_program_id}")
        
        return success

    def test_get_programs(self):
        """Test fetching programs list"""
        success, response = self.run_test(
            "Get Programs List",
            "GET",
            "api/programs",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} programs")
        
        return success

    def test_get_program_by_id(self):
        """Test fetching a specific program"""
        if not self.created_program_id:
            print("❌ Skipped - No program ID available")
            return False
            
        success, response = self.run_test(
            "Get Program by ID",
            "GET",
            f"api/programs/{self.created_program_id}",
            200
        )
        return success

    def test_create_module(self):
        """Test creating a module"""
        if not self.created_program_id:
            print("❌ Skipped - No program ID available")
            return False
            
        module_data = {
            "program_id": self.created_program_id,
            "title": "Classification and Identification",
            "description": "Learn to classify and identify different types of hazardous materials",
            "order": 1
        }
        
        success, response = self.run_test(
            "Create Module",
            "POST",
            "api/modules",
            200,
            data=module_data
        )
        
        if success and 'id' in response:
            self.created_module_id = response['id']
            print(f"   Module ID stored: {self.created_module_id}")
        
        return success

    def test_get_program_modules(self):
        """Test fetching modules for a program"""
        if not self.created_program_id:
            print("❌ Skipped - No program ID available")
            return False
            
        success, response = self.run_test(
            "Get Program Modules",
            "GET",
            f"api/programs/{self.created_program_id}/modules",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} modules")
        
        return success

    def test_create_unit(self):
        """Test creating a unit"""
        if not self.created_module_id:
            print("❌ Skipped - No module ID available")
            return False
            
        unit_data = {
            "module_id": self.created_module_id,
            "title": "UN Number System",
            "learning_objectives": [
                "Understand UN numbering system",
                "Read and interpret hazmat labels"
            ],
            "order": 1
        }
        
        success, response = self.run_test(
            "Create Unit",
            "POST",
            "api/units",
            200,
            data=unit_data
        )
        
        if success and 'id' in response:
            self.created_unit_id = response['id']
            print(f"   Unit ID stored: {self.created_unit_id}")
        
        return success

    def test_get_module_units(self):
        """Test fetching units for a module"""
        if not self.created_module_id:
            print("❌ Skipped - No module ID available")
            return False
            
        success, response = self.run_test(
            "Get Module Units",
            "GET",
            f"api/modules/{self.created_module_id}/units",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} units")
        
        return success

    def test_upload_content(self):
        """Test uploading content to a unit"""
        if not self.created_unit_id:
            print("❌ Skipped - No unit ID available")
            return False
            
        # Create a temporary test file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
            temp_file.write("This is a test content file for the UN Number System unit.\n")
            temp_file.write("It contains sample training material about hazardous materials classification.")
            temp_file_path = temp_file.name
        
        try:
            with open(temp_file_path, 'rb') as file:
                files = {'file': ('test_content.txt', file, 'text/plain')}
                success, response = self.run_test(
                    "Upload Content",
                    "POST",
                    f"api/units/{self.created_unit_id}/content/upload",
                    200,
                    files=files
                )
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
        
        return success

    def test_get_unit_content(self):
        """Test fetching content for a unit"""
        if not self.created_unit_id:
            print("❌ Skipped - No unit ID available")
            return False
            
        success, response = self.run_test(
            "Get Unit Content",
            "GET",
            f"api/units/{self.created_unit_id}/content",
            200
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} content items")
        
        return success

    def test_program_structure(self):
        """Test fetching complete program structure"""
        if not self.created_program_id:
            print("❌ Skipped - No program ID available")
            return False
            
        success, response = self.run_test(
            "Get Program Structure",
            "GET",
            f"api/programs/{self.created_program_id}/structure",
            200
        )
        
        if success:
            if 'program' in response and 'modules' in response:
                modules_count = len(response['modules'])
                units_count = sum(len(module.get('units', [])) for module in response['modules'])
                print(f"   Structure: 1 program, {modules_count} modules, {units_count} units")
            else:
                print("   Warning: Unexpected structure format")
        
        return success

def main():
    print("🚀 Starting Training Management API Tests")
    print("=" * 50)
    
    # Setup
    tester = TrainingAPITester()
    
    # Run all tests in sequence
    tests = [
        tester.test_health_check,
        tester.test_create_program,
        tester.test_get_programs,
        tester.test_get_program_by_id,
        tester.test_create_module,
        tester.test_get_program_modules,
        tester.test_create_unit,
        tester.test_get_module_units,
        tester.test_upload_content,
        tester.test_get_unit_content,
        tester.test_program_structure
    ]
    
    for test in tests:
        test()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! API is working correctly.")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())