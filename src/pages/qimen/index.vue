<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- 页面头部 -->
      <section class="tool-hero">
        <view class="tool-hero-content">
          <view class="section-tag">奇门遁甲</view>
          <view class="tool-hero-title">奇门遁甲 · 预判当下事件与吉凶走向</view>
          <view class="tool-hero-desc">一事一断 · 吉凶预判 · 择时择方 · 趋吉避凶</view>
        </view>
      </section>

      <!-- 工具面板 -->
      <section class="section">
        <view class="tool-container" :class="{ 'has-qimen-result': qfResult }">

          <!-- Tab 切换 -->
          <view class="tool-tabs">
            <view class="tool-tab" id="qiTabFree" :class="{ active: activeTab === 'free' }" @click="switchQiTab('free')" @tap="switchQiTab('free')">
              ☯️ 奇门排盘<text class="tab-badge free">免费</text>
            </view>
            <view v-if="false" class="tool-tab" id="qiTabAi" :class="{ active: activeTab === 'ai' }" @click="switchQiTab('ai')" @tap="switchQiTab('ai')">
              🔮 时安奇门系统<text class="tab-badge">PRO</text>
            </view>
          </view>

          <!-- ══ 奇门排盘（免费） ══ -->
          <view class="tool-tab-content" id="qiTabFreeContent" v-show="activeTab === 'free'">
            <view class="qf-form">
              <!-- 起局时间 -->
              <view class="qf-datetime-section">
                <view class="qf-section-header">
                  <text class="form-label">🕐 起局时间</text>
                  <view class="qf-now-btn-sm" @tap="qfSetNow">今</view>
                </view>
                <view class="qf-datetime-row">
                  <view class="qf-dt-col">
                    <select id="qf-year" class="qf-datetime-select"></select>
                  </view>
                  <view class="qf-dt-col">
                    <select id="qf-month" class="qf-datetime-select"></select>
                  </view>
                  <view class="qf-dt-col">
                    <select id="qf-day" class="qf-datetime-select"></select>
                  </view>
                  <view class="qf-dt-col">
                    <select id="qf-hour" class="qf-datetime-select"></select>
                  </view>
                  <view class="qf-dt-col qf-dt-col-narrow">
                    <select id="qf-minute" class="qf-datetime-select"></select>
                  </view>
                </view>
              </view>

              <!-- 排盘方式 -->
              <view class="qf-options-row">
                <view class="form-group">
                  <text class="form-label">排盘方式</text>
                  <select id="qf-pantype" class="qf-pantype-select"></select>
                </view>
              </view>
            </view>

            <view class="submit-btn" @tap="qimenFreePaipan" style="margin-top:14px;">☯️ 免费排盘</view>
            <text class="form-hint" style="text-align:center;display:block;margin-top:10px;">本地精准排盘，不含 AI 解读。深度解读请回首页选择奇门遁甲或自动选术数。</text>

            <!-- 排盘结果 -->
            <view class="qf-result" v-if="qfResult" v-html="qfResult"></view>
          </view>

          <!-- ══ 奇门AI系统 ══ -->
          <view v-if="false" class="tool-tab-content" id="qiTabAiContent" v-show="activeTab === 'ai'">
            <view id="qiAiFormArea">
              <view class="qf-datetime-section">
                <view class="qf-section-header">
                  <text class="form-label">🕐 起局时间</text>
                  <view class="qf-now-btn-sm" @tap="qaiSetNow">今</view>
                </view>
                <view class="qf-datetime-row">
                  <view class="qf-dt-col">
                    <select id="qai-year" class="qf-datetime-select"></select>
                  </view>
                  <view class="qf-dt-col">
                    <select id="qai-month" class="qf-datetime-select"></select>
                  </view>
                  <view class="qf-dt-col">
                    <select id="qai-day" class="qf-datetime-select"></select>
                  </view>
                  <view class="qf-dt-col">
                    <select id="qai-hour" class="qf-datetime-select"></select>
                  </view>
                  <view class="qf-dt-col qf-dt-col-narrow">
                    <select id="qai-minute" class="qf-datetime-select"></select>
                  </view>
                </view>
              </view>

              <view class="form-group">
                <text class="form-label">你的问题（选填）</text>
                <view id="qaiQuestion-wrap" class="dom-input-wrap"></view>
              </view>

              <view class="advanced-fields" :class="{ show: showAdvanced }">
                <view class="form-row">
                  <view class="form-group">
                    <text class="form-label">局法</text>
                    <select id="qai-ju" class="form-select-picker"></select>
                  </view>
                  <view class="form-group">
                    <text class="form-label">排盘流派</text>
                    <select id="qai-school" class="form-select-picker"></select>
                  </view>
                </view>
              </view>
              <view class="advanced-toggle" @tap="showAdvanced = !showAdvanced">{{ showAdvanced ? '▼ 收起高级选项' : '▶ 高级选项' }}</view>

              <view class="qai-deep-row">
                <label class="qai-deep-toggle" id="qiDeepToggle" :class="{ active: deepMode }" @tap="toggleQiDeepMode()">
                  <text class="qai-toggle-label">深度分析</text>
                  <view class="qai-toggle-track"><view class="qai-toggle-knob"></view></view>
                </label>
              </view>

              <view class="btn-row">
                <view class="submit-btn" :class="{ disabled: qaiLoading }" @click="qimenAskPaipan" @tap="qimenAskPaipan">🔮 一键起局 · 深度解读</view>
                <view class="btn btn-ghost" @tap="qaiReset">🔄 重新问策</view>
              </view>
            </view>

            <!-- 流式解读区域 -->
            <view class="qai-stream-box" id="qiStreamBox" style="display:none;">
              <view class="chat-container" id="qaiChatContainer"></view>
            </view>

            <!-- 追问输入栏 -->
            <view class="chat-input-bar" id="qaiChatInputBar" style="display:none;">
              <input class="chat-input" id="qaiChatInput" placeholder="继续追问..." />
              <view class="chat-send-btn" onclick="window.qaiSendFollowUp()">发送</view>
            </view>

          </view>
        </view>
      </section>
    </view>



  </view>
</template>

<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  uni.setStorageSync('xc_theme', theme.value)
  try {
    document.documentElement.setAttribute('data-theme', theme.value)
    document.body.setAttribute('data-theme', theme.value)
    const root = document.querySelector('.page-root')
    if (root) root.setAttribute('data-theme', theme.value)
    const icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = theme.value === 'dark' ? '🌙' : '☀️'
  } catch(_) {}
}

const mobileMenuOpen = ref(false)
const submenuOpen = ref({ qimen: false, bazi: false, more: false })
function openMobileMenu() { mobileMenuOpen.value = true }
function closeMobileMenu() { mobileMenuOpen.value = false }
function toggleSubmenu(key) { submenuOpen.value[key] = !submenuOpen.value[key] }

const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

function releaseQimenPageScroll() {
  // 从固定首页切到奇门时，确保移动端恢复普通页面滚动。
  // #ifdef H5
  try {
    document.documentElement.classList.remove('home-fixed-page')
    document.body.classList.remove('home-fixed-page')
    document.documentElement.classList.add('qimen-page-active')
    document.body.classList.add('qimen-page-active')
    var wrappers = document.querySelectorAll('uni-page-wrapper')
    for (var i = 0; i < wrappers.length; i++) {
      var el = wrappers[i]
      var rect = el.getBoundingClientRect()
      if (rect.width > 0 && rect.height > 0) {
        el.style.overflowY = 'auto'
        el.style.webkitOverflowScrolling = 'touch'
      }
    }
  } catch(_) {}
  // #endif
}

// Tab切换
const activeTab = ref('free')

// 年/月/日选项（与Flask原版5个独立picker一致）
const yearOptions = Array.from({ length: 111 }, (_, i) => 1940 + i)
const yearLabels = yearOptions.map(y => y + '年')
const monthOptions = Array.from({ length: 12 }, (_, i) => i + 1)
const monthLabels = monthOptions.map(m => m + '月')

function getDaysInMonth(year, month) {
  return new Date(year, month, 0).getDate()
}
function getDayOptions(year, month) {
  if (!year || !month) return Array.from({ length: 31 }, (_, i) => i + 1)
  const max = getDaysInMonth(year, month)
  return Array.from({ length: max }, (_, i) => i + 1)
}
function getDayLabels(year, month) {
  return getDayOptions(year, month).map(d => d + '日')
}

// 小时选项使用具体时间，避免用户看到传统时辰。
const hourOptions = Array.from({ length: 24 }, (_, i) => String(i).padStart(2, '0') + '时')
const hourValues = Array.from({ length: 24 }, (_, i) => i)
const minuteOptions = Array.from({ length: 60 }, (_, i) => String(i).padStart(2, '0') + '分')

