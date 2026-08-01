import type { SupermarketListing } from '../types'
import { formatPrice } from '../format'

/**
 * One Supermarket's price block inside the comparison table. Renders every
 * Listing for that Supermarket (multiple = variants), each showing the Regular
 * Price plus an active Sale or Loyalty Price when the latest snapshot has one.
 */
export function PriceCell({ listings }: { listings: SupermarketListing[] }) {
  if (listings.length === 0) {
    return <span className="not-available">Niet beschikbaar</span>
  }

  const showVariant = listings.length > 1
  return (
    <div className="price-cell">
      {listings.map((listing) => (
        <PriceBlock
          key={listing.listing_id}
          listing={listing}
          showVariant={showVariant}
        />
      ))}
    </div>
  )
}

function PriceBlock({
  listing,
  showVariant,
}: {
  listing: SupermarketListing
  showVariant: boolean
}) {
  const sale = discounted(listing.sale_price, listing.regular_price)
  const loyalty = discounted(listing.loyalty_price, listing.regular_price)
  const hasDeal = sale !== null || loyalty !== null

  return (
    <div className="price-block">
      {showVariant && <span className="variant">{listing.store_name}</span>}
      <span className={hasDeal ? 'regular struck' : 'regular'}>
        {formatPrice(listing.regular_price)}
      </span>
      {sale !== null && (
        <span className="deal sale">Aanbieding {formatPrice(sale)}</span>
      )}
      {loyalty !== null && (
        <span className="deal loyalty">Bonus {formatPrice(loyalty)}</span>
      )}
    </div>
  )
}

/** The price if it is a genuine discount below the Regular Price, else null. */
function discounted(price: number | null, regular: number): number | null {
  return price !== null && price < regular ? price : null
}
