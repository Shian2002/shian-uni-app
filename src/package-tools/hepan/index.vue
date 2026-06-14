<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :isLoggedIn="isLoggedIn" @toggle-theme="toggleTheme" />

    <!-- 合盘表单 -->
    <view class="page">
      <!-- 第一人 -->
      <view class="person-card">
        <view class="person-title">👤 第一人</view>
        <view class="form-row">
          <view class="form-group">
            <text class="form-label">姓名</text>
            <view id="hepanName1-wrap" class="dom-input-wrap"></view>
          </view>
          <view class="form-group">
            <text class="form-label">性别</text>
            <picker :range="['男', '女']" :value="gender1Idx" @change="gender1Idx = $event.detail.value">
              <view class="form-select-picker">{{ ['男', '女'][gender1Idx] }}</view>
            </picker>
          </view>
        </view>
        <view class="form-row">
          <view class="form-group">
            <text class="form-label">出生日期</text>
            <picker mode="date" :value="birth1Date" @change="onBirth1DateChange">
              <view class="form-select-picker">{{ birth1Date || '选择日期' }}</view>
            </picker>
          </view>
          <view class="form-group">
            <text class="form-label">出生时间</text>
            <picker mode="time" :value="birth1Time" @change="onBirth1TimeChange">
              <view class="form-select-picker">{{ birth1Time || '选择时间' }}</view>
            </picker>
          </view>
        </view>
        <view class="form-row">
          <view class="form-group">
            <text class="form-label">出生地</text>
            <view id="hepanAddr1-wrap" class="dom-input-wrap"></view>
          </view>
        </view>
      </view>

      <!-- 第二人 -->
      <view class="person-card">
        <view class="person-title">👤 第二人</view>
        <view class="form-row">
          <view class="form-group">
            <text class="form-label">姓名</text>
            <view id="hepanName2-wrap" class="dom-input-wrap"></view>
          </view>
          <view class="form-group">
            <text class="form-label">性别</text>
            <picker :range="['女', '男']" :value="gender2Idx" @change="gender2Idx = $event.detail.value">
              <view class="form-select-picker">{{ ['女', '男'][gender2Idx] }}</view>
            </picker>
          </view>
        </view>
        <view class="form-row">
          <view class="form-group">
            <text class="form-label">出生日期</text>
            <picker mode="date" :value="birth2Date" @change="onBirth2DateChange">
              <view class="form-select-picker">{{ birth2Date || '选择日期' }}</view>
            </picker>
          </view>
          <view class="form-group">
            <text class="form-label">出生时间</text>
            <picker mode="time" :value="birth2Time" @change="onBirth2TimeChange">
              <view class="form-select-picker">{{ birth2Time || '选择时间' }}</view>
            </picker>
          </view>
        </view>
        <view class="form-row">
          <view class="form-group">
            <text class="form-label">出生地</text>
            <view id="hepanAddr2-wrap" class="dom-input-wrap"></view>
          </view>
        </view>
      </view>

      <!-- 合盘按钮 -->
      <view class="btn-row">
        <view class="btn-primary" :class="{ disabled: hepanLoading }" @tap="doHepan">
          {{ hepanLoading ? '计算中...' : '💑 开始合盘' }}
        </view>
      </view>

      <!-- 结果区域 -->
      <view class="result-area" v-if="resultHtml" v-html="resultHtml"></view>
    </view>


  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import TopNav from '@/components/TopNav.vue'

// ═══ 主题 ═══
const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
function toggleTheme() { theme.value = theme.value === 'dark' ? 'light' : 'dark'; uni.setStorageSync('xc_theme', theme.value) }

// ═══ 登录/注册 ═══
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

// ═══ 合盘表单 ═══
const name1 = ref(''); const gender1Idx = ref(0); const birth1Date = ref(''); const birth1Time = ref(''); const addr1 = ref('')
const name2 = ref(''); const gender2Idx = ref(0); const birth2Date = ref(''); const birth2Time = ref(''); const addr2 = ref('')
const hepanLoading = ref(false)
const resultHtml = ref('')

