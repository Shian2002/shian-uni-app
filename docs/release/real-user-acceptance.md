# 真实用户验收清单

本清单用于每个端包上架前的真实用户测试。测试人员可以是内部成员、审核专用账号或灰度用户，但不能使用生产真实用户数据做破坏性测试。

## 生成测试包

每次准备真实用户测试前，先生成可分发的验收材料：

```bash
npm run real-user:packet
```

脚本会读取 `configs/release/current-release-scope.json`，当前批次只在 `artifacts/real-user-packets/` 下生成 H5、Android、macOS、Windows 目录。iOS 和鸿蒙保留名册配置但标记为 deferred，后续恢复 active 后再生成对应目录。

测试包会自动附带当前已经通过的参考证据：商店截图候选、本地复用线上登录 smoke、本地用户验收、readiness audit 和 release summary。平台 README 里的参考截图只用于告诉测试人“要拍什么画面”，不能替代真实设备、真实安装包或真实浏览器截图。

注意：测试包只是材料模板，不代表真实用户测试已完成。当前批次每个平台至少需要 2 个测试人的通过结果。只有回收测试人、设备、系统版本、安装包、截图和结论后，才允许把对应平台标记为真实用户验收通过。

## 生成发测分发索引

生成测试包后先检查名册：

```bash
npm run real-user:roster
```

名册配置在 `configs/release/real-user-roster.json`。它只记录测试槽位、设备组、结果文件和截图目录，不写手机号、邮箱、审核账号密码、验证码或 token。正式候选前运行：

```bash
npm run real-user:roster -- --strict
```

当前批次每个平台至少 2 个测试槽位必须是 `passed`，并且 `resultPath`、`screenshotDir` 指向真实回传文件；iOS/鸿蒙 deferred 槽位不计入本轮失败。

生成测试包后执行：

```bash
npm run real-user:dispatch
```

脚本会在 `artifacts/real-user-dispatch/` 下生成总索引，按当前批次 H5、Android、macOS、Windows 列出：

- 当前应发给测试人的平台验收单。
- 对应安装包、DMG、EXE/MSI 或 URL 是否已收件；TestFlight 和 HAP 后续批次恢复。
- 商店材料、App Privacy / Data safety、法律 URL 是否已通过。
- 当前平台是否可以发测；如果不能，会列出缺少安装包、隐私材料未通过、法律 URL 未通过等原因。

`real-user:dispatch` 只判断“能不能发给测试人”，不代表真实用户测试已经通过。正式候选前仍必须回收 `results/tester-*.json`、8 张标准截图和全部 `passedFlows`。

## 回收验收

测试人回传后，当前批次每个平台目录必须补齐：

- `results/tester-1.json`、`results/tester-2.json`：填写测试人、设备、系统版本、渠道、安装包/URL、hash 或构建号、账号类型、结论。
- `result.json`：旧格式兼容文件；可保留，但正式候选以 `results/*.json` 的多测试人结果为准。
- `result.example.json`：通过案例示例，只能参考字段结构，不能直接改名当正式结果。
- `screenshots/`：至少包含 `01-home.png`、`02-login-modal.png`、`03-agent.png`、`04-points.png`、`05-tool-bazi.png`、`06-tool-qimen.png`、`07-tool-ziwei.png`、`08-delete-account.png`。
- `referenceEvidence`：脚本自动写入，不要当成通过结论；真实验收通过必须仍然补齐本平台截图。

回收后执行：

```bash
npm run real-user:check
```

脚本会生成 `artifacts/real-user-results/*.json` 和 `*.md`，列出当前批次每个平台是否 READY。正式标记上架候选前必须执行：

```bash
npm run real-user:check -- --strict
```

当前批次每个平台的结果 JSON 不能只写“通过”。测试人必须把已通过的必测流程编号填入 `passedFlows`，至少包括：

- `privacy-entry`
- `permission-timing`
- `login-register`
- `agent-entry-button`
- `agent-login-modal`
- `legacy-login-methods`
- `agent-workbench`
- `question-templates`
- `points-pricing`
- `tools-open`
- `history-report-entry`
- `delete-account-entry`
- `session-restore`

只要当前批次有平台少于 2 个测试人通过、没有填全 `passedFlows`、没有 8 张标准截图、结论不是“通过”、字段仍是“示例/待填写/TODO/TBD/example/placeholder”等占位内容，或触发真实短信/邮件/支付，严格模式必须失败。

