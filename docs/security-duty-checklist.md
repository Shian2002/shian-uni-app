# 安全值守清单

这份清单用于后续安全巡检、上线前安全复核和用户反馈异常时的排查。外部 `Anthropic-Cybersecurity-Skills` 只作为审计思路来源，不整包安装到本仓库，不直接执行其中的攻击模拟类流程。

## 使用原则

- 先保护线上数据和账号资产，再处理代码和部署优化。
- 生产数据库只做备份、恢复演练和只读核验，不用本地库覆盖线上。
- 所有安全结论都要有证据：文件路径、命令输出、接口返回、线上日志或数据库只读结果。
- 涉及线上写操作、密钥轮换、第三方配置变更时，先备份并说明回滚路径。
- 不把密钥、生产库、上传文件、会话 cookie 或 token 写入报告和提交。

## 推荐触发场景

- 上线前复核：后端、登录、充值、积分、上传、数据库、部署脚本或依赖发生改动。
- 用户反馈账号、积分、充值、图片上传、登录异常。
- 收到告警邮件、接口错误、异常流量或可疑数据。
- 准备引入新依赖、第三方脚本、OAuth/SMS/支付等外部服务。

## 基础命令

```bash
npm run lint
npm run audit:prod
python3 -m pytest -q
bash scripts/preflight_release.sh
```

上线环境只读核验：

```bash
npm run qa:online
bash scripts/production_monitor.sh
bash scripts/production_restore_drill.sh
python3 scripts/production_db_audit.py /home/lighthouse/tianji/flask-source/backend/tianji.db
```

## 8 个重点主题

### 1. 依赖与供应链

对应外部技能方向：SCA 依赖扫描、供应链攻击模拟、漏洞分级。

检查项：

- `npm run audit:prod` 是否只有已记录的 DCloud `ws` 中危无修复项。
- `backend/requirements.txt`、`backend/constraints.txt` 是否引入新高风险依赖。
- 前端新增 CDN、远程脚本、第三方 SDK 时，确认来源可信、用途明确、不会携带密钥。
- 新依赖不能绕过现有 `scripts/preflight_release.sh`。

### 2. 密钥与配置

对应外部技能方向：服务账号审计、凭证轮换、密钥泄漏检查。

检查项：

- `backend/.secret_key`、生产 `.env`、短信/OAuth/SMTP 密钥不能进入 Git。
- 前端 `VITE_*`、构建注入变量、静态 JS 中不能放真正的服务端密钥。
- `scripts/lint-check.mjs` 的密钥扫描如果报错，先确认是否真实泄漏；真实泄漏要按事故处理并轮换。
- 线上配置以 systemd 环境和 `/opt/xuan-cet/backend/.env` 为准，文档只作入口说明。

### 3. 认证、会话与 CSRF

对应外部技能方向：Web 应用渗透测试、CSRF、认证安全。

检查项：

- 会话写接口默认受 CSRF 保护；新增 `POST`、`PUT`、`PATCH`、`DELETE` 路由时必须说明是否允许豁免。
- 前端 H5 写请求继续由 `src/main.js` 统一注入 `X-CSRFToken`。
- 登录、注册、验证码、公开排盘等兼容豁免接口不能扩大到后台、积分、社区、资料、充值确认等敏感接口。
- 管理员权限只看 `user.is_admin`，不能用用户名、手机号或用户 ID 推断。

### 4. 越权与资产副作用

对应外部技能方向：Web 漏洞分流、访问控制审计。

检查项：

- 涉及用户资料、记录、收藏、社区、积分、充值订单时，必须校验资源归属。
- 未登录 `/api/me` 可以返回访客状态，但 `/api/membership` 等会员资产接口必须拒绝。
- 积分变动要同时检查余额、`point_log` 和业务记录，不能只看接口成功。
- 管理员操作必须写入 `admin_audit_log`，审计内容不能包含密码或完整密钥。

### 5. 上传与静态资源

对应外部技能方向：文件上传安全、Web 应用测试。

检查项：

- 上传继续校验真实图片内容，不能只信扩展名或前端 MIME。
- 文件名必须使用随机值，不能使用用户原始文件名直接落盘。
- 上传目录为 `/var/www/xuan-cet/static/uploads`，部署同步不能覆盖或清空用户上传文件。
- 静态资源 404、异常 MIME、可执行脚本落入上传目录时按高风险处理。

### 6. XSS、前端注入与安全头

对应外部技能方向：安全头审计、Web 应用渗透测试、XSS 检查。

检查项：

- Vue 模板优先使用默认转义，不新增未审计的 `v-html`、`innerHTML`、`insertAdjacentHTML`。
- 如果必须渲染富文本，先确认来源和清洗策略，再加测试。
- 不新增 `eval`、`new Function`、字符串形式 `setTimeout` / `setInterval`。
- 线上安全头需要运行时验证；仓库看不到的 Nginx/CDN 配置不能直接假设已存在。

### 7. SQLite 数据安全

对应外部技能方向：SQLite 数据库取证、数据完整性审计。

检查项：

- 活跃生产库路径当前以 `/home/lighthouse/tianji/flask-source/backend/tianji.db` 为准；写库前必须重新核对服务环境。
- 数据库变更先跑备份和恢复演练，再做可加性迁移或索引。
- 只读审计覆盖完整性、关键表、负积分、孤儿会员/积分日志、重复积分幂等键。
- 发现资产异常时按数据事故处理：冻结破坏性操作、备份、只读取证、定向恢复。

### 8. 生产运行与告警

对应外部技能方向：漏洞分级、事件响应、服务账号审计。

检查项：

- 生产服务必须由 gunicorn/systemd 承载，不能暴露 Flask dev server 或 Vite dev server。
- `/api/health/deep`、`production_monitor.sh`、`production_alert.py` 是健康和告警主入口。
- 告警先核对时间窗口、服务状态和日志，不把旧迁移日志直接当现网故障。
- 部署后必须跑线上验活；本地构建通过不代表线上已生效。

## 安全报告格式

发现问题时按这个格式记录：

```text
编号：
等级：Critical / High / Medium / Low
位置：文件路径、函数或接口、行号
证据：代码片段、命令输出、接口返回或日志
影响：谁能利用，会造成什么结果
建议：最小修复方案
验证：修复后要跑的命令或线上核验
回滚：如果修复失败如何退回
```

## 外部技能库映射

优先参考这些方向，不直接照搬攻击流程：

- `performing-sca-dependency-scanning-with-snyk`：转成 `npm audit`、Python 依赖和新增依赖复核。
- `performing-security-headers-audit`：转成运行时 HTTP 响应头检查。
- `performing-web-application-penetration-test`：转成授权范围内的登录、CSRF、越权、XSS、上传检查。
- `performing-web-application-vulnerability-triage`：转成按影响和可利用性分级。
- `performing-sqlite-database-forensics`：转成只读数据完整性、资产异常和恢复证据链。
- `performing-supply-chain-attack-simulation`：转成依赖来源、锁文件和构建脚本审查。
- `performing-service-account-audit`：转成 OAuth、短信、SMTP、服务器账号和部署密钥最小权限复核。
- `prioritizing-vulnerabilities-with-cvss-scoring`：转成对 Critical / High / Medium / Low 的统一排序。
