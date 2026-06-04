/**
 * Patch v25 - pre-render all tab pages for H5 hash mode.
 *
 * uni-app H5 的 tabBar 默认会把所有 tab 页面同时挂载。这个项目有顶部
 * 导航、登录弹窗和多个排盘页。为了避免 hash 已切换但目标 tab wrapper
 * 尚未创建导致空白，这里显式预挂载所有 tab 页面，再用 display 控制显隐。
 */

const fs = require('fs')

const fp = 'node_modules/@dcloudio/uni-h5/dist/uni-h5.es.js'
let content = fs.readFileSync(fp, 'utf8')

let patchCount = 0
let failCount = 0

function replaceFunction(source, name, replacement) {
  const start = source.indexOf(`function ${name}(`)
  if (start < 0) return null

  const paramsStart = source.indexOf('(', start)
  if (paramsStart < 0) return null

  let parenDepth = 0
  let paramsEnd = -1
  for (let i = paramsStart; i < source.length; i++) {
    const ch = source[i]
    if (ch === '(') parenDepth++
    if (ch === ')') {
      parenDepth--
      if (parenDepth === 0) {
        paramsEnd = i
        break
      }
    }
  }
  if (paramsEnd < 0) return null

  const bodyStart = source.indexOf('{', paramsEnd)
  if (bodyStart < 0) return null

  let depth = 0
  for (let i = bodyStart; i < source.length; i++) {
    const ch = source[i]
    if (ch === '{') depth++
    if (ch === '}') {
      depth--
      if (depth === 0) {
        return source.substring(0, start) + replacement + source.substring(i + 1)
      }
    }
  }
  return null
}

const createRouterViewVNode = `function createRouterViewVNode({
  routeKey,
  isTabBar,
  routeCache: routeCache2
}) {
  // PATCHED v25: pre-render every tab page so tab switching never lands on an empty wrapper.
  if (isTabBar.value) {
    if (!window.__xcTabRenderVersionRef) window.__xcTabRenderVersionRef = ref(0);
    if (!window.__xcRenderTabPath) {
      window.__xcNormalizeTabPath = function(path) {
        if (!path || path === '/pages/index/index') return '/';
        return path.split('?')[0] || '/';
      };
      window.__xcRenderTabPath = function(path) {
        try {
          path = window.__xcNormalizeTabPath(path);
          var isHome = path === '/';
          var isQimen = path === '/pages/qimen/index';
          if (document && document.documentElement && document.body) {
            document.documentElement.classList.toggle('home-fixed-page', isHome);
            document.body.classList.toggle('home-fixed-page', isHome);
            document.documentElement.classList.toggle('qimen-page-active', isQimen);
            document.body.classList.toggle('qimen-page-active', isQimen);
          }
          var tabContainer = document.querySelector('.tab-pages-container');
          var wrappers = Array.prototype.slice.call(document.querySelectorAll('.tab-page-wrapper'));
          var target = wrappers.find(function(w) { return w.getAttribute('data-tab-path') === path; });
          if (tabContainer && target) tabContainer.style.display = '';
          if (target) {
            wrappers.forEach(function(w) { w.style.display = w === target ? '' : 'none'; });
          }
          if (window.__xcTabRenderVersionRef) window.__xcTabRenderVersionRef.value++;
        } catch(e) { console.warn('[patch v25] __xcRenderTabPath error:', e); }
      };
      window.__switchTabPageDom = function(path) {
        try {
          var hashPath = window.__xcNormalizeTabPath((location.hash.replace('#', '').split('?')[0] || path));
          window.__xcRenderTabPath(hashPath || path);
        } catch(e) { console.warn('[patch v25] __switchTabPageDom error:', e); }
      };
      window.addEventListener('hashchange', function() {
        window.__switchTabPageDom && window.__switchTabPageDom();
      });
    }
    window.__xcTabRenderVersionRef.value;
    var hashPath = (function() {
      try {
        var h = location.hash.replace('#', '').split('?')[0];
        if (!h || h === '/' || h === '/pages/index/index') return '/';
        return h;
      } catch(_e) {
        return '/';
      }
    })();
    var activeRoute = null;
    var routes = __uniRoutes || [];
    for (var i = 0; i < routes.length; i++) {
      if (routes[i].path === hashPath && routes[i].meta && routes[i].meta.isTabBar) {
        activeRoute = routes[i];
        break;
      }
    }
    if (activeRoute) {
      var tabChildren = routes.filter(function(r) {
        return r.meta && r.meta.isTabBar;
      }).map(function(route) {
        var pageKey = 'tabBar$$' + route.path;
        var isActive = route.path === activeRoute.path;
        return createVNode('div', {
          class: 'tab-page-wrapper',
          'data-tab-path': route.path,
          style: isActive ? '' : 'display:none'
        }, [
          createVNode(KeepAlive, { matchBy: 'key', cache: routeCache2 }, [
            createVNode(route.component, { type: 'tabBar', key: pageKey })
          ], 1032, ['cache'])
        ]);
      });
      return createVNode('div', { class: 'tab-pages-container' }, tabChildren);
    }
  }
  return createVNode(RouterView, null, {
    default: withCtx(({
      Component
    }) => [(openBlock(), createBlock(KeepAlive, {
      matchBy: "key",
      cache: routeCache2
    }, [(openBlock(), createBlock(resolveDynamicComponent(Component), {
      type: isTabBar.value ? "tabBar" : "",
      key: routeKey.value
    }))], 1032, ["cache"]))]),
    _: 1
    /* STABLE */
  });
}`

