#!/usr/bin/env python3
"""时安解忧屋 - 八字排盘 + 天机问策 融合门户 (v6.3)

Copyright (c) 2026 JunJunXu. All rights reserved.
原始发起与核心开发：JunJunXu <904752171@qq.com>

v6.3: 模块化重构 — models/engines 独立模块，CSRF安全加固
"""
try:
    import pymysql
    pymysql.install_as_MySQLdb()
except ImportError:
    pass  # SQLite 模式下不需要 pymysql

import os, json, threading, subprocess, time, secrets, shutil, hashlib, logging, re, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, make_response, Response, stream_with_context
from flask_login import login_required, current_user
from sqlalchemy import event, or_
from sqlalchemy.engine import Engine
from sqlalchemy.exc import OperationalError
from deepseek_service import get_chat_completion, get_tarot_reading_stream, get_tarot_followup_stream, get_reading_stream, is_available as deepseek_available
import urllib.parse

# 结构化日志配置
logger = logging.getLogger('xuancetai')
if not logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s', datefmt='%H:%M:%S'))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# 加载 .env 环境变量（开发环境友好，生产环境可不用）
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv 未安装时降级，直接使用系统环境变量

# ═══════ 豆包 API 配置 ═══════
DOUBAO_API_KEY = os.environ.get('DOUBAO_API_KEY', '')
DOUBAO_API_URL = os.environ.get('DOUBAO_API_URL', 'https://ark.cn-beijing.volces.com/api/v3/chat/completions')
DOUBAO_MODEL = os.environ.get('DOUBAO_MODEL', 'doubao-pro-32k')

try:
    from lunarcalendar import Lunar, Converter
    HAS_LUNAR = True
except ImportError:
    HAS_LUNAR = False

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PARENT_DIR = os.path.dirname(BASE_DIR)
_ACTUAL_PARENT = BASE_DIR if PARENT_DIR == "/" else PARENT_DIR

app = Flask(__name__, static_folder=None)

PAIPAN_DIR = os.path.expanduser('~/WorkBuddy/Claw')
PAIPAN_SH = os.path.join(PAIPAN_DIR, 'paipan_auto.sh')

_db_url = os.environ.get('DATABASE_URL',
    'sqlite:///' + os.path.join(BASE_DIR, 'tianji.db'))
if _db_url.startswith('mysql'):
    from urllib.parse import urlparse, urlunparse
    _p = urlparse(_db_url)
    if _p.password:
        _p = _p._replace(netloc='{}:{}@{}:{}'.format(
            _p.username, urllib.parse.quote(urllib.parse.unquote(_p.password), safe=''),
            _p.hostname, _p.port or 3306))
        _db_url = urlunparse(_p)
app.config['SQLALCHEMY_DATABASE_URI'] = _db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
_SECRET_FILE = os.path.join(BASE_DIR, '.secret_key')
if os.environ.get('TIANJI_SECRET_KEY'):
    app.config['SECRET_KEY'] = os.environ['TIANJI_SECRET_KEY']
else:
    if os.path.isfile(_SECRET_FILE):
        with open(_SECRET_FILE, 'r') as _f:
            app.config['SECRET_KEY'] = _f.read().strip()
    else:
        _sk = secrets.token_hex(32)
        with open(_SECRET_FILE, 'w') as _f:
            _f.write(_sk)
        app.config['SECRET_KEY'] = _sk
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['REMEMBER_COOKIE_DURATION'] = 86400 * 30  # 30天
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', os.path.join(BASE_DIR, 'uploads'))
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB 上传限制

# ═══════ 初始化扩展（从 extensions 模块） ═══════
from extensions import db, login_manager, csrf
from points_service import (
    MEMBER_TOOL_LIMIT,
    POINT_RULES,
    add_points,
    create_daily_sign_in_once,
    get_or_create_membership,
    init_points_service,
    refund_ai_quota_once,
    spend_ai_quota_once,
    use_points,
)


@event.listens_for(Engine, 'connect')
def _set_sqlite_connection_pragmas(dbapi_connection, connection_record):
    """统一 SQLite 连接参数，降低生产并发写入和锁等待风险。"""
    module_name = getattr(dbapi_connection.__class__, '__module__', '')
    if 'sqlite3' not in module_name:
        return
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute('PRAGMA busy_timeout=5000')
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.execute('PRAGMA journal_mode=WAL')
    finally:
        cursor.close()


db.init_app(app)
login_manager.init_app(app)
csrf.init_app(app)
init_points_service(db)

