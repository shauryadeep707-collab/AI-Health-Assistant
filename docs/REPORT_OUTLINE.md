# BCA Final-Year Project Report Outline
## "AI Health Assistant – Smart Healthcare & Doctor Connect"

---

### CHAPTER 1: INTRODUCTION
1.1 Project Overview & Motivation  
1.2 Problem Statement (Challenges in self-triage & doctor accessibility)  
1.3 Proposed Solution & Innovation  
1.4 Project Objectives (Traceability to 10 core objectives)  
1.5 Scope and Limitations of the Study  
1.6 Report Organization  

---

### CHAPTER 2: LITERATURE SURVEY & THEORETICAL BACKGROUND
2.1 Review of Existing Health Portals & Symptom Checkers (WebMD, Ada, Babylon)  
2.2 Clinical Decision Support Systems (CDSS) & Safety Regulations (WHO, FDA)  
2.3 Conversational AI & Natural Language Processing in Healthcare  
2.4 Spatial Distance Metrics & Geolocation in Telehealth (Haversine Analysis)  
2.5 Offline-First Progressive Web Applications (PWA) in Low-Bandwidth Regions  

---

### CHAPTER 3: SYSTEM REQUIREMENTS SPECIFICATION (SRS)
3.1 User Personas & Stakeholders (Patient, Doctor, Administrator)  
3.2 Functional Requirements  
   - Conversational AI Symptom Intake  
   - Multi-Tiered Risk Engine (Safety Rules, Scoring, AI Opinion)  
   - Doctor Directory & Haversine Geolocation  
   - FIFO Consultation Workflow  
   - In-App Notifications & Offline Sync  
3.3 Non-Functional Requirements (Security, Performance, Privacy, Accessibility)  
3.4 Hardware and Software Environment Specifications  

---

### CHAPTER 4: SYSTEM DESIGN & ARCHITECTURE
4.1 High-Level Architecture Diagram (Client Tier, Application Tier, Database Tier)  
4.2 Data Flow Diagrams (DFD Level 0, Level 1, Level 2)  
4.3 UML Diagrams  
   - Use Case Diagram (Patient, Doctor, Admin interactions)  
   - Sequence Diagrams (Symptom Chat to Result; Consultation Lifecycle)  
   - Activity Diagram (Triage Escalation Decision Tree)  
   - Class / Module Relationship Diagram  
4.4 Database Design  
   - Entity-Relationship (ER) Diagram  
   - Data Dictionary & Schema Design (SQLite, PostgreSQL, Oracle)  
   - Database Indexing Strategy  

---

### CHAPTER 5: IMPLEMENTATION DETAILS
5.1 Technology Decisions (Python 3.10+, Flask, Vanilla JS, IndexedDB)  
5.2 Core Modules Implementation  
   - Deterministic Risk Engine (`risk_engine.py`)  
   - AI Service with Demo Fallback (`ai_service.py`)  
   - Clinical Summary Generator (`summary_service.py`)  
   - Database Abstraction Layer (`db.py`)  
   - Offline Outbox Queue & Service Worker (`offline.js`, `sw.js`)  
   - Doctor Geolocation Discovery (`location_service.py`, Leaflet Map)  
5.3 Security & Privacy Implementation  
   - CSRF Protection, Password Hashing, Rate Limiting, GDPR Account Deletion  
   - Hindi & Hinglish Emergency Phrase Detection  

---

### CHAPTER 6: TESTING & VERIFICATION
6.1 Testing Methodology & Test Plan  
6.2 Automated Unit Testing with Pytest (Risk Engine 12+ Cases)  
6.3 API Integration & Access Control Testing  
6.4 Offline Resilience & Idempotency Testing  
6.5 Manual Scenario Validation Results:  
   - **Scenario A:** Mild cold (1 day) $\rightarrow$ Low Risk + Guidance + Medicine Card  
   - **Scenario B:** Fever (4 days, worsening) $\rightarrow$ Medium Risk $\rightarrow$ Doctor Consultation $\rightarrow$ Doctor Advice received  
   - **Scenario C:** Chest pain & shortness of breath $\rightarrow$ Immediate Urgent Screen (Call 112/108)  
   - **Scenario D:** AI suggests Low but Red Flag exists $\rightarrow$ Urgent Override Verified  
   - **Scenario E:** No OpenAI API Key $\rightarrow$ Demo Mode End-to-End Verified  
   - **Scenario F:** Network Disconnect $\rightarrow$ Urgent Offline Screen & Outbox Sync Verified  

---

### CHAPTER 7: RESULTS & DISCUSSION
7.1 Evaluation of Objectives vs Implemented Features  
7.2 User Experience Analysis (Desktop vs Mobile Responsive View)  
7.3 System Performance & Low Latency Advantages of Vanilla Stack  

---

### CHAPTER 8: CONCLUSION & FUTURE SCOPE
8.1 Conclusion  
8.2 Key Academic Learnings  
8.3 Future Work:  
   - Machine Learning Risk Model trained on Clinical Datasets  
   - Regional Speech-to-Text & Voice Interaction  
   - Real-Time WebRTC Video Consultations  
   - Electronic Health Record (EHR) Integration  

---

### REFERENCES & BIBLIOGRAPHY
1. World Health Organization (WHO) – Ethics and Governance of AI for Health, 2021.  
2. US FDA – Clinical Decision Support Software Guidance for Industry, 2022.  
3. LeCun, Y., Bengio, Y., & Hinton, G. – "Deep Learning", Nature 521, 436–444, 2015.  
4. Pedregosa, F., et al. – "Scikit-learn: Machine Learning in Python", JMLR 12, 2011.  
5. Grinberg, M. – "Flask Web Development", O'Reilly Media, 2018.  
6. Mozilla Developer Network (MDN) – Service Worker API and IndexedDB Specifications.  
7. OpenAI – GPT-3.5 and Function Calling Technical Documentation, 2023.  
8. OpenStreetMap Foundation – Nominatim & Leaflet Geographic Mapping Documentation.  
