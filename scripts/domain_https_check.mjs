#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.DOMAIN_HTTPS_STRICT === '1'
const configPath = process.env.DOMAIN_HTTPS_CONFIG || 'configs/release/domain-https.json'
const packageJson = readJson('package.json') || {}
const version = process.env.DOMAIN_HTTPS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.DOMAIN_HTTPS_OUT_DIR || join(root, 'artifacts', 'domain-https', `${localTimestamp()}-${version}`)

const allowedStatuses = new Set(['not-ready', 'pending', 'ready', 'not-required'])
const secretPatterns = [
  /password/i,
  /passwd/i,
  /secret/i,
  /token/i,
  /api[_-]?key/i,
  /access[_-]?key/i,
  /private[-_]?key/i,
  /\.pem/i,
  /\.key/i,
  /\.p12/i,
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

function readOptionalText(path) {
  if (!pathExists(path)) return ''
  return readFileSync(join(root, path), 'utf8')
}

function hasSecretText(value) {
  return secretPatterns.some((pattern) => pattern.test(JSON.stringify(value || '')))
}

function isHttpsUrl(value) {
  return typeof value === 'string' && value.startsWith('https://')
}

function hasIpOrLocal(value) {
  return typeof value === 'string' && /119\.29\.128\.18|localhost|127\.0\.0\.1|^http:\/\//.test(value)
}

function latestLegalUrlReport() {
  const base = join(root, 'artifacts', 'legal-url-checks')
  if (!existsSync(base)) return null
  const names = readdirSync(base)
    .map((name) => ({ name, full: join(base, name), reportPath: `artifacts/legal-url-checks/${name}/report.json` }))
    .filter((entry) => statSync(entry.full).isDirectory())
    .sort((a, b) => {
      const byTime = latestReportTime(b.reportPath, b.full) - latestReportTime(a.reportPath, a.full)
      return byTime || b.name.localeCompare(a.name)
    })
  for (const entry of names) {
    const path = entry.reportPath
    const data = readJson(path)
    if (data) return { path, data }
  }
  return null
}

function latestReportTime(path, fullDir) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const parsed = raw ? Date.parse(raw) : 0
  if (Number.isFinite(parsed) && parsed > 0) return parsed
  return existsSync(fullDir) ? statSync(fullDir).mtimeMs : 0
}

