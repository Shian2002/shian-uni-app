#!/usr/bin/env node

import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.env.STORE_SCREENSHOT_BASE_URL || process.env.QA_BASE_URL || 'http://127.0.0.1:5173'
const outDir = process.env.STORE_SCREENSHOT_OUT_DIR || join('artifacts', 'store-screenshots', new Date().toISOString().replace(/[:.]/g, '-'))
let qaUser = process.env.STORE_SCREENSHOT_USER || `st${new Date().toISOString().replace(/[-:.TZ]/g, '').slice(8, 14)}${String(process.pid).slice(-3)}`
const qaPassword = process.env.STORE_SCREENSHOT_PASSWORD || ''
const timeoutMs = Number(process.env.STORE_SCREENSHOT_TIMEOUT_MS || 30000)
const systemBrowserChannel = process.env.STORE_SCREENSHOT_BROWSER_CHANNEL ||
  (existsSync('/Applications/Google Chrome.app') ? 'chrome' : (existsSync('/Applications/Microsoft Edge.app') ? 'msedge' : ''))
const systemBrowserExecutable = process.env.STORE_SCREENSHOT_BROWSER_EXECUTABLE || ''

const presets = [
  { id: 'mobile-390', label: '手机 390x844', viewport: { width: 390, height: 844 }, deviceScaleFactor: 3, isMobile: true },
  { id: 'mobile-430', label: '大屏手机 430x932', viewport: { width: 430, height: 932 }, deviceScaleFactor: 3, isMobile: true },
  { id: 'tablet-1024', label: '平板 1024x1366', viewport: { width: 1024, height: 1366 }, deviceScaleFactor: 2, isMobile: true },
  { id: 'desktop-1440', label: '桌面 1440x900', viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1, isMobile: false },
]

const story = [
  {
    id: '01-home',
    title: '首页主入口',
    hash: '/',
    expected: ['The Oriental Insight Agent', '时安agent', '开始解读'],
    modes: ['mobile-390', 'mobile-430', 'desktop-1440'],
    role: '展示品牌、具体问事入口、未登录登录/注册辅助按钮。',
  },
  {
    id: '02-login-modal',
    title: '旧登录弹窗',
    hash: '/',
    expected: ['密码登录', '验证码登录', 'Gitee 验证登录'],
    modes: ['mobile-390', 'desktop-1440'],
    beforeCapture: async (page) => {
      await page.evaluate(() => {
        if (window._openLoginModal) {
          window._openLoginModal()
          return
        }
        const target = Array.from(document.querySelectorAll('.marketing-agent-link, .marketing-enter, .nav-btn'))
          .find((el) => (el.textContent || '').replace(/\s+/g, '').includes('时安agent'))
        if (target) target.click()
      })
      await waitForText(page, '密码登录')
    },
    role: '证明产品入口没有丢，同时保留线上旧登录方式。',
  },
  {
    id: '03-agent-workbench',
    title: '时安 agent 工作台',
    hash: '/?app=1',
    expected: ['选择命盘', '选择术数', '事业', '感情', '合作', '年运'],
    modes: ['mobile-390', 'tablet-1024', 'desktop-1440'],
    login: true,
    role: '展示登录后的核心使用场景：四类问事模板、命盘、术数选择。',
  },
  {
    id: '04-points',
    title: '积分会员与消耗说明',
    hash: '/pages/points/index',
    expected: ['积分', '短期问题', '长期问题'],
    modes: ['mobile-390', 'desktop-1440'],
    login: true,
    beforeCapture: async (page) => {
      await waitForText(page, '短期问题')
      await page.evaluate(() => {
        const candidates = Array.from(document.querySelectorAll('body *'))
          .filter((el) => (el.innerText || el.textContent || '').includes('短期问题'))
          .map((el) => ({ el, rect: el.getBoundingClientRect() }))
          .filter((item) => item.rect.width > 0 && item.rect.height > 0)
          .sort((a, b) => (a.rect.width * a.rect.height) - (b.rect.width * b.rect.height))
        const target = candidates[0]?.el
        if (target) target.scrollIntoView({ block: 'center', inline: 'nearest' })
      })
      await page.waitForFunction(() => {
        const candidates = Array.from(document.querySelectorAll('body *'))
          .filter((el) => (el.innerText || el.textContent || '').includes('短期问题'))
          .map((el) => el.getBoundingClientRect())
          .filter((rect) => rect.width > 0 && rect.height > 0)
        return candidates.some((rect) => rect.top >= 0 && rect.bottom <= window.innerHeight)
      }, { timeout: timeoutMs })
      await page.waitForTimeout(400)
    },
    role: '解释免费额度、积分消耗和升级理由，是首购转化素材。',
  },
  {
    id: '05-bazi-tool',
    title: '八字排盘工具',
    hash: '/pages/bazi-index/index?tab=free',
    expected: ['八字排盘', '免费'],
    modes: ['mobile-390', 'desktop-1440'],
    role: '展示专业工具能力，辅助应用商店审核理解功能边界。',
  },
  {
    id: '06-profile-delete',
    title: '个人中心与账号注销',
    hash: '/pages/profile/index',
    expected: ['账号注销', '注销账号与删除数据'],
    modes: ['mobile-390', 'desktop-1440'],
    login: true,
    beforeCapture: async (page) => {
      await waitForText(page, '注销账号与删除数据')
      await page.evaluate(() => {
        const danger = document.querySelector('.danger-group')
        if (!danger) throw new Error('找不到账号注销区域')
        danger.scrollIntoView({ block: 'center', inline: 'nearest' })
        const item = danger.querySelector('.settings-item')
        const accordion = danger.querySelector('.settings-accordion')
        if (item && accordion && getComputedStyle(accordion).display === 'none') item.click()
      })
      await page.waitForFunction(() => {
        const accordion = document.querySelector('.danger-group .settings-accordion')
        const input = document.querySelector('#asDeleteConfirm-wrap input')
        const accordionVisible = accordion && getComputedStyle(accordion).display !== 'none'
        return accordionVisible && input && input.getAttribute('placeholder') === '输入：注销账号'
      }, { timeout: timeoutMs })
      await page.waitForTimeout(400)
    },
    role: '展示账号、隐私和注销入口，支撑 App Store/Google Play 审核。',
  },
]

