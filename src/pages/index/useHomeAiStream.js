export const HOME_AI_STREAM_DEFAULTS = {
  frameMs: 16,
  baseCps: 58,
  maxCps: 72,
  maxFrameChars: 1,
  reactiveSyncMs: 420,
}

export function smoothTextSpeed(queueLength, options) {
  const opts = Object.assign({}, HOME_AI_STREAM_DEFAULTS, options || {})
  if (queueLength > 1200) return opts.maxCps
  if (queueLength > 520) return 66
  if (queueLength > 180) return 62
  return opts.baseCps
}

export function takeSmoothTextChunk(queue, targetCount, maxFrameChars) {
  const chars = Array.from(queue || '')
  if (!chars.length) return { chunk: '', rest: '', count: 0 }
  const wanted = Math.max(1, Math.min(chars.length, maxFrameChars || HOME_AI_STREAM_DEFAULTS.maxFrameChars, targetCount || 1))
  const chunkChars = chars.slice(0, wanted)
  return {
    chunk: chunkChars.join(''),
    rest: chars.slice(wanted).join(''),
    count: chunkChars.length,
  }
}

export function shouldSyncStreamContent(now, lastSyncAt, minIntervalMs, done) {
  if (done) return true
  return Number(now || 0) - Number(lastSyncAt || 0) >= Number(minIntervalMs || HOME_AI_STREAM_DEFAULTS.reactiveSyncMs)
}