function validateDomain(domain, legalUrls) {
  const issues = []
  const warnings = []
  if (!domain.id) issues.push('域名台账缺少 id')
  if (!domain.purpose) issues.push(`${domain.id || 'unknown'} 缺少 purpose`)
  if (!domain.hostname) issues.push(`${domain.id || 'unknown'} 缺少 hostname`)
  if (!domain.targetBaseUrl) issues.push(`${domain.id || 'unknown'} 缺少 targetBaseUrl`)
  if (!domain.ownerAlias) issues.push(`${domain.id || 'unknown'} 缺少 ownerAlias`)
  if (hasSecretText(domain)) issues.push(`${domain.id || 'unknown'} 可能包含 DNS 密钥、证书私钥、密码或 token`)

  for (const key of ['dnsStatus', 'httpsStatus', 'tlsCertificateStatus', 'icpStatus', 'appRecordStatus']) {
    if (!allowedStatuses.has(domain[key])) issues.push(`${domain.id || 'unknown'} ${key} 非法: ${domain[key]}`)
  }
  if (domain.dnsStatus && !['ready', 'not-required'].includes(domain.dnsStatus)) issues.push(`${domain.id} DNS 状态未 ready: ${domain.dnsStatus}`)
  if (domain.httpsStatus && !['ready', 'not-required'].includes(domain.httpsStatus)) issues.push(`${domain.id} HTTPS 状态未 ready: ${domain.httpsStatus}`)
  if (domain.tlsCertificateStatus && !['ready', 'not-required'].includes(domain.tlsCertificateStatus)) issues.push(`${domain.id} TLS 证书状态未 ready: ${domain.tlsCertificateStatus}`)
  if (domain.icpStatus && !['ready', 'not-required'].includes(domain.icpStatus)) issues.push(`${domain.id} ICP 备案状态未 ready: ${domain.icpStatus}`)
  if (domain.appRecordStatus && !['ready', 'not-required'].includes(domain.appRecordStatus)) issues.push(`${domain.id} APP 备案状态未 ready: ${domain.appRecordStatus}`)
  if (domain.appRecordStatus === 'not-required' && !domain.appRecordNotRequiredReason) {
    issues.push(`${domain.id} APP 备案状态为 not-required 但缺少 appRecordNotRequiredReason`)
  }
  if (domain.targetBaseUrl && !isHttpsUrl(domain.targetBaseUrl)) issues.push(`${domain.id} targetBaseUrl 不是 HTTPS`)
  if (hasIpOrLocal(domain.targetBaseUrl)) issues.push(`${domain.id} targetBaseUrl 仍使用 IP、本地地址或 http`)
  if (domain.currentCandidateUrl && !isHttpsUrl(domain.currentCandidateUrl)) issues.push(`${domain.id} currentCandidateUrl 不是 HTTPS`)
  if (hasIpOrLocal(domain.currentCandidateUrl)) issues.push(`${domain.id} currentCandidateUrl 仍使用 IP、本地地址或 http`)
  if (domain.privacyPolicyUrl && !isHttpsUrl(domain.privacyPolicyUrl)) issues.push(`${domain.id} privacyPolicyUrl 不是 HTTPS`)
  if (domain.userAgreementUrl && !isHttpsUrl(domain.userAgreementUrl)) issues.push(`${domain.id} userAgreementUrl 不是 HTTPS`)
  if (domain.privacyPolicyUrl && hasIpOrLocal(domain.privacyPolicyUrl)) issues.push(`${domain.id} privacyPolicyUrl 仍使用 IP、本地地址或 http`)
  if (domain.userAgreementUrl && hasIpOrLocal(domain.userAgreementUrl)) issues.push(`${domain.id} userAgreementUrl 仍使用 IP、本地地址或 http`)
  if (domain.onlineVerificationReport && !pathExists(domain.onlineVerificationReport)) {
    warnings.push(`${domain.id} onlineVerificationReport 不存在: ${domain.onlineVerificationReport}`)
  }
  if (domain.icpStatus === 'ready') {
    if (!domain.icpRecordNumber) issues.push(`${domain.id} icpStatus=ready 但缺少 icpRecordNumber`)
    const evidencePaths = Array.isArray(domain.icpEvidencePaths) ? domain.icpEvidencePaths : []
    if (evidencePaths.length === 0) issues.push(`${domain.id} icpStatus=ready 但缺少 icpEvidencePaths`)
    for (const evidencePath of evidencePaths) {
      const text = readOptionalText(evidencePath)
      if (!text) issues.push(`${domain.id} ICP 证据文件不存在: ${evidencePath}`)
      else if (domain.icpRecordNumber && !text.includes(domain.icpRecordNumber)) {
        issues.push(`${domain.id} ICP 证据文件未包含备案号: ${evidencePath}`)
      }
    }
  }

  const currentUrls = [legalUrls?.privacyPolicyUrl, legalUrls?.userAgreementUrl].filter(Boolean)
  if (domain.id === 'h5-production') {
    for (const url of currentUrls) {
      if (!isHttpsUrl(url) || hasIpOrLocal(url)) issues.push(`legal-urls 仍不是正式 HTTPS 域名: ${url}`)
    }
    if (legalUrls?.status !== 'ready') issues.push(`legal-urls status=${legalUrls?.status || 'missing'}，不是 ready`)
  }

  const ready = ['dnsStatus', 'httpsStatus', 'tlsCertificateStatus', 'icpStatus', 'appRecordStatus']
    .every((key) => ['ready', 'not-required'].includes(domain[key])) &&
    Boolean(domain.hostname) &&
    isHttpsUrl(domain.targetBaseUrl) &&
    Boolean(domain.ownerAlias) &&
    (!domain.onlineVerificationReport || pathExists(domain.onlineVerificationReport))

  return {
    id: domain.id,
    purpose: domain.purpose,
    readiness: ready && issues.length === 0 && warnings.length === 0 ? 'ready' : (domain.hostname || domain.targetBaseUrl ? 'partial' : 'missing'),
    hostname: domain.hostname || '',
    targetBaseUrl: domain.targetBaseUrl || '',
    dnsStatus: domain.dnsStatus || '',
    httpsStatus: domain.httpsStatus || '',
    tlsCertificateStatus: domain.tlsCertificateStatus || '',
    icpStatus: domain.icpStatus || '',
    icpRecordNumber: domain.icpRecordNumber || '',
    appRecordStatus: domain.appRecordStatus || '',
    appRecordNotRequiredReason: domain.appRecordNotRequiredReason || '',
    ownerAlias: domain.ownerAlias || '',
    nextAction: domain.nextAction || '',
    issues,
    warnings,
  }
}

