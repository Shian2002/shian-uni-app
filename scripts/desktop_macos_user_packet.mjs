#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { chmodSync, copyFileSync, existsSync, mkdirSync, readdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { basename, isAbsolute, join, relative } from 'node:path'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.DESKTOP_MACOS_USER_PACKET_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.DESKTOP_MACOS_USER_PACKET_DIR || join(root, 'artifacts', 'desktop-macos-user-packets', `${localTimestamp()}-${version}`)
const indexDir = join(root, 'artifacts', 'desktop-macos-user-packets')
const dmgSource = process.env.DESKTOP_MACOS_USER_PACKET_DMG || 'desktop/release/时安解忧屋-1.0.0-arm64.dmg'
const dmgFileName = `shian-${version}-macos-arm64-user-test.dmg`

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function readJson(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  try {
    return JSON.parse(readFileSync(fullPath, 'utf8'))
  } catch (_) {
    return null
  }
}

function git(args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim()
  } catch (_) {
    return ''
  }
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function latestDir(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byReportTime = reportTime(join(path, b.name, 'report.json')) - reportTime(join(path, a.name, 'report.json'))
      return byReportTime || b.name.localeCompare(a.name)
    })
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function latestPassingDesktopSmoke() {
  const fullPath = join(root, 'artifacts', 'desktop-smoke')
  if (!existsSync(fullPath)) return { path: '', report: null }
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byReportTime = reportTime(join('artifacts/desktop-smoke', b.name, 'report.json')) - reportTime(join('artifacts/desktop-smoke', a.name, 'report.json'))
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const dir of dirs) {
    const reportPath = join('artifacts/desktop-smoke', dir.name, 'report.json')
    const report = readJson(reportPath)
    if (report?.passed === true && report?.layout?.agent?.homeAiMain && report?.layout?.agent?.topnav) {
      return { path: reportPath, report }
    }
  }
  return { path: '', report: null }
}

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function fileMtime(path) {
  const fullPath = isAbsolute(path) ? path : join(root, path)
  if (!existsSync(fullPath)) return null
  const stat = statSync(fullPath)
  return { path, mtimeMs: stat.mtimeMs, mtime: new Date(stat.mtimeMs).toISOString() }
}

function copyIfExists(source, targetName) {
  if (!source) return null
  const sourcePath = isAbsolute(source) ? source : join(root, source)
  if (!existsSync(sourcePath)) return null
  if (!statSync(sourcePath).isFile()) return null
  const targetPath = join(outDir, targetName)
  copyFileSync(sourcePath, targetPath)
  const stat = statSync(targetPath)
  const sourceStat = statSync(sourcePath)
  return {
    source,
    path: rel(targetPath),
    fileName: basename(targetPath),
    bytes: stat.size,
    sha256: sha256(targetPath),
    sourceMtime: new Date(sourceStat.mtimeMs).toISOString(),
  }
}

function refreshMacAppZip() {
  const appDir = join(root, 'desktop/release/mac-arm64/时安解忧屋.app')
  const zipPath = join(root, 'desktop/release/时安解忧屋-1.0.0-arm64.app.zip')
  if (!existsSync(appDir)) return
  rmSync(zipPath, { force: true })
  execFileSync('ditto', ['-c', '-k', '--sequesterRsrc', '--keepParent', appDir, zipPath], {
    cwd: root,
    stdio: 'ignore',
  })
}

function screenshotRows(screenshots) {
  return screenshots.length
    ? screenshots.map((item) => `| ${item.label} | \`${item.path}\` |`).join('\n')
    : '| 暂缺 | - |'
}

