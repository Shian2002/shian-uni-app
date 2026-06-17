#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.PLATFORM_BACKEND_MATRIX_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.PLATFORM_BACKEND_MATRIX_OUT_DIR || join(root, 'artifacts', 'platform-backend-matrix', `${localTimestamp()}-${version}`)
const strict = process.argv.includes('--strict') || process.env.PLATFORM_BACKEND_MATRIX_STRICT === '1'
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const activePlatformIds = new Set((releaseScope.activePlatforms || []).filter(Boolean))
const deferredPlatformIds = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))

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
    .sort((a, b) => {
      const byTime = reportTime(b.reportPath, b.fullPath) - reportTime(a.reportPath, a.fullPath)
      return byTime || b.name.localeCompare(a.name)
    })
  return dirs[0] ? `${parent}/${dirs[0].name}` : ''
}

function jsonAt(dir, fileName) {
  return dir ? readJson(`${dir}/${fileName}`) : null
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(join(root, path))).digest('hex')
}

function fileInfo(path) {
  if (!path || !existsSync(join(root, path)) || !statSync(join(root, path)).isFile()) return null
  const stat = statSync(join(root, path))
  return {
    path,
    bytes: stat.size,
    sha256: sha256(path),
    mtime: new Date(stat.mtimeMs).toISOString(),
  }
}

function currentDownload(label) {
  const item = (currentDownloads?.files || []).find((file) => file.label === label)
  const info = fileInfo(item?.path || '')
  return info ? { ...info, manifestSha256: item?.sha256 || '', source: item?.source || '' } : null
}

function windowsPackageFreshness(windowsExe, rebuildReport, h5) {
  if (!windowsExe) {
    return {
      fresh: false,
      issue: 'Windows EXE 文件缺失',
    }
  }
  if (!rebuildReport) {
    return {
      fresh: false,
      issue: 'Windows 重建报告缺失，无法证明当前 EXE 为最新 H5 产物',
    }
  }
  const installer = rebuildReport.files?.installer || {}
  const builtH5 = rebuildReport.files?.h5 || {}
  if (rebuildReport.passed !== true) {
    return {
      fresh: false,
      issue: `Windows 最新重建未通过：${(rebuildReport.issues || []).join('；') || '未知原因'}`,
    }
  }
  if (!installer.sha256 || installer.sha256 !== windowsExe.sha256) {
    return {
      fresh: false,
      issue: 'Windows 当前 EXE 与最新通过的重建报告 SHA-256 不一致',
    }
  }
  if (!h5 || !builtH5.sha256 || builtH5.sha256 !== h5.sha256) {
    return {
      fresh: false,
      issue: 'Windows 安装器不是最新 H5 构建后的产物',
    }
  }
  return {
    fresh: true,
    issue: '',
  }
}

function checkByName(report, name) {
  return (report?.checks || []).find((item) => item.name === name) || null
}

function backendContract(report) {
  const required = [
    'health',
    'login',
    'me',
    'membership',
    'points-log',
    'comprehensive-options',
    'comprehensive-recommend-tools',
    'comprehensive-guide',
    'comprehensive-conversations',
    'ziwei-info',
    'huangli',
    'bazi-paipan',
    'bazi-shian-pro',
    'ziwei-pan',
    'qimen-paipan',
    'meihua-paipan',
    'liuyao-paipan',
    'zeji',
    'records',
    'collections',
  ]
  const checks = Object.fromEntries(required.map((name) => [name, checkByName(report, name)]))
  const missing = required.filter((name) => !checks[name] || checks[name].ok === false || checks[name].passed === false)
  return {
    passed: report?.passed === true && missing.length === 0,
    apiTarget: report?.apiTarget || '',
    user: report?.qaUser || '',
    required,
    missing,
    membership: checks.membership ? {
      level: checks.membership.level,
      points: checks.membership.points,
      schemaReady: checks.membership.schemaReady === true,
    } : null,
    pointsLog: checks['points-log'] ? {
      total: checks['points-log'].total,
      logsReturned: checks['points-log'].logsReturned,
      schemaReady: checks['points-log'].schemaReady === true,
    } : null,
    agent: {
      optionsReady: checks['comprehensive-options']?.schemaReady === true,
      recommendReady: checks['comprehensive-recommend-tools']?.schemaReady === true,
      guideReady: checks['comprehensive-guide']?.schemaReady === true,
      conversationsReady: checks['comprehensive-conversations']?.schemaReady === true,
      recommendedTools: checks['comprehensive-recommend-tools']?.toolModels || [],
    },
    coreFunctions: {
      ziweiInfoReady: checks['ziwei-info']?.schemaReady === true,
      huangliReady: checks.huangli?.schemaReady === true,
      baziPaipanReady: checks['bazi-paipan']?.schemaReady === true,
      baziProReady: checks['bazi-shian-pro']?.schemaReady === true,
      ziweiPanReady: checks['ziwei-pan']?.schemaReady === true,
      qimenReady: checks['qimen-paipan']?.schemaReady === true,
      meihuaReady: checks['meihua-paipan']?.schemaReady === true,
      liuyaoReady: checks['liuyao-paipan']?.schemaReady === true,
      zejiReady: checks.zeji?.schemaReady === true,
      recordsReady: checks.records?.schemaReady === true,
      collectionsReady: checks.collections?.schemaReady === true,
    },
  }
}

