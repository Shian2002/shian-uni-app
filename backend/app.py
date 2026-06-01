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
from flask import Flask, request, jsonify, make_response, session, redirect, Response, stream_with_context
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import case, or_, update
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

# ═══════ 导入数据模型（必须在 db.init_app 之后） ═══════
from models import User, Record, UserProfile, FollowUp, Collection
from models import Post, Comment, Master, PostLike, Membership, PointLog, PaidContent, Purchase, RechargeOrder, AdminAuditLog, TarotConversation, LiuyaoConversation, MeihuaConversation, QimenConversation, BaziConversation, ZiweiConversation, ComprehensiveConversation
from models import BaziRecord
from comprehensive_ai import (
    COMPREHENSIVE_LLM_MODELS,
    COMPREHENSIVE_TOOL_MODELS,
    TOOL_DISPLAY_ORDER,
    calculate_cost,
    normalize_tool_models,
    recommend_tool_models,
    build_comprehensive_messages,
    build_tool_analysis_messages,
    build_summary_messages,
)

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


@app.route('/api/qimen/paipan', methods=['POST'])
@csrf.exempt
def api_qimen_paipan():
    """奇门遁甲免费排盘 — 自写排盘引擎"""
    data = request.get_json(silent=True) or {}
    year = data.get('year')
    month = data.get('month')
    day = data.get('day')
    hour = data.get('hour', 12)
    minute = data.get('minute', 0)
    pan_type = data.get('panType', 1)  # 1=拆补法, 2=置闰法

    if not all([year, month, day]):
        return jsonify({'error': '请提供完整的日期参数'}), 400

    try:
        year, month, day, hour = int(year), int(month), int(day), int(hour)
        minute, pan_type = int(minute), int(pan_type)
    except (ValueError, TypeError):
        return jsonify({'error': '日期参数格式错误'}), 400

    if not (1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23):
        return jsonify({'error': '日期范围错误'}), 400

    result = _qimen_paipan(year, month, day, hour, minute, pan_type)
    if 'error' in result:
        return jsonify(result), 500

    return jsonify(result)


@app.route('/api/qimen/paipan', methods=['GET'])
def api_qimen_paipan_get():
    """奇门遁甲免费排盘 — GET 版本（方便测试）"""
    now = datetime.now()
    year = request.args.get('year', type=int, default=now.year)
    month = request.args.get('month', type=int, default=now.month)
    day = request.args.get('day', type=int, default=now.day)
    hour = request.args.get('hour', type=int, default=now.hour)
    minute = request.args.get('minute', type=int, default=0)
    pan_type = request.args.get('panType', type=int, default=1)

    result = _qimen_paipan(year, month, day, hour, minute, pan_type)
    if 'error' in result:
        return jsonify(result), 500

    return jsonify(result)


# ═══════════════════════════════════════════════════════════════
# 奇门AI问策 — 一键起局 + 豆包AI解盘
def _build_qimen_ask_prompt(question, qimen):
    """根据奇门排盘数据和用户问题构建 Prompt"""
    fp = qimen.get('fourPillars', {})
    palaces = qimen.get('palaces', [])

    prompt = f'''## 奇门排盘数据

**起局时间**：{qimen.get('solarDate', '')}
**局数**：{qimen.get('ju', '')}
**节气**：{qimen.get('solarTerm', '')}

**四柱**：{fp.get('year', '')}年 {fp.get('month', '')}月 {fp.get('day', '')}日 {fp.get('hour', '')}时

**值符**：{qimen.get('zhiFu', '')}
**值使**：{qimen.get('zhiShi', '')}

**九宫详情**：
'''
    for p in palaces:
        g = p.get('gong', p.get('position', '?'))
        men = p.get('men', p.get('gate', ''))
        xing = p.get('xing', '')
        if isinstance(xing, list):
            xing = '/'.join(xing)
        shen = p.get('shen', p.get('deity', ''))
        tian = p.get('tianGan', '')
        if isinstance(tian, list):
            tian = '/'.join(tian)
        di = p.get('diGan', '')
        if isinstance(di, list):
            di = '/'.join(di)
        prompt += f'- {g}宫：门={men} 星={xing} 神={shen} 天={tian} 地={di}\n'

    prompt += f'''

## 用户问题

{question}

## 分析要求

请根据以上奇门排盘数据，对用户的问题进行专业分析。'''
    return prompt




# ═══════════════════════════════════════════════════════════════

_qimen_ask_current_run = 0
_qimen_ask_lock = threading.Lock()

