import streamlit as st
from google import genai
import os
from PyPDF2 import PdfReader
from dotenv import load_dotenv
import re
import pandas as pd
import json

# Load environment variables
load_dotenv()

# Configure Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

# Streamlit Page
st.set_page_config(page_title="Resume Analyzer", page_icon="📄", layout="wide")

st.title("Resume Analyzer")
st.markdown("Upload your resume and get **summary, key skills score and improvement suggestions**")

# Upload PDF
uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])

if uploaded_file:
    pdf = PdfReader(uploaded_file)
    text = ""

    for page in pdf.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    # Clean text
    text_clean = re.sub(r"(?<!\n)\n(?!\n)", " ", text)

    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("Resume Preview")
        st.text_area("Resume Text", value=text_clean, height=400)

    with col2:
        st.subheader("AI Analysis")

        if st.button("Analyze Resume"):

            with st.spinner("Analyzing resume..."):

                prompt = f"""
You are an expert resume analyzer.

Analyze the following resume and provide:

1. Summary
2. List of key skills
3. Suggestions for improvement
4. A score out of 100 based on:
   - Skills Match (30 points)
   - Experience & Achievements (30 points)
   - Clarity & Formatting (20 points)
   - Overall Impression (20 points)

At the end write exactly:

Score JSON:
{{
  "Skills Match": <score>,
  "Experience & Achievements": <score>,
  "Clarity & Formatting": <score>,
  "Overall Impression": <score>
}}

Resume:

{text_clean}
"""

                try:
                    response = client.models.generate_content(
                        model="gemini-3.5-flash",
                        contents=prompt
                    )

                    result = response.text

                    parts = result.split("Score JSON:")
                    analysis_text = parts[0]

                    st.write(analysis_text)

                    if len(parts) > 1:
                        try:
                            score_data = json.loads(parts[1].strip())

                            st.subheader("Score Breakdown")

                            df = pd.DataFrame({
                                "Category": list(score_data.keys()),
                                "Score": list(score_data.values())
                            })

                            st.bar_chart(df.set_index("Category"))

                            st.subheader("Overall Score")

                            total_score = sum(score_data.values())

                            st.progress(total_score / 100)

                            st.metric("Total Score", f"{total_score}/100")

                        except Exception:
                            st.warning("Could not parse score JSON.")

                except Exception as e:
                    st.error(f"Error: {e}")