# ── 启动时检查数据库表结构，添加缺失字段 ──
# 使用模块级标志避免 Gunicorn 多 worker / reload 时重复执行
_early_startup_checks_done = False
_startup_checks_done = False
with app.app_context():
    if not _early_startup_checks_done:
        _early_startup_checks_done = True
        # 确保所有表已创建（适用于 SQLite 和 MySQL）
        try:
            db.create_all()
        except Exception as _e:
            logger.warning(f"db.create_all() 失败: {_e}")
        # 运行迁移脚本（在 migrate_db 定义之后调用，见下方 _run_startup_migrations）
    # SQLite 专属：补充第三方登录字段
    import sqlite3 as _sqlite3
    try:
        conn = _sqlite3.connect(app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', ''))
        c = conn.cursor()
        c.execute("PRAGMA table_info(user)")
        cols = [row[1] for row in c.fetchall()]
        if 'oauth_qq' not in cols:
            c.execute("ALTER TABLE user ADD COLUMN oauth_qq VARCHAR(64)")
        if 'oauth_wechat' not in cols:
            c.execute("ALTER TABLE user ADD COLUMN oauth_wechat VARCHAR(64)")
        if 'oauth_gitee' not in cols:
            c.execute("ALTER TABLE user ADD COLUMN oauth_gitee VARCHAR(64)")
        if 'email' not in cols:
            c.execute("ALTER TABLE user ADD COLUMN email VARCHAR(120)")
        if 'phone' not in cols:
            c.execute("ALTER TABLE user ADD COLUMN phone VARCHAR(20)")
        conn.commit()
        conn.close()
    except Exception as _e:
        pass

# ═══════ Gzip 压缩 ═══════
from flask_compress import Compress
Compress(app)

# ═══════ 静态文件缓存 ═══════
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600  # 静态文件缓存1小时


@app.after_request
def add_security_headers(response):
    """基础安全响应头，不改变现有 API 鉴权方式。"""
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    return response


# ═══════ 导入数据模型（必须在 db.init_app 之后） ═══════
from models import User, Record, UserProfile
from models import Post, Master, Membership, PointLog, PaidContent, Purchase, RechargeOrder, AdminAuditLog, TarotConversation, LiuyaoConversation, MeihuaConversation, QimenConversation, BaziConversation, ZiweiConversation, ComprehensiveConversation
from models import MigrationRecord, VerificationCode, RateLimitBucket, AiRun
from models import BaziRecord
from ai_runs import start_ai_run, mark_ai_run_running, mark_ai_run_done, mark_ai_run_failed
from migrations import record_migration_applied

# ═══════ 农历转公历 ═══════
def lunar_to_solar(birth_time, cal_type):
    if cal_type != '农历' or not HAS_LUNAR or len(birth_time) < 8:
        return birth_time, cal_type
    try:
        year = int(birth_time[0:4])
        month = int(birth_time[4:6])
        day = int(birth_time[6:8])
        lunar = Lunar(year, month, day, isleap=False)
        solar = Converter.Lunar2Solar(lunar)
        new_time = f"{solar.year}{solar.month:02d}{solar.day:02d}"
        if len(birth_time) >= 12:
            new_time += birth_time[8:12]
        logger.debug(f"农历转公历: {birth_time} -> {new_time}")
        return new_time, '公历'
    except Exception as e:
        logger.debug(f"农历转换失败: {e}")
        return birth_time, cal_type

# ═══════ 运行目录管理 (天机问策) ═══════
RUN_BASE = '/tmp/qimen_runs'
current_process = None
current_lock = threading.Lock()
current_run_id = 0

def get_run_dir(run_id):
    d = os.path.join(RUN_BASE, str(run_id))
    os.makedirs(d, exist_ok=True)
    return d

def write_run_status(run_id, data):
    d = get_run_dir(run_id)
    with open(os.path.join(d, 'status.json'), 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)

def read_run_status(run_id):
    try:
        d = get_run_dir(run_id)
        with open(os.path.join(d, 'status.json'), 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {'phase': 'idle', 'message': '未启动', 'progress': 0}

def read_run_result(run_id):
    try:
        d = get_run_dir(run_id)
        with open(os.path.join(d, 'result.txt'), 'r', encoding='utf-8') as f:
            return f.read().strip()
    except (FileNotFoundError, OSError):
        return None

def read_run_qimen(run_id):
    try:
        d = get_run_dir(run_id)
        with open(os.path.join(d, 'qimen.json'), 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None

def cleanup_old_runs(keep_run_id):
    try:
        if not os.path.exists(RUN_BASE):
            return
        for d in os.listdir(RUN_BASE):
            try:
                rid = int(d)
                if rid != keep_run_id:
                    shutil.rmtree(os.path.join(RUN_BASE, d), ignore_errors=True)
            except (ValueError, OSError):
                pass
    except (OSError, ValueError):
        pass

def reserve_run_id():
    """申请新的自动化运行 ID，并停止上一轮 shell 进程。"""
    global current_run_id, current_process
    with current_lock:
        if current_process and current_process.poll() is None:
            current_process.terminate()
            try:
                current_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                current_process.kill()
        current_run_id += 1
        return current_run_id

def set_current_process(proc):
    """记录当前自动化进程，供后续运行打断。"""
    global current_process
    with current_lock:
        current_process = proc

def is_current_run(run_id):
    """判断后台线程是否仍属于最新运行。"""
    with current_lock:
        return run_id == current_run_id

def run_automation(question, run_id, record_id=None):
    """在后台线程中运行奇门自动化"""
    global current_process
    try:
        run_dir = get_run_dir(run_id)
        write_run_status(run_id, {'phase': 'starting', 'message': '准备中...', 'progress': 2, 'run_id': run_id})

        with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
            f.write(question)

        env = os.environ.copy()
        env['QIMEN_QUESTION_FILE'] = os.path.join(run_dir, 'question.txt')
        env['QIMEN_RUN_DIR'] = run_dir
        env['QIMEN_RUN_ID'] = str(run_id)

        stdout_log = open(os.path.join(run_dir, 'stdout.log'), 'w')
        stderr_log = open(os.path.join(run_dir, 'stderr.log'), 'w')
        proc = subprocess.Popen(
            ['bash', os.path.join(BASE_DIR, 'qimen_web.sh')],
            env=env, stdout=stdout_log, stderr=stderr_log,
        )
        with current_lock:
            current_process = proc
        proc.wait()
        stdout_log.close()
        stderr_log.close()

        with current_lock:
            if run_id != current_run_id:
                return

        result = read_run_result(run_id)
        status = read_run_status(run_id)
        if result and status.get('phase') != 'error':
            write_run_status(run_id, {'phase': 'done', 'message': '解答完成', 'progress': 100, 'run_id': run_id})
            if record_id:
                try:
                    with app.app_context():
                        rec = db.session.get(Record, record_id)
                        if rec:
                            rec.result_html = result
                            qimen = read_run_qimen(run_id)
                            if qimen:
                                rec.qimen_json = json.dumps(qimen, ensure_ascii=False)
                            db.session.commit()
                except Exception as e:
                    logger.warning(f"保存记录失败: {e}")
        elif status.get('phase') != 'error':
            write_run_status(run_id, {'phase': 'error', 'message': '自动化完成但未获取到答案', 'progress': 0})

    except Exception as e:
        with current_lock:
            if run_id != current_run_id:
                return
        write_run_status(run_id, {'phase': 'error', 'message': f'运行出错: {str(e)}', 'progress': 0})


# ═══════════════════════════════════════════════════════════════
# 数据库迁移
# ═══════════════════════════════════════════════════════════════

def migrate_db():
    """检查并添加缺失的列/表（兼容已有数据库）"""
    with app.app_context():
        # 1. record.app_type
        try:
            db.session.execute(db.text('SELECT app_type FROM record LIMIT 1'))
        except Exception:
            try:
                db.session.execute(db.text(
                    "ALTER TABLE record ADD COLUMN app_type VARCHAR(20) DEFAULT 'qimen'"
                ))
                db.session.commit()
                logger.info("[DB] 已添加 app_type 字段")
            except Exception as e:
                logger.warning(f"app_type 迁移失败: {e}")

        # 2. 创建新表（如果不存在）
        for tbl in ['user_profile', 'follow_up', 'collection', 'post', 'comment', 'master', 'post_like',
                     'membership', 'point_log', 'paid_content', 'purchase', 'recharge_order',
                     'admin_audit_log', 'tarot_conversation', 'migration_record', 'verification_code',
                     'rate_limit_bucket', 'ai_run']:
            try:
                db.session.execute(db.text(f'SELECT 1 FROM {tbl} LIMIT 1'))
            except Exception:
                logger.warning(f"表 {tbl} 不存在，尝试创建")
                try:
                    db.session.rollback()
                    table = db.metadata.tables.get(tbl)
                    if table is not None:
                        table.create(bind=db.engine, checkfirst=True)
                        logger.info(f"[DB] 已确保 {tbl} 表存在")
                    else:
                        logger.warning(f"表 {tbl} 未在 SQLAlchemy metadata 中声明")
                except Exception as ce:
                    db.session.rollback()
                    if 'already exists' not in str(ce).lower():
                        logger.warning(f"{tbl} 表创建失败: {ce}")

        # 3. user.daily_tool_count / user.last_tool_date
        for col, ctype in [('daily_tool_count', 'INTEGER DEFAULT 0'), ('last_tool_date', 'VARCHAR(10)')]:
            try:
                db.session.execute(db.text(f'SELECT {col} FROM `user` LIMIT 1'))
            except Exception:
                try:
                    db.session.execute(db.text(f'ALTER TABLE `user` ADD COLUMN {col} {ctype}'))
                    db.session.commit()
                    logger.warning(f"已添加 user.{col} 字段")
                except Exception as e:
                    logger.warning(f"user.{col} 迁移失败: {e}")

        # 4. point_log.dedupe_key：用于签到、充值等积分动作幂等
        try:
            db.session.execute(db.text('SELECT dedupe_key FROM point_log LIMIT 1'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE point_log ADD COLUMN dedupe_key VARCHAR(160)'))
                db.session.commit()
                logger.info("[DB] 已添加 point_log.dedupe_key 字段")
            except Exception as e:
                db.session.rollback()
                logger.warning(f"point_log.dedupe_key 迁移失败: {e}")
        try:
            dialect = db.session.bind.dialect.name if db.session.bind else ''
            if dialect == 'sqlite':
                db.session.execute(db.text(
                    'CREATE UNIQUE INDEX IF NOT EXISTS ix_point_log_dedupe_key ON point_log (dedupe_key)'
                ))
            else:
                db.session.execute(db.text(
                    'CREATE UNIQUE INDEX ix_point_log_dedupe_key ON point_log (dedupe_key)'
                ))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                logger.warning(f"point_log.dedupe_key 唯一索引迁移失败: {e}")

        # 5. user.has_password
        try:
            db.session.execute(db.text('SELECT has_password FROM `user` LIMIT 1'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE `user` ADD COLUMN has_password BOOLEAN DEFAULT 0'))
                db.session.commit()
                # 已有用户标记为有密码（保守策略）
                db.session.execute(db.text('UPDATE `user` SET has_password = 1'))
                db.session.commit()
                logger.info("[DB] 已添加 has_password 字段")
            except Exception as e:
                logger.warning(f"has_password 迁移失败: {e}")

        # 6. user.is_admin：统一后台权限字段，并兼容早期 user_id=1 管理员约定
        try:
            db.session.execute(db.text('SELECT is_admin FROM `user` LIMIT 1'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE `user` ADD COLUMN is_admin BOOLEAN DEFAULT 0'))
                db.session.commit()
                logger.info("[DB] 已添加 is_admin 字段")
            except Exception as e:
                db.session.rollback()
                logger.warning(f"is_admin 迁移失败: {e}")
        try:
            admin_count = db.session.execute(db.text(
                'SELECT COUNT(*) FROM `user` WHERE COALESCE(is_admin, 0) = 1'
            )).scalar() or 0
            if admin_count == 0:
                result = db.session.execute(db.text(
                    'UPDATE `user` SET is_admin = 1 WHERE id = 1'
                ))
                db.session.commit()
                if result.rowcount:
                    logger.info("[DB] 已将旧版 id=1 管理员迁移为 is_admin")
        except Exception as e:
            db.session.rollback()
            logger.warning(f"is_admin 兼容迁移失败: {e}")

        # 7. recharge_order 付款识别字段：记录用户提交的支付宝凭证，方便审计和重复核验
        for col, ctype in [
            ('payment_reference', 'VARCHAR(120) DEFAULT \'\''),
            ('payment_proof', 'TEXT DEFAULT \'\''),
            ('verified_at', 'DATETIME'),
        ]:
            try:
                db.session.execute(db.text(f'SELECT {col} FROM recharge_order LIMIT 1'))
            except Exception:
                try:
                    db.session.execute(db.text(f'ALTER TABLE recharge_order ADD COLUMN {col} {ctype}'))
                    db.session.commit()
                    logger.info(f"[DB] 已添加 recharge_order.{col} 字段")
                except Exception as e:
                    db.session.rollback()
                    logger.warning(f"recharge_order.{col} 迁移失败: {e}")
        try:
            dialect = db.session.bind.dialect.name if db.session.bind else ''
            if dialect == 'sqlite':
                db.session.execute(db.text('CREATE INDEX IF NOT EXISTS ix_user_is_admin ON `user` (is_admin)'))
            else:
                db.session.execute(db.text('CREATE INDEX ix_user_is_admin ON `user` (is_admin)'))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                logger.warning(f"is_admin 索引迁移失败: {e}")

        # 8. user_profile 扩展字段：统一命盘档案来源与排盘参数
        for col, ctype in [
            ('profile_type', "VARCHAR(10) DEFAULT 'self'"),
            ('source', "VARCHAR(30) DEFAULT 'manual'"),
            ('source_record_id', 'INTEGER'),
            ('meta_json', 'TEXT DEFAULT \'\''),
            ('last_used_at', 'DATETIME'),
        ]:
            try:
                db.session.execute(db.text(f'SELECT {col} FROM user_profile LIMIT 1'))
            except Exception:
                try:
                    db.session.execute(db.text(f'ALTER TABLE user_profile ADD COLUMN {col} {ctype}'))
                    db.session.commit()
                    logger.info(f"[DB] 已添加 user_profile.{col} 字段")
                except Exception as e:
                    logger.warning(f"user_profile.{col} 迁移失败: {e}")

        # 9. membership AI 次数包字段
        for col, ctype in [
            ('ai_single_credits', 'INTEGER DEFAULT 0'),
            ('ai_combo_credits', 'INTEGER DEFAULT 0'),
            ('daily_ai_light_used_at', "VARCHAR(10) DEFAULT ''"),
        ]:
            try:
                db.session.execute(db.text(f'SELECT {col} FROM membership LIMIT 1'))
            except Exception:
                try:
                    db.session.execute(db.text(f'ALTER TABLE membership ADD COLUMN {col} {ctype}'))
                    db.session.commit()
                    logger.info(f"[DB] 已添加 membership.{col} 字段")
                except Exception as e:
                    db.session.rollback()
                    logger.warning(f"membership.{col} 迁移失败: {e}")

        # 5. post.image_url
        try:
            db.session.execute(db.text('SELECT image_url FROM post LIMIT 1'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE post ADD COLUMN image_url VARCHAR(500)'))
                db.session.commit()
                logger.info("[DB] 已添加 post.image_url 字段")
            except Exception as e:
                logger.warning(f"post.image_url 迁移失败: {e}")

        # 6. user.avatar
        try:
            db.session.execute(db.text('SELECT avatar FROM `user` LIMIT 1'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE `user` ADD COLUMN avatar VARCHAR(200) DEFAULT \'\''))
                db.session.commit()
                logger.info("[DB] 已添加 user.avatar 字段")
            except Exception as e:
                logger.warning(f"user.avatar 迁移失败: {e}")

        # 9. bazi_record.pinned
        try:
            db.session.execute(db.text('SELECT pinned FROM bazi_record LIMIT 1'))
        except Exception:
            try:
                db.session.execute(db.text('ALTER TABLE bazi_record ADD COLUMN pinned BOOLEAN DEFAULT 0'))
                db.session.commit()
                logger.info("[DB] 已添加 bazi_record.pinned 字段")
            except Exception as e:
                logger.warning(f"bazi_record.pinned 迁移失败: {e}")

        # 确保上传目录存在
        upload_dir = app.config.get('UPLOAD_FOLDER')
        if upload_dir and not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            logger.info(f"[DB] 已创建上传目录: {upload_dir}")

        # 7. bazi_conversation.user_id nullable（SQLite不支持ALTER COLUMN）
        try:
            result = db.session.execute(db.text('PRAGMA table_info(bazi_conversation)'))
            for row in result.fetchall():
                if row[1] == 'user_id' and row[3] == 1:  # notnull=1
                    logger.info("[DB] bazi_conversation.user_id 需要改为可空")
                    db.session.execute(db.text('''
                        CREATE TABLE bazi_conversation_new (
                            id INTEGER PRIMARY KEY,
                            user_id INTEGER,
                            title VARCHAR(100),
                            birth_data TEXT,
                            messages_json TEXT,
                            created_at DATETIME,
                            updated_at DATETIME
                        )
                    '''))
                    db.session.execute(db.text('INSERT INTO bazi_conversation_new SELECT * FROM bazi_conversation'))
                    db.session.execute(db.text('DROP TABLE bazi_conversation'))
                    db.session.execute(db.text('ALTER TABLE bazi_conversation_new RENAME TO bazi_conversation'))
                    db.session.commit()
                    logger.info("[DB] bazi_conversation.user_id 已改为可空")
                    break
        except Exception as e:
            logger.warning(f"bazi_conversation 迁移失败: {e}")

        # 10. 高频列表与查重查询的复合索引。只创建缺失索引，不改表结构和数据。
        db_indexes = [
            ('ix_record_user_app_created', 'record', 'user_id, app_type, created_at'),
            ('ix_user_profile_user_type_last_created', 'user_profile', 'user_id, profile_type, last_used_at, created_at'),
            ('ix_user_profile_user_source_record', 'user_profile', 'user_id, source, source_record_id'),
            ('ix_follow_up_user_record_created', 'follow_up', 'user_id, record_id, created_at'),
            ('ix_collection_user_target_created', 'collection', 'user_id, target_type, created_at'),
            ('ix_post_hidden_pinned_created', 'post', 'is_hidden, is_pinned, created_at'),
            ('ix_post_featured_pinned_created', 'post', 'is_featured, is_pinned, created_at'),
            ('ix_post_user_created', 'post', 'user_id, created_at'),
            ('ix_comment_post_parent_created', 'comment', 'post_id, parent_id, created_at'),
            ('ix_notification_user_read_created', 'notification', 'user_id, is_read, created_at'),
            ('ix_report_status_created', 'report', 'status, created_at'),
            ('ix_admin_audit_log_action_created', 'admin_audit_log', 'action, created_at'),
            ('ix_point_log_user_created', 'point_log', 'user_id, created_at'),
            ('ix_point_log_user_action_created', 'point_log', 'user_id, action, created_at'),
            ('ix_recharge_order_user_created', 'recharge_order', 'user_id, created_at'),
            ('ix_recharge_order_status_created', 'recharge_order', 'status, created_at'),
            ('ix_recharge_order_payment_reference', 'recharge_order', 'payment_reference'),
            ('ix_bazi_record_user_pinned_created', 'bazi_record', 'user_id, pinned, created_at'),
            ('ix_tarot_conversation_user_updated', 'tarot_conversation', 'user_id, updated_at'),
            ('ix_liuyao_conversation_user_updated', 'liuyao_conversation', 'user_id, updated_at'),
            ('ix_meihua_conversation_user_updated', 'meihua_conversation', 'user_id, updated_at'),
            ('ix_qimen_conversation_user_updated', 'qimen_conversation', 'user_id, updated_at'),
            ('ix_bazi_conversation_user_updated', 'bazi_conversation', 'user_id, updated_at'),
            ('ix_ziwei_conversation_user_updated', 'ziwei_conversation', 'user_id, updated_at'),
            ('ix_comprehensive_conversation_user_updated', 'comprehensive_conversation', 'user_id, updated_at'),
        ]
        dialect = db.session.bind.dialect.name if db.session.bind else ''
        for idx_name, table_name, columns in db_indexes:
            try:
                if dialect == 'sqlite':
                    db.session.execute(db.text(
                        f'CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name} ({columns})'
                    ))
                else:
                    db.session.execute(db.text(f'CREATE INDEX {idx_name} ON {table_name} ({columns})'))
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                if 'already exists' not in str(e).lower() and 'duplicate' not in str(e).lower():
                    logger.warning(f"{idx_name} 索引迁移失败: {e}")

        # 8. Backfill: 已有 BaziConversation 创建 Record（确保侧边栏显示）
        try:
            from sqlalchemy import text as _sql
            bazi_rec_count = db.session.execute(_sql(
                "SELECT COUNT(*) FROM record WHERE app_type='bazi'"
            )).scalar() or 0
            conv_count = db.session.execute(_sql(
                "SELECT COUNT(*) FROM bazi_conversation"
            )).scalar() or 0
            if bazi_rec_count < conv_count:
                convs = BaziConversation.query.order_by(BaziConversation.created_at.asc()).all()
                count = 0
                for conv in convs:
                    uid = conv.user_id or 1
                    msgs = json.loads(conv.messages_json) if conv.messages_json else []
                    last_assistant = ''
                    for msg in reversed(msgs):
                        if msg.get('role') == 'assistant' and msg.get('content'):
                            last_assistant = msg['content']
                            break
                    rec = Record(
                        user_id=uid, app_type='bazi',
                        question=(conv.title or '八字AI解读')[:200],
                        result_html=last_assistant,
                    )
                    db.session.add(rec)
                    count += 1
                if count:
                    db.session.commit()
                    logger.info(f"[DB] 已为 {count} 条旧 BaziConversation 创建 Record")
        except Exception as e:
            logger.warning(f"bazi backfill 迁移失败: {e}")

        record_migration_applied('legacy_startup_migrate_db', '启动时兼容迁移已执行', logger=logger)

# ── 启动时运行数据库迁移（在 migrate_db 定义之后调用）──
if not _startup_checks_done:
    _startup_checks_done = True
    try:
        with app.app_context():
            migrate_db()
    except Exception as _e:
        logger.warning(f"启动迁移失败: {_e}")

# ═══════════════════════════════════════════════════════════════
# 页面路由
# ═══════════════════════════════════════════════════════════════

@app.route('/sitemap.xml')
def sitemap():
    """动态生成 sitemap.xml"""
    from datetime import datetime
    pages = [
        ('/', '1.0'),
        ('/qimen', '0.9'),
        ('/bazi-page', '0.9'),
        ('/meihua', '0.8'),
        ('/liuyao', '0.8'),
        ('/ziwei', '0.8'),
        ('/tarot', '0.8'),
        ('/hepan', '0.7'),
        ('/calendar', '0.7'),
        ('/about', '0.5'),
        ('/community', '0.5'),
    ]
    today = datetime.utcnow().strftime('%Y-%m-%d')
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, priority in pages:
        xml_parts.append(f'''  <url>
    <loc>https://shian.app{path}</loc>
    <lastmod>{today}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>{priority}</priority>
  </url>''')
    xml_parts.append('</urlset>')
    return '\n'.join(xml_parts), 200, {'Content-Type': 'application/xml'}

@app.route('/')
def home():
    """后端健康检查。前端由 Nginx/H5 静态目录承载。"""
    return jsonify({
        'success': True,
        'service': 'xuan-cet-backend',
        'mode': 'api-only',
        'message': '后端仅提供 API；前端页面由 H5 静态服务承载。',
    })


def _frontend_removed(route_name, frontend_hash=None):
    """旧版 Flask 页面已移除，避免后端继续混入前端模板。"""
    payload = {
        'success': False,
        'error': 'legacy_frontend_removed',
        'message': f'{route_name} 旧版 Flask 页面已移除，请访问 H5 前端。',
    }
    if frontend_hash:
        payload['frontend_hash'] = frontend_hash
    return jsonify(payload), 410

@app.route('/tool')
def tool():
    """旧工具页已由 H5 接管。"""
    return _frontend_removed('工具页', '#/')

@app.route('/calendar')
def calendar():
    """旧专属日历页已由 H5 接管。"""
    return _frontend_removed('专属日历', '#/pages/calendar/index')

@app.route('/about')
def about():
    """旧关于我们页已由 H5 接管。"""
    return _frontend_removed('关于我们', '#/pages/about/index')

@app.route('/algorithm')
def algorithm_review():
    """旧算法说明页已由 H5 接管。"""
    return _frontend_removed('排盘算法说明')

@app.route('/qimen')
def qimen_page():
    """旧奇门遁甲页已由 H5 接管。"""
    return _frontend_removed('奇门遁甲', '#/pages/qimen/index?tab=free')

@app.route('/bazi-page')
def bazi_page():
    """旧八字排盘页已由 H5 接管。"""
    return _frontend_removed('八字排盘', '#/pages/bazi-index/index?tab=free')

@app.route('/meihua')
def meihua_page():
    """旧梅花易数页已由 H5 接管。"""
    return _frontend_removed('梅花易数', '#/pages/meihua/index')


@app.route('/community')
def community_page():
    """旧社区页已由 H5 接管。"""
    return _frontend_removed('社区', '#/pages/community/index')

@app.route('/bazi')
def bazi_result():
    """旧八字结果页已由 H5 接管。"""
    return _frontend_removed('八字排盘结果', '#/pages/bazi-result/index')


@app.route('/bazi-pro')
def bazi_pro_pan():
    """旧时安八字专业细盘页已由 H5 接管。"""
    return _frontend_removed('时安八字专业细盘', '#/pages/bazi-result/index')


@app.route('/hepan')
def hepan():
    """旧八字合盘页已由 H5 接管。"""
    return _frontend_removed('八字合盘')


@app.route('/liuyao')
def liuyao_page():
    """旧六爻排盘页已由 H5 接管。"""
    return _frontend_removed('六爻排盘', '#/pages/liuyao/index')

@app.route('/ziwei')
def ziwei_page():
    """旧紫微斗数页已由 H5 接管。"""
    return _frontend_removed('紫微斗数', '#/pages/ziwei/index')

@app.route('/tarot')
def tarot_page():
    """旧塔罗牌页已由 H5 接管。"""
    return _frontend_removed('塔罗牌', '#/pages/tarot/index')

@app.route('/zeji')
def zeji_page():
    """旧择吉工具页已由 H5 接管。"""
    return _frontend_removed('择吉工具', '#/pages/zeji/index')


@app.route('/profile')
def profile_page():
    """旧个人中心页已由 H5 接管。"""
    return _frontend_removed('个人中心', '#/pages/profile/index')


@app.route('/history')
def bazi_history():
    """旧排盘历史页已由 H5 接管。"""
    return _frontend_removed('排盘历史', '#/pages/bazi-index/index?tab=record')


# ═══════════════════════════════════════════════════════════════
# 天机问策路由
# ═══════════════════════════════════════════════════════════════

@app.route('/start', methods=['POST'])
@login_required
def start():
    global current_run_id, current_process
    question = request.form.get('question', '').strip()
    if not question:
        return jsonify({'error': '请输入问题'}), 400

    with current_lock:
        if current_process and current_process.poll() is None:
            current_process.terminate()
            try:
                current_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                current_process.kill()
        current_run_id += 1
        run_id = current_run_id

    cleanup_old_runs(run_id)
    write_run_status(run_id, {'phase': 'starting', 'message': '准备中...', 'progress': 0, 'run_id': run_id})

    record = Record(question=question, user_id=current_user.id, app_type='qimen', run_id=run_id)
    db.session.add(record)
    db.session.commit()
    record_id = record.id

    t = threading.Thread(target=run_automation, args=(question, run_id, record_id), daemon=True)
    t.start()
    return jsonify({'status': 'started', 'run_id': run_id, 'record_id': record_id})

@app.route('/status')
def status():
    run_id = request.args.get('run_id', '0')
    try:
        run_id = int(run_id)
    except (ValueError, TypeError):
        run_id = 0

    if run_id <= 0:
        return jsonify({'phase': 'idle', 'message': '等待开始', 'progress': 0})

    s = read_run_status(run_id)
    s['result'] = read_run_result(run_id)
    s['qimen'] = read_run_qimen(run_id)
    s['run_id'] = run_id
    return jsonify(s)

@app.route('/reset', methods=['POST'])
def reset():
    return jsonify({'status': 'reset'})


# ═══════════════════════════════════════════════════════════════
# 奇门遁甲自写排盘引擎（时家转盘奇门，拆补法）
# ═══════════════════════════════════════════════════════════════

# 天干地支
_TIAN_GAN = list('甲乙丙丁戊己庚辛壬癸')
_DI_ZHI = list('子丑寅卯辰巳午未申酉戌亥')

# 九宫八卦
_GONG_BAGUA = {1:'坎', 2:'坤', 3:'震', 4:'巽', 5:'中', 6:'乾', 7:'兑', 8:'艮', 9:'离'}
_GONG_NAMES = {1:'坎一宫(北)', 2:'坤二宫(西南)', 3:'震三宫(东)', 4:'巽四宫(东南)',
               5:'中五宫(中)', 6:'乾六宫(西北)', 7:'兑七宫(西)', 8:'艮八宫(东北)', 9:'离九宫(南)'}

# 九宫五行
_GONG_WUXING = {1:'水', 2:'土', 3:'木', 4:'木', 5:'土', 6:'金', 7:'金', 8:'土', 9:'火'}

# 地支→宫位
_DIZHI_GONG = {'子':1, '丑':8, '寅':8, '卯':3, '辰':4, '巳':4,
               '午':9, '未':2, '申':2, '酉':7, '戌':6, '亥':6}

# 宫位→地支(主要)
_GONG_DIZHI = {1:['子'], 2:['未','申'], 3:['卯'], 4:['辰','巳'],
               5:[], 6:['戌','亥'], 7:['酉'], 8:['丑','寅'], 9:['午']}

# 九星原始宫位
_XING_YUAN_GONG = {'蓬':1, '芮':2, '冲':3, '辅':4, '禽':5, '心':6, '柱':7, '任':8, '英':9}
# 九星排列顺序(按原始宫位)
_XING_ORDER = ['蓬','芮','冲','辅','禽','心','柱','任','英']
_XING_FULL = {'蓬':'天蓬','芮':'天芮','冲':'天冲','辅':'天辅','禽':'天禽','心':'天心','柱':'天柱','任':'天任','英':'天英'}

# 八门原始宫位(5宫无门)
_MEN_YUAN_GONG = {'休':1, '死':2, '伤':3, '杜':4, '开':6, '惊':7, '生':8, '景':9}
_MEN_ORDER = ['休','死','伤','杜','开','惊','生','景']
_MEN_FULL = {'休':'休门','死':'死门','伤':'伤门','杜':'杜门','开':'开门','惊':'惊门','生':'生门','景':'景门'}
_MEN_WUXING = {'休':'水','死':'土','伤':'木','杜':'木','开':'金','惊':'金','生':'土','景':'火'}

# 八神排列
_SHEN_ORDER = ['符','蛇','阴','合','虎','玄','地','天']
_SHEN_FULL = {'符':'值符','蛇':'螣蛇','阴':'太阴','合':'六合','虎':'白虎','玄':'玄武','地':'九地','天':'九天'}

# 8宫环形顺序(顺时针: 坎→艮→震→巽→离→坤→兑→乾)
_GONG_RING = [1,8,3,4,9,2,7,6]

# 宫位顺时针序列(从坤2开始，与3meta一致)
_PALACE_CLOCKWISE = [2,7,6,1,8,3,4,9]
_PALACE_COUNTER_CLOCKWISE = [2,9,4,3,8,1,6,7]

# 八门排列顺序(与3meta的GATE_SEQUENCE一致)
_GATE_SEQUENCE = ['休','生','伤','杜','景','死','惊','开']

# 洛书飞步
_LUOSHU_FLY = [1,2,3,4,5,6,7,8,9]

# 六仪遁甲
_XUN_LIUYI = {'甲子':'戊','甲戌':'己','甲申':'庚','甲午':'辛','甲辰':'壬','甲寅':'癸'}
# 反向
_LIUYI_XUN = {'戊':'甲子','己':'甲戌','庚':'甲申','辛':'甲午','壬':'甲辰','癸':'甲寅'}

# 空亡
_XUN_KONG = {'甲子':'戌亥','甲戌':'申酉','甲申':'午未','甲午':'辰巳','甲辰':'寅卯','甲寅':'子丑'}

# 驿马(日支三合局定)
_YIMA = {'申':'寅','子':'寅','辰':'寅',   # 申子辰→寅
         '寅':'申','午':'申','戌':'申',     # 寅午戌→申
         '巳':'亥','酉':'亥','丑':'亥',     # 巳酉丑→亥
         '亥':'巳','卯':'巳','未':'巳'}     # 亥卯未→巳

# 六仪击刑
_JI_XING = {'戊':3, '己':2, '庚':8, '辛':9, '壬':4, '癸':4}

# 入墓 — 十二长生法(与3meta一致)
# 每个天干对应其"墓"所在的地支列表
# 阳干顺行墓、阴干逆行墓，部分干有两个墓地支(如乙墓于未和戌)
_RU_MU_DIZHI = {
    '甲': [],
    '乙': ['未', '戌'],
    '丙': ['戌'],
    '丁': ['丑'],
    '戊': ['戌'],
    '己': ['丑'],
    '庚': ['丑'],
    '辛': ['辰'],
    '壬': ['辰'],
    '癸': ['未'],
}

# 五行相克
_KE_MAP = {'木':'土','土':'水','水':'火','火':'金','金':'木'}

# 中文数字
_NUM_CN = {1:'一',2:'二',3:'三',4:'四',5:'五',6:'六',7:'七',8:'八',9:'九'}

# 局日
_JU_DAY = {'甲':'甲己日','己':'甲己日','乙':'乙庚日','庚':'乙庚日',
           '丙':'丙辛日','辛':'丙辛日','丁':'丁壬日','壬':'丁壬日',
           '戊':'戊癸日','癸':'戊癸日'}

# 24节气局数表
# 格式: (节气名, 遁型'阳'/'阴', 上元局数, 中元局数, 下元局数)
_JIEQI_JU_TABLE = [
    ('冬至', '阳', 1, 7, 4),
    ('小寒', '阳', 2, 8, 5),
    ('大寒', '阳', 3, 9, 6),
    ('立春', '阳', 8, 5, 2),
    ('雨水', '阳', 9, 6, 3),
    ('惊蛰', '阳', 1, 7, 4),
    ('春分', '阳', 3, 9, 6),
    ('清明', '阳', 4, 1, 7),
    ('谷雨', '阳', 5, 2, 8),
    ('立夏', '阳', 4, 1, 7),
    ('小满', '阳', 5, 2, 8),
    ('芒种', '阳', 6, 3, 9),
    ('夏至', '阴', 9, 3, 6),
    ('小暑', '阴', 8, 2, 5),
    ('大暑', '阴', 7, 1, 4),
    ('立秋', '阴', 2, 5, 8),
    ('处暑', '阴', 1, 4, 7),
    ('白露', '阴', 9, 3, 6),
    ('秋分', '阴', 7, 1, 4),
    ('寒露', '阴', 6, 9, 3),
    ('霜降', '阴', 5, 8, 2),
    ('立冬', '阴', 6, 9, 3),
    ('小雪', '阴', 5, 8, 2),
    ('大雪', '阴', 4, 7, 1),
]

# 24节气太阳黄经角度(从冬至270°开始，每15°一个)
_JIEQI_DEGREES = [270, 285, 300, 315, 330, 345, 0, 15, 30, 45, 60, 75,
                  90, 105, 120, 135, 150, 165, 180, 195, 210, 225, 240, 255]

# 长生十二运
_CHANGSHENG_TABLE = {
    '甲': '亥', '乙': '午', '丙': '寅', '丁': '酉',
    '戊': '寅', '己': '酉', '庚': '巳', '辛': '子',
    '壬': '申', '癸': '卯'
}
_CS_ORDER = ['长生','沐浴','冠带','临官','帝旺','衰','病','死','墓','绝','胎','养']
# 阳干顺行
_YANG_GAN = ['甲','丙','戊','庚','壬']

# 宫位→主要地支（用于长生十二运）
_GONG_ZHU_ZHI = {1:'子', 2:'未', 3:'卯', 4:'辰', 5:'', 6:'戌', 7:'酉', 8:'丑', 9:'午'}


def _calc_changsheng(tian_gan, gong_num_or_dizhis):
    """计算天干在某宫的长生十二运（支持多天干×多地支 → 数组返回）
    
    与 3meta calcGrowth() 对齐：当有天干×地支笛卡尔积时返回数组。
    
    Args:
        tian_gan: 天干字符串或天干列表（如'甲' 或 ['辛','丁']）
        gong_num_or_dizhis: 宫位号(int, 1-9) 或地支列表
    
    Returns:
        单个结果时返回字符串（如'长生'），多个结果时返回列表，
        无结果时返回'无'（与 3meta 一致）
    """
    # 获取该宫的全量地支（与 3meta PALACE_BRANCHES 一致）
    if isinstance(gong_num_or_dizhis, int):
        gong_dizhis = _GONG_DIZHI.get(gong_num_or_dizhis, [])
    else:
        gong_dizhis = gong_num_or_dizhis if gong_num_or_dizhis else []
    
    # 中5宫无地支 → 返回 "无"（与 3meta 一致）
    if not gong_dizhis:
        return '无'
    
    # 统一天干为列表
    if isinstance(tian_gan, str):
        tian_gans = [tian_gan] if tian_gan else []
    else:
        tian_gans = tian_gan if tian_gan else []
    
    if not tian_gans:
        return '无'
    
    results = []
    for gan in tian_gans:
        if not gan:
            continue
        cs_start_zhi = _CHANGSHENG_TABLE.get(gan, '')
        if not cs_start_zhi:
            continue
        start_idx = _DI_ZHI.index(cs_start_zhi)
        is_yang = gan in _YANG_GAN
        
        for zhi in gong_dizhis:
            target_idx = _DI_ZHI.index(zhi)
            if is_yang:
                offset = (target_idx - start_idx) % 12
            else:
                offset = (start_idx - target_idx) % 12
            results.append(_CS_ORDER[offset])
    
    if len(results) == 1:
        return results[0]
    elif len(results) > 1:
        return results
    return '无'


# ═══════════════════════════════════════════════════════════════
# 辅助函数
# ═══════════════════════════════════════════════════════════════

def _gan_zhi_to_num(gan, zhi):
    """干支→六十甲子序号(0-59)"""
    tg = _TIAN_GAN.index(gan)
    dz = _DI_ZHI.index(zhi)
    for i in range(60):
        if i % 10 == tg and i % 12 == dz:
            return i
    return 0


def _calc_ganzhi(year, month, day, hour, minute=0):
    """计算四柱干支，使用 sxtwl 库"""
    import sxtwl
    # 处理23点（子时）：23:00-1:00 都属于当前日的子时，用当前日干
    actual_hour = hour
    if hour == 23:
        actual_hour = 0

    # 日柱
    day_obj = sxtwl.fromSolar(year, month, day)
    day_gz_index = day_obj.getDayGZ()
    day_gan = _TIAN_GAN[day_gz_index.tg]
    day_zhi = _DI_ZHI[day_gz_index.dz]

    # 时柱：用五鼠遁（整个子时都用当天日干）
    # 日干甲己起甲子，乙庚起丙子，丙辛起戊子，丁壬起庚子，戊癸起壬子
    hour_gan_start = [0,2,4,6,8][day_gz_index.tg % 5]

    zhi_index = (actual_hour + 1) // 2 % 12
    if hour == 23:
        zhi_index = 0  # 子时
    hour_gan_index = (hour_gan_start + zhi_index) % 10
    hour_gan = _TIAN_GAN[hour_gan_index]
    hour_zhi = _DI_ZHI[zhi_index]

    # 年柱、月柱按精确节气时刻定界；sxtwl 在节气当天容易提前切换整天。
    try:
        from bazi_engine import calc_month_pillar, calc_year_pillar, get_jieqi_times
        dt_solar = datetime(year, month, day, hour, minute, 0)
        jieqi_times = get_jieqi_times(year)
        year_gan, year_zhi = calc_year_pillar(dt_solar, jieqi_times)
        month_gan, month_zhi = calc_month_pillar(dt_solar, year_gan, jieqi_times)
    except Exception:
        year_obj = sxtwl.fromSolar(year, month, day)
        year_gz_index = year_obj.getYearGZ()
        year_gan = _TIAN_GAN[year_gz_index.tg]
        year_zhi = _DI_ZHI[year_gz_index.dz]
        month_gz_index = year_obj.getMonthGZ()
        month_gan = _TIAN_GAN[month_gz_index.tg]
        month_zhi = _DI_ZHI[month_gz_index.dz]

    # 旬首：时柱的旬首
    gz_num = _gan_zhi_to_num(hour_gan, hour_zhi)
    xun_head_num = (gz_num // 10) * 10
    xun_head_gan = _TIAN_GAN[xun_head_num % 10]
    xun_head_zhi = _DI_ZHI[xun_head_num % 12]
    xun_name = xun_head_gan + xun_head_zhi
    xun_shou = _XUN_LIUYI.get(xun_name, '')

    # 日柱旬首
    day_gz_num = _gan_zhi_to_num(day_gan, day_zhi)
    day_xun_head_num = (day_gz_num // 10) * 10
    day_xun_name = _TIAN_GAN[day_xun_head_num % 10] + _DI_ZHI[day_xun_head_num % 12]

    # 空亡
    day_kong = _XUN_KONG.get(day_xun_name, '')
    hour_kong = _XUN_KONG.get(xun_name, '')

    return {
        'year': year_gan + year_zhi,
        'month': month_gan + month_zhi,
        'day': day_gan + day_zhi,
        'hour': hour_gan + hour_zhi,
        'dayGan': day_gan, 'dayZhi': day_zhi,
        'hourGan': hour_gan, 'hourZhi': hour_zhi,
        'xunShou': xun_shou,
        'xunName': xun_name,
        'dayXunName': day_xun_name,
        'xunKong': {'day': day_kong, 'hour': hour_kong},
    }


def _calc_jieqi_ju(year, month, day, hour, minute, pan_type=2):
    """计算节气和起局

    现在项目只保留一套对外"拆补法"：以符头定元，处理超神、接气、正授。
    """
    import ephem
    import datetime

    # 计算太阳黄经。ephem.Date 按 UTC 解释输入，前端和排盘参数均为北京时间。
    # 若直接传北京时间，会在节气当天提前 8 小时切换节气。
    local_dt = datetime.datetime(year, month, day, hour, minute, 0)
    utc_dt = local_dt - datetime.timedelta(hours=8)
    date = ephem.Date(utc_dt)
    sun = ephem.Sun(date)
    eq = ephem.Equatorial(sun.ra, sun.dec, epoch=date)
    ecl = ephem.Ecliptic(eq)
    lon_deg = float(ecl.lon) * 180 / 3.141592653589793
    if lon_deg < 0:
        lon_deg += 360

    # 找当前节气(黄经对应的最近已过节气)
    # _JIEQI_DEGREES 顺序：270(冬至),285,...,345(惊蛰),0(春分),15,...,255(小雪)
    # 黄经范围0-360，需处理345°→0°的跨年跳跃
    jieqi_idx = -1
    for i, deg in enumerate(_JIEQI_DEGREES):
        # 判断黄经是否已过该节气角度
        # 关键：345°(惊蛰)之后是0°(春分)，黄经从345跳到0+时属于惊蛰
        if deg >= 270:
            # 冬至→惊蛰区间(270-345)：只有黄经也在270+范围时才比较
            if lon_deg >= 270:
                if lon_deg >= deg:
                    jieqi_idx = i
                elif jieqi_idx >= 0:
                    break
        else:
            # 春分→小雪区间(0-255)：只有黄经在0-269范围时才比较
            if lon_deg < 270:
                if lon_deg >= deg:
                    jieqi_idx = i
                elif jieqi_idx >= 0:
                    break
    # 处理跨年(270°冬至之后到360°=0°)
    if jieqi_idx == -1:
        for i, deg in enumerate(_JIEQI_DEGREES):
            if lon_deg >= deg:
                jieqi_idx = i

    jieqi_info = _JIEQI_JU_TABLE[jieqi_idx]
    jieqi_name, dun, shang, zhong, xia = jieqi_info
    gz_info = _calc_ganzhi(year, month, day, hour, minute)
    day_gan = gz_info['dayGan']
    day_zhi = gz_info['dayZhi']

    # 拆补法定元：基于符头（甲己日）
    yuan, ju, updated_jieqi_name, updated_dun = _calc_yuan_chaibu(
        year, month, day, hour, minute, jieqi_info, jieqi_idx)
    jieqi_name = updated_jieqi_name
    dun = updated_dun

    # 遁型
    dun_str = '阳遁' if dun == '阳' else '阴遁'
    ju_str = f'{dun_str}{_NUM_CN[ju]}局{yuan}元'

    return {
        'jieqi': jieqi_name,
        'dun': dun,
        'ju': ju,
        'yuan': yuan,
        'juStr': ju_str,
        'juDay': _JU_DAY.get(day_gan, ''),
    }


def _find_jieqi_start_datetime(year, month, day, jieqi_idx):
    """精确计算节气开始时间（二分法）

    使用ephem计算太阳黄经，通过二分法精确定位节气开始时刻。
    返回北京时间的datetime对象。

    Args:
        year, month, day: 当前日期
        jieqi_idx: 节气在_JIEQI_DEGREES中的索引

    Returns:
        datetime对象（北京时间），或None
    """
    import ephem
    import datetime
    import math

    target_deg = _JIEQI_DEGREES[jieqi_idx]

    def get_lon(t):
        """获取太阳黄经(度)"""
        s = ephem.Sun(t)
        eq = ephem.Equatorial(s.ra, s.dec, epoch=t)
        ec = ephem.Ecliptic(eq)
        lon = float(ec.lon) * 180 / math.pi
        if lon < 0:
            lon += 360
        return lon

    def is_after_jieqi(t):
        """判断时刻t是否已在节气之后（太阳已过该黄经度数）"""
        lon = get_lon(t)
        adjusted = (lon - target_deg) % 360
        return adjusted < 180  # True = 太阳已过该节气点

    # 从当前日期往前30天开始搜索，找到节气开始的日期
    test_date = datetime.date(year, month, day)
    start_search = test_date - datetime.timedelta(days=30)
    jieqi_date = None

    for offset in range(35):
        d = start_search + datetime.timedelta(days=offset)
        t = ephem.Date(f'{d.year}/{d.month}/{d.day} 12:00:00')
        if is_after_jieqi(t):
            jieqi_date = d
            break

    if jieqi_date is None:
        return None

    # 二分法精确搜索：在前一天12:00到当天12:00之间精确定位
    prev_date = jieqi_date - datetime.timedelta(days=1)
    lo_t = ephem.Date(f'{prev_date.year}/{prev_date.month}/{prev_date.day} 12:00:00')
    hi_t = ephem.Date(f'{jieqi_date.year}/{jieqi_date.month}/{jieqi_date.day} 12:00:00')

    # 确保搜索范围正确：lo_t应在节气之前，hi_t应在节气之后
    if is_after_jieqi(lo_t):
        # lo_t也在节气之后，继续往前
        for back in range(1, 5):
            d2 = prev_date - datetime.timedelta(days=back)
            lo_t = ephem.Date(f'{d2.year}/{d2.month}/{d2.day} 12:00:00')
            if not is_after_jieqi(lo_t):
                break

    # 50次二分迭代，精度约到秒级
    for _ in range(50):
        mid_t = (lo_t + hi_t) / 2
        if is_after_jieqi(mid_t):
            hi_t = mid_t
        else:
            lo_t = mid_t

    # hi_t是节气开始的精确时刻（UTC）
    # 转换为北京时间 (UTC + 8h)
    d = ephem.Date(hi_t + 8.0 / 24).tuple()
    return datetime.datetime(int(d[0]), int(d[1]), int(d[2]), int(d[3]), int(d[4]))


def _calc_yuan_chaibu(year, month, day, hour, minute, jieqi_info, jieqi_idx):
    """拆补法定元：基于符头（甲己日）

    核心逻辑：
    1. 找到当日干支所属的5日组（符头）
    2. 根据符头干支确定上/中/下元
    3. 计算距当前节气开始日的天数差
    4. 应用超神/接气/正授规则（超神时用下一节气的局数）

    Returns: (yuan, ju, updated_jieqi_name, updated_dun)
        yuan: '上'/'中'/'下'
        ju: 局数 (1-9)
        updated_jieqi_name: 节气名（超神时可能变为下一节气）
        updated_dun: 遁型（超神时可能改变）
    """
    import sxtwl
    import datetime

    jieqi_name, dun, shang, zhong, xia = jieqi_info

    # ─── 1. 获取日干支 ───
    _TIAN_GAN = '甲乙丙丁戊己庚辛壬癸'
    _DI_ZHI = '子丑寅卯辰巳午未申酉戌亥'

    day_obj = sxtwl.fromSolar(year, month, day)
    day_gan_idx = day_obj.getDayGZ().tg
    day_zhi_idx = day_obj.getDayGZ().dz
    day_ganzhi = _TIAN_GAN[day_gan_idx] + _DI_ZHI[day_zhi_idx]

    # ─── 2. 找符头（5日一元）───
    # 60甲子分为12组，每组5天，组首即为符头
    jz = [_TIAN_GAN[i % 10] + _DI_ZHI[i % 12] for i in range(60)]
    day_jz_idx = jz.index(day_ganzhi)
    futou_gz = jz[(day_jz_idx // 5) * 5]  # 当日所属5日组的符头干支

    # ─── 3. 根据符头确定元 ───
    # 符头分类：
    #   上元符头: 甲子/甲午/己卯/己酉
    #   中元符头: 甲寅/甲申/己巳/己亥
    #   下元符头: 甲辰/甲戌/己丑/己未
    _SHANG_FUTOU = {'甲子', '甲午', '己卯', '己酉'}
    _ZHONG_FUTOU = {'甲寅', '甲申', '己巳', '己亥'}
    _XIA_FUTOU = {'甲辰', '甲戌', '己丑', '己未'}

    if futou_gz in _SHANG_FUTOU:
        yuan = '上'
    elif futou_gz in _ZHONG_FUTOU:
        yuan = '中'
    else:
        yuan = '下'

    # ─── 4. 判断当天是否为符头日 ───
    all_futou = _SHANG_FUTOU | _ZHONG_FUTOU | _XIA_FUTOU
    is_futou_day = day_ganzhi in all_futou

    # ─── 5. 精确计算距节气开始日的天数差 ───
    jieqi_start_dt = _find_jieqi_start_datetime(year, month, day, jieqi_idx)

    if jieqi_start_dt:
        current_dt = datetime.datetime(year, month, day, hour, minute, 0)
        difference = (current_dt - jieqi_start_dt).days
    else:
        difference = 0

    # ─── 6. 应用超神/接气/正授规则 ───
    # 超神：符头在节气之前到达，节气还没到但符头已到
    #   条件1: 是符头日 且 距节气>=9天 → 使用下一节气
    #   条件2: 非符头日 且 9<=距节气<15天 → 使用下一节气
    # 正授：符头与节气同日 (符头日 且 距节气==0)
    # 接气：节气在非符头日到达 (非符头日 且 距节气==15)
    # 其他：使用当前节气
    updated_jieqi_name = jieqi_name
    updated_dun = dun
    updated_shang = shang
    updated_zhong = zhong
    updated_xia = xia

    if is_futou_day and difference >= 9:
        # 超神：符头日且距节气>=9天 → 使用下一节气
        next_idx = (jieqi_idx + 1) % 24
        new_info = _JIEQI_JU_TABLE[next_idx]
        updated_jieqi_name = new_info[0]
        updated_dun = new_info[1]
        updated_shang = new_info[2]
        updated_zhong = new_info[3]
        updated_xia = new_info[4]
    elif not is_futou_day and difference >= 9 and difference < 15:
        # 超神：非符头日且9<=距节气<15天 → 使用下一节气
        next_idx = (jieqi_idx + 1) % 24
        new_info = _JIEQI_JU_TABLE[next_idx]
        updated_jieqi_name = new_info[0]
        updated_dun = new_info[1]
        updated_shang = new_info[2]
        updated_zhong = new_info[3]
        updated_xia = new_info[4]

    # 确定局数
    if yuan == '上':
        ju = updated_shang
    elif yuan == '中':
        ju = updated_zhong
    else:
        ju = updated_xia

    return yuan, ju, updated_jieqi_name, updated_dun


def _layout_di_pan(dun, ju):
    """布地盘三奇六仪"""
    gan_order = list('戊己庚辛壬癸丁丙乙')  # 统一顺序
    di_pan = {}
    if dun == '阳':
        # 从ju宫开始，宫号递增(1-9循环)
        for i, gan in enumerate(gan_order):
            gong = (ju - 1 + i) % 9 + 1
            di_pan[gong] = gan
    else:
        # 从ju宫开始，宫号递减(9-1循环)
        for i, gan in enumerate(gan_order):
            gong = (ju - 1 - i) % 9 + 1
            di_pan[gong] = gan
    return di_pan


def _find_zhifu_zhishi(gz_info, di_pan):
    """定值符值使"""
    xun_shou = gz_info['xunShou']  # 旬首六仪(戊己庚辛壬癸之一)

    # 在地盘找旬首六仪所在宫
    liuyi_gong = None
    for gong, gan in di_pan.items():
        if gan == xun_shou:
            liuyi_gong = gong
            break

    # 中宫特殊处理：天禽/天芮寄坤2宫
    if liuyi_gong == 5:
        zhi_fu_star = '禽'
        zhi_shi_door = '死'
        zhi_fu_yuan_gong = 5
        zhi_shi_yuan_gong = 5
        # 实际布星时用天芮代天禽（天禽寄坤 2 宫）
        zhi_fu_star_eff = '芮'
        zhi_fu_eff_gong = 2
    else:
        # 值符：该宫原位九星
        for star, gong in _XING_YUAN_GONG.items():
            if gong == liuyi_gong:
                zhi_fu_star = star
                break
        # 值使：该宫原位八门
        for door, gong in _MEN_YUAN_GONG.items():
            if gong == liuyi_gong:
                zhi_shi_door = door
                break
        zhi_fu_yuan_gong = liuyi_gong
        zhi_shi_yuan_gong = liuyi_gong
        zhi_fu_star_eff = zhi_fu_star
        zhi_fu_eff_gong = liuyi_gong

    return {
        'zhiFuStar': zhi_fu_star,
        'zhiFuStarEff': zhi_fu_star_eff,
        'zhiFuEffGong': zhi_fu_eff_gong,
        'zhiFuYuanGong': zhi_fu_yuan_gong,
        'zhiShiDoor': zhi_shi_door,
        'zhiShiYuanGong': zhi_shi_yuan_gong,
        'liuyiGong': liuyi_gong,
    }


def _layout_tian_pan(di_pan, liuyi_gong, shi_gan_gong, dun):
    """布天盘：转盘法，8宫环形旋转"""
    # 中宫处理
    if liuyi_gong == 5:
        liuyi_gong_eff = 2
    else:
        liuyi_gong_eff = liuyi_gong

    if shi_gan_gong == 5:
        shi_gan_gong_eff = 2  # 时干在中5宫也寄坤2
    else:
        shi_gan_gong_eff = shi_gan_gong

    ring = _GONG_RING  # [1,8,3,4,9,2,7,6]
    src_idx = ring.index(liuyi_gong_eff)
    dst_idx = ring.index(shi_gan_gong_eff)

    # 偏移量：从src旋转到dst需要多少步(顺时针)
    offset = (dst_idx - src_idx) % 8

    tian_pan = {5: di_pan[5]}  # 中5宫不动

    for i in range(8):
        # 地盘 ring[i] 宫的天盘位置
        new_i = (i + offset) % 8
        tian_pan[ring[new_i]] = di_pan[ring[i]]

    return tian_pan


def _layout_jiuxing(zhi_fu_star, zhi_fu_target_gong, dun):
    """布九星：值符星随时干落宫，其余按顺序排布"""
    ring = _GONG_RING

    # 目标宫在环形中的位置
    if zhi_fu_target_gong == 5:
        target_idx = ring.index(2)  # 寄坤2
    else:
        target_idx = ring.index(zhi_fu_target_gong)

    # 九星按环形顺序排列（不含天禽）
    # ring=[1,8,3,4,9,2,7,6] → 蓬,任,冲,辅,英,芮,柱,心
    xing_list = []
    for gong in ring:
        for star, g in _XING_YUAN_GONG.items():
            if g == gong:
                xing_list.append(star)
                break
    
    # 值符星特殊处理：天禽时用天芮替代（天禽寄坤2宫）
    if zhi_fu_star == '禽':
        zhi_fu_star_eff = '芮'
    else:
        zhi_fu_star_eff = zhi_fu_star

    # 值符星在星列表中的索引
    fu_idx = xing_list.index(zhi_fu_star_eff)

    xing_pan = {5: '禽'}  # 天禽永远在5宫

    for i, star in enumerate(xing_list):
        # 值符星对齐到目标宫，其余跟随
        star_ring_idx = (target_idx - fu_idx + i) % 8
        xing_pan[ring[star_ring_idx]] = star

    return xing_pan


def _layout_bamen(zhi_shi_door, steps, dun):
    """布八门：值使门步进法 + 顺时针排列（与3meta一致）

    步进法：值使门从原始宫位出发，每过一个时辰宫位+1(阳遁)或-1(阴遁)。
    排列法：从值使门落宫开始，按PALACE_CLOCKWISE方向排列所有八门。
    """
    # 值使门原始宫位
    yuan_gong = _MEN_YUAN_GONG.get(zhi_shi_door, 2)
    if yuan_gong == 5:
        yuan_gong = 2  # 中门寄坤2

    # 步进法：确定值使门落宫
    position = yuan_gong
    for i in range(steps):
        if dun == '阳':
            position += 1
            if position > 9:
                position = 1
        else:
            position -= 1
            if position < 1:
                position = 9

    # 中5宫寄坤2：对齐转盘奇门「寄坤宫」盘式。
    if position == 5:
        position = 2

    # 从值使门落宫开始，按PALACE_CLOCKWISE方向排列八门
    start_idx = _PALACE_CLOCKWISE.index(position)
    gate_idx = _GATE_SEQUENCE.index(zhi_shi_door)

    men_pan = {5: ''}  # 5宫无门
    for i in range(8):
        palace = _PALACE_CLOCKWISE[(start_idx + i) % 8]
        gate = _GATE_SEQUENCE[(gate_idx + i) % 8]
        men_pan[palace] = gate

    return men_pan


def _layout_bashen(zhi_fu_target_gong, dun):
    """布八神：值符随天盘值符星落宫"""
    ring = _GONG_RING

    if zhi_fu_target_gong == 5:
        target_gong = 2
    else:
        target_gong = zhi_fu_target_gong

    target_idx = ring.index(target_gong)

    shen_pan = {5: ''}  # 5宫无神

    for i, shen in enumerate(_SHEN_ORDER):
        if dun == '阳':
            shen_ring_idx = (target_idx + i) % 8
        else:
            shen_ring_idx = (target_idx - i) % 8
        shen_pan[ring[shen_ring_idx]] = shen

    return shen_pan


_GAN_WUXING = {'甲':'木', '乙':'木', '丙':'火', '丁':'火', '戊':'土', '己':'土', '庚':'金', '辛':'金', '壬':'水', '癸':'水'}
_GAN_YINYANG = {'甲':'阳', '乙':'阴', '丙':'阳', '丁':'阴', '戊':'阳', '己':'阴', '庚':'阳', '辛':'阴', '壬':'阳', '癸':'阴'}
_GAN_HE = {'甲':'己', '己':'甲', '乙':'庚', '庚':'乙', '丙':'辛', '辛':'丙', '丁':'壬', '壬':'丁', '戊':'癸', '癸':'戊'}
_OPPOSITE_GONG = {1:9, 9:1, 2:8, 8:2, 3:7, 7:3, 4:6, 6:4}


def _qimen_pattern(pattern_id, name, pattern_type, level, summary, palace=None, evidence=None, category='palace'):
    auspice = {
        '大吉': 'great_auspicious',
        '吉': 'auspicious',
        '平': 'neutral',
        '凶': 'inauspicious',
        '大凶': 'great_inauspicious',
    }.get(level, 'neutral')
    item = {
        'id': pattern_id,
        'name': name,
        'type': pattern_type,
        'category': category,
        'auspice': auspice,
        'level': level,
        'summary': summary,
        'evidence': evidence or [],
    }
    if palace is not None:
        item['palace'] = palace
        item['palaceName'] = _GONG_NAMES.get(palace, f'{palace}宫')
        item['bagua'] = _GONG_BAGUA.get(palace, '')
    return item


def _qimen_value_list(value):
    if isinstance(value, list):
        return [v for v in value if v]
    return [value] if value else []


def _qimen_add_pattern(patterns, palace_patterns, item):
    patterns.append(item)
    palace = item.get('palace')
    if palace:
        palace_patterns.setdefault(palace, []).append({
            'id': item['id'],
            'name': item['name'],
            'level': item['level'],
            'auspice': item['auspice'],
            'summary': item['summary'],
        })


def _is_wu_bu_yu_shi(day_gan, hour_gan):
    day_wx = _GAN_WUXING.get(day_gan)
    hour_wx = _GAN_WUXING.get(hour_gan)
    if not day_wx or not hour_wx:
        return False
    return _KE_MAP.get(hour_wx) == day_wx and _GAN_YINYANG.get(day_gan) == _GAN_YINYANG.get(hour_gan)


def _detect_qimen_special_patterns(gz, zfzs, shi_gan_gong, palaces):
    """识别可导出的奇门格局。

    这里不替代具体断事，只做客观触发条件输出，供免费排盘、JSON 导出和 AI 解读共用。
    """
    patterns = []
    palace_patterns = {}

    zhi_fu_original = zfzs.get('zhiFuEffGong') or zfzs.get('zhiFuYuanGong')
    if zhi_fu_original and shi_gan_gong:
        if zhi_fu_original == shi_gan_gong:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern(
                'fu_yin', '伏吟', 'global', '凶',
                '值符落回原宫，星门伏吟，事情多停滞反复，宜守不宜急进。',
                palace=shi_gan_gong,
                evidence=[f'值符原宫{zhi_fu_original}宫', f'值符落{shi_gan_gong}宫'],
                category='global',
            ))
        elif _OPPOSITE_GONG.get(zhi_fu_original) == shi_gan_gong:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern(
                'fan_yin', '反吟', 'global', '凶',
                '值符落入原宫对冲之宫，主反复变动、事态易翻转。',
                palace=shi_gan_gong,
                evidence=[f'值符原宫{zhi_fu_original}宫', f'值符落对冲{shi_gan_gong}宫'],
                category='global',
            ))

    day_gan = gz.get('dayGan', '')
    hour_gan = gz.get('hourGan', '')
    if _is_wu_bu_yu_shi(day_gan, hour_gan):
        _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern(
            'wu_bu_yu_shi', '五不遇时', 'global', '大凶',
            '时干克日干且阴阳同性，为奇门重要凶时，谋事多阻。',
            evidence=[f'日干{day_gan}', f'时干{hour_gan}', '时干克日干'],
            category='global',
        ))

    if hour_gan == '甲' or _GAN_HE.get(day_gan) == hour_gan:
        evidence = []
        if hour_gan == '甲':
            evidence.append(f'时柱{gz.get("hour", "")}为六甲时')
        if _GAN_HE.get(day_gan) == hour_gan:
            evidence.append(f'日干{day_gan}与时干{hour_gan}相合')
        _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern(
            'tian_xian_shi_ge', '天显时格', 'global', '吉',
            '六甲透出或日时相合，虽遇伏吟亦可取其显达之象，利明面推进。',
            evidence=evidence,
            category='global',
        ))

    for p in palaces:
        if not p or p.get('gong') == 5:
            continue
        gong = p['gong']
        tian_gans = _qimen_value_list(p.get('tianGan'))
        di_gans = _qimen_value_list(p.get('diGan'))
        men = p.get('men', '')
        shen = p.get('shen', '')
        shen_full = p.get('shenFull') or _SHEN_FULL.get(shen, shen)

        for gan in p.get('ruMuTianGans') or []:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern(
                'ru_mu', '入墓', 'palace', '凶',
                '天盘干入墓库，主受困、闭塞、机会被埋。',
                palace=gong,
                evidence=[f'天盘{gan}入{_GONG_NAMES.get(gong, str(gong))}'],
            ))
            if gan in ('乙', '丙', '丁'):
                _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern(
                    'san_qi_ru_mu', '三奇入墓', 'palace', '凶',
                    '乙丙丁三奇入墓，主机遇受压、才智难展。',
                    palace=gong,
                    evidence=[f'{gan}奇入墓'],
                ))

        if p.get('isKong'):
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern(
                'luo_kong_wang', '落空亡', 'palace', '凶',
                '宫位落入旬空，主虚、空、落空，成事力度不足。',
                palace=gong,
                evidence=['时柱旬空落本宫'],
            ))

        if p.get('isMenPo'):
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern(
                'men_po', '门迫', 'palace', '凶',
                '门克宫位，行动受迫，谋事多阻。',
                palace=gong,
                evidence=[f'{_MEN_FULL.get(men, men)}克宫'],
            ))

        for gan in p.get('jiXingTianGans') or []:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern(
                'liu_yi_ji_xing', '六仪击刑', 'palace', '凶',
                '六仪击刑，主刑伤、争执、官非或突发损害。',
                palace=gong,
                evidence=[f'天盘{gan}临击刑宫'],
            ))

        if '乙' in tian_gans and men == '开':
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('yi_qi_de_shi', '乙奇得使', 'palace', '吉', '乙奇临开门，利谋划、沟通与贵人相助。', gong, ['天盘乙', '开门']))
        if '丙' in tian_gans and men == '休':
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('bing_qi_de_shi', '丙奇得使', 'palace', '吉', '丙奇临休门，利名声、文书和明面推进。', gong, ['天盘丙', '休门']))
        if '丁' in tian_gans and men == '生':
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('ding_qi_de_shi', '丁奇得使', 'palace', '吉', '丁奇临生门，利求财、创意和新机会。', gong, ['天盘丁', '生门']))
        if any(g in tian_gans for g in ('乙', '丙', '丁')) and men in ('休', '生', '开'):
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('san_qi_de_shi', '三奇得使', 'palace', '吉', '三奇临三吉门，主有助力、有机会、有转机。', gong, ['三奇', _MEN_FULL.get(men, men)]))

        if '丁' in tian_gans and men == '开':
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('yu_nv_shou_men', '玉女守门', 'palace', '吉', '丁奇临开门，利婚恋合作、开局启动与求财。', gong, ['天盘丁', '开门']))
        if '丙' in tian_gans and '丁' in di_gans and men == '生':
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('tian_dun', '天遁', 'palace', '吉', '丙丁同临生门，主天时助力，利启动大事。', gong, ['天盘丙', '地盘丁', '生门']))
        if '乙' in tian_gans and men == '开' and shen_full == '九地':
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('di_dun', '地遁', 'palace', '吉', '乙奇临开门加九地，利藏形避害、稳中求成。', gong, ['天盘乙', '开门', '九地']))
        if '丁' in tian_gans and men == '休' and shen_full == '太阴':
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('ren_dun', '人遁', 'palace', '吉', '丁奇临休门加太阴，利人和、暗助、协商。', gong, ['天盘丁', '休门', '太阴']))
        if '丙' in tian_gans and men == '生' and shen_full == '九天':
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('shen_dun', '神遁', 'palace', '吉', '丙奇临生门加九天，利快速推进、高处发力。', gong, ['天盘丙', '生门', '九天']))
        if '丁' in tian_gans and men == '杜' and shen_full == '九地':
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('gui_dun', '鬼遁', 'palace', '吉', '丁奇临杜门加九地，利隐秘布局、暗中成事。', gong, ['天盘丁', '杜门', '九地']))
        if '乙' in tian_gans and men in ('开', '杜') and gong == 4:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('feng_dun', '风遁', 'palace', '吉', '乙奇临开/杜门在巽宫，利运筹、传播、避祸。', gong, ['天盘乙', _MEN_FULL.get(men, men), '巽四宫']))
        if '乙' in tian_gans and men == '开' and gong == 6:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('yun_dun', '云遁', 'palace', '吉', '乙奇临开门在乾宫，利上升、远行、见贵。', gong, ['天盘乙', '开门', '乾六宫']))
        if '乙' in tian_gans and men == '休' and gong == 1:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('long_dun', '龙遁', 'palace', '吉', '乙奇临休门在坎宫，利舒展、远谋、转机。', gong, ['天盘乙', '休门', '坎一宫']))
        if '乙' in tian_gans and men == '开' and gong == 7:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('hu_dun', '虎遁', 'palace', '吉', '乙奇临开门在兑宫，利果断出击、打开局面。', gong, ['天盘乙', '开门', '兑七宫']))

        if '戊' in tian_gans and '丙' in di_gans:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('qing_long_fan_shou', '青龙返首', 'palace', '大吉', '戊加丙，主失而复得、转危为安、名利可成。', gong, ['天盘戊', '地盘丙']))
        if '丙' in tian_gans and '戊' in di_gans:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('fei_niao_die_xue', '飞鸟跌穴', 'palace', '大吉', '丙加戊，主主动进取、大展宏图、诸事顺遂。', gong, ['天盘丙', '地盘戊']))
        if '庚' in tian_gans and '癸' in di_gans:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('da_ge', '大格', 'palace', '大凶', '庚加癸，主谋事难成、阻力重重。', gong, ['天盘庚', '地盘癸']))
        if '庚' in tian_gans and '壬' in di_gans:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('xiao_ge', '小格', 'palace', '凶', '庚加壬，主小阻小滞，进展迟缓。', gong, ['天盘庚', '地盘壬']))
        if '庚' in tian_gans and '己' in di_gans:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('xing_ge', '刑格', 'palace', '凶', '庚加己，主刑伤、官非、争执。', gong, ['天盘庚', '地盘己']))
        if ('丙' in tian_gans and '庚' in di_gans) or ('庚' in tian_gans and '丙' in di_gans):
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('bo_ge', '悖格', 'palace', '大凶', '丙庚互临，主悖逆冲突、事情不顺。', gong, ['丙庚互临']))
        if '癸' in tian_gans and '癸' in di_gans:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('tian_wang_si_zhang', '天网四张', 'palace', '大凶', '癸加癸，主受困难脱，宜避不宜进。', gong, ['天盘癸', '地盘癸']))
        if '辛' in tian_gans and '乙' in di_gans:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('bai_hu_chang_kuang', '白虎猖狂', 'palace', '大凶', '辛加乙，主刑伤灾祸，诸事宜谨慎。', gong, ['天盘辛', '地盘乙']))
        if '丙' in tian_gans and gong == 1:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('zhu_que_tou_jiang', '朱雀投江', 'palace', '凶', '丙奇临坎，文书口舌易沉滞，不利诉讼合约。', gong, ['天盘丙', '坎一宫']))
        if '癸' in tian_gans and '丁' in di_gans:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('teng_she_yao_jiao', '螣蛇夭矫', 'palace', '大凶', '癸加丁，主虚惊缠绕、文书官非、火水相激。', gong, ['天盘癸', '地盘丁']))
        if shen_full == '值符' and zhi_fu_original == gong:
            _qimen_add_pattern(patterns, palace_patterns, _qimen_pattern('tian_yi_fu_gong', '天乙伏宫', 'palace', '吉', '值符伏本宫，主贵人权威、有靠山。', gong, ['值符临本宫']))

    for p in palaces:
        if p:
            p['patterns'] = palace_patterns.get(p.get('gong'), [])

    return patterns


