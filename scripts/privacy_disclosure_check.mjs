#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.PRIVACY_DISCLOSURE_STRICT === '1'
const packageJson = readJson('package.json') || {}
const version = process.env.PRIVACY_DISCLOSURE_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.PRIVACY_DISCLOSURE_DIR || join(root, 'artifacts', 'privacy-disclosures', `${localTimestamp()}-${version}`)

const requiredAppleTypes = ['contact-info', 'identifiers', 'user-content', 'sensitive-info', 'purchases', 'diagnostics']
const requiredGoogleCategories = ['Personal info', 'User content', 'Financial info', 'App activity', 'App info and performance']

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function exists(path) {
  return existsSync(join(root, path))
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

function readText(path) {
  const fullPath = join(root, path)
  return existsSync(fullPath) ? readFileSync(fullPath, 'utf8') : ''
}

function latestReport(path, filename = 'report.json') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory() && exists(item.reportPath))
    .sort((a, b) => {
      const byReportTime = reportTime(b.reportPath) - reportTime(a.reportPath)
      return byReportTime || b.name.localeCompare(a.name)
    })
  return dirs[0] ? { path: dirs[0].reportPath, data: readJson(dirs[0].reportPath) } : null
}

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function checkDisclosure(data) {
  const issues = []
  const warnings = []
  const finalWarnings = []
  if (!data) {
    issues.push('缺少 configs/release/privacy-disclosures.json 或 JSON 不合法')
    return { issues, warnings, finalWarnings }
  }

  for (const key of ['appName', 'versionName', 'status', 'humanReviewStatus', 'privacyPolicySource', 'userAgreementSource', 'legalUrlConfig']) {
    if (!data[key]) issues.push(`缺少字段: ${key}`)
  }
  if (data.dataDeletionAvailable !== true) issues.push('dataDeletionAvailable 必须为 true')
  if (!String(data.dataDeletionPath || '').includes('账号注销')) issues.push('dataDeletionPath 必须指向账号注销路径')
  if (data.encryptedInTransit !== true) issues.push('encryptedInTransit 必须为 true')
  if (data.tracking?.appleTracking !== false || data.tracking?.googleAdsOrCrossAppTracking !== false) {
    warnings.push('当前披露了追踪能力；需确认 App Store/Google Play 审核口径和实际 SDK 一致')
  }
  if (data.status !== 'ready') finalWarnings.push(`privacy-disclosures status=${data.status || 'missing'}，正式提交前需人工复核后改为 ready`)
  if (data.humanReviewStatus !== 'approved') finalWarnings.push(`humanReviewStatus=${data.humanReviewStatus || 'missing'}，正式提交前需完成法务/产品复核`)

  const appleTypes = new Set((data.appleAppPrivacy?.dataTypes || []).map((item) => item.id))
  for (const id of requiredAppleTypes) {
    if (!appleTypes.has(id)) issues.push(`Apple App Privacy 缺少数据类型: ${id}`)
  }
  for (const item of data.appleAppPrivacy?.dataTypes || []) {
    if (!item.appleLabel) issues.push(`Apple 数据类型 ${item.id || 'unknown'} 缺少 appleLabel`)
    if (!Array.isArray(item.purposes) || item.purposes.length === 0) issues.push(`Apple 数据类型 ${item.id || 'unknown'} 缺少 purposes`)
    if (item.usedForTracking !== false) warnings.push(`Apple 数据类型 ${item.id || 'unknown'} 标记为 tracking，需复核`)
  }
  if (data.appleAppPrivacy?.dataUsedToTrackUser !== false) warnings.push('Apple dataUsedToTrackUser 不是 false，需复核')

  const googleCategories = new Set((data.googlePlayDataSafety?.dataTypes || []).map((item) => item.category))
  for (const category of requiredGoogleCategories) {
    if (!googleCategories.has(category)) issues.push(`Google Data safety 缺少分类: ${category}`)
  }
  for (const item of data.googlePlayDataSafety?.dataTypes || []) {
    if (!Array.isArray(item.types) || item.types.length === 0) issues.push(`Google 分类 ${item.category || 'unknown'} 缺少 types`)
    if (!Array.isArray(item.purposes) || item.purposes.length === 0) issues.push(`Google 分类 ${item.category || 'unknown'} 缺少 purposes`)
    if (item.shared === true && (!Array.isArray(item.sharedWith) || item.sharedWith.length === 0)) {
      issues.push(`Google 分类 ${item.category || 'unknown'} 标记 shared=true 但缺少 sharedWith`)
    }
  }
  if (data.googlePlayDataSafety?.usersCanRequestDeletion !== true) issues.push('Google usersCanRequestDeletion 必须为 true')
  if (data.googlePlayDataSafety?.dataEncryptedInTransit !== true) issues.push('Google dataEncryptedInTransit 必须为 true')

  return { issues, warnings, finalWarnings }
}

