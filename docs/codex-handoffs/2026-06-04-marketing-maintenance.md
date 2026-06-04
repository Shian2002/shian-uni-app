# Codex 交接文档：营销页优化与本地维护

## 重新接手提示

继续这个项目时，先阅读本文，然后检查当前仓库状态和线上页面，不要假设旧聊天上下文仍可用。优先保护用户已经满意的手机端第一屏效果，只在明确范围内继续改营销页。

## 项目信息

- 仓库路径：`/Users/junj/WorkBuddy/2026-05-12-task-96/uniapp多平台Hbuilder/xuan-cet-tai`
- 当前分支：`master`
- 主要页面：`src/pages/index/index.vue`
- 线上地址：`http://119.29.128.18/#/`

## 当前目标

用户近期主要在调整首页营销页：

- 第一屏桌面端星轨、粒子、左侧主标题、右侧 Chart 区块的位置和响应式缩放。
- 手机端第一屏特效已经满意，后续改动不能回退。
- 后续营销页的“三大术数体系”、奇门/八字/紫微图案、FAQ 和页脚仍可能继续微调。

## 已完成

- 第一屏恢复了桌面端大范围星轨和额外轨道层。
- 第一屏桌面端左侧内容恢复到 `180px` 左距。
- 第一屏桌面端右侧 `Chart. Reason. Decide.` 恢复到右下偏移。
- 缩小窗口时改成只缩字号和列宽，不再把左侧主标题继续往上推。
- 手机端清掉桌面右侧偏移，避免 Chart 区块被带偏。
- 已构建并部署到 `119.29.128.18`。
- 验活版本参数：`http://119.29.128.18/#/?v=hero-orbit-restore`

## 已运行命令

```bash
PATH=/usr/local/bin:$PATH /usr/local/bin/node scripts/patch-vue-slot.js
PATH=/usr/local/bin:$PATH /usr/local/bin/node scripts/patch-tab-dom.js
PATH=/usr/local/bin:$PATH /usr/local/bin/node node_modules/.bin/uni build
PATH=/usr/local/bin:$PATH /usr/local/bin/node scripts/patch-html-css-order.js
```

部署使用 `dist/build/h5` 打包后通过 `scp` 上传，并在服务器 `/var/www/xuan-cet` 解包覆盖。

## 已验证

- 本地 Playwright 截图：
  - `/tmp/shian-hero-restore2-desktop.png`
  - `/tmp/shian-hero-restore2-narrow.png`
  - `/tmp/shian-hero-restore2-mobile.png`
- 线上 Playwright 截图：
  - `/tmp/shian-hero-live-restore.png`
- 线上 CSS 验证到：
  - 星轨：`width:76rem;height:48rem;opacity:.56`
  - 左侧 hero padding：`padding:0 clamp(96px,8.5vw,140px) 80px 180px`
  - 右侧偏移：`translate(70px,70px)`

## 已知警告

构建会出现以下已知提示，之前也存在：

- `static/js/sidebar-types.js` 和 `static/js/sidebar.js` 缺少 `type=module`，无法被打包器合并。
- `/static/images/logo.svg?v=7` 构建时不解析，运行时解析。
- `patch-html-css-order.js` 会输出多条 `[ADD] missing CSS`，这是脚本补 CSS 顺序的正常输出。

## 当前工作区注意

工作区有大量既有未提交改动，不要随意回退。当前这次维护明确改过：

- `src/pages/index/index.vue`
- 新增本文档：`docs/codex-handoffs/2026-06-04-marketing-maintenance.md`

## Codex 本地维护报告

只读报告显示：

- 活跃线程：26 条。
- 线程标题总字符：106783。
- 线程首条预览总字符：108552。
- 最大标题和最大预览各约 64914 字符。
- 线程标题超限：2 条。
- 线程预览超限：7 条，其中 2 条超过 10000 字符。
- 修复候选：7 条。
- 日志大小：约 691MB。
- 活跃会话大小：约 0.427GB。
- 归档会话大小：约 0.603GB。
- 旧 session、失效 config、陈旧 worktree、Windows 扩展路径候选均为 0。

建议维护方式：

```bash
python3 /Users/junj/.codex/skills/keep-codex-fast/scripts/keep_codex_fast.py \
  --apply \
  --repair-thread-metadata-bloat \
  --archive-older-than-days 10 \
  --worktree-older-than-days 7 \
  --rotate-logs-above-mb 512
```

注意：Codex Desktop 正在运行时不要直接执行写入维护。应在退出 Codex 后执行，或使用 `--wait-for-codex-exit` 等待退出后自动处理。

## 下一步

1. 如果继续营销页，先打开线上第一屏确认用户当前反馈。
2. 若用户说 Codex 卡顿，优先处理线程标题/预览元数据膨胀和日志轮转。
3. 维护后重新运行只读报告确认标题/预览字符数下降、日志是否轮转。
4. 继续改营销页前，先截图桌面和手机端，避免回退已满意效果。
