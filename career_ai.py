import os
import re
import logging
import requests

logger = logging.getLogger(__name__)

# Fallback skills and frameworks for popular careers
ROLE_KNOWLEDGE_BASE = {
    "software engineer": {
        "skills": "Java, Python, C++, Data Structures, Algorithms, SQL",
        "frameworks": "Spring Boot, Django, Flask, Node.js"
    },
    "frontend developer": {
        "skills": "HTML5, CSS3, JavaScript, TypeScript, Responsive Design",
        "frameworks": "React, Vue.js, Angular, Next.js, Tailwind CSS"
    },
    "backend developer": {
        "skills": "Python, Java, Node.js, Go, SQL, PostgreSQL, MongoDB, REST APIs",
        "frameworks": "Django, Flask, FastAPI, Spring Boot, Express.js"
    },
    "full stack developer": {
        "skills": "HTML, CSS, JavaScript, TypeScript, Python, SQL, Git",
        "frameworks": "React, Node.js, Express, MongoDB, PostgreSQL, Next.js"
    },
    "data scientist": {
        "skills": "Python, R, SQL, Statistics, Machine Learning, Data Visualization",
        "frameworks": "TensorFlow, PyTorch, Scikit-Learn, Pandas, NumPy"
    },
    "machine learning engineer": {
        "skills": "Python, C++, Linear Algebra, Calculus, Deep Learning, MLOps",
        "frameworks": "PyTorch, TensorFlow, Keras, MLflow, Hugging Face"
    },
    "devops engineer": {
        "skills": "Linux, Shell Scripting, Python, CI/CD, Networking, Docker, Kubernetes",
        "frameworks": "Terraform, Ansible, Jenkins, GitHub Actions, AWS, Azure"
    },
    "cloud architect": {
        "skills": "AWS, Azure, GCP, Cloud Security, System Architecture, Networking",
        "frameworks": "Terraform, CloudFormation, Kubernetes, Serverless"
    },
    "android developer": {
        "skills": "Kotlin, Java, Android SDK, SQLite, XML, Jetpack",
        "frameworks": "Android Jetpack, Retrofit, Coroutines, Compose"
    },
    "ios developer": {
        "skills": "Swift, Objective-C, iOS SDK, CoreData, Xcode",
        "frameworks": "SwiftUI, UIKit, Combine, Alamofire"
    },
    "cybersecurity analyst": {
        "skills": "Network Security, Penetration Testing, Python, Linux, Cryptography",
        "frameworks": "Wireshark, Metasploit, SIEM, Splunk, Kali Linux"
    }
}

CAREER_ADVICE_INTENTS = [
    (
        r'\b(ats|applicant tracking|format|format resume|resume tips|improve resume)\b',
        "Here are top ATS resume tips: 1) Use a single-column, clean layout. 2) Tailor your bullet points with action verbs and quantifiable metrics (e.g. 'Boosted performance by 35%'). 3) Include relevant keywords from the job description directly in your skills and project sections."
    ),
    (
        r'\b(interview|prepare for interview|interview questions|mock interview)\b',
        "To ace your technical interview: 1) Practice core DSA (Arrays, HashMaps, Trees, DP) on LeetCode. 2) Master the STAR method (Situation, Task, Action, Result) for behavioral questions. 3) Prepare 2-3 deep-dive explanations for your top projects highlighting architecture trade-offs."
    ),
    (
        r'\b(salary|negotiat|raise|compensation)\b',
        "Salary negotiation tip: Research market benchmarks on Levels.fyi or Glassdoor. Never give a single number first; provide a well-researched range and emphasize the high-impact value you bring to the team."
    ),
    (
        r'\b(full stack|frontend|backend|roadmap|learn)\b',
        "For web development: Start with strong JavaScript/TypeScript fundamentals. On the frontend, master React or Vue. On the backend, pick Node.js/Express or Python/Django with relational (PostgreSQL) and NoSQL (MongoDB) databases."
    ),
    (
        r'\b(data science|machine learning|ai|deep learning)\b',
        "For Data Science & AI: Build a strong foundation in Python (NumPy, Pandas), statistics, and core ML algorithms with Scikit-learn before jumping to deep learning with PyTorch. Real-world end-to-end projects with clean deployment make you stand out."
    ),
    (
        r'\b(jobsinline|how to use|features|help)\b',
        "JOBSINLINE helps you optimize your career path! You can: 1) Analyze your resume against a specific target role. 2) Discover related job matches with compatibility scores. 3) Ask me any career, resume, or interview questions!"
    ),
    (
        r'\b(hello|hi|hey|greetings)\b',
        "Hello! I am your JOBSINLINE Career Assistant. Ask me anything about resume improvements, interview preparation, tech skills, or how your profile matches job roles!"
    )
]

def get_job_requirements(job_role: str, google_api_key: str = ""):
    """Fetch skills and frameworks using Gemini if key exists, otherwise fallback to local knowledge base"""
    job_lower = job_role.lower().strip()

    # 1. Try Gemini if key is provided
    if google_api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={google_api_key}"
            prompt = (
                f"Provide the core programming languages (skills) and frameworks required for the job role '{job_role}'. "
                f"Respond strictly in this format: - Skills: skill1, skill2, skill3 - Frameworks: framework1, framework2"
            )
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                text = data['candidates'][0]['content']['parts'][0]['text']
                skills_match = re.search(r'Skills:\s*([^\n\r]+)', text, re.I)
                frameworks_match = re.search(r'Frameworks:\s*([^\n\r]+)', text, re.I)
                skills = skills_match.group(1).strip() if skills_match else ""
                frameworks = frameworks_match.group(1).strip() if frameworks_match else ""
                if skills:
                    return skills, frameworks
        except Exception as e:
            logger.warning(f"Gemini API request failed: {e}. Using fallback.")

    # 2. Local knowledge base lookup
    for role_key, data in ROLE_KNOWLEDGE_BASE.items():
        if role_key in job_lower or job_lower in role_key:
            return data["skills"], data["frameworks"]

    # 3. Generic fallback
    return "Problem Solving, Data Structures, Git, Software Design, Communication", "Agile, CI/CD, Cloud Platforms"

def get_chatbot_response(message: str, google_api_key: str = ""):
    """Respond to user career queries with Gemini or intelligent counselor fallback"""
    clean_msg = message.strip()
    if not clean_msg:
        return "Please ask a question regarding your resume, job roles, or career preparation!"

    # 1. Try Gemini API if key is available
    if google_api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={google_api_key}"
            prompt = (
                f"You are a professional career coach and resume analyst for the JOBSINLINE platform. "
                f"Give a concise, helpful, friendly, and well-structured answer (2-4 sentences max) to: {clean_msg}"
            )
            resp = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=6)
            if resp.status_code == 200:
                data = resp.json()
                text = data['candidates'][0]['content']['parts'][0]['text'].strip()
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text)
                return text
        except Exception as e:
            logger.warning(f"Gemini Chatbot request failed: {e}. Using career advisor fallback.")

    # 2. Intelligent local career advisor fallback
    for pattern, response in CAREER_ADVICE_INTENTS:
        if re.search(pattern, clean_msg, re.IGNORECASE):
            return response

    return (
        f"Regarding '{clean_msg}': To stand out for this, highlight tangible achievements in your projects, "
        "ensure your top technical skills match industry standards, and practice explaining your architectural decisions clearly."
    )
