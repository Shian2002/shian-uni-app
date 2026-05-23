<template>
  <view class="page-root" :data-theme="theme">
    <!-- 背景 -->
    <view class="bg-layer"></view>

    <TopNav :theme="theme" @toggle-theme="toggleTheme" />

    <!-- 错误内容 -->
    <view class="error-page">
      <text class="error-code">{{ code }}</text>
      <text class="error-message">{{ message }}</text>
      <text v-if="detail" class="error-detail">{{ detail }}</text>
      <view class="error-actions">
        <navigator url="/pages/index/index" open-type="switchTab" class="error-btn error-btn-primary">🏠 返回首页</navigator>
        <view class="error-btn error-btn-secondary" @tap="goBack">← 返回上页</view>
      </view>
    </view>
  </view>
</template>

<script>
import TopNav from '@/components/TopNav.vue'
export default {
  data() {
    return {
      code: 404,
      message: '页面不存在',
      detail: '',
      theme: (typeof uni !== 'undefined' && uni.getStorageSync('xc_theme')) || 'dark',
    }
  },
  components: { TopNav },
  onLoad(options) {
    // 从路由参数或全局获取错误信息
    if (options.code) this.code = parseInt(options.code) || 404
    if (options.message) this.message = decodeURIComponent(options.message)
    if (options.detail) this.detail = decodeURIComponent(options.detail)

    // 根据错误码设置默认消息
    if (!options.message) {
      if (this.code === 404) this.message = '页面不存在'
      else if (this.code === 500) this.message = '服务器错误'
      else this.message = '请求错误'
    }

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
    goBack() {
      uni.navigateBack({ delta: 1, fail: () => {
        uni.switchTab({ url: '/pages/index/index' })
      }})
    }
  }
}
</script>

<style scoped>
/* 根容器 */
.page-root { min-height: 100vh; position: relative; overflow-x: hidden; font-family: var(--font-sans, 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif); font-size: 0.9375rem; line-height: 1.75; color: var(--text-1, rgba(240,236,228,0.97)); }

/* ═══ TopNav 组件所需的 CSS 变量 ═══ */
:root { --font-sans: 'PingFang SC', 'Helvetica Neue', -apple-system, sans-serif; }
[data-theme="dark"] { --nav-bg: rgba(22, 26, 42, 0.92); --card-border: rgba(255,255,255,0.12); --text-1: rgba(240,236,228,0.97); --text-2: rgba(195,185,165,0.95); --text-3: rgba(170,160,145,0.88); --accent: hsl(38, 60%, 60%); --accent-glow: hsla(38, 60%, 60%, 0.10); --input-bg: rgba(58, 64, 90, 0.88); --input-border: rgba(255,255,255,0.20); --section-alt: rgba(30,34,55,0.45); }
[data-theme="light"] { --nav-bg: rgba(247,242,234,0.95); --card-border: rgba(0,0,0,0.045); --text-1: rgba(20,16,10,0.96); --text-2: rgba(70,58,40,0.90); --text-3: rgba(100,88,68,0.78); --accent: hsl(38, 72%, 30%); --accent-glow: hsla(38, 72%, 30%, 0.065); --input-bg: rgba(252,248,240,0.75); --input-border: rgba(0,0,0,0.065); --section-alt: rgba(240,235,225,0.45); }

/* 背景 */
.bg-layer {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  z-index: 0;
  pointer-events: none;
  transition: background 0.8s cubic-bezier(0.4, 0, 0.2, 1);
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

/* 错误页面 */
.error-page {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
  text-align: center;
  padding: 60px 20px;
  position: relative;
  z-index: 1;
}
.error-code {
  font-size: 120px;
  font-weight: 800;
  line-height: 1;
  background: linear-gradient(135deg, hsl(38, 60%, 60%), hsl(38, 60%, 48%));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 16px;
}
.error-message {
  font-size: 1.5rem;
  color: var(--text-1, rgba(240,236,228,0.97));
  margin-bottom: 12px;
}
.error-detail {
  font-size: 0.9rem;
  color: var(--text-3, rgba(170,160,145,0.88));
  margin-bottom: 32px;
  max-width: 480px;
}
.error-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
}
.error-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 24px;
  border-radius: 12px;
  font-size: 0.95rem;
  text-decoration: none;
  transition: all 0.2s ease;
  cursor: pointer;
}
.error-btn-primary {
  background: hsl(38, 60%, 60%);
  color: #fff;
}
.error-btn-primary:hover {
  filter: brightness(1.1);
  transform: translateY(-1px);
}
.error-btn-secondary {
  background: rgba(255,255,255,0.05);
  color: rgba(195,185,165,0.95);
  border: 1px solid rgba(255,255,255,0.1);
}
[data-theme="light"] .error-btn-secondary {
  background: rgba(0,0,0,0.03);
  color: rgba(70,58,40,0.90);
  border-color: rgba(0,0,0,0.08);
}
.error-btn-secondary:hover {
  background: rgba(255,255,255,0.08);
}

/* 响应式 */
@media (max-width: 640px) {
  .error-code { font-size: 72px; }
  .error-message { font-size: 1.2rem; }
}

/* 移动端响应式 */
@media (max-width: 768px) { }</style>
