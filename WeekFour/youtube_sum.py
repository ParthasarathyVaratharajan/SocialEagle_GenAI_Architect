import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="YouTube Video Summarizer",
    page_icon="🎥",
    layout="wide"
)

# Initialize session state
if 'summary' not in st.session_state:
    st.session_state.summary = None
if 'transcript' not in st.session_state:
    st.session_state.transcript = None
if 'video_info' not in st.session_state:
    st.session_state.video_info = None

def extract_video_id(url):
    """Extract video ID from YouTube URL"""
    patterns = [
        r'(?:youtube\.com\/watch\?v=)([^&]+)',
        r'(?:youtu\.be\/)([^?]+)',
        r'(?:youtube\.com\/embed\/)([^?]+)',
        r'(?:youtube\.com\/v\/)([^?]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id):
    """Fetch transcript from YouTube video"""
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = " ".join([item['text'] for item in transcript_list])
        return transcript, None
    except TranscriptsDisabled:
        return None, "Transcripts are disabled for this video"
    except NoTranscriptFound:
        return None, "No transcript found for this video"
    except Exception as e:
        return None, f"Error fetching transcript: {str(e)}"

def generate_summary(transcript, summary_type, api_key, model_name):
    """Generate summary using LangChain and OpenAI"""
    try:
        llm = ChatOpenAI(
            model=model_name,
            temperature=0.3,
            api_key=api_key
        )
        
        if summary_type == "Brief Summary":
            template = """You are a professional content summarizer. Provide a concise summary of the following YouTube video transcript.

Transcript:
{transcript}

Create a brief summary (3-5 sentences) that captures the main points and key takeaways of the video."""

        elif summary_type == "Detailed Summary":
            template = """You are a professional content summarizer. Provide a comprehensive summary of the following YouTube video transcript.

Transcript:
{transcript}

Create a detailed summary that includes:
1. Main topic and purpose
2. Key points discussed (with bullet points)
3. Important details and examples
4. Conclusion or final thoughts"""

        elif summary_type == "Key Points":
            template = """You are a professional content summarizer. Extract and list the key points from the following YouTube video transcript.

Transcript:
{transcript}

List the main key points in bullet format. Be specific and concise. Include 5-10 key points."""

        elif summary_type == "Chapter Breakdown":
            template = """You are a professional content summarizer. Create a chapter breakdown of the following YouTube video transcript.

Transcript:
{transcript}

Create a chapter breakdown with:
- Chapter titles
- Time estimates for each section
- Brief description of what's covered in each chapter
Format as a structured outline."""

        else:  # Action Items
            template = """You are a professional content summarizer. Extract actionable insights from the following YouTube video transcript.

Transcript:
{transcript}

Identify and list:
1. Key action items or recommendations
2. Practical tips mentioned
3. Steps to implement ideas discussed
Format as clear, actionable bullet points."""

        prompt = ChatPromptTemplate.from_template(template)
        chain = prompt | llm
        
        response = chain.invoke({"transcript": transcript})
        return response.content, None
        
    except Exception as e:
        return None, f"Error generating summary: {str(e)}"

# Title and description
st.title("🎥 YouTube Video Summarizer")
st.markdown("Get AI-powered summaries of YouTube videos in seconds")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter your OpenAI API key"
    )
    
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key
        st.success("✅ API Key configured!")
    else:
        st.warning("⚠️ Please enter your OpenAI API key")
    
    st.divider()
    
    model_name = st.selectbox(
        "Select Model",
        ["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"],
        index=1,
        help="Choose the OpenAI model for summarization"
    )
    
    summary_type = st.selectbox(
        "Summary Type",
        ["Brief Summary", "Detailed Summary", "Key Points", "Chapter Breakdown", "Action Items"],
        help="Choose the type of summary you want"
    )
    
    st.divider()
    
    if st.session_state.summary:
        if st.button("🔄 New Video", use_container_width=True):
            st.session_state.summary = None
            st.session_state.transcript = None
            st.session_state.video_info = None
            st.rerun()

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    st.header("📹 Video Input")
    
    video_url = st.text_input(
        "YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=...",
        help="Paste the YouTube video URL here"
    )
    
    # Display video preview
    if video_url:
        video_id = extract_video_id(video_url)
        if video_id:
            st.video(video_url)
            st.session_state.video_info = {"id": video_id, "url": video_url}
        else:
            st.error("❌ Invalid YouTube URL. Please check and try again.")

