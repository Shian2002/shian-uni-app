const { app, BrowserWindow, Menu, shell } = require('electron')
const path = require('node:path')
const fs = require('node:fs')
const http = require('node:http')
const https = require('node:https')

// app.isPackaged may be undefined in some Electron runtimes
const isDev = (app && typeof app.isPackaged === 'boolean') ? !app.isPackaged : true
const localBuild = path.join(__dirname, '..', 'dist', 'build', 'h5', 'index.html')
const packagedBuild = path.join(process.resourcesPath || '', 'app.asar', 'app', 'index.html')
const fallbackUrl = process.env.SHIAN_DESKTOP_URL || 'http://localhost:5173'
const apiTarget = process.env.SHIAN_DESKTOP_API_TARGET || 'https://shianjieyouwu.com'
const desktopIcon = path.join(__dirname, 'assets', 'icon.png')
let staticServer = null
let desktopStartUrl = ''
let mainWindow = null

if (process.env.SHIAN_DESKTOP_USER_DATA_DIR) {
  app.setPath('userData', process.env.SHIAN_DESKTOP_USER_DATA_DIR)
}

const hasSingleInstanceLock = app.requestSingleInstanceLock()
if (!hasSingleInstanceLock) {
  app.quit()
}

function contentType(filePath) {
  const ext = path.extname(filePath).toLowerCase()
  const types = {
    '.html': 'text/html; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.webp': 'image/webp',
    '.ico': 'image/x-icon',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2'
  }
  return types[ext] || 'application/octet-stream'
}

function filterProxyRequestHeaders(headers, target) {
  const targetUrl = new URL(target)
  const blocked = new Set([
    'connection',
    'content-length',
    'host',
    'origin',
    'referer',
    'sec-fetch-dest',
    'sec-fetch-mode',
    'sec-fetch-site',
    'transfer-encoding',
    'upgrade'
  ])
  return Object.fromEntries(Object.entries(headers)
    .filter(([key]) => !blocked.has(key.toLowerCase()))
    .concat([
      ['host', targetUrl.host],
      ['origin', targetUrl.origin],
      ['referer', `${targetUrl.origin}/`]
    ]))
}

function rewriteSetCookieHeaders(headers) {
  const setCookie = headers['set-cookie']
  if (!Array.isArray(setCookie)) return headers
  return {
    ...headers,
    'set-cookie': setCookie.map((cookie) => cookie
      .replace(/;\s*Domain=[^;]*/gi, '')
      .replace(/;\s*Secure/gi, ''))
  }
}

function proxyApiRequest(req, res) {
  const targetUrl = new URL(req.url || '/', apiTarget)
  const client = targetUrl.protocol === 'http:' ? http : https
  const proxyReq = client.request(targetUrl, {
    method: req.method || 'GET',
    headers: filterProxyRequestHeaders(req.headers, apiTarget)
  }, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 502, rewriteSetCookieHeaders(proxyRes.headers))
    proxyRes.pipe(res)
  })

  proxyReq.on('error', (error) => {
    if (res.headersSent) {
      res.end()
      return
    }
    res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' })
    res.end(JSON.stringify({ error: 'desktop_api_proxy_failed', message: error.message }))
  })

  req.pipe(proxyReq)
}

function serveBuildDirectory(buildDir) {
  return new Promise((resolve, reject) => {
    const root = path.resolve(buildDir)
    const server = http.createServer((req, res) => {
      try {
        const url = new URL(req.url || '/', 'http://127.0.0.1')
        let pathname = decodeURIComponent(url.pathname || '/')
        if (pathname === '/api' || pathname.startsWith('/api/')) {
          proxyApiRequest(req, res)
          return
        }
        if (pathname === '/') pathname = '/index.html'
        const requested = path.resolve(path.join(root, pathname))
        if (!requested.startsWith(root)) {
          res.writeHead(403)
          res.end('Forbidden')
          return
        }
        const filePath = fs.existsSync(requested) && fs.statSync(requested).isFile()
          ? requested
          : path.join(root, 'index.html')
        res.writeHead(200, {
          'Content-Type': contentType(filePath),
          'Cache-Control': 'no-store'
        })
        fs.createReadStream(filePath).pipe(res)
      } catch (error) {
        res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' })
        res.end(error.message)
      }
    })
    server.once('error', reject)
    server.listen(0, '127.0.0.1', () => {
      staticServer = server
      const address = server.address()
      resolve(`http://127.0.0.1:${address.port}/`)
    })
  })
}

