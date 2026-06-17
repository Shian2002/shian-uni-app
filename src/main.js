// Copyright (c) 2026 JunJunXu. All rights reserved.
// 原始发起与核心开发：JunJunXu <904752171@qq.com>

import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

const csrfWriteMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])
const productionApiOrigin = 'https://shianjieyouwu.com'
let csrfToken = ''
let csrfTokenPromise = null

function isRelativeApiUrl(url) {
  return typeof url === 'string' && (url === '/api' || url.indexOf('/api/') === 0)
}

function isNativeAppRuntime() {
  try {
    if (typeof plus !== 'undefined' && plus && plus.runtime) return true
  } catch (_) {}
  try {
    if (typeof uni !== 'undefined' && uni && uni.getSystemInfoSync) {
      const info = uni.getSystemInfoSync() || {}
      const uniPlatform = String(info.uniPlatform || '').toLowerCase()
      const platform = String(info.platform || '').toLowerCase()
      if (uniPlatform.indexOf('app') === 0) return true
      if (platform === 'android' || platform === 'ios' || platform === 'harmony') return true
    }
  } catch (_) {}
  return false
}

function shouldUseProductionApiOrigin() {
  if (isNativeAppRuntime()) return true
  if (typeof window === 'undefined' || !window.location) return true
  const protocol = window.location.protocol || ''
  return protocol !== 'http:' && protocol !== 'https:'
}

function normalizeApiUrl(url) {
  if (!isRelativeApiUrl(url)) return url
  return shouldUseProductionApiOrigin() ? productionApiOrigin + url : url
}

function isApiUrl(url) {
  if (!url) return false
  if (typeof url === 'string') {
    if (isRelativeApiUrl(url)) return true
    if (url.indexOf(productionApiOrigin + '/api/') === 0 || url === productionApiOrigin + '/api') return true
    if (typeof window !== 'undefined' && window.location) {
      return url.indexOf(window.location.origin + '/api/') === 0
    }
  }
  return false
}

function requestMethod(options) {
  return String((options && (options.method || options.type)) || 'GET').toUpperCase()
}

function shouldAttachCsrf(url, options) {
  return isApiUrl(url) && csrfWriteMethods.has(requestMethod(options))
}

function attachCsrfHeader(options, token) {
  const next = options || {}
  const header = Object.assign({}, next.header || next.headers || {})
  if (token) {
    header['X-CSRFToken'] = token
  }
  next.header = header
  next.headers = header
  return next
}

function refreshCsrfToken() {
  if (csrfTokenPromise) return csrfTokenPromise
  if (typeof fetch !== 'function') {
    csrfToken = ''
    return Promise.resolve('')
  }
  csrfTokenPromise = fetch(normalizeApiUrl('/api/csrf-token'), { credentials: 'include' })
    .then(function(response) { return response.ok ? response.json() : {} })
    .then(function(data) {
      csrfToken = data.csrf_token || ''
      return csrfToken
    })
    .catch(function() {
      csrfToken = ''
      return ''
    })
    .finally(function() {
      csrfTokenPromise = null
    })
  return csrfTokenPromise
}

function installCsrfProtection() {
  refreshCsrfToken()

  if (typeof uni !== 'undefined' && uni.addInterceptor) {
    uni.addInterceptor('request', {
      invoke(args) {
        args.url = normalizeApiUrl(args.url)
        if (isApiUrl(args.url)) {
          args.withCredentials = true
        }
        if (shouldAttachCsrf(args.url, args)) {
          attachCsrfHeader(args, csrfToken)
        }
      },
    })
    uni.addInterceptor('uploadFile', {
      invoke(args) {
        args.url = normalizeApiUrl(args.url)
        if (isApiUrl(args.url)) {
          args.withCredentials = true
          attachCsrfHeader(args, csrfToken)
        }
      },
    })
  }

  if (typeof window !== 'undefined' && window.fetch && !window.__xuanCetCsrfFetchInstalled) {
    const originalFetch = window.fetch.bind(window)
    window.__xuanCetCsrfFetchInstalled = true
    window.fetch = function csrfFetch(input, init) {
      const url = typeof input === 'string' ? input : (input && input.url)
      const normalizedUrl = normalizeApiUrl(url)
      const nextInput = typeof input === 'string' && normalizedUrl !== input ? normalizedUrl : input
      const options = Object.assign({}, init || {})
      const method = requestMethod(options)
      if (isApiUrl(normalizedUrl)) {
        options.credentials = options.credentials || 'include'
      }
      if (!shouldAttachCsrf(normalizedUrl, { method })) {
        return originalFetch(nextInput, isApiUrl(normalizedUrl) ? options : init)
      }
      return refreshCsrfToken().then(function(token) {
        const headers = new Headers(options.headers || (input && input.headers) || {})
        if (token) {
          headers.set('X-CSRFToken', token)
        }
        options.headers = headers
        options.credentials = options.credentials || 'include'
        return originalFetch(nextInput, options)
      })
    }
  }

  if (typeof window !== 'undefined' && window.EventSource && !window.__xuanCetEventSourceInstalled) {
    const OriginalEventSource = window.EventSource
    window.__xuanCetEventSourceInstalled = true
    window.EventSource = function ShianEventSource(url, config) {
      const normalizedUrl = normalizeApiUrl(url)
      return new OriginalEventSource(normalizedUrl, config)
    }
    window.EventSource.prototype = OriginalEventSource.prototype
  }

  if (typeof window !== 'undefined' && window.XMLHttpRequest && !window.__xuanCetXhrInstalled) {
    const OriginalXMLHttpRequest = window.XMLHttpRequest
    window.__xuanCetXhrInstalled = true
    window.XMLHttpRequest = function ShianXMLHttpRequest() {
      const xhr = new OriginalXMLHttpRequest()
      const originalOpen = xhr.open
      xhr.open = function open(method, url) {
        const args = Array.prototype.slice.call(arguments)
        args[1] = normalizeApiUrl(url)
        return originalOpen.apply(xhr, args)
      }
      return xhr
    }
    window.XMLHttpRequest.prototype = OriginalXMLHttpRequest.prototype
  }
}

installCsrfProtection()

export function createApp() {
  const app = createSSRApp(App)
  const pinia = createPinia()
  app.use(pinia)
  app.config.errorHandler = function(err, instance, info) {
    if (err && err.message && (
      err.message.indexOf('read only property') > -1 ||
      err.message.indexOf("Cannot read properties of null (reading 'type')") > -1
    )) {
      return
    }
    console.error('[Vue]', err)
  }
  return { app }
}
