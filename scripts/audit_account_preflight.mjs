#!/usr/bin/env node

import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const baseUrl = process.env.QA_BASE_URL || 'http://localhost:5173'
const qaUser = process.env.QA_USER || 'test1'
const qaPassword = process.env.QA_PASSWORD || ''
const requiredStandardRuns = Number(process.env.QA_REQUIRED_STANDARD_RUNS || 3)
const requiredComboRuns = Number(process.env.QA_REQUIRED_COMBO_RUNS || 1)
const requiredFollowupRuns = Number(process.env.QA_REQUIRED_FOLLOWUP_RUNS || 1)
const strict = process.argv.includes('--strict') || process.env.QA_AUDIT_ACCOUNT_STRICT === '1'
const artifactDir = process.env.QA_ARTIFACT_DIR || join('artifacts', 'audit-account', new Date().toISOString().replace(/[:.]/g, '-'))

function assertCondition(condition, message) {
  if (!condition) throw new Error(message)
}

function cookieFrom(headers) {
  const raw = headers.get('set-cookie') || ''
  return raw.split(',').map((part) => part.split(';')[0].trim()).filter(Boolean).join('; ')
}

async function request(path, options = {}, cookie = '') {
  const response = await fetch(`${baseUrl}${path}`, {
    method: options.method || 'GET',
    headers: {
      'Content-Type': 'application/json',
      ...(cookie ? { Cookie: cookie } : {}),
      ...(options.headers || {}),
    },
    body: options.body ? JSON.stringify(options.body) : undefined,
  })
  const text = await response.text()
  let data = null
  try { data = text ? JSON.parse(text) : null } catch (_) { data = { raw: text } }
  return { ok: response.ok, status: response.status, data, cookie: cookieFrom(response.headers) }
}

