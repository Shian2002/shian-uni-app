/**
 * Patch v20f — Fix ALL navigation in H5 hash mode
 *
 * 根因: Vue 3.4.21 render effect 不追踪 routeKey/isTabBar 依赖,
 * 导致 navigateTo/reLaunch/switchTab 后 DOM 不更新或渲染错误页面.
 *
 * v20f 策略: reLaunch/redirectTo 用目标 path 设 hash + 全页刷新.
 *   1. createRouterViewVNode → v20d hash guard: isTabBar.value=true 时
 *      额外校验 hash 是否真的是 tabBar 页面, 防止初始加载误判.
 *   2. reLaunch/redirectTo → 用目标 path 设 hash + 全页刷新 (v20f),
 *      修复 v20e bug: 误用 router.currentRoute.value (仍是旧路由).
 *   3. __switchTabPageDom → 保留用于 switchTab (tabBar 页面间 CSS 切换).
 */

const fs = require('fs');
const fp = 'node_modules/@dcloudio/uni-h5/dist/uni-h5.es.js';
let content = fs.readFileSync(fp, 'utf8');

let patchCount = 0;
let failCount = 0;

// =======================================================================
// 1. Patch createRouterViewVNode — v20d hash guard
// =======================================================================

// 检查是否已 patch v20f
if (content.indexOf('PATCHED v20f') >= 0) {
  patchCount++;
  console.log('[OK] createRouterViewVNode already patched (v20f)');
} else if (content.indexOf('PATCHED v20d') >= 0 || content.indexOf('PATCHED v20b') >= 0 || content.indexOf('PATCHED v19') >= 0) {
  // 需要升级 — 先找到 createRouterViewVNode 函数并替换
  // 由于函数体可能已被多次 patch, 我们用更灵活的方式
  const funcStart = content.indexOf('function createRouterViewVNode({');
  if (funcStart >= 0) {
    // 找到函数结束位置 (下一个 function 关键字或文件结束)
    let funcEnd = content.indexOf('\nfunction ', funcStart + 50);
    if (funcEnd < 0) funcEnd = content.length;

    const newFunc = `function createRouterViewVNode({
  routeKey,
  isTabBar,
  routeCache: routeCache2
}) {
  // PATCHED v20f: hash guard for initial-load isTabBar stale value bug
  // FIX: map /pages/index/index -> / for homepage alias (uni-app routes homepage as '/')
  // Cloud-inject safe: no const/arrow in map callback
  if (isTabBar.value) {
    var _isReallyTab = (function() {
      try {
        var _h = location.hash.replace('#', '');
        if (!_h) _h = '/';
        if (_h === '/pages/index/index') _h = '/';
        var _routes = __uniRoutes || [];
        for (var _ri = 0; _ri < _routes.length; _ri++) {
          if (_routes[_ri].path === _h) return !!(_routes[_ri].meta && _routes[_ri].meta.isTabBar);
        }
      } catch(_e) {}
      return false;
    })();
    if (_isReallyTab) {
      var _$getHashRoute = function() {
        try {
          var h = location.hash.replace('#', '');
          if (!h || h === '/') return { path: '/' };
          if (h === '/pages/index/index') return { path: '/' };
          var routes = __uniRoutes || [];
          for (var i = 0; i < routes.length; i++) {
            if (routes[i].path === h) return routes[i];
          }
        } catch(e) {}
        return null;
      };
      var SEP_ = '$$';
      var tabPages_ = __uniRoutes.filter(function(r) { return r.meta && r.meta.isTabBar; });
      var hashRoute_ = _$getHashRoute();
      var activePath_ = hashRoute_ ? hashRoute_.path : '/';
      var tabChildren = tabPages_.map(function(route) {
        var pageKey = 'tabBar' + SEP_ + route.path;
        var isActive = route.path === activePath_;
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
    // else: isTabBar.value=true but hash says non-tab -> fall through to RouterView
  }
  // Original RouterView path (non-tab pages + hash-guarded false positives)
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
}`;

    content = content.substring(0, funcStart) + newFunc + content.substring(funcEnd);
    patchCount++;
    console.log('[OK] createRouterViewVNode patched (v20f hash guard)');
  } else {
    failCount++;
    console.log('[WARN] createRouterViewVNode not found');
  }
} else {
  failCount++;
  console.log('[WARN] Unknown patch version in createRouterViewVNode, expected v20f or earlier');
}

