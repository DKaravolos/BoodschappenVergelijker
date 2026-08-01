// TypeScript mirror of the backend Pydantic response models (backend/models.py).

export type Supermarket = 'ah' | 'jumbo' | 'vomar' | 'dekamarkt'

export const SUPERMARKETS: Supermarket[] = ['ah', 'jumbo', 'vomar', 'dekamarkt']

export const SUPERMARKET_LABELS: Record<Supermarket, string> = {
  ah: 'Albert Heijn',
  jumbo: 'Jumbo',
  vomar: 'Vomar',
  dekamarkt: 'Dekamarkt',
}

export interface SupermarketListing {
  listing_id: number
  supermarket: Supermarket
  store_name: string
  store_url: string | null
  scraped_at: string
  regular_price: number
  sale_price: number | null
  loyalty_price: number | null
}

export interface ProductComparison {
  id: number
  brand: string
  name: string
  pack_size: string
  is_favourite: boolean
  listings: SupermarketListing[]
}

export interface Discount {
  listing_id: number
  product_id: number
  brand: string
  name: string
  pack_size: string
  supermarket: Supermarket
  store_name: string
  scraped_at: string
  regular_price: number
  sale_price: number | null
  loyalty_price: number | null
  best_price: number
  savings: number
  savings_pct: number
}

export interface SupermarketStatus {
  supermarket: Supermarket
  last_scraped_at: string | null
  status: string | null
  error_message: string | null
}

export interface ScrapeResult {
  status: string
  statuses: SupermarketStatus[]
}

export interface BasketProduct {
  product_id: number
  brand: string
  name: string
  pack_size: string
  prices: Record<Supermarket, number | null>
  cheapest: Supermarket | null
}

export interface SupermarketTotal {
  supermarket: Supermarket
  total: number
  available_count: number
  complete: boolean
}

export interface Basket {
  favourite_count: number
  products: BasketProduct[]
  totals: SupermarketTotal[]
  cheapest_complete: Supermarket | null
}
