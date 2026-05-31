<template>
  <view class="topnav-wrap">
    <!-- 顶部固定导航 — 两行结构 -->
    <nav class="topnav topnav-solid">
      <!-- 单行：☰ + 按钮栏 + 右侧 -->
      <view class="topnav-sidebar-btn" id="topnavSidebarBtn" @click="toggleSidebar" @tap="toggleSidebar" onclick="window._xc_toggleSidebar()">☰</view>
      <view class="nav-btn-bar" id="navBtnBar">
        <view class="nav-btn" data-href="#/" @click="go('#/')">首页</view>

        <view class="nav-btn" data-href="#/pages/qimen/index?tab=free" onclick="window.__topNavGo('#/pages/qimen/index?tab=free')">奇门遁甲</view>

        <view class="nav-btn" data-href="#/pages/bazi-index/index?tab=free" onclick="window.__topNavGo('#/pages/bazi-index/index?tab=free')">八字排盘</view>

        <view class="nav-btn" data-href="#/pages/liuyao/index" @click="go('#/pages/liuyao/index')">六爻排盘</view>
        <view class="nav-btn" data-href="#/pages/meihua/index" @click="go('#/pages/meihua/index')">梅花易数</view>
        <view class="nav-btn" data-href="#/pages/ziwei/index" @click="go('#/pages/ziwei/index')">紫微斗数</view>
        <view class="nav-btn" data-href="#/pages/tarot/index" @click="go('#/pages/tarot/index')">塔罗牌</view>
        <view class="nav-btn" data-href="#/pages/zeji/index" @click="go('#/pages/zeji/index')">择吉工具</view>
        <view class="nav-btn" data-href="#/pages/calendar/index" @click="go('#/pages/calendar/index')">专属日历</view>
        <view class="nav-btn" data-href="#/pages/community/index" @click="go('#/pages/community/index')">社区</view>
        <view class="nav-btn" data-href="#/pages/about/index" @click="go('#/pages/about/index')">关于我们</view>

        <!-- 溢出"更多"按钮（JS 控制显示） -->
        <view class="nav-btn nav-btn-more" id="navBtnMore" style="display:none;" onclick="window._xc_toggleMore(event)">
          更多 ▾
          <view class="nav-btn-drop-menu" id="navBtnMoreMenu"></view>
        </view>
      </view>
      <view class="topnav-right">
        <view class="theme-toggle-nav" id="themeToggleBtn" data-action="auth" @click="onToggleTheme">
          <text id="themeToggleIcon">{{ theme === 'dark' ? '🌙' : '☀️' }}</text>
        </view>
        <view class="nav-auth-btns" v-if="!isLoggedIn">
          <view class="btn btn-outline btn-sm" onclick="window._openLoginModal()">登录</view>
        </view>
        <view class="nav-avatar-wrap" v-else>
           <view class="nav-avatar-trigger nav-avatar-trigger-global" id="avatarGlobalTrigger">
             <view class="nav-avatar-inner">
               <image v-if="avatarUrl" class="nav-avatar-img" :src="avatarUrl" mode="aspectFill" @error="onAvatarError"></image>
              <text v-else class="nav-avatar-text">{{ avatarLetter }}</text>
             </view>
           </view>
           <view class="nav-avatar-dropdown" id="avatarDropdown">
             <view class="avatar-dropdown-item points-display" id="avatarPointsDisplay">
               <text class="points-label">积分</text>
               <text class="points-badge" id="avatarPointsBadge">...</text>
             </view>
             <view class="avatar-dropdown-divider"></view>
             <view class="avatar-dropdown-item avatar-dropdown-action" data-href="#/pages/profile/index">个人中心 ›</view>
             <view class="avatar-dropdown-item avatar-dropdown-action" data-href="#/pages/points/index">积分中心 ›</view>
             <view class="avatar-dropdown-item avatar-dropdown-action admin-dropdown-item" id="avatarAdminEntry" data-href="#/pages/admin/index" style="display:none;">后台管理 ›</view>
             <view class="avatar-dropdown-divider"></view>
             <view class="avatar-dropdown-item avatar-dropdown-action" data-action="logout">退出登录</view>
           </view>
         </view>
      </view>
    </nav>
  </view>

  <!-- 登录弹窗 — 多Tab登录 -->
  <view class="modal-overlay" id="topnavLoginModal" onclick="if(event.target===this) window._openLoginModal_Close()">
    <view class="modal-box">
      <view class="modal-title">登录</view>
      <view class="login-tabs">
        <view class="login-tab tn-tab-password active" data-tab="password" onclick="window._xc_switchTab(this)">密码</view>
        <view class="login-tab tn-tab-phone" data-tab="phone" onclick="window._xc_switchTab(this)">手机</view>
        <view class="login-tab tn-tab-email" data-tab="email" onclick="window._xc_switchTab(this)">邮箱</view>
      </view>

      <!-- 密码登录 -->
      <view class="tn-panel tn-panel-password" style="">
        <view class="field"><text class="field-label">用户名/邮箱/手机号</text><view id="tnLoginUser-wrap" class="dom-input-wrap"></view></view>
        <view class="field"><text class="field-label">密码</text><view id="tnLoginPass-wrap" class="dom-input-wrap"></view></view>
        <view class="modal-hint">已有账号直接登录 · <text class="register-link" onclick="window._xc_doRegister()" style="color:var(--accent);cursor:pointer;text-decoration:underline;">没有账号？立即注册</text></view>
      </view>

      <!-- 手机验证码登录 -->
      <view class="tn-panel tn-panel-phone" style="display:none;">
        <view class="field"><text class="field-label">手机号</text><view id="tnLoginPhone-wrap" class="dom-input-wrap"></view></view>
        <view class="field code-field">
          <text class="field-label">验证码</text>
          <view style="display:flex;gap:8px;">
            <view id="tnLoginPhoneCode-wrap" class="dom-input-wrap" style="flex:1;"></view>
            <view class="btn btn-outline btn-sm code-btn" onclick="window._xc_sendPhoneCode()" id="tnPhoneCodeBtn">获取验证码</view>
          </view>
        </view>
      </view>

      <!-- 邮箱验证码登录 -->
      <view class="tn-panel tn-panel-email" style="display:none;">
        <view class="field"><text class="field-label">QQ邮箱</text><view id="tnLoginEmail-wrap" class="dom-input-wrap"></view></view>
        <view class="field code-field">
          <text class="field-label">验证码</text>
          <view style="display:flex;gap:8px;">
            <view id="tnLoginEmailCode-wrap" class="dom-input-wrap" style="flex:1;"></view>
            <view class="btn btn-outline btn-sm code-btn" onclick="window._xc_sendEmailCode()" id="tnEmailCodeBtn">获取验证码</view>
          </view>
        </view>
      </view>

      <view class="modal-error" id="tnLoginError"></view>
      <view class="modal-btns"><view class="btn btn-outline" onclick="window._openLoginModal_Close()">取消</view><view class="btn btn-accent" onclick="window._xc_doLogin()">登录</view></view>
      <view class="oauth-divider"><text class="oauth-divider-text">第三方登录</text></view>
      <view class="oauth-btns">
        <view class="oauth-btn oauth-btn-gitee" @tap="oauthLogin('gitee')">
          <text class="oauth-btn-icon">G</text>
          <text class="oauth-btn-label">Gitee</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'

const props = defineProps({
  theme: { type: String, default: 'dark' },
  isLoggedIn: { type: Boolean, default: false }
})

const emit = defineEmits(['toggle-theme', 'show-login'])
const DEFAULT_AVATAR_URL = '/static/images/logo.webp?v=2'

function applySidebarAvatar(src, shouldCache) {
  var sideImg = document.getElementById('sidebarUserAvatar')
  var sideLetter = document.getElementById('sidebarUserLetter')
  var avatarSrc = src || DEFAULT_AVATAR_URL
  if (sideImg) {
    sideImg.onerror = function() {
      if (this.src.indexOf(DEFAULT_AVATAR_URL) === -1) {
        try { uni.removeStorageSync('xc_avatar') } catch(_) {}
        this.src = DEFAULT_AVATAR_URL
      }
    }
    sideImg.src = avatarSrc
    sideImg.style.display = 'block'
  }
  if (sideLetter) sideLetter.style.display = 'none'
  if (shouldCache && src) {
    try { uni.setStorageSync('xc_avatar', src) } catch(_) {}
  }
}

// ── 全局侧边栏：在 document.body 上创建唯一实例 ──
// 原因：uni-app custom tabBar 下每个 tab 页面各有一份 TopNav 实例，
// 若侧边栏 DOM 在 TopNav template 中，会产生 11 份 #tarotSidebar，
// getElementById 只找到第一个（可能是被 display:none 隐藏的 tab 中的），
// 导致侧边栏有时可见有时不可见。
// 修复：改为 JS 动态创建全局唯一 DOM 挂到 body 上，不受 tab 切换影响。
function ensureGlobalSidebar() {
  if (document.getElementById('tarotSidebarGlobal')) return
  var overlay = document.createElement('div')
  overlay.className = 'sidebar-overlay'
  overlay.id = 'sidebarOverlayGlobal'
  overlay.onclick = function() { toggleSidebar() }
  overlay.setAttribute('aria-hidden', 'true')

  var sidebar = document.createElement('div')
  sidebar.className = 'tarot-sidebar'
  sidebar.id = 'tarotSidebarGlobal'
  sidebar.setAttribute('aria-hidden', 'true')
  sidebar.innerHTML = '<div class="sidebar-brand"><span class="sidebar-brand-icon-wrap"><img class="sidebar-brand-icon" src="/static/images/logo.webp?v=2"></span><span class="sidebar-brand-name">时安解忧屋</span></div>'
    + '<div class="sidebar-header"><span class="sidebar-title">对话历史</span></div>'
    + '<div class="sidebar-tabs"><span class="sidebar-tab" id="sidebarTabFlat" onclick="window._xc_setSidebarView(\'flat\')">全部</span><span class="sidebar-tab" id="sidebarTabComprehensive" onclick="window._xc_setSidebarView(\'comprehensive\')">综合</span><span class="sidebar-tab" id="sidebarTabGrouped" onclick="window._xc_setSidebarView(\'grouped\')">分类</span></div>'
    + '<div class="sidebar-content" id="sidebarListGlobal"><div class="sidebar-empty">加载中...</div></div>'
    + '<div class="sidebar-detail" id="sidebarDetailGlobal" style="display:none;">'
    + '<div class="sidebar-detail-back" onclick="window._xc_backToSidebarList()">← 返回</div>'
    + '<div class="sidebar-detail-title" id="sidebarDetailTitle">历史记录</div>'
    + '<div class="sidebar-detail-body" id="sidebarDetailBody"></div></div>'
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
  sidebar.querySelector('#sidebarUserSetting').onclick = function() { toggleSidebar(); go('#/pages/profile/index') }
  sidebar.querySelector('#sidebarUserLogout').onclick = function() { if (window._xc_doLogout) window._xc_doLogout() }
  sidebar.querySelector('#sidebarGuestLogin').onclick = function() { if (window._openLoginModal) window._openLoginModal() }

  document.body.appendChild(overlay)
  document.body.appendChild(sidebar)
  _restoreSidebarView()
  applySidebarAvatar(uni.getStorageSync('xc_avatar') || DEFAULT_AVATAR_URL, false)
}

