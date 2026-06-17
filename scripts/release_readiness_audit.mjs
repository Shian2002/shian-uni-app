#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { existsSync, lstatSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { basename, extname, join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.RELEASE_READINESS_STRICT === '1'
const stamp = new Date().toISOString().replace(/[:.]/g, '-')
const outDir = process.env.RELEASE_READINESS_OUT_DIR || join(root, 'artifacts', 'release-readiness')
const jsonOut = join(outDir, `${stamp}.json`)
const mdOut = join(outDir, `${stamp}.md`)

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function exists(path) {
  return existsSync(join(root, path))
}

function readText(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  return readFileSync(fullPath, 'utf8')
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

function walkFiles(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return []
  const entries = []
  let names = []
  try {
    names = readdirSync(fullPath)
  } catch (err) {
    if (err && err.code === 'ENOENT') return []
    throw err
  }
  for (const name of names) {
    const item = join(fullPath, name)
    let stat
    try {
      stat = lstatSync(item)
    } catch (err) {
      if (err && err.code === 'ENOENT') continue
      throw err
    }
    if (stat.isSymbolicLink()) entries.push({ path: rel(item), bytes: 0, mtimeMs: stat.mtimeMs })
    else if (stat.isDirectory()) entries.push(...walkFiles(rel(item)))
    else entries.push({ path: rel(item), bytes: stat.size, mtimeMs: stat.mtimeMs })
  }
  return entries
}

function latestDir(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  return readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byTime = latestEntryTime(b, path) - latestEntryTime(a, path)
      return byTime || b.name.localeCompare(a.name)
    })[0]?.name
}

function latestEntryTime(entry, basePath) {
  const reportTimeValue = Math.max(
    reportTime(join(basePath, entry.name, 'report.json')),
    reportTime(join(basePath, entry.name, 'summary.json')),
    reportTime(join(basePath, entry.name, 'upload-manifest.json'))
  )
  return reportTimeValue || statSync(entry.full).mtimeMs || 0
}

function latestPassingReport(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, 'report.json') }))
    .filter((item) => exists(item.reportPath))
    .sort((a, b) => {
      const byReportTime = reportTime(b.reportPath) - reportTime(a.reportPath)
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const item of dirs) {
    const data = readJson(item.reportPath)
    if (data?.passed === true) return { path: item.reportPath, data }
  }
  return dirs[0] ? { path: dirs[0].reportPath, data: readJson(dirs[0].reportPath) } : null
}

function latestPassingJson(path, filename) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => exists(item.reportPath))
    .sort((a, b) => {
      const byReportTime = reportTime(b.reportPath) - reportTime(a.reportPath)
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const item of dirs) {
    const data = readJson(item.reportPath)
    if (data?.passed === true) return { path: item.reportPath, data }
  }
  return dirs[0] ? { path: dirs[0].reportPath, data: readJson(dirs[0].reportPath) } : null
}

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function latestJsonFile(path, suffix = '.json') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const files = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name) }))
    .filter((item) => statSync(item.full).isFile() && item.name.endsWith(suffix))
    .sort((a, b) => b.name.localeCompare(a.name))
  for (const item of files) {
    const data = readJson(item.reportPath)
    if (data?.passed === true) return { path: item.reportPath, data }
  }
  return files[0] ? { path: files[0].reportPath, data: readJson(files[0].reportPath) } : null
}

function filesByExt(paths, exts) {
  return paths.flatMap(walkFiles).filter((item) => exts.includes(extname(item.path).toLowerCase()))
}

function isUnpackedDesktopInternal(path) {
  return /desktop\/release\/(?:win|mac)[^/]*-unpacked\//i.test(path) ||
    /desktop\/release\/win-(?:arm64-)?unpacked\//i.test(path)
}

function isRedundantUserPacketBinary(path) {
  return /^artifacts\/desktop-macos-user-packets\/.+\.app\.zip$/i.test(path)
}

function artifactPriority(path) {
  if (path.startsWith('artifacts/desktop-downloads/')) return 0
  if (path.startsWith('artifacts/release-inbox/')) return 1
  if (path.startsWith('artifacts/desktop-macos-user-packets/')) return 2
  if (path.startsWith('artifacts/desktop-windows-user-packets/')) return 2
  if (path.startsWith('desktop/release/')) return 3
  return 4
}

function uniqueByHash(items) {
  const byHash = new Map()
  for (const item of items) {
    const key = `${item.bytes}:${sha256(join(root, item.path))}`
    const existing = byHash.get(key)
    if (!existing || artifactPriority(item.path) < artifactPriority(existing.path)) {
      byHash.set(key, item)
    }
  }
  return [...byHash.values()].sort((a, b) => artifactPriority(a.path) - artifactPriority(b.path) || a.path.localeCompare(b.path))
}

function binaryEvidence(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const stat = statSync(fullPath)
  return { path, bytes: stat.size, sha256: sha256(fullPath) }
}

function item(id, title, status, evidence = [], missing = [], next = []) {
  return { id, title, status, evidence: evidence.filter(Boolean), missing: missing.filter(Boolean), next: next.filter(Boolean) }
}

function statusFrom(hasReady, hasPartial) {
  if (hasReady) return 'ready'
  if (hasPartial) return 'partial'
  return 'missing'
}

