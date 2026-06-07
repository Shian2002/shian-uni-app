<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :isLoggedIn="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- 页面头部 -->
      <section class="tool-hero">
        <view class="tool-hero-content">
          <view class="section-tag">择吉工具</view>
          <view class="tool-hero-title">择吉工具 · 婚嫁搬家开业 · 吉日吉时</view>
          <view class="tool-hero-desc">择吉分析工具 · 传统民俗参考</view>
        </view>
      </section>

      <!-- 工具面板 -->
      <section class="section">
        <view class="tool-container">
          <view class="card">
            <view class="card-header"><text class="ch-icon">🎊</text><text class="ch-title">择吉事项</text></view>
            <view class="card-body">
              <view class="form-group">
                <text class="form-label">择吉事项</text>
                <select id="zejiType" class="wz-datetime-select"></select>
              </view>
              <view class="form-row-2col">
                <view class="form-group">
                  <text class="form-label">开始日期</text>
                  <view class="wz-datetime-row">
                    <view class="wz-dt-col"><select id="zejiStartYear" class="wz-datetime-select"></select></view>
                    <view class="wz-dt-col"><select id="zejiStartMonth" class="wz-datetime-select"></select></view>
                    <view class="wz-dt-col"><select id="zejiStartDay" class="wz-datetime-select"></select></view>
                  </view>
                </view>
                <view class="form-group">
                  <text class="form-label">结束日期</text>
                  <view class="wz-datetime-row">
                    <view class="wz-dt-col"><select id="zejiEndYear" class="wz-datetime-select"></select></view>
                    <view class="wz-dt-col"><select id="zejiEndMonth" class="wz-datetime-select"></select></view>
                    <view class="wz-dt-col"><select id="zejiEndDay" class="wz-datetime-select"></select></view>
                  </view>
                </view>
              </view>
              <view class="form-group">
                <text class="form-label">出生地（选填）</text>
                <view id="zejiAddr-wrap" class="dom-input-wrap"></view>
              </view>
              <view class="btn-row">
                <view class="zeji-submit" @tap="zejiStartFn">🎊 择吉分析</view>
                <view class="zeji-clear" @tap="zejiClear">清空</view>
              </view>
            </view>
          </view>

          <!-- 结果区域（DOM直操作，绕开Vue 3.4.21 render effect bug） -->
          <view class="result-section" id="zejiResultSection" style="display:none;">
            <view class="card">
              <view class="card-header"><text class="ch-icon">📜</text><text class="ch-title">择吉结果</text></view>
              <view class="card-body">
                <view class="result-area" id="zejiResultContent"></view>
              </view>
            </view>
          </view>

          <view class="compliance-notice">⚠️ 以上内容仅为民俗文化参考，不构成任何决策建议</view>
        </view>
      </section>
    </view>



  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import TopNav from '@/components/TopNav.vue'

// ── 主题 ──
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

// ── 登录状态 ──
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

// ── 择吉表单 ──
const zejiTypes = ['婚嫁', '开业', '搬家', '出行', '签约', '动土']
const zejiTypeIdx = ref(0)
const zejiStart = ref('')
const zejiEnd = ref('')
const zejiAddr = ref('')

// 填充select辅助函数（绕过uni-app编译器吞掉<option>的bug）
function fillZejiSelect(id, options, selectedVal, onChange) {
  var el = document.getElementById(id)
  if (!el) return
  el.innerHTML = ''
  for (var i = 0; i < options.length; i++) {
    var opt = document.createElement('option')
    var item = options[i]
    if (typeof item === 'object') { opt.value = item.value; opt.text = item.label }
    else { opt.value = item; opt.text = String(item) }
    if (String(opt.value) === String(selectedVal)) opt.selected = true
    el.appendChild(opt)
  }
  if (onChange) el.addEventListener('change', function(e) { onChange(e.target.value) })
}