function main() {
  const config = readJson(configPath)
  const legalUrls = readJson('configs/release/legal-urls.json')
  const legalReport = latestLegalUrlReport()
  const issues = []
  const warnings = []
  if (!config) issues.push(`缺少或无法解析 ${configPath}`)
  if (config && hasSecretText({ ...config, domains: undefined, policy: undefined })) {
    issues.push(`${configPath} 顶层字段可能包含 DNS 密钥、证书私钥、密码或 token`)
  }
  if (!Array.isArray(config?.domains)) issues.push(`${configPath} 缺少 domains 数组`)
  const rows = Array.isArray(config?.domains) ? config.domains.map((domain) => validateDomain(domain, legalUrls || {})) : []
  for (const row of rows) {
    issues.push(...row.issues)
    warnings.push(...row.warnings)
  }
  if (!rows.some((row) => row.id === 'h5-production')) issues.push(`${configPath} 缺少 h5-production 域名台账`)
  if (!rows.some((row) => row.id === 'api-production')) issues.push(`${configPath} 缺少 api-production 域名台账`)
  if (!legalUrls) issues.push('缺少 configs/release/legal-urls.json')
  if (!legalReport) warnings.push('缺少 store:legal-urls 报告')
  else if (legalReport.data?.passed !== true) warnings.push('最新 store:legal-urls 报告未通过')

  const summary = {
    ready: rows.filter((row) => row.readiness === 'ready').length,
    partial: rows.filter((row) => row.readiness === 'partial').length,
    missing: rows.filter((row) => row.readiness === 'missing').length,
  }
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    configPath,
    legalUrlConfig: 'configs/release/legal-urls.json',
    latestLegalUrlReport: legalReport?.path || '',
    passed: issues.length === 0 && warnings.length === 0 && rows.length > 0 && summary.ready === rows.length,
    summary,
    domains: rows,
    issues,
    warnings,
  }

  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  const md = [
    '# 域名 HTTPS 与备案检查',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 配置：\`${configPath}\``,
    `> 法律 URL：\`${report.legalUrlConfig}\``,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    `汇总：READY ${summary.ready} / PARTIAL ${summary.partial} / MISSING ${summary.missing}`,
    '',
    '| 域名项 | Readiness | Hostname | Target | DNS | HTTPS | TLS | ICP | APP备案 | 负责人 |',
    '| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |',
    ...rows.map((row) => `| ${row.purpose || row.id} | ${row.readiness} | ${row.hostname || '-'} | ${row.targetBaseUrl || '-'} | ${row.dnsStatus || '-'} | ${row.httpsStatus || '-'} | ${row.tlsCertificateStatus || '-'} | ${row.icpStatus || '-'} | ${row.appRecordStatus || '-'} | ${row.ownerAlias || '-'} |`),
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
    ...rows.map((row) => `- ${row.purpose || row.id}：${row.nextAction || '待补下一步。'}`),
    '',
    '## 放行规则',
    '',
    '- 非 strict 模式只生成报告，不因为域名/备案尚未完成而失败。',
    '- 正式商店候选前运行 `npm run domain:https -- --strict`；H5/API 域名、DNS、HTTPS、TLS、ICP 和线上法律 URL 验证必须 ready。',
    '- 移动端 APP 备案按包名、开发者账号和商店材料台账追踪；域名项如标记 not-required，必须填写 `appRecordNotRequiredReason`。',
    '- 线上法律 URL 必须使用 `LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict` 生成通过报告后再改为 ready。',
    '- 本台账禁止记录 DNS provider 密钥、证书私钥、token、密码和验证码。',
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
