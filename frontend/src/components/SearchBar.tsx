/** Free-text search box for the compare page (debounced by the caller). */
export function SearchBar({
  value,
  onChange,
}: {
  value: string
  onChange: (value: string) => void
}) {
  return (
    <div className="search-bar">
      <input
        type="search"
        placeholder="Zoek op product of merk…"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-label="Zoek producten"
      />
    </div>
  )
}
