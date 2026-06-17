# GitHub 多端维护规则

## 分支和远端

- `origin/master`：正式主仓，只接收已通过 staging 验收的提交。
- `staging-origin/master`：测试仓，承接预发布、真机验证和商店包预检。
- 功能分支命名建议：`release/android-vX.Y.Z`、`release/ios-vX.Y.Z`、`release/desktop-vX.Y.Z`、`fix/platform-ios-login`。

## Issue 标签

- 平台：`platform:android`、`platform:ios`、`platform:harmony`、`platform:macos`、`platform:windows`
- 设备：`device:phone`、`device:tablet`、`device:desktop`
- 商店：`store:appstore`、`store:google-play`、`store:yingyongbao`、`store:huawei`、`store:xiaomi`、`store:oppo`、`store:vivo`
- 类型：`release`、`review-rejected`、`compliance`、`signing`、`payment`、`privacy`

## Release 资产

GitHub Releases 可以保存：

- APK、AAB、DMG、EXE、MSI 等安装包。
- 截图、商店素材、审核说明。
- SHA-256 清单和测试报告。

本地准备上传前先执行：

```bash
npm run release:check
npm run release:payment-boundary
npm run release:channel-builds
npm run release:user-actions
npm run release:package
```

脚本会在 `artifacts/release-packages/` 下生成 `RELEASE_NOTES.md`、`upload-manifest.json` 和 `checksums.sha256`。这些文件是 Release 草稿依据；真正发布到 GitHub 前仍要人工确认没有证书、密钥、生产数据库或真实用户数据。

`release:package` 的 `missingHardBlocks` 不能只看安装包。当前批次正式 Release 前必须同时清零：Android APK/AAB、桌面包、人工事项交接包 `userRequired/approvalRequired`、当前批次真实用户回收、法律 URL HTTPS/线上验证、App Privacy/Data safety、商店材料完整性和商店提交状态台账。iOS TestFlight/IPA 和鸿蒙 HAP/AppGallery 已在 `configs/release/current-release-scope.json` 标记为 deferred，后续恢复 active 后再重新纳入硬缺口。

## CI 门禁

GitHub Actions 至少覆盖：

- `npm run lint`
- `npm run typecheck`
- `npm test`
- `npm run release:check`
- `npm run release:readiness`
- `npm run release:user-actions`
- `npm run release:payment-boundary`
- `npm run release:channel-builds`
- `npm run build:app`
- `MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight`
- `npm run build`

`release:channel-builds` 会分别构建 App Store 和 Google Play 审核渠道，验证受限渠道构建产物不含外部充值接口、支付宝二维码文件名或付款截图文案，并在结束后恢复默认 H5 构建。

不得保存：

- keystore、jks、p12、mobileprovision、证书私钥。
- `.env`、生产密钥、支付密钥、短信邮件密钥。
- 真实用户数据、生产数据库、验证码日志。

## 拆仓标准

默认不拆仓。只有满足以下条件之一时才开新仓：

- Electron 桌面壳超过少量包装代码，开始拥有独立窗口、自动更新、原生菜单、系统集成和专属测试。
- 鸿蒙工程脱离 uni-app 配置，进入 DevEco 独立工程维护。
- 外包或第三方团队需要隔离权限，不能访问主仓业务代码。
