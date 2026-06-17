#!/usr/bin/env node

import { createHash } from 'node:crypto'
import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.PLATFORM_HANDOFF_VERSION || `v${packageJson.version || '0.0.0'}`
const outDir = process.env.PLATFORM_HANDOFF_DIR || join(root, 'artifacts', 'platform-build-handoffs', `${localTimestamp()}-${version}`)

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

function latestDir(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => b.name.localeCompare(a.name))
  return dirs[0] ? join(path, dirs[0].name) : ''
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

function list(items) {
  return items.map((item) => `- ${item}`).join('\n')
}

function checklist(items) {
  return items.map((item) => `- [ ] ${item}`).join('\n')
}

const android = readJson('configs/release/android-channels.json') || { channels: [] }
const ios = readJson('configs/release/ios-appstore.json') || {}
const harmony = readJson('configs/release/harmony-appgallery.json') || {}
const desktop = readJson('configs/release/desktop.json') || {}

const evidence = {
  generatedAt: new Date().toISOString(),
  version,
  branch: git(['branch', '--show-current']) || '',
  commit: git(['rev-parse', 'HEAD']) || '',
  appResource: appResourceEvidence(),
  h5Index: fileEvidence('dist/build/h5/index.html'),
  storeIcon: fileEvidence('src/static/app-icons/app-icon-1024.png'),
  appIcons: latestReportDirWith('artifacts/app-icons', 'report.json'),
  androidDebugApk: latestInboxArtifact('android', '.apk'),
  androidDebugAab: latestInboxArtifact('android', '.aab'),
  macDmg: fileEvidence('desktop/release/时安解忧屋-1.0.0-arm64.dmg'),
  macZip: fileEvidence('desktop/release/时安解忧屋-1.0.0-arm64.app.zip'),
  windowsExe: fileEvidence('desktop/release/时安解忧屋 Setup 1.0.0.exe'),
  releaseManifest: latestFile('artifacts/release-manifests', '.json'),
  releaseReadiness: latestFile('artifacts/release-readiness', '.md'),
  releaseSummary: latestFile('artifacts/release-summaries', '.md'),
  releasePackage: latestDir('artifacts/release-packages'),
  storePacket: latestDir('artifacts/store-submission-packets'),
  realUserPacket: latestDir('artifacts/real-user-packets'),
  storeScreenshots: latestReportDirWith('artifacts/store-screenshots', 'summary.json'),
  loginSmoke: latestReportDirWith('artifacts/login-smoke', 'report.json'),
  agentEntry: latestReportDirWith('artifacts/agent-entry', 'report.json'),
  desktopSmoke: latestReportDirWith('artifacts/desktop-smoke', 'report.json'),
}

