#!/usr/bin/env bash
# 安装百度网盘异地备份 timer。实际百度授权需要在服务器上由用户完成。

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"
SSH_CMD=(ssh -i "$SSH_KEY")
SCP_CMD=(scp -i "$SSH_KEY")

REMOTE_OPS_DIR="${REMOTE_OPS_DIR:-/opt/xuan-cet/ops}"
REMOTE_SCRIPT="$REMOTE_OPS_DIR/upload_baidu_backup.sh"
REMOTE_VENV="${REMOTE_VENV:-$REMOTE_OPS_DIR/baidu-venv}"
ENV_FILE="${BAIDU_BACKUP_ENV_FILE:-/etc/xuan-cet-baidu-backup.env}"
TIMER_TIME="${BAIDU_TIMER_TIME:-04:10}"
BAIDU_REMOTE_DIR="${BAIDU_REMOTE_DIR:-/xuan-cet/db}"
BAIDU_KEEP_REMOTE="${BAIDU_KEEP_REMOTE:-60}"
BYPY_TIMEOUT="${BYPY_TIMEOUT:-300}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== 安装百度网盘异地备份 =="
echo "服务器: $SERVER"
echo "远端目录: $BAIDU_REMOTE_DIR"
echo "远端保留份数: $BAIDU_KEEP_REMOTE"
echo "每日时间: $TIMER_TIME"
echo "单个 bypy 命令超时: ${BYPY_TIMEOUT} 秒"

"${SSH_CMD[@]}" "$SERVER" "mkdir -p '$REMOTE_OPS_DIR'"
"${SCP_CMD[@]}" "$ROOT_DIR/scripts/upload_baidu_backup.sh" "$SERVER:$REMOTE_SCRIPT"

"${SSH_CMD[@]}" "$SERVER" "set -euo pipefail
chmod 755 '$REMOTE_SCRIPT'
python3 -m venv '$REMOTE_VENV'
'$REMOTE_VENV/bin/python' -m pip install -q --upgrade pip
'$REMOTE_VENV/bin/python' -m pip install -q bypy
sudo touch '$ENV_FILE'
sudo chmod 600 '$ENV_FILE'
if sudo grep -q '^BAIDU_REMOTE_DIR=' '$ENV_FILE'; then
  sudo sed -i 's#^BAIDU_REMOTE_DIR=.*#BAIDU_REMOTE_DIR=$BAIDU_REMOTE_DIR#' '$ENV_FILE'
else
  echo 'BAIDU_REMOTE_DIR=$BAIDU_REMOTE_DIR' | sudo tee -a '$ENV_FILE' >/dev/null
fi
if sudo grep -q '^BAIDU_KEEP_REMOTE=' '$ENV_FILE'; then
  sudo sed -i 's#^BAIDU_KEEP_REMOTE=.*#BAIDU_KEEP_REMOTE=$BAIDU_KEEP_REMOTE#' '$ENV_FILE'
else
  echo 'BAIDU_KEEP_REMOTE=$BAIDU_KEEP_REMOTE' | sudo tee -a '$ENV_FILE' >/dev/null
fi
if sudo grep -q '^BYPY_TIMEOUT=' '$ENV_FILE'; then
  sudo sed -i 's#^BYPY_TIMEOUT=.*#BYPY_TIMEOUT=$BYPY_TIMEOUT#' '$ENV_FILE'
else
  echo 'BYPY_TIMEOUT=$BYPY_TIMEOUT' | sudo tee -a '$ENV_FILE' >/dev/null
fi
sudo tee /usr/local/bin/xuan-cet-baidu-backup >/dev/null <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
export PATH='$REMOTE_VENV/bin':\"\$PATH\"
'$REMOTE_SCRIPT'
EOF
sudo chmod 755 /usr/local/bin/xuan-cet-baidu-backup
sudo tee /etc/systemd/system/xuan-cet-baidu-backup.service >/dev/null <<'EOF'
[Unit]
Description=时安解忧屋百度网盘异地备份
After=network.target xuan-cet-db-backup.service

[Service]
Type=oneshot
User=$SERVER_USER
EnvironmentFile=-$ENV_FILE
ExecStart=/usr/local/bin/xuan-cet-baidu-backup
EOF
sudo tee /etc/systemd/system/xuan-cet-baidu-backup.timer >/dev/null <<'EOF'
[Unit]
Description=每日执行时安解忧屋百度网盘异地备份

[Timer]
OnCalendar=*-*-* $TIMER_TIME:00
Persistent=true
RandomizedDelaySec=600

[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload
if sudo grep -q '^BAIDU_BACKUP_PASSPHRASE=' '$ENV_FILE'; then
  sudo systemctl enable --now xuan-cet-baidu-backup.timer >/dev/null
else
  echo '[WARN] 未配置 BAIDU_BACKUP_PASSPHRASE，暂不启用 timer。完成百度授权和加密密码配置后再 enable --now。'
fi
systemctl list-timers --all xuan-cet-baidu-backup.timer --no-pager || true
"

echo "== 百度网盘异地备份 timer 已安装 =="
echo "还需要在服务器上完成两步授权/密钥配置："
echo "1. ssh -i \"$SSH_KEY\" $SERVER 'export PATH=\"$REMOTE_VENV/bin:\$PATH\"; bypy info'"
echo "2. ssh -i \"$SSH_KEY\" $SERVER 'echo BAIDU_BACKUP_PASSPHRASE=强密码 | sudo tee -a $ENV_FILE >/dev/null'"
echo "完成后手动测试："
echo "ssh -i \"$SSH_KEY\" $SERVER 'sudo systemctl start xuan-cet-baidu-backup.service && sudo journalctl -u xuan-cet-baidu-backup.service -n 80 --no-pager'"
echo "测试通过后启用定时器："
echo "ssh -i \"$SSH_KEY\" $SERVER 'sudo systemctl enable --now xuan-cet-baidu-backup.timer'"
