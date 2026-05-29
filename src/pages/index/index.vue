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
      <section class="hero-home">
        <view class="hero-home-content">
          <!-- LOGO 和品牌 -->
          <view class="hero-brand">
            <view class="hero-brand-icon-wrap"><img class="hero-brand-icon" src="/static/images/logo.webp?v=2" alt="时安解忧屋" /></view>
            <view class="hero-brand-name">时安解忧屋</view>
            <view class="hero-brand-divider"></view>
            <view class="hero-brand-slogan">八字定终身格局 · 奇门断当下决策</view>
            <view class="hero-brand-sub">看得懂用得上的民俗命理参考平台</view>
          </view>

          <view class="home-ai-console">
            <view class="home-ai-main">
              <view class="profile-picker" @tap="openProfilePicker">
                <text class="profile-plus">＋</text>
                <view class="profile-picked">
                  <text class="profile-name">{{ selectedProfileName || '选择命盘' }}</text>
                  <text class="profile-meta">{{ selectedProfileMeta || '全部 / 客户 / 用户' }}</text>
                </view>
              </view>
              <textarea
                class="home-ai-input"
                v-model="comprehensiveQuestion"
                auto-height
                maxlength="800"
                placeholder="输入你的问题，选择术数模型后开始综合解读..."
              />
              <picker :range="llmModelNames" :value="llmModelIdx" @change="onLlmModelChange">
                <view class="llm-picker">{{ selectedLlmModel.name || '免费模型' }}</view>
              </picker>
              <view class="home-ai-send" :class="{ disabled: comprehensiveLoading }" @tap="startComprehensiveAsk">
                {{ comprehensiveLoading ? '生成中' : '发送' }}
              </view>
            </view>

            <view class="tool-model-row">
              <view
                class="tool-model-chip"
                v-for="tool in toolModels"
                :key="tool.id"
                :class="{ active: selectedToolModels.includes(tool.id) }"
                @tap="toggleToolModel(tool.id)"
              >{{ tool.name }}</view>
            </view>
            <view class="points-hint">预计消耗 {{ estimatedCost }} 积分 · 当前 {{ currentPoints }} 积分</view>

            <view class="home-ai-chat" v-if="comprehensiveMessages.length">
              <view
                v-for="(msg, idx) in comprehensiveMessages"
                :key="idx"
                class="home-ai-message"
                :class="msg.role === 'user' ? 'user' : 'assistant'"
              >
                <text class="home-ai-role">{{ msg.role === 'user' ? '你' : '时安综合 AI' }}</text>
                <text class="home-ai-stage" v-if="msg.stage">{{ msg.stage }}</text>
                <text class="home-ai-content" v-if="msg.content">{{ msg.content }}</text>
              </view>
            </view>
          </view>
        </view>

        <!-- 滚动提示 -->
        <view class="scroll-hint">
          <view class="scroll-arrow">↓</view>
        </view>
      </section>

      <!-- ═══ 页脚 ═══ -->
      <view class="site-footer">
        <view class="footer-disclaimer">
          ⚠️ 本站所有内容仅为民俗文化与传统命理科普参考，不构成任何决策建议，严禁利用本站内容从事封建迷信及违法违规活动，本站不对任何用户基于本站内容做出的决策承担任何责任
        </view>
        <view class="footer-grid">
          <view class="footer-col">
            <view class="footer-col-title">平台信息</view>
            <navigator url="/package-info/about/index">关于我们</navigator>
            <view class="footer-link" @tap="showFooterInfo('contact')">联系方式</view>
            <view class="footer-link" @tap="showFooterInfo('terms')">用户协议</view>
            <view class="footer-link" @tap="showFooterInfo('privacy')">隐私政策</view>
            <view class="footer-link" @tap="showFooterInfo('disclaimer')">完整免责声明</view>
          </view>
          <view class="footer-col">
            <view class="footer-col-title">快捷导航</view>
            <view @tap="goToPage('/pages/qimen/index')">奇门遁甲</view>
            <view @tap="goToPage('/pages/bazi-index/index')">八字排盘</view>
            <view @tap="goToPage('/pages/calendar/index')">专属日历</view>
            <view @tap="goToPage('/pages/community/index')">社区</view>
            <navigator url="/package-info/about/index">关于我们</navigator>
          </view>
          <view class="footer-col">
            <view class="footer-col-title">备案与版权</view>
            <view class="footer-icp">ICP备案号：京ICP备2026050601号-1</view>
            <view class="footer-link" @tap="showFooterInfo('copyright')">版权信息</view>
            <view class="footer-icp">© 2026 时安解忧屋 版权所有</view>
          </view>
        </view>
        <view class="footer-bottom">
          <text class="footer-bottom-text">时安解忧屋 · 看得懂用得上的民俗命理参考平台</text>
          <view class="btn-clear-data" @tap="clearAllData">🗑️ 一键清空所有数据</view>
        </view>
      </view>

    </view><!-- page-wrap -->

    <view class="profile-sheet" v-if="profileSheetOpen">
      <view class="profile-sheet-mask" @tap="profileSheetOpen = false"></view>
      <view class="profile-sheet-panel">
        <view class="profile-sheet-head">
          <text class="profile-sheet-title">选择命盘</text>
          <text class="profile-sheet-close" @tap="profileSheetOpen = false">×</text>
        </view>
        <view class="profile-tabs">
          <view v-for="tab in profileTabs" :key="tab" :class="{ active: profileTab === tab }" @tap="profileTab = tab">{{ tab }}</view>
        </view>
        <view class="profile-options">
          <view v-if="profileGroups[profileTab].length === 0" class="profile-empty">暂无命盘档案</view>
          <view class="profile-option" v-for="p in profileGroups[profileTab]" :key="p.id" @tap="selectProfile(p)">
            <view>
              <text class="profile-option-name">{{ p.name || '未命名' }}</text>
              <text class="profile-option-meta">{{ p.gender }} · {{ formatBirthTime(p.birthTime || p.birth_time) }}</text>
            </view>
            <text class="profile-option-type">{{ profileTypeLabel(p.profileType || p.profile_type) }}</text>
          </view>
        </view>
      </view>
    </view>

  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
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
const selectedProfile = ref(null)
const profileSheetOpen = ref(false)
const profileTab = ref('全部')
const profileTabs = ['全部', '客户', '用户']
const llmModels = ref([{ id: 'free', name: '免费模型', strength: '基础', cost_base: 0, cost_per_tool: 0, followup_cost: 0 }])
const toolModels = ref([{ id: 'bazi', name: '八字', cost: 1 }, { id: 'ziwei', name: '紫微斗数', cost: 1 }])
const llmModelIdx = ref(0)
const selectedToolModels = ref(['bazi'])
const currentPoints = ref(0)
const comprehensiveMessages = ref([])
const currentComprehensiveConvId = ref(null)
const currentPaipanContext = ref({})
let pendingComprehensiveId = ''

