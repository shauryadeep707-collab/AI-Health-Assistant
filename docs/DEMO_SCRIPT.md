# 5-Minute Practical Project Demonstration Script
## "AI Health Assistant – Smart Healthcare & Doctor Connect"

**Total Duration:** 5 Minutes  
**Target Audience:** Project Guide, External Examiners, Viva Panel

---

### Step 1: Introduction & App Initialization (0:00 - 0:45)
- **Speaker:** *"Good morning respected examiners. Our final-year project is 'AI Health Assistant – Smart Healthcare & Doctor Connect'. It bridges the gap between confusing web searches for common symptoms and consulting a verified local doctor."*
- **Action:** Open terminal and run:
  ```bash
  python run.py
  ```
- **Show on Screen:** Notice that SQLite tables and demo doctors in Dehradun are initialized automatically. Open browser to `http://localhost:5000`. Show the landing page with the medical disclaimer and PWA install prompt.

---

### Step 2: Scenario (A) – Mild Cold (Low Risk & Self-Care) (0:45 - 2:00)
- **Speaker:** *"First, let's log in as our demo patient Rahul Sharma."*
- **Action:**
  1. Click **Login** $\rightarrow$ Click **👤 Patient (Rahul)** $\rightarrow$ Click **Sign In**.
  2. On Patient Dashboard, click **Check Symptoms Now**.
  3. In the chat, type: `"I have a mild runny nose and sneezing since yesterday"`.
  4. Notice the AI responds with contextual follow-up questions and quick-reply chips.
  5. Select chips: `"1-2 days"` $\rightarrow$ `"Mild"` $\rightarrow$ `"Staying the same"` $\rightarrow$ `"No fever"` $\rightarrow$ `"None"`.
  6. The chat completes and redirects to `result.html`.
- **Show on Screen:**
  - **Green Low Risk Badge** (Score 0/10).
  - Home-Care Guidance Accordion (Self-care tips, warning signs to watch for).
  - Controlled Over-The-Counter (OTC) medicine cards (Paracetamol, Saline drops) clearly displaying *"Not a prescription - For general information only"*.

---

### Step 3: Scenario (B) – Persistent Fever (Medium Risk & Doctor Connect) (2:00 - 3:45)
- **Speaker:** *"Now let's test a case where symptoms are worsening over 4 days, requiring medical evaluation."*
- **Action:**
  1. Click **+ New Check** or return to chat.
  2. Type: `"I have a high fever that has been getting worse for 4 days"`.
  3. Answer follow-up chips: `"4-7 days"` $\rightarrow$ `"Moderate"` $\rightarrow$ `"Getting worse"` $\rightarrow$ `"101-103°F"`.
  4. The assessment completes and classifies the risk as **Medium Risk (Score 4/10)**.
  5. Click **👨‍⚕️ View Nearby Available Doctors**.
  6. Point out the Leaflet OpenStreetMap view of Dehradun and the sorted doctor cards showing Haversine distances (e.g. 1.2 km away).
  7. Click **Request Consultation** for *Dr. Amit Verma*.
  8. Check the mandatory consent box: *"I consent to share my AI symptom assessment summary with this doctor"*. Click **Confirm & Send Request**.
- **Demonstrating Doctor Portal & FIFO Queue:**
  1. Log out $\rightarrow$ Log in as **👨‍⚕️ Doctor (Dr. Amit)** (`doctor@demo.com`).
  2. Show Doctor Dashboard: Notice the in-app notification bell shows an unread alert.
  3. Show the **FIFO Patient Request Queue** with Rahul's case at the top.
  4. Click **Review Case & Advice**.
  5. Show the **<120-word AI summary**, verified consent timestamp, and collapsible chat transcript.
  6. Click **Accept Case**, type clinical advice: `"Take Paracetamol 500mg SOS, drink ORS electrolytes, and visit clinic if temperature exceeds 102F."`
  7. Click **Complete Consultation & Send Advice**.
  8. Log back in as Rahul: Show the patient sees the doctor's verified advice directly on their dashboard!

---

### Step 4: Scenario (C) & (D) – Red Flag Emergency Override (3:45 - 4:45)
- **Speaker:** *"Now we demonstrate the most critical clinical safety feature: Deterministic Emergency Red Flag Override."*
- **Action:**
  1. Start a new symptom check as a patient.
  2. Type in Hindi/Hinglish: `"mujhe seene mein dard aur saans lene mein takleef ho rahi hai"` *(chest pain and breathing difficulty)*.
  3. **Show Instant Result:** WITHOUT asking any follow-up questions, the system halts conversation immediately and displays the full-width **Urgent Emergency Screen**.
  4. Point out the prominent red emergency buttons:
     - `📞 Call National Emergency (112)`
     - `🚑 Call Ambulance (108)`
  5. Note that no medication is recommended.
  6. Explain that `redflags.js` ensures this emergency override works **even if the user is 100% offline with no internet**.

---

### Step 5: Summary & Viva Conclusion (4:45 - 5:00)
- **Speaker:** *"To conclude, our project demonstrates a complete full-stack AI healthcare triage architecture: deterministic safety guards, conversational AI with demo mode fallback, geolocation discovery, an idempotent offline outbox queue, and end-to-end doctor consultations. Thank you, and we welcome your questions."*
