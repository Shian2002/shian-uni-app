#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { extname, join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.RELEASE_VERSION || `v${packageJson.version || '0.0.0'}`
const inbox = process.env.RELEASE_INBOX_DIR || 'artifacts/release-inbox'
const strict = process.argv.includes('--strict') || process.env.RELEASE_INTAKE_STRICT === '1'
const outDir = process.env.RELEASE_ARTIFACT_INTAKE_DIR || join(root, 'artifacts', 'release-artifact-intake', `${localTimestamp()}-${version}`)

const binaryExts = new Set(['.apk', '.aab', '.ipa', '.hap', '.dmg', '.zip', '.exe', '.msi'])
const recordExts = new Set(['.md', '.json', '.txt'])
const forbiddenPatterns = [
  /keystore/i,
  /\.jks$/i,
  /\.p12$/i,
  /\.mobileprovision$/i,
  /\.cer$/i,
  /\.pem$/i,
  /\.key$/i,
  /\.env$/i,
  /secret/i,
  /password/i,
  /credential/i,
  /private[-_]?key/i,
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

function git(args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim()
  } catch (_) {
    return ''
  }
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
    else entries.push({ path: rel(item), bytes: stat.size, mtimeMs: stat.mtimeMs })
  }
  return entries
}

function isForbidden(path) {
  return forbiddenPatterns.some((pattern) => pattern.test(path))
}

function platformFor(path) {
  const normalized = path.toLowerCase()
  const ext = extname(path).toLowerCase()
  if (normalized.includes('/android/') || ['.apk', '.aab'].includes(ext)) return 'android'
  if (normalized.includes('/ios/') || ext === '.ipa' || normalized.includes('testflight')) return 'ios'
  if (normalized.includes('/harmony/') || ext === '.hap') return 'harmony'
  if (normalized.includes('/windows/') || ['.exe', '.msi'].includes(ext)) return 'windows'
  if (normalized.includes('/macos/') || normalized.includes('/desktop/') || ['.dmg', '.zip'].includes(ext)) return 'macos'
  return 'other'
}

function kindFor(path) {
  const ext = extname(path).toLowerCase()
  if (binaryExts.has(ext)) return 'binary'
  if (recordExts.has(ext)) return 'record'
  return 'other'
}

function collect() {
  const files = walk(inbox)
  const forbidden = files.filter((item) => isForbidden(item.path))
  const accepted = files
    .filter((item) => !isForbidden(item.path))
    .filter((item) => binaryExts.has(extname(item.path).toLowerCase()) || recordExts.has(extname(item.path).toLowerCase()))
    .map((item) => ({
      ...item,
      platform: platformFor(item.path),
      kind: kindFor(item.path),
      sha256: sha256(join(root, item.path)),
    }))
  return { files, accepted, forbidden }
}

function hasPlatform(accepted, platform, exts, recordPattern = null) {
  return accepted.some((item) => {
    if (item.platform !== platform) return false
    const ext = extname(item.path).toLowerCase()
    if (exts.includes(ext)) return true
    return recordPattern ? recordPattern.test(item.path) : false
  })
}

function platformStatus(accepted) {
  const statuses = {
    android: hasPlatform(accepted, 'android', ['.apk', '.aab']) ? 'ready' : 'missing',
    ios: hasPlatform(accepted, 'ios', ['.ipa'], /testflight|appstore|ios-build/i) ? 'ready' : 'missing',
    harmony: hasPlatform(accepted, 'harmony', ['.hap']) ? 'ready' : 'missing',
    macos: hasPlatform(accepted, 'macos', ['.dmg', '.zip']) ? 'ready' : 'missing',
    windows: hasPlatform(accepted, 'windows', ['.exe', '.msi']) ? 'ready' : 'missing',
  }
  return statuses
}

function missingHardBlocks(statuses) {
  return [
    statuses.android === 'ready' ? '' : 'Android APK/AAB',
    statuses.ios === 'ready' ? '' : 'iOS IPA/TestFlight 构建记录',
    statuses.harmony === 'ready' ? '' : '鸿蒙 HAP/AppGallery 包',
    statuses.windows === 'ready' ? '' : 'Windows EXE/MSI',
  ].filter(Boolean)
}

function artifactRows(items) {
  if (!items.length) return '| 暂无 |  |  |  |  |'
  return items.map((item) => `| ${item.path} | ${item.platform} | ${item.kind} | ${item.bytes} | ${item.sha256} |`).join('\n')
}

function forbiddenRows(items) {
  if (!items.length) return ['- 未发现。']
  return items.map((item) => `- ${item.path}`)
}

function writeChecksums(items) {
  const lines = items.filter((item) => item.kind === 'binary').map((item) => `${item.sha256}  ${item.path}`)
  writeFileSync(join(outDir, 'checksums.sha256'), `${lines.join('\n')}${lines.length ? '\n' : ''}`)
}

function main() {
  mkdirSync(outDir, { recursive: true })
  const { accepted, forbidden } = collect()
  const statuses = platformStatus(accepted)
  const missing = missingHardBlocks(statuses)
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    branch: git(['branch', '--show-current']) || '',
    commit: git(['rev-parse', 'HEAD']) || '',
    inbox,
    intakeDir: rel(outDir),
    passed: forbidden.length === 0 && (!strict || missing.length === 0),
    strict,
    platforms: statuses,
    accepted,
    forbidden: forbidden.map((item) => item.path),
    missingHardBlocks: missing,
    notes: [
      '本脚本只读取本机 release inbox，不上传、不提交商店、不移动文件。',
      '证书、密钥、keystore、p12、mobileprovision、pem、key 不允许放入 inbox。',
      '二进制安装包和截图材料被 .gitignore 排除，不应提交到 Git。',
    ],
  }

  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  writeChecksums(accepted)

  const lines = [
    `# ${version} 发行产物收件报告`,
    '',
    `> 生成时间：${report.generatedAt}`,
    `> commit：${report.commit || '未读取到'}`,
    `> inbox：\`${inbox}\``,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    '## 平台状态',
    '',
    `- Android：${statuses.android}`,
    `- iOS：${statuses.ios}`,
    `- 鸿蒙：${statuses.harmony}`,
    `- macOS：${statuses.macos}`,
    `- Windows：${statuses.windows}`,
    '',
    '## 已收件文件',
    '',
    '| 文件 | 平台 | 类型 | Bytes | SHA-256 |',
    '| --- | --- | --- | ---: | --- |',
    artifactRows(accepted),
    '',
    '## 禁止材料',
    '',
    ...forbiddenRows(forbidden),
    '',
    '## 当前硬缺口',
    '',
    ...(missing.length ? missing.map((item) => `- ${item}`) : ['- 暂无硬缺口。']),
    '',
    '## 后续动作',
    '',
    '- 产物齐全后运行 `npm run release:intake -- --strict`。',
    '- 再运行 `npm run release:finalize` 生成 GitHub Release 草稿包、商店包和 readiness 证据。',
    '- 外部上传 GitHub Release 或商店后台前，仍需人工确认版本、hash、审核账号和隐私材料。',
  ]
  writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

  console.log(JSON.stringify({
    outDir: report.intakeDir,
    passed: report.passed,
    platforms: report.platforms,
    missingHardBlocks: report.missingHardBlocks,
    forbidden: report.forbidden,
  }, null, 2))

  if (!report.passed) process.exit(1)
}

main()
