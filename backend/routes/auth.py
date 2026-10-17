"""
Authentication and Profile routes for AI Health Assistant.
Handles registration, login, logout, profile view/edit, account deletion,
and admin verification of doctors.
"""

from flask import Blueprint, request, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from backend import db as database
from backend.auth_utils import (
    role_required,
    get_current_user,
    check_rate_limit,
    record_failed_attempt,
    clear_attempts
)

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new patient or doctor.
    Doctors default to is_verified = 0 (pending approval).
    Patients default to is_verified = 1.
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    name = data.get('name', '').strip()
    role = data.get('role', 'patient').strip().lower()
    phone = data.get('phone', '').strip()

    if not email or not password or not name:
        return jsonify({'ok': False, 'error': 'Name, email, and password are required'}), 400

    if role not in ('patient', 'doctor'):
        return jsonify({'ok': False, 'error': 'Invalid role'}), 400

    if len(password) < 6:
        return jsonify({'ok': False, 'error': 'Password must be at least 6 characters'}), 400

    # Check if user already exists
    existing = database.fetch_one(g.db, "SELECT id FROM users WHERE email = ?", (email,))
    if existing:
        return jsonify({'ok': False, 'error': 'An account with this email already exists'}), 400

    password_hash = generate_password_hash(password)
    # Patients are auto-verified; Doctors require admin approval (is_verified = 0)
    is_verified = 1 if role == 'patient' else 0

    user_id = database.insert(
        g.db,
        "INSERT INTO users (name, email, password_hash, role, phone, is_verified) VALUES (?, ?, ?, ?, ?, ?)",
        (name, email, password_hash, role, phone, is_verified)
    )

    if role == 'patient':
        age = data.get('age')
        gender = data.get('gender')
        chronic_conditions = data.get('chronic_conditions', '')
        allergies = data.get('allergies', '')
        database.execute(
            g.db,
            "INSERT INTO patient_profiles (user_id, age, gender, chronic_conditions, allergies) VALUES (?, ?, ?, ?, ?)",
            (user_id, age, gender, chronic_conditions, allergies)
        )
    elif role == 'doctor':
        specialization = data.get('specialization', 'General Physician')
        clinic_name = data.get('clinic_name', '')
        address = data.get('address', '')
        city = data.get('city', 'Dehradun')
        lat = data.get('lat')
        lng = data.get('lng')
        fee = data.get('fee', 500.0)
        experience_years = data.get('experience_years', 0)

        # Medical Degree, Registration & Verification Document Details
        medical_degree = data.get('medical_degree', 'MBBS').strip() or 'MBBS'
        registration_number = data.get('registration_number', '').strip() or 'NMC-PENDING'
        medical_council = data.get('medical_council', 'State Medical Council').strip() or 'State Medical Council'
        graduation_year = data.get('graduation_year')
        try:
            graduation_year = int(graduation_year) if graduation_year else 2018
        except (ValueError, TypeError):
            graduation_year = 2018
        medical_college = data.get('medical_college', 'Medical College').strip() or 'Medical College'
        document_url = data.get('document_url', '')
        document_name = data.get('document_name', 'Medical_Registration_Certificate.pdf')

        database.execute(
            g.db,
            """INSERT INTO doctor_profiles 
               (user_id, specialization, clinic_name, address, city, lat, lng, fee, experience_years,
                medical_degree, registration_number, medical_council, graduation_year, medical_college,
                document_url, document_name, is_available) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)""",
            (user_id, specialization, clinic_name, address, city, lat, lng, fee, experience_years,
             medical_degree, registration_number, medical_council, graduation_year, medical_college,
             document_url, document_name)
        )


    # Set session login
    session['user_id'] = user_id
    session['user_role'] = role
    session['user_name'] = name

    return jsonify({
        'ok': True,
        'data': {
            'id': user_id,
            'name': name,
            'email': email,
            'role': role,
            'is_verified': is_verified,
            'message': 'Account created successfully. ' + ('Doctor account pending admin approval.' if role == 'doctor' else '')
        }
    }), 201

