# MSC Industrial Supply — New Supplier Inquiry Draft (LC-Flow)

**STATUS: DRAFT — James Gallagher must review and approve before any submission.**  
Do **not** submit this packet as-is. Closing Agent does not submit forms or send emails for this channel.

**Official form URL:** https://www.mscdirect.com/customer-service/new-supplier-inquiry  

**Related MSC pages**
- Industrial suppliers overview: https://www.mscdirect.com/customer-service/supplier-support/industrial-suppliers  
- SupplierGATEWAY (optional visibility): https://msc.suppliergateway.com/  
- Phone: 1-800-645-7270  

**Product:** LC-Flow Valve and Distribution Adaptor  
**Manufacturer:** PTC Inc | **Distributor / channel partner:** Industrial and Molecular Solutions (IMS)  
**Primary contact:** James Gallagher, President · 610-393-1102 · Jgallagher10@gmail.com  
**Draft date:** 2026-09-23 PT  

**NDA / public-content policy (read before filling form)**  
- Closing Agent requires an NDA before detailed specs/pricing for **direct** sales.  
- For **public catalog channels** such as MSC, use **PUBLIC / category-safe** language only.  
- Detailed CAD, proprietary process depth, and controlled pricing packages remain **available under NDA**.  
- **Open question for James:** confirm public list prices + datasheets on MSC vs RFQ-only / NDA-gated content.

---

## 1. Suggested form answers / notes

| Form area | Draft answer / note |
|-----------|---------------------|
| **Business type** | Manufacturer (PTC Inc) with authorized distributor Industrial and Molecular Solutions. Clarify **seller of record** before submit (PTC vs IMS) — open question. |
| **Company legal name** | Confirm with James: PTC Inc and/or Industrial and Molecular Solutions as listed on W-9. |
| **Contact** | James Gallagher, President · 610-393-1102 · Jgallagher10@gmail.com |
| **Product line categories** | Select / emphasize: **Pneumatics & Hydraulics**, **Lubrication**, **Hose/Tube/Fittings** (category adjacency for flow/distribution adaptor use). |
| **Product summary (PUBLIC-SAFE)** | See §2 below. Do not paste proprietary process detail into the public inquiry. |
| **Competitors (as MSC form expects)** | Grainger, McMaster-Carr, Fastenal — note LC-Flow is a specialty additive/material-options line, not a broad MRO catalog competitor. |
| **Barcoding preference** | **Yes — intent to barcode** sellable packs (pack of 2). GTIN/UPC **TBD** — obtain via GS1 before go-live. |
| **SupplierGATEWAY** | Optional: register at https://msc.suppliergateway.com/ after or alongside inquiry for broader MSC supplier visibility. Not a substitute for Product Management review. |
| **First-year MSC potential** | Honest estimate ranges — see §4. Label assumptions; do not invent contracts. |
| **UNSPSC (prepare)** | Primary candidate **40141603** (Pneumatic valves) or **27131614** (Pneumatic adapters). |

---

## 2. Public-safe product summary (paste-ready, category-safe)

> LC-Flow Valve and Distribution Adaptor is a compact flow-control / distribution component for industrial pneumatic and fluid-handling applications, including beverage/PET air conveyors, lubrication circuits, and general MRO pneumatics. Offered in three materials (PC-ISO plastic, 316L stainless, AlSiMg aluminum) as **packs of 2**. Manufactured by PTC Inc; distributed by Industrial and Molecular Solutions.  
>  
> **Public listing copy stays high-level.** Detailed dimensional drawings, CAD, process documentation, and controlled commercial terms are **available under NDA**. Suggested classification: UNSPSC 40141603 (Pneumatic valves) or 27131614 (Pneumatic adapters). GTIN/UPC: **TBD (GS1)**.

---

## 3. SKU sheet (proposed list — subject to MAP & channel policy)

