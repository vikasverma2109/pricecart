"""
Flipkart scraper — uses Playwright to handle JS rendering and login popups.
Extracts product name from URL slug (always reliable) and price from leaf elements.
"""
import logging
from .base import BaseScraper, PlatformMeta
from ..browser_manager import new_page

logger = logging.getLogger(__name__)

# Using raw string to avoid Python escape-sequence interpretation
_EXTRACT_JS = r"""
() => {
    // Flipkart product cards always link to /p/ paths
    let cards = Array.from(document.querySelectorAll('a[href*="/p/"]'))
        .map(a => {
            let el = a;
            for (let i = 0; i < 6; i++) {
                if (!el.parentElement) break;
                el = el.parentElement;
                if (el.querySelector('img') && el.querySelector('a[href*="/p/"]')) {
                    if (/[₹\d,]{3,}/.test(el.textContent)) return el;
                }
            }
            return null;
        })
        .filter(Boolean);

    // Deduplicate by DOM identity
    cards = [...new Set(cards)];

    // Deduplicate by screen position (avoid picking same card twice)
    const seen = new Set();
    cards = cards.filter(el => {
        const top = Math.round(el.getBoundingClientRect().top / 5);
        if (seen.has(top)) return false;
        seen.add(top);
        return true;
    });

    return cards.slice(0, 10).map(card => {
        // Price: lowest number found in a leaf element
        const allEls = Array.from(card.querySelectorAll('div, span'));
        let price = null;
        for (const el of allEls) {
            if (el.children.length > 0) continue;
            const t = el.textContent.trim().replace(/[,\s]/g, '');
            const m = t.match(/^[₹]?(\d{2,6})$/);
            if (m) {
                const n = parseFloat(m[1]);
                if (n > 0 && n < 500000 && (price === null || n < price)) price = n;
            }
        }

        const imgEl = card.querySelector('img');
        const linkEl = card.querySelector('a[href*="/p/"]');
        const href = linkEl?.getAttribute('href') || '';

        // Name: decode from URL slug — always accurate on Flipkart
        // URL pattern: /brand-product-description/p/itemId?params
        const slug = href.split('/p/')[0].split('/').filter(Boolean).pop() || '';
        const name = slug
            .replace(/-/g, ' ')
            .replace(/\b\w/g, l => l.toUpperCase())
            .slice(0, 120);

        return {
            name,
            price,
            image_url: imgEl?.src || null,
            product_url: href.startsWith('http') ? href : 'https://www.flipkart.com' + href,
        };
    }).filter(p => p.name && p.price && p.name.length > 3);
}
"""


class FlipkartScraper(BaseScraper):
    PLATFORM_META = PlatformMeta(
        id="flipkart",
        display="Flipkart",
        color="#2563eb",
        logo="F",
        delivery_time="1-2 days",
    )

    async def search(self, query: str, **kwargs):
        page, context = await new_page()
        results = []
        try:
            url = (
                f"https://www.flipkart.com/search?q={query.replace(' ', '+')}"
                f"&marketplace=FLIPKART&otracker=search&as-show=on"
            )
            logger.info(f"[flipkart] {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(2000)

            # Dismiss login popup
            for attempt in range(2):
                for btn_sel in [
                    '._2KpZ6l._2doB4z',
                    'button[class*="close" i]',
                    'button[class*="_2KpZ6l"]',
                    '[class*="modal"] button',
                    '[class*="Modal"] button',
                    '[role="dialog"] button',
                ]:
                    try:
                        btn = await page.query_selector(btn_sel)
                        if btn:
                            await btn.click()
                            logger.info(f"[flipkart] Dismissed popup via {btn_sel}")
                            await page.wait_for_timeout(500)
                            break
                    except Exception:
                        pass
                await page.wait_for_timeout(1000)

            # Wait for product links
            try:
                await page.wait_for_selector('a[href*="/p/"]', timeout=12000)
            except Exception:
                logger.warning("[flipkart] No product links (/p/) found on page")
                return []

            await page.wait_for_timeout(1000)

            products = await page.evaluate(_EXTRACT_JS)
            logger.info(f"[flipkart] {len(products)} products")

            results = [
                self.build_result({
                    "product_name": p["name"],
                    "price": p["price"],
                    "mrp": None,
                    "unit": None,
                    "image_url": p.get("image_url"),
                    "product_url": p.get("product_url", "https://www.flipkart.com"),
                    "in_stock": True,
                    "discount_pct": None,
                })
                for p in products
            ]
        except Exception as e:
            logger.warning(f"[flipkart] scrape failed: {e}")
        finally:
            await context.close()
        return results
