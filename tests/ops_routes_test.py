import importlib
import os
import sys

import pytest
from werkzeug.security import check_password_hash, generate_password_hash


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    db_path = tmp_path / "test-tianji.db"
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("TIANJI_SECRET_KEY", "test-secret-key")
    sys.path.insert(0, backend_dir)
    try:
        module = importlib.import_module("app")
        module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
        with module.app.app_context():
            module.db.drop_all()
            module.db.create_all()
        yield module
    finally:
        if sys.path and sys.path[0] == backend_dir:
            sys.path.pop(0)


@pytest.fixture()
def client(app_module):
    return app_module.app.test_client()


@pytest.fixture()
def admin_user(app_module):
    with app_module.app.app_context():
        user = app_module.User(
            username="csrf-admin",
            password_hash=generate_password_hash("secret123", method="pbkdf2:sha256"),
            has_password=True,
            is_admin=True,
        )
        app_module.db.session.add(user)
        app_module.db.session.commit()
        return user.id


def test_health_is_lightweight_and_does_not_probe_reference_api(client, monkeypatch):
    import bazi_engine

    def fail_if_called():
        raise AssertionError("轻量健康检查不应访问第三方 API")

    monkeypatch.setattr(bazi_engine, "check_reference_api_health", fail_if_called)
    bazi_engine._REFERENCE_API_HEALTH.update({"available": True, "last_check": 123, "fail_count": 0})

    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["status"] == "running"
    assert data["reference_api"] == {
        "available": True,
        "checked": False,
        "fail_count": 0,
        "last_check": 123,
    }


def test_deep_health_probes_reference_api_when_requested(client, monkeypatch):
    import bazi_engine

    called = {"value": False}

    def fake_check():
        called["value"] = True
        bazi_engine._REFERENCE_API_HEALTH.update({"available": False, "last_check": 456, "fail_count": 3})
        return False

    monkeypatch.setattr(bazi_engine, "check_reference_api_health", fake_check)

    response = client.get("/api/health/deep")

    assert response.status_code == 200
    data = response.get_json()
    assert called["value"] is True
    assert data["reference_api"] == {
        "available": False,
        "checked": True,
        "fail_count": 3,
        "last_check": 456,
    }


def test_deep_health_checks_database_and_upload_folder(app_module, client, monkeypatch, tmp_path):
    import bazi_engine

    upload_dir = tmp_path / "uploads"
    app_module.app.config["UPLOAD_FOLDER"] = str(upload_dir)
    monkeypatch.setattr(bazi_engine, "check_reference_api_health", lambda: True)

    response = client.get("/api/health/deep")

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["database"]["checked"] is True
    assert data["database"]["available"] is True
    assert data["upload"]["checked"] is True
    assert data["upload"]["available"] is True
    assert upload_dir.is_dir()


def test_api_not_found_uses_consistent_error_envelope(client):
    response = client.get("/not-exists")

    assert response.status_code == 404
    data = response.get_json()
    assert data["success"] is False
    assert data["error"] == "页面不存在"


def test_rejected_form_api_request_uses_consistent_error_envelope(client):
    response = client.post(
        "/api/login",
        data="username=a&password=b",
        content_type="application/x-www-form-urlencoded",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert data["error"] == "Invalid request"


def test_csrf_protects_session_write_api_when_enabled(app_module, client, admin_user):
    app_module.app.config.update(WTF_CSRF_ENABLED=True)
    token_response = client.get("/api/csrf-token")
    token = token_response.get_json()["csrf_token"]
    with client.session_transaction() as sess:
        sess["_user_id"] = str(admin_user)
        sess["_fresh"] = True

    rejected = client.post(
        "/api/admin/change-password",
        json={
            "old_password": "secret123",
            "new_password": "new-secret-12345",
            "confirm_password": "new-secret-12345",
        },
    )

    accepted = client.post(
        "/api/admin/change-password",
        json={
            "old_password": "secret123",
            "new_password": "new-secret-12345",
            "confirm_password": "new-secret-12345",
        },
        headers={"X-CSRFToken": token},
    )

    assert rejected.status_code == 400
    assert rejected.get_json()["success"] is False
    assert accepted.status_code == 200
    with app_module.app.app_context():
        refreshed = app_module.db.session.get(app_module.User, admin_user)
        assert check_password_hash(refreshed.password_hash, "new-secret-12345")
