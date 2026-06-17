#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.FINAL_PACKAGE_PLAN_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.FINAL_PACKAGE_PLAN_OUT_DIR || join(root, 'artifacts', 'final-package-plan', `${localTimestamp()}-${version}`)
const strict = process.argv.includes('--strict') || process.env.FINAL_PACKAGE_PLAN_STRICT === '1'
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const activePlatforms = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms.filter((id) => !deferredPlatforms.has(id))
  : ['h5', 'android', 'ios', 'harmony', 'macos', 'windows'].filter((id) => !deferredPlatforms.has(id))

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
    .map((entry) => {
      const fullPath = join(fullParent, entry.name)
      return { name: entry.name, fullPath, reportPath: requiredFile ? `${parent}/${entry.name}/${requiredFile}` : '' }
    })
    .filter((entry) => !requiredFile || existsSync(join(root, entry.reportPath)))
    .sort((a, b) => statSync(b.fullPath).mtimeMs - statSync(a.fullPath).mtimeMs || b.name.localeCompare(a.name))
  return dirs[0] ? `${parent}/${dirs[0].name}` : ''
}

function dirSize(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return 0
  const stat = statSync(fullPath)
  if (stat.isFile()) return stat.size
  let total = 0
  for (const entry of readdirSync(fullPath, { withFileTypes: true })) {
    total += dirSize(join(path, entry.name))
  }
  return total
}

function mb(bytes) {
  return Math.round((bytes / 1024 / 1024) * 10) / 10
}

function existsRel(path) {
  return Boolean(path) && existsSync(join(root, path))
}

function currentFile(label) {
  const file = (currentDownloads?.files || []).find((item) => item.label === label)
  return file && existsRel(file.path) ? file : null
}

function commandStep(id, title, command, phase, reason, requiresUser = false) {
  return { id, title, command, phase, reason, requiresUser }
}

function packageRequired(platformId) {
  return activePlatforms.includes(platformId) && !deferredPlatforms.has(platformId)
}

const latest = {
  currentIndex: latestDir('artifacts/current-index', 'index.json'),
  platformBackendMatrix: latestDir('artifacts/platform-backend-matrix', 'report.json'),
  currentDownloads: existsSync(join(root, 'artifacts', 'current-downloads', 'manifest.json')) ? 'artifacts/current-downloads' : '',
  mobileApiEvidence: latestDir('artifacts/mobile-api-evidence', 'manifest.json'),
  desktopOnlineLoginSmoke: latestDir('artifacts/desktop-online-login-smoke', 'report.json'),
  lowImpactStatus: latestDir('artifacts/low-impact-status', 'report.json'),
}

const currentIndex = latest.currentIndex ? readJson(`${latest.currentIndex}/index.json`) : null
const platformBackendMatrix = latest.platformBackendMatrix ? readJson(`${latest.platformBackendMatrix}/report.json`) : null
const currentDownloads = readJson('artifacts/current-downloads/manifest.json')
const lowImpactStatus = latest.lowImpactStatus ? readJson(`${latest.lowImpactStatus}/report.json`) : null

const currentFiles = {
  macosDmg: currentFile('shian-current-macos-arm64.dmg'),
  macosAppZip: currentFile('shian-current-macos-arm64.app.zip'),
  windowsExe: currentFile('shian-current-windows-x64.exe'),
  androidApk: currentFile('shian-current-android-debug.apk'),
  androidAab: currentFile('shian-current-android-debug.aab'),
  appIcon: currentFile('shian-current-app-icon-1024.png'),
}

const storage = {
  artifactsMB: mb(dirSize('artifacts')),
  distMB: mb(dirSize('dist')),
  desktopReleaseMB: mb(dirSize('desktop/release')),
  desktopNodeModulesMB: mb(dirSize('desktop/node_modules')),
  npmCacheMB: mb(dirSize('.npm-cache')),
}

const missingPackages = [
  packageRequired('macos') && !currentFiles.macosDmg && 'macOS DMG',
  packageRequired('macos') && !currentFiles.macosAppZip && 'macOS App ZIP',
  packageRequired('windows') && !currentFiles.windowsExe && 'Windows EXE',
  packageRequired('android') && !currentFiles.androidApk && 'Android APK',
  packageRequired('android') && !currentFiles.androidAab && 'Android AAB',
  packageRequired('ios') && 'iOS IPA/TestFlight',
  packageRequired('harmony') && '鸿蒙 HAP/AppGallery',
].filter(Boolean)

const scopedBackendPlatforms = (platformBackendMatrix?.platforms || []).filter((platform) => activePlatforms.includes(platform.id))
const backendReady = scopedBackendPlatforms.length > 0
  ? scopedBackendPlatforms.every((platform) => platform.backendReady === true)
  : platformBackendMatrix?.summary?.backendReady === platformBackendMatrix?.summary?.total && platformBackendMatrix?.summary?.total > 0
