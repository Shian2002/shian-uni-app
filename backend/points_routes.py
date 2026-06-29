"""会员与积分 API。"""

from datetime import datetime

from flask import jsonify, request
from flask_login import current_user, login_required

from models import Membership, PointLog


def register_points_routes(app, db, services):
    """注册会员和积分路由。

    services:
      - get_or_create_membership
      - create_daily_sign_in_once
      - use_points
    """
    get_or_create_membership = services['get_or_create_membership']
    create_daily_sign_in_once = services['create_daily_sign_in_once']
    use_points = services['use_points']

    @app.route('/api/membership')
    @login_required
    def api_membership():
        """获取当前用户会员信息。"""
        m = get_or_create_membership(current_user.id)
        expired = False
        if m.expire_at and m.expire_at < datetime.utcnow() and m.level != 'vip':
            m.level = 'free'
            m.expire_at = None
            db.session.commit()
            expired = True

        today = datetime.utcnow().strftime('%Y-%m-%d')
        signed_in_today = bool(PointLog.query.filter_by(user_id=current_user.id, action='sign_in')
            .filter(db.func.DATE(PointLog.created_at) == today).first())
        return jsonify({
            'level': m.level,
            'points': m.points,
            'expireAt': m.expire_at.isoformat() if m.expire_at else None,
            'expired': expired,
            'signed_in_today': signed_in_today,
        })

    @app.route('/api/membership/sign-in', methods=['POST'])
    @login_required
    def api_membership_sign_in():
        """每日签到（+300积分，每天 1 次）。"""
        result = create_daily_sign_in_once(current_user.id)
        if not result.get('ok'):
            return jsonify({'error': result.get('error', '今天已签到')}), 400
        return jsonify(result)

    @app.route('/api/points/log')
    @login_required
    def api_points_log():
        """积分日志列表。"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)

        pagination = PointLog.query.filter_by(user_id=current_user.id)\
            .order_by(PointLog.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)

        logs = [{
            'id': l.id,
            'action': l.action,
            'points': l.points,
            'description': l.description,
            'createdAt': l.created_at.isoformat() if l.created_at else None,
        } for l in pagination.items]

        return jsonify({
            'logs': logs,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
        })

    @app.route('/api/points/use', methods=['POST'])
    @login_required
    def api_points_use():
        """消费积分。"""
        data = request.get_json(silent=True) or {}
        action = (data.get('action') or '').strip()
        points = data.get('points', 0)

        if not action:
            return jsonify({'error': '缺少 action 参数'}), 400
        if not isinstance(points, int) or points <= 0:
            return jsonify({'error': 'points 须为正整数'}), 400

        result = use_points(current_user.id, action, points, data.get('description', ''))
        if not result.get('ok'):
            return jsonify(result), 400
        return jsonify(result)
