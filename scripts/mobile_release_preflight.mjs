#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'

const root = process.cwd()
const issues = []
const warnings = []
const requireBuild = process.env.MOBILE_PREFLIGHT_REQUIRE_BUILD === '1'

function readJson(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) {
    issues.push(`缺少文件: ${path}`)
    return null
  }
  try {
    return JSON.parse(readFileSync(fullPath, 'utf8'))
  } catch (error) {
    issues.push(`${path} 不是合法 JSON: ${error.message}`)
    return null
  }
}

function requireEqual(label, actual, expected) {
  if (actual !== expected) {
    issues.push(`${label} 不一致: actual=${actual || '<empty>'}, expected=${expected || '<empty>'}`)
  }
}

function requireIncludes(label, value, snippets) {
  const text = String(value || '')
  for (const snippet of snippets) {
    if (!text.includes(snippet)) issues.push(`${label} 缺少关键内容: ${snippet}`)
  }
}

function requireFile(path) {
  if (!existsSync(join(root, path))) {
    issues.push(`缺少文件: ${path}`)
  }
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function walk(dir) {
  if (!existsSync(dir)) return []
  const entries = []
  for (const name of readdirSync(dir)) {
    const full = join(dir, name)
    const stat = statSync(full)
    if (stat.isDirectory()) entries.push(...walk(full))
    else entries.push(full)
  }
  return entries
}

function firstExisting(paths) {
  return paths.find((path) => existsSync(join(root, path))) || ''
}

const manifest = readJson('src/manifest.json')
const pages = readJson('src/pages.json')
const android = readJson('configs/release/android-channels.json')
const ios = readJson('configs/release/ios-appstore.json')
const harmony = readJson('configs/release/harmony-appgallery.json')

if (manifest && android && ios && harmony) {
  requireEqual('Android 包名', manifest['app-plus']?.distribute?.android?.packagename, android.packageName)
  requireEqual('iOS Bundle ID', manifest['app-plus']?.distribute?.ios?.bundleIdentifier, ios.bundleId)
  requireEqual('鸿蒙 bundleName', android.packageName, harmony.bundleName)
  requireEqual('versionName', manifest.versionName, android.versionName)
  requireEqual('versionCode', Number(manifest.versionCode), Number(android.versionCode))
  requireEqual('iOS buildNumber', String(manifest.versionCode), String(ios.buildNumber))

  if (!manifest['app-plus']) issues.push('src/manifest.json 缺少 app-plus')
  if (!manifest.appid || manifest.appid.includes('TODO')) issues.push('src/manifest.json appid 必须是 DCloud 发行 ID 或明确占位')
  if (!Array.isArray(manifest['app-plus']?.distribute?.android?.permissions)) {
    issues.push('Android permissions 必须显式配置为数组')
  }
  if ((manifest['app-plus']?.distribute?.android?.permissions || []).length > 0) {
    warnings.push('Android permissions 非空，上架前必须逐项写权限触发说明')
  }
}

if (android) {
  const expectedChannels = ['yingyongbao', 'huawei', 'xiaomi', 'oppo', 'vivo', 'google-play']
  const ids = new Set((android.channels || []).map((item) => item.id))
  for (const id of expectedChannels) {
    if (!ids.has(id)) issues.push(`configs/release/android-channels.json 缺少渠道: ${id}`)
  }
  requireIncludes('Android requiredChecks', JSON.stringify(android.requiredChecks || []), ['登录注册', '首页综合解读', '账号注销'])
}

if (ios) {
  requireIncludes('iOS paymentPolicy', ios.paymentPolicy, ['隐藏', 'Apple IAP'])
  requireIncludes('iOS requiredMaterials', JSON.stringify(ios.requiredMaterials || []), ['App Privacy', '测试账号', '账号删除入口'])
}

if (harmony) {
  requireIncludes('Harmony requiredMaterials', JSON.stringify(harmony.requiredMaterials || []), ['隐私政策 URL', '权限说明', '手机和平板截图'])
  requireIncludes('Harmony requiredChecks', JSON.stringify(harmony.requiredChecks || []), ['鸿蒙手机安装', '鸿蒙平板适配'])
}

if (pages) {
  const pagePaths = new Set((pages.pages || []).map((item) => item.path))
  for (const path of [
    'pages/index/index',
    'pages/profile/index',
    'pages/points/index',
    'pages/user-management/index',
    'pages/about/index',
    'pages/bazi-index/index',
    'pages/qimen/index',
    'pages/ziwei/index',
  ]) {
    if (!pagePaths.has(path)) issues.push(`src/pages.json 缺少关键页面: ${path}`)
  }
  if (!pages.tabBar?.custom) issues.push('src/pages.json tabBar.custom 必须保持 true，避免多端导航不一致')
}

requireFile('docs/release/mobile-build-evidence.md')

const appEntry = firstExisting([
  'dist/build/app/__uniappview.html',
  'dist/build/app/index.html',
])
const appRuntimeEntry = firstExisting([
  'dist/build/app/app-service.js',
  appEntry,
].filter(Boolean))
const appFiles = walk(join(root, 'dist/build/app')).filter((file) => /\.(html|js|json)$/i.test(file))
if (appEntry && appRuntimeEntry) {
  const stat = statSync(join(root, appEntry))
  if (!stat.isFile() || stat.size === 0) issues.push(`${appEntry} 为空或不是文件`)
  const runtimeStat = statSync(join(root, appRuntimeEntry))
  if (!runtimeStat.isFile() || runtimeStat.size === 0) issues.push(`${appRuntimeEntry} 为空或不是文件`)
  const appRuntime = appFiles.map((file) => readFileSync(file, 'utf8')).join('\n')
  requireIncludes('dist/build/app runtime', appRuntime, [
    'https://shianjieyouwu.com',
    'EventSource',
    'XMLHttpRequest',
    'withCredentials',
  ])
  console.log(JSON.stringify({
    appResourceBuild: {
      entry: appEntry,
      runtime: appRuntimeEntry,
      bytes: stat.size,
      sha256: sha256(join(root, appEntry)),
      checkedFiles: appFiles.length
    }
  }, null, 2))
} else if (requireBuild) {
  issues.push('缺少 dist/build/app/__uniappview.html 或 app-service.js；请先执行 npm run build:app')
} else {
  warnings.push('未发现 dist/build/app/__uniappview.html 或 app-service.js；配置预检继续，发包前请执行 MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight')
}

for (const warning of warnings) {
  console.warn(`警告: ${warning}`)
}

if (issues.length > 0) {
  console.error('移动端发行预检失败:')
  for (const issue of issues) {
    console.error(`- ${issue}`)
  }
  process.exit(1)
}

console.log('移动端发行预检通过')
