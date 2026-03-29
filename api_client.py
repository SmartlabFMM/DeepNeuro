"""
API Client for communicating with DeepNeuro Flask Backend
"""
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class APIClient:
    """Client for making HTTP requests to Flask backend"""
    
    def __init__(self, base_url=None):
        """Initialize API client with base URL from environment or parameter"""
        self.base_url = base_url or os.environ.get('API_BASE_URL', 'http://localhost:5000')
        self.timeout = int(os.environ.get('API_TIMEOUT', 10))
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make HTTP request and handle errors"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            return response.json(), response.status_code
        except requests.exceptions.ConnectionError:
            return {'success': False, 'message': 'Failed to connect to server'}, 500
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Request timeout'}, 500
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500
    
    # Authentication endpoints
    def register(self, name, email, password, medical_id):
        """Register a new user"""
        data = {
            'name': name,
            'email': email,
            'password': password,
            'medical_id': medical_id
        }
        return self._make_request('POST', '/api/auth/register', json=data)
    
    def verify_email(self, email, verification_code):
        """Verify email address"""
        data = {
            'email': email,
            'verification_code': verification_code
        }
        return self._make_request('POST', '/api/auth/verify-email', json=data)
    
    def login(self, email, password):
        """Login user"""
        data = {
            'email': email,
            'password': password
        }
        return self._make_request('POST', '/api/auth/login', json=data)
    
    def get_user(self, email):
        """Get user information"""
        return self._make_request('GET', f'/api/auth/user/{email}')
    
    def request_password_reset(self, email):
        """Request password reset"""
        data = {'email': email}
        return self._make_request('POST', '/api/auth/request-password-reset', json=data)
    
    def verify_reset_code(self, email, verification_code):
        """Verify password reset code"""
        data = {
            'email': email,
            'verification_code': verification_code
        }
        return self._make_request('POST', '/api/auth/verify-reset-code', json=data)
    
    def reset_password(self, email, verification_code, new_password):
        """Reset password"""
        data = {
            'email': email,
            'verification_code': verification_code,
            'new_password': new_password
        }
        return self._make_request('POST', '/api/auth/reset-password', json=data)
    
    # Diagnosis endpoints
    def submit_diagnosis_request(self, doctor_email, doctor_name, patient_name,
                                patient_id, patient_age, patient_gender, patient_email,
                                phone_number, diagnosis_type, scan_date, priority,
                                radiologist_email, description):
        """Submit a diagnosis request"""
        data = {
            'doctor_email': doctor_email,
            'doctor_name': doctor_name,
            'patient_name': patient_name,
            'patient_id': patient_id,
            'patient_age': patient_age,
            'patient_gender': patient_gender,
            'patient_email': patient_email,
            'phone_number': phone_number,
            'diagnosis_type': diagnosis_type,
            'scan_date': scan_date,
            'priority': priority,
            'radiologist_email': radiologist_email,
            'description': description
        }
        return self._make_request('POST', '/api/diagnosis/submit', json=data)
    
    def get_doctor_requests(self, doctor_email):
        """Get all requests submitted by a doctor"""
        return self._make_request('GET', f'/api/diagnosis/doctor/{doctor_email}')
    
    def get_radiologist_requests(self, radiologist_email):
        """Get all requests sent to a radiologist"""
        return self._make_request('GET', f'/api/diagnosis/radiologist/{radiologist_email}')
    
    def get_all_radiologists(self):
        """Get list of all available radiologists"""
        return self._make_request('GET', '/api/diagnosis/radiologists')
    
    def get_previous_cases(self, doctor_email):
        """Get previous cases for a doctor"""
        return self._make_request('GET', f'/api/diagnosis/previous-cases/{doctor_email}')

    def add_patient(self, doctor_email, patient_name, patient_age, patient_sex,
                    patient_id, patient_email, phone_number, has_conditions, conditions_notes):
        """Add a patient profile for a doctor"""
        data = {
            'doctor_email': doctor_email,
            'patient_name': patient_name,
            'patient_age': patient_age,
            'patient_sex': patient_sex,
            'patient_id': patient_id,
            'patient_email': patient_email,
            'phone_number': phone_number,
            'has_conditions': has_conditions,
            'conditions_notes': conditions_notes
        }
        return self._make_request('POST', '/api/diagnosis/patients/add', json=data)

    def get_doctor_patients(self, doctor_email):
        """Get all patients for a doctor"""
        return self._make_request('GET', f'/api/diagnosis/patients/doctor/{doctor_email}')

    def delete_patient(self, doctor_email, patient_id):
        """Delete a patient profile for a doctor"""
        data = {
            'doctor_email': doctor_email,
            'patient_id': patient_id,
        }
        return self._make_request('DELETE', '/api/diagnosis/patients/delete', json=data)
    
    def mark_read_doctor(self, request_id):
        """Mark request as read by doctor"""
        return self._make_request('PUT', f'/api/diagnosis/mark-read/doctor/{request_id}')
    
    def mark_read_radiologist(self, request_id):
        """Mark request as read by radiologist"""
        return self._make_request('PUT', f'/api/diagnosis/mark-read/radiologist/{request_id}')

    def complete_case_request(self, request_id, radiologist_email, diagnosis_type,
                              uploaded_test_file, segmentation_file):
        """Attach radiology files to a request and mark it completed."""
        data = {
            'radiologist_email': radiologist_email,
            'diagnosis_type': diagnosis_type,
            'uploaded_test_file': uploaded_test_file,
            'segmentation_file': segmentation_file,
        }
        return self._make_request('PUT', f'/api/diagnosis/complete/{request_id}', json=data)
    
    def download_attached_file(self, request_id, file_type, user_email, save_path=None):
        """Download a test or segmentation file from a request."""
        try:
            url = f"{self.base_url}/api/diagnosis/download/{request_id}/{file_type}/{user_email}"
            response = requests.get(url, timeout=self.timeout, stream=True)
            
            if response.status_code == 200:
                # If save_path provided, save file there
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    return {'success': True, 'message': f'File saved to {save_path}', 'file_path': save_path}, 200
                else:
                    # Return file content and filename
                    filename = response.headers.get('content-disposition', '').split('filename=')[-1].strip('"')
                    return {'success': True, 'data': response.content, 'filename': filename}, 200
            else:
                try:
                    error_data = response.json()
                    return error_data, response.status_code
                except:
                    return {'success': False, 'message': f'Download failed: {response.reason}'}, response.status_code
        except requests.exceptions.ConnectionError:
            return {'success': False, 'message': 'Failed to connect to server'}, 500
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Request timeout'}, 500
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500
    
    # Utility methods
    @staticmethod
    def generate_verification_code(length=6):
        """Generate a random verification code"""
        import random
        import string
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def get_expiration_time(minutes=15):
        """Get expiration time for verification code"""
        return datetime.now() + timedelta(minutes=minutes)


# Global API client instance
api_client = APIClient()
