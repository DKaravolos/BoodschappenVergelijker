import { useState } from 'react'
import type { Supermarket } from '../types'
import { api } from '../api/client'
import { useAsync } from '../hooks/useAsync'
import { AsyncBoundary } from '../components/AsyncBoundary'
import { DiscountList } from '../components/DiscountList'
import { MarketToggle } from '../components/MarketToggle'

/** Discounts tab: all active deals across Supermarkets, filterable. */
export function Discounts({ refreshToken }: { refreshToken: number }) {
  const [filter, setFilter] = useState<Supermarket | null>(null)
  const discounts = useAsync(
    () => api.getDiscounts(filter ?? undefined),
    [filter, refreshToken],
  )

  return (
    <div className="discounts">
      <MarketToggle selected={filter} onSelect={setFilter} />
      <AsyncBoundary
        loading={discounts.loading}
        error={discounts.error}
        empty={(discounts.data ?? []).length === 0}
        emptyMessage="Op dit moment zijn er geen aanbiedingen."
      >
        <DiscountList discounts={discounts.data ?? []} />
      </AsyncBoundary>
    </div>
  )
}
