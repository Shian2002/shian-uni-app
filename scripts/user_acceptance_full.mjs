#!/usr/bin/env node

import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.env.QA_BASE_URL || process.env.REGRESSION_BASE_URL || 'https://shianjieyouwu.com'
const qaMode = process.env.QA_MODE || 'online'
const qaRunSuffix = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(6, 14)
const qaUser = process.env.QA_USER || (qaMode === 'local' ? `qalocal${qaRunSuffix}` : 'test1')
const qaPassword = process.env.QA_PASSWORD || ''
const timeoutMs = Number(process.env.QA_TIMEOUT_MS || 25000)
const streamTimeoutMs = Number(process.env.QA_STREAM_TIMEOUT_MS || 120000)
const mockAgentStream = process.env.QA_MOCK_AGENT_STREAM
  ? process.env.QA_MOCK_AGENT_STREAM !== '0'
  : qaMode === 'local'
const artifactDir = process.env.QA_ARTIFACT_DIR || join('artifacts', 'user-acceptance', new Date().toISOString().replace(/[:.]/g, '-'))

const desktopViewport = { width: 1280, height: 800 }
const mobileViewports = [
  { width: 390, height: 844 },
  { width: 375, height: 812 },
]

const showCommunityRoute = qaMode === 'local' || process.env.QA_SHOW_COMMUNITY === '1'

const routes = [
  { name: '营销首页', hash: '/', texts: ['The Oriental Insight Agent', '开始解读'] },
  { name: '八字排盘', hash: '/pages/bazi-index/index?tab=free', texts: ['八字排盘', '免费'] },
  { name: '奇门遁甲', hash: '/pages/qimen/index?tab=free', texts: ['奇门遁甲', '奇门排盘'] },
  { name: '六爻排盘', hash: '/pages/liuyao/index', texts: ['六爻', '免费'] },
  { name: '梅花易数', hash: '/pages/meihua/index', texts: ['梅花易数', '排盘'] },
  { name: '紫微斗数', hash: '/pages/ziwei/index', texts: ['紫微斗数', '免费排盘'] },
  { name: '塔罗牌', hash: '/pages/tarot/index', texts: ['塔罗牌', '选择牌阵'] },
  { name: '择吉工具', hash: '/pages/zeji/index', texts: ['择吉'] },
  { name: '专属日历', hash: '/pages/calendar/index', texts: ['专属日历', '今天'] },
  ...(showCommunityRoute ? [{ name: '社区', hash: '/pages/community/index', texts: ['社区'] }] : []),
  { name: '关于我们', hash: '/pages/about/index', texts: ['关于'] },
  { name: '个人中心', hash: '/pages/profile/index', texts: ['个人'] },
  { name: '积分中心', hash: '/pages/points/index', texts: ['积分', '积分怎么用'] },
]

function ensureArtifactDir() {
  mkdirSync(artifactDir, { recursive: true })
}

function writeArtifact(name, data) {
  ensureArtifactDir()
  writeFileSync(join(artifactDir, name), typeof data === 'string' ? data : JSON.stringify(data, null, 2))
}

function safeName(name) {
  return name.replace(/[^a-zA-Z0-9\u4e00-\u9fa5_-]+/g, '-')
}

function routeUrl(hash) {
  return `${baseUrl}/#${hash}`
}

function assertCondition(condition, message) {
  if (!condition) throw new Error(message)
}

async function createTrackedPage(browser, name, viewport = desktopViewport) {
  const page = await browser.newPage({ viewport, deviceScaleFactor: viewport.width <= 480 ? 2 : 1, isMobile: viewport.width <= 480 })
  const consoleErrors = []
  const failedRequests = []
  const httpErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (error) => consoleErrors.push(error.message))
  page.on('response', (response) => {
    const status = response.status()
    const url = response.url()
    if (status >= 500 && !url.includes('/sockjs-node') && !url.includes('favicon')) {
      httpErrors.push({ url, status })
    }
  })
  page.on('requestfailed', (request) => {
    const url = request.url()
    if (!url.includes('/sockjs-node') && !url.includes('favicon')) {
      failedRequests.push({ url, failure: request.failure()?.errorText || 'request failed' })
    }
  })
  page._qa = { name, consoleErrors, failedRequests, httpErrors }
  return page
}

async function captureFailure(page, name, error) {
  const base = safeName(name)
  await page.screenshot({ path: join(artifactDir, `${base}.png`), fullPage: true }).catch(() => {})
  const html = await page.content().catch(() => '')
  if (html) writeArtifact(`${base}.html`, html)
  writeArtifact(`${base}.error.json`, {
    name,
    url: page.url(),
    message: error.message,
    consoleErrors: page._qa?.consoleErrors || [],
    failedRequests: page._qa?.failedRequests || [],
    httpErrors: page._qa?.httpErrors || [],
  })
}