const mobileRuntimeReady = platformBackendMatrix?.mobileRuntime?.passed === true
const videoSafe = lowImpactStatus?.videoSafe === true
const allFinalCommands = [
  commandStep('low-impact-snapshot', '记录低影响状态快照', 'npm run release:low-impact-status', 'preflight', '只检查发行重负载进程、磁盘空间和固定下载入口；结果只作为风险提示，不阻塞 build-once 阶段。'),
  commandStep('preflight', '先跑非打包门禁', 'npm run release:check', 'preflight', '确认脚本、配置、文档、敏感文件边界仍完整。'),
  commandStep('backend-matrix', '确认当前批次后端请求路径', 'npm run platform:backend-matrix', 'preflight', '确认当前批次线上登录、积分、时安agent 和移动运行时 API 证据仍可读。'),
  commandStep('storage-dry-run', '打包前存储清理预估', 'npm run artifacts:prune -- --keep=2', 'preflight', '只生成可清理候选报告，不删除 current-downloads、release-inbox 或证书资料。'),
  commandStep('package-cleanup-dry-run', '打包前旧安装包清理预估', 'npm run release:package-cleanup-plan -- --keep=2', 'preflight', '只识别旧 APK/AAB/DMG/ZIP/EXE/MSI，不删除 current-downloads、release-inbox 或证书资料。'),
  commandStep('mobile-toolchain-plan', '刷新移动端工具链准备计划', 'npm run mobile:toolchain-plan', 'preflight', '记录 Android/HBuilderX/DCloud 状态，以及 iOS/鸿蒙后续批次工具链状态；不登录账号、不保存证书。'),
  packageRequired('android') && commandStep('mobile-runtime', '刷新移动 App 运行时构建', 'npm run build:app && npm run mobile:api-evidence', 'build-once', '只刷新 dist/build/app，供当前 Android 包和后续移动端包复用。'),
  packageRequired('macos') && commandStep('macos', '完整刷新 macOS App、DMG 和 App ZIP', 'npm run desktop:build:mac:arm64 && npm run desktop:refresh-macos-app-asar && npm run desktop:make-macos-dmg && npm run desktop:bundle && npm run desktop:macos-user-packet', 'build-once', '缺少 `.app` 时也能在最后统一阶段自洽生成 macOS 下载包。'),
  packageRequired('windows') && commandStep('windows', '刷新 Windows 安装器', 'ELECTRON_MIRROR=https://npmmirror.com/mirrors/electron/ npm run desktop:build:win:x64:safe -- --skip-h5 && npm run desktop:windows-user-packet', 'build-once', 'Windows EXE 当前已存在，最后统一重建时优先使用国内 Electron 镜像以减少重复失败。'),
  packageRequired('android') && commandStep('android-debug', '刷新 Android 调试包', 'npm run android:shell:debug-apk', 'build-once', '生成可安装 APK/AAB 调试包，用来先跑真机登录和后端请求。'),
  packageRequired('ios') && commandStep('ios-local-build-attempt', '记录 iOS 本地构建阻塞', 'IOS_LOCAL_BUILD_EXECUTE=1 npm run mobile:ios-local-build-attempt', 'build-once', '先自动记录完整 Xcode、simctl、Apple 签名身份、provisioning profile 和磁盘余量；不保存证书资料。'),
  packageRequired('harmony') && commandStep('harmony-local-pack', '记录鸿蒙本地打包阻塞', 'HBUILDERX_HARMONY_PACK_EXECUTE=1 npm run mobile:hbuilderx-harmony-pack', 'build-once', '先自动记录 HBuilderX pack app-harmony 对 DevEco/hdc/hvigor 的检查结果；不保存签名资料。'),
  (packageRequired('ios') || packageRequired('harmony')) && commandStep('external-mobile', '回传 iOS 与鸿蒙正式包', 'npm run mobile:build-requests && npm run platform:handoff', 'user-last', 'iOS TestFlight/IPA 和鸿蒙 HAP/AppGallery 需要开发者账号、证书或外部构建机回传。', true),
  commandStep('intake', '收件和元数据校验', 'npm run release:intake && npm run release:artifact-metadata', 'evidence', '统一校验当前批次 APK/AAB、DMG、EXE 的 SHA-256 和 build-metadata。'),
  commandStep('device-smoke', '真机安装与核心功能回归', 'npm run android:device-smoke && npm run real-user:dispatch', 'evidence', '当前批次 Android、macOS、Windows、H5 回收登录、积分、时安agent、卸载截图；iOS/鸿蒙后续批次再补。', true),
  commandStep('legal-deploy', 'H5 法律页生产部署', 'CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5', 'user-last', '生产 H5 法律页部署必须等你明确批准。', true),
  commandStep('final-index', '最后生成统一下载入口', 'npm run release:try-now && npm run release:package && npm run release:external-handoff && npm run release:current-index && npm run release:current-downloads', 'final-index', '安装包全部更新后再生成最终 GitHub Release 候选和固定下载入口。'),
]
const finalCommands = allFinalCommands.filter(Boolean)

