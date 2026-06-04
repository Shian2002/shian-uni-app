import json
import os
import threading
from datetime import datetime

from flask import Response, jsonify, request, stream_with_context
from flask_login import current_user, login_required

from extensions import csrf
from models import Record


LIUYAO_SYSTEM_PROMPT = """你是一位精通六爻纳甲（六爻占卜）的资深命理专家，擅长根据六爻卦象分析问题。
请根据用户提供的六爻排盘数据和问题，给出专业的六爻分析解读。

你的回答应该包括以下结构（markdown格式）：
1. **卦象解读**：解读本卦、变卦的含义和象征
2. **用神分析**：根据问题确定用神，分析用神的旺衰休囚
3. **世应关系**：分析世爻和应爻的位置关系与生克
4. **动爻分析**：如果有动爻，分析动爻的提示意义
5. **建议指导**：给出针对性的建议

要求：语言通俗易懂，用 markdown 组织内容，结合具体卦象分析，字数 600-1200 字。"""


MEIHUA_SYSTEM_PROMPT = """你是一位精通梅花易数的资深命理专家，擅长根据卦象分析问题。
请根据用户提供的梅花易数排盘数据，给出专业的分析解读。

回答结构：
1. **卦象解读**：解读本卦、变卦、互卦的含义
2. **体用分析**：体卦和用卦的生克关系
3. **动爻分析**：动爻的提示意义
4. **建议指导**：针对性的建议

要求：通俗易懂，语言平和，结合具体卦象分析。"""


_liuyao_ask_current_run = 0
_liuyao_ask_lock = threading.Lock()
_meihua_ask_current_run = 0
_meihua_ask_lock = threading.Lock()


def _error_stream(message):
    def generate():
        yield f"event: error\ndata: {json.dumps({'message': message})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


