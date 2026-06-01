#!/usr/bin/env python3
"""SQLite 数据库恢复工具。"""

import argparse
import os
import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


def integrity_check(db_path):
    conn = sqlite3.connect(str(db_path))
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return result and result[0] == "ok"
    finally:
        conn.close()


def restore_sqlite(source_backup, target, pre_restore_dir, confirm):
    source_backup = Path(source_backup).expanduser().resolve()
    target = Path(target).expanduser().resolve()
    pre_restore_dir = Path(pre_restore_dir).expanduser().resolve()

    if not confirm:
        raise SystemExit("恢复数据库必须显式传入 --confirm")
    if not source_backup.is_file():
        raise SystemExit(f"备份文件不存在: {source_backup}")
    if not integrity_check(source_backup):
        raise SystemExit(f"备份完整性校验失败: {source_backup}")

    pre_restore_dir.mkdir(parents=True, exist_ok=True)
    if target.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        safety_backup = pre_restore_dir / f"{target.stem}-pre-restore-{stamp}.db"
        shutil.copy2(target, safety_backup)
        os.chmod(safety_backup, 0o600)
        if not integrity_check(safety_backup):
            raise SystemExit(f"恢复前安全备份校验失败: {safety_backup}")
        print(f"已创建恢复前安全备份: {safety_backup}")

    tmp_target = target.with_suffix(target.suffix + ".restore-tmp")
    shutil.copy2(source_backup, tmp_target)
    os.chmod(tmp_target, 0o600)
    os.replace(tmp_target, target)
    print(f"已恢复数据库: {target}")


def main():
    parser = argparse.ArgumentParser(description="从备份恢复 SQLite 数据库")
    parser.add_argument("--backup", required=True, help="要恢复的备份文件")
    parser.add_argument("--target", default="backend/tianji.db", help="目标数据库路径")
    parser.add_argument("--pre-restore-dir", default="backups/pre-restore", help="恢复前安全备份目录")
    parser.add_argument("--confirm", action="store_true", help="确认执行恢复")
    args = parser.parse_args()
    restore_sqlite(args.backup, args.target, args.pre_restore_dir, args.confirm)


if __name__ == "__main__":
    main()
