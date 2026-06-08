<template>
  <view class="topnav-wrap">
    <!-- 顶部固定导航 — 两行结构 -->
    <nav class="topnav topnav-solid">
      <!-- 单行：☰ + 按钮栏 + 右侧 -->
      <view class="topnav-sidebar-btn" id="topnavSidebarBtn" onclick="window._xc_toggleSidebar(event)" ontouchstart="window._xc_toggleSidebar(event)" onpointerdown="window._xc_toggleSidebar(event)">☰</view>
      <view class="nav-btn-bar" id="navBtnBar">
        <view class="nav-btn" data-href="#/?app=1" @click="goAsync('#/?app=1', $event)">时安agent</view>

        <view class="nav-btn nav-btn-has-drop" onclick="window._xc_toggleDrop(event)">
          术数工具 ▾
          <view class="nav-btn-drop-menu">
            <view class="nav-btn-drop-item" data-href="#/pages/qimen/index?tab=free" onclick="return window.__topNavGoAsync(event, '#/pages/qimen/index?tab=free')">奇门遁甲</view>
            <view class="nav-btn-drop-item" data-href="#/pages/bazi-index/index?tab=free" onclick="return window.__topNavGoAsync(event, '#/pages/bazi-index/index?tab=free')">八字排盘</view>
            <view class="nav-btn-drop-item" data-href="#/pages/liuyao/index" @click="goAsync('#/pages/liuyao/index', $event)">六爻排盘</view>
            <view class="nav-btn-drop-item" data-href="#/pages/meihua/index" @click="goAsync('#/pages/meihua/index', $event)">梅花易数</view>
            <view class="nav-btn-drop-item" data-href="#/pages/ziwei/index" @click="goAsync('#/pages/ziwei/index', $event)">紫微斗数</view>
            <view class="nav-btn-drop-item" data-href="#/pages/tarot/index" @click="goAsync('#/pages/tarot/index', $event)">塔罗牌</view>
            <view class="nav-btn-drop-item" data-href="#/pages/zeji/index" @click="goAsync('#/pages/zeji/index', $event)">择吉工具</view>
          </view>
        </view>
        <view class="nav-btn" data-href="#/pages/calendar/index" @click="goAsync('#/pages/calendar/index', $event)">专属日历</view>
        <view class="nav-btn" data-href="#/pages/user-management/index" @click="goAsync('#/pages/user-management/index', $event)">档案列表</view>
        <view class="nav-btn" data-href="#/pages/community/index" @click="goAsync('#/pages/community/index', $event)">社区</view>
        <view class="nav-btn" data-href="#/pages/about/index" @click="goAsync('#/pages/about/index', $event)">关于我们</view>

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
        <view class="nav-auth-btns" v-if="!localLoggedIn">
          <view class="btn btn-outline btn-sm" @click="openLoginFromNav" @tap="openLoginFromNav" onclick="window._openLoginModal && window._openLoginModal()">登录</view>
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
             <view class="avatar-dropdown-item avatar-dropdown-action" data-href="#/pages/user-management/index">档案列表 ›</view>
             <view class="avatar-dropdown-item avatar-dropdown-action" data-href="#/pages/points/index">积分中心 ›</view>
             <view class="avatar-dropdown-item avatar-dropdown-action admin-dropdown-item" id="avatarAdminEntry" data-href="#/pages/admin/index" style="display:none;">后台管理 ›</view>
             <view class="avatar-dropdown-divider"></view>
             <view class="avatar-dropdown-item avatar-dropdown-action" data-action="logout">退出登录</view>
           </view>
         </view>
      </view>
    </nav>
  </view>

  <!-- 登录弹窗 -->
  <view class="modal-overlay" id="topnavLoginModal" onclick="if(event.target===this) window._openLoginModal_Close()">
    <view class="modal-box">
      <view class="modal-title">登录</view>
      <view class="login-tabs">
        <view class="login-tab tn-tab-password active" data-tab="password" onclick="window._xc_switchTab(this)">密码登录</view>
        <view class="login-tab tn-tab-code" data-tab="code" onclick="window._xc_switchTab(this)">验证码登录</view>
      </view>

      <view class="tn-panel tn-panel-login" style="">
        <view class="field"><text class="field-label">账号</text><view id="tnLoginUser-wrap" class="dom-input-wrap"></view></view>
        <view class="field"><text class="field-label">密码</text><view id="tnLoginPass-wrap" class="dom-input-wrap"></view></view>
        <view class="field code-field" style="display:none;">
          <text class="field-label">验证码</text>
          <view style="display:flex;gap:8px;">
            <view id="tnLoginCode-wrap" class="dom-input-wrap" style="flex:1;"></view>
            <view class="btn btn-outline btn-sm code-btn" onclick="window._xc_sendLoginCode()" id="tnLoginCodeBtn">获取验证码</view>
          </view>
        </view>
        <view class="modal-hint">没有账号？<text class="register-link" onclick="window._xc_doRegister()" style="color:var(--accent);cursor:pointer;text-decoration:underline;">立即注册</text> · <text class="forgot-link" onclick="window._xc_showForgotPassword()" style="color:var(--accent);cursor:pointer;text-decoration:underline;">忘记密码</text></view>
      </view>

      <!-- 忘记密码 -->
      <view class="tn-panel tn-panel-reset" style="display:none;">
        <view class="reset-methods">
          <view class="reset-method active" data-method="email" onclick="window._xc_switchResetMethod(this)">邮箱</view>
        </view>
        <view class="field"><text class="field-label" id="tnResetTargetLabel">邮箱</text><view id="tnResetTarget-wrap" class="dom-input-wrap"></view></view>
        <view class="field code-field">
          <text class="field-label">验证码</text>
          <view style="display:flex;gap:8px;">
            <view id="tnResetCode-wrap" class="dom-input-wrap" style="flex:1;"></view>
            <view class="btn btn-outline btn-sm code-btn" onclick="window._xc_sendResetCode()" id="tnResetCodeBtn">获取验证码</view>
          </view>
        </view>
        <view class="field"><text class="field-label">新密码</text><view id="tnResetPassword-wrap" class="dom-input-wrap"></view></view>
        <view class="modal-hint">想起来了？<text class="login-link" onclick="window._xc_switchToLogin()" style="color:var(--accent);cursor:pointer;text-decoration:underline;">返回登录</text></view>
      </view>

      <view class="modal-error" id="tnLoginError"></view>
      <view class="modal-btns"><view class="btn btn-outline" onclick="window._openLoginModal_Close()">取消</view><view class="btn btn-accent" onclick="window._xc_doLogin()">登录</view></view>
      <view class="oauth-divider"><text class="oauth-divider-text">第三方登录</text></view>
      <view class="oauth-note">已绑定 Gitee 的账号，登录时仍需通过 Gitee 验证身份。</view>
      <view class="oauth-btns">
        <view class="oauth-btn oauth-btn-gitee" @tap="oauthLogin('gitee')">
          <text class="oauth-btn-icon">G</text>
          <text class="oauth-btn-label">Gitee 验证登录</text>
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
function normalizeAvatarUrl(src) {
  var value = (src || '').trim()
  if (!value || value.indexOf('/static/images/logo.') !== -1 || value.indexOf('/logo.webp') !== -1) return ''
  return value
}
function isLocalUploadAvatar(src) {
  var value = (src || '').trim()
  return value.indexOf('/static/uploads/') === 0
}
const localLoggedIn = ref(props.isLoggedIn || !!uni.getStorageSync('xc_token'))

