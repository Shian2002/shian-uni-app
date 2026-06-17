#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { extname, join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.STORE_EVIDENCE_STATUS_STRICT === '1'
const configPath = process.env.STORE_EVIDENCE_STATUS_CONFIG || 'configs/release/store-evidence-requirements.json'
const packageJson = readJson('package.json') || {}
const version = process.env.STORE_EVIDENCE_STATUS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.STORE_EVIDENCE_STATUS_OUT_DIR || join(root, 'artifacts', 'store-evidence-status', `${localTimestamp()}-${version}`)
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const activePlatforms = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms.filter((id) => !deferredPlatforms.has(id))
  : ['h5', 'android', 'ios', 'harmony', 'macos', 'windows'].filter((id) => !deferredPlatforms.has(id))

const allowedIds = new Set([
  'yingyongbao',
  'huawei',
  'xiaomi',
  'oppo',
  'vivo',
  'google-play',
  'appstore',
  'harmony',
  'github-desktop',
])
const evidenceExts = new Set(['.png', '.jpg', '.jpeg', '.webp', '.pdf', '.json', '.md', '.txt', '.sha256'])
const knownEvidenceIds = new Set([
  'submit-status-json',
  'privacy-url-screenshot',
  'permissions-screenshot',
  'app-record-screenshot',
  'account-deletion-device-screenshot',
  'phone-store-screenshots',
  'data-safety-screenshot',
  'testing-track-screenshot',
  'account-deletion-console-screenshot',
  'tablet-store-screenshots',
  'app-privacy-screenshot',
  'testflight-build-screenshot',
  'iphone-store-screenshots',
  'ipad-store-screenshots',
  'harmony-package-screenshot',
  'release-draft-json',
  'desktop-release-page-screenshot',
  'macos-install-screenshots',
  'windows-install-screenshots',
  'desktop-checksums',
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
  /\.pem/i,
  /\.key/i,
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
  return secretPatterns.some((pattern) => pattern.test(JSON.stringify(value || '')))
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function walk(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return []
  const entries = []
  for (const name of readdirSync(fullPath)) {
    const item = join(fullPath, name)
    const stat = statSync(item)
    if (stat.isDirectory()) entries.push(...walk(rel(item)))
    else entries.push({ path: rel(item), bytes: stat.size, ext: extname(name).toLowerCase() })
  }
  return entries
}

function expectedPath(inboxRoot, storeId, evidenceId) {
  return `${inboxRoot}/${storeId}/${evidenceId}`
}

function evidenceFiles(inboxRoot, storeId, evidenceId) {
  return walk(expectedPath(inboxRoot, storeId, evidenceId))
    .filter((item) => evidenceExts.has(item.ext))
    .map((item) => ({
      ...item,
      sha256: sha256(join(root, item.path)),
    }))
}

function validateStore(store, inboxRoot) {
  const issues = []
  const warnings = []
  if (!allowedIds.has(store.id)) issues.push(`未知商店证据台账: ${store.id || 'missing-id'}`)
  if (!store.name) issues.push(`${store.id || 'unknown'} 缺少 name`)
  if (!store.platform) issues.push(`${store.id || 'unknown'} 缺少 platform`)
  if (!Array.isArray(store.requiredEvidence) || store.requiredEvidence.length === 0) {
    issues.push(`${store.id || 'unknown'} 缺少 requiredEvidence`)
  }
  if (hasSecretText(store)) issues.push(`${store.id || 'unknown'} 可能包含账号密码、证书、密钥或验证码敏感信息`)

  const evidence = (store.requiredEvidence || []).map((id) => {
    if (!knownEvidenceIds.has(id)) issues.push(`${store.id} 未知证据项: ${id}`)
    const dir = expectedPath(inboxRoot, store.id, id)
    const files = evidenceFiles(inboxRoot, store.id, id)
    if (!pathExists(dir) || files.length === 0) issues.push(`${store.id} 缺少证据: ${id} -> ${dir}`)
    for (const file of files) {
      if (secretPatterns.some((pattern) => pattern.test(file.path))) {
        issues.push(`${store.id} 证据路径疑似包含敏感文件: ${file.path}`)
      }
    }
    return { id, dir, files }
  })

  const fileCount = evidence.reduce((total, item) => total + item.files.length, 0)
  const readiness = issues.length === 0 ? 'ready' : (fileCount > 0 ? 'partial' : 'missing')
  return {
    id: store.id,
    name: store.name,
    platform: store.platform,
    readiness,
    requiredEvidenceCount: evidence.length,
    readyEvidenceCount: evidence.filter((item) => item.files.length > 0).length,
    fileCount,
    evidence,
    issues,
    warnings,
  }
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
  if (config && hasSecretText({ ...config, stores: undefined, policy: undefined })) {
    issues.push(`${configPath} 顶层字段可能包含账号密码、证书、密钥或验证码敏感信息`)
  }
  if (!Array.isArray(config?.stores)) issues.push(`${configPath} 缺少 stores 数组`)
  const inboxRoot = config?.inboxRoot || 'artifacts/store-evidence-inbox/v1.0.0'

  const rows = Array.isArray(config?.stores) ? config.stores.map((store) => {
    const row = validateStore(store, inboxRoot)
    const deferred = isDeferred(store)
    return deferred ? { ...row, readiness: 'deferred', deferred, issues: [], warnings: [] } : { ...row, deferred }
  }) : []
  for (const row of rows) {
    if (row.deferred) continue
    issues.push(...row.issues)
    warnings.push(...row.warnings)
  }
  const ids = new Set(rows.map((row) => row.id))
  for (const id of allowedIds) {
    if (!ids.has(id)) issues.push(`${configPath} 缺少商店证据台账: ${id}`)
  }

  const activeRows = rows.filter((row) => !row.deferred)
  const summary = {
    ready: activeRows.filter((row) => row.readiness === 'ready').length,
    partial: activeRows.filter((row) => row.readiness === 'partial').length,
    missing: activeRows.filter((row) => row.readiness === 'missing').length,
    deferred: rows.filter((row) => row.readiness === 'deferred').length,
    evidenceFiles: activeRows.reduce((total, row) => total + row.fileCount, 0),
  }
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    configPath,
    inboxRoot,
    passed: issues.length === 0 && activeRows.length > 0 && summary.ready === activeRows.length,
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
    '# 商店后台证据收件检查',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 配置：\`${configPath}\``,
    `> 收件目录：\`${inboxRoot}\``,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    `汇总：READY ${summary.ready} / PARTIAL ${summary.partial} / MISSING ${summary.missing} / DEFERRED ${summary.deferred} / FILES ${summary.evidenceFiles}`,
    '',
    '| 商店 | 平台 | Readiness | 证据项 | 文件数 |',
    '| --- | --- | --- | ---: | ---: |',
    ...rows.map((row) => `| ${row.name || row.id} | ${row.platform || '-'} | ${row.readiness} | ${row.readyEvidenceCount}/${row.requiredEvidenceCount} | ${row.fileCount} |`),
    ...(summary.deferred ? ['', '延期平台本轮不作为阻塞：', ...rows.filter((row) => row.deferred).map((row) => `- \`${row.id}\` ${row.name}`)] : []),
    '',
    '## 回传目录',
    '',
    ...rows.flatMap((row) => row.evidence.map((item) => `- \`${item.dir}/\`：${item.files.length ? `${item.files.length} 个文件` : '缺失'}`)),
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
    '- 非 strict 模式只生成报告，不因为后台截图尚未回传而失败。',
    '- 正式商店候选前运行 `npm run store:evidence-status -- --strict`；所有商店证据项必须有真实回传文件。',
    '- 本台账禁止记录审核账号密码、验证码、证书、签名密钥、后台 token 和用户隐私原始数据。',
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
