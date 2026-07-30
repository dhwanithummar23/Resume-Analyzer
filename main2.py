import streamlit as st
from google import genai
import os
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import re
import pandas as pd
import json

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

# -----------------------------------
# Upload Resume
# -----------------------------------
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
        "",
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