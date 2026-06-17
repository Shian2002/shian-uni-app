#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.MOBILE_BUILD_ENV_STRICT === '1'
const stamp = localTimestamp()
const outDir = process.env.MOBILE_BUILD_ENV_OUT_DIR || join(root, 'artifacts', 'mobile-build-env', stamp)
const defaultAndroidSdkRoot = '/opt/homebrew/share/android-commandlinetools'
const detectedAndroidHome = process.env.ANDROID_HOME || process.env.ANDROID_SDK_ROOT || (existsSync(defaultAndroidSdkRoot) ? defaultAndroidSdkRoot : '')
const detectedJavaHome = process.env.JAVA_HOME || (existsSync('/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home') ? '/opt/homebrew/opt/openjdk@17/libexec/openjdk.jdk/Contents/Home' : '')
const shianExternalVolume = '/Volumes/时安500G'
const xcodeApfsVolume = '/Volumes/XcodeAPFS'
const minXcodeTargetGiB = Number(process.env.MOBILE_BUILD_ENV_MIN_XCODE_TARGET_GIB || 100)
const toolPath = [
  detectedJavaHome && join(detectedJavaHome, 'bin'),
  detectedAndroidHome && join(detectedAndroidHome, 'platform-tools'),
  detectedAndroidHome && join(detectedAndroidHome, 'cmdline-tools', 'latest', 'bin'),
  '/opt/homebrew/bin',
  process.env.PATH || '',
].filter(Boolean).join(':')
const toolEnv = {
  ...process.env,
  PATH: toolPath,
  ...(detectedJavaHome ? { JAVA_HOME: detectedJavaHome } : {}),
  ...(detectedAndroidHome ? { ANDROID_HOME: detectedAndroidHome, ANDROID_SDK_ROOT: detectedAndroidHome } : {}),
}

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function run(command, args = []) {
  try {
    const output = execFileSync(command, args, { cwd: root, env: toolEnv, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim()
    return { ok: true, command: [command, ...args].join(' '), output }
  } catch (error) {
    const stdout = String(error.stdout || '').trim()
    const stderr = String(error.stderr || '').trim()
    return { ok: false, command: [command, ...args].join(' '), output: stdout || stderr || error.message }
  }
}

function which(command) {
  return run('which', [command])
}

function redact(value) {
  return String(value || '')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '<redacted-email>')
    .replace(/(password|passwd|token|secret|certpassword|storepassword|privateKey)(=|:)\s*[^\s"'，,}]+/gi, '$1$2 <redacted>')
}

function runRedacted(command, args = []) {
  const result = run(command, args)
  return { ...result, output: redact(result.output) }
}

function diskInfo(path = root) {
  const result = run('df', ['-Pk', path])
  const line = result.output.split('\n')[1] || ''
  const parts = line.trim().split(/\s+/)
  const availableKb = Number(parts[3] || 0)
  return {
    ok: result.ok,
    command: result.command,
    path,
    availableKb,
    availableGiB: Math.round((availableKb / 1024 / 1024) * 10) / 10,
    output: result.output,
  }
}

function commandOutputIncludes(result, snippet) {
  return String(result?.output || '').includes(snippet)
}

function pathExists(path) {
  return existsSync(path)
}

function firstExisting(paths) {
  return paths.find((path) => pathExists(join(root, path))) || ''
}

function appExists(path) {
  return existsSync(path)
}

function hbuilderxPlugin(name) {
  return appExists(`/Applications/HBuilderX.app/Contents/HBuilderX/plugins/${name}/package.json`)
}

const env = {
  generatedAt: new Date().toISOString(),
  strict,
  disk: diskInfo(root),
  system: {
    macos: run('sw_vers', ['-productVersion']),
    build: run('sw_vers', ['-buildVersion']),
    arch: run('uname', ['-m']),
  },
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
  android: {
    java: run('java', ['-version']),
    gradle: run('gradle', ['-v']),
    adb: which('adb'),
    sdkmanager: which('sdkmanager'),
    javaHome: detectedJavaHome,
    androidHome: toolEnv.ANDROID_HOME || '',
    androidSdkRoot: toolEnv.ANDROID_SDK_ROOT || '',
    sdkPackages: run('sdkmanager', ['--list_installed']),
  },
  ios: {
    xcodeSelect: run('xcode-select', ['-p']),
    xcodebuild: which('xcodebuild'),
    xcodebuildVersion: run('xcodebuild', ['-version']),
    xcrun: which('xcrun'),
    simctl: run('xcrun', ['simctl', 'list', 'devices', 'available']),
    security: which('security'),
    mas: which('mas'),
    xcodesCli: which('xcodes'),
    xcodesApp: appExists('/Applications/Xcodes.app'),
    recommendedXcode: {
      version: '16.2',
      reason: '当前 macOS 14.8.7 优先使用 Xcode 16.2；Xcode 16.3/16.4 需要 macOS 15 系列起。',
      source: 'https://developer.apple.com/support/xcode/',
    },
  },
  harmony: {
    devecoStudio: appExists('/Applications/DevEco-Studio.app') || appExists('/Applications/DevEco Studio.app'),
    hdc: which('hdc'),
    hvigor: which('hvigor'),
  },
  uniApp: {
    hbuilderx: appExists('/Applications/HBuilderX.app'),
    hbuilderxCli: appExists('/Applications/HBuilderX.app/Contents/MacOS/cli'),
    hbuilderxUser: runRedacted('/Applications/HBuilderX.app/Contents/MacOS/cli', ['user', 'info']),
    hbuilderxPlugins: {
      launcher: hbuilderxPlugin('launcher'),
      appSafePack: hbuilderxPlugin('app-safe-pack'),
      launcherTools: hbuilderxPlugin('launcher-tools'),
      nodeModules: hbuilderxPlugin('node_modules'),
      amazonCorretto: hbuilderxPlugin('amazon-corretto'),
    },
    appResourceEntry: firstExisting(['dist/build/app/__uniappview.html', 'dist/build/app/index.html']),
    appResourceRuntime: pathExists(join(root, 'dist/build/app/app-service.js')),
    appResourceIndex: pathExists(join(root, 'dist/build/app/index.html')),
    appResourceAssets: pathExists(join(root, 'dist/build/app/assets')),
  },
}

function androidReady() {
  return env.android.java.ok &&
    env.android.gradle.ok &&
    env.android.adb.ok &&
    env.android.sdkmanager.ok &&
    Boolean(env.android.androidHome || env.android.androidSdkRoot) &&
    env.uniApp.appResourceEntry &&
    env.uniApp.appResourceRuntime
}

function iosReady() {
  return env.ios.xcodebuild.ok &&
    env.ios.xcodebuildVersion.ok &&
    env.ios.xcrun.ok &&
    env.ios.simctl.ok &&
    env.uniApp.appResourceEntry &&
    env.uniApp.appResourceRuntime
}

function harmonyReady() {
  return (env.harmony.devecoStudio || env.harmony.hdc.ok || env.harmony.hvigor.ok) &&
    env.uniApp.appResourceEntry &&
    env.uniApp.appResourceRuntime
}

const platforms = {
  android: androidReady() ? 'ready' : 'missing',
  ios: iosReady() ? 'ready' : (env.uniApp.hbuilderxCli && env.uniApp.appResourceEntry && env.uniApp.appResourceRuntime ? 'partial' : 'missing'),
  harmony: harmonyReady() ? 'partial' : 'missing',
  appResources: env.uniApp.appResourceEntry && env.uniApp.appResourceRuntime ? 'ready' : 'missing',
}
const isXcodeApfsReady = env.externalStorage.xcodeApfs.exists &&
  commandOutputIncludes(env.externalStorage.xcodeApfs.diskutil, 'File System Personality:   APFS')
const xcodeApfsFreeGiB = env.externalStorage.xcodeApfs.disk?.availableGiB || 0
const hasEnoughXcodeTargetSpace = isXcodeApfsReady && xcodeApfsFreeGiB >= minXcodeTargetGiB

const missing = [
  !env.uniApp.appResourceEntry && '缺少 dist/build/app/__uniappview.html，请先执行 npm run build:app',
  !env.uniApp.appResourceRuntime && '缺少 dist/build/app/app-service.js，请先执行 npm run build:app',
  !env.android.java.ok && 'Android 本机构建缺少 Java Runtime',
  !env.android.gradle.ok && 'Android 本机构建缺少 Gradle',
  !env.android.adb.ok && 'Android 真机安装缺少 adb',
  !env.android.sdkmanager.ok && 'Android SDK 缺少 sdkmanager',
  !(env.android.androidHome || env.android.androidSdkRoot) && 'Android SDK 环境变量 ANDROID_HOME/ANDROID_SDK_ROOT 未设置',
  !env.ios.xcodebuild.ok && 'iOS 构建缺少 xcodebuild',
  env.ios.xcodebuild.ok && !env.ios.xcodebuildVersion.ok && 'iOS 本机构建缺少完整 Xcode；当前只有 Command Line Tools 或 xcodebuild 不可用',
  !env.ios.simctl.ok && 'iOS 模拟器/真机自动化缺少 simctl；需要完整 Xcode',
  !env.uniApp.hbuilderx && 'DCloud 云打包缺少本机 HBuilderX 应用',
  env.uniApp.hbuilderx && !env.uniApp.hbuilderxCli && 'HBuilderX CLI 缺失，无法脚本化生成 App Resource',
  env.uniApp.hbuilderx && !env.uniApp.hbuilderxPlugins.launcher && 'HBuilderX 缺少 launcher 插件，无法运行/打包 App 平台',
  env.uniApp.hbuilderx && !env.uniApp.hbuilderxPlugins.appSafePack && 'HBuilderX 缺少 app-safe-pack 插件，无法进入 App 云打包/安全打包流程',
  !env.harmony.devecoStudio && !env.harmony.hdc.ok && !env.harmony.hvigor.ok && '鸿蒙构建缺少 DevEco Studio/hdc/hvigor',
].filter(Boolean)

const warnings = [
  env.disk.availableGiB > 0 && env.disk.availableGiB < 45 && !hasEnoughXcodeTargetSpace && `本机剩余空间不足以可靠安装完整 Xcode 或 DevEco Studio：${env.disk.availableGiB} GiB 可用，建议至少 45 GiB；当前已安装 Android 基础工具链仍可构建 debug APK。`,
  env.disk.availableGiB > 0 && env.disk.availableGiB < 45 && hasEnoughXcodeTargetSpace && `本机剩余空间 ${env.disk.availableGiB} GiB 低于 45 GiB 建议线；/Volumes/XcodeAPFS 已有 ${xcodeApfsFreeGiB} GiB APFS 空间承载 Xcode.app，安装时仍需保留下载/解压临时缓存空间。`,
  env.externalStorage.shian500g.exists && commandOutputIncludes(env.externalStorage.shian500g.diskutil, 'File System Personality:   ExFAT') && '外接盘 /Volumes/时安500G 是 ExFAT：可暂存下载包，但不适合直接承载 Xcode.app；应划分 APFS 卷或使用 APFS 外接盘。',
].filter(Boolean)

const report = {
  ...env,
  platforms,
  passed: missing.length === 0 && warnings.length === 0,
  missing,
  warnings,
  next: [
    platforms.android === 'ready'
      ? 'Android：当前本机 JDK、Gradle、Android SDK、adb 和 App Resource 已可用，可继续生成 debug APK；正式渠道包仍需签名和商店后台证据。'
      : 'Android：安装 JDK、Android Studio/SDK、配置 ANDROID_HOME 或使用 HBuilderX/DCloud 云打包。',
    'iOS：使用 Xcode 和 Apple Developer 证书生成 TestFlight 构建记录。',
    `iOS：当前系统优先准备 Xcode ${env.ios.recommendedXcode.version}；目标安装位置使用 /Volumes/XcodeAPFS APFS 外接盘。`,
    '鸿蒙：使用 DevEco Studio 或 HBuilderX 对应鸿蒙/华为渠道打包。',
    '安装包生成后放入 artifacts/release-inbox/，再执行 npm run release:intake。',
  ],
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

const status = (value) => value ? '可用' : '缺失'
const lines = [
  '# 移动端打包环境检查',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.passed ? '通过' : '未通过'}`,
  '',
  '## 平台状态',
  '',
  `- App 资源：${platforms.appResources}`,
  `- Android：${platforms.android}`,
  `- iOS：${platforms.ios}`,
  `- 鸿蒙：${platforms.harmony}`,
  `- 剩余空间：${env.disk.availableGiB || 0} GiB`,
  '',
  '## Android',
  '',
  `- Java：${status(env.android.java.ok)}，命令：\`${env.android.java.command}\``,
  `- JAVA_HOME：${env.android.javaHome || '未设置'}`,
  `- Gradle：${status(env.android.gradle.ok)}，命令：\`${env.android.gradle.command}\``,
  `- adb：${status(env.android.adb.ok)}`,
  `- sdkmanager：${status(env.android.sdkmanager.ok)}`,
  `- ANDROID_HOME：${env.android.androidHome || '未设置'}`,
  `- ANDROID_SDK_ROOT：${env.android.androidSdkRoot || '未设置'}`,
  '',
  '## iOS',
  '',
  `- macOS：${env.system.macos.output || '未检测到'}（${env.system.arch.output || 'unknown'}）`,
  `- xcode-select：${env.ios.xcodeSelect.output || '未检测到'}`,
  `- xcodebuild：${status(env.ios.xcodebuild.ok)}`,
  `- xcodebuild -version：${status(env.ios.xcodebuildVersion.ok)}`,
  `- xcrun：${status(env.ios.xcrun.ok)}`,
  `- simctl：${status(env.ios.simctl.ok)}`,
  `- Xcodes.app：${status(env.ios.xcodesApp)}`,
  `- xcodes CLI：${status(env.ios.xcodesCli.ok)}`,
  `- mas CLI：${status(env.ios.mas.ok)}`,
  `- 推荐 Xcode：${env.ios.recommendedXcode.version}（${env.ios.recommendedXcode.reason}）`,
  '',
  '## 外接盘',
  '',
  `- /Volumes/时安500G：${status(env.externalStorage.shian500g.exists)}`,
  `- 可用空间：${env.externalStorage.shian500g.disk?.availableGiB ?? '未知'} GiB`,
  `- 文件系统：${commandOutputIncludes(env.externalStorage.shian500g.diskutil, 'File System Personality:   ExFAT') ? 'ExFAT' : '见 report.json'}`,
  `- /Volumes/XcodeAPFS：${status(env.externalStorage.xcodeApfs.exists)}`,
  `- XcodeAPFS 可用空间：${env.externalStorage.xcodeApfs.disk?.availableGiB ?? '未知'} GiB`,
  `- XcodeAPFS 文件系统：${commandOutputIncludes(env.externalStorage.xcodeApfs.diskutil, 'File System Personality:   APFS') ? 'APFS' : '见 report.json'}`,
  '',
  '## HBuilderX',
  '',
  `- HBuilderX App：${status(env.uniApp.hbuilderx)}`,
  `- HBuilderX CLI：${status(env.uniApp.hbuilderxCli)}`,
  `- DCloud 用户信息：${status(env.uniApp.hbuilderxUser.ok)}`,
  `- launcher 插件：${status(env.uniApp.hbuilderxPlugins.launcher)}`,
  `- app-safe-pack 插件：${status(env.uniApp.hbuilderxPlugins.appSafePack)}`,
  `- launcher-tools 插件：${status(env.uniApp.hbuilderxPlugins.launcherTools)}`,
  `- node_modules 依赖插件：${status(env.uniApp.hbuilderxPlugins.nodeModules)}`,
  `- amazon-corretto 插件：${status(env.uniApp.hbuilderxPlugins.amazonCorretto)}`,
  '',
  '## 鸿蒙',
  '',
  `- DevEco Studio：${status(env.harmony.devecoStudio)}`,
  `- hdc：${status(env.harmony.hdc.ok)}`,
  `- hvigor：${status(env.harmony.hvigor.ok)}`,
  '',
  '## 缺口',
  '',
  ...(missing.length ? missing.map((item) => `- ${item}`) : ['- 暂无缺口。']),
  '',
  '## 警告',
  '',
  ...(warnings.length ? warnings.map((item) => `- ${item}`) : ['- 暂无警告。']),
  '',
  '## 下一步',
  '',
  ...report.next.map((item) => `- ${item}`),
]
writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: report.passed,
  platforms,
  missing,
  warnings,
}, null, 2))

if (strict && !report.passed) process.exit(1)
