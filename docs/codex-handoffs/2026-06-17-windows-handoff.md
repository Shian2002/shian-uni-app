# Windows 接力交接手册

本文给一台全新的 Windows 电脑或 Windows 侧 agent 使用，目标是让它能接手 `xuan-cet-tai` 的开发、联调、HBuilderX 打包、部署和线上验活。它不是发布报告；执行前仍需按当前 Git 状态和线上状态复核。

## 1. 项目边界

- 项目核心目录：`xuan-cet-tai`
- 前端：uni-app / Vue 3 / Vite
- 后端：Flask / SQLAlchemy / SQLite
- 生产数据库：SQLite，只允许备份、恢复和只读核验，不能用本地库覆盖线上库
- 多端范围：H5、Android、macOS、Windows 当前优先；iOS、鸿蒙按发行台账状态恢复

重要文档：

- `README.md`：项目结构和技术栈
- `AGENTS.md`：本仓协作规则
- `docs/ops-runbook.md`：服务器、部署、备份、监控和测试手册
- `docs/security-duty-checklist.md`：安全值守入口
- `docs/release/README.md`：全端发行台账和命令入口
- `docs/staging-workflow.md`：预发布流程

## 2. 代码获取

推荐只通过 Git 接力，不要用压缩包长期同步源码。

正式主仓：

```bash
git clone git@github.com:Shian2002/shian-uni-app.git
cd shian-uni-app
```

测试仓：

```bash
git clone git@github.com:Shian2002/shian-uni-app-staging.git
```

如果 Windows 当前只接业务项目，进入核心目录：

```bash
cd xuan-cet-tai
git status --short
```

接手前必须确认当前分支、远端和未提交改动：

```bash
git branch --show-current
git remote -v
git status --short
```

## 3. Windows 必装环境

基础开发：

- Git for Windows
- Node.js LTS
- Python 3.11 或当前项目兼容版本
- HBuilderX Windows 版
- 微信开发者工具，如要调微信小程序
- Playwright Chromium，用于线上回归

推荐额外安装：

- Windows Terminal
- VS Code 或 Cursor
- WSL2 Ubuntu，用于运行 shell 部署脚本

安装 Playwright 浏览器：

```bash
npx playwright install chromium
```

如果要在 Windows 上执行 `bash scripts/*.sh` 或 `deploy-to-server.sh`，优先使用 WSL2。Git Bash 可以做轻量检查，但部署链路以 WSL2 更稳。

## 4. 敏感配置交接

这些内容不能提交到 Git，也不能写入交接文档明文：

- 服务器 SSH 私钥：默认路径为本机 `~/.ssh/deploy_key`
- 后端 `.env`：AI、JWT、SMTP、支付、数据库等配置
- DCloud / HBuilderX 账号
- 各应用商店账号和 2FA
- Android keystore、Apple p12、描述文件、签名密码
- 百度网盘备份加密密码、告警 webhook、SMTP 密码

Windows 机器应从可信介质或密码管理器取回这些配置。取回后先只做连通性检查，不要立刻部署或修改生产环境。

后端本地环境参考：

```bash
cd backend
copy .env.example .env
```

然后由负责人把必要变量补入 `.env`。不要把生产 `.env` 原样发给不需要生产权限的人。

## 5. 首次安装依赖

在 `xuan-cet-tai` 目录执行：

```bash
npm install
```

后端依赖：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
cd ..
```

如果在 WSL2 内运行后端，应使用 Linux 虚拟环境：

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
```

## 6. 本地联调

三个终端分别执行。

后端：

```bash
npm run dev:backend
```

H5 前端：

```bash
npm run dev:h5
```

本地连通性检查：

```bash
npm run dev:check
npm run dev:smoke
```

当前本地端口以代码为准：

- 后端默认：`127.0.0.1:5199`
- H5 Vite 端口：以 `vite.config.js` 为准，近期为 `3001`

如需临时更换后端端口：

```bash
set FLASK_PORT=5299
npm run dev:backend
```

