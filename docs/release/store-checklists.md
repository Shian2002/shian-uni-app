# 应用商店上架清单

## 通用材料

本地整理提交资料：

```bash
npm run store:packet
npm run store:materials
npm run store:submission-status
```

脚本会在 `artifacts/store-submission-packets/` 下按商店生成 `README.md` 和 `submission.json`。它只整理提交材料、审核备注、证据和缺口，不会上传或提交到任何商店。
`store:materials` 会在 `artifacts/store-materials/` 生成材料完整性报告，检查截图场景、手机/平板/桌面尺寸、隐私政策 URL、用户协议 URL、Data safety、App Privacy、审核备注、账号注销和支付边界；正式上架候选前执行 `npm run store:materials -- --strict`。

`store:submission-status` 会读取 `configs/release/store-submissions.json`，在 `artifacts/store-submission-status/` 生成每个商店的提交状态、审核编号、审核截图、反馈和整改台账。正式候选前执行 `npm run store:submission-status -- --strict`；只要仍有 `not-submitted`、缺审核编号、缺截图或缺产物 hash，就不能标记为全端上架候选。

- 应用名称：时安解忧屋。
- 应用分类：生活服务、传统文化、工具或娱乐，按商店审核口径选择。
- 应用简介、详细描述、关键词、版本更新说明。
- 图标、启动图、手机截图、平板截图、桌面截图。
- 商店截图候选可先用 `npm run store:screenshots` 生成，正式提交前必须用真实安装包在对应设备重截。
- 隐私政策 URL、用户协议 URL、账号注销或数据删除入口。
- 测试账号和审核说明，必须能进入核心功能。
- 权限说明和第三方 SDK 清单。
- 软著、ICP备案、APP 备案、运营主体证明，按商店要求提交。

## 国内安卓市场

适用：应用宝、华为、小米、OPPO、vivo。

- Android 包名、签名证书、版本号、渠道标识一致。
- APK 或 AAB 能安装、升级、登录、访问正式 API。
- 首次启动前不采集个人信息，不提前申请无关权限。
- 支付、短信、邮件走正式环境配置；测试包必须走 staging 隔离配置。
- 备案号、隐私政策、用户协议、账号注销入口可见。
- 商店截图至少覆盖：首页主入口、旧登录弹窗、时安 agent、积分说明、工具页、账号注销。

## Google Play

- 准备 AAB、目标 API 等级、Data safety 表单。
- 明确收集的数据类型、用途、共享方和删除方式。
- 准备测试账号和审核路径说明。
- 若涉及数字内容或积分包，确认是否触发 Google Play Billing 要求。

## Apple App Store

- 准备 Bundle ID、证书、描述文件、App Store Connect 记录。
- 完成 App Privacy、年龄分级、审核备注、测试账号。
- iOS 端不得直接暴露不符合审核要求的第三方数字内容充值入口。
- 若积分、AI 次数包或付费内容在 iOS App 内销售，优先按 Apple IAP 改造；未改造前默认隐藏充值入口。
- 截图必须包含 iPhone 和 iPad；账号注销、隐私入口和 App Privacy 口径要一致。

## 鸿蒙

- 使用鸿蒙发行配置和华为开发者后台资料。
- 真机覆盖鸿蒙手机和平板。
- 不把 Android 包当作鸿蒙交付物；鸿蒙包单独记录构建命令和审核状态。
- 截图必须覆盖鸿蒙手机和平板，并展示权限触发前后的说明一致性。

## 桌面端

- macOS、Windows 第一版走官网或 GitHub Releases 下载。
- 记录安装包 SHA-256、签名状态、系统版本、升级路径。
- 暂不进入 Mac App Store 或 Microsoft Store，除非后续明确投入审核工作。
