#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.RELEASE_PROGRESS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.RELEASE_PROGRESS_OUT_DIR || join(root, 'artifacts', 'release-progress', `${localTimestamp()}-${version}`)
const strict = process.argv.includes('--strict') || process.env.RELEASE_PROGRESS_STRICT === '1'
const progressPointerPath = 'artifacts/RELEASE_PROGRESS.md'

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

function reportTime(path, fullPath = '') {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  if (Number.isFinite(time) && time > 0) return time
  return fullPath && existsSync(fullPath) ? statSync(fullPath).mtimeMs : 0
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
    .sort((a, b) => reportTime(b.reportPath, b.fullPath) - reportTime(a.reportPath, a.fullPath) || b.name.localeCompare(a.name))
  return dirs[0] ? `${parent}/${dirs[0].name}` : ''
}

function latestFile(parent, suffix) {
  const fullParent = join(root, parent)
  if (!existsSync(fullParent)) return ''
  const files = readdirSync(fullParent)
    .map((name) => ({ name, fullPath: join(fullParent, name), path: `${parent}/${name}` }))
    .filter((entry) => statSync(entry.fullPath).isFile() && entry.name.endsWith(suffix))
    .sort((a, b) => statSync(b.fullPath).mtimeMs - statSync(a.fullPath).mtimeMs || b.name.localeCompare(a.name))
  return files[0]?.path || ''
}

function readAt(dir, fileName) {
  return dir ? readJson(`${dir}/${fileName}`) : null
}

function status(id, label) {
  return { id, label }
}

function ratio(done, total) {
  return `${done || 0}/${total || 0}`
}

function asList(items) {
  return (items || []).filter(Boolean)
}

function boolText(value) {
  return value ? '是' : '否'
}

function markdownList(items, empty = '- 无。') {
  return items.length ? items.map((item) => `- ${item}`) : [empty]
}

function row(id, phase, state, evidence, remaining, owner, estimate, next) {
  return {
    id,
    phase,
    state: state.id,
    stateLabel: state.label,
    evidence: asList(evidence),
    remaining: asList(remaining),
    owner,
    estimate,
    next,
  }
}

const states = {
  done: status('done', '已完成'),
  active: status('active', '进行中'),
  waitingUser: status('waiting-user', '等你/账号/真机'),
  waitingExternal: status('waiting-external', '等外部审核'),
  deferred: status('deferred', '本批次暂停'),
  missing: status('missing', '缺证据'),
}

const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatforms = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const activePlatforms = releaseScope.activePlatforms || []

const latest = {
  currentIndex: readJson('artifacts/current-index-latest.json')?.path || '',
  currentDownloads: existsSync(join(root, 'artifacts', 'current-downloads', 'manifest.json')) ? 'artifacts/current-downloads' : '',
  releasePackage: latestDir('artifacts/release-packages', 'upload-manifest.json'),
  readinessJson: latestFile('artifacts/release-readiness', '.json'),
  readinessMd: latestFile('artifacts/release-readiness', '.md'),
  platformBackendMatrix: latestDir('artifacts/platform-backend-matrix', 'report.json'),
  finalPackageCompleteness: latestDir('artifacts/final-package-completeness', 'report.json'),
  finalPackagePlan: latestDir('artifacts/final-package-plan', 'report.json'),
  lowImpactStatus: latestDir('artifacts/low-impact-status', 'report.json'),
  allPlatformStatus: latestDir('artifacts/all-platform-status', 'report.json'),
  externalHandoff: latestDir('artifacts/external-handoff', 'manifest.json'),
  releaseFinalizePlan: latestDir('artifacts/release-finalize', 'report.json'),
  artifactPrune: latestDir('artifacts/artifact-prune', 'report.json'),
  packageCleanup: latestDir('artifacts/package-binary-cleanup', 'report.json'),
  realUserRoster: latestDir('artifacts/real-user-roster', 'report.json'),
  realUserDispatch: latestDir('artifacts/real-user-dispatch', 'report.json'),
  realUserResults: latestFile('artifacts/real-user-results', '.json'),
  agentStreamSmoke: latestDir('artifacts/agent-stream-smoke', 'report.json'),
  desktopOnlineLoginSmoke: latestDir('artifacts/desktop-online-login-smoke', 'report.json'),
  h5LegalDeployStatus: latestDir('artifacts/h5-legal-deploy-status', 'report.json'),
}