@app.route('/api/qimen/ask', methods=['POST'])
@csrf.exempt
def api_qimen_ask():
    """一键起局+AI解盘：接收用户问题+时间参数，异步起局并调用豆包API"""
    global _qimen_ask_current_run
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    if not question:
        return jsonify({'error': '请输入您的问题'}), 400

    # 获取时间参数（未传则用当前时间）
    now = datetime.now()
    year = data.get('year', now.year)
    month = data.get('month', now.month)
    day = data.get('day', now.day)
    hour = data.get('hour', now.hour)
    minute = data.get('minute', 0)
    pan_type = data.get('panType', 3)

    # 起局排盘
    try:
        result = _qimen_paipan(int(year), int(month), int(day), int(hour), int(minute), int(pan_type))
    except Exception as e:
        return jsonify({'error': f'起局失败: {str(e)}'}), 500
    if 'error' in result:
        return jsonify({'error': result['error']}), 500

    # 生成 run_id
    with _qimen_ask_lock:
        _qimen_ask_current_run += 1
        run_id = _qimen_ask_current_run

    run_dir = get_run_dir(run_id)

    # 保存排盘数据和问题
    with open(os.path.join(run_dir, 'qimen.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)
    with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
        f.write(question)
    # 保存深度分析模式
    is_deep = data.get('deep_analysis', False)
    with open(os.path.join(run_dir, 'deep_mode.txt'), 'w') as f:
        f.write('1' if is_deep else '0')

    write_run_status(run_id, {'phase': 'calculating', 'message': '起局中...', 'progress': 10, 'run_id': run_id})

    # 启动后台线程
    t = threading.Thread(target=_qimen_ask_task, args=(run_id,), daemon=True)
    t.start()

    return jsonify({'status': 'started', 'run_id': run_id})


@app.route('/api/qimen/ask/status')
def api_qimen_ask_status():
    """查询奇门AI问策任务状态"""
    run_id = request.args.get('run_id', type=int, default=0)
    if run_id <= 0:
        return jsonify({'phase': 'idle', 'message': '等待开始', 'progress': 0})

    s = read_run_status(run_id)
    s['run_id'] = run_id

    # 完成时附带完整结果
    if s.get('phase') == 'done':
        run_dir = get_run_dir(run_id)
        result = None
        for fn in ['result.md', 'result.txt']:
            try:
                with open(os.path.join(run_dir, fn), 'r', encoding='utf-8') as f:
                    result = f.read().strip()
                if result:
                    break
            except:
                continue
        if result:
            s['result'] = result
        # 附加思考过程（R1深度分析）
        try:
            with open(os.path.join(run_dir, 'reasoning.md'), 'r', encoding='utf-8') as f:
                reasoning = f.read().strip()
            if reasoning:
                s['reasoning'] = reasoning
        except:
            pass
    elif s.get('phase') == 'error':
        pass  # 错误信息已在 status 中

    return jsonify(s)


# qimen SSE direct streaming endpoint
@app.route('/api/qimen/ask/stream', methods=['POST'])
@login_required
def api_qimen_ask_stream():
    """奇门遁甲 SSE 流式 AI 解读"""
    if not deepseek_available():
        def eg():
            yield "event: error\ndata: {\"message\": \"AI 服务未配置\"}\n\n"
        return Response(eg(), mimetype='text/event-stream')

    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    if not question:
        def eg2():
            yield "event: error\ndata: {\"message\": \"请输入您的问题\"}\n\n"
        return Response(eg2(), mimetype='text/event-stream')

    now = datetime.now()
    year = data.get('year', now.year)
    month = data.get('month', now.month)
    day = data.get('day', now.day)
    hour = data.get('hour', now.hour)
    minute = data.get('minute', 0)
    pan_type = data.get('panType', 3)
    is_followup = bool(data.get('history') or [])
    try:
        result = _qimen_paipan(int(year), int(month), int(day), int(hour), int(minute), int(pan_type))
    except Exception as ex:
        def eg3():
            yield f"event: error\ndata: {{\"message\": \"起局失败: {ex}\"}}\n\n"
        return Response(eg3(), mimetype='text/event-stream')
    if 'error' in result:
        def eg4():
            yield f"event: error\ndata: {{\"message\": \"{result['error']}\"}}\n\n"
        return Response(eg4(), mimetype='text/event-stream')

    QIMEN_SP = """你是一位精通奇门遁甲的资深命理专家，擅长根据奇门遁甲盘面分析问题。
请根据用户提供的奇门排盘数据和问题，给出专业的奇门遁甲分析解读。

你的回答应该包括以下结构（markdown格式）：
1. **盘面概要**：说明当前的时辰、局数、值符值使
2. **用神分析**：根据用户问题选择对应的用神宫位，分析天盘地盘关系
3. **吉凶判断**：分析八门、九星、八神、天干等吉凶格局和组合
4. **建议指导**：给出针对性的建议和注意事项

要求：
- 语言通俗易懂，专业但不晦涩
- 用 markdown 标题和列表组织内容
- 避免笼统的套话，要结合具体盘面数据
- 字数控制在 800-1500 字"""

    def generate():
        yield "event: progress\ndata: {\"stage\": \"connecting\"}\n\n"
        try:
            prompt = _build_qimen_ask_prompt(question, result)
            if is_followup:
                history = data.get('history') or []
                messages = [{"role": "system", "content": QIMEN_SP}]
                for h in history:
                    messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                messages.append({"role": "user", "content": question})
            else:
                messages = [
                    {"role": "system", "content": QIMEN_SP},
                    {"role": "user", "content": prompt}
                ]
            yield "event: progress\ndata: {\"stage\": \"analyzing\"}\n\n"
            yield "event: progress\ndata: {\"stage\": \"generating\"}\n\n"
            full_text = ""
            for chunk, error in get_reading_stream(messages):
                if error:
                    yield f"event: error\ndata: {{\"message\": \"{error}\"}}\n\n"
                    return
                if chunk:
                    full_text += chunk
                    yield f"event: chunk\ndata: {{\"content\": {json.dumps(chunk)}}}\n\n"
            yield f"event: done\ndata: {{\"length\": {len(full_text)}}}\n\n"
            if not is_followup:
                try:
                    rec = Record(user_id=current_user.id, app_type='qimen', question=question, result_html=full_text)
                    db.session.add(rec)
                    db.session.commit()
                except Exception:
                    pass
        except Exception as ex2:
            logger.error(f"奇闪 AI 解读异帎: {ex2}")
            yield "event: error\ndata: {\"message\": \"AI 服务暂时不可用\"}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
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


@app.route('/api/meihua/paipan', methods=['POST'])
@csrf.exempt
def api_meihua_paipan():
    """梅花易数免费排盘 API — 纯Python本地计算，无需登录"""
    data = request.get_json(silent=True) or {}
    method = data.get('method', 'time')

    if method not in ('time', 'number', 'word'):
        return jsonify({'error': '不支持的起卦方式'}), 400

    # 解析时间参数
    time_str = data.get('time', '')
    year = month = day = hour = None
    if time_str:
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            year, month, day, hour = dt.year, dt.month, dt.day, ((dt.hour + 1) // 2) % 12 + 1
            if hour == 0:
                hour = 12
        except (ValueError, TypeError):
            pass

    result = _meihua_paipan(
        method=method,
        num1=data.get('num1'),
        num2=data.get('num2'),
        words=data.get('words'),
        year=year, month=month, day=day, hour=hour,
    )

    if 'error' in result:
        return jsonify(result), 500

    return jsonify(result)


@app.route('/api/meihua/paipan', methods=['GET'])
def api_meihua_paipan_get():
    """梅花易数免费排盘 — GET 版本（方便测试）"""
    method = request.args.get('method', 'time')
    num1 = request.args.get('num1', type=int)
    num2 = request.args.get('num2', type=int)
    words = request.args.get('words', '')
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    day = request.args.get('day', type=int)
    hour = request.args.get('hour', type=int)

    result = _meihua_paipan(
        method=method, num1=num1, num2=num2, words=words,
        year=year, month=month, day=day, hour=hour,
    )
    if 'error' in result:
        return jsonify(result), 500

    return jsonify(result)


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


@app.route('/api/liuyao/paipan', methods=['POST'])
@csrf.exempt
def api_liuyao_paipan():
    """六爻纳甲免费排盘 API — 纯Python本地计算，无需登录"""
    data = request.get_json(silent=True) or {}
    mode = data.get('mode', 'auto')
    tosses = data.get('tosses')
    question = data.get('question', '')

    if mode not in ('auto', 'manual'):
        return jsonify({'error': '不支持的起卦方式'}), 400

    result = _liuyao_paipan(mode=mode, tosses=tosses, question=question)
    if 'error' in result:
        return jsonify(result), 400

    return jsonify(result)


@app.route('/api/liuyao/paipan', methods=['GET'])
def api_liuyao_paipan_get():
    """六爻纳甲免费排盘 — GET 版本（方便测试，自动摇卦）"""
    result = _liuyao_paipan(mode='auto')
    return jsonify(result)


# ═══════════════════════════════════════════════════════════════
# 六爻AI问策 — 一键起卦 + DeepSeek AI解盘
# ═══════════════════════════════════════════════════════════════

_liuyao_ask_current_run = 0
_liuyao_ask_lock = threading.Lock()

@app.route('/api/liuyao/ask', methods=['POST'])
@csrf.exempt
def api_liuyao_ask():
    """一键起卦+AI解盘：摇卦 → 构建 Prompt → DeepSeek 分析"""
    global _liuyao_ask_current_run
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    mode = data.get('mode', 'auto')
    tosses = data.get('tosses')
    deep_analysis = data.get('deep_analysis', False)

    # 起卦排盘
    result = _liuyao_paipan(mode=mode, tosses=tosses, question=question)
    if 'error' in result:
        return jsonify({'error': result['error']}), 500

    # 生成 run_id
    with _liuyao_ask_lock:
        _liuyao_ask_current_run += 1
        run_id = _liuyao_ask_current_run

    run_dir = get_run_dir(run_id)

    # 保存排盘数据
    with open(os.path.join(run_dir, 'liuyao.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)
    with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
        f.write(question)
    with open(os.path.join(run_dir, 'deep_mode.txt'), 'w') as f:
        f.write('1' if deep_analysis else '0')

    write_run_status(run_id, {'phase': 'calculating', 'message': '起卦中...', 'progress': 10, 'run_id': run_id})

    t = threading.Thread(target=_liuyao_ask_task, args=(run_id,), daemon=True)
    t.start()

    return jsonify({'status': 'started', 'run_id': run_id, 'gua': result.get('本卦', ''), 'bian': result.get('变卦', '')})



@app.route('/api/liuyao/ask/stream', methods=['POST'])
@login_required
def api_liuyao_ask_stream():
    """六爻纳甲 SSE 流式 AI 解读"""
    if not deepseek_available():
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': 'AI 服务未配置'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    history = data.get('history') or []
    is_followup = bool(history)

    if not question:
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': '请输入您的问题'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    cost = 1 if is_followup else 5
    spend = use_points(current_user.id, 'liuyao_reading', cost, '六爻 AI ' + ('追问' if is_followup else '解读'))
    if not spend.get('ok'):
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': f'积分不足（需要 {cost} 积分）'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    LIUYAO_SP = """你是一位精通六爻纳甲（六爻占卜）的资深命理专家，擅长根据六爻卦象分析问题。
请根据用户提供的六爻排盘数据和问题，给出专业的六爻分析解读。

你的回答应该包括以下结构（markdown格式）：
1. **卦象解读**：解读本卦、变卦的含义和象征
2. **用神分析**：根据问题确定用神，分析用神的旺衰休囚
3. **世应关系**：分析世爻和应爻的位置关系与生克
4. **动爻分析**：如果有动爻，分析动爻的提示意义
5. **建议指导**：给出针对性的建议

要求：语言通俗易懂，用 markdown 组织内容，结合具体卦象分析，字数 600-1200 字。"""

    def generate():
        yield f"event: progress\ndata: {json.dumps({'stage': 'connecting'})}\n\n"
        try:
            if is_followup:
                messages = [{"role": "system", "content": LIUYAO_SP}]
                for h in history:
                    messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                messages.append({"role": "user", "content": question})
            else:
                mode = data.get('mode', 'auto')
                tosses = data.get('tosses')
                result = _liuyao_paipan(mode=mode, tosses=tosses, question=question)
                if 'error' in result:
                    yield f"event: error\ndata: {json.dumps({'message': result['error']})}\n\n"
                    return

                yield f"event: progress\ndata: {json.dumps({'stage': 'analyzing'})}\n\n"
                # 发送排盘结果给前端渲染
                paipan_keys = {k: result[k] for k in [
                    '本卦','变卦','palace_name','palace_element','day_ganzhi','month_ganzhi','method',
                    'upper_nature','upper_trigram','lower_nature','lower_trigram',
                    'bian_upper_nature','bian_upper_trigram','bian_lower_nature','bian_lower_trigram',
                    '世爻','应爻','details','bian_details','六亲','六神'
                ] if k in result}
                yield f"event: paipan\ndata: {json.dumps(paipan_keys)}\n\n"
                prompt = _build_liuyao_ask_prompt(question, result)
                messages = [
                    {"role": "system", "content": LIUYAO_SP},
                    {"role": "user", "content": prompt}
                ]

            yield f"event: progress\ndata: {json.dumps({'stage': 'generating'})}\n\n"
            full_text = ""
            for chunk, error in get_reading_stream(messages):
                if error:
                    yield f"event: error\ndata: {json.dumps({'message': error})}\n\n"
                    return
                if chunk:
                    full_text += chunk
                    yield f"event: chunk\ndata: {json.dumps({'content': chunk})}\n\n"
            yield f"event: done\ndata: {json.dumps({'length': len(full_text)})}\n\n"

            if not is_followup:
                try:
                    rec = Record(user_id=current_user.id, app_type='liuyao', question=question, result_html=full_text)
                    db.session.add(rec)
                    db.session.commit()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"六爻 AI 解读异常: {e}")
            yield f"event: error\ndata: {json.dumps({'message': 'AI 服务暂时不可用'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})



def _build_liuyao_ask_prompt(question, liuyao):
    """将六爻排盘数据转为结构化 Prompt"""
    prompt = f'''## 六爻排盘数据

**起卦时间**：{liuyao.get('timestamp', '')}
**卦象**：本卦 {liuyao.get('本卦', '')} → 变卦 {liuyao.get('变卦', '')}
**宫位**：{liuyao.get('palace_name', '')}宫（{liuyao.get('palace_element', '')}）
**世应**：世爻{liuyao.get('世爻', '')}位  应爻{liuyao.get('应爻', '')}位

**日辰**：{liuyao.get('day_ganzhi', '')}  月建：{liuyao.get('month_ganzhi', '')}
**起卦方式**：{liuyao.get('method', '')}

**各爻详情**：
'''
    details = liuyao.get('details', [])
    for i, yao in enumerate(details):
        yao_name = yao.get('name', f'第{i+1}爻')
        liuqin = yao.get('liuqin', '')
        liushen = yao.get('liushen', '')
        naja = yao.get('naja', '')
        yaotype = yao.get('yao_type', '')
        moving = '⚡动爻' if yao.get('is_moving') else ''
        prompt += f'- {yao_name}：{naja} {liuqin} {liushen} {yaotype}{moving}\n'

    # 变爻
    bian_details = liuyao.get('bian_details', [])
    moving_exists = any(y.get('is_moving') for y in details)
    if bian_details and moving_exists:
        prompt += '\n**变卦各爻**：\n'
        for i, yao in enumerate(bian_details):
            yao_name = yao.get('name', f'第{i+1}爻')
            prompt += f'- {yao_name}：{yao.get("naja","")} {yao.get("liuqin","")}\n'

    # 六亲
    liuqin_list = liuyao.get('六亲', [])
    if liuqin_list:
        liuqin_str = ' '.join(liuqin_list)
        prompt += f'\n**六亲**：{liuqin_str}\n'

    # 六神
    liushen_list = liuyao.get('六神', [])
    if liushen_list:
        liushen_str = ' '.join(liushen_list)
        prompt += f'**六神**：{liushen_str}\n'

    prompt += f'''

## 用户问题

{question}

## 分析要求

请根据以上六爻排盘数据，对用户的问题进行专业分析。需要包括：
1. **卦象解读**：本卦、变卦、互卦的含义
2. **用神分析**：根据问题定用神，分析用神旺衰
3. **世应关系**：世爻和应爻的生克关系
4. **动爻分析**：动爻的提示意义
5. **建议指导**：针对性的建议

要求：通俗易懂，结构清晰，结合具体卦象数据。'''
    return prompt


def _liuyao_ask_task(run_id):
    """后台线程：构建 Prompt → 调用 DeepSeek → 保存结果"""
    try:
        run_dir = get_run_dir(run_id)

        # 读取排盘数据
        liuyao = None
        try:
            with open(os.path.join(run_dir, 'liuyao.json'), 'r', encoding='utf-8') as f:
                liuyao = json.load(f)
        except:
            pass
        if not liuyao:
            write_run_status(run_id, {'phase': 'error', 'message': '排盘数据读取失败', 'progress': 0, 'run_id': run_id})
            return

        # 读取问题
        question = ''
        try:
            with open(os.path.join(run_dir, 'question.txt'), 'r', encoding='utf-8') as f:
                question = f.read().strip()
        except:
            pass

        # 读取深度分析模式
        is_deep = False
        try:
            with open(os.path.join(run_dir, 'deep_mode.txt'), 'r') as f:
                is_deep = f.read().strip() == '1'
        except:
            pass

        write_run_status(run_id, {'phase': 'analyzing', 'message': 'AI解卦中...', 'progress': 30, 'run_id': run_id})

        # 构建 Prompt
        prompt = _build_liuyao_ask_prompt(question, liuyao)

        # 调用 DeepSeek（使用六爻专用系统提示词）
        LIUYAO_SYSTEM_PROMPT = """你是一位精通六爻纳甲（六爻占卜）的资深命理专家，擅长根据六爻卦象分析问题。
请根据用户提供的六爻排盘数据和问题，给出专业的六爻分析解读。

你的回答应该包括以下结构（markdown格式）：
1. **卦象解读**：解读本卦、变卦的含义和象征
2. **用神分析**：根据问题确定用神，分析用神的旺衰休囚
3. **世应关系**：分析世爻和应爻的位置关系与生克
4. **动爻分析**：如果有动爻，分析动爻的提示意义
5. **建议指导**：给出针对性的建议

要求：
- 语言通俗易懂，专业但不晦涩
- 用 markdown 标题和列表组织内容
- 结合具体卦象、爻位、六亲、六神进行解读
- 字数控制在 600-1200 字"""

        from deepseek_service import get_qimen_reading as get_liuyao_reading

        write_run_status(run_id, {'phase': 'streaming', 'message': '生成解答中...', 'progress': 50, 'run_id': run_id})

        # 调用 DeepSeek（六爻专用）
        result = get_liuyao_reading(prompt, question, is_deep=is_deep, system_prompt=LIUYAO_SYSTEM_PROMPT)
        if result.get('error'):
            write_run_status(run_id, {'phase': 'error', 'message': result['error'], 'progress': 0, 'run_id': run_id})
            return

        content = result.get('content', '')
        reasoning = result.get('reasoning')

        with open(os.path.join(run_dir, 'result.md'), 'w', encoding='utf-8') as f:
            f.write(content)
        if reasoning:
            with open(os.path.join(run_dir, 'reasoning.md'), 'w', encoding='utf-8') as f:
                f.write(reasoning)
        with open(os.path.join(run_dir, 'stream.txt'), 'w', encoding='utf-8') as f:
            f.write(content)

        write_run_status(run_id, {'phase': 'done', 'message': '解卦完成', 'progress': 100, 'run_id': run_id})

    except Exception as e:
        write_run_status(run_id, {'phase': 'error', 'message': f'处理出错: {str(e)}', 'progress': 0, 'run_id': run_id})


# ═══════════════════════════════════════════════════════════════
# 梅花AI问策 — 一键起卦 + DeepSeek AI解盘
# ═══════════════════════════════════════════════════════════════

_meihua_ask_current_run = 0
_meihua_ask_lock = threading.Lock()

@app.route('/api/meihua/ask', methods=['POST'])
@csrf.exempt
def api_meihua_ask():
    """一键起卦+AI解盘：起卦 → 构建 Prompt → DeepSeek 分析"""
    global _meihua_ask_current_run
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    method = data.get('method', 'time')
    deep_analysis = data.get('deep_analysis', False)

    # 解析参数
    num1 = data.get('num1')
    num2 = data.get('num2')
    words = data.get('words')
    time_str = data.get('time', '')
    year = month = day = hour = None
    if time_str:
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            year, month, day, hour = dt.year, dt.month, dt.day, ((dt.hour + 1) // 2) % 12 + 1
            if hour == 0: hour = 12
        except:
            pass

    # 起卦
    result = _meihua_paipan(method=method, num1=num1, num2=num2, words=words,
                            year=year, month=month, day=day, hour=hour)
    if 'error' in result:
        return jsonify({'error': result['error']}), 500

    # 生成 run_id
    with _meihua_ask_lock:
        _meihua_ask_current_run += 1
        run_id = _meihua_ask_current_run
    run_dir = get_run_dir(run_id)

    with open(os.path.join(run_dir, 'meihua.json'), 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)
    with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
        f.write(question)
    with open(os.path.join(run_dir, 'deep_mode.txt'), 'w') as f:
        f.write('1' if deep_analysis else '0')

    write_run_status(run_id, {'phase': 'calculating', 'message': '起卦中...', 'progress': 10, 'run_id': run_id})

    t = threading.Thread(target=_meihua_ask_task, args=(run_id,), daemon=True)
    t.start()
    return jsonify({'status': 'started', 'run_id': run_id, 'gua': result.get('benGua', {}).get('name', '')})



@app.route('/api/meihua/ask/stream', methods=['POST'])
@login_required
def api_meihua_ask_stream():
    """梅花易数 SSE 流式 AI 解读"""
    if not deepseek_available():
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': 'AI 服务未配置'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    history = data.get('history') or []
    is_followup = bool(history)

    if not question:
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': '请输入您的问题'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    cost = 1 if is_followup else 5
    spend = use_points(current_user.id, 'meihua_reading', cost, '梅花易数 AI ' + ('追问' if is_followup else '解读'))
    if not spend.get('ok'):
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': f'积分不足（需要 {cost} 积分）'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    MEIHUA_SP = """你是一位精通梅花易数的资深命理专家，擅长根据卦象分析问题。
请根据用户提供的梅花易数排盘数据，给出专业的分析解读。

回答结构：
1. **卦象解读**：解读本卦、变卦、互卦的含义
2. **体用分析**：体卦和用卦的生克关系
3. **动爻分析**：动爻的提示意义
4. **建议指导**：针对性的建议

要求：通俗易懂，语言平和，结合具体卦象分析。"""

    def generate():
        yield f"event: progress\ndata: {json.dumps({'stage': 'connecting'})}\n\n"
        try:
            if is_followup:
                messages = [{"role": "system", "content": MEIHUA_SP}]
                for h in history:
                    messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                messages.append({"role": "user", "content": question})
            else:
                method = data.get('method', 'time')
                num1 = data.get('num1')
                num2 = data.get('num2')
                words = data.get('words')
                time_str = data.get('time', '')
                year = month = day = hour = None
                if time_str:
                    try:
                        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
                        year, month, day, hour = dt.year, dt.month, dt.day, ((dt.hour + 1) // 2) % 12 + 1
                        if hour == 0: hour = 12
                    except Exception:
                        pass

                result = _meihua_paipan(method=method, num1=num1, num2=num2, words=words,
                                        year=year, month=month, day=day, hour=hour)
                if 'error' in result:
                    yield f"event: error\ndata: {json.dumps({'message': result['error']})}\n\n"
                    return

                yield f"event: progress\ndata: {json.dumps({'stage': 'analyzing'})}\n\n"
                prompt = _build_meihua_ask_prompt(question, result)
                messages = [
                    {"role": "system", "content": MEIHUA_SP},
                    {"role": "user", "content": prompt}
                ]

            yield f"event: progress\ndata: {json.dumps({'stage': 'generating'})}\n\n"
            full_text = ""
            for chunk, error in get_reading_stream(messages):
                if error:
                    yield f"event: error\ndata: {json.dumps({'message': error})}\n\n"
                    return
                if chunk:
                    full_text += chunk
                    yield f"event: chunk\ndata: {json.dumps({'content': chunk})}\n\n"
            yield f"event: done\ndata: {json.dumps({'length': len(full_text)})}\n\n"

            if not is_followup:
                try:
                    rec = Record(user_id=current_user.id, app_type='meihua', question=question, result_html=full_text)
                    db.session.add(rec)
                    db.session.commit()
                except Exception:
                    pass
        except Exception as e:
            logger.error(f"梅花 AI 解读异常: {e}")
            yield f"event: error\ndata: {json.dumps({'message': 'AI 服务暂时不可用'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})



def _build_meihua_ask_prompt(question, meihua):
    """将梅花易数排盘数据转为结构化的 Prompt"""
    ben = meihua.get('benGua', {})
    bian = meihua.get('bianGua', {})
    hu = meihua.get('huGua', {})
    ty = meihua.get('tiYong', {})

    prompt = f'''## 梅花易数排盘数据

**起卦方式**：{meihua.get('methodLabel', '时间起卦')}
**起卦时间**：{meihua.get('paipanTime', '')}

**本卦**：{ben.get('name', '')}（上{ben.get('upper',{}).get('nature','')} {ben.get('upper',{}).get('name','')}·{ben.get('upper',{}).get('wuxing','')} → 下{ben.get('lower',{}).get('nature','')} {ben.get('lower',{}).get('name','')}·{ben.get('lower',{}).get('wuxing','')}）
**变卦**：{bian.get('name', '')}
**互卦**：{hu.get('name', '')}
**动爻**：第{meihua.get('dongYao', '')}爻

**体用关系**：{ty.get('tiYongJiXiong', '')}
**断语**：{ty.get('verdict', '')}

**干支**：{meihua.get('ganzhi', '')}

## 用户问题

{question}

## 分析要求

请根据以上梅花易数排盘数据，对用户的问题进行专业分析。需要包括：
1. **卦象解读**：本卦、变卦、互卦的含义和象征
2. **体用分析**：体卦和用卦的生克关系和吉凶
3. **动爻分析**：动爻的提示意义
4. **建议指导**：针对性的建议

要求：通俗易懂，结合具体卦象和年月日时进行分析。'''
    return prompt


def _meihua_ask_task(run_id):
    """后台线程：构建 Prompt → 调用 DeepSeek → 保存结果"""
    try:
        run_dir = get_run_dir(run_id)
        meihua = None
        try:
            with open(os.path.join(run_dir, 'meihua.json'), 'r', encoding='utf-8') as f:
                meihua = json.load(f)
        except:
            pass
        if not meihua:
            write_run_status(run_id, {'phase': 'error', 'message': '排盘数据读取失败', 'progress': 0, 'run_id': run_id})
            return

        question = ''
        try:
            with open(os.path.join(run_dir, 'question.txt'), 'r', encoding='utf-8') as f:
                question = f.read().strip()
        except:
            pass

        is_deep = False
        try:
            with open(os.path.join(run_dir, 'deep_mode.txt'), 'r') as f:
                is_deep = f.read().strip() == '1'
        except:
            pass

        write_run_status(run_id, {'phase': 'analyzing', 'message': 'AI解卦中...', 'progress': 30, 'run_id': run_id})

        prompt = _build_meihua_ask_prompt(question, meihua)

        MEIHUA_SYSTEM_PROMPT = """你是一位精通梅花易数的资深命理专家，擅长根据卦象分析问题。
请根据用户提供的梅花易数排盘数据，给出专业的分析解读。

回答结构：
1. **卦象解读**：解读本卦、变卦、互卦的含义
2. **体用分析**：体卦和用卦的生克关系
3. **动爻分析**：动爻的提示意义
4. **建议指导**：针对性的建议

要求：通俗易懂，语言平和，结合具体卦象分析。"""

        from deepseek_service import get_qimen_reading as get_mh_reading

        write_run_status(run_id, {'phase': 'streaming', 'message': '生成解答中...', 'progress': 50, 'run_id': run_id})
        result = get_mh_reading(prompt, question, is_deep=is_deep, system_prompt=MEIHUA_SYSTEM_PROMPT)
        if result.get('error'):
            write_run_status(run_id, {'phase': 'error', 'message': result['error'], 'progress': 0, 'run_id': run_id})
            return

        content = result.get('content', '')
        reasoning = result.get('reasoning')

        with open(os.path.join(run_dir, 'result.md'), 'w', encoding='utf-8') as f:
            f.write(content)
        if reasoning:
            with open(os.path.join(run_dir, 'reasoning.md'), 'w', encoding='utf-8') as f:
                f.write(reasoning)
        with open(os.path.join(run_dir, 'stream.txt'), 'w', encoding='utf-8') as f:
            f.write(content)

        write_run_status(run_id, {'phase': 'done', 'message': '解卦完成', 'progress': 100, 'run_id': run_id})

    except Exception as e:
        write_run_status(run_id, {'phase': 'error', 'message': f'处理出错: {str(e)}', 'progress': 0, 'run_id': run_id})


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

@app.route('/api/tarot/draw', methods=['POST'])
@csrf.exempt
def api_tarot_draw():
    if not HAS_TAROT:
        return jsonify({'code': 1, 'msg': '塔罗引擎不可用', 'data': None}), 503
    """塔罗牌抽牌 API — 纯Python本地计算，secrets真随机无放回抽牌

    请求参数（POST JSON）：
        spread_name: str, 必填, 牌阵名称 (three/time_flow/hexagram/celtic_cross/relationship/single)
        enable_reversed: bool, 可选, 是否开启正逆位, 默认True

    返回格式：
        {
            "code": 0,
            "msg": "success",
            "data": {
                "spread": {...},
                "cards": [{...}],
                "draw_time": "...",
                "deck_info": {...}
            }
        }
    """
    data = request.get_json(silent=True) or {}
    spread_name = (data.get('spread_name') or '').strip()
    enable_reversed = data.get('enable_reversed', True)

    if not spread_name:
        return jsonify({
            'code': 1,
            'msg': '缺少必填参数: spread_name',
            'data': None,
            'available_spreads': _tarot_spreads(),
        }), 400

    try:
        result = _tarot_draw(spread_name=spread_name, enable_reversed=enable_reversed)
        return jsonify(result)
    except ValueError as e:
        return jsonify({
            'code': 2,
            'msg': str(e),
            'data': None,
            'available_spreads': _tarot_spreads(),
        }), 400
    except Exception as e:
        return jsonify({
            'code': 3,
            'msg': f'抽牌计算失败: {str(e)}',
            'data': None,
        }), 500


@app.route('/api/tarot/draw', methods=['GET'])
def api_tarot_draw_get():
    if not HAS_TAROT:
        return jsonify({'code': 1, 'msg': '塔罗引擎不可用', 'data': None}), 503
    """塔罗牌抽牌 — GET 版本（方便测试，默认无牌阵三张）"""
    spread_name = request.args.get('spread_name', 'three')
    enable_reversed = request.args.get('enable_reversed', 'true').lower() == 'true'

    try:
        result = _tarot_draw(spread_name=spread_name, enable_reversed=enable_reversed)
        return jsonify(result)
    except ValueError as e:
        return jsonify({'code': 2, 'msg': str(e), 'data': None}), 400


@app.route('/api/tarot/spreads')
def api_tarot_spreads():
    if not HAS_TAROT:
        return jsonify({'code': 1, 'msg': '塔罗引擎不可用', 'data': None}), 503
    """获取所有可用牌阵信息"""
    return jsonify({
        'code': 0,
        'msg': 'success',
        'data': _tarot_spreads(),
    })


@app.route('/api/tarot/verify')
def api_tarot_verify():
    if not HAS_TAROT:
        return jsonify({'code': 1, 'msg': '塔罗引擎不可用', 'data': None}), 503
    """塔罗牌牌库完整性校验"""
    result = _tarot_verify()
    return jsonify(result)


@app.route('/api/tarot/reading/stream', methods=['POST'])
@login_required
def api_tarot_reading_stream():
    """流式调用 DeepSeek 进行塔罗牌 AI 解读（SSE）"""
    if not deepseek_available():
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': 'AI 服务未配置'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    data = request.get_json(silent=True) or {}
    cards = data.get('cards') or []
    question = (data.get('question') or '').strip()
    spread_name = data.get('spread_name', '')
    history = data.get('history') or []   # 追问模式的历史对话

    is_followup = not cards and history

    if not question:
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': '请输入问题'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    # 追踪模式不需要 cards，首轮需要
    if not is_followup and not cards:
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': '缺少牌面数据'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    # 扣积分：首轮 5 分，追问 1 分
    cost = 1 if is_followup else 5
    spend = use_points(current_user.id, 'tarot_reading', cost, '塔罗牌 AI ' + ('追问' if is_followup else '解读'))
    if not spend.get('ok'):
        def err_gen():
            yield f"event: error\ndata: {json.dumps({'message': f'积分不足（需要 {cost} 积分），每日签到可获取积分'})}\n\n"
        return Response(err_gen(), mimetype='text/event-stream')

    def generate():
        yield f"event: progress\ndata: {json.dumps({'stage': 'connecting'})}\n\n"
        yield f"event: progress\ndata: {json.dumps({'stage': 'analyzing'})}\n\n"
        yield f"event: progress\ndata: {json.dumps({'stage': 'generating'})}\n\n"

        full_text = ""
        try:
            if is_followup:
                stream = get_tarot_followup_stream(history, question)
            else:
                stream = get_tarot_reading_stream(cards, question, spread_name)
            for chunk, error in stream:
                if error:
                    yield f"event: error\ndata: {json.dumps({'message': error})}\n\n"
                    return
                if chunk:
                    full_text += chunk
                    yield f"event: chunk\ndata: {json.dumps({'content': chunk})}\n\n"
            yield f"event: done\ndata: {json.dumps({'length': len(full_text)})}\n\n"
        except Exception as e:
            logger.error(f"塔罗 AI 解读异常: {e}")
            yield f"event: error\ndata: {json.dumps({'message': 'AI 服务暂时不可用，请稍后重试'})}\n\n"

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


# ─── 塔罗对话历史 API ───

@app.route('/api/tarot/conversations', methods=['GET'])
@login_required
def api_tarot_conversations():
    """获取当前用户的对话列表"""
    convs = TarotConversation.query.filter_by(user_id=current_user.id)\
        .order_by(TarotConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id, 'title': c.title, 'spread_name': c.spread_name,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])

@app.route('/api/tarot/conversations', methods=['POST'])
@login_required
def api_tarot_conversations_create():
    """创建/更新对话"""
    data = request.get_json(silent=True) or {}
    conv_id = data.get('id')
    messages = data.get('messages') or []
    if conv_id:
        conv = TarotConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
        if conv:
            conv.messages_json = json.dumps(messages)
            conv.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'id': conv.id, 'ok': True})
    # 新建
    conv = TarotConversation(
        user_id=current_user.id,
        title=data.get('title', '')[:100],
        spread_name=data.get('spread_name', ''),
        cards_json=json.dumps(data.get('cards') or []),
        messages_json=json.dumps(messages),
    )
    db.session.add(conv)
    db.session.commit()
    return jsonify({'id': conv.id, 'ok': True})

@app.route('/api/tarot/conversations/<int:cid>', methods=['GET'])
@login_required
def api_tarot_conversation_detail(cid):
    conv = TarotConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id, 'title': conv.title, 'spread_name': conv.spread_name,
        'cards': json.loads(conv.cards_json) if conv.cards_json else [],
        'messages': json.loads(conv.messages_json) if conv.messages_json else [],
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
    })

@app.route('/api/tarot/conversations/<int:cid>', methods=['DELETE'])
@login_required
def api_tarot_conversation_delete(cid):
    conv = TarotConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})


# ─── 六爻对话历史 API ───

@app.route('/api/liuyao/conversations', methods=['GET'])
@login_required
def api_liuyao_conversations():
    """获取当前用户的六爻对话列表"""
    convs = LiuyaoConversation.query.filter_by(user_id=current_user.id)\
        .order_by(LiuyaoConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id, 'title': c.title,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])


@app.route('/api/liuyao/conversations', methods=['POST'])
@login_required
def api_liuyao_conversations_create():
    """创建/更新六爻对话"""
    data = request.get_json(silent=True) or {}
    conv_id = data.get('id')
    messages = data.get('messages') or []
    if conv_id:
        conv = LiuyaoConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
        if conv:
            conv.messages_json = json.dumps(messages)
            conv.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'id': conv.id, 'ok': True})
    conv = LiuyaoConversation(
        user_id=current_user.id,
        title=(data.get('title') or '')[:100],
        scene_type=(data.get('scene_type') or '')[:40],
        liuyao_data=json.dumps(data.get('liuyao_data') or {}),
        messages_json=json.dumps(messages),
    )
    db.session.add(conv)
    db.session.commit()
    return jsonify({'id': conv.id, 'ok': True})


@app.route('/api/liuyao/conversations/<int:cid>', methods=['GET'])
@login_required
def api_liuyao_conversation_detail(cid):
    """获取单条六爻对话详情"""
    conv = LiuyaoConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id, 'title': conv.title,
        'messages': json.loads(conv.messages_json) if conv.messages_json else [],
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
    })


@app.route('/api/liuyao/conversations/<int:cid>', methods=['DELETE'])
@login_required
def api_liuyao_conversation_delete(cid):
    """删除六爻对话"""
    conv = LiuyaoConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})


# ─── 梅花易数对话历史 API ───

@app.route('/api/meihua/conversations', methods=['GET'])
@login_required
def api_meihua_conversations():
    """获取当前用户的梅花对话列表"""
    convs = MeihuaConversation.query.filter_by(user_id=current_user.id)\
        .order_by(MeihuaConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id, 'title': c.title,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])


@app.route('/api/meihua/conversations', methods=['POST'])
@login_required
def api_meihua_conversations_create():
    """创建/更新梅花对话"""
    data = request.get_json(silent=True) or {}
    conv_id = data.get('id')
    messages = data.get('messages') or []
    if conv_id:
        conv = MeihuaConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
        if conv:
            conv.messages_json = json.dumps(messages)
            conv.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'id': conv.id, 'ok': True})
    conv = MeihuaConversation(
        user_id=current_user.id,
        title=(data.get('title') or '')[:100],
        method=(data.get('method') or '')[:20],
        meihua_data=json.dumps(data.get('meihua_data') or {}),
        messages_json=json.dumps(messages),
    )
    db.session.add(conv)
    db.session.commit()
    return jsonify({'id': conv.id, 'ok': True})


@app.route('/api/meihua/conversations/<int:cid>', methods=['GET'])
@login_required
def api_meihua_conversation_detail(cid):
    """获取单条梅花对话详情"""
    conv = MeihuaConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id, 'title': conv.title,
        'messages': json.loads(conv.messages_json) if conv.messages_json else [],
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
    })


@app.route('/api/meihua/conversations/<int:cid>', methods=['DELETE'])
@login_required
def api_meihua_conversation_delete(cid):
    """删除梅花对话"""
    conv = MeihuaConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})


# ─── 奇门遁甲对话历史 API ───

@app.route('/api/qimen/conversations', methods=['GET'])
@login_required
def api_qimen_conversations():
    """获取当前用户的奇门对话列表"""
    convs = QimenConversation.query.filter_by(user_id=current_user.id)\
        .order_by(QimenConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id, 'title': c.title,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])


@app.route('/api/qimen/conversations', methods=['POST'])
@login_required
def api_qimen_conversations_create():
    """创建/更新奇门对话"""
    data = request.get_json(silent=True) or {}
    conv_id = data.get('id')
    messages = data.get('messages') or []
    if conv_id:
        conv = QimenConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
        if conv:
            conv.messages_json = json.dumps(messages)
            conv.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'id': conv.id, 'ok': True})
    conv = QimenConversation(
        user_id=current_user.id,
        title=(data.get('title') or '')[:100],
        pan_data=json.dumps(data.get('pan_data') or {}),
        messages_json=json.dumps(messages),
    )
    db.session.add(conv)
    db.session.commit()
    return jsonify({'id': conv.id, 'ok': True})


@app.route('/api/qimen/conversations/<int:cid>', methods=['GET'])
@login_required
def api_qimen_conversation_detail(cid):
    """获取单条奇门对话详情"""
    conv = QimenConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id, 'title': conv.title,
        'pan_data': json.loads(conv.pan_data) if conv.pan_data else {},
        'messages': json.loads(conv.messages_json) if conv.messages_json else [],
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
    })


@app.route('/api/qimen/conversations/<int:cid>', methods=['DELETE'])
@login_required
def api_qimen_conversation_delete(cid):
    """删除奇门对话"""
    conv = QimenConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})


# ─── 八字AI对话历史 API ───

@app.route('/api/bazi/conversations', methods=['GET'])
def api_bazi_conversations():
    convs = BaziConversation.query
    if current_user.is_authenticated:
        convs = convs.filter_by(user_id=current_user.id)
    else:
        convs = convs.filter(BaziConversation.user_id.is_(None))
    convs = convs.order_by(BaziConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id, 'title': c.title,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])


@app.route('/api/bazi/conversations', methods=['POST'])
def api_bazi_conversations_create():
    data = request.get_json(silent=True) or {}
    conv_id = data.get('id')
    messages = data.get('messages') or []
    uid = current_user.id if current_user.is_authenticated else None
    if conv_id:
        query = BaziConversation.query.filter_by(id=conv_id)
        if uid is not None:
            query = query.filter_by(user_id=uid)
        else:
            query = query.filter(BaziConversation.user_id.is_(None))
        conv = query.first()
        if conv:
            conv.messages_json = json.dumps(messages)
            conv.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'id': conv.id, 'ok': True})
    conv = BaziConversation(
        user_id=uid,
        title=(data.get('title') or '')[:100],
        birth_data=json.dumps(data.get('birth_data') or {}),
        messages_json=json.dumps(messages),
    )
    db.session.add(conv)
    db.session.commit()
    return jsonify({'id': conv.id, 'ok': True})


@app.route('/api/bazi/conversations/<int:cid>', methods=['GET'])
def api_bazi_conversation_detail(cid):
    query = BaziConversation.query.filter_by(id=cid)
    if current_user.is_authenticated:
        query = query.filter_by(user_id=current_user.id)
    else:
        query = query.filter(BaziConversation.user_id.is_(None))
    conv = query.first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id, 'title': conv.title,
        'birth_data': json.loads(conv.birth_data) if conv.birth_data else {},
        'messages': json.loads(conv.messages_json) if conv.messages_json else [],
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
    })


@app.route('/api/bazi/conversations/<int:cid>', methods=['DELETE'])
def api_bazi_conversation_delete(cid):
    query = BaziConversation.query.filter_by(id=cid)
    if current_user.is_authenticated:
        query = query.filter_by(user_id=current_user.id)
    else:
        query = query.filter(BaziConversation.user_id.is_(None))
    conv = query.first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})


# ─── 紫微斗数对话历史 API ───

@app.route('/api/ziwei/conversations', methods=['GET'])
@login_required
def api_ziwei_conversations():
    convs = ZiweiConversation.query.filter_by(user_id=current_user.id)\
        .order_by(ZiweiConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id, 'title': c.title,
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])


@app.route('/api/ziwei/conversations', methods=['POST'])
@login_required
def api_ziwei_conversations_create():
    data = request.get_json(silent=True) or {}
    conv_id = data.get('id')
    messages = data.get('messages') or []
    if conv_id:
        conv = ZiweiConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
        if conv:
            conv.messages_json = json.dumps(messages)
            conv.updated_at = datetime.utcnow()
            db.session.commit()
            return jsonify({'id': conv.id, 'ok': True})
    conv = ZiweiConversation(
        user_id=current_user.id,
        title=(data.get('title') or '')[:100],
        birth_data=json.dumps(data.get('birth_data') or {}),
        messages_json=json.dumps(messages),
    )
    db.session.add(conv)
    db.session.commit()
    return jsonify({'id': conv.id, 'ok': True})


@app.route('/api/ziwei/conversations/<int:cid>', methods=['GET'])
@login_required
def api_ziwei_conversation_detail(cid):
    conv = ZiweiConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id, 'title': conv.title,
        'birth_data': json.loads(conv.birth_data) if conv.birth_data else {},
        'messages': json.loads(conv.messages_json) if conv.messages_json else [],
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
    })


@app.route('/api/ziwei/conversations/<int:cid>', methods=['DELETE'])
@login_required
def api_ziwei_conversation_delete(cid):
    conv = ZiweiConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})


# ─── 首页综合 AI 对话历史与流式问答 API ───

def _json_loads_safe(text, default):
    try:
        return json.loads(text) if text else default
    except Exception:
        return default


def _profile_to_comprehensive_dict(profile):
    meta = _json_loads_safe(getattr(profile, 'meta_json', ''), {})
    return {
        'id': profile.id,
        'name': profile.name,
        'gender': profile.gender,
        'cal_type': profile.cal_type,
        'birth_time': profile.birth_time,
        'birth_addr': profile.birth_addr,
        'profile_type': profile.profile_type or 'self',
        'source': getattr(profile, 'source', '') or 'manual',
        'source_record_id': getattr(profile, 'source_record_id', None),
        'meta': meta,
    }


def resolve_comprehensive_profile(data):
    profile_id = data.get('profile_id')
    if profile_id:
        prof = UserProfile.query.filter_by(id=profile_id, user_id=current_user.id).first()
        if not prof:
            raise ValueError('命盘档案不存在')
        prof.last_used_at = datetime.utcnow()
        db.session.commit()
        return _profile_to_comprehensive_dict(prof)

    profile = data.get('profile') or {}
    return {
        'name': profile.get('name') or '未命名',
        'gender': profile.get('gender') or '男',
        'cal_type': profile.get('cal_type') or profile.get('calType') or '公历',
        'birth_time': profile.get('birth_time') or profile.get('birthTime') or '',
        'birth_addr': profile.get('birth_addr') or profile.get('birthAddr') or '',
        'profile_type': profile.get('profile_type') or profile.get('profileType') or 'self',
        'meta': profile.get('meta') or {},
    }


def resolve_comprehensive_profiles(data):
    profiles = data.get('profiles')
    if isinstance(profiles, list) and profiles:
        result = []
        for item in profiles[:5]:
            if not isinstance(item, dict):
                continue
            item_data = {'profile': item}
            if item.get('source') == 'profile' and item.get('id'):
                item_data['profile_id'] = item.get('id')
            result.append(resolve_comprehensive_profile(item_data))
        if result:
            return result
    return [resolve_comprehensive_profile(data)]


def _split_birth_time(birth_time):
    raw = ''.join(ch for ch in str(birth_time or '') if ch.isdigit())
    if len(raw) < 8:
        raise ValueError('命盘档案缺少出生年月日')
    return (
        int(raw[0:4]),
        int(raw[4:6]),
        int(raw[6:8]),
        int(raw[8:10]) if len(raw) >= 10 else 0,
        int(raw[10:12]) if len(raw) >= 12 else 0,
    )


def build_bazi_context_from_profile(profile):
    from bazi_engine import paipan as bazi_paipan
    meta = profile.get('meta') or {}
    result = bazi_paipan(
        profile.get('name') or '未命名',
        profile.get('gender') or '男',
        profile.get('birth_time') or '',
        profile.get('cal_type') or '公历',
        profile.get('birth_addr') or '',
        is_dst=bool(meta.get('isDst', False)),
        night_zi_mode=meta.get('nightZiMode', '夜子时不换日'),
        sizi_pillars=meta.get('siziPillars'),
        use_solar_time=bool(meta.get('useSolarTime', True)),
        is_leap_month=bool(meta.get('isLeapMonth', False)),
        longitude=meta.get('birthLng') if meta.get('birthLng') else None,
    )
    if not result.get('success'):
        return {'error': result.get('error') or '八字排盘失败'}
    context = dict(result)
    context.update({
        'name': profile.get('name') or '未命名',
        'gender': profile.get('gender') or '男',
        'birth_time': profile.get('birth_time') or '',
        'cal_type': profile.get('cal_type') or '公历',
        'birth_addr': profile.get('birth_addr') or '',
        'four_pillars': result.get('four_pillars') or {},
        'day_master': result.get('day_master') or result.get('ri_gan') or '',
        'wuxing_stats': result.get('wuxing_stats') or result.get('five_elements') or {},
        'strength': result.get('strength') or result.get('day_master_strength') or '',
        'yongshen': result.get('yongshen') or result.get('useful_god') or '',
        'dayun': result.get('dayun') or result.get('luck_pillars') or result.get('da_yun') or [],
    })
    return context


def build_ziwei_context_from_profile(profile):
    if not HAS_ZIWEI:
        return {'error': '紫微斗数引擎不可用'}
    meta = profile.get('meta') or {}
    year, month, day, hour, minute = _split_birth_time(profile.get('birth_time'))
    date_type = 'lunar' if profile.get('cal_type') == '农历' else 'solar'
    result = _zw_engine.calculate(
        year=year,
        month=month,
        day=day,
        hour=hour,
        minute=minute,
        gender=profile.get('gender') or '男',
        date_type=date_type,
        longitude=meta.get('birthLng') if meta.get('birthLng') else None,
    )
    context = dict(result or {})
    context.update({
        'name': profile.get('name') or '未命名',
        'gender': profile.get('gender') or '男',
        'birth_time': profile.get('birth_time') or '',
        'cal_type': profile.get('cal_type') or '公历',
        'birth_addr': profile.get('birth_addr') or '',
    })
    return context


def _compress_qimen_value(value):
    if isinstance(value, list):
        return '、'.join([str(item) for item in value if item])
    return value


def build_qimen_context_from_question(question=''):
    now = datetime.now()
    result = _qimen_paipan(now.year, now.month, now.day, now.hour, now.minute, 1)
    if result.get('error'):
        return {'error': result.get('error')}
    context = dict(result or {})
    context['question'] = question or ''
    return context


def build_liuyao_context_from_question(question=''):
    result = _liuyao_paipan(mode='auto', question=question or '')
    if result.get('error'):
        return {'error': result.get('error')}
    context = dict(result or {})
    context['question'] = result.get('question') or question or ''
    return context


def build_meihua_context_from_question(question=''):
    result = _meihua_paipan(method='time')
    if result.get('error'):
        return {'error': result.get('error')}
    return {
        'question': question or '',
        'method_label': result.get('methodLabel'),
        'paipan_time': result.get('paipanTime'),
        'ganzhi': result.get('ganzhi'),
        'dong_yao': result.get('dongYao'),
        'ben_gua': result.get('benGua'),
        'ben_gua_yao': result.get('benGuaYao'),
        'benGuaYao': result.get('benGuaYao'),
        'hu_gua': result.get('huGua'),
        'hu_gua_yao': result.get('huGuaYao'),
        'huGuaYao': result.get('huGuaYao'),
        'bian_gua': result.get('bianGua'),
        'bian_gua_yao': result.get('bianGuaYao'),
        'bianGuaYao': result.get('bianGuaYao'),
        'ti_yong': result.get('tiYong'),
    }


def build_tarot_context_from_question(question=''):
    if not _tarot_draw:
        return {'error': '塔罗引擎不可用'}
    q = str(question or '')
    spread_name = 'three'
    if any(k in q for k in ['是', '否', '能不能', '要不要']):
        spread_name = 'single'
    elif any(k in q for k in ['关系', '感情', '复合', '回来']):
        spread_name = 'relationship'
    result = _tarot_draw(spread_name=spread_name, enable_reversed=True)
    payload = result.get('data') if isinstance(result, dict) else {}
    if not isinstance(payload, dict):
        payload = result if isinstance(result, dict) else {}
    return {
        'question': q,
        'spread_name': spread_name,
        'spread': payload.get('spread') or {},
        'cards': payload.get('cards') or [],
        'draw_time': payload.get('draw_time'),
        'deck_info': payload.get('deck_info') or {},
    }


def build_zeji_context_from_question(question=''):
    q = str(question or '')
    zeji_type = '择吉'
    for item in ['婚嫁', '开业', '搬家', '出行', '签约', '动土', '入宅', '领证', '装修']:
        if item in q:
            zeji_type = '搬家' if item == '入宅' else item
            break
    start_dt = datetime.now()
    days = []
    for offset in range(0, 15):
        cursor = start_dt + timedelta(days=offset)
        h = _compute_huangli_local(cursor.year, cursor.month, cursor.day)
        score, reasons, warnings = _score_zeji_day(zeji_type, h)
        days.append({
            'date': cursor.strftime('%Y-%m-%d'),
            'lunar': h.get('lunarDate'),
            'gan_zhi_day': h.get('ganZhiDay'),
            'jian_chu': h.get('jianChu'),
            'zhi_shen': h.get('zhiShen'),
            'score': score,
            'reasons': reasons[:3],
            'warnings': warnings[:3],
        })
    return {
        'question': q,
        'zeji_type': zeji_type,
        'range': '未来15日',
        'best_days': sorted(days, key=lambda x: x['score'], reverse=True)[:5],
    }


_TOOL_DISPLAY = {'bazi': '八字', 'ziwei': '紫微斗数', 'qimen': '奇门遁甲', 'liuyao': '六爻', 'meihua': '梅花易数', 'tarot': '塔罗牌', 'zeji': '择吉工具'}


def _build_one_tool(tool, profile, question):
    try:
        if tool == 'bazi':
            return tool, build_bazi_context_from_profile(profile)
        elif tool == 'ziwei':
            return tool, build_ziwei_context_from_profile(profile)
        elif tool == 'qimen':
            return tool, build_qimen_context_from_question(question)
        elif tool == 'liuyao':
            return tool, build_liuyao_context_from_question(question)
        elif tool == 'meihua':
            return tool, build_meihua_context_from_question(question)
        elif tool == 'tarot':
            return tool, build_tarot_context_from_question(question)
        elif tool == 'zeji':
            return tool, build_zeji_context_from_question(question)
    except Exception as exc:
        return tool, {'error': str(exc)}
    return tool, None


def build_single_comprehensive_paipan_context(profile, tool_models, question=''):
    if len(tool_models) <= 1:
        context = {}
        for t, v in [_build_one_tool(tool_models[0], profile, question)] if tool_models else []:
            if v is not None:
                context[t] = v
        return context
    context = {}
    with ThreadPoolExecutor(max_workers=min(len(tool_models), 5)) as pool:
        futures = [pool.submit(_build_one_tool, t, profile, question) for t in tool_models]
        for f in as_completed(futures):
            t, v = f.result()
            if v is not None:
                context[t] = v
    return context


def build_comprehensive_paipan_context(profiles, tool_models, question=''):
    profile_list = profiles if isinstance(profiles, list) else [profiles]
    if len(profile_list) == 1:
        return build_single_comprehensive_paipan_context(profile_list[0], tool_models, question)
    results = [None] * len(profile_list)
    with ThreadPoolExecutor(max_workers=min(len(profile_list), 4)) as pool:
        futures = {pool.submit(build_single_comprehensive_paipan_context, p, tool_models, question): i for i, p in enumerate(profile_list)}
        for f in as_completed(futures):
            idx = futures[f]
            results[idx] = {'profile': profile_list[idx], 'paipan': f.result()}
    return {'profiles': results}


def _unwrap_comprehensive_paipan(paipan_payload):
    if isinstance(paipan_payload, dict) and ('paipan' in paipan_payload or 'artifacts' in paipan_payload):
        return paipan_payload.get('paipan') or {}, paipan_payload.get('artifacts') or {}
    return paipan_payload or {}, {}


def _artifact_key_for_tool(tool):
    return {
        'bazi': 'bazi.basic',
        'ziwei': 'ziwei.pan',
        'qimen': 'qimen.pan',
        'liuyao': 'liuyao.pan',
        'meihua': 'meihua.pan',
        'tarot': 'tarot.cards',
        'zeji': 'zeji.days',
    }.get(tool, tool + '.pan')


def _ordered_artifact_keys_for_tools(tool_models, include_yun=False):
    keys = []
    ordered = sorted(tool_models or [], key=lambda x: TOOL_DISPLAY_ORDER.index(x) if x in TOOL_DISPLAY_ORDER else 99)
    for tool in ordered:
        key = _artifact_key_for_tool(tool)
        if key not in keys:
            keys.append(key)
        if include_yun and tool == 'bazi' and 'bazi.yun' not in keys:
            keys.append('bazi.yun')
    return keys


def _artifact_display_for_key(key):
    return {
        'bazi.basic': 'bazi_basic',
        'bazi.yun': 'bazi_yun',
        'ziwei.pan': 'ziwei_pan',
        'qimen.pan': 'qimen_pan',
        'liuyao.pan': 'liuyao_pan',
        'meihua.pan': 'meihua_pan',
        'tarot.cards': 'tarot_cards',
        'zeji.days': 'zeji_days',
    }.get(key, 'generic')


def _artifact_title_for_key(key):
    return {
        'bazi.basic': '八字基本排盘',
        'bazi.yun': '大运流年流月',
        'ziwei.pan': '紫微斗数三合盘',
        'qimen.pan': '奇门遁甲盘',
        'liuyao.pan': '六爻排盘',
        'meihua.pan': '梅花易数卦盘',
        'tarot.cards': '塔罗牌面',
        'zeji.days': '择吉候选',
    }.get(key, key)


def _question_needs_yun(question):
    text = str(question or '')
    return any(k in text for k in ['发财', '正缘', '结婚', '婚期', '哪年', '什么时候', '今年', '明年', '运势', '年运', '流年', '流月', '大运', '应期', '机会'])


def _question_force_refresh(question, force_refresh=False):
    text = str(question or '')
    return bool(force_refresh) or any(k in text for k in ['重新排', '重新看', '换命盘', '换时间', '换术数', '再排'])


def _bazi_yun_data(bazi_context):
    if not isinstance(bazi_context, dict):
        return {}
    return {
        'qi_yun_age': bazi_context.get('qi_yun_age'),
        'qi_yun_detail': bazi_context.get('qi_yun_detail') or {},
        'dayun': bazi_context.get('dayun') or bazi_context.get('da_yun') or [],
        'da_yun': bazi_context.get('da_yun') or bazi_context.get('dayun') or [],
        'liu_nian': bazi_context.get('liu_nian') or [],
        'liu_yue': bazi_context.get('liu_yue') or [],
        'xiao_yun': bazi_context.get('xiao_yun') or [],
        'four_pillars': bazi_context.get('four_pillars') or {},
    }


def _tool_data_from_paipan_context(paipan_context, tool, profile_index=0):
    if not isinstance(paipan_context, dict) or not tool:
        return {}
    direct = paipan_context.get(tool)
    if isinstance(direct, dict):
        return direct
    profiles = paipan_context.get('profiles')
    if isinstance(profiles, list) and profiles:
        idx = profile_index if isinstance(profile_index, int) and profile_index >= 0 else 0
        item = profiles[min(idx, len(profiles) - 1)]
        if isinstance(item, dict):
            paipan = item.get('paipan') or {}
            if isinstance(paipan, dict) and isinstance(paipan.get(tool), dict):
                return paipan.get(tool)
    return {}


def _paipan_context_has_tool(paipan_context, tool):
    return bool(_tool_data_from_paipan_context(paipan_context, tool))


def _artifact_from_context(key, tool, data, reading_mode='standard', collapsed=None):
    if collapsed is None:
        collapsed = reading_mode == 'concise'
    payload = _bazi_yun_data(data) if key == 'bazi.yun' else (data or {})
    return {
        'key': key,
        'tool': tool,
        'display': _artifact_display_for_key(key),
        'title': _artifact_title_for_key(key),
        'collapsed': bool(collapsed),
        'data': payload,
    }


def _select_artifacts_for_context(paipan_context, tool_models, question, existing_artifacts=None, is_followup=False, force_refresh=False, reading_mode='standard'):
    existing = dict(existing_artifacts or {})
    artifacts = dict(existing)
    actions = {'reused': [], 'added': [], 'refreshed': [], 'skipped': []}
    needs_yun = _question_needs_yun(question)
    refresh = _question_force_refresh(question, force_refresh)
    for tool in tool_models or []:
        key = _artifact_key_for_tool(tool)
        tool_data = _tool_data_from_paipan_context(paipan_context, tool)
        if key in existing and is_followup and not refresh:
            actions['reused'].append(key)
        elif tool_data:
            artifacts[key] = _artifact_from_context(key, tool, tool_data, reading_mode=reading_mode)
            actions['refreshed' if key in existing else 'added'].append(key)
        else:
            actions['skipped'].append(key)

    bazi_data = _tool_data_from_paipan_context(paipan_context, 'bazi')
    if needs_yun and ('bazi' in (tool_models or []) or 'bazi.basic' in artifacts):
        key = 'bazi.yun'
        if key in existing and is_followup and not refresh:
            actions['reused'].append(key)
        elif bazi_data:
            artifacts[key] = _artifact_from_context(key, 'bazi', bazi_data, reading_mode=reading_mode, collapsed=False)
            actions['refreshed' if key in existing else 'added'].append(key)
        else:
            actions['skipped'].append(key)
    return artifacts, actions


def _comprehensive_summary_only(text):
    """旧综合历史曾把单盘解析拼进正文；展示时只保留最终合参总结。"""
    raw = str(text or '')
    markers = ['【综合合参总结】', '综合合参总结：', '综合合参总结']
    for marker in markers:
        idx = raw.rfind(marker)
        if idx >= 0:
            return raw[idx + len(marker):].strip()
    return raw.strip()


def _clean_comprehensive_messages_for_display(messages):
    cleaned = []
    for item in messages or []:
        if not isinstance(item, dict):
            continue
        next_item = dict(item)
        if next_item.get('role') == 'assistant':
            next_item['content'] = _comprehensive_summary_only(next_item.get('content', ''))
        cleaned.append(next_item)
    return cleaned


def save_comprehensive_conversation(data, question, profile, tool_models, paipan_context, artifacts, model_id, cost, history, answer):
    messages = list(history or [])
    messages.append({'role': 'user', 'content': question})
    messages.append({'role': 'assistant', 'content': _comprehensive_summary_only(answer)})
    conv_id = data.get('conversation_id')
    conv = None
    if conv_id:
        conv = ComprehensiveConversation.query.filter_by(id=conv_id, user_id=current_user.id).first()
    if not conv:
        conv = ComprehensiveConversation(user_id=current_user.id, created_at=datetime.utcnow())
        db.session.add(conv)
    conv.title = (data.get('title') or question or '综合 AI 问答')[:100]
    conv.profile_data = json.dumps(profile or {}, ensure_ascii=False)
    conv.models_json = json.dumps(tool_models or [], ensure_ascii=False)
    conv.paipan_json = json.dumps({'paipan': paipan_context or {}, 'artifacts': artifacts or {}}, ensure_ascii=False)
    conv.model_id = model_id
    conv.points_cost = cost
    conv.messages_json = json.dumps(messages, ensure_ascii=False)
    conv.updated_at = datetime.utcnow()
    db.session.commit()
    return conv


def spend_comprehensive_quota(user_id, tool_models, cost, is_followup=False):
    membership = get_or_create_membership(user_id)
    today = datetime.utcnow().strftime('%Y-%m-%d')
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
    if not is_followup:
        if len(tool_models or []) > 1 and int(membership.ai_combo_credits or 0) > 0:
            membership.ai_combo_credits = int(membership.ai_combo_credits or 0) - 1
            db.session.add(PointLog(user_id=user_id, action='ai_combo_credit_use', points=0, description='首页多术数合参次数 -1'))
            db.session.commit()
            return {'ok': True, 'points': membership.points, 'used_credit': 'ai_combo_credits', 'used': 1}
        if len(tool_models or []) == 1 and int(membership.ai_single_credits or 0) > 0:
            membership.ai_single_credits = int(membership.ai_single_credits or 0) - 1
            db.session.add(PointLog(user_id=user_id, action='ai_single_credit_use', points=0, description='首页单术数 AI 次数 -1'))
            db.session.commit()
            return {'ok': True, 'points': membership.points, 'used_credit': 'ai_single_credits', 'used': 1}
    spend = use_points(user_id, 'comprehensive_ai', cost, '综合 AI ' + ('追问' if is_followup else '解读'))
    spend['used_credit'] = 'points' if spend.get('ok') else ''
    return spend


@app.route('/api/comprehensive/options')
@login_required
def api_comprehensive_options():
    membership = get_or_create_membership(current_user.id)
    return jsonify({
        'llm_models': COMPREHENSIVE_LLM_MODELS,
        'tool_models': COMPREHENSIVE_TOOL_MODELS,
        'points': membership.points,
        'ai_single_credits': int(membership.ai_single_credits or 0),
        'ai_combo_credits': int(membership.ai_combo_credits or 0),
        'daily_light_available': membership.daily_ai_light_used_at != datetime.utcnow().strftime('%Y-%m-%d'),
    })


@app.route('/api/comprehensive/recommend-tools', methods=['POST'])
@login_required
def api_comprehensive_recommend_tools():
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    tools, reason = recommend_tool_models(question)
    model_id = data.get('llm_model') or 'basic'
    profile_count = max(1, int(data.get('profile_count') or 1))
    return jsonify({
        'tool_models': tools,
        'reason': reason,
        'estimated_cost': calculate_cost(model_id, tools, is_followup=False, profile_count=profile_count),
    })


@app.route('/api/comprehensive/conversations', methods=['GET'])
@login_required
def api_comprehensive_conversations():
    convs = ComprehensiveConversation.query.filter_by(user_id=current_user.id)\
        .order_by(ComprehensiveConversation.updated_at.desc()).all()
    return jsonify([{
        'id': c.id,
        'title': c.title,
        'model_id': c.model_id,
        'models': _json_loads_safe(c.models_json, []),
        'created_at': c.created_at.isoformat() if c.created_at else None,
        'updated_at': c.updated_at.isoformat() if c.updated_at else None,
    } for c in convs])


@app.route('/api/comprehensive/conversations/<int:cid>', methods=['GET'])
@login_required
def api_comprehensive_conversation_detail(cid):
    conv = ComprehensiveConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    return jsonify({
        'id': conv.id,
        'title': conv.title,
        'profile_data': _json_loads_safe(conv.profile_data, {}),
        'models': _json_loads_safe(conv.models_json, []),
        'paipan': _unwrap_comprehensive_paipan(_json_loads_safe(conv.paipan_json, {}))[0],
        'artifacts': _unwrap_comprehensive_paipan(_json_loads_safe(conv.paipan_json, {}))[1],
        'model_id': conv.model_id,
        'points_cost': conv.points_cost,
        'messages': _clean_comprehensive_messages_for_display(_json_loads_safe(conv.messages_json, [])),
        'created_at': conv.created_at.isoformat() if conv.created_at else None,
        'updated_at': conv.updated_at.isoformat() if conv.updated_at else None,
    })


@app.route('/api/comprehensive/conversations/<int:cid>', methods=['DELETE'])
@login_required
def api_comprehensive_conversation_delete(cid):
    conv = ComprehensiveConversation.query.filter_by(id=cid, user_id=current_user.id).first()
    if not conv:
        return jsonify({'error': '对话不存在'}), 404
    db.session.delete(conv)
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/comprehensive/ask/stream', methods=['POST'])
@login_required
def api_comprehensive_ask_stream():
    data = request.get_json(silent=True) or {}
    question = (data.get('question') or '').strip()
    history = data.get('history') or []
    reading_mode = data.get('reading_mode') or 'standard'
    if reading_mode not in ('concise', 'standard', 'deep'):
        reading_mode = 'standard'
    force_refresh = bool(data.get('force_refresh', False))
    auto_select_tools = bool(data.get('auto_select_tools', False))
    if auto_select_tools or not data.get('tool_models'):
        tool_models = normalize_tool_models(recommend_tool_models(question)[0])
    else:
        tool_models = normalize_tool_models(data.get('tool_models') or [])
    model_id = data.get('llm_model') or 'basic'
    is_followup = bool(history)
    requested_profiles = data.get('profiles') if isinstance(data.get('profiles'), list) else None
    profile_count = len(requested_profiles) if requested_profiles else 1
    cost = calculate_cost(model_id, tool_models, is_followup=is_followup, profile_count=profile_count)

    def _event(payload):
        return 'data: %s\n\n' % json.dumps(payload, ensure_ascii=False)

    if not question:
        return Response(_event({'error': '请输入问题'}), mimetype='text/event-stream')
    if not tool_models and not is_followup:
        return Response(_event({'error': '请至少选择一个术数模型'}), mimetype='text/event-stream')

    def generate():
        try:
            yield _event({'stage': 'profile', 'message': '正在读取命盘档案'})
            profiles = resolve_comprehensive_profiles(data)
            profile_count = len(profiles)
            profile = profiles[0] if profile_count == 1 else profiles
            paipan_context, existing_artifacts = _unwrap_comprehensive_paipan(data.get('paipan') or {})
            need_yun = _question_needs_yun(question)
            refresh = _question_force_refresh(question, force_refresh)
            needs_paipan = (not is_followup) or refresh or not paipan_context or (need_yun and not _paipan_context_has_tool(paipan_context, 'bazi'))
            if needs_paipan:
                if profile_count == 1:
                    p = profiles[0]
                    p_name = p.get('name', '未命名') if isinstance(p, dict) else getattr(p, 'name', '未命名')
                    context = {}
                    tool_count = len(tool_models)
                    for ti, tool in enumerate(tool_models):
                        t_name = _TOOL_DISPLAY.get(tool, tool)
                        yield _event({'stage': 'paipan', 'message': '正在排盘 %s 的%s (%d/%d)' % (p_name, t_name, ti + 1, tool_count)})
                        _, v = _build_one_tool(tool, p, question)
                        if v is not None:
                            context[tool] = v
                        yield _event({'stage': 'paipan_progress', 'message': '%s 的%s 排盘完成 (%d/%d)' % (p_name, t_name, ti + 1, tool_count)})
                    paipan_context = context
                else:
                    all_tasks = []
                    for pi, p in enumerate(profiles):
                        p_name = p.get('name', '未命名') if isinstance(p, dict) else getattr(p, 'name', '未命名')
                        for tool in tool_models:
                            all_tasks.append((pi, p, p_name, tool))
                    total = len(all_tasks)
                    yield _event({'stage': 'paipan', 'message': '正在并行排盘 %d 个命盘 × %d 种术数 (共 %d 项)' % (profile_count, len(tool_models), total)})
                    task_results = {}
                    with ThreadPoolExecutor(max_workers=min(total, 6)) as pool:
                        future_map = {}
                        for pi, p, p_name, tool in all_tasks:
                            f = pool.submit(_build_one_tool, tool, p, question)
                            future_map[f] = (pi, p_name, tool)
                        done_count = 0
                        for f in as_completed(future_map):
                            pi, p_name, tool = future_map[f]
                            t_name = _TOOL_DISPLAY.get(tool, tool)
                            _, v = f.result()
                            task_results.setdefault(pi, {})[tool] = v if v is not None else {}
                            done_count += 1
                            yield _event({'stage': 'paipan_progress', 'message': '%s 的%s 排盘完成 (%d/%d)' % (p_name, t_name, done_count, total)})
                    profile_results = []
                    for pi, p in enumerate(profiles):
                        profile_results.append({'profile': p, 'paipan': task_results.get(pi, {})})
                    paipan_context = {'profiles': profile_results}
            artifacts, artifact_actions = _select_artifacts_for_context(
                paipan_context,
                tool_models,
                question,
                existing_artifacts=existing_artifacts,
                is_followup=is_followup,
                force_refresh=refresh,
                reading_mode=reading_mode,
            )
            yield _event({
                'stage': 'paipan_done',
                'message': '盘面依据已准备，正在准备解读',
                'paipan': paipan_context,
                'artifacts': artifacts,
                'artifact_actions': artifact_actions,
                'tool_models': tool_models,
            })
            spend = spend_comprehensive_quota(current_user.id, tool_models, cost, is_followup=is_followup)
            if not spend.get('ok'):
                yield _event({'error': '积分不足', 'current': spend.get('current'), 'required': cost})
                return
            full_text = ''
            tool_analyses = {}
            ordered_tools = sorted(tool_models or [], key=lambda x: TOOL_DISPLAY_ORDER.index(x) if x in TOOL_DISPLAY_ORDER else 99)
            for tool in ordered_tools:
                tool_data = _tool_data_from_paipan_context(paipan_context, tool)
                key = _artifact_key_for_tool(tool)
                tool_name = _TOOL_DISPLAY.get(tool, tool)
                yield _event({
                    'stage': 'tool_analysis_start',
                    'message': '正在解读%s' % tool_name,
                    'tool': tool,
                    'tool_key': key,
                })
                tool_messages = build_tool_analysis_messages(question, profile, tool, tool_data, history)
                tool_text = ''
                full_text += '\n\n【%s解析】\n' % tool_name
                for chunk, error in get_reading_stream(tool_messages):
                    if error:
                        yield _event({'error': error})
                        return
                    if chunk:
                        tool_text += chunk
                        full_text += chunk
                        yield _event({'tool': tool, 'tool_key': key, 'content': chunk})
                tool_analyses[tool] = tool_text
                if key in artifacts:
                    artifacts[key]['analysis'] = tool_text
                yield _event({
                    'stage': 'tool_analysis_done',
                    'message': '%s解读完成' % tool_name,
                    'tool': tool,
                    'tool_key': key,
                })

                if tool == 'bazi' and 'bazi.yun' in artifacts:
                    yield _event({
                        'stage': 'tool_analysis_start',
                        'message': '正在结合大运流年流月',
                        'tool': tool,
                        'tool_key': 'bazi.yun',
                    })
                    yun_messages = build_tool_analysis_messages(question, profile, 'bazi', (artifacts.get('bazi.yun') or {}).get('data') or tool_data, history)
                    yun_text = ''
                    full_text += '\n\n【大运流年流月解析】\n'
                    for chunk, error in get_reading_stream(yun_messages):
                        if error:
                            yield _event({'error': error})
                            return
                        if chunk:
                            yun_text += chunk
                            full_text += chunk
                            yield _event({'tool': tool, 'tool_key': 'bazi.yun', 'content': chunk})
                    tool_analyses['bazi.yun'] = yun_text
                    if 'bazi.yun' in artifacts:
                        artifacts['bazi.yun']['analysis'] = yun_text

            yield _event({'stage': 'generating', 'message': '正在生成综合合参总结', 'summary_start': True})
            summary_messages = build_summary_messages(question, profile, ordered_tools, tool_analyses, history)
            summary_text = ''
            full_text += '\n\n【综合合参总结】\n'
            for chunk, error in get_reading_stream(summary_messages):
                if error:
                    yield _event({'error': error})
                    return
                if chunk:
                    summary_text += chunk
                    full_text += chunk
                    yield _event({'summary': True, 'content': chunk})
            conv = save_comprehensive_conversation(data, question, profile, tool_models, paipan_context, artifacts, model_id, cost, history, summary_text)
            points_left = get_or_create_membership(current_user.id).points
            membership = get_or_create_membership(current_user.id)
            yield _event({
                'done': True,
                'conversation_id': conv.id,
                'points_left': points_left,
                'ai_single_credits': int(membership.ai_single_credits or 0),
                'ai_combo_credits': int(membership.ai_combo_credits or 0),
                'used_credit': spend.get('used_credit'),
                'tool_models': tool_models,
                'paipan': paipan_context,
                'artifacts': artifacts,
                'artifact_actions': artifact_actions,
            })
        except Exception as exc:
            logger.exception("综合 AI 生成失败")
            yield _event({'error': '综合解读失败：' + str(exc)[:120]})

    return Response(stream_with_context(generate()), mimetype='text/event-stream',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


# ═══════════════════════════════════════════════════════════════
# 紫微斗数 — SSE 流式 AI 解读
# ═══════════════════════════════════════════════════════════════
_ziwei_ask_current_run = 0
_ziwei_ask_lock = threading.Lock()

@app.route('/api/ziwei/ask/stream', methods=['GET', 'POST'])
@csrf.exempt
def api_ziwei_ask_stream():
    """紫微斗数 SSE 流式 AI 解读。POST=新建任务+流式；GET=读取已有任务"""
    global _ziwei_ask_current_run

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()
        if not question:
            question = '请全面分析我的八字命局'

        gender = data.get('gender', '男')
        date_type = data.get('date_type', 'solar')

        # 参数校验
        for k in ['year', 'month', 'day', 'hour']:
            if k not in data or data[k] is None:
                return jsonify({'error': f'缺少必填参数: {k}'}), 400

        year, month, day, hour = int(data['year']), int(data['month']), int(data['day']), int(data['hour'])
        minute = int(data.get('minute', 0) or 0)
        analysis_type = data.get('analysis_type', '')

        if not HAS_ZIWEI:
            return jsonify({'error': '紫微斗数引擎未安装(iztro-py)'}), 503

        # 排盘
        try:
            pan_data = _zw_engine.calculate(
                year=year, month=month, day=day,
                hour=hour, minute=minute,
                gender=gender,
                date_type=date_type,
            )
        except Exception as e:
            return jsonify({'error': f'排盘失败: {str(e)}'}), 500

        # 生成 run_id（带类型前缀，避免与奇门/六爻等共用数字ID导致目录冲突）
        with _ziwei_ask_lock:
            _ziwei_ask_current_run += 1
            run_id = f"zw_{_ziwei_ask_current_run}"

        run_dir = get_run_dir(run_id)
        with open(os.path.join(run_dir, 'pan.json'), 'w', encoding='utf-8') as f:
            json.dump(pan_data, f, ensure_ascii=False)
        with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
            f.write(question)
        with open(os.path.join(run_dir, 'analysis_type.txt'), 'w') as f:
            f.write(analysis_type)

        write_run_status(run_id, {'phase': 'calculating', 'message': '排盘中...', 'progress': 10, 'run_id': run_id})
        t = threading.Thread(target=_ziwei_ask_task, args=(run_id,), daemon=True)
        t.start()
    else:
        # 紫微 GET：读取已有任务
        run_id = request.args.get('run_id', default='')
        if not run_id:
            return jsonify({'error': '无效的 run_id'}), 400

    # SSE 流式输出（紫微）
    run_dir = get_run_dir(run_id)
    stream_file = os.path.join(run_dir, 'stream.txt')

    def _zw_generate():
        last_size = 0
        while True:
            s = read_run_status(run_id)
            phase = s.get('phase', 'idle')
            try:
                if os.path.exists(stream_file):
                    with open(stream_file, 'r', encoding='utf-8') as f:
                        f.seek(last_size)
                        nc = f.read()
                        if nc:
                            last_size += len(nc.encode('utf-8'))
                            yield f"data: {json.dumps({'type': 'delta', 'content': nc}, ensure_ascii=False)}\n\n"
            except:
                pass
            if phase == 'done':
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                break
            elif phase == 'error':
                yield f"data: {json.dumps({'type': 'error', 'message': s.get('message', '未知错误')}, ensure_ascii=False)}\n\n"
                break
            import time; time.sleep(0.3)

    return Response(_zw_generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive',
    })

def _ziwei_ask_task(run_id):
    """后台线程：构建紫微Prompt → 调用 DeepSeek API → 保存结果"""
    try:
        run_dir = get_run_dir(run_id)
        with open(os.path.join(run_dir, 'pan.json'), 'r', encoding='utf-8') as f:
            pan_data = json.load(f)
        question = open(os.path.join(run_dir, 'question.txt'), 'r', encoding='utf-8').read().strip()
        analysis_type = ''
        try:
            analysis_type = open(os.path.join(run_dir, 'analysis_type.txt'), 'r').read().strip()
        except:
            pass

        write_run_status(run_id, {'phase': 'analyzing', 'message': 'AI解盘中...', 'progress': 30, 'run_id': run_id})

        # 提取命盘摘要
        palaces = []
        for p in (pan_data.get('twelve_palaces') or pan_data.get('palaces') or []):
            name = p.get('name', '')
            all_stars = []
            for s in (p.get('major_stars') or []):
                sn = s.get('name', '') if isinstance(s, dict) else str(s)
                if sn:
                    br = s.get('brightness', '') if isinstance(s, dict) else ''
                    mut = s.get('mutagen', '') if isinstance(s, dict) else ''
                    label = sn
                    if br: label += '(' + br + ')'
                    if mut: label += '[' + mut + ']'
                    all_stars.append(label + '(主星)')
            for s in (p.get('minor_stars') or []):
                sn = s.get('name', '') if isinstance(s, dict) else str(s)
                if sn:
                    br = s.get('brightness', '') if isinstance(s, dict) else ''
                    mut = s.get('mutagen', '') if isinstance(s, dict) else ''
                    label = sn
                    if br: label += '(' + br + ')'
                    if mut: label += '[' + mut + ']'
                    all_stars.append(label)
            for s in (p.get('adjective_stars') or []):
                sn = s.get('name', '') if isinstance(s, dict) else str(s)
                if sn:
                    all_stars.append(sn)
            for s in (p.get('stars') or []):
                sn = s.get('name', '') if isinstance(s, dict) else str(s)
                if sn:
                    br = s.get('brightness', '') if isinstance(s, dict) else ''
                    label = sn
                    if br: label += '(' + br + ')'
                    all_stars.append(label)
            palaces.append(f"{name}: {' '.join(all_stars) if all_stars else '(空宫)'}")

        basic_info = pan_data.get('basic_info', {})
        palace_summary = '\n'.join(palaces)

        core_palace = pan_data.get('core_palace', {})
        core_info = ''
        if core_palace:
            core_info = f"\n命宫详情: {json.dumps(core_palace, ensure_ascii=False)}"

        decadal = pan_data.get('decadal_overview', [])
        decadal_info = ''
        if decadal:
            decadal_info = f"\n大限概览: {json.dumps(decadal, ensure_ascii=False)[:500]}"

        type_hints = {
            'overview': '全面分析命盘格局，从整体角度审视命主的一生运势特点、性格特质和人生轨迹。',
            'career': '重点分析事业财运，包括官禄宫、财帛宫及相关星曜组合，分析其事业运势和财运走势。',
            'love': '重点分析姻缘感情，包括夫妻宫及相关星曜组合，分析其感情状况和姻缘走向。',
            'marriage': '重点分析姻缘感情，包括夫妻宫及相关星曜组合，分析其感情状况和姻缘走向。',
            'health': '重点分析健康运势，包括疾厄宫及相关星曜组合，分析其健康方面的潜在问题和建议。',
            'decadal': '重点分析大限流年，包括当前所处大限、流年运势、四化情况，分析近期运程变化和重要时间节点。',
            'general': '全面分析命盘格局，从整体角度审视命主的一生运势特点、性格特质和人生轨迹。',
        }

        type_desc = type_hints.get(analysis_type, type_hints['general'])
        focus_tip = f'本次分析侧重点：{type_desc}' if analysis_type else ''

        from openai import OpenAI
        import os as _os
        sf_key = _os.environ.get('SILICONFLOW_API_KEY', '')
        sf_url = _os.environ.get('SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1')
        model = _os.environ.get('DEEPSEEK_MODEL_NORMAL', 'deepseek-ai/DeepSeek-V3')
        if sf_key:
            client = OpenAI(api_key=sf_key, base_url=sf_url)
            system_prompt = f"""你是一位精通紫微斗数的资深命理师，经验丰富、底蕴深厚。
{focus_tip}
请根据用户的出生信息和命盘数据，给出专业、有深度、个性化的紫微斗数命理分析。
回答要求：
- 语言自然流畅，像命理师在面对面交流
- 结合命盘具体星曜、宫位来分析，不要泛泛而谈
- 指出关键星曜组合的作用和影响
- 给出建设性建议
- 用 markdown 组织，字数 800-1500 字"""

            user_msg = f"""出生时间：{basic_info.get('birth', '')}
性别：{basic_info.get('gender', '')}
农历：{basic_info.get('lunar_date', '')}
干支：{basic_info.get('chinese_date', '')}
生肖：{basic_info.get('zodiac', '')}
星座：{basic_info.get('sign', '')}
五行局：{basic_info.get('five_elements_class', '')}
时辰：{basic_info.get('shichen', '')} ({basic_info.get('shichen_range', '')})
用户问题：{question}

命盘十二宫：
{palace_summary}
{core_info}
{decadal_info}

请根据以上信息给出详细解析。"""

            write_run_status(run_id, {'phase': 'streaming', 'message': '生成解答中...', 'progress': 50, 'run_id': run_id})
            response = client.chat.completions.create(
                model=model, messages=[
                    {'role': 'system', 'content': system_prompt},
                    {'role': 'user', 'content': user_msg}
                ], temperature=0.8, max_tokens=3072, stream=True
            )

            full_text = ''
            with open(os.path.join(run_dir, 'stream.txt'), 'w', encoding='utf-8') as sf:
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        full_text += text
                        sf.write(text)
                        sf.flush()

            with open(os.path.join(run_dir, 'result.md'), 'w', encoding='utf-8') as f:
                f.write(full_text)
            write_run_status(run_id, {'phase': 'done', 'message': '解答完成', 'progress': 100, 'run_id': run_id})
            return

        # 兜底
        write_run_status(run_id, {'phase': 'error', 'message': '未配置AI API Key', 'progress': 0, 'run_id': run_id})
    except Exception as e:
        write_run_status(run_id, {'phase': 'error', 'message': f'运行出错: {str(e)[:200]}', 'progress': 0, 'run_id': run_id})

# ═══════════════════════════════════════════════════════════════
# 紫微斗数路由 — 100%基于iztro-py官方库
# ═══════════════════════════════════════════════════════════════

@app.route('/api/ziwei/pan', methods=['POST'])
@csrf.exempt
def api_ziwei_pan():
    """紫微斗数排盘 API — 100%基于iztro-py官方库，纯Python本地计算，无需登录

    请求参数（POST JSON）：
        year: int, 必填, 出生年(1900-2100)
        month: int, 必填, 出生月(1-12)
        day: int, 必填, 出生日(1-31)
        hour: int, 必填, 出生小时(0-23)
        minute: int, 可选, 出生分钟(0-59)，默认0
        gender: str, 必填, 性别(男/女/male/female)
        date_type: str, 可选, 历法类型(solar/lunar)，默认solar
        timezone: str, 可选, 时区，默认Asia/Shanghai
        longitude: float, 可选, 出生地经度(真太阳时校准)
        question: str, 可选, 问事主题

    返回格式：
        {
            "code": 0,
            "msg": "success",
            "data": {
                "basic_info": {...},
                "core_palace": {...},
                "twelve_palaces": [...],
                "decadal_overview": [...],
                "meta": {...}
            }
        }
    """
    if not HAS_ZIWEI:
        return jsonify({'code': 1, 'msg': '紫微斗数引擎未安装(iztro-py)', 'data': None}), 503

    data = request.get_json(silent=True) or {}

    # 参数校验
    required = ['year', 'month', 'day', 'hour', 'gender']
    missing = [f for f in required if f not in data or data[f] is None]
    if missing:
        return jsonify({
            'code': 1,
            'msg': f'缺少必填参数: {", ".join(missing)}',
            'data': None,
        }), 400

    year = data['year']
    month = data['month']
    day = data['day']
    hour = data['hour']
    minute = data.get('minute', 0)
    gender = data['gender']
    date_type = data.get('date_type', 'solar')
    timezone = data.get('timezone', 'Asia/Shanghai')
    longitude = data.get('longitude')
    question = data.get('question', '')

    # 值校验
    try:
        year = int(year)
        month = int(month)
        day = int(day)
        hour = int(hour)
        minute = int(minute) if minute else 0
    except (ValueError, TypeError):
        return jsonify({'code': 1, 'msg': '数值参数格式错误', 'data': None}), 400

    if not (1900 <= year <= 2100):
        return jsonify({'code': 1, 'msg': '出生年范围: 1900-2100', 'data': None}), 400
    if not (1 <= month <= 12):
        return jsonify({'code': 1, 'msg': '出生月范围: 1-12', 'data': None}), 400
    if not (1 <= day <= 31):
        return jsonify({'code': 1, 'msg': '出生日范围: 1-31', 'data': None}), 400
    if not (0 <= hour <= 23):
        return jsonify({'code': 1, 'msg': '出生时范围: 0-23', 'data': None}), 400
    if not (0 <= minute <= 59):
        return jsonify({'code': 1, 'msg': '出生分范围: 0-59', 'data': None}), 400
    if gender not in ('male', 'female', '男', '女', 'M', 'F', 'm', 'f', '1', '0'):
        return jsonify({'code': 1, 'msg': '性别参数无效，请输入 男/女', 'data': None}), 400
    if date_type not in ('solar', 'lunar'):
        return jsonify({'code': 1, 'msg': '历法类型无效，请输入 solar/lunar', 'data': None}), 400

    try:
        result = _zw_engine.calculate(
            year=year, month=month, day=day,
            hour=hour, minute=minute,
            gender=gender, date_type=date_type,
            timezone=timezone, longitude=longitude,
        )
        result['request'] = {
            'type': 'ziwei_pan',
            'question': question,
            'timestamp': datetime.now().isoformat(),
        }
        return jsonify({'code': 0, 'msg': 'success', 'data': result})
    except ValueError as e:
        return jsonify({'code': 2, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"紫微排盘失败: {e}")
        return jsonify({'code': 3, 'msg': f'排盘计算失败: {str(e)}', 'data': None}), 500


@app.route('/api/ziwei/horoscope', methods=['POST'])
@csrf.exempt
def api_ziwei_horoscope():
    """紫微斗数推运 API — 大限/流年/流月/流日/流时

    请求参数（POST JSON）：
        year, month, day, hour, minute, gender, date_type: 同排盘
        target_date: str, 必填, 推运目标日期(YYYY-MM-DD)
        question: str, 可选

    返回格式：同排盘，额外包含 decadal/age/yearly/monthly/daily/hourly 推运信息
    """
    if not HAS_ZIWEI:
        return jsonify({'code': 1, 'msg': '紫微斗数引擎未安装(iztro-py)', 'data': None}), 503

    data = request.get_json(silent=True) or {}

    required = ['year', 'month', 'day', 'hour', 'gender']
    missing = [f for f in required if f not in data or data[f] is None]
    if missing:
        return jsonify({
            'code': 1,
            'msg': f'缺少必填参数: {", ".join(missing)}',
            'data': None,
        }), 400

    target_date = data.get('target_date', '')
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')

    try:
        year = int(data['year'])
        month = int(data['month'])
        day = int(data['day'])
        hour = int(data['hour'])
    except (ValueError, TypeError):
        return jsonify({'code': 1, 'msg': '数值参数格式错误', 'data': None}), 400

    try:
        result = _zw_engine.horoscope(
            year=year, month=month, day=day,
            hour=hour, minute=int(data.get('minute', 0) or 0),
            gender=data['gender'],
            target_date=target_date,
            target_hour=int(data.get('target_hour', -1) or -1),
            target_minute=int(data.get('target_minute', 0) or 0),
            date_type=data.get('date_type', 'solar'),
            longitude=data.get('longitude'),
        )
        result['request'] = {
            'type': 'ziwei_horoscope',
            'question': data.get('question', ''),
            'timestamp': datetime.now().isoformat(),
        }
        return jsonify({'code': 0, 'msg': 'success', 'data': result})
    except ValueError as e:
        return jsonify({'code': 2, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"紫微推运失败: {e}")
        return jsonify({'code': 3, 'msg': f'推运计算失败: {str(e)}', 'data': None}), 500


@app.route('/api/ziwei/info')
def api_ziwei_info():
    """获取紫微斗数基本信息（用于前端展示和Agent理解）"""
    if not HAS_ZIWEI:
        return jsonify({'code': 1, 'msg': '紫微斗数引擎未安装', 'data': None}), 503

    return jsonify({
        'code': 0,
        'msg': 'success',
        'data': {
            'name': '紫微斗数',
            'description': '以出生时间排出命盘，通过十二宫星曜组合分析人生运势',
            'input_requirements': [
                {'field': 'year', 'type': 'int', 'required': True, 'description': '出生年(1900-2100)'},
                {'field': 'month', 'type': 'int', 'required': True, 'description': '出生月(1-12)'},
                {'field': 'day', 'type': 'int', 'required': True, 'description': '出生日(1-31)'},
                {'field': 'hour', 'type': 'int', 'required': True, 'description': '出生小时(0-23)'},
                {'field': 'minute', 'type': 'int', 'required': False, 'description': '出生分钟(0-59)'},
                {'field': 'gender', 'type': 'str', 'required': True, 'description': '性别(男/女)'},
                {'field': 'date_type', 'type': 'str', 'required': False, 'description': '历法类型(solar/lunar)'},
            ],
            'twelve_palaces': list(_ZW_PALACE_MAP.values()),
            'shichen': [
                {'index': i, 'name': _ZW_SHICHEN[i], 'range': _ZW_SHICHEN_RANGES[i]}
                for i in range(12)
            ],
            'engine': 'iztro-py v0.3.4',
            'api_version': '1.0.0',
            'compatible_with': ['liuyao', 'meihua', 'tarot'],
        },
    })


@app.route('/api/ziwei/shichen')
def api_ziwei_shichen():
    """获取时辰对照表"""
    return jsonify({
        'code': 0,
        'msg': 'success',
        'data': {
            'shichen': [
                {'index': i, 'name': _ZW_SHICHEN[i], 'range': _ZW_SHICHEN_RANGES[i]}
                for i in range(12)
            ],
            'note': 'hour参数为出生小时(0-23)，系统自动转换为对应时辰。23:00-01:00为子时，支持早子晚子。',
        },
    }) if HAS_ZIWEI else jsonify({'code': 1, 'msg': '引擎未安装', 'data': None}), 503


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


@app.route('/api/paipan', methods=['POST'])
@login_required
@csrf.exempt
def api_paipan():
    """八字排盘 API — 接收排盘参数，调用 paipan_auto.sh"""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    gender = data.get('gender', '男')
    cal_type = data.get('calType', '公历')
    birth_time = (data.get('birthTime') or '').strip()
    birth_addr = (data.get('birthAddr') or '').strip()
    addr_info = data.get('addrInfo', {})

    if not name:
        return jsonify({'success': False, 'error': '缺少姓名'}), 400
    if not birth_time or len(birth_time) < 8:
        return jsonify({'success': False, 'error': '缺少出生时间'}), 400

    # 农历转公历
    birth_time, cal_type = lunar_to_solar(birth_time, cal_type)

    # 构建 shell 命令
    cmd = ['bash', PAIPAN_SH, name, gender, cal_type, birth_time]
    if birth_addr:
        cmd.append(birth_addr)
    if isinstance(addr_info, dict) and addr_info.get('full'):
        cmd.append(addr_info['full'])

    logger.info(f"执行: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True,
            timeout=90, cwd=PAIPAN_DIR
        )
        success = 'SUCCESS' in (result.stdout or '')
        stdout_text = result.stdout.strip() if result.stdout else ''
        stderr_text = result.stderr.strip() if result.stderr else ''

        logger.info(f"{'成功' if success else '失败'}: {name}")

        # 保存记录
        rec = Record(
            question=f"{name} | {gender} | {birth_time} | {birth_addr or '-'}",
            result_html=stdout_text if success else '',
            app_type='paipan',
            user_id=current_user.id,
        )
        db.session.add(rec)
        db.session.commit()

        return jsonify({
            'success': success,
            'message': stdout_text,
            'error': stderr_text if not success else None,
            'name': name,
            'record_id': rec.id,
        })

    except subprocess.TimeoutExpired:
        return jsonify({'success': False, 'error': '执行超时（90秒）', 'name': name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'name': name})


# ═══════════════════════════════════════════════════════════════
# 八字排盘 — SSE 流式 AI 解读
# ═══════════════════════════════════════════════════════════════
_bazi_ask_current_run = 0
_bazi_ask_lock = threading.Lock()

@app.route('/api/bazi/ask/stream', methods=['GET', 'POST'])
@csrf.exempt
def api_bazi_ask_stream():
    """八字排盘 SSE 流式 AI 解读。POST=新建任务+流式；GET=读取已有任务"""
    global _bazi_ask_current_run

    if request.method == 'POST':
        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()

        # 参数
        birth = data.get('birth', '')
        gender = data.get('gender', '')
        name = data.get('name', '')
        cal_type = data.get('cal_type', 'solar')
        birth_addr = data.get('birth_addr', '')
        birth_lng = data.get('birth_lng', 0)
        birth_lat = data.get('birth_lat', 0)
        analysis_type = data.get('analysis_type', '')
        pan_data = data.get('pan_data')
        record_ids = data.get('record_ids', [])  # 从档案选择的多条记录ID
        year, month, day, hour = data.get('year'), data.get('month'), data.get('day'), data.get('hour')

        if not birth and not all([year, month, day, hour]) and not pan_data and not record_ids:
            history = data.get('history', [])
            if not history:
                return jsonify({'error': '请提供出生时间或选择档案'}), 400

        # 排盘：优先使用前端传的 pan_data（八字排盘免费版的专业排盘结果）
        result = None
        results_list = []

        if record_ids and isinstance(record_ids, list) and record_ids:
            # 从数据库加载历史记录，重新排盘
            from bazi_engine import paipan as bazi_paipan
            records = BaziRecord.query.filter(
                BaziRecord.id.in_(record_ids),
                BaziRecord.user_id == (current_user.id if current_user.is_authenticated else -1)
            ).all()
            for rec in records:
                try:
                    params = json.loads(rec.params_json) if rec.params_json else {}
                    bt = rec.birth_time or params.get('birthTime', '')
                    cal = rec.cal_type or params.get('calType', '公历')
                    g = rec.gender or params.get('gender', '男')
                    addr = rec.birth_addr or params.get('birthAddr', '')
                    lng = float(params.get('birthLng', 0) or 0)
                    r = bazi_paipan(rec.name, g, bt, cal, addr, longitude=lng if lng else None)
                    if r and r.get('success'):
                        r['_record_id'] = rec.id
                        r['_record_name'] = rec.name
                        results_list.append(r)
                except:
                    pass
            if results_list:
                # 使用第一条作为主 pan，全部存 pan_list
                result = results_list[0]
        elif pan_data and isinstance(pan_data, dict) and pan_data.get('success'):
            result = pan_data
        elif birth or all([year, month, day, hour]):
            from bazi_engine import paipan as bazi_paipan
            try:
                if birth:
                    result = bazi_paipan(name, gender, birth, cal_type, birth_addr, longitude=birth_lng if birth_lng else None)
                else:
                    birth_str = f"{year}-{month:02d}-{day:02d} {hour}:00"
                    result = bazi_paipan(name, gender, birth_str, cal_type, birth_addr)
            except Exception as e:
                return jsonify({'error': f'排盘失败: {str(e)}'}), 500
            if not result.get('success'):
                return jsonify({'error': result.get('error', '排盘失败')}), 500

        # 生成 run_id（带前缀，避免ID冲突）
        with _bazi_ask_lock:
            _bazi_ask_current_run += 1
            run_id = f"bz_{_bazi_ask_current_run}"

        run_dir = get_run_dir(run_id)
        if result:
            with open(os.path.join(run_dir, 'pan.json'), 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False)
        if results_list:
            with open(os.path.join(run_dir, 'pan_list.json'), 'w', encoding='utf-8') as f:
                json.dump(results_list, f, ensure_ascii=False)
        with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
            f.write(question)
        with open(os.path.join(run_dir, 'analysis_type.txt'), 'w') as f:
            f.write(analysis_type)
        if not result:
            with open(os.path.join(run_dir, 'history.json'), 'w', encoding='utf-8') as f:
                json.dump(data.get('history', []), f, ensure_ascii=False)

        # 创建 Record（如六爻/梅花一样，让侧边栏自动显示）
        uid = current_user.id if current_user.is_authenticated else None
        if uid:
            try:
                record = Record(question=question[:200], user_id=uid, app_type='bazi', result_html='')
                db.session.add(record)
                db.session.commit()
                with open(os.path.join(run_dir, 'record_id.txt'), 'w') as f:
                    f.write(str(record.id))
            except Exception as e:
                logger.warning(f'[bazi] 创建Record失败: {e}')

        write_run_status(run_id, {'phase': 'calculating', 'message': '排盘中...', 'progress': 10, 'run_id': run_id})
        t = threading.Thread(target=_bazi_ask_task, args=(run_id,), daemon=True)
        t.start()
    else:
        # 八字 GET：读取已有任务
        run_id = request.args.get('run_id', default='')
        if not run_id:
            return jsonify({'error': '无效的 run_id'}), 400

    # SSE 流式（八字）
    run_dir = get_run_dir(run_id)
    stream_file = os.path.join(run_dir, 'stream.txt')

    def _bz_generate():
        last_size = 0
        while True:
            s = read_run_status(run_id)
            phase = s.get('phase', 'idle')
            try:
                if os.path.exists(stream_file):
                    with open(stream_file, 'r', encoding='utf-8') as f:
                        f.seek(last_size)
                        nc = f.read()
                        if nc:
                            last_size += len(nc.encode('utf-8'))
                            yield f"data: {json.dumps({'type': 'delta', 'content': nc}, ensure_ascii=False)}\n\n"
            except:
                pass
            if phase == 'done':
                yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                break
            elif phase == 'error':
                yield f"data: {json.dumps({'type': 'error', 'message': s.get('message', '未知错误')}, ensure_ascii=False)}\n\n"
                break
            import time; time.sleep(0.3)

    return Response(_bz_generate(), mimetype='text/event-stream', headers={
        'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no', 'Connection': 'keep-alive',
    })

def _bazi_ask_task(run_id):
    """后台线程：构建八字Prompt → 调用 DeepSeek API → 保存结果"""
    try:
        run_dir = get_run_dir(run_id)
        question = open(os.path.join(run_dir, 'question.txt'), 'r', encoding='utf-8').read().strip()
        analysis_type = ''
        try:
            analysis_type = open(os.path.join(run_dir, 'analysis_type.txt'), 'r').read().strip()
        except:
            pass

        write_run_status(run_id, {'phase': 'analyzing', 'message': 'AI解盘中...', 'progress': 30, 'run_id': run_id})

        from openai import OpenAI
        import os as _os
        sf_key = _os.environ.get('SILICONFLOW_API_KEY', '')
        sf_url = _os.environ.get('SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1')
        model = _os.environ.get('DEEPSEEK_MODEL_NORMAL', 'deepseek-ai/DeepSeek-V3')

        if not sf_key:
            write_run_status(run_id, {'phase': 'error', 'message': '未配置AI API Key', 'progress': 0, 'run_id': run_id})
            return

        client = OpenAI(api_key=sf_key, base_url=sf_url)
        system_prompt = '你是精通八字命理的资深命理师。根据用户的问题和命盘数据，给出专业、有深度、个性化的命理分析。结合八字四柱、五行生克、十神关系来论证观点，给出建设性建议。语言自然流畅，像命理师在面对面交流。'

        pan_path = os.path.join(run_dir, 'pan.json')
        pan_list_path = os.path.join(run_dir, 'pan_list.json')

        # 辅助函数：从命盘结果构建文字
        def _build_bazi_text(pan_result, label=''):
            fp = pan_result.get('four_pillars', {})
            shi_shen = pan_result.get('shi_shen', {})
            cang_gan = pan_result.get('cang_gan', {})
            cang_gan_ss = pan_result.get('cang_gan_shi_shen', {})
            shen_sha_pp = pan_result.get('shen_sha_per_pillar', {})

            pillars_detail = ''
            for p in ['year', 'month', 'day', 'hour']:
                col = fp.get(p, {})
                ss_key = p + '_gan'
                cg = cang_gan.get(p, [])
                cg_ss = cang_gan_ss.get(p, [])
                cg_parts = [f'{cg[i]}({cg_ss[i]})' for i in range(min(len(cg), len(cg_ss)))]
                ss = shen_sha_pp.get(p, [])
                pillars_detail += (
                    f"  {p}柱: {col.get('gan_zhi', '')}  天干十神: {shi_shen.get(ss_key, '')}  "
                    f"纳音: {col.get('nayin', '')}  藏干: {','.join(cg_parts) if cg_parts else '无'}  "
                    f"神煞: {','.join(ss) if ss else '无'}\n"
                )

            da_yun_list = pan_result.get('da_yun', [])
            dy_text = ''
            for dy in da_yun_list:
                p_rels = str(dy.get('pillar_relations', []))
                dy_text += (
                    f"  {dy.get('start_age', '?')}~{dy.get('end_age', '?')}岁: "
                    f"{dy.get('gan_zhi', '')} 十神: {dy.get('gan_shishen_abbrev', '')}/{dy.get('zhi_shishen_abbrev', '')}  "
                    f"纳音: {dy.get('nayin', '')} 神煞: {','.join(dy.get('shen_sha', []) or [])}  "
                    f"冲合: {p_rels[1:-1] if p_rels and p_rels != '[]' else '无'}\n"
                )

            liu_nian_list = pan_result.get('liu_nian', [])[:10]
            ln_text = ''
            for ln in liu_nian_list:
                p_rels = str(ln.get('pillar_relations', []))
                ln_text += (
                    f"  {ln.get('year', '')}: {ln.get('gan_zhi', '')} "
                    f"十神: {ln.get('gan_shishen_abbrev', '')}/{ln.get('zhi_shishen_abbrev', '')}  "
                    f"纳音: {ln.get('nayin', '')} 神煞: {','.join(ln.get('shen_sha', []) or [])}  "
                    f"冲合: {p_rels[1:-1] if p_rels and p_rels != '[]' else '无'}\n"
                )

            geju = pan_result.get('geju', {})
            tiaohou = pan_result.get('tiaohou', {})
            fp2 = fp
            label = label or pan_result.get('_record_name', '')
            name = pan_result.get('name', '') or label
            return f"""【命盘】{name}
  性别: {pan_result.get('gender', '')}  出生: {pan_result.get('birth_solar', '')}
  日主: {fp2.get('day', {}).get('gan', '')}({fp2.get('day', {}).get('wu_xing', '')})
  旺衰: {pan_result.get('wang_shuai', '')}  格局: {geju.get('name', '无')}
  四柱: {fp2.get('year', {}).get('gan_zhi', '')} {fp2.get('month', {}).get('gan_zhi', '')} {fp2.get('day', {}).get('gan_zhi', '')} {fp2.get('hour', {}).get('gan_zhi', '')}
  五行: {pan_result.get('wu_xing', '')}  缺: {', '.join(pan_result.get('lack_wuxing', [])) if pan_result.get('lack_wuxing') else '无'}
  大运: {dy_text}  流年: {ln_text}"""

        if os.path.exists(pan_list_path):
            with open(pan_list_path, 'r', encoding='utf-8') as f:
                pan_list = json.load(f)
            parts = []
            for i, pan in enumerate(pan_list):
                name = pan.get('_record_name', '') or pan.get('name', '') or f'命主{i+1}'
                parts.append(f'【命主{i+1}】{name}\n{_build_bazi_text(pan)}')
            all_text = '\n'.join(parts)
            user_msg = f'以下为多份命盘数据：\n{all_text}\n\n用户的问题：{question}'
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_msg}]
        elif os.path.exists(pan_path):
            with open(pan_path, 'r', encoding='utf-8') as f:
                result = json.load(f)

            fp = result.get('four_pillars', {})
            shi_shen = result.get('shi_shen', {})
            cang_gan = result.get('cang_gan', {})
            cang_gan_ss = result.get('cang_gan_shi_shen', {})
            shen_sha_pp = result.get('shen_sha_per_pillar', {})

            pillars_detail = ''
            for p in ['year', 'month', 'day', 'hour']:
                col = fp.get(p, {})
                ss_key = p + '_gan'
                cg = cang_gan.get(p, [])
                cg_ss = cang_gan_ss.get(p, [])
                cg_parts = [f'{cg[i]}({cg_ss[i]})' for i in range(min(len(cg), len(cg_ss)))]
                ss = shen_sha_pp.get(p, [])
                pillars_detail += (
                    f"  {p}柱: {col.get('gan_zhi', '')}  天干十神: {shi_shen.get(ss_key, '')}  "
                    f"纳音: {col.get('nayin', '')}  藏干: {','.join(cg_parts) if cg_parts else '无'}  "
                    f"神煞: {','.join(ss) if ss else '无'}\n"
                )

            da_yun_list = result.get('da_yun', [])
            dy_text = ''
            for dy in da_yun_list:
                p_rels = str(dy.get('pillar_relations', []))
                dy_text += (
                    f"  {dy.get('start_age', '?')}~{dy.get('end_age', '?')}岁: "
                    f"{dy.get('gan_zhi', '')} 十神: {dy.get('gan_shishen_abbrev', '')}/{dy.get('zhi_shishen_abbrev', '')}  "
                    f"纳音: {dy.get('nayin', '')} 神煞: {','.join(dy.get('shen_sha', []) or [])}  "
                    f"冲合: {p_rels[1:-1] if p_rels and p_rels != '[]' else '无'}\n"
                )

            liu_nian_list = result.get('liu_nian', [])[:10]
            ln_text = ''
            for ln in liu_nian_list:
                p_rels = str(ln.get('pillar_relations', []))
                ln_text += (
                    f"  {ln.get('year', '')}: {ln.get('gan_zhi', '')} "
                    f"十神: {ln.get('gan_shishen_abbrev', '')}/{ln.get('zhi_shishen_abbrev', '')}  "
                    f"纳音: {ln.get('nayin', '')} 神煞: {','.join(ln.get('shen_sha', []) or [])}  "
                    f"冲合: {p_rels[1:-1] if p_rels and p_rels != '[]' else '无'}\n"
                )

            geju = result.get('geju', {})
            tiaohou = result.get('tiaohou', {})
            bazi_data_text = f"""【基础信息】
姓名: {result.get('name', '')}  性别: {result.get('gender', '')}
出生: {result.get('birth_solar', '')}
日主: {fp.get('day', {}).get('gan', '')}({fp.get('day', {}).get('wu_xing', '')})
旺衰: {result.get('wang_shuai', '')}
生肖: {result.get('sheng_xiao', '')}  星座: {result.get('xing_zuo', '')}

【四柱详解】
{pillars_detail}
【五行】
分布: {result.get('wu_xing', '')}
所缺: {', '.join(result.get('lack_wuxing', [])) if result.get('lack_wuxing') else '无'}
旺相休囚: {result.get('wang_xiang_xiu', {})}

【格局】{geju.get('name', '无')}  {geju.get('desc', '')}
【调候用神】{tiaohou.get('shen', '无')}  {tiaohou.get('desc', '')}

【大运】（起运{result.get('qi_yun_age', '?')}岁，{result.get('da_yun_direction', '')}行）
{dy_text}
【近期流年】
{ln_text}"""

            user_msg = f'{bazi_data_text}\n用户的问题：{question}'
            messages = [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_msg}]
        else:
            history = []
            try:
                with open(os.path.join(run_dir, 'history.json'), 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                pass
            messages = [{'role': 'system', 'content': system_prompt}]

            # 追问时重新构建完整的命盘数据，保证模型有全部上下文
            if os.path.exists(pan_path):
                with open(pan_path, 'r', encoding='utf-8') as f:
                    result2 = json.load(f)
                fp2 = result2.get('four_pillars', {})
                si = result2.get('shi_shen', {})
                dy_list = result2.get('da_yun', [])
                dy_t = ''.join([f'{d.get("gan_zhi","")}({d.get("start_age","?")}-{d.get("end_age","?")}岁) ' for d in dy_list[:3]])
                ln_t = ' '.join([f'{l.get("year","")}({l.get("gan_zhi","")})' for l in (result2.get("liu_nian",[]) or [])[:5]])
                pan_text = f'【命盘】{result2.get("birth_solar","")} {result2.get("gender","")} 日主{fp2.get("day",{}).get("gan","")}({fp2.get("day",{}).get("wu_xing","")}) 四柱{" ".join([fp2.get(p,{}).get("gan_zhi","") for p in ["year","month","day","hour"]])} 五行{result2.get("wu_xing","")} 缺{",".join(result2.get("lack_wuxing",[]) or [])} 格局{result2.get("geju",{}).get("name","")} 大运{dy_t} 流年{ln_t}'
                messages.append({'role': 'user', 'content': f'{pan_text}\n\n用户当前问题：{question}'})
            else:
                messages.append({'role': 'user', 'content': f'用户当前问题：{question}\n\n只分析当前问题，不涉及其他内容。'})

        write_run_status(run_id, {'phase': 'streaming', 'message': '生成解答中...', 'progress': 50, 'run_id': run_id})
        response = client.chat.completions.create(
            model=model, messages=messages, temperature=0.6, max_tokens=2048, stream=True
        )

        full_text = ''
        with open(os.path.join(run_dir, 'stream.txt'), 'w', encoding='utf-8') as sf:
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    text = chunk.choices[0].delta.content
                    full_text += text
                    sf.write(text)
                    sf.flush()

        with open(os.path.join(run_dir, 'result.md'), 'w', encoding='utf-8') as f:
            f.write(full_text)
        write_run_status(run_id, {'phase': 'done', 'message': '解答完成', 'progress': 100, 'run_id': run_id})

        # 更新 Record result_html（背景线程需要 app_context）
        try:
            with app.app_context():
                rid_path = os.path.join(run_dir, 'record_id.txt')
                if os.path.exists(rid_path):
                    rid = int(open(rid_path).read().strip())
                    rec = db.session.get(Record, rid)
                    if rec:
                        rec.result_html = full_text
                        db.session.commit()
        except Exception as e:
            logger.warning(f'[bazi] 更新Record结果失败: {e}')
        return

        write_run_status(run_id, {'phase': 'error', 'message': '未配置AI API Key', 'progress': 0, 'run_id': run_id})
    except Exception as e:
        write_run_status(run_id, {'phase': 'error', 'message': f'运行出错: {str(e)[:200]}', 'progress': 0, 'run_id': run_id})


@app.route('/api/bazi/paipan', methods=['POST'])
@csrf.exempt
def api_bazi_paipan():
    """八字排盘免费版 API — 纯Python本地计算，无需登录"""
    from bazi_engine import paipan as bazi_paipan
    data = request.get_json(silent=True) or {}

    name = (data.get('name') or '').strip()
    gender = data.get('gender', '男')
    cal_type = data.get('calType', '公历')  # 公历/农历/四柱
    birth_time = (data.get('birthTime') or '').strip()   # YYYYMMDDHHmm
    birth_addr = (data.get('birthAddr') or '').strip()   # 出生地
    birth_lng = float(data.get('birthLng', 0) or 0)     # 前端传递的精确经度
    birth_lat = float(data.get('birthLat', 0) or 0)     # 前端传递的精确纬度
    is_dst = bool(data.get('isDst', False))               # 夏令时开关
    night_zi_mode = data.get('nightZiMode', '夜子时不换日')  # 早晚子时模式
    sizi_pillars = data.get('siziPillars', None)           # 四柱直接输入
    use_solar_time = bool(data.get('useSolarTime', True))  # 真太阳时开关
    is_leap_month = bool(data.get('isLeapMonth', False))   # 农历闰月

    # 四柱直接输入模式不需要 birthTime
    if cal_type != '四柱' and (not birth_time or len(birth_time) < 8):
        return jsonify({'success': False, 'error': '请输入出生日期'})

    try:
        result = bazi_paipan(name, gender, birth_time, cal_type, birth_addr,
                             is_dst=is_dst, night_zi_mode=night_zi_mode,
                             sizi_pillars=sizi_pillars,
                             use_solar_time=use_solar_time,
                             is_leap_month=is_leap_month,
                             longitude=birth_lng if birth_lng else None)

        # 保存到历史记录（回放标记 _replay 时跳过保存）
        is_replay = bool(data.get('_replay'))
        if result.get('success') and not is_replay:
            fp = result.get('four_pillars', {})
            pillars_str = ''.join(fp.get(p, {}).get('gan', '?') + fp.get(p, {}).get('zhi', '?') for p in ['year', 'month', 'day', 'hour'])
            params_data = {k: v for k, v in data.items() if k not in ('name', '_replay')}

            if current_user.is_authenticated:
                # 已登录 → 保存到数据库
                bazi_rec = BaziRecord(
                    user_id=current_user.id,
                    name=name or '未命名',
                    gender=gender,
                    birth_time=birth_time,
                    cal_type=cal_type,
                    birth_addr=birth_addr,
                    pillars=pillars_str,
                    record_type='paipan',
                    starred=False,
                    category='全部',
                    params_json=json.dumps(params_data, ensure_ascii=False),
                )
                db.session.add(bazi_rec)
                db.session.flush()
                sync_bazi_record_to_profile(current_user.id, bazi_rec, params_data, result)
                db.session.commit()
            else:
                # 未登录 → 保存到 session（降级方案）
                history = session.get('bazi_history', [])
                history.insert(0, {
                    'name': name or '未命名',
                    'gender': gender,
                    'birth_time': birth_time,
                    'cal_type': cal_type,
                    'birth_addr': birth_addr,
                    'pillars': pillars_str,
                    'created_at': datetime.now().isoformat(),
                    'params': params_data,
                    'starred': False,
                    'category': '全部',
                    'type': 'paipan',
                })
                session['bazi_history'] = history[:50]
                session.modified = True

        return jsonify(result)
    except Exception as e:
        logger.error(f"八字排盘异常: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/bazi/lunar-month-data', methods=['POST'])
@csrf.exempt
def api_bazi_lunar_month_data():
    """返回指定农历年的月份列表（含闰月）和日名映射"""
    data = request.get_json(silent=True) or {}
    year = data.get('year', 2024)

    month_names = {1:'正月',2:'二月',3:'三月',4:'四月',5:'五月',6:'六月',
                   7:'七月',8:'八月',9:'九月',10:'十月',11:'冬月',12:'腊月'}

    day_name_map = {1:'初一',2:'初二',3:'初三',4:'初四',5:'初五',
                    6:'初六',7:'初七',8:'初八',9:'初九',10:'初十',
                    11:'十一',12:'十二',13:'十三',14:'十四',15:'十五',
                    16:'十六',17:'十七',18:'十八',19:'十九',20:'二十',
                    21:'廿一',22:'廿二',23:'廿三',24:'廿四',25:'廿五',
                    26:'廿六',27:'廿七',28:'廿八',29:'廿九',30:'三十'}

    try:
        from lunarcalendar import Lunar, DateNotExist
        # 检测该年闰月
        leap_month_num = None
        for m in range(1, 13):
            try:
                Lunar(year, m, 1, isleap=True)
                leap_month_num = m
            except (ValueError, DateNotExist):
                pass

        # 构建月份列表（含天数）
        months_info = []
        for m in range(1, 13):
            # 常规月天数
            try:
                Lunar(year, m, 30, isleap=False)
                day_count = 30
            except (ValueError, DateNotExist):
                day_count = 29
            months_info.append({
                'value': m,
                'label': month_names.get(m, str(m)),
                'isLeap': False,
                'dayCount': day_count
            })
            # 闰月插入在正常月之后
            if m == leap_month_num:
                try:
                    Lunar(year, m, 30, isleap=True)
                    leap_day_count = 30
                except (ValueError, DateNotExist):
                    leap_day_count = 29
                months_info.append({
                    'value': m,
                    'label': f'闰{month_names.get(m, str(m))}',
                    'isLeap': True,
                    'dayCount': leap_day_count
                })

        return jsonify({
            'success': True,
            'months': months_info,
            'dayNames': day_name_map
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/bazi/solar-to-lunar', methods=['POST'])
@csrf.exempt
def api_bazi_solar_to_lunar():
    data = request.get_json(silent=True) or {}
    year = data.get('year')
    month = data.get('month')
    day = data.get('day')
    if not year or not month or not day:
        return jsonify({'success': False, 'error': '缺少参数(year/month/day)'})
    try:
        year = int(year)
        month = int(month)
        day = int(day)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': '日期格式错误'})
    try:
        from lunar_python import Solar
        solar = Solar.fromYmd(year, month, day)
        lunar = solar.getLunar()
        lunar_month = lunar.getMonth()
        is_leap = lunar_month < 0
        return jsonify({
            'success': True,
            'year': lunar.getYear(),
            'month': abs(lunar_month),
            'day': lunar.getDay(),
            'isLeap': is_leap
        })
    except Exception:
        pass
    if not HAS_LUNAR:
        return jsonify({'success': False, 'error': '农历库不可用'})
    try:
        from lunarcalendar import Converter, Solar as LSolar
        s = LSolar(year, month, day)
        l = Converter.Solar2Lunar(s)
        is_leap = getattr(l, 'isleap', False)
        return jsonify({
            'success': True,
            'year': l.year,
            'month': l.month,
            'day': l.day,
            'isLeap': is_leap
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/bazi/lunar-to-solar', methods=['POST'])
@csrf.exempt
def api_bazi_lunar_to_solar():
    data = request.get_json(silent=True) or {}
    year = data.get('year')
    month = data.get('month')
    day = data.get('day')
    is_leap = bool(data.get('isLeap', False))
    if not year or not month or not day:
        return jsonify({'success': False, 'error': '缺少参数(year/month/day)'})
    try:
        year = int(year)
        month = int(month)
        day = int(day)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': '日期格式错误'})
    try:
        from lunar_python import Lunar as _Lunar
        lp_month = -month if is_leap else month
        lunar = _Lunar.fromYmd(year, lp_month, day)
        solar = lunar.getSolar()
        return jsonify({
            'success': True,
            'year': solar.getYear(),
            'month': solar.getMonth(),
            'day': solar.getDay()
        })
    except Exception:
        pass
    if not HAS_LUNAR:
        return jsonify({'success': False, 'error': '农历库不可用'})
    try:
        from lunarcalendar import Lunar, Converter
        lunar = Lunar(year, month, day, isleap=is_leap)
        solar = Converter.Lunar2Solar(lunar)
        return jsonify({
            'success': True,
            'year': solar.year,
            'month': solar.month,
            'day': solar.day
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/bazi/liu-yue', methods=['POST'])
@csrf.exempt
def api_bazi_liu_yue():
    """八字流月查询 API — 根据年份和日主返回12个流月"""
    from bazi_engine import calc_liu_yue
    data = request.get_json(silent=True) or {}

    year = data.get('year')
    day_gan = (data.get('dayGan') or '').strip()

    if not year or not day_gan:
        return jsonify({'success': False, 'error': '缺少参数(year/dayGan)'})

    try:
        year = int(year)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': '年份格式错误'})

    if day_gan not in '甲乙丙丁戊己庚辛壬癸':
        return jsonify({'success': False, 'error': '日主天干无效'})

    try:
        liu_yue = calc_liu_yue(year, day_gan)
        # 计算当前节气月编号（基于节令而非公历月份）
        current_bazi_month = None
        now = datetime.now()
        if year == now.year:
            try:
                from bazi_engine import get_jieqi_times, JIE_ORDER, JIE_ZHI, MONTH_ZHI
                jieqi_times = get_jieqi_times(year)
                # 找出当前时刻之前最近的节令
                candidates = []
                for jie_name in JIE_ORDER:
                    jie_dt = jieqi_times.get(jie_name)
                    if jie_dt and jie_dt <= now:
                        candidates.append((jie_dt, jie_name))
                if candidates:
                    candidates.sort(key=lambda x: x[0])
                    _, latest_jie_name = candidates[-1]
                    current_zhi = JIE_ZHI[latest_jie_name]
                    current_bazi_month = MONTH_ZHI.index(current_zhi) + 1  # 1-12
            except Exception as e2:
                logger.error(f"[八字流月] 节气月计算异常: {e2}")
        return jsonify({'success': True, 'liu_yue': liu_yue, 'year': year, 'current_bazi_month': current_bazi_month})
    except Exception as e:
        logger.error(f"[八字流月] 异常: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/bazi/liu-ri', methods=['POST'])
@csrf.exempt
def api_bazi_liu_ri():
    """八字流日查询 API — 支持按公历月份或八字月份（节令分界）查询

    两种模式:
    1. 传统模式: 传 year + month + dayGan（公历月份1-12）
    2. 八字月模式: 传 year + baziMonth + dayGan（八字月序号1-12，以节令分界）
       优先级: baziMonth > month
    """
    data = request.get_json(silent=True) or {}

    year = data.get('year')
    bazi_month = data.get('baziMonth')
    month = data.get('month')
    day_gan = (data.get('dayGan') or '').strip()

    if not year or not day_gan:
        return jsonify({'success': False, 'error': '缺少参数(year/dayGan)'})

    if day_gan not in '甲乙丙丁戊己庚辛壬癸':
        return jsonify({'success': False, 'error': '日主天干无效'})

    try:
        year = int(year)
    except (ValueError, TypeError):
        return jsonify({'success': False, 'error': '年份格式错误'})

    try:
        if bazi_month:
            # 八字月模式（节令分界）
            from bazi_engine import calc_liu_ri_by_bazi_month
            bazi_month = int(bazi_month)
            if not (1 <= bazi_month <= 12):
                return jsonify({'success': False, 'error': '八字月序号范围1-12'})
            result = calc_liu_ri_by_bazi_month(year, bazi_month, day_gan)
            result['success'] = True
            return jsonify(result)
        elif month:
            # 传统公历月份模式
            from bazi_engine import calc_liu_ri
            month = int(month)
            if not (1 <= month <= 12):
                return jsonify({'success': False, 'error': '月份范围1-12'})
            liu_ri = calc_liu_ri(year, month, day_gan)
            return jsonify({'success': True, 'liu_ri': liu_ri, 'year': year, 'month': month})
        else:
            return jsonify({'success': False, 'error': '缺少参数(baziMonth 或 month)'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        logger.error(f"[八字流日] 异常: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/bazi/liu-shi', methods=['POST'])
@csrf.exempt
def api_bazi_liu_shi():
    """八字流时查询 API — 根据日干和日主返回12个流时"""
    from bazi_engine import calc_liu_shi
    data = request.get_json(silent=True) or {}

    day_gan = (data.get('dayGan') or '').strip()  # 当日天干（五鼠遁用）
    day_zhu_gan = (data.get('dayZhuGan') or '').strip()  # 日主天干（十神计算用）

    if not day_gan:
        return jsonify({'success': False, 'error': '缺少参数(dayGan)'})

    if day_gan not in '甲乙丙丁戊己庚辛壬癸':
        return jsonify({'success': False, 'error': '当日天干无效'})

    if not day_zhu_gan:
        day_zhu_gan = day_gan

    try:
        liu_shi = calc_liu_shi(day_gan, day_zhu_gan)
        return jsonify({'success': True, 'liu_shi': liu_shi})
    except Exception as e:
        logger.error(f"[八字流时] 异常: {e}")
        return jsonify({'success': False, 'error': str(e)})


# ═══════════════════════════════════════════════════════════════
# 八字合盘 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/bazi/hepan', methods=['POST'])
@csrf.exempt
def api_bazi_hepan():
    """八字合盘 API — 双人八字对比分析

    接收两个人的排盘参数，分别排盘后进行干支冲合对比和五行互补分析。
    """
    from bazi_engine import paipan as bazi_paipan, calc_ganzhi_relation_with_pillars
    data = request.get_json(silent=True) or {}

    person1 = data.get('person1', {})
    person2 = data.get('person2', {})

    if not person1 or not person2:
        return jsonify({'success': False, 'error': '请提供person1和person2参数'})

    try:
        # 排盘
        result1 = bazi_paipan(
            (person1.get('name') or '').strip(),
            person1.get('gender', '男'),
            (person1.get('birthTime') or '').strip(),
            person1.get('calType', '公历'),
            (person1.get('birthAddr') or '').strip(),
            is_dst=bool(person1.get('isDst', False)),
            night_zi_mode=person1.get('nightZiMode', '夜子时不换日'),
            sizi_pillars=person1.get('siziPillars'),
            use_solar_time=bool(person1.get('useSolarTime', True)),
            is_leap_month=bool(person1.get('isLeapMonth', False))
        )
        result2 = bazi_paipan(
            (person2.get('name') or '').strip(),
            person2.get('gender', '女'),
            (person2.get('birthTime') or '').strip(),
            person2.get('calType', '公历'),
            (person2.get('birthAddr') or '').strip(),
            is_dst=bool(person2.get('isDst', False)),
            night_zi_mode=person2.get('nightZiMode', '夜子时不换日'),
            sizi_pillars=person2.get('siziPillars'),
            use_solar_time=bool(person2.get('useSolarTime', True)),
            is_leap_month=bool(person2.get('isLeapMonth', False))
        )

        if not result1.get('success') or not result2.get('success'):
            return jsonify({
                'success': False,
                'error': f"排盘失败: {result1.get('error','') or result2.get('error','')}"
            })

        # 干支关系分析
        fp1 = result1['four_pillars']
        fp2 = result2['four_pillars']

        # 每柱对比
        pillar_compare = []
        for p in ['year', 'month', 'day', 'hour']:
            g1, z1 = fp1[p]['gan'], fp1[p]['zhi']
            g2, z2 = fp2[p]['gan'], fp2[p]['zhi']
            rels = _calc_pair_relations(g1, z1, g2, z2)
            pillar_compare.append({
                'pillar': p,
                'label': {'year':'年柱','month':'月柱','day':'日柱','hour':'时柱'}[p],
                'person1': g1 + z1,
                'person2': g2 + z2,
                'relations': rels
            })

        # 五行互补分析
        wx1 = result1.get('wu_xing', {})
        wx2 = result2.get('wu_xing', {})
        wx_complement = _calc_wuxing_complement(wx1, wx2)

        # 日主关系
        day_gan1 = fp1['day']['gan']
        day_gan2 = fp2['day']['gan']
        day_relation = _calc_day_gan_relation(day_gan1, day_gan2)

        # 综合评分
        score = _calc_hepan_score(pillar_compare, wx_complement, day_relation)

        # 保存合盘记录（回放标记 _replay 时跳过保存）
        is_replay = bool(data.get('_replay'))
        if not is_replay:
            name1 = (person1.get('name') or '').strip() or '甲方'
            name2 = (person2.get('name') or '').strip() or '乙方'
            gender1 = person1.get('gender', '男')
            gender2 = person2.get('gender', '女')
            hepan_data = {
                'person1': {'name': name1, 'gender': gender1},
                'person2': {'name': name2, 'gender': gender2},
                'score': score,
            }

            if current_user.is_authenticated:
                # 已登录 → 保存到数据库
                bazi_rec = BaziRecord(
                    user_id=current_user.id,
                    name=f"{name1} & {name2}",
                    gender=f"{gender1}/{gender2}",
                    birth_time='',
                    cal_type='合盘',
                    birth_addr='',
                    pillars='',
                    record_type='hepan',
                    starred=False,
                    category='全部',
                    params_json=json.dumps(data, ensure_ascii=False),
                    hepan_json=json.dumps(hepan_data, ensure_ascii=False),
                )
                db.session.add(bazi_rec)
                db.session.commit()
            else:
                # 未登录 → 保存到 session
                history = session.get('bazi_history', [])
                history.insert(0, {
                    'name': f"{name1} & {name2}",
                    'gender': f"{gender1}/{gender2}",
                    'birth_time': '',
                    'cal_type': '合盘',
                    'birth_addr': '',
                    'pillars': '',
                    'created_at': datetime.now().isoformat(),
                    'params': data,
                    'starred': False,
                    'category': '全部',
                    'type': 'hepan',
                    'hepan_data': hepan_data,
                })
                session['bazi_history'] = history[:50]
                session.modified = True

        return jsonify({
            'success': True,
            'person1': {
                'name': result1.get('name', ''),
                'gender': result1.get('gender', ''),
                'birth': result1.get('birth_solar', ''),
                'four_pillars': fp1,
                'wu_xing': wx1,
                'lack_wuxing': result1.get('lack_wuxing', []),
                'day_master': day_gan1
            },
            'person2': {
                'name': result2.get('name', ''),
                'gender': result2.get('gender', ''),
                'birth': result2.get('birth_solar', ''),
                'four_pillars': fp2,
                'wu_xing': wx2,
                'lack_wuxing': result2.get('lack_wuxing', []),
                'day_master': day_gan2
            },
            'pillar_compare': pillar_compare,
            'wx_complement': wx_complement,
            'day_relation': day_relation,
            'score': score
        })
    except Exception as e:
        logger.error(f"[八字合盘] 异常: {e}")
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


def _calc_pair_relations(g1, z1, g2, z2):
    """计算两组干支之间的关系"""
    # 天干五合
    GAN_HE_PAIRS = [
        ('甲','己','土'), ('乙','庚','金'), ('丙','辛','水'), ('丁','壬','木'), ('戊','癸','火')
    ]
    # 天干相冲
    GAN_CHONG_PAIRS = [('甲','庚'),('乙','辛'),('丙','壬'),('丁','癸')]
    # 地支六合
    ZHI_LIU_HE_PAIRS = [
        ('子','丑','土'), ('寅','亥','木'), ('卯','戌','火'), ('辰','酉','金'), ('巳','申','水'), ('午','未','火')
    ]
    # 地支六冲
    ZHI_CHONG_PAIRS = [('子','午'),('丑','未'),('寅','申'),('卯','酉'),('辰','戌'),('巳','亥')]
    # 地支六害
    ZHI_HAI_PAIRS = [('子','未'),('丑','午'),('寅','巳'),('卯','辰'),('申','亥'),('酉','戌')]

    rels = []

    # 天干关系
    for a, b, name in GAN_HE_PAIRS:
        if (g1 == a and g2 == b) or (g1 == b and g2 == a):
            rels.append({'type': 'gan_he', 'desc': f'{g1}{g2}合化{name}', 'label': '合', 'positive': True})
    for a, b in GAN_CHONG_PAIRS:
        if (g1 == a and g2 == b) or (g1 == b and g2 == a):
            rels.append({'type': 'gan_chong', 'desc': f'{g1}{g2}冲', 'label': '冲', 'positive': False})

    # 地支关系
    for a, b, name in ZHI_LIU_HE_PAIRS:
        if (z1 == a and z2 == b) or (z1 == b and z2 == a):
            rels.append({'type': 'zhi_liu_he', 'desc': f'{z1}{z2}合化{name}', 'label': '合', 'positive': True})
    for a, b in ZHI_CHONG_PAIRS:
        if (z1 == a and z2 == b) or (z1 == b and z2 == a):
            rels.append({'type': 'zhi_liu_chong', 'desc': f'{z1}{z2}冲', 'label': '冲', 'positive': False})
    for a, b in ZHI_HAI_PAIRS:
        if (z1 == a and z2 == b) or (z1 == b and z2 == a):
            rels.append({'type': 'zhi_liu_hai', 'desc': f'{z1}{z2}害', 'label': '害', 'positive': False})

    return rels


def _calc_wuxing_complement(wx1, wx2):
    """五行互补分析"""
    WUXING = ['金', '木', '水', '火', '土']
    result = {}
    for wx in WUXING:
        c1 = wx1.get(wx, 0)
        c2 = wx2.get(wx, 0)
        total = c1 + c2
        if c1 == 0 and c2 > 0:
            status = '互补'
        elif c2 == 0 and c1 > 0:
            status = '互补'
        elif c1 == 0 and c2 == 0:
            status = '双缺'
        elif c1 >= 2 and c2 >= 2:
            status = '偏旺'
        else:
            status = '均衡'
        result[wx] = {'person1': c1, 'person2': c2, 'total': total, 'status': status}
    return result


def _calc_day_gan_relation(g1, g2):
    """日主天干关系"""
    GAN_HE_PAIRS = [('甲','己','土'), ('乙','庚','金'), ('丙','辛','水'), ('丁','壬','木'), ('戊','癸','火')]
    GAN_CHONG_PAIRS = [('甲','庚'),('乙','辛'),('丙','壬'),('丁','癸')]
    GAN_WUXING = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}

    rels = []
    for a, b, name in GAN_HE_PAIRS:
        if (g1 == a and g2 == b) or (g1 == b and g2 == a):
            rels.append(f'日主{g1}{g2}合化{name}')
    for a, b in GAN_CHONG_PAIRS:
        if (g1 == a and g2 == b) or (g1 == b and g2 == a):
            rels.append(f'日主{g1}{g2}相冲')
    wx1 = GAN_WUXING.get(g1, '')
    wx2 = GAN_WUXING.get(g2, '')
    if wx1 and wx2 and wx1 != wx2:
        rels.append(f'{wx1}命与{wx2}命')
    return rels


def _calc_hepan_score(pillar_compare, wx_complement, day_relation):
    """合盘综合评分 (0-100)"""
    score = 60  # 基础分

    # 干支关系评分
    for pc in pillar_compare:
        for r in pc.get('relations', []):
            if r.get('positive'):
                score += 4  # 合+4
            else:
                score -= 5  # 冲害-5

    # 五行互补评分
    for wx, info in wx_complement.items():
        if info['status'] == '互补':
            score += 3  # 互补加分
        elif info['status'] == '双缺':
            score -= 4  # 双缺扣分
        elif info['status'] == '偏旺':
            score -= 2  # 双方都偏旺

    # 日主关系
    for r in day_relation:
        if '合' in r:
            score += 5
        elif '冲' in r:
            score -= 5

    # 限制范围
    return max(20, min(98, score))


# ═══════════════════════════════════════════════════════════════
# 通用工具运行 API（六爻/梅花/紫微/择吉/塔罗等）
# ═══════════════════════════════════════════════════════════════

VALID_APP_TYPES = {'qimen', 'paipan', 'liuyao', 'meihua', 'ziwei', 'zeji', 'huangli', 'taluo'}

@app.route('/api/tool-run', methods=['POST'])
@login_required
@csrf.exempt
def api_tool_run():
    """通用工具运行接口 — 接收工具类型和参数，执行排盘+AI解读"""
    data = request.get_json(silent=True) or {}
    app_type = (data.get('appType') or '').strip()

    if app_type not in VALID_APP_TYPES:
        return jsonify({'error': f'不支持的工具类型: {app_type}'}), 400

    # 构建问题描述
    question_parts = []
    name = (data.get('name') or app_type).strip()
    question_parts.append(f'[{app_type}] {name}')

    if app_type == 'liuyao':
        method = data.get('method', 'coin')
        question_parts.append(f'起卦方式:{method}')
        if data.get('coinResult'): question_parts.append(f'铜钱:{data["coinResult"]}')
        if data.get('num1'): question_parts.append(f'数字:{data["num1"]}/{data.get("num2","")}')
        if data.get('time'): question_parts.append(f'时间:{data["time"]}')
    elif app_type == 'meihua':
        method = data.get('method', 'time')
        question_parts.append(f'起卦方式:{method}')
        if data.get('num1'): question_parts.append(f'数字:{data["num1"]}/{data.get("num2","")}')
        if data.get('char'): question_parts.append(f'字:{data["char"]}')
        if data.get('time'): question_parts.append(f'时间:{data["time"]}')
        # 用Python精准排盘，结果注入data供AI使用
        try:
            mh_result = _meihua_paipan(
                method=method,
                num1=data.get('num1'),
                num2=data.get('num2'),
                words=data.get('char') or data.get('words', ''),
                year=data.get('year'), month=data.get('month'),
                day=data.get('day'), hour=data.get('hour'),
            )
            if 'error' not in mh_result:
                data['_mh_paipan'] = mh_result
                question_parts.append(f'本卦:{mh_result.get("benGua",{}).get("name","")}')
                question_parts.append(f'变卦:{mh_result.get("bianGua",{}).get("name","")}')
                if mh_result.get('tiYong'):
                    ty = mh_result['tiYong']
                    question_parts.append(f'体:{ty.get("tiWuxing","")}({ty.get("tiPosition","")})')
                    question_parts.append(f'用:{ty.get("yongWuxing","")}({ty.get("yongPosition","")})')
                    question_parts.append(f'体用:{ty.get("tiYongRel","")}')
        except Exception:
            pass
    elif app_type == 'ziwei':
        question_parts.append(f'性别:{data.get("gender","男")}')
        question_parts.append(f'出生:{data.get("birthTime","")}')
        if data.get('birthAddr'): question_parts.append(f'出生地:{data["birthAddr"]}')
    elif app_type == 'zeji':
        question_parts.append(f'事项:{data.get("zejiType","")}')
        question_parts.append(f'日期:{data.get("startDate","")}~{data.get("endDate","")}')
    elif app_type == 'taluo':
        question_parts.append(f'牌阵:{data.get("spread_name","three")}')

    q = data.get('question') or data.get('time') or ''
    if q: question_parts.append(f'问题:{q}')

    question = ' | '.join(question_parts)

    # 检查是否有对应的shell脚本
    script_name = f'{app_type}_auto.sh'
    script_path = os.path.join(BASE_DIR, script_name)

    if os.path.exists(script_path):
        # 有shell脚本 — 走后台自动化（类似奇门问策）
        global current_run_id, current_process
        with current_lock:
            if current_process and current_process.poll() is None:
                current_process.terminate()
                try: current_process.wait(timeout=3)
                except subprocess.TimeoutExpired: current_process.kill()
            current_run_id += 1
            run_id = current_run_id

        cleanup_old_runs(run_id)
        write_run_status(run_id, {'phase': 'starting', 'message': '准备中...', 'progress': 0, 'run_id': run_id})

        # 写入参数文件
        run_dir = get_run_dir(run_id)
        with open(os.path.join(run_dir, 'params.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
            f.write(question)

        record = Record(question=question, user_id=current_user.id, app_type=app_type, run_id=run_id)
        db.session.add(record)
        db.session.commit()

        # 后台执行
        env = os.environ.copy()
        env['TOOL_PARAMS_FILE'] = os.path.join(run_dir, 'params.json')
        env['QIMEN_QUESTION_FILE'] = os.path.join(run_dir, 'question.txt')
        env['QIMEN_RUN_DIR'] = run_dir
        env['QIMEN_RUN_ID'] = str(run_id)

        def run_tool():
            global current_process
            try:
                stdout_log = open(os.path.join(run_dir, 'stdout.log'), 'w')
                stderr_log = open(os.path.join(run_dir, 'stderr.log'), 'w')
                proc = subprocess.Popen(['bash', script_path], env=env, stdout=stdout_log, stderr=stderr_log)
                with current_lock: current_process = proc
                proc.wait()
                stdout_log.close(); stderr_log.close()

                with current_lock:
                    if run_id != current_run_id: return

                result = read_run_result(run_id)
                if result:
                    write_run_status(run_id, {'phase': 'done', 'message': '解读完成', 'progress': 100, 'run_id': run_id})
                    with app.app_context():
                        rec = db.session.get(Record, record.id)
                        if rec:
                            rec.result_html = result
                            db.session.commit()
                else:
                    write_run_status(run_id, {'phase': 'error', 'message': '自动化完成但未获取到结果', 'progress': 0})
            except Exception as e:
                write_run_status(run_id, {'phase': 'error', 'message': str(e), 'progress': 0})

        t = threading.Thread(target=run_tool, daemon=True)
        t.start()
        return jsonify({'status': 'started', 'run_id': run_id, 'record_id': record.id})

    else:
        # 无shell脚本 — 直接使用AI解读（基于问题生成解读）
        # 生成结构化排盘描述 + AI解读请求
        ai_prompt = _build_ai_prompt(app_type, data)
        result_text = _generate_ai_reading(app_type, ai_prompt, question, data)

        record = Record(
            question=question, user_id=current_user.id,
            app_type=app_type, result_html=result_text,
        )
        db.session.add(record)
        db.session.commit()

        return jsonify({
            'success': True,
            'result': result_text,
            'message': result_text,
            'record_id': record.id,
        })


def _build_ai_prompt(app_type, data):
    """构建AI解读的prompt"""
    prompts = {
        'liuyao': f"请根据六爻排盘参数进行解卦。起卦方式:{data.get('method','coin')}，"
                  f"问题:{data.get('question','综合解卦')}。"
                  f"请按传统六爻规则排盘并给出卦宫、世应、动爻、六亲、六神分析，"
                  f"最后给出简明白话解读和行动建议。"
                  f"注意：内容仅为民俗文化参考，不构成任何决策建议。",

        'meihua': f"请根据梅花易数参数进行起卦解读。起卦方式:{data.get('method','time')}，"
                  f"问题:{data.get('question','综合解读')}。"
                  + (f"\n排盘结果：本卦={data.get('_mh_paipan',{}).get('benGua',{}).get('name','')}, "
                     f"互卦={data.get('_mh_paipan',{}).get('huGua',{}).get('name','')}, "
                     f"变卦={data.get('_mh_paipan',{}).get('bianGua',{}).get('name','')}, "
                     f"动爻={data.get('_mh_paipan',{}).get('dongYao','')}, "
                     f"体用={data.get('_mh_paipan',{}).get('tiYong',{}).get('tiYongRel','')}, "
                     f"吉凶={data.get('_mh_paipan',{}).get('tiYong',{}).get('tiYongJiXiong','')}, "
                     f"断语={data.get('_mh_paipan',{}).get('tiYong',{}).get('verdict','')}。"
                     if data.get('_mh_paipan') else "")
                  + f"请基于以上排盘结果，给出本卦、互卦、变卦、体用生克的专业分析，"
                  f"最后给出简明白话解读和行动建议。"
                  f"注意：内容仅为民俗文化参考，不构成任何决策建议。",

        'ziwei': f"请根据紫微斗数参数进行命盘解读。性别:{data.get('gender','男')}，"
                 f"出生时间:{data.get('birthTime','')}，出生地:{data.get('birthAddr','')}。"
                 f"请按紫微斗数规则排盘并给出十二宫、主星、四化、流年大运分析，"
                 f"最后给出简明白话解读。"
                 f"注意：内容仅为民俗文化参考，不构成任何决策建议。",

        'zeji': f"请根据择吉参数进行分析。事项:{data.get('zejiType','')}，"
                f"日期范围:{data.get('startDate','')}~{data.get('endDate','')}。"
                f"请给出宜忌吉日、吉时、冲煞提醒，以及择吉建议。"
                f"注意：内容仅为民俗文化参考，不构成任何决策建议。",

        'taluo': f"请进行塔罗牌解读。牌阵:{data.get('spread','three')}，"
                 f"问题:{data.get('question','综合解读')}。"
                 f"请随机抽取对应数量的塔罗牌，给出正/逆位、牌意解读和综合建议。"
                 f"注意：内容仅为民俗文化参考，不构成任何决策建议。",
    }
    return prompts.get(app_type, '请进行综合解读。注意：内容仅为民俗文化参考。')


def _generate_ai_reading(app_type, prompt, question, data=None):
    """生成AI解读 — 当前使用结构化模板，后续可对接真实AI接口"""
    from datetime import datetime
    now = datetime.now().strftime('%Y年%m月%d日 %H:%M')

    # 提取梅花排盘数据
    mh = (data or {}).get('_mh_paipan', {})

    templates = {
        'liuyao': f"""═══ 六爻排盘解读 ═══
起卦时间：{now}
问事：{question}

【排盘参数已接收，AI解读生成中...】
当前版本为模板解读，完整排盘功能开发中。

── 卦象分析 ──
根据起卦参数，本卦与变卦已生成。
世爻代表问卦者自身，应爻代表所问之事。
动爻为变化之关键，需重点关注。

── 综合解读 ──
当前为系统内测阶段，完整AI解卦功能即将上线。
建议您使用「天机问策」获取完整的AI解读。

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",

        'meihua': f"""═══ 梅花易数解读 ═══
起卦时间：{now}
问事：{question}

── 排盘结果 ──
本卦：{mh.get('benGua',{}).get('name','') if mh else '待排'}
  上卦：{mh.get('benGua',{}).get('upper',{}).get('name','')}({mh.get('benGua',{}).get('upper',{}).get('wuxing','')}) {mh.get('benGua',{}).get('upper',{}).get('nature','')}
  下卦：{mh.get('benGua',{}).get('lower',{}).get('name','')}({mh.get('benGua',{}).get('lower',{}).get('wuxing','')}) {mh.get('benGua',{}).get('lower',{}).get('nature','')}
  动爻：第{mh.get('dongYao','')}爻
互卦：{mh.get('huGua',{}).get('name','') if mh else ''}
变卦：{mh.get('bianGua',{}).get('name','') if mh else ''}
干支：{mh.get('ganzhi','') if mh else ''}

── 体用分析 ──
体卦：{mh.get('tiYong',{}).get('tiGua','')}({mh.get('tiYong',{}).get('tiPosition','')}) {mh.get('tiYong',{}).get('tiWuxing','')} {mh.get('tiYong',{}).get('tiWangshuai','')}
用卦：{mh.get('tiYong',{}).get('yongGua','')}({mh.get('tiYong',{}).get('yongPosition','')}) {mh.get('tiYong',{}).get('yongWuxing','')} {mh.get('tiYong',{}).get('yongWangshuai','')}
体用关系：体{mh.get('tiYong',{}).get('tiWuxing','')} {mh.get('tiYong',{}).get('tiYongRel','')} 用{mh.get('tiYong',{}).get('yongWuxing','')}
吉凶：{mh.get('tiYong',{}).get('tiYongJiXiong','')}
断语：{mh.get('tiYong',{}).get('verdict','')}

── 综合解读 ──
体卦代表自身，用卦代表所问之事。
体用生克关系决定事物发展趋势。
{mh.get('tiYong',{}).get('verdict','') if mh else ''}

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",

        'ziwei': f"""═══ 紫微斗数命盘解读 ═══
排盘时间：{now}
问事：{question}

【排盘参数已接收，AI解读生成中...】
当前版本为模板解读，完整排盘功能开发中。

── 命盘分析 ──
根据出生信息，十二宫位与主星已排布完成。
命宫为命盘核心，决定基本性格与人生走向。
四化飞星为流年变化的关键。

── 综合解读 ──
当前为系统内测阶段，完整紫微斗数AI解读功能即将上线。

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",

        'zeji': f"""═══ 择吉分析 ═══
分析时间：{now}
事项：{question}

【择吉参数已接收，分析生成中...】
当前版本为模板分析，完整择吉功能开发中。

── 吉日推荐 ──
根据择吉事项与日期范围，筛选出以下吉日：
（完整黄历数据对接后，将显示详细宜忌信息）

── 综合建议 ──
当前为系统内测阶段，完整择吉功能即将上线。
您可使用「黄历万年历」查询每日宜忌。

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",

        'taluo': f"""═══ 塔罗牌解读 ═══
抽牌时间：{now}
牌阵：{data.get('spread_name', 'three') if 'data' in dir() else '三张牌'}
问事：{question}

【牌阵已生成，AI解读中...】
当前版本为模板解读，完整塔罗功能开发中。

── 牌意解读 ──
根据牌阵类型，已抽取对应数量的塔罗牌。
每张牌的正逆位与位置含义不同，需综合分析。

── 综合解读 ──
当前为系统内测阶段，完整塔罗牌AI解读功能即将上线。

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",
    }

    return templates.get(app_type, f'解读生成中...当前为模板解读，完整功能即将上线。\n\n⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。')


# ═══════════════════════════════════════════════════════════════
# 认证 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/register', methods=['POST'])
@csrf.exempt
def api_register():
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if len(username) < 2 or len(username) > 20:
        return jsonify({'error': '用户名需2-20个字符'}), 400
    if len(password) < 6:
        return jsonify({'error': '密码至少6个字符'}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({'error': '用户名已存在'}), 400

    user = User(username=username, password_hash=generate_password_hash(password, method='pbkdf2:sha256'), has_password=True)
    db.session.add(user)
    db.session.commit()
    login_user(user, remember=True)
    return jsonify({'id': user.id, 'username': user.username, 'has_password': user.has_password, 'avatar': user.avatar or '', 'created_at': user.created_at.isoformat() if user.created_at else None}), 201

@app.route('/api/login', methods=['POST'])
@csrf.exempt
def api_login():
    data = request.get_json(silent=True) or {}
    if not _check_rate_limit('login_' + request.remote_addr, 10, 300):
        return jsonify({'error': '登录尝试过于频繁，请5分钟后再试'}), 429
    login_id = (data.get('username') or '').strip()
    password = data.get('password') or ''

    user = User.query.filter(
        or_(
            User.username == login_id,
            User.email == login_id,
            User.phone == login_id
        )
    ).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': '用户名或密码错误'}), 401

    login_user(user, remember=True)
    return jsonify({'id': user.id, 'username': user.username, 'has_password': user.has_password, 'avatar': user.avatar or '', 'created_at': user.created_at.isoformat() if user.created_at else None})

@app.route('/api/logout', methods=['POST'])
@login_required
@csrf.exempt
def api_logout():
    logout_user()
    return jsonify({'ok': True})

@app.route('/api/me')
def api_me():
    if current_user.is_authenticated:
        return jsonify({'id': current_user.id, 'username': current_user.username, 'has_password': current_user.has_password, 'avatar': current_user.avatar or '', 'created_at': current_user.created_at.isoformat() if current_user.created_at else None, 'is_admin': current_user.is_admin})
    return jsonify({'guest': True})

# ─── 账号绑定 API ───

@app.route('/api/user/bindings')
@login_required
def api_user_bindings():
    """查询当前用户的绑定信息"""
    return jsonify({
        'username': current_user.username,
        'email': current_user.email or '',
        'phone': current_user.phone or '',
        'has_password': current_user.has_password,
        'oauth_gitee': bool(current_user.oauth_gitee),
        'oauth_qq': bool(current_user.oauth_qq),
        'oauth_wechat': bool(current_user.oauth_wechat)
    })

@app.route('/api/bind/email', methods=['POST'])
@login_required
@csrf.exempt
def api_bind_email():
    """绑定邮箱（需验证码）"""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    code = (data.get('code') or '').strip()
    if not email or not code:
        return jsonify({'error': '请填写完整'}), 400
    if not _check_code('email_' + email, code):
        return jsonify({'error': '验证码错误或已过期'}), 400
    # 检查邮箱是否已被其他用户绑定
    existing = User.query.filter(User.email == email, User.id != current_user.id).first()
    if existing:
        return jsonify({'error': '该邮箱已被其他账号绑定'}), 400
    current_user.email = email
    db.session.commit()
    return jsonify({'ok': True, 'email': email})

@app.route('/api/bind/phone', methods=['POST'])
@login_required
@csrf.exempt
def api_bind_phone():
    """绑定手机号（需验证码）"""
    data = request.get_json(silent=True) or {}
    phone = (data.get('phone') or '').strip()
    code = (data.get('code') or '').strip()
    if not phone or not code:
        return jsonify({'error': '请填写完整'}), 400
    if not _check_code('sms_' + phone, code):
        return jsonify({'error': '验证码错误或已过期'}), 400
    existing = User.query.filter(User.phone == phone, User.id != current_user.id).first()
    if existing:
        return jsonify({'error': '该手机号已被其他账号绑定'}), 400
    current_user.phone = phone
    db.session.commit()
    return jsonify({'ok': True, 'phone': phone})

@app.route('/api/bind/password', methods=['POST'])
@login_required
@csrf.exempt
def api_bind_password():
    """设置/修改密码"""
    data = request.get_json(silent=True) or {}
    old_pw = data.get('old_password') or ''
    new_pw = data.get('new_password') or ''

    if len(new_pw) < 6:
        return jsonify({'error': '密码至少6个字符'}), 400

    # 如果有旧密码，需要验证
    if current_user.has_password:
        if not check_password_hash(current_user.password_hash, old_pw):
            return jsonify({'error': '原密码不正确'}), 400

    current_user.password_hash = generate_password_hash(new_pw, method='pbkdf2:sha256')
    current_user.has_password = True
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/unbind/email', methods=['POST'])
@login_required
@csrf.exempt
def api_unbind_email():
    """解绑邮箱"""
    if not current_user.has_password and not current_user.phone:
        return jsonify({'error': '请先设置密码或绑定手机号后再解绑邮箱'}), 400
    current_user.email = None
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/unbind/phone', methods=['POST'])
@login_required
@csrf.exempt
def api_unbind_phone():
    """解绑手机号"""
    if not current_user.has_password and not current_user.email:
        return jsonify({'error': '请先设置密码或绑定邮箱后再解绑手机号'}), 400
    current_user.phone = None
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/user/change-username', methods=['POST'])
@csrf.exempt
@login_required
def api_user_change_username():
    """修改用户名"""
    data = request.get_json(silent=True) or {}
    new_username = (data.get('new_username', '') or '').strip()
    if not new_username or len(new_username) < 2:
        return jsonify({'error': '用户名至少2个字符'}), 400
    if current_user.has_password:
        current_password = data.get('current_password', '')
        if not current_password:
            return jsonify({'error': '请输入当前密码'}), 400
        from werkzeug.security import check_password_hash
        if not check_password_hash(current_user.password_hash, current_password):
            return jsonify({'error': '当前密码错误'}), 403
    if User.query.filter_by(username=new_username).first():
        return jsonify({'error': '用户名已被使用'}), 400
    old_username = current_user.username
    current_user.username = new_username
    db.session.commit()
    return jsonify({'ok': True, 'old_username': old_username, 'new_username': new_username})


@app.route('/api/user/change-password', methods=['POST'])
@csrf.exempt
@login_required
def api_user_change_password():
    """修改/设置密码"""
    data = request.get_json(silent=True) or {}
    new_password = data.get('new_password', '')
    if not new_password or len(new_password) < 4:
        return jsonify({'error': '新密码至少4个字符'}), 400
    from werkzeug.security import check_password_hash, generate_password_hash
    if current_user.has_password:
        old_password = data.get('old_password', '')
        if not old_password:
            return jsonify({'error': '请输入当前密码'}), 400
        if not check_password_hash(current_user.password_hash, old_password):
            return jsonify({'error': '当前密码错误'}), 403
    current_user.password_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
    current_user.has_password = True
    db.session.commit()
    return jsonify({'ok': True})


# ═══════════════════════════════════════════════
# OAuth 登录（QQ / 微信）
# ═══════════════════════════════════════════════

QQ_APP_ID = os.environ.get('QQ_APP_ID', '')
QQ_APP_KEY = os.environ.get('QQ_APP_KEY', '')
QQ_CALLBACK_URL = os.environ.get('QQ_CALLBACK_URL', 'http://localhost:5199/api/oauth/qq/callback')
WECHAT_APP_ID = os.environ.get('WECHAT_APP_ID', '')
WECHAT_APP_SECRET = os.environ.get('WECHAT_APP_SECRET', '')
WECHAT_CALLBACK_URL = os.environ.get('WECHAT_CALLBACK_URL', 'http://localhost:5199/api/oauth/wechat/callback')
OAUTH_ORIGIN = os.environ.get('OAUTH_ORIGIN', 'http://localhost:3001')

@app.route('/api/oauth/qq/url')
def api_oauth_qq_url():
    """返回 QQ OAuth 授权 URL（前端直接跳转）"""
    if not QQ_APP_ID:
        return jsonify({'url': '', 'error': 'QQ登录暂未配置，请使用账号密码登录'})
    import uuid as _uuid
    redirect_uri = urllib.parse.quote(QQ_CALLBACK_URL)
    state = str(_uuid.uuid4().hex[:8])
    session['oauth_qq_state'] = state
    url = f"https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id={QQ_APP_ID}&redirect_uri={redirect_uri}&state={state}&scope=get_user_info"
    return jsonify({'url': url})

@app.route('/api/oauth/qq/callback')
def api_oauth_qq_callback():
    """QQ OAuth 回调 — 获取 access_token → openid → 创建/绑定用户"""
    code = request.args.get('code', '')
    state = request.args.get('state', '')
    if not code:
        return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=QQ登录取消")
    try:
        # 1. 用 code 换 access_token
        token_url = f"https://graph.qq.com/oauth2.0/token?grant_type=authorization_code&client_id={QQ_APP_ID}&client_secret={QQ_APP_KEY}&code={code}&redirect_uri={QQ_CALLBACK_URL}&fmt=json"
        import urllib.request as _ur, json as _json
        token_resp = _json.loads(_ur.urlopen(_ur.Request(token_url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10).read().decode())
        access_token = token_resp.get('access_token', '')
        if not access_token:
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=QQ登录失败")
        # 2. 用 access_token 拿 openid
        openid_url = f"https://graph.qq.com/oauth2.0/me?access_token={access_token}&fmt=json"
        me_resp = _json.loads(_ur.urlopen(_ur.Request(openid_url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10).read().decode())
        openid = me_resp.get('openid', '')
        if not openid:
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=QQ登录获取信息失败")
        if current_user.is_authenticated:
            current_user.oauth_qq = openid
            db.session.commit()
            logger.info(f"[QQ OAuth] 绑定到已有用户 {current_user.username}")
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_success=qq")
        user = User.query.filter_by(oauth_qq=openid).first()
        if not user:
            user = User(username=f'qq_{openid[:8]}', password_hash=generate_password_hash(openid, method='pbkdf2:sha256'), oauth_qq=openid)
            db.session.add(user)
            db.session.commit()
        login_user(user, remember=True)
        return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_success=qq")
    except Exception as e:
        logger.error(f"[QQ OAuth] 回调处理失败: {e}")
        return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=QQ登录异常")

@app.route('/api/oauth/wechat/url')
def api_oauth_wechat_url():
    """返回微信 OAuth 授权 URL（前端直接跳转）"""
    if not WECHAT_APP_ID:
        return jsonify({'url': '', 'error': '微信登录暂未配置，请使用账号密码登录'})
    import uuid as _uuid
    redirect_uri = urllib.parse.quote(WECHAT_CALLBACK_URL)
    state = str(_uuid.uuid4().hex[:8])
    session['oauth_wechat_state'] = state
    url = f"https://open.weixin.qq.com/connect/qrconnect?appid={WECHAT_APP_ID}&redirect_uri={redirect_uri}&response_type=code&scope=snsapi_login&state={state}#wechat_redirect"
    return jsonify({'url': url})

@app.route('/api/oauth/wechat/callback')
def api_oauth_wechat_callback():
    """微信 OAuth 回调 — 获取 access_token → openid → 创建/绑定用户"""
    code = request.args.get('code', '')
    state = request.args.get('state', '')
    if not code:
        return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=微信登录取消")
    try:
        import urllib.request as _ur, json as _json
        # 1. 用 code 换 access_token
        token_url = f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={WECHAT_APP_ID}&secret={WECHAT_APP_SECRET}&code={code}&grant_type=authorization_code"
        token_resp = _json.loads(_ur.urlopen(_ur.Request(token_url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=10).read().decode())
        access_token = token_resp.get('access_token', '')
        openid = token_resp.get('openid', '')
        if not openid:
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=微信登录失败")
        if current_user.is_authenticated:
            current_user.oauth_wechat = openid
            db.session.commit()
            logger.info(f"[WeChat OAuth] 绑定到已有用户 {current_user.username}")
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_success=wechat")
        user = User.query.filter_by(oauth_wechat=openid).first()
        if not user:
            user = User(username=f'wx_{openid[:8]}', password_hash=generate_password_hash(openid, method='pbkdf2:sha256'), oauth_wechat=openid)
            db.session.add(user)
            db.session.commit()
        login_user(user, remember=True)
        return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_success=wechat")
    except Exception as e:
        logger.error(f"[WeChat OAuth] 回调处理失败: {e}")
        return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=微信登录异常")


# ═══════════════════════════════════════════════
# Gitee OAuth 登录
# ═══════════════════════════════════════════════

GITEE_CLIENT_ID = os.environ.get('GITEE_CLIENT_ID', '')
GITEE_CLIENT_SECRET = os.environ.get('GITEE_CLIENT_SECRET', '')
GITEE_CALLBACK_URL = os.environ.get('GITEE_CALLBACK_URL', 'http://localhost:5199/api/oauth/gitee/callback')

@app.route('/api/oauth/gitee/url')
def api_oauth_gitee_url():
    if not GITEE_CLIENT_ID:
        return jsonify({'url': '', 'error': 'Gitee登录暂未配置，请使用其他方式登录'})
    import uuid as _uuid
    state = str(_uuid.uuid4().hex[:8])
    session['oauth_gitee_state'] = state
    url = f"https://gitee.com/oauth/authorize?client_id={GITEE_CLIENT_ID}&redirect_uri={urllib.parse.quote(GITEE_CALLBACK_URL)}&response_type=code&state={state}"
    return jsonify({'url': url})

@app.route('/api/oauth/gitee/callback')
def api_oauth_gitee_callback():
    code = request.args.get('code', '')
    if not code:
        return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=Gitee登录取消")
    try:
        import urllib.request as _ur
        token_url = f"https://gitee.com/oauth/token?grant_type=authorization_code&code={code}&client_id={GITEE_CLIENT_ID}&redirect_uri={urllib.parse.quote(GITEE_CALLBACK_URL)}&client_secret={GITEE_CLIENT_SECRET}"
        token_resp = json.loads(_ur.urlopen(_ur.Request(token_url, data=b'', headers={'Accept': 'application/json'}), timeout=10).read().decode())
        access_token = token_resp.get('access_token', '')
        if not access_token:
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=Gitee登录失败")
        user_url = f"https://gitee.com/api/v5/user?access_token={access_token}"
        user_resp = json.loads(_ur.urlopen(_ur.Request(user_url, headers={'Accept': 'application/json'}), timeout=10).read().decode())
        gitee_id = str(user_resp.get('id', ''))
        if not gitee_id:
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=Gitee获取信息失败")
        if current_user.is_authenticated:
            current_user.oauth_gitee = gitee_id
            db.session.commit()
            logger.info(f"[Gitee OAuth] 绑定到已有用户 {current_user.username}")
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_success=gitee")
        user = User.query.filter_by(oauth_gitee=gitee_id).first()
        if not user:
            username = user_resp.get('login', f'gitee_{gitee_id[:8]}')
            user = User(username=username, password_hash=generate_password_hash(gitee_id, method='pbkdf2:sha256'), oauth_gitee=gitee_id)
            avatar_url = user_resp.get('avatar_url', '')
            if avatar_url:
                user.avatar = avatar_url
            db.session.add(user)
            db.session.commit()
        login_user(user, remember=True)
        return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_success=gitee")
    except Exception as e:
        logger.error(f"[Gitee OAuth] 回调处理失败: {e}")
        return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=Gitee登录异常")

# ═══════════════════════════════════════════════
# 验证码登录（手机 / 邮箱）
# ═══════════════════════════════════════════════

# 环境变量
ALIYUN_SMS_ACCESS_KEY_ID = os.environ.get('ALIYUN_SMS_ACCESS_KEY_ID', '')
ALIYUN_SMS_ACCESS_KEY_SECRET = os.environ.get('ALIYUN_SMS_ACCESS_KEY_SECRET', '')
ALIYUN_SMS_SIGN_NAME = os.environ.get('ALIYUN_SMS_SIGN_NAME', '')
ALIYUN_SMS_TEMPLATE_CODE = os.environ.get('ALIYUN_SMS_TEMPLATE_CODE', '')
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.qq.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', '时安解忧屋')

# 验证码存储（生产环境应改用 Redis）
import random as _random
_verify_code_store = {}

_rate_limit_store = {}
_rate_limit_lock = threading.Lock()

def _check_rate_limit(key, max_count=5, window=60):
    now = time.time()
    with _rate_limit_lock:
        entry = _rate_limit_store.get(key)
        if not entry or now - entry['ts'] > window:
            _rate_limit_store[key] = {'count': 1, 'ts': now}
            return True
        if entry['count'] >= max_count:
            return False
        entry['count'] += 1
        return True

def _gen_code():
    return str(_random.randint(100000, 999999))

def _store_code(key, code):
    _verify_code_store[key] = {'code': code, 'ts': time.time()}

def _check_code(key, code):
    entry = _verify_code_store.get(key)
    if not entry: return False
    if time.time() - entry['ts'] > 300:  # 5分钟有效
        _verify_code_store.pop(key, None)
        return False
    if entry['code'] != code: return False
    _verify_code_store.pop(key, None)
    return True

@app.route('/api/sms/send', methods=['POST'])
@csrf.exempt
def api_sms_send():
    data = request.get_json(silent=True) or {}
    phone = (data.get('phone') or '').strip()
    if not phone or not phone.isdigit() or len(phone) < 11:
        return jsonify({'error': '手机号格式不正确'}), 400
    if not _check_rate_limit('sms_' + phone, 3, 60) or not _check_rate_limit('sms_ip_' + request.remote_addr, 10, 60):
        return jsonify({'error': '发送过于频繁，请稍后再试'}), 429
    if not ALIYUN_SMS_ACCESS_KEY_ID or not ALIYUN_SMS_ACCESS_KEY_SECRET:
        code = _gen_code()
        _store_code('sms_' + phone, code)
        logger.info(f"[SMS Debug] 手机 {phone} 验证码: {code}")
        return jsonify({'ok': True})
    try:
        code = _gen_code()
        # 阿里云短信 SDK 调用
        from aliyunsdkcore.client import AcsClient
        from aliyunsdkdysmsapi.request.v20170525 import SendSmsRequest
        client = AcsClient(ALIYUN_SMS_ACCESS_KEY_ID, ALIYUN_SMS_ACCESS_KEY_SECRET, 'cn-hangzhou')
        req = SendSmsRequest.SendSmsRequest()
        req.set_PhoneNumbers(phone)
        req.set_SignName(ALIYUN_SMS_SIGN_NAME)
        req.set_TemplateCode(ALIYUN_SMS_TEMPLATE_CODE)
        req.set_TemplateParam(json.dumps({'code': code}))
        resp = client.do_action_with_exception(req)
        resp_data = json.loads(resp)
        if resp_data.get('Code') != 'OK':
            logger.error(f"[SMS] 发送失败: {resp_data}")
            return jsonify({'error': '短信发送失败，请稍后重试'}), 500
        _store_code('sms_' + phone, code)
        return jsonify({'ok': True})
    except ImportError:
        _store_code('sms_' + phone, code)
        logger.info(f"[SMS Debug] (无阿里云SDK) 手机 {phone} 验证码: {code}")
        return jsonify({'ok': True})
    except Exception as e:
        logger.error(f"[SMS] 发送异常: {e}")
        return jsonify({'error': '短信发送失败，请稍后重试'}), 500

@app.route('/api/sms/login', methods=['POST'])
@csrf.exempt
def api_sms_login():
    """手机验证码登录（仅限已绑定手机号的用户）"""
    data = request.get_json(silent=True) or {}
    phone = (data.get('phone') or '').strip()
    code = (data.get('code') or '').strip()
    if not phone or not code:
        return jsonify({'error': '请填写完整'}), 400
    if not _check_code('sms_' + phone, code):
        return jsonify({'error': '验证码错误或已过期'}), 400
    user = User.query.filter_by(phone=phone).first()
    if not user:
        return jsonify({'error': '该手机号未绑定账号，请先使用密码登录或注册后再绑定'}), 400
    login_user(user, remember=True)
    return jsonify({'id': user.id, 'username': user.username, 'has_password': user.has_password, 'avatar': user.avatar or '', 'created_at': user.created_at.isoformat() if user.created_at else None})

@app.route('/api/email/send', methods=['POST'])
@csrf.exempt
def api_email_send():
    data = request.get_json(silent=True) or {}
    addr = (data.get('email') or '').strip()
    if not addr or '@' not in addr:
        return jsonify({'error': '邮箱格式不正确'}), 400
    if not _check_rate_limit('email_' + addr, 3, 60) or not _check_rate_limit('email_ip_' + request.remote_addr, 10, 60):
        return jsonify({'error': '发送过于频繁，请稍后再试'}), 429
    code = _gen_code()
    _store_code('email_' + addr, code)
    logger.info(f"[Email Debug] 邮箱 {addr} 验证码: {code}")
    if not SMTP_USER or not SMTP_PASS:
        return jsonify({'ok': True})
    try:
        import smtplib
        import email.utils
        from email.mime.text import MIMEText
        from email.header import Header
        msg = MIMEText(f'您的验证码为：{code}，5分钟内有效。如非本人操作请忽略。', 'plain', 'utf-8')
        msg['Subject'] = Header(f'{SMTP_FROM_NAME} - 登录验证码', 'utf-8')
        msg['From'] = email.utils.formataddr((SMTP_FROM_NAME, SMTP_USER))
        msg['To'] = addr
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, [addr], msg.as_string())
        return jsonify({'ok': True})
    except Exception as e:
        logger.error(f"[Email] 发送异常: {e}（已回退到调试模式）")
        return jsonify({'ok': True})

@app.route('/api/email/login', methods=['POST'])
@csrf.exempt
def api_email_login():
    """邮箱验证码登录（仅限已绑定邮箱的用户）"""
    data = request.get_json(silent=True) or {}
    email = (data.get('email') or '').strip()
    code = (data.get('code') or '').strip()
    if not email or not code:
        return jsonify({'error': '请填写完整'}), 400
    if not _check_code('email_' + email, code):
        return jsonify({'error': '验证码错误或已过期'}), 400
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'error': '该邮箱未绑定账号，请先使用密码登录或注册后再绑定'}), 400
    login_user(user, remember=True)
    return jsonify({'id': user.id, 'username': user.username, 'has_password': user.has_password, 'avatar': user.avatar or '', 'created_at': user.created_at.isoformat() if user.created_at else None})


# ═══════════════════════════════════════════════════════════════
# 历史记录 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/records')
@login_required
def api_records():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    app_type = request.args.get('app_type', '')  # '' | 'qimen' | 'paipan'

    query = Record.query.filter_by(user_id=current_user.id)
    if app_type:
        query = query.filter_by(app_type=app_type)

    pagination = query.order_by(Record.created_at.desc())\
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
    """清空当前用户所有记录"""
    count = Record.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({'ok': True, 'deleted': count})


# ═══════════════════════════════════════════════════════════════
# 命盘存档 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/profiles', methods=['GET'])
@login_required
def api_profiles_list():
    """获取当前用户所有命盘存档，支持按类型/姓名搜索，按最近使用排序"""
    profile_type = request.args.get('type', '')  # self|customer|collect|''
    search = (request.args.get('search') or '').strip()
    sort = request.args.get('sort', 'last_used')  # last_used|created

    try:
        ensure_bazi_records_synced_to_profiles(current_user.id)
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
    except OperationalError as _e:
        # 数据库 schema 不兼容时（如字段缺失）降级返回空列表
        logger.warning(f"查询命盘列表失败（DB schema）: {_e}")
        profiles = []

    return jsonify({'profiles': [_serialize_user_profile(p) for p in profiles]})


def _serialize_user_profile(p):
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

@app.route('/api/profiles', methods=['POST'])
@login_required
def api_profiles_create():
    """创建命盘存档"""
    data = request.get_json(silent=True) or {}
    name = (data.get('name') or '').strip()
    if not name:
        return jsonify({'error': '缺少姓名'}), 400
    birth_time = (data.get('birthTime') or '').strip()
    if not birth_time or len(birth_time) < 8:
        return jsonify({'error': '缺少出生时间'}), 400

    profile_type = data.get('profileType', 'self')
    if profile_type not in ('self', 'customer', 'collect'):
        profile_type = 'self'

    p = UserProfile(
        user_id=current_user.id, name=name,
        gender=data.get('gender', '男'),
        cal_type=data.get('calType', '公历'),
        birth_time=birth_time,
        birth_addr=(data.get('birthAddr') or '').strip(),
        is_default=data.get('isDefault', False),
        profile_type=profile_type,
        source='manual',
        meta_json=json.dumps(data.get('meta') or {}, ensure_ascii=False),
    )
    # 如果设为默认，取消其他默认
    if p.is_default:
        UserProfile.query.filter_by(user_id=current_user.id, is_default=True)\
            .update({'is_default': False})
    db.session.add(p)
    db.session.commit()
    return jsonify({'id': p.id, 'name': p.name, 'profileType': p.profile_type}), 201

@app.route('/api/profiles/<int:pid>', methods=['DELETE'])
@login_required
def api_profiles_delete(pid):
    p = db.session.get(UserProfile, pid)
    if not p or p.user_id != current_user.id:
        return jsonify({'error': '无权操作'}), 403
    db.session.delete(p)
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/profiles/<int:pid>/touch', methods=['POST'])
@login_required
def api_profiles_touch(pid):
    """更新命盘最近使用时间"""
    p = db.session.get(UserProfile, pid)
    if not p or p.user_id != current_user.id:
        return jsonify({'error': '无权操作'}), 403
    p.last_used_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'ok': True})


def sync_bazi_record_to_profile(user_id, record, params_data, paipan_result=None):
    """八字排盘记录同步为通用命盘档案，供首页和其他术数共用。"""
    if not user_id or not record:
        return None
    meta = dict(params_data or {})
    meta.update({
        'source': 'bazi_record',
        'record_id': record.id,
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


def ensure_bazi_records_synced_to_profiles(user_id, limit=80):
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
        sync_bazi_record_to_profile(user_id, record, params_data, None)
        count += 1
    db.session.commit()
    return count


@app.route('/api/profiles/customer', methods=['GET'])
@login_required
def api_profiles_customer():
    """获取客户命盘列表，支持搜索/排序"""
    search = (request.args.get('search') or '').strip()
    sort = request.args.get('sort', 'last_used')
    query = UserProfile.query.filter_by(user_id=current_user.id, profile_type='customer')
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


@app.route('/api/profiles/collect', methods=['GET'])
@login_required
def api_profiles_collect():
    """获取收藏命盘列表，支持搜索/排序"""
    search = (request.args.get('search') or '').strip()
    sort = request.args.get('sort', 'last_used')
    query = UserProfile.query.filter_by(user_id=current_user.id, profile_type='collect')
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


@app.route('/api/profiles/export', methods=['GET'])
@login_required
def api_profiles_export():
    """导出命盘数据为JSON"""
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


# ═══════════════════════════════════════════════════════════════
# 问事跟进 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/followups', methods=['GET'])
@login_required
def api_followups_list():
    """获取跟进列表，可按 record_id 过滤"""
    record_id = request.args.get('record_id', type=int)
    query = FollowUp.query.filter_by(user_id=current_user.id)
    if record_id:
        query = query.filter_by(record_id=record_id)
    items = query.order_by(FollowUp.created_at.desc()).limit(50).all()
    return jsonify({'followups': [{
        'id': f.id, 'recordId': f.record_id, 'note': f.note,
        'feedback': f.feedback,
        'createdAt': f.created_at.isoformat() if f.created_at else None,
    } for f in items]})

@app.route('/api/followups', methods=['POST'])
@login_required
def api_followups_create():
    """创建跟进"""
    data = request.get_json(silent=True) or {}
    record_id = data.get('recordId')
    note = (data.get('note') or '').strip()
    if not record_id or not note:
        return jsonify({'error': '缺少参数'}), 400
    # 校验记录归属
    rec = db.session.get(Record, record_id)
    if not rec or rec.user_id != current_user.id:
        return jsonify({'error': '无权操作'}), 403
    f = FollowUp(
        user_id=current_user.id, record_id=record_id,
        note=note, feedback=data.get('feedback', '待验证'),
    )
    db.session.add(f)
    db.session.commit()
    return jsonify({'id': f.id}), 201

@app.route('/api/followups/<int:fid>', methods=['PUT'])
@login_required
def api_followups_update(fid):
    """更新跟进（修改反馈状态等）"""
    f = db.session.get(FollowUp, fid)
    if not f or f.user_id != current_user.id:
        return jsonify({'error': '无权操作'}), 403
    data = request.get_json(silent=True) or {}
    if 'note' in data:
        f.note = data['note']
    if 'feedback' in data:
        f.feedback = data['feedback']
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/followups/<int:fid>', methods=['DELETE'])
@login_required
def api_followups_delete(fid):
    f = db.session.get(FollowUp, fid)
    if not f or f.user_id != current_user.id:
        return jsonify({'error': '无权操作'}), 403
    db.session.delete(f)
    db.session.commit()
    return jsonify({'ok': True})


# ═══════════════════════════════════════════════════════════════
# 收藏 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/collections', methods=['GET'])
@login_required
def api_collections_list():
    """获取收藏列表"""
    target_type = request.args.get('type', '')
    query = Collection.query.filter_by(user_id=current_user.id)
    if target_type:
        query = query.filter_by(target_type=target_type)
    items = query.order_by(Collection.created_at.desc()).limit(50).all()
    return jsonify({'collections': [{
        'id': c.id, 'targetType': c.target_type, 'targetId': c.target_id,
        'createdAt': c.created_at.isoformat() if c.created_at else None,
    } for c in items]})

@app.route('/api/collections', methods=['POST'])
@login_required
def api_collections_create():
    """添加收藏"""
    data = request.get_json(silent=True) or {}
    target_type = data.get('targetType', '')
    target_id = data.get('targetId')
    if not target_type or not target_id:
        return jsonify({'error': '缺少参数'}), 400
    # 检查是否已收藏
    exists = Collection.query.filter_by(
        user_id=current_user.id, target_type=target_type, target_id=target_id
    ).first()
    if exists:
        return jsonify({'error': '已收藏'}), 409
    c = Collection(
        user_id=current_user.id, target_type=target_type, target_id=target_id,
    )
    db.session.add(c)
    db.session.commit()
    return jsonify({'id': c.id}), 201

@app.route('/api/collections/<int:cid>', methods=['DELETE'])
@login_required
def api_collections_delete(cid):
    c = db.session.get(Collection, cid)
    if not c or c.user_id != current_user.id:
        return jsonify({'error': '无权操作'}), 403
    db.session.delete(c)
    db.session.commit()
    return jsonify({'ok': True})


# ═══════════════════════════════════════════════════════════════
# 运势日历 API（基于 LunarCalendar）
# ═══════════════════════════════════════════════════════════════

@app.route('/api/huangli')
def api_huangli():
    """黄历万年历 — 返回指定日期的农历、干支、五行、建除、冲煞等"""
    date_str = request.args.get('date', '')  # YYYY-MM-DD
    if not date_str:
        date_str = datetime.now().strftime('%Y-%m-%d')
    try:
        parts = date_str.split('-')
        year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
    except (ValueError, IndexError):
        return jsonify({'error': '日期格式错误，需YYYY-MM-DD'}), 400

    result = _compute_huangli(year, month, day)
    return jsonify(result)


@app.route('/api/huangli/month')
def api_huangli_month():
    """黄历万年历 — 返回整月日历数据（并发获取API数据，带整月缓存）"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    if not year or not month:
        now = datetime.now()
        year, month = now.year, now.month

    month_key = f'{year}-{month:02d}'
    now_ts = time.time()
    cached = _huangli_month_cache.get(month_key)
    if cached and cached[1] > now_ts:
        return jsonify(cached[0])

    import calendar
    _, days_in_month = calendar.monthrange(year, month)

    # 并发获取各日数据
    from concurrent.futures import ThreadPoolExecutor, as_completed
    days_dict = {}
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(_compute_huangli, year, month, d): d for d in range(1, days_in_month + 1)}
        for future in as_completed(futures):
            d = futures[future]
            try:
                days_dict[d] = future.result(timeout=10)
            except Exception:
                days_dict[d] = {'solarDate': f'{year}-{month:02d}-{d:02d}', 'source': 'error'}

    days = [days_dict[d] for d in range(1, days_in_month + 1)]
    result = {'year': year, 'month': month, 'days': days, 'disclaimer': '以上内容仅为民俗文化参考，不构成任何决策建议'}
    _huangli_month_cache[month_key] = (result, now_ts + _HUANGLI_MONTH_TTL)
    return jsonify(result)


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


@app.route('/api/zeji', methods=['POST'])
@csrf.exempt
def api_zeji():
    """择吉工具 — 基于本地黄历字段给出日期候选，不依赖登录。"""
    data = request.get_json(silent=True) or {}
    zeji_type = (data.get('zejiType') or data.get('type') or '').strip() or '择吉'
    start_date = (data.get('startDate') or '').strip()
    end_date = (data.get('endDate') or start_date).strip()
    addr = (data.get('addr') or '').strip()

    if not start_date:
        return jsonify({'success': False, 'error': '请选择开始日期'}), 400

    try:
        start_dt = _parse_zeji_date(start_date, '开始日期')
        end_dt = _parse_zeji_date(end_date, '结束日期')
    except ValueError as e:
        return jsonify({'success': False, 'error': str(e)}), 400

    if end_dt < start_dt:
        return jsonify({'success': False, 'error': '结束日期不能早于开始日期'}), 400

    if (end_dt - start_dt).days > 60:
        return jsonify({'success': False, 'error': '择吉日期范围最多支持60天'}), 400

    candidates = []
    cursor = start_dt
    while cursor <= end_dt:
        h = _compute_huangli_local(cursor.year, cursor.month, cursor.day)
        score, reasons, warnings = _score_zeji_day(zeji_type, h)
        candidates.append({
            'date': cursor.strftime('%Y-%m-%d'),
            'score': score,
            'lunar': h.get('lunarDate', ''),
            'ganZhiDay': h.get('ganZhiDay', ''),
            'jianChu': h.get('jianChu', ''),
            'zhiShen': h.get('zhiShen', ''),
            'chong': h.get('chong', ''),
            'sha': h.get('sha', ''),
            'reasons': reasons,
            'warnings': warnings,
        })
        cursor += timedelta(days=1)

    candidates.sort(key=lambda item: (-item['score'], item['date']))
    best = candidates[:3]
    lines = [
        '═══ 择吉分析 ═══',
        f'事项：{zeji_type}',
        f'日期范围：{start_date} ~ {end_date}',
    ]
    if addr:
        lines.append(f'地点：{addr}')
    lines.append('')
    lines.append('推荐日期：')
    for idx, item in enumerate(best, 1):
        reason_text = '；'.join(item['reasons'] or ['综合黄历信息较平稳'])
        warning_text = '；'.join(item['warnings'])
        line = (
            f'{idx}. {item["date"]}（评分{item["score"]}）'
            f' {item["ganZhiDay"]}日 · {item["jianChu"]}日 · 值神{item["zhiShen"]}'
            f' · {item["chong"]}{item["sha"]}。{reason_text}'
        )
        if warning_text:
            line += f'；提醒：{warning_text}'
        lines.append(line)
    lines.extend([
        '',
        '建议：优先选择评分靠前且时间安排从容的日期，具体吉时需结合当事人八字、方位和实际行程进一步细排。',
        '⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。',
    ])

    return jsonify({
        'success': True,
        'zejiType': zeji_type,
        'startDate': start_date,
        'endDate': end_date,
        'addr': addr,
        'bestDays': best,
        'days': candidates,
        'result': '\n'.join(lines),
        'message': '\n'.join(lines),
    })


# ═══════════════════════════════════════════════════════════════
# 搜索 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/search')
@login_required
def api_search():
    """搜索用户的排盘记录"""
    q = (request.args.get('q') or '').strip()
    app_type = request.args.get('type', '')
    if not q:
        return jsonify({'results': [], 'total': 0})

    query = Record.query.filter_by(user_id=current_user.id)
    if app_type:
        query = query.filter_by(app_type=app_type)
    query = query.filter(Record.question.contains(q))
    records = query.order_by(Record.created_at.desc()).limit(20).all()

    return jsonify({
        'results': [{
            'id': r.id, 'appType': r.app_type or 'qimen',
            'question': r.question, 'hasResult': bool(r.result_html),
            'createdAt': r.created_at.isoformat() if r.created_at else None,
        } for r in records],
        'total': len(records),
    })


# ═══════════════════════════════════════════════════════════════
# 图片上传 API
# ═══════════════════════════════════════════════════════════════

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/upload', methods=['POST'])
@login_required
def api_upload():
    """图片上传 — 支持 jpg/png/gif/webp，最大 5MB"""
    if 'file' not in request.files:
        return jsonify({'error': '未选择文件'}), 400
    f = request.files['file']
    if not f.filename:
        return jsonify({'error': '未选择文件'}), 400
    if not allowed_file(f.filename):
        return jsonify({'error': '不支持的文件格式，仅支持 jpg/png/gif/webp'}), 400

    # 生成唯一文件名
    ext = f.filename.rsplit('.', 1)[1].lower()
    fname = f"{int(time.time())}_{secrets.token_hex(6)}.{ext}"
    upload_dir = app.config['UPLOAD_FOLDER']
    os.makedirs(upload_dir, exist_ok=True)
    fpath = os.path.join(upload_dir, fname)
    f.save(fpath)

    url = f"/static/uploads/{fname}"
    return jsonify({'url': url, 'filename': fname}), 201


@app.route('/api/avatar', methods=['POST'])
@login_required
@csrf.exempt
def api_avatar():
    """用户头像上传 — 图片会被裁剪为圆形显示"""
    logger.info(f"[avatar] upload request from user={current_user.id}, files={list(request.files.keys())}, content_type={request.content_type}")
    if 'file' not in request.files:
        logger.warning(f"[avatar] no 'file' in request.files, keys={list(request.files.keys())}")
        return jsonify({'error': '未选择文件'}), 400
    f = request.files['file']
    if not f.filename:
        logger.warning("[avatar] empty filename")
        return jsonify({'error': '未选择文件'}), 400
    if not allowed_file(f.filename):
        logger.warning(f"[avatar] not allowed file: {f.filename}")
        return jsonify({'error': '不支持的文件格式，仅支持 jpg/png/gif/webp'}), 400

    # 用 Pillow 裁剪为正方形（居中裁剪）
    try:
        from PIL import Image
        img = Image.open(f.stream)
        # 转为 RGB（处理 RGBA/P 模式）
        if img.mode not in ('RGB', 'RGBA'):
            img = img.convert('RGBA')
        w, h = img.size
        side = min(w, h)
        left = (w - side) // 2
        top = (h - side) // 2
        img = img.crop((left, top, left + side, top + side))
        # 缩放到合适大小（200x200 足够用于头像）
        img = img.resize((200, 200), Image.LANCZOS)
        # 保存为 PNG
        ext = 'png'
        fname = f"avatar_{current_user.id}_{int(time.time())}.{ext}"
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        fpath = os.path.join(upload_dir, fname)
        # 如果有透明通道，保留；否则转 RGB
        if img.mode == 'RGBA':
            img.save(fpath, 'PNG')
        else:
            img = img.convert('RGB')
            img.save(fpath, 'PNG')
        url = f"/static/uploads/{fname}"
        # 更新用户头像
        # 删除旧头像文件
        if current_user.avatar:
            old_path = os.path.join(upload_dir, current_user.avatar.split('/')[-1])
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
        current_user.avatar = url
        db.session.commit()
        return jsonify({'url': url}), 200
    except ImportError:
        # Pillow 未安装，直接保存原图
        ext = f.filename.rsplit('.', 1)[1].lower()
        fname = f"avatar_{current_user.id}_{int(time.time())}.{ext}"
        upload_dir = app.config['UPLOAD_FOLDER']
        os.makedirs(upload_dir, exist_ok=True)
        fpath = os.path.join(upload_dir, fname)
        f.save(fpath)
        url = f"/static/uploads/{fname}"
        if current_user.avatar:
            old_path = os.path.join(upload_dir, current_user.avatar.split('/')[-1])
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except OSError:
                    pass
        current_user.avatar = url
        db.session.commit()
        return jsonify({'url': url}), 200
    except Exception as e:
        logger.error(f"[avatar] 上传失败: {e}")
        return jsonify({'error': '头像上传失败，请重试'}), 500


# ═══════════════════════════════════════════════════════════════
# 社区帖子 API
# ═══════════════════════════════════════════════════════════════

VALID_CATEGORIES = {'share', 'discuss', 'ask', 'experience'}
REPORT_REASONS = {'spam', 'abuse', 'misinformation', 'illegal', 'other'}


def _create_notification(user_id, ntype, from_user_id=None, post_id=None, comment_id=None, content=None):
    from models import Notification
    n = Notification(user_id=user_id, type=ntype, from_user_id=from_user_id,
                     post_id=post_id, comment_id=comment_id, content=content)
    db.session.add(n)


@app.route('/api/posts', methods=['GET'])
def api_posts_list():
    """社区帖子列表 — 支持 category/tags/page/sort 参数"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    category = request.args.get('category', '')
    tag = request.args.get('tag', '').strip()
    sort = request.args.get('sort', 'latest').strip()

    query = Post.query.filter_by(is_hidden=False)
    if category and category in VALID_CATEGORIES:
        query = query.filter_by(category=category)
    if tag:
        query = query.filter(Post.tags.contains(tag))

    if sort == 'hot':
        query = query.order_by(Post.is_pinned.desc(), Post.likes_count.desc(), Post.comments_count.desc(), Post.created_at.desc())
    elif sort == 'featured':
        query = query.filter_by(is_featured=True).order_by(Post.is_pinned.desc(), Post.created_at.desc())
    else:
        query = query.order_by(Post.is_pinned.desc(), Post.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    posts = []
    for p in pagination.items:
        author = db.session.get(User, p.user_id)
        posts.append({
            'id': p.id,
            'userId': p.user_id,
            'username': author.username if author else '匿名',
            'title': p.title,
            'contentPreview': (p.content[:80] + '...') if p.content and len(p.content) > 80 else (p.content or ''),
            'category': p.category,
            'tags': p.tags.split(',') if p.tags else [],
            'imageUrl': p.image_url or None,
            'likesCount': p.likes_count,
            'commentsCount': p.comments_count,
            'isFeatured': p.is_featured,
            'isPinned': p.is_pinned,
            'createdAt': p.created_at.isoformat() if p.created_at else None,
        })

    return jsonify({
        'posts': posts,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'disclaimer': '本社区内容为民俗文化探讨，不构成命运预测承诺',
    })

@app.route('/api/posts', methods=['POST'])
@login_required
def api_posts_create():
    """创建帖子 — 支持 JSON 和 multipart/form-data（含图片上传）"""
    image_url = None

    # 判断是否为 multipart/form-data（含图片）
    if request.content_type and 'multipart/form-data' in request.content_type:
        title = (request.form.get('title') or '').strip()
        content = (request.form.get('content') or '').strip()
        category = request.form.get('category', 'share')
        tags = request.form.get('tags', '')

        # 处理图片上传
        if 'image' in request.files:
            f = request.files['image']
            if f and f.filename and allowed_file(f.filename):
                ext = f.filename.rsplit('.', 1)[1].lower()
                fname = f"{int(time.time())}_{secrets.token_hex(6)}.{ext}"
                upload_dir = app.config['UPLOAD_FOLDER']
                os.makedirs(upload_dir, exist_ok=True)
                fpath = os.path.join(upload_dir, fname)
                f.save(fpath)
                image_url = f"/static/uploads/{fname}"
    else:
        data = request.get_json(silent=True) or {}
        title = (data.get('title') or '').strip()
        content = (data.get('content') or '').strip()
        category = data.get('category', 'share')
        tags = data.get('tags', '')
        image_url = data.get('imageUrl')  # 前端先上传再传URL

    if not title or len(title) > 200:
        return jsonify({'error': '标题需1-200个字符'}), 400
    if not content:
        return jsonify({'error': '内容不能为空'}), 400
    if category not in VALID_CATEGORIES:
        return jsonify({'error': f'无效分类，可选: {", ".join(VALID_CATEGORIES)}'}), 400

    # 处理标签：逗号分隔，去空去重
    if isinstance(tags, list):
        tag_str = ','.join(t.strip() for t in tags if t.strip())
    else:
        tag_str = ','.join(t.strip() for t in str(tags).split(',') if t.strip())

    post = Post(
        user_id=current_user.id, title=title, content=content,
        category=category, tags=tag_str, image_url=image_url,
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({'id': post.id, 'disclaimer': '本帖内容为民俗文化探讨，不构成命运预测承诺'}), 201

@app.route('/api/posts/<int:pid>')
def api_posts_detail(pid):
    """帖子详情（含评论）"""
    post = db.session.get(Post, pid)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    if post.is_hidden and not (current_user.is_authenticated and current_user.is_admin):
        return jsonify({'error': '帖子已被隐藏'}), 404

    author = db.session.get(User, post.user_id)
    # 查询评论（不含回复，回复通过 parent_id 关联）
    comments = Comment.query.filter_by(post_id=pid, parent_id=None)\
        .order_by(Comment.created_at.asc()).all()

    def format_comment(c):
        author_c = db.session.get(User, c.user_id)
        replies = Comment.query.filter_by(parent_id=c.id)\
            .order_by(Comment.created_at.asc()).all()
        c_liked = False
        if current_user.is_authenticated:
            c_liked = CommentLike.query.filter_by(user_id=current_user.id, comment_id=c.id).first() is not None
        return {
            'id': c.id,
            'userId': c.user_id,
            'username': author_c.username if author_c else '匿名',
            'content': c.content,
            'parentId': c.parent_id,
            'likesCount': c.likes_count,
            'liked': c_liked,
            'replies': [format_comment(r) for r in replies],
            'createdAt': c.created_at.isoformat() if c.created_at else None,
        }

    # 检查当前用户是否已点赞
    liked = False
    if current_user.is_authenticated:
        liked = PostLike.query.filter_by(user_id=current_user.id, post_id=pid).first() is not None

    return jsonify({
        'id': post.id,
        'userId': post.user_id,
        'username': author.username if author else '匿名',
        'title': post.title,
        'content': post.content,
        'category': post.category,
        'tags': post.tags.split(',') if post.tags else [],
        'imageUrl': post.image_url or None,
        'likesCount': post.likes_count,
        'commentsCount': post.comments_count,
        'isFeatured': post.is_featured,
        'isPinned': post.is_pinned,
        'isHidden': post.is_hidden,
        'liked': liked,
        'comments': [format_comment(c) for c in comments],
        'createdAt': post.created_at.isoformat() if post.created_at else None,
        'disclaimer': '本帖内容为民俗文化探讨，不构成命运预测承诺',
    })

@app.route('/api/posts/<int:pid>', methods=['DELETE'])
@login_required
def api_posts_delete(pid):
    """删除帖子（仅作者）"""
    post = db.session.get(Post, pid)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    if post.user_id != current_user.id:
        return jsonify({'error': '仅作者可删除'}), 403

    # 级联删除评论和点赞
    Comment.query.filter_by(post_id=pid).delete()
    PostLike.query.filter_by(post_id=pid).delete()
    db.session.delete(post)
    db.session.commit()
    return jsonify({'ok': True})

@app.route('/api/posts/<int:pid>/like', methods=['POST'])
@login_required
def api_posts_like(pid):
    """点赞/取消点赞"""
    post = db.session.get(Post, pid)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    existing = PostLike.query.filter_by(user_id=current_user.id, post_id=pid).first()
    if existing:
        db.session.delete(existing)
        post.likes_count = max(0, (post.likes_count or 0) - 1)
        db.session.commit()
        return jsonify({'liked': False, 'likesCount': post.likes_count})
    else:
        like = PostLike(user_id=current_user.id, post_id=pid)
        db.session.add(like)
        post.likes_count = (post.likes_count or 0) + 1
        if post.user_id != current_user.id:
            _create_notification(post.user_id, 'like', from_user_id=current_user.id,
                                 post_id=pid, content=f'{current_user.username} 赞了你的帖子')
        db.session.commit()
        return jsonify({'liked': True, 'likesCount': post.likes_count})

@app.route('/api/posts/<int:pid>/comments', methods=['POST'])
@login_required
def api_posts_comment(pid):
    """添加评论"""
    post = db.session.get(Post, pid)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    parent_id = data.get('parentId')

    if not content:
        return jsonify({'error': '评论内容不能为空'}), 400

    # 校验 parent_id：必须属于同一帖子
    if parent_id:
        parent = db.session.get(Comment, parent_id)
        if not parent or parent.post_id != pid:
            return jsonify({'error': '回复的评论不存在'}), 400

    comment = Comment(
        user_id=current_user.id, post_id=pid,
        content=content, parent_id=parent_id,
    )
    db.session.add(comment)
    post.comments_count = (post.comments_count or 0) + 1
    if post.user_id != current_user.id:
        _create_notification(post.user_id, 'comment', from_user_id=current_user.id,
                             post_id=pid, comment_id=comment.id,
                             content=f'{current_user.username} 评论了你的帖子')
    if parent_id:
        parent_c = db.session.get(Comment, parent_id)
        if parent_c and parent_c.user_id != current_user.id:
            _create_notification(parent_c.user_id, 'reply', from_user_id=current_user.id,
                                 post_id=pid, comment_id=comment.id,
                                 content=f'{current_user.username} 回复了你的评论')
    db.session.commit()
    return jsonify({'id': comment.id, 'disclaimer': '本评论内容为民俗文化探讨，不构成命运预测承诺'}), 201

@app.route('/api/comments/<int:cid>', methods=['DELETE'])
@login_required
def api_comments_delete(cid):
    """删除评论（仅作者）"""
    comment = db.session.get(Comment, cid)
    if not comment:
        return jsonify({'error': '评论不存在'}), 404
    if comment.user_id != current_user.id:
        return jsonify({'error': '仅作者可删除'}), 403

    post = db.session.get(Post, comment.post_id)
    if post:
        post.comments_count = max(0, (post.comments_count or 0) - 1)
    Comment.query.filter_by(parent_id=cid).delete()
    CommentLike.query.filter_by(comment_id=cid).delete()
    db.session.delete(comment)
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/posts/<int:pid>', methods=['PUT'])
@login_required
def api_posts_update(pid):
    """编辑帖子（仅作者）"""
    post = db.session.get(Post, pid)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404
    if post.user_id != current_user.id:
        return jsonify({'error': '仅作者可编辑'}), 403

    data = request.get_json(silent=True) or {}
    title = (data.get('title') or '').strip()
    content = (data.get('content') or '').strip()
    category = data.get('category', post.category)
    tags = data.get('tags', None)

    if title:
        if len(title) > 200:
            return jsonify({'error': '标题需1-200个字符'}), 400
        post.title = title
    if content:
        post.content = content
    if category and category in VALID_CATEGORIES:
        post.category = category
    if tags is not None:
        if isinstance(tags, list):
            tag_str = ','.join(t.strip() for t in tags if t.strip())
        else:
            tag_str = ','.join(t.strip() for t in str(tags).split(',') if t.strip())
        post.tags = tag_str

    db.session.commit()
    return jsonify({'ok': True, 'id': post.id})


@app.route('/api/users/<int:uid>/posts')
def api_user_posts(uid):
    """获取用户的帖子列表"""
    user = db.session.get(User, uid)
    if not user:
        return jsonify({'error': '用户不存在'}), 404

    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    pagination = Post.query.filter_by(user_id=uid)\
        .order_by(Post.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    posts = []
    for p in pagination.items:
        posts.append({
            'id': p.id,
            'userId': p.user_id,
            'username': user.username,
            'title': p.title,
            'contentPreview': (p.content[:80] + '...') if p.content and len(p.content) > 80 else (p.content or ''),
            'category': p.category,
            'tags': p.tags.split(',') if p.tags else [],
            'imageUrl': p.image_url or None,
            'likesCount': p.likes_count,
            'commentsCount': p.comments_count,
            'isFeatured': p.is_featured,
            'createdAt': p.created_at.isoformat() if p.created_at else None,
        })

    return jsonify({
        'user': {'id': user.id, 'username': user.username},
        'posts': posts,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
    })


@app.route('/api/comments/<int:cid>/like', methods=['POST'])
@login_required
def api_comments_like(cid):
    """评论点赞/取消点赞"""
    comment = db.session.get(Comment, cid)
    if not comment:
        return jsonify({'error': '评论不存在'}), 404

    existing = CommentLike.query.filter_by(user_id=current_user.id, comment_id=cid).first()
    if existing:
        db.session.delete(existing)
        comment.likes_count = max(0, (comment.likes_count or 0) - 1)
        db.session.commit()
        return jsonify({'liked': False, 'likesCount': comment.likes_count})
    else:
        like = CommentLike(user_id=current_user.id, comment_id=cid)
        db.session.add(like)
        comment.likes_count = (comment.likes_count or 0) + 1
        db.session.commit()
        return jsonify({'liked': True, 'likesCount': comment.likes_count})


# ═══════════════════════════════════════════════════════════════
# 通知 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/notifications')
@login_required
def api_notifications_list():
    """获取当前用户的通知列表"""
    from models import Notification
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 30, type=int), 50)
    pagination = Notification.query.filter_by(user_id=current_user.id)\
        .order_by(Notification.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for n in pagination.items:
        from_user = db.session.get(User, n.from_user_id) if n.from_user_id else None
        items.append({
            'id': n.id,
            'type': n.type,
            'fromUserId': n.from_user_id,
            'fromUsername': from_user.username if from_user else None,
            'postId': n.post_id,
            'commentId': n.comment_id,
            'content': n.content,
            'isRead': n.is_read,
            'createdAt': n.created_at.isoformat() if n.created_at else None,
        })

    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return jsonify({
        'notifications': items,
        'unreadCount': unread_count,
        'total': pagination.total,
        'page': page,
        'has_next': pagination.has_next,
    })


@app.route('/api/notifications/read', methods=['POST'])
@login_required
def api_notifications_read():
    """标记所有通知为已读"""
    from models import Notification
    Notification.query.filter_by(user_id=current_user.id, is_read=False)\
        .update({'is_read': True})
    db.session.commit()
    return jsonify({'ok': True})


@app.route('/api/notifications/<int:nid>/read', methods=['POST'])
@login_required
def api_notification_read_one(nid):
    """标记单条通知为已读"""
    from models import Notification
    n = db.session.get(Notification, nid)
    if not n or n.user_id != current_user.id:
        return jsonify({'error': '通知不存在'}), 404
    n.is_read = True
    db.session.commit()
    return jsonify({'ok': True})


# ═══════════════════════════════════════════════════════════════
# 举报 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/reports', methods=['POST'])
@login_required
def api_reports_create():
    """创建举报"""
    from models import Report
    data = request.get_json(silent=True) or {}
    target_type = (data.get('targetType') or '').strip()
    target_id = data.get('targetId')
    reason = (data.get('reason') or '').strip()

    if target_type not in ('post', 'comment'):
        return jsonify({'error': '无效的举报目标类型'}), 400
    if not target_id:
        return jsonify({'error': '缺少目标ID'}), 400
    if reason not in REPORT_REASONS:
        return jsonify({'error': '无效的举报原因'}), 400

    existing = Report.query.filter_by(user_id=current_user.id, target_type=target_type,
                                       target_id=target_id, status='pending').first()
    if existing:
        return jsonify({'error': '你已经举报过该内容，请等待审核'}), 400

    report = Report(user_id=current_user.id, target_type=target_type,
                    target_id=target_id, reason=reason)
    db.session.add(report)
    db.session.commit()
    return jsonify({'ok': True, 'id': report.id}), 201


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
# 分享 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/posts/<int:pid>/share', methods=['POST'])
@login_required
def api_posts_share(pid):
    """记录分享行为"""
    post = db.session.get(Post, pid)
    if not post:
        return jsonify({'error': '帖子不存在'}), 404

    share_url = f"{request.host_url}community?post={pid}"
    return jsonify({
        'ok': True,
        'shareUrl': share_url,
        'title': post.title,
        'description': (post.content[:100] + '...') if post.content and len(post.content) > 100 else (post.content or ''),
    })


# ═══════════════════════════════════════════════════════════════
# 大师体系 API
# ═══════════════════════════════════════════════════════════════

@app.route('/api/masters', methods=['GET'])
def api_masters_list():
    """大师列表 — 支持 specialty 参数过滤"""
    specialty = request.args.get('specialty', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)

    query = Master.query
    if specialty:
        query = query.filter(Master.specialties.contains(specialty))

    pagination = query.order_by(Master.rating.desc(), Master.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    masters = []
    for m in pagination.items:
        user = db.session.get(User, m.user_id)
        masters.append({
            'id': m.id,
            'userId': m.user_id,
            'username': user.username if user else '匿名',
            'displayName': m.display_name,
            'avatar': m.avatar,
            'title': m.title,
            'specialties': m.specialties.split(',') if m.specialties else [],
            'verified': m.verified,
            'rating': m.rating,
            'reviewCount': m.review_count,
            'createdAt': m.created_at.isoformat() if m.created_at else None,
        })

    return jsonify({
        'masters': masters,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'disclaimer': '大师信息仅供民俗文化交流参考，不构成命运预测承诺',
    })

@app.route('/api/masters/apply', methods=['POST'])
@login_required
def api_masters_apply():
    """申请成为大师"""
    # 检查是否已申请
    existing = Master.query.filter_by(user_id=current_user.id).first()
    if existing:
        return jsonify({'error': '您已提交申请或已是大师'}), 409

    data = request.get_json(silent=True) or {}
    display_name = (data.get('displayName') or '').strip()
    title = (data.get('title') or '').strip()
    specialties = data.get('specialties', '')
    bio = (data.get('bio') or '').strip()

    if not display_name or len(display_name) > 50:
        return jsonify({'error': '展示名需1-50个字符'}), 400
    if not title:
        return jsonify({'error': '请填写头衔'}), 400

    # 处理专长领域
    if isinstance(specialties, list):
        spec_str = ','.join(s.strip() for s in specialties if s.strip())
    else:
        spec_str = ','.join(s.strip() for s in str(specialties).split(',') if s.strip())

    master = Master(
        user_id=current_user.id, display_name=display_name,
        title=title, specialties=spec_str, bio=bio,
        verified=False,
    )
    db.session.add(master)
    db.session.commit()
    return jsonify({'id': master.id, 'verified': False, 'disclaimer': '大师认证仅供民俗文化交流参考，不构成命运预测承诺'}), 201

@app.route('/api/masters/<int:mid>')
def api_masters_detail(mid):
    """大师详情"""
    master = db.session.get(Master, mid)
    if not master:
        return jsonify({'error': '大师不存在'}), 404

    user = db.session.get(User, master.user_id)
    return jsonify({
        'id': master.id,
        'userId': master.user_id,
        'username': user.username if user else '匿名',
        'displayName': master.display_name,
        'avatar': master.avatar,
        'title': master.title,
        'specialties': master.specialties.split(',') if master.specialties else [],
        'bio': master.bio,
        'verified': master.verified,
        'rating': master.rating,
        'reviewCount': master.review_count,
        'createdAt': master.created_at.isoformat() if master.created_at else None,
        'disclaimer': '大师信息仅供民俗文化交流参考，不构成命运预测承诺',
    })


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

def confirm_recharge_order_once(order_id, extra_update=None):
    """只确认 pending 订单一次，并在同一事务内完成到账。"""
    now = datetime.utcnow()
    try:
        update_data = {'status': 'paid', 'updated_at': now}
        if extra_update:
            update_data.update(extra_update)
        changed = RechargeOrder.query.filter_by(id=order_id, status='pending').update(
            update_data,
            synchronize_session=False,
        )
        if changed != 1:
            db.session.rollback()
            order = db.session.get(RechargeOrder, order_id)
            if not order:
                return {'ok': False, 'error': '订单不存在', 'status': None}
            return {'ok': False, 'error': '订单状态错误', 'status': order.status}

        order = db.session.get(RechargeOrder, order_id)
        pkg = next((p for p in RECHARGE_PACKAGES if p['id'] == order.package_id), None)
        if pkg and pkg.get('package_type') == 'ai':
            membership = get_or_create_membership(order.user_id)
            single = int(pkg.get('ai_single_credits') or 0)
            combo = int(pkg.get('ai_combo_credits') or 0)
            membership.ai_single_credits = int(membership.ai_single_credits or 0) + single
            membership.ai_combo_credits = int(membership.ai_combo_credits or 0) + combo
            db.session.add(PointLog(
                user_id=order.user_id,
                action='ai_credit_recharge',
                points=0,
                description=f"{order.package_name}到账: 单术数+{single}次 合参+{combo}次 (¥{order.amount})",
                dedupe_key=f'recharge_order:{order.id}',
            ))
            new_total = membership.points
            added = single or combo
            credit_type = 'ai_single_credits' if single else 'ai_combo_credits'
        else:
            new_total = add_points(
                order.user_id,
                'recharge',
                order.points,
                f'充值到账: +{order.points}分 (¥{order.amount})',
                dedupe_key=f'recharge_order:{order.id}',
                commit=False,
            )
            added = order.points
            credit_type = 'points'
        db.session.commit()
        return {
            'ok': True,
            'order_id': order.id,
            'user_id': order.user_id,
            'points': new_total,
            'added': added,
            'credit_type': credit_type,
        }
    except IntegrityError:
        db.session.rollback()
        order = db.session.get(RechargeOrder, order_id)
        return {'ok': False, 'error': '订单状态错误', 'status': order.status if order else None}

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

@app.route('/api/membership')
@login_required
def api_membership():
    """获取当前用户会员信息"""
    m = get_or_create_membership(current_user.id)
    # 检查会员是否过期
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
    """每日签到（+10积分，每天1次）"""
    result = create_daily_sign_in_once(current_user.id)
    if not result.get('ok'):
        return jsonify({'error': result.get('error', '今天已签到')}), 400
    return jsonify(result)

@app.route('/api/points/log')
@login_required
def api_points_log():
    """积分日志列表"""
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
    """消费积分"""
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


# ═══════════════════════════════════════════════════════════════
# 充值 API（Phase 1：套餐展示 + 创建订单 + 管理员确认）
# ═══════════════════════════════════════════════════════════════

RECHARGE_PACKAGES = [
    {'id': 'test-cent', 'name': '测试包',  'points': 1,    'price': 0.01, 'package_type': 'points'},
    {'id': 'starter',  'name': '体验包',  'points': 60,   'price': 9.9, 'package_type': 'points'},
    {'id': 'standard', 'name': '标准包',  'points': 240,  'price': 29.9, 'package_type': 'points'},
    {'id': 'premium',  'name': '畅享包',  'points': 650,  'price': 68, 'package_type': 'points'},
    {'id': 'vip',      'name': '尊享包',  'points': 2200, 'price': 198, 'package_type': 'points'},
    {'id': 'ai-starter', 'name': '入门 AI 包', 'points': 0, 'price': 9.9, 'package_type': 'ai', 'ai_single_credits': 10, 'ai_combo_credits': 0, 'description': '10 次单术数 AI'},
    {'id': 'ai-standard', 'name': '标准 AI 包', 'points': 0, 'price': 19.9, 'package_type': 'ai', 'ai_single_credits': 25, 'ai_combo_credits': 0, 'description': '25 次单术数 AI'},
    {'id': 'ai-combo', 'name': '深度合参包', 'points': 0, 'price': 68, 'package_type': 'ai', 'ai_single_credits': 0, 'ai_combo_credits': 20, 'description': '20 次多术数合参'},
]

@app.route('/api/recharge/packages', methods=['GET'])
def api_recharge_packages():
    """获取充值套餐列表"""
    return jsonify({'packages': RECHARGE_PACKAGES})


@app.route('/api/recharge/create-order', methods=['POST'])
@login_required
def api_recharge_create_order():
    """创建充值订单"""
    data = request.get_json(silent=True) or {}
    pkg_id = (data.get('package_id') or '').strip()
    pay_method = (data.get('pay_method') or '').strip()

    pkg = None
    for p in RECHARGE_PACKAGES:
        if p['id'] == pkg_id:
            pkg = p
            break
    if not pkg:
        return jsonify({'error': '无效的套餐'}), 400

    order = RechargeOrder(
        user_id=current_user.id,
        package_id=pkg['id'],
        package_name=pkg['name'],
        points=pkg['points'],
        amount=pkg['price'],
        pay_method=pay_method,
        status='pending',
    )
    db.session.add(order)
    db.session.commit()
    return jsonify({
        'ok': True,
        'order_id': order.id,
        'points_amount': pkg['points'],
        'package_type': pkg.get('package_type', 'points'),
        'ai_single_credits': pkg.get('ai_single_credits', 0),
        'ai_combo_credits': pkg.get('ai_combo_credits', 0),
        'price': pkg['price'],
        'status': 'pending',
    })


def _parse_payment_amount(value):
    """把前端识别到的付款金额规整为两位小数。"""
    try:
        amount = float(value)
    except (TypeError, ValueError):
        return None
    if amount <= 0:
        return None
    return round(amount, 2)


def _payment_amount_matches(expected, actual):
    """按分比较金额，避免 0.01 浮点容差把差一分钱的付款放过。"""
    if expected is None or actual is None:
        return False
    return int(round(float(expected) * 100)) == int(round(float(actual) * 100))


RECHARGE_SMALL_AUTO_LIMIT = float(os.environ.get('RECHARGE_SMALL_AUTO_LIMIT', '29.9'))
RECHARGE_MANUAL_MESSAGE = '付款截图已提交，大额充值每日 10:00 - 24:00 在线确认，非在线时间可能延迟到账'


def _extract_amounts_from_payment_text(text):
    """从付款截图 OCR 文本中提取强可信金额，避免把时间、红包、积分识别成付款金额。"""
    amounts = []
    seen = set()
    patterns = [
        r'[¥￥]\s*([0-9]+(?:\.[0-9]{1,2})?)',
        r'(?:支付金额|付款金额|实付金额|实际付款|实付|应付|需支付|付款)\s*[：:为是]?\s*[¥￥]?\s*([0-9]+(?:\.[0-9]{1,2})?)',
    ]
    for pattern in patterns:
        for raw in re.findall(pattern, text or ''):
            amount = _parse_payment_amount(raw)
            if amount is None or amount > 10000:
                continue
            key = f'{amount:.2f}'
            if key in seen:
                continue
            seen.add(key)
            amounts.append(amount)
    return amounts


def _payment_text_matches_receiver(text):
    """校验 OCR 文本是否包含本站收款名。"""
    receiver = os.environ.get('ALIPAY_RECEIVER_NAME', '时安解忧屋').strip()
    if not receiver:
        return True
    compact = re.sub(r'\s+', '', text or '')
    return receiver in compact


def _ocr_payment_image(path):
    """尽量用服务器本地 tesseract 识别付款截图；不可用时返回空文本。"""
    if not shutil.which('tesseract'):
        return ''
    texts = []

    def run_tesseract(image_path):
        try:
            with tempfile.NamedTemporaryFile(suffix='.txt', delete=True) as out:
                base = out.name[:-4]
            cmd = ['tesseract', image_path, base, '-l', 'chi_sim+eng', '--psm', '6']
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8, check=False)
            txt_path = base + '.txt'
            if os.path.exists(txt_path):
                with open(txt_path, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read()
                try:
                    os.remove(txt_path)
                except OSError:
                    pass
                return text
        except Exception as e:
            logger.warning(f"付款截图 OCR 失败: {e}")
        return ''

    full_text = run_tesseract(path)
    if full_text:
        texts.append(full_text)

    crop_path = ''
    try:
        from PIL import Image
        with Image.open(path) as img:
            width, height = img.size
            if height > 0 and width > 0:
                upper = img.crop((0, 0, width, max(1, int(height * 0.45))))
                with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as out:
                    crop_path = out.name
                upper.save(crop_path)
        crop_text = run_tesseract(crop_path) if crop_path else ''
        if crop_text:
            texts.append(crop_text)
    except Exception as e:
        logger.warning(f"付款截图上半部分 OCR 失败: {e}")
    finally:
        if crop_path:
            try:
                os.remove(crop_path)
            except OSError:
                pass

    return '\n'.join(t for t in texts if t)


def _save_recharge_proof_file(file_storage):
    """保存付款截图并返回 URL、哈希和 OCR 文本。"""
    if not file_storage or not file_storage.filename:
        return None, '', ''
    if not allowed_file(file_storage.filename):
        raise ValueError('不支持的文件格式，仅支持 jpg/png/gif/webp')
    ext = file_storage.filename.rsplit('.', 1)[1].lower()
    raw = file_storage.read()
    if not raw:
        raise ValueError('付款截图为空')
    proof_hash = hashlib.sha256(raw).hexdigest()
    upload_dir = os.path.join(app.config['UPLOAD_FOLDER'], 'recharge')
    os.makedirs(upload_dir, exist_ok=True)
    fname = f"{int(time.time())}_{secrets.token_hex(6)}.{ext}"
    fpath = os.path.join(upload_dir, fname)
    with open(fpath, 'wb') as f:
        f.write(raw)
    text = _ocr_payment_image(fpath)
    return f"/static/uploads/recharge/{fname}", proof_hash, text


@app.route('/api/recharge/verify-payment', methods=['POST'])
@login_required
@csrf.exempt
def api_recharge_verify_payment():
    """支付宝二维码付款后自动核验并入账。"""
    data = request.get_json(silent=True) if request.is_json else request.form
    data = data or {}
    order_id = data.get('order_id', 0)
    expected_amount = _parse_payment_amount(data.get('expected_amount') or data.get('paid_amount'))
    payment_reference = (data.get('payment_reference') or '').strip()[:120]
    proof_text = (data.get('payment_proof_text') or '').strip()
    payment_proof = (data.get('payment_proof') or '').strip()[:2000]
    proof_hash = (data.get('payment_proof_hash') or '').strip()[:120]
    proof_url = ''

    try:
        proof_file = request.files.get('file') or request.files.get('payment_proof')
        if proof_file:
            proof_url, image_hash, ocr_text = _save_recharge_proof_file(proof_file)
            proof_hash = proof_hash or image_hash
            if ocr_text:
                proof_text = (proof_text + '\n' + ocr_text).strip()
    except ValueError as e:
        return jsonify({'error': str(e)}), 400

    if not order_id:
        return jsonify({'error': '缺少订单'}), 400
    if len(payment_reference) < 4 and len(payment_proof) < 6 and len(proof_text) < 6 and not proof_hash:
        return jsonify({'error': '请上传付款截图后再识别'}), 400

    order = db.session.get(RechargeOrder, int(order_id))
    if not order or order.user_id != current_user.id:
        return jsonify({'error': '订单不存在'}), 404
    if order.status != 'pending':
        return jsonify({'error': '订单状态错误', 'status': order.status}), 400

    payment_reference = proof_hash or payment_reference
    if payment_reference:
        reused = RechargeOrder.query.filter(
            RechargeOrder.id != order.id,
            RechargeOrder.payment_reference == payment_reference,
        ).first()
        if reused:
            return jsonify({'error': '付款截图已提交过'}), 400

    expected = round(float(order.amount), 2)
    text_amounts = _extract_amounts_from_payment_text(proof_text)
    paid_amount = expected_amount
    if text_amounts:
        matched_amount = next((a for a in text_amounts if _payment_amount_matches(expected, a)), None)
        if matched_amount is None:
            return jsonify({'error': '付款金额与订单金额不一致'}), 400
        paid_amount = matched_amount
    elif paid_amount is None:
        paid_amount = expected

    if not _payment_amount_matches(expected, paid_amount):
        return jsonify({'error': '付款金额与订单金额不一致'}), 400

    proof_detail = {
        'text': proof_text[:1200],
        'url': proof_url,
        'expected_amount': expected,
        'detected_amounts': text_amounts,
    }
    if payment_proof:
        proof_detail['note'] = payment_proof

    proof_update = {
        'pay_method': 'alipay_qr',
        'payment_reference': payment_reference,
        'payment_proof': json.dumps(proof_detail, ensure_ascii=False),
        'verified_at': datetime.utcnow(),
    }

    receiver_ok = _payment_text_matches_receiver(proof_text) if proof_text else False
    small_auto_allowed = expected <= RECHARGE_SMALL_AUTO_LIMIT and receiver_ok and bool(payment_reference)
    force_auto = os.environ.get('ALIPAY_QR_AUTO_CONFIRM') == '1'

    if not force_auto and not small_auto_allowed:
        RechargeOrder.query.filter_by(id=order.id, status='pending').update(
            proof_update,
            synchronize_session=False,
        )
        db.session.commit()
        return jsonify({
            'ok': True,
            'order_id': order.id,
            'status': 'pending',
            'auto_confirmed': False,
            'message': RECHARGE_MANUAL_MESSAGE,
        })

    result = confirm_recharge_order_once(order.id, {
        **proof_update,
    })
    if not result.get('ok'):
        return jsonify({'error': result.get('error', '订单状态错误'), 'status': result.get('status')}), 400
    return jsonify({
        'ok': True,
        'order_id': result.get('order_id'),
        'points': result.get('points'),
        'added': result.get('added'),
        'credit_type': result.get('credit_type'),
        'status': 'paid',
        'auto_confirmed': True,
    })


@app.route('/api/recharge/orders', methods=['GET'])
@login_required
def api_recharge_orders():
    """查询我的充值记录"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    pagination = RechargeOrder.query.filter_by(user_id=current_user.id)\
        .order_by(RechargeOrder.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    orders = [{
        'id': o.id,
        'points_amount': o.points,
        'price': o.amount,
        'status': o.status,
        'pay_method': o.pay_method,
        'payment_reference': o.payment_reference or '',
        'created_at': o.created_at.isoformat() if o.created_at else None,
        'paid_at': o.updated_at.isoformat() if o.status == 'paid' and o.updated_at else None,
    } for o in pagination.items]
    return jsonify({'orders': orders, 'total': pagination.total, 'page': page, 'has_next': pagination.has_next})


from admin_routes import register_admin_routes
from bazi_history_routes import register_bazi_history_routes
from ops_routes import register_ops_routes

register_ops_routes(app)
register_bazi_history_routes(app, db)
register_admin_routes(app, db, {
    'record_admin_audit': record_admin_audit,
    'add_points': add_points,
    'confirm_recharge_order_once': confirm_recharge_order_once,
})

@app.route('/api/paid-contents', methods=['GET'])
def api_paid_contents_list():
    """付费内容列表（返回preview，不返回full_content）"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 50)
    content_type = request.args.get('type', '')
    category = request.args.get('category', '')

    query = PaidContent.query
    if content_type:
        query = query.filter_by(content_type=content_type)
    if category:
        query = query.filter_by(category=category)

    pagination = query.order_by(PaidContent.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)

    items = []
    for c in pagination.items:
        master = db.session.get(Master, c.master_id) if c.master_id else None
        items.append({
            'id': c.id,
            'title': c.title,
            'contentType': c.content_type,
            'preview': c.preview,
            'price': c.price,
            'category': c.category,
            'masterName': master.display_name if master else None,
            'masterId': c.master_id,
            'createdAt': c.created_at.isoformat() if c.created_at else None,
        })

    return jsonify({
        'contents': items,
        'total': pagination.total,
        'page': page,
        'per_page': per_page,
        'has_next': pagination.has_next,
        'disclaimer': '民俗文化内容，仅供学习参考',
    })

@app.route('/api/paid-contents/<int:cid>')
def api_paid_contents_detail(cid):
    """付费内容详情（已购买返回full_content，未购买只返回preview）"""
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
        'disclaimer': '民俗文化内容，仅供学习参考',
    }

    if purchased:
        result['fullContent'] = content.full_content

    return jsonify(result)

@app.route('/api/paid-contents/<int:cid>/purchase', methods=['POST'])
@login_required
def api_paid_contents_purchase(cid):
    """购买付费内容（扣积分）"""
    content = db.session.get(PaidContent, cid)
    if not content:
        return jsonify({'error': '内容不存在'}), 404

    # 检查是否已购买
    existing = Purchase.query.filter_by(user_id=current_user.id, content_id=cid).first()
    if existing:
        return jsonify({'error': '已购买该内容'}), 409

    # 扣除购买者积分
    spend = use_points(current_user.id, 'purchase', content.price, f'购买内容: {content.title}', commit=False)
    if not spend.get('ok'):
        return jsonify(spend), 400

    # 创建购买记录
    purchase = Purchase(user_id=current_user.id, content_id=cid, points_cost=content.price)
    db.session.add(purchase)

    # 作者（大师）获得 70% 积分
    if content.master_id:
        master = db.session.get(Master, content.master_id)
        if master:
            author_points = int(content.price * 0.7)
            add_points(master.user_id, 'purchased', author_points, f'内容被购买: {content.title}', commit=False)

    db.session.commit()

    return jsonify({
        'ok': True,
        'pointsCost': content.price,
        'disclaimer': '民俗文化内容，仅供学习参考',
    })

@app.route('/api/paid-contents', methods=['POST'])
@login_required
def api_paid_contents_create():
    """创建付费内容（仅大师可创建）"""
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
        title=title, content_type=content_type,
        preview=preview, full_content=full_content,
        price=price, master_id=master.id, category=category,
    )
    db.session.add(content)
    db.session.commit()

    return jsonify({
        'id': content.id,
        'disclaimer': '民俗文化内容，仅供学习参考',
    }), 201




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
