"""
BigBasket scraper — Playwright browser with persistent location state.

First run: sets Delhi (Connaught Place) location and saves cookies to bigbasket_state.json.
Subsequent runs: loads saved state → products load immediately without a location gate.
"""
import os
import logging
from typing import List
from .base import BaseScraper, PlatformMeta

logger = logging.getLogger(__name__)

# Storage state saved here (2 levels up from scrapers/ → backend/)
_STATE_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), "..", "..", "bigbasket_state.json")
)

_EXTRACT_JS = r"""
() => {
    // Primary: BigBasket uses SKUDeck class for product cards
    let cards = Array.from(document.querySelectorAll('[class*="SKUDeck"]'));

    // Fallback: ₹-anchored card detection
    if (cards.length < 2) {
        const priceEls = Array.from(document.querySelectorAll('*')).filter(el =>
            el.children.length === 0 && /₹\d/.test(el.textContent.trim())
        );
        const seenCards = new Set();
        const fallback = [];
        for (const priceEl of priceEls) {
            let card = priceEl.parentElement;
            for (let i = 0; i < 8; i++) {
                if (!card || !card.parentElement) break;
                card = card.parentElement;
                const len = (card.textContent || '').trim().length;
                if (len > 20 && len < 600) break;
            }
            if (card && !seenCards.has(card)) {
                seenCards.add(card);
                fallback.push(card);
            }
        }
        if (fallback.length >= 2) cards = fallback;
    }

    const skipWords = ['ADD', 'MINS', 'OFF', 'Ratings', 'Sasta', 'Sale', 'New', 'Free', 'Delivery'];

    return cards.slice(0, 15).map(card => {
        // Price
        const priceEl = Array.from(card.querySelectorAll('span, div')).find(el =>
            el.children.length === 0 && /₹(\d+)/.test(el.textContent.trim())
        );
        const priceMatch = priceEl?.textContent.trim().match(/₹(\d+(?:\.\d+)?)/);
        const price = priceMatch ? parseFloat(priceMatch[1]) : null;

        // Name: longest non-promo leaf text
        const leaves = Array.from(card.querySelectorAll('span, div, p, h3, h2'))
            .filter(el => el.children.length === 0 && el.textContent.trim().length > 4);

        let name = '';
        for (const el of leaves) {
            const t = el.textContent.trim();
            if (/^[₹\d\s,\.%gkmlLpcsMINSOADT+\-]+$/.test(t)) continue;
            if (skipWords.some(w => t.includes(w))) continue;
            if (t.length < 5 || t.length > 200) continue;
            if (t.length > name.length) name = t;
        }

        const linkEl = card.querySelector('a');
        const href = linkEl?.getAttribute('href') || '';

        return {
            name,
            price,
            image_url: null,
            product_url: href.startsWith('http') ? href : 'https://www.bigbasket.com' + href,
        };
    }).filter(p => p.name && p.price && p.name.length > 4);
}
"""

