#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync, spawnSync } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'))
const version = process.env.ANDROID_DEBUG_SHELL_VERSION || `v${packageJson.version || '0.0.0'}`
const versionName = packageJson.version || '1.0.0'
const outDir = process.env.ANDROID_DEBUG_SHELL_OUT_DIR || join(root, 'artifacts', 'android-debug-shell', `${localTimestamp()}-${version}`)
const shellDir = join(root, 'android-shell')
const sourceApk = join(shellDir, 'app', 'build', 'outputs', 'apk', 'debug', 'app-debug.apk')
const sourceAab = join(shellDir, 'app', 'build', 'outputs', 'bundle', 'debug', 'app-debug.aab')
const inboxDir = join(root, 'artifacts', 'release-inbox', version, 'android')
const inboxApk = join(inboxDir, `shian-${version}-android-debug-shell.apk`)
const inboxAab = join(inboxDir, `shian-${version}-android-debug-shell.aab`)
const javaHome = process.env.JAVA_HOME || '/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home'
const androidHome = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT || '/opt/homebrew/share/android-commandlinetools'
const gradleUserHome = process.env.GRADLE_USER_HOME || '/private/tmp/xuan-gradle-home'
const gradleTmp = process.env.XUAN_GRADLE_TMP || '/private/tmp/xuan-gradle-tmp'
const gradleOpts = [
  process.env.GRADLE_OPTS || '',
  `-Djava.io.tmpdir=${gradleTmp}`,
  '-Dorg.gradle.vfs.watch=false',
].filter(Boolean).join(' ')
const toolEnv = {
  ...process.env,
  JAVA_HOME: javaHome,
  ANDROID_HOME: androidHome,
  ANDROID_SDK_ROOT: androidHome,
  GRADLE_USER_HOME: gradleUserHome,
  GRADLE_OPTS: gradleOpts,
  PATH: [
    join(javaHome, 'bin'),
    join(androidHome, 'platform-tools'),
    join(androidHome, 'cmdline-tools', 'latest', 'bin'),
    '/opt/homebrew/bin',
    process.env.PATH || '',
  ].join(':'),
}

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
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

function fileEvidence(path) {
  if (!existsSync(path)) return null
  const stat = statSync(path)
  return {
    path: rel(path),
    bytes: stat.size,
    sha256: sha256(path),
    mtime: new Date(stat.mtimeMs).toISOString(),
  }
}

function readJson(path) {
  if (!existsSync(path)) return null
  try {
    return JSON.parse(readFileSync(path, 'utf8'))
  } catch (_) {
    return null
  }
}

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function latestReportDirWith(path, filename, predicate = () => true) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory() && existsSync(join(root, item.reportPath)))
    .sort((a, b) => {
      const byReportTime = reportTime(b.reportPath) - reportTime(a.reportPath)
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const dir of dirs) {
    const data = readJson(join(root, dir.reportPath))
    if (predicate(data)) return join(path, dir.name)
  }
  return ''
}

function runStep(name, command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || root,
    env: toolEnv,
    encoding: 'utf8',
    timeout: Number(process.env.ANDROID_DEBUG_SHELL_TIMEOUT_MS || 600000),
    maxBuffer: 1024 * 1024 * 24,
  })
  return {
    name,
    command: [command, ...args].join(' '),
    cwd: rel(options.cwd || root),
    status: result.status,
    signal: result.signal,
    ok: result.status === 0 && !result.error,
    stdout: result.stdout || '',
    stderr: result.stderr || (result.error ? result.error.message : ''),
  }
}

mkdirSync(outDir, { recursive: true })
mkdirSync(inboxDir, { recursive: true })
mkdirSync(gradleUserHome, { recursive: true })
mkdirSync(gradleTmp, { recursive: true })
writeFileSync(join(shellDir, 'local.properties'), `sdk.dir=${androidHome}\n`)

const steps = [
  runStep('gradle-assemble-debug', 'gradle', ['-p', shellDir, ':app:assembleDebug', '--no-daemon', '--no-watch-fs']),
]
if (steps.every((step) => step.ok)) {
  steps.push(runStep('gradle-bundle-debug', 'gradle', ['-p', shellDir, ':app:bundleDebug', '--no-daemon', '--no-watch-fs']))
}
const issues = steps.filter((step) => !step.ok).map((step) => `${step.name} 未通过: status=${step.status ?? 'null'} signal=${step.signal || '-'}`)
const buildSucceeded = steps.every((step) => step.ok)

if (!buildSucceeded) {
  issues.push('Gradle 构建未全部通过，已跳过复制旧 APK/AAB 到 release inbox')
} else if (!existsSync(sourceApk)) {
  issues.push(`缺少 Android debug APK: ${rel(sourceApk)}`)
} else {
  copyFileSync(sourceApk, inboxApk)
}
if (!buildSucceeded) {
  // 上面已经记录跳过原因，这里不重复追加 issue。
} else if (!existsSync(sourceAab)) {
  issues.push(`缺少 Android debug AAB: ${rel(sourceAab)}`)
} else {
  copyFileSync(sourceAab, inboxAab)
}

