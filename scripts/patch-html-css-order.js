/**
 * Patch dist/build/h5/index.html — 修复 CSS 在 JS 之后加载导致的 FOUC
 *
 * 根因: uni-app build 生成的 index.html 中, app 级别的 <link rel="stylesheet">
 * 被放在 <script type="module"> 之后, 导致部分浏览器可能先渲染再加载 CSS。
 *
 * 修复:
 *   1. 收集 dist/build/h5/assets/index-*.css 中未被引用的文件并追加到 <head>
 *   2. 将所有 <link rel="stylesheet"> 移到 <head> 最前面（任何 <script> 之前）
 *   3. 不再强制隐藏 #app，避免慢网/缓存命中旧 chunk 时出现长时间黑屏
 */
const fs = require('fs')
const path = require('path')

const htmlPath = path.join(__dirname, '..', 'dist', 'build', 'h5', 'index.html')
const assetsDir = path.join(__dirname, '..', 'dist', 'build', 'h5', 'assets')
if (!fs.existsSync(htmlPath)) {
  console.log('[SKIP] dist/build/h5/index.html not found')
  process.exit(0)
}

let html = fs.readFileSync(htmlPath, 'utf8')

// ── 0. 查找 assets 目录中所有 index-*.css, 将未引用的追加到 <head> ──
if (fs.existsSync(assetsDir)) {
  const allCssFiles = fs.readdirSync(assetsDir).filter(f => /^index-[^.]+\.css$/.test(f))
  for (const cssFile of allCssFiles) {
    if (html.indexOf(cssFile) === -1) {
      const linkTag = '\n<link rel="stylesheet" href="/assets/' + cssFile + '">'
      html = html.replace('</head>', linkTag + '\n</head>')
      console.log('[ADD] missing CSS: ' + cssFile)
    }
  }
}

// ── 1. 收集 <head> 中所有 <link rel="stylesheet"> ──
const headMatch = html.match(/<head>([\s\S]*?)<\/head>/i)
if (!headMatch) {
  console.log('[ERROR] No <head> found')
  process.exit(1)
}

const headContent = headMatch[1]
const cssLinks = []
const restParts = []

// Split head content into CSS links and everything else
let remaining = headContent
let cssRe = /<link[^>]*rel=["']stylesheet["'][^>]*\/?>/gi
let lastIndex = 0
let match

while ((match = cssRe.exec(remaining)) !== null) {
  // Text before this CSS link
  if (match.index > lastIndex) {
    restParts.push(remaining.substring(lastIndex, match.index))
  }
  cssLinks.push(match[0])
  lastIndex = cssRe.lastIndex
}
if (lastIndex < remaining.length) {
  restParts.push(remaining.substring(lastIndex))
}

// ── 2. 重新构建 head: CSS links first, then rest ──
const newHeadContent = cssLinks.join('\n') + '\n' + restParts.join('')
html = html.replace(headContent, newHeadContent)

fs.writeFileSync(htmlPath, html, 'utf8')
console.log('[OK] index.html CSS order patched (moved ' + cssLinks.length + ' stylesheets before scripts)')
