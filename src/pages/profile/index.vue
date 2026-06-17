<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- 页面头部 -->
      <section class="tool-hero">
        <view class="tool-hero-content">
          <view class="section-tag">个人中心</view>
          <view class="tool-hero-title">个人中心 · 账号管理</view>
          <view class="tool-hero-desc">账号信息 · 安全设置 · 跨设备同步</view>
        </view>
      </section>

      <!-- 工具面板 -->
      <section class="section">
        <view class="tool-container" style="max-width:560px;">

          <!-- 头像卡片 -->
          <view class="profile-card" v-if="isLoggedIn">
            <view class="profile-card-avatar" @tap="clickProfileAvatar" title="点击更换头像">
              <image v-if="userInfo.avatar" :src="userInfo.avatar" class="profile-card-avatar-img" mode="aspectFill" @error="handleProfileAvatarError" />
              <text v-else class="profile-card-avatar-text">{{ profileInitial }}</text>
            </view>
            <view class="profile-card-info">
              <text class="profile-card-name">{{ displayUsername }}</text>
              <text class="profile-card-meta">注册于 {{ userInfo.regDate }} · {{ profiles.length }} 个存档</text>
            </view>
          </view>

          <!-- 未登录 -->
          <view class="profile-empty" v-if="!isLoggedIn">
            <view class="profile-empty-icon">🔒</view>
            <text class="profile-empty-text">登录后查看账号信息</text>
            <view class="btn btn-accent btn-sm" style="margin-top:16px;" @tap="showLoginBtn">立即登录</view>
          </view>

          <!-- 账号安全分组 -->
          <view class="settings-group" v-if="isLoggedIn">
            <view class="settings-group-title">账号安全</view>
            <view class="settings-list">
              <!-- 修改用户名 -->
              <view class="settings-item" @tap="toggleAccordion('username')">
                <text class="settings-item-icon settings-icon-user">ID</text>
                <text class="settings-item-label">修改用户名</text>
                <text class="settings-item-value" id="bindUsername">{{ displayUsername }}</text>
                <text class="settings-item-arrow">{{ accordionOpen === 'username' ? '▲' : '›' }}</text>
              </view>
              <view class="settings-accordion" v-show="accordionOpen === 'username'">
                <view class="settings-accordion-inner">
                  <view class="field"><view id="asNewUsername-wrap" class="dom-input-wrap"></view></view>
                  <view class="field" v-if="hasPassword"><view id="asCurrPassForUser-wrap" class="dom-input-wrap"></view></view>
                  <view class="modal-error" id="asUsernameError"></view>
                  <view class="btn btn-accent btn-sm" id="asUsernameBtn" onclick="window._xc_changeUsername()" style="float:right">确认修改</view>
                </view>
              </view>

              <!-- 密码 -->
              <view class="settings-item" @tap="toggleAccordion('password')">
                <text class="settings-item-icon settings-icon-password">PW</text>
                <text class="settings-item-label">{{ hasPassword ? '修改密码' : '设置密码' }}</text>
                <text class="settings-item-value" id="bindPassword">{{ hasPassword ? '已设置' : '未设置' }}</text>
                <text class="settings-item-arrow">{{ accordionOpen === 'password' ? '▲' : '›' }}</text>
              </view>
              <view class="settings-accordion" v-show="accordionOpen === 'password'">
                <view class="settings-accordion-inner">
                  <view class="field" v-if="hasPassword"><view id="asOldPass-wrap" class="dom-input-wrap"></view></view>
                  <view class="field"><view id="asNewPass-wrap" class="dom-input-wrap"></view></view>
                  <view class="modal-error" id="asPassError"></view>
                  <view class="btn btn-accent btn-sm" id="asPasswordBtn" onclick="window._xc_changePassword()" style="float:right">{{ hasPassword ? '确认修改' : '设置密码' }}</view>
                </view>
              </view>

              <!-- 邮箱 -->
              <view class="settings-item" @tap="toggleAccordion('email')">
                <text class="settings-item-icon settings-icon-email">@</text>
                <text class="settings-item-label">绑定邮箱</text>
                <text class="settings-item-value" id="bindEmail">未绑定</text>
                <text class="settings-item-arrow">{{ accordionOpen === 'email' ? '▲' : '›' }}</text>
              </view>
              <view class="settings-accordion" v-show="accordionOpen === 'email'">
                <view class="settings-accordion-inner">
                  <view class="field"><view id="asBindEmail-wrap" class="dom-input-wrap"></view></view>
                  <view class="field code-field" style="display:flex;gap:8px;">
                    <view id="asBindEmailCode-wrap" class="dom-input-wrap" style="flex:1;"></view>
                    <view class="btn btn-outline btn-sm" onclick="window._xc_sendBindEmailCode()" id="asBindEmailBtn">获取验证码</view>
                  </view>
                  <view class="modal-error" id="asBindEmailError"></view>
                  <view class="btn btn-accent btn-sm" id="asBindEmailSubmit" onclick="window._xc_bindEmail()" style="float:right">绑定邮箱</view>
                </view>
              </view>

              <!-- 第三方 -->
              <view class="settings-item" @tap="toggleAccordion('oauth')">
                <text class="settings-item-icon settings-icon-oauth">↗</text>
                <text class="settings-item-label">第三方账号</text>
                <text class="settings-item-value" id="bindGitee">未绑定</text>
                <text class="settings-item-arrow">{{ accordionOpen === 'oauth' ? '▲' : '›' }}</text>
              </view>
              <view class="settings-accordion" v-show="accordionOpen === 'oauth'">
                <view class="settings-accordion-inner">
                  <view class="settings-oauth-row" v-for="item in oauthProviders" :key="item.key">
                    <view class="settings-oauth-left">
                      <text class="settings-oauth-icon">{{ item.icon }}</text>
                      <text class="settings-oauth-label">{{ item.name }}</text>
                    </view>
                    <view class="settings-oauth-right">
                      <text class="settings-oauth-status" v-if="item.bound" style="color:var(--success);">已绑定</text>
                      <view class="btn btn-outline btn-sm" v-if="item.bound" @tap="unbindOAuth(item.key)">解除绑定</view>
                      <view class="btn btn-outline btn-sm" v-else @tap="bindOAuth(item.key)">绑定</view>
                    </view>
                  </view>
                </view>
              </view>
            </view>
          </view>

          <view class="settings-group" v-if="isLoggedIn">
            <view class="settings-group-title">问事体验</view>
            <view class="settings-list">
              <view class="settings-item guidance-setting-item" @tap="toggleQuestionGuidance">
                <text class="settings-item-icon settings-icon-oauth">问</text>
                <view class="settings-item-main">
                  <text class="settings-item-label">问事引导</text>
                  <text class="settings-item-desc">开启后，每次解读前会先通过几轮对话帮你理清所问，并自动推荐适合的解读方式。</text>
                </view>
                <view class="settings-switch" :class="{ active: questionGuidanceEnabled }">
                  <text></text>
                </view>
              </view>
            </view>
          </view>

          <view class="settings-group danger-group" v-if="isLoggedIn">
            <view class="settings-group-title">账号注销</view>
            <view class="settings-list">
              <view class="settings-item" @tap="toggleAccordion('deleteAccount')">
                <text class="settings-item-icon settings-icon-danger">删</text>
                <view class="settings-item-main">
                  <text class="settings-item-label">注销账号与删除数据</text>
                  <text class="settings-item-desc">清除命盘、历史、对话和个人资料；订单与必要审计记录会按合规要求保留。</text>
                </view>
                <text class="settings-item-arrow">{{ accordionOpen === 'deleteAccount' ? '▲' : '›' }}</text>
              </view>
              <view class="settings-accordion" v-show="accordionOpen === 'deleteAccount'">
                <view class="settings-accordion-inner">
                  <text class="delete-account-warning">此操作不可恢复。请先确认已导出需要保留的记录。</text>
                  <view class="field"><view id="asDeleteConfirm-wrap" class="dom-input-wrap"></view></view>
                  <view class="field" v-if="hasPassword"><view id="asDeletePassword-wrap" class="dom-input-wrap"></view></view>
                  <view class="modal-error" id="asDeleteError"></view>
                  <view class="btn btn-danger btn-sm" id="asDeleteAccountBtn" @tap="deleteAccount">确认注销账号</view>
                </view>
              </view>
            </view>
          </view>

          <!-- 退出登录 -->
          <view class="settings-logout" v-if="isLoggedIn" @tap="doLogout">
            <text class="settings-logout-text">退出登录</text>
          </view>

          <!-- 隐藏的弹窗占位（保留给全局API兼容，不显示） -->
          <view id="accountSettingsModal" style="display:none !important;"></view>
        </view>
      </section>
    </view>


  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  uni.setStorageSync('xc_theme', theme.value)
  try {
    document.documentElement.setAttribute('data-theme', theme.value); document.body.setAttribute('data-theme', theme.value); const root = document.querySelector('.page-root')
    if (root) root.setAttribute('data-theme', theme.value)
    const icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = theme.value === 'dark' ? '🌙' : '☀️'
  } catch(_) {}
}