onMounted(function() {
  // 创建全局侧边栏（仅一次）
  ensureGlobalSidebar()

  // 获取可见弹窗的辅助函数 — 兼容 uni-app H5 页面结构
  if (!window._xc_getVisibleModal) {
    window._xc_getVisibleModal = function() {
      // 先找 .tab-page-wrapper 内的弹窗
      var wrappers = document.querySelectorAll('.tab-page-wrapper')
      for (var w of wrappers) { if (w.style.display !== 'none') { var modal = w.querySelector('#topnavLoginModal'); if (modal) return modal } }
      // 找不到则直接全局查找
      return document.getElementById('topnavLoginModal') || null
    }
  }
  // 全局登录tab切换（纯DOM操作，不依赖Vue reactive）
  if (!window._xc_switchTab) {
    window._xc_switchTab = function(el) {
      var tab = el.getAttribute('data-tab') || 'password'
      var modal = el.closest('#topnavLoginModal')
      if (modal) {
        modal.querySelectorAll('.login-tab').forEach(function(t) { t.classList.remove('active') })
        el.classList.add('active')
        modal.querySelectorAll('.tn-panel-password, .tn-panel-phone, .tn-panel-email').forEach(function(p) { p.style.display = 'none' })
        var panel = modal.querySelector('.tn-panel-' + tab)
        if (panel) panel.style.display = ''
      }
      try { var e = document.getElementById('tnLoginError'); if (e) e.textContent = '' } catch(_) {}
    }
  }

  // 全局打开登录弹窗
    window._openLoginModal = function() {
      // 打开登录弹窗前关闭所有其他弹窗，防止 overlay 冲突
      try { document.querySelectorAll('#accountSettingsModal').forEach(function(el) { el.classList.remove('open') }) } catch(_) {}
     var modal = window._xc_getVisibleModal()
      if (modal) {
        modal.classList.add('open')
        var e = modal.querySelector('#tnLoginError'); if (e) e.textContent = ''
        var loginInputs = [
          ['tnLoginUser-wrap', 'text', '用户名/邮箱/手机号'],
          ['tnLoginPass-wrap', 'password', '密码'],
          ['tnLoginPhone-wrap', 'tel', '手机号'],
          ['tnLoginPhoneCode-wrap', 'text', '验证码'],
          ['tnLoginEmail-wrap', 'email', 'QQ邮箱@qq.com'],
          ['tnLoginEmailCode-wrap', 'text', '验证码']
        ]
        loginInputs.forEach(function(item) {
          var wrap = modal.querySelector('#' + item[0])
          if (wrap && !wrap.querySelector('input')) {
            var inp = document.createElement('input')
            inp.type = item[1]
            inp.id = item[0].replace('-wrap', '')
            inp.placeholder = item[2]
            // 内联样式（style scoped 对动态创建的 input 不生效）
            inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;transition:border-color 0.2s,box-shadow 0.2s'
            inp.onfocus = function() { this.style.borderColor = 'var(--accent)'; this.style.boxShadow = '0 0 0 2px var(--accent-glow)' }
            inp.onblur = function() { this.style.borderColor = 'var(--input-border)'; this.style.boxShadow = 'none' }
            if (item[1] === 'text' || item[1] === 'tel') inp.setAttribute('maxlength', '100')
            wrap.appendChild(inp)
          }
        })
        setTimeout(function() {
          try {
            var firstInput = modal.querySelector('#tnLoginUser, #tnLoginPhone, #tnLoginEmail')
            if (firstInput && firstInput.focus) firstInput.focus()
          } catch(_) {}
        }, 60)
      }
    }
    window._openLoginModal_Close = function() {
      document.querySelectorAll('#topnavLoginModal').forEach(function(el) { el.classList.remove('open') })
    }
    window._xc_doRegister = function() {
      var e = document.getElementById('tnLoginError')
      var modal = window._xc_getVisibleModal()
      if (modal) e = modal.querySelector('#tnLoginError') || e
      var uEl = (modal || document).querySelector('#tnLoginUser'); var pEl = (modal || document).querySelector('#tnLoginPass')
      var u = uEl ? uEl.value.trim() : ''; var p = pEl ? pEl.value : ''
      if (!u || !p) { if (e) e.textContent = '请填写完整'; return }
      if (u.length < 2) { if (e) e.textContent = '用户名至少2个字符'; return }
      if (p.length < 6) { if (e) e.textContent = '密码至少6个字符'; return }
      uni.request({ url: '/api/register', method: 'POST', data: { username: u, password: p } }).then(function(res) {
        var d = res.data
        if (d.error) { if (e) e.textContent = d.error; return }
        uni.setStorageSync('xc_token', 'session'); uni.setStorageSync('xc_user', d.username || u); uni.setStorageSync('xc_has_password', '1')
        window._openLoginModal_Close()
        uni.showToast({ title: '注册成功', icon: 'success' })
        setTimeout(function() { try { window.location.reload() } catch(_) {} }, 800)
      }).catch(function() { if (e) e.textContent = '网络错误' })
    }
    window._xc_doLogin = function() {
      var loginMethods = {
        password: {inputs:[{id:'tnLoginUser',key:'username'},{id:'tnLoginPass',key:'password'}],url:'/api/login'},
        phone:    {inputs:[{id:'tnLoginPhone',key:'phone'},{id:'tnLoginPhoneCode',key:'code'}],url:'/api/sms/login'},
        email:    {inputs:[{id:'tnLoginEmail',key:'email'},{id:'tnLoginEmailCode',key:'code'}],url:'/api/email/login'}
      }
      var e = document.getElementById('tnLoginError'), tab = 'password'
      var modal = window._xc_getVisibleModal()
      if (modal) {
        var activeTab = modal.querySelector('.login-tab.active')
        tab = activeTab ? (activeTab.getAttribute('data-tab') || 'password') : 'password'
        e = modal.querySelector('#tnLoginError') || e
      }
      var method = loginMethods[tab]
      if (!method) return
      // 收集输入值 & 构建请求数据
      var vals = {}, empty = false, data = {}
      method.inputs.forEach(function(inp) {
        var el = (modal || document).querySelector('#' + inp.id)
        vals[inp.id] = el ? el.value.trim() : ''
        if (!vals[inp.id]) empty = true
        data[inp.key] = vals[inp.id]
      })
      if (empty) { if (e) e.textContent = '请填写完整'; return }
      uni.request({ url: method.url, method: 'POST', data: data }).then(function(res) {
        var d = res.data
        if (d.error) { if (e) e.textContent = d.error; return }
        uni.setStorageSync('xc_token', 'session')
        uni.setStorageSync('xc_user', d.username || vals[method.inputs[0].id])
        uni.setStorageSync('xc_has_password', d.has_password !== false ? '1' : '0')
        window._openLoginModal_Close()
        uni.showToast({ title: '登录成功', icon: 'success' })
        try { window.location.reload() } catch(_) {}
      }).catch(function() { if (e) e.textContent = '网络错误' })
    }
    // 通用验证码发送（手机/邮箱共用）
    function _xc_sendCode(config) {
      var modal = window._xc_getVisibleModal()
      if (!modal) return
      var inputEl = modal.querySelector('#' + config.inputId)
      var val = inputEl ? inputEl.value.trim() : ''
      if (!val || !config.validate(val)) {
        var e0 = modal.querySelector('#tnLoginError'); if (e0) e0.textContent = config.errMsg; return
      }
      var btn = modal.querySelector('#' + config.btnId); if (btn) btn.setAttribute('disabled', 'disabled')
      var err = function(msg) { var e1 = modal.querySelector('#tnLoginError'); if (e1) e1.textContent = msg; if (btn) btn.removeAttribute('disabled') }
      uni.request({ url: config.url, method: 'POST', data: (config.buildData || function(v) { return {[config.key]: v} })(val) }).then(function(res) {
        var d = res.data
        if (d.error) { err(d.error); return }
        var sec = 60
        var timer = setInterval(function() { sec--; if (btn) btn.textContent = sec + 's'; if (sec <= 0) { clearInterval(timer); if (btn) { btn.textContent = '获取验证码'; btn.removeAttribute('disabled') } } }, 1000)
      }).catch(function() { err('发送失败') })
    }
    window._xc_sendPhoneCode = function() { _xc_sendCode({ inputId:'tnLoginPhone', btnId:'tnPhoneCodeBtn', key:'phone', url:'/api/sms/send', errMsg:'请输入正确的手机号', validate:function(v){return v.length>=11} }) }
    window._xc_sendEmailCode = function() { _xc_sendCode({ inputId:'tnLoginEmail', btnId:'tnEmailCodeBtn', key:'email', url:'/api/email/send', errMsg:'请输入正确的邮箱', validate:function(v){return v.indexOf('@')!==-1} }) }
    if (!window.__xcLoginKeyDelegated) {
      window.__xcLoginKeyDelegated = true
      document.addEventListener('keydown', function(e) {
        var modal = window._xc_getVisibleModal ? window._xc_getVisibleModal() : document.getElementById('topnavLoginModal')
        if (!modal || !modal.classList || !modal.classList.contains('open')) return
        if (e.key === 'Escape') {
          e.preventDefault()
          window._openLoginModal_Close()
        } else if (e.key === 'Enter') {
          var tag = e.target && e.target.tagName ? e.target.tagName.toLowerCase() : ''
          if (tag === 'textarea') return
          e.preventDefault()
          if (window._xc_doLogin) window._xc_doLogin()
        }
      }, true)
    }
  })

window._xc_toggleSidebar = function() { toggleSidebar() }
window._xc_toggleGroup = function(headerEl) {
  var g = headerEl.parentElement
  if (!g) return
  g.classList.toggle('collapsed')
  // 持久化分组折叠状态到 localStorage
  var type = g.getAttribute('data-type')
  if (type) {
    var collapsed = g.classList.contains('collapsed')
    try {
      var state = JSON.parse(localStorage.getItem('xc_sidebar_group_state') || '{}')
      state[type] = collapsed ? 1 : 0
      localStorage.setItem('xc_sidebar_group_state', JSON.stringify(state))
    } catch(_) {}
  }
}

// 从共享模块获取分组数据和工具函数，未加载时自动初始化
if (!window.__sidebarTypes) {
  window.__sidebarTypes = (function() {
    'use strict'
    var TYPE_ORDER = ['comprehensive', 'qimen', 'paipan', 'bazi', 'liuyao', 'meihua', 'ziwei', 'taluo', 'tarot']
    var TYPE_META = {
      comprehensive: { icon: '✦', label: '综合' },
      qimen: { icon: '🔮', label: '奇门遁甲' }, paipan: { icon: '📜', label: '八字排盘' }, bazi: { icon: '📜', label: '八字排盘' },
      liuyao: { icon: '🧭', label: '六爻排盘' }, meihua: { icon: '🌸', label: '梅花易数' }, ziwei: { icon: '⭐', label: '紫微斗数' },
      taluo: { icon: '🃏', label: '塔罗牌' }, tarot: { icon: '🃏', label: '塔罗牌' }
    }
    return {
      groupRecords: function(records) {
        var groups = {}, seen = {}
        records.forEach(function(r) {
          var t = r.app_type || 'qimen'; if (!groups[t]) groups[t] = []; groups[t].push(r)
        })
        var result = []
        TYPE_ORDER.forEach(function(t) {
          if (groups[t]) {
            var meta = TYPE_META[t] || { icon: '🔮', label: t }, dedupKey = meta.label
            if (seen[dedupKey]) { seen[dedupKey].records = seen[dedupKey].records.concat(groups[t]) }
            else { result.push({ type: t, icon: meta.icon, label: meta.label, records: groups[t] }); seen[dedupKey] = result[result.length - 1] }
            delete groups[t]
          }
        })
        Object.keys(groups).forEach(function(t) {
          var meta = TYPE_META[t] || { icon: '🔮', label: t }; result.push({ type: t, icon: meta.icon, label: meta.label, records: groups[t] })
        })
        return result
      },
      escHtml: function(s) { if (!s || typeof s !== 'string') return ''; var d = document.createElement('div'); d.appendChild(document.createTextNode(s)); return d.innerHTML }
    }
  })()
}
var _groupRecords = window.__sidebarTypes.groupRecords
var _escHtml = window.__sidebarTypes.escHtml

function _loadSidebarUserPanel() {
  var loggedEl = document.getElementById('sidebarUserLogged')
  var guestEl = document.getElementById('sidebarUserGuest')
  if (!loggedEl || !guestEl) return
  var token = uni.getStorageSync('xc_token')
  if (!token) { guestEl.style.display = 'flex'; loggedEl.style.display = 'none'; return }
  uni.request({ url: '/api/me', method: 'GET' }).then(function(res) {
    var d = res.data
    if (d && d.guest) { guestEl.style.display = 'flex'; loggedEl.style.display = 'none'; return }
    if (d && d.username) {
      loggedEl.style.display = 'flex'; guestEl.style.display = 'none'
      document.getElementById('sidebarUserName').textContent = d.username
      var letterEl = document.getElementById('sidebarUserLetter')
      if (letterEl) letterEl.textContent = d.username.charAt(0).toUpperCase()
      applySidebarAvatar(d.avatar || DEFAULT_AVATAR_URL, !!d.avatar)
    }
  }).catch(function() { guestEl.style.display = 'flex'; loggedEl.style.display = 'none' })
  uni.request({ url: '/api/membership', method: 'GET' }).then(function(res) {
    var d = res.data
    if (d && typeof d.points === 'number') {
      var el = document.getElementById('sidebarUserPoints')
      if (el) el.textContent = '积分: ' + d.points
    }
  }).catch(function() {})
}

