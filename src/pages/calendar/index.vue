<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- 页面头部 -->
      <section class="calendar-hero">
        <view class="section-tag">专属日历</view>
        <view class="calendar-hero-title">个人专属运势日历</view>
        <view class="calendar-hero-desc">逐日查看黄历宜忌、干支五行、神位月相，择吉避凶参考一目了然</view>
      </section>

      <!-- 日历主体 -->
      <section class="section">
        <view class="calendar-card">
          <!-- 月历导航 -->
          <view class="cal-nav">
            <view class="cal-nav-btn" @tap="calPrev">◂</view>
            <text class="cal-nav-title">{{ calTitle }}</text>
            <view class="cal-nav-btn" @tap="calToday">今天</view>
            <view class="cal-nav-btn" @tap="calNext">▸</view>
          </view>
          <!-- 加载中 -->
          <view class="cal-grid" id="calLoadingMsg" style="display:none">
            <view style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-3);">加载中...</view>
          </view>
          <!-- 月历网格（DOM渲染） -->
          <view class="cal-grid" id="calGrid" style="display:none">
            <!-- 星期头（静态，Vue初次渲染正常） -->
            <view class="cal-wk" v-for="(w, i) in weekdays" :key="'wk'+i" :id="'calWk' + i">{{ w }}</view>
            <!-- 网格内容通过DOM注入到此容器 -->
            <view id="calGridContent" style="display:contents"></view>
          </view>
          <!-- 日期详情面板（DOM渲染） -->
          <view class="cal-detail" id="calDetail" style="display:none">
            <view class="cal-detail-header">
              <text class="cal-detail-date" id="calDetailDate"></text>
              <view class="cal-detail-close" @tap="closeCalDetail">✕</view>
            </view>
            <view class="cal-detail-grid" id="calDetailGrid"></view>
          </view>
          <view class="cal-disclaimer">⚠️ 日历内容仅为民俗文化参考，不构成任何决策建议</view>
        </view>
      </section>
    </view>



  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
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
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

// ═══ 日历核心数据 ═══
const weekdays = ['日', '一', '二', '三', '四', '五', '六']
const currentYear = ref(new Date().getFullYear())
const currentMonth = ref(new Date().getMonth() + 1)
const selectedDate = ref('')
const calMonthData = ref([])  // 从API获取的整月数据（保留ref以供调试）
const calLoading = ref(false)
let calDataCache = []  // DOM渲染数据缓存

const calTitle = computed(() => `${currentYear.value}年${currentMonth.value}月`)

// ═══ DOM渲染：月历网格（绕过Vue 3.4.21 render effect bug） ═══
function renderCalGrid(days, offset, todayStr) {
  var grid = document.getElementById('calGridContent')
  if (!grid) return
  var html = ''
  for (var i = 0; i < offset; i++) {
    html += '<div class="cal-cell empty"></div>'
  }
  for (var i = 0; i < days.length; i++) {
    var d = days[i]
    var cls = 'cal-cell'
    if (d.isToday) cls += ' today'
    if (d.solarDate === selectedDate.value) cls += ' selected'
    if (d.isWeekend) cls += ' weekend'
    var hasWx = d.wuXingColor && d.wuXingDay
    var wxStyle = hasWx ? 'color:' + d.wuXingColor + ';background:' + d.wuXingColor + '15;border:1px solid ' + d.wuXingColor + '30' : ''
    html += '<div class="' + cls + '" data-date="' + d.solarDate + '" onclick="window._calTap && window._calTap(\'' + d.solarDate + '\')">'
    html += '<span class="cal-solar">' + d.solarDay + '</span>'
    if (d.lunarDisplay) {
      html += '<span class="cal-lunar' + (d.lunarDay === 1 ? ' month-first' : '') + '">' + d.lunarDisplay + '</span>'
    }
    if (d.wuXingDay) {
      html += '<span class="cal-wx" style="' + wxStyle + '">' + d.wuXingDay + '</span>'
    }
    if (d.ganZhiDay) {
      html += '<span class="cal-gz">' + d.ganZhiDay + '</span>'
    }
    html += '</div>'
  }
  grid.innerHTML = html
}

