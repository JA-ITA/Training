import requests
import sys
import json
from datetime import datetime
import tempfile
import os

class TrainingAPITester:
    def __init__(self, base_url="https://login-fix-34.preview.emergentagent.com"):
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

    def run_test(self, name, method, endpoint, expected_status, data=None, files=None, token=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'} if not files else {}
        
        # Add authorization header if token provided
        if token:
            headers['Authorization'] = f'Bearer {token}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if token:
            print(f"   Using token: {token[:20]}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    # Remove Content-Type for file uploads
                    if 'Content-Type' in headers:
                        del headers['Content-Type']
                    response = requests.post(url, files=files, headers=headers)
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

    # Authentication Tests
    def test_register_admin(self):
        """Test registering an admin user"""
        user_data = {
            "username": "admin",
            "email": "admin@test.com",
            "password": "admin123",
            "full_name": "Test Admin User",
            "role": "admin"
        }
        
        success, response = self.run_test(
            "Register Admin User",
            "POST",
            "api/register",
            200,
            data=user_data
        )
        
        if success and 'id' in response:
            self.created_user_ids.append(response['id'])
            print(f"   Admin user created: {user_data['username']}")
        
        return success

    def test_register_instructor(self):
        """Test registering an instructor user"""
        user_data = {
            "username": "instructor",
            "email": "instructor@test.com",
            "password": "instructor123",
            "full_name": "Test Instructor User",
            "role": "instructor"
        }
        
        success, response = self.run_test(
            "Register Instructor User",
            "POST",
            "api/register",
            200,
            data=user_data
        )
        
        if success and 'id' in response:
            self.created_user_ids.append(response['id'])
            print(f"   Instructor user created: {user_data['username']}")
        
        return success

    def test_register_learner(self):
        """Test registering a learner user"""
        user_data = {
            "username": "learner",
            "email": "learner@test.com",
            "password": "learner123",
            "full_name": "Test Learner User",
            "role": "learner"
        }
        
        success, response = self.run_test(
            "Register Learner User",
            "POST",
            "api/register",
            200,
            data=user_data
        )
        
        if success and 'id' in response:
            self.created_user_ids.append(response['id'])
            print(f"   Learner user created: {user_data['username']}")
        
        return success

    def test_login_admin(self):
        """Test admin login"""
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "api/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.admin_token = response['access_token']
            print(f"   Admin token obtained")
        
        return success

    def test_login_instructor(self):
        """Test instructor login"""
        login_data = {
            "username": "instructor",
            "password": "instructor123"
        }
        
        success, response = self.run_test(
            "Instructor Login",
            "POST",
            "api/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.instructor_token = response['access_token']
            print(f"   Instructor token obtained")
        
        return success

    def test_login_learner(self):
        """Test learner login"""
        login_data = {
            "username": "learner",
            "password": "learner123"
        }
        
        success, response = self.run_test(
            "Learner Login",
            "POST",
            "api/login",
            200,
            data=login_data
        )
        
        if success and 'access_token' in response:
            self.learner_token = response['access_token']
            print(f"   Learner token obtained")
        
        return success

    def test_get_current_user(self):
        """Test getting current user info"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False
            
        success, response = self.run_test(
            "Get Current User Info",
            "GET",
            "api/me",
            200,
            token=self.admin_token
        )
        
        if success and 'role' in response:
            print(f"   User role: {response['role']}")
        
        return success

    # Question Bank Tests
    def test_create_multiple_choice_question(self):
        """Test creating a multiple choice question"""
        if not self.instructor_token:
            print("❌ Skipped - No instructor token available")
            return False
            
        question_data = {
            "question_text": "What is the primary hazard class for gasoline?",
            "question_type": "multiple_choice",
            "options": [
                {"id": "opt1", "text": "Class 1 - Explosives", "is_correct": False},
                {"id": "opt2", "text": "Class 3 - Flammable Liquids", "is_correct": True},
                {"id": "opt3", "text": "Class 5 - Oxidizers", "is_correct": False},
                {"id": "opt4", "text": "Class 8 - Corrosives", "is_correct": False}
            ],
            "points": 2,
            "explanation": "Gasoline is classified as Class 3 - Flammable Liquids according to DOT regulations."
        }
        
        success, response = self.run_test(
            "Create Multiple Choice Question",
            "POST",
            "api/questions",
            200,
            data=question_data,
            token=self.instructor_token
        )
        
        if success and 'id' in response:
            self.created_question_ids.append(response['id'])
            print(f"   Multiple choice question created")
        
        return success

    def test_create_true_false_question(self):
        """Test creating a true/false question"""
        if not self.instructor_token:
            print("❌ Skipped - No instructor token available")
            return False
            
        question_data = {
            "question_text": "All hazardous materials must be labeled with UN numbers.",
            "question_type": "true_false",
            "correct_answer": "true",
            "points": 1,
            "explanation": "Yes, all hazardous materials must display proper UN identification numbers for transportation."
        }
        
        success, response = self.run_test(
            "Create True/False Question",
            "POST",
            "api/questions",
            200,
            data=question_data,
            token=self.instructor_token
        )
        
        if success and 'id' in response:
            self.created_question_ids.append(response['id'])
            print(f"   True/false question created")
        
        return success

    def test_create_essay_question(self):
        """Test creating an essay question"""
        if not self.instructor_token:
            print("❌ Skipped - No instructor token available")
            return False
            
        question_data = {
            "question_text": "Describe the proper procedure for handling a hazardous material spill.",
            "question_type": "essay",
            "points": 5,
            "explanation": "A comprehensive answer should include containment, notification, cleanup, and documentation procedures."
        }
        
        success, response = self.run_test(
            "Create Essay Question",
            "POST",
            "api/questions",
            200,
            data=question_data,
            token=self.instructor_token
        )
        
        if success and 'id' in response:
            self.created_question_ids.append(response['id'])
            print(f"   Essay question created")
        
        return success

    def test_get_questions(self):
        """Test fetching questions (instructor access)"""
        if not self.instructor_token:
            print("❌ Skipped - No instructor token available")
            return False
            
        success, response = self.run_test(
            "Get Questions List",
            "GET",
            "api/questions",
            200,
            token=self.instructor_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} questions")
        
        return success

    def test_learner_cannot_access_questions(self):
        """Test that learners cannot access question management"""
        if not self.learner_token:
            print("❌ Skipped - No learner token available")
            return False
            
        success, response = self.run_test(
            "Learner Access Questions (Should Fail)",
            "GET",
            "api/questions",
            403,  # Expecting forbidden
            token=self.learner_token
        )
        
        return success

    # Assessment Tests
    def test_create_assessment(self):
        """Test creating an assessment"""
        if not self.instructor_token or len(self.created_question_ids) < 2:
            print("❌ Skipped - No instructor token or insufficient questions")
            return False
            
        assessment_data = {
            "title": "Hazmat Basic Safety Quiz",
            "description": "Basic assessment covering hazardous materials safety fundamentals",
            "question_ids": self.created_question_ids[:2],  # Use first 2 questions
            "pass_mark": 70,
            "max_attempts": 3,
            "time_limit": 30,
            "randomize_questions": False
        }
        
        success, response = self.run_test(
            "Create Assessment",
            "POST",
            "api/assessments",
            200,
            data=assessment_data,
            token=self.instructor_token
        )
        
        if success and 'id' in response:
            self.created_assessment_id = response['id']
            print(f"   Assessment created with {len(assessment_data['question_ids'])} questions")
        
        return success

    def test_get_assessments(self):
        """Test fetching assessments list"""
        if not self.learner_token:
            print("❌ Skipped - No learner token available")
            return False
            
        success, response = self.run_test(
            "Get Assessments List",
            "GET",
            "api/assessments",
            200,
            token=self.learner_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} assessments")
        
        return success

    def test_get_assessment_questions(self):
        """Test fetching questions for an assessment (learner view)"""
        if not self.learner_token or not self.created_assessment_id:
            print("❌ Skipped - No learner token or assessment ID")
            return False
            
        success, response = self.run_test(
            "Get Assessment Questions (Learner View)",
            "GET",
            f"api/assessments/{self.created_assessment_id}/questions",
            200,
            token=self.learner_token
        )
        
        if success and isinstance(response, list):
            print(f"   Retrieved {len(response)} questions for assessment")
            # Check that correct answers are hidden for learners
            for question in response:
                if question.get('question_type') == 'multiple_choice':
                    correct_options = [opt for opt in question.get('options', []) if opt.get('is_correct')]
                    if len(correct_options) == 0:
                        print(f"   ✅ Correct answers properly hidden for learners")
                    else:
                        print(f"   ⚠️  Warning: Correct answers may be visible to learners")
        
        return success

    def test_submit_assessment(self):
        """Test submitting an assessment"""
        if not self.learner_token or not self.created_assessment_id or len(self.created_question_ids) < 2:
            print("❌ Skipped - Missing requirements for assessment submission")
            return False
            
        # Create sample answers
        submission_data = {
            "assessment_id": self.created_assessment_id,
            "answers": [
                {
                    "question_id": self.created_question_ids[0],
                    "selected_option_id": "dummy_option_id",  # This would be a real option ID in practice
                    "answer_text": None
                },
                {
                    "question_id": self.created_question_ids[1],
                    "selected_option_id": None,
                    "answer_text": "true"  # For true/false question
                }
            ]
        }
        
        success, response = self.run_test(
            "Submit Assessment",
            "POST",
            f"api/assessments/{self.created_assessment_id}/submit",
            200,
            data=submission_data,
            token=self.learner_token
        )
        
        if success and 'percentage' in response:
            print(f"   Assessment submitted - Score: {response['percentage']:.1f}%")
            print(f"   Passed: {response.get('is_passed', False)}")
        
        return success

    def test_create_program(self):
        """Test creating a program (requires instructor/admin role)"""
        if not self.instructor_token:
            print("❌ Skipped - No instructor token available")
            return False
            
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
            data=program_data,
            token=self.instructor_token
        )
        
        if success and 'id' in response:
            self.created_program_id = response['id']
            print(f"   Program ID stored: {self.created_program_id}")
        
        return success

    def test_get_programs(self):
        """Test fetching programs list (authenticated)"""
        if not self.learner_token:
            print("❌ Skipped - No learner token available")
            return False
            
        success, response = self.run_test(
            "Get Programs List",
            "GET",
            "api/programs",
            200,
            token=self.learner_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} programs")
        
        return success

    def test_get_program_by_id(self):
        """Test fetching a specific program (authenticated)"""
        if not self.created_program_id or not self.learner_token:
            print("❌ Skipped - No program ID or learner token available")
            return False
            
        success, response = self.run_test(
            "Get Program by ID",
            "GET",
            f"api/programs/{self.created_program_id}",
            200,
            token=self.learner_token
        )
        return success

    def test_create_module(self):
        """Test creating a module (requires instructor/admin role)"""
        if not self.created_program_id or not self.instructor_token:
            print("❌ Skipped - No program ID or instructor token available")
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
            data=module_data,
            token=self.instructor_token
        )
        
        if success and 'id' in response:
            self.created_module_id = response['id']
            print(f"   Module ID stored: {self.created_module_id}")
        
        return success

    def test_get_program_modules(self):
        """Test fetching modules for a program (authenticated)"""
        if not self.created_program_id or not self.learner_token:
            print("❌ Skipped - No program ID or learner token available")
            return False
            
        success, response = self.run_test(
            "Get Program Modules",
            "GET",
            f"api/programs/{self.created_program_id}/modules",
            200,
            token=self.learner_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} modules")
        
        return success

    def test_create_unit(self):
        """Test creating a unit (requires instructor/admin role)"""
        if not self.created_module_id or not self.instructor_token:
            print("❌ Skipped - No module ID or instructor token available")
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
            data=unit_data,
            token=self.instructor_token
        )
        
        if success and 'id' in response:
            self.created_unit_id = response['id']
            print(f"   Unit ID stored: {self.created_unit_id}")
        
        return success

    def test_get_module_units(self):
        """Test fetching units for a module (authenticated)"""
        if not self.created_module_id or not self.learner_token:
            print("❌ Skipped - No module ID or learner token available")
            return False
            
        success, response = self.run_test(
            "Get Module Units",
            "GET",
            f"api/modules/{self.created_module_id}/units",
            200,
            token=self.learner_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} units")
        
        return success

    def test_upload_content(self):
        """Test uploading content to a unit (requires instructor/admin role)"""
        if not self.created_unit_id or not self.instructor_token:
            print("❌ Skipped - No unit ID or instructor token available")
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
                    files=files,
                    token=self.instructor_token
                )
        finally:
            # Clean up temp file
            os.unlink(temp_file_path)
        
        return success

    def test_get_unit_content(self):
        """Test fetching content for a unit (authenticated)"""
        if not self.created_unit_id or not self.learner_token:
            print("❌ Skipped - No unit ID or learner token available")
            return False
            
        success, response = self.run_test(
            "Get Unit Content",
            "GET",
            f"api/units/{self.created_unit_id}/content",
            200,
            token=self.learner_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} content items")
        
        return success

    def test_program_structure(self):
        """Test fetching complete program structure (authenticated)"""
        if not self.created_program_id or not self.learner_token:
            print("❌ Skipped - No program ID or learner token available")
            return False
            
        success, response = self.run_test(
            "Get Program Structure",
            "GET",
            f"api/programs/{self.created_program_id}/structure",
            200,
            token=self.learner_token
        )
        
        if success:
            if 'program' in response and 'modules' in response:
                modules_count = len(response['modules'])
                units_count = sum(len(module.get('units', [])) for module in response['modules'])
                print(f"   Structure: 1 program, {modules_count} modules, {units_count} units")
            else:
                print("   Warning: Unexpected structure format")
        
        return success

        
        return success

    # Enrollment Tests
    def test_create_enrollment(self):
        """Test creating an enrollment (admin only)"""
        if not self.admin_token or not self.created_program_id or len(self.created_user_ids) < 3:
            print("❌ Skipped - Missing admin token, program ID, or user IDs")
            return False
            
        # Enroll the learner in the program
        learner_id = self.created_user_ids[2]  # Learner is the 3rd user created
        enrollment_data = {
            "user_id": learner_id,
            "program_id": self.created_program_id
        }
        
        success, response = self.run_test(
            "Create Enrollment",
            "POST",
            "api/enrollments",
            200,
            data=enrollment_data,
            token=self.admin_token
        )
        
        if success and 'id' in response:
            print(f"   Learner enrolled in program")
        
        return success

    def test_get_enrollments(self):
        """Test fetching all enrollments (admin only)"""
        if not self.admin_token:
            print("❌ Skipped - No admin token available")
            return False
            
        success, response = self.run_test(
            "Get All Enrollments",
            "GET",
            "api/enrollments",
            200,
            token=self.admin_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} enrollments")
        
        return success

    def test_get_user_enrollments(self):
        """Test fetching user's own enrollments"""
        if not self.learner_token or len(self.created_user_ids) < 3:
            print("❌ Skipped - No learner token or user IDs")
            return False
            
        learner_id = self.created_user_ids[2]  # Learner is the 3rd user created
        success, response = self.run_test(
            "Get User Enrollments",
            "GET",
            f"api/users/{learner_id}/enrollments",
            200,
            token=self.learner_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} enrollments for learner")
        
        return success

    def test_get_program_enrollments(self):
        """Test fetching enrollments for a program (instructor access)"""
        if not self.instructor_token or not self.created_program_id:
            print("❌ Skipped - No instructor token or program ID")
            return False
            
        success, response = self.run_test(
            "Get Program Enrollments",
            "GET",
            f"api/programs/{self.created_program_id}/enrollments",
            200,
            token=self.instructor_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} enrollments for program")
        
        return success

    # Certificate Tests
    def test_get_certificates(self):
        """Test fetching certificates (user can see their own)"""
        if not self.learner_token:
            print("❌ Skipped - No learner token available")
            return False
            
        success, response = self.run_test(
            "Get Certificates",
            "GET",
            "api/certificates",
            200,
            token=self.learner_token
        )
        
        if success and isinstance(response, list):
            print(f"   Found {len(response)} certificates")
        
        return success

    def test_certificate_verification(self):
        """Test certificate verification system"""
        # Test with invalid verification code
        verification_data = {
            "verification_code": "INVALID123"
        }
        
        success, response = self.run_test(
            "Verify Invalid Certificate",
            "POST",
            "api/certificates/verify",
            200,
            data=verification_data
        )
        
        if success and 'valid' in response:
            if not response['valid']:
                print(f"   ✅ Invalid certificate correctly rejected")
            else:
                print(f"   ⚠️  Warning: Invalid certificate was accepted")
        
        return success

    def test_manual_certificate_generation(self):
        """Test manual certificate generation (admin/instructor only)"""
        if not self.instructor_token or not self.created_program_id or len(self.created_user_ids) < 3:
            print("❌ Skipped - Missing instructor token, program ID, or user IDs")
            return False
            
        learner_id = self.created_user_ids[2]  # Learner is the 3rd user created
        
        success, response = self.run_test(
            "Manual Certificate Generation",
            "POST",
            f"api/programs/{self.created_program_id}/generate-certificate?user_id={learner_id}",
            400,  # Expecting 400 because user hasn't completed requirements
            token=self.instructor_token
        )
        
        if success:
            print(f"   ✅ Correctly prevented certificate generation for incomplete program")
        
        return success

    # Progress Tracking Tests
    def test_program_progress(self):
        """Test getting program progress"""
        if not self.learner_token or not self.created_program_id:
            print("❌ Skipped - No learner token or program ID")
            return False
            
        success, response = self.run_test(
            "Get Program Progress",
            "GET",
            f"api/programs/{self.created_program_id}/progress",
            200,
            token=self.learner_token
        )
        
        if success and 'program_id' in response:
            modules_count = len(response.get('modules', []))
            print(f"   Progress tracked for {modules_count} modules")
        
        return success

    # Role-based Access Control Tests
    def test_learner_cannot_create_program(self):
        """Test that learners cannot create programs"""
        if not self.learner_token:
            print("❌ Skipped - No learner token available")
            return False
            
        program_data = {
            "title": "Unauthorized Program",
            "description": "This should fail",
            "learning_objectives": ["Should not work"],
            "expiry_duration": 12,
            "renewal_requirements": "None"
        }
        
        success, response = self.run_test(
            "Learner Create Program (Should Fail)",
            "POST",
            "api/programs",
            403,  # Expecting forbidden
            data=program_data,
            token=self.learner_token
        )
        
        return success

    def test_learner_cannot_create_questions(self):
        """Test that learners cannot create questions"""
        if not self.learner_token:
            print("❌ Skipped - No learner token available")
            return False
            
        question_data = {
            "question_text": "Unauthorized question?",
            "question_type": "true_false",
            "correct_answer": "false",
            "points": 1
        }
        
        success, response = self.run_test(
            "Learner Create Question (Should Fail)",
            "POST",
            "api/questions",
            403,  # Expecting forbidden
            data=question_data,
            token=self.learner_token
        )
        
        return success

    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        success, response = self.run_test(
            "Unauthenticated Access (Should Fail)",
            "GET",
            "api/me",
            401,  # Expecting unauthorized
            token=None
        )
        
        return success

def main():
    print("🚀 Starting Comprehensive Training Management API Tests")
    print("=" * 60)
    
    # Setup
    tester = TrainingAPITester()
    
    # Run all tests in sequence
    tests = [
        # Basic health check
        tester.test_health_check,
        
        # Authentication tests
        tester.test_register_admin,
        tester.test_register_instructor, 
        tester.test_register_learner,
        tester.test_login_admin,
        tester.test_login_instructor,
        tester.test_login_learner,
        tester.test_get_current_user,
        
        # Question bank tests
        tester.test_create_multiple_choice_question,
        tester.test_create_true_false_question,
        tester.test_create_essay_question,
        tester.test_get_questions,
        tester.test_learner_cannot_access_questions,
        
        # Assessment tests
        tester.test_create_assessment,
        tester.test_get_assessments,
        tester.test_get_assessment_questions,
        tester.test_submit_assessment,
        
        # Program management tests (with authentication)
        tester.test_create_program,
        tester.test_get_programs,
        tester.test_get_program_by_id,
        tester.test_create_module,
        tester.test_get_program_modules,
        tester.test_create_unit,
        tester.test_get_module_units,
        tester.test_upload_content,
        tester.test_get_unit_content,
        tester.test_program_structure,
        
        # Enrollment tests
        tester.test_create_enrollment,
        tester.test_get_enrollments,
        tester.test_get_user_enrollments,
        tester.test_get_program_enrollments,
        
        # Certificate tests
        tester.test_get_certificates,
        tester.test_certificate_verification,
        tester.test_manual_certificate_generation,
        
        # Progress tracking tests
        tester.test_program_progress,
        
        # Role-based access control tests
        tester.test_learner_cannot_create_program,
        tester.test_learner_cannot_create_questions,
        tester.test_unauthenticated_access_denied
    ]
    
    print(f"\n📋 Running {len(tests)} comprehensive tests...")
    
    for test in tests:
        test()
    
    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! API is working correctly.")
        print("\n✅ Authentication system working")
        print("✅ Role-based access control working")
        print("✅ Question bank management working")
        print("✅ Assessment system working")
        print("✅ Program management working")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} tests failed.")
        print("\n🔧 Issues found that need attention:")
        if tester.admin_token is None:
            print("   - Admin authentication may be failing")
        if tester.instructor_token is None:
            print("   - Instructor authentication may be failing")
        if tester.learner_token is None:
            print("   - Learner authentication may be failing")
        if len(tester.created_question_ids) == 0:
            print("   - Question creation may be failing")
        if tester.created_assessment_id is None:
            print("   - Assessment creation may be failing")
        return 1

if __name__ == "__main__":
    sys.exit(main())