import streamlit as st
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
import json
import os
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="Mock Interview AI",
    page_icon="🎤",
    layout="wide"
)

# Initialize session state
if 'interview_started' not in st.session_state:
    st.session_state.interview_started = False
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'current_question' not in st.session_state:
    st.session_state.current_question = 0
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'feedback' not in st.session_state:
    st.session_state.feedback = {}
if 'interview_complete' not in st.session_state:
    st.session_state.interview_complete = False

# Title
st.title("🎤 Mock Interview AI")
st.markdown("Practice your interview skills with AI-generated questions tailored to your job role")

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
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
        index=1
    )
    
    num_questions = st.slider(
        "Number of Questions",
        min_value=5,
        max_value=15,
        value=5,
        step=1
    )
    
    st.divider()
    
    if st.session_state.interview_started:
        st.info(f"📊 Progress: {st.session_state.current_question}/{len(st.session_state.questions)}")
        
        if st.button("🔄 Reset Interview", use_container_width=True):
            st.session_state.interview_started = False
            st.session_state.questions = []
            st.session_state.current_question = 0
            st.session_state.answers = {}
            st.session_state.feedback = {}
            st.session_state.interview_complete = False
            st.rerun()

# Main content
if not st.session_state.interview_started and not st.session_state.interview_complete:
    st.header("📋 Interview Setup")
    
    col1, col2 = st.columns(2)
    
    with col1:
        job_role = st.text_input(
            "Job Role",
            placeholder="e.g., Senior Software Engineer, Data Scientist, Product Manager",
            help="Enter the position you're interviewing for"
        )
    
    with col2:
        experience_level = st.selectbox(
            "Experience Level",
            ["Entry Level", "Mid Level", "Senior Level", "Lead/Principal"]
        )
    
    job_description = st.text_area(
        "Job Description",
        placeholder="Paste the job description here or describe key responsibilities and requirements...",
        height=200,
        help="Provide details about the role to get more relevant questions"
    )
    
    interview_type = st.multiselect(
        "Question Categories",
        ["Technical Skills", "Behavioral", "Problem Solving", "System Design", "Leadership", "Cultural Fit"],
        default=["Technical Skills", "Behavioral"]
    )
    
    if st.button("🚀 Start Interview", type="primary", use_container_width=True):
        if not api_key:
            st.error("❌ Please enter your OpenAI API key in the sidebar")
        elif not job_role:
            st.error("❌ Please enter a job role")
        elif not job_description:
            st.error("❌ Please provide a job description")
        else:
            with st.spinner("🤖 Generating interview questions..."):
                try:
                    llm = ChatOpenAI(
                        model=model_name,
                        temperature=0.7,
                        api_key=api_key
                    )
                    
                    template = """You are an expert technical interviewer. Generate {num_questions} interview questions for the following position:

Job Role: {job_role}
Experience Level: {experience_level}
Job Description: {job_description}
Question Categories: {categories}

Generate exactly {num_questions} interview questions that:
1. Are relevant to the job role and description
2. Cover the specified categories
3. Match the experience level
4. Range from easy to challenging
5. Include a mix of technical and behavioral questions

Return ONLY a valid JSON array with this exact structure:
[
    {{
        "question": "question text here",
        "category": "category name",
        "difficulty": "Easy/Medium/Hard"
    }}
]

Do not include any markdown formatting, code blocks, or extra text. Return only the JSON array."""

                    prompt = ChatPromptTemplate.from_template(template)
                    chain = prompt | llm
                    
                    response = chain.invoke({
                        "num_questions": num_questions,
                        "job_role": job_role,
                        "experience_level": experience_level,
                        "job_description": job_description,
                        "categories": ", ".join(interview_type)
                    })
                    
                    # Parse JSON response
                    content = response.content.strip()
                    if content.startswith("```json"):
                        content = content.replace("```json", "").replace("```", "").strip()
                    
                    questions = json.loads(content)
                    
                    st.session_state.questions = questions
                    st.session_state.interview_started = True
                    st.session_state.job_role = job_role
                    st.session_state.experience_level = experience_level
                    st.success("✅ Questions generated! Starting interview...")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error generating questions: {str(e)}")

