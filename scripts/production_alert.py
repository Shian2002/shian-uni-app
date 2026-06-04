#!/usr/bin/env python3
"""线上健康自动告警。

设计原则：
- 默认只读检查线上状态，不修改业务数据。
- 支持 SMTP 邮件和企业微信/群机器人 webhook。
- 不把 SMTP 密码或 webhook 写进代码，生产环境从 EnvironmentFile 读取。
"""

import argparse
import json
import os
import re
import smtplib
import socket
import sqlite3
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from email.mime.text import MIMEText
from email.header import Header
from email.utils import formataddr
from pathlib import Path


ERROR_PATTERN = re.compile(
    r"Traceback|Exception|ERROR|CRITICAL|panic|segmentation fault|ModuleNotFoundError|ImportError",
    re.I,
)


def run_command(args, timeout=15):
    try:
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout, check=False)
        return proc.returncode, proc.stdout.strip(), proc.stderr.strip()
    except Exception as exc:
        return 1, "", str(exc)


def http_get_json(url, timeout=10):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = {"raw": raw[:300]}
            return response.status, payload
    except urllib.error.HTTPError as exc:
        return exc.code, {"error": exc.read().decode("utf-8", errors="replace")[:300]}
    except Exception as exc:
        return 0, {"error": str(exc)}


def sqlite_integrity_ok(path):
    conn = sqlite3.connect(str(path))
    try:
        result = conn.execute("PRAGMA integrity_check").fetchone()
        return bool(result and result[0] == "ok")
    finally:
        conn.close()


def check_health(base_url):
    status, payload = http_get_json(base_url.rstrip("/") + "/api/health")
    if status != 200 or not payload.get("success") or payload.get("status") != "running":
        return f"健康检查异常: HTTP {status}, {payload}"
    return None


def check_service(service):
    code, stdout, stderr = run_command(["systemctl", "is-active", service])
    if code != 0 or stdout.strip() != "active":
        return f"后端服务异常: {service} is {stdout or stderr or 'unknown'}"
    return None


def check_disk(path, threshold):
    code, stdout, stderr = run_command(["df", "-P", path])
    if code != 0:
        return f"磁盘检查失败: {stderr or stdout}"
    lines = stdout.splitlines()
    if len(lines) < 2:
        return f"磁盘检查输出异常: {stdout}"
    parts = lines[1].split()
    used = int(parts[4].rstrip("%"))
    if used >= threshold:
        return f"磁盘使用率过高: {path} 已用 {used}% >= {threshold}%"
    return None


def check_backup(backup_dir, max_age_hours):
    path = Path(backup_dir)
    backups = sorted(path.glob("tianji-*.db"), key=lambda item: item.stat().st_mtime, reverse=True)
    if not backups:
        return f"未找到自动备份: {backup_dir}"
    latest = backups[0]
    age_hours = (datetime.now(timezone.utc).timestamp() - latest.stat().st_mtime) / 3600
    if age_hours > max_age_hours:
        return f"自动备份过旧: {latest} 距今 {age_hours:.1f} 小时 > {max_age_hours} 小时"
    if not sqlite_integrity_ok(latest):
        return f"自动备份完整性失败: {latest}"
    return None


def check_recent_logs(service, since):
    code, stdout, stderr = run_command(
        ["journalctl", "-u", service, "--since", since, "--no-pager"],
        timeout=20,
    )
    if code != 0:
        return f"读取后端日志失败: {stderr or stdout}"
    matches = [line for line in stdout.splitlines() if ERROR_PATTERN.search(line)]
    if matches:
        tail = "\n".join(matches[-20:])
        return f"最近后端日志发现错误:\n{tail}"
    return None


def check_database_audit(db_audit_path):
    if not db_audit_path:
        return None
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    try:
        from production_db_audit import audit_database
    except Exception as exc:
        return f"数据库审计脚本不可用: {exc}"

    try:
        findings = audit_database(db_audit_path)
    except Exception as exc:
        return f"数据库审计执行失败: {exc}"

    if findings:
        lines = [
            f"- [{item.get('severity', 'unknown')}] {item.get('code', 'unknown')}: {item.get('message', '')}"
            for item in findings[:20]
        ]
        return "数据库审计发现异常 db_audit:\n" + "\n".join(lines)
    return None


def collect_failures(
    base_url,
    service,
    backup_dir,
    backup_max_age_hours,
    disk_path,
    disk_threshold,
    since,
    db_audit_path="",
    checks=None,
):
    checks = checks or {
        "health": check_health,
        "service": check_service,
        "disk": check_disk,
        "backup": check_backup,
        "logs": check_recent_logs,
    }
    results = [
        checks["health"](base_url),
        checks["service"](service),
        checks["disk"](disk_path, disk_threshold),
        checks["backup"](backup_dir, backup_max_age_hours),
        checks["logs"](service, since),
        check_database_audit(db_audit_path),
    ]
    return [item for item in results if item]