function ensureDir() {
  mkdirSync(outDir, { recursive: true })
}

function routeUrl(hash) {
  return `${baseUrl}/#${hash}`
}

function routeParts(hash) {
  const value = hash || '/'
  const queryIndex = value.indexOf('?')
  return {
    path: queryIndex === -1 ? value : value.slice(0, queryIndex),
    query: queryIndex === -1 ? '' : value.slice(queryIndex),
  }
}

function safeName(value) {
  return value.replace(/[^a-zA-Z0-9\u4e00-\u9fa5_-]+/g, '-')
}

function assertCondition(condition, message) {
  if (!condition) throw new Error(message)
}

async function waitForText(page, text) {
  await page.waitForFunction((expected) => (document.body.innerText || '').includes(expected), text, { timeout: timeoutMs })
}

async function waitForApp(page, expected = '') {
  await page.waitForLoadState('domcontentloaded', { timeout: timeoutMs }).catch(() => {})
  await page.waitForLoadState('networkidle', { timeout: timeoutMs }).catch(() => {})
  await page.waitForFunction((expectedText) => {
    const text = document.body.innerText || ''
    return (expectedText && text.includes(expectedText)) ||
      text.includes('时安解忧屋') ||
      text.includes('The Oriental Insight Agent') ||
      text.includes('选择命盘') ||
      Boolean(document.querySelector('.page-root, .marketing-landing, .home-ai-main, .topnav'))
  }, expected, { timeout: timeoutMs })
  await page.waitForTimeout(600)
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

async function ensureLogin(page) {
  let result = await api(page, '/api/login', { method: 'POST', body: { username: qaUser, password: qaPassword } })
  if (!result.ok) {
    result = await api(page, '/api/register', { method: 'POST', body: { username: qaUser, password: qaPassword } })
  }
  if (!result.ok && /用户名已存在/.test(JSON.stringify(result.data))) {
    qaUser = `st${Math.floor(Math.random() * 100000000).toString().padStart(8, '0')}`
    result = await api(page, '/api/register', { method: 'POST', body: { username: qaUser, password: qaPassword } })
  }
  assertCondition(result.ok, `登录/注册截图账号失败: ${JSON.stringify(result.data)}`)
  const me = await api(page, '/api/me')
  const userPayload = {
    username: (me.data && me.data.username) || qaUser,
    id: me.data && me.data.id,
    phone: (me.data && me.data.phone) || '',
  }
  await page.evaluate(({ userPayload, hasPassword }) => {
    try {
      localStorage.setItem('xc_token', 'session')
      localStorage.setItem('xc_user', JSON.stringify(userPayload))
      localStorage.setItem('xc_has_password', hasPassword ? '1' : '0')
    } catch (_) {}
    try {
      if (window.uni && typeof window.uni.setStorageSync === 'function') {
        window.uni.setStorageSync('xc_token', 'session')
        window.uni.setStorageSync('xc_user', userPayload)
        window.uni.setStorageSync('xc_has_password', hasPassword ? '1' : '0')
      }
    } catch (_) {}
    try {
      if (window._openLoginModal_Close) window._openLoginModal_Close()
      document.querySelectorAll('#topnavLoginModal').forEach((el) => el.classList.remove('open'))
      window.dispatchEvent(new CustomEvent('xc-auth-changed', { detail: { type: 'login', loggedIn: true, user: userPayload } }))
    } catch (_) {}
  }, { userPayload, hasPassword: me.data ? me.data.has_password !== false : true })
  await page.waitForFunction(() => {
    const modal = document.querySelector('#topnavLoginModal.open')
    return !modal
  }, { timeout: timeoutMs })
  await waitForSession(page)
}

async function waitForSession(page) {
  await page.waitForFunction(() => {
    try {
      const token = localStorage.getItem('xc_token')
      const rawUser = localStorage.getItem('xc_user')
      return Boolean(token && rawUser)
    } catch (_) {
      return false
    }
  }, { timeout: timeoutMs })
}

async function navigateStory(page, item) {
  const { path, query } = routeParts(item.hash)
  await page.evaluate(({ path, query, hash }) => {
    try {
      document.querySelectorAll('#topnavLoginModal').forEach((el) => el.classList.remove('open'))
    } catch (_) {}
    try {
      if (window.__xcRenderTabPath && path !== '/pages/bazi-index/index') {
        window.__xcRenderTabPath(path, query)
        return
      }
    } catch (_) {}
    try {
      window.location.hash = hash
    } catch (_) {}
  }, { path, query, hash: item.hash })
  await page.waitForTimeout(250)
  await waitForApp(page, item.expected[0])
}

async function collectSummary(page) {
  return await page.evaluate(() => {
    const isVisible = (el) => {
      if (!el) return false
      const rect = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity || '1') > 0
    }
    const text = document.body.innerText || ''
    const loginModalOpen = Array.from(document.querySelectorAll('#topnavLoginModal')).some(isVisible)
    return {
      href: location.href,
      title: document.title,
      mode: document.body.classList.contains('home-fixed-page') ? 'app' : (window.__xcHomeMode || 'page'),
      loginModalOpen,
      textSample: text.replace(/\s+/g, ' ').slice(0, 500),
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
      visibleButtons: Array.from(document.querySelectorAll('button, .btn, .nav-btn, .marketing-agent-link, .marketing-enter, .home-ai-send, .profile-picker, .tool-picker'))
        .filter(isVisible)
        .map((el) => (el.textContent || el.getAttribute('data-href') || '').trim())
        .filter(Boolean)
        .slice(0, 80),
    }
  })
}

