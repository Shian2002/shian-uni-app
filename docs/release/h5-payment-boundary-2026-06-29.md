# H5 正式站支付入口修复记录

日期：2026-06-29

## 背景

正式站 `https://shianjieyouwu.com/#/pages/points/index` 的积分中心仍展示旧的支付宝二维码充值弹窗。当前代码和后端证据显示，项目里还没有微信支付下单、回调、验签和自动入账链路；现有 `/api/recharge/*` 是支付宝二维码加付款截图识别的人工/半自动充值链路。

## 处理

- 将 `src/utils/releasePolicy.js` 的外部充值入口改为显式渠道开启：只有 `VITE_RELEASE_CHANNEL=h5-recharge`、`internal-recharge` 或 `manual-recharge` 时才展示旧人工充值入口。
- 默认正式站 H5 不展示充值套餐、AI 次数套餐、支付宝二维码、充值弹窗和上传付款截图入口。
- 调整积分页可见文案，避免默认正式站继续出现“充值后”“小额识别到账”等支付暗示。
- 未改动后端订单、积分入账、支付截图识别逻辑；微信支付后续必须按商户配置、回调验签和幂等入账单独接入。

## 验证

本地自动化：

```bash
.venv/bin/pytest tests/payment_boundary_test.py -q
npm run typecheck
npm run lint
npm run release:payment-boundary
npm run build:h5
```

结果：支付边界测试 4 passed，typecheck/lint/payment-boundary/build 均通过。

本地构建页面验活：

- 预览 `dist/build/h5` 后打开 `http://127.0.0.1:4188/#/pages/points/index`
- Playwright 断言可见文本不包含：`支付宝`、`积分充值`、`AI 次数套餐`、`充值后请在账本核对到账记录`、`小额识别通过后自动到账`
- 断言 `#rechargeModal` 数量为 0，充值套餐卡片数量为 0

线上验活：

```bash
BASE_URL=https://shianjieyouwu.com bash scripts/production_monitor.sh
```

结果：健康检查 200，首页 HTML 指向当前构建资源，最近 30 分钟没有后端错误。Nginx 日志中仍可见部署前旧页面请求旧资源的历史 404，不影响当前构建。

线上页面断言：

- 打开 `https://shianjieyouwu.com/#/pages/points/index`
- Playwright 断言同本地：无支付宝、无充值套餐、无充值弹窗、无旧充值文案

Computer Use 本机 Safari 验活：

- Safari 重载 `https://shianjieyouwu.com/?paymentFix=1782708380#/pages/points/index`
- 页面展示积分中心、签到、积分用法、账本说明
- 未再出现旧支付宝弹窗、`积分充值`、`AI 次数套餐` 或二维码付款 UI

## 部署

使用临时 worktree 部署，避免带入当前工作区中无关的本地改动。

```bash
DRY_RUN=1 bash deploy-h5-to-server.sh
CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh
```

部署脚本完成了构建、备份和 rsync 同步。脚本最终退出码为 1 的原因是后置 `store:legal-urls --strict` 仍有历史 warning：`法律 URL 未达到正式商店提交条件`；同步本身已完成，并已通过后续生产监控和线上页面验活。

## 后续

如果要恢复正式站充值入口，不能直接替换二维码或文案为微信支付。需要先完成：

- 微信支付商户配置和服务端密钥管理
- 服务端下单接口
- 支付回调验签
- 订单幂等入账
- 退款/异常订单处理
- 管理后台和账本记录字段梳理
- 线上小额闭环验活