const platforms = [
  {
    id: 'android',
    title: 'Android APK/AAB 打包交接',
    config: 'configs/release/android-channels.json',
    packageIds: [android.packageName],
    expectedOutputs: [
      '应用宝、华为、小米、OPPO、vivo：APK 或渠道后台接受的包格式',
      'Google Play：AAB',
      '每个包对应 SHA-256、versionName、versionCode、构建时间和构建人',
    ],
    commands: [
      'npm run lint',
      'npm run typecheck',
      'npm run test',
      'npm run build:app',
      'MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight',
      'npm run release:app-icons',
      '在 HBuilderX 或 DCloud 云打包中导入 dist/build/app，使用 src/static/app-icons/app-icon-1024.png 作为应用图标母图，并使用安全渠道提供的 Android 签名证书生成 APK/AAB',
    ],
    checks: android.requiredChecks || [],
    screenshots: ['首页', '旧登录弹窗', '时安 agent 工作台', '积分会员页', '八字工具页', '账号注销入口'],
    upload: 'GitHub Releases + 对应安卓市场后台',
    hardNo: ['keystore/jks 不进 GitHub', '签名口令不写入 README/result.json', '不要为单个应用商店拆新仓库'],
  },
  {
    id: 'ios',
    title: 'iOS TestFlight/App Store 打包交接',
    config: 'configs/release/ios-appstore.json',
    packageIds: [ios.bundleId],
    expectedOutputs: [
      'TestFlight 构建号或 IPA 构建记录',
      'App Privacy 表单截图',
      'iPhone 和 iPad 截图',
      '审核账号和审核备注交付记录，不在 GitHub 写密码',
    ],
    commands: [
      'npm run lint',
      'npm run typecheck',
      'npm run build:app',
      'MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight',
      'npm run release:app-icons',
      '在 HBuilderX/DCloud 或 Xcode/iOS 打包环境中使用 src/static/app-icons/app-icon-1024.png 作为应用图标母图，并使用 Apple 证书生成 TestFlight 构建',
    ],
    checks: ios.requiredChecks || [],
    screenshots: ['iPhone 首页', 'iPhone Agent', 'iPhone 账号注销', 'iPad 横屏/竖屏', 'App Privacy 和账号删除后台说明'],
    upload: 'App Store Connect TestFlight + GitHub Releases 记录构建号和 hash',
    hardNo: ['p12/mobileprovision 不进 GitHub', '未接 IAP 前不要在 iOS App 内暴露违规第三方数字内容充值入口'],
  },
  {
    id: 'harmony',
    title: '鸿蒙/AppGallery 打包交接',
    config: 'configs/release/harmony-appgallery.json',
    packageIds: [harmony.bundleName],
    expectedOutputs: [
      'HAP/AppGallery 包或华为后台构建记录',
      '手机和平板截图',
      '权限触发时机说明',
      '华为后台提交状态或测试链接',
    ],
    commands: [
      'npm run lint',
      'npm run typecheck',
      'npm run build:app',
      'MOBILE_PREFLIGHT_REQUIRE_BUILD=1 npm run mobile:preflight',
      'npm run release:app-icons',
      '在华为/鸿蒙打包环境使用 src/static/app-icons/app-icon-1024.png 作为应用图标母图，生成 HAP/AppGallery 测试包；如转为 DevEco 原生工程，再评估是否拆 shian-harmony-shell',
    ],
    checks: harmony.requiredChecks || [],
    screenshots: ['鸿蒙手机首页', '鸿蒙手机 Agent', '鸿蒙平板 Agent', '权限弹窗', '账号注销'],
    upload: 'GitHub Releases + 华为开发者后台',
    hardNo: ['鸿蒙签名资料不进 GitHub', '不要把鸿蒙临时工程复制出一套业务逻辑'],
  },
  {
    id: 'macos',
    title: 'macOS 下载包交接',
    config: 'configs/release/desktop.json',
    packageIds: [desktop.appId],
    expectedOutputs: [
      'DMG 或 ZIP',
      'SHA-256',
      '签名和 notarization 状态',
      '首次打开、登录弹窗、Agent、窗口缩放截图',
    ],
    commands: [
      'npm run desktop:pack',
      'ditto -c -k --sequesterRsrc --keepParent "desktop/release/mac-arm64/时安解忧屋.app" "desktop/release/时安解忧屋-1.0.0-arm64.app.zip"',
      'DESKTOP_SMOKE_EXECUTABLE="<repo>/desktop/release/mac-arm64/时安解忧屋.app/Contents/MacOS/时安解忧屋" npm run desktop:smoke',
    ],
    checks: desktop.requiredChecks || [],
    screenshots: ['首次打开', '登录弹窗', '时安 agent', '积分中心', '窗口缩放'],
    upload: 'GitHub Releases 或官网',
    hardNo: ['Developer ID 证书和 notarization 凭据不进 GitHub'],
  },
  {
    id: 'windows',
    title: 'Windows EXE/MSI 打包交接',
    config: 'configs/release/desktop.json',
    packageIds: [desktop.appId],
    expectedOutputs: [
      'NSIS/EXE 或 MSI',
      'SHA-256',
      '安装、开始菜单、首次打开、卸载截图',
      'Windows 10/11 测试记录',
    ],
    commands: [
      '在 Windows 10/11 打包机拉取同一 commit',
      'npm ci',
      'npm run desktop:build',
      'npm run desktop:smoke 或手工按真实用户验收单回填',
    ],
    checks: desktop.requiredChecks || [],
    screenshots: ['安装向导', '开始菜单', '首次打开', '登录弹窗', '时安 agent', '卸载入口'],
    upload: 'GitHub Releases 或官网',
    hardNo: ['Windows 代码签名证书不进 GitHub', '不要上传未记录 hash 的安装包'],
  },
]