const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { resetProfileSessionState() })
const hasPassword = ref(uni.getStorageSync('xc_has_password') === '1')
const questionGuidanceStorageKey = 'xc_home_question_guidance_enabled_v1'
const questionGuidanceEnabled = ref(readQuestionGuidanceEnabled())
const accordionOpen = ref('')
const accordionInputsCreated = {}

function currentUserScopedStorageKey(base) {
  let userKey = 'guest'
  try {
    const raw = uni.getStorageSync('xc_user')
    const user = typeof raw === 'string' ? JSON.parse(raw) : raw
    userKey = String((user && (user.id || user.username || user.phone)) || 'guest')
  } catch (_) {}
  return base + ':' + userKey
}

function readQuestionGuidanceEnabled() {
  try {
    const raw = uni.getStorageSync(currentUserScopedStorageKey(questionGuidanceStorageKey))
    if (raw === '' || raw === null || typeof raw === 'undefined') return true
    if (typeof raw === 'boolean') return raw
    return JSON.parse(raw) !== false
  } catch(_) {
    return true
  }
}

function toggleQuestionGuidance() {
  questionGuidanceEnabled.value = !questionGuidanceEnabled.value
  uni.setStorageSync(currentUserScopedStorageKey(questionGuidanceStorageKey), JSON.stringify(questionGuidanceEnabled.value))
  uni.showToast({ title: questionGuidanceEnabled.value ? '已开启问事引导' : '已关闭问事引导', icon: 'none' })
}
function normalizeAvatarUrl(src) {
  const value = String(src || '').trim()
  if (!value || value.includes('/static/images/logo.') || value.includes('/logo.webp')) return ''
  return value
}
function normalizeUsername(value) {
  if (!value) return '用户'
  if (typeof value === 'string') return value.trim() || '用户'
  if (typeof value === 'number') return String(value)
  if (typeof value === 'object') {
    return String(value.username || value.phone || value.id || '用户').trim() || '用户'
  }
  return String(value).trim() || '用户'
}
function toggleAccordion(name) {
  accordionOpen.value = accordionOpen.value === name ? '' : name
  if (accordionOpen.value === name && !accordionInputsCreated[name]) {
    setTimeout(function() { createAccordionInputs(name) }, 50)
  }
}
function createAccordionInputs(name) {
  var wrapMap = {
    username: ['asNewUsername-wrap', 'asCurrPassForUser-wrap'],
    password: ['asOldPass-wrap', 'asNewPass-wrap'],
    email: ['asBindEmail-wrap', 'asBindEmailCode-wrap'],
    deleteAccount: ['asDeleteConfirm-wrap', 'asDeletePassword-wrap']
  }
  var wraps = wrapMap[name] || []
  wraps.forEach(function(wrapId) {
    var el = document.getElementById(wrapId)
    if (el && !el.querySelector('input')) {
      var inp = document.createElement('input')
      if (wrapId.indexOf('Code') > -1) inp.type = 'text'
      else if (wrapId.indexOf('Email') > -1) inp.type = 'email'
      else if (wrapId.indexOf('Phone') > -1) inp.type = 'tel'
      else inp.type = wrapId.indexOf('Pass') > -1 ? 'text' : 'text'
      inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;transition:border-color 0.2s,box-shadow 0.2s'
      if (wrapId.indexOf('Pass') > -1) { inp.style.cssText += ';-webkit-text-security:disc;-moz-text-security:disc;text-security:disc;' }
      inp.onfocus = function() { this.style.borderColor = 'var(--accent)'; this.style.boxShadow = '0 0 0 2px var(--accent-glow)' }
      inp.onblur = function() { this.style.borderColor = 'var(--input-border)'; this.style.boxShadow = 'none' }
      if (wrapId === 'asNewUsername-wrap') inp.placeholder = '输入新用户名'
      else if (wrapId === 'asCurrPassForUser-wrap') inp.placeholder = '输入当前密码'
      else if (wrapId === 'asOldPass-wrap') inp.placeholder = '输入当前密码'
      else if (wrapId === 'asNewPass-wrap') inp.placeholder = '输入新密码（至少4位）'
      else if (wrapId === 'asBindEmail-wrap') inp.placeholder = 'your@email.com'
      else if (wrapId === 'asBindEmailCode-wrap') inp.placeholder = '验证码'
      else if (wrapId === 'asDeleteConfirm-wrap') inp.placeholder = '输入：注销账号'
      else if (wrapId === 'asDeletePassword-wrap') inp.placeholder = '输入当前密码'
      else inp.placeholder = '至少4个字符'
      if ((wrapId === 'asCurrPassForUser-wrap' || wrapId === 'asDeletePassword-wrap') && !hasPassword.value) { el.style.display = 'none'; return }
      el.appendChild(inp)
    }
  })
  accordionInputsCreated[name] = true
}

function showLoginBtn() {
  try {
    _openLoginModal()
    var e = document.getElementById('tnLoginError'); if (e) e.textContent = ''
  } catch(_) {}
}

async function doLogout() {
  try {
    await uni.request({ url: '/api/logout', method: 'POST' })
  } catch (_) {}
  uni.removeStorageSync('xc_token')
  uni.removeStorageSync('xc_user')
  resetProfileSessionState()
  try {
    sessionStorage.removeItem('_nav_query')
    window.__xcHomeMode = 'marketing'
    window.dispatchEvent(new CustomEvent('xc-auth-changed', { detail: { type: 'logout', loggedIn: false } }))
    window.dispatchEvent(new CustomEvent('xc-show-marketing-home'))
    window.dispatchEvent(new CustomEvent('xc-home-mode-changed', { detail: { mode: 'marketing' } }))
    uni.$emit('xc-auth-changed', { type: 'logout', loggedIn: false })
    if (window.location.hash !== '#/') window.history.replaceState({ marketing: 'home' }, '', '#/')
    uni.switchTab({ url: '/pages/index/index' })
  } catch(_) {}
  uni.showToast({ title: '已退出登录', icon: 'none' })
}

