<template>
  <view class="page-root" :data-theme="theme">
    <!-- 视频背景层（H5 only） -->
    <!-- #ifdef H5 -->
    <view class="video-bg" :class="{ 'video-fallback': videoFallback, 'video-visible': videoVisible }" id="videoBg">
      <video
        class="video-bg-video"
        id="heroVideo"
        autoplay
        muted
        loop
        playsinline
        @error="onVideoError"
        @loadeddata="onVideoReady"
      >
        <source src="https://assets.mixkit.co/videos/preview/mixkit-abstract-technology-white-lines-2826-large.mp4" type="video/mp4" />
      </video>
      <view class="video-bg-overlay"></view>
    </view>
    <!-- #endif -->
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn"
      @toggle-theme="toggleTheme" ref="topNavRef" />

    <view class="page-wrap">

      <!-- ═══ 首屏 Hero ═══ -->
      <section class="hero-home" :class="{ 'chat-active': comprehensiveMessages.length }">
        <view class="hero-home-content">
          <!-- LOGO 和品牌 -->
          <view class="hero-brand">
            <view class="hero-brand-icon-wrap"><img class="hero-brand-icon" src="/static/images/logo.webp?v=2" alt="时安解忧屋" /></view>
            <view class="hero-brand-name">时安解忧屋</view>
            <view class="hero-brand-divider"></view>
            <view class="hero-brand-slogan">八字定终身格局 · 奇门断当下决策</view>
            <view class="hero-brand-sub">看得懂用得上的民俗命理参考平台</view>
          </view>

          <view class="home-scan-panel" v-if="!comprehensiveMessages.length">
            <view class="home-scan-status">
              <view class="home-scan-status-item">
                <text class="home-scan-label">命盘</text>
                <text class="home-scan-value">{{ selectedProfileName || '待选择' }}</text>
              </view>
              <view class="home-scan-status-item">
                <text class="home-scan-label">术数</text>
                <text class="home-scan-value">{{ selectedToolSummary }}</text>
              </view>
              <view class="home-scan-status-item">
                <text class="home-scan-label">模型</text>
                <text class="home-scan-value">{{ selectedLlmModel.name || '基础模型' }}</text>
              </view>
              <view class="home-scan-status-item">
                <text class="home-scan-label">积分</text>
                <text class="home-scan-value">{{ currentPoints }}</text>
              </view>
            </view>
            <view class="home-scan-actions">
              <view class="home-scan-action" @tap="openProfilePicker">
                <text class="home-scan-action-mark">命</text>
                <text class="home-scan-action-main">选择命盘</text>
                <text class="home-scan-action-sub">载入个人或客户档案</text>
              </view>
              <view class="home-scan-action" @tap="openToolPicker">
                <text class="home-scan-action-mark">术</text>
                <text class="home-scan-action-main">配置术数</text>
                <text class="home-scan-action-sub">支持多模型合参</text>
              </view>
              <view class="home-scan-action" @tap="goToPage('/pages/bazi-index/index')">
                <text class="home-scan-action-mark">八</text>
                <text class="home-scan-action-main">八字排盘</text>
                <text class="home-scan-action-sub">单项排盘入口</text>
              </view>
              <view class="home-scan-action" @tap="goToPage('/pages/points/index')">
                <text class="home-scan-action-mark">分</text>
                <text class="home-scan-action-main">积分中心</text>
                <text class="home-scan-action-sub">充值与明细</text>
              </view>
            </view>
          </view>

          <view class="home-ai-console" :class="{ 'has-chat': comprehensiveMessages.length }">
            <view class="home-ai-chat" v-if="comprehensiveMessages.length">
              <view class="home-ai-chat-head">
                <view class="home-ai-chat-head-main">
                  <text class="home-ai-chat-title">综合解读</text>
                  <text class="home-ai-chat-sub">{{ homeAiContextSummary }}</text>
                </view>
                <view class="home-ai-new-chat" @tap="startNewComprehensiveConversation">新对话</view>
              </view>
              <view
                v-for="(msg, idx) in comprehensiveMessages"
                :key="idx"
                class="home-ai-message"
                :class="msg.role === 'user' ? 'user' : 'assistant'"
              >
                <text class="home-ai-role">{{ msg.role === 'user' ? '你' : '时安综合 AI' }}</text>
                <view class="home-ai-stage-wrap" v-if="msg.stage">
                  <img class="home-ai-stage-logo" src="/static/images/logo.webp?v=2" alt="时安解忧屋" />
                  <view class="home-ai-stage-texts">
                    <text class="home-ai-stage">{{ msg.stage }}</text>
                    <text class="home-ai-stage-note">正在按所选命盘和术数生成，可继续停留在当前页</text>
                  </view>
                </view>
                <view class="home-ai-step-row" v-if="msg.stage && !msg.content">
                  <text>读取资料</text>
                  <text>排盘核对</text>
                  <text>模型解读</text>
                  <text>组织回答</text>
                </view>
                <view class="home-ai-progress-track" v-if="msg.stage">
                  <view class="home-ai-progress-bar"></view>
                </view>
                <text class="home-ai-content" v-if="msg.content">{{ msg.content }}</text>
              </view>
            </view>

            <view class="home-ai-main">
              <textarea
                class="home-ai-input"
                v-model="comprehensiveQuestion"
                auto-height
                maxlength="800"
                :placeholder="comprehensivePlaceholder"
                @keydown="onComprehensiveInputKeydown"
              />
              <view class="home-ai-toolbar">
                <view class="home-ai-toolbar-left">
                  <view class="profile-picker" @tap="openProfilePicker">
                    <text class="profile-plus">＋</text>
                    <text class="profile-name">{{ selectedProfileName || '选择命盘' }}</text>
                  </view>
                  <view class="tool-picker" @tap="openToolPicker">
                    <text class="tool-picker-icon">☷</text>
                    <text>{{ selectedToolSummary }}</text>
                  </view>
                </view>
                <view class="home-ai-toolbar-right">
                  <picker :range="llmModelNames" :value="llmModelIdx" @change="onLlmModelChange">
                    <view class="llm-picker">
                      <text class="llm-name">{{ selectedLlmModel.name || '基础模型' }}</text>
                      <text class="llm-points">消耗 {{ estimatedCost }} · 余 {{ currentPoints }}</text>
                    </view>
                  </picker>
                  <view class="home-ai-send" :class="{ disabled: comprehensiveLoading }" @tap="startComprehensiveAsk">
                    ↑
                  </view>
                </view>
              </view>
            </view>
          </view>
        </view>

      </section>

    </view><!-- page-wrap -->

    <view class="profile-sheet" v-if="profileSheetOpen">
      <view class="profile-sheet-mask" @tap="cancelProfileSelection"></view>
      <view class="profile-sheet-panel">
        <view class="profile-sheet-head">
          <text class="profile-sheet-title">选择命盘</text>
          <text class="profile-sheet-close" @tap="cancelProfileSelection">×</text>
        </view>
        <view class="profile-tabs">
          <view v-for="tab in profileTabs" :key="tab" :class="{ active: profileTab === tab }" @tap="profileTab = tab">{{ tab }}</view>
        </view>
        <view class="profile-options">
          <view v-if="profileGroups[profileTab].length === 0" class="profile-empty">暂无命盘档案</view>
          <view
            class="profile-option"
            v-for="p in profileGroups[profileTab]"
            :key="p.id"
            :class="{ active: isProfileDraftSelected(p) }"
            @tap="toggleProfileSelection(p)"
          >
            <view>
              <text class="profile-option-name">{{ p.name || '未命名' }}</text>
              <text class="profile-option-meta">{{ p.gender }} · {{ formatBirthTime(p.birthTime || p.birth_time) }}</text>
            </view>
            <view class="profile-option-side">
              <text class="profile-option-type">{{ profileTypeLabel(p.profileType || p.profile_type) }}</text>
              <text class="profile-option-check">{{ isProfileDraftSelected(p) ? '✓' : '' }}</text>
            </view>
          </view>
        </view>
        <view class="sheet-actions">
          <view class="sheet-btn sheet-btn-secondary" @tap="cancelProfileSelection">取消</view>
          <view class="sheet-btn sheet-btn-primary" @tap="confirmProfileSelection">确认</view>
        </view>
      </view>
    </view>

    <view class="profile-sheet" v-if="toolSheetOpen">
      <view class="profile-sheet-mask" @tap="toolSheetOpen = false"></view>
      <view class="profile-sheet-panel tool-sheet-panel">
        <view class="profile-sheet-head">
          <text class="profile-sheet-title">选择术数模型</text>
          <text class="profile-sheet-close" @tap="toolSheetOpen = false">×</text>
        </view>
        <view class="tool-options">
          <view
            class="tool-option"
            v-for="tool in toolModels"
            :key="tool.id"
            :class="{ active: selectedToolModels.includes(tool.id) }"
            @tap="toggleToolModel(tool.id)"
          >
            <view>
              <text class="tool-option-name">{{ tool.name }}</text>
              <text class="tool-option-meta">{{ tool.cost }} 积分 · 可复选</text>
            </view>
            <text class="tool-option-check">{{ selectedToolModels.includes(tool.id) ? '✓' : '' }}</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onBeforeUnmount } from 'vue'