function writePlatform(platform) {
  const path = join(outDir, `${platform.id}.md`)
  const md = [
    `# ${platform.title}`,
    '',
    `> 生成时间：${evidence.generatedAt}`,
    `> 版本：${version}`,
    `> commit：${evidence.commit || '未读取到'}`,
    `> 配置文件：\`${platform.config}\``,
    `> 包标识：${platform.packageIds.filter(Boolean).join(' / ') || '待配置'}`,
    '',
    '## 当前输入证据',
    '',
    list([
      evidence.appResource ? `App 资源：\`${evidence.appResource.path}\`，SHA-256 \`${evidence.appResource.sha256}\`` : 'App 资源：缺失，先运行 npm run build:app',
      evidence.h5Index ? `H5 构建：\`${evidence.h5Index.path}\`，SHA-256 \`${evidence.h5Index.sha256}\`` : 'H5 构建：缺失，先运行 npm run build:h5',
      evidence.releaseManifest ? `Release manifest：\`${evidence.releaseManifest}\`` : 'Release manifest：缺失，先运行 npm run release:manifest',
      evidence.releaseSummary ? `Release summary：\`${evidence.releaseSummary}\`` : 'Release summary：缺失',
      evidence.storeScreenshots ? `H5 截图候选：\`${evidence.storeScreenshots}\`` : 'H5 截图候选：缺失',
      evidence.loginSmoke ? `线上登录 smoke：\`${evidence.loginSmoke}/report.json\`` : '线上登录 smoke：缺失',
      evidence.agentEntry ? `Agent 入口验收：\`${evidence.agentEntry}/report.json\`` : 'Agent 入口验收：缺失',
      platform.id === 'android' && evidence.androidDebugApk ? `当前 Android 内部测试 APK：\`${evidence.androidDebugApk.path}\`，SHA-256 \`${evidence.androidDebugApk.sha256}\`` : '',
      platform.id === 'android' && evidence.androidDebugAab ? `当前 Android App Bundle 结构预检 AAB：\`${evidence.androidDebugAab.path}\`，SHA-256 \`${evidence.androidDebugAab.sha256}\`` : '',
      platform.id === 'macos' && evidence.macDmg ? `当前 macOS DMG：\`${evidence.macDmg.path}\`，SHA-256 \`${evidence.macDmg.sha256}\`` : '',
      platform.id === 'macos' && evidence.macZip ? `当前 macOS ZIP：\`${evidence.macZip.path}\`，SHA-256 \`${evidence.macZip.sha256}\`` : '',
      platform.id === 'macos' && evidence.desktopSmoke ? `macOS smoke：\`${evidence.desktopSmoke}/report.json\`` : '',
      platform.id === 'windows' && evidence.windowsExe ? `当前 Windows NSIS：\`${evidence.windowsExe.path}\`，SHA-256 \`${evidence.windowsExe.sha256}\`` : '',
    ].filter(Boolean)),
    '',
    '## 打包前命令',
    '',
    platform.commands.map((cmd) => `- \`${cmd}\``).join('\n'),
    '',
    '## 必须产出',
    '',
    checklist(platform.expectedOutputs),
    '',
    '## 必测流程',
    '',
    checklist(platform.checks),
    '',
    '## 截图清单',
    '',
    checklist(platform.screenshots),
    '',
    '## 上传和归档',
    '',
    `- 上传位置：${platform.upload}`,
    '- 在 GitHub Release 或商店后台记录版本号、commit、构建命令、安装包 SHA-256、测试账号交付方式和审核状态。',
    '- 回收真实用户截图后，按 `real-user:check` 的 result.json 格式补齐。',
    '',
    '## 禁止事项',
    '',
    checklist(platform.hardNo),
    '',
  ].join('\n')
  writeFileSync(path, md)
}

function main() {
  mkdirSync(outDir, { recursive: true })
  for (const platform of platforms) writePlatform(platform)
  const manifest = {
    ...evidence,
    handoffDir: rel(outDir),
    platforms: platforms.map((platform) => ({
      id: platform.id,
      file: `${platform.id}.md`,
      expectedOutputs: platform.expectedOutputs,
      upload: platform.upload,
    })),
  }
  writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
  const readme = [
    `# ${version} 平台打包交接包`,
    '',
    `> 生成时间：${evidence.generatedAt}`,
    `> commit：${evidence.commit || '未读取到'}`,
    `> 分支：${evidence.branch || 'unknown'}`,
    '',
    '## 文件',
    '',
    platforms.map((platform) => `- [${platform.title}](./${platform.id}.md)`).join('\n'),
    '',
    '## 当前结论',
    '',
    '- 本交接包只包含非敏感配置、构建证据、命令、截图和验收清单。',
    '- 移动端和桌面端统一使用你的 logo；图标母图是 `src/static/app-icons/app-icon-1024.png`，检查报告来自 `npm run release:app-icons`。',
    '- 证书、keystore、p12、mobileprovision、代码签名口令、商店后台账号密码不得写入本目录或 GitHub。',
    '- Android/iOS/鸿蒙/Windows 仍需要对应平台打包环境和真机回收；macOS 当前只有未签名测试 ZIP。',
    '',
  ].join('\n')
  writeFileSync(join(outDir, 'README.md'), readme)
  console.log(JSON.stringify({ outDir: rel(outDir), platforms: platforms.length }, null, 2))
}

main()
