import json
import os
import random
import smtplib
import threading
import time
import urllib.parse
import urllib.request
import uuid
from email.header import Header
from email.mime.text import MIMEText

import email.utils
import hashlib
import secrets
from datetime import datetime, timedelta

from flask import has_app_context, jsonify, redirect, request, session
from flask_login import current_user, login_user
from werkzeug.security import generate_password_hash

from extensions import csrf
from extensions import db
from avatar_utils import visible_avatar_url
from models import RateLimitBucket, User, VerificationCode


QQ_APP_ID = os.environ.get('QQ_APP_ID', '')
QQ_APP_KEY = os.environ.get('QQ_APP_KEY', '')
QQ_CALLBACK_URL = os.environ.get('QQ_CALLBACK_URL', 'http://localhost:5199/api/oauth/qq/callback')
WECHAT_APP_ID = os.environ.get('WECHAT_APP_ID', '')
WECHAT_APP_SECRET = os.environ.get('WECHAT_APP_SECRET', '')
WECHAT_CALLBACK_URL = os.environ.get('WECHAT_CALLBACK_URL', 'http://localhost:5199/api/oauth/wechat/callback')
GITEE_CLIENT_ID = os.environ.get('GITEE_CLIENT_ID', '')
GITEE_CLIENT_SECRET = os.environ.get('GITEE_CLIENT_SECRET', '')
GITEE_CALLBACK_URL = os.environ.get('GITEE_CALLBACK_URL', 'http://localhost:5199/api/oauth/gitee/callback')
OAUTH_ORIGIN = os.environ.get('OAUTH_ORIGIN', 'http://localhost:3001')

ALIYUN_SMS_ACCESS_KEY_ID = os.environ.get('ALIYUN_SMS_ACCESS_KEY_ID', '')
ALIYUN_SMS_ACCESS_KEY_SECRET = os.environ.get('ALIYUN_SMS_ACCESS_KEY_SECRET', '')
ALIYUN_SMS_SIGN_NAME = os.environ.get('ALIYUN_SMS_SIGN_NAME', '')
ALIYUN_SMS_TEMPLATE_CODE = os.environ.get('ALIYUN_SMS_TEMPLATE_CODE', '')
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.qq.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASS = os.environ.get('SMTP_PASS', '')
SMTP_FROM_NAME = os.environ.get('SMTP_FROM_NAME', '时安解忧屋')

_verify_code_store = {}
_rate_limit_store = {}
_rate_limit_lock = threading.Lock()


def _check_rate_limit(key, max_count=5, window=60):
    if has_app_context():
        now_dt = datetime.utcnow()
        try:
            bucket = RateLimitBucket.query.filter_by(bucket_key=key).first()
            if not bucket or (now_dt - bucket.window_started_at).total_seconds() > window:
                if not bucket:
                    bucket = RateLimitBucket(bucket_key=key)
                    db.session.add(bucket)
                bucket.count = 1
                bucket.window_started_at = now_dt
                bucket.updated_at = now_dt
                db.session.commit()
                return True
            if bucket.count >= max_count:
                return False
            bucket.count += 1
            bucket.updated_at = now_dt
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()

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
    return str(random.randint(100000, 999999))


def _hash_code(key, code):
    return hashlib.sha256(f'{key}:{code}'.encode('utf-8')).hexdigest()


def _store_code(key, code):
    if has_app_context():
        try:
            item = VerificationCode.query.filter_by(code_key=key).first()
            if not item:
                item = VerificationCode(code_key=key, code_hash='')
                db.session.add(item)
            item.code_hash = _hash_code(key, code)
            item.expires_at = datetime.utcnow() + timedelta(minutes=5)
            item.created_at = datetime.utcnow()
            db.session.commit()
            return
        except Exception:
            db.session.rollback()
    _verify_code_store[key] = {'code': code, 'ts': time.time()}


def _check_code(key, code):
    if has_app_context():
        try:
            item = VerificationCode.query.filter_by(code_key=key).first()
            if not item:
                return _check_memory_code(key, code)
            if item.expires_at < datetime.utcnow():
                db.session.delete(item)
                db.session.commit()
                return False
            ok = secrets.compare_digest(item.code_hash, _hash_code(key, code))
            if ok:
                db.session.delete(item)
                db.session.commit()
            return ok
        except Exception:
            db.session.rollback()

    return _check_memory_code(key, code)


def _check_memory_code(key, code):
    entry = _verify_code_store.get(key)
    if not entry:
        return False
    if time.time() - entry['ts'] > 300:
        _verify_code_store.pop(key, None)
        return False
    if entry['code'] != code:
        return False
    _verify_code_store.pop(key, None)
    return True


def _user_payload(user):
    return {
        'id': user.id,
        'username': user.username,
        'has_password': user.has_password,
        'avatar': visible_avatar_url(user.avatar),
        'created_at': user.created_at.isoformat() if user.created_at else None,
    }


