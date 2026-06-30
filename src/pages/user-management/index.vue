<template>
  <view class="page-root user-management-page" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="user-page-wrap">
      <section class="user-hero">
        <view class="user-hero-main">
          <view class="section-tag">档案列表</view>
          <view class="user-hero-title">档案信息</view>
          <view class="user-hero-desc">统一管理八字、紫微和时安agent共用的出生资料</view>
        </view>
        <view class="user-hero-actions" v-if="isLoggedIn">
          <view class="user-primary-btn" @tap="openCreateForm">＋ 新增用户</view>
        </view>
      </section>

      <section v-if="!isLoggedIn" class="user-login-panel">
        <view class="login-mark">锁</view>
        <view class="login-title">登录后管理档案信息</view>
        <view class="login-desc">档案会同步到八字排盘、紫微斗数和时安agent。</view>
        <view
          class="user-primary-btn"
          role="button"
          tabindex="0"
          data-login-trigger="1"
          @click="openLogin"
          @tap="openLogin"
          onclick="window._openLoginModal && window._openLoginModal()"
        >立即登录</view>
      </section>

      <section v-else class="user-workspace">
        <view class="stats-strip">
          <view class="stat-cell">
            <text class="stat-num">{{ profiles.length }}</text>
            <text class="stat-label">全部档案</text>
          </view>
          <view class="stat-cell">
            <text class="stat-num">{{ baziCount }}</text>
            <text class="stat-label">八字来源</text>
          </view>
          <view class="stat-cell">
            <text class="stat-num">{{ ziweiCount }}</text>
            <text class="stat-label">紫微来源</text>
          </view>
          <view class="stat-cell">
            <text class="stat-num">{{ recentLabel }}</text>
            <text class="stat-label">最近使用</text>
          </view>
        </view>

        <view class="mobile-sync-note" v-if="!mobileTipClosed">
          <view class="mobile-sync-mark">声</view>
          <text>档案可同步用于八字、紫微和时安agent</text>
          <view class="mobile-sync-close" @tap="closeMobileTip">×</view>
        </view>

        <view class="control-band">
          <view class="search-wrap" @tap.stop="focusSearch" @click.stop="focusSearch">
            <view class="profile-search-icon" aria-hidden="true"></view>
            <input
              ref="searchInputRef"
              class="search-input"
              :value="searchText"
              placeholder="搜索姓名、出生地、来源"
              confirm-type="search"
              @input="onSearchInput"
              @confirm="onSearchInput"
              @tap.stop
              @click.stop
            />
          </view>
          <view class="filter-tabs">
            <view v-for="item in sourceTabs" :key="item.key" class="filter-tab" :class="{ active: activeSource === item.key }" @tap="activeSource = item.key">{{ item.label }}</view>
          </view>
          <picker class="sort-picker" :range="sortLabels" :value="sortIdx" @change="sortIdx = Number($event.detail.value || 0)">
            <view class="sort-trigger">{{ sortLabels[sortIdx] }} ▾</view>
          </picker>
        </view>

        <view class="profile-list" v-if="filteredProfiles.length">
          <view class="archive-card" v-for="profile in filteredProfiles" :key="profile.id" :class="{ default: profile.isDefault, 'mobile-actions-open': activeMobileActionsId === profile.id }">
            <view class="archive-mark" :class="'source-' + sourceKey(profile)">{{ avatarText(profile) }}</view>
            <view class="archive-main">
              <view class="archive-head">
                <view class="archive-title-row">
                  <text class="archive-name">{{ profile.name || '未命名' }}</text>
                  <text class="archive-gender">{{ profile.gender || '男' }}</text>
                  <text v-if="profile.isDefault" class="default-badge">默认</text>
                </view>
                <view class="source-pill">{{ sourceLabel(profile) }}</view>
                <view class="mobile-card-tools">
                  <view class="mobile-star" :class="{ active: profile.isDefault }" @tap.stop="profile.isDefault ? null : setDefault(profile)">{{ profile.isDefault ? '★' : '☆' }}</view>
                  <view class="mobile-edit" @tap.stop="openEditForm(profile)">✎</view>
                  <view class="mobile-more" @tap.stop="toggleMobileActions(profile)">⋯</view>
                </view>
              </view>
              <view class="mobile-tag-row">
                <text class="mobile-relation-tag">{{ relationLabel(profile) }}</text>
                <text class="mobile-gender-tag" :class="{ female: profile.gender === '女' }">{{ profile.gender || '男' }}</text>
                <text class="mobile-date-tag">{{ mobileBirthDate(profile) }}</text>
              </view>
              <view class="archive-meta">
                <text class="birth-line">{{ compactBirthLine(profile) }}</text>
                <text class="archive-address">{{ shortAddr(profile) }}</text>
              </view>
              <view class="archive-submeta">
                <text>最近使用 {{ formatDate(profile.lastUsedAt || profile.createdAt) }}</text>
                <text v-if="profile.meta && profile.meta.longitude">经度 {{ profile.meta.longitude }}</text>
                <text v-else-if="profile.meta && profile.meta.birthLng">经度 {{ profile.meta.birthLng }}</text>
              </view>
            </view>
            <view class="archive-actions">
              <view class="action-row primary-actions">
                <view class="action-btn primary" @tap="openBazi(profile)">看八字</view>
                <view class="action-btn primary" @tap="openZiwei(profile)">看紫微</view>
                <view class="action-btn accent" @tap="openAgent(profile)">用此命盘问</view>
              </view>
              <view class="action-row secondary-actions">
                <view class="action-btn ghost" @tap="openEditForm(profile)">编辑</view>
                <view class="action-btn ghost" v-if="!profile.isDefault" @tap="setDefault(profile)">默认</view>
                <view class="action-btn danger" @tap="deleteProfile(profile)">删除</view>
              </view>
            </view>
          </view>
        </view>

        <view class="empty-state" v-else>
          <view class="empty-title">暂无匹配档案</view>
          <view class="empty-desc">可以新增用户，或在八字/紫微排盘时开启保存。</view>
          <view class="user-primary-btn" @tap="openCreateForm">＋ 新增用户</view>
        </view>
      </section>
    </view>

    <view class="profile-modal" v-if="formOpen">
      <view class="profile-modal-mask" @tap="closeForm"></view>
      <view class="profile-modal-panel">
        <view class="modal-head">
          <view>
            <view class="modal-title">{{ editingId ? '编辑档案' : '新增用户' }}</view>
            <view class="modal-desc">出生资料会同步到排盘和时安agent</view>
          </view>
          <view class="modal-close" @tap="closeForm">×</view>
        </view>
        <view class="form-grid">
          <view class="form-field">
            <text class="field-label">姓名</text>
            <input class="field-input" v-model="form.name" placeholder="例如：张三" />
          </view>
          <view class="form-field">
            <text class="field-label">性别</text>
            <picker :range="['男', '女']" :value="form.gender === '女' ? 1 : 0" @change="form.gender = Number($event.detail.value) === 1 ? '女' : '男'">
              <view class="field-picker">{{ form.gender }}</view>
            </picker>
          </view>
          <view class="form-field">
            <text class="field-label">历法</text>
            <picker :range="['公历', '农历']" :value="form.calType === '农历' ? 1 : 0" @change="form.calType = Number($event.detail.value) === 1 ? '农历' : '公历'">
              <view class="field-picker">{{ form.calType }}</view>
            </picker>
          </view>
          <view class="form-field">
            <text class="field-label">出生日期</text>
            <picker mode="date" :value="form.birthDate" @change="form.birthDate = $event.detail.value">
              <view class="field-picker">{{ form.birthDate || '选择日期' }}</view>
            </picker>
          </view>
          <view class="form-field">
            <text class="field-label">出生时间</text>
            <picker mode="time" :value="form.birthClock" @change="form.birthClock = $event.detail.value">
              <view class="field-picker">{{ form.birthClock || '选择时间' }}</view>
            </picker>
          </view>
          <view class="form-field">
            <text class="field-label">档案类型</text>
            <picker :range="profileTypeLabels" :value="profileTypeIndex" @change="setProfileType">
              <view class="field-picker">{{ profileTypeName(form.profileType) }}</view>
            </picker>
          </view>
          <view class="form-field wide">
            <text class="field-label">出生地</text>
            <input class="field-input" v-model="form.birthAddr" placeholder="例如：广东 深圳 南山" />
          </view>
          <view class="form-field switch-field">
            <text class="field-label">默认档案</text>
            <view class="mini-switch" :class="{ active: form.isDefault }" @tap="form.isDefault = !form.isDefault">
              <view class="mini-switch-dot"></view>
            </view>
          </view>
        </view>
        <view class="modal-error" v-if="formError">{{ formError }}</view>
        <view class="modal-actions">
          <view class="modal-btn secondary" @tap="closeForm">取消</view>
          <view class="modal-btn primary" @tap="submitForm">保存</view>
        </view>
      </view>
    </view>

    <view class="profile-modal delete-confirm-modal" v-if="deleteConfirmOpen">
      <view class="profile-modal-mask delete-confirm-mask" @tap="closeDeleteConfirm"></view>
      <view class="delete-confirm-panel" @tap.stop>
        <view class="delete-confirm-head">
          <view class="delete-confirm-mark">!</view>
          <view class="delete-confirm-copy">
            <view class="delete-confirm-title">删除档案</view>
            <view class="delete-confirm-desc">确定删除「{{ deleteConfirmName }}」吗？</view>
          </view>
          <view class="delete-confirm-close" @tap="closeDeleteConfirm">×</view>
        </view>
        <view class="delete-confirm-body">
          <view class="delete-confirm-row">
            <text>档案</text>
            <text>{{ deleteConfirmName }}</text>
          </view>
          <view class="delete-confirm-row">
            <text>来源</text>
            <text>{{ deleteConfirmSource }}</text>
          </view>
          <view class="delete-confirm-note">删除后此档案不会再出现在八字、紫微和时安 agent 中。</view>
          <view class="delete-confirm-subnote">相关历史记录不会自动删除。</view>
        </view>
        <view class="delete-confirm-actions">
          <view class="delete-confirm-btn secondary" @tap="closeDeleteConfirm">取消</view>
          <view class="delete-confirm-btn danger" :class="{ loading: deleteDeleting }" @tap="confirmDeleteProfile">{{ deleteDeleting ? '删除中...' : '删除' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
const profiles = ref([])
const searchText = ref('')
const searchInputRef = ref(null)
const activeSource = ref('all')
const sortIdx = ref(0)
const formOpen = ref(false)
const editingId = ref(null)
const editingSource = ref('manual')
const editingMeta = ref({})
const formError = ref('')
const profilesLoadedAt = ref(0)
const mobileTipClosed = ref(!!uni.getStorageSync('xc_profile_mobile_tip_closed'))
const activeMobileActionsId = ref(null)
const deleteConfirmOpen = ref(false)
const deleteConfirmProfile = ref(null)
const deleteDeleting = ref(false)
let profilesLoadingPromise = null

const sourceTabs = [
  { key: 'all', label: '全部' },
  { key: 'bazi', label: '八字' },
  { key: 'ziwei', label: '紫微' },
  { key: 'manual', label: '手动' },
  { key: 'customer', label: '客户' },
]
const sortLabels = ['最近使用', '默认优先', '姓名排序']
const profileTypeLabels = ['自己', '家人', '朋友', '伴侣', '客户', '名人', '收藏', '其他']
const profileTypeValues = ['self', 'family', 'friend', 'partner', 'customer', 'celebrity', 'collect', 'other']

const form = reactive({
  name: '',
  gender: '男',
  calType: '公历',
  birthDate: '',
  birthClock: '12:00',
  birthAddr: '',
  profileType: 'self',
  isDefault: false,
})

const baziCount = computed(() => profiles.value.filter(p => sourceKey(p) === 'bazi').length)
const ziweiCount = computed(() => profiles.value.filter(p => sourceKey(p) === 'ziwei').length)
const recentLabel = computed(() => {
  if (!profiles.value.length) return '无'
  const p = profiles.value[0]
  return p && p.name ? p.name.slice(0, 4) : '未命名'
})
const deleteConfirmName = computed(() => (deleteConfirmProfile.value && deleteConfirmProfile.value.name) || '未命名')
const deleteConfirmSource = computed(() => deleteConfirmProfile.value ? sourceLabel(deleteConfirmProfile.value) : '手动档案')
const profileTypeIndex = computed(() => Math.max(0, profileTypeValues.indexOf(form.profileType)))

const filteredProfiles = computed(() => {
  const q = searchText.value.trim().toLowerCase()
  let list = profiles.value.slice()
  if (activeSource.value !== 'all') {
    list = list.filter(p => {
      if (activeSource.value === 'customer') return (p.profileType || 'self') === 'customer'
      return sourceKey(p) === activeSource.value
    })
  }
  if (q) {
    list = list.filter(p => {
      const text = [p.name, p.gender, p.birthTime, p.birthAddr, p.calType, sourceLabel(p)].join(' ').toLowerCase()
      return text.indexOf(q) > -1
    })
  }
  if (sortIdx.value === 1) {
    list.sort((a, b) => Number(!!b.isDefault) - Number(!!a.isDefault) || dateValue(b.createdAt) - dateValue(a.createdAt))
  } else if (sortIdx.value === 2) {
    list.sort((a, b) => String(a.name || '').localeCompare(String(b.name || ''), 'zh-Hans-CN'))
  } else {
    list.sort((a, b) => dateValue(b.lastUsedAt || b.createdAt) - dateValue(a.lastUsedAt || a.createdAt))
  }
  return list
})

function onSearchInput(e) {
  const detailValue = e && e.detail ? e.detail.value : undefined
  const targetValue = e && e.target ? e.target.value : undefined
  searchText.value = String(detailValue !== undefined ? detailValue : (targetValue !== undefined ? targetValue : ''))
}

function closeMobileTip() {
  mobileTipClosed.value = true
  try { uni.setStorageSync('xc_profile_mobile_tip_closed', '1') } catch (_) {}
}

function toggleMobileActions(profile) {
  const id = profile && profile.id
  activeMobileActionsId.value = activeMobileActionsId.value === id ? null : id
}

function focusSearch() {
  try {
    const input = searchInputRef.value
    if (input && input.focus) input.focus()
  } catch (_) {}
  try {
    setTimeout(function() {
      const el = document.querySelector('.user-management-page .search-input input, .user-management-page input.search-input, .user-management-page .search-input')
      if (el && el.focus) el.focus()
    }, 0)
  } catch (_) {}
}

function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  uni.setStorageSync('xc_theme', theme.value)
  try {
    document.documentElement.setAttribute('data-theme', theme.value)
    document.body.setAttribute('data-theme', theme.value)
  } catch (_) {}
}

function openLogin() {
  try { if (window._openLoginModal) window._openLoginModal() } catch (_) {}
}

function dateValue(v) {
  const t = Date.parse(v || '')
  return isNaN(t) ? 0 : t
}

function sourceKey(p) {
  const source = p.source || ''
  if (source === 'bazi_record') return 'bazi'
  if (source === 'ziwei_pan') return 'ziwei'
  return 'manual'
}

function sourceLabel(p) {
  const key = sourceKey(p)
  if (key === 'bazi') return '八字保存'
  if (key === 'ziwei') return '紫微保存'
  return (p.profileType || 'self') === 'customer' ? '客户档案' : '手动档案'
}

function sourceShort(p) {
  const key = sourceKey(p)
  if (key === 'bazi') return '八'
  if (key === 'ziwei') return '紫'
  return '档'
}

function avatarText(profile) {
  const name = String((profile && profile.name) || '').trim()
  if (name) return name.slice(0, 2)
  return sourceShort(profile || {})
}

function profileTypeName(type) {
  if (type === 'self') return '自己'
  if (type === 'family') return '家人'
  if (type === 'friend') return '朋友'
  if (type === 'partner') return '伴侣'
  if (type === 'customer') return '客户'
  if (type === 'celebrity') return '名人'
  if (type === 'collect') return '收藏'
  if (type === 'other') return '其他'
  return '档案'
}

function relationLabel(profile) {
  const type = (profile && profile.profileType) || 'self'
  if (type === 'customer') return '客户'
  if (type === 'collect') return '案例'
  if (type === 'family') return '家人'
  if (type === 'friend') return '朋友'
  if (type === 'partner') return '伴侣'
  if (type === 'celebrity') return '名人'
  if (type === 'other') return '其他'
  if (sourceKey(profile || {}) === 'bazi') return '八字'
  if (sourceKey(profile || {}) === 'ziwei') return '紫微'
  return '自己'
}

function setProfileType(e) {
  const idx = Number(e.detail.value || 0)
  form.profileType = profileTypeValues[idx] || 'self'
}

function formatBirthTime(v) {
  const s = String(v || '')
  if (s.length >= 12) return s.slice(0, 4) + '-' + s.slice(4, 6) + '-' + s.slice(6, 8) + ' ' + s.slice(8, 10) + ':' + s.slice(10, 12)
  if (s.length >= 8) return s.slice(0, 4) + '-' + s.slice(4, 6) + '-' + s.slice(6, 8)
  return '未填写出生时间'
}

function compactBirthLine(profile) {
  return `${profile.calType || '公历'} ${formatBirthTime(profile.birthTime)}`
}

function mobileBirthDate(profile) {
  const s = String((profile && profile.birthTime) || '')
  if (s.length >= 8) return s.slice(0, 4) + '.' + Number(s.slice(4, 6)) + '.' + Number(s.slice(6, 8))
  return '未填生日'
}

function shortAddr(profile) {
  const value = String(profile.birthAddr || '').trim()
  return value || '未填写出生地'
}

function formatDate(v) {
  if (!v) return '暂无'
  const d = new Date(v)
  if (isNaN(d.getTime())) return '暂无'
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function birthParts(birthTime) {
  const s = String(birthTime || '').padEnd(12, '0')
  if (s.length < 8) return { date: '', time: '12:00' }
  return {
    date: s.slice(0, 4) + '-' + s.slice(4, 6) + '-' + s.slice(6, 8),
    time: s.slice(8, 10) + ':' + s.slice(10, 12),
  }
}

function formBirthTime() {
  if (!form.birthDate) return ''
  return form.birthDate.replace(/-/g, '') + String(form.birthClock || '00:00').replace(':', '').padEnd(4, '0').slice(0, 4)
}

async function loadProfiles(force) {
  if (!isLoggedIn.value) return
  const now = Date.now()
  if (!force && profilesLoadingPromise) return profilesLoadingPromise
  if (!force && profiles.value.length && now - profilesLoadedAt.value < 30000) return
  profilesLoadingPromise = (async function() {
  try {
    const res = await uni.request({ url: '/api/profiles?sort=last_used', method: 'GET' })
    if (res.statusCode === 401 || res.statusCode === 403) {
      isLoggedIn.value = false
      profiles.value = []
      profilesLoadedAt.value = 0
      try { uni.removeStorageSync('xc_token') } catch (_) {}
      return
    }
    if (res.statusCode && res.statusCode >= 400) throw new Error('profile request failed')
    profiles.value = ((res.data || {}).profiles || []).map(p => Object.assign({ meta: {} }, p))
    profilesLoadedAt.value = Date.now()
  } catch (_) {
    profiles.value = []
    profilesLoadedAt.value = 0
    uni.showToast({ title: '档案加载失败', icon: 'none' })
  }
  })()
  try { await profilesLoadingPromise } finally { profilesLoadingPromise = null }
}

function openCreateForm() {
  editingId.value = null
  editingSource.value = 'manual'
  editingMeta.value = {}
  form.name = ''
  form.gender = '男'
  form.calType = '公历'
  form.birthDate = ''
  form.birthClock = '12:00'
  form.birthAddr = ''
  form.profileType = 'self'
  form.isDefault = false
  formError.value = ''
  formOpen.value = true
}

function queryWantsCreate(query) {
  const raw = String(query || '').replace(/^\?/, '')
  if (!raw) return false
  try {
    const params = new URLSearchParams(raw)
    return params.get('action') === 'create' || params.get('new') === '1' || params.get('create') === '1'
  } catch (_) {
    return /(?:^|&)(action=create|new=1|create=1)(?:&|$)/.test(raw)
  }
}

function currentUserManagementQuery() {
  let query = ''
  try {
    const hash = window.location.hash || ''
    if (hash.indexOf('/pages/user-management/index') >= 0 && hash.indexOf('?') >= 0) {
      query = hash.substring(hash.indexOf('?'))
    }
  } catch (_) {}
  if (!query) {
    try { query = sessionStorage.getItem('_nav_query') || '' } catch (_) {}
  }
  return query
}

function consumeCreateQuery(query) {
  if (!queryWantsCreate(query)) return
  try { sessionStorage.removeItem('_nav_query') } catch (_) {}
  try {
    if ((window.location.hash || '').indexOf('/pages/user-management/index?') >= 0) {
      window.history.replaceState({}, '', '#/pages/user-management/index')
    }
  } catch (_) {}
  if (!isLoggedIn.value) {
    openLogin()
    return
  }
  setTimeout(openCreateForm, 80)
}

function openEditForm(profile) {
  const parts = birthParts(profile.birthTime)
  editingId.value = profile.id
  editingSource.value = profile.source || 'manual'
  editingMeta.value = Object.assign({}, profile.meta || {})
  form.name = profile.name || ''
  form.gender = profile.gender || '男'
  form.calType = profile.calType || '公历'
  form.birthDate = parts.date
  form.birthClock = parts.time
  form.birthAddr = profile.birthAddr || ''
  form.profileType = profile.profileType || 'self'
  form.isDefault = !!profile.isDefault
  formError.value = ''
  formOpen.value = true
}

function closeForm() {
  formOpen.value = false
}

function profilePayload(extra) {
  return Object.assign({
    name: form.name.trim(),
    gender: form.gender,
    calType: form.calType,
    birthTime: formBirthTime(),
    birthAddr: form.birthAddr.trim(),
    profileType: form.profileType,
    isDefault: form.isDefault,
    source: editingSource.value || 'manual',
    meta: editingMeta.value || {},
  }, extra || {})
}

async function submitForm() {
  formError.value = ''
  const payload = profilePayload()
  if (!payload.name) { formError.value = '请填写姓名'; return }
  if (!payload.birthTime) { formError.value = '请选择出生日期和时间'; return }
  try {
    const url = editingId.value ? `/api/profiles/${editingId.value}` : '/api/profiles'
    const method = editingId.value ? 'PUT' : 'POST'
    const res = await uni.request({ url, method, data: payload })
    const data = res.data || {}
    if (data.error) { formError.value = data.error; return }
    formOpen.value = false
    await loadProfiles(true)
    uni.showToast({ title: '已保存', icon: 'success' })
  } catch (_) {
    formError.value = '保存失败，请稍后重试'
  }
}

async function setDefault(profile) {
  const parts = birthParts(profile.birthTime)
  try {
    const res = await uni.request({
      url: `/api/profiles/${profile.id}`,
      method: 'PUT',
      data: {
        name: profile.name,
        gender: profile.gender,
        calType: profile.calType,
        birthTime: profile.birthTime,
        birthAddr: profile.birthAddr,
        profileType: profile.profileType || 'self',
        isDefault: true,
        source: profile.source || 'manual',
        meta: profile.meta || {},
      }
    })
    if ((res.data || {}).error) throw new Error(res.data.error)
    await loadProfiles(true)
    uni.showToast({ title: `${profile.name || '档案'}已设为默认`, icon: 'none' })
  } catch (_) {
    uni.showToast({ title: '设置失败', icon: 'none' })
  }
}

function deleteProfile(profile) {
  deleteConfirmProfile.value = profile
  deleteConfirmOpen.value = true
}

function closeDeleteConfirm() {
  if (deleteDeleting.value) return
  deleteConfirmOpen.value = false
  deleteConfirmProfile.value = null
}

async function confirmDeleteProfile() {
  const profile = deleteConfirmProfile.value
  if (!profile || deleteDeleting.value) return
  deleteDeleting.value = true
  try {
    const deleteRes = await uni.request({ url: `/api/profiles/${profile.id}`, method: 'DELETE' })
    const data = deleteRes.data || {}
    if ((deleteRes.statusCode && deleteRes.statusCode >= 400) || data.error) {
      throw new Error(data.error || 'delete profile failed')
    }
    profiles.value = profiles.value.filter(item => item.id !== profile.id)
    activeMobileActionsId.value = null
    profilesLoadedAt.value = 0
    await loadProfiles(true)
    deleteConfirmOpen.value = false
    deleteConfirmProfile.value = null
    uni.showToast({ title: '已删除', icon: 'none' })
  } catch (_) {
    uni.showToast({ title: '删除失败', icon: 'none' })
  } finally {
    deleteDeleting.value = false
  }
}

function storageProfile(profile) {
  return {
    id: profile.id,
    name: profile.name,
    gender: profile.gender,
    calType: profile.calType,
    birthTime: profile.birthTime,
    birthAddr: profile.birthAddr,
    profileType: profile.profileType || 'self',
    source: profile.source || 'profile',
    meta: profile.meta || {},
  }
}

function agentProfileHandoff(profile) {
  return {
    source: 'profile_card',
    profile_id: profile.id,
    profile: storageProfile(profile),
    paipan: {
      source: 'profile_card',
      profile_name: profile.name || '未命名',
      birth_time: profile.birthTime || '',
      birth_addr: profile.birthAddr || '',
    },
  }
}

async function touchProfile(profile) {
  try { await uni.request({ url: `/api/profiles/${profile.id}/touch`, method: 'POST' }) } catch (_) {}
}

function goHash(hash) {
  const path = String(hash || '').replace(/^#/, '')
  if (typeof window !== 'undefined') {
    try {
      if (window.__topNavGo) window.__topNavGo(hash)
      else window.location.hash = hash
    } catch (_) {
      try { window.location.hash = hash } catch (__) {}
    }
    setTimeout(function() {
      try {
        if (window.location && window.location.hash !== hash) window.location.hash = hash
        if (window.__xcRenderTabPath) window.__xcRenderTabPath(path.split('?')[0])
      } catch (_) {}
    }, 60)
    return
  }
  uni.navigateTo({ url: path })
}

async function openBazi(profile) {
  uni.setStorageSync('xc_selected_profile', JSON.stringify(storageProfile(profile)))
  await touchProfile(profile)
  uni.showToast({ title: '已带入命盘，打开八字', icon: 'none' })
  goHash('#/pages/bazi-index/index?fromProfile=1')
}

async function openZiwei(profile) {
  uni.setStorageSync('xc_selected_profile', JSON.stringify(storageProfile(profile)))
  await touchProfile(profile)
  uni.showToast({ title: '已带入命盘，打开紫微', icon: 'none' })
  goHash('#/pages/ziwei/index?fromProfile=1')
}

async function openAgent(profile) {
  uni.setStorageSync('xc_selected_profile', JSON.stringify(storageProfile(profile)))
  uni.setStorageSync('xc_agent_profile_autoselect', String(profile.id))
  uni.setStorageSync('xc_agent_handoff_v1', JSON.stringify(agentProfileHandoff(profile)))
  await touchProfile(profile)
  uni.showToast({ title: '已带入命盘，进入时安agent', icon: 'none' })
  goHash('#/?app=1')
}

function syncAuth(force) {
  const nextLoggedIn = !!uni.getStorageSync('xc_token')
  const becameLoggedIn = !isLoggedIn.value && nextLoggedIn
  isLoggedIn.value = nextLoggedIn
  if (isLoggedIn.value) loadProfiles(!!force || becameLoggedIn)
  else {
    profiles.value = []
    profilesLoadedAt.value = 0
  }
}

function handleAuthChanged(e) {
  isLoggedIn.value = !!(e && e.detail && e.detail.loggedIn)
  if (isLoggedIn.value) loadProfiles(true)
  else {
    profiles.value = []
    profilesLoadedAt.value = 0
  }
}

onMounted(function() {
  syncAuth(true)
  consumeCreateQuery(currentUserManagementQuery())
  try { uni.$on('nav-query', consumeCreateQuery) } catch (_) {}
  try { window.addEventListener('xc-auth-changed', handleAuthChanged) } catch (_) {}
})

onBeforeUnmount(function() {
  try { uni.$off('nav-query', consumeCreateQuery) } catch (_) {}
  try { window.removeEventListener('xc-auth-changed', handleAuthChanged) } catch (_) {}
})

onShow(function() {
  syncAuth(false)
  consumeCreateQuery(currentUserManagementQuery())
  const savedTheme = uni.getStorageSync('xc_theme')
  if (savedTheme && savedTheme !== theme.value) theme.value = savedTheme
})
</script>

<style scoped>
.user-management-page {
  min-height: 100vh;
  background: linear-gradient(135deg, var(--bg-grad-1), var(--bg-grad-2) 58%, var(--bg-grad-3));
  color: var(--text-1);
}
.user-page-wrap {
  position: relative;
  z-index: 1;
  width: min(1180px, calc(100vw - 48px));
  margin: 0 auto;
  padding: 70px 0 44px;
}
.user-hero {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 24px;
  padding: 8px 0 16px;
  border-bottom: 1px solid var(--card-border);
}
.section-tag {
  display: inline-flex;
  padding: 3px 9px;
  border: 1px solid var(--card-border);
  border-radius: 999px;
  color: var(--accent);
  font-size: 0.68rem;
  letter-spacing: 2px;
}
.user-hero-title {
  margin-top: 10px;
  font-family: var(--font-serif);
  font-size: 1.75rem;
  letter-spacing: 4px;
  color: var(--text-1);
}
.user-hero-desc {
  margin-top: 5px;
  color: var(--text-3);
  font-size: 0.84rem;
}
.user-primary-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-height: 38px;
  padding: 0 18px;
  border-radius: 8px;
  background: var(--accent);
  color: #fff8ea;
  font-weight: 700;
  font-size: 0.86rem;
  cursor: pointer;
  box-shadow: 0 12px 26px rgba(120, 82, 28, 0.18);
}
.user-login-panel,
.user-workspace {
  margin-top: 14px;
}
.user-login-panel {
  min-height: 360px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
  border-radius: 8px;
}
.login-mark {
  width: 58px;
  height: 58px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--section-alt);
  color: var(--accent);
  font-weight: 800;
}
.login-title {
  margin-top: 16px;
  font-size: 1.15rem;
  font-weight: 800;
}
.login-desc {
  margin: 8px 0 18px;
  color: var(--text-3);
  font-size: 0.86rem;
}
.stats-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}
.stat-cell {
  min-height: 60px;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid var(--card-border);
  background: var(--card-bg);
}
.stat-num {
  display: block;
  color: var(--text-1);
  font-size: 1.22rem;
  font-weight: 800;
}
.stat-label {
  display: block;
  margin-top: 3px;
  color: var(--text-3);
  font-size: 0.72rem;
}
.mobile-sync-note,
.mobile-card-tools,
.mobile-tag-row {
  display: none;
}
.control-band {
  position: sticky;
  top: 72px;
  z-index: 20;
  display: grid;
  grid-template-columns: minmax(220px, 1fr) auto auto;
  gap: 8px;
  align-items: center;
  margin-top: 10px;
  padding: 8px;
  border-radius: 8px;
  border: 1px solid var(--card-border);
  background: color-mix(in srgb, var(--nav-bg) 88%, transparent);
  backdrop-filter: blur(16px);
}
.search-wrap {
  position: relative;
  box-sizing: border-box;
  height: 38px;
  min-height: 38px;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px 0 12px;
  border-radius: 9px;
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--input-bg) 96%, #fff 4%), var(--input-bg)),
    radial-gradient(circle at 14% 50%, color-mix(in srgb, var(--accent) 9%, transparent), transparent 34%);
  border: 1px solid color-mix(in srgb, var(--input-border) 78%, var(--accent) 22%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.42), 0 8px 18px rgba(88, 66, 34, 0.045);
  transition: border-color 0.18s ease, box-shadow 0.18s ease, background 0.18s ease;
}
.search-wrap:focus-within {
  border-color: color-mix(in srgb, var(--accent) 58%, var(--input-border));
  background:
    linear-gradient(180deg, color-mix(in srgb, var(--input-bg) 88%, #fff 12%), color-mix(in srgb, var(--input-bg) 94%, var(--accent) 6%)),
    radial-gradient(circle at 14% 50%, color-mix(in srgb, var(--accent) 13%, transparent), transparent 36%);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.56), 0 0 0 3px color-mix(in srgb, var(--accent) 12%, transparent), 0 10px 24px rgba(88, 66, 34, 0.08);
}
.profile-search-icon {
  position: relative !important;
  display: block !important;
  flex: 0 0 22px !important;
  width: 22px !important;
  height: 22px !important;
  border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 10%, var(--section-alt));
  box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--accent) 22%, transparent);
}
.profile-search-icon::before {
  content: "";
  position: absolute;
  left: 6px;
  top: 5px;
  width: 8px;
  height: 8px;
  border: 1.6px solid var(--accent);
  border-radius: 50%;
}
.profile-search-icon::after {
  content: "";
  position: absolute;
  left: 13px;
  top: 13px;
  width: 6px;
  height: 1.6px;
  border-radius: 999px;
  background: var(--accent);
  transform: rotate(45deg);
  transform-origin: left center;
}
.search-input {
  flex: 1;
  align-self: center;
  min-width: 0;
  width: 100%;
  height: 38px;
  padding: 0;
  border: 0;
  outline: none;
  display: flex;
  align-items: center;
  transform: translateY(5px);
  background: transparent;
  box-shadow: none;
  color: var(--text-1);
  font-size: 0.88rem;
  line-height: 38px;
}
.search-input :deep(.uni-input-wrapper),
.search-input :deep(.uni-input-form),
.search-input :deep(.uni-input-input) {
  width: 100%;
  height: 38px;
  line-height: 38px;
  display: flex;
  align-items: center;
  color: var(--text-1);
  font-size: 0.88rem;
  letter-spacing: 0;
}
.search-input :deep(.uni-input-placeholder) {
  height: 38px;
  line-height: 38px;
  display: flex;
  align-items: center;
  color: var(--text-3);
  pointer-events: none;
}
.filter-tabs {
  display: flex;
  gap: 5px;
}
.filter-tab,
.sort-trigger {
  min-height: 32px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 10px;
  border: 1px solid var(--card-border);
  border-radius: 7px;
  color: var(--text-2);
  font-size: 0.74rem;
  cursor: pointer;
}
.filter-tab.active {
  border-color: var(--accent);
  background: var(--accent-glow);
  color: var(--accent);
  font-weight: 700;
}
.profile-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-top: 10px;
}
.archive-card {
  display: grid;
  grid-template-columns: 38px minmax(0, 1fr);
  gap: 10px;
  align-items: flex-start;
  padding: 12px;
  border: 1px solid var(--card-border);
  border-radius: 8px;
  background: var(--card-bg);
  transition: border-color 0.18s, transform 0.18s, box-shadow 0.18s;
}
.archive-card:hover {
  border-color: var(--card-border-hover);
  transform: translateY(-1px);
  box-shadow: var(--card-shadow);
}
.archive-card.default {
  border-left: 3px solid var(--accent);
}
.archive-mark {
  width: 36px;
  height: 36px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  border: 1px solid var(--card-border);
  background: var(--section-alt);
  color: var(--accent);
  font-weight: 800;
  overflow: hidden;
  white-space: nowrap;
}
.archive-mark.source-bazi {
  background: color-mix(in srgb, var(--accent) 13%, var(--section-alt));
}
.archive-mark.source-ziwei {
  background: color-mix(in srgb, #8a6bb8 16%, var(--section-alt));
  color: color-mix(in srgb, #8a6bb8 70%, var(--accent));
}
.archive-mark.source-manual {
  background: color-mix(in srgb, var(--text-2) 10%, var(--section-alt));
  color: var(--text-2);
}
.archive-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  align-items: flex-start;
}
.archive-title-row {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 5px;
}
.archive-name {
  min-width: 0;
  max-width: 190px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 1rem;
  font-weight: 800;
}
.archive-gender,
.default-badge,
.source-pill {
  display: inline-flex;
  padding: 2px 7px;
  border-radius: 999px;
  font-size: 0.68rem;
  color: var(--text-3);
  background: var(--section-alt);
  white-space: nowrap;
  flex: 0 0 auto;
}
.default-badge,
.source-pill {
  color: var(--accent);
}
.archive-meta,
.archive-submeta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-top: 6px;
  color: var(--text-2);
  font-size: 0.76rem;
}
.archive-address {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.archive-submeta {
  color: var(--text-4);
  font-size: 0.72rem;
}
.archive-actions {
  grid-column: 1 / -1;
  display: flex;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
  margin-top: 2px;
}
.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.secondary-actions {
  justify-content: flex-end;
}
.action-btn {
  min-height: 28px;
  padding: 0 9px;
  border: 1px solid var(--card-border);
  border-radius: 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--text-2);
  font-size: 0.72rem;
  cursor: pointer;
  white-space: nowrap;
}
.action-btn.primary {
  color: var(--accent);
  border-color: color-mix(in srgb, var(--accent) 42%, transparent);
}
.action-btn.accent {
  min-width: 86px;
  color: #fff8ea;
  background: var(--accent);
  border-color: var(--accent);
}
.action-btn.ghost {
  background: color-mix(in srgb, var(--section-alt) 72%, transparent);
}
.action-btn.danger {
  color: var(--danger);
  border-color: color-mix(in srgb, var(--danger) 36%, transparent);
}
.empty-state {
  margin-top: 12px;
  min-height: 260px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  border: 1px dashed var(--card-border);
  border-radius: 8px;
  background: var(--section-alt);
}
.empty-title {
  font-weight: 800;
}
.empty-desc {
  margin: 8px 0 16px;
  color: var(--text-3);
  font-size: 0.82rem;
}
.profile-modal {
  position: fixed;
  inset: 0;
  z-index: 1000;
}
.profile-modal-mask {
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.38);
}
.profile-modal-panel {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(620px, calc(100vw - 28px));
  max-height: calc(100dvh - 32px);
  overflow-y: auto;
  transform: translate(-50%, -50%);
  border-radius: 10px;
  border: 1px solid var(--card-border);
  background: var(--bg-grad-1);
  box-shadow: 0 26px 80px rgba(0, 0, 0, 0.32);
  padding: 20px;
  box-sizing: border-box;
}
.modal-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}
.modal-title {
  font-size: 1.15rem;
  font-weight: 800;
}
.modal-desc {
  margin-top: 4px;
  color: var(--text-3);
  font-size: 0.78rem;
}
.modal-close {
  width: 32px;
  height: 32px;
  display: grid;
  place-items: center;
  border-radius: 50%;
  color: var(--text-3);
  cursor: pointer;
}
.form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}
.form-field.wide {
  grid-column: 1 / -1;
}
.field-label {
  display: block;
  margin-bottom: 6px;
  color: var(--text-3);
  font-size: 0.76rem;
}
.field-input,
.field-picker {
  width: 100%;
  min-height: 40px;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--input-border);
  background: var(--input-bg);
  color: var(--text-1);
  font-size: 0.86rem;
  box-sizing: border-box;
}
.switch-field {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}
.mini-switch {
  width: 46px;
  height: 25px;
  padding: 3px;
  border-radius: 999px;
  background: var(--input-bg);
  border: 1px solid var(--input-border);
  cursor: pointer;
}
.mini-switch-dot {
  width: 17px;
  height: 17px;
  border-radius: 50%;
  background: var(--text-3);
  transition: transform 0.18s, background 0.18s;
}
.mini-switch.active .mini-switch-dot {
  transform: translateX(20px);
  background: var(--accent);
}
.modal-error {
  margin-top: 12px;
  color: var(--danger);
  font-size: 0.78rem;
}
.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 18px;
}
.modal-btn {
  min-height: 36px;
  padding: 0 18px;
  border-radius: 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}
