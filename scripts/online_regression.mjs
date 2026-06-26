#!/usr/bin/env node

import { mkdirSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'
import { chromium } from 'playwright'

const baseUrl = process.env.REGRESSION_BASE_URL || 'https://shianjieyouwu.com'
const timeoutMs = Number(process.env.REGRESSION_TIMEOUT_MS || 15000)
const artifactDir = process.env.REGRESSION_ARTIFACT_DIR || join('artifacts', 'qa', new Date().toISOString().replace(/[:.]/g, '-'))

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

function ensureArtifactDir() {
  mkdirSync(artifactDir, { recursive: true })
}

function safeName(name) {
  return name.replace(/[^a-zA-Z0-9\u4e00-\u9fa5_-]+/g, '-')
}

function writeArtifact(name, data) {
  ensureArtifactDir()
  writeFileSync(join(artifactDir, name), typeof data === 'string' ? data : JSON.stringify(data, null, 2))
}

async function captureFailure(page, name, error) {
  ensureArtifactDir()
  const base = safeName(name)
  await page.screenshot({ path: join(artifactDir, `${base}.png`), fullPage: true }).catch(() => {})
  const html = await page.content().catch(() => '')
  if (html) writeFileSync(join(artifactDir, `${base}.html`), html)
  writeArtifact(`${base}.error.json`, {
    name,
    message: error.message,
    url: page.url(),
  })
}

async function fetchJson(path, options = {}) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(`${baseUrl}${path}`, {
      ...options,
      signal: controller.signal,
    })
    const data = await response.json().catch(() => null)
    return { response, data }
  } finally {
    clearTimeout(timer)
  }
}

async function checkStaticAssets() {
  const response = await fetch(`${baseUrl}/`, { signal: AbortSignal.timeout(timeoutMs) })
  assertCondition(response.ok, `首页 HTML HTTP 状态异常: ${response.status}`)
  const html = await response.text()
  const assetUrls = new Set()
  for (const match of html.matchAll(/\b(?:src|href)=["']([^"']+)["']/g)) {
    const raw = match[1]
    if (!raw || raw.startsWith('data:') || raw.startsWith('http')) continue
    if (!raw.startsWith('/assets/') && !raw.startsWith('/static/')) continue
    assetUrls.add(new URL(raw, baseUrl).toString())
  }
  assertCondition(assetUrls.size > 0, '首页没有发现静态资源引用')

  const failures = []
  for (const url of assetUrls) {
    const assetResponse = await fetch(url, { signal: AbortSignal.timeout(timeoutMs) }).catch((error) => ({ ok: false, status: error.message }))
    if (!assetResponse.ok) failures.push({ url, status: assetResponse.status })
  }
  assertCondition(failures.length === 0, `首页静态资源异常: ${failures.slice(0, 5).map((item) => `${item.status} ${item.url}`).join(' | ')}`)
  return { name: '首页静态资源', assetCount: assetUrls.size }
}

async function checkApiHealth() {
  const { response, data } = await fetchJson('/api/health')
  assertCondition(response.ok, `健康检查 HTTP 状态异常: ${response.status}`)
  assertCondition(data?.success === true, '健康检查 success 不是 true')
  assertCondition(data?.status === 'running', `健康检查 status 异常: ${data?.status}`)
  return { name: '后端健康', status: data.status, success: data.success }
}

async function checkDeepHealth() {
  const { response, data } = await fetchJson('/api/health/deep')
  assertCondition(response.ok, `深度健康检查 HTTP 状态异常: ${response.status}`)
  assertCondition(data?.success === true, `深度健康检查失败: ${JSON.stringify(data)}`)
  assertCondition(data?.status === 'running', `深度健康检查 status 异常: ${data?.status}`)
  assertCondition(data?.database?.available === true, '深度健康检查数据库不可用')
  assertCondition(data?.upload?.available === true, '深度健康检查上传目录不可用')
  return {
    name: '深度健康',
    status: data.status,
    database: data.database?.available,
    upload: data.upload?.available,
    wzApi: data.wz_api?.available,
  }
}

