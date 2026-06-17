#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.TRY_NOW_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.TRY_NOW_OUT_DIR || join(root, 'artifacts', 'try-now', `${localTimestamp()}-${version}`)
const indexDir = join(root, 'artifacts', 'try-now')

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

function reportTime(path, fullPath = '') {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  if (Number.isFinite(time) && time > 0) return time
  return fullPath && existsSync(fullPath) ? statSync(fullPath).mtimeMs : 0
}

function latestDir(path, filename = 'manifest.json') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byTime = reportTime(b.reportPath, b.full) - reportTime(a.reportPath, a.full)
      return byTime || b.name.localeCompare(a.name)
    })
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function latestReportDir(path, filename = 'report.json') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory() && existsSync(join(root, item.reportPath)))
    .sort((a, b) => {
      const byTime = reportTime(b.reportPath, b.full) - reportTime(a.reportPath, a.full)
      return byTime || b.name.localeCompare(a.name)
    })
  if (!dirs[0]) return null
  return { dir: join(path, dirs[0].name), path: dirs[0].reportPath, data: readJson(dirs[0].reportPath) }
}

function artifactByExt(manifest, ext) {
  return (manifest?.artifacts || []).find((item) => String(item.fileName || item.path || '').endsWith(ext)) || null
}

function latestInboxArtifact(platform, exts) {
  const dir = join(root, 'artifacts', 'release-inbox', version, platform)
  if (!existsSync(dir)) return null
  const files = readdirSync(dir)
    .filter((name) => exts.some((ext) => name.endsWith(ext)))
    .map((name) => {
      const fullPath = join(dir, name)
      return {
        name,
        path: rel(fullPath),
        mtimeMs: statSync(fullPath).mtimeMs,
        bytes: statSync(fullPath).size,
      }
    })
    .sort((a, b) => b.mtimeMs - a.mtimeMs || a.name.localeCompare(b.name))
  return files[0] || null
}

function readManifest(dir) {
  return dir ? readJson(`${dir}/manifest.json`) : null
}

function status(value) {
  return value ? 'ready' : 'missing'
}

