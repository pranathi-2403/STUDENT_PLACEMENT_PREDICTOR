from flask import Flask, render_template, request, redirect, url_for, session
import os
import csv
from werkzeug.utils import secure_filename
import random
import secrets
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__, template_folder='templates')
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESET_TOKEN_EXPIRATION'] = 3600
app.config['MAIL_SERVER'] = 'smtp.example.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = 'no-reply@example.com'
latest_resume_score = None  # Stores latest resume quality score globally

# Utility functions
def user_exists(username):
    if not os.path.exists('data/loginUsers.csv'):
        return False
    with open('data/loginUsers.csv', 'r') as file:
        return any(row and row[0] == username for row in csv.reader(file))

def register_user(username, password, email):
    with open('data/loginUsers.csv', 'a', newline='') as file:
        csv.writer(file).writerow([username, password, email])

def authenticate_user(username, password):
    if not os.path.exists('data/loginUsers.csv'):
        return False
    with open('data/loginUsers.csv', 'r') as file:
        return any(row and row[0] == username and row[1] == password for row in csv.reader(file))

def get_user_email(username):
    with open('data/loginUsers.csv', 'r') as file:
        for row in csv.reader(file):
            if row and row[0] == username:
                return row[2] if len(row) > 2 else None
    return None

def update_user_password(username, new_password):
    rows = []
    with open('data/loginUsers.csv', 'r') as file:
        rows = list(csv.reader(file))
    with open('data/loginUsers.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        for row in rows:
            if row and row[0] == username:
                row[1] = new_password
            writer.writerow(row)
    return True

def generate_reset_token(username):
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(seconds=app.config['RESET_TOKEN_EXPIRATION'])
    session['reset_tokens'] = session.get('reset_tokens', {})
    session['reset_tokens'][token] = {'username': username, 'expires_at': expires_at.timestamp()}
    return token

def validate_reset_token(token):
    token_data = session.get('reset_tokens', {}).get(token)
    if not token_data or datetime.now().timestamp() > token_data['expires_at']:
        session.get('reset_tokens', {}).pop(token, None)
        return None
    return token_data['username']

def send_reset_email(email, token):
    reset_url = url_for('reset_password', token=token, _external=True)
    message = MIMEText(f"Reset your password: {reset_url}\nThis link expires in 1 hour.")
    message['Subject'] = 'Password Reset'
    message['To'] = email
    try:
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(message)
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False
import csv
import random
import os

def load_questions(filename, count=10, delimiter=','):
    questions = []
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=delimiter)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 6:
                    questions.append({
                        'question': row[0].strip(),
                        'options': [row[1].strip(), row[2].strip(), row[3].strip(), row[4].strip()],
                        'correct': row[5].strip()
                    })
    return random.sample(questions, min(count, len(questions)))

def calculate_score(request, total_questions):
    score = 0
    user_answers = {}

    for i in range(1, total_questions + 1):
        q_key = f'q{i}'
        user_answer = request.form.get(q_key)
        correct_answer = session.get(f'aptitude_q{i}_answer')

        user_answers[q_key] = {
            'selected': user_answer,
            'correct': correct_answer
        }

        if user_answer == correct_answer:
            score += 1

    session['aptitude_user_answers'] = user_answers  # Store user's selected vs correct
    return score

from pdfminer.high_level import extract_text
import docx
def calculate_resume_quality_score(text, file):
    score = 0

    # --- 1. Section Completeness ---
    sections = ['education', 'skills', 'project', 'experience', 'contact']
    found_sections = [s for s in sections if s in text.lower()]
    section_score = (len(found_sections) / len(sections)) * 2
    score += section_score

    # --- 2. Grammar and Spelling ---
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    error_rate = len(matches) / max(len(text.split()), 1)
    if error_rate < 0.01:
        score += 2
    elif error_rate < 0.03:
        score += 1.5
    elif error_rate < 0.05:
        score += 1
    else:
        score += 0.5

    # --- 3. Bullet Point Usage and Readability ---
    bullet_points = text.count("•") + text.count("- ")
    if bullet_points >= 10:
        score += 2
    elif bullet_points >= 5:
        score += 1.5
    elif bullet_points >= 2:
        score += 1
    else:
        score += 0.5

    # --- 4. Action Verbs and Tense Consistency ---
    action_verbs = ['developed', 'created', 'led', 'managed', 'analyzed', 'implemented', 'built', 'designed', 'achieved']
    verb_usage = sum(1 for verb in action_verbs if verb in text.lower())
    if verb_usage >= 8:
        score += 2
    elif verb_usage >= 5:
        score += 1.5
    elif verb_usage >= 3:
        score += 1
    else:
        score += 0.5

    # --- 5. Length and File Format ---
    ext = file.filename.rsplit('.', 1)[1].lower()
    word_count = len(text.split())
    if ext in ['pdf', 'doc', 'docx'] and 200 <= word_count <= 1200:
        score += 2
    elif word_count < 200 or word_count > 1500:
        score += 0.5
    else:
        score += 1.5

    return round(score, 1)