// 免费排盘 - 5个独立picker（默认当前时间）
const _initNow = new Date()
const qfYearIdx = ref(yearOptions.indexOf(_initNow.getFullYear()))
const qfMonthIdx = ref(_initNow.getMonth())
const qfDayOptions = ref(getDayOptions(_initNow.getFullYear(), _initNow.getMonth() + 1))
const qfDayLabels = ref(getDayLabels(_initNow.getFullYear(), _initNow.getMonth() + 1))
const qfDayIdx = ref(_initNow.getDate() - 1)
function _initHourIdx(h) { return Math.max(0, Math.min(23, parseInt(h, 10) || 0)) }
const qfHourIdx = ref(_initHourIdx(_initNow.getHours()))
const qfMinuteIdx = ref(_initNow.getMinutes())
const qfPanTypeIdx = ref(0); const qfResult = ref('')

function qfOnDateChange() {
  const year = qfYearIdx.value >= 0 ? yearOptions[qfYearIdx.value] : 0
  const month = qfMonthIdx.value >= 0 ? monthOptions[qfMonthIdx.value] : 0
  qfDayOptions.value = getDayOptions(year, month)
  qfDayLabels.value = getDayLabels(year, month)
  if (qfDayIdx.value >= qfDayOptions.value.length) {
    qfDayIdx.value = qfDayOptions.value.length - 1
  }
}

// watch 处理联动 + H5原生DOM同步
watch([qfYearIdx, qfMonthIdx], () => {
  qfOnDateChange()
  nextTick(() => { try { _refillDaySelect('qf-day', qfDayLabels.value, qfDayIdx) } catch(e) {} })
})
// qai相关watch移到变量定义之后（qaiYearIdx等在line 527+定义）

function qfSetNow() {
  const now = new Date()
  const y = now.getFullYear(); const m = now.getMonth() + 1; const d = now.getDate()
  qfYearIdx.value = yearOptions.indexOf(y)
  qfMonthIdx.value = m - 1
  qfDayOptions.value = getDayOptions(y, m)
  qfDayLabels.value = getDayLabels(y, m)
  qfDayIdx.value = d - 1
  qfHourIdx.value = _initHourIdx(now.getHours())
  qfMinuteIdx.value = now.getMinutes()
  // 同步DOM select（使用try-catch避免预处理器问题）
  nextTick(() => {
    try { _syncSelectValue('qf-year', qfYearIdx.value) } catch(e) {}
    try { _syncSelectValue('qf-month', qfMonthIdx.value) } catch(e) {}
    try { _refillDaySelect('qf-day', qfDayLabels.value, qfDayIdx) } catch(e) {}
    try { _syncSelectValue('qf-hour', qfHourIdx.value) } catch(e) {}
    try { _syncSelectValue('qf-minute', qfMinuteIdx.value) } catch(e) {}
  })
}

async function qimenFreePaipan() {
  if (qfYearIdx.value < 0 || qfMonthIdx.value < 0 || qfDayIdx.value < 0) {
    uni.showToast({ title: '请选择起局时间', icon: 'none' }); return
  }
  const y = yearOptions[qfYearIdx.value]
  const m = monthOptions[qfMonthIdx.value]
  const d = qfDayOptions.value[qfDayIdx.value]
  const h = hourValues[qfHourIdx.value]
  const min = parseInt(minuteOptions[qfMinuteIdx.value] || '0')
  const panType = [2, 3][qfPanTypeIdx.value]
  try {
    const res = await uni.request({ url: '/api/qimen/paipan', method: 'POST', data: { year: y, month: m, day: d, hour: h, minute: min, panType } })
    const data = res.data
    if (data.error) { qfResult.value = `<div style="color:var(--danger);padding:16px;">${data.error}</div>`; return }
    qfResult.value = renderQimenPalaceGrid(data)
  } catch (e) { qfResult.value = `<div style="color:var(--danger);padding:16px;">排盘失败</div>` }
}

