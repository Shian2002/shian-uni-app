#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { cpSync, existsSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { basename, dirname, join, relative } from 'node:path'
import process from 'node:process'

const root = process.cwd()
const packageJson = JSON.parse(readFileSync(join(root, 'package.json'), 'utf8'))
const version = process.env.DESKTOP_MACOS_REFRESH_VERSION || `v${packageJson.version || '0.0.0'}`
const appDir = process.env.DESKTOP_MACOS_REFRESH_APP || 'desktop/release/mac-arm64/时安解忧屋.app'
const resourcesDir = join(root, appDir, 'Contents', 'Resources')
const asarPath = join(resourcesDir, 'app.asar')
const plistPath = join(root, appDir, 'Contents', 'Info.plist')
const outDir = process.env.DESKTOP_MACOS_REFRESH_OUT_DIR || join(root, 'artifacts', 'desktop-macos-refresh-app-asar', `${localTimestamp()}-${version}`)
const stagingDir = join(outDir, 'asar-root')
const backupDir = join(root, 'artifacts', 'desktop-asar-backups', `${localTimestamp()}-${version}`)
const issues = []
const warnings = []

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

function pathInfo(path, label) {
  if (!existsSync(path)) return { label, path: path.startsWith(root) ? rel(path) : path, exists: false, bytes: 0, sha256: '', mtime: '', mtimeMs: 0 }
  const stat = statSync(path)
  return {
    label,
    path: path.startsWith(root) ? rel(path) : path,
    exists: true,
    kind: stat.isDirectory() ? 'directory' : 'file',
    bytes: stat.isFile() ? stat.size : 0,
    sha256: stat.isFile() ? sha256(path) : '',
    mtime: new Date(stat.mtimeMs).toISOString(),
    mtimeMs: stat.mtimeMs,
  }
}

function git(args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim()
  } catch (_) {
    return ''
  }
}

function copyRequired(source, target, label) {
  const sourcePath = join(root, source)
  const targetPath = join(stagingDir, target)
  if (!existsSync(sourcePath)) {
    issues.push(`缺少 ${label}: ${source}`)
    return
  }
  mkdirSync(dirname(targetPath), { recursive: true })
  cpSync(sourcePath, targetPath, { recursive: true })
}

function backupExistingAsar() {
  if (!existsSync(asarPath)) return null
  mkdirSync(backupDir, { recursive: true })
  const backupPath = join(backupDir, basename(asarPath))
  cpSync(asarPath, backupPath)
  return pathInfo(backupPath, '旧 app.asar 备份')
}

function packAsar() {
  if (process.platform !== 'darwin') {
    issues.push(`当前平台是 ${process.platform}，只能在 macOS 刷新 .app 内的 app.asar。`)
    return null
  }

  const h5Index = join(root, 'dist/build/h5/index.html')
  const asarBin = join(root, 'desktop/node_modules/@electron/asar/bin/asar.js')
  if (!existsSync(join(root, appDir))) issues.push(`缺少 macOS App: ${appDir}`)
  if (!existsSync(h5Index)) issues.push('缺少 H5 构建产物: dist/build/h5/index.html')
  if (!existsSync(asarBin)) issues.push('缺少 @electron/asar，请先执行 npm --prefix desktop install')
  if (issues.length) return null

  rmSync(stagingDir, { recursive: true, force: true })
  mkdirSync(stagingDir, { recursive: true })
  copyRequired('desktop/main.js', 'main.js', '桌面主进程')
  copyRequired('desktop/preload.js', 'preload.js', '桌面 preload')
  copyRequired('desktop/package.json', 'package.json', '桌面 package.json')
  copyRequired('desktop/assets', 'assets', '桌面图标资源')
  copyRequired('dist/build/h5', 'app', '最新 H5 构建产物')
  if (issues.length) return null

  const backup = backupExistingAsar()
  execFileSync(process.execPath, [asarBin, 'pack', stagingDir, asarPath], {
    cwd: root,
    stdio: ['ignore', 'pipe', 'pipe'],
  })

  const newAsar = pathInfo(asarPath, '新 app.asar')
  const integrity = updateAsarIntegrity(newAsar.sha256)
  const h5 = pathInfo(h5Index, 'H5 index.html')
  if (newAsar.mtimeMs < h5.mtimeMs) {
    warnings.push(`新 app.asar 时间早于 H5，可能是文件系统时间精度导致: asar=${newAsar.mtime} h5=${h5.mtime}`)
  }

  return {
    app: pathInfo(join(root, appDir), 'macOS App'),
    h5,
    desktopMain: pathInfo(join(root, 'desktop/main.js'), 'desktop/main.js'),
    newAsar,
    integrity,
    backup,
  }
}

function updateAsarIntegrity(hash) {
  if (!hash || !existsSync(plistPath)) {
    warnings.push('未更新 ElectronAsarIntegrity：缺少 app.asar hash 或 Info.plist。')
    return { updated: false, plist: pathInfo(plistPath, 'Info.plist'), hash: '' }
  }
  try {
    execFileSync('/usr/libexec/PlistBuddy', ['-c', `Set :ElectronAsarIntegrity:Resources/app.asar:hash ${hash}`, plistPath], {
      cwd: root,
      stdio: ['ignore', 'pipe', 'pipe'],
    })
    return { updated: true, plist: pathInfo(plistPath, 'Info.plist'), hash }
  } catch (error) {
    warnings.push(`无法更新 ElectronAsarIntegrity hash: ${String(error.stderr || error.message).trim()}`)
    return { updated: false, plist: pathInfo(plistPath, 'Info.plist'), hash: '' }
  }
}

mkdirSync(outDir, { recursive: true })
const result = packAsar()

const report = {
  generatedAt: new Date().toISOString(),
  version,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  appDir,
  passed: Boolean(result?.newAsar?.exists) && issues.length === 0,
  result,
  issues,
  warnings,
}

writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# macOS app.asar 刷新记录',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> App：\`${appDir}\``,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  '',
  '## 文件',
  '',
  `- H5：\`${result?.h5?.path || '缺失'}\` ${result?.h5?.sha256 || ''}`,
  `- 新 app.asar：\`${result?.newAsar?.path || '缺失'}\` ${result?.newAsar?.sha256 || ''}`,
  `- Info.plist integrity：${result?.integrity?.updated ? result.integrity.hash : '未更新'}`,
  `- 旧 app.asar 备份：\`${result?.backup?.path || '无'}\``,
  '',
  '## 问题',
  '',
  ...(issues.length ? issues.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 警告',
  '',
  ...(warnings.length ? warnings.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 说明',
  '',
  '- 这个脚本只刷新现有 macOS `.app` 内的前端资源，不重新下载 Electron。',
  '- 刷新后还需要执行 `npm run desktop:make-macos-dmg` 重新生成 DMG。',
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  appAsar: result?.newAsar ? { path: result.newAsar.path, sha256: result.newAsar.sha256, bytes: result.newAsar.bytes } : null,
  backup: result?.backup?.path || '',
  issues,
  warnings,
}, null, 2))

if (!report.passed) process.exit(1)