@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """
    Authenticate user with email and password.
    Includes brute-force rate limit protection.
    """
    data = request.get_json() or {}
    email = data.get('email', '').strip().lower()
    password = data.get('password', '')
    ip_address = request.remote_addr

    if not email or not password:
        return jsonify({'ok': False, 'error': 'Email and password are required'}), 400

    # Rate limiting check
    if not check_rate_limit(email, ip_address):
        return jsonify({'ok': False, 'error': 'Too many failed login attempts. Account locked for 5 minutes.'}), 429

    user = database.fetch_one(
        g.db,
        "SELECT id, name, email, password_hash, role, is_verified FROM users WHERE email = ?",
        (email,)
    )

    if not user or not check_password_hash(user['password_hash'], password):
        record_failed_attempt(email, ip_address)
        return jsonify({'ok': False, 'error': 'Invalid email or password'}), 401

    # Login successful
    clear_attempts(email)
    session['user_id'] = user['id']
    session['user_role'] = user['role']
    session['user_name'] = user['name']

    return jsonify({
        'ok': True,
        'data': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'is_verified': user.get('is_verified', 0)
        }
    })

@auth_bp.route('/api/auth/logout', methods=['POST'])
def logout():
    """Clear session data."""
    session.clear()
    return jsonify({'ok': True, 'data': {'message': 'Logged out successfully'}})

@auth_bp.route('/api/auth/me', methods=['GET'])
def me():
    """Return currently logged-in user profile."""
    user = get_current_user()
    if not user:
        return jsonify({'ok': False, 'error': 'Not logged in'}), 401

    profile = None
    if user['role'] == 'patient':
        profile = database.fetch_one(g.db, "SELECT * FROM patient_profiles WHERE user_id = ?", (user['id'],))
    elif user['role'] == 'doctor':
        profile = database.fetch_one(g.db, "SELECT * FROM doctor_profiles WHERE user_id = ?", (user['id'],))

    return jsonify({
        'ok': True,
        'data': {
            'id': user['id'],
            'name': user['name'],
            'email': user['email'],
            'role': user['role'],
            'is_verified': user.get('is_verified', 0),
            'profile': profile or {}
        }
    })

@auth_bp.route('/api/profile', methods=['GET', 'PUT', 'DELETE'])
def manage_profile():
    user = get_current_user()
    if not user:
        return jsonify({'ok': False, 'error': 'Not logged in'}), 401

    if request.method == 'GET':
        return me()

    elif request.method == 'PUT':
        data = request.get_json() or {}
        name = data.get('name', user['name']).strip()
        phone = data.get('phone', '')

        database.execute(
            g.db,
            "UPDATE users SET name = ?, phone = ? WHERE id = ?",
            (name, phone, user['id'])
        )

        if user['role'] == 'patient':
            age = data.get('age')
            gender = data.get('gender')
            chronic = data.get('chronic_conditions', '')
            allergies = data.get('allergies', '')
            database.execute(
                g.db,
                """UPDATE patient_profiles 
                   SET age = ?, gender = ?, chronic_conditions = ?, allergies = ? 
                   WHERE user_id = ?""",
                (age, gender, chronic, allergies, user['id'])
            )
        elif user['role'] == 'doctor':
            spec = data.get('specialization')
            clinic = data.get('clinic_name')
            address = data.get('address')
            city = data.get('city')
            fee = data.get('fee')
            exp = data.get('experience_years')
            database.execute(
                g.db,
                """UPDATE doctor_profiles 
                   SET specialization = ?, clinic_name = ?, address = ?, city = ?, fee = ?, experience_years = ? 
                   WHERE user_id = ?""",
                (spec, clinic, address, city, fee, exp, user['id'])
            )

        return jsonify({'ok': True, 'data': {'message': 'Profile updated successfully'}})

    elif request.method == 'DELETE':
        # Section 17 C: GDPR / Privacy Right to be Forgotten
        # Delete user and all associated records
        database.execute(g.db, "DELETE FROM users WHERE id = ?", (user['id'],))
        session.clear()
        return jsonify({'ok': True, 'data': {'message': 'Account and all health data deleted successfully'}})

# --- Doctor Admin Verification Endpoints (Section 17 B) ---

