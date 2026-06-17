#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { extname, join, relative } from 'node:path'

const root = process.cwd()
const apply = process.argv.includes('--apply')
const confirm = process.env.CONFIRM_PACKAGE_BINARY_CLEANUP || ''
const packageJson = readJson('package.json') || {}
const version = process.env.PACKAGE_BINARY_CLEANUP_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.PACKAGE_BINARY_CLEANUP_OUT_DIR || join(root, 'artifacts', 'package-binary-cleanup', `${localTimestamp()}-${version}`)
const keepArg = process.argv.find((arg) => arg.startsWith('--keep='))
const keep = Math.max(1, Number(keepArg?.split('=')[1] || process.env.PACKAGE_BINARY_CLEANUP_KEEP || 2))

const binaryExts = new Set(['.apk', '.aab', '.ipa', '.hap', '.dmg', '.zip', '.exe', '.msi'])
const protectedPrefixes = [
  'artifacts/current-downloads/',
  'artifacts/release-inbox/',
  'artifacts/ip-evidence/',
  'artifacts/soft-copyright-application/',
]
const scanRoots = [
  'desktop/release',
  'artifacts/desktop-downloads',
  'artifacts/desktop-macos-user-packets',
  'artifacts/desktop-windows-user-packets',
  'artifacts/desktop-macos-dmg-from-app',
  'artifacts/desktop-macos-updated-app',
  'artifacts/release-packages',
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

function reportTime(path, fullPath = '') {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  if (Number.isFinite(time) && time > 0) return time
  return fullPath && existsSync(fullPath) ? statSync(fullPath).mtimeMs : 0
}

function latestDir(parent, requiredFile = '') {
  const fullParent = join(root, parent)
  if (!existsSync(fullParent)) return ''
  const dirs = readdirSync(fullParent, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => {
      const fullPath = join(fullParent, entry.name)
      return { name: entry.name, fullPath, reportPath: requiredFile ? `${parent}/${entry.name}/${requiredFile}` : '' }
    })
    .filter((entry) => !requiredFile || existsSync(join(root, entry.reportPath)))
    .sort((a, b) => reportTime(b.reportPath, b.fullPath) - reportTime(a.reportPath, a.fullPath) || b.name.localeCompare(a.name))
  return dirs[0] ? `${parent}/${dirs[0].name}` : ''
}

function addExistingPath(set, path) {
  if (path && existsSync(join(root, path))) set.add(path)
}

function collectDynamicProtectedPaths() {
  const paths = new Set()
  const currentIndexPointer = readJson('artifacts/current-index-latest.json')
  const currentIndex = currentIndexPointer?.path ? readJson(`${currentIndexPointer.path}/index.json`) : null
  for (const item of Object.values(currentIndex?.usable || {})) {
    addExistingPath(paths, item?.path)
  }
  const currentDownloads = readJson('artifacts/current-downloads/manifest.json')
  for (const item of currentDownloads?.files || []) {
    addExistingPath(paths, item.path)
    addExistingPath(paths, item.source)
  }
  const tryNow = readJson('artifacts/try-now/latest-manifest.json')
  for (const key of ['macosDmg', 'macosUpdatedAppZip', 'windowsInstaller', 'androidDebugApk', 'androidDebugAab']) {
    addExistingPath(paths, tryNow?.[key])
  }
  return paths
}

const dynamicProtectedPaths = collectDynamicProtectedPaths()
const latestLowImpactStatusDir = latestDir('artifacts/low-impact-status', 'report.json')
const lowImpactStatus = latestLowImpactStatusDir ? readJson(`${latestLowImpactStatusDir}/report.json`) : null

function walk(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return []
  const stat = statSync(fullPath)
  if (stat.isFile()) return [fileRow(path, stat)]
  if (!stat.isDirectory()) return []
  return readdirSync(fullPath, { withFileTypes: true }).flatMap((entry) => walk(`${path}/${entry.name}`))
}

function fileRow(path, stat) {
  return {
    path,
    bytes: stat.size,
    ext: extname(path).toLowerCase(),
    mtimeMs: stat.mtimeMs,
    protected: protectedPrefixes.some((prefix) => path.startsWith(prefix)) || dynamicProtectedPaths.has(path),
  }
}

function groupKey(file) {
  if (file.ext === '.apk') return 'android-apk'
  if (file.ext === '.aab') return 'android-aab'
  if (file.ext === '.ipa') return 'ios-ipa'
  if (file.ext === '.hap') return 'harmony-hap'
  if (file.ext === '.dmg') return 'macos-dmg'
  if (file.ext === '.zip' && /mac|arm64|时安解忧屋|app/i.test(file.path)) return 'macos-app-zip'
  if (file.ext === '.exe' || file.ext === '.msi') return 'windows-installer'
  return 'other-binary'
}

function mb(bytes) {
  return Math.round((bytes / 1024 / 1024) * 10) / 10
}

const allFiles = scanRoots.flatMap(walk)
  .filter((file) => binaryExts.has(file.ext))
  .filter((file) => !file.protected)

const groups = new Map()
for (const file of allFiles) {
  const key = groupKey(file)
  const items = groups.get(key) || []
  items.push(file)
  groups.set(key, items)
}

const preserved = []
const candidates = []
for (const [group, files] of groups) {
  const sorted = files.sort((a, b) => b.mtimeMs - a.mtimeMs || b.path.localeCompare(a.path))
  preserved.push(...sorted.slice(0, keep).map((file) => ({ ...file, group })))
  candidates.push(...sorted.slice(keep).map((file) => ({ ...file, group })))
}

const deleted = []
const blockedReasons = []
if (apply && confirm !== `delete-old-packages:${version}`) {
  blockedReasons.push(`删除旧安装包需要设置 CONFIRM_PACKAGE_BINARY_CLEANUP=delete-old-packages:${version}`)
}
const blockedReason = blockedReasons.join('；')
if (apply && blockedReasons.length === 0) {
  for (const file of candidates) {
    rmSync(join(root, file.path), { force: true })
    deleted.push(file)
  }
}

const candidateBytes = candidates.reduce((total, file) => total + file.bytes, 0)
const report = {
  generatedAt: new Date().toISOString(),
  version,
  mode: apply ? 'apply' : 'dry-run',
  applyBlocked: Boolean(blockedReason),
  blockedReason,
  keep,
  lowImpactStatus: {
    path: latestLowImpactStatusDir,
    videoSafe: lowImpactStatus?.videoSafe === true,
    heavyProcesses: lowImpactStatus?.heavyProcesses?.length || 0,
  },
  scanRoots,
  protectedPrefixes,
  dynamicProtectedPaths: [...dynamicProtectedPaths].sort(),
  preserved: preserved.map(({ group, path, bytes, ext }) => ({ group, path, bytes, ext })),
  candidates: candidates.map(({ group, path, bytes, ext }) => ({ group, path, bytes, ext })),
  deleted: deleted.map(({ group, path, bytes, ext }) => ({ group, path, bytes, ext })),
  candidateCount: candidates.length,
  deletedCount: deleted.length,
  estimatedFreedBytes: candidateBytes,
  estimatedFreedMB: mb(candidateBytes),
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# 旧安装包清理计划',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 模式：${report.mode}`,
  `> 每类保留最新：${keep}`,
  `> 候选数量：${report.candidateCount}`,
  `> 预计可释放：${report.estimatedFreedMB}MB`,
  '',
  '## 保护目录',
  '',
  ...protectedPrefixes.map((prefix) => `- \`${prefix}\``),
  '',
  '## 当前入口动态保护',
  '',
  ...([...dynamicProtectedPaths].sort().length ? [...dynamicProtectedPaths].sort().map((path) => `- \`${path}\``) : ['- 无。']),
  '',
  '## 删除候选',
  '',
  ...(report.candidates.length ? report.candidates.map((file) => `- \`${file.path}\` (${file.group}, ${mb(file.bytes)}MB)`) : ['- 无。']),
  '',
  '## 已删除',
  '',
  ...(report.deleted.length ? report.deleted.map((file) => `- \`${file.path}\` (${file.group}, ${mb(file.bytes)}MB)`) : ['- 无。']),
  '',
  '## 执行保护',
  '',
  `- 低影响状态：${latestLowImpactStatusDir ? `\`${latestLowImpactStatusDir}/report.json\`` : '缺失'}；videoSafe=${lowImpactStatus?.videoSafe === true ? 'true' : 'false'}。`,
  '- 删除仍需显式确认变量；脚本会保护 current-downloads、release-inbox、证书/软著证据和当前索引引用的包。',
  blockedReason ? `- ${blockedReason}` : '- 默认 dry-run，不删除文件；确需删除时使用脚本输出的确认变量。',
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  mode: report.mode,
  applyBlocked: report.applyBlocked,
  candidateCount: report.candidateCount,
  deletedCount: report.deletedCount,
  estimatedFreedMB: report.estimatedFreedMB,
  blockedReason,
}, null, 2))

if (apply && blockedReason) process.exit(1)
