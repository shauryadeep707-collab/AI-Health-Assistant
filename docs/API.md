# AI Health Assistant – REST API Documentation

All responses follow the uniform format:
```json
{
  "ok": true,
  "data": { ... },
  "error": "Error message if ok is false"
}
```

---

## 1. Authentication & Profile

### `POST /api/auth/register`
Creates a new patient or doctor account.
- **Request Body (Patient):**
  ```json
  {
    "name": "Rahul Sharma",
    "email": "patient@demo.com",
    "password": "Password@123",
    "role": "patient",
    "phone": "+91 9876543210",
    "age": 28,
    "gender": "Male",
    "chronic_conditions": "None",
    "allergies": "None"
  }
  ```
- **Request Body (Doctor):**
  ```json
  {
    "name": "Dr. Sneha Patel",
    "email": "sneha@demo.com",
    "password": "Password@123",
    "role": "doctor",
    "specialization": "ENT Specialist",
    "clinic_name": "Patel ENT Clinic",
    "address": "12 Haridwar Road",
    "city": "Dehradun",
    "lat": 30.3255,
    "lng": 78.0420,
    "fee": 600,
    "experience_years": 8
  }
  ```
- **Response:** `201 Created`

### `POST /api/auth/login`
Authenticates a user and sets an HttpOnly cookie session.
- **Request Body:**
  ```json
  { "email": "patient@demo.com", "password": "Patient@123" }
  ```
- **Rate Limit:** Locked out for 5 minutes after 5 consecutive failures.

### `POST /api/auth/logout`
Terminates user session.

### `GET /api/auth/me` & `GET /api/profile`
Returns current user profile, role, and verification status.

### `PUT /api/profile`
Updates user profile fields.

### `DELETE /api/profile`
Permanently deletes user account, assessments, chat messages, and consultations (Privacy Right to be Forgotten).

---

## 2. Symptom Assessments

### `POST /api/assessments`
Initializes a new assessment session. Idempotent via `client_id`.
- **Request Body:**
  ```json
  { "client_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6" }
  ```

### `POST /api/assessments/<id>/message`
Submits patient symptoms and returns either an emergency triage result, the next conversational follow-up question, or a completion payload.
- **Request Body:**
  ```json
  {
    "content": "I have had a mild fever and cough for 2 days",
    "client_id": "msg-uuid-1234"
  }
  ```
- **Response (Follow-up):**
  ```json
  {
    "ok": true,
    "data": {
      "type": "followup",
      "message": "How would you rate the severity?",
      "chips": ["Mild", "Moderate", "Severe"],
      "progress": "Question 2 of ~6"
    }
  }
  ```
- **Response (Emergency Urgent Override):**
  ```json
  {
    "ok": true,
    "data": {
      "type": "urgent",
      "assessment_id": 1,
      "risk": { "level": "urgent", "score": 99 },
      "red_flags": [{ "id": "chest_pain", "name": "Chest Pain or Pressure" }]
    }
  }
  ```

### `GET /api/assessments/<id>`
Returns assessment results, clinical summary, risk breakdown, and full conversation history.

### `GET /api/assessments`
Lists all past assessments for the authenticated patient.

---

## 3. Doctors & Discovery

### `GET /api/doctors/nearby`
Finds practicing doctors within geographic radius, ordered by Haversine great-circle distance.
- **Query Parameters:**
  - `lat`: User latitude (e.g. `30.3165`)
  - `lng`: User longitude (e.g. `78.0322`)
  - `radius_km`: Search radius in kilometers (default: 50)
  - `specialization`: Optional filter (e.g. `ENT Specialist`)
  - `city`: Optional city filter (e.g. `Dehradun`)

### `PUT /api/doctor/availability`
Doctor dashboard toggle for immediate online availability.
- **Request Body:**
  ```json
  { "is_available": true }
  ```

---

## 4. Consultations & Triage Queue

### `POST /api/consultations`
Patient books a consultation with an available doctor.
- **Request Body:**
  ```json
  {
    "client_id": "consult-uuid-5678",
    "assessment_id": 1,
    "doctor_id": 4,
    "consent_given": true
  }
  ```

### `GET /api/consultations`
Role-aware consultation retrieval:
- **Doctor:** FIFO Queue (pending requests ordered oldest-first, then active/completed).
- **Patient:** Ordered newest to oldest.

### `GET /api/consultations/<id>`
Full case details including patient profile, AI summary, verified consent timestamp, and message transcript.

### `PUT /api/consultations/<id>/status`
Doctor accepts, declines, completes consultation, or adds medical advice.
- **Conflict Rule:** Status cannot move backwards (`completed` $\rightarrow$ `pending` returns HTTP 400).

---

## 5. In-App Notifications

### `GET /api/notifications`
Polls recent notifications for the logged-in user.

### `POST /api/notifications/<id>/read`
Marks a specific notification as read.

---

## 6. Health & Knowledge Base

### `GET /api/health`
Executes `SELECT 1` on the active database engine (SQLite, PostgreSQL, or Oracle).
- **Response:**
  ```json
  {
    "ok": true,
    "data": { "status": "healthy", "db": "sqlite", "ai_mode": "demo" }
  }
  ```

### `GET /api/guidance/<category>`
Returns home self-care instructions, warning signs, and escalation thresholds.

### `GET /api/medicines/<category>`
Returns controlled OTC remedies with clear "Not a prescription" notices.

---

## 7. Administrator Endpoints

### `GET /api/admin/doctors`
Lists doctor registrations and license approval status.

### `PUT /api/admin/doctors/<id>/verify`
Approves (`status: 1`) or rejects (`status: 2`) a doctor profile.

### `GET /api/admin/stats`
Summary analytics for patients, doctors, pending verifications, and consultations.
