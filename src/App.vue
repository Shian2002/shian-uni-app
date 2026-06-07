<script>
export default {
  onLaunch() {
    // #ifdef H5
    var saved = ''
    try { saved = localStorage.getItem('xc_theme') || '' } catch(_) {}
    if (!saved) {
      try { saved = uni ? uni.getStorageSync('xc_theme') : '' } catch(_) {}
    }
    if (!saved) {
      try { saved = window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark' } catch(_) { saved = 'dark' }
    }
    try {
      localStorage.setItem('xc_theme', saved)
      uni.setStorageSync('xc_theme', saved)
    } catch(_) {}
    document.documentElement.setAttribute('data-theme', saved)
    document.body.setAttribute('data-theme', saved)
    function _hasAppHomeFlag() {
      try {
        var href = window.location.href || ''
        var hash = window.location.hash || ''
        var search = window.location.search || ''
        return /(?:[?&])app=(?:1|true)(?:&|$)/.test(href) ||
          /(?:[?&])app=(?:1|true)(?:&|$)/.test(hash) ||
          /(?:[?&])app=(?:1|true)(?:&|$)/.test(search)
      } catch(_) {}
      return false
    }
    function _setPageClass(name, enabled) {
      try {
        document.documentElement.classList.toggle(name, !!enabled)
        document.body.classList.toggle(name, !!enabled)
      } catch(_) {}
    }
    function _syncHomeFixedRoute() {
      try {
        var hash = window.location.hash || ''
        var isHome = hash.indexOf('#/pages/index/index') === 0 || hash === '' || hash === '#/' || hash.indexOf('#/?') === 0
        var isQimen = hash.indexOf('#/pages/qimen/index') === 0
        var isAppHome = isHome && _hasAppHomeFlag()
        var isMarketingHome = isHome && !isAppHome

        // app 首页是固定工作台，外层不参与滚动；长对话只在消息区内部滚动。
        _setPageClass('home-fixed-page', isAppHome && !isMarketingHome)
        _setPageClass('qimen-page-active', isQimen)
        if (!isHome || isMarketingHome) _setPageClass('marketing-page', isMarketingHome)
      } catch(_) {}
    }
    function _getActivePageScroller() {
      try {
        var pages = Array.prototype.slice.call(document.querySelectorAll('uni-page-wrapper'))
        for (var i = pages.length - 1; i >= 0; i--) {
          var el = pages[i]
          var rect = el.getBoundingClientRect()
          if (rect.width > 0 && rect.height > 0 && el.scrollHeight > el.clientHeight + 2) return el
        }
      } catch(_) {}
      return null
    }
    window.addEventListener('wheel', function(e) {
      try {
        var target = e && e.target
        if (target && target.closest && target.closest('.tarot-sidebar')) return
        var hash = window.location.hash || ''
        var isHome = hash.indexOf('#/pages/index/index') === 0 || hash === '' || hash === '#/' || hash.indexOf('#/?') === 0
        if (isHome || !e.deltaY) return
        var scroller = _getActivePageScroller()
        if (!scroller) return
        var before = scroller.scrollTop
        scroller.scrollTop += e.deltaY
        if (scroller.scrollTop !== before) e.preventDefault()
      } catch(_) {}
    }, { passive: false })
    _syncHomeFixedRoute()
    setTimeout(_syncHomeFixedRoute, 0)
    setTimeout(_syncHomeFixedRoute, 200)
    setTimeout(_syncHomeFixedRoute, 800)
    setTimeout(_syncHomeFixedRoute, 1600)
    window.addEventListener('load', function() { setTimeout(_syncHomeFixedRoute, 0); setTimeout(_syncHomeFixedRoute, 200) })
    window.addEventListener('hashchange', function() { setTimeout(_syncHomeFixedRoute, 0); setTimeout(_syncHomeFixedRoute, 120) })
    window.addEventListener('popstate', function() { setTimeout(_syncHomeFixedRoute, 0); setTimeout(_syncHomeFixedRoute, 120) })
    document.addEventListener('click', function() { setTimeout(_syncHomeFixedRoute, 80); setTimeout(_syncHomeFixedRoute, 300) }, true)
    function _isTypingTarget(el) {
      if (!el) return false
      var tag = (el.tagName || '').toLowerCase()
      return tag === 'input' || tag === 'textarea' || tag === 'select' || el.isContentEditable
    }
    function _closeTopLayer() {
      var closed = false
      try {
        var selectors = [
          '.modal-overlay.open',
          '.profile-sheet.open',
          '.tool-sheet.open',
          '.llm-sheet.open',
          '.nav-btn-more.open',
          '.nav-dropdown.open',
          '.nav-avatar-dropdown.open',
          '.nav-btn-drop-menu.open',
          '.sidebar-overlay.show',
          '.tarot-sidebar.open'
        ]
        selectors.forEach(function(sel) {
          document.querySelectorAll(sel).forEach(function(el) {
            el.classList.remove('open')
            el.classList.remove('show')
            closed = true
          })
        })
        document.querySelectorAll('.modal-overlay[style*="display: flex"], .modal-overlay[style*="display:flex"]').forEach(function(el) {
          el.style.display = 'none'
          closed = true
        })
      } catch(_) {}
      return closed
    }
    document.addEventListener('keydown', function(e) {
      try {
        if (e.key === 'Escape') {
          if (_closeTopLayer()) {
            e.preventDefault()
            e.stopPropagation()
          }
          return
        }
        if (e.key !== 'Enter' || e.shiftKey || e.metaKey || e.ctrlKey || e.altKey) return
        if (_isTypingTarget(e.target) && (e.target.tagName || '').toLowerCase() === 'textarea') return
        var modal = document.querySelector('.modal-overlay.open')
        if (!modal) return
        var primary = modal.querySelector('.btn-primary, .modal-confirm, .confirm-btn, .btn:not(.btn-outline):not(.btn-ghost):not(.btn-secondary)')
        if (primary && !primary.classList.contains('disabled')) {
          primary.click()
          e.preventDefault()
        }
      } catch(_) {}
    }, true)
    // 修复 uni-app H5 运行时桌面端强制缩放 rem 的问题
    // uni-app 内置 useRem() 会设 html font-size = width / 23.4375，
    // 桌面端 800px+ 视口下导致全局放大 2 倍以上。
    // 必须在 load/resize 事件后也覆盖，因为 useRem() 也监听了这些事件。
    // 仅在桌面端（>768px）启用覆盖，手机端由 uni-app 原生 rem 计算管理
    function _fixRem() { document.documentElement.style.fontSize = '16px' }
    _fixRem()
    window.addEventListener('load', _fixRem)
    window.addEventListener('resize', function() { setTimeout(_fixRem, 0); setTimeout(_fixRem, 50); setTimeout(_fixRem, 150); setTimeout(_fixRem, 300) })
    var _remLock = false
    new MutationObserver(function() {
      if (!_remLock && document.documentElement.style.fontSize !== '16px') {
        _remLock = true; _fixRem(); setTimeout(function() { _remLock = false }, 10)
      }
    }).observe(document.documentElement, { attributes: true, attributeFilter: ['style'] })
    // 后备：移除 overlay 并强制显示 #app
    setTimeout(function() {
      var o = document.getElementById('xc-overlay')
      if (o) o.style.display = 'none'
      var a = document.getElementById('app')
      if (a) a.style.setProperty('visibility', 'visible', 'important')
    }, 1500)
    // #endif
    var TAB_PAGES = ['/pages/index/index', '/pages/qimen/index', '/pages/bazi-index/index', '/pages/tarot/index', '/pages/liuyao/index', '/pages/meihua/index', '/pages/ziwei/index', '/pages/zeji/index', '/pages/calendar/index', '/pages/community/index', '/pages/profile/index']
    window.__xcRenderTabPath = function(path, queryStr) {
      try {
        if (!path || path === '/pages/index/index') path = '/'
        queryStr = queryStr || ''
        var isHome = path === '/'
        var isQimen = path === '/pages/qimen/index'
        document.documentElement.classList.toggle('home-fixed-page', isHome)
        document.body.classList.toggle('home-fixed-page', isHome)
        document.documentElement.classList.toggle('qimen-page-active', isQimen)
        document.body.classList.toggle('qimen-page-active', isQimen)

        var container = document.querySelector('.tab-pages-container')
        if (container) container.style.display = ''
        var wrappers = Array.prototype.slice.call(document.querySelectorAll('.tab-page-wrapper'))
        var target = wrappers.find(function(w) { return w.getAttribute('data-tab-path') === path })
        if (target) {
          wrappers.forEach(function(w) { w.style.display = w === target ? '' : 'none' })
        }
        var targetHash = path + queryStr
        var currentHash = (window.location.hash || '').replace('#', '') || '/'
        var currentPath = currentHash.split('?')[0] || '/'
        if (currentHash === '/pages/index/index') currentHash = '/'
        if (currentPath === '/pages/index/index') currentPath = '/'
        if (currentHash !== targetHash) window.location.hash = targetHash
      } catch (err) {
        console.warn('[tab-render-fallback]', err)
      }
    }
    window.__switchTabPageDom = window.__xcRenderTabPath
    document.addEventListener('click', function(e) {
      let el = e.target
      while (el && el.tagName !== 'A') { el = el.parentElement }
      if (!el || !el.href) return
      try {
        const urlObj = new URL(el.href, window.location.origin)
        const path = urlObj.pathname   // e.g. /pages/bazi-index/index
        const search = urlObj.search   // e.g. ?scenario=s_house
        // 只拦截指向 uni-app 页面的链接
        if (!/^\/(pages\/|package-)/.test(path)) return
        // 阻止整页导航
        e.preventDefault()
        e.stopImmediatePropagation()
        const fullPath = path + search
        if (TAB_PAGES.includes(path)) {
          if (search) {
            try { sessionStorage.setItem('_nav_query', search) } catch(_) {}
            uni.switchTab({
              url: path,
              success: function() {
                setTimeout(function() { try { uni.$emit('nav-query', search) } catch(_) {} }, 200)
              }
            })
          } else {
            uni.switchTab({ url: path })
          }
        } else {
          uni.navigateTo({ url: fullPath })
        }
      } catch (err) {
        console.warn('[navigator-fix]', err)
      }
    }, true)
  },
  onShow() {
    console.log('App Show')
  },
  onHide() {
    console.log('App Hide')
  }
}
</script>

<style>
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1200px; }
[data-theme="dark"] {
  --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824;
  --accent: #b2955d; --accent-2: #a07d10;
  --accent-hover: #8d7140;
  --accent-glow: rgba(178,149,93,0.10);
  --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12);
  --card-border-hover: rgba(255,255,255,0.18);
  --card-shadow: 0 16px 48px rgba(0,0,0,0.35);
  --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95);
  --text-3: rgba(170,160,145,0.88); --text-4: rgba(140,130,115,0.60);
  --danger: rgba(215,125,110,0.88);
  --success: rgba(7,233,48,0.88); --info: rgba(46,131,246,0.88);
  --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45);
  --tag-bg: rgba(255,255,255,0.08); --tag-text: rgba(195,185,165,0.85);
  --tab-active-bg: rgba(178,149,93,0.15);
  --sidebar-bg: rgba(30,34,55,0.55);
  --dayun-active: rgba(178,149,93,0.25);
  --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20);
  --hero-logo-backdrop: radial-gradient(circle, rgba(48,53,76,0.85) 50%, rgba(30,34,55,0.4) 80%, transparent 100%);
  --hero-logo-backdrop-shadow: 0 0 30px rgba(0,0,0,0.3);
}
[data-theme="light"] {
  --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0;
  --accent: #b2955d; --accent-2: #a07d10;
  --accent-hover: #8d7140;
  --accent-glow: rgba(178,149,93,0.065);
  --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045);
  --card-border-hover: rgba(0,0,0,0.08);
  --card-shadow: 0 8px 28px rgba(60,40,15,0.055);
  --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90);
  --text-3: rgba(100,88,68,0.78); --text-4: rgba(130,115,100,0.50);
  --danger: rgba(170,65,50,0.88);
  --success: rgba(7,233,48,0.88); --info: rgba(46,131,246,0.88);
  --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45);
  --tag-bg: rgba(0,0,0,0.05); --tag-text: rgba(70,58,40,0.80);
  --tab-active-bg: rgba(178,149,93,0.10);
  --sidebar-bg: rgba(245,242,234,0.55);
  --dayun-active: rgba(178,149,93,0.12);
  --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065);
  --hero-logo-backdrop: radial-gradient(circle, rgba(255,255,255,0.92) 50%, rgba(255,255,255,0.6) 80%, transparent 100%);
  --hero-logo-backdrop-shadow: 0 0 20px rgba(0,0,0,0.06);
}
html, body {
  margin: 0;
  padding: 0;
  background: #161a2a;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  -webkit-text-size-adjust: 100%;
  text-size-adjust: 100%;
  overflow-x: hidden;
  width: 100%;
  box-sizing: border-box;
}
/* 禁用 uni-app H5 内置的远程 picker 阴影预加载，避免线上请求 dcloud 图片触发 CORS 告警。 */
body::after {
  content: none !important;
  animation: none !important;
  background-image: none !important;
}
html[data-theme="light"], html[data-theme="light"] body {
  background: #f7f2ea;
}
#app, .uni-app, uni-app, uni-page-wrapper, uni-page, uni-page-body {
  background: #161a2a !important;
  background-color: #161a2a !important;
  overflow-x: hidden;
  width: 100%;
  box-sizing: border-box;
}
html[data-theme="light"] #app,
html[data-theme="light"] .uni-app,
html[data-theme="light"] uni-app,
html[data-theme="light"] uni-page-wrapper,
html[data-theme="light"] uni-page,
html[data-theme="light"] uni-page-body {
  background: #f7f2ea !important;
  background-color: #f7f2ea !important;
}
uni-page-wrapper.uni-page-wrapper--show {
  animation: none !important;
  -webkit-animation: none !important;
}
uni-page.uni-page-transitioning {
  animation: none !important;
  -webkit-animation: none !important;
  transition: none !important;
}
uni-tabbar, .uni-tabbar, .uni-tabbar-bottom {
  display: none !important;
  height: 0 !important;
  min-height: 0 !important;
}
.uni-app--showtabbar {
  padding-bottom: 0 !important;
}

