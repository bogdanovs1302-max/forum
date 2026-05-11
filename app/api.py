from flask import Blueprint, jsonify, request
from app.models import Topic, Post, User
from app import db, bcrypt
from functools import wraps

api_bp = Blueprint('api', __name__, url_prefix='/api')

def basic_auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not auth.username or not auth.password:
            return jsonify({'error': 'Authorization required'}), 401
        user = User.query.filter_by(username=auth.username).first()
        if not user or not bcrypt.check_password_hash(user.password_hash, auth.password):
            return jsonify({'error': 'Invalid credentials'}), 401
        if user.is_banned:
            return jsonify({'error': 'User is banned'}), 403
        return f(user, *args, **kwargs)
    return decorated

@api_bp.route('/topics')
def get_topics():
    topics = Topic.query.all()
    result = []
    for t in topics:
        result.append({
            'id': t.id,
            'title': t.title,
            'author': t.author.username,
            'posts_count': len(t.posts)
        })
    return jsonify(result)

@api_bp.route('/topics/<int:topic_id>')
def get_topic(topic_id):
    topic = Topic.query.get_or_404(topic_id)
    posts = []
    for p in topic.posts:
        posts.append({
            'id': p.id,
            'content': p.content,
            'author': p.author.username,
            'user_id': p.user_id
        })
    return jsonify({
        'id': topic.id,
        'title': topic.title,
        'author': topic.author.username,
        'posts': posts
    })

@api_bp.route('/posts', methods=['POST'])
@basic_auth_required
def create_post(user):
    data = request.get_json()
    if not data or 'topic_id' not in data or 'content' not in data:
        return jsonify({'error': 'Missing topic_id or content'}), 400
    topic = Topic.query.get(data['topic_id'])
    if not topic:
        return jsonify({'error': 'Topic not found'}), 404
    post = Post(content=data['content'], user_id=user.id, topic_id=topic.id)
    db.session.add(post)
    db.session.commit()
    return jsonify({'message': 'Post created', 'post_id': post.id}), 201
