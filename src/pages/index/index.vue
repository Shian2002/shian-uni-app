<template>
  <view class="page-root" :data-theme="theme">
    <!-- 视频背景层（H5 only） -->
    <!-- #ifdef H5 -->
    <view class="video-bg" :class="{ 'video-fallback': videoFallback }" id="videoBg">
      <video
        class="video-bg-video"
        id="heroVideo"
        autoplay
        muted
        loop
        playsinline
        @error="onVideoError"
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
            <view class="hero-brand-icon-wrap"><image class="hero-brand-icon" src="/static/images/logo.png" mode="aspectFit" /></view>
            <view class="hero-brand-name">时安解忧屋</view>
            <view class="hero-brand-divider"></view>
            <view class="hero-brand-slogan">八字定终身格局 · 奇门断当下决策</view>
            <view class="hero-brand-sub">看得懂用得上的民俗命理参考平台</view>
          </view>

          <!-- 产品卡片 -->
          <view class="hero-cards">
            <navigator url="/pages/qimen/index" open-type="switchTab" class="hero-card hero-card-primary">
              <view class="hero-card-glow"></view>
              <view class="hero-card-content">
                <view class="hero-card-icon">🔮</view>
                <view class="hero-card-title">奇门遁甲</view>
                <view class="hero-card-desc">一事一断 · 吉凶预判 · 择时择方</view>
                <view class="hero-card-features">
                  <view class="hero-card-tag">时安奇门系统</view>
                  <view class="hero-card-tag free">免费排盘</view>
                </view>
                <view class="hero-card-arrow">→</view>
              </view>
            </navigator>

            <navigator url="/pages/bazi-index/index" open-type="switchTab" class="hero-card hero-card-primary">
              <view class="hero-card-glow"></view>
              <view class="hero-card-content">
                <view class="hero-card-icon">📜</view>
                <view class="hero-card-title">八字排盘</view>
                <view class="hero-card-desc">定格局 · 看喜忌 · 断大运 · 知财运</view>
                <view class="hero-card-features">
                  <view class="hero-card-tag">时安八字系统</view>
                  <view class="hero-card-tag free">免费排盘</view>
                </view>
                <view class="hero-card-arrow">→</view>
              </view>
            </navigator>

            <!-- 更多工具小卡片 -->
            <view class="hero-mini-scroll">
              <navigator url="/pages/liuyao/index" open-type="switchTab" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">🧭</view>
                <view class="hero-card-title">六爻排盘</view>
                <view class="hero-card-arrow">→</view>
              </view>
            </navigator>

            <navigator url="/pages/meihua/index" open-type="switchTab" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">🌸</view>
                <view class="hero-card-title">梅花易数</view>
                <view class="hero-card-arrow">→</view>
              </view>
            </navigator>

            <navigator url="/pages/ziwei/index" open-type="switchTab" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">⭐</view>
                <view class="hero-card-title">紫微斗数</view>
                <view class="hero-card-arrow">→</view>
              </view>
            </navigator>

            <navigator url="/pages/tarot/index" open-type="switchTab" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">🃏</view>
                <view class="hero-card-title">塔罗牌</view>
                <view class="hero-card-arrow">→</view>
              </view>
            </navigator>

            <navigator url="/pages/zeji/index" open-type="switchTab" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">📅</view>
                <view class="hero-card-title">择吉工具</view>
                <view class="hero-card-arrow">→</view>
              </view>
            </navigator>

            <navigator url="/pages/calendar/index" open-type="switchTab" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">🗓️</view>
                <view class="hero-card-title">专属日历</view>
                <view class="hero-card-arrow">→</view>
              </view>
            </navigator>

            <navigator url="/pages/community/index" open-type="switchTab" class="hero-card hero-card-mini">
              <view class="hero-card-content">
                <view class="hero-card-icon">💬</view>
                <view class="hero-card-title">交流社区</view>
                <view class="hero-card-arrow">→</view>
              </view>
            </navigator>
            </view>
          </view>
        </view>

        <!-- 滚动提示 -->
        <view class="scroll-hint">
          <view class="scroll-arrow">↓</view>
        </view>
      </section>

      <!-- ═══ 核心特色 ═══ -->
      <section class="section">
        <view class="section-tag">核心特色</view>
        <view class="section-title">双术数融合 · 更全面的命理参考</view>
        <view class="section-desc">以八字定先天根基与人生大势，以奇门断当下事件与具体决策</view>
        <view class="feature-scroll-wrap">
          <view class="feature-grid">
            <view class="feature-card" v-for="f in features" :key="f.title">
              <view class="feature-icon">{{ f.icon }}</view>
              <view class="feature-card-title">{{ f.title }}</view>
              <view class="feature-card-desc">{{ f.desc }}</view>
            </view>
          </view>
        </view>
      </section>

      <!-- ═══ 场景快速入口 ═══ -->
      <view class="section-alt">
        <section class="section">
          <view class="section-tag">快速场景</view>
          <view class="section-title">针对具体事件精准起局</view>
          <view class="section-desc">选择你的场景，一键获取专业解读参考</view>
          <view class="scenario-scroll-wrap">
            <view class="scenario-grid">
              <view class="scenario-card" v-for="s in scenarios" :key="s.key" @tap="goScenario(s.key)">
                <text class="scenario-emoji">{{ s.emoji }}</text>
                <view class="scenario-card-title">{{ s.title }}</view>
              </view>
            </view>
          </view>
        </section>
      </view>

      <!-- ═══ 信任背书 ═══ -->
      <section class="section">
        <view class="section-tag">信任背书</view>
        <view class="section-title">专业排盘体系 · 权威有据可依</view>
        <view class="section-desc">透明公开排盘规则与算法依据，真实应验案例可查可验证</view>
        <view class="trust-grid">
          <view class="trust-authority">
            <view class="trust-authority-title">📋 排盘内核权威说明</view>
            <view class="auth-item" v-for="a in authorities" :key="a.title">
              <view class="auth-item-title">{{ a.title }}</view>
              <view class="auth-item-desc">{{ a.desc }}</view>
            </view>
          </view>
          <view class="case-scroll-wrap">
            <view class="section-tag">真实案例</view>
            <view class="case-tabs">
              <view class="case-tab" id="idxCaseAll" @tap="switchCaseFilter('all')">全部</view>
              <view class="case-tab" id="idxCaseClassic" @tap="switchCaseFilter('classic')">经典案例</view>
              <view class="case-tab" id="idxCaseReal" @tap="switchCaseFilter('real')">实战案例</view>
            </view>
            <view class="case-list">
              <view class="case-card" v-for="c in filteredCases" :key="c.title" :data-source="c.source">
                <view class="case-type">{{ c.type }}</view>
                <view class="case-card-title">{{ c.title }}</view>
                <view class="case-card-desc">{{ c.desc }}</view>
                <view class="case-verified">✅ 已应验</view>
                <view class="case-disclaimer">仅为民俗参考，不代表绝对结果</view>
              </view>
            </view>
          </view>
        </view>
      </section>

      <!-- ═══ FAQ ═══ -->
      <section class="section">
        <view class="faq-panel" id="faqPanel">
          <view class="faq-panel-header" id="faqPanelHeader" @tap="toggleFaqPanel">
            <view class="faq-panel-title">❓ 新手常见问题</view>
            <view class="faq-panel-arrow" id="faqPanelArrow">▲</view>
          </view>
          <view class="faq-panel-body" id="faqPanelBody">
            <view class="faq-item" v-for="(faq, idx) in faqs" :key="faq.q">
              <view class="faq-q" :id="'faqQ' + idx" @tap="toggleFaq">
                <text>{{ faq.q }}</text>
                <text class="arrow">▼</text>
              </view>
              <view class="faq-a">{{ faq.a }}</view>
            </view>
          </view>
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
            <navigator url="/pages/qimen/index" open-type="switchTab">奇门遁甲</navigator>
            <navigator url="/pages/bazi-index/index" open-type="switchTab">八字排盘</navigator>
            <navigator url="/pages/calendar/index" open-type="switchTab">专属日历</navigator>
            <navigator url="/pages/community/index" open-type="switchTab">社区</navigator>
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


  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
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
function onVideoError() {
  videoFallback.value = true
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

// ── 核心特色数据 ──
const features = [
  { icon: '🔮', title: '时安深度解读', desc: '小白极简版 + 专业深度版，专业术语点击即弹出大白话释义' },
  { icon: '⚡', title: '秒出排盘', desc: '本地精准排盘引擎，基于天文历表，节气精确到分钟级' },
  { icon: '🔄', title: '双体系互补', desc: '八字看"命里有没有"，奇门看"现在该怎么做"，双体系结合更全面' },
  { icon: '📜', title: '古籍加持', desc: '融合《渊海子平》《奇门旨归》等经典古籍，以古法为基，以今用为归' },
  { icon: '📱', title: '全端适配', desc: '桌面端、平板、手机全端适配，随时随地查排盘' },
  { icon: '🎯', title: '场景化问事', desc: '面试能否通过、项目能否回款、感情复合时机等快速场景一键起局' },
  { icon: '🔒', title: '无痕模式', desc: '默认开启，所有排盘计算在本地完成，不上传任何数据，退出自动清空' },
]

// ── 场景快速入口 ──
const scenarios = [
  { key: 's_interview', emoji: '💼', title: '面试能否通过' },
  { key: 's_project', emoji: '💰', title: '项目能否回款' },
  { key: 's_loveback', emoji: '💕', title: '感情复合时机' },
  { key: 's_house', emoji: '🏠', title: '买房租房吉凶' },
  { key: 's_travel', emoji: '✈️', title: '出行安全预判' },
  { key: 's_business', emoji: '🏪', title: '开业签约择吉' },
]

function goScenario(key) {
  try { sessionStorage.setItem('_nav_query', '?scenario=' + key) } catch(_) {}
  uni.switchTab({
    url: '/pages/qimen/index',
    success: function() {
      setTimeout(function() { try { uni.$emit('nav-query', '?scenario=' + key) } catch(_) {} }, 200)
    }
  })
}

// ── 信任背书 ──
const authorities = [
  { title: '奇门遁甲排盘规则', desc: '采用时家奇门拆补法起局，支持置闰法、茅山法切换。用神取日干/时干双参体系，值符值使自动推演。' },
  { title: '八字排盘命理体系', desc: '基于子平术命理体系，支持真太阳时校正。四柱推排、十神分析、大运流年自动计算。' },
  { title: '算法依据与数据源', desc: '历法数据对接天文历表，节气精确到分钟级。所有推算逻辑开源可审查。' },
]

const caseFilter = ref('all')

// 模式B: DOM classList切换
function switchCaseFilter(val) {
  caseFilter.value = val
  var all = document.getElementById('idxCaseAll')
  var cls = document.getElementById('idxCaseClassic')
  var real = document.getElementById('idxCaseReal')
  if (all) { val === 'all' ? all.classList.add('active') : all.classList.remove('active') }
  if (cls) { val === 'classic' ? cls.classList.add('active') : cls.classList.remove('active') }
  if (real) { val === 'real' ? real.classList.add('active') : real.classList.remove('active') }
}

function toggleFaq(ev) {
  var el = ev && ev.currentTarget  // .faq-q (guard against programmatic dispatch)
  if (!el) return
  el.classList.toggle('open')
  // DOM操作 toggle .faq-a 和 .arrow（绕过Vue 3.4.21 render effect bug）
  var item = el.parentNode  // .faq-item
  if (item) {
    var answer = item.querySelector('.faq-a')
    if (answer) answer.classList.toggle('open')
    var arrow = item.querySelector('.arrow')
    if (arrow) arrow.classList.toggle('rotated')
  }
  // 备份同步Vue reactive数据（供非DOM操作场合使用）
  var id = el.id
  var idx = parseInt(id.replace('faqQ', ''))
  if (!isNaN(idx) && faqs[idx]) {
    faqs[idx].open = !faqs[idx].open
  }
}
const cases = [
  { source: 'classic', type: '事业 · 奇门遁甲', title: '求职面试能否通过', desc: '排盘解读结论为利东方方位、午时有利。后续果然调整时间后顺利通过。' },
  { source: 'classic', type: '感情 · 奇门遁甲', title: '感情复合时机判断', desc: '排盘显示休门临宫、逢合期在秋分后。用户反馈秋分后确实关系缓和。' },
  { source: 'real', type: '财运 · 八字命理', title: '投资理财方向参考', desc: '八字分析显示偏财星弱、正财为主，建议稳健理财。用户采纳后避免了高风险损失。' },
]
const filteredCases = computed(() => {
  if (caseFilter.value === 'all') return cases
  return cases.filter(c => c.source === caseFilter.value)
})

// ── FAQ ──
const faqPanelOpen = ref(false)
function toggleFaqPanel() {
  faqPanelOpen.value = !faqPanelOpen.value
  var panel = document.getElementById('faqPanel')
  if (panel) panel.classList.toggle('open')
  var body = document.getElementById('faqPanelBody')
  if (body) body.classList.toggle('open')
  var arrow = document.getElementById('faqPanelArrow')
  if (arrow) arrow.classList.toggle('rotated')
}
const faqs = reactive([
  { q: '排盘时间怎么选？', a: '新手模式下默认使用当前时间，这也是最常用的起局方式。奇门遁甲讲究"当时当刻"，用问事时刻起局即可。', open: false },
  { q: '解读结果怎么看？', a: '建议新手先看"小白极简版"，只保留核心结论和行动建议。有基础后可切换"专业深度版"。', open: false },
  { q: '无痕模式怎么用？', a: '无痕模式默认开启，所有排盘计算在本地完成，不上传任何数据。关闭页面后数据自动清空。', open: false },
  { q: '八字和奇门该用哪个？', a: '看整体运势用八字，看具体事件用奇门。两者结合使用效果更全面。', open: false },
])

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
onShow(() => {
  var t = uni.getStorageSync('xc_theme')
  if (t && t !== theme.value) {
    theme.value = t
    try {
      document.documentElement.setAttribute('data-theme', t)
      document.body.setAttribute('data-theme', t)
    } catch(_) {}
  }
})

// ── 视频加载超时处理（H5 only）──
onMounted(() => {
  // #ifdef H5
  setTimeout(() => {
    const v = document.getElementById('heroVideo')
    if (v && v.readyState < 2) {
      videoFallback.value = true
      v.style.display = 'none'
    }
  }, 3000)
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
.video-bg { position: fixed; inset: 0; z-index: -1; overflow: hidden; }
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
.hero-home { min-height: calc(100vh - 60px); display: flex; flex-direction: column; align-items: center; justify-content: flex-start; position: relative; padding: 48px 32px 60px; }
.hero-home-content { max-width: var(--max-w); width: 100%; margin: 0 auto; text-align: center; }
.hero-brand { margin-bottom: 60px; }
.hero-brand-icon-wrap { position: relative; display: flex; align-items: center; justify-content: center; width: 170px; height: 170px; margin: 0 auto 20px; animation: float 6s ease-in-out infinite; }
.hero-brand-icon-wrap::before { content: ''; position: absolute; inset: 0; border-radius: 50%; background: var(--hero-logo-backdrop); box-shadow: var(--hero-logo-backdrop-shadow); z-index: 0; }
.hero-brand-icon { width: 130px; height: 130px; position: relative; z-index: 1; display: block; }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-10px); } }
.hero-brand-name { font-family: var(--font-serif); font-size: 3.2rem; font-weight: 400; letter-spacing: 12px; color: var(--text-1); margin-bottom: 16px; background: linear-gradient(135deg, var(--text-1), var(--accent)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text; }
.hero-brand-divider { width: 60px; height: 2px; background: var(--accent); margin: 16px auto; border-radius: 1px; box-shadow: 0 0 12px var(--accent-glow); }
.hero-brand-slogan { font-family: var(--font-serif); font-size: 1.125rem; letter-spacing: 6px; color: var(--accent); margin-bottom: 8px; }
.hero-brand-sub { font-size: 0.875rem; color: var(--text-3); letter-spacing: 2px; }

/* ═══ 产品卡片网格 ═══ */
.hero-cards { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-top: 20px; }
.hero-card-primary { grid-column: span 2; background: rgba(255, 255, 255, 0.06); border-color: rgba(255, 255, 255, 0.12); }
.hero-card-primary:hover { border-color: var(--accent); }
[data-theme="light"] .hero-card-primary { background: rgba(255, 253, 248, 0.55); }
.hero-card { position: relative; display: block; text-decoration: none; color: inherit; background: rgba(255, 255, 255, 0.04); backdrop-filter: blur(30px) saturate(150%); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 20px; padding: 32px 24px; transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1); overflow: hidden; cursor: pointer; }
[data-theme="light"] .hero-card { background: rgba(255, 253, 248, 0.45); border-color: rgba(0, 0, 0, 0.06); }
.hero-card:hover { transform: translateY(-6px) scale(1.02); border-color: rgba(255, 255, 255, 0.18); box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3), 0 0 40px var(--accent-glow); }
[data-theme="light"] .hero-card:hover { border-color: rgba(0, 0, 0, 0.12); box-shadow: 0 20px 60px rgba(60, 40, 15, 0.1), 0 0 40px var(--accent-glow); }
.hero-card-glow { position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle at center, var(--accent-glow) 0%, transparent 70%); opacity: 0; transition: opacity 0.4s; pointer-events: none; }
.hero-card:hover .hero-card-glow { opacity: 1; }
.hero-card-content { position: relative; z-index: 1; }
.hero-card-icon { font-size: 2.5rem; margin-bottom: 16px; }
.hero-card-title { font-family: var(--font-serif); font-size: 1.25rem; font-weight: 400; letter-spacing: 4px; color: var(--text-1); margin-bottom: 8px; }
.hero-card-desc { font-size: 0.8125rem; color: var(--text-3); letter-spacing: 1px; margin-bottom: 16px; line-height: 1.6; }
.hero-card-features { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 12px; }
.hero-card-tag { padding: 4px 12px; border-radius: 20px; font-size: 0.6875rem; background: var(--accent-glow); color: var(--accent); border: 1px solid rgba(255,255,255,0.06); letter-spacing: 1px; }
[data-theme="light"] .hero-card-tag { border-color: rgba(0,0,0,0.04); }
.hero-card-tag.free { background: rgba(110,195,135,0.1); color: var(--success); }
.hero-card-arrow { font-size: 1.25rem; color: var(--accent); opacity: 0; transform: translateX(-8px); transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.hero-card:hover .hero-card-arrow { opacity: 1; transform: translateX(0); }

.hero-mini-scroll { display: flex; flex-wrap: wrap; gap: 12px; grid-column: 1 / -1; position: relative; }
/* 小卡片 */
.hero-card-mini { background: rgba(255, 255, 255, 0.02); border-color: rgba(255, 255, 255, 0.05); padding: 16px 18px; border-radius: 14px; }
.hero-card-mini:hover { transform: translateY(-3px) scale(1.01); border-color: rgba(255, 255, 255, 0.12); box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
[data-theme="light"] .hero-card-mini { background: rgba(255, 253, 248, 0.3); border-color: rgba(0,0,0,0.04); }
.hero-card-mini .hero-card-content { display: flex; align-items: center; gap: 10px; }
.hero-card-mini .hero-card-icon { font-size: 1.5rem; margin-bottom: 0; flex-shrink: 0; }
.hero-card-mini .hero-card-title { font-size: 0.9375rem; letter-spacing: 2px; margin-bottom: 0; flex: 1; }
.hero-card-mini .hero-card-arrow { font-size: 0.875rem; opacity: 0.5; transform: none; }
.hero-card-mini:hover .hero-card-arrow { opacity: 1; transform: translateX(4px); }
.hero-card-mini .hero-card-desc { display: none; }
.hero-card-mini .hero-card-features { display: none; }

/* 滚动提示 */
.scroll-hint { position: absolute; bottom: 32px; left: 50%; transform: translateX(-50%); text-align: center; color: var(--text-3); font-size: 0.75rem; letter-spacing: 2px; animation: fadeInUp 1s ease 1.5s both; }
.scroll-arrow { font-size: 1.25rem; margin-top: 4px; animation: bounce 2s ease-in-out infinite; }
@keyframes fadeInUp { from { opacity: 0; transform: translateX(-50%) translateY(20px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }
@keyframes bounce { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(8px); } }

/* ═══ 核心特色 ═══ */
.feature-scroll-wrap { position: relative; }
.feature-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; }
.feature-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 28px 24px; backdrop-filter: blur(20px); transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); text-align: center; }
.feature-icon { font-size: 2rem; margin-bottom: 12px; }
.feature-card-title { font-family: var(--font-serif); font-size: 0.9375rem; letter-spacing: 2px; margin-bottom: 8px; color: var(--text-1); }
.feature-card-desc { font-size: 0.8125rem; color: var(--text-3); line-height: 1.6; }

