#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import process from 'node:process'

const root = process.cwd()
const appPath = process.env.DESKTOP_MACOS_LIFECYCLE_APP || '/Applications/时安解忧屋.app'
const executablePath = join(appPath, 'Contents', 'MacOS', '时安解忧屋')
const packageJson = readJson('package.json') || {}
const version = process.env.DESKTOP_MACOS_LIFECYCLE_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.DESKTOP_MACOS_LIFECYCLE_OUT_DIR || join(root, 'artifacts', 'desktop-macos-lifecycle', `${localTimestamp()}-${version}`)
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
  try {
    return JSON.parse(execFileSync('cat', [join(root, path)], { encoding: 'utf8' }))
  } catch (_) {
    return null
  }
}

function run(command, args = []) {
  try {
    return {
      ok: true,
      output: execFileSync(command, args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim(),
    }
  } catch (error) {
    return {
      ok: false,
      output: String(error.stdout || error.stderr || error.message).trim(),
    }
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function processRows() {
  const result = run('pgrep', ['-fl', '时安解忧屋'])
  if (!result.ok || !result.output) return []
  return result.output
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const firstSpace = line.indexOf(' ')
      return {
        pid: firstSpace > -1 ? line.slice(0, firstSpace) : line,
        command: firstSpace > -1 ? line.slice(firstSpace + 1) : '',
      }
    })
}

function mainProcessRows(rows) {
  return rows.filter((row) => row.command === executablePath)
}

async function main() {
  mkdirSync(outDir, { recursive: true })
  if (process.platform !== 'darwin') {
    issues.push(`当前平台是 ${process.platform}，只能在 macOS 验证原生生命周期。`)
  }
  if (!existsSync(appPath)) issues.push(`缺少 App: ${appPath}`)
  if (!existsSync(executablePath)) issues.push(`缺少主可执行文件: ${executablePath}`)

  let before = processRows()
  if (!issues.length) {
    run('osascript', ['-e', 'tell application "时安解忧屋" to quit'])
    await sleep(1200)
    before = processRows()

    const firstOpen = run('open', ['-a', appPath])
    if (!firstOpen.ok) issues.push(`首次 open 失败: ${firstOpen.output}`)
    await sleep(1800)
    const afterFirstOpen = processRows()

    const secondOpen = run('open', ['-a', appPath])
    if (!secondOpen.ok) issues.push(`重复 open 失败: ${secondOpen.output}`)
    await sleep(1800)
    const afterSecondOpen = processRows()
    const mainAfterSecondOpen = mainProcessRows(afterSecondOpen)

    if (mainAfterSecondOpen.length !== 1) {
      issues.push(`重复打开后主进程数量应为 1，实际 ${mainAfterSecondOpen.length}`)
    }

    const report = writeReport({
      before,
      afterFirstOpen,
      afterSecondOpen,
      mainAfterSecondOpen,
    })
    printAndExit(report)
    return
  }

  const report = writeReport({ before, afterFirstOpen: [], afterSecondOpen: [], mainAfterSecondOpen: [] })
  printAndExit(report)
}

function writeReport(result) {
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    appPath,
    executablePath,
    passed: issues.length === 0,
    result,
    issues,
    warnings,
  }
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

  const lines = [
    '# macOS 原生生命周期检查',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> App：\`${appPath}\``,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    '## 进程检查',
    '',
    `- 首次打开后进程数：${result.afterFirstOpen.length}`,
    `- 重复打开后主进程数：${result.mainAfterSecondOpen.length}`,
    '',
    '## 问题',
    '',
    ...(issues.length ? issues.map((issue) => `- ${issue}`) : ['- 无结构性问题。']),
    '',
    '## 说明',
    '',
    '- 本检查会先退出时安解忧屋，再连续打开两次，验证单实例锁能聚焦同一个 App 主进程。',
    '- 检查结束后保留 App 打开，方便继续人工查看页面。',
  ]
  writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)
  return report
}

function printAndExit(report) {
  console.log(JSON.stringify({
    outDir: rel(outDir),
    passed: report.passed,
    appPath,
    mainProcessCount: report.result.mainAfterSecondOpen.length,
    issues,
  }, null, 2))
  if (!report.passed) process.exit(1)
}

main()
