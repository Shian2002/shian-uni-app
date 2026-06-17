#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.APP_RECORD_STRICT === '1'
const configPath = process.env.APP_RECORD_CONFIG || 'configs/release/app-record.json'
const packageJson = readJson('package.json') || {}
const version = process.env.APP_RECORD_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.APP_RECORD_OUT_DIR || join(root, 'artifacts', 'app-record-status', `${localTimestamp()}-${version}`)
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const activePlatforms = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms.filter((id) => !deferredPlatforms.has(id))
  : ['h5', 'android', 'ios', 'harmony', 'macos', 'windows'].filter((id) => !deferredPlatforms.has(id))
const allowedStatuses = new Set(['not-ready', 'pending', 'ready', 'not-required'])
const secretPatterns = [/password/i, /secret/i, /token/i, /api[_-]?key/i, /\.p12/i, /\.jks/i, /验证码/, /密码/, /密钥/]

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
  return secretPatterns.some((pattern) => pattern.test(JSON.stringify(value || '')))
}

function validateRecord(record) {
  const issues = []
  const warnings = []
  if (!record.id) issues.push('APP 备案台账缺少 id')
  if (!record.platform) issues.push(`${record.id || 'unknown'} 缺少 platform`)
  if (!record.target) issues.push(`${record.id || 'unknown'} 缺少 target`)
  if (!record.ownerAlias) issues.push(`${record.id || 'unknown'} 缺少 ownerAlias`)
  if (!allowedStatuses.has(record.status)) issues.push(`${record.id || 'unknown'} status 非法: ${record.status}`)
  if (hasSecretText(record)) issues.push(`${record.id || 'unknown'} 可能包含密码、token、证书或验证码`)
  if (['Android', 'Harmony', 'iOS'].includes(record.platform) && !record.packageOrBundleId) {
    issues.push(`${record.id || 'unknown'} 缺少 packageOrBundleId`)
  }
  const evidencePaths = Array.isArray(record.evidencePaths) ? record.evidencePaths : []
  if (record.status === 'ready' && evidencePaths.length === 0) issues.push(`${record.id} status=ready 但缺少 evidencePaths`)
  if (record.status === 'not-required' && !record.notRequiredReason) issues.push(`${record.id} status=not-required 但缺少 notRequiredReason`)
  for (const evidencePath of evidencePaths) {
    if (!pathExists(evidencePath)) warnings.push(`${record.id} evidencePath 不存在: ${evidencePath}`)
  }
  const readiness = issues.length === 0 && warnings.length === 0 && ['ready', 'not-required'].includes(record.status)
    ? 'ready'
    : (record.status ? 'partial' : 'missing')
  return {
    id: record.id || '',
    platform: record.platform || '',
    target: record.target || '',
    packageOrBundleId: record.packageOrBundleId || '',
    status: record.status || '',
    readiness,
    ownerAlias: record.ownerAlias || '',
    nextAction: record.nextAction || '',
    issues,
    warnings,
  }
}

function platformIds(record) {
  const ids = new Set()
  const platform = String(record?.platform || '').toLowerCase()
  const id = String(record?.id || '').toLowerCase()
  if (platform.includes('h5') || id.includes('h5')) ids.add('h5')
  if (platform.includes('android') || id.includes('android') || id.includes('google-play')) ids.add('android')
  if (platform.includes('ios') || id.includes('ios')) ids.add('ios')
  if (platform.includes('harmony') || id.includes('harmony')) ids.add('harmony')
  return [...ids]
}

function isDeferred(record) {
  const ids = platformIds(record)
  return ids.length > 0 && !ids.some((id) => activePlatforms.includes(id)) && ids.some((id) => deferredPlatforms.has(id))
}

function main() {
  const config = readJson(configPath)
  const issues = []
  const warnings = []
  if (!config) issues.push(`缺少或无法解析 ${configPath}`)
  if (config && hasSecretText({ ...config, policy: undefined, records: undefined })) issues.push(`${configPath} 顶层字段可能包含密码、token、证书或验证码`)
  if (!Array.isArray(config?.records)) issues.push(`${configPath} 缺少 records 数组`)
  const rows = Array.isArray(config?.records) ? config.records.map((record) => {
    const row = validateRecord(record)
    const deferred = isDeferred(record)
    return deferred ? { ...row, readiness: 'deferred', deferred, issues: [], warnings: [] } : { ...row, deferred }
  }) : []
  for (const row of rows) {
    if (row.deferred) continue
    issues.push(...row.issues)
    warnings.push(...row.warnings)
  }
  for (const id of ['h5-domain', 'android-cn', 'harmony-cn', 'ios-appstore', 'google-play']) {
    if (!rows.some((row) => row.id === id)) issues.push(`${configPath} 缺少 ${id} 记录`)
  }
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
    passed: issues.length === 0 && warnings.length === 0 && activeRows.length > 0 && summary.ready === activeRows.length,
    releaseScope: {
      configPath: 'configs/release/current-release-scope.json',
      currentBatch: releaseScope.currentBatch || '',
      activePlatforms,
      deferredPlatforms: [...deferredPlatforms],
    },
    summary,
    records: rows,
    issues,
    warnings,
  }
  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  writeFileSync(join(outDir, 'README.md'), [
    '# APP 备案与不适用说明检查',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 配置：\`${configPath}\``,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    `汇总：READY ${summary.ready} / PARTIAL ${summary.partial} / MISSING ${summary.missing} / DEFERRED ${summary.deferred}`,
    '',
    '| 记录 | 平台 | 目标 | 包名/Bundle ID | 状态 | Readiness | 负责人 |',
    '| --- | --- | --- | --- | --- | --- | --- |',
    ...rows.map((row) => `| ${row.id} | ${row.platform} | ${row.target} | ${row.packageOrBundleId || '-'} | ${row.status} | ${row.readiness} | ${row.ownerAlias || '-'} |`),
    ...(summary.deferred ? ['', '延期平台本轮不作为阻塞：', ...rows.filter((row) => row.deferred).map((row) => `- \`${row.id}\` ${row.platform}`)] : []),
    '',
    '## 问题',
    '',
    ...(issues.length ? issues.map((issue) => `- ${issue}`) : ['- 无结构性问题。']),
    '',
    '## 警告',
    '',
    ...(warnings.length ? warnings.map((warning) => `- ${warning}`) : ['- 无警告。']),
    '',
    '## 下一步',
    '',
    ...rows.map((row) => `- ${row.id}：${row.nextAction || '待补下一步。'}`),
    '',
    '## 放行规则',
    '',
    '- 当前批次国内安卓渠道按包名、开发者账号和商店后台要求追踪 APP 备案、软著或不适用说明；鸿蒙延期时不作为本轮阻塞。',
    '- H5 域名 ICP 与 HTTPS 继续由 `npm run domain:https` 追踪。',
    '- 本台账禁止保存账号密码、token、证书、密钥、验证码和个人隐私数据。',
    '',
  ].join('\n'))
  console.log(JSON.stringify({ outDir: rel(outDir), passed: report.passed, summary, issues: issues.length, warnings: warnings.length }, null, 2))
  if (strict && !report.passed) process.exit(1)
}

main()
