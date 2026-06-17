# 当前全端发行缺口与推进台账

> 更新时间：2026-06-17  
> 当前原则：先复用线上登录、积分、账号体系做本地和 staging 验收；未完成独立改造前，不另起一套登录逻辑。
> 当前批次：先做 H5、Android、macOS、Windows；iOS 和鸿蒙按 2026-06-17 用户指示延期，不作为本轮上架/打包阻塞。

## 1. 当前已具备

- H5 能构建，基础 lint、typecheck、pytest、发行配置检查已接入。
- 本地用户验收脚本已覆盖营销首页、时安 agent 入口、真实登录接口、旧登录弹窗、移动端视口、主要工具页和 Agent 流式请求。
- GitHub 维护结构已建立：发行文档、非敏感发行配置、Issue 模板、PR 模板、Release 模板、平台标签、Electron 桌面壳目录。
- 对标产品 Tianfu Agent 的工作台、积分、会员和转化链路已形成分析文档。
- 账号注销已补前端入口和后端接口，复用现有线上登录态：`个人中心 -> 账号注销 -> 注销账号与删除数据`，接口为 `POST /api/account/delete`。
- 本地已复核登录/agent 入口：未登录顶部显示 `时安agent` + `登录/注册`，登录后点击 `时安agent` 进入 `#/?app=1`，证据见 `docs/release/login-agent-entry-evidence.md`。
- 已补本地复用线上登录模式：`npm run dev:h5:online-login` 临时把 H5 `/api` 代理到线上，退出后恢复本地配置；`npm run qa:login:local-online` 已验证本地前端可通过线上 `/api/login` 登录 `test1`，并通过 `/api/me` 读回同一用户，最新证据见 `artifacts/login-smoke/2026-06-14T18-30-24-122Z/report.json`。
- 已新增全端 readiness audit：`npm run release:readiness` 生成 READY/PARTIAL/MISSING 报告，默认不阻塞；正式放行前用 `npm run release:readiness -- --strict`。
- 已新增人工事项交接包：`npm run release:user-actions` 会从当前 release package、商店账号、商店证据、APP 备案、真实用户、桌面状态和 H5 法律页部署报告中生成“我可以继续做 / 需要你确认后我才能做 / 最后必须你做”的清单；最新 Release summary 和 Release package 都会引用该交接包，使用说明见 `docs/release/user-action-handoff.md`。
- 已新增 release finalization：`npm run release:finalize` 会按固定顺序重建交接包、审计、summary、Release 草稿和商店材料包，最后输出 `artifacts/release-finalize/*/README.md` 作为本地最终索引。
- 已新增平台打包交接包：`npm run platform:handoff` 会生成 Android、iOS、鸿蒙、macOS、Windows 的打包命令、当前构建证据、截图清单、hash 回填和证书禁入说明；当前批次只要求 Android、macOS、Windows 回填，iOS、鸿蒙后续恢复。
- 已新增移动端构建请求包：`npm run mobile:build-requests` 会生成 Android、iOS、鸿蒙可直接发给打包人的请求文件，写清线上登录验收证据、回传目录、期望文件名和证书禁入边界；最新请求包已引用 iOS 本地构建尝试、Android/iOS HBuilderX 云打包尝试和鸿蒙 `pack app-harmony` 尝试。
- 已新增发行产物收件入口：外部打包机把 APK/AAB、IPA/TestFlight 记录、HAP、DMG/ZIP、EXE/MSI 放入 `artifacts/release-inbox/` 后，执行 `npm run release:intake` 生成 `artifacts/release-artifact-intake/*/report.json` 和 `checksums.sha256`。
- 已新增发行产物元数据检查：外部打包机在每个平台回传目录补 `build-metadata.json` 后，执行 `npm run release:artifact-metadata` 校验版本、commit、构建工具、安装包路径、SHA-256、截图路径和审核账号交付方式。
- 已补桌面测试包元数据：macOS DMG 和 Windows NSIS 测试安装器已在 `artifacts/release-inbox/v1.0.0/{macos,windows}/build-metadata.json` 记录非敏感版本、commit、构建工具、SHA-256 和 smoke 证据；Windows 当前固定下载包为 `artifacts/current-downloads/shian-current-windows-x64.exe`，SHA-256 `5bda487d68965132e54c6eafa39b4b8387ff939417a3fd41c9f30a74601fe98c`；移动端 Android/iOS/鸿蒙元数据仍等待真实包回传。
- 已刷新最终安装包完整性：`npm run release:package-completeness` 当前批次为 5/5 ready，iOS TestFlight/IPA 和鸿蒙 HAP/AppGallery 标记为 deferred；Windows 最新 NSIS 不再作为缺口。
- 已刷新后端请求证据：`artifacts/desktop-online-login-smoke/2026-06-16T18-35-03-800Z/report.json` 在真实 Electron 环境通过 20 项线上后端检查；`artifacts/mobile-api-evidence/2026-06-17T02-30-08-732-v1.0.0/manifest.json` 证明移动端 App Resource 具备线上 API、登录态和请求归一化代码；`artifacts/platform-backend-matrix/2026-06-17T03-02-44-266-v1.0.0/report.json` 当前 6 个平台后端路径均 ready。
- 已刷新移动端打包输入包：`artifacts/mobile-app-resource-packets/2026-06-17T02-35-03-827-v1.0.0/manifest.json` 通过 220 个文件检查；HBuilderX 三端 App Resource 检查 `artifacts/hbuilderx-mobile-resources/2026-06-17T02-30-08-675-v1.0.0/report.json` 显示 Android/iOS/Harmony 均 ready。
- 已记录 Android 真机缺口：`artifacts/android-device-smoke/2026-06-17T02-35-03-796-v1.0.0/report.json` 为 `no-device`，说明当前没有 adb 设备，不能把 Android 真机安装/截图验收标成通过。
- 已执行存储清理：删除旧 Codex 会话目录、SodaMusic 缓存、Yarn Berry 缓存、npm 缓存，以及项目内旧报告/旧安装包候选；内置盘可用空间已提升到约 37-39 GiB。项目内清理使用 `npm run artifacts:prune:apply -- --keep=2` 和 `CONFIRM_PACKAGE_BINARY_CLEANUP=delete-old-packages:v1.0.0 npm run release:package-cleanup-plan -- --keep=2 --apply`，保护 `artifacts/current-downloads/`、`artifacts/release-inbox/` 和当前索引引用的包。
- 本轮再次执行 `npm run artifacts:prune:apply -- --keep=2`，清理旧报告约 14MB；`npm run release:package-cleanup-plan -- --keep=2` 显示旧安装包候选为 0，没有删除任何固定下载包或 release inbox 包。
- 已按用户授权清空外接盘 `/Volumes/时安500G` 并重新格式化为 `/Volumes/XcodeAPFS` APFS，约 465 GiB 可用，可作为完整 `Xcode.app` 外接目标盘；Command Line Tools 16.2 和 `xcodes` CLI 2.0.1 已安装，Xcode 16.2 下载当前卡在 Apple 下载认证，不是磁盘格式问题。
- 已加严 GitHub Release 草稿包硬缺口：`npm run release:package` 当前批次会同时检查 Android APK/AAB、桌面包、当前批次真实用户回收、法律 URL HTTPS/线上验证、App Privacy/Data safety、商店材料和商店提交状态台账；iOS/鸿蒙恢复 active 后再纳入硬缺口。
- 已新增真实用户测试名册：`npm run real-user:roster` 检查 `configs/release/real-user-roster.json`，跟踪每个平台 2 个测试槽位、设备覆盖、结果文件和截图目录；正式候选前不得记录手机号、邮箱、审核账号密码或验证码。
- 已新增商店材料完整性检查：`npm run store:materials` 生成 `artifacts/store-materials/*/report.json`，检查渠道配置、截图场景、隐私政策 URL、用户协议 URL、Data safety、App Privacy、审核备注、账号注销和支付边界；正式候选前加 `-- --strict`。
- 已刷新商店截图和提交草稿：`artifacts/store-screenshots/2026-06-16T19-01-27-100Z/summary.json` 通过 14 张 H5 候选截图；`artifacts/store-submission-packets/2026-06-17T03-03-27-236-v1.0.0/README.md` 生成 9 个渠道/平台审核备注草稿；`artifacts/store-materials/2026-06-17T03-03-27-624-v1.0.0/report.json` 将商店材料缺口收敛到 5 项：商店后台证据、APP 备案/不适用说明、线上法律 URL 部署验证和真实安装包截图。
- 已拆分 App Privacy / Data safety 隐私披露状态：`npm run store:privacy` 默认只证明本地结构化草案 `localPassed=true`，可用于商店后台填写；正式候选仍必须用 `npm run store:privacy -- --strict` 验证 `finalPassed=true`，也就是人工复核、线上法律 URL、后台截图和账号注销真机截图全部齐全。
- 已新增商店提交状态台账：`npm run store:submission-status` 检查 `configs/release/store-submissions.json`，跟踪应用宝、华为、小米、OPPO、vivo、Google Play、App Store、鸿蒙和桌面下载的提交状态、审核编号、截图和整改动作。
- 已新增商店后台证据收件台账：`npm run store:evidence-status` 检查 `configs/release/store-evidence-requirements.json`，跟踪各商店后台截图、Data safety/App Privacy 截图、账号注销真机图、提交编号 JSON 和桌面 Release 页面证据。
- 已新增开发者账号访问台账：`npm run store:account-access` 检查 `configs/release/store-account-access.json`，跟踪 DCloud、Apple、Google Play、华为、应用宝、小米、OPPO、vivo、GitHub Releases 的访问、2FA、组织资质和签名能力，不记录密码、验证码、token 或证书；负责人统一使用非敏感别名 `release-owner`，账号/2FA/资质仍待实际确认。
- 已新增 APP 备案交接文档：`docs/release/app-record-handoff.md` 区分 H5 网站 ICP、国内安卓/鸿蒙 APP 备案和 Apple/Google 不适用说明；当前 `npm run store:app-record` 为 READY 3 / PARTIAL 2 / MISSING 0，国内安卓和鸿蒙仍待后台截图或不适用说明。
- 已新增域名 HTTPS 与备案台账：`npm run domain:https` 检查 `configs/release/domain-https.json` 和 `configs/release/legal-urls.json`；当前法律 URL 已切到 `https://shianjieyouwu.com/`，ICP备案号 `粤ICP备2026072162号-1` 已在营销页页脚和关于页展示，非敏感负责人别名已记录为 `release-owner`。H5/API 域名本身不承载 APP 备案，移动端 APP 备案继续按包名、开发者账号和商店材料台账追踪；域名台账剩余是严格线上法律 URL 验证和商店后台截图。
- 已升级法律 URL 线上校验：`LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls` 会抓取 SPA 入口和同源 JS/CSS 资产，不再只看 `index.html`；当前线上站点还未部署包含 `pages/legal/index` 的最新版 H5 产物，所以法律页仍保持 not-ready。
- 已新增桌面端发布状态台账：`npm run desktop:release-status` 检查 `configs/release/desktop-release-status.json`，跟踪 macOS/Windows 安装包、SHA-256、代码签名、公证、真机安装截图和卸载截图。
- 已新增产品上架审计：`npm run product:launch-audit` 生成产品定位、Tianfu 对标、产品 skill 策略画布、变现链路、商店截图、审核账号资产、真实用户回收状态和人工事项清零状态报告；当前未通过项包括真实用户回收未完成、审核账号可登录但积分/AI 次数不足以完成完整 Agent 审核演示，以及 `release:user-actions` 的 `userRequired/approvalRequired` 尚未清零。
- 已新增首页首问模板：时安 agent 应用态展示 `事业 / 感情 / 合作 / 年运` 四类问题模板，点击只预填问题、不自动发送、不扣积分；最新线上登录入口验收通过，证据见 `artifacts/agent-entry/2026-06-14T18-30-24-385Z/report.json`。
- 已新增 staging/local 审核账号资产预置工具：`npm run qa:audit-account:seed -- --username audit_user --points 120 --ai-single 5 --ai-combo 2 --apply`。脚本默认 dry-run，拒绝 production 和已知生产库路径；线上生产账号加权益仍需后台管理员或受控运维流程。

