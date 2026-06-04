#!/usr/bin/env python3
"""时安解忧屋 - 八字排盘 + 天机问策 融合门户 (v6.3)

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
from sqlalchemy import case, event, or_, update
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError, OperationalError
from deepseek_service import get_tarot_reading_stream, get_tarot_followup_stream, get_reading_stream, is_available as deepseek_available
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
                     'admin_audit_log', 'tarot_conversation']:
            try:
                db.session.execute(db.text(f'SELECT 1 FROM {tbl} LIMIT 1'))
            except Exception:
                logger.warning(f"表 {tbl} 不存在，尝试创建")
                try:
                    db.create_all()
                    logger.info(f"[DB] create_all 完成")
                    break  # create_all 一次创建所有缺失表
                except Exception as ce:
                    logger.warning(f"create_all 失败: {ce}")

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
    """旧问真八字专业细盘页已由 H5 接管。"""
    return _frontend_removed('问真八字专业细盘', '#/pages/bazi-result/index')


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


def _calc_ganzhi(year, month, day, hour):
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

    # 年柱
    year_obj = sxtwl.fromSolar(year, month, day)
    year_gz_index = year_obj.getYearGZ()
    year_gan = _TIAN_GAN[year_gz_index.tg]
    year_zhi = _DI_ZHI[year_gz_index.dz]

    # 月柱
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


def _calc_jieqi_ju(year, month, day, hour, minute, pan_type=1):
    """计算节气和起局
    
    Args:
        pan_type: 1=拆补法, 2=置闰法
    """
    import ephem
    import datetime

    # 计算太阳黄经
    date = ephem.Date(f'{year}/{month}/{day} {hour}:{minute}:00')
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
    gz_info = _calc_ganzhi(year, month, day, hour)
    day_gan = gz_info['dayGan']
    day_zhi = gz_info['dayZhi']

    if pan_type == 2:
        # 置闰法定元：基于符头（甲己日）
        yuan, ju, updated_jieqi_name, updated_dun = _calc_yuan_zhirun(
            year, month, day, hour, minute, jieqi_info, jieqi_idx)
        jieqi_name = updated_jieqi_name
        dun = updated_dun
    else:
        # 60甲子直分法（与3meta对齐）：日干支在60甲子中的位置决定三元
        # 无论 pan_type 是 1(茅山法) 还是 3(拆补法)，统一使用此算法
        # 前20（甲子~癸未）→上元，中20（甲申~癸卯）→中元，后20（甲辰~癸亥）→下元
        gan_idx = _TIAN_GAN.index(day_gan)
        zhi_idx = _DI_ZHI.index(day_zhi)
        gz_pos = (gan_idx * 6 - zhi_idx * 5 + 60) % 60

        if gz_pos < 20:
            yuan = '上'
            ju = shang
        elif gz_pos < 40:
            yuan = '中'
            ju = zhong
        else:
            yuan = '下'
            ju = xia

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


def _calc_yuan_zhirun(year, month, day, hour, minute, jieqi_info, jieqi_idx):
    """置闰法定元：基于符头（甲己日）

    置闰法核心逻辑（参照kinqimen实现）：
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

    # 中5宫寄宫：阳遁寄艮8，阴遁寄坤2
    raw_position = position
    if position == 5:
        position = 8 if dun == '阳' else 2

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


# ═══════════════════════════════════════════════════════════════
# 主排盘函数
# ═══════════════════════════════════════════════════════════════

def _qimen_paipan(year, month, day, hour, minute=0, pan_type=1):
    """自写奇门遁甲排盘引擎"""
    try:
        # Step 1: 干支计算
        gz = _calc_ganzhi(year, month, day, hour)

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

        # 中5宫寄宫标记：阳遁寄艮八，阴遁寄坤二
        ji_gong_target = 8 if jq['dun'] == '阳' else 2
        for p in palaces:
            if p and p.get('gong') == 5:
                p['jiGong'] = ji_gong_target

        # 中5宫寄宫处理（3meta handleMiddlePalace 格式）：
        # 1. 寄宫目标（艮8/坤2）的地盘干追加中5宫地盘干 → [原干, 中5宫干]
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
            'palaces': palaces,
            'panType': '置闰法' if pan_type == 2 else '拆补法',
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