async function zejiStartFn() {
  // 从原生DOM读取值
  var typeEl = document.getElementById('zejiType')
  var syEl = document.getElementById('zejiStartYear')
  var smEl = document.getElementById('zejiStartMonth')
  var sdEl = document.getElementById('zejiStartDay')
  var eyEl = document.getElementById('zejiEndYear')
  var emEl = document.getElementById('zejiEndMonth')
  var edEl = document.getElementById('zejiEndDay')

  var typeVal = typeEl ? typeEl.value : zejiTypes[zejiTypeIdx.value]
  var startStr = syEl && smEl && sdEl ? syEl.value + '-' + String(smEl.value).padStart(2,'0') + '-' + String(sdEl.value).padStart(2,'0') : zejiStart.value
  var endStr = eyEl && emEl && edEl ? eyEl.value + '-' + String(emEl.value).padStart(2,'0') + '-' + String(edEl.value).padStart(2,'0') : zejiEnd.value

  if (!startStr) { uni.showToast({ title: '请选择开始日期', icon: 'none' }); return }

  var params = {
    zejiType: typeVal,
    startDate: startStr,
    endDate: endStr || startStr,
    addr: (document.getElementById('zejiAddr')?.value || '').trim(),
    name: '择吉分析'
  }

  // DOM直操作显示loading和结果（绕开Vue 3.4.21 render effect bug）
  var section = document.getElementById('zejiResultSection')
  var content = document.getElementById('zejiResultContent')
  if (section) section.style.display = 'block'
  if (content) content.textContent = '正在分析吉日吉时，请稍候...'

  try {
    const res = await uni.request({ url: '/api/zeji', method: 'POST', data: params })
    const d = res.data
    if (!d || d.error) {
      if (content) content.textContent = d.error || '分析失败，请重试'
    } else {
      if (content) content.textContent = d.result || d.message || '分析完成'
    }
  } catch (e) {
    if (content) content.textContent = '分析失败，请重试'
  }
}

function zejiClear() {
  zejiStart.value = ''; zejiEnd.value = ''
  var section = document.getElementById('zejiResultSection')
  if (section) section.style.display = 'none'
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

// 创建原生DOM输入框 + 填充select（绕过Vue 3.4.21 picker/render effect bug）
onMounted(() => {
  // #ifdef H5
  var now = new Date()
  var curYear = now.getFullYear()

  // 择吉事项 select
  var typeOpts = zejiTypes.map(function(t) { return { value: t, label: t } })
  fillZejiSelect('zejiType', typeOpts, zejiTypes[0], function(v) { zejiTypeIdx.value = zejiTypes.indexOf(v) })

  // 年选项 (当前年 ±5年)
  var yearOpts = []
  for (var y = curYear - 1; y <= curYear + 5; y++) { yearOpts.push({ value: y, label: y + '年' }) }
  fillZejiSelect('zejiStartYear', yearOpts, curYear)
  fillZejiSelect('zejiEndYear', yearOpts, curYear)

  // 月选项
  var monthOpts = []
  for (var m = 1; m <= 12; m++) { monthOpts.push({ value: m, label: m + '月' }) }
  fillZejiSelect('zejiStartMonth', monthOpts, now.getMonth() + 1)
  fillZejiSelect('zejiEndMonth', monthOpts, now.getMonth() + 1)

  // 日选项
  var dayOpts = []
  for (var d = 1; d <= 31; d++) { dayOpts.push({ value: d, label: d + '日' }) }
  fillZejiSelect('zejiStartDay', dayOpts, now.getDate())
  fillZejiSelect('zejiEndDay', dayOpts, now.getDate())

  // 创建地址输入框
  var wrap = document.getElementById('zejiAddr-wrap')
  if (wrap) {
    var inp = document.createElement('input')
    inp.type = 'text'
    inp.id = 'zejiAddr'
    inp.placeholder = '如：北京'
    inp.style.cssText = 'width:100%;padding:10px 14px;border-radius:10px;background:var(--input-bg);border:1px solid var(--input-border);color:var(--text-1);font-size:0.875rem;outline:none;box-sizing:border-box;transition:border-color 0.2s,box-shadow 0.2s'
    inp.onfocus = function() { this.style.borderColor = 'var(--accent)'; this.style.boxShadow = '0 0 0 2px var(--accent-glow)' }
    inp.onblur = function() { this.style.borderColor = 'var(--input-border)'; this.style.boxShadow = 'none' }
    inp.setAttribute('maxlength', '100')
    wrap.appendChild(inp)
  }
  // #endif
})
</script>

<style scoped>
/* ═══ 变量体系 ═══ */
:root { --ease: cubic-bezier(0.4, 0, 0.2, 1); --radius-md: 14px; --radius-lg: 20px; --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif; --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; --max-w: 1280px; }
[data-theme="dark"] { --bg-grad-1: #161a2a; --bg-grad-2: #1a1e30; --bg-grad-3: #141824; --accent: hsl(38, 60%, 60%); --accent-2: hsl(38, 60%, 48%); --accent-glow: hsla(38, 60%, 60%, 0.10); --card-bg: rgba(48, 53, 76, 0.85); --card-border: rgba(255,255,255,0.12); --card-border-hover: rgba(255,255,255,0.18); --card-shadow: 0 16px 48px rgba(0,0,0,0.35); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --danger: rgba(215,125,110,0.88); --success: rgba(110,195,135,0.88); --nav-bg: rgba(22, 26, 42, 0.92); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --bg-grad-1: #f7f2ea; --bg-grad-2: #f0ebe1; --bg-grad-3: #f9f5f0; --accent: hsl(38, 72%, 30%); --accent-2: hsl(38, 72%, 22%); --accent-glow: hsla(38, 72%, 30%, 0.065); --card-bg: rgba(255,253,248,0.68); --card-border: rgba(0,0,0,0.045); --card-border-hover: rgba(0,0,0,0.08); --card-shadow: 0 8px 28px rgba(60,40,15,0.055); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --danger: rgba(170,65,50,0.88); --success: rgba(30,130,60,0.88); --nav-bg: rgba(247,242,234,0.95); --section-alt: rgba(240,235,225,0.45); }

.page-root { min-height: 100vh; }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, var(--bg-grad-1), var(--bg-grad-2) 50%, var(--bg-grad-3)); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, var(--bg-grad-1), var(--bg-grad-2) 60%, var(--bg-grad-3)); }
.page-wrap { position: relative; z-index: 1; }

