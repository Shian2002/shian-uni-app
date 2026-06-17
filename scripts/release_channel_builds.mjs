#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { createHash } from 'node:crypto'
import { join, relative } from 'node:path'

const root = process.cwd()
const channels = ['appstore', 'google-play']
const stamp = localTimestamp()
const outDir = process.env.RELEASE_CHANNEL_BUILDS_DIR || join(root, 'artifacts', 'release-channel-builds', stamp)

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

function runStep(name, command, args, env = {}) {
  const startedAt = new Date().toISOString()
  try {
    const output = execFileSync(command, args, {
      cwd: root,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, ...env },
    })
    return {
      name,
      command: [command, ...args].join(' '),
      env,
      startedAt,
      finishedAt: new Date().toISOString(),
      passed: true,
      output: output.trim().slice(-4000),
    }
  } catch (error) {
    return {
      name,
      command: [command, ...args].join(' '),
      env,
      startedAt,
      finishedAt: new Date().toISOString(),
      passed: false,
      output: String(error.stdout || '').trim().slice(-4000),
      error: String(error.stderr || '').trim().slice(-4000) || error.message,
    }
  }
}

function currentBuildEvidence() {
  const indexPath = join(root, 'dist/build/h5/index.html')
  if (!existsSync(indexPath)) return null
  const stat = statSync(indexPath)
  return {
    index: 'dist/build/h5/index.html',
    bytes: stat.size,
    sha256: sha256(indexPath),
  }
}

function main() {
  mkdirSync(outDir, { recursive: true })
  const channelResults = []

  for (const channel of channels) {
    const env = { VITE_RELEASE_CHANNEL: channel }
    const build = runStep(`${channel}:build:h5`, 'npm', ['run', 'build:h5'], env)
    const boundary = build.passed
      ? runStep(`${channel}:payment-boundary`, 'npm', ['run', 'release:payment-boundary'], env)
      : { name: `${channel}:payment-boundary`, passed: false, skipped: true, error: 'build:h5 failed' }
    channelResults.push({
      channel,
      build,
      boundary,
      evidence: currentBuildEvidence(),
    })
    if (!build.passed || !boundary.passed) break
  }

  const restore = runStep('default:build:h5', 'npm', ['run', 'build:h5'])
  const report = {
    generatedAt: new Date().toISOString(),
    channelBuildsDir: rel(outDir),
    passed: channelResults.every((item) => item.build.passed && item.boundary.passed) && restore.passed,
    channels: channelResults,
    restore,
    restoredDefaultEvidence: currentBuildEvidence(),
    notes: [
      'appstore 和 google-play 构建会隐藏第三方数字内容充值入口。',
      '每个受限渠道构建后都会扫描 dist/build/h5，确认不包含外部充值接口、支付宝二维码文件名和付款截图文案。',
      '检查完成后会重新执行默认 build:h5，避免工作区停留在审核渠道产物。',
    ],
  }

  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

  const lines = [
    '# 审核渠道构建报告',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    '| 渠道 | H5 构建 | 支付边界扫描 | index SHA-256 |',
    '| --- | --- | --- | --- |',
    ...channelResults.map((item) => `| ${item.channel} | ${item.build.passed ? '通过' : '失败'} | ${item.boundary.passed ? '通过' : '失败'} | ${item.evidence?.sha256 || '-'} |`),
    '',
    '## 默认构建恢复',
    '',
    `- 结果：${restore.passed ? '通过' : '失败'}`,
    `- 默认 index：${report.restoredDefaultEvidence ? `\`${report.restoredDefaultEvidence.index}\`` : '缺失'}`,
    `- 默认 SHA-256：${report.restoredDefaultEvidence?.sha256 || '缺失'}`,
    '',
    '## 说明',
    '',
    ...report.notes.map((item) => `- ${item}`),
  ]
  writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

  console.log(JSON.stringify({
    outDir: report.channelBuildsDir,
    passed: report.passed,
    channels: channelResults.map((item) => ({ channel: item.channel, build: item.build.passed, paymentBoundary: item.boundary.passed })),
    defaultRestored: restore.passed,
  }, null, 2))

  if (!report.passed) process.exit(1)
}

main()
