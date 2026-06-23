from flask import Blueprint, request, jsonify, g
from models.db import get_db
from middleware.auth import require_role, get_current_user
from middleware.audit import audit, log_audit
from middleware.validators import validate_public_id

complaints_bp = Blueprint('complaints', __name__)

@complaints_bp.route('', methods=['POST'])
def submit_complaint():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized', 'message': 'Missing or invalid token'}), 401
        
    data = request.get_json()
    target_id = data.get('target_id')
    target_role = data.get('target_role')
    description = data.get('description')
    if not all([target_id, target_role, description]):
        return jsonify({'error': 'target_id, target_role, description required'}), 400
    if not validate_public_id(target_id):
        return jsonify({'error': 'Invalid target_id format'}), 400
        
    db = get_db()
    cursor = db.cursor()
    
    # Target ID validation: Ensure target exists in the DB
    if target_role == 'student':
        cursor.execute("SELECT user_id FROM students WHERE student_id = ?", (target_id,))
    elif target_role == 'volunteer':
        cursor.execute("SELECT user_id FROM volunteers WHERE volunteer_id = ?", (target_id,))
    elif target_role == 'college':
        cursor.execute("SELECT user_id FROM colleges WHERE college_id = ?", (target_id,))
    else:
        return jsonify({'error': 'Invalid target_role. Must be student, volunteer, or college'}), 400
        
    target_row = cursor.fetchone()
    if not target_row:
        return jsonify({'error': f'Target {target_role} with ID {target_id} does not exist'}), 400

    cursor.execute(
        "INSERT INTO complaints (complainant_id, target_id, target_role, description, attachments_json) VALUES (?, ?, ?, ?, ?)",
        (user['user_id'], target_id, target_role, description, '[]')
    )
    db.commit()
    complaint_id = cursor.lastrowid
    log_audit(user['user_id'], user['role'], 'COMPLAINT_SUBMITTED', complaint_id, {'target_id': target_id})
    return jsonify({'message': 'Complaint submitted', 'complaint_id': complaint_id}), 201

@complaints_bp.route('', methods=['GET'])
def list_complaints():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    cursor = db.cursor()
    if user['role'] == 'admin':
        cursor.execute("SELECT * FROM complaints ORDER BY created_at DESC")
    else:
        cursor.execute("SELECT * FROM complaints WHERE complainant_id = ? ORDER BY created_at DESC", (user['user_id'],))
    rows = cursor.fetchall()
    return jsonify([dict(row) for row in rows]), 200

@complaints_bp.route('/<int:complaint_id>', methods=['PUT'])
@require_role('admin')
@audit('COMPLAINT_RESOLVED')
def update_complaint(complaint_id):
    data = request.get_json()
    status = data.get('status')
    admin_notes = data.get('admin_notes')
    if status not in ('open', 'under_review', 'resolved'):
        return jsonify({'error': 'Invalid status'}), 400
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "UPDATE complaints SET status = ?, admin_notes = ?, resolved_at = CURRENT_TIMESTAMP WHERE complaint_id = ?",
        (status, admin_notes, complaint_id)
    )
    db.commit()
    return jsonify({'message': 'Complaint updated'}), 200
