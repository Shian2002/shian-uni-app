import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const artifactsRoot = join(root, 'artifacts')
const packageJson = readJson('package.json') || {}
const version = process.env.RELEASE_CURRENT_INDEX_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.RELEASE_CURRENT_INDEX_OUT_DIR || join(artifactsRoot, 'current-index', `${localTimestamp()}-${version}`)
const strict = process.argv.includes('--strict') || process.env.RELEASE_CURRENT_INDEX_STRICT === '1'

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

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function fileInfo(path) {
  if (!path) return null
  const fullPath = join(root, path)
  if (!existsSync(fullPath) || !statSync(fullPath).isFile()) return null
  const stat = statSync(fullPath)
  return {
    path,
    bytes: stat.size,
    sha256: sha256(fullPath),
    mtime: new Date(stat.mtimeMs).toISOString(),
  }
}

function fileInfoFromManifest(manifest, label) {
  const item = (manifest?.files || []).find((file) => file.label === label)
  return fileInfo(item?.path || '')
}

function desktopArtifactInfo(manifest, id) {
  const item = (manifest?.artifacts || []).find((artifact) => artifact.id === id)
  return fileInfo(item?.path || '')
}

function latestDir(parent, requiredFile = '') {
  const fullParent = join(root, parent)
  if (!existsSync(fullParent)) return ''
  const dirs = readdirSync(fullParent, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => {
      const fullPath = join(fullParent, entry.name)
      return { name: entry.name, fullPath, mtimeMs: statSync(fullPath).mtimeMs }
    })
    .filter((entry) => !requiredFile || existsSync(join(entry.fullPath, requiredFile)))
    .sort((a, b) => b.mtimeMs - a.mtimeMs)
  return dirs[0] ? `${parent}/${dirs[0].name}` : ''
}

function jsonAt(dir, fileName) {
  return dir ? readJson(`${dir}/${fileName}`) : null
}

function status(value) {
  return value ? 'ready' : 'missing'
}

function checkByName(report, name) {
  return (report?.checks || []).find((item) => item.name === name) || null
}

function coreBackendCoverage(report) {
  const expected = [
    ['ziwei-info', '紫微信息'],
    ['huangli', '黄历'],
    ['bazi-paipan', '八字排盘'],
    ['bazi-shian-pro', '专业八字'],
    ['ziwei-pan', '紫微盘'],
    ['qimen-paipan', '奇门排盘'],
    ['meihua-paipan', '梅花排盘'],
    ['liuyao-paipan', '六爻排盘'],
    ['zeji', '择吉'],
    ['records', '记录'],
    ['collections', '收藏'],
  ]
  const items = expected.map(([name, label]) => {
    const check = checkByName(report, name)
    return {
      name,
      label,
      status: check?.status || null,
      ok: check?.ok === true,
      schemaReady: check?.schemaReady === true,
    }
  })
  return {
    total: items.length,
    passed: items.filter((item) => item.ok && item.schemaReady).length,
    items,
  }
}