// =======================================================================
// 2. Patch reLaunch/redirectTo — v20e always full page reload
// =======================================================================

const oldReLaunchPatch = `// PATCHED v20e: For reLaunch/redirectTo, always full page reload
      // This fixes both: non-tabBar -> tabBar and tabBar -> non-tabBar transitions
      if (type === "reLaunch" || type === "redirectTo") {
        window.location.hash = router.currentRoute.value.fullPath || router.currentRoute.value.path;
        window.location.reload();
        return resolve();
      }`;

const newReLaunchPatch = `// PATCHED v20f: For reLaunch/redirectTo, always full page reload
      // FIX: use target path (from parseUrl) instead of router.currentRoute.value
      // v20e bug: router.currentRoute may still be the OLD route after replace() for tabBar pages
      if (type === "reLaunch" || type === "redirectTo") {
        var _targetHash = path;
        if (query && Object.keys(query).length > 0) {
          var _qp = Object.keys(query).map(function(k) { return k + '=' + encodeURIComponent(query[k]); });
          _targetHash += '?' + _qp.join('&');
        }
        window.location.hash = _targetHash;
        window.location.reload();
        return resolve();
      }`;

if (content.indexOf('PATCHED v20f') >= 0) {
  patchCount++;
  console.log('[OK] reLaunch/redirectTo already patched (v20f)');
} else if (content.indexOf(oldReLaunchPatch) >= 0) {
  content = content.replace(oldReLaunchPatch, newReLaunchPatch);
  patchCount++;
  console.log('[OK] reLaunch/redirectTo patched (v20f always reload)');
} else {
  failCount++;
  console.log('[WARN] reLaunch/redirectTo patch pattern not found');
}

// =======================================================================
// 3. Patch __switchTabPageDom — keep for switchTab CSS switching
// =======================================================================

// 检查是否已有 v20b 的 __switchTabPageDom
if (content.indexOf('PATCHED v20b: __switchTabPageDom') >= 0) {
  patchCount++;
  console.log('[OK] __switchTabPageDom already patched (v20b)');
} else if (content.indexOf('PATCHED v19: __switchTabPageDom') >= 0) {
  // 需要升级 v19 -> v20b
  const v19Start = content.indexOf('// PATCHED v19: __switchTabPageDom');
  const v19End = content.indexOf('};', v19Start + 200) + 2;
  if (v19Start >= 0 && v19End > v19Start) {
    const newSwitchTab = `// PATCHED v20b: __switchTabPageDom - tab CSS switching + forceUpdate for non-tab
    window.__switchTabPageDom = function(path) {
      try {
        var tabPages = (__uniRoutes || []).filter(function(r) { return r.meta && r.meta.isTabBar; });
        var isTab = tabPages.some(function(r) { return r.path === path; });
        var tabContainer = document.querySelector('.tab-pages-container');

        if (isTab) {
          // ── Tab page: show the right tab wrapper ──
          if (tabContainer) {
            tabContainer.style.display = '';
            var wrappers = document.querySelectorAll('.tab-page-wrapper');
            wrappers.forEach(function(w) {
              var tabPath = w.getAttribute('data-tab-path');
              w.style.display = (tabPath === path) ? '' : 'none';
            });
          }
        } else {
          // ── Non-tab page: hide all tab pages ──
          if (tabContainer) tabContainer.style.display = 'none';
        }
      } catch(e) { console.warn('[patch v20b] __switchTabPageDom error:', e); }
    };`;
    content = content.substring(0, v19Start) + newSwitchTab + content.substring(v19End);
    patchCount++;
    console.log('[OK] __switchTabPageDom upgraded from v19 to v20b');
  } else {
    failCount++;
    console.log('[WARN] v19 __switchTabPageDom found but markers not located');
  }
} else {
  failCount++;
  console.log('[WARN] __switchTabPageDom patch not found');
}

// =======================================================================
// Write result
// =======================================================================

if (failCount === 0) {
  fs.writeFileSync(fp, content, 'utf8');
  console.log('Patch v20f applied successfully! (' + patchCount + ' modifications)');
} else {
  console.log('Patch v20f partially applied with ' + failCount + ' warnings. (' + patchCount + ' OK)');
  fs.writeFileSync(fp, content, 'utf8');
}
