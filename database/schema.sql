-- ==========================================
-- 时安解忧屋 — 数据库 Schema
-- 数据库类型: SQLite
-- 从 backend/models.py 自动生成
-- ==========================================

-- 用户表
CREATE TABLE IF NOT EXISTS user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(80) NOT NULL UNIQUE,
    password_hash VARCHAR(256) NOT NULL,
    has_password BOOLEAN DEFAULT 0,
    avatar VARCHAR(200) DEFAULT '',
    email VARCHAR(120) UNIQUE,
    phone VARCHAR(20) UNIQUE,
    oauth_qq VARCHAR(64) UNIQUE,
    oauth_wechat VARCHAR(64) UNIQUE,
    oauth_gitee VARCHAR(64) UNIQUE,
    daily_tool_count INTEGER DEFAULT 0,
    last_tool_date VARCHAR(10),
    is_admin BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_user_username ON user(username);
CREATE INDEX IF NOT EXISTS ix_user_email ON user(email);
CREATE INDEX IF NOT EXISTS ix_user_phone ON user(phone);
CREATE INDEX IF NOT EXISTS ix_user_is_admin ON user(is_admin);

-- 通用记录表
CREATE TABLE IF NOT EXISTS record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    app_type VARCHAR(20) DEFAULT 'qimen',
    question TEXT NOT NULL,
    result_html TEXT,
    qimen_json TEXT,
    run_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_record_user_id ON record(user_id);
CREATE INDEX IF NOT EXISTS ix_record_created_at ON record(created_at);

-- 用户命盘存档
CREATE TABLE IF NOT EXISTS user_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    name VARCHAR(40) NOT NULL,
    gender VARCHAR(4) DEFAULT '男',
    cal_type VARCHAR(10) DEFAULT '公历',
    birth_time VARCHAR(20) NOT NULL,
    birth_addr VARCHAR(100) DEFAULT '',
    is_default BOOLEAN DEFAULT 0,
    profile_type VARCHAR(10) DEFAULT 'self',
    last_used_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_user_profile_user_id ON user_profile(user_id);

