from flask import Blueprint, request, jsonify, g
from models.db import get_db
from middleware.auth import require_role, get_current_user
from middleware.audit import audit
from datetime import datetime

student_bp = Blueprint('student', __name__)

@student_bp.route('/requests', methods=['POST'])
@require_role('student')
@audit('REQUEST_CREATED')
def create_request():
    data = request.get_json()
    required = ['date', 'time', 'location', 'language', 'duration']
    if not all(k in data for k in required):
        return jsonify({'error': 'Missing required fields'}), 400
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """INSERT INTO requests (created_by, creator_role, date, time, location, language, duration, num_writers, special_needs)
           VALUES (?, 'student', ?, ?, ?, ?, ?, ?, ?)""",
        (user['user_id'], data['date'], data['time'], data['location'], data['language'],
         data['duration'], data.get('num_writers', 1), data.get('special_needs'))
    )
    db.commit()
    request_id = cursor.lastrowid
    return jsonify({'message': 'Request created', 'request_id': request_id}), 201

@student_bp.route('/requests', methods=['GET'])
@require_role('student')
def get_requests():
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT r.*, 
           (SELECT json_group_array(json_object('volunteer_id', v.volunteer_id, 'role', c.role, 'status', c.status))
            FROM commitments c JOIN volunteers v ON c.volunteer_id = v.user_id WHERE c.request_id = r.request_id) as commitments
           FROM requests r WHERE r.created_by = ? ORDER BY r.created_at DESC""",
        (user['user_id'],)
    )
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    return jsonify(result), 200

@student_bp.route('/dashboard', methods=['GET'])
@require_role('student')
def dashboard():
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    # Active requests
    cursor.execute("SELECT COUNT(*) as active FROM requests WHERE created_by = ? AND status IN ('open','filled')", (user['user_id'],))
    active = cursor.fetchone()['active']
    # Complaints
    cursor.execute("SELECT COUNT(*) as complaints FROM complaints WHERE complainant_id = ? AND status != 'resolved'", (user['user_id'],))
    complaints = cursor.fetchone()['complaints']
    return jsonify({'active_requests': active, 'pending_complaints': complaints}), 200
