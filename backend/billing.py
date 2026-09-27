"""
Internal billing / invoices for Closing Agent Manufacturing.

Creates Draft invoices when an order is Confirmed with a PO number.
No payment processor — HTML (print-to-PDF) + optional reportlab PDF.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

logger = logging.getLogger(__name__)

SELLER = {
    "company": "Industrial and Molecular Solutions / PTC Inc",
    "name": "James Gallagher",
    "email": "Jgallagher10@gmail.com",
    "phone": "610-393-1102",
}

INVOICE_STATUSES = ["Draft", "Sent", "Paid", "Void"]
APPROVAL_STATUSES = ["pending", "approved", "rejected"]
DEFAULT_TERMS = "Net 30"
DEFAULT_CURRENCY = "USD"


def ensure_invoices_schema(conn) -> None:
    """Create invoices table if missing. Safe to call repeatedly."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            contact_id TEXT NOT NULL,
            invoice_number TEXT NOT NULL UNIQUE,
            po_number TEXT,
            status TEXT NOT NULL DEFAULT 'Draft',
            approval_status TEXT NOT NULL DEFAULT 'pending',
            subtotal_usd REAL NOT NULL DEFAULT 0,
            tax_usd REAL NOT NULL DEFAULT 0,
            total_usd REAL NOT NULL DEFAULT 0,
            currency TEXT NOT NULL DEFAULT 'USD',
            terms TEXT DEFAULT 'Net 30',
            notes TEXT,
            line_items TEXT,
            issued_at TEXT,
            due_at TEXT,
            paid_at TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (contact_id) REFERENCES contacts(id)
        )
        """
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_invoices_order_id ON invoices(order_id)"
    )


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def generate_invoice_number(conn) -> str:
    """INV-YYYYMMDD-XXXX with random suffix; retry on rare collision."""
    day = datetime.utcnow().strftime("%Y%m%d")
    for _ in range(8):
        suffix = uuid.uuid4().hex[:4].upper()
        number = f"INV-{day}-{suffix}"
        exists = conn.execute(
            "SELECT 1 FROM invoices WHERE invoice_number=?", (number,)
        ).fetchone()
        if not exists:
            return number
    return f"INV-{day}-{uuid.uuid4().hex[:8].upper()}"


def get_invoice_for_order(conn, order_id: str) -> Optional[dict]:
    row = conn.execute(
        "SELECT * FROM invoices WHERE order_id=? ORDER BY created_at DESC LIMIT 1",
        (order_id,),
    ).fetchone()
    return _row_to_invoice(row) if row else None


def get_invoice(conn, invoice_id: str) -> Optional[dict]:
    row = conn.execute("SELECT * FROM invoices WHERE id=?", (invoice_id,)).fetchone()
    return _row_to_invoice(row) if row else None


def _row_to_invoice(row) -> dict:
    d = dict(row)
    raw = d.get("line_items")
    if isinstance(raw, str):
        try:
            d["line_items"] = json.loads(raw) if raw else []
        except json.JSONDecodeError:
            d["line_items"] = []
    elif raw is None:
        d["line_items"] = []
    return d


def _line_items_from_order(order: dict) -> list[dict]:
    qty = float(order.get("quantity_tons") or 0)
    unit = float(order.get("unit_price_usd") or 0)
    product = order.get("product") or "Item"
    return [
        {
            "product": product,
            "sku": product,
            "qty": qty,
            "unit_price": unit,
            "line_total": round(qty * unit, 2),
        }
    ]


def _build_invoice_email(invoice: dict, contact: dict) -> dict:
    company = contact.get("company") or "Customer"
    name = contact.get("name") or "there"
    inv_no = invoice["invoice_number"]
    po = invoice.get("po_number") or "—"
    total = invoice.get("total_usd") or 0
    due = (invoice.get("due_at") or "")[:10] or "—"
    subject = f"Invoice {inv_no} for PO {po} — {company}"
    body = (
        f"Dear {name},\n\n"
        f"Please find invoice {inv_no} for purchase order {po}.\n\n"
        f"Subtotal: ${invoice.get('subtotal_usd', 0):,.2f} {invoice.get('currency', 'USD')}\n"
        f"Tax: ${invoice.get('tax_usd', 0):,.2f}\n"
        f"Total due: ${total:,.2f} {invoice.get('currency', 'USD')}\n"
        f"Terms: {invoice.get('terms') or DEFAULT_TERMS}\n"
        f"Due date: {due}\n\n"
        f"This invoice is provided for your records following receipt of your PO. "
        f"Payment instructions will be confirmed separately; this system does not "
        f"process card or ACH payments.\n\n"
        f"Best regards,\n"
        f"{SELLER['name']}\n"
        f"{SELLER['company']}\n"
        f"{SELLER['email']} · {SELLER['phone']}\n"
    )
    return {"subject": subject, "body": body}


def create_invoice_for_order(
    conn,
    order_id: str,
    *,
    require_po: bool = True,
) -> Optional[dict]:
    """
    Create a Draft invoice (+ pending email) for an order if none exists.

    Requires order status Confirmed. If require_po is True (default auto path),
    also requires a non-empty po_number. Manual endpoint may pass require_po=False
    only when caller already validated; we still prefer PO when present.
    """
    ensure_invoices_schema(conn)
    order_row = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order_row:
        return None
    order = dict(order_row)
    if order.get("status") != "Confirmed":
        return None
    po = (order.get("po_number") or "").strip()
    if require_po and not po:
        return None

    existing = get_invoice_for_order(conn, order_id)
    if existing:
        return existing

    contact_row = conn.execute(
        "SELECT * FROM contacts WHERE id=?", (order["contact_id"],)
    ).fetchone()
    contact = dict(contact_row) if contact_row else {"id": order["contact_id"], "name": "", "company": ""}

    line_items = _line_items_from_order(order)
    subtotal = round(sum(li["line_total"] for li in line_items), 2)
    tax = 0.0
    total = round(subtotal + tax, 2)
    now = _now_iso()
    issued = datetime.utcnow()
    due = issued + timedelta(days=30)
    iid = str(uuid.uuid4())
    inv_number = generate_invoice_number(conn)

    invoice = {
        "id": iid,
        "order_id": order_id,
        "contact_id": order["contact_id"],
        "invoice_number": inv_number,
        "po_number": po or None,
        "status": "Draft",
        "approval_status": "pending",
        "subtotal_usd": subtotal,
        "tax_usd": tax,
        "total_usd": total,
        "currency": DEFAULT_CURRENCY,
        "terms": DEFAULT_TERMS,
        "notes": order.get("notes") or "",
        "line_items": line_items,
        "issued_at": issued.isoformat(),
        "due_at": due.isoformat(),
        "paid_at": None,
        "created_at": now,
        "updated_at": now,
    }

    conn.execute(
        """INSERT INTO invoices
           (id, order_id, contact_id, invoice_number, po_number, status, approval_status,
            subtotal_usd, tax_usd, total_usd, currency, terms, notes, line_items,
            issued_at, due_at, paid_at, created_at, updated_at)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            invoice["id"],
            invoice["order_id"],
            invoice["contact_id"],
            invoice["invoice_number"],
            invoice["po_number"],
            invoice["status"],
            invoice["approval_status"],
            invoice["subtotal_usd"],
            invoice["tax_usd"],
            invoice["total_usd"],
            invoice["currency"],
            invoice["terms"],
            invoice["notes"],
            json.dumps(line_items),
            invoice["issued_at"],
            invoice["due_at"],
            None,
            now,
            now,
        ),
    )

    email = _build_invoice_email(invoice, contact)
    eid = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO emails
           (id, contact_id, subject, body, status, approval_status, created_at, invoice_id)
           VALUES (?,?,?,?,?,?,?,?)""",
        (
            eid,
            order["contact_id"],
            email["subject"],
            email["body"],
            "Draft",
            "pending",
            now,
            iid,
        ),
    )
    invoice["email_id"] = eid
    invoice["email_subject"] = email["subject"]
    logger.info(
        "Created invoice %s for order %s (PO %s)", inv_number, order_id, po or "—"
    )
    return invoice


def maybe_invoice_on_po_confirmed(conn, order_id: str) -> Optional[dict]:
    """Auto path: Confirmed + PO → create invoice if missing."""
    return create_invoice_for_order(conn, order_id, require_po=True)


def list_invoices(conn, order_id: Optional[str] = None) -> list[dict]:
    ensure_invoices_schema(conn)
    if order_id:
        rows = conn.execute(
            "SELECT i.*, c.name as contact_name, c.company FROM invoices i "
            "JOIN contacts c ON i.contact_id=c.id WHERE i.order_id=? "
            "ORDER BY i.created_at DESC",
            (order_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT i.*, c.name as contact_name, c.company FROM invoices i "
            "JOIN contacts c ON i.contact_id=c.id ORDER BY i.created_at DESC"
        ).fetchall()
    return [_row_to_invoice(r) for r in rows]


def update_invoice_status(conn, invoice_id: str, status: str) -> dict:
    ensure_invoices_schema(conn)
    if status not in INVOICE_STATUSES:
        raise ValueError(f"Invalid status. Choose from: {INVOICE_STATUSES}")
    inv = get_invoice(conn, invoice_id)
    if not inv:
        raise KeyError("Invoice not found")
    if status == "Sent" and inv.get("approval_status") != "approved":
        raise PermissionError("Invoice must be approved before status can be Sent")
    now = _now_iso()
    paid_at = inv.get("paid_at")
    if status == "Paid" and not paid_at:
        paid_at = now
    if status != "Paid":
        # keep existing paid_at if re-opening? clear when leaving Paid
        if inv.get("status") == "Paid" and status != "Paid":
            paid_at = None
    conn.execute(
        "UPDATE invoices SET status=?, paid_at=?, updated_at=? WHERE id=?",
        (status, paid_at, now, invoice_id),
    )
    updated = get_invoice(conn, invoice_id)
    assert updated is not None
    return updated


def _esc(text: Any) -> str:
    s = "" if text is None else str(text)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_invoice_html(invoice: dict, contact: dict) -> str:
    lines = invoice.get("line_items") or []
    rows_html = ""
    for li in lines:
        rows_html += (
            "<tr>"
            f"<td>{_esc(li.get('product') or li.get('sku'))}</td>"
            f"<td style='text-align:right'>{_esc(li.get('qty'))}</td>"
            f"<td style='text-align:right'>${float(li.get('unit_price') or 0):,.2f}</td>"
            f"<td style='text-align:right'>${float(li.get('line_total') or 0):,.2f}</td>"
            "</tr>"
        )
    issued = (invoice.get("issued_at") or "")[:10]
    due = (invoice.get("due_at") or "")[:10]
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8" />
<title>Invoice {_esc(invoice.get('invoice_number'))}</title>
<style>
  body {{ font-family: Georgia, 'Times New Roman', serif; color: #1a1a1a; max-width: 800px; margin: 40px auto; padding: 0 24px; }}
  h1 {{ font-size: 28px; margin: 0 0 4px; }}
  .muted {{ color: #555; font-size: 14px; }}
  .grid {{ display: flex; justify-content: space-between; gap: 24px; margin: 28px 0; }}
  .box {{ flex: 1; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
  th, td {{ border-bottom: 1px solid #ddd; padding: 10px 8px; text-align: left; }}
  th {{ background: #f4f4f4; font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em; }}
  .totals {{ margin-top: 16px; text-align: right; }}
  .totals div {{ margin: 4px 0; }}
  .total-due {{ font-size: 20px; font-weight: bold; margin-top: 8px; }}
  .badge {{ display: inline-block; padding: 2px 10px; border-radius: 12px; background: #eee; font-size: 12px; }}
  @media print {{ body {{ margin: 0; }} .no-print {{ display: none; }} }}
</style>
</head>
<body>
  <p class="no-print muted">Tip: use your browser Print → Save as PDF.</p>
  <div class="grid">
    <div class="box">
      <h1>INVOICE</h1>
      <div><strong>{_esc(invoice.get('invoice_number'))}</strong>
        <span class="badge">{_esc(invoice.get('status'))}</span></div>
      <div class="muted">Issued: {_esc(issued)} · Due: {_esc(due)} · {_esc(invoice.get('terms') or DEFAULT_TERMS)}</div>
      <div class="muted">PO: {_esc(invoice.get('po_number') or '—')}</div>
    </div>
    <div class="box" style="text-align:right">
      <strong>{_esc(SELLER['company'])}</strong><br/>
      {_esc(SELLER['name'])}<br/>
      {_esc(SELLER['email'])}<br/>
      {_esc(SELLER['phone'])}
    </div>
  </div>
  <div class="grid">
    <div class="box">
      <div class="muted">Bill To</div>
      <strong>{_esc(contact.get('name'))}</strong><br/>
      {_esc(contact.get('company'))}<br/>
      {_esc(contact.get('email') or '')}<br/>
      {_esc(contact.get('phone') or '')}
    </div>
  </div>
  <table>
    <thead>
      <tr><th>Product / SKU</th><th style="text-align:right">Qty</th>
          <th style="text-align:right">Unit Price</th><th style="text-align:right">Line Total</th></tr>
    </thead>
    <tbody>
      {rows_html or '<tr><td colspan="4" class="muted">No line items</td></tr>'}
    </tbody>
  </table>
  <div class="totals">
    <div>Subtotal: ${float(invoice.get('subtotal_usd') or 0):,.2f} {_esc(invoice.get('currency'))}</div>
    <div>Tax: ${float(invoice.get('tax_usd') or 0):,.2f}</div>
    <div class="total-due">Total due: ${float(invoice.get('total_usd') or 0):,.2f} {_esc(invoice.get('currency'))}</div>
  </div>
  {f'<p class="muted" style="margin-top:28px">{_esc(invoice.get("notes"))}</p>' if invoice.get("notes") else ""}
  <p class="muted" style="margin-top:32px;font-size:12px">
    Internal billing record only — Closing Agent does not process payments.
    Contact { _esc(SELLER['email']) } for remittance details.
  </p>
</body>
</html>
"""


