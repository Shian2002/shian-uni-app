#!/usr/bin/env node

import { existsSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from 'node:fs'
import { join, relative } from 'node:path'

const root = process.cwd()
const strict = process.argv.includes('--strict') || process.env.PRODUCT_LAUNCH_AUDIT_STRICT === '1'
const stamp = new Date().toISOString().replace(/[:.]/g, '-')
const outDir = process.env.PRODUCT_LAUNCH_AUDIT_OUT_DIR || join(root, 'artifacts', 'product-launch-audits')
const jsonOut = join(outDir, `${stamp}.json`)
const mdOut = join(outDir, `${stamp}.md`)

function rel(path) {
  return relative(root, path).replaceAll('\\', '/')
}

function exists(path) {
  return existsSync(join(root, path))
}

function readText(path) {
  const fullPath = join(root, path)
  return existsSync(fullPath) ? readFileSync(fullPath, 'utf8') : ''
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

function latestFile(path, suffix) {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return ''
  const files = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name) }))
    .filter((item) => statSync(item.full).isFile() && item.name.endsWith(suffix))
    .sort((a, b) => b.name.localeCompare(a.name))
  return files[0] ? join(path, files[0].name) : ''
}

function latestPassingReport(path, filename = 'report.json') {
  const fullPath = join(root, path)
  if (!existsSync(fullPath)) return null
  const dirs = readdirSync(fullPath)
    .map((name) => ({ name, full: join(fullPath, name), reportPath: join(path, name, filename) }))
    .filter((item) => statSync(item.full).isDirectory())
    .sort((a, b) => {
      const byReportTime = reportTime(b.reportPath) - reportTime(a.reportPath)
      return byReportTime || b.name.localeCompare(a.name)
    })
  for (const dir of dirs) {
    const reportPath = dir.reportPath
    const report = readJson(reportPath)
    if (report?.passed === true) return { path: reportPath, data: report }
  }
  return null
}

function reportTime(path) {
  const data = readJson(path)
  const raw = data?.generatedAt || data?.generated_at || ''
  const time = raw ? Date.parse(raw) : 0
  return Number.isFinite(time) ? time : 0
}

function latestJson(path) {
  const latest = latestFile(path, '.json')
  return latest ? { path: latest, data: readJson(latest) } : null
}

function checkText(id, title, text, required, evidencePath, next = []) {
  const missing = required.filter((snippet) => !text.includes(snippet))
  return {
    id,
    title,
    status: missing.length === 0 ? 'ready' : text ? 'partial' : 'missing',
    evidence: text ? [evidencePath] : [],
    missing,
    next,
  }
}

function checkEvidence(id, title, condition, evidence = [], missing = [], next = []) {
  return {
    id,
    title,
    status: condition ? 'ready' : evidence.length ? 'partial' : 'missing',
    evidence: evidence.filter(Boolean),
    missing: condition ? [] : missing.filter(Boolean),
    next,
  }
}

const productDocPath = 'docs/release/product-gtm-benchmark.md'
const strategySkillPath = 'docs/release/product-strategy-skill-report.md'
const contentAcceptancePath = 'docs/release/product-content-acceptance.md'
const storyboardPath = 'docs/release/store-screenshot-storyboard.md'
const realUserPath = 'docs/release/real-user-acceptance.md'
const productDoc = readText(productDocPath)
const strategySkillDoc = readText(strategySkillPath)
const contentAcceptanceDoc = readText(contentAcceptancePath)
const storyboardDoc = readText(storyboardPath)
const realUserDoc = readText(realUserPath)
const storeScreenshots = latestPassingReport('artifacts/store-screenshots', 'summary.json')
const loginSmoke = latestPassingReport('artifacts/login-smoke')
const agentEntry = latestPassingReport('artifacts/agent-entry')
const auditAccount = latestPassingReport('artifacts/audit-account')
const userAcceptance = latestPassingReport('artifacts/user-acceptance')
const realUserResult = latestJson('artifacts/real-user-results')
const realUserPacket = latestDir('artifacts/real-user-packets')
const latestReadiness = latestFile('artifacts/release-readiness', '.md')
const latestUserActions = latestDir('artifacts/release-user-actions')
const latestUserActionsReport = latestUserActions ? readJson(`${latestUserActions}/report.json`) : null

