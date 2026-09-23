"""Xometry API client stub — no auto-charging buyer placement."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional


class XometryClientError(Exception):
    """Raised when buyer API is unavailable or intentionally blocked."""


class XometryClient:
    """
    Stub for a future buyer Instant Quote / PunchOut path.

    The public developer.xometry.com surface is WorkCenter *partner* (shop) API,
    not a buyer place-order API. This client never charges or places paid orders.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
    ):
        self.api_key = api_key if api_key is not None else os.getenv("XOMETRY_API_KEY", "")
        self.api_base = (
            api_base
            if api_base is not None
            else os.getenv("XOMETRY_API_BASE", "https://api.developer.xometry.com")
        ).rstrip("/")

    @property
    def configured(self) -> bool:
        return bool(self.api_key)

    def place_order(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Intentionally does not call any live endpoint that could charge money.
        """
        if not self.configured:
            raise XometryClientError(
                "buyer API not configured — use mock or manual"
            )
        raise XometryClientError(
            "Xometry buyer Instant Quote / place-order API is not available for "
            "auto-submit. Place the order manually on xometry.com (or PunchOut), "
            "then mark the job submitted via approve-xometry. "
            f"(Partner base {self.api_base} is WorkCenter-oriented; payload keys: "
            f"{sorted(payload.keys())})"
        )

    def get_job_status(self, external_job_id: str) -> Dict[str, Any]:
        if not self.configured:
            raise XometryClientError(
                "buyer API not configured — use mock or manual"
            )
        raise XometryClientError(
            f"Live Xometry status pull not implemented for job {external_job_id}; "
            "update status manually or use mock mode."
        )
