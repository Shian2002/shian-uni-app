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

          <view class="home-ai-console" :class="{ 'has-chat': comprehensiveMessages.length }">
            <view class="home-ai-chat" v-if="comprehensiveMessages.length" @scroll="onHomeChatScroll">
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
                <view class="home-tool-cards" v-if="msg.artifacts && msg.artifacts.length">
                  <view
                    class="home-tool-card"
                    v-for="artifact in msg.artifacts"
                    :key="artifact.key"
                    :class="{ collapsed: artifact.collapsed }"
                  >
                    <view class="home-tool-card-head" @tap="toggleArtifact(idx, artifact.key)">
                      <view>
                        <text class="home-tool-card-title">{{ artifact.title }}</text>
                        <text class="home-tool-card-sub">{{ artifactSummary(artifact) }}</text>
                      </view>
                      <text class="home-tool-card-toggle">{{ artifact.collapsed ? '展开' : '收起' }}</text>
                    </view>
                    <view class="home-tool-card-body" v-if="!artifact.collapsed">
                      <view class="home-artifact-render" v-html="renderArtifactHtml(artifact)"></view>
                      <view class="home-artifact-analysis" v-if="artifact.analysis">
                        <view class="home-artifact-analysis-title">{{ artifact.title }}解析</view>
                        <text>{{ artifact.analysis }}</text>
                      </view>
                    </view>
                  </view>
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
                    <text>{{ autoSelectTools ? '自动选术数' : selectedToolSummary }}</text>
                  </view>
                </view>
                <view class="home-ai-toolbar-right">
                  <picker :range="readingModeNames" :value="readingModeIdx" @change="onReadingModeChange">
                    <view class="reading-mode-picker">
                      <text class="reading-mode-label">解读模式</text>
                      <text class="reading-mode-name">{{ selectedReadingMode.name }}</text>
                    </view>
                  </picker>
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
          <view class="tool-option auto-option" :class="{ active: autoSelectTools }" @tap="toggleAutoSelectTools">
            <view>
              <text class="tool-option-name">自动选择术数</text>
              <text class="tool-option-meta">按问题自动匹配八字、奇门、六爻、梅花、紫微、塔罗、择吉</text>
            </view>
            <text class="tool-option-check">{{ autoSelectTools ? '✓' : '' }}</text>
          </view>
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
const autoToolStorageKey = 'xc_home_auto_tool_select_v1'
const readingModeStorageKey = 'xc_home_reading_mode_v1'
const readingModes = [
  { id: 'concise', name: '简洁', cost_delta: -1 },
  { id: 'standard', name: '标准', cost_delta: 0 },
  { id: 'deep', name: '深度', cost_delta: 3 },
]
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
const autoSelectTools = ref(readStorageJson(autoToolStorageKey, true) !== false)
const currentPoints = ref(0)
const aiSingleCredits = ref(0)
const aiComboCredits = ref(0)
const dailyLightAvailable = ref(false)
const comprehensiveMessages = ref([])
const currentComprehensiveConvId = ref(null)
const currentPaipanContext = ref({})
const currentArtifacts = ref({})
const readingMode = ref(readStorageJson(readingModeStorageKey, 'standard'))
const shouldAutoFollowChat = ref(true)
let pendingComprehensiveId = ''
let comprehensiveProgressTimer = null
let comprehensiveTypeTimer = null