def render_invoice_pdf(invoice: dict, contact: dict) -> bytes:
    """Generate a simple PDF via reportlab. Raises ImportError if unavailable."""
    from io import BytesIO

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter, leftMargin=0.75 * inch, rightMargin=0.75 * inch)
    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph(f"<b>INVOICE {invoice.get('invoice_number')}</b>", styles["Title"]))
    story.append(Paragraph(f"Status: {invoice.get('status')} · Terms: {invoice.get('terms') or DEFAULT_TERMS}", styles["Normal"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>From:</b> {SELLER['company']}<br/>{SELLER['name']} · {SELLER['email']} · {SELLER['phone']}", styles["Normal"]))
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            f"<b>Bill To:</b> {contact.get('name') or ''} — {contact.get('company') or ''}<br/>"
            f"{contact.get('email') or ''} {contact.get('phone') or ''}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 8))
    story.append(
        Paragraph(
            f"PO: {invoice.get('po_number') or '—'} · Issued: {(invoice.get('issued_at') or '')[:10]} · "
            f"Due: {(invoice.get('due_at') or '')[:10]}",
            styles["Normal"],
        )
    )
    story.append(Spacer(1, 16))

    data = [["Product / SKU", "Qty", "Unit Price", "Line Total"]]
    for li in invoice.get("line_items") or []:
        data.append(
            [
                str(li.get("product") or li.get("sku") or ""),
                str(li.get("qty") or ""),
                f"${float(li.get('unit_price') or 0):,.2f}",
                f"${float(li.get('line_total') or 0):,.2f}",
            ]
        )
    data.append(["", "", "Subtotal", f"${float(invoice.get('subtotal_usd') or 0):,.2f}"])
    data.append(["", "", "Tax", f"${float(invoice.get('tax_usd') or 0):,.2f}"])
    data.append(["", "", "Total", f"${float(invoice.get('total_usd') or 0):,.2f} {invoice.get('currency') or 'USD'}"])

    table = Table(data, colWidths=[3.2 * inch, 1 * inch, 1.2 * inch, 1.2 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0f0f0")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -4), 0.25, colors.grey),
                ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                ("FONTNAME", (2, -1), (-1, -1), "Helvetica-Bold"),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 24))
    story.append(
        Paragraph(
            "Internal billing record only — Closing Agent does not process payments.",
            styles["Italic"],
        )
    )
    doc.build(story)
    return buf.getvalue()
