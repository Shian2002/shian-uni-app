# 时安解忧屋运营上线手册

这份手册给只熟悉前端的人使用。记住一句话：代码走 GitHub 和部署脚本，数据库只备份和恢复，不用本地覆盖线上。

## 0. 线上环境

- 服务器：`lighthouse@119.29.128.18`
- SSH key：`$HOME/.ssh/deploy_key`
- 前端目录：`/var/www/xuan-cet`
- 后端目录：`/opt/xuan-cet/backend`
- 后端服务：`xuan-cet-flask`
- 后端监听：`127.0.0.1:5199`
- 生产数据库：`/home/lighthouse/tianji/flask-source/backend/tianji.db`
- 用户上传目录：`/var/www/xuan-cet/static/uploads`

## 1. 自动备份数据库

安装或更新线上定时备份：

```bash
bash scripts/install_production_db_backup.sh
```

默认行为：

- 每天服务器时间 `03:20` 备份一次线上 SQLite 数据库。
- 备份目录：`/home/lighthouse/backups/xuan-cet/db`
- 默认保留最近 `90` 份。
- 安装时会立即执行一次备份，并用 SQLite `integrity_check` 校验。

常用检查：

```bash
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 "systemctl list-timers --all xuan-cet-db-backup.timer --no-pager"
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 "ls -lh /home/lighthouse/backups/xuan-cet/db | tail"
```

## 2. 上线前一键检查

每次准备上线前先跑：

```bash
bash scripts/preflight_release.sh
```

它会检查：

- shell 脚本语法
- Python 语法
- 后端全量测试
- H5 构建
- 生产依赖审计

如果想同时检查当前线上站点：

```bash
RUN_PROD_SMOKE=1 bash scripts/preflight_release.sh
```

当前已知情况：`npm run audit:prod` 会报告 DCloud 间接依赖 `@dcloudio/uni-mp-weixin -> ws` 的中危漏洞，而且官方暂无修复。脚本会识别这个已知项并允许继续；如果出现新的审计风险会失败。

## 3. 线上错误日志监控

上线后或用户反馈异常时运行：

```bash
bash scripts/production_monitor.sh
```

默认检查最近 30 分钟：

- `/api/health` 和首页资源是否正常
- 后端 systemd 服务状态
- 磁盘和内存
- 后端 `journalctl` 关键错误
- Nginx `error.log` 关键错误

常用参数：

```bash
SINCE="2 hours ago" bash scripts/production_monitor.sh
FOLLOW=1 bash scripts/production_monitor.sh
FAIL_ON_ERRORS=1 bash scripts/production_monitor.sh
```

安装自动告警：

```bash
ALERT_EMAIL_TO=你的邮箱 bash scripts/install_production_alert.sh
```

默认每 10 分钟检查一次：

- `/api/health`
- 后端 `xuan-cet-flask` 服务状态
- 根分区磁盘使用率
- 最新自动备份是否过旧、是否完整
- 最近后端关键错误日志

告警渠道：

- 邮箱：复用 `/opt/xuan-cet/backend/.env` 里的 `SMTP_USER` / `SMTP_PASS`，收件人由 `ALERT_EMAIL_TO` 设置。
- 微信机器人：个人微信号不能直接变成机器人；拿到企业微信或群机器人的 webhook 后，在服务器 `/etc/xuan-cet-alert.env` 加：

```bash
ALERT_WECHAT_WEBHOOK=https://...
```

发送一条正常测试通知：

```bash
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 "sudo systemctl start xuan-cet-alert-check.service && sudo journalctl -u xuan-cet-alert-check.service -n 80 --no-pager"
```

## 4. 备份恢复演练

恢复演练只操作临时目录，不碰生产库：

```bash
bash scripts/production_restore_drill.sh
```

它会取最新 `tianji-*.db` 自动备份，复制到 `/tmp/xuan-cet-restore-drill`，执行 SQLite `integrity_check`，确认 `user`、`record`、`membership` 等关键表存在，然后清理临时文件。

## 5. 标准上线流程

前端小改：

```bash
bash scripts/preflight_release.sh
bash deploy-to-server.sh
bash scripts/production_monitor.sh
```

后端或数据库相关改动：

