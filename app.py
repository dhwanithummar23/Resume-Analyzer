import streamlit as st
import streamlit.components.v1 as components
from google import genai
import os
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import re
import pandas as pd
import json
from io import BytesIO
from xml.sax.saxutils import escape

from auth.database import *
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
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
create_resumes_table()

# -----------------------------------
# Session State
# -----------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

# NEW: controls whether the login/signup popup is open, and which tab
if "show_auth" not in st.session_state:
    st.session_state.show_auth = False

if "auth_default_tab" not in st.session_state:
    st.session_state.auth_default_tab = "Login"

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
# Handle "Login" / "Sign Up" navbar links via Query Params
# (?auth=login  or  ?auth=signup)
# -----------------------------------
auth_param = st.query_params.get("auth")
if auth_param in ("login", "signup") and not st.session_state.logged_in:
    st.session_state.show_auth = True
    st.session_state.auth_default_tab = "Login" if auth_param == "login" else "Sign Up"
    st.query_params.clear()
    st.rerun()

# -----------------------------------
# Login / Signup Dialog (popup, not full page)
# -----------------------------------
@st.dialog("🔐 AI Resume Analyzer")
def auth_dialog():

    st.markdown(
        f"<div class='login-subtitle'>Login or create an account to continue.</div>",
        unsafe_allow_html=True
    )

    default_index = 0 if st.session_state.auth_default_tab == "Login" else 1
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:

        username = st.text_input("Username", key="login_username")
        password = st.text_input(
            "Password",
            type="password",
            key="login_password"
        )

        if st.button("Login", key="login_submit_btn"):

            user = login_user(username, password)

            if user:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.show_auth = False
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

        if st.button("Create Account", key="signup_submit_btn"):

            success = register_user(
                new_username,
                new_password
            )

            if success:
                st.success("Account created successfully! Please login.")
            else:
                st.error("Username already exists.")


if st.session_state.show_auth and not st.session_state.logged_in:
    auth_dialog()

# -----------------------------------
# Navbar (shown to EVERYONE — logged in or not)
# -----------------------------------
if st.session_state.logged_in:
    nav_links_html = (
        f'<span class="nav-user">👋 {st.session_state.username}</span>'
        '<a href="javascript:void(0)" id="home-link">Home</a>'
        '<a href="javascript:void(0)" id="analyze-link">Analyze</a>'
        '<a href="javascript:void(0)" id="history-link">History</a>'
        '<a href="?logout=true" id="logout-link">Logout</a>'
    )
else:
    nav_links_html = (
        '<a href="javascript:void(0)" id="home-link">Home</a>'
        '<a href="?auth=login" id="login-link">Login</a>'
        '<a href="?auth=signup" id="signup-link">Sign Up</a>'
    )

navbar = f"""
<div class="navbar" style=background-color:#F5F9FF>
    <div class="navbar-left">
        <div class="navbar-title">
            📄 AI Powered Resume Analyzer
        </div>
    </div>
    <div class="nav-links">
        {nav_links_html}
    </div>
</div>
"""

st.markdown(navbar.strip(), unsafe_allow_html=True)
st.markdown("""
    <div class="navbar-divider"></div>
    """, unsafe_allow_html=True)

components.html("""
<script>
window.parent.document.addEventListener("click", function(e){

    if(e.target.id === "analyze-link"){
        e.preventDefault();

        const target = window.parent.document.getElementById("upload-your-resume");

        if(target){
            target.scrollIntoView({
                behavior: "smooth",
                block: "start"
            });
        }
    }

    if (e.target.id === "history-link") {
    e.preventDefault();

    const target = window.parent.document.getElementById("resume-analysis-history");

    if (target) {
        target.scrollIntoView({
            behavior: "smooth",
            block: "start"
        });
    }
}

});
</script>
""", height=0)

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


