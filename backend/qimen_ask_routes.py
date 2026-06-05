import json
import os
import threading
from datetime import datetime

from flask import Response, jsonify, request, stream_with_context
from flask_login import current_user, login_required

from extensions import csrf
from models import Record


QIMEN_SYSTEM_PROMPT = """你是一位精通奇门遁甲的资深命理专家，擅长根据奇门遁甲盘面分析问题。
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


_qimen_ask_current_run = 0
_qimen_ask_lock = threading.Lock()


def _error_stream(message):
    def generate():
        yield f"event: error\ndata: {json.dumps({'message': message}, ensure_ascii=False)}\n\n"

    return Response(generate(), mimetype='text/event-stream')


def _build_qimen_ask_prompt(question, qimen):
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
    for palace in palaces:
        gong = palace.get('gong', palace.get('position', '?'))
        men = palace.get('men', palace.get('gate', ''))
        xing = palace.get('xing', '')
        if isinstance(xing, list):
            xing = '/'.join(xing)
        shen = palace.get('shen', palace.get('deity', ''))
        tian = palace.get('tianGan', '')
        if isinstance(tian, list):
            tian = '/'.join(tian)
        di = palace.get('diGan', '')
        if isinstance(di, list):
            di = '/'.join(di)
        prompt += f'- {gong}宫：门={men} 星={xing} 神={shen} 天={tian} 地={di}\n'

    prompt += f'''

## 用户问题

{question}

## 分析要求

请根据以上奇门排盘数据，对用户的问题进行专业分析。'''
    return prompt


def register_qimen_ask_routes(app, db, services):
    qimen_paipan = services['qimen_paipan']
    deepseek_available = services['deepseek_available']
    get_reading_stream = services['get_reading_stream']
    get_run_dir = services['get_run_dir']
    write_run_status = services['write_run_status']
    read_run_status = services['read_run_status']
    logger = services['logger']

    def _parse_qimen_params(data):
        now = datetime.now()
        year = int(data.get('year', now.year))
        month = int(data.get('month', now.month))
        day = int(data.get('day', now.day))
        hour = int(data.get('hour', now.hour))
        minute = int(data.get('minute', 0))
        # 与免费排盘保持一致：1=拆补法，2=置闰法。
        pan_type = int(data.get('panType', 1))
        return year, month, day, hour, minute, pan_type

    def _qimen_ask_task(run_id):
        try:
            run_dir = get_run_dir(run_id)
            with open(os.path.join(run_dir, 'qimen.json'), 'r', encoding='utf-8') as f:
                qimen = json.load(f)
            question = ''
            try:
                with open(os.path.join(run_dir, 'question.txt'), 'r', encoding='utf-8') as f:
                    question = f.read().strip()
            except Exception:
                pass
            is_deep = False
            try:
                with open(os.path.join(run_dir, 'deep_mode.txt'), 'r') as f:
                    is_deep = f.read().strip() == '1'
            except Exception:
                pass

            write_run_status(run_id, {'phase': 'analyzing', 'message': 'AI解盘中...', 'progress': 30, 'run_id': run_id})
            prompt = _build_qimen_ask_prompt(question, qimen)

            from deepseek_service import get_qimen_reading

            write_run_status(run_id, {'phase': 'streaming', 'message': '生成解答中...', 'progress': 50, 'run_id': run_id})
            result = get_qimen_reading(prompt, question, is_deep=is_deep, system_prompt=QIMEN_SYSTEM_PROMPT)
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

            write_run_status(run_id, {'phase': 'done', 'message': '解盘完成', 'progress': 100, 'run_id': run_id})
        except Exception as e:
            write_run_status(run_id, {'phase': 'error', 'message': f'处理出错: {str(e)}', 'progress': 0, 'run_id': run_id})

    @app.route('/api/qimen/ask', methods=['POST'])
    @csrf.exempt
    def api_qimen_ask():
        global _qimen_ask_current_run
        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()
        if not question:
            return jsonify({'error': '请输入您的问题'}), 400

        try:
            result = qimen_paipan(*_parse_qimen_params(data))
        except Exception as e:
            return jsonify({'error': f'起局失败: {str(e)}'}), 500
        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        with _qimen_ask_lock:
            _qimen_ask_current_run += 1
            run_id = _qimen_ask_current_run

        run_dir = get_run_dir(run_id)
        with open(os.path.join(run_dir, 'qimen.json'), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
        with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
            f.write(question)
        with open(os.path.join(run_dir, 'deep_mode.txt'), 'w') as f:
            f.write('1' if data.get('deep_analysis', False) else '0')

        write_run_status(run_id, {'phase': 'calculating', 'message': '起局中...', 'progress': 10, 'run_id': run_id})
        threading.Thread(target=_qimen_ask_task, args=(run_id,), daemon=True).start()
        return jsonify({'status': 'started', 'run_id': run_id})

    @app.route('/api/qimen/ask/status')
    def api_qimen_ask_status():
        run_id = request.args.get('run_id', type=int, default=0)
        if run_id <= 0:
            return jsonify({'phase': 'idle', 'message': '等待开始', 'progress': 0})

        status = read_run_status(run_id)
        status['run_id'] = run_id
        if status.get('phase') == 'done':
            run_dir = get_run_dir(run_id)
            result = None
            for filename in ['result.md', 'result.txt']:
                try:
                    with open(os.path.join(run_dir, filename), 'r', encoding='utf-8') as f:
                        result = f.read().strip()
                    if result:
                        break
                except Exception:
                    continue
            if result:
                status['result'] = result
            try:
                with open(os.path.join(run_dir, 'reasoning.md'), 'r', encoding='utf-8') as f:
                    reasoning = f.read().strip()
                if reasoning:
                    status['reasoning'] = reasoning
            except Exception:
                pass
        return jsonify(status)

    @app.route('/api/qimen/ask/stream', methods=['POST'])
    @login_required
    def api_qimen_ask_stream():
        if not deepseek_available():
            return _error_stream('AI 服务未配置')

        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()
        if not question:
            return _error_stream('请输入您的问题')

        try:
            result = qimen_paipan(*_parse_qimen_params(data))
        except Exception as e:
            return _error_stream(f'起局失败: {str(e)}')
        if 'error' in result:
            return _error_stream(result['error'])

        is_followup = bool(data.get('history') or [])

        def generate():
            yield "event: progress\ndata: {\"stage\": \"connecting\"}\n\n"
            try:
                if is_followup:
                    messages = [{"role": "system", "content": QIMEN_SYSTEM_PROMPT}]
                    for h in data.get('history') or []:
                        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                    messages.append({"role": "user", "content": question})
                else:
                    messages = [
                        {"role": "system", "content": QIMEN_SYSTEM_PROMPT},
                        {"role": "user", "content": _build_qimen_ask_prompt(question, result)}
                    ]

                yield "event: progress\ndata: {\"stage\": \"analyzing\"}\n\n"
                yield "event: progress\ndata: {\"stage\": \"generating\"}\n\n"
                full_text = ""
                for chunk, error in get_reading_stream(messages):
                    if error:
                        yield f"event: error\ndata: {json.dumps({'message': error}, ensure_ascii=False)}\n\n"
                        return
                    if chunk:
                        full_text += chunk
                        yield f"event: chunk\ndata: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                yield f"event: done\ndata: {json.dumps({'length': len(full_text)}, ensure_ascii=False)}\n\n"

                if not is_followup:
                    try:
                        rec = Record(user_id=current_user.id, app_type='qimen', question=question, result_html=full_text)
                        db.session.add(rec)
                        db.session.commit()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"奇门 AI 解读异常: {e}")
                yield "event: error\ndata: {\"message\": \"AI 服务暂时不可用\"}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
