# LC-Flow Valve — Distributor Catalog & Electronic Offering Integration

**Product:** LC-Flow Valve and Distribution Adaptor  
**Manufacturer:** PTC Inc | **Distributor:** Industrial and Molecular Solutions  
**Contact:** James Gallagher · 610-393-1102 · Jgallagher10@gmail.com  
**SKUs:** LCP061000 (PC-ISO, $145.38/pack of 2) · LCSS61000 (316L SS, $558.28) · LCA061000 (AlSiMg, $1,545.28)  
**Date:** 2026-09-23 PT  
**Scope:** Research — paths, links, checklist, and Closing-Agent feature proposals. The **distributor listing tracker** (table + APIs) is implemented in Closing Agent (see `deliverables/DISTRIBUTOR_LISTING_TRACKER.md`). Other proposals (inventory feed export, punchout, auto form-fill) remain optional / future. Do **not** submit MSC/Zoro forms or touch production deploy from this research alone.

---

## Executive summary

Large industrial catalogs fall into three buckets for a small specialty manufacturer:

| Path type | What it means for LC-Flow | Examples |
|-----------|---------------------------|----------|
| **Open apply / marketplace** | Self-serve form or seller account; still subject to review | MSC New Supplier Inquiry, Zoro Sell on Zoro, Amazon Business (Seller Central), Thomasnet claim, GlobalSpec paid listing |
| **Portal register + category review** | Register in supplier network; listing only if category managers need the line | Grainger (JAGGAER), Fastenal supplier portal, Motion Industries Partner Portal, Applied supplier diversity |
| **Closed / invite / relationship** | No public “list my SKU” path; BD and customer pull | McMaster-Carr; often Digi-Key / Mouser / RS for non-core electronic lines |

**Realistic near-term wins for LC-Flow:** (1) product-data package + GTINs, (2) Thomasnet + GlobalSpec for discovery leads, (3) Amazon Business and/or Zoro for electronic sell-through, (4) MSC / Fastenal branch or Product Management applications, (5) Grainger JAGGAER registration as a longer-cycle play. **McMaster-Carr should be treated as relationship/BD, not an application portal.**

---

## 1. Distributor-by-distributor paths

### 1.1 Grainger (W.W. Grainger)

| Item | Finding |
|------|---------|
| **Path** | **Apply / register** in supplier network + category review. **Not** a self-serve catalog upload marketplace for new SKUs. |
| **Reality** | New suppliers create a profile on Grainger’s **JAGGAER Supplier Network**. Invitation to sourcing events and actual assortment adoption are category-driven. Diverse / small suppliers often also pursue certification (NMSDC, WBENC, etc.) and Supplier Diversity channels. Public `grainger.com/content/supplier-overview` returned **404** when checked (2026-09-23); do not rely on that URL. |
| **EDI / feeds** | Once approved as a supplier, Grainger typically expects structured item data and shipping/compliance docs; EDI/cXML specifics are **not** published as a public “apply then upload 832” path for prospects. Expect onboarding docs after acceptance. |
| **LC-Flow fit** | Strong category adjacency (pneumatics, lubrication, MRO). Small specialty / 3D-printed line may sit in backlog until a category manager has demand or a national account pulls the part. |

**Official / verified links**

- JAGGAER supplier login / create account (CustOrg=WWGrainger): https://solutions.sciquest.com/apps/Router/SupplierLogin?CustOrg=WWGrainger  
- Prospective supplier/vendor contact request form: https://e.grainger.com/pub/sf/ResponseForm?_ei_=Eh1I4V9O_M_RJgog4D7QtDY&_ri_=X0Gzc2X%3DYQpglLjHJlYQGnHTm1zbMllgzazfjhr3zf8RizbyzbOzc7iCGPe6BhVXMtX%3DYQpglLjHJlYQGh8LEJzfdy01Jpv9ufPoGSzgzczbOzc7iCGPe6Bh  
- Supplier maintenance email (login/profile issues): `Supplier_Maintenance@Grainger.com`  
- Reseller / Distributor Alliance (different path — for resellers of Grainger, not manufacturers listing into Grainger): `Distributor_Alliance@grainger.com` (noted on contact form)

**Action for James:** Register on JAGGAER; submit Supplier/Vendor Request; prepare one-pager + UNSPSC/NAICS; optionally pursue diversity cert if eligible. Expect months, not days.

---

### 1.2 McMaster-Carr

