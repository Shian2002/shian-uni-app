# Codex Handoff — 2026-06-02 营销首页上线

## 当前结论

- 线上营销首页已确认可用，用户已明确回复“没错了”。
- 线上地址：`http://119.29.128.18/#/?v=left-up-216-fbe9b8b`
- 最新确认提交：`fbe9b8b fix: lift marketing left title further`
- GitHub 已推送，服务器已部署。

## 本次主要改动

文件：`src/pages/index/index.vue`

- 首页默认展示营销页。
- “进入应用 / 开始解读”进入工具应用页。
- 营销页包含顶部品牌、导航、主视觉英文标题、中文标题、右侧说明、CTA、第二屏内容。
- 左侧标题块位置最终值：
  - `.marketing-copy { transform: translateY(-130px); }`
  - `.marketing-main { transform: translateY(-216px); }`
- 右侧说明和按钮位置保持不动。
- 背景轻粒子数量最终为 `50` 个：
  - `.marketing-particle` 总数：`50`
  - `.marketing-particle-soft` 总数：`45`
- 重特效已被回退并保持关闭：
  - 不要恢复 `.marketing-star-map`
  - 不要恢复 `.marketing-lunar-halo`
  - 不要恢复 `.marketing-light-beam`

## 线上验证结果

验证地址：

```text
http://119.29.128.18/#/?v=left-up-216-fbe9b8b
```

桌面视口 `1228x768` 验证数据：

```json
{
  "main": {
    "top": -31.15625,
    "bottom": 380,
    "center": 174.421875
  },
  "side": {
    "top": 382.4375,
    "bottom": 596,
    "center": 489.21875
  },
  "cta": {
    "top": 540,
    "bottom": 596,
    "center": 568
  },
  "particleCount": 50,
  "softCount": 45
}
```

## 部署命令

```bash
cd /Users/junj/WorkBuddy/2026-05-12-task-96/uniapp多平台Hbuilder/xuan-cet-tai
npm run build:h5
bash deploy-to-server.sh
```

构建时现有提示属于已知提示：

- uni-app 有新版本提示
- `sidebar-types.js`、`sidebar.js` 非 module 提示
- `logo.webp?v=2` 运行时解析提示
- `patch-html-css-order.js` 会追加 CSS 顺序修复日志

## 浏览器验证

按项目规则，网页验证优先使用 gstack browse：

```bash
B=/Users/junj/.agents/skills/gstack/browse/dist/browse
$B goto 'http://119.29.128.18/#/?v=left-up-216-fbe9b8b'
```

可用 Playwright 复测 DOM：

```bash
node - <<'NODE'
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1228, height: 768 }, deviceScaleFactor: 1 });
  await page.goto('http://119.29.128.18/#/?v=left-up-216-fbe9b8b', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1200);
  const data = await page.evaluate(() => {
    const rect = sel => {
      const r = document.querySelector(sel).getBoundingClientRect();
      return { top: r.top, bottom: r.bottom, center: r.top + r.height / 2 };
    };
    return {
      main: rect('.marketing-main'),
      side: rect('.marketing-side'),
      cta: rect('.marketing-cta-row'),
      particleCount: document.querySelectorAll('.marketing-particle').length,
      softCount: document.querySelectorAll('.marketing-particle-soft').length
    };
  });
  console.log(JSON.stringify(data, null, 2));
  await browser.close();
})();
NODE
```

## 注意事项

- 用户对左侧标题高度非常敏感，最终认可的是 `fbe9b8b` 这版，不要随意改 `.marketing-main` 的 `translateY(-216px)`。
- 用户希望粒子明显可见，所以粒子保持 `50` 个；但只要轻粒子，不要恢复大面积光束、光晕或星图。
- 手机端营销页之前有滑动问题，移动端媒体查询里 `.marketing-main { transform: none; }` 保持不变，避免影响手机滑动和首屏流式排版。
- 工作区仍有未跟踪目录 `backups/`、`docs/design/`，不是本次改动，未处理。
