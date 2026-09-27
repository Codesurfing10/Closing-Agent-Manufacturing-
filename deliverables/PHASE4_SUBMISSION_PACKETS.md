# Phase 4 — Approvals-gated submission packets (index)

**Product:** LC-Flow Valve and Distribution Adaptor (`LCP061000`, `LCSS61000`, `LCA061000`)  
**Owner:** James Gallagher · 610-393-1102 · Jgallagher10@gmail.com  
**Date:** 2026-09-26 PT  
**Hard rules:** Closing Agent **never** auto-submits portals, fills browser forms, or sends vendor emails. Humans submit externally; the app only tracks `pending_approval` → `approved` → `submitted_externally` (manual Mark submitted).

**NDA policy:** OEM / BD packets are **NDA-first**. Public catalog packets (MSC, Zoro, Thomasnet) use **public-safe** copy only; detailed CAD/process/controlled pricing stay under NDA.

**Pricing source:** Catalog list prices come from inventory / Catalog Monitor (`GET /distributor-listings`, `POST /distributor-listings/sync-prices-from-inventory`). Do not invent MAP or channel nets in packets.

---

## Packets ready for human approval

| Label | Channel | Packet file | Type | App campaign label | Status seed |
|-------|---------|-------------|------|--------------------|-------------|
| MSC New Supplier Inquiry | MSC | `MSC_SUPPLIER_APPLICATION_DRAFT.md` + `campaigns/msc-submission-packet.md` | apply | `campaign:msc` | pending_approval |
| Sell on Zoro | Zoro | `ZORO_SELL_ON_ZORO_APPLICATION_DRAFT.md` + `campaigns/zoro-submission-packet.md` | apply | `campaign:zoro` | pending_approval |
| Thomasnet claim | Thomasnet | `campaigns/thomasnet-claim-checklist.md` | apply / claim | `campaign:thomasnet` | pending_approval |
| Grainger JAGGAER | Grainger | `campaigns/grainger-jaggaer-checklist.md` | portal / BD (not auto-apply) | `campaign:grainger` | pending_approval |
| McMaster BD outreach | McMaster | `campaigns/mcmaster-bd-outreach.md` | BD only — **no fake apply URL** | `campaign:mcmaster` | pending_approval |

**Related Phase 2 OEM / aerospace drafts (already on main):**  
`OEM_KRONES_SIDEL_CAMPAIGN.md`, `AEROSPACE_SPACE_CATALOG_CHANNELS.md`, `LISTING_CAMPAIGNS_QUEUE.md`, `campaigns/krones-nda-outreach.md`, `sidel-nda-outreach.md`, `khs-nda-outreach.md`, `sipa-nda-outreach.md`, `partsbase-ils-info-request.md`.

---

## App wiring

- Table: `campaigns` (status: `pending_approval` | `approved` | `submitted_externally`)
- API: `GET/POST /campaigns`, `POST /campaigns/{id}/approve`, `POST /campaigns/{id}/reject`, `POST /campaigns/{id}/mark-submitted`
- UI: **Campaigns** nav + pending cards also listed under **Approvals**
- **Mark submitted** is the only path to `submitted_externally` — after James (or designee) completed the external portal/email by hand

---

## SQLite / Render seed note

`_seed_distributor_listings()` and `_seed_campaigns()` **upsert by name/label**: missing channels/campaigns are inserted on every process start; existing rows are left intact (pricing backfill only for listings).

On Render **free** web services, the SQLite file under the instance filesystem is often **ephemeral** — a redeploy may wipe the DB and re-seed cleanly (observed after PR #13: 18 channels including PartsBase/ILS/OEM, no leftover `Aerospace TBD`).

If a **persistent disk** is later attached and an old DB survives:

- New channel names from seed **will still appear** (insert-if-missing by `channel`)
- Stale placeholder rows (e.g. historical `Aerospace TBD`) would remain until manually deleted or a one-shot cleanup runs
- New campaign labels likewise insert-if-missing

No automatic portal submit endpoint exists by design.

---

## What James must approve next (short list)

1. **W-9 / COI / photos / GTIN** readiness for MSC + Zoro (checklists in packets).  
2. **Seller of record** (PTC Inc vs IMS) and public vs NDA list-price policy.  
3. Approve **`campaign:msc`** then manually submit MSC New Supplier Inquiry.  
4. Approve **`campaign:zoro`** (confirm dropship SLA) then manually apply at zoro.com/sell.  
5. Approve **`campaign:thomasnet`** claim + public one-pager categories.  
6. Approve **`campaign:grainger`** JAGGAER profile create (BD — not SKU upload).  
7. Approve **`campaign:mcmaster`** only if pursuing warm intro / customer pull — **no cold apply URL**.  
8. Counsel-approve Mutual NDA, then OEM NDA-first drafts (Krones/Sidel) from Phase 2.

