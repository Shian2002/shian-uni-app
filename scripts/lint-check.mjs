#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { extname, join, relative } from 'node:path'

const root = process.cwd()
const scanDirs = ['backend', 'database', 'scripts', 'src', 'tests']
const textExtensions = new Set([
  '.css',
  '.html',
  '.js',
  '.json',
  '.md',
  '.mjs',
  '.py',
  '.sh',
  '.sql',
  '.svg',
  '.vue',
])
const syntaxExtensions = new Set(['.js', '.mjs'])
const ignoredPathParts = new Set([
  '.git',
  '.gstack',
  '.pytest_cache',
  'backups',
  'dist',
  'node_modules',
  'server-backup',
])

const allowedSecretMatches = [
  'SMTP_PASS',
  'ALERT_WECHAT_WEBHOOK=https://...',
  'QQ_APP_SECRET',
  'WECHAT_APP_SECRET',
  'GITEE_CLIENT_SECRET',
  'DOUBAO_API_KEY',
  'SILICONFLOW_API_KEY',
]

const secretPatterns = [
  {
    name: '疑似硬编码密钥字段',
    pattern: /\b(?:api[_-]?key|secret|token|password|passwd|pwd)\b\s*[:=]\s*['"]([^'"\n]{12,})['"]/i,
  },
  {
    name: '疑似 Bearer Token',
    pattern: /\bBearer\s+[A-Za-z0-9._~+/=-]{20,}/,
  },
  {
    name: '疑似私钥块',
    pattern: /-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----/,
  },
]

function walk(dir) {
  const out = []
  for (const entry of readdirSync(dir)) {
    const path = join(dir, entry)
    const rel = relative(root, path)
    if (rel.split('/').some((part) => ignoredPathParts.has(part))) continue
    const st = statSync(path)
    if (st.isDirectory()) {
      out.push(...walk(path))
    } else if (st.isFile() && textExtensions.has(extname(path))) {
      out.push(path)
    }
  }
  return out
}

function lineNumber(content, index) {
  return content.slice(0, index).split('\n').length
}

function isAllowedSecretLine(line) {
  return allowedSecretMatches.some((token) => line.includes(token))
}

const issues = []
const files = scanDirs.flatMap((dir) => walk(join(root, dir)))

for (const file of files) {
  const rel = relative(root, file)
  const content = readFileSync(file, 'utf8')

  const lines = content.split('\n')
  const debuggerLineIndex = lines.findIndex((line) => /^\s*debugger\s*;?\s*$/.test(line))
  if (debuggerLineIndex >= 0) {
    issues.push(`${rel}:${debuggerLineIndex + 1} 包含 debugger 调试残留`)
  }

  for (const rule of secretPatterns) {
    for (const match of content.matchAll(new RegExp(rule.pattern, rule.pattern.flags.includes('g') ? rule.pattern.flags : `${rule.pattern.flags}g`))) {
      const line = lines[lineNumber(content, match.index || 0) - 1] || ''
      if (isAllowedSecretLine(line)) continue
      issues.push(`${rel}:${lineNumber(content, match.index || 0)} ${rule.name}`)
    }
  }

  if (syntaxExtensions.has(extname(file))) {
    try {
      execFileSync('node', ['--check', file], { stdio: 'pipe' })
    } catch (error) {
      const output = [error.stdout, error.stderr].filter(Boolean).join('\n').trim()
      issues.push(`${rel} JavaScript 语法检查失败\n${output}`)
    }
  }
}

if (issues.length > 0) {
  console.error('[lint-check] 发现问题:')
  for (const issue of issues) console.error(`- ${issue}`)
  process.exit(1)
}

console.log(`[lint-check] 通过，已检查 ${files.length} 个文本文件`)
