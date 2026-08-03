import streamlit as st
import streamlit.components.v1 as components
from google import genai
import os
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import re
import pandas as pd
import json

from auth.database import *
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.colors import HexColor

# -----------------------------------
# Load Environment Variables
# -----------------------------------
load_dotenv()

# -----------------------------------
# Configure Gemini Client
# -----------------------------------
client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)

# -----------------------------------
# Page Configuration
# -----------------------------------
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)

create_users_table()
create_history_table()

# -----------------------------------
# Session State
# -----------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# -----------------------------------
# Load External CSS
# -----------------------------------
def load_css(file_name):
    with open(file_name, encoding="utf-8") as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

load_css("styles/style.css")

# -----------------------------------
# Handle Logout via Query Params
# -----------------------------------
if st.query_params.get("logout") == "true":
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.query_params.clear()
    st.rerun()

# -----------------------------------
# Login / Signup
# -----------------------------------
if not st.session_state.logged_in:

    st.markdown("""
        <div class="login-title">
            🔐 AI Resume Analyzer
        </div>

        <div class="login-subtitle">
            Login or create an account to continue.
        </div>
        """, unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:

        username = st.text_input("Username", key="login_username")
        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login"):

            user = login_user(username, password)

            if user:

                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()

            else:

                st.error("Invalid username or password.")

    with tab2:

        new_username = st.text_input(
            "Choose Username",
            key="signup_username"
        )

        new_password = st.text_input(
            "Choose Password",
            type="password",
            key="signup_password"
        )

        if st.button("Create Account"):

            success = register_user(
                new_username,
                new_password
            )

            if success:

                st.success("Account created successfully!")

            else:

                st.error("Username already exists.")

    st.stop()

# -----------------------------------
# Navbar
# -----------------------------------
st.markdown(f"""
<div class="navbar">
    <div class="navbar-left">
        <div class="navbar-title">
            📄 AI Powered Resume Analyzer
        </div>
    </div>
    <div class="nav-links">
        <span class="nav-user">👋 {st.session_state.username}</span>
        <a href="#" id="home-link">Home</a>
        <a href="#" id="analyze-link">Analyze</a>
        <a href="#" id="history-link">History</a>
        <a href="?logout=true" id="logout-link">Logout</a>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("""
    <div class="navbar-divider"></div>
    """, unsafe_allow_html=True)

components.html(
    """
    <script>

    function attachHandlers() {

        const analyze = parent.document.getElementById("analyze-link");

        if (analyze) {

            analyze.onclick = function(e) {

                e.preventDefault();

                const target = parent.document.getElementById("upload-section");

                if (target) {

                    target.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

                }

            };

        }

        const history = parent.document.getElementById("history-link");

        if (history) {

            history.onclick = function(e) {

                e.preventDefault();

                const target = parent.document.getElementById("history-section");

                if (target) {

                    target.scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

                }

            };

        }

    }

    setTimeout(attachHandlers, 500);

    </script>
    """,
    height=0,
)

# -----------------------------------
# Generate PDF Report
# -----------------------------------
def generate_pdf_report(total_score, score_data, analysis_text):

    doc = SimpleDocTemplate("Resume_Analysis_Report.pdf")
    styles = getSampleStyleSheet()

    title = styles["Heading1"]
    title.alignment = TA_CENTER
    title.textColor = HexColor("#1565C0")

    heading = styles["Heading2"]
    heading.textColor = HexColor("#1565C0")

    normal = styles["BodyText"]

    story = []

    # Title
    story.append(Paragraph("AI Resume Analyzer Report", title))
    story.append(Paragraph("<br/><br/>", normal))

    # Overall Score
    story.append(Paragraph("Overall Resume Score", heading))
    story.append(Paragraph(f"<b>{total_score}/100</b>", normal))
    story.append(Paragraph("<br/>", normal))

    # Score Breakdown
    story.append(Paragraph("Score Breakdown", heading))

    for category, score in score_data.items():
        story.append(
            Paragraph(f"<b>{category}</b> : {score}", normal)
        )

    story.append(Paragraph("<br/>", normal))

    # AI Analysis
    story.append(Paragraph("AI Analysis", heading))

    analysis_text = analysis_text.replace("\n", "<br/>")

    story.append(
        Paragraph(analysis_text, normal)
    )

    doc.build(story)

    return "Resume_Analysis_Report.pdf"


if True:
    # -----------------------------------
    # Header
    # -----------------------------------
    st.markdown(
        """
        <div class="hero">
            <h1>📄 AI Resume Analyzer</h1>
            <p>
                Upload your resume and paste the job description to receive
                an AI-powered ATS analysis, resume score, skill matching,
                gap analysis, and personalized improvement suggestions.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    # ==========================================
    # Welcome Section
    # ==========================================

    st.subheader("👋 Welcome to AI Powered Resume Analyzer")

    st.info("""
    Analyze your resume against any job description using AI.

    Our system compares your resume with the job description and provides:

    - 📊 ATS Compatibility Score
    - 🎯 Skill Match Analysis
    - ⚠ Missing Skills
    - 💪 Resume Strengths
    - 💡 Personalized Improvement Suggestions

    Upload your resume, paste the job description, and receive a detailed report within seconds.
    """)

    st.divider()

    # ==========================================
    # Do's & Don'ts
    # ==========================================

    col1, col2 = st.columns(2)

    with col1:
        st.success("### ✅ Do's")

        st.markdown("""
    - Upload your resume in **PDF** format.
    - Paste the **complete Job Description**.
    - Use ATS-friendly formatting.
    - Highlight measurable achievements.
    - Include relevant technical skills.
    - Keep contact information updated.
    """)

    with col2:
        st.error("### ❌ Don'ts")

        st.markdown("""
    - Don't upload scanned resumes.
    - Don't use excessive graphics or tables.
    - Don't stuff keywords unnaturally.
    - Don't leave important sections incomplete.
    - Don't use outdated information.
    - Don't submit unrelated resumes.
    """)

    st.divider()

    # ==========================================
    # How It Works
    # ==========================================

    st.subheader("⚙️ How It Works")

    step1, step2, step3, step4 = st.columns(4)

    with step1:
        st.info("""
    ### 📄 Step 1

    Upload your resume in PDF format.
    """)

    with step2:
        st.info("""
    ### 💼 Step 2

    Paste the Job Description.
    """)

    with step3:
        st.info("""
    ### 🤖 Step 3

    AI compares your resume with the job requirements.
    """)

    with step4:
        st.info("""
    ### 📊 Step 4

    View ATS score, missing skills, recommendations, and download the PDF report.
    """)

    st.divider()


    # -----------------------------------
    # Upload Resume
    # -----------------------------------

    st.markdown(
        """
        <div id="upload-section" style="height:1px;"></div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("### 📄Upload Your Resume")

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF)",
        type=["pdf"]
    )

    st.markdown("### 💼 Job Description")

    job_description = st.text_area(
        "Paste the Job Description",
        height=220,
        placeholder="Paste the complete job description here..."
    )

    # -----------------------------------
    # Process Uploaded Resume
    # -----------------------------------
    if uploaded_file:

        pdf = PdfReader(uploaded_file)

        text = ""

        for page in pdf.pages:

            page_text = page.extract_text()

            if page_text:

                text += page_text + "\n"

        # Clean extracted text
        text_clean = re.sub(
            r"(?<!\n)\n(?!\n)",
            " ",
            text
        )

        # Two-column layout
        # col1, col2 = st.columns(2)

        # -----------------------------------
        # Resume Preview
        # -----------------------------------
        # with col1:

        st.markdown(
            "<div class='card-title'>📄 Resume Preview</div>",
            unsafe_allow_html=True
        )

        st.text_area(
            "Analysis Report",
            value=text_clean,
            height=500
        )

        # -----------------------------------
        # AI Analysis
        # -----------------------------------
        #with col2:

        st.markdown(
            "<div class='card-title'>🤖 AI Analysis</div>",
            unsafe_allow_html=True
        )

        analyze = st.button(
            "🚀 Analyze Resume",
            use_container_width=True,
            disabled=not (uploaded_file and job_description.strip())
        )

        if analyze:

            with st.spinner("Analyzing Resume..."):
                                    
                job_description_clean = job_description.strip()

                # Check if Job Description is provided
                if not job_description_clean:
                    st.error("⚠️ Please paste a Job Description before analyzing the resume.")
                    st.stop()

                st.info(
                    "📊 Job description detected — running a tailored match analysis."
                )

                prompt = f"""
        Return the entire report in plain text only.
        Do not use Markdown formatting such as ###, **, *, -, or •.
        Use simple numbered headings and plain text lists.
        You are an expert ATS Resume Analyzer.

        Analyze the following resume against the provided job description and provide:

        1. Professional Summary

        2. Key Skills (Bullet Points)

        3. Job Description Match Analysis

        4. Matching Skills

        5. Missing or Gap Skills

        6. Strengths

        7. Areas of Improvement

        8. Suggestions to Improve ATS Score and Job Match

        9. Score out of 100 using:

        - Skills Match (30)
        - Experience & Achievements (30)
        - Clarity & Formatting (20)
        - Overall Impression (20)

        At the end write exactly:

        Score JSON:
        {{
            "Skills Match": 0,
            "Experience & Achievements": 0,
            "Clarity & Formatting": 0,
            "Overall Impression": 0
        }}

        Job Description:

        {job_description_clean}

        Resume:

        {text_clean}
        """
                try:

                    response = client.models.generate_content(
                        model="gemini-3.5-flash-lite",
                        contents=prompt
                    )

                    result = response.text.strip()

                    parts = result.split("Score JSON:")

                    analysis_text = parts[0]

                    st.markdown("### 📋 AI Analysis")
                    st.markdown(analysis_text)

                    score_data = None

                    if len(parts) > 1:

                        try:

                            score_data = json.loads(
                                parts[1].strip()
                            )

                        except Exception:

                            st.warning(
                                "Could not parse score JSON."
                            )

                                                    # -----------------------------------
                                # Display Score Breakdown
                                # -----------------------------------
                    if score_data:

                        st.markdown("### 📊 Score Breakdown")

                        max_scores = {
                            "Skills Match": 30,
                            "Experience & Achievements": 30,
                            "Clarity & Formatting": 20,
                            "Overall Impression": 20
                        }

                        for category, score in score_data.items():

                            max_score = max_scores.get(category, 100)
                            percentage = score / max_score

                            st.markdown(
                                f"""
                                <div class="progress-header">
                                    <span>{category}</span>
                                    <span>{score}/{max_score}</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                            st.markdown(
                                f"""
                                <div class="progress-container">
                                    <div class="progress-fill" style="width:{percentage*100}%">{percentage*100:.0f}%</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        total_score = sum(
                            score_data.values()
                        )

                        st.markdown("### 🎯 Overall Score")

                        st.progress(
                            total_score / 100
                        )

                        st.metric(
                            label="Resume Score",
                            value=f"{total_score}/100"
                        )

                        if total_score >= 85:

                            st.success(
                                "Excellent Resume! Your resume is highly ATS-friendly."
                            )

                        elif total_score >= 70:

                            st.info(
                                "Good Resume. A few improvements can make it even stronger."
                            )

                        elif total_score >= 50:

                            st.warning(
                                "Average Resume. Consider improving formatting, skills, and achievements."
                            )

                        else:

                            st.error(
                                "Your resume needs significant improvements to perform well in ATS systems."
                            )


                        # -----------------------------------
                        # Generate PDF Report
                        # -----------------------------------
                        save_history(
                            st.session_state.username,
                            total_score,
                            job_description_clean,
                            analysis_text
                        )

                        pdf_file = generate_pdf_report(
                            total_score,
                            score_data,
                            analysis_text
                        )

                        st.download_button(
                            label="📥 Download Analysis Report",
                            data=open(pdf_file, "rb").read(),
                            file_name="Resume_Analysis_Report.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )


                    
                except Exception as e:

                    st.error(
                        f"Error: {e}"
                    )

st.markdown(
    """
    <div id="history-section" style="height:1px;"></div>
    """,
    unsafe_allow_html=True
)

st.title("📜 Resume Analysis History")

history = get_history(st.session_state.username)
if not history:
    st.info("No previous analyses found.")

else:
    for item in history:
        history_id = item[0]
        score = item[1]
        date = item[2]
        st.write(f"Score: {score}/100")
        st.write(date)

        # 👇 ADD THE BUTTON HERE
        if st.button("View Report", key=history_id):
            report = get_single_history(history_id)
            st.subheader("Job Description")
            st.write(report[3])

            st.subheader("AI Analysis")
            st.write(report[4])

    st.divider()

st.markdown("""
<div class="footer-divider"></div>
<div class="footer">
    © 2026 AI Resume Analyzer • Made with ❤️ by Dhwani
    <div class="footer-divider2"></div>
    <p>Analyze your resume using AI and compare it with any job
        description to improve ATS compatibility and increase your
        interview chances.
    </p>
</div>
""", unsafe_allow_html=True)