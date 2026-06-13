#!/usr/bin/env bash
# 单向同步：生产数据库 -> 测试数据库。
# 只覆盖测试库，不会把测试库写回生产库。

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"

PROD_DB="${PROD_DB:-/home/lighthouse/tianji/flask-source/backend/tianji.db}"
STAGING_DB="${STAGING_DB:-/home/lighthouse/tianji-staging/backend/tianji.db}"
STAGING_SERVICE="${STAGING_SERVICE:-xuan-cet-staging-flask}"
BACKUP_DIR="${BACKUP_DIR:-/home/lighthouse/backups/xuan-cet-staging/db}"

SSH_CMD=(ssh -i "$SSH_KEY")

echo "============================================"
echo " 生产库 -> 测试库 单向同步"
echo "============================================"
echo "生产库: $PROD_DB"
echo "测试库: $STAGING_DB"

"${SSH_CMD[@]}" "$SERVER" "set -euo pipefail
if [ ! -f '$PROD_DB' ]; then
  echo '[ERROR] 未找到生产库 $PROD_DB'
  exit 1
fi

mkdir -p '$BACKUP_DIR' '$(dirname "$STAGING_DB")'
if [ -f '$STAGING_DB' ]; then
  cp '$STAGING_DB' '$BACKUP_DIR/tianji-staging-before-sync-'\$(date -u +%Y%m%d-%H%M%S)'.db'
  chmod 600 '$BACKUP_DIR'/tianji-staging-before-sync-*.db
  ls -1t '$BACKUP_DIR'/tianji-staging-before-sync-*.db | tail -n +31 | xargs -r rm -f
fi

sudo systemctl stop '$STAGING_SERVICE' >/dev/null 2>&1 || true

if command -v sqlite3 >/dev/null 2>&1; then
  sqlite3 '$PROD_DB' 'PRAGMA wal_checkpoint(FULL);' >/dev/null || true
fi

tmp_db='$STAGING_DB.tmp-sync'
cp '$PROD_DB' \"\$tmp_db\"
chmod 600 \"\$tmp_db\"
mv \"\$tmp_db\" '$STAGING_DB'
rm -f '$STAGING_DB-wal' '$STAGING_DB-shm'
chown '$SERVER_USER:$SERVER_USER' '$STAGING_DB'

sudo systemctl start '$STAGING_SERVICE' >/dev/null 2>&1 || true
"

echo "测试库已从生产库单向刷新。"
echo "下一步可运行: bash deploy-to-staging.sh"
