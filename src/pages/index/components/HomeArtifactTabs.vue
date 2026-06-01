<template>
  <view class="home-artifact-switcher">
    <view
      class="home-artifact-tab conclusion"
      :class="{ active: summaryActive }"
      v-if="showSummary"
      @tap="$emit('select', '__summary__')"
    >
      <text class="home-artifact-tab-title">综合结论</text>
      <text class="home-artifact-tab-sub">最终合参建议</text>
    </view>
    <view
      class="home-artifact-tab"
      v-for="artifact in artifacts"
      :key="artifact.key"
      :class="{ active: activeKey === artifact.key }"
      @tap="$emit('select', artifact.key)"
    >
      <text class="home-artifact-tab-title">{{ artifact.title }}</text>
      <text class="home-artifact-tab-sub">{{ artifact.summary }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  artifacts: { type: Array, default: () => [] },
  activeKey: { type: String, default: '' },
  summaryActive: { type: Boolean, default: false },
  showSummary: { type: Boolean, default: false },
})

defineEmits(['select'])
</script>

<style scoped>
.home-artifact-switcher { display: grid; grid-template-columns: repeat(auto-fit, minmax(112px, 1fr)); gap: 8px; overflow: visible; padding: 2px 0 10px; margin-bottom: 10px; contain: layout; }
.home-artifact-switcher::-webkit-scrollbar { display: none; }
.home-artifact-tab { min-width: 0; padding: 8px 9px; border-radius: 12px; border: 1px solid rgba(178,149,93,.14); background: rgba(255,255,255,.04); cursor: pointer; box-sizing: border-box; }
.home-artifact-tab.active { border-color: rgba(178,149,93,.48); background: rgba(178,149,93,.12); box-shadow: inset 0 1px 0 rgba(255,255,255,.08); }
.home-artifact-tab.conclusion { border-color: rgba(120,150,110,.24); }
.home-artifact-tab-title { display: block; color: var(--text-1); font-size: .76rem; font-weight: 800; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.home-artifact-tab-sub { display: block; margin-top: 3px; color: var(--text-3); font-size: .62rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

@media (max-width: 520px) {
  .home-artifact-switcher { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px; }
  .home-artifact-tab { min-width: 0; max-width: none; padding: 7px 8px; }
  .home-artifact-tab-title { font-size: .7rem; }
  .home-artifact-tab-sub { font-size: .56rem; }
}
</style>
