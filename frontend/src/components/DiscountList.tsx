import type { Discount } from '../types'
import { SUPERMARKET_LABELS } from '../types'
import { formatPrice } from '../format'

/** The list of Discount cards, already sorted by savings descending. */
export function DiscountList({ discounts }: { discounts: Discount[] }) {
  return (
    <ul className="discount-cards">
      {discounts.map((discount) => (
        <li key={discount.listing_id} className="discount-card">
          <div className="discount-badge">-{discount.savings_pct}%</div>
          <div className="discount-body">
            <div className="brand">{discount.brand}</div>
            <div className="name">{discount.name}</div>
            <div className="pack">
              {discount.pack_size} · {SUPERMARKET_LABELS[discount.supermarket]}
            </div>
            <div className="discount-prices">
              <span className="regular struck">
                {formatPrice(discount.regular_price)}
              </span>
              <span className="best">{formatPrice(discount.best_price)}</span>
              <span className="savings">
                bespaar {formatPrice(discount.savings)}
              </span>
            </div>
          </div>
        </li>
      ))}
    </ul>
  )
}
