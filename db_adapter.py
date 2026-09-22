import os
import re
import sqlite3
import logging
from pymongo import MongoClient
import pandas as pd

logger = logging.getLogger(__name__)

def standardize_job_name(job_name: str) -> str:
    """Standardize job names for fuzzy/flexible matching"""
    if not job_name:
        return ""
    # Convert to lowercase and remove special characters
    standardized = re.sub(r'[^\w\s]', '', job_name.lower().strip())
    # Remove common suffixes/prefixes
    standardized = re.sub(r'\b(senior|junior|lead|principal|intern|associate)\b', '', standardized)
    standardized = re.sub(r'\b(i|ii|iii|iv|v)\b', '', standardized)
    # Remove extra spaces
    standardized = re.sub(r'\s+', ' ', standardized).strip()
    return standardized

class DatabaseAdapter:
    def __init__(self, mongo_uri=None, db_path='jobsinline.db'):
        self.mongo_uri = mongo_uri or os.environ.get('MONGO_URI', 'mongodb://localhost:27017/')
        self.db_path = db_path
        self.engine = 'sqlite'
        self.mongo_client = None
        self.mongo_db = None
        self.users_col = None
        self.jobs_col = None

        self._init_connection()

    def _init_connection(self):
        # Attempt MongoDB connection with 1.5s timeout
        try:
            client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=1500)
            client.admin.command('ping')
            self.mongo_client = client
            self.mongo_db = client['jobsinline']
            self.users_col = self.mongo_db['users']
            self.jobs_col = self.mongo_db['job_roles_data']
            self.engine = 'mongo'
            logger.info(f"Connected to MongoDB at {self.mongo_uri}")
        except Exception as e:
            logger.warning(f"MongoDB not available ({e}). Falling back to SQLite: {self.db_path}")
            self.engine = 'sqlite'
            self._init_sqlite()

    def _init_sqlite(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                phone TEXT,
                password TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS job_roles_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_role TEXT NOT NULL,
                standardized_job_role TEXT NOT NULL,
                programming_skills TEXT,
                frameworks TEXT
            )
        ''')
        conn.commit()
        conn.close()

    def _get_sqlite_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ------------------ USER METHODS ------------------
    def find_user(self, username):
        if not username:
            return None
        if self.engine == 'mongo':
            user = self.users_col.find_one({'Username': username})
            if user:
                return {
                    'Username': user.get('Username'),
                    'Password': user.get('Password'),
                    'Email': user.get('Email', ''),
                    'Phone': user.get('Phone', '')
                }
            return None
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT username, password, email, phone FROM users WHERE LOWER(username) = LOWER(?)', (username,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'Username': row['username'],
                    'Password': row['password'],
                    'Email': row['email'],
                    'Phone': row['phone']
                }
            return None

    def create_user(self, username, email, phone, hashed_password):
        if self.engine == 'mongo':
            self.users_col.insert_one({
                'Username': username,
                'Email': email,
                'Phone': phone,
                'Password': hashed_password
            })
            return True
        else:
            try:
                conn = self._get_sqlite_conn()
                cursor = conn.cursor()
                cursor.execute(
                    'INSERT INTO users (username, email, phone, password) VALUES (?, ?, ?, ?)',
                    (username, email, phone, hashed_password)
                )
                conn.commit()
                conn.close()
                return True
            except sqlite3.IntegrityError:
                return False

    # ------------------ JOB METHODS ------------------
    def count_jobs(self):
        if self.engine == 'mongo':
            return self.jobs_col.count_documents({})
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM job_roles_data')
            count = cursor.fetchone()[0]
            conn.close()
            return count

    def get_all_jobs(self):
        if self.engine == 'mongo':
            docs = list(self.jobs_col.find({}))
            results = []
            for d in docs:
                results.append({
                    'JOB ROLES': d.get('JOB ROLES', ''),
                    'standardized_job_role': d.get('standardized_job_role', ''),
                    'PROGRAMMING SKILLS': d.get('PROGRAMMING SKILLS', ''),
                    'FRAMEWORKS': d.get('FRAMEWORKS', '')
                })
            return results
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT job_role, standardized_job_role, programming_skills, frameworks FROM job_roles_data')
            rows = cursor.fetchall()
            conn.close()
            results = []
            for r in rows:
                results.append({
                    'JOB ROLES': r['job_role'],
                    'standardized_job_role': r['standardized_job_role'],
                    'PROGRAMMING SKILLS': r['programming_skills'],
                    'FRAMEWORKS': r['frameworks']
                })
            return results

    def insert_job(self, job_role, programming_skills, frameworks):
        standardized = standardize_job_name(job_role)
        if self.engine == 'mongo':
            self.jobs_col.insert_one({
                'JOB ROLES': job_role,
                'standardized_job_role': standardized,
                'PROGRAMMING SKILLS': programming_skills,
                'FRAMEWORKS': frameworks
            })
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO job_roles_data (job_role, standardized_job_role, programming_skills, frameworks) VALUES (?, ?, ?, ?)',
                (job_role, standardized, programming_skills, frameworks)
            )
            conn.commit()
            conn.close()

    def find_job(self, job_role):
        if not job_role:
            return None
        standardized_input = standardize_job_name(job_role)

        if self.engine == 'mongo':
            # Exact match on standardized
            job = self.jobs_col.find_one({'standardized_job_role': standardized_input})
            if job:
                return {
                    'JOB ROLES': job.get('JOB ROLES'),
                    'standardized_job_role': job.get('standardized_job_role'),
                    'PROGRAMMING SKILLS': job.get('PROGRAMMING SKILLS', ''),
                    'FRAMEWORKS': job.get('FRAMEWORKS', '')
                }
            # Partial match
            words = standardized_input.split()
            for word in words:
                if len(word) > 3:
                    job = self.jobs_col.find_one({'standardized_job_role': {'$regex': word, '$options': 'i'}})
                    if job:
                        return {
                            'JOB ROLES': job.get('JOB ROLES'),
                            'standardized_job_role': job.get('standardized_job_role'),
                            'PROGRAMMING SKILLS': job.get('PROGRAMMING SKILLS', ''),
                            'FRAMEWORKS': job.get('FRAMEWORKS', '')
                        }
            return None
        else:
            conn = self._get_sqlite_conn()
            cursor = conn.cursor()
            cursor.execute('SELECT job_role, standardized_job_role, programming_skills, frameworks FROM job_roles_data WHERE standardized_job_role = ?', (standardized_input,))
            row = cursor.fetchone()
            if row:
                conn.close()
                return {
                    'JOB ROLES': row['job_role'],
                    'standardized_job_role': row['standardized_job_role'],
                    'PROGRAMMING SKILLS': row['programming_skills'],
                    'FRAMEWORKS': row['frameworks']
                }
            # Partial word matching
            words = standardized_input.split()
            for word in words:
                if len(word) > 3:
                    cursor.execute('SELECT job_role, standardized_job_role, programming_skills, frameworks FROM job_roles_data WHERE standardized_job_role LIKE ?', (f'%{word}%',))
                    row = cursor.fetchone()
                    if row:
                        conn.close()
                        return {
                            'JOB ROLES': row['job_role'],
                            'standardized_job_role': row['standardized_job_role'],
                            'PROGRAMMING SKILLS': row['programming_skills'],
                            'FRAMEWORKS': row['frameworks']
                        }
            conn.close()
            return None

    def seed_jobs_if_empty(self, excel_path='jobrolespskillsframeworks.xlsx'):
        try:
            count = self.count_jobs()
            if count > 0:
                logger.info(f"Database already contains {count} job roles.")
                return count

            if not os.path.exists(excel_path):
                logger.warning(f"Excel file {excel_path} not found for seeding.")
                return 0

            logger.info(f"Seeding database from {excel_path}...")
            df = pd.read_excel(excel_path)
            
            # Clean dataframe
            df['JOB ROLES'] = df['JOB ROLES'].astype(str).str.strip()
            df['PROGRAMMING SKILLS'] = df['PROGRAMMING SKILLS'].fillna('').astype(str).str.strip()
            df['FRAMEWORKS'] = df['FRAMEWORKS'].fillna('').astype(str).str.strip()
            df['standardized_job_role'] = df['JOB ROLES'].apply(standardize_job_name)

            if self.engine == 'mongo':
                records = df.to_dict('records')
                self.jobs_col.insert_many(records)
                logger.info(f"Inserted {len(records)} job roles into MongoDB.")
                return len(records)
            else:
                conn = self._get_sqlite_conn()
                cursor = conn.cursor()
                rows = [
                    (row['JOB ROLES'], row['standardized_job_role'], row['PROGRAMMING SKILLS'], row['FRAMEWORKS'])
                    for _, row in df.iterrows()
                ]
                cursor.executemany(
                    'INSERT INTO job_roles_data (job_role, standardized_job_role, programming_skills, frameworks) VALUES (?, ?, ?, ?)',
                    rows
                )
                conn.commit()
                conn.close()
                logger.info(f"Inserted {len(rows)} job roles into SQLite.")
                return len(rows)
        except Exception as e:
            logger.error(f"Error seeding database: {e}")
            return 0
