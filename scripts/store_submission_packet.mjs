#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.STORE_PACKET_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.STORE_PACKET_DIR || join(root, 'artifacts', 'store-submission-packets', `${localTimestamp()}-${version}`)

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

function latestDir(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => b.name.localeCompare(a.name))
  return dirs[0] ? join(path, dirs[0].name) : ''
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
    .sort((a, b) => b.name.localeCompare(a.name))
  return files[0] ? join(path, files[0].name) : ''
}

function checklist(items) {
  return items.map((item) => `- [ ] ${item}`).join('\n')
}

function storeDefinitions() {
  const android = readJson('configs/release/android-channels.json') || { channels: [] }
  const ios = readJson('configs/release/ios-appstore.json') || {}
  const harmony = readJson('configs/release/harmony-appgallery.json') || {}
  const desktop = readJson('configs/release/desktop.json') || {}
  const legal = readJson('configs/release/legal-urls.json') || {}

  const domestic = android.channels.filter((item) => item.id !== 'google-play').map((channel) => ({
    id: channel.id,
    name: channel.name,
    platform: 'Android',
    artifact: channel.artifact.toUpperCase(),
    configPath: 'configs/release/android-channels.json',
    requiredMaterials: [
      'APK/AAB 安装包',
      '应用名称、简介、关键词、分类',
      '图标、启动图、手机截图',
      '隐私政策 URL、用户协议 URL',
      'APP 备案、ICP备案、软著或版权材料',
      '测试账号和审核说明',
      '权限说明和第三方 SDK 清单',
      '账号注销入口截图',
    ],
    requiredChecks: android.requiredChecks || [],
    labels: ['release', 'platform:android', `store:${channel.id}`],
    notes: channel.notes,
  }))

  return [
    ...domestic,
    {
      id: 'google-play',
      name: 'Google Play',
      platform: 'Android',
      artifact: 'AAB',
      configPath: 'configs/release/android-channels.json',
      requiredMaterials: [
        'AAB',
        'Data safety 表单',
        '目标 API 等级说明',
        '测试账号和审核路径',
        '隐私政策 URL',
        '账号删除说明',
        '手机和平板截图',
        'Google Play Billing 适用性判断',
      ],
      requiredChecks: [...(android.requiredChecks || []), 'Data safety 与实际数据使用一致'],
      labels: ['release', 'platform:android', 'store:google-play', 'privacy', 'payment'],
      notes: '数字内容、积分包或 AI 次数包若在 App 内销售，需要确认 Google Play Billing。',
    },
    {
      id: 'appstore',
      name: 'Apple App Store',
      platform: 'iOS',
      artifact: 'TestFlight build / IPA 记录',
      configPath: 'configs/release/ios-appstore.json',
      requiredMaterials: ios.requiredMaterials || [],
      requiredChecks: ios.requiredChecks || [],
      labels: ['release', 'platform:ios', 'store:appstore', 'privacy', 'payment'],
      notes: ios.paymentPolicy || '未接入 IAP 前隐藏第三方数字内容充值入口。',
    },
    {
      id: 'harmony',
      name: '华为 AppGallery / 鸿蒙',
      platform: 'Harmony',
      artifact: 'HAP / AppGallery 包',
      configPath: 'configs/release/harmony-appgallery.json',
      requiredMaterials: harmony.requiredMaterials || [],
      requiredChecks: harmony.requiredChecks || [],
      labels: ['release', 'platform:harmony', 'store:huawei', 'privacy'],
      notes: harmony.distribution || '鸿蒙包和华为开发者后台资料单独记录。',
    },
    {
      id: 'github-desktop',
      name: 'GitHub Releases 桌面下载',
      platform: 'macOS / Windows',
      artifact: 'DMG/ZIP/EXE/MSI',
      configPath: 'configs/release/desktop.json',
      requiredMaterials: [
        'macOS/Windows 安装包',
        'SHA-256 清单',
        'Release notes',
        '安装、首次打开、窗口缩放、卸载截图',
        '签名状态说明',
      ],
      requiredChecks: desktop.requiredChecks || [],
      labels: ['release', 'platform:macos', 'platform:windows'],
      notes: desktop.distribution || '第一版通过官网或 GitHub Releases 分发。',
    },
  ].map((store) => ({
    ...store,
    legalUrls: {
      privacyPolicyUrl: legal.privacyPolicyUrl || '',
      userAgreementUrl: legal.userAgreementUrl || '',
      status: legal.status || 'missing',
      requiresHttpsDomainBeforeStoreSubmit: Boolean(legal.requiresHttpsDomainBeforeStoreSubmit),
    },
  }))
}

