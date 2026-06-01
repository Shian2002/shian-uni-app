"""付费内容与购买接口。"""

from flask import jsonify, request
from flask_login import current_user, login_required

from models import Master, PaidContent, Purchase


DISCLAIMER = '民俗文化内容，仅供学习参考'


def register_paid_content_routes(app, db, services):
    """注册付费内容相关路由。

    services:
      - use_points
      - add_points
    """

    use_points = services['use_points']
    add_points = services['add_points']

    @app.route('/api/paid-contents', methods=['GET'])
    def api_paid_contents_list():
        """付费内容列表，返回预览内容。"""
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 50)
        content_type = request.args.get('type', '')
        category = request.args.get('category', '')

        query = PaidContent.query
        if content_type:
            query = query.filter_by(content_type=content_type)
        if category:
            query = query.filter_by(category=category)

        pagination = query.order_by(PaidContent.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False,
        )

        items = []
        for content in pagination.items:
            master = db.session.get(Master, content.master_id) if content.master_id else None
            items.append({
                'id': content.id,
                'title': content.title,
                'contentType': content.content_type,
                'preview': content.preview,
                'price': content.price,
                'category': content.category,
                'masterName': master.display_name if master else None,
                'masterId': content.master_id,
                'createdAt': content.created_at.isoformat() if content.created_at else None,
            })

        return jsonify({
            'contents': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
            'disclaimer': DISCLAIMER,
        })

    @app.route('/api/paid-contents/<int:cid>')
    def api_paid_contents_detail(cid):
        """付费内容详情，已购买用户返回完整内容。"""
        content = db.session.get(PaidContent, cid)
        if not content:
            return jsonify({'error': '内容不存在'}), 404

        purchased = False
        if current_user.is_authenticated:
            purchased = Purchase.query.filter_by(user_id=current_user.id, content_id=cid).first() is not None

        result = {
            'id': content.id,
            'title': content.title,
            'contentType': content.content_type,
            'preview': content.preview,
            'price': content.price,
            'category': content.category,
            'purchased': purchased,
            'masterId': content.master_id,
            'createdAt': content.created_at.isoformat() if content.created_at else None,
            'disclaimer': DISCLAIMER,
        }

        if purchased:
            result['fullContent'] = content.full_content

        return jsonify(result)

    @app.route('/api/paid-contents/<int:cid>/purchase', methods=['POST'])
    @login_required
    def api_paid_contents_purchase(cid):
        """购买付费内容并扣除积分。"""
        content = db.session.get(PaidContent, cid)
        if not content:
            return jsonify({'error': '内容不存在'}), 404

        existing = Purchase.query.filter_by(user_id=current_user.id, content_id=cid).first()
        if existing:
            return jsonify({'error': '已购买该内容'}), 409

        spend = use_points(current_user.id, 'purchase', content.price, f'购买内容: {content.title}', commit=False)
        if not spend.get('ok'):
            return jsonify(spend), 400

        purchase = Purchase(user_id=current_user.id, content_id=cid, points_cost=content.price)
        db.session.add(purchase)

        if content.master_id:
            master = db.session.get(Master, content.master_id)
            if master:
                author_points = int(content.price * 0.7)
                add_points(master.user_id, 'purchased', author_points, f'内容被购买: {content.title}', commit=False)

        db.session.commit()

        return jsonify({
            'ok': True,
            'pointsCost': content.price,
            'disclaimer': DISCLAIMER,
        })

    @app.route('/api/paid-contents', methods=['POST'])
    @login_required
    def api_paid_contents_create():
        """创建付费内容，仅大师身份可用。"""
        master = Master.query.filter_by(user_id=current_user.id).first()
        if not master:
            return jsonify({'error': '仅大师可创建付费内容'}), 403

        data = request.get_json(silent=True) or {}
        title = (data.get('title') or '').strip()
        content_type = data.get('contentType', 'article')
        preview = (data.get('preview') or '').strip()
        full_content = (data.get('fullContent') or '').strip()
        price = data.get('price', 100)
        category = (data.get('category') or '').strip()

        if not title:
            return jsonify({'error': '标题不能为空'}), 400
        if content_type not in ('article', 'report', 'reading'):
            return jsonify({'error': '无效内容类型'}), 400
        if not full_content:
            return jsonify({'error': '完整内容不能为空'}), 400
        if not isinstance(price, int) or price < 1:
            return jsonify({'error': '价格须为正整数'}), 400

        content = PaidContent(
            title=title,
            content_type=content_type,
            preview=preview,
            full_content=full_content,
            price=price,
            master_id=master.id,
            category=category,
        )
        db.session.add(content)
        db.session.commit()

        return jsonify({
            'id': content.id,
            'disclaimer': DISCLAIMER,
        }), 201
