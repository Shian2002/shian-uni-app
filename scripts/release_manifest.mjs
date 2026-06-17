import { createHash } from 'node:crypto'
import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const outDir = process.env.RELEASE_MANIFEST_DIR || join(root, 'artifacts', 'release-manifests')
const outFile = process.env.RELEASE_MANIFEST_OUT || join(outDir, `${localTimestamp()}-current-worktree.json`)
const artifactDirs = [
  'dist/build/h5',
  'dist/build/app',
  'dist/build/app-plus',
  'desktop/release'
]

function localTimestamp(date = new Date()) {
  const offsetMs = date.getTimezoneOffset() * 60 * 1000
  return new Date(date.getTime() - offsetMs).toISOString().replace('Z', '').replace(/[:.]/g, '-')
}

function sha256(path) {
  return createHash('sha256').update(readFileSync(path)).digest('hex')
}

function walk(dir) {
  if (!existsSync(dir)) return []
  const entries = []
  for (const name of readdirSync(dir)) {
    const path = join(dir, name)
    const stat = statSync(path)
    if (stat.isDirectory()) {
      entries.push(...walk(path))
    } else {
      entries.push({ path, stat })
    }
  }
  return entries
}

const artifacts = []
for (const dir of artifactDirs) {
  for (const entry of walk(join(root, dir))) {
    const rel = relative(root, entry.path)
    if (entry.stat.size === 0) continue
    artifacts.push({
      path: rel,
      bytes: entry.stat.size,
      sha256: sha256(entry.path)
    })
  }
}

const manifest = {
  generatedAt: new Date().toISOString(),
  artifactCount: artifacts.length,
  artifacts
}

mkdirSync(outDir, { recursive: true })
writeFileSync(outFile, `${JSON.stringify(manifest, null, 2)}\n`)
console.error(`release manifest written: ${relative(root, outFile).replaceAll('\\', '/')}`)
console.log(JSON.stringify(manifest, null, 2))
