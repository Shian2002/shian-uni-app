#!/usr/bin/env python3
"""生产 SQLite 数据库只读审计。

用于发布后或定时巡检，重点检查表结构、积分数据和孤儿记录。
"""

import argparse
import json
import sqlite3
import sys
from pathlib import Path


REQUIRED_TABLES = {
    "user",
    "membership",
    "point_log",
    "recharge_order",
    "admin_audit_log",
    "migration_record",
    "verification_code",
    "rate_limit_bucket",
    "ai_run",
}


def _connect_readonly(path):
    uri = f"file:{Path(path).resolve()}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _table_exists(conn, table):
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return bool(row)


def _count(conn, sql):
    row = conn.execute(sql).fetchone()
    return int(row[0] or 0)


def audit_database(path):
    """返回审计发现列表；空列表表示当前检查项未发现异常。"""
    findings = []
    db_path = Path(path)
    if not db_path.exists():
        return [{"severity": "critical", "code": "db_not_found", "message": f"数据库不存在: {db_path}"}]

    conn = _connect_readonly(db_path)
    try:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        if not integrity or integrity[0] != "ok":
            findings.append({
                "severity": "critical",
                "code": "integrity_check_failed",
                "message": f"SQLite integrity_check 失败: {integrity[0] if integrity else 'no result'}",
            })

        existing_tables = {
            row[0]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        for table in sorted(REQUIRED_TABLES - existing_tables):
            findings.append({
                "severity": "critical",
                "code": "missing_table",
                "table": table,
                "message": f"缺少关键表: {table}",
            })

        if _table_exists(conn, "membership"):
            negative = _count(conn, "SELECT COUNT(*) FROM membership WHERE COALESCE(points, 0) < 0")
            if negative:
                findings.append({
                    "severity": "critical",
                    "code": "negative_membership_points",
                    "count": negative,
                    "message": f"发现负积分会员记录: {negative}",
                })

        if _table_exists(conn, "membership") and _table_exists(conn, "user"):
            orphan_memberships = _count(
                conn,
                "SELECT COUNT(*) FROM membership m LEFT JOIN user u ON u.id = m.user_id WHERE u.id IS NULL",
            )
            if orphan_memberships:
                findings.append({
                    "severity": "high",
                    "code": "orphan_membership",
                    "count": orphan_memberships,
                    "message": f"发现无对应用户的会员记录: {orphan_memberships}",
                })

        if _table_exists(conn, "point_log") and _table_exists(conn, "user"):
            orphan_logs = _count(
                conn,
                "SELECT COUNT(*) FROM point_log p LEFT JOIN user u ON u.id = p.user_id WHERE u.id IS NULL",
            )
            if orphan_logs:
                findings.append({
                    "severity": "high",
                    "code": "orphan_point_log",
                    "count": orphan_logs,
                    "message": f"发现无对应用户的积分日志: {orphan_logs}",
                })

        if _table_exists(conn, "point_log"):
            duplicate_dedupe = _count(
                conn,
                """
                SELECT COUNT(*) FROM (
                    SELECT dedupe_key
                    FROM point_log
                    WHERE dedupe_key IS NOT NULL AND dedupe_key != ''
                    GROUP BY dedupe_key
                    HAVING COUNT(*) > 1
                )
                """,
            )
            if duplicate_dedupe:
                findings.append({
                    "severity": "high",
                    "code": "duplicate_point_dedupe_key",
                    "count": duplicate_dedupe,
                    "message": f"发现重复积分幂等键: {duplicate_dedupe}",
                })

        return findings
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="只读审计生产 SQLite 数据库")
    parser.add_argument("db_path", help="SQLite 数据库文件路径")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    findings = audit_database(args.db_path)
    if args.json:
        print(json.dumps({"ok": not findings, "findings": findings}, ensure_ascii=False, indent=2))
    elif not findings:
        print("[OK] 数据库审计未发现异常")
    else:
        print("[FAIL] 数据库审计发现异常")
        for item in findings:
            print(f"- [{item['severity']}] {item['code']}: {item['message']}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
