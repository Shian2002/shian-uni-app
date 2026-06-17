#!/usr/bin/env node

import { readFileSync, writeFileSync } from 'node:fs'
import { spawn } from 'node:child_process'
import { join } from 'node:path'

const root = process.cwd()
const manifestPath = join(root, 'src', 'manifest.json')
const target = process.env.VITE_API_PROXY_TARGET || 'https://shianjieyouwu.com'
const original = readFileSync(manifestPath, 'utf8')
let restored = false

function restoreManifest() {
  if (restored) return
  writeFileSync(manifestPath, original)
  restored = true
}

function patchManifest() {
  const manifest = JSON.parse(original)
  manifest.h5 ||= {}
  manifest.h5.devServer ||= {}
  manifest.h5.devServer.proxy ||= {}
  manifest.h5.devServer.proxy['/api'] ||= {}
  manifest.h5.devServer.proxy['/api'].target = target
  manifest.h5.devServer.proxy['/api'].changeOrigin = true
  writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`)
}

patchManifest()
console.log(`[dev:h5:online-login] 本次 H5 /api 代理目标: ${target}`)
console.log('[dev:h5:online-login] 退出 dev server 后会恢复 src/manifest.json')

const child = spawn('uni dev', {
  cwd: root,
  env: { ...process.env, VITE_API_PROXY_TARGET: target },
  shell: true,
  stdio: 'inherit',
})

function shutdown(signal) {
  if (!child.killed) child.kill(signal)
}

process.on('SIGINT', () => shutdown('SIGINT'))
process.on('SIGTERM', () => shutdown('SIGTERM'))
process.on('exit', restoreManifest)

child.on('exit', (code, signal) => {
  restoreManifest()
  if (signal) process.kill(process.pid, signal)
  process.exit(code ?? 0)
})

child.on('error', (error) => {
  restoreManifest()
  console.error(`[dev:h5:online-login] 启动 uni dev 失败: ${error.message}`)
  process.exit(1)
})
