#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { copyFileSync, cpSync, existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { basename, extname, join, relative } from 'node:path'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.MOBILE_APP_RESOURCE_PACKET_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.MOBILE_APP_RESOURCE_PACKET_DIR || join(root, 'artifacts', 'mobile-app-resource-packets', `${localTimestamp()}-${version}`)
const indexDir = join(root, 'artifacts', 'mobile-app-resource-packets')

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

function git(args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim()
  } catch (_) {
    return ''
  }
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function copyFileEvidence(source, targetDir = outDir, targetName = basename(source)) {
  const sourcePath = join(root, source)
  if (!existsSync(sourcePath)) return null
  const targetPath = join(targetDir, targetName)
  copyFileSync(sourcePath, targetPath)
  const stat = statSync(targetPath)
  const sourceStat = statSync(sourcePath)
  return {
    source,
    path: rel(targetPath),
    fileName: basename(targetPath),
    bytes: stat.size,
    sha256: sha256(targetPath),
    sourceMtimeMs: sourceStat.mtimeMs,
    sourceMtime: new Date(sourceStat.mtimeMs).toISOString(),
  }
}

function copyDir(source, targetName) {
  const sourcePath = join(root, source)
  if (!existsSync(sourcePath)) return null
  const targetPath = join(outDir, targetName)
  cpSync(sourcePath, targetPath, { recursive: true })
  return {
    source,
    path: rel(targetPath),
    fileCount: walkFiles(rel(targetPath)).length,
    bytes: walkFiles(rel(targetPath)).reduce((total, item) => total + item.bytes, 0),
  }
}

function walkFiles(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return []
  const entries = []
  for (const name of readdirSync(fullPath)) {
    const item = join(fullPath, name)
    const stat = statSync(item)
    if (stat.isDirectory()) entries.push(...walkFiles(rel(item)))
    else entries.push({ path: rel(item), bytes: stat.size, sha256: sha256(item), ext: extname(item).toLowerCase() })
  }
  return entries
}

function latestDir(path, filename = '') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory() && (!filename || existsSync(join(item.full, filename))))
    .sort((a, b) => b.name.localeCompare(a.name))
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function fileMtime(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const stat = statSync(fullPath)
  return { path, mtimeMs: stat.mtimeMs, mtime: new Date(stat.mtimeMs).toISOString() }
}

function firstExisting(paths) {
  return paths.find((path) => existsSync(join(root, path))) || ''
}

