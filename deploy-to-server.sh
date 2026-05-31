#!/bin/bash
# 时安解忧屋 - 一键部署
# 用法: bash deploy-to-server.sh

set -e
SERVER_USER="lighthouse"
SERVER="${SERVER_USER}@119.29.128.18"
SSH_KEY="$HOME/.ssh/deploy_key"
SSH_CMD="ssh -i $SSH_KEY"
RSYNC_CMD="rsync -avz --progress -e \"ssh -i $SSH_KEY\""
LOCAL_DIR="$(dirname "$0")"
LIVE_DB="/home/lighthouse/tianji/flask-source/backend/tianji.db"
DATABASE_URL="sqlite:////home/lighthouse/tianji/flask-source/backend/tianji.db"

echo "============================================"
echo " 时安解忧屋 - 部署到服务器"
echo "============================================"

# 1. 同步后端代码
echo "[1/4] 同步后端代码..."
eval "$RSYNC_CMD" \
    "$LOCAL_DIR/backend/app.py" \
    "$LOCAL_DIR/backend/bazi_engine.py" \
    "$LOCAL_DIR/backend/comprehensive_ai.py" \
    "$LOCAL_DIR/backend/deepseek_service.py" \
    "$LOCAL_DIR/backend/extensions.py" \
    "$LOCAL_DIR/backend/models.py" \
    "$LOCAL_DIR/backend/requirements.txt" \
    "$LOCAL_DIR/backend/tarot_engine.py" \
    "$LOCAL_DIR/backend/ziwei_engine.py" \
    "$SERVER:/opt/xuan-cet/backend/"

# 1b. 确保上传目录存在，使头像可被 Nginx 访问
$SSH_CMD "$SERVER" "sudo mkdir -p /var/www/xuan-cet/static/uploads; sudo chown -R lighthouse:lighthouse /var/www/xuan-cet/static/uploads"

# 2. 清理服务器旧的 assets（清理混合版本文件）
echo "[2/4] 清理旧文件..."
$SSH_CMD "$SERVER" "rm -rf /var/www/xuan-cet/assets/" && echo "  旧assets已清理" || echo "  ⚠️ 清理失败，尝试sudo..." && $SSH_CMD "$SERVER" "sudo rm -rf /var/www/xuan-cet/assets/"

# 3. 上传前端 dist
echo "[3/4] 上传前端..."
eval "$RSYNC_CMD" \
    --exclude '/static/uploads/' \
    "$LOCAL_DIR/dist/build/h5/index.html" \
    "$LOCAL_DIR/dist/build/h5/assets" \
    "$LOCAL_DIR/dist/build/h5/static" \
    "$SERVER:/var/www/xuan-cet/"

# 4. 重启后端
echo "[4/4] 重启后端..."
$SSH_CMD "$SERVER" "if [ -f '$LIVE_DB' ]; then cp '$LIVE_DB' '$LIVE_DB.bak-deploy-'\$(date +%Y%m%d-%H%M%S); else echo '[ERROR] 未找到线上生产库 $LIVE_DB，停止部署以避免创建空库'; exit 1; fi"
$SSH_CMD "$SERVER" "cd /opt/xuan-cet/backend && ./venv/bin/pip install -q -r requirements.txt"
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
$SSH_CMD "$SERVER" "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:5199/ 2>/dev/null" | grep -q 200 && echo "  后端 200 OK" || echo "  ⚠️ 后端可能未正常启动，检查: sudo journalctl -u xuan-cet-flask -n 80"

echo ""
echo "============================================"
echo " 部署完成！访问: http://119.29.128.18"
echo "============================================"
