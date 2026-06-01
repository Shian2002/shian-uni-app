"""八字排盘历史 API。"""

import json
import logging
from datetime import datetime

from flask import jsonify, request, session
from flask_login import current_user, login_required

from extensions import csrf
from models import BaziRecord

logger = logging.getLogger('xuancetai')


def register_bazi_history_routes(app, db):
    """注册 /api/bazi/history* 路由。"""

    def _records_for_current_user():
        return BaziRecord.query.filter_by(user_id=current_user.id)\
            .order_by(BaziRecord.pinned.desc(), BaziRecord.created_at.desc())

    def _record_by_id_or_index(data):
        rec_id = data.get('id')
        if rec_id:
            rec = BaziRecord.query.filter_by(id=rec_id, user_id=current_user.id).first()
            if rec:
                return rec

        idx = data.get('index', -1)
        if idx >= 0:
            records = _records_for_current_user().all()
            if 0 <= idx < len(records):
                return records[idx]
        return None

    def _migrate_session_history():
        """将 session 中的旧 bazi_history 合并迁移到数据库。"""
        old_history = session.get('bazi_history')
        if not old_history:
            return

        existing_keys = set()
        existing_records = BaziRecord.query.filter_by(user_id=current_user.id).all()
        for rec in existing_records:
            existing_keys.add((
                rec.name or '',
                rec.gender or '',
                rec.birth_time or '',
                rec.cal_type or '',
                rec.record_type or '',
                rec.pillars or '',
            ))

        migrated = 0
        for item in old_history:
            if not isinstance(item, dict):
                continue
            record_type = item.get('type') or item.get('record_type') or 'paipan'
            key = (
                item.get('name', ''),
                item.get('gender', '男'),
                item.get('birth_time', ''),
                item.get('cal_type', '公历'),
                record_type,
                item.get('pillars', ''),
            )
            if key in existing_keys:
                continue

            created_at = datetime.utcnow()
            if item.get('created_at'):
                try:
                    created_at = datetime.fromisoformat(str(item.get('created_at')).replace('Z', '+00:00'))
                except Exception:
                    created_at = datetime.utcnow()

            rec = BaziRecord(
                user_id=current_user.id,
                name=item.get('name', ''),
                gender=item.get('gender', '男'),
                birth_time=item.get('birth_time', ''),
                cal_type=item.get('cal_type', '公历'),
                birth_addr=item.get('birth_addr', ''),
                pillars=item.get('pillars', ''),
                record_type=record_type,
                starred=item.get('starred', False),
                pinned=item.get('pinned', False),
                category=item.get('category', '全部'),
                params_json=json.dumps(item.get('params', {}), ensure_ascii=False),
                hepan_json=json.dumps(item.get('hepan_data', {}), ensure_ascii=False) if item.get('hepan_data') else '',
                created_at=created_at,
            )
            db.session.add(rec)
            existing_keys.add(key)
            migrated += 1

        db.session.commit()
        session.pop('bazi_history', None)
        session.modified = True
        if migrated:
            logger.info('已迁移旧版八字排盘历史 %s 条，user_id=%s', migrated, current_user.id)

    @app.route('/api/bazi/history')
    @login_required
    def api_bazi_history():
        """获取排盘历史（基于数据库，需登录）。"""
        _migrate_session_history()
        records = _records_for_current_user().limit(50).all()
        return jsonify({'success': True, 'history': [r.to_dict() for r in records], 'total': len(records)})

    @app.route('/api/bazi/history/<int:rec_id>')
    @login_required
    def api_bazi_history_get(rec_id):
        rec = BaziRecord.query.filter_by(id=rec_id, user_id=current_user.id).first()
        if not rec:
            return jsonify({'success': False, 'error': '记录不存在'})
        return jsonify({'success': True, 'record': rec.to_dict()})

    @app.route('/api/bazi/history/clear', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bazi_history_clear():
        """清空排盘历史。"""
        BaziRecord.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        return jsonify({'success': True})

    @app.route('/api/bazi/history/delete', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bazi_history_delete():
        """删除单条排盘记录。"""
        rec = _record_by_id_or_index(request.get_json(silent=True) or {})
        if rec:
            db.session.delete(rec)
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '记录不存在'})

    @app.route('/api/bazi/history/star', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bazi_history_star():
        """切换排盘记录星标状态。"""
        rec = _record_by_id_or_index(request.get_json(silent=True) or {})
        if rec:
            rec.starred = not rec.starred
            db.session.commit()
            return jsonify({'success': True, 'starred': rec.starred})
        return jsonify({'success': False, 'error': '记录不存在'})

    @app.route('/api/bazi/history/pin', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bazi_history_pin():
        """切换排盘记录置顶状态。"""
        rec = _record_by_id_or_index(request.get_json(silent=True) or {})
        if rec:
            rec.pinned = not rec.pinned
            db.session.commit()
            return jsonify({'success': True, 'pinned': rec.pinned})
        return jsonify({'success': False, 'error': '记录不存在'})

    @app.route('/api/bazi/history/category', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bazi_history_category():
        """更新排盘记录分类。"""
        data = request.get_json(silent=True) or {}
        category = data.get('category', '全部')
        ids = data.get('ids', [])
        if ids and isinstance(ids, list):
            recs = BaziRecord.query.filter(BaziRecord.id.in_(ids), BaziRecord.user_id == current_user.id).all()
            for rec in recs:
                rec.category = category
            db.session.commit()
            return jsonify({'success': True})

        rec = _record_by_id_or_index(data)
        if rec:
            rec.category = category
            db.session.commit()
            return jsonify({'success': True})
        return jsonify({'success': False, 'error': '记录不存在'})

    @app.route('/api/bazi/history/batch-delete', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bazi_history_batch_delete():
        """批量删除排盘记录。"""
        data = request.get_json(silent=True) or {}
        ids = data.get('ids', [])
        indices = data.get('indices', [])

        if ids:
            BaziRecord.query.filter(BaziRecord.id.in_(ids), BaziRecord.user_id == current_user.id).delete(synchronize_session='fetch')
            db.session.commit()
            return jsonify({'success': True})

        if indices:
            records = _records_for_current_user().all()
            for idx in sorted(indices, reverse=True):
                if 0 <= idx < len(records):
                    db.session.delete(records[idx])
            db.session.commit()
            return jsonify({'success': True})

        return jsonify({'success': False, 'error': '无有效参数'})

    @app.route('/api/bazi/history/rename', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_bazi_history_rename():
        data = request.get_json(silent=True) or {}
        rec_id = data.get('id')
        new_name = (data.get('name') or '').strip()[:80]
        if not rec_id or not new_name:
            return jsonify({'success': False, 'error': '参数缺失'})
        rec = BaziRecord.query.filter_by(id=rec_id, user_id=current_user.id).first()
        if not rec:
            return jsonify({'success': False, 'error': '记录不存在'})
        rec.name = new_name
        db.session.commit()
        return jsonify({'success': True})
