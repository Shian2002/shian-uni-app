<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />
    <view class="page-wrap">
      <section class="tool-hero"><view class="tool-hero-content"><view class="section-tag">紫微斗数</view><view class="tool-hero-title">紫微斗数 · 十二宫排盘</view><view class="tool-hero-desc">出生时间排盘 · 十二宫星曜 · 四化飞星 · 大限流年推运</view></view></section>
      <section class="section">
        <view class="tool-container">
          <view class="incognito-bar"><label class="incognito-toggle"><view id="zwIncognitoChk" class="incognito-visual" @tap="toggleZwIncognito()"></view><text>{{ incognito ? '🔒 无痕模式' : '🔓 有痕模式' }}</text></label><text class="incognito-desc">本地计算 · 不上传数据 · 退出自动清空</text></view>
          <view class="tool-tabs">
            <view id="zwTabPan" class="tool-tab" :class="{ active: activeTab === 'pan' }" data-zw-tab="pan">⭐ 排盘<text class="tab-badge free">免费</text></view>
            <view id="zwTabAi" class="tool-tab" :class="{ active: activeTab === 'ai' }" @tap="switchZwTab('ai')">🔮 时安紫微系统<text class="tab-badge">PRO</text></view>
            <view id="zwTabHoro" class="tool-tab" :class="{ active: activeTab === 'horoscope' }" data-zw-tab="horoscope">📅 推运<text class="tab-badge">PRO</text></view>
          </view>
          <!-- 排盘面板 -->
          <view class="tool-tab-content" id="zwPanContent" v-show="activeTab === 'pan'">
            <view class="zw-form-grid">
              <view class="form-group"><text class="form-label">出生年</text><view id="zwYear-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生月</text><view id="zwMonth-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生日</text><view id="zwDay-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生时(0-23)</text><view id="zwHour-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生分(可选)</text><view id="zwMinute-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">性别</text><picker :range="['男', '女']" :value="zwGenderIdx" @change="zwGenderIdx = $event.detail.value"><view class="form-select-picker">{{ ['男', '女'][zwGenderIdx] }}</view></picker></view>
              <view class="form-group"><text class="form-label">历法类型</text><picker :range="['阳历(公历)', '农历(阴历)']" :value="zwDateTypeIdx" @change="zwDateTypeIdx = $event.detail.value"><view class="form-select-picker">{{ ['阳历(公历)', '农历(阴历)'][zwDateTypeIdx] }}</view></picker></view>
            </view>
            <view class="btn-row">
              <view class="submit-btn" data-zw-action="freePan">⭐ 免费排盘</view>
              <view class="btn btn-ghost" data-zw-action="resetPan">🔄 清空</view>
            </view>
            <text class="form-hint" style="text-align:center;display:block;margin-top:12px;">基于iztro-py精确排盘，十二宫、主星辅星、四化飞星全展示。</text>
            <view class="privacy-note">✅ 本地计算 · 不上传数据 · 秒出结果</view>
            <view class="zw-result" v-if="zwPanResult" v-html="zwPanResult"></view>
          </view>
          <!-- 推运面板 -->
          <view class="tool-tab-content" id="zwHoroContent" v-show="activeTab === 'horoscope'">
            <view class="zw-form-grid">
              <view class="form-group"><text class="form-label">出生年</text><view id="zwHYear-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生月</text><view id="zwHMonth-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生日</text><view id="zwHDay-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生时(0-23)</text><view id="zwHHour-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">性别</text><picker :range="['男', '女']" :value="zwHGenderIdx" @change="zwHGenderIdx = $event.detail.value"><view class="form-select-picker">{{ ['男', '女'][zwHGenderIdx] }}</view></picker></view>
              <view class="form-group"><text class="form-label">历法类型</text><picker :range="['阳历(公历)', '农历(阴历)']" :value="zwHDateTypeIdx" @change="zwHDateTypeIdx = $event.detail.value"><view class="form-select-picker">{{ ['阳历(公历)', '农历(阴历)'][zwHDateTypeIdx] }}</view></picker></view>
            </view>
            <view class="btn-row">
              <view class="submit-btn" data-zw-action="horoscope">📅 推运排盘</view>
              <view class="btn btn-ghost" data-zw-action="resetHoroscope">🔄 清空</view>
            </view>
            <view class="zw-result" v-if="zwHoroscopeResult" v-html="zwHoroscopeResult"></view>
          </view>
          <!-- AI解读面板 -->
          <view class="tool-tab-content" id="zwTabAiContent" v-show="activeTab === 'ai'">
            <view class="zw-form-grid">
              <view class="form-group"><text class="form-label">出生年</text><view id="zwAiYear-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生月</text><view id="zwAiMonth-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生日</text><view id="zwAiDay-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生时(0-23)</text><view id="zwAiHour-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">出生分(可选)</text><view id="zwAiMinute-wrap" class="dom-input-wrap"></view></view>
              <view class="form-group"><text class="form-label">性别</text><picker :range="['男', '女']" :value="zwAiGenderIdx" @change="zwAiGenderIdx = $event.detail.value"><view class="form-select-picker">{{ ['男', '女'][zwAiGenderIdx] }}</view></picker></view>
              <view class="form-group"><text class="form-label">历法类型</text><picker :range="['阳历(公历)', '农历(阴历)']" :value="zwAiDateTypeIdx" @change="zwAiDateTypeIdx = $event.detail.value"><view class="form-select-picker">{{ ['阳历(公历)', '农历(阴历)'][zwAiDateTypeIdx] }}</view></picker></view>
            </view>
            <view class="form-group"><text class="form-label">分析类型</text>
              <view class="analysis-type-row">
                <view class="analysis-type-btn" :class="{ active: zwAiAnalysisTypeIdx === 0 }" @tap="zwAiAnalysisTypeIdx = 0">🔮 命盘总览</view>
                <view class="analysis-type-btn" :class="{ active: zwAiAnalysisTypeIdx === 1 }" @tap="zwAiAnalysisTypeIdx = 1">💼 事业财运</view>
                <view class="analysis-type-btn" :class="{ active: zwAiAnalysisTypeIdx === 2 }" @tap="zwAiAnalysisTypeIdx = 2">💕 姻缘感情</view>
                <view class="analysis-type-btn" :class="{ active: zwAiAnalysisTypeIdx === 3 }" @tap="zwAiAnalysisTypeIdx = 3">🏥 健康运势</view>
                <view class="analysis-type-btn" :class="{ active: zwAiAnalysisTypeIdx === 4 }" @tap="zwAiAnalysisTypeIdx = 4">📅 大限流年</view>
              </view>
            </view>
            <view class="form-group"><text class="form-label">你的问题（选填）</text><view id="zwAiQuestion-wrap" class="dom-input-wrap"></view></view>
            <view class="btn-row">
              <view class="submit-btn" @tap="zwAiAsk">🔮 AI 深度解读</view>
            </view>
            <view class="qai-stream-box" v-if="zwAiLoading || zwAiResult">
              <view class="chat-container" id="zwChatContainer"></view>
            </view>
            <view class="chat-input-bar" id="zwChatInputBar" style="display:none;">
              <input class="chat-input" id="zwChatInput" placeholder="继续追问..." />
              <view class="chat-send-btn" @tap="zwSendFollowUp">发送</view>
            </view>
            <view class="privacy-note incognito-status">✅ 无痕模式已开启 · 本地计算 · 不上传数据 · 退出自动清空</view>
          </view>
        </view>
      </section>
    </view>
    <view class="site-footer"><view class="footer-disclaimer">⚠️ 本站所有内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</view><view class="footer-grid"><view class="footer-col"><view class="footer-col-title">平台信息</view><navigator url="/package-info/about/index">关于我们</navigator></view><view class="footer-col"><view class="footer-col-title">快捷导航</view><navigator url="/pages/qimen/index" open-type="switchTab">奇门遁甲</navigator><navigator url="/pages/bazi-index/index" open-type="switchTab">八字排盘</navigator><navigator url="/pages/ziwei/index" open-type="switchTab">紫微斗数</navigator><navigator url="/pages/calendar/index" open-type="switchTab">专属日历</navigator></view><view class="footer-col"><view class="footer-col-title">备案与版权</view><view class="footer-icp">ICP备案号：京ICP备2026050601号-1</view><view class="footer-icp">© 2026 时安解忧屋 版权所有</view></view></view></view>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
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
const mobileMenuOpen = ref(false); const submenuOpen = reactive({ qimen: false, bazi: false, more: false })
function openMobileMenu() { mobileMenuOpen.value = true }; function closeMobileMenu() { mobileMenuOpen.value = false }; function toggleSubmenu(k) { submenuOpen[k] = !submenuOpen[k] }
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })
const incognito = ref(true); const activeTab = ref('pan')

