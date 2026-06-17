#!/usr/bin/env node

import { mkdirSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const baseUrl = process.env.QA_BASE_URL || 'https://shianjieyouwu.com'
const qaUser = process.env.QA_USER || 'test1'
const qaPassword = process.env.QA_PASSWORD || ''
const timeoutMs = Number(process.env.AGENT_STREAM_SMOKE_TIMEOUT_MS || 180000)
const outDir = process.env.AGENT_STREAM_SMOKE_OUT_DIR || join(root, 'artifacts', 'agent-stream-smoke', new Date().toISOString().replace(/[:.]/g, '-'))

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function cookieFrom(headers) {
  const raw = headers.get('set-cookie') || ''
  const pairs = []
  for (const part of raw.split(',')) {
    const pair = part.split(';')[0]?.trim()
    if (pair && pair.includes('=')) pairs.push(pair)
  }
  return pairs.join('; ')
}

function mergeCookies(...headers) {
  const pairs = new Map()
  for (const header of headers.filter(Boolean)) {
    for (const part of String(header).split(';')) {
      const trimmed = part.trim()
      if (!trimmed || !trimmed.includes('=')) continue
      const [key, ...rest] = trimmed.split('=')
      if (!key || ['path', 'expires', 'max-age', 'httponly', 'secure', 'samesite'].includes(key.toLowerCase())) continue
      pairs.set(key, rest.join('='))
    }
  }
  return [...pairs.entries()].map(([key, value]) => `${key}=${value}`).join('; ')
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
    signal: AbortSignal.timeout(timeoutMs),
  })
  const text = await response.text()
  let data = null
  try { data = text ? JSON.parse(text) : null } catch (_) { data = { raw: text } }
  return { ok: response.ok, status: response.status, data, cookie: cookieFrom(response.headers) }
}

function parseSseBuffer(buffer, events) {
  let rest = buffer
  let index = rest.indexOf('\n\n')
  while (index >= 0) {
    const block = rest.slice(0, index)
    rest = rest.slice(index + 2)
    const dataLines = block.split('\n')
      .map((line) => line.trimEnd())
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart())
    if (dataLines.length) {
      const raw = dataLines.join('\n')
      try {
        events.push(JSON.parse(raw))
      } catch (_) {
        events.push({ raw })
      }
    }
    index = rest.indexOf('\n\n')
  }
  return rest
}

