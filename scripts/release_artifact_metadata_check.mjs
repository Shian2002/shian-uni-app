#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { extname, join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.RELEASE_ARTIFACT_METADATA_STRICT === '1'
const configPath = process.env.RELEASE_ARTIFACT_METADATA_CONFIG || 'configs/release/artifact-metadata-requirements.json'
const packageJson = readJson('package.json') || {}
const version = process.env.RELEASE_ARTIFACT_METADATA_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.RELEASE_ARTIFACT_METADATA_OUT_DIR || join(root, 'artifacts', 'release-artifact-metadata', `${localTimestamp()}-${version}`)
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))

const allowedPlatforms = new Set(['android', 'ios', 'harmony', 'macos', 'windows'])
const artifactExtByKind = {
  apk: '.apk',
  aab: '.aab',
  ipa: '.ipa',
  testflight: '.json',
  hap: '.hap',
  'appgallery-record': '.json',
  dmg: '.dmg',
  zip: '.zip',
  exe: '.exe',
  msi: '.msi',
}
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

function fileInfo(path) {
  if (!pathExists(path)) return null
  const fullPath = join(root, path)
  const stat = statSync(fullPath)
  return {
    path,
    bytes: stat.size,
    sha256: sha256(fullPath),
    ext: extname(path).toLowerCase(),
  }
}

const evidenceFields = new Set(['deviceTestEvidence', 'appPrivacyEvidence', 'permissionEvidence', 'uninstallEvidence'])

function valueMissing(value) {
  if (value === undefined || value === null || value === '') return true
  if (Array.isArray(value) && value.length === 0) return true
  return false
}

function requiredFieldMissing(metadata, field) {
  if (evidenceFields.has(field)) return metadata[field] === undefined
  return valueMissing(metadata[field])
}

function evidenceReady(value) {
  if (Array.isArray(value)) return value.length > 0 && value.every((item) => {
    if (typeof item === 'string') return pathExists(item)
    return Boolean(item?.path) && pathExists(item.path)
  })
  if (typeof value === 'string') return pathExists(value)
  if (value && typeof value === 'object') return Boolean(value.path) && pathExists(value.path)
  return false
}

function validatePlatform(platform) {
  const issues = []
  const warnings = []
  const deferred = deferredPlatforms.has(platform.id)
  if (!allowedPlatforms.has(platform.id)) issues.push(`未知平台: ${platform.id || 'missing-id'}`)
  if (!platform.metadataPath) issues.push(`${platform.id || 'unknown'} 缺少 metadataPath`)
  if (!Array.isArray(platform.requiredFields) || platform.requiredFields.length === 0) {
    issues.push(`${platform.id || 'unknown'} 缺少 requiredFields`)
  }
  if (!Array.isArray(platform.requiredArtifactKinds) || platform.requiredArtifactKinds.length === 0) {
    issues.push(`${platform.id || 'unknown'} 缺少 requiredArtifactKinds`)
  }
  if (hasSecretText(platform)) issues.push(`${platform.id || 'unknown'} 配置疑似包含密钥、密码或证书信息`)
  if (deferred) {
    const metadata = readJson(platform.metadataPath)
    return {
      id: platform.id,
      name: platform.name,
      deferred,
      readiness: 'deferred',
      metadataPath: platform.metadataPath,
      metadata,
      artifact: metadata?.artifactPath ? fileInfo(metadata.artifactPath) : null,
      issues: [],
      warnings: [],
    }
  }

  const metadata = readJson(platform.metadataPath)
  if (!metadata) {
    if (!deferred) issues.push(`${platform.id} 缺少或无法解析元数据: ${platform.metadataPath}`)
    return {
      id: platform.id,
      name: platform.name,
      readiness: deferred ? 'deferred' : 'missing',
      deferred,
      metadataPath: platform.metadataPath,
      metadata: null,
      artifact: null,
      issues,
      warnings,
    }
  }
  if (hasSecretText(metadata)) issues.push(`${platform.id} 元数据疑似包含密钥、密码、验证码或证书信息`)

  for (const field of platform.requiredFields || []) {
    if (requiredFieldMissing(metadata, field)) issues.push(`${platform.id} 元数据缺少字段: ${field}`)
  }

  const artifact = fileInfo(metadata.artifactPath || '')
  if (!artifact) {
    issues.push(`${platform.id} artifactPath 不存在: ${metadata.artifactPath || 'missing'}`)
  } else {
    const expectedExts = new Set((platform.requiredArtifactKinds || []).map((kind) => artifactExtByKind[kind]).filter(Boolean))
    if (expectedExts.size && !expectedExts.has(artifact.ext)) {
      issues.push(`${platform.id} artifactPath 扩展名不符合 ${[...expectedExts].join('/')}: ${artifact.path}`)
    }
    if (metadata.artifactSha256 && metadata.artifactSha256 !== artifact.sha256) {
      issues.push(`${platform.id} artifactSha256 与实际文件不一致`)
    }
  }

  for (const field of evidenceFields) {
    if (metadata[field] !== undefined && !evidenceReady(metadata[field])) {
      warnings.push(`${platform.id} ${field} 未指向已存在证据文件`)
    }
  }

  const readiness = issues.length === 0 && warnings.length === 0 ? 'ready' : (artifact ? 'partial' : 'missing')
  return {
    id: platform.id,
    name: platform.name,
    deferred,
    readiness,
    metadataPath: platform.metadataPath,
    metadata,
    artifact,
    issues,
    warnings,
  }
}

