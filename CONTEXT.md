# BoodschappenApp

A local app for comparing prices of vegetarian meat alternatives across four Dutch supermarkets: Albert Heijn, Jumbo, Vomar, and Dekamarkt. Prices are scraped and stored over time so users can track promotions and find the best deal.

## Language

### Products

**Product**:
A vegetarian meat alternative as a canonical, normalized entity — identified by brand, normalized name, and pack size. Pack size is part of identity: "Vivera Kipstukjes 200g" and "Vivera Kipstukjes 400g" are distinct Products. A Product exists independently of any supermarket; it represents the real-world item, not how any one store sells it.
_Avoid_: Item, article, canonical product

**Brand**:
The manufacturer of a Product (e.g., Vivera, De Vegetarische Slager, Garden Gourmet). The primary grouping key for Products.
_Avoid_: Manufacturer, producer, label

**Listing**:
A Product as stocked by a specific Supermarket. Has its own store-specific name, and is the entity prices are attached to. One Product may have zero or more Listings per Supermarket — multiple Listings from the same Supermarket represent variants (e.g., seasoned vs. unseasoned) and are shown together in the UI.
_Avoid_: Offer, store product, stock item

### Pricing

**Regular Price**:
The standard shelf price of a Listing, without any promotion or loyalty card requirement.
_Avoid_: Normal price, base price, original price

**Sale Price**:
A time-limited promotional price for a Listing, available to all shoppers. Corresponds to what Dutch supermarkets call "in de aanbieding".
_Avoid_: Discount price, promo price, deal price

**Loyalty Price**:
A reduced price for a Listing that requires the supermarket's loyalty card: AH Bonuskaart or Jumbo Extra's Kaart. Vomar and Dekamarkt have no loyalty programs, so their Listings never have a Loyalty Price.
_Avoid_: Card price, member price, bonus price

**Price Snapshot**:
The Regular Price, Sale Price (if active), and Loyalty Price (if active) for a Listing, captured at a specific point in time during a Scrape.
_Avoid_: Price record, price entry, price point

**Discount**:
A Listing where the current Sale Price or Loyalty Price is below the Regular Price. A Listing can have a Sale Discount, a Loyalty Discount, or both simultaneously.
_Avoid_: Deal, promotion, offer

**Favourite**:
A Product the user has marked for their regular weekly shop. Favourites are stored in the database and displayed in the Favourites tab, which shows the same cross-supermarket comparison as the Compare page but scoped to marked Products only.
_Avoid_: Saved item, bookmark, starred product

### Operations

**Supermarket**:
One of the four Dutch chains supported by this app: Albert Heijn, Jumbo, Vomar, Dekamarkt.
_Avoid_: Store, shop, retailer, chain

**Scrape**:
A single data-collection run for one or all Supermarkets. Produces a set of Price Snapshots timestamped to the moment the data was fetched. A Scrape can partially succeed — if one Supermarket fails, existing Price Snapshots for that Supermarket remain visible with their original timestamp so the user can see how stale the data is.
_Avoid_: Sync, refresh, fetch, pull
