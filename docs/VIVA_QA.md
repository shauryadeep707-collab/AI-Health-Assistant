# AI Health Assistant – 25 BCA Viva Questions & Answers

### 1. What problem does this project solve?
**Answer:** It addresses the confusion patients face when assessing mild to moderate symptoms (fever, cough, headache), preventing reliance on misleading web searches. It provides safe self-care guidance for low-risk cases, routes true emergencies immediately to 112/108, and provides a direct, pre-briefed connection to available local doctors for medium-risk conditions.

### 2. Why did you choose Flask instead of Django or FastAPI?
**Answer:** Flask is minimalist, unopinionated, and easy to explain. Unlike Django, it does not force an ORM or heavy scaffolding, making the database queries and request flow transparent for academic review.

### 3. Why did you use Vanilla JavaScript instead of React or Angular?
**Answer:** Modern browsers support standard DOM APIs and `fetch`. Avoiding front-end build tools (Vite, Webpack) eliminates dependency bloat and allows the entire project to run from a single command (`python run.py`), ensuring that examiners can evaluate the code without needing Node.js or `npm install`.

### 4. How does the hybrid Risk Engine work?
**Answer:** It combines three layers:
1. **Deterministic Red Flags:** Pre-screen raw text with keywords/regex for immediate emergencies (e.g., chest pain, breathing difficulty).
2. **Deterministic Weighted Scoring:** Calculates numerical scores based on duration (>3d, >7d), severity, worsening, fever temperature, age (<5, >60), and chronic conditions.
3. **AI Opinion:** Incorporates LLM classification, but strictly follows the safety rule that **AI can escalate risk, but can never downgrade a clinical rule result**.

### 5. Why is the AI never allowed to downgrade the risk level?
**Answer:** Clinical safety. Machine learning models can produce false negatives or hallucinate. A patient with severe symptoms or red flags must not be categorized as Low risk simply because an LLM parsed their wording passively.

### 6. Where is the FIFO Queue used in this project?
**Answer:** 
1. **Doctor's consultation queue:** Pending patient consultation requests are processed oldest-first (`created_at ASC`).
2. **In-app notifications:** Delivered and handled in order.
3. **Offline IndexedDB Outbox:** Enqueues offline writes and syncs them in FIFO order once reconnected.

### 7. How does the system achieve idempotent offline synchronization?
**Answer:** Each client-side write generates a UUID (`client_id`). The database enforces a `UNIQUE` constraint on `client_id`. If an offline outbox item is flushed multiple times due to network retries, the server identifies the duplicate and returns the existing record without duplicating entries.

### 8. What is the Haversine formula and why is it used?
**Answer:** The Haversine formula calculates the great-circle distance between two latitude and longitude points on the spherical surface of the Earth:
$$d = 2R \arcsin\left(\sqrt{\sin^2\left(\frac{\Delta \phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta \lambda}{2}\right)}\right)$$
It enables nearby doctor discovery without requiring external paid APIs.

### 9. How do you handle database neutrality without an ORM?
**Answer:** Through `backend/db.py`. It converts SQL `?` parameter placeholders dynamically to `%s` for PostgreSQL and `:1, :2` for Oracle, converts cursor tuples to uniform Python dictionaries, and handles key return differences (`lastrowid` vs `RETURNING id`).

### 10. How is patient data protected?
**Answer:** 
- Passwords hashed with PBKDF2/Werkzeug.
- HttpOnly, SameSite=Lax session cookies.
- CSRF token validation on all mutating API calls.
- Strict role-based access control preventing patients from accessing other patients' assessments.
- Patient consent checkbox required before sharing health summaries with doctors.
- GDPR "Right to be Forgotten" account and data deletion endpoint.

### 11. Does the app work without an OpenAI API key?
**Answer:** Yes. The application includes `AI_MODE=demo`, which utilizes medically scripted conversational follow-ups and deterministic extraction. If the OpenAI key is missing or fails, it switches to demo mode automatically.

