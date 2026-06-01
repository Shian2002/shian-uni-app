"""八字 AI 流式解读 API。"""

import json
import os
import threading
import time

from flask import Response, jsonify, request
from flask_login import current_user

from extensions import csrf
from models import BaziRecord, Record

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - 生产依赖缺失时由接口返回错误
    OpenAI = None


_bazi_ask_current_run = 0
_bazi_ask_lock = threading.Lock()


def _relation_text(items):
    text = str(items or [])
    return text[1:-1] if text and text != '[]' else '无'


def _build_bazi_text(pan_result, label=''):
    fp = pan_result.get('four_pillars', {})
    shi_shen = pan_result.get('shi_shen', {})
    cang_gan = pan_result.get('cang_gan', {})
    cang_gan_ss = pan_result.get('cang_gan_shi_shen', {})
    shen_sha_pp = pan_result.get('shen_sha_per_pillar', {})

    pillars_detail = ''
    for pillar in ['year', 'month', 'day', 'hour']:
        column = fp.get(pillar, {})
        hidden = cang_gan.get(pillar, [])
        hidden_shishen = cang_gan_ss.get(pillar, [])
        hidden_parts = [
            f'{hidden[i]}({hidden_shishen[i]})'
            for i in range(min(len(hidden), len(hidden_shishen)))
        ]
        shen_sha = shen_sha_pp.get(pillar, [])
        pillars_detail += (
            f"  {pillar}柱: {column.get('gan_zhi', '')}  "
            f"天干十神: {shi_shen.get(pillar + '_gan', '')}  "
            f"纳音: {column.get('nayin', '')}  "
            f"藏干: {','.join(hidden_parts) if hidden_parts else '无'}  "
            f"神煞: {','.join(shen_sha) if shen_sha else '无'}\n"
        )

    dayun_text = ''
    for dayun in pan_result.get('da_yun', []):
        dayun_text += (
            f"  {dayun.get('start_age', '?')}~{dayun.get('end_age', '?')}岁: "
            f"{dayun.get('gan_zhi', '')} 十神: "
            f"{dayun.get('gan_shishen_abbrev', '')}/{dayun.get('zhi_shishen_abbrev', '')}  "
            f"纳音: {dayun.get('nayin', '')} 神煞: {','.join(dayun.get('shen_sha', []) or [])}  "
            f"冲合: {_relation_text(dayun.get('pillar_relations', []))}\n"
        )

    liunian_text = ''
    for liunian in (pan_result.get('liu_nian', []) or [])[:10]:
        liunian_text += (
            f"  {liunian.get('year', '')}: {liunian.get('gan_zhi', '')} "
            f"十神: {liunian.get('gan_shishen_abbrev', '')}/{liunian.get('zhi_shishen_abbrev', '')}  "
            f"纳音: {liunian.get('nayin', '')} 神煞: {','.join(liunian.get('shen_sha', []) or [])}  "
            f"冲合: {_relation_text(liunian.get('pillar_relations', []))}\n"
        )

    geju = pan_result.get('geju', {})
    tiaohou = pan_result.get('tiaohou', {})
    name = pan_result.get('name', '') or label or pan_result.get('_record_name', '')
    return f"""【命盘】{name}
  性别: {pan_result.get('gender', '')}  出生: {pan_result.get('birth_solar', '')}
  日主: {fp.get('day', {}).get('gan', '')}({fp.get('day', {}).get('wu_xing', '')})
  旺衰: {pan_result.get('wang_shuai', '')}  格局: {geju.get('name', '无')}
  四柱: {fp.get('year', {}).get('gan_zhi', '')} {fp.get('month', {}).get('gan_zhi', '')} {fp.get('day', {}).get('gan_zhi', '')} {fp.get('hour', {}).get('gan_zhi', '')}
  五行: {pan_result.get('wu_xing', '')}  缺: {', '.join(pan_result.get('lack_wuxing', [])) if pan_result.get('lack_wuxing') else '无'}

【四柱详解】
{pillars_detail}
【格局】{geju.get('name', '无')}  {geju.get('desc', '')}
【调候用神】{tiaohou.get('shen', '无')}  {tiaohou.get('desc', '')}
【大运】（起运{pan_result.get('qi_yun_age', '?')}岁，{pan_result.get('da_yun_direction', '')}行）
{dayun_text}
【近期流年】
{liunian_text}"""


