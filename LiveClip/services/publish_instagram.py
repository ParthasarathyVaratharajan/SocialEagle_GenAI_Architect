import requests
from .utils import env

# Simplified flow: publish an already-hosted MP4 URL from Supabase Storage via signed URL
def get_public_url(storage_path: str) -> str:
    from supabase import create_client
    sb = create_client(env("SUPABASE_URL"), env("SUPABASE_KEY"))
    bucket = env("SUPABASE_BUCKET")
    signed = sb.storage.from_(bucket).create_signed_url(storage_path, 3600)
    return signed.get("signedURL")

def publish_instagram_reel(caption: str, video_url: str) -> dict:
    # Step 1: Create container
    user_id = env("IG_BUSINESS_ACCOUNT_ID")
    access_token = env("IG_ACCESS_TOKEN")
    create_url = f"https://graph.facebook.com/v19.0/{user_id}/media"
    payload = {
        "video_url": video_url,
        "caption": caption,
        "media_type": "REELS",
        "access_token": access_token
    }
    r = requests.post(create_url, data=payload)
    r.raise_for_status()
    container_id = r.json()["id"]

    # Step 2: Publish
    publish_url = f"https://graph.facebook.com/v19.0/{user_id}/media_publish"
    pr = requests.post(publish_url, data={"creation_id": container_id, "access_token": access_token})
    pr.raise_for_status()
    return pr.json()