async function pageSummary(page) {
  return await page.evaluate(() => ({
    href: location.href,
    hash: location.hash,
    title: document.title,
    text: document.body.innerText || '',
    mode: document.body.classList.contains('home-fixed-page')
      ? 'app'
      : (location.hash === '#/' || location.hash.indexOf('#/?') === 0 ? (window.__xcHomeMode || 'marketing') : 'page'),
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
    currentNav: Array.from(document.querySelectorAll('.nav-btn.current')).map((el) => (el.textContent || '').trim()),
    visibleButtons: Array.from(document.querySelectorAll('button, .nav-btn, .home-ai-send, .profile-picker, .tool-picker, .submit-btn, .btn, .tool-option, .profile-option'))
      .filter((el) => {
        const r = el.getBoundingClientRect()
        const style = getComputedStyle(el)
        return r.width > 0 && r.height > 0 && style.visibility !== 'hidden' && style.display !== 'none'
      })
      .map((el) => (el.textContent || el.getAttribute('data-href') || '').trim())
      .slice(0, 120),
  }))
}

async function waitForRenderedApp(page, expectedText = '') {
  await page.waitForLoadState('domcontentloaded', { timeout: timeoutMs }).catch(() => {})
  await page.waitForLoadState('networkidle', { timeout: timeoutMs }).catch(() => {})
  await page.waitForFunction((expectedText) => {
    const text = document.body.innerText || ''
    if (expectedText && text.includes(expectedText)) return true
    return text.includes('时安解忧屋') ||
      text.includes('The Oriental Insight Agent') ||
      text.includes('选择命盘') ||
      Boolean(document.querySelector('.page-root, .marketing-landing, .home-ai-main, .topnav'))
  }, expectedText, { timeout: timeoutMs })
  await page.waitForTimeout(500)
}

async function assertHealthyPage(page, name, texts = []) {
  await page.waitForTimeout(900)
  const summary = await pageSummary(page)
  assertCondition(summary.text.trim().length > 20, `${name} 疑似白屏`)
  assertCondition(!summary.horizontalOverflow, `${name} 出现水平溢出`)
  for (const text of texts) {
    assertCondition(summary.text.includes(text), `${name} 缺少关键文案: ${text}`)
  }
  const blockingErrors = (page._qa?.consoleErrors || []).filter((item) => {
    return !/favicon|ResizeObserver loop|Failed to load resource: the server responded with a status of 404.*avatar_/i.test(item)
  })
  const httpErrors = page._qa?.httpErrors || []
  const httpErrorText = httpErrors.slice(0, 5).map((item) => `${item.status} ${item.url}`).join(' | ')
  assertCondition(blockingErrors.length === 0, `${name} 控制台错误: ${blockingErrors.slice(0, 3).join(' | ')}${httpErrorText ? `；接口错误: ${httpErrorText}` : ''}`)
  return summary
}

async function api(page, path, options = {}) {
  return await page.evaluate(async ({ path, options }) => {
    const response = await fetch(path, {
      credentials: 'same-origin',
      headers: Object.assign({ 'Content-Type': 'application/json' }, options.headers || {}),
      method: options.method || 'GET',
      body: options.body ? JSON.stringify(options.body) : undefined,
    })
    const text = await response.text()
    let data = null
    try { data = text ? JSON.parse(text) : null } catch (_) { data = { raw: text } }
    return { ok: response.ok, status: response.status, data }
  }, { path, options })
}

async function clickVisibleMarketingAgentEntry(page) {
  await page.evaluate(() => {
    const visible = (el) => {
      const rect = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
    }
    const target = Array.from(document.querySelectorAll('.marketing-agent-link'))
      .find((el) => visible(el) && (el.textContent || '').replace(/\s+/g, '').includes('时安agent'))
    if (!target) throw new Error('找不到可见的时安agent入口')
    target.click()
  })
}

async function tapVisibleSelector(page, selector, errorMessage) {
  await page.evaluate(({ selector, errorMessage }) => {
    const visible = (el) => {
      const rect = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
    }
    const target = Array.from(document.querySelectorAll(selector)).find(visible)
    if (!target) throw new Error(errorMessage)
    const rect = target.getBoundingClientRect()
    const x = rect.left + rect.width / 2
    const y = rect.top + rect.height / 2
    for (const type of ['pointerdown', 'mousedown', 'touchstart', 'pointerup', 'mouseup', 'touchend', 'click']) {
      if (type.startsWith('touch')) {
        target.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true, touches: [], changedTouches: [] }))
      } else if (type.startsWith('pointer')) {
        target.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, pointerType: 'mouse' }))
      } else {
        target.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y }))
      }
    }
  }, { selector, errorMessage })
}

