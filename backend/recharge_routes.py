"""充值订单与付款核验路由。"""

import hashlib
import json
import logging
import os
import re
import secrets
import shutil
import subprocess
import tempfile
import time
from datetime import datetime

from flask import jsonify, request
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

RECHARGE_SMALL_AUTO_LIMIT = float(os.environ.get('RECHARGE_SMALL_AUTO_LIMIT', '29.9'))
RECHARGE_MANUAL_MESSAGE = '付款截图已提交，大额充值每日 10:00 - 24:00 在线确认，非在线时间可能延迟到账'


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


def _save_recharge_proof_file(app, allowed_file, file_storage):
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


def register_recharge_routes(app, db, services):
    """注册 /api/recharge/* 路由。"""
    confirm_recharge_order_once = services['confirm_recharge_order_once']
    allowed_file = services['allowed_file']

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
                proof_url, image_hash, ocr_text = _save_recharge_proof_file(app, allowed_file, proof_file)
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
