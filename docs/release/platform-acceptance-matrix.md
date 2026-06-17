# 全端平台验收矩阵

> 更新时间：2026-06-14  
> 原则：本矩阵只记录证据，不记录证书、密钥、账号密码或真实用户隐私。登录、积分和账号体系先复用线上同款逻辑，本地与 staging 只验证流程，不另造一套假登录。

## 1. 上架候选定义

一个版本只有同时具备以下证据，才允许进入“可上架候选”：

- 自动门禁：`npm run lint`、`npm run typecheck`、`npm run test`、`npm run build:h5`、`npm run release:check` 全部通过。
- 全端证据盘点：`npm run release:readiness` 生成 `artifacts/release-readiness/*.json` 和 `*.md`；正式放行前运行 `npm run release:readiness -- --strict`。
- 人工事项清零：`npm run release:user-actions` 生成 `artifacts/release-user-actions/*/report.json`；正式放行前 `userRequired` 和 `approvalRequired` 必须为 0。
- 本地验收：`npm run qa:agent:local` 覆盖真实登录接口和本机后端流程；本机登录未修好时，用 `npm run dev:h5:online-login` 启动本地前端，并优先跑 `npm run qa:login:local-online`，再跑 `npm run qa:agent:local-online-login`，复用线上登录、积分和账号接口。
- staging 验收：`QA_BASE_URL=<staging-url> npm run qa:staging` 和 `QA_BASE_URL=<staging-url> npm run qa:agent:online` 通过。
- 真机验收：当前批次 Android、macOS、Windows 每类至少有一个安装包、一组截图、一份真实用户记录；H5 保留线上截图和回归记录；iOS、鸿蒙延期到后续批次再补。
- 真实用户材料：发测前执行 `npm run real-user:packet`，回收后把截图和结论归档到 Release 或 `docs/release/real-user-acceptance.md`。
- 发行记录：GitHub Release 草稿包含安装包、SHA-256、构建命令、commit、测试账号交付方式、审核说明。

`release:readiness` 默认不代表“可上架”，它只把 READY、PARTIAL、MISSING 证据列出来。只有 strict 模式全部 READY，才允许把版本标成全端上架候选。

## 2. 平台证据矩阵

| 平台 | 当前入口 | 必须产物 | 必须截图 | 必须测试 | 通过标准 |
| --- | --- | --- | --- | --- | --- |
| H5 | `npm run build:h5` | `dist/build/h5`、构建日志、线上 URL | 首页、时安 agent、积分会员页、工具页、个人中心 | `qa:online`、`qa:agent:online` | 登录、问事、工具页、积分说明、历史入口无白屏 |
| Android | `npm run build:app` 或 HBuilderX App 云打包 | APK/AAB、SHA-256、渠道名、版本号 | 应用宝、华为、小米、OPPO、vivo 至少各一张首页或安装截图 | 登录、返回键、软键盘、权限弹窗、支付入口隔离 | 同一代码用渠道配置区分，不按品牌拆仓 |
| iOS | HBuilderX/iOS 工程/TestFlight | IPA/TestFlight 构建号、Bundle ID、审核账号 | iPhone 首页、iPhone Agent、iPad 横竖屏、账号注销入口 | 登录、免费额度、隐私入口、IAP/外部支付边界 | 未完成 IAP 前，iOS 不能展示违规外部充值链路 |
| 鸿蒙 | 华为/鸿蒙构建链路 | AppGallery 包、bundleName、SHA-256 | 手机、平板、权限弹窗、隐私协议 | 登录、Agent、工具页、平板布局、权限触发时机 | 权限说明与实际触发一致，华为审核材料可复现 |
| macOS | `npm run desktop:build` | DMG/ZIP、SHA-256、签名状态 | 安装、首次打开、窗口缩放、登录页 | 打开、登录、Agent、积分页、退出重开 | 第一版走 GitHub Releases 或官网，不急进 Mac App Store |
| Windows | `npm run desktop:build` | EXE/MSI/NSIS、SHA-256、签名状态 | 安装、开始菜单、卸载、窗口缩放 | 打开、登录、Agent、积分页、退出重开 | 安装卸载路径清楚，安全提示可解释 |

## 3. 产品链路验收矩阵

