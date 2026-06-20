"""
Shared Playwright browser instance — launched once at server startup,
reused across all scraper requests for speed.
"""
import logging
from playwright.async_api import async_playwright, Browser, Playwright

logger = logging.getLogger(__name__)

_pw: Playwright = None
_browser: Browser = None

STEALTH_SCRIPT = """
    Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
    Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
    Object.defineProperty(navigator, 'languages', { get: () => ['en-IN', 'en'] });
    window.chrome = { runtime: {} };
"""

async def get_browser() -> Browser:
    global _pw, _browser
    if _browser is None or not _browser.is_connected():
        logger.info("Launching Playwright Chromium browser...")
        _pw = await async_playwright().start()
        _browser = await _pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-infobars",
                "--disable-extensions",
                "--mute-audio",
            ],
        )
        logger.info("Playwright browser ready")
    return _browser


async def new_page(lat: float = 28.6315, lon: float = 77.2167):
    """
    Open a fresh browser context + page with Indian locale, geolocation,
    and stealth patches applied. Caller must close the context when done.
    """
    browser = await get_browser()
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
        locale="en-IN",
        timezone_id="Asia/Kolkata",
        geolocation={"latitude": lat, "longitude": lon},
        permissions=["geolocation"],
        extra_http_headers={"Accept-Language": "en-IN,en;q=0.9"},
    )
    page = await context.new_page()
    await page.add_init_script(STEALTH_SCRIPT)
    return page, context


async def stop_browser():
    global _pw, _browser
    if _browser:
        try:
            await _browser.close()
        except Exception:
            pass
        _browser = None
    if _pw:
        try:
            await _pw.stop()
        except Exception:
            pass
        _pw = None
