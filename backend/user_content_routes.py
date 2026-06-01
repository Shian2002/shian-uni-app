import json

from flask import jsonify, request
from flask_login import current_user, login_required

from models import Collection, FollowUp, Record


def register_user_content_routes(app, db):
    @app.route('/api/records')
    @login_required
    def api_records():
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        app_type = request.args.get('app_type', '')

        query = Record.query.filter_by(user_id=current_user.id)
        if app_type:
            query = query.filter_by(app_type=app_type)

        pagination = query.order_by(Record.created_at.desc()) \
            .paginate(page=page, per_page=per_page, error_out=False)

        records = [{
            'id': r.id,
            'app_type': r.app_type or 'qimen',
            'question': r.question,
            'created_at': r.created_at.isoformat() if r.created_at else None,
            'has_result': bool(r.result_html),
        } for r in pagination.items]

        return jsonify({
            'records': records,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'has_next': pagination.has_next,
        })

    @app.route('/api/records/<int:rid>')
    @login_required
    def api_record_detail(rid):
        rec = db.session.get(Record, rid)
        if not rec:
            return jsonify({'error': '记录不存在'}), 404
        if rec.user_id != current_user.id:
            return jsonify({'error': '无权访问'}), 403

        qimen = None
        if rec.qimen_json:
            try:
                qimen = json.loads(rec.qimen_json)
            except (json.JSONDecodeError, TypeError):
                qimen = None

        return jsonify({
            'id': rec.id,
            'app_type': rec.app_type or 'qimen',
            'question': rec.question,
            'result_html': rec.result_html or '',
            'qimen': qimen,
            'created_at': rec.created_at.isoformat() if rec.created_at else None,
        })

    @app.route('/api/records/<int:rid>', methods=['DELETE'])
    @login_required
    def api_record_delete(rid):
        rec = db.session.get(Record, rid)
        if not rec:
            return jsonify({'error': '记录不存在'}), 404
        if rec.user_id != current_user.id:
            return jsonify({'error': '无权操作'}), 403

        db.session.delete(rec)
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/records/clear', methods=['POST'])
    @login_required
    def api_records_clear():
        count = Record.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'ok': True, 'deleted': count})

    @app.route('/api/followups', methods=['GET'])
    @login_required
    def api_followups_list():
        record_id = request.args.get('record_id', type=int)
        query = FollowUp.query.filter_by(user_id=current_user.id)
        if record_id:
            query = query.filter_by(record_id=record_id)
        items = query.order_by(FollowUp.created_at.desc()).limit(50).all()
        return jsonify({'followups': [{
            'id': f.id,
            'recordId': f.record_id,
            'note': f.note,
            'feedback': f.feedback,
            'createdAt': f.created_at.isoformat() if f.created_at else None,
        } for f in items]})

    @app.route('/api/followups', methods=['POST'])
    @login_required
    def api_followups_create():
        data = request.get_json(silent=True) or {}
        record_id = data.get('recordId')
        note = (data.get('note') or '').strip()
        if not record_id or not note:
            return jsonify({'error': '缺少参数'}), 400

        rec = db.session.get(Record, record_id)
        if not rec or rec.user_id != current_user.id:
            return jsonify({'error': '无权操作'}), 403

        followup = FollowUp(
            user_id=current_user.id,
            record_id=record_id,
            note=note,
            feedback=data.get('feedback', '待验证'),
        )
        db.session.add(followup)
        db.session.commit()
        return jsonify({'id': followup.id}), 201

    @app.route('/api/followups/<int:fid>', methods=['PUT'])
    @login_required
    def api_followups_update(fid):
        followup = db.session.get(FollowUp, fid)
        if not followup or followup.user_id != current_user.id:
            return jsonify({'error': '无权操作'}), 403
        data = request.get_json(silent=True) or {}
        if 'note' in data:
            followup.note = data['note']
        if 'feedback' in data:
            followup.feedback = data['feedback']
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/followups/<int:fid>', methods=['DELETE'])
    @login_required
    def api_followups_delete(fid):
        followup = db.session.get(FollowUp, fid)
        if not followup or followup.user_id != current_user.id:
            return jsonify({'error': '无权操作'}), 403
        db.session.delete(followup)
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/collections', methods=['GET'])
    @login_required
    def api_collections_list():
        target_type = request.args.get('type', '')
        query = Collection.query.filter_by(user_id=current_user.id)
        if target_type:
            query = query.filter_by(target_type=target_type)
        items = query.order_by(Collection.created_at.desc()).limit(50).all()
        return jsonify({'collections': [{
            'id': c.id,
            'targetType': c.target_type,
            'targetId': c.target_id,
            'createdAt': c.created_at.isoformat() if c.created_at else None,
        } for c in items]})

    @app.route('/api/collections', methods=['POST'])
    @login_required
    def api_collections_create():
        data = request.get_json(silent=True) or {}
        target_type = data.get('targetType', '')
        target_id = data.get('targetId')
        if not target_type or not target_id:
            return jsonify({'error': '缺少参数'}), 400

        exists = Collection.query.filter_by(
            user_id=current_user.id,
            target_type=target_type,
            target_id=target_id,
        ).first()
        if exists:
            return jsonify({'error': '已收藏'}), 409

        collection = Collection(
            user_id=current_user.id,
            target_type=target_type,
            target_id=target_id,
        )
        db.session.add(collection)
        db.session.commit()
        return jsonify({'id': collection.id}), 201

    @app.route('/api/collections/<int:cid>', methods=['DELETE'])
    @login_required
    def api_collections_delete(cid):
        collection = db.session.get(Collection, cid)
        if not collection or collection.user_id != current_user.id:
            return jsonify({'error': '无权操作'}), 403
        db.session.delete(collection)
        db.session.commit()
        return jsonify({'ok': True})
