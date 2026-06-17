#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.RELEASE_USER_ACTIONS_STRICT === '1'
const packageJson = readJson('package.json') || {}
const version = process.env.RELEASE_USER_ACTIONS_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.RELEASE_USER_ACTIONS_OUT_DIR || join(root, 'artifacts', 'release-user-actions', `${localTimestamp()}-${version}`)
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
const deferredPlatformIds = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const activePlatformIds = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms
  : ['h5', 'android', 'ios', 'harmony', 'macos', 'windows']

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

function latestReport(path, filename = 'report.json') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((entry) => statSync(entry.full).isDirectory() && existsSync(join(root, entry.reportPath)))
    .sort((a, b) => {
      const byTime = reportTime(b.reportPath, b.full) - reportTime(a.reportPath, a.full)
      return byTime || b.name.localeCompare(a.name)
    })
  const latest = dirs[0]
  return latest ? { dir: join(path, latest.name), path: latest.reportPath, data: readJson(latest.reportPath) } : null
}

function latestJson(path, filename) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((entry) => statSync(entry.full).isDirectory() && existsSync(join(root, entry.reportPath)))
    .sort((a, b) => {
      const byTime = reportTime(b.reportPath, b.full) - reportTime(a.reportPath, a.full)
      return byTime || b.name.localeCompare(a.name)
    })
  const latest = dirs[0]
  return latest ? { dir: join(path, latest.name), path: latest.reportPath, data: readJson(latest.reportPath) } : null
}

function reportTime(path, fullDir) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const parsed = raw ? Date.parse(raw) : 0
  if (Number.isFinite(parsed) && parsed > 0) return parsed
  return existsSync(fullDir) ? statSync(fullDir).mtimeMs : 0
}

function action(id, title, owner, status, evidence = [], next = [], reason = '') {
  return {
    id,
    title,
    owner,
    status,
    reason,
    evidence: evidence.filter(Boolean),
    next: next.filter(Boolean),
  }
}

function statusFromReport(report) {
  if (!report) return 'missing'
  return report.data?.passed === true ? 'ready' : 'pending'
}

function rowPlatformIds(row) {
  const platform = String(row?.platform || '').toLowerCase()
  const text = JSON.stringify({
    id: row?.id || '',
    name: row?.name || '',
    platform: row?.platform || '',
    target: row?.target || '',
    requiredFor: row?.requiredFor || [],
  }).toLowerCase()
  const ids = new Set()
  if (platform.includes('h5')) ids.add('h5')
  if (platform.includes('android')) ids.add('android')
  if (platform.includes('ios')) ids.add('ios')
  if (platform.includes('harmony') || text.includes('鸿蒙')) ids.add('harmony')
  if (platform.includes('macos')) ids.add('macos')
  if (platform.includes('windows')) ids.add('windows')
  if (platform.includes('desktop') || text.includes('github releases')) {
    ids.add('macos')
    ids.add('windows')
  }
  if (platform.includes('mobile-build')) {
    ids.add('android')
    ids.add('ios')
  }
  if (text.includes('google-play') || text.includes('yingyongbao') || text.includes('xiaomi') || text.includes('oppo') || text.includes('vivo')) ids.add('android')
  if (text.includes('appstore') || text.includes('apple') || text.includes('testflight')) ids.add('ios')
  if (text.includes('huawei-appgallery') || text.includes('appgallery')) ids.add('harmony')
  return [...ids]
}

function inCurrentScope(row) {
  const ids = rowPlatformIds(row)
  if (!ids.length) return true
  return ids.some((id) => activePlatformIds.includes(id) && !deferredPlatformIds.has(id))
}

function currentBatchPlatformNames() {
  const names = {
    h5: 'H5',
    android: 'Android',
    macos: 'macOS',
    windows: 'Windows',
    ios: 'iOS',
    harmony: '鸿蒙',
  }
  return activePlatformIds.filter((id) => !deferredPlatformIds.has(id)).map((id) => names[id] || id).join('、')
}

