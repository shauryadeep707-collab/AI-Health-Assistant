# Production Deployment Guide: Render, Railway & Supabase

This guide details how to take the AI Health Assistant from your local machine to a production cloud deployment.

---

## 1. Architecture in Production

```
+-----------------------------------------------------------+
| User Browser (Mobile / Desktop)                           |
+-----------------------------------------------------------+
               | HTTPS
               v
+-----------------------------------------------------------+
| Render / Railway Web Service (Flask + Gunicorn)           |
| - Python 3.10+                                            |
| - Serves UI static files & API blueprints                 |
| - Stateless application worker                            |
+-----------------------------------------------------------+
               | Secure SSL PostgreSQL Connection
               v
+-----------------------------------------------------------+
| Supabase Cloud (AWS ap-south-1 / Mumbai)                  |
| - PostgreSQL 15+ Database                                 |
| - Row Level Security (RLS) enabled on all tables          |
| - Connection Pooling on port 6543                         |
+-----------------------------------------------------------+
```

---

## 2. Environment Variables Checklist

Set these on Render / Railway dashboard:

| Variable | Recommended Production Value | Description |
| :--- | :--- | :--- |
| `SECRET_KEY` | *(Generate via `python -c "import secrets; print(secrets.token_hex(32))"`)* | Cryptographic session encryption key |
| `DATABASE_URL` | `postgresql://postgres.[ref]:[pass]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres` | Supabase Transaction Pooler connection string |
| `AI_MODE` | `demo` *(or `openai` if key is funded)* | AI engine mode |
| `OPENAI_API_KEY` | `sk-...` *(optional)* | OpenAI API key |
| `OPENAI_MODEL` | `gpt-3.5-turbo` | OpenAI model identifier |
| `EMERGENCY_NUMBER`| `112` | National Emergency Helpline (India) |
| `AMBULANCE_NUMBER`| `108` | National Ambulance Service (India) |
| `PYTHONUNBUFFERED`| `1` | Forces real-time server logging |

---

## 3. Render Deployment Steps

1. **Link GitHub Repository:**
   - Sign in to [render.com](https://render.com) and click **New Web Service**.
   - Select your repository.
2. **Build & Start Commands:**
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run.py` (or `gunicorn -w 2 -b 0.0.0.0:$PORT backend.app:create_app()`)
3. **Configure Environment Variables:**
   - Add all variables from Section 2 above.
4. **Deploy:**
   - Click **Save Changes** and deploy.
   - Render automatically provisions a free SSL Certificate (`https://...`).

---

## 4. Keeping Free Cloud Instances Awake (/api/health)

Free-tier web services on Render and Railway enter an idle sleep state after 15 minutes of zero traffic. Waking them up can take 30–50 seconds.

### Free Automated Uptime Ping:
1. Register on [cron-job.org](https://cron-job.org) (free).
2. Create a new cron job:
   - **URL:** `https://your-service-name.onrender.com/api/health`
   - **Schedule:** Every 10 minutes (`*/10 * * * *`).
3. This ensures:
   - The web container remains warm and fast.
   - It executes `SELECT 1` on Supabase, preventing the free Supabase database from entering its 7-day idle pause.

---

## 5. Pre-Demo Checklist (Day Before Examination)

- [ ] **Test Demo Logins:**
  - Patient: `patient@demo.com` / `Patient@123`
  - Doctor: `doctor@demo.com` / `Doctor@123`
  - Admin: `admin@demo.com` / `Admin@123`
- [ ] **Check Database Status:** Open `https://your-app.onrender.com/api/health` and verify it returns `{"ok": true, "data": {"status": "healthy"}}`.
- [ ] **Verify Doctor Directory:** Open `/pages/doctors.html` and ensure the Leaflet map loads with Dehradun doctor markers.
- [ ] **Test Offline Mode:** Open Chrome DevTools $\rightarrow$ Network $\rightarrow$ Select **Offline** $\rightarrow$ Click through symptom check $\rightarrow$ Verify that the Urgent emergency screen still renders immediately.
