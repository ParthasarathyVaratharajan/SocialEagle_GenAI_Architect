import os
import streamlit as st
import tempfile
from pathlib import Path
import subprocess

from services.capture import capture_clip
from services.storage import upload_file, create_clip_record, update_clip_record, supabase_client
from services.utils import env, timestamp_slug, vertical_filter
from services.publish_instagram import publish_instagram_reel, get_public_url
from services.publish_youtube import publish_youtube_shorts

FFMPEG = env("FFMPEG_PATH", "ffmpeg")
BUCKET = env("SUPABASE_BUCKET")

st.set_page_config(page_title="Live Clip Orchestrator", layout="wide")

tab1, tab2, tab3 = st.tabs(["Capture", "Review & Approve", "Publish"])

with tab1:
    st.header("Capture YouTube Live Clip")
    source_url = st.text_input("YouTube Live URL")
    duration = st.number_input("Duration (seconds)", min_value=10, max_value=90, value=30)
    platform_target = st.selectbox("Target platform", ["instagram", "youtube"])
    title = st.text_input("Title", value="Live highlight")
    description = st.text_area("Description", value="Captured highlight for reels/shorts")

    if st.button("Capture and Store"):
        try:
            st.info("Resolving stream and capturing…")
            raw_path = capture_clip(source_url, int(duration))
            st.success(f"Captured: {raw_path}")
            st.video(str(raw_path))

            # Create vertical version
            st.info("Converting to vertical 9:16…")
            tmpdir = Path(tempfile.mkdtemp())
            vertical_file = tmpdir / "vertical.mp4"
            vf = vertical_filter()
            cmd = [FFMPEG, "-y", "-i", str(raw_path), "-vf", vf, "-c:v", "libx264", "-preset", "fast", "-c:a", "aac", str(vertical_file)]
            subprocess.run(cmd, check=True)
            st.success(f"Vertical ready: {vertical_file}")
            st.video(str(vertical_file))

            # Upload both to Supabase
            sb_key = timestamp_slug()
            storage_path = f"clips/{sb_key}.mp4"
            vertical_path = f"clips/{sb_key}_vertical.mp4"

            st.info("Uploading to Supabase Storage…")
            upload_file(raw_path, storage_path)
            upload_file(vertical_file, vertical_path)

            # Metadata record
            st.info("Creating metadata record…")
            rec = create_clip_record(
                source_url=source_url,
                duration=int(duration),
                storage_path=storage_path,
                platform_target=platform_target,
                title=title,
                description=description
            )
            update_clip_record(rec["id"], {"vertical_path": vertical_path})
            st.success(f"Clip stored with ID: {rec['id']}")
            st.session_state["last_clip_id"] = rec["id"]

        except Exception as e:
            st.error(f"Capture/Store failed: {e}")

with tab2:
    st.header("Review & Approval")
    sb = supabase_client()
    status_filter = st.selectbox("Filter by status", ["pending", "approved", "rejected", "published", "failed"])
    resp = sb.table("clips").select("*").eq("status", status_filter).order("created_at", desc=True).execute()
    clips = resp.data or []

    if not clips:
        st.info("No clips in this status.")
    else:
        for clip in clips:
            with st.expander(f"{clip['id']} | {clip.get('title','')} | {clip['status']}"):
                st.write(f"Source: {clip['source_url']}")
                st.write(f"Duration: {clip['duration_seconds']}s")
                st.write(f"Target: {clip.get('platform_target')}")
                st.write(f"Created: {clip['created_at']}")
                if clip.get("vertical_path"):
                    from supabase import create_client
                    sb = create_client(env("SUPABASE_URL"), env("SUPABASE_KEY"))
                    signed = sb.storage.from_(BUCKET).create_signed_url(clip["vertical_path"], 600)
                    url = signed.get("signedURL")
                    if url:
                        st.video(url)

                colA, colB, colC = st.columns(3)
                with colA:
                    if st.button("Approve", key=f"approve_{clip['id']}"):
                        update_clip_record(clip["id"], {"status": "approved"})
                        st.success("Approved.")
                with colB:
                    if st.button("Reject", key=f"reject_{clip['id']}"):
                        update_clip_record(clip["id"], {"status": "rejected"})
                        st.warning("Rejected.")
                with colC:
                    if st.button("Mark Failed", key=f"failed_{clip['id']}"):
                        update_clip_record(clip["id"], {"status": "failed"})
                        st.error("Marked failed.")

with tab3:
    st.header("Publish Approved Clips")
    target_platform = st.selectbox("Platform", ["instagram", "youtube"])
    resp = supabase_client().table("clips").select("*").eq("status", "approved").eq("platform_target", target_platform).order("created_at", desc=True).execute()
    clips = resp.data or []
    if not clips:
        st.info("No approved clips for selected platform.")
    else:
        for clip in clips:
            with st.expander(f"Publish: {clip['id']} | {clip.get('title','')}"):
                st.write(f"Title: {clip.get('title')}")
                st.write(f"Desc: {clip.get('description')}")
                st.write(f"Vertical path: {clip.get('vertical_path')}")
                if target_platform == "instagram":
                    if st.button("Publish to Instagram", key=f"pub_ig_{clip['id']}"):
                        try:
                            signed_url = get_public_url(clip["vertical_path"])
                            res = publish_instagram_reel(
                                caption=clip.get("description") or clip.get("title") or "",
                                video_url=signed_url
                            )
                            update_clip_record(clip["id"], {"status": "published"})
                            st.success(f"Published to Instagram: {res}")
                        except Exception as e:
                            st.error(f"Instagram publish failed: {e}")
                else:
                    if st.button("Publish to YouTube Shorts", key=f"pub_yt_{clip['id']}"):
                        try:
                            # Download vertical file locally for upload
                            from supabase import create_client
                            sb = create_client(env("SUPABASE_URL"), env("SUPABASE_KEY"))
                            signed = sb.storage.from_(BUCKET).create_signed_url(clip["vertical_path"], 600)
                            url = signed.get("signedURL")

                            import requests, tempfile
                            dlpath = Path(tempfile.mkdtemp()) / "upload.mp4"
                            r = requests.get(url)
                            r.raise_for_status()
                            dlpath.write_bytes(r.content)

                            res = publish_youtube_shorts(
                                file_path=str(dlpath),
                                title=clip.get("title") or "Short highlight",
                                description=clip.get("description") or "",
                                tags=["shorts", "highlight"]
                            )
                            update_clip_record(clip["id"], {"status": "published"})
                            st.success(f"Published to YouTube: {res.get('id')}")
                        except Exception as e:
                            st.error(f"YouTube publish failed: {e}")