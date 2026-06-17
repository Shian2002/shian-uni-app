#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.MOBILE_TOOLCHAIN_PLAN_VERSION || `v${packageJson.version || '0.0.0'}`
const strict = process.argv.includes('--strict') || process.env.MOBILE_TOOLCHAIN_PLAN_STRICT === '1'
const outDir = process.env.MOBILE_TOOLCHAIN_PLAN_OUT_DIR || join(root, 'artifacts', 'mobile-toolchain-plan', `${localTimestamp()}-${version}`)
const shianExternalVolume = '/Volumes/时安500G'
const xcodeApfsVolume = '/Volumes/XcodeAPFS'
const hbuilderxSupportDir = join(process.env.HOME || '', 'Library', 'Application Support', 'HBuilder X')
const minFreeGiB = Number(process.env.MOBILE_TOOLCHAIN_PLAN_MIN_FREE_GIB || 45)
const minXcodeTargetGiB = Number(process.env.MOBILE_TOOLCHAIN_PLAN_MIN_XCODE_TARGET_GIB || 100)

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

function redact(value) {
  return String(value || '')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '<redacted-email>')
    .replace(/(password|passwd|token|secret|certpassword|storepassword|privateKey)(=|:)\s*[^\s"'，,}]+/gi, '$1$2 <redacted>')
}

function run(command, args = []) {
  try {
    const output = execFileSync(command, args, {
      cwd: root,
      encoding: 'utf8',
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env, LC_ALL: 'en_US.UTF-8', LANG: 'en_US.UTF-8' },
    }).trim()
    return { ok: true, command: [command, ...args].join(' '), output: redact(output) }
  } catch (error) {
    const stdout = String(error.stdout || '').trim()
    const stderr = String(error.stderr || '').trim()
    return { ok: false, command: [command, ...args].join(' '), output: redact(stdout || stderr || error.message) }
  }
}

function which(command) {
  return run('which', [command])
}

function diskInfo(path = root) {
  const result = run('df', ['-Pk', path])
  const line = result.output.split('\n')[1] || ''
  const parts = line.trim().split(/\s+/)
  const availableKb = Number(parts[3] || 0)
  return {
    ok: result.ok,
    path,
    availableKb,
    availableGiB: Math.round((availableKb / 1024 / 1024) * 10) / 10,
    output: result.output,
  }
}

function commandOutputIncludes(result, snippet) {
  return String(result?.output || '').includes(snippet)
}

function step(id, owner, title, command, reason) {
  return { id, owner, title, command, reason }
}

