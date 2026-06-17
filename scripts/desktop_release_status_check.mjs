#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { extname, join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.DESKTOP_RELEASE_STATUS_STRICT === '1'
const configPath = process.env.DESKTOP_RELEASE_STATUS_CONFIG || 'configs/release/desktop-release-status.json'
const packageJson = readJson('package.json') || {}
const version = process.env.DESKTOP_RELEASE_STATUS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.DESKTOP_RELEASE_STATUS_OUT_DIR || join(root, 'artifacts', 'desktop-release-status', `${localTimestamp()}-${version}`)

const allowedPlatformIds = new Set(['macos', 'windows'])
const readySigningStatuses = new Set(['signed', 'developer-id-signed'])
const readyNotarizationStatuses = new Set(['notarized'])
const secretPatterns = [
  /password/i,
  /passwd/i,
  /secret/i,
  /token/i,
  /api[_-]?key/i,
  /certificate/i,
  /private[-_]?key/i,
  /\.p12/i,
  /\.pem/i,
  /\.key/i,
  /mobileprovision/i,
  /证书/,
  /密钥/,
  /密码/,
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

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function latestPassingDesktopSmoke() {
  const basePath = 'artifacts/desktop-smoke'
  const fullPath = join(root, basePath)
  if (!existsSync(fullPath)) return { path: '', data: null }
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byReportTime = reportTime(join(basePath, b.name, 'report.json')) - reportTime(join(basePath, a.name, 'report.json'))
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const dir of dirs) {
    const reportPath = join(basePath, dir.name, 'report.json')
    const data = readJson(reportPath)
    if (data?.passed === true && data?.layout?.agent?.homeAiMain && data?.layout?.agent?.topnav) {
      return { path: reportPath, data }
    }
  }
  return { path: '', data: null }
}

function latestUserPacketEvidence(platformId) {
  const packetBase = {
    macos: 'artifacts/desktop-macos-user-packets',
    windows: 'artifacts/desktop-windows-user-packets',
  }[platformId]
  if (!packetBase) return []
  const fullPath = join(root, packetBase)
  if (!existsSync(fullPath)) return []
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => b.name.localeCompare(a.name))
  const latest = dirs[0]
  if (!latest) return []
  return [
    join(packetBase, latest.name, 'manifest.json'),
    join(packetBase, latest.name, 'desktop-login-modal.png'),
    join(packetBase, latest.name, 'desktop-agent-app.png'),
  ].filter(pathExists)
}

