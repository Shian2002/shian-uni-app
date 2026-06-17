#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { basename, extname, join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.RELEASE_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.RELEASE_PACKAGE_DIR || join(root, 'artifacts', 'release-packages', `${localTimestamp()}-${version}`)

const binaryExts = new Set(['.apk', '.aab', '.ipa', '.hap', '.app', '.dmg', '.zip', '.exe', '.msi'])
const screenshotExts = new Set(['.png', '.jpg', '.jpeg', '.webp'])
const forbiddenPatterns = [
  /keystore/i,
  /\.jks$/i,
  /\.p12$/i,
  /mobileprovision/i,
  /private[-_]?key/i,
  /\.env$/i,
  /secret/i,
  /password/i,
  /credential/i,
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

const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
function packageRequired(platformId) {
  return !deferredPlatforms.has(platformId)
}

function readText(path) {
  const fullPath = join(root, path)
  return existsSync(fullPath) ? readFileSync(fullPath, 'utf8') : ''
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

function walk(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return []
  const entries = []
  for (const name of readdirSync(fullPath)) {
    const item = join(fullPath, name)
    const stat = statSync(item)
    if (stat.isDirectory()) entries.push(...walk(rel(item)))
    else entries.push({ path: rel(item), bytes: stat.size, mtimeMs: stat.mtimeMs })
  }
  return entries
}

function latestDir(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byTime = latestEntryTime(b, path) - latestEntryTime(a, path)
      return byTime || b.name.localeCompare(a.name)
    })
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function latestFile(path, suffix) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const files = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isFile() && item.name.endsWith(suffix))
    .sort((a, b) => {
      const byTime = statSync(b.full).mtimeMs - statSync(a.full).mtimeMs
      return byTime || b.name.localeCompare(a.name)
    })
  return files[0] ? join(path, files[0].name) : ''
}

function latestJsonReport(path) {
  const file = latestFile(path, '.json')
  if (!file) return null
  return { path: file, data: readJson(file) }
}

function latestEntryTime(entry, basePath) {
  const reportTimeValue = Math.max(
    reportTime(join(basePath, entry.name, 'report.json')),
    reportTime(join(basePath, entry.name, 'summary.json')),
    reportTime(join(basePath, entry.name, 'upload-manifest.json'))
  )
  return reportTimeValue || statSync(entry.full).mtimeMs || 0
}

function latestReportDirWith(path, filename) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory() && existsSync(join(root, item.reportPath)))
    .sort((a, b) => {
      const byReportTime = reportTime(b.reportPath) - reportTime(a.reportPath)
      return byReportTime || b.name.localeCompare(a.name)
    })
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function latestReport(path, filename = 'report.json') {
  const dir = latestReportDirWith(path, filename)
  if (!dir) return null
  return { dir, path: join(dir, filename), data: readJson(join(dir, filename)) }
}

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function isForbidden(path) {
  return forbiddenPatterns.some((pattern) => pattern.test(path))
}

function isUnpackedDesktopInternal(path) {
  return /desktop\/release\/(?:win|mac)[^/]*-unpacked\//i.test(path) ||
    /desktop\/release\/win-(?:arm64-)?unpacked\//i.test(path)
}

function isRedundantUserPacketBinary(path) {
  return /^artifacts\/desktop-macos-user-packets\/.+\.app\.zip$/i.test(path)
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
  return [...byHash.values()]
}

function artifactPriority(path) {
  if (path.startsWith('artifacts/desktop-downloads/')) return 0
  if (path.startsWith('artifacts/release-inbox/')) return 1
  if (path.startsWith('desktop/release/')) return 2
  return 2
}

function candidateArtifacts() {
  const latestDesktopBinaryRoots = [
    latestDir('artifacts/desktop-downloads'),
    latestDir('artifacts/desktop-macos-user-packets'),
    latestDir('artifacts/desktop-windows-user-packets'),
  ].filter(Boolean)
  const roots = [
    'dist',
    'desktop/release',
    'artifacts/release-inbox',
    'artifacts/current-downloads',
    ...latestDesktopBinaryRoots,
  ]
  const files = roots.flatMap(walk).filter((item) => item.bytes > 0 && !isForbidden(item.path))
  const binaries = files.filter((item) => binaryExts.has(extname(item.path).toLowerCase()) && !isUnpackedDesktopInternal(item.path) && !isRedundantUserPacketBinary(item.path))
  const screenshotDir = latestReportDirWith('artifacts/store-screenshots', 'summary.json')
  const screenshots = screenshotDir
    ? walk(screenshotDir).filter((item) => screenshotExts.has(extname(item.path).toLowerCase()) && !isForbidden(item.path))
    : []
  return { binaries, screenshots }
}