async function checkReadOnlyApis() {
  const results = []

  const packagesCheck = await fetchJson('/api/recharge/packages')
  assertCondition(packagesCheck.response.ok, `充值套餐 HTTP 状态异常: ${packagesCheck.response.status}`)
  const packages = packagesCheck.data?.packages || []
  assertCondition(Array.isArray(packages) && packages.length >= 5, '充值套餐数量异常')
  assertCondition(packages.some((item) => item.id === 'starter' && item.points === 60), '缺少体验包 starter')
  assertCondition(packages.some((item) => item.id === 'ai-starter' && item.ai_single_credits === 10), '缺少 AI 入门包')
  results.push({ name: '充值套餐接口', packageCount: packages.length })

  const meCheck = await fetchJson('/api/me')
  assertCondition(meCheck.response.ok, `未登录用户接口 HTTP 状态异常: ${meCheck.response.status}`)
  assertCondition(meCheck.data?.guest === true, '未登录 /api/me 没有返回 guest=true')
  results.push({ name: '未登录用户态接口', guest: meCheck.data.guest })

  const membershipCheck = await fetchJson('/api/membership')
  assertCondition(membershipCheck.response.status === 401, `未登录会员接口应为 401，实际: ${membershipCheck.response.status}`)
  assertCondition(membershipCheck.data?.error === '请先登录', '未登录会员接口错误文案异常')
  results.push({ name: '会员鉴权接口', status: membershipCheck.response.status })

  const tarotCheck = await fetchJson('/api/tarot/spreads')
  assertCondition(tarotCheck.response.ok, `塔罗牌阵 HTTP 状态异常: ${tarotCheck.response.status}`)
  assertCondition(tarotCheck.data?.code === 0, '塔罗牌阵 code 异常')
  assertCondition(Array.isArray(tarotCheck.data?.data) && tarotCheck.data.data.length >= 3, '塔罗牌阵数量异常')
  results.push({ name: '塔罗牌阵接口', spreadCount: tarotCheck.data.data.length })

  const ziweiCheck = await fetchJson('/api/ziwei/info')
  assertCondition(ziweiCheck.response.ok, `紫微信息 HTTP 状态异常: ${ziweiCheck.response.status}`)
  assertCondition(ziweiCheck.data?.code === 0, '紫微信息 code 异常')
  const palaces = ziweiCheck.data?.data?.twelve_palaces || []
  assertCondition(Array.isArray(palaces) && palaces.length >= 12, '紫微十二宫数据异常')
  assertCondition(['命宫', '财帛宫', '夫妻宫', '疾厄宫'].every((name) => palaces.includes(name)), '紫微关键宫位缺失')
  results.push({ name: '紫微信息接口', palaceCount: ziweiCheck.data.data.twelve_palaces.length })

  return results
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

  try {
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
  } catch (error) {
    await captureFailure(page, item.name, error)
    await page.close()
    throw error
  }
}