if (typeof window !== 'undefined') {
  window.addEventListener('xc-auth-changed', function(e) {
    const loggedIn = !!(e && e.detail && e.detail.loggedIn)
    localLoggedIn.value = loggedIn
    if (loggedIn) {
      _avatarInstanceLoaded = false
      pointsLoaded = false
      loadAvatar()
      loadPointsSummary()
    } else {
      avatarUrl.value = ''
      avatarLetter.value = ''
      _avatarInstanceLoaded = false
      pointsLoaded = false
    }
  })
}

function applySidebarAvatar(src, shouldCache) {
  var sideImg = document.getElementById('sidebarUserAvatar')
  var sideLetter = document.getElementById('sidebarUserLetter')
  var avatarSrc = normalizeAvatarUrl(src)
  if (sideImg) {
    sideImg.onerror = function() {
      try { uni.removeStorageSync('xc_avatar') } catch(_) {}
      this.removeAttribute('src')
      this.style.display = 'none'
      if (sideLetter) sideLetter.style.display = 'flex'
    }
    if (avatarSrc) {
      sideImg.src = avatarSrc
      sideImg.style.display = 'block'
    } else {
      sideImg.removeAttribute('src')
      sideImg.style.display = 'none'
    }
  }
  if (sideLetter) {
    var nameEl = document.getElementById('sidebarUserName')
    var name = (nameEl && nameEl.textContent) || avatarLetter.value || uni.getStorageSync('xc_user') || '用'
    sideLetter.textContent = String(name).charAt(0).toUpperCase()
    sideLetter.style.display = avatarSrc ? 'none' : 'flex'
  }
  if (shouldCache) {
    if (avatarSrc) try { uni.setStorageSync('xc_avatar', avatarSrc) } catch(_) {}
    else try { uni.removeStorageSync('xc_avatar') } catch(_) {}
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
  sidebar.innerHTML = '<div class="sidebar-brand"><span class="sidebar-brand-icon-wrap"><img class="sidebar-brand-icon" src="/static/images/logo.svg?v=7"></span><span class="sidebar-brand-name">时安解忧屋</span></div>'
    + '<div class="sidebar-header"><span class="sidebar-title">对话历史</span><button class="sidebar-new-chat-btn" id="sidebarNewChatBtn" type="button" onclick="window._xc_startNewConversation(\'comprehensive\')">新对话</button></div>'
    + '<div class="sidebar-tabs"><span class="sidebar-tab active" id="sidebarTabFlat" onclick="window._xc_setSidebarView(\'flat\')">全部</span></div>'
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
  sidebar.querySelector('#sidebarNewChatBtn').onclick = function() { if (window._xc_startNewConversation) window._xc_startNewConversation('comprehensive') }

  document.body.appendChild(overlay)
  document.body.appendChild(sidebar)
  _bindSidebarScrollIsolation(sidebar)
  _bindSidebarListInteractions(sidebar)
  _restoreSidebarView()
  var cachedAvatar = normalizeAvatarUrl(uni.getStorageSync('xc_avatar'))
  applySidebarAvatar(isLocalUploadAvatar(cachedAvatar) ? '' : cachedAvatar, false)
}

onMounted(function() {
  // 创建全局侧边栏（仅一次）
  ensureGlobalSidebar()
  if (!window.__xcSidebarNavDelegated) {
    window.__xcSidebarNavDelegated = true
    window.__xcSidebarNavLastTouch = 0
    var handleSidebarNav = function(e) {
      var target = e.target
      var btn = target && target.closest ? target.closest('#topnavSidebarBtn') : null
      if (!btn) return
      if (Date.now() - (window.__xcSidebarNavLastTouch || 0) < 450) {
        e.preventDefault()
        e.stopPropagation()
        if (e.stopImmediatePropagation) e.stopImmediatePropagation()
        return
      }
      window.__xcSidebarNavLastTouch = Date.now()
      e.preventDefault()
      e.stopPropagation()
      if (e.stopImmediatePropagation) e.stopImmediatePropagation()
      e.__xcSidebarHandled = true
      toggleSidebar()
    }
    document.addEventListener('click', handleSidebarNav, true)
    document.addEventListener('touchstart', handleSidebarNav, true)
    document.addEventListener('pointerdown', handleSidebarNav, true)
  }

  // 获取可见弹窗的辅助函数 — 兼容 uni-app H5 页面结构
  if (!window._xc_getVisibleModal) {
    window._xc_getVisibleModal = function() {
      var modals = Array.prototype.slice.call(document.querySelectorAll('#topnavLoginModal'))
      if (!modals.length) return null
      var isCurrentPageModal = function(el) {
        if (!el) return false
        var style = window.getComputedStyle ? window.getComputedStyle(el) : null
        if (style && (style.display === 'none' || style.visibility === 'hidden')) return false
        var page = el.closest('.tab-page-wrapper')
        if (page) {
          var pageStyle = window.getComputedStyle ? window.getComputedStyle(page) : null
          if ((pageStyle && pageStyle.display === 'none') || page.style.display === 'none') return false
        }
        return true
      }
      var openModal = modals.find(function(el) { return el.classList.contains('open') && isCurrentPageModal(el) })
      if (openModal) return openModal
      var currentModal = modals.find(isCurrentPageModal)
      return currentModal || modals[0]
    }
  }
  function _xc_detectLoginIdentifier(value) {
    var v = (value || '').trim()
    if (!v) return 'empty'
    if (v.indexOf('@') !== -1) return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v) ? 'email' : 'invalid-email'
    if (/^\d+$/.test(v)) return 'username'
    return 'username'
  }

  function _xc_getLoginMode(modal) {
    var active = (modal || document).querySelector('.login-tab.active')
    return active ? (active.getAttribute('data-tab') || 'password') : 'password'
  }

  function _xc_applyLoginMode(modal, mode) {
    if (!modal) return
    var passwordField = modal.querySelector('#tnLoginPass-wrap')
    var passwordRow = passwordField ? passwordField.closest('.field') : null
    var codeField = modal.querySelector('#tnLoginCode-wrap')
    var codeRow = codeField ? codeField.closest('.field') : null
    if (passwordRow) passwordRow.style.display = mode === 'code' ? 'none' : ''
    if (codeRow) codeRow.style.display = mode === 'code' ? '' : 'none'
    var account = modal.querySelector('#tnLoginUser')
    if (account) account.placeholder = mode === 'code' ? '邮箱' : '用户名/邮箱'
    var code = modal.querySelector('#tnLoginCode')
    if (code && mode !== 'code') code.value = ''
  }

  // 全局登录方式切换（纯DOM操作，不依赖Vue reactive）
  if (!window._xc_switchTab) {
    window._xc_switchTab = function(el) {
      var tab = el.getAttribute('data-tab') || 'password'
      var modal = el.closest('#topnavLoginModal')
      if (modal) {
        modal.classList.remove('reset-mode')
        modal.querySelectorAll('.login-tab').forEach(function(t) { t.classList.remove('active') })
        el.classList.add('active')
        modal.querySelectorAll('.tn-panel-login, .tn-panel-reset').forEach(function(p) { p.style.display = 'none' })
        var panel = modal.querySelector('.tn-panel-login')
        if (panel) panel.style.display = ''
        _xc_applyLoginMode(modal, tab)
        var titleEl = modal.querySelector('.modal-title')
        if (titleEl) titleEl.textContent = '登录'
        var loginBtn = modal.querySelector('.modal-btns .btn-accent')
        if (loginBtn) { loginBtn.textContent = '登录'; loginBtn.setAttribute('onclick', 'window._xc_doLogin()') }
      }
      try { var e = document.getElementById('tnLoginError'); if (e) e.textContent = '' } catch(_) {}
    }
  }

  // 全局打开登录弹窗
    window._openLoginModal = function() {
      // 打开登录弹窗前关闭所有其他弹窗，防止 overlay 冲突
      try { document.querySelectorAll('#accountSettingsModal').forEach(function(el) { el.classList.remove('open') }) } catch(_) {}
      try { document.querySelectorAll('#topnavLoginModal').forEach(function(el) { el.classList.remove('open') }) } catch(_) {}
     var modal = window._xc_getVisibleModal()
      if (modal) {
        modal.classList.add('open')
        var e = modal.querySelector('#tnLoginError'); if (e) e.textContent = ''
        var loginInputs = [
          ['tnLoginUser-wrap', 'text', '用户名/邮箱'],
          ['tnLoginPass-wrap', 'password', '密码'],
          ['tnLoginCode-wrap', 'text', '验证码'],
          ['tnResetTarget-wrap', 'email', '已绑定邮箱'],
          ['tnResetCode-wrap', 'text', '验证码'],
          ['tnResetPassword-wrap', 'password', '新密码']
        ]
        loginInputs.forEach(function(item) {
          var wrap = modal.querySelector('#' + item[0])
          if (wrap && !wrap.querySelector('input')) {
            var inp = document.createElement('input')
            inp.type = item[1]
            inp.id = item[0].replace('-wrap', '')
            inp.placeholder = item[2]
            // 内联样式（style scoped 对动态创建的 input 不生效）
            inp.style.cssText = 'width:100%;height:42px;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;transition:border-color 0.2s,box-shadow 0.2s'
            inp.onfocus = function() { this.style.borderColor = 'var(--accent)'; this.style.boxShadow = '0 0 0 2px var(--accent-glow)' }
            inp.onblur = function() { this.style.borderColor = 'var(--input-border)'; this.style.boxShadow = 'none' }
            if (item[1] === 'text' || item[1] === 'tel') inp.setAttribute('maxlength', '100')
            wrap.appendChild(inp)
          }
        })
        setTimeout(function() {
          try {
            var firstInput = modal.querySelector('#tnLoginUser')
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
      if (e) e.textContent = ''
      var modal = window._xc_getVisibleModal()
      var uEl = (modal || document).querySelector('#tnLoginUser'); var pEl = (modal || document).querySelector('#tnLoginPass')
      if (uEl) uEl.value = ''
      if (pEl) pEl.value = ''
      var titleEl = (modal || document).querySelector('.modal-title')
      if (titleEl) titleEl.textContent = '注册'
      if (modal) {
        modal.classList.remove('reset-mode')
        modal.querySelectorAll('.login-tab').forEach(function(t) {
          var isPassword = (t.getAttribute('data-tab') || '') === 'password'
          t.classList.toggle('active', isPassword)
        })
        var loginPanel = modal.querySelector('.tn-panel-login')
        var resetPanel = modal.querySelector('.tn-panel-reset')
        if (loginPanel) loginPanel.style.display = ''
        if (resetPanel) resetPanel.style.display = 'none'
        _xc_applyLoginMode(modal, 'password')
      }
      var hintEl = (modal || document).querySelector('.modal-hint')
      if (hintEl) hintEl.innerHTML = '已有账号？<text class="login-link" onclick="window._xc_switchToLogin()" style="color:var(--accent);cursor:pointer;text-decoration:underline;">立即登录</text>'
      var loginBtn = (modal || document).querySelector('.modal-btns .btn-accent')
      if (loginBtn) { loginBtn.textContent = '注册'; loginBtn.setAttribute('onclick', 'window._xc_doRegisterSubmit()') }
      if (uEl) setTimeout(function() { uEl.focus() }, 100)
      if (e) e.textContent = '请填写用户名和密码完成注册'
    }
    window._xc_doRegisterSubmit = function() {
      var e = document.getElementById('tnLoginError')
      var modal = window._xc_getVisibleModal()
      if (modal) e = modal.querySelector('#tnLoginError') || e
      var uEl = (modal || document).querySelector('#tnLoginUser'); var pEl = (modal || document).querySelector('#tnLoginPass')
      var u = uEl ? uEl.value.trim() : ''; var p = pEl ? pEl.value : ''
      if (!u || !p) { if (e) e.textContent = '请填写完整'; return }
      if (u.length < 2) { if (e) e.textContent = '用户名至少2个字符'; return }
      if (p.length < 6) { if (e) e.textContent = '密码至少6个字符'; return }
      if (e) e.textContent = '注册中...'
      uni.request({ url: '/api/register', method: 'POST', data: { username: u, password: p } }).then(function(res) {
        var d = res.data
        if (d.error) { if (e) e.textContent = d.error; return }
        uni.setStorageSync('xc_token', 'session'); uni.setStorageSync('xc_user', d.username || u); uni.setStorageSync('xc_has_password', '1')
        window._openLoginModal_Close()
        uni.showToast({ title: '注册成功', icon: 'success' })
        setTimeout(function() { applyLoginSuccess() }, 120)
      }).catch(function() { if (e) e.textContent = '网络错误' })
    }
    window._xc_switchToLogin = function() {
      var e = document.getElementById('tnLoginError')
      if (e) e.textContent = ''
      var modal = window._xc_getVisibleModal()
      var titleEl = (modal || document).querySelector('.modal-title')
      if (titleEl) titleEl.textContent = '登录'
      var hintEl = (modal || document).querySelector('.modal-hint')
      if (hintEl) hintEl.innerHTML = '没有账号？<text class="register-link" onclick="window._xc_doRegister()" style="color:var(--accent);cursor:pointer;text-decoration:underline;">立即注册</text> · <text class="forgot-link" onclick="window._xc_showForgotPassword()" style="color:var(--accent);cursor:pointer;text-decoration:underline;">忘记密码</text>'
      var loginBtn = (modal || document).querySelector('.modal-btns .btn-accent')
      if (loginBtn) { loginBtn.textContent = '登录'; loginBtn.setAttribute('onclick', 'window._xc_doLogin()') }
      if (modal) {
        modal.classList.remove('reset-mode')
        var tab = modal.querySelector('.login-tab[data-tab="password"]')
        if (tab && window._xc_switchTab) window._xc_switchTab(tab)
      }
      var uEl = (modal || document).querySelector('#tnLoginUser'); var pEl = (modal || document).querySelector('#tnLoginPass')
      if (uEl) uEl.value = ''
      if (pEl) pEl.value = ''
    }
    window._xc_showForgotPassword = function() {
      var modal = window._xc_getVisibleModal()
      if (!modal) return
      modal.classList.add('reset-mode')
      modal.querySelectorAll('.tn-panel-login').forEach(function(p) { p.style.display = 'none' })
      var resetPanel = modal.querySelector('.tn-panel-reset')
      if (resetPanel) resetPanel.style.display = ''
      var titleEl = modal.querySelector('.modal-title')
      if (titleEl) titleEl.textContent = '重置密码'
      var loginBtn = modal.querySelector('.modal-btns .btn-accent')
      if (loginBtn) { loginBtn.textContent = '重置密码'; loginBtn.setAttribute('onclick', 'window._xc_doResetPassword()') }
      var e = modal.querySelector('#tnLoginError')
      if (e) e.textContent = ''
      var target = modal.querySelector('#tnResetTarget')
      if (target) setTimeout(function() { target.focus() }, 80)
    }
    window._xc_switchResetMethod = function(el) {
      var modal = window._xc_getVisibleModal()
      if (!modal || !el) return
      var method = el.getAttribute('data-method') || 'email'
      modal.querySelectorAll('.reset-method').forEach(function(item) { item.classList.remove('active') })
      el.classList.add('active')
      var label = modal.querySelector('#tnResetTargetLabel')
      var target = modal.querySelector('#tnResetTarget')
      if (label) label.textContent = '邮箱'
      if (target) {
        target.value = ''
        target.type = 'email'
        target.placeholder = '已绑定邮箱'
      }
      var e = modal.querySelector('#tnLoginError')
      if (e) e.textContent = ''
    }
    window._xc_doLogin = function() {
      var e = document.getElementById('tnLoginError')
      var modal = window._xc_getVisibleModal()
      if (modal) e = modal.querySelector('#tnLoginError') || e
      var mode = _xc_getLoginMode(modal)
      var accountEl = (modal || document).querySelector('#tnLoginUser')
      var account = accountEl ? accountEl.value.trim() : ''
      var idType = _xc_detectLoginIdentifier(account)
      if (!account) { if (e) e.textContent = '请输入用户名或邮箱'; return }
      if (mode === 'code' && idType !== 'email') {
        if (e) e.textContent = '验证码登录需要输入邮箱'
        return
      }
      var url = '/api/login'
      var data = { username: account }
      if (mode === 'password') {
        var passEl = (modal || document).querySelector('#tnLoginPass')
        var password = passEl ? passEl.value : ''
        if (!password) { if (e) e.textContent = '请输入密码'; return }
        data.password = password
      } else {
        var codeEl = (modal || document).querySelector('#tnLoginCode')
        var code = codeEl ? codeEl.value.trim() : ''
        if (!code) { if (e) e.textContent = '请输入验证码'; return }
        url = '/api/email/login'
        data = { email: account, code: code }
      }
      uni.request({ url: url, method: 'POST', data: data }).then(function(res) {
        var d = res.data
        if (d.error) { if (e) e.textContent = d.error; return }
        uni.setStorageSync('xc_token', 'session')
        uni.setStorageSync('xc_user', d.username || account)
        uni.setStorageSync('xc_has_password', d.has_password !== false ? '1' : '0')
        window._openLoginModal_Close()
        uni.showToast({ title: '登录成功', icon: 'success' })
        applyLoginSuccess()
      }).catch(function() { if (e) e.textContent = '网络错误' })
    }
    // 通用验证码发送（邮箱登录/找回密码共用）
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
    window._xc_sendLoginCode = function() {
      var modal = window._xc_getVisibleModal()
      if (!modal) return
      var accountEl = modal.querySelector('#tnLoginUser')
      var account = accountEl ? accountEl.value.trim() : ''
      var idType = _xc_detectLoginIdentifier(account)
      if (idType !== 'email') {
        var e0 = modal.querySelector('#tnLoginError')
        if (e0) e0.textContent = '验证码登录需要输入邮箱'
        return
      }
      _xc_sendCode({
        inputId: 'tnLoginUser',
        btnId: 'tnLoginCodeBtn',
        key: 'email',
        url: '/api/email/send',
        errMsg: '请输入正确的邮箱',
        validate: function(){ return true },
      })
    }
    window._xc_sendResetCode = function() {
      var modal = window._xc_getVisibleModal()
      if (!modal) return
      _xc_sendCode({
        inputId: 'tnResetTarget',
        btnId: 'tnResetCodeBtn',
        key: 'email',
        url: '/api/email/send',
        errMsg: '请输入正确的邮箱',
        validate: function(v){return v.indexOf('@')!==-1},
      })
    }
    window._xc_doResetPassword = function() {
      var modal = window._xc_getVisibleModal()
      if (!modal) return
      var method = 'email'
      var targetEl = modal.querySelector('#tnResetTarget')
      var codeEl = modal.querySelector('#tnResetCode')
      var passEl = modal.querySelector('#tnResetPassword')
      var target = targetEl ? targetEl.value.trim() : ''
      var code = codeEl ? codeEl.value.trim() : ''
      var password = passEl ? passEl.value : ''
      var e = modal.querySelector('#tnLoginError')
      if (!target || !code || !password) { if (e) e.textContent = '请填写完整'; return }
      if (password.length < 6) { if (e) e.textContent = '密码至少6个字符'; return }
      if (e) e.textContent = '重置中...'
      uni.request({ url: '/api/password/reset', method: 'POST', data: { method: method, target: target, code: code, new_password: password } }).then(function(res) {
        var d = res.data || {}
        if (d.error) { if (e) e.textContent = d.error; return }
        if (e) e.textContent = '密码已重置，请用新密码登录'
        if (passEl) passEl.value = ''
        if (codeEl) codeEl.value = ''
        setTimeout(function() { if (window._xc_switchToLogin) window._xc_switchToLogin() }, 900)
      }).catch(function() { if (e) e.textContent = '网络错误' })
    }
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
          if (modal.classList.contains('reset-mode') && window._xc_doResetPassword) window._xc_doResetPassword()
          else if (window._xc_doLogin) window._xc_doLogin()
        }
      }, true)
    }
  })

