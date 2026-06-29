# H5 正式站导航下拉对齐修复记录

日期：2026-06-29

## 后续前端验活原则

时安解忧屋所有前端相关问题，尤其是顶部导航、弹层、下拉框、固定输入栏、移动端布局、响应式断点和点击/悬停交互，都需要在 md 里记录验证证据。

默认验活覆盖三端：

- 电脑端：宽屏桌面视口，重点看 hover、click、导航跳转和弹层层级。
- 平板端：约 `768px` 宽度，重点看窄桌面/iPad 宽度下导航是否拥挤、溢出、错位。
- 手机端：约 `390px` 宽度，重点看 touch/click、点空白关闭、点击目标大小和首屏遮挡。

不能只按当前截图宽度判断通过；涉及上线必须补正式服证据。

## 背景

正式站 `https://shianjieyouwu.com/#/pages/points/index` 在 Safari 窗口宽度约 768px 时，点击顶部 `术数工具` 后，下拉菜单没有贴着按钮展开，而是偏到页面中间；右上角头像菜单也可能和导航菜单同时出现，导致顶部区域混乱。

## 原因

`src/components/TopNav.vue` 的移动端断点把普通导航下拉菜单统一设置为 `left: 50%` 和 `translateX(-50%)`，因此在 iPad/窄桌面 Safari 宽度下会按视口居中，而不是按触发按钮定位。

## 处理

- `术数工具` 等普通导航下拉菜单改为读取触发按钮的 `getBoundingClientRect()`，按按钮中心定位，并在视口内做左右边界约束。
- 头像菜单也改为按头像触发区域定位，并限制最大高度和横向溢出。
- 头像 hover 展开增加保护：当普通导航菜单已经打开时，不再自动打开头像菜单，避免两个下拉框同时显示。
- 追加修复 hover/click 不一致：click 路径显式把触发按钮传给定位函数，不再依赖菜单当前父节点推断 anchor。
- 移动端 CSS 不再把所有 `.nav-btn-drop-menu` 强制设为 `left: 50%`，避免点击状态回退到按视口居中。
- 再次修复 click 漂移：普通导航下拉菜单不再搬到 `body` 做 fixed 定位，只保留在触发按钮 DOM 内做 absolute 定位；头像和 `更多` 菜单仍可使用 fixed 定位。
- 取消普通导航下拉菜单的 transform 过渡，hover 和 click 均直接显示，不再从左侧滑入。
- 修复下拉过透明：浅色主题下普通导航菜单和头像菜单背景从半透明 `0.65` 提升到 `0.96`，边框和阴影改为更稳定的浅色浮层样式。
- 修复 click 后点空白不关闭：统一 `_xc_closeAllDropdowns()`，关闭时无条件调用 `_xc_restoreMenu()` 清理菜单 inline 可见样式，不再只处理被搬到 `body` 的菜单。
- 为 `术数工具` 增加明确的 hover 进入/离开兜底：hover 进入时应用定位和浮层样式，hover 离开时复原样式；click 打开后离开或点空白也会关闭。
- 增加 `pointerdown` / `mousedown` 捕获期外部点击关闭，保证页面内控件阻止冒泡时，下拉框仍能先被关闭。
- 修复 hover 下滑断层：普通导航菜单从 `top: calc(100% + 4px)` 改为 `top: 100%`，菜单顶边贴住 `术数工具` 按钮底边，避免鼠标从按钮滑向菜单时经过空白区域导致下拉框立刻消失。

## 验证

本地自动化：

```bash
npm run typecheck
npm run lint
npm run build:h5
```

结果：全部通过。

本地页面验活：

- 预览 `dist/build/h5` 后打开 `http://127.0.0.1:4190/#/pages/points/index`
- in-app Browser 设置 `768x881` 视口，点击 `术数工具`
- 量测结果：菜单中心和按钮中心差值 `0px`，菜单在按钮下方，菜单未超出视口，头像菜单未同时打开

线上自动化验活：

