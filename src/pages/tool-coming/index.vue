<template>
  <view class="page-root" :data-theme="theme">
    <!-- 背景 -->
    <view class="bg-layer"></view>

    <TopNav :theme="theme" :isLoggedIn="isLoggedIn" @toggle-theme="toggleTheme" />

    <view class="page-wrap">
      <!-- 即将上线 -->
      <view class="section">
        <view class="tool-container">
          <view class="coming-soon-wrap">
            <text class="coming-soon-icon">{{ toolIcon }}</text>
            <text class="coming-soon-title">{{ toolName }}</text>
            <view class="coming-soon-badge">🚧 即将上线</view>
            <text class="coming-soon-desc">{{ toolDesc }}</text>
            <navigator url="/pages/index/index" open-type="switchTab" class="btn btn-accent">← 返回首页</navigator>
          </view>
        </view>
      </view>
    </view>



  </view>
</template>

<script>
import TopNav from '@/components/TopNav.vue'
export default {
  data() {
    return {
      toolName: '即将上线',
      toolIcon: '🔧',
      toolDesc: '该功能正在开发中，敬请期待',
      theme: (typeof uni !== 'undefined' && uni.getStorageSync('xc_theme')) || 'dark',
      isLoggedIn: false
    }
  },
  onLoad(options) {
    // 从路由参数获取工具信息
    if (options.name) this.toolName = decodeURIComponent(options.name)
    if (options.icon) this.toolIcon = decodeURIComponent(options.icon)
    if (options.desc) this.toolDesc = decodeURIComponent(options.desc)

    // 主题
    try {
      const t = uni.getStorageSync('xc_theme')
      this.theme = t || 'dark'
    } catch (e) {
      this.theme = 'dark'
    }
  },
  methods: {
    toggleTheme() {
      this.theme = this.theme === 'dark' ? 'light' : 'dark'
      try { uni.setStorageSync('xc_theme', this.theme) } catch (e) {}
      try {
        document.documentElement.setAttribute('data-theme', this.theme); document.body.setAttribute('data-theme', this.theme); const root = document.querySelector('.page-root')
        if (root) root.setAttribute('data-theme', this.theme)
        const icon = document.getElementById('themeToggleIcon')
        if (icon) icon.textContent = this.theme === 'dark' ? '🌙' : '☀️'
      } catch(_) {}
    },

    showFooterInfo(type) {
      uni.showModal({
        title: type === 'contact' ? '联系方式' : '隐私政策',
        content: type === 'contact' ? '如有问题请通过社区反馈' : '我们重视您的隐私，所有数据仅本地处理',
        showCancel: false
      })
    }
  },
  components: { TopNav }
}
</script>

<style scoped>
/* 根容器 */
.page-root {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
  font-family: var(--font-sans, 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif);
  font-size: 0.9375rem;
  line-height: 1.75;
  color: var(--text-1, rgba(240,236,228,0.97));
}

/* CSS变量 — 1:1还原Flask原版 */
:root {
  --ease: cubic-bezier(0.4, 0, 0.2, 1);
  --radius-md: 14px; --radius-lg: 20px;
  --font-serif: 'Songti SC', 'Noto Serif SC', 'STSong', serif;
  --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif;
  --max-w: 1280px;
}
/* ═══ TopNav 组件所需的 CSS 变量 ═══ */
[data-theme="dark"] { --nav-bg: rgba(22, 26, 42, 0.92); --card-border: rgba(255,255,255,0.12); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --nav-bg: rgba(247,242,234,0.95); --card-border: rgba(0,0,0,0.045); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --section-alt: rgba(240,235,225,0.45); }