function writeReport(report) {
  mkdirSync(artifactDir, { recursive: true })
  writeFileSync(join(artifactDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  const lines = [
    '# 审核账号资产预检报告',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> Base URL：${report.baseUrl}`,
    `> 测试账号：${report.qaUser}`,
    `> 结论：${report.fullAgentReady ? '完整 Agent 审核账号可用' : '完整 Agent 审核账号未就绪'}`,
    '',
    `- 入口可用：${report.entryReady ? '是' : '否'}`,
    `- 完整 Agent 可用：${report.fullAgentReady ? '是' : '否'}`,
    `- 当前积分：${report.assets.points}`,
    `- 单术数次数：${report.assets.aiSingleCredits}`,
    `- 多术数合参次数：${report.assets.aiComboCredits}`,
    `- 每日轻量额度可用：${report.assets.dailyLightAvailable ? '是' : '否'}`,
    '',
    '## 需求',
    '',
    `- 标准首问：${report.requirements.standardRuns} 次，每次约 ${report.costs.standardCost} 积分或 1 次单术数额度。`,
    `- 复杂合参：${report.requirements.comboRuns} 次，每次约 ${report.costs.comboCost} 积分或 1 次合参额度。`,
    `- 追问：${report.requirements.followupRuns} 次，每次约 ${report.costs.followupCost} 积分，不能用首问每日轻量额度。`,
    '',
    '## 缺口',
    '',
    ...(report.gaps.length ? report.gaps.map((gap) => `- ${gap}`) : ['- 无']),
    '',
    '## 判断口径',
    '',
    '- 这条预检只读取账号资产，不发起 Agent stream，不扣积分。',
    '- `entryReady=true` 只能证明登录和入口可用，不能证明完整解读可完成。',
    '- `fullAgentReady=false` 时，不能把该账号交给应用商店审核员跑完整 Agent 流程。',
    '',
  ]
  writeFileSync(join(artifactDir, 'report.md'), `${lines.join('\n')}\n`)
}

function findById(items, id) {
  return (Array.isArray(items) ? items : []).find((item) => item.id === id) || {}
}

function calculateCost(options, { readingMode = 'standard', followup = false } = {}) {
  const llm = findById(options.llm_models, 'basic') || (options.llm_models || [])[0] || {}
  const mode = findById(options.reading_modes, readingMode)
  const delta = Number(mode.cost_delta || 0)
  if (followup) return Math.max(0, Number(llm.followup_cost || 2) + delta)
  return Math.max(0, Number(llm.cost_base || 2) + delta)
}

function evaluateReadiness(options) {
  const points = Number(options.points || 0)
  const aiSingleCredits = Number(options.ai_single_credits || 0)
  const aiComboCredits = Number(options.ai_combo_credits || 0)
  const dailyLightAvailable = Boolean(options.daily_light_available)
  const standardCost = calculateCost(options, { readingMode: 'standard' })
  const comboCost = calculateCost(options, { readingMode: 'deep' })
  const followupCost = calculateCost(options, { readingMode: 'standard', followup: true })

  let remainingPoints = points
  let standardCovered = 0
  let comboCovered = 0
  let followupCovered = 0

  if (dailyLightAvailable && standardCost <= 2 && requiredStandardRuns > standardCovered) standardCovered += 1
  const singleByCredits = Math.min(aiSingleCredits, Math.max(0, requiredStandardRuns - standardCovered))
  standardCovered += singleByCredits
  while (standardCovered < requiredStandardRuns && remainingPoints >= standardCost) {
    remainingPoints -= standardCost
    standardCovered += 1
  }

  const comboByCredits = Math.min(aiComboCredits, requiredComboRuns)
  comboCovered += comboByCredits
  while (comboCovered < requiredComboRuns && remainingPoints >= comboCost) {
    remainingPoints -= comboCost
    comboCovered += 1
  }

  while (followupCovered < requiredFollowupRuns && remainingPoints >= followupCost) {
    remainingPoints -= followupCost
    followupCovered += 1
  }

  const gaps = []
  if (standardCovered < requiredStandardRuns) gaps.push(`标准首问不足：需要 ${requiredStandardRuns} 次，当前可覆盖 ${standardCovered} 次。`)
  if (comboCovered < requiredComboRuns) gaps.push(`复杂合参不足：需要 ${requiredComboRuns} 次，当前可覆盖 ${comboCovered} 次。`)
  if (followupCovered < requiredFollowupRuns) gaps.push(`追问积分不足：需要 ${requiredFollowupRuns} 次，当前可覆盖 ${followupCovered} 次。`)

  return {
    assets: { points, aiSingleCredits, aiComboCredits, dailyLightAvailable },
    costs: { standardCost, comboCost, followupCost },
    coverage: { standardCovered, comboCovered, followupCovered, remainingPoints },
    gaps,
    fullAgentReady: gaps.length === 0,
  }
}

const report = {
  generatedAt: new Date().toISOString(),
  baseUrl,
  qaUser,
  artifactDir,
  strict,
  passed: false,
  entryReady: false,
  fullAgentReady: false,
  requirements: {
    standardRuns: requiredStandardRuns,
    comboRuns: requiredComboRuns,
    followupRuns: requiredFollowupRuns,
  },
  assets: { points: 0, aiSingleCredits: 0, aiComboCredits: 0, dailyLightAvailable: false },
  costs: { standardCost: 0, comboCost: 0, followupCost: 0 },
  coverage: { standardCovered: 0, comboCovered: 0, followupCovered: 0, remainingPoints: 0 },
  gaps: [],
  checks: [],
}

try {
  const health = await request('/api/health')
  report.checks.push({ name: 'health', status: health.status, ok: health.ok })
  assertCondition(health.ok, `健康检查失败: ${health.status}`)

  const login = await request('/api/login', {
    method: 'POST',
    body: { username: qaUser, password: qaPassword },
  })
  report.checks.push({ name: 'login', status: login.status, ok: login.ok, hasCookie: Boolean(login.cookie) })
  assertCondition(login.ok && login.cookie, `登录失败: ${login.status} ${JSON.stringify(login.data)}`)

  const me = await request('/api/me', {}, login.cookie)
  report.checks.push({ name: 'me', status: me.status, ok: me.ok, username: me.data?.username || '' })
  assertCondition(me.ok && me.data?.username === qaUser && me.data?.guest !== true, `/api/me 异常: ${JSON.stringify(me.data)}`)

  const membership = await request('/api/membership', {}, login.cookie)
  report.checks.push({ name: 'membership', status: membership.status, ok: membership.ok })
  assertCondition(membership.ok, `会员接口失败: ${membership.status} ${JSON.stringify(membership.data)}`)

  const options = await request('/api/comprehensive/options', {}, login.cookie)
  report.checks.push({ name: 'comprehensive-options', status: options.status, ok: options.ok })
  assertCondition(options.ok, `综合解读配置接口失败: ${options.status} ${JSON.stringify(options.data)}`)

  report.entryReady = true
  report.passed = true
  const readiness = evaluateReadiness(options.data || {})
  Object.assign(report, readiness)
  writeReport(report)
  console.log(JSON.stringify(report, null, 2))
  if (strict && !report.fullAgentReady) process.exit(1)
} catch (error) {
  report.passed = false
  report.error = error.message
  report.gaps.push(error.message)
  writeReport(report)
  console.error(JSON.stringify(report, null, 2))
  process.exit(1)
}
