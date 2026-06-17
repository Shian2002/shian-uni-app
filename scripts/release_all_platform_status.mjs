#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.ALL_PLATFORM_STATUS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.ALL_PLATFORM_STATUS_OUT_DIR || join(root, 'artifacts', 'all-platform-status', `${localTimestamp()}-${version}`)
const strict = process.argv.includes('--strict') || process.env.ALL_PLATFORM_STATUS_STRICT === '1'
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

function readAt(dir, fileName) {
  return dir ? readJson(`${dir}/${fileName}`) : null
}

function yesNo(value) {
  return value ? '是' : '否'
}

function commandList(items) {
  return items.map((item) => `- \`${item}\``)
}

const latest = {
  lowImpactStatus: latestDir('artifacts/low-impact-status', 'report.json'),
  packageCompleteness: latestDir('artifacts/final-package-completeness', 'report.json'),
  platformBackendMatrix: latestDir('artifacts/platform-backend-matrix', 'report.json'),
  finalPackagePlan: latestDir('artifacts/final-package-plan', 'report.json'),
  currentDownloads: existsSync(join(root, 'artifacts', 'current-downloads', 'manifest.json')) ? 'artifacts/current-downloads' : '',
  mobileBuildRequests: latestDir('artifacts/mobile-build-requests', 'manifest.json'),
}

const lowImpactStatus = readAt(latest.lowImpactStatus, 'report.json')
const packageCompleteness = readAt(latest.packageCompleteness, 'report.json')
const platformBackendMatrix = readAt(latest.platformBackendMatrix, 'report.json')
const finalPackagePlan = readAt(latest.finalPackagePlan, 'report.json')
const currentDownloads = readJson('artifacts/current-downloads/manifest.json')
const mobileBuildRequests = readAt(latest.mobileBuildRequests, 'manifest.json')

const videoSafe = lowImpactStatus?.videoSafe === true
const currentDownloadsPassed = currentDownloads?.passed === true
const packageReadyCount = packageCompleteness?.ready ?? (packageCompleteness?.rows || []).filter((row) => row.ready).length
const packageTotal = packageCompleteness?.total ?? packageCompleteness?.rows?.length ?? 0
const missingPackages = packageCompleteness?.missing || []
const backendSummary = platformBackendMatrix?.summary || {}
const scopedPlatforms = (platformBackendMatrix?.platforms || []).filter((platform) => !deferredPlatforms.has(platform.id))
const scopedSummary = scopedPlatforms.length
  ? {
      total: scopedPlatforms.length,
      backendReady: scopedPlatforms.filter((platform) => platform.backendReady).length,
      packageReady: scopedPlatforms.filter((platform) => platform.packageReady).length,
      deviceReady: scopedPlatforms.filter((platform) => platform.deviceReady).length,
      missingCount: scopedPlatforms.reduce((sum, platform) => sum + (platform.missing || []).length, 0),
    }
  : backendSummary
const backendReady = scopedSummary.total > 0 && scopedSummary.backendReady === scopedSummary.total
const packageMatrixReady = scopedSummary.total > 0 && scopedSummary.packageReady === scopedSummary.total
const deviceReady = scopedSummary.total > 0 && scopedSummary.deviceReady === scopedSummary.total
const finalPlanReady = finalPackagePlan?.readyToRunFinalPackageRefresh === true
const storage = finalPackagePlan?.storage || {}

const blockers = [
  !currentDownloadsPassed && '固定下载入口 current-downloads 未通过。',
  !backendReady && '全端后端请求证据不足：platform:backend-matrix 未达到 backendReady=total。',
  !packageCompleteness?.passed && `最终安装包不完整：${missingPackages.join('、') || '未知缺口'}`,
  !deviceReady && '真机安装/登录/积分/时安agent/卸载截图未齐。',
  !finalPlanReady && '最终统一刷新安装包计划未 ready。',
].filter(Boolean)

const lowImpactCommands = [
  'npm run release:low-impact-status',
  'npm run release:all-platform-status',
  'npm run release:quota-status',
  'npm run mobile:build-requests',
  'npm run release:final-package-plan',
]

const afterVideoCommands = [
  'HBuilderX 插件已补齐后，继续用 mobile:build-env/mobile:hbuilderx-resources 记录 App Resource 状态。',
  deferredPlatforms.has('ios')
    ? 'iOS TestFlight/IPA 已延期到后续批次，本轮不补 Xcode/Apple Developer 签名环境。'
    : '补完整 Xcode/Apple Developer 签名环境后生成 iOS TestFlight/IPA。',
  deferredPlatforms.has('harmony')
    ? '鸿蒙 HAP/AppGallery 已延期到后续批次，本轮不补 DevEco/hdc/hvigor 或华为构建环境。'
    : '释放足够空间并补 DevEco/hdc/hvigor 或华为构建环境后生成鸿蒙 HAP/AppGallery。',
  '所有最终包回传后再统一跑 npm run release:intake && npm run release:artifact-metadata && npm run release:current-downloads。',
]