// ═══ DOM渲染：日期详情面板 ═══
function renderCalDetail(d) {
  var detail = document.getElementById('calDetail')
  var dateEl = document.getElementById('calDetailDate')
  var gridEl = document.getElementById('calDetailGrid')
  if (!detail || !dateEl || !gridEl) return
  var weekdayNames = ['日', '一', '二', '三', '四', '五', '六']
  var dayOfWeek = new Date(d.solarDate).getDay()
  dateEl.textContent = d.solarDate + ' ' + weekdayNames[dayOfWeek] + '曜'
  var html = ''
  // 辅助函数：添加详情项
  function addItem(label, value, extraStyle) {
    if (value === undefined || value === null || value === '') return
    var valStyle = extraStyle ? ' style="' + extraStyle + '"' : ''
    html += '<div class="cal-detail-item"><span class="cal-detail-label">' + label + '</span><span class="cal-detail-value"' + valStyle + '>' + value + '</span></div>'
  }
  // 节气
  if (d.solarTerm) html += '<div class="cal-detail-item"><span class="cal-detail-label">节气</span><span class="cal-detail-value" style="color:var(--accent)">' + d.solarTerm + '</span></div>'
  // 公历节日
  if (d.gJie) html += '<div class="cal-detail-item"><span class="cal-detail-label">公历节日</span><span class="cal-detail-value">' + d.gJie + '</span></div>'
  // 农历节日
  if (d.lJie) html += '<div class="cal-detail-item"><span class="cal-detail-label">农历节日</span><span class="cal-detail-value">' + d.lJie + '</span></div>'
  // 农历
  html += '<div class="cal-detail-item"><span class="cal-detail-label">农历</span><span class="cal-detail-value">' + (d.lunarMonthName || '') + (d.lunarDayName || '') + '</span></div>'
  // 干支
  html += '<div class="cal-detail-item"><span class="cal-detail-label">干支年</span><span class="cal-detail-value">' + (d.ganZhiYear || '') + '</span></div>'
  html += '<div class="cal-detail-item"><span class="cal-detail-label">干支月</span><span class="cal-detail-value">' + (d.ganZhiMonth || '') + '</span></div>'
  html += '<div class="cal-detail-item"><span class="cal-detail-label">干支日</span><span class="cal-detail-value">' + (d.ganZhiDay || '') + '</span></div>'
  // 日干五行
  if (d.wuXingDay) html += '<div class="cal-detail-item"><span class="cal-detail-label">日干五行</span><span class="cal-detail-value" style="color:' + (d.wuXingColor || 'inherit') + '">' + d.wuXingDay + '</span></div>'
  // 纳音
  if (d.naYin) html += '<div class="cal-detail-item"><span class="cal-detail-label">纳音</span><span class="cal-detail-value">' + d.naYin + '</span></div>'
  // 建除
  if (d.jianChu) html += '<div class="cal-detail-item"><span class="cal-detail-label">建除</span><span class="cal-detail-value">' + d.jianChu + '</span></div>'
  // 冲煞
  if (d.chong || d.sha) html += '<div class="cal-detail-item"><span class="cal-detail-label">冲煞</span><span class="cal-detail-value">' + (d.chong || '') + ' ' + (d.sha || '') + '</span></div>'
  // 生肖
  if (d.shengXiao) html += '<div class="cal-detail-item"><span class="cal-detail-label">生肖</span><span class="cal-detail-value">' + d.shengXiao + '年</span></div>'
  // 宜
  if (d.yi && d.yi !== '日值岁破 大事不宜') html += '<div class="cal-detail-item"><span class="cal-detail-label">宜</span><span class="cal-detail-value" style="color:#228B22">' + d.yi + '</span></div>'
  // 忌
  if (d.ji && d.ji !== '日值岁破 大事不宜') html += '<div class="cal-detail-item"><span class="cal-detail-label">忌</span><span class="cal-detail-value" style="color:#DC143C">' + d.ji + '</span></div>'
  // 宜忌（岁破）
  if (d.yi === '日值岁破 大事不宜' || d.ji === '日值岁破 大事不宜') html += '<div class="cal-detail-item"><span class="cal-detail-label">宜忌</span><span class="cal-detail-value" style="color:#8B4513">日值岁破 大事不宜</span></div>'
  // 彭祖百忌
  if (d.pengZu) html += '<div class="cal-detail-item"><span class="cal-detail-label">彭祖百忌</span><span class="cal-detail-value">' + d.pengZu + '</span></div>'
  // 神位
  if (d.shenWei) html += '<div class="cal-detail-item"><span class="cal-detail-label">神位</span><span class="cal-detail-value" style="font-size:0.8em">' + d.shenWei + '</span></div>'
  // 月相
  if (d.moonName) html += '<div class="cal-detail-item"><span class="cal-detail-label">月相</span><span class="cal-detail-value">' + d.moonName + '</span></div>'
  gridEl.innerHTML = html
  detail.style.display = 'block'
  detail.classList.add('show')
}

