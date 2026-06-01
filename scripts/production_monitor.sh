#!/usr/bin/env bash
# 线上健康与错误日志检查。默认只读，不修改服务器。

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"
BASE_URL="${BASE_URL:-http://119.29.128.18}"
SINCE="${SINCE:-30 min ago}"
FOLLOW="${FOLLOW:-0}"
FAIL_ON_ERRORS="${FAIL_ON_ERRORS:-0}"
SERVICE="${SERVICE:-xuan-cet-flask}"

SSH_CMD=(ssh -i "$SSH_KEY")
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

section() {
  printf '\n== %s ==\n' "$1"
}

section "线上健康"
python3 "$ROOT_DIR/scripts/production_smoke.py" --base-url "$BASE_URL" --skip-auth

section "服务器状态"
"${SSH_CMD[@]}" "$SERVER" "set -e
systemctl is-active '$SERVICE'
df -h / /home /var 2>/dev/null || df -h
free -h || true"

section "最近后端错误日志"
ERROR_PATTERN='Traceback|Exception|ERROR|CRITICAL|panic|segmentation fault|ModuleNotFoundError|ImportError'
set +e
BACKEND_ERRORS="$("${SSH_CMD[@]}" "$SERVER" "sudo journalctl -u '$SERVICE' --since '$SINCE' --no-pager | grep -Ei '$ERROR_PATTERN' | tail -n 80")"
BACKEND_STATUS=$?
set -e
if [ -n "$BACKEND_ERRORS" ]; then
  printf '%s\n' "$BACKEND_ERRORS"
else
  echo "最近 $SINCE 内没有匹配到后端错误。"
fi

section "最近 Nginx 错误日志"
set +e
NGINX_ERRORS="$("${SSH_CMD[@]}" "$SERVER" "sudo test -f /var/log/nginx/error.log && sudo grep -Ei '$ERROR_PATTERN|connect\\(\\) failed|upstream timed out|502|504' /var/log/nginx/error.log | tail -n 80")"
NGINX_STATUS=$?
set -e
if [ -n "$NGINX_ERRORS" ]; then
  printf '%s\n' "$NGINX_ERRORS"
else
  echo "Nginx error.log 没有匹配到近期关键错误。"
fi

if [ "$FAIL_ON_ERRORS" = "1" ] && { [ "$BACKEND_STATUS" -eq 0 ] || [ "$NGINX_STATUS" -eq 0 ]; }; then
  echo "[FAIL] 发现线上错误日志。"
  exit 1
fi

if [ "$FOLLOW" = "1" ]; then
  section "实时跟踪后端日志"
  "${SSH_CMD[@]}" "$SERVER" "sudo journalctl -u '$SERVICE' -f"
fi

section "完成"
echo "线上监控检查完成。"
