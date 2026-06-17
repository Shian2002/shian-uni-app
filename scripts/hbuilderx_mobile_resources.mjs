#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.HBUILDERX_MOBILE_RESOURCES_STRICT === '1'
const packageJson = readJson('package.json') || {}
const version = process.env.HBUILDERX_MOBILE_RESOURCES_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.HBUILDERX_MOBILE_RESOURCES_DIR || join(root, 'artifacts', 'hbuilderx-mobile-resources', `${localTimestamp()}-${version}`)
const cliPath = process.env.HBUILDERX_CLI || '/Applications/HBuilderX.app/Contents/MacOS/cli'
const projectPath = process.env.HBUILDERX_PROJECT || root
const timeoutMs = Number(process.env.HBUILDERX_CLI_TIMEOUT_MS || 120000)

const platforms = [
  { id: 'android', command: ['publish', 'app-android', '--type', 'appResource', '--project', projectPath] },
  { id: 'ios', command: ['publish', 'app-ios', '--type', 'appResource', '--project', projectPath] },
  { id: 'harmony', command: ['publish', 'app-harmony', '--type', 'appResource', '--project', projectPath] },
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

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function redact(value) {
  return String(value || '')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '<redacted-email>')
    .replace(/(password|passwd|token|secret|certpassword|storepassword|privateKey)(=|:)\s*[^\s"'，,}]+/gi, '$1$2 <redacted>')
}

function runCli(args, options = {}) {
  if (!existsSync(cliPath)) {
    return { ok: false, command: [cliPath, ...args].join(' '), output: `HBuilderX CLI 不存在: ${cliPath}` }
  }
  try {
    const output = execFileSync(cliPath, args, {
      cwd: root,
      env: {
        ...process.env,
        LANG: 'en_US.UTF-8',
        LC_ALL: 'en_US.UTF-8',
        LC_CTYPE: 'en_US.UTF-8',
      },
      encoding: 'utf8',
      timeout: options.timeoutMs || timeoutMs,
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    const redactedOutput = redact(output.trim())
    const cliNotReady = isCliNotReadyOutput(redactedOutput)
    return { ok: !cliNotReady, command: [cliPath, ...args].join(' '), output: redactedOutput }
  } catch (error) {
    const stdout = String(error.stdout || '').trim()
    const stderr = String(error.stderr || '').trim()
    return {
      ok: false,
      command: [cliPath, ...args].join(' '),
      output: redact([stdout, stderr, error.message].filter(Boolean).join('\n')),
    }
  }
}

function sleepMs(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms)
}

function runCliUntilOk(args, options = {}) {
  const attempts = options.attempts || 5
  const delayMs = options.delayMs || 2000
  let last = null
  for (let index = 0; index < attempts; index += 1) {
    last = runCli(args, options)
    if (last.ok || isCliEnvironmentIncompatible(last.output)) return last
    if (index < attempts - 1) sleepMs(delayMs)
  }
  return last
}

function runSystem(command, args = []) {
  try {
    return execFileSync(command, args, {
      cwd: root,
      encoding: 'utf8',
      timeout: 10000,
      stdio: ['ignore', 'pipe', 'pipe'],
    }).trim()
  } catch (error) {
    const stdout = String(error.stdout || '').trim()
    const stderr = String(error.stderr || '').trim()
    return redact([stdout, stderr, error.message].filter(Boolean).join('\n'))
  }
}

function cleanupResidualAppBuildProcesses() {
  const output = runSystem('ps', ['-axo', 'pid=,command='])
  if (!output) return []
  const killed = []
  for (const line of output.split('\n')) {
    const match = line.trim().match(/^(\d+)\s+(.+)$/)
    if (!match) continue
    const pid = Number(match[1])
    const command = match[2]
    if (!Number.isFinite(pid) || pid === process.pid) continue
    if (!command.includes('uni.js build -p app')) continue
    if (!command.includes('xuan-cet-tai')) continue
    try {
      process.kill(pid, 'SIGTERM')
      killed.push({ pid, signal: 'SIGTERM', command: redact(command) })
    } catch (error) {
      killed.push({ pid, signal: 'SIGTERM', command: redact(command), error: error.message })
    }
  }
  return killed
}

function isCliEnvironmentIncompatible(output) {
  return /Incompatible processor|Qt build requires|requires the following features/i.test(String(output || ''))
}

function isCliNotReadyOutput(output) {
  return /未检测到已打开的HBuilderX|请先执行cli open启动HBuilderX/i.test(String(output || ''))
}

function isLoggedInOutput(output) {
  return /<redacted-email>|@/.test(String(output || '')) &&
    !/需要先登录|未登录|login/i.test(String(output || '')) &&
    !isCliNotReadyOutput(output)
}

function walkFiles(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return []
  const entries = []
  for (const name of readdirSync(fullPath)) {
    const item = join(fullPath, name)
    const stat = statSync(item)
    const relativePath = rel(item)
    if (stat.isDirectory()) {
      entries.push(...walkFiles(relativePath))
    } else {
      entries.push({ path: relativePath, bytes: stat.size, sha256: sha256(item), mtimeMs: stat.mtimeMs })
    }
  }
  return entries
}

function appResourceFiles(beforeTime) {
  const files = [
    ...walkFiles('unpackage'),
    ...walkFiles('nativeplugins'),
  ]
  return files
    .filter((item) => item.bytes > 0 && item.mtimeMs >= beforeTime - 1000)
    .filter((item) => !/(keystore|\.jks$|\.p12$|mobileprovision|private[-_]?key|password|secret|token)/i.test(item.path))
    .sort((a, b) => b.mtimeMs - a.mtimeMs)
    .slice(0, 200)
}

function existingAppResourceFiles() {
  return walkFiles('unpackage/resources')
    .filter((item) => item.bytes > 0)
    .filter((item) => !/(keystore|\.jks$|\.p12$|mobileprovision|private[-_]?key|password|secret|token)/i.test(item.path))
    .sort((a, b) => b.mtimeMs - a.mtimeMs)
    .slice(0, 200)
}

function statusFor(result, files) {
  const output = result.output || ''
  if (isCliNotReadyOutput(output)) return 'failed'
  if (files.length > 0) return 'ready'
  if (isCliEnvironmentIncompatible(output)) return 'environment-action'
  if (/需要先登录|未登录|login/i.test(output)) return 'user-action'
  if (/证书|keystore|p12|profile|签名/i.test(output)) return 'user-action'
  if (!result.ok) return 'failed'
  return 'missing-output'
}

mkdirSync(outDir, { recursive: true })

const startedAtMs = Date.now()
const environment = {
  platform: process.platform,
  arch: process.arch,
  hostMachine: runSystem('uname', ['-m']),
  cliFileInfo: existsSync(cliPath) ? `${cliPath} exists` : '',
}
let open = { ok: true, command: [cliPath, 'open'].join(' '), output: '已复用现有 HBuilderX 会话' }
let userInfo = runCliUntilOk(['user', 'info'], { timeoutMs: 30000, attempts: 2, delayMs: 1000 })
if (!userInfo.ok || !isLoggedInOutput(userInfo.output || '')) {
  open = runCli(['open'], { timeoutMs: 30000 })
  if (open.ok) sleepMs(3000)
  userInfo = runCliUntilOk(['user', 'info'], { timeoutMs: 30000 })
}
const projectOpen = runCliUntilOk(['project', 'open', '--path', projectPath], { timeoutMs: 30000 })

const results = []
for (const platform of platforms) {
  const before = Date.now()
  const result = runCli(platform.command)
  const generatedFiles = appResourceFiles(before)
  const files = generatedFiles.length ? generatedFiles : (result.ok ? existingAppResourceFiles() : [])
  results.push({
    id: platform.id,
    command: result.command,
    ok: result.ok,
    status: statusFor(result, files),
    output: result.output,
    files,
  })
}
const residualBuildCleanup = cleanupResidualAppBuildProcesses()

const summary = {
  ready: results.filter((item) => item.status === 'ready').length,
  userAction: results.filter((item) => item.status === 'user-action').length,
  environmentAction: results.filter((item) => item.status === 'environment-action').length,
  failed: results.filter((item) => item.status === 'failed').length,
  missingOutput: results.filter((item) => item.status === 'missing-output').length,
}
const loggedIn = userInfo.ok && isLoggedInOutput(userInfo.output || '')
const passed = loggedIn && projectOpen.ok && summary.ready === platforms.length
const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  cliPath,
  projectPath,
  environment,
  environmentIssue: isCliEnvironmentIncompatible([open.output, userInfo.output, projectOpen.output, ...results.map((item) => item.output)].join('\n'))
    ? 'HBuilderX CLI 启动时报 Qt/processor feature 不兼容；请安装与当前 Mac 架构匹配的 HBuilderX，再确认 DCloud 登录和发行权限。'
    : '',
  hbuilderxDetected: existsSync(cliPath),
  open,
  userInfo: {
    ok: userInfo.ok,
    command: userInfo.command,
    loggedIn,
    output: userInfo.output,
  },
  projectOpen,
  results,
  residualBuildCleanup,
  summary,
  passed,
  startedAtMs,
  policy: {
    noSecretsInGit: true,
    generatedResourcesAreNotSignedPackages: true,
    releaseInboxRequiredForApkIpaHap: true,
  },
  next: [
    '如果 status=environment-action，先修复 HBuilderX 安装/架构兼容问题；当前 CLI 无法正常启动时，登录和发行权限检查都不可信。',
    '如果 status=user-action，先在 HBuilderX 登录 DCloud 账号并确认发行权限，然后重跑 npm run mobile:hbuilderx-resources。',
    '生成的 appResource 仍不是 APK/AAB、IPA/TestFlight 或 HAP；真包仍需放入 artifacts/release-inbox/v1.0.0/<platform>/。',
    '证书、keystore、p12、mobileprovision、签名口令和 DCloud 账号密码不得写入 GitHub。',
  ],
}

writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'latest-commands.sh'), `${[
  '#!/bin/zsh',
  'set -e',
  `cd ${JSON.stringify(root)}`,
  `${JSON.stringify(cliPath)} open`,
  `${JSON.stringify(cliPath)} project open --path ${JSON.stringify(projectPath)}`,
  ...platforms.map((platform) => `${JSON.stringify(cliPath)} ${platform.command.map((item) => JSON.stringify(item)).join(' ')}`),
  '',
].join('\n')}`)

