"""充值订单与付款核验路由。"""

import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib import parse as urlparse
from urllib import request as urlrequest

from flask import Response, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from extensions import csrf
from models import Membership, PointLog, RechargeOrder, RefundRequest

logger = logging.getLogger('xuancetai')


RECHARGE_PACKAGES = [
    {'id': 'test-cent', 'name': '测试包', 'points': 1, 'price': 0.01, 'package_type': 'points'},
    {'id': 'starter', 'name': '入门版', 'points': 3000, 'price': 9.9, 'package_type': 'points'},
    {'id': 'standard', 'name': '标准版', 'points': 12000, 'price': 36, 'package_type': 'points'},
    {'id': 'premium', 'name': '专业版', 'points': 30000, 'price': 68, 'package_type': 'points'},
    {'id': 'vip', 'name': '尊享版', 'points': 100000, 'price': 198, 'package_type': 'points'},
    {'id': 'ai-starter', 'name': '入门 AI 包', 'points': 0, 'price': 9.9, 'package_type': 'ai', 'ai_single_credits': 10, 'ai_combo_credits': 0, 'description': '10 次单术数 AI'},
    {'id': 'ai-standard', 'name': '标准 AI 包', 'points': 0, 'price': 19.9, 'package_type': 'ai', 'ai_single_credits': 25, 'ai_combo_credits': 0, 'description': '25 次单术数 AI'},
    {'id': 'ai-combo', 'name': '深度合参包', 'points': 0, 'price': 68, 'package_type': 'ai', 'ai_single_credits': 0, 'ai_combo_credits': 20, 'description': '20 次多术数合参'},
]

HUPIJIAO_GATEWAY_URL = os.environ.get('HUPIJIAO_GATEWAY_URL', 'https://api.xunhupay.com/payment/do.html')
HUPIJIAO_QUERY_URL = os.environ.get('HUPIJIAO_QUERY_URL', 'https://api.xunhupay.com/payment/query.html')
HUPIJIAO_REFUND_URL = os.environ.get('HUPIJIAO_REFUND_URL', 'https://api.xunhupay.com/payment/refund.html')
HUPIJIAO_TRADE_PREFIX = 'XC'
RECHARGE_PENDING_EXPIRE_SECONDS = int(os.environ.get('RECHARGE_PENDING_EXPIRE_SECONDS', '1800'))
RECHARGE_CREATE_RATE_SECONDS = int(os.environ.get('RECHARGE_CREATE_RATE_SECONDS', '10'))
REFUND_REQUEST_ACTIVE_STATUSES = ('pending', 'approved', 'processing', 'refunded')


