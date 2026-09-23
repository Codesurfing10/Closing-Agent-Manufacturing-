# Xometry Manufacturing Integration — Research + Proposal

**Repo:** Closing-Agent-Manufacturing- (`feature/lc-flow-valve-inventory-nda`; also checked `main`, `origin/add-po-agent`)  
**Related package:** `/workspace/closing-agent/` (same order model)  
**Date:** 2026-09-23 PT  
**Scope:** Research + concrete design only — **do not implement yet**.

---

## 1. Current order / PO hooks in the codebase

### Order lifecycle (already exists)

| Constant / field | Location | Values |
|---|---|---|
| `ORDER_STATUSES` | `backend/app.py` ~L762 | `Pending` → `Confirmed` → `In Production` → `Shipped` → `Delivered` \| `Cancelled` |
| `orders` table | `init_db()` ~L102–113 | `id`, `contact_id`, `product`, `quantity_tons`, `unit_price_usd`, `status`, `notes`, `created_at`, `updated_at` |
| Create | `create_order()` `POST /orders` ~L1122 | Inserts `status="Pending"`, advances contact `stage` → `Closed Won` |
| List | `list_orders()` `GET /orders` ~L1147 | Optional `contact_id` filter |
| Status update | `update_order_status()` `PUT /orders/{order_id}/status` ~L1164 | Validates against `ORDER_STATUSES` |

### What “PO acquired” means today

**There is no `po_number`, `po_acquired_at`, or dedicated PO entity.** Closest semantic:

- **Recommended trigger:** transition `Pending` → `Confirmed` on `PUT /orders/{id}/status` (= customer PO received / payment authorized).
- Alternative: new field `po_number` set via extended `OrderStatusUpdate` or `POST /orders/{id}/po`.

`origin/add-po-agent` exists by name but has **no PO-specific code** (same legacy PET order routes as older main).

### Related but separate surfaces

| Surface | File / function | Notes |
|---|---|---|
| Funnel stages | `FUNNEL_STAGES` ~L761 | Contact CRM; `create_order` sets `Closed Won` |
| Opportunities | `opportunities` table + `GET/POST /opportunities` | Pipeline only; **not linked** to `orders` |
| Inventory SKUs | `_seed_inventory()`, `GET/PUT /inventory` | `LCP061000` / `LCSS61000` / `LCA061000` |
| NDA gate | `_contact_nda_signed`, `/ndas` | Pre-sales; manufacturing should assume NDA already signed |
| Agent | `run_agent()` `POST /agent/run` | Mentions orders in help text; **does not create/update orders** |
| UI | `docs/app.js` `loadOrders` / `submitCreateOrder` / `updateOrderStatus` | Still labels qty as **tons** (PET legacy) |

### Legacy mismatch (important for Xometry qty)

Orders still use `quantity_tons` (PET resin). LC-Flow sells **packs of 2 valves**. Any manufacturing handoff should treat qty as **units or packs**, not tons — rename/alias later (`quantity` + keep `quantity_tons` as alias during migration).

---

## 2. Xometry capability summary

### Critical finding

**There is no public buyer Instant Quote / place-order API documented.**  
`developer.xometry.com` is the **WorkCenter Partner API** (for shops fulfilling Xometry jobs), not a buyer procurement API.

| Capability | Buyer (you) | Partner / WorkCenter |
|---|---|---|
| Instant quote from CAD | Web UI Instant Quoting Engine | N/A |
| Place order | Web checkout / PunchOut / sales RFQ | N/A (accept offers) |
| Track manufacturing | Order History / Teamspace / email | Jobs API + webhooks |
| Public REST to create quote/order | **Not documented / partner-only sales path** | Jobs, Offers, Webhooks |

### Auth / access

- Header: `X-API-Key`
- Base: `https://api.developer.xometry.com`
- Tokens issued in Workcenter: https://start.workcenter.xometry.com/settings/partner/developer/tokens
- Request access: email `support@xometry.com` with Partner Name + business email
- Rate limits: 2 GET/s and 2 write/s per partner org
- **No public sandbox** documented (tokens until revoked)
- Webhook verify header: `X-Signature-SHA256`

### Documented partner endpoints (relevant if partner status)

- `GET /v0/jobs/`, `GET /v0/jobs/{id}` — statuses: `incomplete|pending|progress|complete|error|cancelled`; includes `shippingDetails`, `dates.shipBy/due`
- Webhooks: `job.created`, `job.revised`, `job.statusUpdated`
- Offers: list / accept / reject (job board; extra approval)
- **Does not** create a customer manufacturing order from CAD + material + qty