- 打开 `https://shianjieyouwu.com/?dropdownFix=1782713959#/pages/points/index`
- Playwright 设置 `768x881` 视口，点击可见的 `术数工具`
- 量测结果：菜单中心和按钮中心差值 `0px`，菜单在按钮下方，菜单未超出视口，只有 `术数工具` 菜单可见，头像菜单未打开
- 追加验活打开 `https://shianjieyouwu.com/?dropdownOnline=1782717673258#/pages/points/index`
- Playwright 分别执行 hover 和 click：hover 中心差值 `-0.01px`，click 中心差值 `-0.77px`，两种状态均贴着 `术数工具` 按钮展开
- 漂移复现录制：修复前 Chromium 第 1 帧 click 中心差值 `-70.26px`，WebKit 第 1 帧 click 中心差值 `-47.03px`，随后滑到正确位置，确认问题来自 transform 过渡和 body fixed 定位。
- 修复后本地录制：Chromium/WebKit hover 均可见，click 前 6 次采样中心差值均为 `-0.01px`，`transition: none 0s`，父节点保持 `nav-btn nav-btn-has-drop open`。
- 修复后线上录制：`https://shianjieyouwu.com/?dropdownProdAfter=1782718605700#/pages/points/index`，Chromium/WebKit hover 均可见，click 前 6 次采样中心差值均为 `-0.01px`，间距 `4px`，无控制台错误。
- 透明度和关闭行为本地录制：
  - Chromium：`/tmp/shian-dropdown-close-local-chromium-1782719253201/page@b617b3959a62ce6ff516efdc352fa59a.webm`
  - WebKit：`/tmp/shian-dropdown-close-local-webkit-1782719256011/page@26b715b9cb364b4b457385ad8f5e8b36.webm`
  - 结果：hover 打开背景 `rgba(255, 253, 248, 0.96)`；hover 离开后 `visibility:hidden / opacity:0 / pointer-events:none`；click 打开后点空白也恢复隐藏，并且 inline `display/visibility/opacity/pointer-events/position/top/left` 全部清空。
- 透明度和关闭行为线上录制：
  - Chromium：`https://shianjieyouwu.com/?dropdownCloseProd=1782719384675-chromium#/pages/points/index`，视频 `/tmp/shian-dropdown-close-prod-chromium-1782719384675/page@512d18ee72ef65d300a9befd2821b2ee.webm`
  - WebKit：`https://shianjieyouwu.com/?dropdownCloseProd=1782719388409-webkit#/pages/points/index`，视频 `/tmp/shian-dropdown-close-prod-webkit-1782719388409/page@b7db92c3b7da421515f0f8205b3bf7cc.webm`
  - 结果：两个内核均通过 hover 打开、hover 离开关闭、click 打开、点空白关闭；背景 alpha 为 `0.96`，中心差值 `-0.01px`，间距 `4px`，控制台无错误。
- hover 下滑断层本地三端录制：
  - 电脑端 Chromium：`/tmp/shian-dropdown-bridge-local-chromium-desktop-1782719782068/page@ddd0ecdcad49a6a313f0a5207b58bde7.webm`
  - 电脑端 WebKit：`/tmp/shian-dropdown-bridge-local-webkit-desktop-1782719785687/page@837687f9de87870d849ae6a1ac469be0.webm`
  - 平板端 Chromium：`/tmp/shian-dropdown-bridge-local-chromium-tablet-1782719789675/page@62e9964d09d387d5e06bdae95300f50a.webm`
  - 平板端 WebKit：`/tmp/shian-dropdown-bridge-local-webkit-tablet-1782719792844/page@bedbb70f891318af6c3776f6844dbe3f.webm`
  - 手机端 Chromium：`/tmp/shian-dropdown-bridge-local-chromium-mobile-1782719796253/page@7a44fbf02c162e73bb40d5c3c834724a.webm`
  - 手机端 WebKit：`/tmp/shian-dropdown-bridge-local-webkit-mobile-1782719817139/page@229c03722bf13c581121a80502872e71.webm`
  - 结果：电脑端和平板端从按钮中心滑到第一项 `奇门遁甲`，18 个采样点均保持可见，`gap=0`；手机端点击打开、点击第一项跳转、重新打开后点空白关闭均通过。