async function ensureTestLogin(page) {
  await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
  await waitForRenderedApp(page)

  let result = await api(page, '/api/login', { method: 'POST', body: { username: qaUser, password: qaPassword } })
  if (!result.ok) {
    page._qa.consoleErrors = page._qa.consoleErrors.filter((item) => !item.includes('400 (BAD REQUEST)') && !item.includes('401 (UNAUTHORIZED)'))
    result = await api(page, '/api/register', { method: 'POST', body: { username: qaUser, password: qaPassword } })
    assertCondition(result.ok, `注册 ${qaUser} 失败: ${JSON.stringify(result.data)}`)
  }
  await page.evaluate(({ user }) => {
    try {
      uni.setStorageSync('xc_token', 'session')
      uni.setStorageSync('xc_user', user)
      localStorage.setItem('xc_token', 'session')
      localStorage.setItem('xc_user', user)
      localStorage.removeItem('xc_home_comprehensive_draft_v1')
      sessionStorage.removeItem('xc_comprehensive_resume_id')
      window.dispatchEvent(new CustomEvent('xc-auth-changed', { detail: { loggedIn: true, user: { username: user } } }))
    } catch (_) {}
  }, { user: qaUser })
  page._qa.consoleErrors = page._qa.consoleErrors.filter((item) => !item.includes('401 (UNAUTHORIZED)'))
  const me = await api(page, '/api/me')
  assertCondition(me.ok && me.data && me.data.username === qaUser, `登录态异常: ${JSON.stringify(me.data)}`)
  if (qaMode === 'local') {
    const signIn = await api(page, '/api/membership/sign-in', { method: 'POST' }).catch(() => null)
    if (signIn?.ok) {
      await page.reload({ waitUntil: 'domcontentloaded', timeout: timeoutMs })
      await waitForRenderedApp(page)
    }
  }
  await prepareAgentLocalState(page)
  return me.data
}

async function prepareAgentLocalState(page) {
  await page.evaluate(({ user }) => {
    function scopedKeys(base) {
      const keys = new Set([`${base}:guest`, `${base}:${user}`])
      try {
        const raw = uni.getStorageSync('xc_user')
        const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
        const userKey = String((parsed && (parsed.id || parsed.username || parsed.phone)) || 'guest')
        keys.add(`${base}:${userKey}`)
      } catch (_) {
        keys.add(`${base}:guest`)
      }
      return Array.from(keys)
    }
    const values = {
      xc_home_question_guidance_enabled_v1: false,
      xc_home_send_confirm_skip_v1: true,
    }
    for (const [base, value] of Object.entries(values)) {
      for (const key of scopedKeys(base)) {
        try { uni.setStorageSync(key, value) } catch (_) {}
        try { localStorage.setItem(key, JSON.stringify(value)) } catch (_) {}
      }
    }
  }, { user: qaUser })
}

async function ensureProfiles(page) {
  const definitions = [
    { name: `${qaUser}-self`, gender: '男', birthTime: '1995-03-18 09:30', calType: '公历', birthAddr: '广州', profileType: 'self' },
    { name: `${qaUser}-other`, gender: '女', birthTime: '1997-08-12 15:20', calType: '公历', birthAddr: '深圳', profileType: 'customer' },
  ]
  const list = await api(page, '/api/profiles?sort=last_used')
  assertCondition(list.ok, `读取命盘失败: ${JSON.stringify(list.data)}`)
  const existing = Array.isArray(list.data?.profiles) ? list.data.profiles : []
  const profiles = []
  for (const item of definitions) {
    let found = existing.find((p) => p.name === item.name)
    if (!found) {
      const created = await api(page, '/api/profiles', { method: 'POST', body: item })
      assertCondition(created.ok, `创建命盘 ${item.name} 失败: ${JSON.stringify(created.data)}`)
      found = Object.assign({}, item, created.data)
    }
    profiles.push(found)
  }
  return profiles
}

async function checkUnauthAgentEntry(browser) {
  const page = await createTrackedPage(browser, '未登录时安Agent')
  try {
    await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
    await waitForRenderedApp(page, 'The Oriental Insight Agent')
    await page.context().clearCookies()
    await page.evaluate(() => {
      try {
        localStorage.removeItem('xc_token')
        localStorage.removeItem('xc_user')
        sessionStorage.clear()
        if (window.uni) {
          uni.removeStorageSync('xc_token')
          uni.removeStorageSync('xc_user')
          uni.removeStorageSync('xc_has_password')
        }
        window.dispatchEvent(new CustomEvent('xc-auth-changed', { detail: { type: 'logout', loggedIn: false } }))
      } catch (_) {}
    })
    await page.reload({ waitUntil: 'domcontentloaded', timeout: timeoutMs })
    await waitForRenderedApp(page, 'The Oriental Insight Agent')
    const entryState = await page.evaluate(() => {
      const visible = (el) => {
        const rect = el.getBoundingClientRect()
        const style = getComputedStyle(el)
        return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
      }
      const agent = Array.from(document.querySelectorAll('.marketing-agent-link'))
        .find((el) => visible(el) && (el.textContent || '').replace(/\s+/g, '').includes('时安agent'))
      const authCta = Array.from(document.querySelectorAll('.marketing-enter')).find(visible)
      return {
        hasAgent: Boolean(agent),
        authCtaText: (authCta && authCta.textContent || '').trim(),
      }
    })
    assertCondition(entryState.hasAgent, '营销首页缺少时安agent入口')
    assertCondition(entryState.authCtaText === '登录/注册', `未登录辅助按钮文案异常: ${entryState.authCtaText}`)
    await clickVisibleMarketingAgentEntry(page)
    await waitForRenderedApp(page, 'The Oriental Insight Agent')
    const modal = await page.evaluate(() => {
      const loginModal = document.querySelector('#topnavLoginModal.open')
      const text = loginModal ? loginModal.innerText || '' : ''
      return {
        open: Boolean(loginModal),
        hasPassword: text.includes('密码登录'),
        hasCode: text.includes('验证码登录'),
        hasGitee: text.includes('Gitee 验证登录'),
        theme: document.documentElement.getAttribute('data-theme') || document.body.getAttribute('data-theme') || '',
      }
    })
    assertCondition(modal.open, '未登录点击时安agent应弹出登录弹窗')
    assertCondition(modal.hasPassword && modal.hasCode && modal.hasGitee, '登录弹窗缺少密码/验证码/Gitee 登录入口')
    assertCondition(modal.theme === 'light', `未显式选择主题时登录弹窗应为亮色，实际: ${modal.theme}`)
    const summary = await assertHealthyPage(page, '未登录时安Agent', ['The Oriental Insight Agent', '开始解读'])
    assertCondition(!summary.text.includes('选择命盘'), '未登录不应进入时安 Agent 应用态')
    return { name: '未登录时安 Agent 登录弹窗', passed: true, summary, modal }
  } catch (error) {
    await captureFailure(page, '未登录时安Agent', error)
    throw error
  } finally {
    await page.close()
  }
}