function toggleSidebar() {
  var sidebar = document.getElementById('tarotSidebarGlobal')
  var overlay = document.getElementById('sidebarOverlayGlobal')
  if (!sidebar || !overlay) return
  if (sidebar.classList.contains('open')) {
    sidebar.classList.remove('open'); overlay.classList.remove('show')
    sidebar.setAttribute('aria-hidden', 'true')
    overlay.setAttribute('aria-hidden', 'true')
    document.body.removeEventListener('click', window.__sidebarClickAway)
    return
  }
  sidebar.classList.add('open'); overlay.classList.add('show')
  sidebar.setAttribute('aria-hidden', 'false')
  overlay.setAttribute('aria-hidden', 'false')
  uni.$emit('sidebar-opened')
  document.body.removeEventListener('click', window.__sidebarClickAway)
  window.__sidebarClickAway = function(e) {
    var s = document.getElementById('tarotSidebarGlobal')
    if (s && s.classList.contains('open') && !s.contains(e.target)) {
      e.stopPropagation(); s.classList.remove('open')
      s.setAttribute('aria-hidden', 'true')
      var ov = document.getElementById('sidebarOverlayGlobal')
      if (ov) { ov.classList.remove('show'); ov.setAttribute('aria-hidden', 'true') }
      document.body.removeEventListener('click', window.__sidebarClickAway)
    }
  }
  setTimeout(function() { document.body.addEventListener('click', window.__sidebarClickAway) }, 200)
  var listEl = document.getElementById('sidebarListGlobal')
  if (!listEl) return
  // 并行加载用户面板
  _loadSidebarUserPanel()
  var token = ''
  try { token = uni.getStorageSync('xc_token') || '' } catch(_) {}
  if (!token) {
    window.__sidebarCache = null
    listEl.innerHTML = '<div class="sidebar-empty">登录后可同步历史记录</div>'
    return
  }
  // 30 秒内缓存
  var now = Date.now()
  if (window.__sidebarCache && (now - window.__sidebarCache.ts) < 30000) {
    _restoreSidebarView()
    var ft = document.getElementById('sidebarTabFlat')
    var ct = document.getElementById('sidebarTabComprehensive')
    if (ft && ft.classList.contains('active')) {
      window._xc_setSidebarView('flat')
    } else if (ct && ct.classList.contains('active')) {
      window._xc_setSidebarView('comprehensive')
    } else {
      _renderSidebarGroups(window.__sidebarCache.groups, listEl)
    }
    return
  }
  listEl.innerHTML = '<div class="sidebar-empty">加载中...</div>'
  var recordsLoaded = false, comprehensiveLoaded = false, tarotLoaded = false, lyConvLoaded = false, mhConvLoaded = false, qiConvLoaded = false, baziConvLoaded = false, zwConvLoaded = false
  var allRecords = [], comprehensiveItems = [], tarotItems = [], lyConvItems = [], mhConvItems = [], qiConvItems = [], baziConvItems = [], zwConvItems = []
  function _renderMerged() {
    if (!recordsLoaded || !comprehensiveLoaded || !tarotLoaded || !lyConvLoaded || !mhConvLoaded || !qiConvLoaded || !baziConvLoaded || !zwConvLoaded) return
    comprehensiveItems.forEach(function(c) {
      allRecords.push({ id: 'cp_' + c.id, app_type: 'comprehensive', question: c.title || '综合 AI 问答', created_at: c.updated_at || c.created_at, _comprehensiveConvId: c.id })
    })
    tarotItems.forEach(function(c) {
      allRecords.push({ id: 'tarot_' + c.id, app_type: 'tarot', question: c.title || c.spread_name || '塔罗解读', created_at: c.updated_at || c.created_at, _tarotConvId: c.id })
    })
    lyConvItems.forEach(function(c) {
      allRecords.push({ id: 'ly_' + c.id, app_type: 'liuyao', question: c.title || '六爻占卜', created_at: c.updated_at || c.created_at, _lyConvId: c.id })
    })
    mhConvItems.forEach(function(c) {
      allRecords.push({ id: 'mh_' + c.id, app_type: 'meihua', question: c.title || '梅花易数', created_at: c.updated_at || c.created_at, _mhConvId: c.id })
    })
    qiConvItems.forEach(function(c) {
      allRecords.push({ id: 'qi_' + c.id, app_type: 'qimen', question: c.title || '奇门遁甲', created_at: c.updated_at || c.created_at, _qaiConvId: c.id })
    })
    baziConvItems.forEach(function(c) {
      allRecords.push({ id: 'bz_' + c.id, app_type: 'bazi', question: c.title || '八字AI解读', created_at: c.updated_at || c.created_at, _baziConvId: c.id })
    })
    zwConvItems.forEach(function(c) {
      allRecords.push({ id: 'zw_' + c.id, app_type: 'ziwei', question: c.title || '紫微斗数AI解读', created_at: c.updated_at || c.created_at, _zwConvId: c.id })
    })
    if (!allRecords.length) { listEl.innerHTML = '<div class="sidebar-empty">暂无历史记录</div>'; return }
    var groups = _groupRecords(allRecords)
    window.__sidebarCache = { ts: Date.now(), groups: groups, flat: allRecords }
    // 恢复用户上次的视图选择，再渲染对应视图
    _restoreSidebarView()
    var flatTab = document.getElementById('sidebarTabFlat')
    var comprehensiveTab = document.getElementById('sidebarTabComprehensive')
    if (flatTab && flatTab.classList.contains('active')) {
      window._xc_setSidebarView('flat')
    } else if (comprehensiveTab && comprehensiveTab.classList.contains('active')) {
      window._xc_setSidebarView('comprehensive')
    } else {
      _renderSidebarGroups(groups, listEl)
    }
  }
  uni.request({ url: '/api/records?per_page=50', method: 'GET', success: function(res) {
    allRecords = res.data.records || []; recordsLoaded = true; _renderMerged()
  }, fail: function() { recordsLoaded = true; _renderMerged() }})
  uni.request({ url: '/api/comprehensive/conversations', method: 'GET', success: function(res) {
    comprehensiveItems = res.data || []; if (!Array.isArray(comprehensiveItems)) comprehensiveItems = []; comprehensiveLoaded = true; _renderMerged()
  }, fail: function() { comprehensiveLoaded = true; _renderMerged() }})
  uni.request({ url: '/api/tarot/conversations', method: 'GET', success: function(res) {
    tarotItems = res.data || []; if (!Array.isArray(tarotItems)) tarotItems = []; tarotLoaded = true; _renderMerged()
  }, fail: function() { tarotLoaded = true; _renderMerged() }})
  uni.request({ url: '/api/liuyao/conversations', method: 'GET', success: function(res) {
    lyConvItems = res.data || []; if (!Array.isArray(lyConvItems)) lyConvItems = []; lyConvLoaded = true; _renderMerged()
  }, fail: function() { lyConvLoaded = true; _renderMerged() }})
  uni.request({ url: '/api/meihua/conversations', method: 'GET', success: function(res) {
    mhConvItems = res.data || []; if (!Array.isArray(mhConvItems)) mhConvItems = []; mhConvLoaded = true; _renderMerged()
  }, fail: function() { mhConvLoaded = true; _renderMerged() }})
  uni.request({ url: '/api/qimen/conversations', method: 'GET', success: function(res) {
    qiConvItems = res.data || []; if (!Array.isArray(qiConvItems)) qiConvItems = []; qiConvLoaded = true; _renderMerged()
  }, fail: function() { qiConvLoaded = true; _renderMerged() }})
  uni.request({ url: '/api/bazi/conversations', method: 'GET', success: function(res) {
    baziConvItems = res.data || []; if (!Array.isArray(baziConvItems)) baziConvItems = []; baziConvLoaded = true; _renderMerged()
  }, fail: function() { baziConvLoaded = true; _renderMerged() }})
  uni.request({ url: '/api/ziwei/conversations', method: 'GET', success: function(res) {
    zwConvItems = res.data || []; if (!Array.isArray(zwConvItems)) zwConvItems = []; zwConvLoaded = true; _renderMerged()
  }, fail: function() { zwConvLoaded = true; _renderMerged() }})
}

// 渲染分组历史（共享函数，避免与 sidebar.js 重复）
function _renderSidebarGroups(groups, listEl) {
  // 读取持久化的分组折叠状态
  var savedState = {}
  try { savedState = JSON.parse(localStorage.getItem('xc_sidebar_group_state') || '{}') } catch(_) {}
  var h = ''
  groups.forEach(function(g) {
    var collapsed = savedState[g.type] === 1 ? ' collapsed' : ''
    h += '<div class="sidebar-group' + collapsed + '" data-type="' + g.type + '">'
      + '<div class="sidebar-group-header" onclick="window._xc_toggleGroup(this)">'
      + '<span class="sidebar-group-icon">' + g.icon + '</span>'
      + '<span class="sidebar-group-label">' + g.label + '</span>'
      + '<span class="sidebar-group-count">' + g.records.length + '</span>'
      + '<span class="sidebar-group-arrow">▾</span>'
      + '</div><div class="sidebar-group-items">'
    h += _renderNewConversationItem(g.type, g.label)
    g.records.forEach(function(r) {
      h += _renderSidebarItem(r)
    })
    h += '</div></div>'
  })
  listEl.innerHTML = h
}

function _renderNewConversationItem(type, label) {
  var text = '＋ 新对话'
  if (label) text += ' · ' + _escHtml(label)
  return '<div class="sidebar-item sidebar-new-item">'
    + '<div class="sidebar-item-body" onclick="window._xc_startNewConversation(\'' + type + '\')">'
    + '<span class="sidebar-item-text">' + text + '</span>'
    + '<span class="sidebar-item-time">开始新的提问</span>'
    + '</div></div>'
}

function _renderSidebarItem(r) {
  var time = _formatSidebarTime(r.created_at)
  var text = _escHtml(r.question || '(无问题)')
  var realId = r._comprehensiveConvId || r._tarotConvId || r._lyConvId || r._mhConvId || r._qaiConvId || r._baziConvId || r._zwConvId || r.id
  var appType = r.app_type || ''
  var deleteConfirm = 'if(confirm(\'确定要删除这条记录吗？\'))window._xc_deleteHistoryItem(\'' + appType + '\',\'' + realId + '\',this)'
  var clickAction = r._comprehensiveConvId
    ? 'onclick="window._showComprehensiveConv(' + r._comprehensiveConvId + ')"'
    : r._tarotConvId
    ? 'onclick="window._showTarotConv(' + r._tarotConvId + ')"'
    : r.app_type === 'tarot'
    ? 'onclick="window._showTarotRecordDetail(' + r.id + ')"'
    : r._lyConvId
    ? 'onclick="window._showLyConvDetail(' + r._lyConvId + ')"'
    : r._mhConvId
    ? 'onclick="window._showMhConvDetail(' + r._mhConvId + ')"'
    : r._qaiConvId
    ? 'onclick="window._showQiConvDetail(' + r._qaiConvId + ')"'
    : r._baziConvId
    ? 'onclick="window._showBaziConvDetail(' + r._baziConvId + ')"'
    : r._zwConvId
    ? 'onclick="window._showZwConvDetail(' + r._zwConvId + ')"'
    : r.app_type === 'comprehensive'
    ? 'onclick="window._showComprehensiveConv(' + realId + ')"'
    : r.app_type === 'liuyao'
    ? 'onclick="window._showLyRecordDetail(' + r.id + ')"'
    : r.app_type === 'qimen'
    ? 'onclick="window._showQiRecordDetail(' + r.id + ')"'
    : r.app_type === 'bazi'
    ? 'onclick="window._showBaziRecordDetail(' + r.id + ')"'
    : r.app_type === 'ziwei'
    ? 'onclick="window._showHistoryDetail(' + r.id + ')"'
    : 'onclick="window._showHistoryDetail(' + r.id + ')"'
  return '<div class="sidebar-item">'
    + '<div class="sidebar-item-body" ' + clickAction + '>'
    + '<span class="sidebar-item-text">' + text + '</span>'
    + '<span class="sidebar-item-time">' + time + '</span>'
    + '</div>'
    + '<span class="sidebar-item-del" onclick="' + deleteConfirm + '" title="删除">✕</span>'
    + '</div>'
}

// 返回侧边栏列表
window._xc_backToSidebarList = function() {
  var list = document.getElementById('sidebarListGlobal')
  var detail = document.getElementById('sidebarDetailGlobal')
  if (list) list.style.display = ''
  if (detail) detail.style.display = 'none'
}

function _showSidebarDetail(title, html) {
  var list = document.getElementById('sidebarListGlobal')
  var detail = document.getElementById('sidebarDetailGlobal')
  var detailTitle = document.getElementById('sidebarDetailTitle')
  var detailBody = document.getElementById('sidebarDetailBody')
  if (list) list.style.display = 'none'
  if (detail) detail.style.display = ''
  if (detailTitle) detailTitle.textContent = title
  if (detailBody) detailBody.innerHTML = html
}

// 塔罗对话查看 — 跳转到塔罗页面恢复对话
window._showTarotConv = function(cid) {
  uni.request({ url: '/api/tarot/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) return
    window.__xc_restoreData = { type: 'tarot', messages: d.messages || [], title: d.title || d.spread_name || '塔罗解读', id: d.id }
    window._xc_toggleSidebar()
    uni.switchTab({ url: '/pages/tarot/index', success: function() { setTimeout(function() { uni.$emit('xc-restore') }, 200) } })
  }})
}

