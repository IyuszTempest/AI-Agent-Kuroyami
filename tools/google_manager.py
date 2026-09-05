import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import base64

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/presentations',
    'https://www.googleapis.com/auth/youtube.readonly'
]

def get_google_service(api_name, api_version):
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build(api_name, api_version, credentials=creds)

def handle_google_ecosystem(action: str, target: str = "") -> str:
    try:
        # --- 1. GMAIL ---
        if action == "gmail_read":
            service = get_google_service('gmail', 'v1')
            results = service.users().messages().list(userId='me', maxResults=5, q="is:unread").execute()
            messages = results.get('messages', [])
            if not messages:
                return "Tidak ada email baru yang belum dibaca."
            
            output = []
            for msg in messages:
                txt = service.users().messages().get(userId='me', id=msg['id']).execute()
                headers = txt['payload']['headers']
                subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
                sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown')
                output.append(f"- Dari: {sender} | Subjek: {subject}")
            return "Email Terbaru:\n" + "\n".join(output)

        # --- 2. GOOGLE DRIVE ---
        elif action == "gdrive_search":
            service = get_google_service('drive', 'v3')
            query = f"name contains '{target}' and trashed = false"
            results = service.files().list(q=query, pageSize=5, fields="files(id, name, webViewLink)").execute()
            items = results.get('files', [])
            if not items:
                return f"File '{target}' tidak ditemukan di Google Drive."
            
            output = [f"- {item['name']} ({item['webViewLink']})" for item in items]
            return "Hasil Pencarian Drive:\n" + "\n".join(output)

        elif action == "gdrive_upload":
            service = get_google_service('drive', 'v3')
            file_metadata = {'name': os.path.basename(target)}
            media = MediaFileUpload(target, resumable=True)
            file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
            return f"Berhasil upload ke Drive! Link: {file.get('webViewLink')}"

        # --- 3. GOOGLE TASKS ---
        elif action == "g_tasks_add":
            service = get_google_service('tasks', 'v1')
            task = {'title': target}
            result = service.tasks().insert(tasklist='@default', body=task).execute()
            return f"Berhasil menambah tugas: {result.get('title')}"
            
        elif action == "g_tasks_list":
            service = get_google_service('tasks', 'v1')
            results = service.tasks().list(tasklist='@default', maxResults=10).execute()
            items = results.get('items', [])
            if not items:
                return "Tidak ada tugas aktif."
            return "Daftar Google Tasks:\n" + "\n".join([f"- {i['title']}" for i in items])

        # --- 4. GOOGLE DOCS ---
        elif action == "gdocs_create":
            service = get_google_service('docs', 'v1')
            body = {'title': target}
            doc = service.documents().create(body=body).execute()
            return f"Berhasil membuat Google Doc baru! Judul: {doc.get('title')} (ID: {doc.get('documentId')})"

        # --- 5. GOOGLE SLIDES ---
        elif action == "gslides_create":
            service = get_google_service('slides', 'v1')
            body = {'title': target}
            presentation = service.presentations().create(body=body).execute()
            return f"Berhasil membuat Google Slides baru! Judul: {presentation.get('title')} (ID: {presentation.get('presentationId')})"

        # --- 6. YOUTUBE ---
        elif action == "youtube_search":
            service = get_google_service('youtube', 'v3')
            request = service.search().list(part="snippet", maxResults=3, q=target, type="video")
            response = request.execute()
            items = response.get('items', [])
            if not items:
                return f"Tidak ditemukan video YouTube untuk pencarian: {target}"
            
            output = []
            for item in items:
                title = item['snippet']['title']
                video_id = item['id']['videoId']
                output.append(f"- {title} (https://www.youtube.com/watch?v={video_id})")
            return "Hasil Pencarian YouTube:\n" + "\n".join(output)
            
        return f"Aksi Google '{action}' tidak dikenal."
    except Exception as e:
        return f"Gagal memproses ekosistem Google: {str(e)}"