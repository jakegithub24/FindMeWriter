import io
import os
import json
import hashlib
from models.db import get_db
from middleware.auth import create_tokens, verify_token
from middleware.encryption import decrypt_file

def test_student_registration_and_login(client, app):
    # 1. Register a student
    payload = {
        'role': 'student',
        'email': 'student@test.com',
        'password': 'password123',
        'name': 'Test Student',
        'phone': '1234567890',
        'aadhaar': '123456789012',
        'institution': 'Test Academy',
        'accessibility_needs': 'Screen Reader'
    }
    
    # Aadhaar photocopy file
    data = {**payload}
    data['aadhaar_copy'] = (io.BytesIO(b"fake aadhaar pdf content"), "aadhaar.pdf")
    
    response = client.post('/api/auth/register', data=data, content_type='multipart/form-data')
    assert response.status_code == 201
    res_data = json.loads(response.data)
    assert 'user_id' in res_data
    user_id = res_data['user_id']
    
    # Verify that the student Aadhaar file is encrypted in storage
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT aadhaar_copy_path, student_id FROM students WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        assert row is not None
        encrypted_path = row['aadhaar_copy_path']
        assert os.path.exists(encrypted_path)
        
        # Verify it can be decrypted
        decrypted_temp = encrypted_path + ".dec"
        decrypt_file(encrypted_path, decrypted_temp)
        with open(decrypted_temp, 'rb') as f:
            decrypted_content = f.read()
        assert decrypted_content == b"fake aadhaar pdf content"
        os.remove(decrypted_temp)

    # 2. Login as the student
    login_response = client.post('/api/auth/login', json={
        'email': 'student@test.com',
        'password': 'password123'
    })
    assert login_response.status_code == 200
    login_data = json.loads(login_response.data)
    assert 'access_token' in login_data
    assert login_data['role'] == 'student'
    
    # Verify token payload
    with app.app_context():
        token_payload = verify_token(login_data['access_token'])
        assert token_payload['user_id'] == user_id
        assert token_payload['role'] == 'student'


def test_profile_settings_update(client, app):
    # Register & Login student
    payload = {
        'role': 'student',
        'email': 'profile_student@test.com',
        'password': 'password123',
        'name': 'Profile Student',
        'phone': '1234567890',
        'aadhaar': '123456789013',
        'aadhaar_copy': (io.BytesIO(b"pdf"), "aadhaar.pdf")
    }
    register_res = client.post('/api/auth/register', data=payload, content_type='multipart/form-data')
    assert register_res.status_code == 201
    
    login_res = client.post('/api/auth/login', json={
        'email': 'profile_student@test.com',
        'password': 'password123'
    })
    token = json.loads(login_res.data)['access_token']
    
    # Put new settings
    update_res = client.put('/api/settings', json={
        'name': 'Updated Name',
        'phone': '9876543210',
        'institution': 'Updated Academy',
        'accessibility_needs': 'Extra Time'
    }, headers={'Authorization': f'Bearer {token}'})
    
    assert update_res.status_code == 200
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT name, phone FROM users WHERE email = 'profile_student@test.com'")
        u_row = cursor.fetchone()
        assert u_row['name'] == 'Updated Name'
        assert u_row['phone'] == '9876543210'
        
        cursor.execute("SELECT institution, accessibility_needs FROM students WHERE student_id LIKE 'STU-%'")
        s_row = cursor.fetchone()
        assert s_row['institution'] == 'Updated Academy'
        assert s_row['accessibility_needs'] == 'Extra Time'

def test_admin_mfa_setup(client, app):
    # Register & login admin
    with app.app_context():
        db = get_db()
        # Seed an admin directly or register
        from middleware.auth import hash_password
        db.cursor().execute(
            "INSERT INTO users (role, email, password_hash, name, status) VALUES ('admin', 'admin@test.com', ?, 'Admin User', 'active')",
            (hash_password('adminpass'),)
        )
        db.commit()
        
    login_res = client.post('/api/auth/login', json={
        'email': 'admin@test.com',
        'password': 'adminpass'
    })
    token = json.loads(login_res.data)['access_token']
    
    # Call MFA Setup
    setup_res = client.get('/api/admin/mfa/setup', headers={'Authorization': f'Bearer {token}'})
    assert setup_res.status_code == 200
    setup_data = json.loads(setup_res.data)
    assert 'secret' in setup_data
    assert 'provisioning_uri' in setup_data
    assert 'otpauth://totp/' in setup_data['provisioning_uri']
