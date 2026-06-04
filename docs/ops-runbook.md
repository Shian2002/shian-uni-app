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

## 1.1 百度网盘异地备份

百度网盘只作为 COS 接入前的临时异地备份。上传前脚本会先压缩并加密数据库备份，网盘里只保存 `.db.gz.enc` 文件。

安装百度网盘异地备份 timer：

```bash
bash scripts/install_baidu_offsite_backup.sh
```

安装脚本会在服务器 `/opt/xuan-cet/ops/baidu-venv` 独立虚拟环境里安装 `bypy`、同步上传脚本、创建 `xuan-cet-baidu-backup.timer`。首次安装后还需要手动完成两步：

```bash
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 'export PATH="/opt/xuan-cet/ops/baidu-venv/bin:$PATH"; bypy info'
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 'echo BAIDU_BACKUP_PASSPHRASE=换成一条强密码 | sudo tee -a /etc/xuan-cet-baidu-backup.env >/dev/null'
```

第一条命令会输出百度网盘授权链接，需要用浏览器登录百度账号授权。第二条命令写入上传前加密密码；不要把这条密码提交到 Git。

如果安装时还没有写入 `BAIDU_BACKUP_PASSPHRASE`，脚本只安装服务文件，不会启用定时器，避免每天产生失败任务。

授权和密码配置完成后测试一次：

```bash
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 "sudo systemctl start xuan-cet-baidu-backup.service && sudo journalctl -u xuan-cet-baidu-backup.service -n 80 --no-pager"
```

测试通过后启用定时器：

```bash
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 "sudo systemctl enable --now xuan-cet-baidu-backup.timer"
```

本地 dry-run 检查脚本参数：

```bash
bash scripts/upload_baidu_backup.sh --backup /path/to/tianji.db --dry-run
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

## 2.1 测试接手清单

日常改动先按风险分层，不要每次都从头猜要跑什么。

本地联调先看端口：

```bash
npm run qa:local
```

它会检查：

- 前端开发端口是否监听。当前以 `vite.config.js` 为准，是 `3001`。
- 后端端口 `5199` 是否监听。
- Vite `/api` 代理是否指向 `http://localhost:5199`。
- 前端代理 `/api/health` 是否能连到后端。

如果脚本提示 `manifest devServer.port` 是 `5173`，这是旧配置提醒；实际 H5 本地开发端口以 `vite.config.js` 为准。

标准本地启动流程：

```bash
# 终端 1：后端，默认监听 127.0.0.1:5199
npm run dev:backend

# 终端 2：前端，当前 Vite 端口是 3001
npm run dev:h5

# 终端 3：确认前后端和代理链路
npm run dev:check
```

刚启动服务时可以用等待版验活：

```bash
npm run dev:smoke
```

`dev:check` 会立即检查当前端口状态；`dev:smoke` 会等待前端、后端和代理链路最多 30 秒，适合刚启动服务后运行。

如果要临时换后端端口：

```bash
FLASK_PORT=5299 npm run dev:backend
LOCAL_BACKEND_URL=http://localhost:5299 npm run qa:local
```

只改前端页面、文案或样式：

```bash
python3 -m pytest -q
npm run build:h5
```

改 H5 构建、路由、导航、登录弹窗或 tab 页面切换：

```bash
python3 -m pytest -q
npm run build:h5
```

必须重点看：

- 首页、八字、奇门、六爻、梅花、紫微、塔罗、日历、积分页面是否能直开。
- 登录弹窗能打开，能切到注册，再切回登录。
- 移动端首页不能水平溢出。
- 浏览器控制台不能出现 error。

改后端 API、积分、充值、账号、登录或数据库模型：

```bash
python3 -m pytest -q
bash scripts/preflight_release.sh
```

必须重点看：

- `/api/health` 返回 `success: true` 和 `status: running`。
- `/api/recharge/packages` 返回积分套餐和 AI 次数包。
- 未登录 `/api/me` 返回 `guest: true`。
- 未登录 `/api/membership` 必须是 `401`，不能误放开会员数据。
- 涉及积分异常时，同时核对 `membership.points` 和 `point_log`，不能只看余额。

改部署脚本、依赖、服务器配置或数据库迁移：

```bash
bash scripts/install_production_db_backup.sh
bash scripts/preflight_release.sh
bash deploy-to-server.sh
bash scripts/production_restore_drill.sh
```

`npm run qa:online` 验的是当前线上站点，不是本地未部署代码。通常由 `bash deploy-to-server.sh` 在部署后自动运行；如果只是想确认当前线上健康，也可以手动运行。