/* ═══ 全局侧边栏样式（DOM 在 document.body 上，不受 scoped 限制） ═══ */
.tarot-sidebar {
  position:fixed; top:0; left:0; bottom:0; width:300px; z-index:400;
  background:rgba(22, 26, 42, 0.94); border-right:1px solid rgba(255,255,255,0.1);
  transform:translateX(-100%); transition:transform .3s ease;
  box-shadow:4px 0 24px rgba(0,0,0,.2);
  display:flex; flex-direction:column; overscroll-behavior:contain; touch-action:pan-y;
  -webkit-backdrop-filter: blur(20px) saturate(1.6);
  backdrop-filter: blur(20px) saturate(1.6);
}
[data-theme="light"] .tarot-sidebar {
  background: rgba(247, 242, 234, 0.94);
  border-right: 1px solid rgba(0,0,0,0.05);
  box-shadow: 4px 0 24px rgba(0,0,0,0.08);
}
.tarot-sidebar.open {
  left: 0 !important;
  right: auto !important;
  transform: translateX(0) !important;
  translate: 0 0 !important;
  display: flex !important;
  visibility: visible !important;
  pointer-events: auto !important;
  z-index: 2100 !important;
}
.sidebar-overlay { position:fixed; inset:0; z-index:2000; background:rgba(0,0,0,.4); display:none; }
.sidebar-overlay.show { display:block; z-index:2000 !important; }
.sidebar-brand { display:flex; align-items:center; gap:12px; padding:22px 24px 18px; border-bottom:1px solid var(--card-border); }
.sidebar-brand-icon-wrap { position:relative; display:flex; align-items:center; justify-content:center; width:48px; height:48px; flex-shrink:0; }
.sidebar-brand-icon-wrap::before { content:''; position:absolute; inset:0; border-radius:50%; background:var(--hero-logo-backdrop); box-shadow:var(--hero-logo-backdrop-shadow); z-index:0; }
.sidebar-brand-icon { width:38px; height:38px; object-fit:contain; position:relative; z-index:1; }
.sidebar-brand-name { font-family:var(--font-serif); font-size:1.3rem; color:var(--text-1); letter-spacing:4px; }
.sidebar-header { display:flex; justify-content:space-between; align-items:center; gap:12px; padding:12px 20px 10px; }
.sidebar-title { font-size:0.8rem; color:var(--text-4); letter-spacing:1px; }
.sidebar-close { font-size:1.2rem; color:var(--text-3); cursor:pointer; padding:4px; }
.sidebar-new-chat-btn {
  appearance:none; border:1px solid rgba(178,149,93,.42); border-radius:999px;
  background:rgba(178,149,93,.14); color:var(--accent); cursor:pointer;
  font-size:.75rem; font-weight:600; line-height:1; padding:8px 12px;
  transition:background .16s ease, border-color .16s ease, transform .16s ease;
}
.sidebar-new-chat-btn:hover { background:rgba(178,149,93,.22); border-color:rgba(178,149,93,.62); }
.sidebar-new-chat-btn:active { transform:translateY(1px) scale(.98); }
.sidebar-tabs { display:flex; gap:4px; padding:0 20px 8px; }
.sidebar-tab { font-size:0.75rem; padding:4px 12px; border-radius:12px; color:var(--text-3); background:transparent; transition:all .2s; }
.sidebar-tab.active { color:var(--accent); background:var(--accent-glow); }
/* 内容区（可滚动） */
.sidebar-content { flex:1; overflow-y:auto; min-height:0; overscroll-behavior:contain; -webkit-overflow-scrolling:touch; }
.sidebar-empty { text-align:center; color:var(--text-4); font-size:.85rem; padding:40px 20px; }
/* 分组 */
.sidebar-group { border-bottom:1px solid var(--card-border); }
.sidebar-group-header {
  display:flex; align-items:center; gap:8px; padding:10px 16px;
  cursor:pointer; user-select:none; transition:background .15s;
}
.sidebar-group-header:hover { background:var(--accent-glow); }
.sidebar-group-icon { font-size:1rem; flex-shrink:0; }
.sidebar-group-label { font-size:.78rem; color:var(--text-1); font-weight:600; flex:1; }
.sidebar-group-count { font-size:.68rem; color:var(--text-3); background:var(--tag-bg); border-radius:10px; padding:2px 8px; }
.sidebar-group-arrow { font-size:.7rem; color:var(--text-3); transition:transform .25s ease; }
.sidebar-group.collapsed .sidebar-group-arrow { transform:rotate(-90deg); }
.sidebar-group.collapsed .sidebar-group-items { display:none; }
.sidebar-group-items { padding:0 8px 4px; }
/* 列表项 */
.sidebar-item { display:flex; align-items:center; gap:8px; padding:0; border-bottom:1px solid var(--card-border); transition:background .15s; cursor:pointer; touch-action:manipulation; }
.sidebar-new-item .sidebar-item-body { background:var(--accent-glow); border-radius:10px; margin:6px; padding:9px 12px; }
.sidebar-new-item .sidebar-item-text { color:var(--accent); font-weight:600; }
.sidebar-item-body { flex:1; min-width:0; display:flex; flex-direction:column; gap:2px; padding:10px 14px; cursor:pointer; }
.sidebar-item-body:hover { background:var(--accent-glow); }
.sidebar-item-icon { font-size:1.3rem; flex-shrink:0; }
.sidebar-item-text { font-size:.82rem; color:var(--text-2); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sidebar-item-time { font-size:.68rem; color:var(--text-3); }
.sidebar-item-del { padding:8px 10px; font-size:.7rem; color:var(--text-4); cursor:pointer; flex-shrink:0; opacity:0; transition:opacity .15s,color .15s; }
.sidebar-item:hover .sidebar-item-del { opacity:1; }
.sidebar-item-del { touch-action:manipulation; }
@media (hover: none) {
  .sidebar-item-body:hover { background:transparent; }
  .sidebar-item:hover .sidebar-item-del { opacity:0; }
}
.sidebar-item-del:hover { color:var(--danger); }
.sidebar-item:last-child { border-bottom:none; }
/* 底部用户面板 */
.sidebar-user-panel { flex-shrink:0; border-top:1px solid var(--card-border); padding:12px 16px; background:var(--nav-bg); }
/* 侧边栏内详情面板 */
.sidebar-detail { flex:1; overflow-y:auto; min-height:0; display:flex; flex-direction:column; }
.sidebar-detail-back { font-size:.78rem; color:var(--accent); cursor:pointer; padding:10px 16px 6px; flex-shrink:0; }
.sidebar-detail-back:hover { opacity:.8; }
.sidebar-detail-title { font-size:.85rem; font-weight:700; color:var(--text-1); padding:0 16px 12px; flex-shrink:0; border-bottom:1px solid var(--card-border); }
.sidebar-detail-body { flex:1; overflow-y:auto; padding:16px; }
.sidebar-detail-body .tarot-detail-user,
.sidebar-detail-body .tarot-detail-ai { padding:8px 0; }
.sidebar-detail-body .tarot-detail-label { font-size:.7rem; color:var(--text-4); margin-bottom:4px; }
.sidebar-detail-body .tarot-detail-body { font-size:.82rem; color:var(--text-2); line-height:1.8; white-space:pre-wrap; word-break:break-word; }
.sidebar-detail-body .tarot-detail-ai .tarot-detail-body { color:var(--text-1); }
.sidebar-detail-body .history-markdown { font-size:.82rem; color:var(--text-2); line-height:1.8; }
.sidebar-detail-body .history-markdown p { margin-bottom:8px; }
.sidebar-user-logged { display:flex; align-items:center; gap:10px; }
.sidebar-user-avatar-wrap { width:36px; height:36px; border-radius:50%; background:rgba(255,255,255,0.08); overflow:hidden; display:flex; align-items:center; justify-content:center; flex-shrink:0; border:1px solid rgba(255,255,255,0.12); }
.sidebar-user-avatar { width:100%; height:100%; object-fit:cover; display:none; }
.sidebar-user-avatar-letter { font-size:.9rem; font-weight:700; color:var(--text-3); }
.sidebar-user-info { flex:1; min-width:0; display:flex; flex-direction:column; gap:2px; }
.sidebar-user-name { font-size:.82rem; font-weight:600; color:var(--text-1); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sidebar-user-points { font-size:.7rem; color:var(--accent); }
.sidebar-user-actions { display:flex; gap:8px; flex-shrink:0; }
.sidebar-user-setting, .sidebar-user-logout { font-size:.72rem; color:var(--text-3); cursor:pointer; padding:4px 8px; border-radius:6px; transition:color .15s, background .15s; }
.sidebar-user-setting:hover { color:var(--accent); background:var(--accent-glow); }
.sidebar-user-logout:hover { color:var(--danger); background:rgba(215,125,110,.1); }
.sidebar-user-guest { display:flex; align-items:center; justify-content:space-between; }
.sidebar-guest-text { font-size:.75rem; color:var(--text-3); }
.sidebar-guest-btn { font-size:.75rem; color:var(--accent); cursor:pointer; padding:4px 14px; border-radius:8px; border:1px solid var(--accent); transition:.2s; }
.sidebar-guest-btn:hover { background:var(--accent); color:#fff; }
.history-markdown h2, .history-markdown h3 { color:var(--accent); margin:14px 0 8px; }
.history-markdown strong { color:var(--text-1); }
.history-markdown p { margin-bottom:6px; }
/* 塔罗对话详情 */
.tarot-detail-user { margin-bottom:12px; padding:12px 14px; border-radius:10px; background:var(--accent-glow); }
.tarot-detail-ai { margin-bottom:16px; padding:12px 14px; border-radius:10px; background:var(--card-bg); border:1px solid var(--card-border); }
.tarot-detail-label { font-size:.7rem; color:var(--accent); margin-bottom:6px; letter-spacing:1px; }
.tarot-detail-body { font-size:.82rem; color:var(--text-2); line-height:1.7; white-space:pre-wrap; word-break:break-word; }
@media (max-width: 480px) { .tarot-sidebar { width:260px; } }
.ai-stage-logo{display:inline-block;width:18px;height:18px;border-radius:50%;vertical-align:middle;margin-right:3px;object-fit:cover;animation:ai-logo-spin 1s linear infinite}.ai-stage-logo-box{display:inline-block;width:18px;height:18px;border-radius:50%;vertical-align:middle;margin-right:3px;background:url(/static/images/logo.svg?v=7) center/cover no-repeat;animation:ai-logo-spin 1s linear infinite}@keyframes ai-logo-spin{0%{transform:rotate(0deg)}100%{transform:rotate(360deg)}}
.site-footer{margin-top:0!important;padding:16px 32px 12px!important}.site-footer .footer-disclaimer{margin-bottom:0!important}@media(max-width:768px){.site-footer{padding:12px 16px 10px!important}}
uni-page-wrapper{min-height:0!important}
.page-root{padding-top:60px!important}@media(max-width:768px){.page-root{padding-top:56px!important}}
body.marketing-page .page-root.marketing-active{padding-top:0!important}
body:not(.home-fixed-page) .page-root{
  height:auto!important;
  min-height:calc(100dvh - 60px)!important;
  overflow:visible!important;
}
body:not(.home-fixed-page) .page-wrap{
  height:auto!important;
  min-height:0!important;
  overflow:visible!important;
}
body:not(.home-fixed-page) uni-page-body,
body:not(.home-fixed-page) uni-page-wrapper{
  overflow-y:auto!important;
  -webkit-overflow-scrolling:touch;
}
body:not(.home-fixed-page) uni-page-wrapper{
  height:100dvh!important;
  max-height:100dvh!important;
}
body:not(.home-fixed-page) uni-page-body{
  height:auto!important;
  min-height:100%!important;
  overflow:visible!important;
}
@media(max-width:768px){
  body:not(.home-fixed-page) .page-root{min-height:calc(100dvh - 56px)!important}
}

/* 第二批工具页视觉优化：统一术数工具台的密度、层次和可点击状态 */
body:not(.home-fixed-page) .tool-hero,
body:not(.home-fixed-page) .tarot-hero{
  padding-top:42px!important;
  padding-bottom:22px!important;
}
body:not(.home-fixed-page) .tool-hero-title,
body:not(.home-fixed-page) .tarot-hero-title{
  font-size:clamp(1.45rem,2.2vw,2rem)!important;
  letter-spacing:3px!important;
  margin-bottom:8px!important;
}
body:not(.home-fixed-page) .tool-hero-desc,
body:not(.home-fixed-page) .tarot-hero-desc{
  max-width:720px;
  margin-left:auto!important;
  margin-right:auto!important;
  color:var(--text-3)!important;
}
body:not(.home-fixed-page) .section{
  padding-top:42px!important;
  padding-bottom:72px!important;
}
body:not(.home-fixed-page) .tool-container,
body:not(.home-fixed-page) .tarot-section{
  position:relative;
  border-radius:18px!important;
  border:1px solid rgba(178,149,93,.18)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.08),rgba(255,255,255,.035)),var(--card-bg)!important;
  box-shadow:0 18px 54px rgba(0,0,0,.16),inset 0 1px 0 rgba(255,255,255,.08)!important;
  overflow:visible!important;
}
body:not(.home-fixed-page) .tool-container::before,
body:not(.home-fixed-page) .tarot-section::before{
  content:'';
  position:absolute;
  left:18px;
  right:18px;
  top:0;
  height:1px;
  background:linear-gradient(90deg,transparent,rgba(178,149,93,.48),transparent);
  pointer-events:none;
}
body:not(.home-fixed-page) .tool-tabs{
  display:flex!important;
  gap:6px!important;
  padding:5px!important;
  margin-bottom:22px!important;
  border:1px solid rgba(178,149,93,.14)!important;
  border-radius:14px!important;
  background:rgba(0,0,0,.035)!important;
  position:static!important;
  top:auto!important;
  z-index:auto!important;
  overflow-x:auto!important;
  scrollbar-width:none;
}
body:not(.home-fixed-page) .tool-tabs::-webkit-scrollbar{display:none}
body:not(.home-fixed-page) .tool-tab{
  flex:1 0 auto;
  min-height:38px;
  display:inline-flex!important;
  align-items:center;
  justify-content:center;
  gap:4px;
  padding:9px 14px!important;
  border:1px solid transparent!important;
  border-radius:10px!important;
  color:var(--text-2)!important;
  background:transparent!important;
  white-space:nowrap;
  transition:background .18s ease,border-color .18s ease,color .18s ease,transform .18s ease!important;
}
body:not(.home-fixed-page) .tool-tab.active{
  color:var(--accent)!important;
  border-color:rgba(178,149,93,.34)!important;
  background:linear-gradient(180deg,rgba(178,149,93,.16),rgba(178,149,93,.07))!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.10);
}
body:not(.home-fixed-page) .tool-tab:hover{transform:translateY(-1px)}
body:not(.home-fixed-page) .tab-badge{
  border-radius:999px!important;
  padding:1px 6px!important;
  letter-spacing:0!important;
}
body:not(.home-fixed-page) .qf-datetime-section,
body:not(.home-fixed-page) .wz-advanced-box,
body:not(.home-fixed-page) .tarot-settings,
body:not(.home-fixed-page) .ly-auto-info{
  border:1px solid rgba(178,149,93,.14)!important;
  background:rgba(255,255,255,.045)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06);
}
body:not(.home-fixed-page) .qf-datetime-row,
body:not(.home-fixed-page) .wz-datetime-row{
  display:grid!important;
  grid-template-columns:repeat(auto-fit,minmax(92px,1fr))!important;
  gap:8px!important;
}
body:not(.home-fixed-page) .qf-dt-col,
body:not(.home-fixed-page) .wz-dt-col,
body:not(.home-fixed-page) .wz-dt-hour,
body:not(.home-fixed-page) .wz-dt-minute,
body:not(.home-fixed-page) .qf-dt-col-narrow{
  min-width:0!important;
  width:100%!important;
  flex:initial!important;
}
body:not(.home-fixed-page) .qf-datetime-select,
body:not(.home-fixed-page) .wz-datetime-select,
body:not(.home-fixed-page) .form-select-picker,
body:not(.home-fixed-page) .wz-form-input,
body:not(.home-fixed-page) .dom-input-wrap .native-input{
  min-height:38px!important;
  border-radius:10px!important;
  border-color:rgba(178,149,93,.18)!important;
  background:rgba(255,255,255,.06)!important;
  color:var(--text-1)!important;
}
body:not(.home-fixed-page) .qf-datetime-select:focus,
body:not(.home-fixed-page) .wz-datetime-select:focus,
body:not(.home-fixed-page) .form-select-picker:focus,
body:not(.home-fixed-page) .wz-form-input:focus,
body:not(.home-fixed-page) .dom-input-wrap .native-input:focus{
  border-color:rgba(178,149,93,.58)!important;
  box-shadow:0 0 0 3px rgba(178,149,93,.10)!important;
}
body:not(.home-fixed-page) .submit-btn,
body:not(.home-fixed-page) .wz-submit-btn,
body:not(.home-fixed-page) .tarot-draw-btn,
body:not(.home-fixed-page) .tarot-btn-primary,
body:not(.home-fixed-page) .zeji-submit{
  min-height:42px!important;
  border-radius:999px!important;
  background:linear-gradient(135deg,#7f6128,#c39a45 48%,#8c6a2b)!important;
  color:#fff!important;
  border:1px solid rgba(255,255,255,.18)!important;
  box-shadow:0 10px 24px rgba(105,73,18,.22),inset 0 1px 0 rgba(255,255,255,.18)!important;
  text-shadow:0 1px 1px rgba(0,0,0,.18);
  transition:transform .18s ease,box-shadow .18s ease,filter .18s ease!important;
}
body:not(.home-fixed-page) .submit-btn:hover,
body:not(.home-fixed-page) .wz-submit-btn:hover,
body:not(.home-fixed-page) .tarot-draw-btn:hover,
body:not(.home-fixed-page) .tarot-btn-primary:hover,
body:not(.home-fixed-page) .zeji-submit:hover{
  transform:translateY(-1px);
  filter:saturate(1.05);
  box-shadow:0 14px 30px rgba(105,73,18,.28),inset 0 1px 0 rgba(255,255,255,.22)!important;
}
body:not(.home-fixed-page) .btn-ghost,
body:not(.home-fixed-page) .tarot-btn-outline{
  min-height:40px!important;
  border-radius:999px!important;
  border-color:rgba(178,149,93,.22)!important;
  color:var(--text-2)!important;
  background:rgba(255,255,255,.04)!important;
}
body:not(.home-fixed-page) .record-page{
  border:1px solid rgba(178,149,93,.12);
  box-shadow:inset 0 1px 0 rgba(255,255,255,.05);
}
body:not(.home-fixed-page) .record-toolbar,
body:not(.home-fixed-page) .record-filter-row{
  gap:8px!important;
}
body:not(.home-fixed-page) .record-search{
  border:1px solid rgba(178,149,93,.14)!important;
  background:rgba(255,255,255,.055)!important;
}
body:not(.home-fixed-page) .record-filter-tag,
body:not(.home-fixed-page) .action-btn{
  border-radius:999px!important;
}
body:not(.home-fixed-page) .bz-card{
  border-radius:12px!important;
  border-color:rgba(178,149,93,.14)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.025)),var(--card-bg)!important;
  box-shadow:0 8px 22px rgba(0,0,0,.08);
}
body:not(.home-fixed-page) .bz-card:hover{
  transform:translateY(-1px);
  box-shadow:0 12px 28px rgba(0,0,0,.12);
}
body:not(.home-fixed-page) .tarot-hero-icon{
  font-size:3.25rem!important;
  margin-bottom:10px!important;
}
body:not(.home-fixed-page) .spread-card{
  border-radius:12px!important;
  border-color:rgba(178,149,93,.16)!important;
  background:rgba(255,255,255,.05)!important;
}
@media(max-width:768px){
  body:not(.home-fixed-page) .tool-hero,
  body:not(.home-fixed-page) .tarot-hero{padding:30px 16px 16px!important}
  body:not(.home-fixed-page) .section{padding:28px 14px 56px!important}
  body:not(.home-fixed-page) .tool-container,
  body:not(.home-fixed-page) .tarot-section{border-radius:16px!important}
  body:not(.home-fixed-page) .qf-datetime-row,
  body:not(.home-fixed-page) .wz-datetime-row{grid-template-columns:repeat(2,minmax(0,1fr))!important}
  body:not(.home-fixed-page) .btn-row{gap:8px!important}
}

