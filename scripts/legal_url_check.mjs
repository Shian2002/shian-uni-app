#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.LEGAL_URL_CHECK_STRICT === '1'
const online = process.argv.includes('--online') || process.env.LEGAL_URL_CHECK_ONLINE === '1'
const scopeArg = process.argv.find((arg) => arg.startsWith('--scope='))
const scope = process.env.LEGAL_URL_CHECK_SCOPE || (scopeArg ? scopeArg.split('=').slice(1).join('=') : 'store')
const packageJson = readJson('package.json') || {}
const version = process.env.LEGAL_URL_CHECK_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.LEGAL_URL_CHECK_DIR || join(root, 'artifacts', 'legal-url-checks', `${localTimestamp()}-${version}`)

const requiredTexts = {
  privacy: ['隐私政策', '账号注销', '数据删除', '第三方服务', '联系我们'],
  terms: ['用户协议', '不构成医疗、法律、金融', '积分与付费', '知识产权', '账号注销'],
}
const assetPattern = /(?:src|href)=["']([^"']+\.(?:js|css))["']|["'](\.\/[^"']+\.(?:js|css))["']|["'](\/assets\/[^"']+\.(?:js|css))["']/g

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

function readText(path) {
  const fullPath = join(root, path)
  return existsSync(fullPath) ? readFileSync(fullPath, 'utf8') : ''
}

function isWebsiteScope() {
  return scope === 'website' || scope === 'h5'
}

function localChecks(legalUrls) {
  const page = readText('src/pages/legal/index.vue')
  const pagesJson = readText('src/pages.json')
  const privacyDoc = readText('docs/legal/privacy-policy.md')
  const termsDoc = readText('docs/legal/user-agreement.md')
  const h5IndexExists = existsSync(join(root, 'dist/build/h5/index.html'))
  const issues = []
  const warnings = []

  if (!legalUrls) issues.push('缺少 configs/release/legal-urls.json 或 JSON 不合法')
  if (!legalUrls?.privacyPolicyUrl) issues.push('缺少 privacyPolicyUrl')
  if (!legalUrls?.userAgreementUrl) issues.push('缺少 userAgreementUrl')
  if (!pagesJson.includes('pages/legal/index')) issues.push('src/pages.json 缺少 pages/legal/index 路由')
  if (!page.includes('onLoad') || !page.includes("switchDoc('privacy')") || !page.includes("switchDoc('terms')") || !page.includes('query?.type')) {
    issues.push('法律页面缺少 type=privacy/type=terms 路由处理')
  }
  for (const text of requiredTexts.privacy) {
    if (!page.includes(text) && !privacyDoc.includes(text)) issues.push(`隐私政策缺少关键内容: ${text}`)
  }
  for (const text of requiredTexts.terms) {
    if (!page.includes(text) && !termsDoc.includes(text)) issues.push(`用户协议缺少关键内容: ${text}`)
  }
  if (!h5IndexExists) warnings.push('缺少 dist/build/h5/index.html；部署前需要重新 npm run build:h5')

  for (const [label, url] of [['privacyPolicyUrl', legalUrls?.privacyPolicyUrl], ['userAgreementUrl', legalUrls?.userAgreementUrl]]) {
    if (!url) continue
    if (!url.includes('/#/pages/legal/index?type=')) issues.push(`${label} 未指向 /#/pages/legal/index?type=...`)
    if (!url.startsWith('https://')) warnings.push(`${label} 不是 HTTPS，正式商店提交前不能标记 ready`)
    if (/119\.29\.128\.18|localhost|127\.0\.0\.1/.test(url)) warnings.push(`${label} 使用 IP 或本地地址，只能作为候选 URL`)
  }
  if (!isWebsiteScope() && legalUrls?.status !== 'ready') {
    warnings.push(`legal-urls status=${legalUrls?.status || 'missing'}，线上验证通过后才能改为 ready`)
  }

  return { issues, warnings, h5IndexExists }
}

async function onlineChecks(legalUrls) {
  const results = []
  for (const [id, url] of [['privacy', legalUrls?.privacyPolicyUrl], ['terms', legalUrls?.userAgreementUrl]]) {
    const result = { id, url, passed: false, status: 0, missingText: [], checkedAssets: 0, checkMode: 'html-and-assets', error: '' }
    if (!url) {
      result.error = 'URL 缺失'
      results.push(result)
      continue
    }
    try {
      const response = await fetch(url, { redirect: 'follow' })
      result.status = response.status
      const body = await response.text()
      const assetCorpus = await fetchSameOriginAssets(url, body)
      result.checkedAssets = assetCorpus.count
      const searchableBody = `${body}\n${assetCorpus.text}`
      result.missingText = requiredTexts[id].filter((text) => !searchableBody.includes(text))
      result.passed = response.ok && result.missingText.length === 0
      if (!response.ok) result.error = `HTTP ${response.status}`
    } catch (error) {
      result.error = error.message
    }
    results.push(result)
  }
  return results
}