const lines = [
  '# HBuilderX 移动端 App 资源发行检查',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${passed ? '通过' : '未通过'}`,
  `> CLI：\`${cliPath}\``,
  `> 项目：\`${projectPath}\``,
  '',
  '## 状态',
  '',
  `- HBuilderX CLI：${report.hbuilderxDetected ? '存在' : '缺失'}`,
  `- user info：${report.userInfo.loggedIn ? '已读取到登录态' : '未确认登录态'}`,
  `- READY：${summary.ready}`,
  `- USER-ACTION：${summary.userAction}`,
  `- ENVIRONMENT-ACTION：${summary.environmentAction}`,
  `- FAILED：${summary.failed}`,
  `- MISSING-OUTPUT：${summary.missingOutput}`,
  `- 主机架构：${environment.hostMachine || environment.arch}`,
  `- CLI 文件：${environment.cliFileInfo || '缺失'}`,
  ...(report.environmentIssue ? [`- 环境问题：${report.environmentIssue}`] : []),
  `- 残留 App 构建进程清理：${residualBuildCleanup.length}`,
  '',
  '| 平台 | 状态 | 生成文件数 |',
  '| --- | --- | ---: |',
  ...results.map((item) => `| ${item.id} | ${item.status} | ${item.files.length} |`),
  '',
  '## 说明',
  '',
  '- 这个脚本只尝试生成 HBuilderX App Resource，不会写入证书或账号密码。',
  '- App Resource 不是最终安装包；APK/AAB、IPA/TestFlight、HAP 仍必须回传到 release inbox。',
  '- 如果 HBuilderX 返回“需要先登录”，这是必须你在 HBuilderX 内完成的账号动作。',
  '',
  '## 下一步',
  '',
  ...report.next.map((item) => `- ${item}`),
]
writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

mkdirSync(join(root, 'artifacts', 'hbuilderx-mobile-resources'), { recursive: true })
writeFileSync(join(root, 'artifacts', 'hbuilderx-mobile-resources', 'latest-manifest.json'), `${JSON.stringify({
  generatedAt: report.generatedAt,
  latestPacketDir: rel(outDir),
  report: `${rel(outDir)}/report.json`,
  passed,
  summary,
}, null, 2)}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed,
  summary,
  results: results.map((item) => ({ id: item.id, status: item.status, files: item.files.length })),
}, null, 2))

if (strict && !passed) process.exit(1)