| Item | Finding |
|------|---------|
| **Path** | **Invite / relationship / closed catalog.** No public “become a supplier” or “submit SKU” application found. |
| **Reality** | McMaster curates a large fixed assortment. Supplier Operations roles (job postings) describe evaluating product literature and deciding what enters the database — i.e., **McMaster chooses**, suppliers do not self-list. Industry practice: customer demand, existing supplier relationships, or direct outreach to purchasing/supplier ops. |
| **API note** | McMaster publishes a **Product Information API for approved customers** to *pull* catalog data into e-procurement — **not** a supplier feed API to push new parts. Contact for that API: `eprocurement@mcmaster.com`. |
| **LC-Flow fit** | High customer visibility if listed, but **low probability via cold application**. Treat as BD: warm intro, end-customer pull-through, or samples to a buyer/category contact. |

**Official / verified links**

- Contact (customer service): https://www.mcmaster.com/contact — `sales@mcmaster.com`, (630) 833-0300  
- Product Information API (buyer-side): https://www.mcmaster.com/help/api/  
- Terms (product info comes from suppliers; McMaster controls catalog): https://www.mcmaster.com/termsandconditions  

**No public supplier application URL found** — do not fabricate one. Outreach: ask Customer Service to route to Supplier Operations / purchasing with a capability package (after NDA if sharing detailed IP).

---

### 1.3 MSC Industrial Supply

| Item | Finding |
|------|---------|
| **Path** | **Apply** via New Supplier Inquiry form. Clear public path. |
| **Reality** | Product Management reviews submissions. Form asks business type, revenue bands, first-year MSC potential, market share, competitors (explicitly lists Grainger / McMaster / Fastenal), and product line (includes **Pneumatics & Hydraulics**, **Lubrication**, **Hose/Tube/Fittings** — good LC-Flow matches). Prefers barcoding. Optional SupplierGATEWAY registration for broader visibility. Small/diverse businesses use the same inquiry path with certification noted. |
| **LC-Flow fit** | **High priority** among traditional distributors: open form, category match, MRO/industrial focus. |

**Official / verified links**

- Industrial suppliers overview: https://www.mscdirect.com/customer-service/supplier-support/industrial-suppliers  
- Alternate corporate path: https://www.mscdirect.com/corporate/industrial-suppliers  
- New Supplier Inquiry form: https://www.mscdirect.com/customer-service/new-supplier-inquiry  
- SupplierGATEWAY (MSC): https://msc.suppliergateway.com/  
- Phone: 1-800-645-7270  
- Small business / public-sector reseller (different path): `DiversityandSBprogramMgr@mscdirect.com`

---

### 1.4 Fastenal

| Item | Finding |
|------|---------|
| **Path** | **Register** as Fastenal Supplier in the supplier portal; Compliance reviews Tax ID / payment. **Branch relationship strongly helps** (5-letter store code). |
| **Reality** | Guide directs: Register on fastenal.com → account type **Fastenal Supplier** → “No, I’m not an existing supplier” → optional branch code → Compliance review. Diversity program historically uses RFI / capability statements (`suppliercert@fastenal.com` on older materials). Local branch Managers often source for vending / customer needs — good for specialty valves if a branch has an aerospace/auto/food customer asking. |
| **LC-Flow fit** | Medium–high if a local branch champions the line; cold national portal alone may be slow. |

**Official / verified links**

- New/potential supplier registration guide (PDF): https://crafter.fastenal.com/static-assets/pdfs/FNL-NewSupplierRegistrationGuide_US_CAN.pdf  
- Older mirror of guide: https://www.fastenal.com/content/documents/2015/10/SupplierPortalRegGuide-NewSuppliers.pdf  
- Supplier Compliance: `suppliercompliance@fastenal.com`  
- Site for registration: https://www.fastenal.com (My Account → Register → Fastenal Supplier)

---

### 1.5 Zoro (Grainger-affiliated digital channel)

| Item | Finding |
|------|---------|
| **Path** | **Partnership application** via Sell on Zoro — **not** an open Amazon-style marketplace where anyone lists overnight. |
| **Reality** | Zoro dropships; partners supply full product data, images/attributes, regular inventory updates, US warehouse shipping, and typically EDI (850/855/856/846/810 — SPS Commerce and similar networks commonly used). Zoro owns merchandising/pricing presentation. Contact historically also cited: `businessdevelopment@zoro.com`. |
| **LC-Flow fit** | **Strong electronic path** if IMS can dropship packs, provide clean feed data, and support inventory updates. SKU count is tiny (3) — emphasize uniqueness (3D-printed materials, aerospace/PET use cases) over catalog breadth. |

