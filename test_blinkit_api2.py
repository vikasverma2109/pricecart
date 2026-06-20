"""
Probe Blinkit API for correct search endpoints (newer versions).
"""
import json, urllib.request, urllib.error, traceback

LOG = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\test_blinkit_api2_log.txt"
QUERY = "tata salt"
LAT, LON = "28.6315", "77.2167"
Q = QUERY.replace(" ", "+")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Origin": "https://blinkit.com",
    "Referer": f"https://blinkit.com/s/?q={Q}",
    "app_version": "3.0",
    "web_x_entry_point": "website",
    "lat": LAT,
    "lon": LON,
    "Content-Type": "application/json",
}

ENDPOINTS = [
    f"https://api.blinkit.com/v6/search/products?search_string={Q}&lat={LAT}&lon={LON}",
    f"https://api.blinkit.com/v5/search/products?search_string={Q}&lat={LAT}&lon={LON}",
    f"https://api.blinkit.com/v4/search/products?search_string={Q}&lat={LAT}&lon={LON}",
    f"https://api.blinkit.com/v6/oos/product/search?search_string={Q}&lat={LAT}&lon={LON}&merchant_id=0",
    f"https://api.blinkit.com/v5/oos/product/search?search_string={Q}&lat={LAT}&lon={LON}&merchant_id=0",
    f"https://api.blinkit.com/v4/oos/product/search?search_string={Q}&lat={LAT}&lon={LON}&merchant_id=0",
    f"https://api.blinkit.com/v6/products/search?q={Q}&lat={LAT}&lon={LON}",
    f"https://api.blinkit.com/v6/listing/?search_string={Q}&lat={LAT}&lon={LON}",
    # Try with different params
    f"https://api.blinkit.com/v6/search/products?q={Q}&lat={LAT}&lon={LON}",
    f"https://api.blinkit.com/v3/search/products?search_string={Q}&lat={LAT}&lon={LON}",
]

lines = []
for url in ENDPOINTS:
    lines.append(f"\n{'='*60}")
    lines.append(f"URL: {url}")
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode("utf-8", errors="replace")
            lines.append(f"Status: {r.status} ✅")
            try:
                data = json.loads(raw)
                lines.append(json.dumps(data, indent=2)[:3000])
            except Exception:
                lines.append(raw[:1000])
    except urllib.error.HTTPError as e:
        body = ""
        try: body = e.read().decode()[:300]
        except: pass
        lines.append(f"HTTP {e.code}: {body}")
    except Exception as ex:
        lines.append(f"Error: {ex}")

result = "\n".join(lines)
with open(LOG, "w", encoding="utf-8") as f:
    f.write(result + "\n")
print(result)
input("\nDone. Press Enter to close...")
