"""
Test all 3 scrapers (Blinkit, Flipkart, Amazon) for a query locally.
Double-click to run. Results saved to test_all_scrapers_log.txt
"""
import asyncio
import sys
import os
import json

# ── Path setup so we can import the backend modules ──────────────────────────
BASE = os.path.dirname(os.path.abspath(__file__))
BACKEND = os.path.join(BASE, "backend")
sys.path.insert(0, BACKEND)

QUERY   = "Parle-G"
LOG     = os.path.join(BASE, "test_all_scrapers_log.txt")

# ── Auto-detect location from IP ─────────────────────────────────────────────
import urllib.request, json as _json

def detect_location():
    try:
        with urllib.request.urlopen("http://ip-api.com/json/?fields=lat,lon,city,regionName,zip", timeout=5) as r:
            data = _json.loads(r.read())
        lat  = str(data.get("lat", 18.5074))
        lon  = str(data.get("lon", 73.8077))
        city = data.get("city", "Unknown")
        pin  = data.get("zip", "411057")
        print(f"Auto-detected: {city} — lat={lat}, lon={lon}, zip={pin}")
        return lat, lon, pin, city
    except Exception as e:
        print(f"Location detection failed ({e}), using Pune fallback")
        return "18.5074", "73.8077", "411057", "Pune"

LAT, LON, PINCODE, CITY = detect_location()

lines = []

def p(msg=""):
    print(msg)
    lines.append(str(msg))

async def run():
    from app.scrapers.blinkit  import BlinkitScraper
    from app.scrapers.flipkart import FlipkartScraper
    from app.scrapers.amazon   import AmazonScraper
    from app.browser_manager   import stop_browser

    p(f"Query: {QUERY}")
    p(f"Location: {CITY} — lat={LAT}, lon={LON}, pincode={PINCODE}")
    p("=" * 60)

    scrapers = [
        ("Blinkit",  BlinkitScraper()),
        ("Flipkart", FlipkartScraper()),
        ("Amazon",   AmazonScraper()),
    ]

    # Give Blinkit extra time locally (no global API cap here)
    BlinkitScraper.SEARCH_TIMEOUT = 35.0

    async def run_one(name, scraper):
        p(f"\n[{name}] Starting...")
        try:
            results = await scraper.safe_search(
                QUERY,
                lat=LAT,
                lon=LON,
                pincode=PINCODE,
            )
            p(f"[{name}] Got {len(results)} results")
            return name, results
        except Exception as e:
            p(f"[{name}] ERROR: {e}")
            import traceback
            p(traceback.format_exc())
            return name, []

    # Run all 3 in parallel
    tasks = [run_one(name, scraper) for name, scraper in scrapers]
    all_results = await asyncio.gather(*tasks)

    p("\n" + "=" * 60)
    p(f"PRICE COMPARISON — {QUERY}")
    p("=" * 60)

    for platform_name, results in all_results:
        p(f"\n{'─'*40}")
        p(f"  {platform_name}")
        p(f"{'─'*40}")
        if not results:
            p("  (no results)")
            continue

        # results is a list. Each item may be a dict with product info.
        # The scraper returns list of dicts from build_result()
        # Let's handle both structures.
        products = results
        if isinstance(results, list) and results and isinstance(results[0], list):
            # Wrapped in platform list: [[platform_meta], prod1, prod2, ...]
            products = results[1:] if len(results) > 1 else []

        shown = 0
        for item in products[:5]:
            if not isinstance(item, dict):
                continue
            name  = item.get("product_name") or item.get("name", "?")
            price = item.get("price")
            mrp   = item.get("mrp")
            unit  = item.get("unit", "")

            price_str = f"₹{price:.0f}" if price else "N/A"
            mrp_str   = f" (MRP ₹{mrp:.0f})" if mrp else ""
            unit_str  = f"  [{unit}]" if unit else ""

            p(f"  {shown+1}. {name}")
            p(f"     Price: {price_str}{mrp_str}{unit_str}")
            shown += 1

        if shown == 0:
            p("  (could not parse results)")
            p(f"  Raw sample: {json.dumps(products[:2], default=str)[:400]}")

    await stop_browser()

asyncio.run(run())

output = "\n".join(lines)
with open(LOG, "w", encoding="utf-8") as f:
    f.write(output + "\n")

print(f"\n\nFull log saved to: {LOG}")
input("\nDone. Press Enter to close...")