const packageJson = readJson('package.json') || {}
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const userQa = latestPassingReport('artifacts/user-acceptance')
const loginSmoke = latestPassingReport('artifacts/login-smoke')
const agentStreamSmoke = latestPassingReport('artifacts/agent-stream-smoke')
const desktopSmoke = latestPassingReport('artifacts/desktop-smoke')
const storeScreenshots = latestPassingJson('artifacts/store-screenshots', 'summary.json')
const realUserAcceptance = latestJsonFile('artifacts/real-user-results', '.json')
const realUserPacketName = latestDir('artifacts/real-user-packets')
const realUserPacket = realUserPacketName ? `artifacts/real-user-packets/${realUserPacketName}` : ''
const realUserRosterName = latestDir('artifacts/real-user-roster')
const realUserRoster = realUserRosterName ? `artifacts/real-user-roster/${realUserRosterName}` : ''
const realUserDispatchName = latestDir('artifacts/real-user-dispatch')
const realUserDispatch = realUserDispatchName ? `artifacts/real-user-dispatch/${realUserDispatchName}` : ''
const releasePackageName = latestDir('artifacts/release-packages')
const releasePackage = releasePackageName ? `artifacts/release-packages/${releasePackageName}` : ''
const desktopDownloadsName = latestDir('artifacts/desktop-downloads')
const desktopDownloads = desktopDownloadsName ? `artifacts/desktop-downloads/${desktopDownloadsName}` : ''
const storeSubmissionPacketName = latestDir('artifacts/store-submission-packets')
const storeSubmissionPacket = storeSubmissionPacketName ? `artifacts/store-submission-packets/${storeSubmissionPacketName}` : ''
const legalUrlCheckName = latestDir('artifacts/legal-url-checks')
const legalUrlCheck = legalUrlCheckName ? `artifacts/legal-url-checks/${legalUrlCheckName}` : ''
const privacyDisclosureName = latestDir('artifacts/privacy-disclosures')
const privacyDisclosure = privacyDisclosureName ? `artifacts/privacy-disclosures/${privacyDisclosureName}` : ''
const storeMaterialsName = latestDir('artifacts/store-materials')
const storeMaterials = storeMaterialsName ? `artifacts/store-materials/${storeMaterialsName}` : ''
const storeSubmissionStatusName = latestDir('artifacts/store-submission-status')
const storeSubmissionStatus = storeSubmissionStatusName ? `artifacts/store-submission-status/${storeSubmissionStatusName}` : ''
const storeEvidenceStatusName = latestDir('artifacts/store-evidence-status')
const storeEvidenceStatus = storeEvidenceStatusName ? `artifacts/store-evidence-status/${storeEvidenceStatusName}` : ''
const storeAccountAccessName = latestDir('artifacts/store-account-access')
const storeAccountAccess = storeAccountAccessName ? `artifacts/store-account-access/${storeAccountAccessName}` : ''
const appRecordStatusName = latestDir('artifacts/app-record-status')
const appRecordStatus = appRecordStatusName ? `artifacts/app-record-status/${appRecordStatusName}` : ''
const domainHttpsName = latestDir('artifacts/domain-https')
const domainHttps = domainHttpsName ? `artifacts/domain-https/${domainHttpsName}` : ''
const h5LegalDeployStatusName = latestDir('artifacts/h5-legal-deploy-status')
const h5LegalDeployStatus = h5LegalDeployStatusName ? `artifacts/h5-legal-deploy-status/${h5LegalDeployStatusName}` : ''
const desktopReleaseStatusName = latestDir('artifacts/desktop-release-status')
const desktopReleaseStatus = desktopReleaseStatusName ? `artifacts/desktop-release-status/${desktopReleaseStatusName}` : ''
const desktopMacosInstallName = latestDir('artifacts/desktop-macos-install')
const desktopMacosInstall = desktopMacosInstallName ? `artifacts/desktop-macos-install/${desktopMacosInstallName}` : ''
const desktopMacosLocalInstallName = latestDir('artifacts/desktop-macos-local-install')
const desktopMacosLocalInstall = desktopMacosLocalInstallName ? `artifacts/desktop-macos-local-install/${desktopMacosLocalInstallName}` : ''
const desktopMacosLifecycleName = latestDir('artifacts/desktop-macos-lifecycle')
const desktopMacosLifecycle = desktopMacosLifecycleName ? `artifacts/desktop-macos-lifecycle/${desktopMacosLifecycleName}` : ''
const desktopMacosUserPacketName = latestDir('artifacts/desktop-macos-user-packets')
const desktopMacosUserPacket = desktopMacosUserPacketName ? `artifacts/desktop-macos-user-packets/${desktopMacosUserPacketName}` : ''
const desktopWindowsUserPacketName = latestDir('artifacts/desktop-windows-user-packets')
const desktopWindowsUserPacket = desktopWindowsUserPacketName ? `artifacts/desktop-windows-user-packets/${desktopWindowsUserPacketName}` : ''
const desktopWindowsRebuildName = latestDir('artifacts/desktop-windows-rebuild')
const desktopWindowsRebuild = desktopWindowsRebuildName ? `artifacts/desktop-windows-rebuild/${desktopWindowsRebuildName}` : ''
const appIconsName = latestDir('artifacts/app-icons')
const appIcons = appIconsName ? `artifacts/app-icons/${appIconsName}` : ''
const channelBuildsName = latestDir('artifacts/release-channel-builds')
const channelBuilds = channelBuildsName ? `artifacts/release-channel-builds/${channelBuildsName}` : ''
const mobileBuildEnvName = latestDir('artifacts/mobile-build-env')
const mobileBuildEnv = mobileBuildEnvName ? `artifacts/mobile-build-env/${mobileBuildEnvName}` : ''
const mobileBuildRequestsName = latestDir('artifacts/mobile-build-requests')
const mobileBuildRequests = mobileBuildRequestsName ? `artifacts/mobile-build-requests/${mobileBuildRequestsName}` : ''
const mobileApiEvidenceName = latestDir('artifacts/mobile-api-evidence')
const mobileApiEvidence = mobileApiEvidenceName ? `artifacts/mobile-api-evidence/${mobileApiEvidenceName}` : ''
const mobileAppResourcePacketName = latestDir('artifacts/mobile-app-resource-packets')
const mobileAppResourcePacket = mobileAppResourcePacketName ? `artifacts/mobile-app-resource-packets/${mobileAppResourcePacketName}` : ''
const hbuilderxMobileResourcesName = latestDir('artifacts/hbuilderx-mobile-resources')
const hbuilderxMobileResources = hbuilderxMobileResourcesName ? `artifacts/hbuilderx-mobile-resources/${hbuilderxMobileResourcesName}` : ''
const platformHandoffName = latestDir('artifacts/platform-build-handoffs')
const platformHandoff = platformHandoffName ? `artifacts/platform-build-handoffs/${platformHandoffName}` : ''
const artifactIntakeName = latestDir('artifacts/release-artifact-intake')
const artifactIntake = artifactIntakeName ? `artifacts/release-artifact-intake/${artifactIntakeName}` : ''
const artifactMetadataName = latestDir('artifacts/release-artifact-metadata')
const artifactMetadata = artifactMetadataName ? `artifacts/release-artifact-metadata/${artifactMetadataName}` : ''
const latestDesktopBinaryRoots = [
  desktopDownloads,
  desktopMacosUserPacket,
  desktopWindowsUserPacket,
  'artifacts/release-inbox/v1.0.0',
  'desktop/release',
].filter(Boolean)
const androidPackages = filesByExt(['artifacts', 'dist', 'desktop/release'], ['.apk', '.aab'])
const iosPackages = filesByExt(['artifacts', 'dist', 'desktop/release'], ['.ipa'])
const harmonyPackages = filesByExt(['artifacts', 'dist', 'desktop/release'], ['.hap', '.app'])
const windowsPackages = uniqueByHash(filesByExt(latestDesktopBinaryRoots, ['.exe', '.msi']).filter((entry) => !isUnpackedDesktopInternal(entry.path)))
const macPackages = uniqueByHash(filesByExt(latestDesktopBinaryRoots, ['.dmg', '.zip']).filter((entry) => /mac|arm64|x64|时安解忧屋/i.test(entry.path) && !isUnpackedDesktopInternal(entry.path) && !isRedundantUserPacketBinary(entry.path)))
const latestReadinessJson = ''
const appRecordStatusReport = appRecordStatus ? readJson(`${appRecordStatus}/report.json`) : null
const h5LegalDeployStatusReport = h5LegalDeployStatus ? readJson(`${h5LegalDeployStatus}/report.json`) : null

