import type { ProductComparison, Supermarket, SupermarketListing } from '../types'
import { SUPERMARKETS, SUPERMARKET_LABELS } from '../types'
import { FavouriteButton } from './FavouriteButton'
import { PriceCell } from './PriceCell'

/**
 * The cross-Supermarket comparison table: one row per Product, one column per
 * Supermarket. Reused by both the Compare and Favourites pages.
 */
export function ComparisonTable({
  products,
  onToggleFavourite,
}: {
  products: ProductComparison[]
  onToggleFavourite: (product: ProductComparison) => void
}) {
  return (
    <div className="table-scroll">
      <table className="comparison">
        <thead>
          <tr>
            <th className="product-col">Product</th>
            {SUPERMARKETS.map((market) => (
              <th key={market}>{SUPERMARKET_LABELS[market]}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {products.map((product) => (
            <tr key={product.id}>
              <td className="product-col">
                <div className="product-head">
                  <FavouriteButton
                    active={product.is_favourite}
                    onToggle={() => onToggleFavourite(product)}
                  />
                  <div>
                    <div className="brand">{product.brand}</div>
                    <div className="name">{product.name}</div>
                    <div className="pack">{product.pack_size}</div>
                  </div>
                </div>
              </td>
              {SUPERMARKETS.map((market) => (
                <td key={market}>
                  <PriceCell listings={listingsFor(product, market)} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function listingsFor(
  product: ProductComparison,
  market: Supermarket,
): SupermarketListing[] {
  return product.listings.filter((listing) => listing.supermarket === market)
}
