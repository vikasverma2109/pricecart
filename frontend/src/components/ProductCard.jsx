import PriceRow from "./PriceRow";

export default function ProductCard({ product, sortBy }) {
  const { canonical_name, prices, cheapest_price, savings, image_url } = product;

  const sortedPrices = [...(prices || [])].sort((a, b) => {
    if (sortBy === "unit_price") {
      return (a.price_per_unit ?? Infinity) - (b.price_per_unit ?? Infinity);
    }
    return (a.price ?? Infinity) - (b.price ?? Infinity);
  });

  const bestPrice = sortBy === "unit_price"
    ? Math.min(...sortedPrices.map(p => p.price_per_unit ?? Infinity))
    : cheapest_price;

  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden border border-gray-100">
      <div className="flex items-start gap-3 px-4 py-3 border-b border-gray-100">
        <div className="w-12 h-12 rounded-xl bg-gray-100 flex-shrink-0 overflow-hidden flex items-center justify-center">
          {image_url ? (
            <img src={image_url} alt={canonical_name}
              className="w-full h-full object-contain"
              onError={e => { e.target.style.display = "none"; }} />
          ) : (
            <span className="text-2xl">🛒</span>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="font-semibold text-gray-900 text-sm leading-snug line-clamp-2">
            {canonical_name}
          </h3>
          <div className="flex items-center gap-2 mt-1 flex-wrap">
            {cheapest_price != null && (
              <span className="text-xs font-semibold text-green-700">
                From ₹{cheapest_price.toFixed(0)}
              </span>
            )}
            {savings > 0 && (
              <span className="text-xs text-orange-600 font-medium">
                Save up to ₹{savings.toFixed(0)}
              </span>
            )}
            <span className="text-xs text-gray-400">
              {sortedPrices.length} platform{sortedPrices.length !== 1 ? "s" : ""}
            </span>
          </div>
        </div>
      </div>

      <div>
        {sortedPrices.map((p, i) => (
          <PriceRow
            key={p.platform}
            result={p}
            isBest={
              sortBy === "unit_price"
                ? p.price_per_unit != null && p.price_per_unit === bestPrice
                : p.price != null && p.price === cheapest_price
            }
            isLast={i === sortedPrices.length - 1}
          />
        ))}
      </div>
    </div>
  );
}
