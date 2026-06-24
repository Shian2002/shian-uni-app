#!/bin/bash
# 时安解忧屋 - 一键部署
# 用法: bash deploy-to-server.sh
# 可选: SKIP_PREFLIGHT=1 bash deploy-to-server.sh 跳过部署前检查
# 可选: SKIP_ONLINE_QA=1 bash deploy-to-server.sh 跳过部署后线上回归

set -e
SERVER_USER="lighthouse"
SERVER="${SERVER_USER}@119.29.128.18"
SSH_KEY="$HOME/.ssh/deploy_key"
SSH_CMD="ssh -i $SSH_KEY"
RSYNC_CMD="rsync -avz --progress -e \"ssh -i $SSH_KEY\""
LOCAL_DIR="$(cd "$(dirname "$0")" && pwd)"
LIVE_DB="/home/lighthouse/tianji/flask-source/backend/tianji.db"
DATABASE_URL="sqlite:////home/lighthouse/tianji/flask-source/backend/tianji.db"
DB_BACKUP_DIR="/home/lighthouse/backups/xuan-cet/db"

require_clean_backend_python() {
    if ! git -C "$LOCAL_DIR" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        echo "[ERROR] 当前目录不是 Git 工作树，停止部署以避免同步未受版本控制的后端代码"
        exit 1
    fi

    local dirty_backend
    dirty_backend="$(git -C "$LOCAL_DIR" status --porcelain -- 'backend/*.py')"
    if [ -n "$dirty_backend" ]; then
        echo "[ERROR] 检测到未提交的后端 Python 改动，停止部署以避免线上代码和 Git 不一致"
        echo "$dirty_backend"
        echo "请先提交、暂存到其他分支，或明确处理这些改动后再部署。"
        exit 1
    fi
}

echo "============================================"
echo " 时安解忧屋 - 部署到服务器"
echo "============================================"

require_clean_backend_python

if [ "${SKIP_PREFLIGHT:-0}" = "1" ]; then
    echo "[0/5] 已按 SKIP_PREFLIGHT=1 跳过部署前检查"
else
    echo "[0/5] 部署前检查..."
    bash "$LOCAL_DIR/scripts/preflight_release.sh"
fi

# 1. 同步后端代码
echo "[1/5] 同步后端代码..."
eval "$RSYNC_CMD" \
    "$LOCAL_DIR/backend/"*.py \
    "$LOCAL_DIR/backend/constraints.txt" \
    "$LOCAL_DIR/backend/requirements.txt" \
    "$SERVER:/opt/xuan-cet/backend/"

$SSH_CMD "$SERVER" "mkdir -p /opt/xuan-cet/backend/scripts"
eval "$RSYNC_CMD" \
    "$LOCAL_DIR/scripts/"*.py \
    "$SERVER:/opt/xuan-cet/backend/scripts/"

# 1b. 确保上传目录存在，使头像可被 Nginx 访问
$SSH_CMD "$SERVER" "sudo mkdir -p /var/www/xuan-cet/static/uploads; sudo chown -R lighthouse:lighthouse /var/www/xuan-cet/static/uploads"

# 2. 清理服务器旧的 assets（清理混合版本文件）
echo "[2/5] 清理旧文件..."
$SSH_CMD "$SERVER" "rm -rf /var/www/xuan-cet/assets/" && echo "  旧assets已清理" || echo "  ⚠️ 清理失败，尝试sudo..." && $SSH_CMD "$SERVER" "sudo rm -rf /var/www/xuan-cet/assets/"

# 3. 上传前端 dist
echo "[3/5] 上传前端..."
eval "$RSYNC_CMD" \
    --exclude '/static/uploads/' \
    "$LOCAL_DIR/dist/build/h5/index.html" \
    "$LOCAL_DIR/dist/build/h5/robots.txt" \
    "$LOCAL_DIR/dist/build/h5/sitemap.xml" \
    "$LOCAL_DIR/dist/build/h5/manifest.json" \
    "$LOCAL_DIR/dist/build/h5/indexnow-key.txt" \
    "$LOCAL_DIR/dist/build/h5/assets" \
    "$LOCAL_DIR/dist/build/h5/static" \
    "$SERVER:/var/www/xuan-cet/"