def extract_text_from_resume(file_path):
    if file_path.endswith('.pdf'):
        return extract_text(file_path)
    elif file_path.endswith('.docx'):
        doc = docx.Document(file_path)
        return '\n'.join([para.text for para in doc.paragraphs])
    return ""
    
def score_resume(text):
    score = 0
    keywords = ['project', 'intern', 'python', 'leadership', 'machine learning', 'communication']
    for keyword in keywords:
        if keyword.lower() in text.lower():
            score += 10
    return min(score, 100)
def calculate_readiness_score(data):
    weights = {
        'aptitude_score': 0.3,
        'technical_score': 0.4,
        'communication_score': 0.2,
        'resume_score': 0.1
    }

    # Scale test scores to percentages (0–100)
    scaled_data = {
        'aptitude_score': float(data.get('aptitude_score', 0)) * 10,
        'technical_score': float(data.get('technical_score', 0)) * 10,
        'communication_score': float(data.get('communication_score', 0)) * 10,
        'resume_score': float(data.get('resume_score', 0)) * 10  # Assuming resume score is out of 10
    }

    return min(100, max(0, sum(scaled_data.get(k, 0) * w for k, w in weights.items())))
def generate_feedback(data):
    fb = []

    # Convert scores to percentages
    aptitude = float(data.get('aptitude_score', 0)) * 10
    technical = float(data.get('technical_score', 0)) * 10
    communication = float(data.get('communication_score', 0)) * 10
    resume = float(data.get('resume_score', 0)) * 10
    certifications = int(data.get('certifications', 0))
    projects = int(data.get('projects', 0))

    # Academic performance
    if data.get('cgpa', 0) < 7.5:
        fb.append(f"Improve CGPA (current: {data['cgpa']})")
    if data.get('backlogs', 0) > 0:
        fb.append(f"Clear {data['backlogs']} backlogs to improve eligibility")

    # Skills
    if aptitude < 70:
        fb.append("Practice more aptitude questions and mock tests")
    if technical < 70:
        fb.append("Strengthen technical skills in core subjects and programming")
    if communication < 70:
        fb.append("Improve communication skills via speaking practice or mock interviews")
    # Resume Quality
    if resume < 70:
        fb.append("Improve your resume structure and content clarity")

    # Projects & Certifications
    if projects < 2:
        fb.append("Work on more technical projects to showcase hands-on skills")
    if certifications < 1:
        fb.append("Pursue relevant certifications to strengthen your profile")

    return fb or ["✅ Great work! You're on the right track. Keep going!"]

