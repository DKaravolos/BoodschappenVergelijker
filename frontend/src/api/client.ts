// Typed client for the BoodschappenApp backend. All calls go through the Vite
// dev proxy at /api (see vite.config.ts).

import type {
  Discount,
  ProductComparison,
  ScrapeResult,
  Supermarket,
  SupermarketStatus,
} from '../types'

const BASE = '/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, init)
  if (!resp.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed: ${resp.status}`)
  }
  if (resp.status === 204) {
    return undefined as T
  }
  return resp.json() as Promise<T>
}

function query(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter(
    (entry): entry is [string, string] => Boolean(entry[1]),
  )
  if (entries.length === 0) return ''
  return `?${new URLSearchParams(entries).toString()}`
}

export const api = {
  getProducts(q?: string, brand?: string): Promise<ProductComparison[]> {
    return request(`/products${query({ q, brand })}`)
  },

  getBrands(): Promise<string[]> {
    return request('/brands')
  },

  getDiscounts(supermarket?: Supermarket): Promise<Discount[]> {
    return request(`/discounts${query({ supermarket })}`)
  },

  getFavourites(): Promise<ProductComparison[]> {
    return request('/favourites')
  },

  addFavourite(productId: number): Promise<void> {
    return request(`/favourites/${productId}`, { method: 'POST' })
  },

  removeFavourite(productId: number): Promise<void> {
    return request(`/favourites/${productId}`, { method: 'DELETE' })
  },

  triggerScrape(): Promise<ScrapeResult> {
    return request('/scrape', { method: 'POST' })
  },

  getScrapeStatus(): Promise<SupermarketStatus[]> {
    return request('/scrape/status')
  },
}