async function checkRouteMatrix(browser) {
  const results = []
  const page = await createTrackedPage(browser, '路由矩阵')
  try {
    await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
    await waitForRenderedApp(page, 'The Oriental Insight Agent')
    for (const item of routes) {
      try {
        if (item.hash === '/') {
          await page.evaluate(() => {
            if (window.__topNavGo) window.__topNavGo('#/')
            else location.hash = '#/'
          })
        } else {
          await page.evaluate((hash) => {
            if (!window.__topNavGo) throw new Error('导航函数未就绪')
            window.__topNavGo('#' + hash)
          }, item.hash)
        }
        await waitForRenderedApp(page, item.texts[0])
        const summary = await assertHealthyPage(page, item.name, item.texts)
        await page.screenshot({ path: join(artifactDir, `路由矩阵-${safeName(item.name)}.png`), fullPage: true }).catch(() => {})
        results.push({ name: item.name, passed: true, href: summary.href, mode: summary.mode, currentNav: summary.currentNav.slice(0, 3) })
      } catch (error) {
        await captureFailure(page, `路由矩阵-${item.name}`, error)
        results.push({ name: item.name, passed: false, error: error.message, href: page.url() })
        await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs }).catch(() => {})
        await waitForRenderedApp(page, 'The Oriental Insight Agent').catch(() => {})
      }
    }
    return results
  } catch (error) {
    await captureFailure(page, '路由矩阵', error)
    throw error
  } finally {
    await page.close()
  }
}

async function openAgent(page) {
  await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
  await waitForRenderedApp(page, 'The Oriental Insight Agent')
  await prepareAgentLocalState(page)
  await clickVisibleMarketingAgentEntry(page)
  await waitForRenderedApp(page, '选择命盘')
  await prepareAgentLocalState(page)
  const summary = await assertHealthyPage(page, '时安 Agent 应用态', ['选择命盘', '选择术数'])
  assertCondition(summary.mode === 'app' || summary.hash.includes('app=1'), '时安 Agent 未进入应用态')
  return summary
}

async function disableQuestionGuidanceIfVisible(page) {
  await prepareAgentLocalState(page)
  const action = page.locator('.home-guidance-note-action').filter({ hasText: '以后直接解读' }).first()
  if (await action.count()) {
    await action.click()
    await page.waitForTimeout(500)
  }
}

async function selectProfiles(page, count) {
  await page.locator('.profile-picker').filter({ visible: true }).first().click()
  await page.waitForSelector('.profile-sheet-panel', { timeout: timeoutMs })
  await page.waitForFunction((count) => {
    return document.querySelectorAll('.profile-sheet-panel .profile-option').length >= count
  }, count, { timeout: timeoutMs })
  const options = page.locator('.profile-sheet-panel .profile-option')
  const optionCount = await options.count()
  assertCondition(optionCount >= count, `命盘数量不足: ${optionCount}`)
  const selected = []
  for (let i = 0; i < count; i += 1) {
    const option = options.nth(i)
    selected.push((await option.innerText()).trim())
    await option.click()
  }
  await page.locator('.profile-sheet-panel .sheet-btn').filter({ hasText: '确认' }).click()
  await page.waitForTimeout(500)
  const summary = await pageSummary(page)
  assertCondition(!summary.visibleButtons.includes('选择命盘'), '命盘选择后按钮仍显示选择命盘')
  return selected
}

async function selectProfileNames(page, names) {
  await page.locator('.profile-picker').filter({ visible: true }).first().click()
  await page.waitForSelector('.profile-sheet-panel', { timeout: timeoutMs })
  await page.waitForFunction((names) => {
    const text = document.querySelector('.profile-sheet-panel')?.textContent || ''
    return names.some((name) => text.includes(name))
  }, names, { timeout: timeoutMs })
  const selected = []
  for (const name of names) {
    let option = page.locator('.profile-sheet-panel .profile-option').filter({ hasText: name }).first()
    if (!(await option.count())) {
      const tabs = page.locator('.profile-sheet-panel .profile-tabs > *')
      const tabCount = await tabs.count()
      for (let i = 0; i < tabCount; i += 1) {
        await tabs.nth(i).click()
        await page.waitForTimeout(250)
        option = page.locator('.profile-sheet-panel .profile-option').filter({ hasText: name }).first()
        if (await option.count()) break
      }
    }
    assertCondition(await option.count(), `找不到命盘: ${name}`)
    const cls = (await option.getAttribute('class')) || ''
    if (!cls.includes('active')) await option.click()
    selected.push(name)
  }
  await page.locator('.profile-sheet-panel .sheet-btn').filter({ hasText: '确认' }).click()
  await page.waitForTimeout(500)
  const summary = await pageSummary(page)
  assertCondition(!summary.visibleButtons.includes('选择命盘'), '按名称选择命盘后按钮仍显示选择命盘')
  return selected
}

