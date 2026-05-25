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
    // 修复 uni-app H5 运行时桌面端强制缩放 rem 的问题
    // uni-app 内置 useRem() 会设 html font-size = width / 23.4375，
    // 桌面端 800px+ 视口下导致全局放大 2 倍以上。
    // 必须在 load/resize 事件后也覆盖，因为 useRem() 也监听了这些事件。
    function _fixRem() { var w = window.innerWidth; var fs = '16px'; if (w >= 1920) fs = '18px'; else if (w >= 1400) fs = '17px'; document.documentElement.style.fontSize = fs }
    _fixRem()
    window.addEventListener('load', _fixRem)
    var _fixRemTimer
    window.addEventListener('resize', function() { clearTimeout(_fixRemTimer); _fixRemTimer = setTimeout(_fixRem, 120) })
    // #endif
    var TAB_PAGES = ['/pages/index/index', '/pages/qimen/index', '/pages/bazi-index/index', '/pages/tarot/index', '/pages/liuyao/index', '/pages/meihua/index', '/pages/ziwei/index', '/pages/zeji/index', '/pages/calendar/index', '/pages/community/index', '/pages/profile/index']
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
  --hero-logo-backdrop: radial-gradient(circle, rgba(255,255,255,0.75) 50%, rgba(255,255,255,0.35) 80%, transparent 100%);
  --hero-logo-backdrop-shadow: 0 0 20px rgba(100,80,40,0.08);
}
html, body {
  margin: 0;
  padding: 0;
  background: #161a2a;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}
html[data-theme="light"], html[data-theme="light"] body {
  background: #f7f2ea;
}
#app, .uni-app, uni-app, uni-page-wrapper, uni-page, uni-page-body {
  background: #161a2a !important;
  background-color: #161a2a !important;
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
  background:var(--nav-bg); border-right:1px solid var(--card-border);
  transform:translateX(-100%); transition:transform .3s ease;
  box-shadow:4px 0 24px rgba(0,0,0,.15);
  display:flex; flex-direction:column;
}
.tarot-sidebar.open { transform:translateX(0); }
.sidebar-overlay { position:fixed; inset:0; z-index:399; background:rgba(0,0,0,.4); display:none; }
.sidebar-overlay.show { display:block; }
.sidebar-brand { display:flex; align-items:center; gap:12px; padding:22px 24px 18px; border-bottom:1px solid var(--card-border); }
.sidebar-brand-icon-wrap { position:relative; display:flex; align-items:center; justify-content:center; width:52px; height:52px; flex-shrink:0; }
.sidebar-brand-icon-wrap::before { content:''; position:absolute; inset:0; border-radius:50%; background:var(--hero-logo-backdrop); box-shadow:var(--hero-logo-backdrop-shadow); z-index:0; }
.sidebar-brand-icon { width:38px; height:38px; object-fit:contain; position:relative; z-index:1; }
.sidebar-brand-name { font-family:var(--font-serif); font-size:1.3rem; color:var(--text-1); letter-spacing:4px; }
.sidebar-header { display:flex; justify-content:space-between; align-items:center; padding:12px 20px; }
.sidebar-title { font-size:0.8rem; color:var(--text-4); letter-spacing:1px; }
.sidebar-close { font-size:1.2rem; color:var(--text-3); cursor:pointer; padding:4px; }
/* 内容区（可滚动） */
.sidebar-content { flex:1; overflow-y:auto; min-height:0; }
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
.sidebar-item { display:flex; align-items:center; gap:10px; padding:10px 14px; cursor:pointer; border-bottom:1px solid var(--card-border); transition:background .15s; }
.sidebar-item:hover { background:var(--accent-glow); }
.sidebar-item:last-child { border-bottom:none; }
.sidebar-item-icon { font-size:1.3rem; flex-shrink:0; }
.sidebar-item-body { flex:1; min-width:0; display:flex; flex-direction:column; gap:2px; }
.sidebar-item-type { font-size:.7rem; color:var(--accent); }
.sidebar-item-text { font-size:.82rem; color:var(--text-2); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.sidebar-item-time { font-size:.68rem; color:var(--text-3); }
/* 底部用户面板 */
.sidebar-user-panel { flex-shrink:0; border-top:1px solid var(--card-border); padding:12px 16px; background:var(--nav-bg); }
.sidebar-user-logged { display:flex; align-items:center; gap:10px; }
.sidebar-user-avatar-wrap { width:36px; height:36px; border-radius:50%; background:var(--accent-glow); overflow:hidden; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.sidebar-user-avatar { width:100%; height:100%; object-fit:cover; display:none; }
.sidebar-user-avatar-letter { font-size:.9rem; font-weight:700; color:var(--accent); }
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
/* 历史详情弹窗 */
.history-detail-box { max-width:600px; max-height:70vh; overflow-y:auto; }
.history-detail-content { font-size:.85rem; color:var(--text-2); line-height:1.8; }
.history-markdown h2, .history-markdown h3 { color:var(--accent); margin:14px 0 8px; }
.history-markdown strong { color:var(--text-1); }
.history-markdown p { margin-bottom:6px; }
@media (max-width: 480px) { .tarot-sidebar { width:260px; } }
</style>
