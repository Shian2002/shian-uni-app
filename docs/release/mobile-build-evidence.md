# 移动端构建证据

> 更新时间：2026-06-17  
> 范围：Android、iOS、鸿蒙上架前置构建。当前批次只继续推进 Android；iOS 和鸿蒙证据保留但按 `configs/release/current-release-scope.json` 延期。当前证据证明 uni-app App 资源构建通过，并已额外生成一个 Android 内部调试壳 APK；它不等同于正式签名 APK/AAB、IPA/TestFlight 或鸿蒙 HAP。

## 2026-06-15 App 资源构建

- 构建命令：`npm run build:app`
- 构建结果：通过
- 输出目录：`dist/build/app`
- HBuilderX 提示：`Run method: open HBuilderX, import dist/build/app run.`
- 预检命令：`MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight`
- App 资源 SHA-256：`e3a524d75c214a5a8dd9df6984053e4cb1353ca320c9116a11cfa20ff90aaa29`
- manifest：`artifacts/release-manifests/2026-06-15T10-47-52-088-current-worktree.json`
- 关键产物：
  - `dist/build/app/__uniappview.html`
  - `dist/build/app/app-service.js`
  - `dist/build/app/app-config.js`

## 2026-06-15 Android 内部调试 APK

- 构建命令：`npm run android:shell:debug-apk`
- 构建结果：通过
- APK：`artifacts/release-inbox/v1.0.0/android/shian-v1.0.0-android-debug-shell.apk`
- 元数据：`artifacts/release-inbox/v1.0.0/android/build-metadata.json`
- 包名：`com.shian.xuanctai`
- 版本：`1.0.0` / `100`
- SHA-256：`84b03dd9e6304b31abdc3c81af7106930a1dfbb8858843ac0a2269eb82337c97`
- 线上入口：`https://shianjieyouwu.com/#/?app=1`
- 用途：真机内部安装、登录、积分、时安 agent 在线功能回归。
- 边界：debug 签名，仅内部测试；不是应用宝/华为/小米/OPPO/vivo/Google Play 正式渠道 APK/AAB，不能作为商店正式提交包。

## App 图标资产

- 图标源：`src/static/images/logo.png`
- 商店和打包母图：`src/static/app-icons/app-icon-1024.png`
- 图标配置：`configs/release/app-icons.json`
- 检查命令：`npm run release:app-icons`
- 检查报告：`artifacts/app-icons/*/report.json`
- 适用范围：Android、iOS、鸿蒙、macOS、Windows 第一版都使用同一个 logo 图标源；HBuilderX、DCloud 云打包、Xcode、DevEco 和商店后台优先使用 1024x1024 母图。

## 当前发行配置

| 平台 | 配置文件 | 包标识 | 版本 |
| --- | --- | --- | --- |
| Android | `configs/release/android-channels.json` | `com.shian.xuanctai` | `1.0.0` / `100` |
| iOS | `configs/release/ios-appstore.json` | `com.shian.xuanctai` | `1.0.0` / `100` |
| 鸿蒙 | `configs/release/harmony-appgallery.json` | `com.shian.xuanctai` | `1.0.0` / `100` |

## 已建立的移动端门禁

```bash
npm run mobile:preflight
MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight
npm run mobile:toolchain-plan
npm run mobile:build-env
npm run mobile:build-requests
npm run mobile:api-evidence
npm run mobile:app-resource-packet
npm run mobile:hbuilderx-resources
HBUILDERX_CLOUD_PACK_EXECUTE=1 HBUILDERX_CLOUD_PACK_PLATFORM=android npm run mobile:hbuilderx-cloud-pack
IOS_LOCAL_BUILD_EXECUTE=1 npm run mobile:ios-local-build-attempt
HBUILDERX_HARMONY_PACK_EXECUTE=1 npm run mobile:hbuilderx-harmony-pack
npm run platform:handoff
npm run release:channel-builds
npm run release:app-icons
npm run release:intake
```

门禁检查：

