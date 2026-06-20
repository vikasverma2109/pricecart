"""
Product matching logic.

When searching across 5 platforms, we get up to 40 products.
This module groups them into "comparable" canonical products
by fuzzy-matching product names.

Strategy:
- Normalize names (lowercase, strip units/brands noise)
- Group by similarity score (using difflib SequenceMatcher)
- Pick the best match per platform per group
"""

import re
from difflib import SequenceMatcher
from typing import List, Dict
from collections import defaultdict


def normalize(name: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace."""
    name = name.lower()
    name = re.sub(r"[^\w\s]", " ", name)
    name = re.sub(r"\s+", " ", name).strip()
    # remove common noise words that differ across platforms
    noise = ["pack", "combo", "offer", "free", "buy", "get", "set of"]
    for w in noise:
        name = name.replace(w, "")
    return name.strip()


def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, normalize(a), normalize(b)).ratio()


def group_products(all_results: List[dict], threshold: float = 0.55) -> List[List[dict]]:
    """
    Group product results into clusters of similar items.
    Returns list of groups, each group = list of platform results for same product.
    """
    groups: List[List[dict]] = []

    for item in all_results:
        name = item.get("product_name", "")
        placed = False

        for group in groups:
            # Compare to the first item (representative) in the group
            rep = group[0].get("product_name", "")
            if similarity(name, rep) >= threshold:
                group.append(item)
                placed = True
                break

        if not placed:
            groups.append([item])

    return groups


def build_compared_products(groups: List[List[dict]]) -> List[dict]:
    """
    Convert groups into ComparedProduct dicts, sorted cheapest platform first.
    """
    compared = []

    for group in groups:
        # Take the first item as canonical name/image
        canonical = group[0]

        # Deduplicate: keep only the cheapest result per platform
        platform_best: Dict[str, dict] = {}
        for item in group:
            pid = item["platform"]
            existing = platform_best.get(pid)
            item_price = item.get("price") or float("inf")
            if existing is None or item_price < (existing.get("price") or float("inf")):
                platform_best[pid] = item

        prices = list(platform_best.values())
        # Sort cheapest first
        prices.sort(key=lambda x: x.get("price") or float("inf"))

        valid_prices = [p["price"] for p in prices if p.get("price")]
        cheapest_price = min(valid_prices) if valid_prices else None
        most_exp = max(valid_prices) if valid_prices else None
        cheapest_platform = prices[0]["platform_display"] if prices else None

        compared.append({
            "canonical_name": canonical.get("product_name", ""),
            "category": None,
            "image_url": canonical.get("image_url"),
            "prices": prices,
            "cheapest_platform": cheapest_platform,
            "cheapest_price": cheapest_price,
            "most_expensive_price": most_exp,
            "savings": round(most_exp - cheapest_price, 2) if (most_exp and cheapest_price and most_exp > cheapest_price) else 0,
        })

    # Sort: groups with more platform matches first (better comparison value)
    compared.sort(key=lambda x: len(x["prices"]), reverse=True)
    return compared