// 综合 AI 对话查看 — 回到首页恢复对话
window._showComprehensiveConv = function(cid) {
  uni.request({ url: '/api/comprehensive/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d || !d.id) { uni.showToast({ title: '对话不存在', icon: 'none' }); return }
    window._xc_toggleSidebar()
    try { sessionStorage.setItem('xc_comprehensive_resume_id', String(d.id)) } catch(_) {}
    var restore = function() {
      setTimeout(function() {
        if (window._xc_restoreComprehensive) window._xc_restoreComprehensive(d.id)
      }, 200)
    }
    uni.switchTab({ url: '/pages/index/index', success: restore, fail: restore })
    restore()
  }, fail: function() { uni.showToast({ title: '加载失败', icon: 'none' }) } })
}

window._xc_startNewConversation = function(type) {
  var t = type || 'comprehensive'
  var routeMap = {
    comprehensive: '/pages/index/index',
    qimen: '/pages/qimen/index',
    paipan: '/pages/bazi-index/index',
    bazi: '/pages/bazi-index/index',
    liuyao: '/pages/liuyao/index',
    meihua: '/pages/meihua/index',
    ziwei: '/pages/ziwei/index',
    taluo: '/pages/tarot/index',
    tarot: '/pages/tarot/index'
  }
  var route = routeMap[t] || '/pages/index/index'
  try {
    window.__xc_restoreData = null
    sessionStorage.removeItem('xc_comprehensive_resume_id')
    sessionStorage.removeItem('_nav_query')
    sessionStorage.setItem('xc_start_new_conversation', t)
    if (t === 'qimen' || t === 'bazi' || t === 'paipan') sessionStorage.setItem('_nav_query', 'tab=ai')
  } catch(_) {}
  window._xc_toggleSidebar()

  function runReset() {
    if (t === 'comprehensive' && window._xc_newComprehensive) window._xc_newComprehensive()
    else if ((t === 'bazi' || t === 'paipan') && window._xc_newBazi) window._xc_newBazi()
    else if (t === 'qimen' && window._xc_newQimen) window._xc_newQimen()
    else if (t === 'liuyao' && window._xc_newLiuyao) window._xc_newLiuyao()
    else if (t === 'meihua' && window._xc_newMeihua) window._xc_newMeihua()
    else if (t === 'ziwei' && window._xc_newZiwei) window._xc_newZiwei()
    else if ((t === 'tarot' || t === 'taluo') && window._xc_newTarot) window._xc_newTarot()
  }

  uni.switchTab({ url: route, success: function() {
    setTimeout(runReset, 250)
    setTimeout(runReset, 650)
  }, fail: function() {
    setTimeout(runReset, 250)
  }})
  setTimeout(runReset, 80)
}

// 塔罗旧记录跳转（从/api/records获取数据并恢复）
window._showTarotRecordDetail = function(rid) {
  uni.request({ url: '/api/records/' + rid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) { window._xc_toggleSidebar(); uni.switchTab({ url: '/pages/tarot/index' }); return }
    window.__xc_restoreData = { type: 'tarot', title: d.question || '塔罗解读', question: d.question || '', rawHtml: d.result_html || '', id: d.id }
    window._xc_toggleSidebar()
    uni.switchTab({ url: '/pages/tarot/index', success: function() { setTimeout(function() { uni.$emit('xc-restore') }, 200) } })
  }})
}

function _isOnPage(route) {
  // 使用 location.hash 判断当前页面（比 getCurrentPages 在 H5 tabBar 下更可靠）
  try { return location.hash.indexOf(route) !== -1 } catch(e) {}
  return false
}

// 六爻对话查看 — 跳转到六爻页面恢复对话
window._showLyConvDetail = function(cid) {
  uni.request({ url: '/api/liuyao/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) return
    window.__xc_restoreData = { type: 'liuyao', messages: d.messages || [], title: d.title || '六爻占卜', id: d.id }
    window._xc_toggleSidebar()
    if (_isOnPage('pages/liuyao/index')) {
      setTimeout(function() { if (window._xc_restoreLiuyao) window._xc_restoreLiuyao() }, 100)
    } else {
      uni.switchTab({ url: '/pages/liuyao/index', success: function() {
        setTimeout(function() { if (window._xc_restoreLiuyao) window._xc_restoreLiuyao() }, 400)
      } })
    }
  }})
}

// 六爻旧记录跳转（从/api/records获取数据并恢复）
window._showLyRecordDetail = function(rid) {
  uni.request({ url: '/api/records/' + rid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) { window._xc_toggleSidebar(); return }
    window.__xc_restoreData = { type: 'liuyao', title: d.question || '六爻占卜', question: d.question || '', rawHtml: d.result_html || '', id: d.id }
    window._xc_toggleSidebar()
    if (_isOnPage('pages/liuyao/index')) {
      setTimeout(function() { if (window._xc_restoreLiuyao) window._xc_restoreLiuyao() }, 100)
    } else {
      uni.switchTab({ url: '/pages/liuyao/index', success: function() {
        setTimeout(function() { if (window._xc_restoreLiuyao) window._xc_restoreLiuyao() }, 400)
      } })
    }
  }})
}

// 梅花对话查看 — 跳转到梅花页面恢复对话
window._showMhConvDetail = function(cid) {
  uni.request({ url: '/api/meihua/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) return
    window.__xc_restoreData = { type: 'meihua', messages: d.messages || [], title: d.title || '梅花易数', id: d.id }
    window._xc_toggleSidebar()
    uni.switchTab({ url: '/pages/meihua/index', success: function() {
      setTimeout(function() { uni.$emit('xc-restore') }, 200)
      setTimeout(function() { if (window._xc_restoreMeihua) window._xc_restoreMeihua() }, 400)
    } })
  }})
}

// 奇门遁甲对话查看 — 跳转到奇门页面恢复对话
window._showQiConvDetail = function(cid) {
  uni.request({ url: '/api/qimen/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) return
    window.__xc_restoreData = { type: 'qimen', messages: d.messages || [], title: d.title || '奇门遁甲', id: d.id }
    window._xc_toggleSidebar()
    try { sessionStorage.setItem('_nav_query', 'tab=ai') } catch(_) {}
    if (_isOnPage('pages/qimen/index')) {
      setTimeout(function() { if (window._xc_restoreQimen) window._xc_restoreQimen() }, 100)
    } else {
      uni.switchTab({ url: '/pages/qimen/index', success: function() {
        setTimeout(function() { if (window._xc_restoreQimen) window._xc_restoreQimen() }, 400)
      } })
    }
  }})
}

// 奇门遁甲旧记录跳转（从/api/records获取数据并恢复）
window._showQiRecordDetail = function(rid) {
  uni.request({ url: '/api/records/' + rid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) { window._xc_toggleSidebar(); return }
    window.__xc_restoreData = { type: 'qimen', title: d.question || '奇门遁甲', question: d.question || '', rawHtml: d.result_html || '', id: d.id }
    window._xc_toggleSidebar()
    try { sessionStorage.setItem('_nav_query', 'tab=ai') } catch(_) {}
    if (_isOnPage('pages/qimen/index')) {
      setTimeout(function() { if (window._xc_restoreQimen) window._xc_restoreQimen() }, 100)
    } else {
      uni.switchTab({ url: '/pages/qimen/index', success: function() {
        setTimeout(function() { if (window._xc_restoreQimen) window._xc_restoreQimen() }, 400)
      } })
    }
  }})
}

window._showBaziConvDetail = function(cid) {
  if (window._xc_closeSidebar) window._xc_closeSidebar()
  uni.request({ url: '/api/bazi/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d || !d.id) { uni.showToast({ title: '对话不存在', icon: 'none' }); return }
    window.__xc_restoreData = { type: 'bazi', id: d.id, title: d.title, messages: d.messages, birth_data: d.birth_data }
    try { sessionStorage.setItem('_nav_query', 'tab=ai') } catch(_) {}
    function doRestore() {
      if (window._xc_restoreBazi) { window._xc_restoreBazi(); return true }
      return false
    }
    if (_isOnPage('pages/bazi-index/index')) {
      setTimeout(function() { if (!doRestore()) setTimeout(doRestore, 500) }, 100)
    } else {
      uni.switchTab({ url: '/pages/bazi-index/index' })
      setTimeout(function() { if (!doRestore()) setTimeout(doRestore, 500) }, 600)
    }
  }, fail: function() { uni.showToast({ title: '加载失败', icon: 'none' }) } })
}

window._showBaziRecordDetail = function(rid) {
  if (window._xc_closeSidebar) window._xc_closeSidebar()
  uni.request({ url: '/api/records/' + rid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) { uni.showToast({ title: '记录不存在', icon: 'none' }); return }
    var _bzMsgs = []
    if (d.question) _bzMsgs.push({ role: 'user', content: d.question })
    if (d.result_html) _bzMsgs.push({ role: 'assistant', content: d.result_html })
    window.__xc_restoreData = { type: 'bazi', id: d.id, title: d.question || '八字排盘', messages: _bzMsgs }
    try { sessionStorage.setItem('_nav_query', 'tab=ai') } catch(_) {}
    uni.switchTab({ url: '/pages/bazi-index/index' })
    setTimeout(function() { if (window._xc_restoreBazi) window._xc_restoreBazi(); else setTimeout(function() { if (window._xc_restoreBazi) window._xc_restoreBazi() }, 500) }, 600)
  }, fail: function() { uni.showToast({ title: '加载失败', icon: 'none' }) } })
}

window._showZwConvDetail = function(cid) {
  uni.request({ url: '/api/ziwei/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) return
    window.__xc_restoreData = { type: 'ziwei', messages: d.messages || [], title: d.title || '紫微斗数AI解读', id: d.id }
    window._xc_toggleSidebar()
    function doRestore() {
      if (window._xc_restoreZiwei) { window._xc_restoreZiwei(); return true }
      return false
    }
    if (_isOnPage('pages/ziwei/index')) {
      setTimeout(function() { if (!doRestore()) setTimeout(doRestore, 500) }, 100)
    } else {
      uni.switchTab({ url: '/pages/ziwei/index' })
      setTimeout(function() { if (!doRestore()) setTimeout(doRestore, 500) }, 600)
    }
  }, fail: function() { uni.showToast({ title: '加载失败', icon: 'none' }) } })
}

// 恢复上次使用的视图选择
function _restoreSidebarView() {
  var flatTab = document.getElementById('sidebarTabFlat')
  var groupedTab = document.getElementById('sidebarTabGrouped')
  var comprehensiveTab = document.getElementById('sidebarTabComprehensive')
  if (!flatTab || !groupedTab || !comprehensiveTab) return
  var saved = ''
  try { saved = localStorage.getItem('xc_sidebar_view') || '' } catch(_) {}
  if (saved === 'grouped') {
    groupedTab.classList.add('active')
    comprehensiveTab.classList.remove('active')
    flatTab.classList.remove('active')
  } else if (saved === 'comprehensive') {
    comprehensiveTab.classList.add('active')
    groupedTab.classList.remove('active')
    flatTab.classList.remove('active')
  } else {
    // 默认 flat
    flatTab.classList.add('active')
    comprehensiveTab.classList.remove('active')
    groupedTab.classList.remove('active')
  }
}

// 侧边栏视图切换（分类/全部）
window._xc_setSidebarView = function(view) {
  var groupedTab = document.getElementById('sidebarTabGrouped')
  var flatTab = document.getElementById('sidebarTabFlat')
  var comprehensiveTab = document.getElementById('sidebarTabComprehensive')
  var listEl = document.getElementById('sidebarListGlobal')
  if (!groupedTab || !flatTab || !comprehensiveTab || !listEl) return
  var cache = window.__sidebarCache
  if (!cache || !cache.groups) return
  // 持久化用户选择的视图
  try { localStorage.setItem('xc_sidebar_view', view) } catch(_) {}
  if (view === 'grouped') {
    groupedTab.classList.add('active')
    flatTab.classList.remove('active')
    comprehensiveTab.classList.remove('active')
    _renderSidebarGroups(cache.groups, listEl)
  } else if (view === 'comprehensive') {
    comprehensiveTab.classList.add('active')
    flatTab.classList.remove('active')
    groupedTab.classList.remove('active')
    var comprehensive = (cache.flat || []).filter(function(r) { return r.app_type === 'comprehensive' })
    comprehensive.sort(function(a, b) { return (b.created_at || '').localeCompare(a.created_at || '') })
    var ch = _renderNewConversationItem('comprehensive', '综合')
    comprehensive.forEach(function(r) { ch += _renderSidebarItem(r) })
    if (!comprehensive.length) ch += '<div class="sidebar-empty">暂无综合对话</div>'
    listEl.innerHTML = ch
  } else {
    flatTab.classList.add('active')
    groupedTab.classList.remove('active')
    comprehensiveTab.classList.remove('active')
    // 全部：展平按时间倒序排列
    var flat = cache.flat || []
    flat.sort(function(a, b) { return (b.created_at || '').localeCompare(a.created_at || '') })
    var h = ''
    flat.forEach(function(r) {
      h += _renderSidebarItem(r)
    })
    if (!flat.length) h = '<div class="sidebar-empty">暂无历史记录</div>'
    listEl.innerHTML = h
  }
}

