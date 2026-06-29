#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { basename, join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.H5_LEGAL_DEPLOY_STRICT === '1'
const packageJson = readJson('package.json') || {}
const version = process.env.H5_LEGAL_DEPLOY_VERSION || `v${packageJson.version || '0.0.0'}`
const legalUrls = readJson('configs/release/legal-urls.json') || {}
const domainConfig = readJson('configs/release/domain-https.json') || {}
const baseUrl = process.env.H5_LEGAL_DEPLOY_BASE_URL || legalUrls.productionBaseUrl || 'https://shianjieyouwu.com'
const outDir = process.env.H5_LEGAL_DEPLOY_OUT_DIR || join(root, 'artifacts', 'h5-legal-deploy-status', `${localTimestamp()}-${version}`)
const requiredTexts = {
  privacy: ['隐私政策', '账号注销', '数据删除', '第三方服务', '联系我们'],
  terms: ['用户协议', '不构成医疗、法律、金融', '积分与付费', '知识产权', '账号注销'],
}
const icpRecordHint = '粤ICP备'
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

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function findLocalLegalChunk() {
  const assetDir = join(root, 'dist/build/h5/assets')
  if (!existsSync(assetDir)) return null
  const files = readdirSync(assetDir)
    .filter((name) => /^pages-legal-index\..+\.js$/.test(name))
    .map((name) => join(assetDir, name))
    .filter((path) => statSync(path).isFile())
    .sort((a, b) => basename(a).localeCompare(basename(b)))
  if (!files.length) return null
  const path = files[0]
  const text = readFileSync(path, 'utf8')
  return {
    path: rel(path),
    filename: basename(path),
    bytes: statSync(path).size,
    sha256: sha256(path),
    missingText: allRequiredTexts().filter((item) => !text.includes(item)),
  }
}

function allRequiredTexts() {
  return [...new Set([...requiredTexts.privacy, ...requiredTexts.terms])]
}

async function fetchEntryAndAssets(targetBaseUrl) {
  const normalizedBase = targetBaseUrl.replace(/\/$/, '')
  const entryUrl = `${normalizedBase}/`
  const response = await fetch(entryUrl, { redirect: 'follow' })
  const html = await response.text()
  const assetCorpus = await fetchSameOriginAssets(entryUrl, html)
  return {
    entryUrl,
    status: response.status,
    ok: response.ok,
    html,
    checkedAssets: assetCorpus.count,
    assetUrls: assetCorpus.urls,
    text: `${html}\n${assetCorpus.text}`,
  }
}

async function fetchSameOriginAssets(pageUrl, html) {
  const origin = new URL(pageUrl).origin
  const queue = extractAssetUrls(pageUrl, html)
  const seen = new Set()
  const urls = []
  const texts = []
  while (queue.length && seen.size < 100) {
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
    urls.push(parsed.href)
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
  return { count: seen.size, urls, text: texts.join('\n') }
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

function icpRecordNumber() {
  const h5 = (domainConfig.domains || []).find((item) => item.id === 'h5-production')
  return h5?.icpRecordNumber || ''
}

async function main() {
  const issues = []
  const warnings = []
  const localLegalChunk = findLocalLegalChunk()
  if (!localLegalChunk) issues.push('本地 dist/build/h5/assets 缺少 pages-legal-index.*.js，请先运行 npm run build:h5')
  else if (localLegalChunk.missingText.length) {
    issues.push(`本地法律页 chunk 缺少审核关键字: ${localLegalChunk.missingText.join(', ')}`)
  }

  let online = {
    baseUrl,
    entryUrl: '',
    status: 0,
    ok: false,
    checkedAssets: 0,
    deployedLegalPage: false,
    deployedIcpFooter: false,
    missingText: allRequiredTexts(),
    legalAssetUrls: [],
    error: '',
  }

  try {
    const deployed = await fetchEntryAndAssets(baseUrl)
    const required = allRequiredTexts()
    const missingText = required.filter((item) => !deployed.text.includes(item))
    const icp = icpRecordNumber()
    const legalAssetUrls = deployed.assetUrls.filter((url) => /pages-legal-index/i.test(url))
    online = {
      baseUrl,
      entryUrl: deployed.entryUrl,
      status: deployed.status,
      ok: deployed.ok,
      checkedAssets: deployed.checkedAssets,
      deployedLegalPage: deployed.ok && missingText.length === 0,
      deployedIcpFooter: Boolean(icp) && deployed.text.includes(icp),
      missingText,
      legalAssetUrls,
      error: deployed.ok ? '' : `HTTP ${deployed.status}`,
    }
  } catch (error) {
    online.error = error.message
  }

  if (!online.ok) issues.push(`线上 H5 入口不可访问: ${online.error || online.status}`)
  if (!online.deployedLegalPage) issues.push(`线上 H5 未部署完整法律页正文: ${online.missingText.join(', ')}`)
  if (!online.deployedIcpFooter) warnings.push('线上 H5 入口或资产未检出 ICP 备案号；如果备案号由运行时页面渲染，部署后需补截图证据')

  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    baseUrl,
    legalUrlConfig: 'configs/release/legal-urls.json',
    domainHttpsConfig: 'configs/release/domain-https.json',
    localLegalChunk,
    online,
    passed: issues.length === 0 && warnings.length === 0,
    issues,
    warnings,
  }

  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  writeFileSync(join(outDir, 'README.md'), [
    '# H5 法律页线上部署状态',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 目标域名：${baseUrl}`,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    '## 本地产物',
    '',
    localLegalChunk
      ? `- ${localLegalChunk.path} SHA-256 ${localLegalChunk.sha256}`
      : '- 缺少本地法律页 chunk。',
    '',
    '## 线上状态',
    '',
    `- 入口：${online.entryUrl || baseUrl}`,
    `- HTTP：${online.status || '-'}`,
    `- 检查资产数：${online.checkedAssets}`,
    `- 法律页正文：${online.deployedLegalPage ? '已部署' : '未部署完整'}`,
    `- ICP 备案号：${online.deployedIcpFooter ? '已检出' : '未检出'}`,
    `- 法律页资产：${online.legalAssetUrls.length ? online.legalAssetUrls.join(', ') : '未检出'}`,
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
    '- 部署前必须先运行 `npm run build:h5`，并确认本地 `pages-legal-index.*.js` 包含隐私政策和用户协议正文。',
    `- ICP 备案号通常应包含 \`${icpRecordHint}\` 前缀；当前备案号来自 \`configs/release/domain-https.json\`。`,
    '- 网站 H5 部署后必须运行 `npm run h5:legal-deploy-status -- --strict` 和 `LEGAL_URL_CHECK_SCOPE=website LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict`。',
    '- 正式商店提交前再运行 `LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict`，通过前不得把 `configs/release/legal-urls.json` 的 `status` 改为 `ready`。',
    '',
  ].join('\n'))

  console.log(JSON.stringify({
    outDir: rel(outDir),
    passed: report.passed,
    localLegalChunk: localLegalChunk?.path || '',
    onlineLegalPage: online.deployedLegalPage,
    onlineIcpFooter: online.deployedIcpFooter,
    issues: issues.length,
    warnings: warnings.length,
  }, null, 2))
  if (strict && !report.passed) process.exit(1)
}

main()
