"""
Price Compare API — FastAPI backend

Endpoints:
  GET /api/search?q=<query>&city=<city>
  GET /api/search?q=<query>&lat=<lat>&lon=<lon>&pincode=<pincode>
  GET /api/cities
  GET /api/platforms
  GET /api/health
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from .scrapers import ALL_SCRAPERS
from .matcher import group_products, build_compared_products
from .cache import cache
from .location import get_city, get_city_list, CITIES, DEFAULT_CITY
from .mock_data import find_mock
from .browser_manager import get_browser, stop_browser

STATIC_DIR = Path(__file__).parent.parent / "static"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup — pre-warm Playwright browser so first search is fast
    try:
        await get_browser()
        logger.info("Playwright browser pre-warmed")
    except Exception as e:
        logger.warning(f"Browser pre-warm failed (will retry on first request): {e}")
    yield
    # Shutdown
    await stop_browser()
    logger.info("Playwright browser closed")


app = FastAPI(
    title="Price Compare API",
    description="Compare grocery prices across Flipkart, Blinkit, Zepto, BigBasket, Swiggy Instamart, Amazon Fresh",
    version="3.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    return {"status": "ok", "platforms": len(ALL_SCRAPERS), "version": "3col-price-filter-2026-06-20"}


@app.get("/api/cities")
async def cities():
    """List all supported cities for the location picker."""
    return get_city_list()


@app.get("/api/platforms")
async def platforms():
    """List all supported platforms."""
    return [
        {
            "id": s.PLATFORM_META.id,
            "display": s.PLATFORM_META.display,
            "color": s.PLATFORM_META.color,
            "logo": s.PLATFORM_META.logo,
            "delivery_time": s.PLATFORM_META.delivery_time,
        }
        for s in ALL_SCRAPERS
    ]


@app.get("/api/search")
async def search(
    q: str = Query(..., min_length=2, description="Product search query"),
    city: Optional[str] = Query(None, description="City name (e.g. Mumbai, Delhi)"),
    lat: Optional[str] = Query(None, description="Latitude (overrides city)"),
    lon: Optional[str] = Query(None, description="Longitude (overrides city)"),
    pincode: Optional[str] = Query(None, description="Pincode (overrides city)"),
):
    """
    Search for a product across all platforms and return price comparison.

    Location priority: lat+lon > city name > default (Delhi).
    Results cached 5 min per (query, city/pincode) key.
    """
    # Resolve location
    if lat and lon:
        loc = {
            "lat": lat, "lon": lon,
            "pincode": pincode or "110001",
            "bb_city_id": "5",
            "zepto_store": CITIES["Delhi"]["zepto_store"],
            "name": f"{lat},{lon}",
        }
    elif city:
        loc = get_city(city)
    else:
        loc = get_city(DEFAULT_CITY)

    cache_key = f"{q.lower().strip()}:{loc['name']}"
    cached = cache.get(cache_key)
    if cached:
        logger.info(f"Cache hit: {cache_key}")
        return cached

    logger.info(f"Searching '{q}' @ {loc['name']} (pincode {loc['pincode']})")

    # Run all scrapers in parallel, passing location data.
    # Use asyncio.wait with a global 25s cap so slow scrapers (e.g. Blinkit)
    # don't block the response — we return whatever fast scrapers already found.
    API_TIMEOUT = 30.0
    raw_tasks = [
        asyncio.create_task(
            scraper_cls().safe_search(
                q,
                pincode=loc["pincode"],
                lat=loc["lat"],
                lon=loc["lon"],
                store_id=loc.get("zepto_store"),
                city_id=loc.get("bb_city_id"),
            )
        )
        for scraper_cls in ALL_SCRAPERS
    ]
    done, pending = await asyncio.wait(raw_tasks, timeout=API_TIMEOUT)
    for t in pending:
        t.cancel()
        logger.warning("Scraper task cancelled (exceeded %.0fs global API timeout)", API_TIMEOUT)

    platform_results = []
    for t in done:
        try:
            platform_results.append(t.result())
        except Exception as e:
            logger.warning("Scraper task raised: %s", e)
            platform_results.append([])

    all_results = [item for results in platform_results for item in results]
    is_demo = False

    if not all_results:
        # Fall back to mock data (platforms are blocking scrapers)
        logger.info(f"All scrapers returned 0 results for '{q}' — trying mock data")
        mock_items = find_mock(q)
        if mock_items:
            is_demo = True
            all_results = mock_items
            logger.info(f"Mock data: {len(mock_items)} items for '{q}'")
        else:
            return {"query": q, "location": loc["name"], "results": [], "total": 0, "demo": False}

    if is_demo:
        # Mock data is already structured as flat product dicts — group by name similarity
        # Dedupe per platform for mock: just use them directly
        from itertools import groupby

        # Group by product_name similarity (simple: exact name match groups)
        name_groups: dict[str, list] = {}
        for item in all_results:
            key = item["product_name"].lower()
            name_groups.setdefault(key, []).append(item)

        compared = []
        for name, group_items in name_groups.items():
            cheapest = min(group_items, key=lambda x: x["price"])
            prices_by_platform = {i["platform"]: i for i in group_items}
            compared.append({
                "product_name": group_items[0]["product_name"],
                "cheapest_platform": cheapest["platform_display"],
                "cheapest_price": cheapest["price"],
                "prices": [
                    {
                        "platform": i["platform"],
                        "platform_display": i["platform_display"],
                        "platform_color": i["platform_color"],
                        "platform_logo": i["platform_logo"],
                        "price": i["price"],
                        "mrp": i.get("mrp"),
                        "unit": i.get("unit"),
                        "in_stock": i.get("in_stock", True),
                        "delivery_time": i.get("delivery_time"),
                        "product_url": i.get("product_url"),
                        "image_url": i.get("image_url"),
                        "discount_pct": i.get("discount_pct"),
                    }
                    for i in sorted(group_items, key=lambda x: x["price"])
                ],
            })
        compared.sort(key=lambda x: x["cheapest_price"])
    else:
        groups = group_products(all_results)
        compared = build_compared_products(groups)

    response = {
        "query": q,
        "location": loc["name"],
        "results": compared,
        "total": len(compared),
        "demo": is_demo,
    }

    cache.set(cache_key, response)
    return response


# Serve React frontend — must be LAST (catch-all)
if STATIC_DIR.exists():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/favicon.svg")
    async def favicon():
        return FileResponse(STATIC_DIR / "favicon.svg")

    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        return FileResponse(STATIC_DIR / "index.html")
