# LC-Flow Closing Agent (Manufacturing)

An AI-powered sales agent for the **LC-Flow Valve and Distribution Adaptor** (PTC Inc / Industrial and Molecular Solutions). It identifies multi-industry contacts, builds a sales funnel, crafts outreach emails, schedules meetings, responds to feedback, and processes orders — with **Mutual NDA gating** before sharing specs or pricing.

**Focus industries:** Aerospace · Beverage / PET Packaging · PET Air Conveyors · Automotive Engineering  
**Legacy PET contacts** (Amcor · Niagara Bottling · Coca-Cola · PepsiCo · Unilever) remain seeded.

**Package version:** 1.1.0 (NDA-gated sales)

---

## Architecture

| Layer | Technology | Host |
|-------|-----------|------|
| Backend API | Python / FastAPI | **Render** (`backend/`) |
| Frontend UI | HTML + CSS + JS | **GitHub Pages** (`/docs`) |
| Database | SQLite (file-based) | Render disk |
| AI | OpenAI GPT-4o-mini / Gemini | Optional |

---

## Live Demo

| | URL |
|--|-----|
| **UI** | `https://codesurfing10.github.io/Closing-Agent-Manufacturing-` |
| **API** | `https://closing-agent-pet.onrender.com` |

> After merging this LC-Flow update, **redeploy the Render service** so `/health` reports `"product": "LC-Flow Valve"` and `/inventory` lists the three SKUs. The live API may 404 until redeployed.

---

## Features

