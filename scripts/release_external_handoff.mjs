#!/usr/bin/env node

import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = `v${packageJson.version || '0.0.0'}`
const outDir = join(root, 'artifacts', 'external-handoff', `${localTimestamp()}-${version}`)
const releaseInboxBase = `artifacts/release-inbox/${version}`

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

function latestDir(path, filename = 'report.json') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byTime = reportTime(b.reportPath, b.full) - reportTime(a.reportPath, a.full)
      return byTime || b.name.localeCompare(a.name)
    })
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function latestFile(path, suffix) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const files = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name) }))
    .filter((item) => statSync(item.full).isFile() && item.name.endsWith(suffix))
    .sort((a, b) => statSync(b.full).mtimeMs - statSync(a.full).mtimeMs || b.name.localeCompare(a.name))
  return files[0] ? join(path, files[0].name) : ''
}

function reportTime(path, fullPath = '') {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  if (Number.isFinite(time) && time > 0) return time
  return fullPath && existsSync(fullPath) ? statSync(fullPath).mtimeMs : 0
}

function writeJson(path, data) {
  mkdirSync(join(root, path, '..'), { recursive: true })
  writeFileSync(join(root, path), `${JSON.stringify(data, null, 2)}\n`)
}

function writeText(path, text) {
  mkdirSync(join(root, path, '..'), { recursive: true })
  writeFileSync(join(root, path), text)
}

function metadataTemplate(task) {
  const artifactByTask = {
    'android-package': `shian-${version}-yingyongbao.apk`,
    'ios-testflight': `shian-${version}-ios-testflight-record.json`,
    'harmony-package': `shian-${version}-harmony.hap`,
  }
  const artifactKinds = task.requiredFiles
    .filter((file) => /\.(apk|aab|ipa|hap|json)$/i.test(file))
    .filter((file) => !file.includes('build-metadata'))
    .map((file) => ({
      path: `${task.inbox}${file}`,
      sha256: '<sha256>',
      kind: file.split('.').pop(),
      channel: task.id === 'android-package' ? '<yingyongbao/huawei/xiaomi/oppo/vivo/google-play>' : undefined,
      buildNumber: task.id === 'ios-testflight' ? '<TestFlight build number>' : undefined,
    }))
  return {
    appName: packageJson.uniApp?.name || '时安解忧屋',
    platform: task.id,
    versionName: packageJson.version || '1.0.0',
    versionCode: task.id === 'ios-testflight' ? undefined : 100,
    buildNumber: task.id === 'ios-testflight' ? 100 : undefined,
    commit: '<current-git-commit>',
    buildTool: '<HBuilderX/DCloud/Xcode/DevEco>',
    builder: '<builder-public-name>',
    builtAt: '<ISO-8601-time>',
    channel: task.id === 'android-package' ? '<yingyongbao/huawei/xiaomi/oppo/vivo/google-play>' : undefined,
    artifactPath: `${task.inbox}${artifactByTask[task.id] || '<artifact-file>'}`,
    artifactSha256: '<sha256>',
    artifacts: artifactKinds.map((item) => Object.fromEntries(Object.entries(item).filter(([, value]) => value !== undefined))),
    onlineApiBase: 'https://shianjieyouwu.com',
    sourceBuild: {
      appResourceEntry: 'dist/build/app/__uniappview.html',
      appRuntime: 'dist/build/app/app-service.js',
      manifest: 'src/manifest.json',
      appIcon: 'src/static/app-icons/app-icon-1024.png',
    },
    validationCommands: task.verify,
    reviewAccountDelivery: 'secure-channel-not-in-git',
    deviceTestEvidence: task.requiredFiles
      .filter((file) => file.startsWith('screenshots/'))
      .map((file) => `${task.inbox}${file}`),
    notes: [
      '使用线上登录和线上 API 回归，不在元数据里填写账号口令。',
      '如一个平台有多个渠道包，保留 artifactPath 为主包，并在 artifacts 数组补齐全部包。',
    ],
  }
}

