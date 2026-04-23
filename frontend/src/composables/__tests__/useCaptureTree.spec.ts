import { describe, it, expect } from 'vitest'
import { ref } from 'vue'
import { useCaptureTree } from '../useCaptureTree'
import type { CaptureChain } from '../../types'

function setup(chains: Record<string, CaptureChain[]>) {
  return useCaptureTree(ref(chains))
}

describe('useCaptureTree', () => {
  describe('getFirstStepTargets', () => {
    it('returns first cell of each unique chain', () => {
      const tree = setup({
        '2,2': [
          { path: [{ row: 4, col: 4 }, { row: 6, col: 2 }], captured: [{ row: 3, col: 3 }, { row: 5, col: 3 }] },
          { path: [{ row: 4, col: 0 }], captured: [{ row: 3, col: 1 }] },
        ],
      })
      const targets = tree.getFirstStepTargets(2, 2)
      expect(targets).toHaveLength(2)
      expect(targets).toContainEqual({ row: 4, col: 4 })
      expect(targets).toContainEqual({ row: 4, col: 0 })
    })

    it('deduplicates identical first-step targets', () => {
      const tree = setup({
        '2,2': [
          { path: [{ row: 4, col: 4 }], captured: [{ row: 3, col: 3 }] },
          { path: [{ row: 4, col: 4 }], captured: [{ row: 3, col: 3 }] },
        ],
      })
      expect(tree.getFirstStepTargets(2, 2)).toHaveLength(1)
    })

    it('returns empty array for unknown cell', () => {
      const tree = setup({})
      expect(tree.getFirstStepTargets(0, 0)).toEqual([])
    })

    it('skips chains with empty path', () => {
      const tree = setup({ '2,2': [{ path: [], captured: [] }] })
      expect(tree.getFirstStepTargets(2, 2)).toEqual([])
    })
  })

  describe('getNextStepTargets', () => {
    it('returns next cells matching completed path', () => {
      const tree = setup({
        '2,2': [
          {
            path: [{ row: 4, col: 4 }, { row: 6, col: 2 }],
            captured: [{ row: 3, col: 3 }, { row: 5, col: 3 }],
          },
          {
            path: [{ row: 4, col: 4 }, { row: 6, col: 6 }],
            captured: [{ row: 3, col: 3 }, { row: 5, col: 5 }],
          },
          {
            path: [{ row: 4, col: 0 }],
            captured: [{ row: 3, col: 1 }],
          },
        ],
      })
      const next = tree.getNextStepTargets(2, 2, [{ row: 4, col: 4 }])
      expect(next).toHaveLength(2)
      expect(next).toContainEqual({ row: 6, col: 2 })
      expect(next).toContainEqual({ row: 6, col: 6 })
    })

    it('excludes chains with non-matching completed path', () => {
      const tree = setup({
        '2,2': [
          {
            path: [{ row: 4, col: 4 }, { row: 6, col: 2 }],
            captured: [{ row: 3, col: 3 }, { row: 5, col: 3 }],
          },
        ],
      })
      // wrong first step
      const next = tree.getNextStepTargets(2, 2, [{ row: 4, col: 0 }])
      expect(next).toEqual([])
    })

    it('returns empty when completed path exceeds chain length', () => {
      const tree = setup({
        '2,2': [{ path: [{ row: 4, col: 4 }], captured: [{ row: 3, col: 3 }] }],
      })
      const next = tree.getNextStepTargets(2, 2, [{ row: 4, col: 4 }, { row: 6, col: 2 }])
      expect(next).toEqual([])
    })

    it('deduplicates identical next-step targets', () => {
      const tree = setup({
        '2,2': [
          {
            path: [{ row: 4, col: 4 }, { row: 6, col: 2 }],
            captured: [{ row: 3, col: 3 }, { row: 5, col: 3 }],
          },
          {
            path: [{ row: 4, col: 4 }, { row: 6, col: 2 }],
            captured: [{ row: 3, col: 3 }, { row: 5, col: 3 }],
          },
        ],
      })
      const next = tree.getNextStepTargets(2, 2, [{ row: 4, col: 4 }])
      expect(next).toHaveLength(1)
    })

    it('returns empty for unknown piece cell', () => {
      const tree = setup({})
      expect(tree.getNextStepTargets(5, 5, [{ row: 6, col: 6 }])).toEqual([])
    })
  })
})
