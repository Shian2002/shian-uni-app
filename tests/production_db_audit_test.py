import importlib.util
import sqlite3
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "production_db_audit.py"


def load_audit_module():
    spec = importlib.util.spec_from_file_location("production_db_audit", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def create_minimal_db(path):
    conn = sqlite3.connect(path)
    conn.executescript(
        """
        CREATE TABLE user (id INTEGER PRIMARY KEY, username TEXT);
        CREATE TABLE membership (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            points INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE point_log (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            points INTEGER NOT NULL DEFAULT 0,
            dedupe_key TEXT
        );
        CREATE TABLE recharge_order (id INTEGER PRIMARY KEY);
        CREATE TABLE admin_audit_log (id INTEGER PRIMARY KEY);
        CREATE TABLE migration_record (id INTEGER PRIMARY KEY);
        CREATE TABLE verification_code (id INTEGER PRIMARY KEY);
        CREATE TABLE rate_limit_bucket (id INTEGER PRIMARY KEY);
        CREATE TABLE ai_run (id INTEGER PRIMARY KEY);
        INSERT INTO user (id, username) VALUES (1, 'member');
        INSERT INTO membership (id, user_id, points) VALUES (1, 1, 10);
        INSERT INTO point_log (id, user_id, action, points) VALUES (1, 1, 'admin_add', 10);
        """
    )
    conn.commit()
    conn.close()


def test_production_db_audit_passes_clean_database(tmp_path):
    module = load_audit_module()
    db_path = tmp_path / "clean.db"
    create_minimal_db(db_path)

    findings = module.audit_database(db_path)

    assert findings == []


def test_production_db_audit_reports_missing_required_table(tmp_path):
    module = load_audit_module()
    db_path = tmp_path / "missing.db"
    create_minimal_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("DROP TABLE ai_run")
    conn.commit()
    conn.close()

    findings = module.audit_database(db_path)

    assert any(item["code"] == "missing_table" and item["table"] == "ai_run" for item in findings)


def test_production_db_audit_reports_points_data_anomalies(tmp_path):
    module = load_audit_module()
    db_path = tmp_path / "bad-points.db"
    create_minimal_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE membership SET points = -3 WHERE user_id = 1")
    conn.execute("INSERT INTO membership (id, user_id, points) VALUES (2, 999, 5)")
    conn.execute("INSERT INTO point_log (id, user_id, action, points) VALUES (2, 999, 'ghost', 5)")
    conn.commit()
    conn.close()

    findings = module.audit_database(db_path)
    codes = {item["code"] for item in findings}

    assert "negative_membership_points" in codes
    assert "orphan_membership" in codes
    assert "orphan_point_log" in codes