function writeTaskTemplates(task) {
  if (['android-package', 'ios-testflight', 'harmony-package'].includes(task.id)) {
    writeJson(join(task.inbox, 'build-metadata.template.json'), Object.fromEntries(
      Object.entries(metadataTemplate(task)).filter(([, value]) => value !== undefined)
    ))
    writeText(join(task.inbox, 'screenshots/README.md'), [
      `# ${task.title} 截图回传`,
      '',
      '## 必须覆盖',
      '',
      '- 首次打开或安装完成后的入口页。',
      '- 线上登录成功后的用户态页面。',
      '- 时安 agent 可发送问题并收到结果。',
      '- 积分中心或会员积分可打开。',
      '- 账号注销入口可找到。',
      '',
      '## 命名',
      '',
      ...task.requiredFiles
        .filter((file) => file.startsWith('screenshots/'))
        .map((file) => `- \`${file.replace('screenshots/', '')}\``),
      '',
      '## 禁止',
      '',
      '- 截图不要露出手机号、邮箱验证码、后台账号、证书文件名或签名口令。',
      '',
    ].join('\n'))
    return
  }
  if (task.id === 'store-and-records') {
    writeJson(join(task.inbox, 'evidence-index.template.json'), {
      generatedAt: '<ISO-8601-time>',
      reviewer: '<your-name>',
      submissions: {
        yingyongbao: { status: 'not-submitted/submitted/rejected/approved', evidence: `${task.inbox}yingyongbao/submission.png` },
        huaweiAppGallery: { status: 'not-submitted/submitted/rejected/approved', evidence: `${task.inbox}huawei-appgallery/submission.png` },
        googlePlay: { status: 'not-submitted/submitted/rejected/approved', evidence: `${task.inbox}google-play/data-safety.png` },
        appStore: { status: 'not-submitted/submitted/rejected/approved', evidence: `${task.inbox}appstore/app-privacy.png` },
      },
      notes: '不要写账号密码、验证码、token 或证书信息。',
    })
    return
  }
  if (task.id === 'real-user-results') {
    writeJson(join(task.inbox, 'tester-result.template.json'), {
      tester: '<tester-name>',
      testedAt: '<ISO-8601-time>',
      platforms: ['h5', 'android', 'ios', 'harmony', 'macos', 'windows'],
      checks: [
        'install-or-open',
        'online-login',
        'membership-points',
        'shian-agent',
        'account-delete-entry',
      ],
      screenshots: task.requiredFiles.filter((file) => file.startsWith('screenshots/')).map((file) => `${task.inbox}${file}`),
      result: 'pass/fail',
      notes: '',
    })
  }
}

const quotaStatus = latestDir('artifacts/quota-status')
const releasePackage = latestDir('artifacts/release-packages', 'upload-manifest.json')
const releasePackageReport = releasePackage ? readJson(`${releasePackage}/upload-manifest.json`) : null
const readiness = latestFile('artifacts/release-readiness', '.json')
const mobileRequests = latestDir('artifacts/mobile-build-requests', 'manifest.json')
const tryNow = readJson('artifacts/try-now/latest-manifest.json')