function evidenceSummary(desktopSmoke, desktopOnlineLoginSmoke, agentStreamSmoke, mobileApiEvidence, appIcons) {
  const membership = checkByName(desktopOnlineLoginSmoke, 'membership')
  const pointsLog = checkByName(desktopOnlineLoginSmoke, 'points-log')
  const options = checkByName(desktopOnlineLoginSmoke, 'comprehensive-options')
  const recommendTools = checkByName(desktopOnlineLoginSmoke, 'comprehensive-recommend-tools')
  const guide = checkByName(desktopOnlineLoginSmoke, 'comprehensive-guide')
  return {
    desktopNative: {
      passed: desktopSmoke?.passed === true,
      topbarColor: desktopSmoke?.layout?.agent?.topnav?.backgroundColor || '',
      agentInputBottom: desktopSmoke?.layout?.agent?.homeAiMain?.bottom || null,
      loginModalAlign: desktopSmoke?.layout?.login?.alignItems || '',
    },
    backendContract: {
      passed: desktopOnlineLoginSmoke?.passed === true,
      apiTarget: desktopOnlineLoginSmoke?.apiTarget || '',
      user: desktopOnlineLoginSmoke?.qaUser || '',
      membership: membership ? { level: membership.level, points: membership.points, schemaReady: membership.schemaReady === true } : null,
      pointsLog: pointsLog ? { total: pointsLog.total, logsReturned: pointsLog.logsReturned, schemaReady: pointsLog.schemaReady === true } : null,
      agentOptions: options ? { llmModels: options.llmModels, readingModes: options.readingModes, toolModels: options.toolModels, schemaReady: options.schemaReady === true } : null,
      recommendTools: recommendTools ? { toolModels: recommendTools.toolModels || [], estimatedCost: recommendTools.estimatedCost, schemaReady: recommendTools.schemaReady === true } : null,
      guide: guide ? { status: guide.guideStatus, source: guide.source, schemaReady: guide.schemaReady === true } : null,
      coreFunctions: coreBackendCoverage(desktopOnlineLoginSmoke),
    },
    mobileRuntime: {
      passed: mobileApiEvidence?.passed === true,
      checkedFiles: mobileApiEvidence?.checkedFiles?.length || 0,
      requiredRuntimeEvidence: mobileApiEvidence?.requiredRuntimeEvidence || [],
    },
    agentStream: {
      passed: agentStreamSmoke?.passed === true,
      apiTarget: agentStreamSmoke?.apiTarget || agentStreamSmoke?.baseUrl || '',
      user: agentStreamSmoke?.qaUser || '',
      usedCredit: agentStreamSmoke?.streamSummary?.usedCredit || '',
      conversationId: agentStreamSmoke?.streamSummary?.conversationId || null,
      eventCount: agentStreamSmoke?.streamSummary?.eventCount || 0,
      artifactKeys: agentStreamSmoke?.streamSummary?.artifactKeys || [],
      evidence: latest.agentStreamSmoke || '',
    },
    icons: {
      passed: appIcons?.passed === true,
      mobileIcons: appIcons?.summary?.mobileIcons || appIcons?.icons || null,
      desktopIcons: appIcons?.summary?.desktopIcons || appIcons?.desktopIcons || null,
    },
  }
}

function legalDeploySummary(report) {
  const localLegalChunk = typeof report?.localLegalChunk === 'string'
    ? report.localLegalChunk
    : (report?.localLegalChunk?.path || '')
  return {
    passed: report?.passed === true,
    onlineLegalPage: report?.onlineLegalPage === true || report?.online?.deployedLegalPage === true,
    onlineIcpFooter: report?.onlineIcpFooter === true || report?.online?.deployedIcpFooter === true,
    localLegalChunk,
    issues: report?.issues || [],
  }
}

function windowsPackageFreshness(windowsInstaller, rebuildReport, h5Build) {
  const base = {
    fresh: false,
    issue: '',
    reportPassed: rebuildReport?.passed === true,
    currentSha256: windowsInstaller?.sha256 || '',
    rebuiltInstallerSha256: rebuildReport?.files?.installer?.sha256 || '',
    rebuiltH5Sha256: rebuildReport?.files?.h5?.sha256 || '',
    currentH5Sha256: h5Build?.sha256 || '',
  }
  if (!windowsInstaller) {
    return { ...base, issue: 'Windows 安装器缺失' }
  }
  if (!rebuildReport) {
    return { ...base, issue: 'Windows 重建报告缺失，无法证明当前安装器为最新 H5 产物' }
  }
  if (rebuildReport.passed !== true) {
    return {
      ...base,
      issue: `Windows 最新重建未通过：${(rebuildReport.issues || []).join('；') || '未知原因'}`,
    }
  }
  if (!base.rebuiltInstallerSha256 || base.rebuiltInstallerSha256 !== base.currentSha256) {
    return { ...base, issue: 'Windows 当前安装器与最新通过的重建报告 SHA-256 不一致' }
  }
  if (!base.currentH5Sha256 || !base.rebuiltH5Sha256 || base.rebuiltH5Sha256 !== base.currentH5Sha256) {
    return { ...base, issue: 'Windows 安装器不是最新 H5 构建后的产物' }
  }
  return { ...base, fresh: true }
}

