#!/usr/bin/env bash
# 时安解忧屋 - 回滚 H5 前端静态资源
# 用法: CONFIRM_H5_ROLLBACK=shianjieyouwu.com bash rollback-h5-on-server.sh
# 可选: ROLLBACK_ARCHIVE=/home/lighthouse/backups/xuan-cet/h5/h5-deploy-YYYYMMDD-HHMMSS.tar.gz 指定备份包。

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"
BASE_URL="${BASE_URL:-https://shianjieyouwu.com}"
H5_DIR="${H5_DIR:-/var/www/xuan-cet}"
BACKUP_DIR="${BACKUP_DIR:-/home/lighthouse/backups/xuan-cet/h5}"
ROLLBACK_ARCHIVE="${ROLLBACK_ARCHIVE:-}"
CONFIRM_H5_ROLLBACK="${CONFIRM_H5_ROLLBACK:-}"
SSH_CMD=(ssh -i "$SSH_KEY")

section() {
  printf '\n== %s ==\n' "$1"
}

if [ "$CONFIRM_H5_ROLLBACK" != "shianjieyouwu.com" ]; then
  echo "[ERROR] 这是生产 H5 静态资源回滚。"
  echo "请显式运行: CONFIRM_H5_ROLLBACK=shianjieyouwu.com bash rollback-h5-on-server.sh"
  exit 1
fi

section "选择回滚备份"
if [ -z "$ROLLBACK_ARCHIVE" ]; then
  ROLLBACK_ARCHIVE="$("${SSH_CMD[@]}" "$SERVER" "ls -1t '$BACKUP_DIR'/h5-deploy-*.tar.gz 2>/dev/null | head -n 1")"
fi
if [ -z "$ROLLBACK_ARCHIVE" ]; then
  echo "[ERROR] 未找到 H5 备份包: $BACKUP_DIR/h5-deploy-*.tar.gz"
  exit 1
fi
echo "目标服务器: $SERVER"
echo "目标目录: $H5_DIR"
echo "回滚备份: $ROLLBACK_ARCHIVE"

section "执行回滚"
"${SSH_CMD[@]}" "$SERVER" "set -e
test -f '$ROLLBACK_ARCHIVE'
mkdir -p '$H5_DIR'
rm -rf '$H5_DIR/assets'
tar -C '$H5_DIR' -xzf '$ROLLBACK_ARCHIVE'"

section "回滚后线上验证"
BASE_URL="$BASE_URL" bash scripts/production_monitor.sh

section "完成"
echo "H5 前端已回滚: $BASE_URL"
