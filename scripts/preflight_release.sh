#!/usr/bin/env bash
# 上线前一键检查：后端语法、测试、H5 构建、依赖审计、可选线上烟测。

set -euo pipefail

BASE_URL="${BASE_URL:-https://shianjieyouwu.com}"
RUN_PROD_SMOKE="${RUN_PROD_SMOKE:-0}"
ALLOW_KNOWN_AUDIT="${ALLOW_KNOWN_AUDIT:-1}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

section() {
  printf '\n== %s ==\n' "$1"
}

section "Git 状态"
git status --short
DIRTY_BACKEND="$(git status --porcelain -- 'backend/*.py')"
if [ -n "$DIRTY_BACKEND" ]; then
  echo "[FAIL] 检测到未提交的后端 Python 改动，停止发布检查以避免线上代码和 Git 不一致。"
  printf '%s\n' "$DIRTY_BACKEND"
  exit 1
fi

section "Shell 脚本语法"
bash -n deploy-to-server.sh deploy-h5-to-server.sh rollback-h5-on-server.sh deploy-to-staging.sh scripts/*.sh

section "Python 语法"
python3 -m py_compile backend/*.py scripts/*.py

section "后端测试"
python3 -m pytest -q

section "H5 构建"
npm run build:h5

section "生产依赖审计"
set +e
AUDIT_OUTPUT="$(npm run audit:prod 2>&1)"
AUDIT_STATUS=$?
set -e
printf '%s\n' "$AUDIT_OUTPUT"
if [ "$AUDIT_STATUS" -ne 0 ]; then
  if [ "$ALLOW_KNOWN_AUDIT" = "1" ] \
    && grep -q "No fix available" <<<"$AUDIT_OUTPUT" \
    && grep -q "@dcloudio/uni-mp-weixin" <<<"$AUDIT_OUTPUT" \
    && grep -q "node_modules/ws" <<<"$AUDIT_OUTPUT"; then
    echo "[WARN] 仅发现 DCloud 间接 ws 漏洞，当前无官方修复；允许继续。"
  else
    echo "[FAIL] 生产依赖审计发现未知风险。"
    exit "$AUDIT_STATUS"
  fi
fi

if [ "$RUN_PROD_SMOKE" = "1" ]; then
  section "线上烟测"
  python3 scripts/production_smoke.py --base-url "$BASE_URL"
else
  section "线上烟测"
  echo "跳过。需要时运行: RUN_PROD_SMOKE=1 BASE_URL=$BASE_URL bash scripts/preflight_release.sh"
fi

section "完成"
echo "上线前检查通过。"
