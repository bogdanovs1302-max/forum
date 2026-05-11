import os
import uuid
import requests
from flask import render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt
from app.models import User, Topic, Post
from app.forms import RegisterForm, LoginForm, TopicForm, PostForm
from app.api import api_bp

def save_avatar(form_picture):
    random_hex = uuid.uuid4().hex
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(current_app.root_path, 'static/uploads', picture_fn)
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)
    form_picture.save(picture_path)
    return picture_fn

def init_routes(app):
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        topics = Topic.query.all()
        quote = None
        try:
            resp = requests.get('https://api.quotable.io/random', timeout=3)
            if resp.status_code == 200:
                data = resp.json()
                quote = {'content': data['content'], 'author': data['author']}
        except Exception:
            quote = None
        return render_template('index.html', topics=topics, quote=quote)

    @app.route('/topic/<int:topic_id>')
    def topic_detail(topic_id):
        topic = Topic.query.get_or_404(topic_id)
        form = PostForm()
        posts = Post.query.filter_by(topic_id=topic_id).all()
        return render_template('topic_detail.html', topic=topic, form=form, posts=posts)

    @app.route('/post/create/<int:topic_id>', methods=['POST'])
    @login_required
    def create_post(topic_id):
        if current_user.is_banned:
            flash('Вы забанены и не можете писать посты', 'danger')
            return redirect(url_for('topic_detail', topic_id=topic_id))
        form = PostForm()
        if form.validate_on_submit():
            post = Post(content=form.content.data, user_id=current_user.id, topic_id=topic_id)
            db.session.add(post)
            db.session.commit()
            flash('Пост добавлен!', 'success')
        return redirect(url_for('topic_detail', topic_id=topic_id))

    @app.route('/post/delete/<int:post_id>')
    @login_required
    def delete_post(post_id):
        post = Post.query.get_or_404(post_id)
        if current_user.is_banned:
            flash('Вы забанены и не можете удалять посты', 'danger')
            return redirect(url_for('topic_detail', topic_id=post.topic_id))
        if current_user.role in ['admin', 'moderator'] or current_user.id == post.user_id:
            db.session.delete(post)
            db.session.commit()
            flash('Пост удален', 'success')
        else:
            flash('Нет прав для удаления', 'danger')
        return redirect(url_for('topic_detail', topic_id=post.topic_id))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = RegisterForm()
        if form.validate_on_submit():
            hashed = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
            role = 'admin' if User.query.count() == 0 else 'user'
            avatar_name = 'default.png'
            if form.avatar.data:
                avatar_name = save_avatar(form.avatar.data)
            user = User(username=form.username.data,
                        password_hash=hashed,
                        role=role,
                        avatar=avatar_name)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна!', 'success')
            return redirect(url_for('login'))
        return render_template('register.html', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and bcrypt.check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                if user.is_banned:
                    flash('⚠️ Вы забанены. Вы можете только читать форум, но не писать.', 'warning')
                return redirect(url_for('index'))
            flash('Неверные данные', 'danger')
        return render_template('login.html', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('index'))

    @app.route('/topic/new', methods=['GET', 'POST'])
    @login_required
    def new_topic():
        if current_user.is_banned:
            flash('Вы забанены и не можете создавать темы', 'danger')
            return redirect(url_for('index'))
        form = TopicForm()
        if form.validate_on_submit():
            topic = Topic(title=form.title.data, user_id=current_user.id)
            db.session.add(topic)
            db.session.commit()
            flash('Тема создана!', 'success')
            return redirect(url_for('index'))
        return render_template('topic_form.html', form=form)

    @app.route('/topic/delete/<int:topic_id>')
    @login_required
    def delete_topic(topic_id):
        if current_user.is_banned:
            flash('Вы забанены и не можете удалять темы', 'danger')
            return redirect(url_for('index'))
        topic = Topic.query.get_or_404(topic_id)
        if current_user.role in ['admin', 'moderator'] or current_user.id == topic.user_id:
            db.session.delete(topic)
            db.session.commit()
            flash('Тема удалена', 'success')
        else:
            flash('Нет прав для удаления темы', 'danger')
        return redirect(url_for('index'))

    @app.route('/admin/users')
    @login_required
    def admin_users():
        if current_user.is_banned:
            flash('Вы забанены', 'danger')
            return redirect(url_for('index'))
        if current_user.role not in ['admin', 'moderator']:
            return redirect(url_for('index'))
        users = User.query.all()
        return render_template('admin_users.html', users=users, current_user=current_user)

    @app.route('/admin/ban/<int:user_id>')
    @login_required
    def ban_user(user_id):
        if current_user.is_banned:
            flash('Вы забанены', 'danger')
            return redirect(url_for('index'))
        if current_user.role not in ['admin', 'moderator']:
            flash('Нет прав', 'danger')
            return redirect(url_for('index'))
        user = User.query.get_or_404(user_id)
        if user.id == current_user.id:
            flash('Нельзя забанить самого себя', 'danger')
            return redirect(url_for('admin_users'))
        if user.role == 'admin' and current_user.role != 'admin':
            flash('Нельзя забанить админа', 'danger')
        else:
            user.is_banned = True
            db.session.commit()
            flash(f'Пользователь {user.username} забанен', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/unban/<int:user_id>')
    @login_required
    def unban_user(user_id):
        if current_user.is_banned:
            flash('Вы забанены', 'danger')
            return redirect(url_for('index'))
        if current_user.role not in ['admin', 'moderator']:
            flash('Нет прав', 'danger')
            return redirect(url_for('index'))
        user = User.query.get_or_404(user_id)
        user.is_banned = False
        db.session.commit()
        flash(f'Пользователь {user.username} разбанен', 'success')
        return redirect(url_for('admin_users'))

    @app.route('/admin/role/<int:user_id>/<role>')
    @login_required
    def set_role(user_id, role):
        if current_user.is_banned:
            flash('Вы забанены', 'danger')
            return redirect(url_for('index'))
        if current_user.role != 'admin':
            flash('Только админ может менять роли', 'danger')
            return redirect(url_for('index'))
        user = User.query.get_or_404(user_id)
        if role in ['user', 'moderator', 'admin']:
            user.role = role
            db.session.commit()
            flash(f'Роль {user.username} изменена на {role}', 'success')
        return redirect(url_for('admin_users'))
