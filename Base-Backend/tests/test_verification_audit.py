import os
import json
import tempfile
import pytest
from models.db import get_db
from middleware.auth import hash_password
from middleware.audit import verify_audit_chain
from middleware.encryption import encrypt_file

def setup_users_for_verification(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Scribe/Volunteer
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (20, 'volunteer', 'vol1@test.com', ?, 'Volunteer One', 'active')",
            (hash_password('pass123'),)
        )
        # Create an encrypted Aadhaar file for testing
        plain_fd, plain_path = tempfile.mkstemp(suffix=".png")
        enc_fd, enc_path = tempfile.mkstemp(suffix=".png.enc")
        
        try:
            with open(plain_path, 'wb') as f:
                f.write(b"dummy image data")
            
            # Since encrypt_file requires app context, we are already in one
            encrypt_file(plain_path, enc_path)
        finally:
            os.close(plain_fd)
            try:
                os.unlink(plain_path)
            except OSError:
                pass

        cursor.execute(
            "INSERT INTO volunteers (user_id, volunteer_id, aadhaar_number_hash, aadhaar_copy_path, city, languages) VALUES (20, 'VOL-1111', 'hash2', ?, 'Delhi', 'English,Hindi')",
            (enc_path,)
        )
        
        # College
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (40, 'college', 'clg1@test.com', ?, 'College One', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO colleges (user_id, college_id, institution_name, affiliation_code) VALUES (40, 'CLG-1000', 'College One', 'AFF-1')"
        )
        
        # Admin
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (50, 'admin', 'admin1@test.com', ?, 'Admin One', 'active')",
            (hash_password('pass123'),)
        )

        # Scribe request created by College 40
        cursor.execute(
            """INSERT INTO requests (request_id, created_by, creator_role, date, time, location, language, duration, status)
               VALUES (100, 40, 'college', '2026-07-20', '10:00', 'College Center A', 'English', 120, 'filled')"""
        )
        
        # Commitment of Volunteer 20 to Request 100
        cursor.execute(
            """INSERT INTO commitments (commitment_id, request_id, volunteer_id, role, status)
               VALUES (200, 100, 20, 'primary', 'active')"""
        )
        
        db.commit()
        return enc_path

def test_verification_and_audit_flow(client, app):
    # 1. Setup Database
    enc_path = setup_users_for_verification(app)
    
    try:
        # 2. Login College
        clg_login = client.post('/api/auth/login', json={'email': 'clg1@test.com', 'password': 'pass123'})
        assert clg_login.status_code == 200
        clg_token = json.loads(clg_login.data)['access_token']
        
        # 3. Test Aadhaar Decryption Viewer Endpoint
        aadhaar_res = client.get('/api/college/aadhaar/VOL-1111', headers={'Authorization': f'Bearer {clg_token}'})
        assert aadhaar_res.status_code == 200
        assert aadhaar_res.data == b"dummy image data"
        assert aadhaar_res.mimetype == 'image/png'

        # 4. Test Scribe Verification Logging Endpoint
        verify_payload = {
            'request_id': 100,
            'volunteer_id': 20,
            'physical_match': True,
            'notes': 'Verified successfully side-by-side'
        }
        verify_res = client.post('/api/college/verify', json=verify_payload, headers={'Authorization': f'Bearer {clg_token}'})
        assert verify_res.status_code == 201
        assert b"Verification logged" in verify_res.data

        # Verify database record exists
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM verifications WHERE request_id = 100 AND volunteer_id = 20")
            v_row = cursor.fetchone()
            assert v_row is not None
            assert v_row['physical_match'] == 1
            assert v_row['notes'] == 'Verified successfully side-by-side'

        # 5. Test Scribe Attendance Marking Endpoint
        attendance_payload = {
            'request_id': 100,
            'volunteer_id': 20,
            'status': 'present'
        }
        attendance_res = client.post('/api/college/attendance', json=attendance_payload, headers={'Authorization': f'Bearer {clg_token}'})
        assert attendance_res.status_code == 201
        assert b"Attendance marked" in attendance_res.data

        # Verify attendance record exists in DB
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM attendance_logs WHERE request_id = 100 AND volunteer_id = 20")
            a_row = cursor.fetchone()
            assert a_row is not None
            assert a_row['status'] == 'present'

        # 6. Verify Cryptographic Audit Chain is valid initially
        with app.app_context():
            assert verify_audit_chain() is True

            # Double check that we have logged the audit entries
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT action, actor_id FROM audit_logs ORDER BY log_id")
            logs = cursor.fetchall()
            # Ensure our actions were audit logged correctly
            actions = [log['action'] for log in logs]
            assert 'VERIFICATION_LOGGED' in actions
            assert 'ATTENDANCE_MARKED' in actions

        # 7. Test Admin Audit Viewer UI Page
        # Login Admin
        admin_login = client.post('/api/auth/login', json={'email': 'admin1@test.com', 'password': 'pass123'})
        assert admin_login.status_code == 200
        admin_token = json.loads(admin_login.data)['access_token']

        # Set cookie to simulate browser visit
        client.set_cookie('access_token', admin_token)
        
        # View Audit Logs page
        audit_page_res = client.get('/admin/audit-logs')
        assert audit_page_res.status_code == 200
        assert b"Audit Log Viewer" in audit_page_res.data
        assert b"VERIFICATION_LOGGED" in audit_page_res.data
        assert b"ATTENDANCE_MARKED" in audit_page_res.data
        assert b"Tamper-Evident Chain Verified" in audit_page_res.data

        # 8. Test Chain Tampering / Cryptographic Validation Failure
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            # Mutate one of the audit entries maliciously (details_json is part of the hash)
            cursor.execute("UPDATE audit_logs SET details_json = '{\"tampered\": true}' WHERE action = 'VERIFICATION_LOGGED'")
            db.commit()
            
            # Verify the chain evaluates to False now
            assert verify_audit_chain() is False

        # Reload page and assert warning or invalid tag
        audit_page_tampered_res = client.get('/admin/audit-logs')
        assert audit_page_tampered_res.status_code == 200
        assert b"AUDIT CHAIN TAMPERING DETECTED" in audit_page_tampered_res.data

    finally:
        # Clean up encrypted file
        try:
            os.unlink(enc_path)
        except OSError:
            pass
