#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.HBUILDERX_HARMONY_PACK_VERSION || `v${packageJson.version || '0.0.0'}`
const execute = process.argv.includes('--execute') || process.env.HBUILDERX_HARMONY_PACK_EXECUTE === '1'
const strict = process.argv.includes('--strict') || process.env.HBUILDERX_HARMONY_PACK_STRICT === '1'
const timeoutMs = Number(process.env.HBUILDERX_HARMONY_PACK_TIMEOUT_MS || 600000)
const cliPath = process.env.HBUILDERX_CLI || '/Applications/HBuilderX.app/Contents/MacOS/cli'
const outDir = process.env.HBUILDERX_HARMONY_PACK_OUT_DIR || join(root, 'artifacts', 'hbuilderx-harmony-pack-attempts', `${localTimestamp()}-${version}`)

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

function redact(value) {
  return String(value || '')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '<redacted-email>')
    .replace(/(password|passwd|token|secret|certpassword|storepassword|privateKey)(=|:)\s*[^\s"'，,}<>]+/gi, '$1$2 <redacted>')
}

function buildPackArgs() {
  return [
    'pack',
    'app-harmony',
    '--project',
    root,
  ]
}

function stripAnsiAndHtml(value) {
  return String(value || '')
    .replace(/\u001b\[[0-9;]*m/g, '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, '&')
    .trim()
}

function classifyOutput(output, exitCode) {
  const plain = stripAnsiAndHtml(output)
  const blockers = []
  const warnings = []

  const addBlocker = (id, owner, text) => {
    if (!blockers.some((item) => item.id === id)) blockers.push({ id, owner, text })
  }
  const addWarning = (id, text) => {
    if (!warnings.some((item) => item.id === id)) warnings.push({ id, text })
  }

  if (!execute) addWarning('dry-run', '未执行鸿蒙本地打包；设置 HBUILDERX_HARMONY_PACK_EXECUTE=1 或传 --execute 才会调用 HBuilderX pack app-harmony。')
  if (!existsSync(cliPath)) addBlocker('hbuilderx-cli-missing', 'environment-action', `HBuilderX CLI 不存在：${cliPath}`)
  if (exitCode !== 0 && execute) addBlocker('cli-exit-code', 'environment-action', `HBuilderX CLI exitCode=${exitCode}`)
  if (/未检测到鸿蒙工具链|鸿蒙开发者工具路径|DevEco Studio|hdc|hvigor/i.test(plain)) {
    addBlocker('harmony-toolchain-missing', 'environment-action', '鸿蒙本地打包缺少 DevEco Studio/hdc/hvigor，或 HBuilderX 未配置鸿蒙开发者工具路径。')
  }
  if (/包名不能为空|bundleName|packageName/i.test(plain)) {
    addBlocker('harmony-package-name-required', 'environment-action', '鸿蒙本地打包需要有效包名或 bundleName 配置。')
  }
  if (/证书|签名|profile|p12|keystore/i.test(plain)) {
    addBlocker('harmony-signing-required', 'user-last', '鸿蒙最终包需要签名资料或华为后台构建配置；证书不得入库。')
  }
  if (plain.includes('偏好设置')) addWarning('hbuilderx-run-config', '需要在 HBuilderX 偏好设置的运行配置中填写 DevEco Studio 路径。')
  if (/Error|错误|失败/i.test(plain) && blockers.length === 0) addBlocker('hbuilderx-harmony-pack-error', 'environment-action', 'HBuilderX 鸿蒙本地打包返回错误，查看 output.redacted.log。')

  return { plain, blockers, warnings }
}

mkdirSync(outDir, { recursive: true })
const args = buildPackArgs()
const startedAt = new Date().toISOString()
let result = { status: null, signal: null, stdout: '', stderr: '', error: null }

if (execute && existsSync(cliPath)) {
  const spawned = spawnSync(cliPath, args, {
    cwd: root,
    env: {
      ...process.env,
      LANG: 'en_US.UTF-8',
      LC_ALL: 'en_US.UTF-8',
      LC_CTYPE: 'en_US.UTF-8',
    },
    encoding: 'utf8',
    timeout: timeoutMs,
  })
  result = {
    status: spawned.status,
    signal: spawned.signal,
    stdout: spawned.stdout || '',
    stderr: spawned.stderr || '',
    error: spawned.error ? spawned.error.message : null,
  }
}

const finishedAt = new Date().toISOString()
const combinedOutput = redact(`${result.stdout || ''}\n${result.stderr || ''}`)
const classification = classifyOutput(combinedOutput, result.status)
const passed = execute && result.status === 0 && classification.blockers.length === 0
const attempt = {
  generatedAt: finishedAt,
  startedAt,
  finishedAt,
  version,
  platform: 'harmony',
  execute,
  passed,
  cliPath,
  cwd: root,
  timeoutMs,
  command: [cliPath, ...args],
  exitCode: result.status,
  signal: result.signal,
  error: result.error,
  outputPath: rel(join(outDir, 'output.redacted.log')),
  blockers: classification.blockers,
  warnings: classification.warnings,
  next: [
    '先处理 owner=environment-action 的 DevEco Studio、hdc、hvigor 和 HBuilderX 鸿蒙工具路径。',
    '再处理 owner=user-last 的华为开发者账号、签名、AppGallery 后台构建配置。',
    '鸿蒙 HAP/AppGallery 成功后，把 HAP 或后台构建记录放入 artifacts/release-inbox/v1.0.0/harmony/ 并补 build-metadata.json。',
    '证书、签名口令、p12、keystore、华为后台凭据不进入 GitHub。',
  ],
}

writeFileSync(join(outDir, 'attempt.json'), `${JSON.stringify(attempt, null, 2)}\n`)
writeFileSync(join(outDir, 'output.redacted.log'), `${combinedOutput}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# HBuilderX 鸿蒙本地打包尝试',
  '',
  `> 生成时间：${attempt.generatedAt}`,
  `> 执行：${execute ? '是' : '否，dry-run'}`,
  `> 结论：${passed ? '通过' : '未通过'}`,
  '',
  '## 命令',
  '',
  `\`${attempt.command.join(' ')}\``,
  '',
  '## 阻塞',
  '',
  ...(attempt.blockers.length ? attempt.blockers.map((item) => `- ${item.id} / ${item.owner}：${item.text}`) : ['- 暂无阻塞。']),
  '',
  '## 警告',
  '',
  ...(attempt.warnings.length ? attempt.warnings.map((item) => `- ${item.id}：${item.text}`) : ['- 暂无警告。']),
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
  exitCode: result.status,
  blockers: attempt.blockers,
  warnings: attempt.warnings,
}, null, 2))

if (strict && !passed) process.exit(1)
