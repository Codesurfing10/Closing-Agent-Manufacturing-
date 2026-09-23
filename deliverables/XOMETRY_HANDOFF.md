# Xometry handoff — operator guide

**Modes:** `XOMETRY_MODE=mock` (default) | `manual` | `api`  
**Rule:** Closing Agent never places a paid Xometry order. Real checkout stays on [xometry.com](https://www.xometry.com) (or PunchOut) until a buyer API exists.

## When a job is created

1. Customer PO arrives.
2. Set order to **Confirmed** via UI (“Confirm (PO acquired)”) or:

```bash
curl -s -X PUT "$API/orders/$ORDER_ID/status" \
  -H 'Content-Type: application/json' \
  -d '{"status":"Confirmed","po_number":"PO-1001"}'
```

3. A `manufacturing_jobs` row is created (idempotent if an active job already exists).

| Mode | Initial job status | What you do |
|------|--------------------|-------------|
| `mock` | `queued` | Approve → then Mock advance for demos |
| `manual` | `awaiting_human` | Follow RFQ checklist on xometry.com, then Approve |
| `api` | `error` (no key) or `awaiting_human` (key set) | Do not expect auto-charge; use mock/manual for v1 |

## Human gate

```bash
curl -s -X POST "$API/manufacturing/jobs/$JOB_ID/approve-xometry"
```

Moves job to `submitted`. In **manual** mode this only records that you (the human) completed web placement — it does not call Xometry to charge a card.

## Mock demo sequence

```bash
export API=http://localhost:8000
# create Pending order (use a real contact_id)
ORDER=$(curl -s -X POST "$API/orders" -H 'Content-Type: application/json' \
  -d '{"contact_id":"CONTACT_ID","product":"LCP061000","quantity_tons":2,"unit_price_usd":145.38}')
ORDER_ID=$(python3 -c "import json,sys; print(json.load(sys.stdin)['id'])" <<<"$ORDER")

curl -s -X PUT "$API/orders/$ORDER_ID/status" -H 'Content-Type: application/json' \
  -d '{"status":"Confirmed","po_number":"PO-DEMO-1"}'

JOB_ID=$(curl -s "$API/orders/$ORDER_ID/manufacturing" | python3 -c "import json,sys; print(json.load(sys.stdin)['job']['id'])")

curl -s -X POST "$API/manufacturing/jobs/$JOB_ID/approve-xometry"
curl -s -X POST "$API/manufacturing/jobs/$JOB_ID/mock-advance"   # → in_production (order mirrors)
curl -s -X POST "$API/manufacturing/jobs/$JOB_ID/mock-advance"   # → shipped
curl -s -X POST "$API/manufacturing/jobs/$JOB_ID/mock-advance"   # → delivered
```

## RFQ checklist (manual)

Job `checklist_json` includes process/material from SKU map, pack qty, ship-to placeholder (`XOMETRY_SHIP_TO_JSON`), and CAD path hint (`XOMETRY_CAD_DIR`/`{SKU}.step`). Confirm NDA + counsel before uploading CAD.

## SKU map

| SKU | Process | Material |
|-----|---------|----------|
| LCP061000 | FDM | PC-ISO |
| LCSS61000 | DMLS | Stainless Steel 316/L |
| LCA061000 | DMLS | Aluminum AlSi10Mg |

Unknown SKUs still create a job with `process=unknown` and notes.

## Env

See README — `XOMETRY_MODE`, `XOMETRY_API_KEY`, `XOMETRY_API_BASE`, `XOMETRY_MOCK_LEAD_DAYS`, `XOMETRY_SHIP_TO_JSON`, `XOMETRY_CAD_DIR`.
