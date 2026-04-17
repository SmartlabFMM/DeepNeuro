"""
API Client for communicating with DeepNeuro Flask Backend
"""
import requests
import os
import tempfile
from contextlib import ExitStack
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class APIClient:
    """Client for making HTTP requests to Flask backend"""
    
    def __init__(self, base_url=None):
        """Initialize API client with base URL from environment or parameter"""
        self.base_url = base_url or os.environ.get('API_BASE_URL')
        self.timeout = int(os.environ.get('API_TIMEOUT', 10))
    
    def _make_request(self, method, endpoint, **kwargs):
        """Make HTTP request and handle errors"""
        try:
            url = f"{self.base_url}{endpoint}"
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            return self._parse_json_response(response)
        except requests.exceptions.ConnectionError:
            return {'success': False, 'message': 'Failed to connect to server'}, 500
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Request timeout'}, 500
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

    @staticmethod
    def _parse_json_response(response, fallback_message='Request failed'):
        """Parse JSON responses, preserving status codes for non-JSON errors."""
        try:
            return response.json(), response.status_code
        except ValueError:
            message = (response.text or '').strip() or f'{fallback_message}: {response.reason}'
            return {'success': False, 'message': message}, response.status_code

    @staticmethod
    def _extract_filename(response, default_name='downloaded_file'):
        """Extract filename from Content-Disposition, with a safe fallback."""
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[-1].strip().strip('"')
            if filename:
                return filename
        return default_name
    
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

    def get_segmentation_models(self, diagnosis_type=None):
        """Get available segmentation models, optionally filtered by diagnosis type."""
        params = {}
        if diagnosis_type:
            params['diagnosis_type'] = diagnosis_type
        return self._make_request('GET', '/api/models/segmentation', params=params)

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
    
    def download_attached_file(self, request_id, file_type, user_email, file_index=0, save_path=None):
        """Download a test or segmentation file from a request."""
        try:
            url = f"{self.base_url}/api/diagnosis/download/{request_id}/{file_type}/{user_email}"
            response = requests.get(
                url,
                params={'file_index': file_index},
                timeout=self.timeout,
                stream=True,
            )
            
            if response.status_code == 200:
                filename = self._extract_filename(response)
                # If save_path provided, save file there
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    return {'success': True, 'message': f'File saved to {save_path}', 'file_path': save_path, 'filename': filename}, 200
                else:
                    # Return file content and filename
                    return {'success': True, 'data': response.content, 'filename': filename}, 200

            return self._parse_json_response(response, fallback_message='Download failed')
        except requests.exceptions.ConnectionError:
            return {'success': False, 'message': 'Failed to connect to server'}, 500
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Request timeout'}, 500
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

    def upload_file(self, file_path, uploaded_by_email, related_entity_id=None):
        """Upload a file to the backend file storage API."""
        try:
            if not file_path or not os.path.exists(file_path):
                return {'success': False, 'message': 'File not found'}, 400

            with open(file_path, 'rb') as file_handle:
                files = {
                    'file': (os.path.basename(file_path), file_handle)
                }
                data = {
                    'uploaded_by_email': uploaded_by_email,
                    'related_entity_id': related_entity_id or '',
                }
                response = requests.post(
                    f"{self.base_url}/api/files/upload",
                    data=data,
                    files=files,
                    timeout=self.timeout,
                )

            return self._parse_json_response(response, fallback_message='Upload failed')
        except requests.exceptions.ConnectionError:
            return {'success': False, 'message': 'Failed to connect to server'}, 500
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Request timeout'}, 500
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

    def generate_glioma_segmentation(self, flair_file, t1_file, t1ce_file, t2_file, save_path=None):
        """Generate a glioma segmentation from four MRI modalities."""
        try:
            segmentation_timeout = int(os.environ.get('GLIOMA_SEGMENTATION_TIMEOUT', 300))
            modality_paths = {
                'flair': flair_file,
                't1': t1_file,
                't1ce': t1ce_file,
                't2': t2_file,
            }

            for modality, file_path in modality_paths.items():
                if not file_path or not os.path.exists(file_path):
                    return {'success': False, 'message': f'{modality.upper()} file not found'}, 400

            with ExitStack() as stack:
                files = {
                    modality: (os.path.basename(file_path), stack.enter_context(open(file_path, 'rb')))
                    for modality, file_path in modality_paths.items()
                }

                response = requests.post(
                    f"{self.base_url}/api/models/glioma/segment",
                    files=files,
                    timeout=segmentation_timeout,
                    stream=True,
                )

                if response.status_code == 200:
                    filename = self._extract_filename(response, default_name='glioma_segmentation.nii.gz')
                    if not save_path:
                        temp_dir = os.path.join(tempfile.gettempdir(), 'DeepNeuro', 'generated_segmentations')
                        os.makedirs(temp_dir, exist_ok=True)
                        save_path = os.path.join(temp_dir, filename)
                        if os.path.exists(save_path):
                            name_root, ext = os.path.splitext(filename)
                            if name_root.endswith('.nii') and ext == '.gz':
                                name_root = name_root[:-4]
                                ext = '.nii.gz'

                            counter = 2
                            while os.path.exists(save_path):
                                save_path = os.path.join(temp_dir, f"{name_root}_{counter}{ext}")
                                counter += 1
                    else:
                        os.makedirs(os.path.dirname(save_path), exist_ok=True)

                    with open(save_path, 'wb') as file_handle:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file_handle.write(chunk)

                    return {
                        'success': True,
                        'message': 'Segmentation generated successfully',
                        'file_path': save_path,
                        'filename': filename,
                    }, 200

                return self._parse_json_response(response, fallback_message='Segmentation generation failed')

        except requests.exceptions.ConnectionError:
            return {'success': False, 'message': 'Failed to connect to server'}, 500
        except requests.exceptions.Timeout:
            return {'success': False, 'message': 'Request timeout'}, 500
        except Exception as e:
            return {'success': False, 'message': f'Error: {str(e)}'}, 500

    def get_uploaded_files(self, uploaded_by_email=None, related_entity_id=None):
        """Fetch uploaded file metadata from the backend API."""
        params = {}
        if uploaded_by_email:
            params['uploaded_by_email'] = uploaded_by_email
        if related_entity_id:
            params['related_entity_id'] = related_entity_id
        return self._make_request('GET', '/api/files', params=params)

    def download_uploaded_file(self, file_id, user_email, save_path=None):
        """Download a stored file by ID."""
        try:
            url = f"{self.base_url}/api/files/{file_id}/download"
            response = requests.get(
                url,
                params={'user_email': user_email},
                timeout=self.timeout,
                stream=True,
            )

            if response.status_code == 200:
                filename = self._extract_filename(response)
                if save_path:
                    with open(save_path, 'wb') as file_handle:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                file_handle.write(chunk)
                    return {'success': True, 'message': f'File saved to {save_path}', 'file_path': save_path, 'filename': filename}, 200

                return {'success': True, 'data': response.content, 'filename': filename}, 200

            return self._parse_json_response(response, fallback_message='Download failed')
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
