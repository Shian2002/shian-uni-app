#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const version = process.env.REAL_USER_VERSION || process.env.RELEASE_VERSION || 'v1.0.0'
const stamp = localTimestamp()
const outDir = process.env.REAL_USER_PACKET_DIR || join(root, 'artifacts', 'real-user-packets', `${stamp}-${version}`)
const minimumTestersPerPlatform = Number.parseInt(process.env.REAL_USER_MIN_TESTERS || '2', 10)

const platforms = [
  {
    id: 'h5',
    name: 'H5',
    channels: ['online', 'staging'],
    packageLabel: 'URL',
    requiredDevices: ['iPhone Safari', 'Android Chrome', '桌面 Chrome/Safari'],
    specialChecks: ['登录态保持', '移动端首屏', 'Agent 输入区', '积分会员页', '工具页无白屏'],
  },
  {
    id: 'android',
    name: 'Android',
    channels: ['yingyongbao', 'huawei', 'xiaomi', 'oppo', 'vivo', 'google-play'],
    packageLabel: 'APK/AAB',
    requiredDevices: ['华为/鸿蒙系 Android', '小米', 'OPPO 或 vivo', '普通 Android 平板或大屏'],
    specialChecks: ['返回键', '软键盘遮挡', '权限弹窗', '支付入口隔离', '渠道包版本号'],
  },
  {
    id: 'ios',
    name: 'iOS',
    channels: ['testflight', 'app-store'],
    packageLabel: 'TestFlight build / IPA 记录',
    requiredDevices: ['iPhone', 'iPad'],
    specialChecks: ['安全区', '键盘遮挡', '隐藏违规第三方充值入口', 'App Privacy 口径', '账号删除入口'],
  },
  {
    id: 'harmony',
    name: '鸿蒙',
    channels: ['appgallery', 'harmony-test'],
    packageLabel: '鸿蒙测试包',
    requiredDevices: ['鸿蒙手机', '鸿蒙平板'],
    specialChecks: ['隐私弹窗', '权限触发时机', '平板布局', '华为审核测试账号', '账号注销'],
  },
  {
    id: 'macos',
    name: 'macOS',
    channels: ['github-releases', 'website'],
    packageLabel: 'DMG/ZIP',
    requiredDevices: ['Apple Silicon Mac', 'Intel Mac 如可用'],
    specialChecks: ['首次打开安全提示', '窗口缩放', '登录弹窗', '时安 agent', '退出重开登录态'],
  },
  {
    id: 'windows',
    name: 'Windows',
    channels: ['github-releases', 'website'],
    packageLabel: 'NSIS/EXE/MSI',
    requiredDevices: ['Windows 10', 'Windows 11'],
    specialChecks: ['安装', '卸载', '开始菜单入口', '窗口缩放', '登录弹窗'],
  },
]
const releaseScope = readJson(join(root, 'configs/release/current-release-scope.json')) || {}
const deferredPlatformIds = new Set((releaseScope.deferredPlatforms || []).map((item) => typeof item === 'string' ? item : item.id).filter(Boolean))
const configuredActivePlatformIds = Array.isArray(releaseScope.activePlatforms) && releaseScope.activePlatforms.length
  ? releaseScope.activePlatforms
  : platforms.map((platform) => platform.id)
const activePlatforms = platforms.filter((platform) => configuredActivePlatformIds.includes(platform.id) && !deferredPlatformIds.has(platform.id))
const deferredPlatforms = platforms.filter((platform) => deferredPlatformIds.has(platform.id))

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