// 回放标记
let hepanIsReplay = false

function onBirth1DateChange(e) { birth1Date.value = e.detail.value }
function onBirth1TimeChange(e) { birth1Time.value = e.detail.value }
function onBirth2DateChange(e) { birth2Date.value = e.detail.value }
function onBirth2TimeChange(e) { birth2Time.value = e.detail.value }

// 格式化出生时间为后端格式: 200008011200
function fmtBirth(dateStr, timeStr) {
  if (!dateStr) return ''
  const d = dateStr.replace(/-/g, '')
  const t = (timeStr || '00:00').replace(/:/g, '')
  return (d + t).substring(0, 12)
}

// 五行颜色
function wxColor(wx) {
  const m = { '金': '#FFD700', '木': '#4CAF50', '水': '#4A90D9', '火': '#FF6347', '土': '#A0522D' }
  return m[wx] || 'var(--text-2)'
}

function relationLabelHepan(desc) {
  const raw = String(desc || '').replace(/\s+/g, '')
  const charSource = raw.replace(/缺[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]+/g, '')
  const chars = charSource.match(/[甲乙丙丁戊己庚辛壬癸子丑寅卯辰巳午未申酉戌亥]/g) || []
  const pairText = chars.slice(0, 2).join('')
  const allText = chars.join('')
  const hePairOrder = ['甲己', '乙庚', '丙辛', '丁壬', '戊癸']
  const relationPairOrder = ['辰丑', '酉戌', '辰卯', '午卯', '巳亥', '辰戌', '丑戌']
  const orderedPair = (orders) => chars.length >= 2 && chars[0] !== chars[1] ? (orders.find(item => item.includes(chars[0]) && item.includes(chars[1])) || pairText) : pairText
  const hePairText = orderedPair(hePairOrder)
  const relationPairText = orderedPair(relationPairOrder)
  const juMap = { 子: '水局', 午: '火局', 卯: '木局', 酉: '金局' }
  const huiSets = [
    { zhis: '寅卯辰', ju: '木局' },
    { zhis: '巳午未', ju: '火局' },
    { zhis: '申酉戌', ju: '金局' },
    { zhis: '亥子丑', ju: '水局' },
  ]
  let m = raw.match(/合化([木火土金水])/)
  if (m && pairText) return `${hePairText}合化${m[1]}`
  if (/六合|相合/.test(raw) && pairText) return `${relationPairText}合`
  if (raw.includes('相冲') && pairText) return `${relationPairText}冲`
  if (raw.includes('相破') && pairText) return `${relationPairText}破`
  if (raw.includes('自刑') && pairText) return `${relationPairText}自刑`
  if (/无恩之刑|恃势之刑|无礼之刑/.test(raw) && allText) return `${allText}三刑`
  if (raw.includes('相刑') && pairText) return `${relationPairText}${chars[0] === chars[1] ? '自刑' : '刑'}`
  if (raw.includes('相害') && pairText) return `${relationPairText}害`
  if (raw.includes('相克') && pairText) return `${pairText}克`
  m = raw.match(/拱合([子午卯酉])/)
  if (m && pairText) return `${pairText}拱合${juMap[m[1]] || m[1]}`
  if (raw.includes('拱会') && pairText) {
    const found = huiSets.find(item => chars.slice(0, 2).every(zhi => item.zhis.includes(zhi)))
    return `${pairText}拱会${found ? found.ju : ''}`
  }
  m = raw.match(/半合([木火金水])局/)
  if (m && pairText) return `${pairText}半合${m[1]}局`
  m = raw.match(/三合([木火金水])局/)
  if (m && allText) return `${allText}三合${m[1]}局`
  m = raw.match(/三会([木火金水])局/)
  if (m && raw.includes('缺') && pairText) return `${pairText}拱会${m[1]}局`
  if (m && allText) return `${allText}三会${m[1]}局`
  if (raw.includes('暗合') && pairText) return `${relationPairText}暗合`
  for (const suffix of ['冲', '害', '破', '合', '克']) {
    if (raw.endsWith(suffix) && pairText) return `${relationPairText}${suffix}`
  }
  return raw.replace(/相/g, '')
}

