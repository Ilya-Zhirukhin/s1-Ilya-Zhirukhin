from flask import Flask, render_template, url_for, flash, redirect, request, jsonify
from Tema.forms import RegistrationForm, LoginForm, EditProfileForm, DeleteProfileForm
from Tema import app, bcrypt, db, socketio
from Tema.models import User, Classroom, Membership, Channel, Message, Note, Assignment, DirectMessage, \
    AssignmentSubmission
from flask_login import login_user, current_user, logout_user, login_required
# from Tema.utils import generate_code
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


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Successfully logged in!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('__app__'))
        else:
            flash('Login unsuccessful, please try again.', 'danger')

    # Create GitHub OAuth URL for login with GitHub
    github_login_url = url_for('login_github')

    return render_template('login.html', form=form, title='Login', github_login_url=github_login_url)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home"))


oauth = OAuth(app)
github = oauth.remote_app(
    'github',
    consumer_key='fcea9d2bf64321447a57',
    consumer_secret='64e2c48ba1b1c3f9c0dfde7417a96014bb544113',
    request_token_params={'scope': 'user:email'},
    base_url='https://api.github.com/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize'
)


@github.tokengetter
def get_github_token():
    return session.get('github_token')


@app.route('/login/github')
def login_github():
    return github.authorize(callback=url_for('github_authorized', _external=True))


@app.route('/login/github/callback')
@github.authorized_handler
def github_authorized(resp):
    next_page = request.args.get('next') or url_for('home')
    if resp is None:
        flash('Authorization failed.', 'danger')
        return redirect(next_page)

    access_token = resp['access_token']
    session['github_token'] = access_token

    user_info = github.get('user').data
    email = user_info['login'] + '@mail.ru'

    # Check if the user with the given email already exists in the database
    user = User.query.filter_by(email=email).first()

    if user is None:
        # User doesn't exist, create a new user with the GitHub information
        new_user = User(first_name=user_info['name'], last_name=user_info['name'], username=user_info['login'],
                        email=email, image_file=user_info['avatar_url'], status='github',
                        password=access_token)  # Set a dummy password for GitHub users
        db.session.add(new_user)
        db.session.commit()
        user = new_user

    login_user(user)
    flash('Successfully logged in via Github!', 'success')
    return redirect(url_for('user_profile'))


@app.route('/join-team', methods=['POST'])
def join_team():
    team_code = request.form['code']
    if team_code:
        classroom_id = Classroom.query.filter(Classroom.code == team_code).first()
        if classroom_id:
            new_membership = Membership(user_id=current_user.get_id(), classroom_id=classroom_id.id, role='regular')
            db.session.add(new_membership)
            db.session.commit()
            return jsonify({'result': {'id': classroom_id.id,
                                       'name': classroom_id.name},
                            'url_for_img': url_for('static', filename='imgs/' + classroom_id.image_file)})
        return jsonify({'error': "given code has either expired or is not valid"})
    return jsonify({'error': 'given code is invalid'})


@app.route("/upload", methods=["POST"])
@login_required
def upload():
    if 'file' not in request.files:
        flash('Файл не найден', 'error')
        return redirect(url_for('user_profile'))
    file = request.files['file']
    if file.filename == '':
        flash('Не выбран файл', 'error')
        return redirect(url_for('user_profile'))
    # Здесь добавьте код для сохранения и обновления аватара пользователя в базе данных
    if file:
        # Генерируем уникальное имя файла
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['IMAGE_UPLOADS'], filename))

        # Обновляем поле image_file у пользователя
        current_user.image_file = filename
        db.session.commit()

        flash('Аватар успешно изменен', 'success')
    else:
        flash('Ошибка при загрузке файла', 'error')

    return redirect(url_for('user_profile'))


@app.route("/user-profile", methods=["POST", "GET"])
@login_required
def user_profile():
    return render_template('profile.html', title='Профиль', user=current_user)


@app.route("/app")
@login_required
def __app__():
    return render_template("app.html", title='Application', user=current_user)


@app.route("/edit-profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Профиль успешно обновлен', 'success')
        return redirect(url_for('user_profile'))
    elif request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.email.data = current_user.email
    return render_template('edit_profile.html', form=form)


@app.route("/delete-profile", methods=["POST"])
@login_required
def delete_profile():
    # Additional logic for profile deletion, e.g., deleting related data
    db.session.delete(current_user)
    db.session.commit()
    response = {'success': True, 'message': 'Профиль успешно удален'}
    return jsonify(response)