# ═══════════════════════════════════════════════════════════════
# 主排盘函数
# ═══════════════════════════════════════════════════════════════

def _qimen_paipan(year, month, day, hour, minute=0, pan_type=2):
    """自写奇门遁甲排盘引擎"""
    try:
        pan_type = 2
        # Step 1: 干支计算
        gz = _calc_ganzhi(year, month, day, hour, minute)

        # Step 2: 节气起局
        jq = _calc_jieqi_ju(year, month, day, hour, minute, pan_type)

        # Step 3: 布地盘
        di_pan = _layout_di_pan(jq['dun'], jq['ju'])

        # Step 4: 定值符值使
        zfzs = _find_zhifu_zhishi(gz, di_pan)

        # 找时干在地盘的宫位(天盘目标宫)
        # 注意：时干若为甲，甲遁于六仪之下，需用旬首六仪查找
        shi_gan = gz['hourGan']
        if shi_gan == '甲':
            # 甲遁于六仪，用时柱旬首的六仪
            shi_gan_find = gz['xunShou']  # 旬首六仪(戊己庚辛壬癸)
        else:
            shi_gan_find = shi_gan
        shi_gan_gong = None
        for gong, gan in di_pan.items():
            if gan == shi_gan_find:
                shi_gan_gong = gong
                break

        # 找时支对应宫位(八门目标宫)
        shi_zhi_gong = _DIZHI_GONG.get(gz['hourZhi'], 1)

        # Step 5: 布天盘
        tian_pan = _layout_tian_pan(di_pan, zfzs['liuyiGong'], shi_gan_gong, jq['dun'])

        # 布九星
        xing_pan = _layout_jiuxing(zfzs['zhiFuStar'], shi_gan_gong, jq['dun'])

        # Step 6: 布八门（步进法）
        # 值使门从原始宫位出发，每过一个时辰在环上走一步
        xun_name = gz['xunName']
        xun_num = _gan_zhi_to_num('甲', xun_name[1:])  # 旬首的六十甲子序号
        hour_num = _gan_zhi_to_num(gz['hourGan'], gz['hourZhi'])
        men_steps = (hour_num - xun_num) % 60
        men_pan = _layout_bamen(zfzs['zhiShiDoor'], men_steps, jq['dun'])

        # Step 7: 布八神
        shen_pan = _layout_bashen(shi_gan_gong, jq['dun'])

        # 组装九宫数据
        palaces = [None] * 9

        # 空亡宫（只看时柱旬空）
        kong_gongs = set()
        kong_val = gz['xunKong'].get('hour', '')
        for z in kong_val:
            g = _DIZHI_GONG.get(z)
            if g:
                kong_gongs.add(g)

        # 驿马宫(用时支)
        yima_zhi = _YIMA.get(gz['hourZhi'], '')
        ma_gong = _DIZHI_GONG.get(yima_zhi, 0)

        for gong_num in range(1, 10):
            tian_gan = tian_pan.get(gong_num, '')
            di_gan = di_pan.get(gong_num, '')
            men = men_pan.get(gong_num, '')
            xing = xing_pan.get(gong_num, '')
            shen = shen_pan.get(gong_num, '')

            # 标记
            is_ji_xing = _JI_XING.get(tian_gan) == gong_num
            is_di_ji_xing = _JI_XING.get(di_gan) == gong_num
            # 入墓：天干的墓地支是否在该宫的地支中
            gong_dizhis = _GONG_DIZHI.get(gong_num, [])
            tian_mu_dizhis = _RU_MU_DIZHI.get(tian_gan, [])
            di_mu_dizhis = _RU_MU_DIZHI.get(di_gan, [])
            is_ru_mu = any(dz in tian_mu_dizhis for dz in gong_dizhis)
            is_di_ru_mu = any(dz in di_mu_dizhis for dz in gong_dizhis)
            is_men_po = False
            if men and gong_num in _GONG_WUXING:
                men_wx = _MEN_WUXING.get(men, '')
                gong_wx = _GONG_WUXING.get(gong_num, '')
                # 门迫：门克宫（门五行克宫五行）
                if men_wx and gong_wx and _KE_MAP.get(men_wx) == gong_wx:
                    is_men_po = True

            # 长生十二运
            tian_cs = _calc_changsheng(tian_gan, gong_num)
            di_cs = _calc_changsheng(di_gan, gong_num)

            is_kong = gong_num in kong_gongs
            is_ma = gong_num == ma_gong

            palace = {
                'gong': gong_num,
                'name': _GONG_NAMES.get(gong_num, f'{gong_num}宫'),
                'bagua': _GONG_BAGUA.get(gong_num, ''),
                'tianGan': tian_gan,
                'diGan': di_gan,
                'yinGan': '',  # 稍后计算
                'men': men if men else '无门',
                'menFull': _MEN_FULL.get(men, men) if men else '无门',
                'xing': xing,
                'xingFull': _XING_FULL.get(xing, xing),
                'shen': shen if shen else '无神',
                'shenFull': _SHEN_FULL.get(shen, shen) if shen else '无神',
                'tianCs': tian_cs,
                'diCs': di_cs,
                'isKong': is_kong,
                'isMa': is_ma,
                'isJiXing': is_ji_xing,
                'isDiJiXing': is_di_ji_xing,
                'isRuMu': is_ru_mu,
                'isDiRuMu': is_di_ru_mu,
                'isMenPo': is_men_po,
            }
            palaces[gong_num - 1] = palace

        # 中5宫寄宫标记：对齐天禽/天芮寄坤二宫的常用盘式
        ji_gong_target = 2
        for p in palaces:
            if p and p.get('gong') == 5:
                p['jiGong'] = ji_gong_target

        # 中5宫寄宫处理：
        # 1. 寄宫目标（坤2）的地盘干追加中5宫地盘干 → [原干, 中5宫干]
        # 2. 天芮所在宫追加天禽+中5宫天盘干 → xing=[芮,禽], tianGan=[原干,中5宫干]
        zhong_di_gan = di_pan.get(5, '')
        zhong_tian_gan = tian_pan.get(5, '')

        # 地盘干寄宫：寄宫目标 diGan → [原干, 中5宫地盘干]
        p_target = palaces[ji_gong_target - 1]
        if p_target and zhong_di_gan:
            p_target['diGan'] = [p_target['diGan'], zhong_di_gan]

        # 天芮(天禽)当前落宫 → 双星 + 双天盘干
        rui_gong = None
        for p in palaces:
            if p and p.get('xing') == '芮':
                rui_gong = p['gong']
                break
        if rui_gong and rui_gong != 5:
            p_rui = palaces[rui_gong - 1]
            if p_rui:
                # 双星：[芮, 禽]
                p_rui['xing'] = [p_rui['xing'], '禽']
                p_rui['xingFull'] = [p_rui['xingFull'], '天禽']
                # 双天盘干：[原干, 中宫天盘干]
                if zhong_tian_gan:
                    p_rui['tianGan'] = [p_rui['tianGan'], zhong_tian_gan]

        # 寄宫处理后，重新计算击刑（逐字级别）
        # jiXingTianGans: 该宫天盘干中哪些字击刑了
        # jiXingDiGans: 该宫地盘干中哪些字击刑了
        for p in palaces:
            if not p:
                continue
            gong_num = p['gong']
            tian_gan_val = p.get('tianGan', '')
            di_gan_val = p.get('diGan', '')
            tian_gans = tian_gan_val if isinstance(tian_gan_val, list) else ([tian_gan_val] if tian_gan_val else [])
            di_gans = di_gan_val if isinstance(di_gan_val, list) else ([di_gan_val] if di_gan_val else [])
            p['jiXingTianGans'] = [g for g in tian_gans if _JI_XING.get(g) == gong_num]
            p['jiXingDiGans'] = [g for g in di_gans if _JI_XING.get(g) == gong_num]
            # 入墓逐字：该宫地支中是否包含该干的墓地支
            gong_dizhis = _GONG_DIZHI.get(gong_num, [])
            p['ruMuTianGans'] = [g for g in tian_gans if any(dz in _RU_MU_DIZHI.get(g, []) for dz in gong_dizhis)]
            p['ruMuDiGans'] = [g for g in di_gans if any(dz in _RU_MU_DIZHI.get(g, []) for dz in gong_dizhis)]
            # 更新 isJiXing / isDiJiXing / isRuMu / isDiRuMu
            p['isJiXing'] = len(p['jiXingTianGans']) > 0
            p['isDiJiXing'] = len(p['jiXingDiGans']) > 0
            p['isRuMu'] = len(p['ruMuTianGans']) > 0
            p['isDiRuMu'] = len(p['ruMuDiGans']) > 0
        
        # 寄宫后重算长生十二运（用全量地支 _GONG_DIZHI，与3meta一致）
        # 此时某些宫的天盘干/地盘干/地支已变为数组（如宫6双天盘干、宫8双地盘干）
        for p in palaces:
            if not p:
                continue
            gong_num = p['gong']
            tian_gan_val = p.get('tianGan', '')
            di_gan_val = p.get('diGan', '')
            tian_gans = tian_gan_val if isinstance(tian_gan_val, list) else ([tian_gan_val] if tian_gan_val else [])
            di_gans = di_gan_val if isinstance(di_gan_val, list) else ([di_gan_val] if di_gan_val else [])
            p['tianCs'] = _calc_changsheng(tian_gans, gong_num)
            p['diCs'] = _calc_changsheng(di_gans, gong_num)

        # 隐干计算：飞宫法（与3meta一致）
        # 1. 时干放在值使门落宫
        # 2. 阳遁宫位顺序1→9，阴遁宫位顺序9→1
        # 3. 六仪三奇顺序(戊己庚辛壬癸丁丙乙)始终从时干开始正向排列
        # 4. 特殊：甲时若遁干≠中宫地盘干，从中5宫开始；值符值使同宫时从中5宫开始
        gan_fly_order = list('戊己庚辛壬癸丁丙乙')  # 六仪三奇顺序

        # 时干(甲遁六仪)
        original_hour_gan = gz['hourGan']
        shi_gan_for_yin = original_hour_gan
        if shi_gan_for_yin == '甲':
            shi_gan_for_yin = gz['xunShou']

        # 值使门实际落宫
        zhi_shi_gong_yin = None
        for gong_num_y, door_y in men_pan.items():
            if door_y == zfzs['zhiShiDoor']:
                zhi_shi_gong_yin = gong_num_y
                break
        if zhi_shi_gong_yin is None:
            zhi_shi_gong_yin = ji_gong_target  # fallback

        # 确定起始宫位
        start_palace = zhi_shi_gong_yin
        if original_hour_gan == '甲':
            # 甲时特殊规则：若遁干≠中宫地盘干，从中5宫开始
            center_di_gan = di_pan.get(5, '')
            if shi_gan_for_yin != center_di_gan:
                start_palace = 5
        elif shi_gan_gong == zhi_shi_gong_yin:
            # 值符值使同宫时，从中5宫开始
            start_palace = 5

        # 宫位顺序：阳遁顺排1→9，阴遁逆排9→1
        palace_order = [1,2,3,4,5,6,7,8,9] if jq['dun'] == '阳' else [9,8,7,6,5,4,3,2,1]

        # 从时干开始在六仪三奇序列中的位置
        if shi_gan_for_yin in gan_fly_order:
            gan_start_idx = gan_fly_order.index(shi_gan_for_yin)
        else:
            gan_start_idx = 0

        # 从起始宫位在宫位序列中的位置
        gong_start_idx = palace_order.index(start_palace)

        for step in range(9):
            gong_idx = (gong_start_idx + step) % 9
            gan_idx = (gan_start_idx + step) % 9
            target_gong = palace_order[gong_idx]
            target_gan = gan_fly_order[gan_idx]
            p_yin = palaces[target_gong - 1]
            if p_yin:
                p_yin['yinGan'] = target_gan

        # 顶层信息
        zhi_fu_star_name = zfzs['zhiFuStar']
        zhi_shi_door_name = zfzs['zhiShiDoor']

        # 从步进法结果中提取值使实际落宫
        zhi_shi_gong_actual = None
        for gong_num, door in men_pan.items():
            if door == zhi_shi_door_name:
                zhi_shi_gong_actual = gong_num
                break
        if zhi_shi_gong_actual is None:
            zhi_shi_gong_actual = shi_zhi_gong  # fallback

        # 天乙(小值符)：值符原始宫位在当前星盘中的星
        tian_yi_gong = zfzs['zhiFuEffGong']  # 处理中宫寄坤后的六仪宫
        tian_yi_star = xing_pan.get(tian_yi_gong, '')
        tian_yi_full = _XING_FULL.get(tian_yi_star, tian_yi_star) if tian_yi_star else ''
        tian_yi_gong_name = _GONG_NAMES.get(tian_yi_gong, f'{tian_yi_gong}宫')
        tian_yi_str = f'天乙{tian_yi_full}落{tian_yi_gong_name}' if tian_yi_full else f'天乙落{tian_yi_gong_name}'
        special_patterns = _detect_qimen_special_patterns(gz, zfzs, shi_gan_gong, palaces)

        result = {
            'solarDate': f'{year}年{month}月{day}日 {hour:02d}时{minute:02d}分',
            'fourPillars': {
                'year': gz['year'], 'month': gz['month'],
                'day': gz['day'], 'hour': gz['hour'],
            },
            'dayGan': gz['dayGan'],
            'hourGan': gz['hourGan'],
            'ju': jq['juStr'],
            'juDay': jq.get('juDay', ''),
            'solarTerm': jq['jieqi'],
            'xunShou': gz['xunShou'],
            'xunKong': gz['xunKong'],
            'zhiFu': f'值符天{zhi_fu_star_name}落{_GONG_NAMES.get(shi_gan_gong, "")}',
            'zhiShi': f'值使{_MEN_FULL.get(zhi_shi_door_name, zhi_shi_door_name)}落{_GONG_NAMES.get(zhi_shi_gong_actual, "")}',
            'zhiFuStar': zhi_fu_star_name,
            'zhiFuGong': _GONG_BAGUA.get(shi_gan_gong, ''),
            'zhiShiMen': zhi_shi_door_name,
            'zhiShiGong': _GONG_BAGUA.get(zhi_shi_gong_actual, ''),
            'tianYi': tian_yi_str,
            'tianYiStar': tian_yi_star if tian_yi_star else '',
            'tianYiGong': _GONG_BAGUA.get(tian_yi_gong, '') if tian_yi_gong else '',
            'maXing': {'驛馬': yima_zhi},
            'specialPatterns': special_patterns,
            'palaces': palaces,
            'panType': '拆补法',
        }

        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'error': f'排盘计算失败: {e}'}




