#!/usr/bin/env node

import { chromium } from 'playwright'

const baseUrl = process.env.REGRESSION_BASE_URL || 'http://119.29.128.18'
const timeoutMs = Number(process.env.REGRESSION_TIMEOUT_MS || 15000)

const pages = [
  { name: '首页', hash: '/', mustInclude: ['The Oriental Insight Agent', '开始解读'] },
  { name: '八字', hash: '/pages/bazi-index/index', mustInclude: ['八字排盘 · 看透', '免费'] },
  { name: '奇门', hash: '/pages/qimen/index', mustInclude: ['奇门遁甲 · 预判', '奇门排盘'] },
  { name: '六爻', hash: '/pages/liuyao/index', mustInclude: ['六爻纳甲', '免费排盘'] },
  { name: '梅花', hash: '/pages/meihua/index', mustInclude: ['梅花易数 · 万物皆可起卦', '梅花排盘'] },
  { name: '紫微', hash: '/pages/ziwei/index', mustInclude: ['紫微斗数 · 十二宫排盘', '免费排盘'] },
  { name: '塔罗', hash: '/pages/tarot/index', mustInclude: ['塔罗牌占卜', '选择牌阵'] },
  { name: '日历', hash: '/pages/calendar/index', mustInclude: ['专属日历', '今天'] },
  { name: '积分', hash: '/package-user/points/index', mustInclude: ['积分中心', '积分充值'] },
]

function routeUrl(hash, marker) {
  const path = hash === '/' ? '/?qa=' + marker : hash + '?qa=' + marker
  return `${baseUrl}/#${path}`
}

function assertCondition(condition, message) {
  if (!condition) throw new Error(message)
}