@app.route('/api/bazi/wz-pro')
def api_bazi_wz_pro():
    """问真八字专业细盘 API — 代理调用WZ API + 本地补充计算

    GET 参数:
        y: 出生年(如1990)
        m: 出生月(1-12)
        d: 出生日(1-31)
        h: 出生时(0-23)
        mi: 出生分(0-59), 默认0
        s: 性别(1=男, 2=女), 默认1

    返回: 完整的专业细盘数据，供 bazi.html 前端渲染
    """
    from bazi_engine import (
        fetch_wenzhen_dayun, calc_shi_shen_for_gan,
        calc_liu_nian, calc_liu_yue, calc_liu_ri,
        get_jieqi_times, calc_da_yun, JIE_ORDER, JIE_ZHI, MONTH_ZHI,
        TIAN_GAN, DI_ZHI, GAN_YINYANG,
        NAYIN, CANG_GAN,
        YANG_GAN_CHANG_SHENG, YIN_GAN_CHANG_SHENG, CHANG_SHENG_ORDER,
        calc_shi_er_chang_sheng,
        calc_hour_pillar, zhi_to_hour_name,
    )

    try:
        year = int(request.args.get('y', 0))
        month = int(request.args.get('m', 0))
        day = int(request.args.get('d', 0))
        hour = int(request.args.get('h', 0))
        minute = int(request.args.get('mi', 0))
        sex = int(request.args.get('s', 1))
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': '参数格式错误'}), 400

    if not (1900 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23):
        return jsonify({'success': False, 'error': '日期范围错误'}), 400

    gender = '男' if sex == 1 else '女'

    # 调用问真八字API
    wz_data = fetch_wenzhen_dayun(year, month, day, hour, minute, gender)

    if not wz_data:
        return jsonify({'success': False, 'error': '问真八字API不可用，请稍后重试'}), 503

    # ── 解析四柱 ──
    bz = wz_data.get('bz', {})
    if '0' in bz:
        year_gan, year_zhi = bz.get('0', ''), bz.get('1', '')
        month_gan, month_zhi = bz.get('2', ''), bz.get('3', '')
        day_gan, day_zhi = bz.get('4', ''), bz.get('5', '')
        # 时柱：问真API的时柱不可靠（总是返回"X子"），改用本地计算
        wz_hour_gan, wz_hour_zhi = bz.get('6', ''), bz.get('7', '')
    elif 'year' in bz:
        yr = bz.get('year', {})
        mn = bz.get('month', {})
        dy = bz.get('day', {})
        hr = bz.get('hour', {})
        year_gan, year_zhi = yr.get('tg', ''), yr.get('dz', '')
        month_gan, month_zhi = mn.get('tg', ''), mn.get('dz', '')
        day_gan, day_zhi = dy.get('tg', ''), dy.get('dz', '')
        wz_hour_gan, wz_hour_zhi = hr.get('tg', ''), hr.get('dz', '')
    else:
        return jsonify({'success': False, 'error': '无法解析四柱数据'}), 500

    # ── 时柱本地计算（问真API的时柱数据不可靠，始终返回"X子"） ──
    is_night_zi = (hour == 23)
    if is_night_zi:
        # 夜子时需要次日天干
        from datetime import datetime as _dt, timedelta as _td
        next_day = _dt(year, month, day) + _td(days=1)
        from bazi_engine import calc_day_pillar as _calc_dp
        next_day_gan, _ = _calc_dp(next_day)
        hour_gan, hour_zhi = calc_hour_pillar(hour, day_gan, is_night_zi, next_day_gan)
    else:
        hour_gan, hour_zhi = calc_hour_pillar(hour, day_gan)

    # 修正阴历时辰显示
    hour_zhi_name = zhi_to_hour_name(hour_zhi)
    lunar_str = bz.get('8', '') if '0' in bz else ''
    # 替换问真API返回的阴历时辰为本地计算的时辰
    if lunar_str and hour_zhi_name:
        # 格式如 "1990年四月十四 子时" → 替换最后两字
        import re
        lunar_str = re.sub(r'[子丑寅卯辰巳午未申酉戌亥]时$', hour_zhi_name, lunar_str)

    # 日主
    day_master = day_gan

    # ── 十神 ──
    ss_arr = wz_data.get('ss', [])
    # ── 藏干 ──
    cg_arr = wz_data.get('cg', [])
    cgss_arr = wz_data.get('cgss', [])
    # ── 空亡 ──
    kw_arr = wz_data.get('kw', [])
    # ── 星运 ──
    xy_arr = wz_data.get('xy', [])
    # ── 自坐 ──
    zz_arr = wz_data.get('zz', [])
    # ── 纳音 ──
    ny_arr = wz_data.get('ny', [])
    # ── 四柱神煞 ──
    szshensha = wz_data.get('szshensha', [])
    # ── 大运神煞 ──
    dyshensha = wz_data.get('dyshensha', [])

    # ── 大运 ──
    wz_dayun = wz_data.get('dayun', [])
    # ── 小运 ──
    wz_xiaoyun = wz_data.get('xiaoyun', [])

    # ── 起运信息计算 ──
    # WZ API的qiyunarr格式：[加密值, 月, 天, 时, 年, 加密值]
    # 优先使用WZ API返回的qiyunarr数据（与问真网站完全一致），
    # 降级时使用本地传统算法计算起运岁数和起运时间。
    # 传统规则：3天=1年，1天=4个月，1时辰(2小时)=10天
    from bazi_engine import _calc_qi_yun_age, get_jieqi_times, GAN_YINYANG, JIE_ORDER
    from datetime import datetime as _dt
    from dateutil.relativedelta import relativedelta

    year_gan_for_calc = year_gan
    is_yang_year = GAN_YINYANG.get(year_gan_for_calc, '') == '阳'
    is_male = (sex == 1)
    shun = (is_yang_year and is_male) or (not is_yang_year and not is_male)
    dt_solar_local = _dt(year, month, day, hour, minute)
    jieqi_times_local = get_jieqi_times(year)

    # ── 本地计算小运列表（基于正确的时柱） ──
    # WZ API的xiaoyun基于错误的时柱（始终返回子时），需本地重新计算
    # 小运规则：阳男阴女从时柱顺行，阴男阳女从时柱逆行
    # 1岁小运=时柱下一柱（顺行+1/逆行-1），而非时柱本身
    # 注意：必须使用60甲子循环法（gan_zhi_to_num/num_to_gan_zhi），
    # 不能单独操作天干/地支索引，否则会产生无效组合（如甲丑）。
    from bazi_engine import gan_zhi_to_num as _gz2num, num_to_gan_zhi as _num2gz
    xiaoyun_local = []
    hour_num = _gz2num(hour_gan, hour_zhi)
    direction = 1 if shun else -1
    for age in range(1, 121):
        gz_num = (hour_num + direction * age) % 60
        gz = _num2gz(gz_num)
        xiaoyun_local.append({'age': age, 'gan': gz[0], 'zhi': gz[1], 'gan_zhi': gz})

    # 1) 计算起运岁数
    qi_yun_age = _calc_qi_yun_age(dt_solar_local, jieqi_times_local, shun)

    # 2) 精确计算起运时间（本地问真算法，不使用WZ加密数据）
    # WZ API的qiyunarr年/岁字段始终加密，不可靠，现已弃用。
    # 使用问真对齐算法：3天=1年, 1天=4月, 1小时=5天(小时向下取整)
    qiyun_detail = {}
    qiyun_duration = {}  # 出生后N年M月D天H时

    try:
        import math
        from bazi_engine import get_all_jieqi_jd, jd_to_datetime, _JIEQI_LON_MAP, JIE_ORDER

        # 出生时间的 Julian Day (UTC)
        try:
            import swisseph as swe
            birth_jd = swe.julday(year, month, day, hour + minute / 60.0 - 8)
            has_swisseph = True
        except ImportError:
            has_swisseph = False

        S = None  # 距离目标节令的天数（含小数）
        target_jie_dt = None  # 目标节令datetime (BJ)

        if has_swisseph:
            # ── 高精度路径：Swiss Ephemeris JD ──
            all_jie_jd = {}  # {(year, jie_name): jd}
            for y_jie in [year - 1, year, year + 1]:
                jds = get_all_jieqi_jd(y_jie)
                for jie_name in JIE_ORDER:
                    jd = jds.get(jie_name)
                    if jd is not None:
                        all_jie_jd[(y_jie, jie_name)] = jd

            if shun:
                for (y_jie, jie_name), jd in sorted(all_jie_jd.items(), key=lambda x: x[1]):
                    if jd > birth_jd:
                        S = abs(jd - birth_jd)
                        target_jie_dt = jd_to_datetime(jd)
                        break
            else:
                for (y_jie, jie_name), jd in sorted(all_jie_jd.items(), key=lambda x: x[1], reverse=True):
                    if jd <= birth_jd:
                        S = abs(jd - birth_jd)
                        target_jie_dt = jd_to_datetime(jd)
                        break
        else:
            # ── 降级路径：ephem 逐分钟搜索 ──
            all_jie = []
            for y_jie in [year - 1, year, year + 1]:
                jq = get_jieqi_times(y_jie)
                for jie_name in JIE_ORDER:
                    if jie_name in jq:
                        all_jie.append((jq[jie_name], jie_name))
            all_jie.sort(key=lambda x: x[0])

            if shun:
                for jie_dt, jie_name in all_jie:
                    if jie_dt > dt_solar_local:
                        S = abs((jie_dt - dt_solar_local).total_seconds()) / 86400.0
                        target_jie_dt = jie_dt
                        break
            else:
                for jie_dt, jie_name in reversed(all_jie):
                    if jie_dt <= dt_solar_local:
                        S = abs((dt_solar_local - jie_dt).total_seconds()) / 86400.0
                        target_jie_dt = jie_dt
                        break

        if S is not None:
            # ── 问真对齐算法 ──
            # 规则: 3天=1年, 1天=4月, 1小时=5天(先乘5再取整，保留小数精度)
            qiyun_years = int(S / 3)                              # 年 (3天=1年)
            remaining_days = S - qiyun_years * 3                  # 提取年后剩余天数
            qiyun_months = int(remaining_days * 4)                # 月 (1天=4月)
            remaining_after_months = remaining_days - qiyun_months / 4.0  # 提取月后剩余天数
            remaining_hours = remaining_after_months * 24         # 剩余天数→小时
            qiyun_days = int(remaining_hours * 5)                 # 天 (1小时=5天，先乘5再取整)
            qiyun_hours = 0                                       # 小时已转换为天，剩余为0

            qiyun_duration = {
                'years': qiyun_years, 'months': qiyun_months,
                'days': qiyun_days, 'hours': qiyun_hours,
            }

            # 起运日期 = 出生日期 + 起运时间
            qiyun_dt = dt_solar_local + relativedelta(
                years=qiyun_years, months=qiyun_months, days=qiyun_days
            )
            qiyun_detail = {
                'year': qiyun_dt.year, 'month': qiyun_dt.month,
                'day': qiyun_dt.day, 'hour': qiyun_dt.hour, 'minute': qiyun_dt.minute,
            }

            # 用问真算法重新计算 qi_yun_age（比 _calc_qi_yun_age 更准确）
            qi_yun_age = qiyun_years + (1 if qiyun_months >= 6 else 0)
            qi_yun_age = max(1, qi_yun_age)
    except Exception:
        # 降级：使用 _calc_qi_yun_age 的结果
        if qi_yun_age:
            qiyun_year_est = year + qi_yun_age - 1
            qiyun_detail = {'year': qiyun_year_est, 'month': month, 'day': day}
            qiyun_duration = {'years': qi_yun_age, 'months': 0, 'days': 0, 'hours': 0}

    # 胎元/命宫/身宫
    taiyuan = wz_data.get('taiyuan', '')
    taixi = wz_data.get('taixi', '')
    minggong = wz_data.get('minggong', '')
    shenggong = wz_data.get('shenggong', '')
    kongwang = wz_data.get('kongwang', '')

    # ── 构建四柱数据 ──
    pillar_names = ['year', 'month', 'day', 'hour']
    pillar_labels = ['年柱', '月柱', '日柱', '时柱']
    pillar_gans = [year_gan, month_gan, day_gan, hour_gan]
    pillar_zhis = [year_zhi, month_zhi, day_zhi, hour_zhi]

    sizhu = {}
    for i, name in enumerate(pillar_names):
        canggan_items = []
        if i == 3:
            # 时柱藏干：使用本地计算的时柱地支来获取藏干（问真API的时柱不可靠）
            cg_list = CANG_GAN.get(hour_zhi, [])
            cgss_list = [calc_shi_shen_for_gan(day_master, cg) for cg in cg_list]
        else:
            cg_list = cg_arr[i] if i < len(cg_arr) else []
            cgss_list = cgss_arr[i] if i < len(cgss_arr) else []
        for j, gz in enumerate(cg_list):
            ss = cgss_list[j] if j < len(cgss_list) else ''
            canggan_items.append({'gz': gz, 'ss': ss})

        shensha_list = szshensha[i] if i < len(szshensha) else []

        # 主星: 日柱用"元男/元女"
        if i == 2:
            ss_label = '元男' if sex == 1 else '元女'
        elif i == 3:
            # 时柱十神：使用本地计算的时柱天干来计算（问真API的时柱不可靠）
            ss_label = calc_shi_shen_for_gan(day_master, hour_gan)
        elif i < len(ss_arr):
            ss_label = ss_arr[i]
        else:
            ss_label = ''

        # 空亡: 如果是pair形式(如"戌亥"), 拆分
        kw_str = kw_arr[i] if i < len(kw_arr) else ''
        # 确保空亡显示为两个字
        if len(kw_str) == 2 and kw_str[0] in '子丑寅卯辰巳午未申酉戌亥':
            pass  # 已经是正确格式

        # 时柱特殊处理：使用本地计算的时柱数据
        if i == 3:
            hour_nayin = ''
            try:
                tg_idx = TIAN_GAN.index(hour_gan)
                dz_idx = DI_ZHI.index(hour_zhi)
                gz_num = -1
                for k in range(60):
                    if k % 10 == tg_idx and k % 12 == dz_idx:
                        gz_num = k
                        break
                hour_nayin = NAYIN[gz_num] if gz_num >= 0 and gz_num < len(NAYIN) else ''
            except Exception:
                pass
            hour_xingyun = calc_shi_er_chang_sheng(day_master, hour_zhi) if hour_zhi else ''
            hour_zizuo = calc_shi_er_chang_sheng(hour_gan, hour_zhi) if hour_gan and hour_zhi else ''
            # 时柱空亡：基于日柱旬空计算
            from bazi_engine import get_xun_kong
            _, hour_kw = get_xun_kong(day_gan, day_zhi)
            hour_kw_str = hour_kw if hour_kw else ''
            # 时柱神煞：本地计算
            from bazi_engine import _calc_shen_sha_for_ganzhi
            hour_shensha = _calc_shen_sha_for_ganzhi(hour_gan, hour_zhi, day_master, year_gan, year_zhi, month_zhi, day_zhi, gender, '')

            sizhu[name] = {
                'tg': pillar_gans[i],
                'dz': pillar_zhis[i],
                'ss': ss_label,
                'canggan': canggan_items,
                'xingyun': hour_xingyun,
                'zizuo': hour_zizuo,
                'kongwang': hour_kw_str,
                'nayin': hour_nayin,
                'shensha': hour_shensha,
            }
        else:
            sizhu[name] = {
                'tg': pillar_gans[i],
                'dz': pillar_zhis[i],
                'ss': ss_label,
                'canggan': canggan_items,
                'xingyun': xy_arr[i] if i < len(xy_arr) else '',
                'zizuo': zz_arr[i] if i < len(zz_arr) else '',
                'kongwang': kw_str,
                'nayin': ny_arr[i] if i < len(ny_arr) else '',
                'shensha': shensha_list,
            }

    # ── 计算大运列表（含详细数据） ──
    birth_year = year
    current_year = datetime.now().year
    current_age_xu = current_year - birth_year + 1  # 虚岁: 出生当年=1岁

    dayun_list = []
    # 第0项: 起运前小运（从1岁开始，到起运岁前一年为止）
    pre_end_age = qi_yun_age if qi_yun_age > 1 else 1
    pre_start_year = birth_year  # 虚岁1岁=出生当年
    pre_end_year = birth_year + pre_end_age - 1  # 虚岁: age=pre_end_age 对应的年份
    # 起运前显示出生年的小运干支（xiaoyun_local[0] = 1岁小运）
    pre_xy_gz = xiaoyun_local[0]['gan_zhi'] if xiaoyun_local else ''
    pre_xy_tg = pre_xy_gz[0] if len(pre_xy_gz) >= 1 else ''
    pre_xy_dz = pre_xy_gz[1] if len(pre_xy_gz) >= 2 else ''
    pre_xy_tgSs = calc_shi_shen_for_gan(day_master, pre_xy_tg) if pre_xy_tg else ''
    pre_xy_dzSs = calc_shi_shen_for_gan(day_master, CANG_GAN.get(pre_xy_dz, [''])[0]) if pre_xy_dz else ''
    dayun_list.append({
        'year': str(pre_start_year),
        'age': f'1~{pre_end_age}岁',
        'tg': pre_xy_tg, 'tgSs': pre_xy_tgSs, 'dz': pre_xy_dz, 'dzSs': pre_xy_dzSs,
        'gan_zhi': '',
        'start_age': 1,
        'end_age': pre_end_age,
        'current': (1 <= current_age_xu <= pre_end_age),
        'start_year': pre_start_year,
        'end_year': pre_end_year,
        'is_pre_qiyun': True,  # 标记为起运前小运期
    })

    for i, gz in enumerate(wz_dayun):
        start_age = qi_yun_age + 1 + i * 10
        end_age = start_age + 9
        start_year = birth_year + start_age - 1  # 虚岁: 1岁=出生当年
        tg = gz[0] if len(gz) >= 1 else ''
        dz = gz[1] if len(gz) >= 2 else ''
        tg_ss = calc_shi_shen_for_gan(day_master, tg) if tg else ''
        dz_ss = calc_shi_shen_for_gan(day_master, CANG_GAN.get(dz, [''])[0]) if dz else ''

        is_current = (start_age <= current_age_xu <= end_age)

        dayun_list.append({
            'year': str(start_year),
            'age': f'{start_age}岁',
            'tg': tg, 'tgSs': tg_ss, 'dz': dz, 'dzSs': dz_ss,
            'gan_zhi': gz,
            'current': is_current,
            'start_age': start_age,
            'end_age': end_age,
            'start_year': start_year,
            'end_year': birth_year + end_age - 1,
        })

    # ── 计算流年列表 ──
    # 找当前大运
    current_dayun_idx = 0
    for i, dy in enumerate(dayun_list):
        if dy.get('current'):
            current_dayun_idx = i
            break

    # 当前大运对应的流年
    current_dy = dayun_list[current_dayun_idx] if current_dayun_idx < len(dayun_list) else {}
    dy_start_year = int(current_dy.get('year', current_year)) if current_dy.get('year') else current_year
    dy_start_age = current_dy.get('start_age', current_age_xu)
    dy_end_age = current_dy.get('end_age', current_age_xu + 9)

    liunian_list = []
    try:
        import sxtwl as _sxtwl
        # 计算流年数量：根据大运的岁数范围
        # 第一项（起运前小运）：如 1~5岁，则流年5个
        # 后续大运项：10年一个，流年10个
        if current_dayun_idx == 0:
            # 起运前小运，取 age 字段解析岁数范围
            age_str = current_dy.get('age', '')
            age_match = re.search(r'(\d+)~(\d+)', age_str)
            if age_match:
                ln_start_age = int(age_match.group(1))
                ln_end_age = int(age_match.group(2))
            else:
                ln_start_age = 1
                ln_end_age = dy_start_age if dy_start_age > 1 else 1
        else:
            ln_start_age = dy_start_age
            ln_end_age = dy_end_age

        for age in range(ln_start_age, ln_end_age + 1):
            target_year = birth_year + age - 1  # 1岁=出生当年
            if target_year < birth_year or target_year > birth_year + 120:
                continue
            try:
                obj = _sxtwl.fromSolar(target_year, 6, 15)
                gz_obj = obj.getYearGZ()
                ln_gan = TIAN_GAN[gz_obj.tg]
                ln_zhi = DI_ZHI[gz_obj.dz]
            except Exception:
                continue

            ln_gan_ss = calc_shi_shen_for_gan(day_master, ln_gan)
            ln_zhi_ss = calc_shi_shen_for_gan(day_master, CANG_GAN.get(ln_zhi, [''])[0])
            is_current = (target_year == current_year)

            # 小运干支：从问真API获取（索引=岁数-1）
            xiao_yun = xiaoyun_local[age - 1]['gan_zhi'] if age >= 1 and age <= len(xiaoyun_local) else ''

            # 神煞：本地计算
            from bazi_engine import _calc_shen_sha_for_ganzhi as _calc_ss_for_gz
            ln_shensha = _calc_ss_for_gz(ln_gan, ln_zhi, day_master, year_gan, year_zhi, month_zhi, day_zhi, gender, '')

            liunian_list.append({
                'year': str(target_year),
                'age': f'{age}岁',
                'tg': ln_gan, 'tgSs': ln_gan_ss,
                'dz': ln_zhi, 'dzSs': ln_zhi_ss,
                'gan_zhi': ln_gan + ln_zhi,
                'current': is_current,
                'xiao_yun': xiao_yun,
                'shensha': ln_shensha,
            })
    except ImportError:
        pass

    # ── 计算流月列表 ──
    # 基于当前选中的流年
    liuyue_list = []
    try:
        target_year_for_month = current_year
        month_zhi_list = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']
        # 五虎遁：年干决定月干起始 — 必须用流年的年干，不是命主的出生年干
        # 口诀：甲己丙寅起，乙庚戊寅起，丙辛庚寅起，丁壬壬寅起，戊癸甲寅起
        target_year_gan_idx = (target_year_for_month - 4) % 10
        target_year_gan = TIAN_GAN[target_year_gan_idx]
        year_gan_idx = TIAN_GAN.index(target_year_gan) if target_year_gan in TIAN_GAN else 0
        WU_HU_DUN = [2, 4, 6, 8, 0, 2, 4, 6, 8, 0]  # 甲0→丙2, 乙1→戊4, 丙2→庚6, 丁3→壬8, 戊4→甲0, 己5→丙2...
        month_gan_start = WU_HU_DUN[year_gan_idx]

        jie_names = ['立春', '惊蛰', '清明', '立夏', '芒种', '小暑',
                     '立秋', '白露', '寒露', '立冬', '大雪', '小寒']
        jie_dates = ['2/4', '3/5', '4/5', '5/5', '6/5', '7/7',
                     '8/7', '9/7', '10/8', '11/7', '12/7', '1/5']
        month_names = ['正月', '二月', '三月', '四月', '五月', '六月',
                       '七月', '八月', '九月', '十月', '冬月', '腊月']

        for m_idx in range(12):
            m_gan_idx = (month_gan_start + m_idx) % 10
            m_gan = TIAN_GAN[m_gan_idx]
            m_zhi = month_zhi_list[m_idx]
            m_gan_ss = calc_shi_shen_for_gan(day_master, m_gan)
            m_zhi_ss = calc_shi_shen_for_gan(day_master, CANG_GAN.get(m_zhi, [''])[0])
            # 神煞：本地计算
            from bazi_engine import _calc_shen_sha_for_ganzhi as _calc_ss_for_gz2
            lm_shensha = _calc_ss_for_gz2(m_gan, m_zhi, day_master, year_gan, year_zhi, month_zhi, day_zhi, gender, '')

            liuyue_list.append({
                'jieqi': jie_names[m_idx],
                'date': jie_dates[m_idx],
                'month_name': month_names[m_idx],
                'tg': m_gan, 'tgSs': m_gan_ss,
                'dz': m_zhi, 'dzSs': m_zhi_ss,
                'gan_zhi': m_gan + m_zhi,
                'shensha': lm_shensha,
            })
    except Exception as e:
        logger.error(f"流月计算异常: {e}")

    # ── 五行统计 ──
    wuxing_map = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土',
                  '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水',
                  '寅': '木', '卯': '木', '巳': '火', '午': '火', '辰': '土',
                  '丑': '土', '未': '土', '戌': '土', '申': '金', '酉': '金',
                  '亥': '水', '子': '水'}
    wx_count = {'金': 0, '木': 0, '水': 0, '火': 0, '土': 0}
    all_gz = pillar_gans + pillar_zhis
    for g in all_gz:
        wx = wuxing_map.get(g, '')
        if wx:
            wx_count[wx] += 1

    # 旺衰（简化：按月令判断日主旺衰）
    month_wx = wuxing_map.get(month_zhi, '')
    day_wx = wuxing_map.get(day_gan, '')
    sheng_map = {'木': '火', '火': '土', '土': '金', '金': '水', '水': '木'}
    ke_map = {'木': '土', '土': '水', '水': '火', '火': '金', '金': '木'}
    wangshuai = {}
    for wx_name in ['水', '木', '金', '土', '火']:
        if wx_name == month_wx:
            wangshuai[wx_name] = '旺'
        elif sheng_map.get(month_wx) == wx_name:
            wangshuai[wx_name] = '相'
        elif sheng_map.get(wx_name) == month_wx:
            wangshuai[wx_name] = '休'
        elif ke_map.get(month_wx) == wx_name:
            wangshuai[wx_name] = '囚'
        else:
            wangshuai[wx_name] = '死'

    # ── 生肖 ──
    shengxiao_map = {'子': '鼠', '丑': '牛', '寅': '虎', '卯': '兔', '辰': '龙',
                     '巳': '蛇', '午': '马', '未': '羊', '申': '猴', '酉': '鸡',
                     '戌': '狗', '亥': '猪'}
    shengxiao = shengxiao_map.get(year_zhi, '')

    # ── 天干地支关系 ──
    tg_guanxi = _calc_ganzhi_relations_gan(pillar_gans)
    dz_guanxi = _calc_ganzhi_relations_zhi(pillar_zhis)

    # ── 大运详细数据（含十神/藏干/纳音等，用于点击切换） ──
    dayun_details = []
    for i, gz in enumerate(wz_dayun):
        if len(gz) < 2:
            continue
        tg, dz = gz[0], gz[1]
        dy_ss = calc_shi_shen_for_gan(day_master, tg)
        # 藏干
        canggan_items = []
        cg_list_dy = CANG_GAN.get(dz, [])
        for cg_gan in cg_list_dy:
            cg_ss = calc_shi_shen_for_gan(day_master, cg_gan)
            canggan_items.append({'gz': cg_gan, 'ss': cg_ss})
        # 纳音
        try:
            tg_idx = TIAN_GAN.index(tg)
            dz_idx = DI_ZHI.index(dz)
            # 六十甲子序号
            gz_num = -1
            for k in range(60):
                if k % 10 == tg_idx and k % 12 == dz_idx:
                    gz_num = k
                    break
            dy_nayin = NAYIN[gz_num] if gz_num >= 0 and gz_num < len(NAYIN) else ''
        except Exception:
            dy_nayin = ''
        # 星运（十二长生）
        dy_xingyun = calc_shi_er_chang_sheng(day_master, dz) if dz else ''
        # 自坐
        dy_zizuo = calc_shi_er_chang_sheng(tg, dz) if tg and dz else ''
        # 空亡
        from bazi_engine import _calc_kong_wang_for_ganzhi
        dy_kw = _calc_kong_wang_for_ganzhi(tg, dz) if tg and dz else ''
        # 神煞
        dy_ss_list = []
        for dy_ss_item in dyshensha:
            if isinstance(dy_ss_item, (list, tuple)) and len(dy_ss_item) >= 2:
                if dy_ss_item[0] == gz:
                    dy_ss_list = dy_ss_item[1]
                    break

        dayun_details.append({
            'gan_zhi': gz, 'tg': tg, 'dz': dz,
            'ss': dy_ss, 'canggan': canggan_items,
            'xingyun': dy_xingyun, 'zizuo': dy_zizuo,
            'kongwang': dy_kw, 'nayin': dy_nayin,
            'shensha': dy_ss_list,
        })

    # ── 组装返回数据 ──
    result = {
        'success': True,
        'name': f'案例{year}',
        'shengxiao': shengxiao,
        'gender_label': '乾造' if sex == 1 else '坤造',
        'lunar_date': lunar_str,
        'solar_date': f'{year}年{month:02d}月{day:02d}日 {hour:02d}:{minute:02d}',
        'qiyun_info': _build_qiyun_info(qi_yun_age, qiyun_detail, year, month, day, qiyun_duration),
        'jiaoyun_info': f'胎元{taiyuan} 命宫{minggong} 身宫{shenggong} 空亡({kongwang})' if kongwang else f'胎元{taiyuan} 命宫{minggong} 身宫{shenggong}',
        'tg_guanxi': tg_guanxi,
        'dz_guanxi': dz_guanxi,
        'sizhu': sizhu,
        'dayun_list': dayun_list,
        'dayun_details': dayun_details,
        'liunian_list': liunian_list,
        'xiaoyun_list': xiaoyun_local,
        'liuyue_list': liuyue_list,
        'wuxing_wangdu': wangshuai,
        'wuxing_count': wx_count,
        'taiyuan': taiyuan,
        'taixi': taixi,
        'minggong': minggong,
        'shenggong': shenggong,
        'kongwang': kongwang,
        'day_master': day_master,
        'birth_params': {'y': year, 'm': month, 'd': day, 'h': hour, 'mi': minute, 's': sex},
        'current_age_xu': current_age_xu,
        'qi_yun_age': qi_yun_age,
        'qi_yun_detail': qiyun_detail,
    }

    resp = jsonify(result)
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    return resp


