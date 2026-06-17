# 全端发行总览

本目录是时安解忧屋多端发行的唯一台账，覆盖 H5、Android、iOS、鸿蒙、macOS、Windows 的上架材料、测试记录和审核反馈。当前批次以 `configs/release/current-release-scope.json` 为准：先做 H5、Android、macOS、Windows；iOS 和鸿蒙保留配置与证据，后续批次恢复，不作为本轮阻塞。

## 当前推进入口

- `current-gap-plan.md`：当前距离真实上架、真机测试和真实用户验收还差什么。
- `real-user-acceptance.md`：每个端包的人工验收流程和记录模板。
- `platform-acceptance-matrix.md`：全端安装包、截图、真实用户测试、产品链路和 GitHub Release 证据矩阵。
- `npm run release:readiness`：生成当前全端上架证据盘点，默认只产出报告；正式放行前加 `-- --strict`。
- `npm run release:user-actions`：生成“我还能继续做 / 需要你确认后我才能做 / 最后必须你做”的人工事项交接包，不提交商店、不部署线上、不保存敏感凭据。
- `npm run release:try-now`：生成“当前可试用包”统一入口，集中列出 macOS DMG、Windows 安装器、移动端 App 资源、线上登录/积分/时安agent smoke 和最后必须人工处理的证书/商店事项。
- `npm run platform:backend-matrix`：只读汇总 macOS、Windows、Android、iOS、鸿蒙、H5 的包文件存在性、线上登录/积分/时安agent/八字/紫微/奇门/梅花/六爻/择吉/黄历/记录收藏后端请求证据、移动运行时 API 证据和真机缺口；默认不打包、不部署，正式候选前加 `-- --strict`。
- `npm run release:final-package-plan`：只读生成最后一次统一刷新安装包的执行队列、缺失包清单、存储策略和必须你/外部处理的事项；不自动打包、不部署。
- `npm run release:final-preflight`：只读检查最后执行前本机关键输入，覆盖桌面 Electron/asar 依赖、macOS `.app`、H5/App Resource、固定下载入口和后端矩阵；默认不安装、不打包，正式执行由 `release:finalize` 严格调用。
- `npm run release:package-completeness`：只读检查当前批次最终安装包类型是否齐备；本轮覆盖 Android APK/AAB、macOS DMG/App ZIP、Windows EXE/MSI，iOS IPA/TestFlight 和鸿蒙 HAP/AppGallery 标记为 deferred；默认只报告缺口，正式候选前加 `-- --strict`。
- `npm run artifacts:prune -- --keep=2`：只读生成旧报告清理候选，缓解最后打包前存储压力；默认不删除，且不管理 `artifacts/current-downloads/`、`artifacts/release-inbox/`、证书或软著证据目录。
- `npm run release:package-cleanup-plan -- --keep=2`：只读生成旧安装包/中间包清理候选，覆盖 APK/AAB/IPA/HAP/DMG/ZIP/EXE/MSI；默认不删除，且保护 `current-downloads`、`release-inbox`、证书和软著证据目录。
- `npm run release:current-index`：生成当前可试用包、稳定下载入口、后端证据摘要、剩余硬阻塞和最后人工事项的一页索引；默认只报告缺口，最终严格候选前用 `RELEASE_CURRENT_INDEX_STRICT=1 npm run release:current-index`。
- `npm run release:current-downloads`：把当前 macOS、Windows、Android 包和 App 图标放到 `artifacts/current-downloads/` 的固定文件名；优先使用 hardlink，避免重复占用大空间。
- `npm run release:progress`：生成当前发行进度表，按“安装包优先、后端请求验证、真机回收、最后人工/商店项、最终统一刷新”的顺序显示状态、负责人、预计时间和下一步。
- `npm run release:quota-status`：低成本读取现有证据，生成当前可用入口、剩余硬阻塞和额度紧张时优先命令；不构建、不打包、不启动 App。
- `npm run release:low-impact-status`：看视频或需要保持电脑安静时使用，只检查发行重负载进程、磁盘空间和固定下载入口；不构建、不打包、不下载、不启动预览。
- `npm run release:all-platform-status`：只读汇总低影响状态、固定下载入口、最终包完整性、全端后端矩阵、移动端打包阻塞和存储策略；不构建、不打包、不扫描大目录。
- `npm run release:external-handoff`：低成本生成外部硬阻塞回传目录和 README，告诉你 Android/iOS/鸿蒙真包、商店后台、备案和真实用户截图应放到哪里。
- `npm run release:intake`：扫描 `artifacts/release-inbox/`，生成多端安装包收件报告、SHA-256 和硬缺口。
- `npm run mobile:build-env`：检查 Java、Gradle、Android SDK、Xcode、HBuilderX、DevEco 等移动端打包环境，解释 APK/IPA/HAP 缺口。
- `npm run mobile:toolchain-plan`：生成 iOS/鸿蒙工具链准备计划，记录 Xcode 16.2、Xcodes CLI、DevEco/hdc/hvigor、外接盘 APFS 和最后必须你处理的账号/签名动作；不登录账号、不保存证书。
- `npm run mobile:build-requests`：生成 Android、iOS、鸿蒙构建请求包，明确打包输入、线上登录验收证据、回传目录和不可入库的证书边界。
- `npm run mobile:api-evidence`：检查 `dist/build/app` 是否包含线上 API 基址、`fetch` 登录态、`uni.request`、`EventSource` 和 `XMLHttpRequest` 的后端请求归一化证据，防止移动包变成只有页面没有数据的空壳。
- `npm run mobile:app-resource-packet`：生成移动端 App 资源交付包，集中放置 `dist/build/app`、App 图标、Android/iOS/鸿蒙配置、checksum、manifest 和真实安装包回传目录索引；它不是 APK/AAB、IPA/TestFlight 或 HAP。
- `npm run mobile:hbuilderx-resources`：调用 HBuilderX CLI 尝试生成 Android/iOS/鸿蒙 App Resource；如果返回“此功能需要先登录”，报告会标记为 user-action，不伪造成真包。
- `HBUILDERX_CLOUD_PACK_EXECUTE=1 HBUILDERX_CLOUD_PACK_PLATFORM=android npm run mobile:hbuilderx-cloud-pack`：调用 HBuilderX `pack` 云打包入口并记录 `artifacts/hbuilderx-cloud-pack-attempts/*/attempt.json` 和脱敏日志；证书口令不会写入报告。
- `IOS_LOCAL_BUILD_EXECUTE=1 npm run mobile:ios-local-build-attempt`：只读记录完整 Xcode、simctl、Apple 签名身份、provisioning profile 和磁盘余量，输出 `artifacts/ios-local-build-attempts/*/attempt.json`；证书、p12 和描述文件不会进入 GitHub。
- `HBUILDERX_HARMONY_PACK_EXECUTE=1 npm run mobile:hbuilderx-harmony-pack`：调用 HBuilderX `pack app-harmony` 本地打包入口并记录 `artifacts/hbuilderx-harmony-pack-attempts/*/attempt.json` 和脱敏日志；当前主要用于证明 DevEco/hdc/hvigor 是否齐备。
- `npm run release:artifact-metadata`：检查 `artifacts/release-inbox/v1.0.0/*/build-metadata.json`，校验安装包路径、SHA-256、构建工具、构建号、签名状态、截图路径和审核账号交付方式；正式候选前加 `-- --strict`。
- `npm run release:channel-builds`：连续构建 App Store / Google Play 审核渠道 H5，验证支付边界后恢复默认 H5 构建。
- `npm run release:app-icons`：检查 `configs/release/app-icons.json`、`src/static/app-icons/app-icon-1024.png` 和桌面端 icon 资产，确保 Android、iOS、鸿蒙、macOS、Windows 都使用同一个 logo 图标源。
- `npm run release:package`：生成 GitHub Release 本地草稿包，包含上传候选、SHA-256、审计报告引用、不得上传的敏感文件边界和 `missingHardBlocks` 安装包/人工事项/真实用户/法律 URL/隐私披露/商店提交状态硬缺口。
- `npm run release:finalize:plan`：预览 `release:finalize` 的完整执行队列和当前证据，不构建、不打包、不部署；真正最后统一刷新前先跑它。
- `CONFIRM_FINAL_PACKAGE_REFRESH=final-package-refresh:v1.0.0 npm run release:finalize`：明确确认后，按固定顺序重建 handoff、readiness、summary、Release 草稿包和商店材料包，并输出最终索引；不带确认变量会只写 blocked 报告，不执行打包。
- `npm run real-user:roster`：检查 `configs/release/real-user-roster.json`，按当前批次生成 H5、Android、macOS、Windows 每个平台至少 2 个测试槽位、设备覆盖、结果文件和截图目录状态；iOS/鸿蒙槽位保留但 deferred，正式候选前加 `-- --strict`。
- `npm run real-user:dispatch`：生成当前批次真实用户发测分发索引，列出可发测平台、安装包/URL、测试单和不可发测原因。
- `npm run product:launch-audit`：生成产品定位、Tianfu 对标、变现链路、商店截图、真实用户回收状态审计。
- `npm run store:materials`：检查商店材料完整性，覆盖截图场景、隐私 URL、用户协议 URL、Data safety、App Privacy、审核备注、账号注销和支付边界；正式候选前加 `-- --strict`。
- `npm run store:legal-urls`：验证隐私政策和用户协议页面、候选 URL、H5 构建产物；线上部署后用 `LEGAL_URL_CHECK_ONLINE=1` 验证公开可访问。
- `npm run store:privacy`：生成 Apple App Privacy 与 Google Play Data safety 披露检查报告，正式候选前加 `-- --strict`。
- `npm run store:submission-status`：检查 `configs/release/store-submissions.json`，生成各商店提交状态、审核编号、截图回传和整改台账；正式候选前加 `-- --strict`。
- `npm run store:evidence-status`：检查 `configs/release/store-evidence-requirements.json`，生成商店后台截图、Data safety/App Privacy 截图、提交编号、账号注销真机图和桌面 Release 页面证据收件状态；正式候选前加 `-- --strict`。
- `npm run store:account-access`：检查 `configs/release/store-account-access.json`，生成 DCloud、Apple、Google Play、华为、应用宝、小米、OPPO、vivo、GitHub Releases 的访问、2FA、组织资质和签名能力台账；正式候选前加 `-- --strict`。
- `npm run store:app-record`：检查 `configs/release/app-record.json`，按 H5、国内安卓、鸿蒙、iOS、Google Play 分别追踪 APP 备案或不适用说明；正式候选前加 `-- --strict`。
- `npm run domain:https`：检查 `configs/release/domain-https.json` 和 `configs/release/legal-urls.json`，生成 H5/API 域名、DNS、HTTPS、TLS、ICP备案和法律 URL 切换状态；移动端 APP 备案按包名、开发者账号和商店材料台账追踪，正式候选前加 `-- --strict`。
- `npm run h5:legal-deploy-status`：检查本地 `dist/build/h5` 是否包含法律页 chunk，并只读访问 `https://shianjieyouwu.com/` 判断线上是否已部署完整法律页正文和 ICP 备案号；正式候选前加 `-- --strict`。
- `npm run desktop:release-status`：检查 `configs/release/desktop-release-status.json`，生成 macOS/Windows 安装包、SHA-256、签名、公证、真机安装截图和卸载截图缺口；正式候选前加 `-- --strict`。
- `npm run desktop:signing-preflight`：只读检测本机 Developer ID Application、notarytool、codesign、Gatekeeper、Windows signtool/osslsigncode，不保存证书、密码、Apple ID 或签名私钥；正式公开下载前加 `-- --strict`。
- `npm run desktop:bundle`：把当前 macOS DMG/ZIP 和 Windows NSIS 安装器整理到 `artifacts/desktop-downloads/*/`，生成 URL 友好文件名、`checksums.sha256`、`manifest.json` 和下载说明。
- `npm run desktop:release-inbox-sync`：把当前桌面安装包同步到 `artifacts/release-inbox/v1.0.0/`，并用最新布局 smoke、线上接口 smoke 和 SHA-256 重写 macOS/Windows `build-metadata.json`。
- `npm run desktop:verify-macos`：在 macOS 上只读挂载 DMG，检查包内 `.app`、`Info.plist`、主可执行文件和 `icon.icns`；其他系统会生成 skipped 报告，不替代签名、公证和用户首次打开截图。
- `npm run desktop:install-macos-local`：把当前构建出的 `desktop/release/mac-arm64/时安解忧屋.app` 安装到 `/Applications/时安解忧屋.app`，生成本机安装记录，方便先按正常 macOS App 试用。
- `npm run desktop:macos-lifecycle`：打开 `/Applications/时安解忧屋.app` 两次，验证单实例锁只保留一个主进程，并保留 App 打开方便人工查看。
- `npm run desktop:macos-user-packet`：生成当前优先给本人试用的 macOS 包，集中放置 DMG、备用 `.app.zip`、页面截图、checksum、manifest 和打开说明。
- `npm run desktop:windows-user-packet`：生成 Windows 内部试用包，集中放置 NSIS 安装器、页面预览、checksum、manifest 和 Windows 10/11 真机安装/卸载回收清单。
- `store-screenshot-storyboard.md`：商店截图叙事顺序、平台要求和产品转化判断。
- `screenshot-visual-review.md`：人工复核自动截图是否真的无遮挡、可读、可作为 H5 候选素材。
- `desktop-build-evidence.md`：macOS/Windows 桌面端构建产物、hash、签名状态和剩余缺口。
- `mobile-build-evidence.md`：Android、iOS、鸿蒙上架前置资源构建、配置一致性和剩余缺口。
- `platform-build-handoff.md`：Android、iOS、鸿蒙、macOS、Windows 外部打包交接包生成说明。
- `artifact-intake.md`：外部打包机回传 APK/AAB、IPA/TestFlight、HAP、DMG/ZIP、EXE/MSI 后的本地收件和 hash 校验说明。
- `user-action-handoff.md`：`release:user-actions` 的使用顺序、人工回传材料、禁止入库内容和需要明确确认后才能执行的线上动作。
- `legal-url-verification.md`：隐私政策和用户协议 URL 的本地检查、线上验证和 ready 条件。
- `privacy-disclosure.md`：Apple App Privacy / Google Play Data safety 的结构化披露草案、检查命令和未完成证据。
- `app-record-handoff.md`：网站 ICP、国内安卓/鸿蒙 APP 备案和 Apple/Google 不适用说明的交接口径。
- `store-evidence-handoff.md`：应用宝、华为、小米、OPPO、vivo、Google Play、App Store、鸿蒙和 GitHub Releases 的后台截图、提交状态 JSON 和真机截图回传目录。
- `store-checklists.md`：各应用商店材料清单。
- `app-store-privacy-notes.md`：隐私、账号注销、权限、付费和审核备注口径。
- `product-gtm-benchmark.md`：Tianfu Agent 对标、产品短板、变现和营销链路建议。
- `product-strategy-skill-report.md`：用产品策略、变现策略、营销增长 skill 固化的产品策略画布、变现实验和内容板块验收标准。
- `product-content-acceptance.md`：每个内容板块的产品作用、截图验收、GTM 实验和通过标准。
- `npm run store:packet`：生成应用宝、华为、小米、OPPO、vivo、Google Play、Apple App Store、鸿蒙和桌面下载的提交材料包。
- `npm run platform:handoff`：生成五个平台打包人可执行的交接包，明确命令、产物、hash、截图、回填和证书禁入边界。
- `npm run mobile:toolchain-plan`：默认只读；生成 `artifacts/mobile-toolchain-plan/*/`，用于在最终打包前复核 Xcode/DevEco/外接盘/用户签名边界。
- `npm run mobile:build-requests`：生成移动端外部打包请求包，打包人按 `android.md`、`ios.md`、`harmony.md` 回传 APK/AAB、TestFlight/IPA 和 HAP 证据。
- `npm run mobile:hbuilderx-cloud-pack`：默认 dry-run；带 `HBUILDERX_CLOUD_PACK_EXECUTE=1` 时才真正触发 HBuilderX/DCloud 云打包检查。
- `npm run mobile:ios-local-build-attempt`：默认只读；带 `IOS_LOCAL_BUILD_EXECUTE=1` 时按正式尝试记录 iOS 本地构建前置条件，不触发签名或上传。
- `npm run mobile:hbuilderx-harmony-pack`：默认 dry-run；带 `HBUILDERX_HARMONY_PACK_EXECUTE=1` 时才真正触发 HBuilderX 鸿蒙本地打包检查。

