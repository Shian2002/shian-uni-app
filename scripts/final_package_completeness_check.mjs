#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { extname, join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.FINAL_PACKAGE_COMPLETENESS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.FINAL_PACKAGE_COMPLETENESS_OUT_DIR || join(root, 'artifacts', 'final-package-completeness', `${localTimestamp()}-${version}`)
const strict = process.argv.includes('--strict') || process.env.FINAL_PACKAGE_COMPLETENESS_STRICT === '1'
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))

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

function latestDir(parent, requiredFile = '') {
  const fullParent = join(root, parent)
  if (!existsSync(fullParent)) return ''
  const dirs = readdirSync(fullParent, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => ({ name: entry.name, fullPath: join(fullParent, entry.name) }))
    .filter((entry) => !requiredFile || existsSync(join(entry.fullPath, requiredFile)))
    .sort((a, b) => statSync(b.fullPath).mtimeMs - statSync(a.fullPath).mtimeMs || b.name.localeCompare(a.name))
  return dirs[0] ? `${parent}/${dirs[0].name}` : ''
}

function walk(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return []
  const stat = statSync(fullPath)
  if (stat.isFile()) return [fileInfo(path)].filter(Boolean)
  if (!stat.isDirectory()) return []
  return readdirSync(fullPath, { withFileTypes: true }).flatMap((entry) => walk(`${path}/${entry.name}`))
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(join(root, path))).digest('hex')
}

function fileInfo(path) {
  if (!path || !existsSync(join(root, path)) || !statSync(join(root, path)).isFile()) return null
  const stat = statSync(join(root, path))
  return {
    path,
    bytes: stat.size,
    sha256: sha256(path),
    ext: extname(path).toLowerCase(),
  }
}

function uniqueByPath(items) {
  const map = new Map()
  for (const item of items.filter(Boolean)) {
    if (!map.has(item.path)) map.set(item.path, item)
  }
  return [...map.values()]
}

function uploadCandidateFiles(manifest) {
  return (manifest?.uploadCandidates || []).map((item) => fileInfo(item.path)).filter(Boolean)
}

function manifestFiles(manifest) {
  return (manifest?.files || []).map((item) => fileInfo(item.path)).filter(Boolean)
}

function matchesAny(file, rules) {
  return rules.some((rule) => {
    if (rule.ext && file.ext !== rule.ext) return false
    if (rule.pathIncludes && !rule.pathIncludes.every((part) => file.path.toLowerCase().includes(part))) return false
    return true
  })
}

function platformRow(platformId) {
  return (platformBackendMatrix?.platforms || []).find((platform) => platform.id === platformId) || null
}

function platformPackageReady(platformId) {
  if (!platformId) return true
  if (deferredPlatforms.has(platformId)) return true
  return platformRow(platformId)?.packageReady === true
}

function platformPackageIssue(platformId, label) {
  if (!platformId) return ''
  const row = platformRow(platformId)
  if (!row) return `${label} 平台矩阵缺失，无法证明最终包可用`
  if (row.packageReady === true) return ''
  return `${label} 平台矩阵 packageReady=false：${(row.missing || []).join('；') || '缺少最新最终包证据'}`
}

const latest = {
  releasePackage: latestDir('artifacts/release-packages', 'upload-manifest.json'),
  currentDownloads: existsSync(join(root, 'artifacts/current-downloads/manifest.json')) ? 'artifacts/current-downloads' : '',
  finalPackagePlan: latestDir('artifacts/final-package-plan', 'report.json'),
  platformBackendMatrix: latestDir('artifacts/platform-backend-matrix', 'report.json'),
}

const releasePackage = readJson(`${latest.releasePackage}/upload-manifest.json`)
const currentDownloads = readJson('artifacts/current-downloads/manifest.json')
const finalPackagePlan = readJson(`${latest.finalPackagePlan}/report.json`)
const platformBackendMatrix = readJson(`${latest.platformBackendMatrix}/report.json`)

const evidenceFiles = uniqueByPath([
  ...uploadCandidateFiles(releasePackage),
  ...manifestFiles(currentDownloads),
  ...walk(`artifacts/release-inbox/${packageJson.version || '1.0.0'}`),
])

