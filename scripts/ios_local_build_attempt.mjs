#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from 'node:fs'
import { basename, join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJsonSafe('package.json') || {}
const version = process.env.IOS_LOCAL_BUILD_VERSION || `v${packageJson.version || '0.0.0'}`
const execute = process.argv.includes('--execute') || process.env.IOS_LOCAL_BUILD_EXECUTE === '1'
const strict = process.argv.includes('--strict') || process.env.IOS_LOCAL_BUILD_STRICT === '1'
const timeoutMs = Number(process.env.IOS_LOCAL_BUILD_TIMEOUT_MS || 120000)
const minFreeGiB = Number(process.env.IOS_LOCAL_BUILD_MIN_FREE_GIB || 45)
const xcodeApfsVolume = '/Volumes/XcodeAPFS'
const minXcodeTargetGiB = Number(process.env.IOS_LOCAL_BUILD_MIN_XCODE_TARGET_GIB || 100)
const outDir = process.env.IOS_LOCAL_BUILD_OUT_DIR || join(root, 'artifacts', 'ios-local-build-attempts', `${localTimestamp()}-${version}`)

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function readJsonSafe(path) {
  if (!existsSync(join(root, path))) return null
  try {
    return JSON.parse(readFileSync(join(root, path), 'utf8'))
  } catch (_) {
    return null
  }
}

function redact(value) {
  return String(value || '')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '<redacted-email>')
    .replace(/(password|passwd|token|secret|privateKey|certpassword)(=|:)\s*[^\s"'，,}<>]+/gi, '$1$2 <redacted>')
}

function run(name, command, args = [], options = {}) {
  const startedAt = new Date().toISOString()
  const result = spawnSync(command, args, {
    cwd: options.cwd || root,
    env: { ...process.env, LC_ALL: 'en_US.UTF-8', LANG: 'en_US.UTF-8', ...(options.env || {}) },
    encoding: 'utf8',
    timeout: options.timeoutMs || timeoutMs,
  })
  return {
    name,
    command: [command, ...args],
    startedAt,
    finishedAt: new Date().toISOString(),
    exitCode: result.status,
    signal: result.signal,
    error: result.error ? result.error.message : null,
    stdout: redact(result.stdout || ''),
    stderr: redact(result.stderr || ''),
  }
}

function shell(name, command) {
  return run(name, '/bin/zsh', ['-lc', command])
}

function combined(check) {
  return `${check?.stdout || ''}\n${check?.stderr || ''}`.trim()
}

function parseDisk(check) {
  const lines = combined(check).split('\n').map((line) => line.trim()).filter(Boolean)
  const dataLine = lines.find((line) => line.startsWith('/'))
  if (!dataLine) return null
  const parts = dataLine.split(/\s+/)
  const availableKiB = Number(parts[3])
  if (!Number.isFinite(availableKiB)) return null
  return Math.round((availableKiB / 1024 / 1024) * 10) / 10
}

function provisioningProfileSummary() {
  const profileDir = join(process.env.HOME || '', 'Library', 'MobileDevice', 'Provisioning Profiles')
  if (!existsSync(profileDir)) {
    return { directory: profileDir, count: 0, files: [] }
  }
  const files = readdirSync(profileDir)
    .filter((name) => name.endsWith('.mobileprovision'))
    .sort()
    .slice(0, 20)
    .map((name) => basename(name))
  return { directory: profileDir, count: files.length, files }
}

function codeSigningIdentityCount(check) {
  const text = combined(check)
  const explicit = text.match(/(\d+)\s+valid identities found/i)
  if (explicit) return Number(explicit[1])
  return text.split('\n').filter((line) => /^\s*\d+\)/.test(line)).length
}

function addUnique(items, item) {
  if (!items.some((existing) => existing.id === item.id)) items.push(item)
}

mkdirSync(outDir, { recursive: true })

const checks = {
  xcodeSelect: run('xcode-select', 'xcode-select', ['-p']),
  xcodebuildVersion: run('xcodebuild-version', 'xcodebuild', ['-version']),
  simctlDevices: run('simctl-devices', 'xcrun', ['simctl', 'list', 'devices', '--json']),
  codeSigningIdentities: run('codesigning-identities', 'security', ['find-identity', '-v', '-p', 'codesigning']),
  diskFree: shell('disk-free', `df -k ${JSON.stringify(root)}`),
  xcodeApfsDiskFree: existsSync(xcodeApfsVolume) ? shell('xcode-apfs-disk-free', `df -k ${JSON.stringify(xcodeApfsVolume)}`) : null,
  xcodeApfsDiskutil: existsSync(xcodeApfsVolume) ? run('xcode-apfs-diskutil', 'diskutil', ['info', xcodeApfsVolume]) : null,
  masPath: shell('mas-path', 'command -v mas || true'),
}

const profiles = provisioningProfileSummary()
const diskFreeGiB = parseDisk(checks.diskFree)
const xcodeApfsFreeGiB = checks.xcodeApfsDiskFree ? parseDisk(checks.xcodeApfsDiskFree) : null
const xcodeApfsInfo = checks.xcodeApfsDiskutil ? combined(checks.xcodeApfsDiskutil) : ''
const xcodeApfsReady = existsSync(xcodeApfsVolume) &&
  /File System Personality:\s+APFS/i.test(xcodeApfsInfo) &&
  xcodeApfsFreeGiB !== null &&
  xcodeApfsFreeGiB >= minXcodeTargetGiB
const identityCount = codeSigningIdentityCount(checks.codeSigningIdentities)
const xcodeDeveloperDir = combined(checks.xcodeSelect)
const xcodebuildOutput = combined(checks.xcodebuildVersion)
const simctlOutput = combined(checks.simctlDevices)
const fullXcodeReady = checks.xcodebuildVersion.exitCode === 0 &&
  xcodeDeveloperDir.includes('/Xcode.app/Contents/Developer') &&
  !/requires Xcode|CommandLineTools/i.test(xcodebuildOutput)
const simctlReady = checks.simctlDevices.exitCode === 0 && !/unable to find utility|not a developer tool/i.test(simctlOutput)

const blockers = []
const warnings = []

if (!execute) {
  warnings.push({
    id: 'read-only-attempt',
    text: '本脚本只读记录 iOS 本地打包前置条件；设置 IOS_LOCAL_BUILD_EXECUTE=1 仅表示本轮按正式尝试记录，不会触发签名或上传。',
  })
}

if (!fullXcodeReady) {
  addUnique(blockers, {
    id: 'xcode-full-missing',
    owner: 'environment-action',
    text: '本机未配置完整 Xcode；当前只检测到 Command Line Tools 或 xcodebuild 不可用。',
  })
}

if (!simctlReady) {
  addUnique(blockers, {
    id: 'simctl-missing',
    owner: 'environment-action',
    text: '本机缺少 simctl，不能做 iOS 模拟器/设备侧基础检查。',
  })
}

if (profiles.count === 0) {
  addUnique(blockers, {
    id: 'ios-provisioning-profile-missing',
    owner: 'user-last',
    text: '未检测到 iOS provisioning profile；TestFlight/IPA 需要 Apple Developer 描述文件。',
  })
}

if (identityCount === 0) {
  addUnique(blockers, {
    id: 'ios-code-signing-identity-missing',
    owner: 'user-last',
    text: '未检测到有效 Apple 代码签名身份；TestFlight/IPA 需要 Apple Developer 证书。',
  })
}

if (diskFreeGiB !== null && diskFreeGiB < minFreeGiB) {
  if (xcodeApfsReady) {
    warnings.push({
      id: 'internal-disk-cache-low',
      text: `内置盘当前可用空间约 ${diskFreeGiB} GiB，低于 ${minFreeGiB} GiB 建议线；/Volumes/XcodeAPFS 已有 ${xcodeApfsFreeGiB} GiB APFS 空间可承载 Xcode.app，下载/解压仍需保留临时缓存空间。`,
    })
  } else {
    addUnique(blockers, {
      id: 'disk-space-low',
      owner: 'environment-action',
      text: `当前可用空间约 ${diskFreeGiB} GiB，低于完整 Xcode/DevEco 和多端打包建议阈值 ${minFreeGiB} GiB，且没有 ${minXcodeTargetGiB} GiB 以上 APFS Xcode 目标盘。`,
    })
  }
}

if (!existsSync('/Applications/Xcode.app') && existsSync('/Applications/Xcodes.app')) {
  warnings.push({
    id: 'xcodes-app-without-xcode',
    text: '检测到 Xcodes.app，但未检测到 /Applications/Xcode.app；Xcodes.app 只是安装管理器，不等同于完整 Xcode。',
  })
}

const passed = blockers.length === 0
const attempt = {
  generatedAt: new Date().toISOString(),
  version,
  platform: 'ios',
  execute,
  passed,
  cwd: root,
  timeoutMs,
  minFreeGiB,
  checks: {
    xcodeDeveloperDir,
    xcodebuildVersion: xcodebuildOutput,
    simctlReady,
    fullXcodeReady,
    masPath: combined(checks.masPath),
    diskFreeGiB,
    xcodeApfs: {
      path: xcodeApfsVolume,
      exists: existsSync(xcodeApfsVolume),
      ready: xcodeApfsReady,
      freeGiB: xcodeApfsFreeGiB,
      minTargetGiB: minXcodeTargetGiB,
    },
    provisioningProfiles: profiles,
    codeSigningIdentityCount: identityCount,
  },
  commandLogPath: rel(join(outDir, 'commands.redacted.log')),
  blockers,
  warnings,
  next: [
    '继续用 /Volumes/XcodeAPFS 安装完整 Xcode 16.2；安装成功后用 xcode-select 指向对应 Xcode.app/Contents/Developer。',
    'Apple Developer 证书、p12、mobileprovision、签名口令只在本机钥匙串或安全交接中处理，不进入 GitHub。',
    '如果继续走 HBuilderX/DCloud 云打包，优先处理 provisioning profile、p12 和 DCloud iOS 签名材料。',
    '成功生成 IPA 或 TestFlight 构建号后，把记录放入 artifacts/release-inbox/v1.0.0/ios/ 并补 build-metadata.json。',
  ],
}

const commandLog = Object.values(checks).filter(Boolean).map((check) => [
  `## ${check.name}`,
  `$ ${check.command.join(' ')}`,
  `exitCode=${check.exitCode}`,
  check.error ? `error=${check.error}` : '',
  check.stdout ? `stdout:\n${check.stdout}` : '',
  check.stderr ? `stderr:\n${check.stderr}` : '',
].filter(Boolean).join('\n')).join('\n\n')

writeFileSync(join(outDir, 'attempt.json'), `${JSON.stringify(attempt, null, 2)}\n`)
writeFileSync(join(outDir, 'commands.redacted.log'), `${commandLog}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# iOS 本地构建尝试',
  '',
  `> 生成时间：${attempt.generatedAt}`,
  `> 执行标记：${execute ? '是' : '否，read-only'}`,
  `> 结论：${passed ? '通过' : '未通过'}`,
  '',
  '## 环境',
  '',
  `- Xcode Developer Dir：${xcodeDeveloperDir || '未检测到'}`,
  `- 完整 Xcode：${fullXcodeReady ? '可用' : '不可用'}`,
  `- simctl：${simctlReady ? '可用' : '不可用'}`,
  `- provisioning profile：${profiles.count} 个`,
  `- 代码签名身份：${identityCount} 个`,
  `- 可用空间：${diskFreeGiB ?? '未知'} GiB`,
  `- /Volumes/XcodeAPFS：${xcodeApfsReady ? `${xcodeApfsFreeGiB} GiB APFS 可用` : '不可用或空间不足，见 attempt.json'}`,
  '',
  '## 阻塞',
  '',
  ...(blockers.length ? blockers.map((item) => `- ${item.id} / ${item.owner}：${item.text}`) : ['- 暂无阻塞。']),
  '',
  '## 警告',
  '',
  ...(warnings.length ? warnings.map((item) => `- ${item.id}：${item.text}`) : ['- 暂无警告。']),
  '',
  '## 下一步',
  '',
  ...attempt.next.map((item) => `- ${item}`),
  '',
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  execute,
  passed,
  blockers,
  warnings,
  checks: attempt.checks,
}, null, 2))

if (strict && !passed) process.exit(1)
