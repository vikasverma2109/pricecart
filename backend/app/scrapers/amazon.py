"""
Amazon Fresh scraper — uses Playwright to load the full JS-rendered search page.
"""
import logging
from .base import BaseScraper, PlatformMeta
from ..browser_manager import new_page

logger = logging.getLogger(__name__)

_EXTRACT_JS = """
() => {
    const cards = document.querySelectorAll('[data-component-type="s-search-result"]');
    return Array.from(cards).slice(0, 10).map(card => {
        // Title: multiple possible selectors
        const titleEl = card.querySelector(
            'h2 span.a-text-normal, .a-size-base-plus, .a-size-medium.a-color-base'
        );
        // Price whole + fraction
        const wholeEl = card.querySelector('.a-price-whole');
        const fracEl  = card.querySelector('.a-price-fraction');
        let price = null;
        if (wholeEl) {
            const whole = parseFloat(wholeEl.textContent.replace(/[^0-9]/g, '')) || 0;
            const frac  = parseFloat('0.' + (fracEl?.textContent?.replace(/[^0-9]/g, '') || '0'));
            price = whole + frac;
        }
        const imgEl  = card.querySelector('img.s-image');
        const linkEl = card.querySelector('h2 a, a.a-link-normal');
        const href   = linkEl?.getAttribute('href') || '';

        return {
            name: titleEl?.textContent?.trim() || '',
            price: price && price > 0 ? price : null,
            image_url: imgEl?.src || null,
            product_url: href.startsWith('http') ? href : 'https://www.amazon.in' + href,
        };
    }).filter(p => p.name && p.price);
}
"""


class AmazonScraper(BaseScraper):
    PLATFORM_META = PlatformMeta(
        id="amazon",
        display="Amazon.in",
        color="#ff9900",
        logo="A",
        delivery_time="1-2 days",
    )

    async def search(self, query: str, pincode: str = "110001", **kwargs):
        page, context = await new_page()
        results = []
        try:
            # Grocery category (broad) — much more results than AmazonFresh only
            url = (
                f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
                f"&rh=n%3A976442031"
            )
            logger.info(f"[amazon] {url}")

            # Set currency cookie so prices show in INR
            await context.add_cookies([{
                "name": "i18n-prefs",
                "value": "INR",
                "domain": ".amazon.in",
                "path": "/",
            }])

            await page.goto(url, wait_until="domcontentloaded", timeout=20000)

            # Wait for search results
            try:
                await page.wait_for_selector(
                    '[data-component-type="s-search-result"]',
                    timeout=12000,
                )
            except Exception:
                # Fallback: retry without category filter
                logger.warning("[amazon] No results with category filter, retrying without")
                url2 = f"https://www.amazon.in/s?k={query.replace(' ', '+')}"
                await page.goto(url2, wait_until="domcontentloaded", timeout=20000)
                try:
                    await page.wait_for_selector(
                        '[data-component-type="s-search-result"]',
                        timeout=12000,
                    )
                except Exception:
                    logger.warning("[amazon] No results found even without filter")
                    return []

            products = await page.evaluate(_EXTRACT_JS)
            logger.info(f"[amazon] {len(products)} products")

            results = [
                self.build_result({
                    "product_name": p["name"],
                    "price": p["price"],
                    "mrp": None,
                    "unit": None,
                    "image_url": p.get("image_url"),
                    "product_url": p.get("product_url", "https://www.amazon.in"),
                    "in_stock": True,
                    "discount_pct": None,
                })
                for p in products
            ]
        except Exception as e:
            logger.warning(f"[amazon] scrape failed: {e}")
        finally:
            await context.close()
        return results