async function hasVisibleText(page, expected) {
  return await page.evaluate((expectedText) => {
    const isVisible = (el) => {
      if (!el) return false
      const rect = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden' && Number(style.opacity || '1') > 0
    }
    return Array.from(document.querySelectorAll('body *'))
      .some((el) => isVisible(el) && (el.innerText || el.textContent || '').includes(expectedText))
  }, expected)
}

async function captureStory(browser, item, preset) {
  const page = await browser.newPage({
    viewport: preset.viewport,
    deviceScaleFactor: preset.deviceScaleFactor,
    isMobile: preset.isMobile,
  })
  const consoleErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (error) => consoleErrors.push(error.message))

  await page.goto(routeUrl(item.hash), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
  await waitForApp(page, item.login ? '' : item.expected[0])
  if (item.login) {
    await ensureLogin(page)
    await navigateStory(page, item)
  }
  if (item.beforeCapture) await item.beforeCapture(page)

  const summary = await collectSummary(page)
  assertCondition(!summary.horizontalOverflow, `${item.title}/${preset.label} 出现水平溢出`)
  if (item.id === '03-agent-workbench' || item.id === '04-points' || item.id === '06-profile-delete') {
    assertCondition(!summary.loginModalOpen, `${item.title}/${preset.label} 不应被登录弹窗遮挡`)
  }
  for (const expected of item.expected) {
    assertCondition(await hasVisibleText(page, expected), `${item.title}/${preset.label} 缺少可见关键文案: ${expected}`)
  }
  const blockingErrors = consoleErrors.filter((message) => !/favicon|ResizeObserver loop|Failed to load resource: the server responded with a status of 404.*avatar_|Failed to load resource: the server responded with a status of 401 \(UNAUTHORIZED\)|Failed to load resource: the server responded with a status of 429 \(TOO MANY REQUESTS\)|Failed to load resource: the server responded with a status of 400 \(BAD REQUEST\)/i.test(message))
  assertCondition(blockingErrors.length === 0, `${item.title}/${preset.label} 控制台错误: ${blockingErrors.slice(0, 3).join(' | ')}`)

  const filename = `${item.id}-${preset.id}-${safeName(item.title)}.png`
  const path = join(outDir, filename)
  await page.screenshot({ path, fullPage: false })
  await page.close()
  return {
    id: item.id,
    title: item.title,
    preset: preset.id,
    label: preset.label,
    path,
    role: item.role,
    href: summary.href,
    buttons: summary.visibleButtons,
  }
}

