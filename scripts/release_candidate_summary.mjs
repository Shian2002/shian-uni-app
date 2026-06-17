#!/usr/bin/env node

import { existsSync, readFileSync, writeFileSync, mkdirSync, readdirSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const output = process.env.RELEASE_SUMMARY_OUT || join(root, 'artifacts', 'release-summaries', `${new Date().toISOString().replace(/[:.]/g, '-')}.md`)

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

function latestJson(paths) {
  for (const path of paths) {
    const data = readJson(path)
    if (data) return { path, data }
  }
  return null
}

function manifestArtifacts(manifest, prefix) {
  return (manifest?.artifacts || []).filter((item) => item.path.startsWith(prefix))
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

function latestFileByName(path, suffix) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const files = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isFile() && item.name.endsWith(suffix))
    .sort((a, b) => b.name.localeCompare(a.name))
  return files[0] ? join(path, files[0].name) : ''
}

function latestEntryTime(entry, basePath) {
  const reportTimeValue = Math.max(
    dirReportTime(entry, basePath),
    fileReportTime(join(basePath, entry.name, 'upload-manifest.json'))
  )
  return reportTimeValue || statSync(entry.full).mtimeMs || 0
}

function latestPassingReport(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byReportTime = dirReportTime(b, path) - dirReportTime(a, path)
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const dir of dirs) {
    const reportPath = join(path, dir.name, 'report.json')
    const summaryPath = join(path, dir.name, 'summary.json')
    const report = readJson(reportPath)
    if (report?.passed === true) return { path: reportPath, data: report }
    const summary = readJson(summaryPath)
    if (summary?.passed === true) return { path: summaryPath, data: summary }
  }
  return null
}

