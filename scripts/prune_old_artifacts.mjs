import { existsSync, mkdirSync, readdirSync, rmSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const artifactsRoot = join(root, 'artifacts')
const apply = process.argv.includes('--apply')
const keepArg = process.argv.find((arg) => arg.startsWith('--keep='))
const keep = Math.max(1, Number(keepArg?.split('=')[1] || process.env.ARTIFACT_PRUNE_KEEP || 3))

const managedDirs = [
  'desktop-downloads',
  'desktop-macos-user-packets',
  'desktop-windows-user-packets',
  'desktop-dmg-backups',
  'desktop-macos-dmg-from-app',
  'desktop-macos-updated-app',
  'desktop-asar-backups',
  'desktop-macos-refresh-app-asar',
  'desktop-smoke',
  'desktop-online-login-smoke',
  'user-acceptance',
  'scroll-recordings',
  'store-screenshots',
  'agent-flash-frames',
  'topnav-agent-fixed-online-frames',
  'topnav-agent-fixed-frames-final',
  'agent-entry',
  'qa',
  'mobile-app-resource-packets',
  'mobile-api-evidence',
  'platform-backend-matrix',
  'final-package-plan',
  'final-package-preflight',
  'final-package-completeness',
  'current-index',
  'release-finalize',
  'package-binary-cleanup',
  'release-packages',
  'release-readiness',
  'release-manifests',
  'release-user-actions',
  'try-now',
  'desktop-macos-install',
  'desktop-macos-local-install',
  'desktop-macos-lifecycle',
  'desktop-windows-rebuild',
]

function localTimestamp() {
  const now = new Date()
  const pad = (value) => String(value).padStart(2, '0')
  return [
    now.getFullYear(),
    pad(now.getMonth() + 1),
    pad(now.getDate()),
    'T',
    pad(now.getHours()),
    '-',
    pad(now.getMinutes()),
    '-',
    pad(now.getSeconds()),
  ].join('')
}

function dirSize(path) {
  let total = 0
  const stack = [path]
  while (stack.length) {
    const current = stack.pop()
    let stat
    try {
      stat = statSync(current)
    } catch {
      continue
    }
    total += stat.size
    if (!stat.isDirectory()) continue
    let entries = []
    try {
      entries = readdirSync(current, { withFileTypes: true })
    } catch {
      continue
    }
    for (const entry of entries) stack.push(join(current, entry.name))
  }
  return total
}

function childrenByMtime(path) {
  if (!existsSync(path)) return []
  return readdirSync(path, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => {
      const fullPath = join(path, entry.name)
      const stat = statSync(fullPath)
      return {
        name: entry.name,
        path: fullPath,
        mtimeMs: stat.mtimeMs,
        bytes: dirSize(fullPath),
      }
    })
    .sort((a, b) => b.mtimeMs - a.mtimeMs)
}

const pruneItems = []
const preserved = []

for (const dir of managedDirs) {
  const fullPath = join(artifactsRoot, dir)
  const children = childrenByMtime(fullPath)
  preserved.push(...children.slice(0, keep).map((item) => ({ group: dir, path: relative(root, item.path), bytes: item.bytes })))
  pruneItems.push(...children.slice(keep).map((item) => ({ group: dir, path: item.path, bytes: item.bytes })))
}

let freedBytes = 0
const deleted = []
for (const item of pruneItems) {
  freedBytes += item.bytes
  if (!apply) continue
  rmSync(item.path, { recursive: true, force: true })
  deleted.push({ group: item.group, path: relative(root, item.path), bytes: item.bytes })
}

const outDir = join(artifactsRoot, 'artifact-prune', localTimestamp())
mkdirSync(outDir, { recursive: true })
const report = {
  generatedAt: new Date().toISOString(),
  mode: apply ? 'apply' : 'dry-run',
  keep,
  managedDirs,
  candidates: pruneItems.map((item) => ({ group: item.group, path: relative(root, item.path), bytes: item.bytes })),
  deleted,
  preserved,
  candidateCount: pruneItems.length,
  deletedCount: deleted.length,
  estimatedFreedBytes: freedBytes,
  estimatedFreedMB: Math.round((freedBytes / 1024 / 1024) * 10) / 10,
}

writeFileSync(join(outDir, 'report.json'), JSON.stringify(report, null, 2))
writeFileSync(
  join(outDir, 'README.md'),
  [
    '# Artifact Prune Report',
    '',
    `- Mode: ${report.mode}`,
    `- Keep per managed directory: ${keep}`,
    `- Candidate directories: ${report.candidateCount}`,
    `- Deleted directories: ${report.deletedCount}`,
    `- Estimated freed: ${report.estimatedFreedMB} MB`,
    '',
    '## Deleted',
    '',
    ...(deleted.length ? deleted.map((item) => `- \`${item.path}\` (${Math.round(item.bytes / 1024 / 1024)} MB)`) : ['- Dry-run only; no files deleted.']),
    '',
    '## Candidates',
    '',
    ...report.candidates.slice(0, 200).map((item) => `- \`${item.path}\` (${Math.round(item.bytes / 1024 / 1024)} MB)`),
  ].join('\n'),
)

console.log(JSON.stringify({ outDir: relative(root, outDir), ...report }, null, 2))