const currentIndex = readAt(latest.currentIndex, 'index.json')
const currentDownloads = readJson('artifacts/current-downloads/manifest.json')
const releasePackage = readAt(latest.releasePackage, 'upload-manifest.json')
const readiness = readJson(latest.readinessJson)
const platformBackendMatrix = readAt(latest.platformBackendMatrix, 'report.json')
const finalPackageCompleteness = readAt(latest.finalPackageCompleteness, 'report.json')
const finalPackagePlan = readAt(latest.finalPackagePlan, 'report.json')
const lowImpactStatus = readAt(latest.lowImpactStatus, 'report.json')
const allPlatformStatus = readAt(latest.allPlatformStatus, 'report.json')
const externalHandoff = readAt(latest.externalHandoff, 'manifest.json')
const releaseFinalizePlan = readAt(latest.releaseFinalizePlan, 'report.json')
const artifactPrune = readAt(latest.artifactPrune, 'report.json')
const realUserRoster = readAt(latest.realUserRoster, 'report.json')
const realUserDispatch = readAt(latest.realUserDispatch, 'report.json')
const realUserResults = readJson(latest.realUserResults)
const agentStreamSmoke = readAt(latest.agentStreamSmoke, 'report.json')
const h5LegalDeployStatus = readAt(latest.h5LegalDeployStatus, 'report.json')

const activeMatrixRows = (platformBackendMatrix?.platforms || []).filter((platform) => !deferredPlatforms.has(platform.id))
const backendReadyCount = activeMatrixRows.filter((platform) => platform.backendReady).length
const packageReadyCount = activeMatrixRows.filter((platform) => platform.packageReady).length
const deviceReadyCount = activeMatrixRows.filter((platform) => platform.deviceReady).length
const currentDownloadsPassed = currentDownloads?.passed === true
const packageCompletenessPassed = finalPackageCompleteness?.passed === true
const agentStreamPassed = agentStreamSmoke?.passed === true || currentIndex?.evidenceSummary?.agentStream?.passed === true
const backendReady = activeMatrixRows.length > 0 && backendReadyCount === activeMatrixRows.length && agentStreamPassed
const packageReady = activeMatrixRows.length > 0 && packageReadyCount === activeMatrixRows.length && currentDownloadsPassed && packageCompletenessPassed
const deviceReady = activeMatrixRows.length > 0 && deviceReadyCount === activeMatrixRows.length
const finalPlanReady = finalPackagePlan?.readyToRunFinalPackageRefresh === true
const externalHandoffReady = Boolean(externalHandoff?.tasks?.length)
const deferredHandoffTaskIds = new Set([
  deferredPlatforms.has('ios') && 'ios-testflight',
  deferredPlatforms.has('harmony') && 'harmony-package',
].filter(Boolean))
const externalHandoffTasks = externalHandoff?.tasks || []
const currentHandoffTasks = externalHandoffTasks.filter((task) => !deferredHandoffTaskIds.has(task.id))
const lowImpactHeavyProcessCount = lowImpactStatus?.heavyProcesses?.length || 0
const availableGiB = lowImpactStatus?.disk?.availableGiB ?? null
const readinessSummary = readiness?.summary || {}
const hardBlocks = releasePackage?.missingHardBlocks || currentIndex?.remainingHardBlocks || []
const userLastBlocks = hardBlocks.filter((item) => /人工|真实用户|商店|后台|开发者|备案|域名|法律|提交|名册/.test(item))

const currentFileMap = Object.fromEntries((currentDownloads?.files || []).map((file) => [file.label, file]))
const platformDeliverables = {
  h5: ['https://shianjieyouwu.com/', currentIndex?.evidenceSummary?.backendContract?.apiTarget].filter(Boolean),
  android: [currentFileMap['shian-current-android-debug.apk']?.path, currentFileMap['shian-current-android-debug.aab']?.path].filter(Boolean),
  macos: [currentFileMap['shian-current-macos-arm64.dmg']?.path, currentFileMap['shian-current-macos-arm64.app.zip']?.path].filter(Boolean),
  windows: [currentFileMap['shian-current-windows-x64.exe']?.path].filter(Boolean),
}

