"""
Zepto scraper — uses Playwright browser with geolocation to bypass location gate.
Uses ₹-anchored extraction (no <img> dependency).
"""
import logging
from typing import List
from .base import BaseScraper, PlatformMeta
from ..browser_manager import new_page

logger = logging.getLogger(__name__)

_EXTRACT_JS = r"""
() => {
    // Anchor on ₹ price leaf elements — works regardless of CSS class names
    const priceEls = Array.from(document.querySelectorAll('*')).filter(el =>
        el.children.length === 0 && /₹\d/.test(el.textContent.trim())
    );

    const results = [];
    const seenCards = new Set();

    for (const priceEl of priceEls) {
        const m = priceEl.textContent.trim().match(/₹(\d+(?:\.\d+)?)/);
        if (!m) continue;
        const price = parseFloat(m[1]);
        if (price < 1 || price > 50000) continue;

        // Walk up to card-sized container
        let card = priceEl.parentElement;
        for (let i = 0; i < 8; i++) {
            if (!card || !card.parentElement) break;
            card = card.parentElement;
            const len = (card.textContent || '').trim().length;
            if (len > 15 && len < 900) break;
        }
        if (!card || seenCards.has(card)) continue;
        seenCards.add(card);

        const leaves = Array.from(card.querySelectorAll('*')).filter(el =>
            el.children.length === 0 && el.textContent.trim().length > 3
        );

        let name = '';
        const skip = ['ADD', 'Buy', 'Cart', 'OFF', 'Sold'];
        for (const el of leaves) {
            const t = el.textContent.trim();
            if (/^[₹\d\s,\.%gkmlLpcsMINSOADT+\-]+$/.test(t)) continue;
            if (skip.some(w => t === w)) continue;
            if (t.length < 5 || t.length > 200) continue;
            if (t.length > name.length) name = t;
        }

        const linkEl = card.querySelector('a');
        const href = linkEl?.getAttribute('href') || '';

        if (name && price) {
            results.push({
                name,
                price,
                image_url: null,
                product_url: href.startsWith('http') ? href : 'https://www.zepto.com' + href,
            });
        }
    }

    return results.slice(0, 15);
}
"""


class ZeptoScraper(BaseScraper):
    PLATFORM_META = PlatformMeta(
        id="zepto",
        display="Zepto",
        color="#8b5cf6",
        logo="Z",
        delivery_time="10 mins",
    )

    async def search(self, query: str, lat: str = "28.6315", lon: str = "77.2167", **kwargs) -> List[dict]:
        page, context = await new_page(float(lat or 28.6315), float(lon or 77.2167))
        results = []
        try:
            url = f"https://www.zepto.com/search?q={query.replace(' ', '+')}"
            logger.info(f"[zepto] {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(3000)

            content = await page.content()
            if '₹' not in content:
                logger.warning("[zepto] No price content — possibly location gate")
                return []

            # Scroll to trigger lazy-loaded products
            for _ in range(3):
                await page.evaluate("window.scrollBy(0, 800)")
                await page.wait_for_timeout(500)
            await page.evaluate("window.scrollTo(0, 0)")
            await page.wait_for_timeout(500)

            products = await page.evaluate(_EXTRACT_JS)
            logger.info(f"[zepto] {len(products)} products")

            results = [
                self.build_result({
                    "product_name": p["name"],
                    "price": p["price"],
                    "mrp": None,
                    "unit": None,
                    "image_url": None,
                    "product_url": p.get("product_url", "https://www.zepto.com"),
                    "in_stock": True,
                    "discount_pct": None,
                })
                for p in products
            ]
        except Exception as e:
            logger.warning(f"[zepto] scrape failed: {e}")
        finally:
            await context.close()
        return results