async function deleteAccount() {
  var btn = document.getElementById('asDeleteAccountBtn')
  var origText = btn ? btn.textContent : ''
  var confirmEl = document.querySelector('#asDeleteConfirm-wrap input')
  var passwordEl = document.querySelector('#asDeletePassword-wrap input')
  var errorEl = document.getElementById('asDeleteError')
  var confirmText = confirmEl ? confirmEl.value.trim() : ''
  var password = passwordEl ? passwordEl.value : ''
  if (errorEl) errorEl.textContent = ''
  if (confirmText !== '注销账号') {
    if (errorEl) errorEl.textContent = '请完整输入“注销账号”'
    return
  }
  if (hasPassword.value && !password) {
    if (errorEl) errorEl.textContent = '请输入当前密码'
    return
  }
  uni.showModal({
    title: '确认注销账号',
    content: '注销后命盘、历史、对话和个人资料将被删除或匿名化，此操作不可恢复。',
    confirmText: '确认注销',
    confirmColor: '#d76d5f',
    success: async function(result) {
      if (!result.confirm) return
      if (btn) { btn.textContent = '注销中...'; btn.style.opacity = '0.6'; btn.style.pointerEvents = 'none' }
      try {
        var res = await uni.request({ url: '/api/account/delete', method: 'POST', data: { confirm: confirmText, password: password } })
        var data = res.data || {}
        if (data.error) {
          if (errorEl) errorEl.textContent = data.error
          if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }
          return
        }
        uni.removeStorageSync('xc_token')
        uni.removeStorageSync('xc_user')
        uni.removeStorageSync('xc_avatar')
        uni.removeStorageSync('xc_has_password')
        resetProfileSessionState()
        try {
          window.dispatchEvent(new CustomEvent('xc-auth-changed', { detail: { type: 'logout', loggedIn: false } }))
          uni.$emit('xc-auth-changed', { type: 'logout', loggedIn: false })
          window.__xcHomeMode = 'marketing'
          if (window.location.hash !== '#/') window.history.replaceState({ marketing: 'home' }, '', '#/')
          uni.switchTab({ url: '/pages/index/index' })
        } catch(_) {}
        uni.showToast({ title: '账号已注销', icon: 'success' })
      } catch (e) {
        if (errorEl) errorEl.textContent = '注销失败，请稍后再试'
        if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }
      }
    }
  })
}

