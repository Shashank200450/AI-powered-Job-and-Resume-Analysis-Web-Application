import os
import re
import logging
from flask import Flask, request, jsonify, render_template, send_from_directory, send_file
from flask_cors import CORS
from flask_bcrypt import Bcrypt
import PyPDF2
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from db_adapter import DatabaseAdapter
from career_ai import get_job_requirements, get_chatbot_response

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(
    __name__,
    static_folder='static',
    template_folder='templates',
    static_url_path='/static'
)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'jobsinline-super-secret-key-2026')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

CORS(app)
bcrypt = Bcrypt(app)

# Initialize Database Adapter (MongoDB with auto-fallback to SQLite)
db = DatabaseAdapter()

# Auto-seed jobs on startup if empty
try:
    seeded_count = db.seed_jobs_if_empty()
    logger.info(f"Database initialized with {db.count_jobs()} job roles.")
except Exception as e:
    logger.error(f"Error initializing job roles: {e}")

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# ----------------- HELPER FUNCTIONS -----------------
def normalize_item_for_matching(item: str) -> str:
    return item.strip().lower()

def perform_analysis(resume_text: str, required_skills_str: str, required_frameworks_str: str):
    """Analyze resume text against required skills and frameworks"""
    required_skills = [s.strip() for s in (required_skills_str or '').split(',') if s.strip()]
    required_frameworks = [f.strip() for f in (required_frameworks_str or '').split(',') if f.strip()]

    resume_lower = resume_text.lower()

    # Skill matching
    skills_found = []
    additional_skills = []
    for skill in required_skills:
        # Match word or clean pattern
        pattern = r'(?:\b|(?<=[^a-zA-Z0-9]))' + re.escape(skill.lower()) + r'(?:\b|(?=[^a-zA-Z0-9]))'
        if re.search(pattern, resume_lower):
            skills_found.append(skill)
        else:
            additional_skills.append(skill)

    # Framework matching
    frameworks_found = []
    additional_frameworks = []
    for fw in required_frameworks:
        pattern = r'(?:\b|(?<=[^a-zA-Z0-9]))' + re.escape(fw.lower()) + r'(?:\b|(?=[^a-zA-Z0-9]))'
        if re.search(pattern, resume_lower):
            frameworks_found.append(fw)
        else:
            additional_frameworks.append(fw)

    # Calculate probabilities
    skills_prob = (len(skills_found) / len(required_skills) * 50) if required_skills else 50
    frameworks_prob = (len(frameworks_found) / len(required_frameworks) * 50) if required_frameworks else 50
    probability = min(100, max(0, round(skills_prob + frameworks_prob)))

    # Feedback messages
    missing_all = additional_skills + additional_frameworks
    if probability >= 85:
        feedback = 'Outstanding match! Your qualifications closely align with this job role.'
    elif probability >= 60:
        feedback = f'Strong profile with good foundation! To boost your score, consider adding: {", ".join(missing_all[:4])}.'
    elif probability >= 35:
        feedback = f'Moderate match. Focus on developing key skills: {", ".join(missing_all[:5])}.'
    else:
        feedback = f'Entry-level alignment. We recommend building projects involving: {", ".join(missing_all[:5])}.'

    return {
        'probability': probability,
        'skillsFound': skills_found,
        'frameworksFound': frameworks_found,
        'additionalSkills': ', '.join(additional_skills) if additional_skills else 'None',
        'additionalFrameworks': ', '.join(additional_frameworks) if additional_frameworks else 'None',
        'missingSkillsList': additional_skills,
        'missingFrameworksList': additional_frameworks,
        'feedback': feedback
    }

def extract_text_from_pdf(file_storage) -> str:
    """Extract full text from uploaded PDF file storage object"""
    reader = PyPDF2.PdfReader(file_storage)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

# ----------------- PAGE ROUTES -----------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/index.html')
def index_page():
    return render_template('index.html')

@app.route('/main.html')
def main_page():
    return render_template('main.html')

@app.route('/api/sample_resume')
def download_sample_resume():
    """Serves the generated sample resume PDF for 1-click testing"""
    sample_path = os.path.join(app.static_folder, 'sample_resume.pdf')
    if not os.path.exists(sample_path):
        from generate_sample import generate_sample_resume
        generate_sample_resume(sample_path)
    return send_file(sample_path, mimetype='application/pdf', as_attachment=False, download_name='sample_resume.pdf')

# ----------------- AUTH ROUTE -----------------
@app.route('/auth', methods=['POST'])
def auth():
    req = request.get_json() or {}
    action = req.get('action')
    username = (req.get('username') or '').strip()
    password = req.get('password') or ''

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    if action == 'login':
        user = db.find_user(username)
        if not user:
            return jsonify({'success': False, 'message': 'Username not found! Please register first.', 'redirect': 'register'}), 404
        
        try:
            is_valid = bcrypt.check_password_hash(user['Password'], password)
        except Exception:
            # Fallback for plain-text legacy passwords if any
            is_valid = (user['Password'] == password)

        if not is_valid:
            return jsonify({'success': False, 'message': 'Incorrect password. Please try again.'}), 401

        return jsonify({'success': True, 'message': f'Welcome back, {user["Username"]}!', 'redirect': 'main', 'username': user['Username']})

    elif action == 'register':
        email = (req.get('email') or '').strip()
        phone = (req.get('phone') or '').strip()

        if db.find_user(username):
            return jsonify({'success': False, 'message': f'Username "{username}" already exists. Please pick another or log in.'}), 400

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        created = db.create_user(username, email, phone, hashed_password)
        if created:
            return jsonify({'success': True, 'message': 'Account created successfully! You can now log in.'}), 201
        else:
            return jsonify({'success': False, 'message': 'Registration failed. Username may already exist.'}), 400

    else:
        return jsonify({'success': False, 'message': 'Invalid authentication action specified.'}), 400

