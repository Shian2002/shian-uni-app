# 法律 URL 验证

`store:legal-urls` 用来验证隐私政策和用户协议是否具备商店审核可提交条件。

## 默认本地检查

```bash
npm run store:legal-urls
```

默认模式只做本地静态验证，不访问线上地址。它会检查：

- `configs/release/legal-urls.json` 是否存在 `privacyPolicyUrl` 和 `userAgreementUrl`。
- `src/pages.json` 是否注册 `pages/legal/index`。
- `src/pages/legal/index.vue` 是否同时包含隐私政策、用户协议、账号注销和内容免责声明。
- `docs/legal/privacy-policy.md` 与 `docs/legal/user-agreement.md` 是否保留审核需要的文字口径。
- `dist/build/h5/index.html` 是否已生成。

输出位置：

```text
artifacts/legal-url-checks/<timestamp>-v1.0.0/
```

## 线上验证

线上 H5 部署完成后再执行：

```bash
LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls
```

正式提交商店前使用严格模式：

```bash
LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict
```

严格模式必须满足：

- 两个 URL 都可访问。
- 页面内容包含隐私政策、用户协议、账号注销、数据删除、积分与付费、知识产权、免责声明等关键字。
- URL 已替换为备案域名 HTTPS 地址。
- `configs/release/legal-urls.json` 的 `status` 已从 `candidate` 改为 `ready`。

## 当前状态

当前 `configs/release/legal-urls.json` 已切到 `https://shianjieyouwu.com/#/pages/legal/index?...`，线上域名 HTTPS 可访问。ICP备案号 `粤ICP备2026072162号-1` 已在营销页页脚和关于页展示；正式提交 Apple App Store、Google Play、应用宝、华为、小米、OPPO、vivo 前，还需要生成通过的 `LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict` 报告、回传商店后台 URL 截图，并在完成 APP 备案/不适用说明后把状态改为 `ready`。
