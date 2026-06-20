/**
 * API client — reads VITE_API_URL from env (set in .env or Vercel env vars).
 * Falls back to "" which proxies to localhost:8000 in dev (via vite.config.js).
 */

const BASE_URL = import.meta.env.VITE_API_URL || "";

export async function searchProducts(query, location = {}) {
  const params = new URLSearchParams({ q: query });
  if (location.lat && location.lon) {
    params.set("lat", location.lat);
    params.set("lon", location.lon);
  } else if (location.city) {
    params.set("city", location.city);
  }
  const url = `${BASE_URL}/api/search?${params.toString()}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function getPlatforms() {
  const res = await fetch(`${BASE_URL}/api/platforms`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
