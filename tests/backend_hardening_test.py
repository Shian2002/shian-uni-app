import importlib
import os
import sys
from pathlib import Path

import pytest


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
ROOT_DIR = Path(__file__).resolve().parents[1]


def _fresh_import_app(tmp_path, monkeypatch):
    db_path = tmp_path / "hardening.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("TIANJI_SECRET_KEY", "test-hardening-secret")
    for name in list(sys.modules):
        if name == "app" or name in {"ai_runs", "auth_channel_routes"}:
            sys.modules.pop(name, None)
    sys.path.insert(0, BACKEND_DIR)
    module = importlib.import_module("app")
    module.app.config.update(TESTING=True)
    with module.app.app_context():
        module.db.drop_all()
        module.db.create_all()
    return module


@pytest.fixture()
def app_module(tmp_path, monkeypatch):
    module = _fresh_import_app(tmp_path, monkeypatch)
    try:
        yield module
    finally:
        if sys.path and sys.path[0] == BACKEND_DIR:
            sys.path.pop(0)


def test_operational_hardening_tables_are_declared_in_models_and_schema():
    sys.path.insert(0, BACKEND_DIR)
    try:
        models = importlib.import_module("models")
        model_tables = set(models.db.metadata.tables)
    finally:
        if sys.path and sys.path[0] == BACKEND_DIR:
            sys.path.pop(0)

    schema_sql = (ROOT_DIR / "database" / "schema.sql").read_text(encoding="utf-8")
    for table in {"migration_record", "verification_code", "rate_limit_bucket", "ai_run"}:
        assert table in model_tables
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema_sql


def test_sqlite_connections_use_wal_busy_timeout_and_foreign_keys(app_module):
    with app_module.app.app_context():
        journal_mode = app_module.db.session.execute(app_module.db.text("PRAGMA journal_mode")).scalar()
        busy_timeout = app_module.db.session.execute(app_module.db.text("PRAGMA busy_timeout")).scalar()
        foreign_keys = app_module.db.session.execute(app_module.db.text("PRAGMA foreign_keys")).scalar()

    assert journal_mode.lower() == "wal"
    assert busy_timeout >= 5000
    assert foreign_keys == 1


def test_rate_limit_and_verification_codes_are_persisted(app_module):
    with app_module.app.app_context():
        assert app_module._check_rate_limit("login:1.2.3.4", max_count=1, window=300) is True
        assert app_module._check_rate_limit("login:1.2.3.4", max_count=1, window=300) is False
        bucket = app_module.RateLimitBucket.query.filter_by(bucket_key="login:1.2.3.4").one()
        assert bucket.count == 1

        app_module._store_code("email:test@example.com", "123456")
        stored = app_module.VerificationCode.query.filter_by(code_key="email:test@example.com").one()
        assert stored.code_hash != "123456"
        assert app_module._check_code("email:test@example.com", "123456") is True
        assert app_module._check_code("email:test@example.com", "123456") is False


def test_ai_run_helper_records_lifecycle(app_module):
    with app_module.app.app_context():
        run = app_module.start_ai_run("comprehensive", user_id=7, request_json={"question": "事业"})
        app_module.mark_ai_run_running(run.id)
        app_module.mark_ai_run_done(run.id, response_json={"conversation_id": 3})

        saved = app_module.AiRun.query.filter_by(id=run.id).one()
        assert saved.status == "done"
        assert saved.kind == "comprehensive"
        assert '"conversation_id": 3' in saved.response_json


def test_csrf_token_endpoint_and_security_headers_are_available(app_module):
    client = app_module.app.test_client()
    response = client.get("/api/csrf-token")

    assert response.status_code == 200
    body = response.get_json()
    assert isinstance(body["csrf_token"], str)
    assert len(body["csrf_token"]) > 20
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "SAMEORIGIN"


def test_deploy_script_hard_checks_runtime_database_url():
    deploy_script = (ROOT_DIR / "deploy-to-server.sh").read_text(encoding="utf-8")
    assert "systemctl show xuan-cet-flask -p Environment" in deploy_script
    assert "DATABASE_URL=sqlite:////home/lighthouse/tianji/flask-source/backend/tianji.db" in deploy_script
    assert "exit 1" in deploy_script
