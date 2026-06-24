#!/usr/bin/env node

import { readFileSync } from 'node:fs'
import { request } from 'node:https'

const host = process.env.INDEXNOW_HOST || 'shianjieyouwu.com'
const key = (process.env.INDEXNOW_KEY || readFileSync(new URL('../public/indexnow-key.txt', import.meta.url), 'utf8')).trim()
const keyLocation = `https://${host}/indexnow-key.txt`
const urlList = (process.env.INDEXNOW_URLS || `https://${host}/,https://${host}/sitemap.xml`)
  .split(',')
  .map((url) => url.trim())
  .filter(Boolean)

const payload = JSON.stringify({
  host,
  key,
  keyLocation,
  urlList,
})

const options = {
  hostname: 'api.indexnow.org',
  path: '/IndexNow',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(payload),
  },
}

const req = request(options, (res) => {
  let body = ''
  res.setEncoding('utf8')
  res.on('data', (chunk) => {
    body += chunk
  })
  res.on('end', () => {
    const ok = res.statusCode >= 200 && res.statusCode < 300
    console.log(JSON.stringify({
      ok,
      statusCode: res.statusCode,
      statusMessage: res.statusMessage,
      host,
      keyLocation,
      urlList,
      body: body.slice(0, 500),
    }, null, 2))
    if (!ok) process.exit(1)
  })
})

req.on('error', (error) => {
  console.error(`[indexnow] 提交失败: ${error.message}`)
  process.exit(1)
})

req.write(payload)
req.end()