const requiredFlowChecks = [
  ['privacy-entry', '首次启动能看到隐私政策、用户协议或对应入口'],
  ['permission-timing', '未同意前不提前申请敏感权限'],
  ['login-register', '注册或登录路径可完成，错误提示明确'],
  ['agent-entry-button', '首页首屏能看到时安agent；未登录时辅助按钮是登录/注册，登录后辅助按钮是进入应用'],
  ['agent-login-modal', '未登录点击时安agent能看到旧登录弹窗'],
  ['legacy-login-methods', '旧登录弹窗包含密码登录、验证码登录、Gitee 验证登录'],
  ['agent-workbench', '登录后进入时安 agent 能看到输入框、选择命盘、选择术数'],
  ['question-templates', '时安 agent 应用态能看到事业、感情、合作、年运四类问题模板；点击模板只预填问题，不自动发送'],
  ['points-pricing', '积分会员页能看到短期问题、长期问题、复杂问题和会员方案'],
  ['tools-open', '八字、奇门、紫微、塔罗、择吉至少各打开一次，无白屏'],
  ['history-report-entry', '历史记录或报告入口可进入、返回，不丢登录态'],
  ['delete-account-entry', '账号注销入口可见，注销说明清楚'],
  ['session-restore', '退出重进后登录态表现符合预期'],
]

function git(args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim()
  } catch (_) {
    return ''
  }
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function readJson(path) {
  if (!path || !existsSync(path)) return null
  try {
    return JSON.parse(readFileSync(path, 'utf8'))
  } catch (_) {
    return null
  }
}

function latestPassingReport(path, fileName) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, fileName) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byReportTime = reportTime(b.reportPath) - reportTime(a.reportPath)
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const dir of dirs) {
    const report = readJson(join(root, dir.reportPath))
    if (report?.passed === true) return { path: dir.reportPath, data: report }
  }
  return null
}

