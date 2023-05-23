from flask import Flask, render_template, url_for, flash, redirect, request, jsonify
from classroom_manager.forms import RegistrationForm, LoginForm, EditProfileForm, DeleteProfileForm
from classroom_manager import app, bcrypt, db, socketio
from classroom_manager.models import User, Classroom, Membership, Channel, Message, Note, Assignment, DirectMessage, \
    AssignmentSubmission
from flask_login import login_user, current_user, logout_user, login_required
from classroom_manager.utils import generate_code
from werkzeug.utils import secure_filename
from types import SimpleNamespace
from dateutil import parser
import os
from flask import session, make_response, g, abort, session, redirect, request, Flask, render_template, url_for, flash
from flask_dance.contrib.github import make_github_blueprint, github
from flask_dance.consumer import oauth_authorized
from flask_oauthlib.client import OAuth


@app.route("/")
@app.route("/home")
def home():
    return render_template("home.html", title='Home Page')


@app.route("/register", methods=["GET", "POST"])  # Make sure the form tag has the method, "POST"
def register():
    if current_user.is_authenticated:
        return redirect(url_for("__app__"))

    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")  # Hash the password
        new_user = User(first_name=form.name.data, last_name=form.last_name.data, username=form.username.data,
                        email=form.email.data, status=form.student_or_teacher.data, password=hashed_password)
        db.session.add(new_user)  # Add the new user to the database queue
        db.session.commit()  # Commit all the changes in the queue
        return redirect(url_for('login'))
    return render_template("register.html", form=form, title='Register')
