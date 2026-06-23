import os
import hashlib
from flask import Blueprint, request, jsonify, current_app, g
from werkzeug.utils import secure_filename
from models.db import get_db
from middleware.auth import hash_password, check_password, create_tokens, verify_token, require_role, get_current_user
from middleware.encryption import encrypt_file
from middleware.audit import log_audit
from middleware.validators import validate_aadhaar
from utils.id_generator import generate_public_id

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.form
    role = data.get('role')
    if role not in ('student', 'volunteer', 'college', 'admin'):
        return jsonify({'error': 'Invalid role'}), 400

    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    phone = data.get('phone')

    if not all([email, password, name]):
        return jsonify({'error': 'Missing required fields'}), 400

    db = get_db()
    cursor = db.cursor()

    # Check email uniqueness
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        return jsonify({'error': 'Email already registered'}), 409

    password_hash = hash_password(password)

    # Insert user
    cursor.execute(
        "INSERT INTO users (role, email, password_hash, name, phone, status) VALUES (?, ?, ?, ?, ?, 'active')",
        (role, email, password_hash, name, phone)
    )
    user_id = cursor.lastrowid

    # Role-specific handling
    if role in ('student', 'volunteer'):
        aadhaar = data.get('aadhaar')
        if not aadhaar or not validate_aadhaar(aadhaar):
            return jsonify({'error': 'Valid 12-digit Aadhaar required'}), 400
        # Check Aadhaar uniqueness (hash)
        aadhaar_hash = hashlib.sha256(aadhaar.encode()).hexdigest()
        # Check if already used (in students or volunteers)
        cursor.execute("SELECT user_id FROM students WHERE aadhaar_number_hash = ?", (aadhaar_hash,))
        if cursor.fetchone():
            return jsonify({'error': 'Aadhaar already registered'}), 409
        cursor.execute("SELECT user_id FROM volunteers WHERE aadhaar_number_hash = ?", (aadhaar_hash,))
        if cursor.fetchone():
            return jsonify({'error': 'Aadhaar already registered'}), 409

        # File upload
        file = request.files.get('aadhaar_copy')
        if not file:
            return jsonify({'error': 'Aadhaar photocopy required'}), 400
        filename = secure_filename(f"{user_id}_{file.filename}")
        temp_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"temp_{filename}")
        file.save(temp_path)
        # Encrypt and store
        encrypted_path = os.path.join(current_app.config['UPLOAD_FOLDER'], f"{filename}.enc")
        encrypt_file(temp_path, encrypted_path)
        os.remove(temp_path)

        while True:
            public_id = generate_public_id('STU' if role == 'student' else 'VOL')
            table_name = 'students' if role == 'student' else 'volunteers'
            id_col = 'student_id' if role == 'student' else 'volunteer_id'
            cursor.execute(f"SELECT user_id FROM {table_name} WHERE {id_col} = ?", (public_id,))
            if not cursor.fetchone():
                break

        if role == 'student':
            institution = data.get('institution')
            accessibility = data.get('accessibility_needs')
            cursor.execute(
                "INSERT INTO students (user_id, student_id, aadhaar_number_hash, aadhaar_copy_path, institution, accessibility_needs) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, public_id, aadhaar_hash, encrypted_path, institution, accessibility)
            )
        else:  # volunteer
            city = data.get('city')
            languages = data.get('languages')
            cursor.execute(
                "INSERT INTO volunteers (user_id, volunteer_id, aadhaar_number_hash, aadhaar_copy_path, city, languages) VALUES (?, ?, ?, ?, ?, ?)",
                (user_id, public_id, aadhaar_hash, encrypted_path, city, languages)
            )
    elif role == 'college':
        while True:
            college_id = generate_public_id('CLG')
            cursor.execute("SELECT user_id FROM colleges WHERE college_id = ?", (college_id,))
            if not cursor.fetchone():
                break
        institution_name = data.get('institution_name')
        affiliation_code = data.get('affiliation_code')
        address = data.get('address')
        cursor.execute(
            "INSERT INTO colleges (user_id, college_id, institution_name, affiliation_code, address) VALUES (?, ?, ?, ?, ?)",
            (user_id, college_id, institution_name, affiliation_code, address)
        )
    elif role == 'admin':
        # Admin registration should be restricted; for MVP we allow but only if first admin?
        # For simplicity, we allow admin registration but no extra fields.
        pass

    db.commit()
    log_audit(user_id, role, 'REGISTER', user_id, {'role': role, 'email': email})

    return jsonify({'message': 'User registered successfully', 'user_id': user_id}), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'error': 'Email and password required'}), 400

    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, role, password_hash, status FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    if user['status'] == 'deactivated':
        return jsonify({'error': 'Account deactivated'}), 403
    if not check_password(password, user['password_hash']):
        return jsonify({'error': 'Invalid credentials'}), 401

    access_token, refresh_token = create_tokens(user['id'], user['role'])
    log_audit(user['id'], user['role'], 'LOGIN', user['id'], {})
    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token,
        'role': user['role']
    }), 200

@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json()
    refresh_token = data.get('refresh_token')
    if not refresh_token:
        return jsonify({'error': 'Refresh token required'}), 400
    payload = verify_token(refresh_token)
    if not payload:
        return jsonify({'error': 'Invalid or expired refresh token'}), 401
    # Generate new tokens
    new_access, new_refresh = create_tokens(payload['user_id'], payload['role'])
    return jsonify({'access_token': new_access, 'refresh_token': new_refresh}), 200

@auth_bp.route('/profile', methods=['GET'])
def profile():
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT id, role, email, name, phone, status, created_at FROM users WHERE id = ?", (user['user_id'],))
    user_data = dict(cursor.fetchone())
    # Add role-specific public ID
    role = user_data['role']
    if role == 'student':
        cursor.execute("SELECT student_id FROM students WHERE user_id = ?", (user['user_id'],))
        row = cursor.fetchone()
        user_data['public_id'] = row['student_id'] if row else None
    elif role == 'volunteer':
        cursor.execute("SELECT volunteer_id FROM volunteers WHERE user_id = ?", (user['user_id'],))
        row = cursor.fetchone()
        user_data['public_id'] = row['volunteer_id'] if row else None
    elif role == 'college':
        cursor.execute("SELECT college_id FROM colleges WHERE user_id = ?", (user['user_id'],))
        row = cursor.fetchone()
        user_data['public_id'] = row['college_id'] if row else None
    else:
        user_data['public_id'] = None
    return jsonify(user_data), 200