function commonEvidence() {
  return {
    readiness: latestFile('artifacts/release-readiness', '.md'),
    productAudit: latestFile('artifacts/product-launch-audits', '.md'),
    releaseSummary: latestFile('artifacts/release-summaries', '.md'),
    releasePackage: latestDir('artifacts/release-packages'),
    channelBuilds: latestDir('artifacts/release-channel-builds'),
    mobileBuildEnv: latestDir('artifacts/mobile-build-env'),
    artifactIntake: latestDir('artifacts/release-artifact-intake'),
    platformHandoff: latestDir('artifacts/platform-build-handoffs'),
    realUserPacket: latestDir('artifacts/real-user-packets'),
    realUserResult: latestFile('artifacts/real-user-results', '.md'),
    storeMaterials: latestDir('artifacts/store-materials'),
    legalUrlCheck: latestDir('artifacts/legal-url-checks'),
    privacyDisclosure: latestDir('artifacts/privacy-disclosures'),
    storeScreenshots: latestReportDirWith('artifacts/store-screenshots', 'summary.json'),
    loginSmoke: latestDir('artifacts/login-smoke'),
    agentEntry: latestDir('artifacts/agent-entry'),
  }
}

function hardGaps(store, evidence) {
  const gaps = []
  if (store.platform === 'Android') gaps.push(`${store.artifact} 正式安装包和渠道后台记录`)
  if (store.platform === 'iOS') gaps.push('TestFlight 构建号、App Privacy、iPhone/iPad 真机截图')
  if (store.platform === 'Harmony') gaps.push('鸿蒙测试包、手机/平板截图、华为后台状态')
  if (store.platform.includes('Windows')) gaps.push('Windows EXE/MSI、安装/卸载截图')
  if (!evidence.realUserResult) gaps.push('真实用户回收检查报告')
  else gaps.push('当前批次真实用户 READY 结果')
  gaps.push('审核账号资产充足记录')
  gaps.push('商店后台提交截图或审核编号')
  return gaps
}

function reviewNotes(store) {
  return [
    '审核账号：通过安全渠道提供，不写入 GitHub。',
    '登录方式：复用线上同款登录，支持账号密码、验证码登录和 Gitee 验证入口。',
    '核心路径：启动 App -> 登录 -> 首页点击时安agent/输入问题 -> 选择命盘和术数 -> 查看积分/历史/报告入口。',
    '账号注销入口：个人中心 -> 账号注销 -> 注销账号与删除数据。',
    '内容说明：传统文化与 AI 生成内容，仅供娱乐、参考和自我记录，不替代医疗、法律、金融等专业建议。',
    `付费说明：${store.notes}`,
  ]
}

