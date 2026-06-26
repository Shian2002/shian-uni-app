#!/usr/bin/env bash
# 时安解忧屋 - 部署到测试环境
# 用法: bash deploy-to-staging.sh
# 可选: SKIP_PREFLIGHT=1 bash deploy-to-staging.sh 跳过本地检查
# 可选: RUN_STAGING_QA=1 bash deploy-to-staging.sh 部署后运行测试环境回归

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"

STAGING_FRONTEND_DIR="${STAGING_FRONTEND_DIR:-/var/www/xuan-cet-staging}"
STAGING_BACKEND_DIR="${STAGING_BACKEND_DIR:-/opt/xuan-cet-staging/backend}"
STAGING_UPLOAD_FOLDER="${STAGING_UPLOAD_FOLDER:-$STAGING_FRONTEND_DIR/static/uploads}"
STAGING_DB="${STAGING_DB:-/home/lighthouse/tianji-staging/backend/tianji.db}"
STAGING_DATABASE_URL="${STAGING_DATABASE_URL:-sqlite:///$STAGING_DB}"
STAGING_SERVICE="${STAGING_SERVICE:-xuan-cet-staging-flask}"
STAGING_PORT="${STAGING_PORT:-5299}"
STAGING_BASE_URL="${STAGING_BASE_URL:-http://119.29.128.18}"

SSH_CMD=(ssh -i "$SSH_KEY")
RSYNC_CMD=(rsync -avz --progress -e "ssh -i $SSH_KEY")

require_clean_backend_python() {
    if ! git -C "$LOCAL_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "[ERROR] 当前目录不是 Git 工作树，停止部署以避免同步未受版本控制的后端代码"
        exit 1
    fi

    local dirty_backend
    dirty_backend="$(git -C "$LOCAL_DIR" status --porcelain -- 'backend/*.py')"
    if [ -n "$dirty_backend" ]; then
        echo "[ERROR] 检测到未提交的后端 Python 改动，停止部署以避免测试环境代码和 Git 不一致"
        echo "$dirty_backend"
        echo "请先提交、暂存到其他分支，或明确处理这些改动后再部署。"
        exit 1
    fi
}

echo "============================================"
echo " 时安解忧屋 - 部署到测试环境"
echo "============================================"
echo "后端服务: $STAGING_SERVICE"
echo "后端端口: $STAGING_PORT"
echo "前端目录: $STAGING_FRONTEND_DIR"
echo "数据库: $STAGING_DB"
echo "访问地址: $STAGING_BASE_URL"

require_clean_backend_python

if [ "${SKIP_PREFLIGHT:-0}" = "1" ]; then
    echo "[0/6] 已按 SKIP_PREFLIGHT=1 跳过部署前检查"
else
    echo "[0/6] 部署前检查..."
    bash "$LOCAL_DIR/scripts/preflight_release.sh"
fi

echo "[1/6] 准备远端测试环境目录..."
"${SSH_CMD[@]}" "$SERVER" "set -e
sudo mkdir -p '$STAGING_BACKEND_DIR' '$STAGING_UPLOAD_FOLDER' '$(dirname "$STAGING_DB")'
sudo chown -R '$SERVER_USER:$SERVER_USER' '$(dirname "$STAGING_BACKEND_DIR")' '$STAGING_FRONTEND_DIR' '$(dirname "$STAGING_DB")'
if [ ! -f '$STAGING_DB' ]; then
  echo '[ERROR] 未找到测试库 $STAGING_DB'
  echo '请先运行: bash scripts/sync_staging_db_from_prod.sh'
  exit 1
fi"

echo "[2/6] 同步后端代码..."
"${RSYNC_CMD[@]}" \
    "$LOCAL_DIR/backend/"*.py \
    "$LOCAL_DIR/backend/constraints.txt" \
    "$LOCAL_DIR/backend/requirements.txt" \
    "$SERVER:$STAGING_BACKEND_DIR/"

"${SSH_CMD[@]}" "$SERVER" "mkdir -p '$STAGING_BACKEND_DIR/scripts'"
"${RSYNC_CMD[@]}" \
    "$LOCAL_DIR/scripts/"*.py \
    "$SERVER:$STAGING_BACKEND_DIR/scripts/"

echo "[3/6] 清理并上传测试前端..."
"${SSH_CMD[@]}" "$SERVER" "rm -rf '$STAGING_FRONTEND_DIR/assets'"
"${RSYNC_CMD[@]}" \
    --exclude '/static/uploads/' \
    "$LOCAL_DIR/dist/build/h5/index.html" \
    "$LOCAL_DIR/dist/build/h5/assets" \
    "$LOCAL_DIR/dist/build/h5/static" \
    "$SERVER:$STAGING_FRONTEND_DIR/"

echo "[4/6] 安装依赖并写入测试服务..."
"${SSH_CMD[@]}" "$SERVER" "set -e
cd '$STAGING_BACKEND_DIR'
if [ ! -d venv ]; then python3 -m venv venv; fi
./venv/bin/pip install -q -c constraints.txt -r requirements.txt
sudo tee /etc/systemd/system/$STAGING_SERVICE.service > /dev/null <<'EOF'
[Unit]
Description=时安解忧屋 Staging Gunicorn Backend
After=network.target

[Service]
Type=simple
User=$SERVER_USER
WorkingDirectory=$STAGING_BACKEND_DIR
Environment=APP_ENV=staging
Environment=FLASK_ENV=staging
Environment=DATABASE_URL=$STAGING_DATABASE_URL
Environment=UPLOAD_FOLDER=$STAGING_UPLOAD_FOLDER
Environment=OAUTH_ORIGIN=$STAGING_BASE_URL
Environment=STAGING_SMS_MODE=log
Environment=STAGING_EMAIL_MODE=log
Environment=STAGING_PAYMENT_MODE=manual
EnvironmentFile=-$STAGING_BACKEND_DIR/.env
ExecStart=$STAGING_BACKEND_DIR/venv/bin/gunicorn --workers 1 --threads 4 --timeout 180 --bind 127.0.0.1:$STAGING_PORT app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable '$STAGING_SERVICE' >/dev/null
sudo systemctl restart '$STAGING_SERVICE'"

echo "[5/6] 校验测试服务环境..."
sleep 2
RUNTIME_ENV="$("${SSH_CMD[@]}" "$SERVER" "systemctl show '$STAGING_SERVICE' -p Environment --value")"
if ! grep -q "APP_ENV=staging" <<<"$RUNTIME_ENV"; then
    echo "[ERROR] 运行中 APP_ENV 不符合预期"
    echo "$RUNTIME_ENV"
    exit 1
fi
if ! grep -q "DATABASE_URL=$STAGING_DATABASE_URL" <<<"$RUNTIME_ENV"; then
    echo "[ERROR] 运行中 DATABASE_URL 未指向测试库"
    echo "预期: DATABASE_URL=$STAGING_DATABASE_URL"
    echo "实际: $RUNTIME_ENV"
    exit 1
fi
"${SSH_CMD[@]}" "$SERVER" "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:$STAGING_PORT/ 2>/dev/null" | grep -q 200
echo "测试后端 200 OK，且 DATABASE_URL 已确认指向测试库"

echo "[6/6] 测试环境回归..."
if [ "${RUN_STAGING_QA:-0}" = "1" ]; then
    QA_BASE_URL="$STAGING_BASE_URL" npm run qa:staging
else
    echo "已跳过。需要时运行: RUN_STAGING_QA=1 bash deploy-to-staging.sh"
fi

echo ""
echo "============================================"
echo " 测试环境部署完成！访问: $STAGING_BASE_URL"
echo "============================================"
