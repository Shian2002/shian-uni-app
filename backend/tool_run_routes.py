"""通用工具运行接口。"""

import json
import os
import subprocess
import threading
from datetime import datetime

from flask import jsonify, request
from flask_login import current_user, login_required

from extensions import csrf
from models import Record


VALID_APP_TYPES = {'qimen', 'paipan', 'liuyao', 'meihua', 'ziwei', 'zeji', 'huangli', 'taluo'}


def _append_if(parts, label, value):
    if value:
        parts.append(f'{label}:{value}')


def _build_question(app_type, data, meihua_paipan):
    question_parts = []
    name = (data.get('name') or app_type).strip()
    question_parts.append(f'[{app_type}] {name}')

    if app_type == 'liuyao':
        method = data.get('method', 'coin')
        question_parts.append(f'起卦方式:{method}')
        _append_if(question_parts, '铜钱', data.get('coinResult'))
        if data.get('num1'):
            question_parts.append(f'数字:{data["num1"]}/{data.get("num2", "")}')
        _append_if(question_parts, '时间', data.get('time'))
    elif app_type == 'meihua':
        method = data.get('method', 'time')
        question_parts.append(f'起卦方式:{method}')
        if data.get('num1'):
            question_parts.append(f'数字:{data["num1"]}/{data.get("num2", "")}')
        _append_if(question_parts, '字', data.get('char'))
        _append_if(question_parts, '时间', data.get('time'))
        try:
            mh_result = meihua_paipan(
                method=method,
                num1=data.get('num1'),
                num2=data.get('num2'),
                words=data.get('char') or data.get('words', ''),
                year=data.get('year'),
                month=data.get('month'),
                day=data.get('day'),
                hour=data.get('hour'),
            )
            if 'error' not in mh_result:
                data['_mh_paipan'] = mh_result
                question_parts.append(f'本卦:{mh_result.get("benGua", {}).get("name", "")}')
                question_parts.append(f'变卦:{mh_result.get("bianGua", {}).get("name", "")}')
                if mh_result.get('tiYong'):
                    ti_yong = mh_result['tiYong']
                    question_parts.append(f'体:{ti_yong.get("tiWuxing", "")}({ti_yong.get("tiPosition", "")})')
                    question_parts.append(f'用:{ti_yong.get("yongWuxing", "")}({ti_yong.get("yongPosition", "")})')
                    question_parts.append(f'体用:{ti_yong.get("tiYongRel", "")}')
        except Exception:
            pass
    elif app_type == 'ziwei':
        question_parts.append(f'性别:{data.get("gender", "男")}')
        question_parts.append(f'出生:{data.get("birthTime", "")}')
        _append_if(question_parts, '出生地', data.get('birthAddr'))
    elif app_type == 'zeji':
        question_parts.append(f'事项:{data.get("zejiType", "")}')
        question_parts.append(f'日期:{data.get("startDate", "")}~{data.get("endDate", "")}')
    elif app_type == 'taluo':
        question_parts.append(f'牌阵:{data.get("spread_name", "three")}')

    user_question = data.get('question') or data.get('time') or ''
    _append_if(question_parts, '问题', user_question)
    return ' | '.join(question_parts)


def _build_ai_prompt(app_type, data):
    """构建 AI 解读提示词。"""
    prompts = {
        'liuyao': f"请根据六爻排盘参数进行解卦。起卦方式:{data.get('method','coin')}，"
                  f"问题:{data.get('question','综合解卦')}。"
                  f"请按传统六爻规则排盘并给出卦宫、世应、动爻、六亲、六神分析，"
                  f"最后给出简明白话解读和行动建议。"
                  f"注意：内容仅为民俗文化参考，不构成任何决策建议。",
        'meihua': f"请根据梅花易数参数进行起卦解读。起卦方式:{data.get('method','time')}，"
                  f"问题:{data.get('question','综合解读')}。"
                  + (f"\n排盘结果：本卦={data.get('_mh_paipan',{}).get('benGua',{}).get('name','')}, "
                     f"互卦={data.get('_mh_paipan',{}).get('huGua',{}).get('name','')}, "
                     f"变卦={data.get('_mh_paipan',{}).get('bianGua',{}).get('name','')}, "
                     f"动爻={data.get('_mh_paipan',{}).get('dongYao','')}, "
                     f"体用={data.get('_mh_paipan',{}).get('tiYong',{}).get('tiYongRel','')}, "
                     f"吉凶={data.get('_mh_paipan',{}).get('tiYong',{}).get('tiYongJiXiong','')}, "
                     f"断语={data.get('_mh_paipan',{}).get('tiYong',{}).get('verdict','')}。"
                     if data.get('_mh_paipan') else "")
                  + f"请基于以上排盘结果，给出本卦、互卦、变卦、体用生克的专业分析，"
                  f"最后给出简明白话解读和行动建议。"
                  f"注意：内容仅为民俗文化参考，不构成任何决策建议。",
        'ziwei': f"请根据紫微斗数参数进行命盘解读。性别:{data.get('gender','男')}，"
                 f"出生时间:{data.get('birthTime','')}，出生地:{data.get('birthAddr','')}。"
                 f"请按紫微斗数规则排盘并给出十二宫、主星、四化、流年大运分析，"
                 f"最后给出简明白话解读。"
                 f"注意：内容仅为民俗文化参考，不构成任何决策建议。",
        'zeji': f"请根据择吉参数进行分析。事项:{data.get('zejiType','')}，"
                f"日期范围:{data.get('startDate','')}~{data.get('endDate','')}。"
                f"请给出宜忌吉日、吉时、冲煞提醒，以及择吉建议。"
                f"注意：内容仅为民俗文化参考，不构成任何决策建议。",
        'taluo': f"请进行塔罗牌解读。牌阵:{data.get('spread','three')}，"
                 f"问题:{data.get('question','综合解读')}。"
                 f"请随机抽取对应数量的塔罗牌，给出正/逆位、牌意解读和综合建议。"
                 f"注意：内容仅为民俗文化参考，不构成任何决策建议。",
    }
    return prompts.get(app_type, '请进行综合解读。注意：内容仅为民俗文化参考。')