_CONTEXT_OPTS = dict(
    user_agent=(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    viewport={"width": 1280, "height": 800},
    locale="en-IN",
    timezone_id="Asia/Kolkata",
    extra_http_headers={"Accept-Language": "en-IN,en;q=0.9"},
)


async def _setup_location(browser) -> bool:
    """
    One-time: open BigBasket, select Connaught Place (Delhi) as delivery location,
    save cookies + localStorage to _STATE_PATH so future contexts load without a gate.
    Returns True if state was saved successfully.
    """
    context = await browser.new_context(**_CONTEXT_OPTS)
    page = await context.new_page()
    ok = False
    try:
        logger.info("[bigbasket] Setting up location state (one-time)…")
        await page.goto("https://www.bigbasket.com", wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2500)

        # Click the "Select Location" button to open picker
        loc_btn = page.locator("button", has_text="Select Location").first
        if await loc_btn.count():
            await loc_btn.click()
            await page.wait_for_timeout(1000)

        # Fill using Playwright fill() — fires native events React picks up
        loc_input = page.locator('input[placeholder*="area or street"]').first
        if not await loc_input.count():
            loc_input = page.locator('input[placeholder*="Search for"]').first
        if await loc_input.count():
            await loc_input.fill("Connaught Place")
            await page.wait_for_timeout(2500)  # wait for autocomplete

            # Try to click the first suggestion (various possible selectors)
            for sel in [
                "[class*='address-list'] li",
                "[class*='AddressList'] li",
                "[class*='suggestion-list'] li",
                "ul[class*='list'] li",
                "[role='listbox'] [role='option']",
            ]:
                try:
                    sugg = page.locator(sel).first
                    if await sugg.count():
                        await sugg.click()
                        await page.wait_for_timeout(2000)
                        logger.info(f"[bigbasket] Clicked suggestion via '{sel}'")
                        break
                except Exception:
                    pass
            else:
                # Fallback: press Down + Enter to select first autocomplete item
                await page.keyboard.press("ArrowDown")
                await page.wait_for_timeout(300)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(2000)

        # Save regardless — even partial state (session cookie) may help
        await context.storage_state(path=_STATE_PATH)
        logger.info(f"[bigbasket] State saved → {_STATE_PATH}")
        ok = True

    except Exception as e:
        logger.warning(f"[bigbasket] Location setup error: {e}")
    finally:
        await context.close()
    return ok


class BigBasketScraper(BaseScraper):
    PLATFORM_META = PlatformMeta(
        id="bigbasket",
        display="BigBasket",
        color="#84cc16",
        logo="BB",
        delivery_time="Next day",
    )

    async def search(self, query: str, **kwargs) -> List[dict]:
        import json
        from ..browser_manager import get_browser

        # Skip immediately if state file has no cookies — avoids blocking other scrapers.
        # Run setup_bigbasket_location() manually or at server startup to populate it.
        if os.path.exists(_STATE_PATH):
            with open(_STATE_PATH) as f:
                try:
                    _s = json.load(f)
                    if not _s.get("cookies"):
                        logger.info("[bigbasket] Empty state — skipping (run setup separately)")
                        return []
                except Exception:
                    return []
        else:
            logger.info("[bigbasket] No state file — skipping")
            return []

        browser = await get_browser()

        results = []
        context = None
        try:
            ctx_opts = dict(**_CONTEXT_OPTS)
            if os.path.exists(_STATE_PATH):
                ctx_opts["storage_state"] = _STATE_PATH

            context = await browser.new_context(**ctx_opts)
            # Stealth
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
                Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
                window.chrome = { runtime: {} };
            """)
            page = await context.new_page()

            url = f"https://www.bigbasket.com/ps/?q={query.replace(' ', '+')}&nc=as"
            logger.info(f"[bigbasket] {url}")
            await page.goto(url, wait_until="domcontentloaded", timeout=25000)
            await page.wait_for_timeout(3000)

            content = await page.content()

            # Location gate detected → purge stale state and bail
            if "Select Location" in content and "₹" not in content:
                logger.warning("[bigbasket] Location gate — purging state for next attempt")
                if os.path.exists(_STATE_PATH):
                    os.remove(_STATE_PATH)
                return []

            if "₹" not in content:
                logger.warning("[bigbasket] No price content")
                return []

            # Dismiss any popup
            for sel in ['button:text("Got it")', 'button:text("OK")', '[aria-label*="close" i]']:
                try:
                    btn = await page.query_selector(sel)
                    if btn:
                        await btn.click()
                        await page.wait_for_timeout(300)
                        break
                except Exception:
                    pass

            # Wait for SKUDeck cards
            try:
                await page.wait_for_selector('[class*="SKUDeck"]', timeout=10000)
            except Exception:
                pass  # fallback extraction will handle it

            await page.wait_for_timeout(500)
            products = await page.evaluate(_EXTRACT_JS)
            logger.info(f"[bigbasket] {len(products)} products extracted")

            results = [
                self.build_result({
                    "product_name": p["name"],
                    "price": p["price"],
                    "mrp": None,
                    "unit": None,
                    "image_url": None,
                    "product_url": p.get("product_url", "https://www.bigbasket.com"),
                    "in_stock": True,
                    "discount_pct": None,
                })
                for p in products
            ]

        except Exception as e:
            logger.warning(f"[bigbasket] scrape failed: {e}")
        finally:
            if context:
                await context.close()

        return results
