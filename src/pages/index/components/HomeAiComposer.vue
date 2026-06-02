<template>
  <view class="home-ai-main">
    <textarea
      class="home-ai-input"
      v-model="localValue"
      auto-height
      maxlength="800"
      :placeholder="placeholder"
      @keydown="$emit('keydown', $event)"
    />
    <view class="home-ai-toolbar">
      <view class="home-ai-toolbar-left">
        <view class="profile-picker" @tap="$emit('open-profile')">
          <text class="profile-plus">＋</text>
          <text class="profile-name">{{ selectedProfileName || '选择命盘' }}</text>
        </view>
        <view class="tool-picker" @tap="$emit('open-tool')">
          <text class="tool-picker-icon">☷</text>
          <text>{{ autoSelectTools ? '自动选术数' : selectedToolSummary }}</text>
        </view>
      </view>
      <view class="home-ai-toolbar-right">
        <picker :range="readingModeNames" :value="readingModeIdx" @change="$emit('reading-mode-change', $event)">
          <view class="reading-mode-picker">
            <text class="reading-mode-label">解读模式</text>
            <text class="reading-mode-name">{{ selectedReadingMode.name }}</text>
          </view>
        </picker>
        <picker :range="llmModelNames" :value="llmModelIdx" @change="$emit('llm-model-change', $event)">
          <view class="llm-picker">
            <text class="llm-name">{{ selectedLlmModel.name || '基础模型' }}</text>
            <text class="llm-points">消耗 {{ estimatedCost }} · 余 {{ currentPoints }}</text>
          </view>
        </picker>
        <view class="home-ai-send" :class="{ disabled: loading }" @tap="$emit('send')">
          ↑
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  selectedProfileName: { type: String, default: '' },
  autoSelectTools: { type: Boolean, default: true },
  selectedToolSummary: { type: String, default: '选择术数' },
  readingModeNames: { type: Array, default: () => [] },
  readingModeIdx: { type: Number, default: 0 },
  selectedReadingMode: { type: Object, default: () => ({}) },
  llmModelNames: { type: Array, default: () => [] },
  llmModelIdx: { type: Number, default: 0 },
  selectedLlmModel: { type: Object, default: () => ({}) },
  estimatedCost: { type: Number, default: 0 },
  currentPoints: { type: Number, default: 0 },
})

const emit = defineEmits([
  'update:modelValue',
  'open-profile',
  'open-tool',
  'reading-mode-change',
  'llm-model-change',
  'send',
  'keydown',
])

const localValue = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value),
})
</script>