def _calc_ganzhi_relations_gan(gans):
    """计算天干关系（合、冲、克）"""
    GAN_HE = [('甲','己','土'),('乙','庚','金'),('丙','辛','水'),('丁','壬','木'),('戊','癸','火')]
    GAN_CHONG = [('甲','庚'),('乙','辛'),('丙','壬'),('丁','癸')]
    GAN_KE = {'木':'土','土':'水','水':'火','火':'金','金':'木'}
    GAN_WX = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    rels = []
    for i in range(len(gans)):
        for j in range(i+1, len(gans)):
            g1, g2 = gans[i], gans[j]
            if not g1 or not g2: continue
            for a, b, name in GAN_HE:
                if (g1==a and g2==b) or (g1==b and g2==a):
                    rels.append(f'{g1}{g2}合化{name}')
            for a, b in GAN_CHONG:
                if (g1==a and g2==b) or (g1==b and g2==a):
                    rels.append(f'{g1}{g2}冲')
            wx1, wx2 = GAN_WX.get(g1,''), GAN_WX.get(g2,'')
            if wx1 and wx2 and GAN_KE.get(wx1)==wx2:
                rels.append(f'{g1}克{g2}')
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
    # 格式对齐问真：只显示非零部分，hours始终为0（已转换为天）不显示
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
    ZHI_LIUHE = [('子','丑'),('寅','亥'),('卯','戌'),('辰','酉'),('巳','申'),('午','未')]
    ZHI_CHONG = [('子','午'),('丑','未'),('寅','申'),('卯','酉'),('辰','戌'),('巳','亥')]
    ZHI_XING = [('寅','巳'),('丑','戌'),('子','卯'),('辰','辰'),('午','午'),('酉','酉'),('亥','亥')]
    ZHI_HAI = [('子','未'),('丑','午'),('寅','巳'),('卯','辰'),('申','亥'),('酉','戌')]
    # 半合
    ZHI_BANHE = [
        ('申','子','半合金水局'),('子','辰','半合金水局'),('申','辰','半合金水局'),
        ('亥','卯','半合木局'),('卯','未','半合木局'),('亥','未','半合木局'),
        ('寅','午','半合火局'),('午','戌','半合火局'),('寅','戌','半合火局'),
        ('巳','酉','半合金局'),('酉','丑','半合金局'),('巳','丑','半合金局'),
    ]
    # 暗合
    ZHI_ANHE = [('寅','丑'),('巳','酉'),('午','亥')]
    # 三会
    ZHI_SANHUI = [
        ({'寅','卯','辰'}, '三会木局'),
        ({'巳','午','未'}, '三会火局'),
        ({'申','酉','戌'}, '三会金局'),
        ({'亥','子','丑'}, '三会水局'),
    ]

    zhi_set = set(z for z in zhis if z)
    rels = []
    for i in range(len(zhis)):
        for j in range(i+1, len(zhis)):
            z1, z2 = zhis[i], zhis[j]
            if not z1 or not z2: continue
            for a, b in ZHI_LIUHE:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{z1}{z2}合化')
            for a, b in ZHI_CHONG:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{z1}{z2}冲')
            for a, b in ZHI_XING:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{z1}{z2}刑')
            for a, b in ZHI_HAI:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{z1}{z2}害')
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
                        rels.append(f'{z1}{z2}{desc}')
            for a, b in ZHI_ANHE:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{z1}{z2}暗合')
            # 六破
            ZHI_PO = [('子','酉'),('丑','辰'),('寅','亥'),('卯','午'),('巳','申'),('未','戌')]
            for a, b in ZHI_PO:
                if (z1==a and z2==b) or (z1==b and z2==a):
                    rels.append(f'{z1}{z2}破')

    # 三会局（需要至少2个地支）
    for trio, hui_desc in ZHI_SANHUI:
        present = trio & zhi_set
        if len(present) >= 2:
            involved = [z for z in zhis if z in trio]
            missing = trio - present
            if missing:
                rels.append(f'{"".join(involved)}{hui_desc}(缺{"".join(missing)})')
            else:
                rels.append(f'{"".join(involved)}{hui_desc}')

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