- `src/manifest.json` 的 Android 包名、iOS Bundle ID、版本号与 `configs/release/*` 一致。
- 应用宝、华为、小米、OPPO、vivo、Google Play 六个 Android 渠道配置存在。
- iOS 付费策略明确：未完成 IAP 前隐藏第三方数字内容充值入口。
- 鸿蒙材料包含隐私政策、权限说明、手机和平板截图要求。
- `src/pages.json` 保留首页、个人中心、积分中心、档案列表、关于我们和主要术数页。
- 本地存在 `dist/build/app/__uniappview.html` 与 `dist/build/app/app-service.js` 时，记录大小与 hash；强制模式下缺少这些文件会失败。旧版 H5 风格 `dist/build/app/index.html` 只作为兼容入口，不再作为 uni-app App 资源硬要求。
- `mobile:toolchain-plan` 会记录 Xcode 16.2、`/Volumes/XcodeAPFS` APFS 外接目标盘、Xcodes CLI、DevEco/hdc/hvigor、HBuilderX，以及必须留到最后由你处理的 Apple/DCloud/华为账号和签名步骤。
- `mobile:build-env` 会检查 Java、Gradle、Android SDK、adb、Xcode、HBuilderX、DevEco/hdc/hvigor 是否可用，生成 `artifacts/mobile-build-env/*/report.json`，并记录 `/Volumes/XcodeAPFS` 的 APFS 和可用空间状态。
- `mobile:build-requests` 会生成 `artifacts/mobile-build-requests/*/`，包含 `android.md`、`ios.md`、`harmony.md`、各平台 JSON 请求、线上登录 smoke/Agent 入口证据、回传目录和证书禁入说明。
- `mobile:api-evidence` 会生成 `artifacts/mobile-api-evidence/*/`，检查 `dist/build/app` 里是否包含线上 API、登录态、`fetch`、`uni.request`、`EventSource`、`XMLHttpRequest` 的运行时代码证据；它证明 App 打包输入具备请求后端的能力，不替代真机功能回归。
- `mobile:app-resource-packet` 会生成 `artifacts/mobile-app-resource-packets/*/`，集中包含 `dist/build/app`、`src/static/app-icons`、Android/iOS/鸿蒙配置、checksum、manifest 和真实安装包回传目录；它只证明打包输入齐备，不证明 APK/AAB、TestFlight/IPA 或 HAP 已生成。
- `mobile:hbuilderx-resources` 会启动 HBuilderX CLI、导入当前项目，并尝试执行 `publish app-android/app-ios/app-harmony --type appResource`；有输出资源才标记 ready，遇到 DCloud 登录/发行权限要求时标记 user-action，不伪造成真包。
- `mobile:hbuilderx-cloud-pack` 会调用 HBuilderX `pack` 云打包入口。默认 dry-run；带 `HBUILDERX_CLOUD_PACK_EXECUTE=1` 时才真正触发 DCloud 服务端检查，并在 `artifacts/hbuilderx-cloud-pack-attempts/*/` 写入 `attempt.json` 与 `output.redacted.log`。脚本会脱敏邮箱、证书密码、keystore 密码和 token。
- `mobile:ios-local-build-attempt` 会只读记录完整 Xcode、simctl、Apple 代码签名身份、provisioning profile 和磁盘余量；带 `IOS_LOCAL_BUILD_EXECUTE=1` 时按正式尝试写入 `artifacts/ios-local-build-attempts/*/attempt.json`，但不会触发签名、上传或保存证书文件。
- `mobile:hbuilderx-harmony-pack` 会调用 HBuilderX `pack app-harmony` 本地打包入口。默认 dry-run；带 `HBUILDERX_HARMONY_PACK_EXECUTE=1` 时才真正触发 DevEco/hdc/hvigor 检查，并在 `artifacts/hbuilderx-harmony-pack-attempts/*/` 写入 `attempt.json` 与 `output.redacted.log`。脚本会脱敏邮箱、签名口令和 token。
- `platform:handoff` 会生成 `artifacts/platform-build-handoffs/*/`，把 Android、iOS、鸿蒙、macOS、Windows 的交接清单放在同一包里。
- `release:channel-builds` 会分别用 `appstore`、`google-play` 渠道构建 H5，并确认受限渠道隐藏第三方数字内容充值入口，最后恢复默认构建。
- `release:app-icons` 会检查移动端图标尺寸、1024x1024 商店母图、桌面端 `.icns`/`.ico`/`.png` 图标，并输出 `artifacts/app-icons/*/report.json`。
- HBuilderX、DCloud 云打包、Xcode 或 DevEco 生成的外部安装包统一放入 `artifacts/release-inbox/v1.0.0/<platform>/`，再用 `npm run release:intake` 生成 SHA-256 和收件报告。