## 2. 当前未完成

| 模块 | 状态 | 需要完成的证据 |
| --- | --- | --- |
| Android APK/AAB | 已完成 uni-app App 资源构建、移动 API 证据和 App Resource packet，并生成内部 debug-shell APK；HBuilderX/DCloud 云打包已进入服务端检查，当前卡在 DCloud 账号或应用所有者手机号重新验证；本机当前无 adb 设备 | debug APK 可先做真机登录、积分、时安 agent 回归；正式上架仍需 DCloud 手机号验证、包名登记、隐私配置、签名 APK/AAB、SHA-256、至少 5 个渠道真机截图 |
| iOS TestFlight | 已完成 uni-app App 资源构建前置检查、HBuilderX 云打包尝试和本地 Xcode 前置检查；`/Volumes/XcodeAPFS` 已是 APFS 且约 465 GiB 可用，Command Line Tools 16.2 与 `xcodes` CLI 已就绪 | 已延期到后续批次；当前不继续处理 Xcode、Apple Developer、TestFlight 和 App Store |
| 鸿蒙包 | 已完成配置一致性预检和 HBuilderX `pack app-harmony` 尝试；HBuilderX 鸿蒙插件和 `.app-harmony` 资源链路已识别 | 已延期到后续批次；当前不继续处理 DevEco/hdc/hvigor、华为签名和 AppGallery |
| macOS/Windows | 已有 Electron 壳工程，已生成 macOS arm64 未签名测试 zip/DMG 和 Windows x64 NSIS 测试安装器，并已补非敏感 `build-metadata.json`；真实 Electron 线上后端 smoke 已通过；Windows 本机构建需优先使用 `ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/` | 有效签名状态、macOS 公证、Windows 真机安装/卸载截图、窗口适配记录 |
| 真实用户测试 | 未完成 | 测试人、设备、账号、截图、失败问题和复测结论 |
| 真实用户名册 | 已有 `real-user:roster` 检查，待分配和回传 | 当前批次 H5、Android、macOS、Windows 每个平台至少 2 个测试槽位通过；iOS/鸿蒙槽位保留但 deferred |
| 商店提交 | 未提交 | 每个渠道后台状态、审核备注、被拒记录、整改链接 |
| 隐私和账号注销 | 前后端已补，待 staging/真机复测 | 隐私政策 URL、入口截图、注销后游客态截图、权限和数据说明一致 |
| 商店材料完整性 | H5 候选截图和 9 个渠道/平台审核备注草稿已 ready；`store:materials` 剩余 5 项 not-ready | 商店后台证据、APP 备案/不适用说明、线上法律 URL 部署验证、真实安装包截图、Data safety/App Privacy 后台截图 |
| 商店后台证据 | 已有 `store:evidence-status` 收件检查，待后台截图回传 | 应用宝/华为/小米/OPPO/vivo/Google Play/App Store/鸿蒙/GitHub Releases 的后台状态截图和提交编号 |
| 开发者账号访问 | 已有 `store:account-access` 检查，负责人别名已回填；账号访问、2FA、资质、签名能力和非敏感截图仍未 ready | DCloud、Apple、Google Play、华为、国内安卓市场和 GitHub Releases 的访问、2FA、资质、签名能力 |
| APP 备案与不适用说明 | H5、iOS、Google Play 不适用说明已记录；国内安卓和鸿蒙仍 partial | 国内安卓/鸿蒙后台 APP 备案、软著、应用资质或不适用说明截图 |
| 域名 HTTPS 与备案 | 已有 `domain:https` 检查，域名 HTTPS 已通，ICP备案号已展示，H5/API 域名的 APP 备案为不适用 | `https://shianjieyouwu.com/`、隐私/协议 URL、线上验证报告、商店后台 URL 截图 |
| 线上法律页部署 | 本地 H5 产物已包含法律页，线上未部署最新版 chunk | 部署新版 H5 后，`LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict` 通过 |
| Release 草稿包硬缺口 | 已加严，当前仍 not-ready | `release:package` 的 `missingHardBlocks` 必须清零，不能只看安装包 hash |
| 发行产物元数据 | 桌面测试包元数据已回填；Android/iOS/鸿蒙仍缺真实包和 `build-metadata.json`；Windows 卸载截图仍待回传 | 每个平台 `build-metadata.json`，含非敏感构建记录、hash、截图路径和审核账号交付方式 |
| 付费/IAP 边界 | 待产品决策 | iOS/Google Play 是否隐藏外部充值或接入官方支付的明确规则 |
| 线上 Agent 完整验收 | 登录已通，付费请求未通 | 当前 `qa:agent:local-online-login` 卡在测试账号 `test1` 积分不足；staging/local 可用 `qa:audit-account:seed` 预置资产，线上生产账号仍需后台管理员或受控运维流程 |