function _formatSidebarTime(created_at) {
  if (!created_at) return ''
  var t = new Date(created_at)
  if (isNaN(t.getTime())) return ''
  var offset = 8 * 60
  var local = new Date(t.getTime() + offset * 60 * 1000)
  var y = local.getUTCFullYear()
  var M = ('0' + (local.getUTCMonth() + 1)).slice(-2)
  var d = ('0' + local.getUTCDate()).slice(-2)
  var hh = ('0' + local.getUTCHours()).slice(-2)
  var mm = ('0' + local.getUTCMinutes()).slice(-2)
  return y + '-' + M + '-' + d + ' ' + hh + ':' + mm
}

// 删除历史记录项（支持 records/tarot/liuyao/meihua/qimen）
window._xc_deleteHistoryItem = function(appType, realId, el) {
  if (!realId) return
  var urlMap = {
    comprehensive: '/api/comprehensive/conversations/',
    tarot: '/api/tarot/conversations/',
    liuyao: '/api/liuyao/conversations/',
    meihua: '/api/meihua/conversations/',
    qimen: '/api/qimen/conversations/',
    bazi: '/api/bazi/conversations/'
  }
  var url = urlMap[appType] || '/api/records/'
  var sidebarItem = el && el.closest ? el.closest('.sidebar-item') : null
  uni.request({ url: url + realId, method: 'DELETE', success: function() {
    if (sidebarItem) sidebarItem.remove()
    window.__sidebarCache = null
  }, fail: function(err) { console.error('删除失败:', err) }})
}

// 历史详情弹窗（在侧边栏内展开）
window._showHistoryDetail = function(rid) {
  uni.request({ url: '/api/records/' + rid, method: 'GET', success: function(res) {
    var d = res.data
    var html = '<div class="history-markdown">' + (d.result_html || '') + '</div>'
    _showSidebarDetail(d.question || '历史记录', html)
  }})
}

function onShowLogin() {
  emit('show-login')
  try {
    window._openLoginModal()
  } catch(_) {}
}

var avatarUrl = ref('')
var avatarLetter = ref('')
var _avatarInstanceLoaded = false
function onAvatarError() {
  if (avatarUrl.value && avatarUrl.value.indexOf(DEFAULT_AVATAR_URL) === -1) {
    uni.removeStorageSync('xc_avatar')
    avatarUrl.value = DEFAULT_AVATAR_URL
  }
}
function loadAvatar() {
  if (!props.isLoggedIn) return
  var cachedUser = uni.getStorageSync('xc_user')
  var parsed = null
  try { parsed = typeof cachedUser === 'string' ? JSON.parse(cachedUser) : cachedUser } catch(_) { parsed = null }
  if (parsed && typeof parsed === 'object') {
    if (parsed.username) avatarLetter.value = parsed.username.charAt(0).toUpperCase()
    else if (parsed.nickname) avatarLetter.value = parsed.nickname.charAt(0).toUpperCase()
  } else if (cachedUser && typeof cachedUser === 'string') {
    avatarLetter.value = cachedUser.charAt(0).toUpperCase()
  }
  var cachedAvatar = uni.getStorageSync('xc_avatar')
  avatarUrl.value = cachedAvatar || DEFAULT_AVATAR_URL
  if (_avatarInstanceLoaded) return
  _avatarInstanceLoaded = true
  window.__avatarLoaded = true
  uni.request({ url: '/api/me', method: 'GET' }).then(function(res) {
    var d = res.data
    if (d && d.guest) {
    } else if (d && d.username) {
      avatarLetter.value = d.username.charAt(0).toUpperCase()
      if (d.avatar) { avatarUrl.value = d.avatar; uni.setStorageSync('xc_avatar', d.avatar) }
      else avatarUrl.value = DEFAULT_AVATAR_URL
      document.querySelectorAll('#avatarAdminEntry').forEach(function(el) {
        el.style.display = d.is_admin ? '' : 'none'
      })
    }
  }).catch(function() {})
}
var pointsLoaded = false
function loadPointsSummary() {
  if (!props.isLoggedIn || pointsLoaded) return
  pointsLoaded = true
  uni.request({ url: '/api/membership', method: 'GET' }).then(function(res) {
    var d = res.data
    if (d && typeof d.points === 'number') {
      document.querySelectorAll('#avatarPointsBadge').forEach(function(el) {
        el.textContent = d.points
      })
    }
  }).catch(function() {})
}
// 监听积分更新事件（签到/消费后实时刷新）
if (!window.__xcPointsListener) {
  window.__xcPointsListener = true
  window.addEventListener('xc-points-updated', function(e) {
    if (e.detail && typeof e.detail.points === 'number') {
      document.querySelectorAll('#avatarPointsBadge').forEach(function(el) {
        el.textContent = e.detail.points
      })
    }
  })
}
function doLogout() {
  uni.request({ url: '/api/logout', method: 'POST' }).then(function() {
    uni.removeStorageSync('xc_token'); uni.removeStorageSync('xc_user')
    window.location.reload()
  }).catch(function() {
    uni.removeStorageSync('xc_token'); uni.removeStorageSync('xc_user')
    window.location.reload()
  })
}
function closeLoginModal() { try { document.querySelectorAll('#topnavLoginModal').forEach(function(el) { el.classList.remove('open') }) } catch(_) {} }
async function doLogin() {
  var e = document.getElementById('tnLoginError')
  var tab = loginTab.value || 'password'
  if (tab === 'password') {
    var uEl = document.getElementById('tnLoginUser'); var pEl = document.getElementById('tnLoginPass')
    var u = uEl ? uEl.value.trim() : ''; var p = pEl ? pEl.value : ''
    if (!u || !p) { if (e) e.textContent = '请填写完整'; return }
    try {
      var res = await uni.request({ url: '/api/login', method: 'POST', data: { username: u, password: p } })
      var d = res.data
      if (d.error) { if (e) e.textContent = d.error; return }
      uni.setStorageSync('xc_token', 'session'); uni.setStorageSync('xc_user', d.username || u); uni.setStorageSync('xc_has_password', d.has_password !== false ? '1' : '0')
      closeLoginModal(); window.location.reload()
    } catch (_) { if (e) e.textContent = '网络错误' }
  } else if (tab === 'phone') {
    var phoneEl = document.getElementById('tnLoginPhone'); var codeEl = document.getElementById('tnLoginPhoneCode')
    var phone = phoneEl ? phoneEl.value.trim() : ''; var code = codeEl ? codeEl.value.trim() : ''
    if (!phone || !code) { if (e) e.textContent = '请填写完整'; return }
    try {
      var res = await uni.request({ url: '/api/sms/login', method: 'POST', data: { phone: phone, code: code } })
      var d = res.data
      if (d.error) { if (e) e.textContent = d.error; return }
      uni.setStorageSync('xc_token', 'session'); uni.setStorageSync('xc_user', d.username || phone); uni.setStorageSync('xc_has_password', d.has_password !== false ? '1' : '0')
      closeLoginModal(); window.location.reload()
    } catch (_) { if (e) e.textContent = '网络错误' }
  } else if (tab === 'email') {
    var emailEl = document.getElementById('tnLoginEmail'); var codeEl2 = document.getElementById('tnLoginEmailCode')
    var email = emailEl ? emailEl.value.trim() : ''; var code2 = codeEl2 ? codeEl2.value.trim() : ''
    if (!email || !code2) { if (e) e.textContent = '请填写完整'; return }
    try {
      var res = await uni.request({ url: '/api/email/login', method: 'POST', data: { email: email, code: code2 } })
      var d = res.data
      if (d.error) { if (e) e.textContent = d.error; return }
      uni.setStorageSync('xc_token', 'session'); uni.setStorageSync('xc_user', d.username || email); uni.setStorageSync('xc_has_password', d.has_password !== false ? '1' : '0')
      closeLoginModal(); window.location.reload()
    } catch (_) { if (e) e.textContent = '网络错误' }
  }
}

async function sendPhoneCode() {
  var phoneEl = document.getElementById('tnLoginPhone')
  var phone = phoneEl ? phoneEl.value.trim() : ''
  if (!phone || phone.length < 11) { var e = document.getElementById('tnLoginError'); if (e) e.textContent = '请输入正确的手机号'; return }
  var btn = document.getElementById('tnPhoneCodeBtn'); if (btn) btn.setAttribute('disabled', 'disabled')
  try {
    var res = await uni.request({ url: '/api/sms/send', method: 'POST', data: { phone: phone } })
    var d = res.data
    if (d.error) { var e2 = document.getElementById('tnLoginError'); if (e2) e2.textContent = d.error; if (btn) btn.removeAttribute('disabled'); return }
    var sec = 60; var timer = setInterval(function() { sec--; if (btn) btn.textContent = sec + 's'; if (sec <= 0) { clearInterval(timer); if (btn) { btn.textContent = '获取验证码'; btn.removeAttribute('disabled') } } }, 1000)
  } catch (_) { var e3 = document.getElementById('tnLoginError'); if (e3) e3.textContent = '发送失败'; if (btn) btn.removeAttribute('disabled') }
}

async function sendEmailCode() {
  var emailEl = document.getElementById('tnLoginEmail')
  var email = emailEl ? emailEl.value.trim() : ''
  if (!email || email.indexOf('@') === -1) { var e = document.getElementById('tnLoginError'); if (e) e.textContent = '请输入正确的邮箱'; return }
  var btn = document.getElementById('tnEmailCodeBtn'); if (btn) btn.setAttribute('disabled', 'disabled')
  try {
    var res = await uni.request({ url: '/api/email/send', method: 'POST', data: { email: email } })
    var d = res.data
    if (d.error) { var e2 = document.getElementById('tnLoginError'); if (e2) e2.textContent = d.error; if (btn) btn.removeAttribute('disabled'); return }
    var sec = 60; var timer = setInterval(function() { sec--; if (btn) btn.textContent = sec + 's'; if (sec <= 0) { clearInterval(timer); if (btn) { btn.textContent = '获取验证码'; btn.removeAttribute('disabled') } } }, 1000)
  } catch (_) { var e3 = document.getElementById('tnLoginError'); if (e3) e3.textContent = '发送失败'; if (btn) btn.removeAttribute('disabled') }
}

async function oauthLogin(provider) {
  try {
    var res = await uni.request({ url: '/api/oauth/' + provider + '/url', method: 'GET' })
    var d = res.data
    if (d.url) { window.location.href = d.url }
    else if (d.error) { var e = document.getElementById('tnLoginError'); if (e) e.textContent = d.error }
  } catch (e) { var e2 = document.getElementById('tnLoginError'); if (e2) e2.textContent = '获取登录链接失败' }
}

// 主题切换：全局瞬间生效
var _themeToggleLock = 0
function onToggleTheme() {
  var now = Date.now()
  if (now - _themeToggleLock < 300) return
  _themeToggleLock = now
  var newTheme = props.theme === 'dark' ? 'light' : 'dark'
  try {
    document.documentElement.setAttribute('data-theme', newTheme)
    document.body.setAttribute('data-theme', newTheme)
    var roots = document.querySelectorAll('.page-root')
    roots.forEach(function(r) { r.setAttribute('data-theme', newTheme) })
    var icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = newTheme === 'dark' ? '🌙' : '☀️'
    localStorage.setItem('xc_theme', newTheme)
  } catch(_) {}
  emit('toggle-theme')
}

// ── 【核心】导航函数 — Round 9: 首页用 #/ 而非 #/pages/index/index ──
// 历史教训:
//   Round 1-3: navigator/text/tap → uni-app H5 事件丢失
//   Round 4-5: <a href> → uni-app 框架全局拦截 <a> 点击
//   Round 6: window.location.hash → hash 变了但 DOM 不更新(Vue 3.4.21 render effect bug)
//   Round 7: uni.reLaunch → v20e patch 用了 currentRoute 而非 target path → 跳回原页
//   Round 8: 直接设 hash + reload, 但 HASH_TO_TAB 把首页映射成 /pages/index/index → 白屏
//   Round 9: 首页用真实路由路径 #/ (uni-app 中首页路由注册为 path:"/")
//            其他 tabBar 页面用 #/pages/xxx/index (它们在 __uniRoutes 中 path 就是 /pages/xxx/index)
var TAB_PATHS = ['/', '/pages/qimen/index', '/pages/bazi-index/index', '/pages/tarot/index', '/pages/liuyao/index', '/pages/meihua/index', '/pages/ziwei/index', '/pages/zeji/index', '/pages/calendar/index', '/pages/community/index', '/pages/profile/index', '/pages/about/index', '/pages/points/index']
var TAB_ROUTES = ['pages/index/index', 'pages/qimen/index', 'pages/bazi-index/index', 'pages/tarot/index', 'pages/liuyao/index', 'pages/meihua/index', 'pages/ziwei/index', 'pages/zeji/index', 'pages/calendar/index', 'pages/community/index', 'pages/profile/index', 'pages/about/index', 'pages/points/index']
function isOnTabPage() {
  try {
    var pages = getCurrentPages()
    if (pages && pages.length > 0) {
      var route = pages[pages.length - 1].route || ''
      return TAB_ROUTES.indexOf(route) > -1
    }
  } catch(_) {}
  return false
}

