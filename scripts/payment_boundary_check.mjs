#!/usr/bin/env node

import { existsSync, readdirSync, readFileSync, statSync } from 'node:fs'
import { extname, join, relative } from 'node:path'

const root = process.cwd()
const channel = String(process.env.VITE_RELEASE_CHANNEL || process.env.RELEASE_CHANNEL || '').trim().toLowerCase()
const restricted = new Set(['appstore', 'app-store', 'ios', 'testflight', 'google-play', 'googleplay'])
const restrictedBuild = restricted.has(channel)
const issues = []

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function read(path) {
  return readFileSync(join(root, path), 'utf8')
}

function requireText(path, snippets) {
  if (!existsSync(join(root, path))) {
    issues.push(`缺少文件: ${path}`)
    return
  }
  const text = read(path)
  for (const snippet of snippets) {
    if (!text.includes(snippet)) issues.push(`${path} 缺少关键内容: ${snippet}`)
  }
}

function walk(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return []
  const entries = []
  for (const name of readdirSync(fullPath)) {
    const item = join(fullPath, name)
    const stat = statSync(item)
    if (stat.isDirectory()) entries.push(...walk(rel(item)))
    else entries.push(rel(item))
  }
  return entries
}

function scanBuiltH5() {
  const files = walk('dist/build/h5').filter((path) => ['.html', '.js', '.css'].includes(extname(path).toLowerCase()))
  const forbidden = [
    '/api/recharge/create-order',
    '/api/recharge/verify-payment',
    'alipay-recharge.jpg',
    '上传支付宝付款成功截图',
    '提交截图并识别到账',
  ]
  for (const file of files) {
    const text = read(file)
    for (const snippet of forbidden) {
      if (text.includes(snippet)) issues.push(`受限渠道构建产物 ${file} 不应包含: ${snippet}`)
    }
  }
}

requireText('src/utils/releasePolicy.js', ['appstore', 'google-play', 'isExternalRechargeEnabled'])
for (const path of ['src/pages/points/index.vue', 'src/package-user/points/index.vue']) {
  requireText(path, [
    'externalRechargeEnabled',
    'v-if="externalRechargeEnabled"',
    'v-if="!externalRechargeEnabled"',
    '当前审核渠道暂不开放充值',
  ])
}

if (restrictedBuild) scanBuiltH5()

if (issues.length) {
  console.error('支付边界检查失败:')
  for (const issue of issues) console.error(`- ${issue}`)
  process.exit(1)
}

console.log(JSON.stringify({
  channel: channel || 'default',
  restrictedBuild,
  checkedBuiltH5: restrictedBuild && existsSync(join(root, 'dist/build/h5')),
  result: 'passed',
}, null, 2))
