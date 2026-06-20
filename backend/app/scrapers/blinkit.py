"""
Blinkit scraper — uses Playwright real browser.
Blinkit is a React SPA. We inject geolocation + set localStorage to bypass the
location gate, then extract products anchored on ₹ price leaf elements.
"""
import logging
import re
from .base import BaseScraper, PlatformMeta
from ..browser_manager import new_page

logger = logging.getLogger(__name__)

# Strip trailing unit appended without space, e.g. "Britannia Biscuit152 g" → "Britannia Biscuit"
_UNIT_SUFFIX = re.compile(
    r'\d+\.?\d*\s*(g|gm|gram|grams|kg|kgs|ml|l|ltr|liter|litre|litres|pcs?|pieces?|nos?|pack)s?$',
    re.IGNORECASE
)

_EXTRACT_JS = r"""
() => {
    const RUPEE = '₹';

    // All leaf elements whose text starts with ₹ (actual price elements)
    const priceEls = Array.from(document.querySelectorAll('*')).filter(el =>
        el.children.length === 0 &&
        el.textContent.trim().startsWith(RUPEE) &&
        el.tagName !== 'SCRIPT' &&
        el.tagName !== 'STYLE'
    );

    const results = [];
    const seenCards = new Set();

    for (const priceEl of priceEls) {
        const priceText = priceEl.textContent.trim();
        const m = priceText.match(/₹(\d+(?:\.\d+)?)/);
        if (!m) continue;
        const price = parseFloat(m[1]);
        if (price < 5 || price > 50000) continue;

        // Walk up to find a card container (total text 30-800 chars)
        let card = priceEl.parentElement;
        for (let i = 0; i < 10; i++) {
            if (!card || !card.parentElement) break;
            card = card.parentElement;
            const len = (card.textContent || '').trim().length;
            if (len >= 30 && len <= 800) break;
        }
        if (!card || seenCards.has(card)) continue;
        seenCards.add(card);

        const allLeaves = Array.from(card.querySelectorAll('*')).filter(el =>
            el.children.length === 0 && el.textContent.trim().length > 0 &&
            el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE'
        );

        // Product name: longest text that isn't a price/button/unit
        let name = '';
        let unit = null;
        for (const el of allLeaves) {
            const t = el.textContent.trim();
            if (!t || t.length < 3) continue;
            if (/^[₹\d\s,\.\-\+\%]+$/.test(t)) continue;
            if (/^(ADD|MINS?|OUT OF STOCK|SOLD OUT|BUY|CART|FREE|OFFER|OFF|SAVE|MRP|EACH)$/i.test(t)) continue;
            // Try to capture unit (e.g. "500 g", "1 kg", "250ml", "6 pcs")
            if (!unit && /^\d+\.?\d*\s*(g|gm|gram|grams|kg|kgs|ml|l|ltr|liter|litre|litres|pcs?|pieces?|nos?|pack)s?\b/i.test(t)) {
                unit = t;
                continue;
            }
            if (t.length > name.length && t.length < 200) name = t;
        }

        // Strip trailing unit that was concatenated without space (e.g. "Britannia Biscuit152 g")
        name = name.replace(/\d+\.?\d*\s*(g|gm|gram|grams|kg|kgs|ml|l|ltr|liter|litre|litres|pcs?|pieces?|nos?|pack)s?(\s*[xX×]\s*\d+\.?\d*\s*\w+)?$/i, '').trim();

        // Also try to extract unit from the name itself (e.g. "Amul Butter 500g")
        if (!unit && name) {
            const um = name.match(/(\d+\.?\d*\s*(?:g|gm|gram|grams|kg|kgs|ml|l|ltr|liter|litre|litres|pcs?|pieces?|nos?|pack)s?)\b/i);
            if (um) unit = um[0];
        }

        // MRP: look for a second price or strikethrough price
        let mrp = null;
        const allPrices = allLeaves
            .map(el => el.textContent.trim())
            .filter(t => /^₹\d+/.test(t))
            .map(t => parseFloat(t.replace('₹', '')))
            .filter(p => p >= 5 && p <= 50000);
        if (allPrices.length > 1) {
            const higher = allPrices.filter(p => p > price);
            if (higher.length > 0) mrp = Math.min(...higher);
        }

        // Image: try background-image on card descendants or <img>
        let image_url = null;
        const img = card.querySelector('img[src]');
        if (img) image_url = img.src;

        if (name && price) {
            results.push({
                name,
                price,
                mrp,
                unit,
                image_url,
                product_url: 'https://blinkit.com/s/?q=' + encodeURIComponent(name),
            });
        }
    }

    return results.slice(0, 12);
}
"""