## 仓库边界

- 正式主仓：`Shian2002/shian-uni-app`。保存核心源码、非敏感发行配置、文档、测试、运维脚本和 GitHub Release 记录。
- 测试仓：`Shian2002/shian-uni-app-staging`。保存 staging-first 预发布流，危险改动先在测试环境完成验收。
- 不按机型或应用商店拆仓。应用宝、华为、小米、OPPO、vivo、Google Play 共用 Android/Harmony 发行配置，通过渠道模板、包名、证书和 Release 资产区分。
- 只有桌面端或鸿蒙原生工程出现大量独立代码时，才考虑拆出 `shian-desktop-shell` 或 `shian-harmony-shell`。

## 版本台账

每次准备上架或发版，必须记录：

- 版本号、Git commit、构建分支、构建命令。
- 安装包文件名、SHA-256、构建机器和构建时间。
- 测试账号、测试环境、真机型号、测试结论。
- 商店提交状态、审核反馈、整改负责人。
- 是否影响支付、短信、邮件、账号注销、隐私权限。

## GitHub Release 命名

- Android：`vX.Y.Z-android`
- iOS TestFlight：`vX.Y.Z-ios-testflight`
- 鸿蒙：`vX.Y.Z-harmony`
- 桌面端：`vX.Y.Z-desktop`
- 全端正式版：`vX.Y.Z`

