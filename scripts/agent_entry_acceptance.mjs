#!/usr/bin/env node

import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.env.QA_BASE_URL || 'http://localhost:5173'
const qaMode = process.env.QA_MODE || 'local'
const runSuffix = new Date().toISOString().replace(/[-:.TZ]/g, '').slice(6, 14)
const qaUser = process.env.QA_USER || (qaMode === 'local' ? `qaentry${runSuffix}` : 'test1')
const qaPassword = process.env.QA_PASSWORD || ''
const timeoutMs = Number(process.env.QA_TIMEOUT_MS || 25000)
const artifactDir = process.env.QA_ARTIFACT_DIR || join('artifacts', 'agent-entry', new Date().toISOString().replace(/[:.]/g, '-'))

const viewports = [
  { name: 'desktop', width: 1280, height: 800 },
  { name: 'mobile-390', width: 390, height: 844 },
]

function ensureArtifactDir() {
  mkdirSync(artifactDir, { recursive: true })
}

function writeArtifact(name, data) {
  ensureArtifactDir()
  writeFileSync(join(artifactDir, name), typeof data === 'string' ? data : JSON.stringify(data, null, 2))
}

function routeUrl(hash = '/') {
  return `${baseUrl}/#${hash}`
}

function assertCondition(condition, message) {
  if (!condition) throw new Error(message)
}

async function createPage(browser, viewport) {
  const page = await browser.newPage({
    viewport: { width: viewport.width, height: viewport.height },
    deviceScaleFactor: viewport.width <= 480 ? 2 : 1,
    isMobile: viewport.width <= 480,
  })
  const consoleErrors = []
  const httpErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (error) => consoleErrors.push(error.message))
  page.on('response', (response) => {
    const status = response.status()
    const url = response.url()
    if (status >= 500 && !url.includes('favicon')) httpErrors.push({ status, url })
  })
  page._entryQa = { consoleErrors, httpErrors }
  return page
}

async function waitForHome(page) {
  await page.waitForLoadState('domcontentloaded', { timeout: timeoutMs }).catch(() => {})
  await page.waitForFunction(() => {
    const text = document.body.innerText || ''
    return text.includes('The Oriental Insight Agent') ||
      text.includes('时安agent') ||
      Boolean(document.querySelector('.marketing-agent-link'))
  }, { timeout: timeoutMs })
  await page.waitForTimeout(500)
}

async function waitForAgent(page) {
  await page.waitForFunction(() => {
    const text = document.body.innerText || ''
    return text.includes('选择命盘') && text.includes('选择术数') && text.includes('事业') && text.includes('感情')
  }, { timeout: timeoutMs })
  await page.waitForTimeout(500)
}

