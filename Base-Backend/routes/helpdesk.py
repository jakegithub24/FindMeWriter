from flask import Blueprint, request, jsonify, g
from flask_socketio import emit, join_room, leave_room
from app import socketio
from models.db import get_db
from middleware.auth import get_current_user, require_role
from middleware.audit import log_audit
from datetime import datetime

helpdesk_bp = Blueprint('helpdesk', __name__)

# Shared memory dictionary to track active rooms and online support agents
active_rooms = {}
online_volunteers = {}

# REST endpoints for shifts
@helpdesk_bp.route('/shifts', methods=['GET'])
@require_role('volunteer')
def get_shifts():
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    
    # Seed shifts dynamically if none exist so tests and UI are populated
    cursor.execute("SELECT COUNT(*) as count FROM shifts")
    if cursor.fetchone()['count'] == 0:
        cursor.execute("INSERT INTO shifts (date, start_time, end_time, slots, filled) VALUES ('2026-07-01', '08:00', '12:00', 5, 0)")
        cursor.execute("INSERT INTO shifts (date, start_time, end_time, slots, filled) VALUES ('2026-07-01', '12:00', '16:00', 5, 0)")
        cursor.execute("INSERT INTO shifts (date, start_time, end_time, slots, filled) VALUES ('2026-07-01', '16:00', '20:00', 5, 0)")
        cursor.execute("INSERT INTO shifts (date, start_time, end_time, slots, filled) VALUES ('2026-07-02', '08:00', '12:00', 5, 0)")
        cursor.execute("INSERT INTO shifts (date, start_time, end_time, slots, filled) VALUES ('2026-07-02', '12:00', '16:00', 5, 0)")
        db.commit()

    cursor.execute(
        """SELECT s.*, 
           (SELECT 1 FROM volunteer_shifts WHERE volunteer_id = ? AND shift_id = s.shift_id) as signed_up
           FROM shifts s ORDER BY s.date, s.start_time""",
        (user['user_id'],)
    )
    rows = cursor.fetchall()
    return jsonify({'shifts': [dict(row) for row in rows]}), 200

@helpdesk_bp.route('/shifts/signup', methods=['POST'])
@require_role('volunteer')
def signup_shift():
    data = request.get_json()
    shift_id = data.get('shift_id')
    if not shift_id:
        return jsonify({'error': 'shift_id required'}), 400
        
    user = get_current_user()
    db = get_db()
    cursor = db.cursor()
    
    # Check if shift exists
    cursor.execute("SELECT * FROM shifts WHERE shift_id = ?", (shift_id,))
    shift = cursor.fetchone()
    if not shift:
        return jsonify({'error': 'Shift not found'}), 404
        
    # Check if already signed up
    cursor.execute("SELECT * FROM volunteer_shifts WHERE volunteer_id = ? AND shift_id = ?", (user['user_id'], shift_id))
    if cursor.fetchone():
        return jsonify({'error': 'Already signed up for this shift'}), 409
        
    # Check if slots are full
    if shift['filled'] >= shift['slots']:
        return jsonify({'error': 'Shift is full'}), 400
        
    try:
        cursor.execute("INSERT INTO volunteer_shifts (volunteer_id, shift_id) VALUES (?, ?)", (user['user_id'], shift_id))
        cursor.execute("UPDATE shifts SET filled = filled + 1 WHERE shift_id = ?", (shift_id,))
        db.commit()
    except Exception as e:
        db.rollback()
        return jsonify({'error': 'Failed to sign up for shift', 'details': str(e)}), 500
        
    return jsonify({'message': 'Successfully signed up for shift'}), 200

@helpdesk_bp.route('/history/<room_id>', methods=['GET'])
def get_chat_history(room_id):
    user = get_current_user()
    if not user:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        """SELECT hm.message_id, hm.room_id, hm.sender_id, hm.sender_role, hm.message, CAST(hm.timestamp AS TEXT) as timestamp, u.name as sender_name
           FROM helpdesk_messages hm
           JOIN users u ON hm.sender_id = u.id
           WHERE hm.room_id = ? ORDER BY hm.timestamp ASC""",
        (room_id,)
    )
    rows = cursor.fetchall()
    return jsonify([dict(row) for row in rows]), 200


# SocketIO events
@socketio.on('join_room', namespace='/helpdesk')
def handle_join_room(data):
    room = data.get('room_id')
    user_id = data.get('sender_id')
    role = data.get('sender_role')
    name = data.get('sender_name', 'User')
    
    join_room(room)
    
    if role == 'volunteer':
        join_room('volunteers_lobby')
        online_volunteers[user_id] = name
        emit('online_status', {'online_volunteers': online_volunteers}, to=room)
        # Direct list update to the newly connected support volunteer
        emit('active_rooms_update', {'rooms': active_rooms})
    else:
        active_rooms[room] = {
            'room_id': room,
            'user_name': name,
            'role': role,
            'created_at': datetime.utcnow().isoformat()
        }
        emit('active_rooms_update', {'rooms': active_rooms}, to='volunteers_lobby')
        
    emit('joined', {'room': room, 'online_volunteers': online_volunteers}, to=room)

@socketio.on('leave_room', namespace='/helpdesk')
def handle_leave_room(data):
    room = data.get('room_id')
    user_id = data.get('sender_id')
    role = data.get('sender_role')
    
    leave_room(room)
    
    if role == 'volunteer':
        leave_room('volunteers_lobby')
        if user_id in online_volunteers:
            del online_volunteers[user_id]
            emit('online_status', {'online_volunteers': online_volunteers}, broadcast=True)
    else:
        if room in active_rooms:
            del active_rooms[room]
            emit('active_rooms_update', {'rooms': active_rooms}, to='volunteers_lobby')
            
    emit('left', {'room': room, 'online_volunteers': online_volunteers}, to=room)

@socketio.on('send_message', namespace='/helpdesk')
def handle_send_message(data):
    room = data.get('room_id')
    message = data.get('message')
    sender_id = data.get('sender_id')
    sender_role = data.get('sender_role')
    if not sender_id:
        emit('error', {'message': 'Unauthorized'})
        return
        
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO helpdesk_messages (room_id, sender_id, sender_role, message) VALUES (?, ?, ?, ?)",
        (room, sender_id, sender_role, message)
    )
    db.commit()
    
    emit('new_message', {
        'sender_id': sender_id,
        'sender_role': sender_role,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room)

@socketio.on('typing', namespace='/helpdesk')
def handle_typing(data):
    room = data.get('room_id')
    sender_id = data.get('sender_id')
    is_typing = data.get('is_typing', True)
    emit('typing_status', {'sender_id': sender_id, 'is_typing': is_typing}, to=room, include_self=False)

@socketio.on('escalate_to_admin', namespace='/helpdesk')
def handle_escalate(data):
    room = data.get('room_id')
    reason = data.get('reason')
    sender_id = data.get('sender_id')
    
    emit('escalation_alert', {'room_id': room, 'reason': reason}, to=room)
    log_audit(sender_id or 0, 'student', 'HELP_DESK_ESCALATED', None, {'room_id': room, 'reason': reason})
