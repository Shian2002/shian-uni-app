"""后台管理 API 路由。

主应用仍持有积分、充值和审计等核心业务函数；这里仅负责把后台
HTTP 接口集中注册，避免继续膨胀 app.py。
"""

import json

from flask import jsonify, request
from flask_login import current_user, login_required
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash

from models import AdminAuditLog, Comment, Membership, Post, RechargeOrder, Report, User


def _require_admin():
    if not current_user.is_authenticated or not current_user.is_admin:
        return jsonify({'error': '需要管理员权限'}), 403
    return None


def register_admin_routes(app, db, services):
    """注册 /api/admin/* 路由。

    services:
      - record_admin_audit
      - add_points
      - confirm_recharge_order_once
      - refund_recharge_order_once
    """

    record_admin_audit = services['record_admin_audit']
    add_points = services['add_points']
    confirm_recharge_order_once = services['confirm_recharge_order_once']
    refund_recharge_order_once = services['refund_recharge_order_once']

    @app.route('/api/admin/reports')
    @login_required
    def api_admin_reports():
        """管理员：获取举报列表"""
        denied = _require_admin()
        if denied:
            return denied

        status = request.args.get('status', 'pending')
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        query = Report.query
        if status in ('pending', 'resolved', 'dismissed'):
            query = query.filter_by(status=status)

        pagination = query.order_by(Report.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )

        items = []
        for report in pagination.items:
            reporter = db.session.get(User, report.user_id)
            items.append({
                'id': report.id,
                'reporterId': report.user_id,
                'reporterName': reporter.username if reporter else '匿名',
                'targetType': report.target_type,
                'targetId': report.target_id,
                'reason': report.reason,
                'status': report.status,
                'createdAt': report.created_at.isoformat() if report.created_at else None,
            })

        return jsonify({'reports': items, 'total': pagination.total, 'page': page, 'has_next': pagination.has_next})

    @app.route('/api/admin/reports/<int:rid>/resolve', methods=['POST'])
    @login_required
    def api_admin_report_resolve(rid):
        """管理员：处理举报"""
        denied = _require_admin()
        if denied:
            return denied

        report = db.session.get(Report, rid)
        if not report:
            return jsonify({'error': '举报不存在'}), 404

        data = request.get_json(silent=True) or {}
        action = data.get('action')
        if action == 'resolve':
            report.status = 'resolved'
            if report.target_type == 'post':
                post = db.session.get(Post, report.target_id)
                if post:
                    post.is_hidden = True
            elif report.target_type == 'comment':
                comment = db.session.get(Comment, report.target_id)
                if comment:
                    db.session.delete(comment)
        elif action == 'dismiss':
            report.status = 'dismissed'
        else:
            return jsonify({'error': '无效操作，可选: resolve/dismiss'}), 400

        record_admin_audit(
            'report_' + action,
            'report',
            report.id,
            {'target_type': report.target_type, 'target_id': report.target_id, 'reason': report.reason},
        )
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/admin/posts/<int:pid>/pin', methods=['POST'])
    @login_required
    def api_admin_pin_post(pid):
        """管理员：置顶/取消置顶"""
        denied = _require_admin()
        if denied:
            return denied
        post = db.session.get(Post, pid)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        data = request.get_json(silent=True) or {}
        pinned = data.get('pinned', not post.is_pinned)
        post.is_pinned = bool(pinned)
        record_admin_audit('post_pin', 'post', post.id, {'pinned': bool(pinned), 'title': post.title})
        db.session.commit()
        return jsonify({'ok': True, 'isPinned': post.is_pinned})

    @app.route('/api/admin/posts/<int:pid>/feature', methods=['POST'])
    @login_required
    def api_admin_feature_post(pid):
        """管理员：加精/取消加精"""
        denied = _require_admin()
        if denied:
            return denied
        post = db.session.get(Post, pid)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        data = request.get_json(silent=True) or {}
        featured = data.get('featured', not post.is_featured)
        post.is_featured = bool(featured)
        record_admin_audit('post_feature', 'post', post.id, {'featured': bool(featured), 'title': post.title})
        db.session.commit()
        return jsonify({'ok': True, 'isFeatured': post.is_featured})

    @app.route('/api/admin/posts/<int:pid>/hide', methods=['POST'])
    @login_required
    def api_admin_hide_post(pid):
        """管理员：隐藏/显示帖子"""
        denied = _require_admin()
        if denied:
            return denied
        post = db.session.get(Post, pid)
        if not post:
            return jsonify({'error': '帖子不存在'}), 404

        data = request.get_json(silent=True) or {}
        hidden = data.get('hidden', not post.is_hidden)
        post.is_hidden = bool(hidden)
        record_admin_audit('post_hide', 'post', post.id, {'hidden': bool(hidden), 'title': post.title})
        db.session.commit()
        return jsonify({'ok': True, 'isHidden': post.is_hidden})

    @app.route('/api/admin/summary')
    @login_required
    def api_admin_summary():
        """管理员：后台概览数据"""
        denied = _require_admin()
        if denied:
            return denied

        return jsonify({
            'users': User.query.count(),
            'posts': Post.query.count(),
            'hidden_posts': Post.query.filter_by(is_hidden=True).count(),
            'pending_reports': Report.query.filter_by(status='pending').count(),
            'pending_recharge_orders': RechargeOrder.query.filter_by(status='pending').count(),
        })

    @app.route('/api/admin/users')
    @login_required
    def api_admin_users():
        """管理员：用户列表"""
        denied = _require_admin()
        if denied:
            return denied

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        keyword = (request.args.get('q') or '').strip()

        query = User.query
        if keyword:
            like = f'%{keyword}%'
            query = query.filter(or_(User.username.like(like), User.email.like(like), User.phone.like(like)))

        pagination = query.order_by(User.id.desc()).paginate(page=page, per_page=per_page, error_out=False)
        items = []
        for user in pagination.items:
            membership = Membership.query.filter_by(user_id=user.id).first()
            items.append({
                'id': user.id,
                'username': user.username,
                'email': user.email or '',
                'phone': user.phone or '',
                'is_admin': bool(user.is_admin),
                'points': membership.points if membership else 0,
                'level': membership.level if membership else 'free',
                'created_at': user.created_at.isoformat() if user.created_at else None,
            })

        return jsonify({'users': items, 'total': pagination.total, 'page': page, 'has_next': pagination.has_next})

    @app.route('/api/admin/posts')
    @login_required
    def api_admin_posts():
        """管理员：帖子列表，包含隐藏内容"""
        denied = _require_admin()
        if denied:
            return denied

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        status = (request.args.get('status') or 'all').strip()
        keyword = (request.args.get('q') or '').strip()

        query = Post.query
        if status == 'hidden':
            query = query.filter_by(is_hidden=True)
        elif status == 'visible':
            query = query.filter_by(is_hidden=False)
        if keyword:
            like = f'%{keyword}%'
            query = query.filter(or_(Post.title.like(like), Post.content.like(like), Post.tags.like(like)))

        pagination = query.order_by(Post.is_pinned.desc(), Post.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )
        items = []
        for post in pagination.items:
            author = db.session.get(User, post.user_id)
            items.append({
                'id': post.id,
                'userId': post.user_id,
                'username': author.username if author else '匿名',
                'title': post.title,
                'category': post.category,
                'likesCount': post.likes_count,
                'commentsCount': post.comments_count,
                'isFeatured': bool(post.is_featured),
                'isPinned': bool(post.is_pinned),
                'isHidden': bool(post.is_hidden),
                'createdAt': post.created_at.isoformat() if post.created_at else None,
            })

        return jsonify({'posts': items, 'total': pagination.total, 'page': page, 'has_next': pagination.has_next})

    @app.route('/api/admin/recharge/orders')
    @login_required
    def api_admin_recharge_orders():
        """管理员：充值订单列表"""
        denied = _require_admin()
        if denied:
            return denied

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        status = (request.args.get('status') or 'all').strip()

        query = RechargeOrder.query
        if status in ('pending', 'paid', 'refunded', 'cancelled'):
            query = query.filter_by(status=status)

        pagination = query.order_by(RechargeOrder.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)
        items = []
        for order in pagination.items:
            user = db.session.get(User, order.user_id)
            items.append({
                'id': order.id,
                'user_id': order.user_id,
                'username': user.username if user else '匿名',
                'package_name': order.package_name,
                'points_amount': order.points,
                'price': order.amount,
                'pay_method': order.pay_method,
                'payment_reference': order.payment_reference or '',
                'payment_proof': order.payment_proof or '',
                'status': order.status,
                'created_at': order.created_at.isoformat() if order.created_at else None,
                'verified_at': order.verified_at.isoformat() if order.verified_at else None,
                'paid_at': order.updated_at.isoformat() if order.status == 'paid' and order.updated_at else None,
                'refunded_at': order.refunded_at.isoformat() if order.refunded_at else None,
            })

        return jsonify({'orders': items, 'total': pagination.total, 'page': page, 'has_next': pagination.has_next})

    @app.route('/api/admin/audit-logs')
    @login_required
    def api_admin_audit_logs():
        """管理员：查看最近操作审计"""
        denied = _require_admin()
        if denied:
            return denied

        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        action = (request.args.get('action') or '').strip()

        query = AdminAuditLog.query
        if action:
            query = query.filter_by(action=action)

        pagination = query.order_by(AdminAuditLog.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )
        items = []
        for log in pagination.items:
            admin = db.session.get(User, log.admin_id)
            try:
                detail = json.loads(log.detail) if log.detail else {}
            except json.JSONDecodeError:
                detail = {'raw': log.detail}
            items.append({
                'id': log.id,
                'admin_id': log.admin_id,
                'admin_name': admin.username if admin else '未知管理员',
                'action': log.action,
                'target_type': log.target_type,
                'target_id': log.target_id,
                'detail': detail,
                'ip_address': log.ip_address or '',
                'created_at': log.created_at.isoformat() if log.created_at else None,
            })

        return jsonify({'logs': items, 'total': pagination.total, 'page': page, 'has_next': pagination.has_next})

    @app.route('/api/admin/change-password', methods=['POST'])
    @login_required
    def api_admin_change_password():
        """管理员：修改自己的登录密码"""
        denied = _require_admin()
        if denied:
            return denied

        data = request.get_json(silent=True) or {}
        old_password = data.get('old_password') or ''
        new_password = data.get('new_password') or ''
        confirm_password = data.get('confirm_password') or ''

        if not old_password:
            return jsonify({'error': '请输入当前密码'}), 400
        if len(new_password) < 12:
            return jsonify({'error': '新密码至少12个字符'}), 400
        if new_password != confirm_password:
            return jsonify({'error': '两次输入的新密码不一致'}), 400
        if not check_password_hash(current_user.password_hash, old_password):
            return jsonify({'error': '当前密码错误'}), 403
        if check_password_hash(current_user.password_hash, new_password):
            return jsonify({'error': '新密码不能与当前密码相同'}), 400

        current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        current_user.has_password = True
        record_admin_audit('admin_password_change', 'user', current_user.id, {'username': current_user.username})
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/admin/confirm-recharge', methods=['POST'])
    @login_required
    def api_admin_confirm_recharge():
        """管理员确认充值（手动加积分）"""
        denied = _require_admin()
        if denied:
            return denied

        data = request.get_json(silent=True) or {}
        order_id = data.get('order_id', 0)
        action = (data.get('action') or '').strip()

        if action == 'add':
            target_uid = data.get('user_id', 0)
            user_identifier = (data.get('user_identifier') or '').strip()
            points = data.get('points', 0)
            remark = (data.get('remark') or '').strip()
            target_user = None
            if target_uid:
                target_user = db.session.get(User, int(target_uid))
            elif user_identifier:
                target_user = User.query.filter(or_(
                    User.username == user_identifier,
                    User.email == user_identifier,
                    User.phone == user_identifier,
                )).first()
                if not target_user and user_identifier.isdigit():
                    target_user = db.session.get(User, int(user_identifier))
            if not target_user or not points:
                return jsonify({'error': '参数不完整'}), 400
            target_uid = target_user.id
            new_total = add_points(target_uid, 'admin_add', int(points), remark or '管理员加积分', commit=False)
            record_admin_audit(
                'points_add',
                'user',
                int(target_uid),
                {
                    'points': int(points),
                    'remark': remark or '管理员加积分',
                    'new_total': new_total,
                    'username': target_user.username,
                },
            )
            db.session.commit()
            return jsonify({'ok': True, 'user_id': target_uid, 'username': target_user.username, 'points': new_total, 'added': points})

        if action == 'refund':
            result = refund_recharge_order_once(order_id)
            if not result.get('ok'):
                status_code = 404 if result.get('status') is None else 400
                return jsonify({'error': result.get('error', '订单状态错误'), 'status': result.get('status')}), status_code
            record_admin_audit(
                'recharge_refund',
                'recharge_order',
                result.get('order_id'),
                {
                    'user_id': result.get('user_id'),
                    'refunded': result.get('refunded'),
                    'points': result.get('points'),
                    'credit_type': result.get('credit_type'),
                },
            )
            db.session.commit()
            return jsonify(result)

        result = confirm_recharge_order_once(order_id)
        if not result.get('ok'):
            status_code = 404 if result.get('status') is None else 400
            return jsonify({'error': result.get('error', '订单状态错误'), 'status': result.get('status')}), status_code
        record_admin_audit(
            'recharge_confirm',
            'recharge_order',
            result.get('order_id'),
            {'user_id': result.get('user_id'), 'added': result.get('added'), 'points': result.get('points')},
        )
        db.session.commit()
        return jsonify(result)
