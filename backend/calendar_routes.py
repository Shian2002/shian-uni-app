"""黄历与择吉 API。"""

import calendar
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timedelta

from flask import jsonify, request

from extensions import csrf


def _parse_zeji_date(value, field_name):
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except (TypeError, ValueError):
        raise ValueError(f'{field_name}格式错误，需YYYY-MM-DD')


def register_calendar_routes(app, deps):
    """注册黄历万年历与择吉端点。"""

    compute_huangli = deps['compute_huangli']
    compute_huangli_local = deps['compute_huangli_local']
    score_zeji_day = deps['score_zeji_day']
    month_cache = deps['huangli_month_cache']
    month_ttl = deps['huangli_month_ttl']

    @app.route('/api/huangli')
    def api_huangli():
        """黄历万年历：返回指定日期的农历、干支、五行、建除、冲煞等。"""
        date_str = request.args.get('date', '')
        if not date_str:
            date_str = datetime.now().strftime('%Y-%m-%d')
        try:
            parts = date_str.split('-')
            year, month, day = int(parts[0]), int(parts[1]), int(parts[2])
        except (ValueError, IndexError):
            return jsonify({'error': '日期格式错误，需YYYY-MM-DD'}), 400

        return jsonify(compute_huangli(year, month, day))

    @app.route('/api/huangli/month')
    def api_huangli_month():
        """黄历万年历：返回整月日历数据。"""
        year = request.args.get('year', type=int)
        month = request.args.get('month', type=int)
        if not year or not month:
            now = datetime.now()
            year, month = now.year, now.month

        month_key = f'{year}-{month:02d}'
        now_ts = time.time()
        cached = month_cache.get(month_key)
        if cached and cached[1] > now_ts:
            return jsonify(cached[0])

        _, days_in_month = calendar.monthrange(year, month)
        days_dict = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {executor.submit(compute_huangli, year, month, d): d for d in range(1, days_in_month + 1)}
            for future in as_completed(futures):
                d = futures[future]
                try:
                    days_dict[d] = future.result(timeout=10)
                except Exception:
                    days_dict[d] = {'solarDate': f'{year}-{month:02d}-{d:02d}', 'source': 'error'}

        days = [days_dict[d] for d in range(1, days_in_month + 1)]
        result = {
            'year': year,
            'month': month,
            'days': days,
            'disclaimer': '以上内容仅为民俗文化参考，不构成任何决策建议',
        }
        month_cache[month_key] = (result, now_ts + month_ttl)
        return jsonify(result)

    @app.route('/api/zeji', methods=['POST'])
    @csrf.exempt
    def api_zeji():
        """择吉工具：基于本地黄历字段给出日期候选，不依赖登录。"""
        data = request.get_json(silent=True) or {}
        zeji_type = (data.get('zejiType') or data.get('type') or '').strip() or '择吉'
        start_date = (data.get('startDate') or '').strip()
        end_date = (data.get('endDate') or start_date).strip()
        addr = (data.get('addr') or '').strip()

        if not start_date:
            return jsonify({'success': False, 'error': '请选择开始日期'}), 400

        try:
            start_dt = _parse_zeji_date(start_date, '开始日期')
            end_dt = _parse_zeji_date(end_date, '结束日期')
        except ValueError as e:
            return jsonify({'success': False, 'error': str(e)}), 400

        if end_dt < start_dt:
            return jsonify({'success': False, 'error': '结束日期不能早于开始日期'}), 400

        if (end_dt - start_dt).days > 60:
            return jsonify({'success': False, 'error': '择吉日期范围最多支持60天'}), 400

        candidates = []
        cursor = start_dt
        while cursor <= end_dt:
            h = compute_huangli_local(cursor.year, cursor.month, cursor.day)
            score, reasons, warnings = score_zeji_day(zeji_type, h)
            candidates.append({
                'date': cursor.strftime('%Y-%m-%d'),
                'score': score,
                'lunar': h.get('lunarDate', ''),
                'ganZhiDay': h.get('ganZhiDay', ''),
                'jianChu': h.get('jianChu', ''),
                'zhiShen': h.get('zhiShen', ''),
                'chong': h.get('chong', ''),
                'sha': h.get('sha', ''),
                'reasons': reasons,
                'warnings': warnings,
            })
            cursor += timedelta(days=1)

        candidates.sort(key=lambda item: (-item['score'], item['date']))
        best = candidates[:3]
        lines = [
            '═══ 择吉分析 ═══',
            f'事项：{zeji_type}',
            f'日期范围：{start_date} ~ {end_date}',
        ]
        if addr:
            lines.append(f'地点：{addr}')
        lines.append('')
        lines.append('推荐日期：')
        for idx, item in enumerate(best, 1):
            reason_text = '；'.join(item['reasons'] or ['综合黄历信息较平稳'])
            warning_text = '；'.join(item['warnings'])
            line = (
                f'{idx}. {item["date"]}（评分{item["score"]}）'
                f' {item["ganZhiDay"]}日 · {item["jianChu"]}日 · 值神{item["zhiShen"]}'
                f' · {item["chong"]}{item["sha"]}。{reason_text}'
            )
            if warning_text:
                line += f'；提醒：{warning_text}'
            lines.append(line)
        lines.extend([
            '',
            '建议：优先选择评分靠前且时间安排从容的日期，具体吉时需结合当事人八字、方位和实际行程进一步细排。',
            '⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议。',
        ])

        return jsonify({
            'success': True,
            'zejiType': zeji_type,
            'startDate': start_date,
            'endDate': end_date,
            'addr': addr,
            'bestDays': best,
            'days': candidates,
            'result': '\n'.join(lines),
            'message': '\n'.join(lines),
        })