// ═══ 渲染合盘结果 ═══
function renderHepanResult(d) {
  const p1 = d.person1, p2 = d.person2
  const n1 = p1.name || '甲方', n2 = p2.name || '乙方'
  const score = d.score
  let scoreColor = score >= 80 ? '#2E8B57' : score >= 60 ? '#DAA520' : '#DC143C'

  let html = ''

  // 评分
  html += `<div class="score-ring">
    <div class="score-value" style="color:${scoreColor};">${score}</div>
    <div class="score-label">合盘评分（满分100）</div>
  </div>`

  // 基本信息对比
  html += `<div class="summary-card">
    <div style="display:flex;justify-content:space-between;align-items:center;">
      <div style="text-align:center;flex:1;">
        <div style="font-size:1.1rem;font-weight:600;color:var(--accent);">${n1}</div>
        <div style="font-size:0.8rem;color:var(--text-2);margin-top:4px;">${p1.birth || ''}</div>
        <div style="font-size:1.4rem;margin-top:6px;">${['year','month','day','hour'].map(p=>(p1.four_pillars?.[p]||{}).gan+(p1.four_pillars?.[p]||{}).zhi).join(' ')}</div>
        ${p1.lack_wuxing && p1.lack_wuxing.length ? `<div style="font-size:0.75rem;color:var(--danger);margin-top:4px;">缺${p1.lack_wuxing.join('')}</div>` : ''}
      </div>
      <div style="font-size:1.5rem;color:var(--accent);">💑</div>
      <div style="text-align:center;flex:1;">
        <div style="font-size:1.1rem;font-weight:600;color:var(--accent);">${n2}</div>
        <div style="font-size:0.8rem;color:var(--text-2);margin-top:4px;">${p2.birth || ''}</div>
        <div style="font-size:1.4rem;margin-top:6px;">${['year','month','day','hour'].map(p=>(p2.four_pillars?.[p]||{}).gan+(p2.four_pillars?.[p]||{}).zhi).join(' ')}</div>
        ${p2.lack_wuxing && p2.lack_wuxing.length ? `<div style="font-size:0.75rem;color:var(--danger);margin-top:4px;">缺${p2.lack_wuxing.join('')}</div>` : ''}
      </div>
    </div>
  </div>`

  // 日主关系
  if (d.day_relation && d.day_relation.length) {
    html += `<div class="compare-section">
      <div class="compare-title">☀️ 日主关系</div>
      <div class="day-relation">
        ${d.day_relation.map(r => `<span class="day-relation-item">${r}</span>`).join('')}
      </div>
    </div>`
  }

  // 柱位对比
  if (d.pillar_compare && d.pillar_compare.length) {
    html += `<div class="compare-section">
      <div class="compare-title">📊 柱位对比</div>`
    for (const pc of d.pillar_compare) {
      const relsHtml = (pc.relations || []).map(r =>
        `<span class="rel-tag ${r.positive ? 'positive' : 'negative'}">${relationLabelHepan(r.desc)}</span>`
      ).join('') || '<span style="color:var(--text-3);font-size:0.75rem;">无特殊关系</span>'
      html += `<div class="pillar-row">
        <span class="pillar-label">${pc.label}</span>
        <span class="pillar-gz" style="color:var(--info);">${pc.person1}</span>
        <span class="pillar-arrow">⇄</span>
        <span class="pillar-gz" style="color:var(--success);">${pc.person2}</span>
        <span class="pillar-rels">${relsHtml}</span>
      </div>`
    }
    html += `</div>`
  }

  // 五行互补
  if (d.wx_complement) {
    html += `<div class="compare-section">
      <div class="compare-title">🔄 五行互补</div>
      <view class="wx-table-wrap">
        <view class="wx-table-header">
          <text class="wx-th">五行</text><text class="wx-th">${n1}</text><text class="wx-th">${n2}</text><text class="wx-th">合计</text><text class="wx-th">状态</text>
        </view>
        <view class="wx-table-body">`
    for (const [wx, info] of Object.entries(d.wx_complement)) {
      html += `<view class="wx-table-row">
        <text class="wx-td" style="color:${wxColor(wx)};font-weight:600;">${wx}</text>
        <text class="wx-td">${info.person1}</text>
        <text class="wx-td">${info.person2}</text>
        <text class="wx-td">${info.total}</text>
        <text class="wx-td"><text class="wx-status ${info.status}">${info.status}</text></text>
      </view>`
    }
    html += `</view></view></div>`
  }

  // 综合分析
  if (d.pillar_compare) {
    const heCount = d.pillar_compare.reduce((s, pc) => s + (pc.relations || []).filter(r => r.positive).length, 0)
    const chongCount = d.pillar_compare.reduce((s, pc) => s + (pc.relations || []).filter(r => !r.positive).length, 0)
    const complementCount = d.wx_complement ? Object.values(d.wx_complement).filter(v => v.status === '互补').length : 0
    const lackCount = d.wx_complement ? Object.values(d.wx_complement).filter(v => v.status === '双缺').length : 0

    let summary = ''
    if (score >= 80) {
      summary = `${n1}与${n2}八字相合度很高！四柱干支有${heCount}处相合关系，五行有${complementCount}处互补，命理上属于良配。双方能互相助力，感情和谐。`
    } else if (score >= 60) {
      summary = `${n1}与${n2}八字合盘中规中矩。有${heCount}处相合、${chongCount}处相冲，五行有${complementCount}处互补。整体尚可，需在相处中多包容理解。`
    } else {
      summary = `${n1}与${n2}八字冲合较多，四柱有${chongCount}处冲害关系，五行有${lackCount}处双缺。命理上需注意磨合，但命盘只是参考，关键在双方用心经营。`
    }

    html += `<div class="compare-section">
      <div class="compare-title">📜 综合分析</div>
      <div class="summary-card">
        <div class="summary-text">${summary}</div>
      </div>
    </div>`
  }

  // 免责声明
  html += `<div style="text-align:center;margin:20px 0;font-size:0.72rem;color:var(--text-3);">
    ⚠️ 八字合盘仅供传统文化研究参考，不构成任何决策建议
  </div>`

  resultHtml.value = html
}

