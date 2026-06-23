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
    return render_template('dashboard.html')

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

