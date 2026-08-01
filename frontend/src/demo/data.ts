// Fake dataset for the standalone demo artifact (no backend). Mirrors the shapes
// the real backend returns. Price mapping follows the app's conventions:
//   - AH promotions are Bonuskaart-only  -> loyalty_price (never sale_price)
//   - Jumbo / Vomar / Dekamarkt promos are all-shopper -> sale_price
//   - Vomar / Dekamarkt have no loyalty programme -> loyalty_price always null

import type {
  ProductComparison,
  Supermarket,
  SupermarketListing,
  SupermarketStatus,
} from '../types'

const FRESH = '2026-07-31T08:00:00'
const STALE = '2026-07-30T08:00:00'

// [supermarket, storeName, regular, sale|null, loyalty|null, scrapedAt?]
type Row = [Supermarket, string, number, number | null, number | null, string?]

let _lid = 0
function listings(rows: Row[]): SupermarketListing[] {
  return rows.map(([supermarket, store_name, regular, sale, loyalty, scraped]) => ({
    listing_id: ++_lid,
    supermarket,
    store_name,
    store_url: null,
    scraped_at: scraped ?? FRESH,
    regular_price: regular,
    sale_price: sale,
    loyalty_price: loyalty,
  }))
}

interface Source {
  brand: string
  name: string
  pack: string
  rows: Row[]
}

const SOURCE: Source[] = [
  {
    brand: 'Vivera',
    name: 'Kipstukjes',
    pack: '200g',
    rows: [
      ['ah', 'Vivera Kipstukjes 200g', 2.99, null, 1.99],
      ['jumbo', 'Vivera Kipstukjes', 2.79, 1.99, null],
      ['vomar', 'Vivera Kip Stukjes', 2.89, null, null],
      ['dekamarkt', 'Vivera Kipstukjes', 2.95, null, null, STALE],
    ],
  },
  {
    brand: 'Vivera',
    name: 'Shoarma Reepjes',
    pack: '175g',
    rows: [
      ['ah', 'Vivera Shoarma 175g', 2.79, null, null],
      ['jumbo', 'Vivera Shoarmareepjes', 2.69, null, null],
      ['dekamarkt', 'Vivera Shoarmareepjes', 2.69, 2.19, null, STALE],
    ],
  },
  {
    brand: 'Vivera',
    name: 'Vegan Gehakt',
    pack: '200g',
    rows: [
      ['ah', 'Vivera Vegan Gehakt 200g', 2.89, null, null],
      ['vomar', 'Vivera Gehakt', 2.99, null, null],
    ],
  },
  {
    brand: 'Garden Gourmet',
    name: 'Schnitzel',
    pack: '180g',
    rows: [
      ['ah', 'Garden Gourmet Schnitzel', 3.49, null, null],
      ['jumbo', 'Garden Gourmet Schnitzel 180g', 3.39, null, null],
      ['vomar', 'GG Schnitzel', 3.59, null, null],
      ['dekamarkt', 'Garden Gourmet Schnitzel', 3.29, null, null, STALE],
    ],
  },
  {
    brand: 'Garden Gourmet',
    name: 'Vegetarische Gehaktballen',
    pack: '200g',
    rows: [
      ['ah', 'Garden Gourmet Gehaktballen', 3.29, null, 2.63],
      ['jumbo', 'Garden Gourmet Vega Gehaktballen', 3.19, null, null],
    ],
  },
  {
    brand: 'De Vegetarische Slager',
    name: 'Gerookte Spekjes',
    pack: '100g',
    rows: [
      ['ah', 'De Vegetarische Slager Spekjes', 2.49, null, null],
      ['jumbo', 'Vegetarische Slager Gerookte Spekjes', 2.55, 1.99, null],
      ['vomar', 'Veg. Slager Spekjes', 2.59, null, null],
    ],
  },
  {
    brand: 'De Vegetarische Slager',
    name: 'NoBeef Burger',
    pack: '2 stuks',
    rows: [
      ['ah', 'De Vegetarische Slager NoBeefburger', 3.19, null, null],
      ['dekamarkt', 'Veg. Slager NoBeef Burger', 3.09, null, null, STALE],
    ],
  },
  {
    brand: 'Beyond Meat',
    name: 'Burger',
    pack: '226g',
    rows: [
      ['ah', 'Beyond Meat Burger', 4.69, null, 3.99],
      ['jumbo', 'Beyond Burger 226g', 4.49, 3.49, null],
      ['dekamarkt', 'Beyond Meat Burger', 4.59, null, null, STALE],
    ],
  },
  {
    brand: 'Quorn',
    name: 'Vegan Nuggets',
    pack: '300g',
    rows: [
      ['ah', 'Quorn Vegan Nuggets', 3.99, null, null],
      ['jumbo', 'Quorn Vegan Nuggets 300g', 3.89, 2.99, null],
      ['vomar', 'Quorn Nuggets', 4.05, null, null],
    ],
  },
  {
    brand: 'Quorn',
    name: 'Filet',
    pack: '2 stuks',
    rows: [
      ['ah', 'Quorn Filet', 3.49, null, null],
      ['dekamarkt', 'Quorn Filet', 3.39, null, null, STALE],
    ],
  },
  {
    brand: 'Valess',
    name: 'Schnitzel Kaas',
    pack: '2 stuks',
    rows: [
      ['ah', 'Valess Schnitzel Kaas', 3.29, null, null],
      ['jumbo', 'Valess Schnitzel Kaas 2st', 3.35, null, null],
      ['vomar', 'Valess Schnitzel', 3.39, null, null],
      ['dekamarkt', 'Valess Schnitzel Kaas', 3.25, null, null, STALE],
    ],
  },
  {
    brand: 'AH Terra',
    name: 'Groenteballetjes',
    pack: '200g',
    rows: [['ah', 'AH Terra Groenteballetjes', 2.19, null, 1.75]],
  },
  {
    brand: 'Jumbo',
    name: 'Meatless Kipstukjes',
    pack: '200g',
    rows: [['jumbo', 'Jumbo Meatless Kipstukjes', 1.99, null, null]],
  },
]

export const DEMO_PRODUCTS: ProductComparison[] = SOURCE.map((src, index) => ({
  id: index + 1,
  brand: src.brand,
  name: src.name,
  pack_size: src.pack,
  is_favourite: false,
  listings: listings(src.rows),
}))

export const DEMO_STATUSES: SupermarketStatus[] = [
  { supermarket: 'ah', last_scraped_at: FRESH, status: 'completed', error_message: null },
  { supermarket: 'jumbo', last_scraped_at: FRESH, status: 'completed', error_message: null },
  { supermarket: 'vomar', last_scraped_at: FRESH, status: 'completed', error_message: null },
  {
    supermarket: 'dekamarkt',
    last_scraped_at: STALE,
    status: 'failed',
    error_message: 'Timeout na 20s',
  },
]
