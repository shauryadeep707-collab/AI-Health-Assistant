"""
API endpoint and Integration tests for AI Health Assistant.
Tests authentication, role authorization, consultation workflows,
nearby doctor geolocation sorting, doctor admin approvals, and privacy deletion.
"""

import os
import json
import pytest
from backend.app import create_app
from backend.config import config
from backend import db as database
from database.seed import seed_database

@pytest.fixture
def app():
    # Use a temporary test SQLite database
    test_db_path = os.path.join(os.path.dirname(__file__), 'test_assistant.db')
    config.SQLITE_PATH = test_db_path
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    app = create_app()
    app.config['TESTING'] = True

    with app.app_context():
        conn = database.get_connection()
        database.init_db(conn)
        seed_database(conn)
        database.close_connection(conn)

    yield app

    if os.path.exists(test_db_path):
        os.remove(test_db_path)

@pytest.fixture
def client(app):
    return app.test_client()

def login_user(client, email, password):
    return client.post('/api/auth/login', json={'email': email, 'password': password})

# --- Authentication & Access Control Tests ---

def test_login_patient_success(client):
    res = login_user(client, 'patient@demo.com', 'Patient@123')
    assert res.status_code == 200
    data = res.get_json()
    assert data['ok'] is True
    assert data['data']['role'] == 'patient'

def test_login_invalid_password(client):
    res = login_user(client, 'patient@demo.com', 'WrongPass')
    assert res.status_code == 401
    data = res.get_json()
    assert data['ok'] is False

def test_role_access_control_patient_to_doctor_endpoint(client):
    # Patient tries to toggle doctor availability
    login_user(client, 'patient@demo.com', 'Patient@123')
    res = client.put('/api/doctor/availability', json={'is_available': False})
    # Should be 403 Forbidden
    assert res.status_code == 403

def test_cross_patient_data_isolation(client):
    # 1. Login as patient 1 and create assessment
    login_user(client, 'patient@demo.com', 'Patient@123')
    res = client.post('/api/assessments', json={'client_id': 'patient-1-assessment'})
    assert res.status_code == 201
    assessment_id = res.get_json()['data']['id']

    # 2. Logout and login as patient 2
    client.post('/api/auth/logout')
    login_user(client, 'patient2@demo.com', 'Patient@123')

    # 3. Patient 2 attempts to read Patient 1's assessment
    read_res = client.get(f'/api/assessments/{assessment_id}')
    assert read_res.status_code == 403
    assert read_res.get_json()['ok'] is False

# --- Doctor Geolocation & Search Tests ---

def test_nearby_doctors_sorting(client):
    login_user(client, 'patient@demo.com', 'Patient@123')
    # Search near Dehradun clock tower
    res = client.get('/api/doctors/nearby?lat=30.3165&lng=78.0322&radius_km=50')
    assert res.status_code == 200
    docs = res.get_json()['data']
    assert len(docs) > 0
    # Verify sorted ascending by distance
    distances = [d['distance_km'] for d in docs if d['distance_km'] is not None]
    assert distances == sorted(distances)

# --- Consultation Lifecycle & Conflict Rules ---

