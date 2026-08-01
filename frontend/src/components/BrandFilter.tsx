/** Sidebar list of brands; selecting one filters the comparison table. */
export function BrandFilter({
  brands,
  selected,
  onSelect,
}: {
  brands: string[]
  selected: string | null
  onSelect: (brand: string | null) => void
}) {
  return (
    <nav className="brand-filter" aria-label="Filter op merk">
      <button
        type="button"
        className={selected === null ? 'brand active' : 'brand'}
        onClick={() => onSelect(null)}
      >
        Alle merken
      </button>
      {brands.map((brand) => (
        <button
          key={brand}
          type="button"
          className={selected === brand ? 'brand active' : 'brand'}
          onClick={() => onSelect(brand)}
        >
          {brand}
        </button>
      ))}
    </nav>
  )
}