- hover 下滑断层正式服三端录制：
  - 电脑端 Chromium：`https://shianjieyouwu.com/?dropdownBridgeProd=1782720016112-chromium-desktop#/pages/points/index`，视频 `/tmp/shian-dropdown-bridge-prod-chromium-desktop-1782720016112/page@2884bc5eb40ebb6dbcc6826099139987.webm`
  - 电脑端 WebKit：`https://shianjieyouwu.com/?dropdownBridgeProd=1782720020117-webkit-desktop#/pages/points/index`，视频 `/tmp/shian-dropdown-bridge-prod-webkit-desktop-1782720020117/page@56a1506428e4b5e2a03f6bffd4db3970.webm`
  - 平板端 Chromium：`https://shianjieyouwu.com/?dropdownBridgeProd=1782720024363-chromium-tablet#/pages/points/index`，视频 `/tmp/shian-dropdown-bridge-prod-chromium-tablet-1782720024363/page@538f335e9a940e4d902efc7c96ea5317.webm`
  - 平板端 WebKit：`https://shianjieyouwu.com/?dropdownBridgeProd=1782720027791-webkit-tablet#/pages/points/index`，视频 `/tmp/shian-dropdown-bridge-prod-webkit-tablet-1782720027791/page@3aaf2b0b311019bd5b1d423ab0c147ef.webm`
  - 手机端 Chromium：`https://shianjieyouwu.com/?dropdownBridgeProd=1782720031761-chromium-mobile#/pages/points/index`，视频 `/tmp/shian-dropdown-bridge-prod-chromium-mobile-1782720031761/page@95efa221c9e4dadcc0ace557e6d37348.webm`
  - 手机端 WebKit：`https://shianjieyouwu.com/?dropdownBridgeProd=1782720052531-webkit-mobile#/pages/points/index`，视频 `/tmp/shian-dropdown-bridge-prod-webkit-mobile-1782720052531/page@c0c9e55d32668a049d5dfc3a33191044.webm`
  - 结果：电脑端和平板端从按钮中心滑到第一项 `奇门遁甲`，18 个采样点均保持可见，`gap=0`，第一项可点击进入 `#/pages/qimen/index`；手机端点击打开、点击第一项跳转、重新打开后点空白关闭均通过；6 组正式服验证控制台错误数均为 `0`。

Computer Use 本机 Safari 验活：

- Safari 打开 `https://shianjieyouwu.com/?dropdownFix=1782713959#/pages/points/index`
- 直接点击顶部 `术数工具`
- 实机截图确认：菜单贴着 `术数工具` 按钮下方展开，没有偏到页面中间，也没有和右上角头像菜单同时展开
- 追加 Safari 打开 `https://shianjieyouwu.com/?dropdownSafari=1782717698#/pages/points/index`
- 直接点击顶部 `术数工具`，实机截图确认 click 状态和 hover 预期一致，菜单未再按视口居中
- 追加 Safari 实机验活：正式站顶部点击 `术数工具`，下拉菜单直接在按钮下方展开，未出现从左侧漂移进入。
- 追加 Safari 实机验活：正式站打开 `https://shianjieyouwu.com/?dropdownCloseSafari=1782719518#/pages/points/index`，点击顶部 `术数工具` 后菜单出现，再点击页面左下空白区域，菜单立即关闭。
- 追加 Safari 实机验活：正式站打开 `https://shianjieyouwu.com/?dropdownBridgeSafari=1782720118#/pages/points/index`，点击顶部 `术数工具` 后菜单贴住按钮底边展开，点击第一项 `奇门遁甲` 成功进入 `#/pages/qimen/index`。
- 追加 Safari 实机验活：正式站打开 `https://shianjieyouwu.com/?dropdownBridgeSafariClose=1782720160#/pages/points/index`，点击顶部 `术数工具` 后菜单出现，再点击页面左下空白区域，菜单立即关闭。

## 追加修复：更多与术数工具快速切换

触发问题：手机端先点击 `更多`，再快速点击 `术数工具`，两个菜单会有短暂重叠；并且 `更多` 的 hover 行为缺失。

处理：

- `更多` 补齐 hover 进入/离开逻辑，和 click 共用同一套定位与关闭流程。
- 点击一个下拉触发器前，捕获期先关闭其他已打开菜单；同一个触发器继续走 toggle。
- 关闭菜单时先强制 `display:none / visibility:hidden / opacity:0 / pointer-events:none`，再恢复菜单原父节点，避免两层菜单在同一帧残留。
- 移除纯 CSS hover 直接展示菜单，统一由 JS 在打开前先关闭其他菜单，避免 CSS hover 与 click 之间抢状态。

本地验证：

