from flask import Blueprint, request, jsonify, g
from models.db import get_db
from middleware.auth import require_role, get_current_user
from middleware.audit import audit

college_bp = Blueprint('college', __name__)

@college_bp.route('/requests', methods=['POST'])
@require_role('college')
@audit('COLLEGE_REQUEST_CREATED')
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
           VALUES (?, 'college', ?, ?, ?, ?, ?, ?, ?)""",
        (user['user_id'], data['date'], data['time'], data['location'], data['language'],
         data['duration'], data.get('num_writers', 1), data.get('special_needs'))
    )
    db.commit()
    return jsonify({'message': 'Request created', 'request_id': cursor.lastrowid}), 201

@college_bp.route('/verification-queue', methods=['GET'])
@require_role('college')
def verification_queue():
    # Get requests created by this college with commitments
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT r.request_id, r.date, r.location, v.volunteer_id, u.name as volunteer_name, c.role
           FROM requests r
           JOIN commitments c ON r.request_id = c.request_id
           JOIN volunteers v ON c.volunteer_id = v.user_id
           JOIN users u ON v.user_id = u.id
           WHERE r.created_by = ? AND r.status IN ('filled','completed')
           AND NOT EXISTS (SELECT 1 FROM verifications WHERE request_id = r.request_id AND volunteer_id = v.user_id)""",
        (user['user_id'],)
    )
    rows = cursor.fetchall()
    return jsonify([dict(row) for row in rows]), 200

@college_bp.route('/verify', methods=['POST'])
@require_role('college')
@audit('VERIFICATION_LOGGED')
def verify():
    data = request.get_json()
    request_id = data.get('request_id')
    volunteer_id = data.get('volunteer_id')  # user_id of volunteer
    physical_match = data.get('physical_match')  # boolean
    notes = data.get('notes', '')
    if not request_id or not volunteer_id or physical_match is None:
        return jsonify({'error': 'request_id, volunteer_id, physical_match required'}), 400
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    # Verify that the volunteer is committed to this request
    cursor.execute("SELECT * FROM commitments WHERE request_id = ? AND volunteer_id = ? AND status = 'active'", (request_id, volunteer_id))
    if not cursor.fetchone():
        return jsonify({'error': 'Volunteer not committed to this request'}), 400
    # Insert verification
    cursor.execute(
        """INSERT INTO verifications (request_id, volunteer_id, college_id, verified_by_user_id, physical_match, notes)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (request_id, volunteer_id, user['user_id'], user['user_id'], physical_match, notes)
    )
    db.commit()
    return jsonify({'message': 'Verification logged'}), 201

@college_bp.route('/attendance', methods=['POST'])
@require_role('college')
@audit('ATTENDANCE_MARKED')
def mark_attendance():
    data = request.get_json()
    request_id = data.get('request_id')
    volunteer_id = data.get('volunteer_id')
    status = data.get('status')  # 'present' or 'absent'
    if not all([request_id, volunteer_id, status]):
        return jsonify({'error': 'request_id, volunteer_id, status required'}), 400
    if status not in ('present', 'absent'):
        return jsonify({'error': 'status must be present or absent'}), 400
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    # Check if verification exists
    cursor.execute("SELECT verification_id FROM verifications WHERE request_id = ? AND volunteer_id = ?", (request_id, volunteer_id))
    if not cursor.fetchone():
        return jsonify({'error': 'Volunteer not verified for this request'}), 400
    # For simplicity, we can store attendance in verifications? Or separate table? We'll add a column to verifications? 
    # But schema doesn't have attendance. We'll extend: we could add an attendance table or add status to verifications.
    # To keep MVP, we'll update verifications with a notes field or create a new table. For now, we'll just log an audit.
    # We'll store in a separate table, but since schema not defined, we'll create a new table attendance_logs.
    # Let's create attendance_logs table dynamically.
    cursor.execute("CREATE TABLE IF NOT EXISTS attendance_logs (id INTEGER PRIMARY KEY AUTOINCREMENT, request_id INTEGER, volunteer_id INTEGER, status TEXT, marked_by INTEGER, timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP)")
    cursor.execute(
        "INSERT INTO attendance_logs (request_id, volunteer_id, status, marked_by) VALUES (?, ?, ?, ?)",
        (request_id, volunteer_id, status, user['user_id'])
    )
    db.commit()
    return jsonify({'message': 'Attendance marked'}), 201

@college_bp.route('/attendance-logs', methods=['GET'])
@require_role('college')
def attendance_logs():
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT al.*, u.name as volunteer_name FROM attendance_logs al
           JOIN users u ON al.volunteer_id = u.id
           WHERE al.marked_by = ? ORDER BY al.timestamp DESC""",
        (user['user_id'],)
    )
    rows = cursor.fetchall()
    return jsonify([dict(row) for row in rows]), 200
