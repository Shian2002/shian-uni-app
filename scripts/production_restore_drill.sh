#!/usr/bin/env bash
# 备份恢复演练：把最新线上备份恢复到临时目录并校验，不触碰生产库。

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"
SSH_CMD=(ssh -i "$SSH_KEY")

BACKUP_DIR="${BACKUP_DIR:-/home/lighthouse/backups/xuan-cet/db}"
DRILL_DIR="${DRILL_DIR:-/tmp/xuan-cet-restore-drill}"

echo "== 线上数据库备份恢复演练 =="
echo "服务器: $SERVER"
echo "备份目录: $BACKUP_DIR"
echo "临时目录: $DRILL_DIR"

"${SSH_CMD[@]}" "$SERVER" "set -euo pipefail
LATEST=\$(find '$BACKUP_DIR' -maxdepth 1 -name 'tianji-*.db' -type f -printf '%T@ %p\n' | sort -rn | awk 'NR==1 {print \$2}')
if [ -z \"\$LATEST\" ]; then
  echo '[FAIL] 没有找到自动备份文件'
  exit 1
fi
rm -rf '$DRILL_DIR'
mkdir -p '$DRILL_DIR'
cp \"\$LATEST\" '$DRILL_DIR/tianji-restore-drill.db'
chmod 600 '$DRILL_DIR/tianji-restore-drill.db'
/usr/bin/python3 - <<'PY'
import json
import sqlite3
from pathlib import Path

db_path = Path('$DRILL_DIR/tianji-restore-drill.db')
conn = sqlite3.connect(str(db_path))
try:
    integrity = conn.execute('PRAGMA integrity_check').fetchone()[0]
    tables = {row[0] for row in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\")}
    required = {'user', 'record', 'membership'}
    counts = {}
    for table in sorted(required & tables):
        counts[table] = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
finally:
    conn.close()

result = {
    'restored_db': str(db_path),
    'bytes': db_path.stat().st_size,
    'integrity': integrity,
    'required_tables_present': bool(required <= tables),
    'counts': counts,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
if integrity != 'ok':
    raise SystemExit('[FAIL] 恢复演练完整性校验失败')
if not required <= tables:
    raise SystemExit('[FAIL] 恢复演练缺少关键表')
PY
rm -rf '$DRILL_DIR'"

echo "== 恢复演练通过，临时文件已清理 =="
