"""基础账号认证与绑定 API。"""

from flask import jsonify, request
from flask_login import current_user, login_required, login_user, logout_user
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import csrf
from models import User


def _user_payload(user, include_admin=False):
    payload = {
        'id': user.id,
        'username': user.username,
        'has_password': user.has_password,
        'avatar': user.avatar or '',
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }
    if include_admin:
        payload['is_admin'] = user.is_admin
    return payload


def register_auth_routes(app, db, services):
    """注册基础账号路由。

    services:
      - check_rate_limit
      - check_code
    """
    check_rate_limit = services['check_rate_limit']
    check_code = services['check_code']

    @app.route('/api/register', methods=['POST'])
    @csrf.exempt
    def api_register():
        data = request.get_json(silent=True) or {}
        username = (data.get('username') or '').strip()
        password = data.get('password') or ''

        if len(username) < 2 or len(username) > 20:
            return jsonify({'error': '用户名需2-20个字符'}), 400
        if len(password) < 6:
            return jsonify({'error': '密码至少6个字符'}), 400
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '用户名已存在'}), 400

        user = User(username=username, password_hash=generate_password_hash(password, method='pbkdf2:sha256'), has_password=True)
        db.session.add(user)
        db.session.commit()
        login_user(user, remember=True)
        return jsonify(_user_payload(user)), 201

    @app.route('/api/login', methods=['POST'])
    @csrf.exempt
    def api_login():
        data = request.get_json(silent=True) or {}
        if not check_rate_limit('login_' + request.remote_addr, 10, 300):
            return jsonify({'error': '登录尝试过于频繁，请5分钟后再试'}), 429
        login_id = (data.get('username') or '').strip()
        password = data.get('password') or ''

        user = User.query.filter(
            or_(
                User.username == login_id,
                User.email == login_id,
                User.phone == login_id
            )
        ).first()
        if not user or not check_password_hash(user.password_hash, password):
            return jsonify({'error': '用户名或密码错误'}), 401

        login_user(user, remember=True)
        return jsonify(_user_payload(user))

    @app.route('/api/logout', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_logout():
        logout_user()
        return jsonify({'ok': True})

    @app.route('/api/me')
    def api_me():
        if current_user.is_authenticated:
            return jsonify(_user_payload(current_user, include_admin=True))
        return jsonify({'guest': True})

    @app.route('/api/user/bindings')
    @login_required
    def api_user_bindings():
        """查询当前用户的绑定信息。"""
        return jsonify({
            'username': current_user.username,
            'email': current_user.email or '',
            'phone': current_user.phone or '',
            'has_password': current_user.has_password,
            'oauth_gitee': bool(current_user.oauth_gitee),
            'oauth_qq': bool(current_user.oauth_qq),
            'oauth_wechat': bool(current_user.oauth_wechat)
        })

    @app.route('/api/bind/email', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bind_email():
        """绑定邮箱（需验证码）。"""
        data = request.get_json(silent=True) or {}
        email = (data.get('email') or '').strip()
        code = (data.get('code') or '').strip()
        if not email or not code:
            return jsonify({'error': '请填写完整'}), 400
        if not check_code('email_' + email, code):
            return jsonify({'error': '验证码错误或已过期'}), 400
        existing = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing:
            return jsonify({'error': '该邮箱已被其他账号绑定'}), 400
        current_user.email = email
        db.session.commit()
        return jsonify({'ok': True, 'email': email})

    @app.route('/api/bind/phone', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bind_phone():
        """绑定手机号（需验证码）。"""
        data = request.get_json(silent=True) or {}
        phone = (data.get('phone') or '').strip()
        code = (data.get('code') or '').strip()
        if not phone or not code:
            return jsonify({'error': '请填写完整'}), 400
        if not check_code('sms_' + phone, code):
            return jsonify({'error': '验证码错误或已过期'}), 400
        existing = User.query.filter(User.phone == phone, User.id != current_user.id).first()
        if existing:
            return jsonify({'error': '该手机号已被其他账号绑定'}), 400
        current_user.phone = phone
        db.session.commit()
        return jsonify({'ok': True, 'phone': phone})

    @app.route('/api/bind/password', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bind_password():
        """设置/修改密码。"""
        data = request.get_json(silent=True) or {}
        old_pw = data.get('old_password') or ''
        new_pw = data.get('new_password') or ''

        if len(new_pw) < 6:
            return jsonify({'error': '密码至少6个字符'}), 400
        if current_user.has_password and not check_password_hash(current_user.password_hash, old_pw):
            return jsonify({'error': '原密码不正确'}), 400

        current_user.password_hash = generate_password_hash(new_pw, method='pbkdf2:sha256')
        current_user.has_password = True
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/unbind/email', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_unbind_email():
        """解绑邮箱。"""
        if not current_user.has_password and not current_user.phone:
            return jsonify({'error': '请先设置密码或绑定手机号后再解绑邮箱'}), 400
        current_user.email = None
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/unbind/phone', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_unbind_phone():
        """解绑手机号。"""
        if not current_user.has_password and not current_user.email:
            return jsonify({'error': '请先设置密码或绑定邮箱后再解绑手机号'}), 400
        current_user.phone = None
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/user/change-username', methods=['POST'])
    @csrf.exempt
    @login_required
    def api_user_change_username():
        """修改用户名。"""
        data = request.get_json(silent=True) or {}
        new_username = (data.get('new_username', '') or '').strip()
        if not new_username or len(new_username) < 2:
            return jsonify({'error': '用户名至少2个字符'}), 400
        if current_user.has_password:
            current_password = data.get('current_password', '')
            if not current_password:
                return jsonify({'error': '请输入当前密码'}), 400
            if not check_password_hash(current_user.password_hash, current_password):
                return jsonify({'error': '当前密码错误'}), 403
        if User.query.filter_by(username=new_username).first():
            return jsonify({'error': '用户名已被使用'}), 400
        old_username = current_user.username
        current_user.username = new_username
        db.session.commit()
        return jsonify({'ok': True, 'old_username': old_username, 'new_username': new_username})

    @app.route('/api/user/change-password', methods=['POST'])
    @csrf.exempt
    @login_required
    def api_user_change_password():
        """修改/设置密码。"""
        data = request.get_json(silent=True) or {}
        new_password = data.get('new_password', '')
        if not new_password or len(new_password) < 4:
            return jsonify({'error': '新密码至少4个字符'}), 400
        if current_user.has_password:
            old_password = data.get('old_password', '')
            if not old_password:
                return jsonify({'error': '请输入当前密码'}), 400
            if not check_password_hash(current_user.password_hash, old_password):
                return jsonify({'error': '当前密码错误'}), 403
        current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        current_user.has_password = True
        db.session.commit()
        return jsonify({'ok': True})