const checks = {
  system: {
    macos: run('sw_vers', ['-productVersion']),
    build: run('sw_vers', ['-buildVersion']),
    arch: run('uname', ['-m']),
  },
  disk: diskInfo(root),
  externalStorage: {
    shian500g: {
      path: shianExternalVolume,
      exists: existsSync(shianExternalVolume),
      disk: existsSync(shianExternalVolume) ? diskInfo(shianExternalVolume) : null,
      diskutil: existsSync(shianExternalVolume) ? run('diskutil', ['info', shianExternalVolume]) : null,
    },
    xcodeApfs: {
      path: xcodeApfsVolume,
      exists: existsSync(xcodeApfsVolume),
      disk: existsSync(xcodeApfsVolume) ? diskInfo(xcodeApfsVolume) : null,
      diskutil: existsSync(xcodeApfsVolume) ? run('diskutil', ['info', xcodeApfsVolume]) : null,
    },
  },
  ios: {
    xcodeSelect: run('xcode-select', ['-p']),
    xcodebuildVersion: run('xcodebuild', ['-version']),
    simctl: run('xcrun', ['simctl', 'list', 'devices', '--json']),
    mas: which('mas'),
    xcodesCli: which('xcodes'),
    xcodesApp: existsSync('/Applications/Xcodes.app'),
    fullXcodeApp: existsSync('/Applications/Xcode.app'),
    recommendedXcode: {
      version: '16.2',
      reason: 'macOS 14.8.7 优先使用 Xcode 16.2；Xcode 16.3/16.4 需要 macOS 15 系列起。',
      source: 'https://developer.apple.com/support/xcode/',
    },
  },
  harmony: {
    devecoStudio: existsSync('/Applications/DevEco-Studio.app') || existsSync('/Applications/DevEco Studio.app'),
    devecoCandidates: [
      '/Applications/DevEco-Studio.app',
      '/Applications/DevEco Studio.app',
      join(process.env.HOME || '', 'Applications', 'DevEco-Studio.app'),
      join(process.env.HOME || '', 'Applications', 'DevEco Studio.app'),
    ].filter((path) => existsSync(path)),
    hdc: which('hdc'),
    hvigor: which('hvigor'),
    hbuilderxHarmonyPlugin: existsSync('/Applications/HBuilderX.app/Contents/HBuilderX/plugins/launcher-harmony'),
    generatedHarmonyResource: existsSync(join(root, 'dist', 'build', '.app-harmony')),
    hbuilderxSupportDirExists: existsSync(hbuilderxSupportDir),
    recommendedDevEco: {
      source: 'https://developer.huawei.com/consumer/cn/deveco-studio/',
      downloadCenter: 'https://developer.huawei.com/consumer/cn/download/',
      macosRequirement: 'macOS ARM 12/13/14/15/26 或 macOS X86 11/12/13/14/15/26，硬盘 100GB 及以上。',
      reason: 'HBuilderX pack app-harmony 需要 DevEco Studio、hdc、hvigor，并且需要在 HBuilderX 偏好设置中配置鸿蒙开发者工具路径。',
    },
  },
  hbuilderx: {
    app: existsSync('/Applications/HBuilderX.app'),
    cli: existsSync('/Applications/HBuilderX.app/Contents/MacOS/cli'),
  },
}

const isShian500gExFat = checks.externalStorage.shian500g.exists &&
  commandOutputIncludes(checks.externalStorage.shian500g.diskutil, 'File System Personality:   ExFAT')
const isXcodeApfsReady = checks.externalStorage.xcodeApfs.exists &&
  commandOutputIncludes(checks.externalStorage.xcodeApfs.diskutil, 'File System Personality:   APFS')
const hasFullXcode = checks.ios.fullXcodeApp && checks.ios.xcodebuildVersion.ok && !commandOutputIncludes(checks.ios.xcodebuildVersion, 'requires Xcode')
const hasSimctl = checks.ios.simctl.ok
const hasDevEco = checks.harmony.devecoStudio || checks.harmony.hdc.ok || checks.harmony.hvigor.ok
const hasEnoughInternalSpace = checks.disk.availableGiB >= minFreeGiB
const xcodeApfsFreeGiB = checks.externalStorage.xcodeApfs.disk?.availableGiB || 0
const hasEnoughXcodeTargetSpace = isXcodeApfsReady && xcodeApfsFreeGiB >= minXcodeTargetGiB

