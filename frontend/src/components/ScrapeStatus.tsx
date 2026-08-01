import type { SupermarketStatus } from '../types'
import { SUPERMARKET_LABELS } from '../types'
import { formatTimestamp } from '../format'

/**
 * Per-Supermarket freshness strip: last-updated timestamp plus a warning when
 * that Supermarket's most recent Scrape failed (stale data still shown).
 */
export function ScrapeStatus({ statuses }: { statuses: SupermarketStatus[] }) {
  return (
    <div className="scrape-status">
      {statuses.map((status) => (
        <div key={status.supermarket} className="status-item">
          <span className="status-market">
            {SUPERMARKET_LABELS[status.supermarket]}
          </span>
          <span className="status-time">
            {status.last_scraped_at
              ? `bijgewerkt ${formatTimestamp(status.last_scraped_at)}`
              : 'nog niet opgehaald'}
          </span>
          {status.status === 'failed' && (
            <span
              className="status-warn"
              title={status.error_message ?? 'Laatste scrape mislukt'}
            >
              ⚠ mislukt
            </span>
          )}
        </div>
      ))}
    </div>
  )
}