function go(hash) {
  var raw = hash.replace('#', '') || '/'
  var pathOnly = raw.split('?')[0]
  var queryStr = raw.indexOf('?') > -1 ? raw.substring(raw.indexOf('?')) : ''
  var uniPath = pathOnly === '/' ? '/pages/index/index' : pathOnly
  var fullPath = uniPath + queryStr
  var isTab = TAB_PATHS.indexOf(pathOnly) > -1

  // 从其他术数页点“八字排盘”时，优先回到本次会话最后看的八字结果页。
  // 只使用 window 变量，刷新页面后失效，避免把旧结果永久记住。
  try {
    var currentRoute = getCurrentRoute()
    var lastBaziResult = window.__xc_lastBaziResultRoute || ''
    if (
      pathOnly === '/pages/bazi-index/index' &&
      queryStr.indexOf('tab=free') > -1 &&
      lastBaziResult.indexOf('/pages/bazi-result/index') === 0 &&
      currentRoute.indexOf('/pages/bazi-index/index') !== 0 &&
      currentRoute.indexOf('/pages/bazi-result/index') !== 0
    ) {
      uni.navigateTo({ url: lastBaziResult })
      return
    }
  } catch(_) {}

  if (queryStr) {
    try { sessionStorage.setItem('_nav_query', queryStr) } catch(_) {}
  }

  if (isTab) {
    uni.switchTab({
      url: uniPath,
      success: function() {
        // 切换 tab 后立即同步导航高亮+溢出检测，不依赖 300ms setInterval 轮询
        syncNavHighlight()
        updateNavOverflow()
        if (queryStr) {
          setTimeout(function() { try { uni.$emit('nav-query', queryStr) } catch(_) {} }, 200)
        }
      }
    })
  } else {
    uni.navigateTo({ url: fullPath })
  }
}

// ── 当前路由检测（以 URL hash 为准） ──
// uni-app H5 tabBar 下 getCurrentPages() 返回过时数据（所有 tab 共享同一 page 实例），
// 因此以 window.location.hash 为唯一真实来源。
function getCurrentRoute() {
  try {
    var hash = window.location.hash.replace('#', '') || '/'
    var pathOnly = hash.split('?')[0]
    return pathOnly === '/' ? '/pages/index/index' : pathOnly
  } catch (_) {}
  return ''
}

const currentRoute = ref('')
currentRoute.value = getCurrentRoute()

try {
  // #ifdef H5
  if (!window.__topnavRoutePolling) {
    window.__topnavRoutePolling = true
    let lastRoute = ''
    setInterval(() => {
      const r = getCurrentRoute()
      if (r && r !== lastRoute) { lastRoute = r; currentRoute.value = r; syncNavHighlight() }
    }, 300)
  }
  // #endif
} catch (_) {}

function isCurrent(pathPrefix) {
  if (!currentRoute.value) {
    currentRoute.value = getCurrentRoute()
  }
  return currentRoute.value.indexOf(pathPrefix) === 0
}

// ── 按钮栏溢出检测（处理所有 TopNav 实例） ──
function updateNavOverflow() {
  document.querySelectorAll('#navBtnBar').forEach(function(bar, idx) {
    var more = bar.querySelector('#navBtnMore')
    var moreMenu = bar.querySelector('#navBtnMoreMenu')
    if (!bar || !more || !moreMenu) return

    bar.querySelectorAll('.nav-btn:not(.nav-btn-more)').forEach(function(b) {
      b.style.display = ''
    })
    more.style.display = 'none'
    moreMenu.innerHTML = ''

    var sidebarBtn = bar.parentNode ? bar.parentNode.querySelector('.topnav-sidebar-btn') : null
    var topnavRight = bar.parentNode ? bar.parentNode.querySelector('.topnav-right') : null
    var rightWidth = topnavRight ? topnavRight.getBoundingClientRect().width : 0
    var sidebarWidth = sidebarBtn ? sidebarBtn.getBoundingClientRect().width : 0
    var viewportWidth = window.innerWidth
    var barMaxRight = viewportWidth - Math.max(rightWidth, 0) - sidebarWidth - 20

    var allBtns = []
    bar.querySelectorAll('.nav-btn:not(.nav-btn-more)').forEach(function(btn) {
      allBtns.push(btn)
    })

    var overflow = []
    for (var i = allBtns.length - 1; i >= 0; i--) {
      if (allBtns[i].getBoundingClientRect().right > barMaxRight) {
        overflow.unshift(allBtns[i])
      }
    }

    if (overflow.length > 0) {
      overflow.forEach(function(btn) {
        btn.style.display = 'none'
        var clone = document.createElement('view')
        clone.className = 'nav-btn-drop-item'
        clone.setAttribute('data-href', btn.getAttribute('data-href'))
        clone.textContent = btn.textContent.replace(' ▾','').trim()
        clone.style.cssText = 'display:block;padding:8px 16px;font-size:0.78rem;color:var(--text-1);cursor:pointer;white-space:nowrap;transition:background 0.15s,color 0.15s'
        clone.onmouseenter = function() { this.style.background = 'var(--accent-glow)'; this.style.color = 'var(--accent)' }
        clone.onmouseleave = function() { this.style.background = ''; this.style.color = 'var(--text-1)' }
        clone.onclick = function(e) {
          var href = clone.getAttribute('data-href')
          if (window._xc_dropItemGo) {
            window._xc_dropItemGo(e, href)
          } else {
            e.stopPropagation()
            more.classList.remove('open')
            if (href) go(href)
          }
        }
        moreMenu.appendChild(clone)
      })
      more.style.display = ''
    } else {
      more.style.display = 'none'
    }
  })
}

function toggleMoreMenu(ev) {
  // 从点击事件找到当前实例的"更多"按钮
  var more = ev && ev.currentTarget
  if (!more) more = document.querySelector('#navBtnBar #navBtnMore')
  if (more) {
    var menu = more.querySelector('#navBtnMoreMenu')
    // 如果下拉菜单没有子项，不打开空菜单
    if (menu && menu.children.length === 0) return
    more.classList.contains('open') ? more.classList.remove('open') : more.classList.add('open')
  }
}

// ── 路由变化时同步导航高亮（DOM classList 替代 :class 绑定） ──
// ⚠️ uni-app custom tabBar 下每个 tab 页面各有一份 TopNav 组件实例（共 11 个），
// document.getElementById() 只返回第一个实例的元素，导致高亮只更新隐藏页面的导航。
// 必须用 querySelectorAll 遍历所有实例，确保用户看到的导航也被更新。
function syncNavHighlight() {
  var route = getCurrentRoute()
  if (!route) return

  // 清除所有按钮高亮
  document.querySelectorAll('.nav-btn.current, .nav-btn-drop-item.menu-active').forEach(function(el) {
    el.classList.remove('current', 'menu-active')
  })

  // 通过 data-href 匹配当前路由（精确匹配，避免 "#/" 匹配所有路由）
  document.querySelectorAll('.nav-btn[data-href], .nav-btn-drop-item[data-href]').forEach(function(el) {
    var href = el.getAttribute('data-href') || ''
    var target = href.replace('#/', '/pages/')  // "#/pages/..." → "/pages/..."
    if (href === '#/') target = '/pages/index/index'  // 首页
    if (target && route === target) {
      el.classList.add('current')
      el.classList.add('menu-active')
    }
  })
  // 八字结果页也高亮八字导航
  if (route.indexOf('/pages/bazi-result') === 0 || route.indexOf('/pages/bazi-index') === 0) {
    document.querySelectorAll('.nav-btn[data-href*="bazi-index"]').forEach(function(el) { el.classList.add('current') })
  }
  // 奇门 tab 参数也高亮奇门导航
  if (route.indexOf('/pages/qimen/index') === 0) {
    document.querySelectorAll('.nav-btn[data-href*="qimen"]').forEach(function(el) { el.classList.add('current') })
  }
}

defineExpose({ getCurrentRoute, go })

