/**
 * 时安解忧屋 H5 本地预览服务器
 * 功能：serve H5 static + proxy /api/ → https://shianjieyouwu.com
 */
const http = require('http')
const https = require('https')
const fs = require('fs')
const path = require('path')

const PORT = process.env.PORT || 3003
const BUILD_DIR = path.resolve(__dirname, '..', 'dist', 'build', 'h5')
const API_TARGET = process.env.API_TARGET || 'https://shianjieyouwu.com'

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'text/javascript; charset=utf-8',
  '.mjs':  'text/javascript; charset=utf-8',
  '.css':  'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg':  'image/svg+xml',
  '.png':  'image/png',
  '.jpg':  'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.ico':  'image/x-icon',
  '.woff': 'font/woff',
  '.woff2':'font/woff2',
  '.ttf':  'font/ttf',
}

function ct(fp) {
  return MIME[path.extname(fp).toLowerCase()] || 'application/octet-stream'
}

function filterHeaders(headers, target) {
  const tUrl = new URL(target)
  const blocked = new Set([
    'connection','content-length','host','origin','referer',
    'sec-fetch-dest','sec-fetch-mode','sec-fetch-site','transfer-encoding','upgrade'
  ])
  return Object.fromEntries(
    Object.entries(headers).filter(([k]) => !blocked.has(k.toLowerCase()))
      .concat([['host', tUrl.host], ['origin', tUrl.origin], ['referer', tUrl.origin + '/']])
  )
}

function rewriteSetCookie(headers) {
  const sc = headers['set-cookie']
  if (!Array.isArray(sc)) return headers
  return { ...headers, 'set-cookie': sc.map(c => c.replace(/;\s*Domain=[^;]*/gi, '').replace(/;\s*Secure/gi, '')) }
}

function proxyApi(req, res) {
  const targetUrl = new URL(req.url || '/', API_TARGET)
  const client = targetUrl.protocol === 'http:' ? http : https
  const proxyReq = client.request(targetUrl, {
    method: req.method || 'GET',
    headers: filterHeaders(req.headers, API_TARGET)
  }, (proxyRes) => {
    res.writeHead(proxyRes.statusCode || 502, rewriteSetCookie(proxyRes.headers))
    proxyRes.pipe(res)
  })
  proxyReq.on('error', (e) => {
    if (res.headersSent) { res.end(); return }
    res.writeHead(502, { 'Content-Type': 'application/json; charset=utf-8' })
    res.end(JSON.stringify({ error: 'proxy_failed', message: e.message }))
  })
  req.pipe(proxyReq)
}

const server = http.createServer((req, res) => {
  try {
    const url = new URL(req.url || '/', 'http://127.0.0.1')
    let pathname = decodeURIComponent(url.pathname || '/')

    // API proxy
    if (pathname === '/api' || pathname.startsWith('/api/')) {
      proxyApi(req, res)
      return
    }

    // Static files
    if (pathname === '/') pathname = '/index.html'
    const requested = path.resolve(path.join(BUILD_DIR, pathname))
    if (!requested.startsWith(BUILD_DIR)) {
      res.writeHead(403); res.end('Forbidden'); return
    }
    const filePath = fs.existsSync(requested) && fs.statSync(requested).isFile()
      ? requested
      : path.join(BUILD_DIR, 'index.html')
    res.writeHead(200, { 'Content-Type': ct(filePath), 'Cache-Control': 'no-store' })
    fs.createReadStream(filePath).pipe(res)
  } catch (e) {
    res.writeHead(500, { 'Content-Type': 'text/plain; charset=utf-8' })
    res.end(e.message)
  }
})

server.listen(PORT, '127.0.0.1', () => {
  const addr = server.address()
  console.log(`时安解忧屋 H5 预览服务器已启动:`)
  console.log(`  页面: http://127.0.0.1:${addr.port}/`)
  console.log(`  API代理: /api/ → ${API_TARGET}`)
  console.log(`  按 Ctrl+C 停止`)
})
