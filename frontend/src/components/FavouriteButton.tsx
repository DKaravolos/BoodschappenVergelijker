/** A star toggle that marks/unmarks a Product as a Favourite. */
export function FavouriteButton({
  active,
  onToggle,
}: {
  active: boolean
  onToggle: () => void
}) {
  return (
    <button
      type="button"
      className={active ? 'fav-btn active' : 'fav-btn'}
      aria-pressed={active}
      aria-label={active ? 'Verwijder uit favorieten' : 'Voeg toe aan favorieten'}
      title={active ? 'Verwijder uit favorieten' : 'Voeg toe aan favorieten'}
      onClick={onToggle}
    >
      {active ? '★' : '☆'}
    </button>
  )
}
