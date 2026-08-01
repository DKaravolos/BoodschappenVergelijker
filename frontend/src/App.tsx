import { useState } from 'react'
import type { ProductComparison } from './types'
import { api } from './api/client'
import { useAsync } from './hooks/useAsync'
import { RefreshButton } from './components/RefreshButton'
import { ScrapeStatus } from './components/ScrapeStatus'
import { Compare } from './pages/Compare'
import { Discounts } from './pages/Discounts'
import { Favourites } from './pages/Favourites'
import './App.css'

type Tab = 'compare' | 'discounts' | 'favourites'

const TABS: { id: Tab; label: string }[] = [
  { id: 'compare', label: 'Vergelijken' },
  { id: 'discounts', label: 'Aanbiedingen' },
  { id: 'favourites', label: 'Favorieten' },
]

function App() {
  const [tab, setTab] = useState<Tab>('compare')
  const [refreshToken, setRefreshToken] = useState(0)
  const [scraping, setScraping] = useState(false)

  const status = useAsync(() => api.getScrapeStatus(), [refreshToken])

  function bumpData() {
    setRefreshToken((n) => n + 1)
  }

  async function handleRefresh() {
    setScraping(true)
    try {
      await api.triggerScrape()
      bumpData()
    } finally {
      setScraping(false)
    }
  }

  async function handleToggleFavourite(product: ProductComparison) {
    if (product.is_favourite) {
      await api.removeFavourite(product.id)
    } else {
      await api.addFavourite(product.id)
    }
    bumpData()
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="header-top">
          <h1>BoodschappenApp</h1>
          <RefreshButton busy={scraping} onClick={handleRefresh} />
        </div>
        <ScrapeStatus statuses={status.data ?? []} />
        <nav className="tabs">
          {TABS.map((entry) => (
            <button
              key={entry.id}
              type="button"
              className={tab === entry.id ? 'tab active' : 'tab'}
              onClick={() => setTab(entry.id)}
            >
              {entry.label}
            </button>
          ))}
        </nav>
      </header>

      <div className="app-content">
        {tab === 'compare' && (
          <Compare
            refreshToken={refreshToken}
            onToggleFavourite={handleToggleFavourite}
          />
        )}
        {tab === 'discounts' && <Discounts refreshToken={refreshToken} />}
        {tab === 'favourites' && (
          <Favourites
            refreshToken={refreshToken}
            onToggleFavourite={handleToggleFavourite}
          />
        )}
      </div>
    </div>
  )
}

export default App
