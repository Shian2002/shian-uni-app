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
        if name == "app" or name in {"ai_runs", "auth_channel_routes", "recharge_routes"}:
            sys.modules.pop(name, None)
    sys.path.insert(0, BACKEND_DIR)
    module = importlib.import_module("app")
    module.app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
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


def test_legacy_database_migration_creates_operational_hardening_tables(app_module):
    with app_module.app.app_context():
        for table in ["migration_record", "verification_code", "rate_limit_bucket", "ai_run"]:
            app_module.db.session.execute(app_module.db.text(f"DROP TABLE IF EXISTS {table}"))
        app_module.db.session.commit()

        app_module.migrate_db()

        tables = {
            row[0]
            for row in app_module.db.session.execute(app_module.db.text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )).fetchall()
        }
    assert {"migration_record", "verification_code", "rate_limit_bucket", "ai_run"}.issubset(tables)


def test_migration_registration_recovers_when_record_table_is_missing(app_module):
    with app_module.app.app_context():
        app_module.db.session.execute(app_module.db.text("DROP TABLE IF EXISTS migration_record"))
        app_module.db.session.commit()

        record = app_module.record_migration_applied("test_missing_record_table", "自动建表")

        assert record is not None
        saved = app_module.MigrationRecord.query.filter_by(migration_key="test_missing_record_table").one()
        assert saved.status == "applied"
        assert saved.detail == "自动建表"


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


def test_staging_sms_and_email_default_to_log_mode(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("ALIYUN_SMS_ACCESS_KEY_ID", "real-looking-key")
    monkeypatch.setenv("ALIYUN_SMS_ACCESS_KEY_SECRET", "real-looking-secret")
    monkeypatch.setenv("SMTP_USER", "sender@example.com")
    monkeypatch.setenv("SMTP_PASS", "smtp-secret")
    module = _fresh_import_app(tmp_path, monkeypatch)

    class FailingSMTP:
        def __init__(self, *args, **kwargs):
            raise AssertionError("测试环境默认不应连接 SMTP")

    auth_channel_routes = importlib.import_module("auth_channel_routes")
    monkeypatch.setattr(auth_channel_routes.smtplib, "SMTP", FailingSMTP)
    client = module.app.test_client()

    sms_response = client.post("/api/sms/send", json={"phone": "13800000000"})
    email_response = client.post("/api/email/send", json={"email": "tester@example.com"})

    assert sms_response.status_code == 200
    assert email_response.status_code == 200
    with module.app.app_context():
        assert module.VerificationCode.query.filter_by(code_key="sms_13800000000").one()
        assert module.VerificationCode.query.filter_by(code_key="email_tester@example.com").one()


def test_staging_recharge_records_proof_without_auto_confirm(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_ENV", "staging")
    monkeypatch.setenv("ALIPAY_QR_AUTO_CONFIRM", "1")
    module = _fresh_import_app(tmp_path, monkeypatch)

    with module.app.app_context():
        user = module.User(
            username="staging-buyer",
            password_hash="x",
            has_password=True,
        )
        module.db.session.add(user)
        module.db.session.flush()
        order = module.RechargeOrder(
            user_id=user.id,
            package_id="test-cent",
            package_name="测试包",
            points=1,
            amount=0.01,
            status="pending",
        )
        module.db.session.add(order)
        module.db.session.commit()
        user_id = user.id
        order_id = order.id

    client = module.app.test_client()
    with client.session_transaction() as sess:
        sess["_user_id"] = str(user_id)
        sess["_fresh"] = True

    response = client.post("/api/recharge/verify-payment", json={
        "order_id": order_id,
        "payment_proof_text": "支付宝支付成功 收款方 时安解忧屋 支付金额 ¥0.01",
        "payment_proof_hash": "staging-proof-hash",
    })

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "pending"
    assert body["auto_confirmed"] is False
    assert "测试环境" in body["message"]
    with module.app.app_context():
        refreshed = module.db.session.get(module.RechargeOrder, order_id)
        membership = module.Membership.query.filter_by(user_id=user_id).first()
        logs = module.PointLog.query.filter_by(user_id=user_id, action="recharge").all()
        assert refreshed.status == "pending"
        assert refreshed.payment_reference == "staging-proof-hash"
        assert membership is None
        assert logs == []
