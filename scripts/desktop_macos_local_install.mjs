#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import process from 'node:process'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.DESKTOP_MACOS_LOCAL_INSTALL_VERSION || `v${packageJson.version || '0.0.0'}`
const sourceApp = process.env.DESKTOP_MACOS_LOCAL_INSTALL_SOURCE || 'desktop/release/mac-arm64/时安解忧屋.app'
const targetApp = process.env.DESKTOP_MACOS_LOCAL_INSTALL_TARGET || '/Applications/时安解忧屋.app'
const outDir = process.env.DESKTOP_MACOS_LOCAL_INSTALL_OUT_DIR || join(root, 'artifacts', 'desktop-macos-local-install', `${localTimestamp()}-${version}`)
const issues = []
const warnings = []

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

function run(command, args, options = {}) {
  return execFileSync(command, args, {
    cwd: root,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    ...options,
  }).trim()
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function pathEvidence(path, label) {
  if (!existsSync(path)) {
    issues.push(`缺少 ${label}: ${path}`)
    return null
  }
  const stat = statSync(path)
  return {
    label,
    path: path.startsWith(root) ? rel(path) : path,
    kind: stat.isDirectory() ? 'directory' : 'file',
    bytes: stat.isFile() ? stat.size : 0,
  }
}

function plistValue(plist, key) {
  try {
    return run('plutil', ['-extract', key, 'raw', plist])
  } catch (error) {
    warnings.push(`无法读取 Info.plist ${key}: ${error.message}`)
    return ''
  }
}

function fileHash(path) {
  return existsSync(path) && statSync(path).isFile() ? sha256(path) : ''
}

function installApp() {
  if (process.platform !== 'darwin') {
    issues.push(`当前平台是 ${process.platform}，只能在 macOS 安装到 /Applications。`)
    return { installed: false, checks: [] }
  }

  const sourcePath = join(root, sourceApp)
  const targetPath = targetApp
  const checks = []
  checks.push(pathEvidence(sourcePath, '源 App'))
  if (!existsSync(sourcePath)) return { installed: false, checks: checks.filter(Boolean) }

  try {
    run('osascript', ['-e', 'tell application "时安解忧屋" to quit'])
  } catch (_) {}

  rmSync(targetPath, { recursive: true, force: true })
  mkdirSync(join(targetPath, '..'), { recursive: true })
  run('ditto', [sourcePath, targetPath])

  const plistPath = join(targetPath, 'Contents', 'Info.plist')
  const executablePath = join(targetPath, 'Contents', 'MacOS', '时安解忧屋')
  const iconPath = join(targetPath, 'Contents', 'Resources', 'icon.icns')
  checks.push(pathEvidence(targetPath, '已安装 App'))
  checks.push(pathEvidence(plistPath, 'Info.plist'))
  checks.push(pathEvidence(executablePath, '主可执行文件'))
  checks.push(pathEvidence(iconPath, 'App 图标 icon.icns'))

  const bundleName = existsSync(plistPath) ? plistValue(plistPath, 'CFBundleName') : ''
  const bundleExecutable = existsSync(plistPath) ? plistValue(plistPath, 'CFBundleExecutable') : ''
  const iconFile = existsSync(plistPath) ? plistValue(plistPath, 'CFBundleIconFile') : ''
  if (bundleName !== '时安解忧屋') issues.push(`CFBundleName 应为 时安解忧屋，实际: ${bundleName || '缺失'}`)
  if (bundleExecutable !== '时安解忧屋') issues.push(`CFBundleExecutable 应为 时安解忧屋，实际: ${bundleExecutable || '缺失'}`)
  if (iconFile !== 'icon.icns') issues.push(`CFBundleIconFile 应为 icon.icns，实际: ${iconFile || '缺失'}`)

  try {
    run('codesign', ['--verify', '--deep', '--strict', targetPath])
  } catch (_) {
    warnings.push('已安装 App 未通过 codesign strict 校验；这是未签名测试包，正式公开前仍需 Developer ID 签名和 notarization。')
  }

  return {
    installed: issues.length === 0,
    sourceApp,
    targetApp,
    executablePath,
    executableSha256: fileHash(executablePath),
    plist: {
      CFBundleName: bundleName,
      CFBundleExecutable: bundleExecutable,
      CFBundleIconFile: iconFile,
    },
    checks: checks.filter(Boolean),
  }
}

mkdirSync(outDir, { recursive: true })
const result = installApp()

const report = {
  generatedAt: new Date().toISOString(),
  version,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  platform: process.platform,
  sourceApp,
  targetApp,
  passed: result.installed === true && issues.length === 0,
  result,
  issues,
  warnings,
}
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

const lines = [
  '# macOS 本机安装记录',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 源 App：\`${sourceApp}\``,
  `> 安装位置：\`${targetApp}\``,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  '',
  '## 检查项',
  '',
  '| 项目 | 路径 | 类型 | Bytes |',
  '| --- | --- | --- | ---: |',
  ...result.checks.map((item) => `| ${item.label} | \`${item.path}\` | ${item.kind} | ${item.bytes || 0} |`),
  '',
  '## Info.plist',
  '',
  `- CFBundleName：${result.plist?.CFBundleName || '-'}`,
  `- CFBundleExecutable：${result.plist?.CFBundleExecutable || '-'}`,
  `- CFBundleIconFile：${result.plist?.CFBundleIconFile || '-'}`,
  '',
  '## 问题',
  '',
  ...(issues.length ? issues.map((issue) => `- ${issue}`) : ['- 无结构性问题。']),
  '',
  '## 警告',
  '',
  ...(warnings.length ? warnings.map((warning) => `- ${warning}`) : ['- 无警告。']),
  '',
  '## 说明',
  '',
  '- 本脚本只安装本机测试 App，不签名、不公证、不提交 GitHub Release。',
  '- 安装后可从 Launchpad、Finder 或 `/Applications/时安解忧屋.app` 打开。',
]
writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  targetApp,
  executablePath: result.executablePath || '',
  issues,
  warnings,
}, null, 2))

if (!report.passed) process.exit(1)
