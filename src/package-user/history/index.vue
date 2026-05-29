<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :isLoggedIn="isLoggedIn" @toggle-theme="toggleTheme" />

    <!-- 排盘记录 -->
    <view class="page">
      <!-- 搜索栏 -->
      <view class="search-bar">
        <view id="histSearch-wrap" class="dom-input-wrap"></view>
        <view class="search-type-row">
          <view class="type-chip" id="histFiltAll" @tap="switchHistFilter('')">全部</view>
          <view class="type-chip" id="histFiltComprehensive" @tap="switchHistFilter('综合')">综合</view>
          <view class="type-chip" id="histFiltBazi" @tap="switchHistFilter('八字')">八字</view>
          <view class="type-chip" id="histFiltQimen" @tap="switchHistFilter('奇门')">奇门</view>
          <view class="type-chip" id="histFiltLiuy" @tap="switchHistFilter('六爻')">六爻</view>
          <view class="type-chip" id="histFiltMei" @tap="switchHistFilter('梅花')">梅花</view>
          <view class="type-chip" id="histFiltZiwei" @tap="switchHistFilter('紫微')">紫微</view>
          <view class="type-chip" id="histFiltTaro" @tap="switchHistFilter('塔罗')">塔罗</view>
        </view>
      </view>

      <!-- 空状态 -->
      <view v-if="!loading && filteredRecords.length === 0 && !searchQuery && !filterType" class="empty-state">
        <view class="empty-icon">📋</view>
        <view class="empty-text">暂无排盘记录</view>
        <view class="empty-hint">排盘后记录会自动保存在这里</view>
      </view>

      <!-- 搜索无结果 -->
      <view v-if="!loading && filteredRecords.length === 0 && (searchQuery || filterType)" class="empty-state">
        <view class="empty-icon">🔍</view>
        <view class="empty-text">未找到匹配的记录</view>
        <view class="empty-hint">换个关键词试试</view>
      </view>

      <!-- 加载状态 -->
      <view v-if="loading" class="loading-state">
        <view class="loading-spinner"></view>
        <view style="font-size:0.9375rem;">加载中...</view>
      </view>

      <!-- 记录列表 -->
      <view v-for="(item, idx) in filteredRecords" :key="idx" class="record-card" @tap="rePaipan(item)">
        <view class="record-header">
          <text class="record-name">{{ item.name || item.title || '未命名' }}</text>
          <text class="record-time">{{ formatTime(item.created_at) }}</text>
        </view>
        <view class="record-pillars">{{ item.type === '综合' ? '综合 AI 问答' : (item.pillars || '----') }}</view>
        <view class="record-meta">
          <text v-if="item.type">{{ item.type }}</text>
          <text v-if="item.model_id">{{ item.model_id === 'free' ? '免费模型' : item.model_id }}</text>
          <text v-if="item.models && item.models.length">{{ item.models.join(' / ') }}</text>
          <text v-if="item.gender">{{ item.gender }}</text>
          <text v-if="item.birth_time">{{ item.birth_time }}</text>
          <text v-if="item.cal_type">{{ item.cal_type }}</text>
          <text v-if="item.birth_addr">{{ item.birth_addr }}</text>
        </view>
      </view>
    </view>


  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import TopNav from '@/components/TopNav.vue'

// ═══ 主题 ═══
const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  uni.setStorageSync('xc_theme', theme.value)
  try {
    document.documentElement.setAttribute('data-theme', theme.value); const root = document.querySelector('.page-root')
    if (root) root.setAttribute('data-theme', theme.value)
    const icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = theme.value === 'dark' ? '🌙' : '☀️'
  } catch(_) {}
}

// ═══ 登录/注册 ═══
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

// ═══ 历史记录 ═══
const records = ref([])
const loading = ref(true)
const searchQuery = ref('')
const filterType = ref('')

