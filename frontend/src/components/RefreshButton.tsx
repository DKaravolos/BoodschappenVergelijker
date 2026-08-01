/** Triggers a Scrape; shows a spinner label while the request is in flight. */
export function RefreshButton({
  busy,
  onClick,
}: {
  busy: boolean
  onClick: () => void
}) {
  return (
    <button
      type="button"
      className="refresh-btn"
      onClick={onClick}
      disabled={busy}
    >
      <span className={busy ? 'spinner spinning' : 'spinner'} aria-hidden="true">
        ⟳
      </span>
      {busy ? 'Bezig met verversen…' : 'Ververs prijzen'}
    </button>
  )
}
