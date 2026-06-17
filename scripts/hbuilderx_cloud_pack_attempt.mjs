#!/usr/bin/env node

import { spawnSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.HBUILDERX_CLOUD_PACK_VERSION || `v${packageJson.version || '0.0.0'}`
const platform = cliOption('--platform') || process.env.HBUILDERX_CLOUD_PACK_PLATFORM || 'android'
const execute = process.argv.includes('--execute') || process.env.HBUILDERX_CLOUD_PACK_EXECUTE === '1'
const strict = process.argv.includes('--strict') || process.env.HBUILDERX_CLOUD_PACK_STRICT === '1'
const timeoutMs = Number(process.env.HBUILDERX_CLOUD_PACK_TIMEOUT_MS || 600000)
const cliPath = process.env.HBUILDERX_CLI || '/Applications/HBuilderX.app/Contents/MacOS/cli'
const outDir = process.env.HBUILDERX_CLOUD_PACK_OUT_DIR || join(root, 'artifacts', 'hbuilderx-cloud-pack-attempts', `${localTimestamp()}-${version}-${platform}`)

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

function cliOption(name) {
  const exactIndex = process.argv.indexOf(name)
  if (exactIndex >= 0) return process.argv[exactIndex + 1] || ''
  const prefix = `${name}=`
  const arg = process.argv.find((item) => item.startsWith(prefix))
  return arg ? arg.slice(prefix.length) : ''
}

function redact(value) {
  return String(value || '')
    .replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '<redacted-email>')
    .replace(/(certpassword|storepassword|password|passwd|privateKey|token|secret)(=|:)\s*[^\s"'，,}<>]+/gi, '$1$2 <redacted>')
    .replace(/(--(?:ios\.)?certpassword\s+)[^\s]+/gi, '$1<redacted>')
    .replace(/(--(?:android\.)?certpassword\s+)[^\s]+/gi, '$1<redacted>')
    .replace(/(--(?:android\.)?storepassword\s+)[^\s]+/gi, '$1<redacted>')
}

function redactedArgs(args) {
  const secretFlags = new Set([
    '--ios.certpassword',
    '--android.certpassword',
    '--android.storepassword',
    '--privateKey',
  ])
  const result = []
  for (let index = 0; index < args.length; index += 1) {
    const arg = args[index]
    result.push(arg)
    if (secretFlags.has(arg) && index + 1 < args.length) {
      result.push('<redacted>')
      index += 1
    }
  }
  return result
}

function buildPackArgs() {
  const androidConfig = readJson('configs/release/android-channels.json') || {}
  const iosConfig = readJson('configs/release/ios-appstore.json') || {}
  const args = [
    'pack',
    '--project', root,
    '--platform', platform,
    '--safemode', process.env.HBUILDERX_CLOUD_PACK_SAFE_MODE || 'true',
    '--sourceMap', process.env.HBUILDERX_CLOUD_PACK_SOURCE_MAP || 'false',
  ]

  if (platform === 'android') {
    args.push('--android.packagename', process.env.HBUILDERX_ANDROID_PACKAGE_NAME || androidConfig.packageName || 'com.shian.xuanctai')
    args.push('--android.androidpacktype', process.env.HBUILDERX_ANDROID_PACK_TYPE || '3')
    if (process.env.HBUILDERX_ANDROID_CHANNELS) {
      args.push('--android.channels', process.env.HBUILDERX_ANDROID_CHANNELS)
    }
    if (process.env.HBUILDERX_ANDROID_CERT_ALIAS) {
      args.push('--android.certalias', process.env.HBUILDERX_ANDROID_CERT_ALIAS)
    }
    if (process.env.HBUILDERX_ANDROID_CERT_FILE) {
      args.push('--android.certfile', process.env.HBUILDERX_ANDROID_CERT_FILE)
    }
    if (process.env.HBUILDERX_ANDROID_CERT_PASSWORD) {
      args.push('--android.certpassword', process.env.HBUILDERX_ANDROID_CERT_PASSWORD)
    }
    if (process.env.HBUILDERX_ANDROID_STORE_PASSWORD) {
      args.push('--android.storepassword', process.env.HBUILDERX_ANDROID_STORE_PASSWORD)
    }
  }

  if (platform === 'ios') {
    args.push('--ios.bundle', process.env.HBUILDERX_IOS_BUNDLE_ID || iosConfig.bundleId || 'com.shian.xuanctai')
    args.push('--ios.supporteddevice', process.env.HBUILDERX_IOS_SUPPORTED_DEVICE || 'iPhone,iPad')
    args.push('--ios.isprisonbreak', process.env.HBUILDERX_IOS_IS_PRISONBREAK || 'false')
    if (process.env.HBUILDERX_IOS_CHANNELS) {
      args.push('--ios.channels', process.env.HBUILDERX_IOS_CHANNELS)
    }
    if (process.env.HBUILDERX_IOS_PROFILE) {
      args.push('--ios.profile', process.env.HBUILDERX_IOS_PROFILE)
    }
    if (process.env.HBUILDERX_IOS_CERT_FILE) {
      args.push('--ios.certfile', process.env.HBUILDERX_IOS_CERT_FILE)
    }
    if (process.env.HBUILDERX_IOS_CERT_PASSWORD) {
      args.push('--ios.certpassword', process.env.HBUILDERX_IOS_CERT_PASSWORD)
    }
  }

  return args
}

function stripHtml(value) {
  return String(value || '')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/li>/gi, '\n')
    .replace(/<[^>]+>/g, '')
    .replace(/&quot;/g, '"')
    .replace(/&amp;/g, '&')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function classifyOutput(output, exitCode) {
  const plain = stripHtml(output)
  const blockers = []
  const warnings = []

  const addBlocker = (id, owner, text) => {
    if (!blockers.some((item) => item.id === id)) blockers.push({ id, owner, text })
  }
  const addWarning = (id, text) => {
    if (!warnings.some((item) => item.id === id)) warnings.push({ id, text })
  }

  if (!execute) addWarning('dry-run', '未执行云打包；设置 HBUILDERX_CLOUD_PACK_EXECUTE=1 或传 --execute 才会调用 HBuilderX pack。')
  if (!existsSync(cliPath)) addBlocker('hbuilderx-cli-missing', 'environment-action', `HBuilderX CLI 不存在：${cliPath}`)
  if (exitCode !== 0 && execute) addBlocker('cli-exit-code', 'environment-action', `HBuilderX CLI exitCode=${exitCode}`)
  if (plain.includes('需重新验证手机号')) addBlocker('dcloud-phone-verification', 'user-last', 'DCloud 账号或应用所有者账号需要重新验证手机号。')
  if (plain.includes('公共测试证书存在安全隐患')) addBlocker('android-public-cert-disabled', 'user-last', 'Android 公共测试证书不再支持新应用，需要使用云端证书或自有证书。')
  if (plain.includes('高于云端最新打包SDK')) addBlocker('dcloud-sdk-version-lag', 'environment-action', '当前 uni-app CLI alpha 版本高于 DCloud 云端最新打包 SDK，需要降级到云端支持版本或等云端 SDK 更新。')
  if (plain.includes('云端证书') && plain.includes('[Error]')) addBlocker('cloud-certificate-required', 'user-last', '云打包需要在 DCloud 开发者中心配置云端证书或提供安全签名材料。')
  if (plain.includes('Apple') && plain.includes('证书')) addBlocker('apple-signing-required', 'user-last', 'iOS 云打包需要 Apple 证书、profile 和签名材料。')
  if (plain.includes('profile文件不能为空') || plain.includes('profile 文件不能为空')) addBlocker('ios-profile-required', 'user-last', 'iOS 云打包需要 provisioning profile 文件。')
  if (plain.includes('certfile文件不能为空') || plain.includes('certfile 文件不能为空')) addBlocker('ios-cert-required', 'user-last', 'iOS 云打包需要 p12 证书文件。')
  if (plain.includes('不能为空') && platform === 'ios') addBlocker('ios-signing-material-required', 'user-last', 'iOS 云打包签名材料不完整。')
  if (plain.includes('AppID') || plain.includes('appid')) addWarning('dcloud-appid-check', 'DCloud AppID/包名信息需要在开发者中心保持一致。')
  if (plain.includes('包名') && plain.includes('尚未在开发者中心录入')) addWarning('android-package-not-registered', 'Android 包名尚未在 DCloud 开发者中心录入。')
  if (plain.includes('隐私') || plain.includes('个人信息')) addWarning('android-privacy-config', 'Android 上架前需要补齐隐私合规配置。')
  if (plain.includes('x86')) addWarning('android-x86-abi', '当前 App 未勾选 x86 CPU 支持，模拟器兼容性可能不足。')
  if (/\[Error\]/i.test(plain) && blockers.length === 0) addBlocker('hbuilderx-pack-error', 'environment-action', 'HBuilderX 云打包返回错误，查看 output.redacted.log。')

  return { plain, blockers, warnings }
}

function main() {
  mkdirSync(outDir, { recursive: true })
  const args = buildPackArgs()
  const startedAt = new Date().toISOString()
  let result = { status: null, signal: null, stdout: '', stderr: '', error: null }

  if (execute && existsSync(cliPath)) {
    const spawned = spawnSync(cliPath, args, {
      cwd: root,
      env: {
        ...process.env,
        LC_ALL: 'en_US.UTF-8',
        LANG: 'en_US.UTF-8',
      },
      encoding: 'utf8',
      timeout: timeoutMs,
    })
    result = {
      status: spawned.status,
      signal: spawned.signal,
      stdout: spawned.stdout || '',
      stderr: spawned.stderr || '',
      error: spawned.error ? spawned.error.message : null,
    }
  }

  const finishedAt = new Date().toISOString()
  const combinedOutput = redact(`${result.stdout || ''}\n${result.stderr || ''}`)
  const classification = classifyOutput(combinedOutput, result.status)
  const passed = execute && result.status === 0 && classification.blockers.length === 0
  const attempt = {
    generatedAt: finishedAt,
    startedAt,
    finishedAt,
    version,
    platform,
    execute,
    passed,
    cliPath,
    cwd: root,
    timeoutMs,
    command: [cliPath, ...redactedArgs(args)],
    exitCode: result.status,
    signal: result.signal,
    error: result.error,
    outputPath: rel(join(outDir, 'output.redacted.log')),
    blockers: classification.blockers,
    warnings: classification.warnings,
    next: [
      '先处理 owner=user-last 的账号、手机号、开发者中心、证书动作。',
      '再处理 owner=environment-action 的 SDK/Xcode/DevEco/本机环境动作。',
      '云打包成功后，把 APK/AAB/IPA 或构建号记录放入 artifacts/release-inbox/v1.0.0/<platform>/ 并补 build-metadata.json。',
      '证书、签名口令、p12、mobileprovision、keystore 不进入 GitHub。',
    ],
  }

  writeFileSync(join(outDir, 'attempt.json'), `${JSON.stringify(attempt, null, 2)}\n`)
  writeFileSync(join(outDir, 'output.redacted.log'), `${combinedOutput}\n`)
  writeFileSync(join(outDir, 'README.md'), `${[
    `# HBuilderX 云打包尝试 - ${platform}`,
    '',
    `> 生成时间：${attempt.generatedAt}`,
    `> 执行：${execute ? '是' : '否，dry-run'}`,
    `> 结论：${passed ? '通过' : '未通过'}`,
    '',
    '## 命令',
    '',
    `\`${attempt.command.join(' ')}\``,
    '',
    '## 阻塞',
    '',
    ...(attempt.blockers.length ? attempt.blockers.map((item) => `- ${item.id} / ${item.owner}：${item.text}`) : ['- 暂无阻塞。']),
    '',
    '## 警告',
    '',
    ...(attempt.warnings.length ? attempt.warnings.map((item) => `- ${item.id}：${item.text}`) : ['- 暂无警告。']),
    '',
    '## 下一步',
    '',
    ...attempt.next.map((item) => `- ${item}`),
    '',
  ].join('\n')}\n`)

  console.log(JSON.stringify({
    outDir: rel(outDir),
    platform,
    execute,
    passed,
    exitCode: result.status,
    blockers: attempt.blockers,
    warnings: attempt.warnings,
  }, null, 2))

  if (strict && !passed) process.exit(1)
}

main()
