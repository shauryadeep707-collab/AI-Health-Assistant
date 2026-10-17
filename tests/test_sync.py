"""
Offline Synchronization and Idempotency tests for AI Health Assistant.
Verifies client_id uniqueness, idempotency of repeated requests,
and data consistency during offline-online transitions.
"""

import os
import pytest
from backend.app import create_app
from backend.config import config
from backend import db as database
from database.seed import seed_database

@pytest.fixture
def app():
    test_db_path = os.path.join(os.path.dirname(__file__), 'test_sync.db')
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

def test_assessment_creation_idempotency(client):
    """
    Submitting the same client_id multiple times (e.g. outbox flush retry)
    must return the existing assessment without creating duplicates.
    """
    client.post('/api/auth/login', json={'email': 'patient@demo.com', 'password': 'Patient@123'})
    client_uuid = "unique-client-uuid-12345"

    # First request
    res1 = client.post('/api/assessments', json={'client_id': client_uuid})
    assert res1.status_code == 201
    id1 = res1.get_json()['data']['id']

    # Second request with SAME client_id
    res2 = client.post('/api/assessments', json={'client_id': client_uuid})
    assert res2.status_code == 200
    id2 = res2.get_json()['data']['id']

    # IDs must match and only one record should exist
    assert id1 == id2

    conn = database.get_connection()
    count = database.fetch_one(conn, "SELECT COUNT(*) as cnt FROM assessments WHERE client_id = ?", (client_uuid,))['cnt']
    database.close_connection(conn)
    assert count == 1

def test_consultation_request_idempotency(client):
    """
    Submitting the same consultation client_id multiple times must not duplicate.
    """
    client.post('/api/auth/login', json={'email': 'patient@demo.com', 'password': 'Patient@123'})

    # Create assessment
    ass_res = client.post('/api/assessments', json={'client_id': 'ass-sync-test'})
    ass_id = ass_res.get_json()['data']['id']

    doctor_res = client.get('/api/doctors/nearby')
    doc_id = doctor_res.get_json()['data'][0]['id']

    consult_uuid = "consult-idempotent-uuid-777"

    # First request
    c_res1 = client.post('/api/consultations', json={
        'client_id': consult_uuid,
        'assessment_id': ass_id,
        'doctor_id': doc_id,
        'consent_given': True
    })
    assert c_res1.status_code == 201
    c_id1 = c_res1.get_json()['data']['id']

    # Retry submission with same client_id
    c_res2 = client.post('/api/consultations', json={
        'client_id': consult_uuid,
        'assessment_id': ass_id,
        'doctor_id': doc_id,
        'consent_given': True
    })
    assert c_res2.status_code == 200
    c_id2 = c_res2.get_json()['data']['id']

    assert c_id1 == c_id2

def test_patient_offline_doctor_reads_synced_data(client):
    """
    Once patient syncs data to server, doctor can read and review it
    even if patient goes offline afterwards.
    """
    # 1. Patient syncs assessment and consultation
    client.post('/api/auth/login', json={'email': 'patient@demo.com', 'password': 'Patient@123'})
    ass_res = client.post('/api/assessments', json={'client_id': 'offline-test-ass'})
    ass_id = ass_res.get_json()['data']['id']

    doctor_res = client.get('/api/doctors/nearby')
    docs = doctor_res.get_json()['data']
    doc_id = next(d['id'] for d in docs if d['email'] == 'doctor@demo.com')

    req = client.post('/api/consultations', json={
        'client_id': 'offline-sync-c-1',
        'assessment_id': ass_id,
        'doctor_id': doc_id,
        'consent_given': True
    })
    c_id = req.get_json()['data']['id']

    # 2. Patient logs out / device goes offline
    client.post('/api/auth/logout')

    # 3. Doctor logs in and accesses the consultation
    client.post('/api/auth/login', json={'email': 'doctor@demo.com', 'password': 'Doctor@123'})
    doc_view = client.get(f'/api/consultations/{c_id}')
    assert doc_view.status_code == 200
    detail = doc_view.get_json()['data']
    assert detail['consultation']['id'] == c_id
    assert detail['patient']['name'] == 'Rahul Sharma'
