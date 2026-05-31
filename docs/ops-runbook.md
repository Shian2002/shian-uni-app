# 时安解忧屋运维说明

## 线上环境

- 服务器：`lighthouse@119.29.128.18`
- SSH key：`$HOME/.ssh/deploy_key`
- 前端目录：`/var/www/xuan-cet`
- 后端目录：`/opt/xuan-cet/backend`
- 后端服务：`xuan-cet-flask`
- 后端监听：`127.0.0.1:5199`
- 生产数据库：`/home/lighthouse/tianji/flask-source/backend/tianji.db`
- 用户上传目录：`/var/www/xuan-cet/static/uploads`

## 部署

轻量部署优先使用仓库根目录脚本：

```bash
bash deploy-to-server.sh
```

脚本会执行这些动作：

- 构建 H5 前端并同步到 `/var/www/xuan-cet`
- 同步后端代码和 `backend/requirements.txt`
- 安装 Python 依赖
- 写入并重启 `systemd` 服务 `xuan-cet-flask`
- 使用 `gunicorn --workers 2 --threads 4 --timeout 180 --bind 127.0.0.1:5199 app:app`
- 同步前端时排除 `/static/uploads/`
- 重启前备份真实在线 SQLite 数据库

完整服务器初始化或重装时再使用：

```bash
bash scripts/deploy.sh
```

## 巡检

部署后至少执行：

```bash
curl -sS http://119.29.128.18/api/health
curl -sS -o /dev/null -w '%{http_code} %{time_total}\n' http://119.29.128.18/
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 'sudo systemctl is-active xuan-cet-flask'
```

期望：

- `/api/health` 返回 `success: true`
- 首页 HTTP 状态为 `200`
- `xuan-cet-flask` 状态为 `active`

## 后台管理

后台地址：

```text
http://119.29.128.18/#/pages/admin/index
```

管理员登录后也可以从右上角头像菜单进入“后台管理”。

当前后台包含：

- 概览：用户数、帖子数、隐藏帖、待审举报、待确认充值。
- 举报审核：处理或驳回帖子/评论举报。
- 帖子管理：搜索帖子，置顶、加精、隐藏或恢复。
- 用户积分：搜索用户，按用户 ID 手动加积分。
- 充值订单：查看订单并确认手动充值到账。

## 日志

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

## 重启

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 'sudo systemctl restart xuan-cet-flask'
```

重启后检查：

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 'sudo systemctl show xuan-cet-flask -p MainPID -p NRestarts -p ExecMainStatus -p ExecStart'
```

`ExecStart` 应指向 `/opt/xuan-cet/backend/venv/bin/gunicorn`，`DATABASE_URL` 应指向 `/home/lighthouse/tianji/flask-source/backend/tianji.db`，不应再有 `/opt/xuan-cet/backend/app.py` 的 Flask dev server 进程。

## 数据库备份与回滚

每次轻量部署会在生产数据库同目录生成：

```text
/home/lighthouse/tianji/flask-source/backend/tianji.db.bak-deploy-YYYYMMDD-HHMMSS
```

查看最近备份：

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 'ls -1t /home/lighthouse/tianji/flask-source/backend/tianji.db.bak-deploy-* | head'
```

回滚数据库前先停服务并再做一次当前库备份：

```bash
ssh -i "$HOME/.ssh/deploy_key" lighthouse@119.29.128.18 '
  sudo systemctl stop xuan-cet-flask &&
  cp /home/lighthouse/tianji/flask-source/backend/tianji.db /home/lighthouse/tianji/flask-source/backend/tianji.db.bak-manual-$(date +%Y%m%d-%H%M%S) &&
  cp /home/lighthouse/tianji/flask-source/backend/tianji.db.bak-deploy-YYYYMMDD-HHMMSS /home/lighthouse/tianji/flask-source/backend/tianji.db &&
  sudo systemctl start xuan-cet-flask
'
```

## 配置注意事项

- 生产库路径由 `DATABASE_URL=sqlite:////home/lighthouse/tianji/flask-source/backend/tianji.db` 指定。当前线上真实用户和社区数据在这个旧路径库中，不要误切到 `/opt/xuan-cet/backend/tianji.db`。
- 上传目录由 `UPLOAD_FOLDER=/var/www/xuan-cet/static/uploads` 指定。
- 不要把 `backend/.secret_key`、生产数据库、上传文件提交到 Git。
- 管理员权限以 `user.is_admin` 字段为准，不以用户名或用户 ID 推断。