# 梅花易数排盘引擎 & API
# ═══════════════════════════════════════════════════════════════

# ── 梅花易数基础数据 ──
_MH_BAGUA = {
    '乾': {'num': 1, 'nature': '天', 'trigram': '☰', 'wuxing': '金'},
    '兑': {'num': 2, 'nature': '泽', 'trigram': '☱', 'wuxing': '金'},
    '离': {'num': 3, 'nature': '火', 'trigram': '☲', 'wuxing': '火'},
    '震': {'num': 4, 'nature': '雷', 'trigram': '☳', 'wuxing': '木'},
    '巽': {'num': 5, 'nature': '风', 'trigram': '☴', 'wuxing': '木'},
    '坎': {'num': 6, 'nature': '水', 'trigram': '☵', 'wuxing': '水'},
    '艮': {'num': 7, 'nature': '山', 'trigram': '☶', 'wuxing': '土'},
    '坤': {'num': 8, 'nature': '地', 'trigram': '☷', 'wuxing': '土'},
}

_MH_BAGUA_NAMES = ['乾', '兑', '离', '震', '巽', '坎', '艮', '坤']  # 先天数 1-8

_MH_XIAN_TIAN_NUM = {'乾': 1, '兑': 2, '离': 3, '震': 4, '巽': 5, '坎': 6, '艮': 7, '坤': 8}

