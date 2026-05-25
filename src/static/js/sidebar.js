/**
 * 通用历史记录侧边栏 — 独立加载，不依赖 uni-app 编译
 * 在 index.html 中通过 <script src="/static/js/sidebar.js"> 引入
 *
 * 使用全局 DOM（tarotSidebarGlobal），挂载在 document.body 上，
 * 不受 uni-app custom tabBar 多实例影响。
 */
(function() {
  'use strict'

  if (window.__sidebarLoaded) return
  window.__sidebarLoaded = true

  // 按 app_type 分组（处理后端值不一致）
  var TYPE_ORDER = ['qimen', 'paipan', 'bazi', 'liuyao', 'meihua', 'ziwei', 'taluo', 'tarot']
  var TYPE_META = {
    qimen: { icon: '🔮', label: '奇门遁甲' }, paipan: { icon: '📜', label: '八字排盘' }, bazi: { icon: '📜', label: '八字排盘' },
    liuyao: { icon: '🧭', label: '六爻排盘' }, meihua: { icon: '🌸', label: '梅花易数' }, ziwei: { icon: '⭐', label: '紫微斗数' },
    taluo: { icon: '🃏', label: '塔罗牌' }, tarot: { icon: '🃏', label: '塔罗牌' }
  }
  function groupRecords(records) {
    var groups = {}, seen = {}
    records.forEach(function(r) {
      var t = r.app_type || 'qimen'
      if (!groups[t]) groups[t] = []
      groups[t].push(r)
    })
    var result = []
    TYPE_ORDER.forEach(function(t) {
      if (groups[t]) {
        var meta = TYPE_META[t] || { icon: '🔮', label: t }
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
      var meta = TYPE_META[t] || { icon: '🔮', label: t }
      result.push({ type: t, icon: meta.icon, label: meta.label, records: groups[t] })
    })
    return result
  }

  // ── 确保全局侧边栏 DOM 存在（仅创建一次） ──
  function ensureGlobalSidebar() {
    if (document.getElementById('tarotSidebarGlobal')) return

    var overlay = document.createElement('div')
    overlay.className = 'sidebar-overlay'
    overlay.id = 'sidebarOverlayGlobal'
    overlay.onclick = function() { window._xc_toggleSidebar() }

    var sidebar = document.createElement('div')
    sidebar.className = 'tarot-sidebar'
    sidebar.id = 'tarotSidebarGlobal'
    sidebar.innerHTML = '<div class="sidebar-brand"><span class="sidebar-brand-icon-wrap"><img class="sidebar-brand-icon" src="/static/images/logo.png"></span><span class="sidebar-brand-name">时安解忧屋</span></div>'
      + '<div class="sidebar-header"><span class="sidebar-title">对话历史</span><div class="sidebar-close" id="sidebarCloseGlobal">✕</div></div>'
      + '<div class="sidebar-content" id="sidebarListGlobal"><div class="sidebar-empty">加载中...</div></div>'
      + '<div class="sidebar-user-panel" id="sidebarUserPanel">'
      + '<div class="sidebar-user-logged" id="sidebarUserLogged" style="display:none;">'
      + '<div class="sidebar-user-avatar-wrap"><img class="sidebar-user-avatar" id="sidebarUserAvatar" src=""><span class="sidebar-user-avatar-letter" id="sidebarUserLetter">U</span></div>'
      + '<div class="sidebar-user-info"><span class="sidebar-user-name" id="sidebarUserName">用户</span><span class="sidebar-user-points" id="sidebarUserPoints">积分: --</span></div>'
      + '<div class="sidebar-user-actions"><span class="sidebar-user-setting" id="sidebarUserSetting">⚙</span><span class="sidebar-user-logout" id="sidebarUserLogout">退出</span></div>'
      + '</div>'
      + '<div class="sidebar-user-guest" id="sidebarUserGuest" style="display:none;">'
      + '<span class="sidebar-guest-text">登录后可同步历史记录</span>'
      + '<span class="sidebar-guest-btn" id="sidebarGuestLogin">登录</span>'
      + '</div>'
      + '</div>'
    sidebar.querySelector('#sidebarCloseGlobal').onclick = function() { window._xc_toggleSidebar() }
    sidebar.querySelector('#sidebarUserSetting').onclick = function() { window._xc_toggleSidebar(); if (window.__topNavGo) window.__topNavGo('#/pages/profile/index') }
    sidebar.querySelector('#sidebarUserLogout').onclick = function() { if (window._xc_doLogout) window._xc_doLogout() }
    sidebar.querySelector('#sidebarGuestLogin').onclick = function() { if (window._openLoginModal) window._openLoginModal() }

    var detailOverlay = document.createElement('div')
    detailOverlay.className = 'modal-overlay'
    detailOverlay.id = 'historyDetailOverlayGlobal'
    detailOverlay.onclick = function(e) { if (e.target === detailOverlay) window._closeHistoryDetail() }
    detailOverlay.innerHTML = '<div class="modal-box history-detail-box" onclick="event.stopPropagation()">'
      + '<div class="modal-title" id="historyDetailTitle">历史记录</div>'
      + '<div class="history-detail-content" id="historyDetailContent"></div>'
      + '<div class="modal-btns"><div class="btn btn-outline" onclick="window._closeHistoryDetail()">关闭</div></div></div>'

    document.body.appendChild(overlay)
    document.body.appendChild(sidebar)
    document.body.appendChild(detailOverlay)
  }

  // 折叠/展开分组
  window._xc_toggleGroup = function(headerEl) {
    var g = headerEl.parentElement
    if (g) g.classList.toggle('collapsed')
  }

  // 加载用户面板
  function loadUserPanel() {
    var loggedEl = document.getElementById('sidebarUserLogged')
    var guestEl = document.getElementById('sidebarUserGuest')
    if (!loggedEl || !guestEl) return

    function setGuest() { guestEl.style.display = 'flex'; loggedEl.style.display = 'none' }
    function setLogged(name, avatar) {
      loggedEl.style.display = 'flex'; guestEl.style.display = 'none'
      document.getElementById('sidebarUserName').textContent = name
      var letterEl = document.getElementById('sidebarUserLetter')
      if (letterEl) letterEl.textContent = name.charAt(0).toUpperCase()
      if (avatar) {
        var img = document.getElementById('sidebarUserAvatar')
        if (img) { img.src = avatar; img.style.display = 'block' }
        if (letterEl) letterEl.style.display = 'none'
      }
    }

    var xhr = new XMLHttpRequest()
    xhr.open('GET', '/api/me')
    xhr.onload = function() {
      try {
        var d = JSON.parse(xhr.responseText)
        if (d && d.guest) { setGuest(); return }
        if (d && d.username) { setLogged(d.username, d.avatar || ''); return }
        setGuest()
      } catch(e) { setGuest() }
    }
    xhr.onerror = function() { setGuest() }
    xhr.send()

    var xhr2 = new XMLHttpRequest()
    xhr2.open('GET', '/api/membership')
    xhr2.onload = function() {
      try {
        var d = JSON.parse(xhr2.responseText)
        if (d && typeof d.points === 'number') {
          var el = document.getElementById('sidebarUserPoints')
          if (el) el.textContent = '积分: ' + d.points
        }
      } catch(e) {}
    }
    xhr2.send()
  }

  // ═══ 开/关侧边栏 + 加载历史 ═══
  window._xc_toggleSidebar = function() {
    ensureGlobalSidebar()
    var sidebar = document.getElementById('tarotSidebarGlobal')
    var overlay = document.getElementById('sidebarOverlayGlobal')
    if (!sidebar || !overlay) return

    if (sidebar.classList.contains('open')) {
      sidebar.classList.remove('open')
      overlay.classList.remove('show')
      document.body.removeEventListener('click', window.__sidebarClickAway)
      return
    }

    sidebar.classList.add('open')
    overlay.classList.add('show')

    document.body.removeEventListener('click', window.__sidebarClickAway)
    window.__sidebarClickAway = function(e) {
      var s = document.getElementById('tarotSidebarGlobal')
      if (s && s.classList.contains('open') && !s.contains(e.target)) {
        e.stopPropagation()
        s.classList.remove('open')
        document.getElementById('sidebarOverlayGlobal').classList.remove('show')
        document.body.removeEventListener('click', window.__sidebarClickAway)
      }
    }
    setTimeout(function() {
      document.body.addEventListener('click', window.__sidebarClickAway)
    }, 200)

    // 加载用户面板
    loadUserPanel()

    // 加载分组历史记录
    var listEl = document.getElementById('sidebarListGlobal')
    if (!listEl) return
    listEl.innerHTML = '<div class="sidebar-empty">加载中...</div>'

    var xhr = new XMLHttpRequest()
    xhr.open('GET', '/api/records?per_page=50')
    xhr.setRequestHeader('Accept', 'application/json')
    xhr.onload = function() {
      if (xhr.status !== 200) {
        listEl.innerHTML = '<div class="sidebar-empty">加载失败</div>'
        return
      }
      try {
        var data = JSON.parse(xhr.responseText)
        var items = data.records || []
        // 合并塔罗对话
        var tarotXhr = new XMLHttpRequest()
        tarotXhr.open('GET', '/api/tarot/conversations')
        tarotXhr.setRequestHeader('Accept', 'application/json')
        tarotXhr.onload = function() {
          var tarotItems = []
          try { tarotItems = JSON.parse(tarotXhr.responseText); if (!Array.isArray(tarotItems)) tarotItems = [] } catch(e) {}
          tarotItems.forEach(function(c) {
            items.push({ id: 'tarot_' + c.id, app_type: 'tarot', question: c.title || c.spread_name || '塔罗解读', created_at: c.updated_at || c.created_at, _tarotConvId: c.id })
          })
          if (!items.length) { listEl.innerHTML = '<div class="sidebar-empty">暂无历史记录</div>'; return }
          var groups = groupRecords(items)
          var html = ''
          groups.forEach(function(g) {
            html += '<div class="sidebar-group" data-type="' + g.type + '">'
              + '<div class="sidebar-group-header" onclick="window._xc_toggleGroup(this)">'
              + '<span class="sidebar-group-icon">' + g.icon + '</span>'
              + '<span class="sidebar-group-label">' + g.label + '</span>'
              + '<span class="sidebar-group-count">' + g.records.length + '</span>'
              + '<span class="sidebar-group-arrow">▾</span>'
              + '</div><div class="sidebar-group-items">'
            g.records.forEach(function(r) {
              var time = r.created_at ? r.created_at.substring(0, 16).replace('T', ' ') : ''
              var clickAction = r._tarotConvId
                ? 'onclick="window._showTarotConv(' + r._tarotConvId + ')"'
                : 'onclick="window._showHistoryDetail(' + r.id + ')"'
              html += '<div class="sidebar-item" ' + clickAction + '>'
                + '<div class="sidebar-item-body">'
                + '<span class="sidebar-item-text">' + (r.question || '(无问题)') + '</span>'
                + '<span class="sidebar-item-time">' + time + '</span>'
                + '</div></div>'
            })
            html += '</div></div>'
          })
          listEl.innerHTML = html
        }
        tarotXhr.onerror = function() {
          // 塔罗加载失败，仍显示 records
          if (!items.length) { listEl.innerHTML = '<div class="sidebar-empty">暂无历史记录</div>'; return }
          var groups = groupRecords(items)
          var html = ''
          groups.forEach(function(g) {
            html += '<div class="sidebar-group" data-type="' + g.type + '">'
              + '<div class="sidebar-group-header" onclick="window._xc_toggleGroup(this)">'
              + '<span class="sidebar-group-icon">' + g.icon + '</span>'
              + '<span class="sidebar-group-label">' + g.label + '</span>'
              + '<span class="sidebar-group-count">' + g.records.length + '</span>'
              + '<span class="sidebar-group-arrow">▾</span>'
              + '</div><div class="sidebar-group-items">'
            g.records.forEach(function(r) {
              var time = r.created_at ? r.created_at.substring(0, 16).replace('T', ' ') : ''
              html += '<div class="sidebar-item" onclick="window._showHistoryDetail(' + r.id + ')">'
                + '<div class="sidebar-item-body">'
                + '<span class="sidebar-item-text">' + (r.question || '(无问题)') + '</span>'
                + '<span class="sidebar-item-time">' + time + '</span>'
                + '</div></div>'
            })
            html += '</div></div>'
          })
          listEl.innerHTML = html
        }
        tarotXhr.send()
      } catch(e) {
        listEl.innerHTML = '<div class="sidebar-empty">解析失败</div>'
      }
    }
    xhr.onerror = function() {
      listEl.innerHTML = '<div class="sidebar-empty">网络错误</div>'
    }
    xhr.send()
  }

  // ═══ 查看塔罗对话 ═══
  window._showTarotConv = function(cid) {
    var xhr = new XMLHttpRequest()
    xhr.open('GET', '/api/tarot/conversations/' + cid)
    xhr.setRequestHeader('Accept', 'application/json')
    xhr.onload = function() {
      if (xhr.status !== 200) return
      try {
        var d = JSON.parse(xhr.responseText)
        if (!d) return
        var overlay = document.getElementById('historyDetailOverlayGlobal')
        var title = document.getElementById('historyDetailTitle')
        var content = document.getElementById('historyDetailContent')
        if (overlay) overlay.classList.add('open')
        if (title) title.textContent = d.title || d.spread_name || '塔罗解读'
        var msgs = []
        try { msgs = JSON.parse(d.messages_json || '[]') } catch(_) {}
        var aiMsgs = msgs.filter(function(m) { return m.role === 'assistant' })
        var lastMsg = aiMsgs.length ? aiMsgs[aiMsgs.length - 1].content : ''
        if (content) content.innerHTML = '<div class="history-markdown">' + (lastMsg || '无解读内容') + '</div>'
        window._xc_toggleSidebar()
      } catch(e) {}
    }
    xhr.send()
  }

  // ═══ 查看历史详情 ═══
  window._showHistoryDetail = function(rid) {
    var xhr = new XMLHttpRequest()
    xhr.open('GET', '/api/records/' + rid)
    xhr.setRequestHeader('Accept', 'application/json')
    xhr.onload = function() {
      if (xhr.status !== 200) return
      try {
        var d = JSON.parse(xhr.responseText)
        var overlay = document.getElementById('historyDetailOverlayGlobal')
        var title = document.getElementById('historyDetailTitle')
        var content = document.getElementById('historyDetailContent')
        if (overlay) overlay.classList.add('open')
        if (title) title.textContent = d.question || '历史记录'
        if (content) content.innerHTML = '<div class="history-markdown">' + (d.result_html || '') + '</div>'
        window._xc_toggleSidebar()
      } catch(e) {}
    }
    xhr.send()
  }

  // ═══ 关闭详情弹窗 ═══
  window._closeHistoryDetail = function() {
    var overlay = document.getElementById('historyDetailOverlayGlobal')
    if (overlay) overlay.classList.remove('open')
  }

  console.log('[sidebar] 历史记录侧边栏已就绪')
})()
