# LC-Flow Valve — Sales Brief (Closing Agent)

**Product:** LC-Flow Valve and Distribution Adaptor  
**Manufacturer:** PTC Inc | **Distributor:** Industrial and Molecular Solutions  
**Contact:** James Gallagher, President · 610-393-1102 · Jgallagher10@gmail.com  
**Generated:** 2026-09-23T22:32:01Z

---

## Product pitch

LC-Flow is an apparatus for molecular transfer and delivery of vapors, gases, liquids, and
sprays — controlling flow, distribution, and pressure. Manufactured via advanced 3D printing
(Metal Binder Jetting, DMLS, FDM, SLS, MJF, LSPc, DLS, Polyjet) in plastics (PC-ISO, ABS,
Nylon 12, Ultem 1010, PP) and metals (AlSiMg, 316L SS, 17-4).

**Sell the SKU that matches the environment:**
| SKU | Material | List (pack of 2) | Best fit |
|-----|----------|------------------|----------|
| LCP061000 | PC-ISO Plastic | $145.38 | PET air conveyors, beverage lines, high-volume spares |
| LCSS61000 | 316L Stainless Steel | $558.28 | Washdown, corrosive, aerospace/auto test, CIP |
| LCA061000 | Aluminum AlSiMg | $1,545.28 | Weight-critical aerospace GSE, propulsion, airline |

---

## NDA policy (mandatory for ALL sales discussions)

1. **Every opportunity requires an NDA** (`nda_required=true`, start `nda_status=Pending`).
2. **Before NDA signed:** outreach may introduce the product category only; **do not** share
   detailed specs, drawings, CAD, material process details, or unit pricing. First ask the
   prospect to execute the Mutual NDA (`deliverables/NDA_TEMPLATE.md` — counsel review required).
3. **After NDA signed:** normal technical pitch, samples discussion, and pricing OK.
4. **Closing Agent enforcement:** `ndas` table + APIs; email/meeting/agent routes check NDA
   status for the contact/lead and gate content accordingly.
5. Create NDA: `POST /ndas` with `contact_id` or `lead_id`; mark signed via
   `PUT /ndas/{id}/status` with `{"status":"signed"}`.

### Example curl (NDA workflow)

```bash
# Create pending NDA for a contact
curl -X POST "$API/ndas" -H 'Content-Type: application/json' \
  -d '{"contact_id":"<CONTACT_UUID>","document_ref":"deliverables/NDA_TEMPLATE.md"}'

# List NDAs
curl "$API/ndas"

# Mark signed
curl -X PUT "$API/ndas/<NDA_ID>/status" -H 'Content-Type: application/json' \
  -d '{"status":"signed"}'

# Inventory
curl "$API/inventory"
curl "$API/inventory/LCP061000"
```

---

## ICP by industry

1. **Aerospace** — OEMs, MRO, propulsion test, pneumatic/fluidic systems (Boeing, Lockheed,
   Northrop, SpaceX, Collins, Honeywell, Spirit). Prefer LCA061000 / LCSS61000.
2. **Beverage / PET Packaging** — bottlers & converters (Niagara, Amcor, Coke, PepsiCo,
   Refresco, KDP, Nestlé Waters). Prefer LCP061000; SS for washdown.
3. **PET Air Conveyors** — OEMs & integrators (Sidel, Krones, GEA Convair, SMF, Effiline,
   AMBEC, FlexLink). Prefer LCP061000 OEM volume; SS for duty cycles.
4. **Automotive Engineering** — lubrication, pneumatic fluid control, powertrain test
   (Bosch, Continental, Magna, ZF, Stellantis, Ford, GM). Mix of all three SKUs.

---

## Pipeline snapshot

- **Leads:** 28 (Aerospace: 7, Automotive Engineering: 7, Beverage / PET Packaging: 7, PET Air Conveyors: 7)
- **Opportunities:** 14 (all NDA Pending)
- **Total estimated pipeline:** $302,918.72

### Top 5 opportunities to pursue first

| Rank | Company | SKU | Qty | Est. USD | Next step |
|------|---------|-----|-----|----------|-----------|
| 1 | Boeing | LCA061000 | 24 | $37,086.72 | Schedule discovery with pneumatic systems eng. |
| 2 | Krones | LCSS61000 | 60 | $33,496.80 | Technical review with intralogistics eng. |
| 3 | Sidel | LCP061000 | 200 | $29,076.00 | OEM design-in meeting with air conveyor PM |
| 4 | Magna International | LCSS61000 | 48 | $26,797.44 | Multi-plant framework quote |
| 5 | SpaceX | LCA061000 | 16 | $24,724.48 | Intro via GSE engineering channel |

**Sequence:** (1) Send Mutual NDA → (2) confirm signed in Closing Agent → (3) technical discovery
→ (4) SKU recommendation & quote → (5) sample / design-in.

---

## How inventory maps to the Closing Agent

- SQLite `inventory` table seeded idempotently by SKU on startup (3 sellable SKUs).
- APIs: `GET/POST /inventory`, `GET/PUT /inventory/{sku}`.
- Deliverables JSON/CSV are the offline source of truth for Builder handoff; import into
  agents/CRM as needed.
- Leads generated via `/leads/generate` now cover Aerospace, Beverage/PET, PET Air Conveyors,
  and Automotive Engineering (not PET resin only).
- Optional `opportunities` table + GET/POST mirrors deliverables for live tracking.
- Orders remain available for closed deals; prefer inventory SKU codes in order `product`.

---

## Inventory curl examples

```bash
curl -s "$API/inventory" | jq .
curl -s -X POST "$API/inventory" -H 'Content-Type: application/json' -d '{
  "sku":"LCP061000","name":"LC-Flow Valve — Plastic PC-ISO",
  "material":"PC-ISO","unit_price_usd":145.38,"units_per_pack":2,"stock_qty":50,
  "manufacturer":"PTC Inc","distributor":"Industrial and Molecular Solutions"
}'
curl -s -X PUT "$API/inventory/LCP061000" -H 'Content-Type: application/json' \
  -d '{"stock_qty":45}'
```