def register_auth_channel_routes(app, db, logger):
    @app.route('/api/oauth/qq/url')
    def api_oauth_qq_url():
        if not QQ_APP_ID:
            return jsonify({'url': '', 'error': 'QQ登录暂未配置，请使用账号密码登录'})
        redirect_uri = urllib.parse.quote(QQ_CALLBACK_URL)
        state = str(uuid.uuid4().hex[:8])
        session['oauth_qq_state'] = state
        url = f"https://graph.qq.com/oauth2.0/authorize?response_type=code&client_id={QQ_APP_ID}&redirect_uri={redirect_uri}&state={state}&scope=get_user_info"
        return jsonify({'url': url})

    @app.route('/api/oauth/qq/callback')
    def api_oauth_qq_callback():
        code = request.args.get('code', '')
        if not code:
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=QQ登录取消")
        try:
            token_url = f"https://graph.qq.com/oauth2.0/token?grant_type=authorization_code&client_id={QQ_APP_ID}&client_secret={QQ_APP_KEY}&code={code}&redirect_uri={QQ_CALLBACK_URL}&fmt=json"
            token_resp = json.loads(urllib.request.urlopen(
                urllib.request.Request(token_url, headers={'User-Agent': 'Mozilla/5.0'}),
                timeout=10,
            ).read().decode())
            access_token = token_resp.get('access_token', '')
            if not access_token:
                return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=QQ登录失败")

            openid_url = f"https://graph.qq.com/oauth2.0/me?access_token={access_token}&fmt=json"
            me_resp = json.loads(urllib.request.urlopen(
                urllib.request.Request(openid_url, headers={'User-Agent': 'Mozilla/5.0'}),
                timeout=10,
            ).read().decode())
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
                user = User(
                    username=f'qq_{openid[:8]}',
                    password_hash=generate_password_hash(openid, method='pbkdf2:sha256'),
                    oauth_qq=openid,
                )
                db.session.add(user)
                db.session.commit()
            login_user(user, remember=True)
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_success=qq")
        except Exception as e:
            logger.error(f"[QQ OAuth] 回调处理失败: {e}")
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=QQ登录异常")

    @app.route('/api/oauth/wechat/url')
    def api_oauth_wechat_url():
        if not WECHAT_APP_ID:
            return jsonify({'url': '', 'error': '微信登录暂未配置，请使用账号密码登录'})
        redirect_uri = urllib.parse.quote(WECHAT_CALLBACK_URL)
        state = str(uuid.uuid4().hex[:8])
        session['oauth_wechat_state'] = state
        url = f"https://open.weixin.qq.com/connect/qrconnect?appid={WECHAT_APP_ID}&redirect_uri={redirect_uri}&response_type=code&scope=snsapi_login&state={state}#wechat_redirect"
        return jsonify({'url': url})

    @app.route('/api/oauth/wechat/callback')
    def api_oauth_wechat_callback():
        code = request.args.get('code', '')
        if not code:
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=微信登录取消")
        try:
            token_url = f"https://api.weixin.qq.com/sns/oauth2/access_token?appid={WECHAT_APP_ID}&secret={WECHAT_APP_SECRET}&code={code}&grant_type=authorization_code"
            token_resp = json.loads(urllib.request.urlopen(
                urllib.request.Request(token_url, headers={'User-Agent': 'Mozilla/5.0'}),
                timeout=10,
            ).read().decode())
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
                user = User(
                    username=f'wx_{openid[:8]}',
                    password_hash=generate_password_hash(openid, method='pbkdf2:sha256'),
                    oauth_wechat=openid,
                )
                db.session.add(user)
                db.session.commit()
            login_user(user, remember=True)
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_success=wechat")
        except Exception as e:
            logger.error(f"[WeChat OAuth] 回调处理失败: {e}")
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=微信登录异常")

    @app.route('/api/oauth/gitee/url')
    def api_oauth_gitee_url():
        if not GITEE_CLIENT_ID:
            return jsonify({'url': '', 'error': 'Gitee登录暂未配置，请使用其他方式登录'})
        state = str(uuid.uuid4().hex[:8])
        session['oauth_gitee_state'] = state
        url = f"https://gitee.com/oauth/authorize?client_id={GITEE_CLIENT_ID}&redirect_uri={urllib.parse.quote(GITEE_CALLBACK_URL)}&response_type=code&state={state}"
        return jsonify({'url': url})

    @app.route('/api/oauth/gitee/callback')
    def api_oauth_gitee_callback():
        code = request.args.get('code', '')
        if not code:
            return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=Gitee登录取消")
        try:
            token_url = f"https://gitee.com/oauth/token?grant_type=authorization_code&code={code}&client_id={GITEE_CLIENT_ID}&redirect_uri={urllib.parse.quote(GITEE_CALLBACK_URL)}&client_secret={GITEE_CLIENT_SECRET}"
            token_resp = json.loads(urllib.request.urlopen(
                urllib.request.Request(token_url, data=b'', headers={'Accept': 'application/json'}),
                timeout=10,
            ).read().decode())
            access_token = token_resp.get('access_token', '')
            if not access_token:
                return redirect(f"{OAUTH_ORIGIN}/#/pages/profile/index?oauth_error=Gitee登录失败")
            user_url = f"https://gitee.com/api/v5/user?access_token={access_token}"
            user_resp = json.loads(urllib.request.urlopen(
                urllib.request.Request(user_url, headers={'Accept': 'application/json'}),
                timeout=10,
            ).read().decode())
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
                user = User(
                    username=username,
                    password_hash=generate_password_hash(gitee_id, method='pbkdf2:sha256'),
                    oauth_gitee=gitee_id,
                )
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
        return jsonify(_user_payload(user))

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
        data = request.get_json(silent=True) or {}
        email_addr = (data.get('email') or '').strip()
        code = (data.get('code') or '').strip()
        if not email_addr or not code:
            return jsonify({'error': '请填写完整'}), 400
        if not _check_code('email_' + email_addr, code):
            return jsonify({'error': '验证码错误或已过期'}), 400
        user = User.query.filter_by(email=email_addr).first()
        if not user:
            return jsonify({'error': '该邮箱未绑定账号，请先使用密码登录或注册后再绑定'}), 400
        login_user(user, remember=True)
        return jsonify(_user_payload(user))
