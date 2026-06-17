#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.MOBILE_BUILD_REQUEST_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.MOBILE_BUILD_REQUEST_DIR || join(root, 'artifacts', 'mobile-build-requests', `${localTimestamp()}-${version}`)

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

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function fileEvidence(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const stat = statSync(fullPath)
  return { path, bytes: stat.size, sha256: sha256(fullPath) }
}

function appResourceEvidence() {
  return fileEvidence('dist/build/app/__uniappview.html') ||
    fileEvidence('dist/build/app/index.html') ||
    fileEvidence('dist/build/app/app-service.js')
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

function latestReportDirForPlatform(path, filename, platform) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory() && item.name.endsWith(`-${platform}`) && existsSync(join(root, item.reportPath)))
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

function list(items) {
  return items.filter(Boolean).map((item) => `- ${item}`).join('\n')
}

function checklist(items) {
  return items.filter(Boolean).map((item) => `- [ ] ${item}`).join('\n')
}

const android = readJson('configs/release/android-channels.json') || { channels: [] }
const ios = readJson('configs/release/ios-appstore.json') || {}
const harmony = readJson('configs/release/harmony-appgallery.json') || {}

const evidence = {
  generatedAt: new Date().toISOString(),
  version,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  appResource: appResourceEvidence(),
  h5Index: fileEvidence('dist/build/h5/index.html'),
  manifest: fileEvidence('src/manifest.json'),
  mobileEnv: latestDir('artifacts/mobile-build-env'),
  mobileToolchainPlan: latestReportDirWith('artifacts/mobile-toolchain-plan', 'report.json'),
  hbuilderxResources: latestReportDirWith('artifacts/hbuilderx-mobile-resources', 'report.json'),
  appIcons: latestDir('artifacts/app-icons'),
  storeIcon: fileEvidence('src/static/app-icons/app-icon-1024.png'),
  platformHandoff: latestDir('artifacts/platform-build-handoffs'),
  artifactIntake: latestDir('artifacts/release-artifact-intake'),
  legalUrlCheck: latestDir('artifacts/legal-url-checks'),
  privacyDisclosure: latestDir('artifacts/privacy-disclosures'),
  storeMaterials: latestDir('artifacts/store-materials'),
  loginSmoke: latestReportDirWith('artifacts/login-smoke', 'report.json'),
  agentEntry: latestReportDirWith('artifacts/agent-entry', 'report.json'),
  lowImpactStatus: latestReportDirWith('artifacts/low-impact-status', 'report.json'),
  hbuilderxCloudPackAttempt: latestReportDirWith('artifacts/hbuilderx-cloud-pack-attempts', 'attempt.json'),
  hbuilderxCloudPackAttempts: {
    android: latestReportDirForPlatform('artifacts/hbuilderx-cloud-pack-attempts', 'attempt.json', 'android'),
    ios: latestReportDirForPlatform('artifacts/hbuilderx-cloud-pack-attempts', 'attempt.json', 'ios'),
  },
  hbuilderxHarmonyPackAttempt: latestReportDirWith('artifacts/hbuilderx-harmony-pack-attempts', 'attempt.json'),
  iosLocalBuildAttempt: latestReportDirWith('artifacts/ios-local-build-attempts', 'attempt.json'),
  hbuilderxPluginInstall: latestDir('artifacts/hbuilderx-plugin-installs'),
  androidDebugApk: latestInboxArtifact('android', '.apk'),
  androidDebugAab: latestInboxArtifact('android', '.aab'),
}

