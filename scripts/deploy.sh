#!/bin/bash
# 时安解忧屋 全量部署脚本 (H5 + Flask 后端)
# 用法: bash deploy.sh
set -e

# === 配置 ===
DOMAIN=""                     # 域名（留空则用 IP）
H5_DIR="/var/www/xuan-cet"    # H5 静态文件根目录
FLASK_DIR="/opt/xuan-cet/backend"  # Flask 后端目录
FLASK_PORT=5199               # Flask 端口
FLASK_USER="lighthouse"       # 运行 Flask 的系统用户
DATABASE_URL="sqlite:////opt/xuan-cet/backend/tianji.db"  # 线上生产库，部署脚本禁止覆盖
NGINX_CONF="/etc/nginx/sites-available/xuan-cet"
NGINX_ENABLED="/etc/nginx/sites-enabled/xuan-cet"
SERVER_IP="119.29.128.18"

echo "=========================================="
echo "  时安解忧屋 部署脚本"
echo "=========================================="

# ─── 1. 系统依赖 ───
echo ""
echo "=== 1. 安装系统依赖 ==="
sudo apt-get update
sudo apt-get install -y nginx python3 python3-pip python3-venv

# ─── 2. Flask 后端 ───
echo ""
echo "=== 2. 部署 Flask 后端 ==="
sudo mkdir -p "$FLASK_DIR"

# 如果当前目录有 backend 文件夹，复制过去，但永远不复制 SQLite 数据库。
# 线上 tianji.db 是生产数据，只能通过单独、显式、有备份的流程同步。
if [ -d "./flask-source/backend" ]; then
  sudo find ./flask-source/backend -mindepth 1 -maxdepth 1 \
    ! -name 'tianji.db' ! -name 'tianji.db-*' ! -name 'tianji.db.*' \
    ! -name '.env' \
    -exec cp -r {} "$FLASK_DIR/" \;
elif [ -d "../flask-source/backend" ]; then
  sudo find ../flask-source/backend -mindepth 1 -maxdepth 1 \
    ! -name 'tianji.db' ! -name 'tianji.db-*' ! -name 'tianji.db.*' \
    ! -name '.env' \
    -exec cp -r {} "$FLASK_DIR/" \;
fi

# 创建虚拟环境并安装依赖
sudo python3 -m venv "$FLASK_DIR/venv"
sudo "$FLASK_DIR/venv/bin/pip" install --upgrade pip
sudo "$FLASK_DIR/venv/bin/pip" install -r "$FLASK_DIR/requirements.txt" || echo "[WARN] pip install 部分失败，请手动检查"

# 修正 app.py 中 PAIPAN_DIR 路径（服务器上不需要排盘脚本）
sudo sed -i "s|os.path.expanduser('~/WorkBuddy/Claw')|'/opt/xuan-cet/paipan'|" "$FLASK_DIR/app.py" 2>/dev/null || true
# 确保上传目录存在且有写权限
sudo mkdir -p "$H5_DIR/static/uploads"
sudo chown -R $FLASK_USER:$FLASK_USER "$H5_DIR/static/uploads"

# 后端启动会执行 create_all/轻量迁移；重启前先备份生产库，便于回滚。
if [ -f "$FLASK_DIR/tianji.db" ]; then
  DB_BACKUP="$FLASK_DIR/tianji.db.bak-deploy-$(date +%Y%m%d-%H%M%S)"
  sudo cp "$FLASK_DIR/tianji.db" "$DB_BACKUP"
  sudo chown $FLASK_USER:$FLASK_USER "$DB_BACKUP"
  echo "  已备份生产数据库: $DB_BACKUP"
else
  echo "  [ERROR] 未找到 $FLASK_DIR/tianji.db；为避免静默创建空库，部署已停止。"
  exit 1
fi

# 创建 .env（如果不存在）
if [ ! -f "$FLASK_DIR/.env" ] && [ -f "./flask-source/backend/.env" ]; then
  sudo cp ./flask-source/backend/.env "$FLASK_DIR/"
fi

# 创建 systemd 服务
sudo tee /etc/systemd/system/xuan-cet-flask.service > /dev/null << EOF
[Unit]
Description=时安解忧屋 Flask Backend
After=network.target

[Service]
Type=simple
User=$FLASK_USER
WorkingDirectory=$FLASK_DIR
Environment=FLASK_ENV=production
Environment=DATABASE_URL=$DATABASE_URL
Environment=UPLOAD_FOLDER=$H5_DIR/static/uploads
ExecStart=$FLASK_DIR/venv/bin/python app.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 启动 Flask
sudo systemctl daemon-reload
sudo systemctl enable xuan-cet-flask
sudo systemctl restart xuan-cet-flask
echo "  Flask 后端状态:"
sudo systemctl status xuan-cet-flask --no-pager | grep "Active:"

# ─── 3. H5 静态文件 ───
echo ""
echo "=== 3. 部署 H5 前端 ==="
sudo mkdir -p "$H5_DIR"
sudo mkdir -p "$H5_DIR/static/uploads"
echo "  请手动上传 H5 构建产物:"
echo "  注意：static/uploads 是用户上传头像目录，部署前端时不要覆盖或删除。"
echo "  推荐：rsync -a --exclude='/static/uploads/' dist/build/h5/ lighthouse@$SERVER_IP:$H5_DIR/"

# ─── 4. Nginx 配置 ───
echo ""
echo "=== 4. 配置 Nginx ==="
SERVER_NAME="${DOMAIN:-119.29.128.18}"
sudo tee "$NGINX_CONF" > /dev/null << NGINX
server {
    listen 80;
    server_name $SERVER_NAME;
    root $H5_DIR;
    index index.html;

    gzip on;
    gzip_types text/css application/javascript application/json image/svg+xml;
    gzip_min_length 1024;

    location /assets/ {
        expires 6M;
        add_header Cache-Control "public, immutable";
    }
    location /static/ {
        expires 6M;
        add_header Cache-Control "public, immutable";
    }
    location / {
        try_files \$uri \$uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://127.0.0.1:$FLASK_PORT;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
NGINX

sudo ln -sf "$NGINX_CONF" "$NGINX_ENABLED" 2>/dev/null || true
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

# ─── 5. 完成 ───
echo ""
echo "=========================================="
echo "  部署完成！"
echo "=========================================="
echo "  前端地址: http://$SERVER_NAME"
echo "  API 地址: http://$SERVER_NAME/api/"
echo ""
echo "后续步骤:"
echo "  1. 上传 H5 构建产物:"
echo "     rsync -a --exclude='/static/uploads/' dist/build/h5/ lighthouse@$SERVER_IP:$H5_DIR/"
echo ""
echo "  2. 绑定域名后申请 SSL:"
echo "     sudo apt install -y certbot python3-certbot-nginx"
echo "     sudo certbot --nginx -d 你的域名"
echo ""
echo "  3. 检查 Flask 日志:"
echo "     sudo journalctl -u xuan-cet-flask -f"
echo ""