// ═══ 合盘请求 ═══
async function doHepan() {
  const bt1 = fmtBirth(birth1Date.value, birth1Time.value)
  const bt2 = fmtBirth(birth2Date.value, birth2Time.value)

  if (!bt1 || bt1.length < 10) { uni.showToast({ title: '请输入第一人出生日期', icon: 'none' }); return }
  if (!bt2 || bt2.length < 10) { uni.showToast({ title: '请输入第二人出生日期', icon: 'none' }); return }

  hepanLoading.value = true
  resultHtml.value = '<div class="loading">合盘计算中...</div>'

  try {
    const res = await uni.request({
      url: '/api/bazi/hepan',
      method: 'POST',
      data: {
        person1: {
          name: (document.getElementById('hepanName1')?.value || '').trim(),
          gender: ['男', '女'][gender1Idx.value],
          birthTime: bt1,
          calType: '公历',
          birthAddr: (document.getElementById('hepanAddr1')?.value || '').trim()
        },
        person2: {
          name: (document.getElementById('hepanName2')?.value || '').trim(),
          gender: ['女', '男'][gender2Idx.value],
          birthTime: bt2,
          calType: '公历',
          birthAddr: (document.getElementById('hepanAddr2')?.value || '').trim()
        },
        _replay: hepanIsReplay
      }
    })
    const data = res.data
    if (data && data.success) {
      renderHepanResult(data)
    } else {
      resultHtml.value = `<div class="loading">❌ ${data?.error || '合盘失败'}</div>`
    }
  } catch (e) {
    resultHtml.value = `<div class="loading">❌ 请求失败: ${e.message || e.errMsg || '请稍后重试'}</div>`
  } finally {
    hepanLoading.value = false
    hepanIsReplay = false
  }
}

