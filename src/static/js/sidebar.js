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

  // 从共享模块获取分组数据和工具函数
  var ST = window.__sidebarTypes
  var groupRecords = ST.groupRecords
  var escHtml = ST.escHtml

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

  // 渲染分组历史（共享函数）
  function renderSidebarGroups(groups, listEl) {
    var h = ''
    groups.forEach(function(g) {
      h += '<div class="sidebar-group" data-type="' + g.type + '">'
        + '<div class="sidebar-group-header" onclick="window._xc_toggleGroup(this)">'
        + '<span class="sidebar-group-icon">' + g.icon + '</span>'
        + '<span class="sidebar-group-label">' + g.label + '</span>'
        + '<span class="sidebar-group-count">' + g.records.length + '</span>'
        + '<span class="sidebar-group-arrow">▾</span>'
        + '</div><div class="sidebar-group-items">'
      g.records.forEach(function(r) {
        var time = r.created_at ? r.created_at.substring(0, 16).replace('T', ' ') : ''
        var text = escHtml(r.question || '(无问题)')
        var clickAction = r._tarotConvId
          ? 'onclick="window._showTarotConv(' + r._tarotConvId + ')"'
          : r._baziConvId
          ? 'onclick="window._showBaziConvDetail(' + r._baziConvId + ')"'
          : r.id && String(r.id).indexOf('bazih_') === 0
          ? 'onclick="window._showBaziRecordDetail(' + parseInt(r.id.replace('bazih_', '')) + ')"'
          : 'onclick="window._showHistoryDetail(' + r.id + ')"'
        h += '<div class="sidebar-item" ' + clickAction + '>'
          + '<div class="sidebar-item-body">'
          + '<span class="sidebar-item-text">' + text + '</span>'
          + '<span class="sidebar-item-time">' + time + '</span>'
          + '</div></div>'
      })
      h += '</div></div>'
    })
    listEl.innerHTML = h
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

    // 加载分组历史记录（30 秒内缓存）
    var listEl = document.getElementById('sidebarListGlobal')
    if (!listEl) return
    var now = Date.now()
    if (window.__sidebarCache && (now - window.__sidebarCache.ts) < 30000) {
      renderSidebarGroups(window.__sidebarCache.groups, listEl)
      return
    }
    listEl.innerHTML = '<div class="sidebar-empty">加载中...</div>'
    loadSidebarData()
  }

  // ═══ 加载侧边栏数据（可被刷新函数复用） ═══
  function loadSidebarData() {
    var listEl = document.getElementById('sidebarListGlobal')
    if (!listEl) return

    var xhr = new XMLHttpRequest()
    xhr.open('GET', '/api/records?per_page=50')
    xhr.setRequestHeader('Accept', 'application/json')
    xhr.onload = function() {
      if (xhr.status !== 200) { listEl.innerHTML = '<div class="sidebar-empty">加载失败</div>'; return }
      try {
        var data = JSON.parse(xhr.responseText)
        var items = data.records || []
        var pending = 3
        function onAllDone() {
          pending--
          if (pending > 0) return
          if (!items.length) { listEl.innerHTML = '<div class="sidebar-empty">暂无历史记录</div>'; return }
          var groups = groupRecords(items)
          window.__sidebarCache = { ts: Date.now(), groups: groups }
          renderSidebarGroups(groups, listEl)
        }
        var tarotXhr = new XMLHttpRequest()
        tarotXhr.open('GET', '/api/tarot/conversations')
        tarotXhr.setRequestHeader('Accept', 'application/json')
        tarotXhr.onload = function() {
          var t = []
          try { t = JSON.parse(tarotXhr.responseText); if (!Array.isArray(t)) t = [] } catch(e) {}
          t.forEach(function(c) { items.push({ id: 'tarot_' + c.id, app_type: 'tarot', question: c.title || c.spread_name || '塔罗解读', created_at: c.updated_at || c.created_at, _tarotConvId: c.id }) })
          onAllDone()
        }
        tarotXhr.onerror = function() { onAllDone() }
        tarotXhr.send()
        var baziXhr = new XMLHttpRequest()
        baziXhr.open('GET', '/api/bazi/conversations')
        baziXhr.setRequestHeader('Accept', 'application/json')
        baziXhr.onload = function() {
          var b = []
          try { b = JSON.parse(baziXhr.responseText); if (!Array.isArray(b)) b = [] } catch(e) {}
          b.forEach(function(c) { items.push({ id: 'bazi_' + c.id, app_type: 'bazi', question: c.title || '八字AI解读', created_at: c.updated_at || c.created_at, _baziConvId: c.id }) })
          onAllDone()
        }
        baziXhr.onerror = function() { onAllDone() }
        baziXhr.send()
        var baziHxhr = new XMLHttpRequest()
        baziHxhr.open('GET', '/api/bazi/history')
        baziHxhr.setRequestHeader('Accept', 'application/json')
        baziHxhr.onload = function() {
          var bh = []
          try { bh = JSON.parse(baziHxhr.responseText); if (!Array.isArray(bh)) bh = [] } catch(e) {}
          bh.forEach(function(r) {
            var label = (r.name || '').trim() || '匿名'
            var pillarStr = (r.pillars || '').trim() ? ' [' + r.pillars + ']' : ''
            var birthStr = (r.birth_time || '').substring(0, 12)
            items.push({ id: 'bazih_' + r.id, app_type: 'paipan', question: label + ' ' + birthStr + pillarStr, created_at: r.created_at })
          })
          onAllDone()
        }
        baziHxhr.onerror = function() { onAllDone() }
        baziHxhr.send()
      } catch(e) { listEl.innerHTML = '<div class="sidebar-empty">解析失败</div>' }
    }
    xhr.onerror = function() { listEl.innerHTML = '<div class="sidebar-empty">网络错误</div>' }
    xhr.send()
  }

  // ═══ 强制刷新侧边栏（外部调用） ═══
  window._xc_refreshSidebar = function() {
    window.__sidebarCache = null
    ensureGlobalSidebar()
    loadSidebarData()
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
        if (content) content.innerHTML = '<div class="history-markdown">' + escHtml(lastMsg || '无解读内容') + '</div>'
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