const tasks = [
  {
    id: 'android-package',
    title: 'Android APK/AAB 真包',
    owner: '你或 Android/DCloud 打包机',
    inbox: `${releaseInboxBase}/android/`,
    requiredFiles: [
      `shian-${version}-yingyongbao.apk`,
      `shian-${version}-huawei.apk`,
      `shian-${version}-xiaomi.apk`,
      `shian-${version}-oppo.apk`,
      `shian-${version}-vivo.apk`,
      `shian-${version}-google-play.aab`,
      'build-metadata.json',
      'screenshots/device-login.png',
      'screenshots/agent.png',
      'screenshots/points.png',
      'screenshots/account-delete.png',
    ],
    verify: ['npm run release:intake', 'npm run release:artifact-metadata', 'npm run real-user:dispatch'],
    handoffNotes: [
      '本机已检测到 HBuilderX，但命令行入口需要先打开 HBuilderX 才能继续；当前仓库不会伪造 Android 真包。',
      '国内渠道 APK 与 Google Play AAB 共用同一核心代码，通过渠道配置、签名和商店素材区分。',
      '回传后先跑线上登录、时安 agent、积分中心、账号注销四条主流程。',
    ],
  },
  {
    id: 'ios-testflight',
    title: 'iOS TestFlight/IPA 构建记录',
    owner: '你或 Apple Developer 打包机',
    inbox: `${releaseInboxBase}/ios/`,
    requiredFiles: [
      `shian-${version}-ios-testflight-record.json`,
      'build-metadata.json',
      'screenshots/iphone-agent.png',
      'screenshots/ipad-agent.png',
      'screenshots/app-privacy.png',
      'screenshots/account-delete.png',
    ],
    verify: ['npm run release:intake', 'npm run release:artifact-metadata', 'npm run store:privacy'],
    handoffNotes: [
      'iOS 先以 TestFlight 构建号作为主证据；如导出 IPA，也放入同目录并写入 artifacts 数组。',
      'App Privacy、账号删除、审核账号交付方式必须和商店后台一致。',
      'iPhone 和 iPad 都要真机或 TestFlight 验证，不用网页截图替代。',
    ],
  },
  {
    id: 'harmony-package',
    title: '鸿蒙 HAP/AppGallery 包',
    owner: '你或华为/DevEco 打包机',
    inbox: `${releaseInboxBase}/harmony/`,
    requiredFiles: [
      `shian-${version}-harmony.hap`,
      `shian-${version}-appgallery-record.json`,
      'build-metadata.json',
      'screenshots/harmony-phone-agent.png',
      'screenshots/harmony-tablet-agent.png',
      'screenshots/permissions.png',
      'screenshots/account-delete.png',
    ],
    verify: ['npm run release:intake', 'npm run release:artifact-metadata', 'npm run store:app-record'],
    handoffNotes: [
      '当前本机未检测到 DevEco/鸿蒙命令行环境；鸿蒙包需要华为构建环境或 HBuilderX 支持后回传。',
      '手机与平板截图都要覆盖线上登录、时安 agent 和权限触发说明。',
      '如 AppGallery 只返回后台构建记录，也要保存记录 JSON 和后台状态截图。',
    ],
  },
  {
    id: 'store-and-records',
    title: '商店后台、备案、域名和法律页证据',
    owner: '你登录各开发者后台后回传截图/编号',
    inbox: 'artifacts/store-evidence-inbox/',
    requiredFiles: [
      'yingyongbao/submission.png',
      'huawei-appgallery/submission.png',
      'xiaomi/submission.png',
      'oppo/submission.png',
      'vivo/submission.png',
      'google-play/data-safety.png',
      'appstore/app-privacy.png',
      'domain/https-record.png',
      'app-record/android-cn.png',
      'legal/privacy-online.png',
    ],
    verify: [
      'npm run store:submission-status',
      'npm run store:evidence-status',
      'npm run store:account-access',
      'npm run domain:https',
      'npm run h5:legal-deploy-status',
    ],
  },
  {
    id: 'real-user-results',
    title: '当前批次真实用户回收',
    owner: '你安排测试人回填',
    inbox: 'artifacts/real-user-results/',
    requiredFiles: [
      'tester-1.json',
      'tester-2.json',
      'screenshots/h5-agent.png',
      'screenshots/android-agent.png',
      'screenshots/ios-agent.png',
      'screenshots/harmony-agent.png',
      'screenshots/macos-agent.png',
      'screenshots/windows-agent.png',
    ],
    verify: ['npm run real-user:roster', 'npm run real-user:check'],
  },
]

