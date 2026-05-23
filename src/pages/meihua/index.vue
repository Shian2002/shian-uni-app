<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />
    <view class="page-wrap">
      <section class="tool-hero"><view class="tool-hero-content"><view class="section-tag">梅花易数</view><view class="tool-hero-title">梅花易数 · 万物皆可起卦</view><view class="tool-hero-desc">数字起卦 · 时间起卦 · 字数起卦 · 体用生克 · 断事知机</view></view></section>
      <section class="section">
        <view class="tool-container">
          <view class="incognito-bar"><label class="incognito-toggle"><input type="checkbox" :checked="incognito" @change="incognito = !incognito" /><text>{{ incognito ? '🔒 无痕模式' : '🔓 有痕模式' }}</text></label><text class="incognito-desc">本地计算 · 不上传数据 · 退出自动清空</text></view>
          <view class="tool-tabs">
            <view class="tool-tab" id="mhTabFree" :class="{ active: activeTab === 'free' }" @tap.stop="switchMhTab('free')">🌸 梅花排盘<text class="tab-badge free">免费</text></view>
            <view class="tool-tab" id="mhTabAi" :class="{ active: activeTab === 'ai' }" @tap.stop="switchMhTab('ai')">🔮 时安梅花系统<text class="tab-badge">PRO</text></view>
          </view>

          <!-- 免费排盘 -->
          <view class="tool-tab-content" id="mhTabFreeContent">
            <view class="method-switch">
              <view class="method-switch-btn" id="mhFreeTimeBtn" :class="{ active: mhMethod === 'time' }" @tap.stop="switchMhMethod('time')">⏰ 时间起卦</view>
              <view class="method-switch-btn" id="mhFreeNumBtn" :class="{ active: mhMethod === 'number' }" @tap.stop="switchMhMethod('number')">🔢 数字起卦</view>
              <view class="method-switch-btn" id="mhFreeWordBtn" :class="{ active: mhMethod === 'word' }" @tap.stop="switchMhMethod('word')">✍️ 字数起卦</view>
            </view>

            <view id="mhFreeTimeContent">
              <view class="mh-method-content"><view class="form-group"><text class="form-label">🕐 起卦时间</text><view class="qf-datetime-row"><view class="qf-dt-col"><select id="mfYear" class="qf-datetime-select"></select></view><view class="qf-dt-col"><select id="mfMonth" class="qf-datetime-select"></select></view><view class="qf-dt-col"><select id="mfDay" class="qf-datetime-select"></select></view><view class="qf-dt-col"><select id="mfHour" class="qf-datetime-select"></select></view><view class="qf-dt-col qf-dt-col-narrow"><select id="mfMinute" class="qf-datetime-select"></select></view></view></view></view>
              <text class="form-hint">以当前时间自动起卦，依据年月日时数字推算上下卦与动爻</text>
            </view>
            <view id="mhFreeNumContent" style="display:none;">
              <view class="mh-method-content"><view class="mh-num-row"><view class="form-group"><text class="form-label">第一个数字</text><view id="mf-num1-wrap" class="dom-input-wrap"></view></view><view class="form-group"><text class="form-label">第二个数字</text><view id="mf-num2-wrap" class="dom-input-wrap"></view></view></view></view>
              <text class="form-hint">第一个数字除8余数为上卦，第二个数字除8余数为下卦，两数之和除6余数为动爻</text>
            </view>
            <view id="mhFreeWordContent" style="display:none;">
              <view class="mh-method-content"><view class="form-group"><text class="form-label">输入文字</text><view id="mf-words-wrap" class="dom-input-wrap"></view></view></view>
              <text class="form-hint">字数前半为上卦，后半为下卦，总字数除6为动爻</text>
            </view>

            <view class="form-group" style="margin-top:16px;"><text class="form-label">你的问题（选填）</text><view id="mf-question-wrap" class="dom-input-wrap"></view></view>
            <view class="btn-row">
              <view class="submit-btn" @tap="meihuaFreePaipan">🌸 免费排盘</view>
            </view>
            <text class="form-hint" style="text-align:center;display:block;margin-top:12px;">本地精准排盘，体用生克全分析。如需深度解读请使用时安梅花系统。</text>
            <view class="privacy-note">✅ 本地计算 · 不上传数据 · 秒出结果</view>
            <view class="mh-result" id="mhFreeResult"></view>
          </view>

          <!-- AI系统 -->
          <view class="tool-tab-content" id="mhTabAiContent" style="display:none;">
            <view class="form-group"><text class="form-label">问事类型</text><select id="mai-type" class="form-select" @change="onMaiTypeChangeDom($event)"></select></view>
            <view class="method-switch" style="margin-bottom:16px;">
              <view class="method-switch-btn" id="mhAiTimeBtn" :class="{ active: maiMethod === 'time' }" @tap.stop="switchMaiMethod('time')">⏰ 时间起卦</view>
              <view class="method-switch-btn" id="mhAiNumBtn" :class="{ active: maiMethod === 'number' }" @tap.stop="switchMaiMethod('number')">🔢 数字起卦</view>
              <view class="method-switch-btn" id="mhAiWordBtn" :class="{ active: maiMethod === 'word' }" @tap.stop="switchMaiMethod('word')">✍️ 字数起卦</view>
            </view>
            <view id="mhAiTimeContent"><view class="mh-method-content"><view class="form-group"><text class="form-label">🕐 起卦时间</text><view class="qf-datetime-row"><view class="qf-dt-col"><select id="maiYear" class="qf-datetime-select"></select></view><view class="qf-dt-col"><select id="maiMonth" class="qf-datetime-select"></select></view><view class="qf-dt-col"><select id="maiDay" class="qf-datetime-select"></select></view><view class="qf-dt-col"><select id="maiHour" class="qf-datetime-select"></select></view><view class="qf-dt-col qf-dt-col-narrow"><select id="maiMinute" class="qf-datetime-select"></select></view></view></view></view></view>
            <view id="mhAiNumContent" style="display:none;"><view class="mh-method-content"><view class="mh-num-row"><view class="form-group"><text class="form-label">第一个数字</text><view id="mai-num1-wrap" class="dom-input-wrap"></view></view><view class="form-group"><text class="form-label">第二个数字</text><view id="mai-num2-wrap" class="dom-input-wrap"></view></view></view></view></view>
            <view id="mhAiWordContent" style="display:none;"><view class="mh-method-content"><view class="form-group"><text class="form-label">输入文字</text><view id="mai-words-wrap" class="dom-input-wrap"></view></view></view></view>
            <view class="form-group"><text class="form-label">你的问题（选填）</text><view id="mai-question-wrap" class="dom-input-wrap"></view></view>
            <view class="qai-deep-row"><view class="qai-deep-toggle" id="maiDeepToggle" @tap.stop="toggleDeepMode()"><text class="qai-toggle-label">深度分析</text><view class="qai-toggle-track"><view class="qai-toggle-knob"></view></view></view></view>
            <view class="btn-row">
              <view class="submit-btn" @tap="meihuaAskPaipan">🔮 一键起卦 · 深度解读</view>
            </view>
            <view class="qai-progress" id="mhAiProgress">
              <view class="qai-progress-bar"><view class="qai-progress-fill" id="mhAiProgressFill" style="width:0%;"></view></view>
              <view class="qai-step-text" id="mhAiStepText">准备中...</view>
            </view>
            <view class="qai-result" id="mhAiResult"></view>
            <view class="result-mode-switch"><view class="result-mode-btn" id="mhResultSimpleBtn" @tap.stop="switchResultMode('simple')">小白极简版</view><view class="result-mode-btn" id="mhResultProBtn" @tap.stop="switchResultMode('pro')">专业深度版</view></view>
            <view class="privacy-note incognito-status">✅ 无痕模式已开启 · 本地计算 · 不上传数据 · 退出自动清空</view>
          </view>
        </view>
      </section>
    </view>
    <view class="site-footer"><view class="footer-disclaimer">⚠️ 本站所有内容仅为民俗文化与传统命理科普参考，不构成任何决策建议，严禁利用本站内容从事封建迷信及违法违规活动，本站不对任何用户基于本站内容做出的决策承担任何责任</view><view class="footer-grid"><view class="footer-col"><view class="footer-col-title">平台信息</view><navigator url="/package-info/about/index">关于我们</navigator></view><view class="footer-col"><view class="footer-col-title">快捷导航</view><navigator url="/pages/qimen/index" open-type="switchTab">奇门遁甲</navigator><navigator url="/pages/bazi-index/index" open-type="switchTab">八字排盘</navigator><navigator url="/pages/meihua/index" open-type="switchTab">梅花易数</navigator><navigator url="/pages/calendar/index" open-type="switchTab">专属日历</navigator></view><view class="footer-col"><view class="footer-col-title">备案与版权</view><view class="footer-icp">ICP备案号：京ICP备2026050601号-1</view><view class="footer-icp">© 2026 时安解忧屋 版权所有</view></view></view></view>
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
const incognito = ref(true); const activeTab = ref('free')