<style scoped>
.home-ai-main { position: fixed; left: 50%; bottom: 14px; z-index: 260; transform: translateX(-50%); width: min(960px, calc(100vw - 36px)); box-sizing: border-box; display: flex; flex-direction: column; gap: 7px; padding: 10px 12px; border: 1px solid rgba(178,149,93,0.18); border-radius: 18px; background: rgba(34, 31, 25, 0.50); backdrop-filter: blur(30px) saturate(145%); box-shadow: 0 16px 48px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.08); overflow-x: hidden; transition: border-color .2s ease, box-shadow .2s ease, background .2s ease; }
.home-ai-main:focus-within { border-color: rgba(178,149,93,0.50); box-shadow: 0 18px 52px rgba(0,0,0,0.24), 0 0 0 3px rgba(178,149,93,0.10), inset 0 1px 0 rgba(255,255,255,0.12); }
[data-theme="light"] .home-ai-main { background: rgba(255,253,248,0.80); box-shadow: 0 12px 34px rgba(60,40,15,0.10), inset 0 1px 0 rgba(255,255,255,0.75); }
[data-theme="light"] .home-ai-main:focus-within { box-shadow: 0 14px 42px rgba(60,40,15,0.13), 0 0 0 3px rgba(150,103,20,0.10), inset 0 1px 0 rgba(255,255,255,0.82); }
.home-ai-input { width: 100%; min-height: 42px; max-height: 64px; padding: 5px 4px 0; color: var(--text-1); font-size: 0.9rem; line-height: 1.38; background: transparent !important; background-color: transparent !important; border: none; outline: none; box-sizing: border-box; appearance: none; -webkit-appearance: none; color-scheme: dark; }
[data-theme="light"] .home-ai-input { color-scheme: light; }
.home-ai-input::placeholder { color: rgba(120,108,86,0.68); }
.home-ai-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 40px; flex-wrap: nowrap !important; overflow-x: hidden; box-sizing: border-box; width: 100%; }
.home-ai-toolbar-left { display: flex; align-items: center; gap: 6px; flex-shrink: 1; min-width: 0; }
.home-ai-toolbar-right { display: flex; align-items: center; gap: 6px; margin-left: auto; flex-shrink: 1; min-width: 0; overflow-x: hidden; box-sizing: border-box; }
.profile-picker, .tool-picker, .reading-mode-picker, .llm-picker, .home-ai-send { min-height: 36px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.18); background: rgba(255,255,255,0.065); color: var(--text-1); display: flex; align-items: center; justify-content: center; cursor: pointer; box-sizing: border-box; flex-shrink: 0; transition: border-color .18s ease, background .18s ease, transform .18s ease; }
[data-theme="light"] .profile-picker, [data-theme="light"] .tool-picker, [data-theme="light"] .reading-mode-picker, [data-theme="light"] .llm-picker { background: rgba(255,251,242,0.76); }
.profile-picker:hover, .tool-picker:hover, .reading-mode-picker:hover, .llm-picker:hover { border-color: rgba(178,149,93,0.45); background: var(--accent-glow); }
.profile-picker, .tool-picker { justify-content: flex-start; gap: 6px; padding: 0 10px; max-width: 168px; min-width: 86px; flex-shrink: 1; }
.profile-plus, .tool-picker-icon { width: 20px; height: 20px; border-radius: 50%; background: var(--accent-glow); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; flex-shrink: 0; }
.profile-name, .tool-picker text:last-child { display: block; font-size: 0.75rem; color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.llm-picker { min-width: 96px; max-width: 128px; padding: 4px 10px; flex-direction: column; align-items: flex-start; gap: 1px; color: var(--text-2); white-space: nowrap; flex-shrink: 1; overflow: hidden; }
.reading-mode-picker { min-width: 82px; max-width: 96px; padding: 4px 10px; flex-direction: column; align-items: center; justify-content: center; gap: 1px; color: var(--text-2); white-space: nowrap; flex-shrink: 0; overflow: hidden; text-align: center; }
.reading-mode-label { display: block; width: 100%; overflow: hidden; text-overflow: ellipsis; font-size: 0.56rem; color: var(--text-3); line-height: 1.15; text-align: center; }
.reading-mode-name { display: block; width: 100%; overflow: hidden; text-overflow: ellipsis; font-size: 0.72rem; color: var(--text-1); line-height: 1.2; text-align: center; }
.llm-name { display: block; width: 100%; overflow: hidden; text-overflow: ellipsis; font-size: 0.7rem; line-height: 1.15; }
.llm-points { display: block; width: 100%; overflow: hidden; text-overflow: ellipsis; color: var(--text-3); font-size: 0.56rem; line-height: 1.1; }
.home-ai-send { width: 36px; height: 36px; min-height: 36px; background: var(--accent); border-color: var(--accent); color: #fff; font-size: 1.1rem; font-weight: 700; line-height: 1; flex-shrink: 0; box-shadow: 0 8px 22px rgba(120,80,12,0.22); }
[data-theme="light"] .home-ai-send { background: var(--accent); border-color: var(--accent); color: #fff; }
.home-ai-send:hover { transform: translateY(-1px); }
.home-ai-send.disabled { opacity: 0.55; pointer-events: none; }

@media (max-width: 760px) {
  .home-ai-input { min-height: 40px; max-height: 60px; }
  .home-ai-main { bottom: 12px; }
}

@media (max-width: 640px) {
  .home-ai-input { min-height: 38px; max-height: 56px; font-size: 0.88rem; }
  .home-ai-main { padding: 8px 10px; gap: 5px; bottom: 8px; }
  .home-ai-toolbar { min-height: 34px; }
  .profile-picker, .tool-picker, .reading-mode-picker, .llm-picker, .home-ai-send { min-height: 32px; }
  .home-ai-send { width: 32px; height: 32px; }
}

@media (max-width: 520px) {
  .home-ai-main { bottom: 8px; width: calc(100vw - 18px); border-radius: 16px; padding: 9px 10px; gap: 6px; }
  .home-ai-input { min-height: 40px; max-height: 58px; font-size: 0.88rem; }
  .home-ai-toolbar { gap: 4px; flex-wrap: nowrap !important; overflow-x: hidden; box-sizing: border-box; }
  .home-ai-toolbar-left, .home-ai-toolbar-right { gap: 4px; }
  .home-ai-toolbar-right { gap: 3px; overflow-x: hidden; box-sizing: border-box; }
  .profile-picker, .tool-picker { max-width: 84px; padding: 0 6px; min-height: 30px; }
  .profile-plus, .tool-picker-icon { width: 18px; height: 18px; font-size: 0.72rem; }
  .profile-name, .tool-picker text:last-child { font-size: 0.66rem; }
  .reading-mode-picker { min-width: 58px; max-width: 64px; padding: 3px 6px; min-height: 30px; }
  .reading-mode-label { display: none; }
  .reading-mode-name { font-size: 0.64rem; }
  .llm-picker { min-width: 88px; max-width: 98px; padding: 3px 7px; min-height: 30px; align-items: flex-start; }
  .home-ai-send { width: 30px; height: 30px; min-height: 30px; font-size: 0.95rem; }
}

@media (max-width: 390px) {
  .home-ai-main { padding: 7px 9px; gap: 4px; border-radius: 15px; }
  .home-ai-input { min-height: 34px; max-height: 50px; font-size: 0.84rem; padding: 3px 4px 0; }
  .home-ai-toolbar { gap: 3px; flex-wrap: nowrap !important; overflow-x: hidden; box-sizing: border-box; }
  .home-ai-toolbar-left, .home-ai-toolbar-right { gap: 3px; }
  .home-ai-toolbar-right { overflow-x: hidden; box-sizing: border-box; }
  .profile-picker, .tool-picker { max-width: 72px; padding: 0 4px; min-height: 28px; }
  .profile-plus, .tool-picker-icon { width: 16px; height: 16px; font-size: 0.66rem; }
  .profile-name, .tool-picker text:last-child { font-size: 0.6rem; }
  .reading-mode-picker { min-width: 48px; max-width: 52px; padding: 2px 5px; min-height: 28px; }
  .reading-mode-name { font-size: 0.58rem; }
  .llm-picker { min-width: 76px; max-width: 82px; padding: 2px 6px; min-height: 28px; }
  .home-ai-send { width: 26px; height: 26px; min-height: 26px; font-size: 0.9rem; }
}
</style>
