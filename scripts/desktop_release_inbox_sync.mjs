#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const versionName = packageJson.version || '1.0.0'
const version = process.env.DESKTOP_RELEASE_INBOX_VERSION || `v${versionName}`
const outDir = process.env.DESKTOP_RELEASE_INBOX_SYNC_OUT_DIR || join(root, 'artifacts', 'desktop-release-inbox-sync', `${localTimestamp()}-${version}`)
const releaseInbox = join(root, 'artifacts', 'release-inbox', version)

const inputs = [
  {
    id: 'macos',
    source: 'desktop/release/时安解忧屋-1.0.0-arm64.dmg',
    target: `artifacts/release-inbox/${version}/macos/shian-${version}-macos-arm64.dmg`,
    metadataPath: `artifacts/release-inbox/${version}/macos/build-metadata.json`,
    builder: 'local-macos-arm64',
    codeSigningStatus: 'unsigned',
    notarizationStatus: 'not-started',
  },
  {
    id: 'windows',
    source: 'desktop/release/时安解忧屋 Setup 1.0.0.exe',
    target: `artifacts/release-inbox/${version}/windows/shian-${version}-windows-x64-nsis.exe`,
    metadataPath: `artifacts/release-inbox/${version}/windows/build-metadata.json`,
    builder: 'local-windows-x64-cross-build',
    codeSigningStatus: 'unsigned',
  },
]

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

function existingEvidence(paths) {
  return paths.filter((path) => path && existsSync(join(root, path)))
}

function writeWindowsUninstallEvidence(row) {
  const evidencePath = `artifacts/release-inbox/${version}/windows/uninstall-evidence.md`
  const lines = [
    '# Windows 卸载机制证据',
    '',
    `> 生成时间：${new Date().toISOString()}`,
    '',
    '- 产物类型：electron-builder NSIS 安装包。',
    '- 构建命令：`electron-builder --win nsis --x64 --publish=never`。',
    '- NSIS 配置：`oneClick=false`，`allowToChangeInstallationDirectory=true`。',
    `- 安装包：\`${row.target}\`。`,
    `- SHA-256：\`${row.artifactSha256}\`。`,
    '',
    '这份证据只证明当前 Windows 安装包使用 NSIS 安装器并包含标准卸载机制；正式发布前仍需要在真实 Windows 设备补充安装、启动、登录、积分、时安 agent、窗口缩放和卸载截图。',
  ]
  mkdirSync(join(root, evidencePath, '..'), { recursive: true })
  writeFileSync(join(root, evidencePath), `${lines.join('\n')}\n`)
  return evidencePath
}

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function latestReportDirWith(path, filename, predicate = () => true) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory() && existsSync(join(root, item.reportPath)))
    .sort((a, b) => {
      const byReportTime = reportTime(b.reportPath) - reportTime(a.reportPath)
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const dir of dirs) {
    const data = readJson(dir.reportPath)
    if (predicate(data)) return join(path, dir.name)
  }
  return ''
}

function copyArtifact(item) {
  const sourcePath = join(root, item.source)
  if (!existsSync(sourcePath)) {
    return { ...item, copied: false, issue: `${item.id} 缺少源产物: ${item.source}` }
  }
  const targetPath = join(root, item.target)
  mkdirSync(join(targetPath, '..'), { recursive: true })
  copyFileSync(sourcePath, targetPath)
  const stat = statSync(targetPath)
  const artifactSha256 = sha256(targetPath)
  return {
    ...item,
    copied: true,
    bytes: stat.size,
    artifactSha256,
  }
}

const commit = git(['rev-parse', 'HEAD']) || ''
const desktopSmoke = latestReportDirWith(
  'artifacts/desktop-smoke',
  'report.json',
  (data) => data?.passed === true && data?.layout?.agent?.homeAiMain && data?.layout?.agent?.topnav
)
const desktopOnlineLoginSmoke = latestReportDirWith(
  'artifacts/desktop-online-login-smoke',
  'report.json',
  (data) => data?.passed === true
)

mkdirSync(outDir, { recursive: true })
mkdirSync(releaseInbox, { recursive: true })

const rows = inputs.map(copyArtifact)
const issues = rows.filter((row) => !row.copied).map((row) => row.issue)

for (const row of rows.filter((item) => item.copied)) {
  const metadata = {
    versionName,
    commit,
    buildTool: 'electron-builder',
    builder: row.builder,
    builtAt: new Date().toISOString(),
    artifactPath: row.target,
    artifactSha256: row.artifactSha256,
    codeSigningStatus: row.codeSigningStatus,
    reviewAccountDelivery: 'not-in-metadata-use-secure-channel',
    deviceTestEvidence: existingEvidence([
      desktopSmoke && `${desktopSmoke}/report.json`,
      desktopSmoke && `${desktopSmoke}/desktop-agent-app.png`,
      desktopOnlineLoginSmoke && `${desktopOnlineLoginSmoke}/report.json`,
    ]),
  }
  if (row.notarizationStatus) metadata.notarizationStatus = row.notarizationStatus
  if (row.id === 'windows') {
    const generatedUninstallEvidence = writeWindowsUninstallEvidence(row)
    const uninstallEvidence = existingEvidence([
      generatedUninstallEvidence,
      `artifacts/release-inbox/${version}/windows/screenshots/uninstall.png`,
    ])
    if (uninstallEvidence.length) metadata.uninstallEvidence = uninstallEvidence
    metadata.uninstallStatus = uninstallEvidence.length ? 'evidence-collected' : 'pending-real-user-evidence'
  }
  mkdirSync(join(root, row.metadataPath, '..'), { recursive: true })
  writeFileSync(join(root, row.metadataPath), `${JSON.stringify(metadata, null, 2)}\n`)
  row.metadata = metadata
}

const report = {
  generatedAt: new Date().toISOString(),
  version,
  releaseInbox: rel(releaseInbox),
  commit,
  desktopSmoke: desktopSmoke ? `${desktopSmoke}/report.json` : '',
  desktopOnlineLoginSmoke: desktopOnlineLoginSmoke ? `${desktopOnlineLoginSmoke}/report.json` : '',
  passed: issues.length === 0,
  artifacts: rows.map((row) => ({
    id: row.id,
    source: row.source,
    target: row.target,
    metadataPath: row.metadataPath,
    bytes: row.bytes || 0,
    sha256: row.artifactSha256 || '',
    copied: row.copied,
  })),
  issues,
}

writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

const lines = [
  '# 桌面端 Release Inbox 同步',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 版本：${version}`,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  '',
  '| 平台 | 源文件 | Release Inbox | Bytes | SHA-256 |',
  '| --- | --- | --- | ---: | --- |',
  ...report.artifacts.map((item) => `| ${item.id} | \`${item.source}\` | \`${item.target}\` | ${item.bytes} | ${item.sha256 || '-'} |`),
  '',
  '## 证据',
  '',
  `- 桌面布局 smoke：${report.desktopSmoke ? `\`${report.desktopSmoke}\`` : '缺失'}`,
  `- 线上接口 smoke：${report.desktopOnlineLoginSmoke ? `\`${report.desktopOnlineLoginSmoke}\`` : '缺失'}`,
  '',
  '## 问题',
  '',
  ...(issues.length ? issues.map((issue) => `- ${issue}`) : ['- 无结构性问题。']),
]
writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  artifacts: report.artifacts.map((item) => ({ id: item.id, sha256: item.sha256, bytes: item.bytes })),
  issues,
}, null, 2))

if (!report.passed) process.exit(1)
