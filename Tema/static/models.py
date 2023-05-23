from flask_sqlalchemy import SQLAlchemy
from classroom_manager import login_manager, db
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(25), nullable=False)
    last_name = db.Column(db.String(25), nullable=False)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(254), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default="defaultuser-icon.png")
    status = db.Column(db.String(10), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    notes = db.relationship('Note', backref='author', lazy=True)
    assignments = db.relationship('Assignment', backref='author', lazy=True)
    messages = db.relationship('Message', backref='author', lazy=True)
    membership = db.relationship('Membership', backref='classroom', lazy=True)
    submission = db.relationship('AssignmentSubmission', backref='submission', lazy=True)

    def __repr__(self):
        return f"User(username: '{self.username}', email: '{self.email}', profile_img: '{self.image_file}')"
