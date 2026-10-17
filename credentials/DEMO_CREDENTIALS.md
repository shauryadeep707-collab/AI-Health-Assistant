# 🔐 Demo Accounts & Credentials Directory
**Project:** AI Health Assistant – Smart Healthcare & Doctor Connect

This directory contains all default demonstration credentials, user account IDs, access levels, and references to where authentication data and passwords are created and stored in the source code.

---

## ⚡ Quick Login Cheat Sheet for Demonstrations & Viva

| Role | Name | Email / Login ID | Password | Access Portal URL |
| :--- | :--- | :--- | :--- | :--- |
| **Administrator** | Admin User | `admin@demo.com` | `Admin@123` | [`/pages/admin.html`](http://localhost:5000/pages/admin.html) |
| **Patient 1** | Rahul Sharma | `patient@demo.com` | `Patient@123` | [`/pages/login.html`](http://localhost:5000/pages/login.html) |
| **Patient 2** | Priya Gupta | `patient2@demo.com` | `Patient@123` | [`/pages/login.html`](http://localhost:5000/pages/login.html) |
| **Doctor 1** | Dr. Amit Verma | `doctor@demo.com` | `Doctor@123` | [`/pages/login.html`](http://localhost:5000/pages/login.html) |
| **Doctor 2** | Dr. Sneha Patel | `doctor2@demo.com` | `Doctor@123` | [`/pages/login.html`](http://localhost:5000/pages/login.html) |
| **Doctor 3** | Dr. Rajesh Kumar | `doctor3@demo.com` | `Doctor@123` | [`/pages/login.html`](http://localhost:5000/pages/login.html) |

---

## 📋 Complete Account Profiles & Permissions

### 1. 🛡️ Administrator Account
- **User ID:** `1`
- **Name:** Admin User
- **Email:** `admin@demo.com`
- **Password:** `Admin@123`
- **Phone:** `+91 98000 00001`
- **Role:** `admin`
- **Verification Status:** Approved (`is_verified = 1`)
- **Portal:** `/pages/admin.html`
- **What Can Be Done / Demonstrated:**
  1. **Registered Patients Directory:** View all patient profiles, ages, genders, chronic conditions, and allergy data.
  2. **Doctor Verification Console:** Review newly registered doctors with 1-click **Approve** or **Reject** licensing actions.
  3. **System Audits & Metrics:** Monitor total registered patients, verified doctors, active consultations, and assessments.
  4. **All Accounts Master List:** View all registered IDs across the platform.

---

### 2. 👤 Patient Accounts

#### Patient A (General demo patient):
- **User ID:** `2`
- **Name:** Rahul Sharma
- **Email:** `patient@demo.com`
- **Password:** `Patient@123`
- **Phone:** `+91 98765 43210`
- **Age / Gender:** 28 / Male
- **Chronic Conditions:** None
- **Allergies:** None
- **Portal:** `/pages/patient-dashboard.html`
- **Workflow:** Conversational symptom triage, self-care & low-risk OTC guidance, book consultations with nearby doctors.

#### Patient B (Patient with medical history):
- **User ID:** `3`
- **Name:** Priya Gupta
- **Email:** `patient2@demo.com`
- **Password:** `Patient@123`
- **Phone:** `+91 98765 43211`
- **Age / Gender:** 32 / Female
- **Chronic Conditions:** Mild Asthma
- **Allergies:** Sulfa drugs
- **Portal:** `/pages/patient-dashboard.html`

---

### 3. 🩺 Doctor Accounts (Login Enabled)

#### Doctor 1 (General Physician):
- **User ID:** `4`
- **Name:** Dr. Amit Verma
- **Email:** `doctor@demo.com`
- **Password:** `Doctor@123`
- **Phone:** `+91 98111 11001`
- **Role:** `doctor`
- **Specialization:** General Physician
- **Clinic:** Max Care Clinic, Rajpur Road, Dehradun
- **Experience / Fee:** 12 years / ₹500
- **Portal:** `/pages/doctor-dashboard.html`
- **Workflow:** Real-time FIFO queue, review AI-generated clinical summaries (<120 words), accept patient requests, enter clinical notes.

#### Doctor 2 (Cardiologist):
- **User ID:** `5`
- **Name:** Dr. Sneha Patel
- **Email:** `doctor2@demo.com`
- **Password:** `Doctor@123`
- **Phone:** `+91 98111 11002`
- **Specialization:** Cardiologist
- **Clinic:** Heart Care Centre, Astley Hall, Dehradun
- **Experience / Fee:** 15 years / ₹800
- **Portal:** `/pages/doctor-dashboard.html`

#### Doctor 3 (Pulmonologist):
- **User ID:** `6`
- **Name:** Dr. Rajesh Kumar
- **Email:** `doctor3@demo.com`
- **Password:** `Doctor@123`
- **Phone:** `+91 98111 11003`
- **Specialization:** Pulmonologist
- **Clinic:** Chest & Allergy Clinic, Ballupur, Dehradun
- **Experience / Fee:** 9 years / ₹600
- **Portal:** `/pages/doctor-dashboard.html`

---

## 📍 Where Passwords, IDs, and Accounts are Written in Code

If the examiner asks: *"Where are user credentials, passwords, and security controls defined in your codebase?"*, you can point directly to these files:

### 1. Initial Account Seed Data:
- **File:** [`database/seed.py`](file:///c:/Users/shaur/OneDrive/Desktop/bestproject/AI-Health-Assistant/database/seed.py)
  - **Lines 47–55:** Admin user creation (`admin@demo.com`, `Admin@123`).
  - **Lines 59–84:** Patient user accounts & profiles (`patient@demo.com`, `patient2@demo.com`).
  - **Lines 88–130:** Login-enabled doctor accounts (`doctor@demo.com`, `doctor2@demo.com`, `doctor3@demo.com`).
  - **Lines 133–250:** Dehradun specialist directory seeding (latitude, longitude, clinics, fees).

### 2. Password Hashing & Security Logic:
- **File:** [`backend/auth_utils.py`](file:///c:/Users/shaur/OneDrive/Desktop/bestproject/AI-Health-Assistant/backend/auth_utils.py)
  - Uses industry-standard `werkzeug.security.generate_password_hash` and `check_password_hash` (PBKDF2 SHA-256).
  - Raw passwords are **never** stored in plain text in the database.
  - Implements account lockout after 5 consecutive failed login attempts.

### 3. Authentication Routes & Session Management:
- **File:** [`backend/routes/auth.py`](file:///c:/Users/shaur/OneDrive/Desktop/bestproject/AI-Health-Assistant/backend/routes/auth.py)
  - **Line 26 (`/api/auth/register`):** Creates new accounts, hashes incoming passwords, provisions patient/doctor profiles.
  - **Line 81 (`/api/auth/login`):** Validates email, verifies password hash, and creates secure HTTP-only session cookie.
  - **Line 285 (`/api/admin/patients`):** Queries and returns patient profiles for the admin console.
  - **Line 303 (`/api/admin/users`):** Master query returning all user IDs, names, emails, roles, and registration timestamps.

### 4. Database Storage & Schema:
- **Database File:** `health_assistant.db` (SQLite local database)
- **Table Schema:** [`database/schema.sqlite.sql`](file:///c:/Users/shaur/OneDrive/Desktop/bestproject/AI-Health-Assistant/database/schema.sqlite.sql)
  - `users`: Stores `id`, `name`, `email`, `password_hash`, `role`, `phone`, `is_verified`, `created_at`.
  - `patient_profiles`: Stores `user_id` (foreign key to `users.id`), `age`, `gender`, `chronic_conditions`, `allergies`.
  - `doctor_profiles`: Stores `user_id`, `specialization`, `clinic_name`, `lat`, `lng`, `fee`, `experience_years`.

### 5. Frontend Login & Quick Demo Autofill:
- **File:** [`frontend/pages/login.html`](file:///c:/Users/shaur/OneDrive/Desktop/bestproject/AI-Health-Assistant/frontend/pages/login.html)
  - Includes quick demo buttons to autofill Admin, Doctor, or Patient credentials with one click.
- **File:** [`frontend/pages/admin.html`](file:///c:/Users/shaur/OneDrive/Desktop/bestproject/AI-Health-Assistant/frontend/pages/admin.html)
  - Admin audit dashboard to inspect all registered user IDs and patient medical profiles.

---

## 🔒 Security & Viva Defense Note
> **Why are passwords hashed?**  
> We use salted cryptographic hashing via Werkzeug (`scrypt` / `pbkdf2:sha256`). Even if an attacker accesses the `health_assistant.db` database file, the original passwords cannot be reversed or read in plain text.