// ═══ Tab/Method切换: DOM直操作 (绕过Vue 3.4.21 render effect bug) ═══
// ── 深度分析/结果模式切换 ──
function toggleDeepMode() {
  var toggle = document.getElementById('maiDeepToggle')
  if (!toggle) return
  toggle.classList.toggle('active')
}
function switchResultMode(mode) {
  var simpleBtn = document.getElementById('mhResultSimpleBtn')
  var proBtn = document.getElementById('mhResultProBtn')
  if (simpleBtn) { mode === 'simple' ? simpleBtn.classList.add('active') : simpleBtn.classList.remove('active') }
  if (proBtn) { mode === 'pro' ? proBtn.classList.add('active') : proBtn.classList.remove('active') }
}
function isDeepMode() {
  var toggle = document.getElementById('maiDeepToggle')
  return toggle && toggle.classList.contains('active')
}

function switchMhTab(tab) {
  activeTab.value = tab
  var free = document.getElementById('mhTabFreeContent')
  var ai = document.getElementById('mhTabAiContent')
  var btnFree = document.getElementById('mhTabFree')
  var btnAi = document.getElementById('mhTabAi')
  if (free) free.style.display = tab === 'free' ? 'block' : 'none'
  if (ai) ai.style.display = tab === 'ai' ? 'block' : 'none'
  if (btnFree) { tab === 'free' ? btnFree.classList.add('active') : btnFree.classList.remove('active') }
  if (btnAi) { tab === 'ai' ? btnAi.classList.add('active') : btnAi.classList.remove('active') }
}