// ═══ 九宫格渲染（1:1复刻Flask home.js renderQimenPalaceGrid）═══
function renderQimenPalaceGrid(data) {
  const fp = data.fourPillars || {}
  const palaces = data.palaces || []
  const dayGan = data.dayGan || data.dayGan || ''
  const hourGan = data.hourGan || data.hourGan || ''
  const luoOrder = [4, 9, 2, 3, 5, 7, 8, 1, 6]
  const C_ZHIFU = '#27AE60', C_ZHISHI = '#27AE60', C_RUMU = '#8B4513', C_JIXING = '#9B59B6'
  const C_MENPO = '#E74C3C', C_XINGMU = '#2980B9', C_DEFAULT = '#222', C_KONG = '#444'
  const C_RIGAN = '#E74C3C', C_SHIGAN = '#E74C3C', C_DIGAN = '#555', C_YINGAN = '#AAA', C_MAHORSE = '#D4A017'
  const zhiFuStar = data.zhiFuStar || ''; const zhiShiMen = data.zhiShiMen || ''
  const baguaSimple = {'坎':'坎','坤':'坤','震':'震','巽':'巽','中':'中','乾':'乾','兌':'兑','艮':'艮','離':'离'}
  let html = `<div class="qf-result-card">`
  // 概要信息区
  html += `<div style="margin-bottom:16px;border-bottom:1px solid var(--card-border);padding-bottom:12px;">`
  html += `<div style="font-size:1.1rem;font-weight:700;margin-bottom:10px;color:var(--accent);letter-spacing:2px;">奇门遁甲排盘</div>`
  html += `<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.82rem;color:var(--text-2);margin-bottom:6px;">`
  html += `<span><b style="color:var(--text-1);">盘式：</b>转盘奇门 · ${data.panType || '拆补法'}</span>`
  if (data.solarDate) html += `<span><b style="color:var(--text-1);">时间：</b>${data.solarDate}</span>`
  html += `</div>`
  html += `<div style="display:flex;flex-wrap:wrap;gap:6px 14px;font-size:0.82rem;margin-bottom:6px;">`
  if (fp.year) html += `<span><b style="color:var(--text-1);">年柱</b> ${fp.year}</span>`
  if (fp.month) html += `<span><b style="color:var(--text-1);">月柱</b> ${fp.month}</span>`
  if (fp.day) html += `<span><b style="color:var(--text-1);">日柱</b> ${fp.day}</span>`
  if (fp.hour) html += `<span><b style="color:var(--text-1);">时柱</b> ${fp.hour}</span>`
  html += `</div>`
  const xk = data.xunKong || data.xunkong || {}
  if (xk.day || xk.hour) {
    html += `<div style="font-size:0.82rem;margin-bottom:6px;"><b style="color:var(--text-1);">旬空：</b>`
    if (xk.day) html += `日空${xk.day}`
    if (xk.day && xk.hour) html += ` `
    if (xk.hour) html += `时空${xk.hour}`
    html += `</div>`
  }
  html += `<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.82rem;margin-bottom:6px;">`
  if (data.solarTerm) html += `<span><b style="color:var(--text-1);">节气：</b>${data.solarTerm}</span>`
  if (data.ju) html += `<span><b style="color:var(--text-1);">局数：</b>${data.ju}</span>`
  if (data.xunShou) html += `<span><b style="color:var(--text-1);">旬首：</b>${data.xunShou}</span>`
  html += `</div>`
  html += `<div style="display:flex;flex-wrap:wrap;gap:6px 16px;font-size:0.82rem;">`
  if (data.zhiFu) html += `<span style="font-weight:600;"><b>值符：</b>${data.zhiFu}</span>`
  if (data.zhiShi) html += `<span style="font-weight:600;"><b>值使：</b>${data.zhiShi}</span>`
  if (data.tianYi) html += `<span style="font-weight:500;"><b>天乙：</b>${data.tianYi}</span>`
  const mx = data.maXing || {}
  const maList = []
  if (mx['驛馬'] || mx['驿马']) maList.push('驿马→' + (mx['驛馬']||mx['驿马']))
  if (mx['丁馬'] || mx['丁马']) maList.push('丁马→' + (mx['丁馬']||mx['丁马']))
  if (mx['天馬'] || mx['天马']) maList.push('天马→' + (mx['天馬']||mx['天马']))
  if (maList.length) html += `<span><b style="color:var(--text-1);">马星：</b>${maList.join(' ')}</span>`
  html += `</div></div>`
  // 九宫格
  html += `<div class="qm-scale-shell"><div class="qm-palace-grid">`
  for (const gongNum of luoOrder) {
    const p = palaces[gongNum - 1]
    if (!p) { html += `<div class="qm-palace-cell qm-empty-cell"></div>`; continue }
    if (gongNum === 5) {
      const WX_GAN = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土','己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
      const WX_ZHI = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
      const WX_COLOR = {'木':'#27AE60','火':'#E74C3C','土':'#8B6914','金':'#B8860B','水':'#2980B9'}
      function wxColor(ch) { const wx = WX_GAN[ch] || WX_ZHI[ch]; return wx ? WX_COLOR[wx] : C_DEFAULT }
      function wxSpan(text) { let s = ''; for (const c of text) { const clr = wxColor(c); const w = (clr === C_DEFAULT) ? '500' : '700'; s += `<span style="color:${clr};font-weight:${w};">${c}</span>` } return s }
      const XUN_MAP = {'戊':'甲子','己':'甲戌','庚':'甲申','辛':'甲午','壬':'甲辰','癸':'甲寅'}
      const NUM_CN = ['','一','二','三','四','五','六','七','八','九']
      const BAGUA_NUM = {'坎':1,'坤':2,'震':3,'巽':4,'中':5,'乾':6,'兑':7,'艮':8,'离':9}
      const xunRaw = XUN_MAP[data.xunShou] || ''
      const xkHour = (data.xunKong && data.xunKong.hour) || ''
      const fp5 = data.fourPillars || {}
      const juRaw = data.ju || ''
      const ydMatch = juRaw.match(/([阳阴]遁)/)
      const juNumMatch = juRaw.match(/[一二三四五六七八九十\d]+/)
      const juNumCn = juNumMatch ? juNumMatch[0] : ''
      const juYuanMatch = juRaw.match(/(上元|中元|下元)/)
      const juYuan = juYuanMatch ? juYuanMatch[0] : ''
      const ydStr = ydMatch ? ydMatch[1] : ''
      const cn2num = {'一':'1','二':'2','三':'3','四':'4','五':'5','六':'6','七':'7','八':'8','九':'9','十':'10'}
      const juNumArab = cn2num[juNumCn] || juNumCn
      const juDisplay = ydStr ? `${ydStr}${juNumArab}局` : juRaw
      const zhiFuNum = BAGUA_NUM[data.zhiFuGong] || 5
      const zhiShiNum = BAGUA_NUM[data.zhiShiGong] || 2
      const FS_C = 'var(--qm-center-font)', FS_S = 'var(--qm-center-small-font)'
      html += `<div class="qm-palace-cell qm-center-cell" style="color:${C_DEFAULT};font-size:${FS_C};">`
      const dateStr = (data.solarDate || '').split(' ')[0]
      if (dateStr) html += `<div style="font-weight:700;font-size:var(--qm-center-date-font);">${dateStr}</div>`
      html += `<div>${wxSpan(xunRaw + '旬')}`
      if (xkHour) html += ` ${wxSpan(xkHour)}<span style="color:${C_DEFAULT};">空</span>`
      html += `</div>`
      const zhuArr = []; const zhuLabels = ['年','月','日','时']
      ;['year','month','day','hour'].forEach((k,i) => { const v = fp5[k]; if (v) zhuArr.push(wxSpan(v) + `<span style="color:${C_DEFAULT};font-weight:400;">${zhuLabels[i]}</span>`) })
      html += `<div style="font-size:${FS_S};">${zhuArr.join(' ')}</div>`
      html += `<div style="font-weight:600;">${data.solarTerm || ''} ${juYuan} ${juDisplay}</div>`
      html += `<div>值符天${data.zhiFuStar || ''}落${NUM_CN[zhiFuNum]}宫</div>`
      html += `<div>值使${(data.zhiShiMen || '') + '门'}落${NUM_CN[zhiShiNum]}宫</div>`
      html += `</div>`; continue
    }
    const xingArr = Array.isArray(p.xing) ? p.xing : (p.xing ? [p.xing] : [])
    const tianGanArr = Array.isArray(p.tianGan) ? p.tianGan : (p.tianGan ? [p.tianGan] : [])
    const diGanArr = Array.isArray(p.diGan) ? p.diGan : (p.diGan ? [p.diGan] : [])
    const xingFullArr = Array.isArray(p.xingFull) ? p.xingFull : (p.xingFull ? [p.xingFull] : [])
    const isZhiFu = xingArr.includes(zhiFuStar)
    const isZhiShi = (p.men === zhiShiMen)
    const hasMenPo = p.isMenPo
    const jiXingTianSet = new Set(p.jiXingTianGans || [])
    const jiXingDiSet = new Set(p.jiXingDiGans || [])
    const ruMuTianSet = new Set(p.ruMuTianGans || [])
    const ruMuDiSet = new Set(p.ruMuDiGans || [])
    const shenColor = C_DEFAULT; const shenWeight = '500'
    const xingColor = isZhiFu ? C_ZHIFU : C_DEFAULT; const xingWeight = isZhiFu ? '700' : '500'
    let menColor = C_DEFAULT; let menWeight = '500'
    if (isZhiShi) { menColor = C_ZHISHI; menWeight = '700' }
    if (hasMenPo) { menColor = C_MENPO; menWeight = '700' }
    let tianHtml = ''; tianGanArr.filter(Boolean).forEach(g => { let c = C_DEFAULT, w = '400'; if (jiXingTianSet.has(g)) { c = C_JIXING; w = '700' } else if (ruMuTianSet.has(g)) { c = C_RUMU; w = '700' }; tianHtml += `<span class="qm-heaven-stem" style="color:${c};font-weight:${w};">${g}</span>` })
    let diHtml = ''; diGanArr.filter(Boolean).forEach(g => { let c = C_DIGAN, w = '400'; if (jiXingDiSet.has(g)) { c = C_JIXING; w = '700' } else if (ruMuDiSet.has(g)) { c = C_RUMU; w = '700' }; diHtml += `<span style="color:${c};font-weight:${w};">${g}</span>` })
    const gongLabel = `${gongNum}·${baguaSimple[p.bagua]||p.bagua}`
    const FS = 'var(--qm-cell-font)'
    html += `<div class="qm-palace-cell" style="color:${C_DEFAULT};">`
    html += `<div style="display:flex;justify-content:space-between;align-items:center;">`
    html += `<span style="color:${shenColor};font-weight:${shenWeight};font-size:${FS};white-space:nowrap;">${p.shenFull||''}${p.isKong?`<span style="color:${C_KONG};font-size:0.6rem;font-weight:700;margin-left:2px;">○</span>`:''}</span>`
    html += `<span class="qm-tian-gan" style="font-size:${FS};">${p.isMa?`<span class="qm-ma-marker" style="color:${C_MAHORSE};">🐎</span>`:''}${tianHtml}</span></div>`
    html += `<div style="display:flex;justify-content:space-between;align-items:center;">`
    const xingDisplay = xingFullArr.length > 1 ? xingArr.filter(Boolean).join("") : xingFullArr.filter(Boolean).join("")
    html += `<span style="color:${xingColor};font-weight:${xingWeight};font-size:${FS};white-space:nowrap;">${xingDisplay}</span>`
    html += `<span style="font-size:${FS};white-space:nowrap;">${diHtml}</span></div>`
    html += `<div style="display:flex;justify-content:space-between;align-items:center;">`
    const isDayYin = dayGan && p.yinGan === dayGan
    const isHourYin = hourGan && p.yinGan === hourGan
    let yinColor = C_YINGAN; let yinWeight = '400'
    html += `<span style="white-space:nowrap;">${p.menFull?`<span style="color:${menColor};font-weight:${menWeight};font-size:${FS};">${p.menFull}</span>`:''}</span>`
    html += `<span style="color:${yinColor};font-weight:${yinWeight};font-size:${FS};white-space:nowrap;">${p.yinGan||''}</span></div>`
    html += `<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);font-size:0.45rem;color:#d0d0d0;font-weight:400;pointer-events:none;">${gongLabel}</div>`
    html += `</div>`
  }
  html += `</div></div>`
  html += `<div style="display:flex;flex-wrap:wrap;gap:4px 10px;margin-top:10px;font-size:0.65rem;color:var(--text-3);justify-content:center;align-items:center;">`
  html += `<span><span style="color:${C_ZHISHI};font-weight:700;">值使</span></span>`
  html += `<span><span style="color:${C_MENPO};font-weight:700;">门迫</span></span>`
  html += `<span><span style="color:${C_JIXING};font-weight:700;">击刑</span></span>`
  html += `<span><span style="color:${C_RUMU};font-weight:700;">入墓</span></span>`
  html += `<span><span style="color:${C_KONG};">○</span>空亡</span>`
  html += `<span><span style="color:${C_MAHORSE};">🐎</span>马星</span></div>`
  html += `<div style="text-align:center;font-size:0.65rem;color:var(--text-3);margin-top:8px;">⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议</div>`
  html += `</div>`
  return html
}