# Routes
@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        if authenticate_user(username, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        if not all([username, password, email]):
            return render_template('register.html', error="All fields ")
        if user_exists(username):
            return render_template('register.html', error="Username exists")
        register_user(username, password, email)
        return redirect(url_for('home'))
    return render_template('register.html')

def extract_resume_text(filepath):
    ext = filepath.rsplit('.', 1)[1].lower()
    if ext == 'pdf':
        with open(filepath, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            text = ' '.join(page.extract_text() or '' for page in reader.pages)
    elif ext in ['doc', 'docx']:
        text = docx2txt.process(filepath)
    else:
        text = ''
    return text
def calculate_resume_quality_score(text, file):
    score = 0

    # --- 1. Section Completeness ---
    sections = ['education', 'skills', 'project', 'experience', 'contact']
    found_sections = [s for s in sections if s in text.lower()]
    section_score = (len(found_sections) / len(sections)) * 2
    score += section_score

    # --- 2. Grammar and Spelling ---
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)
    error_rate = len(matches) / max(len(text.split()), 1)
    if error_rate < 0.01:
        score += 2
    elif error_rate < 0.03:
        score += 1.5
    elif error_rate < 0.05:
        score += 1
    else:
        score += 0.5

    # --- 3. Bullet Point Usage and Readability ---
    bullet_points = text.count("•") + text.count("- ")
    if bullet_points >= 10:
        score += 2
    elif bullet_points >= 5:
        score += 1.5
    elif bullet_points >= 2:
        score += 1
    else:
        score += 0.5

    # --- 4. Action Verbs and Tense Consistency ---
    action_verbs =[
    'managed', 'developed', 'led', 'implemented', 'designed', 'created', 'analyzed',
    # Leadership & Management
    "Spearheaded", "Orchestrated", "Supervised", "Managed", "Directed", "Facilitated", "Coordinated", "Delegated", "Oversaw", "Mentored",
    
    # Problem-Solving & Strategy
    "Engineered", "Optimized", "Transformed", "Implemented", "Resolved", "Revamped", "Innovated", "Streamlined", "Devised", "Strategized",
    
    # Development & Technical Execution
    "Developed", "Built", "Programmed", "Designed", "Executed", "Automated", "Integrated", "Debugged", "Deployed", "Configured",
    
    # Sales & Growth Performance
    "Negotiated", "Increased", "Boosted", "Secured", "Generated", "Expanded", "Achieved", "Exceeded", "Amplified", "Propelled",
    
    # Research & Data Analysis
    "Analyzed", "Evaluated", "Investigated", "Assessed", "Examined", "Formulated", "Measured", "Synthesized", "Compiled", "Diagnosed",
    
    # Communication & Collaboration
    "Presented", "Conveyed", "Articulated", "Advocated", "Consulted", "Collaborated", "Engaged", "Negotiated", "Demonstrated", "Facilitated"
]
    verb_usage = sum(1 for verb in action_verbs if verb in text.lower())
    if verb_usage >= 8:
        score += 2
    elif verb_usage >= 5:
        score += 1.5
    elif verb_usage >= 3:
        score += 1
    else:
        score += 0.5

    # --- 5. Length and File Format ---
    ext = file.filename.rsplit('.', 1)[1].lower()
    word_count = len(text.split())
    if ext in ['pdf', 'doc', 'docx'] and 200 <= word_count <= 1200:
        score += 2
    elif word_count < 200 or word_count > 1500:
        score += 0.5
    else:
        score += 1.5

    return round(score, 1)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])
import os
import docx2txt
import PyPDF2
import tempfile
import language_tool_python
from flask import request, render_template, session, redirect, url_for
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
@app.route('/upload_resume', methods=['GET', 'POST'])
def upload_resume():
    if 'username' not in session:
        return redirect(url_for('login'))

    global latest_resume_score  # Declare you're using/modifying the global variable
    resume_score = None

    if request.method == 'POST':
        file = request.files.get('resume')
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)

            text = extract_resume_text(filepath)
            resume_score = calculate_resume_quality_score(text, file)

            session['resume_score'] = resume_score
            latest_resume_score = resume_score  # ✅ Store globally

            return render_template('resume_upload.html', resume_score=resume_score)
        else:
            return render_template('resume_upload.html', resume_score=None, error="Invalid file format")

    return render_template('resume_upload.html', resume_score=session.get('resume_score'))

@app.route('/input_parameters', methods=['GET', 'POST'])
def input_parameters():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        # Debug: Print all form data
        print("Form data received:")
        for key, value in request.form.items():
            print(f"  {key}: {value}")
        
        # Get form values with proper error handling
        try:
            cgpa_value = request.form.get('cgpa', '')
            session['cgpa'] = float(cgpa_value) if cgpa_value else 0.0
            
            backlogs_value = request.form.get('backlogs', '')
            session['backlogs'] = int(backlogs_value) if backlogs_value else 0
            
            hackathons_value = request.form.get('hackathons', '')
            session['hackathons'] = int(hackathons_value) if hackathons_value else 0
            
            certificates_value = request.form.get('certificates', '')
            session['certificates'] = int(certificates_value) if certificates_value else 0
            
            internship_value = request.form.get('internship', '')
            session['internship'] = int(internship_value) if internship_value else 0
            
            projects_value = request.form.get('Projects', '')
            session['Projects'] = int(projects_value) if projects_value else 0
            
            session['Branch'] = request.form.get('Branch', '').strip()
            
            # Debug: Print session values
            print("Session values stored:")
            print(f"  CGPA: {session['cgpa']}")
            print(f"  Backlogs: {session['backlogs']}")
            print(f"  Hackathons: {session['hackathons']}")
            print(f"  Certificates: {session['certificates']}")
            print(f"  Internships: {session['internship']}")
            print(f"  Projects: {session['Projects']}")
            print(f"  Branch: {session['Branch']}")
            
        except (ValueError, TypeError) as e:
            print(f"Error processing form data: {e}")
            # Set default values if there's an error
            session['cgpa'] = 0.0
            session['backlogs'] = 0
            session['hackathons'] = 0
            session['certificates'] = 0
            session['internship'] = 0
            session['Projects'] = 0
            session['Branch'] = ''
        
        session.modified = True
        return redirect(url_for('test_confirmation'))
    return render_template('input_parameters.html')

