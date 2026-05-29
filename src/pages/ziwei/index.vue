<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>
    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />
    <view class="page-wrap">
      <section class="tool-hero">
        <view class="tool-hero-content">
          <view class="section-tag">紫微斗数</view>
          <view class="tool-hero-title">紫微斗数 · 十二宫排盘</view>
          <view class="tool-hero-desc">出生时间排盘 · 十二宫星曜 · 四化飞星 · 大限流年推运</view>
        </view>
      </section>
      <section class="section">
        <view class="tool-container">
          <!-- Tab 切换 -->
          <view class="tool-tabs">
            <view class="tool-tab" :class="{ active: activeTab === 'pan' }" @click="switchTab('pan')">⭐ 排盘<text class="tab-badge free">免费</text></view>
            <view class="tool-tab" :class="{ active: activeTab === 'ai' }" @click="switchTab('ai')">🤖 AI解读</view>
            <view class="tool-tab" :class="{ active: activeTab === 'horoscope' }" @click="switchTab('horoscope')">📅 推运<text class="tab-badge">PRO</text></view>
          </view>
          <!-- 排盘面板 -->
          <view class="tool-tab-content" v-show="activeTab === 'pan'">
            <view class="zw-form-grid">
              <view class="form-group zw-birth-time-group">
                <text class="form-label">出生时间</text>
                <view class="zw-birth-row">
                  <view class="zw-birth-col zw-birth-col-year">
                    <picker :range="birthYearOptions" :value="birthYearIndex(zwForm)" @change="setBirthPart(zwForm, 'year', $event)">
                      <view class="zw-birth-select">{{ zwForm.year }}年</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col">
                    <picker :range="birthMonthOptions" :value="birthMonthIndex(zwForm)" @change="setBirthPart(zwForm, 'month', $event)">
                      <view class="zw-birth-select">{{ zwForm.month }}月</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col">
                    <picker :range="birthDayOptions(zwForm)" :value="birthDayIndex(zwForm)" @change="setBirthPart(zwForm, 'day', $event)">
                      <view class="zw-birth-select">{{ zwForm.day }}日</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col">
                    <picker :range="birthHourOptions" :value="birthHourIndex(zwForm)" @change="setBirthPart(zwForm, 'hour', $event)">
                      <view class="zw-birth-select">{{ pad2(zwForm.hour) }}时</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col zw-birth-col-minute">
                    <picker :range="birthMinuteOptions" :value="birthMinuteIndex(zwForm)" @change="setBirthPart(zwForm, 'minute', $event)">
                      <view class="zw-birth-select">{{ pad2(zwForm.minute) }}分</view>
                    </picker>
                  </view>
                </view>
              </view>
              <view class="form-group">
                <text class="form-label">性别</text>
                <picker :range="['男', '女']" :value="zwForm.genderIdx" @change="zwForm.genderIdx = $event.detail.value">
                  <view class="form-select-picker">{{ ['男', '女'][zwForm.genderIdx] }}</view>
                </picker>
              </view>
              <view class="form-group">
                <text class="form-label">历法类型</text>
                <picker :range="['阳历(公历)', '农历(阴历)']" :value="zwForm.dateTypeIdx" @change="zwForm.dateTypeIdx = $event.detail.value">
                  <view class="form-select-picker">{{ ['阳历(公历)', '农历(阴历)'][zwForm.dateTypeIdx] }}</view>
                </picker>
              </view>
            </view>
            <view class="submit-btn" @click="ziweiFreePan">⭐ 免费排盘</view>
            <text class="form-hint" style="text-align:center;display:block;margin-top:12px;">基于iztro-py精确排盘，十二宫、主星辅星、四化飞星全展示。</text>
            <view class="zw-result" v-if="zwPanResult" v-html="zwPanResult"></view>
          </view>
          <!-- AI解读面板 -->
          <view class="tool-tab-content" v-show="activeTab === 'ai'">
            <view class="zw-form-grid">
              <view class="form-group zw-birth-time-group">
                <text class="form-label">出生时间</text>
                <view class="zw-birth-row">
                  <view class="zw-birth-col zw-birth-col-year">
                    <picker :range="birthYearOptions" :value="birthYearIndex(zwAiForm)" @change="setBirthPart(zwAiForm, 'year', $event)">
                      <view class="zw-birth-select">{{ zwAiForm.year }}年</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col">
                    <picker :range="birthMonthOptions" :value="birthMonthIndex(zwAiForm)" @change="setBirthPart(zwAiForm, 'month', $event)">
                      <view class="zw-birth-select">{{ zwAiForm.month }}月</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col">
                    <picker :range="birthDayOptions(zwAiForm)" :value="birthDayIndex(zwAiForm)" @change="setBirthPart(zwAiForm, 'day', $event)">
                      <view class="zw-birth-select">{{ zwAiForm.day }}日</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col">
                    <picker :range="birthHourOptions" :value="birthHourIndex(zwAiForm)" @change="setBirthPart(zwAiForm, 'hour', $event)">
                      <view class="zw-birth-select">{{ pad2(zwAiForm.hour) }}时</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col zw-birth-col-minute">
                    <picker :range="birthMinuteOptions" :value="birthMinuteIndex(zwAiForm)" @change="setBirthPart(zwAiForm, 'minute', $event)">
                      <view class="zw-birth-select">{{ pad2(zwAiForm.minute) }}分</view>
                    </picker>
                  </view>
                </view>
              </view>
              <view class="form-group">
                <text class="form-label">性别</text>
                <picker :range="['男', '女']" :value="zwAiForm.genderIdx" @change="zwAiForm.genderIdx = $event.detail.value">
                  <view class="form-select-picker">{{ ['男', '女'][zwAiForm.genderIdx] }}</view>
                </picker>
              </view>
              <view class="form-group">
                <text class="form-label">历法类型</text>
                <picker :range="['阳历(公历)', '农历(阴历)']" :value="zwAiForm.dateTypeIdx" @change="zwAiForm.dateTypeIdx = $event.detail.value">
                  <view class="form-select-picker">{{ ['阳历(公历)', '农历(阴历)'][zwAiForm.dateTypeIdx] }}</view>
                </picker>
              </view>
            </view>
            <view class="form-group">
              <text class="form-label">分析类型</text>
              <view class="analysis-type-row">
                <view v-for="(t, idx) in zwAnalysisTypes" :key="idx" 
                  class="analysis-type-btn" 
                  :class="{ active: zwAiForm.analysisTypeIdx === idx }"
                  @click="zwAiForm.analysisTypeIdx = idx">{{ t.label }}</view>
              </view>
            </view>
            <view class="form-group">
              <text class="form-label">您的问题（可选）</text>
              <input type="text" class="form-input" v-model="zwAiForm.question" placeholder="请输入您想问的问题">
            </view>
            <view class="submit-btn" @click="zwAiAsk">🤖 AI解读</view>
            <view class="qai-stream-box" v-if="zwAiResult" style="display:block;">
              <view class="chat-container" v-html="zwAiResult"></view>
              <view class="chat-input-bar" v-if="zwAiChatReady" style="display:flex;">
                <input type="text" class="chat-input" v-model="zwAiFollowUpQuestion" placeholder="继续提问...">
                <view class="chat-send-btn" @click="zwSendFollowUp">发送</view>
              </view>
            </view>
          </view>
          <!-- 推运面板 -->
          <view class="tool-tab-content" v-show="activeTab === 'horoscope'">
            <view class="zw-form-grid">
              <view class="form-group zw-birth-time-group">
                <text class="form-label">出生时间</text>
                <view class="zw-birth-row">
                  <view class="zw-birth-col zw-birth-col-year">
                    <picker :range="birthYearOptions" :value="birthYearIndex(zwHoroForm)" @change="setBirthPart(zwHoroForm, 'year', $event)">
                      <view class="zw-birth-select">{{ zwHoroForm.year }}年</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col">
                    <picker :range="birthMonthOptions" :value="birthMonthIndex(zwHoroForm)" @change="setBirthPart(zwHoroForm, 'month', $event)">
                      <view class="zw-birth-select">{{ zwHoroForm.month }}月</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col">
                    <picker :range="birthDayOptions(zwHoroForm)" :value="birthDayIndex(zwHoroForm)" @change="setBirthPart(zwHoroForm, 'day', $event)">
                      <view class="zw-birth-select">{{ zwHoroForm.day }}日</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col">
                    <picker :range="birthHourOptions" :value="birthHourIndex(zwHoroForm)" @change="setBirthPart(zwHoroForm, 'hour', $event)">
                      <view class="zw-birth-select">{{ pad2(zwHoroForm.hour) }}时</view>
                    </picker>
                  </view>
                  <view class="zw-birth-col zw-birth-col-minute">
                    <picker :range="birthMinuteOptions" :value="birthMinuteIndex(zwHoroForm)" @change="setBirthPart(zwHoroForm, 'minute', $event)">
                      <view class="zw-birth-select">{{ pad2(zwHoroForm.minute) }}分</view>
                    </picker>
                  </view>
                </view>
              </view>
              <view class="form-group">
                <text class="form-label">性别</text>
                <picker :range="['男', '女']" :value="zwHoroForm.genderIdx" @change="zwHoroForm.genderIdx = $event.detail.value">
                  <view class="form-select-picker">{{ ['男', '女'][zwHoroForm.genderIdx] }}</view>
                </picker>
              </view>
              <view class="form-group">
                <text class="form-label">历法类型</text>
                <picker :range="['阳历(公历)', '农历(阴历)']" :value="zwHoroForm.dateTypeIdx" @change="zwHoroForm.dateTypeIdx = $event.detail.value">
                  <view class="form-select-picker">{{ ['阳历(公历)', '农历(阴历)'][zwHoroForm.dateTypeIdx] }}</view>
                </picker>
              </view>
            </view>
            <view class="form-group" style="margin-top:12px;">
              <text class="form-label">🕐 推运日期</text>
              <view class="qf-datetime-row">
                <view class="qf-dt-col">
                  <picker :range="zwYearOptions" :value="zwTargetYearIdx" @change="onTargetYearChange">
                    <view class="qf-datetime-select">{{ zwTargetYearDisplay || '年' }}</view>
                  </picker>
                </view>
                <view class="qf-dt-col">
                  <picker :range="zwMonthOptions" :value="zwTargetMonthIdx" @change="onTargetMonthChange">
                    <view class="qf-datetime-select">{{ zwTargetMonthDisplay || '月' }}</view>
                  </picker>
                </view>
                <view class="qf-dt-col">
                  <picker :range="zwDayOptions" :value="zwTargetDayIdx" @change="onTargetDayChange">
                    <view class="qf-datetime-select">{{ zwTargetDayDisplay || '日' }}</view>
                  </picker>
                </view>
                <view class="qf-dt-col">
                  <picker :range="zwHourOptions" :value="zwTargetHourIdx" @change="onTargetHourChange">
                    <view class="qf-datetime-select">{{ zwTargetHourDisplay || '时' }}</view>
                  </picker>
                </view>
                <view class="qf-dt-col qf-dt-col-narrow">
                  <picker :range="zwMinuteOptions" :value="zwTargetMinuteIdx" @change="onTargetMinuteChange">
                    <view class="qf-datetime-select">{{ zwTargetMinuteDisplay || '分' }}</view>
                  </picker>
                </view>
              </view>
            </view>
            <view class="submit-btn" @click="ziweiHoroscope">📅 推运排盘</view>
            <view class="zw-result" v-if="zwHoroscopeResult" v-html="zwHoroscopeResult"></view>
          </view>
        </view>
      </section>
    </view>
  </view>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
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

