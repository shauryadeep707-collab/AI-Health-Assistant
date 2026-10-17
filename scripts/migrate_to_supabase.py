"""
Supabase Migration & Data Population Script.
Connects to Supabase PostgreSQL, creates all tables, seeds admin, patient accounts,
doctors, and migrates the complete OTC medicine catalog from knowledge_base/medicines.json.
"""

import os
import sys
import json
import psycopg2
from werkzeug.security import generate_password_hash

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

SUPABASE_URI = "postgresql://postgres.fpoyfurmqvmqxzpqwszu:HealthProject%402026@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

def run_migration():
    print("=" * 60)
    print("  [>] Starting Migration to Supabase PostgreSQL")
    print("=" * 60)

    # 1. Connect
    print("1. Connecting to Supabase...")
    conn = psycopg2.connect(SUPABASE_URI)
    conn.autocommit = True
    cur = conn.cursor()
    print("   [+] Connected successfully to Supabase!")

    # 2. Run Schema
    print("\n2. Applying PostgreSQL schema (tables, constraints, indexes)...")
    schema_path = os.path.join(BASE_DIR, 'database', 'schema.postgres.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()

    # Execute schema statements
    cur.execute(schema_sql)
    print("   [+] Schema applied successfully!")

    # 3. Check existing users to avoid duplicates
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]

    if user_count == 0:
        print("\n3. Seeding Users (Admin, Patients, Doctors)...")
        # Admin
        admin_hash = generate_password_hash('Admin@123')
        cur.execute(
            """INSERT INTO users (name, email, password_hash, role, phone, is_verified)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
            ('Admin User', 'admin@demo.com', admin_hash, 'admin', '+91 98000 00001', 1)
        )
        admin_id = cur.fetchone()[0]

        # Patients
        patients = [
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
                'allergies': 'Penicillin, Sulfa drugs'
            }
        ]

        for p in patients:
            p_hash = generate_password_hash(p['password'])
            cur.execute(
                """INSERT INTO users (name, email, password_hash, role, phone, is_verified)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (p['name'], p['email'], p_hash, 'patient', p['phone'], 1)
            )
            pid = cur.fetchone()[0]
            cur.execute(
                """INSERT INTO patient_profiles (user_id, age, gender, chronic_conditions, allergies)
                   VALUES (%s, %s, %s, %s, %s)""",
                (pid, p['age'], p['gender'], p['chronic_conditions'], p['allergies'])
            )

        # 12 Doctors
        doctors_data = [
            {'name': 'Dr. Amit Verma', 'email': 'doctor@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11001', 'specialization': 'General Physician', 'clinic': 'City Health Clinic', 'address': '45 Rajpur Road', 'city': 'Dehradun', 'lat': 30.3165, 'lng': 78.0322, 'fee': 500.0, 'experience': 12, 'is_available': 1},
            {'name': 'Dr. Sneha Patel', 'email': 'doctor2@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11002', 'specialization': 'ENT Specialist', 'clinic': 'Patel ENT Care', 'address': '12 Haridwar Road', 'city': 'Dehradun', 'lat': 30.3255, 'lng': 78.0420, 'fee': 600.0, 'experience': 8, 'is_available': 1},
            {'name': 'Dr. Rajesh Kumar', 'email': 'doctor3@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11003', 'specialization': 'Pulmonologist', 'clinic': 'Breathing Easy Clinic', 'address': '78 Clock Tower', 'city': 'Dehradun', 'lat': 30.3190, 'lng': 78.0380, 'fee': 700.0, 'experience': 15, 'is_available': 1},
            {'name': 'Dr. Meera Singh', 'email': 'doctor4@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11004', 'specialization': 'Pediatrician', 'clinic': 'Child Care Clinic', 'address': '15 EC Road', 'city': 'Dehradun', 'lat': 30.3100, 'lng': 78.0280, 'fee': 450.0, 'experience': 10, 'is_available': 1},
            {'name': 'Dr. Arun Joshi', 'email': 'doctor5@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11005', 'specialization': 'Dermatologist', 'clinic': 'Dermal Care Center', 'address': '88 Subhash Road', 'city': 'Dehradun', 'lat': 30.3220, 'lng': 78.0450, 'fee': 550.0, 'experience': 7, 'is_available': 1},
            {'name': 'Dr. Kavita Rawat', 'email': 'doctor6@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11006', 'specialization': 'Cardiologist', 'clinic': 'Doon Heart Clinic', 'address': '22 Chakrata Road', 'city': 'Dehradun', 'lat': 30.3300, 'lng': 78.0500, 'fee': 800.0, 'experience': 20, 'is_available': 1},
            {'name': 'Dr. Suresh Negi', 'email': 'doctor7@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11007', 'specialization': 'General Physician', 'clinic': 'Negi Family Clinic', 'address': '10 Saharanpur Road', 'city': 'Dehradun', 'lat': 30.3050, 'lng': 78.0250, 'fee': 400.0, 'experience': 5, 'is_available': 1},
            {'name': 'Dr. Anita Bhatt', 'email': 'doctor8@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11008', 'specialization': 'Neurologist', 'clinic': 'Neuro Health Care', 'address': '65 Gandhi Road', 'city': 'Dehradun', 'lat': 30.3280, 'lng': 78.0350, 'fee': 750.0, 'experience': 18, 'is_available': 1},
            {'name': 'Dr. Vikram Chauhan', 'email': 'doctor9@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11009', 'specialization': 'Orthopedic', 'clinic': 'Chauhan Ortho Clinic', 'address': '34 Ballupur Road', 'city': 'Dehradun', 'lat': 30.3120, 'lng': 78.0480, 'fee': 650.0, 'experience': 14, 'is_available': 1},
            {'name': 'Dr. Pooja Sharma', 'email': 'doctor10@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11010', 'specialization': 'Gastroenterologist', 'clinic': 'Digestive Health Clinic', 'address': '51 Kaulagarh Road', 'city': 'Dehradun', 'lat': 30.3200, 'lng': 78.0300, 'fee': 600.0, 'experience': 9, 'is_available': 1},
            {'name': 'Dr. Ravi Thapa', 'email': 'doctor11@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11011', 'specialization': 'General Physician', 'clinic': 'Thapa Medical Care', 'address': '9 Patel Nagar', 'city': 'Dehradun', 'lat': 30.3350, 'lng': 78.0550, 'fee': 350.0, 'experience': 3, 'is_available': 1},
            {'name': 'Dr. Deepa Kandari', 'email': 'doctor12@demo.com', 'password': 'Doctor@123', 'phone': '+91 98111 11012', 'specialization': 'Gynecologist', 'clinic': 'Kandari Women Health', 'address': '17 Astley Hall', 'city': 'Dehradun', 'lat': 30.3210, 'lng': 78.0390, 'fee': 700.0, 'experience': 11, 'is_available': 1}
        ]

        for d in doctors_data:
            doc_hash = generate_password_hash(d.get('password', 'Doctor@123'))
            cur.execute(
                """INSERT INTO users (name, email, password_hash, role, phone, is_verified)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (d['name'], d['email'], doc_hash, 'doctor', d['phone'], 1)
            )
            did = cur.fetchone()[0]
            cur.execute(
                """INSERT INTO doctor_profiles (
                    user_id, specialization, clinic_name, address, city,
                    lat, lng, fee, experience_years, is_available,
                    available_days, available_from, available_to
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                (
                    did, d['specialization'], d['clinic'], d['address'], d['city'],
                    d['lat'], d['lng'], d['fee'], d['experience'],
                    1 if d['is_available'] else 0,
                    'Mon,Tue,Wed,Thu,Fri,Sat',
                    '09:00',
                    '17:00'
                )
            )
        print("   [+] Seeded 1 Admin, 2 Patients, and 12 Doctors into Supabase!")
    else:
        print(f"\n3. Users table already has {user_count} records. Skipping user seeding.")

    # 4. Migrate Medicine Data from medicines.json
    print("\n4. Migrating OTC Medicine Knowledge Base to Supabase...")
    meds_path = os.path.join(BASE_DIR, 'knowledge_base', 'medicines.json')
    cur.execute("SELECT COUNT(*) FROM medicines")
    meds_count = cur.fetchone()[0]

    if meds_count == 0 and os.path.exists(meds_path):
        with open(meds_path, 'r', encoding='utf-8') as f:
            meds_data = json.load(f)

        categories = meds_data.get('categories', {})
        total_meds = 0

        for cat_name, med_list in categories.items():
            for m in med_list:
                precautions_str = json.dumps(m.get('precautions', []))
                avoid_if_str = json.dumps(m.get('avoid_if', []))
                
                cur.execute(
                    """INSERT INTO medicines (category, name, purpose, general_info, precautions, avoid_if, safety_note)
                       VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                    (
                        cat_name,
                        m.get('name', 'Unknown'),
                        m.get('purpose', ''),
                        m.get('general_info', ''),
                        precautions_str,
                        avoid_if_str,
                        m.get('note', '')
                    )
                )
                total_meds += 1

        print(f"   [+] Successfully inserted {total_meds} OTC medicine records into Supabase!")
    else:
        print(f"   [*] Medicines table already contains {meds_count} items.")

    # 5. Summary verification
    print("\n" + "=" * 60)
    print("  [#] SUPABASE DATABASE STATUS REPORT")
    print("=" * 60)
    for table in ['users', 'patient_profiles', 'doctor_profiles', 'medicines']:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  * {table:20}: {count} rows")
    print("=" * 60)

    cur.close()
    conn.close()
    print("[SUCCESS] All patient details and medicine data successfully live in Supabase!")

if __name__ == '__main__':
    run_migration()
