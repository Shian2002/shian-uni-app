"""首页综合 AI 对话、盘面 artifact 与历史接口。"""

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from flask import Response, jsonify, request, stream_with_context
from flask_login import current_user, login_required

from ai_runs import mark_ai_run_done, mark_ai_run_failed, mark_ai_run_running, start_ai_run
from comprehensive_ai import (
    COMPREHENSIVE_LLM_MODELS,
    COMPREHENSIVE_TOOL_MODELS,
    TOOL_DISPLAY_ORDER,
    calculate_cost,
    normalize_tool_models,
    recommend_tool_models,
    build_tool_analysis_messages,
    build_summary_messages,
)
from deepseek_service import get_reading_stream
from models import ComprehensiveConversation, UserProfile


_TOOL_DISPLAY = {'bazi': '八字', 'ziwei': '紫微斗数', 'qimen': '奇门遁甲', 'liuyao': '六爻', 'meihua': '梅花易数', 'tarot': '塔罗牌', 'zeji': '择吉工具'}


def register_comprehensive_routes(app, db, services):
    """注册首页综合 AI 相关路由。"""
    get_or_create_membership = services['get_or_create_membership']
    spend_ai_quota_once = services['spend_ai_quota_once']
    qimen_paipan = services['qimen_paipan']
    liuyao_paipan = services['liuyao_paipan']
    meihua_paipan = services['meihua_paipan']
    tarot_draw = services.get('tarot_draw')
    compute_huangli_local = services['compute_huangli_local']
    score_zeji_day = services['score_zeji_day']
    ziwei_engine = services.get('ziwei_engine')
    has_ziwei = bool(services.get('has_ziwei'))
    logger = services['logger']
    get_build_one_tool_override = services.get('get_build_one_tool_override') or (lambda: None)
    get_reading_stream_func = services.get('get_reading_stream') or (lambda: get_reading_stream)

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
        if not has_ziwei:
            return {'error': '紫微斗数引擎不可用'}
        meta = profile.get('meta') or {}
        year, month, day, hour, minute = _split_birth_time(profile.get('birth_time'))
        date_type = 'lunar' if profile.get('cal_type') == '农历' else 'solar'
        result = ziwei_engine.calculate(
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
        result = qimen_paipan(now.year, now.month, now.day, now.hour, now.minute, 2)
        if result.get('error'):
            return {'error': result.get('error')}
        context = dict(result or {})
        context['question'] = question or ''
        return context


    def build_liuyao_context_from_question(question=''):
        result = liuyao_paipan(mode='auto', question=question or '')
        if result.get('error'):
            return {'error': result.get('error')}
        context = dict(result or {})
        context['question'] = result.get('question') or question or ''
        return context


    def build_meihua_context_from_question(question=''):
        result = meihua_paipan(method='time')
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
        if not tarot_draw:
            return {'error': '塔罗引擎不可用'}
        q = str(question or '')
        spread_name = 'three'
        if any(k in q for k in ['是', '否', '能不能', '要不要']):
            spread_name = 'single'
        elif any(k in q for k in ['关系', '感情', '复合', '回来']):
            spread_name = 'relationship'
        result = tarot_draw(spread_name=spread_name, enable_reversed=True)
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
            h = compute_huangli_local(cursor.year, cursor.month, cursor.day)
            score, reasons, warnings = score_zeji_day(zeji_type, h)
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



    def _build_one_tool(tool, profile, question):
        override = get_build_one_tool_override()
        if callable(override):
            return override(tool, profile, question)
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


    def save_comprehensive_conversation(data, user_id, question, profile, tool_models, paipan_context, artifacts, model_id, cost, history, answer):
        messages = list(history or [])
        messages.append({'role': 'user', 'content': question})
        messages.append({'role': 'assistant', 'content': _comprehensive_summary_only(answer)})
        conv_id = data.get('conversation_id')
        conv = None
        if conv_id:
            conv = ComprehensiveConversation.query.filter_by(id=conv_id, user_id=user_id).first()
        if not conv:
            conv = ComprehensiveConversation(user_id=user_id, created_at=datetime.utcnow())
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

        current_user_id = current_user.id
        ai_run = start_ai_run('comprehensive', user_id=current_user_id, request_json={
            'question': question,
            'tool_models': tool_models,
            'model_id': model_id,
            'is_followup': is_followup,
            'profile_count': profile_count,
        })

        def generate():
            try:
                mark_ai_run_running(ai_run.id)
                yield _event({'run_id': ai_run.id, 'stage': 'profile', 'message': '正在读取命盘档案'})
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
                spend = spend_ai_quota_once(current_user_id, tool_models, cost, is_followup=is_followup)
                if not spend.get('ok'):
                    mark_ai_run_failed(ai_run.id, '积分不足', {'current': spend.get('current'), 'required': cost})
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
                    for chunk, error in get_reading_stream_func()(tool_messages):
                        if error:
                            mark_ai_run_failed(ai_run.id, error, {'tool': tool})
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
                        for chunk, error in get_reading_stream_func()(yun_messages):
                            if error:
                                mark_ai_run_failed(ai_run.id, error, {'tool': tool, 'tool_key': 'bazi.yun'})
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
                for chunk, error in get_reading_stream_func()(summary_messages):
                    if error:
                        mark_ai_run_failed(ai_run.id, error, {'stage': 'summary'})
                        yield _event({'error': error})
                        return
                    if chunk:
                        summary_text += chunk
                        full_text += chunk
                        yield _event({'summary': True, 'content': chunk})
                conv = save_comprehensive_conversation(data, current_user_id, question, profile, tool_models, paipan_context, artifacts, model_id, cost, history, summary_text)
                points_left = get_or_create_membership(current_user_id).points
                membership = get_or_create_membership(current_user_id)
                mark_ai_run_done(ai_run.id, {
                    'conversation_id': conv.id,
                    'points_left': points_left,
                    'used_credit': spend.get('used_credit'),
                    'tool_models': tool_models,
                })
                yield _event({
                    'done': True,
                    'run_id': ai_run.id,
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
                mark_ai_run_failed(ai_run.id, exc)
                yield _event({'error': '综合解读失败：' + str(exc)[:120]})

        return Response(stream_with_context(generate()), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
