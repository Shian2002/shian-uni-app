<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :is-logged-in="isLoggedIn"
      @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <section class="tool-hero">
        <view class="tool-hero-content">
          <view class="section-tag">六爻纳甲</view>
          <view class="tool-hero-title">六爻纳甲 · 铜钱摇卦</view>
          <view class="tool-hero-desc">自动摇卦 · 手动输入 · 纳甲装卦 · 世应六亲 · 动变推断</view>
        </view>
      </section>

      <section class="section">
        <view class="tool-container">
          <view class="tool-tabs">
            <view class="tool-tab" id="lyTabFree" @tap="switchTab('free')">六爻排盘<text class="tab-badge free">免费</text></view>
            <view v-if="false" class="tool-tab" id="lyTabAi" @tap="switchTab('ai')">时安六爻系统<text class="tab-badge">PRO</text></view>
          </view>

          <!-- 免费排盘 -->
          <view class="tool-tab-content" id="lyTabFreeContent" style="display:block">
            <view class="method-switch">
              <view class="method-switch-btn" id="lyMethodAutoBtn" @tap.stop="switchLyMethod('auto')">自动摇卦</view>
              <view class="method-switch-btn" id="lyMethodManBtn" @tap.stop="switchLyMethod('manual')">手动输入</view>
            </view>

            <view class="ly-method-content" id="lyMethodAuto">
              <view class="ly-auto-info">
                <view class="ly-auto-icon">🪙🪙🪙</view>
                <text>系统将模拟三枚铜钱摇卦，正面（字）= 2，反面（花）= 3。</text>
                <text>三枚之和决定爻之阴阳动静：6=老阴(动)、7=少阳、8=少阴、9=老阳(动)</text>
              </view>
            </view>

            <view class="ly-method-content" id="lyMethodManual" style="display:none;">
              <text class="form-hint" style="margin-bottom:12px;">请输入六次摇卦结果，每次三枚铜钱</text>
              <view class="ly-toss-rows">
                <view class="ly-toss-row" v-for="(toss, idx) in lyTossRows" :key="idx">
                  <text class="ly-toss-label">第{{ idx + 1 }}次</text>
                  <view class="ly-toss-coins">
                    <view class="ly-coin-btn" v-for="(coin, ci) in 3" :key="ci"
                      :id="'lyFC-' + idx + '-' + ci"
                      @tap="toggleFreeCoin(idx, ci)">
                      {{ lyTossRows[idx][ci] === 2 ? '字' : '花' }}
                    </view>
                  </view>
                  <text class="ly-toss-sum" :id="'lyFreeSum' + idx">和: {{ lyTossRows[idx].reduce((a,b) => a+b, 0) }}</text>
                </view>
              </view>
            </view>

            <view class="form-group" style="margin-top:16px;">
              <text class="form-label">你的问题（选填）</text>
              <view id="lfQuestion-wrap" class="dom-input-wrap"></view>
            </view>

            <view class="btn-row">
              <view class="submit-btn" @tap="liuyaoFreePaipan">免费排盘</view>
              <view class="btn btn-ghost" @tap="lfReset">清空</view>
            </view>
            <text class="form-hint" style="text-align:center;display:block;margin-top:12px;">本地精准排盘，纳甲装卦、世应六亲全分析。深度解读请回首页选择六爻或自动选术数。</text>
            <view class="ly-result" id="lyFreeResult"></view>
          </view>

          <!-- AI系统 -->
          <view v-if="false" class="tool-tab-content" id="lyTabAiContent">
            <view class="form-group">
              <text class="form-label">问事类型</text>
              <picker :range="laiTypeLabels" :value="laiTypeIdx" @change="onLaiTypeChange($event)">
                <view class="form-select-picker">{{ laiTypeLabels[laiTypeIdx] }}</view>
              </picker>
            </view>
            <view class="method-switch" style="margin-bottom:16px;">
              <view class="method-switch-btn" id="laiMethodAutoBtn" @tap.stop="switchLaiMethod('auto')">自动摇卦</view>
              <view class="method-switch-btn" id="laiMethodManBtn" @tap.stop="switchLaiMethod('manual')">手动输入</view>
            </view>
            <!-- 自动摇卦区 -->
            <view id="laiMethodAuto">
              <view class="ly-auto-info">
                <view class="ly-auto-icon">🪙🪙🪙</view>
                <text>系统将模拟三枚铜钱摇卦，正面（字）= 2，反面（花）= 3。</text>
                <text>三枚之和决定爻之阴阳动静：6=老阴(动)、7=少阳、8=少阴、9=老阳(动)</text>
              </view>
            </view>
            <!-- 手动输入区 -->
            <view id="laiMethodManual" style="display:none;">
              <view class="mh-method-content">
                <view class="ly-toss-rows">
                  <view class="ly-toss-row" v-for="(toss, idx) in laiTossRows" :key="'ai'+idx">
                    <text class="ly-toss-label">第{{ idx + 1 }}次</text>
                    <view class="ly-toss-coins">
                      <view class="ly-coin-btn" v-for="(coin, ci) in 3" :key="ci"
                        :id="'lyAC-' + idx + '-' + ci"
                        @tap="toggleAiCoin(idx, ci)">
                        {{ laiTossRows[idx][ci] === 2 ? '字' : '花' }}
                      </view>
                    </view>
                    <text class="ly-toss-sum" :id="'lyAiSum' + idx">和: {{ laiTossRows[idx].reduce((a,b) => a+b, 0) }}</text>
                  </view>
                </view>
              </view>
            </view>
            <view class="form-group">
              <text class="form-label">你的问题（选填）</text>
              <view id="laiQuestion-wrap" class="dom-input-wrap"></view>
            </view>
            <view class="qai-deep-row">
              <label class="qai-deep-toggle" id="lyDeepToggle" @tap="toggleLyDeepMode()">
                <text class="qai-toggle-label">深度分析</text>
                <view class="qai-toggle-track"><view class="qai-toggle-knob"></view></view>
              </label>
            </view>
            <view class="btn-row">
              <view class="submit-btn" @tap="liuyaoAskPaipan">一键起卦 · 深度解读</view>
              <view class="btn btn-ghost" @tap="laiReset">清空</view>
            </view>
            <!-- 排盘结果 -->
            <view class="ly-result" id="lyAiResult" style="display:none;"></view>
            <!-- 流式解读区域 -->
            <view class="qai-stream-box" id="lyStreamBox" style="display:none;">
              <view class="chat-container" id="lyChatContainer"></view>
            </view>
            <!-- 追问输入栏 -->
            <view class="chat-input-bar" id="lyChatInputBar" style="display:none;">
              <input class="chat-input" id="lyChatInput" placeholder="继续追问..." />
              <view class="chat-send-btn" onclick="window.lySendFollowUp()">发送</view>
            </view>
          </view>
        </view>
      </section>
    </view>

    <!-- 铜钱动画遮罩 -->
    <view class="ly-coin-overlay" id="lyCoinOverlay">
      <view class="ly-coin-center">
        <view class="ly-coin-spinner" id="lyCoinSpinner">
          <view class="ly-coin-face ly-coin-front">字</view>
          <view class="ly-coin-face ly-coin-back">花</view>
        </view>
        <view class="ly-coin-progress" id="lyCoinProgress">第 1/6 次摇卦...</view>
      </view>
    </view>



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