def _amount_decimal(value):
    """按人民币分规整金额，支付验签和金额比较都走 Decimal。"""
    try:
        amount = Decimal(str(value)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        return None
    if amount <= 0:
        return None
    return amount


def _amount_text(value):
    amount = _amount_decimal(value)
    if amount is None:
        return ''
    return format(amount, 'f')


def _amount_cents(value):
    amount = _amount_decimal(value)
    if amount is None:
        return None
    return int(amount * 100)


def _order_amount_cents(order):
    cents = getattr(order, 'amount_cents', None)
    if cents is not None:
        try:
            return int(cents)
        except (TypeError, ValueError):
            return None
    return _amount_cents(order.amount)


def _hupijiao_sign(params, appsecret):
    """虎皮椒签名：非空参数按 ASCII 排序，排除 hash，末尾直接拼 APPSECRET。"""
    pairs = []
    for key in sorted(params):
        if key == 'hash':
            continue
        value = params.get(key)
        if value is None or value == '':
            continue
        pairs.append(f'{key}={value}')
    raw = '&'.join(pairs) + appsecret
    return hashlib.md5(raw.encode('utf-8')).hexdigest()


def _hupijiao_config():
    enabled = os.environ.get('HUPIJIAO_ENABLED', '').strip() == '1'
    appid = os.environ.get('HUPIJIAO_APPID', '').strip()
    appsecret = os.environ.get('HUPIJIAO_APPSECRET', '').strip()
    public_base_url = os.environ.get('PUBLIC_BASE_URL', '').strip().rstrip('/')
    gateway_url = os.environ.get('HUPIJIAO_GATEWAY_URL', HUPIJIAO_GATEWAY_URL).strip() or HUPIJIAO_GATEWAY_URL
    query_url = os.environ.get('HUPIJIAO_QUERY_URL', HUPIJIAO_QUERY_URL).strip() or HUPIJIAO_QUERY_URL
    refund_url = os.environ.get('HUPIJIAO_REFUND_URL', HUPIJIAO_REFUND_URL).strip() or HUPIJIAO_REFUND_URL
    missing = []
    if not enabled:
        missing.append('HUPIJIAO_ENABLED')
    if not appid:
        missing.append('HUPIJIAO_APPID')
    if not appsecret:
        missing.append('HUPIJIAO_APPSECRET')
    if not public_base_url:
        missing.append('PUBLIC_BASE_URL')
    return {
        'enabled': enabled,
        'appid': appid,
        'appsecret': appsecret,
        'public_base_url': public_base_url,
        'gateway_url': gateway_url,
        'query_url': query_url,
        'refund_url': refund_url,
        'missing': missing,
    }


def _hupijiao_trade_order_id(order_id):
    return f'{HUPIJIAO_TRADE_PREFIX}{int(order_id)}'


def _order_id_from_hupijiao_trade_id(trade_order_id):
    value = (trade_order_id or '').strip()
    if not value.startswith(HUPIJIAO_TRADE_PREFIX):
        return None
    raw_id = value[len(HUPIJIAO_TRADE_PREFIX):]
    if not raw_id.isdigit():
        return None
    return int(raw_id)


def _safe_json_compact(payload):
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def _build_hupijiao_order_payload(config, order, pkg):
    public_base_url = config['public_base_url']
    trade_order_id = _hupijiao_trade_order_id(order.id)
    title = f"时安解忧屋-{pkg['name']}"[:42]
    payload = {
        'version': '1.1',
        'appid': config['appid'],
        'trade_order_id': trade_order_id,
        'total_fee': _amount_text(order.amount),
        'title': title,
        'time': str(int(time.time())),
        'notify_url': f'{public_base_url}/api/recharge/hupijiao/notify',
        'return_url': f'{public_base_url}/pages/points/index',
        'callback_url': f'{public_base_url}/pages/points/index',
        'type': 'WAP',
        'wap_url': public_base_url,
        'wap_name': '时安解忧屋',
        'plugins': 'xuan-cet-tai',
        'attach': _safe_json_compact({'order_id': order.id, 'user_id': order.user_id, 'package_id': order.package_id}),
        'nonce_str': secrets.token_hex(16),
    }
    payload['hash'] = _hupijiao_sign(payload, config['appsecret'])
    return payload


def _post_hupijiao_order(gateway_url, payload, timeout=10):
    body = urlparse.urlencode(payload).encode('utf-8')
    req = urlrequest.Request(
        gateway_url,
        data=body,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode('utf-8', errors='replace')
    return json.loads(raw)


def _build_hupijiao_query_payload(config, order):
    payload = {
        'appid': config['appid'],
        'out_trade_order': _hupijiao_trade_order_id(order.id),
        'time': str(int(time.time())),
        'nonce_str': secrets.token_hex(16),
    }
    payload['hash'] = _hupijiao_sign(payload, config['appsecret'])
    return payload


def _post_hupijiao_query(query_url, payload, timeout=10):
    body = urlparse.urlencode(payload).encode('utf-8')
    req = urlrequest.Request(
        query_url,
        data=body,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode('utf-8', errors='replace')
    return json.loads(raw)


def _build_hupijiao_refund_payload(config, order, reason):
    payload = {
        'appid': config['appid'],
        'trade_order_id': _hupijiao_trade_order_id(order.id),
        'reason': (reason or '用户申请退款')[:120],
        'time': str(int(time.time())),
        'nonce_str': secrets.token_hex(16),
    }
    payload['hash'] = _hupijiao_sign(payload, config['appsecret'])
    return payload


def _post_hupijiao_refund(refund_url, payload, timeout=15):
    body = urlparse.urlencode(payload).encode('utf-8')
    req = urlrequest.Request(
        refund_url,
        data=body,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    with urlrequest.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode('utf-8', errors='replace')
    return json.loads(raw)


def _verify_hupijiao_hash(data, appsecret):
    expected = (data.get('hash') or '').strip().lower()
    if not expected:
        return False
    actual = _hupijiao_sign(data, appsecret)
    return secrets.compare_digest(expected, actual)


def _hupijiao_reference(data):
    return (data.get('transaction_id') or data.get('open_order_id') or data.get('trade_order_id') or '')[:120]


def _hupijiao_proof(data):
    return {
        'provider': 'hupijiao',
        'trade_order_id': data.get('trade_order_id', ''),
        'transaction_id': data.get('transaction_id', ''),
        'open_order_id': data.get('open_order_id', ''),
        'status': data.get('status', ''),
        'total_fee': data.get('total_fee', ''),
        'appid': data.get('appid', ''),
        'time': data.get('time', ''),
        'nonce_str': data.get('nonce_str', ''),
        'attach': data.get('attach', ''),
    }


def _hupijiao_query_reference(data):
    return (data.get('transaction_id') or data.get('open_order_id') or data.get('trade_order_id') or '')[:120]


def _hupijiao_query_proof(query_data):
    data = query_data or {}
    return {
        'provider': 'hupijiao',
        'source': 'query_reconcile',
        'trade_order_id': data.get('trade_order_id', ''),
        'transaction_id': data.get('transaction_id', ''),
        'open_order_id': data.get('open_order_id', ''),
        'status': data.get('status', ''),
        'total_fee': data.get('total_fee', ''),
    }


def query_hupijiao_order(config, order):
    payload = _build_hupijiao_query_payload(config, order)
    result = _post_hupijiao_query(config['query_url'], payload)
    errcode = int(result.get('errcode') or 0)
    if errcode != 0:
        return {
            'ok': False,
            'error': result.get('errmsg') or f'虎皮椒查询失败: {errcode}',
            'errcode': errcode,
        }
    data = result.get('data') or {}
    if not isinstance(data, dict):
        return {'ok': False, 'error': '虎皮椒查询返回格式错误', 'errcode': errcode}
    return {
        'ok': True,
        'status': (data.get('status') or '').strip(),
        'reference': _hupijiao_query_reference(data),
        'data': data,
    }


def _hupijiao_refund_status(result):
    data = result.get('data') if isinstance(result, dict) else {}
    if not isinstance(data, dict):
        data = {}
    return (result.get('refund_status') or data.get('refund_status') or data.get('status') or '').strip()


def _hupijiao_refund_reference(result, order):
    data = result.get('data') if isinstance(result, dict) else {}
    if not isinstance(data, dict):
        data = {}
    return (
        data.get('transaction_id')
        or result.get('transaction_id')
        or data.get('open_order_id')
        or result.get('open_order_id')
        or order.payment_reference
        or _hupijiao_trade_order_id(order.id)
        or ''
    )[:120]


def _safe_hupijiao_response(result):
    try:
        return json.dumps(result or {}, ensure_ascii=False, sort_keys=True)[:4000]
    except TypeError:
        return json.dumps({'raw': str(result)[:1000]}, ensure_ascii=False)


def request_hupijiao_refund(config, order, reason):
    payload = _build_hupijiao_refund_payload(config, order, reason)
    result = _post_hupijiao_refund(config['refund_url'], payload)
    errcode = int(result.get('errcode') or 0)
    status = _hupijiao_refund_status(result)
    return {
        'ok': errcode == 0,
        'errcode': errcode,
        'error': result.get('errmsg') or '',
        'refund_status': status,
        'reference': _hupijiao_refund_reference(result, order),
        'response': result,
    }


def _refund_request_to_dict(refund_request):
    order = refund_request.order
    user = refund_request.user
    return {
        'id': refund_request.id,
        'order_id': refund_request.order_id,
        'user_id': refund_request.user_id,
        'username': user.username if user else '',
        'status': refund_request.status,
        'reason': refund_request.reason or '',
        'admin_note': refund_request.admin_note or '',
        'hupijiao_status': refund_request.hupijiao_status or '',
        'package_name': order.package_name if order else '',
        'points_amount': order.points if order else 0,
        'price': order.amount if order else 0,
        'pay_method': order.pay_method if order else '',
        'payment_reference': order.payment_reference if order else '',
        'order_status': order.status if order else '',
        'created_at': refund_request.created_at.isoformat() if refund_request.created_at else None,
        'updated_at': refund_request.updated_at.isoformat() if refund_request.updated_at else None,
        'approved_at': refund_request.approved_at.isoformat() if refund_request.approved_at else None,
        'rejected_at': refund_request.rejected_at.isoformat() if refund_request.rejected_at else None,
        'resolved_at': refund_request.resolved_at.isoformat() if refund_request.resolved_at else None,
    }


def _check_order_refund_balance(order):
    pkg = next((p for p in RECHARGE_PACKAGES if p['id'] == order.package_id), None)
    membership = Membership.query.filter_by(user_id=order.user_id).first()
    if pkg and pkg.get('package_type') == 'ai':
        single = int(pkg.get('ai_single_credits') or 0)
        combo = int(pkg.get('ai_combo_credits') or 0)
        current_single = int(getattr(membership, 'ai_single_credits', 0) or 0)
        current_combo = int(getattr(membership, 'ai_combo_credits', 0) or 0)
        if current_single < single or current_combo < combo:
            return {
                'ok': False,
                'error': 'AI 次数已使用，暂不能自动退款',
                'credit_type': 'ai',
                'required': {'single': single, 'combo': combo},
                'current': {'single': current_single, 'combo': current_combo},
            }
        return {'ok': True, 'credit_type': 'ai'}

    required_points = int(order.points or 0)
    current_points = int(getattr(membership, 'points', 0) or 0)
    if current_points < required_points:
        return {
            'ok': False,
            'error': '积分余额不足，暂不能自动退款',
            'credit_type': 'points',
            'required': required_points,
            'current': current_points,
        }
    return {'ok': True, 'credit_type': 'points'}


def _refund_notice_content(refund_request):
    public_base_url = os.environ.get('PUBLIC_BASE_URL', '').strip().rstrip('/')
    order = refund_request.order
    user = refund_request.user
    admin_url = f"{public_base_url}/#/pages/admin/index?tab=refunds&request_id={refund_request.id}" if public_base_url else ''
    reason = (refund_request.reason or '未填写').strip() or '未填写'
    title_reason = reason[:24] + ('...' if len(reason) > 24 else '')
    title = f"时安解忧屋退款申请 #{refund_request.id} · {title_reason}"
    content = '\n'.join([
        '[时安解忧屋] 新退款申请',
        f"申请 #{refund_request.id} / 订单 #{refund_request.order_id}",
        f"用户: {(user.username if user else '未知')} (ID {refund_request.user_id})",
        f"套餐: {(order.package_name if order else '')} / ¥{(order.amount if order else 0)}",
        f"积分/次数: {(order.points if order else 0)}",
        f"原因: {reason}",
        f"处理: {admin_url or '请进入运营控制台退款审核'}",
    ])
    return title, content


def _notice_response_ok(data):
    if not isinstance(data, dict):
        return False
    if data.get('success') is True:
        return True
    for key in ('code', 'errcode', 'errno'):
        if key not in data:
            continue
        try:
            value = int(data.get(key))
        except (TypeError, ValueError):
            continue
        if value in (0, 1000):
            return True
    nested = data.get('data')
    if isinstance(nested, dict):
        try:
            return int(nested.get('errno')) == 0
        except (TypeError, ValueError):
            return False
    return False


def _read_notice_json(resp):
    raw = resp.read().decode('utf-8', errors='replace')
    try:
        data = json.loads(raw) if raw else {}
    except json.JSONDecodeError:
        data = {'raw': raw[:300]}
    return raw, data


def _serverchan_endpoint(sendkey):
    custom_url = os.environ.get('ALERT_SERVERCHAN_URL', '').strip()
    if custom_url:
        return custom_url.replace('{sendkey}', urlparse.quote(sendkey, safe=''))
    quoted = urlparse.quote(sendkey, safe='')
    if sendkey.startswith('sctp'):
        uid = ''
        for char in sendkey[4:]:
            if not char.isdigit():
                break
            uid += char
        if uid:
            return f'https://{uid}.push.ft07.com/send/{quoted}.send'
    return f'https://sctapi.ftqq.com/{quoted}.send'


def _send_serverchan_notice(sendkey, title, content):
    body = urlparse.urlencode({
        'title': title[:120],
        'desp': content,
        'noip': '1',
    }).encode('utf-8')
    req = urlrequest.Request(
        _serverchan_endpoint(sendkey),
        data=body,
        headers={'Content-Type': 'application/x-www-form-urlencoded'},
        method='POST',
    )
    with urlrequest.urlopen(req, timeout=8) as resp:
        raw, data = _read_notice_json(resp)
    if _notice_response_ok(data):
        return True, ''
    return False, data.get('message') or data.get('errmsg') or raw[:120]


def _send_wxpusher_notice(app_token, uids, topic_ids, title, content):
    payload = {
        'appToken': app_token,
        'summary': title[:100],
        'content': content,
        'contentType': 1,
    }
    if uids:
        payload['uids'] = uids
    if topic_ids:
        payload['topicIds'] = topic_ids
    body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
    req = urlrequest.Request(
        'https://wxpusher.zjiecode.com/api/send/message',
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urlrequest.urlopen(req, timeout=8) as resp:
        raw, data = _read_notice_json(resp)
    if _notice_response_ok(data):
        return True, ''
    return False, data.get('msg') or data.get('message') or raw[:120]


def _notice_list_from_env(name):
    return [item.strip() for item in os.environ.get(name, '').split(',') if item.strip()]


def _send_wechat_webhook_notice(webhook, content):
    text_payload = {'content': content}
    mobiles = [
        item.strip()
        for item in os.environ.get('ALERT_WECHAT_MENTION_MOBILE', '').split(',')
        if item.strip()
    ]
    if mobiles:
        text_payload['mentioned_mobile_list'] = mobiles
    body = json.dumps({'msgtype': 'text', 'text': text_payload}, ensure_ascii=False).encode('utf-8')
    req = urlrequest.Request(
        webhook,
        data=body,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with urlrequest.urlopen(req, timeout=8) as resp:
        raw, data = _read_notice_json(resp)
    if _notice_response_ok(data):
        return True, ''
    return False, data.get('errmsg') or raw[:120]


def _send_refund_request_notice(refund_request):
    title, content = _refund_notice_content(refund_request)
    attempts = []

    serverchan_sendkey = (
        os.environ.get('ALERT_SERVERCHAN_SENDKEY', '').strip()
        or os.environ.get('SERVERCHAN_SENDKEY', '').strip()
    )
    if serverchan_sendkey:
        attempts.append(('Server酱', lambda: _send_serverchan_notice(serverchan_sendkey, title, content)))

    wxpusher_app_token = os.environ.get('ALERT_WXPUSHER_APP_TOKEN', '').strip()
    wxpusher_uids = _notice_list_from_env('ALERT_WXPUSHER_UIDS')
    wxpusher_topic_ids = _notice_list_from_env('ALERT_WXPUSHER_TOPIC_IDS')
    if wxpusher_app_token and (wxpusher_uids or wxpusher_topic_ids):
        attempts.append((
            'WxPusher',
            lambda: _send_wxpusher_notice(
                wxpusher_app_token,
                wxpusher_uids,
                wxpusher_topic_ids,
                title,
                content,
            ),
        ))

    webhook = os.environ.get('ALERT_WECHAT_WEBHOOK', '').strip()
    if webhook:
        attempts.append(('微信 webhook', lambda: _send_wechat_webhook_notice(webhook, content)))

    if not attempts:
        return False, '个人微信推送未配置，请设置 ALERT_SERVERCHAN_SENDKEY 或 ALERT_WXPUSHER_APP_TOKEN/ALERT_WXPUSHER_UIDS'

    errors = []
    for label, sender in attempts:
        try:
            sent, error = sender()
        except Exception as exc:
            sent, error = False, str(exc)
        if sent:
            return True, ''
        errors.append(f'{label}: {error}')
    return False, '; '.join(errors)


def approve_refund_request(db, refund_recharge_order_once, refund_request_id, admin_id, admin_note=''):
    refund_request = db.session.get(RefundRequest, int(refund_request_id))
    if not refund_request:
        return {'ok': False, 'error': '退款申请不存在', 'status': None}
    if refund_request.status not in ('pending', 'failed'):
        return {'ok': False, 'error': '退款申请状态不可审批', 'status': refund_request.status}

    order = refund_request.order
    if not order:
        return {'ok': False, 'error': '充值订单不存在', 'status': refund_request.status}
    if order.status != 'paid':
        return {'ok': False, 'error': '订单不是已支付状态', 'status': order.status}
    if order.pay_method != 'hupijiao':
        return {'ok': False, 'error': '仅支持虎皮椒订单自动退款', 'status': order.pay_method}

    balance = _check_order_refund_balance(order)
    if not balance.get('ok'):
        refund_request.hupijiao_status = 'blocked'
        refund_request.admin_note = admin_note or refund_request.admin_note
        refund_request.updated_at = datetime.utcnow()
        db.session.commit()
        return {'ok': False, 'error': balance.get('error'), 'status': refund_request.status, 'balance': balance}

    config = _hupijiao_config()
    if config['missing']:
        return {'ok': False, 'error': '虎皮椒支付暂未配置', 'missing': config['missing']}

    now = datetime.utcnow()
    refund_request.status = 'approved'
    refund_request.admin_id = admin_id
    refund_request.admin_note = admin_note or ''
    refund_request.approved_at = now
    refund_request.updated_at = now
    db.session.commit()

    try:
        remote = request_hupijiao_refund(config, order, refund_request.reason or admin_note or '用户申请退款')
    except Exception as exc:
        refund_request.status = 'failed'
        refund_request.hupijiao_status = 'request_error'
        refund_request.hupijiao_response = json.dumps({'error': str(exc)}, ensure_ascii=False)[:4000]
        refund_request.updated_at = datetime.utcnow()
        db.session.commit()
        logger.warning("虎皮椒退款 API 请求异常: request_id=%s order_id=%s error=%s", refund_request.id, order.id, exc)
        return {'ok': False, 'error': '虎皮椒退款请求失败', 'detail': str(exc)}

    refund_status = remote.get('refund_status') or ''
    refund_request.hupijiao_status = refund_status
    refund_request.hupijiao_response = _safe_hupijiao_response(remote.get('response'))

    if not remote.get('ok'):
        refund_request.status = 'failed'
        refund_request.updated_at = datetime.utcnow()
        db.session.commit()
        return {'ok': False, 'error': remote.get('error') or '虎皮椒退款失败', 'status': refund_status}

    if refund_status == 'CD':
        result = refund_recharge_order_once(order.id, {
            'refund_reference': remote.get('reference') or order.payment_reference or f'hupijiao-refund:{order.id}',
            'refund_proof': _safe_hupijiao_response(remote.get('response')),
            'refunded_at': datetime.utcnow(),
        })
        if not result.get('ok') and result.get('status') != 'refunded':
            refund_request.status = 'failed'
            refund_request.updated_at = datetime.utcnow()
            db.session.commit()
            return {'ok': False, 'error': result.get('error') or '本站积分回退失败', 'status': result.get('status')}
        refund_request.status = 'refunded'
        refund_request.resolved_at = datetime.utcnow()
        refund_request.updated_at = refund_request.resolved_at
        db.session.commit()
        return {'ok': True, 'status': 'refunded', 'request': _refund_request_to_dict(refund_request), 'refund': result}

    if refund_status == 'RD':
        refund_request.status = 'processing'
        refund_request.updated_at = datetime.utcnow()
        db.session.commit()
        return {'ok': True, 'status': 'processing', 'request': _refund_request_to_dict(refund_request)}

    refund_request.status = 'failed'
    refund_request.updated_at = datetime.utcnow()
    db.session.commit()
    return {'ok': False, 'error': remote.get('error') or f'虎皮椒退款状态异常: {refund_status or "unknown"}', 'status': refund_status}


def reconcile_hupijiao_refunds(
    db,
    refund_recharge_order_once,
    query_order_func=None,
    *,
    lookback_days=14,
    limit=50,
    order_id=None,
    dry_run=False,
):
    """查询虎皮椒订单状态，把已退款的 paid 订单自动回退积分。"""
    config = _hupijiao_config()
    if config['missing']:
        return {'ok': False, 'error': '虎皮椒支付暂未配置', 'missing': config['missing']}

    lookback_days = max(int(lookback_days or 1), 1)
    limit = min(max(int(limit or 1), 1), 200)
    query_order = query_order_func or query_hupijiao_order

    orders_query = RechargeOrder.query.filter(
        RechargeOrder.pay_method == 'hupijiao',
        RechargeOrder.status == 'paid',
    )
    if order_id:
        orders_query = orders_query.filter(RechargeOrder.id == int(order_id))
    else:
        cutoff = datetime.utcnow() - timedelta(days=lookback_days)
        orders_query = orders_query.filter(RechargeOrder.created_at >= cutoff)
    orders = orders_query.order_by(RechargeOrder.id.desc()).limit(limit).all()

    summary = {'ok': True, 'checked': len(orders), 'refunded': [], 'skipped': [], 'failed': []}
    for order in orders:
        try:
            remote = query_order(config, order)
        except Exception as exc:
            db.session.rollback()
            logger.warning("虎皮椒退款对账查询异常: order_id=%s error=%s", order.id, exc)
            summary['failed'].append({'order_id': order.id, 'error': str(exc)})
            continue

        if not remote.get('ok'):
            db.session.rollback()
            summary['failed'].append({'order_id': order.id, 'error': remote.get('error', '查询失败')})
            continue

        remote_status = remote.get('status') or ''
        if remote_status != 'CD':
            summary['skipped'].append({'order_id': order.id, 'remote_status': remote_status})
            continue

        remote_reference = remote.get('reference') or ''
        payment_reference = order.payment_reference or ''
        if payment_reference and remote_reference and remote_reference != payment_reference:
            summary['failed'].append({
                'order_id': order.id,
                'error': '支付流水号不匹配',
                'remote_reference': remote_reference,
            })
            continue

        if dry_run:
            summary['skipped'].append({'order_id': order.id, 'remote_status': remote_status, 'dry_run': True})
            continue

        proof = _hupijiao_query_proof(remote.get('data') or {})
        result = refund_recharge_order_once(order.id, {
            'refund_reference': remote_reference or f'hupijiao-query:{order.id}',
            'refund_proof': json.dumps(proof, ensure_ascii=False, sort_keys=True),
            'refunded_at': datetime.utcnow(),
        })
        if result.get('ok') or result.get('status') == 'refunded':
            related_request = RefundRequest.query.filter(
                RefundRequest.order_id == order.id,
                RefundRequest.status.in_(('pending', 'approved', 'processing', 'failed')),
            ).order_by(RefundRequest.id.desc()).first()
            if related_request:
                related_request.status = 'refunded'
                related_request.hupijiao_status = 'CD'
                related_request.resolved_at = datetime.utcnow()
                related_request.updated_at = related_request.resolved_at
                db.session.commit()
            logger.info(
                "虎皮椒退款对账回退成功: order_id=%s user_id=%s refunded=%s credit_type=%s reference=%s",
                order.id,
                result.get('user_id', order.user_id),
                result.get('refunded', 0),
                result.get('credit_type', ''),
                remote_reference,
            )
            summary['refunded'].append({
                'order_id': order.id,
                'user_id': result.get('user_id', order.user_id),
                'refunded': result.get('refunded', 0),
                'credit_type': result.get('credit_type', ''),
            })
        else:
            logger.warning("虎皮椒退款对账回退失败: order_id=%s error=%s", order.id, result.get('error'))
            summary['failed'].append({
                'order_id': order.id,
                'error': result.get('error', '退款回退失败'),
                'status': result.get('status'),
            })

    return summary


def _expire_stale_hupijiao_pending_orders(db, user_id=None):
    """取消过期的虎皮椒待支付订单，避免同一用户长时间堆积无效账单。"""
    now = datetime.utcnow()
    cutoff = now - timedelta(seconds=max(RECHARGE_PENDING_EXPIRE_SECONDS, 60))
    query = RechargeOrder.query.filter(
        RechargeOrder.status == 'pending',
        RechargeOrder.pay_method == 'hupijiao',
        RechargeOrder.created_at < cutoff,
    )
    if user_id:
        query = query.filter(RechargeOrder.user_id == user_id)
    return query.update({'status': 'cancelled', 'updated_at': now}, synchronize_session=False)


def _recent_pending_order_exists(user_id):
    cutoff = datetime.utcnow() - timedelta(seconds=max(RECHARGE_CREATE_RATE_SECONDS, 1))
    return RechargeOrder.query.filter(
        RechargeOrder.user_id == user_id,
        RechargeOrder.pay_method == 'hupijiao',
        RechargeOrder.status == 'pending',
        RechargeOrder.created_at >= cutoff,
    ).first() is not None


def make_confirm_recharge_order_once(db, get_or_create_membership, add_points):
    """构造幂等订单确认函数，供用户端和后台共用。"""

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

    return confirm_recharge_order_once


def make_refund_recharge_order_once(db, get_or_create_membership):
    """构造幂等退款回退函数；只允许 paid 订单回退一次。"""

    def refund_recharge_order_once(order_id, extra_update=None):
        now = datetime.utcnow()
        try:
            update_data = {'status': 'refunded', 'updated_at': now, 'refunded_at': now}
            if extra_update:
                update_data.update(extra_update)
            changed = RechargeOrder.query.filter_by(id=order_id, status='paid').update(
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
            membership = get_or_create_membership(order.user_id, commit=False)
            if pkg and pkg.get('package_type') == 'ai':
                single = int(pkg.get('ai_single_credits') or 0)
                combo = int(pkg.get('ai_combo_credits') or 0)
                if int(membership.ai_single_credits or 0) < single or int(membership.ai_combo_credits or 0) < combo:
                    db.session.rollback()
                    return {'ok': False, 'error': 'AI 次数不足，无法自动回退', 'status': 'paid'}
                membership.ai_single_credits = int(membership.ai_single_credits or 0) - single
                membership.ai_combo_credits = int(membership.ai_combo_credits or 0) - combo
                db.session.add(PointLog(
                    user_id=order.user_id,
                    action='ai_credit_refund',
                    points=0,
                    description=f"{order.package_name}退款回退: 单术数-{single}次 合参-{combo}次 (¥{order.amount})",
                    dedupe_key=f'refund_order:{order.id}',
                ))
                new_total = membership.points
                refunded = single or combo
                credit_type = 'ai_single_credits' if single else 'ai_combo_credits'
            else:
                refund_points = int(order.points or 0)
                if int(membership.points or 0) < refund_points:
                    db.session.rollback()
                    return {'ok': False, 'error': '积分不足，无法自动回退', 'status': 'paid'}
                membership.points = int(membership.points or 0) - refund_points
                db.session.add(PointLog(
                    user_id=order.user_id,
                    action='recharge_refund',
                    points=-refund_points,
                    description=f'充值退款回退: -{refund_points}分 (¥{order.amount})',
                    dedupe_key=f'refund_order:{order.id}',
                ))
                new_total = membership.points
                refunded = refund_points
                credit_type = 'points'
            db.session.commit()
            return {
                'ok': True,
                'order_id': order.id,
                'user_id': order.user_id,
                'points': new_total,
                'refunded': refunded,
                'credit_type': credit_type,
            }
        except IntegrityError:
            db.session.rollback()
            order = db.session.get(RechargeOrder, order_id)
            return {'ok': False, 'error': '订单状态错误', 'status': order.status if order else None}

    return refund_recharge_order_once


def register_recharge_routes(app, db, services):
    """注册 /api/recharge/* 路由。"""
    confirm_recharge_order_once = services['confirm_recharge_order_once']
    refund_recharge_order_once = services['refund_recharge_order_once']

    @app.route('/api/recharge/packages', methods=['GET'])
    def api_recharge_packages():
        """获取充值套餐列表。"""
        return jsonify({'packages': RECHARGE_PACKAGES})

    @app.route('/api/recharge/create-order', methods=['POST'])
    @login_required
    def api_recharge_create_order():
        """创建充值订单。"""
        data = request.get_json(silent=True) or {}
        pkg_id = (data.get('package_id') or '').strip()
        pay_method = (data.get('pay_method') or '').strip()

        pkg = next((p for p in RECHARGE_PACKAGES if p['id'] == pkg_id), None)
        if not pkg:
            return jsonify({'error': '无效的套餐'}), 400
        if pay_method != 'hupijiao':
            return jsonify({'error': '当前仅支持虎皮椒支付'}), 400
        config = _hupijiao_config()
        if config['missing']:
            return jsonify({'error': '虎皮椒支付暂未配置', 'missing': config['missing']}), 503
        _expire_stale_hupijiao_pending_orders(db, current_user.id)
        if _recent_pending_order_exists(current_user.id):
            db.session.rollback()
            return jsonify({'error': '下单过快，请稍后再试'}), 429

        order = RechargeOrder(
            user_id=current_user.id,
            package_id=pkg['id'],
            package_name=pkg['name'],
            points=pkg['points'],
            amount=pkg['price'],
            amount_cents=_amount_cents(pkg['price']),
            pay_method=pay_method,
            status='pending',
        )
        db.session.add(order)
        db.session.commit()

        payload = _build_hupijiao_order_payload(config, order, pkg)
        try:
            pay_result = _post_hupijiao_order(config['gateway_url'], payload)
        except Exception as e:
            logger.warning(f"虎皮椒下单失败: order_id={order.id} error={e}")
            return jsonify({'error': '创建支付订单失败，请稍后重试'}), 502
        if int(pay_result.get('errcode') or 0) != 0:
            message = pay_result.get('errmsg') or '创建支付订单失败'
            logger.warning(f"虎皮椒下单返回失败: order_id={order.id} err={message}")
            return jsonify({'error': message}), 502

        return jsonify({
            'ok': True,
            'order_id': order.id,
            'trade_order_id': payload['trade_order_id'],
            'points_amount': pkg['points'],
            'package_type': pkg.get('package_type', 'points'),
            'ai_single_credits': pkg.get('ai_single_credits', 0),
            'ai_combo_credits': pkg.get('ai_combo_credits', 0),
            'price': pkg['price'],
            'status': 'pending',
            'pay_url': pay_result.get('url') or '',
            'qrcode_url': pay_result.get('url_qrcode') or '',
        })

    @app.route('/api/recharge/hupijiao/notify', methods=['POST'])
    @csrf.exempt
    def api_recharge_hupijiao_notify():
        """虎皮椒异步支付回调。回调不依赖登录态，只信服务端验签结果。"""
        data = request.form.to_dict(flat=True)
        if not data and request.is_json:
            data = request.get_json(silent=True) or {}
        data = {str(k): '' if v is None else str(v) for k, v in (data or {}).items()}
        config = _hupijiao_config()
        if not config['appid'] or not config['appsecret']:
            logger.warning("虎皮椒回调失败: 未配置 appid/appsecret")
            return Response('failed', mimetype='text/plain'), 400
        if data.get('appid') != config['appid']:
            logger.warning("虎皮椒回调失败: appid 不匹配")
            return Response('failed', mimetype='text/plain'), 400
        if not _verify_hupijiao_hash(data, config['appsecret']):
            logger.warning("虎皮椒回调失败: 签名错误")
            return Response('failed', mimetype='text/plain'), 400
        status = data.get('status')
        if status not in ('OD', 'CD'):
            logger.info(f"虎皮椒回调忽略非入账/退款状态: status={status}")
            return Response('success', mimetype='text/plain')

        order_id = _order_id_from_hupijiao_trade_id(data.get('trade_order_id'))
        order = db.session.get(RechargeOrder, order_id) if order_id else None
        if not order:
            logger.warning(f"虎皮椒回调失败: 订单不存在 trade_order_id={data.get('trade_order_id')}")
            return Response('failed', mimetype='text/plain'), 404
        if order.pay_method != 'hupijiao':
            logger.warning(f"虎皮椒回调失败: 支付方式不匹配 order_id={order.id} pay_method={order.pay_method}")
            return Response('failed', mimetype='text/plain'), 400
        if _order_amount_cents(order) != _amount_cents(data.get('total_fee')):
            logger.warning(f"虎皮椒回调失败: 金额不匹配 order_id={order.id}")
            return Response('failed', mimetype='text/plain'), 400

        if status == 'CD':
            if order.status == 'refunded':
                return Response('success', mimetype='text/plain')
            result = refund_recharge_order_once(order.id, {
                'refund_reference': _hupijiao_reference(data),
                'refund_proof': json.dumps(_hupijiao_proof(data), ensure_ascii=False, sort_keys=True),
                'refunded_at': datetime.utcnow(),
            })
            if result.get('ok') or result.get('status') == 'refunded':
                logger.info(
                    "虎皮椒退款回退成功: order_id=%s user_id=%s refunded=%s credit_type=%s reference=%s",
                    order.id,
                    result.get('user_id', order.user_id),
                    result.get('refunded', 0),
                    result.get('credit_type', ''),
                    _hupijiao_reference(data),
                )
                return Response('success', mimetype='text/plain')
            logger.warning(f"虎皮椒退款回退失败: order_id={order.id} error={result.get('error')}")
            return Response('failed', mimetype='text/plain'), 400

        if order.status == 'paid':
            return Response('success', mimetype='text/plain')

        payment_reference = _hupijiao_reference(data)
        result = confirm_recharge_order_once(order.id, {
            'pay_method': 'hupijiao',
            'payment_reference': payment_reference,
            'payment_proof': json.dumps(_hupijiao_proof(data), ensure_ascii=False, sort_keys=True),
            'verified_at': datetime.utcnow(),
        })
        if result.get('ok') or result.get('status') == 'paid':
            logger.info(
                "虎皮椒支付入账成功: order_id=%s user_id=%s added=%s credit_type=%s reference=%s",
                order.id,
                result.get('user_id', order.user_id),
                result.get('added', 0),
                result.get('credit_type', ''),
                payment_reference,
            )
            return Response('success', mimetype='text/plain')
        logger.warning(f"虎皮椒回调入账失败: order_id={order.id} error={result.get('error')}")
        return Response('failed', mimetype='text/plain'), 400

    @app.route('/api/recharge/verify-payment', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_recharge_verify_payment():
        """历史截图充值接口已停用，积分中心只保留虎皮椒支付。"""
        return jsonify({'error': '支付宝截图充值已停用，请使用虎皮椒支付'}), 410

    @app.route('/api/recharge/orders/<int:order_id>/refund-request', methods=['POST'])
    @login_required
    def api_recharge_refund_request(order_id):
        """用户对自己的虎皮椒已支付订单发起退款申请。"""
        order = RechargeOrder.query.filter_by(id=order_id, user_id=current_user.id).first()
        if not order:
            return jsonify({'error': '订单不存在'}), 404
        if order.pay_method != 'hupijiao':
            return jsonify({'error': '当前仅支持虎皮椒订单申请退款'}), 400
        if order.status != 'paid':
            return jsonify({'error': '只有已支付订单可以申请退款', 'status': order.status}), 400

        active_request = RefundRequest.query.filter(
            RefundRequest.order_id == order.id,
            RefundRequest.status.in_(REFUND_REQUEST_ACTIVE_STATUSES),
        ).order_by(RefundRequest.id.desc()).first()
        if active_request:
            return jsonify({
                'error': '该订单已有退款申请',
                'request': _refund_request_to_dict(active_request),
            }), 409

        balance = _check_order_refund_balance(order)
        if not balance.get('ok'):
            return jsonify({'error': balance.get('error'), 'balance': balance}), 409

        data = request.get_json(silent=True) or {}
        reason = (data.get('reason') or '').strip()[:300]
        refund_request = RefundRequest(
            order_id=order.id,
            user_id=current_user.id,
            reason=reason,
            status='pending',
        )
        db.session.add(refund_request)
        db.session.commit()

        sent, notify_error = _send_refund_request_notice(refund_request)
        if sent:
            refund_request.notify_sent_at = datetime.utcnow()
            db.session.commit()
        elif notify_error:
            logger.warning("退款申请微信提醒失败: request_id=%s error=%s", refund_request.id, notify_error)

        return jsonify({'ok': True, 'request': _refund_request_to_dict(refund_request), 'notify_sent': bool(sent)})

    @app.route('/api/recharge/orders', methods=['GET'])
    @login_required
    def api_recharge_orders():
        """查询我的充值记录。"""
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
            'refund_request': (
                _refund_request_to_dict(o.refund_requests.order_by(RefundRequest.id.desc()).first())
                if o.refund_requests.count() else None
            ),
            'created_at': o.created_at.isoformat() if o.created_at else None,
            'paid_at': o.updated_at.isoformat() if o.status == 'paid' and o.updated_at else None,
        } for o in pagination.items]
        return jsonify({'orders': orders, 'total': pagination.total, 'page': page, 'has_next': pagination.has_next})