function exampleMetadata(platform) {
  const artifactName = {
    android: 'shian-v1.0.0-yingyongbao.apk',
    ios: 'shian-v1.0.0-ios-testflight-record.json',
    harmony: 'shian-v1.0.0-harmony.hap',
    macos: 'shian-v1.0.0-macos-arm64.dmg',
    windows: 'shian-v1.0.0-windows-x64-nsis.exe',
  }[platform.id] || 'artifact.bin'
  const base = platform.metadataPath.replace(/\/build-metadata\.json$/, '')
  const data = {
    versionName: '1.0.0',
    versionCode: platform.id === 'ios' || platform.id === 'macos' || platform.id === 'windows' ? undefined : 100,
    buildNumber: platform.id === 'ios' ? 100 : undefined,
    commit: '<git commit>',
    buildTool: '<HBuilderX/DCloud/Xcode/DevEco/electron-builder>',
    builder: '<builder name or machine id, no account password>',
    builtAt: '<ISO timestamp>',
    channel: platform.id === 'android' ? '<yingyongbao/huawei/xiaomi/oppo/vivo/google-play>' : undefined,
    artifactPath: `${base}/${artifactName}`,
    artifactSha256: '<sha256>',
    testFlightBuildNumber: platform.id === 'ios' ? '<TestFlight build number>' : undefined,
    codeSigningStatus: platform.id === 'macos' || platform.id === 'windows' ? '<signed/unsigned>' : undefined,
    notarizationStatus: platform.id === 'macos' ? '<notarized/not-started>' : undefined,
    reviewAccountDelivery: '<secure-channel, do not write password>',
    deviceTestEvidence: [`${base}/screenshots/device-login.png`],
    appPrivacyEvidence: platform.id === 'ios' ? [`${base}/screenshots/app-privacy.png`] : undefined,
    permissionEvidence: platform.id === 'harmony' ? [`${base}/screenshots/permissions.png`] : undefined,
    uninstallEvidence: platform.id === 'windows' ? [`${base}/screenshots/uninstall.png`] : undefined,
  }
  return Object.fromEntries(Object.entries(data).filter(([, value]) => value !== undefined))
}

function main() {
  const config = readJson(configPath)
  const issues = []
  const warnings = []
  if (!config) issues.push(`缺少或无法解析 ${configPath}`)
  if (config && hasSecretText({ ...config, platforms: undefined, policy: undefined })) {
    issues.push(`${configPath} 顶层字段疑似包含密钥、密码或证书信息`)
  }
  if (!Array.isArray(config?.platforms)) issues.push(`${configPath} 缺少 platforms 数组`)
  const rows = Array.isArray(config?.platforms) ? config.platforms.map(validatePlatform) : []
  for (const row of rows.filter((item) => !item.deferred)) {
    issues.push(...row.issues)
    warnings.push(...row.warnings)
  }
  const ids = new Set(rows.map((row) => row.id))
  for (const id of allowedPlatforms) {
    if (!ids.has(id)) issues.push(`${configPath} 缺少平台元数据要求: ${id}`)
  }

  const summary = {
    ready: rows.filter((row) => row.readiness === 'ready').length,
    partial: rows.filter((row) => row.readiness === 'partial').length,
    missing: rows.filter((row) => row.readiness === 'missing').length,
    deferred: rows.filter((row) => row.readiness === 'deferred').length,
  }
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    configPath,
    passed: issues.length === 0 && warnings.length === 0 && rows.length > 0,
    releaseScope: {
      configPath: 'configs/release/current-release-scope.json',
      currentBatch: releaseScope.currentBatch || '',
      activePlatforms: releaseScope.activePlatforms || [],
      deferredPlatforms: [...deferredPlatforms],
    },
    summary,
    platforms: rows,
    issues,
    warnings,
  }

  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  writeFileSync(join(outDir, 'examples.json'), `${JSON.stringify(Object.fromEntries((config?.platforms || []).map((platform) => [platform.id, exampleMetadata(platform)])), null, 2)}\n`)

  const md = [
    '# 发行产物元数据检查',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 配置：\`${configPath}\``,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    `汇总：READY ${summary.ready} / PARTIAL ${summary.partial} / MISSING ${summary.missing} / DEFERRED ${summary.deferred}`,
    '',
    '| 平台 | Readiness | 元数据 | 产物 |',
    '| --- | --- | --- | --- |',
    ...rows.map((row) => `| ${row.name || row.id} | ${row.readiness} | \`${row.metadataPath || '-'}\` | ${row.artifact ? `\`${row.artifact.path}\`` : '-'} |`),
    '',
    '## 问题',
    '',
    ...(issues.length ? issues.map((issue) => `- ${issue}`) : ['- 无结构性问题。']),
    '',
    '## 警告',
    '',
    ...(warnings.length ? warnings.map((warning) => `- ${warning}`) : ['- 无警告。']),
    '',
    '## 使用规则',
    '',
    '- 外部打包机回传安装包时，同目录必须放 `build-metadata.json`。',
    '- `build-metadata.json` 只记录版本、commit、构建工具、构建人、安装包路径、hash、截图路径和审核账号交付方式。',
    '- 禁止写入审核账号密码、验证码、证书、签名密钥、keystore、p12、mobileprovision 和后台 token。',
    '- 正式候选前运行 `npm run release:artifact-metadata -- --strict`。',
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
