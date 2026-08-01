import type { ProductComparison } from '../types'
import { api } from '../api/client'
import { useAsync } from '../hooks/useAsync'
import { AsyncBoundary } from '../components/AsyncBoundary'
import { ComparisonTable } from '../components/ComparisonTable'

/** Favourites tab: the same comparison table, scoped to marked Products. */
export function Favourites({
  refreshToken,
  onToggleFavourite,
}: {
  refreshToken: number
  onToggleFavourite: (product: ProductComparison) => void
}) {
  const favourites = useAsync(() => api.getFavourites(), [refreshToken])

  return (
    <AsyncBoundary
      loading={favourites.loading}
      error={favourites.error}
      empty={(favourites.data ?? []).length === 0}
      emptyMessage="Nog geen favorieten. Markeer producten met ☆ op de vergelijkpagina."
    >
      <ComparisonTable
        products={favourites.data ?? []}
        onToggleFavourite={onToggleFavourite}
      />
    </AsyncBoundary>
  )
}