# 4. 重启后端
echo "[4/5] 重启后端..."
$SSH_CMD "$SERVER" "if [ -f '$LIVE_DB' ]; then mkdir -p '$DB_BACKUP_DIR'; cp '$LIVE_DB' '$DB_BACKUP_DIR/tianji-deploy-'\$(date -u +%Y%m%d-%H%M%S)'.db'; chmod 600 '$DB_BACKUP_DIR'/tianji-deploy-*.db; ls -1t '$DB_BACKUP_DIR'/tianji-deploy-*.db | tail -n +31 | xargs -r rm -f; else echo '[ERROR] 未找到线上生产库 $LIVE_DB，停止部署以避免创建空库'; exit 1; fi"
$SSH_CMD "$SERVER" "cd /opt/xuan-cet/backend && ./venv/bin/pip install -q -c constraints.txt -r requirements.txt"
$SSH_CMD "$SERVER" "sudo tee /etc/systemd/system/xuan-cet-flask.service > /dev/null <<'EOF'
[Unit]
Description=时安解忧屋 Gunicorn Backend
After=network.target

[Service]
Type=simple
User=$SERVER_USER
WorkingDirectory=/opt/xuan-cet/backend
Environment=FLASK_ENV=production
Environment=DATABASE_URL=$DATABASE_URL
Environment=UPLOAD_FOLDER=/var/www/xuan-cet/static/uploads
EnvironmentFile=-/opt/xuan-cet/backend/.env
ExecStart=/opt/xuan-cet/backend/venv/bin/gunicorn --workers 2 --threads 4 --timeout 180 --bind 127.0.0.1:5199 app:app
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF"
$SSH_CMD "$SERVER" "sudo systemctl daemon-reload && sudo systemctl enable xuan-cet-flask >/dev/null && sudo systemctl restart xuan-cet-flask"
sleep 2
echo "  等待服务启动..."
RUNTIME_ENV="$($SSH_CMD "$SERVER" "systemctl show xuan-cet-flask -p Environment --value")"
EXPECTED_DATABASE_URL_ENV="DATABASE_URL=sqlite:////home/lighthouse/tianji/flask-source/backend/tianji.db"
if ! grep -q "$EXPECTED_DATABASE_URL_ENV" <<<"$RUNTIME_ENV"; then
    echo "  [ERROR] 运行中 DATABASE_URL 不符合预期，停止部署验活以避免误用空库"
    echo "  预期: $EXPECTED_DATABASE_URL_ENV"
    echo "  实际: $RUNTIME_ENV"
    exit 1
fi
echo "  DATABASE_URL 已确认指向生产库"
$SSH_CMD "$SERVER" "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5199/ 2>/dev/null" | grep -q 200 && echo "  后端 200 OK" || echo "  ⚠️ 后端可能未正常启动，检查: sudo journalctl -u xuan-cet-flask -n 80"

# 5. 部署后线上验活
echo "[5/5] 线上验活..."
if [ -x "$LOCAL_DIR/scripts/production_monitor.sh" ]; then
    bash "$LOCAL_DIR/scripts/production_monitor.sh"
else
    echo "  ⚠️ 未找到 production_monitor.sh，跳过基础监控"
fi

if [ "${SKIP_ONLINE_QA:-0}" = "1" ]; then
    echo "  已按 SKIP_ONLINE_QA=1 跳过浏览器线上回归"
else
    npm run qa:online
fi

echo ""
echo "============================================"
echo " 部署完成！访问: https://shianjieyouwu.com/"
echo "============================================"