function reportTime(path) {
  const data = readJson(join(root, path))
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

function fileEvidence(path) {
  if (!path || !existsSync(join(root, path))) return null
  const stat = statSync(join(root, path))
  return { path, bytes: stat.size }
}

function latestInboxArtifact(platform, suffix) {
  const dir = join(root, 'artifacts', 'release-inbox', version, platform)
  if (!existsSync(dir)) return null
  const files = readdirSync(dir)
    .filter((name) => name.endsWith(suffix))
    .map((name) => ({ name, full: join(dir, name) }))
    .filter((item) => statSync(item.full).isFile())
    .sort((a, b) => statSync(b.full).mtimeMs - statSync(a.full).mtimeMs || b.name.localeCompare(a.name))
  return files[0] ? fileEvidence(rel(files[0].full)) : null
}

const currentArtifacts = {
  h5: [
    { label: '线上 H5', value: process.env.REAL_USER_H5_URL || 'https://shianjieyouwu.com/' },
  ],
  android: [
    { label: '内部测试 APK', value: latestInboxArtifact('android', '.apk')?.path || '' },
    { label: 'App Bundle 结构预检 AAB', value: latestInboxArtifact('android', '.aab')?.path || '' },
  ],
  ios: [
    { label: 'TestFlight/IPA', value: latestInboxArtifact('ios', '.ipa')?.path || '缺失：等待 Apple/HBuilderX/DCloud 回传 TestFlight 构建号或 IPA 记录' },
  ],
  harmony: [
    { label: 'HAP/AppGallery', value: latestInboxArtifact('harmony', '.hap')?.path || '缺失：等待 DevEco/HBuilderX/华为后台回传 HAP 或 AppGallery 记录' },
  ],
  macos: [
    { label: 'macOS DMG', value: latestInboxArtifact('macos', '.dmg')?.path || fileEvidence('desktop/release/时安解忧屋-1.0.0-arm64.dmg')?.path || '' },
    { label: 'macOS ZIP', value: latestInboxArtifact('macos', '.zip')?.path || fileEvidence('desktop/release/时安解忧屋-1.0.0-arm64.app.zip')?.path || '' },
  ],
  windows: [
    { label: 'Windows NSIS', value: latestInboxArtifact('windows', '.exe')?.path || fileEvidence('desktop/release/时安解忧屋 Setup 1.0.0.exe')?.path || '' },
  ],
}

function currentArtifactLines(platformId) {
  const rows = currentArtifacts[platformId] || []
  return rows.length
    ? rows.map((item) => `- ${item.label}：${item.value ? `\`${item.value}\`` : '缺失'}`).join('\n')
    : '- 暂无当前产物。'
}

function checkbox(items) {
  return items.map((item) => `- [ ] ${item}`).join('\n')
}

const storeScreenshotSummary = latestPassingReport('artifacts/store-screenshots', 'summary.json')
const loginSmoke = latestPassingReport('artifacts/login-smoke', 'report.json')
const userAcceptance = latestPassingReport('artifacts/user-acceptance', 'report.json')
const latestReadiness = latestFile('artifacts/release-readiness', '.md')
const latestReleaseSummary = latestFile('artifacts/release-summaries', '.md')
const latestTryNow = readJson(join(root, 'artifacts', 'try-now', 'latest-manifest.json'))
const latestAndroidMetadata = readJson(join(root, 'artifacts', 'release-inbox', version, 'android', 'build-metadata.json'))
const latestDesktopReleaseStatus = latestPassingReport('artifacts/desktop-release-status', 'report.json')
const latestDesktopSmoke = latestPassingReport('artifacts/desktop-smoke', 'report.json')
const latestDesktopOnlineLoginSmoke = latestPassingReport('artifacts/desktop-online-login-smoke', 'report.json')

const releaseEvidence = {
  tryNow: latestTryNow?.manifest || latestTryNow?.latestPacketDir || '',
  androidBuildEvidence: latestAndroidMetadata?.buildEvidence || [],
  androidAutomatedEvidence: latestAndroidMetadata?.automatedEvidence || [],
  androidDeviceTestEvidence: latestAndroidMetadata?.deviceTestEvidence || [],
  desktopReleaseStatus: latestDesktopReleaseStatus?.path || '',
  desktopSmoke: latestDesktopSmoke?.path || '',
  desktopOnlineLoginSmoke: latestDesktopOnlineLoginSmoke?.path || '',
}

function releaseEvidenceLines(platformId) {
  const lines = []
  if (releaseEvidence.tryNow) lines.push(`- 最新 try-now：\`${releaseEvidence.tryNow}\``)
  if (platformId === 'android') {
    for (const item of releaseEvidence.androidBuildEvidence || []) lines.push(`- Android 构建证据：\`${item}\``)
    for (const item of releaseEvidence.androidAutomatedEvidence || []) lines.push(`- Android 自动检查：\`${item}\``)
    lines.push(`- Android 真机证据：${(releaseEvidence.androidDeviceTestEvidence || []).length ? releaseEvidence.androidDeviceTestEvidence.map((item) => `\`${item}\``).join('、') : '待回收，不能用构建证据替代'}`)
  }
  if (platformId === 'macos' || platformId === 'windows') {
    if (releaseEvidence.desktopReleaseStatus) lines.push(`- 桌面发布状态：\`${releaseEvidence.desktopReleaseStatus}\``)
    if (releaseEvidence.desktopSmoke) lines.push(`- 桌面 UI smoke：\`${releaseEvidence.desktopSmoke}\``)
    if (releaseEvidence.desktopOnlineLoginSmoke) lines.push(`- 桌面线上登录/积分/agent smoke：\`${releaseEvidence.desktopOnlineLoginSmoke}\``)
  }
  return lines.length ? lines.join('\n') : '- 暂无 release evidence。'
}

