# 安全与可维护性巡检记录 2026-06-01

## 已落地

- 后台管理 API 已从 `backend/app.py` 抽离到 `backend/admin_routes.py`，路由路径保持不变。
- 后台用户列表、充值确认、手动加积分继续要求管理员权限。
- 手动加积分支持用户名、邮箱、手机号或 ID，并有 `AdminAuditLog` 审计。
- 本地 `backend/tianji.db`、`server-backup/backend/tianji.db`、`server-backup/backend/.env` 权限已收紧为 `600`。
- 部署脚本安装 Python 依赖时使用 `backend/constraints.txt`，约束 `kinqimen` 依赖的 `ephem` 与 `sxtwl` 版本。
- 增加 `npm run audit:prod`，固定使用官方 npm registry 跑生产依赖审计，避免镜像站不支持 audit 接口。
- 前端生产依赖审计已从 30 个漏洞降到 2 个中危：补齐 `@intlify/*`、`esbuild`、`jpeg-js`、`phin`、`postcss` 的安全覆盖版本。
- 当前 `npm run build:h5` 和 `python3 -m pytest -q` 均已通过。
- 增加 `scripts/db_backup.py` 与 `scripts/db_restore.py`，使用 SQLite backup API 做一致性备份，恢复前会自动保留安全副本。
- 部署脚本的生产库备份已移动到 `/home/lighthouse/backups/xuan-cet/db/`，默认保留最近 30 份部署备份。
- 增加 `scripts/production_smoke.py`，用于部署后检查健康接口、首页资源、普通用户后台拒绝和管理员后台访问。
- 后端进一步拆出 `backend/ops_routes.py`、`backend/auth_routes.py`、`backend/bazi_history_routes.py`、`backend/points_routes.py` 与 `backend/profile_routes.py`，降低 `backend/app.py` 路由堆积。
- 首页 AI 抽出 `homeAiUtils.js` 与 `useHomeAiDraft.js`，把 HTML 转义、术语清理、本地草稿保存/恢复从主页面里剥离。

## 当前风险

- `npm audit --omit=dev` 仍报告 `@dcloudio/uni-mp-weixin` 依赖链中的 `ws` 中危漏洞，npm 标记为 `No fix available`。当前 H5 线上部署不直接使用微信小程序运行时，但锁文件仍会被审计扫到。
- DCloud 提示存在 `5.11 alpha` 更新。该更新属于整套 Uni/DCloud 平台链升级，风险高于单点安全覆盖，建议单独做小程序/H5 兼容验证后再切换。
- `backend/app.py` 仍然过大，后台管理、基础账号、健康检查、八字历史、会员积分、命盘档案已经拆出，但社区、充值、排盘、AI、第三方/验证码登录仍混在主文件里。
- `src/pages/index/index.vue` 仍然承载首页 AI 对话、artifact 渲染、输入栏和大部分流式输出，后续还应继续拆 `HomeAiInput` 与 `HomeArtifactTabs`。

## 下一步建议

1. 继续拆后端：`community_routes.py`、`points_routes.py`、`metaphysics_routes.py`、`auth_routes.py`。
2. 继续拆首页：`useHomeAiStream`、`useHomeArtifacts`、`HomeAiInput`、`HomeArtifactTabs`。
3. 单独评估 Uni/DCloud alpha 版本链，重点验证 H5、微信/支付宝/头条小程序构建与运行时兼容性。
4. 服务器备份策略移到仓库外目录，例如 `/home/lighthouse/backups/xuan-cet/`，并定期校验恢复。
