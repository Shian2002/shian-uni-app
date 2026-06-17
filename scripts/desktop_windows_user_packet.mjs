#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { basename, isAbsolute, join, relative } from 'node:path'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.DESKTOP_WINDOWS_USER_PACKET_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.DESKTOP_WINDOWS_USER_PACKET_DIR || join(root, 'artifacts', 'desktop-windows-user-packets', `${localTimestamp()}-${version}`)
const indexDir = join(root, 'artifacts', 'desktop-windows-user-packets')
const installerSource = process.env.DESKTOP_WINDOWS_INSTALLER || 'desktop/release/时安解忧屋 Setup 1.0.0.exe'
const installerFileName = `shian-${version}-windows-x64-user-test-nsis.exe`

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

function copyIfExists(source, targetName) {
  if (!source) return null
  const sourcePath = isAbsolute(source) ? source : join(root, source)
  if (!existsSync(sourcePath)) return null
  if (!statSync(sourcePath).isFile()) return null
  const targetPath = join(outDir, targetName)
  copyFileSync(sourcePath, targetPath)
  const sourceStat = statSync(sourcePath)
  const stat = statSync(targetPath)
  return {
    source,
    path: rel(targetPath),
    fileName: basename(targetPath),
    bytes: stat.size,
    sha256: sha256(targetPath),
    sourceMtimeMs: sourceStat.mtimeMs,
    sourceMtime: new Date(sourceStat.mtimeMs).toISOString(),
  }
}

function fileMtime(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const stat = statSync(fullPath)
  return { path, mtimeMs: stat.mtimeMs, mtime: new Date(stat.mtimeMs).toISOString() }
}

function latestDir(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => b.name.localeCompare(a.name))
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function latestPassingDesktopSmoke() {
  const basePath = 'artifacts/desktop-smoke'
  const fullPath = join(root, basePath)
  if (!existsSync(fullPath)) return { path: '', report: null }
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byReportTime = reportTime(join(basePath, b.name, 'report.json')) - reportTime(join(basePath, a.name, 'report.json'))
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const dir of dirs) {
    const reportPath = join(basePath, dir.name, 'report.json')
    const report = readJson(reportPath)
    if (report?.passed === true && report?.layout?.agent?.homeAiMain && report?.layout?.agent?.topnav) {
      return { path: reportPath, report }
    }
  }
  return { path: '', report: null }
}

function htmlEscape(value) {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}

function screenshotRows(screenshots) {
  return screenshots.length
    ? screenshots.map((item) => `| ${item.label} | \`${item.path}\` |`).join('\n')
    : '| 暂缺 | - |'
}

