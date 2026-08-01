import { useState } from 'react'
import type { ProductComparison } from '../types'
import { api } from '../api/client'
import { useAsync } from '../hooks/useAsync'
import { useDebounce } from '../hooks/useDebounce'
import { AsyncBoundary } from '../components/AsyncBoundary'
import { BrandFilter } from '../components/BrandFilter'
import { ComparisonTable } from '../components/ComparisonTable'
import { SearchBar } from '../components/SearchBar'

/** Main page: search + brand filter + cross-Supermarket comparison table. */
export function Compare({
  refreshToken,
  onToggleFavourite,
}: {
  refreshToken: number
  onToggleFavourite: (product: ProductComparison) => void
}) {
  const [search, setSearch] = useState('')
  const [brand, setBrand] = useState<string | null>(null)
  const debouncedSearch = useDebounce(search)

  const brands = useAsync(() => api.getBrands(), [refreshToken])
  const products = useAsync(
    () => api.getProducts(debouncedSearch || undefined, brand ?? undefined),
    [debouncedSearch, brand, refreshToken],
  )

  return (
    <div className="compare">
      <SearchBar value={search} onChange={setSearch} />
      <div className="compare-body">
        <aside>
          <BrandFilter
            brands={brands.data ?? []}
            selected={brand}
            onSelect={setBrand}
          />
        </aside>
        <main>
          <AsyncBoundary
            loading={products.loading}
            error={products.error}
            empty={(products.data ?? []).length === 0}
            emptyMessage="Geen producten gevonden. Ververs de prijzen of pas je zoekopdracht aan."
          >
            <ComparisonTable
              products={products.data ?? []}
              onToggleFavourite={onToggleFavourite}
            />
          </AsyncBoundary>
        </main>
      </div>
    </div>
  )
}