const progressRows = [
  row(
    'storage.cleanup',
    '存储清理与保护 current-downloads',
    artifactPrune || currentIndex?.artifactPrune ? states.done : states.active,
    [
      latest.artifactPrune && `${latest.artifactPrune}/report.json`,
      latest.currentDownloads && 'artifacts/current-downloads/manifest.json',
    ],
    artifactPrune || currentIndex?.artifactPrune ? [] : ['缺少最新 artifacts:prune 报告'],
    '我',
    artifactPrune || currentIndex?.artifactPrune ? '已完成；后续只做增量清理' : '10 分钟',
    '继续保护 current-downloads、release-inbox、证书和软著材料。'
  ),
  row(
    'packages.current',
    '当前批次安装包与固定下载入口',
    packageReady ? states.done : states.active,
    [
      currentDownloadsPassed && 'artifacts/current-downloads/manifest.json',
      latest.currentIndex && `${latest.currentIndex}/index.json`,
      latest.finalPackageCompleteness && `${latest.finalPackageCompleteness}/report.json`,
    ],
    [
      !currentDownloadsPassed && '固定下载入口未通过',
      !packageCompletenessPassed && '最终安装包完整性未通过',
      packageReadyCount < activeMatrixRows.length && `平台包文件未齐：${ratio(packageReadyCount, activeMatrixRows.length)}`,
    ],
    '我',
    packageReady ? '已完成；最终包变更后再统一刷新' : '30-60 分钟，取决于缺失包是否需要重打',
    '安装包最后统一刷新，减少重复打包。'
  ),
  row(
    'backend.requests',
    '线上登录、积分、核心接口、Agent stream 后端请求',
    backendReady ? states.done : states.active,
    [
      latest.desktopOnlineLoginSmoke && `${latest.desktopOnlineLoginSmoke}/report.json`,
      latest.agentStreamSmoke && `${latest.agentStreamSmoke}/report.json`,
      latest.platformBackendMatrix && `${latest.platformBackendMatrix}/report.json`,
    ],
    [
      !backendReady && `后端请求证据未齐：${ratio(backendReadyCount, activeMatrixRows.length)}`,
      !agentStreamPassed && '真实 Agent stream 后端 smoke 未通过',
    ],
    '我',
    backendReady ? '已完成；后续包变更后复跑 smoke' : '30-90 分钟',
    '只用线上登录逻辑，不改生产账号资产。'
  ),
  row(
    'device.real-machine',
    '真机安装、登录、积分、卸载/截图回收',
    deviceReady ? states.done : states.waitingUser,
    [
      latest.realUserRoster && `${latest.realUserRoster}/report.json`,
      latest.realUserDispatch && `${latest.realUserDispatch}/report.json`,
      latest.realUserResults,
    ],
    [
      !deviceReady && `当前批次真机证据未齐：${ratio(deviceReadyCount, activeMatrixRows.length)}`,
      realUserRoster?.passed !== true && '真实用户测试名册未通过',
      realUserResults?.passed !== true && '真实用户回收结果未通过或缺失',
    ],
    '你/真机测试人，我负责收件和复核',
    '你安排设备后通常 0.5-1 天；没有设备则无法闭环',
    '先测 Android、macOS、Windows、H5；iOS/鸿蒙后续批次。'
  ),
  row(
    'handoff.external',
    '外部回传目录和最后材料收件',
    externalHandoffReady ? states.done : states.active,
    [
      latest.externalHandoff && `${latest.externalHandoff}/manifest.json`,
      latest.externalHandoff && `${latest.externalHandoff}/README.md`,
    ],
    [
      !externalHandoffReady && '缺少外部回传清单',
    ],
    '我',
    externalHandoffReady ? '已完成；等你把当前批次真机/后台材料放到对应目录' : '10 分钟',
    '当前批次材料按 handoff 目录回传；iOS/鸿蒙目录保留但后续批次再用。'
  ),
  row(
    'stores.compliance',
    '商店、备案、域名、法律 URL 和账号后台证据',
    userLastBlocks.length ? states.waitingUser : states.done,
    [
      latest.releasePackage && `${latest.releasePackage}/upload-manifest.json`,
      latest.h5LegalDeployStatus && `${latest.h5LegalDeployStatus}/report.json`,
      latest.readinessMd,
    ],
    userLastBlocks,
    '最后你确认/登录后台，我负责整理和复核',
    '资料齐后 0.5-1 天整理；商店审核另算',
    '这些是最后处理项，不抢在安装包和功能验证前面。'
  ),
  row(
    'final.refresh',
    '最终统一刷新安装包、索引、Release 草稿包',
    packageReady && backendReady && !deviceReady ? states.active : (packageReady && backendReady && deviceReady && !userLastBlocks.length ? states.done : states.waitingUser),
    [
      latest.currentIndex && `${latest.currentIndex}/README.md`,
      latest.releasePackage && `${latest.releasePackage}/RELEASE_NOTES.md`,
      currentDownloadsPassed && 'artifacts/current-downloads/manifest.json',
      latest.finalPackagePlan && `${latest.finalPackagePlan}/report.json`,
      latest.releaseFinalizePlan && `${latest.releaseFinalizePlan}/report.json`,
    ],
    [
      !finalPlanReady && '最终统一刷新计划未 ready',
      !deviceReady && '等待真机/真实用户回传后再做最终刷新',
      userLastBlocks.length > 0 && '等待最后人工/后台/法律项清零后再标记正式候选',
    ],
    '我',
    '所有回传到齐后 15-30 分钟',
    '最后一次跑 release:current-index、release:current-downloads、release:package、release:summary。'
  ),
]