/* ═══ 场景快速入口 ═══ */
.scenario-scroll-wrap { position: relative; }
.scenario-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 16px; }
.scenario-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 24px 16px; backdrop-filter: blur(16px); text-align: center; cursor: pointer; transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1); }
.scenario-emoji { font-size: 2rem; display: block; margin-bottom: 8px; }
.scenario-card-title { font-size: 0.8125rem; color: var(--text-2); letter-spacing: 1px; }

/* ═══ 信任背书 ═══ */
.trust-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 32px; }
.trust-authority { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; backdrop-filter: blur(16px); }
.trust-authority-title { font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px; margin-bottom: 16px; }
.auth-item { margin-bottom: 12px; }
.auth-item-title { font-size: 0.8125rem; color: var(--accent); margin-bottom: 4px; }
.auth-item-desc { font-size: 0.75rem; color: var(--text-3); line-height: 1.6; }
.case-scroll-wrap { overflow: hidden; position: relative; }
.case-tabs { display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }
.case-tab { padding: 5px 14px; border-radius: 20px; font-size: 0.75rem; border: 1px solid var(--card-border); color: var(--text-3); cursor: pointer; background: transparent; }
.case-tab.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }
.case-list { display: flex; gap: 16px; overflow-x: auto; padding-bottom: 8px; }
.case-card { flex: 0 0 300px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); padding: 20px; backdrop-filter: blur(16px); }
.case-type { font-size: 0.6875rem; color: var(--accent); margin-bottom: 8px; letter-spacing: 1px; }
.case-card-title { font-size: 0.875rem; margin-bottom: 6px; color: var(--text-1); }
.case-card-desc { font-size: 0.75rem; color: var(--text-3); line-height: 1.5; margin-bottom: 8px; }
.case-verified { font-size: 0.6875rem; color: var(--success); }
.case-disclaimer { font-size: 0.625rem; color: var(--text-3); margin-top: 8px; border-top: 1px dashed var(--card-border); padding-top: 8px; }

