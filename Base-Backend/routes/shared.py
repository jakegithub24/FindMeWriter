from flask import Blueprint, request, jsonify, g
from models.db import get_db
from middleware.auth import require_role, get_current_user
from middleware.audit import audit

shared_bp = Blueprint('shared', __name__)

@shared_bp.route('/profile/<public_id>', methods=['GET'])
def public_profile(public_id):
    db = get_db()
    cursor = db.cursor()
    # Determine role from prefix
    if public_id.startswith('STU'):
        cursor.execute(
            """SELECT u.id, u.name, u.role, s.student_id, s.institution, s.accessibility_needs
               FROM users u JOIN students s ON u.id = s.user_id
               WHERE s.student_id = ? AND u.status = 'active'""",
            (public_id,)
        )
    elif public_id.startswith('VOL'):
        cursor.execute(
            """SELECT u.id, u.name, u.role, v.volunteer_id, v.city, v.languages, v.rating_avg, v.total_exams
               FROM users u JOIN volunteers v ON u.id = v.user_id
               WHERE v.volunteer_id = ? AND u.status = 'active'""",
            (public_id,)
        )
    elif public_id.startswith('CLG'):
        cursor.execute(
            """SELECT u.id, u.name, u.role, c.college_id, c.institution_name, c.address
               FROM users u JOIN colleges c ON u.id = c.user_id
               WHERE c.college_id = ? AND u.status = 'active'""",
            (public_id,)
        )
    else:
        return jsonify({'error': 'Invalid public ID'}), 400
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'Profile not found'}), 404
    return jsonify(dict(row)), 200

@shared_bp.route('/ratings', methods=['POST'])
@require_role('student')
@audit('RATING_SUBMITTED')
def submit_rating():
    data = request.get_json()
    request_id = data.get('request_id')
    to_id = data.get('to_id')  # user_id of volunteer
    score = data.get('score')
    feedback = data.get('feedback', '')
    if not all([request_id, to_id, score]):
        return jsonify({'error': 'request_id, to_id, score required'}), 400
    if not (1 <= score <= 5):
        return jsonify({'error': 'Score must be 1-5'}), 400
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    # Check request belongs to student
    cursor.execute("SELECT created_by FROM requests WHERE request_id = ? AND creator_role = 'student'", (request_id,))
    row = cursor.fetchone()
    if not row or row['created_by'] != user['user_id']:
        return jsonify({'error': 'Request not found or not yours'}), 400
    # Check that volunteer was committed
    cursor.execute("SELECT * FROM commitments WHERE request_id = ? AND volunteer_id = ? AND status = 'fulfilled'", (request_id, to_id))
    if not cursor.fetchone():
        return jsonify({'error': 'Volunteer not committed to this request'}), 400
    # Insert rating
    cursor.execute(
        "INSERT INTO ratings (request_id, from_id, to_id, score, feedback) VALUES (?, ?, ?, ?, ?)",
        (request_id, user['user_id'], to_id, score, feedback)
    )
    # Update volunteer avg
    cursor.execute("UPDATE volunteers SET rating_avg = (SELECT AVG(score) FROM ratings WHERE to_id = ?) WHERE user_id = ?", (to_id, to_id))
    db.commit()
    return jsonify({'message': 'Rating submitted'}), 201

@shared_bp.route('/settings', methods=['PUT'])
def update_settings():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    name = data.get('name')
    phone = data.get('phone')
    
    db = get_db()
    cursor = db.cursor()
    
    # Update users table if name or phone provided
    if name or phone:
        updates = []
        params = []
        if name:
            updates.append("name = ?")
            params.append(name)
        if phone:
            updates.append("phone = ?")
            params.append(phone)
        params.append(user['user_id'])
        cursor.execute(f"UPDATE users SET {', '.join(updates)}, updated_at = CURRENT_TIMESTAMP WHERE id = ?", params)
        
    # Update role-specific table details
    role = user['role']
    if role == 'student':
        institution = data.get('institution')
        accessibility = data.get('accessibility_needs')
        if institution is not None or accessibility is not None:
            updates = []
            params = []
            if institution is not None:
                updates.append("institution = ?")
                params.append(institution)
            if accessibility is not None:
                updates.append("accessibility_needs = ?")
                params.append(accessibility)
            params.append(user['user_id'])
            cursor.execute(f"UPDATE students SET {', '.join(updates)} WHERE user_id = ?", params)
            
    elif role == 'volunteer':
        city = data.get('city')
        languages = data.get('languages')
        if city is not None or languages is not None:
            updates = []
            params = []
            if city is not None:
                updates.append("city = ?")
                params.append(city)
            if languages is not None:
                updates.append("languages = ?")
                params.append(languages)
            params.append(user['user_id'])
            cursor.execute(f"UPDATE volunteers SET {', '.join(updates)} WHERE user_id = ?", params)
            
    elif role == 'college':
        institution_name = data.get('institution_name')
        affiliation_code = data.get('affiliation_code')
        address = data.get('address')
        if institution_name is not None or affiliation_code is not None or address is not None:
            updates = []
            params = []
            if institution_name is not None:
                updates.append("institution_name = ?")
                params.append(institution_name)
            if affiliation_code is not None:
                updates.append("affiliation_code = ?")
                params.append(affiliation_code)
            if address is not None:
                updates.append("address = ?")
                params.append(address)
            params.append(user['user_id'])
            cursor.execute(f"UPDATE colleges SET {', '.join(updates)} WHERE user_id = ?", params)
            
    db.commit()
    return jsonify({'message': 'Profile settings updated'}), 200

@shared_bp.route('/account/delete', methods=['POST'])
@require_role('student')
@audit('ACCOUNT_DELETION_REQUESTED')
def delete_account():
    user = get_current_user()
    data = request.get_json()
    confirm = data.get('confirm')
    if confirm != 'delete my account':
        return jsonify({'error': 'Confirmation text required'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET status = 'deactivated' WHERE id = ?", (user['user_id'],))
    db.commit()
    return jsonify({'message': 'Account deactivated'}), 200
