# Internal billing / invoices — Closing Agent Manufacturing

**Seller:** Industrial and Molecular Solutions / PTC Inc  
**Contact:** James Gallagher · 610-393-1102 · Jgallagher10@gmail.com  
**Currency:** USD · **Default terms:** Net 30  
**Date:** 2026-09-26 PT

---

## What this does

When an order becomes **Confirmed** and has a **PO number**, Closing Agent:

1. Creates a **Draft** invoice (if one does not already exist for that order).
2. Creates a **pending** invoice email draft (`emails.invoice_id`) — subject like `Invoice INV-… for PO … — {company}`.
3. Continues existing manufacturing handoff via `on_po_acquired` (unchanged).

Nothing is auto-sent and **no payment processor** is connected (no Stripe/ACH yet). Approving and marking Sent only update Closing Agent status.

---

## Trigger rules

| Situation | Auto-invoice? |
|-----------|----------------|
| Create / update order → **Confirmed** **with** `po_number` | Yes (if missing) |
| Confirmed **without** PO | No |
| PO added later by setting status **Confirmed** again with `po_number` | Yes (if missing) |
| Manual `POST /orders/{id}/invoice` on a Confirmed order | Yes (PO optional) |

Duplicate invoices for the same order are not created.

---

## Statuses

**Invoice `status`:** `Draft` → `Sent` → `Paid` (or `Void`)

- Setting **Sent** requires `approval_status=approved`.
- **Paid** sets `paid_at`.
- **Void** cancels the invoice record (no payment).

**`approval_status`:** `pending` (default on create) | `approved` | `rejected`  
Invoices appear in **Approvals** alongside emails / meetings / feedback. The linked email draft is also pending under Emails.

---

## How James uses it (dashboard)

1. Confirm an order with a PO (**Orders** → Confirm (PO acquired), or create with status Confirmed + PO).
2. Toast: *Confirmed — manufacturing + invoice draft created* (when both apply).
3. Open **Invoices** (or the invoice block on the order card):
   - **HTML / Print** — browser Print → Save as PDF.
   - **PDF** — download generated PDF (`reportlab`).
4. Open **Approvals** → approve the invoice (and optionally the invoice email).
5. On **Invoices**, set status to **Sent** after you actually email the customer from your mailbox, then **Paid** when remittance clears.

### Printing PDF

| Method | How |
|--------|-----|
| **Preferred** | Open HTML → browser **Print** → **Save as PDF** |
| **Download** | Click **PDF** or `GET /invoices/{id}/pdf` (requires `reportlab` in the API environment) |

---

## API summary

| Method | Path | Notes |
|--------|------|--------|
| `GET` | `/invoices` | List (optional `?order_id=`) |
| `GET` | `/invoices/{id}` | Detail |
| `GET` | `/invoices/{id}/html` | Printable HTML |
| `GET` | `/invoices/{id}/pdf` | PDF attachment (501 if reportlab missing) |
| `POST` | `/orders/{id}/invoice` | Manual create if missing (Confirmed required) |
| `PUT` | `/invoices/{id}/status` | `{ "status": "Draft\|Sent\|Paid\|Void" }` |
| `GET` | `/approvals` | Includes `invoices` array |

Invoice numbers look like `INV-YYYYMMDD-XXXX`. Line items come from the order product / qty / unit price. Due date = issued + 30 days.

---

## Follow-ups (not in this change)

- Stripe (or similar) checkout / payment links
- Tax calculation by jurisdiction
- Real SMTP send of the invoice email with PDF attached
- Multi-currency and partial payments