function artifactRows(items) {
  if (!items.length) return '| 暂缺 |  |  |  |'
  return items
    .map((item) => `| ${item.path} | ${item.bytes} | ${sha256(join(root, item.path))} | ${platformFor(item.path)} |`)
    .join('\n')
}

function platformFor(path) {
  const ext = extname(path).toLowerCase()
  if (['.apk', '.aab'].includes(ext)) return 'Android'
  if (ext === '.ipa') return 'iOS'
  if (['.hap', '.app'].includes(ext) && /harmony/i.test(path)) return 'Harmony'
  if (['.dmg', '.zip'].includes(ext) && /desktop|mac|arm64|x64|时安解忧屋/i.test(path)) return 'macOS/Desktop'
  if (['.exe', '.msi'].includes(ext)) return 'Windows'
  return 'Evidence'
}

function writeChecksums(items) {
  const lines = items.map((item) => `${sha256(join(root, item.path))}  ${item.path}`)
  writeFileSync(join(outDir, 'checksums.sha256'), `${lines.join('\n')}${lines.length ? '\n' : ''}`)
}

function reportHardBlock(report, label) {
  if (!report) return `${label} 报告缺失`
  return report.data?.passed === true ? '' : `${label} 未通过`
}

function artifactMetadataHardBlock(report) {
  if (!report) return '发行产物元数据台账报告缺失'
  if (report.data?.passed === true) return ''
  const issues = Number(report.data?.issues || 0)
  const missing = Number(report.data?.summary?.missing || 0)
  if (issues > 0 || missing > 0) {
    return `发行产物元数据台账未通过 ISSUES=${issues} MISSING=${missing}`
  }
  return ''
}

function desktopReleaseStatusHardBlock(report) {
  if (!report) return '桌面端发布状态报告缺失'
  if (report.data?.passed === true || report.data?.userTestPassed === true) return ''
  return '桌面端发布状态未通过'
}

function legalUrlHardBlock(report) {
  if (!report) return '法律 URL HTTPS/线上验证报告缺失'
  return report.data?.passed === true ? '' : '法律 URL HTTPS/线上验证未通过'
}

function realUserHardBlock(report) {
  if (!report) return '当前批次真实用户回收通过报告'
  if (report.data?.passed === true) return ''
  const summary = report.data?.summary
  if (summary && typeof summary.ready === 'number' && typeof summary.missing === 'number') {
    return `当前批次真实用户回收未通过 READY=${summary.ready} MISSING=${summary.missing}`
  }
  return '当前批次真实用户回收未通过'
}

function platformBackendMatrixHardBlock(report) {
  if (!report) return '全端后端能力矩阵报告缺失'
  const summary = report.data?.summary || {}
  if (summary.total > 0 && summary.backendReady === summary.total) return ''
  return `全端后端能力矩阵未通过 BACKEND_READY=${summary.backendReady ?? 0}/${summary.total ?? 0}`
}

function agentStreamSmokeHardBlock(report) {
  if (!report) return '真实 Agent stream 后端 smoke 报告缺失'
  if (report.data?.passed === true) return ''
  return '真实 Agent stream 后端 smoke 未通过'
}

function finalPackageCompletenessHardBlock(report) {
  if (!report) return '最终安装包完整性报告缺失'
  if (report.data?.passed === true) return ''
  const missing = Array.isArray(report.data?.missing) ? report.data.missing : []
  if (missing.length) return `最终安装包不完整: ${missing.join('、')}`
  return '最终安装包完整性未通过'
}

function userActionsHardBlock(report) {
  if (!report) return '人工事项交接包报告缺失'
  if (report.data?.passed === true) return ''
  const summary = report.data?.summary || {}
  const userRequired = Number.isFinite(summary.userRequired) ? summary.userRequired : 0
  const approvalRequired = Number.isFinite(summary.approvalRequired) ? summary.approvalRequired : 0
  if (userRequired || approvalRequired) {
    return `人工事项交接包未清零 USER=${userRequired} APPROVAL=${approvalRequired}`
  }
  return '人工事项交接包未通过'
}