_MH_GUA64 = {
    ('乾', '乾'): '乾为天', ('坤', '坤'): '坤为地',
    ('兑', '兑'): '兑为泽', ('离', '离'): '离为火',
    ('震', '震'): '震为雷', ('巽', '巽'): '巽为风',
    ('坎', '坎'): '坎为水', ('艮', '艮'): '艮为山',
    ('乾', '坎'): '天水讼', ('坎', '乾'): '水天需',
    ('乾', '震'): '天雷无妄', ('震', '乾'): '雷天大壮',
    ('乾', '巽'): '天风姤', ('巽', '乾'): '风天小畜',
    ('乾', '艮'): '天山遁', ('艮', '乾'): '山天大畜',
    ('乾', '离'): '天火同人', ('离', '乾'): '火天大有',
    ('乾', '兑'): '天泽履', ('兑', '乾'): '泽天夬',
    ('坤', '坎'): '地水师', ('坎', '坤'): '水地比',
    ('坤', '震'): '地雷复', ('震', '坤'): '雷地豫',
    ('坤', '巽'): '地风升', ('巽', '坤'): '风地观',
    ('坤', '艮'): '地山谦', ('艮', '坤'): '山地剥',
    ('坤', '离'): '地火明夷', ('离', '坤'): '火地晋',
    ('坤', '兑'): '地泽临', ('兑', '坤'): '泽地萃',
    ('坎', '震'): '水雷屯', ('震', '坎'): '雷水解',
    ('坎', '巽'): '水风井', ('巽', '坎'): '风水涣',
    ('坎', '艮'): '水山蹇', ('艮', '坎'): '山水蒙',
    ('坎', '离'): '水火既济', ('离', '坎'): '火水未济',
    ('坎', '兑'): '水泽节', ('兑', '坎'): '泽水困',
    ('震', '巽'): '雷风恒', ('巽', '震'): '风雷益',
    ('震', '艮'): '雷山小过', ('艮', '震'): '山雷颐',
    ('震', '离'): '雷火丰', ('离', '震'): '火雷噬嗑',
    ('震', '兑'): '雷泽归妹', ('兑', '震'): '泽雷随',
    ('巽', '艮'): '风山渐', ('艮', '巽'): '山风蛊',
    ('巽', '离'): '风火家人', ('离', '巽'): '火风鼎',
    ('巽', '兑'): '风泽中孚', ('兑', '巽'): '泽风大过',
    ('艮', '离'): '山火贲', ('离', '艮'): '火山旅',
    ('艮', '兑'): '山泽损', ('兑', '艮'): '泽山咸',
    ('离', '兑'): '火泽睽', ('兑', '离'): '泽火革',
}


def _mh_gua64_name(upper_gua, lower_gua):
    name = _MH_GUA64.get((upper_gua, lower_gua))
    if name:
        return name
    if upper_gua == lower_gua:
        return f'{upper_gua}卦'
    return f'{upper_gua}{lower_gua}卦'

_MH_SHENG = {'金': '水', '水': '木', '木': '火', '火': '土', '土': '金'}
_MH_KE = {'金': '木', '木': '土', '土': '水', '水': '火', '火': '金'}
_MH_SHENG_BY = {'水': '金', '木': '水', '火': '木', '土': '火', '金': '土'}
_MH_KE_BY = {'木': '金', '土': '木', '水': '土', '火': '水', '金': '火'}

_MH_TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
_MH_DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

_MH_MONTH_WUXING = {1: '水', 2: '木', 3: '木', 4: '土', 5: '火', 6: '火',
                     7: '土', 8: '金', 9: '金', 10: '土', 11: '水', 12: '水'}

_MH_JIXIONG = {
    '比和': '吉（体用同气，顺势而成）',
    '生': '小耗（体生用，泄气之象）',
    '克': '小吉（体克用，诸事可为）',
    '被生': '大吉（用生体，得助之象）',
    '被克': '大凶（用克体，受制之象）',
}


def _mh_wuxing_relation(wx1, wx2):
    """五行生克关系：wx1 对 wx2"""
    if _MH_SHENG.get(wx1) == wx2:
        return '生'
    elif _MH_KE.get(wx1) == wx2:
        return '克'
    elif _MH_SHENG_BY.get(wx1) == wx2:
        return '被生'
    elif _MH_KE_BY.get(wx1) == wx2:
        return '被克'
    else:
        return '比和'


def _mh_get_wangshuai(wx, month_wx):
    """根据月令判断五行旺衰"""
    if wx == month_wx:
        return '旺'
    elif _MH_SHENG.get(month_wx) == wx:
        return '相'
    elif _MH_SHENG.get(wx) == month_wx:
        return '休'
    elif _MH_KE.get(month_wx) == wx:
        return '囚'
    else:
        return '死'


# 八卦爻象 (1=阳, 0=阴, 从初爻到三爻即从下到上)
_MH_YAO = {
    '乾': [1, 1, 1],  # ☰ 三阳
    '兑': [1, 1, 0],  # ☱ 上阴中阳下阳
    '离': [1, 0, 1],  # ☲ 上阳中阴下阳
    '震': [1, 0, 0],  # ☳ 上阴中阴下阳
    '巽': [0, 1, 1],  # ☴ 上阳中阳下阴
    '坎': [0, 1, 0],  # ☵ 上阴中阳下阴
    '艮': [0, 0, 1],  # ☶ 上阳中阴下阴
    '坤': [0, 0, 0],  # ☷ 三阴
}

# 爻象→卦名反查表
_MH_YAO_TO_NAME = {tuple(v): k for k, v in _MH_YAO.items()}


def _mh_num_to_yao(n):
    """先天数转三爻数组（1=阳, 0=阴），初爻在前（低位在前）"""
    # 通过先天数→卦名→爻象 查表，确保爻线与卦象一致
    gua_name = _MH_BAGUA_NAMES[n - 1]
    return _MH_YAO[gua_name][:]


def _mh_yao_to_gua_name(yao_list):
    """三爻数组转卦名"""
    return _MH_YAO_TO_NAME.get(tuple(yao_list), '乾')


def _meihua_paipan(method='time', num1=None, num2=None, words=None,
                    year=None, month=None, day=None, hour=None):
    """梅花易数排盘核心引擎 — 邵雍正统规则

    支持三种起卦方式：
    - time: 时间起卦（年+月+日 %8 为上卦，年+月+日+时 %8 为下卦）
    - number: 数字起卦（num1%8 为上卦，num2%8 为下卦，和%6 为动爻）
    - word: 字数起卦（前半字数%8 为上卦，后半字数%8 为下卦，总字数%6 为动爻）
    """
    try:
        now = datetime.now()
        y = year or now.year
        m = month or now.month
        d = day or now.day
        h = hour if hour is not None else ((now.hour + 1) // 2) % 12 + 1

        # ── 计算干支（简化版） ──
        gz_year = _MH_TIANGAN[(y - 4) % 10] + _MH_DIZHI[(y - 4) % 12]
        gz_month = _MH_TIANGAN[(m - 1) % 10] + _MH_DIZHI[(m + 1) % 12]
        gz_day = _MH_TIANGAN[(d - 1) % 10] + _MH_DIZHI[(d + 7) % 12]
        hour_idx = (now.hour + 1) // 2 % 12
        gz_hour = _MH_TIANGAN[(d * 2 + hour_idx) % 10] + _MH_DIZHI[hour_idx]

        # ── 起卦 ──
        if method == 'number' and num1 is not None:
            num1 = int(num1)
            num2 = int(num2) if num2 else 0
            upper_num = num1 % 8
            if upper_num == 0:
                upper_num = 8
            lower_num = num2 % 8 if num2 else (num1 + 1) % 8
            if lower_num == 0:
                lower_num = 8
            dong_yao = (num1 + num2) % 6 if num2 else num1 % 6
            if dong_yao == 0:
                dong_yao = 6
            method_label = f'数字起卦（{num1},{num2 or num1+1}）'
        elif method == 'word' and words:
            wlen = len(words)
            if wlen < 1:
                return {'error': '字数不能为空'}
            first_half = wlen // 2
            upper_num = first_half % 8 if first_half > 0 else wlen % 8
            lower_num = (wlen - first_half) % 8 if first_half > 0 else (wlen + 1) % 8
            if upper_num == 0:
                upper_num = 8
            if lower_num == 0:
                lower_num = 8
            dong_yao = wlen % 6
            if dong_yao == 0:
                dong_yao = 6
            method_label = f'字数起卦（{wlen}字）'
        else:
            # 时间起卦（默认）— 使用农历日期 + 年地支序数
            # 年数 = 年地支序数（子1 丑2 ... 亥12）
            # 月数 = 农历月
            # 日数 = 农历日
            # 时数 = 时辰序数（子1 丑2 ... 亥12）
            year_num = (y - 4) % 12 + 1  # 公历转地支序数（子=1 丑=2 ... 亥=12）
            month_num = m
            day_num = d
            hour_num = h
            # 尝试用农历日期（更准确）
            try:
                from lunar_python import Solar, Lunar as _Lunar
                solar = Solar.fromYmd(y, m, d)
                lunar = solar.getLunar()
                lunar_month = lunar.getMonth()
                lunar_day = lunar.getDay()
                if lunar_month:
                    month_num = lunar_month
                    day_num = lunar_day
            except:
                pass

            upper_num = (year_num + month_num + day_num) % 8
            if upper_num == 0:
                upper_num = 8
            lower_num = (year_num + month_num + day_num + hour_num) % 8
            if lower_num == 0:
                lower_num = 8
            dong_yao = (year_num + month_num + day_num + hour_num) % 6
            if dong_yao == 0:
                dong_yao = 6
            method_label = '时间起卦'

        upper_gua = _MH_BAGUA_NAMES[upper_num - 1]
        lower_gua = _MH_BAGUA_NAMES[lower_num - 1]

        # ── 本卦 ──
        ben_gua_name = _mh_gua64_name(upper_gua, lower_gua)
        upper_wuxing = _MH_BAGUA[upper_gua]['wuxing']
        lower_wuxing = _MH_BAGUA[lower_gua]['wuxing']

        # ── 互卦 ──
        upper_yao = _mh_num_to_yao(_MH_XIAN_TIAN_NUM[upper_gua])
        lower_yao = _mh_num_to_yao(_MH_XIAN_TIAN_NUM[lower_gua])
        all_yao = lower_yao + upper_yao  # [初,二,三,四,五,六]

        hu_lower = [all_yao[1], all_yao[2], all_yao[3]]
        hu_upper = [all_yao[2], all_yao[3], all_yao[4]]
        hu_lower_gua = _mh_yao_to_gua_name(hu_lower)
        hu_upper_gua = _mh_yao_to_gua_name(hu_upper)
        hu_gua_name = _mh_gua64_name(hu_upper_gua, hu_lower_gua)

        # ── 变卦 ──
        bian_yao = all_yao[:]
        bian_yao[dong_yao - 1] = 1 - bian_yao[dong_yao - 1]
        bian_lower_gua = _mh_yao_to_gua_name(bian_yao[:3])
        bian_upper_gua = _mh_yao_to_gua_name(bian_yao[3:])
        bian_gua_name = _mh_gua64_name(bian_upper_gua, bian_lower_gua)

        # ── 体用分析 ──
        if dong_yao <= 3:
            ti_gua = upper_gua
            yong_gua = lower_gua
            ti_position = '上卦'
            yong_position = '下卦'
        else:
            ti_gua = lower_gua
            yong_gua = upper_gua
            ti_position = '下卦'
            yong_position = '上卦'

        ti_wuxing = _MH_BAGUA[ti_gua]['wuxing']
        yong_wuxing = _MH_BAGUA[yong_gua]['wuxing']

        ti_yong_rel = _mh_wuxing_relation(ti_wuxing, yong_wuxing)

        # 互卦与体卦关系
        hu_wuxing = _MH_BAGUA[hu_upper_gua]['wuxing']
        ti_hu_rel = _mh_wuxing_relation(ti_wuxing, hu_wuxing)

        # 变卦与体卦关系
        bian_wuxing = _MH_BAGUA[bian_upper_gua]['wuxing']
        ti_bian_rel = _mh_wuxing_relation(ti_wuxing, bian_wuxing)

        # ── 卦气旺衰 ──
        month_wx = _MH_MONTH_WUXING.get(m, '土')
        ti_wangshuai = _mh_get_wangshuai(ti_wuxing, month_wx)
        yong_wangshuai = _mh_get_wangshuai(yong_wuxing, month_wx)

        # ── 断语 ──
        jixiong = _MH_JIXIONG.get(ti_yong_rel, '待断')
        verdict = f'体卦{ti_wuxing}于{m}月{ti_wangshuai}，用卦{yong_wuxing}{yong_wangshuai}。{jixiong}'

        # ── 组装结果 ──
        result = {
            'success': True,
            'methodLabel': method_label,
            'paipanTime': now.strftime('%Y年%m月%d日 %H:%M:%S'),
            'ganzhi': f'{gz_year}年 {gz_month}月 {gz_day}日 {gz_hour}时',
            'dongYao': dong_yao,
            'benGua': {
                'name': ben_gua_name,
                'upper': {'name': upper_gua, 'nature': _MH_BAGUA[upper_gua]['nature'],
                          'trigram': _MH_BAGUA[upper_gua]['trigram'], 'wuxing': upper_wuxing},
                'lower': {'name': lower_gua, 'nature': _MH_BAGUA[lower_gua]['nature'],
                          'trigram': _MH_BAGUA[lower_gua]['trigram'], 'wuxing': lower_wuxing},
            },
            'benGuaYao': all_yao,
            'huGua': {
                'name': hu_gua_name,
                'upper': {'name': hu_upper_gua, 'nature': _MH_BAGUA[hu_upper_gua]['nature'],
                          'trigram': _MH_BAGUA[hu_upper_gua]['trigram'], 'wuxing': _MH_BAGUA[hu_upper_gua]['wuxing']},
                'lower': {'name': hu_lower_gua, 'nature': _MH_BAGUA[hu_lower_gua]['nature'],
                          'trigram': _MH_BAGUA[hu_lower_gua]['trigram'], 'wuxing': _MH_BAGUA[hu_lower_gua]['wuxing']},
            },
            'huGuaYao': hu_lower + hu_upper,
            'bianGua': {
                'name': bian_gua_name,
                'upper': {'name': bian_upper_gua, 'nature': _MH_BAGUA[bian_upper_gua]['nature'],
                          'trigram': _MH_BAGUA[bian_upper_gua]['trigram'], 'wuxing': _MH_BAGUA[bian_upper_gua]['wuxing']},
                'lower': {'name': bian_lower_gua, 'nature': _MH_BAGUA[bian_lower_gua]['nature'],
                          'trigram': _MH_BAGUA[bian_lower_gua]['trigram'], 'wuxing': _MH_BAGUA[bian_lower_gua]['wuxing']},
            },
            'bianGuaYao': bian_yao,
            'tiYong': {
                'tiGua': ti_gua,
                'tiPosition': ti_position,
                'tiTrigram': _MH_BAGUA[ti_gua]['trigram'],
                'tiWuxing': ti_wuxing,
                'tiWangshuai': ti_wangshuai,
                'yongGua': yong_gua,
                'yongPosition': yong_position,
                'yongTrigram': _MH_BAGUA[yong_gua]['trigram'],
                'yongWuxing': yong_wuxing,
                'yongWangshuai': yong_wangshuai,
                'tiYongRel': ti_yong_rel,
                'tiYongJiXiong': jixiong,
                'huWuxing': hu_wuxing,
                'tiHuRel': ti_hu_rel,
                'bianWuxing': bian_wuxing,
                'tiBianRel': ti_bian_rel,
                'verdict': verdict,
            },
        }

        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'error': f'排盘计算失败: {e}'}




# ═══════════════════════════════════════════════════════════════
# 六爻纳甲排盘 API — 纯Python本地计算，基于 yijing-agent 内核
# ═══════════════════════════════════════════════════════════════

# ── 六爻排盘计算引擎（内联，无需额外依赖） ──

import random as _random
try:
    from lunar_python import Lunar as _Lunar, Solar as _Solar
    _HAS_LUNAR_PY = True
except ImportError:
    _HAS_LUNAR_PY = False

# 八卦线条 (bottom to top): 1=yang, 0=yin
_LY_TRIGRAM_LINES = {
    "乾": [1,1,1], "兑": [1,1,0], "离": [1,0,1], "震": [1,0,0],
    "巽": [0,1,1], "坎": [0,1,0], "艮": [0,0,1], "坤": [0,0,0],
}
_LY_TRIGRAM_NATURE = {"乾":"天","兑":"泽","离":"火","震":"雷","巽":"风","坎":"水","艮":"山","坤":"地"}
_LY_TRIGRAM_ELEMENT = {"乾":"金","兑":"金","离":"火","震":"木","巽":"木","坎":"水","艮":"土","坤":"土"}

_LY_HEXAGRAM_NAMES = {
    ("乾","乾"):"乾为天",("乾","兑"):"天泽履",("乾","离"):"天火同人",("乾","震"):"天雷无妄",
    ("乾","巽"):"天风姤",("乾","坎"):"天水讼",("乾","艮"):"天山遁",("乾","坤"):"天地否",
    ("兑","乾"):"泽天夬",("兑","兑"):"兑为泽",("兑","离"):"泽火革",("兑","震"):"泽雷随",
    ("兑","巽"):"泽风大过",("兑","坎"):"泽水困",("兑","艮"):"泽山咸",("兑","坤"):"泽地萃",
    ("离","乾"):"火天大有",("离","兑"):"火泽睽",("离","离"):"离为火",("离","震"):"火雷噬嗑",
    ("离","巽"):"火风鼎",("离","坎"):"火水未济",("离","艮"):"火山旅",("离","坤"):"火地晋",
    ("震","乾"):"雷天大壮",("震","兑"):"雷泽归妹",("震","离"):"雷火丰",("震","震"):"震为雷",
    ("震","巽"):"雷风恒",("震","坎"):"雷水解",("震","艮"):"雷山小过",("震","坤"):"雷地豫",
    ("巽","乾"):"风天小畜",("巽","兑"):"风泽中孚",("巽","离"):"风火家人",("巽","震"):"风雷益",
    ("巽","巽"):"巽为风",("巽","坎"):"风水涣",("巽","艮"):"风山渐",("巽","坤"):"风地观",
    ("坎","乾"):"水天需",("坎","兑"):"水泽节",("坎","离"):"水火既济",("坎","震"):"水雷屯",
    ("坎","巽"):"水风井",("坎","坎"):"坎为水",("坎","艮"):"水山蹇",("坎","坤"):"水地比",
    ("艮","乾"):"山天大畜",("艮","兑"):"山泽损",("艮","离"):"山火贲",("艮","震"):"山雷颐",
    ("艮","巽"):"山风蛊",("艮","坎"):"山水蒙",("艮","艮"):"艮为山",("艮","坤"):"山地剥",
    ("坤","乾"):"地天泰",("坤","兑"):"地泽临",("坤","离"):"地火明夷",("坤","震"):"地雷复",
    ("坤","巽"):"地风升",("坤","坎"):"地水师",("坤","艮"):"地山谦",("坤","坤"):"坤为地",
}

_LY_DIZHI_ELEMENT = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}

_LY_NAJA = {
    "乾":(["子","寅","辰"],["午","申","戌"]),
    "坤":(["未","巳","卯"],["丑","亥","酉"]),
    "震":(["子","寅","辰"],["午","申","戌"]),
    "巽":(["丑","亥","酉"],["未","巳","卯"]),
    "坎":(["寅","辰","午"],["申","戌","子"]),
    "离":(["卯","丑","亥"],["酉","未","巳"]),
    "艮":(["辰","午","申"],["戌","子","寅"]),
    "兑":(["巳","卯","丑"],["亥","酉","未"]),
}

_LY_NAJA_TIANGAN = {"乾":("甲","壬"),"坤":("乙","癸"),"震":("庚","庚"),"巽":("辛","辛"),"坎":("戊","戊"),"离":("己","己"),"艮":("丙","丙"),"兑":("丁","丁")}

_LY_SHENG = {"木":"火","火":"土","土":"金","金":"水","水":"木"}
_LY_KE = {"木":"土","土":"水","水":"火","火":"金","金":"木"}
_LY_LIU_SHEN = ["青龙","朱雀","勾陈","螣蛇","白虎","玄武"]
_LY_DAY_STEM_SHEN = {"甲":0,"乙":0,"丙":1,"丁":1,"戊":2,"己":3,"庚":4,"辛":4,"壬":5,"癸":5}

_LY_PALACE_ORDER = ["乾","兑","离","震","巽","坎","艮","坤"]
_LY_SHI_POSITIONS = [6,1,2,3,4,5,4,3]

