#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { readFileSync } from 'node:fs'
import { join } from 'node:path'

const root = process.cwd()
const waitMs = Number(process.env.DEV_SMOKE_WAIT_MS || 30000)
const intervalMs = Number(process.env.DEV_SMOKE_INTERVAL_MS || 1000)
const requestTimeoutMs = Number(process.env.DEV_SMOKE_REQUEST_TIMEOUT_MS || 3000)

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
  const timer = setTimeout(() => controller.abort(), requestTimeoutMs)
  try {
    return await fetch(url, { signal: controller.signal })
  } finally {
    clearTimeout(timer)
  }
}

async function waitFor(name, fn) {
  const started = Date.now()
  let lastError = ''
  while (Date.now() - started <= waitMs) {
    try {
      const result = await fn()
      if (result.ok) return { name, waitedMs: Date.now() - started, ...result }
      lastError = result.error || ''
    } catch (error) {
      lastError = error.message
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs))
  }
  return { name, ok: false, waitedMs: Date.now() - started, error: lastError || '等待超时' }
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

if (manifestPort !== vitePort) {
  warnings.push(`manifest devServer.port 是 ${manifestPort}，但 vite.config.js server.port 是 ${vitePort}`)
}

const checks = []
checks.push(await waitFor(`前端端口 ${frontendPort}`, async () => {
  const listeners = portListeners(frontendPort)
  if (listeners.length === 0) return { ok: false, error: '端口未监听' }
  const response = await fetchWithTimeout(frontendUrl)
  const text = await response.text()
  if (!response.ok) return { ok: false, error: `HTTP ${response.status}` }
  if (!text.includes('<div id="app"') && !text.includes('时安解忧屋')) {
    return { ok: false, error: '未返回预期 H5 入口内容' }
  }
  return { ok: true, status: response.status, process: listeners[0] || '' }
}))

checks.push(await waitFor(`后端健康 ${backendPort}`, async () => {
  const listeners = portListeners(backendPort)
  if (listeners.length === 0) return { ok: false, error: '端口未监听' }
  const response = await fetchWithTimeout(`${backendUrl}/api/health`)
  const data = await response.json().catch(() => null)
  if (!response.ok) return { ok: false, error: `HTTP ${response.status}` }
  if (data?.success !== true || data?.status !== 'running') {
    return { ok: false, error: '健康接口响应异常' }
  }
  return { ok: true, status: response.status, process: listeners[0] || '' }
}))

checks.push(await waitFor('前端代理 /api/health', async () => {
  const response = await fetchWithTimeout(`${frontendUrl}/api/health`)
  const data = await response.json().catch(() => null)
  if (!response.ok) return { ok: false, error: `HTTP ${response.status}` }
  if (data?.success !== true || data?.status !== 'running') {
    return { ok: false, error: '代理健康接口响应异常' }
  }
  return { ok: true, status: response.status }
}))

const passed = checks.every((check) => check.ok)
console.log(JSON.stringify({
  passed,
  frontendUrl,
  backendUrl,
  proxyTarget,
  warnings,
  checks,
}, null, 2))

if (!passed) {
  console.error('[dev:smoke] 未通过。请确认已分别运行 npm run dev:backend 和 npm run dev:h5。')
  process.exit(1)
}