elif st.session_state.interview_started and not st.session_state.interview_complete:
    st.header(f"🎤 Interview in Progress: {st.session_state.job_role}")
    
    progress = st.session_state.current_question / len(st.session_state.questions)
    st.progress(progress)
    
    if st.session_state.current_question < len(st.session_state.questions):
        current_q = st.session_state.questions[st.session_state.current_question]
        
        st.subheader(f"Question {st.session_state.current_question + 1} of {len(st.session_state.questions)}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.info(f"**Category:** {current_q['category']}")
        with col2:
            difficulty_color = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}
            st.info(f"**Difficulty:** {difficulty_color.get(current_q['difficulty'], '⚪')} {current_q['difficulty']}")
        
        st.markdown(f"### {current_q['question']}")
        
        answer_key = f"answer_{st.session_state.current_question}"
        answer = st.text_area(
            "Your Answer:",
            value=st.session_state.answers.get(st.session_state.current_question, ""),
            height=200,
            key=answer_key,
            placeholder="Type your answer here..."
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.session_state.current_question > 0:
                if st.button("⬅️ Previous", use_container_width=True):
                    st.session_state.answers[st.session_state.current_question] = answer
                    st.session_state.current_question -= 1
                    st.rerun()
        
        with col2:
            if st.session_state.current_question < len(st.session_state.questions) - 1:
                if st.button("Next ➡️", use_container_width=True):
                    if answer.strip():
                        st.session_state.answers[st.session_state.current_question] = answer
                        st.session_state.current_question += 1
                        st.rerun()
                    else:
                        st.warning("⚠️ Please provide an answer before proceeding")
            else:
                if st.button("🏁 Finish Interview", type="primary", use_container_width=True):
                    if answer.strip():
                        st.session_state.answers[st.session_state.current_question] = answer
                        st.session_state.interview_complete = True
                        st.rerun()
                    else:
                        st.warning("⚠️ Please provide an answer before finishing")

elif st.session_state.interview_complete:
    st.header("📊 Interview Complete - Generating Feedback")
    
    if not st.session_state.feedback:
        with st.spinner("🤖 Analyzing your answers and generating feedback..."):
            try:
                llm = ChatOpenAI(
                    model=model_name,
                    temperature=0.7,
                    api_key=api_key
                )
                
                # Generate feedback for each answer
                for idx, question in enumerate(st.session_state.questions):
                    answer = st.session_state.answers.get(idx, "")
                    
                    feedback_template = """You are an expert interviewer providing constructive feedback. 

Question: {question}
Category: {category}
Difficulty: {difficulty}
Candidate's Answer: {answer}

Provide detailed feedback in JSON format with this structure:
{{
    "score": 7.5,
    "strengths": ["point 1", "point 2"],
    "improvements": ["point 1", "point 2"],
    "sample_answer": "A brief example of a strong answer"
}}

The score should be out of 10. Be constructive and specific."""

                    prompt = ChatPromptTemplate.from_template(feedback_template)
                    chain = prompt | llm
                    
                    response = chain.invoke({
                        "question": question['question'],
                        "category": question['category'],
                        "difficulty": question['difficulty'],
                        "answer": answer
                    })
                    
                    content = response.content.strip()
                    if content.startswith("```json"):
                        content = content.replace("```json", "").replace("```", "").strip()
                    
                    feedback = json.loads(content)
                    st.session_state.feedback[idx] = feedback
                
                st.success("✅ Feedback generated!")
                st.rerun()
                
            except Exception as e:
                st.error(f"❌ Error generating feedback: {str(e)}")
    
    # Display results
    st.header("🎯 Interview Results")
    
    # Calculate overall score
    if st.session_state.feedback:
        total_score = sum(f['score'] for f in st.session_state.feedback.values())
        avg_score = total_score / len(st.session_state.feedback)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Overall Score", f"{avg_score:.1f}/10")
        with col2:
            st.metric("Questions Answered", len(st.session_state.answers))
        with col3:
            performance = "Excellent" if avg_score >= 8 else "Good" if avg_score >= 6 else "Fair"
            st.metric("Performance", performance)
        
        st.divider()
        
        # Display detailed feedback
        for idx, question in enumerate(st.session_state.questions):
            with st.expander(f"❓ Question {idx + 1}: {question['question'][:80]}...", expanded=False):
                feedback = st.session_state.feedback.get(idx, {})
                
                col1, col2 = st.columns([2, 1])
                with col1:
                    st.markdown(f"**Full Question:** {question['question']}")
                    st.markdown(f"**Your Answer:** {st.session_state.answers.get(idx, '')}")
                with col2:
                    st.metric("Score", f"{feedback.get('score', 0)}/10")
                
                st.markdown("**✅ Strengths:**")
                for strength in feedback.get('strengths', []):
                    st.markdown(f"- {strength}")
                
                st.markdown("**💡 Areas for Improvement:**")
                for improvement in feedback.get('improvements', []):
                    st.markdown(f"- {improvement}")
                
                st.markdown("**📝 Sample Strong Answer:**")
                st.info(feedback.get('sample_answer', 'N/A'))
        
        # Download report
        st.divider()
        
        report = f"""MOCK INTERVIEW REPORT
===================
Job Role: {st.session_state.job_role}
Experience Level: {st.session_state.experience_level}
Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Overall Score: {avg_score:.1f}/10

"""
        
        for idx, question in enumerate(st.session_state.questions):
            feedback = st.session_state.feedback.get(idx, {})
            report += f"\nQuestion {idx + 1}: {question['question']}\n"
            report += f"Your Answer: {st.session_state.answers.get(idx, '')}\n"
            report += f"Score: {feedback.get('score', 0)}/10\n"
            report += "-" * 80 + "\n"
        
        st.download_button(
            label="📄 Download Full Report",
            data=report,
            file_name=f"interview_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain",
            use_container_width=True
        )

# Footer
st.divider()
st.markdown("""
<div style='text-align: center; color: gray; font-size: 0.9em;'>
    <p>💡 Tip: Take your time with each answer and be specific with examples</p>
    <p>Built with Streamlit, LangChain, and OpenAI</p>
</div>
""", unsafe_allow_html=True)