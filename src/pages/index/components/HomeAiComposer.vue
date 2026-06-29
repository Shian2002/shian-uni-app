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
    <view class="home-ai-toolbar" :class="{ 'no-llm': hideLlmPicker }">
      <view class="home-ai-toolbar-left">
        <view class="profile-picker" @tap="$emit('open-profile')">
          <text class="profile-plus">＋</text>
          <text class="profile-name">{{ selectedProfileName || '选择命盘' }}</text>
        </view>
        <view class="ai-select-wrap">
          <view ref="toolPickerRef" class="tool-picker" :class="{ active: openMenu === 'tool' }" @tap="toggleMenu('tool')">
            <text class="tool-picker-icon">☷</text>
            <text>{{ autoSelectTools ? '自动选术数' : selectedToolSummary }}</text>
          </view>
        </view>
      </view>
      <view class="home-ai-toolbar-right">
        <view class="ai-select-wrap">
          <view ref="modePickerRef" class="reading-mode-picker" aria-label="解读模式" :class="{ active: openMenu === 'mode' }" @tap="toggleMenu('mode')">
            <text class="reading-mode-label">{{ selectedReadingMode.name || '标准' }}</text>
            <text class="reading-mode-points">{{ modeCostText }}</text>
            <text class="reading-mode-caret">⌄</text>
          </view>
        </view>
        <view v-if="!hideLlmPicker" class="ai-select-wrap">
          <view ref="llmPickerRef" class="llm-picker" :class="{ active: openMenu === 'llm' }" @tap="toggleMenu('llm')">
            <text class="llm-name">{{ compactLlmName }}</text>
            <text class="llm-points">{{ llmCostText }}</text>
            <text class="llm-caret">⌄</text>
          </view>
        </view>
        <view class="home-ai-send" :class="{ disabled: loading }" @tap="$emit('send')">
          ↑
        </view>
      </view>
    </view>
  </view>
  <teleport to="body">
    <view v-if="openMenu === 'mode'" class="ai-select-popover mode-popover" :style="popoverStyle">
      <view
        v-for="(label, idx) in readingModeLabels"
        :key="'mode-' + idx"
        class="ai-select-option"
        :class="{ selected: idx === readingModeIdx }"
        @tap="selectReadingMode(idx)"
      >
        <text class="ai-select-name">{{ readingModeNames[idx] || label }}</text>
        <text class="ai-select-meta">{{ modeOptionMeta(label) }}</text>
      </view>
    </view>
    <view v-if="openMenu === 'llm'" class="ai-select-popover llm-popover" :style="popoverStyle">
      <view
        v-for="(name, idx) in llmModelNames"
        :key="'llm-' + idx"
        class="ai-select-option"
        :class="{ selected: idx === llmModelIdx }"
        @tap="selectLlmModel(idx)"
      >
        <text class="ai-select-name">{{ compactModelOption(name) }}</text>
        <text class="ai-select-meta">{{ idx === llmModelIdx ? llmCostText : '选择' }}</text>
      </view>
    </view>
    <view v-if="openMenu === 'tool'" class="ai-select-popover tool-popover" :style="popoverStyle">
      <view
        class="ai-select-option tool-select-option"
        :class="{ selected: autoSelectTools }"
        @tap="toggleAutoTools"
      >
        <text class="ai-select-name">自动选择</text>
        <view class="tool-option-side">
          <text class="ai-select-meta">推荐</text>
          <text class="tool-check-circle" :class="{ checked: autoSelectTools }">{{ autoSelectTools ? '✓' : '' }}</text>
        </view>
      </view>
      <view
        v-for="tool in toolModels"
        :key="'tool-' + tool.id"
        class="ai-select-option tool-select-option"
        :class="{ selected: selectedToolModels.includes(tool.id) }"
        @tap="toggleTool(tool.id)"
      >
        <text class="ai-select-name">{{ tool.name }}</text>
        <view class="tool-option-side">
          <text class="ai-select-meta">{{ toolCostText(tool) }}</text>
          <text class="tool-check-circle" :class="{ checked: selectedToolModels.includes(tool.id) }">{{ selectedToolModels.includes(tool.id) ? '✓' : '' }}</text>
        </view>
      </view>
    </view>
  </teleport>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: '' },
  loading: { type: Boolean, default: false },
  selectedProfileName: { type: String, default: '' },
  autoSelectTools: { type: Boolean, default: false },
  selectedToolSummary: { type: String, default: '选择术数' },
  toolModels: { type: Array, default: () => [] },
  selectedToolModels: { type: Array, default: () => [] },
  readingModeNames: { type: Array, default: () => [] },
  readingModeLabels: { type: Array, default: () => [] },
  readingModeIdx: { type: Number, default: 0 },
  selectedReadingMode: { type: Object, default: () => ({}) },
  llmModelNames: { type: Array, default: () => [] },
  llmModelIdx: { type: Number, default: 0 },
  selectedLlmModel: { type: Object, default: () => ({}) },
  estimatedCost: { type: Number, default: 0 },
  currentPoints: { type: Number, default: 0 },
  hideLlmPicker: { type: Boolean, default: false },
})