const selectedLlmModel = computed(() => llmModels.value[llmModelIdx.value] || llmModels.value[0] || {})
const llmModelNames = computed(() => llmModels.value.map(m => m.name + ' · ' + (m.strength || '基础')))
const estimatedCost = computed(() => {
  if (comprehensiveMessages.value.length > 0) return selectedLlmModel.value.followup_cost || 0
  return (selectedLlmModel.value.cost_base || 0) + selectedToolModels.value.length * (selectedLlmModel.value.cost_per_tool || 0)
})
const selectedProfileName = computed(() => selectedProfile.value ? selectedProfile.value.name : '')
const selectedProfileMeta = computed(() => {
  const p = selectedProfile.value
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
    return
  }
  profileSheetOpen.value = true
  loadProfiles()
}

function selectProfile(p) {
  selectedProfile.value = p
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
    const res = await uni.request({ url: '/api/profiles?sort=last_used' })
    const data = res.data || {}
    profiles.value = data.profiles || []
    if (!selectedProfile.value && profiles.value.length) {
      selectedProfile.value = profiles.value.find(p => p.isDefault) || profiles.value[0]
    }
  } catch (_) {
    profiles.value = []
  }
}

function normalizeMessageHistory() {
  return comprehensiveMessages.value
    .filter(m => m && (m.role === 'user' || m.role === 'assistant') && m.content)
    .map(m => ({ role: m.role, content: m.content }))
}