const requirements = [
  {
    id: 'android-apk',
    label: 'Android APK',
    platformId: 'android',
    rules: [{ ext: '.apk', pathIncludes: ['android'] }],
    requiredForFinal: true,
  },
  {
    id: 'android-aab',
    label: 'Android AAB',
    platformId: 'android',
    rules: [{ ext: '.aab', pathIncludes: ['android'] }],
    requiredForFinal: true,
  },
  {
    id: 'ios-testflight-or-ipa',
    label: 'iOS TestFlight/IPA',
    platformId: 'ios',
    rules: [
      { ext: '.ipa', pathIncludes: ['ios'] },
      { ext: '.json', pathIncludes: ['ios', 'testflight'] },
    ],
    requiredForFinal: true,
  },
  {
    id: 'harmony-hap-or-appgallery',
    label: '鸿蒙 HAP/AppGallery',
    platformId: 'harmony',
    rules: [
      { ext: '.hap', pathIncludes: ['harmony'] },
      { ext: '.json', pathIncludes: ['harmony', 'appgallery'] },
    ],
    requiredForFinal: true,
  },
  {
    id: 'macos-dmg',
    label: 'macOS DMG',
    platformId: 'macos',
    rules: [{ ext: '.dmg', pathIncludes: ['macos'] }],
    requiredForFinal: true,
  },
  {
    id: 'macos-app-zip',
    label: 'macOS App ZIP',
    platformId: 'macos',
    rules: [{ ext: '.zip', pathIncludes: ['macos', 'app'] }],
    requiredForFinal: true,
  },
  {
    id: 'windows-installer',
    label: 'Windows EXE/MSI/NSIS',
    platformId: 'windows',
    rules: [
      { ext: '.exe', pathIncludes: ['windows'] },
      { ext: '.msi', pathIncludes: ['windows'] },
    ],
    requiredForFinal: true,
  },
]

const rows = requirements.map((requirement) => {
  const deferred = deferredPlatforms.has(requirement.platformId)
  const files = evidenceFiles.filter((file) => matchesAny(file, requirement.rules))
  const filesReady = files.length > 0
  const platformReady = platformPackageReady(requirement.platformId)
  const issue = deferred
    ? ''
    : (!filesReady
    ? `缺少最终包：${requirement.label}`
    : (!platformReady ? platformPackageIssue(requirement.platformId, requirement.label) : ''))
  return {
    ...requirement,
    deferred,
    requiredForCurrentBatch: requirement.requiredForFinal && !deferred,
    filesReady,
    platformReady,
    ready: deferred || (filesReady && platformReady),
    issue,
    files,
  }
})

const activeRows = rows.filter((row) => row.requiredForCurrentBatch)
const missing = rows.filter((row) => row.requiredForCurrentBatch && !row.ready).map((row) => row.label)
const backendReady = platformBackendMatrix?.summary?.total > 0 &&
  platformBackendMatrix.summary.backendReady === platformBackendMatrix.summary.total
const planReady = finalPackagePlan?.readyToRunFinalPackageRefresh === true
const issues = [
  !latest.releasePackage && '缺少 release:package upload-manifest',
  !latest.currentDownloads && '缺少 artifacts/current-downloads/manifest.json',
  !backendReady && '全端后端能力矩阵未达到 backendReady=total',
  !planReady && '最终安装包刷新计划未处于 readyToRunFinalPackageRefresh=true',
  ...rows.filter((row) => row.requiredForFinal && !row.ready).map((row) => row.issue || `缺少或过期最终包：${row.label}`),
].filter(Boolean)

const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  passed: issues.length === 0,
  releaseScope: {
    configPath: 'configs/release/current-release-scope.json',
    currentBatch: releaseScope.currentBatch || '',
    activePlatforms: releaseScope.activePlatforms || [],
    deferredPlatforms: [...deferredPlatforms],
  },
  latest,
  backendReady,
  planReady,
  evidenceFileCount: evidenceFiles.length,
  ready: activeRows.filter((row) => row.ready).length,
  total: activeRows.length,
  activeTotal: activeRows.length,
  activeReady: activeRows.filter((row) => row.ready).length,
  rows,
  missing,
  issues,
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# 最终安装包完整性检查',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.passed ? '当前批次最终安装包类型齐备。' : '当前批次最终安装包仍不齐。'}`,
  `> 当前批次：${releaseScope.currentBatch || '未配置'}；延期平台：${[...deferredPlatforms].join('、') || '无'}`,
  '',
  '## 包类型',
  '',
  '| 类型 | 状态 | 文件 |',
  '| --- | --- | --- |',
  ...rows.map((row) => `| ${row.label} | ${row.deferred ? 'deferred' : (row.ready ? 'ready' : (row.filesReady ? 'stale' : 'missing'))} | ${row.files.map((file) => `\`${file.path}\``).join('<br>') || '-'} |`),
  '',
  '## 证据',
  '',
  `- Release package：\`${latest.releasePackage || '缺失'}\``,
  `- 固定下载入口：\`${latest.currentDownloads || '缺失'}\``,
  `- 全端后端矩阵：\`${latest.platformBackendMatrix || '缺失'}\`；后端 ready：${backendReady ? '是' : '否'}`,
  `- 最终打包计划：\`${latest.finalPackagePlan || '缺失'}\`；计划 ready：${planReady ? '是' : '否'}`,
  `- 候选文件数：${report.evidenceFileCount}`,
  '',
  '## 缺口',
  '',
  ...(issues.length ? issues.map((issue) => `- ${issue}`) : ['- 无。']),
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  ready: report.activeReady,
  total: report.activeTotal,
  deferred: [...deferredPlatforms],
  missing,
  issues,
}, null, 2))

if (strict && !report.passed) process.exit(1)
