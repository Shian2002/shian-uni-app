"""时安解忧屋 — 数据模型

所有 SQLAlchemy 模型定义集中管理。
依赖：extensions.db
"""
from datetime import datetime
from flask_login import UserMixin
from extensions import db, login_manager


# ═══════ user_loader ═══════
@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


@login_manager.unauthorized_handler
def unauthorized():
    from flask import jsonify
    return jsonify({'error': '请先登录'}), 401


# ═══════════════════════════════════════════════
# 数据模型
# ═══════════════════════════════════════════════

class User(db.Model, UserMixin):
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    has_password  = db.Column(db.Boolean, default=False)
    avatar        = db.Column(db.String(200), default='')
    email         = db.Column(db.String(120), unique=True, nullable=True, index=True)
    phone         = db.Column(db.String(20), unique=True, nullable=True, index=True)
    oauth_qq      = db.Column(db.String(64), unique=True, nullable=True, index=True)
    oauth_wechat  = db.Column(db.String(64), unique=True, nullable=True, index=True)
    oauth_gitee   = db.Column(db.String(64), unique=True, nullable=True, index=True)
    daily_tool_count = db.Column(db.Integer, default=0)
    last_tool_date   = db.Column(db.String(10))
    is_admin         = db.Column(db.Boolean, default=False, index=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

class Record(db.Model):
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    app_type    = db.Column(db.String(20), default='qimen')
    question    = db.Column(db.Text, nullable=False)
    result_html = db.Column(db.Text, nullable=True)
    qimen_json  = db.Column(db.Text, nullable=True)
    run_id      = db.Column(db.Integer, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user = db.relationship('User', backref=db.backref('records', lazy='dynamic'))

class UserProfile(db.Model):
    """用户命盘存档"""
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name        = db.Column(db.String(40), nullable=False)
    gender      = db.Column(db.String(4), default='男')
    cal_type    = db.Column(db.String(10), default='公历')
    birth_time  = db.Column(db.String(20), nullable=False)
    birth_addr  = db.Column(db.String(100), default='')
    is_default  = db.Column(db.Boolean, default=False)
    profile_type = db.Column(db.String(10), default='self')
    last_used_at = db.Column(db.DateTime)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('profiles', lazy='dynamic'))

class FollowUp(db.Model):
    """问事跟进"""
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    record_id   = db.Column(db.Integer, db.ForeignKey('record.id'), nullable=False, index=True)
    note        = db.Column(db.Text, nullable=False)
    feedback    = db.Column(db.String(20), default='')
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('followups', lazy='dynamic'))
    record = db.relationship('Record', backref=db.backref('followups', lazy='dynamic'))

class Collection(db.Model):
    """收藏"""
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    target_type = db.Column(db.String(20), nullable=False)
    target_id   = db.Column(db.Integer, nullable=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('collections', lazy='dynamic'))

class Post(db.Model):
    """社区帖子"""
    __tablename__ = 'post'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(20), default='share')
    tags = db.Column(db.String(200))
    image_url = db.Column(db.String(500))
    likes_count = db.Column(db.Integer, default=0)
    comments_count = db.Column(db.Integer, default=0)
    is_featured = db.Column(db.Boolean, default=False, index=True)
    is_pinned = db.Column(db.Boolean, default=False, index=True)
    is_hidden = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('posts', lazy='dynamic'))

class Comment(db.Model):
    """评论"""
    __tablename__ = 'comment'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)
    content = db.Column(db.Text, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    likes_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('comments', lazy='dynamic'))
    post = db.relationship('Post', backref=db.backref('comments', lazy='dynamic'))
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]), lazy='dynamic')

class Master(db.Model):
    """大师/专家"""
    __tablename__ = 'master'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True, index=True)
    display_name = db.Column(db.String(50), nullable=False)
    avatar = db.Column(db.String(200))
    title = db.Column(db.String(100))
    specialties = db.Column(db.String(200))
    bio = db.Column(db.Text)
    verified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0)
    review_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('master_profile', uselist=False))

class PostLike(db.Model):
    """帖子点赞"""
    __tablename__ = 'post_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'post_id'),)
    user = db.relationship('User', backref=db.backref('post_likes', lazy='dynamic'))

class CommentLike(db.Model):
    """评论点赞"""
    __tablename__ = 'comment_like'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'comment_id'),)
    user = db.relationship('User', backref=db.backref('comment_likes', lazy='dynamic'))

class Notification(db.Model):
    """通知"""
    __tablename__ = 'notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    type = db.Column(db.String(20), nullable=False)
    from_user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'))
    comment_id = db.Column(db.Integer, db.ForeignKey('comment.id'))
    content = db.Column(db.String(200))
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('notifications', lazy='dynamic'))

class Report(db.Model):
    """举报"""
    __tablename__ = 'report'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    target_type = db.Column(db.String(20), nullable=False)
    target_id = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), default='pending', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('reports', lazy='dynamic'))

