"""
Test Blinkit REST API endpoints locally.
Run by double-clicking. Results written to test_blinkit_api_log.txt
"""
import json
import urllib.request
import urllib.error
import traceback

LOG = r"C:\Create-Tool\PriceComparisonTool\Price Compare Tool\test_blinkit_api_log.txt"
QUERY = "tata salt"
LAT, LON = "28.6315", "77.2167"

# Headers that mimic the Blinkit web app
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-IN,en;q=0.9",
    "Origin": "https://blinkit.com",
    "Referer": f"https://blinkit.com/s/?q={QUERY.replace(' ', '+')}",
    "app_version": "3.0",
    "web_x_entry_point": "website",
    "lat": LAT,
    "lon": LON,
}

ENDPOINTS = [
    # v3 search (used by web app)
    f"https://api.blinkit.com/v3/oos/product/search?lat={LAT}&lon={LON}&merchant_id=0&search_string={QUERY.replace(' ', '+')}",
    # v2 listing
    f"https://api.blinkit.com/v2/listing/category/product?lat={LAT}&lon={LON}&q={QUERY.replace(' ', '+')}",
    # v1 search
    f"https://api.blinkit.com/v1/search/?lat={LAT}&lon={LON}&q={QUERY.replace(' ', '+')}",
    # snb search (Blinkit internal)
    f"https://api.blinkit.com/snb/api/v1/store/search?lat={LAT}&lon={LON}&query={QUERY.replace(' ', '+')}",
]

lines = []

for url in ENDPOINTS:
    lines.append(f"\n{'='*60}")
    lines.append(f"URL: {url}")
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=10) as r:
            status = r.status
            raw = r.read().decode("utf-8", errors="replace")
            lines.append(f"Status: {status}")
            # Try to pretty-print JSON
            try:
                data = json.loads(raw)
                snippet = json.dumps(data, indent=2)[:2000]
                lines.append(f"Response (first 2000 chars):\n{snippet}")
                # Count products if possible
                if isinstance(data, dict):
                    for k in ["products", "data", "results", "items", "response"]:
                        if k in data:
                            v = data[k]
                            if isinstance(v, list):
                                lines.append(f"\n>>> Found {len(v)} items under '{k}'")
                                if v:
                                    lines.append(f"First item keys: {list(v[0].keys()) if isinstance(v[0], dict) else str(v[0])[:200]}")
                            elif isinstance(v, dict):
                                lines.append(f"'{k}' is a dict with keys: {list(v.keys())}")
            except json.JSONDecodeError:
                lines.append(f"Response (raw, first 1000 chars):\n{raw[:1000]}")
    except urllib.error.HTTPError as e:
        lines.append(f"HTTP Error {e.code}: {e.reason}")
        try:
            body = e.read().decode("utf-8", errors="replace")[:500]
            lines.append(f"Body: {body}")
        except Exception:
            pass
    except urllib.error.URLError as e:
        lines.append(f"URL Error: {e.reason}")
    except Exception:
        lines.append(f"Exception:\n{traceback.format_exc()}")

result = "\n".join(lines)
with open(LOG, "w", encoding="utf-8") as f:
    f.write(result + "\n")

print(result)
input("\nDone. Press Enter to close...")
