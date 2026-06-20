import { useState, useCallback, useMemo, useEffect } from "react";
import SearchBar from "./components/SearchBar";
import { searchProducts } from "./api";

const PLATFORMS = [
  { id: "blinkit",  display: "Blinkit",   color: "#f8c200", bg: "#fffbea", delivery: "10 mins" },
  { id: "flipkart", display: "Flipkart",  color: "#2563eb", bg: "#eff6ff", delivery: "1-2 days" },
  { id: "amazon",   display: "Amazon.in", color: "#ff9900", bg: "#fff7ed", delivery: "1-2 days" },
];

// ── Per-platform product card ──────────────────────────────────────────────
function PlatformItem({ item, isCheapest }) {
  return (
    <a
      href={item.product_url || "#"}
      target="_blank"
      rel="noopener noreferrer"
      className={`block px-2 py-2 border-b border-gray-50 hover:bg-gray-50 transition-colors no-underline ${
        isCheapest ? "bg-green-50 hover:bg-green-50" : ""
      }`}
    >
      <div className="flex items-center gap-2">
        {item.image_url ? (
          <img
            src={item.image_url}
            alt={item.name}
            className="w-9 h-9 rounded-lg object-contain flex-shrink-0 bg-white border border-gray-100"
            onError={e => { e.target.style.display = "none"; }}
          />
        ) : (
          <div className="w-9 h-9 rounded-lg bg-gray-100 flex-shrink-0 flex items-center justify-center text-base">🛒</div>
        )}
        <div className="flex-1 min-w-0">
          <p className="text-xs text-gray-800 font-medium leading-snug line-clamp-2">{item.name}</p>
          {item.unit && (
            <p className="text-xs text-gray-400 mt-0.5">{item.unit}</p>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between mt-1.5 pl-11">
        <div className="flex items-center gap-1.5 flex-wrap">
          <span className="text-sm font-bold text-gray-900">
            ₹{item.price != null ? item.price.toFixed(0) : "—"}
          </span>
          {item.mrp && item.mrp > item.price && (
            <span className="text-xs text-gray-400 line-through">₹{item.mrp.toFixed(0)}</span>
          )}
          {item.discount_pct && (
            <span className="text-xs text-green-700 font-semibold">{item.discount_pct.toFixed(0)}% off</span>
          )}
        </div>
        {isCheapest && (
          <span className="text-xs font-semibold text-green-700 bg-green-100 px-1.5 py-0.5 rounded-full whitespace-nowrap">
            Best
          </span>
        )}
      </div>
    </a>
  );
}

// ── Platform column ────────────────────────────────────────────────────────
function PlatformColumn({ platform, items, cheapestPrice }) {
  return (
    <div className="flex flex-col min-w-0 rounded-xl overflow-hidden border border-gray-200 bg-white shadow-sm">
      {/* Header */}
      <div
        className="px-3 py-2 border-b border-gray-100"
        style={{ backgroundColor: platform.bg }}
      >
        <div className="flex items-center gap-1.5">
          <span
            className="w-2.5 h-2.5 rounded-full flex-shrink-0"
            style={{ backgroundColor: platform.color }}
          />
          <span className="font-bold text-gray-900 text-sm">{platform.display}</span>
        </div>
        <div className="flex items-center justify-between mt-0.5">
          <span className="text-xs text-gray-500">⏱ {platform.delivery}</span>
          <span className="text-xs text-gray-500">{items.length} items</span>
        </div>
      </div>

      {/* Product list */}
      <div className="flex-1 overflow-y-auto" style={{ maxHeight: "70vh" }}>
        {items.length === 0 ? (
          <div className="py-8 text-center text-gray-400 text-xs px-3">
            No results
          </div>
        ) : (
          items.map((item, i) => (
            <PlatformItem
              key={i}
              item={item}
              isCheapest={item.price != null && item.price === cheapestPrice}
            />
          ))
        )}
      </div>
    </div>
  );
}

// ── Price range filter ─────────────────────────────────────────────────────
function PriceFilter({ min, max, value, onChange }) {
  const [localMin, setLocalMin] = useState(value[0]);
  const [localMax, setLocalMax] = useState(value[1]);

  useEffect(() => { setLocalMin(value[0]); }, [value[0]]);
  useEffect(() => { setLocalMax(value[1]); }, [value[1]]);

  const commit = (newMin, newMax) => {
    onChange([Math.min(newMin, newMax), Math.max(newMin, newMax)]);
  };

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs text-gray-500 font-medium">Price:</span>
      <div className="flex items-center gap-1">
        <span className="text-xs text-gray-400">₹</span>
        <input
          type="number"
          value={localMin}
          min={min}
          max={max}
          onChange={e => setLocalMin(Number(e.target.value))}
          onBlur={() => commit(localMin, localMax)}
          className="w-16 text-xs border border-gray-200 rounded-lg px-2 py-1 text-center focus:outline-none focus:border-indigo-400"
        />
        <span className="text-xs text-gray-400">—</span>
        <span className="text-xs text-gray-400">₹</span>
        <input
          type="number"
          value={localMax}
          min={min}
          max={max}
          onChange={e => setLocalMax(Number(e.target.value))}
          onBlur={() => commit(localMin, localMax)}
          className="w-16 text-xs border border-gray-200 rounded-lg px-2 py-1 text-center focus:outline-none focus:border-indigo-400"
        />
      </div>
      {(value[0] !== min || value[1] !== max) && (
        <button
          onClick={() => { setLocalMin(min); setLocalMax(max); onChange([min, max]); }}
          className="text-xs text-indigo-500 underline"
        >
          Reset
        </button>
      )}
    </div>
  );
}

// ── Main App ───────────────────────────────────────────────────────────────
export default function App() {
  const [results, setResults]     = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [lastQuery, setLastQuery] = useState("");
  const [priceFilter, setPriceFilter] = useState([0, Infinity]);

  const handleSearch = useCallback(async (query, location = {}) => {
    setLoading(true);
    setError(null);
    setResults(null);
    setLastQuery(query);
    setPriceFilter([0, Infinity]);
    try {
      const data = await searchProducts(query, location);
      setResults(data);
    } catch (e) {
      setError(e.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  }, []);

  // Flatten all prices from API response into per-platform lists
  const platformData = useMemo(() => {
    if (!results?.results) return {};
    const map = {};
    PLATFORMS.forEach(p => { map[p.id] = []; });

    results.results.forEach(product => {
      (product.prices || []).forEach(priceEntry => {
        if (map[priceEntry.platform] !== undefined) {
          map[priceEntry.platform].push({
            name: product.canonical_name || priceEntry.product_name,
            image_url: priceEntry.image_url || product.image_url || null,
            ...priceEntry,
          });
        }
      });
    });

    // Sort each column: price low → high
    Object.keys(map).forEach(pid => {
      map[pid].sort((a, b) => (a.price ?? Infinity) - (b.price ?? Infinity));
    });

    return map;
  }, [results]);

  // Compute global price range from all products
  const [globalMin, globalMax] = useMemo(() => {
    if (!results?.results) return [0, 1000];
    const all = results.results.flatMap(p =>
      (p.prices || []).map(r => r.price).filter(v => v != null)
    );
    if (!all.length) return [0, 1000];
    return [Math.floor(Math.min(...all)), Math.ceil(Math.max(...all))];
  }, [results]);

  // Set initial filter when new results arrive
  useEffect(() => {
    if (results) setPriceFilter([globalMin, globalMax]);
  }, [globalMin, globalMax]);

  // Apply price filter to each column
  const filteredPlatformData = useMemo(() => {
    const [minP, maxP] = priceFilter;
    const out = {};
    Object.entries(platformData).forEach(([pid, items]) => {
      out[pid] = items.filter(item => item.price != null && item.price >= minP && item.price <= maxP);
    });
    return out;
  }, [platformData, priceFilter]);

  // Cheapest price across all platforms (for "Best" badge)
  const cheapestPrice = useMemo(() => {
    const allPrices = Object.values(filteredPlatformData)
      .flat()
      .map(i => i.price)
      .filter(v => v != null);
    return allPrices.length ? Math.min(...allPrices) : null;
  }, [filteredPlatformData]);

  const hasResults = Boolean(results && results.total > 0);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="sticky top-0 z-20 bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-5xl mx-auto px-4 pt-3 pb-3">
          <div className="flex items-center gap-2 mb-2.5">
            <span className="text-xl">🛒</span>
            <span className="font-bold text-gray-900">PriceCart</span>
            <span className="text-xs text-gray-400">· Blinkit · Flipkart · Amazon</span>
          </div>
          <SearchBar onSearch={handleSearch} loading={loading} />
        </div>
      </header>

      {/* Filter bar */}
      {hasResults && !loading && (
        <div className="sticky z-10 bg-white border-b border-gray-100" style={{ top: "112px" }}>
          <div className="max-w-5xl mx-auto px-4 py-2 flex items-center gap-4 flex-wrap">
            <p className="text-xs text-gray-500">
              <span className="font-semibold text-gray-800">{results.total}</span> products for &ldquo;
              <span className="font-medium">{results.query}</span>&rdquo;
              {results.location && <span className="text-gray-400"> · {results.location}</span>}
            </p>
            <div className="ml-auto">
              <PriceFilter
                min={globalMin}
                max={globalMax}
                value={priceFilter}
                onChange={setPriceFilter}
              />
            </div>
          </div>
        </div>
      )}

      <main className="max-w-5xl mx-auto px-4 py-4 pb-10">
        {/* Empty state */}
        {!results && !loading && !error && (
          <div className="text-center py-14">
            <div className="text-5xl mb-4">🛒</div>
            <h2 className="text-xl font-bold text-gray-800 mb-2">Compare grocery prices</h2>
            <p className="text-gray-500 text-sm mb-6 max-w-xs mx-auto">
              Search any product — compare prices across 3 platforms side by side.
            </p>
            <div className="inline-flex flex-col gap-2 text-sm text-left bg-white border border-gray-100 rounded-2xl px-5 py-4 shadow-sm">
              {PLATFORMS.map(p => (
                <div key={p.id} className="flex items-center gap-3">
                  <span className="w-2.5 h-2.5 rounded-full flex-shrink-0" style={{ backgroundColor: p.color }} />
                  <span className="text-gray-700 font-medium w-24">{p.display}</span>
                  <span className="text-gray-400 text-xs">{p.delivery}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Loading skeleton */}
        {loading && (
          <div>
            <p className="text-center text-gray-500 text-sm mb-4">
              Comparing &ldquo;{lastQuery}&rdquo; across 3 platforms&hellip;
            </p>
            <div className="grid grid-cols-3 gap-3">
              {PLATFORMS.map(p => (
                <div key={p.id} className="rounded-xl overflow-hidden border border-gray-200 bg-white shadow-sm animate-pulse">
                  <div className="px-3 py-2 border-b border-gray-100" style={{ backgroundColor: p.bg }}>
                    <div className="h-4 bg-gray-200 rounded w-3/4 mb-1" />
                    <div className="h-3 bg-gray-100 rounded w-1/2" />
                  </div>
                  {[1,2,3,4].map(i => (
                    <div key={i} className="flex items-center gap-2 px-3 py-3 border-b border-gray-50">
                      <div className="w-9 h-9 rounded-lg bg-gray-200 flex-shrink-0" />
                      <div className="flex-1">
                        <div className="h-3 bg-gray-200 rounded w-5/6 mb-1.5" />
                        <div className="h-3 bg-gray-200 rounded w-1/3" />
                      </div>
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Error */}
        {error && !loading && (
          <div className="text-center py-12">
            <div className="text-4xl mb-3">⚠️</div>
            <p className="text-red-600 font-medium text-sm">{error}</p>
          </div>
        )}

        {/* 3-column results */}
        {hasResults && !loading && (
          <div>
            {results.demo && (
              <div className="mb-3 px-4 py-2.5 rounded-xl bg-amber-50 border border-amber-200 text-amber-700 text-xs flex gap-2 items-start">
                <span>⚠️</span>
                <span><strong>Demo prices</strong> — live scraping was blocked. Showing sample data.</span>
              </div>
            )}

            {/* 3-column grid */}
            <div className="grid grid-cols-3 gap-3">
              {PLATFORMS.map(platform => (
                <PlatformColumn
                  key={platform.id}
                  platform={platform}
                  items={filteredPlatformData[platform.id] || []}
                  cheapestPrice={cheapestPrice}
                />
              ))}
            </div>
          </div>
        )}

        {/* No results */}
        {results && !loading && results.total === 0 && (
          <div className="text-center py-14">
            <div className="text-4xl mb-3">😔</div>
            <p className="text-gray-600 font-medium text-sm">No results for &ldquo;{lastQuery}&rdquo;</p>
            <p className="text-gray-400 text-xs mt-1">Try a different product name.</p>
          </div>
        )}
      </main>

      <footer className="text-center py-6 text-xs text-gray-400 border-t border-gray-100">
        PriceCart · Live prices · Sorted low to high · Filter by price
      </footer>
    </div>
  );
}
