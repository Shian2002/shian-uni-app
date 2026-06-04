#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const root = process.cwd()
const timeoutMs = Number(process.env.LOCAL_QA_TIMEOUT_MS || 5000)

function readJson(path) {
  return JSON.parse(readFileSync(join(root, path), 'utf8'))
}

function readText(path) {
  return readFileSync(join(root, path), 'utf8')
}

function matchNumber(text, pattern, fallback) {
  const match = text.match(pattern)
  return match ? Number(match[1]) : fallback
}

function matchString(text, pattern, fallback) {
  const match = text.match(pattern)
  return match ? match[1] : fallback
}

function portListeners(port) {
  try {
    const output = execFileSync('lsof', ['-nP', `-iTCP:${port}`, '-sTCP:LISTEN'], {
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
    }).trim()
    return output.split('\n').slice(1).filter(Boolean)
  } catch {
    return []
  }
}

async function fetchWithTimeout(url) {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    return await fetch(url, { signal: controller.signal })
  } finally {
    clearTimeout(timer)
  }
}

function issueList(title, items) {
  if (items.length === 0) return
  console.error(title)
  for (const item of items) console.error(`- ${item}`)
}

const viteConfig = readText('vite.config.js')
const manifest = readJson('src/manifest.json')
const vitePort = matchNumber(viteConfig, /\bport\s*:\s*(\d+)/, 3001)
const manifestPort = Number(manifest.h5?.devServer?.port || 5173)
const proxyTarget = matchString(viteConfig, /target\s*:\s*['"]([^'"]+)['"]/, 'http://localhost:5199')
const backendPort = matchNumber(proxyTarget, /:(\d+)(?:\/)?$/, 5199)

const frontendPort = Number(process.env.LOCAL_FRONTEND_PORT || vitePort)
const frontendUrl = process.env.LOCAL_FRONTEND_URL || `http://localhost:${frontendPort}`
const backendUrl = process.env.LOCAL_BACKEND_URL || `http://localhost:${backendPort}`

const warnings = []
const failures = []
const results = []

if (manifestPort !== vitePort) {
  warnings.push(`manifest devServer.port 是 ${manifestPort}，但 vite.config.js server.port 是 ${vitePort}；本地验活按 Vite 端口 ${vitePort} 执行`)
}
if (proxyTarget !== `http://localhost:${backendPort}`) {
  warnings.push(`Vite /api proxy target 不是标准 localhost 端口格式: ${proxyTarget}`)
}

const frontendListeners = portListeners(frontendPort)
const backendListeners = portListeners(backendPort)
results.push({
  name: '前端端口监听',
  port: frontendPort,
  listening: frontendListeners.length > 0,
  process: frontendListeners[0] || '',
})
results.push({
  name: '后端端口监听',
  port: backendPort,
  listening: backendListeners.length > 0,
  process: backendListeners[0] || '',
})

if (frontendListeners.length === 0) {
  failures.push(`前端端口 ${frontendPort} 未监听；通常先运行 npm run dev:h5`)
}
if (backendListeners.length === 0) {
  failures.push(`后端端口 ${backendPort} 未监听；通常在 backend 目录启动 Flask 服务`)
}

if (frontendListeners.length > 0) {
  try {
    const response = await fetchWithTimeout(frontendUrl)
    const text = await response.text()
    if (!response.ok) failures.push(`前端 ${frontendUrl} HTTP 状态异常: ${response.status}`)
    if (!text.includes('<div id="app"') && !text.includes('时安解忧屋')) {
      failures.push(`前端 ${frontendUrl} 未返回预期 H5 入口内容`)
    }
    results.push({ name: '前端 HTTP', url: frontendUrl, status: response.status })
  } catch (error) {
    failures.push(`前端 ${frontendUrl} 请求失败: ${error.message}`)
  }
}

if (backendListeners.length > 0) {
  try {
    const response = await fetchWithTimeout(`${backendUrl}/api/health`)
    const data = await response.json().catch(() => null)
    if (!response.ok) failures.push(`后端 /api/health HTTP 状态异常: ${response.status}`)
    if (data?.success !== true || data?.status !== 'running') {
      failures.push('后端 /api/health 响应内容异常')
    }
    results.push({ name: '后端健康', url: `${backendUrl}/api/health`, status: response.status, data })
  } catch (error) {
    failures.push(`后端 ${backendUrl}/api/health 请求失败: ${error.message}`)
  }
}

if (frontendListeners.length > 0) {
  try {
    const response = await fetchWithTimeout(`${frontendUrl}/api/health`)
    const data = await response.json().catch(() => null)
    if (!response.ok) failures.push(`前端代理 /api/health HTTP 状态异常: ${response.status}`)
    if (data?.success !== true || data?.status !== 'running') {
      failures.push('前端代理 /api/health 响应内容异常')
    }
    results.push({ name: '前端代理健康', url: `${frontendUrl}/api/health`, status: response.status, data })
  } catch (error) {
    failures.push(`前端代理 ${frontendUrl}/api/health 请求失败: ${error.message}`)
  }
}

console.log(JSON.stringify({
  passed: failures.length === 0,
  frontendUrl,
  backendUrl,
  proxyTarget,
  warnings,
  results,
}, null, 2))

issueList('[qa:local] 提醒:', warnings)
issueList('[qa:local] 失败:', failures)

if (failures.length > 0) process.exit(1)