- `npm run typecheck`
- `npm run lint`
- `npm run build:h5`
- 本地 `http://127.0.0.1:4194/?clickMoreLocal2=1782722073207#/pages/points/index`
- Chromium / WebKit，`390x844`，点击 `更多` 后菜单保持打开，再快速点 `术数工具`；12 次 16ms 采样，`maxVisibleAfterSwitch=1`。
- 视频：
  - `/tmp/shian-dropdown-clickmore-local2-chromium-1782722073317/page@2b52091221d7db24bf88e1ba546dd5a7.webm`
  - `/tmp/shian-dropdown-clickmore-local2-webkit-1782722075897/page@b0d010fb4b5157092c5a320abbc52a39.webm`

正式服验证：

- `https://shianjieyouwu.com/?clickMoreProd=1782722172968#/pages/points/index`
- Chromium / WebKit，`390x844`，点击 `更多` 后菜单保持打开，再快速点 `术数工具`；12 次 16ms 采样，`maxVisibleAfterSwitch=1`，控制台错误 `0`。
- 视频：
  - `/tmp/shian-dropdown-clickmore-prod-chromium-1782722172968/page@78a237d936c279e4bb51217834011ee1.webm`
  - `/tmp/shian-dropdown-clickmore-prod-webkit-1782722172968/page@d5feb2b74b3bef48fa7d37320695499c.webm`

## 追加修复：挖孔屏与安全区适配

参考依据：

- MDN `env()` 文档说明 `safe-area-inset-top/right/bottom/left` 用于读取视口安全区，适合处理非矩形屏幕和系统 UI 遮挡：https://developer.mozilla.org/en-US/docs/Web/CSS/env
- WebKit iPhone X 适配文档说明需要 `viewport-fit=cover` 后再用安全区变量控制内容避让：https://webkit.org/blog/7929/designing-websites-for-iphone-x/
- Chrome edge-to-edge / display cutout 文档说明 Android Chrome / WebView 的安全区能力和 edge-to-edge 场景有关，不能假设所有宿主 WebView 都返回非零 inset：https://developer.chrome.com/docs/css-ui/edge-to-edge

主流机型与浏览器结论：

- iPhone 刘海屏 / 灵动岛机型：iPhone X 到 iPhone 16 系列，Safari 与 iOS 内置浏览器环境优先走 `viewport-fit=cover` + `env(safe-area-inset-*)`。
- Android 挖孔屏机型：Pixel、Samsung Galaxy S/Flip/Fold、小米/Redmi、OPPO/OnePlus、vivo/iQOO、华为/Honor 等，普通 Chrome/Samsung Browser 通常不需要额外顶部兜底；全屏或半全屏内置浏览器需要按宿主能力补偿。
- 国内 App 内置浏览器：微信、QQ、微博、支付宝、钉钉/飞书、抖音/今日头条、UC、夸克、小米/华为/OPPO/vivo/Samsung 厂商浏览器，可能出现状态栏覆盖网页但 `safe-area-inset-top` 仍为 `0` 的情况，本次给 Android 移动内置浏览器增加 `30px` 顶部兜底。

处理：

- `index.html` 的 viewport meta 增加 `viewport-fit=cover`。
- `src/App.vue` 增加全局 CSS 变量：
  - `--xc-safe-top`
  - `--xc-safe-left`
  - `--xc-safe-right`
  - `--xc-topnav-base-height`
  - `--xc-topnav-total-height`
- 移动端 Android 内置浏览器 / 厂商浏览器命中 UA 时，设置 `--xc-safe-top-fallback:30px`；普通 Android Chrome、iPhone Safari、iPad Safari 保持 `0px`。
- `TopNav` 高度和 padding 使用 `--xc-topnav-total-height` / `--xc-safe-*`，导航内容向下避让状态栏。
- `.page-root`、首页 `.page-wrap`、`.hero-home`、聊天高度全部改用同一个 `--xc-topnav-total-height`，避免导航变高后底部输入框被挤出屏幕。
- 下拉菜单 fixed 定位时读取 `--xc-safe-top`，确保头像菜单和 `更多` 菜单不会贴到顶部系统区域。

本地安全区验证：