// ═══ 修复模式：DOM原生控件操作 ═══
function toggleZwIncognito() {
  incognito.value = !incognito.value
  var el = document.getElementById('zwIncognitoChk')
  if (el) el.classList.toggle('active')
}

function switchZwTab(tab) {
  activeTab.value = tab
  var els = [['zwTabPan','pan'],['zwTabAi','ai'],['zwTabHoro','horoscope']]
  els.forEach(function(e) {
    var btn = document.getElementById(e[0])
    if (btn) { tab === e[1] ? btn.classList.add('active') : btn.classList.remove('active') }
  })
}
// 排盘表单
const zwYear = ref(2000); const zwMonth = ref(8); const zwDay = ref(16); const zwHour = ref(12); const zwMinute = ref(0)
const zwGenderIdx = ref(0); const zwDateTypeIdx = ref(0); const zwPanResult = ref('')

function zwResetPan() {
  zwYear.value = ''; zwMonth.value = ''; zwDay.value = ''; zwHour.value = ''; zwMinute.value = ''
  zwGenderIdx.value = 0; zwDateTypeIdx.value = 0; zwPanResult.value = ''
}

// 推运表单
const zwHYear = ref(2000); const zwHMonth = ref(8); const zwHDay = ref(16); const zwHHour = ref(12)
const zwHGenderIdx = ref(0); const zwHDateTypeIdx = ref(0)
const zwTargetDate = ref(''); const zwHoroscopeResult = ref('')

function zwResetHoroscope() {
  zwHYear.value = ''; zwHMonth.value = ''; zwHDay.value = ''; zwHHour.value = ''
  zwHGenderIdx.value = 0; zwHDateTypeIdx.value = 0; zwTargetDate.value = ''; zwHoroscopeResult.value = ''
}

// AI 解读
const zwAiAnalysisTypeIdx = ref(0)
const zwAiAnalysisTypes = ['overview', 'career', 'love', 'health', 'decadal']
const zwAiGenderIdx = ref(0); const zwAiDateTypeIdx = ref(0)
const zwAiLoading = ref(false); const zwAiResult = ref('')
window._zwChatHistory = []

async function zwAiAsk() {
  if (zwAiLoading.value) return
  var elY = document.getElementById('zwAiYear'); var elM = document.getElementById('zwAiMonth')
  var elD = document.getElementById('zwAiDay'); var elH = document.getElementById('zwAiHour')
  var elMin = document.getElementById('zwAiMinute')
  var y = elY ? parseInt(elY.value) : NaN; var m = elM ? parseInt(elM.value) : NaN
  var d = elD ? parseInt(elD.value) : NaN; var h = elH ? parseInt(elH.value) : NaN
  var min = elMin ? parseInt(elMin.value) : 0
  if (isNaN(y) || isNaN(m) || isNaN(d) || isNaN(h)) {
    uni.showToast({ title: '请填写完整的出生时间', icon: 'none' }); return
  }
  var question = ((document.getElementById('zwAiQuestion') || {}).value || '').trim()
  var gender = ['男', '女'][zwAiGenderIdx.value]
  var date_type = ['solar', 'lunar'][zwAiDateTypeIdx.value]

  // 清理
  zwAiResult.value = ''; window._zwChatHistory = []
  var chatContainer = document.getElementById('zwChatContainer')
  if (chatContainer) chatContainer.innerHTML = ''
  var inputBar = document.getElementById('zwChatInputBar')
  if (inputBar) inputBar.style.display = 'none'
  zwAiLoading.value = true

  var bubbleId = 'zwBubble_' + Date.now()
  var bubbleHTML = '<div class="chat-bubble-ai" id="' + bubbleId + '">' +
    '<div class="ai-stage">🔗 正在连接 DeepSeek AI 引擎...</div>' +
    '<div class="ai-progress-bar"><div class="ai-progress-fill" style="width:20%"></div></div>' +
    '<div class="chat-bubble-content"></div></div>'
  if (chatContainer) chatContainer.innerHTML = bubbleHTML

  _zwDoStreamSSE({
    bubbleId: bubbleId, url: '/api/ziwei/ask/stream',
    body: { year: y, month: m, day: d, hour: h, minute: min, gender: gender, date_type: date_type, question: question, analysis_type: zwAiAnalysisTypes[zwAiAnalysisTypeIdx] },
    question: question,
    onDone: function(fullText) {
      window._zwChatHistory = [{ role: 'user', content: question }, { role: 'assistant', content: fullText }]
      zwAiResult.value = fullText
      var bar = document.getElementById('zwChatInputBar'); if (bar) bar.style.display = 'flex'
    },
    onError: function() { zwAiLoading.value = false }
  })
}

