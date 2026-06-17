# 人工事项交接说明

本文件说明 `npm run release:user-actions` 生成的交接包怎么使用。它只整理当前还需要人工、外部后台或明确确认的事项，不会部署线上、不提交商店、不写入任何敏感凭据。

## 生成命令

```bash
npm run release:user-actions
```

输出目录：

```text
artifacts/release-user-actions/<timestamp>-v1.0.0/
```

每次生成包含：

- `README.md`：按“我可以继续做 / 需要你确认后我才能做 / 最后必须你做”分组。
- `report.json`：机器可读清单，包含 `userRequired`、`approvalRequired`、`agentCanContinue` 和每项证据来源。

## 使用顺序

1. 我继续处理 `owner=agent` 的本地工程事项，例如脚本、文档、台账、检查器、summary、Release 草稿和本地 smoke。
2. `owner=approval-required` 的事项必须先等你明确确认，例如部署新版 H5 法律页到 `https://shianjieyouwu.com/`。
3. `owner=user` 的事项需要你登录后台、拿证书、拿真实设备或组织测试人完成；完成后只回传非敏感证据。
4. 回传后运行对应检查，例如 `npm run store:evidence-status`、`npm run store:app-record`、`npm run release:artifact-metadata`、`npm run real-user:roster`。
5. 所有相关检查默认模式无结构性问题后，再运行 strict 模式。

## 需要你回传的材料类型

| 类型 | 回传位置 | 检查命令 |
| --- | --- | --- |
| 商店后台截图、提交编号、隐私和测试轨道证据 | `artifacts/store-evidence-inbox/v1.0.0/<store-id>/...` | `npm run store:evidence-status` |
| 当前批次国内安卓 APP 备案、软著或不适用说明 | `artifacts/store-evidence-inbox/v1.0.0/<store-id>/app-record-screenshot/` | `npm run store:app-record` |
| 当前批次 Android/macOS/Windows 安装包和 hash | `artifacts/release-inbox/v1.0.0/<platform>/` | `npm run release:intake` |
| 安装包构建元数据 | 安装包同目录 `build-metadata.json` | `npm run release:artifact-metadata` |
| 当前批次真实用户测试结果 | `artifacts/real-user-packets/<timestamp>-v1.0.0/<platform>/results/` | `npm run real-user:roster` |
| 真机截图 | 对应 `screenshots/` 或 store evidence inbox | 对应平台检查脚本 |
| 商店提交状态和审核反馈 | `configs/release/store-submissions.json` 和 `docs/release/review-log.md` | `npm run store:submission-status` |

## 当前发行元数据缺口

最新本地可试用产物已经刷新到 `2026-06-16T01:47` 这一轮：

- macOS DMG：`artifacts/desktop-macos-user-packets/2026-06-16T01-38-46-585-v1.0.0/shian-v1.0.0-macos-arm64-user-test.dmg`
- macOS 当前 `.app` zip：`artifacts/desktop-macos-updated-app/2026-06-16T01-42-00-000-v1.0.0/时安解忧屋-updated-app-v1.0.0-macos-arm64.zip`
- Windows x64 安装器：`artifacts/desktop-windows-user-packets/2026-06-16T01-40-38-723-v1.0.0/shian-v1.0.0-windows-x64-user-test-nsis.exe`
- 桌面 URL 友好下载包：`artifacts/desktop-downloads/2026-06-16T02-01-38-358-v1.0.0`，包含最新 macOS DMG、macOS app zip、Windows NSIS 和 `checksums.sha256`。
- Android debug APK/AAB：`artifacts/release-inbox/v1.0.0/android/shian-v1.0.0-android-debug-shell.apk` 和 `artifacts/release-inbox/v1.0.0/android/shian-v1.0.0-android-debug-shell.aab`
- 移动端 App Resource：`artifacts/mobile-app-resource-packets/2026-06-16T01-45-57-662-v1.0.0`
- 当前试用索引：`artifacts/try-now/2026-06-16T01-47-20-097-v1.0.0`
- 最新 HBuilderX 移动端检查：`artifacts/hbuilderx-mobile-resources/2026-06-16T01-53-56-975-v1.0.0`，Android/iOS/鸿蒙均为 `environment-action`。
- 最新商店材料检查：`artifacts/store-materials/2026-06-16T01-58-46-706-v1.0.0`，当前仍缺真实后台证据、备案/不适用说明、法律 URL 线上验证和真机商店截图。
- 最新商店提交交接包：`artifacts/store-submission-packets/2026-06-16T01-58-55-417-v1.0.0`
- 最新商店证据收件台账：`artifacts/store-evidence-status/2026-06-16T01-58-24-321-v1.0.0`
- 最新开发者账号访问台账：`artifacts/store-account-access/2026-06-16T01-58-33-366-v1.0.0`
- 最新 APP 备案台账：`artifacts/app-record-status/2026-06-16T01-58-33-712-v1.0.0`
- 最新人工事项包：`artifacts/release-user-actions/2026-06-16T01-59-18-559-v1.0.0`，其中 `agentCanContinue=0`、`userRequired=6`、`approvalRequired=1`。

最新 `npm run release:artifact-metadata` 当前为 READY 2 / PARTIAL 1 / DEFERRED 2；本轮只要求 Android、Windows 继续回传非敏感证据，iOS 和鸿蒙后续批次恢复：

