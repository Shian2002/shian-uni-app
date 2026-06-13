#!/usr/bin/env bash
# 安装测试环境 Nginx 入口。只配置测试站，不修改正式站配置。

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"

STAGING_FRONTEND_DIR="${STAGING_FRONTEND_DIR:-/var/www/xuan-cet-staging}"
STAGING_UPLOAD_FOLDER="${STAGING_UPLOAD_FOLDER:-$STAGING_FRONTEND_DIR/static/uploads}"
STAGING_PORT="${STAGING_PORT:-5299}"
STAGING_LISTEN="${STAGING_LISTEN:-8081}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/conf.d/xuan-cet-staging.conf}"

SSH_CMD=(ssh -i "$SSH_KEY")

echo "安装测试环境 Nginx 入口: http://$SERVER_HOST:$STAGING_LISTEN"

"${SSH_CMD[@]}" "$SERVER" "set -e
sudo mkdir -p '$STAGING_FRONTEND_DIR' '$STAGING_UPLOAD_FOLDER'
sudo tee '$NGINX_CONF' > /dev/null <<'EOF'
server {
    listen $STAGING_LISTEN;
    server_name _;

    root $STAGING_FRONTEND_DIR;
    index index.html;

    client_max_body_size 5m;

    location /api/ {
        proxy_pass http://127.0.0.1:$STAGING_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location /static/uploads/ {
        alias $STAGING_UPLOAD_FOLDER/;
        expires 7d;
        add_header Cache-Control \"public\";
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
sudo nginx -t
sudo systemctl reload nginx
"

echo "测试环境 Nginx 入口已安装。"
