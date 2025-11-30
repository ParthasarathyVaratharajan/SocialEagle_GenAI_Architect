from pathlib import Path
from supabase import create_client, Client
from .utils import env

def supabase_client() -> Client:
    return create_client(env("SUPABASE_URL"), env("SUPABASE_KEY"))

def upload_file(path: Path, dest_path: str) -> str:
    sb = supabase_client()
    bucket = env("SUPABASE_BUCKET")
    with open(path, "rb") as f:
        res = sb.storage.from_(bucket).upload(dest_path, f, {"contentType": "video/mp4", "upsert": True})
    if hasattr(res, "error") and res.error:
        raise RuntimeError(f"Upload error: {res.error}")
    return dest_path

def create_clip_record(source_url: str, duration: int, storage_path: str, platform_target: str, title: str, description: str):
    sb = supabase_client()
    data = {
        "source_url": source_url,
        "duration_seconds": duration,
        "storage_path": storage_path,
        "status": "pending",
        "platform_target": platform_target,
        "title": title,
        "description": description,
    }
    return sb.table("clips").insert(data).execute().data[0]

def update_clip_record(id: str, fields: dict):
    sb = supabase_client()
    return sb.table("clips").update(fields).eq("id", id).execute().data