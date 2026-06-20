export default function PriceRow({ result, isBest, isLast }) {
  const {
    platform_display, platform_color,
    price, mrp, price_per_unit, price_per_unit_label,
    unit, delivery_time, discount_pct, in_stock, product_url,
  } = result;

  return (
    <div className={`flex items-center px-4 py-3 gap-3 transition-colors ${
      !isLast ? "border-b border-gray-50" : ""
    } ${isBest ? "bg-green-50" : "hover:bg-gray-50"}`}>

      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="w-2.5 h-2.5 rounded-full flex-shrink-0"
                style={{ backgroundColor: platform_color }} />
          <span className="text-sm font-semibold text-gray-800">{platform_display}</span>
          {isBest && in_stock && (
            <span className="text-xs bg-green-600 text-white px-1.5 py-0.5 rounded-full font-medium leading-none">
              Best
            </span>
          )}
          {!in_stock && (
            <span className="text-xs text-red-500 font-medium">Out of stock</span>
          )}
        </div>
        <div className="flex items-center gap-1.5 mt-0.5 ml-5 flex-wrap">
          {price_per_unit != null && price_per_unit_label && (
            <span className="text-xs font-medium text-gray-700">
              ₹{price_per_unit}{price_per_unit_label}
            </span>
          )}
          {unit && !price_per_unit && (
            <span className="text-xs text-gray-400">{unit}</span>
          )}
          {delivery_time && (
            <span className="text-xs text-gray-400">[{delivery_time}]</span>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3 flex-shrink-0">
        <div className="text-right">
          {discount_pct > 0 && mrp && (
            <div className="text-xs text-gray-400 line-through leading-none mb-0.5">
              ₹{mrp.toFixed(0)}
            </div>
          )}
          <div className={`text-base font-bold leading-none ${
            isBest && in_stock ? "text-green-700" : "text-gray-900"
          }`}>
            {in_stock && price != null ? `₹${price.toFixed(0)}` : "—"}
          </div>
          {discount_pct > 0 && (
            <div className="text-xs text-green-600 font-medium leading-none mt-0.5">
              -{discount_pct.toFixed(0)}%
            </div>
          )}
        </div>
        {product_url && in_stock && (
          <a href={product_url} target="_blank" rel="noopener noreferrer"
             className="text-xs text-indigo-500 hover:text-indigo-700 font-semibold whitespace-nowrap">
            Buy →
          </a>
        )}
      </div>
    </div>
  );
}
