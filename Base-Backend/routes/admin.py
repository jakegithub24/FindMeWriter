from flask import Blueprint, request, jsonify, current_app, g
from models.db import get_db
from middleware.auth import require_role, require_admin_mfa, get_current_user
from middleware.audit import audit, log_audit, get_audit_logs, verify_audit_chain
from utils.exporters import export_csv, export_json
from io import StringIO
from datetime import datetime

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/overview', methods=['GET'])
@require_role('admin')
@require_admin_mfa
def overview():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT COUNT(*) as total_users FROM users")
    total_users = cursor.fetchone()['total_users']
    cursor.execute("SELECT COUNT(*) as pending_complaints FROM complaints WHERE status != 'resolved'")
    pending_complaints = cursor.fetchone()['pending_complaints']
    cursor.execute("SELECT COUNT(*) as open_requests FROM requests WHERE status = 'open'")
    open_requests = cursor.fetchone()['open_requests']
    return jsonify({
        'total_users': total_users,
        'pending_complaints': pending_complaints,
        'open_requests': open_requests
    }), 200

@admin_bp.route('/users', methods=['GET'])
@require_role('admin')
@require_admin_mfa
def list_users():
    status_filter = request.args.get('status', 'active')
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, role, email, name, phone, status, created_at FROM users WHERE status = ?", (status_filter,))
    rows = cursor.fetchall()
    return jsonify([dict(row) for row in rows]), 200

@admin_bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@require_role('admin')
@require_admin_mfa
@audit('USER_SUSPENDED')
def suspend_user(user_id):
    data = request.get_json()
    action = data.get('action')  # 'suspend' or 'reactivate'
    if action not in ('suspend', 'reactivate'):
        return jsonify({'error': 'action must be suspend or reactivate'}), 400
    new_status = 'deactivated' if action == 'suspend' else 'active'
    db = get_db()
    cursor = db.cursor()
    cursor.execute("UPDATE users SET status = ? WHERE id = ?", (new_status, user_id))
    db.commit()
    log_audit(g.user_id, 'admin', f'USER_{action.upper()}', user_id, {'action': action})
    return jsonify({'message': f'User {action}ed successfully'}), 200

@admin_bp.route('/audit-logs', methods=['GET'])
@require_role('admin')
@require_admin_mfa
def audit_logs():
    limit = request.args.get('limit', 20, type=int)
    offset = request.args.get('offset', 0, type=int)
    filters = {}
    if 'action' in request.args:
        filters['action'] = request.args.get('action')
    if 'actor_id' in request.args:
        filters['actor_id'] = request.args.get('actor_id', type=int)
    if 'from_date' in request.args:
        filters['from_date'] = request.args.get('from_date')
    if 'to_date' in request.args:
        filters['to_date'] = request.args.get('to_date')
    logs = get_audit_logs(filters, limit, offset)
    return jsonify([dict(row) for row in logs]), 200

@admin_bp.route('/verify-chain', methods=['GET'])
@require_role('admin')
@require_admin_mfa
def verify_chain():
    valid = verify_audit_chain()
    return jsonify({'chain_valid': valid}), 200

@admin_bp.route('/export', methods=['POST'])
@require_role('admin')
@require_admin_mfa
def export():
    data = request.get_json()
    export_type = data.get('type')  # 'users', 'complaints', 'audit'
    format_type = data.get('format', 'csv')  # 'csv' or 'json'
    if export_type not in ('users', 'complaints', 'audit'):
        return jsonify({'error': 'Invalid export type'}), 400
    db = get_db()
    cursor = db.cursor()
    if export_type == 'users':
        cursor.execute("SELECT id, role, email, name, phone, status, created_at FROM users")
    elif export_type == 'complaints':
        cursor.execute("SELECT * FROM complaints")
    elif export_type == 'audit':
        cursor.execute("SELECT * FROM audit_logs ORDER BY log_id")
    rows = cursor.fetchall()
    data_list = [dict(row) for row in rows]
    if format_type == 'csv':
        output = export_csv(data_list)
        return output, 200, {'Content-Type': 'text/csv'}
    else:
        output = export_json(data_list)
        return output, 200, {'Content-Type': 'application/json'}
