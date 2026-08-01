# Append-only Price Snapshots instead of current-price-only storage

Each Scrape appends new Price Snapshots rather than overwriting existing prices. This preserves history, enabling detection of "sale theatre" (where supermarkets raise the Regular Price before marking a Sale Price) and long-term price trend analysis. The cost is a larger SQLite file over time, which is negligible for a local personal app. Overwriting would have been simpler but destroys the data needed to interpret whether a Discount is genuine.
