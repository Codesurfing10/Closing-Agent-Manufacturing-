# Catalog Monitor — Distributor Listings + Pricing (Phase 1)

**Product:** LC-Flow Valve and Distribution Adaptor  
**Branch:** `feature/catalog-monitor-pricing`  
**Date:** 2026-09-26 PT  
**Related:** `DISTRIBUTOR_LISTING_TRACKER.md`, `inventory.csv`

Tracks industrial catalog / distributor listing **status** and **catalog pricing** inside Closing Agent. Does **not** submit portal forms, scrape distributor sites, or send emails.

No separate pricing sheet is attached for Phase 1. **List prices** come from inventory SKU `unit_price_usd` (`deliverables/inventory.csv` / `/inventory`):

| SKU | Material | List USD |
|-----|----------|----------|
| `LCP061000` | PC-ISO plastic | 145.38 |
| `LCSS61000` | 316L stainless | 558.28 |
| `LCA061000` | Aluminum AlSiMg | 1545.28 |

---

## New / ensured fields on `distributor_listings`

| Column | Type | Notes |
|--------|------|-------|
| `list_price_usd` | REAL | Channel reference list (seeded from `LCP061000` when present) |
| `map_price_usd` | REAL | Minimum advertised price (editable; null until set) |
| `target_catalog_price_usd` | REAL | Target catalog / **distributor_price** (editable) |
| `currency` | TEXT | Default `USD` |
| `last_status_check` | TEXT | ISO timestamp of last pricing/status touch |
| `campaign_notes` | TEXT | Freeform campaign notes |
| `sku_pricing` | TEXT (JSON) | Per-SKU `{sku, list_price_usd, map_price_usd, distributor_price_usd}` |

Existing status / channel fields unchanged (`status`, `priority`, `portal_url`, `skus`, etc.).

Migrations in `_migrate_db()` add these columns on existing SQLite files. Seed backfills empty pricing from inventory.

---

## Focus channels (UI filters)

Primary monitor filters: **Grainger**, **McMaster**, **MSC**, **Zoro**, **Thomasnet**, **Aerospace TBD** (placeholder for aerospace catalog / MRO path). Other seeded channels (GlobalSpec, Amazon Business, Fastenal, Motion, Applied) remain listed.

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/distributor-listings` | List; optional `?status=` `?channel=` |
| `GET` | `/distributor-listings/{id}/pricing` | Pricing payload (list / MAP / target + `sku_pricing`) |
| `PATCH` | `/distributor-listings/{id}/pricing` | Update pricing; accepts `distributor_price_usd` as alias for `target_catalog_price_usd` |
| `POST` | `/distributor-listings/sync-prices-from-inventory` | Refresh `list_price_usd` + `sku_pricing` from inventory; leaves MAP/target alone |

`GET /health` includes `"catalog_monitor_pricing": true`.

### Example curls

```bash
API="${API:-http://127.0.0.1:8000}"

# Status board data
curl -s "$API/distributor-listings" | jq '[.[] | {channel, status, list_price_usd, map_price_usd, target_catalog_price_usd}]'

# Sync list prices from inventory
curl -s -X POST "$API/distributor-listings/sync-prices-from-inventory" | jq .

# Get / patch pricing for one listing
ID=$(curl -s "$API/distributor-listings?channel=MSC" | jq -r '.[0].id')
curl -s "$API/distributor-listings/$ID/pricing" | jq .
curl -s -X PATCH "$API/distributor-listings/$ID/pricing" \
  -H 'Content-Type: application/json' \
  -d '{"map_price_usd":140.00,"target_catalog_price_usd":130.00,"campaign_notes":"MSC draft ready"}' | jq .
```

---

## UI

**Catalog Monitor** nav item (`docs/`):

- Status board counts (channels, not started, in flight, listed, with list price)
- Filters by channel and status
- Table with list / MAP / target prices and SKU chips
- **Edit Pricing** modal (channel + per-SKU)
- **Sync from Inventory** button → `POST .../sync-prices-from-inventory`

---

## Out of scope (later phases)

- Live scrape / price monitoring of Grainger / McMaster / MSC / Zoro storefronts
- Submitting supplier applications
- Aerospace partner shortlist beyond the TBD placeholder
- Attaching an external MAP / distributor price sheet