另一个终端：

```bash
set LOCAL_BACKEND_URL=http://localhost:5299
npm run qa:local
```

## 7. 常规验证命令

普通前端、文案、样式改动：

```bash
python -m pytest -q
npm run build:h5
```

后端、账号、积分、支付、数据库模型、部署脚本改动：

```bash
python -m pytest -q
bash scripts/preflight_release.sh
```

线上健康检查：

```bash
npm run qa:online
bash scripts/production_monitor.sh
```

`npm run qa:online` 验的是当前线上站点，不是本地代码。它会检查健康接口、只读 API、主要页面、登录注册弹窗、移动首页和静态资源。

## 8. 服务器信息

服务器和生产运行信息以 `docs/ops-runbook.md`、部署脚本、运行中 systemd 环境为准。当前交接基线：

- SSH：`lighthouse@119.29.128.18`
- SSH key：`~/.ssh/deploy_key`
- 前端目录：`/var/www/xuan-cet`
- 后端目录：`/opt/xuan-cet/backend`
- 后端服务：`xuan-cet-flask`
- 后端监听：`127.0.0.1:5199`
- 用户上传目录：`/var/www/xuan-cet/static/uploads`
- 生产数据库真路径：以 `DATABASE_URL` 为准，当前应核对为 `sqlite:////home/lighthouse/tianji/flask-source/backend/tianji.db`

只读核验服务器：

```bash
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 "systemctl status xuan-cet-flask --no-pager"
ssh -i ~/.ssh/deploy_key lighthouse@119.29.128.18 "curl -fsS http://127.0.0.1:5199/api/health"
```

数据库原则：

- 不要直接拿生产库试改
- 不要用本地数据库覆盖线上
- 恢复前必须先备份当前生产库
- 不确定生产库路径时，先查 `DATABASE_URL`、systemd 和部署脚本

## 9. 部署流程

完整部署前先确认：

```bash
git status --short
python -m pytest -q
npm run build:h5
```

正式链路：

```bash
bash scripts/preflight_release.sh
bash deploy-to-server.sh
bash scripts/production_monitor.sh
npm run qa:online
```

只更新 H5 法律页和静态资源时，优先走 H5-only 部署：

```bash
DRY_RUN=1 npm run deploy:h5
CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5
```

H5 回滚：

```bash
CONFIRM_H5_ROLLBACK=shianjieyouwu.com npm run rollback:h5
```

部署脚本或生产环境变更后，必要时追加恢复演练：

```bash
bash scripts/production_restore_drill.sh
```

## 10. HBuilderX 和多端打包

Windows 侧应优先跑只读检查，确认环境和缺口：

```bash
npm run mobile:build-env
npm run mobile:api-evidence
npm run mobile:app-resource-packet
npm run platform:backend-matrix
```

HBuilderX 资源包：

```bash
npm run mobile:hbuilderx-resources
```

云打包必须显式确认，不要误触发：

```bash
set HBUILDERX_CLOUD_PACK_EXECUTE=1
set HBUILDERX_CLOUD_PACK_PLATFORM=android
npm run mobile:hbuilderx-cloud-pack
```

外部或新机器打包回传目录：

```text
artifacts/release-inbox/
```

回传后执行：

```bash
npm run release:intake
npm run release:artifact-metadata
```

## 11. Windows 桌面包

Windows 电脑如果负责桌面端包，优先执行：

```bash
npm run desktop:install
npm run desktop:build:win:x64:safe
npm run desktop:windows-user-packet
npm run desktop:release-status
```

桌面端产物、hash、签名和真机安装证据以 `docs/release/desktop-build-evidence.md` 和 `configs/release/desktop-release-status.json` 为准。

签名证书和密码不能入库。公开发布前必须补签名、公证或平台要求的对应证据。

## 12. 全端发行状态

低影响状态检查：

```bash
npm run release:low-impact-status
npm run release:all-platform-status
npm run release:current-index
npm run release:progress
```

生成给外部打包人的交接包：