```bash
bash scripts/install_production_db_backup.sh
bash scripts/preflight_release.sh
bash deploy-to-server.sh
RUN_PROD_SMOKE=1 bash scripts/preflight_release.sh
bash scripts/production_monitor.sh
bash scripts/production_restore_drill.sh
```

轻量部署优先使用仓库根目录脚本：

```bash
bash deploy-to-server.sh
```

脚本会执行这些动作：

- 同步后端代码和 `backend/requirements.txt`
- 重启前备份真实在线 SQLite 数据库
- 安装 Python 依赖
- 写入并重启 `systemd` 服务 `xuan-cet-flask`
- 同步 H5 前端到 `/var/www/xuan-cet`
- 同步前端时排除 `/static/uploads/`

完整服务器初始化或重装时再使用：

```bash
bash scripts/deploy.sh
```

## 6. 数据库原则

- 线上数据库是正式用户资产。
- 本地数据库只是测试用。
- 不要用本地数据库覆盖线上。
- 恢复数据库必须先确认备份完整，并先做恢复前安全备份。
- 如果只想排查数据问题，应该拉一份线上备份到本地只读分析。

每次轻量部署也会在 `/home/lighthouse/backups/xuan-cet/db` 里保留部署前备份。自动备份文件名形如 `tianji-YYYYMMDD-HHMMSS.db`，部署前备份文件名形如 `tianji-deploy-YYYYMMDD-HHMMSS.db`。

恢复数据库前先停服务并再做一次当前库备份，不能直接覆盖：

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 '
  sudo systemctl stop xuan-cet-flask &&
  cp /home/lighthouse/tianji/flask-source/backend/tianji.db /home/lighthouse/backups/xuan-cet/db/tianji-manual-before-restore-$(date +%Y%m%d-%H%M%S).db &&
  cp /home/lighthouse/backups/xuan-cet/db/要恢复的备份.db /home/lighthouse/tianji/flask-source/backend/tianji.db &&
  sudo systemctl start xuan-cet-flask
'
```

## 7. 后台管理

后台地址：

```text
http://119.29.128.18/#/pages/admin/index
```

管理员登录后也可以从右上角头像菜单进入“后台管理”。

当前后台包含：

- 概览：用户数、帖子数、隐藏帖、待审举报、待确认充值。
- 举报审核：处理或驳回帖子/评论举报。
- 帖子管理：搜索帖子，置顶、加精、隐藏或恢复。
- 用户积分：搜索用户，按用户 ID、用户名、邮箱或手机号手动加积分。
- 充值订单：查看订单并确认手动充值到账。
- 操作审计：查看举报处理、帖子管理、手动加积分和确认充值记录。
- 账号安全：管理员修改自己的登录密码。

管理员写操作会记录到 `admin_audit_log` 表，包含管理员、动作、目标对象、详情、来源 IP 和时间。

## 8. 手动日志与重启

查看服务状态：

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 'sudo systemctl status xuan-cet-flask --no-pager'
```

查看最近日志：

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 'sudo journalctl -u xuan-cet-flask -n 120 --no-pager'
```

查看实时日志：

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 'sudo journalctl -u xuan-cet-flask -f'
```

重启后端：

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 'sudo systemctl restart xuan-cet-flask'
```

重启后检查：

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 'sudo systemctl show xuan-cet-flask -p MainPID -p NRestarts -p ExecMainStatus -p ExecStart'
```

`ExecStart` 应指向 `/opt/xuan-cet/backend/venv/bin/gunicorn`，`DATABASE_URL` 应指向 `/home/lighthouse/tianji/flask-source/backend/tianji.db`，不应再有 `/opt/xuan-cet/backend/app.py` 的 Flask dev server 进程。

## 9. 配置注意事项

- 生产库路径由 `DATABASE_URL=sqlite:////home/lighthouse/tianji/flask-source/backend/tianji.db` 指定。当前线上真实用户和社区数据在这个旧路径库中，不要误切到 `/opt/xuan-cet/backend/tianji.db`。
- 上传目录由 `UPLOAD_FOLDER=/var/www/xuan-cet/static/uploads` 指定。
- 不要把 `backend/.secret_key`、生产数据库、上传文件提交到 Git。
- 管理员权限以 `user.is_admin` 字段为准，不以用户名或用户 ID 推断。
