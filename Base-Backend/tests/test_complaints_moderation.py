import json
import pyotp
import pytest
from flask import current_app
from models.db import get_db
from middleware.auth import hash_password
from middleware.audit import get_audit_logs

def setup_complaints_test_users(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Student (Complainant)
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (10, 'student', 'student1@test.com', ?, 'Student One', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO students (user_id, student_id, aadhaar_number_hash, aadhaar_copy_path) VALUES (10, 'STU-1000', 'hash1', 'path1')"
        )
        
        # Volunteer (Reported Target)
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (20, 'volunteer', 'vol1@test.com', ?, 'Volunteer Scribe', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO volunteers (user_id, volunteer_id, aadhaar_number_hash, aadhaar_copy_path, city, languages) VALUES (20, 'VOL-2000', 'hash2', 'path2', 'Delhi', 'English')"
        )
        
        # Admin
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (50, 'admin', 'admin1@test.com', ?, 'Admin One', 'active')",
            (hash_password('pass123'),)
        )
        
        db.commit()

def get_mfa_code(app):
    with app.app_context():
        secret = current_app.config['ADMIN_TOTP_SECRET']
        totp = pyotp.TOTP(secret)
        return totp.now()

def test_complaint_and_moderation_flow(client, app):
    # Setup test users
    setup_complaints_test_users(app)
    
    # 1. Login student
    student_login = client.post('/api/auth/login', json={'email': 'student1@test.com', 'password': 'pass123'})
    assert student_login.status_code == 200
    student_token = json.loads(student_login.data)['access_token']
    
    # 2. Submit complaint against non-existent target ID
    bad_res1 = client.post('/api/complaints', json={
        'target_id': 'VOL-9999',
        'target_role': 'volunteer',
        'description': 'Did not show up.'
    }, headers={'Authorization': f'Bearer {student_token}'})
    assert bad_res1.status_code == 400
    assert b"does not exist" in bad_res1.data
    
    # 3. Submit complaint with malformed public ID format
    bad_res2 = client.post('/api/complaints', json={
        'target_id': 'INVALID-ID-FORMAT',
        'target_role': 'volunteer',
        'description': 'Did not show up.'
    }, headers={'Authorization': f'Bearer {student_token}'})
    assert bad_res2.status_code == 400
    assert b"Invalid target_id format" in bad_res2.data
    
    # 4. Submit valid complaint against Volunteer (VOL-2000)
    good_res = client.post('/api/complaints', json={
        'target_id': 'VOL-2000',
        'target_role': 'volunteer',
        'description': 'Arrived late and used inappropriate language.'
    }, headers={'Authorization': f'Bearer {student_token}'})
    assert good_res.status_code == 201
    complaint_data = json.loads(good_res.data)
    assert 'complaint_id' in complaint_data
    complaint_id = complaint_data['complaint_id']
    
    # Verify complaint in database
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT * FROM complaints WHERE complaint_id = ?", (complaint_id,))
        row = cursor.fetchone()
        assert row is not None
        assert row['target_id'] == 'VOL-2000'
        assert row['status'] == 'open'
        
        # Verify COMPLAINT_SUBMITTED was audit logged
        logs = get_audit_logs({'action': 'COMPLAINT_SUBMITTED'})
        assert len(logs) >= 1
        assert logs[0]['target_id'] == complaint_id

    # 5. Admin Triage Flow
    # Login admin
    admin_login = client.post('/api/auth/login', json={'email': 'admin1@test.com', 'password': 'pass123'})
    assert admin_login.status_code == 200
    admin_token = json.loads(admin_login.data)['access_token']
    
    # Access Admin complaints page (requires admin cookies)
    client.set_cookie('access_token', admin_token)
    triage_page = client.get('/admin/complaints')
    assert triage_page.status_code == 200
    assert b"Complaint Triage Queue" in triage_page.data
    assert b"VOL-2000" in triage_page.data
    
    # 6. Update complaint status to under_review (requires admin role and X-Admin-MFA)
    mfa_code = get_mfa_code(app)
    triage_update1 = client.put(f'/api/complaints/{complaint_id}', json={
        'status': 'under_review',
        'admin_notes': 'Under administrative investigation.'
    }, headers={'Authorization': f'Bearer {admin_token}', 'X-Admin-MFA': mfa_code})
    assert triage_update1.status_code == 200
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT status, admin_notes FROM complaints WHERE complaint_id = ?", (complaint_id,))
        row = cursor.fetchone()
        assert row['status'] == 'under_review'
        assert row['admin_notes'] == 'Under administrative investigation.'
        
    # 7. Suspend target user (Volunteer ID = 20)
    # Reject suspension if X-Admin-MFA header is missing
    suspend_fail = client.post('/api/admin/users/20/suspend', json={'action': 'suspend'}, headers={'Authorization': f'Bearer {admin_token}'})
    assert suspend_fail.status_code == 401
    
    # Succeed suspension with valid MFA code
    mfa_code = get_mfa_code(app)
    suspend_success = client.post('/api/admin/users/20/suspend', json={'action': 'suspend'}, headers={'Authorization': f'Bearer {admin_token}', 'X-Admin-MFA': mfa_code})
    assert suspend_success.status_code == 200
    
    # Verify user is deactivated in database
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT status FROM users WHERE id = 20")
        assert cursor.fetchone()['status'] == 'deactivated'
        
        # Verify USER_SUSPEND was audit logged
        logs = get_audit_logs({'action': 'USER_SUSPEND'})
        assert len(logs) >= 1
        assert logs[0]['target_id'] == 20
        
    # Verify deactivated user cannot log in
    vol_login_fail = client.post('/api/auth/login', json={'email': 'vol1@test.com', 'password': 'pass123'})
    assert vol_login_fail.status_code == 403
    assert b"Account deactivated" in vol_login_fail.data
    
    # 8. Resolve complaint
    mfa_code = get_mfa_code(app)
    triage_resolve = client.put(f'/api/complaints/{complaint_id}', json={
        'status': 'resolved',
        'admin_notes': 'Scribe suspended for 30 days.'
    }, headers={'Authorization': f'Bearer {admin_token}', 'X-Admin-MFA': mfa_code})
    assert triage_resolve.status_code == 200
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT status, admin_notes, resolved_at FROM complaints WHERE complaint_id = ?", (complaint_id,))
        row = cursor.fetchone()
        assert row['status'] == 'resolved'
        assert row['admin_notes'] == 'Scribe suspended for 30 days.'
        assert row['resolved_at'] is not None
        
        # Verify COMPLAINT_RESOLVED was audit logged
        logs = get_audit_logs({'action': 'COMPLAINT_RESOLVED'})
        assert len(logs) >= 1
        assert logs[0]['action'] == 'COMPLAINT_RESOLVED'

    # 9. Reactivate user account
    mfa_code = get_mfa_code(app)
    reactivate_res = client.post('/api/admin/users/20/suspend', json={'action': 'reactivate'}, headers={'Authorization': f'Bearer {admin_token}', 'X-Admin-MFA': mfa_code})
    assert reactivate_res.status_code == 200
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT status FROM users WHERE id = 20")
        assert cursor.fetchone()['status'] == 'active'
        
        # Verify USER_REACTIVATE was audit logged
        logs = get_audit_logs({'action': 'USER_REACTIVATE'})
        assert len(logs) >= 1
        assert logs[0]['target_id'] == 20