const apkEvidence = fileEvidence(inboxApk)
const aabEvidence = fileEvidence(inboxAab)
const report = {
  generatedAt: new Date().toISOString(),
  version,
  passed: issues.length === 0,
  androidShell: 'android-shell',
  releaseInbox: rel(inboxDir),
  apk: apkEvidence,
  aab: aabEvidence,
  metadataPath: rel(join(inboxDir, 'build-metadata.json')),
  env: {
    JAVA_HOME: javaHome,
    ANDROID_HOME: androidHome,
    GRADLE_USER_HOME: gradleUserHome,
    XUAN_GRADLE_TMP: gradleTmp,
  },
  steps: steps.map((step) => ({
    ...step,
    stdout: step.stdout.slice(-12000),
    stderr: step.stderr.slice(-12000),
  })),
  issues,
}
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# Android 调试壳 APK 构建报告',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  `> APK：${apkEvidence ? `\`${apkEvidence.path}\`` : '缺失'}`,
  `> APK SHA-256：${apkEvidence?.sha256 || '-'}`,
  `> AAB：${aabEvidence ? `\`${aabEvidence.path}\`` : '缺失'}`,
  `> AAB SHA-256：${aabEvidence?.sha256 || '-'}`,
  '',
  '## 用途',
  '',
  '- APK 先给 Android 真机安装和线上功能回归使用。',
  '- AAB 先给 Android App Bundle 产物结构和 release inbox 流程预检使用。',
  '- 验证登录、积分中心、时安 agent、账号注销等线上路径是否能请求后端。',
  '- 不是正式商店包，不替代 HBuilderX/DCloud 正式签名 APK/AAB。',
  '',
  '## 问题',
  '',
  ...(issues.length ? issues.map((item) => `- ${item}`) : ['- 暂无。']),
].join('\n')}\n`)

if (report.passed) {
  const mobileApiEvidence = latestReportDirWith(
    'artifacts/mobile-api-evidence',
    'manifest.json',
    (data) => data?.passed === true
  )
  const desktopOnlineLoginSmoke = latestReportDirWith(
    'artifacts/desktop-online-login-smoke',
    'report.json',
    (data) => data?.passed === true &&
      (data.checks || []).some((item) => item.name === 'membership' && item.schemaReady === true) &&
      (data.checks || []).some((item) => item.name === 'comprehensive-guide' && item.schemaReady === true)
  )
  const metadata = {
    versionName,
    versionCode: 100,
    packageName: 'com.shian.xuanctai',
    commit: git(['rev-parse', 'HEAD']) || '',
    buildTool: 'android-shell gradle debug',
    builder: 'local-android-debug-shell',
    builtAt: new Date().toISOString(),
    artifactPath: apkEvidence?.path || rel(inboxApk),
    artifactSha256: apkEvidence?.sha256 || '',
    secondaryArtifacts: [
      aabEvidence && {
        kind: 'aab',
        path: aabEvidence.path,
        sha256: aabEvidence.sha256,
        bytes: aabEvidence.bytes,
        signingStatus: 'debug-signing-only',
      },
    ].filter(Boolean),
    channel: 'debug-shell',
    codeSigningStatus: 'debug-signing-only',
    distributionStatus: 'internal-test-only',
    startUrl: 'https://shianjieyouwu.com/#/?app=1',
    iconSource: 'src/static/app-icons',
    reviewAccountDelivery: 'not-in-metadata-use-secure-channel',
    buildEvidence: [
      rel(join(outDir, 'report.json')),
      rel(join(outDir, 'README.md')),
    ],
    automatedEvidence: [
      'tests/android_debug_shell_test.py',
      'tests/app_icon_assets_test.py',
    ],
    mobileRuntimeEvidence: [
      mobileApiEvidence && `${mobileApiEvidence}/manifest.json`,
    ].filter(Boolean),
    sharedBackendContractEvidence: [
      desktopOnlineLoginSmoke && `${desktopOnlineLoginSmoke}/report.json`,
    ].filter(Boolean),
    deviceTestEvidence: [],
    notes: [
      '这是 HBuilderX/DCloud 发行权限恢复前的 Android 调试壳 APK/AAB。',
      'APK 用于真机安装、登录、积分、时安 agent 在线功能回归；AAB 用于提前验证 Android App Bundle 产物结构。',
      'buildEvidence/automatedEvidence 只证明构建和静态检查，不替代 deviceTestEvidence 真机验收。',
      'mobileRuntimeEvidence/sharedBackendContractEvidence 证明打包输入和线上后端契约可用，不替代 Android 真机安装、登录和功能回归。',
      '不是应用商店正式 APK/AAB；正式上架仍需渠道签名、隐私合规检测、真机截图和商店后台证据。',
    ],
  }
  writeFileSync(join(inboxDir, 'build-metadata.json'), `${JSON.stringify(metadata, null, 2)}\n`)
}

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  apk: apkEvidence,
  aab: aabEvidence,
  metadataPath: report.metadataPath,
  issues,
}, null, 2))

if (!report.passed) process.exit(1)