function writeLatestIndex(manifest) {
  const latestManifest = {
    generatedAt: new Date().toISOString(),
    latestPacketDir: manifest.outDir,
    appResourceDir: `${manifest.outDir}/app-resource`,
    storeIcon: `${manifest.outDir}/app-icon-1024.png`,
    passed: manifest.passed,
    version: manifest.version,
    commit: manifest.commit,
  }
  mkdirSync(indexDir, { recursive: true })
  writeFileSync(join(indexDir, 'latest-manifest.json'), `${JSON.stringify(latestManifest, null, 2)}\n`)
  writeFileSync(join(indexDir, 'LATEST.md'), `${[
    '# 最新移动端 App 资源交付包',
    '',
    `> 更新时间：${latestManifest.generatedAt}`,
    `> 版本：${manifest.version}`,
    `> commit：${manifest.commit || '未读取到'}`,
    `> 结果：${manifest.passed ? '通过' : '未通过'}`,
    '',
    '## 直接入口',
    '',
    `- App 资源目录：\`${latestManifest.appResourceDir}\``,
    `- 1024 图标母图：\`${latestManifest.storeIcon}\``,
    `- 完整目录：\`${latestManifest.latestPacketDir}\``,
    '',
    '## 说明',
    '',
    '- 这是生成 Android APK/AAB、iOS TestFlight/IPA、鸿蒙 HAP 前的输入包，不是安装包。',
    '- 证书、keystore、p12、mobileprovision、签名口令和商店账号密码不得放入本目录。',
    '- 真实安装包生成后仍要回传到 `artifacts/release-inbox/v1.0.0/<platform>/`。',
  ].join('\n')}\n`)
  return latestManifest
}

mkdirSync(outDir, { recursive: true })

const appResource = copyDir('dist/build/app', 'app-resource')
const appIcons = copyDir('src/static/app-icons', 'app-icons')
const configsDir = join(outDir, 'configs')
mkdirSync(configsDir, { recursive: true })
const configFiles = [
  'configs/release/android-channels.json',
  'configs/release/ios-appstore.json',
  'configs/release/harmony-appgallery.json',
  'configs/release/app-icons.json',
]
const expectedConfigCount = configFiles.length
const copiedConfigFiles = configFiles
  .map((path) => copyFileEvidence(path, configsDir))
  .filter(Boolean)

const storeIcon = copyFileEvidence('src/static/app-icons/app-icon-1024.png')
const manifestFile = copyFileEvidence('src/manifest.json', outDir, 'source-manifest.json')
const latestMobileBuildRequests = latestDir('artifacts/mobile-build-requests', 'README.md')
const latestMobileBuildEnv = latestDir('artifacts/mobile-build-env', 'report.json')
const latestHBuilderXResources = latestDir('artifacts/hbuilderx-mobile-resources', 'report.json')
const latestMobileApiEvidence = latestDir('artifacts/mobile-api-evidence', 'manifest.json')
const latestAppIcons = latestDir('artifacts/app-icons', 'report.json')
const latestMobileApiEvidenceManifest = latestMobileApiEvidence ? readJson(`${latestMobileApiEvidence}/manifest.json`) : null
const latestMobileApiEvidenceMtime = latestMobileApiEvidence ? fileMtime(`${latestMobileApiEvidence}/manifest.json`) : null
const appEntryPath = firstExisting([
  'dist/build/app/__uniappview.html',
  'dist/build/app/index.html',
  'dist/build/app/app-service.js',
])
const appEntryInfo = appEntryPath ? fileMtime(appEntryPath) : null
const sourceFreshnessInputs = [
  'src/App.vue',
  'src/main.js',
  'src/manifest.json',
  'src/pages/index/index.vue',
  'package.json',
].map(fileMtime).filter(Boolean)
const newestSource = sourceFreshnessInputs.reduce((latest, item) => (
  !latest || item.mtimeMs > latest.mtimeMs ? item : latest
), null)

const filesForChecksum = [
  ...walkFiles(rel(outDir)).filter((item) => !['.md', '.json'].includes(item.ext)),
]

const issues = []
if (!appResource) issues.push('缺少 dist/build/app，请先执行 npm run build:app')
if (!appEntryInfo) issues.push('缺少 dist/build/app/__uniappview.html 或 app-service.js')
if (appEntryInfo && newestSource && appEntryInfo.mtimeMs < newestSource.mtimeMs) {
  issues.push(`dist/build/app 早于移动端关键源码，请先执行 npm run build:app：app=${appEntryInfo.mtime} source=${newestSource.path} ${newestSource.mtime}`)
}
if (!appIcons) issues.push('缺少 src/static/app-icons，请先执行 npm run release:app-icons')
if (!storeIcon) issues.push('缺少 src/static/app-icons/app-icon-1024.png')
if (copiedConfigFiles.length < expectedConfigCount) issues.push(`移动端发行配置复制不完整: ${copiedConfigFiles.length}/${expectedConfigCount}`)
if (!latestMobileApiEvidenceManifest) issues.push('缺少移动端 API 后端请求证据，请先执行 npm run mobile:api-evidence')
if (latestMobileApiEvidenceManifest && latestMobileApiEvidenceManifest.passed !== true) issues.push('移动端 API 后端请求证据未通过')
if (latestMobileApiEvidenceMtime && appEntryInfo && latestMobileApiEvidenceMtime.mtimeMs < appEntryInfo.mtimeMs) {
  issues.push(`移动端 API 后端请求证据早于最新 App 构建，请先执行 npm run mobile:api-evidence：api=${latestMobileApiEvidenceMtime.mtime} app=${appEntryInfo.mtime}`)
}

const manifest = {
  generatedAt: new Date().toISOString(),
  version,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  outDir: rel(outDir),
  appName: '时安解忧屋',
  status: 'mobile-build-input-packet',
  passed: issues.length === 0,
  appResource,
  appIcons,
  storeIcon,
  manifestFile,
  configFiles: copiedConfigFiles,
  evidence: {
    mobileBuildRequests: latestMobileBuildRequests ? `${latestMobileBuildRequests}/README.md` : '',
    mobileBuildEnv: latestMobileBuildEnv ? `${latestMobileBuildEnv}/report.json` : '',
    hbuilderxResources: latestHBuilderXResources ? `${latestHBuilderXResources}/report.json` : '',
    mobileApiEvidence: latestMobileApiEvidence ? `${latestMobileApiEvidence}/manifest.json` : '',
    appIconReport: latestAppIcons ? `${latestAppIcons}/report.json` : '',
    appEntry: appEntryInfo,
    latestMobileApiEvidenceMtime,
    sourceFreshnessInputs,
    newestSource,
  },
  targetOutputs: [
    'Android APK/AAB',
    'iOS TestFlight/IPA 构建记录',
    '鸿蒙 HAP/AppGallery 包',
  ],
  releaseInbox: {
    android: `artifacts/release-inbox/${version}/android/`,
    ios: `artifacts/release-inbox/${version}/ios/`,
    harmony: `artifacts/release-inbox/${version}/harmony/`,
  },
  forbidden: [
    'keystore',
    'jks',
    'p12',
    'mobileprovision',
    '证书私钥',
    '签名口令',
    '商店账号密码',
  ],
  issues,
}

writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
const latestManifest = writeLatestIndex(manifest)

writeFileSync(join(outDir, 'checksums.sha256'), `${filesForChecksum.map((item) => `${item.sha256}  ${item.path.replace(`${manifest.outDir}/`, '')}`).join('\n')}\n`)

const readme = [
  '# 移动端 App 资源交付包',
  '',
  `> 生成时间：${manifest.generatedAt}`,
  `> 版本：${version}`,
  `> commit：${manifest.commit || '未读取到'}`,
  `> 目录：\`${manifest.outDir}\``,
  '',
  '## 这个包是什么',
  '',
  '- 这是 Android、iOS、鸿蒙真实安装包生成前的输入包。',
  '- 它包含 uni-app App 构建资源、应用图标、非敏感发行配置和打包请求证据。',
  '- 它不是 APK/AAB、IPA/TestFlight 或 HAP，不能直接上架。',
  '',
  '## 打包输入',
  '',
  `- App 资源：\`${manifest.appResource?.path || '缺失'}\``,
  `- 1024 图标母图：\`${manifest.storeIcon?.path || '缺失'}\``,
  `- 图标目录：\`${manifest.appIcons?.path || '缺失'}\``,
  `- manifest：\`${manifest.manifestFile?.path || '缺失'}\``,
  `- 配置目录：\`${rel(configsDir)}\``,
  '',
  '## 生成真实安装包后回传',
  '',
  `- Android：\`${manifest.releaseInbox.android}\``,
  `- iOS：\`${manifest.releaseInbox.ios}\``,
  `- 鸿蒙：\`${manifest.releaseInbox.harmony}\``,
  '- 每个平台同目录补 `build-metadata.json`，记录构建工具、包路径、SHA-256、截图路径和审核账号交付方式。',
  '',
  '## 禁止放入',
  '',
  ...manifest.forbidden.map((item) => `- ${item}`),
  '',
  '## 当前证据',
  '',
  `- 移动端构建请求：${manifest.evidence.mobileBuildRequests ? `\`${manifest.evidence.mobileBuildRequests}\`` : '缺失'}`,
  `- 移动端环境检查：${manifest.evidence.mobileBuildEnv ? `\`${manifest.evidence.mobileBuildEnv}\`` : '缺失'}`,
  `- HBuilderX App Resource 检查：${manifest.evidence.hbuilderxResources ? `\`${manifest.evidence.hbuilderxResources}\`` : '缺失'}`,
  `- 移动端 API 后端请求证据：${manifest.evidence.mobileApiEvidence ? `\`${manifest.evidence.mobileApiEvidence}\`` : '缺失'}`,
  `- 图标检查：${manifest.evidence.appIconReport ? `\`${manifest.evidence.appIconReport}\`` : '缺失'}`,
  '',
  '## 文件校验',
  '',
  '- `checksums.sha256` 记录资源和图标文件 hash。',
  '- `manifest.json` 记录 commit、资源目录、配置和回传目录。',
]

if (issues.length) {
  readme.push('', '## 问题', '', ...issues.map((item) => `- ${item}`))
}

writeFileSync(join(outDir, 'README.md'), `${readme.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: manifest.passed,
  appResource: manifest.appResource?.path || '',
  storeIcon: manifest.storeIcon?.path || '',
  files: filesForChecksum.length,
  latest: latestManifest.latestPacketDir,
  issues,
}, null, 2))

if (!manifest.passed) process.exit(1)