const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

const activeTab = ref('pan')

// Tab切换函数
function switchTab(tabName) {
  activeTab.value = tabName
}

const zwForm = reactive({
  year: 2000, month: 8, day: 16, hour: 12, minute: 0,
  genderIdx: 0, dateTypeIdx: 0
})

// AI解读表单
const zwAiForm = reactive({
  year: 2000, month: 8, day: 16, hour: 12, minute: 0,
  genderIdx: 0, dateTypeIdx: 0,
  analysisTypeIdx: 0, question: ''
})

const zwAnalysisTypes = [
  { key: 'overview', label: '整体概览' },
  { key: 'career', label: '事业财运' },
  { key: 'love', label: '感情姻缘' },
  { key: 'health', label: '健康运势' },
  { key: 'decadal', label: '大限流年' }
]

// 推运表单
const zwHoroForm = reactive({
  year: 2000, month: 8, day: 16, hour: 12, minute: 0,
  genderIdx: 0, dateTypeIdx: 0
})

const birthYearOptions = ref([])
const birthMonthOptions = Array.from({ length: 12 }, (_, i) => (i + 1) + '月')
const birthHourOptions = Array.from({ length: 24 }, (_, i) => pad2(i) + '时')
const birthMinuteOptions = Array.from({ length: 60 }, (_, i) => pad2(i) + '分')

function pad2(v) {
  return String(parseInt(v) || 0).padStart(2, '0')
}

function clampNumber(v, min, max) {
  const n = parseInt(v)
  if (isNaN(n)) return min
  return Math.min(max, Math.max(min, n))
}

function daysInBirthMonth(form) {
  const y = clampNumber(form.year, 1920, new Date().getFullYear() + 3)
  const m = clampNumber(form.month, 1, 12)
  return new Date(y, m, 0).getDate()
}

function birthDayOptions(form) {
  return Array.from({ length: daysInBirthMonth(form) }, (_, i) => (i + 1) + '日')
}

function birthYearIndex(form) {
  return Math.max(0, birthYearOptions.value.indexOf((parseInt(form.year) || 2000) + '年'))
}

function birthMonthIndex(form) {
  return clampNumber(form.month, 1, 12) - 1
}

function birthDayIndex(form) {
  return clampNumber(form.day, 1, daysInBirthMonth(form)) - 1
}

function birthHourIndex(form) {
  return clampNumber(form.hour, 0, 23)
}

function birthMinuteIndex(form) {
  return clampNumber(form.minute, 0, 59)
}

function setBirthPart(form, part, e) {
  const idx = parseInt(e.detail.value) || 0
  if (part === 'year') form.year = parseInt(birthYearOptions.value[idx]) || form.year
  if (part === 'month') form.month = idx + 1
  if (part === 'day') form.day = idx + 1
  if (part === 'hour') form.hour = idx
  if (part === 'minute') form.minute = idx
  if (part === 'year' || part === 'month') {
    form.day = clampNumber(form.day, 1, daysInBirthMonth(form))
  }
}

// 推运日期选择器相关
const zwTargetYearIdx = ref(0)
const zwTargetMonthIdx = ref(0)
const zwTargetDayIdx = ref(0)
const zwTargetHourIdx = ref(0)
const zwTargetMinuteIdx = ref(0)

