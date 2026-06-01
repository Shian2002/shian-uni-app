"""运行状态与运维类 API。"""

from flask import jsonify


def register_ops_routes(app):
    """注册轻量运维端点。"""

    @app.route('/api/health')
    def api_health():
        """健康检查端点：返回服务状态和问真 API 连通性。"""
        from bazi_engine import check_wz_api_health, _WZ_HEALTH

        wz_ok = check_wz_api_health()
        return jsonify({
            'success': True,
            'status': 'running',
            'wz_api': {
                'available': wz_ok,
                'fail_count': _WZ_HEALTH.get('fail_count', 0),
            },
        })
