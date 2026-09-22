# 💼 AI-powered Job and Resume Analysis Web Application

JOBSINLINE is a full-stack Python (Flask) and modern responsive web application designed for intelligent resume parsing, ATS compatibility matching, 170+ job role discovery, and AI career coaching.

---

## 🌟 Key Features

- **ATS Resume Analyzer**: Upload any PDF resume and match it against target job roles with animated compatibility percentage scores.
- **Skill Gap Detection**: Distinguishes between matched skills, missing programming languages, and framework competencies to guide candidate improvement.
- **Related Jobs Discovery**: Scans across 170+ curated tech positions in the database to rank the top job opportunities tailored to the candidate's exact profile.
- **Career AI Assistant**: Answers questions on ATS optimization, technical interview strategies, salary negotiations, and learning roadmaps. Integrates Google Gemini with built-in intelligent fallback.
- **Zero-Config Resilient Database**: Automatically connects to MongoDB (Atlas / local) if available, with zero-setup automatic fallback to an embedded SQLite database (`jobsinline.db`) and automatic seeding from `jobrolespskillsframeworks.xlsx`.
- **1-Click Demo Testing**: Includes built-in sample resume generation for instantaneous testing without needing a PDF on hand.
- **Modern Responsive UI**: Dark glassmorphism interface, smooth sliding auth panels, non-blocking toast notifications, and animated progress visualizers.

---

## 🚀 How to Run Locally

### Option 1: Quick Start (Windows)
Double-click `run.bat` or run:
```powershell
.\run.ps1
```

### Option 2: Manual Start
1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
2. **Start the Web Application**:
   ```bash
   python app.py
   ```
3. **Open in Browser**:
   Navigate to: [http://127.0.0.1:5000](http://127.0.0.1:5000)

---

## ☁️ Deployment Guide

### Deploying to Render (Recommended - Free Web Service)
1. Push this repository to GitHub.
2. Go to [Render Dashboard](https://dashboard.render.com/) -> **New Web Service**.
3. Select your repository.
4. Set:
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt && python -c "from generate_sample import generate_sample_resume; generate_sample_resume()"`
   - **Start Command**: `gunicorn app:app --bind 0.0.0.0:$PORT`
5. (Optional) Set Environment Variables:
   - `MONGO_URI`: Your MongoDB Atlas connection string (or leave empty to use SQLite).
   - `GOOGLE_API_KEY`: Your Google Gemini API Key (or leave empty to use smart local AI fallback).
6. Click **Deploy Web Service**!

### Deploying with Docker
Build and run the container:
```bash
docker build -t jobsinline .
docker run -p 5000:5000 jobsinline
```
Or run full stack with MongoDB via Docker Compose:
```bash
docker-compose up --build
```

---

## 📁 Project Structure

```
JOBSINLINE/
├── app.py                         # Main Flask web application & REST API
├── db_adapter.py                  # Dual-engine database adapter (MongoDB + SQLite)
├── career_ai.py                   # Career AI coach & requirements generator
├── generate_sample.py             # Sample resume PDF generator
├── jobrolespskillsframeworks.xlsx # Curated database of 170+ tech roles
├── migrate_data.py                # Standalone data migration script
├── templates/
│   ├── index.html                 # Login & Registration page
│   └── main.html                  # Dashboard & Analyzer page
├── static/
│   ├── sign_up_styles.css         # Modern glassmorphism design system
│   ├── signup.js                  # Authentication & toast controller
│   ├── main.js                    # Dashboard, dropzone, & chatbot controller
│   └── sample_resume.pdf          # Generated sample resume for demo
├── Dockerfile                     # Container deployment specification
├── docker-compose.yml             # Container composition with MongoDB
├── Procfile                       # Heroku / Render process runner
├── render.yaml                    # Render blueprint
├── requirements.txt               # Production Python dependencies
├── .env.example                   # Documented environment template
├── run.bat                        # Windows 1-click batch launcher
└── run.ps1                        # PowerShell launcher
```