**Official / verified links**

- Sell on Zoro: https://www.zoro.com/sell-on-zoro/  
- EDI partner example (third-party network page, not Zoro-owned): https://www.spscommerce.com/network/find-a-partner/view/zoro/

---

### 1.6 Amazon Business (industrial / B2B)

| Item | Finding |
|------|---------|
| **Path** | **Marketplace / Seller Central** — most open electronic offering among targets. Professional seller account → B2B Central tools. |
| **Reality** | Create listings (need GTIN or Brand Registry / exemption path as applicable), set business prices and quantity discounts, optional FBA or FBM, certifications on seller profile. Amazon Business punchout is buyer-side; sellers use SP-API for inventory/pricing automation. Brand Registry recommended if trademark exists. |
| **LC-Flow fit** | Fastest path to “listed electronically” for SMB/MRO buyers. Margin + MAP + Amazon fees must be modeled. NDA policy for *direct* sales does not map cleanly to public Amazon listings — **open question for user** (public catalog vs NDA-gated direct). |

**Official / verified links**

- Amazon Business for sellers: https://sell.amazon.com/programs/amazon-business  
- Brand Registry: https://sell.amazon.com/brand-registry  
- Seller Central (account required): https://sellercentral.amazon.com  

---

### 1.7 Thomasnet (Thomas)

| Item | Finding |
|------|---------|
| **Path** | **Claim / list company** (free profile) + optional paid Verified / premium. Discovery directory, not stocking distributor. |
| **Reality** | Buyers RFQ / source manufacturers. Claim profile, categories, logo, analytics. Upgrade for better placement. Excellent for inbound industrial leads into Closing-Agent. |
| **LC-Flow fit** | **Do first** — low cost, high discovery, aligns with aerospace/auto/beverage ICPs. |

**Official / verified links**

- Claim / get listed: https://business.thomasnet.com/get-listed-on-thomasnet?nav_src=utilitynav  

---

### 1.8 GlobalSpec / IEEE GlobalSpec

| Item | Finding |
|------|---------|
| **Path** | **Paid Product Discovery / advertising** — list products for engineers and technical buyers; RFQ leads. |
| **Reality** | Submit product specs; GlobalSpec places searchable listings; quote requests delivered as leads. Contact sales for pricing. Not a fulfillment catalog. |
| **LC-Flow fit** | High for engineer-led pneumatic/fluid control discovery; complements Thomasnet. |

**Official / verified links**

- List your products: https://advertising.globalspec.com/list-your-products/  
- Advertising home: https://advertising.globalspec.com/  
- Sales: `sales@globalspec.com` · 800-261-2052  

---

### 1.9 Motion Industries

| Item | Finding |
|------|---------|
| **Path** | **Apply** — request New Supplier Registration Form via Partner Portal; Corporate Purchasing / Supplier Relations / Product Management review. **Also:** Branch Office Purchase Program (local Branch Manager + Indemnity Agreement). |
| **Reality** | Strong in pneumatics, hose, power transmission, MRO. Submission **does not guarantee** acceptance; only advancing candidates are contacted. Diversity certifications can be indicated on the form. |
| **LC-Flow fit** | Good category fit; pursue national form **and** local branch if IMS has regional coverage. |

**Official / verified links**

- Supplier process: https://www.motionpartnerportal.com/Supplier-Process/  
- Partner portal FAQ (support email cited in search): `partnerportal@motion.com`  
- Phone: 1-800-526-9328  

---

### 1.10 Applied Industrial Technologies

| Item | Finding |
|------|---------|
| **Path** | **Apply** via Supplier Diversity / become-a-supplier flow on applied.com (sign-in/register; review Supplier Code of Conduct). Local service centers also used for introductions. |
| **Reality** | Evaluation on quality, customer fit, compliance. Cloudflare often gates the page for automated fetches; URL itself is the official landing. |
| **LC-Flow fit** | Medium–high for industrial pneumatics / fluid power adjacency. |

**Official / verified links**

- Supplier Diversity: https://www.applied.com/supplier-diversity  

*(Public purchase terms pages exist under Applied’s site; use the diversity/apply path for onboarding, not medical or aerospace-named “Applied*” entities that are different companies.)*

---

### 1.11 Digi-Key

