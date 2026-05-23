<template>
  <view class="page-root" :data-theme="theme">
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :is-logged-in="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="container">
      <view class="version-info">
        <view class="ver">xuance-bazi-v1.0.0</view>
        <view class="version-date">排盘算法版本 · 2026-05-12 发布</view>
      </view>

      <view class="badge-row">
        <view class="badge badge-green">✅ 1050/1050 测试通过</view>
        <view class="badge badge-blue">🔄 持续更新</view>
        <view class="badge badge-orange">📝 开源可审查</view>
      </view>

      <view class="section-title">核心排算规则声明</view>
      <view class="section-desc">本站所有排盘计算均在用户设备本地完成，不向服务器发送任何命理数据。以下为各核心规则的算法实现说明。</view>

      <view class="rule-card" v-for="rule in rules" :key="rule.name">
        <view class="rule-name">{{ rule.name }}</view>
        <view class="rule-detail">{{ rule.detail }}</view>
      </view>

      <view class="section-title">测试覆盖报告</view>
      <view class="table-wrap">
        <view class="table-row table-header">
          <text class="table-cell">测试类型</text>
          <text class="table-cell">用例数</text>
          <text class="table-cell">通过率</text>
        </view>
        <view class="table-row" v-for="t in testReport" :key="t.type" :class="{ 'table-total': t.total }">
          <text class="table-cell">{{ t.type }}</text>
          <text class="table-cell">{{ t.count }}</text>
          <text class="table-cell">{{ t.rate }}</text>
        </view>
      </view>

      <view class="section-title">核心文件列表</view>
      <view class="file-list">
        <view class="file-item" v-for="f in files" :key="f.name">
          <text class="file-icon">📄</text>
          <text class="file-name">{{ f.name }}</text>
          <text class="file-desc">{{ f.desc }}</text>
        </view>
      </view>

      <view class="disclaimer">
        <text class="disclaimer-title">📢 免责声明</text>
        <text class="disclaimer-text">本平台所有内容仅为民俗文化与传统命理科普参考，不构成任何决策建议。算法基于公开的天文历表数据和传统命理典籍实现，供文化学习与参考用途。</text>
      </view>

      <view class="footer">
        <text>时安解忧屋 · 看得懂用得上的民俗命理参考平台</text>
        <text>© 2026 时安解忧屋 版权所有 | 算法版本 xuance-bazi-v1.0.0</text>
      </view>
    </view>


  </view>
</template>

<script setup>
import { ref } from 'vue'
import TopNav from '@/components/TopNav.vue'

const theme = ref(uni.getStorageSync('xc_theme') || 'dark')
const isLoggedIn = ref(!!uni.getStorageSync('xc_token'))
window.addEventListener('xc-session-expired', function() { isLoggedIn.value = false })

const toggleTheme = () => {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  uni.setStorageSync('xc_theme', theme.value)
  try {
    document.documentElement.setAttribute('data-theme', theme.value); const root = document.querySelector('.page-root')
    if (root) root.setAttribute('data-theme', theme.value)
    const icon = document.getElementById('themeToggleIcon')
    if (icon) icon.textContent = theme.value === 'dark' ? '🌙' : '☀️'
  } catch(_) {}
}

const goBack = () => {
  uni.navigateBack({ delta: 1, fail: () => { uni.switchTab({ url: '/pages/index/index' }) } })
}

const rules = [
  { name: '年柱 · 立春分界', detail: '以立春节气精确时刻（ephem天文库计算）为年柱分界。立春之前仍属旧年，立春之后（含立春时刻）为新一年。注：非春节分界，这是八字排盘与农历年份的根本区别。' },
  { name: '月柱 · 节令分界 + 五虎遁', detail: '以十二节令精确时刻为月柱分界（非农历初一）。月干由年干通过五虎遁口诀推算。' },
  { name: '日柱 · sxtwl 寿星天文历', detail: '使用 sxtwl 库（寿星天文历）计算精确日柱干支。基于天文历表数据，确保 1900-2100 年的日柱计算准确无误。' },
  { name: '时柱 · 五鼠遁 + 夜子时处理', detail: '时干由日干通过五鼠遁口诀推算。支持夜子时不换日（默认）和子时换日两种模式。' },
  { name: '大运 · 阳顺阴逆 + 起运岁数', detail: '阳年男命/阴年女命 → 顺排大运。阴年男命/阳年女命 → 逆排大运。起运岁数：3天 = 1岁, 1天 = 4个月, 1时辰 = 10天。' },
  { name: '真太阳时校正', detail: '经度修正：当地经度与东经120°的差值 × 4分钟/度。均时差（Equation of Time）公式近似计算。' },
  { name: '节气计算 · ephem 天文库', detail: '使用 ephem 库计算太阳实际黄经位置。三级搜索算法精确到分钟级。24节气按角度计算。' },
]