async function startComprehensiveAsk() {
  if (comprehensiveLoading.value) return
  if (!isLoggedIn.value) return uni.showToast({ title: '请先登录', icon: 'none' })
  const question = comprehensiveQuestion.value.trim()
  if (!question) return uni.showToast({ title: '请输入问题', icon: 'none' })
  if (!selectedProfile.value) return uni.showToast({ title: '请先选择命盘', icon: 'none' })
  if (!selectedToolModels.value.length) return uni.showToast({ title: '请至少选择一个术数模型', icon: 'none' })
  if (currentPoints.value < estimatedCost.value) return uni.showToast({ title: '积分不足', icon: 'none' })

  const history = normalizeMessageHistory()
  comprehensiveLoading.value = true
  comprehensiveMessages.value.push({ role: 'user', content: question })
  const aiMsg = { role: 'assistant', content: '', stage: '正在读取命盘档案...' }
  comprehensiveMessages.value.push(aiMsg)

  try {
    const resp = await fetch('/api/comprehensive/ask/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        profile_id: selectedProfile.value.id,
        llm_model: selectedLlmModel.value.id || 'free',
        tool_models: selectedToolModels.value,
        history,
        paipan: currentPaipanContext.value,
        conversation_id: currentComprehensiveConvId.value,
      })
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
          aiMsg.stage = ''
          aiMsg.content = data.error
        }
        if (data.message) aiMsg.stage = data.message
        if (data.content) {
          aiMsg.stage = ''
          aiMsg.content += data.content
        }
        if (data.conversation_id) currentComprehensiveConvId.value = data.conversation_id
        if (data.paipan) currentPaipanContext.value = data.paipan
        if (typeof data.points_left === 'number') currentPoints.value = data.points_left
        if (data.done) {
          try { window.__sidebarCache = null } catch(_) {}
        }
      })
    }
    comprehensiveQuestion.value = ''
  } catch (e) {
    aiMsg.stage = ''
    aiMsg.content = '生成失败，请稍后重试'
  } finally {
    comprehensiveLoading.value = false
  }
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
    comprehensiveMessages.value = data.messages || []
    const mid = data.model_id || 'free'
    const mi = llmModels.value.findIndex(m => m.id === mid)
    if (mi >= 0) llmModelIdx.value = mi
    const p = data.profile_data || {}
    selectedProfile.value = {
      id: p.id,
      name: p.name,
      gender: p.gender,
      birthTime: p.birth_time,
      calType: p.cal_type,
      birthAddr: p.birth_addr,
      profileType: p.profile_type,
    }
  } catch (_) {}
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

