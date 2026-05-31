import calendar
from datetime import datetime, timedelta

from iztro_py import by_solar, by_lunar

SHICHEN_NAMES = ['子时','丑时','寅时','卯时','辰时','巳时','午时','未时','申时','酉时','戌时','亥时']
SHICHEN_RANGES = ['23:00~01:00','01:00~03:00','03:00~05:00','05:00~07:00','07:00~09:00','09:00~11:00','11:00~13:00','13:00~15:00','15:00~17:00','17:00~19:00','19:00~21:00','21:00~23:00']
PALACE_NAME_MAP = {
    'soulPalace':'命宫','parentsPalace':'父母宫','felicityPalace':'福德宫','estatePalace':'田宅宫',
    'careerPalace':'官禄宫','friendsPalace':'交友宫','movePalace':'迁移宫','wealthPalace':'财帛宫',
    'childrenPalace':'子女宫','spousePalace':'夫妻宫','siblingPalace':'兄弟宫','healthPalace':'疾厄宫',
    'originalPalace':'命宫',
}
HEAVENLY_NAMES = {'jiaHeavenly':'甲','yiHeavenly':'乙','bingHeavenly':'丙','dingHeavenly':'丁','wuHeavenly':'戊','jiHeavenly':'己','gengHeavenly':'庚','xinHeavenly':'辛','renHeavenly':'壬','guiHeavenly':'癸'}
EARTHLY_NAMES = {'ziEarthly':'子','chouEarthly':'丑','yinEarthly':'寅','maoEarthly':'卯','chenEarthly':'辰','siEarthly':'巳','wuEarthly':'午','weiEarthly':'未','shenEarthly':'申','youEarthly':'酉','xuEarthly':'戌','haiEarthly':'亥'}
MUTAGEN_NAMES = {None:None,'lu':'禄','quan':'权','ke':'科','ji':'忌'}
STAR_BRIGHTNESS = {None:None}

def _to_ganzhi(hs, es):
    return (HEAVENLY_NAMES.get(hs, hs or '') or '') + (EARTHLY_NAMES.get(es, es or '') or '')

def _hour_to_time_index(hour, minute):
    if hour == 23: return 0
    if hour == 0: return 0
    return (hour + 1) // 2

def _format_dt(dt):
    return f"{dt.year:04d}-{dt.month:02d}-{dt.day:02d} {dt.hour:02d}:{dt.minute:02d}"

def _calc_true_solar_display(year, month, day, hour, minute, longitude):
    y = int(year)
    m = int(month)
    d = min(int(day), calendar.monthrange(y, m)[1])
    base = datetime(y, m, d, int(hour), int(minute or 0))
    if longitude is None or longitude == "":
        return base, None, 120.0, False
    lng = float(longitude)
    corrected = base + timedelta(minutes=(lng - 120.0) * 4.0)
    return corrected, lng, lng, True

def _normalize_stars(stars, star_type):
    result = []
    for s in (stars or []):
        result.append({
            'name': s.get('name',''),
            'type': star_type,
            'scope': s.get('scope','origin'),
            'brightness': s.get('brightness') or '',
            'mutagen': MUTAGEN_NAMES.get(s.get('mutagen')),
        })
    return result

