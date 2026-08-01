import type { Supermarket } from '../types'
import { SUPERMARKETS, SUPERMARKET_LABELS } from '../types'
import { api } from '../api/client'
import { formatPrice } from '../format'
import { useAsync } from '../hooks/useAsync'
import { AsyncBoundary } from '../components/AsyncBoundary'

/**
 * Weekmand: the cheapest place to do the whole weekly shop. Sums each
 * Favourite's best price per Supermarket and highlights the cheapest Supermarket
 * that stocks the entire basket.
 */
export function Basket({ refreshToken }: { refreshToken: number }) {
  const basket = useAsync(() => api.getBasket(), [refreshToken])
  const data = basket.data

  return (
    <AsyncBoundary
      loading={basket.loading}
      error={basket.error}
      empty={data !== null && data.favourite_count === 0}
      emptyMessage="Nog geen favorieten. Markeer producten met ☆ om je weekmand samen te stellen."
    >
      {data && (
        <div className="basket">
          <Headline
            cheapest={data.cheapest_complete}
            total={
              data.totals.find((t) => t.supermarket === data.cheapest_complete)
                ?.total ?? null
            }
          />

          <div className="table-scroll">
            <table className="comparison basket-table">
              <thead>
                <tr>
                  <th className="product-col">Product</th>
                  {SUPERMARKETS.map((market) => (
                    <th key={market}>{SUPERMARKET_LABELS[market]}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.products.map((product) => (
                  <tr key={product.product_id}>
                    <td className="product-col">
                      <div className="brand">{product.brand}</div>
                      <div className="name">{product.name}</div>
                      <div className="pack">{product.pack_size}</div>
                    </td>
                    {SUPERMARKETS.map((market) => (
                      <td
                        key={market}
                        className={
                          product.cheapest === market ? 'price-num cheapest' : 'price-num'
                        }
                      >
                        {product.prices[market] === null
                          ? '—'
                          : formatPrice(product.prices[market] as number)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr className="totals-row">
                  <th className="product-col">Totaal</th>
                  {SUPERMARKETS.map((market) => {
                    const total = data.totals.find((t) => t.supermarket === market)
                    if (!total) return <td key={market} />
                    const winner = data.cheapest_complete === market
                    return (
                      <td
                        key={market}
                        className={`price-num total-cell${winner ? ' winner' : ''}${
                          total.complete ? ' complete' : ''
                        }`}
                      >
                        <span className="total-amount">{formatPrice(total.total)}</span>
                        <span className="total-coverage">
                          {total.complete
                            ? 'compleet'
                            : `${total.available_count}/${data.favourite_count}`}
                        </span>
                      </td>
                    )
                  })}
                </tr>
              </tfoot>
            </table>
          </div>
        </div>
      )}
    </AsyncBoundary>
  )
}

function Headline({
  cheapest,
  total,
}: {
  cheapest: Supermarket | null
  total: number | null
}) {
  if (cheapest === null || total === null) {
    return (
      <div className="basket-headline none">
        <span className="headline-label">Volledige weekmand</span>
        <span className="headline-note">
          Geen enkele supermarkt heeft al je favorieten op voorraad. Bekijk de
          totalen hieronder voor de beste gedeeltelijke mand.
        </span>
      </div>
    )
  }
  return (
    <div className="basket-headline">
      <span className="headline-label">Goedkoopste volledige weekmand</span>
      <span className="headline-market">{SUPERMARKET_LABELS[cheapest]}</span>
      <span className="headline-total">{formatPrice(total)}</span>
    </div>
  )
}