| SKU | Description | Material | Pack qty | Proposed list (USD) | GTIN |
|-----|-------------|----------|----------|---------------------|------|
| LCP061000 | LC-Flow Valve and Distribution Adaptor | PC-ISO Plastic | 2 | $145.38 | TBD — obtain via GS1 |
| LCSS61000 | LC-Flow Valve and Distribution Adaptor | 316L Stainless | 2 | $558.28 | TBD — obtain via GS1 |
| LCA061000 | LC-Flow Valve and Distribution Adaptor | AlSiMg Aluminum | 2 | $1,545.28 | TBD — obtain via GS1 |

**Pricing note:** Treat figures as **proposed list / subject to MAP & channel policy**. Do not claim MSC-approved net or MAP until James sets channel rules. Direct-sales detailed pricing remains NDA-gated in Closing Agent.

---

## 4. First-year MSC potential (honest ranges + assumptions)

These are **planning estimates only** for the inquiry form’s “potential” fields — not forecasts or commitments.

| Scenario | Est. MSC sell-through (packs, Year 1) | Rough list $ at proposed list | Assumptions |
|----------|----------------------------------------|-------------------------------|-------------|
| Conservative | 20–60 packs | ~$5k–$25k blended | Soft launch; plastic SKU carries most volume; stainless/aluminum sample-driven |
| Base | 60–150 packs | ~$20k–$60k blended | MSC assortment accepted; 1–2 national accounts or branch pull-through |
| Upside | 150–300 packs | ~$50k–$120k+ | Strong branch/category champion + aerospace/beverage MRO demand |

**Assumptions to state if the form asks for narrative:** 3 SKUs only; specialty line; no existing MSC run-rate; GTIN/barcode and product photos still required; acceptance not guaranteed.

---

## 5. Competitors note (form-ready)

MSC’s inquiry typically references **Grainger / McMaster / Fastenal**. Draft framing:

> Primary industrial catalog competitors for adjacent pneumatic/MRO flow hardware include Grainger, McMaster-Carr, and Fastenal. LC-Flow differentiates as a small specialty line with multiple material options (PC-ISO, 316L, AlSiMg) for application-specific environments. We are seeking MSC assortment for customers who prefer MSC as their MRO source of record.

---

## 6. Attachments still needed (checklist — do not submit without)

- [ ] W-9 (legal entity matching seller of record)  
- [ ] Certificate of Insurance (COI)  
- [ ] White-background product photos (multiple angles) per SKU  
- [ ] Public one-pager / category-safe datasheet  
- [ ] GTIN/UPC per sellable pack (GS1) — mark **TBD** until obtained  
- [ ] Barcode label sample / packing dimensions & weight  
- [ ] Country of origin / HTS (as applicable)  
- [ ] Diversity certification docs (if any — optional)  
- [ ] MAP / channel pricing policy (internal — decide before go-live)  
- [ ] Confirm seller of record: PTC Inc vs Industrial and Molecular Solutions  

Detailed CAD / proprietary process packs: **available under NDA** — do not attach to the public inquiry unless James explicitly approves.

---

## 7. Closing Agent tracking

After James approves and submits:

```bash
# Example — mark MSC applied (use actual listing id from GET /distributor-listings)
curl -s -X PUT "$API/distributor-listings/<ID>/status" \
  -H 'Content-Type: application/json' \
  -d '{"status":"applied"}'
```

See `deliverables/DISTRIBUTOR_LISTING_TRACKER.md`.

---

## 8. Pre-submit sign-off

| Item | Owner | Done? |
|------|-------|-------|
| Public vs NDA policy for MSC list price/datasheet | James | |
| Seller of record (PTC vs IMS) | James | |
| MAP / proposed list confirmed | James | |
| Attachments complete | James / IMS | |
| Form answers reviewed against live MSC form fields | James | |
| Submit via official URL only | James | |

**Again: DRAFT only. Do not submit until James reviews.**