import { onLoad, onShow, onHide } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

// ── 主题 ──
const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
const topNavRef = ref(null)
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

// ── 视频背景（H5 only）──
const videoFallback = ref(false)
const videoVisible = ref(false)
function setHomeFixedPage(enabled) {
  // #ifdef H5
  try {
    document.documentElement.classList.toggle('home-fixed-page', !!enabled)
    document.body.classList.toggle('home-fixed-page', !!enabled)
  } catch(_) {}
  // #endif
}
function onVideoError() {
  videoFallback.value = true
  videoVisible.value = true
}
function onVideoReady() {
  videoVisible.value = true
}

// ── 移动端菜单 ──
const mobileMenuOpen = ref(false)
const submenuOpen = reactive({ qimen: false, bazi: false, more: false })
function openMobileMenu() { mobileMenuOpen.value = true }
function closeMobileMenu() { mobileMenuOpen.value = false }
function toggleSubmenu(key) { submenuOpen[key] = !submenuOpen[key] }

// ── 登录状态 ──
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

// ── 首页综合 AI ──
const comprehensiveQuestion = ref('')
const comprehensiveLoading = ref(false)
const profiles = ref([])
const selectedProfiles = ref([])
const draftSelectedProfiles = ref([])
const profileSheetOpen = ref(false)
const toolSheetOpen = ref(false)
const profileTab = ref('全部')
const profileTabs = ['全部', '客户', '用户']
const profileSelectionStorageKey = 'xc_home_selected_profile_keys_v2'
const toolSelectionStorageKey = 'xc_home_selected_tool_models_v2'
const llmModels = ref([{ id: 'basic', name: '基础模型', strength: '基础', cost_base: 2, cost_multiplier: 1, followup_cost: 1 }])
const toolModels = ref([
  { id: 'bazi', name: '八字', cost: 2 },
  { id: 'ziwei', name: '紫微斗数', cost: 3 },
  { id: 'qimen', name: '奇门遁甲', cost: 3 },
  { id: 'liuyao', name: '六爻', cost: 2 },
  { id: 'meihua', name: '梅花易数', cost: 2 },
])
const llmModelIdx = ref(0)
const selectedToolModels = ref(loadSavedToolSelection())
const currentPoints = ref(0)
const comprehensiveMessages = ref([])
const currentComprehensiveConvId = ref(null)
const currentPaipanContext = ref({})
let pendingComprehensiveId = ''
let comprehensiveProgressTimer = null
let comprehensiveTypeTimer = null

const selectedLlmModel = computed(() => llmModels.value[llmModelIdx.value] || llmModels.value[0] || {})
const llmModelNames = computed(() => llmModels.value.map(m => m.name + ' · ' + (m.strength || '基础')))
const comprehensivePlaceholder = computed(() => comprehensiveMessages.value.length ? '请继续输入你想问的问题' : '输入你的问题，选择术数模型后开始综合解读')
const homeAiContextSummary = computed(() => {
  const profileText = selectedProfileName.value || '未选择命盘'
  const toolText = selectedToolSummary.value === '选择术数' ? '未选择术数' : selectedToolSummary.value
  const modelText = selectedLlmModel.value.name || '基础模型'
  const costText = estimatedCost.value ? estimatedCost.value + ' 积分' : '续问'
  return profileText + ' · ' + toolText + ' · ' + modelText + ' · ' + costText
})
const estimatedCost = computed(() => {
  if (comprehensiveMessages.value.length > 0) return selectedLlmModel.value.followup_cost || 0
  const selected = selectedToolModels.value || []
  const profileCount = Math.max(1, selectedProfiles.value.length)
  const toolsCost = selected.reduce((sum, id) => {
    const tool = toolModels.value.find(t => t.id === id)
    return sum + (tool ? Number(tool.cost || 0) : 0)
  }, 0)
  return Math.round((selectedLlmModel.value.cost_base || 0) + toolsCost * profileCount * (selectedLlmModel.value.cost_multiplier || 1))
})
const selectedToolSummary = computed(() => {
  const names = toolModels.value.filter(t => selectedToolModels.value.includes(t.id)).map(t => t.name)
  if (!names.length) return '选择术数'
  if (names.length <= 2) return names.join(' + ')
  return names.slice(0, 2).join(' + ') + ' 等' + names.length + '项'
})
const selectedProfileName = computed(() => {
  const list = selectedProfiles.value || []
  if (!list.length) return ''
  if (list.length === 1) return list[0].name || '未命名'
  return (list[0].name || '未命名') + ' 等' + list.length + '盘'
})
const selectedProfileMeta = computed(() => {
  const p = selectedProfiles.value[0]
  if (!p) return ''
  return (p.gender || '') + ' · ' + formatBirthTime(p.birthTime || p.birth_time)
})
const profileGroups = computed(() => {
  const list = profiles.value || []
  return {
    '全部': list,
    '客户': list.filter(p => (p.profileType || p.profile_type) === 'customer'),
    '用户': list.filter(p => (p.profileType || p.profile_type || 'self') !== 'customer'),
  }
})

function goToPage(url) {
  if (!url) return
  if (url.indexOf('/pages/') === 0) {
    uni.switchTab({
      url,
      fail: function() { uni.navigateTo({ url }) }
    })
  } else {
    uni.navigateTo({ url })
  }
}

function profileTypeLabel(type) {
  if (type === 'customer') return '客户'
  if (type === 'collect') return '收藏'
  if (type === 'bazi_record') return '八字记录'
  return '用户'
}

function formatBirthTime(v) {
  const s = String(v || '')
  if (s.length >= 12) return s.slice(0,4) + '-' + s.slice(4,6) + '-' + s.slice(6,8) + ' ' + s.slice(8,10) + ':' + s.slice(10,12)
  if (s.length >= 8) return s.slice(0,4) + '-' + s.slice(4,6) + '-' + s.slice(6,8)
  return '未填写出生时间'
}

function openProfilePicker() {
  if (!isLoggedIn.value) {
    uni.showToast({ title: '请先登录后选择命盘', icon: 'none' })
    setTimeout(function() {
      try { if (window._openLoginModal) window._openLoginModal() } catch(_) {}
    }, 180)
    return
  }
  draftSelectedProfiles.value = selectedProfiles.value.slice()
  profileSheetOpen.value = true
  loadProfiles()
}

function openToolPicker() {
  toolSheetOpen.value = true
}

function profileKey(p) {
  return (p.source || 'profile') + ':' + String(p.recordId || p.id || '')
}

function readStorageJson(key, fallback) {
  try {
    const raw = uni.getStorageSync(key)
    if (!raw) return fallback
    const parsed = typeof raw === 'string' ? JSON.parse(raw) : raw
    return parsed
  } catch (_) {
    return fallback
  }
}

function writeStorageJson(key, value) {
  try {
    uni.setStorageSync(key, JSON.stringify(value))
  } catch (_) {}
}

function loadSavedToolSelection() {
  const saved = readStorageJson(toolSelectionStorageKey, [])
  return Array.isArray(saved) ? saved.filter(Boolean).map(String) : []
}

function saveSelectedProfiles() {
  writeStorageJson(profileSelectionStorageKey, selectedProfiles.value.map(profileKey))
}

function saveSelectedToolModels() {
  writeStorageJson(toolSelectionStorageKey, selectedToolModels.value.slice())
}

function isProfileSelected(p) {
  const key = profileKey(p)
  return selectedProfiles.value.some(item => profileKey(item) === key)
}

function isProfileDraftSelected(p) {
  const key = profileKey(p)
  return draftSelectedProfiles.value.some(item => profileKey(item) === key)
}

function toggleProfileSelection(p) {
  const list = draftSelectedProfiles.value.slice()
  const key = profileKey(p)
  const idx = list.findIndex(item => profileKey(item) === key)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(p)
  draftSelectedProfiles.value = list
}

function confirmProfileSelection() {
  selectedProfiles.value = draftSelectedProfiles.value.slice()
  saveSelectedProfiles()
  profileSheetOpen.value = false
}

function cancelProfileSelection() {
  draftSelectedProfiles.value = selectedProfiles.value.slice()
  profileSheetOpen.value = false
}

