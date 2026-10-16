-- AI Health Assistant - Oracle Schema
-- All tables for the health assistant application
-- Oracle uses NUMBER, VARCHAR2, CLOB, TIMESTAMP, GENERATED ALWAYS AS IDENTITY, NUMBER(1) for booleans

CREATE TABLE users (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR2(255) NOT NULL,
    email VARCHAR2(255) NOT NULL UNIQUE,
    password_hash VARCHAR2(255) NOT NULL,
    role VARCHAR2(20) NOT NULL CHECK (role IN ('patient', 'doctor', 'admin')),
    phone VARCHAR2(50),
    is_verified NUMBER(1) DEFAULT 0 CHECK (is_verified IN (0, 1, 2)), -- 0=pending, 1=approved, 2=rejected (for doctors)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patient_profiles (
    user_id NUMBER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    age NUMBER(3),
    gender VARCHAR2(50),
    chronic_conditions CLOB,
    allergies CLOB
);

CREATE TABLE doctor_profiles (
    user_id NUMBER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    specialization VARCHAR2(255) DEFAULT 'General Physician',
    clinic_name VARCHAR2(255),
    address VARCHAR2(500),
    city VARCHAR2(100),
    lat NUMBER(10, 6),
    lng NUMBER(10, 6),
    fee NUMBER(10, 2),
    experience_years NUMBER,
    is_available NUMBER(1) DEFAULT 1 CHECK (is_available IN (0, 1)),
    available_days VARCHAR2(100) DEFAULT 'Mon,Tue,Wed,Thu,Fri',
    available_from VARCHAR2(20) DEFAULT '09:00',
    available_to VARCHAR2(20) DEFAULT '17:00'
);

CREATE TABLE assessments (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id VARCHAR2(255) UNIQUE,
    patient_id NUMBER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR2(20) DEFAULT 'in_progress' CHECK (status IN ('in_progress', 'completed')),
    category VARCHAR2(100),
    structured_json CLOB,
    risk_level VARCHAR2(20) CHECK (risk_level IN ('low', 'medium', 'urgent')),
    risk_score NUMBER,
    risk_reasons CLOB,
    summary CLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id VARCHAR2(255) UNIQUE,
    assessment_id NUMBER NOT NULL REFERENCES assessments(id) ON DELETE CASCADE,
    role VARCHAR2(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content CLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE consultations (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    client_id VARCHAR2(255) UNIQUE,
    assessment_id NUMBER NOT NULL REFERENCES assessments(id),
    patient_id NUMBER NOT NULL REFERENCES users(id),
    doctor_id NUMBER NOT NULL REFERENCES users(id),
    status VARCHAR2(20) DEFAULT 'pending' CHECK (status IN ('pending', 'accepted', 'declined', 'completed')),
    consent_given NUMBER(1) DEFAULT 0 CHECK (consent_given IN (0, 1)),
    consent_at TIMESTAMP,
    doctor_advice CLOB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE notifications (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id NUMBER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text VARCHAR2(1000) NOT NULL,
    link VARCHAR2(500),
    is_read NUMBER(1) DEFAULT 0 CHECK (is_read IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE login_attempts (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    email VARCHAR2(255) NOT NULL,
    ip_address VARCHAR2(50),
    attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ai_usage (
    id NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id NUMBER NOT NULL REFERENCES users(id),
    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_doctor_available ON doctor_profiles(is_available, specialization);
CREATE INDEX idx_doctor_location ON doctor_profiles(lat, lng);
CREATE INDEX idx_consultation_doctor ON consultations(doctor_id, status, created_at);
CREATE INDEX idx_assessment_patient ON assessments(patient_id);
CREATE INDEX idx_notification_user ON notifications(user_id, is_read);
CREATE INDEX idx_login_attempts ON login_attempts(email, attempted_at);
CREATE INDEX idx_ai_usage ON ai_usage(user_id, used_at);