const platformRows = activeMatrixRows.map((platform) => ({
  id: platform.id,
  label: platform.label,
  packageReady: platform.packageReady === true,
  backendReady: platform.backendReady === true,
  deviceReady: platform.deviceReady === true,
  deliverables: platformDeliverables[platform.id] || [],
  missing: platform.missing || [],
}))

const deferredRows = [...deferredPlatforms].map((id) => ({
  id,
  label: id === 'ios' ? 'iOS / iPadOS' : (id === 'harmony' ? '鸿蒙 / AppGallery' : id),
  state: states.deferred.id,
  reason: (releaseScope.deferredPlatforms || []).find((item) => (typeof item === 'string' ? item : item.id) === id)?.reason || '本批次暂停',
}))

const agentNextActions = [
  !deviceReady && '继续准备真机/真实用户收件表，收到截图后跑 real-user:check、platform:backend-matrix、release:progress。',
  packageReady && backendReady && '保持安装包不反复刷新；只有修复实际问题后才重跑最终包。',
  currentDownloadsPassed && '保留 artifacts/current-downloads 固定入口，不清理。',
].filter(Boolean)

const userLastActions = [
  ...userLastBlocks,
  !deviceReady && '提供 Android/macOS/Windows/H5 真机或真实浏览器测试截图与结果。',
].filter(Boolean)

const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  complete: packageReady && backendReady && deviceReady && userLastBlocks.length === 0,
  releaseScope: {
    currentBatch: releaseScope.currentBatch || '',
    activePlatforms,
    deferredPlatforms: [...deferredPlatforms],
  },
  summary: {
    packages: ratio(packageReadyCount, activeMatrixRows.length),
    backend: ratio(backendReadyCount, activeMatrixRows.length),
    devices: ratio(deviceReadyCount, activeMatrixRows.length),
    readiness: readinessSummary,
    currentDownloadsPassed,
    agentStreamPassed,
    finalPlanReady,
    externalHandoffTasks: externalHandoffTasks.length,
    currentHandoffTasks: currentHandoffTasks.length,
    deferredHandoffTasks: deferredHandoffTaskIds.size,
    lowImpactHeavyProcesses: lowImpactHeavyProcessCount,
    availableGiB,
    allPlatformBlockers: allPlatformStatus?.blockers?.length || 0,
    hardBlocks: hardBlocks.length,
  },
  latest,
  progressRows,
  platformRows,
  deferredRows,
  agentNextActions,
  userLastActions,
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'progress.json'), `${JSON.stringify(report, null, 2)}\n`)

