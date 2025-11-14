import streamlit as st
import fitz  # PyMuPDF for PDF processing
import mammoth  # Mammoth for .docx processing
import asyncio
from dotenv import load_dotenv
from core.config import Config
from core.gemini_client import GeminiClient
from services.skill_assessment_service import SkillAssessmentService
from services.resume_service import ResumeService
from agents.evaluation_agent import EvaluationAgent, FeedbackAgent
from agents.resume_analysis_agent import ResumeAnalysisAgent

# Load environment variables
load_dotenv()

# Initialize services and agents
config = Config.from_env()
gemini_client = GeminiClient(config)
skill_service = SkillAssessmentService(gemini_client)
evaluation_agent = EvaluationAgent(gemini_client)
feedback_agent = FeedbackAgent(gemini_client)
resume_agent = ResumeAnalysisAgent(gemini_client)
resume_service = ResumeService(gemini_client)

def initialize_session_state():
    session_defaults = {
        "skills_with_levels": [],
        "assessment_questions": None,
        "user_answers": {},
        "resume_text": None,
        "resume_analysis": None,
        "ats_analysis": None,
        "improved_resume": None,
    }
    for key, value in session_defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

def handle_skill_assessment():
    st.header("📝 Student Skill Test")
    available_skills = [
        "Python", "Java", "JavaScript", "Machine Learning", "Data Analysis",
        "Web Development", "DevOps", "Cloud Computing", "Database Management", "Software Testing"
    ]
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        new_skill = st.selectbox("Select Skill", available_skills)
    with col2:
        skill_level = st.selectbox("Select Level", ["Beginner", "Intermediate", "Advanced"])
    with col3:
        if st.button("Add Skill", use_container_width=True):
            skill_info = {"skill": new_skill, "level": skill_level}
            if skill_info not in st.session_state.skills_with_levels:
                st.session_state.skills_with_levels.append(skill_info)
                st.rerun()
    
    if st.session_state.skills_with_levels:
        st.subheader("📌 Selected Skills")
        for idx, skill_info in enumerate(st.session_state.skills_with_levels):
            col1, col2, col3 = st.columns([2, 1, 1])
            col1.write(f"✅ {skill_info['skill']}")
            col2.write(skill_info['level'])
            if col3.button("❌ Remove", key=f"remove_skill_{idx}", use_container_width=True):
                st.session_state.skills_with_levels.pop(idx)
                st.rerun()
    
    if st.session_state.skills_with_levels and not st.session_state.assessment_questions:
        if st.button("Generate Assessment", use_container_width=True):
            with st.spinner("Generating assessment..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    assessment = loop.run_until_complete(skill_service.generate_assessment(st.session_state.skills_with_levels))
                    st.session_state.assessment_questions = assessment["questions"]
                    loop.close()
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    if st.session_state.assessment_questions:
        st.success("Answer all questions and click 'Submit' when done.")
        for idx, question in enumerate(st.session_state.assessment_questions):
            with st.expander(f"Question {idx + 1}: {question['skill']} ({question['difficulty']}) - {question['max_points']} points"):
                st.write(question["question"])
                st.session_state.user_answers[idx] = st.text_area("Your Answer", key=f"answer_{idx}", height=150)
        
        if st.button("Submit Assessment", use_container_width=True):
            if any(not ans.strip() for ans in st.session_state.user_answers.values()):
                st.warning("Please answer all questions before submitting.")
                return
            with st.spinner("Evaluating your answers..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    evaluations, total_points, max_possible = [], 0, 0
                    for idx, question in enumerate(st.session_state.assessment_questions):
                        evaluation = loop.run_until_complete(evaluation_agent.evaluate_answer(question, st.session_state.user_answers[idx]))
                        evaluations.append(evaluation)
                        total_points += evaluation["points_awarded"]
                        max_possible += question["max_points"]
                    feedback = loop.run_until_complete(feedback_agent.generate_feedback(evaluations, st.session_state.assessment_questions))
                    loop.close()
                    st.success("✅ Assessment Evaluated Successfully!")
                    st.metric("Total Score", f"{total_points}/{max_possible}")
                    st.metric("Percentage", f"{(total_points/max_possible)*100:.1f}%")
                    st.subheader("Overall Assessment")
                    st.write(feedback["overall_assessment"])
                except Exception as e:
                    st.error(f"Error during evaluation: {str(e)}")

def handle_resume_review():
    st.header("📄 Resume Review & Improvement")
    input_method = st.radio("Choose input method:", ["Upload File", "Paste Text"])
    job_role = st.text_input("🎯 Target Job Role (Optional)", help="Enter the job role for better analysis")
    resume_text = None
    
    if input_method == "Upload File":
        uploaded_file = st.file_uploader("Upload your resume", type=['txt', 'pdf', 'docx'])
        if uploaded_file:
            try:
                if uploaded_file.type == "text/plain":
                    resume_text = uploaded_file.read().decode()
                elif uploaded_file.type == "application/pdf":
                    pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
                    resume_text = "".join([page.get_text() for page in pdf_document])
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    resume_text = mammoth.extract_raw_text(uploaded_file).value
                else:
                    st.error("Unsupported file type.")
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    else:
        resume_text = st.text_area("Paste your resume text here", height=300)
    
    if resume_text:
        st.session_state.resume_text = resume_text
        if st.button("Analyze Resume", use_container_width=True):
            with st.spinner("Analyzing Resume..."):
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    analysis = loop.run_until_complete(resume_agent.analyze_resume(resume_text, job_role))
                    st.session_state.resume_analysis = analysis
                    loop.close()
                    st.success("✅ Resume Analysis Complete!")
                    st.write(analysis)
                except Exception as e:
                    st.error(f"Error analyzing resume: {str(e)}")

def main():
    initialize_session_state()
    menu_options = ["📊 Skill Assessment", "📑 Resume Review"]
    selected_option = st.sidebar.selectbox("Choose a feature:", menu_options)
    if selected_option == "📊 Skill Assessment":
        handle_skill_assessment()
    elif selected_option == "📑 Resume Review":
        handle_resume_review()

if __name__ == "__main__":
    main()