const emit = defineEmits([
  'update:modelValue',
  'open-profile',
  'tool-auto-toggle',
  'tool-model-toggle',
  'reading-mode-change',
  'llm-model-change',
  'send',
  'keydown',
])

const localValue = computed({
  get: () => props.modelValue,
  set: value => emit('update:modelValue', value),
})

const openMenu = ref('')
const popoverStyle = ref({})
const toolPickerRef = ref(null)
const modePickerRef = ref(null)
const llmPickerRef = ref(null)

function toggleMenu(name) {
  if (openMenu.value === name) {
    closeMenu()
    return
  }
  setPopoverPosition(name)
  openMenu.value = name
}

function closeMenu() {
  openMenu.value = ''
}

function selectReadingMode(index) {
  emit('reading-mode-change', { detail: { value: index } })
  closeMenu()
}

function selectLlmModel(index) {
  emit('llm-model-change', { detail: { value: index } })
  closeMenu()
}

function toggleAutoTools() {
  emit('tool-auto-toggle')
}

function toggleTool(id) {
  emit('tool-model-toggle', id)
}

function onGlobalPointerDown(event) {
  try {
    const target = event && event.target
    if (target && target.closest && target.closest('.ai-select-wrap')) return
    if (target && target.closest && target.closest('.ai-select-popover')) return
  } catch(_) {}
  closeMenu()
}

function getPickerElement(name) {
  const picker = name === 'llm' ? llmPickerRef.value : name === 'tool' ? toolPickerRef.value : modePickerRef.value
  return picker && (picker.$el || picker)
}

function setPopoverPosition(name) {
  try {
    const target = getPickerElement(name)
    const rect = target && target.getBoundingClientRect ? target.getBoundingClientRect() : null
    const width = name === 'tool' ? 214 : name === 'llm' ? 156 : 146
    const viewportWidth = window.innerWidth || 430
    const centerLeft = rect ? rect.left + rect.width / 2 : viewportWidth - width / 2 - 52
    const left = Math.max(12 + width / 2, Math.min(centerLeft, viewportWidth - width / 2 - 12))
    const top = rect ? Math.max(12, rect.top - 8) : undefined
    popoverStyle.value = {
      width: width + 'px',
      left: left + 'px',
      right: 'auto',
      top: top ? top + 'px' : 'auto',
      bottom: 'auto',
    }
  } catch(_) {
    popoverStyle.value = {}
  }
}

const modeCostText = computed(() => {
  const cost = Number(props.selectedReadingMode.display_cost || 0)
  if (cost > 0) return cost + '积分'
  const delta = Number(props.selectedReadingMode.cost_delta || 0)
  if (delta > 0) return '+' + delta + '积分'
  if (delta < 0) return delta + '积分'
  return '800积分'
})

const compactLlmName = computed(() => {
  return String(props.selectedLlmModel.name || '基础模型').replace(/模型$/, '')
})

function compactModelOption(name) {
  return String(name || '基础模型').replace(/模型$/, '')
}

function modeOptionMeta(label) {
  const match = String(label || '').match(/(\d+)\s*(?:分|积分)/)
  return match ? match[1] + '积分' : ''
}

function toolCostText(tool) {
  return tool && tool.id ? '影响估算' : '选择'
}