const knownLocalBlockers = [
  'HBuilderX 登录和 App 打包插件已恢复：launcher、launcher-tools、node_modules、app-safe-pack、amazon-corretto 均应由 npm run mobile:build-env 记录状态。',
  'HBuilderX CLI pack 云打包入口已确认；Android/iOS 云打包尝试由 npm run mobile:hbuilderx-cloud-pack 记录 attempt.json 和脱敏日志。',
  '当前 Android 云打包已进入 DCloud 服务端检查，但被手机号重新验证、证书策略或云端 SDK 版本差异拦截；以最新 hbuilderx-cloud-pack-attempts 报告为准。',
  'HBuilderX 鸿蒙本地打包入口已确认；执行 npm run mobile:hbuilderx-harmony-pack 可记录 pack app-harmony 的 attempt.json 和脱敏日志。',
  '鸿蒙 pack app-harmony 已给出明确阻塞：本机缺 DevEco Studio/hdc/hvigor，需要先安装 DevEco 并在 HBuilderX 偏好设置配置鸿蒙开发者工具路径；以最新 hbuilderx-harmony-pack-attempts 报告为准。',
  '移动端工具链准备计划由 npm run mobile:toolchain-plan 记录；当前 /Volumes/XcodeAPFS 已是 APFS 外接目标盘，Xcode 16.2 安装仍需要 Apple 下载认证，内置盘低空间只作为下载/解压临时缓存风险。',
  'iOS 本地构建阻塞由 npm run mobile:ios-local-build-attempt 记录，覆盖完整 Xcode、simctl、Apple 签名身份、provisioning profile 和磁盘余量。',
  'iOS TestFlight/IPA 仍需要完整 Xcode、Apple Developer 证书、profile 或 DCloud/HBuilderX iOS 云打包签名材料；证书不得入库。',
  '鸿蒙 HAP/AppGallery 仍需要 DevEco/hdc/hvigor 或 HBuilderX/华为构建环境；签名资料和华为后台凭据不得入库。',
]

const commonInputs = [
  '同一 commit、同一核心代码，不为手机品牌或商店拆仓。',
  '本地壳继续复用线上登录接口：/api/login、/api/register、/api/email/login、/api/sms/login、/api/oauth/*/url。',
  '打包前运行 npm run build:app，并确认 dist/build/app/__uniappview.html 和 dist/build/app/app-service.js 存在。',
  '打包前运行 npm run mobile:toolchain-plan，记录 Xcode 16.2、/Volumes/XcodeAPFS、DevEco/hdc/hvigor 和需要你最后处理的账号/证书步骤。',
  '打包前运行 MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight。',
  '打包前运行 npm run release:app-icons，并使用 src/static/app-icons/app-icon-1024.png 作为 HBuilderX、DCloud 云打包、Xcode、DevEco 和商店后台图标母图。',
  '证书、keystore、p12、mobileprovision、商店账号密码和签名口令只走安全交接，不进入 GitHub。',
]

const commonAfterReturn = [
  '把回传产物放入对应 release inbox 目录。',
  '同目录补 build-metadata.json，记录版本、commit、构建工具、安装包路径、SHA-256、截图路径和审核账号交付方式。',
  '执行 npm run release:intake 生成 SHA-256 收件报告。',
  '执行 npm run release:artifact-metadata 生成回传元数据报告。',
  '执行 npm run real-user:dispatch 生成真实用户发测索引。',
  '完成真机安装、线上登录、时安 agent、积分中心、账号注销和截图回传。',
]

const requests = [
  {
    id: 'android',
    title: 'Android APK/AAB 构建请求',
    config: 'configs/release/android-channels.json',
    packageId: android.packageName || '',
    inbox: `${version}/android/`,
    expectedFiles: [
      `shian-${version}-yingyongbao.apk`,
      `shian-${version}-huawei.apk`,
      `shian-${version}-xiaomi.apk`,
      `shian-${version}-oppo.apk`,
      `shian-${version}-vivo.apk`,
      `shian-${version}-google-play.aab`,
      'build-metadata.json',
    ],
    buildCommands: [
      'npm ci',
      'npm run build:app',
      'MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight',
      '使用 HBuilderX/DCloud 云打包或 Android 构建机生成 APK/AAB。',
    ],
    storeScope: (android.channels || []).map((channel) => `${channel.name} (${channel.id}, ${channel.artifact})`),
    mustTest: android.requiredChecks || [],
    returnEvidence: ['APK/AAB 文件', '每个文件 SHA-256', 'versionName/versionCode', '渠道 ID', '打包机系统', '真机截图'],
  },
  {
    id: 'ios',
    title: 'iOS TestFlight 构建请求',
    config: 'configs/release/ios-appstore.json',
    packageId: ios.bundleId || '',
    inbox: `${version}/ios/`,
    expectedFiles: [
      `shian-${version}-ios-testflight-record.json`,
      `shian-${version}.ipa 或 TestFlight 构建号记录`,
      'build-metadata.json',
    ],
    buildCommands: [
      'npm ci',
      'VITE_RELEASE_CHANNEL=appstore npm run build:h5',
      'npm run build:app',
      'MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight',
      'IOS_LOCAL_BUILD_EXECUTE=1 npm run mobile:ios-local-build-attempt',
      '使用 Apple 证书在 HBuilderX/DCloud 或 Xcode/iOS 打包环境提交 TestFlight。',
    ],
    storeScope: ['Apple App Store', 'TestFlight'],
    mustTest: ios.requiredChecks || [],
    returnEvidence: ['TestFlight build number 或 IPA 记录', 'iPhone 截图', 'iPad 截图', 'App Privacy 截图', '审核账号交付方式，不写密码'],
  },
  {
    id: 'harmony',
    title: '鸿蒙/AppGallery 构建请求',
    config: 'configs/release/harmony-appgallery.json',
    packageId: harmony.bundleName || '',
    inbox: `${version}/harmony/`,
    expectedFiles: [
      `shian-${version}-harmony.hap`,
      `shian-${version}-appgallery-record.json`,
      'build-metadata.json',
    ],
    buildCommands: [
      'npm ci',
      'npm run build:app',
      'MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight',
      '使用 HBuilderX/华为构建环境或 DevEco 生成 HAP/AppGallery 测试包。',
    ],
    storeScope: ['华为应用市场', '鸿蒙测试包'],
    mustTest: harmony.requiredChecks || [],
    returnEvidence: ['HAP/AppGallery 包或后台构建记录', '鸿蒙手机截图', '鸿蒙平板截图', '权限触发说明', '华为后台状态截图'],
  },
]

