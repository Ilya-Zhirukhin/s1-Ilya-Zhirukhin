from flask import session, redirect, url_for, request
from flask_login import current_user
from flask_socketio import SocketIO, emit, send, disconnect, join_room, leave_room
from Tema import socketio
from Tema.models import User, Classroom, Membership, Channel, Message, Note, DirectMessage
from Tema.utils import generate_code
from Tema import db
from datetime import datetime

users = {}


@socketio.on('connect')
def handle_connections():
    if not current_user.is_authenticated:
        disconnect()
        print()
        return redirect(url_for('login'))
    user = User.query.filter(User.id == current_user.get_id()).first()
    users[user.username] = request.sid
    user_memberships = Membership.query.filter(Membership.user_id == current_user.get_id())
    [join_room(str(user_membership.classroom_id)) for user_membership in
     user_memberships]  # Instead of making a room for every channel we will make a room for every classroom


@socketio.on('disconnect')
def handle_disconnections():
    if not current_user.is_authenticated:
        disconnect()
        return redirect(url_for('login'))
