#!/bin/bash
# 时安解忧屋 H5 本地预览启动器
# 功能: 启动本地服务器，在浏览器中使用所有功能
# 用法: 双击此文件 或 终端 bash start-h5-preview.sh

cd "$(dirname "$0")"
PORT=3003

# 检查是否已在运行
if curl -s -o /dev/null "http://127.0.0.1:$PORT/" 2>/dev/null; then
    echo "时安解忧屋已在运行，打开浏览器..."
    open "http://127.0.0.1:$PORT/"
    exit 0
fi

echo "启动时安解忧屋 H5 预览服务器..."
echo "后端API代理到: https://shianjieyouwu.com"
echo "访问地址: http://127.0.0.1:$PORT/"
echo ""
echo "按 Ctrl+C 停止服务器"
echo ""

exec /Users/junj/.workbuddy/binaries/node/versions/22.22.2/bin/node scripts/preview-server.js