async function selectTools(page, tools) {
  await page.locator('.tool-picker').filter({ visible: true }).first().click()
  await page.waitForSelector('.ai-select-popover.tool-popover', { timeout: timeoutMs })
  const selected = await page.evaluate((tools) => {
    const labels = {
      bazi: '八字',
      qimen: '奇门',
      ziwei: '紫微',
      liuyao: '六爻',
      meihua: '梅花',
      tarot: '塔罗',
      zeji: '择吉',
    }
    const visible = (el) => {
      const r = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return r.width > 0 && r.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
    }
    const tap = (el) => {
      const r = el.getBoundingClientRect()
      const x = r.left + r.width / 2
      const y = r.top + r.height / 2
      for (const type of ['pointerdown', 'mousedown', 'touchstart', 'pointerup', 'mouseup', 'touchend', 'click']) {
        if (type.startsWith('touch')) {
          el.dispatchEvent(new TouchEvent(type, { bubbles: true, cancelable: true, touches: [], changedTouches: [] }))
        } else if (type.startsWith('pointer')) {
          el.dispatchEvent(new PointerEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y, pointerType: 'mouse' }))
        } else {
          el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, clientX: x, clientY: y }))
        }
      }
    }
    const panel = Array.from(document.querySelectorAll('.ai-select-popover.tool-popover')).find(visible)
    if (!panel) throw new Error('找不到可见术数弹层')
    const options = Array.from(panel.querySelectorAll('.ai-select-option.tool-select-option')).filter(visible)
    const auto = options.find((el) => (el.textContent || '').includes('自动选择'))
    if (auto && auto.classList.contains('active')) tap(auto)
    const chosen = []
    for (const tool of tools) {
      const label = labels[tool] || tool
      const option = options.find((el) => (el.textContent || '').includes(label))
      if (!option) throw new Error(`找不到术数选项: ${tool}`)
      if (!option.classList.contains('active')) tap(option)
      chosen.push(label)
    }
    document.body.click()
    return chosen
  }, tools)
  await page.waitForTimeout(500)
  const summary = await pageSummary(page)
  assertCondition(tools.every((tool) => {
    const expected = { bazi: '八字', qimen: '奇门', ziwei: '紫微' }[tool] || tool
    return summary.text.includes(expected)
  }) || !summary.visibleButtons.includes('自动选术数'), '术数选择后仍显示自动选术数')
  return selected
}

async function fillAgentQuestion(page, question) {
  await page.waitForSelector('.home-ai-input', { timeout: timeoutMs })
  await page.evaluate((question) => {
    const wrapper = document.querySelector('.home-ai-input')
    if (!wrapper) throw new Error('找不到 Agent 输入框')
    const target = wrapper.querySelector('textarea, input, .uni-textarea-textarea') || wrapper
    const setter = Object.getOwnPropertyDescriptor(Object.getPrototypeOf(target), 'value')?.set
    if (setter) {
      setter.call(target, question)
    } else {
      target.value = question
    }
    target.textContent = question
    target.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, inputType: 'insertText', data: question }))
    target.dispatchEvent(new Event('change', { bubbles: true, composed: true }))
    wrapper.dispatchEvent(new InputEvent('input', { bubbles: true, composed: true, inputType: 'insertText', data: question }))
    wrapper.dispatchEvent(new Event('change', { bubbles: true, composed: true }))
  }, question)
  await page.waitForFunction((question) => {
    const wrapper = document.querySelector('.home-ai-input')
    const target = wrapper?.querySelector('textarea, input, .uni-textarea-textarea')
    return (target?.value || wrapper?.textContent || '').includes(question)
  }, question, { timeout: timeoutMs })
}