function htmlEscape(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function writePreviewHtml(manifest) {
  const cards = manifest.screenshots.map((item) => `
        <section class="shot">
          <h2>${htmlEscape(item.label)}</h2>
          <img src="${htmlEscape(item.fileName)}" alt="${htmlEscape(item.label)}" />
        </section>`).join('\n')
  const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>时安解忧屋 macOS 试用预览</title>
  <style>
    :root {
      color-scheme: light;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f6f4ef;
      color: #1d1b16;
    }
    body {
      margin: 0;
      padding: 28px;
    }
    main {
      max-width: 1120px;
      margin: 0 auto;
    }
    header {
      margin-bottom: 24px;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.2;
      letter-spacing: 0;
    }
    p {
      margin: 6px 0;
      line-height: 1.7;
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      margin: 18px 0 26px;
    }
    .meta div, .shot {
      border: 1px solid #ded8ca;
      border-radius: 8px;
      background: #fffdfa;
    }
    .meta div {
      padding: 12px 14px;
      overflow-wrap: anywhere;
    }
    .grid {
      display: grid;
      grid-template-columns: 1fr;
      gap: 18px;
    }
    .shot {
      padding: 14px;
    }
    .shot h2 {
      margin: 0 0 12px;
      font-size: 18px;
      letter-spacing: 0;
    }
    img {
      display: block;
      width: 100%;
      height: auto;
      border-radius: 6px;
      border: 1px solid #e8e1d2;
      background: #f2efe7;
    }
    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      font-size: 0.95em;
    }
  </style>
</head>
<body>
  <main>
    <header>
      <h1>时安解忧屋 macOS 试用预览</h1>
      <p>这个页面展示当前 macOS 包里的关键页面截图。安装包、校验文件和打开说明都在同一个目录。</p>
      <div class="meta">
        <div><strong>DMG</strong><br /><code>${htmlEscape(manifest.artifacts.find((item) => item.fileName.endsWith('.dmg'))?.fileName || '缺失')}</code></div>
        <div><strong>状态</strong><br />未签名、未公证测试包</div>
        <div><strong>图标源</strong><br /><code>${htmlEscape(manifest.iconSource)}</code></div>
        <div><strong>登录</strong><br />复用线上 H5/后端现有登录逻辑</div>
      </div>
    </header>
    <div class="grid">
${cards}
    </div>
  </main>
</body>
</html>
`
  writeFileSync(join(outDir, 'preview.html'), html)
}

function writeOpenCommand(dmg) {
  if (!dmg) return ''
  const command = `#!/bin/zsh
set -e
cd "$(dirname "$0")"
open "${dmg.fileName}"
`
  const commandPath = join(outDir, 'open-macos-dmg.command')
  writeFileSync(commandPath, command)
  chmodSync(commandPath, 0o755)
  return rel(commandPath)
}

function writeLatestIndex(manifest, dmg) {
  const latestManifest = {
    generatedAt: new Date().toISOString(),
    latestPacketDir: manifest.outDir,
    previewPage: `${manifest.outDir}/preview.html`,
    openCommand: `${manifest.outDir}/open-macos-dmg.command`,
    dmg: dmg ? dmg.path : '',
    passed: manifest.passed,
    version: manifest.version,
    commit: manifest.commit,
  }
  writeFileSync(join(indexDir, 'latest-manifest.json'), `${JSON.stringify(latestManifest, null, 2)}\n`)

  const latestReadme = [
    '# 最新 macOS 个人试用包',
    '',
    `> 更新时间：${latestManifest.generatedAt}`,
    `> 版本：${manifest.version}`,
    `> commit：${manifest.commit || '未读取到'}`,
    `> 结果：${manifest.passed ? '通过' : '未通过'}`,
    '',
    '## 直接入口',
    '',
    `- 页面预览：\`${latestManifest.previewPage}\``,
    `- 打开 DMG：\`${latestManifest.openCommand}\``,
    `- DMG：\`${latestManifest.dmg || '缺失'}\``,
    `- 完整目录：\`${latestManifest.latestPacketDir}\``,
    '',
    '## 说明',
    '',
    '- 页面预览可以直接查看首页、登录弹窗和时安 agent 截图。',
    '- DMG 当前仍是未签名、未公证测试包，适合本人或内部测试。',
    '- 正式公开下载前仍需 Apple Developer ID 签名和 notarization。',
  ]
  writeFileSync(join(indexDir, 'LATEST.md'), `${latestReadme.join('\n')}\n`)

  const command = `#!/bin/zsh
set -e
open "${join(root, manifest.outDir, 'preview.html')}"
`
  const commandPath = join(indexDir, 'open-latest-preview.command')
  writeFileSync(commandPath, command)
  chmodSync(commandPath, 0o755)
  return latestManifest
}