function renderSkeletonGrid(y, m) {
  var loadingEl = document.getElementById('calLoadingMsg')
  var gridEl = document.getElementById('calGrid')
  var contentEl = document.getElementById('calGridContent')
  if (!gridEl || !contentEl) return
  if (loadingEl) loadingEl.style.display = 'none'
  gridEl.style.display = 'grid'

  var today = new Date()
  var todayStr = today.getFullYear() + '-' + String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0')
  var daysInMonth = new Date(y, m, 0).getDate()
  var offset = new Date(y, m - 1, 1).getDay()

  var skeletonDays = []
  for (var d = 1; d <= daysInMonth; d++) {
    var solarDate = y + '-' + String(m).padStart(2,'0') + '-' + String(d).padStart(2,'0')
    var dow = new Date(y, m - 1, d).getDay()
    skeletonDays.push({
      solarDate: solarDate,
      solarDay: String(d),
      isToday: solarDate === todayStr,
      isWeekend: dow === 0 || dow === 6,
      lunarDisplay: '', wuXingDay: '', ganZhiDay: '', wuXingColor: '',
      lunarDay: 0, lunarMonthName: '', lunarDayName: ''
    })
  }
  renderCalGrid(skeletonDays, offset, todayStr)
}

// ═══ API调用：获取整月黄历数据（带localStorage缓存） ═══
async function loadCalMonth(y, m) {
  currentYear.value = y
  currentMonth.value = m
  calLoading.value = true
  calMonthData.value = []

  // 立即渲染日期骨架（0延迟，用户立刻看到日历）
  renderSkeletonGrid(y, m)

  // 尝试从 localStorage 读取缓存
  var cacheKey = 'xc_cal_' + y + '_' + m
  var cached = null
  try { cached = JSON.parse(localStorage.getItem(cacheKey)) } catch(_) {}
  if (cached && cached.days && cached.expire > Date.now()) {
    renderMonthData(y, m, cached.days)
    calLoading.value = false
    return
  }

  try {
    const res = await uni.request({ url: '/api/huangli/month?year=' + y + '&month=' + m })
    const data = res.data
    if (data && data.days) {
      try { localStorage.setItem(cacheKey, JSON.stringify({ days: data.days, expire: Date.now() + 7200000 })) } catch(_) {}
      renderMonthData(y, m, data.days)
    }
  } catch (e) {
    console.error('日历数据加载失败', e)
  }
  calLoading.value = false
}

function renderMonthData(y, m, days) {
  const today = new Date()
  const todayStr = today.getFullYear() + '-' + String(today.getMonth()+1).padStart(2,'0') + '-' + String(today.getDate()).padStart(2,'0')
  calDataCache = days.map(function(d) {
    var dow = new Date(d.solarDate).getDay()
    return {
      ...d,
      solarDay: d.solarDate.split('-')[2],
      isToday: d.solarDate === todayStr,
      isWeekend: dow === 0 || dow === 6,
      lunarDisplay: d.lunarDisplay || (d.lunarDay === 1 ? (d.lunarMonthName || '') : (d.lunarDayName || '')),
    }
  })
  calMonthData.value = calDataCache
  var offset = new Date(y, m - 1, 1).getDay()
  renderCalGrid(calDataCache, offset, todayStr)
}

// ═══ 选中日期详情 ═══
function showCalDetail(d) {
  selectedDate.value = d.solarDate
  // 高亮选中的格子
  var cells = document.querySelectorAll('#calGridContent .cal-cell')
  for (var i = 0; i < cells.length; i++) {
    cells[i].classList.remove('selected')
    if (cells[i].getAttribute('data-date') === d.solarDate) {
      cells[i].classList.add('selected')
    }
  }
  renderCalDetail(d)
}

