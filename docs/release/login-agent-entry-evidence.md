# 登录与时安 agent 入口本地验收

> 验收时间：2026-06-14  
> 本地地址：`http://127.0.0.1:5173/#/`  
> 后端地址：`http://127.0.0.1:5199`  
> 原则：复用现有线上同款登录接口和登录态，不另造一套本地假登录。

## 0. 本地复用线上登录的启动方式

默认本地开发仍走本机 Flask：`npm run dev:h5` + `npm run dev:backend`。

如果当前本机登录还没改好，需要“本地前端 + 线上登录/账号接口”验收，使用：

```bash
npm run dev:h5:online-login
```

这条命令会把本地 H5 的 `/api/*` 代理到 `https://shianjieyouwu.com`，前端页面仍在本地打开。需要临时指向 staging 时可以覆盖：

```bash
VITE_API_PROXY_TARGET=http://119.29.128.18:8081 npm run dev:h5:online-login
```

启动后再跑本地前端验收：

```bash
npm run qa:login:local-online
npm run qa:agent:local-online-login
```

`qa:login:local-online` 只验证本地前端代理下的 `/api/health`、`/api/login`、`/api/me`，用于确认本地已经拿回线上登录态。`qa:agent:local-online-login` 会继续跑页面矩阵和 Agent 流程；如果线上测试账号积分不足，可能停在 Agent 付费请求前。

注意：该模式会连接真实线上账号体系，只使用测试账号，不触发真实短信、邮件和支付。

## 1. 当前按钮策略

- 营销页顶部保留 `时安agent`，作为主产品入口。
- 未登录时，右侧辅助按钮显示 `登录/注册`，点击后仍走现有登录弹窗。
- 登录后，右侧辅助按钮显示 `进入应用`，点击进入应用态。
- `开始解读` 仍作为首屏主 CTA，点击后如果未登录会打开旧登录弹窗。

这样处理后，顶部不再让用户把“进入应用”误解成登录按钮，同时不会隐藏原来的 `时安agent` 入口。

## 2. 本地验收结果

| 场景 | 证据文件 | 结论 |
| --- | --- | --- |
| 桌面营销页首屏 | `artifacts/browser-evidence/2026-06-14-login-agent/06-marketing-desktop-auth-cta-fixed.png` | `时安agent` 可见，辅助按钮显示 `登录/注册` |
| 移动营销页首屏 | `artifacts/browser-evidence/2026-06-14-login-agent/07-marketing-mobile-auth-cta-fixed.png` | `时安agent` 可见，辅助按钮显示 `登录/注册`，无横向溢出 |
| 未登录点击 agent | `artifacts/browser-evidence/2026-06-14-login-agent/02-after-agent-click-guest.png` | 打开旧登录弹窗，包含密码登录、验证码登录、Gitee 验证登录 |
| 登录后点击 agent | `artifacts/browser-evidence/2026-06-14-login-agent/04-after-agent-click-logged-in.png` | 进入 `#/?app=1`，显示时安 agent 应用态 |

自动摘要：

- `artifacts/browser-evidence/2026-06-14-login-agent/auth-cta-fixed-summary.json`
- `artifacts/browser-evidence/2026-06-14-login-agent/mobile-auth-cta-fixed-summary.json`
- `artifacts/browser-evidence/2026-06-14-login-agent/logged-in-agent-summary.json`

## 3. 竞品对照

Tianfu Agent 的首页结构是：

- 顶部右侧保留 `Log In`。
- 首屏主 CTA 是 `Start Chat`。
- 未登录点击 `Start Chat` 会打开登录/注册弹窗。

取证文件：

- `artifacts/competitor-research/2026-06-14-tianfu/01-home-hero.png`
- `artifacts/competitor-research/2026-06-14-tianfu/06-start-chat-click.png`
- `artifacts/competitor-research/2026-06-14-tianfu/summary.json`
- `artifacts/competitor-research/2026-06-14-tianfu/start-chat-summary.json`

对我们的判断：未登录先登录的流程可以保留，但按钮文案必须区分“产品入口”和“账号入口”。`时安agent` 和 `开始解读` 承担产品入口，`登录/注册` 承担账号入口。

## 4. 后续真机验收

- Android、iOS、鸿蒙、平板都要截图确认顶部 `时安agent` 和 `登录/注册` 不重叠。
- 审核账号登录后要截图确认 `登录/注册` 变为 `进入应用`。
- 未登录点击 `时安agent`、`开始解读`、底部 `进入应用` 都必须打开同一个旧登录弹窗。
- 登录后点击 `时安agent` 必须进入 `#/?app=1`，不能停留在营销页。
