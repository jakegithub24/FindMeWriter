import json
import pytest
from app import socketio
from models.db import get_db
from middleware.auth import hash_password
from middleware.audit import get_audit_logs

def setup_helpdesk_test_users(app):
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        # Student
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (10, 'student', 'student1@test.com', ?, 'Student One', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO students (user_id, student_id, aadhaar_number_hash, aadhaar_copy_path) VALUES (10, 'STU-1000', 'hash1', 'path1')"
        )
        
        # Volunteer
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (20, 'volunteer', 'vol1@test.com', ?, 'Volunteer One', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO volunteers (user_id, volunteer_id, aadhaar_number_hash, aadhaar_copy_path, city, languages) VALUES (20, 'VOL-2000', 'hash2', 'path2', 'Delhi', 'English')"
        )
        
        # Another Volunteer (for slots full test)
        cursor.execute(
            "INSERT INTO users (id, role, email, password_hash, name, status) VALUES (30, 'volunteer', 'vol2@test.com', ?, 'Volunteer Two', 'active')",
            (hash_password('pass123'),)
        )
        cursor.execute(
            "INSERT INTO volunteers (user_id, volunteer_id, aadhaar_number_hash, aadhaar_copy_path, city, languages) VALUES (30, 'VOL-3000', 'hash3', 'path3', 'Delhi', 'English')"
        )

        db.commit()

def test_helpdesk_rest_endpoints(client, app):
    setup_helpdesk_test_users(app)
    
    # 1. Login Volunteer 1
    v1_login = client.post('/api/auth/login', json={'email': 'vol1@test.com', 'password': 'pass123'})
    assert v1_login.status_code == 200
    v1_token = json.loads(v1_login.data)['access_token']
    
    # 2. Get shifts (should seed shifts dynamically on first run)
    shifts_res = client.get('/api/helpdesk/shifts', headers={'Authorization': f'Bearer {v1_token}'})
    assert shifts_res.status_code == 200
    shifts_data = json.loads(shifts_res.data)
    assert 'shifts' in shifts_data
    assert len(shifts_data['shifts']) >= 5
    
    first_shift = shifts_data['shifts'][0]
    shift_id = first_shift['shift_id']
    assert first_shift['signed_up'] is None
    assert first_shift['filled'] == 0
    
    # 3. Volunteer 1 signs up for the first shift
    signup_res = client.post('/api/helpdesk/shifts/signup', json={'shift_id': shift_id}, headers={'Authorization': f'Bearer {v1_token}'})
    assert signup_res.status_code == 200
    assert b"Successfully signed up" in signup_res.data
    
    # Verify slot filled increments
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute("SELECT filled FROM shifts WHERE shift_id = ?", (shift_id,))
        assert cursor.fetchone()['filled'] == 1
        
        # Verify volunteer_shifts table contains mapping
        cursor.execute("SELECT * FROM volunteer_shifts WHERE volunteer_id = 20 AND shift_id = ?", (shift_id,))
        assert cursor.fetchone() is not None

    # 4. Duplicate signup should be rejected
    signup_fail_dup = client.post('/api/helpdesk/shifts/signup', json={'shift_id': shift_id}, headers={'Authorization': f'Bearer {v1_token}'})
    assert signup_fail_dup.status_code == 409
    
    # 5. Access shifts list page via browser
    client.set_cookie('access_token', v1_token)
    helpdesk_page = client.get('/helpdesk')
    assert helpdesk_page.status_code == 200
    assert b"Help Desk Shift Rota" in helpdesk_page.data
    assert b"Online Support Agents" in helpdesk_page.data