function screenshotReferenceLines(platformId) {
  const lines = []
  if (storeScreenshotSummary?.data?.captures?.length) {
    const captures = storeScreenshotSummary.data.captures
    const mapping = [
      ['01-home.png', '01-home'],
      ['02-login-modal.png', '02-login-modal'],
      ['03-agent.png', '03-agent-workbench'],
      ['04-points.png', '04-points'],
      ['05-tool-bazi.png', '05-bazi-tool'],
      ['08-delete-account.png', '06-profile-delete'],
    ]
    for (const [target, id] of mapping) {
      const capture = captures.find((item) => item.id === id && item.preset === 'mobile-390') ||
        captures.find((item) => item.id === id)
      if (capture) lines.push(`- ${target} 参考候选：\`${capture.path}\``)
    }
  }
  if (platformId !== 'h5') {
    lines.push('- 注意：上述 H5 自动截图只能做拍摄参考，不能替代当前平台真实安装包截图。')
  }
  return lines.length ? lines.join('\n') : '- 暂无自动截图候选，请按截图清单手动拍摄。'
}

function passingResultExample(platform) {
  return {
    platform: platform.id,
    version,
    tester: '示例：张三',
    device: platform.requiredDevices[0] || '示例：真实设备型号',
    systemVersion: '示例：系统版本号',
    channel: platform.channels[0] || '示例：测试渠道',
    packageOrUrl: `示例：${platform.packageLabel} 文件名、TestFlight 构建号或 URL`,
    sha256OrBuild: '示例：安装包 SHA-256 或 TestFlight build number',
    gitCommit: git(['rev-parse', 'HEAD']) || '',
    accountType: '示例：审核账号 / 有积分用户',
    realSmsEmailPaymentTriggered: false,
    passedFlows: requiredFlowChecks.map(([id]) => id),
    requiredFlows: requiredFlowChecks.map(([id, label]) => ({ id, label })),
    failedFlows: [],
    blockers: [],
    retestPassed: true,
    conclusion: '通过',
    canSubmitToStore: true,
    screenshots: [
      '01-home.png',
      '02-login-modal.png',
      '03-agent.png',
      '04-points.png',
      '05-tool-bazi.png',
      '06-tool-qimen.png',
      '07-tool-ziwei.png',
      '08-delete-account.png',
    ],
    notes: '示例文件不能直接改名当验收结果；必须替换测试人、设备、安装包、hash、截图和真实结论。',
  }
}

function writePlatformPacket(platform) {
  const platformDir = join(outDir, platform.id)
  const screenshotDir = join(platformDir, 'screenshots')
  const resultsDir = join(platformDir, 'results')
  mkdirSync(screenshotDir, { recursive: true })
  mkdirSync(resultsDir, { recursive: true })
  const requiredScreenshots = [
    '01-home.png',
    '02-login-modal.png',
    '03-agent.png',
    '04-points.png',
    '05-tool-bazi.png',
    '06-tool-qimen.png',
    '07-tool-ziwei.png',
    '08-delete-account.png',
  ]

  const md = `# ${version} ${platform.name} 真实用户验收单

> 生成时间：${new Date().toISOString()}  
> Git commit：${git(['rev-parse', 'HEAD']) || '待填写'}  
> 分支：${git(['branch', '--show-current']) || '待填写'}  
> 截图目录：\`${platform.id}/screenshots/\`

## 0. 回填文件

- \`results/tester-1.json\`、\`results/tester-2.json\`：正式回收结果；每个平台至少 ${minimumTestersPerPlatform} 个测试人，必须填写真实测试人、设备、系统版本、渠道、安装包/URL、hash 或构建号。
- \`result.json\`：旧格式兼容入口；可以保留，但正式放行以 \`results/*.json\` 的多测试人结果为准。
- \`result.example.json\`：通过案例示例，只能参考字段结构，不能直接改名当正式结果。
- \`screenshots/\`：真实设备截图目录，不能用 H5 参考截图替代。

## 1. 测试对象

- 测试人：
- 设备：
- 系统版本：
- 渠道：${platform.channels.join(' / ')}
- 安装包或地址类型：${platform.packageLabel}
- 安装包文件名或 URL：
- SHA-256 或 TestFlight 构建号：
- 测试账号类型：普通用户 / 有积分用户 / 审核账号 / 其他
- 是否使用真实生产用户数据：否
- 是否触发真实短信、邮件或支付：否 / 是，原因：

## 1.1 当前可发测产物

${currentArtifactLines(platform.id)}

## 1.2 当前 release evidence

${releaseEvidenceLines(platform.id)}

## 2. 必测流程

${checkbox([
  ...requiredFlowChecks.map(([id, label]) => `\`${id}\`：${label}`),
])}

