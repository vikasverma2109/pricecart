"""
Blinkit local debug test — visits homepage first so location is detected,
then searches for Parle-G and shows prices clearly.
Log saved to test_blinkit_debug_log.txt
Double-click to run.
"""

import asyncio, json, sys, os, urllib.request

LOG = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\test_blinkit_debug_log.txt"
QUERY = "Parle-G"

lines = []
def p(msg=""):
    print(msg)
    lines.append(str(msg))

# ── Auto-detect location ──────────────────────────────────────────────────────
def detect_location():
    try:
        with urllib.request.urlopen("http://ip-api.com/json/?fields=lat,lon,city,zip", timeout=5) as r:
            d = json.loads(r.read())
        return str(d["lat"]), str(d["lon"]), d.get("zip","411057"), d.get("city","Pune")
    except Exception as e:
        p(f"IP detection failed: {e}, using Pune fallback")
        return "18.5074", "73.8077", "411057", "Pune"

LAT, LON, PINCODE, CITY = detect_location()
p(f"Location: {CITY}  lat={LAT}  lon={LON}  pincode={PINCODE}")

_SET_LOCATION_JS = """
(lat, lon) => {
    try {
        localStorage.setItem('userLat',    String(lat));
        localStorage.setItem('userLng',    String(lon));
        localStorage.setItem('user-lat',   String(lat));
        localStorage.setItem('user-lng',   String(lon));
        localStorage.setItem('blinkit_lat',String(lat));
        localStorage.setItem('blinkit_lng',String(lon));
        localStorage.setItem('gr_1_city',  JSON.stringify({lat, lng: lon}));
    } catch(e) {}
}
"""

_EXTRACT_JS = r"""
() => {
    const RUPEE = '₹';
    const priceEls = Array.from(document.querySelectorAll('*')).filter(el =>
        el.children.length === 0 &&
        el.textContent.trim().startsWith(RUPEE) &&
        el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE'
    );

    const results = [];
    const seenCards = new Set();

    for (const priceEl of priceEls) {
        const m = priceEl.textContent.trim().match(/₹(\d+(?:\.\d+)?)/);
        if (!m) continue;
        const price = parseFloat(m[1]);
        if (price < 5 || price > 50000) continue;

        let card = priceEl.parentElement;
        for (let i = 0; i < 10; i++) {
            if (!card || !card.parentElement) break;
            card = card.parentElement;
            const len = (card.textContent || '').trim().length;
            if (len >= 30 && len <= 800) break;
        }
        if (!card || seenCards.has(card)) continue;
        seenCards.add(card);

        const leaves = Array.from(card.querySelectorAll('*')).filter(el =>
            el.children.length === 0 && el.textContent.trim().length > 0 &&
            el.tagName !== 'SCRIPT' && el.tagName !== 'STYLE'
        );

        let name = '';
        let unit = null;
        for (const el of leaves) {
            const t = el.textContent.trim();
            if (!t || t.length < 3) continue;
            if (/^[₹\d\s,\.\-\+\%]+$/.test(t)) continue;
            if (/^(ADD|MINS?|OUT OF STOCK|SOLD OUT|BUY|CART|FREE|OFFER|OFF|SAVE|MRP|EACH)$/i.test(t)) continue;
            if (!unit && /^\d+\.?\d*\s*(g|gm|gram|grams|kg|kgs|ml|l|ltr|liter|litres?|pcs?|pieces?|nos?|pack)s?\b/i.test(t)) {
                unit = t; continue;
            }
            if (t.length > name.length && t.length < 200) name = t;
        }

        name = name.replace(/\d+\.?\d*\s*(g|gm|gram|grams|kg|kgs|ml|l|ltr|liter|litres?|pcs?|pieces?|nos?|pack)s?(\s*[xX×]\s*\d+\.?\d*\s*\w+)?$/i, '').trim();

        // MRP
        let mrp = null;
        const allPrices = leaves.map(el => el.textContent.trim())
            .filter(t => /^₹\d+/.test(t))
            .map(t => parseFloat(t.replace('₹','')))
            .filter(p => p >= 5 && p <= 50000);
        if (allPrices.length > 1) {
            const higher = allPrices.filter(p => p > price);
            if (higher.length) mrp = Math.min(...higher);
        }

        if (name && price) results.push({ name, price, mrp, unit });
    }
    return results.slice(0, 8);
}
"""

