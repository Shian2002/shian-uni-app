#!/usr/bin/env node

import { execFileSync } from 'node:child_process'
import { existsSync, mkdirSync, readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const packageJson = readJson('package.json') || {}
const version = `v${packageJson.version || '0.0.0'}`
const outDir = join(root, 'artifacts', 'low-impact-status', `${localTimestamp()}-${version}`)

const heavyProcessRules = [
  {
    id: 'hbuilderx-pack',
    label: 'HBuilderX 打包',
    pattern: /HBuilderX\.app\/Contents\/MacOS\/cli\s+pack\b|cli pack --project/,
  },
  {
    id: 'hbuilderx-plugin-install',
    label: 'HBuilderX 插件安装',
    pattern: /HBuilderX\.app\/Contents\/MacOS\/cli\s+installPlugin\b|installPlugin --name/,
  },
  {
    id: 'hbuilderx-runtime',
    label: 'HBuilderX 主程序或插件进程',
    pattern: /HBuilderX\.app\/Contents\/MacOS\/HBuilderX|plugin-manager\/out\.js|hbuilder\.fswatcher\/index\.js|tsserver\.js.*HBuilderX|indexservice\/out\/server/,
  },
  {
    id: 'xcode-download',
    label: 'Xcode/xcodes 下载或安装',
    pattern: /brew install xcodes|xcodes install|playwright install chromium|Xcode.*download/,
  },
  {
    id: 'uni-app-build',
    label: 'uni-app App 构建',
    pattern: /uni\.js build -p app|uni build -p app|npm run build:app/,
  },
  {
    id: 'desktop-build',
    label: '桌面端 Electron 打包',
    pattern: /electron-builder|npm --prefix desktop run dist|npm run desktop:build/,
  },
  {
    id: 'android-build',
    label: 'Android/Gradle 构建',
    pattern: /\bgradle\b|GradleDaemon|sdkmanager --install/,
  },
  {
    id: 'preview-server',
    label: '本地 Vite 预览服务',
    pattern: /vite preview --port 3003|node .*preview-server\.js/,
  },
]

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

function run(command, args = []) {
  try {
    return {
      ok: true,
      command: [command, ...args].join(' '),
      output: execFileSync(command, args, { cwd: root, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'] }).trim(),
    }
  } catch (error) {
    return {
      ok: false,
      command: [command, ...args].join(' '),
      output: String(error.stdout || error.stderr || error.message).trim(),
    }
  }
}

function parsePs(output) {
  return output
    .split('\n')
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      const match = line.match(/^(\d+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+(.+)$/)
      if (!match) return null
      return {
        pid: Number(match[1]),
        ppid: Number(match[2]),
        cpu: Number(match[3]),
        mem: Number(match[4]),
        command: match[5],
      }
    })
    .filter(Boolean)
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
  }
}

function latestDir(parent, requiredFile) {
  const fullParent = join(root, parent)
  if (!existsSync(fullParent)) return ''
  const dirs = readdirSync(fullParent, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => {
      const fullPath = join(fullParent, entry.name)
      return { name: entry.name, fullPath, mtimeMs: statSync(fullPath).mtimeMs }
    })
    .filter((entry) => !requiredFile || existsSync(join(entry.fullPath, requiredFile)))
    .sort((a, b) => b.mtimeMs - a.mtimeMs || b.name.localeCompare(a.name))
  return dirs[0] ? `${parent}/${dirs[0].name}` : ''
}

function matchHeavyProcesses(processes) {
  const selfPid = process.pid
  return processes
    .flatMap((processInfo) => heavyProcessRules
      .filter((rule) => processInfo.pid !== selfPid && rule.pattern.test(processInfo.command))
      .map((rule) => ({
        ruleId: rule.id,
        label: rule.label,
        pid: processInfo.pid,
        ppid: processInfo.ppid,
        cpu: processInfo.cpu,
        mem: processInfo.mem,
        command: processInfo.command,
      })))
    .sort((a, b) => b.cpu - a.cpu || a.label.localeCompare(b.label))
}

const psResult = run('ps', ['-axo', 'pid=,ppid=,%cpu=,%mem=,command='])
const processes = psResult.ok ? parsePs(psResult.output) : []
const heavyProcesses = matchHeavyProcesses(processes)
const disk = diskInfo(root)
const currentDownloads = readJson('artifacts/current-downloads/manifest.json')
const currentIndexLatest = readJson('artifacts/current-index-latest.json')
const latestPackAttempt = latestDir('artifacts/hbuilderx-cloud-pack-attempts', 'attempt.json')
const latestPluginInstall = latestDir('artifacts/hbuilderx-plugin-installs', '')

const report = {
  generatedAt: new Date().toISOString(),
  version,
  mode: heavyProcesses.length ? 'pause-heavy-work' : 'video-safe',
  videoSafe: heavyProcesses.length === 0,
  note: '看视频期间使用：只检查本机进程、磁盘和已有发行索引，不构建、不打包、不下载、不启动预览。',
  disk,
  heavyProcesses,
  currentDownloads: {
    passed: currentDownloads?.passed === true,
    path: 'artifacts/current-downloads',
    files: (currentDownloads?.files || []).map((file) => ({
      label: file.label,
      path: file.path,
      sha256: file.sha256,
    })),
  },
  evidence: {
    currentIndex: currentIndexLatest?.path || '',
    latestHBuilderXPackAttempt: latestPackAttempt,
    latestHBuilderXPluginInstall: latestPluginInstall,
  },
  safeDuringVideo: [
    'npm run release:low-impact-status',
    'npm run release:quota-status',
    'npm run release:external-handoff',
    '阅读/编辑 docs、configs、脚本和测试。',
  ],
  deferUntilVideoEnds: [
    'npm run build:app',
    'npm run mobile:hbuilderx-resources',
    'HBuilderX cli pack / installPlugin',
    'brew install xcodes / xcodes install',
    'npx playwright install chromium',
    'npm run desktop:build:*',
    'npm run store:screenshots',
    '长链路 qa / Playwright / 真机安装回归。',
  ],
}

mkdirSync(outDir, { recursive: true })
writeFileSync(join(outDir, 'report.json'), `${JSON.stringify(report, null, 2)}\n`)

const lines = [
  '# 低影响工作状态',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${report.videoSafe ? '当前没有发行重负载进程残留，可以继续低影响整理。' : '检测到发行重负载进程，先暂停构建/下载/打包。'}`,
  `> 剩余空间：${report.disk.availableGiB || 0} GiB`,
  '',
  '## 检测到的发行重负载进程',
  '',
  ...(report.heavyProcesses.length
    ? report.heavyProcesses.map((item) => `- ${item.label} PID ${item.pid} CPU ${item.cpu}%：\`${item.command}\``)
    : ['- 无。']),
  '',
  '## 当前稳定下载入口',
  '',
  `- 目录：\`${report.currentDownloads.path}\``,
  `- 状态：${report.currentDownloads.passed ? '通过' : '缺失或未通过'}`,
  ...report.currentDownloads.files.map((file) => `- ${file.label}：\`${file.path}\` SHA-256 \`${file.sha256}\``),
  '',
  '## 看视频期间允许',
  '',
  ...report.safeDuringVideo.map((item) => `- ${item}`),
  '',
  '## 看视频结束后再做',
  '',
  ...report.deferUntilVideoEnds.map((item) => `- ${item}`),
]
writeFileSync(join(outDir, 'README.md'), `${lines.join('\n')}\n`)

console.log(JSON.stringify({
  outDir: rel(outDir),
  videoSafe: report.videoSafe,
  heavyProcesses: report.heavyProcesses.length,
  availableGiB: report.disk.availableGiB,
  currentDownloadsPassed: report.currentDownloads.passed,
}, null, 2))
