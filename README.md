# PET Manufacturing Closing Agent

An AI-powered sales agent that identifies contacts in the **PET plastic manufacturing** industry, builds a sales funnel, crafts outreach emails, schedules meetings, responds to feedback, and processes orders.

**Targeted companies:** Amcor · Niagara Bottling · Coca-Cola · PepsiCo · Unilever

---

## Architecture

| Layer | Technology | Host |
|-------|-----------|------|
| Backend API | Python / FastAPI | **Render** |
| Frontend UI | HTML + CSS + JS | **GitHub Pages** (`/docs`) |
| Database | SQLite (file-based) | Render disk |
| AI | OpenAI GPT-4o-mini | Optional |

---

## Live Demo

| | URL |
|--|-----|
| **UI** | `https://codesurfing10.github.io/Closing-Agent-Manufacturing-` |
| **API** | `https://closing-agent-pet.onrender.com` |

---

## Features

- **Dashboard** – Sales funnel visualisation, pipeline value, key stats (including new leads count)
- **Contacts** – 10 pre-loaded PET-industry contacts; add/filter/stage management
- **Email Generation** – AI-crafted personalised outreach emails with one click
- **Meeting Scheduler** – Book meetings with AI-generated agendas
- **Order Management** – Create and track orders from Pending → Delivered
- **Feedback Handler** – Log customer feedback and get an AI-written response
- **Daily Lead Generation** – Automatic AI-powered lead discovery every 24 hours; manually trigger via the Leads view
- **AI Agent Chat** – Natural-language interface to run any sales task
- **Gemini Integration** – Uses Google Gemini as an AI backend when OpenAI is unavailable

---

## Deploy to Render

1. Fork / push this repo to GitHub.
2. Go to [render.com](https://render.com) → **New Web Service**.
3. Connect the GitHub repo; Render auto-detects `render.yaml`.
4. Set the environment variable **`OPENAI_API_KEY`** (optional – the app runs without it using template responses).
5. Set **`ALLOWED_ORIGINS`** to `https://<your-github-username>.github.io` (comma-separated list).
6. Deploy. Note the service URL (e.g. `https://closing-agent-pet.onrender.com`).

### Manual deploy (local test)

```bash
cd backend
pip install -r requirements.txt
OPENAI_API_KEY=sk-... uvicorn app:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`.

---

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
| `POST` | `/emails/generate` | AI-generate outreach email |
| `POST` | `/emails/{id}/send` | Mark email sent |
| `POST` | `/meetings` | Schedule meeting + AI agenda |
| `POST` | `/orders` | Create order |
| `PUT` | `/orders/{id}/status` | Update order status |
| `POST` | `/feedback` | Log feedback + AI response |
| `GET` | `/funnel` | Funnel stats & dashboard data |
| `POST` | `/leads/generate` | AI-generate new leads (saves to DB) |
| `GET` | `/leads` | List leads (filter by `status`) |
| `PUT` | `/leads/{id}/status` | Update lead status |
| `POST` | `/leads/{id}/convert` | Promote lead to contact |
| `DELETE` | `/leads/{id}` | Delete lead |
| `POST` | `/agent/run` | Natural-language agent endpoint |

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