- 本地 `http://127.0.0.1:4194/?safeAreaLocal=1782723038066#/?app=1`
- Android 内置浏览器模拟：`390x844`，UA 含 `Android + MicroMessenger + wv`，`safeTopFallback=30px`，导航高 `86px`，首个按钮 top `38.89px`，正文 hero top `86px`，横向溢出 `0`。
- Android Chrome 模拟：`412x915`，`safeTopFallback=0px`，导航高 `56px`，正文 hero top `56px`，横向溢出 `0`。
- iPhone 15 Safari WebKit 模拟：`393x852`，`safeTopFallback=0px`，导航高 `56px`，横向溢出 `0`。
- iPad mini WebKit 模拟：`768x1024`，`safeTopFallback=0px`，导航高 `56px`，横向溢出 `0`。
- 本地 `更多 -> 术数工具` 快速切换回归：Chromium / WebKit 均 `maxVisibleAfterSwitch=1`。

正式服安全区验证：

- 正式服 `https://shianjieyouwu.com/?safeAreaProd=1782723218421#/?app=1`
- Android 内置浏览器模拟：`390x844`，`safeTopFallback=30px`，导航高 `86px`，首个按钮 top `38.89px`，正文 hero top `86px`，横向溢出 `0`，控制台错误 `0`。
- Android Chrome 模拟：`412x915`，`safeTopFallback=0px`，导航高 `56px`，正文 hero top `56px`，横向溢出 `0`，控制台错误 `0`。
- iPhone 15 Safari WebKit 模拟：`393x852`，`safeTopFallback=0px`，导航高 `56px`，横向溢出 `0`，控制台错误 `0`。
- iPad mini WebKit 模拟：`768x1024`，`safeTopFallback=0px`，导航高 `56px`，横向溢出 `0`，控制台错误 `0`。
- 视频：
  - `/tmp/shian-safearea-prod-android-inapp-punchhole-1782723218421/page@3030405328182e7a228771164b2422f0.webm`
  - `/tmp/shian-safearea-prod-android-chrome-plain-1782723218421/page@db7b6257456df8efa1a1616f11082e40.webm`
  - `/tmp/shian-safearea-prod-iphone15-safari-webkit-1782723218421/page@4dada4801aac5c82ea4476ed95f101db.webm`
  - `/tmp/shian-safearea-prod-ipad-mini-webkit-1782723218421/page@a2748316a7e020bbdcf66634c21c0c33.webm`
- 正式服 `更多 -> 术数工具` 快速切换回归：
  - Chromium：`/tmp/shian-safearea-dropdown-prod-chromium-1782723218421/page@c1a8a34b69dcf10089d73c10681b885d.webm`
  - WebKit：`/tmp/shian-safearea-dropdown-prod-webkit-1782723218421/page@250a1a0da3c843a7669fbd421a17fb21.webm`
  - 结果：两组均 `maxVisibleAfterSwitch=1`，控制台错误 `0`。

Computer Use 本机 Safari 追加验活：

- Safari 打开 `https://shianjieyouwu.com/?safeAreaSafari=1782723218421#/pages/points/index`。
- 点击 `更多`：只出现 `档案列表 / 关于我们` 菜单，没有和术数菜单重叠。
- 在 `更多` 打开后直接点击 `术数工具`：`更多` 菜单关闭，只保留术数菜单。
- 点击页面空白区域：术数菜单立即关闭。

## 部署

使用临时 worktree 部署，避免带入当前主工作区中无关的本地改动。

```bash
DRY_RUN=1 bash deploy-h5-to-server.sh
CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh
BASE_URL=https://shianjieyouwu.com bash scripts/production_monitor.sh
```

部署脚本完成了构建、备份和 rsync 同步。脚本最终退出码为 1 的原因是后置 `store:legal-urls --strict` 仍有历史 warning：`法律 URL 未达到正式商店提交条件`；同步本身已完成，并已通过后续生产监控、线上 Playwright 和本机 Safari 验活。

追加挖孔屏适配部署：

- 临时 worktree：`/private/tmp/shian-h5-safearea.5Cp7W3`
- 同步资源：`assets/TopNav-CBbjr8GX.css`、`assets/TopNav.BnT8qZPz.js`、`assets/pages-index-index.Bq9EDY9k.js`、`index.html`
- `BASE_URL=https://shianjieyouwu.com bash scripts/production_monitor.sh`：通过
- `curl https://shianjieyouwu.com/?safeCheck=1782723140` 确认线上 HTML 已包含 `viewport-fit=cover`
- 部署命令中的 zsh 变量名 `status` 与 shell 只读变量冲突，导致原命令在 rsync 后中断；已单独补跑生产监控和线上浏览验活，结果通过。