-- 问事跟进
CREATE TABLE IF NOT EXISTS follow_up (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    record_id INTEGER NOT NULL REFERENCES record(id),
    note TEXT NOT NULL,
    feedback VARCHAR(20) DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_follow_up_user_id ON follow_up(user_id);
CREATE INDEX IF NOT EXISTS ix_follow_up_record_id ON follow_up(record_id);

-- 收藏表
CREATE TABLE IF NOT EXISTS collection (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    target_type VARCHAR(20) NOT NULL,
    target_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_collection_user_id ON collection(user_id);

-- 社区帖子
CREATE TABLE IF NOT EXISTS post (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(20) DEFAULT 'share',
    tags VARCHAR(200),
    image_url VARCHAR(500),
    likes_count INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT 0,
    is_pinned BOOLEAN DEFAULT 0,
    is_hidden BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_post_user_id ON post(user_id);
CREATE INDEX IF NOT EXISTS ix_post_is_featured ON post(is_featured);
CREATE INDEX IF NOT EXISTS ix_post_is_pinned ON post(is_pinned);
CREATE INDEX IF NOT EXISTS ix_post_is_hidden ON post(is_hidden);

-- 评论表
CREATE TABLE IF NOT EXISTS comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    post_id INTEGER NOT NULL REFERENCES post(id),
    content TEXT NOT NULL,
    parent_id INTEGER REFERENCES comment(id),
    likes_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_comment_user_id ON comment(user_id);
CREATE INDEX IF NOT EXISTS ix_comment_post_id ON comment(post_id);

-- 大师/专家表
CREATE TABLE IF NOT EXISTS master (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES user(id),
    display_name VARCHAR(50) NOT NULL,
    avatar VARCHAR(200),
    title VARCHAR(100),
    specialties VARCHAR(200),
    bio TEXT,
    verified BOOLEAN DEFAULT 0,
    rating FLOAT DEFAULT 0,
    review_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_master_user_id ON master(user_id);

-- 帖子点赞表
CREATE TABLE IF NOT EXISTS post_like (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    post_id INTEGER NOT NULL REFERENCES post(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, post_id)
);
CREATE INDEX IF NOT EXISTS ix_post_like_post_id ON post_like(post_id);

-- 评论点赞表
CREATE TABLE IF NOT EXISTS comment_like (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    comment_id INTEGER NOT NULL REFERENCES comment(id),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, comment_id)
);
CREATE INDEX IF NOT EXISTS ix_comment_like_comment_id ON comment_like(comment_id);

-- 通知表
CREATE TABLE IF NOT EXISTS notification (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    type VARCHAR(20) NOT NULL,
    from_user_id INTEGER REFERENCES user(id),
    post_id INTEGER REFERENCES post(id),
    comment_id INTEGER REFERENCES comment(id),
    content VARCHAR(200),
    is_read BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_notification_user_id ON notification(user_id);
CREATE INDEX IF NOT EXISTS ix_notification_is_read ON notification(is_read);

-- 举报表
CREATE TABLE IF NOT EXISTS report (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    target_type VARCHAR(20) NOT NULL,
    target_id INTEGER NOT NULL,
    reason VARCHAR(200) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_report_user_id ON report(user_id);
CREATE INDEX IF NOT EXISTS ix_report_status ON report(status);

-- 会员表
CREATE TABLE IF NOT EXISTS membership (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL UNIQUE REFERENCES user(id),
    level VARCHAR(20) DEFAULT 'free',
    points INTEGER DEFAULT 0,
    expire_at DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 积分日志
CREATE TABLE IF NOT EXISTS point_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    action VARCHAR(50) NOT NULL,
    points INTEGER NOT NULL,
    description VARCHAR(200),
    dedupe_key VARCHAR(160) UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_point_log_dedupe_key ON point_log(dedupe_key);

-- 付费内容
CREATE TABLE IF NOT EXISTS paid_content (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title VARCHAR(200) NOT NULL,
    content_type VARCHAR(20) DEFAULT 'article',
    preview TEXT,
    full_content TEXT,
    price INTEGER DEFAULT 100,
    master_id INTEGER REFERENCES master(id),
    category VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 购买记录
CREATE TABLE IF NOT EXISTS purchase (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    content_id INTEGER NOT NULL REFERENCES paid_content(id),
    points_cost INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, content_id)
);

-- 充值订单
CREATE TABLE IF NOT EXISTS recharge_order (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    package_id VARCHAR(50) NOT NULL,
    package_name VARCHAR(100),
    points INTEGER NOT NULL,
    amount FLOAT NOT NULL,
    pay_method VARCHAR(50) DEFAULT 'transfer',
    status VARCHAR(20) DEFAULT 'pending',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 八字排盘/合盘历史记录
CREATE TABLE IF NOT EXISTS bazi_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    name VARCHAR(80) DEFAULT '',
    gender VARCHAR(4) DEFAULT '男',
    birth_time VARCHAR(20) DEFAULT '',
    cal_type VARCHAR(10) DEFAULT '公历',
    birth_addr VARCHAR(100) DEFAULT '',
    pillars VARCHAR(20) DEFAULT '',
    record_type VARCHAR(10) DEFAULT 'paipan',
    starred BOOLEAN DEFAULT 0,
    category VARCHAR(10) DEFAULT '全部',
    params_json TEXT DEFAULT '',
    hepan_json TEXT DEFAULT '',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_bazi_record_user_id ON bazi_record(user_id);
CREATE INDEX IF NOT EXISTS ix_bazi_record_created_at ON bazi_record(created_at);

-- 塔罗对话历史
CREATE TABLE IF NOT EXISTS tarot_conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    title VARCHAR(100),
    spread_name VARCHAR(40),
    cards_json TEXT,
    messages_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_tarot_conversation_user_id ON tarot_conversation(user_id);

-- 六爻对话历史
CREATE TABLE IF NOT EXISTS liuyao_conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    title VARCHAR(100),
    scene_type VARCHAR(40),
    liuyao_data TEXT,
    messages_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_liuyao_conversation_user_id ON liuyao_conversation(user_id);

-- 梅花易数对话历史
CREATE TABLE IF NOT EXISTS meihua_conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    title VARCHAR(100),
    method VARCHAR(20),
    meihua_data TEXT,
    messages_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_meihua_conversation_user_id ON meihua_conversation(user_id);

-- 奇门遁甲对话历史
CREATE TABLE IF NOT EXISTS qimen_conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    title VARCHAR(100),
    pan_data TEXT,
    messages_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_qimen_conversation_user_id ON qimen_conversation(user_id);

-- 八字AI对话历史
CREATE TABLE IF NOT EXISTS bazi_conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    title VARCHAR(100),
    birth_data TEXT,
    messages_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_bazi_conversation_user_id ON bazi_conversation(user_id);

CREATE TABLE IF NOT EXISTS ziwei_conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER REFERENCES user(id),
    title VARCHAR(100),
    birth_data TEXT,
    messages_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_ziwei_conversation_user_id ON ziwei_conversation(user_id);

-- 首页综合 AI 对话历史
CREATE TABLE IF NOT EXISTS comprehensive_conversation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES user(id),
    title VARCHAR(100),
    profile_data TEXT,
    models_json TEXT,
    paipan_json TEXT,
    model_id VARCHAR(50),
    points_cost INTEGER DEFAULT 0,
    messages_json TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_comprehensive_conversation_user_id ON comprehensive_conversation(user_id);