async function checkApiHealth() {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${baseUrl}/api/health`, { signal: controller.signal })
    assertCondition(response.ok, `健康检查 HTTP 状态异常: ${response.status}`)
    const data = await response.json()
    assertCondition(data.success === true, '健康检查 success 不是 true')
    assertCondition(data.status === 'running', `健康检查 status 异常: ${data.status}`)
    return { name: '后端健康', status: data.status, success: data.success }
  } finally {
    clearTimeout(timer)
  }
}

async function pageSummary(page) {
  return await page.evaluate(() => ({
    href: location.href,
    title: document.title,
    text: document.body.innerText || '',
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth,
    imageCount: document.images.length,
  }))
}

async function checkRoute(browser, item, index) {
  const page = await browser.newPage({
    viewport: { width: 1280, height: 800 },
    deviceScaleFactor: 1,
  })
  const errors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text())
  })
  page.on('pageerror', (error) => errors.push(error.message))

  const marker = `online-regression-${Date.now()}-${index}`
  await page.goto(routeUrl(item.hash, marker), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
  await page.waitForLoadState('networkidle', { timeout: timeoutMs }).catch(() => {})
  await page.waitForTimeout(1200)

  const summary = await pageSummary(page)
  for (const text of item.mustInclude) {
    assertCondition(summary.text.includes(text), `${item.name} 缺少关键文案: ${text}`)
  }
  assertCondition(!summary.horizontalOverflow, `${item.name} 出现水平溢出`)
  assertCondition(errors.length === 0, `${item.name} 控制台错误: ${errors.slice(0, 3).join(' | ')}`)
  await page.close()
  return { name: item.name, title: summary.title, href: summary.href, imageCount: summary.imageCount }
}

async function checkLoginModal(browser) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
  const errors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text())
  })
  page.on('pageerror', (error) => errors.push(error.message))

  await page.goto(routeUrl('/', `login-${Date.now()}`), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
  await page.waitForLoadState('networkidle', { timeout: timeoutMs }).catch(() => {})
  await page.waitForTimeout(1200)
  await page.evaluate(() => {
    const targets = Array.from(document.querySelectorAll('button, span, view, text, uni-button'))
    const login = targets.find((el) => (el.innerText || el.textContent || '').trim() === '登录')
    if (!login) throw new Error('找不到登录入口')
    login.click()
  })
  await page.waitForTimeout(800)
  const modal = await page.evaluate(() => ({
    visible: Boolean(document.querySelector('#topnavLoginModal.open,.login-modal.open,[id*=login][class*=open]')),
    userInput: Boolean(document.querySelector('#tnLoginUser')),
    passInput: Boolean(document.querySelector('#tnLoginPass')),
  }))
  assertCondition(modal.visible, '登录弹窗未打开')
  assertCondition(modal.userInput, '登录用户名输入框不存在')
  assertCondition(modal.passInput, '登录密码输入框不存在')

  const registerState = await page.evaluate(() => {
    const link = document.querySelector('.register-link')
    if (!link) throw new Error('找不到注册入口')
    link.click()
    const modalRoot = document.querySelector('#topnavLoginModal.open') || document
    const title = (modalRoot.querySelector('.modal-title')?.textContent || '').trim()
    const primary = (modalRoot.querySelector('.modal-btns .btn-accent')?.textContent || '').trim()
    const error = (modalRoot.querySelector('#tnLoginError')?.textContent || '').trim()
    return { title, primary, error }
  })
  assertCondition(registerState.title === '注册', `注册弹窗标题异常: ${registerState.title}`)
  assertCondition(registerState.primary === '注册', `注册主按钮异常: ${registerState.primary}`)
  assertCondition(registerState.error.includes('请填写用户名和密码完成注册'), '注册提示文案异常')

  const loginState = await page.evaluate(() => {
    const link = document.querySelector('.login-link')
    if (!link) throw new Error('找不到返回登录入口')
    link.click()
    const modalRoot = document.querySelector('#topnavLoginModal.open') || document
    const title = (modalRoot.querySelector('.modal-title')?.textContent || '').trim()
    const primary = (modalRoot.querySelector('.modal-btns .btn-accent')?.textContent || '').trim()
    const hint = (modalRoot.querySelector('.modal-hint')?.textContent || '').trim()
    return { title, primary, hint }
  })
  assertCondition(loginState.title === '登录', `返回登录标题异常: ${loginState.title}`)
  assertCondition(loginState.primary === '登录', `返回登录主按钮异常: ${loginState.primary}`)
  assertCondition(loginState.hint.includes('没有账号？立即注册'), '返回登录提示文案异常')

  assertCondition(errors.length === 0, `登录弹窗控制台错误: ${errors.slice(0, 3).join(' | ')}`)
  await page.close()
  return { name: '登录/注册弹窗', ...modal, registerState, loginState }
}

async function checkMobileHome(browser) {
  const page = await browser.newPage({
    viewport: { width: 375, height: 812 },
    deviceScaleFactor: 2,
    isMobile: true,
  })
  const errors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text())
  })
  await page.goto(routeUrl('/', `mobile-${Date.now()}`), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
  await page.waitForLoadState('networkidle', { timeout: timeoutMs }).catch(() => {})
  await page.waitForTimeout(1200)
  const summary = await pageSummary(page)
  assertCondition(summary.text.includes('The Oriental Insight Agent'), '移动首页关键文案缺失')
  assertCondition(!summary.horizontalOverflow, '移动首页出现水平溢出')
  assertCondition(errors.length === 0, `移动首页控制台错误: ${errors.slice(0, 3).join(' | ')}`)
  await page.close()
  return { name: '移动首页', href: summary.href, imageCount: summary.imageCount }
}

async function main() {
  const browser = await chromium.launch({ headless: true })
  try {
    const results = []
    results.push(await checkApiHealth())
    for (let i = 0; i < pages.length; i += 1) {
      results.push(await checkRoute(browser, pages[i], i))
    }
    results.push(await checkLoginModal(browser))
    results.push(await checkMobileHome(browser))
    console.log(JSON.stringify({ baseUrl, passed: true, results }, null, 2))
  } finally {
    await browser.close()
  }
}

main().catch((error) => {
  console.error(JSON.stringify({ baseUrl, passed: false, error: error.message }, null, 2))
  process.exit(1)
})
