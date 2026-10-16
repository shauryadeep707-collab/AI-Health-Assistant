"""
Demo Data Seeder for AI Health Assistant.
Populates initial administrative, patient, and doctor records for local testing
and university project demonstrations.

WHY this module exists:
A freshly initialized database has zero users or directory entries.
This script provisions realistic demo personas (admin, patients, specialized doctors)
so examiners and evaluators can immediately test triage, chat, search, and booking workflows.
"""

import os
import sys
import secrets
from werkzeug.security import generate_password_hash

# Ensure project root is available in sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend import db as database


def seed_database(conn):
    """
    Seed initial demo users and profiles into the database.
    
    If the users table already contains records, seeding is skipped
    to prevent duplicate data or accidental overwrites.
    """
    # 1. Check if users table already has data
    if database.count_users(conn) > 0:
        print('  Users table already contains data. Skipping seeding.')
        return

    print('  Starting demo database seeding...')

    # Counts for summary report
    admin_count = 0
    patient_count = 0
    doctor_count = 0

    # ---------------------------------------------------------
    # 1. Admin User
    # ---------------------------------------------------------
    admin_password_hash = generate_password_hash('Admin@123')
    admin_id = database.insert(
        conn,
        """INSERT INTO users (name, email, password_hash, role, phone, is_verified)
           VALUES (?, ?, ?, ?, ?, ?)""",
        ('Admin User', 'admin@demo.com', admin_password_hash, 'admin', '+91 98000 00001', 1)
    )
    admin_count += 1

    # ---------------------------------------------------------
    # 2. Patient Users and Profiles
    # ---------------------------------------------------------
    patients_data = [
        {
            'name': 'Rahul Sharma',
            'email': 'patient@demo.com',
            'password': 'Patient@123',
            'phone': '+91 98765 43210',
            'age': 28,
            'gender': 'Male',
            'chronic_conditions': 'None',
            'allergies': 'None'
        },
        {
            'name': 'Priya Gupta',
            'email': 'patient2@demo.com',
            'password': 'Patient@123',
            'phone': '+91 98765 43211',
            'age': 35,
            'gender': 'Female',
            'chronic_conditions': 'Asthma',
            'allergies': 'Penicillin'
        }
    ]

    for p in patients_data:
        p_hash = generate_password_hash(p['password'])
        u_id = database.insert(
            conn,
            """INSERT INTO users (name, email, password_hash, role, phone, is_verified)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (p['name'], p['email'], p_hash, 'patient', p['phone'], 1)
        )
        database.insert(
            conn,
            """INSERT INTO patient_profiles (user_id, age, gender, chronic_conditions, allergies)
               VALUES (?, ?, ?, ?, ?)""",
            (u_id, p['age'], p['gender'], p['chronic_conditions'], p['allergies'])
        )
        patient_count += 1

    # ---------------------------------------------------------
    # 3. Doctors (Active Demo Accounts with Login Credentials)
    # ---------------------------------------------------------
    login_doctors = [
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Amit Verma',
            'email': 'doctor@demo.com',
            'password': 'Doctor@123',
            'phone': '+91 98111 11001',
            'specialization': 'General Physician',
            'clinic': 'City Health Clinic',
            'address': '45 Rajpur Road',
            'city': 'Dehradun',
            'lat': 30.3165,
            'lng': 78.0322,
            'fee': 500.0,
            'experience': 12,
            'is_available': 1
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Sneha Patel',
            'email': 'doctor2@demo.com',
            'password': 'Doctor@123',
            'phone': '+91 98111 11002',
            'specialization': 'ENT Specialist',
            'clinic': 'Patel ENT Care',
            'address': '12 Haridwar Road',
            'city': 'Dehradun',
            'lat': 30.3255,
            'lng': 78.0420,
            'fee': 600.0,
            'experience': 8,
            'is_available': 1
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Rajesh Kumar',
            'email': 'doctor3@demo.com',
            'password': 'Doctor@123',
            'phone': '+91 98111 11003',
            'specialization': 'Pulmonologist',
            'clinic': 'Breathing Easy Clinic',
            'address': '78 Clock Tower',
            'city': 'Dehradun',
            'lat': 30.3190,
            'lng': 78.0380,
            'fee': 700.0,
            'experience': 15,
            'is_available': 1
        }
    ]

    for d in login_doctors:
        d_hash = generate_password_hash(d['password'])
        doc_uid = database.insert(
            conn,
            """INSERT INTO users (name, email, password_hash, role, phone, is_verified)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (d['name'], d['email'], d_hash, 'doctor', d['phone'], 1)
        )
        # -- DEMO DATA - FICTIONAL
        database.insert(
            conn,
            """INSERT INTO doctor_profiles (
                user_id, specialization, clinic_name, address, city,
                lat, lng, fee, experience_years, is_available,
                available_days, available_from, available_to
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_uid,
                d['specialization'],
                d['clinic'],
                d['address'],
                d['city'],
                d['lat'],
                d['lng'],
                d['fee'],
                d['experience'],
                d['is_available'],
                'Mon,Tue,Wed,Thu,Fri,Sat',
                '09:00',
                '17:00'
            )
        )
        doctor_count += 1

    # ---------------------------------------------------------
    # 4. Additional Doctor Directory (Fictional Demo Listings)
    # ---------------------------------------------------------
    directory_doctors = [
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Meera Singh',
            'email': 'doctor4@demo.com',
            'phone': '+91 98111 11004',
            'specialization': 'Pediatrician',
            'clinic': 'Child Care Clinic',
            'address': '15 EC Road',
            'city': 'Dehradun',
            'lat': 30.3100,
            'lng': 78.0280,
            'fee': 450.0,
            'experience': 10
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Arun Joshi',
            'email': 'doctor5@demo.com',
            'phone': '+91 98111 11005',
            'specialization': 'Dermatologist',
            'clinic': 'Dermal Care Center',
            'address': '88 Subhash Road',
            'city': 'Dehradun',
            'lat': 30.3220,
            'lng': 78.0450,
            'fee': 550.0,
            'experience': 7
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Kavita Rawat',
            'email': 'doctor6@demo.com',
            'phone': '+91 98111 11006',
            'specialization': 'Cardiologist',
            'clinic': 'Doon Heart Clinic',
            'address': '22 Chakrata Road',
            'city': 'Dehradun',
            'lat': 30.3300,
            'lng': 78.0500,
            'fee': 800.0,
            'experience': 20
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Suresh Negi',
            'email': 'doctor7@demo.com',
            'phone': '+91 98111 11007',
            'specialization': 'General Physician',
            'clinic': 'Negi Family Clinic',
            'address': '10 Saharanpur Road',
            'city': 'Dehradun',
            'lat': 30.3050,
            'lng': 78.0250,
            'fee': 400.0,
            'experience': 5
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Anita Bhatt',
            'email': 'doctor8@demo.com',
            'phone': '+91 98111 11008',
            'specialization': 'Neurologist',
            'clinic': 'Neuro Health Care',
            'address': '65 Gandhi Road',
            'city': 'Dehradun',
            'lat': 30.3280,
            'lng': 78.0350,
            'fee': 750.0,
            'experience': 18
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Vikram Chauhan',
            'email': 'doctor9@demo.com',
            'phone': '+91 98111 11009',
            'specialization': 'Orthopedic',
            'clinic': 'Chauhan Ortho Clinic',
            'address': '34 Ballupur Road',
            'city': 'Dehradun',
            'lat': 30.3120,
            'lng': 78.0480,
            'fee': 650.0,
            'experience': 14
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Pooja Sharma',
            'email': 'doctor10@demo.com',
            'phone': '+91 98111 11010',
            'specialization': 'Gastroenterologist',
            'clinic': 'Digestive Health Clinic',
            'address': '51 Kaulagarh Road',
            'city': 'Dehradun',
            'lat': 30.3200,
            'lng': 78.0300,
            'fee': 600.0,
            'experience': 9
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Ravi Thapa',
            'email': 'doctor11@demo.com',
            'phone': '+91 98111 11011',
            'specialization': 'General Physician',
            'clinic': 'Thapa Medical Care',
            'address': '9 Patel Nagar',
            'city': 'Dehradun',
            'lat': 30.3350,
            'lng': 78.0550,
            'fee': 350.0,
            'experience': 3
        },
        # -- DEMO DATA - FICTIONAL
        {
            'name': 'Dr. Deepa Kandari',
            'email': 'doctor12@demo.com',
            'phone': '+91 98111 11012',
            'specialization': 'Gynecologist',
            'clinic': 'Kandari Women Health',
            'address': '17 Astley Hall',
            'city': 'Dehradun',
            'lat': 30.3180,
            'lng': 78.0400,
            'fee': 700.0,
            'experience': 11
        }
    ]

    for d in directory_doctors:
        # Non-login doctors receive a secure random password hash
        random_pwd = secrets.token_urlsafe(24)
        d_hash = generate_password_hash(random_pwd)
        doc_uid = database.insert(
            conn,
            """INSERT INTO users (name, email, password_hash, role, phone, is_verified)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (d['name'], d['email'], d_hash, 'doctor', d['phone'], 1)
        )
        # -- DEMO DATA - FICTIONAL
        database.insert(
            conn,
            """INSERT INTO doctor_profiles (
                user_id, specialization, clinic_name, address, city,
                lat, lng, fee, experience_years, is_available,
                available_days, available_from, available_to
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                doc_uid,
                d['specialization'],
                d['clinic'],
                d['address'],
                d['city'],
                d['lat'],
                d['lng'],
                d['fee'],
                d['experience'],
                1,
                'Mon,Tue,Wed,Thu,Fri,Sat',
                '09:00',
                '17:00'
            )
        )
        doctor_count += 1

    # ---------------------------------------------------------
    # 5. Print Seeding Summary Report
    # ---------------------------------------------------------
    total_users = admin_count + patient_count + doctor_count
    print('\n' + '=' * 55)
    print('  Demo Database Seeding Summary')
    print('=' * 55)
    print(f'  Total Users Seeded:     {total_users}')
    print(f'    - Administrators:     {admin_count} (admin@demo.com / Admin@123)')
    print(f'    - Patients:           {patient_count} (patient@demo.com, patient2@demo.com)')
    print(f'    - Doctors Total:      {doctor_count}')
    print('      * Login Enabled:    3 (doctor@, doctor2@, doctor3@demo.com / Doctor@123)')
    print('      * Directory Only:   9 (Dehradun specialists, random credentials)')
    print(f'  Patient Profiles:       {patient_count}')
    print(f'  Doctor Profiles:        {doctor_count}')
    print('=' * 55 + '\n')


if __name__ == '__main__':
    """Allow executing seed.py directly from the terminal."""
    conn = database.get_connection()
    try:
        if not database.check_tables_exist(conn):
            print('  Tables not found. Initializing database schema...')
            database.init_db(conn)
        seed_database(conn)
    finally:
        database.close_connection(conn)
