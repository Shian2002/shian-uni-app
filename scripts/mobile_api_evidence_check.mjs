#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const version = process.env.MOBILE_API_EVIDENCE_VERSION || `v${readJson('package.json')?.version || '0.0.0'}`
const outDir = process.env.MOBILE_API_EVIDENCE_DIR || join(root, 'artifacts', 'mobile-api-evidence', `${localTimestamp()}-${version}`)
const indexDir = join(root, 'artifacts', 'mobile-api-evidence')
const appDir = join(root, 'dist', 'build', 'app')
const issues = []

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
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

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function fileMtime(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const stat = statSync(fullPath)
  return { path, mtimeMs: stat.mtimeMs, mtime: new Date(stat.mtimeMs).toISOString() }
}

function walk(dir) {
  if (!existsSync(dir)) return []
  const entries = []
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    const stat = statSync(full)
    if (stat.isDirectory()) entries.push(...walk(full))
    else entries.push(full)
  }
  return entries
}

function firstExisting(paths) {
  return paths.find((path) => existsSync(join(root, path))) || ''
}

function requireSnippet(label, text, snippet) {
  if (!text.includes(snippet)) issues.push(`${label} 缺少运行时代码: ${snippet}`)
}

const files = walk(appDir).filter((file) => /\.(html|js|css|json)$/i.test(file))
const bundleText = files.map((file) => readFileSync(file, 'utf8')).join('\n')
const appEntryPath = firstExisting([
  'dist/build/app/__uniappview.html',
  'dist/build/app/index.html',
  'dist/build/app/app-service.js',
])
const appEntryInfo = appEntryPath ? fileMtime(appEntryPath) : null
const sourceFreshnessInputs = [
  'src/App.vue',
  'src/main.js',
  'src/manifest.json',
  'src/pages/index/index.vue',
  'package.json',
].map(fileMtime).filter(Boolean)
const newestSource = sourceFreshnessInputs.reduce((latest, item) => (
  !latest || item.mtimeMs > latest.mtimeMs ? item : latest
), null)

if (!appEntryInfo) issues.push('缺少 dist/build/app/__uniappview.html 或 app-service.js，请先执行 npm run build:app')
if (files.length === 0) issues.push('dist/build/app 没有可检查的构建产物')
if (appEntryInfo && newestSource && appEntryInfo.mtimeMs < newestSource.mtimeMs) {
  issues.push(`dist/build/app 早于移动端关键源码，请先执行 npm run build:app：app=${appEntryInfo.mtime} source=${newestSource.path} ${newestSource.mtime}`)
}

for (const snippet of [
  'https://shianjieyouwu.com',
  'credentials',
  'include',
  'withCredentials',
  'EventSource',
  'XMLHttpRequest',
  '/api/csrf-token',
]) {
  requireSnippet('dist/build/app', bundleText, snippet)
}

mkdirSync(outDir, { recursive: true })
mkdirSync(indexDir, { recursive: true })

const manifest = {
  generatedAt: new Date().toISOString(),
  version,
  passed: issues.length === 0,
  appDir: rel(appDir),
  checkedFiles: files.map((file) => ({
    path: rel(file),
    bytes: statSync(file).size,
    sha256: sha256(file),
  })),
  requiredRuntimeEvidence: [
    'production API origin',
    'fetch credentials include',
    'uni.request withCredentials',
    'EventSource normalization',
    'XMLHttpRequest normalization',
    'CSRF token endpoint',
  ],
  freshness: {
    appEntry: appEntryInfo,
    sourceFreshnessInputs,
    newestSource,
  },
  issues,
}

writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
writeFileSync(join(indexDir, 'latest-manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
writeFileSync(join(indexDir, 'LATEST.md'), [
  '# 最新移动端 API 证据',
  '',
  `> 更新时间：${manifest.generatedAt}`,
  `> 版本：${manifest.version}`,
  `> 结果：${manifest.passed ? '通过' : '未通过'}`,
  '',
  `- 完整目录：\`${rel(outDir)}\``,
  `- manifest：\`${rel(join(outDir, 'manifest.json'))}\``,
  `- App 构建目录：\`${manifest.appDir}\``,
  '',
  '## 覆盖范围',
  '',
  '- 原生 App 运行时 `/api` 自动指向线上 API。',
  '- `fetch`、`uni.request`、`EventSource`、`XMLHttpRequest` 都纳入检查。',
  '- 这个检查证明打包输入包含后端请求能力，不替代真机登录和商店包验收。',
].join('\n') + '\n')

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: manifest.passed,
  checkedFiles: manifest.checkedFiles.length,
  issues,
}, null, 2))

if (issues.length > 0) process.exit(1)
