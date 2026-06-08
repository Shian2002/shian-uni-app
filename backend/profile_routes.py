"""命盘档案 API 与八字记录同步逻辑。"""

import json
import logging
from datetime import datetime

from flask import jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import OperationalError

from models import BaziRecord, UserProfile

logger = logging.getLogger('xuancetai')

PROFILE_TYPES = ('self', 'family', 'friend', 'partner', 'customer', 'celebrity', 'collect', 'other')
PROFILE_SOURCES = ('manual', 'bazi_record', 'ziwei_pan')


def _json_loads_safe(text, default):
    try:
        if not text:
            return default
        return json.loads(text)
    except Exception:
        return default


def serialize_user_profile(p):
    meta = _json_loads_safe(getattr(p, 'meta_json', ''), {})
    return {
        'id': p.id, 'name': p.name, 'gender': p.gender,
        'calType': p.cal_type, 'birthTime': p.birth_time,
        'birthAddr': p.birth_addr, 'isDefault': p.is_default,
        'profileType': p.profile_type or 'self',
        'source': getattr(p, 'source', '') or meta.get('source') or 'manual',
        'sourceRecordId': getattr(p, 'source_record_id', None),
        'meta': meta,
        'lastUsedAt': p.last_used_at.isoformat() if p.last_used_at else None,
        'createdAt': p.created_at.isoformat() if p.created_at else None,
    }


def _profile_type_from_payload(data):
    profile_type = data.get('profileType', 'self')
    return profile_type if profile_type in PROFILE_TYPES else 'self'


def _source_from_payload(data, current_source='manual'):
    source = data.get('source') or current_source or 'manual'
    return source if source in PROFILE_SOURCES else 'manual'


def _apply_profile_payload(profile, data):
    name = (data.get('name') or '').strip()
    if not name:
        return '缺少姓名'
    birth_time = (data.get('birthTime') or '').strip()
    if not birth_time or len(birth_time) < 8:
        return '缺少出生时间'

    profile.name = name
    profile.gender = data.get('gender', '男')
    profile.cal_type = data.get('calType', '公历')
    profile.birth_time = birth_time
    profile.birth_addr = (data.get('birthAddr') or '').strip()
    profile.is_default = bool(data.get('isDefault', False))
    profile.profile_type = _profile_type_from_payload(data)
    profile.source = _source_from_payload(data, getattr(profile, 'source', 'manual'))
    meta = data.get('meta') or {}
    if isinstance(meta, dict):
        meta = dict(meta)
        meta['gender'] = profile.gender
    profile.meta_json = json.dumps(meta, ensure_ascii=False)
    profile.last_used_at = datetime.utcnow()
    return ''


def sync_bazi_record_to_profile(db, user_id, record, params_data, paipan_result=None):
    """八字排盘记录同步为通用命盘档案，供首页和其他术数共用。"""
    if not user_id or not record:
        return None
    meta = dict(params_data or {})
    meta.update({
        'source': 'bazi_record',
        'record_id': record.id,
        'gender': record.gender or meta.get('gender') or '男',
        'pillars': record.pillars,
        'four_pillars': (paipan_result or {}).get('four_pillars') or {},
        'birth_solar': (paipan_result or {}).get('birth_solar') or '',
        'birth_lunar': (paipan_result or {}).get('birth_lunar') or '',
        'pillar_source': (paipan_result or {}).get('pillar_source') or '',
    })
    profile = UserProfile.query.filter_by(
        user_id=user_id,
        source='bazi_record',
        source_record_id=record.id,
    ).first()
    if not profile:
        profile = UserProfile(
            user_id=user_id,
            source='bazi_record',
            source_record_id=record.id,
            profile_type='self',
            created_at=datetime.utcnow(),
        )
        db.session.add(profile)
    profile.name = record.name or '未命名'
    profile.gender = record.gender or '男'
    profile.cal_type = record.cal_type or '公历'
    profile.birth_time = record.birth_time or ''
    profile.birth_addr = record.birth_addr or ''
    profile.meta_json = json.dumps(meta, ensure_ascii=False)
    profile.last_used_at = datetime.utcnow()
    return profile


def ensure_bazi_records_synced_to_profiles(db, user_id, limit=80):
    """补同步旧八字排盘记录，避免首页只显示新建后的命盘档案。"""
    if not user_id:
        return 0
    existing_ids = {
        row[0] for row in db.session.query(UserProfile.source_record_id)
        .filter(
            UserProfile.user_id == user_id,
            UserProfile.source == 'bazi_record',
            UserProfile.source_record_id.isnot(None),
        )
        .all()
    }
    query = BaziRecord.query.filter(
        BaziRecord.user_id == user_id,
        BaziRecord.record_type == 'paipan',
        BaziRecord.birth_time != '',
    )
    if existing_ids:
        query = query.filter(~BaziRecord.id.in_(existing_ids))
    records = query.order_by(BaziRecord.created_at.desc()).limit(limit).all()
    if not records:
        return 0
    count = 0
    for record in records:
        params_data = _json_loads_safe(record.params_json, {})
        sync_bazi_record_to_profile(db, user_id, record, params_data, None)
        count += 1
    db.session.commit()
    return count


