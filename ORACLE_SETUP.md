# Oracle Database Configuration Guide (Optional)

This project is fully database-agnostic. While SQLite is used for zero-setup local development and PostgreSQL (Supabase) is used for cloud deployment, an **Oracle option** is provided in case your academic department or college lab requires Oracle Database.

---

## 1. Prerequisites
- Python 3.10+
- Install `python-oracledb` (thin mode requires no Oracle Client installation):
  ```bash
  pip install oracledb
  ```

---

## 2. Configuration Settings (.env)
Set the following variables in your `.env` file:
```ini
# Oracle Database Credentials
ORACLE_USER=system
ORACLE_PASSWORD=your_oracle_password
ORACLE_DSN=localhost:1521/XEPDB1

# Optional: Directory path if connecting to Oracle Autonomous Database via Cloud Wallet
ORACLE_WALLET_DIR=
```

---

## 3. Database Schema & PL/SQL Setup
Run the following scripts in SQL*Plus, SQL Developer, or Oracle APEX:
1. **Schema DDL:** Run `database/schema.oracle.sql` to create all tables with Oracle datatypes (`NUMBER`, `VARCHAR2`, `CLOB`, `TIMESTAMP`, and `GENERATED ALWAYS AS IDENTITY`).
2. **PL/SQL Triggers:** Run `database/oracle_extras.sql` to install triggers that automatically update the `updated_at` column when records in `assessments` or `consultations` are modified.

---

## 4. How `backend/db.py` Handles Oracle Transparently
- **Placeholder Conversion:** Translates standard `?` parameter placeholders to Oracle bind variables (`:1, :2, :3, ...`).
- **Primary Keys:** Uses `RETURNING id INTO :out_id` to retrieve newly created IDs on insert.
- **Health Check:** Automatically runs `SELECT 1 FROM dual` when Oracle mode is active.

---

## 5. Free-Tier Cloud Idle Stop Mitigation
Oracle Cloud Free Tier Autonomous Databases enter an idle stopped state if unused for 7 consecutive days. 
- You can configure a free daily cron ping (e.g. via cron-job.org or GitHub Actions) targeting `GET /api/health` to keep the database active and prevent it from being paused before project review.
