from flask import Blueprint, request, jsonify, g
from flask_socketio import emit, join_room, leave_room
from app import socketio
from models.db import get_db
from middleware.auth import get_current_user, require_role
from middleware.audit import log_audit
from datetime import datetime

helpdesk_bp = Blueprint('helpdesk', __name__)

# REST endpoints for shifts etc.
@helpdesk_bp.route('/shifts', methods=['GET'])
@require_role('volunteer')
def get_shifts():
    # Placeholder
    return jsonify({'shifts': []}), 200

@helpdesk_bp.route('/shifts/signup', methods=['POST'])
@require_role('volunteer')
def signup_shift():
    # Placeholder
    return jsonify({'message': 'Shift signed up'}), 200

# SocketIO events
@socketio.on('join_room', namespace='/helpdesk')
def handle_join_room(data):
    room = data.get('room_id')
    join_room(room)
    emit('joined', {'room': room}, room=room)

@socketio.on('send_message', namespace='/helpdesk')
def handle_send_message(data):
    room = data.get('room_id')
    message = data.get('message')
    # Get sender from request (we have access to request.sid, but we need user_id)
    # We'll store sender in session or token; for simplicity, we'll pass in data.
    # Better to authenticate via token in query string.
    # For MVP, we assume authenticated via token and passed in data.
    sender_id = data.get('sender_id')
    sender_role = data.get('sender_role')
    if not sender_id:
        emit('error', {'message': 'Unauthorized'})
        return
    # Save to DB
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO helpdesk_messages (room_id, sender_id, sender_role, message) VALUES (?, ?, ?, ?)",
        (room, sender_id, sender_role, message)
    )
    db.commit()
    # Broadcast
    emit('new_message', {
        'sender_id': sender_id,
        'sender_role': sender_role,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }, room=room)

@socketio.on('typing', namespace='/helpdesk')
def handle_typing(data):
    room = data.get('room_id')
    sender = data.get('sender_id')
    emit('typing', {'sender': sender}, room=room, include_self=False)

@socketio.on('escalate_to_admin', namespace='/helpdesk')
def handle_escalate(data):
    room = data.get('room_id')
    reason = data.get('reason')
    # Create a complaint
    # For now, just notify admin via a separate room or log
    emit('escalation', {'room': room, 'reason': reason}, room='admin_room')
    log_audit(0, 'system', 'ESCALATE', None, {'room': room, 'reason': reason})
