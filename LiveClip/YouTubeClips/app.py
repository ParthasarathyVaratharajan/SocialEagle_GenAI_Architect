import streamlit as st
import yt_dlp
from datetime import timedelta
import os
import tempfile
from supabase import create_client, Client
import uuid
from pathlib import Path
import time
import json

# YouTube API imports
try:
    from google_auth_oauthlib.flow import Flow
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False

# NEW: Import moviepy for video processing
MOVIEPY_AVAILABLE = False
MOVIEPY_ERROR = None

try:
    # Try new moviepy import structure (v2.x)
    from moviepy import VideoFileClip
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        # Try old moviepy import structure (v1.x)
        from moviepy.editor import VideoFileClip
        MOVIEPY_AVAILABLE = True
    except ImportError as e:
        MOVIEPY_ERROR = f"ImportError: {str(e)}"
    except Exception as e:
        MOVIEPY_ERROR = f"Exception: {str(e)}"
except Exception as e:
    MOVIEPY_ERROR = f"Exception: {str(e)}"

# Page configuration
st.set_page_config(
    page_title="YouTube Clip Publisher",
    page_icon="🎬",
    layout="wide"
)

SUPABASE_URL="https://zmayuqrdfavjihfjcgrg.supabase.co"
SUPABASE_KEY="sb_secret_aK49pK5Uh0ute8O1Qhj6KA_jcW0r4p4"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize session state
if 'clips' not in st.session_state:
    st.session_state.clips = []
if 'current_video_info' not in st.session_state:
    st.session_state.current_video_info = None
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()

def format_time(seconds):
    """Convert seconds to HH:MM:SS format"""
    return str(timedelta(seconds=int(seconds)))

def parse_time(time_str):
    """Convert HH:MM:SS or MM:SS to seconds"""
    try:
        parts = time_str.split(':')
        if len(parts) == 3:  # HH:MM:SS
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        elif len(parts) == 2:  # MM:SS
            return int(parts[0]) * 60 + int(parts[1])
        else:
            return int(parts[0])
    except:
        return 0