# Set localStorage keys Blinkit uses to bypass location gate
_SET_LOCATION_JS = """
(lat, lon) => {
    try {
        // Blinkit stores location in various localStorage keys
        const loc = JSON.stringify({ lat: lat, lng: lon });
        localStorage.setItem('userLat', String(lat));
        localStorage.setItem('userLng', String(lon));
        localStorage.setItem('user-lat', String(lat));
        localStorage.setItem('user-lng', String(lon));
        localStorage.setItem('blinkit_lat', String(lat));
        localStorage.setItem('blinkit_lng', String(lon));
        localStorage.setItem('gr_1_city', JSON.stringify({lat, lng: lon}));
    } catch(e) {}
}
"""


class BlinkitScraper(BaseScraper):
    PLATFORM_META = PlatformMeta(
        id="blinkit",
        display="Blinkit",
        color="#f8c200",
        logo="B",
        delivery_time="10 mins",
    )
    # Homepage + search = ~2 pages. Must fit inside the 25s global API cap.
    SEARCH_TIMEOUT = 23.0

    async def search(self, query: str, lat: str = "28.6315", lon: str = "77.2167", **kwargs):
        lat_f = float(lat or 28.6315)
        lon_f = float(lon or 77.2167)
        import json as _json

        page, context = await new_page(lat_f, lon_f)
        results = []
        try:
            # Pre-populate localStorage via init script so it's available from
            # the very first JS tick — this lets us skip the homepage and go
            # straight to the search URL (saves ~7s).
            lat_s = str(lat_f)
            lon_s = str(lon_f)
            await page.add_init_script(f"""
                (() => {{
                    try {{
                        localStorage.setItem('userLat', '{lat_s}');
                        localStorage.setItem('userLng', '{lon_s}');
                        localStorage.setItem('user-lat', '{lat_s}');
                        localStorage.setItem('user-lng', '{lon_s}');
                        localStorage.setItem('blinkit_lat', '{lat_s}');
                        localStorage.setItem('blinkit_lng', '{lon_s}');
                        localStorage.setItem('gr_1_city', JSON.stringify({{lat:{lat_f},lng:{lon_f}}}));
                    }} catch(e) {{}}
                }})();
            """)

            # Set location cookies (use actual pincode, not hardcoded 110001)
            pincode = str(kwargs.get("pincode") or "110001")
            await context.add_cookies([
                {"name": "gr_1", "value": _json.dumps({"lat": lat_f, "lng": lon_f}),
                 "domain": ".blinkit.com", "path": "/"},
                {"name": "pincode", "value": pincode,
                 "domain": ".blinkit.com", "path": "/"},
            ])

            # Visit homepage first — Blinkit sets up session/store here.
            # Without this, the search page shows a location gate (no ₹).
            logger.info("[blinkit] Loading homepage for session setup...")
            await page.goto("https://blinkit.com/", wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(2000)
            await page.evaluate(_SET_LOCATION_JS, lat_f, lon_f)

            # Now go to search URL
            url = f"https://blinkit.com/s/?q={query.replace(' ', '+')}"
            logger.info(f"[blinkit] Searching: {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=15000)
            await page.wait_for_timeout(4000)

            # Re-inject location in case page navigation cleared localStorage
            await page.evaluate(_SET_LOCATION_JS, lat_f, lon_f)
            await page.wait_for_timeout(500)

            content = await page.content()
            if '₹' not in content:
                logger.warning("[blinkit] No ₹ found after first load — reloading once")
                await page.reload(wait_until="domcontentloaded", timeout=10000)
                await page.wait_for_timeout(3000)
                await page.evaluate(_SET_LOCATION_JS, lat_f, lon_f)
                content = await page.content()

            if '₹' not in content:
                logger.warning("[blinkit] Still no ₹ — location gate blocking")
                return []

            products = await page.evaluate(_EXTRACT_JS)
            # Strip trailing units concatenated without space ("Biscuit152 g" → "Biscuit")
            for p in products:
                p["name"] = _UNIT_SUFFIX.sub('', p["name"]).strip()
            logger.info(f"[blinkit] Extracted {len(products)} products")

            results = [
                self.build_result({
                    "product_name": p["name"],
                    "price": p["price"],
                    "mrp": p.get("mrp"),
                    "unit": p.get("unit"),
                    "image_url": p.get("image_url"),
                    "product_url": p.get("product_url", "https://blinkit.com"),
                    "in_stock": True,
                })
                for p in products
            ]
        except Exception as e:
            logger.warning(f"[blinkit] scrape failed: {e}")
        finally:
            await context.close()
        return results
