#!/usr/bin/env python3
"""只读对账多个 SQLite 数据库中的用户资产和历史记录。"""

from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path


HISTORY_TABLES = [
    "record",
    "bazi_record",
    "tarot_conversation",
    "comprehensive_conversation",
    "bazi_conversation",
    "liuyao_conversation",
    "meihua_conversation",
    "qimen_conversation",
    "ziwei_conversation",
]


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "select 1 from sqlite_master where type='table' and name=?",
        (table,),
    ).fetchone()
    return row is not None


def scalar(conn: sqlite3.Connection, sql: str, args: tuple = ()) -> int | str | None:
    row = conn.execute(sql, args).fetchone()
    return row[0] if row else None


def inspect_db(path: Path, usernames: list[str]) -> dict:
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    try:
        existing_tables = {
            row[0]
            for row in conn.execute("select name from sqlite_master where type='table'")
        }
        result = {
            "path": str(path),
            "size_bytes": path.stat().st_size,
            "tables": sorted(existing_tables),
            "totals": {},
            "users": {},
        }
        for table in ["user", "membership", "point_log", *HISTORY_TABLES]:
            result["totals"][table] = (
                scalar(conn, f"select count(*) from {table}")
                if table in existing_tables
                else "MISSING"
            )

        for username in usernames:
            row = conn.execute(
                """
                select
                  u.id,
                  u.username,
                  u.email,
                  u.phone,
                  u.daily_tool_count,
                  u.last_tool_date,
                  m.level,
                  m.points,
                  m.expire_at,
                  m.updated_at
                from user u
                left join membership m on m.user_id = u.id
                where u.username = ?
                """,
                (username,),
            ).fetchone()
            if not row:
                result["users"][username] = None
                continue
            user = dict(row)
            user_id = user["id"]
            user["point_log_count"] = scalar(
                conn, "select count(*) from point_log where user_id = ?", (user_id,)
            ) if "point_log" in existing_tables else "MISSING"
            user["recent_point_logs"] = [
                dict(log)
                for log in conn.execute(
                    """
                    select id, action, points, description, created_at
                    from point_log
                    where user_id = ?
                    order by id desc
                    limit 10
                    """,
                    (user_id,),
                )
            ] if "point_log" in existing_tables else []
            user["history_counts"] = {}
            for table in HISTORY_TABLES:
                user["history_counts"][table] = (
                    scalar(conn, f"select count(*) from {table} where user_id = ?", (user_id,))
                    if table in existing_tables
                    else "MISSING"
                )
            result["users"][username] = user
        return result
    finally:
        conn.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="只读对账多个 SQLite 数据库中的用户积分、日志和历史记录。",
    )
    parser.add_argument("databases", nargs="+", type=Path)
    parser.add_argument(
        "--user",
        dest="users",
        action="append",
        default=[],
        help="要对账的用户名，可重复传入。默认：shian",
    )
    parser.add_argument("--json", action="store_true", help="输出 JSON。")
    args = parser.parse_args()

    users = args.users or ["shian"]
    reports = [inspect_db(path, users) for path in args.databases]

    if args.json:
        print(json.dumps(reports, ensure_ascii=False, indent=2))
        return 0

    for report in reports:
        print(f"=== {report['path']} ({report['size_bytes']} bytes)")
        print("Totals:")
        for key, value in report["totals"].items():
            print(f"  {key:<28} {value}")
        for username, user in report["users"].items():
            print(f"User: {username}")
            if not user:
                print("  MISSING")
                continue
            print(f"  id={user['id']} level={user['level']} points={user['points']}")
            print(f"  email={user['email'] or ''} phone={user['phone'] or ''}")
            print(f"  point_log_count={user['point_log_count']}")
            print("  history_counts:")
            for table, count in user["history_counts"].items():
                print(f"    {table:<26} {count}")
            print("  recent_point_logs:")
            for log in user["recent_point_logs"]:
                print(
                    "    "
                    f"{log['id']}: {log['action']} {log['points']} "
                    f"{log['created_at']} {log['description'] or ''}"
                )
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