`npm run qa:online` 会额外检查首页引用的 `/assets/` 和 `/static/` 资源是否 404。每次运行都会写入 `artifacts/qa/<时间>/report.json`；页面失败时还会保存截图和 HTML，方便复盘。

数据库原则：

- 线上数据库只做备份、恢复和只读核验。
- 不要用本地数据库覆盖线上。
- 恢复前必须先备份当前生产库。
- 不清楚当前生产库路径时，先核对 `DATABASE_URL`、`systemd` 服务和脚本变量。

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
- 生产 SQLite 只读审计
- 最近后端关键错误日志

告警渠道：

- 邮箱：复用 `/opt/xuan-cet/backend/.env` 里的 `SMTP_USER` / `SMTP_PASS`，收件人由 `ALERT_EMAIL_TO` 设置。
- 微信机器人：个人微信号不能直接变成机器人；拿到企业微信或群机器人的 webhook 后，在服务器 `/etc/xuan-cet-alert.env` 加：

```bash
ALERT_WECHAT_WEBHOOK=https://...
ALERT_WECHAT_MENTION_MOBILE=你的手机号
```

如果通过 `scripts/install_production_alert.sh` 安装，也可以这样写入手机号：

```bash
ALERT_EMAIL_TO=你的邮箱 ALERT_WECHAT_MENTION_MOBILE=你的手机号 bash scripts/install_production_alert.sh
```

发送一条正常测试通知：

```bash
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 "sudo /usr/local/bin/xuan-cet-alert-test"
```

手动深度健康检查：

```bash
curl -sS http://127.0.0.1:5199/api/health/deep
```

`/api/health/deep` 会主动检查问真 API、数据库连通性和上传目录可写性；其中任一项失败时返回 `status: degraded`。

CSRF 检查：

- `/api/csrf-token` 提供 H5 会话写接口使用的 token。
- H5 入口 `src/main.js` 会给 `uni.request`、`uni.uploadFile` 和浏览器 `fetch` 的 `/api/*` 写请求自动加 `X-CSRFToken`。
- 登录、注册、验证码、排盘等明确标注 `@csrf.exempt` 的公开接口仍保持兼容；后台、积分、社区、用户资料等会话写接口默认受 CSRF 保护。

数据库只读审计：

```bash
python3 scripts/production_db_audit.py /home/lighthouse/tianji/flask-source/backend/tianji.db
```

审计脚本只读打开 SQLite，检查关键表、完整性、负积分、孤儿会员记录、孤儿积分日志和重复积分幂等键。发现异常时先备份，再按数据事故处理，不要用本地库覆盖线上库。

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
```

后端或数据库相关改动：

```bash
bash scripts/install_production_db_backup.sh
bash scripts/preflight_release.sh
bash deploy-to-server.sh
bash scripts/production_restore_drill.sh
```

轻量部署优先使用仓库根目录脚本：

```bash
bash deploy-to-server.sh
```

脚本会执行这些动作：

- 默认先运行 `scripts/preflight_release.sh`
- 同步后端代码和 `backend/requirements.txt`
- 重启前备份真实在线 SQLite 数据库
- 安装 Python 依赖
- 写入并重启 `systemd` 服务 `xuan-cet-flask`
- 重启后硬校验 `systemd` 运行环境中的 `DATABASE_URL` 必须指向 `/home/lighthouse/tianji/flask-source/backend/tianji.db`
- 同步 H5 前端到 `/var/www/xuan-cet`
- 同步前端时排除 `/static/uploads/`
- 运行 `scripts/production_monitor.sh`
- 运行 `npm run qa:online`

如果只是临时救急，必须跳过浏览器回归，可以这样运行：

```bash
SKIP_ONLINE_QA=1 bash deploy-to-server.sh
```

跳过后要手动补跑：

```bash
npm run qa:online
```

如果只是临时救急，必须跳过部署前检查，可以这样运行：

```bash
SKIP_PREFLIGHT=1 bash deploy-to-server.sh
```

跳过后要尽快补跑：

```bash
bash scripts/preflight_release.sh
```

GitHub Actions 会在推送和 PR 时自动运行：

```bash
npm run lint
npm run typecheck
npm test
npm run build
```

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
- 后端 SQLite 连接会启用 `WAL`、`busy_timeout=5000` 和外键检查；如果运维检查发现不是这些值，先查服务环境和启动日志。
- 验证码、限流、AI/SSE 任务状态和启动迁移登记分别落在 `verification_code`、`rate_limit_bucket`、`ai_run`、`migration_record` 表，排查登录/AI 流式异常时优先核对这些表。
- H5 前端逐步接入 CSRF 时，可先取 `GET /api/csrf-token`，再把 token 带到登录后写接口；现有豁免接口不要一次性全部改动，避免破坏线上流程。
