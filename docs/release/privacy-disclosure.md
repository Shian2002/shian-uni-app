# App Privacy 与 Data safety 披露

`store:privacy` 用来把 Apple App Privacy 和 Google Play Data safety 的填写口径变成可检查的本地材料。它区分两个状态：

- `localPassed`：本地结构化披露草案完整，可以作为商店后台填写依据。
- `finalPassed`：人工复核、线上法律 URL、后台截图和账号注销真机截图都齐全，可以进入正式提交。

## 命令

```bash
npm run store:privacy
```

输出位置：

```text
artifacts/privacy-disclosures/<timestamp>-v1.0.0/
```

正式商店候选前运行严格模式：

```bash
npm run store:privacy -- --strict
```

## 配置文件

披露草案保存在：

```text
configs/release/privacy-disclosures.json
```

它覆盖：

- Apple App Privacy：Contact Info、Identifiers、User Content、Sensitive Info、Purchases、Diagnostics。
- Google Play Data safety：Personal info、User content、Financial info、App activity、App info and performance。
- 数据删除：个人中心 -> 账号注销 -> 注销账号与删除数据。
- 传输加密、追踪状态、第三方共享、AI/SMS/邮件/支付服务用途。

## 当前状态

当前 `privacy-disclosures.json` 是 `draft`，`humanReviewStatus` 是 `pending`。这意味着默认 `npm run store:privacy` 可以证明本地草案是否完整，但不能把材料标记为已提交、已审核或最终通过。

正式提交前必须补齐：

- 法务/产品人工复核，把 `humanReviewStatus` 改为 `approved`。
- 按实际上架包 SDK、支付、短信、邮件、AI 服务和日志行为复核每个数据类型。
- App Store Connect App Privacy 截图。
- Google Play Console Data safety 截图。
- 通过的 `LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict` 报告。
- 真实安装包里的账号注销截图。

## 判定规则

- 默认模式通过只代表 `localPassed=true`，用于本地工程门禁和商店后台填写草案。
- 严格模式通过必须满足 `finalPassed=true`，也就是人工复核、线上法律 URL 和商店后台截图全部补齐。
- `finalPassed=false` 时，Release 包里仍必须依靠 `store:evidence-status`、`h5:legal-deploy-status` 和 `store:submission-status` 保留外部证据缺口。

## 禁止事项

- 不把审核账号密码、证书、密钥或后台原始截图写入 Git。
- 不把 `draft` 或 `pending` 材料说成已完成。
- 不在 App Store / Google Play 审核包暴露未合规的第三方数字内容充值入口。