def _ly_flip(line): return 1 - line

def _ly_lines_to_trigram(lines):
    for name, tl in _LY_TRIGRAM_LINES.items():
        if tl == lines: return name
    raise ValueError(f"Invalid lines: {lines}")

def _ly_build_palace_lookup():
    lookup = {}
    for palace in _LY_PALACE_ORDER:
        base = _LY_TRIGRAM_LINES[palace] + _LY_TRIGRAM_LINES[palace]
        for pos in range(8):
            lines = list(base)
            if pos == 1: lines[0] = _ly_flip(lines[0])
            elif pos == 2: lines[0] = _ly_flip(lines[0]); lines[1] = _ly_flip(lines[1])
            elif pos == 3: lines[0] = _ly_flip(lines[0]); lines[1] = _ly_flip(lines[1]); lines[2] = _ly_flip(lines[2])
            elif pos == 4: lines[0] = _ly_flip(lines[0]); lines[1] = _ly_flip(lines[1]); lines[2] = _ly_flip(lines[2]); lines[3] = _ly_flip(lines[3])
            elif pos == 5: lines[0] = _ly_flip(lines[0]); lines[1] = _ly_flip(lines[1]); lines[2] = _ly_flip(lines[2]); lines[3] = _ly_flip(lines[3]); lines[4] = _ly_flip(lines[4])
            elif pos == 6: lines[0] = _ly_flip(lines[0]); lines[1] = _ly_flip(lines[1]); lines[2] = _ly_flip(lines[2]); lines[4] = _ly_flip(lines[4])
            elif pos == 7: lines[4] = _ly_flip(lines[4])
            lower = _ly_lines_to_trigram(lines[0:3])
            upper = _ly_lines_to_trigram(lines[3:6])
            key = (upper, lower)
            if key not in lookup: lookup[key] = (palace, pos)
    return lookup

_LY_PALACE_LOOKUP = _ly_build_palace_lookup()

def _ly_get_shi_ying(upper, lower):
    palace, pos = _LY_PALACE_LOOKUP[(upper, lower)]
    shi = _LY_SHI_POSITIONS[pos]
    ying = ((shi - 1 + 3) % 6) + 1
    return shi, ying

def _ly_get_liuqin(palace_el, line_el):
    if palace_el == line_el: return "兄弟"
    if _LY_SHENG[palace_el] == line_el: return "子孙"
    if _LY_SHENG[line_el] == palace_el: return "父母"
    if _LY_KE[palace_el] == line_el: return "妻财"
    if _LY_KE[line_el] == palace_el: return "官鬼"

def _ly_get_day_ganzhi(date=None):
    now = date or datetime.now()
    if _HAS_LUNAR_PY:
        try:
            solar = _Solar.fromYmd(now.year, now.month, now.day)
            lunar = solar.getLunar()
            return lunar.getDayGan() + lunar.getDayZhi(), lunar.getDayGan()
        except Exception:
            pass
    # fallback: use lunarcalendar if available
    if HAS_LUNAR:
        try:
            from lunarcalendar import Converter, Solar as LSolar
            s = LSolar(now.year, now.month, now.day)
            l = Converter.Solar2Lunar(s)
            # simple ganzhi calculation not implemented here
            return "甲子", "甲"
        except Exception:
            pass
    return "甲子", "甲"

def _ly_get_month_ganzhi(date=None):
    now = date or datetime.now()
    if _HAS_LUNAR_PY:
        try:
            solar = _Solar.fromYmd(now.year, now.month, now.day)
            lunar = solar.getLunar()
            return lunar.getMonthGan() + lunar.getMonthZhi()
        except Exception:
            pass
    return "甲子"

def _liuyao_paipan(mode='auto', tosses=None, question=''):
    """六爻纳甲排盘核心函数"""
    if mode == 'manual':
        if not tosses or len(tosses) != 6:
            return {'error': '手动模式需要6次摇卦结果'}
        for i, t in enumerate(tosses):
            if len(t) != 3 or any(v not in (2,3) for v in t):
                return {'error': f'第{i+1}次摇卦数据无效'}
    else:
        tosses = [[_random.choice([2,3]) for _ in range(3)] for _ in range(6)]

    yao_list = []
    ben_lines = []
    for toss in tosses:
        total = sum(toss)
        if total == 6: yao_list.append(('老阴', True, 0))
        elif total == 7: yao_list.append(('少阳', False, 1))
        elif total == 8: yao_list.append(('少阴', False, 0))
        elif total == 9: yao_list.append(('老阳', True, 1))
        else: return {'error': f'Invalid coin sum: {total}'}
        ben_lines.append(yao_list[-1][2])

    lower = _ly_lines_to_trigram(ben_lines[0:3])
    upper = _ly_lines_to_trigram(ben_lines[3:6])
    ben_name = _LY_HEXAGRAM_NAMES[(upper, lower)]

    bian_lines = list(ben_lines)
    for i, (_, is_moving, _) in enumerate(yao_list):
        if is_moving: bian_lines[i] = _ly_flip(bian_lines[i])

    bian_lower = _ly_lines_to_trigram(bian_lines[0:3])
    bian_upper = _ly_lines_to_trigram(bian_lines[3:6])
    bian_name = _LY_HEXAGRAM_NAMES[(bian_upper, bian_lower)]

    shi, ying = _ly_get_shi_ying(upper, lower)

    naja_dz = list(_LY_NAJA[lower][0]) + list(_LY_NAJA[upper][1])
    naja_tg = [_LY_NAJA_TIANGAN[lower][0]]*3 + [_LY_NAJA_TIANGAN[upper][1]]*3
    palace_trigram, _ = _LY_PALACE_LOOKUP[(upper, lower)]
    palace_element = _LY_TRIGRAM_ELEMENT[palace_trigram]

    liuqin = [_ly_get_liuqin(palace_element, _LY_DIZHI_ELEMENT[dz]) for dz in naja_dz]

    day_ganzhi, day_stem = _ly_get_day_ganzhi()
    month_ganzhi = _ly_get_month_ganzhi()
    shen_start = _LY_DAY_STEM_SHEN.get(day_stem, 0)
    liushen = [_LY_LIU_SHEN[(shen_start + i) % 6] for i in range(6)]

    yao_names = ['初爻','二爻','三爻','四爻','五爻','上爻']
    details = []
    for i in range(6):
        details.append({
            'position': i+1, 'name': yao_names[i],
            'yao_type': yao_list[i][0], 'is_yang': ben_lines[i]==1,
            'is_moving': yao_list[i][1], 'liuqin': liuqin[i], 'liushen': liushen[i],
            'naja': f"{naja_tg[i]}{naja_dz[i]}", 'dizhi_element': _LY_DIZHI_ELEMENT[naja_dz[i]],
            'is_shi': shi==i+1, 'is_ying': ying==i+1,
            'coin_result': tosses[i], 'coin_sum': sum(tosses[i]),
        })

    # 变卦详情
    bian_naja_dz = list(_LY_NAJA[bian_lower][0]) + list(_LY_NAJA[bian_upper][1])
    bian_naja_tg = [_LY_NAJA_TIANGAN[bian_lower][0]]*3 + [_LY_NAJA_TIANGAN[bian_upper][1]]*3
    bian_palace_el = _LY_TRIGRAM_ELEMENT[_LY_PALACE_LOOKUP[(bian_upper, bian_lower)][0]]
    bian_shi, bian_ying = _ly_get_shi_ying(bian_upper, bian_lower)
    bian_liuqin = [_ly_get_liuqin(bian_palace_el, _LY_DIZHI_ELEMENT[dz]) for dz in bian_naja_dz]

    bian_details = []
    for i in range(6):
        bian_details.append({
            'position': i+1, 'name': yao_names[i],
            'yao_type': '变' if yao_list[i][1] else yao_list[i][0],
            'is_yang': bian_lines[i]==1, 'is_moving': False,
            'liuqin': bian_liuqin[i], 'liushen': liushen[i],
            'naja': f"{bian_naja_tg[i]}{bian_naja_dz[i]}",
            'dizhi_element': _LY_DIZHI_ELEMENT[bian_naja_dz[i]],
            'is_shi': bian_shi==i+1, 'is_ying': bian_ying==i+1,
            'coin_result': tosses[i], 'coin_sum': sum(tosses[i]),
        })

    return {
        '六爻': [{'yao_type': y[0], 'is_moving': y[1]} for y in yao_list],
        '本卦': ben_name, '变卦': bian_name,
        '世爻': shi, '应爻': ying,
        '六亲': liuqin, '六神': liushen,
        'details': details, 'bian_details': bian_details,
        'upper_trigram': upper, 'lower_trigram': lower,
        'upper_nature': _LY_TRIGRAM_NATURE[upper], 'lower_nature': _LY_TRIGRAM_NATURE[lower],
        'palace_name': palace_trigram, 'palace_element': palace_element,
        'bian_upper_trigram': bian_upper, 'bian_lower_trigram': bian_lower,
        'bian_upper_nature': _LY_TRIGRAM_NATURE[bian_upper], 'bian_lower_nature': _LY_TRIGRAM_NATURE[bian_lower],
        'day_ganzhi': day_ganzhi, 'month_ganzhi': month_ganzhi, 'day_stem': day_stem,
        'method': '手动摇卦' if mode == 'manual' else '自动摇卦',
        'question': question or '',
        'timestamp': datetime.now().isoformat(),
    }




# ═══════════════════════════════════════════════════════════════
# 塔罗牌抽牌 API — 纯Python本地计算，基于 tarot_engine 内核
# ═══════════════════════════════════════════════════════════════

try:
    from tarot_engine import draw_cards as _tarot_draw, get_available_spreads as _tarot_spreads, verify_deck_integrity as _tarot_verify
    HAS_TAROT = True
except ImportError:
    _tarot_draw = None
    _tarot_spreads = None
    _tarot_verify = None
    HAS_TAROT = False

# ── 紫微斗数引擎导入 ──
try:
    from ziwei_engine import ZiweiEngine as _ZiweiEngine, SHICHEN_NAMES as _ZW_SHICHEN, SHICHEN_RANGES as _ZW_SHICHEN_RANGES, PALACE_NAME_MAP as _ZW_PALACE_MAP
    _zw_engine = _ZiweiEngine()
    HAS_ZIWEI = True
except ImportError:
    _zw_engine = None
    HAS_ZIWEI = False




# ═══════════════════════════════════════════════════════════════
# 八字排盘路由
# ═══════════════════════════════════════════════════════════════

def _build_local_bazi_pro_payload(local_result, year, month, day, hour, minute, sex):
    """把时安本地八字结果转换为专业盘兼容结构。"""
    from bazi_engine import calc_shi_shen_for_gan

    fp = local_result.get('four_pillars') or {}
    day_master = local_result.get('day_master') or (fp.get('day') or {}).get('gan', '')

    def _ss_name(value):
        if value == '偏官':
            return '七杀'
        if value == '日主':
            return '比肩'
        return value

    def _pillar_item(key):
        pillar = fp.get(key) or {}
        gan = pillar.get('gan', '')
        zhi = pillar.get('zhi', '')
        cg = (local_result.get('cang_gan') or {}).get(key, [])
        cgss = (local_result.get('cang_gan_shi_shen') or {}).get(key, [])
        return {
            'tg': gan,
            'dz': zhi,
            'ss': local_result.get('day_master_label') if key == 'day' else _ss_name((local_result.get('shi_shen') or {}).get(f'{key}_gan', '')),
            'canggan': [{'gz': item, 'ss': _ss_name(cgss[i] if i < len(cgss) else '')} for i, item in enumerate(cg)],
            'xingyun': (local_result.get('xing_yun') or {}).get(key, ''),
            'zizuo': (local_result.get('zi_zuo') or {}).get(key, ''),
            'kongwang': (local_result.get('kong_wang_per_pillar') or {}).get(key, ''),
            'nayin': pillar.get('nayin', ''),
            'shensha': (local_result.get('shen_sha_per_pillar') or {}).get(key, []),
        }

    def _map_yun_item(item):
        gan = item.get('gan', '')
        zhi = item.get('zhi', '')
        return {
            'year': str(item.get('start_year') or item.get('year') or ''),
            'age': f"{item.get('start_age')}~{item.get('end_age')}岁" if item.get('start_age') and item.get('end_age') and item.get('start_age') != item.get('end_age') else (f"{item.get('start_age')}岁" if item.get('start_age') else ''),
            'tg': gan,
            'tgSs': _ss_name(calc_shi_shen_for_gan(day_master, gan)) if day_master and gan else '',
            'dz': zhi,
            'dzSs': _ss_name(calc_shi_shen_for_gan(day_master, ((item.get('cang_gan') or [''])[0]))) if day_master and item.get('cang_gan') else '',
            'gan_zhi': item.get('gan_zhi', ''),
            'current': bool(item.get('current')),
            'start_age': item.get('start_age'),
            'end_age': item.get('end_age'),
            'start_year': item.get('start_year'),
            'end_year': item.get('end_year'),
            'is_pre_qiyun': bool(item.get('is_pre_qiyun')),
        }

    def _map_liunian_item(item):
        gan = item.get('gan') or (item.get('gan_zhi') or '')[:1]
        zhi = item.get('zhi') or (item.get('gan_zhi') or '')[1:2]
        return {
            'year': str(item.get('year') or ''),
            'age': item.get('age') or '',
            'tg': gan,
            'tgSs': item.get('gan_shishen_abbrev') or _ss_name(item.get('shi_shen_gan') or ''),
            'dz': zhi,
            'dzSs': item.get('zhi_shishen_abbrev') or '',
            'gan_zhi': item.get('gan_zhi') or (gan + zhi),
            'current': bool(item.get('current')),
            'xiao_yun': item.get('xiao_yun_gan_zhi', ''),
            'shensha': item.get('shen_sha', []),
        }

    def _map_xiaoyun_item(item):
        gz = item.get('gan_zhi') or ''
        gan = item.get('gan') or gz[:1]
        zhi = item.get('zhi') or gz[1:2]
        return {'age': item.get('age'), 'tg': gan, 'dz': zhi, 'gan_zhi': gz or (gan + zhi)}

    def _map_liuyue_item(item):
        gz = item.get('gan_zhi') or ''
        gan = item.get('gan') or gz[:1]
        zhi = item.get('zhi') or gz[1:2]
        return {
            'jieqi': item.get('jieqi', ''),
            'date': item.get('date', ''),
            'month_name': item.get('month_name', ''),
            'tg': gan,
            'tgSs': _ss_name(item.get('shi_shen_gan') or (calc_shi_shen_for_gan(day_master, gan) if day_master and gan else '')),
            'dz': zhi,
            'dzSs': '',
            'gan_zhi': gz or (gan + zhi),
            'shensha': item.get('shen_sha', []),
        }

    def _relation_text(rel, keys):
        parts = []
        for key in keys:
            for item in rel.get(key, []) or []:
                desc = item.get('desc') if isinstance(item, dict) else str(item)
                if desc:
                    parts.append(desc)
        return '、'.join(parts)

    def _uniq(parts):
        seen = set()
        out = []
        for part in parts:
            if part and part not in seen:
                seen.add(part)
                out.append(part)
        return out

    def _relation_label_text(desc):
        text = re.sub(r'\s+', '', str(desc or ''))
        if not text:
            return ''
        text = re.sub(r'[（(]缺[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]+[）)]', '', text)
        text = re.sub(r'缺[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]+', '', text)
        chars = ''.join(re.findall(r'[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]', text))
        pair = chars[:2]
        he_pair_order = {
            frozenset({'甲', '己'}): '甲己',
            frozenset({'乙', '庚'}): '乙庚',
            frozenset({'丙', '辛'}): '丙辛',
            frozenset({'丁', '壬'}): '丁壬',
            frozenset({'戊', '癸'}): '戊癸',
        }
        relation_pair_order = {
            frozenset({'丑', '辰'}): '辰丑',
            frozenset({'酉', '戌'}): '酉戌',
            frozenset({'卯', '辰'}): '辰卯',
            frozenset({'卯', '午'}): '午卯',
            frozenset({'巳', '亥'}): '巳亥',
            frozenset({'辰', '戌'}): '辰戌',
            frozenset({'丑', '戌'}): '丑戌',
        }
        he_pair = he_pair_order.get(frozenset(pair), pair) if len(pair) == 2 else pair
        relation_pair = relation_pair_order.get(frozenset(pair), pair) if len(pair) == 2 else pair
        zhi_ju = {'子': '水局', '午': '火局', '卯': '木局', '酉': '金局'}
        hui_pair_ju = {
            frozenset({'寅', '辰'}): '木局',
            frozenset({'巳', '未'}): '火局',
            frozenset({'申', '戌'}): '金局',
            frozenset({'亥', '丑'}): '水局',
        }
        he_pair_ju = {
            frozenset({'申', '子'}): '水局',
            frozenset({'子', '辰'}): '水局',
            frozenset({'申', '辰'}): '水局',
            frozenset({'亥', '卯'}): '木局',
            frozenset({'卯', '未'}): '木局',
            frozenset({'亥', '未'}): '木局',
            frozenset({'寅', '午'}): '火局',
            frozenset({'午', '戌'}): '火局',
            frozenset({'寅', '戌'}): '火局',
            frozenset({'巳', '酉'}): '金局',
            frozenset({'酉', '丑'}): '金局',
            frozenset({'巳', '丑'}): '金局',
        }
        if '合化' in text:
            wx = re.search(r'合化([木火土金水])', text)
            return f'{he_pair}合化{wx.group(1)}' if pair and wx else text
        if '三会' in text:
            ju = re.search(r'三会([木火土金水]局)', text)
            return f'{chars[:3]}三会{ju.group(1)}' if len(chars) >= 3 and ju else text
        if '三合' in text:
            ju = re.search(r'三合([木火土金水]局)', text)
            return f'{chars[:3]}三合{ju.group(1)}' if len(chars) >= 3 and ju else text
        if '拱合' in text and pair:
            ju = re.search(r'拱合([木火土金水]局)', text)
            target = ju.group(1) if ju else (zhi_ju.get(chars[2]) if len(chars) >= 3 else he_pair_ju.get(frozenset(pair), ''))
            return f'{pair}拱合{target}' if target else f'{pair}拱合'
        if '拱会' in text and pair:
            ju = re.search(r'拱会([木火土金水]局)', text)
            target = ju.group(1) if ju else hui_pair_ju.get(frozenset(pair), '')
            return f'{pair}拱会{target}' if target else f'{pair}拱会'
        if '半合' in text and pair:
            ju = re.search(r'半合([木火土金水]局)', text)
            target = ju.group(1) if ju else he_pair_ju.get(frozenset(pair), '')
            return f'{pair}半合{target}' if target else f'{pair}半合'
        if '暗合' in text and pair:
            return f'{relation_pair}暗合'
        if '恃势之刑' in text or '无恩之刑' in text or '无礼之刑' in text or '三刑' in text:
            return f'{chars[:3]}三刑' if len(chars) >= 3 else f'{pair}刑'
        if '相刑' in text or '自刑' in text:
            return f'{relation_pair}自刑' if len(pair) == 2 and pair[0] == pair[1] else f'{relation_pair}刑'
        for old, new in [('相冲', '冲'), ('相害', '害'), ('相破', '破'), ('相合', '合'), ('相克', '克')]:
            if old in text and pair:
                return f'{relation_pair}{new}'
        for suffix in ['冲', '害', '破', '合', '克']:
            if text.endswith(suffix) and pair:
                return f'{relation_pair}{suffix}'
        return text.replace('相', '')

    def _reference_tg_guanxi(four_pillars, rel):
        pillars = ['year', 'month', 'day', 'hour']
        gans = [four_pillars.get(p, {}).get('gan', '') for p in pillars]
        gan_wx = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}
        gan_yinyang = {'甲': '阳', '丙': '阳', '戊': '阳', '庚': '阳', '壬': '阳', '乙': '阴', '丁': '阴', '己': '阴', '辛': '阴', '癸': '阴'}
        wx_ke = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
        gan_he_text = {
            frozenset({'甲', '己'}): '甲己合化土',
            frozenset({'乙', '庚'}): '乙庚合化金',
            frozenset({'丙', '辛'}): '丙辛合化水',
            frozenset({'丁', '壬'}): '丁壬合化木',
            frozenset({'戊', '癸'}): '戊癸合化火',
        }
        gan_he_pairs = set(gan_he_text.keys())
        parts = []
        for i in range(len(gans)):
            for j in range(i + 1, len(gans)):
                g1, g2 = gans[i], gans[j]
                pair = frozenset({g1, g2})
                if pair in gan_he_pairs:
                    continue
                wx1, wx2 = gan_wx.get(g1), gan_wx.get(g2)
                if not wx1 or not wx2:
                    continue
                if gan_yinyang.get(g1) != gan_yinyang.get(g2):
                    continue
                if g1 == '己' and g2 == '壬':
                    continue
                if wx_ke.get(wx1) == wx2:
                    parts.append(f'{g1}{g2}克')
                elif wx_ke.get(wx2) == wx1:
                    parts.append(f'{g2}{g1}克')
        for i in range(len(gans)):
            for j in range(i + 1, len(gans)):
                text = gan_he_text.get(frozenset({gans[i], gans[j]}))
                if text:
                    parts.append(text)
        parts.extend(_relation_label_text(p) for p in (_relation_text(rel, ['gan_chong']).replace('、', ',').split(',') if rel else []))
        return ','.join(_uniq([p for p in parts if p])) or '无合冲关系'

    def _reference_dz_guanxi(four_pillars, rel):
        pillars = ['year', 'month', 'day', 'hour']
        zhis = [four_pillars.get(p, {}).get('zhi', '') for p in pillars]
        parts = []
        liuhe = {
            frozenset({'子', '丑'}): '合化土', frozenset({'寅', '亥'}): '合化木',
            frozenset({'卯', '戌'}): '合化火', frozenset({'辰', '酉'}): '合化金',
            frozenset({'巳', '申'}): '合化水', frozenset({'午', '未'}): '合化土',
        }
        sanhe = [
            ({'申', '子', '辰'}, '水局', '子'),
            ({'亥', '卯', '未'}, '木局', '卯'),
            ({'寅', '午', '戌'}, '火局', '午'),
            ({'巳', '酉', '丑'}, '金局', '酉'),
        ]
        sanhui = [
            ({'寅', '卯', '辰'}, '木局', '卯'),
            ({'巳', '午', '未'}, '火局', '午'),
            ({'申', '酉', '戌'}, '金局', '酉'),
            ({'亥', '子', '丑'}, '水局', '子'),
        ]
        pair_order = {
            frozenset({'申', '子'}): '申子', frozenset({'子', '辰'}): '子辰', frozenset({'申', '辰'}): '申辰',
            frozenset({'亥', '卯'}): '亥卯', frozenset({'卯', '未'}): '卯未', frozenset({'亥', '未'}): '亥未',
            frozenset({'寅', '午'}): '寅午', frozenset({'午', '戌'}): '午戌', frozenset({'寅', '戌'}): '寅戌',
            frozenset({'巳', '酉'}): '巳酉', frozenset({'酉', '丑'}): '酉丑', frozenset({'巳', '丑'}): '巳丑',
            frozenset({'寅', '辰'}): '寅辰', frozenset({'亥', '丑'}): '亥丑', frozenset({'巳', '未'}): '巳未',
            frozenset({'申', '戌'}): '申戌',
        }
        relation_pair_order = {
            frozenset({'丑', '辰'}): '辰丑',
            frozenset({'酉', '戌'}): '酉戌',
            frozenset({'丑', '戌'}): '丑戌',
            frozenset({'辰', '戌'}): '辰戌',
            frozenset({'巳', '亥'}): '巳亥',
        }

        def _normalize_zhi_relation_desc(desc):
            if not desc or len(desc) < 4:
                return desc
            desc = desc.replace(' ', '')
            for z in ['子', '卯', '辰', '午', '酉', '亥']:
                if desc.startswith(z + z) and ('自刑' in desc or '刑' in desc):
                    return f'{z}{z}相刑'
            if '恃势之刑' in desc or '无恩之刑' in desc or '无礼之刑' in desc:
                return desc[:2] + '相刑'
            pair = frozenset({desc[0], desc[1]})
            ordered = relation_pair_order.get(pair)
            if ordered:
                return ordered + desc[2:]
            return desc

        def _add_dark_relations():
            dark_parts = []
            special_parts = []
            zhi_counts = {z: zhis.count(z) for z in set(zhis)}
            dark_order = ['子戌暗合', '子辰暗合', '子巳暗合', '丑寅暗合']
            dark_pairs = {
                frozenset({'子', '戌'}): dark_order[0],
                frozenset({'子', '辰'}): dark_order[1],
                frozenset({'子', '巳'}): dark_order[2],
                frozenset({'丑', '寅'}): dark_order[3],
            }
            for i in range(len(zhis)):
                for j in range(i + 1, len(zhis)):
                    z1, z2 = zhis[i], zhis[j]
                    if z1 == z2:
                        continue
                    pair = frozenset({z1, z2})
                    if pair in dark_pairs:
                        dark_parts.append(dark_pairs[pair])
                    if pair == frozenset({'巳', '丑'}) and zhi_counts.get('巳', 0) == 1 and '亥' in zhi_set:
                        special_parts.append('巳丑见辛暗合')
            ordered_dark = [item for item in dark_order if item in set(dark_parts)]
            return special_parts, ordered_dark

        zhi_set = set([z for z in zhis if z])
        full_sanhui_trios = set()
        for trio, ju, _mid in sanhui:
            if trio.issubset(zhi_set):
                full_sanhui_trios.add(frozenset(trio))
                ordered = {'木局': '寅卯辰', '火局': '巳午未', '金局': '申酉戌', '水局': '亥子丑'}[ju]
                parts.append(f'{ordered}三会{ju}')
        liuhe_parts = []
        sanhe_parts = []
        sanhui_parts = []
        for i in range(len(zhis)):
            for j in range(i + 1, len(zhis)):
                z1, z2 = zhis[i], zhis[j]
                if not z1 or not z2:
                    continue
                if z1 == z2:
                    continue
                pair = frozenset({z1, z2})
                if pair in liuhe:
                    liuhe_parts.append(f'{z1}{z2}{liuhe[pair]}')
                for trio, ju, mid in sanhe:
                    if pair.issubset(trio):
                        if z1 != z2:
                            label = pair_order.get(pair, f'{z1}{z2}')
                            if mid not in pair:
                                sanhe_parts.append(f'{label}拱合{ju}')
                            else:
                                sanhe_parts.append(f'{label}半合{ju}')
                for trio, _ju, mid in sanhui:
                    if pair.issubset(trio) and mid not in pair and frozenset(trio) not in full_sanhui_trios:
                        sanhui_parts.append(f'{pair_order.get(pair, f"{z1}{z2}")}拱会{_ju}')
        special_dark_parts, dark_parts = _add_dark_relations()
        parts.extend(liuhe_parts)
        parts.extend(special_dark_parts)
        parts.extend(sanhe_parts)
        parts.extend(dark_parts)
        parts.extend(sanhui_parts)
        if rel:
            parts.extend(_relation_label_text(_normalize_zhi_relation_desc(p)) for p in _relation_text(rel, ['zhi_an_he', 'zhi_san_xing', 'zhi_liu_chong', 'zhi_liu_hai', 'zhi_liu_po']).replace('、', ',').split(','))
        return ','.join(_uniq([p for p in parts if p]))

    tai_ming = local_result.get('tai_ming_shen') or {}
    tai_yuan = tai_ming.get('tai_yuan') or {}
    ming_gong = tai_ming.get('ming_gong') or {}
    shen_gong = tai_ming.get('shen_gong') or {}
    kong_wang = ''.join(local_result.get('kong_wang') or [])
    rel = local_result.get('ganzhi_relations') or {}
    four_pillars = local_result.get('four_pillars') or {}
    qi_yun_detail = local_result.get('qi_yun_detail') or {}

    return {
        'success': True,
        'source': 'shian-local-bazi',
        'name': local_result.get('name') or f'案例{year}',
        'shengxiao': local_result.get('sheng_xiao', ''),
        'gender_label': '乾造' if sex == 1 else '坤造',
        'lunar_date': local_result.get('birth_lunar', ''),
        'solar_date': f'{year}年{month:02d}月{day:02d}日 {hour:02d}:{minute:02d}',
        'qiyun_info': qi_yun_detail.get('text', ''),
        'jiaoyun_text': qi_yun_detail.get('jiao_yun_text', ''),
        'jiaoyun_info': f"胎元{tai_yuan.get('gan_zhi', '')} 命宫{ming_gong.get('gan_zhi', '')} 身宫{shen_gong.get('gan_zhi', '')} 空亡({kong_wang})",
        'tg_guanxi': _reference_tg_guanxi(four_pillars, rel),
        'dz_guanxi': _reference_dz_guanxi(four_pillars, rel),
        'sizhu': {key: _pillar_item(key) for key in ['year', 'month', 'day', 'hour']},
        'dayun_list': [_map_yun_item(item) for item in local_result.get('da_yun', [])],
        'dayun_details': [],
        'liunian_list': [_map_liunian_item(item) for item in local_result.get('liu_nian', [])],
        'xiaoyun_list': [_map_xiaoyun_item(item) for item in local_result.get('xiao_yun', [])],
        'liuyue_list': [_map_liuyue_item(item) for item in local_result.get('liu_yue', [])],
        'wuxing_wangdu': {},
        'wuxing_count': local_result.get('wu_xing', {}),
        'taiyuan': tai_yuan.get('gan_zhi', ''),
        'taixi': (local_result.get('tai_xi') or {}).get('gan_zhi', ''),
        'minggong': ming_gong.get('gan_zhi', ''),
        'shenggong': shen_gong.get('gan_zhi', ''),
        'kongwang': kong_wang,
        'cheng_gu': local_result.get('cheng_gu') or {},
        'day_master': day_master,
        'birth_params': {'y': year, 'm': month, 'd': day, 'h': hour, 'mi': minute, 's': sex},
        'current_age_xu': datetime.now().year - year + 1,
        'qi_yun_age': local_result.get('qi_yun_age'),
        'qi_yun_detail': qi_yun_detail,
    }