// AI问策
const qaiYearIdx = ref(yearOptions.indexOf(_initNow.getFullYear()))
const qaiMonthIdx = ref(_initNow.getMonth())
const qaiDayOptions = ref(getDayOptions(_initNow.getFullYear(), _initNow.getMonth() + 1))
const qaiDayLabels = ref(getDayLabels(_initNow.getFullYear(), _initNow.getMonth() + 1))
const qaiDayIdx = ref(_initNow.getDate() - 1)
const qaiHourIdx = ref(_initHourIdx(_initNow.getHours()))
const qaiMinuteIdx = ref(_initNow.getMinutes())
const qaiQuestion = ref(''); const showAdvanced = ref(false)
const qaiJuIdx = ref(0); const qaiSchoolIdx = ref(0)
const deepMode = ref(false); const resultMode = ref('simple')
const qaiLoading = ref(false); const qaiProgress = ref(0); const qaiStepText = ref('')
const qaiResult = ref('')

// qai 相关 watch（必须在变量定义之后）
watch([qaiYearIdx, qaiMonthIdx], () => {
  qaiOnDateChange()
  nextTick(() => { try { _refillDaySelect('qai-day', qaiDayLabels.value, qaiDayIdx) } catch(e) {} })
})
function qaiOnDateChange() {
  const year = qaiYearIdx.value >= 0 ? yearOptions[qaiYearIdx.value] : 0
  const month = qaiMonthIdx.value >= 0 ? monthOptions[qaiMonthIdx.value] : 0
  qaiDayOptions.value = getDayOptions(year, month)
  qaiDayLabels.value = getDayLabels(year, month)
  if (qaiDayIdx.value >= qaiDayOptions.value.length) {
    qaiDayIdx.value = qaiDayOptions.value.length - 1
  }
}

function qaiSetNow() {
  const now = new Date()
  const y = now.getFullYear(); const m = now.getMonth() + 1; const d = now.getDate()
  qaiYearIdx.value = yearOptions.indexOf(y)
  qaiMonthIdx.value = m - 1
  qaiDayOptions.value = getDayOptions(y, m)
  qaiDayLabels.value = getDayLabels(y, m)
  qaiDayIdx.value = d - 1
  qaiHourIdx.value = _initHourIdx(now.getHours())
  qaiMinuteIdx.value = now.getMinutes()
  nextTick(() => {
    try { _syncSelectValue('qai-year', qaiYearIdx.value) } catch(e) {}
    try { _syncSelectValue('qai-month', qaiMonthIdx.value) } catch(e) {}
    try { _refillDaySelect('qai-day', qaiDayLabels.value, qaiDayIdx) } catch(e) {}
    try { _syncSelectValue('qai-hour', qaiHourIdx.value) } catch(e) {}
    try { _syncSelectValue('qai-minute', qaiMinuteIdx.value) } catch(e) {}
  })
}

function qfReset() {
  const now = new Date()
  const y = now.getFullYear(); const m = now.getMonth() + 1
  qfYearIdx.value = yearOptions.indexOf(y)
  qfMonthIdx.value = m - 1
  qfDayOptions.value = getDayOptions(y, m)
  qfDayLabels.value = getDayLabels(y, m)
  qfDayIdx.value = now.getDate() - 1
  qfHourIdx.value = _initHourIdx(now.getHours())
  qfMinuteIdx.value = now.getMinutes()
  qfPanTypeIdx.value = 0; qfResult.value = ''
  nextTick(() => {
    try { _syncSelectValue('qf-year', qfYearIdx.value) } catch(e) {}
    try { _syncSelectValue('qf-month', qfMonthIdx.value) } catch(e) {}
    try { _refillDaySelect('qf-day', qfDayLabels.value, qfDayIdx) } catch(e) {}
    try { _syncSelectValue('qf-hour', qfHourIdx.value) } catch(e) {}
    try { _syncSelectValue('qf-minute', qfMinuteIdx.value) } catch(e) {}
    try { _syncSelectValue('qf-pantype', qfPanTypeIdx.value) } catch(e) {}
  })
}

function qaiReset() {
  // 清理轮询定时器 / 历史
  if (qaiPollTimer) { clearInterval(qaiPollTimer); qaiPollTimer = null }
  qaiPollCount = 0
  window._qaiChatHistory = []
  window._qaiPanTime = null
  const now = new Date()
  const y = now.getFullYear(); const m = now.getMonth() + 1
  qaiYearIdx.value = yearOptions.indexOf(y)
  qaiMonthIdx.value = m - 1
  qaiDayOptions.value = getDayOptions(y, m)
  qaiDayLabels.value = getDayLabels(y, m)
  qaiDayIdx.value = now.getDate() - 1
  qaiHourIdx.value = _initHourIdx(now.getHours()); qaiMinuteIdx.value = now.getMinutes()
  qaiQuestion.value = ''; qaiResult.value = ''; showAdvanced.value = false
  deepMode.value = false; resultMode.value = 'simple'
  var qaiInp = document.getElementById('qaiQuestion')
  if (qaiInp) qaiInp.value = ''
  var streamBox = document.getElementById('qiStreamBox')
  if (streamBox) streamBox.style.display = 'none'
  var chatContainer = document.getElementById('qaiChatContainer')
  if (chatContainer) chatContainer.innerHTML = ''
  var inputBar = document.getElementById('qaiChatInputBar')
  if (inputBar) inputBar.style.display = 'none'
  var deepEl = document.getElementById('qiDeepToggle')
  if (deepEl) deepEl.classList.remove('active')
  var simpleEl = document.getElementById('qiResultSimple')
  var proEl = document.getElementById('qiResultPro')
  if (simpleEl) simpleEl.classList.add('active')
  if (proEl) proEl.classList.remove('active')
  qaiLoading.value = false; qaiProgress.value = 0; qaiStepText.value = ''
  nextTick(() => {
    try { _syncSelectValue('qai-year', qaiYearIdx.value) } catch(e) {}
    try { _syncSelectValue('qai-month', qaiMonthIdx.value) } catch(e) {}
    try { _refillDaySelect('qai-day', qaiDayLabels.value, qaiDayIdx) } catch(e) {}
    try { _syncSelectValue('qai-hour', qaiHourIdx.value) } catch(e) {}
    try { _syncSelectValue('qai-minute', qaiMinuteIdx.value) } catch(e) {}
  })
}

// ═══ 奇门 SSE 流式解读 + 追问 ═══
window._qaiChatHistory = []
window._qaiPanTime = null

async function qimenAskPaipan() {
  if (qaiLoading.value) return
  const q = ((document.getElementById('qaiQuestion') || {}).value || '').trim()
  if (!q) {
    uni.showToast({ title: '请输入您的问题', icon: 'none' })
    return
  }
  if (qaiYearIdx.value < 0 || qaiMonthIdx.value < 0 || qaiDayIdx.value < 0) {
    uni.showToast({ title: '请选择起局时间', icon: 'none' }); return
  }

  // 清理旧状态
  qaiLoading.value = true
  qaiResult.value = ''
  window._qaiChatHistory = []
  var streamBox = document.getElementById('qiStreamBox')
  if (streamBox) streamBox.style.display = ''
  var chatContainer = document.getElementById('qaiChatContainer')
  if (chatContainer) chatContainer.innerHTML = ''
  var inputBar = document.getElementById('qaiChatInputBar')
  if (inputBar) inputBar.style.display = 'none'

  // 创建 AI 气泡
  var bubbleId = 'qaiBubble_' + Date.now()
  var bubbleHTML = '<div class="chat-bubble-ai" id="' + bubbleId + '">' +
    '<div class="ai-stage">🔗 正在连接 DeepSeek AI 引擎...</div>' +
    '<div class="ai-progress-bar"><div class="ai-progress-fill" style="width:20%"></div></div>' +
    '<div class="chat-bubble-content"></div></div>'
  if (chatContainer) chatContainer.innerHTML = bubbleHTML

  // 构建参数
  var y = yearOptions[qaiYearIdx.value]
  var m = monthOptions[qaiMonthIdx.value]
  var d = qaiDayOptions.value[qaiDayIdx.value]
  var h = hourValues[qaiHourIdx.value]
  var min = parseInt(minuteOptions[qaiMinuteIdx.value] || '0')
  var panType = [2, 3][qaiJuIdx.value]
  var type = 'general'
  window._qaiPanTime = { year: y, month: m, day: d, hour: h, minute: min, panType: panType }

  _qaiDoStreamSSE({
    bubbleId: bubbleId,
    url: '/api/qimen/ask/stream',
    body: { year: y, month: m, day: d, hour: h, minute: min, panType: panType, type: type, question: q, is_deep: deepMode.value },
    question: q,
    onDone: function(fullText) {
      window._qaiChatHistory = [
        { role: 'user', content: q },
        { role: 'assistant', content: fullText }
      ]
      qaiResult.value = fullText
      _saveQiConversation(q)
      var bar = document.getElementById('qaiChatInputBar')
      if (bar) bar.style.display = 'flex'
    },
    onError: function() {
      qaiLoading.value = false
    }
  })
}

