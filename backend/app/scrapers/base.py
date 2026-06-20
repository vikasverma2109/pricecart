"""
Base scraper class. All platform scrapers inherit from this.

To add a new platform:
1. Create a new file in scrapers/ (e.g., myntra.py)
2. Subclass BaseScraper
3. Implement `search()` and `PLATFORM_META`
4. Register it in scrapers/__init__.py
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Tuple
import re
import httpx
import asyncio
import logging

logger = logging.getLogger(__name__)


class PlatformMeta:
    def __init__(self, id: str, display: str, color: str, logo: str, delivery_time: str):
        self.id = id
        self.display = display
        self.color = color
        self.logo = logo
        self.delivery_time = delivery_time


class BaseScraper(ABC):
    PLATFORM_META: PlatformMeta  # must be set by subclass

    # Override in subclass to use a real session with cookies/headers
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Linux; Android 11; Pixel 5) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/90.0.4430.91 Mobile Safari/537.36"
        ),
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-IN,en;q=0.9",
    }

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.client = httpx.AsyncClient(
            headers=self.DEFAULT_HEADERS,
            timeout=timeout,
            follow_redirects=True,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.client.aclose()

    @abstractmethod
    async def search(self, query: str, pincode: str = "110001") -> List[dict]:
        """
        Search for products and return a list of raw product dicts.
        Each dict must have at least:
            product_name, price, unit
        Optional: mrp, image_url, product_url, in_stock
        """
        ...

    @staticmethod
    def parse_unit_price(price: float, unit_str: Optional[str]) -> Tuple[Optional[float], Optional[str]]:
        """
        Compute per-unit price from a quantity string like "500g", "1L", "6 pcs".
        Returns (price_per_unit, label) e.g. (57.0, "/100g") or (None, None).
        """
        if not price or not unit_str:
            return None, None
        s = unit_str.strip().lower()
        m = re.search(r'(\d+(?:\.\d+)?)\s*(g|gm|gram|grams|kg|kgs|ml|l|ltr|litre|litres|liter|liters|pcs?|pieces?|nos?|pack|packs?)\b', s)
        if not m:
            return None, None
        qty = float(m.group(1))
        utype = m.group(2)
        if qty == 0:
            return None, None
        if utype in ('g', 'gm', 'gram', 'grams'):
            return round(price / qty * 100, 1), "/100g"
        if utype in ('kg', 'kgs'):
            return round(price / (qty * 1000) * 100, 1), "/100g"
        if utype == 'ml':
            return round(price / qty * 100, 1), "/100ml"
        if utype in ('l', 'ltr', 'litre', 'litres', 'liter', 'liters'):
            return round(price / (qty * 1000) * 100, 1), "/100ml"
        if utype in ('pc', 'pcs', 'piece', 'pieces', 'no', 'nos', 'pack', 'packs'):
            return round(price / qty, 1), "/pc"
        return None, None

    def build_result(self, raw: dict) -> dict:
        """Attach platform metadata to a raw product dict."""
        meta = self.PLATFORM_META
        price = raw.get("price")
        mrp = raw.get("mrp")
        unit = raw.get("unit")
        discount = None
        if price and mrp and mrp > price:
            discount = round((mrp - price) / mrp * 100, 1)
        ppu, ppu_label = self.parse_unit_price(price, unit)

        return {
            "platform": meta.id,
            "platform_display": meta.display,
            "platform_color": meta.color,
            "platform_logo": meta.logo,
            "product_name": raw.get("product_name", "Unknown"),
            "price": price,
            "mrp": mrp,
            "unit": unit,
            "price_per_unit": ppu,
            "price_per_unit_label": ppu_label,
            "image_url": raw.get("image_url"),
            "product_url": raw.get("product_url"),
            "in_stock": raw.get("in_stock", True),
            "delivery_time": meta.delivery_time,
            "discount_pct": discount,
        }

    async def safe_search(self, query: str, pincode: str = "110001",
                          lat: str = None, lon: str = None, **kwargs) -> List[dict]:
        """Wraps search() with a 20s hard cap so one slow scraper never blocks all others."""
        try:
            raw_results = await asyncio.wait_for(
                self.search(query, pincode=pincode, lat=lat, lon=lon, **kwargs),
                timeout=20.0,
            )
            return [self.build_result(r) for r in raw_results]
        except asyncio.TimeoutError:
            logger.warning(f"[{self.PLATFORM_META.id}] timed out after 20s")
            return []
        except Exception as e:
            logger.warning(f"[{self.PLATFORM_META.id}] scrape failed: {e}")
            return []
