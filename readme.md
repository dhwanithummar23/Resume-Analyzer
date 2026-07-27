# 🤖 AI-Powered Resume Analyzer

An AI-powered Resume Analyzer built with **Streamlit** and **Google Gemini AI** that analyzes resumes, extracts key information, evaluates resume quality, and provides personalized suggestions for improvement.

It helps students, freshers, and professionals optimize their resumes for better ATS (Applicant Tracking System) compatibility and job opportunities.

---

## 📌 Features

- 📄 Upload Resume in PDF format
- 📝 Automatic Resume Text Extraction
- 🤖 AI-powered Resume Analysis using Google Gemini
- 📋 Professional Resume Summary
- 🛠️ Key Skills Extraction
- 💡 Resume Improvement Suggestions
- 📊 Resume Scoring (Out of 100)
- 📈 Category-wise Performance Breakdown
- 🎯 ATS-Friendly Resume Evaluation
- 🎨 Clean and Responsive Streamlit UI

---

## 🛠️ Tech Stack

### Frontend

- Streamlit
- HTML
- CSS

### Backend

- Python

### AI Model

- Google Gemini API

### Libraries

- PyPDF2
- python-dotenv
- Pandas
- Regular Expressions (re)

---

## 📂 Project Structure

```
Resume-Analyzer/
│
├── styles/
│   └── style.css
│
├── main.py
├── main2.py
├── .env
├── .gitignore
└── README.md
```

---

## ⚙️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/your-username/resume-analyzer.git
```

```bash
cd resume-analyzer
```

---

### 2. Create Virtual Environment

Windows

```bash
python -m venv venv
```

Activate

```bash
venv\Scripts\activate
```

---

### 3. Install Dependencies

```bash
pip install streamlit google-genai PyPDF2 python-dotenv pandas
```

---

### 4. Create Environment Variable

Create a file named:

```
.env
```

Add your Gemini API Key

```env
GEMINI_API_KEY=YOUR_API_KEY
```

Get your API Key from:

https://aistudio.google.com/

---

### 5. Run the Project

```bash
streamlit run main2.py
```

---

## 🚀 How It Works

1. Upload a Resume (PDF)
2. Resume text is extracted using PyPDF2.
3. The extracted text is cleaned and processed.
4. Google Gemini analyzes the resume.
5. The application generates:
   - Resume Summary
   - Key Skills
   - Improvement Suggestions
   - Resume Score
6. Results are displayed in an interactive dashboard.

---

## 📊 Resume Evaluation Criteria

| Category                  |   Marks |
| ------------------------- | ------: |
| Skills Match              |      30 |
| Experience & Achievements |      30 |
| Clarity & Formatting      |      20 |
| Overall Impression        |      20 |
| **Total**                 | **100** |

---
