# Distributor Listing Tracker — Closing Agent

**Product:** LC-Flow Valve and Distribution Adaptor  
**Date:** 2026-09-23 PT  
**Related research:** `deliverables/DISTRIBUTOR_CATALOG_INTEGRATION.md`  
**Application drafts:** `deliverables/MSC_SUPPLIER_APPLICATION_DRAFT.md`, `deliverables/ZORO_SELL_ON_ZORO_APPLICATION_DRAFT.md`

Tracks industrial catalog / distributor listing progress for LC-Flow SKUs inside Closing Agent (SQLite + FastAPI). Does **not** submit portal forms or send emails.

---

## Table: `distributor_listings`

| Column | Type | Notes |
|--------|------|-------|
| `id` | TEXT PK | UUID |
| `channel` | TEXT UNIQUE | e.g. MSC, Zoro, Thomasnet |
| `path_type` | TEXT | `open_apply` \| `portal_review` \| `closed_bd` \| `marketplace` |
| `status` | TEXT | `not_started` \| `applied` \| `in_review` \| `approved` \| `rejected` \| `listed` \| `on_hold` |
| `portal_url` | TEXT | Official portal or contact page (McMaster has **no** public apply URL — contact page only) |
| `priority` | TEXT | `P0`–`P6` style (seed uses P1–P5) |
| `skus` | TEXT | Comma list: `LCP061000,LCSS61000,LCA061000` |
| `notes` | TEXT | Freeform |
| `next_action` | TEXT | Hint for James / BD |
| `next_action_date` | TEXT | ISO date optional |
| `applied_at` | TEXT | Set when status → `applied` (if empty) |
| `listed_at` | TEXT | Set when status → `listed` (if empty) |
| `contact_email` | TEXT | Channel contact if known |
| `created_at` / `updated_at` | TEXT | ISO timestamps |

Created in `init_db()`; seed is **idempotent** by `channel`.

---

## Seed rows (initial)

| Priority | Channel | path_type | portal_url (summary) | Initial status |
|----------|---------|-----------|----------------------|----------------|
| P1 | Thomasnet | open_apply | Thomasnet get-listed | not_started |
| P1 | GlobalSpec | open_apply | advertising.globalspec.com/list-your-products | not_started |
| P2 | MSC | open_apply | mscdirect.com/.../new-supplier-inquiry | not_started |
| P2 | Zoro | open_apply | zoro.com/sell/ | not_started |
| P2 | Amazon Business | marketplace | sell.amazon.com/programs/amazon-business | not_started |
| P3 | Fastenal | portal_review | fastenal.com | not_started |
| P3 | Motion | portal_review | motionpartnerportal.com/Supplier-Process | not_started |
| P3 | Applied | portal_review | applied.com/supplier-diversity | not_started |
| P4 | Grainger | portal_review | JAGGAER WWGrainger login | not_started |
| P5 | McMaster | closed_bd | mcmaster.com/contact (**no apply URL**) | not_started |

---

## API endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/distributor-listings` | List all; optional query `status`, `channel` |
| `POST` | `/distributor-listings` | Create a channel row |
| `GET` | `/distributor-listings/{id}` | Get one |
| `PUT` | `/distributor-listings/{id}` | Partial update |
| `PUT` | `/distributor-listings/{id}/status` | Body: `{"status":"..."}` |

`GET /health` includes `"distributor_listings": true`.

---

## Example curls

```bash
API="${API:-http://127.0.0.1:8000}"

# List all
curl -s "$API/distributor-listings" | jq .

# Filter
curl -s "$API/distributor-listings?status=not_started" | jq .
curl -s "$API/distributor-listings?channel=MSC" | jq .

# Create (example — Digi-Key optional / low priority)
curl -s -X POST "$API/distributor-listings" \
  -H 'Content-Type: application/json' \
  -d '{
    "channel": "Digi-Key",
    "path_type": "open_apply",
    "priority": "P6",
    "portal_url": "https://www.digikey.com/-/media/PDF/Help/SupplierQuestionnaire.PDF",
    "skus": "LCP061000,LCSS61000,LCA061000",
    "notes": "Low category fit unless electronics OEM pull",
    "next_action": "Defer unless electronics demand appears",
    "contact_email": "newsuppliers@digikey.com"
  }' | jq .

# Partial update
curl -s -X PUT "$API/distributor-listings/<ID>" \
  -H 'Content-Type: application/json' \
  -d '{"next_action":"Submit MSC inquiry after James sign-off","next_action_date":"2026-10-01"}' | jq .

# Status transition
curl -s -X PUT "$API/distributor-listings/<ID>/status" \
  -H 'Content-Type: application/json' \
  -d '{"status":"applied"}' | jq .
```

---

## Status workflow (suggested)

`not_started` → `applied` → `in_review` → `approved` → `listed`  
Branches: `on_hold`, `rejected`.

---

## Out of scope

- Submitting MSC / Zoro / portal forms  
- Sending email  
- Render deploy / merge to main without user review  
- Inventing GTINs or claiming McMaster has a public apply URL  
