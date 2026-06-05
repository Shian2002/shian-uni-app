"""单项术数工具路由：塔罗与各术数对话历史。"""

import json
from datetime import datetime

from flask import Response, jsonify, request, stream_with_context
from flask_login import current_user, login_required

from deepseek_service import get_tarot_followup_stream, get_tarot_reading_stream
from extensions import csrf
from models import (
    BaziConversation,
    LiuyaoConversation,
    MeihuaConversation,
    QimenConversation,
    TarotConversation,
    ZiweiConversation,
)


def register_metaphysics_routes(app, db, services):
    """注册单项术数工具相关路由。"""
    has_tarot = bool(services.get('has_tarot'))
    tarot_draw = services.get('tarot_draw')
    tarot_spreads = services.get('tarot_spreads')
    tarot_verify = services.get('tarot_verify')
    deepseek_available_func = services['deepseek_available']
    use_points = services['use_points']
    logger = services['logger']
    qimen_paipan = services['qimen_paipan']
    meihua_paipan = services['meihua_paipan']
    liuyao_paipan = services['liuyao_paipan']
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
        pan_type = data.get('panType', 2)  # 只保留新拆补法；旧参数统一归一到同一算法。

        if not all([year, month, day]):
            return jsonify({'error': '请提供完整的日期参数'}), 400

        try:
            year, month, day, hour = int(year), int(month), int(day), int(hour)
            minute, pan_type = int(minute), 2
        except (ValueError, TypeError):
            return jsonify({'error': '日期参数格式错误'}), 400

        if not (1 <= month <= 12 and 1 <= day <= 31 and 0 <= hour <= 23):
            return jsonify({'error': '日期范围错误'}), 400

        result = qimen_paipan(year, month, day, hour, minute, pan_type)
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
        pan_type = 2

        result = qimen_paipan(year, month, day, hour, minute, pan_type)
        if 'error' in result:
            return jsonify(result), 500

        return jsonify(result)


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

        result = meihua_paipan(
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

        result = meihua_paipan(
            method=method, num1=num1, num2=num2, words=words,
            year=year, month=month, day=day, hour=hour,
        )
        if 'error' in result:
            return jsonify(result), 500

        return jsonify(result)


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

        result = liuyao_paipan(mode=mode, tosses=tosses, question=question)
        if 'error' in result:
            return jsonify(result), 400

        return jsonify(result)


    @app.route('/api/liuyao/paipan', methods=['GET'])
    def api_liuyao_paipan_get():
        """六爻纳甲免费排盘 — GET 版本（方便测试，自动摇卦）"""
        result = liuyao_paipan(mode='auto')
        return jsonify(result)


    @app.route('/api/tarot/draw', methods=['POST'])
    @csrf.exempt
    def api_tarot_draw():
        if not has_tarot:
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
                'available_spreads': tarot_spreads(),
            }), 400

        try:
            result = tarot_draw(spread_name=spread_name, enable_reversed=enable_reversed)
            return jsonify(result)
        except ValueError as e:
            return jsonify({
                'code': 2,
                'msg': str(e),
                'data': None,
                'available_spreads': tarot_spreads(),
            }), 400
        except Exception as e:
            return jsonify({
                'code': 3,
                'msg': f'抽牌计算失败: {str(e)}',
                'data': None,
            }), 500


    @app.route('/api/tarot/draw', methods=['GET'])
    def api_tarot_draw_get():
        if not has_tarot:
            return jsonify({'code': 1, 'msg': '塔罗引擎不可用', 'data': None}), 503
        """塔罗牌抽牌 — GET 版本（方便测试，默认无牌阵三张）"""
        spread_name = request.args.get('spread_name', 'three')
        enable_reversed = request.args.get('enable_reversed', 'true').lower() == 'true'

        try:
            result = tarot_draw(spread_name=spread_name, enable_reversed=enable_reversed)
            return jsonify(result)
        except ValueError as e:
            return jsonify({'code': 2, 'msg': str(e), 'data': None}), 400


    @app.route('/api/tarot/spreads')
    def api_tarot_spreads():
        if not has_tarot:
            return jsonify({'code': 1, 'msg': '塔罗引擎不可用', 'data': None}), 503
        """获取所有可用牌阵信息"""
        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': tarot_spreads(),
        })


    @app.route('/api/tarot/verify')
    def api_tarot_verify():
        if not has_tarot:
            return jsonify({'code': 1, 'msg': '塔罗引擎不可用', 'data': None}), 503
        """塔罗牌牌库完整性校验"""
        result = tarot_verify()
        return jsonify(result)


    @app.route('/api/tarot/reading/stream', methods=['POST'])
    @login_required
    def api_tarot_reading_stream():
        """流式调用 DeepSeek 进行塔罗牌 AI 解读（SSE）"""
        if not deepseek_available_func():
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