### Buyer-side integration options Xometry advertises

1. **Instant Quoting Engine** (web) — upload CAD, pick process/material/qty, checkout  
2. **PunchOut** — Coupa / Ariba / SAP / Dynamics (sales-assisted setup; cXML PO)  
3. **CAD add-ins** — Fusion / SOLIDWORKS / Onshape  
4. **Request a Quote** — sales-managed RFQ for complex/volume jobs  

### Material ↔ Xometry mapping (LC-Flow SKUs)

| SKU | Closing Agent material | Xometry process (suggested) | Xometry material name |
|---|---|---|---|
| `LCP061000` | PC-ISO | FDM | Stratasys PC-ISO (biocompatible) |
| `LCSS61000` | 316L Stainless Steel | DMLS (or Binder Jet 316L) | Stainless Steel 316/L |
| `LCA061000` | Aluminum AlSiMg | DMLS | Aluminum AlSi10Mg |

Confirm finish, heat treat, and certification with engineering before locking quotes.

### Key doc links

- Getting started: https://developer.xometry.com/docs/getting-started  
- Docs index: https://developer.xometry.com/llms.txt  
- Auth / tokens: https://developer.xometry.com/reference/authentication  
- Jobs: https://developer.xometry.com/reference/get_v0-jobs  
- Webhooks: https://developer.xometry.com/docs/webhooks-1 · events: https://developer.xometry.com/docs/webhook-events-payloads  
- PunchOut (buyer procurement): https://www.xometry.com/xometry-enterprise/xometry-integration-punchout/  
- How quoting/ordering works: https://www.xometry.com/how-xometry-works/  
- FDM PC-ISO: https://www.xometry.com/capabilities/3d-printing-service/fused-deposition-modeling/  
- DMLS metals: https://www.xometry.com/capabilities/3d-printing-service/direct-metal-laser-sintering/

---

## 3. Recommended architecture (practical given API gap)

### Design principle

Ship a **manufacturing handoff layer** that works in **mock / manual** mode today, with a clean adapter so a future buyer API or PunchOut can plug in without rewriting order status logic.

### Trigger → quote → order → status sync

```
Customer PO received
        │
        ▼
PUT /orders/{id}/status  status=Confirmed  (+ optional po_number)
        │
        ▼
on_po_acquired(order_id)          # hook inside update_order_status
        │
        ├─ Resolve SKU from order.product → inventory row
        ├─ Map material → Xometry process + material
        ├─ Load CAD path from config (per SKU) — NOT auto-upload until NDA/counsel OK
        │
        ▼
manufacturing_jobs row (status=queued)
        │
        ├─ XOMETRY_MODE=mock  → fake quote_id/order_id, advance timers or manual PUT
        ├─ XOMETRY_MODE=manual → generate RFQ checklist + deep-link notes; human places order on xometry.com
        └─ XOMETRY_MODE=api   → (future) PunchOut / partner buyer API if granted
        │
        ▼
Status sync maps into ORDER_STATUSES:
  quote/manual placed     → Confirmed (already)
  in production           → In Production
  shipped + tracking      → Shipped
  delivered               → Delivered
```

### Config / env vars

| Env | Purpose |
|---|---|
| `XOMETRY_MODE` | `mock` (default) \| `manual` \| `api` |
| `XOMETRY_API_KEY` | Partner API key (only if `api` and access granted) |
| `XOMETRY_API_BASE` | default `https://api.developer.xometry.com` |
| `XOMETRY_WEBHOOK_SECRET` | For signature verification if webhooks used |
| `XOMETRY_SHIP_TO_JSON` | Default ship-to (or per-order override) |
| `XOMETRY_CAD_DIR` | Local/secure path to STEP/STL per SKU (e.g. `LCP061000.step`) |
| `XOMETRY_MOCK_LEAD_DAYS` | Mock lead time for demo |

### Data model (minimal)

New table `manufacturing_jobs` (or columns on `orders`):

- `id`, `order_id` (FK)
- `sku`, `quantity_units`, `material`, `process`
- `provider` = `xometry`
- `mode` (`mock|manual|api`)
- `external_quote_id`, `external_order_id`, `external_job_id` (nullable)
- `quote_usd`, `lead_days`, `tracking_number`, `carrier`
- `status` (`queued|quoted|ordered|in_production|shipped|delivered|failed|cancelled`)
- `ship_to_json`, `cad_ref`, `notes`, `last_synced_at`, `created_at`, `updated_at`