| Item | Finding |
|------|---------|
| **Path** | **Apply** — Prospective Supplier Questionnaire PDF → email `newsuppliers@digikey.com`. |
| **Reality** | Core business is electronic components. Digi-Key has Marketplace / Fulfilled by Digi-Key / traditional programs. LC-Flow is **pneumatic/fluidic hardware**, not a typical Digi-Key line — expect low priority unless framed as interconnect/fluidics for electronics manufacturing or automation. |
| **LC-Flow fit** | Low priority unless user has electronics OEM pull. |

**Official / verified links**

- Questionnaire PDF: https://www.digikey.com/-/media/PDF/Help/SupplierQuestionnaire.PDF  
- Email: `newsuppliers@digikey.com` (include company name in subject)  
- Supplier APIs (existing suppliers): https://developer.digikey.com/how-can-apis-help-you/apis-digikey-suppliers  

---

### 1.12 Mouser Electronics

| Item | Finding |
|------|---------|
| **Path** | **No public open supplier application URL found.** Manufacturer line-card expansion is relationship / product-management driven. |
| **Reality** | Mouser adds manufacturers selectively (electronics-focused). New-manufacturer marketing pages exist for *customers* browsing new lines, not for vendor self-service signup. |
| **LC-Flow fit** | Low unless electronics fluidics niche. |

**What to do:** Contact Mouser manufacturer / supplier relations via general sales channels (e.g. site contact / `sales@mouser.com` — confirm current vendor desk when calling). **Do not claim a dedicated “apply here” URL was found.**

---

### 1.13 RS Components (RS Group / RS Online)

| Item | Finding |
|------|---------|
| **Path** | **No clear public US/global “become a supplier” application URL found** in this research pass. Existing suppliers use internal supplier portals and RS contacts. |
| **Reality** | Strong in industrial automation / pneumatics in some regions; onboarding appears rep-mediated. |
| **LC-Flow fit** | Defer until EU/UK demand or RS category contact identified. |

**Open item:** User or BD to request supplier onboarding contact from local RS sales — URL not fabricated.

---

## 2. Electronic catalog standards (what buyers and distributors expect)

| Standard | Role | Relevance to LC-Flow / Closing-Agent |
|----------|------|--------------------------------------|
| **cXML PunchOut** | Buyer’s procurement system (Ariba, Coupa, etc.) sessions into a supplier catalog; cart returns as cXML | Usually implemented by **large distributors** (Grainger, McMaster, MSC) for *their* customers — not something a 3-SKU specialty maker must build first. Optional later for IMS direct e-proc if enterprise accounts demand it. |
| **EDI 832** | Price / sales catalog | Distributors may require 832 (or spreadsheet equivalent) after vendor approval. |
| **EDI 846** | Inventory inquiry / advice | Zoro and many dropship partners want regular inventory updates (EDI 846 or API/CSV). Maps cleanly to Closing-Agent `inventory` stock_qty. |
| **EDI 850 / 855 / 856 / 810** | PO / ack / ASN / invoice | Order cycle once a distributor partnership is live. |
| **Google Merchant Center** | Free/product ads & Shopping feeds | Possible for Amazon-adjacent or direct web store; needs GTIN/MPN, price, availability, image. B2B-only / NDA-gated offers are a poor fit for public Merchant feeds. Spec: https://support.google.com/merchants/answer/7052112 |
| **UNSPSC** | Classification for punchout / e-proc / diversity portals | Assign on every item record (see below). |
| **GTIN (UPC/EAN) / MPN** | Listing keys for Amazon, Zoro, MSC barcoding | Critical path item if missing today. |

### Suggested UNSPSC candidates for LC-Flow

Pick **one primary** per SKU for feed consistency; note alternates in internal data.

| Code | Name | When to use |
|------|------|-------------|
| **40141603** | Pneumatic valves | Primary if sold as flow/pressure control valve |
| **40141609** | Control valves | Broader control / distribution apparatus framing |
| **40141651** | Air valve | Alternate air-system framing |
| **27131614** | Pneumatic adapters | If marketed primarily as distribution adaptor / fitting |
| **27131604** | Pneumatic lubricators | Only if lubrication-system SKU positioning is primary |

Also prepare **NAICS** (e.g. fluid power / valve manufacturing — confirm with accountant) for Grainger/MSC portals.

---

## 3. Recommended priority order for LC-Flow

