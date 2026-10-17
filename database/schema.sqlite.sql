-- AI Health Assistant - SQLite Schema
-- All tables for the health assistant application
-- SQLite uses INTEGER PRIMARY KEY AUTOINCREMENT, no row-level security

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('patient', 'doctor', 'admin')),
    phone TEXT,
    is_verified INTEGER DEFAULT 0,   -- 0=pending, 1=approved, 2=rejected (for doctors)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS patient_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    age INTEGER,
    gender TEXT,
    chronic_conditions TEXT,
    allergies TEXT
);

CREATE TABLE IF NOT EXISTS doctor_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    specialization TEXT DEFAULT 'General Physician',
    clinic_name TEXT,
    address TEXT,
    city TEXT,
    lat REAL,
    lng REAL,
    fee REAL,
    experience_years INTEGER,
    medical_degree TEXT DEFAULT 'MBBS',
    registration_number TEXT,
    medical_council TEXT DEFAULT 'State Medical Council',
    graduation_year INTEGER,
    medical_college TEXT,
    document_url TEXT,
    document_name TEXT,
    verification_notes TEXT,
    is_available INTEGER DEFAULT 1,
    available_days TEXT DEFAULT 'Mon,Tue,Wed,Thu,Fri',
    available_from TEXT DEFAULT '09:00',
    available_to TEXT DEFAULT '17:00'
);

CREATE TABLE IF NOT EXISTS assessments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT UNIQUE,
    patient_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status TEXT DEFAULT 'in_progress' CHECK(status IN ('in_progress', 'completed')),
    category TEXT,
    structured_json TEXT,
    risk_level TEXT CHECK(risk_level IN ('low', 'medium', 'urgent')),
    risk_score INTEGER,
    risk_reasons TEXT,
    summary TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT UNIQUE,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id TEXT UNIQUE,
    assessment_id INTEGER NOT NULL REFERENCES assessments(id),
    patient_id INTEGER NOT NULL REFERENCES users(id),
    doctor_id INTEGER NOT NULL REFERENCES users(id),
    status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'declined', 'completed')),
    consent_given INTEGER DEFAULT 0,
    consent_at TIMESTAMP,
    doctor_advice TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    link TEXT,
    is_read INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT NOT NULL,
    ip_address TEXT,
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ai_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS medicines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category TEXT NOT NULL,
    name TEXT NOT NULL,
    purpose TEXT,
    general_info TEXT,
    precautions TEXT,
    avoid_if TEXT,
    safety_note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_doctor_available ON doctor_profiles(is_available, specialization);
CREATE INDEX IF NOT EXISTS idx_doctor_location ON doctor_profiles(lat, lng);
CREATE INDEX IF NOT EXISTS idx_consultation_doctor ON consultations(doctor_id, status, created_at);
CREATE INDEX IF NOT EXISTS idx_assessment_patient ON assessments(patient_id);
CREATE INDEX IF NOT EXISTS idx_notification_user ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_login_attempts ON login_attempts(email, attempted_at);
CREATE INDEX IF NOT EXISTS idx_ai_usage ON ai_usage(user_id, used_at);
CREATE INDEX IF NOT EXISTS idx_medicines_category ON medicines(category);
