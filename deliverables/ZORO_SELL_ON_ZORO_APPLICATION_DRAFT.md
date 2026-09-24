# Sell on Zoro — Partnership / Seller Application Draft (LC-Flow)

**STATUS: DRAFT — James Gallagher must review and approve before any application.**  
Do **not** submit this packet as-is. Closing Agent does not submit forms or send emails for this channel.

**Official apply / partnership URL:** https://www.zoro.com/sell/  
**Related Zoro page:** https://www.zoro.com/sell-on-zoro/  
**Historical BD contact (verify current):** businessdevelopment@zoro.com  

**Product:** LC-Flow Valve and Distribution Adaptor  
**Manufacturer:** PTC Inc | **Distributor:** Industrial and Molecular Solutions (IMS)  
**Primary contact:** James Gallagher, President · 610-393-1102 · Jgallagher10@gmail.com  
**Draft date:** 2026-09-23 PT  

**NDA / public-content policy**  
- Direct sales via Closing Agent: NDA before detailed specs/pricing.  
- Zoro catalog listings: use **PUBLIC / category-safe** copy only.  
- Detailed CAD, process depth, and controlled pricing packages: **available under NDA**.  
- **Open question:** public list prices on Zoro vs RFQ / NDA-gated direct only.

---

## 1. Company profile (draft)

| Field | Draft |
|-------|-------|
| **Legal / trading entities** | PTC Inc (manufacturer); Industrial and Molecular Solutions (distributor). **Seller of record TBD** (open question). |
| **Primary contact** | James Gallagher, President · 610-393-1102 · Jgallagher10@gmail.com |
| **Product focus** | Specialty pneumatic / fluid-handling valve and distribution adaptor (3 SKUs, 3 materials). |
| **Industries served** | Beverage / PET air conveyors, industrial lubrication & pneumatics, aerospace MRO adjacency, automotive engineering. |
| **Catalog breadth** | Small specialty line (3 sellable packs) — emphasize uniqueness and material options over SKU count. |
| **US fulfillment** | Recommend **dropship capability** if IMS can ship packs in **1–2 business days** from a US warehouse (Zoro typically dropships). Confirm capacity before apply. |

---

## 2. Dropship vs stock — recommendation

| Option | Recommendation |
|--------|----------------|
| **Dropship (preferred to offer)** | **Recommend enabling dropship** if IMS can reliably ship pack-of-2 orders in 1–2 days with tracking. Fits Zoro’s model and keeps MSC/Fastenal branch stock separate. |
| **Distributor stock** | Optional later if Zoro or a wholesale path requires staged inventory; not required to start the partnership conversation. |
| **FBA-style** | N/A for Zoro; do not conflate with Amazon FBA. |

State shipping cutoffs, weekend policy, and backorder rules in the application notes once confirmed.

---

## 3. Inventory update cadence (map to Closing Agent)

| Cadence | Draft plan |
|---------|------------|
| **Source of truth** | Closing Agent `inventory` table / `GET /inventory` (`stock_qty` per SKU). |
| **Suggested update frequency** | Daily CSV export while live; increase to near-real-time if order volume warrants. |
| **Export fields (outline)** | `sku, mpn, gtin, qty_available, list_price_usd, lead_time_days, unspsc, pack_qty` |
| **EDI 846** | Closing Agent can emit CSV/JSON shaped for inventory advice; **EDI VAN / SPS Commerce onboarding TBD** (human + vendor). |
| **Stockouts** | Push `qty=0` promptly; do not oversell. |

---

## 4. Attribute / SKU sheet outline (3 SKUs)

Prepare a spreadsheet matching Zoro’s attribute template when provided. Baseline columns:

