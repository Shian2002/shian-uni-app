#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.STORE_MATERIALS_STRICT === '1'
const packageJson = readJson('package.json') || {}
const version = process.env.STORE_MATERIALS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.STORE_MATERIALS_DIR || join(root, 'artifacts', 'store-materials', `${localTimestamp()}-${version}`)
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const activePlatforms = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms.filter((id) => !deferredPlatforms.has(id))
  : ['h5', 'android', 'ios', 'harmony', 'macos', 'windows'].filter((id) => !deferredPlatforms.has(id))

const requiredScreenshotIds = [
  '01-home',
  '02-login-modal',
  '03-agent-workbench',
  '04-points',
  '05-bazi-tool',
  '06-profile-delete',
]

const reviewTextRequired = [
  '审核账号',
  '线上同款登录',
  '账号注销',
  '传统文化与 AI 生成内容',
  '不替代医疗、法律、金融',
]

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

function latestReportDirWith(path, filename) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory() && exists(item.reportPath))
    .sort((a, b) => {
      const byReportTime = reportTime(b.reportPath) - reportTime(a.reportPath)
      return byReportTime || b.name.localeCompare(a.name)
    })
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function latestDir(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => b.name.localeCompare(a.name))
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function latestJsonFile(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const files = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name) }))
    .filter((item) => statSync(item.full).isFile() && item.name.endsWith('.json'))
    .sort((a, b) => b.name.localeCompare(a.name))
  return files[0] ? { path: files[0].reportPath, data: readJson(files[0].reportPath) } : null
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

function configChecks() {
  const configs = [
    ['Android 渠道配置', 'configs/release/android-channels.json', ['appName', 'packageName', 'versionName', 'versionCode', 'channels']],
    ['iOS App Store 配置', 'configs/release/ios-appstore.json', ['appName', 'bundleId', 'versionName', 'buildNumber', 'paymentPolicy', 'requiredMaterials', 'requiredChecks']],
    ['鸿蒙 AppGallery 配置', 'configs/release/harmony-appgallery.json', ['appName', 'bundleName', 'versionName', 'versionCode', 'requiredMaterials', 'requiredChecks']],
    ['桌面下载配置', 'configs/release/desktop.json', ['appName', 'appId', 'versionName', 'platforms', 'requiredChecks']],
    ['法律 URL 配置', 'configs/release/legal-urls.json', ['appName', 'privacyPolicyUrl', 'userAgreementUrl', 'requiresHttpsDomainBeforeStoreSubmit']],
  ]
  return configs.map(([name, path, keys]) => {
    const data = readJson(path)
    const missing = []
    if (!data) missing.push('配置文件缺失或不是合法 JSON')
    for (const key of keys) {
      if (!data || data[key] === undefined || data[key] === '' || (Array.isArray(data[key]) && data[key].length === 0)) {
        missing.push(`缺少 ${key}`)
      }
    }
    if (path.includes('android') && data) {
      const ids = new Set((data.channels || []).map((item) => item.id))
      for (const id of ['yingyongbao', 'huawei', 'xiaomi', 'oppo', 'vivo', 'google-play']) {
        if (!ids.has(id)) missing.push(`缺少 Android 渠道 ${id}`)
      }
    }
    return { name, path, status: missing.length ? 'partial' : 'ready', missing }
  })
}

function screenshotChecks() {
  const dir = latestReportDirWith('artifacts/store-screenshots', 'summary.json')
  const report = dir ? readJson(`${dir}/summary.json`) : null
  const captures = Array.isArray(report?.captures) ? report.captures : []
  const ids = new Set(captures.map((item) => item.id))
  const presets = new Set(captures.map((item) => item.preset))
  const missing = []
  if (!report) missing.push('缺少 store:screenshots summary.json')
  if (report && report.passed !== true) missing.push('最新可用截图报告未通过')
  for (const id of requiredScreenshotIds) {
    if (!ids.has(id)) missing.push(`缺少截图场景 ${id}`)
  }
  for (const preset of ['mobile-390', 'desktop-1440']) {
    if (!presets.has(preset)) missing.push(`缺少截图尺寸 ${preset}`)
  }
  if (!presets.has('tablet-1024')) missing.push('缺少平板截图尺寸 tablet-1024')
  return {
    status: missing.length ? 'partial' : 'ready',
    evidence: dir ? `${dir}/summary.json` : '',
    captureCount: captures.length,
    missing,
  }
}

