#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.REAL_USER_ACCEPTANCE_STRICT === '1'
const packetDir = process.env.REAL_USER_PACKET_DIR || latestDir('artifacts/real-user-packets')
const defaultOutDir = 'artifacts/real-user-results'
const outDir = process.env.REAL_USER_ACCEPTANCE_OUT_DIR || join(root, defaultOutDir)
const stamp = new Date().toISOString().replace(/[:.]/g, '-')
const minimumTestersPerPlatform = Number.parseInt(process.env.REAL_USER_MIN_TESTERS || '2', 10)

const releaseScope = readJson(join(root, 'configs/release/current-release-scope.json')) || {}
const platforms = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms
  : ['h5', 'android', 'ios', 'harmony', 'macos', 'windows']
const requiredFields = ['tester', 'device', 'systemVersion', 'channel', 'packageOrUrl', 'sha256OrBuild', 'accountType', 'conclusion']
const requiredScreenshots = [
  '01-home.png',
  '02-login-modal.png',
  '03-agent.png',
  '04-points.png',
  '05-tool-bazi.png',
  '06-tool-qimen.png',
  '07-tool-ziwei.png',
  '08-delete-account.png',
]
const requiredFlowIds = [
  'privacy-entry',
  'permission-timing',
  'login-register',
  'agent-entry-button',
  'agent-login-modal',
  'legacy-login-methods',
  'agent-workbench',
  'question-templates',
  'points-pricing',
  'tools-open',
  'history-report-entry',
  'delete-account-entry',
  'session-restore',
]

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function latestDir(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => b.name.localeCompare(a.name))
  return dirs[0] ? join(root, path, dirs[0].name) : ''
}

function readJson(path) {
  if (!existsSync(path)) return null
  try {
    return JSON.parse(readFileSync(path, 'utf8'))
  } catch (error) {
    return { __parseError: error.message }
  }
}

function hasText(value) {
  return typeof value === 'string' && value.trim().length > 0
}

function hasPlaceholder(value) {
  return typeof value === 'string' && /(示例|待填写|TODO|TBD|example|placeholder)/i.test(value)
}

function resultFilesForPlatform(dir) {
  const resultsDir = join(dir, 'results')
  if (existsSync(resultsDir)) {
    return readdirSync(resultsDir)
      .filter((name) => name.endsWith('.json'))
      .sort()
      .map((name) => join(resultsDir, name))
  }
  const legacy = join(dir, 'result.json')
  return existsSync(legacy) ? [legacy] : []
}

function checkResultFile(resultPath) {
  const result = readJson(resultPath)
  const missing = []
  let passedFlowCount = 0

  if (!existsSync(resultPath)) missing.push(`缺少结果文件: ${rel(resultPath)}`)
  if (result?.__parseError) missing.push(`${rel(resultPath)} 解析失败: ${result.__parseError}`)

  if (result && !result.__parseError) {
    for (const field of requiredFields) {
      if (!hasText(result[field])) missing.push(`${rel(resultPath)} 缺少字段: ${field}`)
      else if (hasPlaceholder(result[field])) missing.push(`${rel(resultPath)} 字段仍是占位内容: ${field}`)
    }
    if (result.conclusion !== '通过') missing.push(`${rel(resultPath)} 结论不是“通过”`)
    if (result.canSubmitToStore !== true) missing.push(`${rel(resultPath)} canSubmitToStore 不是 true`)
    if (result.realSmsEmailPaymentTriggered === true) missing.push(`${rel(resultPath)} 真实用户测试不应触发真实短信、邮件或支付`)
    const passedFlows = Array.isArray(result.passedFlows) ? result.passedFlows : []
    passedFlowCount = passedFlows.length
    for (const flowId of requiredFlowIds) {
      if (!passedFlows.includes(flowId)) missing.push(`${rel(resultPath)} passedFlows 缺少必测流程: ${flowId}`)
    }
    if (Array.isArray(result.blockers) && result.blockers.length > 0 && result.retestPassed !== true) {
      missing.push(`${rel(resultPath)} 存在阻塞问题但 retestPassed 不是 true`)
    }
  }

  return {
    path: rel(resultPath),
    ready: missing.length === 0,
    passedFlowCount,
    missing,
  }
}