// 模式B: filterType DOM classList切换
function switchHistFilter(type) {
  filterType.value = type
  var types = ['','综合','八字','奇门','六爻','梅花','紫微','塔罗']
  var ids = ['histFiltAll','histFiltComprehensive','histFiltBazi','histFiltQimen','histFiltLiuy','histFiltMei','histFiltZiwei','histFiltTaro']
  for (var i = 0; i < types.length; i++) {
    var el = document.getElementById(ids[i])
    if (el) { type === types[i] ? el.classList.add('active') : el.classList.remove('active') }
  }
}

// 模式A: 创建原生input
function createNativeInput(wrapId, type, placeholder) {
  var wrap = document.getElementById(wrapId)
  if (!wrap) return null
  var inp = document.createElement('input')
  inp.type = type
  inp.className = 'search-input'
  inp.id = wrapId.replace('-wrap', '')
  if (placeholder) inp.placeholder = placeholder
  if (type === 'text') inp.setAttribute('maxlength', '100')
  if (type === 'number') { inp.min = '0'; inp.max = '999' }
  wrap.appendChild(inp)
  return inp
}

// 前端过滤 - 在已有 records 基础上做搜索和筛选
const filteredRecords = computed(() => {
  let list = records.value
  // 类型筛选
  if (filterType.value) {
    list = list.filter(r => r.type === filterType.value)
  }
  // 关键词搜索
  if (searchQuery.value.trim()) {
    const q = searchQuery.value.trim().toLowerCase()
    list = list.filter(r => {
      return (r.name || '').toLowerCase().includes(q)
        || (r.pillars || '').toLowerCase().includes(q)
        || (r.birth_time || '').includes(q)
        || (r.gender || '').includes(q)
        || (r.type || '').toLowerCase().includes(q)
    })
  }
  return list
})

function doSearch() {
  // 搜索由 computed 自动处理，这里可以触发额外逻辑
  // 比如记录搜索词用于统计等
}

function formatTime(ts) {
  if (!ts) return ''
  try {
    const d = new Date(ts)
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  } catch (e) { return '' }
}

// 重新排盘 — 保存参数并跳转到排盘结果页
function rePaipan(item) {
  if (item.type === '综合') {
    // #ifdef H5
    try { sessionStorage.setItem('xc_comprehensive_resume_id', String(item.id || '')) } catch(_) {}
    // #endif
    uni.switchTab({ url: '/pages/index/index' })
    return
  }
  const params = item.params || {}
  if (item.type === '八字' || !item.type) {
    // 保存参数到 sessionStorage (H5) 或直接跳转
    // #ifdef H5
    try { sessionStorage.setItem('xc_bazi_params', JSON.stringify(params)) } catch (e) {}
    // #endif
    uni.navigateTo({ url: '/pages/bazi-result/index' })
  } else if (item.type === '奇门') {
    try { sessionStorage.setItem('_nav_query', '?id=' + (item.id || '')) } catch(_) {}
    uni.switchTab({
      url: '/pages/qimen/index',
      success: function() {
        setTimeout(function() { try { uni.$emit('nav-query', '?id=' + (item.id || '')) } catch(_) {} }, 200)
      }
    })
  }
}

// 清空历史
function clearHistory() {
  uni.showModal({
    title: '确认清空',
    content: '确定要清空所有排盘历史吗？',
    success: async (r) => {
      if (r.confirm) {
        try {
          await uni.request({ url: '/api/bazi/history/clear', method: 'POST' })
        } catch (e) {}
        records.value = []
        uni.showToast({ title: '已清空', icon: 'success' })
      }
    }
  })
}

// 加载历史记录
async function loadHistory() {
  loading.value = true
  try {
    const res = await uni.request({ url: '/api/bazi/history' })
    const data = res.data
    let list = []
    if (data && data.success) {
      list = (data.history || []).map(function(item) {
        item.type = item.type === 'paipan' || !item.type ? '八字' : item.type
        return item
      })
    }
    try {
      const cr = await uni.request({ url: '/api/comprehensive/conversations' })
      const convs = Array.isArray(cr.data) ? cr.data : []
      list = convs.map(function(c) {
        return Object.assign({}, c, {
          type: '综合',
          name: c.title || '综合 AI 问答',
          created_at: c.updated_at || c.created_at,
        })
      }).concat(list)
    } catch (_) {}
    records.value = list
  } catch (e) {
    // 后端未启动时显示空状态
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHistory()
  // #ifdef H5
  var inp = createNativeInput('histSearch-wrap', 'text', '搜索姓名、四柱...')
  if (inp) {
    inp.addEventListener('input', function() {
      searchQuery.value = inp.value
    })
  }
  // #endif
})
</script>