class Membership(db.Model):
    """会员"""
    __tablename__ = 'membership'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    level = db.Column(db.String(20), default='free')
    points = db.Column(db.Integer, default=0)
    expire_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('membership', uselist=False))

class PointLog(db.Model):
    """积分日志"""
    __tablename__ = 'point_log'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    points = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('point_logs', lazy='dynamic'))

class PaidContent(db.Model):
    """付费内容"""
    __tablename__ = 'paid_content'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content_type = db.Column(db.String(20), default='article')
    preview = db.Column(db.Text)
    full_content = db.Column(db.Text)
    price = db.Column(db.Integer, default=100)
    master_id = db.Column(db.Integer, db.ForeignKey('master.id'))
    category = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    master = db.relationship('Master', backref=db.backref('paid_contents', lazy='dynamic'))

class Purchase(db.Model):
    """购买记录"""
    __tablename__ = 'purchase'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('paid_content.id'), nullable=False)
    points_cost = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('user_id', 'content_id'),)
    user = db.relationship('User', backref=db.backref('purchases', lazy='dynamic'))
    content = db.relationship('PaidContent', backref=db.backref('purchases', lazy='dynamic'))

class RechargeOrder(db.Model):
    """充值订单"""
    __tablename__ = 'recharge_order'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    package_id = db.Column(db.String(50), nullable=False)
    package_name = db.Column(db.String(100))
    points = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    pay_method = db.Column(db.String(50), default='transfer')
    status = db.Column(db.String(20), default='pending')  # pending/paid/cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('recharge_orders', lazy='dynamic'))


class BaziRecord(db.Model):
    """八字排盘/合盘历史记录"""
    __tablename__ = 'bazi_record'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    name        = db.Column(db.String(80), default='')
    gender      = db.Column(db.String(4), default='男')
    birth_time  = db.Column(db.String(20), default='')
    cal_type    = db.Column(db.String(10), default='公历')
    birth_addr  = db.Column(db.String(100), default='')
    pillars     = db.Column(db.String(20), default='')       # 天干地支如: 甲子丙寅庚午壬申
    record_type = db.Column(db.String(10), default='paipan') # paipan / hepan
    starred     = db.Column(db.Boolean, default=False)
    pinned      = db.Column(db.Boolean, default=False)
    category    = db.Column(db.String(10), default='全部')
    params_json = db.Column(db.Text, default='')             # 排盘参数 JSON
    hepan_json  = db.Column(db.Text, default='')             # 合盘数据 JSON
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user = db.relationship('User', backref=db.backref('bazi_records', lazy='dynamic'))

    def to_dict(self):
        """转换为前端使用的字典格式"""
        import json
        d = {
            'id': self.id,
            'name': self.name,
            'gender': self.gender,
            'birth_time': self.birth_time,
            'cal_type': self.cal_type,
            'birth_addr': self.birth_addr,
            'pillars': self.pillars,
            'type': self.record_type,
            'starred': self.starred,
            'pinned': self.pinned,
            'category': self.category,
            'created_at': self.created_at.isoformat() if self.created_at else '',
            'params': json.loads(self.params_json) if self.params_json else {},
        }
        if self.record_type == 'hepan' and self.hepan_json:
            d['hepan_data'] = json.loads(self.hepan_json)
        return d

class TarotConversation(db.Model):
    """塔罗对话历史"""
    __tablename__ = 'tarot_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(100))
    spread_name = db.Column(db.String(40))
    cards_json = db.Column(db.Text)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'spread_name': self.spread_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class LiuyaoConversation(db.Model):
    """六爻对话历史"""
    __tablename__ = 'liuyao_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(100))
    scene_type = db.Column(db.String(40))
    liuyao_data = db.Column(db.Text)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MeihuaConversation(db.Model):
    """梅花易数对话历史"""
    __tablename__ = 'meihua_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(100))
    method = db.Column(db.String(20))
    meihua_data = db.Column(db.Text)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class QimenConversation(db.Model):
    """奇门遁甲对话历史"""
    __tablename__ = 'qimen_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(100))
    pan_data = db.Column(db.Text)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class BaziConversation(db.Model):
    """八字AI对话历史"""
    __tablename__ = 'bazi_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    title = db.Column(db.String(100))
    birth_data = db.Column(db.Text)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ZiweiConversation(db.Model):
    __tablename__ = 'ziwei_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    title = db.Column(db.String(100))
    birth_data = db.Column(db.Text)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class ComprehensiveConversation(db.Model):
    """首页综合 AI 对话历史"""
    __tablename__ = 'comprehensive_conversation'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    title = db.Column(db.String(100))
    profile_data = db.Column(db.Text)
    models_json = db.Column(db.Text)
    paipan_json = db.Column(db.Text)
    model_id = db.Column(db.String(50))
    points_cost = db.Column(db.Integer, default=0)
    messages_json = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
