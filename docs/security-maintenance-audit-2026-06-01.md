# 安全与可维护性巡检记录 2026-06-01

## 已落地

- 后台管理 API 已从 `backend/app.py` 抽离到 `backend/admin_routes.py`，路由路径保持不变。
- 后台用户列表、充值确认、手动加积分继续要求管理员权限。
- 手动加积分支持用户名、邮箱、手机号或 ID，并有 `AdminAuditLog` 审计。
- 本地 `backend/tianji.db`、`server-backup/backend/tianji.db`、`server-backup/backend/.env` 权限已收紧为 `600`。
- 部署脚本安装 Python 依赖时使用 `backend/constraints.txt`，约束 `kinqimen` 依赖的 `ephem` 与 `sxtwl` 版本。
- 增加 `npm run audit:prod`，固定使用官方 npm registry 跑生产依赖审计，避免镜像站不支持 audit 接口。

## 当前风险

- `npm audit --omit=dev` 仍报告 Uni/DCloud 依赖链中的高危与中危漏洞。直接 `--force` 会触发破坏性版本变化，需要单独分支验证 H5、微信/支付宝/头条小程序构建。
- `backend/app.py` 仍然过大，后台管理已经拆出，但社区、充值、排盘、AI、用户体系仍混在主文件里。
- `src/pages/index/index.vue` 仍然承载首页 AI 对话、artifact 渲染、历史恢复、输入栏和流式输出，后续样式和交互修改容易互相影响。

## 下一步建议

1. 继续拆后端：`community_routes.py`、`points_routes.py`、`metaphysics_routes.py`、`auth_routes.py`。
2. 继续拆首页：`useHomeAiStream`、`useHomeArtifacts`、`HomeAiInput`、`HomeArtifactTabs`。
3. 新开依赖升级分支，先升级可自动修复的 `jpeg-js/phin/postcss`，再评估 Uni/DCloud alpha 版本链。
4. 服务器备份策略移到仓库外目录，例如 `/home/lighthouse/backups/xuan-cet/`，并定期校验恢复。
