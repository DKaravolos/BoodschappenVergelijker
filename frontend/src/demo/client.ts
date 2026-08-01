// Demo implementation of the API client: serves the embedded fake dataset with
// client-side search/filter/discount logic, so the app runs with no backend.
// Favourites live in memory for the session (there is nothing to persist to).

import type {
  Basket,
  BasketProduct,
  Discount,
  ProductComparison,
  ScrapeResult,
  Supermarket,
  SupermarketListing,
  SupermarketTotal,
} from '../types'
import { SUPERMARKETS } from '../types'
import { DEMO_PRODUCTS, DEMO_STATUSES } from './data'

const favourites = new Set<number>()

function round(value: number, dp = 2): number {
  const factor = 10 ** dp
  return Math.round(value * factor) / factor
}

function withFavourite(product: ProductComparison): ProductComparison {
  return { ...product, is_favourite: favourites.has(product.id) }
}

function effectivePrice(listing: SupermarketListing): number {
  const active = [listing.regular_price]
  if (listing.sale_price !== null) active.push(listing.sale_price)
  if (listing.loyalty_price !== null) active.push(listing.loyalty_price)
  return Math.min(...active)
}

// Mirrors backend queries.get_basket over the in-memory favourites.
function buildBasket(): Basket {
  const favs = DEMO_PRODUCTS.filter((p) => favourites.has(p.id))
  const running: Record<Supermarket, { total: number; count: number }> = {
    ah: { total: 0, count: 0 },
    jumbo: { total: 0, count: 0 },
    vomar: { total: 0, count: 0 },
    dekamarkt: { total: 0, count: 0 },
  }

  const products: BasketProduct[] = favs.map((product) => {
    const prices = {} as Record<Supermarket, number | null>
    for (const market of SUPERMARKETS) {
      const listed = product.listings.filter((l) => l.supermarket === market)
      prices[market] = listed.length
        ? round(Math.min(...listed.map(effectivePrice)))
        : null
    }
    let cheapest: Supermarket | null = null
    for (const market of SUPERMARKETS) {
      const price = prices[market]
      if (price === null) continue
      running[market].total += price
      running[market].count += 1
      if (cheapest === null || price < (prices[cheapest] as number)) {
        cheapest = market
      }
    }
    return {
      product_id: product.id,
      brand: product.brand,
      name: product.name,
      pack_size: product.pack_size,
      prices,
      cheapest,
    }
  })

  const totals: SupermarketTotal[] = SUPERMARKETS.map((market) => ({
    supermarket: market,
    total: round(running[market].total),
    available_count: running[market].count,
    complete: favs.length > 0 && running[market].count === favs.length,
  }))

  const complete = totals.filter((t) => t.complete)
  const cheapest_complete = complete.length
    ? complete.reduce((a, b) => (b.total < a.total ? b : a)).supermarket
    : null

  return {
    favourite_count: favs.length,
    products,
    totals,
    cheapest_complete,
  }
}

// A tiny delay so loading states are exercised, like a real network call.
function resolve<T>(value: T): Promise<T> {
  return new Promise((done) => setTimeout(() => done(value), 120))
}

export const demoApi = {
  getProducts(q?: string, brand?: string): Promise<ProductComparison[]> {
    let list = DEMO_PRODUCTS.map(withFavourite)
    if (q) {
      const needle = q.toLowerCase()
      list = list.filter(
        (p) =>
          p.name.toLowerCase().includes(needle) ||
          p.brand.toLowerCase().includes(needle),
      )
    }
    if (brand) {
      list = list.filter((p) => p.brand.toLowerCase() === brand.toLowerCase())
    }
    return resolve(list)
  },

  getBrands(): Promise<string[]> {
    const brands = [...new Set(DEMO_PRODUCTS.map((p) => p.brand))]
    brands.sort((a, b) => a.localeCompare(b))
    return resolve(brands)
  },

  getDiscounts(supermarket?: Supermarket): Promise<Discount[]> {
    const out: Discount[] = []
    for (const product of DEMO_PRODUCTS) {
      for (const listing of product.listings) {
        if (supermarket && listing.supermarket !== supermarket) continue
        const active = [listing.sale_price, listing.loyalty_price].filter(
          (price): price is number =>
            price !== null && price < listing.regular_price,
        )
        if (active.length === 0) continue
        const best = Math.min(...active)
        const savings = round(listing.regular_price - best)
        out.push({
          listing_id: listing.listing_id,
          product_id: product.id,
          brand: product.brand,
          name: product.name,
          pack_size: product.pack_size,
          supermarket: listing.supermarket,
          store_name: listing.store_name,
          scraped_at: listing.scraped_at,
          regular_price: listing.regular_price,
          sale_price: listing.sale_price,
          loyalty_price: listing.loyalty_price,
          best_price: best,
          savings,
          savings_pct: round((savings / listing.regular_price) * 100, 1),
        })
      }
    }
    out.sort((a, b) => b.savings_pct - a.savings_pct)
    return resolve(out)
  },

  getFavourites(): Promise<ProductComparison[]> {
    return resolve(
      DEMO_PRODUCTS.filter((p) => favourites.has(p.id)).map(withFavourite),
    )
  },

  addFavourite(productId: number): Promise<void> {
    favourites.add(productId)
    return resolve<void>(undefined)
  },

  removeFavourite(productId: number): Promise<void> {
    favourites.delete(productId)
    return resolve<void>(undefined)
  },

  getBasket(): Promise<Basket> {
    return resolve(buildBasket())
  },

  triggerScrape(): Promise<ScrapeResult> {
    return resolve({ status: 'completed', statuses: DEMO_STATUSES })
  },

  getScrapeStatus() {
    return resolve(DEMO_STATUSES)
  },
}
