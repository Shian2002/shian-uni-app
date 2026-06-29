#!/usr/bin/env bash
# 时安解忧屋 - 仅部署 H5 前端产物
# 用法: CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh
# 可选: DRY_RUN=1 bash deploy-h5-to-server.sh 只打印将要同步的文件，不改线上。
# 可选: INCLUDE_RECHARGE_ASSETS=1 同步旧充值二维码类静态资源；默认不上传，避免商店审核包混入外部充值素材。
# 可选: STORE_SUBMISSION_CHECK=1 额外执行商店提审严格检查；默认只检查网站 H5 上线必需项。

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"
BASE_URL="${BASE_URL:-https://shianjieyouwu.com}"
H5_DIR="${H5_DIR:-/var/www/xuan-cet}"
BACKUP_DIR="${BACKUP_DIR:-/home/lighthouse/backups/xuan-cet/h5}"
DRY_RUN="${DRY_RUN:-0}"
CONFIRM_H5_DEPLOY="${CONFIRM_H5_DEPLOY:-}"
INCLUDE_RECHARGE_ASSETS="${INCLUDE_RECHARGE_ASSETS:-0}"
STORE_SUBMISSION_CHECK="${STORE_SUBMISSION_CHECK:-0}"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
SSH_CMD=(ssh -i "$SSH_KEY")
RSYNC_CMD=(rsync -avz --progress -e "ssh -i $SSH_KEY")

section() {
  printf '\n== %s ==\n' "$1"
}

require_confirmation() {
  if [ "$DRY_RUN" = "1" ]; then
    return
  fi
  if [ "$CONFIRM_H5_DEPLOY" != "shianjieyouwu.com" ]; then
    echo "[ERROR] 这是生产 H5 静态资源部署。"
    echo "请显式运行: CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh"
    exit 1
  fi
}

require_dist() {
  for path in \
    "$LOCAL_DIR/dist/build/h5/index.html" \
    "$LOCAL_DIR/dist/build/h5/assets" \
    "$LOCAL_DIR/dist/build/h5/static"; do
    if [ ! -e "$path" ]; then
      echo "[ERROR] 缺少 H5 构建产物: $path"
      echo "请先运行: npm run build:h5"
      exit 1
    fi
  done
}

cd "$LOCAL_DIR"

section "确认生产 H5 部署边界"
require_confirmation
echo "目标服务器: $SERVER"
echo "目标目录: $H5_DIR"
echo "目标域名: $BASE_URL"
if [ "$INCLUDE_RECHARGE_ASSETS" = "1" ]; then
  echo "充值素材: 同步"
else
  echo "充值素材: 默认跳过 static/alipay-recharge.jpg（旧支付宝素材）"
fi
if [ "$STORE_SUBMISSION_CHECK" = "1" ]; then
  echo "商店提审严格检查: 执行"
else
  echo "商店提审严格检查: 跳过（网站部署默认只校验 H5 上线必需项）"
fi
if [ "$DRY_RUN" = "1" ]; then
  echo "模式: dry-run，不会修改线上文件。"
fi

section "构建 H5"
npm run build:h5
require_dist

section "本地发行检查"
LEGAL_URL_CHECK_SCOPE=website npm run store:legal-urls
npm run h5:legal-deploy-status

section "备份线上 H5 静态资源"
if [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: 跳过远端备份。"
else
  "${SSH_CMD[@]}" "$SERVER" "set -e
mkdir -p '$BACKUP_DIR'
if [ -d '$H5_DIR' ]; then
  tar -C '$H5_DIR' -czf '$BACKUP_DIR/h5-deploy-'\$(date -u +%Y%m%d-%H%M%S)'.tar.gz' index.html assets static 2>/dev/null || true
  ls -1t '$BACKUP_DIR'/h5-deploy-*.tar.gz 2>/dev/null | tail -n +31 | xargs -r rm -f
fi"
fi

section "同步 H5 前端产物"
RSYNC_FLAGS=()
if [ "$DRY_RUN" = "1" ]; then
  RSYNC_FLAGS+=(--dry-run)
fi
if [ "$INCLUDE_RECHARGE_ASSETS" != "1" ]; then
  RSYNC_FLAGS+=(--exclude '/static/alipay-recharge.jpg')
fi

if [ "$DRY_RUN" = "1" ]; then
  echo "dry-run: 不清理远端 assets。"
else
  "${SSH_CMD[@]}" "$SERVER" "rm -rf '$H5_DIR/assets'"
fi

"${RSYNC_CMD[@]}" "${RSYNC_FLAGS[@]}" \
  --exclude '/static/uploads/' \
  "$LOCAL_DIR/dist/build/h5/index.html" \
  "$LOCAL_DIR/dist/build/h5/assets" \
  "$LOCAL_DIR/dist/build/h5/static" \
  "$SERVER:$H5_DIR/"

if [ "$INCLUDE_RECHARGE_ASSETS" != "1" ] && [ "$DRY_RUN" != "1" ]; then
  "${SSH_CMD[@]}" "$SERVER" "rm -f '$H5_DIR/static/alipay-recharge.jpg'"
fi

if [ "$DRY_RUN" = "1" ]; then
  section "完成"
  echo "dry-run 完成，未修改线上。"
  exit 0
fi

section "部署后线上验证"
H5_LEGAL_DEPLOY_BASE_URL="$BASE_URL" npm run h5:legal-deploy-status -- --strict
LEGAL_URL_CHECK_SCOPE=website LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict
if [ "$STORE_SUBMISSION_CHECK" = "1" ]; then
  LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict
else
  echo "商店提审严格检查已跳过；准备上架前再运行 STORE_SUBMISSION_CHECK=1。"
fi
BASE_URL="$BASE_URL" bash scripts/production_monitor.sh

section "完成"
echo "H5 前端部署完成: $BASE_URL"