// 通用 SSE（奇门专用，Fetch + ReadableStream）
function _qaiDoStreamSSE(opts) {
  var bubble = document.getElementById(opts.bubbleId)
  if (!bubble) return
  var stageEl = bubble.querySelector('.ai-stage')
  var barEl = bubble.querySelector('.ai-progress-fill')
  var contentEl = bubble.querySelector('.chat-bubble-content')
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  var fullText = '', charQueue = '', typeTimer = null, doneReceived = false

  function startTypewriter() {
    if (typeTimer) return
    typeTimer = setInterval(function() {
      if (charQueue.length === 0 && doneReceived) {
        clearInterval(typeTimer); typeTimer = null
        if (stageEl) stageEl.style.display = 'none'
        var barWrap = bubble.querySelector('.ai-progress-bar')
        if (barWrap) barWrap.style.display = 'none'
        if (contentEl) contentEl.innerHTML = renderQimenCards(fullText)
        if (opts.onDone) opts.onDone(fullText)
        return
      }
      if (charQueue.length === 0) return
      var take = charQueue.length > 3 ? 2 : 1
      fullText += charQueue.substring(0, take)
      charQueue = charQueue.substring(take)
      if (contentEl) contentEl.innerHTML = _stripMarkdown(fullText).replace(/\n/g, '<br>')
    }, 35)
  }

  // 使用 Fetch + ReadableStream（比 XHR onprogress 更可靠）
  fetch(opts.url, {
    method: 'POST',
    headers: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
    body: JSON.stringify(opts.body)
  }).then(function(resp) {
    if (!resp.ok) { if (opts.onError) opts.onError(); return }
    var reader = resp.body.getReader(); var decoder = new TextDecoder()
    var buffer = '', eventType = ''
    function pump() {
      reader.read().then(function(r) {
        if (r.done) { doneReceived = true; qaiLoading.value = false; return }
        buffer += decoder.decode(r.value, { stream: true })
        var lines = buffer.split('\n')
        buffer = lines.pop()
        for (var i = 0; i < lines.length; i++) {
          var line = lines[i]
          if (line.indexOf('event:') === 0) { eventType = line.replace('event:', '').trim(); continue }
          if (line.indexOf('data:') !== 0) continue
          try {
            var data = JSON.parse(line.replace('data:', '').trim())
            if (eventType === 'progress') {
              if (data.stage === 'connecting' && stageEl) stageEl.innerHTML = '🔗 正在连接...'
              else if (data.stage === 'analyzing' && stageEl) stageEl.innerHTML = '🧠 排盘分析中...'
              else if (data.stage === 'generating' && stageEl) { stageEl.innerHTML = '<img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成解读...'; startTypewriter() }
              if (barEl) barEl.style.width = '60%'
            } else if (eventType === 'chunk') {
              if (!typeTimer) startTypewriter()
              charQueue += data.content
            } else if (eventType === 'done') {
              doneReceived = true; qaiLoading.value = false
            } else if (eventType === 'error') {
              if (stageEl) stageEl.innerHTML = '⚠️ ' + data.message
              if (barEl) barEl.style.display = 'none'
              if (opts.onError) opts.onError()
            }
            eventType = ''
          } catch(_) {}
        }
        pump()
      }).catch(function() { if (opts.onError) opts.onError() })
    }
    pump()
  }).catch(function() { if (opts.onError) opts.onError() })
}

// ═══ 追问 ═══
function qaiSendFollowUp() {
  var input = document.querySelector('#qaiChatInput input') || document.getElementById('qaiChatInput')
  if (!input) return
  var question = input.value.trim()
  if (!question) return
  input.value = ''

  var chatContainer = document.getElementById('qaiChatContainer')
  if (!chatContainer) return

  // 追问沿用初始起局时间（当时的局）
  var pt = window._qaiPanTime || {}

  // 添加用户气泡
  var userBubble = document.createElement('view')
  userBubble.className = 'chat-bubble-user'
  userBubble.textContent = question
  chatContainer.appendChild(userBubble)

  // 添加 AI 气泡（流式）
  var bubbleId = 'qaiFollow_' + Date.now()
  var aiBubble = document.createElement('view')
  aiBubble.className = 'chat-bubble-ai'
  aiBubble.id = bubbleId
  aiBubble.innerHTML = '<div class="ai-stage"><img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成回复...</div>' +
    '<div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div>' +
    '<div class="chat-bubble-content"></div>'
  chatContainer.appendChild(aiBubble)
  chatContainer.scrollIntoView({ behavior: 'smooth', block: 'end' })

  // 构建历史
  var history = window._qaiChatHistory || []
  history.push({ role: 'user', content: question })

  _qaiDoStreamSSE({
    bubbleId: bubbleId,
    url: '/api/qimen/ask/stream',
    body: {
      question: question,
      history: history,
      year: pt.year || yearOptions[qaiYearIdx.value],
      month: pt.month || monthOptions[qaiMonthIdx.value],
      day: pt.day || qaiDayOptions.value[qaiDayIdx.value],
      hour: pt.hour != null ? pt.hour : hourValues[qaiHourIdx.value],
      minute: pt.minute != null ? pt.minute : parseInt(minuteOptions[qaiMinuteIdx.value] || '0'),
      panType: pt.panType || [2, 3][qaiJuIdx.value]
    },
    question: question,
    onDone: function(fullText) {
      history.push({ role: 'assistant', content: fullText })
      window._qaiChatHistory = history
      if (_qaiCurrentConvId) {
        _updateQiConversation()
      } else {
        _saveQiConversation(question)
      }
    },
    onError: function() {
      var eb = document.getElementById(bubbleId)
      if (eb) { var es = eb.querySelector('.ai-stage'); if (es) es.innerHTML = '⚠️ 追问失败，请重试' }
    }
  })
}
window.qaiSendFollowUp = qaiSendFollowUp

// ═══ DOM直操作辅助函数（绕过Vue 3.4.21 render effect bug） ═══
function switchQiTab(tab) {
  activeTab.value = tab
  // DOM直操作确保显示（防御Vue render滞后）
  var free = document.getElementById('qiTabFreeContent')
  var ai = document.getElementById('qiTabAiContent')
  if (free) free.style.display = tab === 'free' ? 'block' : 'none'
  if (ai) ai.style.display = tab === 'ai' ? 'block' : 'none'
}

function toggleQiDeepMode() {
  deepMode.value = !deepMode.value
  var el = document.getElementById('qiDeepToggle')
  if (el) el.classList.toggle('active')
}

function switchQiResultMode(m) {
  resultMode.value = m
  var simple = document.getElementById('qiResultSimple')
  var pro = document.getElementById('qiResultPro')
  if (simple) { m === 'simple' ? simple.classList.add('active') : simple.classList.remove('active') }
  if (pro) { m === 'pro' ? pro.classList.add('active') : pro.classList.remove('active') }
}

// ── 创建原生DOM输入框（绕过uni-app <input>包装层，保证H5可用）──
function createNativeInput(wrapId, type, placeholder) {
  var wrap = document.getElementById(wrapId)
  if (!wrap) return null
  var inp = document.createElement('input')
  inp.type = type
  inp.className = 'form-input'
  inp.id = wrapId.replace('-wrap', '')
  if (placeholder) inp.placeholder = placeholder
  if (type === 'text') inp.setAttribute('maxlength', '100')
  wrap.appendChild(inp)
  return inp
}

// ══ 原生 DOM 填充 select options（uni-app 编译器吞掉 <option>） ══
// #ifdef H5
function _fillSelect(id, labels, selectedIdx, onChange) {
  var sel = document.getElementById(id)
  if (!sel) return
  sel.innerHTML = ''
  for (var i = 0; i < labels.length; i++) {
    var opt = document.createElement('option')
    opt.value = i
    opt.textContent = labels[i]
    sel.appendChild(opt)
  }
  sel.value = String(selectedIdx)
  if (onChange) {
    sel.addEventListener('change', function() { onChange(parseInt(this.value)) })
  }
}

