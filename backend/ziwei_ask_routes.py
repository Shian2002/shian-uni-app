"""紫微斗数 AI 流式解读 API。"""

import json
import os
import threading
import time

from flask import Response, jsonify, request

from extensions import csrf

try:
    from openai import OpenAI
except ImportError:  # pragma: no cover - 生产依赖缺失时由接口返回错误
    OpenAI = None


_ziwei_ask_current_run = 0
_ziwei_ask_lock = threading.Lock()


def _summarize_palaces(pan_data):
    palaces = []
    for palace in (pan_data.get('twelve_palaces') or pan_data.get('palaces') or []):
        name = palace.get('name', '')
        all_stars = []
        for star in (palace.get('major_stars') or []):
            star_name = star.get('name', '') if isinstance(star, dict) else str(star)
            if star_name:
                brightness = star.get('brightness', '') if isinstance(star, dict) else ''
                mutagen = star.get('mutagen', '') if isinstance(star, dict) else ''
                label = star_name
                if brightness:
                    label += '(' + brightness + ')'
                if mutagen:
                    label += '[' + mutagen + ']'
                all_stars.append(label + '(主星)')
        for star in (palace.get('minor_stars') or []):
            star_name = star.get('name', '') if isinstance(star, dict) else str(star)
            if star_name:
                brightness = star.get('brightness', '') if isinstance(star, dict) else ''
                mutagen = star.get('mutagen', '') if isinstance(star, dict) else ''
                label = star_name
                if brightness:
                    label += '(' + brightness + ')'
                if mutagen:
                    label += '[' + mutagen + ']'
                all_stars.append(label)
        for star in (palace.get('adjective_stars') or []):
            star_name = star.get('name', '') if isinstance(star, dict) else str(star)
            if star_name:
                all_stars.append(star_name)
        for star in (palace.get('stars') or []):
            star_name = star.get('name', '') if isinstance(star, dict) else str(star)
            if star_name:
                brightness = star.get('brightness', '') if isinstance(star, dict) else ''
                label = star_name
                if brightness:
                    label += '(' + brightness + ')'
                all_stars.append(label)
        palaces.append(f"{name}: {' '.join(all_stars) if all_stars else '(空宫)'}")
    return '\n'.join(palaces)


def _build_ziwei_messages(question, pan_data, analysis_type):
    basic_info = pan_data.get('basic_info', {})
    palace_summary = _summarize_palaces(pan_data)

    core_info = ''
    core_palace = pan_data.get('core_palace', {})
    if core_palace:
        core_info = f"\n命宫详情: {json.dumps(core_palace, ensure_ascii=False)}"

    decadal_info = ''
    decadal = pan_data.get('decadal_overview', [])
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

    return [
        {'role': 'system', 'content': system_prompt},
        {'role': 'user', 'content': user_msg},
    ]


def register_ziwei_ask_routes(app, services):
    """注册紫微斗数 AI 解读端点。"""

    has_ziwei = services['has_ziwei']
    engine = services['ziwei_engine']
    get_run_dir = services['get_run_dir']
    write_run_status = services['write_run_status']
    read_run_status = services['read_run_status']

    def _next_run_id():
        global _ziwei_ask_current_run
        with _ziwei_ask_lock:
            _ziwei_ask_current_run += 1
            return f"zw_{_ziwei_ask_current_run}"

    def _ziwei_ask_task(run_id):
        try:
            run_dir = get_run_dir(run_id)
            with open(os.path.join(run_dir, 'pan.json'), 'r', encoding='utf-8') as file_obj:
                pan_data = json.load(file_obj)
            with open(os.path.join(run_dir, 'question.txt'), 'r', encoding='utf-8') as file_obj:
                question = file_obj.read().strip()
            try:
                with open(os.path.join(run_dir, 'analysis_type.txt'), 'r', encoding='utf-8') as file_obj:
                    analysis_type = file_obj.read().strip()
            except OSError:
                analysis_type = ''

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

            write_run_status(run_id, {'phase': 'streaming', 'message': '生成解答中...', 'progress': 50, 'run_id': run_id})
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=_build_ziwei_messages(question, pan_data, analysis_type),
                temperature=0.8,
                max_tokens=3072,
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
        except Exception as exc:
            write_run_status(run_id, {'phase': 'error', 'message': f'运行出错: {str(exc)[:200]}', 'progress': 0, 'run_id': run_id})

    @app.route('/api/ziwei/ask/stream', methods=['GET', 'POST'])
    @csrf.exempt
    def api_ziwei_ask_stream():
        """紫微斗数 SSE 流式 AI 解读。POST=新建任务+流式；GET=读取已有任务。"""
        if request.method == 'POST':
            data = request.get_json(silent=True) or {}
            question = (data.get('question') or '').strip() or '请全面分析我的八字命局'

            for key in ['year', 'month', 'day', 'hour']:
                if key not in data or data[key] is None:
                    return jsonify({'error': f'缺少必填参数: {key}'}), 400

            if not has_ziwei:
                return jsonify({'error': '紫微斗数引擎未安装(iztro-py)'}), 503

            try:
                pan_data = engine.calculate(
                    year=int(data['year']),
                    month=int(data['month']),
                    day=int(data['day']),
                    hour=int(data['hour']),
                    minute=int(data.get('minute', 0) or 0),
                    gender=data.get('gender', '男'),
                    date_type=data.get('date_type', 'solar'),
                )
            except Exception as exc:
                return jsonify({'error': f'排盘失败: {str(exc)}'}), 500

            run_id = _next_run_id()
            run_dir = get_run_dir(run_id)
            with open(os.path.join(run_dir, 'pan.json'), 'w', encoding='utf-8') as file_obj:
                json.dump(pan_data, file_obj, ensure_ascii=False)
            with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as file_obj:
                file_obj.write(question)
            with open(os.path.join(run_dir, 'analysis_type.txt'), 'w', encoding='utf-8') as file_obj:
                file_obj.write(data.get('analysis_type', ''))

            write_run_status(run_id, {'phase': 'calculating', 'message': '排盘中...', 'progress': 10, 'run_id': run_id})
            thread = threading.Thread(target=_ziwei_ask_task, args=(run_id,), daemon=True)
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
