#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.REAL_USER_ROSTER_STRICT === '1'
const configPath = process.env.REAL_USER_ROSTER_CONFIG || 'configs/release/real-user-roster.json'
const packageJson = readJson('package.json') || {}
const version = process.env.REAL_USER_ROSTER_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.REAL_USER_ROSTER_OUT_DIR || join(root, 'artifacts', 'real-user-roster', `${localTimestamp()}-${version}`)
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const activePlatforms = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms
  : ['h5', 'android', 'ios', 'harmony', 'macos', 'windows']

const knownPlatforms = ['h5', 'android', 'ios', 'harmony', 'macos', 'windows']
const allowedStatuses = new Set(['not-assigned', 'assigned', 'in-progress', 'submitted', 'passed', 'failed', 'retest'])
const secretPatterns = [
  /password/i,
  /passwd/i,
  /secret/i,
  /token/i,
  /api[_-]?key/i,
  /验证码/,
  /密码/,
  /密钥/,
  /口令/,
  /[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i,
  /\b1[3-9]\d{9}\b/,
]

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function readJson(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  try {
    return JSON.parse(readFileSync(fullPath, 'utf8'))
  } catch (_) {
    return null
  }
}

function pathExists(path) {
  return Boolean(path) && existsSync(join(root, path))
}

function hasSecretText(value) {
  return secretPatterns.some((pattern) => pattern.test(JSON.stringify(value || '')))
}

function resolveLatestPath(path) {
  if (!path?.includes('/latest/')) return path
  const latestPacket = latestRealUserPacket()
  if (!latestPacket) return path
  return path.replace('artifacts/real-user-packets/latest', latestPacket)
}

function latestRealUserPacket() {
  const base = join(root, 'artifacts', 'real-user-packets')
  if (!existsSync(base)) return ''
  const names = readdirSync(base)
    .filter((name) => statSync(join(base, name)).isDirectory())
    .sort((a, b) => b.localeCompare(a))
  return names[0] ? `artifacts/real-user-packets/${names[0]}` : ''
}

function validateSlot(platform, slot) {
  const issues = []
  const warnings = []
  if (!slot.slotId) issues.push(`${platform.id} 缺少 slotId`)
  if (!allowedStatuses.has(slot.status)) issues.push(`${slot.slotId || platform.id} status 非法: ${slot.status}`)
  if (hasSecretText(slot)) issues.push(`${slot.slotId || platform.id} 可能包含手机号、邮箱、密码、验证码或 token`)
  if (['assigned', 'in-progress', 'submitted', 'passed', 'failed', 'retest'].includes(slot.status) && !slot.testerAlias) {
    issues.push(`${slot.slotId} 已分配但缺少 testerAlias`)
  }
  if (slot.status === 'passed') {
    const resultPath = resolveLatestPath(slot.resultPath)
    const screenshotDir = resolveLatestPath(slot.screenshotDir)
    if (!pathExists(resultPath)) issues.push(`${slot.slotId} passed 但 resultPath 不存在: ${resultPath}`)
    if (!pathExists(screenshotDir)) issues.push(`${slot.slotId} passed 但 screenshotDir 不存在: ${screenshotDir}`)
  }
  if (slot.status === 'submitted') {
    const resultPath = resolveLatestPath(slot.resultPath)
    if (!pathExists(resultPath)) warnings.push(`${slot.slotId} submitted 但 resultPath 不存在: ${resultPath}`)
  }
  return {
    slotId: slot.slotId,
    status: slot.status,
    testerAlias: slot.testerAlias || '',
    deviceGroup: slot.deviceGroup || '',
    resultPath: resolveLatestPath(slot.resultPath || ''),
    screenshotDir: resolveLatestPath(slot.screenshotDir || ''),
    issues,
    warnings,
  }
}

function validatePlatform(platform, minimumTestersPerPlatform) {
  const issues = []
  const warnings = []
  const deferred = deferredPlatforms.has(platform.id)
  if (!knownPlatforms.includes(platform.id)) issues.push(`未知平台: ${platform.id || 'missing-id'}`)
  if (!Array.isArray(platform.slots)) issues.push(`${platform.id || 'unknown'} 缺少 slots`)
  if (hasSecretText(platform)) issues.push(`${platform.id || 'unknown'} 可能包含手机号、邮箱、密码、验证码或 token`)
  if (deferred) {
    return {
      id: platform.id,
      name: platform.name,
      readiness: 'deferred',
      deferred,
      assigned: 0,
      passed: 0,
      required: minimumTestersPerPlatform,
      slots: Array.isArray(platform.slots) ? platform.slots.map((slot) => ({
        slotId: slot.slotId,
        status: slot.status,
        testerAlias: slot.testerAlias || '',
        deviceGroup: slot.deviceGroup || '',
        resultPath: resolveLatestPath(slot.resultPath || ''),
        screenshotDir: resolveLatestPath(slot.screenshotDir || ''),
        issues: [],
        warnings: [],
      })) : [],
      issues: [],
      warnings: [],
    }
  }
  const slots = Array.isArray(platform.slots) ? platform.slots.map((slot) => validateSlot(platform, slot)) : []
  for (const slot of slots) {
    issues.push(...slot.issues)
    warnings.push(...slot.warnings)
  }
  const passed = slots.filter((slot) => slot.status === 'passed').length
  const assigned = slots.filter((slot) => slot.status !== 'not-assigned').length
  if (slots.length < minimumTestersPerPlatform) issues.push(`${platform.id} 测试槽位不足: ${slots.length}/${minimumTestersPerPlatform}`)
  if (passed < minimumTestersPerPlatform) issues.push(`${platform.id} 通过测试人不足: ${passed}/${minimumTestersPerPlatform}`)
  const coveredGroups = new Set(slots.filter((slot) => slot.status !== 'not-assigned').map((slot) => slot.deviceGroup))
  for (const group of platform.requiredDeviceGroups || []) {
    if (!coveredGroups.has(group)) warnings.push(`${platform.id} 设备组未分配: ${group}`)
  }
  const readiness = issues.length === 0 && warnings.length === 0 ? 'ready' : (assigned > 0 ? 'partial' : 'missing')
  return {
    id: platform.id,
    name: platform.name,
    readiness,
    deferred,
    assigned,
    passed,
    required: minimumTestersPerPlatform,
    slots,
    issues,
    warnings,
  }
}

function main() {
  const config = readJson(configPath)
  const issues = []
  const warnings = []
  if (!config) issues.push(`缺少或无法解析 ${configPath}`)
  if (config && hasSecretText({ ...config, platforms: undefined, policy: undefined })) {
    issues.push(`${configPath} 顶层字段可能包含手机号、邮箱、密码、验证码或 token`)
  }
  const minimumTestersPerPlatform = Number.parseInt(config?.minimumTestersPerPlatform || '2', 10)
  if (!Array.isArray(config?.platforms)) issues.push(`${configPath} 缺少 platforms 数组`)
  const rows = Array.isArray(config?.platforms)
    ? config.platforms.map((platform) => validatePlatform(platform, minimumTestersPerPlatform))
    : []
  for (const row of rows.filter((item) => !item.deferred)) {
    issues.push(...row.issues)
    warnings.push(...row.warnings)
  }
  for (const id of activePlatforms) {
    if (!rows.some((row) => row.id === id)) issues.push(`${configPath} 缺少平台: ${id}`)
  }
  const summary = {
    ready: rows.filter((row) => row.readiness === 'ready').length,
    partial: rows.filter((row) => row.readiness === 'partial').length,
    missing: rows.filter((row) => row.readiness === 'missing').length,
    deferred: rows.filter((row) => row.readiness === 'deferred').length,
    assignedSlots: rows.reduce((total, row) => total + row.assigned, 0),
    passedSlots: rows.reduce((total, row) => total + row.passed, 0),
  }
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    configPath,
    latestPacket: latestRealUserPacket(),
    minimumTestersPerPlatform,
    releaseScope: {
      configPath: 'configs/release/current-release-scope.json',
      currentBatch: releaseScope.currentBatch || '',
      activePlatforms,
      deferredPlatforms: [...deferredPlatforms],
    },
    passed: issues.length === 0 && warnings.length === 0 && rows.length > 0,
    summary,
    platforms: rows,
    issues,
    warnings,
  }

  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  const md = [
    '# 真实用户测试名册检查',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 配置：\`${configPath}\``,
    `> 最新测试包：${report.latestPacket ? `\`${report.latestPacket}\`` : '缺失'}`,
    `> 结论：${report.passed ? '通过' : '未通过'}`,
    '',
    `汇总：READY ${summary.ready} / PARTIAL ${summary.partial} / MISSING ${summary.missing} / DEFERRED ${summary.deferred} / ASSIGNED ${summary.assignedSlots} / PASSED ${summary.passedSlots}`,
    '',
    '| 平台 | Readiness | 已分配 | 已通过 | 测试槽位 |',
    '| --- | --- | ---: | ---: | --- |',
    ...rows.map((row) => `| ${row.name || row.id} | ${row.readiness} | ${row.assigned} | ${row.passed}/${row.required} | ${row.slots.map((slot) => `${slot.slotId}:${slot.status}`).join('<br>')} |`),
    '',
    '## 问题',
    '',
    ...(issues.length ? issues.map((issue) => `- ${issue}`) : ['- 无结构性问题。']),
    '',
    '## 警告',
    '',
    ...(warnings.length ? warnings.map((warning) => `- ${warning}`) : ['- 无警告。']),
    '',
    '## 放行规则',
    '',
    '- 非 strict 模式只生成名册报告，不因为尚未分配测试人而失败。',
    `- 正式上架候选前运行 \`npm run real-user:roster -- --strict\`；当前批次平台 ${activePlatforms.join('、')} 至少 2 个测试槽位必须是 \`passed\`，且 resultPath/screenshotDir 指向真实文件。`,
    '- 本台账禁止记录手机号、邮箱、审核账号密码、验证码、token 和用户隐私原始数据。',
    '',
  ].join('\n')
  writeFileSync(join(outDir, 'README.md'), md)
  console.log(JSON.stringify({
    outDir: rel(outDir),
    passed: report.passed,
    summary,
    issues: issues.length,
    warnings: warnings.length,
  }, null, 2))
  if (strict && !report.passed) process.exit(1)
}

main()
