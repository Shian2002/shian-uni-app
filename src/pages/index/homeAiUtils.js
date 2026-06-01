export function readStorageJson(key, fallback) {
  try {
    const raw = uni.getStorageSync(key)
    if (!raw) return fallback
    return typeof raw === 'string' ? JSON.parse(raw) : raw
  } catch (_) {
    return fallback
  }
}

export function writeStorageJson(key, value) {
  try {
    uni.setStorageSync(key, JSON.stringify(value))
  } catch (_) {}
}

export function htmlEscape(value) {
  return String(value == null ? '' : value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

export const BAZI_RELATION_LABELS = {
  gan_he: '天干合',
  gan_chong: '天干冲',
  zhi_san_he: '地支三合',
  zhi_liu_he: '地支六合',
  zhi_ban_he: '地支半合',
  zhi_an_he: '地支暗合',
  zhi_liu_chong: '地支六冲',
  zhi_liu_hai: '地支六害',
  zhi_liu_po: '地支相破',
  zhi_san_xing: '地支三刑',
  zhi_san_hui: '地支三会',
}

export function sanitizeArtifactAnalysisText(text) {
  let result = String(text || '')
  Object.keys(BAZI_RELATION_LABELS).forEach(function(key) {
    result = result.replace(new RegExp(key, 'g'), BAZI_RELATION_LABELS[key])
  })
  return result
}

export function pillarText(pillar) {
  if (!pillar) return ''
  return pillar.gan_zhi || ((pillar.gan || '') + (pillar.zhi || '')) || String(pillar)
}
