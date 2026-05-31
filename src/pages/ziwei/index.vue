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
              <view class="form-group">
                <text class="form-label">盘名</text>
                <input type="text" class="form-input form-input-text" v-model="zwForm.chartName" placeholder="我的命盘">
              </view>
              <view class="form-group">
                <text class="form-label">出生地经度</text>
                <input type="digit" class="form-input form-input-text" v-model="zwForm.longitude" placeholder="如 116.4074">
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
              <input type="text" class="form-input form-input-text" v-model="zwAiForm.question" placeholder="请输入您想问的问题">
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
import { ref, reactive, onMounted, onUnmounted, computed } from 'vue'
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
  genderIdx: 0, dateTypeIdx: 0,
  chartName: '我的命盘',
  longitude: '116.4074'
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
const zwPanData = ref(null)
const zwFlowState = reactive({
  selectedYear: new Date().getFullYear(),
  selectedMonth: new Date().getMonth() + 1,
  selectedDecadeAge: null,
  horoscope: null,
  error: ''
})
let zwFlowRequestSeq = 0

async function ziweiFreePan() {
  try {
    const y = parseInt(zwForm.year)
    const m = parseInt(zwForm.month)
    const d = parseInt(zwForm.day)
    const h = parseInt(zwForm.hour)
    const min = parseInt(zwForm.minute) || 0
    const longitude = parseFloat(zwForm.longitude)
    
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
        date_type: ['solar', 'lunar'][zwForm.dateTypeIdx],
        longitude: isNaN(longitude) ? undefined : longitude,
        question: zwForm.chartName || ''
      }
    })
    
    const data = res.data
    if (data.error || (data.code && data.code !== 0)) {
      zwPanResult.value = '<div style="color:var(--danger);padding:16px;">' + (data.error || data.msg || '排盘失败') + '</div>'
      return
    }
    
    const panData = data.data || data
    zwPanData.value = panData
    zwFlowState.selectedYear = new Date().getFullYear()
    zwFlowState.selectedMonth = new Date().getMonth() + 1
    zwFlowState.selectedDecadeAge = null
    zwFlowState.horoscope = null
    zwFlowState.error = ''
    zwPanResult.value = renderZiweiPan(panData)
    refreshZiweiFlow()
  } catch (e) {
    const errMsg = (e && e.errMsg) || (e && e.message) || (e && String(e)) || '未知错误'
    zwPanResult.value = '<div style="color:var(--danger);padding:16px;">排盘失败: ' + errMsg + '</div>'
  }
}

function rerenderZiweiPan() {
  if (!zwPanData.value) return
  zwPanResult.value = renderZiweiPan(zwPanData.value)
}

function findZiweiFlowTarget(target) {
  let node = target
  while (node) {
    if (node.dataset && (node.dataset.flowDecade || node.dataset.flowYear || node.dataset.flowMonth)) return node
    node = node.parentElement
  }
  return null
}

function handleZiweiPanClick(e) {
  const target = findZiweiFlowTarget(e && e.target)
  if (!target) return
  const decade = parseInt(target.dataset.flowDecade)
  const year = parseInt(target.dataset.flowYear)
  const month = parseInt(target.dataset.flowMonth)
  if (!isNaN(decade)) return selectZiweiFlow('decadal', decade)
  selectZiweiFlow(isNaN(year) ? 'month' : 'year', isNaN(year) ? month : year)
}

function handleZiweiDocumentClick(e) {
  const target = findZiweiFlowTarget(e && e.target)
  if (!target) return
  if (!target.closest || !target.closest('.zw-result')) return
  const decade = parseInt(target.dataset.flowDecade)
  const year = parseInt(target.dataset.flowYear)
  const month = parseInt(target.dataset.flowMonth)
  if (!isNaN(decade)) return selectZiweiFlow('decadal', decade)
  selectZiweiFlow(isNaN(year) ? 'month' : 'year', isNaN(year) ? month : year)
}

function selectZiweiFlow(type, value) {
  const n = parseInt(value)
  if (isNaN(n)) return
  if (type === 'decadal') {
    const birthYear = zwPanData.value ? zwBirthYearFromPan(zwPanData.value) : parseInt(zwForm.year)
    zwFlowState.selectedDecadeAge = n
    zwFlowState.selectedYear = birthYear + n - 1
  }
  if (type === 'year') {
    zwFlowState.selectedYear = n
    const palaces = zwPanData.value ? (zwPanData.value.twelve_palaces || []) : []
    zwFlowState.selectedDecadeAge = zwDecadeStartForYear(palaces, zwPanData.value, n)
  }
  if (type === 'month') zwFlowState.selectedMonth = n
  zwFlowState.error = ''
  rerenderZiweiPan()
  refreshZiweiFlow()
}

async function getZiweiFlowTargetDate(year, lunarMonth) {
  try {
    const res = await uni.request({
      url: '/api/bazi/lunar-to-solar',
      method: 'POST',
      data: { year, month: lunarMonth, day: 1, isLeap: false }
    })
    const data = res.data || {}
    if (data.success && data.year && data.month && data.day) {
      return data.year + '-' + pad2(data.month) + '-' + pad2(data.day)
    }
  } catch (e) {}
  return year + '-' + pad2(lunarMonth) + '-01'
}