const automaticSteps = [
  !checks.ios.xcodesCli.ok && step(
    'install-xcodes-cli',
    'environment-action',
    '安装 xcodes CLI',
    'brew install xcodesorg/made/xcodes',
    '本机已有 Xcodes.app GUI，但缺少可脚本化的 xcodes CLI；安装 CLI 后才能自动列出/下载指定 Xcode 版本。'
  ),
  !hasEnoughInternalSpace && step(
    'free-internal-space',
    'environment-action',
    hasEnoughXcodeTargetSpace ? '保留内置盘临时缓存余量' : '继续释放内置盘空间',
    'npm run artifacts:prune -- --keep=2 && npm run release:package-cleanup-plan -- --keep=2',
    hasEnoughXcodeTargetSpace
      ? `当前内置盘约 ${checks.disk.availableGiB} GiB 可用，低于 ${minFreeGiB} GiB 建议线；/Volumes/XcodeAPFS 已有 ${xcodeApfsFreeGiB} GiB APFS 空间承载 Xcode.app，内置盘只作为下载/解压临时缓存保守清理。`
      : `当前内置盘约 ${checks.disk.availableGiB} GiB 可用，低于 ${minFreeGiB} GiB 建议线；继续优先清理缓存和旧产物，不删除 current-downloads/release-inbox。`
  ),
  !isXcodeApfsReady && isShian500gExFat && step(
    'prepare-apfs-volume',
    'environment-action',
    '把外接盘准备成 APFS 环境',
    '使用磁盘工具给 /Volumes/时安500G 划分独立 APFS 卷，或改用 APFS 外接盘。',
    'ExFAT 可暂存下载包，但不适合直接运行 Xcode.app；本机 sparsebundle APFS 初始化已验证不可靠。'
  ),
  !hasFullXcode && step(
    'install-xcode-16-2',
    'environment-action',
    '安装完整 Xcode 16.2',
    'xcodes install 16.2 --directory /Volumes/XcodeAPFS --experimental-unxip --no-superuser --empty-trash',
    '当前 macOS 14.8.7 不应默认安装需要 macOS 15 的 Xcode 16.3/16.4；完整 Xcode 会补齐 xcodebuild 和 simctl。'
  ),
  !hasDevEco && step(
    'install-deveco',
    'environment-action',
    '安装 DevEco Studio/hdc/hvigor',
    '从 https://developer.huawei.com/consumer/cn/download/ 下载 DevEco Studio macOS 版本并安装。',
    'HBuilderX pack app-harmony 当前阻塞为缺少 DevEco/hdc/hvigor；官方 macOS 要求硬盘 100GB 及以上，安装后还要在 HBuilderX 偏好设置里配置鸿蒙开发者工具路径。'
  ),
].filter(Boolean)

const userLastSteps = [
  !hasFullXcode && step(
    'apple-download-auth',
    'user-last',
    '完成 Apple 下载认证',
    '在 Xcodes.app 登录 Apple ID，或给 xcodes CLI 配置 fastlane session 后重跑 Xcode 16.2 安装命令。',
    'xcodes install 已推进到 Apple ID 认证；不要把 Apple ID 密码、验证码或 FASTLANE_SESSION 写进聊天、GitHub 或报告。'
  ),
  step(
    'apple-signing',
    'user-last',
    '补 Apple Developer 签名资料',
    '在 Apple Developer / Xcode / HBuilderX 中配置证书和 provisioning profile。',
    'p12、mobileprovision、Apple ID、验证码和签名口令不得进入 GitHub。'
  ),
  step(
    'dcloud-phone-and-app',
    'user-last',
    '完成 DCloud 手机号复验和包名/隐私配置',
    '在 DCloud 开发者中心处理手机号复验、Android 包名录入和隐私配置。',
    'Android 云打包已进入 DCloud 服务端检查，当前卡在账号/后台配置。'
  ),
  step(
    'huawei-signing',
    'user-last',
    '补华为/鸿蒙开发者账号和签名配置',
    '在华为 AppGallery/DevEco 中配置应用、签名和测试发布材料。',
    '华为账号、签名口令和后台凭据不得进入 GitHub。'
  ),
  !hasDevEco && step(
    'hbuilderx-harmony-tool-path',
    'user-last',
    '在 HBuilderX 里确认鸿蒙工具路径',
    'HBuilderX -> 偏好设置 -> 运行配置 -> 鸿蒙开发者工具路径，指向 DevEco Studio/SDK 路径后重跑 HBUILDERX_HARMONY_PACK_EXECUTE=1 npm run mobile:hbuilderx-harmony-pack。',
    '本机可以检测 DevEco/hdc/hvigor，但 HBuilderX 的 GUI 偏好设置可能仍需要你确认一次；不在脚本里写 HBuilderX 用户配置，避免误保存账号或 secret。'
  ),
].filter(Boolean)

const blockers = [
  !hasEnoughInternalSpace && !hasEnoughXcodeTargetSpace && `内置盘可用空间 ${checks.disk.availableGiB} GiB，低于 ${minFreeGiB} GiB 建议线，且没有 ${minXcodeTargetGiB} GiB 以上 APFS Xcode 目标盘。`,
  !isXcodeApfsReady && '缺少可承载 Xcode.app 的 APFS 外接卷 /Volumes/XcodeAPFS。',
  isShian500gExFat && '/Volumes/时安500G 为 ExFAT，不适合直接承载 Xcode.app。',
  !hasFullXcode && '缺少完整 Xcode 16.2 和可用 xcodebuild。',
  !hasSimctl && '缺少 simctl。',
  !hasDevEco && '缺少 DevEco Studio/hdc/hvigor。',
  !checks.ios.xcodesCli.ok && '缺少 xcodes CLI。',
].filter(Boolean)

