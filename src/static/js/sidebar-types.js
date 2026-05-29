/**
 * 侧边栏共享数据 — TopNav.vue 和 sidebar.js 共用
 * 在 index.html 中通过 <script src="/static/js/sidebar-types.js"> 引入
 */
(function() {
  'use strict'
  if (window.__sidebarTypes) return
  var T = {
    TYPE_ORDER: ['qimen', 'paipan', 'bazi', 'liuyao', 'meihua', 'ziwei', 'taluo', 'tarot'],
    TYPE_META: {
      qimen: { icon: '🔮', label: '奇门遁甲' },
      paipan: { icon: '📜', label: '八字排盘' },
      bazi: { icon: '🤖', label: '八字AI解读' },
      liuyao: { icon: '🧭', label: '六爻排盘' },
      meihua: { icon: '🌸', label: '梅花易数' },
      ziwei: { icon: '⭐', label: '紫微斗数' },
      taluo: { icon: '🃏', label: '塔罗牌' },
      tarot: { icon: '🃏', label: '塔罗牌' }
    },

    groupRecords: function(records) {
      var groups = {}, seen = {}
      records.forEach(function(r) {
        var t = r.app_type || 'qimen'
        if (!groups[t]) groups[t] = []
        groups[t].push(r)
      })
      var result = []
      T.TYPE_ORDER.forEach(function(t) {
        if (groups[t]) {
          var meta = T.TYPE_META[t] || { icon: '🔮', label: t }
          var dedupKey = meta.label
          if (seen[dedupKey]) {
            seen[dedupKey].records = seen[dedupKey].records.concat(groups[t])
          } else {
            var entry = { type: t, icon: meta.icon, label: meta.label, records: groups[t] }
            result.push(entry)
            seen[dedupKey] = entry
          }
          delete groups[t]
        }
      })
      Object.keys(groups).forEach(function(t) {
        var meta = T.TYPE_META[t] || { icon: '🔮', label: t }
        result.push({ type: t, icon: meta.icon, label: meta.label, records: groups[t] })
      })
      return result
    },

    escHtml: function(s) {
      if (!s || typeof s !== 'string') return ''
      var d = document.createElement('div')
      d.appendChild(document.createTextNode(s))
      return d.innerHTML
    }
  }
  window.__sidebarTypes = T
})()
