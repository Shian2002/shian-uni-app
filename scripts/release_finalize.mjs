#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.RELEASE_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.RELEASE_FINALIZE_DIR || join(root, 'artifacts', 'release-finalize', `${localTimestamp()}-${version}`)
const planOnly = process.argv.includes('--plan-only') || process.env.RELEASE_FINALIZE_PLAN_ONLY === '1'
const requiredFinalizeConfirm = `final-package-refresh:${version}`
const finalizeConfirm = process.env.CONFIRM_FINAL_PACKAGE_REFRESH || ''
const executionBlocked = !planOnly && finalizeConfirm !== requiredFinalizeConfirm
const windowsRebuildEnv = {
  DESKTOP_WINDOWS_REBUILD_TIMEOUT_MS: process.env.DESKTOP_WINDOWS_REBUILD_TIMEOUT_MS || '900000',
  DESKTOP_WINDOWS_REBUILD_SKIP_H5: '1',
  ELECTRON_MIRROR: process.env.ELECTRON_MIRROR || 'https://npmmirror.com/mirrors/electron/',
}
const strictPreflightEnv = { FINAL_PACKAGE_PREFLIGHT_STRICT: '1' }

const steps = [
  ['release:check', ['run', 'release:check']],
  ['platform:backend-matrix:pre', ['run', 'platform:backend-matrix']],
  ['release:final-package-plan:pre', ['run', 'release:final-package-plan']],
  ['release:final-preflight:pre', ['run', 'release:final-preflight'], strictPreflightEnv],
  ['artifacts:prune:dry-run:pre', ['run', 'artifacts:prune', '--', '--keep=2']],
  ['release:package-cleanup-plan:pre', ['run', 'release:package-cleanup-plan', '--', '--keep=2']],
  ['release:channel-builds', ['run', 'release:channel-builds']],
  ['build:app', ['run', 'build:app']],
  ['mobile:build-env', ['run', 'mobile:build-env']],
  ['mobile:toolchain-plan', ['run', 'mobile:toolchain-plan']],
  ['mobile:build-requests', ['run', 'mobile:build-requests']],
  ['mobile:api-evidence', ['run', 'mobile:api-evidence']],
  ['mobile:app-resource-packet', ['run', 'mobile:app-resource-packet']],
  ['mobile:hbuilderx-resources', ['run', 'mobile:hbuilderx-resources']],
  ['mobile:ios-local-build-attempt', ['run', 'mobile:ios-local-build-attempt']],
  ['mobile:hbuilderx-harmony-pack', ['run', 'mobile:hbuilderx-harmony-pack']],
  ['release:intake', ['run', 'release:intake']],
  ['release:artifact-metadata', ['run', 'release:artifact-metadata']],
  ['platform:handoff', ['run', 'platform:handoff']],
  ['product:launch-audit', ['run', 'product:launch-audit']],
  ['real-user:packet', ['run', 'real-user:packet']],
  ['real-user:roster', ['run', 'real-user:roster']],
  ['real-user:dispatch', ['run', 'real-user:dispatch']],
  ['real-user:check', ['run', 'real-user:check']],
  ['store:legal-urls', ['run', 'store:legal-urls']],
  ['store:privacy', ['run', 'store:privacy']],
  ['store:materials', ['run', 'store:materials']],
  ['store:submission-status', ['run', 'store:submission-status']],
  ['store:evidence-status', ['run', 'store:evidence-status']],
  ['store:account-access', ['run', 'store:account-access']],
  ['store:app-record', ['run', 'store:app-record']],
  ['domain:https', ['run', 'domain:https']],
  ['h5:legal-deploy-status', ['run', 'h5:legal-deploy-status']],
  ['desktop:release-status', ['run', 'desktop:release-status']],
  ['desktop:build:mac:arm64', ['run', 'desktop:build:mac:arm64']],
  ['desktop:refresh-macos-app-asar', ['run', 'desktop:refresh-macos-app-asar']],
  ['desktop:make-macos-dmg', ['run', 'desktop:make-macos-dmg']],
  ['desktop:build:win:x64:safe:skip-h5', ['run', 'desktop:build:win:x64:safe', '--', '--skip-h5'], windowsRebuildEnv],
  ['desktop:bundle', ['run', 'desktop:bundle']],
  ['desktop:verify-macos', ['run', 'desktop:verify-macos']],
  ['desktop:macos-user-packet', ['run', 'desktop:macos-user-packet']],
  ['desktop:build:win:x64:safe:verify', ['run', 'desktop:build:win:x64:safe', '--', '--verify-current'], windowsRebuildEnv],
  ['desktop:windows-user-packet', ['run', 'desktop:windows-user-packet']],
  ['release:app-icons', ['run', 'release:app-icons']],
  ['release:readiness', ['run', 'release:readiness']],
  ['release:user-actions', ['run', 'release:user-actions']],
  ['platform:backend-matrix', ['run', 'platform:backend-matrix']],
  ['release:final-package-plan', ['run', 'release:final-package-plan']],
  ['release:final-preflight', ['run', 'release:final-preflight'], strictPreflightEnv],
  ['release:try-now', ['run', 'release:try-now']],
  ['release:summary', ['run', 'release:summary']],
  ['release:package', ['run', 'release:package']],
  ['release:package-completeness:before-handoff', ['run', 'release:package-completeness']],
  ['release:package:with-completeness', ['run', 'release:package']],
  ['release:external-handoff', ['run', 'release:external-handoff']],
  ['release:current-index', ['run', 'release:current-index']],
  ['release:current-downloads', ['run', 'release:current-downloads']],
  ['release:package-completeness:after-downloads', ['run', 'release:package-completeness']],
  ['release:package:after-downloads', ['run', 'release:package']],
  ['store:packet', ['run', 'store:packet']],
  ['store:legal-urls:final', ['run', 'store:legal-urls']],
  ['store:privacy:final', ['run', 'store:privacy']],
  ['store:materials:final', ['run', 'store:materials']],
  ['store:submission-status:final', ['run', 'store:submission-status']],
  ['store:evidence-status:final', ['run', 'store:evidence-status']],
  ['store:account-access:final', ['run', 'store:account-access']],
  ['store:app-record:final', ['run', 'store:app-record']],
  ['domain:https:final', ['run', 'domain:https']],
  ['h5:legal-deploy-status:final', ['run', 'h5:legal-deploy-status']],
  ['desktop:release-status:final', ['run', 'desktop:release-status']],
  ['desktop:build:mac:arm64:final', ['run', 'desktop:build:mac:arm64']],
  ['desktop:refresh-macos-app-asar:final', ['run', 'desktop:refresh-macos-app-asar']],
  ['desktop:make-macos-dmg:final', ['run', 'desktop:make-macos-dmg']],
  ['desktop:build:win:x64:safe:skip-h5:final', ['run', 'desktop:build:win:x64:safe', '--', '--skip-h5'], windowsRebuildEnv],
  ['desktop:bundle:final', ['run', 'desktop:bundle']],
  ['desktop:verify-macos:final', ['run', 'desktop:verify-macos']],
  ['desktop:macos-user-packet:final', ['run', 'desktop:macos-user-packet']],
  ['desktop:build:win:x64:safe:verify:final', ['run', 'desktop:build:win:x64:safe', '--', '--verify-current'], windowsRebuildEnv],
  ['desktop:windows-user-packet:final', ['run', 'desktop:windows-user-packet']],
  ['release:app-icons:final', ['run', 'release:app-icons']],
  ['release:readiness:final', ['run', 'release:readiness']],
  ['release:user-actions:final', ['run', 'release:user-actions']],
  ['platform:backend-matrix:final', ['run', 'platform:backend-matrix']],
  ['release:final-package-plan:final', ['run', 'release:final-package-plan']],
  ['release:final-preflight:final', ['run', 'release:final-preflight'], strictPreflightEnv],
  ['artifacts:prune:dry-run:final', ['run', 'artifacts:prune', '--', '--keep=2']],
  ['release:package-cleanup-plan:final', ['run', 'release:package-cleanup-plan', '--', '--keep=2']],
  ['release:try-now:final', ['run', 'release:try-now']],
  ['release:summary:final', ['run', 'release:summary']],
  ['release:package:final', ['run', 'release:package']],
  ['release:package-completeness:before-handoff:final', ['run', 'release:package-completeness']],
  ['release:package:with-completeness:final', ['run', 'release:package']],
  ['release:external-handoff:final', ['run', 'release:external-handoff']],
  ['release:current-index:final', ['run', 'release:current-index']],
  ['release:current-downloads:final', ['run', 'release:current-downloads']],
  ['release:package-completeness:final', ['run', 'release:package-completeness']],
  ['release:package:after-downloads:final', ['run', 'release:package']],
  ['store:packet:final', ['run', 'store:packet']],
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

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
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

function npm(args, extraEnv = {}) {
  return execFileSync('npm', args, {
    cwd: root,
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    env: { ...process.env, ...extraEnv },
  })
}

function runStep(name, args, extraEnv = {}) {
  const startedAt = new Date().toISOString()
  try {
    const output = npm(args, extraEnv)
    return { name, command: `npm ${args.join(' ')}`, env: extraEnv, startedAt, finishedAt: new Date().toISOString(), passed: true, output: output.trim().slice(-3000) }
  } catch (error) {
    const stdout = String(error.stdout || '').trim()
    const stderr = String(error.stderr || '').trim()
    return {
      name,
      command: `npm ${args.join(' ')}`,
      env: extraEnv,
      startedAt,
      finishedAt: new Date().toISOString(),
      passed: false,
      output: stdout.slice(-3000),
      error: stderr.slice(-3000) || error.message,
    }
  }
}

function planStep(name, args, extraEnv = {}) {
  return {
    name,
    command: `npm ${args.join(' ')}`,
    env: extraEnv,
    planned: true,
    passed: null,
    output: '',
  }
}

function evidence() {
  const releasePackage = latestDir('artifacts/release-packages')
  const uploadManifest = releasePackage ? readJson(`${releasePackage}/upload-manifest.json`) : null
  const currentDownloads = existsSync(join(root, 'artifacts', 'current-downloads', 'manifest.json')) ? 'artifacts/current-downloads' : ''
  return {
    readiness: latestFile('artifacts/release-readiness', '.md'),
    userActions: latestDir('artifacts/release-user-actions'),
    tryNow: latestDir('artifacts/try-now'),
    productAudit: latestFile('artifacts/product-launch-audits', '.md'),
    releaseSummary: latestFile('artifacts/release-summaries', '.md'),
    channelBuilds: latestDir('artifacts/release-channel-builds'),
    mobileBuildEnv: latestDir('artifacts/mobile-build-env'),
    mobileApiEvidence: latestDir('artifacts/mobile-api-evidence'),
    platformBackendMatrix: latestDir('artifacts/platform-backend-matrix'),
    finalPackagePlan: latestDir('artifacts/final-package-plan'),
    finalPackagePreflight: latestDir('artifacts/final-package-preflight'),
    finalPackageCompleteness: latestDir('artifacts/final-package-completeness'),
    mobileAppResourcePacket: latestDir('artifacts/mobile-app-resource-packets'),
    artifactIntake: latestDir('artifacts/release-artifact-intake'),
    artifactMetadata: latestDir('artifacts/release-artifact-metadata'),
    releasePackage,
    releaseUploadManifest: releasePackage ? `${releasePackage}/upload-manifest.json` : '',
    externalHandoff: latestDir('artifacts/external-handoff'),
    currentIndex: latestDir('artifacts/current-index'),
    currentDownloads,
    currentDownloadsManifest: currentDownloads ? `${currentDownloads}/manifest.json` : '',
    storePacket: latestDir('artifacts/store-submission-packets'),
    storeSubmissionStatus: latestDir('artifacts/store-submission-status'),
    storeEvidenceStatus: latestDir('artifacts/store-evidence-status'),
    storeAccountAccess: latestDir('artifacts/store-account-access'),
    domainHttps: latestDir('artifacts/domain-https'),
    desktopReleaseStatus: latestDir('artifacts/desktop-release-status'),
    desktopDownloads: latestDir('artifacts/desktop-downloads'),
    desktopMacosInstall: latestDir('artifacts/desktop-macos-install'),
    desktopMacosUserPacket: latestDir('artifacts/desktop-macos-user-packets'),
    desktopWindowsRebuild: latestDir('artifacts/desktop-windows-rebuild'),
    desktopWindowsUserPacket: latestDir('artifacts/desktop-windows-user-packets'),
    appIcons: latestDir('artifacts/app-icons'),
    legalUrlCheck: latestDir('artifacts/legal-url-checks'),
    privacyDisclosure: latestDir('artifacts/privacy-disclosures'),
    storeMaterials: latestDir('artifacts/store-materials'),
    platformHandoff: latestDir('artifacts/platform-build-handoffs'),
    realUserPacket: latestDir('artifacts/real-user-packets'),
    realUserRoster: latestDir('artifacts/real-user-roster'),
    realUserDispatch: latestDir('artifacts/real-user-dispatch'),
    realUserResult: latestFile('artifacts/real-user-results', '.md'),
    storeScreenshots: latestReportDirWith('artifacts/store-screenshots', 'summary.json'),
    missingHardBlocks: uploadManifest?.missingHardBlocks || [],
  }
}

function writeReport(results) {
  mkdirSync(outDir, { recursive: true })
  const finalEvidence = evidence()
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    branch: git(['branch', '--show-current']) || '',
    commit: git(['rev-parse', 'HEAD']) || '',
    planOnly,
    executionBlocked,
    requiredFinalizeConfirm,
    confirmProvided: Boolean(finalizeConfirm),
    passed: planOnly || executionBlocked ? false : results.every((step) => step.passed),
    finalizeDir: rel(outDir),
    steps: results,
    evidence: finalEvidence,
    verdict: planOnly ? 'plan-only' : (executionBlocked ? 'confirmation-required' : (finalEvidence.missingHardBlocks.length ? 'not-ready' : 'ready-for-human-release-review')),
  }
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

  const lines = [
    `# ${version} Release Finalize 报告`,
    '',
    `> 生成时间：${report.generatedAt}`,
    `> commit：${report.commit || '未读取到'}`,
    `> 模式：${planOnly ? 'plan-only，只预览队列，不执行命令' : (executionBlocked ? 'execute-blocked，缺少最终打包确认，不执行命令' : 'execute，实际执行队列')}`,
    `> 结论：${report.verdict}`,
    '',
    '## 执行结果',
    '',
    '| 步骤 | 命令 | 结果 |',
    '| --- | --- | --- |',
    ...results.map((step) => `| ${step.name} | \`${step.command}\` | ${step.planned ? '计划中' : (step.passed ? '通过' : '失败')} |`),
    '',
    '## 最终证据',
    '',
    `- Readiness：${finalEvidence.readiness ? `\`${finalEvidence.readiness}\`` : '缺失'}`,
    `- User Actions：${finalEvidence.userActions ? `\`${finalEvidence.userActions}\`` : '缺失'}`,
    `- Product Audit：${finalEvidence.productAudit ? `\`${finalEvidence.productAudit}\`` : '缺失'}`,
    `- Release Summary：${finalEvidence.releaseSummary ? `\`${finalEvidence.releaseSummary}\`` : '缺失'}`,
    `- Channel Builds：${finalEvidence.channelBuilds ? `\`${finalEvidence.channelBuilds}\`` : '缺失'}`,
    `- Mobile Build Env：${finalEvidence.mobileBuildEnv ? `\`${finalEvidence.mobileBuildEnv}\`` : '缺失'}`,
    `- Mobile API Evidence：${finalEvidence.mobileApiEvidence ? `\`${finalEvidence.mobileApiEvidence}\`` : '缺失'}`,
    `- Platform Backend Matrix：${finalEvidence.platformBackendMatrix ? `\`${finalEvidence.platformBackendMatrix}\`` : '缺失'}`,
    `- Final Package Plan：${finalEvidence.finalPackagePlan ? `\`${finalEvidence.finalPackagePlan}\`` : '缺失'}`,
    `- Final Package Preflight：${finalEvidence.finalPackagePreflight ? `\`${finalEvidence.finalPackagePreflight}\`` : '缺失'}`,
    `- Final Package Completeness：${finalEvidence.finalPackageCompleteness ? `\`${finalEvidence.finalPackageCompleteness}\`` : '缺失'}`,
    `- Mobile App Resource Packet：${finalEvidence.mobileAppResourcePacket ? `\`${finalEvidence.mobileAppResourcePacket}\`` : '缺失'}`,
    `- Artifact Intake：${finalEvidence.artifactIntake ? `\`${finalEvidence.artifactIntake}\`` : '缺失'}`,
    `- Artifact Metadata：${finalEvidence.artifactMetadata ? `\`${finalEvidence.artifactMetadata}\`` : '缺失'}`,
    `- Release Package：${finalEvidence.releasePackage ? `\`${finalEvidence.releasePackage}\`` : '缺失'}`,
    `- Store Packet：${finalEvidence.storePacket ? `\`${finalEvidence.storePacket}\`` : '缺失'}`,
    `- Store Submission Status：${finalEvidence.storeSubmissionStatus ? `\`${finalEvidence.storeSubmissionStatus}\`` : '缺失'}`,
    `- Store Evidence Status：${finalEvidence.storeEvidenceStatus ? `\`${finalEvidence.storeEvidenceStatus}\`` : '缺失'}`,
    `- Store Account Access：${finalEvidence.storeAccountAccess ? `\`${finalEvidence.storeAccountAccess}\`` : '缺失'}`,
    `- Domain HTTPS：${finalEvidence.domainHttps ? `\`${finalEvidence.domainHttps}\`` : '缺失'}`,
    `- Desktop Release Status：${finalEvidence.desktopReleaseStatus ? `\`${finalEvidence.desktopReleaseStatus}\`` : '缺失'}`,
    `- Desktop Downloads：${finalEvidence.desktopDownloads ? `\`${finalEvidence.desktopDownloads}\`` : '缺失'}`,
    `- Desktop macOS Install Verify：${finalEvidence.desktopMacosInstall ? `\`${finalEvidence.desktopMacosInstall}\`` : '缺失'}`,
    `- Desktop macOS User Packet：${finalEvidence.desktopMacosUserPacket ? `\`${finalEvidence.desktopMacosUserPacket}\`` : '缺失'}`,
    `- Desktop Windows Rebuild：${finalEvidence.desktopWindowsRebuild ? `\`${finalEvidence.desktopWindowsRebuild}\`` : '缺失'}`,
    `- Desktop Windows User Packet：${finalEvidence.desktopWindowsUserPacket ? `\`${finalEvidence.desktopWindowsUserPacket}\`` : '缺失'}`,
    `- App Icons：${finalEvidence.appIcons ? `\`${finalEvidence.appIcons}\`` : '缺失'}`,
    `- Legal URL Check：${finalEvidence.legalUrlCheck ? `\`${finalEvidence.legalUrlCheck}\`` : '缺失'}`,
    `- Privacy Disclosure：${finalEvidence.privacyDisclosure ? `\`${finalEvidence.privacyDisclosure}\`` : '缺失'}`,
    `- Store Materials：${finalEvidence.storeMaterials ? `\`${finalEvidence.storeMaterials}\`` : '缺失'}`,
    `- Platform Handoff：${finalEvidence.platformHandoff ? `\`${finalEvidence.platformHandoff}\`` : '缺失'}`,
    `- Real User Packet：${finalEvidence.realUserPacket ? `\`${finalEvidence.realUserPacket}\`` : '缺失'}`,
    `- Real User Roster：${finalEvidence.realUserRoster ? `\`${finalEvidence.realUserRoster}\`` : '缺失'}`,
    `- Real User Dispatch：${finalEvidence.realUserDispatch ? `\`${finalEvidence.realUserDispatch}\`` : '缺失'}`,
    `- Store Screenshots：${finalEvidence.storeScreenshots ? `\`${finalEvidence.storeScreenshots}\`` : '缺失'}`,
    '',
    '## 当前硬缺口',
    '',
    ...(finalEvidence.missingHardBlocks.length ? finalEvidence.missingHardBlocks.map((item) => `- ${item}`) : ['- 暂无硬缺口。']),
    '',
    '## 说明',
    '',
    ...(planOnly ? ['- 当前是 plan-only 模式：没有执行构建、打包、部署、上传或商店提交命令。'] : []),
    ...(executionBlocked ? [`- 当前缺少最终打包确认：需要先确认所有安装包准备统一刷新后，再执行 \`CONFIRM_FINAL_PACKAGE_REFRESH=${requiredFinalizeConfirm} npm run release:finalize\`。`, '- 因为缺少确认，本次没有执行构建、打包、部署、上传或商店提交命令。'] : []),
    '- 本脚本只做本地证据编排，不上传 GitHub Release，不提交商店后台，不读取或写入证书密钥。',
    '- 如果仍有硬缺口，严格模式和正式上架候选必须继续失败。',
  ]
  writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)
  return report
}

const results = []
for (const [name, args, extraEnv] of steps) {
  console.log(`[release:finalize] ${name}`)
  const result = (planOnly || executionBlocked) ? planStep(name, args, extraEnv || {}) : runStep(name, args, extraEnv || {})
  results.push(result)
  if (!planOnly && !executionBlocked && !result.passed) {
    const report = writeReport(results)
    console.error(JSON.stringify({ outDir: report.finalizeDir, failedStep: name, error: result.error }, null, 2))
    process.exit(1)
  }
}

const report = writeReport(results)
console.log(JSON.stringify({ outDir: report.finalizeDir, planOnly, executionBlocked, verdict: report.verdict, requiredFinalizeConfirm, missingHardBlocks: report.evidence.missingHardBlocks }, null, 2))
if (executionBlocked) process.exit(1)