def generate_ats_resume_pdf(resume):
    """Generate a simple, text-first PDF that is easy for ATS tools to parse."""
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        rightMargin=48,
        leftMargin=48,
        topMargin=42,
        bottomMargin=42,
    )
    styles = getSampleStyleSheet()
    name_style = ParagraphStyle(
        "ResumeName",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_CENTER,
        textColor=HexColor("#1A1A2E"),
        spaceAfter=4,
    )
    headline_style = ParagraphStyle(
        "ResumeHeadline",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontSize=10,
        leading=14,
        textColor=HexColor("#333333"),
        spaceAfter=3,
    )
    contact_style = ParagraphStyle(
        "ResumeContact",
        parent=styles["BodyText"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        textColor=HexColor("#444444"),
        spaceAfter=14,
    )
    section_style = ParagraphStyle(
        "ResumeSection",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=HexColor("#1565C0"),
        spaceBefore=10,
        spaceAfter=5,
    )
    body_style = ParagraphStyle(
        "ResumeBody",
        parent=styles["BodyText"],
        fontSize=10,
        leading=14,
        textColor=HexColor("#222222"),
        spaceAfter=4,
    )

    def paragraph_text(value):
        return escape(value.strip()).replace("\n", "<br/>")

    contact = " | ".join(
        value for value in [
            resume.get("email", ""),
            resume.get("phone", ""),
            resume.get("location", ""),
            resume.get("linkedin", ""),
            resume.get("portfolio", ""),
        ] if value
    )
    story = [Paragraph(paragraph_text(resume["full_name"]), name_style)]

    if resume.get("headline"):
        story.append(Paragraph(paragraph_text(resume["headline"]), headline_style))
    if contact:
        story.append(Paragraph(paragraph_text(contact), contact_style))
    else:
        story.append(Spacer(1, 8))

    sections = [
        ("Professional Summary", resume.get("summary", "")),
        ("Skills", resume.get("skills", "")),
        ("Work Experience", resume.get("experience", "")),
        ("Education", resume.get("education", "")),
        ("Projects", resume.get("projects", "")),
        ("Certifications", resume.get("certifications", "")),
    ]
    for heading, content in sections:
        if content.strip():
            story.append(Paragraph(heading, section_style))
            story.append(Paragraph(paragraph_text(content), body_style))

    document.build(story)
    return buffer.getvalue()


def build_resume_text(resume):
    """Turn a saved profile into ATS-friendly plain text for analysis."""
    contact = " | ".join(
        value for value in [
            resume.get("email", ""),
            resume.get("phone", ""),
            resume.get("location", ""),
            resume.get("linkedin", ""),
            resume.get("portfolio", ""),
        ] if value
    )

    sections = [
        resume.get("full_name", ""),
        resume.get("headline", ""),
        contact,
        "PROFESSIONAL SUMMARY\n" + resume.get("summary", ""),
        "SKILLS\n" + resume.get("skills", ""),
        "EXPERIENCE\n" + resume.get("experience", ""),
        "EDUCATION\n" + resume.get("education", ""),
        "PROJECTS\n" + resume.get("projects", ""),
        "CERTIFICATIONS\n" + resume.get("certifications", ""),
    ]
    return "\n\n".join(section for section in sections if section.strip())


def resume_form(existing_resume, form_key):
    """Render the editable resume profile and return it after a valid save."""
    resume = existing_resume or {}

    with st.form(form_key):
        st.subheader("Your resume details")
        identity_col, contact_col = st.columns(2)
        with identity_col:
            full_name = st.text_input("Full name", value=resume.get("full_name", ""))
            headline = st.text_input(
                "Professional headline",
                value=resume.get("headline", ""),
                placeholder="e.g. Data Analyst | Python | SQL"
            )
        with contact_col:
            email = st.text_input("Email", value=resume.get("email", ""))
            phone = st.text_input("Phone", value=resume.get("phone", ""))

        location_col, link_col = st.columns(2)
        with location_col:
            location = st.text_input("Location", value=resume.get("location", ""))
            linkedin = st.text_input("LinkedIn URL", value=resume.get("linkedin", ""))
        with link_col:
            portfolio = st.text_input(
                "Portfolio or GitHub URL", value=resume.get("portfolio", "")
            )

        summary = st.text_area(
            "Professional summary",
            value=resume.get("summary", ""),
            height=120,
            placeholder="Describe your experience, strengths, and target role."
        )
        skills = st.text_area(
            "Skills",
            value=resume.get("skills", ""),
            height=100,
            placeholder="List skills separated by commas, for example: Python, SQL, Tableau"
        )
        experience = st.text_area(
            "Work experience",
            value=resume.get("experience", ""),
            height=180,
            placeholder="Company | Role | Dates\nDescribe responsibilities and measurable achievements."
        )
        education = st.text_area(
            "Education",
            value=resume.get("education", ""),
            height=110,
            placeholder="Degree | Institution | Graduation year"
        )
        projects = st.text_area(
            "Projects",
            value=resume.get("projects", ""),
            height=130,
            placeholder="Project name | Technologies\nDescribe the outcome or impact."
        )
        certifications = st.text_area(
            "Certifications",
            value=resume.get("certifications", ""),
            height=90,
            placeholder="Optional: certification name, issuer, year"
        )

        save_column, generate_column = st.columns(2)
        with save_column:
            save_submitted = st.form_submit_button(
                "Save resume", use_container_width=True
            )
        with generate_column:
            generate_submitted = st.form_submit_button(
                "Generate ATS-friendly resume", use_container_width=True
            )

    pdf_key = f"{form_key}_pdf"
    if not save_submitted and not generate_submitted:
        if st.session_state.get(pdf_key):
            st.download_button(
                "Download ATS-friendly resume",
                data=st.session_state[pdf_key]["data"],
                file_name=st.session_state[pdf_key]["filename"],
                mime="application/pdf",
                use_container_width=True,
            )
        return None

    if not full_name.strip() or not email.strip() or not summary.strip() or not skills.strip():
        st.error("Add your name, email, professional summary, and skills before saving.")
        return None

    saved_resume = {
        "full_name": full_name.strip(),
        "headline": headline.strip(),
        "email": email.strip(),
        "phone": phone.strip(),
        "location": location.strip(),
        "linkedin": linkedin.strip(),
        "portfolio": portfolio.strip(),
        "summary": summary.strip(),
        "skills": skills.strip(),
        "experience": experience.strip(),
        "education": education.strip(),
        "projects": projects.strip(),
        "certifications": certifications.strip(),
    }
    save_resume(st.session_state.username, saved_resume)

    if generate_submitted:
        file_stem = re.sub(r"[^A-Za-z0-9]+", "_", full_name.strip()).strip("_")
        st.session_state[pdf_key] = {
            "data": generate_ats_resume_pdf(saved_resume),
            "filename": f"{file_stem or 'resume'}_ATS_Resume.pdf",
        }
        st.success("Your ATS-friendly resume is ready to download.")
        st.download_button(
            "Download ATS-friendly resume",
            data=st.session_state[pdf_key]["data"],
            file_name=st.session_state[pdf_key]["filename"],
            mime="application/pdf",
            use_container_width=True,
        )
    else:
        st.session_state.pop(pdf_key, None)

    return saved_resume


def render_score_chart(score_data, max_scores):
    chart_rows = []
    for category, maximum in max_scores.items():
        score = min(max(float(score_data.get(category, 0)), 0), maximum)
        chart_rows.append({
            "Category": category,
            "Score": score,
            "Maximum": maximum,
            "Percentage": round((score / maximum) * 100),
        })

    chart_data = pd.DataFrame(chart_rows)
    st.markdown("### Resume score visual")
    st.caption("Each category is shown as a percentage of its available marks.")
    st.bar_chart(
        chart_data,
        x="Category",
        y="Percentage",
        color="#1565C0",
        horizontal=True,
        height=300,
    )


# -----------------------------------
# Home / Hero Section — PUBLIC, always visible
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
# Upload / Analyze Section — LOGIN REQUIRED
# -----------------------------------
st.markdown(
    """
    <div id="upload-section" style="height:1px;"></div>
    """,
    unsafe_allow_html=True
)

st.markdown("### 📄 Upload Your Resume")

if not st.session_state.logged_in:

    st.warning("🔒 Please login or create an account to analyze your resume.")

    if st.button("Login / Sign Up to Analyze", key="gate_login_btn"):
        st.session_state.show_auth = True
        st.session_state.auth_default_tab = "Login"
        st.rerun()

else:
    saved_resume = get_resume(st.session_state.username)
    resume_text = ""

    if saved_resume:
        st.success("Your saved resume is ready to analyze.")
        with st.expander("Update your saved resume"):
            updated_resume = resume_form(saved_resume, "update_resume_form")
            if updated_resume:
                saved_resume = updated_resume
                st.success("Resume updated.")

        resume_source = st.radio(
            "Choose a resume source",
            ["Saved resume", "Upload a PDF"],
            horizontal=True,
        )
        if resume_source == "Saved resume":
            resume_text = build_resume_text(saved_resume)
            uploaded_file = None
        else:
            uploaded_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    else:
        st.info("You do not have a saved resume yet. Create one below or upload a PDF.")
        created_resume = resume_form(None, "create_resume_form")
        if created_resume:
            saved_resume = created_resume
            resume_text = build_resume_text(saved_resume)
            st.success("Resume created. You can analyze it now.")

        uploaded_file = st.file_uploader("Or upload a Resume (PDF)", type=["pdf"])

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
        resume_text = re.sub(
            r"(?<!\n)\n(?!\n)",
            " ",
            text
        )

    if resume_text:

        st.markdown(
            "<div class='card-title'>📄 Resume Preview</div>",
            unsafe_allow_html=True
        )

        st.text_area(
            "Resume content",
            value=resume_text,
            height=500
        )

        st.markdown(
            "<div class='card-title'>🤖 AI Analysis</div>",
            unsafe_allow_html=True
        )

        analyze = st.button(
            "🚀 Analyze Resume",
            use_container_width=True,
            disabled=not (resume_text and job_description.strip())
        )

        if analyze:

            with st.spinner("Analyzing Resume..."):

                job_description_clean = job_description.strip()

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

        {resume_text}
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

                    if score_data:

                        st.markdown("### 📊 Score Breakdown")

                        max_scores = {
                            "Skills Match": 30,
                            "Experience & Achievements": 30,
                            "Clarity & Formatting": 20,
                            "Overall Impression": 20
                        }

                        normalized_scores = {}
                        for category, maximum in max_scores.items():
                            try:
                                normalized_scores[category] = min(
                                    max(float(score_data.get(category, 0)), 0),
                                    maximum,
                                )
                            except (TypeError, ValueError):
                                normalized_scores[category] = 0
                        score_data = normalized_scores

                        render_score_chart(score_data, max_scores)

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
                        # Save history + Generate PDF Report
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

# -----------------------------------
# History Section — LOGIN REQUIRED
# -----------------------------------
st.markdown(
    """
    <div id="history-section" style="height:1px;"></div>
    """,
    unsafe_allow_html=True
)

st.markdown("""
<h1 id="resume-analysis-history">📜 Resume Analysis History</h1>
""", unsafe_allow_html=True)

if not st.session_state.logged_in:

    st.info("🔒 Login to view your resume analysis history.")

else:

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

            if st.button("View Report", key=history_id):
                report = get_single_history(history_id)
                st.subheader("Job Description")
                st.write(report[3])

                st.subheader("AI Analysis")
                st.write(report[4])

        st.divider()

# -----------------------------------
# Footer
# -----------------------------------
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