/* Hero */
.section { max-width: var(--max-w); margin: 0 auto; padding: 16px 32px 32px; }
.section-tag { display: inline-block; padding: 3px 12px; border-radius: 20px; font-size: 0.66rem; letter-spacing: 1.5px; color: var(--accent); background: var(--accent-glow); margin-bottom: 8px; }
.tool-hero { padding: 28px 32px 14px; text-align: center; position: relative; overflow: hidden; }
.tool-hero::before { content: ''; position: absolute; top: -50%; left: -20%; width: 140%; height: 200%; background: radial-gradient(ellipse at center, var(--accent-glow) 0%, transparent 70%); opacity: 0.5; pointer-events: none; }
.tool-hero-content { position: relative; z-index: 1; max-width: var(--max-w); margin: 0 auto; text-align: center; }
.tool-hero-title { font-family: var(--font-serif); font-size: 1.48rem; font-weight: 400; letter-spacing: 3px; color: var(--text-1); margin-bottom: 6px; }
.tool-hero-desc { font-size: 0.82rem; color: var(--text-3); letter-spacing: 1.5px; }

/* 容器 */
.tool-container { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 22px; backdrop-filter: blur(20px); box-shadow: var(--card-shadow); max-width: 720px; margin: 0 auto; }

/* 卡片 */
.card { background: var(--input-bg); border: 1px solid var(--card-border); border-radius: var(--radius-md); overflow: hidden; }
.card-header { display: flex; align-items: center; gap: 10px; padding: 12px 16px; border-bottom: 1px solid var(--card-border); background: var(--accent-glow); }
.ch-icon { font-size: 1.1rem; }
.ch-title { font-size: 0.9375rem; font-weight: 600; color: var(--text-1); letter-spacing: 1px; }
.card-body { padding: 16px; }

/* 表单 */
.form-group { margin-bottom: 10px; }
.form-label { display: block; font-size: 0.8125rem; font-weight: 600; color: var(--text-2); margin-bottom: 6px; letter-spacing: 1px; }
.form-input { width: 100%; padding: 9px 12px; border: 1.5px solid var(--card-border); border-radius: 10px; font-size: 0.85rem; background: var(--card-bg); color: var(--text-1); outline: none; box-sizing: border-box; }
.picker-display { line-height: 1.4; cursor: pointer; text-align: center; }
.form-select-picker { padding: 9px 12px; border: 1.5px solid var(--card-border); border-radius: 10px; font-size: 0.85rem; background: var(--card-bg); color: var(--text-1); text-align: center; }
.form-row-2col { display: flex; gap: 12px; margin-bottom: 14px; }
.form-row-2col .form-group { flex: 1; margin-bottom: 0; }