async function askAgent(page, question) {
  await fillAgentQuestion(page, question)
  await page.evaluate(() => {
    if (!window.uni || window.__qaToastPatched) return
    window.__qaToastPatched = true
    window.__qaToasts = []
    const original = uni.showToast
    uni.showToast = function(options) {
      try { window.__qaToasts.push(options && options.title ? String(options.title) : '') } catch (_) {}
      return original.apply(this, arguments)
    }
  }).catch(() => {})
  const before = await page.evaluate(() => ({
    conv: window.__qaCurrentConvId || null,
    messages: document.body.innerText,
  }))
  const events = []
  await page.route('**/api/comprehensive/ask/stream', async (route) => {
    const request = route.request()
    let payload = null
    try { payload = JSON.parse(request.postData() || '{}') } catch (_) {}
    events.push({ type: 'request', url: request.url(), payload })
    if (mockAgentStream) {
      const conversationId = payload?.conversation_id || 9001
      const toolModels = payload?.tool_models?.length ? payload.tool_models : ['bazi']
      const paipan = payload?.paipan?.paipan && Object.keys(payload.paipan.paipan).length
        ? payload.paipan.paipan
        : { bazi: { ganzhi: ['乙亥', '己卯', '戊辰', '丁巳'], source: 'qa-mock' } }
      const artifacts = payload?.paipan?.artifacts && Object.keys(payload.paipan.artifacts).length
        ? payload.paipan.artifacts
        : { bazi: { title: '八字命盘', data: paipan.bazi || paipan, analysis: 'QA 模拟盘面' } }
      const chunks = [
        { stage: 'paipan_done', message: '盘面依据已准备，正在准备解读', paipan, artifacts, tool_models: toolModels },
        { stage: 'tool_analysis_start', message: '正在解读八字', tool: 'bazi', tool_key: 'bazi' },
        { tool: 'bazi', tool_key: 'bazi', content: 'QA 模拟单盘解析。' },
        { stage: 'generating', message: '正在生成综合合参总结', summary_start: true },
        { summary: true, content: 'QA 模拟综合结论。' },
        { done: true, conversation_id: conversationId, points_left: 1999, ai_single_credits: 19, ai_combo_credits: 20, tool_models: toolModels, paipan, artifacts },
      ]
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'text/event-stream; charset=utf-8', 'Cache-Control': 'no-cache' },
        body: chunks.map((chunk) => `data: ${JSON.stringify(chunk)}\n\n`).join(''),
      })
      return
    }
    await route.continue()
  })
  const sendButton = page.locator('.home-ai-send').filter({ visible: true }).first()
  assertCondition(await sendButton.count(), '找不到可见发送按钮')
  assertCondition(!((await sendButton.getAttribute('class')) || '').includes('disabled'), '发送按钮仍为禁用状态')
  const streamResponsePromise = page.waitForResponse((response) => {
    return response.url().includes('/api/comprehensive/ask/stream') && response.request().method() === 'POST'
  }, { timeout: timeoutMs }).catch(() => null)
  const clickConfirmIfVisible = async () => {
    const confirmStart = page.locator('.send-confirm-sheet .sheet-btn-primary').filter({ hasText: '开始解读' }).first()
    if (await confirmStart.count()) {
      const dontRemind = page.locator('.send-confirm-sheet .send-confirm-check').first()
      if (await dontRemind.count()) await dontRemind.click()
      await confirmStart.click()
      return true
    }
    return false
  }
  for (let attempt = 0; attempt < 3 && !events.some((event) => event.type === 'request'); attempt += 1) {
    await prepareAgentLocalState(page)
    if (attempt === 0) {
      await sendButton.click({ force: true })
    } else if (attempt === 1) {
      await page.keyboard.press('Enter')
    } else {
      await tapVisibleSelector(page, '.home-ai-send', '找不到可见发送按钮')
    }
    await page.waitForTimeout(300)
    await clickConfirmIfVisible()
    await page.waitForTimeout(1200)
  }
  const streamResponse = await streamResponsePromise
  if (streamResponse) {
    await Promise.race([
      streamResponse.finished().catch(() => {}),
      page.waitForTimeout(streamTimeoutMs),
    ])
  }
  await page.waitForFunction(() => {
    const text = document.body.innerText || ''
    return text.includes('盘面依据已准备') || text.includes('积分不足') || text.includes('生成失败') || Boolean(document.querySelector('.home-artifact-tabs, .artifact-tabs'))
  }, { timeout: streamTimeoutMs }).catch(() => {})
  await page.waitForFunction(() => {
    const text = document.body.innerText || ''
    const send = Array.from(document.querySelectorAll('.home-ai-send')).find((el) => {
      const r = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return r.width > 0 && r.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
    })
    const loadingDone = !send || !send.classList.contains('disabled')
    const stageDone = !text.includes('正在连接综合解读服务') && !text.includes('正在按所选命盘和术数生成')
    return loadingDone && stageDone
  }, { timeout: timeoutMs }).catch(() => {})
  await page.waitForTimeout(1200)
  const after = await page.evaluate(() => ({
    text: document.body.innerText || '',
    convText: Array.from(document.querySelectorAll('.home-ai-message, .message, .home-ai-chat, .home-artifact-tabs')).map((el) => (el.textContent || '').trim()).slice(-8),
    artifactTabs: Array.from(document.querySelectorAll('.artifact-tab, .home-artifact-tab, .tab-btn')).map((el) => (el.textContent || '').trim()).filter(Boolean),
  }))
  await page.unroute('**/api/comprehensive/ask/stream').catch(() => {})
  assertCondition(!after.text.includes('生成失败'), `${question} 返回生成失败`)
  assertCondition(!after.text.includes('请先选择命盘'), `${question} 未识别已选命盘`)
  if (!events.length) {
    const diagnostics = await page.evaluate(() => {
      const visible = (el) => {
        if (!el) return false
        const r = el.getBoundingClientRect()
        const style = getComputedStyle(el)
        return r.width > 0 && r.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
      }
      const wrapper = document.querySelector('.home-ai-input')
      const input = wrapper?.querySelector('textarea, input, .uni-textarea-textarea')
      const send = Array.from(document.querySelectorAll('.home-ai-send')).find(visible)
      const storage = {}
      for (const key of ['xc_token', 'xc_user', 'xc_home_question_guidance_enabled_v1:guest', 'xc_home_send_confirm_skip_v1:guest']) {
        try { storage[key] = uni.getStorageSync(key) } catch (_) {}
      }
      return {
        url: location.href,
        inputValue: input?.value || '',
        wrapperText: wrapper?.textContent || '',
        sendClass: send?.className || '',
        sendText: send?.textContent || '',
        sendConfirmVisible: Boolean(document.querySelector('.send-confirm-sheet')),
        questionGuideVisible: Boolean(document.querySelector('.question-guide-sheet')),
        profilePickerText: document.querySelector('.profile-picker')?.textContent || '',
        toolPickerText: document.querySelector('.tool-picker')?.textContent || '',
        toasts: window.__qaToasts || [],
        storage,
        bodyText: document.body.innerText || '',
      }
    }).catch((error) => ({ error: error.message }))
    writeArtifact(`agent-request-diagnostics-${Date.now()}.json`, diagnostics)
  }
  assertCondition(events.length > 0, `${question} 未捕获 Agent 请求`)
  return { before, after, request: events[0].payload }
}

