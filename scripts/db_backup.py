#!/usr/bin/env python3
"""SQLite 数据库备份工具。"""

import argparse
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def file_size(path):
    return path.stat().st_size if path.exists() else 0


def integrity_check(db_path):
    conn = sqlite3.connect(str(db_path))
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return result and result[0] == "ok"
    finally:
        conn.close()


def backup_sqlite(source, backup_dir, keep):
    source = Path(source).expanduser().resolve()
    backup_dir = Path(backup_dir).expanduser().resolve()
    if not source.is_file():
        raise SystemExit(f"数据库不存在: {source}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    backup_path = backup_dir / f"{source.stem}-{stamp}.db"

    src = sqlite3.connect(str(source))
    dst = sqlite3.connect(str(backup_path))
    try:
        src.backup(dst)
    finally:
        dst.close()
        src.close()

    os.chmod(backup_path, 0o600)
    ok = integrity_check(backup_path)
    manifest = {
        "source": str(source),
        "backup": str(backup_path),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "bytes": file_size(backup_path),
        "integrity_ok": ok,
    }
    manifest_path = backup_path.with_suffix(".json")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    os.chmod(manifest_path, 0o600)

    backups = sorted(backup_dir.glob(f"{source.stem}-*.db"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in backups[keep:]:
        old_manifest = old.with_suffix(".json")
        old.unlink(missing_ok=True)
        old_manifest.unlink(missing_ok=True)

    if not ok:
        raise SystemExit(f"备份完整性校验失败: {backup_path}")

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="创建 SQLite 在线一致性备份")
    parser.add_argument("--source", default="backend/tianji.db", help="源数据库路径")
    parser.add_argument("--backup-dir", default="backups/db", help="备份目录")
    parser.add_argument("--keep", type=int, default=30, help="保留最近多少份备份")
    args = parser.parse_args()
    backup_sqlite(args.source, args.backup_dir, max(args.keep, 1))


if __name__ == "__main__":
    main()