function showAccountSettings() {
  try {
    document.querySelectorAll('#accountSettingsModal').forEach(function(el) { el.classList.add('open') })
    // 在可见的弹窗内创建原生input
    var modal = document.querySelector('#accountSettingsModal.open') || document.querySelector('#accountSettingsModal')
    if (modal) {
      var wraps = ['asNewUsername-wrap', 'asNewPass-wrap']
      if (hasPassword.value) wraps.push('asCurrPassForUser-wrap', 'asOldPass-wrap')
      wraps.forEach(function(wrapId) {
        if (modal.querySelector('#' + wrapId) && !modal.querySelector('#' + wrapId + ' input')) {
          var wrap = modal.querySelector('#' + wrapId)
          var inp = document.createElement('input')
          inp.type = wrapId.indexOf('Pass') > -1 ? 'text' : 'text'
          inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;transition:border-color 0.2s,box-shadow 0.2s'
          if (wrapId.indexOf('Pass') > -1) inp.style.cssText += ';-webkit-text-security:disc;-moz-text-security:disc;text-security:disc;'
          inp.onfocus = function() { this.style.borderColor = 'var(--accent)'; this.style.boxShadow = '0 0 0 2px var(--accent-glow)' }
          inp.onblur = function() { this.style.borderColor = 'var(--input-border)'; this.style.boxShadow = 'none' }
          if (wrapId === 'asNewUsername-wrap') inp.placeholder = '输入新用户名'
          else if (wrapId === 'asCurrPassForUser-wrap') inp.placeholder = '输入当前密码'
          else if (wrapId === 'asOldPass-wrap') inp.placeholder = '输入当前密码'
          else inp.placeholder = '至少4个字符'
          wrap.appendChild(inp)
        }
      })
    }
    document.querySelectorAll('#asUsernameError').forEach(function(el) { el.textContent = '' })
    document.querySelectorAll('#asPassError').forEach(function(el) { el.textContent = '' })
  } catch(_) {}
}
function closeAccountSettings() {
  try { document.querySelectorAll('#accountSettingsModal').forEach(function(el) { el.classList.remove('open') }) } catch(_) {}
}
function onAccountSettingsOverlayTap(e) {
  try { if (e && e.target && e.target.id === 'accountSettingsModal') closeAccountSettings() } catch(_) {}
}
async function changeUsername() {
  var btn = document.getElementById('asUsernameBtn'); var origText = ''
  if (btn) { origText = btn.textContent; btn.textContent = '修改中...'; btn.style.opacity = '0.6'; btn.style.pointerEvents = 'none' }
  try { document.querySelectorAll('#asUsernameError').forEach(function(el) { el.textContent = '' }) } catch(_) {}
  var modal = document.querySelector('#accountSettingsModal.open') || document.querySelector('#accountSettingsModal')
  var u = modal ? modal.querySelector('#asNewUsername-wrap input') : null
  var p = modal ? modal.querySelector('#asCurrPassForUser-wrap input') : null
  var newUsername = u ? u.value.trim() : ''; var currPass = p ? p.value : ''
  if (!newUsername || newUsername.length < 2) { try { document.querySelectorAll('#asUsernameError').forEach(function(el) { el.textContent = '用户名至少2个字符' }) } catch(_) {}; if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; return }
  if (hasPassword.value && !currPass) { try { document.querySelectorAll('#asUsernameError').forEach(function(el) { el.textContent = '请输入当前密码' }) } catch(_) {}; if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; return }
  var data = { new_username: newUsername }
  if (hasPassword.value) data.current_password = currPass
  try {
    var res = await uni.request({ url: '/api/user/change-username', method: 'POST', data: data })
    var d = res.data
    if (d.error) { try { document.querySelectorAll('#asUsernameError').forEach(function(el) { el.textContent = d.error }) } catch(_) {}; if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; return }
    userInfo.username = normalizeUsername(newUsername); uni.setStorageSync('xc_user', { username: normalizeUsername(newUsername) })
    closeAccountSettings(); uni.showToast({ title: '用户名已更新', icon: 'success' }); setTimeout(function() { location.reload() }, 800)
  } catch (e) { try { document.querySelectorAll('#asUsernameError').forEach(function(el) { el.textContent = '网络错误' }) } catch(_) {}; if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' } }
}
async function changePassword() {
  var btn = document.getElementById('asPasswordBtn'); var origText = ''
  if (btn) { origText = btn.textContent; btn.textContent = '设置中...'; btn.style.opacity = '0.6'; btn.style.pointerEvents = 'none' }
  try { document.querySelectorAll('#asPassError').forEach(function(el) { el.textContent = '' }) } catch(_) {}
  var modal = document.querySelector('#accountSettingsModal.open') || document.querySelector('#accountSettingsModal')
  var oldEl = modal ? modal.querySelector('#asOldPass-wrap input') : null
  var newEl = modal ? modal.querySelector('#asNewPass-wrap input') : null
  var oldPass = oldEl ? oldEl.value : ''; var newPass = newEl ? newEl.value : ''
  if (hasPassword.value && !oldPass) { try { document.querySelectorAll('#asPassError').forEach(function(el) { el.textContent = '请输入当前密码' }) } catch(_) {}; if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; return }
  if (!newPass || newPass.length < 4) { try { document.querySelectorAll('#asPassError').forEach(function(el) { el.textContent = '新密码至少4个字符' }) } catch(_) {}; if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; return }
  var data = { new_password: newPass }
  if (hasPassword.value) data.old_password = oldPass
  try {
    var res = await uni.request({ url: '/api/user/change-password', method: 'POST', data: data })
    var d = res.data
    if (d.error) { try { document.querySelectorAll('#asPassError').forEach(function(el) { el.textContent = d.error }) } catch(_) {}; if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; return }
    hasPassword.value = true; uni.setStorageSync('xc_has_password', '1')
    closeAccountSettings(); uni.showToast({ title: '密码已设置', icon: 'success' }); setTimeout(function() { location.reload() }, 800)
  } catch (e) { try { document.querySelectorAll('#asPassError').forEach(function(el) { el.textContent = '网络错误' }) } catch(_) {}; if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' } }
}

const userInfo = reactive({
  username: normalizeUsername(uni.getStorageSync('xc_user')),
  regDate: '—',
  avatar: normalizeAvatarUrl(uni.getStorageSync('xc_avatar'))
})
const displayUsername = computed(() => normalizeUsername(userInfo.username))
const profileInitial = computed(() => displayUsername.value.charAt(0).toUpperCase())
function setProfileAvatar(src, shouldCache) {
  const avatar = normalizeAvatarUrl(src)
  userInfo.avatar = avatar
  if (shouldCache && avatar) uni.setStorageSync('xc_avatar', avatar)
  else if (!avatar) uni.removeStorageSync('xc_avatar')
}
function handleProfileAvatarError() {
  uni.removeStorageSync('xc_avatar')
  userInfo.avatar = ''
}

function resetProfileSessionState() {
  isLoggedIn.value = false
  profiles.value = []
  userInfo.username = '用户'
  userInfo.regDate = '—'
  userInfo.avatar = ''
}

async function refreshProfileSessionState() {
  if (!uni.getStorageSync('xc_token')) {
    resetProfileSessionState()
    return
  }
  isLoggedIn.value = true
  const cachedUser = uni.getStorageSync('xc_user')
  if (cachedUser) userInfo.username = normalizeUsername(cachedUser)
  try {
    const res = await uni.request({ url: '/api/me', method: 'GET' })
    const d = res.data && res.data[0] ? res.data[0] : res.data
    if (d && d.guest) {
      uni.removeStorageSync('xc_token')
      uni.removeStorageSync('xc_user')
      resetProfileSessionState()
      return
    }
    if (d && d.username) {
      isLoggedIn.value = true
      uni.setStorageSync('xc_token', 'session')
      uni.setStorageSync('xc_user', { username: normalizeUsername(d.username), id: d.id, phone: d.phone || '' })
      uni.setStorageSync('xc_has_password', d.has_password !== false ? '1' : '0')
      hasPassword.value = d.has_password !== false
      window.__xc_hasPassword = hasPassword.value
      userInfo.username = normalizeUsername(d.username)
      if (d.created_at) userInfo.regDate = new Date(d.created_at).toLocaleString('zh-CN')
      setProfileAvatar(d.avatar, !!normalizeAvatarUrl(d.avatar))
      if (typeof window !== 'undefined' && window._xc_loadBindings) window._xc_loadBindings()
    }
  } catch (_) {}
  await loadProfiles()
}

function onProfileAuthChanged(event) {
  const detail = event && event.detail ? event.detail : {}
  if (detail.type === 'logout' || detail.loggedIn === false) {
    resetProfileSessionState()
    return
  }
  if (detail.type === 'login' || detail.loggedIn === true) {
    isLoggedIn.value = true
    if (detail.user && detail.user.username) userInfo.username = normalizeUsername(detail.user.username)
    else if (uni.getStorageSync('xc_user')) userInfo.username = normalizeUsername(uni.getStorageSync('xc_user'))
    if (detail.user && detail.user.avatar) setProfileAvatar(detail.user.avatar, true)
    refreshProfileSessionState()
  }
}
const oauthProviders = reactive([
  { key: 'gitee', name: 'Gitee', icon: 'G', bound: false }
])
async function bindOAuth(provider) {
  try {
    var res = await uni.request({ url: '/api/oauth/' + provider + '/url' })
    var d = res.data
    if (d.error) { uni.showToast({ title: d.error, icon: 'none' }); return }
    if (!d.url) { uni.showToast({ title: '该方式暂未配置', icon: 'none' }); return }
    window.location.href = d.url
  } catch (e) {
    uni.showToast({ title: '获取授权链接失败', icon: 'none' })
  }
}
function unbindOAuth(provider) {
  var item = oauthProviders.find(function(p) { return p.key === provider })
  var name = item ? item.name : '第三方账号'
  uni.showModal({
    title: '解除绑定',
    content: '确定要解除绑定' + name + '吗？解除前请确认已设置密码或绑定邮箱。',
    success: async function(r) {
      if (!r.confirm) return
      try {
        var res = await uni.request({ url: '/api/unbind/oauth', method: 'POST', data: { provider: provider } })
        var d = res.data || {}
        if (d.error) { uni.showToast({ title: d.error, icon: 'none' }); return }
        uni.showToast({ title: '已解除绑定', icon: 'success' })
        if (item) item.bound = false
        if (window._xc_loadBindings) window._xc_loadBindings()
      } catch(e) {
        uni.showToast({ title: '解除绑定失败', icon: 'none' })
      }
    }
  })
}
const asForm = reactive({ newUsername: '', currPassForUser: '', oldPass: '', newPass: '' })

// 命理库
const profileTab = ref('self')
const profileSearch = ref('')
const profileSortIdx = ref(0)
const profiles = ref([])
const showProfileForm = ref(false)
const editingProfile = ref(null)
const formData = reactive({ name: '', genderIdx: 0, calTypeIdx: 0, birthDate: '', birthAddr: '', isDefault: false, profileType: 'self' })

const tabLabels = { self: '自身命盘', customer: '客户命盘', collect: '收藏命盘' }

// 格式化出生时间 (YYYYMMDDHHmm → YYYY-MM-DD HH:mm)
function formatBirthTime(bt) {
  if (!bt || bt.length < 8) return '—'
  const s = bt.padEnd(12, '0')
  const y = s.slice(0, 4), m = s.slice(4, 6), d = s.slice(6, 8)
  const h = s.slice(8, 10), min = s.slice(10, 12)
  let result = `${y}-${m}-${d}`
  if (h) result += ` ${h}:${min || '00'}`
  return result
}

// 相对时间
function timeAgo(date) {
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)
  if (diff < 60) return '刚刚'
  if (diff < 3600) return Math.floor(diff / 60) + '分钟前'
  if (diff < 86400) return Math.floor(diff / 3600) + '小时前'
  if (diff < 2592000) return Math.floor(diff / 86400) + '天前'
  return date.toLocaleDateString('zh-CN')
}

// 切换标签页
function switchTab(type) {
  profileTab.value = type
  // DOM直操作active class
  var tabs = ['self','customer','collect']
  var ids = ['profileTabSelf','profileTabCustomer','profileTabCollect']
  for (var i = 0; i < tabs.length; i++) {
    var el = document.getElementById(ids[i])
    if (el) { type === tabs[i] ? el.classList.add('active') : el.classList.remove('active') }
  }
  loadProfiles()
}

// 加载后端档案数据
async function loadProfiles() {
  if (!isLoggedIn.value) return
  try {
    const search = (document.getElementById('profileSearch')?.value || '').trim()
    const sort = profileSortIdx.value === 0 ? 'last_used' : 'created'
    let url = `/api/profiles?type=${profileTab.value}&sort=${sort}`
    if (search) url += `&search=${encodeURIComponent(search)}`
    const res = await uni.request({ url, method: 'GET' })
    const d = res.data
    if (d && !d.error) {
      profiles.value = d.profiles || (Array.isArray(d) ? d : [])
    }
  } catch (_) {
    profiles.value = []
  }
}

// 搜索/排序时重新加载
watch([profileSearch, profileSortIdx], () => {
  if (isLoggedIn.value) loadProfiles()
})
// 搜索值改为从DOM读取，profileSearch ref仅用于watch触发
// loadProfiles中实际用 document.getElementById('profileSearch')?.value

// 搜索过滤 (本地兜底)
const filteredProfiles = computed(() => {
  let list = profiles.value
  // tab 过滤 (本地兜底，后端已过滤时无需二次过滤)
  if (list.length > 0 && (list[0].profileType || list[0].profile_type)) {
    list = list.filter(p => (p.profileType || p.profile_type) === profileTab.value)
  }
  if (profileSearch.value) {
    const q = profileSearch.value.toLowerCase()
    list = list.filter(p => (p.name || '').toLowerCase().includes(q) || (p.birthTime || p.birth_time || '').includes(q))
  }
  // 排序
  if (profileSortIdx.value === 0) {
    // 最近使用
    list = [...list].sort((a, b) => {
      const ta = a.lastUsedAt || a.last_used_at || a.createdAt || a.created_at || ''
      const tb = b.lastUsedAt || b.last_used_at || b.createdAt || b.created_at || ''
      return tb.localeCompare(ta)
    })
  } else {
    // 创建时间
    list = [...list].sort((a, b) => {
      const ta = a.createdAt || a.created_at || ''
      const tb = b.createdAt || b.created_at || ''
      return tb.localeCompare(ta)
    })
  }
  return list
})

function selectProfile(p) {
  uni.setStorageSync('xc_selected_profile', JSON.stringify(p))
  uni.navigateTo({ url: '/pages/bazi-index/index?fromProfile=1' })
}

function hideProfileForm() {
  showProfileForm.value = false
  editingProfile.value = null
  var el = document.getElementById('profileFormCard')
  if (el) el.style.display = 'none'
}

function editProfile(p) {
  editingProfile.value = p
  formData.name = p.name || ''
  formData.genderIdx = (p.gender === '女') ? 1 : 0
  formData.calTypeIdx = (p.calType || p.cal_type) === '农历' ? 1 : 0
  formData.birthAddr = p.birthAddr || p.birth_addr || ''
  // 同步到原生DOM输入框
  var n = document.getElementById('profileName'); if (n) n.value = formData.name
  var a = document.getElementById('profileBirthAddr'); if (a) a.value = formData.birthAddr
  formData.isDefault = !!(p.isDefault || p.is_default)
  formData.profileType = p.profileType || p.profile_type || profileTab.value
  // 出生时间转换: YYYYMMDDHHmm → YYYY-MM-DD
  const bt = (p.birthTime || p.birth_time || '').padEnd(12, '0')
  if (bt.length >= 8) {
    formData.birthDate = bt.slice(0, 4) + '-' + bt.slice(4, 6) + '-' + bt.slice(6, 8)
  } else {
    formData.birthDate = ''
  }
  showProfileForm.value = true
  var el = document.getElementById('profileFormCard')
  if (el) el.style.display = 'block'
}

async function setDefaultProfile(id) {
  try {
    const res = await uni.request({
      url: `/api/profiles/${id}`,
      method: 'PUT',
      data: { isDefault: 1 }
    })
    const d = res.data
    if (d.error) { uni.showToast({ title: d.error, icon: 'none' }); return }
    loadProfiles()
  } catch (e) {
    uni.showToast({ title: '操作失败', icon: 'none' })
  }
}

function deleteProfile(id) {
  uni.showModal({
    title: '确认删除', content: '确定要删除该命盘存档吗？',
    success: async (r) => {
      if (!r.confirm) return
      try {
        await uni.request({ url: `/api/profiles/${id}`, method: 'DELETE' })
      } catch (_) {}
      profiles.value = profiles.value.filter(p => p.id !== id)
      uni.showToast({ title: '已删除', icon: 'success' })
    }
  })
}

async function saveProfile() {
  var domName = (document.getElementById('profileName')?.value || '').trim()
  if (!domName) { uni.showToast({ title: '请输入姓名', icon: 'none' }); return }
  formData.name = domName
  formData.birthAddr = (document.getElementById('profileBirthAddr')?.value || '').trim()
  const data = {
    name: formData.name,
    gender: ['男', '女'][formData.genderIdx],
    calType: ['公历', '农历'][formData.calTypeIdx],
    birthAddr: formData.birthAddr.trim(),
    isDefault: formData.isDefault ? 1 : 0,
    profileType: formData.profileType || profileTab.value,
  }
  // 出生时间: YYYY-MM-DD → YYYYMMDD0000
  if (formData.birthDate) {
    data.birthTime = formData.birthDate.replace(/-/g, '') + '00'
    data.birthTime = data.birthTime.padEnd(12, '0').slice(0, 12)
  }

  try {
    let res
    if (editingProfile.value) {
      res = await uni.request({ url: `/api/profiles/${editingProfile.value.id}`, method: 'PUT', data })
    } else {
      res = await uni.request({ url: '/api/profiles', method: 'POST', data })
    }
    const d = res.data
    if (d.error) { uni.showToast({ title: d.error, icon: 'none' }); return }
    hideProfileForm()
    loadProfiles()
    uni.showToast({ title: '保存成功', icon: 'success' })
  } catch (e) {
    // 后端失败时本地兜底
    const profile = {
      id: editingProfile.value ? editingProfile.value.id : Date.now(),
      ...data,
      birthTime: data.birthTime || '',
      ganzhi: '',
    }
    if (editingProfile.value) {
      const idx = profiles.value.findIndex(p => p.id === editingProfile.value.id)
      if (idx >= 0) profiles.value[idx] = profile
    } else {
      profiles.value.push(profile)
    }
    hideProfileForm()
    uni.showToast({ title: '保存成功(本地)', icon: 'success' })
  }
}

function clickProfileAvatar() {
  uni.chooseImage({
    count: 1,
    sizeType: ['original', 'compressed'],
    sourceType: ['album', 'camera'],
    success: async (res) => {
      const tempFile = res.tempFilePaths[0]
      // 检查文件大小 (5MB)
      try {
        const fileInfo = await uni.getFileInfo({ filePath: tempFile })
        if (fileInfo.size > 5 * 1024 * 1024) {
          uni.showToast({ title: '图片大小不能超过5MB', icon: 'none' })
          return
        }
      } catch (_) {}
      try {
        var _token = ''
        try { _token = localStorage.getItem('xc_token') || '' } catch(_) {}
        var _headers = { 'X-Requested-With': 'XMLHttpRequest' }
        if (_token) _headers['Authorization'] = 'Bearer ' + _token
        const uploadRes = await uni.uploadFile({
          url: '/api/avatar',
          filePath: tempFile,
          name: 'file',
          header: _headers
        })
        console.log('[avatar] upload status:', uploadRes.statusCode, 'data:', uploadRes.data)
        const d = JSON.parse(uploadRes.data)
        if (d.error) { uni.showToast({ title: d.error, icon: 'none' }); return }
        userInfo.avatar = d.url + (d.url.includes('?') ? '&' : '?') + '_t=' + Date.now()
        uni.setStorageSync('xc_avatar', userInfo.avatar)
        if (typeof window !== 'undefined' && window.__sidebar) {
          try { window.__sidebar.updateAvatar(userInfo.avatar) } catch(_) {}
        }
        uni.showToast({ title: '头像已更新', icon: 'success' })
        setTimeout(function() { location.reload() }, 800)
      } catch (e) {
        console.error('[avatar] upload error:', e)
        uni.showToast({ title: '头像上传失败: ' + (e.message || '未知错误'), icon: 'none' })
      }
    }
  })
}

// 页脚链接
function showFooterInfo(type) {
  const info = {
    contact: '联系方式：support@shian.com\n客服时间：工作日 9:00-18:00',
    privacy: '我们重视您的隐私保护。所有命盘数据仅用于排盘展示，不会向第三方共享。详细隐私政策请访问关于我们页面。'
  }
  uni.showModal({
    title: type === 'contact' ? '联系方式' : '隐私政策',
    content: info[type] || '',
    showCancel: false
  })
}

function goNav(url, type) {
  var showCommunityEntry = import.meta.env.DEV || import.meta.env.VITE_SHOW_COMMUNITY === '1'
  var TAB_LIST = ['/pages/index/index', '/pages/qimen/index', '/pages/bazi-index/index', '/pages/tarot/index', '/pages/liuyao/index', '/pages/meihua/index', '/pages/ziwei/index', '/pages/zeji/index', '/pages/calendar/index'].concat(showCommunityEntry ? ['/pages/community/index'] : [], ['/pages/profile/index'])
  var pathOnly = url.split('?')[0]
  if (type === 'switchTab' || TAB_LIST.indexOf(pathOnly) > -1) {
    if (url.indexOf('?') > -1) {
      var queryStr = url.substring(url.indexOf('?'))
      try { sessionStorage.setItem('_nav_query', queryStr) } catch(_) {}
    }
    uni.switchTab({
      url: pathOnly,
      success: function() {
        if (url.indexOf('?') > -1) {
          var q = url.substring(url.indexOf('?'))
          setTimeout(function() { try { uni.$emit('nav-query', q) } catch(_) {} }, 200)
        }
      }
    })
  } else {
    uni.navigateTo({ url })
  }
}

// 页面加载时从后端获取档案
onMounted(() => {
  window.__xc_hasPassword = hasPassword.value
  window.addEventListener('xc-auth-changed', onProfileAuthChanged)
  // 全局账号设置弹窗操作（解决 tabBar 多实例问题 + 防止弹出层覆盖）
  if (!window._xc_showAccountSettings) {
    window._xc_showAccountSettings = function() {
      // 打开账号设置前先关闭所有登录弹窗，防止 position:fixed overlay 拦截点击
      try { document.querySelectorAll('#topnavLoginModal').forEach(function(el) { el.classList.remove('open') }) } catch(_) {}
      document.querySelectorAll('#accountSettingsModal').forEach(function(el) { el.classList.add('open') })
      // 在可见的弹窗内创建原生input
      var modal = document.querySelector('#accountSettingsModal.open') || document.querySelector('#accountSettingsModal')
      if (modal) {
        var wraps = ['asNewUsername-wrap', 'asNewPass-wrap']
        if (window.__xc_hasPassword) wraps.push('asCurrPassForUser-wrap', 'asOldPass-wrap')
        // 添加绑定相关输入框
        wraps = wraps.concat(['asBindEmail-wrap', 'asBindEmailCode-wrap'])
        wraps.forEach(function(wrapId) {
          if (modal.querySelector('#' + wrapId) && !modal.querySelector('#' + wrapId + ' input')) {
            var wrap = modal.querySelector('#' + wrapId)
            var inp = document.createElement('input')
            if (wrapId.indexOf('Code') > -1) inp.type = 'text'
            else if (wrapId.indexOf('Email') > -1) inp.type = 'email'
            else if (wrapId.indexOf('Phone') > -1) inp.type = 'tel'
            else inp.type = wrapId.indexOf('Pass') > -1 ? 'text' : 'text'
            inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;transition:border-color 0.2s,box-shadow 0.2s'
            if (wrapId.indexOf('Pass') > -1) inp.style.cssText += ';-webkit-text-security:disc;-moz-text-security:disc;text-security:disc;'
            inp.onfocus = function() { this.style.borderColor = 'var(--accent)'; this.style.boxShadow = '0 0 0 2px var(--accent-glow)' }
            inp.onblur = function() { this.style.borderColor = 'var(--input-border)'; this.style.boxShadow = 'none' }
            if (wrapId === 'asNewUsername-wrap') inp.placeholder = '输入新用户名'
            else if (wrapId === 'asCurrPassForUser-wrap') inp.placeholder = '输入当前密码'
            else if (wrapId === 'asOldPass-wrap') inp.placeholder = '输入当前密码'
            else if (wrapId === 'asBindEmail-wrap') inp.placeholder = 'your@email.com'
            else if (wrapId === 'asBindEmailCode-wrap') inp.placeholder = '验证码'
            else inp.placeholder = '至少4个字符'
            wrap.appendChild(inp)
          }
        })
      }
      try { document.querySelectorAll('#asUsernameError').forEach(function(el) { el.textContent = '' }); document.querySelectorAll('#asPassError').forEach(function(el) { el.textContent = '' }); document.querySelectorAll('#asBindEmailError').forEach(function(el) { el.textContent = '' }) } catch(_) {}
      // 加载绑定信息
      loadBindings()
    }
  }
  if (!window._xc_closeAccountSettings) {
    window._xc_closeAccountSettings = function() {
      document.querySelectorAll('#accountSettingsModal').forEach(function(el) { el.classList.remove('open') })
    }
  }
  if (!window._xc_changeUsername) {
    window._xc_changeUsername = async function() {
      var btn = document.getElementById('asUsernameBtn'); var origText = btn ? btn.textContent : ''
      if (btn) { origText = btn.textContent; btn.textContent = '修改中...'; btn.style.opacity = '0.6'; btn.style.pointerEvents = 'none' }
      try {
        document.querySelectorAll('#asUsernameError').forEach(function(el) { el.textContent = '' })
        var u = document.querySelector('#asNewUsername-wrap input')
        var p = document.querySelector('#asCurrPassForUser-wrap input')
        var newUsername = u ? u.value.trim() : ''; var currPass = p ? p.value : ''
        if (!newUsername || newUsername.length < 2) { if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; uni.showToast({ title: '用户名至少2个字符', icon: 'none' }); return }
        if (window.__xc_hasPassword && !currPass) { if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; uni.showToast({ title: '请输入当前密码', icon: 'none' }); return }
        var data = { new_username: newUsername }
        if (window.__xc_hasPassword) data.current_password = currPass
        var res = await uni.request({ url: '/api/user/change-username', method: 'POST', data: data })
        var d = res.data
        if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }
        if (d.error) { uni.showToast({ title: d.error, icon: 'none' }); return }
        uni.setStorageSync('xc_user', newUsername); uni.showToast({ title: '用户名已更新', icon: 'success' })
        setTimeout(function() { location.reload() }, 800)
      } catch (e) { if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; uni.showToast({ title: '网络错误', icon: 'none' }) }
    }
  }
  // 加载账号绑定信息
  async function loadBindings() {
    try {
      var res = await uni.request({ url: '/api/user/bindings', method: 'GET' })
      var d = res.data
      if (d && !d.error) {
        try {
          document.getElementById('bindUsername').textContent = d.username || '—'
          document.getElementById('bindEmail').textContent = d.email || '未绑定'
          document.getElementById('bindPassword').textContent = d.has_password ? '已设置' : '未设置'
          document.getElementById('bindGitee').textContent = d.oauth_gitee ? '已绑定' : '未绑定'
          window.__xc_emailBound = !!d.email
          var emailSubmit = document.getElementById('asBindEmailSubmit')
          if (emailSubmit) emailSubmit.textContent = d.email ? '换绑邮箱' : '绑定邮箱'
          var giteeItem = oauthProviders.find(function(p) { return p.key === 'gitee' })
          if (giteeItem) giteeItem.bound = !!d.oauth_gitee
          // 显示解绑按钮
          var eu = document.getElementById('bindEmailUnbind')
          if (eu) eu.style.display = d.email ? 'inline' : 'none'
        } catch(_) {}
      }
    } catch(_) {}
  }
  if (!window._xc_loadBindings) { window._xc_loadBindings = loadBindings }

  // 通用验证码发送（账号设置中绑定邮箱使用）
  function _profileSendCode(config) {
    return async function() {
      var btn = document.getElementById(config.btnId)
      if (btn && btn.getAttribute('data-counting') === '1') return
      var input = document.querySelector('#' + config.wrapId + '-wrap input')
      var val = input ? input.value.trim() : ''
      if (!val || !config.validate(val)) { uni.showToast({ title: config.errMsg, icon: 'none' }); return }
      try {
        var res = await uni.request({ url: config.url, method: 'POST', data: (config.buildData || function(v) { return {[config.key]: v} })(val) })
        if (res.data && res.data.error) { uni.showToast({ title: res.data.error, icon: 'none' }); return }
        uni.showToast({ title: '验证码已发送', icon: 'success' })
        if (btn) {
          btn.setAttribute('data-counting', '1')
          var count = 60; btn.textContent = count + 's'
          var timer = setInterval(function() { count--; if (count <= 0) { clearInterval(timer); btn.textContent = '获取验证码'; btn.removeAttribute('data-counting') } else { btn.textContent = count + 's' } }, 1000)
        }
      } catch(e) { uni.showToast({ title: '发送失败', icon: 'none' }) }
    }
  }
  if (!window._xc_sendBindEmailCode) {
    window._xc_sendBindEmailCode = _profileSendCode({ btnId:'asBindEmailBtn', wrapId:'asBindEmail', key:'email', url:'/api/email/send', errMsg:'请输入正确的邮箱', validate:function(v){return v.indexOf('@')!==-1} })
  }
  // 通用绑定（邮箱使用）
  function _profileBind(config) {
    return async function() {
      var valInput = document.querySelector('#' + config.wrapId + '-wrap input')
      var codeInput = document.querySelector('#' + config.codeWrapId + '-wrap input')
      var val = valInput ? valInput.value.trim() : ''
      var code = codeInput ? codeInput.value.trim() : ''
      if (!val || !code) { uni.showToast({ title: '请填写完整', icon: 'none' }); return }
      var btn = document.getElementById(config.btnId)
      if (btn) { btn.textContent = '绑定中...'; btn.style.opacity = '0.6'; btn.style.pointerEvents = 'none' }
      var resetBtn = function() { if (btn) { btn.textContent = window.__xc_emailBound ? '换绑邮箱' : config.label; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' } }
      try {
        var data = {}; data[config.key] = val; data.code = code
        var res = await uni.request({ url: config.url, method: 'POST', data: data })
        var d = res.data
        if (d && d.error) { uni.showToast({ title: d.error, icon: 'none' }); resetBtn(); return }
        uni.showToast({ title: config.successMsg, icon: 'success' })
        loadBindings()
        if (valInput) valInput.value = ''
        if (codeInput) codeInput.value = ''
        resetBtn()
        setTimeout(function() { location.reload() }, 800)
      } catch(e) { uni.showToast({ title: '绑定失败', icon: 'none' }); resetBtn() }
    }
  }
  // 通用解绑（邮箱使用）
  function _profileUnbind(config) {
    return async function() {
      uni.showModal({
        title: '确认解绑', content: config.confirmMsg,
        success: async function(r) {
          if (!r.confirm) return
          try {
            var res = await uni.request({ url: config.url, method: 'POST' })
            if (res.data && res.data.error) { uni.showToast({ title: res.data.error, icon: 'none' }); return }
            uni.showToast({ title: '已解绑', icon: 'success' }); loadBindings()
          } catch(e) { uni.showToast({ title: '解绑失败', icon: 'none' }) }
        }
      })
    }
  }
  if (!window._xc_bindEmail) {
    window._xc_bindEmail = _profileBind({ wrapId:'asBindEmail', codeWrapId:'asBindEmailCode', btnId:'asBindEmailSubmit', key:'email', url:'/api/bind/email', label:'绑定邮箱', successMsg:'邮箱绑定成功' })
  }
  if (!window._xc_unbindEmail) {
    window._xc_unbindEmail = _profileUnbind({ confirmMsg:'确定要解绑邮箱吗？', url:'/api/unbind/email' })
  }

  if (!window._xc_changePassword) {
    window._xc_changePassword = async function() {
      var btn = document.getElementById('asPasswordBtn'); var origText = btn ? btn.textContent : ''
      if (btn) { origText = btn.textContent; btn.textContent = '设置中...'; btn.style.opacity = '0.6'; btn.style.pointerEvents = 'none' }
      try {
        document.querySelectorAll('#asPassError').forEach(function(el) { el.textContent = '' })
        var oldEl = document.querySelector('#asOldPass-wrap input')
        var newEl = document.querySelector('#asNewPass-wrap input')
        var oldPass = oldEl ? oldEl.value : ''; var newPass = newEl ? newEl.value : ''
        if (window.__xc_hasPassword && !oldPass) { if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; uni.showToast({ title: '请输入当前密码', icon: 'none' }); return }
        if (!newPass || newPass.length < 4) { if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; uni.showToast({ title: '新密码至少4个字符', icon: 'none' }); return }
        var data = { new_password: newPass }
        if (window.__xc_hasPassword) data.old_password = oldPass
        var res = await uni.request({ url: '/api/user/change-password', method: 'POST', data: data })
        var d = res.data
        if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }
        if (d.error) { uni.showToast({ title: d.error, icon: 'none' }); return }
        window.__xc_hasPassword = true; uni.setStorageSync('xc_has_password', '1')
        uni.showToast({ title: '密码已设置', icon: 'success' })
        setTimeout(function() { location.reload() }, 800)
      } catch (e) { if (btn) { btn.textContent = origText; btn.style.opacity = '1'; btn.style.pointerEvents = 'auto' }; uni.showToast({ title: '网络错误', icon: 'none' }) }
    }
  }
  // 创建原生DOM输入框
  function createNativeInput(wrapId, type, placeholder) {
    var wrap = document.getElementById(wrapId)
    if (!wrap) return null
    var inp = document.createElement('input')
    inp.type = type
    inp.id = wrapId.replace('-wrap', '')
    if (placeholder) inp.placeholder = placeholder
    inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;transition:border-color 0.2s,box-shadow 0.2s'
    inp.onfocus = function() { this.style.borderColor = 'var(--accent)'; this.style.boxShadow = '0 0 0 2px var(--accent-glow)' }
    inp.onblur = function() { this.style.borderColor = 'var(--input-border)'; this.style.boxShadow = 'none' }
    if (type === 'text') inp.setAttribute('maxlength', '100')
    wrap.appendChild(inp)
    return inp
  }
  createNativeInput('profileSearch', 'text', '按姓名搜索...')
  createNativeInput('profileName', 'text', '姓名')
  createNativeInput('profileBirthAddr', 'text', '如：北京')

  if (isLoggedIn.value) refreshProfileSessionState()

  // OAuth 回调处理
  try {
    var params = new URLSearchParams(window.location.hash.split('?')[1] || window.location.search)
    var oauthSuccess = params.get('oauth_success')
    var oauthError = params.get('oauth_error')
    if (oauthSuccess) {
      isLoggedIn.value = true
      uni.setStorageSync('xc_token', 'session')
      uni.showToast({ title: oauthSuccess === 'qq' ? 'QQ登录成功' : oauthSuccess === 'gitee' ? 'Gitee绑定成功' : oauthSuccess === 'wechat' ? '微信登录成功' : '登录成功', icon: 'success' })
      loadProfiles()
      loadBindings()
      // 清除 URL 参数
      window.history.replaceState({}, '', window.location.pathname + window.location.hash.split('?')[0])
    }
    if (oauthError) {
      uni.showToast({ title: decodeURIComponent(oauthError), icon: 'none' })
      window.history.replaceState({}, '', window.location.pathname + window.location.hash.split('?')[0])
    }
  } catch(_) {}

  // 验证真实登录状态（后端 session 可能已过期）
  refreshProfileSessionState()
})

onShow(function() {
  questionGuidanceEnabled.value = readQuestionGuidanceEnabled()
  refreshProfileSessionState()
})

onBeforeUnmount(function() {
  window.removeEventListener('xc-auth-changed', onProfileAuthChanged)
})
</script>

<style scoped>
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }

