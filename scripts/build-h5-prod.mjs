#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'node:fs'
import { spawnSync } from 'node:child_process'

const pagesJsonPath = new URL('../src/pages.json', import.meta.url)
const original = readFileSync(pagesJsonPath, 'utf8')

function hideCommunityForProduction() {
  const config = JSON.parse(original)
  config.pages = (config.pages || []).filter((page) => page.path !== 'pages/community/index')
  if (config.tabBar && Array.isArray(config.tabBar.list)) {
    config.tabBar.list = config.tabBar.list.filter((item) => item.pagePath !== 'pages/community/index')
  }
  writeFileSync(pagesJsonPath, JSON.stringify(config, null, 2) + '\n')
}

try {
  if (process.env.KEEP_COMMUNITY_IN_PROD === '1') {
    console.log('[build-h5-prod] KEEP_COMMUNITY_IN_PROD=1，保留社区页面')
  } else {
    hideCommunityForProduction()
    console.log('[build-h5-prod] 生产构建已临时隐藏社区页面和 tab')
  }

  const result = spawnSync('uni', ['build'], {
    stdio: 'inherit',
    env: process.env,
    shell: process.platform === 'win32',
  })
  if (result.error) throw result.error
  process.exitCode = result.status || 0
} finally {
  writeFileSync(pagesJsonPath, original)
}