## 3. 下一阶段执行顺序

1. **先做 staging 预发布验收**：推测试仓，部署 staging，确认线上登录、积分、Agent、历史记录、账号注销入口都能跑通。
2. **生成 readiness 报告**：执行 `npm run release:readiness`，确认当前缺 APK/TestFlight/鸿蒙/Windows/真实用户/商店反馈哪些证据。
3. **生成移动端构建请求包**：当前先使用 Android 打包输入、线上登录证据和回传目录；iOS/鸿蒙请求包保留给后续批次。
4. **生成 Android 第一批测试包**：应用宝、华为、小米、OPPO、vivo 共用代码，先用渠道配置和截图区分，不为每个市场拆仓。
5. **收件并校验安装包**：把外部产物放入 `artifacts/release-inbox/v1.0.0/<platform>/`，执行 `npm run release:intake`；产物齐全后执行 `npm run release:intake -- --strict`。
6. **检查商店材料完整性**：执行 `npm run store:materials`，补隐私政策 URL、用户协议 URL、Data safety、App Privacy、审核备注和真实安装包截图缺口。
7. **生成桌面测试包**：macOS/Windows 第一版走 GitHub Releases 或官网下载安装，不进入 Mac App Store/Microsoft Store。
8. **组织真实用户验收**：当前批次每个平台至少 2 个真实用户或内部测试人，按 `real-user-acceptance.md` 留截图和结论。
9. **分批提交商店**：当前先处理国内安卓、Google Play 准备材料和 GitHub Releases 桌面下载；iOS/鸿蒙后续恢复。