function _fillAllSelects() {
  // 免费版
  _fillSelect('qf-year', yearLabels, qfYearIdx.value, function(v) { qfYearIdx.value = v })
  _fillSelect('qf-month', monthLabels, qfMonthIdx.value, function(v) { qfMonthIdx.value = v })
  _fillSelect('qf-day', qfDayLabels.value, qfDayIdx.value, function(v) { qfDayIdx.value = v })
  _fillSelect('qf-hour', hourOptions, qfHourIdx.value, function(v) { qfHourIdx.value = v })
  _fillSelect('qf-minute', minuteOptions, qfMinuteIdx.value, function(v) { qfMinuteIdx.value = v })
  _fillSelect('qf-pantype', ['拆补法', '置闰法'], qfPanTypeIdx.value, function(v) { qfPanTypeIdx.value = v })
  // AI版
  _fillSelect('qai-year', yearLabels, qaiYearIdx.value, function(v) { qaiYearIdx.value = v })
  _fillSelect('qai-month', monthLabels, qaiMonthIdx.value, function(v) { qaiMonthIdx.value = v })
  _fillSelect('qai-day', qaiDayLabels.value, qaiDayIdx.value, function(v) { qaiDayIdx.value = v })
  _fillSelect('qai-hour', hourOptions, qaiHourIdx.value, function(v) { qaiHourIdx.value = v })
  _fillSelect('qai-minute', minuteOptions, qaiMinuteIdx.value, function(v) { qaiMinuteIdx.value = v })
  _fillSelect('qai-ju', ['拆补法', '置闰法'], qaiJuIdx.value, function(v) { qaiJuIdx.value = v })
  _fillSelect('qai-school', ['时家奇门', '日家奇门'], qaiSchoolIdx.value, function(v) { qaiSchoolIdx.value = v })
}

function _syncSelectValue(id, val) {
  var sel = document.getElementById(id)
  if (sel) sel.value = String(val)
}

function _refillDaySelect(id, labels, idxRef) {
  var sel = document.getElementById(id)
  if (!sel) return
  var curVal = idxRef.value
  sel.innerHTML = ''
  for (var i = 0; i < labels.length; i++) {
    var opt = document.createElement('option')
    opt.value = i
    opt.textContent = labels[i]
    sel.appendChild(opt)
  }
  if (curVal >= labels.length) curVal = labels.length - 1
  sel.value = String(curVal)
  idxRef.value = curVal
}
// #endif

// 初始化（页面刷新时重新同步当前时间，确保时分也正确）
function applyNavQuery(q) {
  if (!q) return
  if (q.includes('tab=free')) { activeTab.value = 'free' }
  else if (q.includes('tab=ai')) { activeTab.value = 'free' }
}

onShow(() => {
  releaseQimenPageScroll()
  try {
    var q = sessionStorage.getItem('_nav_query')
    if (q) { sessionStorage.removeItem('_nav_query'); applyNavQuery(q) }
  } catch(_) {}
  try { _checkQiRestore() } catch(_) {}
  // 每次页面显示时确保 tab DOM 状态正确
  var free = document.getElementById('qiTabFreeContent')
  var ai = document.getElementById('qiTabAiContent')
  if (activeTab.value === 'free') {
    if (free) free.style.display = 'block'
    if (ai) ai.style.display = 'none'
  } else {
    if (free) free.style.display = 'none'
    if (ai) ai.style.display = 'block'
  }
  var t = uni.getStorageSync('xc_theme')
  if (t && t !== theme.value) {
    theme.value = t
    try {
      document.documentElement.setAttribute('data-theme', t)
      document.body.setAttribute('data-theme', t)
    } catch(_) {}
  }
})

onMounted(() => {
  releaseQimenPageScroll()
  try {
    uni.$on('nav-query', function(q) { applyNavQuery(q) })
    var q = sessionStorage.getItem('_nav_query')
    if (q) { sessionStorage.removeItem('_nav_query'); applyNavQuery(q) }
  } catch(_) {}
  const now = new Date()
  const y = now.getFullYear(); const m = now.getMonth() + 1; const d = now.getDate()
  qfYearIdx.value = yearOptions.indexOf(y)
  qfMonthIdx.value = m - 1
  qfDayOptions.value = getDayOptions(y, m)
  qfDayLabels.value = getDayLabels(y, m)
  qfDayIdx.value = d - 1
  qfHourIdx.value = _initHourIdx(now.getHours())
  qfMinuteIdx.value = now.getMinutes()
  qaiYearIdx.value = qfYearIdx.value
  qaiMonthIdx.value = qfMonthIdx.value
  qaiDayOptions.value = [...qfDayOptions.value]
  qaiDayLabels.value = [...qfDayLabels.value]
  qaiDayIdx.value = qfDayIdx.value
  qaiHourIdx.value = qfHourIdx.value
  qaiMinuteIdx.value = qfMinuteIdx.value

  // #ifdef H5
  // 延迟填充，确保 DOM 已渲染（nextTick 可能不够，用 setTimeout 兜底）
  var _fillRetry = 0
  function _tryFill() {
    var sel = document.getElementById('qf-year')
    if (sel && sel.options.length === 0) {
      _fillAllSelects()
      console.log('[qimen] _fillAllSelects done, retry=' + _fillRetry)
    } else if (!sel && _fillRetry < 10) {
      _fillRetry++
      setTimeout(_tryFill, 200)
      console.log('[qimen] select not found, retry ' + _fillRetry)
    }
  }
  nextTick(() => { setTimeout(_tryFill, 100) })
  // 创建AI问题输入框（Flask原版是textarea）
  var qWrap = document.getElementById('qaiQuestion-wrap')
  if (qWrap) {
    var ta = document.createElement('textarea')
    ta.className = 'form-input'
    ta.id = 'qaiQuestion'
    ta.placeholder = '输入你想问策的问题...'
    ta.rows = 3
    // 内联样式（Vue scoped CSS不作用于动态创建的元素）
    // 使用--card-bg/--card-border以匹配起局时间select样式
    var root = document.querySelector('.page-root') || document.documentElement
    var cardBg = getComputedStyle(root).getPropertyValue('--card-bg').trim() || 'rgba(48,53,76,0.85)'
    var cardBorder = getComputedStyle(root).getPropertyValue('--card-border').trim() || 'rgba(255,255,255,0.12)'
    var textColor = getComputedStyle(root).getPropertyValue('--text-1').trim() || 'rgba(240,236,228,0.97)'
    ta.style.cssText = 'width:100%;padding:9px 14px;border-radius:8px;background:' + cardBg + ';border:1.5px solid ' + cardBorder + ';color:' + textColor + ';font-size:0.85rem;outline:none;box-sizing:border-box;min-height:70px;font-family:inherit;line-height:1.6;resize:vertical;'
    qWrap.appendChild(ta)
  }
  // #endif

  // 检查URL参数中的tab
  // #ifdef H5
  const hash = location.hash
  if (hash.includes('tab=free')) activeTab.value = 'free'
  else if (hash.includes('tab=ai')) activeTab.value = 'free'
  // 检查scenario参数
  const params = new URLSearchParams(location.search)
  const scenario = params.get('scenario') || hash.match(/scenario=([^&]+)/)?.[1]
  if (scenario) {
    activeTab.value = 'free'
  }
  // #endif

  // 监听对话恢复事件
  uni.$on('xc-restore', _checkQiRestore)
  _checkQiRestore()
  window._xc_restoreQimen = _checkQiRestore
  setInterval(function() {
    var rd = window.__xc_restoreData
    if (rd && rd.type === 'qimen') _checkQiRestore()
  }, 500)
})