## 2026-06-15 本轮生成证据

- 移动端环境检查：`artifacts/mobile-build-env/2026-06-15T10-46-25-758/report.json`
- 平台打包交接包：`artifacts/platform-build-handoffs/2026-06-15T10-46-26-422-v1.0.0/README.md`
- 移动端构建请求包：`artifacts/mobile-build-requests/2026-06-15T10-46-26-852-v1.0.0/README.md`
- 审核渠道构建报告：`artifacts/release-channel-builds/2026-06-15T10-46-27-129/report.json`
- HBuilderX App Resource 检查：`artifacts/hbuilderx-mobile-resources/*/report.json`

## 2026-06-17 本轮生成证据

- Android HBuilderX 云打包尝试：`artifacts/hbuilderx-cloud-pack-attempts/2026-06-17T01-03-01-995-v1.0.0-android/attempt.json`。结论：HBuilderX 已可调用 DCloud 云打包入口，当前阻塞为 `dcloud-phone-verification`，另有包名未录入和隐私配置 warning。
- iOS HBuilderX 云打包尝试：`artifacts/hbuilderx-cloud-pack-attempts/2026-06-17T01-03-13-571-v1.0.0-ios/attempt.json`。结论：当前阻塞为 `ios-profile-required` 和 `ios-signing-material-required`。
- iOS 本地构建尝试：`artifacts/ios-local-build-attempts/2026-06-17T02-21-16-284-v1.0.0/attempt.json`。结论：`/Volumes/XcodeAPFS` 已是 APFS 且约 465 GiB 可用，磁盘项只剩内置盘临时缓存提醒；实际阻塞为完整 Xcode、simctl、provisioning profile 和 Apple 代码签名身份。
- HBuilderX 三端 App Resource 检查：`artifacts/hbuilderx-mobile-resources/2026-06-17T02-30-08-675-v1.0.0/report.json`。结论：Android、iOS、Harmony 均为 ready，每个平台资源文件 200 个；这证明打包输入已刷新，不等同于最终 APK/IPA/HAP。
- 移动 App Resource packet：`artifacts/mobile-app-resource-packets/2026-06-17T02-35-03-827-v1.0.0/manifest.json`。结论：移动端统一打包输入包已刷新，通过 220 个文件检查，包含 `dist/build/app`、图标母图和 Android/iOS/鸿蒙非敏感配置。
- 鸿蒙 HBuilderX 本地打包尝试：`artifacts/hbuilderx-harmony-pack-attempts/2026-06-17T02-31-07-057-v1.0.0/attempt.json`。结论：HBuilderX 已能执行 `pack app-harmony`，但最终仍阻塞于 `harmony-toolchain-missing`，需要 DevEco Studio/hdc/hvigor 并在 HBuilderX 偏好设置配置鸿蒙开发者工具路径。
- 移动端 API 证据：`artifacts/mobile-api-evidence/2026-06-17T02-30-08-732-v1.0.0/manifest.json`。结论：`dist/build/app` 已刷新且通过请求后端能力检查，检查 68 个文件，无 issues。
- 商店截图候选包：`artifacts/store-screenshots/2026-06-16T19-01-27-100Z/summary.json`。结论：本地 H5 通过线上登录/注册接口生成真实会话，14 张截图全部通过；截图覆盖首页、旧登录弹窗、时安 agent 工作台、积分说明、八字工具和账号注销入口。它是商店素材候选和拍摄参考，不能替代真实安装包截图。
- 商店提交材料包：`artifacts/store-submission-packets/2026-06-17T03-03-27-236-v1.0.0/README.md`。结论：9 个渠道/平台的提交字段、审核备注草稿、法律 URL 和缺口已生成，不包含账号密码、证书或后台 token。
- 商店材料检查：`artifacts/store-materials/2026-06-17T03-03-27-624-v1.0.0/report.json`。结论：截图和审核备注已 ready，剩余 5 项集中在商店后台证据、APP 备案/不适用说明、线上法律 URL 部署验证和真实安装包截图。
- 桌面端线上后端 smoke：`artifacts/desktop-online-login-smoke/2026-06-16T18-35-03-800Z/report.json`。结论：真实 Electron 环境登录 `test1` 成功，`health/login/me/membership/points-log/comprehensive/*/bazi/ziwei/qimen/meihua/liuyao/zeji/records/collections` 共 20 项后端请求均通过。
- Android 真机安装检查：`artifacts/android-device-smoke/2026-06-17T02-35-03-796-v1.0.0/report.json`。结论：当前无 adb device 状态设备，已记录 `no-device`，未把真机验收伪造成通过；连接安卓真机并开启 USB 调试后重跑 `npm run android:device-smoke`。
- 全端后端矩阵：`artifacts/platform-backend-matrix/2026-06-17T03-02-44-266-v1.0.0/report.json`。结论：6 个平台后端请求路径均 ready；当前批次 scoped summary 排除 iOS/鸿蒙，缺口集中在签名/公证、真机截图和 H5 法律页生产部署批准。
- 移动端工具链准备计划：`artifacts/mobile-toolchain-plan/2026-06-17T02-31-06-951-v1.0.0/report.json`。结论：`/Volumes/时安500G` 已清空并重新格式化为 `/Volumes/XcodeAPFS` APFS 外接目标盘，约 465 GiB 可用；Xcodes CLI 2.0.1 已安装；Xcode 16.2 安装命令已准备好；鸿蒙侧已记录华为 DevEco Studio 官方入口、macOS 100GB 硬盘要求、HBuilderX 鸿蒙插件和 `.app-harmony` 资源状态；当前只剩 Apple 下载认证、Apple 签名、DCloud 手机号/应用配置、DevEco 安装路径确认和华为签名资料属于最后人工/账号步骤。
- 最新移动端环境检查：`artifacts/mobile-build-env/2026-06-17T02-15-32-954/report.json`。结论：Android ready，iOS partial，鸿蒙 missing，App Resources ready；报告已记录 Xcodes CLI、`mas` CLI、推荐 Xcode 16.2、`/Volumes/XcodeAPFS` APFS、约 465 GiB 外接可用空间，以及内置盘约 37.6 GiB 的临时缓存风险。
- 最新移动端构建请求包：`artifacts/mobile-build-requests/2026-06-17T02-31-10-356-v1.0.0/README.md`。
- 最新平台打包交接包：`artifacts/platform-build-handoffs/2026-06-17T01-15-39-897-v1.0.0/README.md`。