const loginSource = readText('src/components/TopNav.vue')
const profileSource = readText('src/pages/profile/index.vue')
const authSource = readText('backend/auth_routes.py')
const productDoc = readText('docs/release/product-gtm-benchmark.md')
const productStrategySkillDoc = readText('docs/release/product-strategy-skill-report.md')
const reviewLog = readText('docs/release/review-log.md')
const stagingDoc = readText('docs/staging-workflow.md')
const appResourceEntry = exists('dist/build/app/__uniappview.html')
  ? 'dist/build/app/__uniappview.html'
  : (exists('dist/build/app/index.html') ? 'dist/build/app/index.html' : '')
const appResourceRuntime = exists('dist/build/app/app-service.js') ? 'dist/build/app/app-service.js' : ''
const appResourceBuilt = Boolean(appResourceEntry && appResourceRuntime)

const checks = [
  item(
    'gates.scaffold',
    '发行门禁脚本与仓库骨架',
    ['lint', 'typecheck', 'test', 'build:h5', 'build:app', 'build:h5:appstore', 'build:h5:google-play', 'mobile:preflight', 'mobile:build-env', 'mobile:build-requests', 'mobile:api-evidence', 'mobile:app-resource-packet', 'mobile:hbuilderx-resources', 'release:check', 'release:manifest', 'release:intake', 'release:artifact-metadata', 'release:payment-boundary', 'release:channel-builds', 'release:app-icons', 'release:package', 'release:user-actions', 'release:try-now', 'release:current-index', 'release:current-downloads', 'release:summary', 'real-user:packet', 'real-user:roster', 'real-user:dispatch', 'store:packet', 'store:materials', 'store:legal-urls', 'store:privacy', 'store:submission-status', 'store:evidence-status', 'store:account-access', 'store:app-record', 'domain:https', 'h5:legal-deploy-status', 'desktop:signing-preflight', 'desktop:release-status', 'desktop:bundle', 'desktop:verify-macos', 'desktop:macos-user-packet', 'desktop:build:win:x64:safe', 'desktop:windows-user-packet', 'android:shell:debug-apk', 'android:device-smoke', 'platform:handoff', 'qa:agent:local', 'qa:login:local-online', 'qa:agent:stream-smoke'].every((script) => packageJson.scripts?.[script]) ? 'ready' : 'partial',
    [
      'package.json 发行脚本已配置',
      exists('.github/ISSUE_TEMPLATE/platform-bug.yml') && '.github/ISSUE_TEMPLATE/platform-bug.yml',
      exists('.github/ISSUE_TEMPLATE/store-review.yml') && '.github/ISSUE_TEMPLATE/store-review.yml',
      exists('.github/release-template.md') && '.github/release-template.md',
      exists('configs/release/android-channels.json') && 'configs/release/android-channels.json',
      channelBuilds && `${channelBuilds}/report.json`,
      mobileBuildEnv && `${mobileBuildEnv}/report.json`,
      mobileBuildRequests && `${mobileBuildRequests}/manifest.json`,
      mobileApiEvidence && `${mobileApiEvidence}/manifest.json`,
      mobileAppResourcePacket && `${mobileAppResourcePacket}/manifest.json`,
      hbuilderxMobileResources && `${hbuilderxMobileResources}/report.json`,
      exists('docs/release/platform-build-handoff.md') && 'docs/release/platform-build-handoff.md',
      exists('docs/release/artifact-intake.md') && 'docs/release/artifact-intake.md',
      exists('scripts/release_artifact_metadata_check.mjs') && 'scripts/release_artifact_metadata_check.mjs',
      exists('scripts/mobile_api_evidence_check.mjs') && 'scripts/mobile_api_evidence_check.mjs',
      exists('scripts/mobile_app_resource_packet.mjs') && 'scripts/mobile_app_resource_packet.mjs',
      exists('scripts/hbuilderx_mobile_resources.mjs') && 'scripts/hbuilderx_mobile_resources.mjs',
      exists('scripts/store_materials_check.mjs') && 'scripts/store_materials_check.mjs',
      exists('scripts/legal_url_check.mjs') && 'scripts/legal_url_check.mjs',
      exists('scripts/privacy_disclosure_check.mjs') && 'scripts/privacy_disclosure_check.mjs',
      exists('scripts/real_user_roster_check.mjs') && 'scripts/real_user_roster_check.mjs',
      exists('scripts/store_evidence_status_check.mjs') && 'scripts/store_evidence_status_check.mjs',
      exists('scripts/store_account_access_check.mjs') && 'scripts/store_account_access_check.mjs',
      exists('scripts/domain_https_check.mjs') && 'scripts/domain_https_check.mjs',
      exists('scripts/desktop_release_status_check.mjs') && 'scripts/desktop_release_status_check.mjs',
      exists('scripts/desktop_macos_install_verify.mjs') && 'scripts/desktop_macos_install_verify.mjs',
      exists('scripts/desktop_macos_user_packet.mjs') && 'scripts/desktop_macos_user_packet.mjs',
      exists('scripts/desktop_windows_user_packet.mjs') && 'scripts/desktop_windows_user_packet.mjs',
      exists('scripts/app_icon_asset_check.mjs') && 'scripts/app_icon_asset_check.mjs',
      exists('scripts/agent_stream_smoke.mjs') && 'scripts/agent_stream_smoke.mjs',
    ],
    [
      !packageJson.scripts?.['release:readiness'] && 'package.json 缺少 release:readiness',
    ],
    ['正式放行时使用 npm run release:readiness -- --strict']
  ),
  item(
    'assets.app-icons',
    '全端 App 图标资产',
    appIcons && readJson(`${appIcons}/report.json`)?.passed === true ? 'ready' : (exists('configs/release/app-icons.json') ? 'partial' : 'missing'),
    [
      exists('configs/release/app-icons.json') && 'configs/release/app-icons.json',
      exists('src/static/images/logo.png') && 'src/static/images/logo.png',
      exists('src/static/app-icons/app-icon-1024.png') && 'src/static/app-icons/app-icon-1024.png',
      exists('desktop/assets/icon.icns') && 'desktop/assets/icon.icns',
      exists('desktop/assets/icon.ico') && 'desktop/assets/icon.ico',
      appIcons && `${appIcons}/report.json`,
    ],
    [
      !exists('configs/release/app-icons.json') && '缺少 App 图标配置',
      !exists('src/static/app-icons/app-icon-1024.png') && '缺少 1024x1024 商店母图',
      (!appIcons || readJson(`${appIcons}/report.json`)?.passed !== true) && '缺少通过的 release:app-icons 图标资产报告',
    ],
    ['移动端和桌面端都使用同一个 logo；HBuilderX/DCloud/Xcode/DevEco 打包时优先使用 src/static/app-icons/app-icon-1024.png']
  ),
  item(
    'platform.h5',
    'H5 构建与本地验收',
    statusFrom(exists('dist/build/h5/index.html') && userQa?.data?.passed === true, exists('dist/build/h5/index.html') || userQa),
    [
      exists('dist/build/h5/index.html') && 'dist/build/h5/index.html',
      userQa?.data?.passed === true && userQa.path,
    ],
    [
      !exists('dist/build/h5/index.html') && '缺少 dist/build/h5/index.html',
      userQa?.data?.passed !== true && '缺少通过的 artifacts/user-acceptance/*/report.json',
    ],
    ['继续补 staging/online QA 证据，不能只靠本地 H5']
  ),
  item(
    'platform.app-resources',
    'uni-app App 资源构建',
    appResourceBuilt && mobileApiEvidence && readJson(`${mobileApiEvidence}/manifest.json`)?.passed === true && mobileAppResourcePacket && readJson(`${mobileAppResourcePacket}/manifest.json`)?.passed === true ? 'ready' : statusFrom(false, appResourceBuilt || mobileApiEvidence || mobileAppResourcePacket),
    [
      appResourceEntry,
      appResourceRuntime,
      mobileApiEvidence && `${mobileApiEvidence}/manifest.json`,
      mobileAppResourcePacket && `${mobileAppResourcePacket}/manifest.json`,
    ],
    [
      !appResourceEntry && '缺少 dist/build/app/__uniappview.html',
      !appResourceRuntime && '缺少 dist/build/app/app-service.js',
      (!mobileApiEvidence || readJson(`${mobileApiEvidence}/manifest.json`)?.passed !== true) && '缺少通过的移动端 API 后端请求证据',
      (!mobileAppResourcePacket || readJson(`${mobileAppResourcePacket}/manifest.json`)?.passed !== true) && '缺少通过的移动端 App 资源交付包',
    ],
    ['每次生成安装包前运行 MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight']
  ),
  item(
    'platform.android',
    'Android APK/AAB 上架包',
    androidPackages.length ? 'partial' : 'missing',
    [
      artifactIntake && `${artifactIntake}/report.json`,
      artifactMetadata && `${artifactMetadata}/report.json`,
      channelBuilds && `${channelBuilds}/report.json`,
      mobileBuildEnv && `${mobileBuildEnv}/report.json`,
      mobileBuildRequests && `${mobileBuildRequests}/android.md`,
      ...androidPackages.map((entry) => `${entry.path} sha256=${sha256(join(root, entry.path))}`),
    ],
    [
      androidPackages.length === 0 && '缺少 APK/AAB 文件',
      !artifactMetadata && '缺少发行产物元数据报告',
      '缺少应用宝、华为、小米、OPPO、vivo 真机截图和渠道记录',
    ],
    ['用同一 Android/Harmony 代码生成渠道包，不为每个市场拆仓']
  ),
  item(
    'platform.ios',
    'iOS TestFlight/App Store',
    deferredPlatforms.has('ios') ? 'partial' : (iosPackages.length ? 'partial' : 'missing'),
    [
      deferredPlatforms.has('ios') && 'configs/release/current-release-scope.json 已将 iOS 延期到后续批次',
      artifactIntake && `${artifactIntake}/report.json`,
      artifactMetadata && `${artifactMetadata}/report.json`,
      channelBuilds && `${channelBuilds}/report.json`,
      mobileBuildEnv && `${mobileBuildEnv}/report.json`,
      mobileBuildRequests && `${mobileBuildRequests}/ios.md`,
      ...iosPackages.map((entry) => `${entry.path} sha256=${sha256(join(root, entry.path))}`),
    ],
    [
      !deferredPlatforms.has('ios') && iosPackages.length === 0 && '缺少 IPA/TestFlight 构建记录',
      !deferredPlatforms.has('ios') && !artifactMetadata && '缺少发行产物元数据报告',
      !deferredPlatforms.has('ios') && '缺少 iPhone/iPad 截图、审核账号、App Privacy 截图',
      !deferredPlatforms.has('ios') && '未证明 iOS 外部支付/IAP 边界已按审核策略处理',
    ],
    [deferredPlatforms.has('ios') ? '本批次不处理 iOS；后续恢复时再补 Xcode、TestFlight 和 iOS 支付边界。' : '未接入 IAP 前，iOS 包必须隐藏或隔离违规外部充值入口']
  ),
  item(
    'platform.harmony',
    '鸿蒙/AppGallery 测试包',
    deferredPlatforms.has('harmony') ? 'partial' : (harmonyPackages.length ? 'partial' : 'missing'),
    [
      deferredPlatforms.has('harmony') && 'configs/release/current-release-scope.json 已将鸿蒙延期到后续批次',
      artifactIntake && `${artifactIntake}/report.json`,
      artifactMetadata && `${artifactMetadata}/report.json`,
      mobileBuildEnv && `${mobileBuildEnv}/report.json`,
      mobileBuildRequests && `${mobileBuildRequests}/harmony.md`,
      ...harmonyPackages.map((entry) => `${entry.path} sha256=${sha256(join(root, entry.path))}`),
    ],
    [
      !deferredPlatforms.has('harmony') && harmonyPackages.length === 0 && '缺少鸿蒙 HAP/AppGallery 包',
      !deferredPlatforms.has('harmony') && !artifactMetadata && '缺少发行产物元数据报告',
      !deferredPlatforms.has('harmony') && '缺少手机和平板截图、权限触发说明、华为后台状态',
    ],
    [deferredPlatforms.has('harmony') ? '本批次不处理鸿蒙；后续恢复时再补 DevEco/鸿蒙包和华为后台证据。' : '如果鸿蒙原生工程脱离 uni-app 配置，再考虑拆 shian-harmony-shell']
  ),
  item(
    'platform.macos',
    'macOS 桌面下载包',
    macPackages.length && desktopSmoke?.data?.passed === true ? 'partial' : statusFrom(false, macPackages.length || desktopSmoke),
    [
      artifactIntake && `${artifactIntake}/report.json`,
      artifactMetadata && `${artifactMetadata}/report.json`,
      desktopReleaseStatus && `${desktopReleaseStatus}/report.json`,
      desktopMacosInstall && `${desktopMacosInstall}/report.json`,
      desktopMacosLocalInstall && `${desktopMacosLocalInstall}/report.json`,
      desktopMacosLifecycle && `${desktopMacosLifecycle}/report.json`,
      desktopMacosUserPacket && `${desktopMacosUserPacket}/manifest.json`,
      ...macPackages.map((entry) => `${entry.path} sha256=${sha256(join(root, entry.path))}`),
      desktopSmoke?.data?.passed === true && desktopSmoke.path,
    ],
    [
      macPackages.length === 0 && '缺少 DMG/ZIP',
      !artifactMetadata && '缺少发行产物元数据报告',
      !desktopReleaseStatus && '缺少桌面端发布状态报告',
      (!desktopMacosInstall || readJson(`${desktopMacosInstall}/report.json`)?.passed !== true) && '缺少通过的 macOS DMG 只读挂载安装包校验报告',
      (!desktopMacosLocalInstall || readJson(`${desktopMacosLocalInstall}/report.json`)?.passed !== true) && '缺少通过的 /Applications macOS 本机安装报告',
      (!desktopMacosLifecycle || readJson(`${desktopMacosLifecycle}/report.json`)?.passed !== true) && '缺少通过的 macOS 原生生命周期检查报告',
      (!desktopMacosUserPacket || readJson(`${desktopMacosUserPacket}/manifest.json`)?.passed !== true) && '缺少 macOS 个人试用交付包',
      desktopSmoke?.data?.passed !== true && '缺少桌面 smoke 通过报告',
      '缺少 Apple Developer ID 签名和 notarization 证据',
    ],
    ['第一版可以走 GitHub Releases 下载，但正式对外前要补签名说明']
  ),
  item(
    'platform.windows',
    'Windows 桌面下载包',
    windowsPackages.length ? 'partial' : 'missing',
    [
      artifactIntake && `${artifactIntake}/report.json`,
      artifactMetadata && `${artifactMetadata}/report.json`,
      desktopReleaseStatus && `${desktopReleaseStatus}/report.json`,
      desktopWindowsRebuild && `${desktopWindowsRebuild}/report.json`,
      desktopWindowsUserPacket && `${desktopWindowsUserPacket}/manifest.json`,
      ...windowsPackages.map((entry) => `${entry.path} sha256=${sha256(join(root, entry.path))}`),
    ],
    [
      windowsPackages.length === 0 && '缺少 EXE/MSI/NSIS 安装包',
      !artifactMetadata && '缺少发行产物元数据报告',
      !desktopReleaseStatus && '缺少桌面端发布状态报告',
      (!desktopWindowsRebuild || readJson(`${desktopWindowsRebuild}/report.json`)?.passed !== true) && '缺少通过的 Windows x64 安全重建/新鲜度校验报告',
      (!desktopWindowsUserPacket || readJson(`${desktopWindowsUserPacket}/manifest.json`)?.passed !== true) && '缺少 Windows 个人试用交付包',
      '缺少安装、开始菜单、卸载、窗口缩放截图',
    ],
    ['使用当前 NSIS 测试包在 Windows 10/11 真机回收安装、开始菜单、卸载和窗口缩放截图；正式公开前补代码签名']
  ),
  item(
    'flow.login',
    '线上同款登录入口与时安 agent',
    loginSource.includes('/api/login') &&
      loginSource.includes('/api/register') &&
      loginSource.includes('/api/email/login') &&
      loginSource.includes('/api/sms/login') &&
      loginSource.includes('/api/oauth/') &&
      loginSource.includes('Gitee 验证登录') &&
      loginSmoke?.data?.passed === true ? 'ready' : 'partial',
    [
      'src/components/TopNav.vue 复用 /api/login、/api/register、/api/email/login、/api/sms/login、/api/oauth/*/url',
      loginSmoke?.data?.passed === true && loginSmoke.path,
      userQa?.data?.passed === true && userQa.path,
    ],
    [
      !loginSource.includes('/api/sms/login') && '本地壳缺少短信验证码登录分支',
      !loginSource.includes('Gitee 验证登录') && '旧 Gitee 验证入口缺失',
      loginSmoke?.data?.passed !== true && '缺少通过的 artifacts/login-smoke/*/report.json',
    ],
    ['本地线上登录 smoke 只证明 /api/login 和 /api/me；staging 真机继续验证短信/邮件隔离、Gitee 未配置提示和积分充足账号的 Agent 请求']
  ),
  item(
    'flow.agent-stream',
    '真实 Agent stream 后端请求',
    agentStreamSmoke?.data?.passed === true ? 'ready' : 'missing',
    [
      agentStreamSmoke?.data?.passed === true && agentStreamSmoke.path,
      agentStreamSmoke?.data?.streamSummary?.conversationId && `conversation_id=${agentStreamSmoke.data.streamSummary.conversationId}`,
      agentStreamSmoke?.data?.streamSummary?.eventCount && `event_count=${agentStreamSmoke.data.streamSummary.eventCount}`,
      agentStreamSmoke?.data?.streamSummary?.usedCredit && `used_credit=${agentStreamSmoke.data.streamSummary.usedCredit}`,
    ],
    [
      agentStreamSmoke?.data?.passed !== true && '缺少通过的 artifacts/agent-stream-smoke/*/report.json',
    ],
    ['当前批次必须保留这条真实线上流式证据，不能只看接口 schema。']
  ),
  item(
    'flow.real-users',
    '真实用户测试回收',
    realUserAcceptance?.data?.passed === true ? 'ready' : (realUserPacket ? 'partial' : 'missing'),
    [
      realUserPacket && `${realUserPacket}/README.md`,
      realUserRoster && `${realUserRoster}/report.json`,
      realUserDispatch && `${realUserDispatch}/report.json`,
      realUserAcceptance?.path,
    ],
    [
      !realUserPacket && '缺少 real-user packet',
      !realUserRoster && '缺少真实用户测试名册报告',
      !realUserDispatch && '缺少真实用户发测分发索引',
      realUserAcceptance?.data?.passed !== true && '缺少通过的 artifacts/real-user-results/* 验收报告',
      realUserAcceptance?.data?.passed !== true && '缺少真实用户回传截图、测试人、设备、失败问题和复测结论',
    ],
    ['执行 npm run real-user:packet 后回填 result.json 和 screenshots，再运行 npm run real-user:check']
  ),
  item(
    'store.submissions',
    '商店提交与审核反馈',
    /提交|审核|被拒|整改/.test(reviewLog) && storeSubmissionPacket && storeMaterials && legalUrlCheck && privacyDisclosure && storeSubmissionStatus && storeEvidenceStatus && storeAccountAccess && domainHttps ? 'partial' : 'missing',
    [
      exists('docs/release/review-log.md') && 'docs/release/review-log.md',
      storeSubmissionPacket && `${storeSubmissionPacket}/README.md`,
      legalUrlCheck && `${legalUrlCheck}/report.json`,
      privacyDisclosure && `${privacyDisclosure}/report.json`,
      storeMaterials && `${storeMaterials}/report.json`,
      storeSubmissionStatus && `${storeSubmissionStatus}/report.json`,
      storeEvidenceStatus && `${storeEvidenceStatus}/report.json`,
      storeAccountAccess && `${storeAccountAccess}/report.json`,
      domainHttps && `${domainHttps}/report.json`,
    ],
    [
      !storeSubmissionPacket && '缺少商店提交材料包',
      !legalUrlCheck && '缺少法律 URL 验证报告',
      !privacyDisclosure && '缺少 App Privacy / Data safety 隐私披露报告',
      !storeMaterials && '缺少商店材料完整性检查报告',
      !storeSubmissionStatus && '缺少商店提交状态检查报告',
      !storeEvidenceStatus && '缺少商店后台证据收件检查报告',
      !storeAccountAccess && '缺少开发者账号与后台访问检查报告',
      !domainHttps && '缺少域名 HTTPS 与备案检查报告',
      '缺少应用宝、华为、小米、OPPO、vivo、Google Play、App Store 后台提交状态',
      '缺少真实审核反馈编号或截图',
    ],
    ['国内安卓与华为/鸿蒙优先提交，Apple/Google 按支付和隐私风险分批']
  ),
  item(
    'compliance.app-record',
    'APP 备案与不适用说明',
    appRecordStatusReport?.passed === true ? 'partial' : (appRecordStatus ? 'partial' : 'missing'),
    [
      appRecordStatus && `${appRecordStatus}/report.json`,
      exists('configs/release/app-record.json') && 'configs/release/app-record.json',
      exists('docs/release/app-record-handoff.md') && 'docs/release/app-record-handoff.md',
    ],
    [
      !appRecordStatus && '缺少 APP 备案状态检查报告',
      !exists('configs/release/app-record.json') && '缺少 APP 备案配置',
      !exists('docs/release/app-record-handoff.md') && '缺少 APP 备案交接说明',
      '国内安卓和鸿蒙 APP 备案、软著、应用资质或不适用说明截图仍未回传',
    ],
    ['国内安卓/鸿蒙后台截图回传后运行 npm run store:app-record -- --strict']
  ),
  item(
    'compliance.h5-legal-deploy',
    'H5 法律页线上部署',
    h5LegalDeployStatusReport?.passed === true ? 'ready' : (h5LegalDeployStatus ? 'partial' : 'missing'),
    [
      h5LegalDeployStatus && `${h5LegalDeployStatus}/report.json`,
      exists('dist/build/h5') && 'dist/build/h5',
      exists('docs/release/h5-legal-page-deploy-handoff.md') && 'docs/release/h5-legal-page-deploy-handoff.md',
      'https://shianjieyouwu.com/',
    ],
    [
      !h5LegalDeployStatus && '缺少 H5 法律页线上部署状态报告',
      h5LegalDeployStatus && h5LegalDeployStatusReport?.passed !== true && '线上法律页还未部署最新版 H5 chunk',
      h5LegalDeployStatus && h5LegalDeployStatusReport?.passed !== true && 'LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict 未通过',
    ],
    ['经用户确认后执行 CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5，并运行 strict 验证']
  ),
  item(
    'compliance.privacy-account',
    '隐私、权限、账号注销',
    profileSource.includes('/api/account/delete') && authSource.includes("@app.route('/api/account/delete'") ? 'partial' : 'missing',
    [
      exists('docs/release/app-store-privacy-notes.md') && 'docs/release/app-store-privacy-notes.md',
      profileSource.includes('/api/account/delete') && 'src/pages/profile/index.vue',
      authSource.includes("@app.route('/api/account/delete'") && 'backend/auth_routes.py',
    ],
    [
      '缺少 staging/真机账号注销截图',
      '缺少最终隐私政策 URL 和各商店权限声明截图',
    ],
    ['上架前强制验证注销后游客态、数据清理和审核账号可操作路径']
  ),
  item(
    'product.gtm',
    '产品、商业化、营销链路',
    productDoc.includes('Tianfu Agent') &&
      productDoc.includes('积分') &&
      productDoc.includes('营销链路') &&
      productStrategySkillDoc.includes('产品策略画布') &&
      productStrategySkillDoc.includes('monetization-strategy') &&
      productStrategySkillDoc.includes('gtm-strategy') &&
      productStrategySkillDoc.includes('marketing-ideas') ? 'ready' : 'partial',
    [
      exists('docs/release/product-gtm-benchmark.md') && 'docs/release/product-gtm-benchmark.md',
      exists('docs/release/product-strategy-skill-report.md') && 'docs/release/product-strategy-skill-report.md',
      exists('artifacts/competitor-research/2026-06-14-tianfu/01-home-hero.png') && 'artifacts/competitor-research/2026-06-14-tianfu/01-home-hero.png',
      exists('artifacts/competitor-research/2026-06-14-tianfu/06-start-chat-click.png') && 'artifacts/competitor-research/2026-06-14-tianfu/06-start-chat-click.png',
    ],
    [
      !productDoc.includes('内容板块优化') && '缺少内容板块优化建议',
      !productStrategySkillDoc.includes('产品策略画布') && '缺少产品 skill 策略画布',
      !productStrategySkillDoc.includes('审核账号资产不足') && '缺少审核账号资产产品风险判断',
    ],
    ['继续把商店截图做成“问事 -> 选术数 -> 解读 -> 报告 -> 复购”的转化链路']
  ),
  item(
    'store.screenshots',
    '商店截图素材候选',
    storeScreenshots?.data?.passed === true ? 'partial' : 'missing',
    [
      exists('docs/release/store-screenshot-storyboard.md') && 'docs/release/store-screenshot-storyboard.md',
      storeScreenshots?.data?.passed === true && storeScreenshots.path,
    ],
    [
      storeScreenshots?.data?.passed !== true && '缺少通过的 artifacts/store-screenshots/*/summary.json',
      'H5 自动截图不能替代当前批次 Android、macOS、Windows 真机截图；iOS、鸿蒙延期到后续批次',
    ],
    ['本地跑 npm run store:screenshots 产出候选图，正式提交前用真实安装包重截']
  ),
  item(
    'github.maintenance',
    'GitHub 维护与 Release 归档',
    exists('.github/labels.yml') && exists('.github/release-template.md') && exists('docs/release/github-maintenance.md') && releasePackage && desktopDownloads && platformHandoff && artifactIntake && artifactMetadata && mobileBuildRequests ? 'partial' : 'missing',
    [
      '.github/labels.yml',
      '.github/release-template.md',
      'docs/release/github-maintenance.md',
      artifactIntake && `${artifactIntake}/README.md`,
      artifactMetadata && `${artifactMetadata}/README.md`,
      mobileBuildRequests && `${mobileBuildRequests}/README.md`,
      platformHandoff && `${platformHandoff}/README.md`,
      releasePackage && `${releasePackage}/RELEASE_NOTES.md`,
      releasePackage && `${releasePackage}/upload-manifest.json`,
      releasePackage && `${releasePackage}/checksums.sha256`,
      desktopDownloads && `${desktopDownloads}/manifest.json`,
      desktopDownloads && `${desktopDownloads}/checksums.sha256`,
    ].filter(exists),
    [
      !releasePackage && '缺少本地 GitHub Release 草稿包',
      !desktopDownloads && '缺少桌面下载交付包',
      !platformHandoff && '缺少平台打包交接包',
      !mobileBuildRequests && '缺少移动端构建请求包',
      !artifactIntake && '缺少发行产物收件报告',
      !artifactMetadata && '缺少发行产物元数据报告',
      '缺少真实 GitHub Release 草稿和多端产物上传记录',
    ],
    ['机型问题继续用 Issue 标签，不按品牌拆仓']
  ),
  item(
    'staging.release',
    'staging-first 预发布隔离',
    stagingDoc.includes('Shian2002/shian-uni-app-staging') ? 'partial' : 'missing',
    [exists('docs/staging-workflow.md') && 'docs/staging-workflow.md'],
    [
      '缺少本轮 staging 部署记录',
      '缺少 qa:staging 和 staging 真机登录/积分/注销验收报告',
    ],
    ['危险改动先推 staging-origin/master，正式仓只接收已通过 staging 的提交']
  ),
]