async function streamRequest(cookie, csrfToken, body) {
  const response = await fetch(`${baseUrl}/api/comprehensive/ask/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Cookie: cookie,
      'X-CSRFToken': csrfToken,
      Origin: baseUrl,
      Referer: `${baseUrl}/`,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(timeoutMs),
  })
  const events = []
  const reader = response.body?.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let rawText = ''
  let bytes = 0
  if (reader) {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      bytes += value.byteLength
      const chunkText = decoder.decode(value, { stream: true })
      rawText += chunkText
      buffer += chunkText
      if ((response.headers.get('content-type') || '').includes('text/event-stream')) {
        buffer = parseSseBuffer(buffer, events)
      }
      if (events.some((event) => event.done || event.error)) break
    }
  }
  const tail = decoder.decode()
  rawText += tail
  buffer += tail
  if ((response.headers.get('content-type') || '').includes('text/event-stream')) {
    parseSseBuffer(buffer, events)
  }
  return { status: response.status, ok: response.ok, contentType: response.headers.get('content-type') || '', bytes, events, rawText: rawText.slice(0, 2000) }
}

function summarizeEvents(events) {
  const stages = [...new Set(events.map((event) => event.stage).filter(Boolean))]
  const errors = events.map((event) => event.error).filter(Boolean)
  const done = events.find((event) => event.done)
  const paipanDone = events.find((event) => event.stage === 'paipan_done')
  const toolChunks = events.filter((event) => event.tool && event.content).length
  const summaryChunks = events.filter((event) => event.summary && event.content).length
  return {
    eventCount: events.length,
    stages,
    errors,
    done: Boolean(done),
    conversationId: done?.conversation_id || null,
    runId: done?.run_id || events.find((event) => event.run_id)?.run_id || null,
    pointsLeft: done?.points_left ?? null,
    aiSingleCredits: done?.ai_single_credits ?? null,
    aiComboCredits: done?.ai_combo_credits ?? null,
    usedCredit: done?.used_credit || null,
    toolModels: done?.tool_models || paipanDone?.tool_models || [],
    hasPaipan: Boolean(done?.paipan || paipanDone?.paipan),
    artifactKeys: Object.keys(done?.artifacts || paipanDone?.artifacts || {}),
    toolChunks,
    summaryChunks,
  }
}

function writeReport(report) {
  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  writeFileSync(join(outDir, 'README.md'), `${[
    '# Agent Stream Smoke',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> Base URL：${report.baseUrl}`,
    `> 测试账号：${report.qaUser}`,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    '## 结果',
    '',
    `- HTTP：${report.stream.status}`,
    `- 事件数：${report.streamSummary.eventCount}`,
    `- done：${report.streamSummary.done ? '是' : '否'}`,
    `- conversation_id：${report.streamSummary.conversationId || '-'}`,
    `- used_credit：${report.streamSummary.usedCredit || '-'}`,
    `- points_left：${report.streamSummary.pointsLeft ?? '-'}`,
    `- tool_models：${report.streamSummary.toolModels.join(', ') || '-'}`,
    `- artifact_keys：${report.streamSummary.artifactKeys.join(', ') || '-'}`,
    '',
    '## 阶段',
    '',
    ...(report.streamSummary.stages.length ? report.streamSummary.stages.map((stage) => `- ${stage}`) : ['- 无']),
    '',
    '## 问题',
    '',
    ...(report.issues.length ? report.issues.map((issue) => `- ${issue}`) : ['- 无']),
  ].join('\n')}\n`)
}

const report = {
  generatedAt: new Date().toISOString(),
  baseUrl,
  qaUser,
  artifactDir: rel(outDir),
  passed: false,
  checks: [],
  beforeAssets: null,
  afterAssets: null,
  request: null,
  stream: null,
  streamSummary: null,
  issues: [],
}

try {
  const health = await request('/api/health')
  report.checks.push({ name: 'health', status: health.status, ok: health.ok })
  if (!health.ok) report.issues.push(`健康检查失败: ${health.status}`)

  const login = await request('/api/login', {
    method: 'POST',
    body: { username: qaUser, password: qaPassword },
  })
  report.checks.push({ name: 'login', status: login.status, ok: login.ok, hasCookie: Boolean(login.cookie) })
  if (!login.ok || !login.cookie) report.issues.push(`登录失败: ${login.status}`)

  const cookie = mergeCookies(login.cookie)
  const csrf = await request('/api/csrf-token', {}, cookie)
  const csrfToken = csrf.data?.csrf_token || ''
  const sessionCookie = mergeCookies(cookie, csrf.cookie)
  report.checks.push({ name: 'csrf-token', status: csrf.status, ok: csrf.ok, hasToken: csrfToken.length > 20 })
  if (!csrf.ok || csrfToken.length <= 20) report.issues.push(`CSRF token 获取失败: ${csrf.status}`)

  const optionsBefore = await request('/api/comprehensive/options', {}, sessionCookie)
  report.checks.push({ name: 'comprehensive-options-before', status: optionsBefore.status, ok: optionsBefore.ok })
  report.beforeAssets = {
    points: Number(optionsBefore.data?.points || 0),
    aiSingleCredits: Number(optionsBefore.data?.ai_single_credits || 0),
    aiComboCredits: Number(optionsBefore.data?.ai_combo_credits || 0),
    dailyLightAvailable: Boolean(optionsBefore.data?.daily_light_available),
  }

  if (!report.beforeAssets.dailyLightAvailable && report.beforeAssets.points < 2 && report.beforeAssets.aiSingleCredits < 1) {
    report.issues.push('测试账号没有可用每日轻量额度、积分或单术数额度，跳过真实 stream 消费。')
  }

  const body = {
    question: '请用八字看我最近三个月事业发展，先起盘再给建议',
    profiles: [{
      name: `${qaUser}-stream-smoke`,
      gender: '男',
      calType: '公历',
      birthTime: '1995-03-18 09:30',
      birthAddr: '广州',
      profileType: 'self',
    }],
    profile_confirmed: true,
    llm_model: 'basic',
    tool_models: ['bazi'],
    auto_select_tools: false,
    history: [],
    paipan: { paipan: {}, artifacts: {} },
    reading_mode: 'standard',
    artifact_policy: 'auto',
    existing_artifact_keys: [],
  }
  report.request = {
    question: body.question,
    tool_models: body.tool_models,
    reading_mode: body.reading_mode,
    profileCount: body.profiles.length,
  }

  if (!report.issues.length) {
    report.stream = await streamRequest(sessionCookie, csrfToken, body)
    report.streamSummary = summarizeEvents(report.stream.events)
    if (!report.stream.ok) report.issues.push(`stream HTTP 异常: ${report.stream.status}`)
    if (report.streamSummary.errors.length) report.issues.push(...report.streamSummary.errors.map((error) => `stream error: ${error}`))
    if (!report.streamSummary.done) report.issues.push('stream 未返回 done 事件')
    if (!report.streamSummary.hasPaipan) report.issues.push('stream 未返回排盘上下文')
    if (!report.streamSummary.artifactKeys.length) report.issues.push('stream 未返回 artifacts')
    if (report.streamSummary.toolChunks === 0 && report.streamSummary.summaryChunks === 0) report.issues.push('stream 未返回解读文本 chunk')

    const optionsAfter = await request('/api/comprehensive/options', {}, sessionCookie)
    report.checks.push({ name: 'comprehensive-options-after', status: optionsAfter.status, ok: optionsAfter.ok })
    report.afterAssets = {
      points: Number(optionsAfter.data?.points || 0),
      aiSingleCredits: Number(optionsAfter.data?.ai_single_credits || 0),
      aiComboCredits: Number(optionsAfter.data?.ai_combo_credits || 0),
      dailyLightAvailable: Boolean(optionsAfter.data?.daily_light_available),
    }
  } else {
    report.stream = { status: 0, ok: false, contentType: '', bytes: 0, events: [] }
    report.streamSummary = summarizeEvents([])
  }

  report.passed = report.issues.length === 0
  writeReport(report)
  console.log(JSON.stringify({
    outDir: report.artifactDir,
    passed: report.passed,
    beforeAssets: report.beforeAssets,
    afterAssets: report.afterAssets,
    streamSummary: report.streamSummary,
    issues: report.issues,
  }, null, 2))
  if (!report.passed) process.exit(1)
} catch (error) {
  report.issues.push(error.message)
  report.stream = report.stream || { status: 0, ok: false, contentType: '', bytes: 0, events: [] }
  report.streamSummary = report.streamSummary || summarizeEvents([])
  writeReport(report)
  console.error(JSON.stringify({
    outDir: report.artifactDir,
    passed: false,
    issues: report.issues,
  }, null, 2))
  process.exit(1)
}
