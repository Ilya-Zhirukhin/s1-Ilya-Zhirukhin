from flask import Flask, render_template, url_for, flash, redirect, request, jsonify
from Tema.forms import RegistrationForm, LoginForm, EditProfileForm, DeleteProfileForm, ResetPasswordForm, \
    ResetPasswordForm_2
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
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

import json

app.config['MAIL_SERVER'] = 'smtp.mail.ru'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'for_semestr_work@mail.ru'
app.config['MAIL_PASSWORD'] = '4UyJ8bda8KgvyC27xZAi'
# RZHI1u1taet^
app.config['MAIL_DEFAULT_SENDER'] = 'for_semestr_work@mail.ru'
app.config['MAIL_USE_MANAGEMENT_COMMANDS'] = True  # Включение поддержки асинхронной отправки

mail = Mail(app)
serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])


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
            flash('Login unsuccessful, please try again.', 'error')

    # Create GitHub OAuth URL for login with GitHub
    github_login_url = url_for('login_github')

    return render_template('login.html', form=form, title='Login', github_login_url=github_login_url)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    form = ResetPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(email, salt='reset-password')
            reset_link = url_for('confirm_reset_password', token=token, _external=True)
            message = Message('Сброс пароля', recipients=[email])
            message.body = f'Для сброса пароля пройдите по ссылке: {reset_link}'
            mail.send(message)  # Отправка асинхронного письма
            flash('Инструкции по сбросу пароля были отправлены на вашу почту.', 'info')
            return redirect(url_for('login'))
        flash('Адрес электронной почты не найден.', 'error')
    return render_template('reset_password.html', form=form, title='Сброс пароля')