function artifactMetadataPlatform(platform) {
  return (artifactMetadata?.platforms || []).find((item) => item.platform === platform || item.id === platform) || null
}

function metadataReady(row) {
  return row?.readiness === 'ready' || row?.status === 'ready' || row?.ready === true
}

function metadataValue(row, field) {
  return row?.metadata?.[field] ?? row?.[field]
}

function metadataEvidenceReady(row, field) {
  const value = metadataValue(row, field)
  if (Array.isArray(value)) return value.length > 0
  return Boolean(value)
}

function missingFrom(...groups) {
  return [...new Set(groups.flat().filter(Boolean))]
}

function platformRow({ id, label, packageFiles, packageReady: explicitPackageReady = null, backendMode, backendReady, deviceReady, metadataReady, evidence, missing }) {
  const packageReady = explicitPackageReady === null ? packageFiles.length > 0 && packageFiles.every(Boolean) : explicitPackageReady
  const complete = packageReady && backendReady && deviceReady && metadataReady && missing.length === 0
  const deferred = deferredPlatformIds.has(id)
  const active = activePlatformIds.size ? activePlatformIds.has(id) : !deferred
  return {
    id,
    label,
    active,
    deferred,
    complete,
    packageReady,
    backendReady,
    backendMode,
    deviceReady,
    metadataReady,
    packageFiles: packageFiles.filter(Boolean),
    evidence: evidence.filter(Boolean),
    missing,
  }
}

const latest = {
  desktopOnlineLoginSmoke: latestDir('artifacts/desktop-online-login-smoke', 'report.json'),
  agentStreamSmoke: latestDir('artifacts/agent-stream-smoke', 'report.json'),
  desktopSmoke: latestDir('artifacts/desktop-smoke', 'report.json'),
  desktopWindowsRebuild: latestDir('artifacts/desktop-windows-rebuild', 'report.json'),
  mobileApiEvidence: latestDir('artifacts/mobile-api-evidence', 'manifest.json'),
  artifactMetadata: latestDir('artifacts/release-artifact-metadata', 'report.json'),
  h5LegalDeployStatus: latestDir('artifacts/h5-legal-deploy-status', 'report.json'),
  currentDownloads: existsSync(join(root, 'artifacts', 'current-downloads', 'manifest.json')) ? 'artifacts/current-downloads' : '',
}

const desktopOnlineLoginSmoke = jsonAt(latest.desktopOnlineLoginSmoke, 'report.json')
const agentStreamSmoke = jsonAt(latest.agentStreamSmoke, 'report.json')
const desktopSmoke = jsonAt(latest.desktopSmoke, 'report.json')
const desktopWindowsRebuild = jsonAt(latest.desktopWindowsRebuild, 'report.json')
const mobileApiEvidence = jsonAt(latest.mobileApiEvidence, 'manifest.json')
const artifactMetadata = jsonAt(latest.artifactMetadata, 'report.json')
const h5LegalDeployStatus = jsonAt(latest.h5LegalDeployStatus, 'report.json')
const currentDownloads = jsonAt(latest.currentDownloads, 'manifest.json')

const contract = backendContract(desktopOnlineLoginSmoke)
const agentStreamReady = agentStreamSmoke?.passed === true
const mobileRuntimeReady = mobileApiEvidence?.passed === true
const h5LegalReady = h5LegalDeployStatus?.onlineLegalPage === true || h5LegalDeployStatus?.online?.deployedLegalPage === true

