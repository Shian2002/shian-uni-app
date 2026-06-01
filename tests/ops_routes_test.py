import importlib
import os
import sys

import pytest


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    db_path = tmp_path / "test-tianji.db"
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("TIANJI_SECRET_KEY", "test-secret-key")
    sys.path.insert(0, backend_dir)
    try:
        module = importlib.import_module("app")
        module.app.config.update(TESTING=True)
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


def test_health_is_lightweight_and_does_not_probe_wenzhen(client, monkeypatch):
    import bazi_engine

    def fail_if_called():
        raise AssertionError("轻量健康检查不应访问第三方 API")

    monkeypatch.setattr(bazi_engine, "check_wz_api_health", fail_if_called)
    bazi_engine._WZ_HEALTH.update({"available": True, "last_check": 123, "fail_count": 0})

    response = client.get("/api/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["status"] == "running"
    assert data["wz_api"] == {
        "available": True,
        "checked": False,
        "fail_count": 0,
        "last_check": 123,
    }


def test_deep_health_probes_wenzhen_when_requested(client, monkeypatch):
    import bazi_engine

    called = {"value": False}

    def fake_check():
        called["value"] = True
        bazi_engine._WZ_HEALTH.update({"available": False, "last_check": 456, "fail_count": 3})
        return False

    monkeypatch.setattr(bazi_engine, "check_wz_api_health", fake_check)

    response = client.get("/api/health/deep")

    assert response.status_code == 200
    data = response.get_json()
    assert called["value"] is True
    assert data["wz_api"] == {
        "available": False,
        "checked": True,
        "fail_count": 3,
        "last_check": 456,
    }