def test_helpdesk_socketio_realtime(client, app):
    orig_send_eio_packet = getattr(socketio.server, '_send_eio_packet', None)
    if orig_send_eio_packet:
        def custom_send_eio_packet(eio_sid, eio_pkt):
            if eio_pkt.packet_type == 4:  # MESSAGE
                pkt = socketio.server.packet_class()
                pkt.decode(eio_pkt.data)
                socketio.server._send_packet(eio_sid, pkt)
            else:
                orig_send_eio_packet(eio_sid, eio_pkt)
        socketio.server._send_eio_packet = custom_send_eio_packet

    try:
        setup_helpdesk_test_users(app)
        
        # Login Student
        student_login = client.post('/api/auth/login', json={'email': 'student1@test.com', 'password': 'pass123'})
        student_token = json.loads(student_login.data)['access_token']
        
        # Establish SocketIO connection for Student
        student_socket = socketio.test_client(
            app,
            namespace='/helpdesk'
        )
        if not student_socket.is_connected(namespace='/helpdesk'):
            print("DEBUG: Connection failed!")
            print("DEBUG: socketio.server:", socketio.server)
            if socketio.server:
                print("DEBUG: eio_sid:", student_socket.eio_sid)
                print("DEBUG: rooms in manager:", getattr(socketio.server.manager, 'rooms', None))
                print("DEBUG: eio_sid to sid mapping:", getattr(socketio.server.manager, 'eio_sid_to_sid', None))
                sid = socketio.server.manager.sid_from_eio_sid(student_socket.eio_sid, '/helpdesk')
                print("DEBUG: sid_from_eio_sid:", sid)
        assert student_socket.is_connected(namespace='/helpdesk')
        
        # 1. Join room
        student_socket.emit('join_room', {
            'room_id': 'room_student_10',
            'sender_id': 10,
            'sender_role': 'student',
            'sender_name': 'Student One'
        }, namespace='/helpdesk')
        
        # Verify joined event broadcasted
        received = student_socket.get_received(namespace='/helpdesk')
        event_names = [e['name'] for e in received]
        assert 'joined' in event_names
        
        # 2. Send Message
        student_socket.emit('send_message', {
            'room_id': 'room_student_10',
            'sender_id': 10,
            'sender_role': 'student',
            'message': 'Hello, I need help with my scribe allocation.'
        }, namespace='/helpdesk')
        
        # Verify message event received in room
        received = student_socket.get_received(namespace='/helpdesk')
        msg_events = [e for e in received if e['name'] == 'new_message']
        assert len(msg_events) == 1
        assert msg_events[0]['args'][0]['message'] == 'Hello, I need help with my scribe allocation.'
        
        # Verify message was saved to database (persistence)
        with app.app_context():
            db = get_db()
            cursor = db.cursor()
            cursor.execute("SELECT * FROM helpdesk_messages WHERE room_id = 'room_student_10'")
            row = cursor.fetchone()
            assert row is not None
            assert row['sender_id'] == 10
            assert row['message'] == 'Hello, I need help with my scribe allocation.'
            
        # Test REST endpoint for history
        history_res = client.get('/api/helpdesk/history/room_student_10', headers={'Authorization': f'Bearer {student_token}'})
        assert history_res.status_code == 200
        history_data = json.loads(history_res.data)
        assert len(history_data) == 1
        assert history_data[0]['message'] == 'Hello, I need help with my scribe allocation.'
        assert history_data[0]['sender_name'] == 'Student One'
        
        # 3. Typing Indicator
        student_socket.emit('typing', {
            'room_id': 'room_student_10',
            'sender_id': 10,
            'is_typing': True
          }, namespace='/helpdesk')
        received = student_socket.get_received(namespace='/helpdesk')
        # Since include_self is False, the sender won't receive their own typing event, which is correct
        
        # 4. Escalation Event
        student_socket.emit('escalate_to_admin', {
            'room_id': 'room_student_10',
            'reason': 'No support volunteer responded for 30 minutes.',
            'sender_id': 10
        }, namespace='/helpdesk')
        
        received = student_socket.get_received(namespace='/helpdesk')
        escalate_events = [e for e in received if e['name'] == 'escalation_alert']
        assert len(escalate_events) == 1
        assert escalate_events[0]['args'][0]['reason'] == 'No support volunteer responded for 30 minutes.'
        
        # Verify HELP_DESK_ESCALATED was logged to the audit logs
        with app.app_context():
            logs = get_audit_logs({'action': 'HELP_DESK_ESCALATED'})
            assert len(logs) >= 1
            assert logs[0]['actor_id'] == 10
            assert 'No support volunteer' in json.loads(logs[0]['details_json'])['reason']
    finally:
        if orig_send_eio_packet:
            socketio.server._send_eio_packet = orig_send_eio_packet
