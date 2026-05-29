#!/bin/bash
# 从服务器下载后端代码和数据库到本地
# 运行方式: bash download-from-server.sh

SERVER="root@119.29.128.18"
REMOTE_DIR="/opt/xuan-cet/backend"
LOCAL_DIR="$(dirname "$0")/server-backup"

mkdir -p "$LOCAL_DIR/backend"
mkdir -p "$LOCAL_DIR/database"

echo "正在从 $SERVER 下载后端文件..."

# 下载后端代码（排除 venv 和备份文件）
rsync -avz --progress \
  --exclude='venv/' \
  --exclude='*.bak*' \
  --exclude='__pycache__/' \
  --exclude='*.pyc' \
  "$SERVER:$REMOTE_DIR/" \
  "$LOCAL_DIR/backend/"

# 数据库单独放
cp "$LOCAL_DIR/backend/tianji.db" "$LOCAL_DIR/database/tianji.db" 2>/dev/null

echo ""
echo "============================================"
echo "下载完成！"
echo "  后端代码: $LOCAL_DIR/backend/"
echo "  数据库:   $LOCAL_DIR/database/tianji.db"
echo "============================================"
