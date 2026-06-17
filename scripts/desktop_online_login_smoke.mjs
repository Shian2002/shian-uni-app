#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { mkdirSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { join, resolve } from 'node:path'

const root = process.cwd()
const desktopDir = join(root, 'desktop')
const artifactDir = process.env.QA_ARTIFACT_DIR || join(root, 'artifacts', 'desktop-online-login-smoke', new Date().toISOString().replace(/[:.]/g, '-'))
const timeoutMs = Number(process.env.QA_TIMEOUT_MS || 30000)
const qaUser = process.env.QA_USER || 'test1'
const qaPassword = process.env.QA_PASSWORD || ''
const apiTarget = process.env.SHIAN_DESKTOP_API_TARGET || 'https://shianjieyouwu.com'
const httpOnly = process.env.DESKTOP_ONLINE_LOGIN_HTTP_ONLY === '1'

function assertCondition(condition, message) {
  if (!condition) throw new Error(message)
}

function ensureArtifactDir() {
  mkdirSync(artifactDir, { recursive: true })
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

function runCommand(command, args) {
  try {
    return {
      ok: true,
      stdout: execFileSync(command, args, { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }),
      stderr: '',
    }
  } catch (error) {
    return {
      ok: false,
      stdout: error.stdout?.toString?.() || '',
      stderr: error.stderr?.toString?.() || '',
      error: error.message,
    }
  }
}

function appleScriptString(value) {
  return String(value).replace(/\\/g, '\\\\').replace(/"/g, '\\"')
}

function macosAppNameFromExecutable(executablePath) {
  const appSegment = String(executablePath).split('/').find((part) => part.endsWith('.app'))
  return appSegment ? appSegment.replace(/\.app$/, '') : ''
}

function quitExistingMacosApp(executablePath) {
  if (process.platform !== 'darwin') {
    return { skipped: true, reason: 'not-macos' }
  }

  const appName = macosAppNameFromExecutable(executablePath)
  if (!appName) {
    return { skipped: true, reason: 'not-macos-app-bundle' }
  }

  const existing = runCommand('pgrep', ['-x', appName])
  if (!existing.ok) {
    return { skipped: true, reason: 'not-running', appName }
  }

  const quit = runCommand('osascript', ['-e', `tell application "${appleScriptString(appName)}" to quit`])
  return {
    skipped: false,
    appName,
    pids: existing.stdout.trim().split(/\s+/).filter(Boolean),
    ok: quit.ok,
    error: quit.ok ? '' : quit.error,
    stderr: quit.stderr,
  }
}

function writeFailure(report, error, extra = {}) {
  writeFileSync(join(artifactDir, 'failure.json'), `${JSON.stringify({
    ...report,
    passed: false,
    error: error?.message || String(error),
    ...extra,
  }, null, 2)}\n`)
}

function isObject(value) {
  return Boolean(value) && typeof value === 'object' && !Array.isArray(value)
}

function nonEmptyArray(value) {
  return Array.isArray(value) && value.length > 0
}

function mergeCookies(...cookieHeaders) {
  const pairs = new Map()
  for (const header of cookieHeaders.filter(Boolean)) {
    for (const part of String(header).split(';')) {
      const trimmed = part.trim()
      if (!trimmed || !trimmed.includes('=')) continue
      const [key, ...rest] = trimmed.split('=')
      if (!key || ['path', 'expires', 'max-age', 'httponly', 'secure', 'samesite'].includes(key.toLowerCase())) continue
      pairs.set(key, rest.join('='))
    }
  }
  return Array.from(pairs.entries()).map(([key, value]) => `${key}=${value}`).join('; ')
}

async function runCoreBackendChecks(checks, request) {
  const ziweiInfo = await request('/api/ziwei/info')
  const ziweiInfoReady = ziweiInfo.ok &&
    ziweiInfo.data?.data?.name === '紫微斗数' &&
    nonEmptyArray(ziweiInfo.data?.data?.shichen)
  checks.push({
    name: 'ziwei-info',
    status: ziweiInfo.status,
    ok: ziweiInfo.ok,
    schemaReady: ziweiInfoReady,
    shichenCount: Array.isArray(ziweiInfo.data?.data?.shichen) ? ziweiInfo.data.data.shichen.length : null,
  })
  assertCondition(ziweiInfoReady, `/api/ziwei/info 异常: ${ziweiInfo.status} ${JSON.stringify(ziweiInfo.data)}`)

  const huangli = await request('/api/huangli?date=2024-02-10')
  const huangliReady = huangli.ok &&
    isObject(huangli.data) &&
    typeof huangli.data.solarDate === 'string' &&
    typeof huangli.data.lunarDate === 'string'
  checks.push({
    name: 'huangli',
    status: huangli.status,
    ok: huangli.ok,
    schemaReady: huangliReady,
    solarDate: huangli.data?.solarDate || '',
  })
  assertCondition(huangliReady, `/api/huangli 异常: ${huangli.status} ${JSON.stringify(huangli.data)}`)

  const baziPaipan = await request('/api/bazi/paipan', {
    method: 'POST',
    body: {
      name: '样例',
      gender: '男',
      calType: '公历',
      birthTime: '199001271030',
      birthAddr: '北京',
      birthLng: 116.4074,
      useSolarTime: true,
      _replay: true,
    },
  })
  const baziPaipanReady = baziPaipan.ok &&
    baziPaipan.data?.success === true &&
    isObject(baziPaipan.data?.four_pillars)
  checks.push({
    name: 'bazi-paipan',
    status: baziPaipan.status,
    ok: baziPaipan.ok,
    schemaReady: baziPaipanReady,
    pillarSource: baziPaipan.data?.pillar_source || '',
  })
  assertCondition(baziPaipanReady, `/api/bazi/paipan 异常: ${baziPaipan.status} ${JSON.stringify(baziPaipan.data)}`)

  const baziPro = await request('/api/bazi/shian-pro?y=1990&m=1&d=27&h=10&mi=30&s=1')
  const baziProReady = baziPro.ok &&
    baziPro.data?.success === true &&
    isObject(baziPro.data?.sizhu) &&
    Array.isArray(baziPro.data?.dayun_list)
  checks.push({
    name: 'bazi-shian-pro',
    status: baziPro.status,
    ok: baziPro.ok,
    schemaReady: baziProReady,
    source: baziPro.data?.source || '',
  })
  assertCondition(baziProReady, `/api/bazi/shian-pro 异常: ${baziPro.status} ${JSON.stringify(baziPro.data)}`)

  const ziweiPan = await request('/api/ziwei/pan', {
    method: 'POST',
    body: {
      year: 1990,
      month: 1,
      day: 27,
      hour: 10,
      minute: 30,
      gender: '男',
      date_type: 'solar',
      longitude: 116.4074,
    },
  })
  const ziweiPanReady = ziweiPan.ok &&
    ziweiPan.data?.code === 0 &&
    Array.isArray(ziweiPan.data?.data?.twelve_palaces) &&
    ziweiPan.data.data.twelve_palaces.length === 12
  checks.push({
    name: 'ziwei-pan',
    status: ziweiPan.status,
    ok: ziweiPan.ok,
    schemaReady: ziweiPanReady,
    palaceCount: Array.isArray(ziweiPan.data?.data?.twelve_palaces) ? ziweiPan.data.data.twelve_palaces.length : null,
  })
  assertCondition(ziweiPanReady, `/api/ziwei/pan 异常: ${ziweiPan.status} ${JSON.stringify(ziweiPan.data)}`)

  const qimenPaipan = await request('/api/qimen/paipan', {
    method: 'POST',
    body: { year: 2024, month: 2, day: 4, hour: 16, minute: 30, panType: 2 },
  })
  const qimenPaipanReady = qimenPaipan.ok &&
    isObject(qimenPaipan.data?.fourPillars) &&
    Array.isArray(qimenPaipan.data?.palaces) &&
    qimenPaipan.data.palaces.length === 9
  checks.push({
    name: 'qimen-paipan',
    status: qimenPaipan.status,
    ok: qimenPaipan.ok,
    schemaReady: qimenPaipanReady,
    palaceCount: Array.isArray(qimenPaipan.data?.palaces) ? qimenPaipan.data.palaces.length : null,
  })
  assertCondition(qimenPaipanReady, `/api/qimen/paipan 异常: ${qimenPaipan.status} ${JSON.stringify(qimenPaipan.data)}`)

  const meihuaPaipan = await request('/api/meihua/paipan', {
    method: 'POST',
    body: { method: 'number', num1: 7, num2: 12 },
  })
  const meihuaPaipanReady = meihuaPaipan.ok &&
    meihuaPaipan.data?.success === true &&
    isObject(meihuaPaipan.data?.benGua) &&
    isObject(meihuaPaipan.data?.bianGua)
  checks.push({
    name: 'meihua-paipan',
    status: meihuaPaipan.status,
    ok: meihuaPaipan.ok,
    schemaReady: meihuaPaipanReady,
    benGua: meihuaPaipan.data?.benGua?.name || '',
  })
  assertCondition(meihuaPaipanReady, `/api/meihua/paipan 异常: ${meihuaPaipan.status} ${JSON.stringify(meihuaPaipan.data)}`)

  const liuyaoPaipan = await request('/api/liuyao/paipan', {
    method: 'POST',
    body: {
      mode: 'manual',
      question: '测试',
      tosses: [[2, 2, 2], [2, 2, 3], [2, 3, 3], [3, 3, 3], [2, 3, 2], [3, 2, 3]],
    },
  })
  const liuyaoPaipanReady = liuyaoPaipan.ok &&
    typeof liuyaoPaipan.data?.本卦 === 'string' &&
    typeof liuyaoPaipan.data?.变卦 === 'string' &&
    Array.isArray(liuyaoPaipan.data?.六爻) &&
    liuyaoPaipan.data.六爻.length === 6
  checks.push({
    name: 'liuyao-paipan',
    status: liuyaoPaipan.status,
    ok: liuyaoPaipan.ok,
    schemaReady: liuyaoPaipanReady,
    yaoCount: Array.isArray(liuyaoPaipan.data?.六爻) ? liuyaoPaipan.data.六爻.length : null,
  })
  assertCondition(liuyaoPaipanReady, `/api/liuyao/paipan 异常: ${liuyaoPaipan.status} ${JSON.stringify(liuyaoPaipan.data)}`)

  const zeji = await request('/api/zeji', {
    method: 'POST',
    body: {
      zejiType: '搬家',
      startDate: '2024-02-10',
      endDate: '2024-02-12',
      addr: '北京',
      name: '择吉分析',
    },
  })
  const zejiReady = zeji.ok &&
    zeji.data?.success === true &&
    typeof zeji.data?.result === 'string' &&
    zeji.data.result.includes('民俗文化参考')
  checks.push({
    name: 'zeji',
    status: zeji.status,
    ok: zeji.ok,
    schemaReady: zejiReady,
    zejiType: zeji.data?.zejiType || '',
  })
  assertCondition(zejiReady, `/api/zeji 异常: ${zeji.status} ${JSON.stringify(zeji.data)}`)

  const records = await request('/api/records')
  const recordsReady = records.ok && Array.isArray(records.data?.records || records.data)
  checks.push({
    name: 'records',
    status: records.status,
    ok: records.ok,
    schemaReady: recordsReady,
    recordsReturned: Array.isArray(records.data?.records) ? records.data.records.length : (Array.isArray(records.data) ? records.data.length : null),
  })
  assertCondition(recordsReady, `/api/records 异常: ${records.status} ${JSON.stringify(records.data)}`)

  const collections = await request('/api/collections?type=record')
  const collectionsReady = collections.ok && Array.isArray(collections.data?.collections || collections.data)
  checks.push({
    name: 'collections',
    status: collections.status,
    ok: collections.ok,
    schemaReady: collectionsReady,
    collectionsReturned: Array.isArray(collections.data?.collections) ? collections.data.collections.length : (Array.isArray(collections.data) ? collections.data.length : null),
  })
  assertCondition(collectionsReady, `/api/collections 异常: ${collections.status} ${JSON.stringify(collections.data)}`)
}

async function launchDesktopApp(report) {
  const { _electron: electron } = await import('playwright')
  const requireDesktop = createRequire(join(desktopDir, 'package.json'))
  const electronExecutable = requireDesktop('electron')
  const smokeExecutable = process.env.DESKTOP_SMOKE_EXECUTABLE || electronExecutable
  const smokeArgs = process.env.DESKTOP_SMOKE_EXECUTABLE ? [] : ['.']
  const launchOptions = {
    executablePath: smokeExecutable,
    args: smokeArgs,
    cwd: desktopDir,
    env: {
      ...process.env,
      ELECTRON_DISABLE_SECURITY_WARNINGS: '1',
      SHIAN_DESKTOP_API_TARGET: apiTarget,
      SHIAN_DESKTOP_USER_DATA_DIR: process.env.SHIAN_DESKTOP_USER_DATA_DIR || join(artifactDir, 'user-data')
    }
  }

  if (process.env.DESKTOP_SMOKE_EXECUTABLE) {
    const quitExistingApp = quitExistingMacosApp(smokeExecutable)
    report.launchPreflight = {
      installedExecutable: true,
      quitExistingApp,
    }
    if (!quitExistingApp.skipped) {
      await delay(1200)
    }
  }

  const launchAttempts = []
  for (const attempt of [1, 2]) {
    const startedAt = new Date().toISOString()
    try {
      const app = await electron.launch(launchOptions)
      launchAttempts.push({ attempt, startedAt, finishedAt: new Date().toISOString(), ok: true })
      report.launch = {
        executablePath: smokeExecutable,
        args: smokeArgs,
        cwd: desktopDir,
        attempts: launchAttempts,
      }
      return app
    } catch (error) {
      launchAttempts.push({
        attempt,
        startedAt,
        finishedAt: new Date().toISOString(),
        ok: false,
        error: error.message,
      })
      if (attempt === 1) {
        await delay(900)
        continue
      }
      report.launch = {
        executablePath: smokeExecutable,
        args: smokeArgs,
        cwd: desktopDir,
        attempts: launchAttempts,
      }
      throw error
    }
  }
  throw new Error('Electron launch attempts exhausted')
}

async function requestHttp(path, options = {}, cookie = '') {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${apiTarget}${path}`, {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        Origin: apiTarget,
        Referer: `${apiTarget}/`,
        ...(cookie ? { Cookie: cookie } : {}),
        ...(options.headers || {})
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    })
    const text = await response.text()
    let data = null
    try {
      data = text ? JSON.parse(text) : null
    } catch (_) {
      data = { raw: text }
    }
    const setCookie = response.headers.get('set-cookie') || ''
    return {
      ok: response.ok,
      status: response.status,
      data,
      cookie: setCookie.split(',').map((part) => part.split(';')[0].trim()).filter(Boolean).join('; ')
    }
  } finally {
    clearTimeout(timer)
  }
}

async function runBackendContractOnly() {
  ensureArtifactDir()
  const checks = []
  const report = {
    passed: false,
    mode: 'http-backend-contract',
    generatedAt: new Date().toISOString(),
    artifactDir: resolve(artifactDir),
    apiTarget,
    qaUser,
    checks
  }
  writeFileSync(join(artifactDir, 'pending.json'), `${JSON.stringify(report, null, 2)}\n`)

  const health = await requestHttp('/api/health')
  checks.push({ name: 'health', status: health.status, ok: health.ok })
  assertCondition(health.ok, `后端 /api/health 失败: ${health.status}`)

  const login = await requestHttp('/api/login', {
    method: 'POST',
    body: { username: qaUser, password: qaPassword }
  })
  checks.push({
    name: 'login',
    status: login.status,
    ok: login.ok,
    username: login.data?.username || '',
    hasCookie: Boolean(login.cookie)
  })
  assertCondition(login.ok && login.cookie, `后端登录失败: ${login.status} ${JSON.stringify(login.data)}`)
  let sessionCookie = login.cookie

  const csrf = await requestHttp('/api/csrf-token', {}, sessionCookie)
  sessionCookie = mergeCookies(sessionCookie, csrf.cookie)
  const csrfToken = csrf.data?.csrf_token || ''
  checks.push({
    name: 'csrf-token',
    status: csrf.status,
    ok: csrf.ok,
    hasToken: typeof csrfToken === 'string' && csrfToken.length > 20
  })
  assertCondition(csrf.ok && csrfToken.length > 20, `后端 /api/csrf-token 异常: ${csrf.status} ${JSON.stringify(csrf.data)}`)

  const me = await requestHttp('/api/me', {}, sessionCookie)
  checks.push({
    name: 'me',
    status: me.status,
    ok: me.ok,
    username: me.data?.username || '',
    guest: Boolean(me.data?.guest)
  })
  assertCondition(me.ok && me.data?.username === qaUser, `后端 /api/me 用户异常: ${JSON.stringify(me.data)}`)

  const membership = await requestHttp('/api/membership', {}, sessionCookie)
  const membershipReady = isObject(membership.data) &&
    typeof membership.data.points === 'number' &&
    typeof membership.data.level === 'string'
  checks.push({
    name: 'membership',
    status: membership.status,
    ok: membership.ok,
    level: membership.data?.level || '',
    points: membership.data?.points,
    schemaReady: membershipReady
  })
  assertCondition(membership.ok && membershipReady, `后端 /api/membership 异常: ${membership.status} ${JSON.stringify(membership.data)}`)

  const points = await requestHttp('/api/points/log?page=1&per_page=5', {}, sessionCookie)
  const pointsReady = isObject(points.data) &&
    Array.isArray(points.data.logs) &&
    typeof points.data.total === 'number' &&
    typeof points.data.page === 'number' &&
    typeof points.data.per_page === 'number'
  checks.push({
    name: 'points-log',
    status: points.status,
    ok: points.ok,
    total: points.data?.total,
    logsReturned: Array.isArray(points.data?.logs) ? points.data.logs.length : null,
    schemaReady: pointsReady
  })
  assertCondition(points.ok && pointsReady, `后端 /api/points/log 异常: ${points.status} ${JSON.stringify(points.data)}`)

  const comprehensiveOptions = await requestHttp('/api/comprehensive/options', {}, sessionCookie)
  const comprehensiveOptionsReady = isObject(comprehensiveOptions.data) &&
    nonEmptyArray(comprehensiveOptions.data.llm_models) &&
    nonEmptyArray(comprehensiveOptions.data.reading_modes) &&
    nonEmptyArray(comprehensiveOptions.data.tool_models) &&
    typeof comprehensiveOptions.data.points === 'number'
  checks.push({
    name: 'comprehensive-options',
    status: comprehensiveOptions.status,
    ok: comprehensiveOptions.ok,
    llmModels: Array.isArray(comprehensiveOptions.data?.llm_models) ? comprehensiveOptions.data.llm_models.length : null,
    readingModes: Array.isArray(comprehensiveOptions.data?.reading_modes) ? comprehensiveOptions.data.reading_modes.length : null,
    toolModels: Array.isArray(comprehensiveOptions.data?.tool_models) ? comprehensiveOptions.data.tool_models.length : null,
    schemaReady: comprehensiveOptionsReady
  })
  assertCondition(comprehensiveOptions.ok && comprehensiveOptionsReady, `后端 /api/comprehensive/options 异常: ${comprehensiveOptions.status} ${JSON.stringify(comprehensiveOptions.data)}`)

  const recommendTools = await requestHttp('/api/comprehensive/recommend-tools', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
    body: {
      question: '最近事业选择怎么判断？',
      reading_mode: 'concise'
    }
  }, sessionCookie)
  const recommendToolsReady = isObject(recommendTools.data) &&
    nonEmptyArray(recommendTools.data.tool_models) &&
    typeof recommendTools.data.reason === 'string' &&
    typeof recommendTools.data.estimated_cost === 'number'
  checks.push({
    name: 'comprehensive-recommend-tools',
    status: recommendTools.status,
    ok: recommendTools.ok,
    toolModels: Array.isArray(recommendTools.data?.tool_models) ? recommendTools.data.tool_models : [],
    estimatedCost: recommendTools.data?.estimated_cost,
    schemaReady: recommendToolsReady
  })
  assertCondition(recommendTools.ok && recommendToolsReady, `后端 /api/comprehensive/recommend-tools 异常: ${recommendTools.status} ${JSON.stringify(recommendTools.data)}`)

  const guide = await requestHttp('/api/comprehensive/guide', {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken },
    body: {
      question: '最近事业选择怎么判断？',
      answers: []
    }
  }, sessionCookie)
  const guideStatus = guide.data?.status || ''
  const guideReady = isObject(guide.data) &&
    ['ask', 'recommend'].includes(guideStatus) &&
    (
      (guideStatus === 'ask' && typeof guide.data.assistant_message === 'string' && guide.data.assistant_message.trim().length > 0) ||
      (guideStatus === 'recommend' && nonEmptyArray(guide.data.tool_models))
    )
  checks.push({
    name: 'comprehensive-guide',
    status: guide.status,
    ok: guide.ok,
    guideStatus,
    source: guide.data?.source || '',
    schemaReady: guideReady
  })
  assertCondition(guide.ok && guideReady, `后端 /api/comprehensive/guide 异常: ${guide.status} ${JSON.stringify(guide.data)}`)

  const conversations = await requestHttp('/api/comprehensive/conversations', {}, sessionCookie)
  const conversationsReady = Array.isArray(conversations.data)
  checks.push({
    name: 'comprehensive-conversations',
    status: conversations.status,
    ok: conversations.ok,
    conversationsReturned: Array.isArray(conversations.data) ? conversations.data.length : null,
    schemaReady: conversationsReady
  })
  assertCondition(conversations.ok && conversationsReady, `后端 /api/comprehensive/conversations 异常: ${conversations.status} ${JSON.stringify(conversations.data)}`)

  await runCoreBackendChecks(checks, async (path, options = {}) => {
    const headers = {
      ...(options.headers || {}),
      ...(options.method === 'POST' ? { 'X-CSRFToken': csrfToken } : {}),
    }
    return requestHttp(path, { ...options, headers }, sessionCookie)
  })

  report.passed = true
  writeFileSync(join(artifactDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  console.log(JSON.stringify(report, null, 2))
}

async function requestFromPage(page, path, options = {}) {
  return await page.evaluate(async ({ path, options }) => {
    const response = await fetch(path, {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers || {})
      },
      credentials: 'include',
      body: options.body ? JSON.stringify(options.body) : undefined
    })
    const text = await response.text()
    let data = null
    try {
      data = text ? JSON.parse(text) : null
    } catch (_) {
      data = { raw: text }
    }
    return {
      ok: response.ok,
      status: response.status,
      data,
      cookie: document.cookie
    }
  }, { path, options })
}

async function main() {
  ensureArtifactDir()
  const checks = []
  const report = {
    passed: false,
    generatedAt: new Date().toISOString(),
    artifactDir: resolve(artifactDir),
    apiTarget,
    qaUser,
    checks
  }
  writeFileSync(join(artifactDir, 'pending.json'), `${JSON.stringify(report, null, 2)}\n`)

  let app = null
  let page = null
  const consoleErrors = []

  try {
    app = await launchDesktopApp(report)
    page = await app.firstWindow({ timeout: timeoutMs })
    page.on('console', (msg) => {
      if (msg.type() === 'error') consoleErrors.push(msg.text())
    })
    page.on('pageerror', (error) => consoleErrors.push(error.message))

    await page.waitForFunction(() => Boolean(window.shianDesktop?.platform), null, { timeout: timeoutMs })

    const health = await requestFromPage(page, '/api/health')
    checks.push({ name: 'health', status: health.status, ok: health.ok })
    assertCondition(health.ok, `桌面端 /api/health 失败: ${health.status}`)

    const login = await requestFromPage(page, '/api/login', {
      method: 'POST',
      body: { username: qaUser, password: qaPassword }
    })
    const sessionCookies = await page.context().cookies(page.url())
    checks.push({
      name: 'login',
      status: login.status,
      ok: login.ok,
      username: login.data?.username || '',
      hasCookie: sessionCookies.length > 0,
      visibleCookie: Boolean(login.cookie)
    })
    assertCondition(login.ok, `桌面端登录失败: ${login.status} ${JSON.stringify(login.data)}`)
    assertCondition(sessionCookies.length > 0, '桌面端登录后浏览器上下文没有写入 session cookie')

    const me = await requestFromPage(page, '/api/me')
    checks.push({
      name: 'me',
      status: me.status,
      ok: me.ok,
      username: me.data?.username || '',
      guest: Boolean(me.data?.guest)
    })
    assertCondition(me.ok, `桌面端 /api/me 失败: ${me.status} ${JSON.stringify(me.data)}`)
    assertCondition(me.data?.username === qaUser, `桌面端 /api/me 用户异常: ${JSON.stringify(me.data)}`)

    const membership = await requestFromPage(page, '/api/membership')
    const membershipReady = isObject(membership.data) &&
      typeof membership.data.points === 'number' &&
      typeof membership.data.level === 'string'
    checks.push({
      name: 'membership',
      status: membership.status,
      ok: membership.ok,
      level: membership.data?.level || '',
      points: membership.data?.points,
      schemaReady: membershipReady
    })
    assertCondition(membership.ok, `桌面端 /api/membership 失败: ${membership.status} ${JSON.stringify(membership.data)}`)
    assertCondition(membershipReady, `桌面端 /api/membership 数据结构异常: ${JSON.stringify(membership.data)}`)

    const points = await requestFromPage(page, '/api/points/log?page=1&per_page=5')
    const pointsReady = isObject(points.data) &&
      Array.isArray(points.data.logs) &&
      typeof points.data.total === 'number' &&
      typeof points.data.page === 'number' &&
      typeof points.data.per_page === 'number'
    checks.push({
      name: 'points-log',
      status: points.status,
      ok: points.ok,
      total: points.data?.total,
      logsReturned: Array.isArray(points.data?.logs) ? points.data.logs.length : null,
      schemaReady: pointsReady
    })
    assertCondition(points.ok, `桌面端 /api/points/log 失败: ${points.status} ${JSON.stringify(points.data)}`)
    assertCondition(pointsReady, `桌面端 /api/points/log 数据结构异常: ${JSON.stringify(points.data)}`)

    const comprehensiveOptions = await requestFromPage(page, '/api/comprehensive/options')
    const comprehensiveOptionsReady = isObject(comprehensiveOptions.data) &&
      nonEmptyArray(comprehensiveOptions.data.llm_models) &&
      nonEmptyArray(comprehensiveOptions.data.reading_modes) &&
      nonEmptyArray(comprehensiveOptions.data.tool_models) &&
      typeof comprehensiveOptions.data.points === 'number'
    checks.push({
      name: 'comprehensive-options',
      status: comprehensiveOptions.status,
      ok: comprehensiveOptions.ok,
      llmModels: Array.isArray(comprehensiveOptions.data?.llm_models) ? comprehensiveOptions.data.llm_models.length : null,
      readingModes: Array.isArray(comprehensiveOptions.data?.reading_modes) ? comprehensiveOptions.data.reading_modes.length : null,
      toolModels: Array.isArray(comprehensiveOptions.data?.tool_models) ? comprehensiveOptions.data.tool_models.length : null,
      schemaReady: comprehensiveOptionsReady
    })
    assertCondition(comprehensiveOptions.ok, `桌面端 /api/comprehensive/options 失败: ${comprehensiveOptions.status} ${JSON.stringify(comprehensiveOptions.data)}`)
    assertCondition(comprehensiveOptionsReady, `桌面端 /api/comprehensive/options 数据结构异常: ${JSON.stringify(comprehensiveOptions.data)}`)

    const recommendTools = await requestFromPage(page, '/api/comprehensive/recommend-tools', {
      method: 'POST',
      body: {
        question: '最近事业选择怎么判断？',
        reading_mode: 'concise'
      }
    })
    const recommendToolsReady = isObject(recommendTools.data) &&
      nonEmptyArray(recommendTools.data.tool_models) &&
      typeof recommendTools.data.reason === 'string' &&
      typeof recommendTools.data.estimated_cost === 'number'
    checks.push({
      name: 'comprehensive-recommend-tools',
      status: recommendTools.status,
      ok: recommendTools.ok,
      toolModels: Array.isArray(recommendTools.data?.tool_models) ? recommendTools.data.tool_models : [],
      estimatedCost: recommendTools.data?.estimated_cost,
      schemaReady: recommendToolsReady
    })
    assertCondition(recommendTools.ok, `桌面端 /api/comprehensive/recommend-tools 失败: ${recommendTools.status} ${JSON.stringify(recommendTools.data)}`)
    assertCondition(recommendToolsReady, `桌面端 /api/comprehensive/recommend-tools 数据结构异常: ${JSON.stringify(recommendTools.data)}`)

    const guide = await requestFromPage(page, '/api/comprehensive/guide', {
      method: 'POST',
      body: {
        question: '最近事业选择怎么判断？',
        answers: []
      }
    })
    const guideStatus = guide.data?.status || ''
    const guideReady = isObject(guide.data) &&
      ['ask', 'recommend'].includes(guideStatus) &&
      (
        (guideStatus === 'ask' && typeof guide.data.assistant_message === 'string' && guide.data.assistant_message.trim().length > 0) ||
        (guideStatus === 'recommend' && nonEmptyArray(guide.data.tool_models))
      )
    checks.push({
      name: 'comprehensive-guide',
      status: guide.status,
      ok: guide.ok,
      guideStatus,
      source: guide.data?.source || '',
      schemaReady: guideReady
    })
    assertCondition(guide.ok, `桌面端 /api/comprehensive/guide 失败: ${guide.status} ${JSON.stringify(guide.data)}`)
    assertCondition(guideReady, `桌面端 /api/comprehensive/guide 数据结构异常: ${JSON.stringify(guide.data)}`)

    const conversations = await requestFromPage(page, '/api/comprehensive/conversations')
    const conversationsReady = Array.isArray(conversations.data)
    checks.push({
      name: 'comprehensive-conversations',
      status: conversations.status,
      ok: conversations.ok,
      conversationsReturned: Array.isArray(conversations.data) ? conversations.data.length : null,
      schemaReady: conversationsReady
    })
    assertCondition(conversations.ok, `桌面端 /api/comprehensive/conversations 失败: ${conversations.status} ${JSON.stringify(conversations.data)}`)
    assertCondition(conversationsReady, `桌面端 /api/comprehensive/conversations 数据结构异常: ${JSON.stringify(conversations.data)}`)

    await runCoreBackendChecks(checks, (path, options = {}) => requestFromPage(page, path, options))

    const blockingErrors = consoleErrors.filter((item) => !/favicon|Failed to load resource.*avatar_/i.test(item))
    assertCondition(blockingErrors.length === 0, `桌面端控制台错误: ${blockingErrors.slice(0, 3).join(' | ')}`)

    report.passed = true
    writeFileSync(join(artifactDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
    console.log(JSON.stringify(report, null, 2))
  } catch (error) {
    writeFailure(report, error, { consoleErrors })
    throw error
  } finally {
    if (app) await app.close()
  }
}

const runner = httpOnly ? runBackendContractOnly : main

runner().catch((error) => {
  console.error(error.message)
  process.exit(1)
})
