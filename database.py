"""
Database Module for AI Project Duplicate Detector & Entity Resolution System.
Uses SQL relational database architecture with vector embedding storage.
"""
import sqlite3
import json
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'projects.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Users Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        name TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'student', -- 'student', 'faculty', 'admin'
        reg_no TEXT,
        department TEXT DEFAULT 'Artificial Intelligence',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 2. Projects Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
        title TEXT NOT NULL,
        domain TEXT NOT NULL,
        abstract TEXT NOT NULL,
        methodology TEXT,
        tech_stack TEXT,
        team_members TEXT,
        submitted_by_name TEXT,
        reg_no TEXT,
        status TEXT NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'APPROVED', 'DUPLICATE_FLAGGED', 'MERGED', 'REJECTED'
        max_similarity_score REAL DEFAULT 0.0,
        matched_project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
        uploaded_file TEXT,
        file_path TEXT,
        extracted_text TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # Ensure columns exist if table was already created
    cursor.execute("PRAGMA table_info(projects)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'uploaded_file' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN uploaded_file TEXT")
    if 'file_path' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN file_path TEXT")
    if 'extracted_text' not in columns:
        cursor.execute("ALTER TABLE projects ADD COLUMN extracted_text TEXT")

    # 3. DBMS Vector Index Table (stores dense mathematical embeddings in SQL)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS project_vectors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_id INTEGER UNIQUE NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        vector_json TEXT NOT NULL,
        dimension INTEGER NOT NULL,
        entity_tags_json TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 4. Similarity Matching Log Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS similarity_matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        source_project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        target_project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        similarity_score REAL NOT NULL,
        title_similarity REAL NOT NULL,
        abstract_similarity REAL NOT NULL,
        entity_similarity REAL NOT NULL,
        common_entities TEXT,
        risk_level TEXT NOT NULL, -- 'HIGH_DUPLICATE', 'MODERATE_OVERLAP', 'ORIGINAL'
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 5. Entity Resolution Actions Table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS entity_resolutions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        project_a_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        project_b_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
        action TEXT NOT NULL, -- 'MERGED_COLLABORATION', 'APPROVED_BOTH', 'REJECTED_DUPLICATE', 'REVISION_REQUESTED'
        faculty_id INTEGER REFERENCES users(id),
        faculty_name TEXT,
        resolution_notes TEXT,
        merged_team_name TEXT,
        resolved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()

# ----------------- User Helpers ----------------- #