async function checkLoginModal(browser) {
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } })
  const errors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') errors.push(msg.text())
  })
  page.on('pageerror', (error) => errors.push(error.message))

  try {
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
    const modal = await page.evaluate(() => {
      const modalRoot = document.querySelector('#topnavLoginModal.open,.login-modal.open,[id*=login][class*=open]')
      const visibleText = (modalRoot?.innerText || modalRoot?.textContent || '').trim()
      return {
        visible: Boolean(modalRoot),
        userInput: Boolean(modalRoot?.querySelector('#tnLoginUser')),
        passInput: Boolean(modalRoot?.querySelector('#tnLoginPass')),
        modeTabs: Array.from(modalRoot?.querySelectorAll('.login-tab') || []).map((el) => (el.textContent || '').trim()),
        forbiddenText: ['手机号', '验证码登录', '忘记密码', 'Gitee 验证登录'].filter((text) => visibleText.includes(text)),
        visibleText,
      }
    })
    assertCondition(modal.visible, '登录弹窗未打开')
    assertCondition(modal.userInput, '登录账号输入框不存在')
    assertCondition(modal.passInput, '登录密码输入框不存在')
    assertCondition(JSON.stringify(modal.modeTabs) === JSON.stringify(['账号', '邮箱']), `登录方式不是账号/邮箱: ${modal.modeTabs.join(',')}`)
    assertCondition(modal.visibleText.includes('用户名/邮箱'), '账号输入框文案缺少用户名/邮箱')
    assertCondition(modal.visibleText.includes('已有账号直接登录'), '登录提示未恢复旧版文案')
    assertCondition(modal.visibleText.includes('Gitee'), '第三方登录缺少 Gitee')
    assertCondition(modal.forbiddenText.length === 0, `登录弹窗仍存在不应显示的入口: ${modal.forbiddenText.join(',')}`)
    const measureLoginBox = () => {
      const box = Array.from(document.querySelectorAll('#topnavLoginModal.open .modal-box')).find((el) => {
        const r = el.getBoundingClientRect()
        return r.width > 0 && r.height > 0
      })
      if (!box) throw new Error('找不到可见登录弹窗')
      const r = box.getBoundingClientRect()
      return {
        left: Math.round(r.left),
        top: Math.round(r.top),
        width: Math.round(r.width),
        height: Math.round(r.height),
      }
    }
    const passwordBoxBefore = await page.evaluate(measureLoginBox)

    const codeModeState = await page.evaluate(() => {
      const modalRoot = document.querySelector('#topnavLoginModal.open') || document
      const tab = Array.from(modalRoot.querySelectorAll('.login-tab')).find((el) => (el.textContent || '').trim() === '邮箱')
      if (!tab) throw new Error('找不到邮箱登录切换')
      tab.click()
      const account = modalRoot.querySelector('#tnLoginUser')
      return {
        active: Boolean(tab.classList.contains('active')),
        accountPlaceholder: account?.getAttribute('placeholder') || '',
        hasCode: Boolean(modalRoot.querySelector('#tnLoginCode')),
        hasCodeButton: Boolean(modalRoot.querySelector('#tnLoginCodeBtn')),
        passwordDisplay: window.getComputedStyle(modalRoot.querySelector('#tnLoginPass-wrap')?.closest('.field')).display,
      }
    })
    assertCondition(codeModeState.active, '邮箱登录切换未激活')
    assertCondition(codeModeState.accountPlaceholder === '邮箱', `邮箱登录账号占位异常: ${codeModeState.accountPlaceholder}`)
    assertCondition(codeModeState.hasCode && codeModeState.hasCodeButton, '邮箱登录缺少验证码输入或获取按钮')
    assertCondition(codeModeState.passwordDisplay === 'none', '邮箱登录时密码输入未隐藏')
    const codeBox = await page.evaluate(measureLoginBox)

    await page.evaluate(() => {
      const modalRoot = document.querySelector('#topnavLoginModal.open') || document
      const tab = Array.from(modalRoot.querySelectorAll('.login-tab')).find((el) => (el.textContent || '').trim() === '账号')
      if (!tab) throw new Error('找不到账号登录切换')
      tab.click()
    })
    const passwordBoxAfter = await page.evaluate(measureLoginBox)
    const stableBox = JSON.stringify(passwordBoxBefore) === JSON.stringify(codeBox) && JSON.stringify(passwordBoxBefore) === JSON.stringify(passwordBoxAfter)
    assertCondition(stableBox, `登录方式切换导致弹窗尺寸变化: ${JSON.stringify({ passwordBoxBefore, codeBox, passwordBoxAfter })}`)

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

    const resetState = await page.evaluate(() => {
      const modalRoot = document.querySelector('#topnavLoginModal.open') || document
      return {
        hasForgot: Boolean(modalRoot.querySelector('.forgot-link')),
        hasResetPanel: Boolean(modalRoot.querySelector('.tn-panel-reset')),
      }
    })
    assertCondition(!resetState.hasForgot && !resetState.hasResetPanel, '登录弹窗仍显示忘记密码入口或重置面板')

    assertCondition(errors.length === 0, `登录弹窗控制台错误: ${errors.slice(0, 3).join(' | ')}`)
    await page.close()
    return { name: '登录/注册弹窗', ...modal, codeModeState, loginBox: { passwordBoxBefore, codeBox, passwordBoxAfter }, registerState, loginState, resetState }
  } catch (error) {
    await captureFailure(page, '登录注册弹窗', error)
    await page.close()
    throw error
  }
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
  try {
    await page.goto(routeUrl('/', `mobile-${Date.now()}`), { waitUntil: 'domcontentloaded', timeout: timeoutMs })
    await page.waitForLoadState('networkidle', { timeout: timeoutMs }).catch(() => {})
    await page.waitForTimeout(1200)
    const summary = await pageSummary(page)
    assertCondition(summary.text.includes('The Oriental Insight Agent'), '移动首页关键文案缺失')
    assertCondition(!summary.horizontalOverflow, '移动首页出现水平溢出')
    assertCondition(errors.length === 0, `移动首页控制台错误: ${errors.slice(0, 3).join(' | ')}`)
    await page.close()
    return { name: '移动首页', href: summary.href, imageCount: summary.imageCount }
  } catch (error) {
    await captureFailure(page, '移动首页', error)
    await page.close()
    throw error
  }
}

async function main() {
  const browser = await chromium.launch({ headless: true })
  try {
    const results = []
    results.push(await checkApiHealth())
    results.push(await checkDeepHealth())
    results.push(...await checkReadOnlyApis())
    results.push(await checkStaticAssets())
    for (let i = 0; i < pages.length; i += 1) {
      results.push(await checkRoute(browser, pages[i], i))
    }
    results.push(await checkLoginModal(browser))
    results.push(await checkMobileHome(browser))
    const report = { baseUrl, passed: true, artifactDir, results }
    writeArtifact('report.json', report)
    console.log(JSON.stringify(report, null, 2))
  } finally {
    await browser.close()
  }
}

main().catch((error) => {
  const report = { baseUrl, passed: false, artifactDir, error: error.message }
  writeArtifact('report.json', report)
  console.error(JSON.stringify(report, null, 2))
  process.exit(1)
})