mkdirSync(outDir, { recursive: true })
refreshMacAppZip()

const installVerify = latestDir('artifacts/desktop-macos-install')
const installVerifyReport = installVerify ? readJson(`${installVerify}/report.json`) : null
const latestSmoke = latestPassingDesktopSmoke()
const smokeReportPath = latestSmoke.path
const smokeReport = latestSmoke.report
const dmg = copyIfExists(dmgSource, dmgFileName)
const appZip = copyIfExists('desktop/release/时安解忧屋-1.0.0-arm64.app.zip', `shian-${version}-macos-arm64-user-test.app.zip`)
const latestH5Build = fileMtime('dist/build/h5/index.html')
const latestDesktopMain = fileMtime('desktop/main.js')
const freshnessFloor = [latestH5Build, latestDesktopMain]
  .filter(Boolean)
  .reduce((latest, item) => Math.max(latest, item.mtimeMs), 0)

const screenshots = [
  { label: '营销首页', source: smokeReport?.screenshots?.marketingHome || '', fileName: 'desktop-marketing-home.png' },
  { label: '登录弹窗', source: smokeReport?.screenshots?.loginModal || '', fileName: 'desktop-login-modal.png' },
  { label: '时安 agent', source: smokeReport?.screenshots?.agentApp || '', fileName: 'desktop-agent-app.png' },
]
  .map((item) => {
    const copied = copyIfExists(item.source, item.fileName)
    return copied ? { ...copied, label: item.label } : null
  })
  .filter(Boolean)

const issues = []
if (!dmg) issues.push(`缺少 macOS DMG: ${dmgSource}`)
if (installVerifyReport?.passed !== true) issues.push('缺少通过的 macOS DMG 只读挂载校验报告')
if (smokeReport?.passed !== true) issues.push('缺少通过的桌面 smoke 报告')
if (!smokeReport?.layout?.agent?.homeAiMain || !smokeReport?.layout?.agent?.topnav) issues.push('桌面 smoke 缺少浅色顶栏和底部对话框布局指标')
if (!screenshots.some((item) => item.fileName === 'desktop-agent-app.png')) issues.push('缺少时安 agent 应用态截图')
for (const artifact of [dmg, appZip].filter(Boolean)) {
  const sourceTime = artifact.sourceMtime ? Date.parse(artifact.sourceMtime) : 0
  if (freshnessFloor && sourceTime < freshnessFloor) {
    issues.push(`macOS 产物早于最新 H5 或桌面壳源码，请重新执行 npm run desktop:build:mac:arm64：artifact=${artifact.sourceMtime} h5=${latestH5Build?.mtime || 'missing'} desktopMain=${latestDesktopMain?.mtime || 'missing'}`)
  }
}

const manifest = {
  generatedAt: new Date().toISOString(),
  version,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  outDir: rel(outDir),
  appName: '时安解忧屋',
  platform: 'macOS arm64',
  status: 'personal-test-packet',
  passed: issues.length === 0,
  unsignedNotice: '当前 macOS 包未签名、未公证；适合本人或内部测试，正式公开分发前必须补 Apple Developer ID 签名和 notarization。',
  loginPolicy: '桌面端继续加载现有 H5 构建产物，登录复用线上 H5/后端现有登录逻辑。',
  iconSource: 'src/static/images/logo.png',
  artifacts: [dmg, appZip].filter(Boolean),
  screenshots,
  evidence: {
    installVerify: installVerify ? `${installVerify}/report.json` : '',
    smokeReport: smokeReport?.passed === true ? smokeReportPath : '',
    smokeLayout: smokeReport?.layout?.agent || null,
    latestH5Build,
    latestDesktopMain,
    desktopBuildEvidence: 'docs/release/desktop-build-evidence.md',
  },
  previewPage: 'preview.html',
  openCommand: dmg ? 'open-macos-dmg.command' : '',
  issues,
}

writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
writePreviewHtml(manifest)
writeOpenCommand(dmg)
const latestManifest = writeLatestIndex(manifest, dmg)

const checksumItems = [...manifest.artifacts, ...screenshots]
writeFileSync(join(outDir, 'checksums.sha256'), `${checksumItems.map((item) => `${item.sha256}  ${item.fileName}`).join('\n')}\n`)

const readme = [
  '# 时安解忧屋 macOS 个人试用包',
  '',
  `> 生成时间：${manifest.generatedAt}`,
  `> 版本：${version}`,
  `> commit：${manifest.commit || '未读取到'}`,
  `> 目录：\`${manifest.outDir}\``,
  '',
  '## 先打开哪个文件',
  '',
  '- 先看页面预览：`preview.html`。',
  '- 想直接打开 DMG：双击 `open-macos-dmg.command`，或手动双击 DMG。',
  dmg
    ? `- 优先打开：\`${dmg.fileName}\``
    : '- DMG 缺失，先执行 `npm run desktop:build:mac:arm64`。',
  appZip
    ? `- 备用压缩包：\`${appZip.fileName}\``
    : '- 备用 `.app.zip` 缺失。',
  '',
  '## macOS 打开方式',
  '',
  '1. 双击 DMG。',
  '2. 把“时安解忧屋.app”拖到 Applications。',
  '3. 因为当前是未签名测试包，如果 macOS 拦截，先右键应用选择“打开”，或到“系统设置 -> 隐私与安全性”允许打开。',
  '4. 打开后先看首页，再点“登录/注册”验证线上登录弹窗，再点“时安agent”看应用态。',
  '',
  '## 当前已验证',
  '',
  `- DMG 只读挂载校验：${installVerifyReport?.passed === true ? `\`${installVerify}/report.json\`` : '缺失或未通过'}`,
  `- 桌面 smoke：${smokeReport?.passed === true ? `\`${smokeReportPath}\`` : '缺失或未通过'}`,
  '- 图标来自 `src/static/images/logo.png`，不是 Electron 默认图标。',
  '- 登录继续复用线上 H5/后端现有登录逻辑。',
  `- 页面预览：\`${manifest.previewPage}\`。`,
  `- 打开脚本：\`${manifest.openCommand || '缺失'}\`。`,
  '',
  '## 截图',
  '',
  '| 场景 | 文件 |',
  '| --- | --- |',
  screenshotRows(screenshots),
  '',
  '## 文件校验',
  '',
  '- `checksums.sha256` 记录 DMG、ZIP 和截图 hash。',
  '- `manifest.json` 记录 commit、产物、截图和证据路径。',
  '',
  '## 仍未完成',
  '',
  '- Apple Developer ID 签名。',
  '- notarization。',
  '- 用户侧首次打开截图和安全提示截图。',
  '- 正式 GitHub Release 或官网发布。',
]

if (issues.length) {
  readme.push('', '## 问题', '', ...issues.map((item) => `- ${item}`))
}

writeFileSync(join(outDir, 'README.md'), `${readme.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: manifest.passed,
  dmg: dmg?.path || '',
  installVerify: manifest.evidence.installVerify,
  screenshots: screenshots.length,
  issues,
  latest: latestManifest.latestPacketDir,
}, null, 2))

if (!manifest.passed) process.exit(1)
