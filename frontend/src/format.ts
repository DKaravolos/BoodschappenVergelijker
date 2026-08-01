// Locale-aware formatting helpers (Dutch), shared across components.

const euro = new Intl.NumberFormat('nl-NL', {
  style: 'currency',
  currency: 'EUR',
})

export function formatPrice(value: number): string {
  return euro.format(value)
}

const dateTime = new Intl.DateTimeFormat('nl-NL', {
  day: 'numeric',
  month: 'short',
  hour: '2-digit',
  minute: '2-digit',
})

/** Format an ISO8601 scrape timestamp, or a dash when there is none. */
export function formatTimestamp(iso: string | null): string {
  if (!iso) return '—'
  const parsed = new Date(iso)
  if (Number.isNaN(parsed.getTime())) return iso
  return dateTime.format(parsed)
}