/* ═══ FAQ ═══ */
.faq-panel { max-width: var(--max-w); margin: 0 auto 32px; border: 1px solid var(--card-border); border-radius: var(--radius-md); overflow: hidden; background: var(--card-bg); backdrop-filter: blur(12px); }
.faq-panel-header { display: flex; justify-content: space-between; align-items: center; padding: 16px 24px; cursor: pointer; }
.faq-panel-title { font-family: var(--font-serif); font-size: 0.9375rem; letter-spacing: 2px; color: var(--text-2); }
.faq-panel-arrow { font-size: 0.75rem; color: var(--text-3); transition: transform 0.3s var(--ease); }
.faq-panel-arrow.rotated { transform: rotate(180deg); }
.faq-panel-body { max-height: 0; overflow: hidden; transition: max-height 0.4s var(--ease); padding: 0 20px; }
.faq-panel-body.open { max-height: 600px; padding: 0 20px 16px; }
.faq-item { border: 1px solid var(--card-border); border-radius: 10px; margin-bottom: 8px; overflow: hidden; }
.faq-q { padding: 14px 20px; cursor: pointer; font-size: 0.875rem; color: var(--text-2); display: flex; justify-content: space-between; align-items: center; background: var(--card-bg); }
.faq-q .arrow { transition: transform 0.2s; }
.faq-q .arrow.rotated { transform: rotate(180deg); }
.faq-a { padding: 0 20px; max-height: 0; overflow: hidden; transition: max-height 0.3s var(--ease); font-size: 0.8125rem; color: var(--text-3); line-height: 1.7; }
.faq-a.open { max-height: 200px; padding: 14px 20px; }