const selectedLlmModel = computed(() => llmModels.value[llmModelIdx.value] || llmModels.value[0] || {})
const llmModelNames = computed(() => llmModels.value.map(m => m.name + ' · ' + (m.strength || '基础')))
const selectedReadingMode = computed(() => readingModes.find(m => m.id === readingMode.value) || readingModes[1])
const readingModeNames = computed(() => readingModes.map(m => m.name))
const readingModeIdx = computed(() => Math.max(0, readingModes.findIndex(m => m.id === selectedReadingMode.value.id)))
const comprehensivePlaceholder = computed(() => comprehensiveMessages.value.length ? '请继续输入你想问的问题' : '输入你的问题，选择术数模型后开始综合解读')
const homeAiContextSummary = computed(() => {
  const profileText = selectedProfileName.value || '未选择命盘'
  const toolText = selectedToolSummary.value === '选择术数' ? '未选择术数' : selectedToolSummary.value
  const modelText = selectedLlmModel.value.name || '基础模型'
  const costText = estimatedCost.value ? estimatedCost.value + ' 积分' : '次数包/体验额度'
  return profileText + ' · ' + toolText + ' · ' + modelText + ' · ' + costText
})
const estimatedCost = computed(() => {
  if (comprehensiveMessages.value.length > 0) return Math.max(0, (selectedLlmModel.value.followup_cost || 0) + modeCostDelta())
  const selected = selectedToolModels.value || []
  if (selected.length > 1 && aiComboCredits.value > 0) return 0
  if (selected.length === 1 && aiSingleCredits.value > 0) return 0
  const profileCount = Math.max(1, selectedProfiles.value.length)
  const toolsCost = selected.reduce((sum, id) => {
    const tool = toolModels.value.find(t => t.id === id)
    return sum + (tool ? Number(tool.cost || 0) : 0)
  }, 0)
  const cost = Math.round((selectedLlmModel.value.cost_base || 0) + toolsCost * profileCount * (selectedLlmModel.value.cost_multiplier || 1) + modeCostDelta())
  if (dailyLightAvailable.value && cost <= 2) return 0
  return cost
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

function onReadingModeChange(e) {
  const idx = Number(e.detail.value || 0)
  readingMode.value = (readingModes[idx] && readingModes[idx].id) || 'standard'
  writeStorageJson(readingModeStorageKey, readingMode.value)
}

function modeCostDelta() {
  const mode = selectedReadingMode.value || readingModes[1]
  return Number(mode.cost_delta || 0)
}

function toggleToolModel(id) {
  autoSelectTools.value = false
  writeStorageJson(autoToolStorageKey, false)
  const list = selectedToolModels.value.slice()
  const idx = list.indexOf(id)
  if (idx >= 0) list.splice(idx, 1)
  else list.push(id)
  selectedToolModels.value = list
  saveSelectedToolModels()
}

function toggleAutoSelectTools() {
  autoSelectTools.value = !autoSelectTools.value
  writeStorageJson(autoToolStorageKey, autoSelectTools.value)
}

async function loadComprehensiveOptions() {
  if (!isLoggedIn.value) return
  try {
    const res = await uni.request({ url: '/api/comprehensive/options' })
    const data = res.data || {}
    if (Array.isArray(data.llm_models) && data.llm_models.length) llmModels.value = data.llm_models
    if (Array.isArray(data.tool_models) && data.tool_models.length) toolModels.value = data.tool_models
    if (typeof data.points === 'number') currentPoints.value = data.points
    if (typeof data.ai_single_credits === 'number') aiSingleCredits.value = data.ai_single_credits
    if (typeof data.ai_combo_credits === 'number') aiComboCredits.value = data.ai_combo_credits
    dailyLightAvailable.value = !!data.daily_light_available
  } catch (_) {}
}

async function loadProfiles() {
  if (!isLoggedIn.value) return
  try {
    const res = await uni.request({ url: '/api/profiles?sort=last_used' })
    const profileData = res.data || {}
    const profileList = (profileData.profiles || []).map(function(p) {
      return Object.assign({ source: 'profile' }, p)
    })
    profiles.value = profileList
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
    meta: p.meta || {},
  }
}

function getToolName(id) {
  const tool = toolModels.value.find(t => t.id === id)
  return tool ? tool.name : id
}

function htmlEscape(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function pillarText(pillar) {
  if (!pillar) return ''
  return pillar.gan_zhi || ((pillar.gan || '') + (pillar.zhi || '')) || String(pillar)
}

function artifactListFromMap(map) {
  const order = ['qimen.pan', 'bazi.basic', 'bazi.yun', 'liuyao.pan', 'meihua.pan', 'ziwei.pan', 'tarot.cards', 'zeji.days']
  const source = map || {}
  return Object.keys(source)
    .sort(function(a, b) {
      const ai = order.indexOf(a)
      const bi = order.indexOf(b)
      return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi)
    })
    .map(function(key) {
      const artifact = source[key] || {}
      return Object.assign({}, artifact, {
        key: artifact.key || key,
        title: artifact.title || artifactTitle(key, artifact.tool),
        collapsed: !!artifact.collapsed,
      })
    })
}

function appendArtifactAnalysis(aiIndex, artifactKey, content) {
  const current = comprehensiveMessages.value[aiIndex]
  if (!current || !artifactKey || !content) return
  const artifacts = (current.artifacts || []).map(function(artifact) {
    if (artifact.key !== artifactKey) return artifact
    return Object.assign({}, artifact, {
      collapsed: false,
      analysis: stripComprehensiveMarkdown((artifact.analysis || '') + content)
    })
  })
  updateComprehensiveAssistant(aiIndex, { artifacts })
  scrollComprehensiveChatToBottom('auto')
}

function artifactTitle(key, tool) {
  const map = {
    'bazi.basic': '八字基本排盘',
    'bazi.yun': '大运流年流月',
    'qimen.pan': '奇门遁甲完整盘',
    'liuyao.pan': '六爻卦象',
    'meihua.pan': '梅花易数卦象',
    'ziwei.pan': '紫微斗数三合盘',
    'tarot.cards': '塔罗牌面',
    'zeji.days': '择吉结果',
  }
  return map[key] || getToolName(tool || key)
}

function artifactSummary(artifact) {
  const data = artifact && artifact.data ? artifact.data : {}
  if (artifact.key === 'bazi.basic') {
    const fp = data.four_pillars || {}
    return [pillarText(fp.year), pillarText(fp.month), pillarText(fp.day), pillarText(fp.hour)].filter(Boolean).join(' ')
  }
  if (artifact.key === 'bazi.yun') return '按问题追加推运依据，不重复基础盘'
  if (artifact.key === 'qimen.pan') return [data.ju, data.solar_date].filter(Boolean).join(' · ') || '完整九宫盘'
  if (artifact.key === 'liuyao.pan') return [data.ben_gua, data.bian_gua].filter(Boolean).join(' → ') || '六亲六神世应'
  if (artifact.key === 'meihua.pan') return '本卦 · 互卦 · 变卦 · 体用'
  if (artifact.key === 'ziwei.pan') return ((data.twelve_palaces || data.palaces || []).length || 12) + ' 宫'
  if (artifact.key === 'tarot.cards') return (data.spread && data.spread.name) || data.spread_name || '抽牌翻牌结果'
  if (artifact.key === 'zeji.days') return (data.best_days || []).length + ' 个候选日'
  return artifact.title || ''
}

function renderKV(label, value) {
  return '<div class="artifact-kv"><span>' + htmlEscape(label) + '</span><strong>' + htmlEscape(value || '-') + '</strong></div>'
}

function renderBaziBasicArtifact(data) {
  const fp = data.four_pillars || {}
  const rows = [
    ['年柱', fp.year],
    ['月柱', fp.month],
    ['日柱', fp.day],
    ['时柱', fp.hour],
  ].map(function(row) {
    const pillar = row[1] || {}
    const gan = pillar.gan || String(pillarText(pillar) || '').slice(0, 1)
    const zhi = pillar.zhi || String(pillarText(pillar) || '').slice(1, 2)
    return '<div class="bz-artifact-pillar"><span class="bz-artifact-label">' + htmlEscape(row[0]) + '</span><div class="bz-artifact-gz"><b class="wx-color-' + wxClass(ganWuxing(gan)) + '">' + htmlEscape(gan || '-') + '</b><b class="wx-color-' + wxClass(zhiWuxing(zhi)) + '">' + htmlEscape(zhi || '-') + '</b></div><span class="bz-artifact-sub">' + htmlEscape(pillar.nayin || '') + '</span></div>'
  }).join('')
  const wuxing = data.wu_xing || data.wuxing_stats || {}
  const wuxingHtml = ['金', '木', '水', '火', '土'].map(function(k) {
    return '<span class="bz-wuxing-chip wx-color-' + wxClass(k) + '">' + k + ' ' + htmlEscape(wuxing[k] === undefined ? '-' : wuxing[k]) + '</span>'
  }).join('')
  return '<div class="bz-artifact-panel">' +
    '<div class="bz-artifact-head"><div><b>八字基本排盘</b><span>' + htmlEscape([data.name, data.gender, data.birth_solar || data.birth_time].filter(Boolean).join(' · ')) + '</span></div><em>' + htmlEscape(data.birth_lunar || '') + '</em></div>' +
    '<div class="bz-artifact-pillars">' + rows + '</div>' +
    '<div class="bz-artifact-meta">' +
    '<span>日主 <b>' + htmlEscape(data.day_master || (fp.day && fp.day.gan) || '-') + '</b></span>' +
    '<span>强弱 <b>' + htmlEscape(data.strength || (data.wang_shuai_detail && data.wang_shuai_detail.strength) || '-') + '</b></span>' +
    '<span>格局 <b>' + htmlEscape((data.geju && data.geju.geju) || '-') + '</b></span>' +
    '<span>出生地 <b>' + htmlEscape(data.birth_addr || (data.location && data.location.addr) || '-') + '</b></span>' +
    '</div><div class="bz-wuxing-row">' + wuxingHtml + '</div>' +
    '</div>'
}

function renderBaziYunArtifact(data) {
  const dayun = data.dayun || data.da_yun || data.luck_pillars || []
  const liunian = data.liu_nian || data.liunians || []
  const colorGz = function(gz) {
    const text = String(gz || '')
    return text.split('').map(function(ch) {
      const wx = ganWuxing(ch) || zhiWuxing(ch)
      return '<b class="wx-text-' + wxClass(wx) + '">' + htmlEscape(ch) + '</b>'
    }).join('')
  }
  const itemGz = function(item) {
    if (!item) return ''
    return item.gan_zhi || item.gz || item.name || item.stem_branch || [item.gan, item.zhi].filter(Boolean).join('')
  }
  const itemLabel = function(item) {
    if (!item) return ''
    if (item.start_age && item.end_age) return item.start_age + '-' + item.end_age + '岁'
    return item.age_range || item.range || item.start_age || item.age || item.year || ''
  }
  const renderRow = function(title, list) {
    const items = (Array.isArray(list) ? list : []).slice(0, 12).map(function(item) {
      const label = itemLabel(item)
      const value = itemGz(item)
      const sub = item.gan_shishen_abbrev || item.shi_shen || item.ss_full || item.tgSs || ''
      const year = item.start_year || item.year || ''
      return '<div class="bz-yun-item"><span class="bz-yun-year">' + htmlEscape(year) + '</span><span class="bz-yun-age">' + htmlEscape(label) + '</span><strong class="bz-yun-gz">' + colorGz(value) + '</strong><em>' + htmlEscape(sub) + '</em></div>'
    }).join('')
    return '<div class="bz-yun-section"><div class="bz-yun-title">' + htmlEscape(title) + '</div><div class="bz-yun-scroll">' + (items || '<span class="artifact-empty">暂无数据</span>') + '</div></div>'
  }
  return '<div class="bz-yun-panel">' +
    renderRow('大运', dayun) +
    renderRow('流年', liunian) +
    renderRow('流月', data.liu_yue || data.liu_month || []) +
    '</div>'
}

function ganWuxing(gan) {
  return ({ '甲': '木', '乙': '木', '丙': '火', '丁': '火', '戊': '土', '己': '土', '庚': '金', '辛': '金', '壬': '水', '癸': '水' })[gan] || ''
}

function zhiWuxing(zhi) {
  return ({ '子': '水', '丑': '土', '寅': '木', '卯': '木', '辰': '土', '巳': '火', '午': '火', '未': '土', '申': '金', '酉': '金', '戌': '土', '亥': '水' })[zhi] || ''
}

function pickValue(obj, keys, fallback) {
  for (let i = 0; i < keys.length; i++) {
    if (obj && obj[keys[i]] !== undefined && obj[keys[i]] !== null && obj[keys[i]] !== '') return obj[keys[i]]
  }
  return fallback === undefined ? '' : fallback
}

function wxClass(wx) {
  const map = { '金': 'jin', '木': 'mu', '水': 'shui', '火': 'huo', '土': 'tu' }
  return map[wx] || ''
}

function wsClass(ws) {
  const map = { '旺': 'wang', '相': 'xiang', '休': 'xiu', '囚': 'qiu', '死': 'si' }
  return map[ws] || 'xiu'
}

function relClass(rel) {
  if (rel === '被生' || rel === '比和') return 'ji'
  if (rel === '被克') return 'xiong'
  return 'zhong'
}

function normalizeMeihuaData(data) {
  const tiYong = data.tiYong || data.ti_yong || {}
  return {
    methodLabel: pickValue(data, ['methodLabel', 'method_label'], '时间起卦'),
    paipanTime: pickValue(data, ['paipanTime', 'paipan_time', 'time'], ''),
    ganzhi: data.ganzhi || '',
    dongYao: pickValue(data, ['dongYao', 'dong_yao'], ''),
    benGua: data.benGua || data.ben_gua || {},
    huGua: data.huGua || data.hu_gua || {},
    bianGua: data.bianGua || data.bian_gua || {},
    benGuaYao: data.benGuaYao || data.ben_gua_yao || null,
    huGuaYao: data.huGuaYao || data.hu_gua_yao || null,
    bianGuaYao: data.bianGuaYao || data.bian_gua_yao || null,
    tiYong: {
      tiPosition: pickValue(tiYong, ['tiPosition', 'ti_position'], ''),
      tiGua: pickValue(tiYong, ['tiGua', 'ti_gua'], ''),
      tiTrigram: pickValue(tiYong, ['tiTrigram', 'ti_trigram'], ''),
      tiWuxing: pickValue(tiYong, ['tiWuxing', 'ti_wuxing'], ''),
      tiWangshuai: pickValue(tiYong, ['tiWangshuai', 'ti_wangshuai'], ''),
      yongPosition: pickValue(tiYong, ['yongPosition', 'yong_position'], ''),
      yongGua: pickValue(tiYong, ['yongGua', 'yong_gua'], ''),
      yongTrigram: pickValue(tiYong, ['yongTrigram', 'yong_trigram'], ''),
      yongWuxing: pickValue(tiYong, ['yongWuxing', 'yong_wuxing'], ''),
      yongWangshuai: pickValue(tiYong, ['yongWangshuai', 'yong_wangshuai'], ''),
      tiYongRel: pickValue(tiYong, ['tiYongRel', 'ti_yong_rel', 'relation'], ''),
      tiYongJiXiong: pickValue(tiYong, ['tiYongJiXiong', 'ti_yong_ji_xiong', 'jixiong'], ''),
      tiHuRel: pickValue(tiYong, ['tiHuRel', 'ti_hu_rel'], ''),
      huWuxing: pickValue(tiYong, ['huWuxing', 'hu_wuxing'], ''),
      tiBianRel: pickValue(tiYong, ['tiBianRel', 'ti_bian_rel'], ''),
      bianWuxing: pickValue(tiYong, ['bianWuxing', 'bian_wuxing'], ''),
      verdict: tiYong.verdict || '',
    }
  }
}

function renderMeihuaGuaCard(label, gua, cardClass, dongYao, yaoList) {
  if (!gua) return ''
  const upper = gua.upper || {}
  const lower = gua.lower || {}
  let html = '<div class="gua-card ' + htmlEscape(cardClass) + '">'
  html += '<div class="gua-card-label">' + htmlEscape(label) + '</div>'
  html += '<div class="gua-card-name">' + htmlEscape(gua.name || '') + '</div>'
  if (Array.isArray(yaoList) && yaoList.length === 6) {
    html += '<div class="gua-yao-wrap">'
    for (let i = 5; i >= 0; i--) {
      const isYang = Number(yaoList[i]) === 1
      const isDong = (i + 1) === Number(dongYao)
      html += '<div class="gua-yao ' + (isYang ? 'yang' : 'yin') + (isDong ? ' dong-yao' : '') + '">'
      html += isYang ? '<div class="gua-yao-line"></div>' : '<div class="gua-yao-line"></div><div class="gua-yao-line"></div>'
      html += '</div>'
    }
    html += '</div>'
  } else {
    html += '<div class="gua-trigram">' + htmlEscape((upper.trigram || '') + (lower.trigram || '')) + '</div>'
  }
  html += '<div class="gua-sub-info">'
  html += '<span>上卦 ' + htmlEscape([upper.name, upper.nature, upper.wuxing].filter(Boolean).join('·')) + '</span>'
  html += '<span>下卦 ' + htmlEscape([lower.name, lower.nature, lower.wuxing].filter(Boolean).join('·')) + '</span>'
  html += '</div></div>'
  return html
}

function renderMeihuaArtifact(data) {
  const d = normalizeMeihuaData(data)
  let html = '<div class="mh-result-wrap">'
  html += '<div class="mh-summary">'
  html += '<span><b>起卦方式：</b>' + htmlEscape(d.methodLabel) + '</span>'
  html += '<span><b>排盘时间：</b>' + htmlEscape(d.paipanTime) + '</span>'
  if (d.ganzhi) html += '<span><b>干支：</b>' + htmlEscape(d.ganzhi) + '</span>'
  html += '</div>'
  html += '<div class="gua-display">'
  html += renderMeihuaGuaCard('本卦', d.benGua, 'ben-gua', d.dongYao, d.benGuaYao)
  html += renderMeihuaGuaCard('互卦', d.huGua, 'hu-gua', 0, d.huGuaYao)
  html += renderMeihuaGuaCard('变卦', d.bianGua, 'bian-gua', 0, d.bianGuaYao)
  html += '</div>'
  if (d.tiYong && (d.tiYong.tiGua || d.tiYong.yongGua || d.tiYong.verdict)) {
    html += '<div class="ti-yong-section">'
    html += '<div class="ti-yong-title">🌸 体用分析</div>'
    html += '<div class="ti-yong-grid">'
    html += '<div class="ti-yong-box ti"><div class="ti-yong-label">体卦（' + htmlEscape(d.tiYong.tiPosition) + '）</div><div class="ti-yong-gua">' + htmlEscape(d.tiYong.tiGua) + '</div><div class="ti-yong-wx">' + htmlEscape(d.tiYong.tiTrigram) + ' <span class="wx-tag ' + wxClass(d.tiYong.tiWuxing) + '">' + htmlEscape(d.tiYong.tiWuxing) + '</span> <span class="ws-tag ' + wsClass(d.tiYong.tiWangshuai) + '">' + htmlEscape(d.tiYong.tiWangshuai) + '</span></div></div>'
    html += '<div class="ti-yong-rel ' + relClass(d.tiYong.tiYongRel) + '">体' + htmlEscape(d.tiYong.tiWuxing) + ' ' + htmlEscape(d.tiYong.tiYongRel) + ' 用' + htmlEscape(d.tiYong.yongWuxing) + '</div>'
    html += '<div class="ti-yong-box yong"><div class="ti-yong-label">用卦（' + htmlEscape(d.tiYong.yongPosition) + '）</div><div class="ti-yong-gua">' + htmlEscape(d.tiYong.yongGua) + '</div><div class="ti-yong-wx">' + htmlEscape(d.tiYong.yongTrigram) + ' <span class="wx-tag ' + wxClass(d.tiYong.yongWuxing) + '">' + htmlEscape(d.tiYong.yongWuxing) + '</span> <span class="ws-tag ' + wsClass(d.tiYong.yongWangshuai) + '">' + htmlEscape(d.tiYong.yongWangshuai) + '</span></div></div>'
    html += '</div><table class="mh-analysis-table"><tr><th>分析项</th><th>关系</th><th>吉凶</th></tr>'
    if (d.tiYong.tiYongJiXiong) html += '<tr><td>体用关系</td><td>体' + htmlEscape(d.tiYong.tiWuxing) + ' ' + htmlEscape(d.tiYong.tiYongRel) + ' 用' + htmlEscape(d.tiYong.yongWuxing) + '</td><td>' + htmlEscape(d.tiYong.tiYongJiXiong) + '</td></tr>'
    if (d.tiYong.tiHuRel) html += '<tr><td>互卦与体</td><td>体' + htmlEscape(d.tiYong.tiWuxing) + ' ' + htmlEscape(d.tiYong.tiHuRel) + ' 互' + htmlEscape(d.tiYong.huWuxing) + '</td><td>-</td></tr>'
    if (d.tiYong.tiBianRel) html += '<tr><td>变卦与体</td><td>体' + htmlEscape(d.tiYong.tiWuxing) + ' ' + htmlEscape(d.tiYong.tiBianRel) + ' 变' + htmlEscape(d.tiYong.bianWuxing) + '</td><td>-</td></tr>'
    html += '</table>'
    if (d.tiYong.verdict) html += '<div class="mh-verdict">' + htmlEscape(d.tiYong.verdict) + '</div>'
    html += '</div>'
  }
  html += '</div>'
  return html
}

function normalizeQimenData(data) {
  return {
    fourPillars: data.fourPillars || data.four_pillars || {},
    palaces: data.palaces || data.gong_pan || [],
    solarDate: pickValue(data, ['solarDate', 'solar_date'], ''),
    panType: pickValue(data, ['panType', 'pan_type'], ''),
    xunKong: data.xunKong || data.xun_kong || data.xunkong || {},
    solarTerm: pickValue(data, ['solarTerm', 'solar_term'], ''),
    ju: data.ju || '',
    xunShou: pickValue(data, ['xunShou', 'xun_shou'], ''),
    zhiFu: pickValue(data, ['zhiFu', 'zhi_fu'], ''),
    zhiShi: pickValue(data, ['zhiShi', 'zhi_shi'], ''),
  }
}

function renderQimenArtifact(data) {
  const d = normalizeQimenData(data)
  const palaces = d.palaces || []
  const luoOrder = [4, 9, 2, 3, 5, 7, 8, 1, 6]
  const fp = d.fourPillars || {}
  let html = '<div class="qm-result-wrap"><div class="qm-summary">'
  html += '<span><b>盘式：</b>' + htmlEscape(d.panType || '转盘奇门') + '</span>'
  if (d.solarDate) html += '<span><b>时间：</b>' + htmlEscape(d.solarDate) + '</span>'
  if (d.ju) html += '<span><b>局数：</b>' + htmlEscape(d.ju) + '</span>'
  if (d.solarTerm) html += '<span><b>节气：</b>' + htmlEscape(d.solarTerm) + '</span>'
  html += '<span><b>四柱：</b>' + htmlEscape([fp.year, fp.month, fp.day, fp.hour].filter(Boolean).join(' ')) + '</span>'
  html += '</div><div class="qm-nine-grid">'
  luoOrder.forEach(function(gongNum) {
    const p = palaces[gongNum - 1] || palaces.find(function(x) { return Number(x.gong || x.gong_num || x.number) === gongNum }) || {}
    if (gongNum === 5) {
      html += '<div class="qm-palace center"><div class="qm-center-title">奇门遁甲</div><div class="qm-center-meta">' + htmlEscape([d.ju, d.xunShou && ('旬首 ' + d.xunShou), d.zhiFu && ('值符 ' + d.zhiFu), d.zhiShi && ('值使 ' + d.zhiShi)].filter(Boolean).join(' · ')) + '</div></div>'
      return
    }
    const name = p.name || p.gong || p.palace || (gongNum + '宫')
    const tianGan = pickValue(p, ['tianGan', 'tian_gan'], '')
    const diGan = pickValue(p, ['diGan', 'di_gan'], '')
    const men = pickValue(p, ['men', 'door'], '')
    const xing = pickValue(p, ['xing', 'star'], '')
    const shen = pickValue(p, ['shen', 'god'], '')
    const tianPan = pickValue(p, ['tianPan', 'tian_pan'], '')
    const diPan = pickValue(p, ['diPan', 'di_pan'], '')
    html += '<div class="qm-palace">'
    html += '<div class="qm-palace-head"><b>' + htmlEscape(name) + '</b><span>' + htmlEscape(gongNum + '宫') + '</span></div>'
    html += '<div class="qm-star-row"><span class="qm-star red">' + htmlEscape(tianGan || tianPan) + '</span><span class="qm-star blue">' + htmlEscape(xing) + '</span><span class="qm-star green">' + htmlEscape(men) + '</span></div>'
    html += '<div class="qm-info-row"><span>' + htmlEscape(shen) + '</span><span>' + htmlEscape(diGan || diPan) + '</span></div>'
    html += '</div>'
  })
  html += '</div></div>'
  return html
}

function renderYaoGraphic(isYang) {
  return isYang ? '<div class="ly-yang-bar"></div>' : '<div class="ly-yin-bars"><div class="ly-yin-seg"></div><div class="ly-yin-seg"></div></div>'
}

function renderLiuyaoArtifact(data) {
  const details = data.details || data.lines || []
  const bianDetails = data.bian_details || data.changed_details || []
  const benName = data['本卦'] || data.ben_gua || ''
  const bianName = data['变卦'] || data.bian_gua || ''
  const hasBian = !!bianName || bianDetails.length
  const movingCount = details.filter(function(x) { return x && x.is_moving }).length
  let html = '<div class="ly-result-wrap"><div class="ly-ben-bian-box">'
  html += '<div class="ly-ben-bian-top"><div class="ly-ben-bian-name-block"><div class="ly-ben-bian-label">本 卦</div><div class="ly-ben-bian-name-text">' + htmlEscape(benName) + '</div><div class="ly-ben-bian-trigrams"><span class="ly-trigram-badge">' + htmlEscape([data.upper_nature, data.upper_trigram].filter(Boolean).join(' ')) + '</span><span class="ly-trigram-badge">' + htmlEscape([data.lower_nature, data.lower_trigram].filter(Boolean).join(' ')) + '</span></div></div>'
  if (hasBian) html += '<div class="ly-ben-bian-top-arrow">→</div><div class="ly-ben-bian-name-block"><div class="ly-ben-bian-label">变 卦</div><div class="ly-ben-bian-name-text">' + htmlEscape(bianName) + '</div><div class="ly-ben-bian-trigrams"><span class="ly-trigram-badge">' + htmlEscape([data.bian_upper_nature, data.bian_upper_trigram].filter(Boolean).join(' ')) + '</span><span class="ly-trigram-badge">' + htmlEscape([data.bian_lower_nature, data.bian_lower_trigram].filter(Boolean).join(' ')) + '</span></div></div>'
  html += '</div><div class="ly-ben-bian-body">'
  for (let i = details.length - 1; i >= 0; i--) {
    const ben = details[i] || {}
    const bian = bianDetails[i] || null
    html += '<div class="ly-paired-row ' + (ben.is_moving ? 'moving' : '') + (bian ? ' has-bian' : ' has-ben-only') + '">'
    html += '<div class="ly-row-ben-side"><div class="ly-yao-tags-left">'
    if (ben.is_shi) html += '<span class="ly-tag ly-tag-shi">世</span>'
    if (ben.is_ying) html += '<span class="ly-tag ly-tag-ying">应</span>'
    if (ben.is_moving) html += '<span class="ly-tag ly-tag-moving">动</span>'
    html += '</div><div class="ly-paired-ben">' + renderYaoGraphic(!!ben.is_yang) + '</div><div class="ly-paired-info">'
    html += '<span class="ly-yao-pos">' + htmlEscape(ben.name || '') + '</span><span class="ly-tag ly-tag-liuqin">' + htmlEscape(ben.liuqin || ben.liu_qin || '') + '</span><span class="ly-tag ly-tag-liushen">' + htmlEscape(ben.liushen || ben.liu_shen || '') + '</span><span class="ly-tag ly-tag-naja">' + htmlEscape(ben.naja || ben.na_jia || '') + '</span></div></div>'
    if (bian) {
      html += '<div class="ly-row-divider"></div><div class="ly-row-bian-side"><div class="ly-yao-tags-left">' + (bian.yao_type === '变' ? '<span class="ly-tag ly-tag-bian">变</span>' : '') + '</div><div class="ly-paired-bian">' + renderYaoGraphic(!!bian.is_yang) + '</div><div class="ly-paired-bian-info"><span class="ly-tag ly-tag-liuqin">' + htmlEscape(bian.liuqin || bian.liu_qin || '') + '</span><span class="ly-tag ly-tag-liushen">' + htmlEscape(bian.liushen || bian.liu_shen || '') + '</span><span class="ly-tag ly-tag-naja">' + htmlEscape(bian.naja || bian.na_jia || '') + '</span></div></div>'
    }
    html += '</div>'
  }
  html += '</div><div class="ly-ben-bian-footer">'
  html += '<span class="ly-ben-bian-meta">宫：' + htmlEscape(data.palace_name || '') + '宫（' + htmlEscape(data.palace_element || '') + '）</span>'
  html += '<span class="ly-ben-bian-meta">日辰：' + htmlEscape(data.day_ganzhi || data.ri_chen || '') + '</span>'
  html += '<span class="ly-ben-bian-meta">月建：' + htmlEscape(data.month_ganzhi || data.yue_jian || '') + '</span>'
  html += '<span class="ly-ben-bian-meta">' + (movingCount ? ('动爻：' + movingCount + '个') : '静卦（无动爻）') + '</span>'
  html += '</div></div>'
  html += '<div class="ly-detail-table-wrap"><table class="ly-detail-table"><tr><th>爻位</th><th>阴阳</th><th>六亲</th><th>六神</th><th>纳甲</th><th>地支五行</th><th>世应</th><th>动</th></tr>'
  for (let i = details.length - 1; i >= 0; i--) {
    const x = details[i] || {}
    html += '<tr class="' + (x.is_moving ? 'moving-row' : '') + '"><td>' + htmlEscape(x.name || '') + '</td><td>' + (x.is_yang ? '⚊ 阳' : '⚋ 阴') + '</td><td>' + htmlEscape(x.liuqin || x.liu_qin || '') + '</td><td>' + htmlEscape(x.liushen || x.liu_shen || '') + '</td><td>' + htmlEscape(x.naja || x.na_jia || '') + '</td><td>' + htmlEscape(x.dizhi_element || '') + '</td><td>' + htmlEscape(x.is_shi ? '世' : x.is_ying ? '应' : '') + '</td><td>' + (x.is_moving ? '⚡ 动' : '') + '</td></tr>'
  }
  html += '</table></div>'
  html += '<div class="ly-paipan-meta"><span>🕐 ' + htmlEscape(data.timestamp || '') + '</span><span>📖 ' + htmlEscape(data.method || '自动摇卦') + '</span>' + (data.question ? '<span>❓ ' + htmlEscape(data.question) + '</span>' : '') + '</div></div>'
  return html
}

function renderZiweiArtifact(data) {
  const palaces = (data.twelve_palaces || data.palaces || []).slice(0, 12)
  const order = [4, 3, 5, 6, 2, 'center', 7, 1, 8, 0, 11, 10, 9]
  const starName = function(s) { return typeof s === 'string' ? s : ((s && s.name) || '') }
  const palaceCell = function(p, idx) {
    if (!p) return '<div class="zw-artifact-palace empty"></div>'
    const major = (p.major_stars || p.stars || []).slice(0, 5).map(starName).filter(Boolean)
    const minor = (p.minor_stars || []).slice(0, 8).map(starName).filter(Boolean)
    const adj = (p.adjective_stars || []).slice(0, 6).map(starName).filter(Boolean)
    const palaceName = p.name || p.palace_name || ''
    const dec = p.decadal || {}
    const decText = dec.range ? ('大限 ' + dec.range[0] + '-' + dec.range[1] + '岁 ' + ((dec.heavenly_stem || '') + (dec.earthly_branch || ''))) : (p.da_xian || '')
    const support = [p.changsheng12, p.boshi12, p.jiangqian12, p.suiqian12].filter(Boolean).join(' · ')
    const ages = (p.ages || []).slice(0, 8).join(',')
    return '<div class="zw-artifact-palace palace-' + idx + '"><div class="zw-artifact-top"><b>' + htmlEscape(palaceName) + '</b><span>' + htmlEscape(p.ganzhi || p.gan_zhi || ((p.heavenly_stem || '') + (p.earthly_branch || ''))) + '</span></div>' +
      '<div class="zw-artifact-stars major">' + major.map(function(s) { return '<span>' + htmlEscape(s) + '</span>' }).join('') + '</div>' +
      '<div class="zw-artifact-stars minor">' + minor.map(function(s) { return '<span>' + htmlEscape(s) + '</span>' }).join('') + '</div>' +
      '<div class="zw-artifact-stars adj">' + adj.map(function(s) { return '<span>' + htmlEscape(s) + '</span>' }).join('') + '</div>' +
      (support ? '<div class="zw-artifact-support">' + htmlEscape(support) + '</div>' : '') +
      '<div class="zw-artifact-foot"><span>' + htmlEscape(decText) + '</span><strong>' + htmlEscape((p.is_body_palace || p.body_palace) ? '身宫' : '') + '</strong></div>' +
      (ages ? '<div class="zw-artifact-ages">流年:' + htmlEscape(ages) + '</div>' : '') +
      '</div>'
  }
  const cells = order.map(function(idx) {
    if (idx === 'center') {
      const bi = data.basic_info || {}
      const cp = data.core_palace || {}
      const meta = data.display_meta || {}
      return '<div class="zw-artifact-center"><span class="zw-center-kicker">三合盘</span><b>紫微斗数命盘</b><span>' + htmlEscape([(meta.gender_yinyang || data.gender), bi.five_elements_class || data.wuxingju || data.five_element_class].filter(Boolean).join(' · ')) + '</span><em>北京时间 ' + htmlEscape(meta.beijing_time || bi.solar_date || data.birth_time || '') + '</em><em>真太阳时 ' + htmlEscape(meta.true_solar_time || '') + '</em><em>农历 ' + htmlEscape(bi.lunar_date || data.lunar_date || '') + '</em><em>节气四柱 ' + htmlEscape(bi.chinese_date || '') + '</em><em>' + htmlEscape([cp.soul_star && ('命主 ' + cp.soul_star), cp.body_star && ('身主 ' + cp.body_star)].filter(Boolean).join('  ')) + '</em></div>'
    }
    return palaceCell(palaces[idx], idx)
  }).join('')
  const timeline = palaces.filter(function(p) { return p && p.decadal && p.decadal.range }).map(function(p) {
    const r = p.decadal.range || []
    return '<span class="zw-flow-item"><b>' + htmlEscape(r[0] + '-' + r[1]) + '</b><em>' + htmlEscape((p.decadal.heavenly_stem || '') + (p.decadal.earthly_branch || '')) + '</em><i>' + htmlEscape(p.name || '') + '</i></span>'
  }).join('')
  return '<div class="zw-artifact-wrap"><div class="zw-orientation">正南方</div><div class="zw-artifact-grid">' + cells + '</div><div class="zw-orientation">正北方</div><div class="zw-flow-row"><div class="zw-flow-title">大限</div><div class="zw-flow-scroll">' + timeline + '</div></div></div>'
}

function renderTarotArtifact(data) {
  const icons = { 0: '🃏', 1: '🎩', 2: '🌙', 3: '👑', 4: '🏛️', 5: '⛪', 6: '💕', 7: '⚔️', 8: '🦁', 9: '🏔️', 10: '🎡', 11: '⚖️', 12: '🔄', 13: '🦋', 14: '🏺', 15: '⛓️', 16: '⚡', 17: '⭐', 18: '🌕', 19: '☀️', 20: '📯', 21: '🌍' }
  const suitIcons = { '权杖': '🔥', '圣杯': '💧', '宝剑': '🗡️', '星币': '🪙' }
  const cards = (data.cards || []).map(function(c, i) {
    const icon = c.type === 'major' ? (icons[c.id] || '🃏') : (suitIcons[c.suit] || '🃏')
    const orientationClass = c.is_reversed ? 'reversed' : 'upright'
    const keyword = c.is_reversed && c.keyword_reversed ? c.keyword_reversed : (c.keyword || '')
    return '<div class="tarot-card-slot" style="animation: tarotCardAppear 0.5s ' + (i * 0.12) + 's both">' +
      '<div class="tarot-card-flipper flipped">' +
        '<div class="tarot-card-back"><div class="tarot-card-back-pattern"></div><span class="tarot-card-back-symbol">✦</span></div>' +
        '<div class="tarot-card-front">' +
          '<div class="tarot-card-num">' + htmlEscape(c.type === 'major' ? ((c.id || 0) + 1) : (c.number || '')) + '</div>' +
          '<div class="tarot-card-icon">' + icon + '</div>' +
          '<div class="tarot-card-name">' + htmlEscape(c.name || '') + '</div>' +
          '<div class="tarot-card-name-en">' + htmlEscape(c.name_en || '') + '</div>' +
          '<div class="tarot-card-orientation ' + orientationClass + '">' + htmlEscape(c.orientation || '') + '</div>' +
          '<div class="tarot-card-keyword">' + htmlEscape(keyword) + '</div>' +
        '</div>' +
      '</div>' +
      '<div class="tarot-card-position"><div class="tarot-card-position-name">' + htmlEscape(c.position_name || c.position || '') + '</div><div class="tarot-card-position-meaning">' + htmlEscape(c.position_meaning || '') + '</div>' + (c.is_reversed ? '<div class="tarot-card-reversed-hint">逆位</div>' : '') + '</div>' +
    '</div>'
  }).join('')
  const count = (data.cards || []).length
  return '<div class="tarot-artifact-wrap"><div class="tarot-drawing-text">✦ 塔罗抽牌结果 ✦</div><div class="tarot-cards-display" data-count="' + htmlEscape(count) + '">' + cards + '</div></div>'
}

function renderZejiArtifact(data) {
  const days = (data.best_days || data.days || []).slice(0, 8).map(function(d) {
    return '<div class="artifact-line"><span>' + htmlEscape(d.date || '') + '</span><strong>' + htmlEscape((d.score || '') + ' ' + (d.jian_chu || d.zhi_shen || '')) + '</strong></div>'
  }).join('')
  return '<div class="artifact-panel"><div class="artifact-line-list">' + days + '</div></div>'
}

function renderArtifactHtml(artifact) {
  const data = artifact && artifact.data ? artifact.data : {}
  if (artifact.key === 'bazi.basic') return renderBaziBasicArtifact(data)
  if (artifact.key === 'bazi.yun') return renderBaziYunArtifact(data)
  if (artifact.key === 'qimen.pan') return renderQimenArtifact(data)
  if (artifact.key === 'liuyao.pan') return renderLiuyaoArtifact(data)
  if (artifact.key === 'meihua.pan') return renderMeihuaArtifact(data)
  if (artifact.key === 'ziwei.pan') return renderZiweiArtifact(data)
  if (artifact.key === 'tarot.cards') return renderTarotArtifact(data)
  if (artifact.key === 'zeji.days') return renderZejiArtifact(data)
  return '<div class="artifact-panel"><pre>' + htmlEscape(JSON.stringify(data, null, 2)) + '</pre></div>'
}

function toggleArtifact(messageIndex, artifactKey) {
  const msg = comprehensiveMessages.value[messageIndex]
  if (!msg || !msg.artifacts) return
  comprehensiveMessages.value[messageIndex] = Object.assign({}, msg, {
    artifacts: msg.artifacts.map(function(artifact) {
      return artifact.key === artifactKey ? Object.assign({}, artifact, { collapsed: !artifact.collapsed }) : artifact
    })
  })
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
  if (!autoSelectTools.value && !selectedToolModels.value.length) return uni.showToast({ title: '请至少选择一个术数模型', icon: 'none' })
  if (autoSelectTools.value && !comprehensiveMessages.value.length) {
    try {
      const rec = await uni.request({
        url: '/api/comprehensive/recommend-tools',
        method: 'POST',
        data: { question, llm_model: selectedLlmModel.value.id || 'basic', profile_count: Math.max(1, selectedProfiles.value.length) }
      })
      const d = rec.data || {}
      if (Array.isArray(d.tool_models) && d.tool_models.length) selectedToolModels.value = d.tool_models
    } catch (_) {}
  }
  if (currentPoints.value < estimatedCost.value) return uni.showToast({ title: '积分不足', icon: 'none' })

  const history = normalizeMessageHistory()
  comprehensiveLoading.value = true
  comprehensiveMessages.value.push({ role: 'user', content: question })
  const aiIndex = comprehensiveMessages.value.length
  comprehensiveMessages.value.push({ role: 'assistant', content: '', stage: '正在连接综合解读服务' })
  startComprehensiveProgressTimer(aiIndex)
  shouldAutoFollowChat.value = true
  scrollComprehensiveChatToBottom('smooth', true)
  const typeState = { queue: '', displayed: '', done: false }

  try {
    const requestBody = {
      question,
      profile_id: selectedProfiles.value.length === 1 && selectedProfiles.value[0].source === 'profile' ? selectedProfiles.value[0].id : undefined,
      profile: selectedProfiles.value.length === 1 ? comprehensiveProfilePayload(selectedProfiles.value[0]) : undefined,
      profiles: selectedProfiles.value.map(comprehensiveProfilePayload),
      llm_model: selectedLlmModel.value.id || 'basic',
      tool_models: selectedToolModels.value,
      auto_select_tools: autoSelectTools.value && !history.length,
      history,
      paipan: { paipan: currentPaipanContext.value, artifacts: currentArtifacts.value },
      reading_mode: readingMode.value,
      artifact_policy: 'auto',
      existing_artifact_keys: Object.keys(currentArtifacts.value || {}),
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
          if (data.tool_key) {
            appendArtifactAnalysis(aiIndex, data.tool_key, data.content)
          } else {
            typeState.queue += data.content
            startComprehensiveTypewriter(aiIndex, typeState)
          }
          stopComprehensiveProgressTimer()
        }
        if (data.conversation_id) currentComprehensiveConvId.value = data.conversation_id
        if (Array.isArray(data.tool_models) && data.tool_models.length) selectedToolModels.value = data.tool_models
        if (data.paipan) {
          currentPaipanContext.value = data.paipan
        }
        if (data.artifacts) {
          currentArtifacts.value = data.artifacts || {}
          updateComprehensiveAssistant(aiIndex, { artifacts: artifactListFromMap(currentArtifacts.value) })
        }
        if (typeof data.points_left === 'number') currentPoints.value = data.points_left
        if (typeof data.ai_single_credits === 'number') aiSingleCredits.value = data.ai_single_credits
        if (typeof data.ai_combo_credits === 'number') aiComboCredits.value = data.ai_combo_credits
        if (data.used_credit === 'daily_light') dailyLightAvailable.value = false
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
    currentArtifacts.value = data.artifacts || {}
    selectedToolModels.value = data.models && data.models.length ? data.models : ['bazi']
    const restoredArtifacts = artifactListFromMap(currentArtifacts.value)
    let attached = false
    comprehensiveMessages.value = (data.messages || []).map(function(m) {
      if (m && m.role === 'assistant' && m.content) {
        const next = Object.assign({}, m, { content: stripComprehensiveMarkdown(m.content) })
        if (!attached && restoredArtifacts.length) {
          next.artifacts = restoredArtifacts
          attached = true
        }
        return next
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
    shouldAutoFollowChat.value = true
    scrollComprehensiveChatToBottom('smooth', true)
  } catch (_) {}
}

function isComprehensiveChatNearBottom() {
  // #ifdef H5
  try {
    const el = document.querySelector('.home-ai-chat')
    if (!el) return true
    return el.scrollHeight - el.scrollTop - el.clientHeight < 96
  } catch(_) {
    return true
  }
  // #endif
  return true
}

function onHomeChatScroll() {
  shouldAutoFollowChat.value = isComprehensiveChatNearBottom()
}

function scrollComprehensiveChatToBottom(behavior, force) {
  if (!force && !shouldAutoFollowChat.value) return
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
  currentArtifacts.value = {}
  shouldAutoFollowChat.value = true
  pendingComprehensiveId = ''
  try { sessionStorage.removeItem('xc_comprehensive_resume_id') } catch(_) {}
  scrollComprehensiveChatToBottom('auto', true)
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
.profile-picker, .tool-picker, .reading-mode-picker, .llm-picker, .home-ai-send { min-height: 36px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.18); background: rgba(255,255,255,0.065); color: var(--text-1); display: flex; align-items: center; justify-content: center; cursor: pointer; box-sizing: border-box; flex-shrink: 0; transition: border-color .18s ease, background .18s ease, transform .18s ease; }
[data-theme="light"] .profile-picker, [data-theme="light"] .tool-picker, [data-theme="light"] .reading-mode-picker, [data-theme="light"] .llm-picker { background: rgba(255,251,242,0.76); }
.profile-picker:hover, .tool-picker:hover, .reading-mode-picker:hover, .llm-picker:hover { border-color: rgba(178,149,93,0.45); background: var(--accent-glow); }
.profile-picker, .tool-picker { justify-content: flex-start; gap: 6px; padding: 0 10px; max-width: 168px; min-width: 86px; flex-shrink: 1; }
.profile-plus, .tool-picker-icon { width: 20px; height: 20px; border-radius: 50%; background: var(--accent-glow); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; flex-shrink: 0; }
.profile-name, .tool-picker text:last-child { display: block; font-size: 0.75rem; color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile-meta { display: block; margin-top: 2px; font-size: 0.66rem; color: var(--text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.llm-picker { min-width: 96px; max-width: 128px; padding: 4px 10px; flex-direction: column; align-items: flex-start; gap: 1px; color: var(--text-2); white-space: nowrap; flex-shrink: 1; overflow: hidden; }
.reading-mode-picker { min-width: 82px; max-width: 96px; padding: 4px 10px; flex-direction: column; align-items: flex-start; gap: 1px; color: var(--text-2); white-space: nowrap; flex-shrink: 0; overflow: hidden; }
.reading-mode-label { display: block; width: 100%; overflow: hidden; text-overflow: ellipsis; font-size: 0.56rem; color: var(--text-3); line-height: 1.15; }
.reading-mode-name { display: block; width: 100%; overflow: hidden; text-overflow: ellipsis; font-size: 0.72rem; color: var(--text-1); line-height: 1.2; }
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
.home-tool-cards { display: grid; gap: 10px; margin: 10px 0 12px; }
.home-tool-card { border: 1px solid rgba(178,149,93,0.18); border-radius: 12px; background: rgba(178,149,93,0.055); overflow: hidden; }
.home-tool-card-head { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 10px 12px; cursor: pointer; }
.home-tool-card-title { display: block; color: var(--text-1); font-size: 0.84rem; font-weight: 700; }
.home-tool-card-sub { display: block; margin-top: 3px; color: var(--text-3); font-size: 0.68rem; line-height: 1.35; }
.home-tool-card-toggle { flex-shrink: 0; color: var(--accent); font-size: 0.68rem; }
.home-tool-card-body { padding: 0 12px 12px; }
.home-artifact-render { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.home-artifact-analysis { margin-top: 12px; padding: 12px 14px; border-radius: 12px; border: 1px solid rgba(178,149,93,.16); background: rgba(178,149,93,.055); color: var(--text-2); line-height: 1.8; white-space: pre-wrap; font-size: .84rem; }
.home-artifact-analysis-title { color: var(--accent); font-weight: 800; font-size: .78rem; margin-bottom: 6px; letter-spacing: 1px; }
.home-artifact-render :deep(.artifact-panel) { display: grid; gap: 10px; color: var(--text-2); font-size: 0.74rem; }
.home-artifact-render :deep(.artifact-grid) { display: grid; gap: 8px; }
.home-artifact-render :deep(.artifact-grid-4) { grid-template-columns: repeat(4, minmax(0, 1fr)); }
.home-artifact-render :deep(.artifact-grid-3) { grid-template-columns: repeat(3, minmax(0, 1fr)); }
.home-artifact-render :deep(.bazi-pillar),
.home-artifact-render :deep(.artifact-gua),
.home-artifact-render :deep(.artifact-tarot-card),
.home-artifact-render :deep(.artifact-kv),
.home-artifact-render :deep(.artifact-chip),
.home-artifact-render :deep(.artifact-line),
.home-artifact-render :deep(.artifact-palace),
.home-artifact-render :deep(.artifact-ziwei-palace) { min-width: 0; padding: 8px 9px; border: 1px solid rgba(178,149,93,0.13); border-radius: 10px; background: rgba(255,255,255,0.045); box-sizing: border-box; }
.home-artifact-render :deep(.bazi-pillar span),
.home-artifact-render :deep(.artifact-gua span),
.home-artifact-render :deep(.artifact-tarot-card span),
.home-artifact-render :deep(.artifact-kv span),
.home-artifact-render :deep(.artifact-chip span),
.home-artifact-render :deep(.artifact-line span),
.home-artifact-render :deep(.artifact-palace span),
.home-artifact-render :deep(.artifact-ziwei-palace span) { display: block; color: var(--text-3); font-size: 0.62rem; line-height: 1.25; overflow-wrap: anywhere; }
.home-artifact-render :deep(.bazi-pillar strong),
.home-artifact-render :deep(.artifact-gua strong),
.home-artifact-render :deep(.artifact-tarot-card strong),
.home-artifact-render :deep(.artifact-kv strong),
.home-artifact-render :deep(.artifact-chip strong),
.home-artifact-render :deep(.artifact-line strong),
.home-artifact-render :deep(.artifact-palace b),
.home-artifact-render :deep(.artifact-ziwei-palace b) { display: block; color: var(--text-1); font-size: 0.82rem; line-height: 1.35; margin-top: 3px; overflow-wrap: anywhere; }
.home-artifact-render :deep(.artifact-kv-grid) { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; }
.home-artifact-render :deep(.artifact-palace-grid) { display: grid; grid-template-columns: repeat(3, minmax(92px, 1fr)); border: 1px solid rgba(178,149,93,0.14); border-radius: 12px; overflow: hidden; }
.home-artifact-render :deep(.artifact-palace) { border-radius: 0; min-height: 68px; border-width: 0 1px 1px 0; }
.home-artifact-render :deep(.artifact-ziwei-grid) { display: grid; grid-template-columns: repeat(4, minmax(98px, 1fr)); gap: 6px; }
.home-artifact-render :deep(.artifact-ziwei-palace) { min-height: 82px; display: flex; flex-direction: column; gap: 3px; }
.home-artifact-render :deep(.artifact-chip-row) { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 2px; }
.home-artifact-render :deep(.artifact-chip) { min-width: 78px; flex: 0 0 auto; }
.home-artifact-render :deep(.artifact-row-title) { color: var(--accent); font-weight: 700; font-size: 0.72rem; margin-bottom: 6px; }
.home-artifact-render :deep(.artifact-line-list) { display: grid; gap: 6px; }
.home-artifact-render :deep(.artifact-line) { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.home-artifact-render :deep(.artifact-tarot-card em) { display: block; margin-top: 3px; color: var(--accent); font-style: normal; font-size: 0.62rem; }
.home-artifact-render :deep(.artifact-empty) { color: var(--text-3); font-size: 0.68rem; }

.home-artifact-render :deep(.bz-artifact-panel) { width: 100%; padding: 16px; border: 1px solid rgba(178,149,93,.16); border-radius: 14px; background: rgba(255,253,248,.05); box-sizing: border-box; }
.home-artifact-render :deep(.bz-artifact-head) { display: flex; align-items: flex-start; justify-content: space-between; gap: 12px; margin-bottom: 14px; padding-bottom: 10px; border-bottom: 1px solid rgba(178,149,93,.14); }
.home-artifact-render :deep(.bz-artifact-head b) { display: block; color: var(--text-1); font-family: var(--font-serif); font-size: 1rem; letter-spacing: 2px; }
.home-artifact-render :deep(.bz-artifact-head span),
.home-artifact-render :deep(.bz-artifact-head em) { display: block; margin-top: 4px; color: var(--text-3); font-size: .72rem; font-style: normal; }
.home-artifact-render :deep(.bz-artifact-pillars) { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
.home-artifact-render :deep(.bz-artifact-pillar) { min-width: 0; padding: 12px 10px; border: 1px solid rgba(178,149,93,.14); border-radius: 12px; text-align: center; background: rgba(255,255,255,.045); }
.home-artifact-render :deep(.bz-artifact-label) { display: block; color: var(--text-3); font-size: .68rem; margin-bottom: 8px; }
.home-artifact-render :deep(.bz-artifact-gz) { display: flex; align-items: center; justify-content: center; gap: 8px; }
.home-artifact-render :deep(.bz-artifact-gz b) { width: 34px; height: 34px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; color: #fff; font-size: 1rem; font-weight: 800; box-shadow: 0 6px 16px rgba(0,0,0,.12); }
.home-artifact-render :deep(.bz-artifact-sub) { display: block; min-height: 16px; margin-top: 7px; color: var(--text-3); font-size: .66rem; }
.home-artifact-render :deep(.bz-artifact-meta) { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-top: 12px; }
.home-artifact-render :deep(.bz-artifact-meta span) { padding: 8px 10px; border-radius: 10px; background: rgba(178,149,93,.06); color: var(--text-3); font-size: .68rem; }
.home-artifact-render :deep(.bz-artifact-meta b) { color: var(--text-1); font-size: .78rem; margin-left: 4px; }
.home-artifact-render :deep(.bz-wuxing-row) { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 12px; }
.home-artifact-render :deep(.bz-wuxing-chip) { padding: 4px 9px; border-radius: 999px; color: #fff; font-size: .68rem; font-weight: 700; }
.home-artifact-render :deep(.wx-color-jin) { background: #B8860B; }
.home-artifact-render :deep(.wx-color-mu) { background: #2E8B57; }
.home-artifact-render :deep(.wx-color-shui) { background: #2878B5; }
.home-artifact-render :deep(.wx-color-huo) { background: #C44D3A; }
.home-artifact-render :deep(.wx-color-tu) { background: #8A6A2A; }
.home-artifact-render :deep(.wx-text-jin) { color: #B8860B; }
.home-artifact-render :deep(.wx-text-mu) { color: #2E8B57; }
.home-artifact-render :deep(.wx-text-shui) { color: #2878B5; }
.home-artifact-render :deep(.wx-text-huo) { color: #C44D3A; }
.home-artifact-render :deep(.wx-text-tu) { color: #8A6A2A; }
.home-artifact-render :deep(.bz-yun-panel) { display: grid; gap: 10px; }
.home-artifact-render :deep(.bz-yun-section) { border: 1px solid var(--card-border); border-radius: 12px; overflow: hidden; background: rgba(255,255,255,.035); }
.home-artifact-render :deep(.bz-yun-title) { padding: 8px 12px; color: var(--accent); font-size: .74rem; font-weight: 800; background: var(--accent-glow); border-bottom: 1px solid var(--card-border); }
.home-artifact-render :deep(.bz-yun-scroll) { display: flex; flex-wrap: nowrap; overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
.home-artifact-render :deep(.bz-yun-scroll::-webkit-scrollbar) { display: none; }
.home-artifact-render :deep(.bz-yun-item) { flex: 0 0 auto; min-width: 58px; min-height: 72px; padding: 8px 6px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; border-right: 1px solid rgba(178,149,93,.10); box-sizing: border-box; }
.home-artifact-render :deep(.bz-yun-item:nth-child(3)) { background: rgba(178,149,93,.10); }
.home-artifact-render :deep(.bz-yun-year) { color: var(--text-3); font-size: .62rem; }
.home-artifact-render :deep(.bz-yun-age) { color: var(--text-3); font-size: .54rem; }
.home-artifact-render :deep(.bz-yun-gz) { display: flex; gap: 2px; font-family: var(--font-serif); font-size: .88rem; line-height: 1.1; }
.home-artifact-render :deep(.bz-yun-gz b) { font-weight: 800; }
.home-artifact-render :deep(.bz-yun-item em) { color: var(--text-3); font-size: .52rem; font-style: normal; }

/* 首页 artifact 直接承载单项页盘面结构，避免重新画一套黑字简化卡片 */
.home-artifact-render :deep(.mh-result-wrap),
.home-artifact-render :deep(.qm-result-wrap),
.home-artifact-render :deep(.ly-result-wrap) { width: 100%; color: var(--text-2); box-sizing: border-box; }
.home-artifact-render :deep(.mh-summary),
.home-artifact-render :deep(.qm-summary) { display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 0.8125rem; color: var(--text-2); padding: 12px 16px; background: rgba(255,255,255,0.035); border-radius: 10px; border: 1px solid var(--card-border); margin-bottom: 16px; }
.home-artifact-render :deep(.mh-summary b),
.home-artifact-render :deep(.qm-summary b) { color: var(--text-1); }
.home-artifact-render :deep(.gua-display) { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px; margin: 20px 0; }
.home-artifact-render :deep(.gua-card) { background: rgba(255,255,255,0.035); border: 1px solid var(--card-border); border-radius: 14px; padding: 18px 14px 14px; text-align: center; position: relative; transition: all .25s ease; box-sizing: border-box; }
.home-artifact-render :deep(.gua-card-name) { font-family: var(--font-serif); font-size: 1.25rem; font-weight: 700; color: var(--text-1); letter-spacing: 3px; margin-bottom: 12px; }
.home-artifact-render :deep(.gua-card-label) { font-size: .72rem; color: var(--text-3); letter-spacing: 2px; margin-bottom: 8px; }
.home-artifact-render :deep(.gua-card.ben-gua .gua-card-name) { color: var(--accent); }
.home-artifact-render :deep(.gua-card.hu-gua .gua-card-name) { color: #7C93C3; }
.home-artifact-render :deep(.gua-card.bian-gua .gua-card-name) { color: #E8A87C; }
.home-artifact-render :deep(.gua-yao-wrap) { display: flex; flex-direction: column; align-items: center; gap: 6px; margin: 0 auto; width: 120px; max-width: 120px; }
.home-artifact-render :deep(.gua-yao) { display: flex; justify-content: center; align-items: center; gap: 6px; height: 8px; width: 100%; position: relative; }
.home-artifact-render :deep(.gua-yao-line) { height: 6px; border-radius: 2px; background: var(--text-1); }
.home-artifact-render :deep(.gua-yao.yang .gua-yao-line) { width: 80%; }
.home-artifact-render :deep(.gua-yao.yin .gua-yao-line) { width: calc((80% - 6px) / 2); }
.home-artifact-render :deep(.gua-yao.dong-yao .gua-yao-line) { background: var(--accent); box-shadow: 0 0 8px rgba(178,149,93,.35); }
.home-artifact-render :deep(.gua-yao.dong-yao::after) { content: '○'; position: absolute; right: -14px; font-size: .625rem; color: var(--accent); font-weight: 700; }
.home-artifact-render :deep(.gua-trigram) { font-size: 2.2rem; line-height: 1; margin-bottom: 4px; opacity: .82; }
.home-artifact-render :deep(.gua-sub-info) { margin-top: 12px; font-size: .72rem; color: var(--text-3); line-height: 1.8; }
.home-artifact-render :deep(.gua-sub-info span) { display: inline-block; padding: 2px 8px; border-radius: 4px; margin: 2px; background: rgba(255,255,255,.05); }
.home-artifact-render :deep(.ti-yong-section) { background: rgba(255,255,255,.035); border: 1px solid var(--card-border); border-radius: 14px; padding: 18px; margin: 18px 0; }
.home-artifact-render :deep(.ti-yong-title) { font-family: var(--font-serif); font-size: 1rem; font-weight: 700; color: var(--text-1); letter-spacing: 2px; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--card-border); }
.home-artifact-render :deep(.ti-yong-grid) { display: grid; grid-template-columns: 1fr auto 1fr; gap: 16px; align-items: center; margin-bottom: 16px; }
.home-artifact-render :deep(.ti-yong-box) { text-align: center; padding: 16px 12px; border-radius: 12px; border: 1px solid var(--card-border); }
.home-artifact-render :deep(.ti-yong-box.ti) { background: rgba(110,195,135,.07); border-color: rgba(110,195,135,.20); }
.home-artifact-render :deep(.ti-yong-box.yong) { background: rgba(124,147,195,.07); border-color: rgba(124,147,195,.20); }
.home-artifact-render :deep(.ti-yong-label) { font-size: .72rem; color: var(--text-3); margin-bottom: 4px; letter-spacing: 1px; }
.home-artifact-render :deep(.ti-yong-gua) { font-family: var(--font-serif); font-size: 1.45rem; font-weight: 700; color: var(--text-1); }
.home-artifact-render :deep(.ti-yong-wx) { font-size: .8rem; color: var(--text-2); margin-top: 4px; }
.home-artifact-render :deep(.ti-yong-rel) { text-align: center; padding: 8px 16px; font-size: .84rem; font-weight: 700; border-radius: 8px; letter-spacing: 1px; white-space: nowrap; }
.home-artifact-render :deep(.ti-yong-rel.ji) { background: rgba(110,195,135,.12); color: var(--success); }
.home-artifact-render :deep(.ti-yong-rel.xiong) { background: rgba(215,125,110,.12); color: var(--danger); }
.home-artifact-render :deep(.ti-yong-rel.zhong) { background: rgba(255,255,255,.05); color: var(--text-2); }
.home-artifact-render :deep(.mh-analysis-table) { width: 100%; border-collapse: collapse; font-size: .78rem; }
.home-artifact-render :deep(.mh-analysis-table th) { text-align: left; padding: 10px 12px; color: var(--text-3); font-weight: 500; border-bottom: 1px solid var(--card-border); white-space: nowrap; }
.home-artifact-render :deep(.mh-analysis-table td) { padding: 10px 12px; color: var(--text-2); border-bottom: 1px solid var(--card-border); }
.home-artifact-render :deep(.mh-verdict) { margin-top: 16px; padding: 16px 20px; border-radius: 12px; border-left: 3px solid var(--accent); background: rgba(178,149,93,.055); font-size: .9rem; color: var(--text-2); line-height: 1.8; }
.home-artifact-render :deep(.wx-tag),
.home-artifact-render :deep(.ws-tag) { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: .72rem; font-weight: 600; }
.home-artifact-render :deep(.wx-tag.jin) { background: rgba(255,215,0,.12); color: #D4A017; }
.home-artifact-render :deep(.wx-tag.mu) { background: rgba(110,195,135,.12); color: #6EC387; }
.home-artifact-render :deep(.wx-tag.shui) { background: rgba(70,130,180,.12); color: #4682B4; }
.home-artifact-render :deep(.wx-tag.huo) { background: rgba(215,125,110,.12); color: #D77D6E; }
.home-artifact-render :deep(.wx-tag.tu) { background: rgba(160,140,100,.12); color: #A08C64; }
.home-artifact-render :deep(.ws-tag.wang) { background: rgba(110,195,135,.12); color: #6EC387; }
.home-artifact-render :deep(.ws-tag.xiang) { background: rgba(70,130,180,.12); color: #4682B4; }
.home-artifact-render :deep(.ws-tag.xiu) { background: rgba(255,255,255,.06); color: var(--text-3); }
.home-artifact-render :deep(.ws-tag.qiu) { background: rgba(215,125,110,.10); color: #D77D6E; }
.home-artifact-render :deep(.ws-tag.si) { background: rgba(160,140,100,.10); color: #A08C64; }

.home-artifact-render :deep(.qm-nine-grid) { display: grid; grid-template-columns: repeat(3, minmax(94px, 1fr)); gap: 2px; width: min(100%, 460px); margin: 0 auto; border: 2px solid rgba(184,176,160,.78); border-radius: 12px; overflow: hidden; background: #d5cfc2; box-shadow: 0 2px 12px rgba(0,0,0,.08); }
.home-artifact-render :deep(.qm-palace) { min-height: 112px; padding: 8px; background: rgba(255,253,248,.92); color: #222; display: flex; flex-direction: column; gap: 8px; box-sizing: border-box; }
.home-artifact-render :deep(.qm-palace.center) { justify-content: center; align-items: center; text-align: center; background: #f0ede5; }
.home-artifact-render :deep(.qm-center-title) { color: #8a6319; font-weight: 800; letter-spacing: 2px; font-size: .92rem; }
.home-artifact-render :deep(.qm-center-meta) { color: #6f6250; font-size: .66rem; line-height: 1.5; }
.home-artifact-render :deep(.qm-palace-head) { display: flex; align-items: center; justify-content: space-between; color: #6f6250; font-size: .68rem; }
.home-artifact-render :deep(.qm-palace-head b) { color: #8a6319; font-size: .8rem; }
.home-artifact-render :deep(.qm-star-row) { display: grid; grid-template-columns: repeat(3, 1fr); gap: 4px; align-items: center; font-size: .9rem; font-weight: 800; text-align: center; }
.home-artifact-render :deep(.qm-star.red) { color: #E74C3C; }
.home-artifact-render :deep(.qm-star.blue) { color: #2980B9; }
.home-artifact-render :deep(.qm-star.green) { color: #27AE60; }
.home-artifact-render :deep(.qm-info-row) { display: flex; justify-content: space-between; color: #444; font-size: .7rem; margin-top: auto; }

.home-artifact-render :deep(.ly-ben-bian-box) { border: 1px solid var(--card-border); border-radius: 14px; background: rgba(255,255,255,.035); padding: 16px; }
.home-artifact-render :deep(.ly-ben-bian-top) { display: grid; grid-template-columns: 1fr auto 1fr; gap: 10px; align-items: center; margin-bottom: 14px; }
.home-artifact-render :deep(.ly-ben-bian-name-block) { text-align: center; border: 1px solid rgba(178,149,93,.16); border-radius: 12px; padding: 10px; background: rgba(255,255,255,.035); }
.home-artifact-render :deep(.ly-ben-bian-label) { font-size: .66rem; color: var(--text-3); letter-spacing: 2px; }
.home-artifact-render :deep(.ly-ben-bian-name-text) { margin-top: 4px; font-family: var(--font-serif); font-size: 1.1rem; font-weight: 800; color: var(--accent); letter-spacing: 2px; }
.home-artifact-render :deep(.ly-ben-bian-top-arrow) { color: var(--accent); font-size: 1.2rem; font-weight: 800; }
.home-artifact-render :deep(.ly-ben-bian-body) { display: grid; gap: 7px; }
.home-artifact-render :deep(.ly-paired-row) { display: grid; grid-template-columns: minmax(0, 1fr) 1px minmax(0, 1fr); gap: 8px; align-items: center; padding: 8px; border-radius: 10px; background: rgba(255,255,255,.035); border: 1px solid rgba(178,149,93,.10); }
.home-artifact-render :deep(.ly-paired-row.has-ben-only) { grid-template-columns: minmax(0, 1fr); }
.home-artifact-render :deep(.ly-paired-row.moving) { background: rgba(215,125,110,.08); border-color: rgba(215,125,110,.22); }
.home-artifact-render :deep(.ly-row-ben-side),
.home-artifact-render :deep(.ly-row-bian-side) { display: grid; grid-template-columns: 42px 74px minmax(0, 1fr); gap: 8px; align-items: center; min-width: 0; }
.home-artifact-render :deep(.ly-row-divider) { width: 1px; align-self: stretch; background: rgba(178,149,93,.18); }
.home-artifact-render :deep(.ly-yao-tags-left) { display: flex; gap: 4px; justify-content: flex-start; flex-wrap: wrap; }
.home-artifact-render :deep(.ly-tag) { display: inline-flex; align-items: center; justify-content: center; min-height: 20px; padding: 1px 6px; border-radius: 6px; font-size: .65rem; line-height: 1; background: rgba(178,149,93,.10); color: var(--text-2); white-space: nowrap; }
.home-artifact-render :deep(.ly-tag-shi) { color: #fff; background: #8a6319; }
.home-artifact-render :deep(.ly-tag-ying) { color: #fff; background: #7C93C3; }
.home-artifact-render :deep(.ly-tag-moving) { color: #fff; background: #D77D6E; }
.home-artifact-render :deep(.ly-tag-bian) { color: #fff; background: #27AE60; }
.home-artifact-render :deep(.ly-tag-liuqin) { color: #8a6319; }
.home-artifact-render :deep(.ly-tag-liushen) { color: #2980B9; }
.home-artifact-render :deep(.ly-tag-naja) { color: #6d5a38; }
.home-artifact-render :deep(.ly-paired-ben),
.home-artifact-render :deep(.ly-paired-bian) { width: 74px; display: flex; align-items: center; justify-content: center; }
.home-artifact-render :deep(.ly-yang-bar) { width: 64px; height: 7px; border-radius: 3px; background: var(--text-1); }
.home-artifact-render :deep(.ly-yin-bars) { width: 64px; display: flex; gap: 12px; justify-content: center; }
.home-artifact-render :deep(.ly-yin-seg) { width: 26px; height: 7px; border-radius: 3px; background: var(--text-1); }
.home-artifact-render :deep(.ly-paired-info) { display: flex; gap: 5px; flex-wrap: wrap; align-items: center; min-width: 0; }
.home-artifact-render :deep(.ly-yao-pos) { color: var(--text-1); font-weight: 700; font-size: .72rem; }
.home-artifact-render :deep(.ly-meta-row) { margin-top: 12px; padding-top: 10px; border-top: 1px solid var(--card-border); color: var(--text-3); font-size: .72rem; }
.home-artifact-render :deep(.ly-ben-bian-footer) { display: flex; align-items: center; justify-content: center; gap: 12px; flex-wrap: wrap; padding-top: 10px; margin-top: 10px; border-top: 1px solid var(--card-border); color: var(--text-3); font-size: .72rem; }
.home-artifact-render :deep(.ly-detail-table-wrap) { overflow-x: auto; margin-top: 12px; }
.home-artifact-render :deep(.ly-detail-table) { width: 100%; border-collapse: collapse; font-size: .72rem; }
.home-artifact-render :deep(.ly-detail-table th) { padding: 8px 6px; color: var(--text-3); font-weight: 600; border-bottom: 1px solid var(--card-border); white-space: nowrap; }
.home-artifact-render :deep(.ly-detail-table td) { padding: 8px 6px; color: var(--text-2); border-bottom: 1px solid rgba(178,149,93,.10); text-align: center; white-space: nowrap; }
.home-artifact-render :deep(.ly-detail-table .moving-row td) { color: var(--danger); }
.home-artifact-render :deep(.ly-paipan-meta) { display: flex; align-items: center; justify-content: center; flex-wrap: wrap; gap: 12px; margin-top: 12px; padding: 12px; border-radius: 10px; background: rgba(255,255,255,.035); color: var(--text-3); font-size: .72rem; }

.home-artifact-render :deep(.zw-artifact-wrap) { width: 100%; overflow-x: auto; }
.home-artifact-render :deep(.zw-artifact-grid) { min-width: 620px; display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); grid-template-rows: repeat(4, minmax(128px, auto)); gap: 2px; background: rgba(178,149,93,.20); border: 1px solid rgba(178,149,93,.22); border-radius: 12px; overflow: hidden; position: relative; }
.home-artifact-render :deep(.zw-artifact-palace) { min-height: 112px; padding: 8px; background: rgba(255,253,248,.92); color: #222; display: flex; flex-direction: column; gap: 6px; box-sizing: border-box; }
.home-artifact-render :deep(.zw-artifact-palace:nth-child(odd)) { background: rgba(255,247,242,.95); }
.home-artifact-render :deep(.zw-artifact-top) { display: flex; align-items: center; justify-content: space-between; color: #8a6319; font-size: .68rem; }
.home-artifact-render :deep(.zw-artifact-top b) { color: #B84D4D; font-size: .76rem; }
.home-artifact-render :deep(.zw-artifact-stars) { display: flex; flex-wrap: wrap; gap: 3px 6px; align-content: flex-start; }
.home-artifact-render :deep(.zw-artifact-stars.major span) { color: #b66b2d; font-size: .82rem; font-weight: 800; }
.home-artifact-render :deep(.zw-artifact-stars.minor span) { color: #2b89c9; font-size: .72rem; font-weight: 700; }
.home-artifact-render :deep(.zw-artifact-stars.adj span) { color: #6f6250; font-size: .64rem; font-weight: 500; }
.home-artifact-render :deep(.zw-artifact-support),
.home-artifact-render :deep(.zw-artifact-ages) { color: #7c7163; font-size: .58rem; line-height: 1.35; }
.home-artifact-render :deep(.zw-artifact-foot) { margin-top: auto; display: flex; align-items: flex-end; justify-content: space-between; gap: 6px; color: #6f6250; font-size: .62rem; }
.home-artifact-render :deep(.zw-artifact-foot strong) { color: #B84D4D; font-size: .68rem; }
.home-artifact-render :deep(.zw-artifact-center) { grid-column: 2 / 4; grid-row: 2 / 4; background: rgba(255,255,255,.96); display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8px; text-align: center; color: #4a3922; padding: 16px; box-sizing: border-box; }
.home-artifact-render :deep(.zw-artifact-center b) { font-family: var(--font-serif); color: #8a6319; font-size: 1.05rem; letter-spacing: 2px; }
.home-artifact-render :deep(.zw-artifact-center span),
.home-artifact-render :deep(.zw-artifact-center em) { color: #6f6250; font-size: .72rem; font-style: normal; }
.home-artifact-render :deep(.zw-orientation) { min-width: 620px; text-align: center; color: var(--text-3); font-size: .72rem; margin: 4px 0; }
.home-artifact-render :deep(.zw-flow-row) { min-width: 620px; display: grid; grid-template-columns: 54px minmax(0, 1fr); gap: 8px; margin-top: 8px; }
.home-artifact-render :deep(.zw-flow-title) { display: flex; align-items: center; justify-content: center; border-radius: 8px; background: var(--accent-glow); color: var(--accent); font-size: .7rem; font-weight: 800; }
.home-artifact-render :deep(.zw-flow-scroll) { display: flex; overflow-x: auto; scrollbar-width: none; }
.home-artifact-render :deep(.zw-flow-scroll::-webkit-scrollbar) { display: none; }
.home-artifact-render :deep(.zw-flow-item) { flex: 0 0 62px; min-height: 54px; padding: 6px 4px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px; border-right: 1px solid rgba(178,149,93,.10); background: rgba(255,255,255,.035); }
.home-artifact-render :deep(.zw-flow-item b) { color: var(--text-1); font-size: .66rem; }
.home-artifact-render :deep(.zw-flow-item em),
.home-artifact-render :deep(.zw-flow-item i) { color: var(--text-3); font-size: .54rem; font-style: normal; }

.home-artifact-render :deep(.tarot-artifact-wrap) { width: 100%; padding: 14px 0 4px; }
.home-artifact-render :deep(.tarot-drawing-text) { text-align: center; color: var(--accent); font-family: var(--font-serif); font-size: 1rem; font-weight: 800; letter-spacing: 2px; margin-bottom: 16px; }
.home-artifact-render :deep(.tarot-cards-display) { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; margin: 0 auto 12px; justify-items: center; }
.home-artifact-render :deep(.tarot-cards-display[data-count="1"]) { grid-template-columns: 1fr; max-width: 200px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="3"]) { grid-template-columns: repeat(3, 1fr); max-width: 560px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="5"]) { grid-template-columns: repeat(3, 1fr); max-width: 560px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="6"]) { grid-template-columns: repeat(3, 1fr); max-width: 560px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="7"]) { grid-template-columns: repeat(4, 1fr); max-width: 720px; }
.home-artifact-render :deep(.tarot-cards-display[data-count="10"]) { grid-template-columns: repeat(5, 1fr); max-width: 880px; }
.home-artifact-render :deep(.tarot-card-slot) { width: 100%; max-width: 148px; perspective: 600px; }
.home-artifact-render :deep(.tarot-card-flipper) { position: relative; width: 100%; height: 238px; transform-style: preserve-3d; transform: rotateY(180deg); }
.home-artifact-render :deep(.tarot-card-front),
.home-artifact-render :deep(.tarot-card-back) { position: absolute; inset: 0; border-radius: 12px; backface-visibility: hidden; overflow: hidden; box-sizing: border-box; }
.home-artifact-render :deep(.tarot-card-back) { background: linear-gradient(135deg, rgba(31,29,24,.95), rgba(65,48,22,.92)); border: 2px solid var(--accent); display: flex; align-items: center; justify-content: center; }
.home-artifact-render :deep(.tarot-card-back-pattern) { position: absolute; inset: 8px; border: 1px solid rgba(201,162,60,.25); border-radius: 8px; }
.home-artifact-render :deep(.tarot-card-back-symbol) { font-size: 3rem; color: var(--accent); opacity: .65; }
.home-artifact-render :deep(.tarot-card-front) { transform: rotateY(180deg); background: rgba(255,253,248,.96); border: 2px solid var(--accent); display: flex; flex-direction: column; align-items: center; padding: 14px 9px; color: #2e2a24; }
.home-artifact-render :deep(.tarot-card-num) { font-size: .68rem; color: #8d806d; margin-bottom: 4px; }
.home-artifact-render :deep(.tarot-card-icon) { font-size: 2.05rem; margin-bottom: 6px; line-height: 1; }
.home-artifact-render :deep(.tarot-card-name) { font-weight: 800; font-size: .9rem; color: #2e2a24; text-align: center; margin-bottom: 2px; letter-spacing: 1px; }
.home-artifact-render :deep(.tarot-card-name-en) { font-size: .58rem; color: #8d806d; text-align: center; margin-bottom: 6px; }
.home-artifact-render :deep(.tarot-card-orientation) { font-size: .72rem; padding: 2px 8px; border-radius: 8px; margin-bottom: 6px; font-weight: 700; }
.home-artifact-render :deep(.tarot-card-orientation.upright) { color: #5b8c5a; background: rgba(91,140,90,.12); border: 1px solid rgba(91,140,90,.3); }
.home-artifact-render :deep(.tarot-card-orientation.reversed) { color: #c0392b; background: rgba(192,57,43,.12); border: 1px solid rgba(192,57,43,.3); }
.home-artifact-render :deep(.tarot-card-keyword) { font-size: .66rem; color: #6f6250; text-align: center; line-height: 1.45; }
.home-artifact-render :deep(.tarot-card-position) { text-align: center; margin-top: 10px; }
.home-artifact-render :deep(.tarot-card-position-name) { font-weight: 800; font-size: .8rem; color: var(--accent); letter-spacing: 1px; }
.home-artifact-render :deep(.tarot-card-position-meaning) { font-size: .66rem; color: var(--text-4); margin-top: 2px; }
.home-artifact-render :deep(.tarot-card-reversed-hint) { font-size: .62rem; color: #c0392b; margin-top: 2px; }
.mini-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); border: 1px solid rgba(178,149,93,0.14); border-radius: 10px; overflow: hidden; }
.mini-palace { min-height: 64px; padding: 7px; border-right: 1px solid rgba(178,149,93,0.12); border-bottom: 1px solid rgba(178,149,93,0.12); display: flex; flex-direction: column; gap: 2px; color: var(--text-3); font-size: 0.62rem; box-sizing: border-box; }
.mini-palace:nth-child(3n) { border-right: none; }
.mini-palace:nth-last-child(-n+3) { border-bottom: none; }
.mini-palace-name { color: var(--accent); font-size: 0.68rem; font-weight: 700; }
.mini-list { display: grid; gap: 6px; }
.mini-line { display: flex; align-items: center; justify-content: space-between; gap: 10px; padding: 7px 9px; border-radius: 9px; background: rgba(255,255,255,0.045); color: var(--text-2); font-size: 0.68rem; }
.mini-gua-row, .mini-tarot-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 8px; }
.mini-gua, .mini-tarot { min-width: 0; padding: 9px; border-radius: 10px; background: rgba(255,255,255,0.045); border: 1px solid rgba(178,149,93,0.12); }
.mini-gua-label, .mini-tarot-pos { display: block; color: var(--text-3); font-size: 0.62rem; margin-bottom: 4px; }
.mini-gua-name, .mini-tarot-name { display: block; color: var(--text-1); font-size: 0.76rem; font-weight: 700; line-height: 1.35; }

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
  .profile-picker, .tool-picker, .reading-mode-picker, .llm-picker, .home-ai-send { min-height: 32px; }
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
  .home-ai-console.has-chat .home-ai-chat { height: auto; min-height: 0; max-height: calc(100dvh - 244px); }
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
  .reading-mode-picker { min-width: 58px; max-width: 64px; padding: 3px 6px; min-height: 30px; }
  .reading-mode-label { display: none; }
  .reading-mode-name { font-size: 0.64rem; }
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
  .home-tool-card-head { padding: 9px 10px; }
  .home-artifact-render :deep(.artifact-grid-4),
  .home-artifact-render :deep(.artifact-grid-3),
  .home-artifact-render :deep(.artifact-kv-grid) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .home-artifact-render :deep(.artifact-ziwei-grid) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .home-artifact-render :deep(.bz-artifact-pillars),
  .home-artifact-render :deep(.bz-artifact-meta) { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .home-artifact-render :deep(.bz-artifact-head) { flex-direction: column; }
  .home-artifact-render :deep(.zw-artifact-grid) { min-width: 560px; }
  .home-artifact-render :deep(.gua-display) { grid-template-columns: 1fr; gap: 12px; }
  .home-artifact-render :deep(.ti-yong-grid) { grid-template-columns: 1fr; gap: 8px; }
  .home-artifact-render :deep(.ti-yong-rel) { white-space: normal; }
  .home-artifact-render :deep(.qm-nine-grid) { grid-template-columns: repeat(3, minmax(82px, 1fr)); }
  .home-artifact-render :deep(.qm-palace) { min-height: 96px; padding: 6px; }
  .home-artifact-render :deep(.qm-star-row) { font-size: .76rem; }
  .home-artifact-render :deep(.ly-ben-bian-box) { padding: 12px; }
  .home-artifact-render :deep(.ly-row-ben-side),
  .home-artifact-render :deep(.ly-row-bian-side) { grid-template-columns: 34px 62px minmax(0, 1fr); gap: 6px; }
  .home-artifact-render :deep(.ly-paired-ben),
  .home-artifact-render :deep(.ly-paired-bian) { width: 62px; }
  .home-artifact-render :deep(.ly-yang-bar),
  .home-artifact-render :deep(.ly-yin-bars) { width: 54px; }
  .home-artifact-render :deep(.ly-yin-seg) { width: 22px; }
  .home-artifact-render :deep(.tarot-card-slot) { max-width: 122px; }
  .home-artifact-render :deep(.tarot-card-flipper) { height: 198px; }
  .home-artifact-render :deep(.tarot-cards-display[data-count="6"]) { grid-template-columns: repeat(3, 1fr); max-width: 420px; }
  .home-artifact-render :deep(.tarot-cards-display[data-count="7"]) { grid-template-columns: repeat(4, 1fr); max-width: 560px; }
  .home-artifact-render :deep(.tarot-cards-display[data-count="10"]) { grid-template-columns: repeat(5, 1fr); max-width: 680px; }
  .mini-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .mini-palace:nth-child(3n) { border-right: 1px solid rgba(178,149,93,0.12); }
  .mini-palace:nth-child(2n) { border-right: none; }
  .mini-palace:nth-last-child(-n+3) { border-bottom: 1px solid rgba(178,149,93,0.12); }
  .mini-gua-row, .mini-tarot-row { grid-template-columns: 1fr; }
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
  .home-ai-console.has-chat .home-ai-chat { height: auto; min-height: 0; max-height: calc(100dvh - 228px); padding: 10px; }
  .home-ai-main { padding: 10px; gap: 6px; border-radius: 16px; }
  .home-ai-input { min-height: 68px; font-size: 0.86rem; padding: 8px 4px 2px; }
  .home-ai-toolbar { gap: 3px; flex-wrap: nowrap !important; overflow-x: hidden; box-sizing: border-box; }
  .home-ai-toolbar-left, .home-ai-toolbar-right { gap: 3px; }
  .home-ai-toolbar-right { overflow-x: hidden; box-sizing: border-box; }
  .profile-picker, .tool-picker { max-width: 72px; padding: 0 4px; min-height: 28px; }
  .profile-plus, .tool-picker-icon { width: 16px; height: 16px; font-size: 0.66rem; }
  .profile-name, .tool-picker text:last-child { font-size: 0.6rem; }
  .reading-mode-picker { min-width: 48px; max-width: 52px; padding: 2px 5px; min-height: 28px; }
  .reading-mode-name { font-size: 0.58rem; }
  .llm-picker { min-width: 76px; max-width: 82px; padding: 2px 6px; min-height: 28px; }
  .llm-name { font-size: 0.58rem; }
  .llm-points { font-size: 0.48rem; }
  .home-ai-send { width: 26px; height: 26px; min-height: 26px; font-size: 0.9rem; }
  .home-ai-chat-head { margin: -2px 0 10px; border-radius: 12px; }
  .home-ai-chat-title { font-size: 0.8rem; }
  .home-ai-chat-sub { max-width: calc(100vw - 136px); font-size: 0.6rem; }
  .home-ai-stage-note { font-size: 0.6rem; }
  .home-ai-step-row text { font-size: 0.5rem; }
  .home-tool-card-title { font-size: 0.78rem; }
  .home-tool-card-sub { font-size: 0.62rem; }
  .home-artifact-render :deep(.artifact-grid-4),
  .home-artifact-render :deep(.artifact-grid-3),
  .home-artifact-render :deep(.artifact-kv-grid),
  .home-artifact-render :deep(.artifact-ziwei-grid) { grid-template-columns: 1fr; }
  .home-artifact-render :deep(.bz-artifact-panel) { padding: 12px; }
  .home-artifact-render :deep(.bz-artifact-pillars),
  .home-artifact-render :deep(.bz-artifact-meta) { grid-template-columns: 1fr 1fr; gap: 7px; }
  .home-artifact-render :deep(.bz-artifact-gz b) { width: 30px; height: 30px; font-size: .9rem; }
  .home-artifact-render :deep(.zw-artifact-grid) { min-width: 520px; grid-template-rows: repeat(4, minmax(100px, auto)); }
  .home-artifact-render :deep(.zw-artifact-palace) { min-height: 100px; padding: 6px; }
  .home-artifact-render :deep(.qm-nine-grid) { grid-template-columns: repeat(3, minmax(76px, 1fr)); }
  .home-artifact-render :deep(.qm-palace) { min-height: 88px; padding: 5px; }
  .home-artifact-render :deep(.qm-palace-head) { font-size: .56rem; }
  .home-artifact-render :deep(.qm-palace-head b) { font-size: .66rem; }
  .home-artifact-render :deep(.qm-star-row) { font-size: .68rem; gap: 2px; }
  .home-artifact-render :deep(.qm-info-row) { font-size: .58rem; }
  .home-artifact-render :deep(.ly-ben-bian-top) { grid-template-columns: 1fr; }
  .home-artifact-render :deep(.ly-ben-bian-top-arrow) { transform: rotate(90deg); text-align: center; }
  .home-artifact-render :deep(.ly-paired-row),
  .home-artifact-render :deep(.ly-paired-row.has-bian) { grid-template-columns: 1fr; }
  .home-artifact-render :deep(.ly-row-divider) { width: 100%; height: 1px; }
  .home-artifact-render :deep(.ly-row-ben-side),
  .home-artifact-render :deep(.ly-row-bian-side) { grid-template-columns: 32px 58px minmax(0, 1fr); }
  .home-artifact-render :deep(.tarot-cards-display),
  .home-artifact-render :deep(.tarot-cards-display[data-count="3"]),
  .home-artifact-render :deep(.tarot-cards-display[data-count="5"]),
  .home-artifact-render :deep(.tarot-cards-display[data-count="6"]) { grid-template-columns: repeat(2, 1fr); max-width: 260px; gap: 12px; }
  .home-artifact-render :deep(.tarot-cards-display[data-count="7"]),
  .home-artifact-render :deep(.tarot-cards-display[data-count="10"]) { grid-template-columns: repeat(3, 1fr); max-width: 390px; gap: 10px; }
  .home-artifact-render :deep(.tarot-card-slot) { max-width: 112px; }
  .home-artifact-render :deep(.tarot-card-flipper) { height: 184px; }
  .home-artifact-render :deep(.tarot-card-name) { font-size: .78rem; }
  .home-artifact-render :deep(.tarot-card-icon) { font-size: 1.7rem; }
  .mini-line { align-items: flex-start; flex-direction: column; gap: 3px; }
  .section { padding: 32px 16px; }
  .section-title { font-size: 1.15rem; }
  .section-desc { font-size: 0.75rem; }
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .footer-col:nth-child(3) { grid-column: 1 / -1; }
  .site-footer { padding: 32px 16px 24px; margin-top: 0; }
  .footer-bottom { flex-direction: column; gap: 8px; text-align: center; }
}
</style>