## 3. 平台专项

${checkbox(platform.specialChecks)}

## 4. 设备覆盖

${checkbox(platform.requiredDevices)}

## 5. 截图清单

截图文件请放入 \`${platform.id}/screenshots/\`，建议命名：

${checkbox([
  `${requiredScreenshots[0]}：首页首屏，能看到时安agent和正确的登录/进入应用辅助按钮`,
  `${requiredScreenshots[1]}：旧登录弹窗，含密码/验证码/Gitee`,
  `${requiredScreenshots[2]}：时安 agent 应用态，需看到四类问题模板、输入框、选择命盘、选择术数`,
  `${requiredScreenshots[3]}：积分会员页`,
  `${requiredScreenshots[4]}：八字工具页`,
  `${requiredScreenshots[5]}：奇门工具页`,
  `${requiredScreenshots[6]}：紫微工具页`,
  `${requiredScreenshots[7]}：账号注销入口或说明`,
])}

## 5.1 参考截图候选

${screenshotReferenceLines(platform.id)}

## 6. 失败记录

| 编号 | 流程 | 现象 | 截图/录屏 | 严重级别 | 是否复测通过 |
| --- | --- | --- | --- | --- | --- |
| 1 |  |  |  | 阻塞 / 高 / 中 / 低 |  |

## 7. 结论

- 结论：通过 / 阻塞 / 需整改
- 可进入商店提交：是 / 否
- 审核备注需要补充：
- 测试人签名：
- 日期：
`

  writeFileSync(join(platformDir, 'README.md'), md)
  writeFileSync(join(platformDir, 'result.example.json'), `${JSON.stringify(passingResultExample(platform), null, 2)}\n`)

  const blankResult = {
    platform: platform.id,
    version,
    tester: '',
    device: '',
    systemVersion: '',
    channel: '',
    packageOrUrl: '',
    sha256OrBuild: '',
    gitCommit: git(['rev-parse', 'HEAD']) || '',
    accountType: '',
    realSmsEmailPaymentTriggered: false,
    passedFlows: [],
    requiredFlows: requiredFlowChecks.map(([id, label]) => ({ id, label })),
    failedFlows: [],
    blockers: [],
    retestPassed: false,
    conclusion: '',
    canSubmitToStore: false,
    screenshots: requiredScreenshots,
    referenceEvidence: {
      currentArtifacts: currentArtifacts[platform.id] || [],
      releaseEvidence,
      storeScreenshots: storeScreenshotSummary?.path ? rel(join(root, storeScreenshotSummary.path)) : '',
      loginSmoke: loginSmoke?.path ? rel(join(root, loginSmoke.path)) : '',
      userAcceptance: userAcceptance?.path ? rel(join(root, userAcceptance.path)) : '',
      readiness: latestReadiness,
      releaseSummary: latestReleaseSummary,
    },
    notes: '',
  }

  writeFileSync(join(platformDir, 'result.json'), `${JSON.stringify(blankResult, null, 2)}\n`)
  for (let index = 1; index <= minimumTestersPerPlatform; index += 1) {
    writeFileSync(join(resultsDir, `tester-${index}.json`), `${JSON.stringify({ ...blankResult, testerSlot: index }, null, 2)}\n`)
  }
}

