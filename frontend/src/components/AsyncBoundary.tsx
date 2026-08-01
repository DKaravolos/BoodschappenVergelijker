import type { ReactNode } from 'react'

/** Renders loading / error / empty placeholders, or the children when ready. */
export function AsyncBoundary({
  loading,
  error,
  empty,
  emptyMessage,
  children,
}: {
  loading: boolean
  error: string | null
  empty: boolean
  emptyMessage: string
  children: ReactNode
}) {
  if (loading) return <div className="state loading">Laden…</div>
  if (error) return <div className="state error">Er ging iets mis: {error}</div>
  if (empty) return <div className="state empty">{emptyMessage}</div>
  return <>{children}</>
}