## 自动验收分层

本地和 staging 先把不消耗积分的入口链路单独跑通：

```bash
npm run qa:agent:entry-online-login
```

这条链路只验证首页 `时安agent`、`登录/注册`、旧登录弹窗、线上登录态、登录后进入 `#/?app=1`、积分页入口和移动端视口，不证明完整解读已付费完成。

完整 Agent stream/消费流继续使用：

```bash
npm run qa:audit-account
npm run qa:agent:local-online-login
```

完整 stream 链路必须使用积分充足测试账号；如果 `qa:audit-account` 显示 `fullAgentReady=false`，说明账号资产不足，不能把入口验收失败和完整消费验收失败混在一起判断。

当前最新可分发模板：

- `artifacts/real-user-packets/2026-06-15T-reference-evidence-v1/`
- 新生成模板会包含 `results/tester-1.json` 和 `results/tester-2.json` 两个测试人结果文件。

当前最新回收检查：

- `artifacts/real-user-results/2026-06-14T16-44-15-107Z.md`
- 结论：未通过，当前批次最新检查为 `READY=0 MISSING=4`，原因是 H5、Android、macOS、Windows 还未回收至少 2 个真实设备测试人填写结果和标准截图；iOS/鸿蒙 deferred。

## 测试账号

- 普通用户：用于注册、登录、基础排盘、首页综合解读。
- 有积分用户：用于积分消费、付费内容预览、历史记录。
- 审核账号：用于应用商店审核，密码单独通过安全渠道提供，不写入 Git。
- 管理员账号：只用于后台验证，不提供给应用商店审核员，除非审核明确要求。

## 通用流程

- 首次启动：看到隐私政策和用户协议入口，未同意前不提前申请敏感权限。
- 注册登录：手机号/邮箱/账号登录路径可完成，错误提示明确。
- 首页问事：输入一个真实问题，能进入时安 agent 综合解读，流式输出不卡死。
- 工具页：八字、奇门、紫微、塔罗、择吉至少各跑一次基础流程。
- 积分中心：能查看余额；测试环境不得触发真实短信、邮件或支付到账。
- 历史记录：能保存、进入、返回，不丢登录态。
- 账号注销：入口可见，流程说明清楚。
- 退出重进：关闭 App 或桌面端后重新打开，登录态表现符合预期。

## 截图要求

- 首页首屏：必须看到 `时安agent`；未登录时辅助按钮应为 `登录/注册`，登录后辅助按钮应为 `进入应用`，不能只剩登录按钮。
- 登录弹窗：必须看到 `密码登录`、`验证码登录`、`Gitee 验证登录`。
- Agent 工作台：必须看到输入框、选择命盘、选择术数、积分或历史入口。
- 积分会员页：必须看到短期问题、长期问题、复杂问题的预计消耗和会员方案。
- 工具页：八字、奇门、紫微、塔罗、择吉各至少一张结果或可操作状态截图。
- 账号注销：必须保留入口截图、确认页截图和注销后登录态变化截图。
- 商店素材：当前批次每个平台至少准备 5 张能展示“问事 -> 选术数 -> 解读 -> 报告/历史”的截图。

## 平台专项

- Android：覆盖应用宝/华为/小米/OPPO/vivo 至少各一台或同系统近似设备；检查返回键、软键盘、权限弹窗。
- iOS：本轮 deferred；后续恢复时覆盖 iPhone 和 iPad，检查安全区、键盘遮挡、充值入口策略。
- 鸿蒙：本轮 deferred；后续恢复时覆盖手机和平板，检查华为审核要求的隐私权限触发时机。
- macOS：检查 DMG 安装、首次打开、安全提示、窗口缩放。
- Windows：检查安装、卸载、开始菜单入口、窗口缩放。

## 记录模板

```markdown
## YYYY-MM-DD vX.Y.Z 平台/渠道

- 测试人：
- 设备：
- 系统版本：
- 安装包：
- Git commit：
- 测试账号类型：
- 通过流程：
- 失败流程：
- 截图位置：
- 截图是否覆盖：首页 / 登录 / Agent / 积分会员 / 工具页 / 注销
- 是否触发真实短信邮件支付：否 / 是，原因：
- 结论：通过 / 阻塞 / 需整改
```
