#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, statSync, symlinkSync, writeFileSync } from 'node:fs'
import { basename, join, relative } from 'node:path'
import process from 'node:process'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.DESKTOP_MACOS_DMG_VERSION || packageJson.version || '0.0.0'
const sourceApp = process.env.DESKTOP_MACOS_DMG_SOURCE_APP || 'desktop/release/mac-arm64/时安解忧屋.app'
const dmgPath = process.env.DESKTOP_MACOS_DMG_OUTPUT || `desktop/release/时安解忧屋-${version}-arm64.dmg`
const volumeName = process.env.DESKTOP_MACOS_DMG_VOLUME || '时安解忧屋'
const outDir = process.env.DESKTOP_MACOS_DMG_REPORT_DIR || join(root, 'artifacts', 'desktop-macos-dmg-from-app', `${localTimestamp()}-v${version}`)
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

function pathInfo(path, label) {
  if (!existsSync(path)) return null
  const stat = statSync(path)
  return {
    label,
    path: path.startsWith(root) ? rel(path) : path,
    kind: stat.isDirectory() ? 'directory' : 'file',
    bytes: stat.isFile() ? stat.size : 0,
    mtime: new Date(stat.mtimeMs).toISOString(),
    sha256: stat.isFile() ? sha256(path) : '',
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

function backupExistingDmg(targetPath) {
  if (!existsSync(targetPath)) return null
  const backupDir = join(root, 'artifacts', 'desktop-dmg-backups', `${localTimestamp()}-v${version}`)
  mkdirSync(backupDir, { recursive: true })
  const backupPath = join(backupDir, basename(targetPath))
  copyFileSync(targetPath, backupPath)
  return pathInfo(backupPath, '旧 DMG 备份')
}

function makeDmg() {
  if (process.platform !== 'darwin') {
    issues.push(`当前平台是 ${process.platform}，只能在 macOS 使用 hdiutil 生成 DMG。`)
    return null
  }

  const sourcePath = join(root, sourceApp)
  const targetPath = join(root, dmgPath)
  if (!existsSync(sourcePath)) {
    issues.push(`缺少源 App: ${sourceApp}`)
    return null
  }

  const plistPath = join(sourcePath, 'Contents', 'Info.plist')
  const executablePath = join(sourcePath, 'Contents', 'MacOS', '时安解忧屋')
  const iconPath = join(sourcePath, 'Contents', 'Resources', 'icon.icns')
  const asarPath = join(sourcePath, 'Contents', 'Resources', 'app.asar')
  for (const [path, label] of [
    [plistPath, 'Info.plist'],
    [executablePath, '主可执行文件'],
    [iconPath, '图标 icon.icns'],
    [asarPath, 'app.asar'],
  ]) {
    if (!existsSync(path)) issues.push(`源 App 缺少 ${label}: ${path}`)
  }
  if (issues.length) return null

  const bundleName = plistValue(plistPath, 'CFBundleName')
  const bundleExecutable = plistValue(plistPath, 'CFBundleExecutable')
  const iconFile = plistValue(plistPath, 'CFBundleIconFile')
  if (bundleName !== '时安解忧屋') issues.push(`CFBundleName 应为 时安解忧屋，实际: ${bundleName || '缺失'}`)
  if (bundleExecutable !== '时安解忧屋') issues.push(`CFBundleExecutable 应为 时安解忧屋，实际: ${bundleExecutable || '缺失'}`)
  if (iconFile !== 'icon.icns') issues.push(`CFBundleIconFile 应为 icon.icns，实际: ${iconFile || '缺失'}`)
  if (issues.length) return null

  const staging = join(outDir, 'dmg-root')
  rmSync(staging, { recursive: true, force: true })
  mkdirSync(staging, { recursive: true })
  run('ditto', [sourcePath, join(staging, '时安解忧屋.app')])
  try {
    symlinkSync('/Applications', join(staging, 'Applications'))
  } catch (_) {
    warnings.push('无法创建 Applications 快捷方式；DMG 仍包含 App，可手动拖到 /Applications。')
  }

  mkdirSync(join(targetPath, '..'), { recursive: true })
  const backup = backupExistingDmg(targetPath)
  run('hdiutil', [
    'create',
    '-volname', volumeName,
    '-srcfolder', staging,
    '-ov',
    '-format', 'UDZO',
    targetPath,
  ])
  run('hdiutil', ['verify', targetPath])
  rmSync(staging, { recursive: true, force: true })

  return {
    sourceApp: pathInfo(sourcePath, '源 App'),
    dmg: pathInfo(targetPath, '生成 DMG'),
    backup,
    plist: {
      CFBundleName: bundleName,
      CFBundleExecutable: bundleExecutable,
      CFBundleIconFile: iconFile,
    },
    embedded: {
      appAsar: pathInfo(asarPath, '源 app.asar'),
      icon: pathInfo(iconPath, '源 icon.icns'),
    },
  }
}

mkdirSync(outDir, { recursive: true })
const result = makeDmg()

const report = {
  generatedAt: new Date().toISOString(),
  version: `v${version}`,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  sourceApp,
  dmgPath,
  volumeName,
  passed: Boolean(result?.dmg) && issues.length === 0,
  unsignedNotice: '当前 DMG 内 App 未签名、未公证，只能作为本人或内部测试包；正式公开前必须补 Apple Developer ID 签名和 notarization。',
  result,
  issues,
  warnings,
}

writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# macOS DMG 生成记录',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 源 App：\`${sourceApp}\``,
  `> DMG：\`${dmgPath}\``,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  '',
  '## 文件',
  '',
  `- DMG：\`${result?.dmg?.path || '缺失'}\``,
  `- SHA256：\`${result?.dmg?.sha256 || '缺失'}\``,
  `- 源 app.asar：\`${result?.embedded?.appAsar?.path || '缺失'}\``,
  `- 源图标：\`${result?.embedded?.icon?.path || '缺失'}\``,
  '',
  '## 问题',
  '',
  ...(issues.length ? issues.map((item) => `- ${item}`) : ['- 无结构性问题。']),
  '',
  '## 警告',
  '',
  ...(warnings.length ? warnings.map((item) => `- ${item}`) : ['- 无警告。']),
  '',
  '## 说明',
  '',
  '- 这个脚本只从当前 `.app` 生成 DMG，不重新下载 Electron。',
  '- 正式公开下载前仍要补 Apple Developer ID 签名和 notarization。',
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  dmgPath,
  sha256: result?.dmg?.sha256 || '',
  backup: result?.backup?.path || '',
  issues,
  warnings,
}, null, 2))

if (!report.passed) process.exit(1)