- **Dashboard** – Sales funnel visualisation, pipeline value, key stats (including new leads count)
- **Contacts** – Pre-loaded PET-industry contacts; add/filter/stage management; `nda_signed` flag
- **Inventory** – LC-Flow SKUs (`LCP061000`, `LCSS61000`, `LCA061000`) with list prices; Inventory UI view
- **Opportunities** – Pipeline opportunities; all require NDA (`nda_required`, default `nda_status=Pending`)
- **NDA gating** – Emails, meeting agendas, and `/agent/run` withhold detailed specs/pricing until NDA is signed
- **Email Generation** – AI-crafted outreach (NDA-first when unsigned)
- **Meeting Scheduler** – Book meetings with AI-generated agendas (NDA confirmation as item #1 when unsigned)
- **Order Management** – Create and track orders from Pending → Delivered
- **Xometry manufacturing handoff** – On `Confirmed` (+ optional PO), enqueue mock/manual manufacturing job with human approve gate (no auto-charge)
- **Feedback Handler** – Log customer feedback and get an AI-written response
- **Multi-industry Lead Generation** – Aerospace, Beverage/PET, PET Air Conveyors, Automotive Engineering (`industry_focus` on `POST /leads/generate`)
- **AI Agent Chat** – Natural-language interface to run any sales task
- **Gemini Integration** – Uses Google Gemini as an AI backend when OpenAI is unavailable

---

## LC-Flow inventory (seeded on startup)

| SKU | Material | List (pack of 2) |
|-----|----------|------------------|
| `LCP061000` | PC-ISO Plastic | $145.38 |
| `LCSS61000` | 316L Stainless Steel | $558.28 |
| `LCA061000` | Aluminum AlSiMg | $1,545.28 |

Offline CRM exports and sales collateral live under [`deliverables/`](deliverables/):

| File | Contents |
|------|----------|
| `inventory.json` / `.csv` | Parent product + 3 SKUs |
| `leads.json` / `.csv` | 28 multi-industry leads (7 per focus industry) |
| `opportunities.json` / `.csv` | 14 opportunities, pipeline ~$302,918.72, all NDA Pending |
| `NDA_TEMPLATE.md` | Mutual NDA template (**counsel review required before customer use**) |
| `SALES_BRIEF.md` | Pitch, ICP, top opportunities, NDA workflow, curl examples |
| `XOMETRY_INTEGRATION_RESEARCH.md` | API gap research + recommended architecture |
| `XOMETRY_HANDOFF.md` | Operator guide for mock/manual Xometry flow |

---

## NDA workflow (all sales discussions)

1. Create NDA record: `POST /ndas` with `contact_id` or `lead_id` and `document_ref` → `deliverables/NDA_TEMPLATE.md`
2. Send Mutual NDA to prospect (template is **not legal advice** — counsel must approve)
3. On signature: `PUT /ndas/{id}/status` `{"status":"signed"}` (sets `contacts.nda_signed=1`)
4. Only then: technical emails, pricing, drawings, samples discussion

```bash
export API=https://YOUR-RENDER-SERVICE.onrender.com
curl -s -X POST "$API/ndas" -H 'Content-Type: application/json' \
  -d '{"contact_id":"<UUID>","document_ref":"deliverables/NDA_TEMPLATE.md"}'
curl -s -X PUT "$API/ndas/<NDA_ID>/status" -H 'Content-Type: application/json' \
  -d '{"status":"signed"}'
curl -s "$API/inventory"
```

---

## Deploy to Render

1. Merge this PR (or push to `main`), then trigger a Render redeploy.
2. Render auto-detects `render.yaml` (`rootDir: backend`).
3. Set **`OPENAI_API_KEY`** and/or **`GEMINI_API_KEY`** (optional — template responses without keys).
4. Set **`ALLOWED_ORIGINS`** to `https://codesurfing10.github.io` (comma-separated list).
5. Confirm after deploy:
   - `GET /health` returns `"product": "LC-Flow Valve"`
   - `GET /inventory` lists three SKUs with list prices 145.38 / 558.28 / 1545.28

### Manual deploy (local test)

```bash
cd backend
pip install -r requirements.txt
OPENAI_API_KEY=sk-... uvicorn app:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

---


## Xometry manufacturing handoff (mock + manual)

There is **no public buyer Instant Quote / place-order API**. Closing Agent ships a handoff layer that works offline today and never auto-charges.

**Flow (prose):** Customer PO received → `PUT /orders/{id}/status` with `status=Confirmed` and optional `po_number` → `on_po_acquired` creates an idempotent `manufacturing_jobs` row → mode `mock` starts `queued` with fake quote/job IDs and ETA; mode `manual` starts `awaiting_human` with an RFQ checklist → human clicks **Approve Xometry handoff** (`POST /manufacturing/jobs/{id}/approve-xometry`) → status `submitted` (manual: you still place the order on xometry.com) → in `mock`, **Mock advance** steps `submitted` → `in_production` → `shipped` → `delivered` and mirrors the order status. Mode `api` returns a clear error unless `XOMETRY_API_KEY` is set; even then approve is required and no paid placement is called.

SKU map: `LCP061000` → FDM / PC-ISO · `LCSS61000` → DMLS / Stainless Steel 316/L · `LCA061000` → DMLS / Aluminum AlSi10Mg.

Operator guide: [`deliverables/XOMETRY_HANDOFF.md`](deliverables/XOMETRY_HANDOFF.md). Research: [`deliverables/XOMETRY_INTEGRATION_RESEARCH.md`](deliverables/XOMETRY_INTEGRATION_RESEARCH.md).

## Enable GitHub Pages

1. Go to **Settings → Pages** in this repo.
2. Set source to **`main` branch / `docs` folder**.
3. Open `docs/app.js` and update `API_BASE` to your Render URL:
   ```js
   const API_BASE = "https://closing-agent-pet.onrender.com";
   ```
4. Push the change – GitHub Pages will redeploy automatically.

---

## API Reference (summary)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/contacts` | List contacts (filter by `company`, `stage`) |
| `POST` | `/contacts` | Add contact |
| `PUT` | `/contacts/{id}/stage` | Update funnel stage |
| `POST` | `/emails/generate` | AI-generate outreach email (NDA-gated) |
| `POST` | `/emails/{id}/send` | Mark email sent |
| `POST` | `/meetings` | Schedule meeting + AI agenda (NDA-gated) |
| `POST` | `/orders` | Create order (optional `status`, `po_number`) |
| `PUT` | `/orders/{id}/status` | Update order status (+ optional `po_number`; Confirmed enqueues mfg job) |
| `GET` | `/orders/{id}/manufacturing` | Manufacturing job for order |
| `GET` | `/manufacturing/jobs` | List manufacturing jobs |
| `GET` | `/manufacturing/jobs/{id}` | Get job |
| `PUT` | `/manufacturing/jobs/{id}/status` | Update job status (mirrors order when in_production/shipped/delivered) |
| `POST` | `/manufacturing/jobs/{id}/approve-xometry` | Human gate → submitted (no auto-charge) |
| `POST` | `/manufacturing/jobs/{id}/mock-advance` | Mock-only: step one stage forward |
| `POST` | `/feedback` | Log feedback + AI response |
| `GET` | `/funnel` | Funnel stats & dashboard data |
| `GET` / `POST` | `/inventory` | List / create inventory items |
| `GET` / `PUT` | `/inventory/{sku}` | Get / update SKU |
| `GET` / `POST` | `/ndas` | List / create NDA records |
| `PUT` | `/ndas/{id}/status` | Set NDA status (`pending` \| `signed` \| `declined`) |
| `GET` / `POST` | `/opportunities` | List / create opportunities (NDA required) |
| `POST` | `/leads/generate` | AI-generate leads (`industry_focus` optional) |
| `GET` | `/leads` | List leads (filter by `status`) |
| `PUT` | `/leads/{id}/status` | Update lead status |
| `POST` | `/leads/{id}/convert` | Promote lead to contact |
| `DELETE` | `/leads/{id}` | Delete lead |
| `POST` | `/agent/run` | Natural-language agent endpoint (NDA-gated) |

Full interactive docs: `<API_URL>/docs`

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | No | Enables OpenAI GPT-4o-mini. Takes priority over Gemini when set. |
| `GEMINI_API_KEY` | No | Enables Google Gemini 1.5 Flash. Used as fallback when OpenAI is unavailable. |
| `ALLOWED_ORIGINS` | Yes | Comma-separated list of allowed CORS origins (your GitHub Pages URL) |
| `DB_PATH` | No | SQLite file path (default: `closing_agent.db`) |
| `LEAD_GEN_INTERVAL_SECS` | No | How often the background lead generator runs in seconds (default: `86400` = 24 h) |
| `XOMETRY_MODE` | No | `mock` (default) \| `manual` \| `api` |
| `XOMETRY_API_KEY` | No | Partner/API key; without it `api` mode errors. Never auto-charges. |
| `XOMETRY_API_BASE` | No | Default `https://api.developer.xometry.com` |
| `XOMETRY_MOCK_LEAD_DAYS` | No | Mock ETA lead time (default `10`) |
| `XOMETRY_SHIP_TO_JSON` | No | Default ship-to JSON for RFQ checklist |
| `XOMETRY_CAD_DIR` | No | Local/secure CAD directory hint for checklist |

---

## Changelog — LC-Flow 1.2.0 (Xometry handoff)

- `manufacturing_jobs` table + `orders.po_number`
- Hook on Confirmed → mock/manual Xometry job; human `approve-xometry` gate
- UI: PO field, mfg status, Approve / Mock advance
- Docs: `XOMETRY_HANDOFF.md`, research committed

## Changelog — LC-Flow 1.1.0

- New SQLite tables: `inventory`, `opportunities`, `ndas`; contacts gain `nda_signed`
- Idempotent seed of 3 LC-Flow SKUs on startup
- Multi-industry lead generation (`_LEAD_GEN_TARGETS`)
- NDA enforcement in email, agenda, and agent sales flows
- Docs Inventory nav + table view; LC-Flow branding
- `deliverables/` offline inventory, leads, opportunities, NDA template, sales brief

**Important:** Have counsel review `deliverables/NDA_TEMPLATE.md` before customer use. Redeploy Render after merge.