const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })
const activeTab = ref('free')

// ═══ Tab/Method切换: DOM直操作 (绕过Vue 3.4.21 render effect bug) ═══
function switchTab(tab) {
  activeTab.value = tab
  var free = document.getElementById('lyTabFreeContent')
  var ai = document.getElementById('lyTabAiContent')
  var btnFree = document.getElementById('lyTabFree')
  var btnAi = document.getElementById('lyTabAi')
  if (free) free.style.display = tab === 'free' ? 'block' : 'none'
  if (ai) ai.style.display = tab === 'ai' ? 'block' : 'none'
  if (btnFree) { tab === 'free' ? btnFree.classList.add('active') : btnFree.classList.remove('active') }
  if (btnAi) { tab === 'ai' ? btnAi.classList.add('active') : btnAi.classList.remove('active') }
}

function switchLyMethod(m) {
  lyMethod.value = m
  // 免费版方法切换 (v-if替代: DOM直操作)
  if (m === 'auto') {
    var autoEl = document.getElementById('lyMethodAuto')
    var manEl = document.getElementById('lyMethodManual')
    if (autoEl) autoEl.style.display = 'block'
    if (manEl) manEl.style.display = 'none'
  } else {
    var autoEl = document.getElementById('lyMethodAuto')
    var manEl = document.getElementById('lyMethodManual')
    if (autoEl) autoEl.style.display = 'none'
    if (manEl) manEl.style.display = 'block'
  }
  // 更新按钮active class
  var autoBtn = document.getElementById('lyMethodAutoBtn')
  var manBtn = document.getElementById('lyMethodManBtn')
  if (autoBtn) { m === 'auto' ? autoBtn.classList.add('active') : autoBtn.classList.remove('active') }
  if (manBtn) { m === 'manual' ? manBtn.classList.add('active') : manBtn.classList.remove('active') }
}

function switchLaiMethod(m) {
  laiMethod.value = m
  // AI版方法切换
  if (m === 'auto') {
    var autoEl = document.getElementById('laiMethodAuto')
    var manEl = document.getElementById('laiMethodManual')
    if (autoEl) autoEl.style.display = 'block'
    if (manEl) manEl.style.display = 'none'
  } else {
    var autoEl = document.getElementById('laiMethodAuto')
    var manEl = document.getElementById('laiMethodManual')
    if (autoEl) autoEl.style.display = 'none'
    if (manEl) manEl.style.display = 'block'
  }
  var autoBtn = document.getElementById('laiMethodAutoBtn')
  var manBtn = document.getElementById('laiMethodManBtn')
  if (autoBtn) { m === 'auto' ? autoBtn.classList.add('active') : autoBtn.classList.remove('active') }
  if (manBtn) { m === 'manual' ? manBtn.classList.add('active') : manBtn.classList.remove('active') }
}

// 六爻免费排盘
const lyMethod = ref('auto')
const lyTossRows = reactive(Array.from({ length: 6 }, () => [3, 3, 3]))
const lfQuestion = ref('')
function lfReset() {
  lyMethod.value = 'auto'
  var lfInp = document.getElementById('lfQuestion')
  if (lfInp) lfInp.value = ''
  const resultEl = document.getElementById('lyFreeResult')
  if (resultEl) resultEl.innerHTML = ''
  for (let i = 0; i < 6; i++) { lyTossRows[i] = [3, 3, 3] }
  // 重置方法显示
  switchLyMethod('auto')
}

// ═══ 铜钱动画（1:1复刻Flask liuyao.js） ═══
async function showLyCoinAnimation() {
  return new Promise(function(resolve) {
    const overlay = document.getElementById('lyCoinOverlay')
    const spinner = document.getElementById('lyCoinSpinner')
    const progress = document.getElementById('lyCoinProgress')
    if (!overlay || !spinner || !progress) { resolve(); return }
    overlay.classList.add('active')
    let count = 0
    const interval = setInterval(function() {
      count++
      spinner.classList.remove('spinning')
      void spinner.offsetWidth
      spinner.classList.add('spinning')
      progress.textContent = '第 ' + count + '/6 次摇卦...'
      if (count >= 6) {
        clearInterval(interval)
        setTimeout(function() {
          overlay.classList.remove('active')
          resolve()
        }, 700)
      }
    }, 500)
  })
}

