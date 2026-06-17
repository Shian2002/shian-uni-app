# 审核反馈记录

每次提交商店审核后，在本文件追加记录。不要写入账号密码、证书口令、密钥或用户隐私数据。

## 模板

```markdown
## YYYY-MM-DD vX.Y.Z 渠道名称

- 平台：Android / iOS / Harmony / macOS / Windows
- 商店：应用宝 / 华为 / 小米 / OPPO / vivo / Google Play / App Store / GitHub Releases
- Git commit：
- 安装包：
- SHA-256：
- 测试账号：
- 提交状态：待提交 / 审核中 / 通过 / 被拒 / 已整改
- 审核反馈：
- 整改动作：
- 复测结论：
```

## 2026-06-14 v1.0.0 本地预审

- 平台：H5 / Android App 资源 / macOS 测试包
- 商店：未提交，仅本地预审和 GitHub Releases 准备
- Git commit：`f6f57f8cad21e2f9317de733190b4b3630c837f5`
- 安装包：macOS 未签名测试 zip；Android/iOS/鸿蒙/Windows 正式安装包未完成
- SHA-256：macOS zip `41139db26d5ff5fd92f0269fce5c8a77cb795eaae7b239c80f84d95cd2f45a23`
- 测试账号：不写入文档；审核账号后续通过安全渠道交付
- 提交状态：待提交
- 审核反馈：暂无商店反馈
- 整改动作：本地修正营销页按钮口径，保留 `时安agent` 主入口，未登录辅助按钮显示 `登录/注册`，登录后进入 `#/?app=1`；补账号注销接口和前端入口；补 Tianfu Agent 竞品取证与产品/GTM 文档
- 复测结论：本地 `qa:agent:local`、`lint`、`typecheck`、`test`、`build:h5`、`build:app`、`mobile:preflight`、`release:check` 已通过；当前批次仍需真实用户真机测试、Android APK/AAB、Windows 安装包和商店后台提交记录；iOS TestFlight 与鸿蒙包后续批次再恢复

## 2026-06-15 v1.0.0 本地复用线上登录预审

- 平台：H5 本地前端 + 线上账号接口
- 商店：未提交，仅用于上架前登录链路核验
- Git commit：本地未提交工作区
- 安装包：无，本轮只验证本地 H5 代理线上登录
- SHA-256：不适用
- 测试账号：不写入文档；使用安全渠道维护
- 提交状态：待提交
- 审核反馈：暂无商店反馈
- 整改动作：新增 `npm run dev:h5:online-login`，启动时临时把 `src/manifest.json` 的 H5 `/api` 代理切到线上，退出后自动恢复；新增 `npm run qa:login:local-online`，只验证 `/api/health`、`/api/login`、`/api/me`。
- 复测结论：`qa:login:local-online` 已通过，报告为 `artifacts/login-smoke/2026-06-14T16-02-43-828Z/report.json`；`qa:agent:local-online-login` 的未登录拦截和路由矩阵已通过，但完整 Agent 请求因线上测试账号 `test1` 积分不足未发出，后续需要积分充足的测试账号或 staging 隔离积分策略。

## 2026-06-15 v1.0.0 商店提交状态台账预审

- 平台：Android / iOS / Harmony / macOS / Windows
- 商店：应用宝 / 华为 / 小米 / OPPO / vivo / Google Play / App Store / GitHub Releases
- Git commit：本地未提交工作区
- 安装包：移动端 APK/AAB、iOS TestFlight/IPA、鸿蒙 HAP 仍未回传；桌面包已有本地测试产物
- SHA-256：以 `release:intake` 和 `release:package` 输出为准
- 测试账号：不写入文档；审核账号后续通过安全渠道交付
- 提交状态：待提交
- 审核反馈：暂无商店反馈
- 整改动作：新增 `configs/release/store-submissions.json` 和 `npm run store:submission-status`，把每个商店的提交状态、审核编号、审核截图、反馈和整改动作变成可检查台账；台账禁止写入账号密码、证书、密钥、验证码或用户隐私数据。
- 复测结论：`store:submission-status` 已生成报告 `artifacts/store-submission-status/2026-06-15T05-06-59-381-v1.0.0/report.json`；当前 9 个渠道均为 `not-submitted`，因此仍不能标记为全端上架候选。
