"""LC-Flow SKU → Xometry process / material mapping."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

# sku → (process, xometry_material)
SKU_PROCESS_MATERIAL: Dict[str, Tuple[str, str]] = {
    "LCP061000": ("FDM", "PC-ISO"),
    "LCSS61000": ("DMLS", "Stainless Steel 316/L"),
    "LCA061000": ("DMLS", "Aluminum AlSi10Mg"),
}

LC_FLOW_SKUS = set(SKU_PROCESS_MATERIAL.keys())


def resolve_sku_from_product(product: str) -> Optional[str]:
    """Return SKU if product string is or contains a known LC-Flow SKU."""
    if not product:
        return None
    p = product.strip()
    if p in SKU_PROCESS_MATERIAL:
        return p
    upper = p.upper()
    for sku in SKU_PROCESS_MATERIAL:
        if sku.upper() in upper:
            return sku
    # Also match by common product name fragments
    lowered = p.lower()
    if "pc-iso" in lowered or "plastic" in lowered and "lc-flow" in lowered:
        return "LCP061000"
    if "316" in lowered or "stainless" in lowered:
        if "lc-flow" in lowered or "lcss" in lowered:
            return "LCSS61000"
    if "alsi" in lowered or "aluminum" in lowered or "aluminium" in lowered:
        if "lc-flow" in lowered or "lca" in lowered:
            return "LCA061000"
    return None


def map_sku(sku: Optional[str]) -> Tuple[str, str, str]:
    """
    Return (sku_or_unknown, process, material).
    Unknown SKUs → process=unknown, material from sku or 'unknown'.
    """
    if not sku:
        return ("unknown", "unknown", "unknown")
    if sku in SKU_PROCESS_MATERIAL:
        process, material = SKU_PROCESS_MATERIAL[sku]
        return (sku, process, material)
    return (sku, "unknown", "unknown")