class ZiweiEngine:
    def calculate(self, year, month, day, hour, minute=0, gender='男', date_type='solar', timezone='Asia/Shanghai', longitude=None):
        true_dt, display_lng, used_lng, has_true_solar = _calc_true_solar_display(year, month, day, hour, minute, longitude)
        ti = _hour_to_time_index(true_dt.hour, true_dt.minute)
        g = '男' if gender in ('male','M','m','1','男') else '女'
        if date_type == 'lunar':
            astro = by_lunar(str(year) + '-' + str(month) + '-' + str(day), ti, g, fix_leap=True)
        else:
            astro = by_solar(str(true_dt.year) + '-' + str(true_dt.month) + '-' + str(true_dt.day), ti, g, fix_leap=True)
        d = astro.model_dump()
        raw = astro.to_iztro_dict()
        raw_palaces_list = raw.get('palaces', [])
        twelve = []
        for p in d.get('palaces', []):
            palace_index = p.get('index', 0)
            raw_p = raw_palaces_list[palace_index] if palace_index < len(raw_palaces_list) else {}
            palace_name = raw_p.get('name', PALACE_NAME_MAP.get(p.get('name',''), p.get('name','')))
            major_stars = _normalize_stars(raw_p.get('majorStars', p.get('major_stars',[])), 'major')
            minor_stars = _normalize_stars(raw_p.get('minorStars', p.get('minor_stars',[])), 'minor')
            adj_stars = _normalize_stars(raw_p.get('adjectiveStars', p.get('adjective_stars',[])), 'adjective')
            dec = p.get('decadal', {})
            ages = p.get('ages', [])
            hs = p.get('heavenly_stem','')
            es = p.get('earthly_branch','')
            twelve.append({
                'index': palace_index,
                'name': palace_name,
                'is_body_palace': p.get('is_body_palace', False),
                'is_original_palace': p.get('is_original_palace', False),
                'heavenly_stem': HEAVENLY_NAMES.get(hs, hs or ''),
                'earthly_branch': EARTHLY_NAMES.get(es, es or ''),
                'ganzhi': _to_ganzhi(hs, es),
                'major_stars': major_stars,
                'minor_stars': minor_stars,
                'adjective_stars': adj_stars,
                'changsheng12': p.get('changsheng12',''),
                'boshi12': p.get('boshi12',''),
                'jiangqian12': p.get('jiangqian12',''),
                'suiqian12': p.get('suiqian12',''),
                'decadal': {
                    'range': dec.get('range', []),
                    'heavenly_stem': HEAVENLY_NAMES.get(dec.get('heavenly_stem',''), dec.get('heavenly_stem','') or ''),
                    'earthly_branch': EARTHLY_NAMES.get(dec.get('earthly_branch',''), dec.get('earthly_branch','') or ''),
                } if dec else None,
                'ages': ages,
            })
        raw_cp = raw.get('corePalace') or raw.get('soul')
        result = {
            'basic_info': {
                'solar_date': raw.get('solarDate',''),
                'lunar_date': raw.get('lunarDate',''),
                'chinese_date': raw.get('chineseDate',''),
                'shichen': raw.get('time',''),
                'shichen_range': raw.get('timeRange',''),
                'zodiac': raw.get('zodiac',''),
                'sign': raw.get('sign',''),
                'five_elements_class': raw.get('fiveElementsClass',''),
            },
            'core_palace': {
                'soul_star': raw.get('soul',''),
                'body_star': raw.get('body',''),
            },
            'twelve_palaces': twelve,
            'decadal_overview': [],
            'display_meta': {
                'chart_name': '玄策专业盘',
                'gender_yinyang': g,
                'calendar_type': '农历' if date_type == 'lunar' else '阳历',
                'beijing_time': _format_dt(_calc_true_solar_display(year, month, day, hour, minute, None)[0]),
                'true_solar_time': _format_dt(true_dt),
                'longitude': display_lng if display_lng is not None else used_lng,
                'true_solar_enabled': has_true_solar,
                'time_rule': '按真太阳时定时辰' if has_true_solar else '按北京时间定时辰',
                'chart_method': '三合盘',
                'available_modes': ['三合', '四化'],
                'coming_modes': ['飞星', '飞化'],
                'source_note': '基于 iztro-py 本地排盘；春节/立春边界与其他紫微软件可能存在流派口径差异。',
            },
        }
        result['decadal_overview'] = [
            {
                'palace_name': p.get('name', ''),
                'age_range': (p.get('decadal') or {}).get('range', []),
                'ganzhi': ((p.get('decadal') or {}).get('heavenly_stem') or '') + ((p.get('decadal') or {}).get('earthly_branch') or ''),
            }
            for p in twelve
            if p.get('decadal')
        ]
        return result

    def horoscope(self, year, month, day, hour, minute=0, gender='男', date_type='solar', target_date=None, target_hour=-1, target_minute=0, **kwargs):
        ti = _hour_to_time_index(hour, minute)
        g = '男' if gender in ('male','M','m','1','男') else '女'
        if date_type == 'lunar':
            astro = by_lunar(str(year) + '-' + str(month) + '-' + str(day), ti, g, fix_leap=True)
        else:
            astro = by_solar(str(year) + '-' + str(month) + '-' + str(day), ti, g, fix_leap=True)
        d = astro.model_dump()
        raw = astro.to_iztro_dict()
        h = astro.horoscope(target_date)
        hd = h.model_dump() if hasattr(h, 'model_dump') else {}
        result = self.calculate(year, month, day, hour, minute, gender, date_type)
        result['target_date'] = target_date
        result['horoscope'] = self._normalize_horoscope(hd)
        return result

    def _normalize_horoscope(self, hd):
        def _norm_period(pd):
            if not pd or not isinstance(pd, dict):
                return pd
            p = dict(pd)
            hs = p.get('heavenly_stem', '')
            es = p.get('earthly_branch', '')
            hs_cn = HEAVENLY_NAMES.get(hs, hs or '')
            es_cn = EARTHLY_NAMES.get(es, es or '')
            p['heavenly_stem'] = hs_cn
            p['earthly_branch'] = es_cn
            if hs_cn or es_cn:
                p['ganzhi'] = hs_cn + es_cn
            if 'palace_names' in p:
                p['palace_names'] = [PALACE_NAME_MAP.get(n, n) for n in p['palace_names']]
            return p
        return {
            'solar_date': hd.get('solar_date',''),
            'lunar_date': hd.get('lunar_date',''),
            'age': hd.get('nominal_age', hd.get('age', 0)),
            'decadal': _norm_period(hd.get('decadal')),
            'yearly': _norm_period(hd.get('yearly')),
            'monthly': _norm_period(hd.get('monthly')),
            'daily': _norm_period(hd.get('daily')),
            'hourly': _norm_period(hd.get('hourly')),
        }
