#!/usr/bin/env bash
# 将最新 SQLite 备份压缩、加密后上传到百度网盘 bypy 应用目录。
#
# 首次使用前需要在服务器上执行:
#   python3 -m pip install --user bypy
#   bypy info
# 按提示完成百度网盘授权。bypy 只能访问网盘中的应用目录。

set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/home/lighthouse/backups/xuan-cet/db}"
REMOTE_DIR="${BAIDU_REMOTE_DIR:-/xuan-cet/db}"
KEEP_REMOTE="${BAIDU_KEEP_REMOTE:-60}"
BYPY_TIMEOUT="${BYPY_TIMEOUT:-300}"
DRY_RUN=0
BACKUP_FILE=""

usage() {
  cat <<'EOF'
用法:
  bash scripts/upload_baidu_backup.sh [--backup /path/to/tianji.db] [--dry-run]

环境变量:
  BAIDU_BACKUP_PASSPHRASE  上传前加密密码，实际上传必填
  BAIDU_REMOTE_DIR         百度网盘应用目录内的远端目录，默认 /xuan-cet/db
  BAIDU_KEEP_REMOTE        远端保留份数，默认 60
  BYPY_TIMEOUT             单个 bypy 命令超时秒数，默认 300
  BACKUP_DIR               本地备份目录，默认 /home/lighthouse/backups/xuan-cet/db
EOF
}

while [ "$#" -gt 0 ]; do
  case "$1" in
    --backup)
      BACKUP_FILE="${2:-}"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "[ERROR] 未知参数: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [ -z "$BACKUP_FILE" ]; then
  BACKUP_FILE="$(find "$BACKUP_DIR" -maxdepth 1 -name 'tianji-*.db' -type f -printf '%T@ %p\n' 2>/dev/null | sort -rn | awk 'NR==1 {print $2}')"
fi

if [ -z "$BACKUP_FILE" ] || [ ! -f "$BACKUP_FILE" ]; then
  echo "[ERROR] 未找到要上传的备份文件: ${BACKUP_FILE:-$BACKUP_DIR/tianji-*.db}" >&2
  exit 1
fi

if [ "$DRY_RUN" != "1" ]; then
  command -v bypy >/dev/null 2>&1 || {
    echo "[ERROR] 未安装 bypy。请先运行: python3 -m pip install --user bypy && bypy info" >&2
    exit 1
  }
  command -v timeout >/dev/null 2>&1 || {
    echo "[ERROR] 未安装 timeout" >&2
    exit 1
  }
  command -v openssl >/dev/null 2>&1 || {
    echo "[ERROR] 未安装 openssl" >&2
    exit 1
  }
  if [ -z "${BAIDU_BACKUP_PASSPHRASE:-}" ]; then
    echo "[ERROR] 缺少 BAIDU_BACKUP_PASSPHRASE，拒绝上传未加密备份" >&2
    exit 1
  fi
fi

STAMP="$(date -u +%Y%m%d-%H%M%S)"
BASE_NAME="$(basename "$BACKUP_FILE")"
REMOTE_NAME="${BASE_NAME%.db}-${STAMP}.db.gz.enc"
TMP_FILE="$(mktemp "/tmp/xuan-cet-baidu-${REMOTE_NAME}.XXXXXX")"

cleanup() {
  rm -f "$TMP_FILE"
}
trap cleanup EXIT

echo "本地备份: $BACKUP_FILE"
echo "远端目录: $REMOTE_DIR"
echo "远端文件: $REMOTE_NAME"

if [ "$DRY_RUN" = "1" ]; then
  echo "DRY-RUN: 将执行 gzip + openssl 加密，然后运行:"
  echo "bypy upload <encrypted-backup> '$REMOTE_DIR/$REMOTE_NAME'"
  exit 0
fi

gzip -c "$BACKUP_FILE" | openssl enc -aes-256-cbc -pbkdf2 -salt -out "$TMP_FILE" -pass env:BAIDU_BACKUP_PASSPHRASE
chmod 600 "$TMP_FILE"

timeout "$BYPY_TIMEOUT" bypy mkdir "$REMOTE_DIR" >/dev/null || true
timeout "$BYPY_TIMEOUT" bypy upload "$TMP_FILE" "$REMOTE_DIR/$REMOTE_NAME"

if [ "$KEEP_REMOTE" -gt 0 ] 2>/dev/null; then
  timeout "$BYPY_TIMEOUT" bypy list "$REMOTE_DIR" \
    | awk '/\.db\.gz\.enc$/ {print $NF}' \
    | sort \
    | head -n "-$KEEP_REMOTE" \
    | while read -r old; do
        [ -n "$old" ] && timeout "$BYPY_TIMEOUT" bypy delete "$REMOTE_DIR/$old" || true
      done
fi

echo "百度网盘异地备份上传完成: $REMOTE_DIR/$REMOTE_NAME"