async function getStartUrl() {
  if (desktopStartUrl) return desktopStartUrl
  if (!isDev && fs.existsSync(packagedBuild)) {
    desktopStartUrl = await serveBuildDirectory(path.dirname(packagedBuild))
    return desktopStartUrl
  }
  if (fs.existsSync(localBuild)) {
    desktopStartUrl = await serveBuildDirectory(path.dirname(localBuild))
    return desktopStartUrl
  }
  desktopStartUrl = fallbackUrl
  return desktopStartUrl
}

function getDesktopAppStartUrl(startUrl) {
  const url = new URL(startUrl)
  url.hash = '/?app=1'
  return url.toString()
}

async function createWindow() {
  if (mainWindow && !mainWindow.isDestroyed()) {
    if (mainWindow.isMinimized()) mainWindow.restore()
    mainWindow.focus()
    return mainWindow
  }
  const win = new BrowserWindow({
    width: 1220,
    height: 820,
    minWidth: 960,
    minHeight: 680,
    title: '时安解忧屋',
    backgroundColor: '#f1e7d7',
    icon: fs.existsSync(desktopIcon) ? desktopIcon : undefined,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    titleBarOverlay: process.platform === 'darwin' ? {
      color: '#f1e7d7',
      symbolColor: '#5a4424',
      height: 36
    } : undefined,
    trafficLightPosition: process.platform === 'darwin' ? { x: 14, y: 9 } : undefined,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true
    }
  })
  mainWindow = win

  win.webContents.setWindowOpenHandler(({ url }) => {
    if (desktopStartUrl && url.startsWith(desktopStartUrl)) {
      return { action: 'allow' }
    }
    shell.openExternal(url)
    return { action: 'deny' }
  })

  win.webContents.on('will-navigate', (event, url) => {
    const allowedDesktop = desktopStartUrl && url.startsWith(desktopStartUrl)
    const allowedFallback = url.startsWith(fallbackUrl)
    if (!allowedDesktop && !allowedFallback) {
      event.preventDefault()
      shell.openExternal(url)
    }
  })

  const startUrl = await getStartUrl()
  win.loadURL(getDesktopAppStartUrl(startUrl))
  win.on('closed', () => {
    if (mainWindow === win) mainWindow = null
  })
  return win
}

function createAppMenu() {
  const template = [
    ...(process.platform === 'darwin' ? [{
      label: app.name || '时安解忧屋',
      submenu: [
        { role: 'about', label: '关于时安解忧屋' },
        { type: 'separator' },
        { role: 'services', label: '服务' },
        { type: 'separator' },
        { role: 'hide', label: '隐藏时安解忧屋' },
        { role: 'hideOthers', label: '隐藏其他' },
        { role: 'unhide', label: '全部显示' },
        { type: 'separator' },
        { role: 'quit', label: '退出时安解忧屋' }
      ]
    }] : []),
    {
      label: '编辑',
      submenu: [
        { role: 'undo', label: '撤销' },
        { role: 'redo', label: '重做' },
        { type: 'separator' },
        { role: 'cut', label: '剪切' },
        { role: 'copy', label: '复制' },
        { role: 'paste', label: '粘贴' },
        { role: 'selectAll', label: '全选' }
      ]
    },
    {
      label: '窗口',
      submenu: [
        { role: 'minimize', label: '最小化' },
        { role: 'zoom', label: '缩放' },
        ...(process.platform === 'darwin' ? [
          { type: 'separator' },
          { role: 'front', label: '前置全部窗口' }
        ] : [
          { role: 'close', label: '关闭' }
        ])
      ]
    }
  ]
  Menu.setApplicationMenu(Menu.buildFromTemplate(template))
}

app.whenReady().then(() => {
  app.setName('时安解忧屋')
  createAppMenu()
  createWindow()

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow()
    }
  })
})

app.on('second-instance', () => {
  if (!mainWindow || mainWindow.isDestroyed()) {
    createWindow()
    return
  }
  if (mainWindow.isMinimized()) mainWindow.restore()
  mainWindow.focus()
})

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit()
  }
})

app.on('before-quit', () => {
  if (staticServer) {
    staticServer.close()
    staticServer = null
  }
})
