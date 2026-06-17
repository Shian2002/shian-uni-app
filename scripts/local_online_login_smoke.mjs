#!/usr/bin/env node

import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

const baseUrl = process.env.QA_BASE_URL || 'http://localhost:5173'
const qaUser = process.env.QA_USER || 'test1'
const qaPassword = process.env.QA_PASSWORD || ''
const artifactDir = process.env.QA_ARTIFACT_DIR || join('artifacts', 'login-smoke', new Date().toISOString().replace(/[:.]/g, '-'))

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
  return {
    ok: response.ok,
    status: response.status,
    data,
    cookie: cookieFrom(response.headers),
  }
}

function writeReport(report) {
  mkdirSync(artifactDir, { recursive: true })
  writeFileSync(join(artifactDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
}

const report = {
  baseUrl,
  qaUser,
  artifactDir,
  checks: [],
  passed: false,
}

try {
  const health = await request('/api/health')
  report.checks.push({ name: 'health', status: health.status, ok: health.ok })
  assertCondition(health.ok, `线上代理健康检查失败: ${health.status}`)

  const login = await request('/api/login', {
    method: 'POST',
    body: { username: qaUser, password: qaPassword },
  })
  report.checks.push({
    name: 'login',
    status: login.status,
    ok: login.ok,
    username: login.data?.username || '',
    hasCookie: Boolean(login.cookie),
  })
  assertCondition(login.ok, `线上登录失败: ${login.status} ${JSON.stringify(login.data)}`)
  assertCondition(login.cookie, '线上登录未返回 session cookie')

  const me = await request('/api/me', {}, login.cookie)
  report.checks.push({
    name: 'me',
    status: me.status,
    ok: me.ok,
    username: me.data?.username || '',
    guest: Boolean(me.data?.guest),
  })
  assertCondition(me.ok, `登录态 /api/me 失败: ${me.status} ${JSON.stringify(me.data)}`)
  assertCondition(me.data?.username === qaUser, `/api/me 用户异常: ${JSON.stringify(me.data)}`)

  report.passed = true
  writeReport(report)
  console.log(JSON.stringify(report, null, 2))
} catch (error) {
  report.error = error.message
  writeReport(report)
  console.error(JSON.stringify(report, null, 2))
  process.exit(1)
}
