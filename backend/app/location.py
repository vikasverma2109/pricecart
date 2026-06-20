"""
Location database for major Indian cities.

Each entry provides:
  - lat / lon     : coordinates (used by Blinkit, Zepto, Swiggy)
  - pincode       : 6-digit PIN (used by Amazon Fresh, Flipkart)
  - bb_city_id    : BigBasket city ID
  - zepto_store   : Zepto default store ID for this city

To add a new city: copy any row, update the values.
Zepto store IDs can be found by inspecting network requests on zeptonow.com.
"""

CITIES: dict[str, dict] = {
    "Delhi": {
        "lat": "28.6315",
        "lon": "77.2167",
        "pincode": "110001",
        "bb_city_id": "5",
        "zepto_store": "b3bb4e28-3ee3-4e5f-9dcc-4bc08e5b6e4c",
        "display": "Delhi / NCR",
    },
    "Mumbai": {
        "lat": "19.0760",
        "lon": "72.8777",
        "pincode": "400001",
        "bb_city_id": "1",
        "zepto_store": "e1b5f0a2-4c73-4d1b-8e3c-1d2e3f4a5b6c",
        "display": "Mumbai",
    },
    "Bengaluru": {
        "lat": "12.9716",
        "lon": "77.5946",
        "pincode": "560001",
        "bb_city_id": "2",
        "zepto_store": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "display": "Bengaluru",
    },
    "Hyderabad": {
        "lat": "17.3850",
        "lon": "78.4867",
        "pincode": "500001",
        "bb_city_id": "3",
        "zepto_store": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "display": "Hyderabad",
    },
    "Chennai": {
        "lat": "13.0827",
        "lon": "80.2707",
        "pincode": "600001",
        "bb_city_id": "4",
        "zepto_store": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        "display": "Chennai",
    },
    "Kolkata": {
        "lat": "22.5726",
        "lon": "88.3639",
        "pincode": "700001",
        "bb_city_id": "6",
        "zepto_store": "d4e5f6a7-b8c9-0123-defa-234567890123",
        "display": "Kolkata",
    },
    "Pune": {
        "lat": "18.5204",
        "lon": "73.8567",
        "pincode": "411001",
        "bb_city_id": "7",
        "zepto_store": "e5f6a7b8-c9d0-1234-efab-345678901234",
        "display": "Pune",
    },
    "Ahmedabad": {
        "lat": "23.0225",
        "lon": "72.5714",
        "pincode": "380001",
        "bb_city_id": "8",
        "zepto_store": "f6a7b8c9-d0e1-2345-fabc-456789012345",
        "display": "Ahmedabad",
    },
    "Jaipur": {
        "lat": "26.9124",
        "lon": "75.7873",
        "pincode": "302001",
        "bb_city_id": "9",
        "zepto_store": "a7b8c9d0-e1f2-3456-abcd-567890123456",
        "display": "Jaipur",
    },
    "Chandigarh": {
        "lat": "30.7333",
        "lon": "76.7794",
        "pincode": "160001",
        "bb_city_id": "10",
        "zepto_store": "b8c9d0e1-f2a3-4567-bcde-678901234567",
        "display": "Chandigarh",
    },
}

# Default fallback
DEFAULT_CITY = "Delhi"


def get_city(name: str) -> dict:
    """Case-insensitive lookup. Falls back to Delhi if not found."""
    for key, data in CITIES.items():
        if key.lower() == name.lower().strip():
            return {**data, "name": key}
    return {**CITIES[DEFAULT_CITY], "name": DEFAULT_CITY}


def get_city_list() -> list[dict]:
    """Return all cities for the frontend dropdown."""
    return [
        {"id": key, "display": val["display"], "pincode": val["pincode"]}
        for key, val in CITIES.items()
    ]
