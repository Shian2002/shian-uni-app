#!/usr/bin/env node

import { _electron as electron } from 'playwright'
import { mkdirSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { join, resolve } from 'node:path'

const root = process.cwd()
const desktopDir = join(root, 'desktop')
const requireDesktop = createRequire(join(desktopDir, 'package.json'))
const electronExecutable = requireDesktop('electron')
const smokeExecutable = process.env.DESKTOP_SMOKE_EXECUTABLE || electronExecutable
const smokeArgs = process.env.DESKTOP_SMOKE_EXECUTABLE ? [] : ['.']
const artifactDir = process.env.QA_ARTIFACT_DIR || join(root, 'artifacts', 'desktop-smoke', new Date().toISOString().replace(/[:.]/g, '-'))
const timeoutMs = Number(process.env.QA_TIMEOUT_MS || 30000)

function assertCondition(condition, message) {
  if (!condition) throw new Error(message)
}

function ensureArtifactDir() {
  mkdirSync(artifactDir, { recursive: true })
}

async function waitForText(page, text) {
  await page.waitForFunction((expected) => ((document.body && document.body.innerText) || '').includes(expected), text, { timeout: timeoutMs })
}

async function waitForAnyText(page, texts) {
  await page.waitForFunction(
    (expectedTexts) => {
      const bodyText = (document.body && document.body.innerText) || ''
      return expectedTexts.some((text) => bodyText.includes(text))
    },
    texts,
    { timeout: timeoutMs },
  )
}

async function summary(page) {
  return await page.evaluate(() => ({
    href: location.href,
    hash: location.hash,
    title: document.title,
    text: document.body.innerText || '',
    desktop: window.shianDesktop || null,
    horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 2,
    visibleButtons: Array.from(document.querySelectorAll('button, .nav-btn, .marketing-agent-link, .marketing-enter, .home-ai-send, .profile-picker, .tool-picker, .btn, .oauth-btn'))
      .filter((el) => {
        const rect = el.getBoundingClientRect()
        const style = getComputedStyle(el)
        return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
      })
      .map((el) => (el.textContent || '').trim())
      .slice(0, 80),
  }))
}

async function desktopLayoutMetrics(page) {
  return await page.evaluate(() => {
    const rectOf = (selector) => {
      const el = document.querySelector(selector)
      if (!el) return null
      const rect = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return {
        top: Math.round(rect.top),
        right: Math.round(rect.right),
        bottom: Math.round(rect.bottom),
        left: Math.round(rect.left),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        backgroundColor: style.backgroundColor,
        backgroundImage: style.backgroundImage,
      }
    }
    return {
      viewport: { width: window.innerWidth, height: window.innerHeight },
      htmlTheme: document.documentElement.getAttribute('data-theme') || '',
      bodyTheme: document.body.getAttribute('data-theme') || '',
      topnav: rectOf('.topnav'),
      homeAiMain: rectOf('.home-ai-main'),
      desktopShellClass: document.body.classList.contains('desktop-native-shell'),
      homeFixedClass: document.body.classList.contains('home-fixed-page'),
    }
  })
}

async function loginModalMetrics(page) {
  return await page.evaluate(() => {
    const rectOf = (selector) => {
      const el = document.querySelector(selector)
      if (!el) return null
      const rect = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return {
        top: Math.round(rect.top),
        right: Math.round(rect.right),
        bottom: Math.round(rect.bottom),
        left: Math.round(rect.left),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        backgroundColor: style.backgroundColor,
        backgroundImage: style.backgroundImage,
      }
    }
    if (typeof window._openLoginModal === 'function') window._openLoginModal()
    const modal = document.querySelector('#topnavLoginModal')
    const box = modal && modal.querySelector('.modal-box')
    const modalStyle = modal ? getComputedStyle(modal) : null
    const boxStyle = box ? getComputedStyle(box) : null
    const rect = box ? box.getBoundingClientRect() : null
    return {
      viewport: { width: window.innerWidth, height: window.innerHeight },
      htmlTheme: document.documentElement.getAttribute('data-theme') || '',
      bodyTheme: document.body.getAttribute('data-theme') || '',
      hasModal: Boolean(modal),
      modalOpen: Boolean(modal && modal.classList.contains('open')),
      display: modalStyle ? modalStyle.display : '',
      alignItems: modalStyle ? modalStyle.alignItems : '',
      justifyContent: modalStyle ? modalStyle.justifyContent : '',
      overlayBackground: modalStyle ? modalStyle.backgroundColor : '',
      box: rect ? {
        top: Math.round(rect.top),
        right: Math.round(rect.right),
        bottom: Math.round(rect.bottom),
        left: Math.round(rect.left),
        width: Math.round(rect.width),
        height: Math.round(rect.height),
        backgroundColor: boxStyle.backgroundColor,
        backgroundImage: boxStyle.backgroundImage,
        color: boxStyle.color,
      } : null,
      topnav: rectOf('.topnav'),
      homeFixedClass: document.body.classList.contains('home-fixed-page'),
      desktopShellClass: document.body.classList.contains('desktop-native-shell'),
    }
  })
}

function assertDesktopNativeLayout(metrics) {
  assertCondition(metrics.desktopShellClass, '桌面 App 未挂载 desktop-native-shell 原生壳样式')
  assertCondition(metrics.htmlTheme === 'light', `桌面 App html 主题不是浅色: ${metrics.htmlTheme}`)
  assertCondition(metrics.bodyTheme === 'light', `桌面 App body 主题不是浅色: ${metrics.bodyTheme}`)
  assertCondition(metrics.topnav, '桌面 App 缺少顶部导航栏')
  assertCondition(metrics.topnav.height <= 42, `桌面顶部栏过高: ${metrics.topnav.height}px`)
  assertCondition(
    !/rgba?\(255,\s*255,\s*255/.test(metrics.topnav.backgroundColor) &&
      !String(metrics.topnav.backgroundImage || '').includes('255, 255, 255'),
    `桌面顶部栏仍接近纯白: ${metrics.topnav.backgroundColor} ${metrics.topnav.backgroundImage}`
  )
  assertCondition(
    /rgba?\(24[0-9],\s*23[0-9],\s*21[0-9]/.test(metrics.topnav.backgroundColor) ||
      String(metrics.topnav.backgroundImage || '').includes('241, 231, 215'),
    `桌面顶部栏不是主题暖米色: ${metrics.topnav.backgroundColor} ${metrics.topnav.backgroundImage}`
  )
}

function assertLoginModalDocked(metrics) {
  assertDesktopNativeLayout(metrics)
  assertCondition(metrics.hasModal && metrics.modalOpen, '桌面登录弹窗未打开')
  assertCondition(metrics.display === 'flex', `桌面登录弹窗 display 异常: ${metrics.display}`)
  assertCondition(metrics.alignItems === 'flex-end', `桌面登录弹窗未底部对齐: ${metrics.alignItems}`)
  assertCondition(metrics.justifyContent === 'center', `桌面登录弹窗水平对齐异常: ${metrics.justifyContent}`)
  assertCondition(metrics.box, '桌面登录弹窗缺少 modal-box')
  const bottomGap = metrics.viewport.height - metrics.box.bottom
  assertCondition(bottomGap >= 0 && bottomGap <= 28, `桌面登录弹窗未贴近底部: bottom gap ${bottomGap}px`)
  assertCondition(
    String(metrics.box.backgroundImage || '').includes('255, 253, 248') ||
      String(metrics.box.backgroundImage || '').includes('247, 242, 234'),
    `桌面登录弹窗不是浅色主题: ${metrics.box.backgroundColor} ${metrics.box.backgroundImage}`
  )
}

function assertAgentInputDocked(metrics) {
  assertDesktopNativeLayout(metrics)
  assertCondition(metrics.homeFixedClass, '时安agent 桌面工作台未进入固定首页布局')
  assertCondition(metrics.homeAiMain, '时安agent 缺少底部对话输入框')
  const bottomGap = metrics.viewport.height - metrics.homeAiMain.bottom
  assertCondition(bottomGap >= 0 && bottomGap <= 24, `时安agent 对话框未贴近底部: bottom gap ${bottomGap}px`)
  assertCondition(
    metrics.homeAiMain.top >= Math.round(metrics.viewport.height * 0.65),
    `时安agent 对话框跑到中间: top ${metrics.homeAiMain.top}px / viewport ${metrics.viewport.height}px`
  )
}

async function screenshot(page, name, fullPage = true) {
  ensureArtifactDir()
  await page.mouse.move(20, 220).catch(() => {})
  await page.evaluate(() => {
    document.querySelectorAll('.nav-btn-drop-menu.open, .nav-btn-more.open, .nav-dropdown.open, .nav-avatar-dropdown.open')
      .forEach((el) => {
        el.classList.remove('open')
        el.classList.remove('show')
      })
  }).catch(() => {})
  const path = join(artifactDir, name)
  await page.screenshot({ path, fullPage })
  return path
}

async function clickVisible(page, selector, includesText) {
  await page.evaluate(({ selector, includesText }) => {
    const visible = (el) => {
      const rect = el.getBoundingClientRect()
      const style = getComputedStyle(el)
      return rect.width > 0 && rect.height > 0 && style.display !== 'none' && style.visibility !== 'hidden'
    }
    const target = Array.from(document.querySelectorAll(selector))
      .find((el) => visible(el) && (!includesText || (el.textContent || '').replace(/\s+/g, '').includes(includesText)))
    if (!target) throw new Error(`找不到可见元素: ${selector} ${includesText || ''}`)
    target.click()
  }, { selector, includesText })
}

async function main() {
  ensureArtifactDir()
  const app = await electron.launch({
    executablePath: smokeExecutable,
    args: smokeArgs,
    cwd: desktopDir,
    env: {
      ...process.env,
      ELECTRON_DISABLE_SECURITY_WARNINGS: '1',
      SHIAN_DESKTOP_USER_DATA_DIR: process.env.SHIAN_DESKTOP_USER_DATA_DIR || join(artifactDir, 'user-data'),
    },
  })

  const page = await app.firstWindow({ timeout: timeoutMs })
  const consoleErrors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') consoleErrors.push(msg.text())
  })
  page.on('pageerror', (error) => consoleErrors.push(error.message))

  try {
    await page.setViewportSize({ width: 1220, height: 820 })
    await waitForAnyText(page, ['The Oriental Insight Agent', '选择命盘'])
    const initial = await summary(page)
    let marketingShot = null
    let loginShot = null
    let marketing = null
    let login = null
    let marketingLayout = null
    let loginLayout = null

    if (initial.text.includes('The Oriental Insight Agent')) {
      marketingShot = await screenshot(page, 'desktop-marketing-home.png')
      marketing = initial
      assertCondition(marketing.text.includes('时安agent'), '桌面首页缺少时安agent入口')
      assertCondition(marketing.text.includes('开始解读'), '桌面首页缺少开始解读入口')
      assertCondition(marketing.desktop && marketing.desktop.platform, 'Electron preload 未暴露桌面环境信息')
      assertCondition(!marketing.horizontalOverflow, '桌面首页出现水平溢出')
      marketingLayout = await desktopLayoutMetrics(page)
      assertDesktopNativeLayout(marketingLayout)

      await clickVisible(page, '.marketing-agent-link', '时安agent')
      await waitForText(page, '密码登录')
      loginLayout = await loginModalMetrics(page)
      assertLoginModalDocked(loginLayout)
      loginShot = await screenshot(page, 'desktop-login-modal.png')
      login = await summary(page)
      assertCondition(login.text.includes('验证码登录'), '桌面登录弹窗缺少验证码登录')
      assertCondition(login.text.includes('Gitee 验证登录'), '桌面登录弹窗缺少 Gitee 验证登录')

      await page.evaluate(() => {
        try {
          document.querySelectorAll('#topnavLoginModal.open').forEach((el) => el.classList.remove('open'))
          localStorage.setItem('xc_token', 'desktop-smoke')
          localStorage.setItem('xc_user', JSON.stringify({ username: 'desktop-smoke' }))
          if (window.uni && typeof uni.setStorageSync === 'function') {
            uni.setStorageSync('xc_token', 'desktop-smoke')
            uni.setStorageSync('xc_user', 'desktop-smoke')
          }
          window.dispatchEvent(new CustomEvent('xc-auth-changed', { detail: { loggedIn: true, user: { username: 'desktop-smoke' } } }))
          if (window.__topNavGo) window.__topNavGo('#/?app=1')
          else location.hash = '#/?app=1'
        } catch (error) {
          throw new Error(error.message)
        }
      })
    } else {
      assertCondition(initial.desktop && initial.desktop.platform, 'Electron preload 未暴露桌面环境信息')
      assertCondition(!initial.horizontalOverflow, '桌面应用态出现水平溢出')
    }

    await waitForText(page, '选择命盘')
    await waitForText(page, '选择术数')
    const agentShot = await screenshot(page, 'desktop-agent-app.png')
    const agent = await summary(page)
    assertCondition(agent.text.includes('选择命盘'), '桌面 Agent 缺少选择命盘')
    assertCondition(agent.text.includes('选择术数'), '桌面 Agent 缺少选择术数')
    assertCondition(!agent.horizontalOverflow, '桌面 Agent 应用态出现水平溢出')
    const agentLayout = await desktopLayoutMetrics(page)
    assertAgentInputDocked(agentLayout)

    if (!loginShot) {
      loginLayout = await loginModalMetrics(page)
      assertLoginModalDocked(loginLayout)
      await waitForText(page, '密码登录')
      loginShot = await screenshot(page, 'desktop-login-modal.png')
      login = await summary(page)
    }

    const blockingErrors = consoleErrors.filter((item) => !(
      /favicon|Failed to load resource.*avatar_/i.test(item) ||
      /Failed to load resource: the server responded with a status of 401 \(Unauthorized\)/i.test(item)
    ))
    assertCondition(blockingErrors.length === 0, `桌面端控制台错误: ${blockingErrors.slice(0, 3).join(' | ')}`)

    const report = {
      passed: true,
      generatedAt: new Date().toISOString(),
      artifactDir: resolve(artifactDir),
      screenshots: {
        marketingHome: marketingShot,
        loginModal: loginShot,
        agentApp: agentShot,
      },
      desktop: (marketing || agent).desktop,
      layout: {
        marketing: marketingLayout,
        login: loginLayout,
        agent: agentLayout,
      },
      hrefs: {
        marketing: marketing ? marketing.href : '',
        login: login ? login.href : '',
        agent: agent.href,
      },
    }
    writeFileSync(join(artifactDir, 'report.json'), JSON.stringify(report, null, 2))
    console.log(JSON.stringify(report, null, 2))
  } catch (error) {
    await screenshot(page, 'desktop-smoke-failure.png').catch(() => {})
    writeFileSync(join(artifactDir, 'failure.json'), JSON.stringify({
      passed: false,
      message: error.message,
      consoleErrors,
      artifactDir: resolve(artifactDir),
    }, null, 2))
    throw error
  } finally {
    await app.close()
  }
}

main().catch((error) => {
  console.error(error.message)
  process.exit(1)
})
