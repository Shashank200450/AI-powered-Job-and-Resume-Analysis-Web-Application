import unittest
import io
import os
from app import app, db

class JobsInlineTestSuite(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    def test_01_health_and_database(self):
        """Test health endpoint and database seeding"""
        res = self.client.get('/health')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['status'], 'healthy')
        self.assertGreaterEqual(data['job_roles_count'], 170)
        print(f"PASS: Health check OK (Engine: {data['database_engine']}, Roles: {data['job_roles_count']})")

    def test_02_registration_and_login(self):
        """Test user registration and login with bcrypt hashing"""
        test_user = "tester_unit"
        test_pass = "SecurePass123!"

        # Register
        reg_res = self.client.post('/auth', json={
            'action': 'register',
            'username': test_user,
            'email': 'tester@example.com',
            'phone': '555-0199',
            'password': test_pass
        })
        # Could be 201 if new, or 400 if already in DB
        self.assertIn(reg_res.status_code, [201, 400])

        # Login
        login_res = self.client.post('/auth', json={
            'action': 'login',
            'username': test_user,
            'password': test_pass
        })
        self.assertEqual(login_res.status_code, 200)
        login_data = login_res.get_json()
        self.assertTrue(login_data['success'])
        self.assertEqual(login_data['username'], test_user)
        print(f"PASS: User registration and login verified")

    def test_03_sample_resume_endpoint(self):
        """Test that sample resume is available and is a valid PDF"""
        res = self.client.get('/api/sample_resume')
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.mimetype, 'application/pdf')
        self.assertGreater(len(res.data), 1000)
        print(f"PASS: Sample resume PDF endpoint verified ({len(res.data)} bytes)")

    def test_04_resume_upload_analysis(self):
        """Test resume analysis against target job role"""
        # Read the sample resume PDF
        with open('static/sample_resume.pdf', 'rb') as f:
            pdf_bytes = f.read()

        data = {
            'jobRole': 'Software Engineer',
            'resume': (io.BytesIO(pdf_bytes), 'sample_resume.pdf', 'application/pdf')
        }
        res = self.client.post('/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        result = res.get_json()
        self.assertTrue(result['success'])
        self.assertGreaterEqual(result['probability'], 50)
        self.assertTrue(len(result['skillsFound']) > 0)
        print(f"PASS: Resume upload analysis verified: {result['probability']}% match for {result['jobRole']}")
        print(f"      Matched Skills: {result['skillsFound']}")

    def test_05_related_jobs_discovery(self):
        """Test related jobs matching against database"""
        with open('static/sample_resume.pdf', 'rb') as f:
            pdf_bytes = f.read()

        data = {
            'resume': (io.BytesIO(pdf_bytes), 'sample_resume.pdf', 'application/pdf')
        }
        res = self.client.post('/related_jobs', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        result = res.get_json()
        self.assertTrue(result['success'])
        self.assertGreater(len(result['relatedJobs']), 0)
        top_job = result['relatedJobs'][0]
        print(f"PASS: Related jobs verified. Top match: {top_job['jobRole']} ({top_job['probability']}%)")

    def test_06_chatbot_endpoint(self):
        """Test career chatbot responds constructively"""
        res = self.client.post('/chatbot', json={'message': 'How can I optimize my resume for ATS?'})
        self.assertEqual(res.status_code, 200)
        result = res.get_json()
        self.assertTrue(result['success'])
        self.assertIn('ATS', result['response'])
        print(f"PASS: Chatbot response verified: {result['response'][:75]}...")

if __name__ == '__main__':
    unittest.main()