/* 日期时间行（复用bazi页面样式） */
.wz-datetime-row { display: flex; gap: 8px; align-items: center; justify-content: space-between; }
.wz-dt-col { flex: 1; min-width: 0; position: relative; }
.wz-datetime-select { width: 100%; padding: 9px 6px; border: 1.5px solid var(--card-border); border-radius: 8px; font-size: 0.85rem; font-weight: 500; background: var(--card-bg); color: var(--text-1); cursor: pointer; text-align: center; appearance: none; -webkit-appearance: none; -moz-appearance: none; outline: none; box-sizing: border-box; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='10' height='10' viewBox='0 0 10 10'%3E%3Cpath d='M5 7L1 3h8z' fill='%23999'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 4px center; padding-right: 16px; }
.wz-datetime-select:focus { border-color: var(--accent); }
.wz-dt-suffix { position: absolute; right: -2px; top: 50%; transform: translateY(-50%); font-size: 0.7rem; color: var(--text-3); pointer-events: none; }

/* 按钮 */
.btn-row { display: flex; gap: 10px; align-items: center; justify-content: center; margin-top: 14px; }
.zeji-submit { padding: 12px 28px; border-radius: 30px; font-size: 0.9375rem; font-weight: 600; background: hsl(35, 38%, 52%); color: #fff; text-align: center; cursor: pointer; line-height: 1; display: flex; align-items: center; justify-content: center; }
.zeji-clear { padding: 12px 18px; border-radius: 20px; font-size: 0.8125rem; font-weight: 400; border: 1px solid var(--card-border); color: var(--text-3); text-align: center; cursor: pointer; background: transparent; white-space: nowrap; line-height: 1; display: flex; align-items: center; justify-content: center; }

/* 结果 */
.result-section { margin-top: 20px; }
.result-area { font-size: 0.875rem; color: var(--text-2); white-space: pre-wrap; line-height: 1.8; }
.compliance-notice { margin-top: 16px; padding: 10px 14px; border-radius: 8px; font-size: 0.75rem; color: var(--text-3); background: rgba(170,160,145,0.06); text-align: center; }

/* 弹窗 */
.modal-overlay { display: none; position: fixed; inset: 0; z-index: 300; background: rgba(0,0,0,0.5); align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal-box { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: var(--radius-lg); padding: 28px; width: 90%; max-width: 400px; }
.modal-title { font-size: 1.125rem; font-weight: 600; color: var(--text-1); margin-bottom: 20px; text-align: center; }
.field { margin-bottom: 12px; }
.field-label { display: block; font-size: 0.8125rem; color: var(--text-2); margin-bottom: 4px; }
.field-input { width: 100%; padding: 8px 12px; border: 1px solid var(--card-border); border-radius: 8px; font-size: 0.875rem; background: var(--input-bg); color: var(--text-1); box-sizing: border-box; }
.modal-error { font-size: 0.8125rem; color: var(--danger); text-align: center; margin: 8px 0; min-height: 1.2em; }
.modal-btns { display: flex; gap: 10px; justify-content: center; margin-top: 16px; }

/* 响应式 */
@media (max-width: 768px) {
  .tool-hero { padding: 28px 16px 16px; }
  .tool-hero-title { font-size: 1.5rem; }
  .tool-container { padding: 20px 16px; }
  .section { padding: 24px 16px 36px; }
  .card-header { padding: 9px 14px; }
  .card-body { padding: 12px; }
  .form-group { margin-bottom: 8px; }
  .form-label { font-size: 0.72rem; margin-bottom: 4px; }
  .form-row-2col { flex-direction: column; gap: 8px; margin-bottom: 8px; }
  .form-row-2col .form-group { margin-bottom: 0; }
  .wz-datetime-row { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 6px; }
  .wz-datetime-select,
  .form-input { min-height: 34px; padding-top: 6px; padding-bottom: 6px; font-size: 0.76rem; }
  .btn-row { margin-top: 8px; gap: 8px; }
  .zeji-submit { flex: 1; padding: 10px 14px; font-size: 0.84rem; }
  .zeji-clear { flex: 0 0 76px; padding: 10px 12px; font-size: 0.74rem; }
  .compliance-notice { margin-top: 8px; padding: 7px 10px; font-size: 0.66rem; line-height: 1.35; }

}
</style>