| 链路 | 用户要看到什么 | 当前自动证据 | 还需人工证据 |
| --- | --- | --- | --- |
| 营销首页 | `时安agent`、未登录 `登录/注册`、登录后 `进入应用`、`开始解读`，不是只有登录按钮 | `docs/release/login-agent-entry-evidence.md`、`qa:agent:local` 截图首页和移动端首页 | 真机首屏截图、按钮点击录屏 |
| 旧登录弹窗 | `密码登录`、`验证码登录`、`Gitee 验证登录` 都在 | `user_acceptance_full.mjs` 断言旧登录弹窗文案 | 审核账号登录截图 |
| 时安 agent | 进入后看到输入区、选择命盘、选择术数、历史侧栏 | `积分会员-跳转Agent.png`、Agent 核心流式断言 | 真机键盘遮挡和长文本输出截图 |
| 积分会员 | 看懂短期、长期、复杂问题预计消耗和会员方案 | `积分会员-消耗说明.png`、`积分会员-会员方案.png` | 真实用户是否理解“为什么要买积分”的访谈记录 |
| 工具页转 Agent | 八字、奇门、紫微等结果能继续追问 | 当前仅覆盖工具页不白屏 | 每个工具页结果页一键追问截图 |
| 报告资产 | 完整解读能沉淀成可保存、可复看、可分享的报告 | 尚未完成 | 报告页截图、分享页截图、历史回访记录 |
| 账号注销 | 用户能找到入口并理解注销后果 | `src/pages/profile/index.vue` 入口、`POST /api/account/delete`、账号注销回归测试 | staging/真机入口截图、注销确认页截图、注销后游客态截图 |
| Readiness Audit | 产品、技术、商店、真实用户缺口可被逐项追踪 | `npm run release:readiness` 输出 READY/PARTIAL/MISSING | 每次 Release 草稿附最新 audit md/json |
| 人工事项交接 | 必须人工登录后台、回传真机证据或确认线上动作的事项清楚列出 | `npm run release:user-actions` 输出 `userRequired`、`approvalRequired`、`agentCanContinue` | `userRequired=0`、`approvalRequired=0` 后才能进入全端上架候选 |
| 商店截图素材 | 首页、登录、Agent、积分、工具、注销形成完整叙事 | `npm run store:screenshots` 输出 `artifacts/store-screenshots/*` | 真机安装包截图和最终商店尺寸裁切 |

## 4. 对标 Tianfu Agent 的产品验收问题

每次发版前按下面问题做一次产品复盘：

- 命主是否是长期资产，而不是一次性表单？
- 用户是否在首屏就知道可以问事业、感情、决策、年运这类具体问题？
- 免费体验是否能让用户看到价值，同时不会把完整报告全免费送完？
- 积分消耗是否透明，用户能否预估一次复杂合参要花多少？
- 结果是否有“继续追问、保存报告、查看历史、升级积分”的下一步？
- 多端截图是否展示完整价值链，而不是只展示排盘表格？

## 5. GitHub 归档规则

- 自动报告放在 `artifacts/user-acceptance/<timestamp>/`，提交前可作为本地证据，不默认上传 Git。
- 上架候选的安装包、截图、hash 和审核说明上传 GitHub Releases。
- 商店审核反馈追加到 `docs/release/review-log.md`。
- 真实用户测试记录追加到 `docs/release/real-user-acceptance.md` 或以截图包上传 Release。
- 真实用户发测材料由 `npm run real-user:packet` 生成，未回收截图、结论和 `passedFlows` 必测流程编号前不得标记通过。
- 全端 readiness 报告由 `npm run release:readiness` 生成，未达到 strict 全 READY 前不得标记为全端可上架候选。
- 人工事项交接包由 `npm run release:user-actions` 生成，`userRequired` 或 `approvalRequired` 未清零前不得标记为全端可上架候选。
- 商店素材候选由 `npm run store:screenshots` 生成，正式提交当前批次前仍需用真实包在 Android、macOS、Windows 设备上重截；iOS、鸿蒙恢复时单独补真机图。
- 机型问题用 GitHub Issue 标签管理：`platform:android`、`platform:ios`、`platform:harmony`、`platform:macos`、`platform:windows`、`device:tablet`。
