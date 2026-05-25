<template>
  <view class="topnav-wrap">
    <!-- 顶部固定导航 — 两行结构 -->
    <nav class="topnav topnav-solid">
      <!-- 单行：☰ + 按钮栏 + 右侧 -->
      <view class="topnav-sidebar-btn" id="topnavSidebarBtn" @click="toggleSidebar" @tap="toggleSidebar" onclick="window._xc_toggleSidebar()">☰</view>
      <view class="nav-btn-bar" id="navBtnBar">
        <view class="nav-btn" data-href="#/" @click="go('#/')">首页</view>

        <view class="nav-btn nav-btn-has-drop" data-href="#/pages/qimen/index" @click="go('#/pages/qimen/index')">
          奇门遁甲 ▾
          <view class="nav-btn-drop-menu">
            <view class="nav-btn-drop-item" data-href="#/pages/qimen/index?tab=ai" @click.stop="go('#/pages/qimen/index?tab=ai')">🔮 时安奇门系统</view>
            <view class="nav-btn-drop-item" data-href="#/pages/qimen/index?tab=free" @click.stop="go('#/pages/qimen/index?tab=free')">☯️ 奇门排盘免费版</view>
          </view>
        </view>

        <view class="nav-btn nav-btn-has-drop" data-href="#/pages/bazi-index/index" @click="go('#/pages/bazi-index/index')">
          八字排盘 ▾
          <view class="nav-btn-drop-menu">
            <view class="nav-btn-drop-item" data-href="#/pages/bazi-index/index?tab=free" @click.stop="go('#/pages/bazi-index/index?tab=free')">📜 八字排盘免费版</view>
            <view class="nav-btn-drop-item" data-href="#/pages/bazi-index/index?tab=ai" @click.stop="go('#/pages/bazi-index/index?tab=ai')">🤖 时安八字系统</view>
            <view class="nav-btn-drop-item" data-href="#/package-user/history/index" @click.stop="go('#/package-user/history/index')">📋 排盘记录</view>
          </view>
        </view>

        <view class="nav-btn" data-href="#/pages/liuyao/index" @click="go('#/pages/liuyao/index')">六爻排盘</view>
        <view class="nav-btn" data-href="#/pages/meihua/index" @click="go('#/pages/meihua/index')">梅花易数</view>
        <view class="nav-btn" data-href="#/pages/ziwei/index" @click="go('#/pages/ziwei/index')">紫微斗数</view>
        <view class="nav-btn" data-href="#/pages/tarot/index" @click="go('#/pages/tarot/index')">塔罗牌</view>
        <view class="nav-btn" data-href="#/pages/zeji/index" @click="go('#/pages/zeji/index')">择吉工具</view>
        <view class="nav-btn" data-href="#/pages/calendar/index" @click="go('#/pages/calendar/index')">专属日历</view>
        <view class="nav-btn" data-href="#/pages/community/index" @click="go('#/pages/community/index')">社区</view>
        <view class="nav-btn" data-href="#/package-info/about/index" @click="go('#/package-info/about/index')">关于我们</view>

        <!-- 溢出"更多"按钮（JS 控制显示） -->
        <view class="nav-btn nav-btn-more" id="navBtnMore" style="display:none;" @click.stop="toggleMoreMenu($event)">
          更多 ▾
          <view class="nav-btn-drop-menu" id="navBtnMoreMenu"></view>
        </view>
      </view>
      <view class="topnav-right">
        <view class="nav-profile-btn" data-href="#/pages/profile/index" @click="go('#/pages/profile/index')">个人中心</view>
        <view class="theme-toggle-nav" id="themeToggleBtn" data-action="auth" @click="onToggleTheme">
          <text id="themeToggleIcon">{{ theme === 'dark' ? '🌙' : '☀️' }}</text>
        </view>
        <view class="nav-auth-btns" v-if="!isLoggedIn">
          <view class="btn btn-outline btn-sm" onclick="window._openLoginModal()">登录</view>
        </view>
        <view class="nav-avatar-wrap" v-else>
           <view class="nav-avatar-trigger nav-avatar-trigger-global" id="avatarGlobalTrigger">
             <view class="nav-avatar-inner">
               <image v-if="avatarUrl" class="nav-avatar-img" :src="avatarUrl" mode="aspectFill"></image>
               <text v-else class="nav-avatar-text">{{ avatarLetter }}</text>
             </view>
           </view>
           <view class="nav-avatar-dropdown" id="avatarDropdown">
             <view class="avatar-dropdown-item points-display" id="avatarPointsDisplay">
               <text class="points-label">积分</text>
               <text class="points-badge" id="avatarPointsBadge">...</text>
             </view>
             <view class="avatar-dropdown-divider"></view>
             <view class="avatar-dropdown-item" data-href="#/package-user/points/index" onclick="window.__topNavGo('#/package-user/points/index')">积分中心 ›</view>
             <view class="avatar-dropdown-divider"></view>
             <view class="avatar-dropdown-item" onclick="window._xc_doLogout()">退出登录</view>
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
  sidebar.querySelector('#sidebarCloseGlobal').onclick = function() { toggleSidebar() }
  sidebar.querySelector('#sidebarUserSetting').onclick = function() { toggleSidebar(); go('#/pages/profile/index') }
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
  })