// ── onMounted: 原生 DOM 事件委托兜底 ──
// 原因: uni-app H5 的 <view @click> 编译后用 Vue 内部事件系统，
// 模拟点击 (dispatchEvent/native click) 无法触发。
// 但真人点击可以触发 Vue 事件代理。
// 此处添加 data-href + 原生 capture 事件监听，确保即使 Vue 事件不响应也能跳转。
onMounted(() => {
  // #ifdef H5
  window.__topNavGo = go
  window.__topNavGo.avatarLoad = loadAvatar

  var _xc_applyFrost = function(el) {
    if (!el) return
    var parent = el.parentElement
    var isMoreMenu = parent && parent.classList && parent.classList.contains('nav-btn-more')
    if (window.innerWidth > 768 && !isMoreMenu) return
    if (parent && parent !== document.body) {
      el._xc_origParent = parent
      el._xc_origNext = el.nextElementSibling
      document.body.appendChild(el)
    }
    el.style.setProperty('display', 'block', 'important')
    el.style.setProperty('position', 'fixed', 'important')
    el.style.setProperty('background', 'rgba(255,255,255,0.65)', 'important')
    el.style.setProperty('border-color', 'rgba(255,255,255,0.3)', 'important')
    el.style.setProperty('border-radius', '20px', 'important')
    el.style.setProperty('box-shadow', '0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.4)', 'important')
    el.style.setProperty('-webkit-backdrop-filter', 'blur(20px) saturate(180%)', 'important')
    el.style.setProperty('backdrop-filter', 'blur(20px) saturate(180%)', 'important')
    el.style.setProperty('z-index', '9999', 'important')
    el.style.setProperty('padding', '6px 0', 'important')
    el.style.setProperty('color', '#333', 'important')
    el.style.setProperty('visibility', 'visible', 'important')
    el.style.setProperty('opacity', '1', 'important')
    el.style.setProperty('pointer-events', 'auto', 'important')

    if (el.id === 'avatarDropdown') {
      if (el._xc_origParent) {
        var rect = el._xc_origParent.getBoundingClientRect()
        el.style.setProperty('top', (rect.bottom + 8) + 'px', 'important')
        el.style.setProperty('right', (window.innerWidth - rect.right) + 'px', 'important')
        el.style.setProperty('left', 'auto', 'important')
        el.style.setProperty('transform', 'translateZ(0)', 'important')
      }
    } else if (isMoreMenu || (el._xc_origParent && el._xc_origParent.classList && el._xc_origParent.classList.contains('nav-btn-more'))) {
      var moreAnchor = el._xc_origParent || parent
      var moreRect = moreAnchor ? moreAnchor.getBoundingClientRect() : null
      var vw = window.innerWidth || document.documentElement.clientWidth || 0
      var vh = window.innerHeight || document.documentElement.clientHeight || 0
      var gap = 10
      var pageZoom = 1
      try { pageZoom = parseFloat(window.getComputedStyle(document.body).zoom) || 1 } catch(_) {}
      var top = moreRect ? Math.max(52, moreRect.bottom + 8) : 60
      var maxHeight = Math.max(140, vh - top - gap)
      el.style.setProperty('min-width', '160px', 'important')
      el.style.setProperty('max-width', 'min(240px, calc(100vw - 20px))', 'important')
      el.style.setProperty('max-height', (maxHeight / pageZoom) + 'px', 'important')
      el.style.setProperty('overflow-y', 'auto', 'important')
      el.style.setProperty('overflow-x', 'hidden', 'important')
      var menuWidth = Math.min(Math.max(el.getBoundingClientRect().width || 160, 160), Math.max(160, vw - gap * 2))
      var left = moreRect ? (moreRect.right - menuWidth) : (vw - menuWidth - gap)
      left = Math.max(gap, Math.min(left, vw - menuWidth - gap))
      el.style.setProperty('top', (top / pageZoom) + 'px', 'important')
      el.style.setProperty('left', (left / pageZoom) + 'px', 'important')
      el.style.setProperty('right', 'auto', 'important')
      el.style.setProperty('transform', 'translateZ(0)', 'important')
    } else {
      el.style.setProperty('top', '60px', 'important')
      el.style.setProperty('left', '50%', 'important')
      el.style.setProperty('transform', 'translateX(-50%) translateZ(0)', 'important')
    }
  }

  var _xc_restoreMenu = function(el) {
    if (!el) return
    el.style.removeProperty('display')
    el.style.removeProperty('position')
    el.style.removeProperty('top')
    el.style.removeProperty('left')
    el.style.removeProperty('right')
    el.style.removeProperty('transform')
    el.style.removeProperty('background')
    el.style.removeProperty('border-color')
    el.style.removeProperty('border-radius')
    el.style.removeProperty('box-shadow')
    el.style.removeProperty('-webkit-backdrop-filter')
    el.style.removeProperty('backdrop-filter')
    el.style.removeProperty('min-width')
    el.style.removeProperty('max-width')
    el.style.removeProperty('max-height')
    el.style.removeProperty('overflow-y')
    el.style.removeProperty('overflow-x')
    el.style.removeProperty('z-index')
    el.style.removeProperty('padding')
    el.style.removeProperty('color')
    el.style.removeProperty('visibility')
    el.style.removeProperty('opacity')
    el.style.removeProperty('pointer-events')
    if (el._xc_origParent) {
      var origParent = el._xc_origParent
      var origNext = el._xc_origNext
      if (origNext && origNext.parentElement === origParent) {
        origParent.insertBefore(el, origNext)
      } else {
        origParent.appendChild(el)
      }
      el._xc_origParent = null
      el._xc_origNext = null
    }
  }

  if (!window.__xcDropInited) {
    window.__xcDropInited = true

    var _xc_closeAllDropdowns = function() {
      document.querySelectorAll('.nav-btn-has-drop.open, .nav-btn-more.open, #avatarDropdown').forEach(function(d) {
        d.classList.remove('open')
      })
      document.querySelectorAll('.nav-btn-drop-menu, #avatarDropdown').forEach(function(m) {
        if (m._xc_origParent) _xc_restoreMenu(m)
      })
    }
    window._xc_closeAllDropdowns = _xc_closeAllDropdowns

    window._xc_toggleDrop = function(event) {
      event.stopPropagation()
      event.preventDefault()
      var el = event.currentTarget
      var wasOpen = el.classList.contains('open')
      _xc_closeAllDropdowns()
      if (!wasOpen) {
        el.classList.add('open')
        var menu = el.querySelector('.nav-btn-drop-menu')
        if (menu) _xc_applyFrost(menu)
      }
    }

    window._xc_toggleMore = function(event) {
      event.stopPropagation()
      event.preventDefault()
      var el = event && event.currentTarget
      if (!el || !el.classList) el = document.querySelector('#navBtnBar #navBtnMore')
      if (!el) return
      var wasOpen = el.classList.contains('open')
      _xc_closeAllDropdowns()
      if (!wasOpen) {
        el.classList.add('open')
        var menu = el.querySelector('.nav-btn-drop-menu')
        if (menu) _xc_applyFrost(menu)
      }
    }

    window._xc_dropItemGo = function(event, href) {
      event.stopPropagation()
      event.preventDefault()
      _xc_closeAllDropdowns()
      if (href) go(href)
    }

    document.addEventListener('click', function(e) {
      var el = e.target
      for (var d = 10; el && d > 0; d--) {
        if (el.classList && (el.classList.contains('nav-btn-has-drop') || el.classList.contains('nav-btn-more'))) return
        if (el.classList && el.classList.contains('nav-btn-drop-menu')) return
        if (el.id === 'navBtnMore' || el.id === 'avatarDropdown') return
        if (el.classList && el.classList.contains('nav-avatar-wrap')) return
        if (el.classList && el.classList.contains('avatar-dropdown-item')) return
        if (el.dataset && el.dataset.href) {
          e.preventDefault()
          e.stopPropagation()
          _xc_closeAllDropdowns()
          go(el.dataset.href)
          return
        }
        el = el.parentElement
      }
      _xc_closeAllDropdowns()
    }, true)

    document.addEventListener('touchstart', function(e) {
      var el = e.target
      for (var d = 10; el && d > 0; d--) {
        if (el.classList && (el.classList.contains('nav-btn-has-drop') || el.classList.contains('nav-btn-more'))) return
        if (el.classList && el.classList.contains('nav-btn-drop-menu')) return
        if (el.id === 'navBtnMore' || el.id === 'avatarDropdown') return
        if (el.classList && el.classList.contains('nav-avatar-wrap')) return
        if (el.classList && el.classList.contains('avatar-dropdown-item')) return
        el = el.parentElement
      }
      _xc_closeAllDropdowns()
    }, true)
  }
  // 初始路由高亮同步
  nextTick(() => { syncNavHighlight(); updateNavOverflow() })
  // 等布局稳定后再检测一次，防止字体加载导致的测量偏差
  setTimeout(updateNavOverflow, 500)
  // 窗口 resize 时重新检测按钮溢出（仅注册一次，避免多实例重复监听）
  if (!window.__topnavResizeDelegated) {
    window.__topnavResizeDelegated = true
    window.addEventListener('resize', function() {
      if (window._xc_closeAllDropdowns) window._xc_closeAllDropdowns()
      updateNavOverflow()
    })
  }
  // 初始主题DOM同步（render effect bug: :data-theme 不响应）
  try {
    document.documentElement.setAttribute('data-theme', props.theme)
    var root = document.querySelector('.page-root')
    if (root) root.setAttribute('data-theme', props.theme)
    var icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = props.theme === 'dark' ? '🌙' : '☀️'
  } catch(_) {}
  // #endif
  // 加载头像
  loadAvatar()
  // 加载积分
  loadPointsSummary()
  // 全局头像事件委托 - 使用 mouseenter/mouseleave 防止闪烁消失
  if (!window.__avatarDelegated) {
    window.__avatarDelegated = true
    document.addEventListener('mouseover', function(e) {
      for (var el = e.target; el; el = el.parentElement) {
        if (el.classList && el.classList.contains('nav-avatar-trigger-global')) {
          // 同一 wrap 内的 dropdown
          var wrap = el.closest('.nav-avatar-wrap')
          if (wrap) {
            var dd = wrap.querySelector('#avatarDropdown')
            if (dd) {
              var wasOpen = dd.classList.contains('open')
              _xc_closeAllDropdowns()
              dd.classList.add('open')
              _xc_applyFrost(dd)
            }
          }
          if (!window.__avatarLoaded) loadAvatar()
          return
        }
      }
    }, true)
    document.addEventListener('click', function(e) {
      for (var el = e.target; el; el = el.parentElement) {
        if (el.classList && el.classList.contains('avatar-dropdown-action')) {
          e.preventDefault()
          e.stopPropagation()
          if (el.dataset.action === 'logout') {
            window._xc_doLogout()
          } else if (el.dataset.href) {
            go(el.dataset.href)
          }
          return
        }
        if (el.classList && (el.classList.contains('nav-avatar-trigger-global') || el.classList.contains('nav-avatar-wrap') || el.id === 'avatarDropdown')) return
      }
      document.querySelectorAll('#avatarDropdown').forEach(function(x) {
        x.classList.remove('open')
        if (x._xc_origParent) _xc_restoreMenu(x)
      })
    }, true)
    // 移动端 nav-dropdown 点击切换（移动端无 hover）
    document.addEventListener('touchstart', function(e) {
      var touchedAvatar = false
      var clickedDropdownItem = false
      for (var el = e.target; el; el = el.parentElement) {
        if (el.classList && el.classList.contains('avatar-dropdown-action')) {
          e.preventDefault()
          e.stopPropagation()
          touchedAvatar = true
          clickedDropdownItem = true
          if (el.dataset.action === 'logout') {
            window._xc_doLogout()
          } else if (el.dataset.href) {
            go(el.dataset.href)
          }
          break
        }
        if (el.id === 'avatarDropdown') {
          clickedDropdownItem = true
          touchedAvatar = true
          break
        }
        if (el.classList && el.classList.contains('nav-drop-trigger')) {
          var dropdown = el.closest('.nav-dropdown')
          if (dropdown) {
            var isOpen = dropdown.classList.contains('open')
            document.querySelectorAll('.nav-dropdown.open').forEach(function(d) { d.classList.remove('open') })
            if (!isOpen) {
              dropdown.classList.add('open')
              var dm = dropdown.querySelector('.nav-dropdown-menu')
              if (dm) _xc_applyFrost(dm)
            }
          }
          return
        }
        if (el.classList && el.classList.contains('nav-avatar-trigger-global')) {
          touchedAvatar = true
          var wrap = el.closest('.nav-avatar-wrap')
          if (wrap) {
            var dd = wrap.querySelector('#avatarDropdown')
            if (dd) {
              var wasOpen = dd.classList.contains('open')
              _xc_closeAllDropdowns()
              if (!wasOpen) {
                dd.classList.add('open')
                _xc_applyFrost(dd)
              }
            }
          }
          if (!window.__avatarLoaded) loadAvatar()
          e.preventDefault()
          e.stopPropagation()
          return
        }
      }
      if (clickedDropdownItem) {
        e.preventDefault()
        e.stopPropagation()
        return
      }
      if (!touchedAvatar) {
        document.querySelectorAll('#avatarDropdown').forEach(function(x) {
          x.classList.remove('open')
          if (x._xc_origParent) _xc_restoreMenu(x)
        })
      }
    }, true)
    document.addEventListener('click', function(e) {
      for (var el = e.target; el; el = el.parentElement) {
        if (el.classList && el.classList.contains('nav-drop-trigger')) {
          var dropdown = el.closest('.nav-dropdown')
          if (dropdown) {
            var isOpen = dropdown.classList.contains('open')
            document.querySelectorAll('.nav-dropdown.open').forEach(function(d) { d.classList.remove('open') })
            if (!isOpen) {
              dropdown.classList.add('open')
              var dm = dropdown.querySelector('.nav-dropdown-menu')
              if (dm) _xc_applyFrost(dm)
            }
          }
          return
        }
      }
    }, true)
  }
  // 全局退出登录函数
  if (!window._xc_doLogout) {
    window._xc_doLogout = function() {
      uni.request({ url: '/api/logout', method: 'POST' }).then(function() {
        uni.removeStorageSync('xc_token'); uni.removeStorageSync('xc_user')
        window.location.reload()
      }).catch(function() {
        uni.removeStorageSync('xc_token'); uni.removeStorageSync('xc_user')
        window.location.reload()
      })
    }
  }
  // 创建登录弹窗原生输入框
  try {
    var modalInputs = [
      { wrap: 'tnLoginUser-wrap', id: 'tnLoginUser', type: 'text', placeholder: '用户名' },
      { wrap: 'tnLoginPass-wrap', id: 'tnLoginPass', type: 'text', placeholder: '密码', isPassword: true },
      { wrap: 'tnLoginPhone-wrap', id: 'tnLoginPhone', type: 'text', placeholder: '手机号' },
      { wrap: 'tnLoginPhoneCode-wrap', id: 'tnLoginPhoneCode', type: 'text', placeholder: '验证码' },
      { wrap: 'tnLoginEmail-wrap', id: 'tnLoginEmail', type: 'text', placeholder: 'QQ邮箱地址' },
      { wrap: 'tnLoginEmailCode-wrap', id: 'tnLoginEmailCode', type: 'text', placeholder: '验证码' },
    ]
    modalInputs.forEach(function(item) {
      var w = document.getElementById(item.wrap)
      if (w) {
        if (document.getElementById(item.id)) return
        var inp = document.createElement('input')
        inp.type = item.type
        inp.id = item.id
        inp.placeholder = item.placeholder
        inp.className = 'field-input'
        inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;'
        if (item.isPassword) inp.style.cssText += '-webkit-text-security:disc;-moz-text-security:disc;text-security:disc;'
        w.appendChild(inp)
      }
    })
  } catch(_) {}
})
</script>

<style scoped>
/* ═══ 容器 ═══ */
.topnav-wrap { position: fixed; top: 0; left: 0; right: 0; z-index: 100; }

/* ═══ 顶部导航栏 ═══ */
.topnav {
  top: 0;
  z-index: 100;
  background: var(--nav-bg);
  backdrop-filter: blur(40px) saturate(1.4);
  display: flex;
  align-items: center;
  height: 60px;
  padding: 0 24px;
  border-bottom: 1px solid var(--card-border);
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', 'Helvetica Neue', sans-serif;
  font-weight: 400;
}
.topnav-solid {
  background: var(--nav-bg) !important;
  border-bottom-color: var(--card-border);
  box-shadow: 0 1px 12px rgba(0,0,0,0.15);
}
[data-theme="light"] .topnav-solid {
  background: var(--nav-bg) !important;
  box-shadow: 0 1px 8px rgba(0,0,0,0.06);
}

/* ═══ 单行：☰ + 按钮栏 + 右侧 ═══ */
.topnav-row {
  display: flex;
  align-items: center;
  height: 60px;
  flex:1;
  min-width:0;
}
.topnav-sidebar-btn { display:flex; font-size:1.4rem; color:var(--text-2); cursor:pointer; padding:0 10px; margin-right:4px; flex-shrink:0; align-items:center; justify-content:center; border-radius:8px; width:40px; height:40px; line-height:1; margin-top:-5px; }
.topnav-sidebar-btn:hover { background:var(--accent-glow); }
.topnav-logo {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Songti SC', 'Noto Serif SC', 'STSong', serif;
  font-size: 1rem;
  letter-spacing: 3px;
  color: var(--text-1);
  white-space: nowrap;
  text-decoration: none;
  flex-shrink: 0;
  cursor: pointer;
}
.topnav-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: auto;
  z-index: 10;
}

