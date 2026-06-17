#!/bin/bash
# 时安解忧屋 macOS 启动脚本（开发者模式 - 绕过签名检查）
# 用法: 在真实终端中运行 bash start-macos-dev.sh
#
# 此脚本直接用Electron运行源码，不需要签名
# 适用于开发和测试阶段

cd "$(dirname "$0")"

DESKTOP_DIR="./desktop"
H5_BUILD="./dist/build/h5"

echo "========================================"
echo "  时安解忧屋 - macOS 开发者模式启动"
echo "========================================"

# 检查H5构建是否存在
if [ ! -f "$H5_BUILD/index.html" ]; then
    echo "H5构建不存在，正在构建..."
    npm run build:h5
fi

# 检查electron是否安装
if [ ! -f "$DESKTOP_DIR/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron" ]; then
    echo "安装Electron依赖..."
    cd "$DESKTOP_DIR" && npm install && cd ..
fi

echo ""
echo "启动桌面应用..."
echo "后端API代理到: https://shianjieyouwu.com"
echo ""

cd "$DESKTOP_DIR" && npx electron .