@app.route('/test_confirmation', methods=['GET', 'POST'])
def test_confirmation():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if request.form.get('action') == 'confirm':
            return redirect(url_for('aptitude_test'))
        return redirect(url_for('input_parameters'))

    # Debug: Print session values being passed to template
    print("Session values being passed to test_confirmation template:")
    print(f"  Username: {session.get('username')}")
    print(f"  CGPA: {session.get('cgpa')}")
    print(f"  Backlogs: {session.get('backlogs')}")
    print(f"  Hackathons: {session.get('hackathons')}")
    print(f"  Certificates: {session.get('certificates')}")
    print(f"  Internships: {session.get('internship')}")
    print(f"  Projects: {session.get('Projects')}")
    print(f"  Branch: {session.get('Branch')}")

    return render_template(
        'test_confirmation.html',
        username=session.get('username'),
        cgpa=session.get('cgpa', 0),
        backlogs=session.get('backlogs', 0),
        hackathons=session.get('hackathons', 0),
        certificates=session.get('certificates', 0),
        internship=session.get('internship', 0),
        Projects=session.get('Projects', 0),       
        Branch=session.get('Branch', '')        
    )

from flask import render_template_string, redirect, url_for, session, request
@app.route('/aptitude_test', methods=['GET', 'POST'])
def aptitude_test():
    if 'username' not in session:
        return redirect(url_for('login'))

    if 'tests' not in session:
        session['tests'] = {}

    if request.method == 'POST':
        score = 0
        selected_answers = {}

        for i in range(1, 11):
            q_key = f'q{i}'
            user_answer = request.form.get(q_key)
            correct_answer = session.get(f'aptitude_q{i}_answer')

            # Debug output
            print(f"Question {i}: User answered '{user_answer}', Correct is '{correct_answer}'")

            selected_answers[q_key] = {
                'selected': user_answer,
                'correct': correct_answer
            }

            if user_answer and correct_answer and \
               user_answer.strip().upper() == correct_answer.strip().upper():
                score += 1

        # Store scores
        session['aptitude_score'] = score
        session['tests']['aptitude'] = score
        session['aptitude_answers'] = selected_answers
        session.modified = True

        print(f"Final Aptitude Score: {score}/10")
        return redirect(url_for('technical_test'))

    # Load questions with ; delimiter for aptitude
    questions = []
    try:
        with open('data/Apquestions.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=';')
            next(reader)  # Skip header
            for row in reader:
                if len(row) >= 6:
                    questions.append({
                        'question': row[0].strip(),
                        'options': [row[1].strip(), row[2].strip(), 
                                   row[3].strip(), row[4].strip()],
                        'correct': row[5].strip()  # A, B, C, or D
                    })
    except Exception as e:
        print(f"Error loading aptitude questions: {e}")
        return "Error loading test questions", 500

    questions = random.sample(questions, min(10, len(questions)))
    
    form_html = '<form method="post" id="test-form">'
    for i, question in enumerate(questions, 1):
        qname = f"q{i}"
        correct_answer_letter = question['correct']
        correct_answer_text = question['options'][ord(correct_answer_letter.upper()) - ord('A')]
        session[f'aptitude_q{i}_answer'] = correct_answer_text  # Store full answer text
        
        form_html += f'''
        <div class="question-container">
            <p class="question-text">Q{i}. {question['question']}</p>
            <div class="options-container">
        '''
        for option in question['options']:
            form_html += f'''
            <label class="option-label">
                <input type="radio" name="{qname}" value="{option}" >
                {option}
            </label>
            '''
        form_html += '</div></div>'
    form_html += '<button type="submit" class="submit-btn">Submit</button></form>'

    return render_template_string(f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Aptitude Test</title>
        <link rel="stylesheet" href="{{{{ url_for('static', filename='css/style.css') }}}}">
    </head>
    <body>
        <div class="progress-info" style="position:fixed">Time Remaining: <span id="timer">10:00</span></div>
        <div class="container">
            <h1>Aptitude Test</h1>
            {form_html}
        </div>
        <script>
            let duration = 10 * 60;
            let display = document.getElementById('timer');
            let timer = duration, minutes, seconds;
            let interval = setInterval(function () {{
                minutes = parseInt(timer / 60, 10);
                seconds = parseInt(timer % 60, 10);
                minutes = minutes < 10 ? "0" + minutes : minutes;
                seconds = seconds < 10 ? "0" + seconds : seconds;
                display.textContent = minutes + ":" + seconds;
                if (--timer < 0) {{
                    clearInterval(interval);
                    document.getElementById('test-form').submit();
                }}
            }}, 1000);
        </script>
    </body>
    </html>
    ''')


@app.route('/technical_test', methods=['GET', 'POST'])
def technical_test():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        score = 0
        selected_answers = {}

        for i in range(1, 11):
            q_key = f'q{i}'
            user_answer = request.form.get(q_key)
            correct_answer = session.get(f'technical_q{i}_answer')

            selected_answers[q_key] = {
                'selected': user_answer,
                'correct': correct_answer
            }

            if user_answer and correct_answer and \
               user_answer.strip().upper() == correct_answer.strip().upper():
                score += 1

        session['technical_score'] = score
        session['tests']['technical'] = score
        session['technical_answers'] = selected_answers
        session.modified = True

        return redirect(url_for('communication_test'))

    # Load questions with , delimiter for technical
    questions = []
    try:
        with open('data/TechnicalQuestions.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=',')
            next(reader)
            for row in reader:
                if len(row) >= 6:
                    questions.append({
                        'question': row[0].strip(),
                        'options': [row[1].strip(), row[2].strip(),
                                   row[3].strip(), row[4].strip()],
                        'correct': row[5].strip()
                    })
    except Exception as e:
        print(f"Error loading technical questions: {e}")
        return "Error loading test questions", 500

    questions = random.sample(questions, min(10, len(questions)))
    
    form_html = '<form method="post" id="test-form">'
    for i, question in enumerate(questions, 1):
        qname = f'q{i}'
        correct_answer_letter = question['correct']
        correct_answer_text = question['options'][ord(correct_answer_letter.upper()) - ord('A')]
        session[f'technical_q{i}_answer'] = correct_answer_text
        
        form_html += f'''
        <div class="question-container">
            <p class="question-text">Q{i}. {question['question']}</p>
            <div class="options-container">
        '''
        for option in question['options']:
            form_html += f'''
            <label class="option-label">
                <input type="radio" name="{qname}" value="{option}" >
                {option}
            </label>
            '''
        form_html += '</div></div>'
    form_html += '<button type="submit" class="submit-btn">Submit</button></form>'

    return render_template_string(f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Technical Test</title>
        <link rel="stylesheet" href="{{{{ url_for('static', filename='css/style.css') }}}}">
    </head>
    <body>
        <div class="progress-info" style="position:fixed">Time Remaining: <span id="timer">10:00</span></div>
        <div class="container">
            <h1>Technical Test</h1>
            {form_html}
        </div>
        <script>
            let duration = 10 * 60;
            let display = document.getElementById('timer');
            let timer = duration, minutes, seconds;
            let interval = setInterval(function () {{
                minutes = parseInt(timer / 60, 10);
                seconds = parseInt(timer % 60, 10);
                minutes = minutes < 10 ? "0" + minutes : minutes;
                seconds = seconds < 10 ? "0" + seconds : seconds;
                display.textContent = minutes + ":" + seconds;
                if (--timer < 0) {{
                    clearInterval(interval);
                    document.getElementById('test-form').submit();
                }}
            }}, 1000);
        </script>
    </body>
    </html>
    ''')


@app.route('/communication_test', methods=['GET', 'POST'])
def communication_test():
    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        score = 0
        selected_answers = {}

        for i in range(1, 11):
            q_key = f'q{i}'
            user_answer = request.form.get(q_key)
            correct_answer = session.get(f'communication_q{i}_answer')

            selected_answers[q_key] = {
                'selected': user_answer,
                'correct': correct_answer
            }

            if user_answer and correct_answer and \
               user_answer.strip().upper() == correct_answer.strip().upper():
                score += 1

        session['communication_score'] = score
        session['tests']['communication'] = score
        session['communication_answers'] = selected_answers
        session.modified = True

        return redirect(url_for('results'))

    # Load questions with , delimiter for communication
    questions = []
    try:
        with open('data/CommunicationAssess.csv', 'r', encoding='utf-8') as file:
            reader = csv.reader(file, delimiter=',')
            next(reader)
            for row in reader:
                if len(row) >= 6:
                    questions.append({
                        'question': row[0].strip(),
                        'options': [row[1].strip(), row[2].strip(),
                                   row[3].strip(), row[4].strip()],
                        'correct': row[5].strip()
                    })
    except Exception as e:
        print(f"Error loading communication questions: {e}")
        return "Error loading test questions", 500

    questions = random.sample(questions, min(10, len(questions)))
    
    form_html = '<form method="post" id="test-form">'
    for i, question in enumerate(questions, 1):
        qname = f'q{i}'
        correct_answer_letter = question['correct']
        correct_answer_text = question['options'][ord(correct_answer_letter.upper()) - ord('A')]
        session[f'communication_q{i}_answer'] = correct_answer_text
        
        form_html += f'''
        <div class="question-container">
            <p class="question-text">Q{i}. {question['question']}</p>
            <div class="options-container">
        '''
        for option in question['options']:
            form_html += f'''
            <label class="option-label">
                <input type="radio" name="{qname}" value="{option}" >
                {option}
            </label>
            '''
        form_html += '</div></div>'
    form_html += '<button type="submit" class="submit-btn">Submit</button></form>'

    return render_template_string(f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Communication Test</title>
        <link rel="stylesheet" href="{{{{ url_for('static', filename='css/style.css') }}}}">
    </head>
    <body>
        <div class="progress-info" style="position:fixed">Time Remaining: <span id="timer">10:00</span></div>
        <div class="container">
            <h1>Communication Test</h1>
            {form_html}
        </div>
        <script>
            let duration = 10 * 60;
            let display = document.getElementById('timer');
            let timer = duration, minutes, seconds;
            let interval = setInterval(function () {{
                minutes = parseInt(timer / 60, 10);
                seconds = parseInt(timer % 60, 10);
                minutes = minutes < 10 ? "0" + minutes : minutes;
                seconds = seconds < 10 ? "0" + seconds : seconds;
                display.textContent = minutes + ":" + seconds;
                if (--timer < 0) {{
                    clearInterval(interval);
                    document.getElementById('test-form').submit();
                }}
            }}, 1000);
        </script>
    </body>
    </html>
    ''')
@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('login'))

    # Get scores from session with defaults
    aptitude_score = session.get('aptitude_score', 0)
    technical_score = session.get('technical_score', 0)
    communication_score = session.get('communication_score', 0)
    resume_score = session.get('resume_score', 0)

    # Create a tests dictionary with all scores
    tests = {
        'aptitude': aptitude_score,
        'technical': technical_score,
        'communication': communication_score,
        'resume': resume_score
    }

    # Get other user data
    user_data = {
        'username': session.get('username'),
        'cgpa': session.get('cgpa', 0),
        'backlogs': session.get('backlogs', 0),
        'hackathons': session.get('hackathons', 0),
        'certificates': session.get('certificates', 0),
        'internship': session.get('internship', 0)
    }

    return render_template('results.html',
        tests=tests,
        **user_data
    )
@app.route('/final_result')
def final_result():
    if 'username' not in session:
        return redirect(url_for('login'))

    from ml_predictor import get_prediction_from_session

    prediction = get_prediction_from_session(session)

    data = {
        'cgpa': session.get('cgpa', 0),
        'backlogs': session.get('backlogs', 0),
        'certifications': session.get('certificates', 0),
        'aptitude_score': session.get('aptitude_score', 0),
        'technical_score': session.get('technical_score', 0),
        'communication_score': session.get('communication_score', 0),
        'resume_score': session.get('resume_score', 0),
    }

    readiness_score = calculate_readiness_score(data)
    feedback = generate_feedback({**data, 'resume_score': session.get('resume_score', 0)})

    return render_template('final_result.html',
                           username=session['username'],
                           readiness_score=round(readiness_score, 2),
                           feedback=feedback,
                           placement_ready=prediction['placement_ready'],
                           company_fit=prediction['company_fit'])

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

if __name__ == '__main__':
    os.makedirs('data', exist_ok=True)
    app.run(debug=True)
