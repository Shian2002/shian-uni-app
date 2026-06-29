"""充值订单与付款核验路由。"""

import hashlib
import json
import logging
import os
import secrets
import time
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from urllib import parse as urlparse
from urllib import request as urlrequest

from flask import Response, jsonify, request
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError

from extensions import csrf
from models import Membership, PointLog, RechargeOrder

logger = logging.getLogger('xuancetai')


RECHARGE_PACKAGES = [
    {'id': 'test-cent', 'name': '测试包', 'points': 1, 'price': 0.01, 'package_type': 'points'},
    {'id': 'starter', 'name': '体验包', 'points': 60, 'price': 9.9, 'package_type': 'points'},
    {'id': 'standard', 'name': '标准包', 'points': 240, 'price': 29.9, 'package_type': 'points'},
    {'id': 'premium', 'name': '畅享包', 'points': 650, 'price': 68, 'package_type': 'points'},
    {'id': 'vip', 'name': '尊享包', 'points': 2200, 'price': 198, 'package_type': 'points'},
    {'id': 'ai-starter', 'name': '入门 AI 包', 'points': 0, 'price': 9.9, 'package_type': 'ai', 'ai_single_credits': 10, 'ai_combo_credits': 0, 'description': '10 次单术数 AI'},
    {'id': 'ai-standard', 'name': '标准 AI 包', 'points': 0, 'price': 19.9, 'package_type': 'ai', 'ai_single_credits': 25, 'ai_combo_credits': 0, 'description': '25 次单术数 AI'},
    {'id': 'ai-combo', 'name': '深度合参包', 'points': 0, 'price': 68, 'package_type': 'ai', 'ai_single_credits': 0, 'ai_combo_credits': 20, 'description': '20 次多术数合参'},
]

HUPIJIAO_GATEWAY_URL = os.environ.get('HUPIJIAO_GATEWAY_URL', 'https://api.xunhupay.com/payment/do.html')
HUPIJIAO_TRADE_PREFIX = 'XC'


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


def _verify_hupijiao_hash(data, appsecret):
    expected = (data.get('hash') or '').strip().lower()
    if not expected:
        return False
    actual = _hupijiao_sign(data, appsecret)
    return secrets.compare_digest(expected, actual)


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


def register_recharge_routes(app, db, services):
    """注册 /api/recharge/* 路由。"""
    confirm_recharge_order_once = services['confirm_recharge_order_once']

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
        if data.get('status') != 'OD':
            logger.info(f"虎皮椒回调忽略非支付成功状态: status={data.get('status')}")
            return Response('success', mimetype='text/plain')

        order_id = _order_id_from_hupijiao_trade_id(data.get('trade_order_id'))
        order = db.session.get(RechargeOrder, order_id) if order_id else None
        if not order:
            logger.warning(f"虎皮椒回调失败: 订单不存在 trade_order_id={data.get('trade_order_id')}")
            return Response('failed', mimetype='text/plain'), 404
        if order.pay_method != 'hupijiao':
            logger.warning(f"虎皮椒回调失败: 支付方式不匹配 order_id={order.id} pay_method={order.pay_method}")
            return Response('failed', mimetype='text/plain'), 400
        if _amount_cents(order.amount) != _amount_cents(data.get('total_fee')):
            logger.warning(f"虎皮椒回调失败: 金额不匹配 order_id={order.id}")
            return Response('failed', mimetype='text/plain'), 400
        if order.status == 'paid':
            return Response('success', mimetype='text/plain')

        payment_reference = (data.get('transaction_id') or data.get('open_order_id') or data.get('trade_order_id') or '')[:120]
        proof = {
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
        result = confirm_recharge_order_once(order.id, {
            'pay_method': 'hupijiao',
            'payment_reference': payment_reference,
            'payment_proof': json.dumps(proof, ensure_ascii=False, sort_keys=True),
            'verified_at': datetime.utcnow(),
        })
        if result.get('ok') or result.get('status') == 'paid':
            return Response('success', mimetype='text/plain')
        logger.warning(f"虎皮椒回调入账失败: order_id={order.id} error={result.get('error')}")
        return Response('failed', mimetype='text/plain'), 400

    @app.route('/api/recharge/verify-payment', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_recharge_verify_payment():
        """历史截图充值接口已停用，积分中心只保留虎皮椒支付。"""
        return jsonify({'error': '支付宝截图充值已停用，请使用虎皮椒支付'}), 410

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
            'created_at': o.created_at.isoformat() if o.created_at else None,
            'paid_at': o.updated_at.isoformat() if o.status == 'paid' and o.updated_at else None,
        } for o in pagination.items]
        return jsonify({'orders': orders, 'total': pagination.total, 'page': page, 'has_next': pagination.has_next})