```bash
npm run release:external-handoff
npm run mobile:build-requests
npm run platform:handoff
```

正式候选前严格检查：

```bash
npm run release:readiness -- --strict
npm run platform:backend-matrix -- --strict
npm run release:artifact-metadata -- --strict
npm run store:materials -- --strict
npm run desktop:release-status -- --strict
```

当前发行原则：

- 先把全端安装包和后端请求可用性处理完
- 必须用户本人处理的商店、账号、2FA、签名动作留到最后
- 最终安装包刷新集中到最后一批，避免重复打包
- 旧包清理先生成计划，不直接删除

## 13. 安全和生产边界

接手后遇到以下内容，先读 `docs/security-duty-checklist.md`，再动手：

- 登录、注册、JWT、会话
- 充值、支付、积分、AI 次数包
- 上传、静态资源、用户文件
- 数据库 schema、迁移、恢复
- 部署脚本、systemd、Nginx、告警
- 任何密钥、证书、商店账号

支付和积分验证不能只看接口返回；还要核对 `Membership.points`、`PointLog`、`Record` 等副作用是否闭环。

生产告警不是当前故障证明。收到告警时，优先跑：

```bash
bash scripts/production_monitor.sh
python scripts/production_alert.py --dry-run
```

## 14. 接手后的最小验收

Windows 电脑完成接力后，至少交付以下证据：

```bash
git status --short
npm run dev:check
python -m pytest -q
npm run build:h5
npm run qa:online
npm run release:low-impact-status
```

如果负责部署，再补：

```bash
bash scripts/preflight_release.sh
bash deploy-to-server.sh
bash scripts/production_monitor.sh
npm run qa:online
```

如果负责 Windows 安装包，再补：

```bash
npm run desktop:build:win:x64:safe
npm run desktop:windows-user-packet
npm run desktop:release-status
```

## 15. Skills 交接

本业务仓库当前没有内置 `skills/` 目录。项目相关技能主要存在于当前 Mac 的 Codex 记忆目录和全局技能目录里，不随业务代码发布。Windows 侧接力时要明确区分三类东西：

- 项目权威流程：本仓 `AGENTS.md`、`docs/ops-runbook.md`、`docs/release/README.md`、`docs/security-duty-checklist.md`、部署脚本和测试脚本
- 项目专属 skills：当前 Mac 本机记忆里的 `xuan-cet-tai-*` 技能
- 通用工程 skills：`addyosmani-*`、`gstack /browse`、UI/UX、安全、发布、代码评审等全局技能

### 15.1 Windows 必须知道的项目专属 skills

这些技能如果 Windows 侧有 Codex memory skills，可以安装到同等位置；如果没有，就把下面的触发条件和步骤当作人工流程执行。

`xuan-cet-tai-release-qa-loop`

- 用途：发布、部署、线上验活、确认“线上是不是真的好了”
- 触发：用户说“测试”“部署”“执行”“上传部署”“线上是不是真的好了”
- 必读：`docs/ops-runbook.md`、`scripts/preflight_release.sh`、`deploy-to-server.sh`、`scripts/online_regression.mjs`
- 标准链路：

```bash
bash scripts/preflight_release.sh
bash deploy-to-server.sh
bash scripts/production_monitor.sh
npm run qa:online
```

`xuan-cet-tai-safe-db-workflow`

- 用途：生产 SQLite 审计、备份、恢复演练、只读核验、低风险优化
- 触发：用户提到“数据库优化”“schema drift”“线上库核验”“关键表检查”
- 硬边界：先备份、先副本验证、不能直接拿生产库试；用户要求“先看不要修”时只读
- 必读：`docs/ops-runbook.md`、`deploy-to-server.sh`、`scripts/production_restore_drill.sh`、`scripts/production_db_audit.py`
- 标准链路：

```bash
npm run ops:backup
npm run ops:restore-drill
python scripts/production_db_audit.py
```

`xuan-cet-tai-staging-release-isolation`