## 4. 本地验收必须覆盖

- 营销首页必须能看到 `时安agent`；未登录时辅助按钮显示 `登录/注册`，登录后辅助按钮才显示 `进入应用`，不能用旧登录按钮替换 agent 入口。
- 旧登录弹窗仍保留 `密码登录`、`验证码登录`、`Gitee 验证登录`，便于现有用户路径继续使用。
- 本地 QA 使用真实登录接口，不能只用 localStorage 假状态替代。
- 本机登录未修好时，先用 `npm run dev:h5:online-login` + `npm run qa:login:local-online` 验证线上登录态；完整 Agent 流程必须使用积分充足的测试账号。
- Agent QA 分两层：`npm run qa:agent:entry-online-login` 只验 `时安agent` 入口、旧登录弹窗、登录后进入应用态和积分页入口，不消耗积分；`npm run qa:agent:local-online-login` 才验完整 stream/消费流，必须使用积分充足账号。
- 完整 Agent 流程前先跑 `npm run qa:audit-account`，确认测试账号积分、单术数次数、多术数合参次数和每日轻量额度足够；这条预检只读账号资产，不发起 stream、不扣积分。
- staging/local 若账号资产不足，先 dry-run `npm run qa:audit-account:seed -- --username audit_user`，确认目标库和账号无误后再加 `--apply`；禁止用该脚本直接改线上生产库。
- 从营销首页进入工具页后，八字、奇门、紫微、塔罗、择吉不能出现白屏。
- 移动端 375/390 视口下，顶部入口、Agent 输入区、底部工具选择不能互相遮挡。

