#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'))
const version = process.env.DESKTOP_SIGNING_PREFLIGHT_VERSION || `v${packageJson.version || '0.0.0'}`
const strict = process.argv.includes('--strict') || process.env.DESKTOP_SIGNING_PREFLIGHT_STRICT === '1'
const outDir = process.env.DESKTOP_SIGNING_PREFLIGHT_OUT_DIR || join(root, 'artifacts', 'desktop-signing-preflight', `${localTimestamp()}-${version}`)

const paths = {
  macApp: 'desktop/release/mac-arm64/时安解忧屋.app',
  macDmg: 'desktop/release/时安解忧屋-1.0.0-arm64.dmg',
  macInboxDmg: `artifacts/release-inbox/${version}/macos/shian-${version}-macos-arm64.dmg`,
  windowsExe: 'desktop/release/时安解忧屋 Setup 1.0.0.exe',
  windowsInboxExe: `artifacts/release-inbox/${version}/windows/shian-${version}-windows-x64-nsis.exe`,
}

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function run(command, args = []) {
  const result = spawnSync(command, args, {
    cwd: root,
    encoding: 'utf8',
    timeout: 120000,
    maxBuffer: 1024 * 1024 * 12,
  })
  return {
    command: [command, ...args].join(' '),
    status: result.status,
    signal: result.signal,
    ok: result.status === 0 && !result.error,
    stdout: redact(result.stdout || ''),
    stderr: redact(result.stderr || (result.error ? result.error.message : '')),
  }
}

function redact(value) {
  return String(value || '')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '<redacted-email>')
    .replace(/([A-F0-9]{40})/gi, '<redacted-sha1>')
    .replace(/(password|passwd|token|secret|keychain-profile|apple-id|team-id)(=|:|\s+)[^\s"'，,}]+/gi, '$1$2<redacted>')
}

function fileInfo(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return { path, exists: false, bytes: 0, mtime: '' }
  const stat = statSync(fullPath)
  return { path, exists: true, bytes: stat.size, mtime: new Date(stat.mtimeMs).toISOString() }
}

function commandExists(command) {
  return run('which', [command])
}

function parseDeveloperIdIdentity(output) {
  const lines = String(output || '').split('\n')
  const developerIdLines = lines.filter((line) => /Developer ID Application/i.test(line))
  const validCountMatch = String(output || '').match(/(\d+) valid identities found/i)
  return {
    hasDeveloperIdApplication: developerIdLines.length > 0,
    developerIdIdentityCount: developerIdLines.length,
    validIdentityCount: validCountMatch ? Number(validCountMatch[1]) : null,
  }
}

mkdirSync(outDir, { recursive: true })

const securityIdentity = run('security', ['find-identity', '-v', '-p', 'codesigning'])
const identitySummary = parseDeveloperIdIdentity(`${securityIdentity.stdout}\n${securityIdentity.stderr}`)
const notarytool = run('xcrun', ['notarytool', '--help'])
const codesignMacApp = fileInfo(paths.macApp).exists
  ? run('codesign', ['--verify', '--deep', '--strict', join(root, paths.macApp)])
  : { ok: false, command: 'codesign --verify --deep --strict <mac app>', stdout: '', stderr: 'mac app missing' }
const spctlMacApp = fileInfo(paths.macApp).exists
  ? run('spctl', ['--assess', '--type', 'execute', '--verbose=4', join(root, paths.macApp)])
  : { ok: false, command: 'spctl --assess <mac app>', stdout: '', stderr: 'mac app missing' }
const signtool = commandExists('signtool')
const osslsigncode = commandExists('osslsigncode')

const macReady = identitySummary.hasDeveloperIdApplication && notarytool.ok && codesignMacApp.ok && spctlMacApp.ok
const windowsToolReady = signtool.ok || osslsigncode.ok
const issues = [
  !identitySummary.hasDeveloperIdApplication && 'macOS 缺少有效 Developer ID Application 签名身份。',
  !notarytool.ok && 'macOS 缺少 xcrun notarytool 或当前 Xcode/CLT 不支持 notarization。',
  !codesignMacApp.ok && 'macOS .app 当前未通过 codesign --verify --deep --strict。',
  !spctlMacApp.ok && 'macOS .app 当前未通过 Gatekeeper spctl assess。',
  !windowsToolReady && 'Windows 缺少 signtool 或 osslsigncode，无法本机验证/执行代码签名。',
].filter(Boolean)

const warnings = [
  '本预检不会读取、保存或要求输入证书密码、Apple ID、notarytool keychain profile、Windows 代码签名私钥。',
  '未签名测试包可以继续内部试用；正式公开下载前必须完成 macOS Developer ID 签名、公证和 Windows 代码签名。',
]

const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  passed: issues.length === 0,
  summary: {
    macSigningReady: macReady,
    developerIdApplication: identitySummary.hasDeveloperIdApplication,
    notarytool: notarytool.ok,
    macCodesignStrict: codesignMacApp.ok,
    macGatekeeperAssess: spctlMacApp.ok,
    windowsSigningTool: windowsToolReady,
  },
  artifacts: {
    macApp: fileInfo(paths.macApp),
    macDmg: fileInfo(paths.macDmg),
    macInboxDmg: fileInfo(paths.macInboxDmg),
    windowsExe: fileInfo(paths.windowsExe),
    windowsInboxExe: fileInfo(paths.windowsInboxExe),
  },
  checks: {
    securityIdentity,
    identitySummary,
    notarytool,
    codesignMacApp,
    spctlMacApp,
    signtool,
    osslsigncode,
  },
  issues,
  warnings,
  outDir: rel(outDir),
}

writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# 桌面端签名与公证预检',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  '',
  '## 摘要',
  '',
  `- Developer ID Application：${report.summary.developerIdApplication ? '可用' : '缺失'}`,
  `- notarytool：${report.summary.notarytool ? '可用' : '缺失'}`,
  `- macOS codesign strict：${report.summary.macCodesignStrict ? '通过' : '未通过'}`,
  `- macOS Gatekeeper：${report.summary.macGatekeeperAssess ? '通过' : '未通过'}`,
  `- Windows 签名工具：${report.summary.windowsSigningTool ? '可用' : '缺失'}`,
  '',
  '## 产物',
  '',
  ...Object.entries(report.artifacts).map(([key, value]) => `- ${key}：${value.exists ? `\`${value.path}\` (${value.bytes} bytes)` : `缺失 ${value.path}`}`),
  '',
  '## 问题',
  '',
  ...(issues.length ? issues.map((issue) => `- ${issue}`) : ['- 暂无。']),
  '',
  '## 边界',
  '',
  ...warnings.map((warning) => `- ${warning}`),
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: report.outDir,
  passed: report.passed,
  summary: report.summary,
  issues,
}, null, 2))

if (strict && !report.passed) process.exit(1)
