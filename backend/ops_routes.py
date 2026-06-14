"""运行状态与运维类 API。"""

import os
import tempfile

from flask import jsonify
from flask_wtf.csrf import generate_csrf
from sqlalchemy import text

from extensions import db


def _check_database():
    try:
        db.session.execute(text("SELECT 1")).scalar()
        return {"available": True, "checked": True}
    except Exception as exc:
        return {"available": False, "checked": True, "error": str(exc)[:200]}


def _check_upload_folder(app):
    upload_dir = app.config.get("UPLOAD_FOLDER", "")
    try:
        os.makedirs(upload_dir, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix=".health-", dir=upload_dir, delete=True) as fp:
            fp.write(b"ok")
            fp.flush()
        return {"available": True, "checked": True, "path": upload_dir}
    except Exception as exc:
        return {"available": False, "checked": True, "path": upload_dir, "error": str(exc)[:200]}


def register_ops_routes(app):
    """注册轻量运维端点。"""

    @app.route('/api/health')
    def api_health():
        """健康检查端点：只做本服务轻量探活，不阻塞等待第三方 API。"""
        from bazi_engine import _REFERENCE_API_HEALTH, external_reference_enabled

        reference_enabled = external_reference_enabled()

        return jsonify({
            'success': True,
            'status': 'running',
            'reference_api': {
                'enabled': reference_enabled,
                'available': True if not reference_enabled else _REFERENCE_API_HEALTH.get('available', True),
                'fail_count': _REFERENCE_API_HEALTH.get('fail_count', 0),
                'last_check': _REFERENCE_API_HEALTH.get('last_check', 0),
                'checked': False,
            },
        })

    @app.route('/api/health/deep')
    def api_health_deep():
        """深度健康检查端点：需要时主动验证参考口径 API 连通性。"""
        from bazi_engine import check_reference_api_health, _REFERENCE_API_HEALTH, external_reference_enabled

        reference_enabled = external_reference_enabled()
        reference_ok = check_reference_api_health() if reference_enabled else True
        database = _check_database()
        upload = _check_upload_folder(app)
        success = bool(reference_ok and database["available"] and upload["available"])
        return jsonify({
            'success': success,
            'status': 'running' if success else 'degraded',
            'reference_api': {
                'enabled': reference_enabled,
                'available': reference_ok,
                'fail_count': _REFERENCE_API_HEALTH.get('fail_count', 0),
                'last_check': _REFERENCE_API_HEALTH.get('last_check', 0),
                'checked': reference_enabled,
            },
            'database': database,
            'upload': upload,
        })

    @app.route('/api/csrf-token')
    def api_csrf_token():
        """给 H5 前端逐步接入 CSRF 保护使用。"""
        return jsonify({'csrf_token': generate_csrf()})
