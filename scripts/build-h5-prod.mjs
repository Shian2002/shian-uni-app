#!/usr/bin/env node

import { copyFileSync, existsSync, mkdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'

const pagesJsonPath = new URL('../src/pages.json', import.meta.url)
const publicDir = new URL('../public/', import.meta.url)
const h5DistDir = new URL('../dist/build/h5/', import.meta.url)
const seoPublicFiles = ['robots.txt', 'sitemap.xml', 'manifest.json', 'indexnow-key.txt']
const lockParentDir = new URL('../node_modules/.cache', import.meta.url)
const lockDir = new URL('../node_modules/.cache/build-h5-prod.lock', import.meta.url)
let lockAcquired = false
let original = ''

function wait(ms) {
  Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms)
}

function acquireLock() {
  mkdirSync(lockParentDir, { recursive: true })
  const startedAt = Date.now()
  while (!lockAcquired) {
    try {
      mkdirSync(lockDir, { recursive: false })
      lockAcquired = true
    } catch (error) {
      if (Date.now() - startedAt > 120000) {
        throw new Error(`等待 build:h5 锁超时: ${error.message}`)
      }
      wait(250)
    }
  }
}

function releaseLock() {
  if (!lockAcquired) return
  rmSync(lockDir, { recursive: true, force: true })
  lockAcquired = false
}

function hideCommunityForProduction(original) {
  const config = JSON.parse(original)
  config.pages = (config.pages || []).filter((page) => page.path !== 'pages/community/index')
  if (config.tabBar && Array.isArray(config.tabBar.list)) {
    config.tabBar.list = config.tabBar.list.filter((item) => item.pagePath !== 'pages/community/index')
  }
  writeFileSync(pagesJsonPath, JSON.stringify(config, null, 2) + '\n')
}

function copySeoPublicFiles() {
  if (!existsSync(h5DistDir)) return
  for (const fileName of seoPublicFiles) {
    const source = new URL(fileName, publicDir)
    if (!existsSync(source)) continue
    copyFileSync(source, new URL(fileName, h5DistDir))
    console.log(`[build-h5-prod] 已复制公开 SEO 文件: ${fileName}`)
  }
}

try {
  acquireLock()
  original = readFileSync(pagesJsonPath, 'utf8')
  if (process.env.KEEP_COMMUNITY_IN_PROD === '1') {
    console.log('[build-h5-prod] KEEP_COMMUNITY_IN_PROD=1，保留社区页面')
  } else {
    hideCommunityForProduction(original)
    console.log('[build-h5-prod] 生产构建已临时隐藏社区页面和 tab')
  }

  const result = spawnSync('uni', ['build'], {
    stdio: 'inherit',
    env: process.env,
    shell: process.platform === 'win32',
  })
  if (result.error) throw result.error
  if ((result.status || 0) === 0) {
    copySeoPublicFiles()
  }
  process.exitCode = result.status || 0
} finally {
  try {
    if (lockAcquired && typeof original === 'string') {
      writeFileSync(pagesJsonPath, original)
    }
  } finally {
    releaseLock()
  }
}
