#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.FINAL_PACKAGE_PREFLIGHT_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.FINAL_PACKAGE_PREFLIGHT_OUT_DIR || join(root, 'artifacts', 'final-package-preflight', `${localTimestamp()}-${version}`)
const strict = process.argv.includes('--strict') || process.env.FINAL_PACKAGE_PREFLIGHT_STRICT === '1'

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

function latestDir(parent, requiredFile = '') {
  const fullParent = join(root, parent)
  if (!existsSync(fullParent)) return ''
  const dirs = readdirSync(fullParent, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => ({ name: entry.name, fullPath: join(fullParent, entry.name) }))
    .filter((entry) => !requiredFile || existsSync(join(entry.fullPath, requiredFile)))
    .sort((a, b) => statSync(b.fullPath).mtimeMs - statSync(a.fullPath).mtimeMs || b.name.localeCompare(a.name))
  return dirs[0] ? `${parent}/${dirs[0].name}` : ''
}

function fileState(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return { path, exists: false, kind: 'missing', bytes: 0, mtime: '' }
  const stat = statSync(fullPath)
  return {
    path,
    exists: true,
    kind: stat.isDirectory() ? 'directory' : 'file',
    bytes: stat.isFile() ? stat.size : 0,
    mtime: new Date(stat.mtimeMs).toISOString(),
  }
}

function checkPath(path, label, hard = true) {
  const state = fileState(path)
  return { label, hard, ...state }
}

const latest = {
  backendMatrix: latestDir('artifacts/platform-backend-matrix', 'report.json'),
  finalPackagePlan: latestDir('artifacts/final-package-plan', 'report.json'),
  currentDownloads: existsSync(join(root, 'artifacts/current-downloads/manifest.json')) ? 'artifacts/current-downloads' : '',
}

const backendMatrix = latest.backendMatrix ? readJson(`${latest.backendMatrix}/report.json`) : null
const finalPackagePlan = latest.finalPackagePlan ? readJson(`${latest.finalPackagePlan}/report.json`) : null
const currentDownloads = readJson('artifacts/current-downloads/manifest.json')
const expectedConfirm = `final-package-refresh:${version}`

const checks = [
  checkPath('node_modules/@dcloudio', '根项目 uni-app 依赖'),
  checkPath('dist/build/h5/index.html', 'H5 构建产物'),
  checkPath('dist/build/app/__uniappview.html', '移动 App Resource 视图入口'),
  checkPath('dist/build/app/app-service.js', '移动 App Runtime'),
  checkPath('desktop/package-lock.json', '桌面依赖锁文件'),
  checkPath('desktop/node_modules/electron/dist/Electron.app/Contents/MacOS/Electron', '桌面 Electron 可执行文件'),
  checkPath('desktop/node_modules/@electron/asar/bin/asar.js', 'macOS app.asar 打包脚本'),
  checkPath('desktop/release/mac-arm64/时安解忧屋.app', 'macOS .app 最终构建产物', false),
  checkPath('artifacts/current-downloads/shian-current-macos-arm64.dmg', '当前 macOS DMG', false),
  checkPath('artifacts/current-downloads/shian-current-windows-x64.exe', '当前 Windows EXE', false),
  checkPath('artifacts/current-downloads/shian-current-android-debug.apk', '当前 Android APK', false),
  checkPath('artifacts/current-downloads/shian-current-android-debug.aab', '当前 Android AAB', false),
]

const hardMissing = checks.filter((item) => item.hard && !item.exists).map((item) => `${item.label}: ${item.path}`)
const softMissing = checks.filter((item) => !item.hard && !item.exists).map((item) => `${item.label}: ${item.path}`)
const evidenceIssues = [
  backendMatrix?.summary?.backendReady !== backendMatrix?.summary?.total && '全端后端矩阵未达到 backendReady=total',
  !backendMatrix && '缺少全端后端矩阵报告',
  !finalPackagePlan && '缺少最终安装包刷新计划报告',
  finalPackagePlan && finalPackagePlan.readyToRunFinalPackageRefresh !== true && '最终安装包刷新计划未显示 readyToRunFinalPackageRefresh=true',
  !currentDownloads && '缺少 artifacts/current-downloads/manifest.json',
].filter(Boolean)

const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  expectedConfirm,
  passed: hardMissing.length === 0 && evidenceIssues.length === 0,
  readyForConfirmedFinalize: hardMissing.length === 0 && evidenceIssues.length === 0,
  latest,
  backendSummary: backendMatrix?.summary || null,
  finalPackagePlan: finalPackagePlan ? {
    readyToRunFinalPackageRefresh: finalPackagePlan.readyToRunFinalPackageRefresh === true,
    missingPackages: finalPackagePlan.missingPackages || [],
    userMustDoLast: finalPackagePlan.userMustDoLast || [],
  } : null,
  currentDownloadsPassed: currentDownloads?.passed === true,
  checks,
  hardMissing,
  softMissing,
  evidenceIssues,
  next: [
    '默认先跑 npm run release:finalize:plan 预览队列。',
    '若 hardMissing 包含 desktop/node_modules/electron 或 @electron/asar，先执行 npm --prefix desktop install。',
    '若缺少 macOS .app 最终构建产物，最后统一打包阶段会先运行 desktop:build:mac:arm64 重新生成。',
    `真正执行前需要显式设置 CONFIRM_FINAL_PACKAGE_REFRESH=${expectedConfirm}。`,
  ],
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# 最终打包执行前置检查',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.passed ? '可进入确认后的最终打包' : '仍有本机或证据缺口'}`,
  `> 真正执行确认：\`CONFIRM_FINAL_PACKAGE_REFRESH=${expectedConfirm} npm run release:finalize\``,
  '',
  '## 关键输入',
  '',
  ...checks.map((item) => `- ${item.exists ? 'OK' : (item.hard ? '缺失' : '可最后补齐')} ${item.label}：\`${item.path}\``),
  '',
  '## 硬缺口',
  '',
  ...(hardMissing.length ? hardMissing.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 可最后补齐',
  '',
  ...(softMissing.length ? softMissing.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 证据缺口',
  '',
  ...(evidenceIssues.length ? evidenceIssues.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 下一步',
  '',
  ...report.next.map((item) => `- ${item}`),
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  readyForConfirmedFinalize: report.readyForConfirmedFinalize,
  hardMissing,
  softMissing,
  evidenceIssues,
}, null, 2))

if (strict && !report.passed) process.exit(1)