## 当前结论

- 移动端前置资源构建已通过，HBuilderX 已登录且 `launcher`、`launcher-tools`、`node_modules`、`app-safe-pack`、`amazon-corretto` 插件已补齐，可以生成 Android/iOS/鸿蒙 App Resource；最新 App Resource packet 已刷新，后续最终 APK/IPA/HAP 应使用这一批输入。
- Android 本机基础工具链已就绪，并已生成一个 debug WebView 壳 APK，可用于先在安卓真机看到页面和验证线上登录/积分/时安 agent 请求链路。
- 移动端打包请求包可以先发给打包人执行；它只证明请求材料已整理，不证明 APK/AAB、TestFlight/IPA 或 HAP 已经生成。
- 当前还没有正式签名 APK/AAB，因此不能标记为 Android 上架候选；IPA/TestFlight 和鸿蒙安装包已延期，不作为本轮移动端候选阻塞。
- 当前 Android 权限配置为空数组，符合最小权限原则；后续如增加相机、相册、定位、通知等权限，必须同步更新商店权限说明。
- iOS 后续批次仍按既定策略处理：未接 Apple IAP 前，不在 iOS App 内暴露第三方数字内容充值入口。

## 仍需补齐

- Android：生成 APK/AAB，至少覆盖应用宝、华为、小米、OPPO、vivo、Google Play 的渠道记录和真机截图。
- iOS：deferred，后续恢复 active 后再补完整 Xcode 或 DCloud/HBuilderX iOS 云打包签名环境，生成 TestFlight 构建。
- 鸿蒙：deferred，后续恢复 active 后再补 DevEco Studio/hdc/hvigor 和华为/鸿蒙测试包。
- 真实用户测试：当前批次 H5、Android、macOS、Windows 每个平台至少 2 个测试人或内部用户，按 `real-user-acceptance.md` 留存设备、账号类型、截图和结论。