const report = {
  generatedAt: new Date().toISOString(),
  version,
  strict,
  passed: blockers.length === 0,
  checks,
  blockers,
  warnings: [
    !hasEnoughInternalSpace && hasEnoughXcodeTargetSpace && `内置盘 ${checks.disk.availableGiB} GiB 低于 ${minFreeGiB} GiB 建议线，但 /Volumes/XcodeAPFS 有 ${xcodeApfsFreeGiB} GiB APFS 空间，Xcode.app 可放外接盘；下载/解压仍可能需要临时缓存空间。`,
  ].filter(Boolean),
  automaticSteps,
  userLastSteps,
  boundaries: [
    '不自动登录 Apple、DCloud、华为账号。',
    '不保存 p12、mobileprovision、keystore、签名口令、验证码或后台凭据。',
    '不删除 artifacts/current-downloads、artifacts/release-inbox 或当前索引引用的安装包。',
  ],
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# 移动端工具链准备计划',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  '',
  '## 当前状态',
  '',
  `- macOS：${checks.system.macos.output || 'unknown'} (${checks.system.arch.output || 'unknown'})`,
  `- 内置盘可用空间：${checks.disk.availableGiB} GiB`,
  `- /Volumes/时安500G：${checks.externalStorage.shian500g.exists ? `${checks.externalStorage.shian500g.disk?.availableGiB ?? '未知'} GiB，可用；${isShian500gExFat ? 'ExFAT' : '非 ExFAT 或见 report.json'}` : '不存在'}`,
  `- /Volumes/XcodeAPFS：${checks.externalStorage.xcodeApfs.exists ? `${checks.externalStorage.xcodeApfs.disk?.availableGiB ?? '未知'} GiB，可用；${isXcodeApfsReady ? 'APFS' : '非 APFS 或见 report.json'}` : '不存在'}`,
  `- Xcodes.app：${checks.ios.xcodesApp ? '可用' : '缺失'}`,
  `- xcodes CLI：${checks.ios.xcodesCli.ok ? '可用' : '缺失'}`,
  `- 推荐 Xcode：${checks.ios.recommendedXcode.version}`,
  `- 完整 Xcode：${hasFullXcode ? '可用' : '缺失'}`,
  `- simctl：${hasSimctl ? '可用' : '缺失'}`,
  `- DevEco/hdc/hvigor：${hasDevEco ? '部分可用' : '缺失'}`,
  `- HBuilderX 鸿蒙插件：${checks.harmony.hbuilderxHarmonyPlugin ? '可用' : '缺失'}`,
  `- HBuilderX .app-harmony 资源：${checks.harmony.generatedHarmonyResource ? '存在' : '缺失'}`,
  `- DevEco 下载入口：${checks.harmony.recommendedDevEco.downloadCenter}`,
  `- DevEco macOS 要求：${checks.harmony.recommendedDevEco.macosRequirement}`,
  '',
  '## 自动/环境动作',
  '',
  ...(automaticSteps.length ? automaticSteps.map((item) => `- ${item.title}：\`${item.command}\`。${item.reason}`) : ['- 暂无。']),
  '',
  '## 最后必须你处理',
  '',
  ...userLastSteps.map((item) => `- ${item.title}：\`${item.command}\`。${item.reason}`),
  '',
  '## 阻塞',
  '',
  ...(blockers.length ? blockers.map((item) => `- ${item}`) : ['- 暂无。']),
  '',
  '## 提醒',
  '',
  ...(report.warnings.length ? report.warnings.map((item) => `- ${item}`) : ['- 暂无。']),
  '',
  '## 边界',
  '',
  ...report.boundaries.map((item) => `- ${item}`),
  '',
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  blockers,
  automaticSteps: automaticSteps.map((item) => item.id),
  userLastSteps: userLastSteps.map((item) => item.id),
}, null, 2))

if (strict && !report.passed) process.exit(1)
