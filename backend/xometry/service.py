"""Manufacturing job service: PO-acquired hook, human gate, mock advance."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from .client import XometryClient, XometryClientError
from .sku_map import map_sku, resolve_sku_from_product

JOB_STATUSES = [
    "queued",
    "awaiting_human",
    "submitted",
    "in_production",
    "shipped",
    "delivered",
    "cancelled",
    "error",
]

ACTIVE_STATUSES = {
    "queued",
    "awaiting_human",
    "submitted",
    "in_production",
    "shipped",
}

# manufacturing job status → order status mirror
JOB_TO_ORDER_STATUS = {
    "in_production": "In Production",
    "shipped": "Shipped",
    "delivered": "Delivered",
    "cancelled": "Cancelled",
}

MOCK_ADVANCE_SEQ = [
    "queued",
    "submitted",
    "in_production",
    "shipped",
    "delivered",
]


def _mode() -> str:
    raw = (os.getenv("XOMETRY_MODE") or "mock").strip().lower()
    if raw not in ("mock", "manual", "api"):
        return "mock"
    return raw


def _mock_lead_days() -> int:
    try:
        return int(os.getenv("XOMETRY_MOCK_LEAD_DAYS", "10"))
    except ValueError:
        return 10


def _default_ship_to() -> Dict[str, Any]:
    raw = os.getenv("XOMETRY_SHIP_TO_JSON", "").strip()
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw": raw, "note": "invalid XOMETRY_SHIP_TO_JSON; fix env"}
    return {
        "name": "PTC Inc / Industrial and Molecular Solutions",
        "attention": "Receiving",
        "line1": "TBD — set XOMETRY_SHIP_TO_JSON",
        "city": "",
        "state": "",
        "postal_code": "",
        "country": "US",
    }


def _cad_dir() -> str:
    return os.getenv("XOMETRY_CAD_DIR", "").strip() or "(set XOMETRY_CAD_DIR)"


def xometry_config_summary() -> Dict[str, Any]:
    client = XometryClient()
    return {
        "xometry_mode": _mode(),
        "api_configured": client.configured,
        "api_base": client.api_base,
        "mock_lead_days": _mock_lead_days(),
        "cad_dir_set": bool(os.getenv("XOMETRY_CAD_DIR", "").strip()),
        "ship_to_env_set": bool(os.getenv("XOMETRY_SHIP_TO_JSON", "").strip()),
    }


def _now() -> str:
    return datetime.utcnow().isoformat()


def _eta_iso(days: Optional[int] = None) -> str:
    d = days if days is not None else _mock_lead_days()
    return (datetime.utcnow() + timedelta(days=d)).date().isoformat()


def _build_checklist(
    *,
    sku: str,
    process: str,
    material: str,
    quantity_packs: float,
    po_number: Optional[str],
    order_id: str,
) -> Dict[str, Any]:
    cad_hint = f"{_cad_dir().rstrip('/')}/{sku}.step" if sku != "unknown" else _cad_dir()
    return {
        "title": "Xometry RFQ checklist (manual handoff)",
        "steps": [
            "Confirm NDA signed and counsel OK to share CAD with Xometry network",
            f"Open https://www.xometry.com Instant Quote (or sales RFQ)",
            f"Upload CAD: {cad_hint}",
            f"Select process: {process}",
            f"Select material: {material}",
            f"Quantity: {quantity_packs} pack(s) of 2 valves (confirm units with engineering)",
            f"Reference PO: {po_number or '(none provided)'}",
            f"Internal order_id: {order_id}",
            "Set ship-to from checklist ship_to / XOMETRY_SHIP_TO_JSON",
            "Do NOT auto-charge from Closing Agent — place order on xometry.com after quote review",
            "After placing: click Approve Xometry handoff in Closing Agent UI",
        ],
        "sku": sku,
        "process": process,
        "material": material,
        "quantity_packs": quantity_packs,
        "cad_path_hint": cad_hint,
        "xometry_web": "https://www.xometry.com",
        "note": "Real placement remains on Xometry web until PunchOut/buyer API exists.",
    }


def ensure_schema(conn) -> None:
    """Create manufacturing_jobs + ensure orders.po_number (idempotent)."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS manufacturing_jobs (
            id TEXT PRIMARY KEY,
            order_id TEXT NOT NULL,
            mode TEXT NOT NULL,
            status TEXT NOT NULL,
            sku TEXT,
            quantity_packs REAL,
            process TEXT,
            material TEXT,
            po_number TEXT,
            xometry_job_id TEXT,
            xometry_quote_ref TEXT,
            tracking_number TEXT,
            ship_to_json TEXT,
            checklist_json TEXT,
            notes TEXT,
            error_message TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            eta_ship_date TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
        """
    )
    try:
        conn.execute("ALTER TABLE orders ADD COLUMN po_number TEXT")
    except Exception:
        pass


def _row_to_job(row) -> Dict[str, Any]:
    d = dict(row)
    for key in ("ship_to_json", "checklist_json"):
        raw = d.get(key)
        if raw:
            try:
                d[key.replace("_json", "")] = json.loads(raw)
            except (TypeError, json.JSONDecodeError):
                d[key.replace("_json", "")] = raw
        else:
            d[key.replace("_json", "")] = None
    return d


def _find_active_job(conn, order_id: str) -> Optional[Dict[str, Any]]:
    placeholders = ",".join("?" * len(ACTIVE_STATUSES))
    row = conn.execute(
        f"""SELECT * FROM manufacturing_jobs
            WHERE order_id=? AND status IN ({placeholders})
            ORDER BY created_at DESC LIMIT 1""",
        (order_id, *ACTIVE_STATUSES),
    ).fetchone()
    return _row_to_job(row) if row else None


def on_po_acquired(
    conn,
    order_id: str,
    *,
    po_number: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a manufacturing_jobs row for a Confirmed order (idempotent).
    Does not place a paid Xometry order.
    """
    ensure_schema(conn)
    existing = _find_active_job(conn, order_id)
    if existing:
        return {"job": existing, "created": False, "message": "Active manufacturing job already exists"}

    order = conn.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
    if not order:
        raise ValueError(f"Order not found: {order_id}")
    order = dict(order)

    if po_number is not None:
        conn.execute(
            "UPDATE orders SET po_number=?, updated_at=? WHERE id=?",
            (po_number, _now(), order_id),
        )
        order["po_number"] = po_number
    else:
        po_number = order.get("po_number")

    product = order.get("product") or ""
    resolved = resolve_sku_from_product(product)
    if resolved:
        sku, process, material = map_sku(resolved)
    else:
        # Treat bare product string as SKU when possible; else unknown
        sku, process, material = map_sku(product.strip() or None)

    qty = float(order.get("quantity_tons") or 0)
    # LC-Flow SKUs: quantity_tons field holds packs
    quantity_packs = qty

    mode = _mode()
    ship_to = _default_ship_to()
    checklist = _build_checklist(
        sku=sku,
        process=process,
        material=material,
        quantity_packs=quantity_packs,
        po_number=po_number,
        order_id=order_id,
    )
    notes_parts: List[str] = []
    if process == "unknown":
        notes_parts.append(f"Unknown SKU/product '{product}' — set process/material manually on Xometry.")

    now = _now()
    job_id = str(uuid.uuid4())
    status = "queued"
    xometry_job_id = None
    xometry_quote_ref = None
    eta = None
    error_message = None

    if mode == "mock":
        status = "queued"
        xometry_job_id = f"MOCK-JOB-{job_id[:8].upper()}"
        xometry_quote_ref = f"MOCK-Q-{job_id[9:13].upper() if len(job_id) > 13 else job_id[:4].upper()}"
        eta = _eta_iso()
        notes_parts.append(
            f"Mock mode: fake quote/job IDs generated; ETA ~{_mock_lead_days()} days. "
            "Use approve-xometry then mock-advance for demos."
        )
    elif mode == "manual":
        status = "awaiting_human"
        eta = None
        notes_parts.append(
            "Manual mode: complete RFQ checklist on xometry.com, then Approve Xometry handoff. "
            "Closing Agent will not place a paid order."
        )
    else:  # api
        client = XometryClient()
        if not client.configured:
            status = "error"
            error_message = "buyer API not configured — use mock or manual"
            notes_parts.append(error_message)
        else:
            # Key present but we still never auto-charge
            status = "awaiting_human"
            notes_parts.append(
                "API mode: key present but auto-charge is disabled. "
                "Human must approve; real placement still requires PunchOut/web until buyer API exists."
            )

    notes = " ".join(notes_parts)
    conn.execute(
        """INSERT INTO manufacturing_jobs
           (id, order_id, mode, status, sku, quantity_packs, process, material,
            po_number, xometry_job_id, xometry_quote_ref, tracking_number,
            ship_to_json, checklist_json, notes, error_message,
            created_at, updated_at, eta_ship_date)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            job_id,
            order_id,
            mode,
            status,
            sku,
            quantity_packs,
            process,
            material,
            po_number,
            xometry_job_id,
            xometry_quote_ref,
            None,
            json.dumps(ship_to),
            json.dumps(checklist),
            notes,
            error_message,
            now,
            now,
            eta,
        ),
    )
    row = conn.execute("SELECT * FROM manufacturing_jobs WHERE id=?", (job_id,)).fetchone()
    return {"job": _row_to_job(row), "created": True, "message": f"Manufacturing job created (mode={mode})"}


def list_jobs(conn, order_id: Optional[str] = None) -> List[Dict[str, Any]]:
    ensure_schema(conn)
    if order_id:
        rows = conn.execute(
            "SELECT * FROM manufacturing_jobs WHERE order_id=? ORDER BY created_at DESC",
            (order_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM manufacturing_jobs ORDER BY created_at DESC"
        ).fetchall()
    return [_row_to_job(r) for r in rows]


def get_job(conn, job_id: str) -> Optional[Dict[str, Any]]:
    ensure_schema(conn)
    row = conn.execute("SELECT * FROM manufacturing_jobs WHERE id=?", (job_id,)).fetchone()
    return _row_to_job(row) if row else None


def get_job_for_order(conn, order_id: str) -> Optional[Dict[str, Any]]:
    ensure_schema(conn)
    row = conn.execute(
        "SELECT * FROM manufacturing_jobs WHERE order_id=? ORDER BY created_at DESC LIMIT 1",
        (order_id,),
    ).fetchone()
    return _row_to_job(row) if row else None


def _mirror_order_status(conn, order_id: str, job_status: str) -> Optional[str]:
    order_status = JOB_TO_ORDER_STATUS.get(job_status)
    if not order_status:
        return None
    conn.execute(
        "UPDATE orders SET status=?, updated_at=? WHERE id=?",
        (order_status, _now(), order_id),
    )
    return order_status


def approve_xometry_job(conn, job_id: str) -> Dict[str, Any]:
    """
    Human gate: move mock/manual (or api-awaiting) job to submitted.
    Never places a paid Xometry order automatically.
    """
    job = get_job(conn, job_id)
    if not job:
        raise KeyError("Manufacturing job not found")

    if job["status"] in ("cancelled", "delivered", "error"):
        raise ValueError(f"Cannot approve job in status={job['status']}")

    if job["status"] in ("submitted", "in_production", "shipped"):
        return {
            "job": job,
            "message": f"Job already past handoff (status={job['status']})",
            "order_status": None,
        }

    # queued (mock) or awaiting_human (manual/api)
    if job["status"] not in ("queued", "awaiting_human"):
        raise ValueError(f"Unexpected status for approve: {job['status']}")

    now = _now()
    extra_note = (
        " Human approved Xometry handoff. "
        "Real placement remains on xometry.com in manual mode until PunchOut/API exists. "
        "No auto-charge from Closing Agent."
    )
    notes = (job.get("notes") or "") + extra_note

    # Ensure mock IDs exist
    xjid = job.get("xometry_job_id")
    xq = job.get("xometry_quote_ref")
    if job.get("mode") == "mock" and not xjid:
        xjid = f"MOCK-JOB-{job_id[:8].upper()}"
        xq = xq or f"MOCK-Q-{job_id[9:13].upper()}"

    if job.get("mode") == "api":
        # Still do not call place_order — document only
        notes += " API mode approve: recorded as submitted without calling buyer charge API."

    conn.execute(
        """UPDATE manufacturing_jobs
           SET status=?, xometry_job_id=?, xometry_quote_ref=?, notes=?, updated_at=?
           WHERE id=?""",
        ("submitted", xjid, xq, notes, now, job_id),
    )
    updated = get_job(conn, job_id)
    return {
        "job": updated,
        "message": (
            "Handoff approved → submitted. "
            "In manual mode, confirm the order was placed on xometry.com. "
            "Never auto-submits paid orders."
        ),
        "order_status": None,
    }


def update_job_status(
    conn,
    job_id: str,
    status: str,
    *,
    tracking_number: Optional[str] = None,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    if status not in JOB_STATUSES:
        raise ValueError(f"Invalid job status. Choose from: {JOB_STATUSES}")
    job = get_job(conn, job_id)
    if not job:
        raise KeyError("Manufacturing job not found")

    now = _now()
    new_tracking = tracking_number if tracking_number is not None else job.get("tracking_number")
    new_notes = notes if notes is not None else job.get("notes")
    conn.execute(
        """UPDATE manufacturing_jobs
           SET status=?, tracking_number=?, notes=?, updated_at=?
           WHERE id=?""",
        (status, new_tracking, new_notes, now, job_id),
    )
    order_status = _mirror_order_status(conn, job["order_id"], status)
    updated = get_job(conn, job_id)
    return {"job": updated, "order_status": order_status, "message": "Job status updated"}


def mock_advance_job(conn, job_id: str) -> Dict[str, Any]:
    job = get_job(conn, job_id)
    if not job:
        raise KeyError("Manufacturing job not found")
    if job.get("mode") != "mock":
        raise ValueError("mock-advance is only available when job mode=mock")
    if job["status"] in ("cancelled", "error", "delivered"):
        raise ValueError(f"Cannot advance job in status={job['status']}")

    # If still queued/awaiting_human, require approve first for clarity
    if job["status"] in ("queued", "awaiting_human"):
        raise ValueError(
            "Approve Xometry handoff first (POST .../approve-xometry), then mock-advance"
        )

    try:
        idx = MOCK_ADVANCE_SEQ.index(job["status"])
    except ValueError:
        raise ValueError(f"Cannot mock-advance from status={job['status']}")

    if idx >= len(MOCK_ADVANCE_SEQ) - 1:
        raise ValueError("Job already at final mock stage (delivered)")

    next_status = MOCK_ADVANCE_SEQ[idx + 1]
    tracking = job.get("tracking_number")
    notes = job.get("notes") or ""
    if next_status == "shipped" and not tracking:
        tracking = f"MOCK-TRACK-{job_id[:8].upper()}"
        notes = notes + f" Mock tracking assigned: {tracking}."
    if next_status == "in_production":
        notes = notes + " Mock: entered production."
    if next_status == "delivered":
        notes = notes + " Mock: delivered."

    return update_job_status(
        conn,
        job_id,
        next_status,
        tracking_number=tracking,
        notes=notes,
    )
