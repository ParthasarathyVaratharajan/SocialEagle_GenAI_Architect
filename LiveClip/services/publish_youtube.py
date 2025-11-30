import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from .utils import env

def youtube_client():
    creds = Credentials(
        token=None,
        refresh_token=env("YOUTUBE_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=env("YOUTUBE_CLIENT_ID"),
        client_secret=env("YOUTUBE_CLIENT_SECRET"),
        scopes=["https://www.googleapis.com/auth/youtube.upload"]
    )
    return build("youtube", "v3", credentials=creds)

def publish_youtube_shorts(file_path: str, title: str, description: str, tags=None, privacy_status="public"):
    youtube = youtube_client()
    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "22"  # People & Blogs (placeholder)
        },
        "status": {"privacyStatus": privacy_status},
    }
    # media upload
    from googleapiclient.http import MediaFileUpload
    media = MediaFileUpload(file_path, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    while response is None:
        status, response = request.next_chunk()
    return response