const latest = {
  tryNow: latestDir('artifacts/try-now', 'manifest.json'),
  releasePackage: latestDir('artifacts/release-packages', 'upload-manifest.json'),
  externalHandoff: latestDir('artifacts/external-handoff', 'manifest.json'),
  userActions: latestDir('artifacts/release-user-actions', 'report.json'),
  desktopDownloads: latestDir('artifacts/desktop-downloads', 'manifest.json'),
  desktopWindowsRebuild: latestDir('artifacts/desktop-windows-rebuild', 'report.json'),
  currentDownloads: existsSync(join(root, 'artifacts', 'current-downloads', 'manifest.json')) ? 'artifacts/current-downloads' : '',
  macosUserPacket: latestDir('artifacts/desktop-macos-user-packets', 'manifest.json'),
  windowsUserPacket: latestDir('artifacts/desktop-windows-user-packets', 'manifest.json'),
  desktopSmoke: latestDir('artifacts/desktop-smoke', 'report.json'),
  desktopOnlineLoginSmoke: latestDir('artifacts/desktop-online-login-smoke', 'report.json'),
  agentStreamSmoke: latestDir('artifacts/agent-stream-smoke', 'report.json'),
  mobileApiEvidence: latestDir('artifacts/mobile-api-evidence', 'manifest.json'),
  mobileAppResourcePacket: latestDir('artifacts/mobile-app-resource-packets', 'manifest.json'),
  platformBackendMatrix: latestDir('artifacts/platform-backend-matrix', 'report.json'),
  appIcons: latestDir('artifacts/app-icons', 'report.json'),
  artifactPrune: latestDir('artifacts/artifact-prune', 'report.json'),
  h5LegalDeployStatus: latestDir('artifacts/h5-legal-deploy-status', 'report.json'),
}

const tryNow = jsonAt(latest.tryNow, 'manifest.json')
const releasePackage = jsonAt(latest.releasePackage, 'upload-manifest.json')
const externalHandoff = jsonAt(latest.externalHandoff, 'manifest.json')
const userActions = jsonAt(latest.userActions, 'report.json')
const desktopSmoke = jsonAt(latest.desktopSmoke, 'report.json')
const desktopOnlineLoginSmoke = jsonAt(latest.desktopOnlineLoginSmoke, 'report.json')
const agentStreamSmoke = jsonAt(latest.agentStreamSmoke, 'report.json')
const desktopWindowsRebuild = jsonAt(latest.desktopWindowsRebuild, 'report.json')
const mobileApiEvidence = jsonAt(latest.mobileApiEvidence, 'manifest.json')
const mobileAppResourcePacket = jsonAt(latest.mobileAppResourcePacket, 'manifest.json')
const platformBackendMatrix = jsonAt(latest.platformBackendMatrix, 'report.json')
const currentDownloads = jsonAt(latest.currentDownloads, 'manifest.json')
const desktopDownloads = jsonAt(latest.desktopDownloads, 'manifest.json')
const appIcons = jsonAt(latest.appIcons, 'report.json')
const artifactPrune = jsonAt(latest.artifactPrune, 'report.json')
const h5LegalDeployStatus = jsonAt(latest.h5LegalDeployStatus, 'report.json')

const usable = {
  macosDmg: fileInfo(tryNow?.tryNow?.macosDmg || externalHandoff?.currentUsable?.macosDmg || '') || desktopArtifactInfo(desktopDownloads, 'macos-dmg') || fileInfoFromManifest(currentDownloads, 'shian-current-macos-arm64.dmg'),
  macosAppZip: fileInfo(tryNow?.tryNow?.macosUpdatedAppZip || '') || desktopArtifactInfo(desktopDownloads, 'macos-app-zip') || fileInfoFromManifest(currentDownloads, 'shian-current-macos-arm64.app.zip'),
  windowsInstaller: fileInfo(tryNow?.tryNow?.windowsInstaller || externalHandoff?.currentUsable?.windowsInstaller || '') || desktopArtifactInfo(desktopDownloads, 'windows-nsis') || fileInfoFromManifest(currentDownloads, 'shian-current-windows-x64.exe'),
  androidDebugApk: fileInfo(tryNow?.tryNow?.androidDebugApk || externalHandoff?.currentUsable?.androidDebugApk || '') || fileInfoFromManifest(currentDownloads, 'shian-current-android-debug.apk'),
  androidDebugAab: fileInfo(tryNow?.tryNow?.androidDebugAab || externalHandoff?.currentUsable?.androidDebugAab || '') || fileInfoFromManifest(currentDownloads, 'shian-current-android-debug.aab'),
  mobileStoreIcon: fileInfo(mobileAppResourcePacket?.storeIcon?.path || '') || fileInfo(tryNow?.tryNow?.mobileStoreIcon || '') || fileInfoFromManifest(currentDownloads, 'shian-current-app-icon-1024.png'),
}