## 5. 产品化验收重点

- 用户首次进入时，应先知道“可以问什么”，而不是先理解工具名。
- 结果页要引导继续追问、保存报告、查看历史和升级积分。
- 付费页要解释“短期问题、长期问题、复杂问题”的预计消耗，降低积分焦虑。
- 每次完整解读应沉淀成报告资产，作为分享、复购和客服解释的依据。
- 商店截图不要只展示表单，要展示“问事 -> 选术数 -> 解读 -> 报告”的完整价值链。

## 6. 版本放行口径

一个版本只有同时满足以下条件，才允许标记为可上架候选：

- `npm run lint`
- `npm run typecheck`
- `npm run test`
- `npm run build:h5`
- `npm run release:check`
- `npm run release:readiness`
- `npm run release:user-actions`
- `npm run mobile:toolchain-plan`
- `npm run mobile:build-requests`
- `npm run release:intake`
- `npm run release:artifact-metadata`
- `npm run release:package`
- `npm run product:launch-audit`
- `npm run store:materials`
- `npm run store:submission-status`
- `npm run real-user:roster`
- `npm run store:evidence-status`
- `npm run store:account-access`
- `npm run domain:https`
- `npm run desktop:release-status`
- `npm run qa:agent:entry-online-login`
- `npm run qa:audit-account`
- staging 真机验收通过
- 当前批次至少一个 Android 包、macOS/Windows 桌面包有构建记录和真机验收记录；iOS TestFlight 包和鸿蒙测试包后续恢复 active 后再补
- GitHub Release 草稿包含安装包、hash、截图、审核说明和测试账号交付方式

正式宣称“当前批次可上架候选”前，必须执行 `npm run release:readiness -- --strict` 和 `npm run product:launch-audit -- --strict` 并全 READY；当前只要缺少 Android APK/AAB、发行产物元数据、桌面签名/公证/真机安装截图、真实用户名册/回传、商店后台证据、开发者账号访问、域名备案/线上验证或商店提交记录，strict 就必须失败。iOS TestFlight 和鸿蒙包后续恢复 active 后再重新计入。
