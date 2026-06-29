// Copyright (c) 2026 JunJunXu. All rights reserved.
// 原始发起与核心开发：JunJunXu <904752171@qq.com>

import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

const csrfWriteMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])
const productionApiOrigin = 'https://shianjieyouwu.com'
let csrfToken = ''
let csrfTokenPromise = null
let sessionExpiredNoticeAt = 0

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

function apiPathFromUrl(url) {
  if (!url || typeof url !== 'string') return ''
  try {
    const base = typeof window !== 'undefined' && window.location ? window.location.origin : productionApiOrigin
    return new URL(url, base).pathname || ''
  } catch (_) {
    const queryIndex = url.indexOf('?')
    const clean = queryIndex > -1 ? url.slice(0, queryIndex) : url
    if (clean.indexOf('/api/') === 0 || clean === '/api') return clean
  }
  return ''
}

function isAuthEndpoint(path) {
  return path === '/api/login' ||
    path === '/api/register' ||
    path === '/api/logout' ||
    path === '/api/csrf-token' ||
    path === '/api/email/login' ||
    path === '/api/email/send' ||
    path === '/api/sms/login' ||
    path === '/api/sms/send' ||
    path.indexOf('/api/oauth/') === 0
}

function hasCachedAuthMarker() {
  try {
    if (typeof uni !== 'undefined' && uni.getStorageSync && uni.getStorageSync('xc_token')) return true
  } catch (_) {}
  try {
    if (typeof localStorage !== 'undefined' && localStorage.getItem('xc_token')) return true
  } catch (_) {}
  return false
}

function clearCachedAuthMarkers() {
  try {
    if (typeof uni !== 'undefined' && uni.removeStorageSync) {
      uni.removeStorageSync('xc_token')
      uni.removeStorageSync('xc_user')
      uni.removeStorageSync('xc_has_password')
      uni.removeStorageSync('xc_avatar')
    }
  } catch (_) {}
  try {
    if (typeof localStorage !== 'undefined') {
      localStorage.removeItem('xc_token')
      localStorage.removeItem('xc_user')
      localStorage.removeItem('xc_has_password')
      localStorage.removeItem('xc_avatar')
    }
  } catch (_) {}
}

function openExpiredLoginPrompt(message) {
  if (typeof window === 'undefined') return
  const text = message || '登录状态已过期，请重新登录'
  if (window._openLoginModal) {
    window._openLoginModal({ message: text, reason: 'expired' })
    return
  }
  try {
    setTimeout(function() {
      if (window._openLoginModal) window._openLoginModal({ message: text, reason: 'expired' })
    }, 120)
  } catch (_) {}
  try {
    if (typeof uni !== 'undefined' && uni.showToast) uni.showToast({ title: text, icon: 'none' })
  } catch (_) {}
}

function handleSessionExpired(options) {
  const opts = options || {}
  const openLogin = !!opts.openLogin
  const hadCachedAuth = hasCachedAuthMarker()
  clearCachedAuthMarkers()
  if (typeof window !== 'undefined') {
    try {
      window.dispatchEvent(new CustomEvent('xc-session-expired', {
        detail: {
          type: 'expired',
          reason: opts.reason || 'session-expired',
          openLogin,
        },
      }))
    } catch (_) {}
    try {
      window.dispatchEvent(new CustomEvent('xc-auth-changed', {
        detail: {
          type: 'expired',
          loggedIn: false,
        },
      }))
    } catch (_) {}
  }
  try {
    if (typeof uni !== 'undefined' && uni.$emit) {
      uni.$emit('xc-auth-changed', { type: 'expired', loggedIn: false })
    }
  } catch (_) {}
  if (openLogin) {
    const now = Date.now()
    if (!hadCachedAuth && now - sessionExpiredNoticeAt < 800) return
    sessionExpiredNoticeAt = now
    openExpiredLoginPrompt(opts.message)
  }
}

function inspectSessionResponse(url, statusCode, data, method) {
  if (!isApiUrl(url)) return
  const path = apiPathFromUrl(url)
  if (path === '/api/me' && data && data.guest && hasCachedAuthMarker()) {
    handleSessionExpired({ reason: 'me-returned-guest', openLogin: false })
    return
  }
  if (statusCode === 401 && !isAuthEndpoint(path)) {
    const methodName = String(method || 'GET').toUpperCase()
    handleSessionExpired({
      reason: 'api-unauthorized',
      openLogin: methodName !== 'GET',
      message: '登录状态已过期，请重新登录',
    })
  }
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
      const send = function() {
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
      return send().then(function(response) {
        if (!isApiUrl(normalizedUrl)) return response
        const cloned = response.clone()
        return cloned.json()
          .catch(function() { return null })
          .then(function(data) {
            inspectSessionResponse(normalizedUrl, response.status, data, method)
            return response
          })
      })
    }
  }

  if (typeof uni !== 'undefined' && uni.request && !uni.__xuanCetSessionRequestInstalled) {
    const originalUniRequest = uni.request.bind(uni)
    uni.__xuanCetSessionRequestInstalled = true
    uni.request = function sessionAwareRequest(options) {
      if (!options || typeof options !== 'object') return originalUniRequest(options)
      const requestUrl = options.url
      const method = requestMethod(options)
      const userSuccess = options.success
      const userFail = options.fail
      const userComplete = options.complete
      const shouldReturnPromise =
        typeof userSuccess !== 'function' &&
        typeof userFail !== 'function' &&
        typeof userComplete !== 'function'
      let resolveCompatRequest = null
      let rejectCompatRequest = null
      const compatPromise = shouldReturnPromise ? new Promise(function(resolve, reject) {
        resolveCompatRequest = resolve
        rejectCompatRequest = reject
      }) : null
      const nextOptions = Object.assign({}, options)
      let inspected = false
      const inspectOnce = function(res) {
        if (inspected) return
        inspected = true
        inspectSessionResponse(requestUrl, res && res.statusCode, res && res.data, method)
      }
      nextOptions.success = function(res) {
        try {
          inspectOnce(res)
        } catch (_) {}
        if (resolveCompatRequest) resolveCompatRequest(res)
        if (typeof userSuccess === 'function') return userSuccess.apply(this, arguments)
      }
      nextOptions.fail = function(err) {
        if (rejectCompatRequest) rejectCompatRequest(err)
        if (typeof userFail === 'function') return userFail.apply(this, arguments)
      }
      nextOptions.complete = function(res) {
        if (typeof userComplete === 'function') return userComplete.apply(this, arguments)
      }
      const result = originalUniRequest(nextOptions)
      if (result && typeof result.then === 'function') {
        return result.then(function(res) {
          try {
            inspectOnce(res)
          } catch (_) {}
          return res
        })
      }
      if (compatPromise) return compatPromise
      return result
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
        xhr.__xuanCetApiUrl = args[1]
        xhr.__xuanCetMethod = method
        return originalOpen.apply(xhr, args)
      }
      try {
        xhr.addEventListener('loadend', function() {
          inspectSessionResponse(xhr.__xuanCetApiUrl, xhr.status, null, xhr.__xuanCetMethod)
        })
      } catch (_) {}
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
