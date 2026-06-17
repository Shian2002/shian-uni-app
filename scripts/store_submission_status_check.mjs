#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.STORE_SUBMISSION_STATUS_STRICT === '1'
const configPath = process.env.STORE_SUBMISSION_STATUS_CONFIG || 'configs/release/store-submissions.json'
const packageJson = readJson('package.json') || {}
const version = process.env.STORE_SUBMISSION_STATUS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.STORE_SUBMISSION_STATUS_OUT_DIR || join(root, 'artifacts', 'store-submission-status', `${localTimestamp()}-${version}`)
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const activePlatforms = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms.filter((id) => !deferredPlatforms.has(id))
  : ['h5', 'android', 'ios', 'harmony', 'macos', 'windows'].filter((id) => !deferredPlatforms.has(id))

const requiredStores = [
  'yingyongbao',
  'huawei',
  'xiaomi',
  'oppo',
  'vivo',
  'google-play',
  'appstore',
  'harmony',
  'github-desktop',
]

const allowedStatuses = new Set([
  'not-submitted',
  'draft',
  'submitted',
  'in-review',
  'approved',
  'rejected',
  'remediating',
  'resubmitted',
])

const secretPatterns = [
  /password/i,
  /passwd/i,
  /secret/i,
  /token/i,
  /api[_-]?key/i,
  /keystore/i,
  /\.jks/i,
  /\.p12/i,
  /mobileprovision/i,
  /验证码/,
  /密码/,
  /密钥/,
  /口令/,
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

function pathExists(path) {
  return Boolean(path) && existsSync(join(root, path))
}

function hasSecretText(value) {
  const text = JSON.stringify(value || '')
  return secretPatterns.some((pattern) => pattern.test(text))
}

function storeReady(store) {
  return store.status === 'approved' &&
    Boolean(store.submissionId) &&
    Boolean(store.submittedAt) &&
    Boolean(store.artifactPath) &&
    Boolean(store.artifactSha256) &&
    Array.isArray(store.reviewScreenshotPaths) &&
    store.reviewScreenshotPaths.length > 0
}

function storePartial(store) {
  return ['draft', 'submitted', 'in-review', 'rejected', 'remediating', 'resubmitted'].includes(store.status)
}

function validateStore(store) {
  const issues = []
  const warnings = []

  if (!store.id) issues.push('缺少 id')
  if (!store.name) issues.push(`${store.id || 'unknown'} 缺少 name`)
  if (!store.platform) issues.push(`${store.id || 'unknown'} 缺少 platform`)
  if (!allowedStatuses.has(store.status)) issues.push(`${store.id || 'unknown'} status 非法: ${store.status}`)
  if (hasSecretText(store)) issues.push(`${store.id || 'unknown'} 可能包含账号密码、证书、密钥或验证码敏感信息`)

  if (['submitted', 'in-review', 'approved', 'rejected', 'remediating', 'resubmitted'].includes(store.status)) {
    if (!store.submissionId) warnings.push(`${store.id} 已进入提交/审核状态但缺少 submissionId`)
    if (!store.submittedAt) warnings.push(`${store.id} 已进入提交/审核状态但缺少 submittedAt`)
    if (!store.artifactPath) warnings.push(`${store.id} 已进入提交/审核状态但缺少 artifactPath`)
    if (!store.artifactSha256) warnings.push(`${store.id} 已进入提交/审核状态但缺少 artifactSha256`)
  }

  if (store.status === 'approved') {
    if (!store.submissionId) issues.push(`${store.id} approved 但缺少 submissionId`)
    if (!store.submittedAt) issues.push(`${store.id} approved 但缺少 submittedAt`)
    if (!store.artifactPath) issues.push(`${store.id} approved 但缺少 artifactPath`)
    if (!store.artifactSha256) issues.push(`${store.id} approved 但缺少 artifactSha256`)
    if (!Array.isArray(store.reviewScreenshotPaths) || store.reviewScreenshotPaths.length === 0) {
      issues.push(`${store.id} approved 但缺少 reviewScreenshotPaths`)
    }
  }

  if (store.artifactPath && !pathExists(store.artifactPath)) {
    warnings.push(`${store.id} artifactPath 不存在: ${store.artifactPath}`)
  }

  for (const screenshotPath of store.reviewScreenshotPaths || []) {
    if (!pathExists(screenshotPath)) warnings.push(`${store.id} reviewScreenshotPaths 不存在: ${screenshotPath}`)
  }

  return { issues, warnings }
}

function platformIds(store) {
  const ids = new Set()
  const id = String(store?.id || '').toLowerCase()
  const platform = String(store?.platform || '').toLowerCase()
  if (platform.includes('android')) ids.add('android')
  if (platform.includes('ios') || id === 'appstore') ids.add('ios')
  if (platform.includes('harmony') || id === 'harmony') ids.add('harmony')
  if (platform.includes('macos') || platform.includes('windows') || id.includes('desktop')) {
    ids.add('macos')
    ids.add('windows')
  }
  if (['yingyongbao', 'huawei', 'xiaomi', 'oppo', 'vivo', 'google-play'].includes(id)) ids.add('android')
  return [...ids]
}

function isDeferred(store) {
  const ids = platformIds(store)
  return ids.length > 0 && !ids.some((id) => activePlatforms.includes(id)) && ids.some((id) => deferredPlatforms.has(id))
}

function main() {
  const config = readJson(configPath)
  const issues = []
  const warnings = []
  if (!config) issues.push(`缺少或无法解析 ${configPath}`)
  if (!config?.stores || !Array.isArray(config.stores)) issues.push(`${configPath} 缺少 stores 数组`)
  const topLevelReview = { ...config, policy: undefined, stores: undefined }
  if (config && hasSecretText(topLevelReview)) issues.push(`${configPath} 顶层字段可能包含敏感信息`)

  const stores = Array.isArray(config?.stores) ? config.stores : []
  const ids = new Set(stores.map((store) => store.id))
  for (const id of requiredStores) {
    if (!ids.has(id)) issues.push(`${configPath} 缺少商店台账: ${id}`)
  }

  const rows = stores.map((store) => {
    const result = validateStore(store)
    const deferred = isDeferred(store)
    if (!deferred) {
      issues.push(...result.issues)
      warnings.push(...result.warnings)
    }
    const status = deferred ? 'deferred' : (storeReady(store) ? 'ready' : (storePartial(store) ? 'partial' : 'missing'))
    return {
      id: store.id,
      name: store.name,
      platform: store.platform,
      status: store.status,
      readiness: status,
      deferred,
      submissionId: store.submissionId || '',
      artifactPath: store.artifactPath || '',
      screenshotCount: (store.reviewScreenshotPaths || []).length,
      nextAction: store.nextAction || '',
      feedback: store.feedback || '',
      remediation: store.remediation || '',
      issues: result.issues,
      warnings: result.warnings,
    }
  })

  const activeRows = rows.filter((row) => !row.deferred)
  const summary = {
    ready: activeRows.filter((row) => row.readiness === 'ready').length,
    partial: activeRows.filter((row) => row.readiness === 'partial').length,
    missing: activeRows.filter((row) => row.readiness === 'missing').length,
    deferred: rows.filter((row) => row.readiness === 'deferred').length,
  }

  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    configPath,
    passed: issues.length === 0 && activeRows.length > 0 && summary.missing === 0 && summary.partial === 0,
    releaseScope: {
      configPath: 'configs/release/current-release-scope.json',
      currentBatch: releaseScope.currentBatch || '',
      activePlatforms,
      deferredPlatforms: [...deferredPlatforms],
    },
    summary,
    stores: rows,
    issues,
    warnings,
  }

  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

  const md = [
    '# 商店提交状态检查',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 配置：\`${configPath}\``,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    `汇总：READY ${summary.ready} / PARTIAL ${summary.partial} / MISSING ${summary.missing} / DEFERRED ${summary.deferred}`,
    '',
    '| 商店 | 平台 | 提交状态 | Readiness | 审核编号 | 截图数 | 下一步 |',
    '| --- | --- | --- | --- | --- | ---: | --- |',
    ...rows.map((row) => `| ${row.name || row.id} | ${row.platform || '-'} | ${row.status || '-'} | ${row.readiness} | ${row.submissionId || '-'} | ${row.screenshotCount} | ${row.nextAction || '-'} |`),
    ...(summary.deferred ? ['', '延期平台本轮不作为阻塞：', ...rows.filter((row) => row.deferred).map((row) => `- \`${row.id}\` ${row.name}`)] : []),
    '',
    '## 问题',
    '',
    ...(issues.length ? issues.map((issue) => `- ${issue}`) : ['- 无结构性问题。']),
    '',
    '## 警告',
    '',
    ...(warnings.length ? warnings.map((warning) => `- ${warning}`) : ['- 无警告。']),
    '',
    '## 放行规则',
    '',
    '- 非 strict 模式只生成台账报告，不因为未提交商店而失败。',
    '- 正式上架候选前运行 `npm run store:submission-status -- --strict`；所有商店必须至少有真实提交/审核证据，不能只停留在 `not-submitted`。',
    '- 本台账禁止记录账号密码、证书、密钥、验证码和用户隐私数据。',
    '',
  ].join('\n')
  writeFileSync(join(outDir, 'README.md'), md)

  console.log(JSON.stringify({
    outDir: rel(outDir),
    passed: report.passed,
    summary,
    issues,
    warnings,
  }, null, 2))

  if (strict && !report.passed) process.exit(1)
}

main()
