"""紫微斗数排盘、推运与元信息 API。"""

from datetime import datetime

from flask import jsonify, request

from extensions import csrf


def register_ziwei_routes(app, deps):
    """注册紫微斗数纯排盘相关端点。"""

    has_ziwei = bool(deps.get('has_ziwei'))
    engine = deps.get('ziwei_engine')
    shichen_names = deps.get('shichen_names') or []
    shichen_ranges = deps.get('shichen_ranges') or []
    palace_name_map = deps.get('palace_name_map') or {}
    logger = deps.get('logger')

    @app.route('/api/ziwei/pan', methods=['POST'])
    @csrf.exempt
    def api_ziwei_pan():
        """紫微斗数排盘 API。"""
        if not has_ziwei:
            return jsonify({'code': 1, 'msg': '紫微斗数引擎未安装(iztro-py)', 'data': None}), 503

        data = request.get_json(silent=True) or {}

        required = ['year', 'month', 'day', 'hour', 'gender']
        missing = [f for f in required if f not in data or data[f] is None]
        if missing:
            return jsonify({
                'code': 1,
                'msg': f'缺少必填参数: {", ".join(missing)}',
                'data': None,
            }), 400

        year = data['year']
        month = data['month']
        day = data['day']
        hour = data['hour']
        minute = data.get('minute', 0)
        gender = data['gender']
        date_type = data.get('date_type', 'solar')
        timezone = data.get('timezone', 'Asia/Shanghai')
        longitude = data.get('longitude')
        question = data.get('question', '')

        try:
            year = int(year)
            month = int(month)
            day = int(day)
            hour = int(hour)
            minute = int(minute) if minute else 0
        except (ValueError, TypeError):
            return jsonify({'code': 1, 'msg': '数值参数格式错误', 'data': None}), 400

        if not (1900 <= year <= 2100):
            return jsonify({'code': 1, 'msg': '出生年范围: 1900-2100', 'data': None}), 400
        if not (1 <= month <= 12):
            return jsonify({'code': 1, 'msg': '出生月范围: 1-12', 'data': None}), 400
        if not (1 <= day <= 31):
            return jsonify({'code': 1, 'msg': '出生日范围: 1-31', 'data': None}), 400
        if not (0 <= hour <= 23):
            return jsonify({'code': 1, 'msg': '出生时范围: 0-23', 'data': None}), 400
        if not (0 <= minute <= 59):
            return jsonify({'code': 1, 'msg': '出生分范围: 0-59', 'data': None}), 400
        if gender not in ('male', 'female', '男', '女', 'M', 'F', 'm', 'f', '1', '0'):
            return jsonify({'code': 1, 'msg': '性别参数无效，请输入 男/女', 'data': None}), 400
        if date_type not in ('solar', 'lunar'):
            return jsonify({'code': 1, 'msg': '历法类型无效，请输入 solar/lunar', 'data': None}), 400

        try:
            result = engine.calculate(
                year=year, month=month, day=day,
                hour=hour, minute=minute,
                gender=gender, date_type=date_type,
                timezone=timezone, longitude=longitude,
            )
            result['request'] = {
                'type': 'ziwei_pan',
                'question': question,
                'timestamp': datetime.now().isoformat(),
            }
            return jsonify({'code': 0, 'msg': 'success', 'data': result})
        except ValueError as e:
            return jsonify({'code': 2, 'msg': str(e), 'data': None}), 400
        except Exception as e:
            if logger:
                logger.error(f"紫微排盘失败: {e}")
            return jsonify({'code': 3, 'msg': f'排盘计算失败: {str(e)}', 'data': None}), 500

    @app.route('/api/ziwei/horoscope', methods=['POST'])
    @csrf.exempt
    def api_ziwei_horoscope():
        """紫微斗数推运 API。"""
        if not has_ziwei:
            return jsonify({'code': 1, 'msg': '紫微斗数引擎未安装(iztro-py)', 'data': None}), 503

        data = request.get_json(silent=True) or {}

        required = ['year', 'month', 'day', 'hour', 'gender']
        missing = [f for f in required if f not in data or data[f] is None]
        if missing:
            return jsonify({
                'code': 1,
                'msg': f'缺少必填参数: {", ".join(missing)}',
                'data': None,
            }), 400

        target_date = data.get('target_date', '')
        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')

        try:
            year = int(data['year'])
            month = int(data['month'])
            day = int(data['day'])
            hour = int(data['hour'])
        except (ValueError, TypeError):
            return jsonify({'code': 1, 'msg': '数值参数格式错误', 'data': None}), 400

        try:
            result = engine.horoscope(
                year=year, month=month, day=day,
                hour=hour, minute=int(data.get('minute', 0) or 0),
                gender=data['gender'],
                target_date=target_date,
                target_hour=int(data.get('target_hour', -1) or -1),
                target_minute=int(data.get('target_minute', 0) or 0),
                date_type=data.get('date_type', 'solar'),
                longitude=data.get('longitude'),
            )
            result['request'] = {
                'type': 'ziwei_horoscope',
                'question': data.get('question', ''),
                'timestamp': datetime.now().isoformat(),
            }
            return jsonify({'code': 0, 'msg': 'success', 'data': result})
        except ValueError as e:
            return jsonify({'code': 2, 'msg': str(e), 'data': None}), 400
        except Exception as e:
            if logger:
                logger.error(f"紫微推运失败: {e}")
            return jsonify({'code': 3, 'msg': f'推运计算失败: {str(e)}', 'data': None}), 500

    @app.route('/api/ziwei/info')
    def api_ziwei_info():
        """获取紫微斗数基本信息。"""
        if not has_ziwei:
            return jsonify({'code': 1, 'msg': '紫微斗数引擎未安装', 'data': None}), 503

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'name': '紫微斗数',
                'description': '以出生时间排出命盘，通过十二宫星曜组合分析人生运势',
                'input_requirements': [
                    {'field': 'year', 'type': 'int', 'required': True, 'description': '出生年(1900-2100)'},
                    {'field': 'month', 'type': 'int', 'required': True, 'description': '出生月(1-12)'},
                    {'field': 'day', 'type': 'int', 'required': True, 'description': '出生日(1-31)'},
                    {'field': 'hour', 'type': 'int', 'required': True, 'description': '出生小时(0-23)'},
                    {'field': 'minute', 'type': 'int', 'required': False, 'description': '出生分钟(0-59)'},
                    {'field': 'gender', 'type': 'str', 'required': True, 'description': '性别(男/女)'},
                    {'field': 'date_type', 'type': 'str', 'required': False, 'description': '历法类型(solar/lunar)'},
                ],
                'twelve_palaces': list(palace_name_map.values()),
                'shichen': [
                    {'index': i, 'name': shichen_names[i], 'range': shichen_ranges[i]}
                    for i in range(12)
                ],
                'engine': 'iztro-py v0.3.4',
                'api_version': '1.0.0',
                'compatible_with': ['liuyao', 'meihua', 'tarot'],
            },
        })

    @app.route('/api/ziwei/shichen')
    def api_ziwei_shichen():
        """获取时辰对照表。"""
        if not has_ziwei:
            return jsonify({'code': 1, 'msg': '引擎未安装', 'data': None}), 503

        return jsonify({
            'code': 0,
            'msg': 'success',
            'data': {
                'shichen': [
                    {'index': i, 'name': shichen_names[i], 'range': shichen_ranges[i]}
                    for i in range(12)
                ],
                'note': 'hour参数为出生小时(0-23)，系统自动转换为对应时辰。23:00-01:00为子时，支持早子晚子。',
            },
        })