async function clearAuth(page) {
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

async function login(page) {
  let result = await api(page, '/api/login', {
    method: 'POST',
    body: { username: qaUser, password: qaPassword },
  })
  if (!result.ok && qaMode === 'local') {
    result = await api(page, '/api/register', {
      method: 'POST',
      body: { username: qaUser, password: qaPassword },
    })
  }
  assertCondition(result.ok, `登录失败: ${JSON.stringify(result)}`)
  await page.evaluate(({ user }) => {
    try {
      const userPayload = { username: user }
      localStorage.setItem('xc_token', 'session')
      localStorage.setItem('xc_user', JSON.stringify(userPayload))
      if (window.uni) {
        uni.setStorageSync('xc_token', 'session')
        uni.setStorageSync('xc_user', userPayload)
      }
      window.dispatchEvent(new CustomEvent('xc-auth-changed', { detail: { loggedIn: true, user: userPayload } }))
    } catch (_) {}
  }, { user: qaUser })
  const me = await api(page, '/api/me')
  assertCondition(me.ok && me.data?.username === qaUser && me.data?.guest !== true, `登录态异常: ${JSON.stringify(me)}`)
  return me.data
}

async function readEntryState(page) {
  return await page.evaluate(() => {
    const visible = (el) => {
      if (!el) return false
      const rect = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
    }
    const agent = Array.from(document.querySelectorAll('.marketing-agent-link'))
      .find((el) => visible(el) && (el.textContent || '').replace(/\s+/g, '').includes('时安agent'))
    const appNavAgent = Array.from(document.querySelectorAll('.nav-btn'))
      .find((el) => visible(el) && (el.textContent || '').replace(/\s+/g, '').includes('时安agent'))
    const cta = Array.from(document.querySelectorAll('.marketing-enter')).find(visible)
    const bodyText = document.body.innerText || ''
    return {
      hasAgent: Boolean(agent),
      hasAppNavAgent: Boolean(appNavAgent),
      agentText: (agent?.textContent || '').trim(),
      appNavAgentText: (appNavAgent?.textContent || '').trim(),
      ctaText: (cta?.textContent || '').trim(),
      appControlsVisible: bodyText.includes('选择命盘') && bodyText.includes('选择术数'),
      questionTemplatesVisible: ['事业', '感情', '合作', '年运'].every((item) => bodyText.includes(item)),
      mode: document.body.classList.contains('home-fixed-page')
        ? 'app'
        : (location.hash.includes('app=1') ? 'app' : 'marketing'),
      bodyText,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
    }
  })
}

async function clickAgent(page) {
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

async function assertLoginModal(page) {
  await page.waitForFunction(() => {
    const modal = document.querySelector('#topnavLoginModal.open')
    return Boolean(modal && (modal.innerText || '').includes('密码登录'))
  }, { timeout: timeoutMs })
  const modal = await page.evaluate(() => {
    const el = document.querySelector('#topnavLoginModal.open')
    const text = el?.innerText || ''
    return {
      open: Boolean(el),
      hasPassword: text.includes('密码登录'),
      hasCode: text.includes('验证码登录'),
      hasGitee: text.includes('Gitee 验证登录'),
      theme: document.documentElement.getAttribute('data-theme') || document.body.getAttribute('data-theme') || '',
    }
  })
  assertCondition(modal.open, '登录弹窗未打开')
  assertCondition(modal.hasPassword, '登录弹窗缺少密码登录')
  assertCondition(modal.hasCode, '登录弹窗缺少验证码登录')
  assertCondition(modal.hasGitee, '登录弹窗缺少 Gitee 验证登录')
  assertCondition(modal.theme === 'light', `未显式选择主题时登录弹窗应为亮色，实际: ${modal.theme}`)
  return modal
}

async function assertNoBlockingErrors(page, label) {
  const consoleErrors = (page._entryQa?.consoleErrors || []).filter((item) => {
    return !/favicon|ResizeObserver loop|401 \(UNAUTHORIZED\)|400 \(BAD REQUEST\)/i.test(item)
  })
  const httpErrors = page._entryQa?.httpErrors || []
  assertCondition(consoleErrors.length === 0, `${label} 控制台错误: ${consoleErrors.slice(0, 3).join(' | ')}`)
  assertCondition(httpErrors.length === 0, `${label} 5xx 接口错误: ${JSON.stringify(httpErrors.slice(0, 3))}`)
}

async function checkViewport(browser, viewport) {
  const page = await createPage(browser, viewport)
  const result = { viewport: viewport.name, checks: [] }
  try {
    await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
    await waitForHome(page)
    await clearAuth(page)
    await page.reload({ waitUntil: 'domcontentloaded', timeout: timeoutMs })
    await waitForHome(page)
    const unauth = await readEntryState(page)
    assertCondition(unauth.hasAgent, `${viewport.name} 未登录首页缺少时安agent`)
    assertCondition(unauth.ctaText === '登录/注册', `${viewport.name} 未登录辅助按钮应为登录/注册，实际: ${unauth.ctaText}`)
    assertCondition(!unauth.horizontalOverflow, `${viewport.name} 未登录首页出现水平溢出`)
    await clickAgent(page)
    await waitForHome(page)
    const unauthAfterClick = await readEntryState(page)
    const modal = await assertLoginModal(page)
    assertCondition(unauthAfterClick.mode === 'marketing' && unauthAfterClick.hasAgent, `${viewport.name} 未登录点击时安agent应停留营销页`)
    assertCondition(!unauthAfterClick.appControlsVisible, `${viewport.name} 未登录不应看到 Agent 应用控件`)
    await page.screenshot({ path: join(artifactDir, `${viewport.name}-01-unauth-agent-login-modal.png`), fullPage: true })
    result.checks.push({ name: 'unauth-agent-login-modal', passed: true, state: unauth, afterClick: unauthAfterClick, modal })

    await page.goto(routeUrl('/'), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
    await waitForHome(page)
    const user = await login(page)
    await page.reload({ waitUntil: 'domcontentloaded', timeout: timeoutMs })
    await waitForHome(page)
    const authed = await readEntryState(page)
    assertCondition(authed.hasAgent || authed.hasAppNavAgent, `${viewport.name} 登录后缺少时安agent入口`)
    if (authed.hasAgent) {
      assertCondition(authed.ctaText === '进入应用', `${viewport.name} 登录后辅助按钮应为进入应用，实际: ${authed.ctaText}`)
    } else {
      assertCondition(authed.mode === 'app' && authed.appControlsVisible, `${viewport.name} 登录后既不在营销页，也未进入完整应用态`)
    }
    assertCondition(!authed.horizontalOverflow, `${viewport.name} 登录后首页出现水平溢出`)
    if (authed.mode !== 'app' || !authed.appControlsVisible) {
      await clickAgent(page)
      await waitForAgent(page)
    }
    const agent = await page.evaluate(() => ({
      href: location.href,
      hash: location.hash,
      text: document.body.innerText || '',
      mode: document.body.classList.contains('home-fixed-page')
        ? 'app'
        : (location.hash.includes('app=1') ? 'app' : 'unknown'),
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
    }))
    assertCondition(agent.mode === 'app', `${viewport.name} 登录后点击时安agent未进入应用态`)
    assertCondition(agent.text.includes('选择命盘') && agent.text.includes('选择术数'), `${viewport.name} Agent 应用态缺少核心控件`)
    assertCondition(['事业', '感情', '合作', '年运'].every((label) => agent.text.includes(label)), `${viewport.name} Agent 应用态缺少四类问题模板`)
    assertCondition(!agent.horizontalOverflow, `${viewport.name} Agent 应用态出现水平溢出`)
    await page.locator('[data-template-key="career"]').first().click({ timeout: timeoutMs })
    await page.waitForFunction(() => {
      const input = document.querySelector('.home-ai-input')
      const text = input?.value || input?.textContent || ''
      return text.includes('跳槽') && text.includes('事业趋势')
    }, { timeout: timeoutMs })
    const templatePrefill = await page.evaluate(() => {
      const input = document.querySelector('.home-ai-input')
      return input?.value || input?.textContent || ''
    })
    assertCondition(templatePrefill.includes('跳槽') && templatePrefill.includes('事业趋势'), `${viewport.name} 点击事业模板未预填问题`)
    await page.screenshot({ path: join(artifactDir, `${viewport.name}-02-authed-agent-app.png`), fullPage: true })
    result.checks.push({ name: 'authed-agent-app', passed: true, state: authed, agent, user: { username: user.username } })

    await page.evaluate(() => {
      if (window.__topNavGo) window.__topNavGo('#/pages/points/index')
      else location.hash = '#/pages/points/index'
    })
    await page.waitForFunction(() => {
      const text = document.body.innerText || ''
      return text.includes('积分怎么用') || text.includes('会员方案') || text.includes('短期问题')
    }, { timeout: timeoutMs })
    await page.screenshot({ path: join(artifactDir, `${viewport.name}-03-points-pricing.png`), fullPage: true })
    result.checks.push({ name: 'points-pricing-entry', passed: true })
    await assertNoBlockingErrors(page, viewport.name)
    result.passed = true
    return result
  } catch (error) {
    await page.screenshot({ path: join(artifactDir, `${viewport.name}-failure.png`), fullPage: true }).catch(() => {})
    result.passed = false
    result.error = error.message
    return result
  } finally {
    await page.close()
  }
}

async function main() {
  ensureArtifactDir()
  const browserExecutable = process.env.QA_BROWSER_EXECUTABLE || ''
  let exitCode = 0
  const browser = await chromium.launch({
    headless: process.env.QA_HEADLESS !== '0',
    ...(browserExecutable ? { executablePath: browserExecutable, args: ['--no-sandbox'] } : {}),
  })
  try {
    const results = []
    for (const viewport of viewports) {
      results.push(await checkViewport(browser, viewport))
    }
    const passed = results.every((item) => item.passed)
    const report = {
      generatedAt: new Date().toISOString(),
      baseUrl,
      qaMode,
      qaUser,
      artifactDir,
      passed,
      results,
    }
    writeArtifact('report.json', report)
    console.log(JSON.stringify(report, null, 2))
    if (!passed) exitCode = 1
  } finally {
    await Promise.race([
      browser.close(),
      new Promise((resolve) => setTimeout(resolve, 3000)),
    ])
    process.exit(exitCode)
  }
}

main()