// ── 视频加载超时处理（H5 only）──
onMounted(() => {
  loadComprehensiveOptions()
  loadProfiles()
  // #ifdef H5
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

.page-root { min-height: 100vh; overflow-x: hidden; }
.bg-layer { position: fixed; inset: 0; z-index: 0; transition: background 0.8s var(--ease); pointer-events: none; }
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
.page-wrap { position: relative; z-index: 1; }

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
.hero-home { min-height: calc(100vh - 60px); display: flex; flex-direction: column; align-items: center; justify-content: flex-start; position: relative; padding: 48px 32px 32px; }
.hero-home-content { max-width: var(--max-w); width: 100%; margin: 0 auto; text-align: center; }
.hero-brand { margin-bottom: 60px; }
.hero-brand-icon-wrap { position: relative; display: flex; align-items: center; justify-content: center; width: 160px; height: 160px; margin: 0 auto 20px; animation: float 6s ease-in-out infinite; }
.hero-brand-icon-wrap::before { content: ''; position: absolute; inset: 0; border-radius: 50%; background: var(--hero-logo-backdrop); box-shadow: var(--hero-logo-backdrop-shadow); z-index: 0; }
.hero-brand-icon { width: 140px; height: 140px; object-fit: cover; position: relative; z-index: 1; display: block; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.hero-brand-name { font-family: var(--font-serif); font-size: 3.2rem; font-weight: 400; letter-spacing: 12px; color: var(--text-1); margin-bottom: 16px; background: linear-gradient(135deg, var(--text-1), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; text-indent: 12px; }
.hero-brand-divider { width: 60px; height: 2px; background: var(--accent); margin: 16px auto; border-radius: 1px; box-shadow: 0 0 12px var(--accent-glow); }
.hero-brand-slogan { font-family: var(--font-serif); font-size: 1.125rem; letter-spacing: 6px; color: var(--accent); margin-bottom: 8px; }
.hero-brand-sub { font-size: 0.875rem; color: var(--text-3); letter-spacing: 2px; }

/* ═══ 首页综合 AI 输入框 ═══ */
.home-ai-console { max-width: 920px; margin: -20px auto 0; text-align: left; }
.home-ai-main { display: grid; grid-template-columns: 190px 1fr 132px 78px; gap: 10px; align-items: stretch; padding: 10px; border: 1px solid var(--card-border); border-radius: 18px; background: rgba(255,255,255,0.055); backdrop-filter: blur(28px) saturate(140%); box-shadow: 0 18px 60px rgba(0,0,0,0.20); }
[data-theme="light"] .home-ai-main { background: rgba(255,253,248,0.68); box-shadow: 0 12px 36px rgba(60,40,15,0.08); }
.profile-picker, .llm-picker, .home-ai-send { min-height: 52px; border-radius: 12px; border: 1px solid var(--card-border); background: var(--input-bg); color: var(--text-1); display: flex; align-items: center; justify-content: center; cursor: pointer; box-sizing: border-box; }
.profile-picker { justify-content: flex-start; gap: 10px; padding: 8px 12px; min-width: 0; }
.profile-plus { width: 28px; height: 28px; border-radius: 50%; background: var(--accent-glow); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 1.1rem; flex-shrink: 0; }
.profile-picked { min-width: 0; }
.profile-name { display: block; font-size: 0.84rem; color: var(--text-1); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.profile-meta { display: block; margin-top: 2px; font-size: 0.66rem; color: var(--text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-ai-input { width: 100%; min-height: 52px; max-height: 132px; padding: 15px 6px; color: var(--text-1); font-size: 0.92rem; line-height: 1.55; background: transparent; border: none; outline: none; box-sizing: border-box; }
.llm-picker { padding: 0 12px; font-size: 0.78rem; color: var(--text-2); white-space: nowrap; }
.home-ai-send { background: var(--accent); border-color: var(--accent); color: #fff; font-size: 0.86rem; font-weight: 600; }
.home-ai-send.disabled { opacity: 0.55; pointer-events: none; }
.tool-model-row { display: flex; gap: 8px; flex-wrap: wrap; margin: 12px 10px 0; }
.tool-model-chip { padding: 6px 12px; border-radius: 999px; border: 1px solid var(--card-border); background: var(--tag-bg); color: var(--text-3); font-size: 0.74rem; cursor: pointer; }
.tool-model-chip.active { border-color: var(--accent); background: var(--accent-glow); color: var(--accent); }
.points-hint { margin: 8px 12px 0; color: var(--text-3); font-size: 0.72rem; }
.home-ai-chat { margin-top: 16px; border: 1px solid var(--card-border); border-radius: 16px; background: var(--card-bg); backdrop-filter: blur(18px); padding: 14px; max-height: 420px; overflow-y: auto; }
.home-ai-message { padding: 12px 14px; border-radius: 12px; margin-bottom: 10px; border: 1px solid var(--card-border); }
.home-ai-message.user { margin-left: 72px; background: var(--accent-glow); border-color: rgba(178,149,93,0.26); }
.home-ai-message.assistant { margin-right: 72px; background: rgba(255,255,255,0.035); }
.home-ai-role { display: block; font-size: 0.68rem; color: var(--text-3); margin-bottom: 6px; }
.home-ai-stage { display: block; font-size: 0.82rem; color: var(--accent); }
.home-ai-content { display: block; white-space: pre-wrap; font-size: 0.86rem; color: var(--text-2); line-height: 1.7; }

.profile-sheet { position: fixed; inset: 0; z-index: 400; }
.profile-sheet-mask { position: absolute; inset: 0; background: rgba(0,0,0,0.48); backdrop-filter: blur(8px); }
.profile-sheet-panel { position: absolute; left: 50%; bottom: 24px; transform: translateX(-50%); width: min(640px, calc(100vw - 28px)); max-height: 72vh; overflow: hidden; border-radius: 18px; border: 1px solid var(--card-border); background: var(--nav-bg); box-shadow: var(--card-shadow); padding: 18px; box-sizing: border-box; }
.profile-sheet-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
.profile-sheet-title { color: var(--text-1); font-size: 1rem; font-family: var(--font-serif); letter-spacing: 2px; }
.profile-sheet-close { color: var(--text-3); font-size: 1.4rem; cursor: pointer; }
.profile-tabs { display: flex; gap: 8px; margin-bottom: 12px; }
.profile-tabs view { flex: 1; text-align: center; padding: 8px 10px; border-radius: 10px; border: 1px solid var(--card-border); color: var(--text-3); font-size: 0.8rem; cursor: pointer; }
.profile-tabs view.active { background: var(--accent-glow); border-color: var(--accent); color: var(--accent); }
.profile-options { max-height: 48vh; overflow-y: auto; }
.profile-option { display: flex; justify-content: space-between; gap: 16px; padding: 12px; border-radius: 12px; border: 1px solid var(--card-border); background: rgba(255,255,255,0.035); margin-bottom: 8px; cursor: pointer; }
.profile-option-name { display: block; color: var(--text-1); font-size: 0.88rem; }
.profile-option-meta { display: block; margin-top: 4px; color: var(--text-3); font-size: 0.72rem; }
.profile-option-type { color: var(--accent); font-size: 0.72rem; white-space: nowrap; }
.profile-empty { padding: 28px; text-align: center; color: var(--text-3); font-size: 0.84rem; }

/* 滚动提示 */
.scroll-hint { position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%); text-align: center; color: var(--text-3); font-size: 0.75rem; letter-spacing: 2px; animation: fadeInUp 1s ease 1.5s both; }
.scroll-arrow { font-size: 1.25rem; margin-top: 4px; animation: bounce 2s ease-in-out infinite; }
@keyframes fadeInUp { from { opacity: 0; transform: translateX(-50%) translateY(20px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(8px); } }

/* ═══ 页脚 ═══ */
.site-footer { background: var(--nav-bg); border-top: 1px solid var(--card-border); padding: 24px 32px 24px; margin-top: 0; }
.footer-disclaimer { max-width: var(--max-w); margin: 0 auto 32px; padding: 14px 20px; border-radius: 10px; background: rgba(215,125,110,0.08); border: 1px solid rgba(215,125,110,0.15); font-size: 0.75rem; color: var(--danger); line-height: 1.6; text-align: center; }
.footer-grid { max-width: var(--max-w); margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 40px; }
.footer-col-title { font-size: 0.8125rem; color: var(--text-2); margin-bottom: 12px; letter-spacing: 1px; }
.footer-col navigator, .footer-col .footer-link { display: block; font-size: 0.75rem; color: var(--text-3); text-decoration: none; padding: 3px 0; }
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
  .home-ai-main { grid-template-columns: 1fr; }
  .profile-picker, .llm-picker, .home-ai-send { min-height: 46px; }
  .footer-grid { grid-template-columns: 1fr; gap: 24px; }
}
@media (max-width: 768px) {
  .hero-home { padding: 100px 16px 60px; min-height: auto; }
  .hero-brand { margin-bottom: 38px; }
  .hero-brand-name { font-size: 2rem; letter-spacing: 6px; }
  .hero-brand-slogan { font-size: 0.875rem; letter-spacing: 3px; }
  .home-ai-console { margin-top: -8px; }
  .home-ai-message.user, .home-ai-message.assistant { margin-left: 0; margin-right: 0; }
  .section { padding: 48px 16px; }
  .scroll-hint { display: none; }
  .section-title { font-size: 1.35rem; }
  .section-desc { font-size: 0.8125rem; }
}
@media (max-width: 480px) {
  .hero-home { padding: 50px 16px 36px; }
  .hero-brand-icon-wrap { width: 120px; height: 120px; }
  .hero-brand-icon { width: 90px; height: 90px; }
  .hero-brand-name { font-size: 1.6rem; letter-spacing: 4px; }
  .hero-brand-slogan { font-size: 0.75rem; letter-spacing: 3px; }
  .hero-brand-sub { font-size: 0.75rem; }
  .section { padding: 32px 16px; }
  .section-title { font-size: 1.15rem; }
  .section-desc { font-size: 0.75rem; }
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .footer-col:nth-child(3) { grid-column: 1 / -1; }
  .site-footer { padding: 32px 16px 24px; margin-top: 0; }
  .footer-bottom { flex-direction: column; gap: 8px; text-align: center; }
}
</style>