const cleanupPolicy = [
  '低影响阶段不执行删除，只读取报告。',
  '旧安装包清理先用 npm run release:package-cleanup-plan -- --keep=2 做 dry-run。',
  '只保护 current-downloads、release-inbox、证书/软著证据；确认后再删除旧 DMG/EXE/ZIP/APK 中间包。',
  '最终包全部更新后再刷新 current-downloads，减少反复生成和重复占用。',
]

const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  complete: blockers.length === 0,
  latest,
  releaseScope: {
    configPath: 'configs/release/current-release-scope.json',
    currentBatch: releaseScope.currentBatch || '',
    activePlatforms: releaseScope.activePlatforms || [],
    deferredPlatforms: [...deferredPlatforms],
  },
  videoSafe,
  currentDownloadsPassed,
  packageCompleteness: {
    passed: packageCompleteness?.passed === true,
    ready: packageReadyCount,
    total: packageTotal,
    missing: missingPackages,
  },
  backendMatrix: {
    complete: platformBackendMatrix?.complete === true,
    summary: backendSummary,
    scopedSummary,
    backendReady,
    packageMatrixReady,
    deviceReady,
  },
  storage,
  mobileBuildBlockers: mobileBuildRequests?.knownLocalBlockers || [],
  blockers,
  lowImpactCommands,
  afterVideoCommands,
  cleanupPolicy,
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

const currentDownloadLines = (currentDownloads?.files || []).map((file) => `- ${file.label}：\`${file.path}\` SHA-256 \`${file.sha256}\``)
const platformRows = (platformBackendMatrix?.platforms || []).map((platform) => `| ${platform.label} | ${yesNo(platform.packageReady)} | ${yesNo(platform.backendReady)} | ${yesNo(platform.deviceReady)} | ${platform.missing?.length ? platform.missing.join('<br>') : '无'} |`)

writeFileSync(join(outDir, 'README.md'), `${[
  '# 全端安装包与后端状态总览',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.complete ? '全端包、后端证据和真机证据齐备。' : '仍有安装包、真机证据或人工事项缺口。'}`,
  `> 低影响状态快照：${videoSafe ? '通过' : '未通过'}；仅提示本机风险，不作为安装包缺口。`,
  '',
  '## 总览',
  '',
  `- 固定下载入口：${currentDownloadsPassed ? '通过' : '缺失或未通过'}`,
  `- 当前批次：${releaseScope.currentBatch || '未配置'}；延期平台：${[...deferredPlatforms].join('、') || '无'}`,
  `- 最终包完整性：${report.packageCompleteness.ready}/${report.packageCompleteness.total}；缺口：${missingPackages.join('、') || '无'}`,
  `- 后端请求证据：${backendReady ? `${scopedSummary.backendReady}/${scopedSummary.total}` : '不足'}`,
  `- 真机证据：${deviceReady ? `${scopedSummary.deviceReady}/${scopedSummary.total}` : `${scopedSummary.deviceReady ?? 0}/${scopedSummary.total ?? 0}`}`,
  `- 存储占用：artifacts ${storage.artifactsMB ?? '-'}MB；desktop/release ${storage.desktopReleaseMB ?? '-'}MB；desktop/node_modules ${storage.desktopNodeModulesMB ?? '-'}MB；.npm-cache ${storage.npmCacheMB ?? '-'}MB。`,
  '',
  '## 平台矩阵',
  '',
  '| 平台 | 包文件 | 后端请求 | 真机证据 | 缺口 |',
  '| --- | --- | --- | --- | --- |',
  ...(platformRows.length ? platformRows : ['| - | - | - | - | 缺少 platform:backend-matrix 报告 |']),
  ...(deferredPlatforms.size ? ['', '延期平台本轮不作为阻塞：', ...[...deferredPlatforms].map((id) => `- \`${id}\``)] : []),
  '',
  '## 当前固定下载文件',
  '',
  ...(currentDownloadLines.length ? currentDownloadLines : ['- 固定下载入口缺失。']),
  '',
  '## 当前阻塞',
  '',
  ...(blockers.length ? blockers.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 移动端已知本机阻塞',
  '',
  ...(report.mobileBuildBlockers.length ? report.mobileBuildBlockers.map((item) => `- ${item}`) : ['- 暂无移动端本机阻塞记录。']),
  '',
  '## 低影响可先跑',
  '',
  ...commandList(lowImpactCommands),
  '',
  '## 重负载或外部环境补齐后再做',
  '',
  ...afterVideoCommands.map((item) => `- ${item}`),
  '',
  '## 存储策略',
  '',
  ...cleanupPolicy.map((item) => `- ${item}`),
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  complete: report.complete,
  videoSafe,
  currentDownloadsPassed,
  packageCompleteness: report.packageCompleteness,
  backendReady,
  blockers: blockers.length,
}, null, 2))

if (strict && !report.complete) process.exit(1)
