# APP 备案与不适用说明交接

本文件用于区分网站 ICP、移动端 APP 备案和海外商店不适用说明。当前正式访问域名为：

```text
https://shianjieyouwu.com/
```

网站 ICP 备案号在营销页末尾展示：

```text
粤ICP备2026072162号-1
```

## 检查命令

```bash
npm run store:app-record
```

正式候选前使用严格模式：

```bash
npm run store:app-record -- --strict
```

## 当前口径

| 记录 | 当前状态 | 口径 |
| --- | --- | --- |
| `h5-domain` | `not-required` | H5 网站域名走 ICP 与 HTTPS 台账，不按移动端 APP 备案处理。 |
| `android-cn` | `not-ready` | 国内安卓市场按包名 `com.shian.xuanctai` 准备 APP 备案、软著或后台要求的不适用说明。 |
| `harmony-cn` | `not-ready` | 华为 AppGallery / 鸿蒙按包名 `com.shian.xuanctai` 准备 APP 备案、应用资质或后台要求的不适用说明。 |
| `ios-appstore` | `not-required` | Apple App Store 不使用国内安卓市场 APP 备案入口；仍需完成 App Privacy、审核账号和隐私政策 URL。 |
| `google-play` | `not-required` | Google Play 不使用国内安卓市场 APP 备案入口；仍需完成 Data safety、测试轨道和隐私政策 URL。 |

## 国内安卓回传材料

适用：应用宝、华为、小米、OPPO、vivo。

回传到商店后台证据目录：

```text
artifacts/store-evidence-inbox/v1.0.0/<store-id>/app-record-screenshot/
```

每个市场至少回传：

- APP 备案状态截图，或后台要求的不适用说明截图。
- 如后台要求软著/版权材料，回传上传成功截图或审核状态截图。
- 如后台要求主体证明，回传不含敏感证件号的后台状态截图。

不要把身份证、营业执照原件、证书、密码、验证码或后台 token 放进仓库。

## 鸿蒙回传材料

回传到：

```text
artifacts/store-evidence-inbox/v1.0.0/harmony/app-record-screenshot/
```

至少包含：

- AppGallery / 鸿蒙后台应用资质或 APP 备案状态截图。
- 权限、隐私政策 URL 和应用包名一致性截图。

## H5 与 API 域名

H5/API 域名不承载移动端 APP 备案，继续由以下命令验证：

```bash
npm run domain:https
npm run h5:legal-deploy-status
```

当前 H5 法律页还未部署最新版 chunk，因此 `h5:legal-deploy-status` 必须保持 `not-ready`，直到线上法律页和 ICP 展示都通过严格验证。

## Ready 条件

- `android-cn` 和 `harmony-cn` 只有在后台截图或不适用说明真实回传后才能从 `not-ready` 改为 `ready` 或 `not-required`。
- `h5-domain`、`ios-appstore`、`google-play` 的 `not-required` 必须继续保留清晰理由和证据路径。
- `npm run store:app-record -- --strict` 通过前，Release 包里的 `APP 备案与不适用说明 未通过` 硬缺口不能移除。