function checkPlatform(platform) {
  const dir = join(packetDir, platform)
  const screenshotsDir = join(dir, 'screenshots')
  const missing = []
  const evidence = []
  let screenshotCount = 0

  if (!existsSync(dir)) missing.push(`缺少平台目录: ${platform}`)

  const resultFiles = existsSync(dir) ? resultFilesForPlatform(dir) : []
  if (!resultFiles.length) missing.push('缺少 results/*.json 或旧格式 result.json')
  const resultChecks = resultFiles.map(checkResultFile)
  const readyResultChecks = resultChecks.filter((item) => item.ready)
  for (const resultCheck of resultChecks) {
    evidence.push(resultCheck.path)
    missing.push(...resultCheck.missing)
  }
  if (readyResultChecks.length < minimumTestersPerPlatform) {
    missing.push(`通过测试人不足: ${readyResultChecks.length}/${minimumTestersPerPlatform}`)
  }

  for (const name of requiredScreenshots) {
    const shot = join(screenshotsDir, name)
    if (!existsSync(shot)) missing.push(`缺少截图: screenshots/${name}`)
    else {
      screenshotCount += 1
      evidence.push(rel(shot))
    }
  }

  return {
    platform,
    status: missing.length === 0 ? 'ready' : 'missing',
    passedTesterCount: readyResultChecks.length,
    requiredTesterCount: minimumTestersPerPlatform,
    passedFlowCount: readyResultChecks.reduce((max, item) => Math.max(max, item.passedFlowCount), 0),
    requiredFlowCount: requiredFlowIds.length,
    screenshotCount,
    requiredScreenshotCount: requiredScreenshots.length,
    evidence,
    missing,
  }
}

function main() {
  const issues = []
  if (!packetDir || !existsSync(packetDir)) {
    issues.push(`缺少真实用户测试包目录: ${packetDir || 'artifacts/real-user-packets'}`)
  }

  const platformsResult = packetDir && existsSync(packetDir)
    ? platforms.map(checkPlatform)
    : platforms.map((platform) => ({ platform, status: 'missing', evidence: [], missing: ['缺少真实用户测试包目录'] }))

  const ready = platformsResult.filter((item) => item.status === 'ready').length
  const missing = platformsResult.length - ready
  const report = {
    generatedAt: new Date().toISOString(),
    packetDir: packetDir ? rel(packetDir) : '',
    strict,
    minimumTestersPerPlatform,
    releaseScope: {
      configPath: 'configs/release/current-release-scope.json',
      currentBatch: releaseScope.currentBatch || '',
      activePlatforms: platforms,
      deferredPlatforms: (releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean),
    },
    passed: issues.length === 0 && missing === 0,
    summary: { ready, missing },
    issues,
    platforms: platformsResult,
  }

  mkdirSync(outDir, { recursive: true })
  const jsonOut = join(outDir, `${stamp}.json`)
  const mdOut = join(outDir, `${stamp}.md`)
  writeFileSync(jsonOut, `${JSON.stringify(report, null, 2)}\n`)

  const md = [
    '# 真实用户回收验收报告',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 测试包：${report.packetDir || '缺失'}`,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    `汇总：READY ${ready} / MISSING ${missing}`,
    `当前批次平台：${platforms.join('、')}`,
    '',
    '| 平台 | 状态 | 证据 | 缺口 |',
    '| --- | --- | --- | --- |',
    ...platformsResult.map((item) => {
      const evidence = item.evidence.length ? item.evidence.map((entry) => `\`${entry}\``).join('<br>') : '-'
      const gaps = item.missing.length ? item.missing.join('<br>') : '-'
      return `| ${item.platform} | ${item.status.toUpperCase()} | 测试人 ${item.passedTesterCount}/${item.requiredTesterCount}<br>流程 ${item.passedFlowCount}/${item.requiredFlowCount}<br>截图 ${item.screenshotCount}/${item.requiredScreenshotCount}<br>${evidence} | ${gaps} |`
    }),
    '',
    '## 规则',
    '',
    `- 当前批次每个平台至少需要 ${minimumTestersPerPlatform} 个测试人的通过结果，推荐填写 \`results/tester-*.json\`。`,
    '- 结果 JSON 不能保留“示例、待填写、TODO、TBD、example、placeholder”等占位内容。',
    '- 每个平台的 passedFlows 必须包含全部必测流程编号。',
    '- 每个平台必须回收 8 张标准截图：首页、登录弹窗、Agent、积分页、八字、奇门、紫微、账号注销。',
    '- 真实用户测试不得触发真实短信、邮件或支付；如触发必须记录原因并阻止上架候选。',
    '- 默认模式只生成报告；正式上架候选前使用 `npm run real-user:check -- --strict`。',
    '',
  ].join('\n')
  writeFileSync(mdOut, md)

  console.log(`Real user acceptance: ${report.passed ? 'ready' : 'not-ready'}`)
  console.log(`JSON: ${rel(jsonOut)}`)
  console.log(`Markdown: ${rel(mdOut)}`)
  console.log(`READY=${ready} MISSING=${missing}`)

  if (strict && !report.passed) {
    console.error('严格模式失败：真实用户回收证据不完整。')
    process.exit(1)
  }
}

main()
