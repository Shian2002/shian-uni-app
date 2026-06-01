export function createHomeAiDraftStorage(options) {
  const storageKey = options.storageKey
  const saveDelayMs = options.saveDelayMs || 300
  const maxAgeMs = options.maxAgeMs || 24 * 60 * 60 * 1000
  let timer = null

  function storageAvailable() {
    return typeof localStorage !== 'undefined'
  }

  function clearDraft() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    try {
      if (storageAvailable()) localStorage.removeItem(storageKey)
    } catch (_) {}
  }

  function saveNow() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
    try {
      if (!storageAvailable()) return
      const payload = options.getPayload()
      if (!payload || !Array.isArray(payload.messages) || !payload.messages.length) {
        localStorage.removeItem(storageKey)
        return
      }
      localStorage.setItem(storageKey, JSON.stringify(payload))
    } catch (_) {}
  }

  function scheduleSave() {
    if (timer) return
    timer = setTimeout(saveNow, saveDelayMs)
  }

  function restoreDraft() {
    try {
      if (!storageAvailable()) return false
      if (options.canRestore && !options.canRestore()) return false
      const raw = localStorage.getItem(storageKey)
      if (!raw) return false
      const draft = JSON.parse(raw)
      if (!draft || !Array.isArray(draft.messages) || !draft.messages.length) {
        clearDraft()
        return false
      }
      if (draft.updatedAt && Date.now() - Number(draft.updatedAt) > maxAgeMs) {
        clearDraft()
        return false
      }
      return !!options.applyDraft(draft)
    } catch (_) {
      return false
    }
  }

  function stop() {
    if (timer) {
      clearTimeout(timer)
      timer = null
    }
  }

  return {
    clearDraft,
    restoreDraft,
    saveNow,
    scheduleSave,
    stop,
  }
}