def create_user(username, password, name, role='student', reg_no=None, department='Artificial Intelligence'):
    conn = get_db_connection()
    cursor = conn.cursor()
    pw_hash = generate_password_hash(password)
    try:
        cursor.execute('''
        INSERT INTO users (username, password_hash, name, role, reg_no, department)
        VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, pw_hash, name, role, reg_no, department))
        conn.commit()
        user_id = cursor.lastrowid
        return user_id
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

def authenticate_user(username, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    if user and check_password_hash(user['password_hash'], password):
        return dict(user)
    return None

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, name, role, reg_no, department, created_at FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

# ----------------- Project Helpers ----------------- #

def add_project(student_id, title, domain, abstract, methodology="", tech_stack="", team_members="", submitted_by_name="", reg_no="", uploaded_file=None, file_path=None, extracted_text=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO projects (student_id, title, domain, abstract, methodology, tech_stack, team_members, submitted_by_name, reg_no, uploaded_file, file_path, extracted_text)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (student_id, title, domain, abstract, methodology, tech_stack, team_members, submitted_by_name, reg_no, uploaded_file, file_path, extracted_text))
    conn.commit()
    project_id = cursor.lastrowid
    conn.close()
    return project_id

def update_project_status(project_id, status, max_score=None, matched_id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    if max_score is not None and matched_id is not None:
        cursor.execute('''
        UPDATE projects SET status = ?, max_similarity_score = ?, matched_project_id = ?
        WHERE id = ?
        ''', (status, max_score, matched_id, project_id))
    elif max_score is not None:
        cursor.execute('''
        UPDATE projects SET status = ?, max_similarity_score = ?
        WHERE id = ?
        ''', (status, max_score, project_id))
    else:
        cursor.execute('UPDATE projects SET status = ? WHERE id = ?', (status, project_id))
    conn.commit()
    conn.close()

def get_project_by_id(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p.*, u.name as student_name, u.reg_no as student_reg_no,
           mp.title as matched_project_title
    FROM projects p
    LEFT JOIN users u ON p.student_id = u.id
    LEFT JOIN projects mp ON p.matched_project_id = mp.id
    WHERE p.id = ?
    ''', (project_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def get_all_projects(status_filter=None, domain_filter=None, search_query=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    query = '''
    SELECT p.*, mp.title as matched_project_title
    FROM projects p
    LEFT JOIN projects mp ON p.matched_project_id = mp.id
    WHERE 1=1
    '''
    params = []
    if status_filter:
        query += ' AND p.status = ?'
        params.append(status_filter)
    if domain_filter:
        query += ' AND p.domain = ?'
        params.append(domain_filter)
    if search_query:
        query += ' AND (p.title LIKE ? OR p.abstract LIKE ? OR p.tech_stack LIKE ?)'
        wildcard = f'%{search_query}%'
        params.extend([wildcard, wildcard, wildcard])

    query += ' ORDER BY p.id DESC'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_projects_by_student(student_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT p.*, mp.title as matched_project_title
    FROM projects p
    LEFT JOIN projects mp ON p.matched_project_id = mp.id
    WHERE p.student_id = ?
    ORDER BY p.id DESC
    ''', (student_id,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

# ----------------- Vector Index Storage ----------------- #

def store_project_vector(project_id, vector, entity_tags):
    conn = get_db_connection()
    cursor = conn.cursor()
    vector_json = json.dumps(vector)
    entity_tags_json = json.dumps(entity_tags)
    dimension = len(vector)
    cursor.execute('''
    INSERT INTO project_vectors (project_id, vector_json, dimension, entity_tags_json)
    VALUES (?, ?, ?, ?)
    ON CONFLICT(project_id) DO UPDATE SET
        vector_json = excluded.vector_json,
        dimension = excluded.dimension,
        entity_tags_json = excluded.entity_tags_json,
        updated_at = CURRENT_TIMESTAMP
    ''', (project_id, vector_json, dimension, entity_tags_json))
    conn.commit()
    conn.close()

def get_all_vectors():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT pv.project_id, pv.vector_json, pv.dimension, pv.entity_tags_json,
           p.title, p.domain, p.abstract, p.tech_stack, p.methodology, p.submitted_by_name, p.status
    FROM project_vectors pv
    JOIN projects p ON pv.project_id = p.id
    ''')
    rows = cursor.fetchall()
    conn.close()
    result = []
    for r in rows:
        result.append({
            'project_id': r['project_id'],
            'vector': json.loads(r['vector_json']),
            'dimension': r['dimension'],
            'entity_tags': json.loads(r['entity_tags_json']) if r['entity_tags_json'] else [],
            'title': r['title'],
            'domain': r['domain'],
            'abstract': r['abstract'],
            'tech_stack': r['tech_stack'],
            'methodology': r['methodology'],
            'submitted_by_name': r['submitted_by_name'],
            'status': r['status']
        })
    return result

# ----------------- Similarity Matches & Resolutions ----------------- #

def record_similarity_match(source_id, target_id, score, title_sim, abs_sim, entity_sim, common_entities, risk_level):
    conn = get_db_connection()
    cursor = conn.cursor()
    common_json = json.dumps(common_entities) if isinstance(common_entities, list) else common_entities
    cursor.execute('''
    INSERT INTO similarity_matches 
    (source_project_id, target_project_id, similarity_score, title_similarity, abstract_similarity, entity_similarity, common_entities, risk_level)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (source_id, target_id, score, title_sim, abs_sim, entity_sim, common_json, risk_level))
    conn.commit()
    conn.close()

def get_similarity_matches_for_project(project_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT sm.*, 
           p1.title as source_title, p1.submitted_by_name as source_author,
           p2.title as target_title, p2.submitted_by_name as target_author, p2.domain as target_domain
    FROM similarity_matches sm
    JOIN projects p1 ON sm.source_project_id = p1.id
    JOIN projects p2 ON sm.target_project_id = p2.id
    WHERE sm.source_project_id = ? OR sm.target_project_id = ?
    ORDER BY sm.similarity_score DESC
    ''', (project_id, project_id))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_high_risk_matches():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT sm.*, 
           p1.title as source_title, p1.submitted_by_name as source_author, p1.status as source_status, p1.reg_no as source_reg,
           p2.title as target_title, p2.submitted_by_name as target_author, p2.status as target_status, p2.reg_no as target_reg
    FROM similarity_matches sm
    JOIN projects p1 ON sm.source_project_id = p1.id
    JOIN projects p2 ON sm.target_project_id = p2.id
    WHERE sm.similarity_score >= 50.0
    ORDER BY sm.similarity_score DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def record_resolution(project_a_id, project_b_id, action, faculty_id, faculty_name, notes, merged_name=""):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO entity_resolutions
    (project_a_id, project_b_id, action, faculty_id, faculty_name, resolution_notes, merged_team_name)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (project_a_id, project_b_id, action, faculty_id, faculty_name, notes, merged_name))

    # Update project statuses according to action
    if action == 'MERGED_COLLABORATION':
        cursor.execute("UPDATE projects SET status = 'MERGED' WHERE id IN (?, ?)", (project_a_id, project_b_id))
    elif action == 'APPROVED_BOTH':
        cursor.execute("UPDATE projects SET status = 'APPROVED' WHERE id IN (?, ?)", (project_a_id, project_b_id))
    elif action == 'REJECTED_DUPLICATE':
        cursor.execute("UPDATE projects SET status = 'APPROVED' WHERE id = ?", (project_b_id,))
        cursor.execute("UPDATE projects SET status = 'REJECTED' WHERE id = ?", (project_a_id,))
    elif action == 'REVISION_REQUESTED':
        cursor.execute("UPDATE projects SET status = 'PENDING' WHERE id IN (?, ?)", (project_a_id, project_b_id))

    conn.commit()
    conn.close()

def get_resolutions_history():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT er.*,
           p1.title as project_a_title, p1.submitted_by_name as project_a_author,
           p2.title as project_b_title, p2.submitted_by_name as project_b_author
    FROM entity_resolutions er
    JOIN projects p1 ON er.project_a_id = p1.id
    JOIN projects p2 ON er.project_b_id = p2.id
    ORDER BY er.resolved_at DESC
    ''')
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_dashboard_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) as total FROM projects')
    total_projects = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) as flagged FROM projects WHERE status = 'DUPLICATE_FLAGGED'")
    flagged_projects = cursor.fetchone()['flagged']

    cursor.execute("SELECT COUNT(*) as approved FROM projects WHERE status = 'APPROVED'")
    approved_projects = cursor.fetchone()['approved']

    cursor.execute("SELECT COUNT(*) as merged FROM projects WHERE status = 'MERGED'")
    merged_projects = cursor.fetchone()['merged']

    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']

    cursor.execute("SELECT AVG(similarity_score) as avg_sim FROM similarity_matches")
    avg_sim_row = cursor.fetchone()['avg_sim']
    avg_similarity = round(avg_sim_row, 1) if avg_sim_row else 0.0

    cursor.execute('''
    SELECT domain, COUNT(*) as count 
    FROM projects 
    GROUP BY domain 
    ORDER BY count DESC
    ''')
    domain_distribution = [dict(r) for r in cursor.fetchall()]

    conn.close()
    return {
        'total_projects': total_projects,
        'flagged_projects': flagged_projects,
        'approved_projects': approved_projects,
        'merged_projects': merged_projects,
        'total_users': total_users,
        'avg_similarity': avg_similarity,
        'domain_distribution': domain_distribution
    }

def run_custom_query(sql_statement):
    """Execute raw read-only SQL queries for the interactive SQL viewer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(sql_statement)
        rows = cursor.fetchall()
        columns = [description[0] for description in cursor.description] if cursor.description else []
        result = [dict(r) for r in rows]
        return {'success': True, 'columns': columns, 'rows': result, 'count': len(result)}
    except Exception as e:
        return {'success': False, 'error': str(e)}
    finally:
        conn.close()