function desktopDownloadsHardBlock(path) {
  if (!path) return '桌面下载交付包缺失'
  const manifest = readJson(`${path}/manifest.json`)
  if (manifest?.passed === true) return ''
  return '桌面下载交付包未通过'
}

function appIconsHardBlock(report) {
  if (!report) return 'App 图标资产检查报告缺失'
  if (report.data?.passed === true) return ''
  return 'App 图标资产检查未通过'
}

function main() {
  mkdirSync(outDir, { recursive: true })
  const { binaries, screenshots } = candidateArtifacts()
  const readiness = latestFile('artifacts/release-readiness', '.md')
  const tryNowPacket = latestDir('artifacts/try-now')
  const userActions = latestDir('artifacts/release-user-actions')
  const userActionsReport = latestReport('artifacts/release-user-actions')
  const productAudit = latestFile('artifacts/product-launch-audits', '.md')
  const releaseSummary = latestFile('artifacts/release-summaries', '.md')
  const realUserResult = latestFile('artifacts/real-user-results', '.md')
  const realUserResultReport = latestJsonReport('artifacts/real-user-results')
  const realUserPacket = latestDir('artifacts/real-user-packets')
  const realUserRoster = latestDir('artifacts/real-user-roster')
  const realUserRosterReport = latestReport('artifacts/real-user-roster')
  const realUserDispatch = latestDir('artifacts/real-user-dispatch')
  const channelBuilds = latestDir('artifacts/release-channel-builds')
  const mobileBuildEnv = latestDir('artifacts/mobile-build-env')
  const mobileBuildRequests = latestDir('artifacts/mobile-build-requests')
  const mobileApiEvidence = latestDir('artifacts/mobile-api-evidence')
  const mobileApiEvidenceReport = latestReport('artifacts/mobile-api-evidence', 'manifest.json')
  const agentStreamSmoke = latestDir('artifacts/agent-stream-smoke')
  const agentStreamSmokeReport = latestReport('artifacts/agent-stream-smoke')
  const platformBackendMatrix = latestDir('artifacts/platform-backend-matrix')
  const platformBackendMatrixReport = latestReport('artifacts/platform-backend-matrix')
  const finalPackageCompleteness = latestDir('artifacts/final-package-completeness')
  const finalPackageCompletenessReport = latestReport('artifacts/final-package-completeness')
  const mobileAppResourcePacket = latestDir('artifacts/mobile-app-resource-packets')
  const mobileAppResourcePacketReport = latestReport('artifacts/mobile-app-resource-packets', 'manifest.json')
  const platformHandoff = latestDir('artifacts/platform-build-handoffs')
  const artifactIntake = latestDir('artifacts/release-artifact-intake')
  const artifactMetadata = latestDir('artifacts/release-artifact-metadata')
  const artifactMetadataReport = latestReport('artifacts/release-artifact-metadata')
  const legalUrlCheck = latestDir('artifacts/legal-url-checks')
  const legalUrlCheckReport = latestReport('artifacts/legal-url-checks')
  const privacyDisclosure = latestDir('artifacts/privacy-disclosures')
  const privacyDisclosureReport = latestReport('artifacts/privacy-disclosures')
  const storeMaterials = latestDir('artifacts/store-materials')
  const storeMaterialsReport = latestReport('artifacts/store-materials')
  const storeSubmissionStatus = latestDir('artifacts/store-submission-status')
  const storeSubmissionStatusReport = latestReport('artifacts/store-submission-status')
  const storeEvidenceStatus = latestDir('artifacts/store-evidence-status')
  const storeEvidenceStatusReport = latestReport('artifacts/store-evidence-status')
  const storeAccountAccess = latestDir('artifacts/store-account-access')
  const storeAccountAccessReport = latestReport('artifacts/store-account-access')
  const appRecordStatus = latestDir('artifacts/app-record-status')
  const appRecordStatusReport = latestReport('artifacts/app-record-status')
  const domainHttps = latestDir('artifacts/domain-https')
  const domainHttpsReport = latestReport('artifacts/domain-https')
  const h5LegalDeployStatus = latestDir('artifacts/h5-legal-deploy-status')
  const h5LegalDeployStatusReport = latestReport('artifacts/h5-legal-deploy-status')
  const desktopReleaseStatus = latestDir('artifacts/desktop-release-status')
  const desktopReleaseStatusReport = latestReport('artifacts/desktop-release-status')
  const desktopDownloads = latestDir('artifacts/desktop-downloads')
  const desktopMacosInstall = latestDir('artifacts/desktop-macos-install')
  const desktopMacosInstallReport = latestReport('artifacts/desktop-macos-install')
  const desktopMacosLocalInstall = latestDir('artifacts/desktop-macos-local-install')
  const desktopMacosLifecycle = latestDir('artifacts/desktop-macos-lifecycle')
  const desktopMacosUserPacket = latestDir('artifacts/desktop-macos-user-packets')
  const desktopMacosUserPacketReport = latestReport('artifacts/desktop-macos-user-packets', 'manifest.json')
  const desktopWindowsUserPacket = latestDir('artifacts/desktop-windows-user-packets')
  const desktopWindowsUserPacketReport = latestReport('artifacts/desktop-windows-user-packets', 'manifest.json')
  const desktopWindowsRebuild = latestDir('artifacts/desktop-windows-rebuild')
  const desktopWindowsRebuildReport = latestReport('artifacts/desktop-windows-rebuild')
  const appIcons = latestDir('artifacts/app-icons')
  const appIconsReport = latestReport('artifacts/app-icons')
  const storeScreenshots = latestReportDirWith('artifacts/store-screenshots', 'summary.json')
  const allUploadCandidates = uniqueByHash([...binaries, ...screenshots])

  writeChecksums(allUploadCandidates)

  const uploadManifest = {
    generatedAt: new Date().toISOString(),
    version,
    branch: git(['branch', '--show-current']) || '',
    commit: git(['rev-parse', 'HEAD']) || '',
    releasePackageDir: rel(outDir),
    tryNowPacket,
    uploadCandidates: allUploadCandidates.map((item) => ({
      path: item.path,
      bytes: item.bytes,
      sha256: sha256(join(root, item.path)),
      kind: binaryExts.has(extname(item.path).toLowerCase()) ? 'binary' : 'screenshot',
      platform: platformFor(item.path),
    })),
    evidence: {
      readiness,
      tryNowPacket,
      userActions,
      productAudit,
      releaseSummary,
      channelBuilds,
      mobileBuildEnv,
      mobileBuildRequests,
      mobileApiEvidence,
      agentStreamSmoke,
      platformBackendMatrix,
      finalPackageCompleteness,
      mobileAppResourcePacket,
      artifactIntake,
      artifactMetadata,
      realUserResult,
      realUserPacket,
      realUserRoster,
      realUserDispatch,
      platformHandoff,
      legalUrlCheck,
      privacyDisclosure,
      storeMaterials,
      storeSubmissionStatus,
      storeEvidenceStatus,
      storeAccountAccess,
      appRecordStatus,
      domainHttps,
      h5LegalDeployStatus,
      desktopReleaseStatus,
      desktopDownloads,
      desktopMacosInstall,
      desktopMacosLocalInstall,
      desktopMacosLifecycle,
      desktopMacosUserPacket,
      desktopWindowsUserPacket,
      desktopWindowsRebuild,
      appIcons,
      storeScreenshots,
      githubTemplate: '.github/release-template.md',
    },
    missingHardBlocks: [
      binaries.some((item) => ['.apk', '.aab'].includes(extname(item.path).toLowerCase())) ? '' : 'Android APK/AAB',
      !packageRequired('ios') || binaries.some((item) => extname(item.path).toLowerCase() === '.ipa') ? '' : 'iOS IPA/TestFlight 构建记录',
      !packageRequired('harmony') || binaries.some((item) => ['.hap'].includes(extname(item.path).toLowerCase())) ? '' : '鸿蒙 HAP/AppGallery 包',
      binaries.some((item) => ['.exe', '.msi'].includes(extname(item.path).toLowerCase())) ? '' : 'Windows EXE/MSI',
      userActionsHardBlock(userActionsReport),
      realUserHardBlock(realUserResultReport),
      reportHardBlock(realUserRosterReport, '真实用户测试名册'),
      reportHardBlock(mobileApiEvidenceReport, '移动端 API 后端请求证据'),
      agentStreamSmokeHardBlock(agentStreamSmokeReport),
      platformBackendMatrixHardBlock(platformBackendMatrixReport),
      finalPackageCompletenessHardBlock(finalPackageCompletenessReport),
      reportHardBlock(mobileAppResourcePacketReport, '移动端 App 资源交付包'),
      legalUrlHardBlock(legalUrlCheckReport),
      reportHardBlock(privacyDisclosureReport, 'App Privacy / Data safety 隐私披露'),
      reportHardBlock(storeMaterialsReport, '商店材料完整性检查'),
      reportHardBlock(storeSubmissionStatusReport, '商店提交状态台账'),
      reportHardBlock(storeEvidenceStatusReport, '商店后台证据收件台账'),
      reportHardBlock(storeAccountAccessReport, '开发者账号与后台访问台账'),
      reportHardBlock(appRecordStatusReport, 'APP 备案与不适用说明'),
      reportHardBlock(domainHttpsReport, '域名 HTTPS 与备案台账'),
      reportHardBlock(h5LegalDeployStatusReport, 'H5 法律页线上部署状态'),
      artifactMetadataHardBlock(artifactMetadataReport),
      desktopReleaseStatusHardBlock(desktopReleaseStatusReport),
      desktopDownloadsHardBlock(desktopDownloads),
      reportHardBlock(desktopMacosInstallReport, 'macOS DMG 安装包校验'),
      reportHardBlock(desktopMacosUserPacketReport, 'macOS 个人试用交付包'),
      reportHardBlock(desktopWindowsRebuildReport, 'Windows x64 安全重建/新鲜度校验'),
      reportHardBlock(desktopWindowsUserPacketReport, 'Windows 个人试用交付包'),
      appIconsHardBlock(appIconsReport),
    ].filter(Boolean),
    releaseScope: {
      configPath: 'configs/release/current-release-scope.json',
      currentBatch: releaseScope.currentBatch || '',
      activePlatforms: releaseScope.activePlatforms || [],
      deferredPlatforms: [...deferredPlatforms],
    },
    sensitiveFilesExcluded: forbiddenPatterns.map((pattern) => String(pattern)),
  }
  writeFileSync(join(outDir, 'upload-manifest.json'), `${JSON.stringify(uploadManifest, null, 2)}\n`)

  const notes = [
    `# ${version} GitHub Release 草稿包`,
    '',
    `> 生成时间：${uploadManifest.generatedAt}`,
    `> commit：${uploadManifest.commit || '未读取到'}`,
    `> branch：${uploadManifest.branch || 'unknown'}`,
    `> 本地证据包：\`${uploadManifest.releasePackageDir}\``,
    '',
    '## 上传候选',
    '',
    '| 文件 | Bytes | SHA-256 | 平台 |',
    '| --- | ---: | --- | --- |',
    artifactRows(allUploadCandidates),
    '',
    '## 关键证据',
    '',
    `- Readiness Audit：${readiness ? `\`${readiness}\`` : '缺失'}`,
    `- Try Now Packet：${tryNowPacket ? `\`${tryNowPacket}\`` : '缺失'}`,
    `- User Action Handoff：${userActions ? `\`${userActions}\`` : '缺失'}`,
    `- Product Launch Audit：${productAudit ? `\`${productAudit}\`` : '缺失'}`,
    `- Release Summary：${releaseSummary ? `\`${releaseSummary}\`` : '缺失'}`,
    `- Channel Builds：${channelBuilds ? `\`${channelBuilds}\`` : '缺失'}`,
    `- Mobile Build Env：${mobileBuildEnv ? `\`${mobileBuildEnv}\`` : '缺失'}`,
    `- Mobile Build Requests：${mobileBuildRequests ? `\`${mobileBuildRequests}\`` : '缺失'}`,
    `- Mobile API Evidence：${mobileApiEvidence ? `\`${mobileApiEvidence}\`` : '缺失'}`,
    `- Agent Stream Smoke：${agentStreamSmoke ? `\`${agentStreamSmoke}\`` : '缺失'}`,
    `- Platform Backend Matrix：${platformBackendMatrix ? `\`${platformBackendMatrix}\`` : '缺失'}`,
    `- Final Package Completeness：${finalPackageCompleteness ? `\`${finalPackageCompleteness}\`` : '缺失'}`,
    `- Mobile App Resource Packet：${mobileAppResourcePacket ? `\`${mobileAppResourcePacket}\`` : '缺失'}`,
    `- Artifact Intake：${artifactIntake ? `\`${artifactIntake}\`` : '缺失'}`,
    `- Artifact Metadata：${artifactMetadata ? `\`${artifactMetadata}\`` : '缺失'}`,
    `- Real User Result：${realUserResult ? `\`${realUserResult}\`` : '缺失'}`,
    `- Real User Packet：${realUserPacket ? `\`${realUserPacket}\`` : '缺失'}`,
    `- Real User Roster：${realUserRoster ? `\`${realUserRoster}\`` : '缺失'}`,
    `- Real User Dispatch：${realUserDispatch ? `\`${realUserDispatch}\`` : '缺失'}`,
    `- Platform Handoff：${platformHandoff ? `\`${platformHandoff}\`` : '缺失'}`,
    `- Legal URL Check：${legalUrlCheck ? `\`${legalUrlCheck}\`` : '缺失'}`,
    `- Privacy Disclosure：${privacyDisclosure ? `\`${privacyDisclosure}\`` : '缺失'}`,
    `- Store Materials：${storeMaterials ? `\`${storeMaterials}\`` : '缺失'}`,
    `- Store Submission Status：${storeSubmissionStatus ? `\`${storeSubmissionStatus}\`` : '缺失'}`,
    `- Store Evidence Status：${storeEvidenceStatus ? `\`${storeEvidenceStatus}\`` : '缺失'}`,
    `- Store Account Access：${storeAccountAccess ? `\`${storeAccountAccess}\`` : '缺失'}`,
    `- App Record Status：${appRecordStatus ? `\`${appRecordStatus}\`` : '缺失'}`,
    `- Domain HTTPS：${domainHttps ? `\`${domainHttps}\`` : '缺失'}`,
    `- H5 Legal Deploy Status：${h5LegalDeployStatus ? `\`${h5LegalDeployStatus}\`` : '缺失'}`,
    `- Desktop Release Status：${desktopReleaseStatus ? `\`${desktopReleaseStatus}\`` : '缺失'}`,
    `- Desktop Downloads：${desktopDownloads ? `\`${desktopDownloads}\`` : '缺失'}`,
    `- Desktop macOS Install Verify：${desktopMacosInstall ? `\`${desktopMacosInstall}\`` : '缺失'}`,
    `- Desktop macOS Local Install：${desktopMacosLocalInstall ? `\`${desktopMacosLocalInstall}\`` : '缺失'}`,
    `- Desktop macOS Lifecycle：${desktopMacosLifecycle ? `\`${desktopMacosLifecycle}\`` : '缺失'}`,
    `- Desktop macOS User Packet：${desktopMacosUserPacket ? `\`${desktopMacosUserPacket}\`` : '缺失'}`,
    `- Desktop Windows Rebuild：${desktopWindowsRebuild ? `\`${desktopWindowsRebuild}\`` : '缺失'}`,
    `- Desktop Windows User Packet：${desktopWindowsUserPacket ? `\`${desktopWindowsUserPacket}\`` : '缺失'}`,
    `- App Icons：${appIcons ? `\`${appIcons}\`` : '缺失'}`,
    `- Store Screenshots：${storeScreenshots ? `\`${storeScreenshots}\`` : '缺失'}`,
    '',
    '## 不上传内容',
    '',
    '- keystore、jks、p12、mobileprovision、证书私钥。',
    '- `.env`、生产密钥、支付密钥、短信邮件密钥。',
    '- 真实用户数据、生产数据库、验证码日志。',
    '',
    '## 当前硬缺口',
    '',
    ...(uploadManifest.missingHardBlocks.length ? uploadManifest.missingHardBlocks.map((item) => `- ${item}`) : ['- 暂无硬缺口。']),
    '',
    '## 发布判断',
    '',
    uploadManifest.missingHardBlocks.length
      ? '当前只能作为 GitHub Release 草稿/内部测试证据包，不能标记为全端正式上架候选。'
      : '当前可进入人工复核，仍需确认商店后台状态和外部审批。',
    '',
  ].join('\n')
  writeFileSync(join(outDir, 'RELEASE_NOTES.md'), notes)

  console.log(JSON.stringify({
    outDir: rel(outDir),
    uploadCandidates: uploadManifest.uploadCandidates.length,
    missingHardBlocks: uploadManifest.missingHardBlocks,
  }, null, 2))
}

main()
