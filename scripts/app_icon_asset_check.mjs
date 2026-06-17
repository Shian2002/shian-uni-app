#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const configPath = 'configs/release/app-icons.json'
const outDir = process.env.APP_ICON_REPORT_DIR || join(root, 'artifacts', 'app-icons', localTimestamp())
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
  if (!existsSync(fullPath)) {
    issues.push(`缺少文件: ${path}`)
    return null
  }
  try {
    return JSON.parse(readFileSync(fullPath, 'utf8'))
  } catch (error) {
    issues.push(`${path} 不是合法 JSON: ${error.message}`)
    return null
  }
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function git(args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim()
  } catch (_) {
    return ''
  }
}

function pngInfo(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const buffer = readFileSync(fullPath)
  const signature = buffer.subarray(0, 8).toString('hex')
  if (signature !== '89504e470d0a1a0a') {
    issues.push(`${path} 不是合法 PNG 文件`)
    return null
  }
  return {
    path,
    bytes: statSync(fullPath).size,
    width: buffer.readUInt32BE(16),
    height: buffer.readUInt32BE(20),
    sha256: sha256(fullPath),
  }
}

function binaryInfo(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) {
    issues.push(`缺少图标文件: ${path}`)
    return null
  }
  const stat = statSync(fullPath)
  if (stat.size <= 0) {
    issues.push(`${path} 是空文件`)
  }
  return { path, bytes: stat.size, sha256: sha256(fullPath) }
}

function checkPng(path, expectedSize, label) {
  const info = pngInfo(path)
  if (!info) {
    issues.push(`缺少 PNG 图标: ${path}`)
    return null
  }
  if (info.bytes <= 0) {
    issues.push(`${path} 是空文件`)
  }
  if (info.width !== expectedSize || info.height !== expectedSize) {
    issues.push(`${label} 尺寸错误: ${path} 应为 ${expectedSize}x${expectedSize}，实际 ${info.width}x${info.height}`)
  }
  return { ...info, expectedSize, label }
}

const config = readJson(configPath)
const iconResults = []
const desktopResults = []

if (config) {
  const source = checkPng(config.sourceLogo, 1024, 'sourceLogo')
  if (source) iconResults.push(source)

  for (const icon of config.requiredIcons || []) {
    if (!icon.path || !icon.size || !icon.id) {
      issues.push(`${configPath} requiredIcons 存在不完整配置`)
      continue
    }
    const result = checkPng(icon.path, icon.size, icon.id)
    if (result) {
      iconResults.push({
        ...result,
        id: icon.id,
        platforms: icon.platforms || [],
      })
    }
  }

  for (const [kind, path] of Object.entries(config.desktopIcons || {})) {
    const result = binaryInfo(path)
    if (result) desktopResults.push({ kind, ...result })
  }

  if (config.storeIcon && !iconResults.some((item) => item.path === config.storeIcon)) {
    warnings.push(`storeIcon 未包含在 requiredIcons 中: ${config.storeIcon}`)
  }
}

const report = {
  generatedAt: new Date().toISOString(),
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  config: configPath,
  sourceLogo: config?.sourceLogo || '',
  storeIcon: config?.storeIcon || '',
  passed: issues.length === 0,
  icons: iconResults,
  desktopIcons: desktopResults,
  issues,
  warnings,
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

const lines = [
  '# App 图标资产检查',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  `> 配置：\`${configPath}\``,
  '',
  '## 移动端和商店图标',
  '',
  '| ID | 文件 | 尺寸 | SHA-256 |',
  '| --- | --- | ---: | --- |',
  ...iconResults.map((icon) => `| ${icon.id || icon.label} | \`${icon.path}\` | ${icon.width}x${icon.height} | \`${icon.sha256}\` |`),
  '',
  '## 桌面图标',
  '',
  '| 类型 | 文件 | Bytes | SHA-256 |',
  '| --- | --- | ---: | --- |',
  ...desktopResults.map((icon) => `| ${icon.kind} | \`${icon.path}\` | ${icon.bytes} | \`${icon.sha256}\` |`),
  '',
  '## 说明',
  '',
  '- HBuilderX、DCloud 云打包、Xcode、DevEco 和商店后台优先使用 1024x1024 母图。',
  '- 证书、密钥、keystore、p12、mobileprovision 和签名口令不进入 GitHub。',
  '- 本检查只验证图标资产和尺寸，不替代平台真实打包和真机安装截图。',
]

if (issues.length) {
  lines.push('', '## 问题', '', ...issues.map((item) => `- ${item}`))
}
if (warnings.length) {
  lines.push('', '## 警告', '', ...warnings.map((item) => `- ${item}`))
}

writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  icons: iconResults.length,
  desktopIcons: desktopResults.length,
  issues,
}, null, 2))

if (!report.passed) {
  process.exit(1)
}
