"""运行状态与运维类 API。"""

from flask import jsonify


def register_ops_routes(app):
    """注册轻量运维端点。"""

    @app.route('/api/health')
    def api_health():
        """健康检查端点：只做本服务轻量探活，不阻塞等待第三方 API。"""
        from bazi_engine import _WZ_HEALTH

        return jsonify({
            'success': True,
            'status': 'running',
            'wz_api': {
                'available': _WZ_HEALTH.get('available', True),
                'fail_count': _WZ_HEALTH.get('fail_count', 0),
                'last_check': _WZ_HEALTH.get('last_check', 0),
                'checked': False,
            },
        })

    @app.route('/api/health/deep')
    def api_health_deep():
        """深度健康检查端点：需要时主动验证问真 API 连通性。"""
        from bazi_engine import check_wz_api_health, _WZ_HEALTH

        wz_ok = check_wz_api_health()
        return jsonify({
            'success': True,
            'status': 'running',
            'wz_api': {
                'available': wz_ok,
                'fail_count': _WZ_HEALTH.get('fail_count', 0),
                'last_check': _WZ_HEALTH.get('last_check', 0),
                'checked': True,
            },
        })