def _generate_ai_reading(app_type, question, data=None):
    """生成模板解读。"""
    now = datetime.now().strftime('%Y年%m月%d日 %H:%M')
    mh = (data or {}).get('_mh_paipan', {})
    templates = {
        'liuyao': f"""═══ 六爻排盘解读 ═══
起卦时间：{now}
问事：{question}

【排盘参数已接收，AI解读生成中...】
当前版本为模板解读，完整排盘功能开发中。

── 卦象分析 ──
根据起卦参数，本卦与变卦已生成。
世爻代表问卦者自身，应爻代表所问之事。
动爻为变化之关键，需重点关注。

── 综合解读 ──
当前为系统内测阶段，完整AI解卦功能即将上线。
建议您使用「天机问策」获取完整的AI解读。

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",
        'meihua': f"""═══ 梅花易数解读 ═══
起卦时间：{now}
问事：{question}

── 排盘结果 ──
本卦：{mh.get('benGua',{}).get('name','') if mh else '待排'}
  上卦：{mh.get('benGua',{}).get('upper',{}).get('name','')}({mh.get('benGua',{}).get('upper',{}).get('wuxing','')}) {mh.get('benGua',{}).get('upper',{}).get('nature','')}
  下卦：{mh.get('benGua',{}).get('lower',{}).get('name','')}({mh.get('benGua',{}).get('lower',{}).get('wuxing','')}) {mh.get('benGua',{}).get('lower',{}).get('nature','')}
  动爻：第{mh.get('dongYao','')}爻
互卦：{mh.get('huGua',{}).get('name','') if mh else ''}
变卦：{mh.get('bianGua',{}).get('name','') if mh else ''}
干支：{mh.get('ganzhi','') if mh else ''}

── 体用分析 ──
体卦：{mh.get('tiYong',{}).get('tiGua','')}({mh.get('tiYong',{}).get('tiPosition','')}) {mh.get('tiYong',{}).get('tiWuxing','')} {mh.get('tiYong',{}).get('tiWangshuai','')}
用卦：{mh.get('tiYong',{}).get('yongGua','')}({mh.get('tiYong',{}).get('yongPosition','')}) {mh.get('tiYong',{}).get('yongWuxing','')} {mh.get('tiYong',{}).get('yongWangshuai','')}
体用关系：体{mh.get('tiYong',{}).get('tiWuxing','')} {mh.get('tiYong',{}).get('tiYongRel','')} 用{mh.get('tiYong',{}).get('yongWuxing','')}
吉凶：{mh.get('tiYong',{}).get('tiYongJiXiong','')}
断语：{mh.get('tiYong',{}).get('verdict','')}

── 综合解读 ──
体卦代表自身，用卦代表所问之事。
体用生克关系决定事物发展趋势。
{mh.get('tiYong',{}).get('verdict','') if mh else ''}

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",
        'ziwei': f"""═══ 紫微斗数命盘解读 ═══
排盘时间：{now}
问事：{question}

【排盘参数已接收，AI解读生成中...】
当前版本为模板解读，完整排盘功能开发中。

── 命盘分析 ──
根据出生信息，十二宫位与主星已排布完成。
命宫为命盘核心，决定基本性格与人生走向。
四化飞星为流年变化的关键。

── 综合解读 ──
当前为系统内测阶段，完整紫微斗数AI解读功能即将上线。

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",
        'zeji': f"""═══ 择吉分析 ═══
分析时间：{now}
事项：{question}

【择吉参数已接收，分析生成中...】
当前版本为模板分析，完整择吉功能开发中。

── 吉日推荐 ──
根据择吉事项与日期范围，筛选出以下吉日：
（完整黄历数据对接后，将显示详细宜忌信息）

── 综合建议 ──
当前为系统内测阶段，完整择吉功能即将上线。
您可使用「黄历万年历」查询每日宜忌。

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",
        'taluo': f"""═══ 塔罗牌解读 ═══
抽牌时间：{now}
牌阵：{data.get('spread_name', 'three') if data else '三张牌'}
问事：{question}

【牌阵已生成，AI解读中...】
当前版本为模板解读，完整塔罗功能开发中。

── 牌意解读 ──
根据牌阵类型，已抽取对应数量的塔罗牌。
每张牌的正逆位与位置含义不同，需综合分析。

── 综合解读 ──
当前为系统内测阶段，完整塔罗牌AI解读功能即将上线。

⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。""",
    }
    return templates.get(app_type, '解读生成中...当前为模板解读，完整功能即将上线。\n\n⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。')