@app.route('/api/bazi/shian-pro')
def api_bazi_shian_pro():
    """时安八字专业细盘 API。

    使用时安本地算法生成专业盘兼容结构；当前发行版不内置第三方排盘接口。
    """
    try:
        year = int(request.args.get("y", 0))
        month = int(request.args.get("m", 0))
        day = int(request.args.get("d", 0))
        hour = int(request.args.get("h", 0))
        minute = int(request.args.get("mi", 0))
        sex = int(request.args.get("s", 1))
    except (ValueError, TypeError):
        return jsonify({"success": False, "error": "参数格式错误"}), 400

    if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23):
        return jsonify({"success": False, "error": "日期范围错误"}), 400

    gender = "男" if sex == 1 else "女"
    birth_time = f"{year:04d}{month:02d}{day:02d}{hour:02d}{minute:02d}"
    use_solar_time_raw = str(request.args.get("useSolarTime", request.args.get("use_solar_time", "0"))).strip().lower()
    use_solar_time = use_solar_time_raw in ("1", "true", "yes", "on")
    birth_addr = request.args.get("birthAddr") or request.args.get("birth_addr") or ""
    longitude = request.args.get("lng", request.args.get("longitude", request.args.get("birthLng", "")))
    try:
        longitude = float(longitude) if longitude not in ("", None) else None
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "经度参数格式错误"}), 400

    jy_raw = (request.args.get("jy") or "").strip()
    jy_dt = None
    if jy_raw:
        jy_match = re.fullmatch(r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})", jy_raw)
        if not jy_match:
            return jsonify({"success": False, "error": "交运时间参数格式错误"}), 400
        try:
            jy_dt = datetime(
                int(jy_match.group(1)),
                int(jy_match.group(2)),
                int(jy_match.group(3)),
                int(jy_match.group(4)),
                int(jy_match.group(5)),
            )
        except ValueError:
            return jsonify({"success": False, "error": "交运时间参数范围错误"}), 400

    from bazi_engine import calc_qi_yun_detail, paipan as bazi_paipan

    local_result = bazi_paipan(
        name=f"案例{year}",
        gender=gender,
        birth_time=birth_time,
        cal_type="公历",
        birth_addr=birth_addr,
        use_solar_time=use_solar_time,
        longitude=longitude,
    )
    if not local_result.get("success"):
        return jsonify({"success": False, "error": local_result.get("error") or "本地专业盘生成失败"}), 500

    if jy_dt is not None:
        qi_yun_detail = dict(local_result.get("qi_yun_detail") or {})
        jy_detail = calc_qi_yun_detail(jy_dt, {}, local_result.get("four_pillars") or {}, gender)
        if jy_detail.get("jiao_yun_text"):
            qi_yun_detail["jiao_yun_text"] = jy_detail["jiao_yun_text"]
            local_result["qi_yun_detail"] = qi_yun_detail

    resp = jsonify(_build_local_bazi_pro_payload(local_result, year, month, day, hour, minute, sex))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp

def _calc_ganzhi_relations_gan(gans):
    """计算天干关系（合、冲、克）"""
    GAN_HE = [('甲','己','土'),('乙','庚','金'),('丙','辛','水'),('丁','壬','木'),('戊','癸','火')]
    GAN_CHONG = [('甲','庚'),('乙','辛'),('丙','壬'),('丁','癸')]
    GAN_KE = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
    GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    GAN_YINYANG = {'甲':'阳','丙':'阳','戊':'阳','庚':'阳','壬':'阳','乙':'阴','丁':'阴','己':'阴','辛':'阴','癸':'阴'}
    GAN_HE_ORDER = {
        frozenset({'甲', '己'}): '甲己',
        frozenset({'乙', '庚'}): '乙庚',
        frozenset({'丙', '辛'}): '丙辛',
        frozenset({'丁', '壬'}): '丁壬',
        frozenset({'戊', '癸'}): '戊癸',
    }
    rels = []
    for i in range(len(gans)):
        for j in range(i+1, len(gans)):
            g1, g2 = gans[i], gans[j]
            if not g1 or not g2: continue
            he_pair = False
            for a, b, name in GAN_HE:
                if (g1==a and g2==b) or (g1==b and g2==a):
                    rels.append(f'{GAN_HE_ORDER[frozenset({g1, g2})]}合化{name}')
                    he_pair = True
            for a, b in GAN_CHONG:
                if (g1==a and g2==b) or (g1==b and g2==a):
                    rels.append(f'{g1}{g2}冲')
            if he_pair or GAN_YINYANG.get(g1) != GAN_YINYANG.get(g2):
                continue
            wx1, wx2 = GAN_WX.get(g1,''), GAN_WX.get(g2,'')
            if wx1 and wx2 and GAN_KE.get(wx1)==wx2:
                rels.append(f'{g1}{g2}克')
            elif wx1 and wx2 and GAN_KE.get(wx2)==wx1:
                rels.append(f'{g2}{g1}克')
    return ', '.join(rels)


def _build_qiyun_info(qi_yun_age, qiyun_detail, birth_year, birth_month, birth_day, qiyun_duration=None):
    """构建起运信息字符串，包含详细的起运时间

    Args:
        qi_yun_age: 起运虚岁
        qiyun_detail: 起运日期详情 dict(year, month, day, hour, minute) 或空
        birth_year/month/day: 出生日期
        qiyun_duration: 起运时长 dict(years, months, days) 或空

    Returns:
        str: 如 "出生后7年4个月15天起运  起运时间:1997年10月15日"
    """
    if not qi_yun_age:
        return ''

    # 优先使用传统方法计算的起运时长
    # 格式对齐参考口径：只显示非零部分，hours始终为0（已转换为天）不显示
    if qiyun_duration:
        y = qiyun_duration.get('years', 0)
        m = qiyun_duration.get('months', 0)
        d = qiyun_duration.get('days', 0)
        # hours始终为0，不显示"0时"
        dp = []
        if y: dp.append(f'{y}年')
        if m: dp.append(f'{m}月')
        if d: dp.append(f'{d}天')
        duration_str = ''.join(dp) if dp else '0天'
    else:
        duration_str = f'{qi_yun_age}岁'

    parts = [f'出生后{duration_str}起运']

    # 如果有详细的起运日期，补充具体信息
    if qiyun_detail and qiyun_detail.get('year'):
        qy = qiyun_detail['year']
        qm = qiyun_detail.get('month', 0)
        qd = qiyun_detail.get('day', 0)
        if qy > 1900 and qy < 2200:
            parts.append(f'起运时间:{qy}年{qm}月{qd}日')
    else:
        # 没有详细起运日期，从虚岁推算起运年份
        qiyun_year = birth_year + qi_yun_age - 1
        parts.append(f'约{qiyun_year}年起运')

    return '  '.join(parts)


def _calc_ganzhi_relations_zhi(zhis):
    """计算地支关系（冲、合、刑、害、半合、暗合、三会）"""
    ZHI_LIUHE = [('子','丑','土'),('寅','亥','木'),('卯','戌','火'),('辰','酉','金'),('巳','申','水'),('午','未','土')]
    ZHI_CHONG = [('子','午'),('丑','未'),('寅','申'),('卯','酉'),('辰','戌'),('巳','亥')]
    ZHI_XING = [('寅','巳'),('丑','戌'),('子','卯'),('辰','辰'),('午','午'),('酉','酉'),('亥','亥')]
    ZHI_HAI = [('子','未'),('丑','午'),('寅','巳'),('卯','辰'),('申','亥'),('酉','戌')]
    RELATION_PAIR_ORDER = {
        frozenset({'丑', '辰'}): '辰丑',
        frozenset({'酉', '戌'}): '酉戌',
        frozenset({'卯', '辰'}): '辰卯',
        frozenset({'卯', '午'}): '午卯',
        frozenset({'巳', '亥'}): '巳亥',
        frozenset({'辰', '戌'}): '辰戌',
        frozenset({'丑', '戌'}): '丑戌',
    }
    def _pair_text(z1, z2):
        return RELATION_PAIR_ORDER.get(frozenset({z1, z2}), f'{z1}{z2}')
    # 半合
    ZHI_BANHE = [
        ('申','子','半合水局'),('子','辰','半合水局'),('申','辰','拱合水局'),
        ('亥','卯','半合木局'),('卯','未','半合木局'),('亥','未','拱合木局'),
        ('寅','午','半合火局'),('午','戌','半合火局'),('寅','戌','拱合火局'),
        ('巳','酉','半合金局'),('酉','丑','半合金局'),('巳','丑','拱合金局'),
    ]
    # 暗合
    ZHI_ANHE = [('寅','丑'),('巳','酉'),('午','亥')]
    # 三会
    ZHI_SANHUI = [
        ({'寅','卯','辰'}, '木局', '卯'),
        ({'巳','午','未'}, '火局', '午'),
        ({'申','酉','戌'}, '金局', '酉'),
        ({'亥','子','丑'}, '水局', '子'),
    ]

    zhi_set = set(z for z in zhis if z)
    rels = []
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            z1, z2 = zhis[i], zhis[j]
            if not z1 or not z2: continue
            pair_text = _pair_text(z1, z2)
            for a, b, wx in ZHI_LIUHE:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{pair_text}合化{wx}')
            for a, b in ZHI_CHONG:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{pair_text}冲')
            for a, b in ZHI_XING:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{pair_text}自刑' if z1 == z2 else f'{pair_text}刑')
            for a, b in ZHI_HAI:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{pair_text}害')
            for a, b, desc in ZHI_BANHE:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    # 检查对应三合局是否已完整（三合优先级更高）
                    skip = False
                    if '金水局' in desc:
                        if {'申','子','辰'}.issubset(zhi_set): skip = True
                    elif '木局' in desc:
                        if {'亥','卯','未'}.issubset(zhi_set): skip = True
                    elif '火局' in desc:
                        if {'寅','午','戌'}.issubset(zhi_set): skip = True
                    elif '金局' in desc:
                        if {'巳','酉','丑'}.issubset(zhi_set): skip = True
                    if not skip:
                        rels.append(f'{pair_text}{desc}')
            for a, b in ZHI_ANHE:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{pair_text}暗合')
            # 六破
            ZHI_PO = [('子','酉'),('丑','辰'),('寅','亥'),('卯','午'),('巳','申'),('未','戌')]
            for a, b in ZHI_PO:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{pair_text}破')

    # 三会局（需要至少2个地支）
    for trio, ju, mid in ZHI_SANHUI:
        present = trio & zhi_set
        if len(present) >= 2:
            involved = [z for z in zhis if z in trio]
            if len(present) == 3:
                rels.append(f'{"".join(involved)}三会{ju}')
            elif mid not in present:
                rels.append(f'{"".join(involved)}拱会{ju}')

    return ', '.join(rels)


# ═══════════════════════════════════════════════════════════════
# 黄历万年历 API（外部接口 + 本地 fallback）
# ═══════════════════════════════════════════════════════════════

# 内存缓存：{date_str: (data_dict, expire_timestamp)} + {month_key: data}
_huangli_cache = {}
_huangli_month_cache = {}  # 'YYYY-MM': data
_HUANGLI_CACHE_TTL = 3600 * 6  # 6 小时缓存
_HUANGLI_MONTH_TTL = 3600 * 2  # 整月缓存 2 小时


def _fetch_huangli_from_api(year, month, day):
    """从 36jxs 免费黄历 API 获取精确数据（含宜忌、干支、纳音等）"""
    import urllib.request, urllib.error

    date_str = f'{year}-{month:02d}-{day:02d}'

    # 检查缓存
    now = time.time()
    cached = _huangli_cache.get(date_str)
    if cached and cached[1] > now:
        return cached[0]

    url = f'https://www.36jxs.com/api/Commonweal/almanac?sun={date_str}'
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'XuanCeTai/5.0 (macOS; Huangli)',
            'Accept': 'application/json',
        })
        with urllib.request.urlopen(req, timeout=5) as resp:
            raw = json.loads(resp.read().decode('utf-8'))

        if raw.get('code') != 1 or 'data' not in raw:
            return None

        d = raw['data']

        # 五行颜色映射
        wx_color_map = {'金': '#DAA520', '木': '#228B22', '水': '#4169E1', '火': '#DC143C', '土': '#8B4513'}

        # 解析农历月日
        ldt = d.get('LunarDateTime', '').split('-')
        lunar_month = int(ldt[1]) if len(ldt) >= 2 else 0
        lunar_day = int(ldt[2]) if len(ldt) >= 3 else 0

        # 日名映射
        day_name_map = {1: '初一', 2: '初二', 3: '初三', 4: '初四', 5: '初五',
                        6: '初六', 7: '初七', 8: '初八', 9: '初九', 10: '初十',
                        11: '十一', 12: '十二', 13: '十三', 14: '十四', 15: '十五',
                        16: '十六', 17: '十七', 18: '十八', 19: '十九', 20: '二十',
                        21: '廿一', 22: '廿二', 23: '廿三', 24: '廿四', 25: '廿五',
                        26: '廿六', 27: '廿七', 28: '廿八', 29: '廿九', 30: '三十'}

        # 日支五行
        wu_xing_map = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                       '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
                       '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火',
                       '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水'}
        gan_zhi_day = d.get('TianGanDiZhiDay', '')
        ri_zhi = gan_zhi_day[1] if len(gan_zhi_day) >= 2 else ''
        wu_xing_day = wu_xing_map.get(ri_zhi, '')

        result = {
            'solarDate': date_str,
            'source': 'api',
            # 农历
            'lunarDate': d.get('LunarDateTime', ''),
            'lunarYear': int(ldt[0]) if len(ldt) >= 1 else 0,
            'lunarMonth': lunar_month,
            'lunarDay': lunar_day,
            'isLeap': False,
            'lunarDayName': d.get('LDay', day_name_map.get(lunar_day, str(lunar_day))),
            'lunarMonthName': d.get('LMonth', ''),
            'lunarDisplay': d.get('LMonth', '') if lunar_day == 1 else d.get('LDay', day_name_map.get(lunar_day, '')),
            # 干支
            'ganZhiYear': d.get('TianGanDiZhiYear', '') + '年',
            'ganZhiMonth': d.get('TianGanDiZhiMonth', ''),
            'ganZhiDay': d.get('TianGanDiZhiDay', ''),
            # 生肖
            'shengXiao': d.get('LYear', ''),
            # 五行
            'wuXingDay': wu_xing_day,
            'wuXingColor': wx_color_map.get(wu_xing_day, '#888'),
            'naYin': d.get('WuxingNaDay', ''),
            'naYinYear': d.get('WuxingNaYear', ''),
            'naYinMonth': d.get('WuxingNaMonth', ''),
            # 建除
            'jianChu': d.get('JianShen', ''),
            # 冲煞
            'chong': d.get('Chong', ''),
            'sha': d.get('SuiSha', ''),
            # 值神（从 ShenWei 解析）
            'zhiShen': d.get('JianShen', ''),
            # 宜忌
            'yi': d.get('Yi', ''),
            'ji': d.get('Ji', ''),
            # 彭祖百忌
            'pengZu': d.get('PengZu', ''),
            # 喜神/福神/财神
            'shenWei': d.get('ShenWei', ''),
            # 胎神
            'taiShen': d.get('Taishen', ''),
            # 星宿
            'xingEast': d.get('XingEast', ''),
            'xingWest': d.get('XingWest', ''),
            # 月相
            'moonName': d.get('MoonName', ''),
            # 节气
            'solarTerm': d.get('SolarTermName', ''),
            # 节日
            'gJie': d.get('GJie', ''),
            'lJie': d.get('LJie', ''),
            # 星期
            'weekday': ['日', '一', '二', '三', '四', '五', '六'][datetime(year, month, day).weekday() % 7],
            'disclaimer': '以上内容仅为民俗文化参考，不构成任何决策建议',
        }

        # 写入缓存
        _huangli_cache[date_str] = (result, now + _HUANGLI_CACHE_TTL)
        return result

    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, KeyError, Exception) as e:
        logger.error(f'[黄历API] 获取失败 {date_str}: {e}')
        return None