def _build_bazi_messages(run_dir, question, system_prompt):
    pan_path = os.path.join(run_dir, 'pan.json')
    pan_list_path = os.path.join(run_dir, 'pan_list.json')

    if os.path.exists(pan_list_path):
        with open(pan_list_path, 'r', encoding='utf-8') as file_obj:
            pan_list = json.load(file_obj)
        parts = []
        for index, pan in enumerate(pan_list):
            name = pan.get('_record_name', '') or pan.get('name', '') or f'命主{index + 1}'
            parts.append(f'【命主{index + 1}】{name}\n{_build_bazi_text(pan)}')
        all_text = '\n'.join(parts)
        user_msg = f'以下为多份命盘数据：\n{all_text}\n\n用户的问题：{question}'
        return [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_msg}]

    if os.path.exists(pan_path):
        with open(pan_path, 'r', encoding='utf-8') as file_obj:
            result = json.load(file_obj)
        user_msg = f'{_build_bazi_text(result)}\n用户的问题：{question}'
        return [{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_msg}]

    history = []
    try:
        with open(os.path.join(run_dir, 'history.json'), 'r', encoding='utf-8') as file_obj:
            history = json.load(file_obj)
    except OSError:
        pass
    messages = [{'role': 'system', 'content': system_prompt}]
    for item in history[-12:]:
        role = item.get('role')
        content = item.get('content')
        if role in ('user', 'assistant') and content:
            messages.append({'role': role, 'content': content})
    messages.append({'role': 'user', 'content': f'用户当前问题：{question}\n\n只分析当前问题，不涉及其他内容。'})
    return messages


