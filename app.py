"""
AI Project Idea Duplicate Detector & Entity Resolution System (SRM-AIDRS)
Flask Web Application & REST API Server.
SRMIST | B.Tech CSE (AI) | Guide: Dr. S.P. Ramya
Team: Sudhan Babu, Keerthi Vasaa, Dayanandan
"""
import os
import json
import socket
from datetime import datetime
from functools import wraps
from flask import (
    Flask, render_template, request, redirect, url_for,
    session, jsonify, flash, send_from_directory
)
from flask_cors import CORS
from werkzeug.utils import secure_filename

import database as db
from nlp_engine import engine, extract_entities, highlight_overlapping_phrases
from file_extractor import extract_text_from_document

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'srmist-ai-duplicate-detector-2026-secret-token')
CORS(app)

# Auto-initialize database and seed on startup if empty
try:
    db.init_db()
    _stats = db.get_dashboard_statistics()
    if _stats['total_projects'] == 0:
        from seed_data import seed_database
        seed_database()
except Exception as _e:
    print(f"[!] Startup DB initialization note: {_e}")

# Uploads Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc', 'txt'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024 # 32 MB max file size

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Authorized Core Personnel
AUTHORIZED_PERSONNEL = {
    'ramya.guide': {'name': 'Dr. S.P. Ramya', 'role': 'faculty', 'title': 'Project Guide & Coordinator'},
    'sudhan': {'name': 'Sudhan Babu', 'role': 'student', 'reg_no': 'RA2411047050032', 'title': 'Team Lead'},
    'keerthi': {'name': 'Keerthi Vasaa', 'role': 'student', 'reg_no': 'RA2411047050041', 'title': 'Team Member'},
    'dayanandan': {'name': 'Dayanandan', 'role': 'student', 'reg_no': 'RA2411047050029', 'title': 'Team Member'}
}

# Helper to detect local LAN IP
def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

PUBLIC_URL = os.environ.get('PUBLIC_URL', 'https://supplemental-combinations-hollow-competing.trycloudflare.com')

# Authentication Decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Access Restricted: Please sign in as Project Guide (Dr. S.P. Ramya) or Team Member (Sudhan Babu, Keerthi Vasaa, Dayanandan) to access this module.", "warning")
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Context processor for templates
@app.context_processor
def inject_global_data():
    user = None
    is_authorized = False
    if 'user_id' in session:
        user = db.get_user_by_id(session['user_id'])
        if user and (user['role'] == 'faculty' or user['username'] in AUTHORIZED_PERSONNEL):
            is_authorized = True

    lan_ip = get_host_ip()
    return {
        'current_user': user,
        'is_authorized': is_authorized,
        'lan_ip': lan_ip,
        'port': 5000,
        'public_url': PUBLIC_URL,
        'guide_name': 'Dr. S.P. Ramya',
        'team_lead': 'Sudhan Babu (RA2411047050032)',
        'department': 'Artificial Intelligence - 3rd Year',
        'institution': 'SRM Institute of Science and Technology'
    }

# ----------------- Navigation Views ----------------- #

@app.route('/')
def index():
    user_logged_in = 'user_id' in session
    stats = db.get_dashboard_statistics()

    # Only load internal project cards if logged in as Guide or Team Member
    recent_projects = []
    high_matches = []
    if user_logged_in:
        recent_projects = db.get_all_projects()[:6]
        high_matches = db.get_high_risk_matches()[:4]

    return render_template(
        'index.html',
        stats=stats,
        recent_projects=recent_projects,
        high_matches=high_matches,
        user_logged_in=user_logged_in
    )

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        user = db.authenticate_user(username, password)
        if user:
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']
            session['username'] = user['username']
            flash(f"Welcome back, {user['name']}!", "success")
            
            next_url = request.args.get('next')
            if next_url:
                return redirect(next_url)
            if user['role'] == 'faculty':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('my_submissions'))
        else:
            flash("Invalid credentials. Please verify username and password.", "error")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out safely.", "info")
    return redirect(url_for('index'))