function switchMhMethod(m) {
  mhMethod.value = m
  var time = document.getElementById('mhFreeTimeContent')
  var num = document.getElementById('mhFreeNumContent')
  var word = document.getElementById('mhFreeWordContent')
  var timeBtn = document.getElementById('mhFreeTimeBtn')
  var numBtn = document.getElementById('mhFreeNumBtn')
  var wordBtn = document.getElementById('mhFreeWordBtn')
  if (time) time.style.display = m === 'time' ? 'block' : 'none'
  if (num) num.style.display = m === 'number' ? 'block' : 'none'
  if (word) word.style.display = m === 'word' ? 'block' : 'none'
  if (timeBtn) { m === 'time' ? timeBtn.classList.add('active') : timeBtn.classList.remove('active') }
  if (numBtn) { m === 'number' ? numBtn.classList.add('active') : numBtn.classList.remove('active') }
  if (wordBtn) { m === 'word' ? wordBtn.classList.add('active') : wordBtn.classList.remove('active') }
}

function switchMaiMethod(m) {
  maiMethod.value = m
  var time = document.getElementById('mhAiTimeContent')
  var num = document.getElementById('mhAiNumContent')
  var word = document.getElementById('mhAiWordContent')
  var timeBtn = document.getElementById('mhAiTimeBtn')
  var numBtn = document.getElementById('mhAiNumBtn')
  var wordBtn = document.getElementById('mhAiWordBtn')
  if (time) time.style.display = m === 'time' ? 'block' : 'none'
  if (num) num.style.display = m === 'number' ? 'block' : 'none'
  if (word) word.style.display = m === 'word' ? 'block' : 'none'
  if (timeBtn) { m === 'time' ? timeBtn.classList.add('active') : timeBtn.classList.remove('active') }
  if (numBtn) { m === 'number' ? numBtn.classList.add('active') : numBtn.classList.remove('active') }
  if (wordBtn) { m === 'word' ? wordBtn.classList.add('active') : wordBtn.classList.remove('active') }
}

// 免费排盘
const mhMethod = ref('time')

function onMaiTypeChangeDom(e) {
  const val = e.target.value
  const questionInput = document.getElementById('mai-question')
  if (!questionInput) return
  const MAI_SCENE_QUESTIONS = { s_project: '这个项目能否成功？需要注意什么？', s_loveback: '我和对方复合的最佳时机是什么时候？', s_interview: '我的面试能否通过？有什么需要准备的？', s_house: '这套房子风水如何？适合购买或租住吗？', s_travel: '近期出行是否安全？需要注意什么？', s_lawsuit: '这场官司诉讼的走向如何？有什么策略？' }
  if (MAI_SCENE_QUESTIONS[val]) { questionInput.value = MAI_SCENE_QUESTIONS[val]; questionInput.focus() }
}

