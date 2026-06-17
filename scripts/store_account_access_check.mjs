#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.STORE_ACCOUNT_ACCESS_STRICT === '1'
const configPath = process.env.STORE_ACCOUNT_ACCESS_CONFIG || 'configs/release/store-account-access.json'
const packageJson = readJson('package.json') || {}
const version = process.env.STORE_ACCOUNT_ACCESS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.STORE_ACCOUNT_ACCESS_OUT_DIR || join(root, 'artifacts', 'store-account-access', `${localTimestamp()}-${version}`)
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const activePlatforms = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms.filter((id) => !deferredPlatforms.has(id))
  : ['h5', 'android', 'ios', 'harmony', 'macos', 'windows'].filter((id) => !deferredPlatforms.has(id))

const requiredAccounts = [
  'dcloud',
  'apple-developer',
  'google-play',
  'huawei-appgallery',
  'yingyongbao',
  'xiaomi',
  'oppo',
  'vivo',
  'github-releases',
]
const readyStatuses = new Set(['ready'])
const allowedStatuses = new Set(['not-ready', 'pending', 'ready', 'blocked', 'not-required'])
const secretPatterns = [
  /password/i,
  /passwd/i,
  /secret/i,
  /token/i,
  /api[_-]?key/i,
  /验证码/,
  /密码/,
  /密钥/,
  /口令/,
  /access[_-]?key/i,
  /private[-_]?key/i,
  /\.p12/i,
  /\.pem/i,
  /\.key/i,
  /\.mobileprovision/i,
  /\b1[3-9]\d{9}\b/,
  /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i,
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
  return secretPatterns.some((pattern) => pattern.test(JSON.stringify(value || '')))
}

function validateAccount(account) {
  const issues = []
  const warnings = []
  if (!account.id) issues.push('账号台账缺少 id')
  if (!account.name) issues.push(`${account.id || 'unknown'} 缺少 name`)
  if (!account.platform) issues.push(`${account.id || 'unknown'} 缺少 platform`)
  if (!account.consoleUrl) issues.push(`${account.id || 'unknown'} 缺少 consoleUrl`)
  if (!allowedStatuses.has(account.accessStatus)) issues.push(`${account.id} accessStatus 非法: ${account.accessStatus}`)
  if (!allowedStatuses.has(account.twoFactorStatus)) issues.push(`${account.id} twoFactorStatus 非法: ${account.twoFactorStatus}`)
  if (!allowedStatuses.has(account.organizationStatus)) issues.push(`${account.id} organizationStatus 非法: ${account.organizationStatus}`)
  if (!allowedStatuses.has(account.signingCapabilityStatus)) issues.push(`${account.id} signingCapabilityStatus 非法: ${account.signingCapabilityStatus}`)
  if (hasSecretText(account)) issues.push(`${account.id} 可能包含手机号、邮箱、密码、验证码、token 或证书私钥`)
  if (!account.ownerAlias) issues.push(`${account.id} 缺少 ownerAlias，需填负责人别名但不要填手机号/邮箱`)
  if (!Array.isArray(account.requiredFor) || account.requiredFor.length === 0) issues.push(`${account.id} 缺少 requiredFor`)
  if (!account.nextAction) warnings.push(`${account.id} 缺少 nextAction`)

  const evidencePaths = Array.isArray(account.evidencePaths) ? account.evidencePaths : []
  for (const evidencePath of evidencePaths) {
    if (!pathExists(evidencePath)) warnings.push(`${account.id} evidencePaths 不存在: ${evidencePath}`)
    if (hasSecretText(evidencePath)) issues.push(`${account.id} evidencePath 疑似敏感: ${evidencePath}`)
  }

  const ready = readyStatuses.has(account.accessStatus) &&
    readyStatuses.has(account.twoFactorStatus) &&
    ['ready', 'not-required'].includes(account.organizationStatus) &&
    ['ready', 'not-required'].includes(account.signingCapabilityStatus) &&
    Boolean(account.ownerAlias) &&
    evidencePaths.length > 0

  return {
    id: account.id,
    name: account.name,
    platform: account.platform,
    readiness: ready ? 'ready' : (account.accessStatus === 'not-ready' ? 'missing' : 'partial'),
    accessStatus: account.accessStatus,
    twoFactorStatus: account.twoFactorStatus,
    organizationStatus: account.organizationStatus,
    signingCapabilityStatus: account.signingCapabilityStatus,
    ownerAlias: account.ownerAlias || '',
    evidenceCount: evidencePaths.length,
    nextAction: account.nextAction || '',
    issues,
    warnings,
  }
}