@app.route('/submit', methods=['GET', 'POST'])
def submit_project():
    """
    Submission Portal: Asks ONLY:
    - Project Title
    - Domain / Specialization
    - Lead Register Number
    - Submitter Name
    - Team Members (Names & Reg Nos)
    - Abstract & Problem Statement
    - Option for uploading project idea as PDF, Word (.docx/.doc), or TXT
    """
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        domain = request.form.get('domain', '').strip()
        reg_no = request.form.get('reg_no', '').strip()
        submitted_by_name = request.form.get('submitted_by_name', '').strip()
        team_members = request.form.get('team_members', '').strip()
        abstract = request.form.get('abstract', '').strip()

        if not title or not domain or not reg_no or not submitted_by_name:
            flash("Please fill in all required fields (Title, Domain, Reg No, Submitter Name).", "error")
            return render_template('submit.html')

        # Handle File Upload (PDF, Word, TXT)
        uploaded_file = None
        file_path = None
        extracted_text = ""

        if 'proposal_file' in request.files:
            file = request.files['proposal_file']
            if file and file.filename and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                timestamp_str = datetime.now().strftime('%Y%m%d_%H%M%S')
                saved_filename = f"{timestamp_str}_{original_filename}"
                saved_path = os.path.join(app.config['UPLOAD_FOLDER'], saved_filename)
                file.save(saved_path)

                uploaded_file = original_filename
                file_path = saved_path
                # Extract text content from PDF / Word document
                extracted_text = extract_text_from_document(saved_path)

        # Combine abstract with extracted document text for comprehensive semantic analysis
        combined_content = abstract
        if extracted_text:
            combined_content = f"{abstract}\n\n[Document Content Extracted from {uploaded_file}]:\n{extracted_text[:4000]}"

        # If user didn't write an abstract, use extracted text as the abstract
        if not abstract and extracted_text:
            abstract = extracted_text[:1200]
            combined_content = extracted_text

        student_id = session.get('user_id')

        # 1. Insert Project into SQL Relational Table
        project_id = db.add_project(
            student_id=student_id,
            title=title,
            domain=domain,
            abstract=abstract,
            methodology="",
            tech_stack="",
            team_members=team_members,
            submitted_by_name=submitted_by_name,
            reg_no=reg_no,
            uploaded_file=uploaded_file,
            file_path=file_path,
            extracted_text=extracted_text
        )

        # 2. Generate Dense AI Vector Embedding from content (Title, Domain, Document Text)
        vector = engine.generate_embedding(
            title=title,
            domain=domain,
            abstract=combined_content
        )
        entities = extract_entities(combined_content + ' ' + title)
        db.store_project_vector(project_id, vector, entities)

        # 3. Cross-compare against all existing projects in SQL Database
        all_existing = db.get_all_projects()
        max_score = 0.0
        best_matched_id = None
        new_project_dict = {
            'title': title,
            'domain': domain,
            'abstract': combined_content
        }

        for existing in all_existing:
            if existing['id'] == project_id:
                continue
            comp = engine.compare_proposals(new_project_dict, existing)
            score = comp['similarity_percentage']

            if score > max_score:
                max_score = score
                best_matched_id = existing['id']

            if score >= 20.0:
                db.record_similarity_match(
                    source_id=project_id,
                    target_id=existing['id'],
                    score=score,
                    title_sim=comp['title_similarity'],
                    abs_sim=comp['abstract_similarity'],
                    entity_sim=comp['entity_similarity'],
                    common_entities=comp['common_entities'],
                    risk_level=comp['risk_level']
                )

        # 4. Status determination
        if max_score >= 80.0:
            status = 'DUPLICATE_FLAGGED'
        elif max_score >= 50.0:
            status = 'PENDING'
        else:
            status = 'APPROVED'

        db.update_project_status(project_id, status, max_score=max_score, matched_id=best_matched_id)

        # Redirect to private confirmation receipt (doesn't expose other proposals)
        return redirect(url_for('submission_success', project_id=project_id))

    return render_template('submit.html')

@app.route('/submission_success/<int:project_id>')
def submission_success(project_id):
    """
    Private confirmation receipt for the student who submitted.
    Shows only their own proposal details and similarity verification score.
    """
    project = db.get_project_by_id(project_id)
    if not project:
        flash("Submission record not found.", "error")
        return redirect(url_for('submit_project'))

    return render_template('submission_success.html', project=project)

@app.route('/download/<int:project_id>')
@login_required
def download_proposal_file(project_id):
    """Download uploaded PDF/Word document (restricted to logged-in personnel)."""
    project = db.get_project_by_id(project_id)
    if not project or not project['file_path']:
        flash("File not found.", "error")
        return redirect(url_for('my_submissions'))

    directory = os.path.dirname(project['file_path'])
    filename = os.path.basename(project['file_path'])
    return send_from_directory(directory, filename, as_attachment=True, download_name=project['uploaded_file'])