async function fetchSameOriginAssets(pageUrl, html) {
  const origin = new URL(pageUrl).origin
  const queue = extractAssetUrls(pageUrl, html)
  const seen = new Set()
  const texts = []

  while (queue.length && seen.size < 80) {
    const assetUrl = queue.shift()
    if (!assetUrl || seen.has(assetUrl)) continue
    seen.add(assetUrl)
    let parsed
    try {
      parsed = new URL(assetUrl)
    } catch (_) {
      continue
    }
    if (parsed.origin !== origin) continue
    try {
      const response = await fetch(parsed.href, { redirect: 'follow' })
      if (!response.ok) continue
      const text = await response.text()
      texts.push(text)
      for (const nested of extractAssetUrls(parsed.href, text)) {
        if (!seen.has(nested)) queue.push(nested)
      }
    } catch (_) {}
  }

  return {
    count: seen.size,
    text: texts.join('\n'),
  }
}

function extractAssetUrls(baseUrl, text) {
  const urls = []
  for (const match of text.matchAll(assetPattern)) {
    const raw = match[1] || match[2] || match[3]
    if (!raw) continue
    try {
      urls.push(new URL(raw, baseUrl).href)
    } catch (_) {}
  }
  return [...new Set(urls)]
}

function writeReport(report) {
  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  writeFileSync(join(outDir, 'README.md'), [
    `# ${version} 法律 URL 验证报告`,
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 模式：${report.online ? 'online' : 'local-static'}`,
    `> 范围：${report.scope === 'website' ? 'website' : 'store'}`,
    `> 结论：${report.passed ? 'ready' : 'not-ready'}`,
    '',
    '## URL',
    '',
    `- 隐私政策：${report.legalUrls?.privacyPolicyUrl || '缺失'}`,
    `- 用户协议：${report.legalUrls?.userAgreementUrl || '缺失'}`,
    `- 状态：${report.legalUrls?.status || 'missing'}`,
    '',
    '## 本地检查',
    '',
    ...(report.local.issues.length ? report.local.issues.map((item) => `- 缺口：${item}`) : ['- 缺口：无']),
    ...(report.local.warnings.length ? report.local.warnings.map((item) => `- 待处理：${item}`) : ['- 待处理：无']),
    '',
    '## 线上检查',
    '',
    report.online
      ? report.onlineResults.map((item) => `- ${item.id}: ${item.passed ? '通过' : '未通过'} status=${item.status || '-'} assets=${item.checkedAssets || 0} missing=${item.missingText.join(',') || '-'} error=${item.error || '-'}`).join('\n')
      : '- 未执行。需要线上部署后运行 `LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls`。',
    '',
    '## 使用规则',
    '',
    '- 默认模式只做本地静态验证，不访问线上地址。',
    '- 网站 H5 部署使用 `LEGAL_URL_CHECK_SCOPE=website LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict`，只校验网站法律页可访问性与正文。',
    '- 正式商店提交前必须先部署 H5，再执行 `LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict`。',
    '- 线上验证、HTTPS 域名和真实商店截图都通过后，才能把 `configs/release/legal-urls.json` 的 `status` 改为 `ready`。',
  ].join('\n') + '\n')
}

async function main() {
  const legalUrls = readJson('configs/release/legal-urls.json')
  const local = localChecks(legalUrls)
  const onlineResults = online ? await onlineChecks(legalUrls || {}) : []
  const onlinePassed = !online || onlineResults.every((item) => item.passed)
  const passed = local.issues.length === 0 && local.warnings.length === 0 && onlinePassed
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    online,
    scope: isWebsiteScope() ? 'website' : 'store',
    passed,
    legalUrls,
    local,
    onlineResults,
    outDir: rel(outDir),
  }
  writeReport(report)
  console.log(JSON.stringify({ outDir: report.outDir, passed: report.passed, online: report.online, scope: report.scope, issues: local.issues.length, warnings: local.warnings.length }, null, 2))
  if (strict && !passed) {
    const target = report.scope === 'website' ? '网站 H5 上线' : '正式商店提交'
    console.error(`严格模式失败：法律 URL 未达到${target}条件。`)
    process.exit(1)
  }
}

main()
