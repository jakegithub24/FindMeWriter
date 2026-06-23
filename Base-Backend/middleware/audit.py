import json
import hashlib
from functools import wraps
from flask import request, current_app, g
from datetime import datetime
from models.db import get_db

def audit(action, target_id=None):
    """Decorator to log audit events."""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            result = f(*args, **kwargs)
            
            # Retrieve actor from g.user or auth middleware
            user = getattr(g, 'user', None)
            if not user:
                try:
                    from middleware.auth import get_current_user
                    user = get_current_user()
                except Exception:
                    user = None
                    
            actor_id = user.get('user_id') if user else 0
            actor_role = user.get('role') if user else 'unknown'
            
            details = {
                'endpoint': request.endpoint,
                'method': request.method,
                'path': request.path,
                'args': request.args.to_dict(),
                'form': request.form.to_dict() if request.form else {},
                'json': request.get_json(silent=True) or {},
                'status_code': getattr(result, 'status_code', 200) if hasattr(result, 'status_code') else 200
            }
            log_audit(actor_id, actor_role, action, target_id, details)
            return result
        return wrapped
    return decorator

def log_audit(actor_id, actor_role, action, target_id, details_json):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT hash FROM audit_logs ORDER BY log_id DESC LIMIT 1")
    row = cursor.fetchone()
    prev_hash = row['hash'] if row else ''
    details_str = json.dumps(details_json, default=str)
    # Use identical datetime format for both recording and verification
    timestamp_str = datetime.utcnow().isoformat()
    hash_input = prev_hash + details_str + timestamp_str
    current_hash = hashlib.sha256(hash_input.encode()).hexdigest()
    cursor.execute(
        """INSERT INTO audit_logs (action, actor_id, actor_role, target_id, details_json, timestamp, hash)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (action, actor_id, actor_role, target_id, details_str, timestamp_str, current_hash)
    )
    db.commit()

def get_audit_logs(filters=None, limit=20, offset=0):
    db = get_db()
    cursor = db.cursor()
    query = "SELECT log_id, action, actor_id, actor_role, target_id, details_json, CAST(timestamp AS TEXT) as timestamp, hash FROM audit_logs"
    params = []
    if filters:
        conditions = []
        if 'action' in filters:
            conditions.append("action = ?")
            params.append(filters['action'])
        if 'actor_id' in filters:
            conditions.append("actor_id = ?")
            params.append(filters['actor_id'])
        if 'from_date' in filters:
            conditions.append("timestamp >= ?")
            params.append(filters['from_date'])
        if 'to_date' in filters:
            conditions.append("timestamp <= ?")
            params.append(filters['to_date'])
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY log_id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])
    cursor.execute(query, params)
    return cursor.fetchall()

def verify_audit_chain():
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT log_id, hash, details_json, CAST(timestamp AS TEXT) as timestamp FROM audit_logs ORDER BY log_id")
    rows = cursor.fetchall()
    prev_hash = ''
    valid = True
    for row in rows:
        hash_input = prev_hash + row['details_json'] + row['timestamp']
        expected = hashlib.sha256(hash_input.encode()).hexdigest()
        if row['hash'] != expected:
            valid = False
            break
        prev_hash = row['hash']
    return valid