/* 第三批工具页体验优化：首屏可达、记录与结果区阅读性 */
body:not(.home-fixed-page) .tool-tabs{
  position:static!important;
  top:auto!important;
  z-index:auto!important;
  backdrop-filter:blur(18px) saturate(150%);
}
body:not(.home-fixed-page) .record-tabs{
  position:sticky;
  top:68px;
  z-index:18;
  background:linear-gradient(180deg,rgba(255,255,255,.10),rgba(255,255,255,.04)),var(--card-bg);
  backdrop-filter:blur(18px) saturate(150%);
}
body:not(.home-fixed-page) .record-tab{
  min-height:44px;
  display:flex;
  align-items:center;
  border-bottom-width:3px!important;
}
body:not(.home-fixed-page) .record-empty{
  margin:14px 20px 22px!important;
  padding:42px 20px!important;
  border:1px dashed rgba(178,149,93,.22);
  border-radius:16px;
  background:rgba(255,255,255,.035);
}
body:not(.home-fixed-page) .empty-icon{
  opacity:.72!important;
  filter:drop-shadow(0 8px 18px rgba(120,80,12,.12));
}
body:not(.home-fixed-page) .qai-stream-box,
body:not(.home-fixed-page) .qai-result,
body:not(.home-fixed-page) .ly-result-card,
body:not(.home-fixed-page) .qf-result-card,
body:not(.home-fixed-page) .tarot-reading-section,
body:not(.home-fixed-page) .chat-bubble-ai{
  border-radius:16px!important;
  border-color:rgba(178,149,93,.16)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.025)),var(--card-bg)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.06)!important;
}
body:not(.home-fixed-page) .qai-card-title,
body:not(.home-fixed-page) .reading-title,
body:not(.home-fixed-page) .qf-result-title{
  letter-spacing:1px!important;
}
body:not(.home-fixed-page) .chat-input-bar{
  border-radius:14px!important;
  border:1px solid rgba(178,149,93,.16)!important;
  background:rgba(255,255,255,.045)!important;
}
body:not(.home-fixed-page) .chat-input{
  min-height:38px!important;
  border-radius:999px!important;
  border-color:rgba(178,149,93,.16)!important;
  background:rgba(255,255,255,.055)!important;
}
body:not(.home-fixed-page) .chat-send-btn{
  min-height:38px!important;
  border-radius:999px!important;
  display:flex!important;
  align-items:center;
  justify-content:center;
  background:linear-gradient(135deg,#7f6128,#c39a45 48%,#8c6a2b)!important;
  box-shadow:0 8px 18px rgba(105,73,18,.18);
}
body:not(.home-fixed-page) .tarot-btn-row,
body:not(.home-fixed-page) .btn-row,
body:not(.home-fixed-page) .wz-smart-btns{
  align-items:stretch!important;
}
body:not(.home-fixed-page) .tarot-btn-row .btn-ghost,
body:not(.home-fixed-page) .btn-row .btn-ghost{
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}
@media(max-width:480px){
  body:not(.home-fixed-page) .page-root{padding-top:52px!important}
  body:not(.home-fixed-page) .tool-hero,
  body:not(.home-fixed-page) .tarot-hero{padding:18px 14px 10px!important}
  body:not(.home-fixed-page) .tool-hero-title,
  body:not(.home-fixed-page) .tarot-hero-title{font-size:1.16rem!important;letter-spacing:1.5px!important}
  body:not(.home-fixed-page) .tool-hero-desc,
  body:not(.home-fixed-page) .tarot-hero-desc{font-size:.72rem!important;line-height:1.55!important;letter-spacing:.5px!important}
  body:not(.home-fixed-page) .section{padding:14px 10px 48px!important}
  body:not(.home-fixed-page) .tool-container,
  body:not(.home-fixed-page) .tarot-section{padding:14px 10px!important}
  body:not(.home-fixed-page) .tool-tabs{top:auto!important;margin-bottom:14px!important}
  body:not(.home-fixed-page) .record-tabs{top:56px;padding:0 10px!important}
  body:not(.home-fixed-page) .tool-tab{min-height:34px!important;padding:7px 10px!important;font-size:.72rem!important}
  body:not(.home-fixed-page) .tab-badge{font-size:.48rem!important}
  body:not(.home-fixed-page) .qf-datetime-row,
  body:not(.home-fixed-page) .wz-datetime-row{grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:6px!important}
  body:not(.home-fixed-page) .qf-datetime-select,
  body:not(.home-fixed-page) .wz-datetime-select,
  body:not(.home-fixed-page) .form-select-picker,
  body:not(.home-fixed-page) .wz-form-input,
  body:not(.home-fixed-page) .dom-input-wrap .native-input{min-height:36px!important;font-size:.78rem!important}
  body:not(.home-fixed-page) .submit-btn,
  body:not(.home-fixed-page) .wz-submit-btn,
  body:not(.home-fixed-page) .tarot-draw-btn,
  body:not(.home-fixed-page) .tarot-btn-primary,
  body:not(.home-fixed-page) .zeji-submit{min-height:40px!important;font-size:.84rem!important;letter-spacing:1px!important}
  body:not(.home-fixed-page) .tarot-btn-row,
  body:not(.home-fixed-page) .btn-row{display:grid!important;grid-template-columns:1fr!important}
  body:not(.home-fixed-page) .tarot-btn-row > *,
  body:not(.home-fixed-page) .btn-row > *,
  body:not(.home-fixed-page) .wz-smart-btns > *{width:100%!important;max-width:100%!important;box-sizing:border-box!important}
  body:not(.home-fixed-page) .spread-grid{grid-template-columns:1fr 1fr!important;gap:8px!important}
  body:not(.home-fixed-page) .spread-card{min-height:72px!important;padding:9px 10px!important}
  body:not(.home-fixed-page) .spread-card-desc{-webkit-line-clamp:2!important}
  body:not(.home-fixed-page) .record-toolbar{padding:10px 12px 4px!important}
  body:not(.home-fixed-page) .record-filter-row{padding:8px 12px 10px!important}
  body:not(.home-fixed-page) .case-cards,
  body:not(.home-fixed-page) .star-cards{padding:12px!important}
  body:not(.home-fixed-page) .bz-card .card-gz{min-width:104px!important;gap:6px!important;padding:6px!important}
  body:not(.home-fixed-page) .bz-card .gz-col{flex-basis:24px!important;min-width:24px!important}
  body:not(.home-fixed-page) .bz-card .gz-circle{width:22px!important;height:22px!important}
  body:not(.home-fixed-page) .record-empty{margin:12px!important;padding:32px 14px!important}
}

/* 第四批内容页视觉收口：个人中心、积分中心、专属日历、社区、关于我们 */
body:not(.home-fixed-page) .about-hero,
body:not(.home-fixed-page) .calendar-hero{
  padding-top:46px!important;
  padding-bottom:24px!important;
}
body:not(.home-fixed-page) .about-hero-title,
body:not(.home-fixed-page) .calendar-hero-title{
  font-size:clamp(1.36rem,2vw,1.86rem)!important;
  letter-spacing:2.5px!important;
  margin-bottom:10px!important;
}
body:not(.home-fixed-page) .about-hero-desc,
body:not(.home-fixed-page) .calendar-hero-desc{
  color:var(--text-3)!important;
  max-width:720px!important;
}
body:not(.home-fixed-page) .points-card,
body:not(.home-fixed-page) .calendar-card,
body:not(.home-fixed-page) .profile-card,
body:not(.home-fixed-page) .settings-list,
body:not(.home-fixed-page) .community-post-card,
body:not(.home-fixed-page) .up-header,
body:not(.home-fixed-page) .faq-panel,
body:not(.home-fixed-page) .trust-authority,
body:not(.home-fixed-page) .case-card,
body:not(.home-fixed-page) .feature-card,
body:not(.home-fixed-page) .scenario-card,
body:not(.home-fixed-page) .edu-card,
body:not(.home-fixed-page) .hero-card{
  border-color:rgba(178,149,93,.16)!important;
  box-shadow:0 16px 42px rgba(0,0,0,.12),inset 0 1px 0 rgba(255,255,255,.07)!important;
}
body:not(.home-fixed-page) .calendar-card,
body:not(.home-fixed-page) .settings-list,
body:not(.home-fixed-page) .community-post-card,
body:not(.home-fixed-page) .up-header,
body:not(.home-fixed-page) .faq-panel,
body:not(.home-fixed-page) .trust-authority,
body:not(.home-fixed-page) .case-card,
body:not(.home-fixed-page) .feature-card,
body:not(.home-fixed-page) .scenario-card,
body:not(.home-fixed-page) .edu-card,
body:not(.home-fixed-page) .hero-card{
  background:linear-gradient(180deg,rgba(255,255,255,.065),rgba(255,255,255,.026)),var(--card-bg)!important;
}
body:not(.home-fixed-page) .points-card{
  background:
    radial-gradient(circle at 82% 0%,rgba(255,255,255,.22),transparent 34%),
    linear-gradient(135deg,#84662b 0%,#c5a14e 48%,#7a5b22 100%)!important;
  border:1px solid rgba(255,255,255,.18)!important;
  overflow:hidden!important;
}
body:not(.home-fixed-page) .signin-btn,
body:not(.home-fixed-page) .load-more,
body:not(.home-fixed-page) .cal-nav-btn,
body:not(.home-fixed-page) .pd-back,
body:not(.home-fixed-page) .pd-like-btn,
body:not(.home-fixed-page) .pd-edit-btn,
body:not(.home-fixed-page) .img-upload-btn{
  border-radius:999px!important;
  border-color:rgba(178,149,93,.22)!important;
}
body:not(.home-fixed-page) .pkg-scroll{
  gap:12px!important;
  padding:4px 2px 10px!important;
  overflow-x:auto!important;
  scrollbar-width:none;
}
body:not(.home-fixed-page) .pkg-scroll::-webkit-scrollbar{display:none}
body:not(.home-fixed-page) .pkg-card{
  border-radius:14px!important;
  border-color:rgba(178,149,93,.16)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.06),rgba(255,255,255,.025)),var(--card-bg)!important;
  box-shadow:0 8px 22px rgba(0,0,0,.08)!important;
}
body:not(.home-fixed-page) .pkg-card:first-child{
  background:linear-gradient(180deg,rgba(178,149,93,.20),rgba(178,149,93,.06)),var(--card-bg)!important;
  border-color:rgba(178,149,93,.46)!important;
}
body:not(.home-fixed-page) .dp-tabs,
body:not(.home-fixed-page) .case-tabs,
body:not(.home-fixed-page) .category-tab,
body:not(.home-fixed-page) .sort-tab{
  gap:8px!important;
  overflow-x:auto!important;
  flex-wrap:nowrap!important;
  scrollbar-width:none;
}
body:not(.home-fixed-page) .dp-tabs::-webkit-scrollbar,
body:not(.home-fixed-page) .case-tabs::-webkit-scrollbar,
body:not(.home-fixed-page) .category-tab::-webkit-scrollbar,
body:not(.home-fixed-page) .sort-tab::-webkit-scrollbar{display:none}
body:not(.home-fixed-page) .dp-tab,
body:not(.home-fixed-page) .case-tab,
body:not(.home-fixed-page) .ctab,
body:not(.home-fixed-page) .stab{
  flex:0 0 auto!important;
  border-radius:999px!important;
  border-color:rgba(178,149,93,.18)!important;
  background:rgba(255,255,255,.035)!important;
  color:var(--text-2)!important;
}
body:not(.home-fixed-page) .dp-tab.active,
body:not(.home-fixed-page) .case-tab.active,
body:not(.home-fixed-page) .ctab.active,
body:not(.home-fixed-page) .stab.active{
  color:var(--accent)!important;
  background:rgba(178,149,93,.14)!important;
  border-color:rgba(178,149,93,.46)!important;
}
body:not(.home-fixed-page) .dp-list{
  border-color:rgba(178,149,93,.16)!important;
  background:rgba(255,255,255,.025)!important;
}
body:not(.home-fixed-page) .dp-item{
  min-height:58px!important;
  gap:12px!important;
}
body:not(.home-fixed-page) .cal-grid{
  gap:5px!important;
}
body:not(.home-fixed-page) .cal-cell{
  min-height:72px!important;
  border-radius:10px!important;
  background:rgba(255,255,255,.045)!important;
  border-color:rgba(178,149,93,.08)!important;
}
body:not(.home-fixed-page) .cal-cell.today,
body:not(.home-fixed-page) .cal-cell.selected{
  background:rgba(178,149,93,.14)!important;
  border-color:rgba(178,149,93,.52)!important;
  box-shadow:0 0 0 1px rgba(178,149,93,.18)!important;
}
body:not(.home-fixed-page) .cal-detail-item,
body:not(.home-fixed-page) .compliance-notice,
body:not(.home-fixed-page) .search-row .form-input,
body:not(.home-fixed-page) .settings-accordion{
  border:1px solid rgba(178,149,93,.14)!important;
  background:rgba(255,255,255,.045)!important;
}
body:not(.home-fixed-page) .search-row .form-input:focus{
  border-color:rgba(178,149,93,.55)!important;
  box-shadow:0 0 0 3px rgba(178,149,93,.10)!important;
}
body:not(.home-fixed-page) .community-post-card{
  padding:22px!important;
}
body:not(.home-fixed-page) .post-avatar,
body:not(.home-fixed-page) .up-avatar,
body:not(.home-fixed-page) .profile-card-avatar{
  box-shadow:0 8px 22px rgba(0,0,0,.12),inset 0 1px 0 rgba(255,255,255,.12)!important;
}
body:not(.home-fixed-page) .post-badge{
  border-color:rgba(178,149,93,.35)!important;
  background:rgba(178,149,93,.12)!important;
}
body:not(.home-fixed-page) .post-actions,
body:not(.home-fixed-page) .pd-actions{
  border-top-color:rgba(178,149,93,.12)!important;
}
body:not(.home-fixed-page) .settings-item{
  min-height:50px!important;
  border-bottom-color:rgba(178,149,93,.10)!important;
}
body:not(.home-fixed-page) .settings-item:hover,
body:not(.home-fixed-page) .dp-item:hover,
body:not(.home-fixed-page) .community-post-card:hover,
body:not(.home-fixed-page) .hero-card:hover,
body:not(.home-fixed-page) .scenario-card:hover{
  background:rgba(178,149,93,.08)!important;
  border-color:rgba(178,149,93,.32)!important;
}
body:not(.home-fixed-page) .settings-logout{
  border-radius:999px!important;
  background:rgba(215,125,110,.05)!important;
}
body:not(.home-fixed-page) .profile-empty,
body:not(.home-fixed-page) .com-empty,
body:not(.home-fixed-page) .com-loading,
body:not(.home-fixed-page) .record-empty{
  border-radius:16px!important;
  background:rgba(255,255,255,.035)!important;
}
body:not(.home-fixed-page) .section-alt,
body:not(.home-fixed-page) .site-footer{
  border-top:1px solid rgba(178,149,93,.10)!important;
}
body:not(.home-fixed-page) .section-title{
  letter-spacing:1.2px!important;
}
@media(max-width:768px){
  body:not(.home-fixed-page) .about-hero,
  body:not(.home-fixed-page) .calendar-hero{padding:30px 16px 16px!important}
  body:not(.home-fixed-page) .points-card{padding:24px 18px 22px!important}
  body:not(.home-fixed-page) .points-number{font-size:2.45rem!important}
  body:not(.home-fixed-page) .pkg-card{flex:0 0 132px!important}
  body:not(.home-fixed-page) .calendar-card{padding:16px!important}
  body:not(.home-fixed-page) .cal-grid{gap:4px!important}
  body:not(.home-fixed-page) .cal-cell{min-height:64px!important;padding:4px 1px!important}
  body:not(.home-fixed-page) .community-post-card{padding:16px!important}
  body:not(.home-fixed-page) .post-badge{margin-left:0!important}
}
@media(max-width:480px){
  body:not(.home-fixed-page) .about-hero,
  body:not(.home-fixed-page) .calendar-hero{padding:20px 14px 12px!important}
  body:not(.home-fixed-page) .about-hero-title,
  body:not(.home-fixed-page) .calendar-hero-title{font-size:1.12rem!important;letter-spacing:1.2px!important}
  body:not(.home-fixed-page) .about-hero-desc,
  body:not(.home-fixed-page) .calendar-hero-desc{font-size:.72rem!important;line-height:1.55!important}
  body:not(.home-fixed-page) .points-card{margin-bottom:16px!important}
  body:not(.home-fixed-page) .pkg-scroll{margin-left:-2px!important;margin-right:-2px!important}
  body:not(.home-fixed-page) .pkg-card{flex-basis:118px!important;padding:14px 10px!important}
  body:not(.home-fixed-page) .dp-item{padding:12px!important}
  body:not(.home-fixed-page) .cal-nav{gap:8px!important}
  body:not(.home-fixed-page) .cal-nav-title{font-size:.82rem!important;letter-spacing:1px!important}
  body:not(.home-fixed-page) .cal-cell{min-height:54px!important;border-radius:8px!important}
  body:not(.home-fixed-page) .cal-lunar,
  body:not(.home-fixed-page) .cal-gz,
  body:not(.home-fixed-page) .cal-jc{font-size:.46rem!important}
  body:not(.home-fixed-page) .search-row{gap:8px!important}
  body:not(.home-fixed-page) .category-tab,
  body:not(.home-fixed-page) .sort-tab{margin-bottom:14px!important}
  body:not(.home-fixed-page) .profile-card{gap:12px!important;padding-bottom:18px!important;margin-bottom:18px!important}
  body:not(.home-fixed-page) .settings-item{padding:12px!important}
  body:not(.home-fixed-page) .hero-card,
  body:not(.home-fixed-page) .trust-authority,
  body:not(.home-fixed-page) .case-card,
  body:not(.home-fixed-page) .feature-card,
  body:not(.home-fixed-page) .scenario-card,
  body:not(.home-fixed-page) .edu-card,
  body:not(.home-fixed-page) .faq-panel{box-shadow:0 10px 24px rgba(0,0,0,.10),inset 0 1px 0 rgba(255,255,255,.06)!important}
}

