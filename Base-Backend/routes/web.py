from flask import Blueprint, render_template, request, g, redirect, url_for
from middleware.auth import verify_token

web_bp = Blueprint('web', __name__)

@web_bp.before_app_request
def load_logged_in_user():
    # Attempt to load user from cookie
    token = request.cookies.get('access_token')
    if token:
        payload = verify_token(token)
        if payload:
            # We can also fetch the user details from DB here if needed
            # For efficiency, we can construct the basic user info from payload
            g.user = {
                'user_id': payload.get('user_id'),
                'role': payload.get('role'),
                # In a real app we might query the user's name from database.
                # For now, let's look up the name in the database using user_id.
                'name': 'User'
            }
            # Fetch real name from database to display in navbar
            from models.db import get_db
            try:
                db = get_db()
                cursor = db.cursor()
                cursor.execute("SELECT name FROM users WHERE id = ?", (g.user['user_id'],))
                row = cursor.fetchone()
                if row:
                    g.user['name'] = row['name']
            except Exception:
                pass
            return
    g.user = None

@web_bp.route('/')
def index():
    return render_template('index.html')

@web_bp.route('/login')
def login():
    if g.user:
        return redirect(url_for('web.dashboard'))
    return render_template('login.html')

@web_bp.route('/register')
def register():
    if g.user:
        return redirect(url_for('web.dashboard'))
    return render_template('register.html')

@web_bp.route('/dashboard')
def dashboard():
    if not g.user:
        return redirect(url_for('web.login'))
        
    from models.db import get_db
    db = get_db()
    cursor = db.cursor()
    
    role = g.user['role']
    data = {}
    
    if role == 'student':
        # Get student's requests
        cursor.execute(
            """SELECT r.*, 
               (SELECT u.name FROM commitments c JOIN users u ON c.volunteer_id = u.id WHERE c.request_id = r.request_id AND c.status = 'active' LIMIT 1) as volunteer_name
               FROM requests r WHERE r.created_by = ? ORDER BY r.created_at DESC""",
            (g.user['user_id'],)
        )
        data['requests'] = [dict(row) for row in cursor.fetchall()]
        
    elif role == 'volunteer':
        # Get volunteer's commitments
        cursor.execute(
            """SELECT c.commitment_id, c.role as commitment_role, r.*, u.name as creator_name
               FROM commitments c
               JOIN requests r ON c.request_id = r.request_id
               LEFT JOIN users u ON r.created_by = u.id
               WHERE c.volunteer_id = ? AND c.status = 'active'""",
            (g.user['user_id'],)
        )
        data['commitments'] = [dict(row) for row in cursor.fetchall()]
        
        # Get open requests for feed, filtering if parameters are present
        loc = request.args.get('location', '')
        lang = request.args.get('language', '')
        dt = request.args.get('date', '')
        
        query = "SELECT r.*, u.name as creator_name FROM requests r JOIN users u ON r.created_by = u.id WHERE r.status = 'open'"
        params = []
        if loc:
            query += " AND r.location LIKE ?"
            params.append(f'%{loc}%')
        if lang:
            query += " AND r.language = ?"
            params.append(lang)
        if dt:
            query += " AND r.date = ?"
            params.append(dt)
            
        cursor.execute(query, params)
        data['feed'] = [dict(row) for row in cursor.fetchall()]
        data['filters'] = {'location': loc, 'language': lang, 'date': dt}
        
    elif role == 'college':
        # Get college's requests
        cursor.execute(
            "SELECT * FROM requests WHERE created_by = ? ORDER BY created_at DESC",
            (g.user['user_id'],)
        )
        data['requests'] = [dict(row) for row in cursor.fetchall()]
        
        # Get verified volunteers for attendance marking
        cursor.execute(
            """SELECT v.verification_id, r.request_id, r.date, r.time, r.location, u.name as volunteer_name, u.id as volunteer_user_id,
               (SELECT status FROM attendance_logs WHERE request_id = r.request_id AND volunteer_id = u.id LIMIT 1) as attendance_status
               FROM verifications v
               JOIN requests r ON v.request_id = r.request_id
               JOIN users u ON v.volunteer_id = u.id
               WHERE r.created_by = ?""",
            (g.user['user_id'],)
        )
        data['verified_volunteers'] = [dict(row) for row in cursor.fetchall()]

        
    return render_template('dashboard.html', data=data)