.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }

@media (min-width: 769px) {
  :deep(.topnav) { padding-left: 16px; padding-right: 16px; }
  :deep(.nav-btn) { padding-left: 8px; padding-right: 8px; font-size: 0.9rem; }
  :deep(.topnav-sidebar-btn) { margin-right: 0; }
}

.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.tool-hero { padding: 60px 32px 32px; text-align: center; position: relative; overflow: hidden; }
.tool-hero::before { content: ''; position: absolute; top: -50%; left: -20%; width: 140%; height: 200%; background: radial-gradient(ellipse at center, var(--accent-glow) 0%, transparent 70%); opacity: 0.5; pointer-events: none; }
.tool-hero-content { position: relative; z-index: 1; max-width: var(--max-w); margin: 0 auto; }
.tool-hero-title { font-family: var(--font-serif); font-size: 2rem; font-weight: 400; letter-spacing: 4px; color: var(--text-1); margin-bottom: 12px; }
.tool-hero-desc { font-size: 0.9375rem; color: var(--text-3); letter-spacing: 2px; }

.tool-container { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; backdrop-filter: blur(20px); box-shadow: var(--card-shadow); max-width: 560px; margin: 0 auto; }

/* ═══ 头像卡片 ═══ */
.profile-card { display: flex; align-items: center; gap: 16px; padding: 18px 4px 22px 16px; margin-bottom: 24px; border-bottom: 1px solid var(--card-border); box-sizing: border-box; }
.profile-card-avatar { position: relative; width: 72px; height: 72px; border-radius: 50%; background: rgba(255,255,255,0.06); overflow: hidden; display: flex; align-items: center; justify-content: center; cursor: pointer; flex-shrink: 0; border: 2px solid var(--card-border); transition: border-color 0.2s, transform 0.2s; box-sizing: border-box; }
.profile-card-avatar:active { transform: scale(1.05); }
.profile-card-avatar:hover { border-color: var(--accent); }
.profile-card-avatar-img { display: block; width: 100%; height: 100%; border-radius: 50%; object-fit: cover; object-position: center; }
.profile-card-avatar-text { font-size: 1.8rem; font-weight: 600; color: var(--text-3); }
.profile-card-avatar-badge { position: absolute; bottom: 0; right: 0; width: 22px; height: 22px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.55rem; }
.profile-card-info { flex: 1; min-width: 0; }
.profile-card-name { display: block; font-size: 1.15rem; font-weight: 600; color: var(--text-1); margin-bottom: 4px; }
.profile-card-meta { display: block; font-size: 0.75rem; color: var(--text-3); letter-spacing: 0.5px; }

