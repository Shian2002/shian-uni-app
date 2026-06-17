#!/bin/bash
# 时安解忧屋 macOS 启动脚本
# 用法: 双击此文件 或 终端 bash start-macos.sh
#
# 如果应用无法启动，请:
# 1. 打开 系统设置 → 隐私与安全性
# 2. 找到被阻止的"时安解忧屋"应用
# 3. 点击"仍要打开"
# 4. 然后重新运行此脚本

APP_PATH="/Applications/时安解忧屋.app"
FALLBACK_PATH="$(dirname "$0")/desktop/release/mac-arm64/时安解忧屋.app"

echo "时安解忧屋 启动中..."

# 清除隔离属性
xattr -cr "$APP_PATH" 2>/dev/null
xattr -cr "$FALLBACK_PATH" 2>/dev/null

# 尝试从 /Applications 启动
if [ -d "$APP_PATH" ]; then
    open "$APP_PATH" 2>/dev/null
    echo "已尝试从 /Applications 启动"
# 回退到项目目录
elif [ -d "$FALLBACK_PATH" ]; then
    open "$FALLBACK_PATH" 2>/dev/null
    echo "已尝试从项目目录启动"
else
    echo "错误: 找不到时安解忧屋.app"
    echo "请先运行: open \"\$(dirname \$0)/desktop/release/时安解忧屋-1.0.0-arm64.dmg\""
    exit 1
fi

echo ""
echo "如果应用没有出现，请:"
echo "  1. 打开 系统设置 → 隐私与安全性"
echo "  2. 点击底部的 '仍要打开' 按钮"
echo "  3. 再次运行此脚本"
echo ""
echo "或使用 H5 网页版: open http://127.0.0.1:3003/"
