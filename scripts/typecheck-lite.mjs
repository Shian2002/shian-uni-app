#!/usr/bin/env node

import { existsSync, readFileSync } from 'node:fs'
import { extname, join } from 'node:path'

const root = process.cwd()
const issues = []

function readJson(path) {
  try {
    return JSON.parse(readFileSync(join(root, path), 'utf8'))
  } catch (error) {
    issues.push(`${path} JSON 解析失败: ${error.message}`)
    return null
  }
}

function requireFile(path) {
  if (!existsSync(join(root, path))) issues.push(`缺少必要文件: ${path}`)
}

function pageFile(pagePath) {
  return `src/${pagePath}.vue`
}

function checkPageExists(pagePath, source) {
  if (!pagePath || typeof pagePath !== 'string') {
    issues.push(`${source} 页面路径不是字符串`)
    return
  }
  requireFile(pageFile(pagePath))
}

function checkImagePath(path, source) {
  if (!path || typeof path !== 'string') {
    issues.push(`${source} 图标路径不是字符串`)
    return
  }
  const allowed = new Set(['.png', '.jpg', '.jpeg', '.svg', '.webp'])
  if (!allowed.has(extname(path).toLowerCase())) {
    issues.push(`${source} 图标扩展名异常: ${path}`)
  }
  requireFile(`src/${path}`)
}

requireFile('index.html')
requireFile('src/App.vue')
requireFile('src/main.js')
requireFile('src/pages.json')
requireFile('src/manifest.json')
requireFile('deploy-to-server.sh')

const pkg = readJson('package.json')
const pagesJson = readJson('src/pages.json')
const manifest = readJson('src/manifest.json')

if (pkg) {
  for (const script of ['lint', 'typecheck', 'test', 'build', 'build:h5', 'qa:local', 'qa:online']) {
    if (!pkg.scripts?.[script]) issues.push(`package.json 缺少 scripts.${script}`)
  }
}

if (manifest) {
  if (manifest.h5?.router?.mode !== 'hash') {
    issues.push(`src/manifest.json h5.router.mode 应为 hash，实际: ${manifest.h5?.router?.mode}`)
  }
  if (manifest.h5?.devServer?.proxy?.['/api']?.target !== 'http://localhost:5199') {
    issues.push('src/manifest.json /api 本地代理目标异常')
  }
}

if (pagesJson) {
  if (!Array.isArray(pagesJson.pages) || pagesJson.pages.length === 0) {
    issues.push('src/pages.json pages 不能为空')
  } else {
    for (const page of pagesJson.pages) {
      checkPageExists(page.path, 'pages')
    }
  }

  const mainPages = new Set((pagesJson.pages || []).map((page) => page.path))
  const tabList = pagesJson.tabBar?.list || []
  if (!Array.isArray(tabList) || tabList.length === 0) {
    issues.push('src/pages.json tabBar.list 不能为空')
  }
  for (const item of tabList) {
    if (!mainPages.has(item.pagePath)) {
      issues.push(`tabBar 页面未在 pages 中声明: ${item.pagePath}`)
    }
    checkPageExists(item.pagePath, 'tabBar')
    checkImagePath(item.iconPath, `tabBar ${item.pagePath}`)
    checkImagePath(item.selectedIconPath, `tabBar ${item.pagePath}`)
  }

  for (const pack of pagesJson.subPackages || []) {
    if (!pack.root || typeof pack.root !== 'string') {
      issues.push('subPackages.root 不是字符串')
      continue
    }
    for (const page of pack.pages || []) {
      checkPageExists(`${pack.root}/${page.path}`, `subPackages ${pack.root}`)
    }
  }
}

const deployScript = readFileSync(join(root, 'deploy-to-server.sh'), 'utf8')
for (const requiredSnippet of [
  'dist/build/h5/index.html',
  'dist/build/h5/assets',
  'dist/build/h5/static',
  'npm run qa:online',
]) {
  if (!deployScript.includes(requiredSnippet)) {
    issues.push(`deploy-to-server.sh 缺少关键部署约定: ${requiredSnippet}`)
  }
}

if (issues.length > 0) {
  console.error('[typecheck-lite] 发现问题:')
  for (const issue of issues) console.error(`- ${issue}`)
  process.exit(1)
}

console.log('[typecheck-lite] 通过，项目结构和关键配置正常')