window._xc_toggleSidebar = function() { toggleSidebar() }
window._xc_toggleGroup = function(headerEl) { var g = headerEl.parentElement; if (g) g.classList.toggle('collapsed') }

// 从共享模块获取分组数据和工具函数，未加载时自动初始化
if (!window.__sidebarTypes) {
  window.__sidebarTypes = (function() {
    'use strict'
    var TYPE_ORDER = ['qimen', 'paipan', 'bazi', 'liuyao', 'meihua', 'ziwei', 'taluo', 'tarot']
    var TYPE_META = {
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
      if (d.avatar) {
        var img = document.getElementById('sidebarUserAvatar')
        if (img) { img.src = d.avatar; img.style.display = 'block' }
        if (letterEl) letterEl.style.display = 'none'
      }
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
    document.body.removeEventListener('click', window.__sidebarClickAway)
    return
  }
  sidebar.classList.add('open'); overlay.classList.add('show')
  uni.$emit('sidebar-opened')
  document.body.removeEventListener('click', window.__sidebarClickAway)
  window.__sidebarClickAway = function(e) {
    var s = document.getElementById('tarotSidebarGlobal')
    if (s && s.classList.contains('open') && !s.contains(e.target)) {
      e.stopPropagation(); s.classList.remove('open')
      document.getElementById('sidebarOverlayGlobal').classList.remove('show')
      document.body.removeEventListener('click', window.__sidebarClickAway)
    }
  }
  setTimeout(function() { document.body.addEventListener('click', window.__sidebarClickAway) }, 200)
  var listEl = document.getElementById('sidebarListGlobal')
  if (!listEl) return
  // 并行加载用户面板
  _loadSidebarUserPanel()
  // 30 秒内缓存
  var now = Date.now()
  if (window.__sidebarCache && (now - window.__sidebarCache.ts) < 30000) {
    _renderSidebarGroups(window.__sidebarCache.groups, listEl)
    return
  }
  listEl.innerHTML = '<div class="sidebar-empty">加载中...</div>'
  var recordsLoaded = false, tarotLoaded = false
  var allRecords = [], tarotItems = []
  function _renderMerged() {
    if (!recordsLoaded || !tarotLoaded) return
    tarotItems.forEach(function(c) {
      allRecords.push({ id: 'tarot_' + c.id, app_type: 'tarot', question: c.title || c.spread_name || '塔罗解读', created_at: c.updated_at || c.created_at, _tarotConvId: c.id })
    })
    if (!allRecords.length) { listEl.innerHTML = '<div class="sidebar-empty">暂无历史记录</div>'; return }
    var groups = _groupRecords(allRecords)
    window.__sidebarCache = { ts: Date.now(), groups: groups }
    _renderSidebarGroups(groups, listEl)
  }
  uni.request({ url: '/api/records?per_page=50', method: 'GET', success: function(res) {
    allRecords = res.data.records || []; recordsLoaded = true; _renderMerged()
  }, fail: function() { recordsLoaded = true; _renderMerged() }})
  uni.request({ url: '/api/tarot/conversations', method: 'GET', success: function(res) {
    tarotItems = res.data || []; if (!Array.isArray(tarotItems)) tarotItems = []; tarotLoaded = true; _renderMerged()
  }, fail: function() { tarotLoaded = true; _renderMerged() }})
}

// 渲染分组历史（共享函数，避免与 sidebar.js 重复）
function _renderSidebarGroups(groups, listEl) {
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
      var text = _escHtml(r.question || '(无问题)')
      var clickAction = r._tarotConvId
        ? 'onclick="window._showTarotConv(' + r._tarotConvId + ')"'
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

// 塔罗对话查看（挂在 window 上避免 tree-shaking）
window._showTarotConv = function(cid) {
  uni.request({ url: '/api/tarot/conversations/' + cid, method: 'GET', success: function(res) {
    var d = res.data
    if (!d) return
    var overlay = document.getElementById('historyDetailOverlayGlobal')
    var title = document.getElementById('historyDetailTitle')
    var content = document.getElementById('historyDetailContent')
    if (overlay) overlay.classList.add('open')
    if (title) title.textContent = d.title || d.spread_name || '塔罗解读'
    // 解析对话消息，显示最后一条 AI 回复
    var msgs = []
    try { msgs = JSON.parse(d.messages_json || '[]') } catch(_) {}
    var aiMsgs = msgs.filter(function(m) { return m.role === 'assistant' })
    var lastMsg = aiMsgs.length ? aiMsgs[aiMsgs.length - 1].content : ''
    if (content) content.innerHTML = '<div class="history-markdown">' + _escHtml(lastMsg || '无解读内容') + '</div>'
    window._xc_toggleSidebar()
  }})
}

// 历史详情弹窗（挂在 window 上避免 tree-shaking）
window._showHistoryDetail = function(rid) {
  uni.request({ url: '/api/records/' + rid, method: 'GET', success: function(res) {
    var d = res.data
    var overlay = document.getElementById('historyDetailOverlayGlobal')
    var title = document.getElementById('historyDetailTitle')
    var content = document.getElementById('historyDetailContent')
    if (overlay) overlay.classList.add('open')
    if (title) title.textContent = d.question || '历史记录'
    if (content) content.innerHTML = '<div class="history-markdown">' + (d.result_html || '') + '</div>'
    window._xc_toggleSidebar()
  }})
}
window._closeHistoryDetail = function() {
  var overlay = document.getElementById('historyDetailOverlayGlobal')
  if (overlay) overlay.classList.remove('open')
}

function onShowLogin() {
  emit('show-login')
  try {
    window._openLoginModal()
  } catch(_) {}
}
var avatarUrl = ref('')
var avatarLetter = ref('')
var avatarLoaded = false
function loadAvatar() {
  if (avatarLoaded || !props.isLoggedIn) return
  avatarLoaded = true
  window.__avatarLoaded = true
  var cachedUser = uni.getStorageSync('xc_user')
  if (cachedUser) avatarLetter.value = cachedUser.charAt(0).toUpperCase()
  uni.request({ url: '/api/me', method: 'GET' }).then(function(res) {
    var d = res.data
    if (d && d.guest) {
      // Safari 可能在页面刚加载时延迟发送 Cookie，不要因为 /api/me 返回 guest 就清除登录态
      // 只要 localStorage 中还有 token，前端就保持登录状态
      // 真正的 session 过期会在后续 API 调用返回 401 时自然处理
    } else if (d && d.username) {
      avatarLetter.value = d.username.charAt(0).toUpperCase()
      if (d.avatar) avatarUrl.value = d.avatar
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
    if (d.debug_code) { var codeEl = document.getElementById('tnLoginPhoneCode'); if (codeEl) codeEl.value = d.debug_code }
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
    if (d.debug_code) { var codeEl = document.getElementById('tnLoginEmailCode'); if (codeEl) codeEl.value = d.debug_code }
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
var TAB_PATHS = ['/', '/pages/qimen/index', '/pages/bazi-index/index', '/pages/tarot/index', '/pages/liuyao/index', '/pages/meihua/index', '/pages/ziwei/index', '/pages/zeji/index', '/pages/calendar/index', '/pages/community/index', '/pages/profile/index']
var TAB_ROUTES = ['pages/index/index', 'pages/qimen/index', 'pages/bazi-index/index', 'pages/tarot/index', 'pages/liuyao/index', 'pages/meihua/index', 'pages/ziwei/index', 'pages/zeji/index', 'pages/calendar/index', 'pages/community/index', 'pages/profile/index']
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

    // 重置：显示所有按钮
    bar.querySelectorAll('.nav-btn:not(.nav-btn-more)').forEach(function(b) {
      b.style.display = ''
    })
    more.style.display = 'none'
    moreMenu.innerHTML = ''

    // 检测溢出：按钮右边界超出视口右边界
    // ⚠️ 不能用 bar.getBoundingClientRect().right 作为阈值，
    // 移动端 nav-btn-bar 可能宽于视口（flex-shrink:0），
    // 导致所有按钮都在 bar 内部不溢出，但实际上已经超出屏幕
    var viewportWidth = window.innerWidth
    var overflow = []
    bar.querySelectorAll('.nav-btn:not(.nav-btn-more)').forEach(function(btn) {
      if (btn.getBoundingClientRect().right > viewportWidth - 10) overflow.push(btn)
    })

    if (overflow.length > 0) {
      overflow.forEach(function(btn) {
        btn.style.display = 'none'
        // 在"更多"下拉中创建克隆项
        var clone = document.createElement('view')
        clone.className = 'nav-btn-drop-item'
        clone.setAttribute('data-href', btn.getAttribute('data-href'))
        clone.textContent = btn.textContent.replace(' ▾','').trim()
        clone.onclick = function(e) {
          e.stopPropagation()
          var href = clone.getAttribute('data-href')
          if (href) go(href)
          more.classList.remove('open')
        }
        moreMenu.appendChild(clone)
      })
      more.style.display = ''
    } else {
      // 没有溢出时明确隐藏"更多"按钮
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
  // 暴露 go 到 window 方便调试
  window.__topNavGo = go
  window.__topNavGo.avatarLoad = loadAvatar
  // 初始路由高亮同步
  nextTick(() => { syncNavHighlight(); updateNavOverflow() })
  // 等布局稳定后再检测一次，防止字体加载导致的测量偏差
  setTimeout(updateNavOverflow, 500)
  // 窗口 resize 时重新检测按钮溢出（仅注册一次，避免多实例重复监听）
  if (!window.__topnavResizeDelegated) {
    window.__topnavResizeDelegated = true
    window.addEventListener('resize', updateNavOverflow)
  }
  // 初始主题DOM同步（render effect bug: :data-theme 不响应）
  try {
    document.documentElement.setAttribute('data-theme', props.theme)
    var root = document.querySelector('.page-root')
    if (root) root.setAttribute('data-theme', props.theme)
    var icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = props.theme === 'dark' ? '🌙' : '☀️'
  } catch(_) {}
  // 给所有导航元素添加 data-href 属性
  try {
    var wrap = document.querySelector('.topnav-wrap')
    if (wrap) {
      // 事件委托: 在 topnav-wrap 上监听所有 click，找到有 data-href 的元素
      // ⚠️ 跳过 data-action="auth" 的元素（登录/注册按钮），避免拦截 emit 事件
      wrap.addEventListener('click', function(e) {
        var target = e.target
        var maxDepth = 10
        // 先检查是否点击了 auth 按钮（有 data-action="auth" 的元素），如果是则不拦截
        var checkTarget = target
        while (checkTarget && checkTarget !== wrap && maxDepth > 0) {
          if (checkTarget.dataset && checkTarget.dataset.action === 'auth') return // 不拦截
          checkTarget = checkTarget.parentElement
          maxDepth--
        }
        // 重置 maxDepth，查找 data-href 导航元素
        maxDepth = 10
        target = e.target
        while (target && target !== wrap && maxDepth > 0) {
          if (target.dataset && target.dataset.href) {
            // 找到了带 data-href 的元素
            e.preventDefault()
            e.stopPropagation()
            go(target.dataset.href)
            // 如果移动端菜单打开，关闭它（capture阶段stopPropagation阻止了@click中的closeMobileMenu）
            var menuEl = document.getElementById('mobileMenu')
            if (menuEl && menuEl.classList.contains('open')) {
              menuEl.classList.remove('open')
              ;['mobileSubQimen', 'mobileSubBazi', 'mobileSubMore'].forEach(function(id) {
                var sub = document.getElementById(id)
                if (sub) sub.classList.remove('open')
              })
            }
            return
          }
          target = target.parentElement
          maxDepth--
        }
      }, true) // capture phase — 比 Vue 的事件代理更早执行
    }
  } catch (_) {}
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
            if (dd) { document.querySelectorAll('#avatarDropdown').forEach(function(x) { x.classList.remove('open') }); dd.classList.add('open') }
          }
          if (!window.__avatarLoaded) loadAvatar()
          return
        }
      }
    }, true)
    document.addEventListener('click', function(e) {
       for (var el = e.target; el; el = el.parentElement) {
         if (el.classList && (el.classList.contains('nav-avatar-trigger-global') || el.classList.contains('nav-avatar-wrap') || el.id === 'avatarDropdown')) return
       }
       document.querySelectorAll('#avatarDropdown').forEach(function(x) { x.classList.remove('open') })
     }, true)
    // 移动端 nav-dropdown 点击切换（移动端无 hover）
    document.addEventListener('touchstart', function(e) {
      var touchedDropTrigger = false
      for (var el = e.target; el; el = el.parentElement) {
        if (el.classList && el.classList.contains('nav-drop-trigger')) {
          touchedDropTrigger = true
          var dropdown = el.closest('.nav-dropdown')
          if (dropdown) {
            var isOpen = dropdown.classList.contains('open')
            document.querySelectorAll('.nav-dropdown.open').forEach(function(d) { d.classList.remove('open') })
            if (!isOpen) dropdown.classList.add('open')
          }
          return
        }
        if (el.classList && el.classList.contains('nav-avatar-trigger-global')) {
          var wrap = el.closest('.nav-avatar-wrap')
          if (wrap) {
            var dd = wrap.querySelector('#avatarDropdown')
            if (dd) { document.querySelectorAll('#avatarDropdown').forEach(function(x) { x.classList.remove('open') }); dd.classList.add('open') }
          }
          if (!window.__avatarLoaded) loadAvatar()
          return
        }
      }
      // 点击空白处关闭所有下拉
      if (!touchedDropTrigger) {
        document.querySelectorAll('.nav-dropdown.open').forEach(function(d) { d.classList.remove('open') })
      }
    }, true)
    // 移动端 nav-dropdown 点击切换（兼容 click）
    document.addEventListener('click', function(e) {
      for (var el = e.target; el; el = el.parentElement) {
        if (el.classList && el.classList.contains('nav-drop-trigger')) {
          var dropdown = el.closest('.nav-dropdown')
          if (dropdown) {
            var isOpen = dropdown.classList.contains('open')
            document.querySelectorAll('.nav-dropdown.open').forEach(function(d) { d.classList.remove('open') })
            if (!isOpen) dropdown.classList.add('open')
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
      { wrap: 'tnLoginPass-wrap', id: 'tnLoginPass', type: 'password', placeholder: '密码' },
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
        w.appendChild(inp)
      }
    })
  } catch(_) {}
})
</script>

<style scoped>
/* ═══ 容器 ═══ */
.topnav-wrap { position: relative; z-index: 100; }

/* ═══ 顶部导航栏 ═══ */
.topnav {
  position: sticky;
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
.topnav-sidebar-btn { display:inline-flex; font-size:1.6rem; color:var(--text-2); cursor:pointer; padding:6px 10px; margin-right:4px; flex-shrink:0; align-items:center; border-radius:8px; }
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
}

/* ═══ 第 2 行：按钮栏 ═══ */
.nav-btn-bar {
  display: flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 2px;
  flex-shrink: 0;
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
  background: var(--card-bg);
  border: 1px solid var(--card-border);
  border-radius: 10px;
  padding: 6px 0;
  z-index: 200;
  box-shadow: 0 8px 32px rgba(0,0,0,0.2);
  pointer-events: none;
  transition: opacity 0.2s ease, transform 0.2s ease, visibility 0.2s;
}
.nav-btn-has-drop:hover .nav-btn-drop-menu,
.nav-btn-has-drop:active .nav-btn-drop-menu,
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
  transition: background 0.15s, color 0.15s;
}
.nav-btn-drop-item:hover { background: var(--accent-glow); color: var(--accent); }
.nav-btn-drop-item.current,
.nav-btn-drop-item.menu-active { color: var(--accent); font-weight: 600; }

/* "更多"按钮 */
.nav-btn-more { position: relative; }

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

/* ═══ 响应式 ═══ */
@media (max-width: 768px) {
  .topnav { padding: 0 10px; }
  .nav-btn { padding: 3px 7px; font-size: 0.7rem; }
  .topnav-right { margin-left: 0; }
  .nav-btn-bar { flex-shrink: 1; }
}
@media (max-width: 480px) {
  .nav-btn { padding: 3px 6px; font-size: 0.65rem; }
}

/* ═══ 用户头像 ═══ */
.nav-avatar-wrap { position: relative; display: flex; align-items: center; cursor: pointer; margin-left: 8px; }
.nav-avatar-inner { width: 38px; height: 38px; border-radius: 50%; overflow: hidden; background: var(--accent-glow); display: flex; align-items: center; justify-content: center; }
.nav-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.nav-avatar-text { font-size: 0.95rem; font-weight: 700; color: var(--accent); }
.nav-avatar-dropdown { position: absolute; top: 100%; right: 0; margin-top: 8px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 4px 0; min-width: 120px; display: none; box-shadow: var(--card-shadow); z-index: 200; }
.nav-avatar-dropdown.open { display: block; }
.avatar-dropdown-item { padding: 10px 16px; font-size: 0.78rem; color: var(--text-2); cursor: pointer; white-space: nowrap; }
.avatar-dropdown-item:hover { background: var(--accent-glow); color: var(--accent); }
.points-display { display: flex; align-items: center; justify-content: space-between; cursor: default; }
.points-display:hover { background: transparent; color: var(--text-2); }
.points-label { font-size: 0.78rem; color: var(--text-3); }
.points-badge { font-size: 0.82rem; font-weight: 700; color: var(--accent); }
.avatar-dropdown-divider { height: 1px; background: var(--card-border); margin: 2px 0; }

/* ═══ 登录/注册弹窗 ═══ */
.modal-overlay { position: fixed; inset: 0; z-index: 999; background: rgba(0,0,0,0.55); display: none; align-items: center; justify-content: center; backdrop-filter: blur(4px); }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 20px; padding: 28px 32px; max-width: 400px; width: 90%; box-shadow: var(--card-shadow); }
.modal-title { font-family: var(--font-serif); font-size: 1.2rem; text-align: center; color: var(--text-1); margin-bottom: 20px; }
.field { margin-bottom: 14px; }
.field-label { font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; display: block; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }
.oauth-divider { display: flex; align-items: center; margin: 16px 0 12px; }
.oauth-divider::before, .oauth-divider::after { content: ''; flex: 1; height: 1px; background: var(--card-border); }
.oauth-divider-text { font-size: 0.72rem; color: var(--text-3); padding: 0 12px; white-space: nowrap; }
.oauth-btns { display: flex; gap: 10px; }
.oauth-btn { flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px; padding: 10px; border-radius: 10px; border: 1px solid var(--card-border); cursor: pointer; transition: all 0.2s; background: var(--input-bg); }
.oauth-btn:hover { border-color: var(--accent); background: var(--accent-glow); }
.oauth-btn-qq .oauth-btn-icon { width: 24px; height: 24px; border-radius: 50%; background: #12b7f5; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.62rem; font-weight: 700; flex-shrink: 0; }
.oauth-btn-wechat .oauth-btn-icon { width: 24px; height: 24px; border-radius: 6px; background: #07c160; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.62rem; font-weight: 700; flex-shrink: 0; }
.oauth-btn-label { font-size: 0.78rem; color: var(--text-2); }
.oauth-btn-gitee .oauth-btn-icon { width: 24px; height: 24px; border-radius: 50%; background: #c71d23; color: #fff; display: flex; align-items: center; justify-content: center; font-size: 0.7rem; font-weight: 700; flex-shrink: 0; }
.login-tabs { display: flex; gap: 4px; margin-bottom: 16px; background: var(--input-bg); border-radius: 10px; padding: 3px; }
.login-tab { flex: 1; text-align: center; padding: 8px 0; border-radius: 8px; font-size: 0.78rem; color: var(--text-3); cursor: pointer; transition: all 0.2s; }
.login-tab.active { background: var(--accent); color: #fff; font-weight: 600; }
.code-field { margin-bottom: 10px; }
.code-btn { white-space: nowrap; flex-shrink: 0; }
.code-btn[disabled] { opacity: 0.5; pointer-events: none; }
.modal-hint { font-size: 0.7rem; color: var(--text-3); text-align: center; margin-top: 12px; line-height: 1.4; }

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