### 12. How does the service worker enable offline usability?
**Answer:** `sw.js` caches the application shell (HTML, CSS, JS, emergency knowledge base). Even without internet access, patients can open the app, run the symptom checker (using `redflags.js`), and view emergency contact numbers (112 and 108).

### 13. How does the doctor consultation workflow work?
**Answer:** 
1. Medium risk assessment $\rightarrow$ patient chooses a doctor and provides consent.
2. Request enters doctor's FIFO pending queue (`status: pending`).
3. Doctor accepts the case (`status: accepted`), reviews the under-120-word AI summary and transcript.
4. Doctor writes advice and completes the consultation (`status: completed`).
5. Patient receives in-app notifications throughout each transition.

### 14. What happens if a doctor tries to change status from 'completed' back to 'pending'?
**Answer:** The request is rejected with HTTP 400. The system enforces unidirectional state transitions (`pending` $\rightarrow$ `accepted`/`declined` $\rightarrow$ `completed`). Status cannot move backwards.

### 15. How do you prevent brute force login attacks?
**Answer:** Rate limiting in `backend/auth_utils.py` tracks failed login attempts by email and IP address. More than 5 failed attempts locks the account for 5 minutes.

### 16. What is the daily AI call limit and why is it implemented?
**Answer:** A limit of 30 AI requests per user per day is tracked in the `ai_usage` table. This prevents API abuse and manages computational costs.

### 17. How does doctor licensing verification work?
**Answer:** Newly registered doctors have `is_verified = 0` (pending). An administrator must review their credentials via `/pages/admin.html` and approve them before they appear in nearby patient searches.

### 18. Why does the AI not generate medication dosages?
**Answer:** Safety regulations. AI models must never prescribe medications or advise specific dosages for children. All OTC medicine information is loaded strictly from a static, controlled JSON file (`medicines.json`) with clear non-prescription disclaimers.

### 19. How does Hinglish/Hindi detection work?
**Answer:** Emergency keywords and regex patterns in `knowledge_base/red_flags.json` and `frontend/js/redflags.js` include common colloquial Hindi phrases like *"seene mein dard"*, *"saans lene mein takleef"*, *"behosh"*, and *"khoon ki ulti"*.

### 20. How is the under-120-word doctor summary generated?
**Answer:** In OpenAI mode, an extraction prompt produces a concise clinical note. In Demo mode, `_template_summary()` aggregates demographics, chief complaints, duration, severity, vital signs, and risk factors into a concise clinical brief.

### 21. How do you prevent sensitive health data from leaking through Supabase?
**Answer:** In `schema.postgres.sql`, Row Level Security (RLS) is enabled on all tables with no public access policies. All access is handled through parameterized backend queries using direct PostgreSQL connections.

### 22. What database indexes did you create and why?
**Answer:**
- `doctor_profiles(is_available, specialization)`: Fast search filtering.
- `doctor_profiles(lat, lng)`: Efficient spatial lookups.
- `consultations(doctor_id, status, created_at)`: Optimized doctor FIFO queue retrieval.
- `assessments(patient_id)`: Quick patient history access.
- `notifications(user_id, is_read)`: Fast unread notification counts.

### 23. What is the difference between Low, Medium, and Urgent risk?
**Answer:**
- **Low (Score 0-2):** Mild, short duration, manageable via home self-care and controlled OTC guidance.
- **Medium (Score 3-5):** Persistent or worsening symptoms requiring consultation with an available doctor.
- **Urgent (Score $\ge$ 6 or Red Flag):** High-risk indicators requiring immediate emergency care (Call 112/108).

### 24. What are the limitations of this project?
**Answer:**
- Not an FDA/CDSCO approved medical diagnostic device.
- Chatbot relies on user self-reporting, which may omit critical clinical signs.
- Teleconsultation messaging is currently asynchronous rather than live WebRTC video.

### 25. What are the key future enhancements?
**Answer:**
- Training a custom clinical ML model on verified datasets (e.g. MIMIC-III).
- Voice speech-to-text integration for regional Indian dialects.
- WebRTC video teleconsultation directly between patient and doctor.