async function liuyaoFreePaipan() {
  let tossData = null
  if (lyMethod.value === 'manual') {
    tossData = lyTossRows.map(row => [...row])
  }

  // 铜钱动画
  await showLyCoinAnimation()

  const resultEl = document.getElementById('lyFreeResult')
  if (!resultEl) return
  resultEl.innerHTML = '<div style="text-align:center;padding:24px;color:var(--text-3);">🧭 排盘计算中...</div>'

  try {
    const question = (document.getElementById('lfQuestion') || {}).value || ''
    const res = await uni.request({ url: '/api/liuyao/paipan', method: 'POST', data: { mode: lyMethod.value, tosses: tossData, question } })
    const data = res.data
    if (data.error) { resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">${data.error}</div>`; return }
    const panData = data.data || data
    _unscopeStyles()
    resultEl.innerHTML = renderLiuyaoResult(panData)
  } catch (e) { resultEl.innerHTML = `<div style="color:var(--danger);padding:16px;">排盘失败</div>` }
}

// ═══ 六爻纳甲渲染函数 (1:1移植自Flask liuyao.js) ═══
function renderLyYaoLine(detail) {
  const lineGraphic = detail.is_yang
    ? '<div class="ly-yang-bar"></div>'
    : '<div class="ly-yin-bars"><div class="ly-yin-seg"></div><div class="ly-yin-seg"></div></div>'
  const tags = []
  tags.push(`<span class="ly-tag ly-tag-liuqin">${detail.liuqin}</span>`)
  tags.push(`<span class="ly-tag ly-tag-liushen">${detail.liushen}</span>`)
  tags.push(`<span class="ly-tag ly-tag-naja">${detail.naja}</span>`)
  // 世/应/动/变在左边横排显示，不在info中重复
  const leftTags = []
  if (detail.is_shi) leftTags.push(`<span class="ly-tag ly-tag-shi">世</span>`)
  if (detail.is_ying) leftTags.push(`<span class="ly-tag ly-tag-ying">应</span>`)
  if (detail.is_moving) leftTags.push(`<span class="ly-tag ly-tag-moving">动</span>`)
  if (detail.yao_type === '变') leftTags.push(`<span class="ly-tag ly-tag-bian">变</span>`)
  const leftTagsHtml = `<div class="ly-yao-left-tags${leftTags.length ? '' : ' ly-empty'}">${leftTags.join('')}</div>`
  const lineExtraClass = detail.is_moving ? 'moving' : (detail.yao_type === '变' ? 'bian' : '')
  return `<div class="ly-yao-line ${lineExtraClass}">
    <div class="ly-yao-left-col">
      ${leftTagsHtml}
      <div class="ly-yao-pos">${detail.name}</div>
    </div>
    <div class="ly-yao-graphic">${lineGraphic}</div>
    <div class="ly-yao-info">${tags.join('')}</div>
  </div>`
}

function renderLiuyaoResult(d) {
  const isManual = d.method && d.method.includes('手动')
  let html = '<div class="ly-result-wrap">'
  const hasMoving = d.details && d.details.some(x => x.is_moving)
  const movingCount = d.details ? d.details.filter(x => x.is_moving).length : 0

  // ── 单盒子：合并卦名 + 三才 + 爻线 + 元信息 ──
  html += '<div class="ly-ben-bian-box">'
  // 顶部：卦名 + 三才
  html += '<div class="ly-ben-bian-top">'
  html += `<div class="ly-ben-bian-name-block">
    <div class="ly-ben-bian-label">本 卦</div>
    <div class="ly-ben-bian-name-text">${d['本卦'] || ''}</div>
    <div class="ly-ben-bian-trigrams">
      <span class="ly-trigram-badge">${d.upper_nature || ''} ${d.upper_trigram || ''}</span>
      <span class="ly-trigram-badge">${d.lower_nature || ''} ${d.lower_trigram || ''}</span>
    </div>
  </div>`
  if (hasMoving) {
    html += '<div class="ly-ben-bian-top-arrow">→</div>'
    html += `<div class="ly-ben-bian-name-block">
      <div class="ly-ben-bian-label">变 卦</div>
      <div class="ly-ben-bian-name-text">${d['变卦'] || ''}</div>
      <div class="ly-ben-bian-trigrams">
        <span class="ly-trigram-badge">${d.bian_upper_nature || ''} ${d.bian_upper_trigram || ''}</span>
        <span class="ly-trigram-badge">${d.bian_lower_nature || ''} ${d.bian_lower_trigram || ''}</span>
      </div>
    </div>`
  }
  html += '</div>' // end ly-ben-bian-top

  // 中部：配对行（每行左右并排本卦 + 变卦）
  html += '<div class="ly-ben-bian-body">'
  if (d.details) {
    for (let i = d.details.length - 1; i >= 0; i--) {
      const ben = d.details[i]
      const bian = hasMoving && d.bian_details ? d.bian_details[i] : null
      const showBian = !!bian // 只要有变卦数据就显示
      const benMoving = ben.is_moving ? 'moving' : ''
      const bianChanged = (bian && bian.yao_type === '变') ? 'bian' : ''
      html += `<div class="ly-paired-row ${benMoving} ${bianChanged}${showBian ? ' has-bian' : ' has-ben-only'}">`
      // 列1：本卦区（世应动 + 阴阳条 + 信息）
      html += '<div class="ly-row-ben-side">'
      // 世应动标记在左边
      html += '<div class="ly-yao-tags-left">'
      if (ben.is_shi) html += '<span class="ly-tag ly-tag-shi">世</span>'
      if (ben.is_ying) html += '<span class="ly-tag ly-tag-ying">应</span>'
      if (ben.is_moving) html += '<span class="ly-tag ly-tag-moving">动</span>'
      html += '</div>'
      // 阴阳条
      html += '<div class="ly-paired-ben">'
      html += ben.is_yang
        ? '<div class="ly-yang-bar"></div>'
        : '<div class="ly-yin-bars"><div class="ly-yin-seg"></div><div class="ly-yin-seg"></div></div>'
      html += '</div>'
      // 信息区（爻位 + 六亲 + 六神 + 纳甲）
      html += '<div class="ly-paired-info">'
      html += `<span class="ly-yao-pos">${ben.name}</span>`
      html += `<span class="ly-tag ly-tag-liuqin">${ben.liuqin}</span>`
      html += `<span class="ly-tag ly-tag-liushen">${ben.liushen}</span>`
      html += `<span class="ly-tag ly-tag-naja">${ben.naja}</span>`
      html += '</div>'
      html += '</div>'
      // 列2：分隔
      if (showBian) {
        html += '<div class="ly-row-divider"></div>'
      }
      // 列3：变卦区（变标记 + 阴阳条 + 信息）
      if (showBian) {
        html += '<div class="ly-row-bian-side">'
        // 变标记在左边
        html += '<div class="ly-yao-tags-left">'
        if (bian.yao_type === '变') html += '<span class="ly-tag ly-tag-bian">变</span>'
        html += '</div>'
        // 阴阳条
        html += '<div class="ly-paired-bian">'
        html += bian.is_yang
          ? '<div class="ly-yang-bar"></div>'
          : '<div class="ly-yin-bars"><div class="ly-yin-seg"></div><div class="ly-yin-seg"></div></div>'
        html += '</div>'
        // 信息区（六亲 + 六神 + 纳甲）
        html += '<div class="ly-paired-bian-info">'
        html += `<span class="ly-tag ly-tag-liuqin">${bian.liuqin}</span>`
        html += `<span class="ly-tag ly-tag-liushen">${bian.liushen}</span>`
        html += `<span class="ly-tag ly-tag-naja">${bian.naja}</span>`
        html += '</div>'
        html += '</div>'
      }
      html += '</div>' // end ly-paired-row
    }
  }
  html += '</div>' // end ly-ben-bian-body

  // 底部：元信息
  html += '<div class="ly-ben-bian-footer">'
  html += `<span class="ly-ben-bian-meta">宫：${d.palace_name || ''}宫（${d.palace_element || ''}）</span>`
  html += `<span class="ly-ben-bian-meta">日辰：${d.day_ganzhi || ''}</span>`
  html += `<span class="ly-ben-bian-meta">月建：${d.month_ganzhi || ''}</span>`
  if (hasMoving) {
    html += `<span class="ly-ben-bian-meta" style="color:var(--danger)">动爻：${movingCount}个</span>`
  } else {
    html += `<span class="ly-ben-bian-meta">静卦（无动爻）</span>`
  }
  html += '</div></div>' // end ly-ben-bian-footer + ly-ben-bian-box

  // 明细表格
  html += '<div style="overflow-x:auto;">'
  html += '<table class="ly-detail-table">'
  html += '<tr><th>爻位</th><th>阴阳</th><th>六亲</th><th>六神</th><th>纳甲</th><th>地支五行</th><th>世应</th><th>动</th></tr>'
  if (d.details) {
    for (let i = d.details.length - 1; i >= 0; i--) {
      const x = d.details[i]
      html += `<tr class="${x.is_moving ? 'moving-row' : ''}">
        <td>${x.name}</td>
        <td>${x.is_yang ? '⚊ 阳' : '⚋ 阴'}</td>
        <td>${x.liuqin}</td>
        <td>${x.liushen}</td>
        <td>${x.naja}</td>
        <td>${x.dizhi_element}</td>
        <td>${x.is_shi ? '世' : x.is_ying ? '应' : ''}</td>
        <td>${x.is_moving ? '⚡ 动' : ''}</td>
      </tr>`
    }
  }
  html += '</table></div>'

  html += '<div class="ly-paipan-meta">'
  html += `<span>🕐 ${new Date().toLocaleString('zh-CN')}</span>`
  html += `<span>📖 ${d.method || '自动摇卦'}</span>`
  if (d.question) html += `<span>❓ ${d.question}</span>`
  html += '</div>'
  html += '<div style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>'
  html += '</div>'
  return html
}

// 六爻AI
const laiTypeLabels = ['事业财运', '姻缘感情', '学业考试', '健康出行', '百事占断', '💰 项目能否成功', '💕 感情复合时机', '💼 面试能否通过', '🤝 合作是否靠谱', '🔍 失物能否找回', '⚖️ 官司诉讼参考']
const laiTypeValues = ['career', 'love', 'study', 'health', 'general', 's_project', 's_loveback', 's_interview', 's_coop', 's_lost', 's_lawsuit']
const laiTypeIdx = ref(0)
const laiMethod = ref('auto')
const laiTossRows = reactive(Array.from({ length: 6 }, () => [3, 3, 3]))
const laiQuestion = ref('')
const deepMode = ref(false)
const resultMode = ref('simple')
const laiLoading = ref(false)
const laiProgress = ref(0)
const laiStepText = ref('')
const laiResult = ref('')

function laiReset() {
  laiMethod.value = 'auto'; laiResult.value = ''; laiTypeIdx.value = 0
  deepMode.value = false; resultMode.value = 'simple'
  // 隐藏排盘结果和流式盒子
  var r = document.getElementById('lyAiResult')
  if (r) { r.style.display = 'none'; r.innerHTML = '' }
  var b = document.getElementById('lyStreamBox')
  if (b) b.style.display = 'none'
  var laiInp = document.getElementById('laiQuestion')
  if (laiInp) laiInp.value = ''
  var deepEl = document.getElementById('lyDeepToggle')
  if (deepEl) deepEl.classList.remove('active')
  var simpleEl = document.getElementById('lyResultSimple')
  var proEl = document.getElementById('lyResultPro')
  if (simpleEl) simpleEl.classList.add('active')
  if (proEl) proEl.classList.remove('active')
  for (let i = 0; i < 6; i++) { laiTossRows[i] = [3, 3, 3] }
  switchLaiMethod('auto')
}

const LAI_SCENE_QUESTIONS = { s_project: '这个项目能否成功？需要注意什么？', s_loveback: '我和对方复合的最佳时机是什么时候？', s_interview: '我的面试能否通过？有什么需要准备的？', s_coop: '这个合作是否靠谱？值得投入吗？', s_lost: '失物还能找回吗？在什么方向？', s_lawsuit: '这场官司诉讼的走向如何？有什么策略？' }

function onLaiTypeChange(e) {
  laiTypeIdx.value = e.detail.value
  const val = laiTypeValues[laiTypeIdx.value]
  if (LAI_SCENE_QUESTIONS[val]) {
    var qi = document.getElementById('laiQuestion')
    if (qi) { qi.value = LAI_SCENE_QUESTIONS[val]; qi.focus() }
  }
}

// ═══ 六爻 SSE 流式解读 + 追问 ═══
window._lyChatHistory = []

async function liuyaoAskPaipan() {
  if (laiLoading.value) return
  laiLoading.value = true
  laiResult.value = ''
  window._lyChatHistory = []

  // 铜钱摇卦动画
  if (laiMethod.value === 'auto') { await showLyCoinAnimation() }

  // 直接显示盒子（绕过 Vue 3.4.21 v-show 渲染时序问题）
  var box = document.getElementById('lyStreamBox')
  if (box) box.style.display = ''
  var resultEl = document.getElementById('lyAiResult')
  if (resultEl) { resultEl.style.display = 'none'; resultEl.innerHTML = '' }

  var chatContainer = document.getElementById('lyChatContainer')
  if (chatContainer) chatContainer.innerHTML = ''
  var inputBar = document.getElementById('lyChatInputBar')
  if (inputBar) inputBar.style.display = 'none'

  // 创建 AI 气泡
  var bubbleId = 'lyBubble_' + Date.now()
  var bubbleHTML = '<div class="chat-bubble-ai" id="' + bubbleId + '">' +
    '<div class="ai-stage">🔗 正在连接 DeepSeek AI 引擎...</div>' +
    '<div class="ai-progress-bar"><div class="ai-progress-fill" style="width:20%"></div></div>' +
    '<div class="chat-bubble-content"></div></div>'
  if (chatContainer) chatContainer.innerHTML = bubbleHTML
  _lyScrollToChat()

  // 构建参数
  var tossData = null
  if (laiMethod.value === 'manual') { tossData = laiTossRows.map(function(row) { return [...row] }) }
  var type = laiTypeValues[laiTypeIdx.value] || 'general'
  var question = ((document.getElementById('laiQuestion') || {}).value || '').trim()

  _lyDoStreamSSE({
    bubbleId: bubbleId,
    url: '/api/liuyao/ask/stream',
    body: { mode: laiMethod.value, tosses: tossData, question: question, deep_analysis: deepMode.value },
    question: question,
    onDone: function(fullText) {
      window._lyChatHistory = [
        { role: 'user', content: question },
        { role: 'assistant', content: fullText }
      ]
      laiResult.value = fullText
      _saveLyConversation(question)
      var bar = document.getElementById('lyChatInputBar')
      if (bar) bar.style.display = 'flex'
      _lyScrollToChat()
    },
    onError: function() {
      laiLoading.value = false
    }
  })
}

function _lyDoStreamSSE(opts) {
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
        if (contentEl) contentEl.innerHTML = _lyRenderCards(fullText)
        if (opts.onDone) opts.onDone(fullText)
        laiLoading.value = false
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
        if (r.done) { doneReceived = true; return }
        buffer += decoder.decode(r.value, { stream: true })
        var lines = buffer.split('\n')
        buffer = lines.pop() // 最后一行可能不完整，保留到下次
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
              doneReceived = true
            } else if (eventType === 'error') {
              if (stageEl) stageEl.innerHTML = '⚠️ ' + data.message
              if (opts.onError) opts.onError()
            } else if (eventType === 'paipan') {
              var r = document.getElementById('lyAiResult')
              if (r) { r.style.display = ''; r.innerHTML = renderLiuyaoResult(data) }
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

function _lyRenderCards(text) {
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

function _stripMarkdown(s) {
  if (!s) return ''
  return s.replace(/^#{1,6}\s*/gm, '').replace(/\*\*/g, '').replace(/^[-*]\s+/gm, '')
}

// ═══ 追问 ═══
function lySendFollowUp() {
  try {
    var input = document.querySelector('#lyChatInput input') || document.getElementById('lyChatInput')
    if (!input) { console.warn('[liuyao] lyChatInput not found'); return }
    var question = input.value.trim()
    if (!question) return
    input.value = ''

    var chatContainer = document.getElementById('lyChatContainer')
    if (!chatContainer) return

    var userBubble = document.createElement('view')
    userBubble.className = 'chat-bubble-user'
    userBubble.textContent = question
    chatContainer.appendChild(userBubble)

    var bubbleId = 'lyFollow_' + Date.now()
    var aiBubble = document.createElement('view')
    aiBubble.className = 'chat-bubble-ai'
    aiBubble.id = bubbleId
    aiBubble.innerHTML = '<div class="ai-stage"><img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成回复...</div>' +
      '<div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div>' +
      '<div class="chat-bubble-content"></div>'
    chatContainer.appendChild(aiBubble)
    _lyScrollToChat()

    var history = window._lyChatHistory || []
    history.push({ role: 'user', content: question })

    // 发送时立即保存
    if (_lyCurrentConvId) {
      window._lyChatHistory = history
      _updateLyConversation()
    } else {
      window._lyChatHistory = history
      _saveLyConversation(question)
    }

    _lyDoStreamSSE({
      bubbleId: bubbleId,
      url: '/api/liuyao/ask/stream',
      body: { question: question, history: history },
      question: question,
      onDone: function(fullText) {
        history.push({ role: 'assistant', content: fullText })
        window._lyChatHistory = history
        if (_lyCurrentConvId) { _updateLyConversation() } else { _saveLyConversation(question) }
      },
      onError: function() {
        var eb = document.getElementById(bubbleId)
        if (eb) { var es = eb.querySelector('.ai-stage'); if (es) es.innerHTML = '⚠️ 追问失败，请重试' }
      }
    })
  } catch (err) { console.error('[liuyao] lySendFollowUp error:', err) }
}
window.lySendFollowUp = lySendFollowUp

// ═══ 六爻手动输入切换（DOM直操作绕过Vue 3.4.21嵌套数组render bug） ═══
function _afterRender(fn) {
  requestAnimationFrame(function() { requestAnimationFrame(fn) })
}
// 滚动到追问输入框（显示对话内容+继续追问区域）
function _lyScrollToChat() {
  setTimeout(function() {
    var el = document.getElementById('lyChatInputBar')
    if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, 100)
}
function toggleFreeCoin(idx, ci) {
  lyTossRows[idx][ci] = lyTossRows[idx][ci] === 2 ? 3 : 2
  var newVal = lyTossRows[idx][ci]
  var coinId = 'lyFC-' + idx + '-' + ci
  var sumId = 'lyFreeSum' + idx
  // 直接DOM操作（不依赖_afterRender，避免时机问题）
  var el = document.getElementById(coinId)
  if (el) {
    if (newVal === 2) { el.classList.add('heads') } else { el.classList.remove('heads') }
    el.textContent = newVal === 2 ? '字' : '花'
  }
  var sumEl = document.getElementById(sumId)
  if (sumEl) sumEl.textContent = '和: ' + lyTossRows[idx].reduce(function(a, b) { return a + b }, 0)
}
function toggleAiCoin(idx, ci) {
  laiTossRows[idx][ci] = laiTossRows[idx][ci] === 2 ? 3 : 2
  var newVal = laiTossRows[idx][ci]
  var coinId = 'lyAC-' + idx + '-' + ci
  var sumId = 'lyAiSum' + idx
  var el = document.getElementById(coinId)
  if (el) {
    if (newVal === 2) { el.classList.add('heads') } else { el.classList.remove('heads') }
    el.textContent = newVal === 2 ? '字' : '花'
  }
  var sumEl = document.getElementById(sumId)
  if (sumEl) sumEl.textContent = '和: ' + laiTossRows[idx].reduce(function(a, b) { return a + b }, 0)
}

// ═══ DOM直操作辅助函数（绕过Vue 3.4.21 render effect bug） ═══
function toggleLyDeepMode() {
  deepMode.value = !deepMode.value
  var el = document.getElementById('lyDeepToggle')
  if (el) { deepMode.value ? el.classList.add('active') : el.classList.remove('active') }
}

function switchLyResultMode(m) {
  resultMode.value = m
  var simple = document.getElementById('lyResultSimple')
  var pro = document.getElementById('lyResultPro')
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

// ═══ 注入全局样式（合并所有stylesheet，绕开uni-app强制scope） ═══
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
  // 刷新注入（移除旧的再创建，确保样式最新）
  const old = document.getElementById('ly-unscoped')
  if (old) old.remove()
  const style = document.createElement('style')
  style.id = 'ly-unscoped'
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
  // 确保表单内容在页面切换回时可见（防御：uni-app tab切换可能重置DOM状态）
  var tabFree = document.getElementById('lyTabFreeContent')
  var tabAi = document.getElementById('lyTabAiContent')
  if (activeTab.value === 'free') {
    if (tabFree) tabFree.style.display = 'block'
    if (tabAi) tabAi.style.display = 'none'
  } else {
    if (tabFree) tabFree.style.display = 'none'
    if (tabAi) tabAi.style.display = 'block'
  }
  // 每次页面显示时检查是否有需要恢复的对话数据
  try { _checkLyRestore() } catch(_) {}
})

onMounted(() => {
  _unscopeStyles()
  // 创建原生DOM输入框
  createNativeInput('lfQuestion-wrap', 'text', '如：这件事能成吗？')
  createNativeInput('laiQuestion-wrap', 'text', '如：这件事能不能成？')
  // 初始化DOM状态
  var tabFree = document.getElementById('lyTabFreeContent')
  var tabAi = document.getElementById('lyTabAiContent')
  if (tabFree) tabFree.style.display = 'block'
  if (tabAi) tabAi.style.display = 'none'
  var lyMan = document.getElementById('lyMethodManual')
  if (lyMan) lyMan.style.display = 'none'
  var laiMan = document.getElementById('laiMethodManual')
  if (laiMan) laiMan.style.display = 'none'
  var lyTabFreeBtn = document.getElementById('lyTabFree')
  if (lyTabFreeBtn) lyTabFreeBtn.classList.add('active')
  var lyAutoBtn = document.getElementById('lyMethodAutoBtn')
  if (lyAutoBtn) lyAutoBtn.classList.add('active')
  var laiAutoBtn = document.getElementById('laiMethodAutoBtn')
  if (laiAutoBtn) laiAutoBtn.classList.add('active')
  var simpleBtn = document.getElementById('lyResultSimple')
  if (simpleBtn) simpleBtn.classList.add('active')
  for (var i = 0; i < 6; i++) {
    for (var j = 0; j < 3; j++) {
      var coinEl = document.getElementById('lyFC-' + i + '-' + j)
      if (coinEl) coinEl.textContent = '花'
      var aiCoinEl = document.getElementById('lyAC-' + i + '-' + j)
      if (aiCoinEl) aiCoinEl.textContent = '花'
    }
  }
  // 监听对话恢复事件
  uni.$on('xc-restore', _checkLyRestore)
  _checkLyRestore()
  // 导出全局恢复函数，供 TopNav 直接调用
  window._xc_restoreLiuyao = _checkLyRestore
  // 轮询检查恢复数据（持续运行，不限次数）
  setInterval(function() {
    var rd = window.__xc_restoreData
    if (rd && rd.type === 'liuyao') _checkLyRestore()
  }, 500)
})

function _checkLyRestore() {
  var d = window.__xc_restoreData
  if (!d || d.type !== 'liuyao') return
  switchTab('ai')
  var chatContainer = document.getElementById('lyChatContainer')
  var inputBar = document.getElementById('lyChatInputBar')
  var streamBox = document.getElementById('lyStreamBox')
  if (streamBox) streamBox.style.display = ''
  if (!chatContainer) return
  window.__xc_restoreData = null
  chatContainer.innerHTML = ''
  if (d.rawHtml) {
    // 旧记录格式
    if (d.question) {
      var ub = document.createElement('view')
      ub.className = 'chat-bubble-user'
      ub.textContent = d.question
      chatContainer.appendChild(ub)
    }
    var cleanHtml = _stripMarkdown(d.rawHtml.replace(/<[^>]+>/g, '')).replace(/\n/g, '<br>')
    var ab = document.createElement('view')
    ab.className = 'chat-bubble-ai'
    ab.innerHTML = '<div class="chat-bubble-content">' + cleanHtml + '</div>'
    chatContainer.appendChild(ab)
    window._lyChatHistory = [
      { role: 'user', content: d.question || '' },
      { role: 'assistant', content: cleanHtml.replace(/<[^>]+>/g, '').substring(0, 200) + '...' }
    ]
    _lyCurrentConvId = null
  } else {
    // 新记录格式：按messages渲染
    var messages = d.messages || []
    window._lyChatHistory = messages.slice()
    _lyCurrentConvId = d.id || null
    messages.forEach(function(m) {
      if (m.role === 'user') {
        var ub = document.createElement('view')
        ub.className = 'chat-bubble-user'
        ub.textContent = m.content
        chatContainer.appendChild(ub)
      } else if (m.role === 'assistant') {
        var ab = document.createElement('view')
        ab.className = 'chat-bubble-ai'
        ab.innerHTML = '<div class="chat-bubble-content">' + _stripMarkdown(m.content).replace(/\n/g, '<br>') + '</div>'
        chatContainer.appendChild(ab)
      }
    })
  }
  if (inputBar) inputBar.style.display = 'flex'
  _lyScrollToChat()
}
// ═══ 六爻对话保存 ═══
var _lyCurrentConvId = null

function _saveLyConversation(question) {
  var title = (question || '六爻占卜').substring(0, 50)
  var typeSelect = document.getElementById('lai-type')
  var sceneType = typeSelect ? typeSelect.value : ''
  uni.request({
    url: '/api/liuyao/conversations', method: 'POST',
    data: {
      title: title, scene_type: sceneType,
      question: question,
      messages: window._lyChatHistory || []
    },
    success: function(res) {
      if (res.data && res.data.id) _lyCurrentConvId = res.data.id
      window.__sidebarCache = null
    },
    fail: function(err) { console.error('[liuyao] 保存对话失败:', err) }
  })
}

function _updateLyConversation() {
  if (!_lyCurrentConvId) return
  uni.request({
    url: '/api/liuyao/conversations', method: 'POST',
    data: { id: _lyCurrentConvId, messages: window._lyChatHistory || [] },
    success: function() { window.__sidebarCache = null },
    fail: function(err) { console.error('[liuyao] 更新对话失败:', err) }
  })
}
</script>

<style>
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --bg-2: rgba(40,45,68,0.80); --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --text-4: rgba(160,150,135,0.78); --border: rgba(255,255,255,0.12); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --bg-2: rgba(245,240,230,0.80); --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --text-4: rgba(90,78,58,0.68); --border: rgba(0,0,0,0.045); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }
.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }

/* 工具页 */
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.section-tag { display: inline-block; padding: 4px 14px; border-radius: 20px; font-size: 0.6875rem; letter-spacing: 2px; color: var(--accent); background: var(--accent-glow); margin-bottom: 12px; }
.tool-hero { padding: 60px 32px 32px; text-align: center; position: relative; overflow: hidden; }
.tool-hero-content { position: relative; z-index: 1; max-width: var(--max-w); margin: 0 auto; }
.tool-hero-title { font-family: var(--font-serif); font-size: 2rem; font-weight: 400; letter-spacing: 4px; color: var(--text-1); margin-bottom: 12px; }
.tool-hero-desc { font-size: 0.9375rem; color: var(--text-3); letter-spacing: 2px; }
.tool-container { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; backdrop-filter: blur(20px); box-shadow: var(--card-shadow); max-width: 960px; margin: 0 auto; box-sizing: border-box; }
.tool-tabs { display: flex; gap: 4px; margin-bottom: 28px; border-bottom: 1px solid var(--card-border); }
.tool-tab { padding: 12px 20px; border-radius: 10px 10px 0 0; font-size: 0.875rem; cursor: pointer; border: 1px solid transparent; border-bottom: none; color: var(--text-3); background: transparent; }
.tool-tab.active { color: var(--accent); background: var(--accent-glow); border-color: var(--accent); font-weight: 600; }
.tab-badge { font-size: 0.5625rem; padding: 1px 5px; border-radius: 4px; background: var(--accent); color: #fff; margin-left: 4px; }
.tab-badge.free { background: var(--success); }
#lyTabAiContent { display: none; }

/* 表单 */
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 6px; letter-spacing: 1px; }
.form-input, .form-select-picker { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.form-hint { font-size: 0.6875rem; color: var(--text-3); }
.submit-btn { width: 100%; padding: 14px; border-radius: 30px; border: none; background: hsl(35, 38%, 52%); color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; letter-spacing: 2px; margin-top: 8px; text-align: center; }
.btn-row { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 16px; }
.btn-row .submit-btn { margin-top: 0; }
.btn-row .btn-ghost { margin-top: 0; }
.btn-ghost { background: transparent; border: 1px solid var(--card-border); color: var(--text-3); padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; }

/* 起卦方式切换 */
.method-switch { display: flex; gap: 8px; margin-bottom: 16px; }
.method-switch-btn { padding: 8px 16px; border-radius: 10px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.8125rem; cursor: pointer; }
.method-switch-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); font-weight: 600; }

/* 六爻手动输入 */
.ly-auto-info { text-align: center; padding: 16px; }
.ly-auto-icon { font-size: 2rem; margin-bottom: 8px; }
.ly-toss-rows { display: flex; flex-direction: column; gap: 8px; }
.ly-toss-row { display: flex; align-items: center; gap: 8px; padding: 8px 12px; border-radius: 8px; background: var(--section-alt); border: 1px solid var(--card-border); }
.ly-toss-label { font-size: 0.75rem; color: var(--text-3); min-width: 48px; }
.ly-toss-coins { display: flex; gap: 6px; }
.ly-coin-btn { padding: 6px 12px; border-radius: 8px; border: 1px solid var(--card-border); background: var(--card-bg); color: var(--text-2); font-size: 0.75rem; cursor: pointer; }
.ly-coin-btn.heads { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }
.ly-toss-sum { font-size: 0.75rem; color: var(--accent); margin-left: auto; font-weight: 600; }
.ly-result { margin-top: 16px; display: none; width: 100%; }
.ly-result:empty { display: none; }
.ly-result:not(:empty) { display: flex; justify-content: center; }
.ly-result-card { background: var(--card-bg); border-radius: 12px; padding: 20px; border: 1px solid var(--card-border); }

/* ═══ 六爻纳甲排盘结果样式 ═══ */
.ly-result-wrap { margin: 24px auto 0; width: min(100%, 860px); }
.ly-trigram-badge { padding: 4px 12px; background: var(--accent-glow); border: 1px solid var(--border); border-radius: 8px; font-size: 0.8125rem; color: var(--accent); }
.ly-ben-bian-box { background: var(--bg-2); border: 1px solid var(--border); border-radius: 12px; padding: 14px; margin-bottom: 20px; }
.ly-ben-bian-top { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 8px; padding-bottom: 12px; margin-bottom: 10px; border-bottom: 1px solid var(--border); }
.ly-ben-bian-name-block { text-align: center; }
.ly-ben-bian-name-block:first-child:nth-last-child(1) { grid-column: 1 / -1; }
.ly-ben-bian-label { font-size: 0.75rem; color: var(--text-3); letter-spacing: 2px; margin-bottom: 4px; }
.ly-ben-bian-name-text { font-size: 1.75rem; font-weight: 700; color: var(--accent); letter-spacing: 4px; font-family: var(--font-serif), serif; }
.ly-ben-bian-trigrams { display: flex; align-items: center; justify-content: center; gap: 8px; margin: 6px 0 0; }
.ly-ben-bian-top-arrow { font-size: 1.5rem; color: var(--danger); animation: lyPulse 2s ease-in-out infinite; }
@keyframes lyPulse { 0%, 100% { opacity: 0.4; } 50% { opacity: 1; } }
.ly-ben-bian-body { display: flex; flex-direction: column; gap: 2px; }
.ly-paired-row { display: grid; grid-template-columns: 1fr auto 1fr; align-items: center; gap: 8px; padding: 3px 0; border-radius: 6px; min-height: 28px; transition: background 0.2s; }
.ly-paired-row:hover { background: rgba(212,168,71,0.04); }
.ly-paired-row.moving { background: rgba(231,76,60,0.04); }
.ly-paired-row.bian { background: rgba(155,89,182,0.04); }
.ly-paired-ben, .ly-paired-bian { width: 40px; height: 10px; display: flex; align-items: center; flex-shrink: 0; }
.ly-paired-info { flex: 1; display: flex; align-items: center; gap: 2px; flex-wrap: nowrap; min-width: 0; }
.ly-paired-bian-info { flex: 1; display: flex; align-items: center; gap: 2px; flex-wrap: nowrap; min-width: 0; }
.ly-row-ben-side, .ly-row-bian-side { display: flex; align-items: center; gap: 4px; min-width: 0; }
.ly-yao-tags-left { display: flex; align-items: center; gap: 2px; flex-shrink: 0; width: 44px; }
.ly-row-bian-side .ly-yao-tags-left { width: 24px; }
.ly-row-bian-side { padding-left: 20px; }
.ly-row-divider { width: 24px; display: flex; align-items: center; justify-content: center; align-self: stretch; }
.ly-row-divider::after { content: ''; width: 1px; align-self: stretch; background: var(--border); min-height: 16px; }
/* 静卦：只有本卦区，跨全行居中 */
.ly-paired-row.has-ben-only .ly-row-ben-side { grid-column: 1 / -1; justify-self: center; }

.ly-ben-bian-footer { display: flex; align-items: center; justify-content: center; gap: 14px; flex-wrap: wrap; padding-top: 10px; margin-top: 10px; border-top: 1px solid var(--border); font-size: 0.8125rem; color: var(--text-3); }
.ly-ben-bian-meta { color: var(--text-3); }
.ly-yao-line { display: flex; align-items: center; gap: 6px; min-height: 30px; padding: 3px 8px; border-radius: 6px; transition: background 0.2s; }
.ly-yao-line:hover { background: rgba(212,168,71,0.04); }
.ly-yao-pos { width: 28px; font-size: 0.6875rem; color: var(--text-4); text-align: center; flex-shrink: 0; }
.ly-yao-left-col { display: flex; align-items: center; gap: 3px; flex-shrink: 0; }
.ly-yao-left-tags { display: flex; align-items: center; gap: 2px; min-width: 66px; }
.ly-yao-left-tags.ly-empty { min-width: 66px; }
.ly-yao-graphic { width: 64px; height: 10px; display: flex; align-items: center; justify-content: center; gap: 3px; flex-shrink: 0; }
.ly-yang-bar { width: 100%; height: 5px; background: var(--accent); border-radius: 3px; }
.ly-yin-bars { width: 100%; display: flex; gap: 10px; }
.ly-yin-seg { flex: 1; height: 5px; background: var(--text-4); border-radius: 3px; }
@keyframes lyLineGlow { 0%, 100% { opacity: 1; } 50% { opacity: 0.4; } }
.ly-paired-row.moving .ly-yang-bar, .ly-paired-row.moving .ly-yin-seg { background: var(--danger); animation: lyLineGlow 1.5s ease-in-out infinite; }
.ly-paired-row.bian .ly-yang-bar, .ly-paired-row.bian .ly-yin-seg { background: #9b59b6; }

.ly-tag { padding: 1px 5px; border-radius: 3px; font-size: 0.625rem; font-weight: 500; letter-spacing: 0.5px; white-space: nowrap; }
.ly-tag-liuqin { background: var(--accent-glow); color: var(--accent); }
.ly-tag-liushen { background: rgba(41,128,185,0.12); color: #3498db; }
.ly-tag-naja { background: rgba(39,174,96,0.12); color: #27ae60; }
.ly-tag-shi { background: rgba(243,156,18,0.15); color: #f39c12; font-weight: 700; }
.ly-tag-ying { background: rgba(52,152,219,0.15); color: #3498db; font-weight: 700; }
.ly-tag-moving { background: rgba(231,76,60,0.12); color: var(--danger); }
.ly-tag-bian { background: rgba(155,89,182,0.15); color: #9b59b6; font-weight: 700; }
.ly-yao-line.bian { background: rgba(155,89,182,0.04); border-radius: 6px; }
.ly-yao-line.bian .ly-yang-bar, .ly-yao-line.bian .ly-yin-seg { background: #9b59b6; }
.ly-detail-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; margin-bottom: 16px; }
.ly-detail-table th { padding: 10px 6px; text-align: center; color: var(--text-3); font-weight: 500; border-bottom: 1px solid var(--border); font-size: 0.75rem; letter-spacing: 1px; }
.ly-detail-table td { padding: 10px 6px; text-align: center; border-bottom: 1px solid rgba(212,168,71,0.06); color: var(--text-2); }
.ly-detail-table tr:hover td { background: rgba(212,168,71,0.03); }
.ly-detail-table .moving-row td { color: var(--danger); }
.ly-paipan-meta { display: flex; align-items: center; justify-content: center; gap: 14px; padding: 14px; background: var(--bg-2); border-radius: 10px; margin-top: 16px; font-size: 0.8125rem; color: var(--text-3); flex-wrap: wrap; }
.ly-paipan-meta span { display: flex; align-items: center; gap: 4px; }
@media (max-width: 480px) { .ly-ben-bian-name-text { font-size: 1.25rem; letter-spacing: 2px; } .ly-ben-bian-footer { flex-direction: column; gap: 6px; } .ly-paired-row { gap: 8px; padding: 3px 0; } .ly-paired-ben, .ly-paired-bian { width: 30px; } .ly-paired-info { gap: 1px; } .ly-yao-pos { width: 22px; font-size: 0.55rem; } .ly-tag { font-size: 0.45rem; padding: 1px 2px; border-radius: 2px; } .ly-yao-tags-left { width: 34px; } .ly-row-bian-side .ly-yao-tags-left { width: 20px; } .ly-row-bian-side { padding-left: 14px; } .ly-ben-bian-box { padding: 10px; } .ly-detail-table { font-size: 0.625rem; } .ly-detail-table th, .ly-detail-table td { padding: 6px 2px; } }

/* AI进度条/结果/开关 */
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
.mh-method-content { margin-bottom: 16px; }

/* 页脚 */
/* ── 铜钱动画遮罩 ── */
.ly-coin-overlay { position: fixed; inset: 0; z-index: 9999; display: none; align-items: center; justify-content: center; background: rgba(0,0,0,0.7); backdrop-filter: blur(10px); }
.ly-coin-overlay.active { display: flex; }
.ly-coin-center { text-align: center; }
.ly-coin-spinner { width: 100px; height: 100px; position: relative; perspective: 600px; margin: 0 auto 32px; }
.ly-coin-face { position: absolute; inset: 0; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 28px; font-weight: 700; backface-visibility: hidden; border: 3px solid var(--accent); }
.ly-coin-front { background: linear-gradient(135deg, #f0d078, #d4a847, #a07828); color: #0a0a0f; }
.ly-coin-back { background: linear-gradient(135deg, #c0392b, #e74c3c, #a93226); color: #fff; transform: rotateY(180deg); }
.ly-coin-spinner.spinning .ly-coin-face { animation: lyCoinSpin 0.7s ease-in-out; }
@keyframes lyCoinSpin { 0% { transform: rotateY(0deg); } 50% { transform: rotateY(900deg) scale(1.1); } 100% { transform: rotateY(1800deg); } }
.ly-coin-progress { color: var(--accent); font-size: 1rem; letter-spacing: 2px; }

/* 弹窗 */
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

@media (max-width: 768px) {
  .tool-hero { padding: 40px 16px 24px; }
  .tool-hero-title { font-size: 1.5rem; }
  .tool-container { padding: 20px 16px; }
  .section { padding: 48px 16px; }

}
@media (max-width: 480px) {
  .tool-hero { padding: 24px 16px 16px !important; }
  .tool-hero-title { font-size: 1.25rem !important; margin-bottom: 6px !important; }
  .tool-hero-desc { font-size: 0.75rem !important; }
  .section { padding: 20px 16px !important; }
  .tool-container { padding: 16px !important; }
  .incognito-bar { padding: 8px 12px !important; margin-bottom: 12px !important; gap: 4px !important; }
  .tool-tabs { margin-bottom: 14px !important; }
  .tool-tab { font-size: 0.78rem; padding: 8px 10px; }
  .tab-badge { font-size: 0.5rem; padding: 1px 5px; }
  .method-switch { gap: 6px; }
  .method-switch-btn { font-size: 0.78rem; padding: 8px 10px; }
  .btn-row { grid-template-columns: 1fr; gap: 8px; }
  .submit-btn { font-size: 0.875rem; padding: 12px 16px; }
  .result-mode-btn { font-size: 0.72rem; padding: 6px 12px; }
  .ly-toss-row { gap: 6px; }
  .ly-toss-label { font-size: 0.72rem; }
  .ly-coin-btn { width: 38px; height: 38px; font-size: 0.75rem; }
}
/* 超窄屏（375px以下）六爻结果进一步紧凑 */
@media (max-width: 420px) {
  .ly-ben-bian-name-text { font-size: 1rem; letter-spacing: 1px; }
  .ly-ben-bian-box { padding: 6px; }
  .ly-paired-row { padding: 2px 0; gap: 6px; min-height: 20px; } .ly-row-divider { width: 16px; } .ly-paired-ben, .ly-paired-bian { width: 26px; }
  .ly-paired-info { gap: 1px; }
  .ly-yao-pos { width: 16px; font-size: 0.45rem; }
  .ly-yao-tags-left { width: 28px; }
  .ly-row-bian-side .ly-yao-tags-left { width: 16px; }
  .ly-tag { font-size: 0.38rem; padding: 0 2px; border-radius: 2px; letter-spacing: 0; }
  .ly-ben-bian-top { padding: 8px 4px; gap: 6px; }
  .ly-ben-bian-footer { font-size: 0.65rem; gap: 3px; }
  .ly-ben-bian-label { font-size: 0.6rem; }
  .ly-ben-bian-top-arrow { font-size: 1rem; }
  .ly-trigram-badge { font-size: 0.65rem; padding: 2px 6px; }
  .ly-ben-bian-body { gap: 1px; }
}

/* ═══ 流式解读 + 对话气泡 ═══ */
.qai-stream-box {
  margin-top: 20px; padding: 16px;
  background: var(--card-bg); border: 1px solid var(--card-border);
  border-radius: 14px;
}
.qai-card-item {
  background: var(--section-alt); border: 1px solid var(--card-border);
  border-radius: 10px; padding: 14px 16px; margin-bottom: 10px;
}
.qai-card-title { font-size: 0.9rem; font-weight: 700; color: var(--accent); margin-bottom: 6px; }
.qai-card-body { font-size: 0.82rem; color: var(--text-2); line-height: 1.7; }
.qai-card-body strong { color: var(--text-1); }
.chat-container { display: flex; flex-direction: column; gap: 12px; }
.chat-bubble-ai {
  align-self: flex-start;
  background: var(--section-alt); border: 1px solid var(--card-border);
  border-radius: 14px 14px 14px 4px;
  padding: 16px 20px; max-width: 92%; width: 100%; box-sizing: border-box;
}
.chat-bubble-user {
  align-self: flex-end;
  background: var(--accent); color: #fff;
  border-radius: 14px 14px 4px 14px;
  padding: 10px 16px; max-width: 80%;
  font-size: 0.9rem; line-height: 1.5;
}
.chat-bubble-content { font-size: 0.875rem; color: var(--text-2); line-height: 1.9; }
.ai-stage { font-size: 0.9rem; color: var(--text-1); margin-bottom: 8px; display: flex; align-items: center; gap: 8px; }
.ai-progress-bar { height: 4px; background: var(--card-border); border-radius: 2px; overflow: hidden; margin-bottom: 16px; }
.ai-progress-fill {
  height: 100%; width: 20%;
  background: linear-gradient(90deg, var(--accent), #8b5cf6);
  border-radius: 2px; animation: ai-progress-pulse 1.5s ease-in-out infinite; transition: width 0.3s ease;
}
@keyframes ai-progress-pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
.chat-input-bar {
  display: flex; gap: 8px; margin-top: 16px;
  padding: 10px 14px; background: var(--section-alt);
  border-radius: 12px; border: 1px solid var(--card-border);
}
.chat-input {
  flex: 1; padding: 8px 14px; border-radius: 8px;
  border: 1px solid var(--card-border);
  background: var(--input-bg); color: var(--text-1);
  font-size: 0.875rem; outline: none;
}
.chat-send-btn {
  padding: 8px 20px; background: var(--accent); color: #fff;
  border-radius: 8px; font-size: 0.875rem; cursor: pointer; white-space: nowrap;
}
</style>
