import { createHash } from 'node:crypto'
import { copyFileSync, existsSync, linkSync, mkdirSync, readFileSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { basename, join, relative } from 'node:path'

const root = process.cwd()
const outDir = join(root, 'artifacts', 'current-downloads')
const latestIndexPointer = readJson('artifacts/current-index-latest.json')
const currentIndexPath = latestIndexPointer?.path ? `${latestIndexPointer.path}/index.json` : ''
const currentIndex = currentIndexPath ? readJson(currentIndexPath) : null
const issues = []

function readJson(path) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  try {
    return JSON.parse(readFileSync(fullPath, 'utf8'))
  } catch (_) {
    return null
  }
}

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function placeFile(sourceRel, targetName) {
  if (!sourceRel) return null
  const source = join(root, sourceRel)
  const target = join(outDir, targetName)
  if (!existsSync(source)) {
    issues.push(`源文件缺失: ${sourceRel}`)
    return null
  }
  const samePath = source === target
  if (existsSync(target) && !samePath) rmSync(target)
  let mode = 'hardlink'
  if (samePath) {
    mode = 'existing'
  } else {
    try {
      linkSync(source, target)
    } catch (_) {
      copyFileSync(source, target)
      mode = 'copy'
    }
  }
  const stat = statSync(target)
  return {
    label: targetName,
    source: sourceRel,
    path: rel(target),
    sourceFileName: basename(sourceRel),
    bytes: stat.size,
    sha256: sha256(target),
    mode,
  }
}

mkdirSync(outDir, { recursive: true })

if (!currentIndex) {
  issues.push(`缺少当前索引: ${currentIndexPath || 'artifacts/current-index-latest.json'}`)
}
const propagatedIndexIssues = (currentIndex?.issues || [])
  .filter((issue) => issue !== '当前稳定下载入口未通过或缺失')
if (propagatedIndexIssues.length) {
  issues.push(...propagatedIndexIssues.map((issue) => `当前索引问题: ${issue}`))
}

const usable = currentIndex?.usable || {}
const files = [
  placeFile(usable.macosDmg?.path, 'shian-current-macos-arm64.dmg'),
  placeFile(usable.macosAppZip?.path, 'shian-current-macos-arm64.app.zip'),
  placeFile(usable.windowsInstaller?.path, 'shian-current-windows-x64.exe'),
  placeFile(usable.androidDebugApk?.path, 'shian-current-android-debug.apk'),
  placeFile(usable.androidDebugAab?.path, 'shian-current-android-debug.aab'),
  placeFile(usable.mobileStoreIcon?.path, 'shian-current-app-icon-1024.png'),
].filter(Boolean)

for (const label of [
  'shian-current-macos-arm64.dmg',
  'shian-current-macos-arm64.app.zip',
  'shian-current-windows-x64.exe',
  'shian-current-android-debug.apk',
  'shian-current-android-debug.aab',
  'shian-current-app-icon-1024.png',
]) {
  if (!files.some((item) => item.label === label)) issues.push(`固定下载文件缺失: ${label}`)
}

for (const item of files) {
  const expected = usable[{
    'shian-current-macos-arm64.dmg': 'macosDmg',
    'shian-current-macos-arm64.app.zip': 'macosAppZip',
    'shian-current-windows-x64.exe': 'windowsInstaller',
    'shian-current-android-debug.apk': 'androidDebugApk',
    'shian-current-android-debug.aab': 'androidDebugAab',
    'shian-current-app-icon-1024.png': 'mobileStoreIcon',
  }[item.label]]?.sha256
  if (expected && expected !== item.sha256) issues.push(`${item.label} SHA-256 与当前索引不一致`)
}

const manifest = {
  generatedAt: new Date().toISOString(),
  passed: issues.length === 0 && files.length >= 5,
  currentIndex: currentIndexPath,
  currentIndexGeneratedAt: currentIndex?.generatedAt || '',
  files,
  evidenceSummary: currentIndex?.evidenceSummary || null,
  freshness: currentIndex?.freshness || null,
  userMustDoLast: currentIndex?.userMustDoLast || [],
  remainingHardBlocks: currentIndex?.remainingHardBlocks || [],
  issues,
}

writeFileSync(join(outDir, 'manifest.json'), `${JSON.stringify(manifest, null, 2)}\n`)
writeFileSync(join(outDir, 'checksums.sha256'), `${files.map((item) => `${item.sha256}  ${item.label}`).join('\n')}\n`)
writeFileSync(join(outDir, 'README.md'), `${[
  '# 当前稳定下载入口',
  '',
  `> 生成时间：${manifest.generatedAt}`,
  `> 结论：${manifest.passed ? '通过' : '未通过'}`,
  `> 当前索引：\`${currentIndexPath || '缺失'}\``,
  '',
  '## 文件',
  '',
  '| 文件 | 来源 | Bytes | SHA-256 | 放置方式 |',
  '| --- | --- | ---: | --- | --- |',
  ...files.map((item) => `| \`${item.path}\` | \`${item.source}\` | ${item.bytes} | \`${item.sha256}\` | ${item.mode} |`),
  '',
  '## 证据摘要',
  '',
  `- macOS 原生窗口：${manifest.evidenceSummary?.desktopNative?.passed ? '通过' : '缺失'}；顶栏颜色 \`${manifest.evidenceSummary?.desktopNative?.topbarColor || '-'}\`。`,
  `- 线上后端：${manifest.evidenceSummary?.backendContract?.passed ? '通过' : '缺失'}；目标 \`${manifest.evidenceSummary?.backendContract?.apiTarget || '-'}\`。`,
  `- 积分/会员：${manifest.evidenceSummary?.backendContract?.membership?.schemaReady ? '结构通过' : '缺失'}；points \`${manifest.evidenceSummary?.backendContract?.membership?.points ?? '-'}\`。`,
  `- 时安 agent：${manifest.evidenceSummary?.backendContract?.guide?.schemaReady ? '结构通过' : '缺失'}；推荐 \`${(manifest.evidenceSummary?.backendContract?.recommendTools?.toolModels || []).join(',') || '-'}\`。`,
  `- 移动端后端请求能力：${manifest.evidenceSummary?.mobileRuntime?.passed ? '通过' : '缺失'}。`,
  `- Windows 新鲜度：${manifest.freshness?.windows?.fresh ? '通过' : manifest.freshness?.windows?.issue || '缺失'}。`,
  '',
  '## 仍需最后人工处理',
  '',
  ...(manifest.userMustDoLast.length ? manifest.userMustDoLast.map((item) => `- ${item}`) : ['- 无。']),
  '',
  '## 问题',
  '',
  ...(issues.length ? issues.map((item) => `- ${item}`) : ['- 无。']),
].join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  passed: manifest.passed,
  files: files.map((item) => ({ label: item.label, path: item.path, mode: item.mode, sha256: item.sha256 })),
  issues,
}, null, 2))

if (!manifest.passed) process.exit(1)