def register_tool_run_routes(app, db, services):
    """注册通用工具运行接口。"""

    base_dir = services['base_dir']
    meihua_paipan = services['meihua_paipan']
    reserve_run_id = services['reserve_run_id']
    set_current_process = services['set_current_process']
    is_current_run = services['is_current_run']
    cleanup_old_runs = services['cleanup_old_runs']
    write_run_status = services['write_run_status']
    get_run_dir = services['get_run_dir']
    read_run_result = services['read_run_result']

    @app.route('/api/tool-run', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_tool_run():
        """接收工具参数，执行 shell 自动化或生成模板解读。"""
        data = request.get_json(silent=True) or {}
        app_type = (data.get('appType') or '').strip()

        if app_type not in VALID_APP_TYPES:
            return jsonify({'error': f'不支持的工具类型: {app_type}'}), 400

        question = _build_question(app_type, data, meihua_paipan)
        script_path = os.path.join(base_dir, f'{app_type}_auto.sh')

        if os.path.exists(script_path):
            run_id = reserve_run_id()
            cleanup_old_runs(run_id)
            write_run_status(run_id, {'phase': 'starting', 'message': '准备中...', 'progress': 0, 'run_id': run_id})

            run_dir = get_run_dir(run_id)
            with open(os.path.join(run_dir, 'params.json'), 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
            with open(os.path.join(run_dir, 'question.txt'), 'w', encoding='utf-8') as f:
                f.write(question)

            record = Record(question=question, user_id=current_user.id, app_type=app_type, run_id=run_id)
            db.session.add(record)
            db.session.commit()
            record_id = record.id

            env = os.environ.copy()
            env['TOOL_PARAMS_FILE'] = os.path.join(run_dir, 'params.json')
            env['QIMEN_QUESTION_FILE'] = os.path.join(run_dir, 'question.txt')
            env['QIMEN_RUN_DIR'] = run_dir
            env['QIMEN_RUN_ID'] = str(run_id)

            def run_tool():
                try:
                    stdout_log = open(os.path.join(run_dir, 'stdout.log'), 'w')
                    stderr_log = open(os.path.join(run_dir, 'stderr.log'), 'w')
                    proc = subprocess.Popen(['bash', script_path], env=env, stdout=stdout_log, stderr=stderr_log)
                    set_current_process(proc)
                    proc.wait()
                    stdout_log.close()
                    stderr_log.close()

                    if not is_current_run(run_id):
                        return

                    result = read_run_result(run_id)
                    if result:
                        write_run_status(run_id, {'phase': 'done', 'message': '解读完成', 'progress': 100, 'run_id': run_id})
                        with app.app_context():
                            rec = db.session.get(Record, record_id)
                            if rec:
                                rec.result_html = result
                                db.session.commit()
                    else:
                        write_run_status(run_id, {'phase': 'error', 'message': '自动化完成但未获取到结果', 'progress': 0})
                except Exception as e:
                    write_run_status(run_id, {'phase': 'error', 'message': str(e), 'progress': 0})

            threading.Thread(target=run_tool, daemon=True).start()
            return jsonify({'status': 'started', 'run_id': run_id, 'record_id': record_id})

        _build_ai_prompt(app_type, data)
        result_text = _generate_ai_reading(app_type, question, data)
        record = Record(question=question, user_id=current_user.id, app_type=app_type, result_html=result_text)
        db.session.add(record)
        db.session.commit()

        return jsonify({
            'success': True,
            'result': result_text,
            'message': result_text,
            'record_id': record.id,
        })
