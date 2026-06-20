# 🛒 PriceCart — Grocery Price Comparison Tool

Compare prices for any grocery product across **Flipkart, Blinkit, Zepto, BigBasket, and Swiggy Instamart** in real time.

---

## Architecture

```
┌─────────────────────────┐       ┌──────────────────────────────────┐
│   Frontend (React+Vite) │ ────▶ │   Backend (Python + FastAPI)     │
│   Deployed: Vercel      │       │   Deployed: Railway              │
└─────────────────────────┘       └──────────────────────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
              Flipkart API          Blinkit API             Zepto API
              BigBasket API         Swiggy API
```

- Scrapers run **in parallel** (asyncio gather) — total latency ≈ slowest single scraper
- Results are **cached 5 minutes** per (query, pincode) pair
- Products are **fuzzy-matched** across platforms so you compare like-for-like

---

## Local Development

### 1. Backend

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Test: http://localhost:8000/api/health

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

The Vite dev server proxies `/api/*` to `localhost:8000` automatically.

---

## Deploy to Production

### Backend → Railway

1. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
2. Select the `backend/` folder (or set root directory to `backend`)
3. Railway auto-detects Python via Nixpacks — no extra config needed
4. Copy the generated public URL (e.g. `https://pricecart-backend.railway.app`)

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → New Project → Import from GitHub
2. Set **Root Directory** to `frontend`
3. Add Environment Variable:
   - `VITE_API_URL` = `https://your-backend.railway.app`
4. Deploy — Vercel auto-builds with `npm run build`

---

## Adding a New Platform

1. Create `backend/app/scrapers/myntra.py` (copy any existing scraper as template)
2. Subclass `BaseScraper`, set `PLATFORM_META`, implement `search()`
3. Import and add to `ALL_SCRAPERS` in `backend/app/scrapers/__init__.py`
4. Add platform metadata to `PLATFORMS` array in `frontend/src/App.jsx`

That's it — the framework handles parallel fetch, caching, matching, and UI automatically.

---

## Notes on Scraping

Real-world grocery apps use anti-bot measures (CAPTCHAs, rate limits, location gating).
If scrapers return empty results:

- **Add request delays**: `await asyncio.sleep(0.5)` in the scraper
- **Rotate User-Agents**: update `DEFAULT_HEADERS` in `base.py`
- **Use residential proxies**: set `proxies` on the `httpx.AsyncClient`
- **Switch to Playwright**: for JS-rendered pages, replace `httpx` with Playwright for that scraper

Each scraper is independent — a failed scraper shows 0 results for that platform but doesn't break others.