| Priority | Channel | Why | Effort / cost |
|----------|---------|-----|----------------|
| **P0** | Product data package (specs, photos, CAD redacted or NDA, SDS/CoC, UNSPSC, GTIN) | Unlocks every other channel | Internal — days to weeks |
| **P1** | Thomasnet claim + categories | Free discovery → Closing-Agent leads | Low |
| **P1** | GlobalSpec Product Discovery inquiry | Engineer RFQs; paid | Medium $ |
| **P2** | MSC New Supplier Inquiry | Open form; category match | Low–medium |
| **P2** | Zoro Sell on Zoro | Digital industrial sell-through + inventory feed | Medium (EDI/dropship) |
| **P2** | Amazon Business (Professional seller) | Fastest electronic listing | Medium (fees, content, brand) |
| **P3** | Fastenal supplier register + **local branch** pitch | Branch can stock for named customers | Medium |
| **P3** | Motion Industries Partner Portal (+ optional branch) | Pneumatics adjacency | Medium |
| **P3** | Applied supplier diversity apply | Industrial fluid power network | Medium |
| **P4** | Grainger JAGGAER + vendor contact request | Large upside, slow category gate | Medium–high time |
| **P5** | McMaster-Carr | Closed; BD / customer pull only | High uncertainty |
| **P6** | Digi-Key / Mouser / RS | Weak category fit unless electronics OEM pull | Low priority |

---

## 4. Product data package checklist (for listings)

Prepare a **distributor-ready kit** per SKU (and a parent brand sheet). Closing-Agent already holds SKU, price, stock, material — extend with the rest.

### Identity & commerce

- [ ] Legal entity (PTC Inc vs Industrial and Molecular Solutions) — who is the **seller of record** on each channel  
- [ ] Brand name for Brand Registry / packaging  
- [ ] SKU / MPN: `LCP061000`, `LCSS61000`, `LCA061000`  
- [ ] **GTIN/UPC** per sellable pack (pack of 2) — obtain if missing  
- [ ] Country of origin, HTS/Schedule B, ECCN / export classification  
- [ ] List price, distributor net / MAP policy, case pack = 2  
- [ ] Lead time, MOQ, reorder point, warranty  

### Classification

- [ ] Primary **UNSPSC** (recommend start with `40141603` or `27131614`)  
- [ ] NAICS / SIC  
- [ ] Keywords: pneumatic valve, flow control, distribution adaptor, lubrication, airline, aerospace fluidic, PET air conveyor  

### Technical content (respect NDA policy)

- [ ] Public one-pager (category-safe, no secret process detail)  
- [ ] Full datasheet (NDA or controlled release)  
- [ ] Dimensional drawing / CAD (STEP/IGES) — watermark or NDA gate as needed  
- [ ] Materials: PC-ISO / 316L / AlSiMg; process note (additive) at allowed depth  
- [ ] Pressure / media / temperature ratings (as releasable)  
- [ ] Certifications: ISO, material certs, RoHS/REACH if applicable, aerospace quality docs if claimed  

### Compliance & logistics

- [ ] SDS if any process chemicals / packaging materials require  
- [ ] COA / material test reports for SS and Al SKUs  
- [ ] Barcode label spec (MSC preference)  
- [ ] Packaging dimensions, weight, hazmat (usually none)  
- [ ] Insurance / COI, W-9, banking for supplier portals  

### Media

- [ ] White-background product photos (multiple angles) per SKU  
- [ ] Application lifestyle images (PET line, aerospace GSE — rights-cleared)  
- [ ] Short demo video (optional)  

### Channel-specific extras

- [ ] Amazon: A+ content, business price tiers, FBA vs FBM decision  
- [ ] Zoro: attribute spreadsheet + inventory update cadence  
- [ ] Grainger/MSC/Motion: competitive cross-refs (who they sell today vs LC-Flow differentiation)  

---

## 5. What Closing-Agent could automate vs what stays human/BD

### Already in Closing-Agent (usable as foundation)

- Inventory SKUs + stock_qty + list prices (`inventory.json` / `/inventory`)  
- Leads, opportunities, NDA gating  
- Sales brief / outreach assets  

### Closing-Agent features — status