function complianceChecks() {
  const appStoreDoc = readText('docs/release/app-store-privacy-notes.md')
  const storeChecklist = readText('docs/release/store-checklists.md')
  const profile = readText('src/pages/profile/index.vue')
  const legalPage = readText('src/pages/legal/index.vue')
  const privacyDoc = readText('docs/legal/privacy-policy.md')
  const termsDoc = readText('docs/legal/user-agreement.md')
  const paymentPolicy = readText('src/utils/releasePolicy.js')
  const privacyDisclosure = readJson('configs/release/privacy-disclosures.json')
  const privacyDisclosureReport = latestReport('artifacts/privacy-disclosures')
  const storeEvidenceStatusReport = latestReport('artifacts/store-evidence-status')
  const appRecordStatusReport = latestReport('artifacts/app-record-status')
  const missing = []
  for (const text of ['隐私政策', '用户协议', '账号注销', 'App Privacy', 'Data safety', '审核账号']) {
    if (!appStoreDoc.includes(text) && !storeChecklist.includes(text)) missing.push(`缺少合规口径：${text}`)
  }
  if (!profile.includes('/api/account/delete')) missing.push('个人中心缺少账号注销接口入口')
  if (!legalPage.includes('隐私政策') || !legalPage.includes('用户协议') || !legalPage.includes('账号注销')) {
    missing.push('缺少独立法律页面或法律页面内容不完整')
  }
  if (!privacyDoc.includes('账号注销') || !privacyDoc.includes('数据删除')) missing.push('隐私政策 Markdown 缺少账号注销/数据删除口径')
  if (!termsDoc.includes('不构成医疗、法律、金融') || !termsDoc.includes('积分与付费')) missing.push('用户协议 Markdown 缺少内容边界或付费口径')
  if (!paymentPolicy.includes('google-play') || !paymentPolicy.includes('appstore')) missing.push('缺少 App Store / Google Play 支付边界策略')
  if (!privacyDisclosure) missing.push('缺少隐私披露配置')
  if (privacyDisclosure && !privacyDisclosure.appleAppPrivacy) missing.push('缺少 Apple App Privacy 披露')
  if (privacyDisclosure && !privacyDisclosure.googlePlayDataSafety) missing.push('缺少 Google Play Data safety 披露')
  if (!privacyDisclosureReport) missing.push('缺少 store:privacy 检查报告')
  else if (privacyDisclosureReport.data?.passed !== true) missing.push('store:privacy 检查报告未通过')
  if (!storeEvidenceStatusReport) missing.push('缺少 store:evidence-status 商店后台证据检查报告')
  else if (storeEvidenceStatusReport.data?.passed !== true) missing.push('store:evidence-status 商店后台证据检查报告未通过')
  if (!appRecordStatusReport) missing.push('缺少 store:app-record APP 备案与不适用说明检查报告')
  else if (appRecordStatusReport.data?.passed !== true) missing.push('store:app-record APP 备案与不适用说明检查报告未通过')
  if (!appStoreDoc.includes('VITE_RELEASE_CHANNEL=appstore') || !appStoreDoc.includes('VITE_RELEASE_CHANNEL=google-play')) {
    missing.push('缺少审核渠道构建说明')
  }
  return {
    status: missing.length ? 'partial' : 'ready',
    evidence: [privacyDisclosureReport?.path, storeEvidenceStatusReport?.path, appRecordStatusReport?.path].filter(Boolean),
    missing,
  }
}

function reviewNotesChecks() {
  const packetDir = latestDir('artifacts/store-submission-packets')
  const paths = packetDir
    ? readdirSync(join(root, packetDir))
        .map((name) => join(packetDir, name, 'submission.json'))
        .filter(exists)
    : []
  const notes = paths.flatMap((path) => readJson(path)?.reviewNotes || [])
  const joined = notes.join('\n')
  const missing = []
  if (!paths.length) missing.push('缺少 store:packet 生成的 submission.json')
  for (const item of reviewTextRequired) {
    if (!joined.includes(item)) missing.push(`审核备注缺少：${item}`)
  }
  return { status: missing.length ? 'partial' : 'ready', evidence: packetDir, storeCount: paths.length, missing }
}

