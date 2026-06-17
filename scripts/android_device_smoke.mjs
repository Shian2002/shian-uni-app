#!/usr/bin/env node

import { execFileSync, spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'))
const version = process.env.ANDROID_DEVICE_SMOKE_VERSION || `v${packageJson.version || '0.0.0'}`
const strict = process.argv.includes('--strict') || process.env.ANDROID_DEVICE_SMOKE_STRICT === '1'
const outDir = process.env.ANDROID_DEVICE_SMOKE_OUT_DIR || join(root, 'artifacts', 'android-device-smoke', `${localTimestamp()}-${version}`)
const apkPath = process.env.ANDROID_DEVICE_SMOKE_APK || join(root, 'artifacts', 'release-inbox', version, 'android', `shian-${version}-android-debug-shell.apk`)
const metadataPath = join(root, 'artifacts', 'release-inbox', version, 'android', 'build-metadata.json')
const packageName = 'com.shian.xuanctai'
const activityName = 'com.shian.xuanctai/.MainActivity'
const androidHome = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT || '/opt/homebrew/share/android-commandlinetools'
const toolEnv = {
  ...process.env,
  ANDROID_HOME: androidHome,
  ANDROID_SDK_ROOT: androidHome,
  PATH: [
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

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: options.cwd || root,
    env: toolEnv,
    encoding: 'utf8',
    timeout: Number(process.env.ANDROID_DEVICE_SMOKE_TIMEOUT_MS || options.timeoutMs || 120000),
    maxBuffer: 1024 * 1024 * 12,
  })
  return {
    command: [command, ...args].join(' '),
    status: result.status,
    signal: result.signal,
    ok: result.status === 0 && !result.error,
    stdout: String(result.stdout || '').trim(),
    stderr: String(result.stderr || (result.error ? result.error.message : '')).trim(),
  }
}

function adb(args, options = {}) {
  return run('adb', args, options)
}

function readJson(path) {
  if (!existsSync(path)) return null
  try {
    return JSON.parse(readFileSync(path, 'utf8'))
  } catch (_) {
    return null
  }
}

function writeJson(path, data) {
  writeFileSync(path, `${JSON.stringify(data, null, 2)}\n`)
}

function parseDevices(output) {
  return output
    .split('\n')
    .slice(1)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const [serial, state] = line.split(/\s+/)
      return { serial, state }
    })
    .filter((item) => item.serial)
}

function fileEvidence(path) {
  if (!existsSync(path)) return null
  const stat = statSync(path)
  return { path: rel(path), bytes: stat.size, mtime: new Date(stat.mtimeMs).toISOString() }
}

function appendMetadataEvidence(evidencePaths) {
  const metadata = readJson(metadataPath)
  if (!metadata) return false
  const current = Array.isArray(metadata.deviceTestEvidence) ? metadata.deviceTestEvidence : []
  metadata.deviceTestEvidence = Array.from(new Set([...current, ...evidencePaths]))
  metadata.deviceTestedAt = new Date().toISOString()
  metadata.deviceSmokeStatus = 'passed'
  writeJson(metadataPath, metadata)
  return true
}

mkdirSync(outDir, { recursive: true })

const steps = []
const issues = []
const warnings = []

if (!existsSync(apkPath)) issues.push(`缺少 Android APK: ${rel(apkPath)}`)

const adbDevices = adb(['devices'])
steps.push({ name: 'adb-devices', ...adbDevices })
const devices = adbDevices.ok ? parseDevices(adbDevices.stdout) : []
const readyDevices = devices.filter((item) => item.state === 'device')
const blockedDevices = devices.filter((item) => item.state !== 'device')
if (blockedDevices.length) {
  warnings.push(`检测到未就绪设备: ${blockedDevices.map((item) => `${item.serial}:${item.state}`).join(', ')}`)
}

let status = 'no-device'
let selectedDevice = null
let screenshot = null
let deviceInfo = {}
let metadataUpdated = false

