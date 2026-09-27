# MSC — submission packet (Phase 4 approvals gate)

**Campaign label:** `campaign:msc`  
**STATUS:** DRAFT / pending_approval — James must approve in-app, then **manually** submit.  
**Closing Agent does not fill the MSC form or send email.**

**Canonical draft:** [`../MSC_SUPPLIER_APPLICATION_DRAFT.md`](../MSC_SUPPLIER_APPLICATION_DRAFT.md)  
**Official form:** https://www.mscdirect.com/customer-service/new-supplier-inquiry  
**Optional visibility:** https://msc.suppliergateway.com/

---

## Pre-submit checklist (W-9 / COI / photos / GTIN)

- [ ] W-9 for seller of record (PTC Inc and/or IMS — confirm legal name)
- [ ] Certificate of Insurance (COI)
- [ ] White-background product photos (multiple angles) × 3 SKUs
- [ ] Public one-pager / category-safe datasheet (no proprietary process depth)
- [ ] GTIN/UPC per sellable pack via GS1 — **TBD** until obtained
- [ ] Barcode label sample; pack dimensions & weight
- [ ] UNSPSC candidates: 40141603 or 27131614
- [ ] MAP / public list policy decided (prices from Catalog Monitor / inventory)
- [ ] Form answers reviewed against **live** MSC fields (draft may drift)
- [ ] James sign-off in Approvals / Campaigns UI (`approved`)

**Do not attach** detailed CAD or NDA-gated pricing to the public inquiry unless James explicitly approves.

---

## After human submits externally

1. In app: **Mark submitted** on `campaign:msc` → `submitted_externally`
2. Update distributor listing: `PUT /distributor-listings/<MSC_id>/status` `{"status":"applied"}`

Pricing remains from inventory / Catalog Monitor — refresh with sync-from-inventory if needed.
