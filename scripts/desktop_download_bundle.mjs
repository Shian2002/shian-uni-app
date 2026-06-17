#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { basename, join, relative } from 'node:path'

const root = process.cwd()
const packageJson = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'))
const version = process.env.DESKTOP_DOWNLOAD_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.DESKTOP_DOWNLOAD_BUNDLE_DIR || join(root, 'artifacts', 'desktop-downloads', `${localTimestamp()}-${version}`)

const artifacts = [
  {
    id: 'macos-dmg',
    platform: 'macOS arm64',
    source: 'desktop/release/时安解忧屋-1.0.0-arm64.dmg',
    fileName: `shian-${version}-macos-arm64.dmg`,
    status: 'unsigned-not-notarized',
  },
  {
    id: 'macos-app-zip',
    platform: 'macOS arm64',
    source: 'desktop/release/时安解忧屋-1.0.0-arm64.app.zip',
    fileName: `shian-${version}-macos-arm64.app.zip`,
    status: 'unsigned-not-notarized',
  },
  {
    id: 'windows-nsis',
    platform: 'Windows x64',
    source: 'desktop/release/时安解忧屋 Setup 1.0.0.exe',
    fileName: `shian-${version}-windows-x64-nsis.exe`,
    status: 'unsigned',
  },
]

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

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function fileMtime(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const stat = statSync(fullPath)
  return { path, mtimeMs: stat.mtimeMs, mtime: new Date(stat.mtimeMs).toISOString() }
}

function assertSafeFileName(name) {
  if (!/^[a-z0-9._-]+$/i.test(name)) {
    throw new Error(`下载文件名必须保持 URL 友好: ${name}`)
  }
}

mkdirSync(outDir, { recursive: true })
refreshMacAppZip()

const copied = []
const missing = []
const issues = []
const latestH5Build = fileMtime('dist/build/h5/index.html')
const latestDesktopMain = fileMtime('desktop/main.js')
const freshnessFloor = [latestH5Build, latestDesktopMain]
  .filter(Boolean)
  .reduce((latest, item) => Math.max(latest, item.mtimeMs), 0)

for (const artifact of artifacts) {
  const sourcePath = join(root, artifact.source)
  assertSafeFileName(artifact.fileName)
  if (!existsSync(sourcePath)) {
    missing.push(artifact.source)
    continue
  }
  const targetPath = join(outDir, artifact.fileName)
  copyFileSync(sourcePath, targetPath)
  const sourceStat = statSync(sourcePath)
  const stat = statSync(targetPath)
  if (freshnessFloor && sourceStat.mtimeMs < freshnessFloor) {
    const command = artifact.id === 'windows-nsis' ? 'npm run desktop:build:win:x64' : 'npm run desktop:build:mac:arm64'
    issues.push(`${artifact.platform} ${artifact.fileName} 早于最新 H5 或桌面壳源码，请重新执行 ${command}：artifact=${new Date(sourceStat.mtimeMs).toISOString()} h5=${latestH5Build?.mtime || 'missing'} desktopMain=${latestDesktopMain?.mtime || 'missing'}`)
  }
  copied.push({
    ...artifact,
    path: rel(targetPath),
    fileName: basename(targetPath),
    bytes: stat.size,
    sha256: sha256(targetPath),
    sourceMtime: new Date(sourceStat.mtimeMs).toISOString(),
  })
}

const checksumLines = copied.map((item) => `${item.sha256}  ${item.fileName}`)
writeFileSync(join(outDir, 'checksums.sha256'), `${checksumLines.join('\n')}${checksumLines.length ? '\n' : ''}`)

const manifest = {
  generatedAt: new Date().toISOString(),
  version,
  outDir: rel(outDir),
  appName: '时安解忧屋',
  iconSource: 'src/static/images/logo.png',
  loginPolicy: '桌面端只加载现有 H5 构建产物，登录仍复用线上 H5/后端现有登录逻辑。',
  distribution: '第一版用于官网或 GitHub Releases 内测下载；正式公开前需要签名、公证和真机验收证据。',
  artifacts: copied,
  missing,
  issues,
  evidence: {
    latestH5Build,
    latestDesktopMain,
  },
  passed: missing.length === 0 && issues.length === 0,
}

writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)

const lines = [
  '# 时安解忧屋桌面下载包',
  '',
  `> 生成时间：${manifest.generatedAt}`,
  `> 版本：${version}`,
  `> 目录：\`${manifest.outDir}\``,
  '',
  '## 下载文件',
  '',
  '| 平台 | 文件 | 大小 | SHA-256 | 状态 |',
  '| --- | --- | ---: | --- | --- |',
  ...copied.map((item) => `| ${item.platform} | \`${item.fileName}\` | ${item.bytes} | \`${item.sha256}\` | ${item.status} |`),
  '',
  '## 使用说明',
  '',
  '- macOS 当前是未签名、未公证测试包；本机可打开，正式分发前需要 Apple Developer ID 签名和 notarization。',
  '- Windows 当前是未签名 NSIS 测试安装器；正式分发前需要 Windows 代码签名，并在 Windows 10/11 真机安装和卸载验证。',
  '- 桌面端图标来自 `src/static/images/logo.png`，不是 Electron 默认图标。',
  '- 桌面端不复制登录业务，继续复用线上登录逻辑。',
  '- `checksums.sha256` 用于上传 GitHub Releases 或官网前核对文件完整性。',
]

if (missing.length) {
  lines.push('', '## 缺失文件', '', ...missing.map((item) => `- ${item}`))
}
if (issues.length) {
  lines.push('', '## 阻塞问题', '', ...issues.map((item) => `- ${item}`))
}

writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: manifest.passed,
  artifacts: copied.map((item) => ({ fileName: item.fileName, sha256: item.sha256, bytes: item.bytes })),
  missing,
  issues,
}, null, 2))

if (!manifest.passed) process.exit(1)