/* 第五批交互质感：焦点、按压、加载与键盘可达性 */
:focus{outline:none}
:focus-visible{
  outline:2px solid rgba(178,149,93,.62)!important;
  outline-offset:3px!important;
}
body:not(.home-fixed-page) .btn,
body:not(.home-fixed-page) .btn-primary,
body:not(.home-fixed-page) .btn-outline,
body:not(.home-fixed-page) .btn-ghost,
body:not(.home-fixed-page) .submit-btn,
body:not(.home-fixed-page) .wz-submit-btn,
body:not(.home-fixed-page) .tarot-draw-btn,
body:not(.home-fixed-page) .tarot-btn-primary,
body:not(.home-fixed-page) .tarot-btn-outline,
body:not(.home-fixed-page) .zeji-submit,
body:not(.home-fixed-page) .chat-send-btn,
body:not(.home-fixed-page) .home-ai-send,
body:not(.home-fixed-page) .signin-btn,
body:not(.home-fixed-page) .load-more,
body:not(.home-fixed-page) .cal-nav-btn,
body:not(.home-fixed-page) .pd-back,
body:not(.home-fixed-page) .pd-like-btn,
body:not(.home-fixed-page) .pd-edit-btn,
body:not(.home-fixed-page) .img-upload-btn,
body:not(.home-fixed-page) .settings-item,
body:not(.home-fixed-page) .record-filter-tag,
body:not(.home-fixed-page) .action-btn,
body:not(.home-fixed-page) .tool-tab,
body:not(.home-fixed-page) .record-tab,
body:not(.home-fixed-page) .dp-tab,
body:not(.home-fixed-page) .case-tab,
body:not(.home-fixed-page) .ctab,
body:not(.home-fixed-page) .stab{
  -webkit-tap-highlight-color:transparent;
  touch-action:manipulation;
  transition:transform .16s ease,border-color .16s ease,box-shadow .16s ease,background .16s ease,color .16s ease,opacity .16s ease!important;
}
body:not(.home-fixed-page) .btn:active,
body:not(.home-fixed-page) .btn-primary:active,
body:not(.home-fixed-page) .btn-outline:active,
body:not(.home-fixed-page) .btn-ghost:active,
body:not(.home-fixed-page) .submit-btn:active,
body:not(.home-fixed-page) .wz-submit-btn:active,
body:not(.home-fixed-page) .tarot-draw-btn:active,
body:not(.home-fixed-page) .tarot-btn-primary:active,
body:not(.home-fixed-page) .tarot-btn-outline:active,
body:not(.home-fixed-page) .zeji-submit:active,
body:not(.home-fixed-page) .chat-send-btn:active,
body:not(.home-fixed-page) .home-ai-send:active,
body:not(.home-fixed-page) .signin-btn:active,
body:not(.home-fixed-page) .load-more:active,
body:not(.home-fixed-page) .cal-nav-btn:active,
body:not(.home-fixed-page) .pd-back:active,
body:not(.home-fixed-page) .pd-like-btn:active,
body:not(.home-fixed-page) .pd-edit-btn:active,
body:not(.home-fixed-page) .img-upload-btn:active,
body:not(.home-fixed-page) .tool-tab:active,
body:not(.home-fixed-page) .record-tab:active,
body:not(.home-fixed-page) .dp-tab:active,
body:not(.home-fixed-page) .case-tab:active,
body:not(.home-fixed-page) .ctab:active,
body:not(.home-fixed-page) .stab:active{
  transform:translateY(1px) scale(.985)!important;
}
body:not(.home-fixed-page) .disabled,
body:not(.home-fixed-page) [disabled],
body:not(.home-fixed-page) .btn.disabled,
body:not(.home-fixed-page) .submit-btn.disabled,
body:not(.home-fixed-page) .tarot-draw-btn.disabled{
  cursor:not-allowed!important;
  opacity:.55!important;
  filter:saturate(.8)!important;
  box-shadow:none!important;
}
body:not(.home-fixed-page) .com-loading,
body:not(.home-fixed-page) .record-loading,
body:not(.home-fixed-page) .loading,
body:not(.home-fixed-page) .loading-text,
body:not(.home-fixed-page) #calLoadingMsg{
  position:relative;
  overflow:hidden;
}
body:not(.home-fixed-page) .com-loading::after,
body:not(.home-fixed-page) .record-loading::after,
body:not(.home-fixed-page) .loading::after,
body:not(.home-fixed-page) .loading-text::after,
body:not(.home-fixed-page) #calLoadingMsg::after{
  content:'';
  position:absolute;
  inset:0;
  transform:translateX(-100%);
  background:linear-gradient(90deg,transparent,rgba(178,149,93,.12),transparent);
  animation:xc-shimmer 1.45s ease-in-out infinite;
  pointer-events:none;
}
@keyframes xc-shimmer{100%{transform:translateX(100%)}}
body:not(.home-fixed-page) ::selection{
  background:rgba(178,149,93,.28);
  color:var(--text-1);
}
body:not(.home-fixed-page) *{
  scrollbar-width:thin;
  scrollbar-color:rgba(178,149,93,.34) transparent;
}
body:not(.home-fixed-page) *::-webkit-scrollbar{width:8px;height:8px}
body:not(.home-fixed-page) *::-webkit-scrollbar-thumb{background:rgba(178,149,93,.30);border-radius:999px}
body:not(.home-fixed-page) *::-webkit-scrollbar-track{background:transparent}