function onLlmModelChange(e) {
  llmModelIdx.value = Number(e.detail.value || 0)
}

function toggleToolModel(id) {
  const list = selectedToolModels.value.slice()
  const idx = list.indexOf(id)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(id)
  selectedToolModels.value = list
  saveSelectedToolModels()
}

async function loadComprehensiveOptions() {
  if (!isLoggedIn.value) return
  try {
    const res = await uni.request({ url: '/api/comprehensive/options' })
    const data = res.data || {}
    if (Array.isArray(data.llm_models) && data.llm_models.length) llmModels.value = data.llm_models
    if (Array.isArray(data.tool_models) && data.tool_models.length) toolModels.value = data.tool_models
    if (typeof data.points === 'number') currentPoints.value = data.points
  } catch (_) {}
}

async function loadProfiles() {
  if (!isLoggedIn.value) return
  try {
    const results = await Promise.all([
      uni.request({ url: '/api/profiles?sort=last_used' }).catch(function() { return { data: {} } }),
      isLoggedIn.value ? uni.request({ url: '/api/bazi/history' }).catch(function() { return { data: {} } }) : { data: {} },
    ])
    const profileData = results[0].data || {}
    const baziData = results[1].data || {}
    const profileList = (profileData.profiles || []).map(function(p) {
      return Object.assign({ source: 'profile' }, p)
    })
    const baziList = (baziData.history || [])
      .filter(function(r) { return r && r.type !== 'hepan' && r.birth_time })
      .map(function(r) {
        return {
          id: 'bazi-' + r.id,
          source: 'bazi_record',
          recordId: r.id,
          name: r.name || '八字记录',
          gender: r.gender || '男',
          calType: r.cal_type || '公历',
          birthTime: r.birth_time || '',
          birthAddr: r.birth_addr || '',
          profileType: 'bazi_record',
          createdAt: r.created_at,
          pillars: r.pillars || '',
        }
      })
    profiles.value = profileList.concat(baziList)
    if (!selectedProfiles.value.length && profiles.value.length) {
      const savedKeys = readStorageJson(profileSelectionStorageKey, [])
      if (Array.isArray(savedKeys) && savedKeys.length) {
        selectedProfiles.value = profiles.value.filter(p => savedKeys.includes(profileKey(p)))
      }
    }
  } catch (_) {
    profiles.value = []
  }
}

function comprehensiveProfilePayload(p) {
  return {
    name: p.name || '未命名',
    gender: p.gender || '男',
    cal_type: p.cal_type || p.calType || '公历',
    birth_time: p.birth_time || p.birthTime || '',
    birth_addr: p.birth_addr || p.birthAddr || '',
    profile_type: p.profile_type || p.profileType || 'self',
    source: p.source || 'profile',
    record_id: p.recordId || null,
  }
}

function normalizeMessageHistory() {
  return comprehensiveMessages.value
    .filter(m => m && (m.role === 'user' || m.role === 'assistant') && m.content)
    .map(m => ({ role: m.role, content: m.content }))
}

function stopComprehensiveProgressTimer() {
  if (comprehensiveProgressTimer) {
    clearInterval(comprehensiveProgressTimer)
    comprehensiveProgressTimer = null
  }
}

function stopComprehensiveTypeTimer() {
  if (comprehensiveTypeTimer) {
    clearInterval(comprehensiveTypeTimer)
    comprehensiveTypeTimer = null
  }
}