async function refreshZiweiFlow() {
  if (!zwPanData.value) return
  const seq = ++zwFlowRequestSeq
  zwFlowState.error = ''
  try {
    const longitude = parseFloat(zwForm.longitude)
    const targetDate = await getZiweiFlowTargetDate(zwFlowState.selectedYear, zwFlowState.selectedMonth)
    const res = await uni.request({
      url: '/api/ziwei/horoscope',
      method: 'POST',
      data: {
        year: parseInt(zwForm.year),
        month: parseInt(zwForm.month),
        day: parseInt(zwForm.day),
        hour: parseInt(zwForm.hour),
        minute: parseInt(zwForm.minute) || 0,
        gender: ['男', '女'][zwForm.genderIdx],
        date_type: ['solar', 'lunar'][zwForm.dateTypeIdx],
        longitude: isNaN(longitude) ? undefined : longitude,
        target_date: targetDate,
        question: zwForm.chartName || ''
      }
    })
    const data = res.data || {}
    if (data.error || (data.code && data.code !== 0)) {
      if (seq !== zwFlowRequestSeq) return
      zwFlowState.error = data.error || data.msg || '流月切换失败'
      return
    }
    const flowData = data.data || data
    if (seq !== zwFlowRequestSeq) return
    zwFlowState.horoscope = flowData.horoscope || null
    if (flowData.target_date) zwPanData.value.target_date = flowData.target_date
  } catch (e) {
    if (seq !== zwFlowRequestSeq) return
    zwFlowState.error = (e && (e.errMsg || e.message)) || '流月切换失败'
  } finally {
    if (seq === zwFlowRequestSeq) rerenderZiweiPan()
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
var _zwCurrentConvId = null

function _saveZwConversation(question, birthInfo) {
  var token = uni.getStorageSync('xc_token') || ''
  if (!token) return
  uni.request({
    url: '/api/ziwei/conversations', method: 'POST',
    header: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
    data: JSON.stringify({
      title: (question || '紫微斗数AI解读').substring(0, 50),
      birth_data: birthInfo || {},
      messages: window._zwChatHistory || []
    }),
    success: function(res) {
      if (res.data && res.data.id) _zwCurrentConvId = res.data.id
      window.__sidebarCache = null
    }
  })
}

function _updateZwConversation() {
  var token = uni.getStorageSync('xc_token') || ''
  if (!token || !_zwCurrentConvId) return
  uni.request({
    url: '/api/ziwei/conversations', method: 'POST',
    header: { 'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json' },
    data: JSON.stringify({ id: _zwCurrentConvId, messages: window._zwChatHistory }),
    success: function() { window.__sidebarCache = null }
  })
}

function _checkZwRestore() {
  var d = window.__xc_restoreData
  if (!d || d.type !== 'ziwei') return
  window.__xc_restoreData = null
  switchTab('ai')
  var messages = d.messages || []
  window._zwChatHistory = messages.slice()
  _zwCurrentConvId = d.id || null
  var html = ''
  messages.forEach(function(m) {
    if (m.role === 'user') {
      html += '<div class="chat-bubble-user">' + _escZwHtml(m.content) + '</div>'
    } else if (m.role === 'assistant') {
      html += '<div class="chat-bubble-ai"><div class="chat-bubble-content">' + _zwRenderCards(m.content) + '</div></div>'
    }
  })
  zwAiResult.value = html
  zwAiChatReady.value = true
  zwAiFollowUpQuestion.value = ''
}

function _escZwHtml(s) {
  if (!s || typeof s !== 'string') return ''
  var d = document.createElement('div')
  d.appendChild(document.createTextNode(s))
  return d.innerHTML
}

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
          window._zwChatHistory.push({ role: 'user', content: question || '紫微斗数AI解读' })
          window._zwChatHistory.push({ role: 'assistant', content: fullText })
          _zwCurrentConvId = null
          _saveZwConversation(question || '紫微斗数AI解读', { year: y, month: m, day: d, hour: h, minute: min, gender: gender, date_type: date_type, analysis_type: zwAnalysisTypes[zwAiForm.analysisTypeIdx].key })
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
  const token = uni.getStorageSync('xc_token') || ''
  
  window._zwChatHistory = window._zwChatHistory || []
  window._zwChatHistory.push({ role: 'user', content: question })
  
  const userBubble = '<div class="chat-bubble-user">' + question + '</div>'
  const aiBubbleId = 'zwFollow_' + Date.now()
  const aiBubble = '<div class="chat-bubble-ai" id="' + aiBubbleId + '"><div class="ai-stage"><img class="ai-stage-logo" src="/static/images/logo.webp?v=2">正在生成回复...</div><div class="ai-progress-bar"><div class="ai-progress-fill" style="width:60%"></div></div><div class="chat-bubble-content"></div></div>'
  
  zwAiResult.value = zwAiResult.value + userBubble + aiBubble
  
  fetch('/api/ziwei/ask/stream', {
    method: 'POST',
    headers: Object.assign({ 'Content-Type': 'application/json' }, token ? { 'Authorization': 'Bearer ' + token } : {}),
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
          var bubble = document.getElementById(aiBubbleId)
          if (bubble) {
            var contentEl = bubble.querySelector('.chat-bubble-content')
            if (contentEl) contentEl.innerHTML = _zwRenderCards(fullText)
          }
          _updateZwConversation()
          return
        }
        if (charQueue.length === 0) return
        var take = charQueue.length > 3 ? 2 : 1
        fullText += charQueue.substring(0, take)
        charQueue = charQueue.substring(take)
        var bubble = document.getElementById(aiBubbleId)
        if (bubble) {
          var contentEl = bubble.querySelector('.chat-bubble-content')
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
function zwEsc(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function zwBasicItem(label, value) {
  return '<div class="zw-basic-item"><span class="zw-basic-label">' + zwEsc(label) + '</span><span class="zw-basic-value">' + zwEsc(value || '') + '</span></div>'
}

function zwMutagenClass(mutagen) {
  if (!mutagen) return ''
  if (mutagen.includes('禄')) return 'zw-mutagen-lu'
  if (mutagen.includes('权')) return 'zw-mutagen-quan'
  if (mutagen.includes('科')) return 'zw-mutagen-ke'
  if (mutagen.includes('忌')) return 'zw-mutagen-ji'
  return ''
}

function zwStarHtml(star, cls) {
  if (!star || !star.name) return ''
  const brightness = star.brightness ? '<em>' + zwEsc(star.brightness) + '</em>' : ''
  const mutagen = star.mutagen ? '<b class="zw-mutagen ' + zwMutagenClass(star.mutagen) + '">' + zwEsc(star.mutagen) + '</b>' : ''
  return '<span class="' + cls + '">' + zwEsc(star.name) + brightness + mutagen + '</span>'
}

const zwGan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
const zwZhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
const zwLunarMonthNames = ['正月', '二月', '三月', '四月', '五月', '六月', '七月', '八月', '九月', '十月', '冬月', '腊月']
const zwMonthBranches = ['寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥', '子', '丑']

function zwGanzhiYear(year) {
  const offset = year - 1984
  return zwGan[((offset % 10) + 10) % 10] + zwZhi[((offset % 12) + 12) % 12]
}

function zwGanzhiMonth(year, month) {
  const yearStem = zwGanzhiYear(year).charAt(0)
  const startMap = { '甲': 2, '己': 2, '乙': 4, '庚': 4, '丙': 6, '辛': 6, '丁': 8, '壬': 8, '戊': 0, '癸': 0 }
  const stemIdx = ((startMap[yearStem] || 0) + month - 1) % 10
  return zwGan[stemIdx] + zwMonthBranches[month - 1]
}

function zwBirthYearFromPan(d) {
  const solar = (d.basic_info || {}).solar_date || ''
  const m = String(solar).match(/^(\d{4})/)
  return m ? parseInt(m[1]) : parseInt(zwForm.year)
}

function zwPalaceByAge(palaces, age) {
  return (palaces || []).find(function(p) { return (p.ages || []).includes(age) }) || null
}

function zwSelectedNominalAge(d) {
  const birthYear = zwBirthYearFromPan(d || zwPanData.value || {})
  return zwFlowState.selectedYear - birthYear + 1
}

function zwDecadeStartForYear(palaces, d, year) {
  const birthYear = zwBirthYearFromPan(d || zwPanData.value || {})
  const age = year - birthYear + 1
  const palace = (palaces || []).find(function(p) {
    const r = p && p.decadal && p.decadal.range
    return r && age >= r[0] && age <= r[1]
  })
  const range = palace && palace.decadal && palace.decadal.range
  return range ? range[0] : null
}

function zwFlowPeriods(palaces) {
  const periods = Object.assign({}, zwFlowState.horoscope || {})
  const nominalAge = zwSelectedNominalAge(zwPanData.value || {})
  const agePalace = zwPalaceByAge(palaces, nominalAge)
  if (agePalace) {
    periods.age = {
      name: '小限',
      index: agePalace.index,
      nominal_age: nominalAge,
      palace_name: agePalace.name
    }
  }
  const selectedAge = zwFlowState.selectedDecadeAge
  if (!selectedAge) return periods
  const palace = (palaces || []).find(function(p) {
    const r = p && p.decadal && p.decadal.range
    return r && r[0] === selectedAge
  })
  if (!palace || !palace.decadal) return periods
  periods.decadal = Object.assign({}, periods.decadal || {}, {
    name: '大限',
    index: palace.index,
    range: palace.decadal.range,
    heavenly_stem: palace.decadal.heavenly_stem || '',
    earthly_branch: palace.decadal.earthly_branch || '',
    ganzhi: (palace.decadal.heavenly_stem || '') + (palace.decadal.earthly_branch || '')
  })
  return periods
}

function zwFlowPeriodBadge(period, label, cls) {
  if (!period) return ''
  const suffix = period.ganzhi ? period.ganzhi : (period.nominal_age ? (period.nominal_age + '岁') : '')
  return '<span class="zw-flow-badge ' + cls + '">' + zwEsc(label) + (suffix ? ' ' + zwEsc(suffix) : '') + '</span>'
}

function zwPalaceCell(p, periods) {
  if (!p) return '<div class="zw-palace-cell"></div>'
  let cls = 'zw-palace-cell'
  let badge = ''
  if (p.is_body_palace) { cls += ' is-body'; badge += '<span class="zw-palace-badge zw-badge-body">身宫</span>' }
  if (p.name === '命宫') { cls += ' is-soul'; badge += '<span class="zw-palace-badge zw-badge-soul">命宫</span>' }
  const yearly = periods && periods.yearly
  const monthly = periods && periods.monthly
  const decadal = periods && periods.decadal
  const age = periods && periods.age
  const flowBadges = []
  if (decadal && decadal.index === p.index) { cls += ' is-flow-decadal'; flowBadges.push(zwFlowPeriodBadge(decadal, '大限', 'decadal')) }
  if (age && age.index === p.index) { cls += ' is-flow-age'; flowBadges.push(zwFlowPeriodBadge(age, '小限', 'age')) }
  if (yearly && yearly.index === p.index) { cls += ' is-flow-year'; flowBadges.push(zwFlowPeriodBadge(yearly, '流年', 'year')) }
  if (monthly && monthly.index === p.index) { cls += ' is-flow-month'; flowBadges.push(zwFlowPeriodBadge(monthly, '流月', 'month')) }
  const majorHtml = (p.major_stars || []).map(function(s) { return zwStarHtml(s, 'zw-star-major') }).join('')
  const minorHtml = (p.minor_stars || []).map(function(s) { return zwStarHtml(s, 'zw-star-minor') }).join('')
  const adjHtml = (p.adjective_stars || []).slice(0, 8).map(function(s) { return zwStarHtml(s, 'zw-star-adj') }).join('')
  const support = [p.changsheng12, p.boshi12, p.jiangqian12, p.suiqian12].filter(Boolean).map(zwEsc).join(' · ')
  const ages = (p.ages || []).slice(0, 8).join(',')
  let decHtml = ''
  if (p.decadal && p.decadal.range) {
    decHtml = '<div class="zw-palace-decadal"><span>大限</span>' + zwEsc(p.decadal.range[0]) + '-' + zwEsc(p.decadal.range[1]) + '岁 ' + zwEsc((p.decadal.heavenly_stem || '') + (p.decadal.earthly_branch || '')) + '</div>'
  }
  return '<div class="' + cls + '">' +
    badge +
    '<div class="zw-palace-header"><span class="zw-palace-name">' + zwEsc(p.name) + '</span><span class="zw-palace-ganzhi">' + zwEsc(p.ganzhi || ((p.heavenly_stem || '') + (p.earthly_branch || ''))) + '</span></div>' +
    '<div class="zw-palace-stars zw-palace-stars-major">' + majorHtml + '</div>' +
    '<div class="zw-palace-stars zw-palace-stars-minor">' + minorHtml + '</div>' +
    '<div class="zw-palace-stars zw-palace-stars-adj">' + adjHtml + '</div>' +
    (support ? '<div class="zw-palace-support">' + support + '</div>' : '') +
    (flowBadges.length ? '<div class="zw-palace-flow">' + flowBadges.join('') + '</div>' : '') +
    decHtml +
    (ages ? '<div class="zw-palace-ages">流年:' + zwEsc(ages) + '</div>' : '') +
    '</div>'
}

function zwCenterInfo(bi, cp, meta, periods) {
  const method = meta.chart_method || '三合盘'
  const modes = (meta.available_modes || ['三合', '四化']).map(function(m, idx) {
    return '<span class="zw-mode-chip ' + (idx === 0 ? 'active' : '') + '">' + zwEsc(m) + '</span>'
  }).join('')
  const coming = (meta.coming_modes || ['飞星', '飞化']).map(function(m) {
    return '<span class="zw-mode-chip muted">' + zwEsc(m) + '</span>'
  }).join('')
  const yearly = periods && periods.yearly
  const monthly = periods && periods.monthly
  const age = periods && periods.age
  const selectedMonthName = zwLunarMonthNames[zwFlowState.selectedMonth - 1] || (zwFlowState.selectedMonth + '月')
  const ageText = age ? ('小限 ' + zwEsc(age.nominal_age) + '岁 ' + zwEsc(age.palace_name || '')) : ('小限 ' + zwEsc(zwSelectedNominalAge(zwPanData.value || {})) + '岁')
  const flowLine = '<div class="zw-center-flow"><span>流年 ' + zwEsc(zwFlowState.selectedYear) + ' ' + zwEsc((yearly && yearly.ganzhi) || zwGanzhiYear(zwFlowState.selectedYear)) + '</span><span>' + ageText + '</span><span>流月 ' + zwEsc(selectedMonthName) + ' ' + zwEsc((monthly && monthly.ganzhi) || zwGanzhiMonth(zwFlowState.selectedYear, zwFlowState.selectedMonth)) + '</span></div>'
  const flowStatus = zwFlowState.error ? '<div class="zw-center-error">' + zwEsc(zwFlowState.error) + '</div>' : ''
  return '<div class="zw-center-info">' +
    '<div class="zw-center-kicker">' + zwEsc(method) + '</div>' +
    '<div class="zw-center-title">紫微斗数命盘</div>' +
    '<div class="zw-center-wuxing">' + zwEsc((meta.gender_yinyang || '') + ' · ' + (bi.five_elements_class || '')) + '</div>' +
    '<div class="zw-center-line"><span>北京时间</span><strong>' + zwEsc(meta.beijing_time || bi.solar_date || '') + '</strong></div>' +
    '<div class="zw-center-line"><span>真太阳时</span><strong>' + zwEsc(meta.true_solar_time || meta.beijing_time || '') + '</strong></div>' +
    '<div class="zw-center-line"><span>农历</span><strong>' + zwEsc(bi.lunar_date || '') + '</strong></div>' +
    '<div class="zw-center-line"><span>节气四柱</span><strong>' + zwEsc(bi.chinese_date || '') + '</strong></div>' +
    '<div class="zw-center-two"><span>命主 ' + zwEsc(cp.soul_star || '') + '</span><span>身主 ' + zwEsc(cp.body_star || '') + '</span></div>' +
    flowLine +
    flowStatus +
    '<div class="zw-center-modes">' + modes + coming + '</div>' +
    '</div>'
}

function zwTimeline(title, palaces, periods) {
  const decadal = periods && periods.decadal
  const items = (palaces || []).filter(function(p) { return p && p.decadal && p.decadal.range }).map(function(p) {
    const r = p.decadal.range || []
    const active = (zwFlowState.selectedDecadeAge ? r[0] === zwFlowState.selectedDecadeAge : (decadal && decadal.index === p.index)) ? ' active' : ''
    return '<span class="zw-flow-item zw-flow-clickable zw-flow-decade' + active + '" data-flow-decade="' + zwEsc(r[0]) + '"><b>' + zwEsc(r[0]) + '-' + zwEsc(r[1]) + '</b><em>' + zwEsc((p.decadal.heavenly_stem || '') + (p.decadal.earthly_branch || '')) + '</em><i>' + zwEsc(p.name || '') + '</i></span>'
  }).join('')
  return '<div class="zw-flow-row"><div class="zw-flow-title">' + zwEsc(title) + '</div><div class="zw-flow-scroll">' + items + '</div></div>'
}

function zwYearTimeline(palaces, d) {
  const birthYear = zwBirthYearFromPan(d)
  const currentYear = new Date().getFullYear()
  const selectedAge = zwFlowState.selectedDecadeAge || zwDecadeStartForYear(palaces, d, zwFlowState.selectedYear)
  const selectedStartYear = selectedAge ? birthYear + selectedAge - 1 : null
  const startYear = selectedStartYear || currentYear
  const years = Array.from({ length: 10 }, function(_, i) { return startYear + i })
  const items = years.map(function(year) {
    const age = year - birthYear + 1
    const p = zwPalaceByAge(palaces, age)
    const active = year === zwFlowState.selectedYear ? ' active' : ''
    return '<span class="zw-flow-item zw-flow-clickable compact' + active + '" data-flow-year="' + year + '"><b>' + year + '</b><em>' + zwEsc(zwGanzhiYear(year)) + '年</em><i>' + zwEsc(age + '岁 ' + (p ? p.name : '')) + '</i></span>'
  }).join('')
  return '<div class="zw-flow-row"><div class="zw-flow-title">流年</div><div class="zw-flow-scroll">' + items + '</div></div>'
}

function zwAgeTimeline(palaces, d) {
  const birthYear = zwBirthYearFromPan(d)
  const selectedAge = zwFlowState.selectedDecadeAge || zwDecadeStartForYear(palaces, d, zwFlowState.selectedYear)
  const startAge = selectedAge || Math.max(1, zwSelectedNominalAge(d) - 4)
  const ages = Array.from({ length: 10 }, function(_, i) { return startAge + i })
  const items = ages.map(function(age) {
    const year = birthYear + age - 1
    const p = zwPalaceByAge(palaces, age)
    const active = year === zwFlowState.selectedYear ? ' active' : ''
    return '<span class="zw-flow-item zw-flow-clickable zw-flow-age compact' + active + '" data-flow-year="' + year + '"><b>' + zwEsc(age) + '岁</b><em>' + zwEsc(year) + '</em><i>' + zwEsc(p ? p.name : '') + '</i></span>'
  }).join('')
  return '<div class="zw-flow-row"><div class="zw-flow-title">小限</div><div class="zw-flow-scroll">' + items + '</div></div>'
}

function zwMonthTimeline() {
  const items = zwLunarMonthNames.map(function(name, idx) {
    const month = idx + 1
    const active = month === zwFlowState.selectedMonth ? ' active' : ''
    return '<span class="zw-flow-item zw-flow-clickable zw-flow-month' + active + '" data-flow-month="' + month + '"><b>' + zwEsc(name) + '</b><em>' + zwEsc(zwGanzhiMonth(zwFlowState.selectedYear, month)) + '</em></span>'
  }).join('')
  return '<div class="zw-flow-row"><div class="zw-flow-title">流月</div><div class="zw-flow-scroll">' + items + '</div></div>'
}

function renderZiweiPan(d) {
  let html = '<div class="zw-result-wrap">'
  const bi = d.basic_info || {}
  const cp = d.core_palace || {}
  const meta = d.display_meta || {}
  const req = d.request || {}
  const palaces = d.twelve_palaces || []
  const periods = zwFlowPeriods(palaces)
  html += '<div class="zw-pro-header"><div><div class="zw-pro-title">' + zwEsc(req.question || meta.chart_name || '玄策专业盘') + '</div><div class="zw-pro-subtitle">' + zwEsc(meta.source_note || '基于本地算法排盘，结果供民俗文化参考。') + '</div></div><div class="zw-pro-pill">' + zwEsc(meta.time_rule || '按北京时间定时辰') + '</div></div>'
  html += '<div class="zw-basic-card zw-pro-basic"><div class="zw-basic-grid">'
  html += zwBasicItem('阳历', bi.solar_date)
  html += zwBasicItem('农历', bi.lunar_date)
  html += zwBasicItem('节气四柱', bi.chinese_date)
  html += zwBasicItem('时辰', (bi.shichen || '') + ' ' + (bi.shichen_range || ''))
  html += zwBasicItem('北京时间', meta.beijing_time)
  html += zwBasicItem('真太阳时', meta.true_solar_time)
  html += zwBasicItem('生肖', bi.zodiac)
  html += zwBasicItem('五行局', bi.five_elements_class)
  html += zwBasicItem('命主', cp.soul_star)
  html += zwBasicItem('身主', cp.body_star)
  html += '</div></div>'
  html += '<div class="zw-orientation zw-orientation-top">正南方</div>'
  html += '<div class="zw-palace-grid zw-pro-grid">'
  html += zwPalaceCell(palaces[4], periods)
  html += zwPalaceCell(palaces[3], periods)
  html += zwPalaceCell(palaces[5], periods)
  html += zwPalaceCell(palaces[6], periods)
  html += zwPalaceCell(palaces[2], periods)
  html += zwCenterInfo(bi, cp, meta, periods)
  html += zwPalaceCell(palaces[7], periods)
  html += zwPalaceCell(palaces[1], periods)
  html += zwPalaceCell(palaces[8], periods)
  html += zwPalaceCell(palaces[0], periods)
  html += zwPalaceCell(palaces[11], periods)
  html += zwPalaceCell(palaces[10], periods)
  html += zwPalaceCell(palaces[9], periods)
  html += '</div>'
  html += '<div class="zw-orientation zw-orientation-bottom">正北方</div>'
  html += zwTimeline('大限', palaces, periods)
  html += zwYearTimeline(palaces, d)
  html += zwAgeTimeline(palaces, d)
  html += zwMonthTimeline()
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
  uni.$on('xc-restore', _checkZwRestore)
  _checkZwRestore()
  window._xc_restoreZiwei = _checkZwRestore
  window.__xuanZiweiFlowClick = selectZiweiFlow
  document.addEventListener('click', handleZiweiDocumentClick)
  setInterval(function() {
    var rd = window.__xc_restoreData
    if (rd && rd.type === 'ziwei') _checkZwRestore()
  }, 500)
})

onUnmounted(function() {
  document.removeEventListener('click', handleZiweiDocumentClick)
  if (window.__xuanZiweiFlowClick === selectZiweiFlow) {
    delete window.__xuanZiweiFlowClick
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
.tool-container { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 32px; backdrop-filter: blur(20px); box-shadow: var(--card-shadow); max-width: 1180px; margin: 0 auto; }
.tool-tabs { display: flex; gap: 4px; margin-bottom: 28px; border-bottom: 1px solid var(--card-border); }
.tool-tab { padding: 12px 20px; border-radius: 10px 10px 0 0; font-size: 0.875rem; cursor: pointer; border: 1px solid transparent; border-bottom: none; color: var(--text-3); background: transparent; transition: all 0.2s; }
.tool-tab.active { color: var(--accent); background: var(--accent-glow); border-color: var(--accent); font-weight: 600; }
.tool-tab:hover { color: var(--accent); }
.tab-badge { font-size: 0.5625rem; padding: 1px 5px; border-radius: 4px; background: var(--accent); color: #fff; margin-left: 4px; }
.tab-badge.free { background: var(--success); }
.form-group { margin-bottom: 16px; }
.form-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 6px; letter-spacing: 1px; }
.form-input, .form-select-picker { width: 100%; padding: 10px 14px; border-radius: 10px; background: var(--input-bg); border: 1px solid var(--input-border); color: var(--text-1); font-size: 0.875rem; outline: none; box-sizing: border-box; }
.zw-form-grid .form-input .uni-input-wrapper { height: 22px; }
.zw-form-grid .form-input .uni-input-input { height: 22px !important; padding: 0 !important; margin: 0; border: none !important; background: transparent !important; font-size: inherit !important; color: inherit !important; line-height: 22px !important; }
.form-input-text { height: 48px !important; padding: 0 14px !important; display: flex !important; align-items: center !important; }
.form-input-text .uni-input-wrapper { width: 100%; height: auto; display: flex; align-items: center; }
.form-input-text .uni-input-input { height: auto !important; padding: 0 !important; margin: 0; border: none !important; background: transparent !important; font-size: 1rem !important; color: inherit !important; line-height: normal !important; }
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
.zw-pro-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 14px; padding: 14px 16px; border: 1px solid rgba(132,84,190,0.22); border-radius: 12px; background: linear-gradient(135deg, rgba(132,84,190,0.10), rgba(37,109,156,0.08)); }
.zw-pro-title { font-family: var(--font-serif); font-size: 1.05rem; font-weight: 700; color: var(--text-1); letter-spacing: 1px; }
.zw-pro-subtitle { margin-top: 4px; font-size: 0.74rem; line-height: 1.55; color: var(--text-3); }
.zw-pro-pill { flex: 0 0 auto; padding: 5px 9px; border-radius: 999px; background: rgba(108,92,231,0.16); color: #a48cff; border: 1px solid rgba(108,92,231,0.22); font-size: 0.7rem; white-space: nowrap; }
.zw-pro-basic { padding: 14px 16px; margin-bottom: 14px; }
.zw-basic-card { background: var(--bg-2); border: 1px solid var(--border); border-radius: 12px; padding: 20px; margin-bottom: 20px; }
.zw-basic-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 10px; }
.zw-basic-item { display: flex; flex-direction: column; gap: 2px; }
.zw-basic-label { font-size: 0.75rem; color: var(--text-4); letter-spacing: 1px; }
.zw-basic-value { font-size: 0.9375rem; font-weight: 600; color: var(--accent); }
.zw-orientation { text-align: center; color: var(--text-4); font-size: 0.72rem; letter-spacing: 4px; margin: 6px 0; }
.zw-palace-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 5px; margin-bottom: 12px; }
.zw-palace-cell { background: rgba(255,255,255,0.035); border: 1px solid var(--border); border-radius: 6px; padding: 7px; min-height: 158px; position: relative; transition: all 0.2s; cursor: default; overflow: hidden; }
.zw-palace-cell:hover { border-color: var(--accent); box-shadow: 0 0 20px rgba(212,168,71,0.08); }
.zw-palace-cell.is-soul { border-color: var(--accent); box-shadow: 0 0 16px rgba(212,168,71,0.12); }
.zw-palace-cell.is-body { border-color: var(--danger); }
.zw-palace-cell.is-flow-age { box-shadow: inset 0 0 0 1px rgba(39,174,96,0.52), 0 0 14px rgba(39,174,96,0.08); }
.zw-palace-cell.is-flow-year { border-color: rgba(212,168,71,0.62); background: rgba(212,168,71,0.06); }
.zw-palace-cell.is-flow-month { box-shadow: inset 0 0 0 1px rgba(45,156,219,0.55), 0 0 16px rgba(45,156,219,0.08); }
.zw-palace-header { display: flex; justify-content: space-between; align-items: center; gap: 4px; margin-bottom: 4px; padding-right: 28px; }
.zw-palace-name { font-size: 0.86rem; font-weight: 800; color: #d85f67; white-space: nowrap; }
.zw-palace-ganzhi { font-size: 0.72rem; color: var(--text-3); white-space: nowrap; }
.zw-palace-badge { font-size: 0.56rem; padding: 1px 4px; border-radius: 3px; position: absolute; top: 5px; right: 5px; }
.zw-badge-soul { background: rgba(212,168,71,0.15); color: var(--accent); }
.zw-badge-body { background: rgba(231,76,60,0.12); color: var(--danger); }
.zw-palace-stars { margin-top: 3px; display: flex; flex-wrap: wrap; gap: 2px 4px; align-items: flex-start; }
.zw-star-major { display: inline-flex; align-items: center; gap: 1px; color: #6f62e8; font-size: 0.82rem; font-weight: 800; line-height: 1.2; }
.zw-star-minor { display: inline-flex; align-items: center; gap: 1px; color: #2b89c9; font-size: 0.72rem; font-weight: 700; line-height: 1.25; }
.zw-star-adj { display: inline-flex; align-items: center; color: var(--text-2); font-size: 0.66rem; line-height: 1.25; }
.zw-star-major em, .zw-star-minor em, .zw-star-adj em { font-style: normal; color: var(--text-4); font-size: 0.6rem; margin-left: 1px; }
.zw-mutagen { display: inline-flex; min-width: 14px; height: 14px; align-items: center; justify-content: center; font-size: 0.58rem; padding: 0 3px; border-radius: 3px; margin-left: 1px; font-weight: 800; }
.zw-mutagen-lu { background: rgba(39,174,96,0.15); color: #27ae60; }
.zw-mutagen-quan { background: rgba(231,76,60,0.12); color: #e74c3c; }
.zw-mutagen-ke { background: rgba(52,152,219,0.12); color: #3498db; }
.zw-mutagen-ji { background: rgba(142,68,173,0.12); color: #8e44ad; }
.zw-palace-support { margin-top: 4px; color: var(--text-4); font-size: 0.61rem; line-height: 1.35; }
.zw-palace-flow { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
.zw-flow-badge { display: inline-flex; align-items: center; border-radius: 4px; padding: 1px 4px; font-size: 0.56rem; font-weight: 800; line-height: 1.25; }
.zw-flow-badge.decadal { background: rgba(132,84,190,0.14); color: #a48cff; }
.zw-flow-badge.age { background: rgba(39,174,96,0.14); color: #27ae60; }
.zw-flow-badge.year { background: rgba(212,168,71,0.14); color: var(--accent); }
.zw-flow-badge.month { background: rgba(45,156,219,0.14); color: #2d9cdb; }
.zw-palace-decadal { margin-top: 5px; font-size: 0.65rem; color: var(--text-3); border-top: 1px solid var(--border); padding-top: 4px; line-height: 1.3; }
.zw-palace-decadal span { color: var(--accent); margin-right: 4px; font-weight: 700; }
.zw-palace-ages { margin-top: 2px; color: var(--text-4); font-size: 0.58rem; line-height: 1.25; }
.zw-center-info { grid-column: 2 / 4; grid-row: 2 / 4; background: linear-gradient(180deg, rgba(255,255,255,0.055), rgba(108,92,231,0.055)); border: 1.5px solid rgba(108,92,231,0.32); border-radius: 6px; padding: 14px; display: flex; flex-direction: column; align-items: stretch; justify-content: center; text-align: center; min-height: 318px; }
.zw-center-kicker { font-size: 0.72rem; color: #8d7cff; font-weight: 700; }
.zw-center-title { font-family: var(--font-serif); font-size: 1.25rem; color: var(--text-1); font-weight: 800; letter-spacing: 2px; margin: 4px 0; }
.zw-center-wuxing { font-size: 0.92rem; color: #7f6df2; font-weight: 800; margin-bottom: 8px; }
.zw-center-line { display: grid; grid-template-columns: 64px minmax(0,1fr); gap: 6px; align-items: baseline; text-align: left; margin: 2px 0; font-size: 0.72rem; color: var(--text-4); }
.zw-center-line strong { color: var(--text-2); font-size: 0.76rem; font-weight: 700; word-break: break-word; }
.zw-center-two { display: flex; justify-content: center; gap: 8px; margin: 8px 0 6px; color: var(--text-2); font-size: 0.75rem; font-weight: 700; }
.zw-center-flow { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 5px; margin: 5px 0 6px; }
.zw-center-flow span { padding: 4px 5px; border-radius: 6px; background: rgba(255,255,255,0.055); border: 1px solid var(--border); color: var(--text-2); font-size: 0.66rem; font-weight: 800; }
.zw-center-error { margin: 2px auto 4px; font-size: 0.62rem; }
.zw-center-error { color: var(--danger); }
.zw-center-modes { display: flex; gap: 4px; justify-content: center; flex-wrap: wrap; margin-top: 4px; }
.zw-mode-chip { padding: 3px 7px; border-radius: 999px; background: rgba(255,255,255,0.06); color: var(--text-3); font-size: 0.65rem; border: 1px solid var(--border); }
.zw-mode-chip.active { background: rgba(108,92,231,0.18); border-color: rgba(108,92,231,0.32); color: #a48cff; font-weight: 800; }
.zw-mode-chip.muted { opacity: 0.55; }
.zw-flow-row { display: grid; grid-template-columns: 54px minmax(0,1fr); gap: 8px; align-items: stretch; margin-top: 8px; }
.zw-flow-title { display: flex; align-items: center; justify-content: center; border-radius: 8px; background: rgba(108,92,231,0.16); color: #a48cff; font-weight: 800; font-size: 0.78rem; }
.zw-flow-scroll { display: flex; overflow-x: auto; gap: 4px; padding-bottom: 2px; }
.zw-flow-item { flex: 0 0 76px; min-height: 46px; border: 1px solid var(--border); border-radius: 8px; background: rgba(255,255,255,0.035); padding: 5px 6px; text-align: center; box-sizing: border-box; }
.zw-flow-clickable { cursor: pointer; transition: border-color 0.15s, background 0.15s, transform 0.15s; }
.zw-flow-clickable:hover { border-color: rgba(212,168,71,0.55); transform: translateY(-1px); }
.zw-flow-item.active { border-color: var(--accent); background: rgba(212,168,71,0.13); box-shadow: 0 0 0 1px rgba(212,168,71,0.08); }
.zw-flow-age.active { border-color: #27ae60; background: rgba(39,174,96,0.13); }
.zw-flow-month.active { border-color: #2d9cdb; background: rgba(45,156,219,0.13); }
.zw-flow-item b, .zw-flow-item em, .zw-flow-item i { display: block; font-style: normal; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.zw-flow-item b { color: var(--text-1); font-size: 0.72rem; }
.zw-flow-item em { color: #7f6df2; font-size: 0.72rem; font-weight: 800; }
.zw-flow-item i { color: var(--text-4); font-size: 0.62rem; }
.zw-flow-item.compact { flex-basis: 72px; }
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
.zw-result :deep(.zw-palace-cell.is-flow-age) { box-shadow: inset 0 0 0 1px rgba(39,174,96,0.52), 0 0 14px rgba(39,174,96,0.08); }
.zw-result :deep(.zw-palace-cell.is-flow-year) { border-color: rgba(212,168,71,0.62); background: rgba(212,168,71,0.06); }
.zw-result :deep(.zw-palace-cell.is-flow-month) { box-shadow: inset 0 0 0 1px rgba(45,156,219,0.55), 0 0 16px rgba(45,156,219,0.08); }
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
.zw-result :deep(.zw-pro-header) { display: flex; align-items: flex-start; justify-content: space-between; gap: 14px; margin-bottom: 14px; padding: 14px 16px; border: 1px solid rgba(132,84,190,0.22); border-radius: 12px; background: linear-gradient(135deg, rgba(132,84,190,0.10), rgba(37,109,156,0.08)); }
.zw-result :deep(.zw-pro-title) { font-family: var(--font-serif); font-size: 1.05rem; font-weight: 700; color: var(--text-1); letter-spacing: 1px; }
.zw-result :deep(.zw-pro-subtitle) { margin-top: 4px; font-size: 0.74rem; line-height: 1.55; color: var(--text-3); }
.zw-result :deep(.zw-pro-pill) { flex: 0 0 auto; padding: 5px 9px; border-radius: 999px; background: rgba(108,92,231,0.16); color: #a48cff; border: 1px solid rgba(108,92,231,0.22); font-size: 0.7rem; white-space: nowrap; }
.zw-result :deep(.zw-pro-basic) { padding: 14px 16px; margin-bottom: 14px; }
.zw-result :deep(.zw-orientation) { text-align: center; color: var(--text-4); font-size: 0.72rem; letter-spacing: 4px; margin: 6px 0; }
.zw-result :deep(.zw-pro-grid) { grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 5px; margin-bottom: 12px; }
.zw-result :deep(.zw-pro-grid .zw-palace-cell) { background: rgba(255,255,255,0.035); border-radius: 6px; padding: 7px; min-height: 158px; overflow: hidden; }
.zw-result :deep(.zw-pro-grid .zw-palace-header) { gap: 4px; margin-bottom: 4px; padding-right: 28px; }
.zw-result :deep(.zw-pro-grid .zw-palace-name) { font-size: 0.86rem; font-weight: 800; color: #d85f67; white-space: nowrap; }
.zw-result :deep(.zw-pro-grid .zw-palace-ganzhi) { font-size: 0.72rem; color: var(--text-3); white-space: nowrap; }
.zw-result :deep(.zw-pro-grid .zw-palace-badge) { font-size: 0.56rem; padding: 1px 4px; border-radius: 3px; }
.zw-result :deep(.zw-pro-grid .zw-palace-stars) { margin-top: 3px; display: flex; flex-wrap: wrap; gap: 2px 4px; align-items: flex-start; }
.zw-result :deep(.zw-pro-grid .zw-star-major) { display: inline-flex; align-items: center; gap: 1px; padding: 0; background: transparent; color: #6f62e8; border-radius: 0; font-size: 0.82rem; font-weight: 800; line-height: 1.2; }
.zw-result :deep(.zw-pro-grid .zw-star-minor) { display: inline-flex; align-items: center; gap: 1px; padding: 0; background: transparent; color: #2b89c9; border-radius: 0; font-size: 0.72rem; font-weight: 700; line-height: 1.25; }
.zw-result :deep(.zw-pro-grid .zw-star-adj) { display: inline-flex; align-items: center; padding: 0; color: var(--text-2); font-size: 0.66rem; line-height: 1.25; }
.zw-result :deep(.zw-pro-grid .zw-star-major em), .zw-result :deep(.zw-pro-grid .zw-star-minor em), .zw-result :deep(.zw-pro-grid .zw-star-adj em) { font-style: normal; color: var(--text-4); font-size: 0.6rem; margin-left: 1px; }
.zw-result :deep(.zw-pro-grid .zw-mutagen) { display: inline-flex; min-width: 14px; height: 14px; align-items: center; justify-content: center; font-size: 0.58rem; padding: 0 3px; border-radius: 3px; margin-left: 1px; font-weight: 800; }
.zw-result :deep(.zw-palace-support) { margin-top: 4px; color: var(--text-4); font-size: 0.61rem; line-height: 1.35; }
.zw-result :deep(.zw-palace-flow) { display: flex; flex-wrap: wrap; gap: 3px; margin-top: 4px; }
.zw-result :deep(.zw-flow-badge) { display: inline-flex; align-items: center; border-radius: 4px; padding: 1px 4px; font-size: 0.56rem; font-weight: 800; line-height: 1.25; }
.zw-result :deep(.zw-flow-badge.decadal) { background: rgba(132,84,190,0.14); color: #a48cff; }
.zw-result :deep(.zw-flow-badge.age) { background: rgba(39,174,96,0.14); color: #27ae60; }
.zw-result :deep(.zw-flow-badge.year) { background: rgba(212,168,71,0.14); color: var(--accent); }
.zw-result :deep(.zw-flow-badge.month) { background: rgba(45,156,219,0.14); color: #2d9cdb; }
.zw-result :deep(.zw-pro-grid .zw-palace-decadal) { margin-top: 5px; font-size: 0.65rem; color: var(--text-3); border-top: 1px solid var(--border); padding-top: 4px; line-height: 1.3; }
.zw-result :deep(.zw-pro-grid .zw-palace-decadal span) { color: var(--accent); margin-right: 4px; font-weight: 700; }
.zw-result :deep(.zw-palace-ages) { margin-top: 2px; color: var(--text-4); font-size: 0.58rem; line-height: 1.25; }
.zw-result :deep(.zw-pro-grid .zw-center-info) { background: linear-gradient(180deg, rgba(255,255,255,0.055), rgba(108,92,231,0.055)); border: 1.5px solid rgba(108,92,231,0.32); border-radius: 6px; padding: 14px; align-items: stretch; min-height: 318px; }
.zw-result :deep(.zw-center-kicker) { font-size: 0.72rem; color: #8d7cff; font-weight: 700; }
.zw-result :deep(.zw-pro-grid .zw-center-title) { font-family: var(--font-serif); font-size: 1.25rem; color: var(--text-1); font-weight: 800; letter-spacing: 2px; margin: 4px 0; }
.zw-result :deep(.zw-pro-grid .zw-center-wuxing) { font-size: 0.92rem; color: #7f6df2; font-weight: 800; margin-bottom: 8px; }
.zw-result :deep(.zw-center-line) { display: grid; grid-template-columns: 64px minmax(0,1fr); gap: 6px; align-items: baseline; text-align: left; margin: 2px 0; font-size: 0.72rem; color: var(--text-4); }
.zw-result :deep(.zw-center-line strong) { color: var(--text-2); font-size: 0.76rem; font-weight: 700; word-break: break-word; }
.zw-result :deep(.zw-center-two) { display: flex; justify-content: center; gap: 8px; margin: 8px 0 6px; color: var(--text-2); font-size: 0.75rem; font-weight: 700; }
.zw-result :deep(.zw-center-flow) { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 5px; margin: 5px 0 6px; }
.zw-result :deep(.zw-center-flow span) { padding: 4px 5px; border-radius: 6px; background: rgba(255,255,255,0.055); border: 1px solid var(--border); color: var(--text-2); font-size: 0.66rem; font-weight: 800; }
.zw-result :deep(.zw-center-error) { margin: 2px auto 4px; font-size: 0.62rem; }
.zw-result :deep(.zw-center-error) { color: var(--danger); }
.zw-result :deep(.zw-center-modes) { display: flex; gap: 4px; justify-content: center; flex-wrap: wrap; margin-top: 4px; }
.zw-result :deep(.zw-mode-chip) { padding: 3px 7px; border-radius: 999px; background: rgba(255,255,255,0.06); color: var(--text-3); font-size: 0.65rem; border: 1px solid var(--border); }
.zw-result :deep(.zw-mode-chip.active) { background: rgba(108,92,231,0.18); border-color: rgba(108,92,231,0.32); color: #a48cff; font-weight: 800; }
.zw-result :deep(.zw-mode-chip.muted) { opacity: 0.55; }
.zw-result :deep(.zw-flow-row) { display: grid; grid-template-columns: 54px minmax(0,1fr); gap: 8px; align-items: stretch; margin-top: 8px; }
.zw-result :deep(.zw-flow-title) { display: flex; align-items: center; justify-content: center; border-radius: 8px; background: rgba(108,92,231,0.16); color: #a48cff; font-weight: 800; font-size: 0.78rem; }
.zw-result :deep(.zw-flow-scroll) { display: flex; overflow-x: auto; gap: 4px; padding-bottom: 2px; }
.zw-result :deep(.zw-flow-item) { flex: 0 0 76px; min-height: 46px; border: 1px solid var(--border); border-radius: 8px; background: rgba(255,255,255,0.035); padding: 5px 6px; text-align: center; box-sizing: border-box; }
.zw-result :deep(.zw-flow-clickable) { cursor: pointer; transition: border-color 0.15s, background 0.15s, transform 0.15s; }
.zw-result :deep(.zw-flow-clickable:hover) { border-color: rgba(212,168,71,0.55); transform: translateY(-1px); }
.zw-result :deep(.zw-flow-item.active) { border-color: var(--accent); background: rgba(212,168,71,0.13); box-shadow: 0 0 0 1px rgba(212,168,71,0.08); }
.zw-result :deep(.zw-flow-age.active) { border-color: #27ae60; background: rgba(39,174,96,0.13); }
.zw-result :deep(.zw-flow-month.active) { border-color: #2d9cdb; background: rgba(45,156,219,0.13); }
.zw-result :deep(.zw-flow-item b), .zw-result :deep(.zw-flow-item em), .zw-result :deep(.zw-flow-item i) { display: block; font-style: normal; line-height: 1.25; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.zw-result :deep(.zw-flow-item b) { color: var(--text-1); font-size: 0.72rem; }
.zw-result :deep(.zw-flow-item em) { color: #7f6df2; font-size: 0.72rem; font-weight: 800; }
.zw-result :deep(.zw-flow-item i) { color: var(--text-4); font-size: 0.62rem; }
.zw-result :deep(.zw-flow-item.compact) { flex-basis: 72px; }

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
  .zw-result :deep(.zw-pro-header) { flex-direction: column; gap: 8px; padding: 12px; }
  .zw-result :deep(.zw-pro-pill) { align-self: flex-start; white-space: normal; }
  .zw-result :deep(.zw-pro-grid) { gap: 2px; }
  .zw-result :deep(.zw-pro-grid .zw-palace-cell) { min-height: 108px; padding: 4px; border-radius: 4px; }
  .zw-result :deep(.zw-pro-grid .zw-palace-header) { padding-right: 18px; margin-bottom: 2px; gap: 2px; }
  .zw-result :deep(.zw-pro-grid .zw-palace-name) { font-size: 0.63rem; }
  .zw-result :deep(.zw-pro-grid .zw-palace-ganzhi) { font-size: 0.48rem; }
  .zw-result :deep(.zw-pro-grid .zw-palace-badge) { font-size: 0.42rem; padding: 0 2px; top: 3px; right: 3px; }
  .zw-result :deep(.zw-pro-grid .zw-star-major) { font-size: 0.56rem; }
  .zw-result :deep(.zw-pro-grid .zw-star-minor) { font-size: 0.5rem; }
  .zw-result :deep(.zw-pro-grid .zw-star-adj) { font-size: 0.46rem; }
  .zw-result :deep(.zw-pro-grid .zw-star-major em), .zw-result :deep(.zw-pro-grid .zw-star-minor em), .zw-result :deep(.zw-pro-grid .zw-star-adj em) { font-size: 0.42rem; }
  .zw-result :deep(.zw-pro-grid .zw-mutagen) { min-width: 10px; height: 10px; font-size: 0.42rem; padding: 0 1px; }
  .zw-result :deep(.zw-palace-support) { font-size: 0.43rem; line-height: 1.2; margin-top: 2px; }
  .zw-result :deep(.zw-pro-grid .zw-palace-decadal) { font-size: 0.44rem; margin-top: 2px; padding-top: 2px; }
  .zw-result :deep(.zw-palace-ages) { font-size: 0.4rem; }
  .zw-result :deep(.zw-pro-grid .zw-center-info) { min-height: 218px; padding: 6px; border-radius: 4px; }
  .zw-result :deep(.zw-center-kicker) { font-size: 0.48rem; }
  .zw-result :deep(.zw-pro-grid .zw-center-title) { font-size: 0.72rem; letter-spacing: 1px; margin: 2px 0; }
  .zw-result :deep(.zw-pro-grid .zw-center-wuxing) { font-size: 0.58rem; margin-bottom: 4px; }
  .zw-result :deep(.zw-center-line) { grid-template-columns: 40px minmax(0,1fr); gap: 3px; font-size: 0.45rem; margin: 1px 0; }
  .zw-result :deep(.zw-center-line strong) { font-size: 0.47rem; }
  .zw-result :deep(.zw-center-two) { gap: 4px; margin: 4px 0 3px; font-size: 0.48rem; }
  .zw-result :deep(.zw-center-flow) { gap: 3px; margin: 3px 0; }
  .zw-result :deep(.zw-center-flow span) { font-size: 0.43rem; padding: 2px 3px; }
  .zw-result :deep(.zw-center-error) { font-size: 0.42rem; margin: 1px auto 2px; }
  .zw-result :deep(.zw-flow-badge) { font-size: 0.38rem; padding: 0 2px; }
  .zw-result :deep(.zw-palace-flow) { gap: 2px; margin-top: 2px; }
  .zw-result :deep(.zw-mode-chip) { font-size: 0.45rem; padding: 2px 4px; }
  .zw-result :deep(.zw-flow-row) { grid-template-columns: 40px minmax(0,1fr); gap: 5px; }
  .zw-result :deep(.zw-flow-item) { flex-basis: 62px; min-height: 40px; padding: 4px; }
  .zw-result :deep(.zw-flow-title) { font-size: 0.64rem; }
  .zw-result :deep(.zw-flow-item b), .zw-result :deep(.zw-flow-item em) { font-size: 0.6rem; }
  .zw-result :deep(.zw-flow-item i) { font-size: 0.52rem; }
}
</style>