function requestJson(request) {
  return {
    ...request,
    generatedAt: evidence.generatedAt,
    version,
    branch: evidence.branch,
    commit: evidence.commit,
    inputEvidence: evidence,
    knownLocalBlockers,
    commonInputs,
    commonAfterReturn,
    releaseInbox: `artifacts/release-inbox/${request.inbox}`,
    hbuilderxCloudPackAttempt: evidence.hbuilderxCloudPackAttempts?.[request.id] || '',
    hbuilderxHarmonyPackAttempt: request.id === 'harmony' ? evidence.hbuilderxHarmonyPackAttempt : '',
    iosLocalBuildAttempt: request.id === 'ios' ? evidence.iosLocalBuildAttempt : '',
    sensitiveFilesPolicy: '证书、密钥、keystore、p12、mobileprovision、签名口令和商店账号密码不得进入 GitHub。',
  }
}

function writeRequest(request) {
  const data = requestJson(request)
  const platformCloudPackAttempt = evidence.hbuilderxCloudPackAttempts?.[request.id] || ''
  writeFileSync(join(outDir, `${request.id}.json`), `${JSON.stringify(data, null, 2)}\n`)

  const lines = [
    `# ${request.title}`,
    '',
    `> 生成时间：${evidence.generatedAt}`,
    `> 版本：${version}`,
    `> commit：${evidence.commit || '未读取到'}`,
    `> 配置文件：\`${request.config}\``,
    `> 包标识：${request.packageId || '待配置'}`,
    `> 回传目录：\`artifacts/release-inbox/${request.inbox}\``,
    '',
    '## 打包输入',
    '',
    list(commonInputs),
    '',
    '## 当前输入证据',
    '',
    list([
      evidence.appResource ? `App 资源：\`${evidence.appResource.path}\`，SHA-256 \`${evidence.appResource.sha256}\`` : 'App 资源：缺失，先执行 npm run build:app',
      evidence.h5Index ? `H5 构建：\`${evidence.h5Index.path}\`，SHA-256 \`${evidence.h5Index.sha256}\`` : 'H5 构建：缺失，先执行 npm run build:h5',
      evidence.manifest ? `manifest：\`${evidence.manifest.path}\`，SHA-256 \`${evidence.manifest.sha256}\`` : 'manifest：缺失',
      evidence.storeIcon ? `App 图标母图：\`${evidence.storeIcon.path}\`，SHA-256 \`${evidence.storeIcon.sha256}\`` : 'App 图标母图：缺失，先执行 npm run release:app-icons',
      evidence.appIcons ? `App 图标资产检查：\`${evidence.appIcons}/report.json\`` : 'App 图标资产检查：缺失，先执行 npm run release:app-icons',
      evidence.mobileToolchainPlan ? `移动端工具链准备计划：\`${evidence.mobileToolchainPlan}/report.json\`` : '移动端工具链准备计划：缺失，先执行 npm run mobile:toolchain-plan',
      evidence.mobileEnv ? `移动端环境检查：\`${evidence.mobileEnv}/report.json\`` : '移动端环境检查：缺失，先执行 npm run mobile:build-env',
      evidence.hbuilderxResources ? `HBuilderX App Resource 检查：\`${evidence.hbuilderxResources}/report.json\`` : 'HBuilderX App Resource 检查：缺失，先执行 npm run mobile:hbuilderx-resources',
      evidence.platformHandoff ? `平台打包交接包：\`${evidence.platformHandoff}/README.md\`` : '平台打包交接包：缺失，先执行 npm run platform:handoff',
      evidence.loginSmoke ? `线上登录 smoke：\`${evidence.loginSmoke}/report.json\`` : '线上登录 smoke：缺失，先执行 npm run qa:login:local-online',
      evidence.agentEntry ? `时安 agent 入口验收：\`${evidence.agentEntry}/report.json\`` : '时安 agent 入口验收：缺失，先执行 npm run qa:agent:entry-online-login',
      evidence.lowImpactStatus ? `低影响状态：\`${evidence.lowImpactStatus}/report.json\`` : '低影响状态：缺失，先执行 npm run release:low-impact-status',
      platformCloudPackAttempt ? `HBuilderX 云打包尝试：\`${platformCloudPackAttempt}/attempt.json\`` : 'HBuilderX 云打包尝试：缺失；可执行 HBUILDERX_CLOUD_PACK_EXECUTE=1 HBUILDERX_CLOUD_PACK_PLATFORM=android npm run mobile:hbuilderx-cloud-pack 记录 DCloud 服务端检查结果。',
      request.id === 'ios' && evidence.iosLocalBuildAttempt ? `iOS 本地构建尝试：\`${evidence.iosLocalBuildAttempt}/attempt.json\`` : '',
      request.id === 'ios' && !evidence.iosLocalBuildAttempt ? 'iOS 本地构建尝试：缺失；可执行 IOS_LOCAL_BUILD_EXECUTE=1 npm run mobile:ios-local-build-attempt 记录 Xcode、simctl、签名身份、profile 和磁盘余量。' : '',
      request.id === 'harmony' && evidence.hbuilderxHarmonyPackAttempt ? `HBuilderX 鸿蒙本地打包尝试：\`${evidence.hbuilderxHarmonyPackAttempt}/attempt.json\`` : '',
      request.id === 'harmony' && !evidence.hbuilderxHarmonyPackAttempt ? 'HBuilderX 鸿蒙本地打包尝试：缺失；可执行 HBUILDERX_HARMONY_PACK_EXECUTE=1 npm run mobile:hbuilderx-harmony-pack 记录 DevEco/hdc/hvigor 检查结果。' : '',
      evidence.hbuilderxPluginInstall ? `HBuilderX 插件安装尝试：\`${evidence.hbuilderxPluginInstall}\`` : 'HBuilderX 插件安装尝试：本轮已手工补齐插件目录，最终状态以 mobile:build-env 为准。',
      evidence.legalUrlCheck ? `法律 URL 检查：\`${evidence.legalUrlCheck}/report.json\`` : '法律 URL 检查：缺失，先执行 npm run store:legal-urls',
      evidence.privacyDisclosure ? `隐私披露检查：\`${evidence.privacyDisclosure}/report.json\`` : '隐私披露检查：缺失，先执行 npm run store:privacy',
      evidence.storeMaterials ? `商店材料检查：\`${evidence.storeMaterials}/report.json\`` : '商店材料检查：缺失，先执行 npm run store:materials',
      request.id === 'android' && evidence.androidDebugApk ? `现有 Android 内部测试 APK：\`${evidence.androidDebugApk.path}\`，SHA-256 \`${evidence.androidDebugApk.sha256}\`` : '',
      request.id === 'android' && evidence.androidDebugAab ? `现有 Android App Bundle 结构预检 AAB：\`${evidence.androidDebugAab.path}\`，SHA-256 \`${evidence.androidDebugAab.sha256}\`` : '',
    ]),
    '',
    '## 已知本机阻塞与低影响规则',
    '',
    list(knownLocalBlockers),
    '',
    '## 打包命令',
    '',
    request.buildCommands.map((cmd) => `- \`${cmd}\``).join('\n'),
    '',
    '## 覆盖渠道',
    '',
    checklist(request.storeScope),
    '',
    '## 期望回传文件',
    '',
    checklist(request.expectedFiles),
    '',
    '## 必测流程',
    '',
    checklist(request.mustTest),
    '',
    '## 回传证据',
    '',
    checklist(request.returnEvidence),
    '',
    '## 回传后检查',
    '',
    checklist(commonAfterReturn),
    '',
    '## 禁止事项',
    '',
    '- [ ] 不把证书、密钥、签名文件、商店账号密码写入 GitHub、README、result.json 或截图说明。',
    '- [ ] 不复制一套业务逻辑给单独渠道；渠道差异只走配置、证书、包和截图材料。',
    '',
  ]
  writeFileSync(join(outDir, `${request.id}.md`), `${lines.join('\n')}\n`)
}