/* 第六批表单与弹层收口：弹窗可达、输入清晰、底部操作不被遮挡 */
body:not(.home-fixed-page) .modal-overlay{
  padding:18px!important;
  box-sizing:border-box!important;
  overscroll-behavior:contain!important;
}
body:not(.home-fixed-page) .modal-box{
  width:min(92vw,460px)!important;
  max-height:min(82dvh,720px)!important;
  overflow:auto!important;
  border-radius:20px!important;
  border:1px solid rgba(178,149,93,.18)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.03)),var(--card-bg)!important;
  box-shadow:0 24px 76px rgba(0,0,0,.32),inset 0 1px 0 rgba(255,255,255,.08)!important;
}
body:not(.home-fixed-page) .modal-title{
  margin-bottom:18px!important;
  line-height:1.35!important;
}
body:not(.home-fixed-page) .modal-btns{
  position:sticky;
  bottom:-1px;
  padding-top:12px;
  background:linear-gradient(180deg,transparent,var(--card-bg) 34%);
}
body:not(.home-fixed-page) .modal-btns .btn,
body:not(.home-fixed-page) .modal-btns > *{
  min-height:40px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
}
body:not(.home-fixed-page) input,
body:not(.home-fixed-page) textarea,
body:not(.home-fixed-page) select,
body:not(.home-fixed-page) .form-input,
body:not(.home-fixed-page) .field-input,
body:not(.home-fixed-page) .chat-input,
body:not(.home-fixed-page) .record-search-input,
body:not(.home-fixed-page) .native-input,
body:not(.home-fixed-page) .dom-input-wrap .native-input{
  caret-color:var(--accent)!important;
}
body:not(.home-fixed-page) textarea,
body:not(.home-fixed-page) .form-textarea{
  line-height:1.7!important;
  resize:vertical;
}
body:not(.home-fixed-page) input::placeholder,
body:not(.home-fixed-page) textarea::placeholder,
body:not(.home-fixed-page) .form-input::placeholder,
body:not(.home-fixed-page) .field-input::placeholder,
body:not(.home-fixed-page) .chat-input::placeholder{
  color:var(--text-4)!important;
}
body:not(.home-fixed-page) .field-label,
body:not(.home-fixed-page) .form-label,
body:not(.home-fixed-page) .settings-group-title,
body:not(.home-fixed-page) .modal-error{
  letter-spacing:.8px!important;
}
body:not(.home-fixed-page) .modal-error{
  border-radius:10px!important;
}
body:not(.home-fixed-page) .profile-sheet-panel,
body:not(.home-fixed-page) .tool-sheet-panel,
body:not(.home-fixed-page) .llm-sheet-panel{
  border:1px solid rgba(178,149,93,.18)!important;
  box-shadow:0 24px 76px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.08)!important;
}