const files = {
  macosDmg: currentDownload('shian-current-macos-arm64.dmg'),
  macosAppZip: currentDownload('shian-current-macos-arm64.app.zip'),
  windowsExe: currentDownload('shian-current-windows-x64.exe'),
  androidApk: currentDownload('shian-current-android-debug.apk'),
  androidAab: currentDownload('shian-current-android-debug.aab'),
  appIcon: currentDownload('shian-current-app-icon-1024.png'),
  h5Index: fileInfo('dist/build/h5/index.html'),
}

const freshness = {
  windows: windowsPackageFreshness(files.windowsExe, desktopWindowsRebuild, files.h5Index),
}

const metadata = {
  macos: artifactMetadataPlatform('macos'),
  windows: artifactMetadataPlatform('windows'),
  android: artifactMetadataPlatform('android'),
  ios: artifactMetadataPlatform('ios'),
  harmony: artifactMetadataPlatform('harmony'),
}

const platforms = [
  platformRow({
    id: 'macos',
    label: 'macOS',
    packageFiles: [files.macosDmg],
    backendMode: contract.passed && agentStreamReady ? 'real-electron-online-smoke-plus-agent-stream' : 'missing-real-backend-or-agent-stream',
    backendReady: contract.passed && agentStreamReady,
    deviceReady: Boolean(metadata.macos?.installEvidencePaths?.length || desktopSmoke?.passed === true),
    metadataReady: metadataReady(metadata.macos),
    evidence: [latest.currentDownloads, latest.desktopOnlineLoginSmoke, latest.agentStreamSmoke, latest.desktopSmoke, latest.artifactMetadata],
    missing: missingFrom(
      files.macosDmg ? [] : ['macOS DMG 文件缺失'],
      contract.passed ? [] : ['macOS 线上登录/积分/时安agent 后端 smoke 缺失或未通过'],
      agentStreamReady ? [] : ['macOS 共享 Agent stream 真实后端证据缺失或未通过'],
      metadata.macos ? [] : ['macOS build-metadata 缺失'],
      metadataValue(metadata.macos, 'codeSigningStatus') === 'signed' ? [] : ['Apple Developer ID 签名/公证最后处理'],
    ),
  }),
  platformRow({
    id: 'windows',
    label: 'Windows',
    packageFiles: [files.windowsExe],
    packageReady: Boolean(files.windowsExe) && freshness.windows.fresh,
    backendMode: contract.passed && agentStreamReady ? 'shared-electron-online-smoke-plus-agent-stream' : 'missing-shared-backend-or-agent-stream',
    backendReady: contract.passed && agentStreamReady,
    deviceReady: Boolean(metadata.windows?.installEvidencePaths?.length),
    metadataReady: metadataReady(metadata.windows),
    evidence: [latest.currentDownloads, latest.desktopWindowsRebuild, latest.desktopOnlineLoginSmoke, latest.agentStreamSmoke, latest.artifactMetadata],
    missing: missingFrom(
      files.windowsExe ? [] : ['Windows EXE 文件缺失'],
      freshness.windows.fresh ? [] : [freshness.windows.issue],
      contract.passed ? [] : ['Windows 线上登录/积分/时安agent 后端 smoke 缺失或未通过'],
      agentStreamReady ? [] : ['Windows 共享 Agent stream 真实后端证据缺失或未通过'],
      metadata.windows ? [] : ['Windows build-metadata 缺失'],
      metadataValue(metadata.windows, 'codeSigningStatus') === 'signed' ? [] : ['Windows 代码签名最后处理'],
      metadata.windows?.installEvidencePaths?.length ? [] : ['Windows 真机安装/卸载截图缺失'],
    ),
  }),
  platformRow({
    id: 'android',
    label: 'Android',
    packageFiles: [files.androidApk, files.androidAab],
    backendMode: mobileRuntimeReady && contract.passed && agentStreamReady ? 'runtime-config-plus-shared-contract-agent-stream' : 'missing-mobile-runtime-contract-or-agent-stream',
    backendReady: mobileRuntimeReady && contract.passed && agentStreamReady,
    deviceReady: metadataEvidenceReady(metadata.android, 'deviceTestEvidence'),
    metadataReady: metadataReady(metadata.android),
    evidence: [latest.currentDownloads, latest.mobileApiEvidence, latest.desktopOnlineLoginSmoke, latest.agentStreamSmoke, latest.artifactMetadata],
    missing: missingFrom(
      files.androidApk ? [] : ['Android APK 文件缺失'],
      files.androidAab ? [] : ['Android AAB 文件缺失'],
      mobileRuntimeReady ? [] : ['Android 移动运行时代码请求线上后端证据缺失'],
      contract.passed ? [] : ['共享后端登录/积分/时安agent 契约 smoke 缺失'],
      agentStreamReady ? [] : ['共享 Agent stream 真实后端证据缺失或未通过'],
      metadataEvidenceReady(metadata.android, 'deviceTestEvidence') ? [] : ['Android 真机登录/积分/时安agent 截图缺失'],
      metadata.android ? [] : ['Android build-metadata 缺失'],
    ),
  }),
  platformRow({
    id: 'ios',
    label: 'iOS / iPadOS',
    packageFiles: [],
    packageReady: false,
    backendMode: mobileRuntimeReady ? 'runtime-config-only' : 'missing-mobile-runtime',
    backendReady: mobileRuntimeReady,
    deviceReady: metadataEvidenceReady(metadata.ios, 'deviceTestEvidence'),
    metadataReady: metadataReady(metadata.ios),
    evidence: [latest.mobileApiEvidence, latest.artifactMetadata],
    missing: missingFrom(
      ['iOS IPA/TestFlight 构建产物缺失'],
      mobileRuntimeReady ? [] : ['iOS 移动运行时代码请求线上后端证据缺失'],
      metadataEvidenceReady(metadata.ios, 'deviceTestEvidence') ? [] : ['iPhone/iPad 真机登录/积分/时安agent 截图缺失'],
      metadata.ios ? [] : ['iOS build-metadata 缺失'],
    ),
  }),
  platformRow({
    id: 'harmony',
    label: '鸿蒙',
    packageFiles: [],
    packageReady: false,
    backendMode: mobileRuntimeReady ? 'runtime-config-only' : 'missing-mobile-runtime',
    backendReady: mobileRuntimeReady,
    deviceReady: metadataEvidenceReady(metadata.harmony, 'deviceTestEvidence'),
    metadataReady: metadataReady(metadata.harmony),
    evidence: [latest.mobileApiEvidence, latest.artifactMetadata],
    missing: missingFrom(
      ['鸿蒙 HAP/AppGallery 构建产物缺失'],
      mobileRuntimeReady ? [] : ['鸿蒙移动运行时代码请求线上后端证据缺失'],
      metadataEvidenceReady(metadata.harmony, 'deviceTestEvidence') ? [] : ['鸿蒙真机登录/积分/时安agent 截图缺失'],
      metadata.harmony ? [] : ['鸿蒙 build-metadata 缺失'],
    ),
  }),
  platformRow({
    id: 'h5',
    label: 'H5',
    packageFiles: [],
    packageReady: true,
    backendMode: contract.passed && agentStreamReady ? 'shared-online-contract-plus-agent-stream' : 'missing-online-contract-or-agent-stream',
    backendReady: contract.passed && agentStreamReady,
    deviceReady: contract.passed && agentStreamReady,
    metadataReady: h5LegalReady,
    evidence: [latest.desktopOnlineLoginSmoke, latest.agentStreamSmoke, latest.h5LegalDeployStatus],
    missing: missingFrom(
      contract.passed ? [] : ['H5 线上登录/积分/时安agent 后端 smoke 缺失或未通过'],
      agentStreamReady ? [] : ['H5 Agent stream 真实后端证据缺失或未通过'],
      h5LegalReady ? [] : ['H5 法律页线上正文未部署，需要你明确批准后再执行 deploy:h5'],
    ),
  }),
]

