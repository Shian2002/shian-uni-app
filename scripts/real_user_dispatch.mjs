#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'
import { execFileSync } from 'node:child_process'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = process.env.REAL_USER_VERSION || process.env.RELEASE_VERSION || `v${packageJson.version || '0.0.0'}`
const strict = process.argv.includes('--strict') || process.env.REAL_USER_DISPATCH_STRICT === '1'
const defaultOutRoot = 'artifacts/real-user-dispatch'
const outDir = process.env.REAL_USER_DISPATCH_DIR || join(root, defaultOutRoot, `${localTimestamp()}-${version}`)

const platforms = [
  { id: 'h5', name: 'H5', requiredArtifact: '线上或 staging URL', packageRequired: false },
  { id: 'android', name: 'Android', requiredArtifact: 'APK/AAB', packageRequired: true },
  { id: 'ios', name: 'iOS', requiredArtifact: 'TestFlight 构建号或 IPA 记录', packageRequired: true },
  { id: 'harmony', name: '鸿蒙', requiredArtifact: 'HAP/AppGallery 包', packageRequired: true },
  { id: 'macos', name: 'macOS', requiredArtifact: 'DMG/ZIP', packageRequired: true },
  { id: 'windows', name: 'Windows', requiredArtifact: 'EXE/MSI/NSIS', packageRequired: true },
]
const releaseScope = readJson('configs/release/current-release-scope.json') || {}
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

function latestDir(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => b.name.localeCompare(a.name))
  return dirs[0] ? join(path, dirs[0].name) : ''
}

function latestReport(path, filename = 'report.json') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory() && existsSync(join(root, item.reportPath)))
    .sort((a, b) => {
      const aData = readJson(a.reportPath) || {}
      const bData = readJson(b.reportPath) || {}
      const byReportTime = Date.parse(bData.generatedAt || bData.generated_at || '') - Date.parse(aData.generatedAt || aData.generated_at || '')
      return (Number.isFinite(byReportTime) ? byReportTime : 0) || b.name.localeCompare(a.name)
    })
  return dirs[0] ? { path: dirs[0].reportPath, data: readJson(dirs[0].reportPath) } : null
}

function git(args) {
  try {
    return execFileSync('git', args, { cwd: root, encoding: 'utf8' }).trim()
  } catch (_) {
    return ''
  }
}

function platformArtifact(platform, artifactIntake) {
  if (platform.id === 'h5') {
    return {
      ready: true,
      label: process.env.REAL_USER_H5_URL || '线上或 staging URL 待测试负责人填写',
      evidence: existsSync(join(root, 'dist/build/h5/index.html')) ? 'dist/build/h5/index.html' : '',
      missing: existsSync(join(root, 'dist/build/h5/index.html')) ? [] : ['缺少 H5 构建产物'],
    }
  }
  const status = artifactIntake?.data?.platforms?.[platform.id]
  const accepted = (artifactIntake?.data?.accepted || []).filter((item) => item.platform === platform.id)
  const binary = accepted.find((item) => item.kind === 'binary') || accepted[0]
  return {
    ready: status === 'ready',
    label: binary ? binary.path : '',
    evidence: artifactIntake?.path || '',
    missing: status === 'ready' ? [] : [`缺少 ${platform.requiredArtifact}`],
  }
}

function dispatchFor(platform, evidence) {
  const packetPath = evidence.realUserPacket ? `${evidence.realUserPacket}/${platform.id}/README.md` : ''
  const resultPath = evidence.realUserPacket ? `${evidence.realUserPacket}/${platform.id}/result.json` : ''
  const artifact = platformArtifact(platform, evidence.artifactIntake)
  const missing = []
  if (!evidence.realUserPacket) missing.push('缺少真实用户测试包')
  if (platform.packageRequired && !artifact.ready) missing.push(...artifact.missing)
  if (!evidence.storeMaterials?.data || evidence.storeMaterials.data.passed !== true) missing.push('商店材料检查未通过')
  if (!evidence.privacyDisclosure?.data || evidence.privacyDisclosure.data.passed !== true) missing.push('App Privacy / Data safety 披露未通过')
  if (!evidence.legalUrlCheck?.data || evidence.legalUrlCheck.data.passed !== true) missing.push('法律 URL 验证未通过')
  return {
    platform: platform.id,
    name: platform.name,
    status: missing.length ? 'not-ready' : 'ready-to-dispatch',
    packageOrUrl: artifact.label,
    packetReadme: packetPath,
    resultJson: resultPath,
    evidence: [
      artifact.evidence,
      packetPath,
      evidence.storeMaterials?.path,
      evidence.privacyDisclosure?.path,
      evidence.legalUrlCheck?.path,
    ].filter(Boolean),
    missing,
  }
}