def _fetch_huangli_and_merge(year, month, day):
    """后台线程：从 API 获取黄历数据并与本地计算结果合并，更新缓存"""
    date_str = f'{year}-{month:02d}-{day:02d}'
    try:
        api_data = _fetch_huangli_from_api(year, month, day)
        if not api_data:
            return
        local_data = _compute_huangli_local(year, month, day)
        merged = dict(local_data)
        for k, v in api_data.items():
            if k == 'source':
                continue
            if k in ('yi', 'ji', 'pengZu', 'shenWei') and v:
                merged[k] = v
            elif k not in merged or not merged[k]:
                merged[k] = v
        merged['source'] = 'local+api'
        now = time.time()
        _huangli_cache[date_str] = (merged, now + _HUANGLI_CACHE_TTL)
    except Exception as e:
        logger.debug(f'[黄历] 后台合并失败 {date_str}: {e}')


def _compute_huangli(year, month, day):
    """计算单日黄历数据 — 先用本地计算（快），后台尝试用API补充丰富数据"""
    # ===== 本地计算（<50ms/天） =====
    result = _compute_huangli_local(year, month, day)

    # ===== 后台尝试API补充（不阻塞主流程） =====
    if not _huangli_cache.get(f'{year}-{month:02d}-{day:02d}'):
        import threading as _t
        _t.Thread(target=_fetch_huangli_and_merge, args=(year, month, day), daemon=True).start()

    return result


def _compute_huangli_local(year, month, day):
    """纯本地计算黄历数据（快速，不依赖外部API）"""
    result = {'solarDate': f'{year}-{month:02d}-{day:02d}', 'source': 'local'}

    # ===== 基础农历 =====
    if HAS_LUNAR:
        try:
            from lunarcalendar import Lunar, Converter, Solar
            solar = Solar(year, month, day)
            lunar = Converter.Solar2Lunar(solar)
            result['lunarDate'] = f'{lunar.year}年{lunar.month}月{lunar.day}日'
            result['lunarYear'] = lunar.year
            result['lunarMonth'] = lunar.month
            result['lunarDay'] = lunar.day
            result['isLeap'] = lunar.isleap
        except Exception as e:
            result['lunarError'] = str(e)
    else:
        result['lunarError'] = 'LunarCalendar 库未安装'

    # ===== 天干地支 =====
    gan_list = ['甲','乙','丙','丁','戊','己','庚','辛','壬','癸']
    zhi_list = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
    sx_list = ['鼠','牛','虎','兔','龙','蛇','马','羊','猴','鸡','狗','猪']

    # 年干支
    g_idx_y = (year - 4) % 10
    z_idx_y = (year - 4) % 12
    result['ganZhiYear'] = gan_list[g_idx_y] + zhi_list[z_idx_y] + '年'
    result['shengXiao'] = sx_list[z_idx_y]

    # 日干支（基于儒略日计算）
    # 以 2024-01-01 = 甲子日 为基准 (甲=0, 子=0)，API已验证
    from datetime import date as dt_date
    base = dt_date(2024, 1, 1)
    target = dt_date(year, month, day)
    delta = (target - base).days
    g_idx_d = (0 + delta) % 10
    z_idx_d = (0 + delta) % 12
    result['ganZhiDay'] = gan_list[g_idx_d] + zhi_list[z_idx_d]

    # 月干支（年上起月法）
    # 甲己之年丙作首，乙庚之岁戊为头，丙辛必定寻庚起，丁壬壬位顺行流，戊癸何方发，甲寅之上好追求
    lunar_month = result.get('lunarMonth', month)
    yin_offset = (lunar_month - 1) if lunar_month >= 1 else 0
    z_idx_m = (yin_offset + 2) % 12  # 正月=寅
    g_idx_m = (g_idx_y * 2 + 2 + yin_offset) % 10
    result['ganZhiMonth'] = gan_list[g_idx_m] + zhi_list[z_idx_m]

    # ===== 五行 =====
    # 日干对应五行
    wu_xing_gan = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土',
                   '己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    wu_xing_zhi = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火',
                   '午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
    ri_gan = gan_list[g_idx_d]
    ri_zhi = zhi_list[z_idx_d]
    result['wuXingDay'] = wu_xing_zhi[ri_zhi]  # 日支五行
    result['wuXingZhi'] = wu_xing_zhi[ri_zhi]   # 日支五行

    # 纳音五行（简化：60甲子纳音表）
    na_yin_table = [
        '海中金','海中金','炉中火','炉中火','大林木','大林木',
        '路旁土','路旁土','剑锋金','剑锋金','山头火','山头火',
        '涧下水','涧下水','城头土','城头土','白蜡金','白蜡金',
        '杨柳木','杨柳木','泉中水','泉中水','屋上土','屋上土',
        '霹雳火','霹雳火','松柏木','松柏木','长流水','长流水',
        '砂石金','砂石金','山下火','山下火','平地木','平地木',
        '壁上土','壁上土','金箔金','金箔金','覆灯火','覆灯火',
        '天河水','天河水','大驿土','大驿土','钗钏金','钗钏金',
        '桑柘木','桑柘木','大溪水','大溪水','沙中土','沙中土',
        '天上火','天上火','石榴木','石榴木','大海水','大海水',
    ]
    jiazi_idx = (g_idx_d * 6 + z_idx_d // 2) % 30
    # 更精确的纳音索引
    na_yin_idx = (g_idx_d % 5 * 12 + z_idx_d) // 2
    na_yin_idx = min(na_yin_idx, 29)
    result['naYin'] = na_yin_table[na_yin_idx]

    # ===== 建除十二神 =====
    # 基于日支与月支的关系推算
    yue_zhi_idx = z_idx_m  # 月支索引
    jian_chu_list = ['建','除','满','平','定','执','破','危','成','收','开','闭']
    offset = (z_idx_d - yue_zhi_idx) % 12
    result['jianChu'] = jian_chu_list[offset]

    # ===== 冲煞 =====
    # 六冲：子午冲、丑未冲、寅申冲、卯酉冲、辰戌冲、巳亥冲
    chong_map = {0:6, 1:7, 2:8, 3:9, 4:10, 5:11, 6:0, 7:1, 8:2, 9:3, 10:4, 11:5}
    chong_zhi = zhi_list[chong_map[z_idx_d]]
    chong_sx = sx_list[chong_map[z_idx_d]]
    # 煞方
    sha_map = {0:'南',1:'东',2:'北',3:'西',4:'南',5:'东',
               6:'北',7:'西',8:'南',9:'东',10:'北',11:'西'}
    result['chong'] = f'冲{chong_sx}({chong_zhi})'
    result['sha'] = f'煞{sha_map[z_idx_d]}'

    # ===== 值神（简化版：12值神循环） =====
    zhi_shen_list = ['青龙','明堂','天刑','朱雀','金匮','天德',
                     '白虎','玉堂','天牢','玄武','司命','勾陈']
    result['zhiShen'] = zhi_shen_list[z_idx_d]

    # ===== 星期 =====
    result['weekday'] = ['日','一','二','三','四','五','六'][dt_date(year, month, day).weekday() % 7]

    # ===== 农历日名美化 =====
    lunar_day = result.get('lunarDay', 0)
    lunar_month_val = result.get('lunarMonth', 0)
    day_name_map = {1:'初一',2:'初二',3:'初三',4:'初四',5:'初五',
                    6:'初六',7:'初七',8:'初八',9:'初九',10:'初十',
                    11:'十一',12:'十二',13:'十三',14:'十四',15:'十五',
                    16:'十六',17:'十七',18:'十八',19:'十九',20:'二十',
                    21:'廿一',22:'廿二',23:'廿三',24:'廿四',25:'廿五',
                    26:'廿六',27:'廿七',28:'廿八',29:'廿九',30:'三十'}
    month_name_map = {1:'正月',2:'二月',3:'三月',4:'四月',5:'五月',6:'六月',
                      7:'七月',8:'八月',9:'九月',10:'十月',11:'冬月',12:'腊月'}
    result['lunarDayName'] = day_name_map.get(lunar_day, str(lunar_day))
    result['lunarMonthName'] = month_name_map.get(lunar_month_val, str(lunar_month_val))

    # 初一显示月名
    if lunar_day == 1:
        result['lunarDisplay'] = result['lunarMonthName']
    else:
        result['lunarDisplay'] = result['lunarDayName']

    # ===== 五行颜色 =====
    wx_color_map = {'金':'#DAA520','木':'#228B22','水':'#4169E1','火':'#DC143C','土':'#8B4513'}
    result['wuXingColor'] = wx_color_map.get(result['wuXingDay'], '#888')

    # ===== 补充 API 版本才有的字段（fallback 留空） =====
    result.setdefault('yi', '')
    result.setdefault('ji', '')
    result.setdefault('pengZu', '')
    result.setdefault('shenWei', '')
    result.setdefault('taiShen', '')
    result.setdefault('xingEast', '')
    result.setdefault('xingWest', '')
    result.setdefault('moonName', '')
    result.setdefault('solarTerm', '')
    result.setdefault('gJie', '')
    result.setdefault('lJie', '')
    result.setdefault('naYinYear', '')
    result.setdefault('naYinMonth', '')

    result['disclaimer'] = '以上内容仅为民俗文化参考，不构成任何决策建议'
    return result


# ═══════════════════════════════════════════════════════════════
# 择吉 API
# ═══════════════════════════════════════════════════════════════

_ZEJI_GOOD_JIANCHU = {
    '婚嫁': {'成', '开', '定'},
    '开业': {'开', '成', '满'},
    '搬家': {'成', '开', '定'},
    '出行': {'开', '成', '除'},
    '签约': {'成', '定', '开'},
    '动土': {'成', '开', '定'},
}
_ZEJI_BAD_JIANCHU = {'破', '闭', '危'}
_ZEJI_GOOD_ZHISHEN = {'青龙', '明堂', '金匮', '天德', '玉堂', '司命'}


def _parse_zeji_date(value, field_name):
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except (TypeError, ValueError):
        raise ValueError(f'{field_name}格式错误，需YYYY-MM-DD')


def _score_zeji_day(zeji_type, huangli):
    score = 60
    reasons = []
    warnings = []

    jian_chu = huangli.get('jianChu', '')
    zhi_shen = huangli.get('zhiShen', '')
    yi = huangli.get('yi', '') or ''
    ji = huangli.get('ji', '') or ''

    if jian_chu in _ZEJI_GOOD_JIANCHU.get(zeji_type, {'成', '开', '定'}):
        score += 18
        reasons.append(f'{jian_chu}日利于推进事项')
    elif jian_chu in _ZEJI_BAD_JIANCHU:
        score -= 18
        warnings.append(f'{jian_chu}日宜谨慎')
    else:
        reasons.append(f'{jian_chu}日中平')

    if zhi_shen in _ZEJI_GOOD_ZHISHEN:
        score += 10
        reasons.append(f'值神{zhi_shen}为吉神')
    elif zhi_shen:
        warnings.append(f'值神{zhi_shen}，需结合实际安排')

    if zeji_type and zeji_type in yi:
        score += 12
        reasons.append(f'黄历宜项包含{zeji_type}')
    if zeji_type and zeji_type in ji:
        score -= 20
        warnings.append(f'黄历忌项包含{zeji_type}')

    return max(0, min(100, score)), reasons, warnings


def record_admin_audit(action, target_type, target_id=None, detail=None):
    """记录管理员写操作，随外层事务一起提交。"""
    payload = detail or {}
    try:
        detail_text = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    except TypeError:
        detail_text = json.dumps({'detail': str(payload)}, ensure_ascii=False)
    log = AdminAuditLog(
        admin_id=current_user.id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        detail=detail_text,
        ip_address=request.headers.get('X-Forwarded-For', request.remote_addr or '').split(',')[0].strip(),
    )
    db.session.add(log)
    return log


# ═══════════════════════════════════════════════════════════════
# 商业化与会员体系 API
# ═══════════════════════════════════════════════════════════════

def check_tool_limit(user):
    """检查用户当日工具使用次数，返回 (allowed, current_count, limit)"""
    today = datetime.utcnow().strftime('%Y-%m-%d')
    if user.last_tool_date != today:
        user.daily_tool_count = 0
        user.last_tool_date = today
        db.session.commit()

    m = get_or_create_membership(user.id)
    limit = MEMBER_TOOL_LIMIT.get(m.level, 3)
    if limit == -1:
        return True, user.daily_tool_count, limit
    return user.daily_tool_count < limit, user.daily_tool_count, limit

from admin_routes import register_admin_routes
from auth_channel_routes import _check_code, _check_rate_limit, _store_code, register_auth_channel_routes
from auth_routes import register_auth_routes
from bazi_history_routes import register_bazi_history_routes
from bazi_ask_routes import register_bazi_ask_routes
from bazi_routes import register_bazi_routes
from calendar_routes import register_calendar_routes
from community_routes import register_community_routes
from comprehensive_routes import register_comprehensive_routes
from media_routes import allowed_file, register_media_routes, validate_image_upload
from metaphysics_ask_routes import register_metaphysics_ask_routes
from metaphysics_routes import register_metaphysics_routes
from ops_routes import register_ops_routes
from paid_content_routes import register_paid_content_routes
from points_routes import register_points_routes
from profile_routes import register_profile_routes, sync_bazi_record_to_profile
from qimen_ask_routes import register_qimen_ask_routes
from recharge_routes import (
    RECHARGE_PACKAGES,
    _payment_text_matches_receiver,
    make_confirm_recharge_order_once,
    register_recharge_routes,
)
from tool_run_routes import register_tool_run_routes
from user_content_routes import register_user_content_routes
from ziwei_ask_routes import register_ziwei_ask_routes
from ziwei_routes import register_ziwei_routes

_build_one_tool = None
confirm_recharge_order_once = make_confirm_recharge_order_once(db, get_or_create_membership, add_points)
register_ops_routes(app)
register_auth_routes(app, db, {
    'check_rate_limit': _check_rate_limit,
    'check_code': _check_code,
})
register_auth_channel_routes(app, db, logger)
register_bazi_routes(app, db, {
    'Record': Record,
    'BaziRecord': BaziRecord,
    'lunar_to_solar': lunar_to_solar,
    'sync_bazi_record_to_profile': sync_bazi_record_to_profile,
    'paipan_dir': PAIPAN_DIR,
    'paipan_sh': PAIPAN_SH,
    'has_lunar': HAS_LUNAR,
    'logger': logger,
})
register_bazi_ask_routes(app, db, {
    'get_run_dir': get_run_dir,
    'write_run_status': write_run_status,
    'read_run_status': read_run_status,
    'logger': logger,
})
register_bazi_history_routes(app, db)
register_profile_routes(app, db)
register_points_routes(app, db, {
    'get_or_create_membership': get_or_create_membership,
    'create_daily_sign_in_once': create_daily_sign_in_once,
    'use_points': use_points,
})
register_calendar_routes(app, {
    'compute_huangli': _compute_huangli,
    'compute_huangli_local': _compute_huangli_local,
    'score_zeji_day': _score_zeji_day,
    'huangli_month_cache': _huangli_month_cache,
    'huangli_month_ttl': _HUANGLI_MONTH_TTL,
})
register_recharge_routes(app, db, {
    'confirm_recharge_order_once': confirm_recharge_order_once,
    'validate_image_upload': validate_image_upload,
})
register_community_routes(app, db, {
    'allowed_file': allowed_file,
})
register_media_routes(app, db, {
    'Record': Record,
    'logger': logger,
})
register_comprehensive_routes(app, db, {
    'get_or_create_membership': get_or_create_membership,
    'spend_ai_quota_once': spend_ai_quota_once,
    'refund_ai_quota_once': refund_ai_quota_once,
    'qimen_paipan': _qimen_paipan,
    'liuyao_paipan': _liuyao_paipan,
    'meihua_paipan': _meihua_paipan,
    'tarot_draw': _tarot_draw,
    'compute_huangli_local': _compute_huangli_local,
    'score_zeji_day': _score_zeji_day,
    'ziwei_engine': _zw_engine,
    'has_ziwei': HAS_ZIWEI,
    'logger': logger,
    'get_build_one_tool_override': lambda: _build_one_tool if callable(_build_one_tool) else None,
    'get_reading_stream': lambda: get_reading_stream,
    'get_chat_completion': get_chat_completion,
})
register_ziwei_routes(app, {
    'has_ziwei': HAS_ZIWEI,
    'ziwei_engine': _zw_engine,
    'shichen_names': _ZW_SHICHEN if HAS_ZIWEI else [],
    'shichen_ranges': _ZW_SHICHEN_RANGES if HAS_ZIWEI else [],
    'palace_name_map': _ZW_PALACE_MAP if HAS_ZIWEI else {},
    'logger': logger,
})
register_ziwei_ask_routes(app, {
    'has_ziwei': HAS_ZIWEI,
    'ziwei_engine': _zw_engine,
    'get_run_dir': get_run_dir,
    'write_run_status': write_run_status,
    'read_run_status': read_run_status,
})
register_metaphysics_routes(app, db, {
    'has_tarot': HAS_TAROT,
    'tarot_draw': _tarot_draw,
    'tarot_spreads': _tarot_spreads,
    'tarot_verify': _tarot_verify,
    'qimen_paipan': _qimen_paipan,
    'meihua_paipan': _meihua_paipan,
    'liuyao_paipan': _liuyao_paipan,
    'deepseek_available': deepseek_available,
    'use_points': use_points,
    'logger': logger,
})
register_metaphysics_ask_routes(app, db, {
    'liuyao_paipan': _liuyao_paipan,
    'meihua_paipan': _meihua_paipan,
    'deepseek_available': lambda: deepseek_available(),
    'get_reading_stream': lambda messages: get_reading_stream(messages),
    'use_points': use_points,
    'get_run_dir': get_run_dir,
    'write_run_status': write_run_status,
    'logger': logger,
})
register_qimen_ask_routes(app, db, {
    'qimen_paipan': _qimen_paipan,
    'deepseek_available': lambda: deepseek_available(),
    'get_reading_stream': lambda messages: get_reading_stream(messages),
    'get_run_dir': get_run_dir,
    'write_run_status': write_run_status,
    'read_run_status': read_run_status,
    'logger': logger,
})
register_admin_routes(app, db, {
    'record_admin_audit': record_admin_audit,
    'add_points': add_points,
    'confirm_recharge_order_once': confirm_recharge_order_once,
})
register_paid_content_routes(app, db, {
    'use_points': use_points,
    'add_points': add_points,
})
register_tool_run_routes(app, db, {
    'base_dir': BASE_DIR,
    'meihua_paipan': _meihua_paipan,
    'reserve_run_id': reserve_run_id,
    'set_current_process': set_current_process,
    'is_current_run': is_current_run,
    'cleanup_old_runs': cleanup_old_runs,
    'write_run_status': write_run_status,
    'get_run_dir': get_run_dir,
    'read_run_result': read_run_result,
})
register_user_content_routes(app, db)




# ═══════ 全局错误处理 ═══════
def _error_response(e, code, msg):
    """API-only 错误响应。"""
    return jsonify({'success': False, 'error': msg, 'detail': str(e)}), code

# ═══════ CORS 中间件（小程序端必需） ═══════
@app.after_request
def add_cors_headers(response):
    """为 API 请求添加 CORS 头，支持小程序和跨域 H5 访问"""
    origin = request.headers.get('Origin', '')
    # 允许的来源：本地开发 + 小程序
    allowed_origins = [
        'http://localhost:3000',
        'http://127.0.0.1:3000',
        'http://localhost:5199',
        'http://127.0.0.1:5199',
    ]
    # 微信小程序没有 Origin 或使用 wx:// 格式
    if origin in allowed_origins or not origin or origin.startswith('wx://'):
        response.headers['Access-Control-Allow-Origin'] = origin or '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken, X-Requested-With'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Max-Age'] = '3600'
    return response

@app.route('/api/<path:path>', methods=['OPTIONS'])
def api_options(path):
    """处理 API 预检请求 (CORS preflight)"""
    resp = make_response()
    resp.status_code = 204
    return resp

@app.errorhandler(400)
def bad_request(e):
    return _error_response(e, 400, '请求参数无效')

@app.errorhandler(404)
def not_found(e):
    return _error_response(e, 404, '页面不存在')

@app.errorhandler(405)
def method_not_allowed(e):
    return _error_response(e, 405, '请求方法不允许')

@app.errorhandler(500)
def internal_error(e):
    logger.error(f"服务器内部错误: {e}")
    return _error_response(e, 500, '服务器内部错误')

@app.errorhandler(Exception)
def handle_exception(e):
    """捕获所有未处理的异常"""
    logger.error(f"未处理异常: {type(e).__name__}: {e}")
    # CSRF 错误特殊处理
    if 'CSRF' in str(type(e)) or 'csrf' in str(e).lower():
        return jsonify({'success': False, 'error': 'CSRF验证失败，请刷新页面重试'}), 400
    return _error_response(e, 500, str(e) if app.debug else '服务器内部错误')


@app.before_request
def _require_api_header():
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH') and request.path.startswith('/api/'):
        ct = request.content_type or ''
        if 'application/x-www-form-urlencoded' in ct and not request.headers.get('X-Requested-With') and not request.headers.get('Authorization'):
            return jsonify({'success': False, 'error': 'Invalid request'}), 400


if __name__ == '__main__':
    os.makedirs(RUN_BASE, exist_ok=True)
    with app.app_context():
        db.create_all()
        migrate_db()
    logger.info(f"数据库: {os.path.join(BASE_DIR, 'tianji.db')}")
    logger.info(f"排盘脚本: {PAIPAN_SH}")
    _flask_port = int(os.environ.get('FLASK_PORT', '5199'))
    logger.info(f"服务启动: http://127.0.0.1:{_flask_port}")
    app.run(host='127.0.0.1', port=_flask_port, debug=False)
