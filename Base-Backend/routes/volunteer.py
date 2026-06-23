from flask import Blueprint, request, jsonify, g
from models.db import get_db
from middleware.auth import require_role, get_current_user
from middleware.audit import audit

volunteer_bp = Blueprint('volunteer', __name__)

@volunteer_bp.route('/feed', methods=['GET'])
@require_role('volunteer')
def feed():
    # Filters: location, language, date
    location = request.args.get('location')
    language = request.args.get('language')
    date = request.args.get('date')
    db = get_db()
    cursor = db.cursor()
    query = "SELECT * FROM requests WHERE status = 'open'"
    params = []
    if location:
        query += " AND location LIKE ?"
        params.append(f'%{location}%')
    if language:
        query += " AND language = ?"
        params.append(language)
    if date:
        query += " AND date = ?"
        params.append(date)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    result = [dict(row) for row in rows]
    return jsonify(result), 200

@volunteer_bp.route('/commit', methods=['POST'])
@require_role('volunteer')
@audit('VOLUNTEER_COMMIT')
def commit():
    data = request.get_json()
    request_id = data.get('request_id')
    role = data.get('role')  # 'primary' or 'backup'
    if not request_id or role not in ('primary', 'backup'):
        return jsonify({'error': 'request_id and role (primary/backup) required'}), 400
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    # Check if request is open
    cursor.execute("SELECT status FROM requests WHERE request_id = ?", (request_id,))
    row = cursor.fetchone()
    if not row or row['status'] != 'open':
        return jsonify({'error': 'Request not open'}), 400
    # Check if volunteer already committed to this request
    cursor.execute("SELECT * FROM commitments WHERE request_id = ? AND volunteer_id = ? AND status = 'active'", (request_id, user['user_id']))
    if cursor.fetchone():
        return jsonify({'error': 'Already committed to this request'}), 409
    # If primary, ensure not already filled
    if role == 'primary':
        cursor.execute("SELECT COUNT(*) as cnt FROM commitments WHERE request_id = ? AND role = 'primary' AND status = 'active'", (request_id,))
        if cursor.fetchone()['cnt'] > 0:
            return jsonify({'error': 'Primary slot already filled'}), 409
    # Insert commitment
    cursor.execute(
        "INSERT INTO commitments (request_id, volunteer_id, role, status) VALUES (?, ?, ?, 'active')",
        (request_id, user['user_id'], role)
    )
    # If primary, update request status to filled
    if role == 'primary':
        cursor.execute("UPDATE requests SET status = 'filled' WHERE request_id = ?", (request_id,))
    db.commit()
    return jsonify({'message': 'Commitment successful'}), 201

@volunteer_bp.route('/commitments', methods=['GET'])
@require_role('volunteer')
def commitments():
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT c.*, r.date, r.time, r.location, r.language FROM commitments c
           JOIN requests r ON c.request_id = r.request_id
           WHERE c.volunteer_id = ? AND c.status = 'active'""",
        (user['user_id'],)
    )
    rows = cursor.fetchall()
    return jsonify([dict(row) for row in rows]), 200

# Auto-promote backup on cancellation (admin or volunteer can cancel)
@volunteer_bp.route('/cancel', methods=['POST'])
@require_role('volunteer')
@audit('VOLUNTEER_CANCEL')
def cancel_commitment():
    data = request.get_json()
    commitment_id = data.get('commitment_id')
    if not commitment_id:
        return jsonify({'error': 'commitment_id required'}), 400
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT role, request_id FROM commitments WHERE commitment_id = ? AND volunteer_id = ? AND status = 'active'", (commitment_id, user['user_id']))
    row = cursor.fetchone()
    if not row:
        return jsonify({'error': 'Commitment not found'}), 404
    # Cancel the commitment
    cursor.execute("UPDATE commitments SET status = 'cancelled' WHERE commitment_id = ?", (commitment_id,))
    # If it was primary, promote a backup
    if row['role'] == 'primary':
        # Check if there is a backup
        cursor.execute("SELECT commitment_id FROM commitments WHERE request_id = ? AND role = 'backup' AND status = 'active' ORDER BY created_at LIMIT 1", (row['request_id'],))
        backup = cursor.fetchone()
        if backup:
            # Promote backup to primary
            cursor.execute("UPDATE commitments SET role = 'primary' WHERE commitment_id = ?", (backup['commitment_id'],))
        else:
            # No backup, set request open
            cursor.execute("UPDATE requests SET status = 'open' WHERE request_id = ?", (row['request_id'],))
    db.commit()
    return jsonify({'message': 'Commitment cancelled'}), 200