function _zwDoStreamSSE(opts) {
  var bubble = document.getElementById(opts.bubbleId); if (!bubble) return
  var stageEl = bubble.querySelector('.ai-stage'); var barEl = bubble.querySelector('.ai-progress-fill')
  var contentEl = bubble.querySelector('.chat-bubble-content')
  var xhr = new XMLHttpRequest(); xhr.open('POST', opts.url, true); xhr.setRequestHeader('Content-Type', 'application/json')
  var token = ''; try { token = localStorage.getItem('xc_token') || '' } catch(_) {}
  if (token) xhr.setRequestHeader('Authorization', 'Bearer ' + token)
  var lastIndex = 0, fullText = '', charQueue = '', typeTimer = null, doneReceived = false
  function startTypewriter() {
    if (typeTimer) return
    typeTimer = setInterval(function() {
      if (charQueue.length === 0 && doneReceived) {
        clearInterval(typeTimer); typeTimer = null
        if (stageEl) stageEl.style.display = 'none'
        var barWrap = bubble.querySelector('.ai-progress-bar'); if (barWrap) barWrap.style.display = 'none'
        if (contentEl) contentEl.innerHTML = _zwRenderCards(fullText)
        if (opts.onDone) opts.onDone(fullText); return
      }
      if (charQueue.length === 0) return
      var take = charQueue.length > 3 ? 2 : 1
      fullText += charQueue.substring(0, take); charQueue = charQueue.substring(take)
      if (contentEl) contentEl.innerHTML = fullText.replace(/\n/g, '<br>')
    }, 35)
  }
  xhr.onprogress = function() {
    var newText = xhr.responseText.substring(lastIndex); lastIndex = xhr.responseText.length
    var lines = newText.split('\n'), eventType = ''
    for (var i = 0; i < lines.length; i++) {
      var line = lines[i]
      if (line.indexOf('event:') === 0) { eventType = line.replace('event:', '').trim(); continue }
      if (line.indexOf('data:') !== 0) continue
      try {
        var data = JSON.parse(line.replace('data:', '').trim())
        if (eventType === 'progress') {
          if (data.stage === 'connecting' && stageEl) stageEl.innerHTML = '🔗 正在连接...'
          else if (data.stage === 'analyzing' && stageEl) stageEl.innerHTML = '🧠 排盘分析中...'
          else if (data.stage === 'generating' && stageEl) { stageEl.innerHTML = '✍️ 正在生成解读...'; startTypewriter() }
          if (barEl) barEl.style.width = '60%'
        } else if (eventType === 'chunk') { charQueue += data.content }
        else if (eventType === 'done') { doneReceived = true; zwAiLoading.value = false }
        else if (eventType === 'error') { if (stageEl) stageEl.innerHTML = '⚠️ ' + data.message; if (opts.onError) opts.onError() }
        eventType = ''
      } catch(_) {}
    }
  }
  xhr.onerror = function() { if (stageEl) stageEl.innerHTML = '⚠️ 网络错误'; if (opts.onError) opts.onError() }
  xhr.send(JSON.stringify(opts.body))
}