def get_video_info(youtube_url):
    """Get YouTube video metadata"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=False)
            return {
                'title': info.get('title', 'Unknown'),
                'duration': info.get('duration', 0),
                'thumbnail': info.get('thumbnail', ''),
                'video_id': info.get('id', ''),
                'url': youtube_url
            }
    except Exception as e:
        st.error(f"Error fetching video info: {str(e)}")
        return None

def get_youtube_embed_url(video_id, start_time, end_time):
    """Generate YouTube embed URL with start and end times"""
    return f"https://www.youtube.com/embed/{video_id}?start={start_time}&end={end_time}&autoplay=0"

def download_clip_moviepy(youtube_url, start_time, end_time, output_path, progress_callback=None):
    """Download and clip video using moviepy (no FFmpeg binary needed)"""
    
    if not MOVIEPY_AVAILABLE:
        st.error("MoviePy is not installed. Please run: pip install moviepy")
        return False
    
    temp_full_video = None
    video_clip = None
    final_clip = None
    
    try:
        # Import VideoFileClip with the correct import path
        try:
            from moviepy import VideoFileClip
        except ImportError:
            from moviepy.editor import VideoFileClip
        
        if progress_callback:
            progress_callback(5, "Initializing download...")
        
        # Step 1: Download full video using yt-dlp
        temp_full_video = os.path.join(st.session_state.temp_dir, f"temp_full_{uuid.uuid4()}.mp4")
        
        ydl_opts = {
            'format': 'best[ext=mp4][height<=720]/best[ext=mp4]/best',
            'outtmpl': temp_full_video,
            'quiet': True,
            'no_warnings': True,
        }
        
        if progress_callback:
            progress_callback(20, "Downloading video from YouTube...")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([youtube_url])
        
        # Check if file was downloaded
        if not os.path.exists(temp_full_video):
            for ext in ['.mp4', '.webm', '.mkv']:
                alt_path = temp_full_video.replace('.mp4', ext)
                if os.path.exists(alt_path):
                    temp_full_video = alt_path
                    break
        
        if not os.path.exists(temp_full_video):
            raise Exception("Failed to download video from YouTube")
        
        if progress_callback:
            progress_callback(50, "Video downloaded. Processing clip...")
        
        # Step 2: Load video with moviepy
        video_clip = VideoFileClip(temp_full_video)
        
        if progress_callback:
            progress_callback(60, "Extracting clip segment...")
        
        # Step 3: Extract the clip (handle both v1.x and v2.x)
        try:
            # Try moviepy 2.x method
            final_clip = video_clip.subclipped(start_time, end_time)
        except AttributeError:
            # Fallback to moviepy 1.x method
            final_clip = video_clip.subclip(start_time, end_time)
        
        if progress_callback:
            progress_callback(75, "Encoding clip to MP4...")
        
        # Step 4: Write the clip to output file (moviepy 2.x compatible)
        final_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac'
        )
        
        if progress_callback:
            progress_callback(100, "Complete!")
        
        # Verify output file
        if os.path.exists(output_path):
            file_size = os.path.getsize(output_path)
            if file_size > 1000:
                return True
            else:
                raise Exception(f"Output file too small ({file_size} bytes)")
        else:
            raise Exception("Output file not created")
        
    except Exception as e:
        st.error(f"Error processing clip: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return False
    
    finally:
        # Cleanup: Close video clips and delete temp files
        try:
            if final_clip:
                final_clip.close()
            if video_clip:
                video_clip.close()
            if temp_full_video and os.path.exists(temp_full_video):
                os.remove(temp_full_video)
        except Exception as cleanup_error:
            st.warning(f"Cleanup warning: {cleanup_error}")

def save_clip_to_database(clip_data):
    """Save clip metadata to Supabase"""
    try:
        response = supabase.table('video_clips').insert({
            'id': clip_data['id'],
            'user_id': clip_data.get('user_id'),
            'youtube_url': clip_data['youtube_url'],
            'youtube_video_id': clip_data['youtube_video_id'],
            'start_time': clip_data['start_time'],
            'end_time': clip_data['end_time'],
            'duration': clip_data['duration'],
            'thumbnail_url': clip_data['thumbnail_url'],
            'title': clip_data['title'],
            'status': clip_data['status']
        }).execute()
        return response.data[0]['id'] if response.data else str(uuid.uuid4())
    except Exception as e:
        st.warning(f"Database save skipped: {str(e)}")
        return str(uuid.uuid4())

def update_clip_status(clip_id, status, video_file_path=None):
    """Update clip status in database"""
    try:
        update_data = {'status': status}
        if video_file_path:
            update_data['video_file_url'] = video_file_path
        response = supabase.table('video_clips').update(update_data).eq('id', clip_id).execute()
        return True
    except Exception as e:
        st.warning(f"Database update skipped: {str(e)}")
        return True

def authenticate_youtube():
    """Authenticate with YouTube using OAuth2"""
    try:
        if 'youtube_credentials' not in st.session_state:
            return None
        
        client_config = st.session_state.youtube_credentials
        
        # Check if we have saved credentials
        if 'youtube_token' in st.session_state:
            credentials = Credentials.from_authorized_user_info(
                st.session_state.youtube_token,
                scopes=['https://www.googleapis.com/auth/youtube.upload']
            )
            
            # Refresh if expired
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                st.session_state.youtube_token = json.loads(credentials.to_json())
            
            return credentials
        
        return None
        
    except Exception as e:
        st.error(f"YouTube authentication error: {str(e)}")
        return None

def start_youtube_oauth():
    """Start YouTube OAuth flow"""
    try:
        if 'youtube_credentials' not in st.session_state:
            st.error("Please upload client_secrets.json first")
            return
        
        client_config = st.session_state.youtube_credentials
        
        # Create flow
        flow = Flow.from_client_config(
            client_config,
            scopes=['https://www.googleapis.com/auth/youtube.upload'],
            redirect_uri='urn:ietf:wg:oauth:2.0:oob'
        )
        
        # Get authorization URL
        auth_url, _ = flow.authorization_url(prompt='consent')
        
        st.session_state.oauth_flow = flow
        st.session_state.oauth_url = auth_url
        
        return auth_url
        
    except Exception as e:
        st.error(f"OAuth setup error: {str(e)}")
        return None

def complete_youtube_oauth(auth_code):
    """Complete YouTube OAuth with authorization code"""
    try:
        if 'oauth_flow' not in st.session_state:
            st.error("OAuth flow not initialized")
            return False
        
        flow = st.session_state.oauth_flow
        flow.fetch_token(code=auth_code)
        
        credentials = flow.credentials
        st.session_state.youtube_token = json.loads(credentials.to_json())
        st.session_state.youtube_authenticated = True
        
        # Clean up
        del st.session_state.oauth_flow
        if 'oauth_url' in st.session_state:
            del st.session_state.oauth_url
        
        return True
        
    except Exception as e:
        st.error(f"OAuth completion error: {str(e)}")
        return False

def upload_to_youtube(video_path, title, description, tags=None):
    """Upload video to YouTube Shorts"""
    try:
        credentials = authenticate_youtube()
        if not credentials:
            st.error("Not authenticated with YouTube")
            return None
        
        # Build YouTube service
        youtube = build('youtube', 'v3', credentials=credentials)
        
        # Prepare video metadata
        body = {
            'snippet': {
                'title': title[:100],  # Max 100 characters
                'description': description,
                'tags': tags or ['shorts', 'clip'],
                'categoryId': '22'  # People & Blogs
            },
            'status': {
                'privacyStatus': 'public',
                'selfDeclaredMadeForKids': False,
                'madeForKids': False
            }
        }
        
        # Upload video
        media = MediaFileUpload(
            video_path,
            chunksize=1024*1024,  # 1MB chunks
            resumable=True,
            mimetype='video/mp4'
        )
        
        request = youtube.videos().insert(
            part='snippet,status',
            body=body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                st.progress(progress / 100, f"Uploading: {progress}%")
        
        video_id = response['id']
        return video_id
        
    except Exception as e:
        st.error(f"YouTube upload error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Header
st.title("🎬 YouTube Clip Publisher")
st.markdown("Capture and publish video clips to social media platforms")

# Check moviepy installation
if not MOVIEPY_AVAILABLE:
    st.error("⚠️ **MoviePy is required but not loading properly!**")
    if MOVIEPY_ERROR:
        st.error(f"Error: {MOVIEPY_ERROR}")
    st.code("pip install moviepy", language="bash")
    st.info("**Troubleshooting:**")
    st.markdown("""
    1. Make sure moviepy is installed in the correct Python environment
    2. Restart the Streamlit app completely (Ctrl+C and restart)
    3. Try: `pip uninstall moviepy` then `pip install moviepy`
    4. Check if you're using the correct Python/pip version
    """)
    
    # Show system info for debugging
    with st.expander("🔍 Debug Information"):
        import sys
        st.write(f"**Python Path:** {sys.executable}")
        st.write(f"**Python Version:** {sys.version}")
        st.write("**Installed Packages (moviepy related):**")
        try:
            import subprocess
            result = subprocess.run([sys.executable, "-m", "pip", "list"], 
                                  capture_output=True, text=True)
            lines = [line for line in result.stdout.split('\n') if 'movie' in line.lower() or 'imageio' in line.lower()]
            for line in lines:
                st.code(line)
        except:
            st.write("Could not list packages")
    
    st.stop()

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Settings")
    
    st.subheader("Social Media Accounts")
    
    # Connection status
    youtube_authenticated = st.session_state.get('youtube_authenticated', False)
    instagram_connected = 'instagram_token' in st.session_state
    facebook_connected = 'facebook_token' in st.session_state
    
    # YouTube Connection
    with st.expander("📺 YouTube Setup", expanded=not youtube_authenticated):
        if not YOUTUBE_API_AVAILABLE:
            st.error("YouTube API not installed!")
            st.code("pip install google-auth google-auth-oauthlib google-api-python-client")
        else:
            st.write("**Step 1: Upload OAuth Credentials**")
            st.caption("Get from Google Cloud Console → APIs & Services → Credentials")
            
            uploaded_file = st.file_uploader("Upload client_secrets.json", type=['json'], key="youtube_creds")
            if uploaded_file:
                try:
                    credentials = json.load(uploaded_file)
                    # Handle both formats
                    if 'web' in credentials:
                        st.session_state.youtube_credentials = credentials
                    elif 'installed' in credentials:
                        st.session_state.youtube_credentials = credentials
                    else:
                        st.session_state.youtube_credentials = {'installed': credentials}
                    st.success("✅ Credentials loaded!")
                except Exception as e:
                    st.error(f"Invalid JSON file: {str(e)}")
            
            if 'youtube_credentials' in st.session_state and not youtube_authenticated:
                st.write("**Step 2: Authenticate**")
                
                if 'oauth_url' not in st.session_state:
                    if st.button("🔐 Start Authentication", use_container_width=True):
                        auth_url = start_youtube_oauth()
                        if auth_url:
                            st.rerun()
                
                if 'oauth_url' in st.session_state:
                    st.info("Click the link below to authorize:")
                    st.markdown(f"[Authorize YouTube Access]({st.session_state.oauth_url})")
                    
                    auth_code = st.text_input("Paste authorization code here:", key="auth_code")
                    
                    if st.button("✅ Complete Authentication", use_container_width=True):
                        if auth_code:
                            if complete_youtube_oauth(auth_code):
                                st.success("🎉 YouTube authenticated!")
                                st.rerun()
                        else:
                            st.error("Please enter the authorization code")
            
            if youtube_authenticated:
                st.success("✅ YouTube Connected & Authenticated!")
                if st.button("Disconnect YouTube", use_container_width=True):
                    if 'youtube_credentials' in st.session_state:
                        del st.session_state.youtube_credentials
                    if 'youtube_token' in st.session_state:
                        del st.session_state.youtube_token
                    if 'youtube_authenticated' in st.session_state:
                        del st.session_state.youtube_authenticated
                    st.rerun()
    
    # Instagram Setup
    with st.expander("📸 Instagram Setup"):
        st.write("**Requires:** Instagram Business Account")
        st.write("**Get Token:** [Facebook Graph API Explorer](https://developers.facebook.com/tools/explorer/)")
        
        insta_token = st.text_input("Access Token", type="password", key="insta_token")
        insta_id = st.text_input("Account ID", key="insta_id")
        
        if insta_token and insta_id:
            st.session_state.instagram_token = insta_token
            st.session_state.instagram_id = insta_id
            st.success("✅ Instagram configured!")
    
    # Facebook Setup
    with st.expander("👥 Facebook Setup"):
        st.write("**Requires:** Facebook Page")
        st.write("**Get Token:** [Access Token Tool](https://developers.facebook.com/tools/accesstoken/)")
        
        fb_token = st.text_input("Page Access Token", type="password", key="fb_token")
        fb_id = st.text_input("Page ID", key="fb_id")
        
        if fb_token and fb_id:
            st.session_state.facebook_token = fb_token
            st.session_state.facebook_page_id = fb_id
            st.success("✅ Facebook configured!")
    
    st.divider()
    
    # Connection Summary
    st.subheader("Connection Status")
    st.write(f"📺 YouTube: {'✅ Connected' if youtube_authenticated else '❌ Not Connected'}")
    st.write(f"📸 Instagram: {'✅ Connected' if instagram_connected else '❌ Not Connected'}")
    st.write(f"👥 Facebook: {'✅ Connected' if facebook_connected else '❌ Not Connected'}")
    
    st.divider()
    
    st.subheader("Processing Status")
    st.success("✅ MoviePy: Ready")
    if YOUTUBE_API_AVAILABLE:
        st.success("✅ YouTube API: Ready")
    else:
        st.error("❌ YouTube API: Not Installed")
    
    st.divider()
    st.caption("💡 Need help? Check Google Cloud Console for setup")

# Main content
tab1, tab2, tab3 = st.tabs(["📹 Create Clip", "🖼️ Preview & Approve", "📤 Publish"])

with tab1:
    st.header("Create Clip Configuration")
    st.info("📝 Note: Video will NOT be downloaded yet. Only metadata is saved.")
    
    # YouTube URL input
    col1, col2 = st.columns([3, 1])
    with col1:
        youtube_url = st.text_input(
            "YouTube Video URL",
            placeholder="https://www.youtube.com/watch?v=...",
            help="Paste a YouTube video URL"
        )
    
    with col2:
        if st.button("Load Video", type="primary"):
            if youtube_url:
                with st.spinner("Loading video information..."):
                    video_info = get_video_info(youtube_url)
                    if video_info:
                        st.session_state.current_video_info = video_info
                        st.success("Video loaded successfully!")
            else:
                st.error("Please enter a YouTube URL")
    
    # Display video information
    if st.session_state.current_video_info:
        video_info = st.session_state.current_video_info
        
        st.divider()
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(video_info['thumbnail'], use_container_width=True)
        
        with col2:
            st.subheader(video_info['title'])
            st.write(f"**Duration:** {format_time(video_info['duration'])}")
            st.write(f"**Video ID:** {video_info['video_id']}")
        
        st.divider()
        
        # Time interval selection
        st.subheader("Select Clip Interval")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            start_time_str = st.text_input(
                "Start Time",
                value="00:00:00",
                help="Format: HH:MM:SS or MM:SS"
            )
        
        with col2:
            end_time_str = st.text_input(
                "End Time",
                value="00:01:00",
                help="Format: HH:MM:SS or MM:SS"
            )
        
        with col3:
            st.write("")
            st.write("")
            clip_duration = parse_time(end_time_str) - parse_time(start_time_str)
            st.metric("Clip Duration", f"{clip_duration}s")
        
        # Timeline slider
        st.subheader("Visual Timeline")
        time_range = st.slider(
            "Adjust clip range",
            0,
            int(video_info['duration']),
            (parse_time(start_time_str), parse_time(end_time_str)),
            format="%d seconds"
        )
        
        # Validation
        start_time = time_range[0]
        end_time = time_range[1]
        duration = end_time - start_time
        
        if duration < 3:
            st.warning("⚠️ Clip duration must be at least 3 seconds")
        elif duration > 60:
            st.warning("⚠️ Clip duration cannot exceed 60 seconds (platform limitation)")
        elif end_time > video_info['duration']:
            st.error("❌ End time exceeds video duration")
        else:
            st.success(f"✅ Valid clip duration: {duration} seconds")
        
        # Save button
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("💾 Save Clip Configuration", type="primary", use_container_width=True):
                if 3 <= duration <= 60 and end_time <= video_info['duration']:
                    clip_id = str(uuid.uuid4())
                    
                    clip_data = {
                        'id': clip_id,
                        'youtube_url': youtube_url,
                        'youtube_video_id': video_info['video_id'],
                        'title': video_info['title'],
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': duration,
                        'thumbnail_url': video_info['thumbnail'],
                        'status': 'draft',
                        'video_file_path': None,
                        'platforms': []
                    }
                    
                    st.session_state.clips.append(clip_data)
                    save_clip_to_database(clip_data)
                    
                    st.success(f"✅ Clip configuration saved! ID: {clip_id[:8]}...")
                    st.info("➡️ Go to 'Preview & Approve' tab to review and approve the clip")
                    st.balloons()
                else:
                    st.error("Please adjust the clip duration to be between 3-60 seconds")

with tab2:
    st.header("Preview & Approve Clips")
    
    draft_clips = [c for c in st.session_state.clips if c['status'] == 'draft']
    approved_clips = [c for c in st.session_state.clips if c['status'] == 'approved']
    
    if len(draft_clips) == 0 and len(approved_clips) == 0:
        st.info("📭 No clips waiting for approval. Create clips in the 'Create Clip' tab first!")
    else:
        if len(draft_clips) > 0:
            st.write(f"**{len(draft_clips)} clips waiting for your approval**")
            st.divider()
        
        for idx, clip in enumerate(draft_clips):
            with st.container():
                st.subheader(f"🎬 {clip['title']}")
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    embed_url = get_youtube_embed_url(
                        clip['youtube_video_id'],
                        clip['start_time'],
                        clip['end_time']
                    )
                    
                    st.markdown(f"""
                    <iframe width="100%" height="400" 
                    src="{embed_url}" 
                    frameborder="0" 
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" 
                    allowfullscreen>
                    </iframe>
                    """, unsafe_allow_html=True)
                    
                    st.caption(f"▶️ Preview: {format_time(clip['start_time'])} to {format_time(clip['end_time'])} ({clip['duration']}s)")
                
                with col2:
                    st.write("**Clip Details:**")
                    st.write(f"**ID:** {clip['id'][:16]}...")
                    st.write(f"**Duration:** {clip['duration']} seconds")
                    st.write(f"**Start:** {format_time(clip['start_time'])}")
                    st.write(f"**End:** {format_time(clip['end_time'])}")
                    st.write(f"**Status:** {clip['status'].upper()}")
                    
                    st.divider()
                    
                    if st.button("✅ Approve & Download Clip", key=f"approve_{idx}", type="primary", use_container_width=True):
                        output_file = os.path.join(st.session_state.temp_dir, f"clip_{clip['id']}.mp4")
                        
                        progress_placeholder = st.empty()
                        status_placeholder = st.empty()
                        
                        def update_progress(percent, message):
                            progress_placeholder.progress(percent / 100)
                            status_placeholder.info(f"⏳ {message}")
                        
                        success = download_clip_moviepy(
                            clip['youtube_url'],
                            clip['start_time'],
                            clip['end_time'],
                            output_file,
                            update_progress
                        )
                        
                        progress_placeholder.empty()
                        status_placeholder.empty()
                        
                        if success and os.path.exists(output_file):
                            file_size = os.path.getsize(output_file)
                            
                            if file_size > 1000:
                                for i, c in enumerate(st.session_state.clips):
                                    if c['id'] == clip['id']:
                                        st.session_state.clips[i]['status'] = 'approved'
                                        st.session_state.clips[i]['video_file_path'] = output_file
                                        break
                                
                                update_clip_status(clip['id'], 'approved', output_file)
                                
                                st.success(f"✅ Clip approved and downloaded! ({file_size / (1024*1024):.2f} MB)")
                                st.info("➡️ Go to 'Publish' tab to publish this clip")
                                
                                # ✅ Download button inside block
                                with open(output_file, 'rb') as f:
                                    st.download_button(
                                        "🧪 Test Download Video",
                                        f,
                                        file_name=f"test_clip_{clip['id'][:8]}.mp4",
                                        mime="video/mp4",
                                        key=f"test_download_{idx}_{clip['id']}"
                                    )
                                
                                st.rerun()
                            else:
                                st.error(f"❌ Downloaded file is too small ({file_size} bytes)")
                        else:
                            st.error("❌ Failed to download clip. Please try again.")
                    
                    if st.button("🗑️ Delete", key=f"delete_{idx}", use_container_width=True):
                        for i, c in enumerate(st.session_state.clips):
                            if c['id'] == clip['id']:
                                st.session_state.clips.pop(i)
                                break
                        st.success("Clip deleted!")
                        st.rerun()
        
        # ✅ Show already approved clips with persistent download button
        if len(approved_clips) > 0:
            st.write(f"**{len(approved_clips)} approved clips ready for publishing**")
            st.divider()
            
            for idx, clip in enumerate(approved_clips):
                st.subheader(f"🎬 {clip['title']} (Approved)")
                if clip.get('video_file_path') and os.path.exists(clip['video_file_path']):
                    with open(clip['video_file_path'], 'rb') as f:
                        st.download_button(
                            "⬇️ Download Approved Clip",
                            f,
                            file_name=f"approved_clip_{clip['id'][:8]}.mp4",
                            mime="video/mp4",
                            key=f"approved_download_{idx}_{clip['id']}"
                        )                 
with tab3:
    st.header("Publish Approved Clips")
    
    approved_clips = [c for c in st.session_state.clips if c['status'] == 'approved' and c.get('video_file_path')]
    
    if len(approved_clips) == 0:
        st.info("📭 No approved clips available for publishing. Approve clips in the 'Preview & Approve' tab first!")
    else:
        st.write(f"**{len(approved_clips)} approved clips ready for publishing**")
        
        clip_titles = [f"{c['title'][:40]}... ({c['duration']}s)" for c in approved_clips]
        selected_clip_idx = st.selectbox("Select clip to publish", range(len(approved_clips)), format_func=lambda x: clip_titles[x])
        
        selected_clip = approved_clips[selected_clip_idx]
        
        st.divider()
        
        # Video Preview Section
        st.subheader("📹 Video Preview")
        st.info("🎬 Watch the full clip before publishing to ensure it's perfect!")
        
        video_path = selected_clip.get('video_file_path')
        if video_path and os.path.exists(video_path):
            try:
                with open(video_path, 'rb') as video_file:
                    video_bytes = video_file.read()
                
                st.video(video_bytes, start_time=0)
                
                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    st.metric("Duration", f"{selected_clip['duration']}s")
                with col_info2:
                    st.metric("Start Time", format_time(selected_clip['start_time']))
                with col_info3:
                    st.metric("End Time", format_time(selected_clip['end_time']))
                
                col_dl1, col_dl2, col_dl3 = st.columns([1, 2, 1])
                with col_dl2:
                    st.download_button(
                        label="⬇️ Download Clip",
                        data=video_bytes,
                        file_name=f"clip_{selected_clip['id'][:8]}.mp4",
                        mime="video/mp4",
                        use_container_width=True
                    )
                
                st.success("✅ Video file ready for publishing")
                
                file_size_mb = len(video_bytes) / (1024 * 1024)
                st.caption(f"📊 File size: {file_size_mb:.2f} MB")
                
            except Exception as e:
                st.error(f"❌ Error loading video: {str(e)}")
                st.image(selected_clip['thumbnail_url'], use_container_width=True)
        else:
            st.image(selected_clip['thumbnail_url'], use_container_width=True)
            st.error("⚠️ Video file not found. Please re-approve the clip.")
        
        st.divider()
        
        # Publishing Options
        st.subheader("📤 Publishing Options")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.write("**Clip Information:**")
            st.write(f"**Title:** {selected_clip['title']}")
            st.write(f"**Video ID:** {selected_clip['youtube_video_id']}")
            st.write(f"**Source:** YouTube")
            
            st.divider()
            
            st.write("**Select Platforms:**")
            
            youtube_authenticated = st.session_state.get('youtube_authenticated', False)
            instagram_connected = 'instagram_token' in st.session_state
            facebook_connected = 'facebook_token' in st.session_state
            
            publish_youtube = st.checkbox("📺 YouTube Shorts", disabled=not youtube_authenticated, value=youtube_authenticated)
            publish_instagram = st.checkbox("📸 Instagram Reels", disabled=not instagram_connected)
            publish_facebook = st.checkbox("👥 Facebook Reels", disabled=not facebook_connected)
            
            if not (youtube_authenticated or instagram_connected or facebook_connected):
                st.warning("⚠️ Configure accounts in the sidebar first")
            
            # Show manual download option
            st.divider()
            st.write("**Manual Upload Option:**")
            
            if os.path.exists(selected_clip['video_file_path']):
                with open(selected_clip['video_file_path'], 'rb') as f:
                    if clip.get('video_file_path') and os.path.exists(clip['video_file_path']):
                       

                        with open(clip['video_file_path'], 'rb') as f:
                            st.download_button(
                                "⬇️ Download Approved Clip",
                                f,
                                file_name=f"approved_clip_{clip['id'][:8]}.mp4",
                                mime="video/mp4",
                                key=f"approved_download_{idx}_{clip['id']}_{uuid.uuid4()}"
                            )
                
                st.caption("Download and upload manually to any platform")
        
        with col2:
            st.write("**Caption / Description:**")
            caption = st.text_area(
                "Add a caption",
                placeholder="Write a catchy caption...\n\n#Shorts #Viral",
                height=150,
                label_visibility="collapsed"
            )
            
            if caption:
                st.caption(f"📝 {len(caption)} characters")
            
            with st.expander("💡 Suggested Hashtags"):
                st.write("#Shorts #Viral #Trending #VideoClip #ContentCreator")
        
        st.divider()
        
        platforms_selected = [
            p for p, selected in [
                ('YouTube Shorts', publish_youtube),
                ('Instagram Reels', publish_instagram),
                ('Facebook Reels', publish_facebook)
            ] if selected
        ]
        
        col_btn1, col_btn2, col_btn3 = st.columns([1, 2, 1])
        
        with col_btn2:
            if platforms_selected:
                st.write(f"**Ready to publish to:** {', '.join(platforms_selected)}")
            
            if st.button("🚀 Publish to Selected Platforms", type="primary", use_container_width=True, disabled=not platforms_selected):
                if not platforms_selected:
                    st.error("Please select at least one platform")
                else:
                    if not (selected_clip.get('video_file_path') and os.path.exists(selected_clip['video_file_path'])):
                        st.error("❌ Video file not available")
                    else:
                        # Publish to YouTube
                        if publish_youtube and st.session_state.get('youtube_authenticated'):
                            with st.spinner("📤 Publishing to YouTube Shorts..."):
                                video_id = upload_to_youtube(
                                    selected_clip['video_file_path'],
                                    selected_clip['title'],
                                    caption if caption else selected_clip['title']
                                )
                                
                                if video_id:
                                    st.success(f"✅ Published to YouTube Shorts!")
                                    st.info(f"**Video URL:** https://youtube.com/shorts/{video_id}")
                                    st.balloons()
                                    
                                    # Update clip status
                                    for idx, clip in enumerate(st.session_state.clips):
                                        if clip['id'] == selected_clip['id']:
                                            if 'platforms' not in st.session_state.clips[idx]:
                                                st.session_state.clips[idx]['platforms'] = []
                                            st.session_state.clips[idx]['platforms'].append('YouTube Shorts')
                                            st.session_state.clips[idx]['status'] = 'published'
                                            break
                                    
                                    update_clip_status(selected_clip['id'], 'published')
                                else:
                                    st.error("❌ Failed to publish to YouTube")
                        
                        # Publish to Instagram (placeholder)
                        if publish_instagram:
                            st.warning("Instagram publishing coming soon! Please use manual download for now.")
                        
                        # Publish to Facebook (placeholder)
                        if publish_facebook:
                            st.warning("Facebook publishing coming soon! Please use manual download for now.")
            
            if not platforms_selected:
                st.info("👆 Select at least one platform above")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>YouTube Clip Publisher v3.0 | Built with Streamlit + MoviePy</p>
    <p>✨ Workflow: Save Config → Preview → Approve & Download → Publish</p>
    <p>💡 No FFmpeg binary required - powered by MoviePy!</p>
</div>
""", unsafe_allow_html=True)