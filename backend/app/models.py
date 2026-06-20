from pydantic import BaseModel
from typing import Optional, List


class ProductResult(BaseModel):
    """A product found on a specific platform."""
    platform: str                  # "blinkit", "zepto", etc.
    platform_display: str          # "Blinkit", "Zepto", etc.
    platform_color: str            # hex color for UI
    platform_logo: str             # emoji or URL
    product_name: str
    price: Optional[float]         # in INR
    mrp: Optional[float]           # original price
    unit: Optional[str]            # "500g", "1L", etc.
    image_url: Optional[str]
    product_url: Optional[str]
    in_stock: bool = True
    delivery_time: Optional[str]   # "10 mins", "Next day", etc.
    discount_pct: Optional[float]  # computed: (mrp-price)/mrp*100


class SearchResponse(BaseModel):
    query: str
    results: List["ComparedProduct"]
    total: int


class ComparedProduct(BaseModel):
    """A canonical product with prices across platforms."""
    canonical_name: str
    category: Optional[str]
    image_url: Optional[str]
    prices: List[ProductResult]    # sorted cheapest first
    cheapest_platform: Optional[str]
    cheapest_price: Optional[float]
    most_expensive_price: Optional[float]
    savings: Optional[float]       # max savings vs most expensive