function main() {
  const releasePackage = latestJson('artifacts/release-packages', 'upload-manifest.json')
  const storeAccountAccess = latestReport('artifacts/store-account-access')
  const storeEvidenceStatus = latestReport('artifacts/store-evidence-status')
  const appRecordStatus = latestReport('artifacts/app-record-status')
  const h5LegalDeployStatus = latestReport('artifacts/h5-legal-deploy-status')
  const domainHttps = latestReport('artifacts/domain-https')
  const realUserRoster = latestReport('artifacts/real-user-roster')
  const realUserResult = latestJson('artifacts/real-user-results', 'report.json')
  const desktopReleaseStatus = latestReport('artifacts/desktop-release-status')
  const artifactMetadata = latestReport('artifacts/release-artifact-metadata')
  const storeSubmissionStatus = latestReport('artifacts/store-submission-status')
  const storeMaterials = latestReport('artifacts/store-materials')
  const mobileBuildEnv = latestReport('artifacts/mobile-build-env')
  const hbuilderxMobileResources = latestReport('artifacts/hbuilderx-mobile-resources')
  const mobileBuildRequests = latestJson('artifacts/mobile-build-requests', 'manifest.json')
  const mobileAppResourcePacket = latestJson('artifacts/mobile-app-resource-packets', 'manifest.json')

  const accountRows = (storeAccountAccess?.data?.accounts || []).filter(inCurrentScope)
  const missingAccounts = accountRows.filter((row) => row.readiness !== 'ready')
  const evidenceRows = (storeEvidenceStatus?.data?.stores || []).filter(inCurrentScope)
  const missingEvidenceRows = evidenceRows.filter((row) => row.readiness !== 'ready')
  const appRecordRows = appRecordStatus?.data?.records || appRecordStatus?.data?.items || []
  const pendingAppRecordRows = Array.isArray(appRecordRows) ? appRecordRows.filter((row) => inCurrentScope(row) && row.readiness !== 'ready' && row.status !== 'not-required') : []
  const mobileEnvMissing = mobileBuildEnv?.data?.missing || []
  const hbuilderxResults = hbuilderxMobileResources?.data?.results || []
  const hbuilderxUserActions = hbuilderxResults.filter((row) => row.status === 'user-action')
  const hbuilderxEnvironmentActions = hbuilderxResults.filter((row) => row.status === 'environment-action')

  const actions = [
    action(
      'user.developer-accounts',
      '开发者账号、2FA、组织资质和签名能力',
      'user',
      missingAccounts.length ? 'pending' : statusFromReport(storeAccountAccess),
      [
        storeAccountAccess?.path,
        'configs/release/store-account-access.json',
      ],
      missingAccounts.length
        ? missingAccounts.map((row) => `${row.name || row.id}：${row.nextAction || '登录后台确认访问、2FA、资质和签名能力，并回传非敏感截图。'}`)
        : ['所有开发者账号访问台账 ready 后再进入商店提交。'],
      '需要你持有或授权 DCloud、Apple Developer、Google Play、华为、应用宝、小米、OPPO、vivo、GitHub Releases 等后台访问。'
    ),
    action(
      'user.store-evidence',
      '商店后台截图、提交编号、隐私和测试轨道证据',
      'user',
      missingEvidenceRows.length ? 'pending' : statusFromReport(storeEvidenceStatus),
      [
        storeEvidenceStatus?.path,
        'docs/release/store-evidence-handoff.md',
      ],
      missingEvidenceRows.length
        ? missingEvidenceRows.map((row) => `${row.name || row.id}：回传 ${row.readyEvidenceCount || 0}/${row.requiredEvidenceCount || 0} 项证据到对应 inbox 目录。`)
        : ['所有商店后台证据 ready 后再运行 strict 检查。'],
      '后台截图、审核编号和测试轨道状态只能由登录对应商店后台的人回传。'
    ),
    action(
      'user.app-record',
      deferredPlatformIds.has('harmony') ? '国内安卓 APP 备案、软著或不适用说明' : '国内安卓和鸿蒙 APP 备案、软著或不适用说明',
      'user',
      statusFromReport(appRecordStatus),
      [
        appRecordStatus?.path,
        'docs/release/app-record-handoff.md',
      ],
      pendingAppRecordRows.length
        ? pendingAppRecordRows.map((row) => `${row.name || row.id}：${row.nextAction || '补后台 APP 备案/软著/应用资质或不适用说明截图。'}`)
        : [deferredPlatformIds.has('harmony') ? '国内安卓后台截图回传后运行 npm run store:app-record -- --strict；鸿蒙后续批次再恢复。' : '国内安卓和鸿蒙后台截图回传后运行 npm run store:app-record -- --strict。'],
      'H5 域名 ICP 已在营销页末尾展示；当前批次移动端 APP 备案按包名和商店后台要求处理。'
    ),
    action(
      'approval.h5-legal-deploy',
      '部署新版 H5 法律页到 https://shianjieyouwu.com/',
      'approval-required',
      statusFromReport(h5LegalDeployStatus),
      [
        h5LegalDeployStatus?.path,
        domainHttps?.path,
        'docs/release/h5-legal-page-deploy-handoff.md',
      ],
      [
        '需要你明确确认后，才能执行 CONFIRM_H5_DEPLOY=shianjieyouwu.com npm run deploy:h5。',
        '部署后运行 LEGAL_URL_CHECK_ONLINE=1 npm run store:legal-urls -- --strict 和 npm run h5:legal-deploy-status -- --strict。',
      ],
      '这是线上发布动作，不能在没有明确确认时自动执行。'
    ),
    action(
      'user.real-user-testing',
      '当前批次真实用户真机回收',
      'user',
      realUserResult?.data?.passed === true ? 'ready' : 'pending',
      [
        realUserRoster?.path,
        realUserResult?.path,
        'docs/release/real-user-acceptance.md',
      ],
      [
        `组织 ${currentBatchPlatformNames()} 真实设备安装和登录回归。`,
        '回传测试人、设备、截图、失败问题和复测结论，不写入真实用户隐私。',
      ],
      '真实设备、测试人和商店安装体验必须人工回传。'
    ),
    action(
      'user.platform-artifacts',
      '当前批次安装包和桌面签名证据',
      'user',
      releasePackage?.data?.missingHardBlocks?.some((item) => /Android|iOS|鸿蒙|桌面|元数据|Windows|macOS/.test(item)) ? 'pending' : 'ready',
      [
        releasePackage?.path,
        artifactMetadata?.path,
        desktopReleaseStatus?.path,
        mobileBuildEnv?.path,
        hbuilderxMobileResources?.path,
        mobileBuildRequests?.path,
        mobileAppResourcePacket?.path,
        'docs/release/platform-build-handoff.md',
      ],
      [
        ...mobileEnvMissing.map((item) => `移动端环境：${item}`),
        ...hbuilderxEnvironmentActions.map((row) => `HBuilderX ${row.id}：CLI 启动环境不兼容；安装与当前 Mac 架构匹配的 HBuilderX，确认 cli open 不再报 Qt/processor feature 错误后重跑 npm run mobile:hbuilderx-resources。`),
        ...hbuilderxUserActions.map((row) => `HBuilderX ${row.id}：CLI 已导入项目，但发行命令仍提示需要登录/发行权限；在 HBuilderX 内确认 DCloud 登录态和发行权限后重跑 npm run mobile:hbuilderx-resources。`),
        '当前批次先补 Android APK/AAB、macOS DMG/ZIP、Windows EXE/MSI/NSIS 的正式元数据、签名状态和真机截图。',
        deferredPlatformIds.has('ios') ? 'iOS TestFlight/IPA 后续批次再恢复，不作为本轮阻塞。' : '用 Apple Developer 或 HBuilderX/DCloud 产出 IPA/TestFlight 记录。',
        deferredPlatformIds.has('harmony') ? '鸿蒙 HAP/AppGallery 后续批次再恢复，不作为本轮阻塞。' : '用 DevEco/HBuilderX/华为后台产出 HAP/AppGallery 包。',
        '回传安装包、SHA-256、构建命令、签名/公证状态和安装/卸载截图。',
      ],
      '证书、签名账号、真机安装截图和各平台构建后台访问不能进 GitHub，也不能由本地脚本凭空生成。'
    ),
    action(
      'user.store-submission',
      '商店正式提交和审核反馈',
      'user',
      statusFromReport(storeSubmissionStatus),
      [
        storeSubmissionStatus?.path,
        storeMaterials?.path,
        'docs/release/review-log.md',
      ],
      [
        deferredPlatformIds.has('ios') && deferredPlatformIds.has('harmony')
          ? '在应用宝、华为 Android、小米、OPPO、vivo、Google Play 和 GitHub Releases 后台提交或保存草稿。'
          : '在应用宝、华为、小米、OPPO、vivo、Google Play、App Store 后台提交或保存草稿。',
        '回填提交状态、审核编号、被拒原因、整改动作和非敏感截图。',
      ],
      '商店提交会改变第三方后台状态，必须由你确认并操作或授权。'
    ),
    action(
      'agent.local-gates',
      '我可以继续本地维护的门禁',
      'agent',
      'ready',
      [
        'npm run release:readiness',
        'npm run release:package',
        'npm run lint',
        'npm run typecheck',
      ],
      [
        '继续补脚本、文档、台账、检查器和本地 smoke。',
        '继续保持本地线上登录代理测试，不替换为未完成的新登录逻辑。',
      ],
      '这些不需要外部后台权限，可以继续由本地工程完成。'
    ),
  ]

  const summary = {
    ready: actions.filter((item) => item.status === 'ready').length,
    pending: actions.filter((item) => item.status === 'pending').length,
    missing: actions.filter((item) => item.status === 'missing').length,
    userRequired: actions.filter((item) => item.owner === 'user' && item.status !== 'ready').length,
    approvalRequired: actions.filter((item) => item.owner === 'approval-required' && item.status !== 'ready').length,
    agentCanContinue: actions.filter((item) => item.owner === 'agent' && item.status !== 'ready').length,
  }

  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    passed: summary.userRequired === 0 && summary.approvalRequired === 0 && summary.pending === 0 && summary.missing === 0,
    summary,
    releaseScope: {
      configPath: 'configs/release/current-release-scope.json',
      currentBatch: releaseScope.currentBatch || '',
      activePlatforms: activePlatformIds.filter((id) => !deferredPlatformIds.has(id)),
      deferredPlatforms: [...deferredPlatformIds],
    },
    sources: {
      releasePackage: releasePackage?.path || '',
      storeAccountAccess: storeAccountAccess?.path || '',
      storeEvidenceStatus: storeEvidenceStatus?.path || '',
      appRecordStatus: appRecordStatus?.path || '',
      h5LegalDeployStatus: h5LegalDeployStatus?.path || '',
      domainHttps: domainHttps?.path || '',
      realUserRoster: realUserRoster?.path || '',
      realUserResult: realUserResult?.path || '',
      desktopReleaseStatus: desktopReleaseStatus?.path || '',
      artifactMetadata: artifactMetadata?.path || '',
      storeSubmissionStatus: storeSubmissionStatus?.path || '',
      storeMaterials: storeMaterials?.path || '',
      mobileBuildEnv: mobileBuildEnv?.path || '',
      hbuilderxMobileResources: hbuilderxMobileResources?.path || '',
      mobileBuildRequests: mobileBuildRequests?.path || '',
      mobileAppResourcePacket: mobileAppResourcePacket?.path || '',
    },
    actions,
  }

  mkdirSync(outDir, { recursive: true })
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

  const md = [
    '# 最后必须人工完成的上架事项',
    '',
    `> 生成时间：${report.generatedAt}`,
    `> 版本：${version}`,
    `> 结论：${report.passed ? '已无人工阻塞' : '仍有人工作业/外部授权阻塞'}`,
    '',
    `汇总：READY ${summary.ready} / PENDING ${summary.pending} / MISSING ${summary.missing} / USER ${summary.userRequired} / APPROVAL ${summary.approvalRequired}`,
    '',
    '## 我可以继续做',
    '',
    ...actions
      .filter((item) => item.owner === 'agent')
      .flatMap((item) => [`### ${item.title}`, '', item.reason, '', ...item.next.map((next) => `- ${next}`), '']),
    '',
    '## 需要你确认后我才能做',
    '',
    ...actions
      .filter((item) => item.owner === 'approval-required' && item.status !== 'ready')
      .flatMap((item) => [`### ${item.title}`, '', item.reason, '', ...item.next.map((next) => `- ${next}`), '', '证据：', ...item.evidence.map((entry) => `- \`${entry}\``), '']),
    '',
    '## 最后必须你做',
    '',
    ...actions
      .filter((item) => item.owner === 'user' && item.status !== 'ready')
      .flatMap((item) => [`### ${item.title}`, '', item.reason, '', ...item.next.map((next) => `- ${next}`), '', '证据：', ...item.evidence.map((entry) => `- \`${entry}\``), '']),
    '',
    '## 规则',
    '',
    '- 不在 GitHub 保存账号密码、验证码、证书、签名密钥、后台 token、身份证件原件或真实用户隐私。',
    '- 任何部署、push、商店提交、后台状态变更都需要明确确认。',
    '- 人工事项完成后，先回传非敏感截图/编号/安装包 hash，再运行对应 strict 检查。',
    '',
  ].join('\n')
  writeFileSync(join(outDir, 'README.md'), md)

  console.log(JSON.stringify({
    outDir: rel(outDir),
    passed: report.passed,
    summary,
  }, null, 2))
  if (strict && !report.passed) process.exit(1)
}

main()