if (!issues.length && readyDevices.length) {
  selectedDevice = readyDevices[0]
  status = 'running'
  const serialArgs = ['-s', selectedDevice.serial]
  const install = adb([...serialArgs, 'install', '-r', apkPath], { timeoutMs: 180000 })
  steps.push({ name: 'adb-install', ...install })
  if (!install.ok) issues.push('adb install 未通过')

  const start = adb([...serialArgs, 'shell', 'am', 'start', '-n', activityName])
  steps.push({ name: 'adb-start', ...start })
  if (!start.ok) issues.push('adb 启动 MainActivity 未通过')

  const brand = adb([...serialArgs, 'shell', 'getprop', 'ro.product.brand'])
  const model = adb([...serialArgs, 'shell', 'getprop', 'ro.product.model'])
  const release = adb([...serialArgs, 'shell', 'getprop', 'ro.build.version.release'])
  const sdk = adb([...serialArgs, 'shell', 'getprop', 'ro.build.version.sdk'])
  steps.push({ name: 'device-brand', ...brand })
  steps.push({ name: 'device-model', ...model })
  steps.push({ name: 'device-android-release', ...release })
  steps.push({ name: 'device-android-sdk', ...sdk })
  deviceInfo = {
    serial: selectedDevice.serial,
    brand: brand.stdout,
    model: model.stdout,
    androidRelease: release.stdout,
    androidSdk: sdk.stdout,
  }

  const remoteScreenshot = '/sdcard/shian-device-smoke.png'
  const screenCapture = adb([...serialArgs, 'shell', 'screencap', '-p', remoteScreenshot])
  steps.push({ name: 'adb-screencap', ...screenCapture })
  const localScreenshot = join(outDir, 'android-device-agent.png')
  const pull = adb([...serialArgs, 'pull', remoteScreenshot, localScreenshot])
  steps.push({ name: 'adb-pull-screenshot', ...pull })
  if (pull.ok && existsSync(localScreenshot)) screenshot = fileEvidence(localScreenshot)
  else warnings.push('未能拉取安卓设备截图')

  if (!issues.length && screenshot) {
    const reportPath = join(outDir, 'report.json')
    metadataUpdated = appendMetadataEvidence([rel(reportPath), screenshot.path])
  }
}

if (!readyDevices.length && !issues.length) {
  warnings.push('未检测到 adb device 状态的安卓设备；连接真机并开启 USB 调试后重跑 npm run android:device-smoke。')
}

if (issues.length) status = 'failed'
else if (readyDevices.length && screenshot) status = 'passed'

const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  status,
  passed: status === 'passed',
  apk: fileEvidence(apkPath),
  packageName,
  activityName,
  devices,
  selectedDevice,
  deviceInfo,
  screenshot,
  metadataPath: rel(metadataPath),
  metadataUpdated,
  steps: steps.map((step) => ({
    ...step,
    stdout: step.stdout.slice(-8000),
    stderr: step.stderr.slice(-8000),
  })),
  issues,
  warnings,
  outDir: rel(outDir),
}
writeJson(join(outDir, 'report.json'), report)
writeFileSync(join(outDir, 'README.md'), `${[
  '# Android 真机安装验收',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 状态：${status}`,
  `> APK：${report.apk ? `\`${report.apk.path}\`` : '缺失'}`,
  `> 设备：${selectedDevice ? `\`${selectedDevice.serial}\`` : '未连接'}`,
  '',
  '## 结果',
  '',
  `- 安装并启动：${status === 'passed' ? '通过' : '未通过或未执行'}`,
  `- 截图：${screenshot ? `\`${screenshot.path}\`` : '缺失'}`,
  `- 元数据回填：${metadataUpdated ? '已更新 deviceTestEvidence' : '未更新'}`,
  '',
  '## 缺口',
  '',
  ...(issues.length ? issues.map((item) => `- ${item}`) : ['- 无结构性错误。']),
  '',
  '## 警告',
  '',
  ...(warnings.length ? warnings.map((item) => `- ${item}`) : ['- 无警告。']),
  '',
  '## 使用规则',
  '',
  '- 连接安卓真机并开启 USB 调试后运行 `npm run android:device-smoke`。',
  '- 默认无设备不失败，只产出 no-device 报告；正式候选前运行 `npm run android:device-smoke -- --strict`。',
  '- 该脚本只验证安装、启动和截图；登录、积分、时安 agent、账号注销仍需人工按截图规范补齐。',
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: report.outDir,
  status,
  passed: report.passed,
  selectedDevice,
  screenshot: screenshot?.path || '',
  metadataUpdated,
  issues,
  warnings,
}, null, 2))

if (strict && !report.passed) process.exit(1)