function row(label, state, evidence, note = '') {
  return `| ${label} | ${state} | ${evidence ? `\`${evidence}\`` : '-'} | ${note} |`
}

mkdirSync(outDir, { recursive: true })
mkdirSync(indexDir, { recursive: true })

const macDir = latestDir('artifacts/desktop-macos-user-packets')
const macUpdatedAppDir = latestDir('artifacts/desktop-macos-updated-app')
const winDir = latestDir('artifacts/desktop-windows-user-packets')
const mobileResourceDir = latestDir('artifacts/mobile-app-resource-packets')
const mobileApiDir = latestDir('artifacts/mobile-api-evidence')
const desktopDownloadsDir = latestDir('artifacts/desktop-downloads')
const releasePackageReport = latestReportDir('artifacts/release-packages', 'upload-manifest.json')
const releasePackageDir = releasePackageReport?.dir || ''
const desktopSmoke = latestReportDir('artifacts/desktop-smoke')
const desktopOnlineLogin = latestReportDir('artifacts/desktop-online-login-smoke')
const desktopMacosLocalInstall = latestReportDir('artifacts/desktop-macos-local-install')
const desktopMacosLifecycle = latestReportDir('artifacts/desktop-macos-lifecycle')
const h5LegalDeployStatus = latestReportDir('artifacts/h5-legal-deploy-status')
const userActions = latestReportDir('artifacts/release-user-actions')
const androidDebugApk = latestInboxArtifact('android', ['.apk'])
const androidDebugAab = latestInboxArtifact('android', ['.aab'])
const androidBuildMetadata = readJson(`artifacts/release-inbox/${version}/android/build-metadata.json`)

const macManifest = readManifest(macDir)
const macUpdatedAppManifest = readManifest(macUpdatedAppDir)
const winManifest = readManifest(winDir)
const mobileResourceManifest = readManifest(mobileResourceDir)
const mobileApiManifest = readManifest(mobileApiDir)
const downloadsManifest = readManifest(desktopDownloadsDir)
const releaseManifest = releasePackageReport?.data || null

const macDmg = artifactByExt(macManifest, '.dmg')
const macDownloadsAppZip = artifactByExt(downloadsManifest, '.app.zip')
const macUpdatedAppZip = macDownloadsAppZip?.path || macUpdatedAppManifest?.package?.path || latestInboxArtifact('macos', ['.zip'])?.path || ''
const winExe = artifactByExt(winManifest, '.exe')
const desktopLayout = desktopSmoke?.data?.layout?.agent || null
const desktopOnlineChecks = desktopOnlineLogin?.data?.checks || []
const mobileStoreIconPath = typeof mobileResourceManifest?.storeIcon === 'string'
  ? mobileResourceManifest.storeIcon
  : (mobileResourceManifest?.storeIcon?.path || `${mobileResourceDir}/app-icon-1024.png`)

const issues = []
if ((!macManifest?.passed || !macDmg) && !macUpdatedAppZip) issues.push('macOS 个人试用包缺失或未通过')
if (!winManifest?.passed || !winExe) issues.push('Windows 个人试用包缺失或未通过')
if (!mobileResourceManifest?.passed) issues.push('移动端 App 资源交付包缺失或未通过')
if (mobileApiManifest?.passed !== true) issues.push('移动端 API 后端请求证据缺失或未通过')
if (!androidDebugApk) issues.push('Android 调试安装 APK 缺失')
if (!androidDebugAab) issues.push('Android 调试 AAB 缺失')
if (desktopSmoke?.data?.passed !== true || !desktopLayout?.homeAiMain || !desktopLayout?.topnav) issues.push('桌面布局 smoke 缺失或未包含浅色顶栏/底部对话框指标')
if (desktopOnlineLogin?.data?.passed !== true) issues.push('桌面线上登录/积分/agent smoke 缺失或未通过')
if (!releaseManifest) issues.push('Release package upload-manifest 缺失或未写完')

const manifest = {
  generatedAt: new Date().toISOString(),
  version,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  outDir: rel(outDir),
  passed: issues.length === 0,
  tryNow: {
    macosUpdatedAppZip: macUpdatedAppZip || '',
    macosDmg: macDmg?.path || '',
    windowsInstaller: winExe?.path || '',
    androidDebugApk: androidDebugApk?.path || '',
    androidDebugAab: androidDebugAab?.path || '',
    mobileAppResource: mobileResourceDir,
    mobileStoreIcon: mobileStoreIconPath,
    previewPages: {
      macos: macDir ? `${macDir}/preview.html` : '',
      windows: winDir ? `${winDir}/preview.html` : '',
    },
  },
  evidence: {
    macosUserPacket: macDir,
    macosUpdatedApp: macUpdatedAppDir,
    windowsUserPacket: winDir,
    mobileAppResourcePacket: mobileResourceDir,
    mobileApiEvidence: mobileApiDir,
    desktopDownloads: desktopDownloadsDir,
    releasePackage: releasePackageDir,
    desktopSmoke: desktopSmoke?.path || '',
    desktopOnlineLoginSmoke: desktopOnlineLogin?.path || '',
    desktopMacosLocalInstall: desktopMacosLocalInstall?.path || '',
    desktopMacosLifecycle: desktopMacosLifecycle?.path || '',
    h5LegalDeployStatus: h5LegalDeployStatus?.path || '',
    userActions: userActions?.path || '',
    androidBuildMetadata: `artifacts/release-inbox/${version}/android/build-metadata.json`,
  },
  androidDebugApk: androidDebugApk ? {
    path: androidDebugApk.path,
    bytes: androidDebugApk.bytes,
    sha256: androidBuildMetadata?.artifactSha256 || '',
    packageName: androidBuildMetadata?.packageName || '',
    versionName: androidBuildMetadata?.versionName || '',
    versionCode: androidBuildMetadata?.versionCode || '',
    signing: androidBuildMetadata?.codeSigningStatus || '',
    distribution: androidBuildMetadata?.distributionStatus || '',
    startUrl: androidBuildMetadata?.startUrl || '',
  } : null,
  androidDebugAab: androidDebugAab ? {
    path: androidDebugAab.path,
    bytes: androidDebugAab.bytes,
    sha256: (androidBuildMetadata?.secondaryArtifacts || []).find((item) => item.kind === 'aab')?.sha256 || '',
    signing: (androidBuildMetadata?.secondaryArtifacts || []).find((item) => item.kind === 'aab')?.signingStatus || '',
  } : null,
  desktopLayout,
  desktopOnlineChecks,
  downloads: downloadsManifest?.artifacts || [],
  releaseMissingHardBlocks: releaseManifest?.missingHardBlocks || [],
  userMustDoLast: [
    'Apple Developer ID 签名和 notarization。',
    'Windows 代码签名。',
    'Android APK/AAB、iOS TestFlight/IPA、鸿蒙 HAP/AppGallery 包。',
    '明确批准后才能执行生产 H5 法律页部署：CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh。',
    'H5 法律页部署后回填法律 URL 严格验证和商店后台 URL 截图。',
    '开发者账号、商店后台、备案、隐私材料和提交编号截图。',
    '当前批次真实用户真机安装、登录、积分、时安agent、窗口缩放和卸载回收；iOS/鸿蒙后续批次再补。',
  ],
  issues,
}

writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)

const readme = [
  '# 当前可试用包',
  '',
  `> 生成时间：${manifest.generatedAt}`,
  `> 版本：${version}`,
  `> commit：${manifest.commit || '未读取到'}`,
  `> 结果：${manifest.passed ? '通过' : '未通过'}`,
  '',
  '## 现在先用',
  '',
  '| 平台 | 状态 | 入口 | 说明 |',
  '| --- | --- | --- | --- |',
  row('macOS', status(macDmg), macDmg?.path, 'DMG 内部测试包，未签名未公证。'),
  row('macOS 当前已更新 App', status(macUpdatedAppZip), macUpdatedAppZip, '已替换最新 H5/app.asar 并通过安装、生命周期、布局和线上后端 smoke；正式对外仍需重打 DMG。'),
  row('Windows', status(winExe), winExe?.path, 'NSIS 内部测试安装器，未代码签名。'),
  row('Android', status(androidDebugApk), androidDebugApk?.path, 'Debug WebView 壳安装包，连接线上站点和线上 API，只用于真机内部测试；正式上架仍需签名 APK/AAB。'),
  row('Android AAB', status(androidDebugAab), androidDebugAab?.path, 'Debug App Bundle 结构预检包，不是商店正式 AAB。'),
  row('移动端 App 资源', status(mobileResourceManifest?.passed), mobileResourceDir, '给 HBuilderX/DCloud/DevEco 打 Android/iOS/鸿蒙测试包。'),
  row('移动端 1024 图标', status(existsSync(join(root, manifest.tryNow.mobileStoreIcon || ''))), manifest.tryNow.mobileStoreIcon, '移动端和桌面端统一使用你的 logo。'),
  '',
  '## Android 调试安装包',
  '',
  `- APK：\`${manifest.tryNow.androidDebugApk || '缺失'}\``,
  `- AAB：\`${manifest.tryNow.androidDebugAab || '缺失'}\``,
  `- 包名：${manifest.androidDebugApk?.packageName || '缺失'}`,
  `- 版本：${manifest.androidDebugApk?.versionName || '缺失'} / ${manifest.androidDebugApk?.versionCode || '缺失'}`,
  `- APK SHA-256：${manifest.androidDebugApk?.sha256 || '缺失'}`,
  `- AAB SHA-256：${manifest.androidDebugAab?.sha256 || '缺失'}`,
  `- APK 签名状态：${manifest.androidDebugApk?.signing || '缺失'}`,
  `- AAB 签名状态：${manifest.androidDebugAab?.signing || '缺失'}`,
  `- 分发边界：${manifest.androidDebugApk?.distribution || '缺失'}`,
  `- 线上入口：${manifest.androidDebugApk?.startUrl || '缺失'}`,
  '',
  '## 页面预览',
  '',
  `- macOS 预览：\`${manifest.tryNow.previewPages.macos || '缺失'}\``,
  `- Windows 预览：\`${manifest.tryNow.previewPages.windows || '缺失'}\``,
  '',
  '## 已验证的后端能力',
  '',
  `- 桌面线上登录/积分/时安agent smoke：\`${manifest.evidence.desktopOnlineLoginSmoke || '缺失'}\``,
  `- macOS 本机安装记录：\`${manifest.evidence.desktopMacosLocalInstall || '缺失'}\``,
  `- macOS 原生生命周期：\`${manifest.evidence.desktopMacosLifecycle || '缺失'}\``,
  `- macOS 当前已更新 App 包：\`${manifest.tryNow.macosUpdatedAppZip || manifest.evidence.macosUpdatedApp || '缺失'}\``,
  `- 移动端 API 后端请求证据：\`${manifest.evidence.mobileApiEvidence || '缺失'}\``,
  '',
  '## 法律 URL 与生产部署',
  '',
  `- H5 法律页线上状态：\`${manifest.evidence.h5LegalDeployStatus || '缺失'}\``,
  `- 人工事项交接包：\`${manifest.evidence.userActions || '缺失'}\``,
  '- 生产 H5 法律页部署必须等你明确批准后执行：`CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh`',
  '- 部署后还要重新跑法律 URL 严格验证，并保存商店后台 URL 截图。',
  '',
  '| 接口检查 | 状态 |',
  '| --- | --- |',
  ...desktopOnlineChecks.map((item) => `| ${item.name} | ${item.ok ? '通过' : '失败'} ${item.status || ''} |`),
  '',
  '## 桌面布局指标',
  '',
  `- 顶栏高度：${desktopLayout?.topnav?.height ?? '缺失'}px`,
  `- 顶栏颜色：${desktopLayout?.topnav?.backgroundColor || '缺失'}`,
  `- 对话框 top/bottom：${desktopLayout?.homeAiMain?.top ?? '缺失'} / ${desktopLayout?.homeAiMain?.bottom ?? '缺失'}`,
  `- 桌面布局 smoke：\`${manifest.evidence.desktopSmoke || '缺失'}\``,
  '',
  '## 最后必须你做',
  '',
  ...manifest.userMustDoLast.map((item) => `- ${item}`),
  '',
  '## Release 草稿',
  '',
  `- 最新 Release 草稿包：\`${manifest.evidence.releasePackage || '缺失'}\``,
  `- 仍有硬缺口：${manifest.releaseMissingHardBlocks.length} 项`,
]