function stripComprehensiveMarkdown(text) {
  if (!text) return ''
  return String(text)
    .replace(/\r\n/g, '\n')
    .replace(/^\s*#{1,6}\s*/gm, '')
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*\*/g, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    .replace(/`{1,3}/g, '')
    .replace(/\n{3,}/g, '\n\n')
    .replace(/^\s+/, '')
}

function startComprehensiveTypewriter(aiIndex, state) {
  if (comprehensiveTypeTimer) return
  comprehensiveTypeTimer = setInterval(function() {
    const current = comprehensiveMessages.value[aiIndex]
    if (!current) {
      stopComprehensiveTypeTimer()
      return
    }
    if (!state.queue.length) {
      if (state.done) stopComprehensiveTypeTimer()
      return
    }
    const take = state.queue.length > 3 ? 2 : 1
    state.displayed += state.queue.slice(0, take)
    state.queue = state.queue.slice(take)
    updateComprehensiveAssistant(aiIndex, {
      stage: '',
      content: stripComprehensiveMarkdown(state.displayed)
    })
  }, 35)
}

function updateComprehensiveAssistant(aiIndex, patch) {
  const current = comprehensiveMessages.value[aiIndex]
  if (!current) return null
  comprehensiveMessages.value[aiIndex] = Object.assign({}, current, patch)
  if (comprehensiveMessages.value.length && (patch.content || patch.stage)) {
    scrollComprehensiveChatToBottom('auto')
  }
  return comprehensiveMessages.value[aiIndex]
}

function startComprehensiveProgressTimer(aiIndex) {
  stopComprehensiveProgressTimer()
  const startedAt = Date.now()
  let localIndex = 0
  const localStages = [
    '正在连接综合解读服务',
    '正在读取命盘与排盘记录',
    '正在核对所选命盘和术数',
    '正在生成所选术数盘面',
    '正在整理盘面重点',
    '正在组织综合解读思路',
    '模型正在生成回答，请保持当前页面',
  ]
  updateComprehensiveAssistant(aiIndex, { _lastServerStageAt: startedAt })
  comprehensiveProgressTimer = setInterval(function() {
    const current = comprehensiveMessages.value[aiIndex]
    if (!comprehensiveLoading.value || !current || current.content) {
      stopComprehensiveProgressTimer()
      return
    }
    const elapsed = Math.max(1, Math.floor((Date.now() - startedAt) / 1000))
    const idleMs = Date.now() - (current._lastServerStageAt || startedAt)
    if (idleMs >= 2600) {
      updateComprehensiveAssistant(aiIndex, {
        stage: localStages[Math.min(localIndex, localStages.length - 1)] + ' · 已等待 ' + elapsed + ' 秒'
      })
      localIndex += 1
    } else if (current.stage && elapsed >= 4 && current.stage.indexOf('已等待') < 0) {
      updateComprehensiveAssistant(aiIndex, {
        stage: current.stage.replace(/ · \d+ 秒$/, '') + ' · ' + elapsed + ' 秒'
      })
    }
  }, 1200)
}

async function startComprehensiveAsk() {
  if (comprehensiveLoading.value) return
  if (!isLoggedIn.value) return uni.showToast({ title: '请先登录', icon: 'none' })
  const question = comprehensiveQuestion.value.trim()
  if (!question) return uni.showToast({ title: '请输入问题', icon: 'none' })
  if (!selectedProfiles.value.length) return uni.showToast({ title: '请先选择命盘', icon: 'none' })
  if (!selectedToolModels.value.length) return uni.showToast({ title: '请至少选择一个术数模型', icon: 'none' })
  if (currentPoints.value < estimatedCost.value) return uni.showToast({ title: '积分不足', icon: 'none' })

  const history = normalizeMessageHistory()
  comprehensiveLoading.value = true
  comprehensiveMessages.value.push({ role: 'user', content: question })
  const aiIndex = comprehensiveMessages.value.length
  comprehensiveMessages.value.push({ role: 'assistant', content: '', stage: '正在连接综合解读服务' })
  startComprehensiveProgressTimer(aiIndex)
  scrollComprehensiveChatToBottom()
  const typeState = { queue: '', displayed: '', done: false }

  try {
    const requestBody = {
      question,
      profile_id: selectedProfiles.value.length === 1 && selectedProfiles.value[0].source === 'profile' ? selectedProfiles.value[0].id : undefined,
      profile: selectedProfiles.value.length === 1 ? comprehensiveProfilePayload(selectedProfiles.value[0]) : undefined,
      profiles: selectedProfiles.value.map(comprehensiveProfilePayload),
      llm_model: selectedLlmModel.value.id || 'basic',
      tool_models: selectedToolModels.value,
      history,
      paipan: currentPaipanContext.value,
      conversation_id: currentComprehensiveConvId.value,
    }
    const resp = await fetch('/api/comprehensive/ask/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })
    if (!resp.ok || !resp.body) throw new Error('连接失败')
    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const parts = buffer.split('\n\n')
      buffer = parts.pop() || ''
      parts.forEach(part => {
        const line = part.split('\n').find(l => l.indexOf('data: ') === 0)
        if (!line) return
        const data = JSON.parse(line.slice(6))
        if (data.error) {
          updateComprehensiveAssistant(aiIndex, { stage: '', content: data.error })
          stopComprehensiveProgressTimer()
          stopComprehensiveTypeTimer()
        }
        if (data.message) {
          updateComprehensiveAssistant(aiIndex, { stage: data.message, _lastServerStageAt: Date.now() })
        }
        if (data.content) {
          typeState.queue += data.content
          startComprehensiveTypewriter(aiIndex, typeState)
          stopComprehensiveProgressTimer()
        }
        if (data.conversation_id) currentComprehensiveConvId.value = data.conversation_id
        if (data.paipan) currentPaipanContext.value = data.paipan
        if (typeof data.points_left === 'number') currentPoints.value = data.points_left
        if (data.done) {
          typeState.done = true
          stopComprehensiveProgressTimer()
          try { window.__sidebarCache = null } catch(_) {}
        }
      })
    }
    typeState.done = true
    if (!typeState.queue.length) stopComprehensiveTypeTimer()
    comprehensiveQuestion.value = ''
  } catch (e) {
    stopComprehensiveTypeTimer()
    updateComprehensiveAssistant(aiIndex, { stage: '', content: '生成失败，请稍后重试' })
  } finally {
    comprehensiveLoading.value = false
    stopComprehensiveProgressTimer()
  }
}

function onComprehensiveInputKeydown(e) {
  if (!e || e.isComposing) return
  if (e.key !== 'Enter') return
  if (e.shiftKey || e.altKey || e.ctrlKey || e.metaKey) return
  e.preventDefault()
  startComprehensiveAsk()
}

async function restoreComprehensiveConversation(id) {
  if (!id || !isLoggedIn.value) return
  try {
    const res = await uni.request({ url: '/api/comprehensive/conversations/' + id })
    const data = res.data || {}
    if (!data.id) return
    currentComprehensiveConvId.value = data.id
    currentPaipanContext.value = data.paipan || {}
    selectedToolModels.value = data.models && data.models.length ? data.models : ['bazi']
    comprehensiveMessages.value = (data.messages || []).map(function(m) {
      if (m && m.role === 'assistant' && m.content) {
        return Object.assign({}, m, { content: stripComprehensiveMarkdown(m.content) })
      }
      return m
    })
    const mid = data.model_id || 'basic'
    const mi = llmModels.value.findIndex(m => m.id === mid)
    if (mi >= 0) llmModelIdx.value = mi
    const p = data.profile_data || {}
    selectedProfiles.value = [{
      id: p.id,
      name: p.name,
      gender: p.gender,
      birthTime: p.birth_time,
      calType: p.cal_type,
      birthAddr: p.birth_addr,
      profileType: p.profile_type,
    }]
    scrollComprehensiveChatToBottom()
  } catch (_) {}
}

function scrollComprehensiveChatToBottom(behavior) {
  // #ifdef H5
  setTimeout(function() {
    try {
      const el = document.querySelector('.home-ai-chat')
      if (el) el.scrollTo({ top: el.scrollHeight, behavior: behavior || 'smooth' })
    } catch(_) {}
  }, 120)
  // #endif
}

function restoreComprehensiveFromSidebar(id) {
  const restoreId = id || pendingComprehensiveId
  if (!restoreId) return
  pendingComprehensiveId = ''
  restoreComprehensiveConversation(restoreId)
}

function startNewComprehensiveConversation() {
  stopComprehensiveProgressTimer()
  stopComprehensiveTypeTimer()
  comprehensiveQuestion.value = ''
  comprehensiveMessages.value = []
  currentComprehensiveConvId.value = null
  currentPaipanContext.value = {}
  pendingComprehensiveId = ''
  try { sessionStorage.removeItem('xc_comprehensive_resume_id') } catch(_) {}
  scrollComprehensiveChatToBottom()
}

function onHomeKeydown(e) {
  if (!e || e.isComposing) return
  if (profileSheetOpen.value) {
    if (e.key === 'Escape') {
      e.preventDefault()
      cancelProfileSelection()
    } else if (e.key === 'Enter') {
      e.preventDefault()
      confirmProfileSelection()
    }
    return
  }
  if (toolSheetOpen.value && (e.key === 'Escape' || e.key === 'Enter')) {
    e.preventDefault()
    toolSheetOpen.value = false
  }
}

// ── 页脚 ──
function showFooterInfo(type) {
  const infoMap = {
    contact: '联系方式：请通过社区留言或邮件联系',
    terms: '用户协议：使用本站即表示同意遵守相关条款',
    privacy: '隐私政策：所有数据本地处理，不上传服务器',
    disclaimer: '免责声明：本站内容仅为民俗文化参考',
    copyright: '版权信息：© 2026 时安解忧屋 版权所有',
  }
  uni.showModal({ title: '提示', content: infoMap[type] || '', showCancel: false })
}

function clearAllData() {
  uni.showModal({
    title: '确认清空',
    content: '确认清空所有本地数据？此操作不可撤销。',
    success: (res) => {
      if (res.confirm) {
        var _savedTheme = uni.getStorageSync('xc_theme')
        uni.clearStorageSync()
        if (_savedTheme) uni.setStorageSync('xc_theme', _savedTheme)
        uni.showToast({ title: '已清空', icon: 'success' })
      }
    }
  })
}

// ── Tab 切换回来时同步主题 ──
onLoad((query) => {
  pendingComprehensiveId = query && query.comprehensive_id ? String(query.comprehensive_id) : ''
})

onShow(() => {
  setHomeFixedPage(true)
  var t = uni.getStorageSync('xc_theme')
  if (t && t !== theme.value) {
    theme.value = t
    try {
      document.documentElement.setAttribute('data-theme', t)
      document.body.setAttribute('data-theme', t)
    } catch(_) {}
  }
  // #ifdef H5
  try {
    const resumeId = sessionStorage.getItem('xc_comprehensive_resume_id')
    if (resumeId) {
      sessionStorage.removeItem('xc_comprehensive_resume_id')
      pendingComprehensiveId = resumeId
    }
  } catch(_) {}
  // #endif
  loadComprehensiveOptions()
  loadProfiles().then(function() {
    if (pendingComprehensiveId) {
      const id = pendingComprehensiveId
      pendingComprehensiveId = ''
      restoreComprehensiveConversation(id)
    }
  })
})

onHide(() => {
  setHomeFixedPage(false)
})

// ── 视频加载超时处理（H5 only）──
onMounted(() => {
  loadComprehensiveOptions()
  loadProfiles()
  // #ifdef H5
  setHomeFixedPage(true)
  window._xc_restoreComprehensive = restoreComprehensiveFromSidebar
  window._xc_newComprehensive = startNewComprehensiveConversation
  window.addEventListener('keydown', onHomeKeydown)
  // 视频加载超时处理：3秒后如果视频还没准备好，显示fallback背景
  setTimeout(() => {
    const v = document.getElementById('heroVideo')
    if (v && v.readyState < 2) {
      videoFallback.value = true
      videoVisible.value = true
      v.style.display = 'none'
    }
  }, 3000)
  
  // 即使视频还没加载好，也在页面渲染完成后1秒显示视频背景层（避免刷新时的闪烁）
  setTimeout(() => {
    if (!videoVisible.value) {
      videoVisible.value = true
    }
  }, 1000)
  // #endif
})

onBeforeUnmount(() => {
  stopComprehensiveProgressTimer()
  stopComprehensiveTypeTimer()
  // #ifdef H5
  if (window._xc_restoreComprehensive === restoreComprehensiveFromSidebar) window._xc_restoreComprehensive = null
  if (window._xc_newComprehensive === startNewComprehensiveConversation) window._xc_newComprehensive = null
  window.removeEventListener('keydown', onHomeKeydown)
  setHomeFixedPage(false)
  // #endif
})
</script>

<style scoped>
/* ═══ 变量体系 ═══ */
:root {
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --radius-md: 14px; --radius-lg: 20px;
  --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif;
  --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif;
  --max-w: 1280px;
}
[data-theme="dark"] {
  --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824;
  --accent-h: 38; --accent-s: 60%; --accent-l: 60%;
  --accent: hsl(var(--accent-h), var(--accent-s), var(--accent-l));
  --accent-2: hsl(var(--accent-h), var(--accent-s), 48%);
  --accent-glow: hsla(var(--accent-h), var(--accent-s), var(--accent-l), 0.10);
  --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12);
  --card-border-hover: rgba(255,255,255,0.18);
  --card-shadow: 0 16px 48px rgba(0,0,0,0.35);
  --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20);
  --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95);
  --text-3: rgba(170,160,145,0.88); --text-4: rgba(160,150,135,0.78);
  --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88);
  --info: rgba(120,170,230,0.88);
  --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45);
  --tag-bg: rgba(255,255,255,0.08); --tag-text: rgba(195,185,165,0.85);
}
[data-theme="light"] {
  --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0;
  --accent-h: 38; --accent-s: 72%; --accent-l: 30%;
  --accent: hsl(var(--accent-h), var(--accent-s), var(--accent-l));
  --accent-2: hsl(var(--accent-h), var(--accent-s), 22%);
  --accent-glow: hsla(var(--accent-h), var(--accent-s), var(--accent-l), 0.065);
  --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045);
  --card-border-hover: rgba(0,0,0,0.08);
  --card-shadow: 0 8px 28px rgba(60,40,15,0.055);
  --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065);
  --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90);
  --text-3: rgba(100,88,68,0.78); --text-4: rgba(90,78,58,0.68);
  --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88);
  --info: rgba(30,90,200,0.88);
  --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45);
  --tag-bg: rgba(0,0,0,0.05); --tag-text: rgba(70,58,40,0.80);
}

:global(html.home-fixed-page),
:global(body.home-fixed-page) { height: 100%; overflow: hidden !important; overscroll-behavior: none; }
:global(body.home-fixed-page uni-page-body),
:global(body.home-fixed-page uni-page-wrapper),
:global(body.home-fixed-page .uni-page-body) { height: 100dvh !important; overflow: hidden !important; }

.page-root { height: 100dvh; min-height: 0; overflow: hidden !important; width: 100% !important; max-width: 100vw !important; box-sizing: border-box; }
.bg-layer { position: fixed; inset: 0; z-index: 0; transition: background 0.8s var(--ease); pointer-events: none; overflow: hidden; }
[data-theme="dark"] .bg-layer {
  background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%),
              radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%),
              linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3));
}
[data-theme="light"] .bg-layer {
  background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%),
              radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%),
              linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3));
}
.page-wrap { position: relative; z-index: 1; width: 100%; height: calc(100dvh - 60px); max-width: 100vw; overflow: hidden; box-sizing: border-box; }

@media (min-width: 769px) {
  :deep(.topnav) { padding-left: 16px; padding-right: 16px; }
  :deep(.nav-btn) { padding-left: 8px; padding-right: 8px; font-size: 0.9rem; }
  :deep(.topnav-sidebar-btn) { margin-right: 0; }
}

/* ═══ 视频背景 ═══ */
.video-bg { position: fixed; inset: 0; z-index: -1; overflow: hidden; opacity: 0; visibility: hidden; transition: opacity 0.4s ease, visibility 0.4s ease; }
.video-bg.video-visible { opacity: 1; visibility: visible; }
.video-bg-video { width: 100%; height: 100%; object-fit: cover; opacity: 0.15; filter: blur(2px) saturate(0.5); }
[data-theme="light"] .video-bg-video { opacity: 0.08; }
.video-bg-overlay { position: absolute; inset: 0; background: linear-gradient(180deg, transparent 0%, var(--bg-grad-1) 85%); }
[data-theme="dark"] .video-bg-overlay { background: linear-gradient(180deg, rgba(22,26,42,0.3) 0%, rgba(22,26,42,0.9) 85%); }
[data-theme="light"] .video-bg-overlay { background: linear-gradient(180deg, rgba(247,242,234,0.3) 0%, rgba(247,242,234,0.9) 85%); }
.video-fallback { background: linear-gradient(135deg, var(--bg-grad-1), var(--bg-grad-2), var(--bg-grad-3), var(--bg-grad-2)); background-size: 400% 400%; animation: gradientShift 12s ease infinite; }
@keyframes gradientShift { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
.video-fallback .video-bg-overlay { background: linear-gradient(180deg, transparent 0%, var(--bg-grad-1) 85%) !important; }

/* ═══ 通用区块 ═══ */
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-alt { background: var(--section-alt); }
.section-alt .section { background: none; }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.section-title { font-family: var(--font-serif); font-size: 1.75rem; font-weight: 400; letter-spacing: 3px; color: var(--text-1); margin-bottom: 8px; }
.section-desc { color: var(--text-3); font-size: 0.875rem; margin-bottom: 40px; max-width: 600px; }

/* ═══ Hero ═══ */
.hero-home { height: calc(100dvh - 60px); min-height: 0; display: flex; flex-direction: column; align-items: center; justify-content: center; position: relative; padding: 36px 32px 154px; overflow: hidden; box-sizing: border-box; }
.hero-home-content { max-width: var(--max-w); width: 100%; height: 100%; min-height: 0; margin: 0 auto; text-align: center; display: flex; flex-direction: column; justify-content: center; }
.hero-brand { margin-bottom: 24px; flex: 0 0 auto; }
.hero-home.chat-active { padding: 14px 32px 176px; justify-content: flex-start; }
.hero-home.chat-active .hero-home-content { justify-content: flex-start; }
.hero-home.chat-active .hero-brand { display: flex; align-items: center; justify-content: center; gap: 12px; margin-bottom: 12px; }
.hero-brand-icon-wrap { position: relative; display: flex; align-items: center; justify-content: center; width: 120px; height: 120px; margin: 0 auto 16px; animation: float 6s ease-in-out infinite; }
.hero-brand-icon-wrap::before { content: ''; position: absolute; left: 50%; top: 50%; width: 100%; height: 100%; transform: translate(-50%, -50%); border-radius: 50%; background: var(--hero-logo-backdrop); box-shadow: var(--hero-logo-backdrop-shadow); z-index: 0; }
.hero-brand-icon { width: 100px; height: 100px; object-fit: cover; object-position: center center; position: relative; z-index: 1; display: block; transform: translateY(4px); }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.hero-brand-name { font-family: var(--font-serif); font-size: 2.2rem; font-weight: 400; letter-spacing: 8px; color: var(--text-1); margin-bottom: 12px; background: linear-gradient(135deg, var(--text-1), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-indent: 12px; }
.hero-brand-divider { width: 50px; height: 2px; background: var(--accent); margin: 12px auto; border-radius: 1px; box-shadow: 0 0 12px var(--accent-glow); }
.hero-brand-slogan { font-family: var(--font-serif); font-size: 0.95rem; letter-spacing: 4px; color: var(--accent); margin-bottom: 6px; }
.hero-brand-sub { font-size: 0.78rem; color: var(--text-3); letter-spacing: 1px; }
.hero-home.chat-active .hero-brand-icon-wrap { width: 58px; height: 58px; margin: 0; animation: none; }
.hero-home.chat-active .hero-brand-icon { width: 48px; height: 48px; transform: translateY(2px); }
.hero-home.chat-active .hero-brand-name { font-size: 1.28rem; letter-spacing: 5px; margin: 0; text-indent: 5px; }
.hero-home.chat-active .hero-brand-divider { display: none; }
.hero-home.chat-active .hero-brand-slogan { display: none; }
.hero-home.chat-active .hero-brand-sub { display: none; }

.home-scan-panel { width: min(920px, 100%); margin: 0 auto 18px; display: grid; grid-template-columns: 1fr; gap: 10px; flex: 0 0 auto; }
.home-scan-status { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.home-scan-status-item { min-width: 0; padding: 10px 12px; border: 1px solid rgba(178,149,93,0.14); border-radius: 12px; background: rgba(255,255,255,0.045); backdrop-filter: blur(12px); box-sizing: border-box; text-align: left; }
[data-theme="light"] .home-scan-status-item { background: rgba(255,253,248,0.56); }
.home-scan-label { display: block; font-size: 0.64rem; line-height: 1.2; color: var(--text-3); margin-bottom: 5px; }
.home-scan-value { display: block; min-width: 0; color: var(--text-1); font-size: 0.82rem; line-height: 1.25; font-weight: 600; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-scan-actions { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.home-scan-action { min-width: 0; display: grid; grid-template-columns: 28px minmax(0, 1fr); column-gap: 9px; row-gap: 2px; align-items: center; padding: 10px 12px; border: 1px solid rgba(178,149,93,0.16); border-radius: 14px; background: rgba(34,31,25,0.30); color: var(--text-1); cursor: pointer; box-sizing: border-box; transition: transform .18s ease, border-color .18s ease, background .18s ease; text-align: left; }
[data-theme="light"] .home-scan-action { background: rgba(255,253,248,0.62); }
.home-scan-action:hover { transform: translateY(-1px); border-color: rgba(178,149,93,0.46); background: var(--accent-glow); }
.home-scan-action-mark { grid-row: 1 / span 2; width: 28px; height: 28px; border-radius: 9px; display: flex; align-items: center; justify-content: center; background: var(--accent-glow); color: var(--accent); font-family: var(--font-serif); font-size: 0.82rem; }
.home-scan-action-main { display: block; min-width: 0; color: var(--text-1); font-size: 0.82rem; line-height: 1.2; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-scan-action-sub { display: block; min-width: 0; color: var(--text-3); font-size: 0.66rem; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

/* ═══ 首页综合 AI 输入框 ═══ */
.home-ai-console { max-width: 920px; margin: 0 auto; padding-bottom: 0; text-align: left; display: flex; flex-direction: column; gap: 12px; width: 100%; min-height: 0; overflow: hidden; box-sizing: border-box; }
.home-ai-console.has-chat { width: min(1180px, calc(100vw - 48px)); max-width: none; flex: 1 1 auto; min-height: 0; margin: 0 auto; padding: 0; box-sizing: border-box; overflow: hidden; }
.home-ai-main { position: fixed; left: 50%; bottom: 18px; z-index: 260; transform: translateX(-50%); width: min(960px, calc(100vw - 36px)); box-sizing: border-box; display: flex; flex-direction: column; gap: 10px; padding: 14px; border: 1px solid rgba(178,149,93,0.18); border-radius: 20px; background: rgba(34, 31, 25, 0.50); backdrop-filter: blur(30px) saturate(145%); box-shadow: 0 22px 70px rgba(0,0,0,0.24), inset 0 1px 0 rgba(255,255,255,0.08); overflow-x: hidden; transition: border-color .2s ease, box-shadow .2s ease, background .2s ease; }
.home-ai-main:focus-within { border-color: rgba(178,149,93,0.50); box-shadow: 0 22px 76px rgba(0,0,0,0.26), 0 0 0 3px rgba(178,149,93,0.10), inset 0 1px 0 rgba(255,255,255,0.12); }
[data-theme="light"] .home-ai-main { background: rgba(255,253,248,0.80); box-shadow: 0 16px 44px rgba(60,40,15,0.10), inset 0 1px 0 rgba(255,255,255,0.75); }
[data-theme="light"] .home-ai-main:focus-within { box-shadow: 0 18px 52px rgba(60,40,15,0.13), 0 0 0 3px rgba(150,103,20,0.10), inset 0 1px 0 rgba(255,255,255,0.82); }
.home-ai-input { width: 100%; min-height: 92px; max-height: 180px; padding: 10px 4px 2px; color: var(--text-1); font-size: 0.94rem; line-height: 1.65; background: transparent; border: none; outline: none; box-sizing: border-box; }
.home-ai-input::placeholder { color: rgba(120,108,86,0.68); }
.home-ai-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 40px; flex-wrap: nowrap !important; overflow-x: hidden; box-sizing: border-box; width: 100%; }
.home-ai-toolbar-left { display: flex; align-items: center; gap: 6px; flex-shrink: 1; min-width: 0; }
.home-ai-toolbar-right { display: flex; align-items: center; gap: 6px; margin-left: auto; flex-shrink: 1; min-width: 0; overflow-x: hidden; box-sizing: border-box; }
.profile-picker, .tool-picker, .llm-picker, .home-ai-send { min-height: 36px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.18); background: rgba(255,255,255,0.065); color: var(--text-1); display: flex; align-items: center; justify-content: center; cursor: pointer; box-sizing: border-box; flex-shrink: 0; transition: border-color .18s ease, background .18s ease, transform .18s ease; }
[data-theme="light"] .profile-picker, [data-theme="light"] .tool-picker, [data-theme="light"] .llm-picker { background: rgba(255,251,242,0.76); }
.profile-picker:hover, .tool-picker:hover, .llm-picker:hover { border-color: rgba(178,149,93,0.45); background: var(--accent-glow); }
.profile-picker, .tool-picker { justify-content: flex-start; gap: 6px; padding: 0 10px; max-width: 168px; min-width: 86px; flex-shrink: 1; }
.profile-plus, .tool-picker-icon { width: 20px; height: 20px; border-radius: 50%; background: var(--accent-glow); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; flex-shrink: 0; }
.profile-name, .tool-picker text:last-child { display: block; font-size: 0.75rem; color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile-meta { display: block; margin-top: 2px; font-size: 0.66rem; color: var(--text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.llm-picker { min-width: 96px; max-width: 128px; padding: 4px 10px; flex-direction: column; align-items: flex-start; gap: 1px; color: var(--text-2); white-space: nowrap; flex-shrink: 1; overflow: hidden; }
.llm-name { display: block; width: 100%; overflow: hidden; text-overflow: ellipsis; font-size: 0.72rem; color: var(--text-1); line-height: 1.2; }
.llm-points { display: block; width: 100%; overflow: hidden; text-overflow: ellipsis; font-size: 0.58rem; color: var(--text-3); line-height: 1.2; }
.home-ai-send { width: 36px; height: 36px; min-height: 36px; background: var(--accent); border-color: var(--accent); color: #fff; font-size: 1.1rem; font-weight: 700; line-height: 1; flex-shrink: 0; box-shadow: 0 8px 22px rgba(120,80,12,0.22); }
[data-theme="light"] .home-ai-send { background: var(--accent); border-color: var(--accent); color: #fff; }
.home-ai-send:hover { transform: translateY(-1px); }
.home-ai-send.disabled { opacity: 0.55; pointer-events: none; }
.home-ai-chat { border: 1px solid rgba(178,149,93,0.16); border-radius: 18px; background: rgba(255,255,255,0.045); backdrop-filter: blur(18px); padding: 16px; max-height: 420px; overflow-y: auto; overscroll-behavior: contain; box-shadow: inset 0 1px 0 rgba(255,255,255,0.06); }
[data-theme="light"] .home-ai-chat { background: rgba(255,253,248,0.66); }
.home-ai-console.has-chat .home-ai-chat { flex: 1 1 auto; min-height: 0; max-height: none; height: auto; box-sizing: border-box; }
.home-ai-console.has-chat .home-ai-input { min-height: 62px; max-height: 130px; }
.home-ai-chat-head { position: sticky; top: 0; z-index: 2; display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 12px; margin: -4px 0 12px; border: 1px solid rgba(178,149,93,0.16); border-radius: 14px; background: rgba(34,31,25,0.62); backdrop-filter: blur(18px) saturate(145%); box-shadow: 0 10px 28px rgba(0,0,0,0.12); }
[data-theme="light"] .home-ai-chat-head { background: rgba(255,251,242,0.86); box-shadow: 0 10px 28px rgba(80,55,18,0.08); }
.home-ai-chat-head-main { min-width: 0; display: flex; flex-direction: column; gap: 3px; }
.home-ai-chat-title { color: var(--text-1); font-size: 0.88rem; font-weight: 700; letter-spacing: 1px; }
.home-ai-chat-sub { color: var(--text-3); font-size: 0.72rem; line-height: 1.35; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: min(680px, 62vw); }
.home-ai-new-chat { flex-shrink: 0; height: 30px; padding: 0 12px; border-radius: 999px; display: flex; align-items: center; justify-content: center; color: var(--accent); border: 1px solid rgba(178,149,93,0.22); background: var(--accent-glow); font-size: 0.74rem; cursor: pointer; box-sizing: border-box; }
.home-ai-new-chat:hover { border-color: rgba(178,149,93,0.48); }
.home-ai-message { padding: 14px 16px; border-radius: 14px; margin-bottom: 12px; border: 1px solid rgba(178,149,93,0.14); }
.home-ai-message.user { margin-left: 72px; background: rgba(178,149,93,0.13); border-color: rgba(178,149,93,0.26); }
.home-ai-message.assistant { margin-right: 72px; background: rgba(255,255,255,0.045); }
.home-ai-role { display: block; font-size: 0.68rem; color: var(--text-3); margin-bottom: 6px; }
.home-ai-stage { display: inline; font-size: 0.82rem; color: var(--accent); }
.home-ai-stage-wrap { display: flex; align-items: center; gap: 8px; margin: 4px 0; }
.home-ai-stage-logo { width: 22px; height: 22px; border-radius: 50%; flex-shrink: 0; animation: stage-spin 1.8s linear infinite; }
.home-ai-stage-texts { min-width: 0; display: flex; flex-direction: column; gap: 2px; }
.home-ai-stage-note { color: var(--text-3); font-size: 0.68rem; line-height: 1.35; }
.home-ai-step-row { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 6px; margin: 10px 0 8px; }
.home-ai-step-row text { min-width: 0; padding: 5px 6px; border-radius: 999px; color: var(--text-3); background: rgba(178,149,93,0.08); border: 1px solid rgba(178,149,93,0.10); text-align: center; font-size: 0.64rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; box-sizing: border-box; }
.home-ai-step-row text:nth-child(1) { color: var(--accent); border-color: rgba(178,149,93,0.26); }
@keyframes stage-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
.home-ai-progress-track { height: 3px; margin-top: 8px; border-radius: 999px; overflow: hidden; background: rgba(178,149,93,0.12); }
.home-ai-progress-bar { width: 38%; height: 100%; border-radius: inherit; background: linear-gradient(90deg, transparent, var(--accent), transparent); animation: progress-sweep 1.35s ease-in-out infinite; }
@keyframes progress-sweep { 0% { transform: translateX(-110%); } 100% { transform: translateX(280%); } }
.home-ai-content { display: block; white-space: pre-wrap; font-size: 0.9rem; color: var(--text-2); line-height: 1.86; letter-spacing: 0; word-break: break-word; }

.profile-sheet { position: fixed; inset: 0; z-index: 400; }
.profile-sheet-mask { position: absolute; inset: 0; background: rgba(20,16,10,0.50); backdrop-filter: blur(10px); }
.profile-sheet-panel { position: absolute; left: 50%; bottom: 24px; transform: translateX(-50%); width: min(640px, calc(100vw - 28px)); max-height: 72vh; overflow: hidden; border-radius: 20px; border: 1px solid rgba(178,149,93,0.20); background: rgba(31, 29, 24, 0.92); box-shadow: 0 24px 80px rgba(0,0,0,0.34), inset 0 1px 0 rgba(255,255,255,0.08); padding: 20px; box-sizing: border-box; backdrop-filter: blur(30px) saturate(145%); }
[data-theme="light"] .profile-sheet-panel { background: rgba(255,253,248,0.96); box-shadow: 0 24px 80px rgba(60,40,15,0.14), inset 0 1px 0 rgba(255,255,255,0.85); }
.profile-sheet-panel::before { content: ''; display: block; width: 42px; height: 4px; border-radius: 999px; background: rgba(178,149,93,0.30); margin: 0 auto 14px; }
.profile-sheet-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.profile-sheet-title { color: var(--text-1); font-size: 1rem; font-family: var(--font-serif); letter-spacing: 2px; }
.profile-sheet-close { width: 30px; height: 30px; border-radius: 50%; color: var(--text-3); font-size: 1.25rem; cursor: pointer; display: flex; align-items: center; justify-content: center; border: 1px solid transparent; }
.profile-sheet-close:hover { color: var(--accent); border-color: rgba(178,149,93,0.24); background: var(--accent-glow); }
.profile-tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.profile-tabs view { flex: 1; text-align: center; padding: 8px 10px; border-radius: 10px; border: 1px solid var(--card-border); color: var(--text-3); font-size: 0.8rem; cursor: pointer; }
.profile-tabs view.active { background: var(--accent-glow); border-color: var(--accent); color: var(--accent); }
.profile-options { max-height: 48vh; overflow-y: auto; }
.profile-option { display: flex; justify-content: space-between; gap: 16px; padding: 12px; border-radius: 14px; border: 1px solid rgba(178,149,93,0.13); background: rgba(255,255,255,0.035); margin-bottom: 8px; cursor: pointer; transition: border-color .18s ease, background .18s ease; }
.profile-option-name { display: block; color: var(--text-1); font-size: 0.88rem; }
.profile-option-meta { display: block; margin-top: 4px; color: var(--text-3); font-size: 0.72rem; }
.profile-option.active { border-color: rgba(178,149,93,0.62); background: var(--accent-glow); }
.profile-option-side { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.profile-option-type { color: var(--accent); font-size: 0.72rem; white-space: nowrap; }
.profile-option-check { width: 22px; height: 22px; border-radius: 50%; border: 1px solid var(--card-border); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.78rem; font-weight: 700; }
.profile-empty { padding: 28px; text-align: center; color: var(--text-3); font-size: 0.84rem; }
.sheet-actions { display: flex; justify-content: flex-end; gap: 10px; padding-top: 12px; margin-top: 12px; border-top: 1px solid rgba(178,149,93,0.14); }
.sheet-btn { min-width: 88px; height: 38px; border-radius: 999px; display: flex; align-items: center; justify-content: center; font-size: 0.82rem; cursor: pointer; border: 1px solid rgba(178,149,93,0.18); box-sizing: border-box; transition: transform .18s ease, border-color .18s ease; }
.sheet-btn:hover { transform: translateY(-1px); border-color: rgba(178,149,93,0.45); }
.sheet-btn-secondary { color: var(--text-2); background: var(--input-bg); }
.sheet-btn-primary { color: #fff; background: var(--accent); border-color: var(--accent); }
.tool-sheet-panel { width: min(520px, calc(100vw - 28px)); }
.tool-options { display: grid; gap: 8px; }
.tool-option { display: flex; align-items: center; justify-content: space-between; gap: 16px; min-height: 58px; padding: 10px 12px; border-radius: 14px; border: 1px solid rgba(178,149,93,0.13); background: rgba(255,255,255,0.035); cursor: pointer; box-sizing: border-box; transition: border-color .18s ease, background .18s ease; }
.tool-option.active { border-color: rgba(178,149,93,0.62); background: var(--accent-glow); }
.tool-option-name { display: block; color: var(--text-1); font-size: 0.88rem; }
.tool-option-meta { display: block; margin-top: 4px; color: var(--text-3); font-size: 0.72rem; }
.tool-option-check { width: 24px; height: 24px; border-radius: 50%; border: 1px solid var(--card-border); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.86rem; font-weight: 700; flex-shrink: 0; }

/* ═══ 页脚 ═══ */
.site-footer { background: var(--nav-bg); border-top: 1px solid var(--card-border); padding: 24px 32px 24px; margin-top: 0; }
.footer-disclaimer { max-width: var(--max-w); margin: 0 auto 32px; padding: 14px 20px; border-radius: 10px; background: rgba(215,125,110,0.08); border: 1px solid rgba(215,125,110,0.15); font-size: 0.75rem; color: var(--danger); line-height: 1.6; text-align: center; }
.footer-grid { max-width: var(--max-w); margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 40px; }
.footer-col-title { font-size: 0.8125rem; color: var(--text-2); margin-bottom: 12px; letter-spacing: 1px; }
.footer-col navigator, .footer-col .footer-link { display: block; font-size: 0.75rem; color: var(--text-3); text-decoration: none; padding: 6px 0; }
.footer-icp { font-size: 0.6875rem; color: var(--text-3); margin-top: 8px; }
.footer-bottom { max-width: var(--max-w); margin: 24px auto 0; padding-top: 16px; border-top: 1px solid var(--card-border); display: flex; justify-content: space-between; align-items: center; }
.footer-bottom-text { font-size: 0.6875rem; color: var(--text-3); }
.btn-clear-data { font-size: 0.6875rem; padding: 4px 10px; border-radius: 6px; background: transparent; border: 1px solid var(--danger); color: var(--danger); cursor: pointer; }

/* ═══ 弹窗 ═══ */
.modal-overlay { display: none; position: fixed; inset: 0; z-index: 300; background: rgba(0,0,0,0.55); backdrop-filter: blur(8px); align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; width: 360px; backdrop-filter: blur(40px); box-shadow: var(--card-shadow); }
.modal-title { font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px; text-align: center; margin-bottom: 24px; color: var(--text-1); }
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }

/* ═══ 响应式 ═══ */
@media (max-width: 1024px) {
  .footer-grid { grid-template-columns: 1fr; gap: 24px; }
}
@media (min-width: 769px) and (max-height: 720px) {
  .hero-home { padding: 20px 32px 132px; }
  .hero-brand { margin-bottom: 16px; }
  .hero-brand-icon-wrap { width: 96px; height: 96px; margin-bottom: 10px; }
  .hero-brand-icon { width: 80px; height: 80px; transform: translateY(3px); }
  .hero-brand-name { font-size: 1.82rem; letter-spacing: 6px; margin-bottom: 8px; text-indent: 6px; }
  .hero-brand-divider { margin: 8px auto; }
  .hero-brand-slogan { font-size: 0.82rem; letter-spacing: 3px; }
  .hero-brand-sub { display: none; }
  .home-scan-panel { margin-bottom: 12px; }
  .home-scan-status-item, .home-scan-action { padding-top: 8px; padding-bottom: 8px; }
  .home-scan-action-sub { display: none; }
  .home-ai-input { min-height: 74px; max-height: 120px; }
  .home-ai-main { bottom: 14px; }
  .hero-home.chat-active { padding: 10px 32px 158px; }
  .hero-home.chat-active .hero-brand { margin-bottom: 10px; }
  .hero-home.chat-active .hero-brand-icon-wrap { width: 50px; height: 50px; }
  .hero-home.chat-active .hero-brand-icon { width: 42px; height: 42px; transform: translateY(2px); }
  .hero-home.chat-active .hero-brand-name { font-size: 1.14rem; letter-spacing: 4px; text-indent: 4px; }
}
@media (min-width: 769px) and (max-height: 620px) {
  .hero-home { padding: 14px 32px 120px; }
  .hero-brand { margin-bottom: 10px; }
  .hero-brand-icon-wrap { width: 78px; height: 78px; margin-bottom: 8px; }
  .hero-brand-icon { width: 64px; height: 64px; transform: translateY(2px); }
  .hero-brand-name { font-size: 1.45rem; letter-spacing: 4px; margin-bottom: 6px; text-indent: 4px; }
  .hero-brand-divider, .hero-brand-slogan, .hero-brand-sub { display: none; }
  .home-scan-panel { margin-bottom: 8px; gap: 8px; }
  .home-scan-status { display: none; }
  .home-scan-actions { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .home-scan-action { grid-template-columns: 22px minmax(0, 1fr); padding: 7px 8px; border-radius: 12px; }
  .home-scan-action-mark { width: 22px; height: 22px; border-radius: 7px; font-size: 0.7rem; }
  .home-scan-action-main { font-size: 0.72rem; }
  .home-scan-action-sub { display: none; }
  .home-ai-input { min-height: 58px; max-height: 92px; font-size: 0.9rem; }
  .home-ai-main { padding: 10px; gap: 6px; bottom: 10px; }
  .home-ai-toolbar { min-height: 34px; }
  .profile-picker, .tool-picker, .llm-picker, .home-ai-send { min-height: 32px; }
  .home-ai-send { width: 32px; height: 32px; }
  .hero-home.chat-active { padding: 8px 32px 156px; }
  .hero-home.chat-active .hero-brand { margin-bottom: 8px; }
  .hero-home.chat-active .hero-brand-icon-wrap { width: 42px; height: 42px; }
  .hero-home.chat-active .hero-brand-icon { width: 34px; height: 34px; transform: translateY(1px); }
  .hero-home.chat-active .hero-brand-name { font-size: 1rem; letter-spacing: 3px; text-indent: 3px; }
}
@media (max-width: 768px) {
  .hero-home { height: calc(100dvh - 60px); min-height: 0; padding: 34px 16px 126px; }
  .hero-home.chat-active { height: calc(100dvh - 60px); min-height: 0; padding: 10px 16px 162px; }
  .hero-brand { margin-bottom: 38px; }
  .hero-home.chat-active .hero-brand { gap: 8px; margin-bottom: 10px; }
  .hero-home.chat-active .hero-brand-icon-wrap { width: 48px; height: 48px; margin: 0; }
  .hero-home.chat-active .hero-brand-icon { width: 40px; height: 40px; transform: translateY(2px); }
  .hero-home.chat-active .hero-brand-name { font-size: 1.05rem; letter-spacing: 3px; margin: 0; text-indent: 3px; }
  .hero-home.chat-active .hero-brand-divider { display: none; }
  .hero-home.chat-active .hero-brand-slogan { font-size: 0.68rem; letter-spacing: 2px; }
  .hero-brand-name { font-size: 2rem; letter-spacing: 6px; }
  .hero-brand-slogan { font-size: 0.875rem; letter-spacing: 3px; }
  .home-scan-panel { width: 100%; margin-bottom: 12px; gap: 8px; }
  .home-scan-status { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
  .home-scan-status-item { padding: 8px 10px; border-radius: 10px; }
  .home-scan-label { font-size: 0.58rem; margin-bottom: 3px; }
  .home-scan-value { font-size: 0.72rem; }
  .home-scan-actions { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
  .home-scan-action { padding: 8px 9px; border-radius: 12px; }
  .home-scan-action-sub { display: none; }
  .home-ai-console { margin-top: 0; padding-bottom: 0; }
  .home-ai-console.has-chat { width: calc(100vw - 32px); padding: 0; margin-top: 0; }
  .home-ai-console.has-chat .home-ai-chat { height: auto; min-height: 0; }
  .home-ai-main { bottom: 10px; width: calc(100vw - 18px); border-radius: 16px; }
  .home-ai-main { padding: 12px; gap: 8px; }
  .home-ai-input { min-height: 76px; font-size: 0.9rem; }
  .home-ai-console.has-chat .home-ai-input { min-height: 58px; max-height: 116px; }
  .home-ai-toolbar { gap: 4px; flex-wrap: nowrap !important; overflow-x: hidden; box-sizing: border-box; }
  .home-ai-toolbar-left, .home-ai-toolbar-right { gap: 4px; }
  .home-ai-toolbar-right { gap: 3px; overflow-x: hidden; box-sizing: border-box; }
  .profile-picker, .tool-picker { max-width: 84px; padding: 0 6px; min-height: 30px; }
  .profile-plus, .tool-picker-icon { width: 18px; height: 18px; font-size: 0.72rem; }
  .profile-name, .tool-picker text:last-child { font-size: 0.66rem; }
  .llm-picker { min-width: 88px; max-width: 98px; padding: 3px 7px; min-height: 30px; align-items: flex-start; }
  .llm-name { font-size: 0.64rem; }
  .llm-points { font-size: 0.52rem; }
  .home-ai-send { width: 30px; height: 30px; min-height: 30px; font-size: 0.95rem; }
  .home-ai-message.user, .home-ai-message.assistant { margin-left: 0; margin-right: 0; }
  .home-ai-chat-head { align-items: flex-start; padding: 9px 10px; gap: 8px; }
  .home-ai-chat-sub { max-width: calc(100vw - 148px); font-size: 0.66rem; }
  .home-ai-new-chat { height: 28px; padding: 0 10px; font-size: 0.68rem; }
  .home-ai-step-row { gap: 4px; }
  .home-ai-step-row text { padding: 4px 3px; font-size: 0.56rem; }
  .section { padding: 48px 16px; }
  .section-title { font-size: 1.35rem; }
  .section-desc { font-size: 0.8125rem; }
}
@media (max-width: 480px) {
  .hero-home { padding: 54px 16px 120px; }
  .hero-home.chat-active { height: calc(100dvh - 60px); min-height: 0; padding: 10px 16px 156px; }
  .hero-brand-icon-wrap { width: 120px; height: 120px; }
  .hero-brand-icon { width: 90px; height: 90px; transform: translateY(3px); }
  .hero-brand-name { font-size: 1.6rem; letter-spacing: 4px; }
  .hero-brand-slogan { font-size: 0.75rem; letter-spacing: 3px; }
  .hero-brand-sub { font-size: 0.75rem; }
  .home-scan-panel { display: none; }
  .hero-home.chat-active .hero-brand-slogan { display: none; }
  .home-ai-console.has-chat { width: calc(100vw - 32px); padding-top: 0; }
  .home-ai-console.has-chat .home-ai-chat { height: auto; min-height: 0; padding: 10px; }
  .home-ai-main { padding: 10px; gap: 6px; border-radius: 16px; }
  .home-ai-input { min-height: 68px; font-size: 0.86rem; padding: 8px 4px 2px; }
  .home-ai-toolbar { gap: 3px; flex-wrap: nowrap !important; overflow-x: hidden; box-sizing: border-box; }
  .home-ai-toolbar-left, .home-ai-toolbar-right { gap: 3px; }
  .home-ai-toolbar-right { overflow-x: hidden; box-sizing: border-box; }
  .profile-picker, .tool-picker { max-width: 72px; padding: 0 4px; min-height: 28px; }
  .profile-plus, .tool-picker-icon { width: 16px; height: 16px; font-size: 0.66rem; }
  .profile-name, .tool-picker text:last-child { font-size: 0.6rem; }
  .llm-picker { min-width: 76px; max-width: 82px; padding: 2px 6px; min-height: 28px; }
  .llm-name { font-size: 0.58rem; }
  .llm-points { font-size: 0.48rem; }
  .home-ai-send { width: 26px; height: 26px; min-height: 26px; font-size: 0.9rem; }
  .home-ai-chat-head { margin: -2px 0 10px; border-radius: 12px; }
  .home-ai-chat-title { font-size: 0.8rem; }
  .home-ai-chat-sub { max-width: calc(100vw - 136px); font-size: 0.6rem; }
  .home-ai-stage-note { font-size: 0.6rem; }
  .home-ai-step-row text { font-size: 0.5rem; }
  .section { padding: 32px 16px; }
  .section-title { font-size: 1.15rem; }
  .section-desc { font-size: 0.75rem; }
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .footer-col:nth-child(3) { grid-column: 1 / -1; }
  .site-footer { padding: 32px 16px 24px; margin-top: 0; }
  .footer-bottom { flex-direction: column; gap: 8px; text-align: center; }
}
</style>
