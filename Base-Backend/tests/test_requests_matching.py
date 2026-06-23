import json
from models.db import get_db
from middleware.auth import hash_password

def setup_users(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Student
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (10, 'student', 'student1@test.com', ?, 'Student One', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO students (user_id, student_id, aadhaar_number_hash, aadhaar_copy_path) VALUES (10, 'STU-1234', 'hash1', 'path1')"
        )
        
        # Volunteers
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (20, 'volunteer', 'vol1@test.com', ?, 'Volunteer One', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO volunteers (user_id, volunteer_id, aadhaar_number_hash, aadhaar_copy_path, city, languages) VALUES (20, 'VOL-1111', 'hash2', 'path2', 'Delhi', 'English,Hindi')"
        )
        
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (30, 'volunteer', 'vol2@test.com', ?, 'Volunteer Two', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO volunteers (user_id, volunteer_id, aadhaar_number_hash, aadhaar_copy_path, city, languages) VALUES (30, 'VOL-2222', 'hash3', 'path3', 'Delhi', 'English')"
        )
        
        # College
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (40, 'college', 'clg1@test.com', ?, 'College One', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO colleges (user_id, college_id, institution_name, affiliation_code) VALUES (40, 'CLG-1000', 'College One', 'AFF-1')"
        )
        
        db.commit()

def test_request_creation_and_matching_flow(client, app):
    setup_users(app)
    
    # 1. Login student
    login_res = client.post('/api/auth/login', json={'email': 'student1@test.com', 'password': 'pass123'})
    student_token = json.loads(login_res.data)['access_token']
    
    # 2. Create scribe request
    req_res = client.post('/api/student/requests', json={
        'date': '2026-07-20',
        'time': '10:00',
        'location': 'Delhi Exam Center A',
        'language': 'English',
        'duration': 120,
        'special_needs': 'Extra light'
    }, headers={'Authorization': f'Bearer {student_token}'})
    
    assert req_res.status_code == 201
    request_id = json.loads(req_res.data)['request_id']
    
    # Verify request created in DB
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT status FROM requests WHERE request_id = ?", (request_id,))
        assert cursor.fetchone()['status'] == 'open'
        
    # 3. Login Volunteer 1 (Delhi, English/Hindi) & check feed
    v1_login = client.post('/api/auth/login', json={'email': 'vol1@test.com', 'password': 'pass123'})
    v1_token = json.loads(v1_login.data)['access_token']
    
    feed_res = client.get('/api/volunteer/feed?location=Delhi&language=English', headers={'Authorization': f'Bearer {v1_token}'})
    assert feed_res.status_code == 200
    feed_data = json.loads(feed_res.data)
    assert len(feed_data) == 1
    assert feed_data[0]['request_id'] == request_id
    
    # 4. Volunteer 1 commits as primary
    commit_res = client.post('/api/volunteer/commit', json={
        'request_id': request_id,
        'role': 'primary'
    }, headers={'Authorization': f'Bearer {v1_token}'})
    assert commit_res.status_code == 201
    
    # Verify request status changes to filled
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT status FROM requests WHERE request_id = ?", (request_id,))
        assert cursor.fetchone()['status'] == 'filled'
        
    # 5. Login Volunteer 2 & commit as backup
    v2_login = client.post('/api/auth/login', json={'email': 'vol2@test.com', 'password': 'pass123'})
    v2_token = json.loads(v2_login.data)['access_token']
    
    # Should fail if trying to commit as primary again
    commit_fail = client.post('/api/volunteer/commit', json={
        'request_id': request_id,
        'role': 'primary'
    }, headers={'Authorization': f'Bearer {v2_token}'})
    assert commit_fail.status_code in (400, 409)

    
    # Commit as backup should succeed
    commit_backup = client.post('/api/volunteer/commit', json={
        'request_id': request_id,
        'role': 'backup'
    }, headers={'Authorization': f'Bearer {v2_token}'})
    assert commit_backup.status_code == 201
    
    # Verify commitments in DB
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT commitment_id, volunteer_id, role FROM commitments WHERE request_id = ? AND status='active'", (request_id,))
        rows = cursor.fetchall()
        assert len(rows) == 2
        roles = {r['volunteer_id']: r['role'] for r in rows}
        assert roles[20] == 'primary'
        assert roles[30] == 'backup'
        
    # 6. Volunteer 1 cancels commitment (role primary)
    with app.app_context():
        # Fetch commitment_id for volunteer 1
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT commitment_id FROM commitments WHERE request_id = ? AND volunteer_id = 20", (request_id,))
        commitment_id_v1 = cursor.fetchone()['commitment_id']
        
    cancel_res = client.post('/api/volunteer/cancel', json={
        'commitment_id': commitment_id_v1
    }, headers={'Authorization': f'Bearer {v1_token}'})
    assert cancel_res.status_code == 200
    
    # Verify that Volunteer 2 (backup) is promoted to primary, request status remains filled
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT role, status FROM commitments WHERE request_id = ? AND volunteer_id = 30", (request_id,))
        v2_row = cursor.fetchone()
        assert v2_row['role'] == 'primary'
        assert v2_row['status'] == 'active'
        
        cursor.execute("SELECT status FROM requests WHERE request_id = ?", (request_id,))
        assert cursor.fetchone()['status'] == 'filled'

def test_college_bulk_request_creation(client, app):
    setup_users(app)
    
    # Login college
    clg_login = client.post('/api/auth/login', json={'email': 'clg1@test.com', 'password': 'pass123'})
    clg_token = json.loads(clg_login.data)['access_token']
    
    # Post bulk requests
    bulk_res = client.post('/api/college/requests/bulk', json={
        'requests': [
            {
                'date': '2026-08-01',
                'time': '09:00',
                'location': 'Hall 1',
                'language': 'English',
                'duration': 180
            },
            {
                'date': '2026-08-02',
                'time': '14:00',
                'location': 'Hall 2',
                'language': 'Hindi',
                'duration': 180
            }
        ]
    }, headers={'Authorization': f'Bearer {clg_token}'})
    
    assert bulk_res.status_code == 201
    assert 'request_ids' in json.loads(bulk_res.data)
    assert len(json.loads(bulk_res.data)['request_ids']) == 2
    
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) as count FROM requests WHERE created_by = 40")
        assert cursor.fetchone()['count'] == 2