// ═══ 卡片式渲染 ═══
function renderQimenCards(text) {
  text = _stripMarkdown(text)
  var sections = text.split(/\n(?=#{2,} |\d+\.\s+\*\*)/)
  var html = ''
  sections.forEach(function(sec) {
    var title = ''
    var body = sec
    var m = sec.match(/^(#{2,})\s+(.+)/)
    if (m) {
      title = m[2]
      body = sec.substring(m[0].length).trim()
    } else {
      var m2 = sec.match(/^(\d+\.)\s+\*\*(.+?)\*\*[：:]\s*/)
      if (m2) {
        title = m2[2]
        body = sec.substring(m2[0].length).trim()
      }
    }
    body = body.replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>')
    if (!body) body = '&nbsp;'
    if (title) {
      html += '<div class="qai-card-item"><div class="qai-card-title">' + title + '</div><div class="qai-card-body"><p>' + body + '</p></div></div>'
    } else {
      html += '<div class="qai-card-item"><div class="qai-card-body"><p>' + body + '</p></div></div>'
    }
  })
  return html
}
// ═══ 奇门对话保存 ═══
var _qaiCurrentConvId = null

function _saveQiConversation(question) {
  var title = (question || '奇门遁甲').substring(0, 50)
  uni.request({
    url: '/api/qimen/conversations', method: 'POST',
    data: {
      title: title,
      question: question,
      messages: window._qaiChatHistory || [],
      pan_data: window._qaiPanTime || {}
    },
    success: function(res) {
      if (res.data && res.data.id) _qaiCurrentConvId = res.data.id
      window.__sidebarCache = null
    },
    fail: function(err) { console.error('[qimen] 保存对话失败:', err) }
  })
}

function _updateQiConversation() {
  if (!_qaiCurrentConvId) return
  uni.request({
    url: '/api/qimen/conversations', method: 'POST',
    data: { id: _qaiCurrentConvId, messages: window._qaiChatHistory || [] },
    success: function() { window.__sidebarCache = null },
    fail: function(err) { console.error('[qimen] 更新对话失败:', err) }
  })
}

function _stripMarkdown(s) {
  if (!s) return ''
  return s.replace(/^#{1,6}\s*/gm, '').replace(/\*\*/g, '').replace(/^[-*]\s+/gm, '')
}

// 滚动到追问输入框
function _qiScrollToChat() {
  setTimeout(function() {
    var el = document.getElementById('qaiChatInputBar')
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, 100)
}

function _checkQiRestore() {
  var d = window.__xc_restoreData
  if (!d || d.type !== 'qimen') return
  switchQiTab('ai')
  var chatContainer = document.getElementById('qaiChatContainer')
  var inputBar = document.getElementById('qaiChatInputBar')
  if (!chatContainer) return
  window.__xc_restoreData = null
  var streamBox = document.getElementById('qiStreamBox')
  if (streamBox) streamBox.style.display = ''
  chatContainer.innerHTML = ''
  if (d.rawHtml) {
    // 旧记录：先去除 markdown 格式，再渲染
    if (d.question) {
      var ub2 = document.createElement('view')
      ub2.className = 'chat-bubble-user'
      ub2.textContent = d.question
      chatContainer.appendChild(ub2)
    }
    // 先去除 HTML 标签，再去除 markdown 格式，最后转成 HTML
    var cleanHtml = _stripMarkdown(d.rawHtml.replace(/<[^>]+>/g, '')).replace(/\n/g, '<br>')
    var ab2 = document.createElement('view')
    ab2.className = 'chat-bubble-ai'
    ab2.innerHTML = '<div class="chat-bubble-content">' + cleanHtml + '</div>'
    chatContainer.appendChild(ab2)
    // 模拟旧记录为可追问的history
    window._qaiChatHistory = [
      { role: 'user', content: d.question || '' },
      { role: 'assistant', content: cleanHtml.replace(/<[^>]+>/g, '').substring(0, 200) + '...' }
    ]
    _qaiCurrentConvId = null
    window._qaiPanTime = null
  } else {
    // 新记录：按messages渲染
    var messages = d.messages || []
    window._qaiChatHistory = messages.slice()
    _qaiCurrentConvId = d.id || null
    window._qaiPanTime = d.pan_data || null
    messages.forEach(function(m) {
      if (m.role === 'user') {
        var ub = document.createElement('view')
        ub.className = 'chat-bubble-user'
        ub.textContent = m.content
        chatContainer.appendChild(ub)
      } else if (m.role === 'assistant') {
        var ab = document.createElement('view')
        ab.className = 'chat-bubble-ai'
        ab.innerHTML = '<div class="chat-bubble-content">' + renderQimenCards(m.content) + '</div>'
        chatContainer.appendChild(ab)
      }
    })
  }
  if (inputBar) inputBar.style.display = 'flex'
  _qiScrollToChat()
}
</script>

<style scoped>
/* 复用首页变量体系和通用样式 */
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --accent: hsl(38, 60%, 60%); --accent-2: hsl(38, 60%, 48%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --accent: hsl(38, 72%, 30%); --accent-2: hsl(38, 72%, 22%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }

.page-root { position: relative; z-index: 0; min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }

/* 工具页Hero */
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.tool-hero { padding: 60px 32px 32px; text-align: center; position: relative; overflow: hidden; }
.tool-hero::before { content: ''; position: absolute; top: -50%; left: -20%; width: 140%; height: 200%; background: radial-gradient(ellipse at center, var(--accent-glow) 0%, transparent 70%); opacity: 0.5; pointer-events: none; }
.tool-hero-content { position: relative; z-index: 1; max-width: var(--max-w); margin: 0 auto; }
.tool-hero-title { font-family: var(--font-serif); font-size: 2rem; font-weight: 400; letter-spacing: 4px; color: var(--text-1); margin-bottom: 12px; }
.tool-hero-desc { font-size: 0.9375rem; color: var(--text-3); letter-spacing: 2px; }

/* 工具容器 */
.tool-container { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; backdrop-filter: blur(20px); box-shadow: var(--card-shadow); max-width: 720px; margin: 0 auto; }
.tool-container.has-qimen-result { max-width: min(1120px, calc(100vw - 64px)); }
.tool-tabs { display: flex; gap: 4px; margin-bottom: 28px; border-bottom: 1px solid var(--card-border); }
.tool-tab { padding: 12px 20px; border-radius: 10px 10px 0 0; font-size: 0.875rem; cursor: pointer; border: 1px solid transparent; border-bottom: none; color: var(--text-3); background: transparent; }
.tool-tab.active { color: var(--accent); background: var(--accent-glow); border-color: var(--accent); font-weight: 600; }
.tab-badge { font-size: 0.5625rem; padding: 1px 5px; border-radius: 4px; background: var(--accent); color: #fff; margin-left: 4px; }
.tab-badge.free { background: var(--success); }
.tool-tab-content { display: block; }

/* 表单 */
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 6px; letter-spacing: 1px; }
.form-input, .form-select-picker { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
select.form-select-picker { appearance: none; -webkit-appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath d='M6 8L1 3h10z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 12px center; padding-right: 32px; cursor: pointer; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.form-hint { font-size: 0.6875rem; color: var(--text-3); }
.advanced-fields { display: none; margin-top: 12px; padding-top: 12px; border-top: 1px dashed var(--card-border); }
.advanced-fields.show { display: block; }
.advanced-toggle { font-size: 0.75rem; color: var(--text-3); cursor: pointer; border: none; background: none; text-decoration: underline; margin-top: 8px; }
.submit-btn { width: 100%; padding: 14px 16px; border-radius: 30px; border: none; background: hsl(35, 38%, 52%); color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; letter-spacing: 2px; margin-top: 8px; transition: opacity 0.2s; text-align: center; box-sizing: border-box; }
.submit-btn.disabled { opacity: 0.5; cursor: not-allowed; }
.btn-row { display: flex; gap: 10px; justify-content: center; margin-top: 16px; }
.btn-row .submit-btn { flex: 85; margin-top: 0; }
.btn-ghost { background: transparent; border: 1.5px solid var(--card-border-hover, var(--card-border)); color: var(--text-2); padding: 12px 18px; border-radius: 30px; font-size: 0.875rem; font-weight: 600; cursor: pointer; letter-spacing: 1px; transition: all 0.2s; text-align: center; }
.btn-ghost:hover { border-color: var(--accent); color: var(--accent); background: var(--accent-glow); }
.btn-row .btn-ghost { flex: 15; }

/* 奇门免费版表单 */
.qf-form { padding: 4px 0; }
.qf-datetime-section { background: var(--section-alt); border-radius: 12px; padding: 14px 16px; border: 1px solid var(--card-border); margin-bottom: 14px; }
.qf-section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.qf-now-btn-sm { width: 32px; height: 32px; border: 1.5px solid var(--card-border); border-radius: 8px; background: var(--card-bg); color: var(--text-1); font-size: 0.85rem; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.qf-datetime-row { display: flex; gap: 8px; align-items: center; justify-content: space-between; }
.qf-dt-col { flex: 1; min-width: 0; }
.qf-dt-col-narrow { flex: 0.8; }
.qf-datetime-select { width: 100%; padding: 9px 6px; border: 1.5px solid var(--card-border); border-radius: 8px; font-size: 0.85rem; font-weight: 500; background: var(--card-bg); color: var(--text-1); cursor: pointer; text-align: center; appearance: none; -webkit-appearance: none; -moz-appearance: none; outline: none; box-sizing: border-box; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath d='M5 7L1 3h8z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 4px center; padding-right: 16px; }
.qf-datetime-select:focus { border-color: var(--accent); }
.qf-pantype-select { width: 100%; padding: 9px 12px; border: 1.5px solid var(--card-border); border-radius: 8px; font-size: 0.85rem; font-weight: 500; background: var(--card-bg); color: var(--text-1); cursor: pointer; appearance: none; -webkit-appearance: none; -moz-appearance: none; outline: none; box-sizing: border-box; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath d='M5 7L1 3h8z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 8px center; padding-right: 24px; }
.qf-pantype-select:focus { border-color: var(--accent); }
.qf-options-row { display: flex; gap: 10px; align-items: flex-end; }
.qf-result { margin-top: 16px; overflow-x: auto; -webkit-overflow-scrolling: touch; }
.qf-result-card { background: var(--card-bg); border-radius: 12px; padding: 20px; border: 1px solid var(--card-border); }
.qf-result-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; color: var(--accent); letter-spacing: 2px; }
.qf-result-row { font-size: 0.82rem; color: var(--text-2); margin-bottom: 6px; }
.qf-result :deep(.qf-result-card) { background: var(--card-bg); border-radius: 12px; padding: clamp(14px, 2.2vw, 24px); border: 1px solid var(--card-border); }
.qf-result :deep(.qm-scale-shell) {
  --qm-grid-size: clamp(300px, min(72vw, 72dvh), 760px);
  --qm-cell-font: clamp(0.62rem, calc(var(--qm-grid-size) / 48), 1rem);
  --qm-center-font: clamp(0.54rem, calc(var(--qm-grid-size) / 58), 0.86rem);
  --qm-center-small-font: clamp(0.48rem, calc(var(--qm-grid-size) / 68), 0.76rem);
  --qm-center-date-font: clamp(0.56rem, calc(var(--qm-grid-size) / 54), 0.9rem);
  width: min(100%, var(--qm-grid-size));
  margin: 0 auto;
}
.qf-result :deep(.qm-palace-grid) {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: clamp(2px, 0.35vw, 4px);
  width: 100%;
  aspect-ratio: 1;
  background: #d5cfc2;
  border-radius: 12px;
  overflow: hidden;
  border: 2px solid #b8b0a0;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.qf-result :deep(.qm-palace-cell) {
  aspect-ratio: 1;
  position: relative;
  background: #fff;
  padding: clamp(4px, 1.3%, 9px);
  font-size: clamp(0.62rem, calc(var(--qm-grid-size) / 48), 1rem);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-sizing: border-box;
  min-width: 0;
  line-height: 1.18;
}
.qf-result :deep(.qm-center-cell) {
  background: #f0ede5;
  justify-content: center;
  gap: clamp(1px, 0.45vw, 4px);
  text-align: center;
  line-height: 1.25;
}
.qf-result :deep(.qm-empty-cell) { background: #f5f0e8; }
.qf-result :deep(.qm-tian-gan) {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  white-space: nowrap;
}
.qf-result :deep(.qm-ma-marker) {
  flex: 0 0 auto;
  font-size: 0.82em;
  line-height: 1;
}

/* AI进度条 */
.qai-progress { margin-top: 16px; }
.qai-progress-bar { height: 6px; background: var(--card-border); border-radius: 4px; overflow: hidden; margin: 0 4px; }
.qai-progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent), #e8a84c); border-radius: 4px; transition: width 0.6s ease; }
.qai-step-text { text-align: center; font-size: 0.82rem; color: var(--text-2); margin-top: 8px; }
.qai-result { margin-top: 16px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; max-height: 600px; overflow-y: auto; line-height: 1.8; }
.qai-markdown { font-size: 0.88rem; color: var(--text-1); }
.qai-error { text-align: center; padding: 24px; color: var(--danger); }
.qai-deep-row { display: flex; align-items: center; gap: 8px; margin: 8px 0; }
.qai-deep-toggle { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; }
.qai-deep-toggle.active .qai-toggle-track { background: var(--accent); }
.qai-toggle-label { font-size: 0.82rem; color: var(--text-2); font-weight: 500; }
.qai-toggle-track { width: 40px; height: 22px; background: var(--card-border); border-radius: 11px; position: relative; transition: background 0.3s; }
.qai-toggle-knob { width: 18px; height: 18px; background: #fff; border-radius: 50%; position: absolute; top: 2px; left: 2px; transition: transform 0.3s; }
.qai-deep-toggle.active .qai-toggle-knob { transform: translateX(18px); }
.result-mode-switch { display: flex; gap: 8px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--card-border); }
.result-mode-btn { flex: 1; padding: 8px; border-radius: 8px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.75rem; cursor: pointer; text-align: center; }
.result-mode-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }

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
  .tool-hero { padding: 40px 16px 24px; }
  .tool-hero-title { font-size: 1.5rem; letter-spacing: 2px; }
  .tool-container,
  .tool-container.has-qimen-result { padding: 20px 16px; max-width: calc(100vw - 32px); }
  .section { padding: 48px 16px; }
  .qf-datetime-row { flex-wrap: wrap; }
  .qf-dt-col { flex: 1 1 calc(33% - 8px); min-width: 60px; }
  .qf-result :deep(.qm-scale-shell) { --qm-grid-size: clamp(280px, 92vw, 560px); }
}
@media (max-width: 480px) {
  .tool-hero-title { font-size: 1.2rem; letter-spacing: 1px; }
  .tool-hero-desc { font-size: 0.75rem; }
  .tool-container,
  .tool-container.has-qimen-result { padding: 16px 12px; max-width: calc(100vw - 24px); }
  .qf-dt-col { flex: 1 1 calc(50% - 6px); min-width: 50px; }
  .qf-datetime-select { font-size: 0.78rem; padding: 7px 4px; }
  .tool-tab { padding: 8px 10px; font-size: 0.75rem; }
  .submit-btn { font-size: 0.875rem; padding: 12px 16px; }
  .btn-row { flex-direction: column; }
  .qf-result :deep(.qf-result-card) { padding: 12px; }
  .qf-result :deep(.qm-scale-shell) { --qm-grid-size: clamp(260px, 92vw, 420px); }
}

/* ═══ 流式解读卡片 ═══ */
.qai-stream-box {
  margin-top: 20px; padding: 16px;
  background: var(--card-bg); border: 1px solid rgba(178,149,93,0.16);
  border-radius: 16px; box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}
.qai-card-item {
  background: rgba(255,255,255,0.04); border: 1px solid rgba(178,149,93,0.14);
  border-radius: 14px; padding: 14px 16px; margin-bottom: 10px;
}
.qai-card-title {
  font-size: 0.92rem; font-weight: 700; letter-spacing: 0.5px;
  color: var(--accent); margin-bottom: 6px;
}
.qai-card-body { font-size: 0.86rem; color: var(--text-2); line-height: 1.86; }
.qai-card-body strong { color: var(--text-1); }

/* ═══ 对话气泡 ═══ */
.chat-container { display: flex; flex-direction: column; gap: 12px; }
.chat-bubble-ai {
  align-self: flex-start;
  background: rgba(255,255,255,0.045); border: 1px solid rgba(178,149,93,0.16);
  border-radius: 16px;
  padding: 16px 18px; max-width: 94%; width: 100%; box-sizing: border-box;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
}
.chat-bubble-user {
  align-self: flex-end;
  background: var(--accent); color: #fff;
  border-radius: 16px;
  padding: 10px 16px; max-width: 80%;
  font-size: 0.9rem; line-height: 1.6;
}
.chat-bubble-content {
  font-size: 0.9rem; color: var(--text-2); line-height: 1.86; word-break: break-word;
}
.ai-stage {
  font-size: 0.9rem; color: var(--text-1);
  margin-bottom: 8px; display: flex; align-items: center; gap: 8px;
}
.ai-progress-bar {
  height: 4px; background: var(--card-border);
  border-radius: 2px; overflow: hidden; margin-bottom: 16px;
}
.ai-progress-fill {
  height: 100%; width: 20%;
  background: linear-gradient(90deg, transparent, var(--accent), #d6b46d, transparent);
  border-radius: 2px;
  animation: ai-progress-pulse 1.5s ease-in-out infinite;
  transition: width 0.3s ease;
}
@keyframes ai-progress-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* ═══ 追问输入栏 ═══ */
.chat-input-bar {
  display: flex; gap: 8px; margin-top: 16px;
  padding: 10px 14px; background: rgba(255,255,255,0.045);
  border-radius: 16px; border: 1px solid rgba(178,149,93,0.16);
}
.chat-input {
  flex: 1; padding: 8px 14px; border-radius: 999px;
  border: 1px solid rgba(178,149,93,0.16);
  background: var(--input-bg); color: var(--text-1);
  font-size: 0.875rem; outline: none;
}
.chat-send-btn {
  padding: 8px 20px; background: var(--accent); color: #fff;
  border-radius: 999px; font-size: 0.875rem; cursor: pointer; white-space: nowrap;
}

@media (max-width: 768px) {
  .page-root,
  .page-wrap,
  .tool-container,
  .tool-tab-content {
    touch-action: pan-y;
  }
  .qai-result {
    max-height: none;
    overflow-y: visible;
    -webkit-overflow-scrolling: auto;
  }
  .qai-stream-box,
  .chat-container,
  .chat-bubble-ai,
  .chat-bubble-content {
    overflow: visible;
    touch-action: pan-y;
  }
  .qf-result {
    overflow-x: auto;
    overflow-y: visible;
    overscroll-behavior-x: contain;
  }
}
:global(html.qimen-page-active),
:global(body.qimen-page-active) {
  overflow: hidden !important;
  overscroll-behavior: none;
}
:global(body.qimen-page-active uni-page-wrapper) {
  height: 100dvh !important;
  max-height: 100dvh !important;
  overflow-y: auto !important;
  -webkit-overflow-scrolling: touch;
  overscroll-behavior-y: contain;
}
:global(body.qimen-page-active uni-page-body) {
  overflow: visible !important;
}
</style>