.modal-btn.secondary {
  border: 1px solid var(--card-border);
  color: var(--text-2);
}
.modal-btn.primary {
  background: var(--accent);
  color: #fff8ea;
  font-weight: 800;
}
.delete-confirm-modal {
  z-index: 1100;
}
.delete-confirm-mask {
  background: rgba(20, 16, 10, 0.46);
  backdrop-filter: blur(10px) saturate(120%);
}
.delete-confirm-panel {
  position: absolute;
  left: 50%;
  top: 50%;
  width: min(430px, calc(100vw - 30px));
  transform: translate(-50%, -50%);
  border: 1px solid color-mix(in srgb, var(--accent) 22%, var(--card-border));
  border-radius: 12px;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.72), rgba(255,255,255,0.28)),
    var(--bg-grad-1);
  box-shadow: 0 24px 72px rgba(68, 45, 18, 0.18), inset 0 1px 0 rgba(255,255,255,0.72);
  padding: 18px;
  box-sizing: border-box;
}
[data-theme="dark"] .delete-confirm-panel {
  background:
    linear-gradient(180deg, rgba(255,255,255,0.08), rgba(255,255,255,0.03)),
    rgba(31, 29, 24, 0.94);
  box-shadow: 0 24px 78px rgba(0,0,0,0.36), inset 0 1px 0 rgba(255,255,255,0.08);
}
.delete-confirm-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}
.delete-confirm-mark {
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--danger) 44%, transparent);
  background: color-mix(in srgb, var(--danger) 10%, transparent);
  color: var(--danger);
  font-weight: 900;
  line-height: 1;
}
.delete-confirm-copy {
  min-width: 0;
  flex: 1;
}
.delete-confirm-title {
  color: var(--text-1);
  font-family: var(--font-serif);
  font-size: 1.02rem;
  font-weight: 800;
  letter-spacing: 2px;
}
.delete-confirm-desc {
  margin-top: 4px;
  color: var(--text-3);
  font-size: 0.78rem;
  line-height: 1.55;
}
.delete-confirm-close {
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  color: var(--text-3);
  cursor: pointer;
}
.delete-confirm-close:hover {
  color: var(--accent);
  background: var(--accent-glow);
}
.delete-confirm-body {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}
.delete-confirm-row {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  padding: 9px 10px;
  border: 1px solid color-mix(in srgb, var(--accent) 14%, var(--card-border));
  border-radius: 10px;
  background: color-mix(in srgb, var(--card-bg) 72%, transparent);
  color: var(--text-2);
  font-size: 0.78rem;
}
.delete-confirm-row text:first-child {
  flex-shrink: 0;
  color: var(--text-4);
}
.delete-confirm-row text:last-child {
  min-width: 0;
  color: var(--text-1);
  text-align: right;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.delete-confirm-note {
  margin-top: 2px;
  padding: 10px 12px;
  border: 1px solid color-mix(in srgb, var(--danger) 18%, transparent);
  border-radius: 10px;
  background: color-mix(in srgb, var(--danger) 7%, transparent);
  color: var(--text-2);
  font-size: 0.78rem;
  line-height: 1.55;
}
.delete-confirm-subnote {
  color: var(--text-4);
  font-size: 0.72rem;
  line-height: 1.5;
}
.delete-confirm-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-top: 18px;
}
.delete-confirm-btn {
  min-height: 38px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.82rem;
  font-weight: 800;
  cursor: pointer;
  transition: transform 0.16s ease, border-color 0.16s ease, background 0.16s ease, opacity 0.16s ease;
}
.delete-confirm-btn:hover {
  transform: translateY(-1px);
}
.delete-confirm-btn.secondary {
  border: 1px solid color-mix(in srgb, var(--accent) 18%, var(--card-border));
  background: var(--input-bg);
  color: var(--text-2);
}
.delete-confirm-btn.danger {
  border: 1px solid color-mix(in srgb, var(--danger) 48%, transparent);
  background: var(--danger);
  color: #fff8ea;
}
.delete-confirm-btn.loading {
  opacity: 0.68;
  pointer-events: none;
}
[data-theme="dark"] {
  --bg-grad-1: #161a2a;
  --bg-grad-2: #1a1e30;
  --bg-grad-3: #141824;
  --accent: hsl(38, 60%, 60%);
  --accent-glow: hsla(38, 60%, 60%, 0.10);
  --card-bg: rgba(48, 53, 76, 0.85);
  --card-border: rgba(255,255,255,0.12);
  --card-border-hover: rgba(255,255,255,0.18);
  --card-shadow: 0 16px 48px rgba(0,0,0,0.35);
  --input-bg: rgba(58, 64, 90, 0.88);
  --input-border: rgba(255,255,255,0.20);
  --text-1: rgba(240,236,228,0.97);
  --text-2: rgba(195,185,165,0.95);
  --text-3: rgba(170,160,145,0.88);
  --text-4: rgba(150,140,125,0.78);
  --danger: rgba(215,125,110,0.88);
  --nav-bg: rgba(22, 26, 42, 0.92);
  --section-alt: rgba(30,34,55,0.45);
}
[data-theme="light"] {
  --bg-grad-1: #ffffff;
  --bg-grad-2: #fafafa;
  --bg-grad-3: #ffffff;
  --accent: hsl(38, 72%, 30%);
  --accent-glow: hsla(38, 72%, 30%, 0.065);
  --card-bg: rgba(255,255,255,0.70);
  --card-border: rgba(0,0,0,0.055);
  --card-border-hover: rgba(0,0,0,0.09);
  --card-shadow: 0 12px 32px rgba(72, 48, 18, 0.08);
  --input-bg: rgba(255,255,255,0.78);
  --input-border: rgba(0,0,0,0.075);
  --text-1: rgba(20,16,10,0.96);
  --text-2: rgba(70,58,40,0.90);
  --text-3: rgba(100,88,68,0.78);
  --text-4: rgba(120,108,88,0.66);
  --danger: rgba(170,65,50,0.88);
  --nav-bg: rgba(255,255,255,0.95);
  --section-alt: rgba(247,247,244,0.55);
}
@media (max-width: 1080px) {
  .profile-list {
    gap: 8px;
  }
  .archive-actions {
    flex-direction: column;
    gap: 6px;
  }
  .secondary-actions {
    justify-content: flex-start;
  }
}
@media (max-width: 860px) {
  .user-page-wrap {
    width: calc(100vw - 22px);
    padding-top: 54px;
    padding-bottom: 28px;
  }
  .user-hero {
    align-items: flex-start;
    flex-direction: column;
    gap: 9px;
    padding: 2px 0 10px;
  }
  .section-tag {
    padding: 2px 8px;
    font-size: 0.62rem;
    letter-spacing: 1px;
  }
  .user-hero-title {
    margin-top: 6px;
    font-size: 1.22rem;
    letter-spacing: 3px;
  }
  .user-hero-desc {
    margin-top: 2px;
    line-height: 1.55;
    font-size: 0.72rem;
  }
  .user-primary-btn {
    min-height: 34px;
    padding: 0 14px;
    border-radius: 999px;
    font-size: 0.78rem;
  }
  .stats-strip {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding-bottom: 2px;
  }
  .stat-cell {
    flex: 0 0 auto;
    min-width: 72px;
    min-height: 30px;
    padding: 5px 8px;
    border-radius: 999px;
  }
  .stat-num {
    display: inline;
    font-size: 0.8rem;
    margin-right: 3px;
  }
  .stat-label {
    display: inline;
    margin-top: 0;
    font-size: 0.6rem;
  }
  .mobile-sync-note {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 6px;
    min-height: 30px;
    padding: 5px 8px;
    border: 1px solid color-mix(in srgb, var(--accent) 12%, var(--card-border));
    border-radius: 9px;
    background: color-mix(in srgb, var(--accent-glow) 52%, var(--card-bg));
    color: var(--text-2);
    font-size: 0.7rem;
  }
  .mobile-sync-mark {
    width: 20px;
    height: 20px;
    display: grid;
    place-items: center;
    border-radius: 50%;
    background: color-mix(in srgb, var(--accent) 14%, var(--section-alt));
    color: var(--accent);
    font-size: 0.62rem;
    font-weight: 800;
    flex: 0 0 auto;
  }
  .mobile-sync-note text {
    min-width: 0;
    flex: 1;
  }
  .mobile-sync-close {
    width: 24px;
    height: 24px;
    display: grid;
    place-items: center;
    color: var(--text-4);
    font-size: 1rem;
    flex: 0 0 auto;
  }
  .control-band {
    top: 50px;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 7px;
    margin-top: 6px;
    padding: 6px;
    border-radius: 10px;
  }
  .search-wrap {
    grid-column: 1 / -1;
    height: 36px;
    min-height: 36px;
    border-radius: 999px;
    padding-left: 10px;
  }
  .search-input,
  .search-input :deep(.uni-input-wrapper),
  .search-input :deep(.uni-input-form),
  .search-input :deep(.uni-input-input),
  .search-input :deep(.uni-input-placeholder) {
    height: 36px;
    line-height: 36px;
    font-size: 0.82rem;
  }
  .filter-tabs {
    overflow-x: auto;
    padding-bottom: 2px;
    min-width: 0;
  }
  .sort-picker {
    flex: 0 0 auto;
  }
  .filter-tab,
  .sort-trigger {
    min-height: 30px;
    padding: 0 10px;
    border-radius: 999px;
    font-size: 0.72rem;
    white-space: nowrap;
  }
  .profile-list {
    grid-template-columns: 1fr;
    gap: 0;
    margin-top: 7px;
    border: 1px solid var(--card-border);
    border-radius: 12px;
    overflow: hidden;
    background: color-mix(in srgb, var(--card-bg) 70%, transparent);
  }
  .archive-card {
    grid-template-columns: 54px minmax(0, 1fr);
    align-items: center;
    gap: 11px;
    padding: 10px;
    border: 0;
    border-bottom: 1px solid var(--card-border);
    border-radius: 0;
    background: transparent;
    box-shadow: none;
  }
  .archive-card:last-child {
    border-bottom: 0;
  }
  .archive-card:hover {
    transform: none;
    box-shadow: none;
  }
  .archive-card.default {
    border-left: 0;
    background: color-mix(in srgb, var(--accent-glow) 50%, transparent);
  }
  .archive-mark {
    width: 50px;
    height: 50px;
    font-size: 0.94rem;
    letter-spacing: 0;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.18);
  }
  .archive-head {
    align-items: center;
    gap: 7px;
  }
  .archive-title-row {
    flex: 1;
    min-width: 0;
    gap: 5px;
  }
  .archive-name {
    display: inline-block;
    max-width: calc(100vw - 190px);
    font-size: 1.02rem;
    line-height: 1.2;
  }
  .archive-gender,
  .default-badge,
  .source-pill {
    display: none;
  }
  .mobile-card-tools {
    display: flex;
    align-items: center;
    gap: 10px;
    flex: 0 0 auto;
    color: var(--text-4);
    font-size: 1.2rem;
  }
  .mobile-star.active {
    color: var(--accent);
  }
  .mobile-edit {
    font-size: 1.12rem;
  }
  .mobile-more {
    width: 20px;
    height: 22px;
    display: grid;
    place-items: center;
    font-size: 1.08rem;
    letter-spacing: 1px;
  }
  .mobile-tag-row {
    display: flex;
    align-items: center;
    gap: 7px;
    min-width: 0;
    margin-top: 5px;
    color: var(--text-3);
    font-size: 0.76rem;
  }
  .mobile-relation-tag {
    padding: 1px 6px;
    border-radius: 999px;
    background: color-mix(in srgb, var(--accent) 9%, var(--section-alt));
    color: var(--accent);
    white-space: nowrap;
  }
  .mobile-gender-tag {
    color: color-mix(in srgb, #4d8ac8 76%, var(--text-3));
    font-weight: 700;
  }
  .mobile-gender-tag.female {
    color: color-mix(in srgb, #c06ca7 76%, var(--text-3));
  }
  .mobile-date-tag {
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    font-weight: 700;
    letter-spacing: 0.4px;
  }
  .archive-meta {
    margin-top: 4px;
    gap: 0;
    color: var(--text-4);
    font-size: 0.72rem;
  }
  .archive-meta .birth-line {
    display: none;
  }
  .archive-address {
    max-width: calc(100vw - 128px);
  }
  .archive-submeta {
    display: none;
  }
  .archive-actions {
    display: none;
  }
  .archive-card.mobile-actions-open .archive-actions {
    grid-column: 1 / -1;
    width: 100%;
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 6px;
    margin-top: 2px;
    padding-left: 61px;
    box-sizing: border-box;
  }
  .primary-actions {
    width: 100%;
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 6px;
  }
  .secondary-actions {
    display: flex;
    gap: 0;
  }
  .secondary-actions .action-btn.ghost {
    display: none;
  }
  .action-btn {
    min-height: 28px;
    padding: 0 6px;
    border-radius: 999px;
    font-size: 0.7rem;
  }
  .profile-modal-panel {
    left: 0;
    right: 0;
    top: auto;
    bottom: 0;
    width: 100%;
    max-height: 88dvh;
    transform: none;
    border-radius: 14px 14px 0 0;
    padding: 18px 14px 16px;
  }
  .modal-head {
    align-items: center;
  }
  .modal-title {
    font-size: 1.08rem;
  }
  .form-grid {
    grid-template-columns: 1fr;
    gap: 9px;
    margin-top: 14px;
  }
  .field-label {
    margin-bottom: 5px;
    font-size: 0.72rem;
  }
  .field-input,
  .field-picker {
    min-height: 42px;
    border-radius: 10px;
    font-size: 0.88rem;
  }
  .switch-field {
    align-items: center;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid var(--input-border);
    background: var(--input-bg);
  }
  .switch-field .field-label {
    margin-bottom: 0;
    color: var(--text-1);
    font-weight: 700;
  }
  .modal-actions {
    position: sticky;
    bottom: -16px;
    margin: 14px -14px -16px;
    padding: 12px 14px 16px;
    background: var(--bg-grad-1);
    border-top: 1px solid var(--card-border);
  }
}
@media (min-width: 721px) and (max-width: 860px) {
  .user-page-wrap {
    width: 100%;
    box-sizing: border-box;
    padding-left: 32px;
    padding-right: 24px;
  }
  .profile-modal-panel {
    left: 56px;
    right: 0;
    width: calc(100vw - 56px);
    max-width: none;
  }
}
</style>
