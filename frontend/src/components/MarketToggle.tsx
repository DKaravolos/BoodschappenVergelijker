import type { Supermarket } from '../types'
import { SUPERMARKETS, SUPERMARKET_LABELS } from '../types'

/** "Alle" + per-Supermarket filter chips for the Discounts tab. */
export function MarketToggle({
  selected,
  onSelect,
}: {
  selected: Supermarket | null
  onSelect: (market: Supermarket | null) => void
}) {
  return (
    <div className="market-toggle" role="group" aria-label="Filter op supermarkt">
      <button
        type="button"
        className={selected === null ? 'chip active' : 'chip'}
        onClick={() => onSelect(null)}
      >
        Alle
      </button>
      {SUPERMARKETS.map((market) => (
        <button
          key={market}
          type="button"
          className={selected === market ? 'chip active' : 'chip'}
          onClick={() => onSelect(market)}
        >
          {SUPERMARKET_LABELS[market]}
        </button>
      ))}
    </div>
  )
}