const nextContent = replaceFunction(content, 'createRouterViewVNode', createRouterViewVNode)
if (nextContent) {
  content = nextContent
  patchCount++
  console.log('[OK] createRouterViewVNode patched (v25 all tab render)')
} else {
  failCount++
  console.log('[WARN] createRouterViewVNode not found')
}

const orphanStart = content.indexOf('}) {\n  // PATCHED v20f: hash guard for initial-load isTabBar stale value bug')
if (orphanStart >= 0) {
  const keepBrace = content.substring(0, orphanStart + 1)
  const orphanEnd = content.indexOf('\nfunction useTopWindow', orphanStart)
  if (orphanEnd >= 0) {
    content = keepBrace + content.substring(orphanEnd)
    patchCount++
    console.log('[OK] removed stale createRouterViewVNode fragment')
  } else {
    failCount++
    console.log('[WARN] stale createRouterViewVNode fragment found but end marker missing')
  }
}

const oldReLaunchPatch = `// PATCHED v20e: For reLaunch/redirectTo, always full page reload
      // This fixes both: non-tabBar -> tabBar and tabBar -> non-tabBar transitions
      if (type === "reLaunch" || type === "redirectTo") {
        window.location.hash = router.currentRoute.value.fullPath || router.currentRoute.value.path;
        window.location.reload();
        return resolve();
      }`

const newReLaunchPatch = `// PATCHED v23: For reLaunch/redirectTo, always full page reload
      // FIX: use target path (from parseUrl) instead of router.currentRoute.value
      if (type === "reLaunch" || type === "redirectTo") {
        var _targetHash = path;
        if (query && Object.keys(query).length > 0) {
          var _qp = Object.keys(query).map(function(k) { return k + '=' + encodeURIComponent(query[k]); });
          _targetHash += '?' + _qp.join('&');
        }
        window.location.hash = _targetHash;
        window.location.reload();
        return resolve();
      }`

if (content.indexOf('PATCHED v25: For reLaunch/redirectTo') >= 0) {
  patchCount++
  console.log('[OK] reLaunch/redirectTo already patched (v25)')
} else if (content.indexOf('PATCHED v24: For reLaunch/redirectTo') >= 0) {
  content = content.replace('PATCHED v24: For reLaunch/redirectTo', 'PATCHED v25: For reLaunch/redirectTo')
  patchCount++
  console.log('[OK] reLaunch/redirectTo marker upgraded (v25)')
} else if (content.indexOf('PATCHED v23: For reLaunch/redirectTo') >= 0) {
  content = content.replace('PATCHED v23: For reLaunch/redirectTo', 'PATCHED v25: For reLaunch/redirectTo')
  patchCount++
  console.log('[OK] reLaunch/redirectTo marker upgraded (v25)')
} else if (content.indexOf('PATCHED v20f: For reLaunch/redirectTo') >= 0) {
  content = content.replace('PATCHED v20f: For reLaunch/redirectTo', 'PATCHED v25: For reLaunch/redirectTo')
  patchCount++
  console.log('[OK] reLaunch/redirectTo marker upgraded (v25)')
} else if (content.indexOf(oldReLaunchPatch) >= 0) {
  content = content.replace(oldReLaunchPatch, newReLaunchPatch)
  patchCount++
  console.log('[OK] reLaunch/redirectTo patched (v25)')
} else {
  console.log('[INFO] reLaunch/redirectTo legacy patch point not present; handled by hash renderer')
}

const staleSwitchCall = 'window.__switchTabPageDom && window.__switchTabPageDom(router.currentRoute.value.path);'
const targetSwitchCall = 'window.__switchTabPageDom && window.__switchTabPageDom(path);'
if (content.indexOf(targetSwitchCall) >= 0) {
  patchCount++
  console.log('[OK] switchTab target path call already patched')
} else if (content.indexOf(staleSwitchCall) >= 0) {
  content = content.replace(staleSwitchCall, targetSwitchCall)
  patchCount++
  console.log('[OK] switchTab target path call patched')
} else {
  console.log('[INFO] switchTab legacy call point not present; handled by hash renderer')
}

console.log('[INFO] __switchTabPageDom handled inside createRouterViewVNode')

fs.writeFileSync(fp, content, 'utf8')

if (failCount === 0) {
  console.log('Patch v25 applied successfully! (' + patchCount + ' modifications)')
} else {
  console.log('Patch v25 partially applied with ' + failCount + ' warnings. (' + patchCount + ' OK)')
  process.exitCode = 1
}