function resolveSmokeReportPath(platform) {
  if (platform.smokeReportPath === 'latest:desktop-smoke') return latestPassingDesktopSmoke().path
  return platform.smokeReportPath || ''
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function hasSecretText(value) {
  return secretPatterns.some((pattern) => pattern.test(JSON.stringify(value || '')))
}

function artifactRow(path) {
  if (!pathExists(path)) return { path, exists: false, bytes: 0, sha256: '' }
  const fullPath = join(root, path)
  return {
    path,
    exists: true,
    bytes: statSync(fullPath).size,
    sha256: sha256(fullPath),
    ext: extname(path).toLowerCase(),
  }
}

function smokePassed(platform) {
  const smokeReportPath = resolveSmokeReportPath(platform)
  if (!smokeReportPath) return platform.id === 'windows' ? null : false
  const data = readJson(smokeReportPath)
  if (!data) return false
  return data.passed === true
}

function validatePlatform(platform) {
  const issues = []
  const warnings = []
  const fatalIssues = []

  if (!allowedPlatformIds.has(platform.id)) fatalIssues.push(`未知桌面平台: ${platform.id || 'missing-id'}`)
  if (!platform.name) fatalIssues.push(`${platform.id || 'unknown'} 缺少 name`)
  if (!Array.isArray(platform.artifactPaths) || platform.artifactPaths.length === 0) {
    fatalIssues.push(`${platform.id || 'unknown'} 缺少 artifactPaths`)
  }
  if (hasSecretText(platform)) fatalIssues.push(`${platform.id || 'unknown'} 可能包含证书、密钥、密码或 token 敏感信息`)

  const artifacts = (platform.artifactPaths || []).map(artifactRow)
  const existingArtifacts = artifacts.filter((item) => item.exists)
  const requiredExts = new Set(platform.requiredArtifactExts || [])
  const hasRequiredArtifact = existingArtifacts.some((item) => requiredExts.size === 0 || requiredExts.has(item.ext))

  if (!hasRequiredArtifact) {
    fatalIssues.push(`${platform.id} 缺少可用安装包: ${(platform.requiredArtifactExts || []).join('/') || 'artifact'}`)
  }

  const configuredEvidencePaths = platform.installEvidencePaths || []
  const autoEvidencePaths = configuredEvidencePaths.length ? [] : latestUserPacketEvidence(platform.id)
  const evidencePaths = [...configuredEvidencePaths, ...autoEvidencePaths]
  const installEvidenceCount = evidencePaths.filter(pathExists).length
  const requiredInstallEvidenceCount = (platform.installEvidence || []).length
  const missingEvidence = evidencePaths.filter((path) => !pathExists(path))
  for (const path of missingEvidence) warnings.push(`${platform.id} installEvidencePaths 不存在: ${path}`)
  if (installEvidenceCount < requiredInstallEvidenceCount) {
    issues.push(`${platform.id} 安装/验收截图不足: ${installEvidenceCount}/${requiredInstallEvidenceCount}`)
  }

  const signingReady = readySigningStatuses.has(platform.codeSigningStatus)
  const notarizationReady = platform.id === 'macos' ? readyNotarizationStatuses.has(platform.notarizationStatus) : true
  if (!signingReady) issues.push(`${platform.id} 代码签名未完成: ${platform.codeSigningStatus || 'missing'}`)
  if (!notarizationReady) issues.push(`${platform.id} notarization 未完成: ${platform.notarizationStatus || 'missing'}`)

  const smokeReportPath = resolveSmokeReportPath(platform)
  const smokeReport = smokeReportPath ? readJson(smokeReportPath) : null
  const smoke = smokeReportPath ? smokeReport?.passed === true : (platform.id === 'windows' ? null : false)
  if (platform.id === 'macos' && smoke !== true) fatalIssues.push('macos 缺少通过的桌面 smoke 报告')
  if (platform.id === 'macos' && (!smokeReport?.layout?.agent?.homeAiMain || !smokeReport?.layout?.agent?.topnav)) {
    fatalIssues.push('macos 桌面 smoke 缺少浅色顶栏和底部对话框布局指标')
  }
  if (platform.id === 'windows' && smoke === false) warnings.push('windows 已配置 smokeReportPath 但未通过')

  issues.unshift(...fatalIssues)
  const userTestReady = fatalIssues.length === 0 && hasRequiredArtifact && (
    platform.id === 'windows' ||
    (smoke === true && Boolean(smokeReport?.layout?.agent?.homeAiMain) && Boolean(smokeReport?.layout?.agent?.topnav))
  )
  const readiness = issues.length === 0 ? 'ready' : (existingArtifacts.length > 0 || smoke === true || installEvidenceCount > 0 ? 'partial' : 'missing')
  return {
    id: platform.id,
    name: platform.name,
    target: platform.target || '',
    readiness,
    codeSigningStatus: platform.codeSigningStatus || '',
    notarizationStatus: platform.notarizationStatus || '',
    artifacts,
    smokeReportPath,
    configuredSmokeReportPath: platform.smokeReportPath || '',
    smokePassed: smoke,
    userTestReady,
    requiredInstallEvidenceCount,
    installEvidenceCount,
    installEvidencePaths: evidencePaths,
    configuredInstallEvidencePaths: configuredEvidencePaths,
    autoInstallEvidencePaths: autoEvidencePaths,
    issues,
    warnings,
  }
}

function main() {
  const config = readJson(configPath)
  const issues = []
  const fatalIssues = []
  const warnings = []

  if (!config) fatalIssues.push(`缺少或无法解析 ${configPath}`)
  if (config && hasSecretText({ ...config, platforms: undefined, policy: undefined })) {
    fatalIssues.push(`${configPath} 顶层字段可能包含证书、密钥、密码或 token 敏感信息`)
  }
  if (!Array.isArray(config?.platforms)) fatalIssues.push(`${configPath} 缺少 platforms 数组`)

  const rows = Array.isArray(config?.platforms) ? config.platforms.map(validatePlatform) : []
  issues.push(...fatalIssues)
  for (const row of rows) {
    issues.push(...row.issues)
    warnings.push(...row.warnings)
  }

  for (const id of allowedPlatformIds) {
    if (!rows.some((row) => row.id === id)) {
      const issue = `${configPath} 缺少桌面平台: ${id}`
      issues.push(issue)
      fatalIssues.push(issue)
    }
  }

  const summary = {
    ready: rows.filter((row) => row.readiness === 'ready').length,
    partial: rows.filter((row) => row.readiness === 'partial').length,
    missing: rows.filter((row) => row.readiness === 'missing').length,
    artifacts: rows.reduce((total, row) => total + row.artifacts.filter((item) => item.exists).length, 0),
    userTestReady: rows.filter((row) => row.userTestReady).length,
  }
  const formalPassed = issues.length === 0 && summary.ready === rows.length && rows.length > 0
  const userTestPassed = fatalIssues.length === 0 && rows.length > 0 && rows.every((row) => row.userTestReady)

  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    configPath,
    passed: strict ? formalPassed : userTestPassed,
    formalPassed,
    userTestPassed,
    summary,
    platforms: rows,
    issues,
    warnings,
  }

  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

  const md = [
    '# 桌面端发布状态检查',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 配置：\`${configPath}\``,
    `> 结论：${report.passed ? (strict ? '正式发布通过' : '测试下载包通过') : '未通过'}`,
    `> 正式发布：${report.formalPassed ? '通过' : '未通过'}`,
    `> 测试下载包：${report.userTestPassed ? '通过' : '未通过'}`,
    '',
    `汇总：READY ${summary.ready} / PARTIAL ${summary.partial} / MISSING ${summary.missing} / USER_TEST_READY ${summary.userTestReady} / ARTIFACTS ${summary.artifacts}`,
    '',
    '| 平台 | Readiness | 测试包 | 签名 | 公证 | 产物数 | 安装截图 | Smoke |',
    '| --- | --- | --- | --- | --- | ---: | ---: | --- |',
    ...rows.map((row) => {
      const artifactCount = row.artifacts.filter((item) => item.exists).length
      const smoke = row.smokePassed === null ? '-' : (row.smokePassed ? '通过' : '未通过')
      return `| ${row.name || row.id} | ${row.readiness} | ${row.userTestReady ? '通过' : '未通过'} | ${row.codeSigningStatus || '-'} | ${row.notarizationStatus || '-'} | ${artifactCount} | ${row.installEvidenceCount}/${row.requiredInstallEvidenceCount} | ${smoke} |`
    }),
    '',
    '## 产物',
    '',
    '| 平台 | 文件 | Bytes | SHA-256 |',
    '| --- | --- | ---: | --- |',
    ...rows.flatMap((row) => row.artifacts.map((artifact) => `| ${row.name || row.id} | ${artifact.exists ? `\`${artifact.path}\`` : `${artifact.path}（缺失）`} | ${artifact.bytes || 0} | ${artifact.sha256 || '-'} |`)),
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
    '- 非 strict 模式只生成报告，不因为桌面端尚未签名或缺截图而失败。',
    '- 非 strict 模式的 `passed` 表示“可交给用户试装的测试下载包”已具备安装包和基础 smoke 证据；不代表正式公开发布完成。',
    '- 正式桌面下载包候选前运行 `npm run desktop:release-status -- --strict`；macOS 必须签名、公证并补齐安装截图，Windows 必须签名并补齐安装/卸载截图。',
    '- 本台账禁止记录证书、私钥、密码、token 和 notarization 凭据。',
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