function closeCalDetail() {
  selectedDate.value = ''
  var detail = document.getElementById('calDetail')
  if (detail) { detail.style.display = 'none'; detail.classList.remove('show') }
}

// ═══ 月份导航 ═══
function calPrev() {
  let y = currentYear.value, m = currentMonth.value - 1
  if (m < 1) { m = 12; y-- }
  loadCalMonth(y, m)
  preloadAdjacent(y, m)
}
function calNext() {
  let y = currentYear.value, m = currentMonth.value + 1
  if (m > 12) { m = 1; y++ }
  loadCalMonth(y, m)
  preloadAdjacent(y, m)
}
function calToday() {
  const now = new Date()
  // 点击"今天"时清除当前月缓存以获取最新数据
  var key = 'xc_cal_' + now.getFullYear() + '_' + (now.getMonth() + 1)
  try { localStorage.removeItem(key) } catch(_) {}
  loadCalMonth(now.getFullYear(), now.getMonth() + 1)
}

// 后台预加载相邻月份，使切换月份时秒开
function preloadAdjacent(y, m) {
  var pairs = []
  var py = y, pm = m - 1; if (pm < 1) { pm = 12; py-- }
  pairs.push([py, pm])
  var ny = y, nm = m + 1; if (nm > 12) { nm = 1; ny++ }
  pairs.push([ny, nm])
  pairs.forEach(function(p) {
    var key = 'xc_cal_' + p[0] + '_' + p[1]
    try {
      var cached = JSON.parse(localStorage.getItem(key))
      if (cached && cached.expire > Date.now()) return
    } catch(_) {}
    uni.request({ url: '/api/huangli/month?year=' + p[0] + '&month=' + p[1], success: function(res) {
      if (res.data && res.data.days) {
        try { localStorage.setItem(key, JSON.stringify({ days: res.data.days, expire: Date.now() + 7200000 })) } catch(_) {}
      }
    }})
  })
}

// ═══ 页脚导航 ═══
function go(path) {
  // 判断是否tabBar页面
  const tabPaths = ['/pages/index/index', '/pages/qimen/index', '/pages/bazi-index/index', '/pages/tarot/index', '/pages/liuyao/index', '/pages/meihua/index', '/pages/ziwei/index', '/pages/zeji/index', '/pages/calendar/index', '/pages/community/index', '/pages/profile/index']
  if (tabPaths.includes(path)) {
    uni.switchTab({ url: path })
  } else {
    uni.navigateTo({ url: path })
  }
}
function goTab(path) {
  uni.switchTab({ url: path })
}

// ═══ 清空数据 ═══
function clearAllData() {
  uni.showModal({
    title: '确认清空',
    content: '确认清空所有本地数据？',
    success: (r) => {
      if (r.confirm) {
        var _savedTheme = uni.getStorageSync('xc_theme')
        uni.clearStorageSync()
        if (_savedTheme) uni.setStorageSync('xc_theme', _savedTheme)
        uni.showToast({ title: '已清空', icon: 'success' })
      }
    }
  })
}

