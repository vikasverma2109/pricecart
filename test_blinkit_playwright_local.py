"""
Local Blinkit Playwright test.
1. Intercepts API calls blinkit.com makes to api.blinkit.com  → reveals real endpoint format
2. Checks if search results load (Indian IP should bypass geo-block)
3. Logs everything to test_blinkit_pw_log.txt

Double-click to run. Requires 'playwright' installed:
  pip install playwright
  playwright install chromium
"""

import asyncio
import json
import sys

LOG = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\test_blinkit_pw_log.txt"
LAT, LON = "28.6315", "77.2167"
QUERY = "toothpaste"

lines = []

def p(msg):
    print(msg)
    lines.append(str(msg))

async def run():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        p("ERROR: playwright not installed. Run: pip install playwright && playwright install chromium")
        return

    p(f"Starting Playwright test for Blinkit ({QUERY})...")
    p(f"Using lat={LAT}, lon={LON}")

    api_calls = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept-Language": "en-IN,en;q=0.9",
            }
        )

        # Intercept ALL requests to api.blinkit.com
        async def on_request(request):
            url = request.url
            if "api.blinkit.com" in url or "blinkit.com/api" in url:
                api_calls.append({"type": "REQUEST", "url": url, "method": request.method})
                p(f"  [REQ] {request.method} {url}")

        async def on_response(response):
            url = response.url
            if "api.blinkit.com" in url or "blinkit.com/api" in url:
                try:
                    body = await response.body()
                    body_str = body.decode("utf-8", errors="replace")[:500]
                    api_calls.append({
                        "type": "RESPONSE",
                        "url": url,
                        "status": response.status,
                        "body_preview": body_str
                    })
                    p(f"  [RSP] {response.status} {url}")
                    p(f"        body: {body_str[:200]}")
                except Exception as e:
                    p(f"  [RSP ERR] {url}: {e}")

        page = await context.new_page()
        page.on("request", on_request)
        page.on("response", on_response)

        # Pre-set location via init script
        lat_f, lon_f = float(LAT), float(LON)
        await page.add_init_script(f"""
            (() => {{
                try {{
                    localStorage.setItem('userLat', '{LAT}');
                    localStorage.setItem('userLng', '{LON}');
                    localStorage.setItem('user-lat', '{LAT}');
                    localStorage.setItem('user-lng', '{LON}');
                    localStorage.setItem('blinkit_lat', '{LAT}');
                    localStorage.setItem('blinkit_lng', '{LON}');
                    localStorage.setItem('gr_1_city', JSON.stringify({{lat:{lat_f},lng:{lon_f}}}));
                }} catch(e) {{}}
            }})();
        """)

        # Set cookies
        await context.add_cookies([
            {"name": "gr_1", "value": json.dumps({"lat": lat_f, "lng": lon_f}),
             "domain": ".blinkit.com", "path": "/"},
            {"name": "pincode", "value": "110001",
             "domain": ".blinkit.com", "path": "/"},
        ])

        search_url = f"https://blinkit.com/s/?q={QUERY.replace(' ', '+')}"
        p(f"\nNavigating to: {search_url}")

        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            p("Page loaded (domcontentloaded)")
        except Exception as e:
            p(f"goto error: {e}")

        await page.wait_for_timeout(5000)
        p("Waited 5s for JS to execute")

        content = await page.content()
        has_rupee = "₹" in content
        p(f"\n=== RESULT: '₹' in page: {has_rupee} ===")

        if has_rupee:
            # Try to count product prices
            prices = await page.query_selector_all('[class*="price"], [class*="Price"]')
            p(f"Price elements found: {len(prices)}")

            # Try to count product names
            from playwright.async_api import Page
            items = await page.evaluate("""
                () => {
                    const els = document.querySelectorAll('[class*="product"], [class*="Product"]');
                    return els.length;
                }
            """)
            p(f"Product-like elements found: {items}")
        else:
            p("No ₹ found — geo-blocked or location not set")
            # Save page source for inspection
            src_path = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\blinkit_page_source.html"
            with open(src_path, "w", encoding="utf-8") as f:
                f.write(content)
            p(f"Saved page source to: {src_path}")

        p(f"\n=== API CALLS CAPTURED ({len(api_calls)}) ===")
        req_urls = [c['url'] for c in api_calls if c['type'] == 'REQUEST']
        seen = set()
        for url in req_urls:
            if url not in seen:
                seen.add(url)
                p(f"  {url}")

        if api_calls:
            dump_path = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\blinkit_api_calls.json"
            with open(dump_path, "w") as f:
                json.dump(api_calls, f, indent=2)
            p(f"\nFull API call log saved to: {dump_path}")

        await browser.close()

asyncio.run(run())

with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"\n\nLog saved to: {LOG}")
input("\nDone. Press Enter to close...")
