# 测试环境发布流程

## 环境边界

- 正式环境：GitHub 正式库 `Shian2002/shian-uni-app` 的 `master` 分支，对应 `deploy-to-server.sh`，使用正式数据库和正式服务。
- 测试环境：GitHub 测试库 `Shian2002/shian-uni-app-staging` 的 `master` 分支，对应 `deploy-to-staging.sh`，使用独立前端目录、独立后端服务、独立数据库副本。
- 数据库只允许从正式库单向同步到测试库；测试库的写入永远不回流正式库。

## GitHub 分支流程

1. 日常开发先推到测试库，例如 `staging-origin/master` 或测试库里的功能分支。
2. 功能完成后部署测试环境。
3. 在测试环境验收真实前后端交互。
4. 验收通过后，把同一批提交从测试库同步到正式库 `origin/master`。
5. 只在确认发布时运行正式部署。

推荐命令：

```bash
git checkout master
git pull staging-origin master
bash scripts/sync_staging_db_from_prod.sh
bash deploy-to-staging.sh
QA_BASE_URL=http://119.29.128.18:8081 npm run qa:staging
```

发布正式环境：

```bash
git checkout master
git pull origin master
git merge --ff-only staging-origin/master
bash deploy-to-server.sh
```

如果本地还没有测试库远端，第一次添加：

```bash
git remote add staging-origin git@github.com:Shian2002/shian-uni-app-staging.git
git push -u staging-origin master
```

## 测试环境外部服务策略

- 短信：默认 `STAGING_SMS_MODE=log`，只把验证码写入后端日志，不调用阿里云短信。
- 邮件：默认 `STAGING_EMAIL_MODE=log`，只把验证码写入后端日志，不连接 SMTP。
- 支付：默认 `STAGING_PAYMENT_MODE=manual`，只记录付款凭证，不自动确认到账。
- OAuth：测试环境使用 `OAUTH_ORIGIN` 指向测试站地址，生产 OAuth 配置不要直接复用到测试域名。

如需给自己的测试手机号或邮箱真实发送，在测试环境 `.env` 中配置白名单：

```bash
STAGING_SMS_MODE=send
STAGING_SMS_WHITELIST=13800000000
STAGING_EMAIL_MODE=send
STAGING_EMAIL_WHITELIST=you@example.com
```

不要把真实用户手机号、邮箱批量放入白名单。

## 服务器隔离

测试环境默认使用：

- 前端目录：`/var/www/xuan-cet-staging`
- 后端目录：`/opt/xuan-cet-staging/backend`
- 后端服务：`xuan-cet-staging-flask`
- 后端端口：`127.0.0.1:5299`
- 数据库：`/home/lighthouse/tianji-staging/backend/tianji.db`
- 访问地址：`http://119.29.128.18:8081`

如果服务器还没有测试站 Nginx 入口，需要给 `8081` 配置一个只代理测试服务的站点。

可直接运行：

```bash
bash scripts/install_staging_nginx.sh
```