if (issues.length) {
  readme.push('', '## 问题', '', ...issues.map((item) => `- ${item}`))
}

writeFileSync(join(outDir, 'README.md'), `${readme.join('\n')}\n`)

const latest = {
  generatedAt: new Date().toISOString(),
  latestPacketDir: manifest.outDir,
  readme: `${manifest.outDir}/README.md`,
  manifest: `${manifest.outDir}/manifest.json`,
  macosDmg: manifest.tryNow.macosDmg,
  macosUpdatedAppZip: manifest.tryNow.macosUpdatedAppZip,
  windowsInstaller: manifest.tryNow.windowsInstaller,
  androidDebugApk: manifest.tryNow.androidDebugApk,
  androidDebugAab: manifest.tryNow.androidDebugAab,
  mobileAppResource: manifest.tryNow.mobileAppResource,
  passed: manifest.passed,
}
writeFileSync(join(indexDir, 'latest-manifest.json'), `${JSON.stringify(latest, null, 2)}\n`)
writeFileSync(join(indexDir, 'LATEST.md'), `${[
  '# 最新当前可试用包',
  '',
  `> 更新时间：${latest.generatedAt}`,
  `> 结果：${latest.passed ? '通过' : '未通过'}`,
  '',
  `- README：\`${latest.readme}\``,
  `- manifest：\`${latest.manifest}\``,
  `- macOS DMG：\`${latest.macosDmg || '缺失'}\``,
  `- macOS 当前已更新 App：\`${latest.macosUpdatedAppZip || '缺失'}\``,
  `- Windows 安装器：\`${latest.windowsInstaller || '缺失'}\``,
  `- Android APK：\`${manifest.tryNow.androidDebugApk || '缺失'}\``,
  `- Android AAB：\`${manifest.tryNow.androidDebugAab || '缺失'}\``,
  `- 移动端资源：\`${latest.mobileAppResource || '缺失'}\``,
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: manifest.outDir,
  passed: manifest.passed,
  macosDmg: manifest.tryNow.macosDmg,
  macosUpdatedAppZip: manifest.tryNow.macosUpdatedAppZip,
  windowsInstaller: manifest.tryNow.windowsInstaller,
  androidDebugApk: manifest.tryNow.androidDebugApk,
  androidDebugAab: manifest.tryNow.androidDebugAab,
  mobileAppResource: manifest.tryNow.mobileAppResource,
  issues,
}, null, 2))

if (!manifest.passed) process.exit(1)
