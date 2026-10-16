# AI Health Assistant – Architecture & Technical Design

## 1. System Architecture Overview

The application follows an **Offline-First, Lightweight Tiered Architecture** designed for high reliability, explainability, and speed:

```mermaid
flowchart TD
    subgraph Client ["Client Browser (PWA)"]
        UI[Vanilla HTML5 / CSS3 / JS]
        SW[sw.js - Service Worker Cache]
        RF[redflags.js - Instant Offline Triage]
        IDB[(IndexedDB Outbox Queue)]
    end

    subgraph Server ["Flask Backend Server"]
        App[app.py & auth_utils.py]
        Routes[API Route Blueprints]
        RiskEng[Deterministic Risk Engine]
        AISvc[AI Service: OpenAI / Demo Fallback]
        SummSvc[Clinical Summary Service]
        LocSvc[Haversine Location Service]
        NotifSvc[Notification Service]
        DBLayer[db.py Unified DB Abstraction]
    end

    subgraph Data ["Database Tier"]
        SQLite[(SQLite local)]
        Postgres[(Supabase PostgreSQL)]
        Oracle[(Oracle Database)]
    end

    UI --> SW
    UI --> RF
    UI --> IDB
    UI -- "REST API (Fetch with CSRF)" --> App
    IDB -- "FIFO Outbox Sync" --> App
    App --> Routes
    Routes --> RiskEng
    Routes --> AISvc
    Routes --> SummSvc
    Routes --> LocSvc
    Routes --> NotifSvc
    Routes --> DBLayer
    DBLayer --> SQLite
    DBLayer --> Postgres
    DBLayer --> Oracle
```

---

## 2. Key Architectural Decisions

### A. Simplicity & Explainability for BCA Viva
- **No Heavy Frameworks:** Built with Plain HTML5, Modern CSS3 variables, and Vanilla JavaScript. Any BCA evaluator can inspect the code without dealing with Webpack, Babel, Vite, or node_modules.
- **One Unified Server Command:** Flask directly serves static assets and API routes on `http://localhost:5000`.

### B. Two-Layer Safety Architecture
1. **Pre-AI Deterministic Safety Filter:** The raw user input is checked against regex and keyword rules in `redflags.js` (client-side) and `risk_engine.py` (server-side) **before** invoking the AI.
2. **AI Escalation Rule:** The AI can elevate risk level (e.g. Low to Medium), but **can never downgrade** a level determined by clinical safety rules.

### C. Database Agnostic Abstraction Layer (`backend/db.py`)
Routes and business logic write SQL using `?` placeholders. The abstraction layer dynamically:
- Converts `?` to `%s` for PostgreSQL or `:1, :2` for Oracle.
- Automatically handles row-to-dictionary conversion.
- Manages auto-increment keys across `lastrowid`, `RETURNING id`, and Oracle `RETURNING ... INTO`.

### D. Offline-First Resilience (IndexedDB Outbox)
All client state modifications (chat messages, consultation bookings, doctor status toggles) are assigned a unique UUID `client_id` and queued into an IndexedDB FIFO outbox.
- When connection is restored, items are flushed oldest-first.
- All backend endpoints are **idempotent**, ensuring retries never produce duplicate entries.

---

## 3. Data Flow

```mermaid
sequenceDiagram
    autonumber
    actor Patient
    participant Browser as Browser (PWA)
    participant Server as Flask Server
    participant Risk as Risk Engine
    participant Doctor as Doctor Portal

    Patient->>Browser: Describes symptoms
    Browser->>Browser: Check client red flags (Instant triage)
    Browser->>Server: POST /api/assessments/<id>/message
    Server->>Risk: Check red flags on raw text
    alt Red Flag Triggered
        Risk-->>Server: Immediate URGENT
        Server-->>Browser: Direct to Call 112/108 Screen
    else Normal Progression
        Server-->>Browser: Conversational follow-up question
        Browser->>Patient: Displays prompt + quick-reply chips
        Note over Patient,Browser: Q&A repeats (max 6 questions)
        Browser->>Server: Final response submitted
        Server->>Risk: Compute score + AI opinion
        Server-->>Browser: Low / Medium Result
    end

    opt Medium Risk
        Patient->>Browser: Request consultation with Consent
        Browser->>Server: POST /api/consultations
        Server->>Doctor: Enqueue request in FIFO queue + In-app notification
        Doctor->>Server: Accept case & write clinical advice
        Server-->>Patient: In-app notification: Advice received!
    end
```
