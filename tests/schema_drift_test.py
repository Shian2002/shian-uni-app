import importlib
import os
import sqlite3
import sys


def _load_models_metadata():
    backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
    sys.path.insert(0, backend_dir)
    try:
        models = importlib.import_module("models")
        return models.db.metadata
    finally:
        if sys.path and sys.path[0] == backend_dir:
            sys.path.pop(0)


def _schema_columns():
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql"))
    with open(schema_path, "r", encoding="utf-8") as file_obj:
        schema_sql = file_obj.read()

    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(schema_sql)
        tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            if row[0] != "sqlite_sequence"
        }
        return {
            table: {
                row[1]: {"notnull": bool(row[3]), "primary_key": bool(row[5])}
                for row in conn.execute(f"PRAGMA table_info({table})")
            }
            for table in tables
        }
    finally:
        conn.close()


def _schema_indexes():
    schema_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "database", "schema.sql"))
    with open(schema_path, "r", encoding="utf-8") as file_obj:
        schema_sql = file_obj.read()

    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(schema_sql)
        return {
            row[0]: row[1]
            for row in conn.execute(
                "SELECT name, tbl_name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
        }
    finally:
        conn.close()


def test_schema_sql_matches_model_tables_and_columns():
    metadata = _load_models_metadata()
    model_tables = {
        name: {column.name for column in table.columns}
        for name, table in metadata.tables.items()
    }
    schema_tables = {
        name: set(columns)
        for name, columns in _schema_columns().items()
    }

    assert schema_tables.keys() == model_tables.keys()
    for table_name, model_columns in model_tables.items():
        assert schema_tables[table_name] == model_columns, table_name


def test_schema_sql_matches_model_required_columns():
    metadata = _load_models_metadata()
    schema_tables = _schema_columns()

    mismatches = []
    for table_name, table in metadata.tables.items():
        for column in table.columns:
            if column.primary_key:
                continue
            expected_notnull = not column.nullable
            actual_notnull = schema_tables[table_name][column.name]["notnull"]
            if actual_notnull != expected_notnull:
                mismatches.append(
                    f"{table_name}.{column.name}: schema notnull={actual_notnull}, model notnull={expected_notnull}"
                )

    assert mismatches == []


def test_schema_sql_keeps_operational_indexes():
    indexes = _schema_indexes()
    expected_indexes = {
        "ix_record_user_app_created": "record",
        "ix_user_profile_user_type_last_created": "user_profile",
        "ix_user_profile_user_source_record": "user_profile",
        "ix_follow_up_user_record_created": "follow_up",
        "ix_collection_user_target_created": "collection",
        "ix_post_hidden_pinned_created": "post",
        "ix_post_featured_pinned_created": "post",
        "ix_post_user_created": "post",
        "ix_comment_post_parent_created": "comment",
        "ix_notification_user_read_created": "notification",
        "ix_report_status_created": "report",
        "ix_admin_audit_log_action_created": "admin_audit_log",
        "ix_point_log_user_created": "point_log",
        "ix_point_log_user_action_created": "point_log",
        "ix_recharge_order_user_created": "recharge_order",
        "ix_recharge_order_status_created": "recharge_order",
        "ix_recharge_order_payment_reference": "recharge_order",
        "ix_bazi_record_user_pinned_created": "bazi_record",
        "ix_tarot_conversation_user_updated": "tarot_conversation",
        "ix_liuyao_conversation_user_updated": "liuyao_conversation",
        "ix_meihua_conversation_user_updated": "meihua_conversation",
        "ix_qimen_conversation_user_updated": "qimen_conversation",
        "ix_bazi_conversation_user_updated": "bazi_conversation",
        "ix_ziwei_conversation_user_updated": "ziwei_conversation",
        "ix_comprehensive_conversation_user_updated": "comprehensive_conversation",
    }

    missing = {
        name: table
        for name, table in expected_indexes.items()
        if indexes.get(name) != table
    }
    assert missing == {}