def _parse_meihua_time(data):
    time_str = data.get('time', '')
    year = month = day = hour = None
    if time_str:
        try:
            dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            year, month, day, hour = dt.year, dt.month, dt.day, ((dt.hour + 1) // 2) % 12 + 1
            if hour == 0:
                hour = 12
        except Exception:
            pass
    return year, month, day, hour


def _build_liuyao_ask_prompt(question, liuyao):
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
        yao_name = yao.get('name', f'第{i + 1}爻')
        liuqin = yao.get('liuqin', '')
        liushen = yao.get('liushen', '')
        naja = yao.get('naja', '')
        yaotype = yao.get('yao_type', '')
        moving = '⚡动爻' if yao.get('is_moving') else ''
        prompt += f'- {yao_name}：{naja} {liuqin} {liushen} {yaotype}{moving}\n'

    bian_details = liuyao.get('bian_details', [])
    moving_exists = any(y.get('is_moving') for y in details)
    if bian_details and moving_exists:
        prompt += '\n**变卦各爻**：\n'
        for i, yao in enumerate(bian_details):
            yao_name = yao.get('name', f'第{i + 1}爻')
            prompt += f'- {yao_name}：{yao.get("naja", "")} {yao.get("liuqin", "")}\n'

    liuqin_list = liuyao.get('六亲', [])
    if liuqin_list:
        prompt += f'\n**六亲**：{" ".join(liuqin_list)}\n'

    liushen_list = liuyao.get('六神', [])
    if liushen_list:
        prompt += f'**六神**：{" ".join(liushen_list)}\n'

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


def _build_meihua_ask_prompt(question, meihua):
    ben = meihua.get('benGua', {})
    bian = meihua.get('bianGua', {})
    hu = meihua.get('huGua', {})
    ty = meihua.get('tiYong', {})

    prompt = f'''## 梅花易数排盘数据

**起卦方式**：{meihua.get('methodLabel', '时间起卦')}
**起卦时间**：{meihua.get('paipanTime', '')}

**本卦**：{ben.get('name', '')}（上{ben.get('upper', {}).get('nature', '')} {ben.get('upper', {}).get('name', '')}·{ben.get('upper', {}).get('wuxing', '')} → 下{ben.get('lower', {}).get('nature', '')} {ben.get('lower', {}).get('name', '')}·{ben.get('lower', {}).get('wuxing', '')}）
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


def register_metaphysics_ask_routes(app, db, services):
    liuyao_paipan = services['liuyao_paipan']
    meihua_paipan = services['meihua_paipan']
    deepseek_available = services['deepseek_available']
    get_reading_stream = services['get_reading_stream']
    use_points = services['use_points']
    get_run_dir = services['get_run_dir']
    write_run_status = services['write_run_status']
    logger = services['logger']

    def liuyao_ask_task(run_id):
        try:
            run_dir = get_run_dir(run_id)
            liuyao = None
            try:
                with open(os.path.join(run_dir, 'liuyao.json'), 'r', encoding='utf-8') as f:
                    liuyao = json.load(f)
            except Exception:
                pass
            if not liuyao:
                write_run_status(run_id, {'phase': 'error', 'message': '排盘数据读取失败', 'progress': 0, 'run_id': run_id})
                return

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

            write_run_status(run_id, {'phase': 'analyzing', 'message': 'AI解卦中...', 'progress': 30, 'run_id': run_id})
            prompt = _build_liuyao_ask_prompt(question, liuyao)

            from deepseek_service import get_qimen_reading as get_liuyao_reading

            write_run_status(run_id, {'phase': 'streaming', 'message': '生成解答中...', 'progress': 50, 'run_id': run_id})
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

    def meihua_ask_task(run_id):
        try:
            run_dir = get_run_dir(run_id)
            meihua = None
            try:
                with open(os.path.join(run_dir, 'meihua.json'), 'r', encoding='utf-8') as f:
                    meihua = json.load(f)
            except Exception:
                pass
            if not meihua:
                write_run_status(run_id, {'phase': 'error', 'message': '排盘数据读取失败', 'progress': 0, 'run_id': run_id})
                return

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

            write_run_status(run_id, {'phase': 'analyzing', 'message': 'AI解卦中...', 'progress': 30, 'run_id': run_id})
            prompt = _build_meihua_ask_prompt(question, meihua)

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

    @app.route('/api/liuyao/ask', methods=['POST'])
    @csrf.exempt
    def api_liuyao_ask():
        global _liuyao_ask_current_run
        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()
        result = liuyao_paipan(mode=data.get('mode', 'auto'), tosses=data.get('tosses'), question=question)
        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        with _liuyao_ask_lock:
            _liuyao_ask_current_run += 1
            run_id = _liuyao_ask_current_run

        run_dir = get_run_dir(run_id)
        with open(os.path.join(run_dir, 'liuyao.json'), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
        with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
            f.write(question)
        with open(os.path.join(run_dir, 'deep_mode.txt'), 'w') as f:
            f.write('1' if data.get('deep_analysis', False) else '0')

        write_run_status(run_id, {'phase': 'calculating', 'message': '起卦中...', 'progress': 10, 'run_id': run_id})
        threading.Thread(target=liuyao_ask_task, args=(run_id,), daemon=True).start()
        return jsonify({'status': 'started', 'run_id': run_id, 'gua': result.get('本卦', ''), 'bian': result.get('变卦', '')})

    @app.route('/api/liuyao/ask/stream', methods=['POST'])
    @login_required
    def api_liuyao_ask_stream():
        if not deepseek_available():
            return _error_stream('AI 服务未配置')

        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()
        history = data.get('history') or []
        is_followup = bool(history)

        if not question:
            return _error_stream('请输入您的问题')

        cost = 1 if is_followup else 5
        user_id = current_user.id
        spend = use_points(user_id, 'liuyao_reading', cost, '六爻 AI ' + ('追问' if is_followup else '解读'))
        if not spend.get('ok'):
            return _error_stream(f'积分不足（需要 {cost} 积分）')

        def generate():
            yield f"event: progress\ndata: {json.dumps({'stage': 'connecting'})}\n\n"
            try:
                if is_followup:
                    messages = [{"role": "system", "content": LIUYAO_SYSTEM_PROMPT}]
                    for h in history:
                        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                    messages.append({"role": "user", "content": question})
                else:
                    result = liuyao_paipan(mode=data.get('mode', 'auto'), tosses=data.get('tosses'), question=question)
                    if 'error' in result:
                        yield f"event: error\ndata: {json.dumps({'message': result['error']})}\n\n"
                        return
                    yield f"event: progress\ndata: {json.dumps({'stage': 'analyzing'})}\n\n"
                    paipan_keys = {k: result[k] for k in [
                        '本卦', '变卦', 'palace_name', 'palace_element', 'day_ganzhi', 'month_ganzhi', 'method',
                        'upper_nature', 'upper_trigram', 'lower_nature', 'lower_trigram',
                        'bian_upper_nature', 'bian_upper_trigram', 'bian_lower_nature', 'bian_lower_trigram',
                        '世爻', '应爻', 'details', 'bian_details', '六亲', '六神'
                    ] if k in result}
                    yield f"event: paipan\ndata: {json.dumps(paipan_keys)}\n\n"
                    messages = [
                        {"role": "system", "content": LIUYAO_SYSTEM_PROMPT},
                        {"role": "user", "content": _build_liuyao_ask_prompt(question, result)}
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
                        rec = Record(user_id=user_id, app_type='liuyao', question=question, result_html=full_text)
                        db.session.add(rec)
                        db.session.commit()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"六爻 AI 解读异常: {e}")
                yield f"event: error\ndata: {json.dumps({'message': 'AI 服务暂时不可用'})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})

    @app.route('/api/meihua/ask', methods=['POST'])
    @csrf.exempt
    def api_meihua_ask():
        global _meihua_ask_current_run
        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()
        year, month, day, hour = _parse_meihua_time(data)
        result = meihua_paipan(
            method=data.get('method', 'time'),
            num1=data.get('num1'),
            num2=data.get('num2'),
            words=data.get('words'),
            year=year,
            month=month,
            day=day,
            hour=hour,
        )
        if 'error' in result:
            return jsonify({'error': result['error']}), 500

        with _meihua_ask_lock:
            _meihua_ask_current_run += 1
            run_id = _meihua_ask_current_run

        run_dir = get_run_dir(run_id)
        with open(os.path.join(run_dir, 'meihua.json'), 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False)
        with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
            f.write(question)
        with open(os.path.join(run_dir, 'deep_mode.txt'), 'w') as f:
            f.write('1' if data.get('deep_analysis', False) else '0')

        write_run_status(run_id, {'phase': 'calculating', 'message': '起卦中...', 'progress': 10, 'run_id': run_id})
        threading.Thread(target=meihua_ask_task, args=(run_id,), daemon=True).start()
        return jsonify({'status': 'started', 'run_id': run_id, 'gua': result.get('benGua', {}).get('name', '')})

    @app.route('/api/meihua/ask/stream', methods=['POST'])
    @login_required
    def api_meihua_ask_stream():
        if not deepseek_available():
            return _error_stream('AI 服务未配置')

        data = request.get_json(silent=True) or {}
        question = (data.get('question') or '').strip()
        history = data.get('history') or []
        is_followup = bool(history)

        if not question:
            return _error_stream('请输入您的问题')

        cost = 1 if is_followup else 5
        user_id = current_user.id
        spend = use_points(user_id, 'meihua_reading', cost, '梅花易数 AI ' + ('追问' if is_followup else '解读'))
        if not spend.get('ok'):
            return _error_stream(f'积分不足（需要 {cost} 积分）')

        def generate():
            yield f"event: progress\ndata: {json.dumps({'stage': 'connecting'})}\n\n"
            try:
                if is_followup:
                    messages = [{"role": "system", "content": MEIHUA_SYSTEM_PROMPT}]
                    for h in history:
                        messages.append({"role": h.get("role", "user"), "content": h.get("content", "")})
                    messages.append({"role": "user", "content": question})
                else:
                    year, month, day, hour = _parse_meihua_time(data)
                    result = meihua_paipan(
                        method=data.get('method', 'time'),
                        num1=data.get('num1'),
                        num2=data.get('num2'),
                        words=data.get('words'),
                        year=year,
                        month=month,
                        day=day,
                        hour=hour,
                    )
                    if 'error' in result:
                        yield f"event: error\ndata: {json.dumps({'message': result['error']})}\n\n"
                        return
                    yield f"event: progress\ndata: {json.dumps({'stage': 'analyzing'})}\n\n"
                    messages = [
                        {"role": "system", "content": MEIHUA_SYSTEM_PROMPT},
                        {"role": "user", "content": _build_meihua_ask_prompt(question, result)}
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
                        rec = Record(user_id=user_id, app_type='meihua', question=question, result_html=full_text)
                        db.session.add(rec)
                        db.session.commit()
                    except Exception:
                        pass
            except Exception as e:
                logger.error(f"梅花 AI 解读异常: {e}")
                yield f"event: error\ndata: {json.dumps({'message': 'AI 服务暂时不可用'})}\n\n"

        return Response(stream_with_context(generate()), mimetype='text/event-stream',
                        headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})