安装包和截图可以上传到 GitHub Releases；证书、密钥、keystore、p12、描述文件不得上传。

## 固定门禁

发版前至少执行：

```bash
npm run lint
npm run typecheck
npm run release:check
npm run release:readiness
npm run release:user-actions
npm run release:try-now
npm run platform:backend-matrix
npm run release:final-package-plan
npm run release:final-preflight
npm run release:package-completeness
npm run artifacts:prune -- --keep=2
npm run release:package-cleanup-plan -- --keep=2
npm run release:current-index
npm run release:current-downloads
npm run release:quota-status
npm run release:low-impact-status
npm run release:all-platform-status
npm run release:external-handoff
npm run mobile:build-env
npm run mobile:toolchain-plan
npm run mobile:build-requests
npm run mobile:api-evidence
npm run mobile:app-resource-packet
npm run mobile:hbuilderx-resources
npm run mobile:hbuilderx-cloud-pack
IOS_LOCAL_BUILD_EXECUTE=1 npm run mobile:ios-local-build-attempt
npm run release:channel-builds
npm run release:app-icons
npm run release:intake
npm run release:artifact-metadata
npm run release:package
npm run release:finalize:plan
CONFIRM_FINAL_PACKAGE_REFRESH=final-package-refresh:v1.0.0 npm run release:finalize
npm run real-user:roster
npm run real-user:dispatch
npm run product:launch-audit
npm run store:packet
npm run store:materials
npm run store:legal-urls
npm run store:privacy
npm run store:submission-status
npm run store:evidence-status
npm run store:account-access
npm run store:app-record
npm run domain:https
npm run h5:legal-deploy-status
npm run desktop:release-status
npm run desktop:release-inbox-sync
npm run desktop:verify-macos
npm run desktop:install-macos-local
npm run desktop:macos-lifecycle
npm run desktop:macos-user-packet
npm run desktop:windows-user-packet
npm run store:screenshots
npm run mobile:preflight
npm run test
npm run build:h5
QA_BASE_URL=http://119.29.128.18:8081 npm run qa:staging
QA_BASE_URL=http://119.29.128.18:8081 npm run qa:agent:online
QA_BASE_URL=https://shianjieyouwu.com npm run qa:agent:online
```

正式部署继续沿用现有发布链路：

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

需要回滚 H5 静态资源时：

```bash
CONFIRM_H5_ROLLBACK=shianjieyouwu.com npm run rollback:h5
```

正式标记“可上架候选”前必须额外执行：

```bash
npm run release:readiness -- --strict
npm run product:launch-audit -- --strict
npm run store:materials -- --strict
LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict
npm run store:privacy -- --strict
npm run store:submission-status -- --strict
npm run store:evidence-status -- --strict
npm run store:account-access -- --strict
npm run store:app-record -- --strict
npm run domain:https -- --strict
npm run h5:legal-deploy-status -- --strict
npm run release:artifact-metadata -- --strict
npm run platform:backend-matrix -- --strict
npm run real-user:roster -- --strict
npm run desktop:release-status -- --strict
```

当前批次只要 Android APK/AAB、发行产物元数据、真实用户名册/回传截图、隐私/用户协议 HTTPS URL、域名/备案、App Privacy/Data safety、商店材料、商店后台证据、开发者账号访问、商店提交证据或桌面端签名/公证/真机安装截图仍缺失，严格模式和 Release 草稿包硬缺口都必须保持失败。iOS TestFlight 和鸿蒙包后续恢复 active 后再重新纳入硬缺口。