@app.route('/confirm_reset_password/<token>', methods=['GET', 'POST'])
def confirm_reset_password(token):
    form = ResetPasswordForm_2()
    if form.validate_on_submit():
        email = serializer.loads(token, salt='reset-password', max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user:
            # Обновление пароля пользователя
            user.password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")  # Hash the password

            db.session.commit()
            flash('Пароль успешно изменен.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Пользователь не найден.', 'error')
            return redirect(url_for('login'))

    return render_template('confirm_reset_password.html', form=form, token=token, title='Подтверждение сброса пароля')


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


yandex = oauth.remote_app(
    'yandex',
    consumer_key='86d4d51e635144e49df6fd48b5b64321',
    consumer_secret='ed6c48bcac5f426891e47f666330f657',
    request_token_params={'scope': 'login:email'},
    base_url='https://login.yandex.com/info',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://oauth.yandex.com/token',
    authorize_url='https://oauth.yandex.com/authorize'
)


@yandex.tokengetter
def get_yandex_token():
    return session.get('yandex_token')


@app.route('/login/yandex')
def login_yandex():
    return yandex.authorize(callback=url_for('yandex_authorized', _external=True))


@app.route('/login/yandex/callback')
@yandex.authorized_handler
def yandex_authorized(resp):
    next_page = request.args.get('next') or url_for('home')
    if resp is None:
        flash('Authorization failed.', 'danger')
        return redirect(next_page)

    access_token = resp['access_token']
    session['yandex_token'] = access_token

    user_info_data = yandex.get('https://login.yandex.ru/info', headers={'Authorization': f'OAuth {access_token}'}).data

    # Check response
    if not user_info_data:
        flash('Failed to fetch user data.', 'danger')
        return redirect(next_page)

    email = user_info_data['login'] + '@yandex.ru'

    user = User.query.filter_by(email=email).first()

    if user is None:
        new_user = User(
            first_name=user_info_data.get('first_name', ''),
            last_name=user_info_data.get('last_name', ''),
            username=user_info_data['login'],
            email=email,
            image_file=user_info_data.get('default_avatar_id', ''),
            status='yandex',
            password=access_token
        )
        db.session.add(new_user)
        db.session.commit()
        user = new_user

    login_user(user)
    flash('Successfully logged in via Yandex!', 'success')
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


@app.route('/app/chats', methods=['POST'])
def app_chats():
    # создается множество users, в котором будут храниться идентификаторы пользователей, связанные с сообщениями.
    # Создается пустой список contacts, который будет содержать информацию о контактах.
    # Выполняется запрос к базе данных, чтобы получить все сообщения, связанные с текущим пользователем (current_user.get_id()). Результат сохраняется в переменной messages.
    # Для каждого сообщения в messages проверяется, является ли идентификатор отправителя или получателя текущим пользователем. Если нет, то идентификатор добавляется в множество users.
    # Выполняется запрос к базе данных для получения информации о пользователях, идентификаторы которых находятся в множестве users. Результат сохраняется в переменной User.query.filter(User.id.in_(users)).all().
    # Для каждого пользователя создается объект contact с атрибутами id и name, которые соответствуют идентификатору пользователя и его имени соответственно. Объект contact добавляется в список contacts.
    # Возвращается результат вызова функции render_template, которая отображает шаблон chats.html с переданными аргументами title='Contacts', data=contacts и type='contact'.

    users, contacts = set(), []
    messages = DirectMessage.query.filter(
        (DirectMessage.receiver_id == current_user.get_id()) | (DirectMessage.sender_id == current_user.get_id())).all()
    [users.add(message.receiver_id) if int(message.receiver_id) != int(current_user.get_id()) else users.add(
        int(message.sender_id)) for message in messages]
    for user in User.query.filter(User.id.in_(users)).all():
        contact = SimpleNamespace()
        contact.id = user.id
        contact.name = user.username
        contacts.append(contact)
    return render_template('chats.html', title='Contacts', data=contacts, type='contact')


@app.route('/add-contact', methods=['POST'])
def add_contact():
    contact = User.query.filter(User.username == request.form['username']).first()
    if contact and int(contact.id) == int(current_user.get_id()):
        contact = None  #
    return jsonify({'name': contact.username, 'id': contact.id, 'img_url': url_for('static',
                                                                                   filename='imgs/defaultuser-icon.png')}) if contact and contact.id != current_user.get_id() else jsonify(
        {'error': 'user not found.'})


@app.route('/retrieve-directmessages/<user_id>', methods=['POST'])
def retrieve_directmessages(user_id):
    # Обработчик принимает параметр user_id, который представляет идентификатор пользователя, с которым нужно извлечь директные сообщения.
    # Выполняется запрос к базе данных для извлечения сообщений, удовлетворяющих следующим условиям:
    # sender_id равен user_id, а receiver_id равен идентификатору текущего пользователя (current_user.get_id()).
    # ИЛИ sender_id равен идентификатору текущего пользователя, а receiver_id равен user_id.
    # Результат сохраняется в переменной messages.
    # Создается словарь, содержащий ключ 'messages' и значение, которое представляет список словарей сообщений.
    # Для каждого сообщения в messages создается словарь с ключами 'content', 'date', 'author' и 'mein', которые представляют содержимое сообщения, дату, имя автора и флаг, указывающий, является ли текущий пользователь автором сообщения.
    # В словарь 'messages' добавляется созданный словарь для каждого сообщения в messages.
    # Возвращается JSON-ответ с данными о сообщениях.
    # Обработчик маршрута извлекает директные сообщения между заданным
    # пользователем и текущим пользователем, и возвращает их в формате JSON.
    # Каждое сообщение содержит информацию о содержимом, дате, авторе и флаге,
    # указывающем, является ли текущий пользователь автором сообщения.
    messages = DirectMessage.query.filter(
        (DirectMessage.sender_id == user_id) & (DirectMessage.receiver_id == current_user.get_id()) |
        (DirectMessage.sender_id == current_user.get_id()) & (DirectMessage.receiver_id == user_id)
    )
    return jsonify({
        'messages': [
            {
                'content': message.content,
                'date': message.date,
                'author': User.query.filter(User.id == message.sender_id).first().username,
                'mein': int(current_user.get_id()) == message.sender_id
            }
            for message in messages
        ]
    })