const summary = {
  ready: checks.filter((entry) => entry.status === 'ready').length,
  partial: checks.filter((entry) => entry.status === 'partial').length,
  missing: checks.filter((entry) => entry.status === 'missing').length,
}

const report = {
  generatedAt: new Date().toISOString(),
  version: packageJson.version || 'unknown',
  branch: git(['branch', '--show-current']) || 'unknown',
  commit: git(['rev-parse', 'HEAD']) || 'unknown',
  strict,
  summary,
  checks,
  releaseScope: {
    currentBatch: releaseScope.currentBatch || '',
    activePlatforms: releaseScope.activePlatforms || [],
    deferredPlatforms: [...deferredPlatforms],
  },
  verdict: summary.missing === 0 && summary.partial === 0 ? 'ready' : 'not-ready',
}

const statusLabel = {
  ready: 'READY',
  partial: 'PARTIAL',
  missing: 'MISSING',
}

const md = [
  '# 全端发行 Readiness Audit',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 版本：${report.version}`,
  `> 分支：${report.branch}`,
  `> commit：${report.commit}`,
  `> 当前批次：${report.releaseScope.currentBatch || '未配置'}；已暂停平台：${report.releaseScope.deferredPlatforms.join('、') || '无'}`,
  `> 结论：${report.verdict === 'ready' ? '可进入全端上架候选' : '未达到全端上架候选'}`,
  '',
  `汇总：READY ${summary.ready} / PARTIAL ${summary.partial} / MISSING ${summary.missing}`,
  '',
  '| 项目 | 状态 | 证据 | 缺口 | 下一步 |',
  '| --- | --- | --- | --- | --- |',
  ...checks.map((entry) => {
    const evidence = entry.evidence.length ? entry.evidence.map((text) => `\`${text}\``).join('<br>') : '-'
    const missing = entry.missing.length ? entry.missing.join('<br>') : '-'
    const next = entry.next.length ? entry.next.join('<br>') : '-'
    return `| ${entry.title} | ${statusLabel[entry.status]} | ${evidence} | ${missing} | ${next} |`
  }),
  '',
  '## 放行规则',
  '',
  '- 默认 `npm run release:readiness` 只生成报告，不因为缺少商店包而失败。',
  '- 正式标记“可上架候选”前运行 `npm run release:readiness -- --strict`；只要存在 PARTIAL 或 MISSING 即失败。',
  '- 安装包、截图、hash、审核记录进入 GitHub Releases；证书、密钥、keystore、p12、描述文件不进入 Git。',
  '',
].join('\n')

mkdirSync(outDir, { recursive: true })
writeFileSync(jsonOut, `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(mdOut, md)

console.log(`Readiness audit: ${report.verdict}`)
console.log(`JSON: ${rel(jsonOut)}`)
console.log(`Markdown: ${rel(mdOut)}`)
console.log(`READY=${summary.ready} PARTIAL=${summary.partial} MISSING=${summary.missing}`)

if (strict && report.verdict !== 'ready') {
  console.error('严格模式失败：仍有 PARTIAL 或 MISSING 项。')
  process.exit(1)
}
