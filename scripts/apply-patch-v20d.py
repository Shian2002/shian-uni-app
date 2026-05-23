#!/usr/bin/env python3
"""Patch v20d: Fix initial load of non-tabBar pages showing tab content.

Root cause: createRouterViewVNode only checks isTabBar.value (Vue computed).
On initial load of non-tabBar page, Vue Router may not have fully resolved,
so isTabBar.value is still true from previous/default state.

Fix: Also check location.hash as ground truth. Only enter tab branch when
BOTH isTabBar.value AND hash-based check agree the current route is a tab page.
"""

import os

# Resolve path relative to this script's location (scripts/ → parent = xuan-cet-tai/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SCRIPT_DIR)
fp = os.path.join(PROJECT_DIR, 'node_modules/@dcloudio/uni-h5/dist/uni-h5.es.js')
with open(fp, 'r') as f:
    content = f.read()

# Check current state
if 'PATCHED v20d' in content:
    print('OK: v20d already applied')
    exit(0)

if 'PATCHED v20c' not in content:
    print('ERROR: Expected v20c patch not found. Current markers:')
    for m in ['PATCHED v20', 'PATCHED v19', 'PATCHED v18']:
        if m in content:
            print(f'  Found: {m}')
    exit(1)

old_marker = '// ----- PATCHED v20c: Tab pages DOM cache for tabBar, original RouterView for non-tab -----'
end_marker = '// ----- END PATCHED v20c -----'

start_idx = content.find(old_marker)
end_idx = content.find(end_marker)

if start_idx < 0 or end_idx < 0:
    print(f'ERROR: Markers not found (start={start_idx}, end={end_idx})')
    exit(1)

new_func = '''function createRouterViewVNode({
  routeKey,
  isTabBar,
  routeCache: routeCache2
}) {
  // ----- PATCHED v20d: hash-based truth + isTabBar double-check -----
  // Root cause: on initial load of non-tabBar page (e.g. #/pages/liuyao/index),
  // Vue Router computed isTabBar may still be true (route not fully resolved).
  // Fix: use location.hash as ground truth — only enter tab branch when BOTH agree.
  var $$getHashRoute = function() {
    try {
      var h = location.hash.replace('#', '');
      if (!h || h === '/') return { path: '/', meta: {} };
      var routes = __uniRoutes || [];
      for (var i = 0; i < routes.length; i++) {
        if (routes[i].path === h) return routes[i];
      }
    } catch(e) {}
    return { path: '/', meta: {} };
  };
  var hashRoute = $$getHashRoute();
  var hashIsTabBar = hashRoute.meta && hashRoute.meta.isTabBar;
  const SEP = '$$';
  if (isTabBar.value && hashIsTabBar) {
    // BOTH agree this is a tab page → render all tabs (DOM cache)
    const tabPages = __uniRoutes.filter(r => r.meta && r.meta.isTabBar);
    const activePath = hashRoute.path;
    return createVNode('div', { class: 'tab-pages-container' },
      tabPages.map(route => {
        const pageKey = 'tabBar' + SEP + route.path;
        const isActive = route.path === activePath;
        return createVNode('div', {
          class: 'tab-page-wrapper',
          'data-tab-path': route.path,
          style: isActive ? '' : 'display:none',
        }, [
          createVNode(KeepAlive, { matchBy: 'key', cache: routeCache2 }, [
            createVNode(route.component, {
              type: 'tabBar',
              key: pageKey,
            })
          ], 1032, ['cache'])
        ];
      })
    );
  } else {
    // Non-tab page (isTabBar=false OR hash says non-tab) → use RouterView
    return createVNode(RouterView, null, {
      default: withCtx(({
        Component
      }) => [(openBlock(), createBlock(KeepAlive, {
        matchBy: "key",
        cache: routeCache2
      }, [(openBlock(), createBlock(resolveDynamicComponent(Component), {
        type: "",
        key: routeKey.value
      }))], 1032, ["cache"]))]),
      _: 1
      /* STABLE */
    });
  }
  // ----- END PATCHED v20d -----
}'''

# Replace from function declaration start to end marker
func_start = content.rfind('function createRouterViewVNode({', 0, start_idx)
if func_start < 0:
    print('ERROR: Could not find function start')
    exit(1)

# Find the closing brace after end_marker
after_end = end_idx + len(end_marker)
close_brace = content.find('}\n', after_end)
if close_brace < 0:
    close_brace = content.find('}\r\n', after_end)
if close_brace < 0:
    print('ERROR: Could not find closing brace')
    exit(1)
close_brace += 1  # include the }

content = content[:func_start] + new_func + content[close_brace+1:]

with open(fp, 'w') as f:
    f.write(content)

print('OK: Patch v20d applied successfully!')
print(f'  Replaced bytes {func_start}..{close_brace} ({close_brace - func_start} bytes -> {len(new_func)} bytes)')