async function main() {
  ensureDir()
  const browserLaunchOptions = {
    headless: true,
    ...(systemBrowserExecutable ? { executablePath: systemBrowserExecutable } : {}),
    ...(!systemBrowserExecutable && systemBrowserChannel ? { channel: systemBrowserChannel } : {}),
  }
  const browser = await chromium.launch(browserLaunchOptions)
  const captures = []
  const failures = []

  try {
    for (const item of story) {
      for (const presetId of item.modes) {
        const preset = presets.find((entry) => entry.id === presetId)
        try {
          captures.push(await captureStory(browser, item, preset))
        } catch (error) {
          failures.push({ id: item.id, title: item.title, preset: presetId, error: error.message })
        }
      }
    }
  } finally {
    await browser.close()
  }

  const report = {
    generatedAt: new Date().toISOString(),
    baseUrl,
    outDir,
    qaUser,
    browser: {
      channel: browserLaunchOptions.channel || '',
      executablePath: browserLaunchOptions.executablePath || '',
    },
    passed: failures.length === 0,
    captures,
    failures,
    storyboard: story.map((item) => ({ id: item.id, title: item.title, role: item.role, modes: item.modes })),
  }

  writeFileSync(join(outDir, 'summary.json'), `${JSON.stringify(report, null, 2)}\n`)
  const md = [
    '# 商店截图素材包',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> baseUrl：${baseUrl}`,
    `> 结论：${report.passed ? '通过' : '失败'}`,
    '',
    '| 截图 | 设备 | 用途 | 文件 |',
    '| --- | --- | --- | --- |',
    ...captures.map((entry) => `| ${entry.title} | ${entry.label} | ${entry.role} | \`${entry.path}\` |`),
    '',
    failures.length ? '## 失败项' : '',
    ...failures.map((entry) => `- ${entry.title}/${entry.preset}: ${entry.error}`),
    '',
  ].join('\n')
  writeFileSync(join(outDir, 'README.md'), md)

  console.log(JSON.stringify({
    passed: report.passed,
    outDir,
    captures: captures.length,
    failures,
  }, null, 2))

  if (!report.passed) process.exit(1)
}

main().catch((error) => {
  console.error(error)
  process.exit(1)
})