# 积分规则
POINT_RULES = {
    'sign_in': 10,
    'tool_use': -5,   # 免费用户 -5，会员 0
    'post': 5,
    'comment': 2,
    'liked': 1,        # 被点赞
    'purchased': 0,    # 作者被购买内容获得 70%，动态计算
}

# 会员等级对应的每日工具使用限制（-1 表示不限）
MEMBER_TOOL_LIMIT = {
    'free': 3,
    'basic': -1,
    'premium': -1,
    'vip': -1,
}

def get_or_create_membership(user_id, commit=True):
    """获取或创建会员记录"""
    m = Membership.query.filter_by(user_id=user_id).first()
    if not m:
        m = Membership(user_id=user_id, level='free', points=0)
        db.session.add(m)
        if commit:
            db.session.commit()
        else:
            db.session.flush()
    return m

def add_points(user_id, action, points, description='', dedupe_key=None, commit=True):
    """添加积分日志并更新会员积分。

    commit=False 时由外层事务统一提交，用于订单确认等复合操作。
    dedupe_key 用于同一业务动作幂等，例如每日签到和订单到账。
    """
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
        m = get_or_create_membership(user_id)
        return {'ok': False, 'error': '积分不足', 'current': m.points, 'required': points}
    log = PointLog(user_id=user_id, action=action, points=-points, description=description)
    db.session.add(log)
    db.session.flush()
    new_points = Membership.query.filter_by(user_id=user_id).with_entities(Membership.points).scalar()
    if commit:
        db.session.commit()
    return {'ok': True, 'points': new_points, 'used': points}

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
from media_routes import allowed_file, register_media_routes
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
    'allowed_file': allowed_file,
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
    'use_points': use_points,
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


for _cr in app.url_map.iter_rules():
    if _cr.rule.startswith('/api/'):
        _cf = app.view_functions.get(_cr.endpoint)
        if _cf:
            csrf.exempt(_cf)

@app.before_request
def _require_api_header():
    if request.method in ('POST', 'PUT', 'DELETE', 'PATCH') and request.path.startswith('/api/'):
        ct = request.content_type or ''
        if 'application/x-www-form-urlencoded' in ct and not request.headers.get('X-Requested-With') and not request.headers.get('Authorization'):
            return jsonify({'error': 'Invalid request'}), 400


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
