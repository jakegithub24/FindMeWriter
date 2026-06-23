import jwt
import bcrypt
import pyotp
from functools import wraps
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
from models.db import get_db

def create_tokens(user_id, role):
    access_payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES'])
    }
    refresh_payload = {
        'user_id': user_id,
        'role': role,
        'exp': datetime.utcnow() + timedelta(seconds=current_app.config['JWT_REFRESH_TOKEN_EXPIRES'])
    }
    access_token = jwt.encode(access_payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    refresh_token = jwt.encode(refresh_payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    return access_token, refresh_token

def verify_token(token):
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def get_current_user():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    payload = verify_token(token)
    if not payload:
        return None
    return payload

def require_role(role):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user = get_current_user()
            if not user:
                return jsonify({'error': 'Unauthorized', 'message': 'Missing or invalid token'}), 401
            if user['role'] != role:
                return jsonify({'error': 'Forbidden', 'message': f'Role {role} required'}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator

def require_admin_mfa(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user or user['role'] != 'admin':
            return jsonify({'error': 'Forbidden'}), 403
        totp_header = request.headers.get('X-Admin-MFA')
        if not totp_header:
            return jsonify({'error': 'MFA required', 'message': 'Missing X-Admin-MFA header'}), 401
        totp = pyotp.TOTP(current_app.config['ADMIN_TOTP_SECRET'])
        if not totp.verify(totp_header):
            return jsonify({'error': 'Invalid MFA code'}), 401
        return f(*args, **kwargs)
    return decorated

def hash_password(password):
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