const llmCostText = computed(() => {
  const cost = Number(props.selectedLlmModel.cost_base || props.estimatedCost || 0)
  return cost > 0 ? cost + '积分' : '800积分'
})

onMounted(() => {
  try {
    document.addEventListener('pointerdown', onGlobalPointerDown, true)
  } catch(_) {}
})

onBeforeUnmount(() => {
  try {
    document.removeEventListener('pointerdown', onGlobalPointerDown, true)
  } catch(_) {}
})
</script>

<style scoped>
.home-ai-main { position: fixed; left: 50%; bottom: 14px; z-index: 880; transform: translateX(-50%); width: min(960px, calc(100vw - 36px)); box-sizing: border-box; display: flex; flex-direction: column; gap: 7px; padding: 10px 12px; border: 1px solid rgba(178,149,93,0.18); border-radius: 18px; background: rgba(34, 31, 25, 0.50); backdrop-filter: blur(30px) saturate(145%); box-shadow: 0 16px 48px rgba(0,0,0,0.22), inset 0 1px 0 rgba(255,255,255,0.08); overflow: visible; transition: border-color .2s ease, box-shadow .2s ease, background .2s ease; }
.home-ai-main:focus-within { border-color: rgba(178,149,93,0.50); box-shadow: 0 18px 52px rgba(0,0,0,0.24), 0 0 0 3px rgba(178,149,93,0.10), inset 0 1px 0 rgba(255,255,255,0.12); }
[data-theme="light"] .home-ai-main { background: rgba(255,253,248,0.80); box-shadow: 0 12px 34px rgba(60,40,15,0.10), inset 0 1px 0 rgba(255,255,255,0.75); }
[data-theme="light"] .home-ai-main:focus-within { box-shadow: 0 14px 42px rgba(60,40,15,0.13), 0 0 0 3px rgba(150,103,20,0.10), inset 0 1px 0 rgba(255,255,255,0.82); }
.home-ai-input { width: 100%; min-height: 42px; max-height: 64px; padding: 5px 4px 0; color: var(--text-1); font-size: 0.9rem; line-height: 1.38; background: transparent !important; background-color: transparent !important; border: none; outline: none; box-sizing: border-box; appearance: none; -webkit-appearance: none; color-scheme: dark; }
[data-theme="light"] .home-ai-input { color-scheme: light; }
.home-ai-input::placeholder { color: rgba(120,108,86,0.68); }
.home-ai-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 8px; min-height: 40px; flex-wrap: nowrap !important; overflow-x: visible; box-sizing: border-box; width: 100%; }
.home-ai-toolbar-left { display: flex; align-items: center; gap: 6px; flex-shrink: 1; min-width: 0; }
.home-ai-toolbar-right { display: flex; align-items: center; gap: 6px; margin-left: auto; flex-shrink: 1; min-width: 0; overflow-x: visible; box-sizing: border-box; }
.profile-picker, .tool-picker, .reading-mode-picker, .llm-picker, .home-ai-send { min-height: 36px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.18); background: rgba(255,255,255,0.065); color: var(--text-1); display: flex; align-items: center; justify-content: center; cursor: pointer; box-sizing: border-box; flex-shrink: 0; transition: border-color .18s ease, background .18s ease, transform .18s ease; }
[data-theme="light"] .profile-picker, [data-theme="light"] .tool-picker, [data-theme="light"] .reading-mode-picker, [data-theme="light"] .llm-picker { background: rgba(255,251,242,0.76); }
.profile-picker:hover, .tool-picker:hover, .reading-mode-picker:hover, .llm-picker:hover, .tool-picker.active, .reading-mode-picker.active, .llm-picker.active { border-color: rgba(178,149,93,0.45); background: var(--accent-glow); }
.profile-picker, .tool-picker { justify-content: flex-start; gap: 6px; padding: 0 10px; max-width: 168px; min-width: 86px; flex-shrink: 1; }
.profile-plus, .tool-picker-icon { width: 20px; height: 20px; border-radius: 50%; background: var(--accent-glow); color: var(--accent); display: flex; align-items: center; justify-content: center; font-size: 0.8rem; flex-shrink: 0; }
.profile-name, .tool-picker text:last-child { display: block; font-size: 0.75rem; color: var(--text-2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.reading-mode-picker { min-width: 96px; max-width: 116px; min-height: 34px; padding: 0 8px 0 10px; border-radius: 999px; border: 1px solid rgba(178,149,93,0.18); background: rgba(255,255,255,0.055); color: var(--text-2); display: flex; align-items: center; justify-content: flex-start; gap: 6px; cursor: pointer; box-sizing: border-box; flex-shrink: 0; transition: border-color .18s ease, background .18s ease; }
[data-theme="light"] .reading-mode-picker { background: rgba(255,251,242,0.76); }
.reading-mode-picker:hover { border-color: rgba(178,149,93,0.45); background: var(--accent-glow); }
.reading-mode-label { display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-size: 0.68rem; line-height: 1; color: var(--text-1); }
.reading-mode-points { display: flex; align-items: center; height: 18px; padding: 0 5px; border-radius: 999px; background: var(--accent-glow); color: var(--accent); font-size: 0.54rem; line-height: 1; flex-shrink: 0; }
.reading-mode-caret { color: var(--text-3); font-size: 0.68rem; line-height: 1; margin-left: -2px; flex-shrink: 0; }
.llm-picker { min-width: 112px; max-width: 142px; padding: 0 9px 0 11px; gap: 7px; justify-content: flex-start; color: var(--text-2); white-space: nowrap; flex-shrink: 1; overflow: hidden; }
.llm-name { display: block; min-width: 0; overflow: hidden; text-overflow: ellipsis; font-size: 0.72rem; line-height: 1; color: var(--text-1); }
.llm-points { display: flex; align-items: center; height: 18px; padding: 0 6px; border-radius: 999px; background: var(--accent-glow); color: var(--accent); font-size: 0.58rem; line-height: 1; flex-shrink: 0; }
.llm-caret { color: var(--text-3); font-size: 0.72rem; line-height: 1; margin-left: -2px; flex-shrink: 0; }
.ai-select-wrap { position: relative; min-width: 0; flex-shrink: 1; }
.ai-select-popover {
  position: fixed;
  right: 0;
  bottom: auto;
  z-index: 920;
  min-width: 136px;
  padding: 6px;
  border-radius: 14px;
  border: 1px solid rgba(178,149,93,0.22);
  background: rgba(31,29,24,0.86);
  box-sizing: border-box;
  -webkit-backdrop-filter: blur(24px) saturate(1.45);
  backdrop-filter: blur(24px) saturate(1.45);
  box-shadow: 0 18px 48px rgba(0,0,0,0.26), inset 0 1px 0 rgba(255,255,255,0.08);
  pointer-events: auto;
  transform: translate(-50%, -100%);
}
[data-theme="light"] .ai-select-popover {
  background: rgba(255,253,248,0.92);
  border-color: rgba(178,149,93,0.20);
  box-shadow: 0 18px 44px rgba(72,47,12,0.15), inset 0 1px 0 rgba(255,255,255,0.82);
}
.llm-popover { min-width: 150px; }
.tool-popover { min-width: 196px; max-height: min(360px, calc(100vh - 120px)); overflow-y: auto; }
.ai-select-option {
  min-height: 34px;
  padding: 7px 9px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: var(--text-2);
  box-sizing: border-box;
}
.ai-select-option + .ai-select-option { margin-top: 3px; }
.ai-select-option.selected {
  color: var(--text-1);
  background: rgba(178,149,93,0.16);
  box-shadow: inset 0 0 0 1px rgba(178,149,93,0.18);
}
.ai-select-option:active { background: rgba(178,149,93,0.12); }
.tool-select-option { min-height: 32px; }
.tool-option-side { display: flex; align-items: center; gap: 7px; flex-shrink: 0; }
.tool-check-circle {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 1px solid rgba(178,149,93,0.34);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.58rem;
  font-weight: 800;
  line-height: 1;
  box-sizing: border-box;
  background: rgba(255,255,255,0.035);
}
.tool-check-circle.checked { border-color: var(--accent); background: var(--accent); }
[data-theme="light"] .tool-check-circle { background: rgba(255,251,242,0.72); }
[data-theme="light"] .tool-check-circle.checked { background: var(--accent); }
.ai-select-name {
  min-width: 0;
  font-size: 0.72rem;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.ai-select-meta {
  flex-shrink: 0;
  height: 18px;
  padding: 0 6px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  color: var(--accent);
  background: var(--accent-glow);
  font-size: 0.54rem;
  line-height: 1;
}
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
  .profile-picker, .tool-picker, .llm-picker, .home-ai-send { min-height: 32px; }
  .reading-mode-picker { min-height: 32px; }
  .home-ai-send { width: 32px; height: 32px; }
}

@media (max-width: 520px) {
  .home-ai-main { bottom: 8px; width: calc(100vw - 18px); border-radius: 16px; padding: 9px 10px; gap: 6px; }
  .home-ai-input { min-height: 40px; max-height: 58px; font-size: 0.88rem; }
  .home-ai-toolbar { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.08fr) 72px 72px 30px; align-items: center; gap: 4px; flex-wrap: nowrap !important; overflow: visible; box-sizing: border-box; }
  .home-ai-toolbar.no-llm { grid-template-columns: minmax(0, 1fr) minmax(0, 1.08fr) 72px 30px; }
  .home-ai-toolbar-left, .home-ai-toolbar-right { display: contents; }
  .profile-picker, .tool-picker, .reading-mode-picker, .llm-picker { width: 100%; min-width: 0; max-width: none; height: 30px; min-height: 30px; padding: 0 7px; flex-direction: row; align-items: center; justify-content: flex-start; gap: 4px; overflow: hidden; }
  .ai-select-wrap { width: 100%; min-width: 0; }
  .ai-select-popover { min-width: 132px; max-width: calc(100vw - 30px); }
  .llm-popover { min-width: 142px; }
  .tool-popover { min-width: 190px; max-height: min(320px, calc(100vh - 108px)); }
  .profile-plus, .tool-picker-icon { width: 18px; height: 18px; font-size: 0.72rem; }
  .profile-name, .tool-picker text:last-child { font-size: 0.66rem; }
  .reading-mode-label, .llm-name { font-size: 0.64rem; }
  .reading-mode-points, .llm-points { display: flex; align-items: center; height: 16px; padding: 0 4px; border-radius: 999px; background: var(--accent-glow); color: var(--accent); font-size: 0.5rem; line-height: 1; flex-shrink: 0; }
  .reading-mode-caret, .llm-caret { display: none; }
  .home-ai-send { width: 30px; min-width: 30px; height: 30px; min-height: 30px; font-size: 0.95rem; justify-self: end; }
}

@media (max-width: 390px) {
  .home-ai-main { padding: 7px 9px; gap: 4px; border-radius: 15px; }
  .home-ai-input { min-height: 34px; max-height: 50px; font-size: 0.84rem; padding: 3px 4px 0; }
  .home-ai-toolbar { grid-template-columns: minmax(0, 1fr) minmax(0, 1.05fr) 72px 72px 28px; gap: 3px; overflow: visible; box-sizing: border-box; }
  .home-ai-toolbar.no-llm { grid-template-columns: minmax(0, 1fr) minmax(0, 1.05fr) 72px 28px; }
  .profile-picker, .tool-picker, .reading-mode-picker, .llm-picker { height: 28px; min-height: 28px; padding: 0 5px; gap: 3px; }
  .ai-select-popover { min-width: 124px; padding: 5px; }
  .llm-popover { min-width: 134px; }
  .tool-popover { min-width: 184px; }
  .ai-select-option { min-height: 31px; padding: 6px 8px; gap: 8px; }
  .ai-select-name { font-size: 0.66rem; }
  .ai-select-meta { height: 16px; padding: 0 5px; font-size: 0.48rem; }
  .tool-option-side { gap: 5px; }
  .tool-check-circle { width: 16px; height: 16px; font-size: 0.52rem; }
  .profile-plus, .tool-picker-icon { width: 16px; height: 16px; font-size: 0.66rem; }
  .profile-name, .tool-picker text:last-child { font-size: 0.6rem; }
  .reading-mode-label, .llm-name { font-size: 0.58rem; }
  .reading-mode-points, .llm-points { height: 15px; padding: 0 3px; font-size: 0.46rem; }
  .home-ai-send { width: 28px; min-width: 28px; height: 28px; min-height: 28px; font-size: 0.9rem; }
}
</style>