const zwYearOptions = ref([])
const zwMonthOptions = ref([])
const zwDayOptions = ref([])
const zwHourOptions = ref([])
const zwMinuteOptions = ref([])

const zwTargetYearDisplay = computed(() => zwYearOptions.value[zwTargetYearIdx.value] || '')
const zwTargetMonthDisplay = computed(() => zwMonthOptions.value[zwTargetMonthIdx.value] || '')
const zwTargetDayDisplay = computed(() => zwDayOptions.value[zwTargetDayIdx.value] || '')
const zwTargetHourDisplay = computed(() => zwHourOptions.value[zwTargetHourIdx.value] || '')
const zwTargetMinuteDisplay = computed(() => zwMinuteOptions.value[zwTargetMinuteIdx.value] || '')

// 初始化日期选择器
function initDatePickers() {
  const now = new Date()
  const curYear = now.getFullYear()
  
  birthYearOptions.value = []
  for (let y = curYear + 3; y >= 1920; y--) birthYearOptions.value.push(y + '年')
  
  zwYearOptions.value = []
  for (let y = curYear + 3; y >= 1920; y--) zwYearOptions.value.push(y + '年')
  zwTargetYearIdx.value = zwYearOptions.value.indexOf(curYear + '年')
  
  zwMonthOptions.value = []
  for (let m = 1; m <= 12; m++) zwMonthOptions.value.push(m + '月')
  zwTargetMonthIdx.value = now.getMonth()
  
  updateDayOptions()
  
  zwHourOptions.value = []
  for (let h = 0; h <= 23; h++) zwHourOptions.value.push(h + '时')
  zwTargetHourIdx.value = now.getHours()
  
  zwMinuteOptions.value = []
  for (let m = 0; m <= 59; m++) zwMinuteOptions.value.push(m + '分')
  zwTargetMinuteIdx.value = now.getMinutes()
}

function updateDayOptions() {
  const now = new Date()
  const yearText = zwYearOptions.value[zwTargetYearIdx.value]
  const monthText = zwMonthOptions.value[zwTargetMonthIdx.value]
  let y = now.getFullYear()
  let m = now.getMonth() + 1
  
  if (yearText) y = parseInt(yearText)
  if (monthText) m = parseInt(monthText)
  
  const daysInMonth = new Date(y, m, 0).getDate()
  
  zwDayOptions.value = []
  for (let d = 1; d <= daysInMonth; d++) zwDayOptions.value.push(d + '日')
  
  if (zwTargetDayIdx.value >= zwDayOptions.value.length) {
    zwTargetDayIdx.value = Math.min(zwTargetDayIdx.value, zwDayOptions.value.length - 1)
  }
}

function onTargetYearChange(e) { zwTargetYearIdx.value = e.detail.value; updateDayOptions() }
function onTargetMonthChange(e) { zwTargetMonthIdx.value = e.detail.value; updateDayOptions() }
function onTargetDayChange(e) { zwTargetDayIdx.value = e.detail.value }
function onTargetHourChange(e) { zwTargetHourIdx.value = e.detail.value }
function onTargetMinuteChange(e) { zwTargetMinuteIdx.value = e.detail.value }

const zwPanResult = ref('')
const zwHoroscopeResult = ref('')

async function ziweiFreePan() {
  try {
    const y = parseInt(zwForm.year)
    const m = parseInt(zwForm.month)
    const d = parseInt(zwForm.day)
    const h = parseInt(zwForm.hour)
    const min = parseInt(zwForm.minute) || 0
    
    if (isNaN(y) || isNaN(m) || isNaN(d) || isNaN(h)) {
      zwPanResult.value = '<div style="color:var(--danger);padding:16px;">请填写完整的出生时间</div>'
      return
    }
    
    const res = await uni.request({
      url: '/api/ziwei/pan',
      method: 'POST',
      data: {
        year: y, month: m, day: d, hour: h, minute: min,
        gender: ['男', '女'][zwForm.genderIdx],
        date_type: ['solar', 'lunar'][zwForm.dateTypeIdx]
      }
    })
    
    const data = res.data
    if (data.error || (data.code && data.code !== 0)) {
      zwPanResult.value = '<div style="color:var(--danger);padding:16px;">' + (data.error || data.msg || '排盘失败') + '</div>'
      return
    }
    
    const panData = data.data || data
    zwPanResult.value = renderZiweiPan(panData)
  } catch (e) {
    const errMsg = (e && e.errMsg) || (e && e.message) || (e && String(e)) || '未知错误'
    zwPanResult.value = '<div style="color:var(--danger);padding:16px;">排盘失败: ' + errMsg + '</div>'
  }
}

async function ziweiHoroscope() {
  try {
    const y = parseInt(zwHoroForm.year)
    const m = parseInt(zwHoroForm.month)
    const d = parseInt(zwHoroForm.day)
    const h = parseInt(zwHoroForm.hour)
    const mi = parseInt(zwHoroForm.minute)
    
    if (isNaN(y) || isNaN(m) || isNaN(d) || isNaN(h) || isNaN(mi)) {
      zwHoroscopeResult.value = '<div style="color:var(--danger);padding:16px;">请填写完整的出生时间</div>'
      return
    }
    
    const ty = zwYearOptions.value[zwTargetYearIdx.value]
    const tm = zwMonthOptions.value[zwTargetMonthIdx.value]
    const td = zwDayOptions.value[zwTargetDayIdx.value]
    if (!ty || !tm || !td) {
      zwHoroscopeResult.value = '<div style="color:var(--danger);padding:16px;">请选择推运日期</div>'
      return
    }
    
    const targetYear = parseInt(ty)
    const targetMonth = String(parseInt(tm)).padStart(2, '0')
    const targetDay = String(parseInt(td)).padStart(2, '0')
    const targetDate = targetYear + '-' + targetMonth + '-' + targetDay
    
    const res = await uni.request({
      url: '/api/ziwei/horoscope',
      method: 'POST',
      data: {
        year: y, month: m, day: d, hour: h, minute: mi,
        gender: ['男', '女'][zwHoroForm.genderIdx],
        date_type: ['solar', 'lunar'][zwHoroForm.dateTypeIdx],
        target_date: targetDate
      }
    })
    
    const data = res.data
    if (data.error || (data.code && data.code !== 0)) {
      zwHoroscopeResult.value = '<div style="color:var(--danger);padding:16px;">' + (data.error || data.msg || '推运失败') + '</div>'
      return
    }
    
    const horoData = data.data || data
    zwHoroscopeResult.value = renderZiweiHoroscopeWithPan(horoData)
  } catch (e) {
    zwHoroscopeResult.value = '<div style="color:var(--danger);padding:16px;">推运失败</div>'
  }
}

// AI解读相关
const zwAiResult = ref('')
const zwAiLoading = ref(false)
const zwAiChatReady = ref(false)
const zwAiFollowUpQuestion = ref('')
window._zwChatHistory = []

