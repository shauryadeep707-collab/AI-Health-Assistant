# Beginner's Setup Guide & Account Checkpoints

This guide explains how to run the project locally, and walks you through optional cloud deployments step-by-step.

---

## 1. Quick Local Setup (Zero-Configuration)

The project works completely out of the box on your local computer using **SQLite** and **Demo AI Mode** (no API keys, credit cards, or external services required).

### On Windows:
1. Double-click `start.bat` **OR** open PowerShell in this folder and run:
   ```powershell
   python run.py
   ```
2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```

### On Mac / Linux:
1. Open Terminal in this folder and run:
   ```bash
   bash start.sh
   # OR
   python3 run.py
   ```
2. Open your web browser to `http://localhost:5000`.

---

## 2. Interactive Setup Wizard
You can configure or test your settings at any time by running:
```bash
python scripts/setup_wizard.py
```
To verify that all required environment variables are set (without exposing any secrets), run:
```bash
python scripts/check_env.py
```

---

## 3. Account Checkpoints (Click-by-Click Cloud Guide)

Whenever you are ready to publish your project online or connect cloud databases, follow these numbered checkpoints.

---

### Checkpoint 1 (CP1): GitHub Repository
**Goal:** Host your source code in a private or public GitHub repository.

1. Open your browser and go to [github.com](https://github.com) and sign in.
2. Click the **+** icon in the top right $\rightarrow$ select **New repository**.
3. Set Repository name to: `AI-Health-Assistant`.
4. Choose **Public** or **Private**.
5. **Do NOT** check *"Add a README file"*, *"Add .gitignore"*, or *"Choose a license"* (we already created these).
6. Click the green **Create repository** button.
7. Open PowerShell/Terminal in the project directory and run the exact commands below:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: AI Health Assistant complete project"
   git branch -M main
   git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/AI-Health-Assistant.git
   git push -u origin main
   ```

---

### Checkpoint 2 (CP2): Supabase Cloud Database (PostgreSQL)
**Goal:** Connect a free cloud PostgreSQL database so data stays accessible even when your computer is off.

1. Open [supabase.com](https://supabase.com) and click **Start your project** (log in via GitHub).
2. Click **New project**.
3. Choose an organization $\rightarrow$ Enter Project Name: `ai-health-assistant`.
4. Generate or enter a strong **Database Password** (write it down in a safe note).
5. Choose Region: `South Asia (Mumbai)` or the region closest to you.
6. Click **Create new project** and wait ~2 minutes for initialization.
7. In the left sidebar, click the **Project Settings** (gear icon) $\rightarrow$ select **Database**.
8. Scroll down to **Connection parameters** / **Connection string**:
   - Choose the **URI** tab.
   - Select **Session** or **Transaction Pooler** (recommended for cloud servers).
   - Copy the connection string. It will look like:
     ```
     postgresql://postgres.[project-ref]:[YOUR-PASSWORD]@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
     ```
9. Open `.env` in this project folder and paste it into `DATABASE_URL`:
   ```ini
   DATABASE_URL=postgresql://postgres.xxx:YourActualPassword@aws-0-ap-south-1.pooler.supabase.com:6543/postgres
   ```
10. Initialize the cloud tables by running:
    ```bash
    python run.py
    ```
    The application will automatically detect PostgreSQL, create all tables, apply Row Level Security, and seed demo records.

---

### Checkpoint 3 (CP3): Cloud Deployment on Render
**Goal:** Host your working web app on the internet with a public HTTPS URL.

1. Go to [render.com](https://render.com) and sign up using your GitHub account.
2. Click **New +** $\rightarrow$ select **Web Service**.
3. Choose **Build and deploy from a Git repository** $\rightarrow$ select `AI-Health-Assistant`.
4. Configure the settings:
   - **Name:** `ai-health-assistant`
   - **Region:** Singapore / Frankfurt / Ohio
   - **Branch:** `main`
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python run.py`
5. Scroll down to **Environment Variables** $\rightarrow$ Click **Add Environment Variable**:
   - `SECRET_KEY`: (Enter a random 32-character string)
   - `AI_MODE`: `demo` (or `openai`)
   - `DATABASE_URL`: (Paste your Supabase connection string from CP2)
   - `PYTHONUNBUFFERED`: `1`
6. Click **Deploy Web Service**.
7. Wait 2–3 minutes until the status shows **Live** $\rightarrow$ Open the provided `.onrender.com` URL.
8. **Free Cloud Ping Setup:** Free instances on Render spin down after 15 minutes of inactivity. To keep it warm before your college demo:
   - Go to [cron-job.org](https://cron-job.org) (free).
   - Create a cron job that pings `https://your-app.onrender.com/api/health` every 10 minutes.

---

### Checkpoint 4 (CP4): OpenAI API Key (Optional)
**Goal:** Enable OpenAI GPT natural language processing instead of the offline demo engine.

1. Go to [platform.openai.com](https://platform.openai.com) and sign in.
2. Navigate to **API keys** $\rightarrow$ click **Create new secret key**.
3. Copy the secret key (`sk-...`).
4. Paste it into your `.env` file:
   ```ini
   AI_MODE=openai
   OPENAI_API_KEY=sk-your-key-here
   OPENAI_MODEL=gpt-3.5-turbo
   ```
5. Restart the server. The AI chat will now utilize OpenAI. *(Note: If your OpenAI account has zero credits, the app gracefully falls back to demo mode automatically without crashing).*

---

### Checkpoint 5 (CP5): Google Drive Automated Backups (Optional)
**Goal:** Automatically backup your SQLite database to a private Google Drive folder.

1. Go to [Google Cloud Console](https://console.cloud.google.com).
2. Create a project $\rightarrow$ Enable **Google Drive API**.
3. Go to **Credentials** $\rightarrow$ Create **Service Account** $\rightarrow$ Generate a **JSON Key**.
4. Download the JSON key file to a secure directory (e.g. `service_account.json`).
5. In Google Drive, create a folder named `HealthAssistantBackups` $\rightarrow$ Share it with the service account email (giving *Editor* permission).
6. Copy the Folder ID from the URL (the characters after `/folders/`).
7. In `.env`:
   ```ini
   GOOGLE_DRIVE_CREDENTIALS_PATH=C:\path\to\service_account.json
   GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
   ```
8. Run manual backup whenever desired:
   ```bash
   python -m backend.services.drive_backup
   ```
   The script keeps the last 7 backups and deletes older archives automatically.
