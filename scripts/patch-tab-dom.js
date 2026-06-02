/**
 * Patch v24 - visited tab page rendering for H5 hash mode.
 *
 * uni-app H5 的 tabBar 默认会把所有 tab 页面同时挂载。这个项目有顶部
 * 导航、登录弹窗和多个重型排盘页，如果首页一次性挂 13 个 tab 页面，
 * 桌面端切换时会明显卡顿。这里改为只渲染当前 tab 页面。
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
  // PATCHED v24: render visited tab pages instead of mounting every tab page.
  if (isTabBar.value) {
    if (!window.__xcTabRenderVersionRef) window.__xcTabRenderVersionRef = ref(0);
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
      if (!window.__xcVisitedTabPaths) window.__xcVisitedTabPaths = [];
      if (window.__xcVisitedTabPaths.indexOf(activeRoute.path) < 0) window.__xcVisitedTabPaths.push(activeRoute.path);
      var visited = window.__xcVisitedTabPaths;
      var tabChildren = routes.filter(function(r) {
        return r.meta && r.meta.isTabBar && visited.indexOf(r.path) >= 0;
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
  console.log('[OK] createRouterViewVNode patched (v24 visited tab render)')
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

if (content.indexOf('PATCHED v24: For reLaunch/redirectTo') >= 0) {
  patchCount++
  console.log('[OK] reLaunch/redirectTo already patched (v24)')
} else if (content.indexOf('PATCHED v23: For reLaunch/redirectTo') >= 0) {
  content = content.replace('PATCHED v23: For reLaunch/redirectTo', 'PATCHED v24: For reLaunch/redirectTo')
  patchCount++
  console.log('[OK] reLaunch/redirectTo marker upgraded (v24)')
} else if (content.indexOf('PATCHED v20f: For reLaunch/redirectTo') >= 0) {
  content = content.replace('PATCHED v20f: For reLaunch/redirectTo', 'PATCHED v24: For reLaunch/redirectTo')
  patchCount++
  console.log('[OK] reLaunch/redirectTo marker upgraded (v24)')
} else if (content.indexOf(oldReLaunchPatch) >= 0) {
  content = content.replace(oldReLaunchPatch, newReLaunchPatch)
  patchCount++
  console.log('[OK] reLaunch/redirectTo patched (v24)')
} else {
  failCount++
  console.log('[WARN] reLaunch/redirectTo patch pattern not found')
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
  failCount++
  console.log('[WARN] switchTab target path call pattern not found')
}

const switchTabPatch = `// PATCHED v24: __switchTabPageDom - active tab is rendered reactively.
    window.__xcRenderTabPath = function(path) {
      try {
        if (!path || path === '/pages/index/index') path = '/';
        if (!window.__xcVisitedTabPaths) window.__xcVisitedTabPaths = [];
        if (window.__xcVisitedTabPaths.indexOf(path) < 0) window.__xcVisitedTabPaths.push(path);
        var currentHash = (location.hash.replace('#', '').split('?')[0] || '/');
        if (currentHash === '/pages/index/index') currentHash = '/';
        if (currentHash !== path) window.location.hash = path;
        if (window.__xcTabRenderVersionRef) window.__xcTabRenderVersionRef.value++;
      } catch(e) { console.warn('[patch v24] __xcRenderTabPath error:', e); }
    };
    window.__switchTabPageDom = function(path) {
      try {
        var hashPath = (function() {
          try {
            var h = location.hash.replace('#', '').split('?')[0];
            if (!h || h === '/' || h === '/pages/index/index') return '/';
            return h;
          } catch(_e) {
            return path;
          }
        })();
        if (hashPath) path = hashPath;
        var tabPages = (__uniRoutes || []).filter(function(r) { return r.meta && r.meta.isTabBar; });
        var isTab = tabPages.some(function(r) { return r.path === path; });
        var tabContainer = document.querySelector('.tab-pages-container');

        if (!isTab) {
          if (tabContainer) tabContainer.style.display = 'none';
          return;
        }

        if (tabContainer) tabContainer.style.display = '';
        var wrappers = Array.prototype.slice.call(document.querySelectorAll('.tab-page-wrapper'));
        var target = wrappers.find(function(w) { return w.getAttribute('data-tab-path') === path; });
        if (target) {
          wrappers.forEach(function(w) {
            w.style.display = w === target ? '' : 'none';
          });
          return;
        }

        if (window.__xcRenderTabPath) window.__xcRenderTabPath(path);
      } catch(e) { console.warn('[patch v24] __switchTabPageDom error:', e); }
    };`

const switchMarker = 'window.__switchTabPageDom = function(path)'
const switchStart = content.indexOf(switchMarker)
if (switchStart >= 0) {
  const commentStart = content.lastIndexOf('// PATCHED', switchStart)
  const end = content.indexOf('    };', switchStart)
  if (commentStart >= 0 && end > switchStart) {
    content = content.substring(0, commentStart) + switchTabPatch + content.substring(end + '    };'.length)
    patchCount++
    console.log('[OK] __switchTabPageDom patched (v24)')
  } else {
    failCount++
    console.log('[WARN] __switchTabPageDom markers not found')
  }
} else {
  failCount++
  console.log('[WARN] __switchTabPageDom patch point not found')
}

fs.writeFileSync(fp, content, 'utf8')

if (failCount === 0) {
  console.log('Patch v24 applied successfully! (' + patchCount + ' modifications)')
} else {
  console.log('Patch v24 partially applied with ' + failCount + ' warnings. (' + patchCount + ' OK)')
  process.exitCode = 1
}