| Attribute | LCP061000 | LCSS61000 | LCA061000 |
|-----------|-----------|-----------|-----------|
| Brand / seller brand | TBD (LC-Flow / PTC / IMS) | same | same |
| MPN / SKU | LCP061000 | LCSS61000 | LCA061000 |
| Title (public) | LC-Flow Valve and Distribution Adaptor, PC-ISO Plastic, Pack of 2 | … 316L Stainless … | … AlSiMg Aluminum … |
| Material | PC-ISO Plastic | 316L Stainless Steel | Aluminum AlSiMg |
| Pack quantity | 2 | 2 | 2 |
| Proposed list (USD) | 145.38 | 558.28 | 1,545.28 |
| GTIN / UPC | TBD (GS1) | TBD (GS1) | TBD (GS1) |
| UNSPSC | 40141603 or 27131614 | same | same |
| Country of origin | TBD | TBD | TBD |
| Weight / dims | TBD | TBD | TBD |
| Lead time (days) | TBD (target 1–2 if dropship) | TBD | TBD |
| Image URLs | TBD | TBD | TBD |
| Public description | Category-safe — see §5 | same | same |
| Restricted docs | CAD/process under NDA | same | same |

**Pricing:** proposed list subject to **MAP & channel policy** — James must set before go-live.

---

## 5. Public listing copy (no secret process)

> **LC-Flow Valve and Distribution Adaptor** — compact flow-control / distribution component for industrial pneumatic and fluid applications (including beverage/PET air conveyors and lubrication circuits). Available in PC-ISO plastic, 316L stainless steel, and AlSiMg aluminum. Sold as a **pack of 2**.  
>  
> Manufactured by PTC Inc; offered via Industrial and Molecular Solutions.  
> Detailed drawings, CAD, and proprietary process documentation are **available under NDA**. Classification: UNSPSC 40141603 (Pneumatic valves) or 27131614 (Pneumatic adapters).

Do **not** include proprietary additive-process depth, unpublished ratings, or NDA-only pricing language on the public Zoro PDP.

---

## 6. Fulfillment & returns (draft notes)

| Topic | Draft note for James to confirm |
|-------|----------------------------------|
| **Ship-from** | US warehouse / IMS facility (address TBD on application). |
| **SLA** | Target ship in 1–2 business days when in stock. |
| **Carriers** | TBD (UPS/FedEx/USPS as applicable). |
| **Returns** | Follow Zoro partner returns policy once contracted; defectives: RMA via IMS; restocking rules TBD. |
| **Hazmat** | Typically none for finished valve packs — confirm packaging materials. |
| **Insurance / COI** | Provide COI as required during onboarding. |

---

## 7. EDI / inventory feed readiness

| Capability | Status |
|------------|--------|
| Closing Agent inventory API / CSV export | **Ready to build/export** from `inventory` (`stock_qty`, SKU, list price). |
| Attribute sheet (3 SKUs) | Outline above — finalize when Zoro sends template. |
| EDI (850/855/856/846/810) | **EDI VAN TBD** (e.g. SPS Commerce commonly used with Zoro). Closing Agent can emit files; commercial VAN is external. |
| Images / GTIN | Photos TBD; GTIN **TBD via GS1**. |

---

## 8. Open questions (must answer before / during apply)

1. **Seller of record:** PTC Inc vs Industrial and Molecular Solutions on Zoro invoices/PDP?  
2. **MAP / channel pricing:** Zoro price vs MSC vs Amazon Business vs direct list?  
3. **GTIN:** Budget/timeline for GS1 UPCs on all three packs?  
4. **Public vs NDA:** Are proposed list prices and public datasheets allowed on Zoro?  
5. **Dropship capacity:** Can IMS hit 1–2 day ship on packs consistently?  
6. **Brand / trademark:** Brand string for PDP and any future Brand Registry–style needs?  
7. **EDI:** Self-EDI vs SPS/other network — who owns cost?

---

## 9. Attachments / readiness checklist

- [ ] Company profile + W-9 for seller of record  
- [ ] COI  
- [ ] Product photos (white background) × 3 SKUs  
- [ ] Public one-pager (category-safe)  
- [ ] Attribute spreadsheet (Zoro template when received)  
- [ ] Inventory feed sample CSV from Closing Agent  
- [ ] GTIN (TBD)  
- [ ] Shipping / returns SOP  
- [ ] MAP policy signed off by James  

---

## 10. Closing Agent tracking

```bash
curl -s -X PUT "$API/distributor-listings/<ID>/status" \
  -H 'Content-Type: application/json' \
  -d '{"status":"applied"}'
```

See `deliverables/DISTRIBUTOR_LISTING_TRACKER.md`.

---

**Again: DRAFT only. Apply only via the official Zoro URL after James reviews. Do not invent GTINs, approvals, or EDI readiness claims beyond CSV export capability.**
