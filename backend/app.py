"""
PET Plastic Manufacturing Closing Agent
FastAPI backend – deployable on Render
"""

from __future__ import annotations

import os
import json
import uuid
import sqlite3
import logging
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime
from typing import Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ALLOWED_ORIGINS_RAW = os.getenv(
    "ALLOWED_ORIGINS",
    "https://codesurfing10.github.io,http://localhost:3000,http://localhost:5500",
)
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
DB_PATH = os.getenv("DB_PATH", "closing_agent.db")

# ──────────────────────────────────────────────────────────────────────────────
# Database helpers
# ──────────────────────────────────────────────────────────────────────────────

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS contacts (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                title TEXT,
                company TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                linkedin TEXT,
                industry TEXT DEFAULT 'PET Plastic Manufacturing',
                stage TEXT DEFAULT 'Identified',
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS emails (
                id TEXT PRIMARY KEY,
                contact_id TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT DEFAULT 'Draft',
                sent_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            );

            CREATE TABLE IF NOT EXISTS meetings (
                id TEXT PRIMARY KEY,
                contact_id TEXT NOT NULL,
                title TEXT NOT NULL,
                scheduled_at TEXT NOT NULL,
                duration_mins INTEGER DEFAULT 30,
                location TEXT,
                agenda TEXT,
                status TEXT DEFAULT 'Scheduled',
                notes TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id TEXT PRIMARY KEY,
                contact_id TEXT NOT NULL,
                product TEXT NOT NULL,
                quantity_tons REAL NOT NULL,
                unit_price_usd REAL NOT NULL,
                status TEXT DEFAULT 'Pending',
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,
                contact_id TEXT NOT NULL,
                message TEXT NOT NULL,
                sentiment TEXT DEFAULT 'Neutral',
                response TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            );
        """)
    _seed_contacts()


# Pre-populated contacts for PET manufacturing targets
_SEED_CONTACTS = [
    {
        "name": "Sarah Mitchell",
        "title": "VP of Procurement",
        "company": "Amcor",
        "email": "s.mitchell@amcor.com",
        "phone": "+1-847-555-0182",
        "linkedin": "linkedin.com/in/sarah-mitchell-amcor",
    },
    {
        "name": "James Thornton",
        "title": "Director of Packaging Innovation",
        "company": "Amcor",
        "email": "j.thornton@amcor.com",
        "phone": "+1-847-555-0193",
        "linkedin": "linkedin.com/in/james-thornton-amcor",
    },
    {
        "name": "Linda Chávez",
        "title": "Head of Supply Chain",
        "company": "Niagara Bottling",
        "email": "l.chavez@niagarabottling.com",
        "phone": "+1-909-555-0214",
        "linkedin": "linkedin.com/in/linda-chavez-niagara",
    },
    {
        "name": "Derek Owens",
        "title": "Senior Buyer – Packaging",
        "company": "Niagara Bottling",
        "email": "d.owens@niagarabottling.com",
        "phone": "+1-909-555-0228",
        "linkedin": "linkedin.com/in/derek-owens-niagara",
    },
    {
        "name": "Patricia Huang",
        "title": "Global Packaging Director",
        "company": "Coca-Cola",
        "email": "p.huang@coca-cola.com",
        "phone": "+1-404-555-0341",
        "linkedin": "linkedin.com/in/patricia-huang-cocacola",
    },
    {
        "name": "Michael Torres",
        "title": "Procurement Manager – Resins",
        "company": "Coca-Cola",
        "email": "m.torres@coca-cola.com",
        "phone": "+1-404-555-0358",
        "linkedin": "linkedin.com/in/michael-torres-cocacola",
    },
    {
        "name": "Angela Brooks",
        "title": "Sustainability & Packaging Lead",
        "company": "PepsiCo",
        "email": "a.brooks@pepsico.com",
        "phone": "+1-914-555-0462",
        "linkedin": "linkedin.com/in/angela-brooks-pepsico",
    },
    {
        "name": "Robert Kline",
        "title": "VP Supply Chain – Beverages",
        "company": "PepsiCo",
        "email": "r.kline@pepsico.com",
        "phone": "+1-914-555-0477",
        "linkedin": "linkedin.com/in/robert-kline-pepsico",
    },
    {
        "name": "Claire Dupont",
        "title": "Category Manager – Packaging",
        "company": "Unilever",
        "email": "c.dupont@unilever.com",
        "phone": "+1-201-555-0561",
        "linkedin": "linkedin.com/in/claire-dupont-unilever",
    },
    {
        "name": "Nathan Patel",
        "title": "Head of Procurement NOAM",
        "company": "Unilever",
        "email": "n.patel@unilever.com",
        "phone": "+1-201-555-0579",
        "linkedin": "linkedin.com/in/nathan-patel-unilever",
    },
]


def _seed_contacts():
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
        if count == 0:
            now = datetime.utcnow().isoformat()
            for c in _SEED_CONTACTS:
                conn.execute(
                    """INSERT INTO contacts
                       (id, name, title, company, email, phone, linkedin,
                        industry, stage, notes, created_at, updated_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (
                        str(uuid.uuid4()),
                        c["name"], c["title"], c["company"],
                        c["email"], c["phone"], c["linkedin"],
                        "PET Plastic Manufacturing", "Identified", "",
                        now, now,
                    ),
                )


# ──────────────────────────────────────────────────────────────────────────────
# AI helpers
# ──────────────────────────────────────────────────────────────────────────────

def _ai_complete(system: str, user: str) -> str:
    """Call OpenAI ChatCompletion, fall back to template string on failure."""
    if not OPENAI_API_KEY:
        return ""
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            max_tokens=600,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as exc:
        logger.warning("OpenAI call failed: %s", exc)
        return ""


def _generate_email(contact: dict, context: str = "") -> dict:
    system = (
        "You are an expert B2B sales copywriter specialising in PET plastic resin "
        "and packaging materials. Write concise, persuasive outreach emails (≤180 words). "
        "Always include a clear value proposition and a soft call-to-action."
    )
    user = (
        f"Write a cold outreach email to {contact['name']}, {contact['title']} at "
        f"{contact['company']}. They operate in the PET plastic manufacturing / "
        f"beverage packaging industry. {context}"
        f"\nReturn ONLY JSON with keys 'subject' and 'body'."
    )
    raw = _ai_complete(system, user)
    try:
        data = json.loads(raw)
        if "subject" in data and "body" in data:
            return data
    except Exception:
        pass

    # Fallback template
    subject = f"Helping {contact['company']} Reduce PET Resin Costs by 12-18%"
    body = (
        f"Hi {contact['name'].split()[0]},\n\n"
        f"I hope this finds you well. I'm reaching out because we help leading "
        f"packaging and beverage companies like {contact['company']} secure high-grade "
        f"recycled PET (rPET) resin at competitive prices while meeting sustainability "
        f"targets.\n\n"
        f"Our clients typically see 12-18% cost savings and a 30% improvement in "
        f"recycled content ratios within the first year.\n\n"
        f"Would you have 20 minutes this week for a quick call to explore if there's "
        f"a fit?\n\n"
        f"Best regards,\n[Your Name]\n[Your Company]"
    )
    return {"subject": subject, "body": body}


def _generate_feedback_response(contact: dict, feedback_msg: str) -> str:
    system = (
        "You are a professional account manager in the PET plastic manufacturing "
        "industry. Write a warm, empathetic, and solution-focused reply to customer "
        "feedback. Keep it under 120 words."
    )
    user = (
        f"Customer: {contact['name']} ({contact['company']})\n"
        f"Feedback: {feedback_msg}\n\n"
        f"Write a professional reply."
    )
    result = _ai_complete(system, user)
    if result:
        return result
    return (
        f"Hi {contact['name'].split()[0]},\n\n"
        "Thank you for your feedback – we genuinely value your input and take it "
        "seriously. Our team will review your comments and follow up with you within "
        "24 hours with a concrete next step.\n\n"
        "Best regards,\n[Your Account Manager]"
    )


def _generate_meeting_agenda(contact: dict, context: str = "") -> str:
    system = (
        "You are a senior B2B sales professional in PET plastic manufacturing. "
        "Create a concise meeting agenda (3-5 bullet points) for a discovery call."
    )
    user = (
        f"Meeting with {contact['name']}, {contact['title']} at {contact['company']}. "
        f"{context} Generate a short agenda."
    )
    result = _ai_complete(system, user)
    if result:
        return result
    return (
        "• Introductions and company overview\n"
        "• Current PET resin sourcing volumes and pain points\n"
        "• rPET sustainability targets and timelines\n"
        "• How we can support cost reduction goals\n"
        "• Agree on next steps / pilot programme"
    )


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ──────────────────────────────────────────────────────────────────────────────

FUNNEL_STAGES = ["Identified", "Contacted", "Meeting Scheduled", "Proposal Sent", "Closed Won", "Closed Lost"]
ORDER_STATUSES = ["Pending", "Confirmed", "In Production", "Shipped", "Delivered", "Cancelled"]

class ContactCreate(BaseModel):
    name: str
    title: Optional[str] = ""
    company: str
    email: Optional[str] = ""
    phone: Optional[str] = ""
    linkedin: Optional[str] = ""
    notes: Optional[str] = ""

class ContactStageUpdate(BaseModel):
    stage: str

class EmailGenerateRequest(BaseModel):
    contact_id: str
    context: Optional[str] = ""

class EmailSendRequest(BaseModel):
    email_id: str

class MeetingCreate(BaseModel):
    contact_id: str
    title: str
    scheduled_at: str  # ISO datetime string
    duration_mins: Optional[int] = 30
    location: Optional[str] = "Video Call (Zoom)"
    context: Optional[str] = ""

class MeetingNotesUpdate(BaseModel):
    notes: str
    status: Optional[str] = None

class OrderCreate(BaseModel):
    contact_id: str
    product: str
    quantity_tons: float
    unit_price_usd: float
    notes: Optional[str] = ""

class OrderStatusUpdate(BaseModel):
    status: str

class FeedbackCreate(BaseModel):
    contact_id: str
    message: str

class AgentRunRequest(BaseModel):
    task: str
    contact_id: Optional[str] = None
    context: Optional[str] = ""

# ──────────────────────────────────────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("Database initialised. ALLOWED_ORIGINS=%s", ALLOWED_ORIGINS)
    yield


app = FastAPI(
    title="PET Manufacturing Closing Agent",
    description="AI-powered sales agent for the PET plastic manufacturing industry",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────────────────────
# Routes – Contacts
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/contacts")
def list_contacts(company: Optional[str] = None, stage: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM contacts WHERE 1=1"
        params: list = []
        if company:
            query += " AND company = ?"
            params.append(company)
        if stage:
            query += " AND stage = ?"
            params.append(stage)
        query += " ORDER BY company, name"
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@app.post("/contacts", status_code=201)
def create_contact(body: ContactCreate):
    now = datetime.utcnow().isoformat()
    cid = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            """INSERT INTO contacts
               (id, name, title, company, email, phone, linkedin,
                industry, stage, notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (cid, body.name, body.title, body.company, body.email,
             body.phone, body.linkedin, "PET Plastic Manufacturing",
             "Identified", body.notes, now, now),
        )
    return {"id": cid, "message": "Contact created"}


@app.get("/contacts/{contact_id}")
def get_contact(contact_id: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM contacts WHERE id=?", (contact_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    return dict(row)


@app.put("/contacts/{contact_id}/stage")
def update_contact_stage(contact_id: str, body: ContactStageUpdate):
    if body.stage not in FUNNEL_STAGES:
        raise HTTPException(status_code=400, detail=f"Invalid stage. Choose from: {FUNNEL_STAGES}")
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        result = conn.execute(
            "UPDATE contacts SET stage=?, updated_at=? WHERE id=?",
            (body.stage, now, contact_id),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Stage updated", "stage": body.stage}


@app.delete("/contacts/{contact_id}")
def delete_contact(contact_id: str):
    with get_db() as conn:
        result = conn.execute("DELETE FROM contacts WHERE id=?", (contact_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Contact not found")
    return {"message": "Contact deleted"}


# ──────────────────────────────────────────────────────────────────────────────
# Routes – Emails
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/emails/generate", status_code=201)
def generate_email(body: EmailGenerateRequest):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM contacts WHERE id=?", (body.contact_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact = dict(row)
    email_data = _generate_email(contact, body.context or "")
    now = datetime.utcnow().isoformat()
    eid = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO emails (id, contact_id, subject, body, status, created_at) VALUES (?,?,?,?,?,?)",
            (eid, body.contact_id, email_data["subject"], email_data["body"], "Draft", now),
        )
    return {"id": eid, **email_data, "status": "Draft"}


@app.get("/emails")
def list_emails(contact_id: Optional[str] = None):
    with get_db() as conn:
        if contact_id:
            rows = conn.execute(
                "SELECT e.*, c.name as contact_name, c.company FROM emails e "
                "JOIN contacts c ON e.contact_id = c.id WHERE e.contact_id=? ORDER BY e.created_at DESC",
                (contact_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT e.*, c.name as contact_name, c.company FROM emails e "
                "JOIN contacts c ON e.contact_id = c.id ORDER BY e.created_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]


@app.post("/emails/{email_id}/send")
def send_email(email_id: str):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        result = conn.execute(
            "UPDATE emails SET status='Sent', sent_at=? WHERE id=?",
            (now, email_id),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Email not found")
        row = conn.execute(
            "SELECT e.*, c.name as contact_name FROM emails e JOIN contacts c ON e.contact_id=c.id WHERE e.id=?",
            (email_id,),
        ).fetchone()
        # Auto-advance contact stage to Contacted
        conn.execute(
            "UPDATE contacts SET stage='Contacted', updated_at=? WHERE id=? AND stage='Identified'",
            (now, row["contact_id"]),
        )
    return {"message": "Email marked as sent", "sent_at": now}


# ──────────────────────────────────────────────────────────────────────────────
# Routes – Meetings
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/meetings", status_code=201)
def schedule_meeting(body: MeetingCreate):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM contacts WHERE id=?", (body.contact_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact = dict(row)
    agenda = _generate_meeting_agenda(contact, body.context or "")
    now = datetime.utcnow().isoformat()
    mid = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            """INSERT INTO meetings
               (id, contact_id, title, scheduled_at, duration_mins, location, agenda, status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (mid, body.contact_id, body.title, body.scheduled_at,
             body.duration_mins, body.location, agenda, "Scheduled", now),
        )
        # Advance stage
        conn.execute(
            "UPDATE contacts SET stage='Meeting Scheduled', updated_at=? WHERE id=? AND stage IN ('Identified','Contacted')",
            (now, body.contact_id),
        )
    return {"id": mid, "agenda": agenda, "status": "Scheduled"}


@app.get("/meetings")
def list_meetings(contact_id: Optional[str] = None):
    with get_db() as conn:
        if contact_id:
            rows = conn.execute(
                "SELECT m.*, c.name as contact_name, c.company FROM meetings m "
                "JOIN contacts c ON m.contact_id=c.id WHERE m.contact_id=? ORDER BY m.scheduled_at",
                (contact_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT m.*, c.name as contact_name, c.company FROM meetings m "
                "JOIN contacts c ON m.contact_id=c.id ORDER BY m.scheduled_at"
            ).fetchall()
    return [dict(r) for r in rows]


@app.put("/meetings/{meeting_id}")
def update_meeting(meeting_id: str, body: MeetingNotesUpdate):
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        if body.status:
            result = conn.execute(
                "UPDATE meetings SET notes=?, status=? WHERE id=?",
                (body.notes, body.status, meeting_id),
            )
        else:
            result = conn.execute(
                "UPDATE meetings SET notes=? WHERE id=?",
                (body.notes, meeting_id),
            )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Meeting not found")
    return {"message": "Meeting updated"}


# ──────────────────────────────────────────────────────────────────────────────
# Routes – Orders
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/orders", status_code=201)
def create_order(body: OrderCreate):
    with get_db() as conn:
        row = conn.execute("SELECT id FROM contacts WHERE id=?", (body.contact_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    now = datetime.utcnow().isoformat()
    oid = str(uuid.uuid4())
    total = body.quantity_tons * body.unit_price_usd
    with get_db() as conn:
        conn.execute(
            """INSERT INTO orders
               (id, contact_id, product, quantity_tons, unit_price_usd, status, notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (oid, body.contact_id, body.product, body.quantity_tons,
             body.unit_price_usd, "Pending", body.notes, now, now),
        )
        # Advance stage to Closed Won
        conn.execute(
            "UPDATE contacts SET stage='Closed Won', updated_at=? WHERE id=?",
            (now, body.contact_id),
        )
    return {"id": oid, "total_usd": total, "status": "Pending"}


@app.get("/orders")
def list_orders(contact_id: Optional[str] = None):
    with get_db() as conn:
        if contact_id:
            rows = conn.execute(
                "SELECT o.*, c.name as contact_name, c.company FROM orders o "
                "JOIN contacts c ON o.contact_id=c.id WHERE o.contact_id=? ORDER BY o.created_at DESC",
                (contact_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT o.*, c.name as contact_name, c.company FROM orders o "
                "JOIN contacts c ON o.contact_id=c.id ORDER BY o.created_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]


@app.put("/orders/{order_id}/status")
def update_order_status(order_id: str, body: OrderStatusUpdate):
    if body.status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {ORDER_STATUSES}")
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        result = conn.execute(
            "UPDATE orders SET status=?, updated_at=? WHERE id=?",
            (body.status, now, order_id),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Order not found")
    return {"message": "Order status updated", "status": body.status}


# ──────────────────────────────────────────────────────────────────────────────
# Routes – Feedback
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/feedback", status_code=201)
def submit_feedback(body: FeedbackCreate):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM contacts WHERE id=?", (body.contact_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Contact not found")
    contact = dict(row)
    # Simple sentiment heuristic
    msg_lower = body.message.lower()
    if any(w in msg_lower for w in ["great", "excellent", "happy", "love", "perfect", "good"]):
        sentiment = "Positive"
    elif any(w in msg_lower for w in ["bad", "issue", "problem", "unhappy", "disappointed", "late", "wrong"]):
        sentiment = "Negative"
    else:
        sentiment = "Neutral"
    ai_response = _generate_feedback_response(contact, body.message)
    now = datetime.utcnow().isoformat()
    fid = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            "INSERT INTO feedback (id, contact_id, message, sentiment, response, created_at) VALUES (?,?,?,?,?,?)",
            (fid, body.contact_id, body.message, sentiment, ai_response, now),
        )
    return {"id": fid, "sentiment": sentiment, "response": ai_response}


@app.get("/feedback")
def list_feedback(contact_id: Optional[str] = None):
    with get_db() as conn:
        if contact_id:
            rows = conn.execute(
                "SELECT f.*, c.name as contact_name, c.company FROM feedback f "
                "JOIN contacts c ON f.contact_id=c.id WHERE f.contact_id=? ORDER BY f.created_at DESC",
                (contact_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT f.*, c.name as contact_name, c.company FROM feedback f "
                "JOIN contacts c ON f.contact_id=c.id ORDER BY f.created_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────────────────────
# Routes – Funnel & Dashboard
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/funnel")
def get_funnel():
    with get_db() as conn:
        rows = conn.execute(
            "SELECT stage, COUNT(*) as count FROM contacts GROUP BY stage"
        ).fetchall()
        totals = conn.execute(
            "SELECT COUNT(*) as contacts, "
            "(SELECT COUNT(*) FROM emails WHERE status='Sent') as emails_sent, "
            "(SELECT COUNT(*) FROM meetings) as meetings, "
            "(SELECT COUNT(*) FROM orders) as orders, "
            "(SELECT COALESCE(SUM(quantity_tons * unit_price_usd), 0) FROM orders WHERE status != 'Cancelled') as pipeline_usd "
            "FROM contacts"
        ).fetchone()
    stage_counts = {r["stage"]: r["count"] for r in rows}
    funnel = [{"stage": s, "count": stage_counts.get(s, 0)} for s in FUNNEL_STAGES]
    return {
        "funnel": funnel,
        "stats": dict(totals),
        "stages": FUNNEL_STAGES,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Routes – Agent (AI orchestration endpoint)
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/agent/run")
def run_agent(body: AgentRunRequest):
    """
    High-level agent endpoint. Accepts a natural language task and contact_id.
    Determines the right action and executes it.
    """
    task_lower = body.task.lower()
    contact = None
    if body.contact_id:
        with get_db() as conn:
            row = conn.execute("SELECT * FROM contacts WHERE id=?", (body.contact_id,)).fetchone()
        if row:
            contact = dict(row)

    # Route to appropriate sub-agent based on task keywords
    if any(k in task_lower for k in ["email", "outreach", "write", "draft", "message"]):
        if not contact:
            return {"error": "contact_id required for email tasks"}
        email_data = _generate_email(contact, body.context or body.task)
        now = datetime.utcnow().isoformat()
        eid = str(uuid.uuid4())
        with get_db() as conn:
            conn.execute(
                "INSERT INTO emails (id, contact_id, subject, body, status, created_at) VALUES (?,?,?,?,?,?)",
                (eid, body.contact_id, email_data["subject"], email_data["body"], "Draft", now),
            )
        return {"action": "email_generated", "email_id": eid, **email_data}

    elif any(k in task_lower for k in ["meeting", "schedule", "call", "appointment"]):
        if not contact:
            return {"error": "contact_id required for meeting tasks"}
        agenda = _generate_meeting_agenda(contact, body.context or body.task)
        return {"action": "meeting_agenda_generated", "agenda": agenda,
                "suggestion": f"Schedule a 30-min discovery call with {contact['name']} at {contact['company']}"}

    elif any(k in task_lower for k in ["feedback", "respond", "reply", "complaint"]):
        if not contact:
            return {"error": "contact_id required for feedback tasks"}
        response = _generate_feedback_response(contact, body.context or body.task)
        return {"action": "feedback_response_generated", "response": response}

    elif any(k in task_lower for k in ["funnel", "pipeline", "status", "overview", "dashboard"]):
        return get_funnel()

    else:
        # General AI assistant
        system = (
            "You are an intelligent B2B sales agent specialising in PET plastic "
            "manufacturing. Help the user with their sales task concisely."
        )
        user_msg = body.task
        if contact:
            user_msg += f"\nContact: {contact['name']}, {contact['title']} at {contact['company']}"
        if body.context:
            user_msg += f"\nContext: {body.context}"
        result = _ai_complete(system, user_msg)
        if not result:
            result = (
                "I can help you with: generating outreach emails, scheduling meetings, "
                "processing orders, and responding to customer feedback. "
                "Please specify a contact and task."
            )
        return {"action": "agent_response", "response": result}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}