function main() {
  mkdirSync(outDir, { recursive: true })
  const evidence = {
    artifactIntake: latestReport('artifacts/release-artifact-intake'),
    storeMaterials: latestReport('artifacts/store-materials'),
    privacyDisclosure: latestReport('artifacts/privacy-disclosures'),
    legalUrlCheck: latestReport('artifacts/legal-url-checks'),
    realUserPacket: latestDir('artifacts/real-user-packets'),
  }
  const dispatch = activePlatforms.map((platform) => dispatchFor(platform, evidence))
  const ready = dispatch.filter((item) => item.status === 'ready-to-dispatch').length
  const report = {
    generatedAt: new Date().toISOString(),
    version,
    strict,
    branch: git(['branch', '--show-current']) || '',
    commit: git(['rev-parse', 'HEAD']) || '',
    passed: ready === activePlatforms.length,
    releaseScope: {
      configPath: 'configs/release/current-release-scope.json',
      currentBatch: releaseScope.currentBatch || '',
      activePlatforms: activePlatforms.map((platform) => platform.id),
      deferredPlatforms: deferredPlatforms.map((platform) => platform.id),
    },
    summary: { ready, missing: activePlatforms.length - ready, deferred: deferredPlatforms.length },
    evidence: {
      artifactIntake: evidence.artifactIntake?.path || '',
      storeMaterials: evidence.storeMaterials?.path || '',
      privacyDisclosure: evidence.privacyDisclosure?.path || '',
      legalUrlCheck: evidence.legalUrlCheck?.path || '',
      realUserPacket: evidence.realUserPacket,
    },
    platforms: dispatch,
    outDir: rel(outDir),
  }
  writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)
  writeFileSync(join(outDir, 'README.md'), [
    `# ${version} 真实用户发测分发索引`,
    '',
    `> 生成时间：${report.generatedAt}`,
    `> commit：${report.commit || '未读取到'}`,
    `> 当前批次：${releaseScope.currentBatch || '未配置'}；延期平台：${deferredPlatforms.map((platform) => platform.name).join('、') || '无'}`,
    `> 结论：${report.passed ? '当前批次可发测' : '当前批次不可发测'}`,
    '',
    `汇总：READY ${report.summary.ready} / MISSING ${report.summary.missing} / DEFERRED ${report.summary.deferred}`,
    '',
    '## 平台分发状态',
    '',
    '| 平台 | 状态 | 包/URL | 测试单 | 缺口 |',
    '| --- | --- | --- | --- | --- |',
    ...dispatch.map((item) => `| ${item.name} | ${item.status} | ${item.packageOrUrl || '-'} | ${item.packetReadme ? `\`${item.packetReadme}\`` : '-'} | ${item.missing.length ? item.missing.join('<br>') : '-'} |`),
    ...(deferredPlatforms.length ? ['', '延期平台本轮不作为阻塞：', ...deferredPlatforms.map((platform) => `- \`${platform.id}\` ${platform.name}`)] : []),
    '',
    '## 证据',
    '',
    `- 发行产物收件：${report.evidence.artifactIntake ? `\`${report.evidence.artifactIntake}\`` : '缺失'}`,
    `- 真实用户测试包：${report.evidence.realUserPacket ? `\`${report.evidence.realUserPacket}\`` : '缺失'}`,
    `- 商店材料检查：${report.evidence.storeMaterials ? `\`${report.evidence.storeMaterials}\`` : '缺失'}`,
    `- 隐私披露检查：${report.evidence.privacyDisclosure ? `\`${report.evidence.privacyDisclosure}\`` : '缺失'}`,
    `- 法律 URL 验证：${report.evidence.legalUrlCheck ? `\`${report.evidence.legalUrlCheck}\`` : '缺失'}`,
    '',
    '## 使用规则',
    '',
    '- 本索引只判断是否可以把测试包发给真实测试人，不代表真实用户测试已通过。',
    '- 每个平台回收后仍必须补齐 `result.json`、8 张截图和全部 `passedFlows`。',
    '- 正式上架候选前必须运行 `npm run real-user:check -- --strict`。',
  ].join('\n') + '\n')

  console.log(JSON.stringify({ outDir: report.outDir, ready: report.summary.ready, missing: report.summary.missing }, null, 2))
  if (strict && !report.passed) {
    console.error('严格模式失败：仍有平台不可发测。')
    process.exit(1)
  }
}

main()
