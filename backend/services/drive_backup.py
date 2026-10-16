"""
Google Drive Backup Service for AI Health Assistant.
Backs up the SQLite database or dumps data to a private Drive folder using a Service Account.
Keeps only the last 7 backups to save space.
NOTE: Google Drive is only a secondary backup, NEVER the live database.
"""

import os
import shutil
from datetime import datetime
from backend.config import config

def backup_local_database(dest_folder="backups"):
    """
    Creates a timestamped copy of the local SQLite database.
    """
    os.makedirs(dest_folder, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"health_assistant_backup_{timestamp}.db"
    dest_path = os.path.join(dest_folder, backup_filename)

    if os.path.exists(config.SQLITE_PATH):
        shutil.copy2(config.SQLITE_PATH, dest_path)
        print(f"Created local backup: {dest_path}")
        
        # Enforce last 7 backups limit
        backups = sorted([
            os.path.join(dest_folder, f) for f in os.listdir(dest_folder)
            if f.startswith("health_assistant_backup_") and f.endswith(".db")
        ])
        while len(backups) > 7:
            oldest = backups.pop(0)
            os.remove(oldest)
            print(f"Removed old backup: {oldest}")
            
        return dest_path
    else:
        print("No SQLite database found to backup.")
        return None

def upload_to_drive(file_path):
    """
    Uploads backup file to Google Drive using google-api-python-client if installed
    and GOOGLE_DRIVE_CREDENTIALS_PATH is configured.
    """
    creds_path = os.getenv("GOOGLE_DRIVE_CREDENTIALS_PATH")
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")

    if not creds_path or not os.path.exists(creds_path):
        print("Google Drive backup skipped: GOOGLE_DRIVE_CREDENTIALS_PATH not set or file not found.")
        return False

    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = service_account.Credentials.from_service_account_file(
            creds_path,
            scopes=['https://www.googleapis.com/auth/drive.file']
        )
        service = build('drive', 'v3', credentials=creds)

        file_metadata = {
            'name': os.path.basename(file_path),
            'parents': [folder_id] if folder_id else []
        }
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        print(f"Backup uploaded to Google Drive. File ID: {file.get('id')}")

        # List files in folder and prune if > 7
        if folder_id:
            query = f"'{folder_id}' in parents and trashed = false"
            results = service.files().list(q=query, orderBy='createdTime', fields='files(id, name)').execute()
            items = results.get('files', [])
            while len(items) > 7:
                oldest_file = items.pop(0)
                service.files().delete(fileId=oldest_file['id']).execute()
                print(f"Removed older drive backup: {oldest_file['name']}")

        return True
    except ImportError:
        print("google-api-python-client is not installed. To use Drive backup, install google-api-python-client google-auth.")
        return False
    except Exception as e:
        print(f"Drive backup error: {e}")
        return False

if __name__ == "__main__":
    local_file = backup_local_database()
    if local_file:
        upload_to_drive(local_file)