const contentBlocks = [
  '首页首屏',
  'Critical Moment',
  'Product 推理区',
  '时安 agent',
  '积分会员页',
  '历史记录',
  '工具页',
  '个人中心',
]

const checks = [
  checkText(
    'strategy.positioning',
    '产品定位与对标判断',
    productDoc,
    ['Tianfu Agent', 'The Metaphysics Agent', '时安agent', '工作台感', '产品入口和账号入口必须分层'],
    productDocPath,
    ['继续补 Tianfu 登录态深层截图：命主、历史、付费页、报告承接。']
  ),
  checkText(
    'strategy.monetization',
    '变现与定价链路',
    productDoc,
    ['免费额度', '积分包', '正式报告 SKU', '订阅会员', '短期问题', '复杂长期问题'],
    productDocPath,
    ['上线前准备积分充足审核账号，避免审核员卡在首次 Agent 消耗。']
  ),
  checkText(
    'strategy.gtm',
    '营销链路与 90 天节奏',
    `${productDoc}\n${strategySkillDoc}`,
    ['营销链路建议', '90 天 GTM 执行路线', '事业', '感情', '决策', '年运'],
    `${productDocPath} / ${strategySkillPath}`,
    ['先用 4 类场景模板测试首页进入 Agent 点击率和首问完成率。']
  ),
  checkText(
    'strategy.skill-canvas',
    '产品 skill 策略画布与实验',
    strategySkillDoc,
    ['product-strategy', 'monetization-strategy', 'gtm-strategy', 'marketing-ideas', '产品策略画布', '北极星指标', '免费额度 + 积分包', '正式报告 SKU', '四类问题模板', '审核账号资产不足', '真实用户测试未回收'],
    strategySkillPath,
    ['每次产品定位、付费模式或营销链路调整后，同步更新产品 skill 报告。']
  ),
  checkText(
    'strategy.content-blocks',
    '每个内容板块的产品判断',
    `${productDoc}\n${strategySkillDoc}\n${contentAcceptanceDoc}`,
    [...contentBlocks, 'GTM 实验矩阵', '截图验收清单', '四类问题模板', '正式报告 SKU'],
    `${productDocPath} / ${contentAcceptancePath}`,
    ['每轮大改首页、积分、历史或工具页后，都更新内容板块矩阵和截图验收清单。']
  ),
  checkText(
    'screenshots.storyboard',
    '商店截图叙事与审核材料',
    storyboardDoc,
    ['问事 -> 登录/注册 -> Agent 工作台', '账号注销', '真实 Android、macOS、Windows 包', '时安agent'],
    storyboardPath,
    ['自动 H5 截图只能做候选，正式提交前必须真机重拍。']
  ),
  checkText(
    'real-users.packet',
    '真实用户验收方法',
    realUserDoc,
    ['real-user:packet', 'real-user:check', '测试包只是材料模板', 'referenceEvidence', 'READY=0 MISSING=4'],
    realUserPath,
    ['回收当前批次四个平台的 results/tester-*.json 和 8 张标准截图后，再跑严格模式；iOS/鸿蒙后续批次再补。']
  ),
  checkEvidence(
    'evidence.login-online',
    '本地复用线上登录证据',
    loginSmoke?.data?.passed === true && agentEntry?.data?.passed === true,
    [loginSmoke?.path, agentEntry?.path, userAcceptance?.path],
    [
      loginSmoke?.data?.passed !== true && '缺少通过的 qa:login:local-online 报告。',
      agentEntry?.data?.passed !== true && '缺少通过的 qa:agent:entry-online-login 入口验收报告。',
    ],
    ['登录通过不等于完整 Agent 消费通过；下一步需要积分充足账号。']
  ),
  checkEvidence(
    'evidence.audit-account',
    '审核账号资产预检',
    auditAccount?.data?.fullAgentReady === true,
    [auditAccount?.path],
    [
      auditAccount?.data?.entryReady !== true && '缺少可登录的审核账号预检。',
      auditAccount?.data?.entryReady === true && auditAccount?.data?.fullAgentReady !== true && '审核账号可登录，但积分/AI 次数不足以完成完整 Agent 审核演示。',
    ],
    ['准备积分充足审核账号，或在 staging 使用隔离积分策略。']
  ),
  checkEvidence(
    'evidence.store-screenshots',
    '商店截图候选证据',
    storeScreenshots?.data?.passed === true && (storeScreenshots?.data?.captures || []).some((item) => item.id === '06-profile-delete'),
    [storeScreenshots?.path],
    ['缺少通过的 store:screenshots 报告，或账号注销截图没有拍到注销区。'],
    ['当前批次正式上架前按 Android/桌面真机重拍；iOS/鸿蒙后续批次再补。']
  ),
  checkEvidence(
    'evidence.real-users',
    '真实用户回收状态',
    realUserResult?.data?.passed === true,
    [realUserPacket, realUserResult?.path],
    [
      realUserResult?.data?.passed !== true && '真实用户回收未通过。',
      realUserResult?.data?.summary && `当前 READY=${realUserResult.data.summary.ready} MISSING=${realUserResult.data.summary.missing}`,
    ],
    ['没有真实设备回收前，不能把任何平台标记为可上架候选。']
  ),
  checkEvidence(
    'evidence.release-summary',
    '发行 readiness 证据',
    Boolean(latestReadiness),
    [latestReadiness],
    ['缺少 release:readiness 输出。'],
    ['每次补新证据后串行重跑 readiness 和 summary，summary 负责引用最新产品审计。']
  ),
  checkEvidence(
    'evidence.user-actions',
    '人工事项交接包清零状态',
    latestUserActionsReport?.passed === true,
    [latestUserActions && `${latestUserActions}/report.json`, 'docs/release/user-action-handoff.md'],
    [
      !latestUserActions && '缺少 release:user-actions 输出。',
      latestUserActionsReport?.summary && `当前 USER=${latestUserActionsReport.summary.userRequired} APPROVAL=${latestUserActionsReport.summary.approvalRequired}`,
      latestUserActionsReport && latestUserActionsReport.passed !== true && '人工事项或需要明确确认的线上动作尚未清零。',
    ],
    ['正式产品上架候选前，release:user-actions 的 userRequired 和 approvalRequired 必须为 0。']
  ),
]

