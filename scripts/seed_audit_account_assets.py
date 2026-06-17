#!/usr/bin/env python3
"""为 staging/local 审核账号预置积分和 AI 次数。

默认 dry-run，不修改数据库。必须显式传入 --apply，且运行环境不能是
production，也不能指向已知生产库路径。
"""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DB = ROOT / "backend" / "tianji.db"
KNOWN_PROD_DB = "/home/lighthouse/tianji/flask-source/backend/tianji.db"


def parse_sqlite_url(value: str | None) -> Path:
    if not value:
        return DEFAULT_DB
    if value.startswith("sqlite:////"):
        return Path("/" + unquote(value[len("sqlite:////") :]))
    if value.startswith("sqlite:///"):
        raw = unquote(value[len("sqlite:///") :])
        return Path(raw) if raw.startswith("/") else (ROOT / raw)
    raise ValueError("DATABASE_URL 必须是 sqlite:/// 路径")


def current_env() -> str:
    return (os.environ.get("APP_ENV") or os.environ.get("FLASK_ENV") or "development").lower()


def assert_safe_target(db_path: Path, allow_production: bool) -> None:
    env = current_env()
    resolved = db_path.expanduser().resolve()
    if allow_production:
        return
    if env == "production":
        raise RuntimeError("拒绝在 production 环境预置审核账号资产")
    if str(resolved) == KNOWN_PROD_DB:
        raise RuntimeError(f"拒绝修改已知生产库: {KNOWN_PROD_DB}")
    if "/home/lighthouse/tianji/flask-source/" in str(resolved):
        raise RuntimeError(f"拒绝修改生产目录下数据库: {resolved}")


def require_tables(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    tables = {row[0] for row in rows}
    missing = {"user", "membership", "point_log"} - tables
    if missing:
        raise RuntimeError(f"数据库缺少表: {', '.join(sorted(missing))}")


def get_user_id(conn: sqlite3.Connection, username: str) -> int:
    row = conn.execute("SELECT id FROM user WHERE username=?", (username,)).fetchone()
    if not row:
        raise RuntimeError(f"找不到用户: {username}。请先在 staging/local 注册审核账号。")
    return int(row[0])


def ensure_membership(conn: sqlite3.Connection, user_id: int) -> None:
    row = conn.execute("SELECT id FROM membership WHERE user_id=?", (user_id,)).fetchone()
    if row:
        return
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    conn.execute(
        """
        INSERT INTO membership
          (user_id, level, points, ai_single_credits, ai_combo_credits, daily_ai_light_used_at, created_at, updated_at)
        VALUES (?, 'free', 0, 0, 0, '', ?, ?)
        """,
        (user_id, now, now),
    )


def current_assets(conn: sqlite3.Connection, user_id: int) -> dict[str, int | str]:
    row = conn.execute(
        """
        SELECT points, ai_single_credits, ai_combo_credits, COALESCE(daily_ai_light_used_at, '')
        FROM membership
        WHERE user_id=?
        """,
        (user_id,),
    ).fetchone()
    if not row:
        return {"points": 0, "ai_single_credits": 0, "ai_combo_credits": 0, "daily_ai_light_used_at": ""}
    return {
        "points": int(row[0] or 0),
        "ai_single_credits": int(row[1] or 0),
        "ai_combo_credits": int(row[2] or 0),
        "daily_ai_light_used_at": str(row[3] or ""),
    }


def add_log(conn: sqlite3.Connection, user_id: int, action: str, points: int, description: str) -> None:
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    conn.execute(
        "INSERT INTO point_log (user_id, action, points, description, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, action, points, description[:200], now),
    )


def apply_assets(
    conn: sqlite3.Connection,
    user_id: int,
    points: int,
    ai_single: int,
    ai_combo: int,
    reset_daily_light: bool,
    description: str,
) -> dict[str, dict[str, int | str]]:
    before = current_assets(conn, user_id)
    now = datetime.utcnow().isoformat(sep=" ", timespec="seconds")
    daily_value = "" if reset_daily_light else before["daily_ai_light_used_at"]
    conn.execute(
        """
        UPDATE membership
        SET points=?,
            ai_single_credits=?,
            ai_combo_credits=?,
            daily_ai_light_used_at=?,
            updated_at=?
        WHERE user_id=?
        """,
        (points, ai_single, ai_combo, daily_value, now, user_id),
    )
    point_delta = int(points) - int(before["points"])
    if point_delta:
        add_log(conn, user_id, "audit_seed_points", point_delta, description)
    if int(ai_single) != int(before["ai_single_credits"]):
        add_log(conn, user_id, "audit_seed_ai_single", 0, f"{description}: 单术数 AI 次数 {before['ai_single_credits']} -> {ai_single}")
    if int(ai_combo) != int(before["ai_combo_credits"]):
        add_log(conn, user_id, "audit_seed_ai_combo", 0, f"{description}: 多术数合参次数 {before['ai_combo_credits']} -> {ai_combo}")
    if reset_daily_light and before["daily_ai_light_used_at"]:
        add_log(conn, user_id, "audit_seed_daily_light_reset", 0, f"{description}: 重置每日轻量额度")
    after = current_assets(conn, user_id)
    return {"before": before, "after": after}


def main() -> int:
    parser = argparse.ArgumentParser(description="仅 staging/local 使用的审核账号资产预置工具")
    parser.add_argument("--username", default=os.environ.get("QA_USER", "test1"))
    parser.add_argument("--points", type=int, default=int(os.environ.get("AUDIT_SEED_POINTS", "120")))
    parser.add_argument("--ai-single", type=int, default=int(os.environ.get("AUDIT_SEED_AI_SINGLE", "5")))
    parser.add_argument("--ai-combo", type=int, default=int(os.environ.get("AUDIT_SEED_AI_COMBO", "2")))
    parser.add_argument("--database-url", default=os.environ.get("DATABASE_URL", ""))
    parser.add_argument("--apply", action="store_true", help="实际写入数据库；不传则只 dry-run")
    parser.add_argument("--allow-production", action="store_true", help="危险开关：默认禁止 production 和生产库路径")
    parser.add_argument("--reset-daily-light", action="store_true", default=True)
    args = parser.parse_args()

    if args.points < 0 or args.ai_single < 0 or args.ai_combo < 0:
        raise SystemExit("points / ai-single / ai-combo 不能为负数")

    db_path = parse_sqlite_url(args.database_url)
    assert_safe_target(db_path, args.allow_production)
    if not db_path.exists():
        raise SystemExit(f"数据库不存在: {db_path}")

    conn = sqlite3.connect(str(db_path))
    try:
        require_tables(conn)
        user_id = get_user_id(conn, args.username)
        ensure_membership(conn, user_id)
        before = current_assets(conn, user_id)
        result = {
            "mode": "apply" if args.apply else "dry-run",
            "env": current_env(),
            "db_path": str(db_path.expanduser().resolve()),
            "username": args.username,
            "user_id": user_id,
            "target": {
                "points": args.points,
                "ai_single_credits": args.ai_single,
                "ai_combo_credits": args.ai_combo,
                "daily_ai_light_used_at": "" if args.reset_daily_light else before["daily_ai_light_used_at"],
            },
            "before": before,
        }
        if args.apply:
            change = apply_assets(
                conn,
                user_id,
                args.points,
                args.ai_single,
                args.ai_combo,
                args.reset_daily_light,
                "审核账号资产预置，仅 staging/local 使用",
            )
            conn.commit()
            result.update(change)
        else:
            conn.rollback()
            result["after"] = result["target"]
        print(result)
        return 0
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"seed_audit_account_assets failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