function dirReportTime(dir, path) {
  const report = readJson(join(path, dir.name, 'report.json'))
  const summary = readJson(join(path, dir.name, 'summary.json'))
  const raw = report?.generatedAt || report?.generated_at || summary?.generatedAt || summary?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function fileReportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function evidenceStatus(condition, ok, missing) {
  return condition ? `已具备：${ok}` : `缺口：${missing}`
}

const packageJson = readJson('package.json') || {}
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const latestManifest = latestJson([latestFileByName('artifacts/release-manifests', '.json')].filter(Boolean))
const mobileManifest = latestJson([
  latestManifest?.path,
  latestFileByName('artifacts/release-manifests', 'mobile-app-resources.json'),
].filter(Boolean))
const desktopManifest = latestJson([
  latestManifest?.path,
  latestFileByName('artifacts/release-manifests', 'desktop-macos-arm64.json'),
].filter(Boolean))
const mobileArtifacts = manifestArtifacts(mobileManifest?.data, 'dist/build/app/')
const desktopZip = (desktopManifest?.data?.artifacts || []).find((item) => item.path === 'desktop/release/时安解忧屋-1.0.0-arm64.app.zip')
const loginEvidenceDir = 'artifacts/browser-evidence/2026-06-14-login-agent'
const competitorEvidenceDir = 'artifacts/competitor-research/2026-06-14-tianfu'
const desktopSmoke = latestPassingReport('artifacts/desktop-smoke')?.data
const latestUserQa = latestPassingReport('artifacts/user-acceptance')
const latestLoginSmoke = latestPassingReport('artifacts/login-smoke')
const latestAgentEntry = latestPassingReport('artifacts/agent-entry')
const latestAgentStreamSmoke = latestPassingReport('artifacts/agent-stream-smoke')
const latestAuditAccount = latestPassingReport('artifacts/audit-account')
const latestStoreScreenshots = latestPassingReport('artifacts/store-screenshots')
const latestRealUserPacket = latestDir('artifacts/real-user-packets')
const latestRealUserRoster = latestDir('artifacts/real-user-roster')
const latestRealUserDispatch = latestDir('artifacts/real-user-dispatch')
const latestReleasePackage = latestDir('artifacts/release-packages')
const latestStoreSubmissionPacket = latestDir('artifacts/store-submission-packets')
const latestLegalUrlCheck = latestDir('artifacts/legal-url-checks')
const latestPrivacyDisclosure = latestDir('artifacts/privacy-disclosures')
const latestStoreMaterials = latestDir('artifacts/store-materials')
const latestStoreSubmissionStatus = latestDir('artifacts/store-submission-status')
const latestStoreEvidenceStatus = latestDir('artifacts/store-evidence-status')
const latestStoreAccountAccess = latestDir('artifacts/store-account-access')
const latestAppRecordStatus = latestDir('artifacts/app-record-status')
const latestDomainHttps = latestDir('artifacts/domain-https')
const latestH5LegalDeployStatus = latestDir('artifacts/h5-legal-deploy-status')
const latestDesktopReleaseStatus = latestDir('artifacts/desktop-release-status')
const latestDesktopDownloads = latestDir('artifacts/desktop-downloads')
const latestDesktopDownloadsManifest = latestDesktopDownloads ? readJson(`${latestDesktopDownloads}/manifest.json`) : null
const latestDesktopMacosInstall = latestDir('artifacts/desktop-macos-install')
const latestDesktopMacosInstallReport = latestDesktopMacosInstall ? readJson(`${latestDesktopMacosInstall}/report.json`) : null
const latestDesktopMacosUserPacket = latestDir('artifacts/desktop-macos-user-packets')
const latestDesktopMacosUserPacketManifest = latestDesktopMacosUserPacket ? readJson(`${latestDesktopMacosUserPacket}/manifest.json`) : null
const latestDesktopWindowsUserPacket = latestDir('artifacts/desktop-windows-user-packets')
const latestDesktopWindowsUserPacketManifest = latestDesktopWindowsUserPacket ? readJson(`${latestDesktopWindowsUserPacket}/manifest.json`) : null
const latestDesktopWindowsRebuild = latestDir('artifacts/desktop-windows-rebuild')
const latestDesktopWindowsRebuildReport = latestDesktopWindowsRebuild ? readJson(`${latestDesktopWindowsRebuild}/report.json`) : null
const latestTryNow = readJson('artifacts/try-now/latest-manifest.json')
const latestAndroidMetadata = readJson('artifacts/release-inbox/v1.0.0/android/build-metadata.json')
const latestAppIcons = latestDir('artifacts/app-icons')
const latestAppIconsReport = latestAppIcons ? readJson(`${latestAppIcons}/report.json`) : null
const latestPlatformHandoff = latestDir('artifacts/platform-build-handoffs')
const latestMobileBuildRequests = latestDir('artifacts/mobile-build-requests')
const latestMobileApiEvidence = latestDir('artifacts/mobile-api-evidence')
const latestMobileApiEvidenceManifest = latestMobileApiEvidence ? readJson(`${latestMobileApiEvidence}/manifest.json`) : null
const latestMobileAppResourcePacket = latestDir('artifacts/mobile-app-resource-packets')
const latestMobileAppResourcePacketManifest = latestMobileAppResourcePacket ? readJson(`${latestMobileAppResourcePacket}/manifest.json`) : null
const latestArtifactIntake = latestDir('artifacts/release-artifact-intake')
const latestArtifactMetadata = latestDir('artifacts/release-artifact-metadata')
const latestReadinessMd = latestFile('artifacts/release-readiness', '.md')
const latestUserActions = latestDir('artifacts/release-user-actions')
const latestProductAuditMd = latestFile('artifacts/product-launch-audits', '.md')

const lines = []
lines.push(`# Release 候选证据汇总`)
lines.push('')
lines.push(`> 生成时间：${new Date().toISOString()}`)
lines.push(`> 版本：${packageJson.version || 'unknown'}`)
lines.push(`> commit：${git(['rev-parse', 'HEAD']) || '未读取到'}`)
lines.push(`> branch：${git(['branch', '--show-current']) || 'unknown'}`)
lines.push('')
lines.push('## 自动门禁')
lines.push('')
lines.push('- `npm run lint`')
lines.push('- `npm run typecheck`')
lines.push('- `npm run release:check`')
lines.push('- `npm run test`')
lines.push('- `npm run build:h5`')
lines.push('- `npm run build:app`')
lines.push('- `MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight`')
lines.push('- `npm run mobile:build-requests`')
lines.push('- `npm run mobile:api-evidence`')
lines.push('- `npm run mobile:app-resource-packet`')
lines.push('- `npm run qa:agent:stream-smoke`')
lines.push('- `npm run release:intake`')
lines.push('- `npm run release:artifact-metadata`')
lines.push('- `npm run desktop:smoke`')
lines.push('- `npm run real-user:packet`')
lines.push('- `npm run real-user:roster`')
lines.push('- `npm run real-user:dispatch`')
lines.push('- `npm run store:materials`')
lines.push('- `npm run store:legal-urls`')
lines.push('- `npm run store:privacy`')
lines.push('- `npm run store:submission-status`')
lines.push('- `npm run store:evidence-status`')
lines.push('- `npm run store:account-access`')
lines.push('- `npm run store:app-record`')
lines.push('- `npm run domain:https`')
lines.push('- `npm run h5:legal-deploy-status`')
lines.push('- `npm run desktop:release-status`')
lines.push('- `npm run desktop:bundle`')
lines.push('- `npm run desktop:verify-macos`')
lines.push('- `npm run desktop:macos-user-packet`')
lines.push('- `npm run desktop:windows-user-packet`')
lines.push('- `npm run release:app-icons`')
lines.push('- `npm run release:user-actions`')
lines.push('- `npm run product:launch-audit`')
lines.push('')
lines.push('## 当前可证明产物')
lines.push('')
if (latestTryNow?.passed) {
  lines.push(`- 当前可试用包入口：\`${latestTryNow.latestPacketDir}\``)
  lines.push(`- try-now manifest：\`${latestTryNow.manifest || 'artifacts/try-now/latest-manifest.json'}\``)
  lines.push('')
}
lines.push('| 平台 | 状态 | 证据 |')
lines.push('| --- | --- | --- |')
lines.push(`| H5 | ${existsSync(join(root, 'dist/build/h5/index.html')) ? '已构建' : '未发现构建产物'} | \`dist/build/h5/index.html\` |`)
lines.push(`| App 资源 | ${mobileArtifacts.length ? '已构建' : '未发现构建产物'} | \`${mobileManifest?.path || '缺少 manifest'}\` |`)
lines.push(`| Android APK/AAB | ${latestTryNow?.androidDebugApk && latestTryNow?.androidDebugAab ? '内部测试 APK/AAB 已具备，正式渠道包未完成' : '未完成'} | ${latestTryNow?.androidDebugApk ? `APK \`${latestTryNow.androidDebugApk}\`；AAB \`${latestTryNow.androidDebugAab}\`；构建证据 ${(latestAndroidMetadata?.buildEvidence || []).map((item) => `\`${item}\``).join('、') || '缺少'}` : '需要 HBuilderX/DCloud 云打包、签名、真机截图；收件入口 `artifacts/release-inbox/`'} |`)
lines.push(`| iOS TestFlight | ${deferredPlatforms.has('ios') ? '本批次暂停' : '未完成'} | ${deferredPlatforms.has('ios') ? '按 current-release-scope.json 延期，不阻塞当前批次。' : '需要 Apple 证书、TestFlight 构建号、iPhone/iPad 截图；收件入口 `artifacts/release-inbox/`'} |`)
lines.push(`| 鸿蒙 | ${deferredPlatforms.has('harmony') ? '本批次暂停' : '未完成'} | ${deferredPlatforms.has('harmony') ? '按 current-release-scope.json 延期，不阻塞当前批次。' : '需要华为/鸿蒙构建记录、手机和平板截图；收件入口 `artifacts/release-inbox/`'} |`)
lines.push(`| macOS | ${desktopZip ? '已有未签名测试 zip' : '未发现 zip'} | ${desktopZip ? `\`${desktopZip.path}\`, SHA-256 \`${desktopZip.sha256}\`` : '缺少桌面产物'} |`)
lines.push(`| Windows | ${latestDesktopDownloadsManifest?.artifacts?.some((item) => item.id === 'windows-nsis') ? '已有未签名 NSIS 测试包' : '未完成'} | ${latestDesktopDownloads ? `\`${latestDesktopDownloads}/manifest.json\`` : '需要 Windows 环境生成 NSIS/EXE/MSI'} |`)
lines.push('')
lines.push('## 截图证据')
lines.push('')
if (desktopSmoke?.passed) {
  lines.push('- macOS 打包后 smoke：通过')
  lines.push(`- 营销首页：\`${desktopSmoke.screenshots.marketingHome}\``)
  lines.push(`- 登录弹窗：\`${desktopSmoke.screenshots.loginModal}\``)
  lines.push(`- 时安 agent：\`${desktopSmoke.screenshots.agentApp}\``)
} else {
  lines.push('- macOS 打包后 smoke：缺少通过报告')
}
if (existsSync(join(root, loginEvidenceDir, '06-marketing-desktop-auth-cta-fixed.png'))) {
  lines.push('- 登录/agent 入口本地验收：通过')
  lines.push(`- 桌面首页按钮：\`${loginEvidenceDir}/06-marketing-desktop-auth-cta-fixed.png\``)
  lines.push(`- 移动首页按钮：\`${loginEvidenceDir}/07-marketing-mobile-auth-cta-fixed.png\``)
  lines.push(`- 登录后 agent：\`${loginEvidenceDir}/04-after-agent-click-logged-in.png\``)
} else {
  lines.push('- 登录/agent 入口本地验收：缺少本轮截图证据')
}
if (existsSync(join(root, competitorEvidenceDir, '06-start-chat-click.png'))) {
  lines.push('- Tianfu Agent 对标取证：已记录首页、Start Chat 登录弹窗和产品文案')
  lines.push(`- Tianfu 首页：\`${competitorEvidenceDir}/01-home-hero.png\``)
  lines.push(`- Tianfu Start Chat：\`${competitorEvidenceDir}/06-start-chat-click.png\``)
}
if (latestLoginSmoke) {
  lines.push(`- 本地前端复用线上登录 smoke：\`${latestLoginSmoke.path}\``)
}
if (latestAgentEntry) {
  lines.push(`- 时安agent 入口验收：\`${latestAgentEntry.path}\``)
  const entryDir = latestAgentEntry.path.replace(/\/report\.json$/, '')
  lines.push(`- 未登录桌面登录弹窗：\`${entryDir}/desktop-01-unauth-agent-login-modal.png\``)
  lines.push(`- 登录后桌面 Agent：\`${entryDir}/desktop-02-authed-agent-app.png\``)
  lines.push(`- 未登录移动登录弹窗：\`${entryDir}/mobile-390-01-unauth-agent-login-modal.png\``)
  lines.push(`- 登录后移动 Agent：\`${entryDir}/mobile-390-02-authed-agent-app.png\``)
}
if (latestAgentStreamSmoke) {
  lines.push(`- 真实 Agent stream 后端 smoke：\`${latestAgentStreamSmoke.path}\``)
  lines.push(`- Agent stream conversation_id：${latestAgentStreamSmoke.data?.streamSummary?.conversationId || '-'}；事件数：${latestAgentStreamSmoke.data?.streamSummary?.eventCount || 0}；扣减：${latestAgentStreamSmoke.data?.streamSummary?.usedCredit || '-'}`)
}
if (latestAuditAccount) {
  lines.push(`- 审核账号资产预检：\`${latestAuditAccount.path}\``)
  lines.push(`- 审核账号完整 Agent 可用：${latestAuditAccount.data?.fullAgentReady ? '是' : '否'}`)
}
if (latestUserQa) {
  lines.push(`- 最新通过的本地用户验收：\`${latestUserQa.path}\``)
}
if (latestStoreScreenshots) {
  lines.push(`- 商店截图素材候选：\`${latestStoreScreenshots.path}\``)
  const captureCount = latestStoreScreenshots.data?.captures?.length || 0
  if (captureCount) lines.push(`- 商店截图数量：${captureCount} 张`)
  const deleteCaptures = (latestStoreScreenshots.data?.captures || []).filter((item) => item.id === '06-profile-delete')
  for (const item of deleteCaptures) {
    lines.push(`- 账号注销截图（${item.preset}）：\`${item.path}\``)
  }
}
if (latestReleasePackage) {
  lines.push(`- GitHub Release 本地草稿包：\`${latestReleasePackage}\``)
  lines.push(`- Release Notes：\`${latestReleasePackage}/RELEASE_NOTES.md\``)
  lines.push(`- 上传清单：\`${latestReleasePackage}/upload-manifest.json\``)
  lines.push(`- SHA-256 清单：\`${latestReleasePackage}/checksums.sha256\``)
}
if (latestUserActions) {
  lines.push(`- 最后人工事项交接包：\`${latestUserActions}\``)
}
if (latestRealUserDispatch) {
  lines.push(`- 真实用户发测分发索引：\`${latestRealUserDispatch}\``)
}
if (latestRealUserRoster) {
  lines.push(`- 真实用户测试名册：\`${latestRealUserRoster}\``)
}
if (latestPlatformHandoff) {
  lines.push(`- 平台打包交接包：\`${latestPlatformHandoff}\``)
}
if (latestMobileBuildRequests) {
  lines.push(`- 移动端构建请求包：\`${latestMobileBuildRequests}\``)
}
if (latestMobileApiEvidence) {
  lines.push(`- 移动端 API 后端请求证据：\`${latestMobileApiEvidence}/manifest.json\``)
}
if (latestMobileAppResourcePacket) {
  lines.push(`- 移动端 App 资源交付包：\`${latestMobileAppResourcePacket}/README.md\``)
  lines.push(`- 移动端 App 资源目录：\`${latestMobileAppResourcePacket}/app-resource\``)
}
if (latestArtifactIntake) {
  lines.push(`- 发行产物收件报告：\`${latestArtifactIntake}\``)
}
if (latestArtifactMetadata) {
  lines.push(`- 发行产物元数据报告：\`${latestArtifactMetadata}\``)
}
if (latestStoreSubmissionPacket) {
  lines.push(`- 商店提交材料包：\`${latestStoreSubmissionPacket}\``)
}
if (latestLegalUrlCheck) {
  lines.push(`- 法律 URL 验证：\`${latestLegalUrlCheck}\``)
}
if (latestPrivacyDisclosure) {
  lines.push(`- App Privacy / Data safety 隐私披露：\`${latestPrivacyDisclosure}\``)
}
if (latestStoreMaterials) {
  lines.push(`- 商店材料完整性检查：\`${latestStoreMaterials}\``)
}
if (latestStoreSubmissionStatus) {
  lines.push(`- 商店提交状态检查：\`${latestStoreSubmissionStatus}\``)
}
if (latestStoreEvidenceStatus) {
  lines.push(`- 商店后台证据收件检查：\`${latestStoreEvidenceStatus}\``)
}
if (latestStoreAccountAccess) {
  lines.push(`- 开发者账号与后台访问检查：\`${latestStoreAccountAccess}\``)
}
if (latestAppRecordStatus) {
  lines.push(`- APP 备案与不适用说明：\`${latestAppRecordStatus}\``)
}
if (latestDomainHttps) {
  lines.push(`- 域名 HTTPS 与备案检查：\`${latestDomainHttps}\``)
}
if (latestH5LegalDeployStatus) {
  lines.push(`- H5 法律页线上部署状态：\`${latestH5LegalDeployStatus}\``)
}
if (latestDesktopReleaseStatus) {
  lines.push(`- 桌面端发布状态检查：\`${latestDesktopReleaseStatus}\``)
}
if (latestDesktopDownloads) {
  lines.push(`- 桌面下载交付包：\`${latestDesktopDownloads}\``)
  lines.push(`- 桌面下载 manifest：\`${latestDesktopDownloads}/manifest.json\``)
  lines.push(`- 桌面下载 checksums：\`${latestDesktopDownloads}/checksums.sha256\``)
}
if (latestDesktopMacosInstall) {
  lines.push(`- macOS DMG 安装包校验：\`${latestDesktopMacosInstall}/report.json\``)
}
if (latestDesktopMacosUserPacket) {
  lines.push(`- macOS 个人试用包：\`${latestDesktopMacosUserPacket}/README.md\``)
  const dmgArtifact = (latestDesktopMacosUserPacketManifest?.artifacts || []).find((item) => item.fileName?.endsWith('.dmg'))
  if (dmgArtifact) lines.push(`- macOS 个人试用 DMG：\`${dmgArtifact.path}\``)
}
if (latestDesktopWindowsUserPacket) {
  lines.push(`- Windows 个人试用包：\`${latestDesktopWindowsUserPacket}/README.md\``)
  const exeArtifact = (latestDesktopWindowsUserPacketManifest?.artifacts || []).find((item) => item.fileName?.endsWith('.exe'))
  if (exeArtifact) lines.push(`- Windows 个人试用安装器：\`${exeArtifact.path}\``)
}
if (latestDesktopWindowsRebuild) {
  lines.push(`- Windows x64 安全重建/新鲜度校验：\`${latestDesktopWindowsRebuild}/report.json\``)
}
if (latestAppIcons) {
  lines.push(`- App 图标资产：\`${latestAppIcons}/report.json\``)
  lines.push(`- App 图标 1024 母图：\`${latestAppIconsReport?.storeIcon || 'src/static/app-icons/app-icon-1024.png'}\``)
}
lines.push('')
lines.push('## 上架候选判断')
lines.push('')
lines.push(`- Readiness Audit：${latestReadinessMd ? `\`${latestReadinessMd}\`` : '执行 `npm run release:readiness` 生成 READY/PARTIAL/MISSING 缺口报告。'}`)
lines.push(`- 人工事项交接包：${latestUserActions ? `\`${latestUserActions}\`` : '执行 `npm run release:user-actions` 生成“我可以继续做 / 需要确认 / 最后必须你做”的交接包。'}`)
lines.push(`- Product Launch Audit：${latestProductAuditMd ? `\`${latestProductAuditMd}\`` : '执行 `npm run product:launch-audit` 生成产品/GTM/截图/真实用户链路报告。'}`)
lines.push(`- ${evidenceStatus(mobileArtifacts.length, 'uni-app App 资源构建通过', '缺少 dist/build/app 构建产物')}`)
lines.push(`- ${evidenceStatus(Boolean(desktopZip), 'macOS 未签名测试 zip 和 hash', '缺少 macOS 桌面测试包')}`)
lines.push(`- ${evidenceStatus(Boolean(latestStoreScreenshots), '商店截图 H5 候选包已通过', '缺少通过的 store:screenshots 素材包')}`)
lines.push(`- ${evidenceStatus(Boolean(latestLoginSmoke), '本地前端复用线上登录 smoke 已通过', '缺少 qa:login:local-online 通过报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestAgentEntry), '时安agent 入口验收已通过', '缺少 qa:agent:entry-online-login 通过报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestAgentStreamSmoke), '真实 Agent stream 后端 smoke 已通过，已验证线上登录后可创建会话、流式返回和产物', '缺少 qa:agent:stream-smoke 通过报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestArtifactIntake), '发行产物收件报告已生成', '缺少 release:intake 收件报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestArtifactMetadata), '发行产物元数据报告已生成', '缺少 release:artifact-metadata 报告')}`)
lines.push(`- ${evidenceStatus(latestMobileApiEvidenceManifest?.passed === true, '移动端 API 后端请求证据已通过，本地 App 资源包含线上登录态和后端请求归一化', '缺少 mobile:api-evidence 后端请求证据')}`)
lines.push(`- ${evidenceStatus(latestMobileAppResourcePacketManifest?.passed === true, '移动端 App 资源交付包已生成，可交给 HBuilderX/DCloud/DevEco 打包', '缺少 mobile:app-resource-packet 资源交付包')}`)
lines.push(`- ${evidenceStatus(Boolean(latestLegalUrlCheck), '法律 URL 验证报告已生成', '缺少 store:legal-urls 报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestPrivacyDisclosure), 'App Privacy / Data safety 隐私披露报告已生成', '缺少 store:privacy 报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestStoreMaterials), '商店材料完整性检查已生成', '缺少 store:materials 报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestStoreEvidenceStatus), '商店后台证据收件检查已生成', '缺少 store:evidence-status 报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestStoreAccountAccess), '开发者账号与后台访问检查已生成', '缺少 store:account-access 报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestAppRecordStatus), 'APP 备案与不适用说明检查已生成', '缺少 store:app-record 报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestDomainHttps), '域名 HTTPS 与备案检查已生成', '缺少 domain:https 报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestH5LegalDeployStatus), 'H5 法律页线上部署状态已生成', '缺少 h5:legal-deploy-status 报告')}`)
lines.push(`- ${evidenceStatus(Boolean(latestDesktopReleaseStatus), '桌面端发布状态检查已生成', '缺少 desktop:release-status 报告')}`)
lines.push(`- ${evidenceStatus(latestDesktopDownloadsManifest?.passed === true, '桌面下载交付包已生成，文件名可用于 GitHub Releases/官网', '缺少 desktop:bundle 下载交付包')}`)
lines.push(`- ${evidenceStatus(latestDesktopMacosInstallReport?.passed === true, 'macOS DMG 已完成本机只读挂载和 App 结构校验', '缺少 desktop:verify-macos 通过报告')}`)
lines.push(`- ${evidenceStatus(latestDesktopMacosUserPacketManifest?.passed === true, 'macOS 个人试用包已生成，可直接找到 DMG、截图、checksum 和打开说明', '缺少 desktop:macos-user-packet 个人试用包')}`)
lines.push(`- ${evidenceStatus(latestDesktopWindowsRebuildReport?.passed === true, 'Windows x64 安全重建/新鲜度校验已通过', '缺少 desktop:build:win:x64:safe -- --verify-current 通过报告')}`)
lines.push(`- ${evidenceStatus(latestDesktopWindowsUserPacketManifest?.passed === true, 'Windows 个人试用包已生成，可用于 Windows 真机安装/卸载回收', '缺少 desktop:windows-user-packet 个人试用包')}`)
lines.push(`- ${evidenceStatus(latestAppIconsReport?.passed === true, 'App 图标资产检查已通过，移动端和桌面端共用你的 logo', '缺少 release:app-icons 图标资产报告')}`)
lines.push(`- ${evidenceStatus(latestTryNow?.passed === true, 'try-now 当前可试用包清单已生成，包含 macOS DMG、Windows 安装器、Android APK/AAB', '缺少 release:try-now 当前可试用包清单')}`)
lines.push(`- ${evidenceStatus(latestAuditAccount?.data?.fullAgentReady === true, '审核账号资产足够完整 Agent 演示', '审核账号资产不足或缺少 qa:audit-account 报告')}`)
lines.push(`- 缺口：当前批次仍需 Android 正式渠道签名包、桌面签名/公证/真机安装截图；iOS TestFlight 和鸿蒙包已延期到后续批次。`)
lines.push(`- 缺口：真实用户真机测试和商店后台提交记录仍未完成。`)
lines.push(`- 发测材料：${latestRealUserPacket ? `\`${latestRealUserPacket}\`` : '执行 `npm run real-user:packet` 生成当前批次 H5、Android、macOS、Windows 验收单；iOS、鸿蒙后续批次恢复。'}`)
lines.push(`- 测试名册：${latestRealUserRoster ? `\`${latestRealUserRoster}\`` : '执行 `npm run real-user:roster` 生成每个平台 2 个测试槽位、设备覆盖和回传状态报告。'}`)
lines.push(`- 发测分发索引：${latestRealUserDispatch ? `\`${latestRealUserDispatch}\`` : '执行 `npm run real-user:dispatch` 生成各平台可发测/不可发测原因。'}`)
lines.push(`- 平台打包交接包：${latestPlatformHandoff ? `\`${latestPlatformHandoff}\`` : '执行 `npm run platform:handoff` 生成平台打包交接包。'}`)
lines.push(`- 移动端构建请求包：${latestMobileBuildRequests ? `\`${latestMobileBuildRequests}\`` : '执行 `npm run mobile:build-requests` 生成 Android、iOS、鸿蒙构建请求和回传目录。'}`)
lines.push(`- 移动端 API 后端请求证据：${latestMobileApiEvidence ? `\`${latestMobileApiEvidence}\`` : '执行 `npm run mobile:api-evidence` 验证 dist/build/app 包含线上 API、登录态和后端请求归一化。'}`)
lines.push(`- 移动端 App 资源交付包：${latestMobileAppResourcePacket ? `\`${latestMobileAppResourcePacket}\`` : '执行 `npm run mobile:app-resource-packet` 生成 dist/build/app、图标、发行配置和回传目录索引。'}`)
lines.push(`- 发行产物收件报告：${latestArtifactIntake ? `\`${latestArtifactIntake}\`` : '外部安装包放入 `artifacts/release-inbox/` 后执行 `npm run release:intake`。'}`)
lines.push(`- 发行产物元数据报告：${latestArtifactMetadata ? `\`${latestArtifactMetadata}\`` : '外部安装包回传时同目录放 `build-metadata.json` 后执行 `npm run release:artifact-metadata`。'}`)
lines.push(`- GitHub Release 草稿包：${latestReleasePackage ? `\`${latestReleasePackage}\`` : '执行 `npm run release:package` 生成本地上传清单和 Release notes。'}`)
lines.push(`- 商店提交材料包：${latestStoreSubmissionPacket ? `\`${latestStoreSubmissionPacket}\`` : '执行 `npm run store:packet` 生成各商店提交材料草稿。'}`)
lines.push(`- 法律 URL 验证：${latestLegalUrlCheck ? `\`${latestLegalUrlCheck}\`` : '执行 `npm run store:legal-urls` 生成隐私政策和用户协议 URL 验证报告。'}`)
lines.push(`- App Privacy / Data safety 隐私披露：${latestPrivacyDisclosure ? `\`${latestPrivacyDisclosure}\`` : '执行 `npm run store:privacy` 生成 Apple/Google 隐私披露报告。'}`)
lines.push(`- 商店材料完整性检查：${latestStoreMaterials ? `\`${latestStoreMaterials}\`` : '执行 `npm run store:materials` 生成隐私 URL、截图、审核备注、Data safety/App Privacy 缺口报告。'}`)
lines.push(`- 商店提交状态台账：${latestStoreSubmissionStatus ? `\`${latestStoreSubmissionStatus}\`` : '执行 `npm run store:submission-status` 生成各商店提交状态、审核编号和整改台账。'}`)
lines.push(`- 商店后台证据收件台账：${latestStoreEvidenceStatus ? `\`${latestStoreEvidenceStatus}\`` : '执行 `npm run store:evidence-status` 生成商店后台截图、Data safety/App Privacy 截图、提交编号和账号注销真机图收件状态。'}`)
lines.push(`- 开发者账号与后台访问台账：${latestStoreAccountAccess ? `\`${latestStoreAccountAccess}\`` : '执行 `npm run store:account-access` 生成 DCloud、Apple、Google Play、华为、国内安卓市场和 GitHub Releases 的访问/2FA/资质/签名能力状态。'}`)
lines.push(`- APP 备案与不适用说明：${latestAppRecordStatus ? `\`${latestAppRecordStatus}\`` : '执行 `npm run store:app-record` 生成国内安卓、鸿蒙、iOS、Google Play 与 H5 的 APP 备案或不适用说明状态。'}`)
lines.push(`- 域名 HTTPS 与备案台账：${latestDomainHttps ? `\`${latestDomainHttps}\`` : '执行 `npm run domain:https` 生成 H5/API 域名、DNS、HTTPS、TLS、ICP备案和法律 URL 切换状态。移动端 APP 备案按包名、开发者账号和商店材料台账追踪。'}`)
lines.push(`- H5 法律页线上部署状态：${latestH5LegalDeployStatus ? `\`${latestH5LegalDeployStatus}\`` : '执行 `npm run h5:legal-deploy-status` 生成本地法律页 chunk 与线上部署状态对比报告。'}`)
lines.push(`- 桌面端发布状态台账：${latestDesktopReleaseStatus ? `\`${latestDesktopReleaseStatus}\`` : '执行 `npm run desktop:release-status` 生成 macOS/Windows 签名、公证、安装截图和安装包 hash 缺口报告。'}`)
lines.push(`- 桌面下载交付包：${latestDesktopDownloads ? `\`${latestDesktopDownloads}\`` : '执行 `npm run desktop:bundle` 生成 URL 友好文件名、manifest 和 checksums。'}`)
lines.push(`- macOS DMG 安装包校验：${latestDesktopMacosInstall ? `\`${latestDesktopMacosInstall}\`` : '执行 `npm run desktop:verify-macos` 只读挂载 DMG 并检查包内 App、Info.plist、主可执行文件和 icon.icns。'}`)
lines.push(`- macOS 个人试用包：${latestDesktopMacosUserPacket ? `\`${latestDesktopMacosUserPacket}\`` : '执行 `npm run desktop:macos-user-packet` 生成你当前优先使用的 DMG、README、截图和 checksum。'}`)
lines.push(`- Windows x64 安全重建/新鲜度校验：${latestDesktopWindowsRebuild ? `\`${latestDesktopWindowsRebuild}\`` : '执行 `npm run desktop:build:win:x64:safe -- --verify-current` 校验 Windows 安装器新鲜度。'}`)
lines.push(`- Windows 个人试用包：${latestDesktopWindowsUserPacket ? `\`${latestDesktopWindowsUserPacket}\`` : '执行 `npm run desktop:windows-user-packet` 生成 Windows 安装器、README、截图、checksum 和真机回收清单。'}`)
lines.push(`- App 图标资产：${latestAppIcons ? `\`${latestAppIcons}\`` : '执行 `npm run release:app-icons` 生成移动端/桌面端统一 logo 图标检查报告。'}`)
lines.push(`- 登录入口判断：未登录顶部应显示 \`时安agent\` + \`登录/注册\`，登录后点击 \`时安agent\` 进入 \`#/?app=1\`。`)
lines.push(`- 产品/GTM判断：Tianfu 的 \`Start Chat\` 也是先打开登录弹窗；我们的按钮必须保持产品入口和账号入口分层。`)
lines.push(`- 结论：当前不是全端正式上架候选，但已具备 H5、App 资源、macOS/Windows 桌面测试包和多端发行门禁证据。`)
lines.push('')
lines.push('## 下一步')
lines.push('')
lines.push('1. 在 HBuilderX/DCloud 云打包生成 Android 正式渠道签名 APK/AAB，并上传 GitHub Releases 记录 hash。当前内部测试 APK/AAB 只用于先行真机回归。')
lines.push('2. 在 Windows 10/11 真机安装当前 NSIS 测试包，补安装、开始菜单、卸载、窗口缩放截图和代码签名状态。')
lines.push('3. 按 `real-user-acceptance.md` 组织当前批次 H5、Android、macOS、Windows 真实用户测试。')
lines.push('4. iOS 和鸿蒙本批次暂停，后续恢复时再补 Xcode/TestFlight 与 DevEco/鸿蒙包。')

mkdirSync(join(output, '..'), { recursive: true })
writeFileSync(output, `${lines.join('\n')}\n`)
console.log(output)