/* ═══ 页脚 ═══ */
.site-footer { background: var(--nav-bg); border-top: 1px solid var(--card-border); padding: 48px 32px 24px; margin-top: 80px; }
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
  .hero-cards { grid-template-columns: repeat(2, 1fr); }
  .hero-card-primary { grid-column: span 2; }
  .feature-grid { grid-template-columns: repeat(2, 1fr); }
  .scenario-grid { grid-template-columns: repeat(3, 1fr); }
  .trust-grid { grid-template-columns: 1fr; }
  .footer-grid { grid-template-columns: 1fr; gap: 24px; }
}
@media (max-width: 768px) {
  .hero-home { padding: 100px 16px 60px; min-height: auto; }
  .hero-brand-name { font-size: 2rem; letter-spacing: 6px; }
  .hero-brand-slogan { font-size: 0.875rem; letter-spacing: 3px; }
  .hero-cards { grid-template-columns: 1fr 1fr; gap: 12px; }
  .hero-card-primary { grid-column: span 2; }
  .hero-card { padding: 20px 16px; }
  .section { padding: 48px 16px; }
  .feature-grid { grid-template-columns: 1fr 1fr; }
  .scenario-grid { grid-template-columns: repeat(3, 1fr); }
  .scroll-hint { display: none; }
  .section-title { font-size: 1.35rem; }
  .section-desc { font-size: 0.8125rem; }
  .feature-card-title { font-size: 0.875rem; }
  .feature-card-desc { font-size: 0.75rem; }
  .scenario-card-title { font-size: 0.75rem; }
  .hero-card-title { font-size: 1.05rem; }
  .hero-card-desc { font-size: 0.75rem; }
  /* 案例卡片右侧淡出提示更多内容 */
  .case-scroll-wrap::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 60px;
    height: 100%;
    background: linear-gradient(to right, transparent, var(--bg));
    pointer-events: none;
    z-index: 1;
  }
}
@media (max-width: 480px) {
  .hero-home { padding: 50px 16px 36px; }
  .hero-brand-icon-wrap { width: 120px; height: 120px; }
  .hero-brand-icon { width: 90px; height: 90px; }
  .hero-brand-name { font-size: 1.6rem; letter-spacing: 4px; }
  .hero-brand-slogan { font-size: 0.75rem; letter-spacing: 3px; }
  .hero-brand-sub { font-size: 0.75rem; }
  .hero-cards { grid-template-columns: 1fr; }
  .hero-card-primary { grid-column: span 1; }
  .hero-mini-scroll { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; padding-bottom: 0; }
  .hero-mini-scroll .hero-card-mini {
    padding: 20px 12px;
    border-radius: 12px;
    flex-direction: column;
    text-align: center;
    gap: 6px;
  }
  .hero-mini-scroll .hero-card-mini .hero-card-content {
    flex-direction: column;
    gap: 6px;
  }
  .hero-mini-scroll .hero-card-mini .hero-card-arrow { display: none; }
  .hero-mini-scroll .hero-card-mini .hero-card-icon { font-size: 1.5rem; margin-bottom: 0; }
  .hero-mini-scroll .hero-card-mini .hero-card-title { font-size: 0.6875rem; letter-spacing: 1px; text-align: center; }
  .feature-scroll-wrap { overflow: hidden; }
  .feature-grid { display: flex; gap: 12px; overflow-x: auto; flex-wrap: nowrap; padding-bottom: 8px; }
  .feature-card { flex: 0 0 100px; min-height: auto; padding: 16px 10px; }
  .feature-scroll-wrap::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 48px;
    height: 100%;
    background: linear-gradient(to right, transparent, var(--bg));
    pointer-events: none;
    z-index: 1;
  }
  .scenario-scroll-wrap { overflow: hidden; }
  .scenario-grid { display: flex; gap: 10px; overflow-x: auto; flex-wrap: nowrap; padding-bottom: 8px; }
  .scenario-card { flex: 0 0 100px; }
  .scenario-scroll-wrap::after {
    content: '';
    position: absolute;
    top: 0; right: 0;
    width: 48px;
    height: 100%;
    background: linear-gradient(to right, transparent, var(--section-alt));
    pointer-events: none;
    z-index: 1;
  }
  .section { padding: 32px 16px; }
  .section-title { font-size: 1.15rem; }
  .section-desc { font-size: 0.75rem; }
  .feature-card .feature-icon { font-size: 1.5rem; margin-bottom: 6px; }
  .feature-card-title { font-size: 0.6875rem; }
  .feature-card-desc { font-size: 0.625rem; line-height: 1.3; max-height: 2.6em; overflow: hidden; }
  .scenario-card-title { font-size: 0.6875rem; }
  .hero-card-title { font-size: 0.9375rem; }
  .case-card { flex: 0 0 240px; }
  .faq-panel { margin-bottom: 0; }
  .footer-grid { grid-template-columns: 1fr 1fr; }
  .footer-col:nth-child(3) { grid-column: 1 / -1; }
  .site-footer { padding: 32px 16px 24px; margin-top: 24px; }
  .footer-bottom { flex-direction: column; gap: 8px; text-align: center; }
}
</style>