function writeStore(store, evidence) {
  const dir = join(outDir, store.id)
  mkdirSync(dir, { recursive: true })
  const gaps = hardGaps(store, evidence)
  const md = [
    `# ${version} ${store.name} 提交材料包`,
    '',
    `> 生成时间：${new Date().toISOString()}`,
    `> commit：${git(['rev-parse', 'HEAD']) || '未读取到'}`,
    `> branch：${git(['branch', '--show-current']) || 'unknown'}`,
    `> 平台：${store.platform}`,
    `> 产物类型：${store.artifact}`,
    `> 配置：\`${store.configPath}\``,
    '',
    '## 需准备材料',
    '',
    checklist(store.requiredMaterials),
    '',
    '## 必测流程',
    '',
    checklist(store.requiredChecks),
    '',
    '## 审核备注草稿',
    '',
    reviewNotes(store).map((item) => `- ${item}`).join('\n'),
    '',
    '## 法律 URL',
    '',
    `- 隐私政策 URL：${store.legalUrls?.privacyPolicyUrl || '缺失'}`,
    `- 用户协议 URL：${store.legalUrls?.userAgreementUrl || '缺失'}`,
    `- URL 状态：${store.legalUrls?.status || 'missing'}`,
    store.legalUrls?.requiresHttpsDomainBeforeStoreSubmit ? '- 提交前动作：替换为备案域名 HTTPS URL。' : '- 提交前动作：复核 URL 可公开访问。',
    '',
    '## 当前证据',
    '',
    `- Readiness Audit：${evidence.readiness ? `\`${evidence.readiness}\`` : '缺失'}`,
    `- Product Launch Audit：${evidence.productAudit ? `\`${evidence.productAudit}\`` : '缺失'}`,
    `- Release Summary：${evidence.releaseSummary ? `\`${evidence.releaseSummary}\`` : '缺失'}`,
    `- Release Package：${evidence.releasePackage ? `\`${evidence.releasePackage}\`` : '缺失'}`,
    `- Channel Builds：${evidence.channelBuilds ? `\`${evidence.channelBuilds}\`` : '缺失'}`,
    `- Mobile Build Env：${evidence.mobileBuildEnv ? `\`${evidence.mobileBuildEnv}\`` : '缺失'}`,
    `- Artifact Intake：${evidence.artifactIntake ? `\`${evidence.artifactIntake}\`` : '缺失'}`,
    `- Platform Handoff：${evidence.platformHandoff ? `\`${evidence.platformHandoff}\`` : '缺失'}`,
    `- Real User Packet：${evidence.realUserPacket ? `\`${evidence.realUserPacket}\`` : '缺失'}`,
    `- Real User Result：${evidence.realUserResult ? `\`${evidence.realUserResult}\`` : '缺失'}`,
    `- Store Materials：${evidence.storeMaterials ? `\`${evidence.storeMaterials}\`` : '缺失'}`,
    `- Legal URL Check：${evidence.legalUrlCheck ? `\`${evidence.legalUrlCheck}\`` : '缺失'}`,
    `- Privacy Disclosure：${evidence.privacyDisclosure ? `\`${evidence.privacyDisclosure}\`` : '缺失'}`,
    `- Store Screenshots：${evidence.storeScreenshots ? `\`${evidence.storeScreenshots}\`` : '缺失'}`,
    `- Login Smoke：${evidence.loginSmoke ? `\`${evidence.loginSmoke}\`` : '缺失'}`,
    `- Agent Entry：${evidence.agentEntry ? `\`${evidence.agentEntry}\`` : '缺失'}`,
    '',
    '## 当前缺口',
    '',
    gaps.map((item) => `- ${item}`).join('\n'),
    '',
    '## GitHub Issue 标签建议',
    '',
    store.labels.map((label) => `- \`${label}\``).join('\n'),
    '',
    '## 提交状态',
    '',
    '- 状态：待提交',
    '- 商店后台链接：',
    '- 审核编号：',
    '- 提交人：',
    '- 提交日期：',
    '- 审核反馈：',
    '',
  ].join('\n')
  writeFileSync(join(dir, 'README.md'), md)
  writeFileSync(join(dir, 'submission.json'), `${JSON.stringify({
    version,
    id: store.id,
    name: store.name,
    platform: store.platform,
    artifact: store.artifact,
    configPath: store.configPath,
    labels: store.labels,
    requiredMaterials: store.requiredMaterials,
    requiredChecks: store.requiredChecks,
    legalUrls: store.legalUrls,
    reviewNotes: reviewNotes(store),
    evidence,
    gaps,
    status: '待提交',
  }, null, 2)}\n`)
}

function main() {
  mkdirSync(outDir, { recursive: true })
  const evidence = commonEvidence()
  const stores = storeDefinitions()
  for (const store of stores) writeStore(store, evidence)

  const index = [
    `# ${version} 商店提交材料包`,
    '',
    `> 生成时间：${new Date().toISOString()}`,
    `> commit：${git(['rev-parse', 'HEAD']) || '未读取到'}`,
    `> 分支：${git(['branch', '--show-current']) || 'unknown'}`,
    '',
    '## 商店目录',
    '',
    ...stores.map((store) => `- [${store.name}](./${store.id}/README.md)`),
    '',
    '## 使用规则',
    '',
    '- 本材料包只整理提交字段、审核备注、证据和缺口，不会上传或提交任何商店。',
    '- 账号密码、证书、签名密钥、后台截图原件不写入 Git。',
    '- 正式提交前必须补真实安装包、真机截图、真实用户回收和审核账号资产。',
    '- 提交后把审核编号、反馈和整改动作追加到 `docs/release/review-log.md`。',
    '',
  ].join('\n')
  writeFileSync(join(outDir, 'README.md'), index)
  console.log(JSON.stringify({ outDir: rel(outDir), stores: stores.length }, null, 2))
}

main()