async function meihuaFreePaipan() {
  const resultEl = document.getElementById('mhFreeResult')
  if (!resultEl) return
  resultEl.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-3);">🧭 排盘计算中...</div>'
  try {
    const payload = { method: mhMethod.value }
    if (mhMethod.value === 'time') {
      const y = document.getElementById('mfYear')?.value
      const m = document.getElementById('mfMonth')?.value
      const d = document.getElementById('mfDay')?.value
      const h = document.getElementById('mfHour')?.value || '12'
      const mi = document.getElementById('mfMinute')?.value || '0'
      if (y && m && d) payload.time = y + '-' + m + '-' + d + 'T' + h + ':' + mi
    } else if (mhMethod.value === 'number') {
      const n1 = document.getElementById('mf-num1')?.value
      if (!n1) { resultEl.innerHTML = '<div style="color:var(--danger);padding:16px;">请输入第一个数字</div>'; return }
      payload.num1 = parseInt(n1)
      const n2 = document.getElementById('mf-num2')?.value
      if (n2) payload.num2 = parseInt(n2)
    } else if (mhMethod.value === 'word') {
      const w = document.getElementById('mf-words')?.value
      if (!w || !w.trim()) { resultEl.innerHTML = '<div style="color:var(--danger);padding:16px;">请输入文字</div>'; return }
      payload.words = w.trim()
    }
    const q = document.getElementById('mf-question')?.value
    if (q && q.trim()) payload.question = q.trim()
    const res = await uni.request({ url: '/api/meihua/paipan', method: 'POST', data: payload })
    const data = res.data
    if (data.error) { resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">${data.error}</div>`; return }
    const panData = data.data || data
    _unscopeStyles()
    resultEl.innerHTML = renderMeihuaResult(panData)
  } catch (e) { resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">排盘失败</div>` }
}

// ═══ 梅花易数渲染函数 (1:1移植自Flask meihua.js) ═══
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
function renderGuaCard(label, gua, cardClass, dongYao, yaoList) {
  if (!gua) return ''
  const upper = gua.upper || {}
  const lower = gua.lower || {}
  let html = `<div class="gua-card ${cardClass}">`
  html += `<div class="gua-card-label">${label}</div>`
  html += `<div class="gua-card-name">${gua.name || ''}</div>`
  if (yaoList && yaoList.length === 6) {
    html += '<div class="gua-yao-wrap">'
    for (let i = 5; i >= 0; i--) {
      const isYang = yaoList[i] === 1
      const isDong = (i + 1) === dongYao
      html += `<div class="gua-yao ${isYang ? 'yang' : 'yin'} ${isDong ? 'dong-yao' : ''}">`
      if (isYang) {
        html += '<div class="gua-yao-line"></div>'
      } else {
        html += '<div class="gua-yao-line"></div><div class="gua-yao-line"></div>'
      }
      html += '</div>'
    }
    html += '</div>'
  } else {
    html += `<div class="gua-trigram">${upper.trigram || ''}${lower.trigram || ''}</div>`
  }
  html += '<div class="gua-sub-info">'
  html += `<span>上卦 ${upper.name || ''}·${upper.nature || ''}·${upper.wuxing || ''}</span>`
  html += `<span>下卦 ${lower.name || ''}·${lower.nature || ''}·${lower.wuxing || ''}</span>`
  html += '</div>'
  html += '</div>'
  return html
}
function renderMeihuaResult(d) {
  let html = '<div class="mh-result-wrap">'
  html += '<div class="mh-summary">'
  html += `<span><b>起卦方式：</b>${d.methodLabel || '时间起卦'}</span>`
  html += `<span><b>排盘时间：</b>${d.paipanTime || ''}</span>`
  if (d.ganzhi) html += `<span><b>干支：</b>${d.ganzhi}</span>`
  html += '</div>'
  html += '<div class="gua-display">'
  html += renderGuaCard('本卦', d.benGua, 'ben-gua', d.dongYao, d.benGuaYao || null)
  html += renderGuaCard('互卦', d.huGua, 'hu-gua', 0, d.huGuaYao || null)
  html += renderGuaCard('变卦', d.bianGua, 'bian-gua', 0, d.bianGuaYao || null)
  html += '</div>'
  if (d.tiYong) {
    html += '<div class="ti-yong-section">'
    html += '<div class="ti-yong-title">🌸 体用分析</div>'
    html += '<div class="ti-yong-grid">'
    html += `<div class="ti-yong-box ti">
      <div class="ti-yong-label">体卦（${d.tiYong.tiPosition}）</div>
      <div class="ti-yong-gua">${d.tiYong.tiGua}</div>
      <div class="ti-yong-wx">
        ${d.tiYong.tiTrigram || ''}
        <span class="wx-tag ${wxClass(d.tiYong.tiWuxing)}">${d.tiYong.tiWuxing}</span>
        <span class="ws-tag ${wsClass(d.tiYong.tiWangshuai)}">${d.tiYong.tiWangshuai}</span>
      </div>
    </div>`
    html += `<div class="ti-yong-rel ${relClass(d.tiYong.tiYongRel)}">
      体${d.tiYong.tiWuxing} ${d.tiYong.tiYongRel} 用${d.tiYong.yongWuxing}
    </div>`
    html += `<div class="ti-yong-box yong">
      <div class="ti-yong-label">用卦（${d.tiYong.yongPosition}）</div>
      <div class="ti-yong-gua">${d.tiYong.yongGua}</div>
      <div class="ti-yong-wx">
        ${d.tiYong.yongTrigram || ''}
        <span class="wx-tag ${wxClass(d.tiYong.yongWuxing)}">${d.tiYong.yongWuxing}</span>
        <span class="ws-tag ${wsClass(d.tiYong.yongWangshuai)}">${d.tiYong.yongWangshuai}</span>
      </div>
    </div>`
    html += '</div>'
    html += '<table class="mh-analysis-table">'
    html += '<tr><th>分析项</th><th>关系</th><th>吉凶</th></tr>'
    if (d.tiYong.tiYongJiXiong) {
      html += `<tr><td>体用关系</td><td>体${d.tiYong.tiWuxing} ${d.tiYong.tiYongRel} 用${d.tiYong.yongWuxing}</td><td>${d.tiYong.tiYongJiXiong}</td></tr>`
    }
    if (d.tiYong.tiHuRel) {
      html += `<tr><td>互卦与体</td><td>体${d.tiYong.tiWuxing} ${d.tiYong.tiHuRel} 互${d.tiYong.huWuxing || ''}</td><td>-</td></tr>`
    }
    if (d.tiYong.tiBianRel) {
      html += `<tr><td>变卦与体</td><td>体${d.tiYong.tiWuxing} ${d.tiYong.tiBianRel} 变${d.tiYong.bianWuxing || ''}</td><td>-</td></tr>`
    }
    html += '</table>'
    if (d.tiYong.verdict) {
      html += `<div class="mh-verdict">${d.tiYong.verdict}</div>`
    }
    html += '</div>'
  }
  html += '<div class="privacy-note" style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>'
  html += '</div>'
  return html
}

// AI
const maiTypeLabels = ['事业财运', '姻缘感情', '学业考试', '健康出行', '百事占断', '💰 项目能否成功', '💕 感情复合时机', '💼 面试能否通过', '🏠 买房租房吉凶', '✈️ 出行安全预判', '⚖️ 官司诉讼参考']
const maiTypeValues = ['career', 'love', 'study', 'health', 'general', 's_project', 's_loveback', 's_interview', 's_house', 's_travel', 's_lawsuit']
const maiTypeIdx = ref(0); const maiMethod = ref('time')
const maiLoading = ref(false)

const MAI_SCENE_QUESTIONS = { s_project: '这个项目能否成功？需要注意什么？', s_loveback: '我和对方复合的最佳时机是什么时候？', s_interview: '我的面试能否通过？有什么需要准备的？', s_house: '这套房子风水如何？适合购买或租住吗？', s_travel: '近期出行是否安全？需要注意什么？', s_lawsuit: '这场官司诉讼的走向如何？有什么策略？' }
async function meihuaAskPaipan() {
  maiLoading.value = true
  var progressEl = document.getElementById('mhAiProgress')
  var fillEl = document.getElementById('mhAiProgressFill')
  var stepEl = document.getElementById('mhAiStepText')
  var resultEl = document.getElementById('mhAiResult')
  if (progressEl) progressEl.style.display = 'block'
  if (fillEl) fillEl.style.width = '10%'
  if (stepEl) stepEl.textContent = '起卦中...'
  if (resultEl) resultEl.innerHTML = ''
  try {
    const typeSelect = document.getElementById('mai-type')
    const typeVal = typeSelect ? typeSelect.value : 'general'
    const questionInput = document.getElementById('mai-question')
    const question = questionInput ? questionInput.value : ''
    const payload = { method: maiMethod.value, type: typeVal || 'general', question: question, deepMode: isDeepMode() }
    if (maiMethod.value === 'time') {
      const y = document.getElementById('maiYear')?.value
      const m = document.getElementById('maiMonth')?.value
      const d = document.getElementById('maiDay')?.value
      const h = document.getElementById('maiHour')?.value || '12'
      const mi = document.getElementById('maiMinute')?.value || '0'
      if (y && m && d) payload.time = y + '-' + m + '-' + d + 'T' + h + ':' + mi
    } else if (maiMethod.value === 'number') {
      const n1 = document.getElementById('mai-num1')?.value
      if (!n1) { if (resultEl) resultEl.innerHTML = '<div class="qai-error">请输入第一个数字</div>'; maiLoading.value = false; if (progressEl) progressEl.style.display = 'none'; return }
      payload.num1 = parseInt(n1)
      const n2 = document.getElementById('mai-num2')?.value
      if (n2) payload.num2 = parseInt(n2)
    } else if (maiMethod.value === 'word') {
      const w = document.getElementById('mai-words')?.value
      if (!w || !w.trim()) { if (resultEl) resultEl.innerHTML = '<div class="qai-error">请输入文字</div>'; maiLoading.value = false; if (progressEl) progressEl.style.display = 'none'; return }
      payload.words = w.trim()
    }
    if (fillEl) fillEl.style.width = '30%'
    if (stepEl) stepEl.textContent = '排盘计算中...'
    const res = await uni.request({ url: '/api/meihua/ask', method: 'POST', data: payload })
    if (fillEl) fillEl.style.width = '80%'
    if (stepEl) stepEl.textContent = 'AI解读中...'
    const data = res.data
    if (resultEl) {
      if (data.error) { resultEl.innerHTML = `<div class="qai-error">${data.error}</div>` }
      else { resultEl.innerHTML = `<div class="qai-markdown">${data.result || data.markdown || '排盘完成'}</div>` }
    }
    if (fillEl) fillEl.style.width = '100%'
    if (stepEl) stepEl.textContent = '完成'
  } catch (e) { var resultEl = document.getElementById('mhAiResult'); if (resultEl) resultEl.innerHTML = `<div class="qai-error">请求失败</div>` }
  setTimeout(function() {
    maiLoading.value = false
    var progressEl = document.getElementById('mhAiProgress')
    if (progressEl) progressEl.style.display = 'none'
  }, 500)
}

// ═══ 注入全局样式（合并所有stylesheet） ═══
function _unscopeStyles() {
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
  const old = document.getElementById('mh-unscoped')
  if (old) old.remove()
  const style = document.createElement('style')
  style.id = 'mh-unscoped'
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
  // 初始化DOM状态 (绕过Vue 3.4.21 render effect bug)
  var tabAi = document.getElementById('mhTabAiContent')
  var tabFree = document.getElementById('mhTabFreeContent')
  if (tabAi) tabAi.style.display = 'none'
  if (tabFree) tabFree.style.display = 'block'
  var freeNum = document.getElementById('mhFreeNumContent')
  var freeWord = document.getElementById('mhFreeWordContent')
  if (freeNum) freeNum.style.display = 'none'
  if (freeWord) freeWord.style.display = 'none'
  var aiNum = document.getElementById('mhAiNumContent')
  var aiWord = document.getElementById('mhAiWordContent')
  if (aiNum) aiNum.style.display = 'none'
  if (aiWord) aiWord.style.display = 'none'
  var progress = document.getElementById('mhAiProgress')
  if (progress) progress.style.display = 'none'
  // ── 初始化日期选择器（仿Flask风格，原生DOM填充） ──
  const now = new Date()
  const curYear = now.getFullYear()
  ;['mf','mai'].forEach(function(prefix) {
    var yearSel = document.getElementById(prefix + 'Year')
    if (!yearSel) return
    yearSel.innerHTML = '<option value="" selected disabled>年</option>'
    for (var y = curYear; y >= 1920; y--) {
      var opt = document.createElement('option')
      opt.value = y; opt.textContent = y + '年'
      yearSel.appendChild(opt)
    }
    var monthSel = document.getElementById(prefix + 'Month')
    if (monthSel) {
      monthSel.innerHTML = '<option value="" selected disabled>月</option>'
      for (var m = 1; m <= 12; m++) {
        var opt = document.createElement('option')
        opt.value = String(m).padStart(2,'0'); opt.textContent = m + '月'
        monthSel.appendChild(opt)
      }
    }
    var hourSel = document.getElementById(prefix + 'Hour')
    if (hourSel) {
      hourSel.innerHTML = '<option value="" disabled selected>时</option>'
      for (var h = 0; h <= 23; h++) {
        var opt = document.createElement('option')
        opt.value = String(h).padStart(2,'0'); opt.textContent = h + '时'
        hourSel.appendChild(opt)
      }
    }
    var minSel = document.getElementById(prefix + 'Minute')
    if (minSel) {
      minSel.innerHTML = '<option value="" selected disabled>分</option>'
      for (var m = 0; m <= 59; m++) {
        var opt = document.createElement('option')
        opt.value = String(m).padStart(2,'0'); opt.textContent = m + '分'
        minSel.appendChild(opt)
      }
    }
    // 默认当前时间
    yearSel.value = curYear
    if (monthSel) monthSel.value = String(now.getMonth()+1).padStart(2,'0')
    if (hourSel) hourSel.value = String(now.getHours()).padStart(2,'0')
    if (minSel) minSel.value = String(now.getMinutes()).padStart(2,'0')
    // 年月联动 → 填充日select
    var daySel = document.getElementById(prefix + 'Day')
    if (daySel) {
      var y = parseInt(yearSel.value)
      var m = parseInt(monthSel ? monthSel.value : 1)
      var daysInMonth = new Date(y, m, 0).getDate()
      daySel.innerHTML = '<option value="" disabled>日</option>'
      for (var d = 1; d <= daysInMonth; d++) {
        var opt = document.createElement('option')
        opt.value = String(d).padStart(2,'0'); opt.textContent = d + '日'
        daySel.appendChild(opt)
      }
      daySel.value = String(now.getDate()).padStart(2,'0')
    }
    // 年月联动change事件
    if (monthSel) {
      monthSel.addEventListener('change', function() {
        var p = this.id.replace('Month','')
        var ys = document.getElementById(p + 'Year')
        var ds = document.getElementById(p + 'Day')
        if (!ys || !ds) return
        var yy = parseInt(ys.value)
        var mm = parseInt(this.value)
        if (isNaN(yy) || isNaN(mm)) return
        var dim = new Date(yy, mm, 0).getDate()
        var prevDay = ds.value
        ds.innerHTML = '<option value="" disabled>日</option>'
        for (var di = 1; di <= dim; di++) {
          var opt = document.createElement('option')
          opt.value = String(di).padStart(2,'0'); opt.textContent = di + '日'
          ds.appendChild(opt)
        }
        if (prevDay && parseInt(prevDay) <= dim) ds.value = prevDay
      })
    }
  })
  // ── 初始化AI问事类型select ──
  var typeSel = document.getElementById('mai-type')
  if (typeSel) {
    var labels = ['事业财运','姻缘感情','学业考试','健康出行','百事占断','💰 项目能否成功','💕 感情复合时机','💼 面试能否通过','🏠 买房租房吉凶','✈️ 出行安全预判','⚖️ 官司诉讼参考']
    var values = ['career','love','study','health','general','s_project','s_loveback','s_interview','s_house','s_travel','s_lawsuit']
    // optgroup分组的Flask风格
    var g1 = document.createElement('optgroup'); g1.label = '── 基础分类 ──'
    var g2 = document.createElement('optgroup'); g2.label = '── 快速场景 ──'
    for (var i = 0; i < labels.length; i++) {
      var opt = document.createElement('option')
      opt.value = values[i]; opt.textContent = labels[i]
      if (i < 5) g1.appendChild(opt); else g2.appendChild(opt)
    }
    typeSel.appendChild(g1); typeSel.appendChild(g2)
    typeSel.value = 'general'
    // change事件绑定
    typeSel.addEventListener('change', function() {
      var qi = document.getElementById('mai-question')
      if (!qi) return
      var sceneQ = { s_project: '这个项目能否成功？需要注意什么？', s_loveback: '我和对方复合的最佳时机是什么时候？', s_interview: '我的面试能否通过？有什么需要准备的？', s_house: '这套房子风水如何？适合购买或租住吗？', s_travel: '近期出行是否安全？需要注意什么？', s_lawsuit: '这场官司诉讼的走向如何？有什么策略？' }
      if (sceneQ[this.value]) { qi.value = sceneQ[this.value]; qi.focus() }
    })
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
    if (type === 'number') { inp.min = '0'; inp.max = '999' }
    wrap.appendChild(inp)
    return inp
  }
  createNativeInput('mf-num1-wrap', 'number', '如 3')
  createNativeInput('mf-num2-wrap', 'number', '选填')
  createNativeInput('mf-words-wrap', 'text', '如：今天天气很好')
  createNativeInput('mf-question-wrap', 'text', '如：这件事能成吗？')
  createNativeInput('mai-num1-wrap', 'number', '如 3')
  createNativeInput('mai-num2-wrap', 'number', '选填')
  createNativeInput('mai-words-wrap', 'text', '如：今天天气很好')
  createNativeInput('mai-question-wrap', 'text', '如：这件事能不能成？')
})
</script>