def register_profile_routes(app, db):
    """注册 /api/profiles* 路由。"""

    @app.route('/api/profiles', methods=['GET'])
    @login_required
    def api_profiles_list():
        """获取当前用户所有命盘存档，支持按类型/姓名搜索，按最近使用排序。"""
        profile_type = request.args.get('type', '')
        search = (request.args.get('search') or '').strip()
        sort = request.args.get('sort', 'last_used')

        try:
            ensure_bazi_records_synced_to_profiles(db, current_user.id)
            query = UserProfile.query.filter_by(user_id=current_user.id)
            if profile_type:
                query = query.filter_by(profile_type=profile_type)
            if search:
                query = query.filter(UserProfile.name.contains(search))

            if sort == 'last_used':
                query = query.order_by(
                    UserProfile.last_used_at.is_(None),
                    UserProfile.last_used_at.desc(),
                    UserProfile.created_at.desc()
                )
            else:
                query = query.order_by(UserProfile.is_default.desc(), UserProfile.created_at.desc())

            profiles = query.all()
        except OperationalError as exc:
            logger.warning(f"查询命盘列表失败（DB schema）: {exc}")
            profiles = []

        return jsonify({'profiles': [serialize_user_profile(p) for p in profiles]})

    @app.route('/api/profiles', methods=['POST'])
    @login_required
    def api_profiles_create():
        """创建命盘存档。"""
        data = request.get_json(silent=True) or {}
        source = _source_from_payload(data)
        p = None
        if source == 'ziwei_pan':
            p = UserProfile.query.filter_by(
                user_id=current_user.id,
                source='ziwei_pan',
                name=(data.get('name') or '').strip(),
                birth_time=(data.get('birthTime') or '').strip(),
                cal_type=data.get('calType', '公历'),
            ).first()
        created = p is None
        if not p:
            p = UserProfile(user_id=current_user.id, created_at=datetime.utcnow())
            db.session.add(p)

        error = _apply_profile_payload(p, data)
        if error:
            if created:
                db.session.rollback()
            return jsonify({'error': error}), 400
        if p.is_default:
            UserProfile.query.filter_by(user_id=current_user.id, is_default=True)\
                .update({'is_default': False})
        db.session.commit()
        status = 201 if created else 200
        return jsonify(serialize_user_profile(p)), status

    @app.route('/api/profiles/<int:pid>', methods=['PUT'])
    @login_required
    def api_profiles_update(pid):
        """编辑命盘存档。"""
        p = db.session.get(UserProfile, pid)
        if not p or p.user_id != current_user.id:
            return jsonify({'error': '无权操作'}), 403
        data = request.get_json(silent=True) or {}
        error = _apply_profile_payload(p, data)
        if error:
            return jsonify({'error': error}), 400
        if p.is_default:
            UserProfile.query.filter(
                UserProfile.user_id == current_user.id,
                UserProfile.id != p.id,
                UserProfile.is_default == True,  # noqa: E712
            ).update({'is_default': False})
        db.session.commit()
        return jsonify(serialize_user_profile(p))

    @app.route('/api/profiles/<int:pid>', methods=['DELETE'])
    @login_required
    def api_profiles_delete(pid):
        p = db.session.get(UserProfile, pid)
        if not p or p.user_id != current_user.id:
            return jsonify({'error': '无权操作'}), 403
        deleted_source_record = False
        if p.source == 'bazi_record' and p.source_record_id:
            record = db.session.get(BaziRecord, p.source_record_id)
            if record and record.user_id == current_user.id:
                db.session.delete(record)
                deleted_source_record = True
        db.session.delete(p)
        db.session.commit()
        return jsonify({'ok': True, 'deletedSourceRecord': deleted_source_record})

    @app.route('/api/profiles/<int:pid>/touch', methods=['POST'])
    @login_required
    def api_profiles_touch(pid):
        """更新命盘最近使用时间。"""
        p = db.session.get(UserProfile, pid)
        if not p or p.user_id != current_user.id:
            return jsonify({'error': '无权操作'}), 403
        p.last_used_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'ok': True})

    @app.route('/api/profiles/customer', methods=['GET'])
    @login_required
    def api_profiles_customer():
        """获取客户命盘列表，支持搜索/排序。"""
        return _profiles_by_type('customer')

    @app.route('/api/profiles/collect', methods=['GET'])
    @login_required
    def api_profiles_collect():
        """获取收藏命盘列表，支持搜索/排序。"""
        return _profiles_by_type('collect')

    @app.route('/api/profiles/export', methods=['GET'])
    @login_required
    def api_profiles_export():
        """导出命盘数据为 JSON。"""
        profile_type = request.args.get('type', '')
        query = UserProfile.query.filter_by(user_id=current_user.id)
        if profile_type:
            query = query.filter_by(profile_type=profile_type)
        profiles = query.order_by(UserProfile.created_at.desc()).all()
        export_data = [{
            'name': p.name, 'gender': p.gender,
            'calType': p.cal_type, 'birthTime': p.birth_time,
            'birthAddr': p.birth_addr, 'profileType': p.profile_type,
        } for p in profiles]
        return jsonify({'count': len(export_data), 'profiles': export_data})

    def _profiles_by_type(profile_type):
        search = (request.args.get('search') or '').strip()
        sort = request.args.get('sort', 'last_used')
        query = UserProfile.query.filter_by(user_id=current_user.id, profile_type=profile_type)
        if search:
            query = query.filter(UserProfile.name.contains(search))
        if sort == 'last_used':
            query = query.order_by(UserProfile.last_used_at.is_(None), UserProfile.last_used_at.desc(), UserProfile.created_at.desc())
        else:
            query = query.order_by(UserProfile.created_at.desc())
        profiles = query.all()
        return jsonify({'profiles': [{
            'id': p.id, 'name': p.name, 'gender': p.gender,
            'calType': p.cal_type, 'birthTime': p.birth_time,
            'birthAddr': p.birth_addr, 'isDefault': p.is_default,
            'profileType': p.profile_type,
            'lastUsedAt': p.last_used_at.isoformat() if p.last_used_at else None,
            'createdAt': p.created_at.isoformat() if p.created_at else None,
        } for p in profiles]})