<style scoped>
/* ═══ 变量体系 ═══ */
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] {
  --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824;
  --accent: hsl(38, 60%, 60%); --accent-2: hsl(38, 60%, 48%);
  --accent-glow: hsla(38, 60%, 60%, 0.10);
  --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12);
  --card-border-hover: rgba(255,255,255,0.18);
  --card-shadow: 0 16px 48px rgba(0,0,0,0.35);
  --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20);
  --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95);
  --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88);
  --success: rgba(110,195,135,0.88); --info: rgba(46,131,246,0.88);
  --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45);
  --tag-bg: rgba(255,255,255,0.08); --tag-text: rgba(195,185,165,0.85);
}
[data-theme="light"] {
  --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0;
  --accent: hsl(38, 72%, 30%); --accent-2: hsl(38, 72%, 22%);
  --accent-glow: hsla(38, 72%, 30%, 0.065);
  --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045);
  --card-border-hover: rgba(0,0,0,0.08);
  --card-shadow: 0 8px 28px rgba(60,40,15,0.055);
  --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065);
  --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90);
  --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88);
  --success: rgba(30,130,60,0.88); --info: rgba(46,131,246,0.88);
  --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45);
  --tag-bg: rgba(0,0,0,0.05); --tag-text: rgba(70,58,40,0.80);
}

.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }

/* 记录页 */
.page { max-width: 680px; margin: 0 auto; padding: 16px; position: relative; z-index: 1; }
.search-bar { padding: 0 0 16px; }
.search-input { width: 100%; padding: 9px 14px; border-radius: 8px; background: var(--card-bg); border: 1.5px solid var(--card-border); color: var(--text-1); font-size: 0.85rem; outline: none; box-sizing: border-box; margin-bottom: 10px; }
.search-type-row { display: flex; gap: 6px; flex-wrap: wrap; }
.type-chip { padding: 5px 12px; border-radius: 16px; font-size: 0.75rem; background: var(--tag-bg); border: 1px solid var(--card-border); color: var(--text-3); cursor: pointer; transition: 0.2s; }
.type-chip.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); font-weight: 600; }
.empty-state { text-align: center; padding: 60px 20px; color: var(--text-3); }
.empty-icon { font-size: 3rem; margin-bottom: 16px; }
.empty-text { font-size: 0.9375rem; color: var(--text-2); margin-bottom: 4px; }
.empty-hint { font-size: 0.8125rem; color: var(--text-3); }
.loading-state { text-align: center; padding: 60px 20px; color: var(--text-3); }
.loading-spinner { display: inline-block; width: 40px; height: 40px; border: 3px solid var(--card-border); border-top-color: var(--accent); border-radius: 50%; animation: spin 0.8s linear infinite; margin-bottom: 16px; }
@keyframes spin { to { transform: rotate(360deg); } }

.record-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 14px; margin-bottom: 10px; cursor: pointer; transition: all 0.2s var(--ease); }
.record-card:active { border-color: var(--accent); transform: translateY(-1px); }
.record-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.record-name { font-weight: 600; font-size: 0.95rem; color: var(--text-1); }
.record-time { font-size: 0.72rem; color: var(--text-3); }
.record-pillars { font-size: 1.2rem; letter-spacing: 4px; margin: 6px 0; color: var(--accent); font-family: var(--font-serif); }
.record-meta { font-size: 0.78rem; color: var(--text-2); display: flex; gap: 12px; flex-wrap: wrap; }

/* 弹窗 */
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

/* 响应式 */
@media (max-width: 768px) {
  .page { padding: 12px; }
}
</style>