/* 第七批移动与暗黑一致性：安全区、阅读宽度、降级动效 */
body:not(.home-fixed-page) .page-root{
  padding-bottom:max(34px,env(safe-area-inset-bottom))!important;
}
body:not(.home-fixed-page) .qai-result,
body:not(.home-fixed-page) .qai-stream-box,
body:not(.home-fixed-page) .ly-result-card,
body:not(.home-fixed-page) .qf-result-card,
body:not(.home-fixed-page) .tarot-reading-section,
body:not(.home-fixed-page) .chat-bubble-ai,
body:not(.home-fixed-page) .post-content,
body:not(.home-fixed-page) .sidebar-detail-body,
body:not(.home-fixed-page) .history-markdown{
  text-wrap:pretty;
  word-break:break-word;
}
[data-theme="dark"] body:not(.home-fixed-page) .modal-box,
[data-theme="dark"] body:not(.home-fixed-page) .tool-container,
[data-theme="dark"] body:not(.home-fixed-page) .tarot-section,
[data-theme="dark"] body:not(.home-fixed-page) .calendar-card,
[data-theme="dark"] body:not(.home-fixed-page) .community-post-card,
[data-theme="dark"] body:not(.home-fixed-page) .settings-list,
[data-theme="dark"] body:not(.home-fixed-page) .hero-card{
  background:linear-gradient(180deg,rgba(255,255,255,.075),rgba(255,255,255,.032)),rgba(48,53,76,.90)!important;
  border-color:rgba(255,255,255,.15)!important;
}
[data-theme="light"] body:not(.home-fixed-page) .modal-box,
[data-theme="light"] body:not(.home-fixed-page) .tool-container,
[data-theme="light"] body:not(.home-fixed-page) .tarot-section,
[data-theme="light"] body:not(.home-fixed-page) .calendar-card,
[data-theme="light"] body:not(.home-fixed-page) .community-post-card,
[data-theme="light"] body:not(.home-fixed-page) .settings-list,
[data-theme="light"] body:not(.home-fixed-page) .hero-card{
  background:linear-gradient(180deg,rgba(255,255,255,.72),rgba(255,255,255,.44)),rgba(255,253,248,.70)!important;
}
@media(max-width:768px){
  body:not(.home-fixed-page) .modal-overlay{
    align-items:flex-end!important;
    padding:12px!important;
    padding-bottom:max(12px,env(safe-area-inset-bottom))!important;
  }
  body:not(.home-fixed-page) .modal-box{
    width:100%!important;
    max-height:84dvh!important;
    border-radius:22px 22px 16px 16px!important;
    padding:22px 18px 18px!important;
  }
  body:not(.home-fixed-page) .modal-btns{
    display:grid!important;
    grid-template-columns:1fr 1fr!important;
    gap:8px!important;
  }
  body:not(.home-fixed-page) .modal-btns > *:only-child{
    grid-column:1 / -1;
  }
}
@media(max-width:480px){
  body:not(.home-fixed-page) .tool-container,
  body:not(.home-fixed-page) .tarot-section,
  body:not(.home-fixed-page) .calendar-card,
  body:not(.home-fixed-page) .community-post-card,
  body:not(.home-fixed-page) .settings-list,
  body:not(.home-fixed-page) .points-card,
  body:not(.home-fixed-page) .hero-card{
    border-radius:16px!important;
  }
  body:not(.home-fixed-page) .sidebar-detail-body,
  body:not(.home-fixed-page) .history-markdown,
  body:not(.home-fixed-page) .post-content{
    font-size:.82rem!important;
    line-height:1.75!important;
  }
}
@media(prefers-reduced-motion:reduce){
  *,
  *::before,
  *::after{
    animation-duration:.001ms!important;
    animation-iteration-count:1!important;
    scroll-behavior:auto!important;
    transition-duration:.001ms!important;
  }
}
.dp-list{border:1px solid var(--card-border);border-radius:12px;overflow:hidden}.dp-item{display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid var(--card-border);transition:background .12s}.dp-item:last-child{border-bottom:none}.dp-item:hover{background:var(--accent-glow)}.dp-left{display:flex;flex-direction:column;gap:3px;min-width:0;flex:1}.dp-desc{font-size:.85rem;color:var(--text-1);font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.dp-date{font-size:.7rem;color:var(--text-3)}.dp-points{font-size:1rem;font-weight:700;flex-shrink:0;min-width:60px;text-align:right}.dp-plus{color:var(--accent)}.dp-minus{color:var(--danger)}
.dp-tabs{display:flex;gap:8px;margin-bottom:12px}.dp-tab{padding:6px 18px;border-radius:18px;font-size:.8rem;color:var(--text-3);background:var(--card-bg);border:1px solid var(--card-border);cursor:pointer;transition:all .15s}.dp-tab.active{background:var(--accent-glow);color:var(--accent);border-color:var(--accent)}.dp-tab:hover{background:var(--accent-glow)}.dp-pager{display:flex;align-items:center;justify-content:center;gap:6px;margin-top:14px}.dp-page-btn{padding:4px 12px;border-radius:8px;font-size:.85rem;color:var(--accent);cursor:pointer;background:var(--card-bg);border:1px solid var(--card-border);transition:all .12s}.dp-page-btn:hover{background:var(--accent-glow)}.dp-page-num{padding:4px 10px;border-radius:6px;font-size:.78rem;color:var(--text-3);cursor:pointer;transition:all .12s;min-width:28px;text-align:center}.dp-page-num:hover{background:var(--accent-glow)}.dp-page-cur{background:var(--accent-glow);color:var(--accent);font-weight:600}.dp-page-ellipsis{padding:4px 8px;font-size:.78rem;color:var(--text-3);cursor:default}

/* 第八批全站设计系统：东方术数工作台骨架 */
:root{
  --xc-paper: rgba(255,253,247,.72);
  --xc-paper-strong: rgba(255,253,247,.88);
  --xc-ink-line: rgba(93,73,39,.11);
  --xc-red: #c95b61;
  --xc-green: #4c9a72;
}
[data-theme="dark"]{
  --xc-paper: rgba(45,50,73,.72);
  --xc-paper-strong: rgba(50,56,82,.9);
  --xc-ink-line: rgba(255,255,255,.09);
  --xc-red: #d87578;
  --xc-green: #78c89e;
}
body:not(.home-fixed-page) .page-root{
  background:
    linear-gradient(90deg,rgba(178,149,93,.045) 1px,transparent 1px),
    linear-gradient(180deg,rgba(178,149,93,.035) 1px,transparent 1px),
    radial-gradient(circle at 14% 12%,rgba(178,149,93,.12),transparent 28%),
    radial-gradient(circle at 86% 82%,rgba(178,149,93,.10),transparent 26%),
    var(--bg)!important;
  background-size:42px 42px,42px 42px,auto,auto,auto!important;
}
body:not(.home-fixed-page) .page-wrap,
body:not(.home-fixed-page) .page{
  max-width:min(1180px,calc(100vw - 32px))!important;
  margin-left:auto!important;
  margin-right:auto!important;
  box-sizing:border-box!important;
}
body:not(.home-fixed-page) .tool-hero,
body:not(.home-fixed-page) .tarot-hero,
body:not(.home-fixed-page) .about-hero,
body:not(.home-fixed-page) .calendar-hero{
  position:relative!important;
  width:min(1180px,calc(100vw - 32px))!important;
  margin-left:auto!important;
  margin-right:auto!important;
  text-align:center!important;
  padding:34px 0 18px!important;
}
body:not(.home-fixed-page) .tool-hero::before,
body:not(.home-fixed-page) .tarot-hero::before,
body:not(.home-fixed-page) .about-hero::before,
body:not(.home-fixed-page) .calendar-hero::before{
  display:none!important;
  content:none!important;
}
body:not(.home-fixed-page) .tool-hero-content,
body:not(.home-fixed-page) .tarot-hero-content,
body:not(.home-fixed-page) .about-hero-content,
body:not(.home-fixed-page) .calendar-hero-content{
  padding-left:0!important;
  max-width:780px!important;
  margin:0 auto!important;
  text-align:center!important;
}
body:not(.home-fixed-page) .section-tag{
  display:inline-flex!important;
  align-items:center!important;
  min-height:24px!important;
  padding:3px 10px!important;
  border:1px solid rgba(178,149,93,.22)!important;
  border-radius:999px!important;
  background:rgba(178,149,93,.08)!important;
  color:var(--accent)!important;
  letter-spacing:1.8px!important;
}
body:not(.home-fixed-page) .tool-hero-title,
body:not(.home-fixed-page) .tarot-hero-title,
body:not(.home-fixed-page) .about-hero-title,
body:not(.home-fixed-page) .calendar-hero-title{
  max-width:860px!important;
  margin-left:auto!important;
  margin-right:auto!important;
  letter-spacing:0!important;
  text-indent:0!important;
  line-height:1.16!important;
}
body:not(.home-fixed-page) .tool-hero-desc,
body:not(.home-fixed-page) .tarot-hero-desc,
body:not(.home-fixed-page) .about-hero-desc,
body:not(.home-fixed-page) .calendar-hero-desc{
  margin-left:auto!important;
  margin-right:auto!important;
  max-width:720px!important;
  line-height:1.75!important;
}
body:not(.home-fixed-page) .tool-container,
body:not(.home-fixed-page) .tarot-section,
body:not(.home-fixed-page) .calendar-card,
body:not(.home-fixed-page) .settings-list,
body:not(.home-fixed-page) .community-post-card,
body:not(.home-fixed-page) .admin-panel,
body:not(.home-fixed-page) .admin-section,
body:not(.home-fixed-page) .profile-card,
body:not(.home-fixed-page) .points-card,
body:not(.home-fixed-page) .hero-card{
  background:
    linear-gradient(180deg,rgba(255,255,255,.62),rgba(255,255,255,.20)),
    var(--xc-paper)!important;
  border:1px solid rgba(178,149,93,.18)!important;
  border-radius:18px!important;
  box-shadow:0 18px 54px rgba(74,54,24,.10),inset 0 1px 0 rgba(255,255,255,.36)!important;
}
[data-theme="dark"] body:not(.home-fixed-page) .tool-container,
[data-theme="dark"] body:not(.home-fixed-page) .tarot-section,
[data-theme="dark"] body:not(.home-fixed-page) .calendar-card,
[data-theme="dark"] body:not(.home-fixed-page) .settings-list,
[data-theme="dark"] body:not(.home-fixed-page) .community-post-card,
[data-theme="dark"] body:not(.home-fixed-page) .admin-panel,
[data-theme="dark"] body:not(.home-fixed-page) .admin-section,
[data-theme="dark"] body:not(.home-fixed-page) .profile-card,
[data-theme="dark"] body:not(.home-fixed-page) .points-card,
[data-theme="dark"] body:not(.home-fixed-page) .hero-card{
  background:linear-gradient(180deg,rgba(255,255,255,.075),rgba(255,255,255,.025)),var(--xc-paper)!important;
  box-shadow:0 18px 54px rgba(0,0,0,.26),inset 0 1px 0 rgba(255,255,255,.08)!important;
}
body:not(.home-fixed-page) .tool-container,
body:not(.home-fixed-page) .tarot-section{
  padding:22px!important;
  margin-left:auto!important;
  margin-right:auto!important;
  box-sizing:border-box!important;
}
body:not(.home-fixed-page) .tool-tabs,
body:not(.home-fixed-page) .record-tabs,
body:not(.home-fixed-page) .method-switch,
body:not(.home-fixed-page) .dp-tabs,
body:not(.home-fixed-page) .case-tabs,
body:not(.home-fixed-page) .category-tab,
body:not(.home-fixed-page) .sort-tab{
  padding:4px!important;
  border:1px solid rgba(178,149,93,.18)!important;
  border-radius:999px!important;
  background:rgba(178,149,93,.055)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.20)!important;
}
body:not(.home-fixed-page) .tool-tab,
body:not(.home-fixed-page) .record-tab,
body:not(.home-fixed-page) .method-switch-btn,
body:not(.home-fixed-page) .dp-tab,
body:not(.home-fixed-page) .case-tab,
body:not(.home-fixed-page) .ctab,
body:not(.home-fixed-page) .stab{
  border-radius:999px!important;
  border:0!important;
  background:transparent!important;
  color:var(--text-2)!important;
  box-shadow:none!important;
}
body:not(.home-fixed-page) .tool-tab.active,
body:not(.home-fixed-page) .record-tab.active,
body:not(.home-fixed-page) .method-switch-btn.active,
body:not(.home-fixed-page) .dp-tab.active,
body:not(.home-fixed-page) .case-tab.active,
body:not(.home-fixed-page) .ctab.active,
body:not(.home-fixed-page) .stab.active{
  background:var(--xc-paper-strong)!important;
  color:var(--accent)!important;
  box-shadow:0 6px 18px rgba(84,62,24,.11)!important;
}
body:not(.home-fixed-page) .qf-datetime-section,
body:not(.home-fixed-page) .wz-advanced-box,
body:not(.home-fixed-page) .tarot-settings,
body:not(.home-fixed-page) .ly-auto-info,
body:not(.home-fixed-page) .form-group,
body:not(.home-fixed-page) .qf-options-row,
body:not(.home-fixed-page) .profile-info-row,
body:not(.home-fixed-page) .settings-item{
  border-color:var(--xc-ink-line)!important;
  background:rgba(255,255,255,.26)!important;
  border-radius:14px!important;
}
body:not(.home-fixed-page) .qf-datetime-select,
body:not(.home-fixed-page) .wz-datetime-select,
body:not(.home-fixed-page) .form-select-picker,
body:not(.home-fixed-page) .wz-form-input,
body:not(.home-fixed-page) .dom-input-wrap .native-input,
body:not(.home-fixed-page) input,
body:not(.home-fixed-page) textarea,
body:not(.home-fixed-page) select{
  border:1px solid rgba(178,149,93,.20)!important;
  border-radius:12px!important;
  background:rgba(255,255,255,.45)!important;
  color:var(--text-1)!important;
}
[data-theme="dark"] body:not(.home-fixed-page) .qf-datetime-select,
[data-theme="dark"] body:not(.home-fixed-page) .wz-datetime-select,
[data-theme="dark"] body:not(.home-fixed-page) .form-select-picker,
[data-theme="dark"] body:not(.home-fixed-page) .wz-form-input,
[data-theme="dark"] body:not(.home-fixed-page) .dom-input-wrap .native-input,
[data-theme="dark"] body:not(.home-fixed-page) input,
[data-theme="dark"] body:not(.home-fixed-page) textarea,
[data-theme="dark"] body:not(.home-fixed-page) select{
  background:rgba(23,28,44,.46)!important;
}
body:not(.home-fixed-page) .qf-result,
body:not(.home-fixed-page) .ly-result,
body:not(.home-fixed-page) .mh-result,
body:not(.home-fixed-page) .zw-result,
body:not(.home-fixed-page) .qai-stream-box,
body:not(.home-fixed-page) .qai-result,
body:not(.home-fixed-page) .ly-result-card,
body:not(.home-fixed-page) .qf-result-card,
body:not(.home-fixed-page) .tarot-reading-section{
  border-radius:16px!important;
  border:1px solid rgba(178,149,93,.16)!important;
  background:linear-gradient(180deg,rgba(255,255,255,.38),rgba(255,255,255,.12)),rgba(255,255,255,.08)!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.22)!important;
}
body:not(.home-fixed-page) .submit-btn,
body:not(.home-fixed-page) .wz-submit-btn,
body:not(.home-fixed-page) .tarot-draw-btn,
body:not(.home-fixed-page) .tarot-btn-primary,
body:not(.home-fixed-page) .zeji-submit,
body:not(.home-fixed-page) .btn-primary{
  background:linear-gradient(135deg,#7f6128,#c7a252 52%,#8b6827)!important;
  border:1px solid rgba(255,255,255,.26)!important;
  border-radius:13px!important;
  color:#fff!important;
  box-shadow:0 12px 26px rgba(120,86,28,.20)!important;
}
body:not(.home-fixed-page) .btn-ghost,
body:not(.home-fixed-page) .tarot-btn-outline,
body:not(.home-fixed-page) .btn-outline,
body:not(.home-fixed-page) .qf-now-btn-sm{
  border:1px solid rgba(178,149,93,.22)!important;
  border-radius:12px!important;
  background:rgba(178,149,93,.06)!important;
  color:var(--text-2)!important;
}
body:not(.home-fixed-page) table,
body:not(.home-fixed-page) .admin-table,
body:not(.home-fixed-page) .detail-table{
  border-collapse:separate!important;
  border-spacing:0!important;
  border:1px solid rgba(178,149,93,.15)!important;
  border-radius:14px!important;
  overflow:hidden!important;
}
body:not(.home-fixed-page) th,
body:not(.home-fixed-page) td{
  border-color:rgba(178,149,93,.11)!important;
}
body:not(.home-fixed-page) th{
  background:rgba(178,149,93,.075)!important;
  color:var(--text-2)!important;
}
body.home-fixed-page .home-ai-console.has-chat{
  border:1px solid rgba(178,149,93,.18)!important;
  border-radius:18px!important;
  background:linear-gradient(180deg,rgba(255,255,255,.55),rgba(255,255,255,.18)),var(--xc-paper)!important;
  box-shadow:0 18px 54px rgba(74,54,24,.10),inset 0 1px 0 rgba(255,255,255,.36)!important;
}
[data-theme="dark"] body.home-fixed-page .home-ai-console.has-chat{
  background:linear-gradient(180deg,rgba(255,255,255,.07),rgba(255,255,255,.025)),var(--xc-paper)!important;
}
body.home-fixed-page .home-ai-chat-head,
body.home-fixed-page .home-tool-cards,
body.home-fixed-page .home-tool-card,
body.home-fixed-page .home-ai-agent-head{
  border-color:rgba(178,149,93,.16)!important;
}
body.home-fixed-page .home-tool-card,
body.home-fixed-page .home-tool-selector,
body.home-fixed-page .home-summary-card{
  border-radius:14px!important;
  background:rgba(255,255,255,.24)!important;
}
body.home-fixed-page .home-ai-main{
  border-top:1px solid rgba(178,149,93,.12)!important;
  background:linear-gradient(180deg,rgba(247,242,234,.68),rgba(247,242,234,.92))!important;
  bottom:max(12px,calc(env(safe-area-inset-bottom) + 8px))!important;
}
@media(max-width:768px){
  body:not(.home-fixed-page) .page-wrap,
  body:not(.home-fixed-page) .page,
  body:not(.home-fixed-page) .tool-hero,
  body:not(.home-fixed-page) .tarot-hero,
  body:not(.home-fixed-page) .about-hero,
  body:not(.home-fixed-page) .calendar-hero{
    width:min(100vw - 24px,560px)!important;
    max-width:min(100vw - 24px,560px)!important;
  }
  body:not(.home-fixed-page) .tool-container,
  body:not(.home-fixed-page) .tarot-section{
    padding:14px!important;
  }
  body:not(.home-fixed-page) .tool-hero-content,
  body:not(.home-fixed-page) .tarot-hero-content,
  body:not(.home-fixed-page) .about-hero-content,
  body:not(.home-fixed-page) .calendar-hero-content{
    padding-left:0!important;
  }
  body:not(.home-fixed-page) .tool-hero-title,
  body:not(.home-fixed-page) .tarot-hero-title,
  body:not(.home-fixed-page) .about-hero-title,
  body:not(.home-fixed-page) .calendar-hero-title{
    font-size:clamp(1.08rem,4.6vw,1.38rem)!important;
    line-height:1.24!important;
    white-space:normal!important;
    overflow-wrap:anywhere!important;
  }
  body:not(.home-fixed-page) .tool-hero-desc,
  body:not(.home-fixed-page) .tarot-hero-desc,
  body:not(.home-fixed-page) .about-hero-desc,
  body:not(.home-fixed-page) .calendar-hero-desc{
    font-size:.8rem!important;
    line-height:1.65!important;
    white-space:normal!important;
  }
  body:not(.home-fixed-page) .spread-grid{
    grid-template-columns:1fr!important;
  }
  body:not(.home-fixed-page) .spread-card{
    min-height:72px!important;
  }
  body:not(.home-fixed-page) .spread-card-desc{
    -webkit-line-clamp:2!important;
  }
  body:not(.home-fixed-page) .section{
    width:min(100vw - 24px,560px)!important;
    max-width:min(100vw - 24px,560px)!important;
    margin-left:auto!important;
    margin-right:auto!important;
    box-sizing:border-box!important;
  }
  body:not(.home-fixed-page) .tool-container,
  body:not(.home-fixed-page) .tarot-section,
  body:not(.home-fixed-page) .calendar-card,
  body:not(.home-fixed-page) .settings-list,
  body:not(.home-fixed-page) .community-post-card,
  body:not(.home-fixed-page) .points-card,
  body:not(.home-fixed-page) .hero-card{
    width:100%!important;
    max-width:100%!important;
    margin-left:auto!important;
    margin-right:auto!important;
    box-sizing:border-box!important;
  }
  body:not(.home-fixed-page) .submit-btn,
  body:not(.home-fixed-page) .wz-submit-btn,
  body:not(.home-fixed-page) .tarot-draw-btn,
  body:not(.home-fixed-page) .tarot-btn-primary,
  body:not(.home-fixed-page) .zeji-submit{
    position:sticky!important;
    bottom:max(14px,calc(env(safe-area-inset-bottom) + 8px))!important;
    z-index:30!important;
  }
  body:not(.home-fixed-page) .search-row{
    display:grid!important;
    grid-template-columns:1fr auto!important;
    align-items:center!important;
    gap:10px!important;
  }
  body:not(.home-fixed-page) .search-box{
    min-width:0!important;
  }
  body:not(.home-fixed-page) .search-row .btn,
  body:not(.home-fixed-page) .btn-accent{
    min-height:42px!important;
    padding:0 18px!important;
    display:inline-flex!important;
    align-items:center!important;
    justify-content:center!important;
    white-space:nowrap!important;
  }
  body:not(.home-fixed-page) .notif-bell{
    display:none!important;
  }
  body.home-fixed-page .home-ai-console.has-chat{
    border-radius:14px!important;
  }
}

/* 第九批全站居中与移动端手感修正 */
body.home-fixed-page .hero-brand,
body.home-fixed-page .hero-brand-icon-wrap,
body.home-fixed-page .hero-brand-icon{
  outline:none!important;
  border:0!important;
  -webkit-tap-highlight-color:transparent!important;
}
body.home-fixed-page .hero-brand-icon-wrap{
  animation:none!important;
}
body.home-fixed-page .hero-brand-icon{
  position:absolute!important;
  left:50%!important;
  top:50%!important;
  transform:translate(-50%,-50%)!important;
}
body.home-fixed-page .hero-brand::before,
body.home-fixed-page .hero-brand::after,
body.home-fixed-page .hero-brand-icon-wrap::after,
body.home-fixed-page .hero-brand-icon::before,
body.home-fixed-page .hero-brand-icon::after{
  display:none!important;
  content:none!important;
}
body.home-fixed-page .home-ai-main{
  bottom:max(12px,calc(env(safe-area-inset-bottom) + 10px))!important;
}
body.home-fixed-page .home-ai-toolbar{
  overflow:visible!important;
}
body:not(.home-fixed-page) .notif-bell{
  display:none!important;
}
body:not(.home-fixed-page) .header-icons{
  margin-left:0!important;
}
@media(max-width:768px){
  body.home-fixed-page .hero-home{
    padding-bottom:calc(var(--home-ai-dock-space) + env(safe-area-inset-bottom) + 16px)!important;
  }
  body.home-fixed-page .home-ai-main{
    width:calc(100vw - 20px)!important;
    bottom:max(12px,calc(env(safe-area-inset-bottom) + 10px))!important;
  }
}

/* 第十批首页空态单屏锁定：避免下滑时底部 AI 输入栏被挤出视口 */
html.home-fixed-page:not(:has(.home-ai-console.has-chat)),
body.home-fixed-page:not(:has(.home-ai-console.has-chat)){
  height:100dvh!important;
  min-height:100dvh!important;
  max-height:100dvh!important;
  overflow:hidden!important;
  overscroll-behavior:none!important;
}
body.home-fixed-page:not(:has(.home-ai-console.has-chat)) uni-page-body,
body.home-fixed-page:not(:has(.home-ai-console.has-chat)) uni-page-wrapper,
body.home-fixed-page:not(:has(.home-ai-console.has-chat)) .uni-page-body,
body.home-fixed-page:not(:has(.home-ai-console.has-chat)) .page-root{
  height:100dvh!important;
  min-height:100dvh!important;
  max-height:100dvh!important;
  overflow:hidden!important;
}
body.home-fixed-page:not(:has(.home-ai-console.has-chat)) .page-wrap,
body.home-fixed-page:not(:has(.home-ai-console.has-chat)) .hero-home{
  height:calc(100dvh - 60px)!important;
  min-height:calc(100dvh - 60px)!important;
  max-height:calc(100dvh - 60px)!important;
  overflow:hidden!important;
}
body.home-fixed-page:not(:has(.home-ai-console.has-chat)) .home-ai-main{
  bottom:max(18px,calc(env(safe-area-inset-bottom) + 14px))!important;
  max-height:min(128px,calc(100dvh - 120px))!important;
  overflow:hidden!important;
}
</style>
