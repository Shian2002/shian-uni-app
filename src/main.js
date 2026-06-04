import { createSSRApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'

const csrfWriteMethods = new Set(['POST', 'PUT', 'PATCH', 'DELETE'])
let csrfToken = ''
let csrfTokenPromise = null

function isApiUrl(url) {
  if (!url) return false
  if (typeof url === 'string') {
    if (url.indexOf('/api/') === 0) return true
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
  csrfTokenPromise = fetch('/api/csrf-token', { credentials: 'same-origin' })
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
        if (shouldAttachCsrf(args.url, args)) {
          attachCsrfHeader(args, csrfToken)
        }
      },
    })
    uni.addInterceptor('uploadFile', {
      invoke(args) {
        if (isApiUrl(args.url)) {
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
      const options = Object.assign({}, init || {})
      const method = requestMethod(options)
      if (!shouldAttachCsrf(url, { method })) {
        return originalFetch(input, init)
      }
      return refreshCsrfToken().then(function(token) {
        const headers = new Headers(options.headers || (input && input.headers) || {})
        if (token) {
          headers.set('X-CSRFToken', token)
        }
        options.headers = headers
        options.credentials = options.credentials || 'same-origin'
        return originalFetch(input, options)
      })
    }
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