@auth_bp.route('/api/admin/doctors', methods=['GET'])
@role_required('admin')
def admin_list_doctors(user):
    """Admin endpoint to view all doctors with qualifications, council registration, and certificate document."""
    doctors = database.fetch_all(
        g.db,
        """SELECT u.id, u.name, u.email, u.phone, u.is_verified, u.created_at,
                  d.specialization, d.clinic_name, d.city, d.experience_years,
                  d.medical_degree, d.registration_number, d.medical_council,
                  d.graduation_year, d.medical_college, d.document_url, d.document_name, d.verification_notes
           FROM users u
           JOIN doctor_profiles d ON u.id = d.user_id
           WHERE u.role = 'doctor'
           ORDER BY u.created_at DESC"""
    )
    return jsonify({'ok': True, 'data': doctors})

@auth_bp.route('/api/admin/doctors/<int:doctor_id>/verify', methods=['PUT'])
@role_required('admin')
def admin_verify_doctor(user, doctor_id):
    """Admin endpoint to approve (1) or reject (2) a doctor with audit verification notes."""
    data = request.get_json() or {}
    status = data.get('status', 1)  # 1 = approved, 2 = rejected
    notes = data.get('notes', '')
    database.execute(
        g.db,
        "UPDATE users SET is_verified = ? WHERE id = ? AND role = 'doctor'",
        (status, doctor_id)
    )
    if notes:
        database.execute(
            g.db,
            "UPDATE doctor_profiles SET verification_notes = ? WHERE user_id = ?",
            (notes, doctor_id)
        )
    return jsonify({'ok': True, 'data': {'message': 'Doctor verification status updated'}})


@auth_bp.route('/api/admin/stats', methods=['GET'])
@role_required('admin')
def admin_stats(user):
    """Admin summary statistics."""
    patient_count = database.fetch_one(g.db, "SELECT COUNT(*) as count FROM users WHERE role = 'patient'")['count']
    doctor_count = database.fetch_one(g.db, "SELECT COUNT(*) as count FROM users WHERE role = 'doctor'")['count']
    pending_doctors = database.fetch_one(g.db, "SELECT COUNT(*) as count FROM users WHERE role = 'doctor' AND is_verified = 0")['count']
    consultation_count = database.fetch_one(g.db, "SELECT COUNT(*) as count FROM consultations")['count']
    assessment_count = database.fetch_one(g.db, "SELECT COUNT(*) as count FROM assessments")['count']

    return jsonify({
        'ok': True,
        'data': {
            'patients': patient_count,
            'doctors': doctor_count,
            'pending_doctors': pending_doctors,
            'consultations': consultation_count,
            'assessments': assessment_count
        }
    })

@auth_bp.route('/api/admin/patients', methods=['GET'])
@role_required('admin')
def admin_list_patients(user):
    """Admin endpoint to view all registered patients with profile and medical details."""
    patients = database.fetch_all(
        g.db,
        """SELECT u.id, u.name, u.email, u.phone, u.created_at,
                  p.age, p.gender, p.chronic_conditions, p.allergies,
                  (SELECT COUNT(*) FROM assessments a WHERE a.patient_id = u.id) as assessment_count,
                  (SELECT COUNT(*) FROM consultations c WHERE c.patient_id = u.id) as consultation_count
           FROM users u
           LEFT JOIN patient_profiles p ON u.id = p.user_id
           WHERE u.role = 'patient'
           ORDER BY u.created_at DESC"""
    )
    return jsonify({'ok': True, 'data': patients})

@auth_bp.route('/api/admin/users', methods=['GET'])
@role_required('admin')
def admin_list_all_users(user):
    """Admin endpoint to view all system users (patients, doctors, admins)."""
    users = database.fetch_all(
        g.db,
        """SELECT u.id, u.name, u.email, u.phone, u.role, u.is_verified, u.created_at,
                  p.age, p.gender, p.chronic_conditions,
                  d.specialization, d.clinic_name
           FROM users u
           LEFT JOIN patient_profiles p ON u.id = p.user_id
           LEFT JOIN doctor_profiles d ON u.id = d.user_id
           ORDER BY u.created_at DESC"""
    )
    return jsonify({'ok': True, 'data': users})

