"""八字排盘、历法转换、流运与合盘 API。"""

import json
import os
import subprocess
from datetime import datetime

from flask import jsonify, request, session
from flask_login import current_user, login_required

from extensions import csrf


def _calc_pair_relations(g1, z1, g2, z2):
    """计算两组干支之间的关系。"""
    gan_he_pairs = [
        ('甲', '己', '土'), ('乙', '庚', '金'), ('丙', '辛', '水'), ('丁', '壬', '木'), ('戊', '癸', '火')
    ]
    gan_chong_pairs = [('甲', '庚'), ('乙', '辛'), ('丙', '壬'), ('丁', '癸')]
    zhi_liu_he_pairs = [
        ('子', '丑', '土'), ('寅', '亥', '木'), ('卯', '戌', '火'), ('辰', '酉', '金'), ('巳', '申', '水'), ('午', '未', '火')
    ]
    zhi_chong_pairs = [('子', '午'), ('丑', '未'), ('寅', '申'), ('卯', '酉'), ('辰', '戌'), ('巳', '亥')]
    zhi_hai_pairs = [('子', '未'), ('丑', '午'), ('寅', '巳'), ('卯', '辰'), ('申', '亥'), ('酉', '戌')]

    rels = []
    for a, b, name in gan_he_pairs:
        if (g1 == a and g2 == b) or (g1 == b and g2 == a):
            rels.append({'type': 'gan_he', 'desc': f'{g1}{g2}合化{name}', 'label': '合', 'positive': True})
    for a, b in gan_chong_pairs:
        if (g1 == a and g2 == b) or (g1 == b and g2 == a):
            rels.append({'type': 'gan_chong', 'desc': f'{g1}{g2}冲', 'label': '冲', 'positive': False})

    for a, b, name in zhi_liu_he_pairs:
        if (z1 == a and z2 == b) or (z1 == b and z2 == a):
            rels.append({'type': 'zhi_liu_he', 'desc': f'{z1}{z2}合化{name}', 'label': '合', 'positive': True})
    for a, b in zhi_chong_pairs:
        if (z1 == a and z2 == b) or (z1 == b and z2 == a):
            rels.append({'type': 'zhi_liu_chong', 'desc': f'{z1}{z2}冲', 'label': '冲', 'positive': False})
    for a, b in zhi_hai_pairs:
        if (z1 == a and z2 == b) or (z1 == b and z2 == a):
            rels.append({'type': 'zhi_liu_hai', 'desc': f'{z1}{z2}害', 'label': '害', 'positive': False})

    return rels


def _calc_wuxing_complement(wx1, wx2):
    """五行互补分析。"""
    result = {}
    for wx in ['金', '木', '水', '火', '土']:
        c1 = wx1.get(wx, 0)
        c2 = wx2.get(wx, 0)
        total = c1 + c2
        if (c1 == 0 and c2 > 0) or (c2 == 0 and c1 > 0):
            status = '互补'
        elif c1 == 0 and c2 == 0:
            status = '双缺'
        elif c1 >= 2 and c2 >= 2:
            status = '偏旺'
        else:
            status = '均衡'
        result[wx] = {'person1': c1, 'person2': c2, 'total': total, 'status': status}
    return result


def _calc_day_gan_relation(g1, g2):
    """日主天干关系。"""
    gan_he_pairs = [('甲', '己', '土'), ('乙', '庚', '金'), ('丙', '辛', '水'), ('丁', '壬', '木'), ('戊', '癸', '火')]
    gan_chong_pairs = [('甲', '庚'), ('乙', '辛'), ('丙', '壬'), ('丁', '癸')]
    gan_wuxing = {'甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水'}

    rels = []
    for a, b, name in gan_he_pairs:
        if (g1 == a and g2 == b) or (g1 == b and g2 == a):
            rels.append(f'日主{g1}{g2}合化{name}')
    for a, b in gan_chong_pairs:
        if (g1 == a and g2 == b) or (g1 == b and g2 == a):
            rels.append(f'日主{g1}{g2}冲')
    wx1 = gan_wuxing.get(g1, '')
    wx2 = gan_wuxing.get(g2, '')
    if wx1 and wx2 and wx1 != wx2:
        rels.append(f'{wx1}命与{wx2}命')
    return rels


