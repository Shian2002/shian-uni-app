#!/usr/bin/env bash
# 安装线上 SQLite 数据库自动备份 timer，并立即执行一次备份校验。

set -euo pipefail

SERVER_USER="${SERVER_USER:-lighthouse}"
SERVER_HOST="${SERVER_HOST:-119.29.128.18}"
SERVER="${SERVER_USER}@${SERVER_HOST}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/deploy_key}"
SSH_CMD=(ssh -i "$SSH_KEY")
SCP_CMD=(scp -i "$SSH_KEY")

LIVE_DB="${LIVE_DB:-/home/lighthouse/tianji/flask-source/backend/tianji.db}"
BACKUP_DIR="${BACKUP_DIR:-/home/lighthouse/backups/xuan-cet/db}"
KEEP="${KEEP:-90}"
TIMER_TIME="${TIMER_TIME:-03:20}"
REMOTE_OPS_DIR="${REMOTE_OPS_DIR:-/opt/xuan-cet/ops}"
REMOTE_BACKUP_PY="$REMOTE_OPS_DIR/db_backup.py"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "== 安装线上数据库自动备份 =="
echo "服务器: $SERVER"
echo "数据库: $LIVE_DB"
echo "备份目录: $BACKUP_DIR"
echo "保留份数: $KEEP"
echo "每日时间: $TIMER_TIME"

"${SSH_CMD[@]}" "$SERVER" "mkdir -p '$REMOTE_OPS_DIR' '$BACKUP_DIR'"
"${SCP_CMD[@]}" "$ROOT_DIR/scripts/db_backup.py" "$SERVER:$REMOTE_BACKUP_PY"

"${SSH_CMD[@]}" "$SERVER" "set -euo pipefail
sudo tee /usr/local/bin/xuan-cet-db-backup >/dev/null <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
/usr/bin/python3 '$REMOTE_BACKUP_PY' --source '$LIVE_DB' --backup-dir '$BACKUP_DIR' --keep '$KEEP'
EOF
sudo chmod 755 /usr/local/bin/xuan-cet-db-backup
sudo tee /etc/systemd/system/xuan-cet-db-backup.service >/dev/null <<'EOF'
[Unit]
Description=时安解忧屋 SQLite 数据库备份
After=network.target

[Service]
Type=oneshot
User=$SERVER_USER
ExecStart=/usr/local/bin/xuan-cet-db-backup
EOF
sudo tee /etc/systemd/system/xuan-cet-db-backup.timer >/dev/null <<'EOF'
[Unit]
Description=每日执行时安解忧屋数据库备份

[Timer]
OnCalendar=*-*-* $TIMER_TIME:00
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now xuan-cet-db-backup.timer >/dev/null
sudo systemctl start xuan-cet-db-backup.service
systemctl list-timers --all xuan-cet-db-backup.timer --no-pager
ls -lh '$BACKUP_DIR' | tail -n 8"

echo "== 自动备份已安装并完成一次即时备份 =="