def register_bazi_ask_routes(app, db, services):
    """注册八字 AI 解读端点。"""

    get_run_dir = services['get_run_dir']
    write_run_status = services['write_run_status']
    read_run_status = services['read_run_status']
    logger = services.get('logger')

    def _next_run_id():
        global _bazi_ask_current_run
        with _bazi_ask_lock:
            _bazi_ask_current_run += 1
            return f"bz_{_bazi_ask_current_run}"

    def _load_records(record_ids):
        from bazi_engine import paipan as bazi_paipan

        results = []
        records = BaziRecord.query.filter(
            BaziRecord.id.in_(record_ids),
            BaziRecord.user_id == (current_user.id if current_user.is_authenticated else -1),
        ).all()
        for record in records:
            try:
                params = json.loads(record.params_json) if record.params_json else {}
                birth_time = record.birth_time or params.get('birthTime', '')
                cal_type = record.cal_type or params.get('calType', '公历')
                gender = record.gender or params.get('gender', '男')
                address = record.birth_addr or params.get('birthAddr', '')
                longitude = float(params.get('birthLng', 0) or 0)
                result = bazi_paipan(
                    record.name,
                    gender,
                    birth_time,
                    cal_type,
                    address,
                    longitude=longitude if longitude else None,
                )
                if result and result.get('success'):
                    result['_record_id'] = record.id
                    result['_record_name'] = record.name
                    results.append(result)
            except Exception:
                continue
        return results

    def _build_request_pan(data):
        pan_data = data.get('pan_data')
        record_ids = data.get('record_ids', [])
        birth = data.get('birth', '')
        year = data.get('year')
        month = data.get('month')
        day = data.get('day')
        hour = data.get('hour')

        if record_ids and isinstance(record_ids, list):
            records = _load_records(record_ids)
            return (records[0] if records else None), records

        if pan_data and isinstance(pan_data, dict) and pan_data.get('success'):
            return pan_data, []

        if birth or all([year, month, day, hour]):
            from bazi_engine import paipan as bazi_paipan

            name = data.get('name', '')
            gender = data.get('gender', '')
            cal_type = data.get('cal_type', 'solar')
            birth_addr = data.get('birth_addr', '')
            birth_lng = data.get('birth_lng', 0)
            if birth:
                result = bazi_paipan(
                    name,
                    gender,
                    birth,
                    cal_type,
                    birth_addr,
                    longitude=birth_lng if birth_lng else None,
                )
            else:
                birth_str = f"{int(year)}-{int(month):02d}-{int(day):02d} {int(hour)}:00"
                result = bazi_paipan(name, gender, birth_str, cal_type, birth_addr)
            return result, []

        return None, []

    def _bazi_ask_task(run_id):
        try:
            run_dir = get_run_dir(run_id)
            with open(os.path.join(run_dir, 'question.txt'), 'r', encoding='utf-8') as file_obj:
                question = file_obj.read().strip()

            write_run_status(run_id, {'phase': 'analyzing', 'message': 'AI解盘中...', 'progress': 30, 'run_id': run_id})

            api_key = os.environ.get('SILICONFLOW_API_KEY', '')
            base_url = os.environ.get('SILICONFLOW_BASE_URL', 'https://api.siliconflow.cn/v1')
            model = os.environ.get('DEEPSEEK_MODEL_NORMAL', 'deepseek-ai/DeepSeek-V3')
            if not api_key:
                write_run_status(run_id, {'phase': 'error', 'message': '未配置AI API Key', 'progress': 0, 'run_id': run_id})
                return
            if OpenAI is None:
                write_run_status(run_id, {'phase': 'error', 'message': 'OpenAI SDK 未安装', 'progress': 0, 'run_id': run_id})
                return

            system_prompt = '你是精通八字命理的资深命理师。根据用户的问题和命盘数据，给出专业、有深度、个性化的命理分析。结合八字四柱、五行生克、十神关系来论证观点，给出建设性建议。语言自然流畅，像命理师在面对面交流。'
            messages = _build_bazi_messages(run_dir, question, system_prompt)

            write_run_status(run_id, {'phase': 'streaming', 'message': '生成解答中...', 'progress': 50, 'run_id': run_id})
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.6,
                max_tokens=2048,
                stream=True,
            )

            full_text = ''
            with open(os.path.join(run_dir, 'stream.txt'), 'w', encoding='utf-8') as stream_file:
                for chunk in response:
                    if chunk.choices and chunk.choices[0].delta.content:
                        text = chunk.choices[0].delta.content
                        full_text += text
                        stream_file.write(text)
                        stream_file.flush()

            with open(os.path.join(run_dir, 'result.md'), 'w', encoding='utf-8') as result_file:
                result_file.write(full_text)
            write_run_status(run_id, {'phase': 'done', 'message': '解答完成', 'progress': 100, 'run_id': run_id})

            try:
                with app.app_context():
                    record_id_path = os.path.join(run_dir, 'record_id.txt')
                    if os.path.exists(record_id_path):
                        with open(record_id_path, 'r', encoding='utf-8') as file_obj:
                            record_id = int(file_obj.read().strip())
                        record = db.session.get(Record, record_id)
                        if record:
                            record.result_html = full_text
                            db.session.commit()
            except Exception as exc:
                if logger:
                    logger.warning(f'[bazi] 更新Record结果失败: {exc}')
        except Exception as exc:
            write_run_status(run_id, {'phase': 'error', 'message': f'运行出错: {str(exc)[:200]}', 'progress': 0, 'run_id': run_id})

    @app.route('/api/bazi/ask/stream', methods=['GET', 'POST'])
    @csrf.exempt
    def api_bazi_ask_stream():
        """八字排盘 SSE 流式 AI 解读。POST=新建任务+流式；GET=读取已有任务。"""
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            question = (data.get('question') or '').strip()

            birth = data.get('birth', '')
            year = data.get('year')
            month = data.get('month')
            day = data.get('day')
            hour = data.get('hour')
            pan_data = data.get('pan_data')
            record_ids = data.get('record_ids', [])
            if not birth and not all([year, month, day, hour]) and not pan_data and not record_ids:
                if not data.get('history', []):
                    return jsonify({'error': '请提供出生时间或选择档案'}), 400

            try:
                result, results_list = _build_request_pan(data)
            except Exception as exc:
                return jsonify({'error': f'排盘失败: {str(exc)}'}), 500
            if result and not result.get('success'):
                return jsonify({'error': result.get('error', '排盘失败')}), 500

            run_id = _next_run_id()
            run_dir = get_run_dir(run_id)
            if result:
                with open(os.path.join(run_dir, 'pan.json'), 'w', encoding='utf-8') as file_obj:
                    json.dump(result, file_obj, ensure_ascii=False)
            if results_list:
                with open(os.path.join(run_dir, 'pan_list.json'), 'w', encoding='utf-8') as file_obj:
                    json.dump(results_list, file_obj, ensure_ascii=False)
            with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as file_obj:
                file_obj.write(question)
            if not result:
                with open(os.path.join(run_dir, 'history.json'), 'w', encoding='utf-8') as file_obj:
                    json.dump(data.get('history', []), file_obj, ensure_ascii=False)

            if current_user.is_authenticated:
                try:
                    record = Record(question=question[:200], user_id=current_user.id, app_type='bazi', result_html='')
                    db.session.add(record)
                    db.session.commit()
                    with open(os.path.join(run_dir, 'record_id.txt'), 'w', encoding='utf-8') as file_obj:
                        file_obj.write(str(record.id))
                except Exception as exc:
                    if logger:
                        logger.warning(f'[bazi] 创建Record失败: {exc}')

            write_run_status(run_id, {'phase': 'calculating', 'message': '排盘中...', 'progress': 10, 'run_id': run_id})
            thread = threading.Thread(target=_bazi_ask_task, args=(run_id,), daemon=True)
            thread.start()
        else:
            run_id = request.args.get('run_id', default='')
            if not run_id:
                return jsonify({'error': '无效的 run_id'}), 400

        run_dir = get_run_dir(run_id)
        stream_file_path = os.path.join(run_dir, 'stream.txt')

        def generate():
            last_position = 0
            while True:
                status = read_run_status(run_id)
                phase = status.get('phase', 'idle')
                try:
                    if os.path.exists(stream_file_path):
                        with open(stream_file_path, 'r', encoding='utf-8') as stream_file:
                            stream_file.seek(last_position)
                            content = stream_file.read()
                            if content:
                                last_position = stream_file.tell()
                                yield f"data: {json.dumps({'type': 'delta', 'content': content}, ensure_ascii=False)}\n\n"
                except OSError:
                    pass

                if phase == 'done':
                    yield f"data: {json.dumps({'type': 'done'}, ensure_ascii=False)}\n\n"
                    break
                if phase == 'error':
                    yield f"data: {json.dumps({'type': 'error', 'message': status.get('message', '未知错误')}, ensure_ascii=False)}\n\n"
                    break
                time.sleep(0.3)

        return Response(generate(), mimetype='text/event-stream', headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no',
            'Connection': 'keep-alive',
        })