function _zwRenderCards(text) {
  var sections = text.split(/\n(?=#{2,3} )/), html = ''
  sections.forEach(function(sec) {
    var m = sec.match(/^(#{2,3})\s+(.+)/); var title = m ? m[2] : ''
    var body = m ? sec.substring(m[0].length).trim() : sec
    body = body.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')
    if (!body) body = '&nbsp;'
    if (title) html += '<div class="qai-card-item"><div class="qai-card-title">' + title + '</div><div class="qai-card-body"><p>' + body + '</p></div></div>'
  })
  return html
}

function zwSendFollowUp() {
  var input = document.getElementById('zwChatInput'); if (!input) return
  var question = input.value.trim(); if (!question) return; input.value = ''
  var chatContainer = document.getElementById('zwChatContainer'); if (!chatContainer) return
  var userBubble = document.createElement('view'); userBubble.className = 'chat-bubble-user'; userBubble.textContent = question
  chatContainer.appendChild(userBubble)
  var bubbleId = 'zwFollow_' + Date.now()
  var aiBubble = document.createElement('view'); aiBubble.className = 'chat-bubble-ai'; aiBubble.id = bubbleId
  aiBubble.innerHTML = '<div class="ai-stage">✍️ 正在生成回复...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div><div class="chat-bubble-content"></div>'
  chatContainer.appendChild(aiBubble); chatContainer.scrollIntoView({ behavior: 'smooth', block: 'end' })
  var history = window._zwChatHistory || []; history.push({ role: 'user', content: question })
  _zwDoStreamSSE({
    bubbleId: bubbleId, url: '/api/ziwei/ask/stream', body: { question: question, history: history },
    question: question,
    onDone: function(fullText) { history.push({ role: 'assistant', content: fullText }); window._zwChatHistory = history },
    onError: function() {}
  })
}

async function ziweiFreePan() {
  try {
    var elY = document.getElementById('zwYear'); var elM = document.getElementById('zwMonth'); var elD = document.getElementById('zwDay')
    var elH = document.getElementById('zwHour'); var elMin = document.getElementById('zwMinute')
    var y = elY ? parseInt(elY.value) : NaN; var m = elM ? parseInt(elM.value) : NaN; var d = elD ? parseInt(elD.value) : NaN
    var h = elH ? parseInt(elH.value) : NaN; var min = elMin ? parseInt(elMin.value) : 0
    if (isNaN(y) || isNaN(m) || isNaN(d) || isNaN(h)) { zwPanResult.value = '<div style="color:var(--danger);">请填写完整的出生时间</div>'; return }
    const res = await uni.request({ url: '/api/ziwei/pan', method: 'POST', data: { year: y, month: m, day: d, hour: h, minute: min, gender: ['男', '女'][zwGenderIdx.value], date_type: ['solar', 'lunar'][zwDateTypeIdx.value] } })
    const data = res.data
    if (data.error || (data.code && data.code !== 0)) { zwPanResult.value = '<div style="color:var(--danger);">' + (data.error || data.msg || '排盘失败') + '</div>'; return }
    const panData = data.data || data
    zwPanResult.value = renderZiweiPan(panData)
  } catch (e) { zwPanResult.value = '<div style="color:var(--danger);">排盘失败</div>' }
}
async function ziweiHoroscope() {
  try {
    var elY = document.getElementById('zwHYear'); var elM = document.getElementById('zwHMonth'); var elD = document.getElementById('zwHDay'); var elH = document.getElementById('zwHHour')
    var y = elY ? parseInt(elY.value) : NaN; var m = elM ? parseInt(elM.value) : NaN; var d = elD ? parseInt(elD.value) : NaN; var h = elH ? parseInt(elH.value) : NaN
    if (isNaN(y) || isNaN(m) || isNaN(d) || isNaN(h)) { zwHoroscopeResult.value = '<div style="color:var(--danger);">请填写完整的出生时间</div>'; return }
    var now = new Date(); var td = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0')
    const res = await uni.request({ url: '/api/ziwei/horoscope', method: 'POST', data: { year: y, month: m, day: d, hour: h, gender: ['男', '女'][zwHGenderIdx.value], date_type: ['solar', 'lunar'][zwHDateTypeIdx.value], target_date: td } })
    const data = res.data
    if (data.error || (data.code && data.code !== 0)) { zwHoroscopeResult.value = '<div style="color:var(--danger);">' + (data.error || data.msg || '推运失败') + '</div>'; return }
    const horoData = data.data || data
    zwHoroscopeResult.value = renderZiweiHoroscope(horoData)
  } catch (e) { zwHoroscopeResult.value = '<div style="color:var(--danger);">推运失败</div>' }
}

// ═══ 紫微斗数渲染函数 (1:1移植自Flask ziwei.js) ═══
function zwBasicItem(label, value) {
  return `<div class="zw-basic-item"><span class="zw-basic-label">${label}</span><span class="zw-basic-value">${value || ''}</span></div>`
}
function zwPalaceCell(p) {
  if (!p) return '<div class="zw-palace-cell"></div>'
  let cls = 'zw-palace-cell'
  let badge = ''
  if (p.is_body_palace) { cls += ' is-body'; badge += '<span class="zw-palace-badge zw-badge-body">身</span>' }
  if (p.name === '命宫') { cls += ' is-soul'; badge += '<span class="zw-palace-badge zw-badge-soul">命</span>' }
  let starsHtml = ''
  ;(p.major_stars || []).forEach(s => {
    let mut = ''
    if (s.mutagen) {
      let mCls = ''
      if (s.mutagen.includes('禄')) mCls = 'zw-mutagen-lu'
      else if (s.mutagen.includes('权')) mCls = 'zw-mutagen-quan'
      else if (s.mutagen.includes('科')) mCls = 'zw-mutagen-ke'
      else if (s.mutagen.includes('忌')) mCls = 'zw-mutagen-ji'
      mut = `<span class="zw-mutagen ${mCls}">${s.mutagen}</span>`
    }
    const brightness = s.brightness ? `(${s.brightness})` : ''
    starsHtml += `<span class="zw-star-major">${s.name}${brightness}${mut}</span>`
  })
  ;(p.minor_stars || []).forEach(s => {
    starsHtml += `<span class="zw-star-minor">${s.name}</span>`
  })
  ;(p.adjective_stars || []).slice(0, 4).forEach(s => {
    starsHtml += `<span class="zw-star-adj">${s.name}</span>`
  })
  let decHtml = ''
  if (p.decadal && p.decadal.range) {
    decHtml = `<div class="zw-palace-decadal">大限: ${p.decadal.range[0]}-${p.decadal.range[1]}岁 ${p.decadal.heavenly_stem || ''}${p.decadal.earthly_branch || ''}</div>`
  }
  return `<div class="${cls}">
    ${badge}
    <div class="zw-palace-header">
      <span class="zw-palace-name">${p.name}</span>
      <span class="zw-palace-ganzhi">${p.ganzhi || ''}</span>
    </div>
    <div class="zw-palace-stars">${starsHtml}</div>
    ${decHtml}
  </div>`
}
function renderZiweiPan(d) {
  let html = '<div class="zw-result-wrap">'
  const bi = d.basic_info || {}
  const cp = d.core_palace || {}
  html += '<div class="zw-basic-card"><div class="zw-basic-grid">'
  html += zwBasicItem('阳历', bi.solar_date)
  html += zwBasicItem('农历', bi.lunar_date)
  html += zwBasicItem('八字', bi.chinese_date)
  html += zwBasicItem('时辰', (bi.shichen || '') + ' ' + (bi.shichen_range || ''))
  html += zwBasicItem('生肖', bi.zodiac)
  html += zwBasicItem('星座', bi.sign)
  html += zwBasicItem('五行局', cp.five_elements_class)
  html += zwBasicItem('命主', cp.soul_star)
  html += zwBasicItem('身主', cp.body_star)
  html += '</div></div>'
  const palaces = d.twelve_palaces || []
  html += '<div class="zw-palace-grid">'
  html += zwPalaceCell(palaces[4])
  html += zwPalaceCell(palaces[3])
  html += zwPalaceCell(palaces[5])
  html += zwPalaceCell(palaces[6])
  html += zwPalaceCell(palaces[2])
  html += `<div class="zw-center-info">
    <div class="zw-center-title">紫微斗数命盘</div>
    <div class="zw-center-wuxing">${cp.five_elements_class || ''}</div>
    <div class="zw-center-soul">命主: ${cp.soul_star || ''}</div>
    <div class="zw-center-soul">身主: ${cp.body_star || ''}</div>
    <div class="zw-center-date">${bi.solar_date || ''} ${bi.shichen || ''}</div>
  </div>`
  html += zwPalaceCell(palaces[7])
  html += zwPalaceCell(palaces[1])
  html += zwPalaceCell(palaces[8])
  html += zwPalaceCell(palaces[0])
  html += zwPalaceCell(palaces[11])
  html += zwPalaceCell(palaces[10])
  html += zwPalaceCell(palaces[9])
  html += '</div>'
  if (d.decadal_overview && d.decadal_overview.length > 0) {
    html += '<div class="zw-decadal-card">'
    html += '<div class="zw-decadal-title">📅 大限概览</div>'
    html += '<table class="zw-decadal-table">'
    html += '<tr><th>宫位</th><th>年龄范围</th><th>干支</th></tr>'
    d.decadal_overview.forEach(dec => {
      const range = dec.age_range || []
      html += `<tr><td>${dec.palace_name || ''}</td><td>${range[0] || ''}-${range[1] || ''}岁</td><td>${dec.ganzhi || ''}</td></tr>`
    })
    html += '</table></div>'
  }
  html += '<div class="privacy-note" style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>'
  html += '</div>'
  return html
}
function renderZiweiHoroscope(d) {
  const hd = d.horoscope || d
  let html = '<div class="zw-result-wrap">'
  html += `<div class="zw-horoscope-title">🔮 推运信息 - ${d.target_date || ''}</div>`
  html += '<div class="zw-period-grid">'
  const periods = [
    { key: 'decadal', label: '大限' },
    { key: 'age', label: '小限' },
    { key: 'yearly', label: '流年' },
    { key: 'monthly', label: '流月' },
    { key: 'daily', label: '流日' },
    { key: 'hourly', label: '流时' },
  ]
  periods.forEach(p => {
    const pd = hd[p.key]
    if (!pd) return
    html += '<div class="zw-period-card">'
    html += `<div class="zw-period-name">${pd.name || p.label}</div>`
    html += `<div class="zw-period-ganzhi">${pd.ganzhi || ''}</div>`
    if (pd.range) html += `<div class="zw-period-range">${pd.range[0]}-${pd.range[1]}岁</div>`
    if (pd.nominal_age) html += `<div class="zw-period-range">虚岁${pd.nominal_age}</div>`
    if (pd.mutagen && pd.mutagen.length > 0) {
      html += '<div class="zw-period-mutagen">'
      html += '<span style="color:var(--text-4);font-size:0.6875rem;">四化:</span>'
      pd.mutagen.forEach(m => {
        let mCls = ''
        if (m.includes('禄')) mCls = 'zw-mutagen-lu'
        else if (m.includes('权')) mCls = 'zw-mutagen-quan'
        else if (m.includes('科')) mCls = 'zw-mutagen-ke'
        else if (m.includes('忌')) mCls = 'zw-mutagen-ji'
        html += `<span class="zw-mutagen ${mCls}">${m}</span>`
      })
      html += '</div>'
    }
    html += '</div>'
  })
  html += '</div>'
  html += '<div class="privacy-note" style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>'
  html += '</div>'
  return html
}

// ═══ 注入全局样式（合并所有stylesheet） ═══
function _unscopeStyles() {
  if (document.getElementById('zw-unscoped')) return
  let css = ''
  for (let i = 0; i < document.styleSheets.length; i++) {
    try {
      const sheet = document.styleSheets[i]
      if (!sheet.cssRules) continue
      for (let j = 0; j < sheet.cssRules.length; j++) {
        let t = sheet.cssRules[j].cssText
        t = t.replace(/\[data-v-[^\]]*\]/g, '')
        t = t.replace(/-[a-f0-9]{7,}\b/g, '')
        css += t
      }
    } catch(e) {}
  }
  if (!css) return
  const old = document.getElementById('zw-unscoped')
  if (old) old.remove()
  const style = document.createElement('style')
  style.id = 'zw-unscoped'
  style.textContent = css
  document.head.appendChild(style)
}

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

onMounted(() => {
  _unscopeStyles()
  // 全局排盘函数（解决 tabBar 多实例 @tap 失效问题）
  if (!window._xc_ziweiFreePan) {
    window._xc_ziweiFreePan = async function() {
      try {
        var elY = document.getElementById('zwYear'); var elM = document.getElementById('zwMonth'); var elD = document.getElementById('zwDay')
        var elH = document.getElementById('zwHour'); var elMin = document.getElementById('zwMinute')
        var y = elY ? parseInt(elY.value) : NaN; var m = elM ? parseInt(elM.value) : NaN; var d = elD ? parseInt(elD.value) : NaN
        var h = elH ? parseInt(elH.value) : NaN; var min = elMin ? parseInt(elMin.value) : 0
        if (isNaN(y) || isNaN(m) || isNaN(d) || isNaN(h)) { zwPanResult.value = '<div style="color:var(--danger);">请填写完整的出生时间</div>'; return }
        const res = await uni.request({ url: '/api/ziwei/pan', method: 'POST', data: { year: y, month: m, day: d, hour: h, minute: min, gender: ['男', '女'][zwGenderIdx.value], date_type: ['solar', 'lunar'][zwDateTypeIdx.value] } })
        const data = res.data
         if (data.error || (data.code && data.code !== 0)) { zwPanResult.value = '<div style="color:var(--danger);">' + (data.error || data.msg || '排盘失败') + '</div>'; return }
        const panData = data.data || data
        zwPanResult.value = renderZiweiPan(panData)
      } catch (e) { zwPanResult.value = '<div style="color:var(--danger);">排盘失败</div>' }
    }
  }
  if (!window._xc_zwResetPan) {
    window._xc_zwResetPan = function() {
      zwPanResult.value = ''
      try {
        var ids = ['zwYear', 'zwMonth', 'zwDay', 'zwHour', 'zwMinute']
        ids.forEach(function(id) { var el = document.getElementById(id); if (el) el.value = '' })
      } catch(_) {}
    }
  }
  if (!window._xc_ziweiHoroscope) {
    window._xc_ziweiHoroscope = async function() {
      try {
        var elY = document.getElementById('zwHYear'); var elM = document.getElementById('zwHMonth'); var elD = document.getElementById('zwHDay'); var elH = document.getElementById('zwHHour')
        var y = elY ? parseInt(elY.value) : NaN; var m = elM ? parseInt(elM.value) : NaN; var d = elD ? parseInt(elD.value) : NaN; var h = elH ? parseInt(elH.value) : NaN
        if (isNaN(y) || isNaN(m) || isNaN(d) || isNaN(h)) { zwHoroscopeResult.value = '<div style="color:var(--danger);">请填写完整的出生时间</div>'; return }
        var now = new Date(); var td = now.getFullYear() + '-' + String(now.getMonth()+1).padStart(2,'0') + '-' + String(now.getDate()).padStart(2,'0')
        const res = await uni.request({ url: '/api/ziwei/horoscope', method: 'POST', data: { year: y, month: m, day: d, hour: h, gender: ['男', '女'][zwHGenderIdx.value], date_type: ['solar', 'lunar'][zwHDateTypeIdx.value], target_date: td } })
        const data = res.data
        if (data.error || (data.code && data.code !== 0)) { zwHoroscopeResult.value = '<div style="color:var(--danger);">' + (data.error || data.msg || '推运失败') + '</div>'; return }
        const horoData = data.data || data
        zwHoroscopeResult.value = renderZiweiHoroscope(horoData)
      } catch (e) { zwHoroscopeResult.value = '<div style="color:var(--danger);">推运失败</div>' }
    }
  }
  if (!window._xc_zwResetHoroscope) {
    window._xc_zwResetHoroscope = function() {
      zwHoroscopeResult.value = ''
      try {
        var ids = ['zwHYear', 'zwHMonth', 'zwHDay', 'zwHHour']
        ids.forEach(function(id) { var el = document.getElementById(id); if (el) el.value = '' })
      } catch(_) {}
    }
  }
  // 全局Tab切换函数
  if (!window._xc_switchZwTab) {
    window._xc_switchZwTab = function(tab) {
      activeTab.value = tab
    }
  }
  // DOM事件委托：修复<view onclick>在uni-app H5中不生效的问题
  try {
    document.querySelector('.tool-tabs')?.addEventListener('click', function(e) {
      var target = e.target; var depth = 8
      while (target && target !== this && depth > 0) {
        if (target.dataset && target.dataset.zwTab) {
          window._xc_switchZwTab(target.dataset.zwTab); return
        }
        target = target.parentElement; depth--
      }
    })
    document.querySelector('.btn-row')?.addEventListener('click', function(e) {
      var target = e.target; var depth = 8
      while (target && target !== this && depth > 0) {
        if (target.dataset && target.dataset.zwAction) {
          var action = target.dataset.zwAction
          if (action === 'freePan') window._xc_ziweiFreePan()
          else if (action === 'resetPan') window._xc_zwResetPan()
          return
        }
        target = target.parentElement; depth--
      }
    })
    // 推运按钮行（在zwHoroContent内）
    var horoContent = document.getElementById('zwHoroContent')
    if (horoContent) {
      horoContent.addEventListener('click', function(e) {
        var target = e.target; var depth = 8
        while (target && target !== this && depth > 0) {
          if (target.dataset && target.dataset.zwAction) {
            var action = target.dataset.zwAction
            if (action === 'horoscope') window._xc_ziweiHoroscope()
            else if (action === 'resetHoroscope') window._xc_zwResetHoroscope()
            return
          }
          target = target.parentElement; depth--
        }
      })
    }
  } catch(_) {}
  // 创建原生输入框
  function createNativeInput(wrapId, type, placeholder, extra) {
    if (typeof document === 'undefined') return null
    var wrap = document.getElementById(wrapId)
    if (!wrap) return null
    var inp = document.createElement('input')
    inp.type = type
    inp.id = wrapId.replace('-wrap', '')
    if (placeholder) inp.placeholder = placeholder
    inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;transition:border-color 0.2s,box-shadow 0.2s'
    inp.onfocus = function() { this.style.borderColor = 'var(--accent)'; this.style.boxShadow = '0 0 0 2px var(--accent-glow)' }
    inp.onblur = function() { this.style.borderColor = 'var(--input-border)'; this.style.boxShadow = 'none' }
    if (type === 'text') inp.setAttribute('maxlength', extra || '100')
    if (type === 'number') { inp.min = '0'; inp.max = '999' }
    wrap.appendChild(inp)
    return inp
  }
  createNativeInput('zwYear-wrap', 'number', 'yyyy')
  createNativeInput('zwMonth-wrap', 'number', '1-12')
  createNativeInput('zwDay-wrap', 'number', '1-31')
  createNativeInput('zwHour-wrap', 'number', '0-23')
  createNativeInput('zwMinute-wrap', 'number', '0-59')
  createNativeInput('zwHYear-wrap', 'number', 'yyyy')
  createNativeInput('zwHMonth-wrap', 'number', '1-12')
  createNativeInput('zwHDay-wrap', 'number', '1-31')
  createNativeInput('zwHHour-wrap', 'number', '0-23')
  // AI 表单
  createNativeInput('zwAiYear-wrap', 'number', 'yyyy')
  createNativeInput('zwAiMonth-wrap', 'number', '1-12')
  createNativeInput('zwAiDay-wrap', 'number', '1-31')
  createNativeInput('zwAiHour-wrap', 'number', '0-23')
  createNativeInput('zwAiMinute-wrap', 'number', '0-59')
  createNativeInput('zwAiQuestion-wrap', 'text', '请输入您想问的问题', '200')
  const now = new Date()
  // 默认填充当前时间
  var elY = document.getElementById('zwYear'); if (elY) elY.value = now.getFullYear()
  var elM = document.getElementById('zwMonth'); if (elM) elM.value = now.getMonth() + 1
  var elD = document.getElementById('zwDay'); if (elD) elD.value = now.getDate()
  var elH = document.getElementById('zwHour'); if (elH) elH.value = now.getHours()
  var elMin = document.getElementById('zwMinute'); if (elMin) elMin.value = now.getMinutes()
  var elHY = document.getElementById('zwHYear'); if (elHY) elHY.value = now.getFullYear()
  var elHM = document.getElementById('zwHMonth'); if (elHM) elHM.value = now.getMonth() + 1
  var elHD = document.getElementById('zwHDay'); if (elHD) elHD.value = now.getDate()
  var elHH = document.getElementById('zwHHour'); if (elHH) elHH.value = now.getHours()
  zwTargetDate.value = `${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}-${String(now.getDate()).padStart(2,'0')}`
  // 初始化面板显隐
  try {
    var pc = document.getElementById('zwPanContent'); var hc = document.getElementById('zwHoroContent')
    if (pc) pc.style.display = ''; if (hc) hc.style.display = 'none'
  } catch(_) {}
})
</script>

<style>
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --bg-2: rgba(40,45,68,0.80); --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --text-4: rgba(140,130,120,0.80); --border: rgba(255,255,255,0.08); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --bg-2: rgba(245,240,230,0.80); --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --text-4: rgba(120,108,88,0.70); --border: rgba(0,0,0,0.05); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }
.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.tool-hero { padding: 60px 32px 32px; text-align: center; position: relative; overflow: hidden; }
.tool-hero-content { position: relative; z-index: 1; max-width: var(--max-w); margin: 0 auto; }
.tool-hero-title { font-family: var(--font-serif); font-size: 2rem; font-weight: 400; letter-spacing: 4px; color: var(--text-1); margin-bottom: 12px; }
.tool-hero-desc { font-size: 0.9375rem; color: var(--text-3); letter-spacing: 2px; }
.tool-container { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; backdrop-filter: blur(20px); box-shadow: var(--card-shadow); max-width: 720px; margin: 0 auto; }
.incognito-bar { display: flex; align-items: center; justify-content: space-between; padding: 12px 18px; border-radius: 12px; background: rgba(110,195,135,0.06); border: 1px solid rgba(110,195,135,0.12); margin-bottom: 24px; }
.incognito-toggle { display: flex; align-items: center; gap: 6px; font-size: 0.75rem; color: var(--success); }
.incognito-desc { font-size: 0.6875rem; color: var(--success); opacity: 0.7; }
.tool-tabs { display: flex; gap: 4px; margin-bottom: 28px; border-bottom: 1px solid var(--card-border); }
.tool-tab { padding: 12px 20px; border-radius: 10px 10px 0 0; font-size: 0.875rem; cursor: pointer; border: 1px solid transparent; border-bottom: none; color: var(--text-3); background: transparent; }
.tool-tab.active { color: var(--accent); background: var(--accent-glow); border-color: var(--accent); font-weight: 600; }
.tab-badge { font-size: 0.5625rem; padding: 1px 5px; border-radius: 4px; background: var(--accent); color: #fff; margin-left: 4px; }
.tab-badge.free { background: var(--success); }
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 6px; letter-spacing: 1px; }
.form-input, .form-select-picker { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.form-hint { font-size: 0.6875rem; color: var(--text-3); }
.submit-btn { width: 100%; padding: 14px; border-radius: 30px; border: none; background: hsl(35, 38%, 52%); color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; letter-spacing: 2px; margin-top: 8px; text-align: center; }
.btn-row { display: flex; gap: 10px; justify-content: center; margin-top: 16px; }
.btn-row .submit-btn { flex: 1; margin-top: 0; }
.btn-ghost { background: transparent; border: 1px solid var(--card-border); color: var(--text-3); padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; }
.privacy-note { margin-top: 16px; padding: 10px 14px; border-radius: 10px; background: rgba(110,195,135,0.08); border: 1px solid rgba(110,195,135,0.15); font-size: 0.75rem; color: var(--success); text-align: center; }
.zw-form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.zw-result { margin-top: 16px; }
.zw-result-card { background: var(--card-bg); border-radius: 12px; padding: 20px; border: 1px solid var(--card-border); }
.zw-result-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; color: var(--accent); letter-spacing: 2px; }

/* ═══ 紫微斗数排盘结果样式 — 低饱和水墨风格 ═══ */
.zw-result-wrap { margin-top: 24px; font-family: 'STKaiti', 'KaiTi', 'Songti SC', 'Noto Serif SC', serif; }
.zw-basic-card { background: var(--bg-2); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.zw-basic-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
.zw-basic-item { display: flex; flex-direction: column; gap: 2px; }
.zw-basic-label { font-size: 0.7rem; color: var(--text-3); letter-spacing: 2px; }
.zw-basic-value { font-size: 0.95rem; font-weight: 500; color: hsl(38, 35%, 50%); }
.zw-palace-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 20px; }
.zw-palace-cell { background: var(--bg-2); border: 1px solid var(--border); border-radius: 8px; padding: 10px 10px 8px; min-height: 105px; position: relative; transition: all 0.2s; cursor: default; }
.zw-palace-cell:hover { border-color: var(--accent); box-shadow: 0 0 20px rgba(212,168,71,0.06); }
.zw-palace-cell.is-soul { border-color: hsl(38, 40%, 55%); box-shadow: 0 0 14px rgba(212,168,71,0.08); }
.zw-palace-cell.is-body { border-color: hsl(6, 45%, 55%); }
.zw-palace-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
.zw-palace-name { font-size: 0.8rem; font-weight: 600; color: hsl(38, 40%, 48%); letter-spacing: 1px; }
.zw-palace-ganzhi { font-size: 0.65rem; color: var(--text-3); }
.zw-palace-badge { font-size: 0.55rem; padding: 1px 5px; border-radius: 3px; position: absolute; top: 4px; right: 4px; font-family: var(--font-sans); }
.zw-badge-soul { background: rgba(212,168,71,0.12); color: hsl(38, 35%, 50%); }
.zw-badge-body { background: rgba(180,80,60,0.10); color: hsl(6, 40%, 50%); }
.zw-palace-stars { margin-top: 4px; display: flex; flex-wrap: wrap; gap: 3px; font-family: 'STKaiti', 'KaiTi', 'Songti SC', 'Noto Serif SC', serif; }
.zw-star-major { display: inline-block; padding: 2px 7px; background: rgba(180,150,100,0.10); color: hsl(38, 35%, 50%); border-radius: 4px; font-size: 0.78rem; font-weight: 500; letter-spacing: 0.5px; }
.zw-star-minor { display: inline-block; padding: 1px 6px; background: rgba(80,140,180,0.08); color: hsl(204, 30%, 55%); border-radius: 4px; font-size: 0.72rem; font-weight: 400; }
.zw-star-adj { display: inline-block; padding: 1px 4px; color: hsl(145, 25%, 48%); font-size: 0.68rem; font-weight: 400; }
.zw-mutagen { font-size: 0.6rem; padding: 1px 4px; border-radius: 3px; margin-left: 2px; font-weight: 500; font-family: var(--font-sans); }
.zw-mutagen-lu { background: rgba(39,174,96,0.12); color: hsl(145, 30%, 45%); }
.zw-mutagen-quan { background: rgba(180,80,60,0.12); color: hsl(6, 35%, 50%); }
.zw-mutagen-ke { background: rgba(60,130,180,0.12); color: hsl(204, 30%, 50%); }
.zw-mutagen-ji { background: rgba(120,80,150,0.12); color: hsl(282, 25%, 50%); }
.zw-palace-decadal { margin-top: 5px; font-size: 0.65rem; color: var(--text-3); border-top: 1px solid var(--border); padding-top: 4px; letter-spacing: 0.5px; font-family: var(--font-sans); }
.zw-center-info { grid-column: 2 / 4; grid-row: 2 / 4; background: var(--bg-2); border: 1.5px solid hsl(38, 30%, 55%); border-radius: 10px; padding: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.zw-center-title { font-size: 1.05rem; color: hsl(38, 35%, 45%); font-weight: 500; letter-spacing: 3px; margin-bottom: 6px; }
.zw-center-wuxing { font-size: 0.9rem; color: hsl(282, 20%, 48%); font-weight: 500; margin-bottom: 4px; }
.zw-center-soul { font-size: 0.78rem; color: var(--text-2); margin: 1px 0; font-family: var(--font-sans); }
.zw-center-date { font-size: 0.72rem; color: var(--text-3); margin-top: 4px; }
.zw-decadal-card { background: var(--bg-2); border: 1px solid var(--border); border-radius: 10px; padding: 18px; margin-bottom: 18px; }
.zw-decadal-title { font-size: 0.9rem; font-weight: 500; color: hsl(38, 35%, 48%); margin-bottom: 12px; display: flex; align-items: center; gap: 6px; font-family: 'STKaiti', 'KaiTi', 'Songti SC', 'Noto Serif SC', serif; }
.zw-decadal-table { width: 100%; border-collapse: collapse; font-size: 0.78rem; font-family: var(--font-sans); }
.zw-decadal-table th, .zw-decadal-table td { padding: 6px 8px; text-align: center; border-bottom: 1px solid var(--border); }
.zw-decadal-table th { color: var(--text-3); font-weight: 500; font-size: 0.7rem; letter-spacing: 1px; }
.zw-decadal-table td { color: var(--text-1); }
.zw-horoscope-title { font-size: 0.9rem; font-weight: 500; color: hsl(282, 20%, 48%); margin-bottom: 14px; font-family: 'STKaiti', 'KaiTi', 'Songti SC', 'Noto Serif SC', serif; }
.zw-period-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 10px; }
.zw-period-card { background: var(--bg-2); border: 1px solid var(--border); border-radius: 8px; padding: 12px; transition: all 0.2s; font-family: var(--font-sans); }
.zw-period-card:hover { border-color: hsl(282, 20%, 55%); box-shadow: 0 0 10px rgba(120,80,150,0.08); }
.zw-period-name { font-weight: 500; color: hsl(38, 35%, 48%); margin-bottom: 3px; font-size: 0.82rem; letter-spacing: 1px; }
.zw-period-ganzhi { font-size: 0.82rem; color: hsl(282, 20%, 48%); font-weight: 500; }
.zw-period-range { font-size: 0.7rem; color: var(--text-3); margin-top: 2px; }
.zw-period-mutagen { font-size: 0.72rem; color: var(--text-2); margin-top: 4px; display: flex; flex-wrap: wrap; gap: 4px; }
@media (max-width: 768px) { .zw-palace-grid { grid-template-columns: repeat(2, 1fr); } .zw-center-info { grid-column: 1 / -1; grid-row: auto; } .zw-form-grid { grid-template-columns: 1fr 1fr; } .zw-basic-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 480px) {
  .zw-palace-grid { gap: 4px; }
  .zw-palace-cell { min-height: 72px; padding: 5px; }
  .zw-palace-header { margin-bottom: 3px; }
  .zw-palace-name { font-size: 0.68rem; }
  .zw-palace-ganzhi { font-size: 0.55rem; }
  .zw-palace-stars { gap: 2px; }
  .zw-star-major { font-size: 0.62rem; padding: 1px 4px; }
  .zw-star-minor { font-size: 0.58rem; padding: 1px 3px; }
  .zw-star-adj { font-size: 0.55rem; padding: 0 3px; }
  .zw-mutagen { font-size: 0.52rem; padding: 0 3px; }
  .zw-palace-decadal { font-size: 0.55rem; margin-top: 3px; padding-top: 3px; }
  .zw-center-title { font-size: 0.82rem; }
  .zw-center-wuxing { font-size: 0.72rem; }
  .zw-center-soul { font-size: 0.62rem; }
  .zw-center-date { font-size: 0.58rem; }
  .zw-basic-card { padding: 14px; }
  .zw-basic-grid { gap: 6px; }
  .zw-basic-label { font-size: 0.6rem; }
  .zw-basic-value { font-size: 0.78rem; }
  .zw-period-grid { grid-template-columns: 1fr 1fr; gap: 6px; }
  .zw-period-card { padding: 8px; }
  .zw-period-name { font-size: 0.72rem; }
  .zw-period-ganzhi { font-size: 0.72rem; }
  .zw-period-range { font-size: 0.6rem; }
  .zw-period-mutagen { font-size: 0.62rem; }
  .zw-palace-badge { font-size: 0.5rem; padding: 0 4px; }
}
.site-footer { background: var(--nav-bg); border-top: 1px solid var(--card-border); padding: 48px 32px 24px; margin-top: 80px; }
.footer-disclaimer { max-width: var(--max-w); margin: 0 auto 32px; padding: 14px 20px; border-radius: 10px; background: rgba(215,125,110,0.08); border: 1px solid rgba(215,125,110,0.15); font-size: 0.75rem; color: var(--danger); line-height: 1.6; text-align: center; }
.footer-grid { max-width: var(--max-w); margin: 0 auto; display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 40px; }
.footer-col-title { font-size: 0.8125rem; color: var(--text-2); margin-bottom: 12px; }
.footer-col navigator { display: block; font-size: 0.75rem; color: var(--text-3); text-decoration: none; padding: 3px 0; }
.footer-icp { font-size: 0.6875rem; color: var(--text-3); margin-top: 8px; }
.modal-overlay { display: none; position: fixed; inset: 0; z-index: 300; background: rgba(0,0,0,0.55); backdrop-filter: blur(8px); align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; width: 360px; backdrop-filter: blur(40px); }
.modal-title { font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px; text-align: center; margin-bottom: 24px; color: var(--text-1); }
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: var(--danger); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }
@media (max-width: 768px) { .tool-hero { padding: 40px 16px 24px; } .tool-hero-title { font-size: 1.5rem; } .tool-container { padding: 20px 16px; } .section { padding: 48px 16px; } .footer-grid { grid-template-columns: 1fr; gap: 24px; } .zw-form-grid { grid-template-columns: 1fr 1fr; } }

/* ═══ 流式解读 + 对话气泡 ═══ */
.qai-stream-box { margin-top: 20px; padding: 16px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 14px; }
.qai-card-item { background: var(--section-alt); border: 1px solid var(--card-border); border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; }
.qai-card-title { font-size: 0.9rem; font-weight: 700; color: var(--accent); margin-bottom: 6px; }
.qai-card-body { font-size: 0.82rem; color: var(--text-2); line-height: 1.7; }
.qai-card-body strong { color: var(--text-1); }
.chat-container { display: flex; flex-direction: column; gap: 12px; }
.chat-bubble-ai { align-self: flex-start; background: var(--section-alt); border: 1px solid var(--card-border); border-radius: 14px 14px 14px 4px; padding: 16px 20px; max-width: 92%; width: 100%; box-sizing: border-box; }
.chat-bubble-user { align-self: flex-end; background: var(--accent); color: #fff; border-radius: 14px 14px 4px 14px; padding: 10px 16px; max-width: 80%; font-size: 0.9rem; line-height: 1.5; }
.chat-bubble-content { font-size: 0.875rem; color: var(--text-2); line-height: 1.9; }
.ai-stage { font-size: 0.9rem; color: var(--text-1); margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
.ai-progress-bar { height: 4px; background: var(--card-border); border-radius: 2px; overflow: hidden; margin-bottom: 16px; }
.ai-progress-fill { height: 100%; width: 20%; background: linear-gradient(90deg, var(--accent), #8b5cf6); border-radius: 2px; animation: ai-progress-pulse 1.5s ease-in-out infinite; transition: width 0.3s ease; }
@keyframes ai-progress-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.chat-input-bar { display: flex; gap: 8px; margin-top: 16px; padding: 10px 14px; background: var(--section-alt); border-radius: 12px; border: 1px solid var(--card-border); }
.chat-input { flex: 1; padding: 8px 14px; border-radius: 8px; border: 1px solid var(--card-border); background: var(--input-bg); color: var(--text-1); font-size: 0.875rem; outline: none; }
.chat-send-btn { padding: 8px 20px; background: var(--accent); color: #fff; border-radius: 8px; font-size: 0.875rem; cursor: pointer; white-space: nowrap; }

/* 分析类型选择器 */
.analysis-type-row { display: flex; flex-wrap: wrap; gap: 6px; }
.analysis-type-btn { padding: 6px 12px; border-radius: 8px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.75rem; cursor: pointer; text-align: center; white-space: nowrap; transition: all .15s; }
.analysis-type-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }
</style>
