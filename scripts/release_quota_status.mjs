#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = `v${packageJson.version || '0.0.0'}`
const outDir = join(root, 'artifacts', 'quota-status', `${localTimestamp()}-${version}`)
const weeklyQuotaPercent = process.env.CODEX_WEEKLY_QUOTA_PERCENT || ''

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

function latestDir(path, filename = 'report.json') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory() && readJson(item.reportPath))
    .sort((a, b) => {
      const byTime = reportTime(b.reportPath, b.full) - reportTime(a.reportPath, a.full)
      return byTime || b.name.localeCompare(a.name)
    })
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function latestFile(path, suffix) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const files = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name) }))
    .filter((item) => statSync(item.full).isFile() && item.name.endsWith(suffix))
    .sort((a, b) => statSync(b.full).mtimeMs - statSync(a.full).mtimeMs || b.name.localeCompare(a.name))
  return files[0] ? join(path, files[0].name) : ''
}

function reportTime(path, fullPath = '') {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  if (Number.isFinite(time) && time > 0) return time
  return fullPath && existsSync(fullPath) ? statSync(fullPath).mtimeMs : 0
}

function status(ok) {
  return ok ? 'ready' : 'missing'
}

function quotaLevel(percentText) {
  if (String(percentText || '').trim() === '') return 'unknown'
  const percent = Number(percentText)
  if (!Number.isFinite(percent)) return 'unknown'
  if (percent <= 40) return 'low'
  if (percent <= 60) return 'cautious'
  return 'normal'
}

function suggestedMode(level) {
  if (level === 'low') return 'evidence-only'
  if (level === 'cautious') return 'avoid-rebuilds'
  if (level === 'normal') return 'normal'
  return 'manual'
}

function remainingHardBlocks(report, reportDir) {
  if (!reportDir) return ['release package 尚未生成']
  if (!report) return ['release package manifest 尚未可读']
  if (Array.isArray(report.missingHardBlocks)) return report.missingHardBlocks
  return ['release package manifest 缺少 missingHardBlocks 字段']
}

const tryNowLatest = readJson('artifacts/try-now/latest-manifest.json')
const tryNowManifest = tryNowLatest?.manifest ? readJson(tryNowLatest.manifest) : null
const releasePackageDir = latestDir('artifacts/release-packages', 'upload-manifest.json')
const releasePackage = releasePackageDir ? readJson(`${releasePackageDir}/upload-manifest.json`) : null
const readinessFile = latestFile('artifacts/release-readiness', '.json')
const localInstallDir = latestDir('artifacts/desktop-macos-local-install')
const lifecycleDir = latestDir('artifacts/desktop-macos-lifecycle')
const onlineSmokeDir = latestDir('artifacts/desktop-online-login-smoke')
const desktopSmokeDir = latestDir('artifacts/desktop-smoke')
const externalHandoffDir = latestDir('artifacts/external-handoff', 'manifest.json')
const currentQuotaLevel = quotaLevel(weeklyQuotaPercent)
const currentSuggestedMode = suggestedMode(currentQuotaLevel)
const currentRemainingHardBlocks = remainingHardBlocks(releasePackage, releasePackageDir)

const report = {
  generatedAt: new Date().toISOString(),
  version,
  quotaMode: true,
  weeklyQuotaPercent,
  quotaLevel: currentQuotaLevel,
  suggestedMode: currentSuggestedMode,
  note: '低成本状态包：只读取现有证据，不构建、不打包、不启动 App。',
  currentUsable: {
    macosInstalledApp: status(existsSync('/Applications/时安解忧屋.app/Contents/MacOS/时安解忧屋')),
    macosDmg: tryNowLatest?.macosDmg || '',
    windowsInstaller: tryNowLatest?.windowsInstaller || '',
    mobileAppResource: tryNowLatest?.mobileAppResource || '',
  },
  evidence: {
    tryNow: tryNowLatest?.latestPacketDir || '',
    tryNowManifest: tryNowLatest?.manifest || '',
    releasePackage: releasePackageDir,
    readiness: readinessFile,
    macosLocalInstall: localInstallDir ? `${localInstallDir}/report.json` : '',
    macosLifecycle: lifecycleDir ? `${lifecycleDir}/report.json` : '',
    desktopSmoke: desktopSmokeDir ? `${desktopSmokeDir}/report.json` : '',
    desktopOnlineLoginSmoke: onlineSmokeDir ? `${onlineSmokeDir}/report.json` : '',
    externalHandoff: externalHandoffDir ? `${externalHandoffDir}/README.md` : '',
  },
  proofSummary: {
    tryNowPassed: tryNowLatest?.passed === true && tryNowManifest?.passed === true,
    localInstallRecorded: Boolean(localInstallDir),
    lifecycleRecorded: Boolean(lifecycleDir),
    onlineApiRecorded: Boolean(onlineSmokeDir),
    remainingHardBlocks: currentRemainingHardBlocks,
  },
  quotaSafeNextCommands: [
    'npm run release:quota-status',
    'npm run release:external-handoff',
    'npm run release:check',
    'python3 -m pytest -q tests/desktop_macos_local_install_test.py tests/current_try_now_packet_test.py',
  ],
  avoidUntilNeeded: [
    'npm run desktop:build:mac:arm64',
    'npm run desktop:build:win:x64',
    'npm run build:app',
    'npm run store:screenshots',
  ],
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

const lines = [
  '# 低成本发行状态包',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 版本：${version}`,
  `> Codex Pro 周额度：${weeklyQuotaPercent ? `${weeklyQuotaPercent}%` : '未提供'}`,
  `> 额度等级：${currentQuotaLevel}`,
  `> 建议模式：${currentSuggestedMode}`,
  '> 说明：只读取现有证据，不构建、不打包、不启动 App。',
  '',
  '## 现在可用',
  '',
  `- macOS 已安装 App：${report.currentUsable.macosInstalledApp}`,
  `- macOS DMG：\`${report.currentUsable.macosDmg || '缺失'}\``,
  `- Windows 安装器：\`${report.currentUsable.windowsInstaller || '缺失'}\``,
  `- 移动端 App 资源：\`${report.currentUsable.mobileAppResource || '缺失'}\``,
  '',
  '## 当前证据',
  '',
  ...Object.entries(report.evidence).map(([key, value]) => `- ${key}：\`${value || '缺失'}\``),
  '',
  '## 额度策略',
  '',
  `- 当前等级：${currentQuotaLevel}`,
  `- 当前建议：${currentSuggestedMode}`,
  '- low/evidence-only 时只做文档、模板、状态包、现有证据检查；暂缓构建、打包、截图和长链路回归。',
  '',
  '## 剩余硬阻塞',
  '',
  ...(report.proofSummary.remainingHardBlocks.length
    ? report.proofSummary.remainingHardBlocks.map((item) => `- ${item}`)
    : ['- 暂无硬阻塞。']),
  '',
  '## 额度紧张时优先跑',
  '',
  ...report.quotaSafeNextCommands.map((cmd) => `- \`${cmd}\``),
  '',
  '## 暂缓重跑',
  '',
  ...report.avoidUntilNeeded.map((cmd) => `- \`${cmd}\``),
]
writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  weeklyQuotaPercent: weeklyQuotaPercent || 'unknown',
  quotaLevel: currentQuotaLevel,
  suggestedMode: currentSuggestedMode,
  macosInstalledApp: report.currentUsable.macosInstalledApp,
  tryNowPassed: report.proofSummary.tryNowPassed,
  remainingHardBlocks: report.proofSummary.remainingHardBlocks.length,
}, null, 2))