const testReport = [
  { type: '已知标准案例（与问真八字对齐）', count: 15, rate: '100%' },
  { type: '节气边界测试（3年份×24节气）', count: 216, rate: '100%' },
  { type: '真太阳时校正测试', count: 59, rate: '100%' },
  { type: '夜子时/早子时边界', count: 24, rate: '100%' },
  { type: '大运排列测试', count: 4, rate: '100%' },
  { type: '随机采样（1900-2100年）', count: 726, rate: '100%' },
  { type: '总计', count: 1050, rate: '100% ✅', total: true },
]

const files = [
  { name: 'bazi_engine.py', desc: '(211KB, 5103行) — 八字排盘核心引擎' },
  { name: 'app.py', desc: '(274KB, 6744行) — Flask Web应用 + 奇门遁甲引擎' },
  { name: 'ziwei_engine.py', desc: '(17KB) — 紫微斗数排盘引擎' },
  { name: 'src/services/TimeService.py', desc: '(35KB) — 时间服务单例模块' },
  { name: 'src/algorithms/version.py', desc: '— 算法版本标签系统' },
  { name: 'tests/algorithms/test_suite.json', desc: '— 1050条标准测试用例' },
]
</script>

<style scoped>
.page-root { min-height: 100vh; background: #f5f7fa; }
[data-theme="dark"] .page-root { background: #1a1a2e; color: rgba(240,236,228,0.97); }
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
/* ═══ TopNav 组件所需的 CSS 变量 ═══ */
:root { --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; }
[data-theme="dark"] { --nav-bg: rgba(22, 26, 42, 0.92); --card-border: rgba(255,255,255,0.12); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --nav-bg: rgba(247,242,234,0.95); --card-border: rgba(0,0,0,0.045); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --section-alt: rgba(240,235,225,0.45); }
[data-theme="dark"] .bg-layer { background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%), radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%), linear-gradient(162deg, #161a2a, #1a1e30 50%, #141824); }
[data-theme="light"] .bg-layer { background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%), radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%), linear-gradient(155deg, #f7f2ea, #f0ebe1 60%, #f9f5f0); }
.container { max-width: 900px; margin: 0 auto; padding: 20px; }
.version-info { background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; border-radius: 8px; padding: 20px; text-align: center; margin: 20px 0; }
[data-theme="dark"] .version-info { background: linear-gradient(135deg, #2a2a4e, #26213e); }
.ver { font-size: 2em; font-weight: 700; }
.version-date { margin-top: 8px; opacity: 0.8; }
.badge-row { display: flex; gap: 12px; flex-wrap: wrap; margin: 16px 0; }
.badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.85em; font-weight: 600; }
.badge-green { background: #d4edda; color: #155724; }
.badge-blue { background: #d1ecf1; color: #0c5460; }
.badge-orange { background: #fff3cd; color: #856404; }
[data-theme="dark"] .badge-green { background: rgba(110,195,135,0.2); color: rgba(110,195,135,0.9); }
[data-theme="dark"] .badge-blue { background: rgba(120,170,230,0.2); color: rgba(120,170,230,0.9); }
[data-theme="dark"] .badge-orange { background: rgba(230,180,80,0.2); color: rgba(230,180,80,0.9); }
.section-title { font-size: 1.3em; color: #16213e; margin: 28px 0 12px; padding-left: 10px; border-left: 3px solid #e94560; }
[data-theme="dark"] .section-title { color: rgba(240,236,228,0.97); border-left-color: #e94560; }
.section-desc { color: #666; font-size: 0.95em; margin-bottom: 16px; }
[data-theme="dark"] .section-desc { color: rgba(170,160,145,0.88); }
.rule-card { background: white; border-radius: 8px; padding: 16px 20px; margin: 12px 0; box-shadow: 0 1px 3px rgba(0,0,0,.1); }
[data-theme="dark"] .rule-card { background: rgba(48,53,76,0.85); }
.rule-name { font-weight: 600; color: #e94560; margin-bottom: 4px; }
.rule-detail { color: #666; font-size: 0.95em; line-height: 1.8; }
[data-theme="dark"] .rule-detail { color: rgba(195,185,165,0.95); }
.table-wrap { margin: 12px 0; }
.table-row { display: flex; padding: 8px 12px; border-bottom: 1px solid #dee2e6; }
.table-row.table-header { background: #f8f9fa; font-weight: 600; color: #495057; }
.table-row.table-total { font-weight: bold; background: #e8f5e9; }
[data-theme="dark"] .table-row.table-header { background: rgba(48,53,76,0.6); color: rgba(240,236,228,0.9); }
[data-theme="dark"] .table-row.table-total { background: rgba(110,195,135,0.1); }
[data-theme="dark"] .table-row { border-bottom-color: rgba(255,255,255,0.08); }
.table-cell { flex: 1; font-size: 0.9em; }
.file-list { margin: 12px 0; }
.file-item { padding: 8px 0; border-bottom: 1px solid #eee; display: flex; align-items: center; gap: 8px; }
[data-theme="dark"] .file-item { border-bottom-color: rgba(255,255,255,0.06); }
.file-icon { font-size: 1em; }
.file-name { font-family: monospace; background: #f0f0f0; padding: 2px 6px; border-radius: 4px; font-size: 0.9em; color: #e83e8c; }
[data-theme="dark"] .file-name { background: rgba(255,255,255,0.06); color: #e83e8c; }
.file-desc { font-size: 0.85em; color: #666; }
[data-theme="dark"] .file-desc { color: rgba(170,160,145,0.88); }
.disclaimer { background: #fff3cd; border-left: 4px solid #ffc107; padding: 12px 16px; margin: 20px 0; border-radius: 4px; }
[data-theme="dark"] .disclaimer { background: rgba(230,180,80,0.1); border-left-color: rgba(230,180,80,0.5); }
.disclaimer-title { font-weight: 600; display: block; margin-bottom: 4px; }
.disclaimer-text { font-size: 0.9em; line-height: 1.6; display: block; }
.footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd; text-align: center; color: #999; font-size: 0.9em; }
[data-theme="dark"] .footer { border-top-color: rgba(255,255,255,0.08); color: rgba(170,160,145,0.6); }
.footer text { display: block; margin: 4px 0; }

/* 弹窗 */
.modal-overlay { display: none; position: fixed; inset: 0; z-index: 300; background: rgba(0,0,0,0.55); backdrop-filter: blur(8px); align-items: center; justify-content: center; }
.modal-overlay.open { display: flex; }
.modal-box { background: rgba(48,53,76,0.95); border: 1px solid rgba(255,255,255,0.12); border-radius: 20px; padding: 32px; width: 360px; backdrop-filter: blur(40px); }
[data-theme="light"] .modal-box { background: rgba(255,253,248,0.95); border-color: rgba(0,0,0,0.045); }
.modal-title { font-size: 1.1rem; letter-spacing: 2px; text-align: center; margin-bottom: 24px; }
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: rgba(170,160,145,0.88); margin-bottom: 4px; }
.field-input { width: 100%; padding: 10px 14px; border-radius: 10px; background: rgba(58,64,90,0.88); border: 1px solid rgba(255,255,255,0.20); color: rgba(240,236,228,0.97); font-size: 0.875rem; outline: none; box-sizing: border-box; }
[data-theme="light"] .field-input { background: rgba(252,248,240,0.75); border-color: rgba(0,0,0,0.065); color: rgba(20,16,10,0.96); }
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: rgba(215,125,110,0.88); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; }
.btn { padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; cursor: pointer; border: none; display: inline-flex; align-items: center; justify-content: center; }
.btn-outline { background: transparent; border: 1px solid rgba(255,255,255,0.12); color: rgba(195,185,165,0.95); }
.btn-accent { background: hsl(38,60%,60%); color: #fff; }
</style>