async function zwAiAsk() {
  if (zwAiLoading.value) return
  
  const y = parseInt(zwAiForm.year)
  const m = parseInt(zwAiForm.month)
  const d = parseInt(zwAiForm.day)
  const h = parseInt(zwAiForm.hour)
  const min = parseInt(zwAiForm.minute) || 0
  
  if (isNaN(y) || isNaN(m) || isNaN(d) || isNaN(h)) {
    uni.showToast({ title: '请填写完整的出生时间', icon: 'none' })
    return
  }
  
  const question = zwAiForm.question
  const gender = ['男', '女'][zwAiForm.genderIdx]
  const date_type = ['solar', 'lunar'][zwAiForm.dateTypeIdx]
  
  zwAiLoading.value = true
  zwAiResult.value = '<div class="chat-bubble-ai"><div class="ai-stage">🔗 正在连接 DeepSeek AI 引擎...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:20%"></div></div><div class="chat-bubble-content"></div></div>'
  zwAiChatReady.value = false
  window._zwChatHistory = []
  
  try {
    let fullText = ''
    let charQueue = ''
    let typeTimer = null
    let doneReceived = false
    
    function startTypewriter() {
      if (typeTimer) return
      typeTimer = setInterval(function() {
        if (charQueue.length === 0 && doneReceived) {
          clearInterval(typeTimer)
          typeTimer = null
          zwAiResult.value = '<div class="chat-bubble-ai"><div class="chat-bubble-content">' + _zwRenderCards(fullText) + '</div></div>'
          zwAiChatReady.value = true
          zwAiLoading.value = false
          return
        }
        if (charQueue.length === 0) return
        const take = charQueue.length > 3 ? 2 : 1
        fullText += charQueue.substring(0, take)
        charQueue = charQueue.substring(take)
        zwAiResult.value = '<div class="chat-bubble-ai"><div class="ai-stage"><img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成解读...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div><div class="chat-bubble-content">' + _stripMarkdown(fullText).replace(/\n/g, '<br>') + '</div></div>'
      }, 35)
    }
    
    const token = uni.getStorageSync('xc_token') || ''
    const resp = await fetch('/api/ziwei/ask/stream', {
      method: 'POST',
      headers: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
      body: JSON.stringify({
        year: y, month: m, day: d, hour: h, minute: min,
        gender: gender, date_type: date_type,
        question: question,
        analysis_type: zwAnalysisTypes[zwAiForm.analysisTypeIdx].key
      })
    })
    
    if (!resp.ok) {
      zwAiResult.value = '<div style="color:var(--danger);padding:16px;">请求失败</div>'
      zwAiLoading.value = false
      return
    }
    
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    
    async function pump() {
      try {
        const { done, value } = await reader.read()
        if (done) {
          doneReceived = true
          return
        }
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i]
          if (line.indexOf('data:') !== 0) continue
          try {
            const data = JSON.parse(line.replace('data:', '').trim())
            if (data.type === 'progress') {
              if (data.stage === 'connecting') {
                zwAiResult.value = '<div class="chat-bubble-ai"><div class="ai-stage">🔗 正在连接...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:20%"></div></div><div class="chat-bubble-content"></div></div>'
              } else if (data.stage === 'analyzing') {
                zwAiResult.value = '<div class="chat-bubble-ai"><div class="ai-stage">🧠 排盘分析中...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:40%"></div></div><div class="chat-bubble-content"></div></div>'
              } else if (data.stage === 'generating') {
                zwAiResult.value = '<div class="chat-bubble-ai"><div class="ai-stage"><img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成解读...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div><div class="chat-bubble-content"></div></div>'
                startTypewriter()
              }
            } else if (data.type === 'chunk' || data.type === 'delta') {
              if (!typeTimer) startTypewriter()
              charQueue += data.content
            } else if (data.type === 'done') {
              doneReceived = true
            } else if (data.type === 'error') {
              zwAiResult.value = '<div style="color:var(--danger);padding:16px;">' + data.message + '</div>'
              zwAiLoading.value = false
            }
          } catch(_) {}
        }
        pump()
      } catch (e) {
        zwAiResult.value = '<div style="color:var(--danger);padding:16px;">请求失败</div>'
        zwAiLoading.value = false
      }
    }
    pump()
  } catch (e) {
    zwAiResult.value = '<div style="color:var(--danger);padding:16px;">请求失败</div>'
    zwAiLoading.value = false
  }
}

function zwSendFollowUp() {
  const question = zwAiFollowUpQuestion.value.trim()
  if (!question) return
  zwAiFollowUpQuestion.value = ''
  
  window._zwChatHistory = window._zwChatHistory || []
  window._zwChatHistory.push({ role: 'user', content: question })
  
  const userBubble = '<div class="chat-bubble-user">' + question + '</div>'
  const aiBubbleId = 'zwFollow_' + Date.now()
  const aiBubble = '<div class="chat-bubble-ai" id="' + aiBubbleId + '"><div class="ai-stage"><img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成回复...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div><div class="chat-bubble-content"></div></div>'
  
  zwAiResult.value = zwAiResult.value + userBubble + aiBubble
  
  fetch('/api/ziwei/ask/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question: question, history: window._zwChatHistory })
  }).then(async function(resp) {
    if (!resp.ok) return
    const reader = resp.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    let fullText = ''
    let charQueue = ''
    let typeTimer = null
    let doneReceived = false
    
    function startTypewriter() {
      if (typeTimer) return
      typeTimer = setInterval(function() {
        if (charQueue.length === 0 && doneReceived) {
          clearInterval(typeTimer)
          typeTimer = null
          window._zwChatHistory.push({ role: 'assistant', content: fullText })
          return
        }
        if (charQueue.length === 0) return
        const take = charQueue.length > 3 ? 2 : 1
        fullText += charQueue.substring(0, take)
        charQueue = charQueue.substring(take)
        const bubble = document.getElementById(aiBubbleId)
        if (bubble) {
          const contentEl = bubble.querySelector('.chat-bubble-content')
          if (contentEl) contentEl.innerHTML = _stripMarkdown(fullText).replace(/\n/g, '<br>')
        }
      }, 35)
    }
    
    async function pump() {
      try {
        const { done, value } = await reader.read()
        if (done) {
          doneReceived = true
          return
        }
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (let i = 0; i < lines.length; i++) {
          const line = lines[i]
          if (line.indexOf('data:') !== 0) continue
          try {
            const data = JSON.parse(line.replace('data:', '').trim())
            if (data.type === 'chunk' || data.type === 'delta') {
              if (!typeTimer) startTypewriter()
              charQueue += data.content
            } else if (data.type === 'done') {
              doneReceived = true
            }
          } catch(_) {}
        }
        pump()
      } catch(e) {}
    }
    pump()
  })
}