with col2:
    st.header("🚀 Actions")
    
    if st.button("Generate Summary", type="primary", use_container_width=True, disabled=not video_url):
        if not api_key:
            st.error("❌ Please enter your OpenAI API key in the sidebar")
        elif not video_url:
            st.error("❌ Please enter a YouTube video URL")
        else:
            video_id = extract_video_id(video_url)
            if not video_id:
                st.error("❌ Invalid YouTube URL")
            else:
                # Step 1: Fetch transcript
                with st.spinner("📝 Fetching video transcript..."):
                    transcript, error = get_transcript(video_id)
                    
                    if error:
                        st.error(f"❌ {error}")
                    else:
                        st.session_state.transcript = transcript
                        st.success("✅ Transcript fetched successfully!")
                        
                        # Step 2: Generate summary
                        with st.spinner(f"🤖 Generating {summary_type.lower()}..."):
                            summary, error = generate_summary(
                                transcript,
                                summary_type,
                                api_key,
                                model_name
                            )
                            
                            if error:
                                st.error(f"❌ {error}")
                            else:
                                st.session_state.summary = summary
                                st.success("✅ Summary generated!")
                                st.rerun()
    
    if st.session_state.transcript:
        st.metric("Transcript Length", f"{len(st.session_state.transcript.split())} words")
        
        with st.expander("📄 View Full Transcript"):
            st.text_area(
                "Full Transcript",
                value=st.session_state.transcript,
                height=300,
                key="transcript_view"
            )

# Display summary
if st.session_state.summary:
    st.divider()
    st.header("📊 Summary Results")
    
    # Summary type badge
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.info(f"**Summary Type:** {summary_type}")
    with col2:
        st.info(f"**Model:** {model_name}")
    with col3:
        timestamp = datetime.now().strftime("%H:%M:%S")
        st.info(f"**Generated:** {timestamp}")
    
    # Display summary
    st.markdown("### Summary")
    st.markdown(st.session_state.summary)
    
    # Action buttons
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📥 Download Summary",
            data=st.session_state.summary,
            file_name=f"youtube_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col2:
        st.download_button(
            label="📥 Download Transcript",
            data=st.session_state.transcript,
            file_name=f"youtube_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )
    
    with col3:
        # Create full report
        report = f"""YouTube Video Summary Report
{'=' * 50}

Video URL: {st.session_state.video_info['url']}
Summary Type: {summary_type}
Model Used: {model_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 50}
SUMMARY
{'=' * 50}

{st.session_state.summary}

{'=' * 50}
FULL TRANSCRIPT
{'=' * 50}

{st.session_state.transcript}
"""
        
        st.download_button(
            label="📥 Download Full Report",
            data=report,
            file_name=f"youtube_full_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

# Information section
if not st.session_state.summary:
    st.divider()
    st.header("ℹ️ How to Use")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 1️⃣ Setup
        - Enter your OpenAI API key
        - Choose your preferred model
        - Select summary type
        """)
    
    with col2:
        st.markdown("""
        ### 2️⃣ Input
        - Paste YouTube video URL
        - Preview the video
        - Click "Generate Summary"
        """)
    
    with col3:
        st.markdown("""
        ### 3️⃣ Results
        - View AI-generated summary
        - Download summary/transcript
        - Generate new summaries
        """)
    
    st.info("💡 **Tip:** The video must have captions/subtitles enabled for transcription to work.")

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>⚠️ Note: This tool only works with videos that have transcripts/captions available</p>
    <p>Built with Streamlit, LangChain, OpenAI, and YouTube Transcript API</p>
</div>
""", unsafe_allow_html=True)