async function checkAgentCritical(browser) {
  const page = await createTrackedPage(browser, '时安Agent核心')
  try {
    await ensureTestLogin(page)
    const profiles = await ensureProfiles(page)
    await openAgent(page)
    await disableQuestionGuidanceIfVisible(page)

    await selectProfiles(page, 1)
    await selectTools(page, ['bazi'])
    const first = await askAgent(page, '请用八字看我最近三个月事业发展，先起盘再给建议')
    assertCondition((first.request.tool_models || []).includes('bazi') || first.request.auto_select_tools, '八字首问没有进入术数选择/自动推荐流程')
    assertCondition(Array.isArray(first.request.profiles) && first.request.profiles.length === 1, '单命盘请求 profile 数量不正确')
    assertCondition(!first.request.history || first.request.history.length === 0, '首次提问不应带历史')

    const follow = await askAgent(page, '那刚才这个八字盘里，我下一步最应该注意什么？')
    assertCondition(Array.isArray(follow.request.history) && follow.request.history.length > 0, '普通追问没有携带历史')
    assertCondition(follow.request.paipan && Object.keys(follow.request.paipan.paipan || {}).length > 0, '普通追问没有复用原盘 paipan')
    assertCondition(follow.request.conversation_id, '普通追问没有携带 conversation_id')

    await page.locator('.home-ai-new-chat').filter({ visible: true }).first().click()
    await page.waitForTimeout(800)
    await selectProfileNames(page, [`${qaUser}-self`, `${qaUser}-other`])
    await selectTools(page, ['bazi', 'qimen', 'ziwei'])
    const multi = await askAgent(page, '请共同分析我和对方的合作关系，重点看八字奇门紫微合参')
    assertCondition(Array.isArray(multi.request.profiles) && multi.request.profiles.length >= 2, '多命盘共同分析没有传多个 profile')
    const multiTools = multi.request.tool_models || []
    assertCondition(multi.request.auto_select_tools || ['bazi', 'qimen', 'ziwei'].every((tool) => multiTools.includes(tool)), `多术数请求不完整: ${multiTools.join(',')}`)

    await page.click('.topnav-sidebar-btn')
    await page.waitForTimeout(800)
    const sidebarText = await page.evaluate(() => document.body.innerText || '')
    assertCondition(sidebarText.includes('对话历史') || sidebarText.includes('新对话'), '历史侧边栏未打开')
    await page.screenshot({ path: join(artifactDir, '时安Agent核心.png'), fullPage: true }).catch(() => {})

    await page.evaluate(() => {
      const home = Array.from(document.querySelectorAll('.nav-btn')).find((el) => (el.textContent || '').trim() === '首页')
      if (home) home.click()
      else window.location.hash = '#/'
    })
    await page.waitForTimeout(800)
    const homeSummary = await pageSummary(page)
    assertCondition(homeSummary.hash === '#/' && homeSummary.mode === 'marketing', '点击首页未回营销页')

    return {
      name: '时安 Agent 核心',
      profiles: profiles.map((p) => p.name),
      firstRequest: { tools: first.request.tool_models, profileCount: first.request.profiles?.length || 0 },
      followupRequest: { history: follow.request.history?.length || 0, hasPaipan: Boolean(follow.request.paipan?.paipan), conversationId: follow.request.conversation_id },
      multiRequest: { tools: multi.request.tool_models, profileCount: multi.request.profiles?.length || 0 },
    }
  } catch (error) {
    await captureFailure(page, '时安Agent核心', error)
    throw error
  } finally {
    await page.close()
  }
}