@web_bp.route('/requests/new', methods=['GET'])
def new_request():
    if not g.user or g.user['role'] not in ('student', 'college'):
        return redirect(url_for('web.login'))
    return render_template('request_new.html')


@web_bp.route('/profile')
def profile():
    if not g.user:
        return redirect(url_for('web.login'))
    
    from models.db import get_db
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, role, email, name, phone, status, created_at FROM users WHERE id = ?", (g.user['user_id'],))
    user_row = cursor.fetchone()
    if not user_row:
        return redirect(url_for('web.logout'))
        
    user_data = dict(user_row)
    role = user_data['role']
    
    if role == 'student':
        cursor.execute("SELECT student_id, institution, accessibility_needs FROM students WHERE user_id = ?", (g.user['user_id'],))
        row = cursor.fetchone()
        if row:
            user_data.update(dict(row))
    elif role == 'volunteer':
        cursor.execute("SELECT volunteer_id, city, languages FROM volunteers WHERE user_id = ?", (g.user['user_id'],))
        row = cursor.fetchone()
        if row:
            user_data.update(dict(row))
    elif role == 'college':
        cursor.execute("SELECT college_id, institution_name, affiliation_code, address FROM colleges WHERE user_id = ?", (g.user['user_id'],))
        row = cursor.fetchone()
        if row:
            user_data.update(dict(row))
            
    return render_template('profile.html', profile=user_data)

@web_bp.route('/logout')
def logout():
    response = redirect(url_for('web.index'))
    response.delete_cookie('access_token')
    response.delete_cookie('refresh_token')
    return response

@web_bp.route('/terms')
def terms():
    return render_template('terms.html')

@web_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')

@web_bp.route('/verification-queue')
def verification_queue():
    if not g.user or g.user['role'] != 'college':
        return redirect(url_for('web.login'))
        
    from models.db import get_db
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT r.request_id, r.date, r.time, r.location, r.language, v.volunteer_id, c.volunteer_id as volunteer_user_id, u.name as volunteer_name, c.role as commitment_role
           FROM requests r
           JOIN commitments c ON r.request_id = c.request_id
           JOIN volunteers v ON c.volunteer_id = v.user_id
           JOIN users u ON v.user_id = u.id
           WHERE r.created_by = ? AND r.status IN ('filled','completed')
           AND NOT EXISTS (SELECT 1 FROM verifications WHERE request_id = r.request_id AND volunteer_id = v.user_id)""",
        (g.user['user_id'],)
    )
    queue = [dict(row) for row in cursor.fetchall()]
    return render_template('verification_queue.html', queue=queue)

@web_bp.route('/admin/audit-logs')
def admin_audit_logs():
    if not g.user or g.user['role'] != 'admin':
        return redirect(url_for('web.login'))
        
    from models.db import get_db
    db = get_db()
    cursor = db.cursor()
    
    action_filter = request.args.get('action', '')
    actor_filter = request.args.get('actor_id', '')
    
    query = "SELECT log_id, action, actor_id, actor_role, target_id, details_json, CAST(timestamp AS TEXT) as timestamp, hash FROM audit_logs"
    params = []
    conditions = []
    if action_filter:
        conditions.append("action = ?")
        params.append(action_filter)
    if actor_filter:
        conditions.append("actor_id = ?")
        params.append(actor_filter)
        
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += " ORDER BY log_id DESC LIMIT 100"
    
    cursor.execute(query, params)
    logs = [dict(row) for row in cursor.fetchall()]
    
    from middleware.audit import verify_audit_chain
    chain_valid = verify_audit_chain()
    
    return render_template('admin_audit_logs.html', logs=logs, chain_valid=chain_valid, action_filter=action_filter, actor_filter=actor_filter)



