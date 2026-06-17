#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { basename, join, relative } from 'node:path'
import process from 'node:process'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.DESKTOP_MACOS_VERIFY_VERSION || `v${packageJson.version || '0.0.0'}`
const dmgPath = process.env.DESKTOP_MACOS_DMG || 'desktop/release/时安解忧屋-1.0.0-arm64.dmg'
const appName = process.env.DESKTOP_MACOS_APP_NAME || '时安解忧屋.app'
const outDir = process.env.DESKTOP_MACOS_VERIFY_OUT_DIR || join(root, 'artifacts', 'desktop-macos-install', `${localTimestamp()}-${version}`)
const mountPoint = join(outDir, 'mount')
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

function fileEvidence(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const stat = statSync(fullPath)
  return { path, bytes: stat.size, sha256: sha256(fullPath) }
}

function mountedPath(...parts) {
  return join(mountPoint, ...parts)
}

function pathEvidence(path, label) {
  if (!existsSync(path)) {
    issues.push(`缺少 ${label}: ${path}`)
    return null
  }
  const stat = statSync(path)
  return {
    label,
    path: rel(path),
    bytes: stat.isFile() ? stat.size : 0,
    kind: stat.isDirectory() ? 'directory' : 'file',
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

function verifyMacosDmg() {
  if (process.platform !== 'darwin') {
    return {
      skipped: true,
      skipReason: `当前平台是 ${process.platform}，只有 macOS 能使用 hdiutil 只读挂载 DMG。`,
      checks: [],
    }
  }

  const dmgEvidence = fileEvidence(dmgPath)
  if (!dmgEvidence) {
    issues.push(`缺少 DMG: ${dmgPath}`)
    return { skipped: false, checks: [] }
  }

  mkdirSync(mountPoint, { recursive: true })
  let attached = false
  const checks = [{ label: 'DMG 文件', ...dmgEvidence }]

  try {
    run('hdiutil', ['attach', join(root, dmgPath), '-readonly', '-nobrowse', '-mountpoint', mountPoint])
    attached = true

    const appPath = mountedPath(appName)
    const contentsPath = join(appPath, 'Contents')
    const plistPath = join(contentsPath, 'Info.plist')
    const executablePath = join(contentsPath, 'MacOS', '时安解忧屋')
    const resourcesIconPath = join(contentsPath, 'Resources', 'icon.icns')
    const appAsarPath = join(contentsPath, 'Resources', 'app.asar')

    checks.push(pathEvidence(appPath, 'DMG 内 App'))
    checks.push(pathEvidence(plistPath, 'Info.plist'))
    checks.push(pathEvidence(executablePath, '主可执行文件'))
    checks.push(pathEvidence(resourcesIconPath, 'App 图标 icon.icns'))
    checks.push(pathEvidence(appAsarPath, 'App 前端资源 app.asar'))

    const iconFile = existsSync(plistPath) ? plistValue(plistPath, 'CFBundleIconFile') : ''
    if (iconFile !== 'icon.icns') {
      issues.push(`CFBundleIconFile 应为 icon.icns，实际: ${iconFile || '缺失'}`)
    }

    const bundleName = existsSync(plistPath) ? plistValue(plistPath, 'CFBundleName') : ''
    const bundleExecutable = existsSync(plistPath) ? plistValue(plistPath, 'CFBundleExecutable') : ''
    if (bundleName && bundleName !== '时安解忧屋') warnings.push(`CFBundleName 非预期: ${bundleName}`)
    if (bundleExecutable && bundleExecutable !== '时安解忧屋') warnings.push(`CFBundleExecutable 非预期: ${bundleExecutable}`)

    try {
      run('codesign', ['--verify', '--deep', '--strict', appPath])
    } catch (_) {
      warnings.push('当前 App 未通过 codesign strict 校验；第一版本地测试可继续，正式公开下载前仍需 Developer ID 签名和 notarization。')
    }

    return {
      skipped: false,
      mounted: true,
      appPath: rel(appPath),
      plist: {
        CFBundleIconFile: iconFile,
        CFBundleName: bundleName,
        CFBundleExecutable: bundleExecutable,
      },
      checks: checks.filter(Boolean),
    }
  } catch (error) {
    issues.push(`DMG 挂载或结构校验失败: ${String(error.stderr || error.message).trim()}`)
    return {
      skipped: false,
      mounted: attached,
      checks: checks.filter(Boolean),
    }
  } finally {
    if (attached) {
      try {
        run('hdiutil', ['detach', mountPoint, '-quiet'])
      } catch (error) {
        warnings.push(`DMG detach 失败，请手动检查挂载点 ${mountPoint}: ${error.message}`)
      }
    }
    rmSync(mountPoint, { recursive: true, force: true })
  }
}

mkdirSync(outDir, { recursive: true })
const result = verifyMacosDmg()

const report = {
  generatedAt: new Date().toISOString(),
  version,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  platform: process.platform,
  dmgPath,
  dmgFileName: basename(dmgPath),
  appName,
  passed: !result.skipped && issues.length === 0,
  skipped: result.skipped === true,
  skipReason: result.skipReason || '',
  result,
  issues,
  warnings,
}

writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

const lines = [
  '# macOS DMG 安装包校验',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> DMG：\`${dmgPath}\``,
  `> 结论：${report.skipped ? '跳过' : (report.passed ? '通过' : '未通过')}`,
  '',
  '## 检查项',
  '',
  '| 项目 | 路径 | 类型 | Bytes |',
  '| --- | --- | --- | ---: |',
  ...result.checks.map((item) => `| ${item.label} | \`${item.path}\` | ${item.kind || 'file'} | ${item.bytes || 0} |`),
  '',
  '## Info.plist',
  '',
  `- CFBundleIconFile：${result.plist?.CFBundleIconFile || '-'}`,
  `- CFBundleName：${result.plist?.CFBundleName || '-'}`,
  `- CFBundleExecutable：${result.plist?.CFBundleExecutable || '-'}`,
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
  '- 本脚本只读挂载 DMG 并检查 `.app` 结构，不写入证书、不公证、不提交 GitHub Release。',
  '- 通过本检查代表 DMG 可被本机挂载，且包内 App、Info.plist、主可执行文件和 logo 图标资源存在。',
  '- 检查项也包含 `app.asar`，用于确认 DMG 里不是空壳 App。',
  '- 正式公开下载前仍要补 Apple Developer ID 签名、notarization 和用户侧首次打开截图。',
]

if (report.skipped) {
  lines.splice(5, 0, `> 跳过原因：${report.skipReason}`)
}

writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  skipped: report.skipped,
  issues,
  warnings,
}, null, 2))

if (!report.passed && !report.skipped) {
  process.exit(1)
}
