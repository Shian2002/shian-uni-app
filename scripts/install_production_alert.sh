#!/usr/bin/env bash
# 安装线上健康自动告警 timer。SMTP 密码与机器人 webhook 从环境文件读取，不写入代码。

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"
SSH_CMD=(ssh -i "$SSH_KEY")
SCP_CMD=(scp -i "$SSH_KEY")

REMOTE_OPS_DIR="${REMOTE_OPS_DIR:-/opt/xuan-cet/ops}"
REMOTE_ALERT_PY="$REMOTE_OPS_DIR/production_alert.py"
ALERT_ENV_FILE="${ALERT_ENV_FILE:-/etc/xuan-cet-alert.env}"
ALERT_EMAIL_TO="${ALERT_EMAIL_TO:-}"
ALERT_INTERVAL_MIN="${ALERT_INTERVAL_MIN:-10}"
ALERT_BASE_URL="${ALERT_BASE_URL:-http://119.29.128.18}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== 安装线上健康自动告警 =="
echo "服务器: $SERVER"
echo "检查间隔: ${ALERT_INTERVAL_MIN} 分钟"
echo "邮箱收件人: ${ALERT_EMAIL_TO:-未设置}"

"${SSH_CMD[@]}" "$SERVER" "mkdir -p '$REMOTE_OPS_DIR'"
"${SCP_CMD[@]}" "$ROOT_DIR/scripts/production_alert.py" "$SERVER:$REMOTE_ALERT_PY"

"${SSH_CMD[@]}" "$SERVER" "set -euo pipefail
sudo touch '$ALERT_ENV_FILE'
sudo chmod 600 '$ALERT_ENV_FILE'
if ! sudo grep -q '^ALERT_BASE_URL=' '$ALERT_ENV_FILE'; then
  echo 'ALERT_BASE_URL=$ALERT_BASE_URL' | sudo tee -a '$ALERT_ENV_FILE' >/dev/null
fi
if [ -n '$ALERT_EMAIL_TO' ]; then
  if sudo grep -q '^ALERT_EMAIL_TO=' '$ALERT_ENV_FILE'; then
    sudo sed -i 's#^ALERT_EMAIL_TO=.*#ALERT_EMAIL_TO=$ALERT_EMAIL_TO#' '$ALERT_ENV_FILE'
  else
    echo 'ALERT_EMAIL_TO=$ALERT_EMAIL_TO' | sudo tee -a '$ALERT_ENV_FILE' >/dev/null
  fi
fi
sudo tee /usr/local/bin/xuan-cet-alert-check >/dev/null <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
/usr/bin/python3 '$REMOTE_ALERT_PY'
EOF
sudo chmod 755 /usr/local/bin/xuan-cet-alert-check
sudo tee /etc/systemd/system/xuan-cet-alert-check.service >/dev/null <<'EOF'
[Unit]
Description=时安解忧屋线上健康告警检查
After=network.target xuan-cet-flask.service

[Service]
Type=oneshot
User=$SERVER_USER
EnvironmentFile=-/opt/xuan-cet/backend/.env
EnvironmentFile=-$ALERT_ENV_FILE
ExecStart=/usr/local/bin/xuan-cet-alert-check
EOF
sudo tee /etc/systemd/system/xuan-cet-alert-check.timer >/dev/null <<'EOF'
[Unit]
Description=定时执行时安解忧屋线上健康告警检查

[Timer]
OnBootSec=3min
OnUnitActiveSec=${ALERT_INTERVAL_MIN}min
Persistent=true

[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now xuan-cet-alert-check.timer >/dev/null
sudo systemctl start xuan-cet-alert-check.service
systemctl list-timers --all xuan-cet-alert-check.timer --no-pager
sudo systemctl status xuan-cet-alert-check.service --no-pager || true"

echo "== 线上健康自动告警已安装 =="
echo "微信机器人：拿到企业微信/群机器人 webhook 后，在服务器 $ALERT_ENV_FILE 增加 ALERT_WECHAT_WEBHOOK=..."