// ═══ 注入全局CSS（绕过uni-app自动scoped） ═══
function injectCalendarCSS() {
  if (document.getElementById('calendar-global-css')) return
  var style = document.createElement('style')
  style.id = 'calendar-global-css'
  style.textContent = `
.calendar-hero{max-width:var(--max-w);margin:0 auto;padding:18px 24px 8px!important;text-align:center}
.calendar-hero-title{font-family:var(--font-serif);font-size:1.42rem!important;letter-spacing:3px;color:var(--text-1);margin-bottom:6px!important}
.calendar-hero-desc{font-size:0.82rem!important;color:var(--text-2);line-height:1.55!important;max-width:640px;margin:0 auto}
.section{max-width:var(--max-w);margin:0 auto;padding:8px 32px 24px!important}
.section-tag{display:inline-block;padding:3px 12px;border-radius:20px;font-size:0.66rem;letter-spacing:1.5px;color:var(--accent);background:var(--accent-glow);margin-bottom:8px}
.calendar-card{max-width:720px;margin:0 auto;background:var(--card-bg);border:1px solid var(--card-border);border-radius:var(--radius-lg);padding:14px 16px!important;backdrop-filter:blur(20px);box-shadow:var(--card-shadow)}
.cal-nav{display:flex;align-items:center;justify-content:space-between;margin-bottom:8px}
.cal-nav-btn{background:var(--input-bg);border:1px solid var(--card-border);border-radius:8px;padding:4px 12px;font-size:0.875rem;color:var(--text-2);transition:all 0.2s;cursor:pointer}
.cal-nav-btn:hover{border-color:var(--accent);color:var(--accent)}
.cal-nav-title{font-family:var(--font-serif);font-size:1rem;font-weight:600;color:var(--text-1);letter-spacing:2px}
.cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:2px;margin-bottom:10px!important}
#calLoadingMsg{display:none!important}
#calGrid{display:grid!important}
.cal-wk{text-align:center;font-size:0.66rem;color:var(--text-3);padding:4px 0;font-weight:600}
.cal-wk.weekend{color:var(--accent)}
.cal-cell{min-height:40px!important;border-radius:6px;display:flex;flex-direction:column;align-items:center;justify-content:flex-start;padding:2px!important;background:var(--input-bg);border:1px solid transparent;cursor:pointer;transition:all 0.15s;position:relative}
.cal-cell:hover{border-color:var(--accent);transform:translateY(-1px)}
.cal-cell.today{border-color:var(--accent);background:var(--accent-glow)}
.cal-cell.selected{border-color:var(--accent);background:var(--accent-glow);box-shadow:0 0 0 1px var(--accent)}
.cal-cell.empty{background:transparent;cursor:default}
.cal-cell.empty:hover{border-color:transparent;transform:none}
.cal-solar{font-size:0.86rem;font-weight:600;color:var(--text-1);line-height:1.1}
.cal-cell.weekend .cal-solar{color:var(--accent)}
.cal-lunar{font-size:0.52rem;color:var(--text-3);line-height:1.12;margin-top:1px}
.cal-lunar.month-first{color:var(--accent);font-weight:600}
.cal-wx{font-size:0.48rem;padding:0px 4px;border-radius:3px;margin-top:1px;line-height:1.25}
.cal-gz{font-size:0.48rem;color:var(--text-3);line-height:1.1;margin-top:1px}
.cal-jc{font-size:0.48rem;line-height:1.1;margin-top:1px;opacity:0.7}
.cal-detail{margin-top:8px;display:none;max-height:112px!important;overflow:auto}
.cal-detail.show{display:block}
.cal-detail-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px}
.cal-detail-date{font-family:var(--font-serif);font-size:1.08rem;font-weight:700;color:var(--text-1)}
.cal-detail-close{background:none;border:none;font-size:1.25rem;color:var(--text-3);cursor:pointer}
.cal-detail-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}
.cal-detail-item{padding:8px 12px;border-radius:8px;background:var(--input-bg)}
.cal-detail-label{font-size:0.6875rem;color:var(--text-3)}
.cal-detail-value{font-size:0.875rem;color:var(--text-1);font-weight:500;margin-top:2px}
.cal-disclaimer{text-align:center;margin-top:10px;font-size:0.72rem;color:var(--text-3)}
@media(max-width:768px){.calendar-hero{padding:24px 16px 14px}.calendar-hero-title{font-size:1.35rem;letter-spacing:2px}.calendar-hero-desc{font-size:0.8125rem}.section{padding:24px 16px 36px}.cal-detail-grid{grid-template-columns:1fr}}
@media(max-width:480px){.calendar-hero{padding:24px 16px 16px}.calendar-hero-title{font-size:1.25rem;margin-bottom:8px}.calendar-hero-desc{font-size:0.75rem}.section{padding:20px 16px}.calendar-card{padding:16px}.cal-nav{margin-bottom:8px}.cal-nav-btn{font-size:0.75rem;padding:3px 8px}.cal-nav-title{font-size:0.875rem}}
body:not(.home-fixed-page) .calendar-hero{padding:18px 0 8px!important}
body:not(.home-fixed-page) .calendar-hero-title{font-size:1.42rem!important;margin-bottom:6px!important}
body:not(.home-fixed-page) .calendar-hero-desc{font-size:0.82rem!important;line-height:1.55!important}
body:not(.home-fixed-page) .calendar-card{padding:14px 16px!important}
body:not(.home-fixed-page) .cal-cell{min-height:40px!important;padding:2px!important}
body:not(.home-fixed-page) .cal-detail{max-height:112px!important;overflow:auto!important}
@media(max-width:768px){body:not(.home-fixed-page) .calendar-hero{padding:24px 16px 14px!important}body:not(.home-fixed-page) .cal-cell{min-height:54px!important}}
@media(max-width:480px){body:not(.home-fixed-page) .calendar-hero{padding:20px 14px 12px!important}body:not(.home-fixed-page) .cal-cell{min-height:46px!important}}
`
  document.head.appendChild(style)
}

