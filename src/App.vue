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
    function _fixRem() { document.documentElement.style.fontSize = '16px' }
    _fixRem()
    window.addEventListener('load', _fixRem)
    window.addEventListener('resize', _fixRem)
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
  --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88);
  --success: rgba(7,233,48,0.88); --info: rgba(46,131,246,0.88);
  --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45);
  --tag-bg: rgba(255,255,255,0.08); --tag-text: rgba(195,185,165,0.85);
  --tab-active-bg: rgba(178,149,93,0.15);
  --sidebar-bg: rgba(30,34,55,0.55);
  --dayun-active: rgba(178,149,93,0.25);
  --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20);
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
  --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88);
  --success: rgba(7,233,48,0.88); --info: rgba(46,131,246,0.88);
  --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45);
  --tag-bg: rgba(0,0,0,0.05); --tag-text: rgba(70,58,40,0.80);
  --tab-active-bg: rgba(178,149,93,0.10);
  --sidebar-bg: rgba(245,242,234,0.55);
  --dayun-active: rgba(178,149,93,0.12);
  --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065);
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
</style>