function urlChecks() {
  const legalUrls = readJson('configs/release/legal-urls.json') || {}
  const legalUrlReport = latestReport('artifacts/legal-url-checks')
  const docs = [
    'docs/release/app-store-privacy-notes.md',
    'docs/release/store-checklists.md',
    'docs/release/platform-build-handoff.md',
    'configs/release/legal-urls.json',
  ].map(readText).join('\n')
  const urls = [
    legalUrls.privacyPolicyUrl,
    legalUrls.userAgreementUrl,
    ...[...docs.matchAll(/https?:\/\/[^\s)`，。"]+/g)].map((match) => match[0]),
  ].filter(Boolean)
  const missing = []
  const warnings = []
  if (!legalUrls.privacyPolicyUrl) missing.push('缺少隐私政策 URL')
  if (!legalUrls.userAgreementUrl) missing.push('缺少用户协议 URL')
  if (legalUrls.privacyPolicyUrl && !/privacy|隐私/i.test(legalUrls.privacyPolicyUrl)) warnings.push('隐私政策 URL 路径未包含 privacy/隐私 标识')
  if (legalUrls.userAgreementUrl && !/terms|agreement|user|协议/i.test(legalUrls.userAgreementUrl)) warnings.push('用户协议 URL 路径未包含 terms/agreement/user/协议 标识')
  for (const [label, url] of [['隐私政策 URL', legalUrls.privacyPolicyUrl], ['用户协议 URL', legalUrls.userAgreementUrl]]) {
    if (url && !url.startsWith('https://')) warnings.push(`${label} 当前不是 HTTPS，正式提交商店前需要替换为备案域名 HTTPS 地址`)
    if (url && /119\.29\.128\.18|localhost|127\.0\.0\.1/.test(url)) warnings.push(`${label} 当前使用 IP 或本地地址，只能作为候选 URL`)
  }
  if (legalUrls.status === 'candidate') warnings.push('法律 URL 当前状态为 candidate，需部署验证后改为 ready')
  if (!legalUrlReport) warnings.push('缺少 store:legal-urls 验证报告')
  else if (legalUrlReport.data?.passed !== true) warnings.push('store:legal-urls 验证报告未通过')
  return {
    status: missing.length ? 'partial' : (warnings.length ? 'partial' : 'ready'),
    urls,
    warnings,
    missing,
    evidence: legalUrlReport?.path || '',
  }
}

function main() {
  mkdirSync(outDir, { recursive: true })
  const realUserAcceptance = latestJsonFile('artifacts/real-user-results')
  const sections = {
    configs: configChecks(),
    screenshots: screenshotChecks(),
    compliance: complianceChecks(),
    reviewNotes: reviewNotesChecks(),
    urls: urlChecks(),
  }

  const allMissing = [
    ...sections.configs.flatMap((item) => item.missing.map((text) => `${item.name}: ${text}`)),
    ...sections.screenshots.missing.map((text) => `截图素材: ${text}`),
    ...sections.compliance.missing.map((text) => `合规材料: ${text}`),
    ...sections.reviewNotes.missing.map((text) => `审核备注: ${text}`),
    ...sections.urls.missing.map((text) => `URL: ${text}`),
    ...sections.urls.warnings.map((text) => `URL 待替换: ${text}`),
    realUserAcceptance?.data?.passed === true ? '' : `当前批次 ${activePlatforms.join('/')} 真机商店截图仍需由真实安装包回收`,
  ].filter(Boolean)

  const evidence = [
    sections.screenshots.evidence,
    ...(Array.isArray(sections.compliance.evidence) ? sections.compliance.evidence : [sections.compliance.evidence]),
    sections.reviewNotes.evidence,
    sections.urls.evidence,
    realUserAcceptance?.path,
  ]

  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    passed: allMissing.length === 0,
    verdict: allMissing.length ? 'not-ready' : 'ready',
    releaseScope: {
      configPath: 'configs/release/current-release-scope.json',
      currentBatch: releaseScope.currentBatch || '',
      activePlatforms,
      deferredPlatforms: [...deferredPlatforms],
    },
    sections,
    evidence: evidence.filter(Boolean),
    missing: allMissing,
    outDir: rel(outDir),
  }

  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  writeFileSync(join(outDir, 'README.md'), [
    `# ${version} 商店材料完整性检查`,
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 结论：${report.verdict}`,
    '',
    '## 检查范围',
    '',
    `- 当前批次：${activePlatforms.join('、')}；延期平台：${[...deferredPlatforms].join('、') || '无'}。`,
    '- 渠道配置：Android、iOS、鸿蒙、桌面端非敏感配置；延期平台只保留配置，不作为本轮材料缺口。',
    '- 截图素材：本地商店截图候选场景和手机/平板/桌面尺寸。',
    '- 合规材料：隐私政策、用户协议、账号注销、Data safety、App Privacy、付费边界。',
    '- 审核备注：审核账号、线上同款登录、账号注销、AI 内容免责声明。',
    '',
    '## 当前缺口',
    '',
    ...(allMissing.length ? allMissing.map((item) => `- ${item}`) : ['- 暂无缺口。']),
    '',
    '## 使用规则',
    '',
    '- 默认模式只生成报告，不上传商店、不读取证书、不阻断 CI。',
    '- 正式上架候选前运行 `npm run store:materials -- --strict`；存在缺口时必须失败。',
  ].join('\n') + '\n')

  console.log(JSON.stringify({ outDir: report.outDir, verdict: report.verdict, missing: allMissing.length }, null, 2))
  if (strict && !report.passed) {
    console.error('严格模式失败：商店材料仍有缺口。')
    process.exit(1)
  }
}

main()
