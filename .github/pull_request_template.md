## 变更摘要

- 

## 影响平台

- [ ] H5
- [ ] Android
- [ ] iOS
- [ ] Harmony
- [ ] macOS
- [ ] Windows
- [ ] 后端/API

## 发行和合规检查

- [ ] 未提交 keystore、p12、mobileprovision、私钥、`.env` 或生产数据库
- [ ] 隐私政策、用户协议、权限说明与实际行为一致
- [ ] iOS 支付入口策略已确认
- [ ] staging 已验证，正式环境未被测试配置污染

## 验证

- [ ] `npm run lint`
- [ ] `npm run typecheck`
- [ ] `npm run release:check`
- [ ] `npm run build:app`
- [ ] `MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight`
- [ ] `npm run test`
- [ ] `npm run build:h5`
- [ ] 涉及上架/真机验收时已执行 `npm run real-user:packet`
- [ ] `npm run qa:staging`
