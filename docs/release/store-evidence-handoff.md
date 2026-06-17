# 商店后台证据回传交接

本文件只定义证据回传路径和命名口径，不代表已经提交商店。所有后台截图、提交编号和真机截图都放到 `artifacts/store-evidence-inbox/v1.0.0/`，再运行：

```bash
npm run store:evidence-status
```

正式候选前使用严格模式：

```bash
npm run store:evidence-status -- --strict
```

## 禁止写入

- 审核账号密码、验证码、手机号、邮箱、token、证书、私钥、keystore、p12、mobileprovision。
- 含真实用户隐私的后台原始数据。
- 仅用于占位的空文件。证据目录里只放真实截图、真实 JSON、真实 hash 或真实说明。

## 提交状态 JSON

每个商店的 `submit-status-json/` 目录至少放 1 个 JSON 文件，例如：

```json
{
  "store": "yingyongbao",
  "status": "submitted",
  "submittedAt": "2026-06-15T10:00:00+08:00",
  "appVersion": "1.0.0",
  "artifactPath": "artifacts/release-inbox/v1.0.0/android/shian-v1.0.0-yingyongbao.apk",
  "artifactSha256": "<sha256>",
  "reviewId": "<后台审核编号或工单编号>",
  "notes": "不写账号密码和验证码"
}
```

## 国内安卓

适用：应用宝、华为应用市场、小米应用商店、OPPO 软件商店、vivo 应用商店。

每个商店按同样结构回传：

```text
artifacts/store-evidence-inbox/v1.0.0/<store-id>/
  submit-status-json/
  privacy-url-screenshot/
  permissions-screenshot/
  app-record-screenshot/
  account-deletion-device-screenshot/
  phone-store-screenshots/
```

`<store-id>` 分别是：

- `yingyongbao`
- `huawei`
- `xiaomi`
- `oppo`
- `vivo`

## Google Play

```text
artifacts/store-evidence-inbox/v1.0.0/google-play/
  submit-status-json/
  privacy-url-screenshot/
  data-safety-screenshot/
  testing-track-screenshot/
  account-deletion-console-screenshot/
  phone-store-screenshots/
  tablet-store-screenshots/
```

## Apple App Store

```text
artifacts/store-evidence-inbox/v1.0.0/appstore/
  submit-status-json/
  privacy-url-screenshot/
  app-privacy-screenshot/
  testflight-build-screenshot/
  account-deletion-device-screenshot/
  iphone-store-screenshots/
  ipad-store-screenshots/
```

## 华为 AppGallery / 鸿蒙

```text
artifacts/store-evidence-inbox/v1.0.0/harmony/
  submit-status-json/
  privacy-url-screenshot/
  permissions-screenshot/
  harmony-package-screenshot/
  account-deletion-device-screenshot/
  phone-store-screenshots/
  tablet-store-screenshots/
```

## GitHub Releases 桌面下载

```text
artifacts/store-evidence-inbox/v1.0.0/github-desktop/
  release-draft-json/
  desktop-release-page-screenshot/
  macos-install-screenshots/
  windows-install-screenshots/
  desktop-checksums/
```

## 当前状态

截至 2026-06-15，本地已生成检查器和清单，但证据 inbox 还没有真实后台文件。`npm run store:evidence-status` 必须继续输出 `not-ready`，直到每个目录都有真实回传证据。