# ----------------- RESUME ANALYSIS ROUTE -----------------
@app.route('/upload', methods=['POST'])
def upload():
    if 'resume' not in request.files or 'jobRole' not in request.form:
        return jsonify({'success': False, 'error': 'Please provide both a job role and a PDF resume.'}), 400

    file = request.files['resume']
    job_role = request.form.get('jobRole', '').strip()

    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected. Please choose a PDF file.'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Only PDF files (.pdf) are supported.'}), 400

    try:
        resume_text = extract_text_from_pdf(file)
        if not resume_text:
            return jsonify({'success': False, 'error': 'Unable to extract text from PDF. Ensure the PDF is not an image-only scan.'}), 400

        # Look up job in database
        job_data = db.find_job(job_role)
        if job_data:
            required_skills = job_data.get('PROGRAMMING SKILLS', '')
            required_frameworks = job_data.get('FRAMEWORKS', '')
        else:
            # Fallback to AI or local knowledge base
            logger.info(f"Job role '{job_role}' not in DB. Querying Career AI...")
            required_skills, required_frameworks = get_job_requirements(job_role, GOOGLE_API_KEY)
            # Cache it for future requests
            try:
                db.insert_job(job_role, required_skills, required_frameworks)
            except Exception as e:
                logger.warning(f"Could not cache job '{job_role}': {e}")

        analysis = perform_analysis(resume_text, required_skills, required_frameworks)

        return jsonify({
            'success': True,
            'jobRole': job_role,
            'probability': analysis['probability'],
            'skillsFound': analysis['skillsFound'],
            'frameworksFound': analysis['frameworksFound'],
            'additionalSkills': analysis['additionalSkills'],
            'additionalFrameworks': analysis['additionalFrameworks'],
            'missingSkillsList': analysis['missingSkillsList'],
            'missingFrameworksList': analysis['missingFrameworksList'],
            'feedback': analysis['feedback']
        })

    except Exception as e:
        logger.error(f"Error during resume upload analysis: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'An error occurred during resume analysis.', 'details': str(e)}), 500

# ----------------- RELATED JOBS ROUTE -----------------
@app.route('/related_jobs', methods=['POST'])
def related_jobs():
    file = request.files.get('resume') or request.files.get('relatedResume')
    if not file or file.filename == '':
        return jsonify({'success': False, 'error': 'Please upload a PDF resume.'}), 400

    if not file.filename.lower().endswith('.pdf'):
        return jsonify({'success': False, 'error': 'Only PDF files (.pdf) are supported.'}), 400

    try:
        resume_text = extract_text_from_pdf(file)
        if not resume_text:
            return jsonify({'success': False, 'error': 'Unable to extract text from PDF. The file may be an image scan.'}), 400

        all_jobs = db.get_all_jobs()
        if not all_jobs:
            # Try to reseed
            db.seed_jobs_if_empty()
            all_jobs = db.get_all_jobs()

        if not all_jobs:
            return jsonify({'success': False, 'error': 'No job roles found in database.'}), 500

        matches = []
        for job in all_jobs:
            job_title = job.get('JOB ROLES', '').strip()
            skills = job.get('PROGRAMMING SKILLS', '')
            frameworks = job.get('FRAMEWORKS', '')
            if not job_title:
                continue

            analysis = perform_analysis(resume_text, skills, frameworks)
            matches.append({
                'jobRole': job_title,
                'probability': analysis['probability'],
                'skillsFound': analysis['skillsFound'],
                'frameworksFound': analysis['frameworksFound'],
                'additionalSkills': analysis['additionalSkills'],
                'additionalFrameworks': analysis['additionalFrameworks']
            })

        # Sort by match probability descending
        matches.sort(key=lambda x: x['probability'], reverse=True)

        return jsonify({
            'success': True,
            'count': len(matches),
            'relatedJobs': matches[:15]  # Top 15 best matches
        })

    except Exception as e:
        logger.error(f"Error finding related jobs: {e}", exc_info=True)
        return jsonify({'success': False, 'error': 'Error processing related jobs search.', 'details': str(e)}), 500

@app.route('/find_jobs', methods=['POST'])
def find_jobs():
    return related_jobs()

# ----------------- CHATBOT ROUTE -----------------
@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.get_json() or {}
    message = data.get('message', '').strip()

    if not message:
        return jsonify({'success': False, 'error': 'Please provide a message.'}), 400

    try:
        reply = get_chatbot_response(message, GOOGLE_API_KEY)
        return jsonify({'success': True, 'response': reply})
    except Exception as e:
        logger.error(f"Error in chatbot endpoint: {e}", exc_info=True)
        return jsonify({'success': True, 'response': "I am here to help you optimize your resume, understand job skills, and prepare for interviews! Feel free to ask a question."})

# ----------------- DIAGNOSTIC & HEALTH ROUTE -----------------
@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'database_engine': db.engine,
        'job_roles_count': db.count_jobs(),
        'ai_configured': bool(GOOGLE_API_KEY)
    })

@app.route('/debug/job_roles', methods=['GET'])
def debug_job_roles():
    jobs = db.get_all_jobs()
    return jsonify({
        'success': True,
        'total': len(jobs),
        'roles': [j.get('JOB ROLES') for j in jobs[:25]]
    })

# ----------------- ERROR HANDLERS -----------------
@app.errorhandler(404)
def not_found(e):
    if request.path.startswith(('/auth', '/upload', '/related_jobs', '/chatbot', '/api')):
        return jsonify({'success': False, 'error': 'Endpoint not found'}), 404
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'false').lower() in ('1', 'true')
    print(f"Starting JOBSINLINE server on http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)