# ----------------- PROTECTED ACCESS MODULES ----------------- #
# Accessible ONLY to Project Guide (Dr. S.P. Ramya) or Team Members (Sudhan, Keerthi, Dayanandan)

@app.route('/submissions')
@login_required
def my_submissions():
    projects = db.get_all_projects()
    return render_template('submissions.html', projects=projects)

@app.route('/admin')
@login_required
def admin_dashboard():
    stats = db.get_dashboard_statistics()
    high_risk_matches = db.get_high_risk_matches()
    all_projects = db.get_all_projects()
    resolutions_history = db.get_resolutions_history()
    return render_template(
        'admin.html',
        stats=stats,
        matches=high_risk_matches,
        projects=all_projects,
        resolutions=resolutions_history
    )

@app.route('/resolution/<int:match_id>')
@login_required
def side_by_side_resolution(match_id):
    conn = db.get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT sm.*, 
           p1.title as p1_title, p1.domain as p1_domain, p1.abstract as p1_abstract, p1.uploaded_file as p1_file,
           p1.team_members as p1_team, p1.submitted_by_name as p1_author, p1.reg_no as p1_reg, p1.status as p1_status,
           p2.title as p2_title, p2.domain as p2_domain, p2.abstract as p2_abstract, p2.uploaded_file as p2_file,
           p2.team_members as p2_team, p2.submitted_by_name as p2_author, p2.reg_no as p2_reg, p2.status as p2_status
    FROM similarity_matches sm
    JOIN projects p1 ON sm.source_project_id = p1.id
    JOIN projects p2 ON sm.target_project_id = p2.id
    WHERE sm.id = ?
    ''', (match_id,))
    match_row = cursor.fetchone()
    conn.close()

    if not match_row:
        flash("Similarity match record not found.", "error")
        return redirect(url_for('admin_dashboard'))

    m = dict(match_row)
    try:
        common_entities = json.loads(m['common_entities'])
    except Exception:
        common_entities = []

    hl_title1, hl_title2 = highlight_overlapping_phrases(m['p1_title'], m['p2_title'])
    hl_abstract1, hl_abstract2 = highlight_overlapping_phrases(m['p1_abstract'], m['p2_abstract'])

    return render_template(
        'resolution.html',
        m=m,
        common_entities=common_entities,
        hl_title1=hl_title1,
        hl_title2=hl_title2,
        hl_abstract1=hl_abstract1,
        hl_abstract2=hl_abstract2
    )

@app.route('/search')
@login_required
def semantic_search():
    query = request.args.get('q', '').strip()
    results = []
    if query:
        all_vectors = db.get_all_vectors()
        results = engine.search_query_against_vectors(query, all_vectors, top_k=6)
    return render_template('search.html', query=query, results=results)

@app.route('/database')
@login_required
def database_inspector():
    stats = db.get_dashboard_statistics()
    vectors = db.get_all_vectors()
    sample_vector = vectors[0] if vectors else None
    return render_template('database_view.html', stats=stats, sample_vector=sample_vector)

@app.route('/certificate/<int:project_id>')
def view_certificate(project_id):
    project = db.get_project_by_id(project_id)
    if not project:
        flash("Project not found.", "error")
        return redirect(url_for('index'))
    
    matches = db.get_similarity_matches_for_project(project_id)
    top_match = matches[0] if matches else None

    return render_template('certificate.html', project=project, top_match=top_match)

@app.route('/network')
def network_hub():
    lan_ip = get_host_ip()
    port = 5000
    lan_url = f"http://{lan_ip}:{port}"
    return render_template('network.html', lan_url=lan_url, lan_ip=lan_ip, port=port)

# ----------------- REST API Endpoints ----------------- #

@app.route('/api/check_similarity', methods=['POST'])
def api_check_similarity():
    """
    Live real-time pre-check endpoint.
    Supports both JSON and Multipart Form Data (with PDF/Word file upload!).
    Extracts text from uploaded documents and evaluates similarity against SQL vectors.
    """
    title = ""
    domain = ""
    abstract = ""
    file_text = ""

    # Check if multipart form data (with file upload)
    if request.content_type and 'multipart/form-data' in request.content_type:
        title = request.form.get('title', '').strip()
        domain = request.form.get('domain', '').strip()
        abstract = request.form.get('abstract', '').strip()

        if 'proposal_file' in request.files:
            file = request.files['proposal_file']
            if file and file.filename and allowed_file(file.filename):
                original_filename = secure_filename(file.filename)
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{original_filename}")
                file.save(temp_path)
                file_text = extract_text_from_document(temp_path)
                try:
                    os.remove(temp_path) # Clean up temp preview file
                except Exception:
                    pass
    else:
        # JSON payload
        data = request.get_json() or {}
        title = data.get('title', '').strip()
        domain = data.get('domain', '').strip()
        abstract = data.get('abstract', '').strip()

    if not title and not abstract and not file_text:
        return jsonify({'error': 'Title, abstract, or document file is required'}), 400

    combined_text = f"{abstract} {file_text}".strip()
    draft_project = {
        'title': title,
        'domain': domain,
        'abstract': combined_text,
        'methodology': '',
        'tech_stack': ''
    }

    all_projects = db.get_all_projects()
    ranked_matches = []
    max_score = 0.0
    best_match = None

    for p in all_projects:
        comp = engine.compare_proposals(draft_project, p)
        score = comp['similarity_percentage']
        if score > max_score:
            max_score = score
            best_match = {
                'id': p['id'],
                'title': p['title'],
                'domain': p['domain'],
                'author': p['submitted_by_name'],
                'score': score,
                'risk_level': comp['risk_level'],
                'common_entities': comp['common_entities']
            }

        if score >= 30.0:
            ranked_matches.append({
                'id': p['id'],
                'title': p['title'],
                'domain': p['domain'],
                'author': p['submitted_by_name'],
                'score': score,
                'risk_level': comp['risk_level'],
                'common_entities': comp['common_entities']
            })

    ranked_matches.sort(key=lambda x: x['score'], reverse=True)

    if max_score >= 80.0:
        overall_risk = "HIGH_DUPLICATE"
        badge_color = "red"
        message = f"High Duplicate Warning: {max_score}% match with an existing proposal."
    elif max_score >= 50.0:
        overall_risk = "MODERATE_OVERLAP"
        badge_color = "amber"
        message = f"Moderate Overlap: {max_score}% similarity detected."
    else:
        overall_risk = "ORIGINAL"
        badge_color = "emerald"
        message = f"Original Project: {max_score}% similarity. Idea appears unique!"

    return jsonify({
        'max_similarity': max_score,
        'overall_risk': overall_risk,
        'badge_color': badge_color,
        'message': message,
        'file_analyzed': bool(file_text),
        'file_text_words': len(file_text.split()) if file_text else 0,
        'best_match': best_match,
        'matches': ranked_matches[:4]
    })

@app.route('/api/resolve_match', methods=['POST'])
@login_required
def api_resolve_match():
    data = request.get_json() or {}
    match_id = data.get('match_id')
    action = data.get('action')
    project_a_id = data.get('project_a_id')
    project_b_id = data.get('project_b_id')
    notes = data.get('notes', '')
    merged_name = data.get('merged_name', '')

    faculty_id = session.get('user_id')
    faculty_name = session.get('name', 'Dr. S.P. Ramya (Coordinator)')

    if not action or not project_a_id or not project_b_id:
        return jsonify({'error': 'Missing required fields'}), 400

    db.record_resolution(
        project_a_id=project_a_id,
        project_b_id=project_b_id,
        action=action,
        faculty_id=faculty_id,
        faculty_name=faculty_name,
        notes=notes,
        merged_name=merged_name
    )

    return jsonify({'success': True, 'message': f'Action {action} processed successfully.'})

@app.route('/api/run_sql', methods=['POST'])
@login_required
def api_run_sql():
    data = request.get_json() or {}
    sql = data.get('sql', '').strip()
    if not sql:
        return jsonify({'success': False, 'error': 'Query string cannot be empty.'})

    first_word = sql.split()[0].upper()
    if first_word not in ('SELECT', 'PRAGMA', 'EXPLAIN'):
        return jsonify({'success': False, 'error': 'Only SELECT, PRAGMA, and EXPLAIN queries are allowed.'})

    res = db.run_custom_query(sql)
    return jsonify(res)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0'
    lan_ip = get_host_ip()
    print("=" * 65)
    print("  SRMIST AI PROJECT DUPLICATE DETECTOR & ENTITY RESOLUTION")
    print("=" * 65)
    print(f"[*] Public Live URL:       {PUBLIC_URL}")
    print(f"[*] Local Host Access:     http://localhost:{port}")
    print(f"[*] Network / Wi-Fi:       http://{lan_ip}:{port}")
    print(f"[*] Faculty Guide:         Dr. S.P. Ramya")
    print(f"[*] Team:                  Sudhan Babu, Keerthi Vasaa, Dayanandan")
    print("=" * 65)
    app.run(host=host, port=port, debug=False)