| 平台 | 当前状态 | 需要补的非敏感证据 |
| --- | --- | --- |
| Android | 已有 `debug-shell` APK/AAB，元数据 partial | 当前 `npm run android:device-smoke` 返回 `no-device`。连接安卓真机并开启 USB 调试后先执行 `npm run android:device-smoke` 自动安装、启动和截图；再回传登录、时安 agent、积分、账号注销截图到 `artifacts/release-inbox/v1.0.0/android/screenshots/`，并把路径填入 `build-metadata.json` 的 `deviceTestEvidence`。 |
| Windows | 安装器已收件，元数据 partial | 在 Windows 10/11 机器安装和卸载后，回传卸载截图到 `artifacts/release-inbox/v1.0.0/windows/screenshots/uninstall.png`。 |
| iOS | deferred | 本轮不上架，不生成 TestFlight/IPA；保留配置，后续恢复 active 后再补 `build-metadata.json`、iPhone/iPad 截图、App Privacy 截图。 |
| 鸿蒙 | deferred | 本轮不上架，不生成 HAP/AppGallery；保留配置，后续恢复 active 后再补 `build-metadata.json`、手机/平板截图、权限触发截图。 |

不要为了让检查变绿而放占位空图或虚假截图；缺真实设备/后台证据时必须保持 partial/missing。

## 移动端专项

移动端当前分成两类证据：

- `npm run mobile:build-env`：检查本机 Java、Gradle、Android SDK、adb、完整 Xcode/simctl、HBuilderX、DevEco/hdc/hvigor 和剩余磁盘空间。
- `npm run mobile:hbuilderx-resources`：通过 HBuilderX CLI 导入项目并尝试生成 Android/iOS/鸿蒙 App Resource。

当前 `npm run mobile:hbuilderx-resources` 能找到 `/Applications/HBuilderX.app/Contents/MacOS/cli`，但 CLI 启动失败：

```text
Incompatible processor. This Qt build requires the following features:
    neon
```

这说明当前安装的 HBuilderX CLI 与本机处理器/运行环境不兼容。处理顺序是：

1. 当前主机架构为 `arm64`，CLI 文件也显示 `Mach-O 64-bit executable arm64`，但运行仍报 Qt processor feature 错误；先重新安装与当前 Mac/系统版本匹配的 HBuilderX，确认 `cli open` 不再报 `neon`。
2. 在 HBuilderX 图形界面确认 DCloud 账号已经登录，并确认当前账号有 App 发行权限。
3. 确认项目已经导入当前仓库目录，而不是旧目录。
4. 重新执行 `npm run mobile:hbuilderx-resources`。
5. 当前批次真正的 APK/AAB、桌面包产出后，放入 `artifacts/release-inbox/v1.0.0/<platform>/`，同时补 `build-metadata.json` 和 sha256；IPA/TestFlight 与鸿蒙 HAP 后续批次再处理。

当前本机已具备 Android SDK/JDK/Gradle/adb 基础环境，并已能生成 `artifacts/release-inbox/v1.0.0/android/shian-v1.0.0-android-debug-shell.apk` 作为内部真机测试入口。正式 Android 商店包仍需要渠道签名、商店账号、正式构建元数据、合规检测和真机截图；iOS 与鸿蒙当前延期，不作为本轮交接包清零条件。证书、签名口令、keystore、p12、mobileprovision 不进 GitHub。

## 禁止回传

不在 GitHub 保存：

- 账号密码、验证码、手机号、邮箱、后台 token。
- keystore、jks、p12、mobileprovision、证书私钥、签名密钥。
- 身份证、营业执照原件、银行卡、真实用户隐私原始数据。
- 只用于占位的空文件或虚假截图。

如果截图里有账号、手机号、邮箱、身份证号、付款信息或用户隐私，先在本地打码，只保留审核状态、应用名、版本号、包名、提交编号、测试轨道、隐私 URL、权限配置和通过/被拒原因。

## 需要明确确认后我才能执行

线上动作必须等你明确确认，包括：

最新只读核验结果：

- `artifacts/legal-url-checks/2026-06-16T01-55-40-455-v1.0.0`：`online=false`。
- `artifacts/h5-legal-deploy-status/2026-06-16T01-55-40-454-v1.0.0`：线上 H5 入口 `fetch failed`，法律页正文和 ICP 页脚未检出。
- `artifacts/domain-https/2026-06-16T01-55-40-462-v1.0.0`：域名台账仍 partial，阻断原因来自法律 URL 状态未 ready。

本地构建里的法律页资源已存在，但线上 `https://shianjieyouwu.com/` 未检出完整法律页；这一步是部署动作，必须等你明确确认。

```bash
CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5
```

部署后再执行：

```bash
LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict
npm run h5:legal-deploy-status -- --strict
```

没有你的明确确认时，我只做只读检查、文档、脚本、台账、构建本地草稿和本地 smoke。

## 放行规则

- `release:user-actions` 不是放行命令，只是人工事项索引。
- 正式宣称“全端可上架候选”前，`release:user-actions` 里的 `userRequired` 和 `approvalRequired` 必须为 0。
- `release:package` 的 `missingHardBlocks` 必须清零。
- `release:readiness -- --strict`、`product:launch-audit -- --strict`、各商店/证据/备案/桌面 strict 检查都必须通过。
