# Product matching via brand + fuzzy name instead of EAN codes

Supermarket APIs sometimes expose EAN barcodes, which would give exact product identity across stores. We chose not to rely on them because EAN availability is inconsistent across the four supermarkets, and scraping it reliably would require extra work per supermarket with frequent breakage. Instead, Products are matched across Listings by normalizing Brand and product name and applying fuzzy string matching. This means the same real-world product (e.g., "Vivera Schnitzel 200g") is linked across stores even when store names differ slightly. The trade-off is occasional false matches or missed matches at the edges, which users can observe but not currently correct — acceptable for a local personal tool.

## Considered Options

- **EAN codes** — precise but inconsistently exposed and fragile to scraper changes
- **Manual mapping** — accurate but requires ongoing maintenance
- **Brand + fuzzy name** (chosen) — automated, good enough coverage, low maintenance