def test_consultation_status_flow(client):
    # 1. Patient creates assessment and sends consultation request
    login_user(client, 'patient@demo.com', 'Patient@123')
    res = client.post('/api/assessments', json={'client_id': 'consult-test-assessment'})
    ass_id = res.get_json()['data']['id']

    # Find Dr. Amit Verma (doctor@demo.com)
    doctor_res = client.get('/api/doctors/nearby')
    docs = doctor_res.get_json()['data']
    doc_id = next(d['id'] for d in docs if d['email'] == 'doctor@demo.com')

    req_res = client.post('/api/consultations', json={
        'client_id': 'consult-uuid-1',
        'assessment_id': ass_id,
        'doctor_id': doc_id,
        'consent_given': True
    })
    assert req_res.status_code == 201
    consult_id = req_res.get_json()['data']['id']

    # 2. Doctor logs in, accepts case
    client.post('/api/auth/logout')
    login_user(client, 'doctor@demo.com', 'Doctor@123')

    accept_res = client.put(f'/api/consultations/{consult_id}/status', json={'status': 'accepted'})
    assert accept_res.status_code == 200
    assert accept_res.get_json()['data']['status'] == 'accepted'

    # 3. Doctor completes case with advice
    complete_res = client.put(f'/api/consultations/{consult_id}/status', json={
        'status': 'completed',
        'doctor_advice': 'Take plenty of fluids and rest. Review in 3 days.'
    })
    assert complete_res.status_code == 200
    assert complete_res.get_json()['data']['status'] == 'completed'

    # 4. Conflict rule test: Backward status transition must be rejected
    backward_res = client.put(f'/api/consultations/{consult_id}/status', json={'status': 'pending'})
    assert backward_res.status_code == 400
    assert 'Illegal status transition' in backward_res.get_json()['error']

# --- Doctor Admin Verification (Section 17 B) ---

def test_doctor_admin_verification(client):
    # 1. Register a new doctor
    reg_res = client.post('/api/auth/register', json={
        'name': 'Dr. New Applicant',
        'email': 'newdoc@demo.com',
        'password': 'Password@123',
        'role': 'doctor',
        'specialization': 'Cardiologist',
        'city': 'Dehradun'
    })
    assert reg_res.status_code == 201
    new_doc_id = reg_res.get_json()['data']['id']
    client.post('/api/auth/logout')

    # 2. Patient searches doctors: unverified doctor MUST NOT appear
    login_user(client, 'patient@demo.com', 'Patient@123')
    nearby_res = client.get('/api/doctors/nearby')
    ids = [d['id'] for d in nearby_res.get_json()['data']]
    assert new_doc_id not in ids
    client.post('/api/auth/logout')

    # 3. Admin logs in and approves doctor
    login_user(client, 'admin@demo.com', 'Admin@123')
    verify_res = client.put(f'/api/admin/doctors/{new_doc_id}/verify', json={'status': 1})
    assert verify_res.status_code == 200
    client.post('/api/auth/logout')

    # 4. Patient searches again: now approved doctor appears
    login_user(client, 'patient@demo.com', 'Patient@123')
    nearby_res2 = client.get('/api/doctors/nearby')
    ids2 = [d['id'] for d in nearby_res2.get_json()['data']]
    assert new_doc_id in ids2

# --- Privacy Account Deletion (Section 17 C) ---

def test_delete_account_and_data(client):
    # Register disposable patient
    client.post('/api/auth/register', json={
        'name': 'Temporary User',
        'email': 'temp@demo.com',
        'password': 'TempPass@123',
        'role': 'patient'
    })
    # Delete account
    del_res = client.delete('/api/profile')
    assert del_res.status_code == 200
    assert del_res.get_json()['ok'] is True

    # Attempt login with deleted credentials
    login_res = login_user(client, 'temp@demo.com', 'TempPass@123')
    assert login_res.status_code == 401

def test_admin_list_patients_and_users(client):
    login_user(client, 'admin@demo.com', 'Admin@123')
    
    # 1. Test GET /api/admin/patients
    res = client.get('/api/admin/patients')
    assert res.status_code == 200
    data = res.get_json()
    assert data['ok'] is True
    assert len(data['data']) >= 2
    patient_emails = [p['email'] for p in data['data']]
    assert 'patient@demo.com' in patient_emails

    # 2. Test GET /api/admin/users
    res_users = client.get('/api/admin/users')
    assert res_users.status_code == 200
    u_data = res_users.get_json()
    assert u_data['ok'] is True
    assert len(u_data['data']) >= 15
    roles = {u['role'] for u in u_data['data']}
    assert 'admin' in roles
    assert 'patient' in roles
    assert 'doctor' in roles