const phaseTable = progressRows.map((item) => `| ${item.phase} | ${item.stateLabel} | ${item.owner} | ${item.estimate} | ${item.evidence.join('<br>') || '-'} | ${item.remaining.join('<br>') || '-'} | ${item.next} |`)
const platformTable = platformRows.map((item) => `| ${item.label} | ${boolText(item.packageReady)} | ${boolText(item.backendReady)} | ${boolText(item.deviceReady)} | ${item.deliverables.map((entry) => `\`${entry}\``).join('<br>') || '-'} | ${item.missing.join('<br>') || '-'} |`)

writeFileSync(join(outDir, 'README.md'), `${[
  '# 当前发行进度表',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 当前批次：${report.releaseScope.currentBatch || '未配置'}`,
  `> 范围：${activePlatforms.join('、') || '未配置'}；暂停：${report.releaseScope.deferredPlatforms.join('、') || '无'}`,
  '> 原则：安装包优先，后端请求必须验证，用户亲自做的商店/账号/真机事项放最后。',
  `> 结论：${report.complete ? '当前目标已完成。' : '安装包和后端请求已优先推进；剩余主要是最后人工/真机/商店项。'}`,
  '',
  '## 总进度',
  '',
  `- 安装包：${report.summary.packages}`,
  `- 后端请求：${report.summary.backend}`,
  `- 真机证据：${report.summary.devices}`,
  `- 固定下载入口：${currentDownloadsPassed ? '通过' : '未通过'}`,
  `- Agent stream：${agentStreamPassed ? '通过' : '未通过'}`,
  `- 最终刷新计划：${finalPlanReady ? 'ready' : '未 ready'}`,
  `- 外部回传任务：当前批次 ${currentHandoffTasks.length}/${externalHandoffTasks.length}；后续批次 ${deferredHandoffTaskIds.size}`,
  `- 低影响状态：${lowImpactHeavyProcessCount ? `检测到 ${lowImpactHeavyProcessCount} 个发行相关进程` : '无发行重负载进程'}；剩余空间 ${availableGiB ?? '-'} GiB`,
  `- 全平台状态阻塞：${allPlatformStatus?.blockers?.length || 0}`,
  `- Readiness：READY ${readinessSummary.ready ?? 0} / PARTIAL ${readinessSummary.partial ?? 0} / MISSING ${readinessSummary.missing ?? 0}`,
  `- Release 硬阻塞：${hardBlocks.length}`,
  '',
  '## 阶段进度表',
  '',
  '| 阶段 | 状态 | 负责人 | 预计 | 证据 | 剩余 | 下一步 |',
  '| --- | --- | --- | --- | --- | --- | --- |',
  ...phaseTable,
  '',
  '## 平台进度表',
  '',
  '| 平台 | 包文件 | 后端请求 | 真机证据 | 当前交付物 | 缺口 |',
  '| --- | --- | --- | --- | --- | --- |',
  ...(platformTable.length ? platformTable : ['| - | - | - | - | - | 缺少 platform:backend-matrix 报告 |']),
  '',
  '## 本批次暂停平台',
  '',
  ...(deferredRows.length ? deferredRows.map((item) => `- ${item.label}：${item.reason}`) : ['- 无。']),
  '',
  '## 我下一步能继续做',
  '',
  ...markdownList(agentNextActions),
  '',
  '## 最后需要你或外部后台处理',
  '',
  ...markdownList(userLastActions),
].join('\n')}\n`)

writeFileSync(join(root, progressPointerPath), `当前进度表：\`${rel(outDir)}/README.md\`\n`)
writeFileSync(join(root, 'artifacts', 'release-progress-latest.json'), `${JSON.stringify({ path: rel(outDir), generatedAt: report.generatedAt, complete: report.complete }, null, 2)}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  complete: report.complete,
  packages: report.summary.packages,
  backend: report.summary.backend,
  devices: report.summary.devices,
  currentDownloadsPassed,
  hardBlocks: hardBlocks.length,
}, null, 2))

if (strict && !report.complete) process.exit(1)