/* 背景 */
.bg-layer {
  position: fixed; top: 0; left: 0; right: 0; bottom: 0;
  z-index: 0; pointer-events: none;
  transition: background 0.8s var(--ease);
}
[data-theme="dark"] .bg-layer {
  background: radial-gradient(ellipse 80% 60% at 18% 8%, rgba(45,50,90,0.30) 0%, transparent 72%),
              radial-gradient(ellipse 65% 50% at 88% 92%, rgba(65,42,18,0.16) 0%, transparent 68%),
              linear-gradient(162deg, #161a2a, #1a1e30 50%, #141824);
}
[data-theme="light"] .bg-layer {
  background: radial-gradient(ellipse 72% 52% at 12% 18%, rgba(210,190,150,0.20) 0%, transparent 65%),
              radial-gradient(ellipse 55% 42% at 92% 85%, rgba(195,175,135,0.13) 0%, transparent 60%),
              linear-gradient(155deg, #f7f2ea, #f0ebe1 60%, #f9f5f0);
}

.page-wrap { position: relative; z-index: 1; }

/* 通用区块 */
.section { max-width: var(--max-w); margin: 0 auto; padding: 80px 32px; }
.tool-container { max-width: 640px; margin: 0 auto; }

/* 即将上线 */
.coming-soon-wrap {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  min-height: 50vh; text-align: center; padding: 80px 20px;
}
.coming-soon-icon {
  font-size: 5rem; margin-bottom: 24px;
  animation: float 3s ease-in-out infinite;
}
.coming-soon-title {
  font-family: var(--font-serif); font-size: 2rem; color: inherit;
  margin-bottom: 12px; letter-spacing: 3px;
}
.coming-soon-badge {
  display: inline-block; padding: 6px 20px; border-radius: 20px;
  background: hsla(38, 60%, 60%, 0.10); border: 1px solid hsl(38, 60%, 60%);
  color: hsl(38, 60%, 60%); font-size: 0.8125rem; letter-spacing: 2px;
  margin-bottom: 32px;
}
[data-theme="light"] .coming-soon-badge {
  background: hsla(38, 72%, 30%, 0.065); border-color: hsl(38, 72%, 30%);
  color: hsl(38, 72%, 30%);
}
.coming-soon-desc {
  font-size: 1rem; color: rgba(170,160,145,0.88); margin-bottom: 36px; line-height: 1.8;
}
[data-theme="light"] .coming-soon-desc { color: rgba(100,88,68,0.78); }
@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-12px); }
}

/* 按钮（弹窗用） */
.btn {
  padding: 7px 18px; border-radius: 10px; font-size: 0.8125rem; cursor: pointer;
  border: none; transition: all 0.2s; display: inline-block; text-align: center;
}
.btn-outline { background: transparent; border: 1px solid rgba(255,255,255,0.12); color: rgba(195,185,165,0.95); }
.btn-accent { background: hsl(38, 60%, 60%); color: #fff; }
[data-theme="light"] .btn-outline { border-color: rgba(0,0,0,0.045); color: rgba(70,58,40,0.90); }
[data-theme="light"] .btn-accent { background: hsl(38, 72%, 30%); }
.btn-sm { padding: 5px 12px; font-size: 0.75rem; border-radius: 8px; }

/* 弹窗 */
.modal-overlay {
  display: none; position: fixed; inset: 0; z-index: 300;
  background: rgba(0,0,0,0.55); backdrop-filter: blur(8px);
  align-items: center; justify-content: center;
}
.modal-overlay.open { display: flex; }
.modal-box {
  background: rgba(48, 53, 76, 0.85); border: 1px solid rgba(255,255,255,0.12);
  border-radius: var(--radius-lg); padding: 32px; width: 360px;
  backdrop-filter: blur(40px);
}
[data-theme="light"] .modal-box {
  background: rgba(255,253,248,0.68); border-color: rgba(0,0,0,0.045);
}
.modal-title {
  font-family: var(--font-serif); font-size: 1.1rem; letter-spacing: 2px;
  text-align: center; margin-bottom: 24px; display: block;
}
.field { margin-bottom: 14px; }
.field-label { display: block; font-size: 0.75rem; color: rgba(170,160,145,0.88); margin-bottom: 4px; }
.field input {
  width: 100%; padding: 10px 14px; border-radius: 10px;
  background: rgba(58, 64, 90, 0.88); border: 1px solid rgba(255,255,255,0.20);
  color: inherit; font-size: 0.875rem; outline: none;
}
[data-theme="light"] .field input {
  background: rgba(252,248,240,0.75); border-color: rgba(0,0,0,0.065);
}
.modal-btns { display: flex; gap: 10px; margin-top: 20px; }
.modal-btns .btn { flex: 1; text-align: center; }
.modal-error { color: rgba(215,125,110,0.88); font-size: 0.75rem; text-align: center; margin-top: 10px; min-height: 18px; display: block; }

/* 响应式 */
@media (max-width: 768px) {
  .section { padding: 48px 16px; }

}
</style>