window._xc_toggleSidebar = function(e) {
  if (e && e.stopPropagation) e.stopPropagation()
  if (e && e.preventDefault) e.preventDefault()
  if (e && e.__xcSidebarHandled) return
  if (e && Date.now() - (window.__xcSidebarNavLastTouch || 0) < 450) return
  window.__xcSidebarNavLastTouch = Date.now()
  toggleSidebar()
}
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
      applySidebarAvatar(d.avatar, !!normalizeAvatarUrl(d.avatar))
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
    closeSidebarPanel(sidebar, overlay)
    document.body.removeEventListener('click', window.__sidebarClickAway)
    return
  }
  openSidebarPanel(sidebar, overlay)
  window.__xcSidebarOpenedAt = Date.now()
  uni.$emit('sidebar-opened')
  document.body.removeEventListener('click', window.__sidebarClickAway)
  window.__sidebarClickAway = function(e) {
    if (Date.now() - (window.__xcSidebarOpenedAt || 0) < 800) return
    var s = document.getElementById('tarotSidebarGlobal')
    var target = e && e.target
    if (target && target.closest && target.closest('#topnavSidebarBtn')) return
    if (s && s.classList.contains('open') && !s.contains(target)) {
      e.stopPropagation()
      var ov = document.getElementById('sidebarOverlayGlobal')
      if (ov) closeSidebarPanel(s, ov)
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
    window._xc_setSidebarView('flat')
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
    // 对话历史只保留全部视图。
    _restoreSidebarView()
    window._xc_setSidebarView('flat')
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
  var actionId = _registerSidebarAction(function() { window._xc_startNewConversation(type) })
  return '<div class="sidebar-item sidebar-new-item" data-click-action="' + actionId + '">'
    + '<div class="sidebar-item-body">'
    + '<span class="sidebar-item-text">' + text + '</span>'
    + '<span class="sidebar-item-time">开始新的提问</span>'
    + '</div></div>'
}

function _renderSidebarItem(r) {
  var time = _formatSidebarTime(r.created_at)
  var text = _escHtml(r.question || '(无问题)')
  var realId = r._comprehensiveConvId || r._tarotConvId || r._lyConvId || r._mhConvId || r._qaiConvId || r._baziConvId || r._zwConvId || r.id
  var appType = r.app_type || ''
  var clickAction = function() {
    if (r._comprehensiveConvId) window._showComprehensiveConv(r._comprehensiveConvId)
    else if (r._tarotConvId) window._showTarotConv(r._tarotConvId)
    else if (r.app_type === 'tarot') window._showTarotRecordDetail(r.id)
    else if (r._lyConvId) window._showLyConvDetail(r._lyConvId)
    else if (r._mhConvId) window._showMhConvDetail(r._mhConvId)
    else if (r._qaiConvId) window._showQiConvDetail(r._qaiConvId)
    else if (r._baziConvId) window._showBaziConvDetail(r._baziConvId)
    else if (r._zwConvId) window._showZwConvDetail(r._zwConvId)
    else if (r.app_type === 'comprehensive') window._showComprehensiveConv(realId)
    else if (r.app_type === 'liuyao') window._showLyRecordDetail(r.id)
    else if (r.app_type === 'qimen') window._showQiRecordDetail(r.id)
    else if (r.app_type === 'bazi') window._showBaziRecordDetail(r.id)
    else window._showHistoryDetail(r.id)
  }
  var clickActionId = _registerSidebarAction(clickAction)
  var deleteActionId = _registerSidebarAction(function(el) {
    if (confirm('确定要删除这条记录吗？')) window._xc_deleteHistoryItem(appType, realId, el)
  })
  return '<div class="sidebar-item" data-click-action="' + clickActionId + '">'
    + '<div class="sidebar-item-body">'
    + '<span class="sidebar-item-text">' + text + '</span>'
    + '<span class="sidebar-item-time">' + time + '</span>'
    + '</div>'
    + '<span class="sidebar-item-del" data-delete-action="' + deleteActionId + '" title="删除">✕</span>'
    + '</div>'
}

function _registerSidebarAction(fn) {
  if (!window.__sidebarActionMap) window.__sidebarActionMap = {}
  if (!window.__sidebarActionSeq) window.__sidebarActionSeq = 1
  var id = 'a' + (window.__sidebarActionSeq++)
  window.__sidebarActionMap[id] = fn
  return id
}

function _runSidebarAction(id, el) {
  var map = window.__sidebarActionMap || {}
  if (id && typeof map[id] === 'function') map[id](el)
}

function _bindSidebarScrollIsolation(sidebar) {
  if (!sidebar || sidebar.__scrollIsolationBound) return
  sidebar.__scrollIsolationBound = true
  var stopScrollBubble = function(e) {
    if (!e) return
    e.stopPropagation()
    if (e.stopImmediatePropagation) e.stopImmediatePropagation()
  }
  sidebar.addEventListener('wheel', stopScrollBubble, { passive: true })
  sidebar.addEventListener('touchmove', stopScrollBubble, { passive: true })
}

function _bindSidebarListInteractions(sidebar) {
  var list = sidebar && sidebar.querySelector ? sidebar.querySelector('#sidebarListGlobal') : null
  if (!list || list.__sidebarTouchBound) return
  list.__sidebarTouchBound = true
  var touchState = null

  list.addEventListener('touchstart', function(e) {
    var t = e.touches && e.touches[0]
    if (!t) return
    touchState = { x: t.clientX, y: t.clientY, time: Date.now(), moving: false }
    list.classList.remove('sidebar-touch-moving')
  }, { passive: true })

  list.addEventListener('touchmove', function(e) {
    if (!touchState) return
    var t = e.touches && e.touches[0]
    if (!t) return
    var dx = Math.abs(t.clientX - touchState.x)
    var dy = Math.abs(t.clientY - touchState.y)
    if (dx > 8 || dy > 8) {
      touchState.moving = true
      list.classList.add('sidebar-touch-moving')
    }
  }, { passive: true })

  list.addEventListener('touchend', _handleSidebarTouchEnd, { passive: false })

  list.addEventListener('click', function(e) {
    if (list.classList.contains('sidebar-touch-moving')) {
      e.preventDefault()
      e.stopPropagation()
      list.classList.remove('sidebar-touch-moving')
      return
    }
    _handleSidebarActionEvent(e)
  })

  function _handleSidebarTouchEnd(e) {
    if (!touchState) return
    var wasMoving = touchState.moving || (Date.now() - touchState.time > 700)
    touchState = null
    if (wasMoving) {
      list.classList.add('sidebar-touch-moving')
      setTimeout(function() { list.classList.remove('sidebar-touch-moving') }, 120)
      return
    }
    e.preventDefault()
    _handleSidebarActionEvent(e)
  }

  window._handleSidebarTouchEnd = _handleSidebarTouchEnd
}

function _handleSidebarActionEvent(e) {
  var target = e.target
  var del = target && target.closest ? target.closest('[data-delete-action]') : null
  if (del) {
    e.preventDefault()
    e.stopPropagation()
    _runSidebarAction(del.getAttribute('data-delete-action'), del)
    return
  }
  var item = target && target.closest ? target.closest('.sidebar-item[data-click-action]') : null
  if (item) {
    e.preventDefault()
    e.stopPropagation()
    _runSidebarAction(item.getAttribute('data-click-action'), item)
  }
}

function openSidebarPanel(sidebar, overlay) {
  try {
    document.documentElement.classList.remove('marketing-page', 'marketing-android')
    document.body.classList.remove('marketing-page', 'marketing-android')
  } catch(_) {}
  sidebar.classList.add('open')
  overlay.classList.add('show')
  sidebar.setAttribute('aria-hidden', 'false')
  overlay.setAttribute('aria-hidden', 'false')
  sidebar.style.setProperty('left', '0', 'important')
  sidebar.style.setProperty('right', 'auto', 'important')
  sidebar.style.setProperty('display', 'flex', 'important')
  sidebar.style.setProperty('transform', 'translateX(0)', 'important')
  sidebar.style.setProperty('translate', '0 0', 'important')
  sidebar.style.setProperty('visibility', 'visible', 'important')
  sidebar.style.setProperty('pointer-events', 'auto', 'important')
  sidebar.style.setProperty('z-index', '2100', 'important')
  overlay.style.setProperty('display', 'block', 'important')
  overlay.style.setProperty('z-index', '2000', 'important')
}

function closeSidebarPanel(sidebar, overlay) {
  sidebar.classList.remove('open')
  overlay.classList.remove('show')
  sidebar.setAttribute('aria-hidden', 'true')
  overlay.setAttribute('aria-hidden', 'true')
  sidebar.style.setProperty('left', '0', 'important')
  sidebar.style.setProperty('right', 'auto', 'important')
  sidebar.style.setProperty('transform', 'translateX(-100%)', 'important')
  sidebar.style.removeProperty('translate')
  sidebar.style.removeProperty('display')
  sidebar.style.removeProperty('visibility')
  sidebar.style.removeProperty('pointer-events')
  sidebar.style.removeProperty('z-index')
  overlay.style.setProperty('display', 'none', 'important')
  overlay.style.removeProperty('z-index')
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

// 对话历史只保留全部视图。
function _restoreSidebarView() {
  var flatTab = document.getElementById('sidebarTabFlat')
  if (flatTab) flatTab.classList.add('active')
  try { localStorage.setItem('xc_sidebar_view', 'flat') } catch(_) {}
}

// 侧边栏视图切换：保留兼容入口，统一渲染全部。
window._xc_setSidebarView = function() {
  var flatTab = document.getElementById('sidebarTabFlat')
  var listEl = document.getElementById('sidebarListGlobal')
  if (!flatTab || !listEl) return
  var cache = window.__sidebarCache
  if (!cache || !cache.flat) return
  try { localStorage.setItem('xc_sidebar_view', 'flat') } catch(_) {}
  flatTab.classList.add('active')
  var flat = cache.flat || []
  flat.sort(function(a, b) { return (b.created_at || '').localeCompare(a.created_at || '') })
  var h = ''
  flat.forEach(function(r) {
    h += _renderSidebarItem(r)
  })
  if (!flat.length) h = '<div class="sidebar-empty">暂无历史记录</div>'
  listEl.innerHTML = h
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
  uni.removeStorageSync('xc_avatar')
  avatarUrl.value = ''
  applySidebarAvatar('', false)
}
function loadAvatar() {
  if (!localLoggedIn.value) return
  var cachedUser = uni.getStorageSync('xc_user')
  var parsed = null
  try { parsed = typeof cachedUser === 'string' ? JSON.parse(cachedUser) : cachedUser } catch(_) { parsed = null }
  if (parsed && typeof parsed === 'object') {
    if (parsed.username) avatarLetter.value = parsed.username.charAt(0).toUpperCase()
    else if (parsed.nickname) avatarLetter.value = parsed.nickname.charAt(0).toUpperCase()
  } else if (cachedUser && typeof cachedUser === 'string') {
    avatarLetter.value = cachedUser.charAt(0).toUpperCase()
  }
  var cachedAvatar = normalizeAvatarUrl(uni.getStorageSync('xc_avatar'))
  if (!cachedAvatar) uni.removeStorageSync('xc_avatar')
  var safeCachedAvatar = isLocalUploadAvatar(cachedAvatar) ? '' : cachedAvatar
  avatarUrl.value = safeCachedAvatar
  applySidebarAvatar(safeCachedAvatar, false)
  if (_avatarInstanceLoaded) return
  _avatarInstanceLoaded = true
  window.__avatarLoaded = true
  uni.request({ url: '/api/me', method: 'GET' }).then(function(res) {
    var d = res.data
    if (d && d.guest) {
    } else if (d && d.username) {
      avatarLetter.value = d.username.charAt(0).toUpperCase()
      var nextAvatar = normalizeAvatarUrl(d.avatar)
      if (nextAvatar) { avatarUrl.value = nextAvatar; uni.setStorageSync('xc_avatar', nextAvatar) }
      else { avatarUrl.value = ''; uni.removeStorageSync('xc_avatar') }
      applySidebarAvatar(nextAvatar, !!nextAvatar)
      document.querySelectorAll('#avatarAdminEntry').forEach(function(el) {
        el.style.display = d.is_admin ? '' : 'none'
      })
    }
  }).catch(function() {})
}
var pointsLoaded = false
function loadPointsSummary() {
  if (!localLoggedIn.value || pointsLoaded) return
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

function applyLoginSuccess() {
  localLoggedIn.value = true
  _avatarInstanceLoaded = false
  pointsLoaded = false
  loadAvatar()
  loadPointsSummary()
  try { _loadSidebarUserPanel() } catch(_) {}
  try { window.dispatchEvent(new CustomEvent('xc-auth-changed', { detail: { loggedIn: true } })) } catch(_) {}
  try { uni.$emit('xc-auth-changed', { loggedIn: true }) } catch(_) {}
}

function applyLogoutState() {
  localLoggedIn.value = false
  avatarUrl.value = ''
  avatarLetter.value = ''
  _avatarInstanceLoaded = false
  pointsLoaded = false
  try {
    uni.removeStorageSync('xc_avatar')
    document.querySelectorAll('#avatarPointsBadge').forEach(function(el) { el.textContent = '...' })
    document.querySelectorAll('#avatarAdminEntry').forEach(function(el) { el.style.display = 'none' })
    applySidebarAvatar('', false)
    var sideName = document.getElementById('sidebarUserName')
    var sidePoints = document.getElementById('sidebarUserPoints')
    var sideLogged = document.getElementById('sidebarUserLogged')
    var sideGuest = document.getElementById('sidebarUserGuest')
    var sideList = document.getElementById('sidebarHistoryList')
    if (sideName) sideName.textContent = '用户'
    if (sidePoints) sidePoints.textContent = '积分: --'
    if (sideLogged) sideLogged.style.display = 'none'
    if (sideGuest) sideGuest.style.display = 'flex'
    if (sideList) sideList.innerHTML = '<div class="sidebar-empty">请登录后查看历史记录</div>'
    window.__sidebarCache = null
  } catch(_) {}
  try { window.dispatchEvent(new CustomEvent('xc-auth-changed', { detail: { type: 'logout', loggedIn: false } })) } catch(_) {}
  try { uni.$emit('xc-auth-changed', { type: 'logout', loggedIn: false }) } catch(_) {}
}

function clearHomeAgentSessionPrefs() {
  const bases = ['xc_home_selected_profiles_v1', 'xc_home_selected_tools_v1', 'xc_home_send_confirm_skip_v1']
  let userKey = 'guest'
  try {
    const raw = uni.getStorageSync('xc_user')
    const user = typeof raw === 'string' ? JSON.parse(raw) : raw
    userKey = String((user && (user.id || user.username || user.phone)) || 'guest')
  } catch (_) {}
  bases.forEach(function(base) {
    try { uni.removeStorageSync(base + ':' + userKey) } catch (_) {}
    try { uni.removeStorageSync(base + ':guest') } catch (_) {}
  })
}

function showMarketingHomeAfterAuthChange() {
  // 退出账号后统一回到营销页，避免停留在需要登录态的应用页导致空白。
  try {
    sessionStorage.removeItem('_nav_query')
    window.__xcHomeMode = 'marketing'
    if (window.location.hash !== '#/') window.history.replaceState({ marketing: 'home' }, '', '#/')
    window.dispatchEvent(new CustomEvent('xc-show-marketing-home'))
    window.dispatchEvent(new CustomEvent('xc-home-mode-changed', { detail: { mode: 'marketing' } }))
    window.scrollTo({ top: 0, behavior: 'smooth' })
  } catch(_) {}
  try {
    uni.switchTab({
      url: '/pages/index/index',
      success: function() {
        try {
          if (window.__xcRenderTabPath) window.__xcRenderTabPath('/')
          window.dispatchEvent(new CustomEvent('xc-show-marketing-home'))
        } catch(_) {}
      },
      fail: function() {
        try {
          if (window.__xcRenderTabPath) window.__xcRenderTabPath('/')
        } catch(_) {}
      }
    })
  } catch(_) {}
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
function openLoginFromNav() {
  try {
    if (window._openLoginModal) window._openLoginModal()
  } catch(_) {}
}

function performLogout() {
  uni.request({ url: '/api/logout', method: 'POST' }).then(function() {
    clearHomeAgentSessionPrefs()
    uni.removeStorageSync('xc_token'); uni.removeStorageSync('xc_user'); uni.removeStorageSync('xc_has_password'); uni.removeStorageSync('xc_avatar')
    applyLogoutState()
    showMarketingHomeAfterAuthChange()
  }).catch(function() {
    clearHomeAgentSessionPrefs()
    uni.removeStorageSync('xc_token'); uni.removeStorageSync('xc_user'); uni.removeStorageSync('xc_has_password'); uni.removeStorageSync('xc_avatar')
    applyLogoutState()
    showMarketingHomeAfterAuthChange()
  })
}

function doLogout() {
  uni.showModal({
    title: '确认退出',
    content: '确定要退出当前账号吗？',
    confirmText: '退出',
    cancelText: '取消',
    success: function(res) {
      if (res && res.confirm) performLogout()
    }
  })
}
function closeLoginModal() { try { document.querySelectorAll('#topnavLoginModal').forEach(function(el) { el.classList.remove('open') }) } catch(_) {} }
async function doLogin() {
  if (window._xc_doLogin) window._xc_doLogin()
}

async function sendPhoneCode() {
  if (window._xc_sendLoginCode) window._xc_sendLoginCode()
}

async function sendEmailCode() {
  if (window._xc_sendLoginCode) window._xc_sendLoginCode()
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
var TAB_PATHS = ['/', '/pages/qimen/index', '/pages/bazi-index/index', '/pages/tarot/index', '/pages/liuyao/index', '/pages/meihua/index', '/pages/ziwei/index', '/pages/zeji/index', '/pages/calendar/index', '/pages/community/index', '/pages/user-management/index', '/pages/profile/index', '/pages/about/index', '/pages/points/index']
var TAB_ROUTES = ['pages/index/index', 'pages/qimen/index', 'pages/bazi-index/index', 'pages/tarot/index', 'pages/liuyao/index', 'pages/meihua/index', 'pages/ziwei/index', 'pages/zeji/index', 'pages/calendar/index', 'pages/community/index', 'pages/user-management/index', 'pages/profile/index', 'pages/about/index', 'pages/points/index']
var TAB_TITLES = {
  '/': '时安解忧屋',
  '/pages/qimen/index': '奇门遁甲',
  '/pages/bazi-index/index': '八字排盘',
  '/pages/tarot/index': '塔罗牌',
  '/pages/liuyao/index': '六爻排盘',
  '/pages/meihua/index': '梅花易数',
  '/pages/ziwei/index': '紫微斗数',
  '/pages/zeji/index': '择吉工具',
  '/pages/calendar/index': '专属日历',
  '/pages/community/index': '社区',
  '/pages/user-management/index': '档案列表',
  '/pages/profile/index': '个人中心',
  '/pages/about/index': '关于我们',
  '/pages/points/index': '积分中心',
}
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

function closeBlockingOverlaysBeforeNav() {
  try {
    document.querySelectorAll('#topnavLoginModal').forEach(function(el) { el.classList.remove('open') })
  } catch(_) {}
  try {
    document.querySelectorAll('.modal-overlay.open').forEach(function(el) {
      if (el.id === 'topnavLoginModal') el.classList.remove('open')
    })
  } catch(_) {}
}

function goAsync(hash, event) {
  try {
    if (event && event.preventDefault) event.preventDefault()
    if (event && event.stopPropagation) event.stopPropagation()
    if (event && event.stopImmediatePropagation) event.stopImmediatePropagation()
  } catch(_) {}
  setTimeout(function() { go(hash) }, 0)
  return false
}

function go(hash) {
  closeBlockingOverlaysBeforeNav()
  var routeBeforeNav = getCurrentRoute()
  var raw = hash.replace('#', '') || '/'
  var pathOnly = raw.split('?')[0]
  var queryStr = raw.indexOf('?') > -1 ? raw.substring(raw.indexOf('?')) : ''
  var uniPath = pathOnly === '/' ? '/pages/index/index' : pathOnly
  var fullPath = uniPath + queryStr
  var isTab = TAB_PATHS.indexOf(pathOnly) > -1
  var wantsAppHome = pathOnly === '/' && /(?:[?&])app=(?:1|true)(?:&|$)/.test(queryStr)
  var wantsMarketingHome = pathOnly === '/' && !wantsAppHome
  var routeBeforeIsTab = TAB_PATHS.indexOf(routeBeforeNav) > -1 || routeBeforeNav === '/pages/index/index'
  var shouldSwitchForAgentHome = wantsAppHome && !routeBeforeIsTab

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

  if (wantsAppHome && !shouldSwitchForAgentHome) {
    try {
      sessionStorage.removeItem('_nav_query')
      window.__xcHomeMode = 'app'
      document.documentElement.classList.add('home-fixed-page')
      document.body.classList.add('home-fixed-page')
      document.documentElement.classList.remove('marketing-page')
      document.body.classList.remove('marketing-page')
      if (window.location.hash !== '#/?app=1') window.history.pushState({ app: 'home' }, '', '#/?app=1')
      window.dispatchEvent(new CustomEvent('xc-home-mode-changed', { detail: { mode: 'app' } }))
    } catch(_) {}
  } else if (wantsMarketingHome) {
    try {
      sessionStorage.removeItem('_nav_query')
      window.__xcHomeMode = 'marketing'
      if (window.location.hash !== '#/') window.history.pushState({ marketing: 'home' }, '', '#/')
      window.dispatchEvent(new CustomEvent('xc-show-marketing-home'))
      window.dispatchEvent(new CustomEvent('xc-home-mode-changed', { detail: { mode: 'marketing' } }))
    } catch(_) {}
  } else if (queryStr) {
    try { sessionStorage.setItem('_nav_query', queryStr) } catch(_) {}
  }

  if (wantsAppHome) {
    var renderAgentHome = function() {
      try {
        if (window.__xcRenderTabPath) window.__xcRenderTabPath('/', '?app=1')
        window.__xcHomeMode = 'app'
        try { document.title = '时安解忧屋' } catch(_) {}
        document.documentElement.classList.add('home-fixed-page')
        document.body.classList.add('home-fixed-page')
        document.documentElement.classList.remove('marketing-page')
        document.body.classList.remove('marketing-page')
        if (window.location.hash !== '#/?app=1') window.history.replaceState({ app: 'home' }, '', '#/?app=1')
        window.dispatchEvent(new CustomEvent('xc-home-mode-changed', { detail: { mode: 'app' } }))
      } catch(_) {}
    }
    try {
      if (shouldSwitchForAgentHome) {
        uni.switchTab({
          url: '/pages/index/index',
          success: function() {
            renderAgentHome()
            setTimeout(renderAgentHome, 80)
            setTimeout(renderAgentHome, 260)
          },
          fail: function() {
            renderAgentHome()
            setTimeout(renderAgentHome, 120)
          }
        })
        return
      }
    } catch(_) {}
    renderAgentHome()
    setTimeout(renderAgentHome, 60)
    setTimeout(renderAgentHome, 220)
    syncNavHighlight()
    updateNavOverflow()
    return
  }

  if (isTab) {
    var renderTargetTab = function() {
      try {
        if (window.__xcRenderTabPath) window.__xcRenderTabPath(pathOnly, '')
      } catch(_) {}
    }
    var finishTargetTab = function() {
      renderTargetTab()
      try { document.title = TAB_TITLES[pathOnly] || document.title } catch(_) {}
      if (wantsMarketingHome) {
        try { window.dispatchEvent(new CustomEvent('xc-show-marketing-home')) } catch(_) {}
      }
      // 切换 tab 后立即同步导航高亮+溢出检测，不依赖 300ms setInterval 轮询
      syncNavHighlight()
      updateNavOverflow()
      if (queryStr) {
        setTimeout(function() { try { uni.$emit('nav-query', queryStr) } catch(_) {} }, 200)
      }
    }
    if (!routeBeforeIsTab) {
      uni.switchTab({
        url: uniPath,
        success: function() {
          setTimeout(finishTargetTab, 30)
          setTimeout(finishTargetTab, 180)
        },
        fail: function() {
          setTimeout(finishTargetTab, 80)
        }
      })
      return
    }
    uni.switchTab({
      url: uniPath,
      success: finishTargetTab,
      fail: renderTargetTab
    })
    setTimeout(renderTargetTab, 60)
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

function getCurrentRouteWithQuery() {
  try {
    var hash = window.location.hash.replace('#', '') || '/'
    var pathOnly = hash.split('?')[0]
    var queryStr = hash.indexOf('?') > -1 ? hash.substring(hash.indexOf('?')) : ''
    var route = pathOnly === '/' ? '/pages/index/index' : pathOnly
    return route + queryStr
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
  function appendMoreItem(moreMenu, more, label, href) {
    var clone = document.createElement('view')
    clone.className = 'nav-btn-drop-item'
    if (href) clone.setAttribute('data-href', href)
    clone.textContent = label
    clone.onclick = function(e) {
      var targetHref = clone.getAttribute('data-href')
      if (window._xc_dropItemGo) {
        window._xc_dropItemGo(e, targetHref)
      } else {
        e.stopPropagation()
        more.classList.remove('open')
        if (targetHref) goAsync(targetHref, e)
      }
    }
    moreMenu.appendChild(clone)
  }

  function getTopLevelNavText(btn) {
    var copy = btn.cloneNode(true)
    copy.querySelectorAll('.nav-btn-drop-menu').forEach(function(menu) { menu.remove() })
    return copy.textContent.replace(' ▾','').trim()
  }

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
        var nestedMenu = btn.querySelector('.nav-btn-drop-menu')
        if (nestedMenu) {
          var section = document.createElement('view')
          section.className = 'nav-btn-drop-section'
          section.textContent = getTopLevelNavText(btn)
          moreMenu.appendChild(section)
          nestedMenu.querySelectorAll('.nav-btn-drop-item').forEach(function(item) {
            appendMoreItem(moreMenu, more, item.textContent.trim(), item.getAttribute('data-href'))
          })
        } else {
          appendMoreItem(moreMenu, more, getTopLevelNavText(btn), btn.getAttribute('data-href'))
        }
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
  var fullRoute = getCurrentRouteWithQuery()
  if (!route) return
  try {
    if (route === '/pages/index/index' && window.__xcHomeMode === 'app') {
      fullRoute = '/pages/index/index?app=1'
    }
  } catch (_) {}

  // 清除所有按钮高亮
  document.querySelectorAll('.nav-btn.current, .nav-btn-drop-item.menu-active').forEach(function(el) {
    el.classList.remove('current', 'menu-active')
  })

  // 通过 data-href 匹配当前路由（精确匹配，避免 "#/" 匹配所有路由）
  document.querySelectorAll('.nav-btn[data-href], .nav-btn-drop-item[data-href]').forEach(function(el) {
    var href = el.getAttribute('data-href') || ''
    var raw = href.replace('#', '') || '/'
    var pathOnly = raw.split('?')[0]
    var queryStr = raw.indexOf('?') > -1 ? raw.substring(raw.indexOf('?')) : ''
    var target = pathOnly === '/' ? '/pages/index/index' : pathOnly
    var fullTarget = target + queryStr
    if (fullTarget && fullRoute === fullTarget) {
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
  window.__topNavGoAsync = function(event, hash) { return goAsync(hash, event) }
  window.__topNavGo.avatarLoad = loadAvatar
  window.addEventListener('xc-home-mode-changed', syncNavHighlight)

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
        if (el.classList && el.classList.contains('nav-btn')) return
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
  // 全局退出登录函数：所有头像菜单、侧边栏退出都统一走确认弹窗。
  window._xc_doLogout = function() {
    doLogout()
  }
  // 创建登录弹窗原生输入框
  try {
    var modalInputs = [
      { wrap: 'tnLoginUser-wrap', id: 'tnLoginUser', type: 'text', placeholder: '用户名/邮箱' },
      { wrap: 'tnLoginPass-wrap', id: 'tnLoginPass', type: 'text', placeholder: '密码', isPassword: true },
      { wrap: 'tnLoginCode-wrap', id: 'tnLoginCode', type: 'text', placeholder: '验证码' },
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
.nav-btn-has-drop:hover .nav-btn-drop-menu,
.nav-btn-has-drop.open .nav-btn-drop-menu {
  visibility: visible !important;
  opacity: 1 !important;
  pointer-events: auto !important;
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
.nav-btn-drop-section {
  display: block;
  padding: 8px 16px 4px;
  font-size: 0.72rem;
  line-height: 1.3;
  color: var(--accent);
  cursor: default;
  white-space: nowrap;
}

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
.modal-box { background: rgba(31, 29, 24, 0.94); border: 1px solid rgba(178,149,93,0.20); border-radius: 20px; padding: 28px 32px; max-width: 400px; width: min(400px, 90vw); min-height: 555px; box-sizing: border-box; box-shadow: 0 24px 80px rgba(0,0,0,0.38), inset 0 1px 0 rgba(255,255,255,0.08); -webkit-backdrop-filter: blur(28px) saturate(1.45); backdrop-filter: blur(28px) saturate(1.45); }
[data-theme="light"] .modal-box { background: rgba(255, 253, 248, 0.96); border: 1px solid rgba(178,149,93,0.18); box-shadow: 0 24px 80px rgba(60,40,15,0.16), inset 0 1px 0 rgba(255,255,255,0.85); }
.modal-title { font-family: var(--font-serif); font-size: 1.2rem; text-align: center; color: var(--text-1); margin-bottom: 20px; letter-spacing: 2px; }
.field { margin-bottom: 14px; }
.field-label { font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; display: block; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 12px; background: var(--input-bg); border: 1px solid rgba(178,149,93,0.16); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; transition: border-color .18s ease, box-shadow .18s ease, background .18s ease; }
.field-input:focus { border-color: rgba(178,149,93,0.54); box-shadow: 0 0 0 3px rgba(178,149,93,0.10); }
.tn-panel { min-height: 180px; }
.tn-panel-login { height: 180px; }
.tn-panel .dom-input-wrap { min-height: 42px; }
.tn-panel .field-input { height: 42px; }
.tn-panel .code-field > view { min-height: 42px; align-items: stretch; }
.tn-panel .code-btn { min-width: 96px; height: 42px; box-sizing: border-box; }
.modal-overlay.reset-mode .login-tabs { display: none; }
.tn-panel-reset { min-height: 256px; }
.reset-methods { display: flex; gap: 4px; margin-bottom: 12px; background: rgba(178,149,93,0.09); border: 1px solid rgba(178,149,93,0.12); border-radius: 12px; padding: 3px; }
.reset-method { flex: 1; text-align: center; padding: 8px 0; border-radius: 9px; font-size: 0.78rem; color: var(--text-3); cursor: pointer; transition: all 0.2s; }
.reset-method.active { background: var(--accent); color: #fff; font-weight: 600; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }
.oauth-divider { display: flex; align-items: center; margin: 16px 0 12px; }
.oauth-divider::before, .oauth-divider::after { content: ''; flex: 1; height: 1px; background: var(--card-border); }
.oauth-divider-text { font-size: 0.72rem; color: var(--text-3); padding: 0 12px; white-space: nowrap; }
.oauth-note { color: var(--text-3); font-size: 0.68rem; line-height: 1.45; text-align: center; margin: -4px 0 10px; }
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
  .nav-btn-more .nav-btn-drop-menu,
  body > #navBtnMoreMenu.nav-btn-drop-menu {
    width: min(300px, calc(100vw - 40px)) !important;
  }
  .nav-btn-more .nav-btn-drop-item,
  body > #navBtnMoreMenu.nav-btn-drop-menu .nav-btn-drop-item {
    white-space: normal !important;
    line-height: 1.35 !important;
  }
  .nav-btn-drop-section {
    color: var(--accent) !important;
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
  .modal-box { padding: 20px 16px; border-radius: 16px; max-width: 100%; width: 92%; min-height: 520px; }
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