const activePlatforms = platforms.filter((item) => item.active && !item.deferred)
const deferredPlatforms = platforms.filter((item) => item.deferred)

const summary = {
  total: activePlatforms.length,
  complete: activePlatforms.filter((item) => item.complete).length,
  packageReady: activePlatforms.filter((item) => item.packageReady).length,
  backendReady: activePlatforms.filter((item) => item.backendReady).length,
  deviceReady: activePlatforms.filter((item) => item.deviceReady).length,
  missingCount: activePlatforms.reduce((total, item) => total + item.missing.length, 0),
  deferred: deferredPlatforms.length,
}

const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  complete: activePlatforms.every((item) => item.complete),
  releaseScope: {
    configPath: 'configs/release/current-release-scope.json',
    currentBatch: releaseScope.currentBatch || '',
    activePlatforms: [...activePlatformIds],
    deferredPlatforms: [...deferredPlatformIds],
  },
  latest,
  files,
  freshness,
  backendContract: contract,
  agentStream: {
    passed: agentStreamReady,
    evidence: latest.agentStreamSmoke,
    usedCredit: agentStreamSmoke?.streamSummary?.usedCredit || '',
    conversationId: agentStreamSmoke?.streamSummary?.conversationId || null,
    eventCount: agentStreamSmoke?.streamSummary?.eventCount || 0,
    artifactKeys: agentStreamSmoke?.streamSummary?.artifactKeys || [],
  },
  mobileRuntime: {
    passed: mobileRuntimeReady,
    checkedFiles: mobileApiEvidence?.checkedFiles?.length || 0,
    requiredRuntimeEvidence: mobileApiEvidence?.requiredRuntimeEvidence || [],
  },
  h5LegalDeploy: {
    onlineLegalPage: h5LegalReady,
    evidence: latest.h5LegalDeployStatus,
  },
  summary,
  platforms,
  deferredPlatforms,
  userMustDoLast: [
    'Apple Developer ID 签名和 notarization。',
    'Windows 代码签名。',
    'Android/Windows/macOS 真机安装、登录、积分、时安agent 和卸载截图。',
    'iOS IPA/TestFlight、鸿蒙 HAP/AppGallery 正式构建已延期到后续批次。',
    '明确批准后才能执行生产 H5 法律页部署：CONFIRM_H5_DEPLOY=shianjieyouwu.com bash deploy-h5-to-server.sh。',
    '开发者账号、商店后台、备案、隐私材料和提交编号截图。',
  ],
}