<style>
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }
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
.incognito-status { margin-top: 16px; }

/* ═══ 梅花易数排盘结果样式 ═══ */
.mh-result-wrap { animation: mhFadeIn 0.4s ease; }
@keyframes mhFadeIn { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.mh-summary { display: flex; flex-wrap: wrap; gap: 8px 16px; font-size: 0.8125rem; color: var(--text-2); padding: 12px 16px; background: rgba(255,255,255,0.02); border-radius: 10px; border: 1px solid var(--card-border); margin-bottom: 16px; }
.mh-summary b { color: var(--text-1); }
.gua-display { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 16px; margin: 24px 0 20px; }
.gua-card { background: rgba(255,255,255,0.02); border: 1px solid var(--card-border); border-radius: 14px; padding: 20px 16px 16px; text-align: center; position: relative; transition: all 0.3s; }
.gua-card:hover { border-color: var(--card-border-hover); transform: translateY(-2px); box-shadow: var(--card-shadow); }
.gua-card-label { font-size: 0.75rem; color: var(--text-3); letter-spacing: 2px; margin-bottom: 8px; }
.gua-card-name { font-family: var(--font-serif); font-size: 1.375rem; font-weight: 600; color: var(--text-1); letter-spacing: 3px; margin-bottom: 12px; }
.gua-card.ben-gua .gua-card-name { color: var(--accent); }
.gua-card.hu-gua .gua-card-name { color: #7C93C3; }
.gua-card.bian-gua .gua-card-name { color: #E8A87C; }
.gua-yao-wrap { display: flex; flex-direction: column; align-items: center; gap: 6px; margin: 0 auto; width: 120px; max-width: 120px; }
.gua-yao { display: flex; justify-content: center; align-items: center; gap: 6px; height: 8px; width: 100%; position: relative; }
.gua-yao-line { height: 6px; border-radius: 2px; transition: all 0.3s; }
.gua-yao.yang .gua-yao-line { width: 80%; background: var(--text-1); }
.gua-yao.yin .gua-yao-line { width: calc((80% - 6px) / 2); background: var(--text-1); }
.gua-yao.dong-yao .gua-yao-line { background: var(--accent); box-shadow: 0 0 8px rgba(110,195,135,0.5); }
.gua-yao.dong-yao::after { content: '○'; position: absolute; right: -14px; font-size: 0.625rem; color: var(--accent); font-weight: 700; }
.gua-sub-info { margin-top: 12px; font-size: 0.75rem; color: var(--text-3); line-height: 1.8; }
.gua-sub-info span { display: inline-block; padding: 2px 8px; border-radius: 4px; margin: 2px; background: rgba(255,255,255,0.04); }
.gua-trigram { font-size: 2.5rem; line-height: 1; margin-bottom: 4px; opacity: 0.8; }
.ti-yong-section { background: rgba(255,255,255,0.02); border: 1px solid var(--card-border); border-radius: 14px; padding: 20px; margin: 20px 0; }
.ti-yong-title { font-family: var(--font-serif); font-size: 1rem; font-weight: 600; color: var(--text-1); letter-spacing: 2px; margin-bottom: 16px; padding-bottom: 10px; border-bottom: 1px solid var(--card-border); }
.ti-yong-grid { display: grid; grid-template-columns: 1fr auto 1fr; gap: 16px; align-items: center; margin-bottom: 16px; }
.ti-yong-box { text-align: center; padding: 16px 12px; border-radius: 12px; border: 1px solid var(--card-border); }
.ti-yong-box.ti { background: rgba(110,195,135,0.06); border-color: rgba(110,195,135,0.2); }
.ti-yong-box.yong { background: rgba(124,147,195,0.06); border-color: rgba(124,147,195,0.2); }
.ti-yong-label { font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; letter-spacing: 1px; }
.ti-yong-gua { font-family: var(--font-serif); font-size: 1.5rem; font-weight: 600; color: var(--text-1); }
.ti-yong-wx { font-size: 0.8125rem; color: var(--text-2); margin-top: 4px; }
.ti-yong-rel { text-align: center; padding: 8px 16px; font-size: 0.875rem; font-weight: 600; border-radius: 8px; letter-spacing: 2px; white-space: nowrap; }
.ti-yong-rel.ji { background: rgba(110,195,135,0.1); color: var(--success); }
.ti-yong-rel.xiong { background: rgba(215,125,110,0.1); color: var(--danger); }
.ti-yong-rel.zhong { background: rgba(255,255,255,0.05); color: var(--text-2); }
.mh-analysis-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
.mh-analysis-table th { text-align: left; padding: 10px 12px; color: var(--text-3); font-weight: 500; border-bottom: 1px solid var(--card-border); white-space: nowrap; }
.mh-analysis-table td { padding: 10px 12px; color: var(--text-2); border-bottom: 1px solid var(--card-border); }
.mh-analysis-table tr:last-child td { border-bottom: none; }
.wx-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 500; }
.wx-tag.jin { background: rgba(255,215,0,0.12); color: #D4A017; }
.wx-tag.mu { background: rgba(110,195,135,0.12); color: #6EC387; }
.wx-tag.shui { background: rgba(70,130,180,0.12); color: #4682B4; }
.wx-tag.huo { background: rgba(215,125,110,0.12); color: #D77D6E; }
.wx-tag.tu { background: rgba(160,140,100,0.12); color: #A08C64; }
.ws-tag { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: 600; }
.ws-tag.wang { background: rgba(110,195,135,0.12); color: #6EC387; }
.ws-tag.xiang { background: rgba(70,130,180,0.12); color: #4682B4; }
.ws-tag.xiu { background: rgba(255,255,255,0.05); color: var(--text-3); }
.ws-tag.qiu { background: rgba(215,125,110,0.08); color: #D77D6E; }
.ws-tag.si { background: rgba(160,140,100,0.08); color: #A08C64; }
.mh-verdict { margin-top: 16px; padding: 16px 20px; border-radius: 12px; border-left: 3px solid var(--accent); background: rgba(110,195,135,0.04); font-size: 0.9375rem; color: var(--text-2); line-height: 1.8; }
.qf-datetime-row { display: flex; gap: 8px; align-items: center; justify-content: space-between; }
.qf-dt-col { flex: 1; min-width: 0; }
.qf-dt-col-narrow { flex: 0.8; }
.qf-datetime-select { width: 100%; padding: 9px 6px; border: 1.5px solid var(--card-border); border-radius: 8px; font-size: 0.85rem; font-weight: 500; background: var(--card-bg); color: var(--text-1); cursor: pointer; text-align: center; appearance: none; -webkit-appearance: none; -moz-appearance: none; outline: none; box-sizing: border-box; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath d='M5 7L1 3h8z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 4px center; padding-right: 16px; }
.qf-datetime-select:focus { border-color: var(--accent); }
.dom-input-wrap { width: 100%; }
.form-select { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; appearance: auto; -webkit-appearance: auto; -moz-appearance: auto; }
@media (max-width: 600px) { .gua-display { grid-template-columns: 1fr; gap: 12px; } .ti-yong-grid { grid-template-columns: 1fr; gap: 8px; } .qf-datetime-row { flex-wrap: wrap; } .qf-dt-col { flex: 1 1 calc(33% - 8px); min-width: 60px; } }
.method-switch { display: flex; gap: 8px; margin-bottom: 16px; flex-wrap: wrap; }
.method-switch-btn { padding: 8px 16px; border-radius: 10px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.8125rem; cursor: pointer; }
.method-switch-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); font-weight: 600; }
.mh-method-content { margin-bottom: 16px; }
.mh-num-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.mh-result { margin-top: 16px; }
.ly-result-card { background: var(--card-bg); border-radius: 12px; padding: 20px; border: 1px solid var(--card-border); }
.ly-result-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; color: var(--accent); letter-spacing: 2px; }
.qai-deep-row { display: flex; align-items: center; gap: 8px; margin: 8px 0; }
.qai-deep-toggle { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; }
.qai-deep-toggle.active .qai-toggle-track { background: var(--accent); }
.qai-toggle-label { font-size: 0.82rem; color: var(--text-2); }
.qai-toggle-track { width: 40px; height: 22px; background: var(--card-border); border-radius: 11px; position: relative; transition: background 0.3s; }
.qai-toggle-knob { width: 18px; height: 18px; background: #fff; border-radius: 50%; position: absolute; top: 2px; left: 2px; transition: transform 0.3s; }
.qai-deep-toggle.active .qai-toggle-knob { transform: translateX(18px); }
.qai-progress { margin-top: 16px; }
.qai-progress-bar { height: 6px; background: var(--card-border); border-radius: 4px; overflow: hidden; }
.qai-progress-fill { height: 100%; background: linear-gradient(90deg, var(--accent), #e8a84c); border-radius: 4px; transition: width 0.6s ease; }
.qai-step-text { text-align: center; font-size: 0.82rem; color: var(--text-2); margin-top: 8px; }
.qai-result { margin-top: 16px; background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 20px; max-height: 600px; overflow-y: auto; line-height: 1.8; }
.qai-markdown { font-size: 0.88rem; color: var(--text-1); }
.qai-error { text-align: center; padding: 24px; color: var(--danger); }
.result-mode-switch { display: flex; gap: 8px; margin-top: 16px; padding-top: 16px; border-top: 1px solid var(--card-border); }
.result-mode-btn { flex: 1; padding: 8px; border-radius: 8px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.75rem; cursor: pointer; text-align: center; }
.result-mode-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }
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
@media (max-width: 768px) { .tool-hero { padding: 40px 16px 24px; } .tool-hero-title { font-size: 1.5rem; } .tool-container { padding: 20px 16px; } .section { padding: 48px 16px; } .footer-grid { grid-template-columns: 1fr; gap: 24px; } }</style>