function platformIds(account) {
  const ids = new Set()
  const platform = String(account?.platform || '').toLowerCase()
  const text = JSON.stringify({
    id: account?.id || '',
    name: account?.name || '',
    requiredFor: account?.requiredFor || [],
  }).toLowerCase()
  if (platform.includes('android') || text.includes('android') || text.includes('apk') || text.includes('aab')) ids.add('android')
  if (platform.includes('ios') || text.includes('ios') || text.includes('testflight') || text.includes('app store')) ids.add('ios')
  if (platform.includes('harmony') || text.includes('鸿蒙')) ids.add('harmony')
  if (platform.includes('desktop') || text.includes('macos') || text.includes('developer id') || text.includes('dmg')) ids.add('macos')
  if (platform.includes('desktop') || text.includes('windows') || text.includes('exe') || text.includes('msi')) ids.add('windows')
  if (platform.includes('mobile-build')) {
    ids.add('android')
    ids.add('ios')
  }
  if (text.includes('华为应用市场')) ids.add('android')
  return [...ids]
}

function isDeferred(account) {
  const ids = platformIds(account)
  return ids.length > 0 && !ids.some((id) => activePlatforms.includes(id)) && ids.some((id) => deferredPlatforms.has(id))
}

function main() {
  const config = readJson(configPath)
  const issues = []
  const warnings = []
  if (!config) issues.push(`缺少或无法解析 ${configPath}`)
  if (config && hasSecretText({ ...config, accounts: undefined, policy: undefined })) {
    issues.push(`${configPath} 顶层字段可能包含手机号、邮箱、密码、验证码、token 或证书私钥`)
  }
  if (!Array.isArray(config?.accounts)) issues.push(`${configPath} 缺少 accounts 数组`)
  const rows = Array.isArray(config?.accounts) ? config.accounts.map((account) => {
    const row = validateAccount(account)
    const deferred = isDeferred(account)
    return deferred ? { ...row, readiness: 'deferred', deferred, issues: [], warnings: [] } : { ...row, deferred }
  }) : []
  for (const row of rows) {
    if (row.deferred) continue
    issues.push(...row.issues)
    warnings.push(...row.warnings)
  }
  const ids = new Set(rows.map((row) => row.id))
  for (const id of requiredAccounts) {
    if (!ids.has(id)) issues.push(`${configPath} 缺少账号台账: ${id}`)
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
    accounts: rows,
    issues,
    warnings,
  }

  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

  const md = [
    '# 开发者账号与后台访问检查',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 配置：\`${configPath}\``,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    `汇总：READY ${summary.ready} / PARTIAL ${summary.partial} / MISSING ${summary.missing} / DEFERRED ${summary.deferred}`,
    '',
    '| 账号 | 平台 | Readiness | 访问 | 2FA | 资质 | 签名能力 | 负责人 | 证据数 |',
    '| --- | --- | --- | --- | --- | --- | --- | --- | ---: |',
    ...rows.map((row) => `| ${row.name || row.id} | ${row.platform || '-'} | ${row.readiness} | ${row.accessStatus || '-'} | ${row.twoFactorStatus || '-'} | ${row.organizationStatus || '-'} | ${row.signingCapabilityStatus || '-'} | ${row.ownerAlias || '-'} | ${row.evidenceCount} |`),
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
    '## 下一步',
    '',
    ...rows.map((row) => `- ${row.name || row.id}：${row.nextAction || '待补下一步。'}`),
    '',
    '## 放行规则',
    '',
    '- 非 strict 模式只生成台账报告，不因为账号未开通而失败。',
    '- 正式上架候选前运行 `npm run store:account-access -- --strict`；所有开发者账号、2FA、组织资质、签名能力和非敏感证据必须 ready。',
    '- 本台账禁止记录手机号、邮箱、审核账号密码、验证码、token、证书、签名密钥和后台密钥。',
    '',
  ].join('\n')
  writeFileSync(join(outDir, 'README.md'), md)
  console.log(JSON.stringify({
    outDir: rel(outDir),
    passed: report.passed,
    summary,
    issues: issues.length,
    warnings: warnings.length,
  }, null, 2))
  if (strict && !report.passed) process.exit(1)
}

main()