// ═══ 初始化 ═══
var _calInitDate = new Date().toDateString()

onShow(() => {
  var t = uni.getStorageSync('xc_theme')
  if (t && t !== theme.value) {
    theme.value = t
    try {
      document.documentElement.setAttribute('data-theme', t)
      document.body.setAttribute('data-theme', t)
    } catch(_) {}
  }
  var nowDate = new Date().toDateString()
  if (nowDate !== _calInitDate) {
    _calInitDate = nowDate
    calToday()
  }
})

onMounted(() => {
  injectCalendarCSS()
  const now = new Date()
  document.querySelectorAll('.cal-wk').forEach(function(el, i) {
    if (i === 0 || i === 6) el.classList.add('weekend')
  })
  window._calTap = function(solarDate) {
    var found = null
    for (var i = 0; i < calDataCache.length; i++) {
      if (calDataCache[i].solarDate === solarDate) { found = calDataCache[i]; break }
    }
    if (found) showCalDetail(found)
  }
  loadCalMonth(now.getFullYear(), now.getMonth() + 1)
  setTimeout(function() {
    preloadAdjacent(now.getFullYear(), now.getMonth() + 1)
  }, 100)

  setTimeout(function() {
    var closeBtn = document.querySelector('.cal-detail-close')
    if (closeBtn) closeBtn.addEventListener('click', function(e) { if (e._xcHandled) return; e._xcHandled = true; closeCalDetail() })
    var footerMap = {
      '/package-info/about/index': function() { go('/package-info/about/index') },
      '/pages/qimen/index': function() { goTab('/pages/qimen/index') },
      '/pages/bazi-index/index': function() { go('/pages/bazi-index/index') },
      '/pages/calendar/index': function() { go('/pages/calendar/index') }
    }
    document.querySelectorAll('.footer-link').forEach(function(el) {
      el.addEventListener('click', function(e) {
        if (e._xcHandled) return; e._xcHandled = true
        var txt = el.textContent.trim()
        for (var path in footerMap) {
          if (el.getAttribute('data-path') === path || txt.indexOf('奇门') >= 0 && path.indexOf('qimen') >= 0 || txt.indexOf('八字') >= 0 && path.indexOf('bazi') >= 0 || txt.indexOf('日历') >= 0 && path.indexOf('calendar') >= 0 || txt.indexOf('关于') >= 0 && path.indexOf('about') >= 0) {
            footerMap[path](); return
          }
        }
      })
    })
    var clearBtn = document.querySelector('.btn-clear-data')
    if (clearBtn) clearBtn.addEventListener('click', function(e) { if (e._xcHandled) return; e._xcHandled = true; clearAllData() })
  }, 0)
})
</script>

<style>
/* ═══ CSS变量 + 页面布局（仅Vue模板元素用，编译器会加data-v） ═══ */
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }

.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }

/* 弹窗 */
.modal-overlay { display: none; position: fixed; inset: 0; z-index: 300; background: rgba(0,0,0,0.55); backdrop-filter: blur(8px); align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 20px; padding: 32px; width: 360px; backdrop-filter: blur(40px); box-shadow: 0 16px 48px rgba(0,0,0,0.35); }
.modal-title { font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px; text-align: center; margin-bottom: 24px; color: var(--text-1); }
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }
.btn { padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; cursor: pointer; border: none; display: inline-flex; align-items: center; justify-content: center; }
.btn-outline { background: transparent; border: 1px solid var(--card-border); color: var(--text-2); }
.btn-accent { background: var(--accent); color: #fff; }
</style>