function tableRow(item) {
  return `| ${item.label} | ${item.deferred ? '延期' : '当前'} | ${item.packageReady ? '是' : '否'} | ${item.backendReady ? '是' : '否'} | ${item.deviceReady ? '是' : '否'} | ${item.backendMode} | ${item.missing.length ? item.missing.join('<br>') : '无'} |`
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# 全端后端能力矩阵',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.complete ? '全端安装包、后端请求和真机证据齐备。' : '仍有端缺少安装包、后端请求证据或真机证据。'}`,
  '',
  '## 汇总',
  '',
  `- 当前批次：${report.releaseScope.activePlatforms.join(', ') || '-'}`,
  `- 后续延期：${report.releaseScope.deferredPlatforms.join(', ') || '-'}`,
  `- 当前批次平台总数：${summary.total}`,
  `- 完整平台：${summary.complete}`,
  `- 安装包可用：${summary.packageReady}`,
  `- 后端请求证据可用：${summary.backendReady}`,
  `- 真机/安装证据可用：${summary.deviceReady}`,
  `- 缺口数：${summary.missingCount}`,
  '',
  '## 矩阵',
  '',
  '| 平台 | 本轮状态 | 包文件存在 | 后端请求可用 | 真机证据 | 后端证据模式 | 缺口 |',
  '| --- | --- | --- | --- | --- | --- | --- |',
  ...platforms.map(tableRow),
  '',
  '## 已真实请求后端',
  '',
  `- 桌面线上 smoke：${contract.passed ? '通过' : '缺失'}；目标 \`${contract.apiTarget || '-'}\`；用户 \`${contract.user || '-'}\`。`,
  `- 已覆盖接口：${contract.required.filter((name) => !contract.missing.includes(name)).join(', ') || '-'}`,
  `- 积分/会员：${contract.membership?.schemaReady ? '结构通过' : '缺失'}；points \`${contract.membership?.points ?? '-'}\`。`,
  `- 时安agent：options ${contract.agent.optionsReady ? '通过' : '缺失'}；recommend ${contract.agent.recommendReady ? '通过' : '缺失'}；guide ${contract.agent.guideReady ? '通过' : '缺失'}。`,
  `- Agent stream：${agentStreamReady ? '通过' : '缺失'}；证据 \`${latest.agentStreamSmoke || '-'}\`；conversation_id \`${report.agentStream.conversationId || '-'}\`；事件数 \`${report.agentStream.eventCount}\`。`,
  '',
  '## 已证明移动端会请求线上后端',
  '',
  `- 移动运行时证据：${mobileRuntimeReady ? '通过' : '缺失'}；检查文件数 \`${report.mobileRuntime.checkedFiles}\`。`,
  `- 运行时要求：${report.mobileRuntime.requiredRuntimeEvidence.join(', ') || '-'}`,
  '',
  '## 当前固定下载文件',
  '',
  ...Object.entries(files).map(([key, value]) => `- ${key}：${value ? `\`${value.path}\` SHA-256 \`${value.sha256}\`` : '缺失'}`),
  '',
  '## 最后必须人工处理',
  '',
  ...report.userMustDoLast.map((item) => `- ${item}`),
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  complete: report.complete,
  summary,
}, null, 2))

if (strict && !report.complete) process.exit(1)