function checkConsistency(data) {
  const issues = []
  const warnings = []
  const finalWarnings = []
  const privacyDoc = readText('docs/legal/privacy-policy.md')
  const termsDoc = readText('docs/legal/user-agreement.md')
  const profile = readText('src/pages/profile/index.vue')
  const paymentPolicy = readText('src/utils/releasePolicy.js')
  const legalUrls = readJson('configs/release/legal-urls.json') || {}
  const legalUrlReport = latestReport('artifacts/legal-url-checks')

  for (const text of ['账号注销', '数据删除', '第三方服务', '积分', '订单']) {
    if (!privacyDoc.includes(text)) issues.push(`隐私政策缺少披露关键字: ${text}`)
  }
  for (const text of ['不构成医疗、法律、金融', '积分与付费', '知识产权']) {
    if (!termsDoc.includes(text)) issues.push(`用户协议缺少披露关键字: ${text}`)
  }
  if (!profile.includes('/api/account/delete')) issues.push('个人中心缺少账号注销接口入口')
  if (!paymentPolicy.includes('appstore') || !paymentPolicy.includes('google-play')) {
    issues.push('支付边界策略缺少 appstore/google-play 渠道')
  }
  if (!legalUrls.privacyPolicyUrl || !legalUrls.userAgreementUrl) issues.push('法律 URL 配置缺少隐私政策或用户协议 URL')
  if (!legalUrlReport) finalWarnings.push('缺少 store:legal-urls 验证报告')
  else if (legalUrlReport.data?.passed !== true) finalWarnings.push('store:legal-urls 验证报告未通过')

  const evidenceMissing = []
  for (const name of data?.submissionEvidenceRequired || []) {
    evidenceMissing.push(name)
  }
  if (evidenceMissing.length) finalWarnings.push(`正式提交前仍需人工上传/截图证据: ${evidenceMissing.join('；')}`)

  return { issues, warnings, finalWarnings, evidence: { legalUrlCheck: legalUrlReport?.path || '' } }
}

function rows(items, type) {
  if (!items.length) return `- ${type}：无`
  return items.map((item) => `- ${type}：${item}`).join('\n')
}

function main() {
  mkdirSync(outDir, { recursive: true })
  const data = readJson('configs/release/privacy-disclosures.json')
  const disclosure = checkDisclosure(data)
  const consistency = checkConsistency(data)
  const issues = [...disclosure.issues, ...consistency.issues]
  const warnings = [...disclosure.warnings, ...consistency.warnings]
  const finalWarnings = [...disclosure.finalWarnings, ...consistency.finalWarnings]
  const localPassed = issues.length === 0 && warnings.length === 0
  const finalPassed = localPassed && finalWarnings.length === 0
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    passed: localPassed,
    localPassed,
    finalPassed,
    verdict: localPassed ? 'local-ready' : 'not-ready',
    finalVerdict: finalPassed ? 'ready-for-store-submit' : 'not-ready',
    status: data?.status || 'missing',
    humanReviewStatus: data?.humanReviewStatus || 'missing',
    issues,
    warnings,
    finalWarnings,
    evidence: consistency.evidence,
    outDir: rel(outDir),
  }
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  writeFileSync(join(outDir, 'README.md'), [
    `# ${version} 隐私披露检查`,
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 本地结构化披露：${report.verdict}`,
    `> 正式提交状态：${report.finalVerdict}`,
    `> 配置状态：${report.status}`,
    `> 人工复核：${report.humanReviewStatus}`,
    '',
    '## 本地缺口',
    '',
    rows(issues, '阻断'),
    rows(warnings, '待处理'),
    '',
    '## 正式提交前缺口',
    '',
    rows(finalWarnings, '待处理'),
    '',
    '## 证据',
    '',
    `- 法律 URL 验证：${report.evidence.legalUrlCheck ? `\`${report.evidence.legalUrlCheck}\`` : '缺失'}`,
    `- 隐私政策：\`docs/legal/privacy-policy.md\``,
    `- 用户协议：\`docs/legal/user-agreement.md\``,
    `- 披露配置：\`configs/release/privacy-disclosures.json\``,
    '',
    '## 使用规则',
    '',
    '- 默认模式只证明本地 App Privacy / Data safety 披露草案结构完整，不上传商店后台。',
    '- 正式商店候选前运行 `npm run store:privacy -- --strict`。',
    '- 严格模式通过前，不得把 App Privacy / Data safety 标记为已提交或已审核通过。',
  ].join('\n') + '\n')
  console.log(JSON.stringify({ outDir: report.outDir, verdict: report.verdict, finalVerdict: report.finalVerdict, issues: issues.length, warnings: warnings.length, finalWarnings: finalWarnings.length }, null, 2))
  if (strict && !report.finalPassed) {
    console.error('严格模式失败：隐私披露仍有缺口。')
    process.exit(1)
  }
}

main()
