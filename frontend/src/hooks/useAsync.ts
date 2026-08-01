import { useEffect, useRef, useState } from 'react'

export interface AsyncState<T> {
  data: T | null
  loading: boolean
  error: string | null
  reload: () => void
}

/**
 * Run an async fetch and expose loading/error/data plus a manual `reload`.
 * Re-runs whenever an entry in `deps` changes. In-flight results are dropped
 * if the inputs change before they resolve (last-write-wins).
 */
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): AsyncState<T> {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [nonce, setNonce] = useState(0)

  // Always call the latest `fn` without making it an effect dependency.
  const fnRef = useRef(fn)
  fnRef.current = fn

  // A stable, statically-checkable key derived from the caller's deps.
  const depsKey = JSON.stringify(deps)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)
    fnRef
      .current()
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err))
          setData(null)
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [depsKey, nonce])

  return { data, loading, error, reload: () => setNonce((n) => n + 1) }
}