const ready = checks.filter((item) => item.status === 'ready').length
const partial = checks.filter((item) => item.status === 'partial').length
const missing = checks.filter((item) => item.status === 'missing').length
const passed = missing === 0 && checks.every((item) => !['evidence.real-users', 'evidence.user-actions'].includes(item.id) || item.status === 'ready')
const report = {
  generatedAt: new Date().toISOString(),
  strict,
  passed,
  summary: { ready, partial, missing },
  checks,
}

mkdirSync(outDir, { recursive: true })
writeFileSync(jsonOut, `${JSON.stringify(report, null, 2)}\n`)

const md = [
  '# 产品与上架链路审计报告',
  '',
  `> 生成时间：${report.generatedAt}`,
  `> 结论：${passed ? '通过' : '未完全通过'}`,
  `> 汇总：READY ${ready} / PARTIAL ${partial} / MISSING ${missing}`,
  '',
  '| 项目 | 状态 | 证据 | 缺口 | 下一步 |',
  '| --- | --- | --- | --- | --- |',
  ...checks.map((item) => {
    const evidence = item.evidence.length ? item.evidence.map((entry) => `\`${entry}\``).join('<br>') : '-'
    const gaps = item.missing.length ? item.missing.join('<br>') : '-'
    const next = item.next.length ? item.next.join('<br>') : '-'
    return `| ${item.title} | ${item.status.toUpperCase()} | ${evidence} | ${gaps} | ${next} |`
  }),
  '',
  '## 判断口径',
  '',
  '- 产品入口和账号入口必须分层：`时安agent` 是产品入口，`登录/注册` 是账号入口。',
  '- 本地复用线上登录 smoke 只证明登录链路，不能替代完整 Agent、积分、报告和真机验收。',
  '- 自动 H5 截图只能作为商店素材候选，不能替代各平台真实安装包截图。',
  '- 产品/GTM 通过不等于发行 ready；真实用户回收和平台安装包仍是硬门槛。',
  '- 人工事项交接包未清零时，产品上架审计不能通过。',
  '',
].join('\n')
writeFileSync(mdOut, md)

console.log(`Product launch audit: ${passed ? 'ready' : 'not-ready'}`)
console.log(`JSON: ${rel(jsonOut)}`)
console.log(`Markdown: ${rel(mdOut)}`)
console.log(`READY=${ready} PARTIAL=${partial} MISSING=${missing}`)

if (strict && !passed) {
  console.error('严格模式失败：产品/上架链路证据仍不完整。')
  process.exit(1)
}