function writePreviewHtml(manifest) {
  const cards = manifest.screenshots.map((item) => `
        <section class="shot">
          <h2>${htmlEscape(item.label)}</h2>
          <img src="${htmlEscape(item.fileName)}" alt="${htmlEscape(item.label)}" />
        </section>`).join('\n')
  const installer = manifest.artifacts.find((item) => item.fileName.endsWith('.exe'))?.fileName || '缺失'
  const html = `<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>时安解忧屋 Windows 试用预览</title>
  <style>
    :root {
      color-scheme: light;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: #f5f6f2;
      color: #1b1d18;
    }
    body {
      margin: 0;
      padding: 28px;
    }
    main {
      max-width: 1120px;
      margin: 0 auto;
    }
    h1 {
      margin: 0 0 8px;
      font-size: 30px;
      line-height: 1.2;
      letter-spacing: 0;
    }
    p {
      line-height: 1.7;
    }
    .meta {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
      margin: 18px 0 26px;
    }
    .meta div, .shot {
      border: 1px solid #d9ddce;
      border-radius: 8px;
      background: #fffef9;
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
      border: 1px solid #e3e6d8;
      background: #f0f2e9;
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
      <h1>时安解忧屋 Windows 试用预览</h1>
      <p>这个页面展示 Windows 安装器对应的桌面端关键页面截图。当前截图来自 macOS 桌面 smoke，只用于页面视觉预览；Windows 安装和卸载仍需真机回收。</p>
      <div class="meta">
        <div><strong>安装器</strong><br /><code>${htmlEscape(installer)}</code></div>
        <div><strong>状态</strong><br />未签名 NSIS 测试安装器</div>
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

function writeLatestIndex(manifest, installer) {
  const latestManifest = {
    generatedAt: new Date().toISOString(),
    latestPacketDir: manifest.outDir,
    previewPage: `${manifest.outDir}/preview.html`,
    installer: installer ? installer.path : '',
    passed: manifest.passed,
    version: manifest.version,
    commit: manifest.commit,
  }
  mkdirSync(indexDir, { recursive: true })
  writeFileSync(join(indexDir, 'latest-manifest.json'), `${JSON.stringify(latestManifest, null, 2)}\n`)
  writeFileSync(join(indexDir, 'LATEST.md'), `${[
    '# 最新 Windows 个人试用包',
    '',
    `> 更新时间：${latestManifest.generatedAt}`,
    `> 版本：${manifest.version}`,
    `> commit：${manifest.commit || '未读取到'}`,
    `> 结果：${manifest.passed ? '通过' : '未通过'}`,
    '',
    '## 直接入口',
    '',
    `- 页面预览：\`${latestManifest.previewPage}\``,
    `- Windows 安装器：\`${latestManifest.installer || '缺失'}\``,
    `- 完整目录：\`${latestManifest.latestPacketDir}\``,
    '',
    '## 说明',
    '',
    '- 当前安装器是未签名 NSIS 测试包。',
    '- 这个包可以发到 Windows 10/11 真机做安装、开始菜单、打开、登录、窗口缩放和卸载回收。',
    '- 正式公开下载前仍需 Windows 代码签名。',
  ].join('\n')}\n`)
  return latestManifest
}

mkdirSync(outDir, { recursive: true })

const installer = copyIfExists(installerSource, installerFileName)
const latestSmoke = latestPassingDesktopSmoke()
const smokeReportPath = latestSmoke.path
const smokeReport = latestSmoke.report
const desktopReleaseStatus = latestDir('artifacts/desktop-release-status')
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
if (!installer) issues.push(`缺少 Windows 安装器: ${installerSource}`)
if (installer && freshnessFloor && installer.sourceMtimeMs < freshnessFloor) {
  issues.push(`Windows 安装器早于最新 H5 或桌面壳源码，请重新执行 npm run desktop:build:win:x64：installer=${installer.sourceMtime} h5=${latestH5Build?.mtime || 'missing'} desktopMain=${latestDesktopMain?.mtime || 'missing'}`)
}
if (smokeReport?.passed !== true) issues.push('缺少通过的桌面 smoke 报告')
if (!smokeReport?.layout?.agent?.homeAiMain || !smokeReport?.layout?.agent?.topnav) issues.push('桌面 smoke 缺少浅色顶栏和底部对话框布局指标')
if (!screenshots.some((item) => item.fileName === 'desktop-agent-app.png')) issues.push('缺少时安 agent 应用态截图')

const manifest = {
  generatedAt: new Date().toISOString(),
  version,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  outDir: rel(outDir),
  appName: '时安解忧屋',
  platform: 'Windows x64',
  status: 'personal-test-packet',
  passed: issues.length === 0,
  unsignedNotice: '当前 Windows 包未签名；适合内部测试，正式公开分发前必须补 Windows 代码签名。',
  loginPolicy: '桌面端继续加载现有 H5 构建产物，登录复用线上 H5/后端现有登录逻辑。',
  iconSource: 'src/static/images/logo.png',
  artifacts: [installer].filter(Boolean),
  screenshots,
  evidence: {
    smokeReport: smokeReport?.passed === true ? smokeReportPath : '',
    smokeLayout: smokeReport?.layout?.agent || null,
    desktopReleaseStatus: desktopReleaseStatus ? `${desktopReleaseStatus}/report.json` : '',
    desktopBuildEvidence: 'docs/release/desktop-build-evidence.md',
    latestH5Build,
    latestDesktopMain,
  },
  previewPage: 'preview.html',
  requiredWindowsEvidence: [
    'Windows 10/11 安装器启动截图',
    '安装完成截图',
    '开始菜单入口截图',
    '首次打开截图',
    '登录弹窗截图',
    '时安 agent 应用态截图',
    '窗口缩放截图',
    '卸载流程截图',
  ],
  issues,
}

writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
writePreviewHtml(manifest)
const latestManifest = writeLatestIndex(manifest, installer)

const checksumItems = [...manifest.artifacts, ...screenshots]
writeFileSync(join(outDir, 'checksums.sha256'), `${checksumItems.map((item) => `${item.sha256}  ${item.fileName}`).join('\n')}\n`)

const readme = [
  '# 时安解忧屋 Windows 个人试用包',
  '',
  `> 生成时间：${manifest.generatedAt}`,
  `> 版本：${version}`,
  `> commit：${manifest.commit || '未读取到'}`,
  `> 目录：\`${manifest.outDir}\``,
  '',
  '## 先打开哪个文件',
  '',
  '- 先看页面预览：`preview.html`。',
  installer ? `- Windows 真机上运行：\`${installer.fileName}\`` : '- Windows 安装器缺失，先执行 `npm run desktop:build:win:x64`。',
  '- release inbox 备份由 `npm run desktop:release-inbox-sync` 统一生成，避免旧安装器混入用户包。',
  '',
  '## Windows 真机测试步骤',
  '',
  '1. 把本目录复制到 Windows 10/11 机器。',
  '2. 双击 NSIS 安装器。',
  '3. 完成安装后检查开始菜单入口。',
  '4. 打开应用，验证首页、登录/注册弹窗、时安 agent 应用态。',
  '5. 调整窗口大小，确认界面不溢出。',
  '6. 执行卸载，记录卸载截图。',
  '',
  '## 当前已验证',
  '',
  `- 桌面 smoke：${smokeReport?.passed === true ? `\`${smokeReportPath}\`` : '缺失或未通过'}`,
  `- 桌面发布状态：${desktopReleaseStatus ? `\`${desktopReleaseStatus}/report.json\`` : '缺失'}`,
  '- 图标来自 `src/static/images/logo.png`，不是 Electron 默认图标。',
  '- 登录继续复用线上 H5/后端现有登录逻辑。',
  '- 页面预览：`preview.html`。',
  '',
  '## 截图',
  '',
  '| 场景 | 文件 |',
  '| --- | --- |',
  screenshotRows(screenshots),
  '',
  '## 仍需 Windows 真机回收',
  '',
  ...manifest.requiredWindowsEvidence.map((item) => `- ${item}`),
  '',
  '## 文件校验',
  '',
  '- `checksums.sha256` 记录安装器和截图 hash。',
  '- `manifest.json` 记录 commit、产物、截图和证据路径。',
  '',
  '## 仍未完成',
  '',
  '- Windows 代码签名。',
  '- Windows 10/11 真机安装、开始菜单、窗口缩放和卸载截图。',
  '- 正式 GitHub Release 或官网发布。',
]

if (issues.length) {
  readme.push('', '## 问题', '', ...issues.map((item) => `- ${item}`))
}

writeFileSync(join(outDir, 'README.md'), `${readme.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: manifest.passed,
  installer: installer?.path || '',
  screenshots: screenshots.length,
  issues,
  latest: latestManifest.latestPacketDir,
}, null, 2))

if (!manifest.passed) process.exit(1)