// ═══ 页面加载 ═══
onMounted(() => {
  // 创建原生DOM输入框（绕过uni-app input包装层）
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
  createNativeInput('hepanName1', 'text', '选填')
  createNativeInput('hepanAddr1', 'text', '选填，如北京')
  createNativeInput('hepanName2', 'text', '选填')
  createNativeInput('hepanAddr2', 'text', '选填，如上海')

  // 检查是否有来自记录跳转的合盘参数
  // #ifdef H5
  try {
    const stored = sessionStorage.getItem('xc_hepan_params')
    if (stored) {
      sessionStorage.removeItem('xc_hepan_params')
      const params = JSON.parse(stored)
      if (params.person1 && params.person2) {
        hepanIsReplay = !!params._replay
        // 填充表单
        const p1 = params.person1, p2 = params.person2
        name1.value = p1.name || ''
        gender1Idx.value = p1.gender === '女' ? 1 : 0
        addr1.value = p1.birthAddr || ''
        if (p1.birthTime && p1.birthTime.length >= 12) {
          const bt = p1.birthTime
          birth1Date.value = bt.slice(0, 4) + '-' + bt.slice(4, 6) + '-' + bt.slice(6, 8)
          birth1Time.value = bt.slice(8, 10) + ':' + bt.slice(10, 12)
        }
        name2.value = p2.name || ''
        gender2Idx.value = p2.gender === '男' ? 1 : 0
        addr2.value = p2.birthAddr || ''
        // 同步到原生DOM输入框
        var n1 = document.getElementById('hepanName1'); if (n1) n1.value = p1.name || ''
        var a1 = document.getElementById('hepanAddr1'); if (a1) a1.value = p1.birthAddr || ''
        var n2 = document.getElementById('hepanName2'); if (n2) n2.value = p2.name || ''
        var a2 = document.getElementById('hepanAddr2'); if (a2) a2.value = p2.birthAddr || ''
        if (p2.birthTime && p2.birthTime.length >= 12) {
          const bt = p2.birthTime
          birth2Date.value = bt.slice(0, 4) + '-' + bt.slice(4, 6) + '-' + bt.slice(6, 8)
          birth2Time.value = bt.slice(8, 10) + ':' + bt.slice(10, 12)
        }
        // 自动触发合盘
        setTimeout(() => doHepan(), 300)
      }
    }
  } catch (e) {}
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

/* 按钮（弹窗用） */
.btn { padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; border: none; display: inline-block; text-align: center; }
.btn-outline { background: transparent; border: 1px solid var(--card-border); color: var(--text-2); }
.btn-accent { background: var(--accent); color: #fff; }
.btn-sm { padding: 5px 12px; font-size: 0.75rem; }

/* 合盘页面样式 */
.page { max-width: 800px; margin: 0 auto; padding: 16px; position: relative; z-index: 1; }
.person-card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 16px; margin-bottom: 16px; backdrop-filter: blur(20px); }
.person-title { font-size: 0.9rem; color: var(--accent); margin-bottom: 12px; font-weight: 600; font-family: var(--font-serif); letter-spacing: 1px; }
.form-row { display: flex; gap: 10px; margin-bottom: 10px; flex-wrap: wrap; }
.form-group { flex: 1; min-width: 120px; }
.form-label { display: block; font-size: 0.75rem; color: var(--text-3); margin-bottom: 4px; letter-spacing: 1px; }
.form-input, .form-select-picker { width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid var(--input-border); background: var(--input-bg); color: var(--text-1); font-size: 0.85rem; outline: none; box-sizing: border-box; }
.btn-row { text-align: center; margin: 24px 0; }
.btn-primary { display: inline-block; padding: 12px 40px; border-radius: 10px; border: none; background: linear-gradient(135deg, var(--accent), var(--accent-2)); color: #fff; font-size: 1rem; font-weight: 600; cursor: pointer; letter-spacing: 2px; transition: opacity 0.2s, transform 0.2s; }
.btn-primary:active { opacity: 0.9; transform: translateY(-1px); }
.btn-primary.disabled { opacity: 0.5; cursor: not-allowed; transform: none; }

/* 结果区域 */
.result-area { display: block; margin-top: 24px; }
.loading { text-align: center; padding: 40px; color: var(--text-2); }
.score-ring { text-align: center; margin: 20px 0; }
.score-value { font-size: 3rem; font-weight: 700; }
.score-label { font-size: 0.85rem; color: var(--text-2); }
.compare-section { margin: 20px 0; }
.compare-title { font-size: 1rem; color: var(--accent); margin-bottom: 12px; font-weight: 600; border-left: 3px solid var(--accent); padding-left: 10px; }
.pillar-row { display: flex; align-items: center; gap: 8px; padding: 10px 12px; margin-bottom: 6px; background: var(--section-alt); border-radius: 8px; border: 1px solid var(--card-border); }
.pillar-label { width: 40px; font-size: 0.8rem; color: var(--text-3); }
.pillar-gz { width: 50px; text-align: center; font-size: 1rem; font-weight: 600; }
.pillar-arrow { color: var(--text-3); font-size: 0.8rem; }
.pillar-rels { flex: 1; display: flex; flex-wrap: wrap; gap: 4px; }
.rel-tag { padding: 2px 8px; border-radius: 4px; font-size: 0.72rem; }
.rel-tag.positive { background: rgba(46,139,87,0.15); color: #2E8B57; }
.rel-tag.negative { background: rgba(220,20,60,0.15); color: #DC143C; }
.wx-table-wrap { border: 1px solid var(--card-border); border-radius: 8px; overflow: hidden; }
.wx-table-header { display: flex; background: var(--section-alt); border-bottom: 1px solid var(--card-border); }
.wx-th { flex: 1; padding: 8px 10px; text-align: center; font-size: 0.82rem; color: var(--accent); font-weight: 600; }
.wx-table-body { }
.wx-table-row { display: flex; border-bottom: 1px solid var(--card-border); }
.wx-table-row:last-child { border-bottom: none; }
.wx-td { flex: 1; padding: 8px 10px; text-align: center; font-size: 0.82rem; color: var(--text-2); }
.wx-status { font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; }
.wx-status.互补 { background: rgba(46,139,87,0.15); color: #2E8B57; }
.wx-status.双缺 { background: rgba(220,20,60,0.15); color: #DC143C; }
.wx-status.偏旺 { background: rgba(218,165,32,0.15); color: #DAA520; }
.wx-status.均衡 { color: var(--text-3); }
.day-relation { padding: 12px; background: var(--section-alt); border-radius: 8px; margin: 10px 0; border: 1px solid var(--card-border); }
.day-relation-item { display: inline-block; padding: 4px 10px; margin: 4px; border-radius: 6px; font-size: 0.82rem; background: rgba(212,168,70,0.1); color: var(--accent); }
.summary-card { background: var(--section-alt); border: 1px solid var(--card-border); border-radius: 12px; padding: 16px; margin: 16px 0; }
.summary-text { font-size: 0.88rem; color: var(--text-2); line-height: 1.8; }

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
}
@media (max-width: 600px) {
  .form-row { flex-direction: column; }
  .form-group { min-width: auto; }
}
</style>