const freshness = {
  windows: windowsPackageFreshness(usable.windowsInstaller, desktopWindowsRebuild, fileInfo('dist/build/h5/index.html')),
}

const checks = {
  tryNowPassed: tryNow?.passed === true,
  releasePackageHasLatestTryNow: Boolean(releasePackage?.tryNowPacket && latest.tryNow && releasePackage.tryNowPacket === latest.tryNow),
  externalHandoffHasLatestPackage: Boolean(externalHandoff?.evidence?.releasePackage && latest.releasePackage && externalHandoff.evidence.releasePackage === latest.releasePackage),
  currentDownloadsPassed: currentDownloads?.passed === true && (currentDownloads.files || []).every((file) => Boolean(fileInfo(file.path))),
  desktopSmokePassed: desktopSmoke?.passed === true,
  desktopOnlineLoginSmokePassed: desktopOnlineLoginSmoke?.passed === true,
  agentStreamSmokePassed: agentStreamSmoke?.passed === true,
  mobileApiEvidencePassed: mobileApiEvidence?.passed === true,
  platformBackendMatrixGenerated: Boolean(platformBackendMatrix),
  appIconsPassed: appIcons?.passed === true,
  macosDmgPresent: Boolean(usable.macosDmg),
  windowsInstallerPresent: Boolean(usable.windowsInstaller),
  windowsInstallerFresh: freshness.windows.fresh,
  androidDebugApkPresent: Boolean(usable.androidDebugApk),
}

const remainingHardBlocks = releasePackage?.missingHardBlocks || tryNow?.releaseMissingHardBlocks || externalHandoff?.remainingHardBlocks || []
const userSummary = userActions?.summary || {}
const legalDeploy = legalDeploySummary(h5LegalDeployStatus)
const approvalRequiredActions = legalDeploy.passed ? [] : [
  '明确批准后才能执行生产 H5 法律页部署：CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh。',
  '部署后重新跑法律 URL 严格验证，并保存商店后台 URL 截图。',
]
const issues = [
  !checks.tryNowPassed && 'try-now 当前清单未通过或缺失',
  !checks.currentDownloadsPassed && '当前稳定下载入口未通过或缺失',
  !checks.desktopSmokePassed && '桌面布局 smoke 未通过或缺失',
  !checks.desktopOnlineLoginSmokePassed && '桌面线上登录/积分/agent smoke 未通过或缺失',
  !checks.agentStreamSmokePassed && '真实 Agent stream 后端 smoke 未通过或缺失',
  !checks.mobileApiEvidencePassed && '移动端 API 后端请求证据未通过或缺失',
  !checks.platformBackendMatrixGenerated && '全端后端能力矩阵缺失',
  !checks.appIconsPassed && 'App 图标检查未通过或缺失',
  !checks.macosDmgPresent && 'macOS DMG 缺失',
  !checks.windowsInstallerPresent && 'Windows 安装器缺失',
  checks.windowsInstallerPresent && !checks.windowsInstallerFresh && freshness.windows.issue,
  !checks.androidDebugApkPresent && 'Android debug APK 缺失',
].filter(Boolean)