def send_email(subject, body):
    to_addr = os.environ.get("ALERT_EMAIL_TO", "").strip()
    smtp_user = os.environ.get("ALERT_SMTP_USER", os.environ.get("SMTP_USER", "")).strip()
    smtp_pass = os.environ.get("ALERT_SMTP_PASS", os.environ.get("SMTP_PASS", "")).strip()
    smtp_host = os.environ.get("ALERT_SMTP_HOST", os.environ.get("SMTP_HOST", "smtp.qq.com")).strip()
    smtp_port = int(os.environ.get("ALERT_SMTP_PORT", os.environ.get("SMTP_PORT", "587")))
    from_name = os.environ.get("ALERT_FROM_NAME", os.environ.get("SMTP_FROM_NAME", "时安解忧屋监控"))
    if not to_addr or not smtp_user or not smtp_pass:
        return False, "邮箱告警未配置 ALERT_EMAIL_TO/SMTP_USER/SMTP_PASS"

    message = MIMEText(body, "plain", "utf-8")
    message["Subject"] = Header(subject, "utf-8")
    message["From"] = formataddr((str(Header(from_name, "utf-8")), smtp_user))
    message["To"] = to_addr
    with smtplib.SMTP(smtp_host, smtp_port, timeout=15) as server:
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, [to_addr], message.as_string())
    return True, f"已发送邮件到 {to_addr}"


def send_wechat(subject, body):
    webhook = os.environ.get("ALERT_WECHAT_WEBHOOK", "").strip()
    if not webhook:
        return False, "微信机器人 webhook 未配置"
    mentioned_mobile = [
        item.strip()
        for item in os.environ.get("ALERT_WECHAT_MENTION_MOBILE", "").split(",")
        if item.strip()
    ]
    text = {"content": f"{subject}\n\n{body}"}
    if mentioned_mobile:
        text["mentioned_mobile_list"] = mentioned_mobile
    payload = json.dumps({
        "msgtype": "text",
        "text": text,
    }).encode("utf-8")
    request = urllib.request.Request(
        webhook,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=15) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return response.status == 200, raw


def notify(subject, body, dry_run=False):
    if dry_run:
        print(f"[DRY-RUN] {subject}\n{body}")
        return

    results = []
    for sender in (send_email, send_wechat):
        try:
            ok, message = sender(subject, body)
        except Exception as exc:
            ok, message = False, str(exc)
        results.append((ok, message))
        print(("[OK] " if ok else "[WARN] ") + message)

    if not any(ok for ok, _ in results):
        print("[WARN] 没有任何告警渠道发送成功")


def main():
    parser = argparse.ArgumentParser(description="检查线上状态并在异常时发送告警")
    parser.add_argument("--base-url", default=os.environ.get("ALERT_BASE_URL", "http://119.29.128.18"))
    parser.add_argument("--service", default=os.environ.get("ALERT_SERVICE", "xuan-cet-flask"))
    parser.add_argument("--backup-dir", default=os.environ.get("ALERT_BACKUP_DIR", "/home/lighthouse/backups/xuan-cet/db"))
    parser.add_argument("--backup-max-age-hours", type=float, default=float(os.environ.get("ALERT_BACKUP_MAX_AGE_HOURS", "30")))
    parser.add_argument("--disk-path", default=os.environ.get("ALERT_DISK_PATH", "/"))
    parser.add_argument("--disk-threshold", type=int, default=int(os.environ.get("ALERT_DISK_THRESHOLD", "85")))
    parser.add_argument("--since", default=os.environ.get("ALERT_LOG_SINCE", "15 min ago"))
    parser.add_argument("--db-audit-path", default=os.environ.get("ALERT_DB_AUDIT_PATH", ""))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--send-ok", action="store_true", help="正常时也发送一条测试通知")
    args = parser.parse_args()

    failures = collect_failures(
        base_url=args.base_url,
        service=args.service,
        backup_dir=args.backup_dir,
        backup_max_age_hours=args.backup_max_age_hours,
        disk_path=args.disk_path,
        disk_threshold=args.disk_threshold,
        since=args.since,
        db_audit_path=args.db_audit_path,
    )

    host = socket.gethostname()
    if failures:
        subject = f"[时安解忧屋告警] {len(failures)} 个线上异常"
        body = "\n\n".join(failures) + f"\n\n主机: {host}\n时间: {datetime.now().isoformat()}"
        notify(subject, body, dry_run=args.dry_run)
        return 1

    print("线上健康、服务、磁盘、备份、日志检查均正常。")
    if args.send_ok:
        notify(
            "[时安解忧屋监控] 测试通知",
            f"线上监控检查正常。\n主机: {host}\n时间: {datetime.now().isoformat()}",
            dry_run=args.dry_run,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