function _stripMarkdown(s) {
  if (!s) return ''
  return s.replace(/^#{1,6}\s*/gm, '').replace(/\*\*/g, '').replace(/^[-*]\s+/gm, '')
}

function _zwRenderCards(text) {
  text = _stripMarkdown(text)
  const sections = text.split(/\n(?=#{2,}|\d+\.\s+\*\*)/)
  let html = ''
  sections.forEach(function(sec) {
    let title = ''
    let body = sec
    let m = sec.match(/^(#{2,})\s+(.+)/)
    if (m) {
      title = m[2]
      body = sec.substring(m[0].length).trim()
    } else {
      m = sec.match(/^(\d+\.)\s+\*\*(.+?)\*\*[：:]\s*/)
      if (m) {
        title = m[2]
        body = sec.substring(m[0].length).trim()
      }
    }
    body = body.replace(/\*\*(.+?)\*\*/g, '$1').replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')
    if (!body) body = '&nbsp;'
    if (title) {
      html += '<div class="qai-card-item"><div class="qai-card-title">' + title + '</div><div class="qai-card-body"><p>' + body + '</p></div></div>'
    } else {
      html += '<div class="qai-card-item"><div class="qai-card-body"><p>' + body + '</p></div></div>'
    }
  })
  return html
}

// 渲染函数
function zwBasicItem(label, value) {
  return '<div class="zw-basic-item"><span class="zw-basic-label">' + label + '</span><span class="zw-basic-value">' + (value || '') + '</span></div>'
}

function zwPalaceCell(p) {
  if (!p) return '<div class="zw-palace-cell"></div>'
  let cls = 'zw-palace-cell'
  let badge = ''
  if (p.is_body_palace) { cls += ' is-body'; badge += '<span class="zw-palace-badge zw-badge-body">身</span>' }
  if (p.name === '命宫') { cls += ' is-soul'; badge += '<span class="zw-palace-badge zw-badge-soul">命</span>' }
  let starsHtml = ''
  ;(p.major_stars || []).forEach(function(s) {
    let mut = ''
    if (s.mutagen) {
      let mCls = ''
      if (s.mutagen.includes('禄')) mCls = 'zw-mutagen-lu'
      else if (s.mutagen.includes('权')) mCls = 'zw-mutagen-quan'
      else if (s.mutagen.includes('科')) mCls = 'zw-mutagen-ke'
      else if (s.mutagen.includes('忌')) mCls = 'zw-mutagen-ji'
      mut = '<span class="zw-mutagen ' + mCls + '">' + s.mutagen + '</span>'
    }
    const brightness = s.brightness ? '(' + s.brightness + ')' : ''
    starsHtml += '<span class="zw-star-major">' + s.name + brightness + mut + '</span>'
  })
  ;(p.minor_stars || []).forEach(function(s) {
    starsHtml += '<span class="zw-star-minor">' + s.name + '</span>'
  })
  ;(p.adjective_stars || []).slice(0, 4).forEach(function(s) {
    starsHtml += '<span class="zw-star-adj">' + s.name + '</span>'
  })
  let decHtml = ''
  if (p.decadal && p.decadal.range) {
    decHtml = '<div class="zw-palace-decadal">大限: ' + p.decadal.range[0] + '-' + p.decadal.range[1] + '岁 ' + (p.decadal.heavenly_stem || '') + (p.decadal.earthly_branch || '') + '</div>'
  }
  return '<div class="' + cls + '">' +
    badge +
    '<div class="zw-palace-header"><span class="zw-palace-name">' + p.name + '</span><span class="zw-palace-ganzhi">' + (p.ganzhi || '') + '</span></div>' +
    '<div class="zw-palace-stars">' + starsHtml + '</div>' +
    decHtml +
    '</div>'
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
  html += zwBasicItem('五行局', bi.five_elements_class)
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
  html += '<div class="zw-center-info"><div class="zw-center-title">紫微斗数命盘</div><div class="zw-center-wuxing">' + (bi.five_elements_class || '') + '</div><div class="zw-center-soul">命主: ' + (cp.soul_star || '') + '</div><div class="zw-center-soul">身主: ' + (cp.body_star || '') + '</div><div class="zw-center-date">' + (bi.solar_date || '') + ' ' + (bi.shichen || '') + '</div></div>'
  html += zwPalaceCell(palaces[7])
  html += zwPalaceCell(palaces[1])
  html += zwPalaceCell(palaces[8])
  html += zwPalaceCell(palaces[0])
  html += zwPalaceCell(palaces[11])
  html += zwPalaceCell(palaces[10])
  html += zwPalaceCell(palaces[9])
  html += '</div>'
  if (d.decadal_overview && d.decadal_overview.length > 0) {
    html += '<div class="zw-decadal-card"><div class="zw-decadal-title">📅 大限概览</div><table class="zw-decadal-table"><tr><th>宫位</th><th>年龄范围</th><th>干支</th></tr>'
    d.decadal_overview.forEach(function(dec) {
      const range = dec.age_range || []
      html += '<tr><td>' + (dec.palace_name || '') + '</td><td>' + (range[0] || '') + '-' + (range[1] || '') + '岁</td><td>' + (dec.ganzhi || '') + '</td></tr>'
    })
    html += '</table></div>'
  }
  html += '<div class="privacy-note" style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>'
  html += '</div>'
  return html
}

function renderZiweiHoroscopeWithPan(d) {
  let html = '<div class="zw-result-wrap">'
  const hd = d.horoscope || d
  
  html += '<div class="zw-horoscope-title">🔮 推运信息 - ' + (d.target_date || '') + '</div>'
  html += '<div class="zw-period-grid">'
  const periods = [
    { key: 'decadal', label: '大限' },
    { key: 'age', label: '小限' },
    { key: 'yearly', label: '流年' },
    { key: 'monthly', label: '流月' },
    { key: 'daily', label: '流日' },
    { key: 'hourly', label: '流时' }
  ]
  periods.forEach(function(p) {
    const pd = hd[p.key]
    if (!pd) return
    html += '<div class="zw-period-card">'
    html += '<div class="zw-period-name">' + (pd.name || p.label) + '</div>'
    html += '<div class="zw-period-ganzhi">' + (pd.ganzhi || '') + '</div>'
    if (pd.range) html += '<div class="zw-period-range">' + pd.range[0] + '-' + pd.range[1] + '岁</div>'
    if (pd.nominal_age) html += '<div class="zw-period-range">虚岁' + pd.nominal_age + '</div>'
    if (pd.mutagen && pd.mutagen.length > 0) {
      html += '<div class="zw-period-mutagen"><span style="color:var(--text-4);font-size:0.6875rem;">四化:</span>'
      pd.mutagen.forEach(function(m) {
        let mCls = ''
        if (m.includes('禄')) mCls = 'zw-mutagen-lu'
        else if (m.includes('权')) mCls = 'zw-mutagen-quan'
        else if (m.includes('科')) mCls = 'zw-mutagen-ke'
        else if (m.includes('忌')) mCls = 'zw-mutagen-ji'
        html += '<span class="zw-mutagen ' + mCls + '">' + m + '</span>'
      })
      html += '</div>'
    }
    html += '</div>'
  })
  html += '</div>'
  
  if (d.pan && d.pan.twelve_palaces) {
    const panData = d.pan
    const bi = panData.basic_info || {}
    const cp = panData.core_palace || {}
    html += '<div class="zw-basic-card"><div class="zw-basic-grid">'
    html += zwBasicItem('阳历', bi.solar_date)
    html += zwBasicItem('农历', bi.lunar_date)
    html += zwBasicItem('八字', bi.chinese_date)
    html += zwBasicItem('时辰', (bi.shichen || '') + ' ' + (bi.shichen_range || ''))
    html += zwBasicItem('生肖', bi.zodiac)
    html += zwBasicItem('星座', bi.sign)
    html += zwBasicItem('五行局', bi.five_elements_class)
    html += zwBasicItem('命主', cp.soul_star)
    html += zwBasicItem('身主', cp.body_star)
    html += '</div></div>'
    const palaces = panData.twelve_palaces || []
    html += '<div class="zw-palace-grid">'
    html += zwPalaceCell(palaces[4])
    html += zwPalaceCell(palaces[3])
    html += zwPalaceCell(palaces[5])
    html += zwPalaceCell(palaces[6])
    html += zwPalaceCell(palaces[2])
    html += '<div class="zw-center-info"><div class="zw-center-title">紫微斗数命盘</div><div class="zw-center-wuxing">' + (bi.five_elements_class || '') + '</div><div class="zw-center-soul">命主: ' + (cp.soul_star || '') + '</div><div class="zw-center-soul">身主: ' + (cp.body_star || '') + '</div><div class="zw-center-date">' + (bi.solar_date || '') + ' ' + (bi.shichen || '') + '</div></div>'
    html += zwPalaceCell(palaces[7])
    html += zwPalaceCell(palaces[1])
    html += zwPalaceCell(palaces[8])
    html += zwPalaceCell(palaces[0])
    html += zwPalaceCell(palaces[11])
    html += zwPalaceCell(palaces[10])
    html += zwPalaceCell(palaces[9])
    html += '</div>'
  } else if (d.twelve_palaces) {
    const bi = d.basic_info || {}
    const cp = d.core_palace || {}
    html += '<div class="zw-basic-card"><div class="zw-basic-grid">'
    html += zwBasicItem('阳历', bi.solar_date)
    html += zwBasicItem('农历', bi.lunar_date)
    html += zwBasicItem('八字', bi.chinese_date)
    html += zwBasicItem('时辰', (bi.shichen || '') + ' ' + (bi.shichen_range || ''))
    html += zwBasicItem('生肖', bi.zodiac)
    html += zwBasicItem('星座', bi.sign)
    html += zwBasicItem('五行局', bi.five_elements_class)
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
    html += '<div class="zw-center-info"><div class="zw-center-title">紫微斗数命盘</div><div class="zw-center-wuxing">' + (bi.five_elements_class || '') + '</div><div class="zw-center-soul">命主: ' + (cp.soul_star || '') + '</div><div class="zw-center-soul">身主: ' + (cp.body_star || '') + '</div><div class="zw-center-date">' + (bi.solar_date || '') + ' ' + (bi.shichen || '') + '</div></div>'
    html += zwPalaceCell(palaces[7])
    html += zwPalaceCell(palaces[1])
    html += zwPalaceCell(palaces[8])
    html += zwPalaceCell(palaces[0])
    html += zwPalaceCell(palaces[11])
    html += zwPalaceCell(palaces[10])
    html += zwPalaceCell(palaces[9])
    html += '</div>'
  }
  
  html += '<div class="privacy-note" style="margin-top:16px;">⚠️ 以上内容仅为民俗文化与传统命理科普参考，不构成任何决策建议</div>'
  html += '</div>'
  return html
}

onShow(function() {
  const t = uni.getStorageSync('xc_theme')
  if (t && t !== theme.value) {
    theme.value = t
    try {
      document.documentElement.setAttribute('data-theme', t)
      document.body.setAttribute('data-theme', t)
    } catch(_) {}
  }
})

onMounted(function() {
  initDatePickers()
  const now = new Date()
  const day = now.getDate()
  if (zwDayOptions.value.length > day - 1) {
    zwTargetDayIdx.value = day - 1
  }
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
.tool-tabs { display: flex; gap: 4px; margin-bottom: 28px; border-bottom: 1px solid var(--card-border); }
.tool-tab { padding: 12px 20px; border-radius: 10px 10px 0 0; font-size: 0.875rem; cursor: pointer; border: 1px solid transparent; border-bottom: none; color: var(--text-3); background: transparent; transition: all 0.2s; }
.tool-tab.active { color: var(--accent); background: var(--accent-glow); border-color: var(--accent); font-weight: 600; }
.tool-tab:hover { color: var(--accent); }
.tab-badge { font-size: 0.5625rem; padding: 1px 5px; border-radius: 4px; background: var(--accent); color: #fff; margin-left: 4px; }
.tab-badge.free { background: var(--success); }
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 6px; letter-spacing: 1px; }
.form-input, .form-select-picker { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.form-input .uni-input-wrapper { height: 22px; }
.form-input .uni-input-input { height: 22px !important; padding: 0 !important; margin: 0; border: none !important; background: transparent !important; font-size: inherit !important; color: inherit !important; line-height: 22px !important; }
.form-hint { font-size: 0.6875rem; color: var(--text-3); }
.submit-btn { width: 100%; padding: 14px; border-radius: 30px; border: none; background: hsl(35, 38%, 52%); color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; letter-spacing: 2px; margin-top: 8px; text-align: center; transition: opacity 0.2s; }
.submit-btn:hover { opacity: 0.9; }
.btn-row { display: flex; gap: 10px; justify-content: center; margin-top: 16px; }
.btn-row .submit-btn { flex: 1; margin-top: 0; }
.btn-ghost { background: transparent; border: 1px solid var(--card-border); color: var(--text-3); padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; }
.privacy-note { margin-top: 12px; padding: 10px 14px; border-radius: 10px; background: rgba(110,195,135,0.08); border: 1px solid rgba(110,195,135,0.15); font-size: 0.75rem; color: var(--success); text-align: center; }
.zw-form-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 12px; }
.zw-birth-time-group { grid-column: 1 / -1; padding: 14px 16px; border-radius: 12px; border: 1px solid var(--card-border); background: var(--section-alt); margin-bottom: 4px; }
.zw-birth-row { display: grid; grid-template-columns: minmax(104px, 1.25fr) repeat(4, minmax(64px, 1fr)); gap: 8px; align-items: center; }
.zw-birth-col { min-width: 0; }
.zw-birth-select { width: 100%; min-height: 40px; padding: 9px 22px 9px 10px; border: 1.5px solid var(--card-border); border-radius: 8px; background-color: var(--card-bg); color: var(--text-1); font-size: 0.85rem; font-weight: 600; line-height: 20px; text-align: center; box-sizing: border-box; cursor: pointer; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath d='M5 7L1 3h8z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 8px center; transition: border-color 0.18s, background-color 0.18s, box-shadow 0.18s; }
.zw-birth-select:hover { border-color: var(--accent); background-color: var(--input-bg); }
.zw-result { margin-top: 16px; }
.zw-result-card { background: var(--card-bg); border-radius: 12px; padding: 20px; border: 1px solid var(--card-border); }
.zw-result-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 10px; color: var(--accent); letter-spacing: 2px; }

.qf-datetime-row { display: flex; gap: 8px; flex-wrap: wrap; }
.qf-dt-col { flex: 1; min-width: 60px; }
.qf-dt-col-narrow { flex: 0 0 70px; }
.qf-datetime-select { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; text-align: center; }

.zw-result-wrap { margin-top: 24px; }
.zw-basic-card { background: var(--bg-2); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.zw-basic-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
.zw-basic-item { display: flex; flex-direction: column; gap: 2px; }
.zw-basic-label { font-size: 0.75rem; color: var(--text-4); letter-spacing: 1px; }
.zw-basic-value { font-size: 0.9375rem; font-weight: 600; color: var(--accent); }
.zw-palace-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 20px; }
.zw-palace-cell { background: var(--bg-2); border: 1px solid var(--border); border-radius: 10px; padding: 12px; min-height: 110px; position: relative; transition: all 0.2s; cursor: default; }
.zw-palace-cell:hover { border-color: var(--accent); box-shadow: 0 0 20px rgba(212,168,71,0.08); }
.zw-palace-cell.is-soul { border-color: var(--accent); box-shadow: 0 0 16px rgba(212,168,71,0.12); }
.zw-palace-cell.is-body { border-color: var(--danger); }
.zw-palace-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.zw-palace-name { font-size: 0.875rem; font-weight: 700; color: var(--accent); }
.zw-palace-ganzhi { font-size: 0.6875rem; color: var(--text-4); }
.zw-palace-badge { font-size: 0.5625rem; padding: 1px 5px; border-radius: 3px; position: absolute; top: 5px; right: 5px; }
.zw-badge-soul { background: rgba(212,168,71,0.15); color: var(--accent); }
.zw-badge-body { background: rgba(231,76,60,0.12); color: var(--danger); }
.zw-palace-stars { margin-top: 4px; display: flex; flex-wrap: wrap; gap: 3px; }
.zw-star-major { display: inline-block; padding: 2px 7px; background: rgba(212,168,71,0.1); color: var(--accent); border-radius: 4px; font-size: 0.8125rem; font-weight: 600; }
.zw-star-minor { display: inline-block; padding: 1px 6px; background: rgba(41,128,185,0.08); color: #5dade2; border-radius: 4px; font-size: 0.75rem; }
.zw-star-adj { display: inline-block; padding: 1px 4px; color: #7dcea0; font-size: 0.6875rem; }
.zw-mutagen { font-size: 0.625rem; padding: 1px 4px; border-radius: 3px; margin-left: 2px; font-weight: 600; }
.zw-mutagen-lu { background: rgba(39,174,96,0.15); color: #27ae60; }
.zw-mutagen-quan { background: rgba(231,76,60,0.12); color: #e74c3c; }
.zw-mutagen-ke { background: rgba(52,152,219,0.12); color: #3498db; }
.zw-mutagen-ji { background: rgba(142,68,173,0.12); color: #8e44ad; }
.zw-palace-decadal { margin-top: 6px; font-size: 0.6875rem; color: var(--text-4); border-top: 1px solid var(--border); padding-top: 4px; }
.zw-center-info { grid-column: 2 / 4; grid-row: 2 / 4; background: var(--bg-2); border: 2px solid var(--accent); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.zw-center-title { font-size: 1.125rem; color: var(--accent); font-weight: 700; letter-spacing: 3px; margin-bottom: 8px; }
.zw-center-wuxing { font-size: 1rem; color: #c39bd3; font-weight: 600; margin-bottom: 6px; }
.zw-center-soul { font-size: 0.8125rem; color: var(--text-3); margin: 2px 0; }
.zw-center-date { font-size: 0.75rem; color: var(--text-4); margin-top: 6px; }
.zw-decadal-card { background: var(--bg-2); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.zw-decadal-title { font-size: 0.9375rem; font-weight: 600; color: var(--accent); margin-bottom: 14px; display: flex; align-items: center; gap: 6px; }
.zw-decadal-table { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
.zw-decadal-table th, .zw-decadal-table td { padding: 8px 10px; text-align: center; border-bottom: 1px solid var(--border); }
.zw-decadal-table th { color: var(--text-4); font-weight: 500; font-size: 0.75rem; letter-spacing: 1px; }
.zw-decadal-table td { color: var(--text-2); }
.zw-horoscope-title { font-size: 0.9375rem; font-weight: 600; color: #c39bd3; margin-bottom: 16px; }
.zw-period-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.zw-period-card { background: var(--bg-2); border: 1px solid var(--border); border-radius: 10px; padding: 14px; transition: all 0.2s; }
.zw-period-card:hover { border-color: #c39bd3; box-shadow: 0 0 12px rgba(155,89,182,0.08); }
.zw-period-name { font-weight: 600; color: var(--accent); margin-bottom: 4px; font-size: 0.875rem; }
.zw-period-ganzhi { font-size: 0.875rem; color: #c39bd3; }
.zw-period-range { font-size: 0.75rem; color: var(--text-4); margin-top: 2px; }
.zw-period-mutagen { font-size: 0.75rem; color: var(--text-3); margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }

/* v-html 插入的命盘节点不会带页面 scope 属性，必须用 deep 才能保留卡片样式 */
.zw-result :deep(.zw-result-wrap) { margin-top: 24px; }
.zw-result :deep(.zw-basic-card) { background: var(--bg-2); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.zw-result :deep(.zw-basic-grid) { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
.zw-result :deep(.zw-basic-item) { display: flex; flex-direction: column; gap: 2px; }
.zw-result :deep(.zw-basic-label) { font-size: 0.75rem; color: var(--text-4); letter-spacing: 1px; }
.zw-result :deep(.zw-basic-value) { font-size: 0.9375rem; font-weight: 600; color: var(--accent); }
.zw-result :deep(.zw-palace-grid) { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; margin-bottom: 20px; }
.zw-result :deep(.zw-palace-cell) { background: var(--bg-2); border: 1px solid var(--border); border-radius: 10px; padding: 12px; min-height: 110px; position: relative; transition: all 0.2s; cursor: default; }
.zw-result :deep(.zw-palace-cell:hover) { border-color: var(--accent); box-shadow: 0 0 20px rgba(212,168,71,0.08); }
.zw-result :deep(.zw-palace-cell.is-soul) { border-color: var(--accent); box-shadow: 0 0 16px rgba(212,168,71,0.12); }
.zw-result :deep(.zw-palace-cell.is-body) { border-color: var(--danger); }
.zw-result :deep(.zw-palace-header) { display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px; }
.zw-result :deep(.zw-palace-name) { font-size: 0.875rem; font-weight: 700; color: var(--accent); }
.zw-result :deep(.zw-palace-ganzhi) { font-size: 0.6875rem; color: var(--text-4); }
.zw-result :deep(.zw-palace-badge) { font-size: 0.5625rem; padding: 1px 5px; border-radius: 3px; position: absolute; top: 5px; right: 5px; }
.zw-result :deep(.zw-badge-soul) { background: rgba(212,168,71,0.15); color: var(--accent); }
.zw-result :deep(.zw-badge-body) { background: rgba(231,76,60,0.12); color: var(--danger); }
.zw-result :deep(.zw-palace-stars) { margin-top: 4px; display: flex; flex-wrap: wrap; gap: 3px; }
.zw-result :deep(.zw-star-major) { display: inline-block; padding: 2px 7px; background: rgba(212,168,71,0.1); color: var(--accent); border-radius: 4px; font-size: 0.8125rem; font-weight: 600; }
.zw-result :deep(.zw-star-minor) { display: inline-block; padding: 1px 6px; background: rgba(41,128,185,0.08); color: #5dade2; border-radius: 4px; font-size: 0.75rem; }
.zw-result :deep(.zw-star-adj) { display: inline-block; padding: 1px 4px; color: #7dcea0; font-size: 0.6875rem; }
.zw-result :deep(.zw-mutagen) { font-size: 0.625rem; padding: 1px 4px; border-radius: 3px; margin-left: 2px; font-weight: 600; }
.zw-result :deep(.zw-mutagen-lu) { background: rgba(39,174,96,0.15); color: #27ae60; }
.zw-result :deep(.zw-mutagen-quan) { background: rgba(231,76,60,0.12); color: #e74c3c; }
.zw-result :deep(.zw-mutagen-ke) { background: rgba(52,152,219,0.12); color: #3498db; }
.zw-result :deep(.zw-mutagen-ji) { background: rgba(142,68,173,0.12); color: #8e44ad; }
.zw-result :deep(.zw-palace-decadal) { margin-top: 6px; font-size: 0.6875rem; color: var(--text-4); border-top: 1px solid var(--border); padding-top: 4px; }
.zw-result :deep(.zw-center-info) { grid-column: 2 / 4; grid-row: 2 / 4; background: var(--bg-2); border: 2px solid var(--accent); border-radius: 12px; padding: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; }
.zw-result :deep(.zw-center-title) { font-size: 1.125rem; color: var(--accent); font-weight: 700; letter-spacing: 3px; margin-bottom: 8px; }
.zw-result :deep(.zw-center-wuxing) { font-size: 1rem; color: #c39bd3; font-weight: 600; margin-bottom: 6px; }
.zw-result :deep(.zw-center-soul) { font-size: 0.8125rem; color: var(--text-3); margin: 2px 0; }
.zw-result :deep(.zw-center-date) { font-size: 0.75rem; color: var(--text-4); margin-top: 6px; }
.zw-result :deep(.zw-decadal-card) { background: var(--bg-2); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.zw-result :deep(.zw-decadal-title) { font-size: 0.9375rem; font-weight: 600; color: var(--accent); margin-bottom: 14px; display: flex; align-items: center; gap: 6px; }
.zw-result :deep(.zw-decadal-table) { width: 100%; border-collapse: collapse; font-size: 0.8125rem; }
.zw-result :deep(.zw-decadal-table th), .zw-result :deep(.zw-decadal-table td) { padding: 8px 10px; text-align: center; border-bottom: 1px solid var(--border); }
.zw-result :deep(.zw-decadal-table th) { color: var(--text-4); font-weight: 500; font-size: 0.75rem; letter-spacing: 1px; }
.zw-result :deep(.zw-decadal-table td) { color: var(--text-2); }
.zw-result :deep(.zw-horoscope-title) { font-size: 0.9375rem; font-weight: 600; color: #c39bd3; margin-bottom: 16px; }
.zw-result :deep(.zw-period-grid) { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 12px; }
.zw-result :deep(.zw-period-card) { background: var(--bg-2); border: 1px solid var(--border); border-radius: 10px; padding: 14px; transition: all 0.2s; }
.zw-result :deep(.zw-period-card:hover) { border-color: #c39bd3; box-shadow: 0 0 12px rgba(155,89,182,0.08); }
.zw-result :deep(.zw-period-name) { font-weight: 600; color: var(--accent); margin-bottom: 4px; font-size: 0.875rem; }
.zw-result :deep(.zw-period-ganzhi) { font-size: 0.875rem; color: #c39bd3; }
.zw-result :deep(.zw-period-range) { font-size: 0.75rem; color: var(--text-4); margin-top: 2px; }
.zw-result :deep(.zw-period-mutagen) { font-size: 0.75rem; color: var(--text-3); margin-top: 6px; display: flex; flex-wrap: wrap; gap: 4px; }

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
.analysis-type-row { display: flex; flex-wrap: wrap; gap: 6px; }
.analysis-type-btn { padding: 6px 12px; border-radius: 8px; border: 1px solid var(--card-border); background: transparent; color: var(--text-3); font-size: 0.75rem; cursor: pointer; text-align: center; white-space: nowrap; transition: all 0.15s; }
.analysis-type-btn.active { background: var(--accent-glow); color: var(--accent); border-color: var(--accent); }

@media (max-width: 768px) {
  .section { padding: 48px 16px; }
  .tool-hero { padding: 40px 16px 24px; }
  .tool-hero-title { font-size: 1.5rem; }
  .tool-container { padding: 20px 16px; }
  .zw-form-grid { grid-template-columns: 1fr 1fr; }
  .zw-birth-time-group { padding: 12px; }
  .zw-birth-row { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .zw-birth-col-year { grid-column: span 1; }
  .zw-birth-col-minute { grid-column: span 1; }
  .zw-basic-grid { grid-template-columns: 1fr 1fr; }
  .zw-palace-grid { grid-template-columns: repeat(4, 1fr); }
  .zw-center-info { grid-column: 2 / 4; grid-row: 2 / 4; }
  .qf-datetime-row { gap: 6px; }
  .qf-dt-col { min-width: 55px; }
  .qf-dt-col-narrow { flex: 0 0 60px; }
}

@media (max-width: 480px) {
  .tool-tabs { overflow-x: auto; gap: 2px; }
  .tool-tab { padding: 10px 14px; font-size: 0.8125rem; white-space: nowrap; }
  .zw-result-wrap { overflow-x: hidden; }
  .zw-result :deep(.zw-result-wrap) { overflow-x: hidden; }
  .zw-palace-grid { grid-template-columns: repeat(4, 1fr); gap: 3px; }
  .zw-result :deep(.zw-palace-grid) { grid-template-columns: repeat(4, 1fr); gap: 3px; }
  .zw-palace-cell { min-height: 70px; padding: 5px; }
  .zw-result :deep(.zw-palace-cell) { min-height: 70px; padding: 5px; }
  .zw-star-major { font-size: 0.625rem; padding: 1px 3px; }
  .zw-result :deep(.zw-star-major) { font-size: 0.625rem; padding: 1px 3px; }
  .zw-star-minor { font-size: 0.5625rem; padding: 1px 3px; }
  .zw-result :deep(.zw-star-minor) { font-size: 0.5625rem; padding: 1px 3px; }
  .zw-star-adj { font-size: 0.5rem; }
  .zw-result :deep(.zw-star-adj) { font-size: 0.5rem; }
  .zw-palace-name { font-size: 0.7rem; }
  .zw-result :deep(.zw-palace-name) { font-size: 0.7rem; }
  .zw-palace-ganzhi { font-size: 0.5rem; }
  .zw-result :deep(.zw-palace-ganzhi) { font-size: 0.5rem; }
  .zw-center-info { padding: 8px; }
  .zw-result :deep(.zw-center-info) { padding: 8px; }
  .zw-center-title { font-size: 0.875rem; letter-spacing: 2px; }
  .zw-result :deep(.zw-center-title) { font-size: 0.875rem; letter-spacing: 2px; }
  .zw-center-wuxing { font-size: 0.75rem; }
  .zw-result :deep(.zw-center-wuxing) { font-size: 0.75rem; }
  .zw-center-soul { font-size: 0.625rem; }
  .zw-result :deep(.zw-center-soul) { font-size: 0.625rem; }
  .zw-center-date { font-size: 0.5625rem; }
  .zw-result :deep(.zw-center-date) { font-size: 0.5625rem; }
  .zw-period-grid { grid-template-columns: 1fr 1fr; }
  .zw-result :deep(.zw-period-grid) { grid-template-columns: 1fr 1fr; }
  .zw-form-grid { grid-template-columns: 1fr 1fr; gap: 8px; }
  .zw-birth-time-group { padding: 10px; }
  .zw-birth-row { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
  .zw-birth-col-year { grid-column: span 2; }
  .zw-birth-select { min-height: 38px; padding: 8px 20px 8px 8px; font-size: 0.8125rem; }
  .zw-basic-grid { grid-template-columns: 1fr 1fr; }
  .qf-datetime-row { gap: 4px; }
  .qf-dt-col { min-width: 50px; }
  .qf-dt-col-narrow { flex: 0 0 55px; }
  .qf-datetime-select { padding: 8px 10px; font-size: 0.8125rem; }
  .zw-palace-decadal { font-size: 0.5rem; padding-top: 2px; }
  .zw-result :deep(.zw-palace-decadal) { font-size: 0.5rem; padding-top: 2px; }
  .zw-palace-badge { font-size: 0.4375rem; padding: 1px 2px; }
  .zw-result :deep(.zw-palace-badge) { font-size: 0.4375rem; padding: 1px 2px; }
  .zw-mutagen { font-size: 0.5rem; padding: 1px 2px; }
  .zw-result :deep(.zw-mutagen) { font-size: 0.5rem; padding: 1px 2px; }
}
</style>
