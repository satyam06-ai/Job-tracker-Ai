from flask import Flask, render_template, request, jsonify
import sqlite3
import os
import json
from datetime import datetime

# PDF reading
try:
    import PyPDF2
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Gemini AI
try:
    import google.generativeai as genai
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', '')
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        ai_model = genai.GenerativeModel('gemini-1.5-flash')
        AI_SUPPORT = True
    else:
        AI_SUPPORT = False
except ImportError:
    AI_SUPPORT = False

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# ─────────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────────
def get_db():
    conn = sqlite3.connect('job_tracker.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            company       TEXT    NOT NULL,
            role          TEXT    NOT NULL,
            job_desc      TEXT,
            status        TEXT    DEFAULT 'Applied',
            match_pct     REAL    DEFAULT 0,
            ai_result     TEXT,
            applied_date  TEXT,
            resume_text   TEXT,
            notes         TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def extract_pdf_text(file_path):
    if not PDF_SUPPORT:
        return ""
    text = ""
    try:
        with open(file_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() or ""
    except Exception:
        pass
    return text


def analyze_with_ai(resume_text, job_desc):
    if not AI_SUPPORT:
        return {
            "match_percentage": 0,
            "matched_skills": [],
            "missing_skills": [],
            "suggestions": ["Add your GEMINI_API_KEY in .env to enable AI analysis"],
            "summary": "AI not configured"
        }
    prompt = f"""
You are an expert HR analyst. Analyze how well the resume matches the job description.

RESUME:
{resume_text[:3000]}

JOB DESCRIPTION:
{job_desc[:2000]}

Respond ONLY in valid JSON — no extra text, no markdown:
{{
  "match_percentage": <integer 0-100>,
  "matched_skills": ["skill1", "skill2"],
  "missing_skills": ["skill1", "skill2"],
  "suggestions": ["improvement1", "improvement2", "improvement3"],
  "summary": "2-sentence honest summary"
}}
"""
    try:
        response = ai_model.generate_content(prompt)
        text = response.text.strip()
        # Strip markdown fences if present
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())
    except Exception as e:
        return {
            "match_percentage": 0,
            "matched_skills": [],
            "missing_skills": [],
            "suggestions": [f"AI Error: {str(e)}"],
            "summary": "Could not analyze"
        }


# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/stats')
def stats():
    conn = get_db()
    total = conn.execute('SELECT COUNT(*) FROM applications').fetchone()[0]
    avg_match = conn.execute(
        'SELECT AVG(match_pct) FROM applications WHERE match_pct > 0'
    ).fetchone()[0] or 0
    status_rows = conn.execute(
        'SELECT status, COUNT(*) as cnt FROM applications GROUP BY status'
    ).fetchall()
    conn.close()
    return jsonify({
        'total': total,
        'avg_match': round(avg_match, 1),
        'status_counts': {r['status']: r['cnt'] for r in status_rows}
    })


@app.route('/api/applications', methods=['GET'])
def list_applications():
    conn = get_db()
    rows = conn.execute(
        'SELECT id, company, role, status, match_pct, applied_date, notes '
        'FROM applications ORDER BY id DESC'
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


@app.route('/api/applications', methods=['POST'])
def add_application():
    company     = request.form.get('company', '').strip()
    role        = request.form.get('role', '').strip()
    job_desc    = request.form.get('job_desc', '').strip()
    status      = request.form.get('status', 'Applied')
    notes       = request.form.get('notes', '').strip()
    resume_file = request.files.get('resume')

    if not company or not role:
        return jsonify({'error': 'Company and Role are required'}), 400

    resume_text = ""
    if resume_file and resume_file.filename.endswith('.pdf'):
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
        path = os.path.join(app.config['UPLOAD_FOLDER'], resume_file.filename)
        resume_file.save(path)
        resume_text = extract_pdf_text(path)

    ai_result = {}
    match_pct  = 0
    if resume_text and job_desc:
        ai_result = analyze_with_ai(resume_text, job_desc)
        match_pct = ai_result.get('match_percentage', 0)

    conn = get_db()
    cur = conn.execute(
        '''INSERT INTO applications
           (company, role, job_desc, status, match_pct, ai_result, applied_date, resume_text, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        (company, role, job_desc, status, match_pct,
         json.dumps(ai_result), datetime.now().strftime('%Y-%m-%d'),
         resume_text, notes)
    )
    new_id = cur.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'id': new_id, 'ai_result': ai_result, 'match_pct': match_pct})


@app.route('/api/applications/<int:app_id>', methods=['GET'])
def get_application(app_id):
    conn = get_db()
    row = conn.execute('SELECT * FROM applications WHERE id = ?', (app_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'Not found'}), 404
    data = dict(row)
    try:
        data['ai_result'] = json.loads(data['ai_result'] or '{}')
    except Exception:
        data['ai_result'] = {}
    return jsonify(data)


@app.route('/api/applications/<int:app_id>/status', methods=['PUT'])
def update_status(app_id):
    new_status = request.json.get('status')
    if not new_status:
        return jsonify({'error': 'Status required'}), 400
    conn = get_db()
    conn.execute('UPDATE applications SET status = ? WHERE id = ?', (new_status, app_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


@app.route('/api/applications/<int:app_id>', methods=['DELETE'])
def delete_application(app_id):
    conn = get_db()
    conn.execute('DELETE FROM applications WHERE id = ?', (app_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})


# ─────────────────────────────────────────────
if __name__ == '__main__':
    init_db()
    os.makedirs('uploads', exist_ok=True)
    print("🚀 Job Tracker running at http://127.0.0.1:5000")
    app.run(debug=True)