mkdirSync(outDir, { recursive: true })
for (const task of tasks) {
  mkdirSync(join(root, task.inbox), { recursive: true })
  writeTaskTemplates(task)
  writeText(join(task.inbox, 'README.md'), [
    `# ${task.title}`,
    '',
    `> 负责人：${task.owner}`,
    `> 回传目录：\`${task.inbox}\``,
    '',
    '## 需要回传',
    '',
    ...task.requiredFiles.map((file) => `- [ ] \`${file}\``),
    '',
    '## 回传后验证',
    '',
    ...task.verify.map((cmd) => `- \`${cmd}\``),
    '',
    ...(task.handoffNotes?.length ? [
      '## 打包说明',
      '',
      ...task.handoffNotes.map((note) => `- ${note}`),
      '',
    ] : []),
    '',
    '## 模板',
    '',
    '- 如果目录内有 `*.template.json`，先复制一份去掉 `.template` 再填写真实路径、hash、截图和状态。',
    '',
    '## 禁止',
    '',
    '- 不要放入证书、私钥、keystore、p12、mobileprovision、账号密码、验证码、token。',
  ].join('\n') + '\n')
}

const manifest = {
  generatedAt: new Date().toISOString(),
  version,
  quotaSafe: true,
  note: '只生成外部回传清单和目录，不构建、不打包、不启动 App。',
  evidence: {
    quotaStatus,
    releasePackage,
    readiness,
    mobileRequests,
    tryNow: tryNow?.latestPacketDir || '',
  },
  currentUsable: {
    macosDmg: tryNow?.macosDmg || '',
    windowsInstaller: tryNow?.windowsInstaller || '',
    androidDebugApk: tryNow?.androidDebugApk || '',
    androidDebugAab: tryNow?.androidDebugAab || '',
  },
  remainingHardBlocks: releasePackageReport?.missingHardBlocks || [],
  tasks,
}
writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)

const readme = [
  '# 外部硬阻塞回传清单',
  '',
  `> 生成时间：${manifest.generatedAt}`,
  `> 版本：${version}`,
  '> 说明：低成本清单，只创建回传目录和 README，不触发构建。',
  '',
  '## 当前可用证据',
  '',
  ...Object.entries(manifest.evidence).map(([key, value]) => `- ${key}：\`${value || '缺失'}\``),
  '',
  '## 当前可先试装',
  '',
  `- macOS DMG：${manifest.currentUsable.macosDmg ? `\`${manifest.currentUsable.macosDmg}\`` : '缺失'}`,
  `- Windows 安装器：${manifest.currentUsable.windowsInstaller ? `\`${manifest.currentUsable.windowsInstaller}\`` : '缺失'}`,
  `- Android 调试 APK：${manifest.currentUsable.androidDebugApk ? `\`${manifest.currentUsable.androidDebugApk}\`` : '缺失'}`,
  `- Android 调试 AAB：${manifest.currentUsable.androidDebugAab ? `\`${manifest.currentUsable.androidDebugAab}\`` : '缺失'}`,
  '',
  '> Android 调试 APK/AAB 只用于先行真机回归；正式上架仍需回传渠道签名 APK/AAB、真机截图和商店后台证据。',
  '',
  '## 需要外部回传',
  '',
  '| 事项 | 回传目录 | 验证命令 |',
  '| --- | --- | --- |',
  ...tasks.map((task) => `| ${task.title} | \`${task.inbox}\` | ${task.verify.map((cmd) => `\`${cmd}\``).join('<br>')} |`),
  '',
  '## 仍存在的硬阻塞',
  '',
  ...(manifest.remainingHardBlocks.length ? manifest.remainingHardBlocks.map((item) => `- ${item}`) : ['- 暂无硬阻塞。']),
]
writeFileSync(join(outDir, 'README.md'), `${readme.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  tasks: tasks.length,
  remainingHardBlocks: manifest.remainingHardBlocks.length,
  quotaSafe: manifest.quotaSafe,
}, null, 2))