/* ═══ 设置分组（iOS风格） ═══ */
.settings-group { margin-bottom: 28px; }
.settings-group-title { font-size: 0.72rem; font-weight: 500; color: var(--text-3); letter-spacing: 2px; text-transform: uppercase; margin-bottom: 10px; padding-left: 4px; }
.settings-list { background: rgba(255,255,255,0.03); border: 1px solid var(--card-border); border-radius: 14px; overflow: hidden; }
.settings-item { display: flex; align-items: center; padding: 14px 16px; cursor: pointer; transition: background 0.15s; border-bottom: 1px solid var(--card-border); gap: 12px; }
.settings-item:last-child { border-bottom: none; }
.settings-item:hover { background: var(--accent-glow); }
.settings-item:active { background: rgba(255,255,255,0.06); }
.settings-item-icon {
  flex-shrink: 0; width: 28px; height: 28px;
  display: inline-flex; align-items: center; justify-content: center;
  border-radius: 9px; border: 1px solid rgba(178,149,93,0.16);
  background: var(--accent-glow); color: var(--accent);
  font-size: 0.66rem; line-height: 1; font-weight: 700; letter-spacing: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'PingFang SC', sans-serif;
  box-sizing: border-box;
}
.settings-icon-phone { font-size: 0.54rem; }
.settings-icon-oauth { font-size: 0.82rem; }
.settings-icon-danger { background: rgba(215,109,95,0.12); border-color: rgba(215,109,95,0.26); color: #d76d5f; font-size: 0.72rem; }
.settings-item-label { flex: 1; font-size: 0.875rem; color: var(--text-1); }
.settings-item-main { flex: 1; display: grid; gap: 4px; min-width: 0; }
.settings-item-main .settings-item-label { flex: none; }
.settings-item-desc { color: var(--text-3); font-size: 0.72rem; line-height: 1.5; }
.settings-item-value { font-size: 0.78rem; color: var(--text-3); max-width: 120px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.settings-item-arrow { font-size: 0.85rem; color: var(--text-3); flex-shrink: 0; margin-left: 4px; transition: transform 0.2s; }
.guidance-setting-item { align-items: flex-start; }
.settings-switch { width: 42px; height: 24px; border-radius: 999px; padding: 2px; background: rgba(255,255,255,0.12); border: 1px solid var(--card-border); box-sizing: border-box; flex-shrink: 0; transition: background .18s ease, border-color .18s ease; }
.settings-switch text { display: block; width: 18px; height: 18px; border-radius: 50%; background: var(--text-3); transition: transform .18s ease, background .18s ease; }
.settings-switch.active { background: var(--accent-glow); border-color: rgba(178,149,93,0.45); }
.settings-switch.active text { transform: translateX(18px); background: var(--accent); }
.danger-group .settings-list { border-color: rgba(215,109,95,0.26); background: rgba(215,109,95,0.045); }
.danger-group .settings-item:hover { background: rgba(215,109,95,0.08); }
.delete-account-warning { display: block; margin-bottom: 12px; color: #d76d5f; font-size: 0.78rem; line-height: 1.65; }
.btn-danger { background: rgba(215,109,95,0.14); border: 1px solid rgba(215,109,95,0.38); color: #ffb5aa; }
.btn-danger:hover { background: rgba(215,109,95,0.22); border-color: rgba(215,109,95,0.58); }

/* ═══ Accordion 展开区 ═══ */
.settings-accordion { border-top: 1px solid var(--card-border); background: rgba(0,0,0,0.08); }
.settings-accordion-inner { padding: 14px 16px; }
.settings-accordion-inner::after { content: ''; display: table; clear: both; }
.settings-accordion-inner .field { margin-bottom: 10px; }
.settings-accordion-inner .btn-block { margin-top: 6px; }

.settings-oauth-row { display: flex; align-items: center; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid var(--card-border); }
.settings-oauth-row:last-child { border-bottom: none; }
.settings-oauth-left { display: flex; align-items: center; gap: 10px; }
.settings-oauth-icon {
  width: 24px; height: 24px; border-radius: 8px;
  display: inline-flex; align-items: center; justify-content: center;
  border: 1px solid rgba(178,149,93,0.18);
  background: var(--accent-glow); color: var(--accent);
  font-size: 0.7rem; font-weight: 800;
}
.settings-oauth-label { font-size: 0.85rem; color: var(--text-2); }
.settings-oauth-right { display: flex; align-items: center; gap: 8px; }
.settings-oauth-status { font-size: 0.78rem; color: var(--text-3); }

/* ═══ 退出登录 ═══ */
.settings-logout { margin-top: 24px; text-align: center; padding: 14px; border-radius: 12px; cursor: pointer; border: 1px solid var(--danger); transition: background 0.2s; }
.settings-logout:hover { background: rgba(215,125,110,0.08); }
.settings-logout:active { background: rgba(215,125,110,0.15); }
.settings-logout-text { color: var(--danger); font-size: 0.9rem; font-weight: 500; letter-spacing: 1px; }

/* ═══ 通用 ═══ */
.profile-empty { text-align: center; padding: 48px 20px; color: var(--text-3); }
.profile-empty-icon { font-size: 3rem; margin-bottom: 12px; }
.profile-empty-text { font-size: 0.9375rem; color: var(--text-2); display: block; margin-bottom: 4px; }

.field { margin-bottom: 10px; }
.modal-error { color: var(--danger); font-size: 0.75rem; min-height: 18px; margin: 4px 0 8px; line-height: 1.4; }

.modal-overlay { position: fixed; inset: 0; z-index: 999; background: rgba(0,0,0,0.55); display: none; align-items: center; justify-content: center; backdrop-filter: blur(4px); padding: 16px; box-sizing: border-box; }
.modal-overlay.open { display: flex; }
#accountSettingsModal .modal-box { position: relative; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 20px; padding: 32px 28px 24px; max-width: 420px; width: 100%; box-shadow: 0 12px 48px rgba(0,0,0,0.25); }
#accountSettingsModal .modal-title { font-family: var(--font-serif); font-size: 1.15rem; text-align: center; color: var(--text-1); margin-bottom: 24px; letter-spacing: 1px; }
#accountSettingsModal .modal-close { position: absolute; top: 12px; right: 16px; width: 28px; height: 28px; display: flex; align-items: center; justify-content: center; border-radius: 50%; font-size: 0.85rem; color: var(--text-3); cursor: pointer; }
#accountSettingsModal .modal-close:hover { background: var(--accent-glow); color: var(--accent); }

@media (max-width: 768px) {
  .section { padding: 48px 16px; }
  .tool-container { padding: 20px; }
  .profile-card { gap: 14px; padding: 14px 2px 18px 12px; }
  .profile-card-avatar { width: 60px; height: 60px; }
}
</style>