async def run():
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        p("ERROR: playwright not installed. Run:  pip install playwright && playwright install chromium")
        return

    lat_f, lon_f = float(LAT), float(LON)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=["--no-sandbox","--disable-dev-shm-usage","--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/125.0.0.0 Safari/537.36",
            viewport={"width":1280,"height":800},
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            geolocation={"latitude": lat_f, "longitude": lon_f},
            permissions=["geolocation"],
            extra_http_headers={"Accept-Language":"en-IN,en;q=0.9"},
        )
        page = await context.new_page()

        # ── STEP 1: pre-inject localStorage via init script ───────────────────
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

        # ── STEP 2: set cookies ───────────────────────────────────────────────
        await context.add_cookies([
            {"name": "gr_1",   "value": json.dumps({"lat": lat_f, "lng": lon_f}),
             "domain": ".blinkit.com", "path": "/"},
            {"name": "pincode","value": PINCODE,
             "domain": ".blinkit.com", "path": "/"},
        ])

        # ── STEP 3: visit homepage first (critical — Blinkit sets session here)
        p("\nStep 1/3: Loading blinkit.com homepage...")
        try:
            await page.goto("https://blinkit.com/", wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(3000)
            await page.evaluate(_SET_LOCATION_JS, lat_f, lon_f)
            homepage_content = await page.content()
            has_rupee_hp = "₹" in homepage_content
            p(f"  Homepage loaded. ₹ present: {has_rupee_hp}")
        except Exception as e:
            p(f"  Homepage load error: {e}")

        # ── STEP 4: go to search URL ──────────────────────────────────────────
        search_url = f"https://blinkit.com/s/?q={QUERY.replace(' ', '+')}"
        p(f"\nStep 2/3: Searching '{QUERY}' → {search_url}")
        try:
            await page.goto(search_url, wait_until="domcontentloaded", timeout=20000)
            await page.wait_for_timeout(4000)
            await page.evaluate(_SET_LOCATION_JS, lat_f, lon_f)
            await page.wait_for_timeout(500)
        except Exception as e:
            p(f"  Search navigation error: {e}")

        content = await page.content()
        has_rupee = "₹" in content
        p(f"  ₹ on search page: {has_rupee}")

        if not has_rupee:
            p("  No ₹ — reloading once...")
            try:
                await page.reload(wait_until="domcontentloaded", timeout=15000)
                await page.wait_for_timeout(3000)
                await page.evaluate(_SET_LOCATION_JS, lat_f, lon_f)
                content = await page.content()
                has_rupee = "₹" in content
                p(f"  After reload, ₹ present: {has_rupee}")
            except Exception as e:
                p(f"  Reload error: {e}")

        # ── STEP 5: extract and show prices ──────────────────────────────────
        p(f"\nStep 3/3: Extracting prices...")
        if has_rupee:
            products = await page.evaluate(_EXTRACT_JS)
            p(f"\n{'='*50}")
            p(f"  BLINKIT — {QUERY} — {CITY}")
            p(f"{'='*50}")
            if products:
                for i, prod in enumerate(products, 1):
                    name  = prod.get("name","?")
                    price = prod.get("price")
                    mrp   = prod.get("mrp")
                    unit  = prod.get("unit","")

                    price_str = f"₹{price:.0f}" if price else "N/A"
                    mrp_str   = f"  MRP ₹{mrp:.0f}" if mrp else ""
                    unit_str  = f"  [{unit}]" if unit else ""
                    disc_str  = ""
                    if price and mrp and mrp > price:
                        disc = round((mrp - price) / mrp * 100)
                        disc_str = f"  ({disc}% off)"

                    p(f"  {i}. {name}")
                    p(f"     Price: {price_str}{mrp_str}{disc_str}{unit_str}")
            else:
                p("  No products extracted (JS selector issue?)")
                # Save page for inspection
                html_path = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\blinkit_debug_page.html"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(content)
                p(f"  Page saved to: {html_path}")
        else:
            p("  ❌ Still no ₹ — Blinkit showing location gate, can't extract prices.")
            html_path = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\blinkit_debug_page.html"
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(content)
            p(f"  Page saved to: {html_path}")

        await browser.close()


asyncio.run(run())

with open(LOG, "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print(f"\nLog saved to: {LOG}")
input("\nDone. Press Enter to close...")
