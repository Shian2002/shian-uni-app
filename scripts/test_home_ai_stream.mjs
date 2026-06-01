import assert from 'node:assert/strict'
import {
  shouldSyncStreamContent,
  smoothTextSpeed,
  takeSmoothTextChunk,
} from '../src/pages/index/useHomeAiStream.js'

assert.deepEqual(takeSmoothTextChunk('abcdef', 3, 2), {
  chunk: 'ab',
  rest: 'cdef',
  count: 2,
})

assert.deepEqual(takeSmoothTextChunk('甲乙丙丁', 10, 1), {
  chunk: '甲',
  rest: '乙丙丁',
  count: 1,
})

assert.deepEqual(takeSmoothTextChunk('A😀B', 2, 2), {
  chunk: 'A😀',
  rest: 'B',
  count: 2,
})

assert.equal(smoothTextSpeed(80), 88)
assert.equal(smoothTextSpeed(260), 108)
assert.equal(smoothTextSpeed(800), 140)
assert.equal(smoothTextSpeed(1600), 180)

assert.equal(shouldSyncStreamContent(1000, 900, 160, false), false)
assert.equal(shouldSyncStreamContent(1100, 900, 160, false), true)
assert.equal(shouldSyncStreamContent(1000, 999, 160, true), true)

console.log('[OK] home AI stream utilities')