| Feature | Automate? | Status / Notes |
|---------|-----------|----------------|
| **Distributor application tracker** | Partial | **Implemented** — SQLite `distributor_listings` + REST APIs (`/distributor-listings`). See `deliverables/DISTRIBUTOR_LISTING_TRACKER.md`. |
| **Inventory export feed** | Yes | **Not yet** — CSV/JSON/EDI-846-shaped export of `sku, gtin, qty, price, lead_time, unspsc` for Zoro/Amazon/SPS (optional future) |
| **Distributor lead channel** | Yes | Ingest Thomasnet/GlobalSpec RFQ emails or form webhooks → `leads` with source=`thomasnet`/`globalspec` |
| **Public vs NDA content packs** | Yes | Two asset bundles: public catalog fields vs NDA-only CAD/specs |
| **Punchout / cXML host** | Later / unlikely soon | Expensive; only if a Fortune account demands IMS punchout vs buying via Grainger/MSC |
| **Supplier portal form fill** | **No / human** | Legal entity, tax, banking, wet signatures — BD + James |
| **McMaster / Grainger category sell-in** | **Human BD** | Samples, plant visits, national account pull-through |
| **Pricing / MAP decisions** | **Human** | Channel conflict Grainger vs Amazon vs direct |
| **EDI VAN / SPS contracts** | **Human + vendor** | Closing-Agent can emit files; commercial EDI onboarding is external |

---

## 6. Realistic path summary matrix

| Distributor / channel | Path | Public apply URL found? |
|----------------------|------|-------------------------|
| Grainger | Register JAGGAER + vendor contact; category review | Yes — JAGGAER + contact form |
| McMaster-Carr | Closed / relationship | **No** supplier apply URL |
| MSC | New Supplier Inquiry | Yes |
| Fastenal | Supplier portal register (+ branch) | Yes — guide + fastenal.com register |
| Zoro | Sell on Zoro partnership | Yes |
| Amazon Business | Seller Central Professional | Yes |
| Thomasnet | Claim company (free/paid) | Yes |
| GlobalSpec | Paid Product Discovery | Yes |
| Motion Industries | New Supplier Registration (request form) | Yes — process page; form via support |
| Applied Industrial | Supplier diversity / apply | Yes — landing page |
| Digi-Key | Questionnaire email | Yes — PDF + email |
| Mouser | Contact manufacturer relations | **No** open apply URL found |
| RS Components | Rep / portal (unclear public) | **No** clear public apply URL found |

---

## 7. Open questions for the user

1. **Seller of record:** Will PTC Inc or Industrial and Molecular Solutions appear on distributor / Amazon invoices? Any branding conflict?  
2. **NDA vs public catalog:** Closing-Agent currently requires NDA before detailed specs/pricing. Are Amazon/Zoro/MSC **public** list prices and datasheets allowed, or should those channels sell only after RFQ?  
3. **GTIN status:** Do the three SKUs already have UPCs? If not, budget GS1 membership?  
4. **Fulfillment:** Can IMS dropship single packs in 1–2 days (Zoro/Amazon FBM), or is distributor stock (MSC/Fastenal branch) preferred?  
5. **MAP / channel pricing:** Target distributor net vs Amazon Business price vs direct list?  
6. **Diversity certifications:** Any current or planned WBE/MBE/VOSB/etc.? Affects Grainger/MSC/Applied/Fastenal priority.  
7. **Trademark:** Is “LC-Flow” (or house brand) registered for Amazon Brand Registry?  
8. **McMaster strategy:** Pursue cold outreach now, or wait for an end-customer who will request McMaster to stock it?  
9. **CAD release policy:** Public STEP on Thomasnet/GlobalSpec vs NDA-only?  
10. **Geography:** US-only first, or also RS (EU/UK) and Digi-Key global?

---

## 8. Suggested next 30-day BD plan (human + light tooling)

1. **Week 1:** Finish product data package; assign UNSPSC; start GTIN if needed; claim Thomasnet.  
2. **Week 1–2:** Submit MSC New Supplier Inquiry; Fastenal supplier registration; inquire GlobalSpec pricing; submit Zoro Sell on Zoro.  
3. **Week 2:** Amazon Professional seller + draft listings (or hold until NDA/public policy answered).  
4. **Week 2–3:** Motion Partner Portal request; Applied supplier diversity apply; Grainger JAGGAER + contact form.  
5. **Week 3–4:** Local Fastenal / Motion branch visits with samples (SS + plastic); log every application in a simple tracker (spreadsheet or future Closing-Agent table).  
6. **Ongoing:** McMaster only via warm intro or customer pull; skip Digi-Key/Mouser/RS unless electronics demand appears.

---

## Sources checked (2026-09-23 PT)

Official or primary pages fetched/searched as cited in sections above. Third-party blogs (e.g. SupplierDiversity.com) used only as secondary color on Grainger diversity process — **prefer Grainger JAGGAER and Grainger contact form for action**. Where no public apply URL existed (McMaster, Mouser, RS), that absence is stated explicitly.