/* ═══ 第 2 行：按钮栏 ═══ */
.nav-btn-bar {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 2px;
  flex: 1 1 0;
  min-width: 0;
  overflow: visible;
}
.nav-btn {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 7px;
  font-size: 1rem;
  color: var(--text-2);
  white-space: nowrap;
  letter-spacing: 0.5px;
  transition: color 0.2s, background 0.2s;
  cursor: pointer;
  position: relative;
  flex-shrink: 0;
}
.nav-btn:hover { background: var(--accent-glow); color: var(--accent); }
.nav-btn.current {
  background: var(--accent-glow);
  color: var(--accent);
  font-weight: 600;
}

/* 带下拉的按钮 */
.nav-btn-has-drop { position: relative; }
.nav-btn-drop-menu {
  visibility: hidden;
  opacity: 0;
  position: absolute;
  top: 100%;
  left: 50%;
  transform: translateX(-50%) translateY(4px);
  min-width: 160px;
  background: rgba(48, 53, 76, 0.94);
  border: 1px solid rgba(255,255,255,0.14);
  border-radius: 10px;
  padding: 6px 0;
  z-index: 200;
  box-shadow: 0 8px 32px rgba(0,0,0,0.25);
  pointer-events: none;
  -webkit-backdrop-filter: blur(20px) saturate(1.6);
  backdrop-filter: blur(20px) saturate(1.6);
  transition: opacity 0.2s ease, transform 0.2s ease, visibility 0.2s;
}
[data-theme="light"] .nav-btn-drop-menu {
  background: rgba(255, 253, 248, 0.94);
  border: 1px solid rgba(0,0,0,0.07);
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
}
.nav-btn-has-drop.open .nav-btn-drop-menu,
.nav-btn-more.open .nav-btn-drop-menu {
  visibility: visible;
  opacity: 1;
  pointer-events: auto;
  transform: translateX(-50%) translateY(2px);
}
.nav-btn-drop-item {
  display: block;
  padding: 8px 16px;
  font-size: 0.78rem;
  color: var(--text-2);
  cursor: pointer;
  white-space: nowrap;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: background 0.15s, color 0.15s;
}
.nav-btn-drop-item:hover { background: var(--accent-glow); color: var(--accent); }
.nav-btn-drop-item.current,
.nav-btn-drop-item.menu-active { color: var(--accent); font-weight: 600; }

/* "更多"按钮 */
.nav-btn-more { position: relative; }
.nav-btn-more .nav-btn-drop-menu {
  left: auto;
  right: 0;
  max-width: min(240px, calc(100vw - 20px));
  max-height: calc(100dvh - 70px);
  overflow-y: auto;
  overflow-x: hidden;
  transform: translateY(4px);
}
.nav-btn-more.open .nav-btn-drop-menu { transform: translateY(2px); }
body > #navBtnMoreMenu.nav-btn-drop-menu {
  transform: translateZ(0) !important;
  max-width: min(240px, calc(100vw - 20px));
  max-height: calc(100dvh - 70px);
  overflow-y: auto;
  overflow-x: hidden;
}

/* 按钮 */
.btn {
  padding: 5px 14px;
  border-radius: 8px;
  font-size: 0.75rem;
  cursor: pointer;
  border: none;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  text-decoration: none;
}
.btn-outline { background: transparent; border: 1px solid var(--card-border); color: var(--text-2); }
.btn-accent { background: var(--accent); color: #fff; }
.btn-sm { padding: 6px 14px; font-size: 0.9rem; border-radius: 7px; }
.nav-profile-btn {
  display: inline-flex;
  align-items: center;
  padding: 6px 12px;
  border-radius: 7px;
  font-size: 1rem;
  color: var(--text-2);
  white-space: nowrap;
  cursor: pointer;
}
.theme-toggle-nav {
  background: none;
  border: none;
  color: var(--text-3);
  cursor: pointer;
  font-size: 1.25rem;
  padding: 4px;
}

/* ═══ 用户头像 ═══ */
.nav-avatar-wrap { position: relative; display: flex; align-items: center; cursor: pointer; margin-left: 8px; }
.nav-avatar-inner { width: 38px; height: 38px; border-radius: 50%; overflow: hidden; background: rgba(255,255,255,0.08); display: flex; align-items: center; justify-content: center; border: 1px solid rgba(255,255,255,0.12); }
.nav-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.nav-avatar-text { font-size: 0.95rem; font-weight: 700; color: var(--text-3); }
.nav-avatar-dropdown { position: absolute; top: 100%; right: 0; margin-top: 8px; background: rgba(48, 53, 76, 0.94); border: 1px solid rgba(255,255,255,0.14); border-radius: 10px; padding: 4px 0; min-width: 120px; display: none; box-shadow: 0 8px 32px rgba(0,0,0,0.25); z-index: 200; -webkit-backdrop-filter: blur(20px) saturate(1.6); backdrop-filter: blur(20px) saturate(1.6); }
[data-theme="light"] .nav-avatar-dropdown { background: rgba(255, 253, 248, 0.94); border: 1px solid rgba(0,0,0,0.07); box-shadow: 0 8px 32px rgba(0,0,0,0.1); }
.nav-avatar-dropdown.open { display: block; }
.avatar-dropdown-item { padding: 10px 16px; font-size: 0.78rem; color: var(--text-2); cursor: pointer; white-space: nowrap; }
.avatar-dropdown-item:hover { background: var(--accent-glow); color: var(--accent); }
.points-display { display: flex; align-items: center; justify-content: space-between; cursor: default; }
.points-display:hover { background: transparent; color: var(--text-2); }
.points-label { font-size: 0.78rem; color: var(--text-3); }
.points-badge { font-size: 0.82rem; font-weight: 700; color: var(--accent); }
.avatar-dropdown-divider { height: 1px; background: var(--card-border); margin: 2px 0; }

/* ═══ 登录/注册弹窗 ═══ */
.modal-overlay { position: fixed; inset: 0; z-index: 999; background: rgba(20,16,10,0.48); display: none; align-items: center; justify-content: center; -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px); }
.modal-overlay.open { display: flex; }
.modal-box { background: rgba(31, 29, 24, 0.94); border: 1px solid rgba(178,149,93,0.20); border-radius: 20px; padding: 28px 32px; max-width: 400px; width: 90%; box-shadow: 0 24px 80px rgba(0,0,0,0.38), inset 0 1px 0 rgba(255,255,255,0.08); -webkit-backdrop-filter: blur(28px) saturate(1.45); backdrop-filter: blur(28px) saturate(1.45); }
[data-theme="light"] .modal-box { background: rgba(255, 253, 248, 0.96); border: 1px solid rgba(178,149,93,0.18); box-shadow: 0 24px 80px rgba(60,40,15,0.16), inset 0 1px 0 rgba(255,255,255,0.85); }
.modal-title { font-family: var(--font-serif); font-size: 1.2rem; text-align: center; color: var(--text-1); margin-bottom: 20px; letter-spacing: 2px; }
.field { margin-bottom: 14px; }
.field-label { font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; display: block; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 12px; background: var(--input-bg); border: 1px solid rgba(178,149,93,0.16); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; transition: border-color .18s ease, box-shadow .18s ease, background .18s ease; }
.field-input:focus { border-color: rgba(178,149,93,0.54); box-shadow: 0 0 0 3px rgba(178,149,93,0.10); }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }
.oauth-divider { display: flex; align-items: center; margin: 16px 0 12px; }
.oauth-divider::before, .oauth-divider::after { content: ''; flex: 1; height: 1px; background: var(--card-border); }
.oauth-divider-text { font-size: 0.72rem; color: var(--text-3); padding: 0 12px; white-space: nowrap; }
.oauth-btns { display: flex; gap: 10px; }
.oauth-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 10px; border-radius: 12px; border: 1px solid rgba(178,149,93,0.16); cursor: pointer; transition: all 0.2s; background: var(--input-bg); }
.oauth-btn:hover { border-color: var(--accent); background: var(--accent-glow); }
.oauth-btn-qq .oauth-btn-icon { width: 24px; height: 24px; border-radius: 50%; background: #12b7f5; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.62rem; font-weight: 700; flex-shrink: 0; }
.oauth-btn-wechat .oauth-btn-icon { width: 24px; height: 24px; border-radius: 6px; background: #07c160; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.62rem; font-weight: 700; flex-shrink: 0; }
.oauth-btn-label { font-size: 0.78rem; color: var(--text-2); }
.oauth-btn-gitee .oauth-btn-icon { width: 24px; height: 24px; border-radius: 50%; background: #c71d23; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; flex-shrink: 0; }
.login-tabs { display: flex; gap: 4px; margin-bottom: 16px; background: rgba(178,149,93,0.09); border: 1px solid rgba(178,149,93,0.12); border-radius: 12px; padding: 3px; }
.login-tab { flex: 1; text-align: center; padding: 8px 0; border-radius: 9px; font-size: 0.78rem; color: var(--text-3); cursor: pointer; transition: all 0.2s; }
.login-tab.active { background: var(--accent); color: #fff; font-weight: 600; }
.code-field { margin-bottom: 10px; }
.code-btn { white-space: nowrap; flex-shrink: 0; }
.code-btn[disabled] { opacity: 0.5; pointer-events: none; }
.modal-hint { font-size: 0.7rem; color: var(--text-3); text-align: center; margin-top: 12px; line-height: 1.4; }

/* ═══ 响应式 ═══ */
@media (max-width: 768px) {
  .topnav { padding: 0 8px; }
  .topnav-right { margin-left: 0; flex-shrink: 0; gap: 4px; }
  .theme-toggle-nav { font-size: 1rem; padding: 2px 4px; }
  .nav-auth-btns .btn-sm { font-size: 0.8rem; padding: 4px 8px; }
  
  /* 完全按照 record-ctx-menu 手机版样式 */
  .nav-btn-drop-menu,
  .nav-avatar-dropdown {
    position: fixed !important;
    top: 60px !important;
    left: 50% !important;
    transform: translateX(-50%) translateZ(0) !important;
    background: rgba(28,32,52,0.98) !important;
    border-color: rgba(255,255,255,0.14) !important;
    border-radius: 20px !important;
    box-shadow: 0 14px 40px rgba(0,0,0,0.30), inset 0 1px 0 rgba(255,255,255,0.08) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    isolation: isolate !important;
    padding: 6px 0 !important;
    color: rgba(246,241,232,0.98) !important;
    z-index: 9999 !important;
  }
  .nav-btn-drop-item,
  .avatar-dropdown-item {
    color: rgba(246,241,232,0.96) !important;
  }
  .nav-btn-drop-item:hover,
  .avatar-dropdown-item:hover {
    background: rgba(178,149,93,0.16) !important;
    color: var(--accent) !important;
  }
  
  /* 覆盖主题切换的浅色样式 */
  [data-theme="light"] .nav-btn-drop-menu,
  [data-theme="light"] .nav-avatar-dropdown {
    background: rgba(255,255,255,0.65) !important;
    border-color: rgba(255,255,255,0.3) !important;
    border-radius: 20px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.12), inset 0 1px 0 rgba(255,255,255,0.4) !important;
    -webkit-backdrop-filter: blur(20px) saturate(180%) !important;
    backdrop-filter: blur(20px) saturate(180%) !important;
    isolation: isolate !important;
    padding: 6px 0 !important;
    color: #333 !important;
  }
  [data-theme="light"] .nav-btn-drop-item,
  [data-theme="light"] .avatar-dropdown-item {
    color: rgba(70,58,40,0.92) !important;
  }
}
@media (max-width: 480px) {
  .topnav-right { gap: 2px; }
  .theme-toggle-nav { font-size: 0.9rem; padding: 1px 2px; }
  .nav-auth-btns .btn-sm { font-size: 0.75rem; padding: 3px 6px; }
}

/* ═══ 登录弹窗移动端适配 ═══ */
@media (max-width: 480px) {
  .modal-box { padding: 20px 16px; border-radius: 16px; max-width: 100%; width: 92%; }
  .modal-title { font-size: 1rem; margin-bottom: 14px; }
  .field { margin-bottom: 10px; }
  .field-input { font-size: 0.8125rem; padding: 10px 12px; }
  .login-tabs { margin-bottom: 12px; }
  .login-tab { font-size: 0.75rem; padding: 7px 0; }
  .modal-btns { margin-top: 14px; gap: 8px; }
  .modal-btns .btn { font-size: 0.8125rem; padding: 10px; }
  .oauth-divider { margin: 12px 0 10px; }
  .oauth-btn { padding: 8px; }
  .oauth-btn-label { font-size: 0.72rem; }
  .code-btn { font-size: 0.72rem; padding: 8px 10px; }
}

</style>
