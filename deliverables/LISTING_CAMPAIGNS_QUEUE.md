# Listing & OEM Campaigns Queue — Phase 2

**Product:** LC-Flow (`LCP061000`, `LCSS61000`, `LCA061000`)  
**Owner contact:** James Gallagher · 610-393-1102 · Jgallagher10@gmail.com  
**Date:** 2026-09-26 PT  
**Rule:** No form submits, no vendor emails, no paid spend without explicit James approval. NDA before specs/pricing.

**Research packets:**  
- `AEROSPACE_SPACE_CATALOG_CHANNELS.md`  
- `OEM_KRONES_SIDEL_CAMPAIGN.md`  
- Prior: `DISTRIBUTOR_CATALOG_INTEGRATION.md`, `MSC_SUPPLIER_APPLICATION_DRAFT.md`, `ZORO_SELL_ON_ZORO_APPLICATION_DRAFT.md`

---

## Priority legend

| Priority | Meaning |
|----------|---------|
| **P0** | Blocked only on human approval to execute this week |
| **P1** | Highest ROI / lowest friction discovery |
| **P2** | Strong fit; prepare packet then approve apply/BD |
| **P3** | Good fit; longer cycle or secondary OEM |
| **P4** | Long-cycle / high bar |
| **P5–P6** | Closed or low category fit — hold unless pull |

**Action types:** `apply` (open form) · `BD` (outreach / relationship) · `portal` (register / await invite) · `marketplace` (seller membership) · `research` (done / light follow-up)

**Packet status:** `ready_draft` · `needs_counsel_nda` · `needs_gtin_photos` · `research_complete` · `blocked_policy`

---

## Queue (prioritized)

| Pri | Campaign / Channel | Action type | Packet status | Seed `channel` name | Next **human approval** step |
|-----|-------------------|-------------|-----------------|---------------------|------------------------------|
| P1 | Thomasnet claim + aerospace/pneumatic categories | apply | research_complete | `Thomasnet` | Approve claiming company profile + public one-pager upload (no secrets) |
| P1 | GlobalSpec Product Discovery inquiry | apply / BD | research_complete | `GlobalSpec` | Approve contacting `sales@globalspec.com` for pricing; approve any paid listing spend separately |
| P2 | MSC New Supplier Inquiry | apply | ready_draft (`MSC_SUPPLIER_APPLICATION_DRAFT.md`) | `MSC` | James reviews draft; approve **submit** of inquiry form (not done by agent) |
| P2 | Zoro Sell on Zoro | apply | ready_draft (`ZORO_SELL_ON_ZORO_APPLICATION_DRAFT.md`) | `Zoro` | James reviews draft; confirm dropship SLA; approve apply |
| P2 | Amazon Business seller | marketplace | needs_gtin_photos + blocked_policy (public vs NDA) | `Amazon Business` | Decide public-listing vs NDA-gated direct policy; approve seller account + GTINs |
| P2 | **Krones OEM** NDA outreach | BD | needs_counsel_nda; draft in `campaigns/krones-nda-outreach.md` | `Krones OEM` | Counsel OK on NDA; James approve recipient + send |
| P2 | **Sidel OEM** NDA outreach | BD | needs_counsel_nda; draft in `campaigns/sidel-nda-outreach.md` | `Sidel OEM` | Counsel OK on NDA; James approve recipient + send |
| P2 | **PartsBase** seller info call | marketplace | research_complete | `PartsBase` | Approve booking sales/info call; approve membership fee if proposed |
| P2 | **ILS** membership conversation | marketplace | research_complete | `ILS` | Approve contacting ILS sales; approve membership if proposed |
| P3 | Fastenal supplier register | portal | research_complete | `Fastenal` | Approve supplier account registration + local branch intro |
| P3 | Motion Partner Portal | portal | research_complete | `Motion` | Approve request for New Supplier Registration Form |
| P3 | Applied supplier diversity | portal | research_complete | `Applied` | Approve registration / apply |
| P3 | **KHS OEM** NDA outreach | BD | needs_counsel_nda; draft in `campaigns/khs-nda-outreach.md` | `KHS OEM` | Verify contact; counsel NDA; James approve send |
| P3 | **Sipa OEM** NDA outreach | BD | needs_counsel_nda; draft in `campaigns/sipa-nda-outreach.md` | `Sipa OEM` | Verify contact via sipasolutions.com; counsel NDA; James approve send |
| P4 | Grainger JAGGAER | portal | research_complete | `Grainger` | Approve JAGGAER profile create + vendor contact request |
| P4 | **Boeing ESLC** capability registration | portal / BD | research_complete; QMS gap likely | `Boeing ESLC` | Approve email to `boeingassessment@boeing.com`; confirm QMS posture first |
| P5 | McMaster-Carr | BD | research_complete — **no apply URL** | `McMaster` | Hold cold apply; approve only warm intro / customer pull narrative |
| P6 | Digi-Key | apply | research_complete — **low fit** | `Digi-Key` | Defer unless electronics OEM pull; do not prioritize |

---

## Recommended next human actions (top 5)

1. **Counsel-approve Mutual NDA** for OEM outbound (Krones/Sidel first).  
2. **Approve & claim Thomasnet** profile with aerospace-adjacent + pneumatic categories (public-safe copy only).  
3. **Verify 1–2 real recipients** at Krones and Sidel; approve send of NDA-first drafts from `deliverables/campaigns/`.  
4. **Review MSC + Zoro drafts**; choose one industrial apply to submit manually when packet (W-9, COI, photos, GTIN) is ready.  
5. **Decide public marketplace policy** (Amazon/PartsBase/ILS): public catalog vs NDA-gated direct — blocks several P2 items.

---

## Explicitly out of scope this phase

- Submitting any supplier form  
- Sending email to OEMs or catalogs  
- Paying GlobalSpec / PartsBase / ILS / Amazon fees  
- SAM.gov registration (documented only in aerospace research)  
- Inventing McMaster or AVOX apply URLs  
- Merging this PR to `main` without review  

---

## Tracker API (after deploy)

```bash
API="${API:-https://closing-agent-manufacturing.onrender.com}"
curl -s "$API/distributor-listings" | jq '[.[] | {channel, priority, status, path_type, next_action}]'
curl -s "$API/distributor-listings?status=not_started" | jq .
```

New Phase 2 channels are seeded idempotently in `backend/app.py` → `_SEED_DISTRIBUTOR_LISTINGS`.