const index = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  passed: issues.length === 0,
  latest,
  usable,
  checks,
  evidenceSummary: evidenceSummary(desktopSmoke, desktopOnlineLoginSmoke, agentStreamSmoke, mobileApiEvidence, appIcons),
  freshness,
  platformBackendMatrix: platformBackendMatrix ? {
    path: latest.platformBackendMatrix,
    complete: platformBackendMatrix.complete === true,
    summary: platformBackendMatrix.summary || null,
  } : null,
  userActions: userSummary,
  legalDeploy,
  approvalRequiredActions,
  remainingHardBlocks,
  userMustDoLast: [...new Set([...(tryNow?.userMustDoLast || []), ...approvalRequiredActions])],
  artifactPrune: artifactPrune ? {
    mode: artifactPrune.mode,
    keep: artifactPrune.keep,
    deletedCount: artifactPrune.deletedCount,
    estimatedFreedMB: artifactPrune.estimatedFreedMB,
  } : null,
  issues,
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'index.json'), `${JSON.stringify(index, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# 当前可试用与发行状态索引',
  '',
  `> 生成时间：${index.generatedAt}`,
  `> 结论：${index.passed ? '当前可试用包齐备；正式上架仍有人工硬阻塞。' : '当前索引存在缺口。'}`,
  '',
  '## 当前可试用包',
  '',
  `- macOS DMG：${usable.macosDmg ? `\`${usable.macosDmg.path}\` SHA-256 \`${usable.macosDmg.sha256}\`` : '缺失'}`,
  `- macOS App ZIP：${usable.macosAppZip ? `\`${usable.macosAppZip.path}\` SHA-256 \`${usable.macosAppZip.sha256}\`` : '缺失'}`,
  `- Windows 安装器：${usable.windowsInstaller ? `\`${usable.windowsInstaller.path}\` SHA-256 \`${usable.windowsInstaller.sha256}\`` : '缺失'}`,
  `- Windows 新鲜度：${freshness.windows.fresh ? '通过' : freshness.windows.issue || '缺失'}；重建报告 \`${latest.desktopWindowsRebuild || '缺失'}\`。`,
  `- Android APK：${usable.androidDebugApk ? `\`${usable.androidDebugApk.path}\` SHA-256 \`${usable.androidDebugApk.sha256}\`` : '缺失'}`,
  `- Android AAB：${usable.androidDebugAab ? `\`${usable.androidDebugAab.path}\` SHA-256 \`${usable.androidDebugAab.sha256}\`` : '缺失'}`,
  `- App 图标母图：${usable.mobileStoreIcon ? `\`${usable.mobileStoreIcon.path}\` SHA-256 \`${usable.mobileStoreIcon.sha256}\`` : '缺失'}`,
  '',
  '## 稳定下载入口',
  '',
  `- 固定文件名目录：\`${latest.currentDownloads || '缺失'}\``,
  `- macOS DMG：\`${latest.currentDownloads ? 'artifacts/current-downloads/shian-current-macos-arm64.dmg' : '缺失'}\``,
  `- Windows 安装器：\`${latest.currentDownloads ? 'artifacts/current-downloads/shian-current-windows-x64.exe' : '缺失'}\``,
  `- Android APK：\`${latest.currentDownloads ? 'artifacts/current-downloads/shian-current-android-debug.apk' : '缺失'}\``,
  '',
  '## 关键证据',
  '',
  `- try-now：\`${latest.tryNow || '缺失'}\``,
  `- release package：\`${latest.releasePackage || '缺失'}\``,
  `- external handoff：\`${latest.externalHandoff || '缺失'}\``,
  `- 桌面布局 smoke：\`${latest.desktopSmoke || '缺失'}\``,
  `- 桌面线上后端 smoke：\`${latest.desktopOnlineLoginSmoke || '缺失'}\``,
  `- 真实 Agent stream smoke：\`${latest.agentStreamSmoke || '缺失'}\``,
  `- 移动端 API 后端请求证据：\`${latest.mobileApiEvidence || '缺失'}\``,
  `- 全端后端能力矩阵：\`${latest.platformBackendMatrix || '缺失'}\``,
  `- 图标检查：\`${latest.appIcons || '缺失'}\``,
  `- H5 法律页线上状态：\`${latest.h5LegalDeployStatus || '缺失'}\``,
  `- 人工事项交接包：\`${latest.userActions || '缺失'}\``,
  '',
  '## 证据摘要',
  '',
  `- macOS 原生窗口：${index.evidenceSummary.desktopNative.passed ? '通过' : '缺失'}；顶栏颜色 \`${index.evidenceSummary.desktopNative.topbarColor || '-'}\`；登录弹窗对齐 \`${index.evidenceSummary.desktopNative.loginModalAlign || '-'}\`。`,
  `- 线上后端：${index.evidenceSummary.backendContract.passed ? '通过' : '缺失'}；目标 \`${index.evidenceSummary.backendContract.apiTarget || '-'}\`；测试用户 \`${index.evidenceSummary.backendContract.user || '-'}\`。`,
  `- 积分/会员：${index.evidenceSummary.backendContract.membership?.schemaReady ? '结构通过' : '缺失'}；level \`${index.evidenceSummary.backendContract.membership?.level ?? '-'}\`；points \`${index.evidenceSummary.backendContract.membership?.points ?? '-'}\`。`,
  `- 时安 agent：${index.evidenceSummary.backendContract.guide?.schemaReady ? '结构通过' : '缺失'}；工具模型数 \`${index.evidenceSummary.backendContract.agentOptions?.toolModels ?? '-'}\`；推荐 \`${(index.evidenceSummary.backendContract.recommendTools?.toolModels || []).join(',') || '-'}\`；引导状态 \`${index.evidenceSummary.backendContract.guide?.status || '-'}\`。`,
  `- Agent 流式真实后端：${index.evidenceSummary.agentStream.passed ? '通过' : '缺失'}；conversation_id \`${index.evidenceSummary.agentStream.conversationId || '-'}\`；事件数 \`${index.evidenceSummary.agentStream.eventCount}\`；扣减 \`${index.evidenceSummary.agentStream.usedCredit || '-'}\`；产物 \`${index.evidenceSummary.agentStream.artifactKeys.join(',') || '-'}\`。`,
  `- 核心功能接口：通过 \`${index.evidenceSummary.backendContract.coreFunctions.passed}/${index.evidenceSummary.backendContract.coreFunctions.total}\`；${index.evidenceSummary.backendContract.coreFunctions.items.map((item) => `${item.label}${item.ok && item.schemaReady ? ' OK' : ' 缺失'}`).join('，') || '-'}。`,
  `- 移动端后端请求能力：${index.evidenceSummary.mobileRuntime.passed ? '通过' : '缺失'}；检查文件数 \`${index.evidenceSummary.mobileRuntime.checkedFiles}\`。`,
  `- H5 法律页：线上正文 ${index.legalDeploy.onlineLegalPage ? '已部署' : '未部署'}；ICP ${index.legalDeploy.onlineIcpFooter ? '已检出' : '未检出'}；本地法律页 chunk \`${index.legalDeploy.localLegalChunk || '-'}\`。`,
  `- 全端后端矩阵：${index.platformBackendMatrix ? `${index.platformBackendMatrix.complete ? '全端完整' : '仍有缺口'}；完整平台 \`${index.platformBackendMatrix.summary?.complete ?? 0}/${index.platformBackendMatrix.summary?.total ?? 0}\`；后端请求证据可用 \`${index.platformBackendMatrix.summary?.backendReady ?? 0}/${index.platformBackendMatrix.summary?.total ?? 0}\`` : '缺失'}。`,
  '',
  '## 需要你明确批准后才能做',
  '',
  ...(index.approvalRequiredActions.length ? index.approvalRequiredActions.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 仍需最后人工处理',
  '',
  ...(index.userMustDoLast.length ? index.userMustDoLast.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 硬阻塞',
  '',
  ...(remainingHardBlocks.length ? remainingHardBlocks.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 索引问题',
  '',
  ...(issues.length ? issues.map((item) => `- ${item}`) : ['- 无。']),
].join('\n')}\n`)

writeFileSync(join(artifactsRoot, 'CURRENT_RELEASE_INDEX.md'), `当前索引：\`${rel(outDir)}/README.md\`\n`)
writeFileSync(join(artifactsRoot, 'current-index-latest.json'), `${JSON.stringify({ path: rel(outDir), generatedAt: index.generatedAt, passed: index.passed }, null, 2)}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: index.passed,
  usable: Object.fromEntries(Object.entries(usable).map(([key, value]) => [key, value?.path || ''])),
  remainingHardBlocks: remainingHardBlocks.length,
  issues,
}, null, 2))

if (strict && !index.passed) process.exit(1)
