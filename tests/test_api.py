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
    orig_db_url = config.DATABASE_URL
    config.DATABASE_URL = ''
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

    config.DATABASE_URL = orig_db_url
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

def test_doctor_credentials_registration_and_review(client):
    """Test doctor registration with degree, license registration number, and document inspection."""
    # 1. Register a doctor with degrees and council license
    reg_res = client.post('/api/auth/register', json={
        'name': 'Dr. Kavish Mehra',
        'email': 'kavish@demo.com',
        'password': 'Doctor@123',
        'role': 'doctor',
        'specialization': 'Cardiologist',
        'city': 'Dehradun',
        'medical_degree': 'MBBS, MD',
        'registration_number': 'UKMC-2019-9041',
        'medical_council': 'Uttarakhand Medical Council',
        'graduation_year': 2017,
        'medical_college': 'AIIMS Rishikesh',
        'document_url': 'data:image/svg+xml;utf8,<svg>SampleCert</svg>',
        'document_name': 'AIIMS_Degree_Certificate.svg'
    })
    assert reg_res.status_code == 201
    doc_id = reg_res.get_json()['data']['id']
    client.post('/api/auth/logout')

    # 2. Admin logs in and reviews credentials
    login_user(client, 'admin@demo.com', 'Admin@123')
    docs_res = client.get('/api/admin/doctors')
    assert docs_res.status_code == 200
    docs = docs_res.get_json()['data']
    doc = next((d for d in docs if d['id'] == doc_id), None)
    assert doc is not None
    assert doc['medical_degree'] == 'MBBS, MD'
    assert doc['registration_number'] == 'UKMC-2019-9041'
    assert doc['medical_council'] == 'Uttarakhand Medical Council'
    assert doc['document_name'] == 'AIIMS_Degree_Certificate.svg'

    # 3. Admin verifies and approves with audit notes
    verify_res = client.put(f'/api/admin/doctors/{doc_id}/verify', json={
        'status': 1,
        'notes': 'Degrees and State Council registration verified against UKMC registry.'
    })
    assert verify_res.status_code == 200
    assert verify_res.get_json()['ok'] is True


def test_accurate_symptom_nlp_extraction():
    from backend.services.ai_service import extract_structured_data_demo
    from backend.services.risk_engine import calculate_risk_score

    # Simulate realistic user messages
    messages = [
        {'role': 'user', 'content': 'I have severe fever and stomach pain for 4 days getting worse, temperature is 102.5'},
        {'role': 'assistant', 'content': 'Do you have any other symptoms?'},
        {'role': 'user', 'content': 'Yes, severe headache and vomiting'}
    ]

    extracted = extract_structured_data_demo(messages, 'fever')
    assert extracted['duration_days'] == 4
    assert extracted['severity'] == 'severe'
    assert extracted['worsening'] is True
    assert extracted['temperature_f'] == 102.5
    assert len(extracted['other_symptoms']) >= 1

    # Ensure risk score is calculated accurately and NOT 0
    score, reasons = calculate_risk_score(extracted)
    assert score >= 5
    assert any('Severe' in r for r in reasons)
    assert any('worse' in r for r in reasons)


def test_assessment_high_risk_alert_and_offline_doctor_consult(client):
    login_user(client, 'patient@demo.com', 'Patient@123')

    # 1. Create assessment
    ass_res = client.post('/api/assessments', json={'client_id': 'alert-test-ass'})
    assert ass_res.status_code == 201
    ass_id = ass_res.get_json()['data']['id']

    # 2. Trigger high risk alert
    alert_res = client.post(f'/api/assessments/{ass_id}/alert')
    assert alert_res.status_code == 200
    alert_data = alert_res.get_json()['data']
    assert alert_data['alert_active'] is True

    # 3. Check notifications
    notif_res = client.get('/api/notifications')
    assert notif_res.status_code == 200
    notifs = notif_res.get_json()['data']
    assert any('High-Risk Health Alert' in n['text'] for n in notifs)

    # 4. Search related doctors including offline
    doc_res = client.get('/api/doctors/nearby?category=fever&include_offline=true')
    assert doc_res.status_code == 200
    docs = doc_res.get_json()['data']
    assert len(docs) > 0
    assert 'medical_degree' in docs[0]

    # 5. Request consultation with is_urgent flag
    target_doc = docs[0]
    consult_res = client.post('/api/consultations', json={
        'client_id': 'urgent-consult-client',
        'doctor_id': target_doc['id'],
        'assessment_id': ass_id,
        'consent_given': True,
        'is_urgent': True
    })
    assert consult_res.status_code == 201
    assert consult_res.get_json()['data']['is_urgent'] is True


def test_automatic_dialogue_summary_and_doctor_routing(client):
    """Test that patient talk with the checker automatically generates a structured summary and routes case to doctor."""
    login_user(client, 'patient@demo.com', 'Patient@123')

    # 1. Create assessment
    ass_res = client.post('/api/assessments', json={'client_id': 'auto-route-test-ass'})
    assert ass_res.status_code == 201
    ass_id = ass_res.get_json()['data']['id']

    # 2. Complete with red flag (immediate auto-route)
    msg_res = client.post(f'/api/assessments/{ass_id}/message', json={
        'content': 'I am having crushing chest pain radiating to my left arm',
        'client_id': 'auto-msg-1'
    })
    assert msg_res.status_code == 200
    data = msg_res.get_json()['data']
    assert data['type'] == 'urgent'
    assert 'summary' in data
    assert 'Chief Complaint' in data['summary'] or 'crushing chest pain' in data['summary']
    assert data['consultation_id'] is not None
    assert data['doctor'] is not None

    # 3. Patient gets assessment details and verifies assigned_consultation is present
    get_res = client.get(f'/api/assessments/{ass_id}')
    assert get_res.status_code == 200
    ass_data = get_res.get_json()['data']
    assert ass_data['assigned_consultation'] is not None
    assert ass_data['assigned_consultation']['id'] == data['consultation_id']

    # 4. Doctor logs in and views consultation details
    login_user(client, 'doctor@demo.com', 'Doctor@123')
    consult_id = data['consultation_id']
    doc_res = client.get(f'/api/consultations/{consult_id}')
    assert doc_res.status_code == 200
    doc_data = doc_res.get_json()['data']
    assert doc_data['consultation']['status'] == 'pending'
    assert doc_data['assessment']['summary'] is not None
    assert len(doc_data['messages']) >= 1