async function checkPointsPricing(browser) {
  const page = await createTrackedPage(browser, '积分会员转化链路')
  try {
    await ensureTestLogin(page)
    await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
    await waitForRenderedApp(page, 'The Oriental Insight Agent')
    await page.evaluate(() => {
      if (!window.__topNavGo) throw new Error('导航函数未就绪')
      window.__topNavGo('#/pages/points/index')
    })
    await waitForRenderedApp(page, '积分怎么用')
    await page.waitForFunction(() => {
      const el = document.querySelector('.points-page .usage-section')
      if (!el) return false
      const rect = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
    }, { timeout: timeoutMs })
    const summary = await assertHealthyPage(page, '积分会员转化链路', [
      '积分怎么用',
      '去问时安 agent',
      '短期问题',
      '300积分',
      '长期问题',
      '800积分',
      '复杂合参',
      '1500积分',
      '会员方案参考',
      '从首问到报告',
    ])
    const layout = await page.evaluate(() => {
      const visible = (selector) => {
        const el = document.querySelector(selector)
        if (!el) return false
        const rect = el.getBoundingClientRect()
        const style = getComputedStyle(el)
        return rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none'
      }
      return {
        usageCards: document.querySelectorAll('.usage-section .plan-card').length,
        planCards: document.querySelectorAll('.plan-section .plan-card').length,
        conversionSteps: document.querySelectorAll('.conversion-step').length,
        ctaVisible: visible('.usage-cta'),
        sectionTop: Math.round(document.querySelector('.usage-section')?.getBoundingClientRect().top || 0),
      }
    })
    assertCondition(layout.usageCards >= 4, `积分消耗卡数量不足: ${layout.usageCards}`)
    assertCondition(layout.planCards >= 4, `会员方案卡数量不足: ${layout.planCards}`)
    assertCondition(layout.conversionSteps >= 3, `报告链路步骤数量不足: ${layout.conversionSteps}`)
    assertCondition(layout.ctaVisible, '去问时安 agent 转化卡不可见')
    await page.locator('.usage-section').screenshot({ path: join(artifactDir, '积分会员-消耗说明.png') }).catch(() => {})
    await page.locator('.plan-section').screenshot({ path: join(artifactDir, '积分会员-会员方案.png') }).catch(() => {})
    await page.screenshot({ path: join(artifactDir, '积分会员-页面.png'), fullPage: true }).catch(() => {})

    await page.locator('.usage-cta').click()
    await page.waitForTimeout(1200)
    await waitForRenderedApp(page, '选择命盘')
    const agentSummary = await assertHealthyPage(page, '积分会员跳转时安Agent', ['时安解忧屋', '选择命盘', '选择术数'])
    assertCondition(agentSummary.mode === 'app' || agentSummary.hash.includes('app=1'), '积分会员页未跳转到时安 Agent 应用态')
    await page.screenshot({ path: join(artifactDir, '积分会员-跳转Agent.png'), fullPage: true }).catch(() => {})

    return {
      name: '积分会员转化链路',
      href: summary.href,
      layout,
      agentHref: agentSummary.href,
      agentMode: agentSummary.mode,
    }
  } catch (error) {
    await captureFailure(page, '积分会员转化链路', error)
    throw error
  } finally {
    await page.close()
  }
}

async function checkMobile(browser) {
  const results = []
  for (const viewport of mobileViewports) {
    const page = await createTrackedPage(browser, `移动端-${viewport.width}`, viewport)
    try {
      await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
      await waitForRenderedApp(page, 'The Oriental Insight Agent')
      const marketing = await assertHealthyPage(page, `移动端营销页-${viewport.width}`, ['The Oriental Insight Agent'])
      await ensureTestLogin(page)
      await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
      await waitForRenderedApp(page, 'The Oriental Insight Agent')
      await clickVisibleMarketingAgentEntry(page)
      await waitForRenderedApp(page, '选择命盘')
      const agent = await assertHealthyPage(page, `移动端Agent-${viewport.width}`, ['选择命盘'])
      await page.screenshot({ path: join(artifactDir, `移动端-${viewport.width}.png`), fullPage: true }).catch(() => {})
      results.push({ viewport, marketing: marketing.href, agent: agent.href })
    } catch (error) {
      await captureFailure(page, `移动端-${viewport.width}`, error)
      throw error
    } finally {
      await page.close()
    }
  }
  return results
}

async function main() {
  ensureArtifactDir()
  const browser = await chromium.launch({ headless: process.env.QA_HEADLESS !== '0' })
  const results = []
  try {
    results.push(await checkUnauthAgentEntry(browser))
    results.push({ name: '路由矩阵', results: await checkRouteMatrix(browser) })
    results.push(await checkAgentCritical(browser))
    results.push(await checkPointsPricing(browser))
    results.push({ name: '移动端', results: await checkMobile(browser) })
    const report = { baseUrl, qaMode, qaUser, passed: true, artifactDir, results }
    writeArtifact('report.json', report)
    console.log(JSON.stringify(report, null, 2))
  } catch (error) {
    const report = { baseUrl, qaMode, qaUser, passed: false, artifactDir, error: error.message, results }
    writeArtifact('report.json', report)
    console.error(JSON.stringify(report, null, 2))
    process.exit(1)
  } finally {
    await browser.close()
  }
}

main()