Optional on `orders`: `po_number TEXT`, `sku TEXT`, `quantity REAL` (alias of tons).

### Minimal API surface in `app.py`

| Method | Path | Behavior |
|---|---|---|
| (hook) | existing `PUT /orders/{id}/status` | If → `Confirmed` and no open mfg job → `enqueue_xometry_job` |
| `POST` | `/orders/{id}/manufacturing` | Explicit kickoff (idempotent) |
| `GET` | `/orders/{id}/manufacturing` | List jobs + tracking |
| `POST` | `/manufacturing/{job_id}/sync` | Pull status (mock advance / manual note / future API) |
| `POST` | `/webhooks/xometry` | Stub for partner webhooks (verify signature; no-op in mock) |
| `GET` | `/health` | Include `xometry_mode` |

Do **not** auto-place paid orders without human confirmation unless user explicitly opts in.

### Exact files to change (when implementing)

1. `backend/app.py` — schema migration, models, order-status hook, routes, `xometry_client.py` inline or sibling module  
2. `backend/requirements.txt` — `httpx` if calling APIs  
3. `docs/app.js` + `docs/index.html` — show mfg status / tracking; fix “tons” label  
4. `README.md` + `deliverables/SALES_BRIEF.md` — env vars + flow  
5. Optional: `backend/xometry/` package (`client.py`, `mapping.py`, `mock.py`)  
6. Optional: Compose `deliverables/XOMETRY_RFQ_CHECKLIST.md` for manual mode  

Related package mirror: `/workspace/closing-agent/app.py` if kept in sync.

---

## 4. Risks

| Risk | Detail |
|---|---|
| **Counsel / NDA vs manufacturing** | CAD/drawings must not leave the vault until NDA signed **and** counsel OK with sending files to Xometry’s network. Treat mfg handoff as post-NDA, post-PO. |
| **No buyer Instant Quote API** | Full automation blocked without PunchOut sales engagement or undocumented partner access. Mock/manual is the honest v1. |
| **WorkCenter API wrong direction** | Partner Jobs API is for *makers* fulfilling Xometry work, not for *buyers* ordering parts. Do not build against Jobs accept/reject unless PTC becomes a Xometry supplier. |
| **Lead times** | Instant quote lead times vary by process/qty; AlSiMg/316L DMLS often longer than FDM PC-ISO. Don’t promise list-price ship dates. |
| **Pricing vs list** | Inventory list (145.38 / 558.28 / 1545.28 per pack of 2) may diverge from Xometry quote + shipping. Keep `quote_usd` separate from customer `unit_price_usd`. |
| **Materials naming** | `AlSiMg` ≈ Xometry `AlSi10Mg`; confirm alloy. PC-ISO is FDM-specific grade. |
| **ITAR / certs** | Aerospace opps (Boeing, SpaceX) may need ITAR — Xometry line items have `isItar`; Closing Agent has no ITAR flag yet. |
| **Ship-to source** | Contacts have no address fields today — must add ship-to or use env default. |
| **Quantity semantics** | `quantity_tons` will confuse mfg qty; migrate carefully. |

---

## 5. Open questions for the user

1. **Credentials:** Do you have (or want) a Xometry buyer account, PunchOut with Coupa/Ariba/etc., or WorkCenter partner API access? Or proceed with **mock + manual RFQ** only?  
2. **Which Xometry product:** Instant Quote web, PunchOut, sales RFQ, or CAD add-in? (API alone is insufficient for buyer order placement today.)  
3. **Ship-to address source:** Company HQ? Per-contact field? Per-order body? Env default?  
4. **CAD assets:** Where do STEP/STL files live per SKU, and may they be uploaded to Xometry after NDA?  
5. **PO definition:** Confirm trigger = order status `Confirmed` + optional `po_number`?  
6. **Human gate:** Auto-submit paid order vs require explicit `POST .../manufacturing` after quote review?  
7. **Process choice for metals:** Prefer DMLS vs Binder Jet for 316L / AlSiMg?  
8. **Customer vs factory ship:** Deliver to end customer or to PTC/IMS for inspection then forward?

---

## 6. Suggested check-in before bigger moves

**Propose v1 (small PR after approval):**  
- `po_number` + manufacturing_jobs table  
- Hook on `Confirmed`  
- `XOMETRY_MODE=mock|manual` only  
- Material mapping dict for 3 SKUs  
- Docs + UI status chip  

**Defer:** Live API/PunchOut until credentials and product choice are confirmed.