const deleteCandidates = [
  { path: 'desktop/release', reason: '打包中间目录，可在最终打包前后清理，当前若为 0MB 不需要处理。' },
  { path: 'artifacts/platform-backend-matrix', reason: '矩阵历史报告可保留最新 1-2 份。' },
  { path: 'artifacts/mobile-api-evidence', reason: '移动 API 历史证据可保留最新 1-2 份。' },
  { path: 'artifacts/current-downloads', reason: '固定下载入口不要提前删除；最终包刷新完成后由 release:current-downloads 覆盖。' },
  { path: '.npm-cache', reason: '临时 npm cache，可在桌面依赖恢复完成后删除；若要避免重复联网，可暂时保留。' },
].map((item) => ({ ...item, exists: existsRel(item.path), sizeMB: mb(dirSize(item.path)) }))

const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  readyToRunFinalPackageRefresh: backendReady && mobileRuntimeReady,
  releaseScope: {
    configPath: 'configs/release/current-release-scope.json',
    currentBatch: releaseScope.currentBatch || '',
    activePlatforms,
    deferredPlatforms: [...deferredPlatforms],
  },
  videoSafe,
  lowImpactStatus: latest.lowImpactStatus,
  backendReady,
  mobileRuntimeReady,
  latest,
  storage,
  currentFiles,
  missingPackages,
  finalCommands,
  deleteCandidates,
  userMustDoLast: finalCommands.filter((item) => item.requiresUser).map((item) => ({
    id: item.id,
    title: item.title,
    command: item.command,
    reason: item.reason,
  })),
  currentIndexPassed: currentIndex?.passed === true,
  currentDownloadsPassed: currentDownloads?.passed === true,
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# 最终安装包刷新计划',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.readyToRunFinalPackageRefresh ? '可以进入最后统一刷新安装包阶段，但仍有用户/外部动作。' : '还不应开始最终打包。'}`,
  `> 当前批次：${releaseScope.currentBatch || '未配置'}；延期平台：${[...deferredPlatforms].join('、') || '无'}`,
  '',
  '## 当前状态',
  '',
  `- 后端请求证据：${backendReady ? `${activePlatforms.length}/${activePlatforms.length} 可用` : '不足'}`,
  `- 移动运行时证据：${mobileRuntimeReady ? '通过' : '缺失'}`,
  `- 低影响状态快照：${videoSafe ? '通过' : '未通过或缺失'}${latest.lowImpactStatus ? `（${latest.lowImpactStatus}）` : ''}；仅提示风险，不阻塞最终打包计划。`,
  `- 当前索引：${report.currentIndexPassed ? '通过' : '存在缺口'}`,
  `- 固定下载入口：${report.currentDownloadsPassed ? '通过' : '存在缺口'}`,
  `- 存储占用：artifacts ${storage.artifactsMB}MB；dist ${storage.distMB}MB；desktop/release ${storage.desktopReleaseMB}MB；desktop/node_modules ${storage.desktopNodeModulesMB}MB；.npm-cache ${storage.npmCacheMB}MB。`,
  '',
  '## 缺少的安装包/发行件',
  '',
  ...(missingPackages.length ? missingPackages.map((item) => `- ${item}`) : ['- 无。']),
  ...(deferredPlatforms.size ? ['', '延期平台本轮不作为缺包阻塞：', ...[...deferredPlatforms].map((id) => `- \`${id}\``)] : []),
  '',
  '## 最后统一执行队列',
  '',
  '| 阶段 | 步骤 | 命令 | 说明 |',
  '| --- | --- | --- | --- |',
  ...finalCommands.map((item) => `| ${item.phase} | ${item.title}${item.requiresUser ? '（需你/外部处理）' : ''} | \`${item.command}\` | ${item.reason} |`),
  '',
  '## 存储策略',
  '',
  ...deleteCandidates.map((item) => `- \`${item.path}\`：${item.exists ? `${item.sizeMB}MB` : '不存在'}；${item.reason}`),
  '',
  '## 最后必须你或外部处理',
  '',
  ...report.userMustDoLast.map((item) => `- ${item.title}：\`${item.command}\`。${item.reason}`),
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  readyToRunFinalPackageRefresh: report.readyToRunFinalPackageRefresh,
  missingPackages,
  storage,
  userMustDoLast: report.userMustDoLast.length,
}, null, 2))

if (strict && !report.readyToRunFinalPackageRefresh) process.exit(1)
