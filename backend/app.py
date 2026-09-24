"""
PET Plastic Manufacturing Closing Agent
FastAPI backend – deployable on Render
"""

from __future__ import annotations

import asyncio
import os
import json
import uuid
import sqlite3
import logging
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timedelta, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

from xometry import (
    approve_xometry_job,
    get_job,
    get_job_for_order,
    list_jobs as list_mfg_jobs,
    mock_advance_job,
    on_po_acquired,
    update_job_status as update_mfg_job_status,
    xometry_config_summary,
)
from xometry.service import ensure_schema as ensure_mfg_schema

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
ALLOWED_ORIGINS_RAW = os.getenv(
    "ALLOWED_ORIGINS",
    "https://codesurfing10.github.io,http://localhost:3000,http://localhost:5500",
)
ALLOWED_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_RAW.split(",") if o.strip()]
DB_PATH = os.getenv("DB_PATH", "closing_agent.db")
# How often the daily lead-generation task runs (seconds); override via env for testing
LEAD_GEN_INTERVAL_SECS = int(os.getenv("LEAD_GEN_INTERVAL_SECS", str(24 * 60 * 60)))

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
                approval_status TEXT NOT NULL DEFAULT 'approved',
                sent_at TEXT,
                created_at TEXT NOT NULL,
                meeting_id TEXT,
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
                approval_status TEXT NOT NULL DEFAULT 'approved',
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
                approval_status TEXT NOT NULL DEFAULT 'approved',
                created_at TEXT NOT NULL,
                FOREIGN KEY (contact_id) REFERENCES contacts(id)
            );

            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                title TEXT,
                company TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                linkedin TEXT,
                industry TEXT DEFAULT 'PET Plastic Manufacturing',
                rationale TEXT,
                source TEXT DEFAULT 'AI Generated',
                status TEXT DEFAULT 'New',
                created_at TEXT NOT NULL
            );


            CREATE TABLE IF NOT EXISTS inventory (
                id TEXT PRIMARY KEY,
                sku TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                description TEXT,
                material TEXT,
                unit_price_usd REAL,
                units_per_pack INTEGER DEFAULT 2,
                stock_qty INTEGER DEFAULT 0,
                category TEXT,
                manufacturer TEXT,
                distributor TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS opportunities (
                id TEXT PRIMARY KEY,
                company TEXT NOT NULL,
                contact_name TEXT,
                industry TEXT,
                recommended_sku TEXT,
                estimated_quantity INTEGER,
                unit_price_usd REAL,
                estimated_deal_value_usd REAL,
                stage TEXT DEFAULT 'Prospecting',
                next_step TEXT,
                value_proposition TEXT,
                nda_required INTEGER DEFAULT 1,
                nda_status TEXT DEFAULT 'Pending',
                lead_id TEXT,
                contact_id TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ndas (
                id TEXT PRIMARY KEY,
                contact_id TEXT,
                lead_id TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                signed_at TEXT,
                document_ref TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS distributor_listings (
                id TEXT PRIMARY KEY,
                channel TEXT NOT NULL UNIQUE,
                path_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'not_started',
                portal_url TEXT,
                priority TEXT NOT NULL DEFAULT 'P3',
                skus TEXT,
                notes TEXT,
                next_action TEXT,
                next_action_date TEXT,
                applied_at TEXT,
                listed_at TEXT,
                contact_email TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

        """)
    _migrate_db()
    with get_db() as conn:
        ensure_mfg_schema(conn)
    _seed_contacts()
    _seed_inventory()
    _seed_distributor_listings()


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


def _migrate_db():
    """Add columns to existing databases that predate newer features."""
    migration_sqls = [
        "ALTER TABLE emails   ADD COLUMN approval_status TEXT NOT NULL DEFAULT 'approved'",
        "ALTER TABLE meetings ADD COLUMN approval_status TEXT NOT NULL DEFAULT 'approved'",
        "ALTER TABLE feedback ADD COLUMN approval_status TEXT NOT NULL DEFAULT 'approved'",
        "ALTER TABLE contacts ADD COLUMN nda_signed INTEGER NOT NULL DEFAULT 0",
        "ALTER TABLE orders ADD COLUMN po_number TEXT",
        "ALTER TABLE emails ADD COLUMN meeting_id TEXT",
    ]
    with get_db() as conn:
        for sql in migration_sqls:
            try:
                conn.execute(sql)
            except Exception:
                pass  # column already exists


_SEED_INVENTORY = [
    {
        "sku": "LCP061000",
        "name": "LC-Flow Valve — Plastic PC-ISO",
        "description": "LC-Flow Valve and Distribution Adaptor in PC-ISO plastic. Units per listing: 2.",
        "material": "PC-ISO",
        "unit_price_usd": 145.38,
        "units_per_pack": 2,
        "stock_qty": 50,
        "category": "Flow Control / Distribution",
        "manufacturer": "PTC Inc",
        "distributor": "Industrial and Molecular Solutions",
        "notes": "PET air conveyors, beverage packaging, non-corrosive pneumatic fluid control.",
    },
    {
        "sku": "LCSS61000",
        "name": "LC-Flow Valve — Stainless Steel 316L",
        "description": "LC-Flow Valve and Distribution Adaptor in 316L stainless steel. Units per listing: 2.",
        "material": "316L Stainless Steel",
        "unit_price_usd": 558.28,
        "units_per_pack": 2,
        "stock_qty": 30,
        "category": "Flow Control / Distribution",
        "manufacturer": "PTC Inc",
        "distributor": "Industrial and Molecular Solutions",
        "notes": "Corrosion-resistant; aerospace pneumatics, automotive lubrication, washdown.",
    },
    {
        "sku": "LCA061000",
        "name": "LC-Flow Valve — Aluminum AlSiMg",
        "description": "LC-Flow Valve and Distribution Adaptor in Aluminum AlSiMg. Units per listing: 2.",
        "material": "Aluminum AlSiMg",
        "unit_price_usd": 1545.28,
        "units_per_pack": 2,
        "stock_qty": 15,
        "category": "Flow Control / Distribution",
        "manufacturer": "PTC Inc",
        "distributor": "Industrial and Molecular Solutions",
        "notes": "Lightweight; aerospace MRO, propulsion test, weight-critical automotive/airline.",
    },
]


def _seed_inventory():
    """Idempotent seed of LC-Flow SKUs by sku."""
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        for item in _SEED_INVENTORY:
            existing = conn.execute(
                "SELECT id FROM inventory WHERE sku=?", (item["sku"],)
            ).fetchone()
            if existing:
                continue
            conn.execute(
                """INSERT INTO inventory
                   (id, sku, name, description, material, unit_price_usd,
                    units_per_pack, stock_qty, category, manufacturer,
                    distributor, notes, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()),
                    item["sku"], item["name"], item["description"], item["material"],
                    item["unit_price_usd"], item["units_per_pack"], item["stock_qty"],
                    item["category"], item["manufacturer"], item["distributor"],
                    item["notes"], now,
                ),
            )



_LC_FLOW_SKUS = "LCP061000,LCSS61000,LCA061000"

_SEED_DISTRIBUTOR_LISTINGS = [
    {
        "channel": "Thomasnet",
        "path_type": "open_apply",
        "status": "not_started",
        "portal_url": "https://business.thomasnet.com/get-listed-on-thomasnet?nav_src=utilitynav",
        "priority": "P1",
        "skus": _LC_FLOW_SKUS,
        "notes": "Claim/list company (free) + categories; discovery leads into Closing-Agent.",
        "next_action": "Claim Thomasnet profile; set pneumatics / valve categories; upload public one-pager.",
        "next_action_date": None,
        "contact_email": None,
    },
    {
        "channel": "GlobalSpec",
        "path_type": "open_apply",
        "status": "not_started",
        "portal_url": "https://advertising.globalspec.com/list-your-products/",
        "priority": "P1",
        "skus": _LC_FLOW_SKUS,
        "notes": "Paid Product Discovery; engineer RFQs. Contact sales for pricing.",
        "next_action": "Inquire Product Discovery pricing; prepare public-safe product specs.",
        "next_action_date": None,
        "contact_email": "sales@globalspec.com",
    },
    {
        "channel": "MSC",
        "path_type": "open_apply",
        "status": "not_started",
        "portal_url": "https://www.mscdirect.com/customer-service/new-supplier-inquiry",
        "priority": "P2",
        "skus": _LC_FLOW_SKUS,
        "notes": "New Supplier Inquiry draft in deliverables/MSC_SUPPLIER_APPLICATION_DRAFT.md. DRAFT only.",
        "next_action": "James reviews MSC draft; gather W-9/COI/photos/GTIN; submit inquiry when ready.",
        "next_action_date": None,
        "contact_email": None,
    },
    {
        "channel": "Zoro",
        "path_type": "open_apply",
        "status": "not_started",
        "portal_url": "https://www.zoro.com/sell/",
        "priority": "P2",
        "skus": _LC_FLOW_SKUS,
        "notes": "Sell on Zoro partnership draft in deliverables/ZORO_SELL_ON_ZORO_APPLICATION_DRAFT.md. Prefer dropship if 1–2 day ship.",
        "next_action": "James reviews Zoro draft; confirm dropship SLA + seller of record; apply when ready.",
        "next_action_date": None,
        "contact_email": "businessdevelopment@zoro.com",
    },
    {
        "channel": "Amazon Business",
        "path_type": "marketplace",
        "status": "not_started",
        "portal_url": "https://sell.amazon.com/programs/amazon-business",
        "priority": "P2",
        "skus": _LC_FLOW_SKUS,
        "notes": "Fastest electronic listing path; needs GTIN or Brand Registry path. Public vs NDA policy open.",
        "next_action": "Decide public-vs-NDA policy; obtain GTINs; open Professional seller + B2B tools.",
        "next_action_date": None,
        "contact_email": None,
    },
    {
        "channel": "Fastenal",
        "path_type": "portal_review",
        "status": "not_started",
        "portal_url": "https://www.fastenal.com",
        "priority": "P3",
        "skus": _LC_FLOW_SKUS,
        "notes": "Register as Fastenal Supplier; local branch code helps. Guide: crafter.fastenal.com PDF.",
        "next_action": "Register supplier account; identify local branch champion; email suppliercompliance if needed.",
        "next_action_date": None,
        "contact_email": "suppliercompliance@fastenal.com",
    },
    {
        "channel": "Motion",
        "path_type": "portal_review",
        "status": "not_started",
        "portal_url": "https://www.motionpartnerportal.com/Supplier-Process/",
        "priority": "P3",
        "skus": _LC_FLOW_SKUS,
        "notes": "Request New Supplier Registration Form via Partner Portal; optional branch program.",
        "next_action": "Request New Supplier form; prepare capability one-pager + UNSPSC.",
        "next_action_date": None,
        "contact_email": "partnerportal@motion.com",
    },
    {
        "channel": "Applied",
        "path_type": "portal_review",
        "status": "not_started",
        "portal_url": "https://www.applied.com/supplier-diversity",
        "priority": "P3",
        "skus": _LC_FLOW_SKUS,
        "notes": "Supplier diversity / become-a-supplier path; local service centers for intros.",
        "next_action": "Register/apply via Applied supplier diversity page; review Supplier Code of Conduct.",
        "next_action_date": None,
        "contact_email": None,
    },
    {
        "channel": "Grainger",
        "path_type": "portal_review",
        "status": "not_started",
        "portal_url": "https://solutions.sciquest.com/apps/Router/SupplierLogin?CustOrg=WWGrainger",
        "priority": "P4",
        "skus": _LC_FLOW_SKUS,
        "notes": "JAGGAER Supplier Network + vendor contact request; slow category gate. No self-serve SKU upload.",
        "next_action": "Create JAGGAER profile; submit supplier/vendor contact request; prepare UNSPSC/NAICS one-pager.",
        "next_action_date": None,
        "contact_email": "Supplier_Maintenance@Grainger.com",
    },
    {
        "channel": "McMaster",
        "path_type": "closed_bd",
        "status": "not_started",
        "portal_url": "https://www.mcmaster.com/contact",
        "priority": "P5",
        "skus": _LC_FLOW_SKUS,
        "notes": "No public supplier apply URL. Relationship/BD or end-customer pull only. Do not fabricate an apply link.",
        "next_action": "Hold cold apply; pursue warm intro or customer pull-through to Supplier Operations.",
        "next_action_date": None,
        "contact_email": "sales@mcmaster.com",
    },
]


def _seed_distributor_listings():
    """Idempotent seed of priority distributor channels by channel name."""
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        for item in _SEED_DISTRIBUTOR_LISTINGS:
            existing = conn.execute(
                "SELECT id FROM distributor_listings WHERE channel=?",
                (item["channel"],),
            ).fetchone()
            if existing:
                continue
            conn.execute(
                """INSERT INTO distributor_listings
                   (id, channel, path_type, status, portal_url, priority, skus,
                    notes, next_action, next_action_date, applied_at, listed_at,
                    contact_email, created_at, updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    str(uuid.uuid4()),
                    item["channel"],
                    item["path_type"],
                    item["status"],
                    item["portal_url"],
                    item["priority"],
                    item["skus"],
                    item["notes"],
                    item["next_action"],
                    item.get("next_action_date"),
                    None,
                    None,
                    item.get("contact_email"),
                    now,
                    now,
                ),
            )


def _contact_nda_signed(contact_id: Optional[str] = None, lead_id: Optional[str] = None) -> bool:
    """Return True if an NDA is signed for this contact or lead."""
    with get_db() as conn:
        if contact_id:
            row = conn.execute(
                "SELECT 1 FROM ndas WHERE contact_id=? AND status='signed' LIMIT 1",
                (contact_id,),
            ).fetchone()
            if row:
                return True
            crow = conn.execute(
                "SELECT nda_signed FROM contacts WHERE id=?", (contact_id,)
            ).fetchone()
            if crow and crow["nda_signed"]:
                return True
        if lead_id:
            row = conn.execute(
                "SELECT 1 FROM ndas WHERE lead_id=? AND status='signed' LIMIT 1",
                (lead_id,),
            ).fetchone()
            if row:
                return True
    return False


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
    """Call OpenAI ChatCompletion, fall back to Gemini, then to template string on failure."""
    # Try OpenAI first
    if OPENAI_API_KEY:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=OPENAI_API_KEY)
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                max_tokens=1200,
                temperature=0.7,
            )
            return resp.choices[0].message.content.strip()
        except Exception as exc:
            logger.warning("OpenAI call failed: %s", exc)

    # Fall back to Gemini
    if GEMINI_API_KEY:
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                system_instruction=system,
            )
            resp = model.generate_content(
                user,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=1200,
                    temperature=0.7,
                ),
            )
            return resp.text.strip()
        except Exception as exc:
            logger.warning("Gemini call failed: %s", exc)

    return ""


def _generate_email(contact: dict, context: str = "") -> dict:
    """Generate outreach; if NDA not signed, request NDA before specs/pricing."""
    contact_id = contact.get("id")
    nda_ok = _contact_nda_signed(contact_id=contact_id) if contact_id else bool(contact.get("nda_signed"))
    industry = contact.get("industry") or "industrial manufacturing"
    first = contact["name"].split()[0]

    if not nda_ok:
        system = (
            "You are a B2B sales copywriter for Industrial and Molecular Solutions / PTC Inc "
            "selling the LC-Flow Valve and Distribution Adaptor. NDA is NOT yet signed. "
            "Write a short email (<=150 words) that introduces the product category at a high "
            "level ONLY and requests that the prospect execute a Mutual NDA before any "
            "technical specs, drawings, or pricing. Do NOT include unit prices, CAD, or "
            "detailed process/material specs. Return ONLY JSON with keys 'subject' and 'body'."
        )
        user = (
            f"Write an NDA-first outreach to {contact['name']}, {contact.get('title','')} at "
            f"{contact['company']} ({industry}). {context}\n"
            "Return ONLY JSON with keys 'subject' and 'body'."
        )
        raw = _ai_complete(system, user)
        try:
            data = json.loads(raw)
            if "subject" in data and "body" in data:
                data["nda_gate"] = "pending"
                return data
        except Exception:
            pass
        subject = f"Mutual NDA to explore LC-Flow with {contact['company']}"
        body = (
            f"Hi {first},\n\n"
            f"I'm reaching out from Industrial and Molecular Solutions (PTC Inc manufacturing) "
            f"regarding our LC-Flow Valve and Distribution Adaptor — apparatus for controlled "
            f"delivery of vapors, gases, liquids, and sprays used in {industry}.\n\n"
            f"Before we share technical specifications, drawings, or pricing, we ask all "
            f"prospects to execute a short Mutual NDA (template available on request). "
            f"Once signed, we can discuss SKU options (plastic PC-ISO, 316L SS, AlSiMg) "
            f"and fit for {contact['company']}.\n\n"
            f"May I send the NDA for your review this week?\n\n"
            f"Best regards,\nJames Gallagher\nIndustrial and Molecular Solutions\n"
            f"610-393-1102 | Jgallagher10@gmail.com"
        )
        return {"subject": subject, "body": body, "nda_gate": "pending"}

    system = (
        "You are an expert B2B sales copywriter for LC-Flow Valve and Distribution Adaptor "
        "(PTC Inc / Industrial and Molecular Solutions). NDA IS signed — you may discuss "
        "technical fit, materials, and list pricing. Write concise persuasive emails (<=180 words). "
        "Return ONLY JSON with keys 'subject' and 'body'."
    )
    user = (
        f"Write outreach to {contact['name']}, {contact.get('title','')} at {contact['company']} "
        f"({industry}). NDA is signed. {context}\nReturn ONLY JSON with keys 'subject' and 'body'."
    )
    raw = _ai_complete(system, user)
    try:
        data = json.loads(raw)
        if "subject" in data and "body" in data:
            data["nda_gate"] = "signed"
            return data
    except Exception:
        pass
    subject = f"LC-Flow Valve options for {contact['company']} — next steps"
    body = (
        f"Hi {first},\n\n"
        f"Thanks for executing the NDA. LC-Flow controls flow, distribution, and pressure for "
        f"vapors, gases, liquids, and sprays — relevant to {industry} at {contact['company']}.\n\n"
        f"SKUs (pack of 2): LCP061000 PC-ISO $145.38 | LCSS61000 316L SS $558.28 | "
        f"LCA061000 AlSiMg $1,545.28. Happy to recommend based on environment and duty cycle.\n\n"
        f"Would 20 minutes this week work for a technical fit discussion?\n\n"
        f"Best regards,\nJames Gallagher\nIndustrial and Molecular Solutions"
    )
    return {"subject": subject, "body": body, "nda_gate": "signed"}


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
    contact_id = contact.get("id")
    nda_ok = _contact_nda_signed(contact_id=contact_id) if contact_id else bool(contact.get("nda_signed"))
    industry = contact.get("industry") or "industrial manufacturing"
    nda_note = (
        "NDA is NOT signed — agenda item #1 MUST be Mutual NDA confirmation; "
        "do not plan to share detailed specs, drawings, or pricing until signed."
        if not nda_ok else
        "NDA is signed — technical discussion and pricing OK."
    )
    system = (
        "You are a senior B2B sales professional for LC-Flow Valve (PTC Inc / "
        "Industrial and Molecular Solutions). Create a concise meeting agenda (3-5 bullets). "
        + nda_note
    )
    user = (
        f"Meeting with {contact['name']}, {contact.get('title','')} at {contact['company']} "
        f"({industry}). {context} Generate a short agenda."
    )
    result = _ai_complete(system, user)
    if result:
        if not nda_ok and "NDA" not in result and "nda" not in result.lower():
            result = "• Confirm Mutual NDA status / execute NDA before technical deep-dive\n" + result
        return result
    if not nda_ok:
        return (
            "• Confirm Mutual NDA status — execute NDA before sharing specs, drawings, or pricing\n"
            "• High-level LC-Flow category overview (no detailed specs)\n"
            f"• Understand {contact['company']} flow/distribution pain points in {industry}\n"
            "• Agree NDA timeline and schedule technical follow-up after signing\n"
            "• Next steps / owners"
        )
    return (
        "• Confirm NDA on file and introductions\n"
        f"• Current flow / pneumatic / lubrication needs at {contact['company']}\n"
        "• SKU fit: PC-ISO vs 316L SS vs AlSiMg\n"
        "• Sample / pilot quantity and timeline\n"
        "• Agree on quote and next steps"
    )



# Organizer defaults for calendar invites / meeting emails
_ORGANIZER_NAME = "James Gallagher"
_ORGANIZER_EMAIL = "Jgallagher10@gmail.com"
_ORGANIZER_PHONE = "610-393-1102"
_ORGANIZER_COMPANY = "Industrial and Molecular Solutions / PTC Inc"
_ICS_TZ = ZoneInfo("America/Tijuana")


def _parse_iso_dt(value: str) -> datetime:
    """Parse ISO datetime; treat naive values as UTC."""
    raw = (value or "").strip()
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    dt = datetime.fromisoformat(raw)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _ics_escape(text: str) -> str:
    return (
        (text or "")
        .replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
        .replace("\r", "\\n")
    )


def _ics_fold(line: str) -> str:
    """Fold ICS content lines to <=75 octets (RFC 5545)."""
    if len(line.encode("utf-8")) <= 75:
        return line
    out = []
    buf = ""
    for ch in line:
        candidate = buf + ch
        if len(candidate.encode("utf-8")) > 75:
            out.append(buf)
            buf = " " + ch
        else:
            buf = candidate
    if buf:
        out.append(buf)
    return "\r\n".join(out)


def _fmt_ics_utc(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _fmt_pt_display(dt: datetime) -> str:
    local = dt.astimezone(_ICS_TZ)
    # Drop leading zero on hour for readability (e.g. 09 -> 9) while keeping AM/PM
    return local.strftime("%A, %B %d, %Y at %I:%M %p PT").replace(" at 0", " at ")


def _safe_ics_filename(title: str) -> str:
    base = "".join(ch if ch.isalnum() or ch in ("-", "_", " ") else "_" for ch in (title or "meeting"))
    base = "_".join(base.split())[:60] or "meeting"
    return f"{base}.ics"


def _build_ics(meeting: dict, contact: dict) -> str:
    """Build RFC 5545 VCALENDAR/VEVENT (METHOD:REQUEST) for a meeting. Times in UTC (Z)."""
    start = _parse_iso_dt(meeting["scheduled_at"])
    duration = int(meeting.get("duration_mins") or 30)
    end = start + timedelta(minutes=duration)
    now = datetime.now(timezone.utc)
    mid = meeting["id"]
    summary = meeting.get("title") or "Meeting"
    location = meeting.get("location") or ""
    agenda = (meeting.get("agenda") or "").strip()

    desc_parts = []
    if agenda:
        desc_parts.append("Agenda:\n" + agenda)
    desc_parts.append(
        f"Organizer: {_ORGANIZER_NAME}\n"
        f"{_ORGANIZER_COMPANY}\n"
        f"{_ORGANIZER_PHONE} | {_ORGANIZER_EMAIL}"
    )
    description = _ics_escape("\n\n".join(desc_parts))

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Closing Agent Manufacturing//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:REQUEST",
        "BEGIN:VEVENT",
        f"UID:{mid}@closing-agent",
        f"DTSTAMP:{_fmt_ics_utc(now)}",
        f"DTSTART:{_fmt_ics_utc(start)}",
        f"DTEND:{_fmt_ics_utc(end)}",
        f"SUMMARY:{_ics_escape(summary)}",
        f"LOCATION:{_ics_escape(location)}",
        f"DESCRIPTION:{description}",
        f"ORGANIZER;CN={_ics_escape(_ORGANIZER_NAME)}:mailto:{_ORGANIZER_EMAIL}",
    ]
    attendee_email = (contact or {}).get("email") or ""
    if attendee_email:
        cn = _ics_escape((contact or {}).get("name") or attendee_email)
        lines.append(f"ATTENDEE;CN={cn};RSVP=TRUE:mailto:{attendee_email}")
    lines.extend([
        "STATUS:CONFIRMED",
        "SEQUENCE:0",
        "END:VEVENT",
        "END:VCALENDAR",
    ])
    return "\r\n".join(_ics_fold(line) for line in lines) + "\r\n"


def _generate_meeting_invite_email(meeting: dict, contact: dict, agenda: str) -> dict:
    """NDA-aware invite email draft (template + optional AI). Never auto-sends."""
    contact_id = contact.get("id")
    nda_ok = _contact_nda_signed(contact_id=contact_id) if contact_id else bool(contact.get("nda_signed"))
    first = (contact.get("name") or "there").split()[0]
    start = _parse_iso_dt(meeting["scheduled_at"])
    when_pt = _fmt_pt_display(start)
    duration = int(meeting.get("duration_mins") or 30)
    location = meeting.get("location") or "TBD"
    title = meeting.get("title") or "Meeting"
    agenda_text = (agenda or meeting.get("agenda") or "").strip()
    company = contact.get("company") or "your company"

    if not nda_ok:
        subject = f"Meeting invite: {title} (discovery / NDA) — {company}"
        body = (
            f"Hi {first},\n\n"
            f"I'd like to confirm our upcoming call:\n\n"
            f"• When: {when_pt}\n"
            f"• Duration: {duration} minutes\n"
            f"• Location: {location}\n\n"
            f"Proposed agenda:\n{agenda_text or '• Discovery discussion and Mutual NDA next steps'}\n\n"
            f"IMPORTANT: An NDA is not yet on file for {company}. "
            f"This discussion is limited to high-level discovery and Mutual NDA execution — "
            f"we will not share technical specifications, drawings, or pricing until an NDA is signed.\n\n"
            f"A calendar invite (.ics) is available from Closing Agent (Download .ics on the meeting) "
            f"and can be opened in Outlook, Google Calendar, or Apple Calendar.\n\n"
            f"Looking forward to connecting.\n\n"
            f"Best regards,\n{_ORGANIZER_NAME}\n{_ORGANIZER_COMPANY}\n"
            f"{_ORGANIZER_PHONE} | {_ORGANIZER_EMAIL}"
        )
        return {"subject": subject, "body": body, "nda_gate": "pending"}

    subject = f"Meeting invite: {title} — {company}"
    body = (
        f"Hi {first},\n\n"
        f"Confirming our upcoming meeting:\n\n"
        f"• When: {when_pt}\n"
        f"• Duration: {duration} minutes\n"
        f"• Location: {location}\n\n"
        f"Agenda:\n{agenda_text or '• Technical fit discussion and next steps'}\n\n"
        f"A calendar invite (.ics) is available from Closing Agent (Download .ics on the meeting) "
        f"and can be opened in Outlook, Google Calendar, or Apple Calendar.\n\n"
        f"Looking forward to it.\n\n"
        f"Best regards,\n{_ORGANIZER_NAME}\n{_ORGANIZER_COMPANY}\n"
        f"{_ORGANIZER_PHONE} | {_ORGANIZER_EMAIL}"
    )
    system = (
        "You are a B2B sales assistant for Industrial and Molecular Solutions / PTC Inc. "
        "NDA IS signed. Rewrite the meeting invite email to be concise and professional "
        "(<=180 words). Keep When/Duration/Location, agenda bullets, and the note that "
        "a .ics calendar invite is available from Closing Agent. "
        "Return ONLY JSON with keys 'subject' and 'body'."
    )
    user = (
        f"Contact: {contact.get('name')} at {company}.\n"
        f"Draft subject: {subject}\nDraft body:\n{body}\n"
        "Return ONLY JSON with keys 'subject' and 'body'."
    )
    raw = _ai_complete(system, user)
    try:
        data = json.loads(raw)
        if "subject" in data and "body" in data:
            data["nda_gate"] = "signed"
            return data
    except Exception:
        pass
    return {"subject": subject, "body": body, "nda_gate": "signed"}


# Industry-focused lead targets for LC-Flow Valve (flow / distribution adaptor)
_LEAD_GEN_TARGETS = {
    "Aerospace": [
        "Boeing", "Lockheed Martin", "Northrop Grumman", "SpaceX", "Spirit AeroSystems",
        "Collins Aerospace", "Honeywell Aerospace", "Raytheon", "General Dynamics",
        "Blue Origin",
    ],
    "Beverage / PET Packaging": [
        "Amcor", "Niagara Bottling", "Coca-Cola", "PepsiCo", "Refresco",
        "Keurig Dr Pepper", "Nestlé Waters", "Danone", "Berry Global", "Plastipak",
        "Alpla", "Silgan", "Graham Packaging",
    ],
    "PET Air Conveyors": [
        "Sidel", "Krones", "GEA Convair", "SMF", "Effiline", "AMBEC", "FlexLink",
        "Sacmi", "Tech-Long", "SIPA",
    ],
    "Automotive Engineering": [
        "Bosch", "Continental", "Magna International", "ZF Friedrichshafen",
        "Stellantis", "Ford Motor Company", "General Motors", "Toyota", "Aptiv",
        "Schaeffler",
    ],
}

_INDUSTRY_RATIONALE = {
    "Aerospace": (
        "{company} operates pneumatic/fluidic or propulsion-adjacent systems where "
        "LC-Flow Valve distribution adaptors improve flow, pressure, and vapor/gas delivery."
    ),
    "Beverage / PET Packaging": (
        "{company} runs PET packaging or bottling lines that need air/lube/spray distribution; "
        "LC-Flow fits line spares and plant standardization."
    ),
    "PET Air Conveyors": (
        "{company} builds or integrates empty-bottle air conveyors; LC-Flow is a natural "
        "OEM/spare distribution adaptor for air manifolds."
    ),
    "Automotive Engineering": (
        "{company} uses industrial lubrication, pneumatic fluid control, or powertrain test "
        "benches where LC-Flow provides precise multi-media distribution."
    ),
}


def _generate_leads_ai(count: int = 5, industry_focus: Optional[str] = None) -> list[dict]:
    """Generate LC-Flow sales leads across Aerospace, Beverage/PET, Air Conveyors, Automotive."""
    industries = list(_LEAD_GEN_TARGETS.keys())
    focus_note = industry_focus or ("balanced mix across " + ", ".join(industries))
    system = (
        "You are a B2B lead generation specialist for the LC-Flow Valve and Distribution "
        "Adaptor (PTC Inc / Industrial and Molecular Solutions) — apparatus for molecular "
        "transfer of vapors, gases, liquids, and sprays. Generate realistic decision-maker "
        "prospects in Aerospace, Beverage/PET packaging, PET empty-bottle air conveyor OEMs, "
        "and Automotive engineering/manufacturing. Return ONLY a JSON array with no extra text."
    )
    user = (
        f"Generate exactly {count} new sales leads for LC-Flow Valve. Industry focus: {focus_note}. "
        "Target engineering, procurement, plant, OEM product, and MRO leaders. "
        "Return a JSON array where each element has keys: "
        "name, title, company, email, phone, linkedin, industry, rationale. "
        "industry must be one of: Aerospace, Beverage / PET Packaging, PET Air Conveyors, "
        "Automotive Engineering. Rationale: 1-2 sentences on why LC-Flow fits. "
        "Use realistic but fictional contact details."
    )
    raw = _ai_complete(system, user)
    if raw:
        clean = raw.strip()
        if clean.startswith("```"):
            clean = clean.split("```", 2)[1]
            if clean.startswith("json"):
                clean = clean[4:]
            clean = clean.rsplit("```", 1)[0].strip()
        try:
            leads = json.loads(clean)
            if isinstance(leads, list) and leads:
                for lead in leads:
                    if "industry" not in lead or not lead["industry"]:
                        lead["industry"] = industry_focus or "Beverage / PET Packaging"
                return leads[:count]
        except Exception:
            pass

    import random
    titles_by_industry = {
        "Aerospace": [
            "Manager, Pneumatic Systems", "Director Propulsion Test", "Sr. Buyer – Fluid Systems MRO",
            "Lead Engineer, Ground Support", "Principal Engineer, ECS",
        ],
        "Beverage / PET Packaging": [
            "VP of Procurement", "Head of Supply Chain", "Director of Plant Engineering",
            "Packaging Equipment Buyer", "Global Packaging Director",
        ],
        "PET Air Conveyors": [
            "Product Manager – Air Conveyors", "Head of Engineering – Intralogistics",
            "Sales Engineering Manager", "Technical Director", "OEM Partnerships Lead",
        ],
        "Automotive Engineering": [
            "Manager, Powertrain Test Labs", "Director of Manufacturing Engineering",
            "Sr. Buyer – Fluid Power", "Plant Maintenance Manager", "Category Manager – Pneumatics",
        ],
    }
    first_names = ["Jordan", "Taylor", "Morgan", "Casey", "Riley", "Drew", "Avery", "Quinn", "Sam", "Alex"]
    last_names = ["Rivera", "Nguyen", "Okafor", "Petrov", "Svensson", "Kowalski", "Ahmed", "Patel", "Brooks"]

    if industry_focus and industry_focus in _LEAD_GEN_TARGETS:
        pool_industries = [industry_focus] * count
    else:
        pool_industries = [industries[i % len(industries)] for i in range(count)]

    leads = []
    for ind in pool_industries:
        company = random.choice(_LEAD_GEN_TARGETS[ind])
        fn = random.choice(first_names)
        ln = random.choice(last_names)
        title = random.choice(titles_by_industry[ind])
        slug = "".join(ch for ch in company.lower() if ch.isalnum())
        leads.append({
            "name": f"{fn} {ln}",
            "title": title,
            "company": company,
            "email": f"{fn.lower()}.{ln.lower()}@{slug}.com",
            "phone": f"+1-{random.randint(200,999)}-555-{random.randint(1000,9999)}",
            "linkedin": f"linkedin.com/in/{fn.lower()}-{ln.lower()}-{slug[:20]}",
            "industry": ind,
            "rationale": _INDUSTRY_RATIONALE[ind].format(company=company) + f" Contact: {title}.",
        })
    return leads


def _run_daily_lead_generation():
    """Generate and persist a batch of new leads to the DB."""
    leads = _generate_leads_ai(count=5)
    now = datetime.utcnow().isoformat()
    saved = 0
    with get_db() as conn:
        for lead in leads:
            lid = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO leads
                   (id, name, title, company, email, phone, linkedin,
                    industry, rationale, source, status, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    lid,
                    lead.get("name", "Unknown"),
                    lead.get("title", ""),
                    lead.get("company", "Unknown"),
                    lead.get("email", ""),
                    lead.get("phone", ""),
                    lead.get("linkedin", ""),
                    lead.get("industry", "Beverage / PET Packaging"),
                    lead.get("rationale", ""),
                    "AI Generated",
                    "New",
                    now,
                ),
            )
            saved += 1
    logger.info("Daily lead generation: saved %d leads", saved)
    return saved


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
    status: Optional[str] = "Pending"
    po_number: Optional[str] = None

class OrderStatusUpdate(BaseModel):
    status: str
    po_number: Optional[str] = None

class ManufacturingJobStatusUpdate(BaseModel):
    status: str
    tracking_number: Optional[str] = None
    notes: Optional[str] = None

class FeedbackCreate(BaseModel):
    contact_id: str
    message: str

class LeadGenerateRequest(BaseModel):
    count: Optional[int] = 5
    industry_focus: Optional[str] = None  # Aerospace | Beverage / PET Packaging | PET Air Conveyors | Automotive Engineering

class LeadStatusUpdate(BaseModel):
    status: str

class InventoryCreate(BaseModel):
    sku: str
    name: str
    description: Optional[str] = ""
    material: Optional[str] = ""
    unit_price_usd: Optional[float] = None
    units_per_pack: Optional[int] = 2
    stock_qty: Optional[int] = 0
    category: Optional[str] = "Flow Control / Distribution"
    manufacturer: Optional[str] = "PTC Inc"
    distributor: Optional[str] = "Industrial and Molecular Solutions"
    notes: Optional[str] = ""

class InventoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    material: Optional[str] = None
    unit_price_usd: Optional[float] = None
    units_per_pack: Optional[int] = None
    stock_qty: Optional[int] = None
    category: Optional[str] = None
    manufacturer: Optional[str] = None
    distributor: Optional[str] = None
    notes: Optional[str] = None

class NdaCreate(BaseModel):
    contact_id: Optional[str] = None
    lead_id: Optional[str] = None
    document_ref: Optional[str] = "deliverables/NDA_TEMPLATE.md"

class NdaStatusUpdate(BaseModel):
    status: str  # pending | signed | declined

class OpportunityCreate(BaseModel):
    company: str
    contact_name: Optional[str] = ""
    industry: Optional[str] = ""
    recommended_sku: Optional[str] = ""
    estimated_quantity: Optional[int] = 1
    unit_price_usd: Optional[float] = None
    stage: Optional[str] = "Prospecting"
    next_step: Optional[str] = ""
    value_proposition: Optional[str] = ""
    lead_id: Optional[str] = None
    contact_id: Optional[str] = None
    nda_required: Optional[bool] = True
    nda_status: Optional[str] = "Pending"


_DISTRIBUTOR_STATUSES = [
    "not_started", "applied", "in_review", "approved", "rejected", "listed", "on_hold",
]
_DISTRIBUTOR_PATH_TYPES = ["open_apply", "portal_review", "closed_bd", "marketplace"]

class DistributorListingCreate(BaseModel):
    channel: str
    path_type: str = "open_apply"
    status: Optional[str] = "not_started"
    portal_url: Optional[str] = None
    priority: Optional[str] = "P3"
    skus: Optional[str] = _LC_FLOW_SKUS
    notes: Optional[str] = ""
    next_action: Optional[str] = ""
    next_action_date: Optional[str] = None
    contact_email: Optional[str] = None

class DistributorListingUpdate(BaseModel):
    channel: Optional[str] = None
    path_type: Optional[str] = None
    status: Optional[str] = None
    portal_url: Optional[str] = None
    priority: Optional[str] = None
    skus: Optional[str] = None
    notes: Optional[str] = None
    next_action: Optional[str] = None
    next_action_date: Optional[str] = None
    applied_at: Optional[str] = None
    listed_at: Optional[str] = None
    contact_email: Optional[str] = None

class DistributorListingStatusUpdate(BaseModel):
    status: str  # not_started | applied | in_review | approved | rejected | listed | on_hold

class AgentRunRequest(BaseModel):
    task: str
    contact_id: Optional[str] = None
    context: Optional[str] = ""

# ──────────────────────────────────────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────────────────────────────────────

async def _daily_lead_gen_loop():
    """Background task: generate leads every LEAD_GEN_INTERVAL_SECS seconds."""
    await asyncio.sleep(10)  # small initial delay to let the server start up
    while True:
        try:
            saved = _run_daily_lead_generation()
            logger.info("Background lead generation complete: %d leads added", saved)
        except Exception as exc:
            logger.error("Background lead generation failed: %s", exc)
        await asyncio.sleep(LEAD_GEN_INTERVAL_SECS)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    logger.info("Database initialised. ALLOWED_ORIGINS=%s", ALLOWED_ORIGINS)
    task = asyncio.create_task(_daily_lead_gen_loop())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="Closing Agent Manufacturing — LC-Flow",
    description="AI-powered sales agent for LC-Flow Valve / industrial manufacturing (NDA-gated)",
    version="1.3.0",
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
            "INSERT INTO emails (id, contact_id, subject, body, status, approval_status, created_at) VALUES (?,?,?,?,?,?,?)",
            (eid, body.contact_id, email_data["subject"], email_data["body"], "Draft", "pending", now),
        )
    return {"id": eid, **email_data, "status": "Draft", "approval_status": "pending"}


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
        email_row = conn.execute("SELECT * FROM emails WHERE id=?", (email_id,)).fetchone()
        if not email_row:
            raise HTTPException(status_code=404, detail="Email not found")
        if email_row["approval_status"] == "pending":
            raise HTTPException(status_code=403, detail="Email must be approved before sending")
        if email_row["approval_status"] == "rejected":
            raise HTTPException(status_code=403, detail="This email has been rejected and cannot be sent")
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
    meeting = {
        "id": mid,
        "contact_id": body.contact_id,
        "title": body.title,
        "scheduled_at": body.scheduled_at,
        "duration_mins": body.duration_mins or 30,
        "location": body.location or "Video Call (Zoom)",
        "agenda": agenda,
    }
    invite = _generate_meeting_invite_email(meeting, contact, agenda)
    eid = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            """INSERT INTO meetings
               (id, contact_id, title, scheduled_at, duration_mins, location, agenda, status, approval_status, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (mid, body.contact_id, body.title, body.scheduled_at,
             body.duration_mins, body.location, agenda, "Scheduled", "pending", now),
        )
        conn.execute(
            """INSERT INTO emails
               (id, contact_id, subject, body, status, approval_status, created_at, meeting_id)
               VALUES (?,?,?,?,?,?,?,?)""",
            (eid, body.contact_id, invite["subject"], invite["body"], "Draft", "pending", now, mid),
        )
        # Advance stage
        conn.execute(
            "UPDATE contacts SET stage='Meeting Scheduled', updated_at=? WHERE id=? AND stage IN ('Identified','Contacted')",
            (now, body.contact_id),
        )
    return {
        "id": mid,
        "agenda": agenda,
        "status": "Scheduled",
        "approval_status": "pending",
        "email_id": eid,
        "ics_url": f"/meetings/{mid}/ics",
        "invite_subject": invite["subject"],
        "nda_gate": invite.get("nda_gate"),
    }


@app.get("/meetings")
def list_meetings(contact_id: Optional[str] = None):
    invite_join = (
        "LEFT JOIN emails e ON e.meeting_id = m.id "
    )
    select_cols = (
        "SELECT m.*, c.name as contact_name, c.company, "
        "e.id as invite_email_id, e.approval_status as invite_approval_status, "
        "e.status as invite_email_status, e.subject as invite_subject "
    )
    with get_db() as conn:
        if contact_id:
            rows = conn.execute(
                select_cols
                + "FROM meetings m "
                "JOIN contacts c ON m.contact_id=c.id "
                + invite_join
                + "WHERE m.contact_id=? ORDER BY m.scheduled_at",
                (contact_id,),
            ).fetchall()
        else:
            rows = conn.execute(
                select_cols
                + "FROM meetings m "
                "JOIN contacts c ON m.contact_id=c.id "
                + invite_join
                + "ORDER BY m.scheduled_at"
            ).fetchall()
    results = []
    for r in rows:
        d = dict(r)
        d["ics_url"] = f"/meetings/{d['id']}/ics"
        results.append(d)
    return results


@app.get("/meetings/{meeting_id}/ics")
def download_meeting_ics(meeting_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT m.*, c.name as contact_name, c.email as contact_email, c.company "
            "FROM meetings m JOIN contacts c ON m.contact_id=c.id WHERE m.id=?",
            (meeting_id,),
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Meeting not found")
    meeting = dict(row)
    contact = {
        "id": meeting["contact_id"],
        "name": meeting.get("contact_name") or "",
        "email": meeting.get("contact_email") or "",
        "company": meeting.get("company") or "",
    }
    ics = _build_ics(meeting, contact)
    filename = _safe_ics_filename(meeting.get("title") or "meeting")
    return Response(
        content=ics,
        media_type="text/calendar; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@app.get("/meetings/{meeting_id}/invite")
def get_meeting_invite(meeting_id: str):
    """Return ICS text plus linked invite email fields (if any)."""
    with get_db() as conn:
        row = conn.execute(
            "SELECT m.*, c.name as contact_name, c.email as contact_email, c.company "
            "FROM meetings m JOIN contacts c ON m.contact_id=c.id WHERE m.id=?",
            (meeting_id,),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Meeting not found")
        meeting = dict(row)
        email_row = conn.execute(
            "SELECT * FROM emails WHERE meeting_id=? ORDER BY created_at DESC LIMIT 1",
            (meeting_id,),
        ).fetchone()
    contact = {
        "id": meeting["contact_id"],
        "name": meeting.get("contact_name") or "",
        "email": meeting.get("contact_email") or "",
        "company": meeting.get("company") or "",
    }
    ics = _build_ics(meeting, contact)
    payload = {
        "meeting_id": meeting_id,
        "ics": ics,
        "ics_url": f"/meetings/{meeting_id}/ics",
        "filename": _safe_ics_filename(meeting.get("title") or "meeting"),
        "suggested_to": contact.get("email") or "",
        "suggested_subject": None,
        "suggested_body": None,
        "email_id": None,
        "approval_status": None,
    }
    if email_row:
        er = dict(email_row)
        payload["email_id"] = er["id"]
        payload["suggested_subject"] = er["subject"]
        payload["suggested_body"] = er["body"]
        payload["approval_status"] = er["approval_status"]
        payload["email_status"] = er["status"]
    return payload


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
    initial_status = body.status or "Pending"
    if initial_status not in ORDER_STATUSES:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {ORDER_STATUSES}")
    now = datetime.utcnow().isoformat()
    oid = str(uuid.uuid4())
    total = body.quantity_tons * body.unit_price_usd
    mfg = None
    with get_db() as conn:
        ensure_mfg_schema(conn)
        conn.execute(
            """INSERT INTO orders
               (id, contact_id, product, quantity_tons, unit_price_usd, status, notes, created_at, updated_at, po_number)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (oid, body.contact_id, body.product, body.quantity_tons,
             body.unit_price_usd, initial_status, body.notes, now, now, body.po_number),
        )
        # Advance stage to Closed Won
        conn.execute(
            "UPDATE contacts SET stage='Closed Won', updated_at=? WHERE id=?",
            (now, body.contact_id),
        )
        if initial_status == "Confirmed":
            mfg = on_po_acquired(conn, oid, po_number=body.po_number)
    out = {"id": oid, "total_usd": total, "status": initial_status, "po_number": body.po_number}
    if mfg:
        out["manufacturing"] = mfg
    return out


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
    mfg = None
    with get_db() as conn:
        ensure_mfg_schema(conn)
        row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        if body.po_number is not None:
            conn.execute(
                "UPDATE orders SET status=?, po_number=?, updated_at=? WHERE id=?",
                (body.status, body.po_number, now, order_id),
            )
        else:
            conn.execute(
                "UPDATE orders SET status=?, updated_at=? WHERE id=?",
                (body.status, now, order_id),
            )
        if body.status == "Confirmed":
            mfg = on_po_acquired(conn, order_id, po_number=body.po_number)
    out = {"message": "Order status updated", "status": body.status, "po_number": body.po_number}
    if mfg:
        out["manufacturing"] = mfg
    return out


@app.get("/orders/{order_id}/manufacturing")
def get_order_manufacturing(order_id: str):
    with get_db() as conn:
        ensure_mfg_schema(conn)
        row = conn.execute("SELECT id FROM orders WHERE id=?", (order_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Order not found")
        job = get_job_for_order(conn, order_id)
    if not job:
        return {"order_id": order_id, "job": None}
    return {"order_id": order_id, "job": job}


# ──────────────────────────────────────────────────────────────────────────────
# Routes – Manufacturing / Xometry handoff
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/manufacturing/jobs")
def api_list_manufacturing_jobs(order_id: Optional[str] = None):
    with get_db() as conn:
        return list_mfg_jobs(conn, order_id=order_id)


@app.get("/manufacturing/jobs/{job_id}")
def api_get_manufacturing_job(job_id: str):
    with get_db() as conn:
        job = get_job(conn, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Manufacturing job not found")
    return job


@app.put("/manufacturing/jobs/{job_id}/status")
def api_update_manufacturing_job_status(job_id: str, body: ManufacturingJobStatusUpdate):
    try:
        with get_db() as conn:
            result = update_mfg_job_status(
                conn,
                job_id,
                body.status,
                tracking_number=body.tracking_number,
                notes=body.notes,
            )
        return result
    except KeyError:
        raise HTTPException(status_code=404, detail="Manufacturing job not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/manufacturing/jobs/{job_id}/approve-xometry")
def api_approve_xometry(job_id: str):
    """Human gate before treating a job as submitted. Never auto-charges Xometry."""
    try:
        with get_db() as conn:
            return approve_xometry_job(conn, job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Manufacturing job not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/manufacturing/jobs/{job_id}/mock-advance")
def api_mock_advance(job_id: str):
    """Mock-only helper: step job forward one stage and mirror order status."""
    try:
        with get_db() as conn:
            return mock_advance_job(conn, job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Manufacturing job not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


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
            "INSERT INTO feedback (id, contact_id, message, sentiment, response, approval_status, created_at) VALUES (?,?,?,?,?,?,?)",
            (fid, body.contact_id, body.message, sentiment, ai_response, "pending", now),
        )
    return {"id": fid, "sentiment": sentiment, "response": ai_response, "approval_status": "pending"}


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
# Routes – Leads
# ──────────────────────────────────────────────────────────────────────────────

@app.post("/leads/generate", status_code=201)
def generate_leads(body: LeadGenerateRequest):
    """Generate new AI-powered leads and save them to the database."""
    count = max(1, min(body.count or 5, 20))
    saved = 0
    leads_out = []
    generated = _generate_leads_ai(count=count, industry_focus=body.industry_focus)
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        for lead in generated:
            lid = str(uuid.uuid4())
            industry = lead.get("industry") or body.industry_focus or "Beverage / PET Packaging"
            conn.execute(
                """INSERT INTO leads
                   (id, name, title, company, email, phone, linkedin,
                    industry, rationale, source, status, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (
                    lid,
                    lead.get("name", "Unknown"),
                    lead.get("title", ""),
                    lead.get("company", "Unknown"),
                    lead.get("email", ""),
                    lead.get("phone", ""),
                    lead.get("linkedin", ""),
                    industry,
                    lead.get("rationale", ""),
                    "AI Generated",
                    "New",
                    now,
                ),
            )
            leads_out.append({**lead, "id": lid, "industry": industry, "status": "New", "created_at": now})
            saved += 1
    return {"generated": saved, "leads": leads_out}


@app.get("/leads")
def list_leads(status: Optional[str] = None):
    with get_db() as conn:
        if status:
            rows = conn.execute(
                "SELECT * FROM leads WHERE status=? ORDER BY created_at DESC",
                (status,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM leads ORDER BY created_at DESC"
            ).fetchall()
    return [dict(r) for r in rows]


@app.put("/leads/{lead_id}/status")
def update_lead_status(lead_id: str, body: LeadStatusUpdate):
    allowed = ["New", "Contacted", "Qualified", "Converted", "Dismissed"]
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {allowed}")
    with get_db() as conn:
        result = conn.execute(
            "UPDATE leads SET status=? WHERE id=?",
            (body.status, lead_id),
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead status updated", "status": body.status}


@app.post("/leads/{lead_id}/convert", status_code=201)
def convert_lead_to_contact(lead_id: str):
    """Promote a lead into the contacts pipeline."""
    with get_db() as conn:
        row = conn.execute("SELECT * FROM leads WHERE id=?", (lead_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead = dict(row)
    now = datetime.utcnow().isoformat()
    cid = str(uuid.uuid4())
    with get_db() as conn:
        conn.execute(
            """INSERT INTO contacts
               (id, name, title, company, email, phone, linkedin,
                industry, stage, notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                cid, lead["name"], lead["title"], lead["company"],
                lead["email"], lead["phone"], lead["linkedin"],
                lead.get("industry") or "Beverage / PET Packaging", "Identified",
                lead.get("rationale", ""), now, now,
            ),
        )
        conn.execute(
            "UPDATE leads SET status='Converted' WHERE id=?",
            (lead_id,),
        )
    return {"message": "Lead converted to contact", "contact_id": cid}


@app.delete("/leads/{lead_id}")
def delete_lead(lead_id: str):
    with get_db() as conn:
        result = conn.execute("DELETE FROM leads WHERE id=?", (lead_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Lead not found")
    return {"message": "Lead deleted"}


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
            "(SELECT COALESCE(SUM(quantity_tons * unit_price_usd), 0) FROM orders WHERE status != 'Cancelled') as pipeline_usd, "
            "(SELECT COUNT(*) FROM leads WHERE status='New') as new_leads, "
            "(SELECT COUNT(*) FROM emails WHERE approval_status='pending') + "
            "(SELECT COUNT(*) FROM meetings WHERE approval_status='pending') + "
            "(SELECT COUNT(*) FROM feedback WHERE approval_status='pending') as pending_approvals "
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
                "INSERT INTO emails (id, contact_id, subject, body, status, approval_status, created_at) VALUES (?,?,?,?,?,?,?)",
                (eid, body.contact_id, email_data["subject"], email_data["body"], "Draft", "pending", now),
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
        # General AI assistant — always NDA-aware for LC-Flow
        nda_ok = False
        if contact:
            nda_ok = _contact_nda_signed(contact_id=body.contact_id)
        nda_rule = (
            "CRITICAL NDA POLICY: Never share detailed LC-Flow specs, drawings, CAD, "
            "material process details, or unit pricing until an NDA is signed for that "
            "contact/lead. If NDA is not signed, offer to send the Mutual NDA first "
            "(deliverables/NDA_TEMPLATE.md). High-level product category mentions are OK."
        )
        if contact and not nda_ok:
            nda_rule += " Current contact NDA status: NOT SIGNED — gate all technical/pricing content."
        elif contact and nda_ok:
            nda_rule += " Current contact NDA status: SIGNED — technical discussion OK."
        system = (
            "You are an intelligent B2B sales agent for LC-Flow Valve and Distribution "
            "Adaptor (PTC Inc / Industrial and Molecular Solutions), covering Aerospace, "
            "Beverage/PET, PET Air Conveyors, and Automotive Engineering. "
            + nda_rule +
            " Help the user with their sales task concisely."
        )
        user_msg = body.task
        if contact:
            user_msg += f"\nContact: {contact['name']}, {contact.get('title','')} at {contact['company']}"
        if body.context:
            user_msg += f"\nContext: {body.context}"
        result = _ai_complete(system, user_msg)
        if not result:
            if contact and not nda_ok:
                result = (
                    f"NDA is not yet signed for {contact['name']} at {contact['company']}. "
                    "I can draft an NDA-first outreach or create a pending NDA via POST /ndas. "
                    "I will not share detailed specs or pricing until the NDA is marked signed."
                )
            else:
                result = (
                    "I can help you with: NDA-gated outreach emails, meetings, inventory, "
                    "orders, feedback, and distributor listing tracking "
                    "(/distributor-listings). Please specify a contact and task."
                )
        return {"action": "agent_response", "response": result, "nda_signed": nda_ok}



# ──────────────────────────────────────────────────────────────────────────────
# Routes – Approvals
# ──────────────────────────────────────────────────────────────────────────────

_APPROVAL_TABLES = {"emails": "emails", "meetings": "meetings", "feedback": "feedback"}

# Pre-built approve/reject queries keyed by comm_type to avoid any f-string SQL construction
_APPROVE_QUERIES = {
    "emails":   "UPDATE emails   SET approval_status='approved' WHERE id=? AND approval_status='pending'",
    "meetings": "UPDATE meetings SET approval_status='approved' WHERE id=? AND approval_status='pending'",
    "feedback": "UPDATE feedback SET approval_status='approved' WHERE id=? AND approval_status='pending'",
}
_REJECT_QUERIES = {
    "emails":   "UPDATE emails   SET approval_status='rejected' WHERE id=? AND approval_status='pending'",
    "meetings": "UPDATE meetings SET approval_status='rejected' WHERE id=? AND approval_status='pending'",
    "feedback": "UPDATE feedback SET approval_status='rejected' WHERE id=? AND approval_status='pending'",
}


@app.get("/approvals")
def list_approvals():
    """Return all outgoing communications pending manager approval."""
    with get_db() as conn:
        pending_emails = conn.execute(
            "SELECT e.*, c.name as contact_name, c.company FROM emails e "
            "JOIN contacts c ON e.contact_id = c.id "
            "WHERE e.approval_status = 'pending' ORDER BY e.created_at DESC"
        ).fetchall()
        pending_meetings = conn.execute(
            "SELECT m.*, c.name as contact_name, c.company FROM meetings m "
            "JOIN contacts c ON m.contact_id = c.id "
            "WHERE m.approval_status = 'pending' ORDER BY m.created_at DESC"
        ).fetchall()
        pending_feedback = conn.execute(
            "SELECT f.*, c.name as contact_name, c.company FROM feedback f "
            "JOIN contacts c ON f.contact_id = c.id "
            "WHERE f.approval_status = 'pending' ORDER BY f.created_at DESC"
        ).fetchall()
    emails_list = [dict(r) for r in pending_emails]
    meetings_list = [dict(r) for r in pending_meetings]
    feedback_list = [dict(r) for r in pending_feedback]
    return {
        "emails": emails_list,
        "meetings": meetings_list,
        "feedback": feedback_list,
        "total": len(emails_list) + len(meetings_list) + len(feedback_list),
    }


@app.post("/approvals/{comm_type}/{item_id}/approve")
def approve_item(comm_type: str, item_id: str):
    """Approve a pending outgoing communication."""
    if comm_type not in _APPROVE_QUERIES:
        raise HTTPException(status_code=400, detail=f"Invalid type. Choose from: {list(_APPROVAL_TABLES)}")
    with get_db() as conn:
        result = conn.execute(_APPROVE_QUERIES[comm_type], (item_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found or not pending approval")
    return {"message": "Approved", "id": item_id, "comm_type": comm_type}


@app.post("/approvals/{comm_type}/{item_id}/reject")
def reject_item(comm_type: str, item_id: str):
    """Reject a pending outgoing communication."""
    if comm_type not in _REJECT_QUERIES:
        raise HTTPException(status_code=400, detail=f"Invalid type. Choose from: {list(_APPROVAL_TABLES)}")
    with get_db() as conn:
        result = conn.execute(_REJECT_QUERIES[comm_type], (item_id,))
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Item not found or not pending approval")
    return {"message": "Rejected", "id": item_id, "comm_type": comm_type}



# ──────────────────────────────────────────────────────────────────────────────
# Routes – Inventory (LC-Flow SKUs)
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/inventory")
def list_inventory():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM inventory ORDER BY sku").fetchall()
    return [dict(r) for r in rows]


@app.post("/inventory", status_code=201)
def create_inventory(body: InventoryCreate):
    now = datetime.utcnow().isoformat()
    iid = str(uuid.uuid4())
    with get_db() as conn:
        existing = conn.execute("SELECT id FROM inventory WHERE sku=?", (body.sku,)).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail=f"SKU {body.sku} already exists")
        conn.execute(
            """INSERT INTO inventory
               (id, sku, name, description, material, unit_price_usd, units_per_pack,
                stock_qty, category, manufacturer, distributor, notes, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                iid, body.sku, body.name, body.description, body.material,
                body.unit_price_usd, body.units_per_pack, body.stock_qty,
                body.category, body.manufacturer, body.distributor, body.notes, now,
            ),
        )
    return {"id": iid, "sku": body.sku, "message": "Inventory item created"}


@app.get("/inventory/{sku}")
def get_inventory(sku: str):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM inventory WHERE sku=?", (sku,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="SKU not found")
    return dict(row)


@app.put("/inventory/{sku}")
def update_inventory(sku: str, body: InventoryUpdate):
    fields = body.dict(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [sku]
    with get_db() as conn:
        result = conn.execute(f"UPDATE inventory SET {sets} WHERE sku=?", vals)
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="SKU not found")
        row = conn.execute("SELECT * FROM inventory WHERE sku=?", (sku,)).fetchone()
    return dict(row)


# ──────────────────────────────────────────────────────────────────────────────
# Routes – NDAs (required for all LC-Flow sales discussions)
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/ndas")
def list_ndas(status: Optional[str] = None, contact_id: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM ndas WHERE 1=1"
        params: list = []
        if status:
            query += " AND status=?"
            params.append(status)
        if contact_id:
            query += " AND contact_id=?"
            params.append(contact_id)
        query += " ORDER BY created_at DESC"
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@app.post("/ndas", status_code=201)
def create_nda(body: NdaCreate):
    if not body.contact_id and not body.lead_id:
        raise HTTPException(status_code=400, detail="contact_id or lead_id required")
    now = datetime.utcnow().isoformat()
    nid = str(uuid.uuid4())
    with get_db() as conn:
        if body.contact_id:
            row = conn.execute("SELECT id FROM contacts WHERE id=?", (body.contact_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Contact not found")
        if body.lead_id:
            row = conn.execute("SELECT id FROM leads WHERE id=?", (body.lead_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Lead not found")
        conn.execute(
            """INSERT INTO ndas (id, contact_id, lead_id, status, signed_at, document_ref, created_at)
               VALUES (?,?,?,?,?,?,?)""",
            (nid, body.contact_id, body.lead_id, "pending", None, body.document_ref, now),
        )
    return {
        "id": nid,
        "status": "pending",
        "document_ref": body.document_ref,
        "message": "NDA record created — send Mutual NDA before technical specs/pricing",
    }


@app.put("/ndas/{nda_id}/status")
def update_nda_status(nda_id: str, body: NdaStatusUpdate):
    allowed = ["pending", "signed", "declined"]
    if body.status not in allowed:
        raise HTTPException(status_code=400, detail=f"Invalid status. Choose from: {allowed}")
    now = datetime.utcnow().isoformat()
    signed_at = now if body.status == "signed" else None
    with get_db() as conn:
        row = conn.execute("SELECT * FROM ndas WHERE id=?", (nda_id,)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="NDA not found")
        conn.execute(
            "UPDATE ndas SET status=?, signed_at=? WHERE id=?",
            (body.status, signed_at, nda_id),
        )
        if body.status == "signed" and row["contact_id"]:
            try:
                conn.execute(
                    "UPDATE contacts SET nda_signed=1, updated_at=? WHERE id=?",
                    (now, row["contact_id"]),
                )
            except Exception:
                pass
        if body.status == "declined" and row["contact_id"]:
            try:
                conn.execute(
                    "UPDATE contacts SET nda_signed=0, updated_at=? WHERE id=?",
                    (now, row["contact_id"]),
                )
            except Exception:
                pass
    return {"message": "NDA status updated", "status": body.status, "signed_at": signed_at}


# ──────────────────────────────────────────────────────────────────────────────
# Routes – Opportunities
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/opportunities")
def list_opportunities(stage: Optional[str] = None):
    with get_db() as conn:
        if stage:
            rows = conn.execute(
                "SELECT * FROM opportunities WHERE stage=? ORDER BY estimated_deal_value_usd DESC",
                (stage,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM opportunities ORDER BY estimated_deal_value_usd DESC"
            ).fetchall()
    return [dict(r) for r in rows]


@app.post("/opportunities", status_code=201)
def create_opportunity(body: OpportunityCreate):
    now = datetime.utcnow().isoformat()
    oid = str(uuid.uuid4())
    unit = body.unit_price_usd
    if unit is None and body.recommended_sku:
        with get_db() as conn:
            inv = conn.execute(
                "SELECT unit_price_usd FROM inventory WHERE sku=?", (body.recommended_sku,)
            ).fetchone()
        if inv:
            unit = inv["unit_price_usd"]
    unit = unit or 0.0
    qty = body.estimated_quantity or 1
    deal = round(unit * qty, 2)
    with get_db() as conn:
        conn.execute(
            """INSERT INTO opportunities
               (id, company, contact_name, industry, recommended_sku, estimated_quantity,
                unit_price_usd, estimated_deal_value_usd, stage, next_step, value_proposition,
                nda_required, nda_status, lead_id, contact_id, created_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                oid, body.company, body.contact_name, body.industry, body.recommended_sku,
                qty, unit, deal, body.stage, body.next_step, body.value_proposition,
                1 if body.nda_required else 0, body.nda_status or "Pending",
                body.lead_id, body.contact_id, now,
            ),
        )
    return {
        "id": oid,
        "estimated_deal_value_usd": deal,
        "nda_required": True,
        "nda_status": body.nda_status or "Pending",
        "message": "Opportunity created — NDA required before technical/pricing deep-dive",
    }



# ──────────────────────────────────────────────────────────────────────────────
# Routes – Distributor listings (MSC / Zoro / catalogs tracker)
# ──────────────────────────────────────────────────────────────────────────────

@app.get("/distributor-listings")
def list_distributor_listings(status: Optional[str] = None, channel: Optional[str] = None):
    with get_db() as conn:
        query = "SELECT * FROM distributor_listings WHERE 1=1"
        params: list = []
        if status:
            query += " AND status=?"
            params.append(status)
        if channel:
            query += " AND channel=?"
            params.append(channel)
        query += " ORDER BY priority ASC, channel ASC"
        rows = conn.execute(query, params).fetchall()
    return [dict(r) for r in rows]


@app.post("/distributor-listings", status_code=201)
def create_distributor_listing(body: DistributorListingCreate):
    if body.path_type not in _DISTRIBUTOR_PATH_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path_type. Choose from: {_DISTRIBUTOR_PATH_TYPES}",
        )
    status = body.status or "not_started"
    if status not in _DISTRIBUTOR_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Choose from: {_DISTRIBUTOR_STATUSES}",
        )
    now = datetime.utcnow().isoformat()
    lid = str(uuid.uuid4())
    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM distributor_listings WHERE channel=?", (body.channel,)
        ).fetchone()
        if existing:
            raise HTTPException(status_code=409, detail=f"Channel {body.channel} already exists")
        conn.execute(
            """INSERT INTO distributor_listings
               (id, channel, path_type, status, portal_url, priority, skus,
                notes, next_action, next_action_date, applied_at, listed_at,
                contact_email, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                lid, body.channel, body.path_type, status, body.portal_url,
                body.priority or "P3", body.skus, body.notes, body.next_action,
                body.next_action_date, None, None, body.contact_email, now, now,
            ),
        )
    return {"id": lid, "channel": body.channel, "status": status, "message": "Distributor listing created"}


@app.get("/distributor-listings/{listing_id}")
def get_distributor_listing(listing_id: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM distributor_listings WHERE id=?", (listing_id,)
        ).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Distributor listing not found")
    return dict(row)


@app.put("/distributor-listings/{listing_id}")
def update_distributor_listing(listing_id: str, body: DistributorListingUpdate):
    fields = body.dict(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    if "path_type" in fields and fields["path_type"] not in _DISTRIBUTOR_PATH_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path_type. Choose from: {_DISTRIBUTOR_PATH_TYPES}",
        )
    if "status" in fields and fields["status"] not in _DISTRIBUTOR_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Choose from: {_DISTRIBUTOR_STATUSES}",
        )
    now = datetime.utcnow().isoformat()
    fields["updated_at"] = now
    if fields.get("status") == "applied" and "applied_at" not in fields:
        fields["applied_at"] = now
    if fields.get("status") == "listed" and "listed_at" not in fields:
        fields["listed_at"] = now
    sets = ", ".join(f"{k}=?" for k in fields)
    vals = list(fields.values()) + [listing_id]
    with get_db() as conn:
        result = conn.execute(
            f"UPDATE distributor_listings SET {sets} WHERE id=?", vals
        )
        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Distributor listing not found")
        row = conn.execute(
            "SELECT * FROM distributor_listings WHERE id=?", (listing_id,)
        ).fetchone()
    return dict(row)


@app.put("/distributor-listings/{listing_id}/status")
def update_distributor_listing_status(listing_id: str, body: DistributorListingStatusUpdate):
    if body.status not in _DISTRIBUTOR_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Choose from: {_DISTRIBUTOR_STATUSES}",
        )
    now = datetime.utcnow().isoformat()
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM distributor_listings WHERE id=?", (listing_id,)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Distributor listing not found")
        applied_at = row["applied_at"]
        listed_at = row["listed_at"]
        if body.status == "applied" and not applied_at:
            applied_at = now
        if body.status == "listed" and not listed_at:
            listed_at = now
        conn.execute(
            """UPDATE distributor_listings
               SET status=?, applied_at=?, listed_at=?, updated_at=? WHERE id=?""",
            (body.status, applied_at, listed_at, now, listing_id),
        )
        updated = conn.execute(
            "SELECT * FROM distributor_listings WHERE id=?", (listing_id,)
        ).fetchone()
    return dict(updated)


@app.get("/health")
def health():
    payload = {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "product": "LC-Flow Valve",
        "distributor_listings": True,
    }
    payload.update(xometry_config_summary())
    return payload