function main() {
  mkdirSync(outDir, { recursive: true })
  for (const request of requests) writeRequest(request)

  const manifest = {
    generatedAt: evidence.generatedAt,
    version,
    branch: evidence.branch,
    commit: evidence.commit,
    requestDir: rel(outDir),
    platforms: requests.map((request) => ({
      id: request.id,
      title: request.title,
      config: request.config,
      packageId: request.packageId,
      releaseInbox: `artifacts/release-inbox/${request.inbox}`,
      files: [`${request.id}.md`, `${request.id}.json`],
    })),
    inputEvidence: evidence,
    knownLocalBlockers,
  }
  writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)

  const readme = [
    `# ${version} 移动端构建请求包`,
    '',
    `> 生成时间：${evidence.generatedAt}`,
    `> commit：${evidence.commit || '未读取到'}`,
    `> 分支：${evidence.branch || 'unknown'}`,
    `> 输出目录：\`${rel(outDir)}\``,
    '',
    '## 请求文件',
    '',
    requests.map((request) => `- [${request.title}](./${request.id}.md)：回传到 \`artifacts/release-inbox/${request.inbox}\``).join('\n'),
    '',
    '## 当前判断',
    '',
    '- 这个请求包用于把 Android、iOS、鸿蒙打包任务交给 HBuilderX/DCloud、Xcode、DevEco 或外部打包机执行。',
    '- 当前本地继续复用线上登录逻辑，移动端真机验收必须覆盖登录/注册、时安 agent、积分中心和账号注销。',
    '- 移动端和桌面端统一使用你的 logo；打包人必须使用 `src/static/app-icons/app-icon-1024.png` 作为商店和平台图标母图。',
    '- 请求包不代表已经有 APK/AAB、IPA/TestFlight 或 HAP；回传产物后必须执行 `npm run release:intake` 和 `npm run release:artifact-metadata`。',
    '- HBuilderX 登录和 App 打包插件已恢复，三端 App Resource 可由 CLI 生成；这不是最终 APK/IPA/HAP。',
    '- Android/iOS 的 HBuilderX pack 云打包入口已确认；执行 `HBUILDERX_CLOUD_PACK_EXECUTE=1 HBUILDERX_CLOUD_PACK_PLATFORM=android npm run mobile:hbuilderx-cloud-pack` 可记录 DCloud 服务端检查结果。',
    '- 移动端工具链计划已记录 `/Volumes/XcodeAPFS` 作为 Xcode 外接 APFS 目标盘；Xcode 16.2 下载/安装当前最后卡在 Apple 下载认证，不把 Apple ID、FASTLANE_SESSION、证书或验证码写入仓库。',
    '- iOS 本地构建尝试会记录完整 Xcode、simctl、Apple 签名身份、provisioning profile 和磁盘余量；鸿蒙 `pack app-harmony` 当前明确缺 DevEco/hdc/hvigor。',
    '- 证书、keystore、p12、mobileprovision、签名口令和商店账号密码不得进入 GitHub。',
    '',
  ]
  writeFileSync(join(outDir, 'README.md'), `${readme.join('\n')}\n`)

  console.log(JSON.stringify({
    outDir: rel(outDir),
    platforms: requests.map((request) => request.id),
    appResourceReady: Boolean(evidence.appResource),
    appIconReady: Boolean(evidence.storeIcon && evidence.appIcons),
    loginSmoke: evidence.loginSmoke || null,
    agentEntry: evidence.agentEntry || null,
  }, null, 2))
}

main()
