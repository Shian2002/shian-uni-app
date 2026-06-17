#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync, spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const verifyCurrent = process.argv.includes('--verify-current') || process.env.DESKTOP_WINDOWS_REBUILD_VERIFY_CURRENT === '1'
const skipH5 = process.argv.includes('--skip-h5') || process.env.DESKTOP_WINDOWS_REBUILD_SKIP_H5 === '1'
const timeoutMs = Number(process.env.DESKTOP_WINDOWS_REBUILD_TIMEOUT_MS || 360000)
const packageJson = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'))
const version = process.env.DESKTOP_WINDOWS_REBUILD_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.DESKTOP_WINDOWS_REBUILD_OUT_DIR || join(root, 'artifacts', 'desktop-windows-rebuild', `${localTimestamp()}-${version}`)
const installerPath = 'desktop/release/时安解忧屋 Setup 1.0.0.exe'
const unpackedExePath = 'desktop/release/win-unpacked/时安解忧屋.exe'
const h5IndexPath = 'dist/build/h5/index.html'

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function fileInfo(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return { path, exists: false, bytes: 0, sha256: '', mtime: '', mtimeMs: 0 }
  const stat = statSync(fullPath)
  return {
    path,
    exists: true,
    bytes: stat.size,
    sha256: sha256(fullPath),
    mtime: new Date(stat.mtimeMs).toISOString(),
    mtimeMs: stat.mtimeMs,
  }
}

function runStep(name, command, args, options = {}) {
  const startedAt = new Date().toISOString()
  const result = spawnSync(command, args, {
    cwd: options.cwd || root,
    env: options.env || process.env,
    encoding: 'utf8',
    timeout: options.timeoutMs || timeoutMs,
    maxBuffer: 1024 * 1024 * 24,
  })
  return {
    name,
    command: [command, ...args].join(' '),
    cwd: options.cwd ? rel(options.cwd) : '.',
    startedAt,
    finishedAt: new Date().toISOString(),
    status: result.status,
    signal: result.signal,
    timedOut: Boolean(result.error && result.error.code === 'ETIMEDOUT'),
    ok: result.status === 0 && !result.error,
    stdout: result.stdout || '',
    stderr: result.stderr || (result.error ? result.error.message : ''),
  }
}

function git(args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim()
  } catch (_) {
    return ''
  }
}

mkdirSync(outDir, { recursive: true })

const buildEnv = {
  ...process.env,
  CSC_IDENTITY_AUTO_DISCOVERY: process.env.CSC_IDENTITY_AUTO_DISCOVERY || 'false',
  ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES: process.env.ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES || 'true',
  USE_HARD_LINKS: process.env.USE_HARD_LINKS || 'false',
}

const steps = []
if (!verifyCurrent && !skipH5) {
  steps.push(runStep('build-h5', 'npm', ['run', 'build:h5'], { env: buildEnv, timeoutMs }))
}
if (!verifyCurrent && steps.every((step) => step.ok)) {
  steps.push(runStep('dist-win-x64', 'npm', ['--prefix', 'desktop', 'run', 'dist:win:x64'], { env: buildEnv, timeoutMs }))
}

const h5 = fileInfo(h5IndexPath)
const installer = fileInfo(installerPath)
const unpackedExe = fileInfo(unpackedExePath)
const issues = [
  !h5.exists && `缺少 H5 构建产物: ${h5IndexPath}`,
  !installer.exists && `缺少 Windows NSIS 安装器: ${installerPath}`,
  !unpackedExe.exists && `缺少 Windows unpacked exe: ${unpackedExePath}`,
  installer.exists && h5.exists && installer.mtimeMs < h5.mtimeMs && `Windows 安装器早于最新 H5 构建产物: installer=${installer.mtime} h5=${h5.mtime}`,
  unpackedExe.exists && h5.exists && unpackedExe.mtimeMs < h5.mtimeMs && `Windows unpacked exe 早于最新 H5 构建产物: exe=${unpackedExe.mtime} h5=${h5.mtime}`,
  ...steps.filter((step) => !step.ok).map((step) => `${step.name} 未通过: status=${step.status ?? 'null'} signal=${step.signal || '-'}${step.timedOut ? ' timedOut=true' : ''}`),
].filter(Boolean)

const report = {
  generatedAt: new Date().toISOString(),
  version,
  mode: verifyCurrent ? 'verify-current' : (skipH5 ? 'rebuild-skip-h5' : 'rebuild'),
  timeoutMs,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  env: {
    CSC_IDENTITY_AUTO_DISCOVERY: buildEnv.CSC_IDENTITY_AUTO_DISCOVERY,
    ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES: buildEnv.ELECTRON_BUILDER_ALLOW_UNRESOLVED_DEPENDENCIES,
    ELECTRON_MIRROR: buildEnv.ELECTRON_MIRROR || '',
    USE_HARD_LINKS: buildEnv.USE_HARD_LINKS,
  },
  passed: issues.length === 0,
  files: { h5, installer, unpackedExe },
  steps: steps.map((step) => ({
    ...step,
    stdout: step.stdout.slice(-12000),
    stderr: step.stderr.slice(-12000),
  })),
  issues,
  next: issues.length
    ? [
        '释放至少 8-12GiB 空间后重跑 npm run desktop:build:win:x64:safe。',
        '如果 dist-win-x64 超时，优先在 Windows 10/11 机器或 CI runner 上执行同一命令。',
        '通过后继续执行 npm run desktop:windows-user-packet、npm run desktop:bundle、npm run desktop:release-inbox-sync。',
      ]
    : [
        '继续执行 npm run desktop:windows-user-packet。',
        '继续执行 npm run desktop:bundle。',
        '继续执行 npm run desktop:release-inbox-sync 和 npm run release:try-now。',
      ],
}

writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'build.log'), steps.map((step) => [
  `# ${step.name}`,
  `$ ${step.command}`,
  `status=${step.status ?? 'null'} signal=${step.signal || '-'} timedOut=${step.timedOut}`,
  '## stdout',
  step.stdout,
  '## stderr',
  step.stderr,
  '',
].join('\n')).join('\n'))
writeFileSync(join(outDir, 'README.md'), `${[
  '# Windows x64 安全重建报告',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 模式：${report.mode}`,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  '',
  '## 文件',
  '',
  `- H5：${h5.exists ? `${h5.mtime} sha256=${h5.sha256}` : '缺失'}`,
  `- NSIS：${installer.exists ? `${installer.mtime} sha256=${installer.sha256}` : '缺失'}`,
  `- Unpacked EXE：${unpackedExe.exists ? `${unpackedExe.mtime} sha256=${unpackedExe.sha256}` : '缺失'}`,
  '',
  '## 问题',
  '',
  ...(issues.length ? issues.map((item) => `- ${item}`) : ['- 暂无。']),
  '',
  '## 下一步',
  '',
  ...report.next.map((item) => `- ${item}`),
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  mode: report.mode,
  installer: installer.exists ? { sha256: installer.sha256, mtime: installer.mtime, bytes: installer.bytes } : null,
  issues,
}, null, 2))

if (!report.passed) process.exit(1)