def _calc_hepan_score(pillar_compare, wx_complement, day_relation):
    """合盘综合评分。"""
    score = 60
    for pc in pillar_compare:
        for r in pc.get('relations', []):
            score += 4 if r.get('positive') else -5
    for info in wx_complement.values():
        if info['status'] == '互补':
            score += 3
        elif info['status'] == '双缺':
            score -= 4
        elif info['status'] == '偏旺':
            score -= 2
    for r in day_relation:
        if '合' in r:
            score += 5
        elif '冲' in r:
            score -= 5
    return max(20, min(98, score))


def register_bazi_routes(app, db, deps):
    """注册八字非流式端点。"""

    Record = deps['Record']
    BaziRecord = deps['BaziRecord']
    lunar_to_solar = deps['lunar_to_solar']
    sync_bazi_record_to_profile = deps['sync_bazi_record_to_profile']
    paipan_dir = deps['paipan_dir']
    paipan_sh = deps['paipan_sh']
    has_lunar = deps.get('has_lunar', False)
    logger = deps.get('logger')

    @app.route('/api/paipan', methods=['POST'])
    @login_required
    @csrf.exempt
    def api_paipan():
        """旧版八字排盘接口：调用 paipan_auto.sh。"""
        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        gender = data.get('gender', '男')
        cal_type = data.get('calType', '公历')
        birth_time = (data.get('birthTime') or '').strip()
        birth_addr = (data.get('birthAddr') or '').strip()
        addr_info = data.get('addrInfo', {})

        if not name:
            return jsonify({'success': False, 'error': '缺少姓名'}), 400
        if not birth_time or len(birth_time) < 8:
            return jsonify({'success': False, 'error': '缺少出生时间'}), 400

        birth_time, cal_type = lunar_to_solar(birth_time, cal_type)

        cmd = ['bash', paipan_sh, name, gender, cal_type, birth_time]
        if birth_addr:
            cmd.append(birth_addr)
        if isinstance(addr_info, dict) and addr_info.get('full'):
            cmd.append(addr_info['full'])

        if logger:
            logger.info(f"执行: {' '.join(cmd)}")

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90, cwd=paipan_dir)
            success = 'SUCCESS' in (result.stdout or '')
            stdout_text = result.stdout.strip() if result.stdout else ''
            stderr_text = result.stderr.strip() if result.stderr else ''

            if logger:
                logger.info(f"{'成功' if success else '失败'}: {name}")

            rec = Record(
                question=f"{name} | {gender} | {birth_time} | {birth_addr or '-'}",
                result_html=stdout_text if success else '',
                app_type='paipan',
                user_id=current_user.id,
            )
            db.session.add(rec)
            db.session.commit()

            return jsonify({
                'success': success,
                'message': stdout_text,
                'error': stderr_text if not success else None,
                'name': name,
                'record_id': rec.id,
            })
        except subprocess.TimeoutExpired:
            return jsonify({'success': False, 'error': '执行超时（90秒）', 'name': name})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e), 'name': name})

    @app.route('/api/bazi/paipan', methods=['POST'])
    @csrf.exempt
    def api_bazi_paipan():
        """八字排盘免费版 API。"""
        from bazi_engine import paipan as bazi_paipan

        data = request.get_json(silent=True) or {}
        name = (data.get('name') or '').strip()
        gender = data.get('gender', '男')
        cal_type = data.get('calType', '公历')
        birth_time = (data.get('birthTime') or '').strip()
        birth_addr = (data.get('birthAddr') or '').strip()
        birth_lng = float(data.get('birthLng', 0) or 0)
        is_dst = bool(data.get('isDst', False))
        night_zi_mode = data.get('nightZiMode', '夜子时不换日')
        sizi_pillars = data.get('siziPillars', None)
        use_solar_time = bool(data.get('useSolarTime', True))
        is_leap_month = bool(data.get('isLeapMonth', False))

        if cal_type != '四柱' and (not birth_time or len(birth_time) < 8):
            return jsonify({'success': False, 'error': '请输入出生日期'})

        try:
            result = bazi_paipan(
                name, gender, birth_time, cal_type, birth_addr,
                is_dst=is_dst, night_zi_mode=night_zi_mode,
                sizi_pillars=sizi_pillars,
                use_solar_time=use_solar_time,
                is_leap_month=is_leap_month,
                longitude=birth_lng if birth_lng else None,
            )

            is_replay = bool(data.get('_replay'))
            if result.get('success') and not is_replay:
                fp = result.get('four_pillars', {})
                pillars_str = ''.join(
                    fp.get(p, {}).get('gan', '?') + fp.get(p, {}).get('zhi', '?')
                    for p in ['year', 'month', 'day', 'hour']
                )
                params_data = {k: v for k, v in data.items() if k not in ('name', '_replay')}

                if current_user.is_authenticated:
                    bazi_rec = BaziRecord(
                        user_id=current_user.id,
                        name=name or '未命名',
                        gender=gender,
                        birth_time=birth_time,
                        cal_type=cal_type,
                        birth_addr=birth_addr,
                        pillars=pillars_str,
                        record_type='paipan',
                        starred=False,
                        category='全部',
                        params_json=json.dumps(params_data, ensure_ascii=False),
                    )
                    db.session.add(bazi_rec)
                    db.session.flush()
                    sync_bazi_record_to_profile(db, current_user.id, bazi_rec, params_data, result)
                    db.session.commit()
                else:
                    history = session.get('bazi_history', [])
                    history.insert(0, {
                        'name': name or '未命名',
                        'gender': gender,
                        'birth_time': birth_time,
                        'cal_type': cal_type,
                        'birth_addr': birth_addr,
                        'pillars': pillars_str,
                        'created_at': datetime.now().isoformat(),
                        'params': params_data,
                        'starred': False,
                        'category': '全部',
                        'type': 'paipan',
                    })
                    session['bazi_history'] = history[:50]
                    session.modified = True

            return jsonify(result)
        except Exception as e:
            if logger:
                logger.error(f"八字排盘异常: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/bazi/lunar-month-data', methods=['POST'])
    @csrf.exempt
    def api_bazi_lunar_month_data():
        """返回指定农历年的月份列表（含闰月）和日名映射。"""
        data = request.get_json(silent=True) or {}
        year = data.get('year', 2024)

        month_names = {1: '正月', 2: '二月', 3: '三月', 4: '四月', 5: '五月', 6: '六月',
                       7: '七月', 8: '八月', 9: '九月', 10: '十月', 11: '冬月', 12: '腊月'}
        day_name_map = {1: '初一', 2: '初二', 3: '初三', 4: '初四', 5: '初五',
                        6: '初六', 7: '初七', 8: '初八', 9: '初九', 10: '初十',
                        11: '十一', 12: '十二', 13: '十三', 14: '十四', 15: '十五',
                        16: '十六', 17: '十七', 18: '十八', 19: '十九', 20: '二十',
                        21: '廿一', 22: '廿二', 23: '廿三', 24: '廿四', 25: '廿五',
                        26: '廿六', 27: '廿七', 28: '廿八', 29: '廿九', 30: '三十'}

        try:
            from lunarcalendar import DateNotExist, Lunar
            leap_month_num = None
            for m in range(1, 13):
                try:
                    Lunar(year, m, 1, isleap=True)
                    leap_month_num = m
                except (ValueError, DateNotExist):
                    pass

            months_info = []
            for m in range(1, 13):
                try:
                    Lunar(year, m, 30, isleap=False)
                    day_count = 30
                except (ValueError, DateNotExist):
                    day_count = 29
                months_info.append({'value': m, 'label': month_names.get(m, str(m)), 'isLeap': False, 'dayCount': day_count})
                if m == leap_month_num:
                    try:
                        Lunar(year, m, 30, isleap=True)
                        leap_day_count = 30
                    except (ValueError, DateNotExist):
                        leap_day_count = 29
                    months_info.append({'value': m, 'label': f'闰{month_names.get(m, str(m))}', 'isLeap': True, 'dayCount': leap_day_count})

            return jsonify({'success': True, 'months': months_info, 'dayNames': day_name_map})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/bazi/solar-to-lunar', methods=['POST'])
    @csrf.exempt
    def api_bazi_solar_to_lunar():
        data = request.get_json(silent=True) or {}
        year, month, day = data.get('year'), data.get('month'), data.get('day')
        if not year or not month or not day:
            return jsonify({'success': False, 'error': '缺少参数(year/month/day)'})
        try:
            year, month, day = int(year), int(month), int(day)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '日期格式错误'})
        try:
            from lunar_python import Solar
            lunar = Solar.fromYmd(year, month, day).getLunar()
            lunar_month = lunar.getMonth()
            return jsonify({'success': True, 'year': lunar.getYear(), 'month': abs(lunar_month), 'day': lunar.getDay(), 'isLeap': lunar_month < 0})
        except Exception:
            pass
        if not has_lunar:
            return jsonify({'success': False, 'error': '农历库不可用'})
        try:
            from lunarcalendar import Converter, Solar as LSolar
            l = Converter.Solar2Lunar(LSolar(year, month, day))
            return jsonify({'success': True, 'year': l.year, 'month': l.month, 'day': l.day, 'isLeap': getattr(l, 'isleap', False)})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/bazi/lunar-to-solar', methods=['POST'])
    @csrf.exempt
    def api_bazi_lunar_to_solar():
        data = request.get_json(silent=True) or {}
        year, month, day = data.get('year'), data.get('month'), data.get('day')
        is_leap = bool(data.get('isLeap', False))
        if not year or not month or not day:
            return jsonify({'success': False, 'error': '缺少参数(year/month/day)'})
        try:
            year, month, day = int(year), int(month), int(day)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '日期格式错误'})
        try:
            from lunar_python import Lunar as _Lunar
            solar = _Lunar.fromYmd(year, -month if is_leap else month, day).getSolar()
            return jsonify({'success': True, 'year': solar.getYear(), 'month': solar.getMonth(), 'day': solar.getDay()})
        except Exception:
            pass
        if not has_lunar:
            return jsonify({'success': False, 'error': '农历库不可用'})
        try:
            from lunarcalendar import Converter, Lunar
            solar = Converter.Lunar2Solar(Lunar(year, month, day, isleap=is_leap))
            return jsonify({'success': True, 'year': solar.year, 'month': solar.month, 'day': solar.day})
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/bazi/liu-yue', methods=['POST'])
    @csrf.exempt
    def api_bazi_liu_yue():
        """八字流月查询 API。"""
        from bazi_engine import calc_liu_yue
        data = request.get_json(silent=True) or {}
        year = data.get('year')
        day_gan = (data.get('dayGan') or '').strip()
        if not year or not day_gan:
            return jsonify({'success': False, 'error': '缺少参数(year/dayGan)'})
        try:
            year = int(year)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '年份格式错误'})
        if day_gan not in '甲乙丙丁戊己庚辛壬癸':
            return jsonify({'success': False, 'error': '日主天干无效'})
        try:
            liu_yue = calc_liu_yue(year, day_gan)
            current_bazi_month = None
            now = datetime.now()
            if year == now.year:
                try:
                    from bazi_engine import JIE_ORDER, JIE_ZHI, MONTH_ZHI, get_jieqi_times
                    jieqi_times = get_jieqi_times(year)
                    candidates = [(jieqi_times.get(jie_name), jie_name) for jie_name in JIE_ORDER if jieqi_times.get(jie_name) and jieqi_times.get(jie_name) <= now]
                    if candidates:
                        candidates.sort(key=lambda x: x[0])
                        _, latest_jie_name = candidates[-1]
                        current_bazi_month = MONTH_ZHI.index(JIE_ZHI[latest_jie_name]) + 1
                except Exception as e2:
                    if logger:
                        logger.error(f"[八字流月] 节气月计算异常: {e2}")
            return jsonify({'success': True, 'liu_yue': liu_yue, 'year': year, 'current_bazi_month': current_bazi_month})
        except Exception as e:
            if logger:
                logger.error(f"[八字流月] 异常: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/bazi/liu-ri', methods=['POST'])
    @csrf.exempt
    def api_bazi_liu_ri():
        """八字流日查询 API。"""
        data = request.get_json(silent=True) or {}
        year = data.get('year')
        bazi_month = data.get('baziMonth')
        month = data.get('month')
        day_gan = (data.get('dayGan') or '').strip()
        if not year or not day_gan:
            return jsonify({'success': False, 'error': '缺少参数(year/dayGan)'})
        if day_gan not in '甲乙丙丁戊己庚辛壬癸':
            return jsonify({'success': False, 'error': '日主天干无效'})
        try:
            year = int(year)
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': '年份格式错误'})
        try:
            if bazi_month:
                from bazi_engine import calc_liu_ri_by_bazi_month
                bazi_month = int(bazi_month)
                if not (1 <= bazi_month <= 12):
                    return jsonify({'success': False, 'error': '八字月序号范围1-12'})
                result = calc_liu_ri_by_bazi_month(year, bazi_month, day_gan)
                result['success'] = True
                return jsonify(result)
            if month:
                from bazi_engine import calc_liu_ri
                month = int(month)
                if not (1 <= month <= 12):
                    return jsonify({'success': False, 'error': '月份范围1-12'})
                return jsonify({'success': True, 'liu_ri': calc_liu_ri(year, month, day_gan), 'year': year, 'month': month})
            return jsonify({'success': False, 'error': '缺少参数(baziMonth 或 month)'})
        except Exception as e:
            if logger:
                logger.error(f"[八字流日] 异常: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/bazi/liu-shi', methods=['POST'])
    @csrf.exempt
    def api_bazi_liu_shi():
        """八字流时查询 API。"""
        from bazi_engine import calc_liu_shi
        data = request.get_json(silent=True) or {}
        day_gan = (data.get('dayGan') or '').strip()
        day_zhu_gan = (data.get('dayZhuGan') or '').strip() or day_gan
        if not day_gan:
            return jsonify({'success': False, 'error': '缺少参数(dayGan)'})
        if day_gan not in '甲乙丙丁戊己庚辛壬癸':
            return jsonify({'success': False, 'error': '当日天干无效'})
        try:
            return jsonify({'success': True, 'liu_shi': calc_liu_shi(day_gan, day_zhu_gan)})
        except Exception as e:
            if logger:
                logger.error(f"[八字流时] 异常: {e}")
            return jsonify({'success': False, 'error': str(e)})

    @app.route('/api/bazi/hepan', methods=['POST'])
    @csrf.exempt
    def api_bazi_hepan():
        """八字合盘 API。"""
        from bazi_engine import paipan as bazi_paipan
        data = request.get_json(silent=True) or {}
        person1 = data.get('person1', {})
        person2 = data.get('person2', {})
        if not person1 or not person2:
            return jsonify({'success': False, 'error': '请提供person1和person2参数'})

        try:
            result1 = bazi_paipan(
                (person1.get('name') or '').strip(), person1.get('gender', '男'),
                (person1.get('birthTime') or '').strip(), person1.get('calType', '公历'),
                (person1.get('birthAddr') or '').strip(),
                is_dst=bool(person1.get('isDst', False)),
                night_zi_mode=person1.get('nightZiMode', '夜子时不换日'),
                sizi_pillars=person1.get('siziPillars'),
                use_solar_time=bool(person1.get('useSolarTime', True)),
                is_leap_month=bool(person1.get('isLeapMonth', False)),
            )
            result2 = bazi_paipan(
                (person2.get('name') or '').strip(), person2.get('gender', '女'),
                (person2.get('birthTime') or '').strip(), person2.get('calType', '公历'),
                (person2.get('birthAddr') or '').strip(),
                is_dst=bool(person2.get('isDst', False)),
                night_zi_mode=person2.get('nightZiMode', '夜子时不换日'),
                sizi_pillars=person2.get('siziPillars'),
                use_solar_time=bool(person2.get('useSolarTime', True)),
                is_leap_month=bool(person2.get('isLeapMonth', False)),
            )
            if not result1.get('success') or not result2.get('success'):
                return jsonify({'success': False, 'error': f"排盘失败: {result1.get('error','') or result2.get('error','')}"})

            fp1 = result1['four_pillars']
            fp2 = result2['four_pillars']
            pillar_compare = []
            for p in ['year', 'month', 'day', 'hour']:
                g1, z1 = fp1[p]['gan'], fp1[p]['zhi']
                g2, z2 = fp2[p]['gan'], fp2[p]['zhi']
                pillar_compare.append({
                    'pillar': p,
                    'label': {'year': '年柱', 'month': '月柱', 'day': '日柱', 'hour': '时柱'}[p],
                    'person1': g1 + z1,
                    'person2': g2 + z2,
                    'relations': _calc_pair_relations(g1, z1, g2, z2),
                })
            wx1 = result1.get('wu_xing', {})
            wx2 = result2.get('wu_xing', {})
            wx_complement = _calc_wuxing_complement(wx1, wx2)
            day_gan1 = fp1['day']['gan']
            day_gan2 = fp2['day']['gan']
            day_relation = _calc_day_gan_relation(day_gan1, day_gan2)
            score = _calc_hepan_score(pillar_compare, wx_complement, day_relation)

            is_replay = bool(data.get('_replay'))
            if not is_replay:
                name1 = (person1.get('name') or '').strip() or '甲方'
                name2 = (person2.get('name') or '').strip() or '乙方'
                gender1 = person1.get('gender', '男')
                gender2 = person2.get('gender', '女')
                hepan_data = {'person1': {'name': name1, 'gender': gender1}, 'person2': {'name': name2, 'gender': gender2}, 'score': score}
                if current_user.is_authenticated:
                    bazi_rec = BaziRecord(
                        user_id=current_user.id,
                        name=f"{name1} & {name2}",
                        gender=f"{gender1}/{gender2}",
                        birth_time='',
                        cal_type='合盘',
                        birth_addr='',
                        pillars='',
                        record_type='hepan',
                        starred=False,
                        category='全部',
                        params_json=json.dumps(data, ensure_ascii=False),
                        hepan_json=json.dumps(hepan_data, ensure_ascii=False),
                    )
                    db.session.add(bazi_rec)
                    db.session.commit()
                else:
                    history = session.get('bazi_history', [])
                    history.insert(0, {
                        'name': f"{name1} & {name2}",
                        'gender': f"{gender1}/{gender2}",
                        'birth_time': '',
                        'cal_type': '合盘',
                        'birth_addr': '',
                        'pillars': '',
                        'created_at': datetime.now().isoformat(),
                        'params': data,
                        'starred': False,
                        'category': '全部',
                        'type': 'hepan',
                        'hepan_data': hepan_data,
                    })
                    session['bazi_history'] = history[:50]
                    session.modified = True

            return jsonify({
                'success': True,
                'person1': {
                    'name': result1.get('name', ''),
                    'gender': result1.get('gender', ''),
                    'birth': result1.get('birth_solar', ''),
                    'four_pillars': fp1,
                    'wu_xing': wx1,
                    'lack_wuxing': result1.get('lack_wuxing', []),
                    'day_master': day_gan1,
                },
                'person2': {
                    'name': result2.get('name', ''),
                    'gender': result2.get('gender', ''),
                    'birth': result2.get('birth_solar', ''),
                    'four_pillars': fp2,
                    'wu_xing': wx2,
                    'lack_wuxing': result2.get('lack_wuxing', []),
                    'day_master': day_gan2,
                },
                'pillar_compare': pillar_compare,
                'wx_complement': wx_complement,
                'day_relation': day_relation,
                'score': score,
            })
        except Exception as e:
            if logger:
                logger.error(f"[八字合盘] 异常: {e}")
            return jsonify({'success': False, 'error': str(e)})
