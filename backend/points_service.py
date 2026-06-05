"""积分、会员额度与 AI 消耗的统一服务。"""

from datetime import datetime

from sqlalchemy import case, update
from sqlalchemy.exc import IntegrityError

from models import Membership, PointLog


POINT_RULES = {
    'sign_in': 10,
    'tool_use': -5,
    'post': 5,
    'comment': 2,
    'liked': 1,
    'purchased': 0,
}

MEMBER_TOOL_LIMIT = {
    'free': 3,
    'basic': -1,
    'premium': -1,
    'vip': -1,
}

_db = None


def init_points_service(db):
    global _db
    _db = db


def _require_db():
    if _db is None:
        raise RuntimeError('积分服务尚未初始化')
    return _db


def get_or_create_membership(user_id, commit=True):
    """获取或创建会员记录。"""
    db = _require_db()
    membership = Membership.query.filter_by(user_id=user_id).first()
    if not membership:
        membership = Membership(user_id=user_id, level='free', points=0)
        db.session.add(membership)
        try:
            if commit:
                db.session.commit()
            else:
                db.session.flush()
        except IntegrityError:
            if not commit:
                raise
            db.session.rollback()
            membership = Membership.query.filter_by(user_id=user_id).first()
            if not membership:
                raise
    return membership


def add_points(user_id, action, points, description='', dedupe_key=None, commit=True):
    """添加积分日志并更新会员积分。"""
    db = _require_db()
    try:
        log = PointLog(
            user_id=user_id,
            action=action,
            points=points,
            description=description,
            dedupe_key=dedupe_key,
        )
        db.session.add(log)
        get_or_create_membership(user_id, commit=False)
        db.session.flush()
        db.session.execute(
            update(Membership)
            .where(Membership.user_id == user_id)
            .values(
                points=case(
                    (Membership.points + points < 0, 0),
                    else_=Membership.points + points,
                ),
                updated_at=datetime.utcnow(),
            )
        )
        db.session.flush()
        new_points = Membership.query.filter_by(user_id=user_id).with_entities(Membership.points).scalar()
        if commit:
            db.session.commit()
        return new_points
    except IntegrityError:
        db.session.rollback()
        raise


def create_daily_sign_in_once(user_id):
    """每日签到幂等写入，同一用户同一天只加一次积分。"""
    today = datetime.utcnow().strftime('%Y-%m-%d')
    dedupe_key = f'sign_in:{user_id}:{today}'
    try:
        new_points = add_points(
            user_id,
            'sign_in',
            POINT_RULES['sign_in'],
            '每日签到',
            dedupe_key=dedupe_key,
        )
        return {'ok': True, 'points': new_points, 'added': POINT_RULES['sign_in']}
    except IntegrityError:
        return {'ok': False, 'error': '今天已签到'}


def use_points(user_id, action, points, description='', commit=True):
    """原子扣减积分，余额不足时不写日志。"""
    db = _require_db()
    if points <= 0:
        return {'ok': False, 'error': 'points 须为正整数'}
    get_or_create_membership(user_id, commit=False)
    changed = Membership.query.filter(
        Membership.user_id == user_id,
        Membership.points >= points,
    ).update(
        {'points': Membership.points - points, 'updated_at': datetime.utcnow()},
        synchronize_session=False,
    )
    if changed != 1:
        db.session.rollback()
        membership = get_or_create_membership(user_id)
        return {'ok': False, 'error': '积分不足', 'current': membership.points, 'required': points}
    log = PointLog(user_id=user_id, action=action, points=-points, description=description)
    db.session.add(log)
    db.session.flush()
    new_points = Membership.query.filter_by(user_id=user_id).with_entities(Membership.points).scalar()
    if commit:
        db.session.commit()
    return {'ok': True, 'points': new_points, 'used': points}


def spend_ai_quota_once(user_id, tool_models, cost, is_followup=False):
    """按免费轻量额度、套餐次数、积分的顺序扣减综合 AI 消耗。"""
    db = _require_db()
    membership = get_or_create_membership(user_id)
    today = datetime.utcnow().strftime('%Y-%m-%d')
    tool_count = len(tool_models or [])
    if not is_followup and cost <= 2 and membership.daily_ai_light_used_at != today:
        membership.daily_ai_light_used_at = today
        db.session.add(PointLog(
            user_id=user_id,
            action='daily_ai_light',
            points=0,
            description='每日轻量 AI 体验额度',
            dedupe_key=f'daily_ai_light:{user_id}:{today}',
        ))
        db.session.commit()
        return {'ok': True, 'points': membership.points, 'used_credit': 'daily_light', 'used': 0}
    if not is_followup and tool_count > 1 and int(membership.ai_combo_credits or 0) > 0:
        membership.ai_combo_credits = int(membership.ai_combo_credits or 0) - 1
        db.session.add(PointLog(user_id=user_id, action='ai_combo_credit_use', points=0, description='首页多术数合参次数 -1'))
        db.session.commit()
        return {'ok': True, 'points': membership.points, 'used_credit': 'ai_combo_credits', 'used': 1}
    if not is_followup and tool_count == 1 and int(membership.ai_single_credits or 0) > 0:
        membership.ai_single_credits = int(membership.ai_single_credits or 0) - 1
        db.session.add(PointLog(user_id=user_id, action='ai_single_credit_use', points=0, description='首页单术数 AI 次数 -1'))
        db.session.commit()
        return {'ok': True, 'points': membership.points, 'used_credit': 'ai_single_credits', 'used': 1}
    spend = use_points(user_id, 'comprehensive_ai', cost, '综合 AI ' + ('追问' if is_followup else '解读'))
    spend['used_credit'] = 'points' if spend.get('ok') else ''
    return spend