function main() {
  mkdirSync(outDir, { recursive: true })
  for (const platform of activePlatforms) writePlatformPacket(platform)

  const index = `# ${version} 真实用户测试包

> 生成时间：${new Date().toISOString()}  
> Git commit：${git(['rev-parse', 'HEAD']) || '待填写'}  
> 分支：${git(['branch', '--show-current']) || '待填写'}  
> 当前批次：${releaseScope.currentBatch || '未配置'}  
> 当前平台：${activePlatforms.map((platform) => platform.name).join('、') || '未配置'}  
> 延期平台：${deferredPlatforms.map((platform) => platform.name).join('、') || '无'}

## 使用方式

1. 把对应平台目录发给测试人。
2. 测试人按 \`README.md\` 勾选流程，并把截图放入 \`screenshots/\`。
3. 测试人参考 \`result.example.json\`，把真实信息填入 \`results/tester-*.json\`；不要把示例文件直接改名当正式结果。
4. 当前批次每个平台至少回收 ${minimumTestersPerPlatform} 个测试人的通过结果；旧 \`result.json\` 只做兼容，不作为最终充分证据。
5. 测试人把通过的流程编号同步填入自己的 \`results/tester-*.json\` 的 \`passedFlows\`。
5. 回收后把通过记录追加到 \`docs/release/real-user-acceptance.md\`。
6. 阻塞问题进入 GitHub Issues，并添加 \`platform:*\`、\`device:*\`、\`store:*\` 标签。
7. 上架候选包的截图、hash、审核备注上传 GitHub Releases。

## 当前参考证据

- 最新 try-now：${releaseEvidence.tryNow ? `\`${releaseEvidence.tryNow}\`` : '缺少 try-now manifest'}
- Android 构建证据：${releaseEvidence.androidBuildEvidence?.length ? releaseEvidence.androidBuildEvidence.map((item) => `\`${item}\``).join('、') : '缺少 Android 成功构建证据'}
- 桌面发布状态：${releaseEvidence.desktopReleaseStatus ? `\`${releaseEvidence.desktopReleaseStatus}\`` : '缺少桌面发布状态报告'}
- 桌面 UI smoke：${releaseEvidence.desktopSmoke ? `\`${releaseEvidence.desktopSmoke}\`` : '缺少桌面 smoke 报告'}
- 桌面线上登录/积分/agent smoke：${releaseEvidence.desktopOnlineLoginSmoke ? `\`${releaseEvidence.desktopOnlineLoginSmoke}\`` : '缺少桌面线上 smoke 报告'}
- 商店截图候选：${storeScreenshotSummary ? `\`${storeScreenshotSummary.path}\`` : '缺少通过的 store:screenshots 报告'}
- 本地复用线上登录 smoke：${loginSmoke ? `\`${loginSmoke.path}\`` : '缺少通过的 qa:login:local-online 报告'}
- 本地用户验收：${userAcceptance ? `\`${userAcceptance.path}\`` : '缺少通过的用户验收报告'}
- Readiness Audit：${latestReadiness ? `\`${latestReadiness}\`` : '缺少 readiness 报告'}
- Release 候选汇总：${latestReleaseSummary ? `\`${latestReleaseSummary}\`` : '缺少 release summary'}

## 当前可发测产物索引

${activePlatforms.map((platform) => `### ${platform.name}\n${currentArtifactLines(platform.id)}`).join('\n\n')}

## 平台目录

${activePlatforms.map((platform) => `- [${platform.name}](./${platform.id}/README.md)`).join('\n')}

## 延期平台

${deferredPlatforms.length ? deferredPlatforms.map((platform) => `- ${platform.name}：本轮不生成测试包目录，配置与历史证据保留，后续恢复 active 后再生成。`).join('\n') : '- 无。'}

## 当前不能替代的证据

- 这个测试包只是验收材料模板，不代表真实用户测试已完成。
- 参考截图只能告诉测试人要拍什么，不能替代真实设备截图。
- 必须回收测试人、设备、系统版本、安装包、截图、\`passedFlows\` 和结论后，才能标记为真实用户验收通过。
- 当前批次 Android、Windows 的安装包和真机证据仍需要对应构建环境、设备或开发者后台产出。
`

  writeFileSync(join(outDir, 'README.md'), index)
  console.log(outDir)
}

main()
