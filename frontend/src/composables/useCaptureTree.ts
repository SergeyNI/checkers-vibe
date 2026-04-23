import type { Ref } from 'vue'
import type { Cell, CaptureChain } from '../types'

export function useCaptureTree(captureChains: Ref<Record<string, CaptureChain[]>>) {
  // Повертає дозволені наступні клітинки для фігури що починає серію
  function getFirstStepTargets(row: number, col: number): Cell[] {
    const chains = captureChains.value[`${row},${col}`] ?? []
    const seen = new Set<string>()
    const result: Cell[] = []
    for (const chain of chains) {
      const next = chain.path[0]
      if (!next) continue
      const key = `${next.row},${next.col}`
      if (!seen.has(key)) {
        seen.add(key)
        result.push(next)
      }
    }
    return result
  }

  // Після першого стрибка — знаходить наступні кроки в обраному ланцюжку
  function getNextStepTargets(
    pieceRow: number,
    pieceCol: number,
    completedPath: Cell[],
  ): Cell[] {
    const chains = captureChains.value[`${pieceRow},${pieceCol}`] ?? []
    const step = completedPath.length
    const seen = new Set<string>()
    const result: Cell[] = []

    for (const chain of chains) {
      if (chain.path.length <= step) continue
      // перевіряємо що вже пройдені кроки збігаються
      const matches = completedPath.every(
        (c, i) => chain.path[i]?.row === c.row && chain.path[i]?.col === c.col,
      )
      if (!matches) continue
      const next = chain.path[step]
      const key = `${next.row},${next.col}`
      if (!seen.has(key)) {
        seen.add(key)
        result.push(next)
      }
    }
    return result
  }

  return { getFirstStepTargets, getNextStepTargets }
}