- 用途：测试仓、staging 部署、生产到测试单向同步、短信邮件支付隔离
- 触发：用户提到“测试版本单独仓库”“先推测试版本”“测试环境不要影响正式用户”
- 必读：`docs/staging-workflow.md`、`deploy-to-staging.sh`、`scripts/sync_staging_db_from_prod.sh`、`.env.staging.example`
- 硬边界：`prod -> staging` 单向同步；不要把 staging 数据反向写回正式库；不要误推正式 `origin`
- 推送前门禁：

```bash
npm run lint
npm run typecheck
python -m pytest -q
npm run build:h5
```

### 15.2 通用 skills 交接

当前项目已有说明见 `docs/ai-skill-sources.md`。Windows 侧如果要复刻当前工作流，优先准备这些能力：

- `gstack /browse`：网页浏览、页面测试、截图、线上验活统一走它；不要改用 Chrome MCP
- `addyosmani-test-driven-development`：复杂功能或 bug 修复时先补测试
- `addyosmani-code-review-and-quality`：代码改完后做质量复核
- `addyosmani-security-and-hardening`：登录、支付、上传、数据库、部署链路改动前后使用
- `addyosmani-ci-cd-and-automation`：CI、发布脚本、自动化门禁相关改动使用
- `addyosmani-shipping-and-launch`：发布、上架、候选包整理时使用
- `ui-ux-pro-max` 或同等 UI/UX skill：首页、H5 移动端、uni-app 页面设计时使用

通用 skills 只提供方法论和检查清单，不能覆盖本仓 runbook。涉及生产、数据库、支付、账号、部署时，本仓文档和脚本优先级最高。

### 15.3 Skills 复制边界

不要把当前 Mac 的整个 `~/.codex/skills/`、`~/.agents/skills/` 或外部技能包直接复制进业务仓库。正确做法：

1. Windows 侧自己的 Codex / agent 环境安装对应 skills。
2. 项目内只保留必要的 handoff、runbook 和检查清单。
3. 如果某个技能形成了项目长期规则，再沉淀到 `docs/` 或 `AGENTS.md`，不要复制外部仓库整包。
4. 任何技能脚本如果会联网、发消息、部署、推送、修改第三方资源，默认先只读或 dry-run，得到明确确认后再执行。

### 15.4 给 Windows 侧 agent 的 skills 指令

```text
本项目没有内置 skills/ 目录。你必须先读 AGENTS.md、docs/ops-runbook.md、docs/release/README.md、docs/security-duty-checklist.md、docs/ai-skill-sources.md 和 docs/codex-handoffs/2026-06-17-windows-handoff.md。遇到发布/部署/线上验活，按 xuan-cet-tai-release-qa-loop 的流程执行；遇到生产数据库，按 xuan-cet-tai-safe-db-workflow，只读优先、先备份、先副本验证；遇到 staging，按 xuan-cet-tai-staging-release-isolation，确认 staging-origin 和环境隔离。网页验活统一使用 gstack /browse，不使用 Chrome MCP。
```

## 16. 给 Windows 侧 agent 的第一句话

可以直接把下面这段给 Windows 侧 agent：

```text
你正在接手 xuan-cet-tai 项目。先阅读 AGENTS.md、README.md、docs/ops-runbook.md、docs/release/README.md、docs/security-duty-checklist.md、docs/ai-skill-sources.md 和 docs/codex-handoffs/2026-06-17-windows-handoff.md。不要修改生产数据库，不要提交密钥，不要跳过 git status。本项目没有内置 skills/ 目录；发布验活按 xuan-cet-tai-release-qa-loop，生产数据库按 xuan-cet-tai-safe-db-workflow，staging 按 xuan-cet-tai-staging-release-isolation。先完成本地依赖安装、本地 dev:check、pytest、build:h5、qa:online，再根据任务决定是否部署或打包。部署必须走 scripts/preflight_release.sh -> deploy-to-server.sh -> production_monitor.sh -> qa:online。网页验活统一使用 gstack /browse，不使用 Chrome MCP。
```