## 当前本机打包环境结论

当前机器已具备 Android 基础构建工具链：Java 17、Gradle、Android SDK command line tools、platform-tools、build-tools 35、platform android-35、adb 和 sdkmanager 已可用；`mobile:build-env` 当前将 Android 标记为 `ready`。完整 Xcode 或 DevEco Studio 属于大体积工具，剩余空间低于 45 GiB 会作为 warning，不再把已可构建 debug APK 的 Android 工具链误判为 missing。最新证据见 `artifacts/mobile-build-env/*/report.json`。

正式 Android 商店包仍不能直接放行：应用宝、华为、小米、OPPO、vivo 和 Google Play 需要渠道签名、隐私合规检测、渠道截图、正式构建元数据和真机回归证据。正式产物仍需放入 `artifacts/release-inbox/v1.0.0/android/` 并补 `build-metadata.json` 后运行 `npm run release:intake` 和 `npm run release:artifact-metadata`。

iOS 当前已延期；既有记录显示只有 Command Line Tools 入口，缺少完整 Xcode 和 `simctl`，因此不能在本机完成 iOS 模拟器/真机自动化或 TestFlight 构建。后续恢复时再安装与当前 macOS 兼容的完整 Xcode 并配置 Apple Developer 证书后生成 IPA/TestFlight 记录。标准证据由 `IOS_LOCAL_BUILD_EXECUTE=1 npm run mobile:ios-local-build-attempt` 生成到 `artifacts/ios-local-build-attempts/*/attempt.json`。

外接盘 `/Volumes/时安500G` 已按用户授权清空并重新格式化为 `/Volumes/XcodeAPFS`，文件系统为 APFS，约 465 GiB 可用，可以作为完整 `Xcode.app` 的外接目标盘。Command Line Tools 16.2 已安装，`xcodes` CLI 2.0.1 已安装，推荐安装命令为 `xcodes install 16.2 --directory /Volumes/XcodeAPFS --experimental-unxip --no-superuser --empty-trash`；当前实际阻塞是 Apple 下载认证返回缺少 username/password。不要把 Apple 证书、p12、mobileprovision、FASTLANE_SESSION、Apple ID 密码或验证码写进仓库、聊天或发行文档。

当前系统是 macOS 14.8.7。按 Apple 官方 Xcode 支持表，Xcode 16.2 支持 macOS Sonoma 14.5 到 macOS Sequoia 15.x，可作为当前系统优先选择；Xcode 16.3/16.4 需要 macOS Sequoia 15.x 起，不适合作为当前系统的默认安装目标。参考：`https://developer.apple.com/support/xcode/`。

鸿蒙当前已延期；既有 `pack app-harmony` 记录明确返回“未检测到鸿蒙工具链”。后续恢复时再安装 DevEco Studio/hdc/hvigor，并在 HBuilderX 偏好设置里把鸿蒙开发者工具路径指向 DevEco Studio；标准证据由 `HBUILDERX_HARMONY_PACK_EXECUTE=1 npm run mobile:hbuilderx-harmony-pack` 生成到 `artifacts/hbuilderx-harmony-pack-attempts/*/attempt.json`。华为官方入口为 `https://developer.huawei.com/consumer/cn/deveco-studio/` 和 `https://developer.huawei.com/consumer/cn/download/`；官方页面写明 macOS ARM 支持 12/13/14/15/26，硬盘要求 100GB 及以上。

HBuilderX CLI 可用命令已经确认：

```bash
/Applications/HBuilderX.app/Contents/MacOS/cli publish app-android --type appResource --project <repo>
/Applications/HBuilderX.app/Contents/MacOS/cli publish app-ios --type appResource --project <repo>
/Applications/HBuilderX.app/Contents/MacOS/cli publish app-harmony --type appResource --project <repo>
```

这些命令生成的是本地 App Resource，不是 APK/AAB、IPA/TestFlight 或 HAP；如果 HBuilderX 返回“此功能需要先登录”，需要先在 HBuilderX 内完成 DCloud 账号登录和发行权限确认。
